"""
DTI v0.1 Ingest Runner
======================

End-to-end CLI for Bobby's DTI substrate build. Invocation:

    python run_dti_ingest.py --season 2025-26 --season-type Playoffs

What it does:
    1. Ensures pbpstats (and tqdm) are installed; offers nba_api fallback.
    2. Pulls every game for the season + season_type from stats.nba.com
       (cached as JSON in dti_data/pbpstats_response_cache/).
    3. Extracts possession-level rows and writes a parquet to
       dti_data/poss_level_<season>_<season_type_slug>.parquet.
    4. Prints a summary: possessions ingested, unique games, unique
       players, defender-resolution rate.

Expected runtime:
    - 30-60 min for a full Regular Season (~1230 games).
    - 5-15 min for a Playoffs run (60-105 games).
    - First run is slower (cold cache); re-runs hit the cache and finish
      in ~1/3 the time.

Author: Bobby Morong / DataDunkNBA — sole author
License: MIT
"""

from __future__ import annotations

import argparse
import importlib
import logging
import subprocess
import sys
import time
from pathlib import Path


# -----------------------------------------------------------------------------
# Dependency bootstrap
# -----------------------------------------------------------------------------
REQUIRED = ["pbpstats", "tqdm", "pandas", "pyarrow"]
OPTIONAL_FALLBACK = ["nba_api"]


def _pip_install(packages):
    cmd = [sys.executable, "-m", "pip", "install", "--quiet", *packages]
    print(f"[bootstrap] Installing: {' '.join(packages)}")
    subprocess.check_call(cmd)


def ensure_dependencies():
    missing = []
    for pkg in REQUIRED:
        try:
            importlib.import_module(pkg)
        except ImportError:
            missing.append(pkg)
    if missing:
        _pip_install(missing)

    # Optional fallback — only install if pbpstats import truly fails downstream
    for pkg in OPTIONAL_FALLBACK:
        try:
            importlib.import_module(pkg)
        except ImportError:
            try:
                _pip_install([pkg])
            except subprocess.CalledProcessError:
                print(f"[bootstrap] optional fallback {pkg} install failed — continuing")


# -----------------------------------------------------------------------------
# CLI
# -----------------------------------------------------------------------------
def parse_args():
    parser = argparse.ArgumentParser(
        description="Run the DTI v0.1 possession-level ingest."
    )
    parser.add_argument(
        "--season", required=True,
        help="Season string, e.g., '2025-26'.",
    )
    parser.add_argument(
        "--season-type", default="Regular Season",
        choices=["Regular Season", "Playoffs", "Play In"],
        help="Season type (default: Regular Season).",
    )
    parser.add_argument(
        "--out-dir", type=Path,
        default=Path("/Users/robertmorong/Documents/Claude/Projects/Basketball Stats Book/dti_data"),
        help="Parquet output directory.",
    )
    parser.add_argument(
        "--max-games", type=int, default=None,
        help="Cap games for dry-run / smoke test.",
    )
    parser.add_argument(
        "--sleep-between-games", type=float, default=0.6,
        help="Polite sleep between game fetches (seconds).",
    )
    parser.add_argument(
        "--verbose", action="store_true",
        help="Enable DEBUG logging from dti_ingest.",
    )
    return parser.parse_args()


def slugify(s: str) -> str:
    return s.lower().replace(" ", "_")


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------
def main():
    args = parse_args()
    ensure_dependencies()

    # Import here, after install
    sys.path.insert(0, str(Path(__file__).parent))
    from dti_ingest import (
        ingest_season,
        compute_expected_PPP_baseline,
        save_to_parquet,
        summarize,
    )

    if args.verbose:
        logging.getLogger("dti_ingest").setLevel(logging.DEBUG)

    t0 = time.time()
    print(
        f"[run] Starting DTI ingest — season={args.season} "
        f"season_type={args.season_type} out_dir={args.out_dir}"
    )

    df = ingest_season(
        season_str=args.season,
        season_type=args.season_type,
        max_games=args.max_games,
        sleep_between_games=args.sleep_between_games,
    )

    elapsed_min = (time.time() - t0) / 60.0
    print(f"[run] Ingest complete in {elapsed_min:.1f} min.")

    if df.empty:
        print("[run] WARNING: empty DataFrame — nothing to write. Bailing out.")
        sys.exit(1)

    parquet_name = f"poss_level_{args.season}_{slugify(args.season_type)}.parquet"
    parquet_path = args.out_dir / parquet_name
    written = save_to_parquet(df, parquet_path)
    print(f"[run] Wrote possession-level table → {written}")

    # Baseline by action type — used by downstream DTI compute
    baseline = compute_expected_PPP_baseline(df)
    baseline_path = args.out_dir / f"expected_ppp_baseline_{args.season}_{slugify(args.season_type)}.csv"
    baseline.to_csv(baseline_path, index=False, float_format="%.4f")
    print(f"[run] Wrote action-type baseline → {baseline_path}")

    # Summary line
    summary = summarize(df)
    print("[run] Summary:")
    for k, v in summary.items():
        print(f"        {k}: {v}")
    print("[run] Done.")


if __name__ == "__main__":
    main()
