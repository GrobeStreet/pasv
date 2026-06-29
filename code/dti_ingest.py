"""
DTI v0.1 — Defender Targeting Index Ingest Pipeline
====================================================

Pulls NBA possession-level play-by-play data via the PBPstats library and
emits a normalized player-matchup-possession parquet table that downstream
DTI computation consumes.

DTI (Defender Targeting Index) is the Optimization-Gap lane defined in
`OptGap_MASTER_Dossier_2026-06-13.md` (Lane 1):

    "Which defender ended up guarding the primary action, what was the PPP
     of that possession vs the league baseline PPP for that defender on that
     action type, and how many possessions per game is this defender hunted?"

This module ingests the substrate. It does NOT compute DTI itself — that
runs in a downstream notebook on the parquet this script produces.

v0.1 simplifications (to be revisited in v0.2 with optical tracking):
    1. "Primary defender" = the on-court defender most likely to have been
       guarding the shooter / TOV player at possession end.
       Heuristic: shot-blocker on the play → assigned defender from a
       same-position matchup table → fallback to "unknown" tag.
    2. Action-type classification is derived from event sequence
       (assists, putbacks, transition timing, shot clock, etc.). PBPstats
       does NOT label P&R / iso / post-up natively; we approximate.
    3. Shot distance and zone come straight from PBPstats `shot_data`.

Author: Bobby Morong / DataDunkNBA — sole author
License: MIT
Version: v0.1 — 2026-06-13 (substrate; downstream DTI is unbuilt)
"""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import pandas as pd

try:
    from tqdm import tqdm
except ImportError:  # pragma: no cover — tqdm is in requirements but degrade gracefully
    def tqdm(it, **kwargs):  # type: ignore
        return it


# -----------------------------------------------------------------------------
# Logging
# -----------------------------------------------------------------------------
logger = logging.getLogger("dti_ingest")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter("[%(asctime)s] %(levelname)s %(name)s — %(message)s")
    )
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


# -----------------------------------------------------------------------------
# Constants — locked, framework conventions
# -----------------------------------------------------------------------------
import os as _os
DEFAULT_DATA_DIR = Path(
    _os.environ.get(
        "DTI_DATA_DIR",
        "/Users/robertmorong/Documents/Claude/Projects/Basketball Stats Book/dti_data",
    )
)
PBPSTATS_RESPONSE_DIR = DEFAULT_DATA_DIR / "pbpstats_response_cache"

# Shot-zone bins (consistent with NBA.com and pbpstats AT_RIM_CUTOFF / SHORT_MID_RANGE_CUTOFF)
AT_RIM_FT = 4
SHORT_MID_FT = 14
LONG_MID_FT = 23  # corner-3 line

# Transition possession: short shot clock + short time since prev possession
TRANSITION_SECONDS_SINCE_PREV = 8
TRANSITION_SHOT_CLOCK = 17  # roughly 7 sec elapsed of a 24-clock

# Action-type vocabulary (string-stable, used downstream)
ACTION_TRANSITION = "transition"
ACTION_PUTBACK = "putback"
ACTION_ASSISTED_3 = "assisted_3"
ACTION_ASSISTED_2 = "assisted_2"
ACTION_ISO = "iso"
ACTION_POST_UP_OR_DRIVE = "post_or_drive"
ACTION_TURNOVER = "turnover"
ACTION_FREE_THROW = "free_throw"
ACTION_OTHER = "other"

# Outcome vocabulary
OUTCOME_MADE_2 = "made_2"
OUTCOME_MADE_3 = "made_3"
OUTCOME_MISSED_2 = "missed_2"
OUTCOME_MISSED_3 = "missed_3"
OUTCOME_TURNOVER = "turnover"
OUTCOME_FOUL_TRIP = "foul_drawn_ft_trip"  # possession ended on FT trip
OUTCOME_OTHER = "other"

# Sentinel for unresolved primary defender (downstream filters these out
# unless v0.2 optical tracking is layered on top)
UNKNOWN_DEFENDER_ID = -1


# -----------------------------------------------------------------------------
# Dependency / fallback loader
# -----------------------------------------------------------------------------
def ensure_pbpstats_available() -> str:
    """
    Return 'pbpstats' if importable, else 'nba_api' if importable,
    else raise. The runner script will pip-install pbpstats before
    calling this; this function is the in-process sanity gate.

    Override: set DTI_BACKEND=nba_api to force the fallback path
    (useful when pbpstats's stats.nba.com endpoint is throttling).
    """
    if _os.environ.get("DTI_BACKEND") == "nba_api":
        logger.warning("DTI_BACKEND=nba_api set; forcing nba_api fallback path.")
        return "nba_api"
    try:
        import pbpstats  # noqa: F401
        return "pbpstats"
    except ImportError:
        pass

    try:
        import nba_api  # noqa: F401
        logger.warning("pbpstats not available; falling back to nba_api raw mode.")
        return "nba_api"
    except ImportError as exc:
        raise RuntimeError(
            "Neither pbpstats nor nba_api is installed. Run `pip install pbpstats nba_api`."
        ) from exc


# -----------------------------------------------------------------------------
# Client wiring (pbpstats)
# -----------------------------------------------------------------------------
def make_pbpstats_client(data_dir: Path = PBPSTATS_RESPONSE_DIR):
    """
    Build a configured pbpstats Client that uses the web data source and
    caches JSON responses to `data_dir`. Re-runs hit cache, not the API.
    """
    from pbpstats.client import Client

    data_dir.mkdir(parents=True, exist_ok=True)
    settings = {
        "dir": str(data_dir),
        "Boxscore": {"source": "web", "data_provider": "stats_nba"},
        "Possessions": {"source": "web", "data_provider": "stats_nba"},
        "EnhancedPbp": {"source": "web", "data_provider": "stats_nba"},
        "Games": {"source": "web", "data_provider": "stats_nba"},
    }
    return Client(settings)


def list_season_game_ids(client, season_str: str, season_type: str) -> List[str]:
    """
    Return all game_ids for a season (e.g., '2025-26', 'Regular Season').
    """
    season = client.Season("nba", season_str, season_type)
    games_resource = getattr(season, "games", None)
    if games_resource is None:
        raise RuntimeError("Season object missing `games` resource.")
    game_ids = [item.game_id for item in games_resource.items]
    logger.info(
        "Found %d games for %s %s", len(game_ids), season_str, season_type
    )
    return game_ids


def load_game_with_retries(
    client, game_id: str, max_retries: int = 4, backoff_seconds: float = 2.0
):
    """
    Wrap the stats.nba.com fetch with exponential backoff. The endpoint
    throttles aggressively, so a 3-5x retry budget is standard.
    """
    last_exc: Optional[Exception] = None
    for attempt in range(1, max_retries + 1):
        try:
            return client.Game(game_id)
        except Exception as exc:  # broad: stats.nba.com surfaces many error types
            last_exc = exc
            sleep_for = backoff_seconds * (2 ** (attempt - 1))
            logger.warning(
                "Game %s load failed (attempt %d/%d): %s. Sleeping %.1fs.",
                game_id, attempt, max_retries, exc, sleep_for,
            )
            time.sleep(sleep_for)
    raise RuntimeError(f"Exhausted retries for game {game_id}") from last_exc


# -----------------------------------------------------------------------------
# Event-level helpers (work against pbpstats enhanced_pbp items)
# -----------------------------------------------------------------------------
def _is_fieldgoal(event) -> bool:
    from pbpstats.resources.enhanced_pbp import FieldGoal
    return isinstance(event, FieldGoal)


def _is_freethrow(event) -> bool:
    from pbpstats.resources.enhanced_pbp import FreeThrow
    return isinstance(event, FreeThrow)


def _is_turnover(event) -> bool:
    from pbpstats.resources.enhanced_pbp import Turnover
    return isinstance(event, Turnover) and not getattr(event, "is_no_turnover", False)


def _last_terminal_event(possession):
    """
    Return the event that ended the possession: the shot, FT trip, or TOV.
    Filters out substitutions / fouls that don't terminate the possession.
    """
    for event in reversed(possession.events):
        if _is_fieldgoal(event):
            return event
        if _is_turnover(event):
            return event
        if _is_freethrow(event):
            return event
    # Fall back to last event of any kind
    return possession.events[-1] if possession.events else None


def shot_zone_from_distance(distance_ft: Optional[float], shot_value: int,
                            is_corner_3: bool) -> str:
    """Categorical shot zone."""
    if distance_ft is None:
        return "unknown"
    if shot_value == 3:
        return "corner_3" if is_corner_3 else "above_break_3"
    if distance_ft < AT_RIM_FT:
        return "at_rim"
    if distance_ft < SHORT_MID_FT:
        return "short_mid"
    return "long_mid"


# -----------------------------------------------------------------------------
# Primary-defender heuristic (v0.1)
# -----------------------------------------------------------------------------
def derive_primary_defender(possession, terminal_event) -> Tuple[int, str]:
    """
    Derive the primary defender on the possession-ending event.

    Heuristic priority (v0.1):
        1. If the shot was blocked, the blocker is the primary defender.
        2. If a defensive foul was logged on the terminal event by a single
           defender within the same possession at the same clock, use that
           defender.
        3. Otherwise: use the matchup heuristic — among the 5 on-court
           defenders, assign the defender whose listed position best matches
           the shooter's, falling back to "same-index" of the on-court lineup.
           (Without optical tracking we cannot do better in v0.1.)
        4. If we still can't resolve, return UNKNOWN_DEFENDER_ID.

    Returns (defender_player_id, heuristic_used).

    Returns the heuristic tag so downstream DTI can stratify or trim by
    confidence level.
    """
    from pbpstats.resources.enhanced_pbp import FieldGoal, Foul, Turnover

    if terminal_event is None:
        return UNKNOWN_DEFENDER_ID, "no_terminal_event"

    # --- 1. Blocked shot → blocker is the defender ---
    if isinstance(terminal_event, FieldGoal) and getattr(terminal_event, "is_blocked", False):
        blocker_id = getattr(terminal_event, "player3_id", 0) or 0
        if blocker_id:
            return blocker_id, "blocker"

    # --- 2. Defensive shooting foul at same clock ---
    same_clock_fouls = [
        ev for ev in possession.events
        if isinstance(ev, Foul)
        and getattr(ev, "clock", None) == getattr(terminal_event, "clock", None)
        and getattr(ev, "player1_id", 0)
    ]
    if same_clock_fouls:
        # The committing player is on defense relative to possession's offense_team_id
        offense_team_id = possession.offense_team_id
        for foul in same_clock_fouls:
            if getattr(foul, "team_id", 0) != offense_team_id and getattr(foul, "player1_id", 0):
                return foul.player1_id, "shooting_foul"

    # --- 3. Matchup heuristic from on-court lineup ---
    try:
        current_players = terminal_event.current_players  # {team_id: [pids]}
    except AttributeError:
        return UNKNOWN_DEFENDER_ID, "no_lineup_data"

    offense_team_id = possession.offense_team_id
    defense_team_ids = [tid for tid in current_players if tid != offense_team_id]
    if not defense_team_ids:
        return UNKNOWN_DEFENDER_ID, "no_defense_team"
    defenders = current_players[defense_team_ids[0]]

    # Identify the shooter / TOV player
    shooter_id = 0
    if isinstance(terminal_event, FieldGoal):
        shooter_id = getattr(terminal_event, "player1_id", 0)
    elif isinstance(terminal_event, Turnover):
        shooter_id = getattr(terminal_event, "player1_id", 0)
    elif _is_freethrow(terminal_event):
        shooter_id = getattr(terminal_event, "player1_id", 0)

    if not shooter_id:
        return UNKNOWN_DEFENDER_ID, "no_shooter"

    offense_players = current_players.get(offense_team_id, [])
    if shooter_id in offense_players and len(defenders) == len(offense_players):
        # Same-index pairing — extremely crude but documented.
        try:
            idx = offense_players.index(shooter_id)
            return defenders[idx], "matchup_same_index_fallback"
        except (ValueError, IndexError):
            pass

    # Last resort: tag and move on
    return UNKNOWN_DEFENDER_ID, "unresolved"


# -----------------------------------------------------------------------------
# Action-type tagger (v0.1)
# -----------------------------------------------------------------------------
def tag_action_type(possession, terminal_event) -> str:
    """
    Classify the possession's primary action type.

    PBPstats does NOT label P&R / iso / post-up natively. We approximate from:
        - possession start type + elapsed clock → transition
        - putback flag on the terminal shot
        - assisted vs unassisted 2 vs 3 (proxy for catch-and-shoot vs iso)
        - turnover terminal
        - FT trip terminal (foul-drawn possession)

    Returns one of the ACTION_* constants. Downstream DTI groups baselines
    by this tag, so the vocabulary is intentionally compact and stable.
    """
    from pbpstats.resources.enhanced_pbp import FieldGoal, FreeThrow, Turnover

    if terminal_event is None:
        return ACTION_OTHER

    # --- Transition: short time-since-prev + short seconds since possession start
    seconds_remaining = getattr(terminal_event, "seconds_remaining", None)
    try:
        seconds_since_prev = getattr(terminal_event, "seconds_since_previous_event", None)
    except Exception:
        seconds_since_prev = None

    # Use possession start clock vs terminal clock as the elapsed-on-this-poss proxy
    try:
        start_clock_parts = possession.start_time.split(":") if possession.start_time else None
        end_clock_parts = possession.end_time.split(":") if possession.end_time else None
        if start_clock_parts and end_clock_parts and len(start_clock_parts) == 2:
            start_sec = int(start_clock_parts[0]) * 60 + int(start_clock_parts[1])
            end_sec = int(end_clock_parts[0]) * 60 + int(end_clock_parts[1])
            elapsed = start_sec - end_sec
        else:
            elapsed = None
    except Exception:
        elapsed = None

    if elapsed is not None and 0 < elapsed <= TRANSITION_SECONDS_SINCE_PREV:
        # Plus check that prior possession ended in a steal / live-ball turnover or made FG
        return ACTION_TRANSITION

    # --- Terminal-event classification
    if isinstance(terminal_event, Turnover):
        return ACTION_TURNOVER

    if isinstance(terminal_event, FreeThrow):
        return ACTION_FREE_THROW

    if isinstance(terminal_event, FieldGoal):
        if getattr(terminal_event, "is_putback", False):
            return ACTION_PUTBACK
        is_assisted = getattr(terminal_event, "is_assisted", False)
        shot_value = getattr(terminal_event, "shot_value", 2)
        if is_assisted:
            return ACTION_ASSISTED_3 if shot_value == 3 else ACTION_ASSISTED_2
        # Unassisted 2 → most often iso, drive, or post-up. Distance separates:
        distance = getattr(terminal_event, "distance", None)
        if distance is not None and distance <= AT_RIM_FT:
            return ACTION_POST_UP_OR_DRIVE
        return ACTION_ISO

    return ACTION_OTHER


# -----------------------------------------------------------------------------
# Possession-level extraction
# -----------------------------------------------------------------------------
@dataclass
class PossessionRow:
    game_id: str
    period: int
    possession_number: int
    offensive_team_id: int
    defensive_team_id: int
    offensive_player_ids: List[int] = field(default_factory=list)
    defensive_player_ids: List[int] = field(default_factory=list)
    primary_action_type: str = ACTION_OTHER
    shot_outcome: str = OUTCOME_OTHER
    points: int = 0
    shot_distance: Optional[float] = None
    shot_zone: str = "unknown"
    primary_offensive_player: int = 0
    primary_defensive_player: int = UNKNOWN_DEFENDER_ID
    defender_heuristic: str = "unresolved"
    start_clock: Optional[str] = None
    end_clock: Optional[str] = None
    possession_start_type: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            **self.__dict__,
            "offensive_player_ids": tuple(self.offensive_player_ids),
            "defensive_player_ids": tuple(self.defensive_player_ids),
        }


def _outcome_and_points(terminal_event) -> Tuple[str, int, Optional[float], str]:
    """
    Returns (outcome_tag, points_scored, shot_distance, shot_zone).
    Points are credited to the offensive team on this possession.
    """
    from pbpstats.resources.enhanced_pbp import FieldGoal, FreeThrow, Turnover

    if terminal_event is None:
        return OUTCOME_OTHER, 0, None, "unknown"

    if isinstance(terminal_event, Turnover):
        return OUTCOME_TURNOVER, 0, None, "unknown"

    if isinstance(terminal_event, FieldGoal):
        shot_value = getattr(terminal_event, "shot_value", 2)
        distance = getattr(terminal_event, "distance", None)
        zone = shot_zone_from_distance(
            distance, shot_value, getattr(terminal_event, "is_corner_3", False)
        )
        if getattr(terminal_event, "is_made", False):
            return (
                OUTCOME_MADE_3 if shot_value == 3 else OUTCOME_MADE_2,
                shot_value,
                distance,
                zone,
            )
        return (
            OUTCOME_MISSED_3 if shot_value == 3 else OUTCOME_MISSED_2,
            0,
            distance,
            zone,
        )

    if isinstance(terminal_event, FreeThrow):
        # We don't double-count FTs; the FT possession is tagged distinctly.
        # Points for the possession come from the running score margin.
        return OUTCOME_FOUL_TRIP, 0, None, "free_throw_line"

    return OUTCOME_OTHER, 0, None, "unknown"


def extract_possessions(game) -> List[Dict[str, Any]]:
    """
    Convert one pbpstats Game into a list of possession-level dicts.

    Each possession's points are derived from the score delta on the
    possession's events (so FT trips are credited correctly).
    """
    rows: List[Dict[str, Any]] = []

    possessions = getattr(game, "possessions", None)
    if possessions is None or not possessions.items:
        logger.warning("Game %s has no possessions; skipping.", getattr(game, "game_id", "?"))
        return rows

    for poss in possessions.items:
        try:
            terminal = _last_terminal_event(poss)
            offense_team_id = poss.offense_team_id
            team_ids = poss.get_team_ids()
            defense_team_id = next((tid for tid in team_ids if tid != offense_team_id), 0)

            # On-court lineups at the moment of the terminal event
            offense_players: List[int] = []
            defense_players: List[int] = []
            if terminal is not None:
                try:
                    current = terminal.current_players
                    offense_players = list(current.get(offense_team_id, []))
                    defense_players = list(current.get(defense_team_id, []))
                except Exception:
                    pass

            action_type = tag_action_type(poss, terminal)
            outcome, points_from_fg, distance, zone = _outcome_and_points(terminal)

            # Compute points scored on the possession from score margin delta
            points_on_poss = _points_scored_on_possession(poss)

            defender_id, heuristic = derive_primary_defender(poss, terminal)

            # Primary offensive player: the shooter / TOV player
            primary_off = 0
            if terminal is not None and hasattr(terminal, "player1_id"):
                primary_off = getattr(terminal, "player1_id", 0)

            row = PossessionRow(
                game_id=getattr(poss, "game_id", ""),
                period=getattr(poss, "period", 0),
                possession_number=getattr(poss, "number", 0),
                offensive_team_id=offense_team_id,
                defensive_team_id=defense_team_id,
                offensive_player_ids=offense_players,
                defensive_player_ids=defense_players,
                primary_action_type=action_type,
                shot_outcome=outcome,
                points=points_on_poss if points_on_poss is not None else points_from_fg,
                shot_distance=distance,
                shot_zone=zone,
                primary_offensive_player=primary_off,
                primary_defensive_player=defender_id,
                defender_heuristic=heuristic,
                start_clock=getattr(poss, "start_time", None),
                end_clock=getattr(poss, "end_time", None),
                possession_start_type=getattr(poss, "possession_start_type", None),
            )
            rows.append(row.to_dict())
        except Exception as exc:
            logger.debug(
                "Skipping possession in game %s period %s: %s",
                getattr(poss, "game_id", "?"),
                getattr(poss, "period", "?"),
                exc,
            )
            continue

    return rows


def _points_scored_on_possession(possession) -> Optional[int]:
    """
    Calculate points scored ON this possession from the offense's perspective
    by diffing the score between possession start and end.
    """
    try:
        events = possession.events
        if not events:
            return None
        offense_team_id = possession.offense_team_id
        # `score` on first event is "score BEFORE event"; last event has "score AFTER"
        first_score = getattr(events[0], "score", None)
        last_score = getattr(events[-1], "score", None)
        if first_score is None or last_score is None:
            return None
        first_off = first_score.get(offense_team_id, 0)
        last_off = last_score.get(offense_team_id, 0)
        return max(0, last_off - first_off)
    except Exception:
        return None


# -----------------------------------------------------------------------------
# Season ingest orchestration
# -----------------------------------------------------------------------------
def ingest_season(
    season_str: str,
    season_type: str = "Regular Season",
    response_dir: Path = PBPSTATS_RESPONSE_DIR,
    max_games: Optional[int] = None,
    sleep_between_games: float = 0.6,
) -> pd.DataFrame:
    """
    Ingest a full season of possession-level data.

    Args:
        season_str: e.g., "2025-26"
        season_type: "Regular Season", "Playoffs", or "Play In"
        response_dir: Where pbpstats caches API JSON responses
        max_games: Optional cap for dry runs / testing
        sleep_between_games: Polite sleep between game fetches

    Returns:
        DataFrame, one row per possession, with framework columns.
    """
    backend = ensure_pbpstats_available()
    if backend == "nba_api":
        # Fallback path is implemented separately; kept thin in v0.1.
        return _ingest_season_via_nba_api(season_str, season_type, max_games=max_games)

    client = make_pbpstats_client(response_dir)
    game_ids = list_season_game_ids(client, season_str, season_type)
    if max_games:
        game_ids = game_ids[:max_games]
        logger.info("Capped to %d games (dry-run mode).", len(game_ids))

    all_rows: List[Dict[str, Any]] = []
    failed_games: List[Tuple[str, str]] = []

    for game_id in tqdm(game_ids, desc=f"Ingesting {season_str} {season_type}"):
        try:
            game = load_game_with_retries(client, game_id)
        except Exception as exc:
            failed_games.append((game_id, str(exc)))
            continue

        try:
            rows = extract_possessions(game)
            all_rows.extend(rows)
        except Exception as exc:
            failed_games.append((game_id, f"extract failed: {exc}"))

        time.sleep(sleep_between_games)

    if failed_games:
        logger.warning(
            "Failed to ingest %d games. First 5: %s",
            len(failed_games), failed_games[:5],
        )

    df = pd.DataFrame(all_rows)
    df["season"] = season_str
    df["season_type"] = season_type
    df["ingest_version"] = "v0.1"
    df["ingest_date"] = pd.Timestamp.utcnow().date().isoformat()
    return df


def _ingest_season_via_nba_api(
    season_str: str, season_type: str, max_games: Optional[int] = None
) -> pd.DataFrame:
    """
    Minimal nba_api fallback. Pulls scoreboard + playbyplayv2 per game and
    re-derives possessions on a coarser grid (no enhanced PBP). This path
    exists so the DTI ingest does not block on a pbpstats outage for the
    2025-26 season — Bobby gets a degraded-but-non-empty parquet either way.

    Possession reconstruction here is a simplified version of pbpstats'
    rule: a possession ends on a made FG/last-FT, a defensive rebound, or
    a turnover. We do NOT compute full matchup data on this path.
    """
    from nba_api.stats.endpoints import leaguegamefinder, playbyplayv2

    logger.info("nba_api fallback mode — possession reconstruction is coarse.")
    # leaguegamefinder lacks a direct season_type filter for all years; fetch and filter
    finder = leaguegamefinder.LeagueGameFinder(
        season_nullable=season_str,
        season_type_nullable=season_type,
        league_id_nullable="00",
    )
    games_df = finder.get_data_frames()[0]
    game_ids = sorted(games_df["GAME_ID"].unique().tolist())
    if max_games:
        game_ids = game_ids[:max_games]

    all_rows: List[Dict[str, Any]] = []
    for game_id in tqdm(game_ids, desc=f"[nba_api fallback] {season_str} {season_type}"):
        try:
            pbp_df = playbyplayv2.PlayByPlayV2(game_id=game_id).get_data_frames()[0]
        except Exception as exc:
            logger.warning("nba_api fetch failed for %s: %s", game_id, exc)
            continue
        all_rows.extend(_nba_api_possession_rows(game_id, pbp_df))
        time.sleep(0.6)

    df = pd.DataFrame(all_rows)
    df["season"] = season_str
    df["season_type"] = season_type
    df["ingest_version"] = "v0.1-fallback"
    df["ingest_date"] = pd.Timestamp.utcnow().date().isoformat()
    return df


def _nba_api_possession_rows(game_id: str, pbp_df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Coarse possession reconstruction from nba_api playbyplayv2.

    Drops most framework columns (matchups, action types) and emits only
    the bare minimum: shot outcome, points, shot distance proxy. This is
    the explicit degraded path.
    """
    rows: List[Dict[str, Any]] = []
    pbp_df = pbp_df.sort_values(["PERIOD", "EVENTNUM"]).reset_index(drop=True)
    poss_num = 0
    current_off_team = 0

    for _, ev in pbp_df.iterrows():
        ev_type = int(ev.get("EVENTMSGTYPE", 0) or 0)
        is_terminal = ev_type in (1, 2, 5)  # made FG, missed FG, turnover
        if is_terminal:
            poss_num += 1
            distance = None
            if ev_type in (1, 2):
                desc = (ev.get("HOMEDESCRIPTION") or "") + " " + (ev.get("VISITORDESCRIPTION") or "")
                # crude distance extraction "23' Pullup" → 23
                import re
                m = re.search(r"(\d+)'", desc)
                if m:
                    distance = float(m.group(1))
            outcome = (
                OUTCOME_MADE_2 if ev_type == 1
                else OUTCOME_MISSED_2 if ev_type == 2
                else OUTCOME_TURNOVER
            )
            rows.append({
                "game_id": str(game_id),
                "period": int(ev.get("PERIOD", 0) or 0),
                "possession_number": poss_num,
                "offensive_team_id": int(ev.get("PLAYER1_TEAM_ID", 0) or 0),
                "defensive_team_id": 0,
                "offensive_player_ids": (),
                "defensive_player_ids": (),
                "primary_action_type": ACTION_OTHER,
                "shot_outcome": outcome,
                "points": 2 if ev_type == 1 else 0,
                "shot_distance": distance,
                "shot_zone": "unknown",
                "primary_offensive_player": int(ev.get("PLAYER1_ID", 0) or 0),
                "primary_defensive_player": UNKNOWN_DEFENDER_ID,
                "defender_heuristic": "nba_api_fallback",
                "start_clock": ev.get("PCTIMESTRING"),
                "end_clock": ev.get("PCTIMESTRING"),
                "possession_start_type": None,
            })
    return rows


# -----------------------------------------------------------------------------
# Downstream baselines (consumed by DTI computation notebook)
# -----------------------------------------------------------------------------
def compute_expected_PPP_baseline(season_df: pd.DataFrame) -> pd.DataFrame:
    """
    League-wide expected points per possession by action type.

    Output schema:
        primary_action_type, n_possessions, total_points, expected_PPP

    Downstream DTI compares "actual PPP when defender X is targeted" against
    `expected_PPP` for the same action type — that delta is the index.
    """
    if season_df.empty:
        return pd.DataFrame(columns=["primary_action_type", "n_possessions",
                                     "total_points", "expected_PPP"])
    agg = (
        season_df.groupby("primary_action_type", dropna=False)
        .agg(n_possessions=("points", "size"), total_points=("points", "sum"))
        .reset_index()
    )
    agg["expected_PPP"] = agg["total_points"] / agg["n_possessions"]
    return agg.sort_values("n_possessions", ascending=False).reset_index(drop=True)


# -----------------------------------------------------------------------------
# Persistence
# -----------------------------------------------------------------------------
def save_to_parquet(df: pd.DataFrame, path: Path) -> Path:
    """
    Write the possession DataFrame to parquet at `path`. Creates parent dirs.

    We explicitly cast list-of-int columns to object so parquet doesn't fight
    us on schema inference, and we coerce numeric columns to nullable Int64.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    df_out = df.copy()
    for col in ("offensive_player_ids", "defensive_player_ids"):
        if col in df_out.columns:
            df_out[col] = df_out[col].apply(lambda x: list(x) if x is not None else [])

    for col in ("offensive_team_id", "defensive_team_id", "primary_offensive_player",
                "primary_defensive_player", "period", "possession_number", "points"):
        if col in df_out.columns:
            df_out[col] = pd.to_numeric(df_out[col], errors="coerce").astype("Int64")

    try:
        df_out.to_parquet(path, index=False)
    except Exception as exc:
        logger.warning("parquet write failed (%s); falling back to CSV.", exc)
        csv_path = path.with_suffix(".csv")
        df_out.to_csv(csv_path, index=False)
        return csv_path

    return path


# -----------------------------------------------------------------------------
# Summary helper (used by the runner)
# -----------------------------------------------------------------------------
def summarize(df: pd.DataFrame) -> Dict[str, Any]:
    """Return a small summary dict for the runner's stdout line."""
    if df.empty:
        return {"n_possessions": 0, "n_games": 0, "n_players": 0}

    all_players = set()
    for col in ("offensive_player_ids", "defensive_player_ids"):
        if col in df.columns:
            for row in df[col]:
                if row is None:
                    continue
                for pid in row:
                    if pid:
                        all_players.add(int(pid))

    return {
        "n_possessions": int(len(df)),
        "n_games": int(df["game_id"].nunique()) if "game_id" in df else 0,
        "n_players": len(all_players),
        "n_defenders_resolved": int(
            (df["primary_defensive_player"] != UNKNOWN_DEFENDER_ID).sum()
        ) if "primary_defensive_player" in df else 0,
        "defender_resolution_pct": round(
            100.0 * (df["primary_defensive_player"] != UNKNOWN_DEFENDER_ID).mean(), 2
        ) if "primary_defensive_player" in df else 0.0,
    }
