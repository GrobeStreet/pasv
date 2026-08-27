# SSAC27 Abstract Submission — PASV v4

**Conference:** MIT Sloan Sports Analytics Conference 2027  
**Track:** Basketball  
**Author:** Robert Morong (DataDunkNBA) — sole author  
**Repository:** https://github.com/GrobeStreet/pasv  
**Version:** v4 — 2026-08-26  
**Status:** current resubmission candidate; supersedes v3 for any new SSAC27 submission

## Title

**Every Shot Is a Measurement: Possibility-Adjusted Shot Value for NBA Decision Quality**

## Abstract

### Introduction

NBA shot-quality models estimate the value of the shot taken, but not the value of the possession alternatives that disappear when the shot is released. We ask whether that foreclosed continuation value can be made explicit as a per-shot decision grade. We introduce **Possibility-Adjusted Shot Value (PASV)**: `PASV = xPTS(shot) - V*(s*)`, where xPTS is expected shot value and V*(s*) is the value of declining the shot and continuing the possession.

### Methods

We calibrate on **219,527 field-goal attempts** from the 2024-25 NBA regular season and test out-of-sample on **14,377 playoff attempts**. xPTS is a six-cell distance-by-shot-type model fit only on the regular season. Public-event V*(s*) is estimated from the calibrated shooting value of the other four offensive players on the floor. We evaluate PASV under player fixed effects, asking whether a player's own higher-PASV shots score more than his lower-PASV shots. We compare PASV with raw xPTS and a public-event implementation of Skinner's (2012) shot-selection cutoff.

### Results

On the held-out playoffs, within-player R² is **0.0231 for xPTS, 0.0216 for PASV, and 0.0125 for the Skinner comparison**. PASV therefore improves on that classical cutoff benchmark but does not improve on shot quality. Adding PASV to xPTS plus player fixed effects produces **Delta R² = 0.00007, nested-test p = 0.31, cluster-robust p = 0.24, and worse AIC**. PASV is approximately **0.97-0.98 correlated with xPTS within player** because the public-event continuation term varies little shot to shot. An independent public-play-by-play reconstruction reproduces the same near-collinearity and shows only about **0.09 expected points** of continuation variation across the public clock proxy.

### Conclusion

PASV contributes an interpretable signed counterfactual decision framework, but the strong empirical hypothesis fails at public-event resolution: the current continuation term adds no independent predictive signal beyond xPTS. That negative result localizes the research frontier. To measure possibility cost rather than merely restate shot quality, V*(s*) must vary with possession state such as defender positioning, help configuration, transition state, and true shot-clock context. The framework and validation code are open-source at **github.com/GrobeStreet/pasv**.

## Submission checks

- Uses the required **Introduction / Methods / Results / Conclusion** structure.
- Title + abstract body are comfortably below Sloan's **fewer than 500 words** limit (approximately 340 words by a conservative local count; re-check in the portal).
- Does **not** claim PASV beats xPTS.
- Qualifies the Skinner comparison as a **public-event implementation**, avoiding a stronger claim than the available clock state supports.
- Omits the old team-aggregate correlation, OPC ceiling, Holding-Math 72.3% example, and pre-registration narrative from the abstract so the submission has one empirical spine.
- The held-out result and public-data reproduction are consistent with `results/Study1_FINAL_Verdict_2026-06-25.md` and the 2026-07-14 Section 5 public-data addendum.
