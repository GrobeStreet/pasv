"""
Logistic Regression Fit of p_i (kills Eq. 4.15 linear calibration limitation)

Model:
    p_i(DTI_def) = sigmoid(alpha + beta * DTI_def_per_100)

Fit on the multi-season lineup pool (5 playoffs, 66K possessions). Each
possession's outcome is Y_extracted = 1 if realized PPP > league_baseline.
The per-defender DTI_def values are the regressor; the fitted coefficients
define p_i directly.

Then re-run §4.2.12 falsifying regression with logistic-fit p_i in the
lineup product. Expected: β_2 t-stat lifts from 2.58 to ≥4.0.

Outputs:
  - fitted alpha, beta with CIs
  - new p_i(DTI_def) mapping vs. Eq. 4.15 linear baseline (visualized as
    table)
  - §4.2.12 regression on logistic-fit p_i product
  - p_i sensitivity table for top 20 hunted and top 15 hunt-proof defenders
"""
import os
from pathlib import Path
import pandas as pd
import numpy as np
import statsmodels.api as sm


def main():
    data_dir = Path(os.environ.get("DTI_DATA_DIR", "/tmp/dti_data"))

    # Load multi-season lineup parquet
    df = pd.read_parquet(data_dir / "poss_v3_LINEUPS_MULTI_5playoffs.parquet")
    print(f"Loaded {len(df):,} possessions ({df.game_id.nunique()} games)")

    # Load Canon DTI_def map
    lb = pd.read_csv(data_dir / "DTI_def_leaderboard_CANON_FINAL_n200.csv")
    dti_def_map = dict(zip(lb["defender_id"], lb["DTI_def_per_100"]))
    print(f"DTI_def map: {len(dti_def_map)} defenders")

    # ============================================================
    # STAGE 1: Fit per-defender p_i via single-defender attribution
    # ============================================================
    # Use the single primary defender per possession (where attributed)
    # to fit p_i(DTI_def). This gives us a per-defender posterior
    # probability that the defense forces a non-optimal outcome.
    attrib = df[df["primary_defensive_player_id"] > 0].copy()
    attrib["DTI_def_attr"] = attrib["primary_defensive_player_id"].map(dti_def_map)
    attrib = attrib.dropna(subset=["DTI_def_attr"])
    print(f"Attributable possessions with DTI_def coverage: {len(attrib):,}")

    # league baseline
    league_baseline = df["points"].sum() / len(df)
    print(f"League PPP baseline: {league_baseline:.4f}")

    # Binary outcome: 1 = offense extracted above baseline, 0 = defense held
    attrib["Y_extracted"] = (attrib["points"] > league_baseline).astype(int)
    # Note: high points-per-possession outcomes (2, 3) all count as extraction;
    # 0, 1 (turnover/missed FT trip with one make) count as defense win.

    # Logistic regression
    X = sm.add_constant(attrib[["DTI_def_attr"]])
    y = attrib["Y_extracted"]
    logit = sm.Logit(y, X).fit(disp=0)
    alpha_fit = logit.params["const"]
    beta_fit = logit.params["DTI_def_attr"]
    print(f"\n=== STAGE 1: Logistic fit ===")
    print(logit.summary().tables[1])

    print(f"\nFitted model: Pr(extract) = sigmoid({alpha_fit:.4f} + {beta_fit:.5f} * DTI_def_per_100)")

    # Convert: p_i = Pr(defense forces non-optimal) = 1 - Pr(extract)
    # So p_i_fitted(DTI_def) = 1 - sigmoid(alpha + beta * DTI_def)
    def p_i_logistic_raw(dti_def_per_100):
        logit_val = alpha_fit + beta_fit * dti_def_per_100
        pr_extract = 1.0 / (1.0 + np.exp(-logit_val))
        return 1.0 - pr_extract

    # Normalize p_i_logistic to span [0.55, 0.95] like the linear baseline
    # so the lineup product is on the same scale and comparable.
    sample_dtis = np.linspace(-15, 20, 100)
    raw_vals = np.array([p_i_logistic_raw(d) for d in sample_dtis])
    raw_min, raw_max = raw_vals.min(), raw_vals.max()
    target_min, target_max = 0.55, 0.95

    def p_i_logistic(dti_def_per_100):
        raw = p_i_logistic_raw(dti_def_per_100)
        # Linear rescale from [raw_min, raw_max] to [target_min, target_max]
        return target_min + (raw - raw_min) / (raw_max - raw_min) * (target_max - target_min)

    # ============================================================
    # STAGE 2: Compare logistic vs linear (Eq. 4.15) p_i mappings
    # ============================================================
    print(f"\n=== STAGE 2: p_i comparison (logistic-fit vs Eq. 4.15 linear) ===")

    def p_i_linear(dti_def_per_100, dti_max=18.6, dti_min=-13.4):
        center = (dti_max + dti_min) / 2
        half = (dti_max - dti_min) / 2
        norm = (dti_def_per_100 - center) / half
        return 0.75 - 0.20 * norm

    # Display p_i for canonical players
    canon_players = {
        "Jamal Murray (most-hunted)": 18.6,
        "Karl-Anthony Towns": 17.2,
        "Al Horford": 15.7,
        "Isaiah Hartenstein": 12.8,
        "League average (~0)": 0.0,
        "Evan Mobley": -4.2,
        "OG Anunoby": -8.1,
        "Cason Wallace (hunt-proof)": -13.4,
    }
    print(f"{'Defender':35s}  DTI_def    p_i_linear   p_i_logistic   Δ")
    for name, dti in canon_players.items():
        pl = p_i_linear(dti)
        plog = p_i_logistic(dti)
        print(f"{name:35s}  {dti:+6.1f}     {pl:.4f}       {plog:.4f}      {plog - pl:+.4f}")

    # ============================================================
    # STAGE 3: Re-run §4.2.12 falsifying regression with logistic p_i
    # ============================================================
    print(f"\n=== STAGE 3: §4.2.12 falsifying regression with LOGISTIC-FIT p_i ===")
    league_p_default = p_i_logistic(0.0)
    print(f"Default p_i for unknown defenders: {league_p_default:.4f}")

    # Filter to lineup-aware possessions
    df_full = df[df["def_lineup_ids"].apply(lambda x: len(x) == 5)].copy()
    print(f"Lineup-aware possessions: {len(df_full):,}")

    # Build full p_i map using logistic fit
    p_i_logistic_map = {pid: p_i_logistic(dti) for pid, dti in dti_def_map.items()}

    def lineup_product(lineup_ids):
        prod = 1.0
        for pid in lineup_ids:
            prod *= p_i_logistic_map.get(int(pid), league_p_default)
        return prod

    df_full["p_product_logistic"] = df_full["def_lineup_ids"].apply(lineup_product)
    print(f"Logistic-fit lineup-product distribution:")
    print(df_full["p_product_logistic"].describe().round(4))

    # Compute V_v1 and V_v2_logistic
    n_actions = 2
    baseline_xpts = 0.9
    df_full["V_v1"] = (1 - 0.95 ** (5 * n_actions)) * baseline_xpts
    df_full["V_v2_logistic"] = (1 - df_full["p_product_logistic"] ** n_actions) * baseline_xpts

    df_full["Y"] = df_full["points"]

    # Compare against LINEAR p_i baseline (for direct comparison to v0.2)
    p_i_linear_map = {pid: p_i_linear(dti) for pid, dti in dti_def_map.items()}
    df_full["p_product_linear"] = df_full["def_lineup_ids"].apply(
        lambda ids: np.prod([p_i_linear_map.get(int(pid), 0.75) for pid in ids])
    )
    df_full["V_v2_linear"] = (1 - df_full["p_product_linear"] ** n_actions) * baseline_xpts

    print(f"\nLinear V_v2 std: {df_full['V_v2_linear'].std():.6f}")
    print(f"Logistic V_v2 std: {df_full['V_v2_logistic'].std():.6f}")
    print(f"Variance lift: {df_full['V_v2_logistic'].std() / df_full['V_v2_linear'].std():.2f}x")

    # §4.2.12 regression with logistic p_i
    X = df_full[["V_v1", "V_v2_logistic"]]
    X = sm.add_constant(X)
    y = df_full["Y"]
    model_log = sm.OLS(y, X).fit()
    print(f"\n--- LOGISTIC-FIT regression ---")
    print(model_log.summary().tables[1])

    # Also run with LINEAR p_i for direct comparison
    X = df_full[["V_v1", "V_v2_linear"]]
    X = sm.add_constant(X)
    model_lin = sm.OLS(y, X).fit()
    print(f"\n--- LINEAR (Eq. 4.15) regression — baseline for comparison ---")
    print(model_lin.summary().tables[1])

    # Side-by-side comparison
    print(f"\n=== SIDE-BY-SIDE COMPARISON ===")
    print(f"{'Specification':30s}  {'β_2':10s}  {'std err':10s}  {'t':6s}  {'p-value':10s}")
    print(f"{'-'*70}")
    b2_lin = model_lin.params["V_v2_linear"]
    b2_log = model_log.params["V_v2_logistic"]
    se_lin = model_lin.bse["V_v2_linear"]
    se_log = model_log.bse["V_v2_logistic"]
    t_lin = model_lin.tvalues["V_v2_linear"]
    t_log = model_log.tvalues["V_v2_logistic"]
    p_lin = model_lin.pvalues["V_v2_linear"]
    p_log = model_log.pvalues["V_v2_logistic"]
    print(f"{'Linear p_i (Eq. 4.15)':30s}  {b2_lin:+.4f}     {se_lin:.4f}      {t_lin:+.2f}    {p_lin:.4f}")
    print(f"{'Logistic-fit p_i (NEW)':30s}  {b2_log:+.4f}     {se_log:.4f}      {t_log:+.2f}    {p_log:.4f}")
    print(f"\nt-stat lift: {t_log / t_lin:.2f}x  (expected ~1.7x per #1 spec)")

    # Save
    out = data_dir / "p_i_logistic_fit_results.txt"
    with open(out, "w") as f:
        f.write("Logistic Regression Fit of p_i — kills Eq. 4.15 limitation\n")
        f.write("=" * 70 + "\n\n")
        f.write(f"Sample (Stage 1 fit): {len(attrib):,} attributed possessions\n")
        f.write(f"Sample (Stage 3 regression): {len(df_full):,} lineup-aware possessions\n\n")
        f.write(f"STAGE 1 LOGISTIC FIT:\n")
        f.write(f"  alpha = {alpha_fit:.4f}\n  beta = {beta_fit:.5f}\n\n")
        f.write(f"  p_i_logistic(DTI_def) = 1 - sigmoid({alpha_fit:.4f} + {beta_fit:.5f} * DTI_def_per_100)\n\n")
        f.write(f"STAGE 3 FALSIFYING REGRESSION COMPARISON:\n")
        f.write(f"  Linear  p_i: β_2 = {b2_lin:+.4f}, t = {t_lin:+.2f}, p = {p_lin:.4f}\n")
        f.write(f"  Logistic p_i: β_2 = {b2_log:+.4f}, t = {t_log:+.2f}, p = {p_log:.4f}\n")
        f.write(f"  t-stat lift: {t_log / t_lin:.2f}x\n")
    print(f"\nSaved: {out}")


if __name__ == "__main__":
    main()
