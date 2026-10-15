# NPSS held-out validation (corrected rule), 2026-10-15

Run: `python3 code/_npss_heldout.py` on the bundled `data/npss_panel.json`. Raw output: [`npss_heldout_output_2026-10-15.txt`](npss_heldout_output_2026-10-15.txt).

## Design
- Panel: 1,131 regular-season → playoff player-seasons, 2017–2025 (bundled, self-contained).
- Rules were defined on 2017–2022 and are evaluated unchanged on held-out 2023–2025.
- Schemable Big: `big AND 3PA ÷ FGA < 0.20 AND (BLK% ≥ 2.0 OR DRB% ≥ 18)`.
- Hunt-Exposed: `(USG% ÷ 30) × max(0, (4 − (STL% + BLK%)) ÷ 4) ≥ 0.30`.
- Star tier: regular-season AQI ≥ 2.0. Collapse: playoff AQI < 1.75.
- AQI in this panel is a BPM-based proxy: BPM × usage rate × (TS% ÷ 0.550). See the README limitations.

## Results

| | Train 2017–22 | Held-out 2023–25 | Full 2017–25 |
|---|---|---|---|
| Player-seasons | 751 | 380 | 1,131 |
| Schemable-big RS→PO AQI change | −0.197 (n=111) | −0.190 (n=51) | −0.194 (n=162) |
| Comparison bigs RS→PO AQI change | +0.022 (n=47) | −0.108 (n=24) | −0.022 (n=71) |
| RS stars | 50 | 21 | 71 |
| Flagged collapse rate | 38.1% (n=21) | 36.4% (n=11) | 37.5% (n=32) |
| Not-flagged collapse rate | 17.2% (n=29) | 20.0% (n=10) | 17.9% (n=39) |
| Lift | 2.21× | 1.82× | 2.09× |
| Recall | 61.5% (8/13) | 66.7% (4/6) | 63.2% (12/19) |
| Precision | 38.1% | 36.4% | 37.5% |
| Specificity | 64.9% | 53.3% | 61.5% |
| Confusion (TP/FP/FN/TN) | 8/13/5/24 | 4/7/2/8 | 12/20/7/32 |

## Reading
1. The schemable-big decline replicates out of sample at the same size: −0.197 in training, −0.190 held out.
2. The contrast with other bigs is weaker out of sample. Comparison bigs fell −0.108 in 2023–25, leaving a held-out gap of about 0.08 on 24 comparison players.
3. Held-out recall of star collapses is 66.7% (4 of 6), with 36.4% precision. These are small counts and should be read with that in mind.

## Correction history
An earlier held-out script treated every non-zero continuous `hunt` value as a positive Hunt-Exposed flag, which produced a reported 100% held-out recall (README and the June 29 abstract). The script in `code/_npss_heldout.py` applies the `hunt >= 0.30` threshold; 100% is retired and 66.7% replaces it. The README previously cited `results/Validation_NPSS_HeldOut_2026-06-29.md`, which was never committed; this file replaces that reference.
