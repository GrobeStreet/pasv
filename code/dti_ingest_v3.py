"""
DTI Ingest v0.1.1 — PlayByPlayV3 native path.

Bypasses the broken nba_api PlayByPlayV2 path (deprecated, returns empty JSON
since 2025) by reading PlayByPlayV3 directly. Schema is completely different
from V2, so this is a parallel ingest module — not a patch to dti_ingest.py.

This is the path that actually runs in the sandbox today (2026-06-13).

Output: possession-level parquet at <out_dir>/poss_v3_<season>_<type>.parquet
"""

from __future__ import annotations
import os
import sys
import time
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import pandas as pd
from tqdm import tqdm
from nba_api.stats.endpoints import leaguegamefinder, playbyplayv3

logger = logging.getLogger("dti_ingest_v3")
if not logger.handlers:
    h = logging.StreamHandler()
    h.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s %(name)s — %(message)s"))
    logger.addHandler(h)
    logger.setLevel(logging.INFO)

# ---------- Possession-end action types in V3 ----------
# V3 actionType vocabulary (from observed data):
#   "2pt", "3pt", "turnover", "rebound", "foul", "freethrow", "substitution",
#   "period", "timeout", "violation", "jumpball", "ejection"
# A possession ends on:
#   - Made FG (2pt or 3pt with shotResult=Made)
#   - Made last FT (freethrow with isFGM=True AND no more FTs in trip)
#   - Defensive rebound
#   - Turnover
TERMINAL_ACTION_TYPES = {"Made Shot", "Missed Shot", "Turnover", "Free Throw"}


def list_playoff_game_ids(season: str) -> List[str]:
    """List all playoff game IDs for a given season (e.g., '2024-25')."""
    finder = leaguegamefinder.LeagueGameFinder(
        season_nullable=season,
        season_type_nullable="Playoffs",
        league_id_nullable="00",
        timeout=60,
    )
    df = finder.get_data_frames()[0]
    return sorted(df["GAME_ID"].unique().tolist())


def list_regular_season_game_ids(season: str, limit: Optional[int] = None) -> List[str]:
    """List regular-season game IDs."""
    finder = leaguegamefinder.LeagueGameFinder(
        season_nullable=season,
        season_type_nullable="Regular Season",
        league_id_nullable="00",
        timeout=60,
    )
    df = finder.get_data_frames()[0]
    ids = sorted(df["GAME_ID"].unique().tolist())
    if limit:
        ids = ids[:limit]
    return ids


def fetch_pbp_v3(game_id: str, retries: int = 3) -> Optional[pd.DataFrame]:
    """Fetch one game's V3 play-by-play with retries."""
    for attempt in range(retries):
        try:
            df = playbyplayv3.PlayByPlayV3(game_id=game_id, timeout=45).get_data_frames()[0]
            return df
        except Exception as exc:
            if attempt == retries - 1:
                logger.warning("PBPv3 fetch failed for %s: %s", game_id, exc)
                return None
            time.sleep(2 ** attempt)
    return None


def extract_possessions_v3(pbp_df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Walk the V3 play-by-play and emit one row per possession.

    Each possession row carries:
      - game_id, period, possession_number
      - offensive_team_id (the team taking the terminal action)
      - primary_offensive_player_id (the shooter / fouler / TOer)
      - primary_defensive_player_id (best-effort: blocker if present, else
        the player on the defensive shooting foul if present at same clock,
        else UNKNOWN -1)
      - action_type (one of: made_2, missed_2, made_3, missed_3, turnover,
        ft_trip, other)
      - points (0, 1, 2, 3 — points on the possession)
      - shot_distance (for FGAs only)
    """
    rows: List[Dict[str, Any]] = []
    if pbp_df is None or len(pbp_df) == 0:
        return rows

    pbp_df = pbp_df.sort_values(["period", "actionNumber"]).reset_index(drop=True)
    poss_num = 0
    game_id = str(pbp_df["gameId"].iloc[0]) if "gameId" in pbp_df.columns else ""

    # Precompute foul events keyed by (period, clock) for defender attribution
    foul_by_clock: Dict[Tuple[int, str], int] = {}
    for _, ev in pbp_df.iterrows():
        if str(ev.get("actionType", "")) == "Foul":
            sub = str(ev.get("subType", "")).lower()
            if "shooting" in sub or "personal" in sub:
                key = (int(ev.get("period", 0)), str(ev.get("clock", "")))
                # personId on foul is the defender who committed it
                foul_by_clock[key] = int(ev.get("personId", 0) or 0)

    # Precompute blockers from the description
    # V3 doesn't have a clean blocker field, but blocks show up as subType
    # on the missed FG event itself in many cases.
    for _, ev in pbp_df.iterrows():
        action_type = str(ev.get("actionType", ""))
        if action_type not in TERMINAL_ACTION_TYPES:
            continue

        period = int(ev.get("period", 0) or 0)
        clock = str(ev.get("clock", "") or "")
        off_player = int(ev.get("personId", 0) or 0)
        off_team = int(ev.get("teamId", 0) or 0)
        sub = str(ev.get("subType", "") or "")
        shot_distance = ev.get("shotDistance")
        is_fg = bool(ev.get("isFieldGoal", 0))
        try:
            shot_value = int(ev.get("shotValue", 0) or 0)
        except (ValueError, TypeError):
            shot_value = 0
        desc = str(ev.get("description", "") or "")

        # Identify defender (best-effort heuristic)
        defender_id = -1
        defender_heuristic = "unknown"

        # 1. Blocker if the description contains BLOCK
        if "BLOCK" in desc.upper():
            defender_heuristic = "blocked_attempt_no_id"

        # 2. Defensive shooting foul at the same clock?
        key = (period, clock)
        if key in foul_by_clock:
            defender_id = foul_by_clock[key]
            defender_heuristic = "shooting_foul_attribution"

        # Classify outcome
        if action_type == "Made Shot":
            if shot_value == 3:
                outcome, points = "made_3", 3
            else:
                outcome, points = "made_2", 2
        elif action_type == "Missed Shot":
            if shot_value == 3:
                outcome, points = "missed_3", 0
            else:
                outcome, points = "missed_2", 0
        elif action_type == "Turnover":
            outcome, points = "turnover", 0
            is_fg = False
        elif action_type == "Free Throw":
            # Only count the LAST FT of a trip as the possession end.
            # V3 subType examples: "Free Throw 1 of 2", "Free Throw 2 of 2", "Free Throw 1 of 1"
            sub_lower = sub.lower()
            if "of" in sub_lower:
                try:
                    parts = sub_lower.split("of")
                    num = int(parts[0].strip().split()[-1])
                    denom = int(parts[1].strip().split()[0])
                    if num != denom:
                        continue  # not terminal — middle FT of a 2 or 3 trip
                except (ValueError, IndexError):
                    continue
            # Determine made/miss from shotResult or pointsTotal change
            shot_result = str(ev.get("shotResult", "") or "").lower()
            if not shot_result:
                # fallback: "MISS" appears in description
                shot_result = "missed" if "MISS" in desc.upper() else "made"
            outcome = "ft_trip_made" if shot_result == "made" else "ft_trip_miss"
            points = 1 if shot_result == "made" else 0
            is_fg = False
        else:
            continue

        poss_num += 1
        rows.append({
            "game_id": game_id,
            "period": period,
            "possession_number": poss_num,
            "offensive_team_id": off_team,
            "primary_offensive_player_id": off_player,
            "primary_defensive_player_id": defender_id,
            "defender_heuristic": defender_heuristic,
            "action_type": action_type,
            "shot_outcome": outcome,
            "points": points,
            "shot_distance": shot_distance if pd.notna(shot_distance) else None,
            "is_field_goal": is_fg,
            "clock": clock,
        })

    return rows


def ingest_v3(
    season: str,
    season_type: str = "Playoffs",
    max_games: Optional[int] = None,
    sleep_between_games: float = 0.6,
) -> pd.DataFrame:
    """Main entry point."""
    if season_type == "Playoffs":
        game_ids = list_playoff_game_ids(season)
    else:
        game_ids = list_regular_season_game_ids(season, limit=max_games)

    if max_games:
        game_ids = game_ids[:max_games]

    logger.info("Pulling %d games (%s %s)", len(game_ids), season, season_type)

    all_rows: List[Dict[str, Any]] = []
    failed: List[str] = []

    for gid in tqdm(game_ids, desc=f"PBP v3 {season} {season_type}"):
        pbp = fetch_pbp_v3(gid)
        if pbp is None:
            failed.append(gid)
            continue
        rows = extract_possessions_v3(pbp)
        all_rows.extend(rows)
        time.sleep(sleep_between_games)

    df = pd.DataFrame(all_rows)
    df["season"] = season
    df["season_type"] = season_type
    df["ingest_version"] = "v0.1.1-pbpv3"
    df["ingest_date"] = pd.Timestamp.utcnow().date().isoformat()

    logger.info("Ingested %d possessions across %d games (%d failed)",
                len(df), len(game_ids) - len(failed), len(failed))
    return df


def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--season", required=True, help="e.g. 2024-25")
    p.add_argument("--season-type", default="Playoffs",
                   choices=["Regular Season", "Playoffs"])
    p.add_argument("--max-games", type=int, default=None)
    p.add_argument("--out-dir", default=None,
                   help="Default: $DTI_DATA_DIR or /tmp/dti_data")
    p.add_argument("--sleep", type=float, default=0.6)
    args = p.parse_args()

    out_dir = Path(
        args.out_dir
        or os.environ.get("DTI_DATA_DIR", "/tmp/dti_data")
    )
    out_dir.mkdir(parents=True, exist_ok=True)

    df = ingest_v3(
        season=args.season,
        season_type=args.season_type,
        max_games=args.max_games,
        sleep_between_games=args.sleep,
    )

    if len(df) == 0:
        logger.error("Empty DataFrame. Exiting.")
        sys.exit(1)

    safe_type = args.season_type.replace(" ", "_")
    out_path = out_dir / f"poss_v3_{args.season}_{safe_type}.parquet"
    df.to_parquet(out_path, index=False)
    logger.info("Wrote %s (%d rows)", out_path, len(df))

    # Quick summary
    print(f"\n=== INGEST SUMMARY ===")
    print(f"Possessions: {len(df):,}")
    print(f"Unique games: {df['game_id'].nunique()}")
    print(f"Unique offensive players: {df['primary_offensive_player_id'].nunique()}")
    print(f"Unique defenders identified: {(df['primary_defensive_player_id'] > 0).sum()}")
    print(f"Defender attribution rate: {(df['primary_defensive_player_id'] > 0).mean():.1%}")
    print(f"Output: {out_path}")


if __name__ == "__main__":
    main()
