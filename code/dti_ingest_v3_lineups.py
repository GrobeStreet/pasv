"""
DTI v0.2 — Lineup-aware ingest module.

Adds 5-defender lineup tracking via PlayByPlayV3 substitution events +
boxscoretraditionalv3 starting-5. Outputs lineup-augmented parquet with
two new columns: off_lineup_ids (tuple of 5 player IDs on offense at
moment of terminal action) and def_lineup_ids (tuple of 5 on defense).

Per-game runtime: ~3-4 seconds (vs 2-3s for v3). Roughly +50% over v3.
"""
from __future__ import annotations
import os
import time
import logging
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Set

import pandas as pd
from tqdm import tqdm
from nba_api.stats.endpoints import (
    leaguegamefinder,
    playbyplayv3,
    boxscoretraditionalv3,
)

# Reuse the v3 ingest logic
from dti_ingest_v3 import (
    list_playoff_game_ids,
    list_regular_season_game_ids,
    extract_possessions_v3,
)

logger = logging.getLogger("dti_ingest_v3_lineups")
if not logger.handlers:
    h = logging.StreamHandler()
    h.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s %(name)s — %(message)s"))
    logger.addHandler(h)
    logger.setLevel(logging.INFO)


def fetch_game_data(game_id: str, retries: int = 3):
    """Fetch PBP + boxscore for one game with retries."""
    pbp_df, box_df = None, None
    for attempt in range(retries):
        try:
            pbp_df = playbyplayv3.PlayByPlayV3(game_id=game_id, timeout=45).get_data_frames()[0]
            break
        except Exception as exc:
            if attempt == retries - 1:
                logger.warning(f"PBP fetch failed {game_id}: {exc}")
                return None, None
            time.sleep(2 ** attempt)
    for attempt in range(retries):
        try:
            box_df = boxscoretraditionalv3.BoxScoreTraditionalV3(game_id=game_id, timeout=45).get_data_frames()[0]
            break
        except Exception as exc:
            if attempt == retries - 1:
                logger.warning(f"BOX fetch failed {game_id}: {exc}")
                return pbp_df, None
            time.sleep(2 ** attempt)
    return pbp_df, box_df


def get_starting_fives(box_df: pd.DataFrame) -> Dict[int, Set[int]]:
    """Return {team_id: set of 5 starting player_ids} from boxscore."""
    starters_df = box_df[box_df["position"].notna() & (box_df["position"] != "")]
    return {
        int(team_id): set(grp["personId"].astype(int).tolist())
        for team_id, grp in starters_df.groupby("teamId")
    }


def build_name_to_id_map(box_df: pd.DataFrame) -> Dict[int, Dict[str, int]]:
    """Build per-team {familyName_lower: personId} map for sub-description parsing."""
    name_map: Dict[int, Dict[str, int]] = {}
    for _, row in box_df.iterrows():
        team_id = int(row["teamId"])
        family = str(row.get("familyName", "")).strip().lower()
        if not family:
            continue
        name_map.setdefault(team_id, {})[family] = int(row["personId"])
    return name_map


SUB_RE = re.compile(r"SUB:\s+(\S+(?:\s\S+)*?)\s+FOR\s+(\S+(?:\s\S+)*)", re.IGNORECASE)


def parse_sub(description: str) -> Optional[Tuple[str, str]]:
    """Parse 'SUB: <In> FOR <Out>' → (in_name_lower, out_name_lower)."""
    m = SUB_RE.search(description or "")
    if not m:
        return None
    in_name = m.group(1).strip().lower()
    out_name = m.group(2).strip().lower()
    return in_name, out_name


def attribute_team_to_possession(
    poss_row: Dict[str, Any], lineup_off: Set[int], lineup_def: Set[int]
) -> Tuple[Tuple[int, ...], Tuple[int, ...]]:
    """Determine which lineup is offense and which is defense for this possession.
    The poss already has offensive_team_id. We just need to return both as tuples.
    """
    return tuple(sorted(lineup_off)), tuple(sorted(lineup_def))


def walk_lineups(
    pbp_df: pd.DataFrame, starting_fives: Dict[int, Set[int]], name_to_id: Dict[int, Dict[str, int]]
) -> Dict[int, Tuple[int, ...]]:
    """Walk the PBP per-period, tracking the on-court lineup for each team.
    Returns a list of (action_id, {team_id: 5-tuple}) snapshots — one per terminal event.
    Actually returns a dict: {actionNumber: {team_id: 5-tuple}} for fast lookup downstream.
    """
    pbp_df = pbp_df.sort_values(["period", "actionNumber"]).reset_index(drop=True)
    snapshots: Dict[int, Dict[int, Tuple[int, ...]]] = {}

    # Track current lineup per team
    team_ids = list(starting_fives.keys())
    current = {tid: set(players) for tid, players in starting_fives.items()}
    current_period = 0

    for _, ev in pbp_df.iterrows():
        period = int(ev.get("period", 0) or 0)
        # New period: reset to starters (no period-start subs in V3 means we keep current as default)
        # In practice, lineups carry through quarter breaks unless subs happen.
        # If period changes AND we hit a "period" actionType, no reset is needed because subs
        # to set the new period's starting lineup happen first.
        if period != current_period:
            current_period = period

        action_type = str(ev.get("actionType", ""))
        if action_type == "Substitution":
            team_id = int(ev.get("teamId", 0) or 0)
            out_id = int(ev.get("personId", 0) or 0)
            parsed = parse_sub(str(ev.get("description", "") or ""))
            if parsed:
                in_name, _out_name_check = parsed
                in_id = name_to_id.get(team_id, {}).get(in_name)
                if in_id is not None and team_id in current:
                    current[team_id].discard(out_id)
                    current[team_id].add(in_id)
            continue

        # Snapshot every non-sub event (cheap; downstream filters to terminal)
        snapshots[int(ev.get("actionNumber", 0) or 0)] = {
            tid: tuple(sorted(players)) for tid, players in current.items() if len(players) == 5
        }

    return snapshots


def ingest_game_with_lineups(game_id: str) -> List[Dict[str, Any]]:
    """Pull one game, build possession rows with off_lineup_ids + def_lineup_ids."""
    pbp_df, box_df = fetch_game_data(game_id)
    if pbp_df is None or box_df is None or len(pbp_df) == 0:
        return []

    starting_fives = get_starting_fives(box_df)
    if len(starting_fives) != 2 or any(len(s) != 5 for s in starting_fives.values()):
        logger.warning(f"Bad starters for {game_id}")
        return []

    name_to_id = build_name_to_id_map(box_df)

    # Walk lineups
    snapshots = walk_lineups(pbp_df, starting_fives, name_to_id)

    # Extract possessions using v3 logic
    rows = extract_possessions_v3(pbp_df)

    # Match each possession to its lineup snapshot (use terminal action's actionNumber)
    # The terminal action's actionNumber isn't directly in our row; reconstruct via game state
    # PRO TIP: the possession_number maps to terminal events in order; we need a different join
    # Since extract_possessions_v3 doesn't preserve actionNumber, let's enrich it.
    # Quick fix: re-walk PBP, match terminal events to possession rows by (period, clock, off_player)
    terminal_actions: Dict[Tuple[int, str, int], int] = {}
    pbp_df_sorted = pbp_df.sort_values(["period", "actionNumber"])
    for _, ev in pbp_df_sorted.iterrows():
        at = str(ev.get("actionType", ""))
        if at not in ("Made Shot", "Missed Shot", "Turnover", "Free Throw"):
            continue
        key = (int(ev.get("period", 0)), str(ev.get("clock", "")), int(ev.get("personId", 0) or 0))
        terminal_actions[key] = int(ev.get("actionNumber", 0) or 0)

    for row in rows:
        key = (row["period"], row["clock"], row["primary_offensive_player_id"])
        action_num = terminal_actions.get(key)
        if action_num is None or action_num not in snapshots:
            row["off_lineup_ids"] = ()
            row["def_lineup_ids"] = ()
            continue
        team_lineups = snapshots[action_num]
        off_team = row["offensive_team_id"]
        def_team = next((t for t in team_lineups if t != off_team), None)
        row["off_lineup_ids"] = team_lineups.get(off_team, ())
        row["def_lineup_ids"] = team_lineups.get(def_team, ()) if def_team else ()

    return rows


def ingest_with_lineups(season: str, season_type: str = "Playoffs",
                        start: int = 0, end: Optional[int] = None,
                        sleep: float = 0.3) -> pd.DataFrame:
    if season_type == "Playoffs":
        game_ids = list_playoff_game_ids(season)
    else:
        game_ids = list_regular_season_game_ids(season)
    game_ids = game_ids[start:end]
    logger.info(f"Lineup-ingest: {len(game_ids)} games ({season} {season_type})")

    all_rows = []
    failed = 0
    for gid in tqdm(game_ids, desc=f"v0.2 lineups {season}"):
        rows = ingest_game_with_lineups(gid)
        if not rows:
            failed += 1
            continue
        all_rows.extend(rows)
        time.sleep(sleep)

    df = pd.DataFrame(all_rows)
    df["season"] = season
    df["season_type"] = season_type
    df["ingest_version"] = "v0.2-lineups"
    df["ingest_date"] = pd.Timestamp.utcnow().date().isoformat()
    logger.info(f"v0.2 ingest done: {len(df):,} possessions, {failed} games failed")
    return df


def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--season", required=True)
    p.add_argument("--season-type", default="Playoffs")
    p.add_argument("--start", type=int, default=0)
    p.add_argument("--end", type=int, default=None)
    p.add_argument("--out-dir", default=None)
    p.add_argument("--sleep", type=float, default=0.3)
    args = p.parse_args()

    out_dir = Path(args.out_dir or os.environ.get("DTI_DATA_DIR", "/tmp/dti_data"))
    out_dir.mkdir(parents=True, exist_ok=True)

    df = ingest_with_lineups(args.season, args.season_type, args.start, args.end, args.sleep)
    if len(df) == 0:
        logger.error("Empty df")
        return

    safe = args.season_type.replace(" ", "_")
    suffix = f"_chunk_{args.start}_{args.end}" if args.end else ""
    out = out_dir / f"poss_v3_LINEUPS_{args.season}_{safe}{suffix}.parquet"
    df.to_parquet(out, index=False)
    print(f"\nWrote {out} ({len(df):,} rows)")
    print(f"With lineup coverage: {(df['def_lineup_ids'].apply(len) == 5).sum():,} ({(df['def_lineup_ids'].apply(len) == 5).mean():.1%})")


if __name__ == "__main__":
    main()
