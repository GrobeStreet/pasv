"""
Chunked ingest — pulls a range of game indices then writes to a chunked
parquet. Designed to fit inside sandbox-friendly timeouts. Combine chunks
later with `combine_chunks.py`.
"""
import os, sys, time, argparse
from pathlib import Path
import pandas as pd
from tqdm import tqdm
from dti_ingest_v3 import (
    list_playoff_game_ids,
    list_regular_season_game_ids,
    fetch_pbp_v3,
    extract_possessions_v3,
)

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--season", required=True)
    p.add_argument("--season-type", default="Playoffs")
    p.add_argument("--start", type=int, default=0)
    p.add_argument("--end", type=int, required=True)
    p.add_argument("--out-dir", default=None)
    args = p.parse_args()

    out_dir = Path(args.out_dir or os.environ.get("DTI_DATA_DIR", "/tmp/dti_data"))
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.season_type == "Playoffs":
        game_ids = list_playoff_game_ids(args.season)
    else:
        game_ids = list_regular_season_game_ids(args.season)
    game_ids = game_ids[args.start:args.end]

    rows = []
    failed = 0
    for gid in tqdm(game_ids, desc=f"chunk {args.start}-{args.end}"):
        pbp = fetch_pbp_v3(gid)
        if pbp is None:
            failed += 1
            continue
        rows.extend(extract_possessions_v3(pbp))
        time.sleep(0.2)

    df = pd.DataFrame(rows)
    df["season"] = args.season
    df["season_type"] = args.season_type
    safe = args.season_type.replace(" ", "_")
    out = out_dir / f"poss_v3_{args.season}_{safe}_chunk_{args.start}_{args.end}.parquet"
    df.to_parquet(out, index=False)
    print(f"\n{len(df)} possessions, {failed} failed → {out}")

if __name__ == "__main__":
    main()
