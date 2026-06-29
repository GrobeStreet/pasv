"""
v3 holdout validation — split 5 playoffs into TRAIN (21-22 to 23-24) and
TEST (24-25, 25-26). Fit alpha/beta on TRAIN, validate β_2 t-stat on TEST.

If the v3 result holds out-of-sample, the asymmetric weighting is genuine.
If it collapses on TEST, alpha=4 is overfitting to TRAIN-set noise.
"""
import os
from pathlib import Path
import pandas as pd
import numpy as np
import statsmodels.api as sm


DTI_MAX = 18.6
DTI_MIN = -13.4


def p_i_linear(dti_def_per_100):
    center = (DTI_MAX + DTI_MIN) / 2
    half = (DTI_MAX - DTI_MIN) / 2
    norm = (dti_def_per_100 - center) / half
    return 0.75 - 0.20 * norm


def asym_prod(p_on, p_off_list, alpha, beta):
    return (p_on ** alpha) * np.prod([p ** beta for p in p_off_list])


def fit_alpha_beta(df_fit, p_i_map, p_default, alphas, betas, n=2, base_xpts=0.9):
    """Grid search returns (best_alpha, best_beta, t)."""
    df_fit = df_fit.copy()
    df_fit["V_v1"] = (1 - 0.95 ** (5 * n)) * base_xpts
    results = []
    for alpha in alphas:
        for beta in betas:
            p_v3 = df_fit.apply(
                lambda r: asym_prod(r["p_on"], r["p_off"], alpha, beta), axis=1,
            )
            V_v3 = (1 - p_v3 ** n) * base_xpts
            X = sm.add_constant(pd.DataFrame({"V_v1": df_fit["V_v1"], "V_v3": V_v3}))
            m = sm.OLS(df_fit["Y"], X).fit()
            results.append({
                "alpha": alpha, "beta": beta,
                "t": m.tvalues["V_v3"], "p": m.pvalues["V_v3"], "coef": m.params["V_v3"],
            })
    rdf = pd.DataFrame(results).sort_values("t", ascending=False)
    return rdf.iloc[0]


def evaluate_spec(df_eval, p_i_map, p_default, alpha, beta, n=2, base_xpts=0.9):
    df_eval = df_eval.copy()
    df_eval["V_v1"] = (1 - 0.95 ** (5 * n)) * base_xpts
    p_v3 = df_eval.apply(
        lambda r: asym_prod(r["p_on"], r["p_off"], alpha, beta), axis=1,
    )
    V_v3 = (1 - p_v3 ** n) * base_xpts
    X = sm.add_constant(pd.DataFrame({"V_v1": df_eval["V_v1"], "V_v3": V_v3}))
    m = sm.OLS(df_eval["Y"], X).fit()
    return m


def main():
    data_dir = Path(os.environ.get("DTI_DATA_DIR", "/tmp/dti_data"))
    df = pd.read_parquet(data_dir / "poss_v3_LINEUPS_MULTI_5playoffs.parquet")
    lb = pd.read_csv(data_dir / "DTI_def_leaderboard_CANON_FINAL_n200.csv")
    p_i_map = {pid: p_i_linear(dti) for pid, dti in zip(lb["defender_id"], lb["DTI_def_per_100"])}
    p_default = 0.75

    df_full = df[
        (df["def_lineup_ids"].apply(lambda x: len(x) == 5))
        & (df["primary_defensive_player_id"] > 0)
    ].copy()

    def split(row):
        lineup = list(row["def_lineup_ids"])
        on_id = int(row["primary_defensive_player_id"])
        return (
            p_i_map.get(on_id, p_default),
            [p_i_map.get(int(x), p_default) for x in lineup if int(x) != on_id],
        )
    df_full["p_on"], df_full["p_off"] = zip(*df_full.apply(split, axis=1))
    df_full["Y"] = df_full["points"]

    train_seasons = ["2021-22", "2022-23", "2023-24"]
    test_seasons = ["2024-25", "2025-26"]
    train = df_full[df_full["season"].isin(train_seasons)]
    test = df_full[df_full["season"].isin(test_seasons)]
    print(f"TRAIN: {len(train):,} possessions (3 playoffs)")
    print(f"TEST:  {len(test):,} possessions (2 playoffs)")

    print(f"\n=== FIT alpha, beta on TRAIN ===")
    alphas = [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 5.0]
    betas = [0.25, 0.4, 0.5, 0.6, 0.75, 1.0]
    best = fit_alpha_beta(train, p_i_map, p_default, alphas, betas)
    print(f"Best TRAIN: alpha={best['alpha']}, beta={best['beta']}, t={best['t']:+.2f}, p={best['p']:.4f}")

    print(f"\n=== EVALUATE WINNING SPEC ON TEST ===")
    test_model = evaluate_spec(test, p_i_map, p_default, best["alpha"], best["beta"])
    test_t = test_model.tvalues["V_v3"]
    test_p = test_model.pvalues["V_v3"]
    test_coef = test_model.params["V_v3"]
    print(f"TEST (held-out): alpha={best['alpha']}, beta={best['beta']}")
    print(f"  β_2 = {test_coef:+.4f}")
    print(f"  t = {test_t:+.2f}")
    print(f"  p = {test_p:.4f}")
    print(f"\nVerdict:")
    if test_p < 0.05:
        print(f"  ✓ HOLDS OUT-OF-SAMPLE. v3 spec is genuine, not overfit.")
    elif test_p < 0.10:
        print(f"  ⚠ Marginal on TEST (p<0.10 but >0.05). Real signal but smaller effect.")
    else:
        print(f"  ✗ COLLAPSES on TEST. alpha/beta were overfit to TRAIN noise.")

    # Cross-check: also evaluate the symmetric baseline on TEST
    print(f"\n=== Baseline (alpha=1, beta=1) on TEST for comparison ===")
    sym_model = evaluate_spec(test, p_i_map, p_default, 1.0, 1.0)
    print(f"  β_2 = {sym_model.params['V_v3']:+.4f}")
    print(f"  t = {sym_model.tvalues['V_v3']:+.2f}")
    print(f"  p = {sym_model.pvalues['V_v3']:.4f}")

    # And a "moderately asymmetric" spec
    print(f"\n=== Moderate (alpha=2, beta=0.5) on TEST ===")
    mod_model = evaluate_spec(test, p_i_map, p_default, 2.0, 0.5)
    print(f"  β_2 = {mod_model.params['V_v3']:+.4f}")
    print(f"  t = {mod_model.tvalues['V_v3']:+.2f}")
    print(f"  p = {mod_model.pvalues['V_v3']:.4f}")


if __name__ == "__main__":
    main()
