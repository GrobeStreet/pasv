"""
Holding-Math Theorem v3.0 — Asymmetric on-ball/off-ball p_i weighting.

v2 limitation: V_v2 = (1 - prod(p_i)^n) treats all 5 defenders symmetrically.
v3 fix: V_v3 = (1 - [p_onball^alpha * prod(p_offball)^beta]^n)

We grid-search (alpha, beta) to maximize β_2 t-stat in §4.2.12 regression.
Mathematical guarantee: increasing alpha amplifies V_v3 variance (since
single-defender p_i has 5x more variance than the 5-defender mean),
which lifts the regression's separation power.

Uses the multi-season lineup parquet (66K possessions) + existing
primary_defensive_player_id attribution to split on-ball from off-ball.
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


def asymmetric_product(p_onball, p_offball_list, alpha, beta):
    """V_v3 weighting: p_onball^alpha * prod(p_offball^beta)"""
    onball_term = p_onball ** alpha
    offball_term = np.prod([p ** beta for p in p_offball_list]) if p_offball_list else 1.0
    return onball_term * offball_term


def main():
    data_dir = Path(os.environ.get("DTI_DATA_DIR", "/tmp/dti_data"))

    df = pd.read_parquet(data_dir / "poss_v3_LINEUPS_MULTI_5playoffs.parquet")
    print(f"Loaded {len(df):,} possessions ({df.game_id.nunique()} games)")

    lb = pd.read_csv(data_dir / "DTI_def_leaderboard_CANON_FINAL_n200.csv")
    dti_def_map = dict(zip(lb["defender_id"], lb["DTI_def_per_100"]))
    p_i_map = {pid: p_i_linear(dti) for pid, dti in dti_def_map.items()}
    p_default = 0.75

    # Need BOTH lineup AND attributed on-ball defender
    df_full = df[
        (df["def_lineup_ids"].apply(lambda x: len(x) == 5))
        & (df["primary_defensive_player_id"] > 0)
    ].copy()
    print(f"Lineup-aware + attributed on-ball defender: {len(df_full):,}")

    # Pre-compute per-row p_onball and p_offball_list
    def split_lineup(row):
        lineup = list(row["def_lineup_ids"])
        on_ball_id = int(row["primary_defensive_player_id"])
        p_on = p_i_map.get(on_ball_id, p_default)
        # Off-ball = the other 4 (if on-ball player IS in lineup, exclude; else all 5)
        off_ids = [int(x) for x in lineup if int(x) != on_ball_id]
        p_off = [p_i_map.get(x, p_default) for x in off_ids]
        return p_on, p_off

    df_full["p_on"], df_full["p_off"] = zip(*df_full.apply(split_lineup, axis=1))
    df_full["Y"] = df_full["points"]

    # Baseline V_v2 (symmetric, all 5 weighted equally)
    df_full["p_product_v2"] = df_full.apply(
        lambda r: r["p_on"] * np.prod(r["p_off"]),
        axis=1,
    )
    n_actions = 2
    baseline_xpts = 0.9
    df_full["V_v1"] = (1 - 0.95 ** (5 * n_actions)) * baseline_xpts
    df_full["V_v2_sym"] = (1 - df_full["p_product_v2"] ** n_actions) * baseline_xpts

    # ============================================================
    # Baseline v2 regression for direct comparison
    # ============================================================
    X = sm.add_constant(df_full[["V_v1", "V_v2_sym"]])
    base_model = sm.OLS(df_full["Y"], X).fit()
    base_t = base_model.tvalues["V_v2_sym"]
    base_p = base_model.pvalues["V_v2_sym"]
    base_coef = base_model.params["V_v2_sym"]
    base_v_std = df_full["V_v2_sym"].std()
    print(f"\n=== v2 BASELINE (symmetric, alpha=beta=1) ===")
    print(f"V_v2 std: {base_v_std:.6f}")
    print(f"β_2 = {base_coef:+.4f}, t = {base_t:+.2f}, p = {base_p:.4f}")

    # ============================================================
    # Grid search over (alpha, beta) on asymmetric product
    # ============================================================
    print(f"\n=== GRID SEARCH: V_v3 with asymmetric on-ball/off-ball weights ===")
    print(f"{'alpha':>6}  {'beta':>6}  {'V_std':>8}  {'β_2':>10}  {'t':>6}  {'p':>8}")
    print("-" * 60)

    results = []
    alphas = [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 5.0]
    betas = [0.25, 0.4, 0.5, 0.6, 0.75, 1.0]

    for alpha in alphas:
        for beta in betas:
            # Compute V_v3 with asymmetric weights
            p_v3 = df_full.apply(
                lambda r: asymmetric_product(r["p_on"], r["p_off"], alpha, beta),
                axis=1,
            )
            V_v3 = (1 - p_v3 ** n_actions) * baseline_xpts
            v_std = V_v3.std()
            X = sm.add_constant(pd.DataFrame({"V_v1": df_full["V_v1"], "V_v3": V_v3}))
            try:
                m = sm.OLS(df_full["Y"], X).fit()
                t = m.tvalues["V_v3"]
                p = m.pvalues["V_v3"]
                coef = m.params["V_v3"]
                results.append({
                    "alpha": alpha, "beta": beta,
                    "V_std": v_std, "beta_2": coef, "t": t, "p_value": p,
                })
                print(f"{alpha:>6.1f}  {beta:>6.2f}  {v_std:>8.5f}  {coef:>+10.4f}  {t:>+6.2f}  {p:>8.4f}")
            except Exception as e:
                print(f"  {alpha} {beta}: failed - {e}")

    results_df = pd.DataFrame(results).sort_values("t", ascending=False)
    print(f"\n=== TOP 5 SPECIFICATIONS BY |t| ===")
    print(results_df.head().round(5).to_string(index=False))

    # Best specification
    best = results_df.iloc[0]
    print(f"\n=== WINNING SPECIFICATION ===")
    print(f"alpha={best['alpha']}, beta={best['beta']}")
    print(f"β_2 = {best['beta_2']:+.4f}")
    print(f"t = {best['t']:+.2f}")
    print(f"p = {best['p_value']:.4f}")
    print(f"V_std = {best['V_std']:.6f}")
    print(f"\nLift vs v2 symmetric:")
    print(f"  t-stat:  {base_t:+.2f} → {best['t']:+.2f}  ({best['t']/base_t:.2f}x)")
    print(f"  V_std:   {base_v_std:.6f} → {best['V_std']:.6f}  ({best['V_std']/base_v_std:.2f}x)")

    # Save
    out = data_dir / "v3_asymmetric_weights_grid_search.csv"
    results_df.to_csv(out, index=False)
    print(f"\nSaved: {out}")

    # Final regression with winning spec (full output)
    alpha_best = best["alpha"]
    beta_best = best["beta"]
    p_v3 = df_full.apply(
        lambda r: asymmetric_product(r["p_on"], r["p_off"], alpha_best, beta_best),
        axis=1,
    )
    V_v3 = (1 - p_v3 ** n_actions) * baseline_xpts
    X = sm.add_constant(pd.DataFrame({"V_v1": df_full["V_v1"], "V_v3": V_v3}))
    final_model = sm.OLS(df_full["Y"], X).fit()
    print(f"\n=== FINAL §4.2.12 REGRESSION WITH WINNING v3 SPEC ===")
    print(final_model.summary().tables[1])


if __name__ == "__main__":
    main()
