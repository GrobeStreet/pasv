# SSAC27 Abstract Submission — Schemable Big v2

**Conference:** MIT Sloan Sports Analytics Conference 2027  
**Track:** Basketball  
**Author:** Robert Morong (DataDunkNBA) — sole author  
**Repository:** https://github.com/GrobeStreet/pasv  
**Version:** v2 — 2026-08-26  
**Status:** corrected resubmission candidate; supersedes the original NPSS abstract for any new SSAC27 submission

## Title

**Spaced Out: A Held-Out Test of Paint-Bound NBA Bigs in the Playoffs**

## Abstract

### Introduction

Regular-season star value does not always survive playoff basketball. We test whether one structurally identifiable archetype — the **paint-bound anchor big** — experiences a repeatable postseason decline that a generic regression-to-the-mean baseline obscures. The practical question is whether teams can identify roster-specific playoff fragility before a series begins using only regular-season public data.

### Methods

We construct a panel of **1,131 regular-season-to-playoff player-seasons from 2017-2025**. A Schemable Big is defined from regular-season information only: a big-man/anchor profile (center or high rebounding/shot-blocking rates) that is also paint-bound, with three-point attempt share below 20%. Player impact is summarized by the repository's public-data Anchor Quality Index implementation, which combines a BPM-based impact proxy, usage, and scoring efficiency. We define the rule on **2017-2022** and evaluate it without refitting on held-out **2023-2025** seasons. The primary outcome is within-player change in anchor quality from regular season to playoffs.

### Results

In the training window, Schemable Bigs lose approximately **0.20 AQI points** from regular season to playoffs. In the unseen 2023-2025 seasons, the decline remains approximately **0.19 points**, while comparison bigs remain roughly stable. The effect therefore preserves both sign and magnitude across the temporal split. This result is narrower than the earlier Net Playoff Survival Score claim: a prior held-out script incorrectly treated every nonzero defensive-hunt score as a positive Hunt-Exposed flag. That implementation has been corrected in the open repository, and the earlier **100% collapse-recall claim is retired**. The present submission relies only on the held-out paint-bound-big result that survives the correction.

### Conclusion

Paint-bound anchor bigs show a repeatable regular-season-to-playoff erosion that survives a held-out temporal test, while comparable bigs with greater spacing capacity do not show the same decline. The result offers front offices and coaching staffs a simple, interpretable pre-playoff risk screen for roster construction and matchup planning, while illustrating the value of separating a robust subgroup effect from an overbroad predictive rule. Code, data, the corrected validation script, and the historical error record are open-source at **github.com/GrobeStreet/pasv**.

## Submission checks

- Required **Introduction / Methods / Results / Conclusion** structure.
- Comfortably below Sloan's **fewer than 500 words including title** limit (re-check in portal).
- Removes the invalid **100% held-out recall** claim.
- Does not promote the full NPSS composite.
- Defines AQI consistently with the NPSS repository's BPM-based public-data implementation.
- Uses the corrected `hunt >= 0.30` validation implementation committed on 2026-08-26.
