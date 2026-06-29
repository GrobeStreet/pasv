"""
Study 1 — POSSESSION/SHOT-LEVEL validation of PASV vs Skinner vs raw xPTS
=========================================================================

The player-aggregated Study 1 reported R2(PASV)=0.055 vs R2(Skinner)=0.109,
so PASV lost. Hypothesis: that test is structurally unfair. It aggregates a
per-shot decision metric to player means and correlates with the player's OWN
realized scoring (which is essentially xPTS by construction), so any xPTS-like
quantity wins automatically. The honest test of a per-SHOT decision metric is
at the SHOT level: does the metric, evaluated on each individual attempt,
predict the realized outcome of THAT attempt?

This script runs that test on the held-out 2024-25 playoff file.

CALIBRATE: 2024-25 Regular Season (no off_lineup_ids)
TEST OOS : 2024-25 Playoffs LINEUPS file (has off_lineup_ids for V*)

Predictors per FG attempt:
  - PASV        = xPTS - V*   (decision metric)
  - Skinner_gap = xPTS - f*(tau)
  - raw xPTS    (reference; the shot-quality model itself)

Ground truth per FG attempt:
  - realized FG points (made_2=2, made_3=3, else 0)
  - made/miss binary

Tests:
  1. Pearson r and R2 of each predictor vs realized FG points (shot level).
  2. Out-of-sample OLS (5-fold CV on the playoff sample) predicting realized
     points; report mean CV R2 per single predictor.
  3. Out-of-sample logistic (5-fold CV) predicting made/miss; report mean CV
     log-loss and AUC per single predictor.
  4. Decision-quality framing: bucket by PASV sign and by Skinner SHOOT/HOLD,
     report realized PPP (points per shot) in each bucket and the separation.

All numbers are printed and written to results/study1_possession_level.txt.

Author: Bobby Morong / DataDunkNBA
Version: v0.1 — 2026-06-25
"""
import os
import numpy as np
import pandas as pd

import pasv_per_shot as eng
from skinner_2012 import compute_cutoff_schedule, skinner_decision

from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.model_selection import KFold
from sklearn.metrics import log_loss, roc_auc_score, r2_score

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
DTI = os.path.join(ROOT, "dti_data")
RESULTS = os.path.join(HERE, "..", "results")
os.makedirs(RESULTS, exist_ok=True)


def pearson_r2(x, y):
    x = np.asarray(x, float); y = np.asarray(y, float)
    m = np.isfinite(x) & np.isfinite(y)
    x, y = x[m], y[m]
    if len(x) < 3 or x.std() == 0 or y.std() == 0:
        return np.nan, np.nan, len(x)
    r = np.corrcoef(x, y)[0, 1]
    return r, r * r, len(x)


def cv_ols_r2(x, y, k=5, seed=0):
    x = np.asarray(x, float).reshape(-1, 1)
    y = np.asarray(y, float)
    kf = KFold(n_splits=k, shuffle=True, random_state=seed)
    scores = []
    for tr, te in kf.split(x):
        m = LinearRegression().fit(x[tr], y[tr])
        scores.append(r2_score(y[te], m.predict(x[te])))
    return float(np.mean(scores))


def cv_logit(x, y, k=5, seed=0):
    x = np.asarray(x, float).reshape(-1, 1)
    y = np.asarray(y, int)
    kf = KFold(n_splits=k, shuffle=True, random_state=seed)
    lls, aucs = [], []
    for tr, te in kf.split(x):
        m = LogisticRegression().fit(x[tr], y[tr])
        p = m.predict_proba(x[te])[:, 1]
        lls.append(log_loss(y[te], p, labels=[0, 1]))
        aucs.append(roc_auc_score(y[te], p))
    return float(np.mean(lls)), float(np.mean(aucs))


def main():
    train_path = os.path.join(DTI, "poss_v3_2024-25_Regular_Season.parquet")
    test_path = os.path.join(DTI, "poss_v3_LINEUPS_2024-25_Playoffs.parquet")

    train = eng.prepare(eng.load_poss(train_path))
    test = eng.prepare(eng.load_poss(test_path))

    xpts_tab = eng.fit_xpts(train)
    cont_tab = eng.fit_continuation_playervalue(train)
    cutoffs = compute_cutoff_schedule()
    fb_x = float(np.mean(list(xpts_tab.values())))
    fb_v = float(np.mean([v for k, v in cont_tab.items() if isinstance(k, int)]))

    scored = eng.compute_scores(test, xpts_tab, cont_tab, cutoffs, fb_x, fb_v)

    # ground truth at the shot level
    scored["made"] = (scored["fg_pts"] > 0).astype(int)
    s = scored.dropna(subset=["PASV", "Skinner_gap", "xPTS", "fg_pts"]).copy()
    n = len(s)

    out = []
    def p(line=""):
        print(line); out.append(line)

    p("PASV Study 1 — POSSESSION/SHOT-LEVEL validation (held-out OOS)")
    p("=" * 68)
    p(f"Calibrate: 2024-25 RS ({len(train):,} FG attempts)")
    p(f"Test OOS : 2024-25 Playoffs LINEUPS ({n:,} FG attempts with full scores)")
    p("")
    p(f"Realized PPP (all shots): {s['fg_pts'].mean():.4f}")
    p(f"FG made rate            : {s['made'].mean():.4f}")
    p(f"corr(PASV, Skinner_gap) : {np.corrcoef(s['PASV'], s['Skinner_gap'])[0,1]:.4f}")
    p(f"corr(PASV, xPTS)        : {np.corrcoef(s['PASV'], s['xPTS'])[0,1]:.4f}")
    p(f"corr(Skinner, xPTS)     : {np.corrcoef(s['Skinner_gap'], s['xPTS'])[0,1]:.4f}")
    p("")

    # ---- 1. Pearson r / R2 vs realized FG points ----
    p("-" * 68)
    p("1. SHOT-LEVEL correlation with realized FG points (made_2=2, made_3=3, miss=0)")
    p("-" * 68)
    p(f"{'predictor':<14}{'Pearson r':>12}{'R2':>12}{'n':>10}")
    rows = {}
    for name, col in [("PASV", "PASV"), ("Skinner_gap", "Skinner_gap"), ("xPTS", "xPTS")]:
        r, r2v, nn = pearson_r2(s[col], s["fg_pts"])
        rows[name] = (r, r2v)
        p(f"{name:<14}{r:>12.4f}{r2v:>12.4f}{nn:>10,}")
    p("")

    # ---- 1b. Pearson with made/miss ----
    p("1b. SHOT-LEVEL point-biserial correlation with made/miss binary")
    p(f"{'predictor':<14}{'Pearson r':>12}{'R2':>12}")
    for name, col in [("PASV", "PASV"), ("Skinner_gap", "Skinner_gap"), ("xPTS", "xPTS")]:
        r, r2v, _ = pearson_r2(s[col], s["made"])
        p(f"{name:<14}{r:>12.4f}{r2v:>12.4f}")
    p("")

    # ---- 2. CV OLS R2 predicting realized points ----
    p("-" * 68)
    p("2. Out-of-sample 5-fold CV OLS R2 (single predictor -> realized FG points)")
    p("-" * 68)
    for name, col in [("PASV", "PASV"), ("Skinner_gap", "Skinner_gap"), ("xPTS", "xPTS")]:
        cv = cv_ols_r2(s[col], s["fg_pts"])
        p(f"  {name:<14} CV R2 = {cv:+.4f}")
    p("")

    # ---- 3. CV logistic predicting made/miss ----
    p("-" * 68)
    p("3. Out-of-sample 5-fold CV logistic (single predictor -> made/miss)")
    p("-" * 68)
    base_ll = log_loss(s["made"], np.full(n, s["made"].mean()), labels=[0, 1])
    p(f"  baseline (intercept-only) log-loss = {base_ll:.4f}")
    p(f"{'predictor':<14}{'CV log-loss':>14}{'CV AUC':>12}")
    for name, col in [("PASV", "PASV"), ("Skinner_gap", "Skinner_gap"), ("xPTS", "xPTS")]:
        ll, auc = cv_logit(s[col], s["made"])
        p(f"{name:<14}{ll:>14.4f}{auc:>12.4f}")
    p("")

    # ---- 4. Decision-quality bucketing ----
    p("-" * 68)
    p("4. DECISION-QUALITY framing: realized PPP by metric sign / decision")
    p("-" * 68)

    # PASV sign
    pos = s[s["PASV"] > 0]; neg = s[s["PASV"] <= 0]
    p("PASV sign:")
    p(f"  PASV>0  (good decision): n={len(pos):>6,}  realized PPP={pos['fg_pts'].mean():.4f}  made%={pos['made'].mean():.4f}")
    p(f"  PASV<=0 (bad decision) : n={len(neg):>6,}  realized PPP={neg['fg_pts'].mean():.4f}  made%={neg['made'].mean():.4f}")
    pasv_sep = pos['fg_pts'].mean() - neg['fg_pts'].mean()
    p(f"  PPP separation (good - bad) = {pasv_sep:+.4f}")
    p("")

    # Skinner decision
    s = s.copy()
    s["skin_shoot"] = s.apply(lambda r: skinner_decision(r["xPTS"], int(r["tau"]), cutoffs), axis=1)
    sh = s[s["skin_shoot"]]; ho = s[~s["skin_shoot"]]
    p("Skinner decision (shoot iff xPTS >= f*(tau)):")
    p(f"  SHOOT: n={len(sh):>6,}  realized PPP={sh['fg_pts'].mean():.4f}  made%={sh['made'].mean():.4f}")
    p(f"  HOLD : n={len(ho):>6,}  realized PPP={(ho['fg_pts'].mean() if len(ho) else float('nan')):.4f}  made%={(ho['made'].mean() if len(ho) else float('nan')):.4f}")
    skin_sep = (sh['fg_pts'].mean() - ho['fg_pts'].mean()) if len(ho) else float('nan')
    p(f"  PPP separation (shoot - hold) = {skin_sep:+.4f}")
    if len(ho) == 0:
        p("  NOTE: every attempt clears f*(tau) -> Skinner's binary rule never says HOLD")
        p("  on real NBA xPTS (cutoffs are in Skinner's normalized units ~0.9-1.0).")
        p("  Below we split Skinner by gap sign relative to its own MEDIAN gap so it")
        p("  gets a comparable two-bucket decision split.")
    p("")

    # Skinner gap sign split (median-centered) for a fair two-bucket comparison
    skin_med = s["Skinner_gap"].median()
    sg_hi = s[s["Skinner_gap"] >= skin_med]; sg_lo = s[s["Skinner_gap"] < skin_med]
    p("Skinner gap relative to its own median (fair 2-bucket split):")
    p(f"  high gap: n={len(sg_hi):>6,}  realized PPP={sg_hi['fg_pts'].mean():.4f}  made%={sg_hi['made'].mean():.4f}")
    p(f"  low  gap: n={len(sg_lo):>6,}  realized PPP={sg_lo['fg_pts'].mean():.4f}  made%={sg_lo['made'].mean():.4f}")
    skin_med_sep = sg_hi['fg_pts'].mean() - sg_lo['fg_pts'].mean()
    p(f"  PPP separation (high - low) = {skin_med_sep:+.4f}")
    # matched PASV median split for apples-to-apples vs the Skinner median split
    pasv_med = s["PASV"].median()
    pv_hi = s[s["PASV"] >= pasv_med]; pv_lo = s[s["PASV"] < pasv_med]
    pasv_med_sep = pv_hi['fg_pts'].mean() - pv_lo['fg_pts'].mean()
    p(f"  (matched PASV median split PPP separation = {pasv_med_sep:+.4f})")
    p("")

    # also: xPTS-above-median split as a reference for "shot quality" buckets
    med = s["xPTS"].median()
    hi = s[s["xPTS"] >= med]; lo = s[s["xPTS"] < med]
    p(f"Reference - raw xPTS above/below median ({med:.3f}):")
    p(f"  high xPTS: n={len(hi):>6,}  realized PPP={hi['fg_pts'].mean():.4f}")
    p(f"  low  xPTS: n={len(lo):>6,}  realized PPP={lo['fg_pts'].mean():.4f}")
    p(f"  PPP separation = {hi['fg_pts'].mean() - lo['fg_pts'].mean():+.4f}")
    p("")

    p("=" * 68)
    p("Summary deltas (shot-level R2 vs realized points):")
    p(f"  R2(PASV)={rows['PASV'][1]:.4f}  R2(Skinner)={rows['Skinner_gap'][1]:.4f}  R2(xPTS)={rows['xPTS'][1]:.4f}")
    p(f"  PASV - Skinner = {rows['PASV'][1]-rows['Skinner_gap'][1]:+.4f}")
    p(f"  PASV - xPTS    = {rows['PASV'][1]-rows['xPTS'][1]:+.4f}")
    p(f"  Decision separation: PASV={pasv_sep:+.4f} vs Skinner={skin_sep:+.4f}")

    with open(os.path.join(RESULTS, "study1_possession_level.txt"), "w") as f:
        f.write("\n".join(out) + "\n")
    s.to_csv(os.path.join(RESULTS, "study1_possession_level_shots.csv"), index=False)
    print(f"\nwrote results/study1_possession_level.txt")


if __name__ == "__main__":
    main()
