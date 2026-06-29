# SSAC27 Abstract Submission — PASV / Possibility Cost (v3)

**Conference:** MIT Sloan Sports Analytics Conference 2027
**Track:** Basketball
**Submission window:** opens late June 2026 · abstract due **October 1, 2026**
**Author:** Bobby Morong (DataDunkNBA) — sole author
**Draft version:** v3 — 2026-06-29
**Supersedes:** v1/v2 (2026-06-03). Reframed around the Study 1 per-shot validation (2026-06-25): the team-aggregate r≈0.61 claim is no longer the empirical headline, and the DTI team-aggregate result is reported honestly as a negative finding in the paper, not implied as a win here.

---

## Title

**Every Shot Is a Measurement: A Per-Shot Theory of Possibility Cost in the NBA**

### Title alternates
- *The Shot Forecloses the Possession: A Counterfactual Theory of Per-Shot Value in the NBA*
- *What the Shot Kills: Possibility-Adjusted Shot Value as a Per-Shot Decision Scalar*

---

## Abstract

**Background.** Two frameworks anchor the valuation of NBA possessions. Skinner (2012) modeled possession decisions as a Markov Decision Process, deriving an optimal shot-quality cutoff conditioned on the shot clock. Cervone et al. (2014) introduced Expected Possession Value (EPV), estimating a possession's worth in real time from player-tracking data. Both treat foreclosed alternatives implicitly — Skinner inside a derived threshold, Cervone inside an integral — but neither exposes an explicit, signed, per-shot grade of a shot against the alternatives it eliminates. Coaches and front offices lack a single decision-grading scalar at the unit where the decision is actually made: the shot.

**Contribution.** We introduce **Possibility-Adjusted Shot Value (PASV)**, a per-shot signed scalar in expected points:

> PASV = xPTS(shot) − V*(s*)

where xPTS is the shot's expected points and V*(s*) is the continuation value of the alternatives the shot forecloses. PASV makes explicit, at the instant of release, the possibility cost that Skinner's cutoff and Cervone's integral hold only implicitly — turning an implicit threshold into an operational, signed, per-decision grade.

**A closed-form theorem.** We derive a **Holding-Math Theorem**: under a per-action defender execution rate p, the probability of inducing at least one defensive error across *n* sequential forcing actions is

> P(≥1 mistake) = 1 − p^(5n)

At p = 0.95, n = 5, this reaches 72.3% — formally grounding the intuition that ball-movement offenses compound advantage with possession length, and independently verifiable in seconds.

**Companion construct.** The **Option Preservation Coefficient (OPC)** measures how long a possession's decision tree stays alive before terminal extraction, distinguishing Jokić-class players who sustain mixed-strategy threats (50.3% AST%, the modern center ceiling) from those who foreclose alternatives prematurely.

**Empirical validation (held-out).** We compute per-shot PASV on the 2024-25 regular season (219,527 attempts), calibrate the shot-quality (xPTS) and continuation-value models, and test out-of-sample on the 2024-25 playoffs (14,377 attempts) — the first per-shot validation on public event data. Two findings, plainly: PASV outperforms the Skinner (2012) cutoff baseline as a per-shot grade, including under player fixed effects; but it is statistically indistinguishable from the shot-quality model, because a continuation value from event data alone varies too little within a possession to separate from xPTS. This is the correct falsifiable result, and it localizes the frontier precisely: possibility cost becomes separable from shot quality only at tracking resolution.

**Methodological commitment.** Before the 2026 Conference Finals we filed a timestamped pre-registration; the paper grades it verbatim, misses included.

**Implications.** PASV gives coaches a per-shot decision scalar and a precise statement of when possibility cost separates from shot quality. Unlike black-box learned evaluators, it is closed-form and directly interpretable — every grade decomposes into shot value minus a named alternative, the form a coach can act on.

**Open source.** All formulas, code, and held-out validation are public at github.com/GrobeStreet/pasv.

**Figures.** (1) Holding-math curve: P(≥1 mistake) vs forcing actions *n* ∈ [1,10]. (2) Held-out per-shot comparison: PASV vs Skinner vs xPTS, within-player.

---

## Word count
- Title: 14 words
- Body (Background → Figures): 486 words
- **Total: 500** ✅ (at Sloan's limit; counted via word-count script. Re-verify against the portal's own counter at submission, since counting rules for formulas/headers may differ.)
- Includes the interpretability-as-feature line (2026-06-29) added to counter the Basketball-track's ML/black-box trend, per the submission-guidelines analysis.

## What changed from v2 — and why
1. **Removed the team-aggregate r≈0.61 as the empirical centerpiece.** The Study 1 per-shot validation is now the empirical content; the team-aggregate proxy is demoted to a robustness mention in the paper, not the abstract.
2. **Removed any implied DTI win.** The real DTI team-aggregate result was negative (r=0.62 < v0.1's 0.81); per the submission tracker it is reported as an honest negative finding, not claimed here.
3. **States the honest two-part result:** PASV beats Skinner (real, citable) and ties xPTS within-player (the V* term adds nothing at event-data resolution). This is the falsification-discipline posture the paper already commits to via the pre-registration — it strengthens credibility with reviewers rather than weakening it.
4. **Reframes V* as the frontier:** "possibility cost needs tracking-grade continuation values to separate from shot quality" turns the negative into the paper's forward-looking contribution and a clean future-work hook.
5. **Figure 1 is now the Holding-Math curve** (the most independently-verifiable element) and Figure 2 is the held-out per-shot comparison — replacing the old team-ranking figure.

## Reviewer-fit notes
- Leads with the construct + the closed-form theorem (the two elements that don't depend on the empirical win).
- The empirical section is honest and falsifiable — exactly Sloan's "reproducibility" and "academic rigor" criteria.
- Does NOT claim PASV beats a shot-quality baseline (untrue on the evidence). Claims only what Study 1 supports: beats the Skinner MDP cutoff; formalizes per-shot possibility cost.
- Sole-author, public-data, AI-assisted build remains the narrative — strength, not weakness.

## Open items before submission
- [ ] Exact word-count check on final body.
- [ ] Confirm SSAC27 abstract guidelines unchanged once portal opens (page mixed stale SSAC24/25 boilerplate).
- [ ] Optional pre-submission peer review (Phillips / Narsu / Partnow) on the reframed empirical claim.
- [ ] Decide whether to run the multi-season DTI lineup ingest (β₂ p=0.083 → projected p<0.001) before the Dec full-paper deadline — not needed for the abstract.
