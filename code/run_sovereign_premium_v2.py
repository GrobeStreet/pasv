"""
Sovereign Premium v0.2 — Lineup-aware Sovereign Exception test.

Improves v0.1 by:
  1. Using true 5-defender lineup product for V_L (not single-defender proxy)
  2. Per-player "Sovereign Premium" metric: realized PPP - xPTS on math-unjustified shots
  3. Multi-season lineup pool (5 playoffs, 66K possessions with full lineups)

Sovereign Premium identifies players who CONVERT math-unjustified shots above
baseline — the empirical foundation of the Sovereign Exception clause.
"""
import os
from pathlib import Path
import pandas as pd
import numpy as np

DTI_MAX = 18.6
DTI_MIN = -13.4


def compute_p_i(dti_def_per_100):
    center = (DTI_MAX + DTI_MIN) / 2
    half = (DTI_MAX - DTI_MIN) / 2
    norm = (dti_def_per_100 - center) / half
    return 0.75 - 0.20 * norm


def main():
    data_dir = Path(os.environ.get("DTI_DATA_DIR", "/tmp/dti_data"))

    # Load the multi-season lineup parquet
    parquet = data_dir / "poss_v3_LINEUPS_MULTI_5playoffs.parquet"
    df = pd.read_parquet(parquet)
    print(f"Loaded {len(df):,} possessions from {parquet.name}")

    # Load DTI_def map
    lb = pd.read_csv(data_dir / "DTI_def_leaderboard_CANON_FINAL_n200.csv")
    dti_def_map = dict(zip(lb["defender_id"], lb["DTI_def_per_100"]))
    p_i_map = {pid: compute_p_i(dti) for pid, dti in dti_def_map.items()}
    league_p_default = 0.75

    # Filter to shots with 5-defender lineup
    all_shots = df[df["action_type"].isin(["Made Shot", "Missed Shot"])].copy()
    print(f"Total FG attempts: {len(all_shots):,}")

    # Build zone-based xPTS table from full league
    league_3pt = all_shots[all_shots["shot_outcome"].isin(["made_3", "missed_3"])]
    league_2pt = all_shots[all_shots["shot_outcome"].isin(["made_2", "missed_2"])]
    pct_3 = (league_3pt["shot_outcome"] == "made_3").mean()
    pct_2 = (league_2pt["shot_outcome"] == "made_2").mean()
    xpts_3, xpts_2 = pct_3 * 3, pct_2 * 2
    print(f"League 3PT% = {pct_3:.3f}, xPTS(3) = {xpts_3:.3f}")
    print(f"League 2PT% = {pct_2:.3f}, xPTS(2) = {xpts_2:.3f}")

    # Distance-based xPTS table
    with_dist = all_shots.dropna(subset=["shot_distance"]).copy()
    def assign_zone(d):
        if pd.isna(d): return "unknown"
        d = float(d)
        if d <= 3: return "at_rim"
        if d <= 8: return "short_paint"
        if d <= 14: return "mid"
        if d <= 22: return "long_mid"
        if d <= 27: return "3pt"
        return "long_3"
    with_dist["zone"] = with_dist["shot_distance"].apply(assign_zone)
    with_dist["is_3"] = with_dist["shot_outcome"].isin(["made_3", "missed_3"])
    with_dist["made"] = with_dist["shot_outcome"].isin(["made_2", "made_3"])
    zt = with_dist.groupby("zone").agg(
        fg_pct=("made", "mean"),
        avg_val=("is_3", lambda x: x.mean() * 3 + (1 - x.mean()) * 2),
    )
    zt["xpts"] = zt["fg_pct"] * zt["avg_val"]
    print(f"\n=== Zone xPTS ===")
    print(zt.round(3))
    zone_xpts = {z: float(x) for z, x in zt["xpts"].items()}

    # Filter to lineup-aware shots
    shots = all_shots[all_shots["def_lineup_ids"].apply(lambda x: len(x) == 5)].copy()
    print(f"\nLineup-aware shots: {len(shots):,}")

    # Assign zone + xPTS_shot
    shots["zone"] = shots["shot_distance"].apply(assign_zone)
    shots["xPTS_shot"] = shots["zone"].map(zone_xpts)
    fallback = np.where(
        shots["shot_outcome"].isin(["made_3", "missed_3"]), xpts_3, xpts_2
    )
    shots["xPTS_shot"] = shots["xPTS_shot"].fillna(pd.Series(fallback, index=shots.index))

    # LINEUP-AWARE V_L (using true 5-defender product)
    def lineup_product(ids):
        prod = 1.0
        for pid in ids:
            prod *= p_i_map.get(int(pid), league_p_default)
        return prod
    shots["p_product"] = shots["def_lineup_ids"].apply(lineup_product)
    league_xpts_avg = all_shots["points"].sum() / len(all_shots)
    contested_baseline = 0.85
    shots["V_L_lineup"] = (
        league_xpts_avg * (1 - shots["p_product"])
        + contested_baseline * shots["p_product"]
    )

    # Sovereign classification
    shots["justified"] = shots["xPTS_shot"] >= shots["V_L_lineup"]
    shots["unjustified"] = ~shots["justified"]

    print(f"\n=== AGGREGATE (lineup-aware) ===")
    print(f"Total lineup-aware shots: {len(shots):,}")
    print(f"Justified: {shots['justified'].sum():,} ({shots['justified'].mean():.1%})")
    print(f"Unjustified: {shots['unjustified'].sum():,} ({shots['unjustified'].mean():.1%})")
    print(f"PPP on justified: {shots[shots.justified]['points'].mean():.3f}")
    print(f"PPP on unjustified: {shots[shots.unjustified]['points'].mean():.3f}")
    print(f"xPTS on unjustified: {shots[shots.unjustified]['xPTS_shot'].mean():.3f}")

    # SOVEREIGN PREMIUM: per-player realized PPP - xPTS on UNJUSTIFIED shots only
    unj = shots[shots.unjustified].copy()
    unj["sovereign_pts_over_xpts"] = unj["points"] - unj["xPTS_shot"]
    by_player = unj.groupby("primary_offensive_player_id").agg(
        n_unjustified=("xPTS_shot", "count"),
        avg_realized=("points", "mean"),
        avg_xpts=("xPTS_shot", "mean"),
        sovereign_premium=("sovereign_pts_over_xpts", "mean"),
    )
    qualified = by_player[by_player["n_unjustified"] >= 50].copy()
    qualified = qualified.sort_values("sovereign_premium", ascending=False)
    print(f"\nQualified Sovereign-candidates (n_unjustified ≥ 50): {len(qualified)}")

    # Resolve names
    try:
        from nba_api.stats.endpoints import commonallplayers
        cdf = commonallplayers.CommonAllPlayers(is_only_current_season=0, league_id="00", timeout=60).get_data_frames()[0]
        name_map = dict(zip(cdf["PERSON_ID"].astype(int), cdf["DISPLAY_FIRST_LAST"]))
        qualified["name"] = qualified.index.map(lambda x: name_map.get(int(x), f"Player_{x}"))
    except Exception as e:
        print(f"name resolution failed: {e}")
        qualified["name"] = qualified.index.map(lambda x: f"Player_{x}")

    out = data_dir / "Sovereign_Premium_v0.2_5playoffs.csv"
    qualified.reset_index().to_csv(out, index=False)
    print(f"\nSaved: {out}")

    print(f"\n=== TOP 30 SOVEREIGN PREMIUM (highest pts above xPTS on math-unjustified shots) ===")
    print(qualified.head(30)[["name", "n_unjustified", "avg_realized", "avg_xpts", "sovereign_premium"]].round(3).to_string())

    print(f"\n=== BOTTOM 15 SOVEREIGN PREMIUM (worst pts vs xPTS — should NOT take math-unjustified shots) ===")
    print(qualified.tail(15)[["name", "n_unjustified", "avg_realized", "avg_xpts", "sovereign_premium"]].round(3).to_string())


if __name__ == "__main__":
    main()
