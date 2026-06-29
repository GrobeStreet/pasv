# PASV Study 1 — Per-Shot PASV vs Skinner 2012 (Held-Out OOS)

**Date:** 2026-06-25 · **Author:** Bobby Morong (DataDunkNBA) · **Status: `Needs Check` → informs paper Section 5 reframing**
**Compute:** `code/pasv_per_shot.py`, `code/run_study1.py`, `code/study1_possession_level.py`
**Data:** `dti_data/poss_v3_2024-25_Regular_Season.parquet` (calibrate) · `dti_data/poss_v3_LINEUPS_2024-25_Playoffs.parquet` (held-out test)

---

## What we ran

The per-shot engine that the SSAC27 tracker listed as *"engine built, data join needed — NOT YET COMPUTED."* It is now built and run on real possession data.

- **PASV per shot** = `xPTS(shot) − V*(s*)`, where `xPTS` is a calibrated 6-cell shot-quality model and `V*(s*)` is the continuation value of declining the shot (operationalized as the mean shooting value of the other four offensive players on the floor — a publicly-reproducible coarse-EPV analog, no tracking data).
- **Skinner 2012 baseline** = `xPTS − f*(τ)` from `code/baselines/skinner_2012.py`.
- **Out-of-sample design:** calibrate xPTS + player-values on the 2024-25 regular season (219,527 FG attempts); test on the held-out 2024-25 playoffs (14,377 FG attempts). Player-values come from RS (leakage-clean); only lineup composition is read from test possessions.

## The xPTS model holds up (independent audit)

Calibrated points-per-FGA by cell, and the held-out playoff generalization:

| Cell | RS PPS | PO PPS | shift |
|---|---|---|---|
| 2_rim | 1.357 | 1.346 | −0.8% |
| 2_short | 0.897 | 0.885 | −1.3% |
| 2_mid | 0.884 | 0.867 | −1.9% |
| 2_long | 0.803 | 0.751 | −6.4% |
| 3_reg | 1.099 | 1.093 | −0.6% |
| 3_deep | 1.014 | 0.955 | −5.8% |

The three high-volume cells (~76% of shots) shift <2% RS→PO — a genuine OOS strength worth citing. The two cells that move (long-2, deep-3) are low-volume and move in the expected direction (playoff defenses suppress the hardest shots). **No leakage** in cell assignment. (Documented trap: do NOT enrich xPTS with `defender_heuristic` — its `shooting_foul_attribution` tag is and-1 leakage, 90.6% FG% vs 45.5% baseline.)

## The headline numbers — honest

### Player-aggregated test (n=90 players, ≥50 playoff FGA)
Ground truth = player's own realized points-per-FGA in the playoffs.

| Predictor | R² vs truth |
|---|---|
| Skinner gap | 0.109 |
| **PASV** | **0.055** |
| raw xPTS | 0.107 |

### Possession/shot-level test (n=14,377 held-out FG attempts)
Ground truth = realized points on the shot.

| Test | PASV | Skinner | raw xPTS |
|---|---|---|---|
| R² vs realized points | 0.0219 | 0.0141 | **0.0243** |
| 5-fold CV OLS R² | +0.0211 | +0.0133 | **+0.0236** |
| 5-fold CV AUC (made/miss) | 0.583 | 0.573 | **0.586** |
| PASV-sign bucket PPP split | +0.278 | (degenerate) | +0.318 |

corr(PASV, xPTS) = 0.969; corr(PASV, Skinner) = 0.85.

## What this means (two findings, both real)

**Finding 1 — PASV beats Skinner per-shot, but the aggregate test hid it.** At the shot level PASV outperforms the Skinner cutoff on every measure (R² 0.022 vs 0.014; better CV R², log-loss, AUC; its sign separates realized PPP by +0.28). The player-averaged test (PASV 0.055 < Skinner 0.109) was a **category error** — averaging a per-shot decision metric to a season player-mean collapses it onto mean xPTS, and the ground truth (own efficiency) is itself ≈xPTS, so the test mechanically rewards "looks most like xPTS." Skinner only "won" the aggregate test because its subtraction is nearly flat across players, i.e. it's a near-passthrough of xPTS.

**Finding 2 — the honest problem: PASV does not beat raw xPTS.** At the per-shot level, `corr(PASV, xPTS) = 0.969` and raw xPTS matches or slightly beats PASV on every metric. The `V*` subtraction (teammate environment) adds noise relative to the shot-points ground truth rather than signal. So as currently constructed, **PASV's decision-value-add over the shot-quality model it's built from is zero-to-negative at this validation target.**

## Why the test still can't fully judge PASV — and the fix

The deeper issue (flagged independently by design review): a per-shot *decision* metric must be validated against **possession value under a counterfactual**, not against the player's own realized efficiency. Both the current ground truths are ≈xPTS, which structurally cannot reward a metric whose whole job is to subtract the alternative. The valid test:

1. Unit = possession/shot, never player-mean.
2. Ground truth = realized possession points (have it) — but framed as a **within-player** decision test (player fixed effects): for the *same* player, do higher-PASV shots yield higher realized PPP than lower-PASV shots? That isolates decision quality from "who can score," the only axis on which PASV can legitimately beat xPTS.
3. Then head-to-head PASV vs Skinner vs xPTS on possession-outcome discrimination, not R² against an efficiency proxy.

## Verdict for the paper

- The per-shot engine **works and runs on real held-out data** — the tracker's biggest open item is closed.
- Honest current status: **PASV ≻ Skinner per-shot (real, citable), but PASV ⊁ raw xPTS** on the outcome targets tested. Reporting "PASV beats Skinner" is supportable; claiming PASV beats a shot-quality baseline is **not yet earned**.
- The within-player decision test (above) is the make-or-break next computation. If PASV beats xPTS there, that's the paper's headline. If it doesn't, the honest paper reframes PASV as *a decision-diagnosis lens, not a predictive improvement over shot quality* — still novel, less marketable.
- Do not put a per-shot R²-beats-baseline claim in the October abstract until the within-player test resolves.

*All numbers reproducible from the three scripts above on the two parquet files. Calibrate-RS / test-playoffs split; player values out-of-sample.*
