# NPSS — Net Playoff Survival Score

**The Schemable Anchor: which star bigs vanish in the playoffs, and why.**

Companion code, data, and held-out validation for the SSAC27 research-paper submission. Sibling project to PASV (this repo's root); NPSS is a separate contribution — a player-season playoff-collapse *screen*, distinct from PASV's per-shot decision value.

**Author:** Robert Morong ([DataDunkNBA](https://datadunknba.substack.com)) · **License:** MIT (repo root)

---

## What this is

NPSS flags two structural playoff-fragility profiles from regular-season public stats:

1. **Schemable Big** — a rim/glass anchor who is paint-bound (shoots few threes) and can be spaced/schemed out of a series: `big AND 3PA-rate < 0.20 AND (BLK% ≥ 2.0 OR DRB% ≥ 18)`.
2. **Hunt-Exposed** guard — high usage with little rim/perimeter deterrence: `(USG%/30) × max(0, (4 − (STL%+BLK%))/4) ≥ 0.30`.

Both are binary, computed from box + advanced stats — no tracking data required.

## The central finding (held-out)

Panel: 1,131 regular-season→playoff player-seasons, 2017–2025. Flags defined on 2017–2022; tested on **held-out 2023–2025**. Every number below is printed by `code/_npss_heldout.py` on the bundled panel; the full output is in [`results/npss_heldout_output_2026-10-15.txt`](results/npss_heldout_output_2026-10-15.txt) and the write-up in [`results/Validation_NPSS_HeldOut_2026-10-15.md`](results/Validation_NPSS_HeldOut_2026-10-15.md).

| | Train 2017–22 | **Held-out 2023–25** | Full 2017–25 |
|---|---|---|---|
| Schemable-big RS→PO AQI change | −0.197 (n=111) | **−0.190 (n=51)** | −0.194 (n=162) |
| Comparison (non-schemable) bigs | +0.022 (n=47) | **−0.108 (n=24)** | −0.022 (n=71) |
| Star-collapse recall | 61.5% (8/13) | **66.7% (4/6)** | 63.2% (12/19) |
| Precision | 38.1% | 36.4% | 37.5% |
| Specificity | 64.9% | 53.3% | 61.5% |
| Lift (flagged ÷ not-flagged collapse rate) | 2.21× | 1.82× | 2.09× |

**What holds:** paint-bound anchors lose about 0.19 AQI from regular season to playoffs, and the size of that decline is the same in training and in the unseen 2023–25 seasons.

**What narrows out of sample:** comparison bigs held roughly steady in training (+0.022) but fell −0.108 in the held-out years, so the held-out gap between schemable and comparison bigs is about 0.08, on 24 comparison players. A full paper reports both numbers.

**Recall:** the corrected held-out recall is **66.7% (4 of 6)**, with precision and specificity shown above. An earlier version of this README reported 100% held-out recall; that figure came from a held-out script that treated every non-zero continuous `hunt` value as a positive flag. It is retired. The corrected rule is `hunt >= 0.30`.

## Reproduce

```bash
cd npss
python3 code/_npss_heldout.py     # prints the train / held-out / full-panel table above
```

Reads the bundled `data/npss_panel.json` (self-contained; no external data needed).

## Layout

```
npss/
├── code/
│   ├── _schemable.py        # the schemable-big flag logic
│   ├── _npss_v2.py          # NPSS v0.2 model (expected playoff AQI + 2 penalties)
│   ├── _npss_heldout.py     # held-out temporal validation (train 2017-22 / test 2023-25)
│   └── _npss_verdict.py     # backtest summary
├── data/
│   └── npss_panel.json      # 1,131 RS→PO player-seasons, 2017-2025 (self-contained)
├── paper/
│   ├── SSAC27_NPSS_Abstract_v1_2026-06-29.md          # as filed; contains the retired 100% recall
│   ├── SSAC27_Schemable_Big_Abstract_v2_2026-08-26.md # corrected abstract
│   └── Framework_NPSS_v0.2.md
└── results/
    ├── Validation_NPSS_HeldOut_2026-10-15.md
    └── npss_heldout_output_2026-10-15.txt
```

## Limitations
- Single panel (2017–2025); penalties fit on it. The held-out temporal split confirms the schemable-big decline; the comparison-big contrast is much weaker out of sample (see above), and the star tier (n=71 full panel, n=21 held-out) limits the precision of the collapse-rate multiplier.
- **AQI here is a BPM-based proxy.** Basketball-Reference carries no individual on/off net rating, so this panel computes AQI as BPM × usage rate × (TS% ÷ 0.550). The star tier is AQI ≥ 2.0 and a playoff "collapse" is falling below 1.75. DataDunkNBA's published AQI uses on-court net rating in place of BPM, with a 1.73 champion floor. The two are related but not interchangeable; numbers from this subproject should be cited as AQI (BPM proxy).
- NPSS is a screen, not a point predictor. On the full population it matches the regression baseline on aggregate fit and does not claim to beat it.
