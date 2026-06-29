#!/bin/bash
# Full Regular-Season DTI Ingest — Bobby Local Runner
#
# Runs the chunked PlayByPlayV3 ingest for all 2024-25 + 2025-26 RS games.
# ~1,230 games per season * 2 = 2,460 games total. Expected runtime: 30-45 min.
# At ~2.5 games/sec we burn through ~150 games per minute.
#
# Run from: pasv-sloan-repo/code/
# Usage:    bash run_full_rs_ingest.sh

set -e

cd "$(dirname "$0")"

DATA_DIR="$(cd ../../dti_data 2>/dev/null || mkdir -p ../../dti_data && cd ../../dti_data && pwd)"
export DTI_DATA_DIR="$DATA_DIR"

echo "==> Output directory: $DATA_DIR"
echo "==> Starting full RS ingest at $(date)"

# Smaller chunks (60 games each) to fit polite rate limiting and avoid API hangs
# Total chunks: 21 per season * 2 seasons = 42 chunks
# Per chunk: ~30s -> ~21 min total

run_chunk() {
    local season="$1"
    local start="$2"
    local end="$3"
    local out="$DATA_DIR/poss_v3_${season}_Regular_Season_chunk_${start}_${end}.parquet"

    if [ -f "$out" ]; then
        echo "    [skip] $season chunk $start-$end already exists"
        return 0
    fi

    echo "    [run]  $season chunk $start-$end"
    python dti_ingest_v3_batched.py \
        --season "$season" \
        --season-type "Regular Season" \
        --start "$start" \
        --end "$end" 2>&1 | tail -1
}

# 2024-25 RS — 1,230 games -> 21 chunks of 60
echo "==> 2024-25 RS ingest"
for start in 0 60 120 180 240 300 360 420 480 540 600 660 720 780 840 900 960 1020 1080 1140 1200; do
    end=$((start + 60))
    if [ "$end" -gt 1230 ]; then end=1230; fi
    run_chunk "2024-25" "$start" "$end"
done

# 2025-26 RS — 1,230 games -> 21 chunks of 60
echo "==> 2025-26 RS ingest"
for start in 0 60 120 180 240 300 360 420 480 540 600 660 720 780 840 900 960 1020 1080 1140 1200; do
    end=$((start + 60))
    if [ "$end" -gt 1230 ]; then end=1230; fi
    run_chunk "2025-26" "$start" "$end"
done

# Combine chunks into per-season files
echo "==> Combining chunks..."
python <<'PYEOF'
import pandas as pd, glob, os
data_dir = os.environ["DTI_DATA_DIR"]
for season in ["2024-25", "2025-26"]:
    chunks = sorted(glob.glob(f"{data_dir}/poss_v3_{season}_Regular_Season_chunk_*.parquet"))
    if not chunks:
        print(f"  No chunks for {season}")
        continue
    df = pd.concat([pd.read_parquet(c) for c in chunks], ignore_index=True)
    out = f"{data_dir}/poss_v3_{season}_Regular_Season.parquet"
    df.to_parquet(out, index=False)
    print(f"  {season}: {len(df):,} possessions, {df.game_id.nunique()} games -> {out}")

# Build the MEGA pooled parquet (5 Playoffs + 2 RS = ~600,000 possessions)
files = [
    f"{data_dir}/poss_v3_MULTI_5seasons_Playoffs.parquet",
    f"{data_dir}/poss_v3_2024-25_Regular_Season.parquet",
    f"{data_dir}/poss_v3_2025-26_Regular_Season.parquet",
]
loaded = []
for f in files:
    if os.path.exists(f):
        loaded.append(pd.read_parquet(f))
        print(f"  loaded {f}: {len(loaded[-1]):,}")
mega = pd.concat(loaded, ignore_index=True)
mega_out = f"{data_dir}/poss_v3_CANON_5playoffs_2RS.parquet"
mega.to_parquet(mega_out, index=False)
print(f"\nCANON pooled: {len(mega):,} possessions, {mega.game_id.nunique()} games")
print(f"Output: {mega_out}")
PYEOF

# Compute the canon leaderboards
echo "==> Computing canon leaderboards..."
DTI_MIN_TARGETED=800 DTI_MIN_HUNT=300 python dti_compute_v3.py \
    --parquet "$DATA_DIR/poss_v3_CANON_5playoffs_2RS.parquet" \
    --label "CANON_5playoffs_2RS" 2>&1 | tail -60

# Also dump a leaner n>=300 cut for the publishable leaderboard
DTI_MIN_TARGETED=300 DTI_MIN_HUNT=100 python dti_compute_v3.py \
    --parquet "$DATA_DIR/poss_v3_CANON_5playoffs_2RS.parquet" \
    --label "CANON_n300" 2>&1 | tail -60

echo ""
echo "==> Done at $(date)"
echo "==> Canon-grade leaderboards: $DATA_DIR/DTI_def_leaderboard_CANON_*"
