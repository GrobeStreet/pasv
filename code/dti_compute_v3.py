"""
DTI v0.1.1 computation engine for the v3 ingest schema.

Three layers:
  - DTI_poss: per-possession score = (PPP_actual - league_baseline) for
              attributable possessions only (defender_id > 0).
  - DTI_def:  per-defender. For each defender targeted via shooting-foul
              attribution >= MIN_TARGETED times, computes PPP_against
              and (PPP_against - league_baseline) per 100 targeted poss.
  - DTI_hunt: per-offensive-player. For each hunter with >= MIN_HUNT
              hunting attempts, computes raw PPP against
              vulnerable-target defenders (DTI_def > +0.05).

This is the v3-schema-compatible companion to dti_compute.py. The
v3-fallback path doesn't yet have action-type κ multipliers — those
are v0.2 work.
"""
import os
import argparse
from pathlib import Path
import pandas as pd
import numpy as np

# Defender-name resolution
try:
    from nba_api.stats.endpoints import commonallplayers
    _can_resolve_names = True
except Exception:
    _can_resolve_names = False


import os as _os
MIN_TARGETED_POSS = int(_os.environ.get("DTI_MIN_TARGETED", "25"))
MIN_HUNT_ATTEMPTS = int(_os.environ.get("DTI_MIN_HUNT", "10"))
VULNERABLE_THRESHOLD = 0.05  # PPP above baseline


def resolve_player_names(player_ids):
    """Map player_id -> name using nba_api commonallplayers."""
    if not _can_resolve_names:
        return {pid: f"Player_{pid}" for pid in player_ids}
    try:
        df = commonallplayers.CommonAllPlayers(
            is_only_current_season=0, league_id="00", timeout=60
        ).get_data_frames()[0]
        name_map = dict(zip(df["PERSON_ID"].astype(int), df["DISPLAY_FIRST_LAST"]))
        return {pid: name_map.get(int(pid), f"Player_{pid}") for pid in player_ids}
    except Exception as exc:
        print(f"name resolution failed: {exc}")
        return {pid: f"Player_{pid}" for pid in player_ids}


def compute_dti_def(df: pd.DataFrame, league_ppp: float):
    """Aggregate per-defender. Only uses possessions with attributed defender."""
    attrib = df[df["primary_defensive_player_id"] > 0].copy()
    grp = attrib.groupby("primary_defensive_player_id").agg(
        possessions_targeted=("points", "count"),
        points_against=("points", "sum"),
    )
    grp["PPP_against"] = grp["points_against"] / grp["possessions_targeted"]
    grp["DTI_def_per_poss"] = grp["PPP_against"] - league_ppp
    grp["DTI_def_per_100"] = grp["DTI_def_per_poss"] * 100
    # Filter
    qualified = grp[grp["possessions_targeted"] >= MIN_TARGETED_POSS].copy()
    qualified = qualified.sort_values("DTI_def_per_100", ascending=False)
    qualified.reset_index(inplace=True)
    qualified.rename(columns={"primary_defensive_player_id": "defender_id"}, inplace=True)
    return qualified


def compute_dti_hunt(df: pd.DataFrame, dti_def_df: pd.DataFrame, league_ppp: float):
    """Aggregate per-hunter. Hunter = offensive player attacking a defender
    with DTI_def > +0.05 (i.e., 'vulnerable target')."""
    vulnerable_ids = set(
        dti_def_df[dti_def_df["DTI_def_per_poss"] > VULNERABLE_THRESHOLD]["defender_id"]
    )
    hunting = df[
        (df["primary_defensive_player_id"].isin(vulnerable_ids))
        & (df["primary_offensive_player_id"] > 0)
    ].copy()
    grp = hunting.groupby("primary_offensive_player_id").agg(
        hunt_attempts=("points", "count"),
        points_when_hunting=("points", "sum"),
    )
    grp["PPP_when_hunting"] = grp["points_when_hunting"] / grp["hunt_attempts"]
    grp["DTI_hunt_vs_league"] = grp["PPP_when_hunting"] - league_ppp
    qualified = grp[grp["hunt_attempts"] >= MIN_HUNT_ATTEMPTS].copy()
    qualified = qualified.sort_values("PPP_when_hunting", ascending=False)
    qualified.reset_index(inplace=True)
    qualified.rename(columns={"primary_offensive_player_id": "hunter_id"}, inplace=True)
    return qualified


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--parquet", required=True)
    p.add_argument("--out-dir", default=None)
    p.add_argument("--label", default="2024-25_Playoffs")
    args = p.parse_args()

    out_dir = Path(args.out_dir or os.environ.get("DTI_DATA_DIR", "/tmp/dti_data"))
    out_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_parquet(args.parquet)
    print(f"Loaded {len(df):,} possessions from {args.parquet}")

    league_ppp = df["points"].sum() / len(df)
    print(f"League PPP baseline: {league_ppp:.4f}")

    # Per-defender
    dti_def_df = compute_dti_def(df, league_ppp)
    print(f"\nDTI_def: {len(dti_def_df)} qualified defenders (>= {MIN_TARGETED_POSS} targeted poss)")

    # Per-hunter
    dti_hunt_df = compute_dti_hunt(df, dti_def_df, league_ppp)
    print(f"DTI_hunt: {len(dti_hunt_df)} qualified hunters (>= {MIN_HUNT_ATTEMPTS} hunt attempts)")

    # Resolve names
    all_ids = list(set(dti_def_df["defender_id"].tolist() + dti_hunt_df["hunter_id"].tolist()))
    print(f"\nResolving {len(all_ids)} player names...")
    name_map = resolve_player_names(all_ids)
    dti_def_df["player_name"] = dti_def_df["defender_id"].map(name_map)
    dti_hunt_df["player_name"] = dti_hunt_df["hunter_id"].map(name_map)

    # Order columns
    dti_def_df = dti_def_df[[
        "player_name", "defender_id", "possessions_targeted",
        "points_against", "PPP_against", "DTI_def_per_poss", "DTI_def_per_100"
    ]]
    dti_hunt_df = dti_hunt_df[[
        "player_name", "hunter_id", "hunt_attempts",
        "points_when_hunting", "PPP_when_hunting", "DTI_hunt_vs_league"
    ]]

    # Save
    def_path = out_dir / f"DTI_def_leaderboard_{args.label}.csv"
    hunt_path = out_dir / f"DTI_hunt_leaderboard_{args.label}.csv"
    dti_def_df.to_csv(def_path, index=False)
    dti_hunt_df.to_csv(hunt_path, index=False)
    print(f"\nSaved:\n  {def_path}\n  {hunt_path}")

    # Print top 20 of each
    print("\n=== TOP 20 MOST-HUNTED DEFENDERS (highest DTI_def — they surrender PPP) ===")
    print(dti_def_df.head(20).to_string(index=False))

    print("\n=== BOTTOM 15 (HUNT-PROOF DEFENDERS — they suppress PPP) ===")
    print(dti_def_df.tail(15).to_string(index=False))

    print("\n=== TOP 20 HUNTERS (highest PPP vs. vulnerable targets) ===")
    print(dti_hunt_df.head(20).to_string(index=False))


if __name__ == "__main__":
    main()
