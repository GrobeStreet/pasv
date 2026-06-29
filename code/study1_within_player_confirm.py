"""
Study 1 — INDEPENDENT CONFIRMATION of the within-player fixed-effects verdict.
=============================================================================

This is a CLEAN-ROOM re-test written from scratch. It does NOT reuse
study1_within_player.py's demeaning-by-hand approach. Instead it uses three
DIFFERENT estimators to triangulate the same question:

  Q: Conditional on a player's identity (player fixed effects), does each
     shot-decision predictor (PASV, Skinner_gap, raw xPTS) explain any of the
     variation in REALIZED FG points?

Methods:
  (1) Pooled OLS with explicit player dummies (statsmodels C(player)). For each
      predictor separately, report the within (partial) R^2 attributable to the
      predictor AFTER absorbing player FE, plus the predictor's t-stat.
  (2) NESTED MODEL TEST. Base = xPTS + player FE. Full = xPTS + PASV + player FE.
      Does adding the V* term (PASV) improve fit conditional on xPTS already
      being in? Report F-test p-value, ΔR^2, ΔAIC. This is the sharp test:
      PASV = xPTS - V*, so adding PASV to a model with xPTS is exactly a test
      of whether the -V* term carries independent signal.
  (3) Robustness: within-player median-split lift at min_shots = 30 AND 50.

The within-player demeaning is done via the Frisch-Waugh-Lovell theorem
(residualize both y and x on player dummies, then regress) for the partial-R^2
numbers, and via statsmodels OLS with C(player) for the nested F-test. Both
should agree.

Engine reused only for the SCORE DEFINITIONS (xPTS, V*, PASV, Skinner) so we
test the same metrics; the statistical machinery is independent.

Author: independent verification — 2026-06-25
"""
import os
import sys
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "baselines"))

import pasv_per_shot as eng
from skinner_2012 import compute_cutoff_schedule

# Data lives in the sandbox mount, not the repo dti_data
DTI_CANDIDATES = [
    "/sessions/vibrant-confident-faraday/mnt/Basketball Stats Book/dti_data",
    os.path.abspath(os.path.join(HERE, "..", "..", "dti_data")),
]
DTI = next((p for p in DTI_CANDIDATES if os.path.isdir(p)), DTI_CANDIDATES[0])


def residualize_on_fe(y, fe_codes):
    """FWL: subtract group means (player FE) -> within residual."""
    s = pd.Series(np.asarray(y, float))
    grp = pd.Series(fe_codes)
    return (s - s.groupby(grp).transform("mean")).values


def within_partial_r2(df, pred_col, y_col, fe_col):
    """
    Partial R^2 of `pred_col` after absorbing player FE, via FWL:
      1. residualize y on FE
      2. residualize x on FE
      3. R^2 of OLS y_res ~ x_res  ==  squared partial correlation
    Returns (r, partial_R2, t_stat, n).
    """
    fe = df[fe_col].values
    yr = residualize_on_fe(df[y_col].values, fe)
    xr = residualize_on_fe(df[pred_col].values, fe)
    m = np.isfinite(yr) & np.isfinite(xr)
    yr, xr = yr[m], xr[m]
    n = len(yr)
    if xr.std() == 0 or yr.std() == 0:
        return np.nan, np.nan, np.nan, n
    r = np.corrcoef(xr, yr)[0, 1]
    # t-stat with df reduced by #players (FE absorbed) + 1
    n_players = df[fe_col].nunique()
    dof = n - n_players - 1
    t = r * np.sqrt(dof / (1 - r * r)) if r * r < 1 else np.inf
    return r, r * r, t, n


def median_split_lift(df, score_col, pts_col, by, min_shots):
    gaps, wins, n = [], 0, 0
    for _, g in df.groupby(by):
        if len(g) < min_shots:
            continue
        med = g[score_col].median()
        hi = g[g[score_col] > med][pts_col]
        lo = g[g[score_col] <= med][pts_col]
        if len(hi) < 5 or len(lo) < 5:
            continue
        gap = hi.mean() - lo.mean()
        gaps.append(gap); wins += int(gap > 0); n += 1
    return (np.mean(gaps) if gaps else np.nan,
            (wins / n) if n else np.nan, n)


def main():
    train = eng.prepare(eng.load_poss(os.path.join(
        DTI, "poss_v3_2024-25_Regular_Season.parquet")))
    test = eng.prepare(eng.load_poss(os.path.join(
        DTI, "poss_v3_LINEUPS_2024-25_Playoffs.parquet")))

    xpts_tab = eng.fit_xpts(train)
    cont_tab = eng.fit_continuation_playervalue(train)
    cutoffs = compute_cutoff_schedule()
    fb_x = float(np.mean(list(xpts_tab.values())))
    fb_v = cont_tab["_league_mean_"]

    s = eng.compute_scores(test, xpts_tab, cont_tab, cutoffs, fb_x, fb_v)
    by = "primary_offensive_player_id"

    counts = s.groupby(by).size()
    keep = counts[counts >= 30].index
    s = s[s[by].isin(keep)].copy()
    s["pid"] = s[by].astype("category")
    n_players = s["pid"].nunique()

    # Diagnostic: how much does V* vary WITHIN a player? If ~0, PASV and xPTS
    # are identical up to a player-constant shift -> identical within-FE.
    vstar_within_std = s.groupby(by)["Vstar"].transform("std")
    frac_zero_within = (vstar_within_std.fillna(0) < 1e-9).mean()

    out = []
    P = out.append
    P("PASV Study 1 — INDEPENDENT CONFIRMATION (different estimators)")
    P("=" * 70)
    P(f"Data dir: {DTI}")
    P(f"Calibrate: 2024-25 RS | Test: 2024-25 Playoffs (held out)")
    P(f"Players >=30 playoff FGA: {n_players} | shots pooled: {len(s):,}")
    P("")

    # ---- DIAGNOSTIC on V* within-player variance --------------------------
    P("[DIAG] Does V* vary WITHIN a player's own shots?")
    P(f"  mean within-player SD of V*    = {vstar_within_std.mean():.5f}")
    P(f"  fraction of shots w/ ~0 within-V* variance = {frac_zero_within:.3f}")
    P(f"  corr(PASV, xPTS) raw           = {s['PASV'].corr(s['xPTS']):.4f}")
    # within-player correlation of PASV residual vs xPTS residual
    pasv_w = residualize_on_fe(s["PASV"].values, s[by].values)
    xpts_w = residualize_on_fe(s["xPTS"].values, s[by].values)
    mm = np.isfinite(pasv_w) & np.isfinite(xpts_w)
    P(f"  corr(PASV_within, xPTS_within) = "
      f"{np.corrcoef(pasv_w[mm], xpts_w[mm])[0,1]:.4f}")
    P("")

    # ---- METHOD 1: partial R^2 after player FE (FWL) ----------------------
    P("[METHOD 1] Within-player partial R^2 via FWL (residualize on player FE)")
    P("-" * 70)
    P(f"{'Predictor':<14}{'within-r':>11}{'partial-R2':>12}{'t-stat':>10}{'n':>9}")
    m1 = {}
    for name, col in [("PASV", "PASV"), ("Skinner_gap", "Skinner_gap"),
                      ("raw xPTS", "xPTS")]:
        r, r2, t, n = within_partial_r2(s, col, "fg_pts", by)
        m1[name] = (r, r2, t, n)
        P(f"{name:<14}{r:>11.4f}{r2:>12.4f}{t:>10.3f}{n:>9}")
    P("-" * 70)
    P(f"  partial-R2  PASV - Skinner = {m1['PASV'][1]-m1['Skinner_gap'][1]:+.4f}")
    P(f"  partial-R2  PASV - rawxPTS = {m1['PASV'][1]-m1['raw xPTS'][1]:+.4f}")
    P("")

    # ---- METHOD 1b: statsmodels OLS with C(player) to cross-check ----------
    P("[METHOD 1b] statsmodels OLS y ~ predictor + C(player), single-predictor")
    P("-" * 70)
    P(f"{'Predictor':<14}{'coef':>11}{'t':>9}{'p':>11}{'R2(full)':>11}")
    base_fe = smf.ols("fg_pts ~ C(pid)", data=s).fit()
    r2_fe_only = base_fe.rsquared
    P(f"{'(player FE only)':<14}{'':>11}{'':>9}{'':>11}{r2_fe_only:>11.4f}")
    for name, col in [("PASV", "PASV"), ("Skinner_gap", "Skinner_gap"),
                      ("raw xPTS", "xPTS")]:
        mdl = smf.ols(f"fg_pts ~ {col} + C(pid)", data=s).fit()
        coef = mdl.params[col]; tval = mdl.tvalues[col]; pval = mdl.pvalues[col]
        P(f"{name:<14}{coef:>11.4f}{tval:>9.3f}{pval:>11.3e}{mdl.rsquared:>11.4f}")
    P("")

    # ---- METHOD 2: NESTED F-TEST (the sharp question) ---------------------
    P("[METHOD 2] NESTED TEST: does adding PASV to {xPTS + player FE} help?")
    P("  Base : fg_pts ~ xPTS + C(player)")
    P("  Full : fg_pts ~ xPTS + PASV + C(player)   (PASV = xPTS - V*)")
    P("-" * 70)
    base = smf.ols("fg_pts ~ xPTS + C(pid)", data=s).fit()
    full = smf.ols("fg_pts ~ xPTS + PASV + C(pid)", data=s).fit()
    # F-test of the added PASV term
    ftest = full.compare_f_test(base)  # (F, p, df_diff)
    P(f"  Base  R2={base.rsquared:.5f}  AIC={base.aic:.2f}")
    P(f"  Full  R2={full.rsquared:.5f}  AIC={full.aic:.2f}")
    P(f"  ΔR2 (full-base)       = {full.rsquared-base.rsquared:+.6f}")
    P(f"  ΔAIC (full-base)      = {full.aic-base.aic:+.3f}  "
      f"({'PASV helps' if full.aic<base.aic else 'PASV does NOT help'})")
    P(f"  F-test F              = {ftest[0]:.4f}")
    P(f"  F-test p-value        = {ftest[1]:.4f}   <-- KEY NUMBER")
    P(f"  PASV coef in full     = {full.params.get('PASV', float('nan')):+.5f}")
    P(f"  PASV t in full        = {full.tvalues.get('PASV', float('nan')):+.3f}")

    # Reverse nested test for completeness: add xPTS to {PASV + FE}
    base_p = smf.ols("fg_pts ~ PASV + C(pid)", data=s).fit()
    full_p = smf.ols("fg_pts ~ PASV + xPTS + C(pid)", data=s).fit()
    ftest_p = full_p.compare_f_test(base_p)
    P("")
    P("  [reverse] add xPTS to {PASV + FE}:")
    P(f"    ΔR2={full_p.rsquared-base_p.rsquared:+.6f}  F={ftest_p[0]:.3f}  "
      f"p={ftest_p[1]:.4f}  (xPTS adds signal over PASV?)")
    P("")

    # Also test Skinner nested vs xPTS (sanity: PASV>Skinner claim)
    full_sk = smf.ols("fg_pts ~ xPTS + Skinner_gap + C(pid)", data=s).fit()
    fsk = full_sk.compare_f_test(base)
    P(f"  [Skinner] add Skinner_gap to {{xPTS+FE}}: ΔR2="
      f"{full_sk.rsquared-base.rsquared:+.6f}  p={fsk[1]:.4f}")
    P("")

    # ---- METHOD 3: robustness median-split lift at 30 and 50 --------------
    P("[METHOD 3] Within-player median-split lift (robustness to min_shots)")
    P("-" * 70)
    for thr in (30, 50):
        P(f"  min_shots = {thr}:")
        P(f"    {'Predictor':<14}{'lift(PPP)':>12}{'%players up':>13}{'n_pl':>7}")
        res = {}
        for name, col in [("PASV", "PASV"), ("Skinner_gap", "Skinner_gap"),
                          ("raw xPTS", "xPTS")]:
            lift, ws, npl = median_split_lift(s, col, "fg_pts", by, thr)
            res[name] = lift
            P(f"    {name:<14}{lift:>+12.4f}{ws*100:>12.1f}%{npl:>7}")
        order = sorted(res.items(), key=lambda kv: -(kv[1] if np.isfinite(kv[1]) else -9))
        P(f"    ordering (high->low lift): "
          f"{' > '.join(f'{k}({v:+.3f})' for k,v in order)}")
        P("")

    # ---- VERDICT ----------------------------------------------------------
    P("=" * 70)
    P("VERDICT")
    P("-" * 70)
    d_xpts = m1['PASV'][1] - m1['raw xPTS'][1]
    d_skin = m1['PASV'][1] - m1['Skinner_gap'][1]
    pval = ftest[1]
    P(f"  Method1 partial-R2: PASV-xPTS = {d_xpts:+.4f}, "
      f"PASV-Skinner = {d_skin:+.4f}")
    P(f"  Method2 nested F p (PASV | xPTS) = {pval:.4f}, "
      f"ΔAIC = {full.aic-base.aic:+.2f}")
    if abs(d_xpts) <= 0.005:
        c1 = "PASV approximately EQUALS raw xPTS within player"
    elif d_xpts > 0:
        c1 = "PASV BEATS raw xPTS within player"
    else:
        c1 = "PASV LOSES to raw xPTS within player"
    c2 = "BEATS" if d_skin > 0.001 else ("TIES" if abs(d_skin) <= 0.001 else "LOSES to")
    P(f"  -> {c1}; PASV {c2} Skinner.")
    if pval < 0.05:
        P(f"  -> Conditional on xPTS, V* term IS significant (p={pval:.4f}).")
    else:
        P(f"  -> Conditional on xPTS, V* term is NOT significant (p={pval:.4f}).")
        P(f"     => original 'within-player equivalent to xPTS' conclusion HOLDS.")

    text = "\n".join(out)
    print(text)
    rp = os.path.join(HERE, "..", "results")
    os.makedirs(rp, exist_ok=True)
    with open(os.path.join(rp, "study1_within_player_confirm.txt"), "w") as f:
        f.write(text + "\n")


if __name__ == "__main__":
    main()
