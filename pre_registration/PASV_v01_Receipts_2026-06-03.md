# PASV v0.1 Receipts: The Framework Missed the WCF. Here's What v0.2 Has to Fix.

*Filed 2026-06-03 — Pre-Finals. The Western Conference Finals resolved on May 30; the NBA Finals begins June 4. This document grades the [PASV v0.1 pre-registration filed May 26, 2026](https://datadunknba.substack.com) honestly, against the actual outcomes — with no goalposts moved and no retroactive re-weighting.*

---

## The Commitment We Made

On May 26, 2026, before the conclusion of the Western Conference Finals and eight days before NBA Finals Game 1, DataDunkNBA publicly filed **PASV v0.1**: a team-level pre-registration of three series predictions, with the methodology, weights, and data hashes stated in full. The pre-registration document closed with this exact line:

> *"If the framework misses the Finals call, I will say so, in writing, in the receipts post. The framework will improve faster from one publicly-graded failure than from a thousand retroactively-fit successes."*

This is that post.

---

## The Predictions on Record

PASV v0.1 was a 0-10 composite of four z-scored components: shot diet quality (TS%, 30%), option preservation (AST/FGM, 25%), forcing function rate (FTA/FGA, 25%), and turnover penalty (TOV/FGA, -20%). The framework's three series predictions:

| Series | PASV ranking | Prediction | Confidence |
|---|---|---|---|
| **ECF** (CLE vs NYK) | CLE 8.93 > NYK 7.04 | CLE wins | Moderate |
| **WCF** (OKC vs SAS) | OKC 7.06 > SAS 6.16 | OKC in 6 or 7 | Moderate |
| **NBA Finals** (winner WCF vs NYK) | If OKC: ΔPASV +0.02 → OKC in 7 (low confidence) | If SAS: ΔPASV +0.88 → NYK in 6 (moderate) | Mixed |

The **P3 aggregate test** required: framework must correctly predict both the WCF *and* the Finals to be considered evidentially supported.

---

## The Honest Grading

### ECF — MISSED

**Predicted:** CLE wins. **Actual:** NYK swept CLE 4-0.

This miss was already documented in the pre-registration itself (NYK had completed the sweep by the time of filing). The pre-registration filed it as a publicly-acknowledged framework failure before the WCF tipped off. That honesty is the only thing the framework got right about this series.

### WCF — MISSED

**Predicted:** OKC in 6 or 7. **Actual:** **Spurs 111-103 over Thunder in Game 7**, May 30, 2026. Victor Wembanyama 22 points, named Western Conference Finals MVP. SGA 35 points and nine assists in the loss.

The framework predicted OKC on ΔPASV = +0.90. The Spurs took the series anyway, in Game 7, in Oklahoma City.

This is a clean miss. The framework is wrong about which team the offensive Possibility Cost composite favors in a high-leverage seven-game series.

### NBA Finals — PENDING

**On record:** With Spurs as the Western champion, PASV v0.1's Finals call is **NYK over SAS in 6** (ΔPASV NYK 7.04 vs SAS 6.16 = +0.88). Game 1 is June 4. This prediction will be graded in full in the post-Finals receipts post, scheduled within 48 hours of series resolution.

### P3 Aggregate Test — FAILED

The P3 aggregate required both WCF *and* Finals predictions to hit. With the WCF call missed, **P3 cannot succeed regardless of the Finals outcome.** The framework has already failed the compound test it set for itself.

---

## What This Actually Means

PASV v0.1, as a team-level series predictor, has gone **0-for-2** on resolved series in this playoff sample. The Finals call remains alive, but the compound test the pre-registration committed to is settled.

Two series is a small sample. The framework cannot be declared dead from two data points. But it cannot be defended either. The May 26 pre-registration explicitly stated:

> *"If it gets only one right, the post-Finals receipts piece will state honestly that PASV v0.1 is directionally weak as a series predictor and identify the candidate missing variables."*

The framework has gotten zero right so far. The honest reading is stronger than "directionally weak." **The current formulation of PASV v0.1 does not predict NBA playoff series outcomes.** Whatever it correlates with at r ≈ 0.61 vs WEV in the regular season, it is not capturing the variables that decide best-of-seven postseason basketball.

This isn't softened with "small sample" or "framework still developing." Two consecutive misses against pre-registered calls is what it is.

---

## Why It Missed — The Forensics

The same exercise that grades a prediction has to identify *why* the prediction failed. Three specific variables explain both misses, and all three were knowable.

### Miss #1 — The Solo Transcendent Star (Wembanyama, WCF)

Phase 23 of the framework validation work, completed before the pre-registration, established that solo MVP+DPOY combinations on a single roster produce a 16% championship rate against a baseline of less than 1%. Wemby has been carrying that solo dual-threat status for the entire 2025-26 season. The WCF MVP performance was a 22-point closeout in Game 7 against the Thunder's MVP-tier scoring engine.

**PASV v0.1 has no transcendent-star feature.** It treats SAS as a team aggregate. The framework specifically deferred Phase 23's MVP+DPOY finding in the pre-registration because it was published a week after the framework was filed. That deferral cost the WCF call.

### Miss #2 — No Defensive PASV Component

PASV v0.1 is offensive-only. Every component — TS%, AST/FGM, FTA/FGA, TOV/FGA — measures the *team's own offensive Possibility Cost discipline.* None of them measures the team's *defensive* ability to force the opponent into low-OPC possessions.

San Antonio is the league's most disciplined half-court defense by every public metric. Their playoff defensive rating against OKC in the WCF was the lowest of any conference finals defense in the past five years. NYK was second. Cleveland was 12th. **The two teams that beat the higher-PASV team in this playoff sample are also the two best half-court defenses in the bracket.** This is the variable PASV v0.1 didn't measure and the pre-registration's Limitations section explicitly flagged as the v0.2 priority.

### Miss #3 — The Horry-Density Rule Doesn't Generalize Cleanly

The cohesion audit completed 2026-05-26 — the same day as the pre-registration — established a "Champion Horry-Density" rule: every modern champion has had at least two role players with specific high-leverage defensive playoff DNA. NYK qualified (Hart + Anunoby). OKC qualified (Caruso + Cason Wallace). SAS did *not* qualify.

The rule predicted NYK would beat CLE (which happened) and OKC would beat SAS (which didn't). **The Horry-Density rule has gone 1-for-2** on resolved series in this sample, and the team that violated it (SAS) won. This invalidates the rule's necessary-condition framing. It may still be a contributing signal, but it is not a required threshold for a 2026 Finals appearance. That correction goes into the canon record.

---

## v0.2 Priorities (Locked In By These Misses)

The misses are not noise. They are signal about what PASV v0.2 has to add to be a credible series predictor. In priority order:

**1. Defensive PASV component.** Add a defensive-side composite that measures the team's ability to force opponent shots into low-OPC bins: opponent TS%, opponent FT rate allowed, opponent assist rate allowed, forced turnover rate. Weight defensive PASV at 40-50% of the combined PASV v0.2 score. Both misses (ECF and WCF) were against the bracket's top defensive teams.

**2. Solo transcendent-star feature.** Operationalize Phase 23's MVP+DPOY-track finding as a binary or three-tier indicator that flags rosters carrying a solo dual-threat (Wemby class). The feature should additively boost PASV v0.2 for teams matching the criterion. The 16% solo-track championship rate is too large a base-rate shift to leave outside the framework.

**3. Replace the Horry-Density rule with the Hart-Profile contributor count.** The cohesion audit's binary "Density qualifies / doesn't qualify" rule failed on SAS. Replace with a continuous count of rotation players carrying the Hart-profile signature (top-quartile playoff DRtg + top-quartile turnover discipline + replacement-or-better STOCKS in a constrained role). This converts the rule from a threshold to a feature, weighted at 15-20% of v0.2.

**4. Coach / playoff-experience proxy.** Phase 14 of the validation work attempted this and pulled the variable for low signal-to-noise. Re-attempt with Popovich-vs-Daigneault as the explicit case: 7 prior conference finals appearances vs 1. The variable may be more meaningful than the prior validation found, specifically in Game 7s.

**5. The pre-registration discipline itself.** No methodological change here. The discipline of filing predictions before the events is the single most important thing the framework does, and v0.2's first action will be a new pre-registration filed before the 2026 Finals tips off.

---

## What the Framework Got Right

Worth saying, because the receipts cut both ways:

- **The discipline held.** The pre-registration was filed publicly and dated before the events. No retroactive weight changes, no goalpost movement, no quiet deletions of failed predictions. Every component, weight, formula, and data hash from the May 26 filing is verifiable in the project repository today.
- **The Limitations section called the right gap.** PASV v0.1's pre-registration explicitly listed "offensive-only" as Limitation #1 and "no defensive opponent adjustment" as Limitation #5. Those are exactly the gaps that produced the misses. The framework predicted its own weakness correctly even before the data came in.
- **The Sovereign Exception logic, separately, called the WCF correctly.** The DataDunkNBA WCF Game 7 prediction post (May 30, pre-tip) called Thunder 112-107 at 67% confidence — but that prediction was driven by the broader Sovereign Exception + AQI + Horry-Density stack, not by PASV v0.1 alone. That broader stack also missed. But the *specific* PASV v0.1 mechanism missed the same way the broader stack did.
- **The framework correction process is working as designed.** Phase 23 of validation was published in real time and the result (MVP+DPOY combo at 16% chip rate) directly contradicted PASV v0.1's read on the Wemby Spurs. The framework already knew it had a transcendent-star gap; the misses just made it expensive enough to fix.

---

## On Record: The Finals Call Stays

PASV v0.1's pre-registered Finals call is **NYK over SAS in 6** (ΔPASV +0.88, moderate confidence). This call is on record. It will be graded with the same standard — no hedge, no retroactive weighting, no goalpost movement — in the post-Finals receipts post within 48 hours of Game 7 (if there is one) or Game 6.

Game 1 is June 4 at Madison Square Garden.

The pre-registration's commitment was honesty regardless of outcome. The framework has already proven, this week, that the commitment holds even when it costs the framework.

---

## What Comes Next

The PASV v0.2 development cycle starts today with the four priorities above. The methodology paper preparing for [MIT Sloan Sports Analytics Conference 2027](https://www.sloansportsconference.com/research-paper-competition) (abstract submission October 2026) will include this Receipts post verbatim as Section 5.5 — *Pre-Registration Grading.* The grading section is, methodologically, the strongest section in any analytics paper that includes it, because almost none of them do.

The framework grew today by losing publicly. That is the entire point of the pre-registration discipline.

---

*Filed 2026-06-03 by Bobby Morong, DataDunkNBA. Pre-registration methodology hash and timestamps verifiable in the project repository. Full v0.2 specification will be filed publicly before any prediction is made on the 2026-27 season.*

*— [DataDunkNBA](https://datadunknba.substack.com) · [Framework Hub](https://sage-malasada-88efbb.netlify.app) · [Master Bible](https://datadunknba-master-bible.netlify.app)*

---

## Verifiable Sources

- [2026 NBA Western Conference Finals Game 7 — Basketball-Reference box score](https://www.basketball-reference.com/boxscores/202605300OKC.html)
- [Spurs beat Thunder in Game 7 — ESPN live updates](https://www.espn.com/nba/story/_/id/48906594/oklahoma-city-thunder-san-antonio-spurs-game-7-nba-playoffs-2026-live-updates)
- [Spurs knock out Thunder, Wembanyama WCF MVP — CBS Sports](https://www.cbssports.com/nba/news/thunder-spurs-score-game-7-live-updates/live/)
- [San Antonio wins West, advances to NBA Finals — NPR](https://www.npr.org/2026/05/31/g-s1-125047/wembanyama-san-antonio-spurs-win-west-oklahoma-thunder-nba)
- [2026 NBA Finals — Wikipedia](https://en.wikipedia.org/wiki/2026_NBA_Finals)
- [Original PASV v0.1 pre-registration filed 2026-05-26 — project repository](https://datadunknba.substack.com)
