"""
Sovereign Exception Per-Possession Test (§4.2.14 of Holding-Math Theorem v2)

Spec: A Sovereign call is justified if xPTS(shot) ≥ V*_L(s*) against the
specific lineup faced. We score every shot in the dataset:
  - xPTS(shot)   = expected points for the shot type (proxy via shot_zone)
  - V*_L(s*)     = continuation value vs. the actual defender's p_i (single-defender
                   v0.1 approximation; full lineup is v0.2)
  - Justified    = xPTS >= V*_L
  - Unjustified  = xPTS < V*_L (player should have held, not shot)

Output: per-player Sovereign-justification rate leaderboard.
"""
import os
from pathlib import Path
import pandas as pd
import numpy as np

# Same constants as v2 falsifying regression
DTI_MAX = 18.6
DTI_MIN = -13.4
P_FLOOR = 0.55
P_CEILING = 0.95


def compute_p_i(dti_def_per_100, dti_max=DTI_MAX, dti_min=DTI_MIN):
    center = (dti_max + dti_min) / 2
    half_range = (dti_max - dti_min) / 2
    norm = (dti_def_per_100 - center) / half_range
    return 0.75 - 0.20 * norm  # maps to [0.55, 0.95]


def main():
    data_dir = Path(os.environ.get("DTI_DATA_DIR", "/tmp/dti_data"))

    df = pd.read_parquet(data_dir / "poss_v3_CANON_FINAL_5playoffs_FULL_2RS.parquet")
    print(f"Loaded {len(df):,} possessions")

    # Load Canon DTI_def leaderboard
    lb = pd.read_csv(data_dir / "DTI_def_leaderboard_CANON_FINAL_n200.csv")
    dti_def_map = dict(zip(lb["defender_id"], lb["DTI_def_per_100"]))

    # Filter to FG attempts (skip turnovers, FT trips)
    all_shots = df[df["action_type"].isin(["Made Shot", "Missed Shot"])].copy()
    print(f"Total FG attempts: {len(all_shots):,}")

    # Compute LEAGUE 2PT% and 3PT% from the full shot pool (not the attributed subset)
    league_3pt_attempts = all_shots[all_shots["shot_outcome"].isin(["made_3", "missed_3"])]
    league_2pt_attempts = all_shots[all_shots["shot_outcome"].isin(["made_2", "missed_2"])]
    pct_3 = (league_3pt_attempts["shot_outcome"] == "made_3").mean()
    pct_2 = (league_2pt_attempts["shot_outcome"] == "made_2").mean()
    xpts_3 = pct_3 * 3   # ~1.08
    xpts_2 = pct_2 * 2   # ~1.10
    print(f"League 3PT%: {pct_3:.3f}, xPTS(3) = {xpts_3:.3f}")
    print(f"League 2PT%: {pct_2:.3f}, xPTS(2) = {xpts_2:.3f}")

    # Need defender attribution + DTI_def coverage
    shots = all_shots[all_shots["primary_defensive_player_id"] > 0].copy()
    shots["DTI_def_attr"] = shots["primary_defensive_player_id"].map(dti_def_map)
    shots = shots.dropna(subset=["DTI_def_attr"])
    print(f"Attributed shots with DTI_def coverage: {len(shots):,}")

    # Build distance-aware xPTS table from full league data
    # Bin shot_distance into zones; for each zone, compute league FG%; assign xPTS
    def make_distance_xpts(all_shots_df):
        # only attempts with shot_distance present
        with_dist = all_shots_df.dropna(subset=["shot_distance"]).copy()
        with_dist["zone"] = pd.cut(
            with_dist["shot_distance"],
            bins=[-0.1, 3, 8, 14, 22, 27, 50],
            labels=["at_rim", "short_paint", "mid", "long_mid", "3pt", "long_3"],
        )
        with_dist["is_3"] = with_dist["shot_outcome"].isin(["made_3", "missed_3"])
        with_dist["made"] = with_dist["shot_outcome"].isin(["made_2", "made_3"])
        zone_xpts = with_dist.groupby("zone", observed=True).agg(
            fg_pct=("made", "mean"),
            avg_value=("is_3", lambda x: x.mean() * 3 + (1 - x.mean()) * 2),
        )
        zone_xpts["xpts"] = zone_xpts["fg_pct"] * zone_xpts["avg_value"]
        return zone_xpts

    zone_table = make_distance_xpts(all_shots)
    print(f"\n=== Zone xPTS table ===")
    print(zone_table.round(3))

    # Assign zone + xPTS per shot. Use string zones (not categorical) to avoid dtype issues.
    zone_to_xpts = {str(idx): float(row["xpts"]) for idx, row in zone_table.iterrows()}

    def assign_zone(dist):
        if pd.isna(dist):
            return "unknown"
        d = float(dist)
        if d <= 3: return "at_rim"
        if d <= 8: return "short_paint"
        if d <= 14: return "mid"
        if d <= 22: return "long_mid"
        if d <= 27: return "3pt"
        return "long_3"

    shots["zone"] = shots["shot_distance"].apply(assign_zone)
    shots["xPTS_shot"] = shots["zone"].map(zone_to_xpts)

    # Fall back for unknown: use 2/3 baseline
    fallback_xpts = np.where(
        shots["shot_outcome"].isin(["made_3", "missed_3"]),
        xpts_3,
        xpts_2,
    )
    shots["xPTS_shot"] = shots["xPTS_shot"].fillna(pd.Series(fallback_xpts, index=shots.index))
    print(f"After zone assignment: {len(shots):,} shots (xPTS range {shots['xPTS_shot'].min():.3f}-{shots['xPTS_shot'].max():.3f})")

    # Compute p_i and V_L per shot
    shots["p_i"] = compute_p_i(shots["DTI_def_attr"])
    # V_L(s*) is the continuation value if we HOLD. Should be expressed in
    # same units as xPTS_shot. Use n=1 (next action) and league avg xPTS as baseline:
    # V_L = league_avg_xPTS_per_attempt × P(extract value next action against this defender)
    # P(extract) = 1 - p_i (defender executes → forces non-optimal action)
    league_xpts_avg = all_shots["points"].sum() / len(all_shots)   # ~1.10 per attempt
    print(f"League xPTS per attempt: {league_xpts_avg:.3f}")
    # If we HOLD, the next action returns league avg conditional on the defender breaking
    # V_L = league_xpts_avg * (1 - p_i) + (xpts_2_baseline) * p_i
    # i.e. with probability (1-p_i) defender breaks and we get league_avg;
    # with probability p_i defender executes and we get a contested 2pt baseline
    contested_baseline = 0.85   # PPP on contested 2 league-wide
    shots["V_L"] = league_xpts_avg * (1 - shots["p_i"]) + contested_baseline * shots["p_i"]

    # Sovereign justification: xPTS_shot >= V_L (this shot extracts at least as much as holding would)
    shots["sovereign_justified"] = shots["xPTS_shot"] >= shots["V_L"]
    shots["sovereign_unjustified"] = ~shots["sovereign_justified"]

    print(f"\n=== AGGREGATE ===")
    print(f"Total attributed shots: {len(shots):,}")
    print(f"Justified shots:        {shots['sovereign_justified'].sum():,} ({shots['sovereign_justified'].mean():.1%})")
    print(f"Unjustified shots:      {shots['sovereign_unjustified'].sum():,} ({shots['sovereign_unjustified'].mean():.1%})")
    print(f"League PPP on justified: {shots[shots.sovereign_justified]['points'].mean():.3f}")
    print(f"League PPP on unjustified: {shots[shots.sovereign_unjustified]['points'].mean():.3f}")

    # Per-shooter aggregation
    by_shooter = shots.groupby("primary_offensive_player_id").agg(
        shots_total=("xPTS_shot", "count"),
        shots_justified=("sovereign_justified", "sum"),
        avg_realized_pts=("points", "mean"),
        avg_xpts=("xPTS_shot", "mean"),
    )
    by_shooter["justification_rate"] = by_shooter["shots_justified"] / by_shooter["shots_total"]
    by_shooter = by_shooter[by_shooter["shots_total"] >= 30]
    print(f"\nQualified shooters (n≥200 attributed shots): {len(by_shooter)}")

    # Resolve names
    try:
        from nba_api.stats.endpoints import commonallplayers
        cdf = commonallplayers.CommonAllPlayers(is_only_current_season=0, league_id="00", timeout=60).get_data_frames()[0]
        name_map = dict(zip(cdf["PERSON_ID"].astype(int), cdf["DISPLAY_FIRST_LAST"]))
        by_shooter["name"] = by_shooter.index.map(lambda x: name_map.get(int(x), f"Player_{x}"))
    except Exception:
        by_shooter["name"] = by_shooter.index.map(lambda x: f"Player_{x}")

    by_shooter = by_shooter.sort_values("justification_rate", ascending=False)
    out = data_dir / "Sovereign_Exception_Leaderboard_v0.1.csv"
    by_shooter.to_csv(out)
    print(f"\nSaved: {out}")

    print(f"\n=== TOP 25 BEST-JUSTIFIED SHOOTERS (highest % justified Sovereign calls) ===")
    print(by_shooter.head(25)[["name", "shots_total", "shots_justified", "justification_rate", "avg_realized_pts"]].round(3).to_string(index=False))

    print(f"\n=== BOTTOM 15 WORST-JUSTIFIED SHOOTERS (most unjustified Sovereign calls) ===")
    print(by_shooter.tail(15)[["name", "shots_total", "shots_justified", "justification_rate", "avg_realized_pts"]].round(3).to_string(index=False))


if __name__ == "__main__":
    main()
