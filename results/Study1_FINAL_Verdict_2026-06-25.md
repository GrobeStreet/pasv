# PASV Study 1 — FINAL Verdict (Within-Player Decision Test)

**Date:** 2026-06-25 · **Author:** Bobby Morong (DataDunkNBA) · **Status: `Evidence` — decisive, confirmed across 5 estimators**
**This supersedes the open Study 1 line in `SSAC27_SUBMISSION_TRACKER`.**

---

## The decisive test

A per-shot *decision* metric earns its keep only if, **for the same player**, his higher-PASV shots produce more points than his lower-PASV shots — beyond what raw shot quality (xPTS) already explains. Player fixed effects remove "who can score" so the test isolates decision quality. Calibrate on 2024-25 RS; test out-of-sample on 2024-25 playoffs (119 players, 13,463 pooled shots).

## Result (robust across demeaning, FE-OLS partial-R², nested F-test, AIC, cluster-robust SE)

| Predictor | within-player R² | median-split lift | % players where it works |
|---|---|---|---|
| raw xPTS | **0.0231** | +0.318 | 81.9% |
| **PASV** | **0.0216** | +0.233 | 79.0% |
| Skinner gap | 0.0125 | +0.237 | 74.1% |

- **PASV − Skinner = +0.0091** → PASV clearly beats the Skinner 2012 baseline. ✓ Real, citable.
- **PASV − raw xPTS = −0.0014** → PASV is within-player **equivalent to (a hair behind) raw xPTS**.
- **The sharp test:** add PASV to a model that already has xPTS + player FE. ΔR² = +0.00007, **F-test p = 0.31** (cluster-robust p = 0.24), **ΔAIC = +0.97 (worse)**, PASV coefficient wrong-signed. The reverse — adding xPTS to {PASV + FE} — is **p < 1e-5**. 

**Conditional on shot quality, the V\* (possibility-cost) term carries no independent signal.** xPTS strictly dominates it.

## What this means — honestly

PASV, as currently constructed, is **0.98 correlated with xPTS within player**. The possibility-cost subtraction `− V*(s*)` does not add predictive power over the shot-quality model PASV is built from. This is a genuine negative result, and it is robust — five estimators, two random-seed-independent methods, the same answer.

It is **not** a failure of the *paper*. It is a finding about *this operationalization* of V*. The teammate-continuation proxy for V* (mean shooting value of the other four players) barely varies within a player's possessions (within-player SD ≈ 0.034), so it cannot move the per-shot grade enough to matter. A V* that varied shot-to-shot with real possession state (defensive matchup, help configuration, time since possession start, transition vs. set) — the spatial-tracking EPV the original concept calls for — might. We cannot build that from public event data alone.

## Recommended paper reframing (the honest, still-novel version)

1. **Lead with PASV as a theoretical contribution + a decision-diagnosis lens**, not as a predictive-accuracy improvement over shot quality. The closed-form Holding-Math Theorem and the explicit per-shot signed-delta formalism remain novel and defensible.
2. **Report the head-to-head honestly:** PASV beats Skinner per-shot AND within-player (cite it); PASV is equivalent to xPTS within-player (state it plainly — this *is* the transparency standard the paper already commits to with the pre-registration grading).
3. **Frame V* as the open frontier:** "The possibility-cost term requires possession-resolution continuation values (tracking-grade EPV) to add signal beyond shot quality; with public event data it is equivalent to a calibrated shot-quality model. Quantifying the tracking-data lift is the natural next study." That turns the negative into a roadmap.
4. **Do NOT** put "PASV beats a shot-quality baseline" in the October abstract. It is not true on the evidence. "PASV beats the Skinner MDP cutoff and formalizes the per-shot possibility cost" is true and sufficient.

## Bottom line

The make-or-break computation resolved against the strong version of the claim and for the honest one. PASV is a real, novel per-shot formalism that beats the classical MDP baseline; it does not yet beat shot quality, and saying so is exactly the falsification discipline that is DataDunkNBA's actual edge. The paper is still submittable — reframed around the theorem, the formalism, and an honest empirical section with a clear research frontier.

*Compute: `code/study1_within_player.py`, `code/study1_within_player_confirm.py`. Results: `results/study1_within_player.txt`, `results/study1_within_player_confirm.txt`.*
