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

Panel: 1,131 regular-season→playoff player-seasons, 2017–2025. Flags defined on 2017–2022; tested on **held-out 2023–2025**.

| | Train 2017–22 | **Held-out 2023–25** | Full panel |
|---|---|---|---|
| Schemable-big RS→PO AQI drop | −0.197 | **−0.190** | −0.194 |
| Recall (star collapses flagged) | 92% | **100%** | 95% |

**Paint-bound anchors decline systematically out-of-sample; stretch bigs hold steady.** That effect is the contribution. On the full population NPSS matches the regression baseline (r ≈ 0.71) *by construction* — its value is isolating *which* stars sit in the danger profile, not a higher correlation. The precise collapse-rate multiplier is full-panel descriptive only (the regular-season-star tier is small, n=71); see `results/Validation_NPSS_HeldOut_2026-06-29.md` for the honest bounds.

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
│   ├── SSAC27_NPSS_Abstract_v1_2026-06-29.md
│   └── Framework_NPSS_v0.2.md
└── results/
    └── Validation_NPSS_HeldOut_2026-06-29.md
```

## Honest limitations
- Single panel (2017–2025); penalties fit on it. Held-out *temporal* split confirms the schemable-big effect generalizes; the star-tier sample (71) limits the precision of the collapse-rate multiplier.
- AQI uses BPM as an individual net-rating proxy (Basketball-Reference carries no on/off net rating) — same convention as the PASV project.
- NPSS is a validated *screen*, not a point predictor; it does not beat regression-to-mean on aggregate fit, and does not claim to.
