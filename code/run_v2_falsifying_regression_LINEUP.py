"""
Holding-Math Theorem v2.0 — Falsifying Regression with LINEUP-AWARE p_i product
(§4.2.12 v0.2 upgrade)

The v0.1 regression used p_i = single attributed defender's p. Result:
  β_2 = 0.773, p < 0.001 BUT β_1 also significant (artifact: V_v1 std=0)

The v0.2 regression uses prod(p_i for i in def_lineup) — true 5-defender product.
Expected: β_1 collapses (no longer significant), β_2 stays significant.
"""
import os
from pathlib import Path
import pandas as pd
import numpy as np
import statsmodels.api as sm

DTI_MAX = 18.6
DTI_MIN = -13.4


def compute_p_i(dti_def_per_100):
    center = (DTI_MAX + DTI_MIN) / 2
    half = (DTI_MAX - DTI_MIN) / 2
    norm = (dti_def_per_100 - center) / half
    return 0.75 - 0.20 * norm   # [0.55, 0.95]


def main():
    data_dir = Path(os.environ.get("DTI_DATA_DIR", "/tmp/dti_data"))

    # Load v0.2 lineup parquet
    parquet = data_dir / "poss_v3_LINEUPS_MULTI_5playoffs.parquet"
    df = pd.read_parquet(parquet)
    print(f"Loaded {len(df):,} possessions ({df.game_id.nunique()} games)")

    # Load Canon DTI_def leaderboard for the p_i map
    lb = pd.read_csv(data_dir / "DTI_def_leaderboard_CANON_FINAL_n200.csv")
    dti_def_map = dict(zip(lb["defender_id"], lb["DTI_def_per_100"]))
    print(f"DTI_def map: {len(dti_def_map)} defenders")

    # Compute p_i per defender id
    p_i_map = {pid: compute_p_i(dti) for pid, dti in dti_def_map.items()}
    league_p_default = 0.75   # for defenders not in our leaderboard

    # Filter to possessions with full 5-man lineup
    df_full = df[df["def_lineup_ids"].apply(lambda x: len(x) == 5)].copy()
    print(f"With 5-man def lineup: {len(df_full):,}")

    # Compute LINEUP-PRODUCT p_i per possession
    def lineup_product(lineup_ids):
        prod = 1.0
        for pid in lineup_ids:
            prod *= p_i_map.get(int(pid), league_p_default)
        return prod

    df_full["p_product_lineup"] = df_full["def_lineup_ids"].apply(lineup_product)
    print(f"\nLineup product distribution:")
    print(df_full["p_product_lineup"].describe().round(4))

    # Compute V_v1 (uniform p=0.95) and V_v2 (lineup product)
    n_actions = 2
    baseline_xpts = 0.9
    df_full["V_v1"] = (1 - 0.95 ** (5 * n_actions)) * baseline_xpts
    df_full["V_v2"] = (1 - df_full["p_product_lineup"] ** n_actions) * baseline_xpts

    df_full["Y"] = df_full["points"]

    print(f"\n=== Pre-regression sanity ===")
    print(f"Y mean (PPP): {df_full['Y'].mean():.4f}")
    print(f"V_v1 std: {df_full['V_v1'].std():.6f}   (still 0 — matchup-blind)")
    print(f"V_v2 std: {df_full['V_v2'].std():.6f}   (varies via lineup product)")
    print(f"V_v2 range: [{df_full['V_v2'].min():.4f}, {df_full['V_v2'].max():.4f}]")

    # Regression
    X = df_full[["V_v1", "V_v2"]]
    X = sm.add_constant(X)
    y = df_full["Y"]
    model = sm.OLS(y, X).fit()
    print(f"\n=== §4.2.12 v0.2 LINEUP-AWARE REGRESSION ===")
    print(model.summary().tables[1])

    beta_1 = model.params.get("V_v1", float("nan"))
    beta_2 = model.params["V_v2"]
    p_1 = model.pvalues.get("V_v1", float("nan"))
    p_2 = model.pvalues["V_v2"]

    print(f"\n=== INTERPRETATION ===")
    print(f"β_1 (v1): {beta_1:.5f}, p = {p_1:.4f}")
    print(f"β_2 (v2-lineup): {beta_2:.5f}, p = {p_2:.4f}")

    if p_2 > 0.10:
        print("FALSIFICATION MET: v2 dies.")
    elif p_1 > 0.10 and p_2 < 0.05:
        print("CLEAN v2 WIN: β_1 collapsed, β_2 stays significant.")
    elif p_2 < 0.05 and beta_2 > 0:
        print("PARTIAL v2 SUPPORT: β_2 significant + positive (may still need lineup variance).")
    else:
        print("INCONCLUSIVE.")

    # Direct correlation
    corr = df_full[["p_product_lineup", "Y"]].corr().iloc[0,1]
    print(f"\nPearson r(p_product_lineup, Y): {corr:.4f}  (expected: negative)")

    # Bucketed PPP by lineup product quartile
    df_full["p_bucket"] = pd.qcut(df_full["p_product_lineup"], 4, labels=["Q1_softest", "Q2", "Q3", "Q4_hardest"])
    print(f"\nMean realized PPP by lineup hardness quartile:")
    print(df_full.groupby("p_bucket", observed=True)["Y"].agg(["mean", "count"]).round(4))

    # Save artifact
    out = data_dir / "v2_LINEUP_falsifying_regression_results.txt"
    with open(out, "w") as f:
        f.write("Holding-Math v2.0 — LINEUP-AWARE Falsifying Regression (§4.2.12 v0.2)\n")
        f.write("="*70 + "\n\n")
        f.write(f"Sample: {len(df_full):,} possessions with 5-defender lineup\n")
        f.write(f"League PPP: {df_full['Y'].mean():.4f}\n\n")
        f.write(str(model.summary()))
        f.write(f"\n\nPearson r(p_product, Y) = {corr:.4f}\n")
    print(f"\nSaved: {out}")


if __name__ == "__main__":
    main()
