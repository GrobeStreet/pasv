# 5. Empirical Validation (v2 — reframed around the per-shot study)

**Version note (2026-06-29).** This replaces the v1 Section 5. The v1 section asserted that per-shot validation required possession-tracking data and fell back entirely to a team-aggregate proxy. That assertion was too pessimistic: Study 1 (below) performs a genuine per-shot, out-of-sample validation on public event data. The per-shot study is now the empirical headline; the team-aggregate proxy is demoted to a robustness check (5.3); the OPC ceiling (5.4) and the pre-registration grading (5.5) carry forward intact. The reframing also corrects the v1/v2 abstract's reliance on a team-aggregate correlation that a later DTI wire-up showed to be partly an artifact (see 5.3.3).

---

## 5.0 Overview

PASV is, by construction, a per-shot signed scalar (Eq. 4.2): `PASV = xPTS(shot) − V*(s*)`. A faithful empirical test must therefore operate at the shot level, not at a season aggregate. We report:

1. **Study 1 (5.1) — the core per-shot validation.** Per-shot PASV computed on the 2024-25 NBA regular season and tested out-of-sample on the held-out 2024-25 playoffs, benchmarked against the Skinner (2012) MDP cutoff and against a calibrated shot-quality (xPTS) model.
2. **The continuation-value frontier (5.2).** A precise statement of when the possibility-cost term V*(s*) is and is not separable from shot quality, and what data resolution is required to separate it.
3. **A team-aggregate robustness check (5.3).** The PASV v0.1 team proxy, reported as supporting context with its honest limitations — including the negative DTI result.
4. **The OPC ceiling (5.4)** and **the pre-registration grading (5.5)**, unchanged in substance from v1.

All results are reproducible from the open-source repository (Section 10); the per-shot engine and study scripts are `code/pasv_per_shot.py`, `code/run_study1.py`, `code/study1_within_player.py`, and `code/study1_within_player_confirm.py`.

---

## 5.1 Study 1 — Per-Shot PASV vs. Skinner (held-out, out-of-sample)

### 5.1.1 Design

We compute per-shot PASV on possession-level event data and validate it out-of-sample. The data are play-by-play-derived possession records (one row per terminal field-goal attempt) with shot type, shot distance, game-clock state, the primary offensive player, and the five-man offensive lineup on the floor.

- **Calibration sample:** 2024-25 NBA regular season — 219,527 field-goal attempts.
- **Held-out test sample:** 2024-25 NBA playoffs — 14,377 field-goal attempts. The playoff sample is a genuinely different competitive context that the calibration never observed.

All model components — the xPTS shot-quality model and the V*(s*) continuation model — are fit on the regular season only; player shooting values used by V* are likewise estimated out-of-sample. The playoffs are touched only at scoring time. This is a held-out test, not an in-sample fit.

### 5.1.2 The xPTS shot-quality model

xPTS is a six-cell expected-points lookup keyed on distance × shot type: rim, short-two, mid-two, long-two, regular three, deep three. Each cell's xPTS is the realized points-per-attempt in that cell on the calibration season. Cell assignment is leakage-free (the two-vs-three distinction is a shot-type fact, not a make/miss outcome). The calibration generalizes out-of-sample: on the three high-volume cells (≈76% of attempts) the regular-season → playoff shift is under 2 percentage points; the two cells that move materially (long-two −6.4%, deep-three −5.8%) are low-volume and shift in the expected direction of tighter playoff defense.

| Cell | Reg-season xPTS | Playoff xPTS | shift |
|---|---|---|---|
| Rim (≤3 ft) | 1.357 | 1.346 | −0.8% |
| Short (4–10 ft) | 0.897 | 0.885 | −1.3% |
| Mid (11–16 ft) | 0.884 | 0.867 | −1.9% |
| Long-two (17–21 ft) | 0.803 | 0.751 | −6.4% |
| Three (regular) | 1.099 | 1.093 | −0.6% |
| Three (deep, 27+ ft) | 1.014 | 0.955 | −5.8% |

*(We note one boundary artifact for transparency: a small share of attempts logged at exactly 22 ft but labeled two-pointers, and a set of threes recorded at distance 0, are reconciled by the label term; the net misrouting is ≈0.5% of attempts and immaterial to the cell means. We also document that a defender-presence feature available in the data must NOT be used in xPTS: its only populated value is a foul-attribution tag carrying 90.6% make rate — and-1 leakage — so enriching xPTS with it would contaminate the model with the outcome.)*

### 5.1.3 The continuation value V*(s*) and the Skinner baseline

V*(s*) is the value of declining the shot and continuing the possession. On public event data (no spatial tracking) we operationalize it as the teammate-continuation value: the mean calibrated shooting value of the other four offensive players on the floor — the alternatives the ball could move to. This is the publicly-reproducible coarse-EPV analog the framework's continuation term calls for.

The **Skinner (2012) baseline** is the signed gap `xPTS − f*(τ)`, where f*(τ) is the closed-form MDP cutoff (`code/baselines/skinner_2012.py`), evaluated on the same shots. Skinner's f*(τ) is, by its derivation, a function of clock pressure only; PASV's V* additionally depends on lineup composition, so the two are genuinely distinct constructs (a first engine version that keyed V* on the same clock proxy as Skinner produced near-collinear metrics, r=0.997, and was discarded as a construction artifact — see the repository audit `code/audit_collinearity.py`).

### 5.1.4 Result: PASV vs. Skinner vs. shot quality

We aggregate each per-shot grade to the player level on the held-out playoffs and test it under **player fixed effects** — the decisive specification for a *decision* metric, since fixed effects remove "who can score" and isolate whether a player's own higher-graded shots actually score more. (We report player fixed effects rather than a raw player-mean correlation because the latter collapses a per-shot decision metric onto season-level scoring efficiency and cannot, even in principle, distinguish PASV from xPTS; see 5.1.6.)

| Predictor | Within-player R² (held-out PO) | Median-split lift (PPP) |
|---|---|---|
| Raw xPTS (shot-quality baseline) | 0.0231 | +0.318 |
| **PASV** | **0.0216** | +0.233 |
| Skinner (2012) gap | 0.0125 | +0.237 |

Two findings:

1. **PASV outperforms the Skinner cutoff** as a per-shot grade (within-player R² 0.0216 vs. 0.0125; ΔR² = +0.0091). The signed-magnitude information PASV exposes carries decision signal the threshold-only model discards. This holds across estimators (within-player demeaning, fixed-effects OLS partial-R², median-split lift) and is robust to the minimum-shot threshold.

2. **PASV is statistically indistinguishable from the shot-quality model** at this resolution (ΔR² vs. xPTS = −0.0014). The sharp test confirms it: adding PASV to a model that already contains xPTS and player fixed effects yields no improvement (nested F-test p = 0.31; cluster-robust p = 0.24; ΔAIC = +0.97, i.e. worse; PASV's added coefficient is wrong-signed). The reverse — adding xPTS to a model containing PASV — is significant at p < 1e-5. Conditional on shot quality, the possibility-cost term carries no independent signal in this operationalization.

### 5.1.5 Interpretation

This is the correct, falsifiable result for an event-data operationalization, and it is more informative than a manufactured win would be. PASV is 0.97–0.98 correlated with xPTS within player because the teammate-continuation estimate of V* varies very little from shot to shot within a single possession context (within-player standard deviation ≈ 0.03). A continuation value that cannot move shot-to-shot cannot add shot-to-shot signal. PASV therefore beats the classical MDP baseline — a real, citable contribution at the per-shot level — but does not, with event data alone, improve on the shot-quality model it is built from.

### 5.1.6 Why player fixed effects, and not a player-mean correlation

A per-shot decision metric must be validated at the shot/possession level. Averaging PASV to a season player-mean and correlating it with the player's own scoring rate is a category error: the player-mean collapses onto mean xPTS, and the ground truth (own efficiency) is itself ≈xPTS, so such a test mechanically rewards whatever predictor most resembles xPTS and penalizes the very subtraction PASV performs. A naïve player-aggregated version of this test indeed shows PASV "losing" (R² 0.055 vs. Skinner 0.109) — an artifact of aggregation, not a finding about PASV. The fixed-effects design in 5.1.4 is the valid test, and it reverses that artifact (PASV > Skinner) while honestly reporting the xPTS tie.

---

## 5.2 The Continuation-Value Frontier

Section 5.1 localizes the construct's empirical frontier precisely. The possibility-cost term V*(s*) becomes separable from shot quality only when continuation value varies meaningfully *within* a possession — which requires resolution that public event data does not contain: defender positions and closeout state, help-side configuration, time elapsed since possession start, and transition-vs-set context. These are exactly the dimensions Cervone et al.'s EPV captures from player tracking. The empirical claim of this paper is therefore sharp and twofold: (a) PASV is a valid per-shot decision scalar that improves on the Skinner cutoff; (b) realizing its possibility-cost signal *beyond* shot quality is a tracking-data problem, and we have quantified precisely what that data must add — within-possession variance in V* on the order of the cross-player variance in xPTS. This is the paper's central forward-looking contribution and the highest-priority item for a tracking-data partnership (Section 9).

---

## 5.3 Team-Aggregate Proxy (robustness context)

### 5.3.1 Construction and result

As supporting context at the season scale, we compute a team-aggregate proxy, PASV v0.1, from four publicly-available components — Shot Diet Quality (team TS%), team-level Option Preservation (AST/FGM), Forcing-Function Score (FTA/FGA), and a turnover penalty (TOV/FGA) — z-scored across the 30 teams with pre-registered weights (30/25/25/−20; not optimized to the outcome). On the 2025 regular season it correlates with our composite team rating (WEV v3) at **r ≈ 0.81**, robust to ±0.05 weight perturbation.

### 5.3.2 Status of this result

This is a **proxy at one aggregation level above the construct** and is reported as such — supporting context, not the paper's empirical claim. The per-shot study (5.1) is the validation that matches the theory's unit of analysis.

### 5.3.3 The DTI extension — a documented negative result

A v0.2 attempt to add a fifth, defender-targeting component (DTI) to the team aggregate did **not** improve the proxy. With a TS%-deviation fallback, DTI appeared to lift the correlation to r ≈ 0.85; but wiring in the real DTI leaderboard revealed that lift to be a TS% re-weighting (double-counting efficiency), and the genuine DTI signal aggregated to team level produced r ≈ 0.62 — below the v0.1 baseline. We report this plainly: the team-aggregate DTI extension is rejected, and any earlier abstract language implying a DTI-driven team-aggregate gain is corrected by this section. The DTI substrate retains value at the possession level (the lineup-aware falsifying regression, Math Appendix §4.4), not as a team-aggregate PASV component.

---

## 5.4 OPC Proxy — Modern NBA Center Ceiling

*(Carried forward from v1, unchanged in substance.)*

The full OPC operationalization requires forcing-action tagging from tracking data. As a publicly-computable, conservative lower-bound proxy we use assist percentage (AST%): the share of teammate field goals a player assisted while on the floor. The proxy undercounts forcing actions that end in a foul, offensive rebound, or turnover, and is appropriate for within-position comparison only.

The maximum single-season center AST% in the basketball-reference player-season database is **Nikola Jokić, 50.3% (2022-23)** — roughly 15 points clear of the next center-position figure, establishing a clear modern-era ceiling for the construct. The position-stratified 2024-25 distribution confirms the expected guard > forward > center ordering, with Jokić sitting in the point-guard band — consistent with the framework's identification of him as a high-OPC positional outlier.

---

## 5.5 Pre-Registration Grading

*(Carried forward from v1, unchanged in substance — the framework's load-bearing methodological commitment.)*

On 2026-05-26, before the conclusion of the Western Conference Finals and eight days before NBA Finals Game 1, we filed a public, timestamped pre-registration of PASV v0.1 series predictions. We grade it verbatim:

| Series | Predicted | Actual | Result |
|---|---|---|---|
| ECF (CLE vs NYK) | CLE | NYK swept 4-0 | MISS (known at filing) |
| WCF (OKC vs SAS) | OKC | SAS won Game 7 | MISS |
| Aggregate P3 (both WCF + Finals correct) | — | — | FAILED |

The misses align precisely with the framework's own pre-registered limitations: PASV v0.1 is offensive-only (both losing teams fell to the bracket's top half-court defenses), carries no transcendent-solo-star feature (SAS advanced behind the league's lone MVP+DPOY-track player), and includes no defensive-coordination term (the Holding-Math Theorem's independence assumption, §4.2.5). We do not claim validation as a series predictor on the 2026 sample. We claim only that the prediction was public and falsifiable, the misses map onto the documented limitations, and those limitations define empirically-grounded v0.2 priorities (defensive component, transcendent-star feature, defender-coordination extension, strength-of-schedule adjustment).

---

## 5.6 Summary

The per-shot study (5.1) is the empirical core: on held-out playoff data, PASV grades shot decisions better than the Skinner (2012) MDP cutoff under player fixed effects, and is statistically equivalent to a calibrated shot-quality model — the possibility-cost term adding no independent signal at event-data resolution. We frame this as the correct falsifiable result and localize the frontier (5.2): separating possibility cost from shot quality is a tracking-data problem, and we specify exactly what that data must supply. The team-aggregate proxy (5.3, including the rejected DTI extension), the OPC ceiling (5.4), and the honestly-graded pre-registration (5.5) are supporting context. The paper's contribution remains primarily conceptual — the explicit per-shot signed scalar and the closed-form Holding-Math Theorem — now paired with an empirical section that matches the theory's unit of analysis and reports its results without overclaiming.

---

## Reproducibility note

Study 1 figures and tables regenerate from: `code/pasv_per_shot.py` (engine), `code/run_study1.py` (player-aggregate run), `code/study1_within_player.py` and `code/study1_within_player_confirm.py` (fixed-effects validation, five estimators), with results in `results/Study1_FINAL_Verdict_2026-06-25.md`, `results/study1_within_player.txt`, and `results/study1_within_player_confirm.txt`. Calibration: `dti_data/poss_v3_2024-25_Regular_Season.parquet`; held-out test: `dti_data/poss_v3_LINEUPS_2024-25_Playoffs.parquet`.
