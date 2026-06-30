# Framework: NPSS v0.2 — The Two-Flag Playoff Collapse Screen

**Date:** 2026-06-24 · **Desk:** Research → Framework Registry candidate · **Status: `Evidence` (collapse-screen validated; NOT a point-predictor)**
**Supersedes:** NPSS v0.1 (4-factor product, `Needs Check`). Re-backtested on the same 1,131 RS→PO player-seasons (2017–2025). Labels per CLAUDE.md.

---

## What changed from v0.1
v0.1 was a 4-factor product (`AQI × PDR × GPI × Hunt`) that **failed**: it didn't beat raw AQI, the GPI term was dead at the star tier, and the archetype-PDR term fired *backwards* — it treated the biggest collapsers (Embiid, Giannis, Gobert) as "safe" playmaking bigs.

v0.2 throws out the two broken layers and rebuilds around the actual failure modes the data revealed:
1. Keep the **Hunt Tax** flag (validated in v0.1).
2. Add a **Schemable Big** flag — the missing piece that catches the Embiid/Gobert collapse.
3. Anchor everything to a **regression baseline**, because the honest truth is most playoff change is regression to the mean, and any model must be measured against that, not against zero.

---

## The formula (v0.2)
```
NPSS_v0.2 = expected_playoff_AQI  +  hunt_penalty  +  schemable_penalty

  expected_playoff_AQI = 0.050 + 0.797 × RS_AQI        [empirical regression, n=1131]

  hunt_penalty      = −0.027  if hunt_exposed,  else 0
  schemable_penalty = −0.100  if schemable_big, else 0   [4× the hunt penalty]

  hunt_exposed  = (USG%/30) × max(0, (4 − (STL%+BLK%))/4) ≥ 0.30
                  [high-usage guard with little rim/perimeter deterrence — gets hunted]

  schemable_big = big (C/PF or BLK% ≥ 2.5) AND paint-bound (3PA rate < 0.20)
                  AND rim/glass anchor (BLK% ≥ 2.0 or DRB% ≥ 18)
                  [drop-coverage anchor that can be spaced/schemed out of the series]
```
Penalties are **fit from the data** (the mean residual miss for flagged players vs. their regression expectation), not guessed.

---

## The re-backtest (1,131 RS→PO seasons, 2017–2025)

### The honest ceiling: nothing beats AQI on the full population
| Predictor | r with actual playoff AQI | MAE |
|---|---|---|
| Raw RS AQI | 0.7077 | 0.501 |
| Regression baseline | 0.7077 | 0.486 |
| NPSS v0.1 | 0.7092 | — |
| **NPSS v0.2** | **0.7091** | **0.485** |

On all 1,131 players, v0.2 ties AQI. **This is expected and worth stating plainly:** ~70% of a player's playoff level is just his regular-season level regressed toward the mean. No flag system meaningfully improves that correlation, and a framework that claimed otherwise would be overfitting. The value isn't in the r — it's in *who the flags catch.*

### Where v0.2 earns its keep: star-collapse detection
Restricting to regular-season stars (AQI ≥ 2.0, n=71), scoring a "collapse" as falling below the **1.75 anchor floor** in the playoffs:

| Group | n | Collapse rate | Mean AQI drop |
|---|---|---|---|
| **v0.2 flagged** (hunt OR schemable) | 32 | **38%** | **−0.64** |
| v0.2 not flagged | 39 | 18% | −0.24 |

- **2.1× collapse-rate separation**, up from v0.1's 1.75×.
- **Recall: v0.2 flags 12 of 19 actual star collapses (63%)** using two binary screens.
- The **schemable-big penalty (−0.10) is 4× the hunt penalty (−0.03)** — the data's verdict that paint-bound anchors are the single biggest playoff-fragility profile, and exactly the one v0.1 was blind to.

### The schemable-big flag, validated directly
| Group | n | Mean AQI drop RS→PO |
|---|---|---|
| Schemable bigs | 162 | −0.19 |
| Non-schemable bigs | 275 | **+0.01** (hold steady) |

And it catches the marquee cases v0.1 missed: **Embiid 2022 ✓, Embiid 2023 ✓, Gobert 2025 ✓, Giannis 2023 ✓** all flag schemable. (Durant 2022 correctly does *not* — he's a shooting forward whose collapse was hunt/variance-driven, caught by the other flag.)

---

## NPSS v0.2 applied — current $40M+ stars (2025-26)
**Now computed from the raw 2025-26 advanced fields** (3PA-rate, BLK%, DRB%) — identical inputs to the backtest, full fidelity. Sorted worst→best projected playoff survival.

| Player | $M | AQI | NPSS v0.2 | 3PAr | BLK% | DRB% | Flags |
|---|---|---|---|---|---|---|---|
| Zach LaVine | 47 | −0.40 | −0.29 | .46 | 0.8 | 9.4 | HUNT |
| Domantas Sabonis | 42 | 0.15 | 0.04 | .12 | 0.7 | 31.0 | HUNT, **SCHEMABLE-BIG** |
| Pascal Siakam | 46 | 0.21 | 0.19 | .25 | 1.0 | 17.4 | HUNT |
| Paul George | 52 | 0.41 | 0.38 | .50 | 1.3 | 17.1 | — |
| Anthony Davis | 54 | 0.66 | 0.48 | .11 | 4.5 | 26.7 | **SCHEMABLE-BIG** |
| Devin Booker | 53 | 0.75 | 0.62 | .31 | 0.8 | 10.7 | HUNT |
| Evan Mobley | 46 | 0.73 | 0.64 | .24 | 5.2 | 22.7 | — |
| Lauri Markkanen | 46 | 0.81 | 0.69 | .40 | 1.4 | 15.7 | — |
| Karl-Anthony Towns | 53 | 0.96 | 0.82 | .30 | 1.8 | 31.7 | — |
| LeBron James | 53 | 1.03 | 0.87 | .26 | 1.6 | 18.3 | — |
| Jaylen Brown | 53 | 1.25 | 1.02 | .26 | 1.1 | 18.1 | HUNT |
| Jamal Murray | 46 | 1.29 | 1.05 | .41 | 1.0 | 12.0 | HUNT |
| Jayson Tatum | 54 | 1.42 | 1.15 | .50 | 0.6 | 31.3 | HUNT |
| Kevin Durant | 55 | 1.42 | 1.18 | .33 | 2.3 | 14.8 | — |
| Joel Embiid | 55 | 1.81 | 1.49 | .23 | 3.6 | 20.0 | — *(see note)* |
| Stephen Curry | 60 | 2.03 | 1.67 | .61 | 1.2 | 11.7 | — |
| Kawhi Leonard | 50 | 3.06 | 2.49 | .35 | 1.2 | 18.6 | — |
| Giannis Antetokounmpo | 54 | 4.21 | 3.30 | .07 | 2.3 | 27.4 | **SCHEMABLE-BIG** |

**With real fields the live flag now matches backtest fidelity.** It catches **Giannis** (3PAr 0.07 — extreme non-shooter, textbook schemable anchor), **Anthony Davis** (3PAr 0.11, BLK 4.5), and **Sabonis** (3PAr 0.12, DRB 31) — paint-bound anchors all. And **Evan Mobley correctly does *not* flag** (3PAr 0.24 — he stretched his game), where the old approximation would have lumped him in.

### The Embiid finding — the flag is right, and here's the proof
The textbook collapse case **does not flag in 2025-26 — because Embiid changed.** His 3PA-rate by season tells the whole story, and the flag tracks it perfectly:

| Season | 3PAr | Schemable? | Note |
|---|---|---|---|
| 2017–2020 | .20–.23 | 0 | shot enough 3s |
| **2021–2024** | **.15–.19** | **1** | paint-bound — *the collapse years (incl. 2022, 2023)* |
| 2025 | .24 | 0 | re-stretched |
| **2026** | **.23** | **0** | shooting more 3s again — less schemable |

This is the opposite of a bug. The flag fired on Embiid in exactly the four paint-bound seasons that produced his playoff collapses, and correctly stopped firing when he expanded his range. **Forcing it to flag the 2026 Embiid would be fitting to a name, not the data.** Identical logic, applied across every season — that's the fidelity the join delivered.

**What v0.2 fixed:** with the raw advanced fields joined, the live flag now warns on the paint-anchored bigs (Giannis, Davis, Sabonis) the backtest validated, and correctly *clears* re-stretched bigs (Mobley, the 2026 Embiid) — the data-honest version v0.1 couldn't produce.

---

## Verdict
NPSS v0.2 is a **validated playoff-collapse *screen*, not a point *predictor*.**
- `Evidence`: two binary flags (Hunt Tax + Schemable Big) catch 63% of star collapses at a 2.1× base-rate lift. The Schemable-Big flag is the real discovery — paint-bound anchors decline while stretch bigs hold steady (−0.19 vs +0.01).
- `Canon` (honest ceiling): on the full population, playoff AQI ≈ regression of RS AQI; no flag system beats that correlation, and v0.2 doesn't pretend to. Its job is flagging *which* stars sit in the danger profiles.
- `Needs Check`: the penalty magnitudes (−0.027 / −0.100) are fit on one 2017–2025 panel; re-fit as seasons accrue. (The live flag now uses the raw 2025-26 advanced fields, so it matches backtest fidelity — that gap is closed.)

This is the framework doing exactly what it should: v0.1's failure pointed at the real fragility (schemable bigs), v0.2 built and validated a flag for it, and the result is honest about being a screen rather than overclaiming a predictor.

---

## Sources / artifacts
- Internal panel: `scrape_output/{2017–2025}_advanced.csv` + `_playoff_advanced.csv` + `_per_game.csv` (1,131 RS→PO seasons)
- Canon: `DataDunkNBA_Formula_Registry.md` (#12 AQI, #4 PDR, #17 DTI, #18 PEI)
- Compute: `_schemable.py`, `_npss_v2.py`, `_npss_v2_current.py`; data `_npss_panel.json`, `_npss_v2_current.json`
- Prior: `Framework_NPSS_Net_Playoff_Survival_Score_2026-06-24.md` (v0.1, superseded)
