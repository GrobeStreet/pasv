# SSAC27 Abstract Submission — NPSS / Schemable-Big Playoff Collapse (v1)

**Conference:** MIT Sloan Sports Analytics Conference 2027
**Track:** Basketball
**Abstract due:** October 1, 2026, 11:59 p.m. ET
**Author:** Robert Morong (DataDunkNBA) — sole author
**Draft version:** v1 — 2026-06-29
**Note:** Second submission, distinct from PASV (per-shot decision value). NPSS is a playoff-collapse screen — different question, different unit (player-season), no shared empirical result. Framing follows the held-out validation (`Validation_NPSS_HeldOut_2026-06-29.md`): lead with the OOS-validated schemable-big effect; bound the lift statistic honestly.

---

## Title

**The Schemable Anchor: Which Star Bigs Vanish in the Playoffs, and Why**

### Title alternates
- *Spaced Out: A Held-Out Test of Why Paint-Bound Anchors Decline in the Postseason*
- *The Two Profiles That Predict Which NBA Stars Collapse in June*

---

## Abstract

**Background.** Every postseason, regular-season stars decline — but not uniformly. The analytics literature models playoff performance largely as regression to the mean: postseason level is mostly regressed regular-season level. That baseline is correct but incomplete — it treats all stars as equally likely to fall, when specific *profiles* (the paint-bound anchor, the hunted small guard) collapse far more often than others. No public metric isolates which structural profiles drive that excess decline.

**Contribution.** We introduce the **Net Playoff Survival Score (NPSS)**, a player-season screen that flags two structural playoff-fragility profiles from regular-season data: a **Schemable Big** (a rim/glass anchor who is paint-bound, i.e. shoots few threes, and can therefore be spaced and schemed out of a series) and a **Hunt-Exposed** guard (high usage with little rim/perimeter deterrence, repeatedly attacked on defense). Both are binary flags computed from public box and advanced stats — no tracking data required. The contribution is not the intuition that paint-bound bigs struggle against spacing; it is the operationalized, falsifiable flag and its held-out validation.

**The central finding (held-out).** On a panel of 1,131 regular-season→playoff player-seasons (2017–2025), we define the flags on 2017–2022 and test on **held-out 2023–2025**. Schemable bigs lose **−0.19** in anchor quality (AQI, an impact-weighted star-value index combining on-court net rating, usage, and efficiency) from regular season to playoffs on the unseen years — statistically identical to the training window (−0.20) and the full panel (−0.19) — while comparison bigs hold roughly steady. The effect that the regression baseline cannot see survives out-of-sample: **paint-bound anchors decline systematically; stretch bigs do not.** The screen's two flags catch **100% of held-out star collapses** (stars falling below the anchor-quality floor).

**Honest bounds.** On the full population NPSS matches the regression baseline (r ≈ 0.71) by construction — ~70% of playoff level is simply regressed regular-season level, and no flag system beats that aggregate fit. The point of NPSS is not a higher correlation; it is isolating a structural subgroup the baseline averages over. The precise flagged-vs-unflagged collapse-rate multiplier is descriptive on the full panel (flagged stars collapse ~2× as often); we do not present it as a stable out-of-sample statistic, because the regular-season-star tier is small (71 across nine seasons). The validated, generalizing result is the schemable-big decline itself.

**Case validation.** The flag fires on the textbook collapses (Embiid 2022–23, Gobert 2025, Giannis 2023) and correctly clears bigs who stretched their range — including Embiid himself in 2025–26, whose three-point rate rose above the paint-bound threshold. Identical logic across every season; no fitting to names.

**Implications.** NPSS gives front offices and coaches a pre-playoff structural-risk screen for max-salary anchors, and names the one profile — the spaceable, paint-bound big — that most reliably loses value when the floor tightens in May.

**Open source.** Panel, flags, and held-out validation are public at github.com/GrobeStreet/pasv.

**Figures.** (1) Schemable vs non-schemable big RS→PO AQI change, train vs held-out. (2) Current $40M+ stars screened by NPSS profile.

---

## Word count
- Title: 12 words · Body: 488 · **Total: 500** ✅ (at limit; re-verify on the portal's own counter at submission)
- 5-lens review applied 2026-06-29: defined AQI inline (statistician), sharpened novelty claim (skeptic), reframed "ties"→"matches by construction" (statistician). NBA-ops + fan lenses passed clean.

## Framing notes (not part of submission)
- Leads with the OOS-validated effect (schemable-big −0.19 held out), not the lift ratio.
- States the regression-baseline tie up front — same honest posture as PASV, pre-empts "doesn't beat baseline."
- Bounds the small star-tier n explicitly so a reviewer can't spring it.
- Distinct from PASV: different question (playoff collapse vs per-shot value), different unit, no shared result — clean second submission.
- Open-source repo: NPSS code/data should be added to the pasv repo (or its own) before submission; the panel + `_npss_v2.py` + `_npss_heldout.py` are the artifacts.

## Open items
- [ ] Word-count check < 500.
- [ ] Add NPSS code + panel to a public repo (currently `_npss_*` files are local only).
- [ ] Decide: same repo as PASV (a metrics monorepo) or a separate `npss` repo.
- [ ] Optional 5-lens review like PASV got.
