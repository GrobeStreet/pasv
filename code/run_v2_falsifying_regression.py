"""
Holding-Math Theorem v2.0 — Falsifying Empirical Test (§4.2.12)

Regression spec:
    Y = beta_0 + beta_1 * V_star_v1(s) + beta_2 * V_star_v2(s) + eps

where:
    V_star_v1 uses uniform p = 0.95 (matchup-blind)
    V_star_v2 uses per-defender p_i derived from DTI_def

Falsification:
    v2 dies if beta_2 indistinguishable from zero AND beta_1 stays significant.
    v2 supported if beta_2 > 0 AND beta_1 collapses.
    Clean v2 win: beta_2 significant, beta_1 -> 0 or flips sign.

v0.1 approximation (acknowledged): we have the attributed *primary* defender
per possession, not the full 5-man lineup. We use the single-defender p_i as
a lineup proxy (p_lineup ~= p_i). This is the WEAKEST form of the v2 test --
if v2 dies here, it's dead.
"""
import os
from pathlib import Path
import numpy as np
import pandas as pd

# Statsmodels for regression with t-stats + p-values
try:
    import statsmodels.api as sm
except ImportError:
    print("Installing statsmodels...")
    import subprocess, sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--break-system-packages", "-q", "statsmodels"])
    import statsmodels.api as sm


# Eq. 4.15: p_i = 0.5 + 0.5 * (1 - DTI_def_normalized_i)
# DTI_def normalized to [-1, +1] across the league
P_FLOOR = 0.55
P_CEILING = 0.95
DTI_MAX = 18.6   # Jamal Murray multi-season high
DTI_MIN = -13.4  # Cason Wallace multi-season low


def normalize_dti(dti_def_per_100, dti_max=DTI_MAX, dti_min=DTI_MIN):
    """Rescale DTI_def to [-1, +1]."""
    center = (dti_max + dti_min) / 2
    half_range = (dti_max - dti_min) / 2
    return (dti_def_per_100 - center) / half_range


def compute_p_i(dti_def_per_100):
    """Eq. 4.15: per-defender execution rate."""
    norm = normalize_dti(dti_def_per_100)
    return P_FLOOR + 0.5 * (P_CEILING - P_FLOOR) * (1 - norm) * 2 / (P_CEILING - P_FLOOR) * (P_CEILING - P_FLOOR) / 2 + (P_CEILING - P_FLOOR) / 2
    # Cleaner: linear map from norm in [-1,+1] to p_i in [0.95, 0.55]
    # (high DTI_def -> high norm -> low p_i)


def compute_p_i_clean(dti_def_per_100):
    """Cleaner version: p_i = 0.75 - (norm * 0.20), giving [0.55, 0.95]."""
    norm = normalize_dti(dti_def_per_100)
    return 0.75 - 0.20 * norm


def compute_v_star_v1(shot_clock_proxy, p=0.95, n=2):
    """v1 continuation value: V* ~= (1 - p^(5n)) * baseline_xPTS.
    Matchup-blind. Same value for every possession at the same n.
    """
    # Use shot_clock_proxy as n_remaining. Approximation: n = max(1, shot_clock_proxy / 8).
    n = np.maximum(1, shot_clock_proxy / 8.0)
    return (1 - p ** (5 * n)) * 0.9  # baseline_xPTS proxy ~0.9


def compute_v_star_v2(shot_clock_proxy, p_i_observed, n_actions=2):
    """v2 continuation value using per-defender p_i.
    For v0.1 approximation: use p_lineup = p_i^single as proxy for prod(p_j).
    """
    # Approximation: prod(p_j) ~ p_i (the attributed defender) for single-defender attribution.
    # Multi-defender lineup product is unobserved at v0.1.
    p_lineup_approx = p_i_observed
    n = np.maximum(1, shot_clock_proxy / 8.0)
    return (1 - p_lineup_approx ** n) * 0.9


def main():
    data_dir = Path(os.environ.get("DTI_DATA_DIR", "/tmp/dti_data"))

    # Default to Canon 403K parquet if present
    canon_path = data_dir / "poss_v3_CANON_5playoffs_2526RS.parquet"
    playoff_path = data_dir / "poss_v3_MULTI_5seasons_Playoffs.parquet"
    parquet_path = canon_path if canon_path.exists() else playoff_path

    if not parquet_path.exists():
        print(f"NOT FOUND: {parquet_path}")
        return

    df = pd.read_parquet(parquet_path)
    print(f"Loaded {len(df):,} possessions from {parquet_path.name}")

    # Prefer the Canon n≥150 leaderboard; fall back to multi-season-n50
    canon_lb = data_dir / "DTI_def_leaderboard_CANON_n150.csv"
    multi_lb = data_dir / "DTI_def_leaderboard_MULTI_5seasons_Playoffs_n50.csv"
    lb_path = canon_lb if canon_lb.exists() else multi_lb
    dti_def_df = pd.read_csv(lb_path)
    dti_def_map = dict(zip(dti_def_df["defender_id"], dti_def_df["DTI_def_per_100"]))
    print(f"Using DTI_def leaderboard: {lb_path.name}")
    print(f"DTI_def map: {len(dti_def_map)} defenders with multi-season DTI_def")

    # Filter to attributed possessions
    attrib = df[df["primary_defensive_player_id"] > 0].copy()
    print(f"Attributable possessions: {len(attrib):,}")

    # Merge DTI_def onto each possession via the primary defender
    attrib["DTI_def_attr"] = attrib["primary_defensive_player_id"].map(dti_def_map)

    # Keep only possessions where attributed defender has multi-season DTI_def
    attrib = attrib.dropna(subset=["DTI_def_attr"])
    print(f"With DTI_def coverage: {len(attrib):,}")

    # Compute p_i for the attributed defender
    attrib["p_i"] = compute_p_i_clean(attrib["DTI_def_attr"])

    # Compute V_v1 and V_v2 per possession
    # Use a synthetic shot clock proxy (since we don't have shot clock in v0.1 ingest):
    # period 1-4 -> clock decreases; we'll use "PT" in clock field if available.
    # For v0.1 falsifying test, use period as a coarse n_remaining proxy.
    # This is intentionally rough -- the test is whether per-defender p_i has ANY explanatory
    # power v1 doesn't, not the precise lift.
    attrib["clock_proxy"] = 10.0  # neutral default - same for all possessions
    attrib["V_v1"] = compute_v_star_v1(attrib["clock_proxy"])
    attrib["V_v2"] = compute_v_star_v2(attrib["clock_proxy"], attrib["p_i"])

    # Realized PPP (Y)
    attrib["Y"] = attrib["points"]

    print(f"\n=== Pre-regression sanity checks ===")
    print(f"Y mean: {attrib['Y'].mean():.3f}")
    print(f"V_v1 std: {attrib['V_v1'].std():.4f}  (should be ~0 since matchup-blind)")
    print(f"V_v2 std: {attrib['V_v2'].std():.4f}  (should be >0; varies with defender p_i)")
    print(f"V_v2 range: [{attrib['V_v2'].min():.3f}, {attrib['V_v2'].max():.3f}]")
    print(f"p_i range: [{attrib['p_i'].min():.3f}, {attrib['p_i'].max():.3f}]")

    # Run the §4.2.12 regression: Y = beta_0 + beta_1 * V_v1 + beta_2 * V_v2 + eps
    X = attrib[["V_v1", "V_v2"]]
    X = sm.add_constant(X)
    y = attrib["Y"]
    model = sm.OLS(y, X).fit()
    print(f"\n=== §4.2.12 REGRESSION: Y = beta_0 + beta_1 * V_v1 + beta_2 * V_v2 ===")
    print(model.summary().tables[1])

    # Falsification interpretation
    beta_2 = model.params["V_v2"]
    p_2 = model.pvalues["V_v2"]
    beta_1 = model.params.get("V_v1", float("nan"))
    p_1 = model.pvalues.get("V_v1", float("nan"))

    print(f"\n=== FALSIFICATION TEST ===")
    print(f"beta_1 (v1): {beta_1:.5f}, p = {p_1:.4f}")
    print(f"beta_2 (v2): {beta_2:.5f}, p = {p_2:.4f}")
    print()
    if p_2 > 0.10:
        print(f"FALSIFICATION CRITERION MET: beta_2 not distinguishable from 0 (p > 0.10)")
        print(f"  -> v2 is FALSIFIED in favor of v1 for this approximation.")
    elif p_2 < 0.05 and beta_2 > 0:
        if abs(beta_1) < abs(beta_2) * 0.5 or p_1 > 0.05:
            print(f"CLEAN v2 WIN: beta_2 significant, beta_1 collapsed.")
            print(f"  -> v2 SUBSUMES v1 explanatory power.")
        else:
            print(f"PARTIAL v2 SUPPORT: beta_2 significant + positive, but v1 also still significant.")
            print(f"  -> v2 has explanatory power v1 doesn't, but v1 not fully subsumed.")
    elif p_2 < 0.05 and beta_2 < 0:
        print(f"WRONG SIGN: beta_2 significant but negative.")
        print(f"  -> p_i mapping has wrong sign or v2 reformulation needed.")
    else:
        print(f"INCONCLUSIVE: 0.05 < p_2 < 0.10. Larger sample needed.")

    # SANITY CHECK 2: Direct test — does p_i correlate with realized PPP?
    print(f"\n=== SANITY CHECK: corr(p_i, Y) ===")
    corr = attrib[["p_i", "Y"]].corr().iloc[0,1]
    print(f"Pearson r(p_i, realized PPP): {corr:.4f}")
    print(f"Expected: NEGATIVE — higher p_i = better defender = lower PPP against.")

    # SANITY CHECK 3: Direct mean comparison by DTI bucket
    print(f"\n=== Mean realized PPP by DTI_def bucket ===")
    attrib["DTI_bucket"] = pd.cut(attrib["DTI_def_attr"],
                                   bins=[-30, -5, 0, 5, 30],
                                   labels=["hunt-proof (<-5)", "below avg [-5,0)", "above avg [0,5)", "hunted (>5)"])
    print(attrib.groupby("DTI_bucket", observed=True)["Y"].agg(["mean", "count"]).round(3))

    # Save the regression artifact
    summary_path = data_dir / "v2_falsifying_regression_results.txt"
    with open(summary_path, "w") as f:
        f.write("Holding-Math Theorem v2.0 — Falsifying Regression (§4.2.12)\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Sample: {len(attrib):,} possessions with attributed defender + DTI_def coverage\n")
        f.write(f"League PPP baseline: {attrib['Y'].mean():.4f}\n\n")
        f.write(str(model.summary()))
        f.write("\n\n")
        f.write(f"beta_1 (v1, uniform p=0.95): {beta_1:.5f}, p = {p_1:.4f}\n")
        f.write(f"beta_2 (v2, per-defender p_i): {beta_2:.5f}, p = {p_2:.4f}\n")
        f.write(f"Pearson r(p_i, Y): {corr:.4f}\n")
    print(f"\nSaved: {summary_path}")


if __name__ == "__main__":
    main()
