"""
run_dti_compute.py — DTI Leaderboard Runner
==========================================

Consumes the possession-level parquet emitted by the ingest pipeline,
runs the three DTI layers, and writes the three leaderboard CSVs Bobby
uses for the Substack draft + the validation desk.

Usage
-----
    python run_dti_compute.py --season 2025-26 --season-type Playoffs

Outputs (written to ../dti_data/ by default)
--------------------------------------------
    defender_leaderboard_<season>_<season_type>.csv   (top 30 hunted)
    hunter_leaderboard_<season>_<season_type>.csv     (top 30 hunters)
    top_possessions_<season>_<season_type>.csv        (top 100 poss)
    validation_<season>_<season_type>.csv             (known-target check)

Author : Bobby Morong / DataDunkNBA
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

# Allow `python run_dti_compute.py` from the code/ directory.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from dti_compute import (  # noqa: E402
    compute_dti_def,
    compute_dti_hunt,
    compute_dti_poss,
    load_baseline,
    load_possessions,
    validate_against_known_targets,
)


DEFAULT_DATA_DIR = (
    Path(__file__).resolve().parents[2] / "dti_data"
)


def _slug(season: str, season_type: str) -> str:
    return f"{season}_{season_type.replace(' ', '_')}"


def _safe_top(df: pd.DataFrame, n: int) -> pd.DataFrame:
    return df.head(n).copy() if len(df) else df.copy()


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Compute DTI leaderboards from a possession-level "
                    "parquet ingest."
    )
    ap.add_argument(
        "--season", required=True,
        help="Season string used by the ingest, e.g. '2025-26'.",
    )
    ap.add_argument(
        "--season-type", default="Playoffs",
        choices=("Regular Season", "Playoffs", "All"),
        help="Filter the possession data to this season type.",
    )
    ap.add_argument(
        "--data-dir", type=Path, default=DEFAULT_DATA_DIR,
        help="Directory containing the ingest parquet files and where the "
             "leaderboard CSVs will be written. "
             f"Default: {DEFAULT_DATA_DIR}",
    )
    ap.add_argument(
        "--poss-parquet", type=Path, default=None,
        help="Override the possession-level parquet path. Default: "
             "<data-dir>/poss_level_<season>.parquet",
    )
    ap.add_argument(
        "--baseline-parquet", type=Path, default=None,
        help="Override the baseline parquet path. Default: "
             "<data-dir>/baseline_<season>.parquet",
    )
    ap.add_argument(
        "--min-targeted-possessions", type=int, default=200,
        help="Minimum possessions to qualify for the defender "
             "leaderboard. Default 200.",
    )
    ap.add_argument(
        "--min-hunting-possessions", type=int, default=150,
        help="Minimum hunting possessions to qualify for the hunter "
             "leaderboard. Default 150.",
    )
    ap.add_argument(
        "--top-n", type=int, default=30,
        help="Number of leaderboard rows to write per layer. Default 30.",
    )
    ap.add_argument(
        "--top-possessions", type=int, default=100,
        help="Number of top DTI_poss rows to write. Default 100.",
    )
    args = ap.parse_args()

    data_dir: Path = args.data_dir
    data_dir.mkdir(parents=True, exist_ok=True)

    poss_path = (
        args.poss_parquet
        or data_dir / f"poss_level_{args.season}.parquet"
    )
    baseline_path = (
        args.baseline_parquet
        or data_dir / f"baseline_{args.season}.parquet"
    )

    if not poss_path.exists():
        print(
            f"[ERROR] Possession-level parquet not found at {poss_path}. "
            "Run the ingest first.",
            file=sys.stderr,
        )
        return 2
    if not baseline_path.exists():
        print(
            f"[ERROR] Baseline parquet not found at {baseline_path}. "
            "Run the ingest first.",
            file=sys.stderr,
        )
        return 2

    print(f"[load] {poss_path}")
    poss_df = load_possessions(poss_path)
    print(f"[load] {baseline_path}")
    baseline_df = load_baseline(baseline_path)

    if args.season_type != "All" and "season_type" in poss_df.columns:
        before = len(poss_df)
        poss_df = poss_df[poss_df["season_type"] == args.season_type].copy()
        print(
            f"[filter] season_type={args.season_type!r}: "
            f"{before:,} -> {len(poss_df):,} possessions"
        )

    print(f"[compute] DTI_poss over {len(poss_df):,} possessions")
    poss_dti = compute_dti_poss(poss_df, baseline_df)

    print("[compute] DTI_def — defender leaderboard")
    def_lb = compute_dti_def(
        poss_dti,
        min_targeted_possessions=args.min_targeted_possessions,
    )

    print("[compute] DTI_hunt — hunter leaderboard")
    hunt_lb = compute_dti_hunt(
        poss_dti,
        min_hunting_possessions=args.min_hunting_possessions,
    )

    print("[compute] validation against known 2026 hunt-targets")
    validation = validate_against_known_targets(def_lb, top_n=args.top_n)

    # ----- write outputs -----
    slug = _slug(args.season, args.season_type)

    def_path = data_dir / f"defender_leaderboard_{slug}.csv"
    hunt_path = data_dir / f"hunter_leaderboard_{slug}.csv"
    poss_path_out = data_dir / f"top_possessions_{slug}.csv"
    val_path = data_dir / f"validation_{slug}.csv"

    _safe_top(def_lb, args.top_n).to_csv(
        def_path, index=False, float_format="%.4f"
    )
    _safe_top(hunt_lb, args.top_n).to_csv(
        hunt_path, index=False, float_format="%.4f"
    )

    top_poss = poss_dti.sort_values("DTI_poss", ascending=False).head(
        args.top_possessions
    )
    top_poss.to_csv(poss_path_out, index=False, float_format="%.4f")

    validation.to_csv(val_path, index=False, float_format="%.4f")

    print(f"[write] {def_path}")
    print(f"[write] {hunt_path}")
    print(f"[write] {poss_path_out}")
    print(f"[write] {val_path}")

    # ----- summary -----
    print("\n========== DTI v0.1 Summary ==========")
    print(f"Season: {args.season}    Season type: {args.season_type}")
    print(
        f"Hunting flag source: "
        f"{hunt_lb.attrs.get('hunting_flag_source', 'unknown')}"
    )

    if len(def_lb):
        top5_def = def_lb.head(5)[["defender_name", "DTI_def_per100"]]
        print("\nTop 5 most-hunted defenders (DTI_def_per100):")
        for _, row in top5_def.iterrows():
            print(
                f"  {row['defender_name']:<28s}  "
                f"{row['DTI_def_per100']:+.2f}"
            )
    else:
        print("\nTop 5 most-hunted defenders: (none qualified)")

    if len(hunt_lb):
        top5_hunt = hunt_lb.head(5)[["hunter_name", "DTI_hunt_per100"]]
        print("\nTop 5 most-effective hunters (DTI_hunt_per100):")
        for _, row in top5_hunt.iterrows():
            print(
                f"  {row['hunter_name']:<28s}  "
                f"{row['DTI_hunt_per100']:+.2f}"
            )
    else:
        print("\nTop 5 most-effective hunters: (none qualified)")

    print("\nValidation against known 2026 hunt-targets:")
    if len(validation):
        for _, row in validation.iterrows():
            tag = "FOUND" if row["in_top_n"] else "MISS "
            rank = (
                f"#{int(row['observed_rank']):<3d}"
                if pd.notna(row["observed_rank"]) else "n/a "
            )
            print(
                f"  [{tag}] {row['player_name']:<22s} "
                f"rank={rank}  "
                f"DTI_def/100={row['observed_DTI_def_per100']:+.2f}"
            )
    else:
        print("  (no targets to validate)")
    print("=======================================\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
