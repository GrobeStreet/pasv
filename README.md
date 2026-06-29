# PASV — Possibility-Adjusted Shot Value

**Every Shot Is a Measurement: A Theory of Possibility Cost in NBA Possession Value**

Companion code, data, and pre-registration artifacts for the MIT Sloan Sports Analytics Conference 2027 research paper submission.

**Author:** Bobby Morong ([DataDunkNBA](https://datadunknba.substack.com))
**Contact:** bobby@datadunknba.com
**Paper:** [`paper/SSAC27_PASV_PAPER_FULL_v1.md`](paper/SSAC27_PASV_PAPER_FULL_v1.md)
**License:** MIT

---

## What this is

PASV (Possibility-Adjusted Shot Value) is a per-shot signed scalar that grades each NBA shot decision against the value of the alternatives the shot foreclosed. It unifies Skinner's (2012) MDP-cutoff framework and Cervone et al.'s (2014) Expected Possession Value framework into a single, operationally useful per-shot decision-grading metric.

The framework contributes three formal constructs:

1. **PASV** — per-shot signed scalar: `PASV = xPTS(shot) − Σ P(foreclosed_i) × EV(foreclosed_i)`
2. **The Holding-Math Theorem** — closed-form expression: `P(≥1 mistake) = 1 − 0.95^(5n)`, reaching 72.3% cumulative defender-mistake probability at five forcing actions
3. **OPC (Option Preservation Coefficient)** — player-level metric for how long a possession's decision tree remains alive before optimal extraction

Empirically validated on 2025 NBA regular-season data. Pre-registered against the 2026 NBA Conference Finals.

---

## Repository structure

```
.
├── README.md                                    # This file
├── LICENSE                                      # MIT
├── requirements.txt                             # Python dependencies
├── paper/
│   ├── SSAC27_PASV_PAPER_FULL_v1.md             # The complete paper
│   └── SSAC27_PASV_Abstract_v1.md               # The 490-word abstract
├── code/
│   ├── pasv_v01.py                              # PASV v0.1 team-aggregate computation
│   ├── opc_proxy.py                             # OPC AST% proxy computation
│   └── sensitivity.py                           # Weight-sensitivity analysis
├── data/
│   └── pasv_v01_2025_team_aggregate.csv         # 30-team computed inputs + scores
├── notebooks/
│   └── validation.md                            # Reproducing Section 5 results
├── pre_registration/
│   ├── PASV_v01_PreRegistration_2026-05-26.md   # Pre-tip filing (verbatim)
│   └── PASV_v01_Receipts_2026-06-03.md          # Honest grading (verbatim)
└── results/
    └── (populated by running code/pasv_v01.py)
```

---

## Reproducing the empirical results

### Quick start

```bash
git clone https://github.com/GrobeStreet/pasv.git
cd pasv
pip install -r requirements.txt
python code/pasv_v01.py --season 2025 --output results/pasv_v01_2025.csv
python code/sensitivity.py --input data/pasv_v01_2025_team_aggregate.csv --wev-column WEV_v3 --output results/sensitivity_2025.csv
```

The full validation pipeline runs in under 30 seconds on a standard laptop.

### Data provenance

All input data is sourced from [basketball-reference.com](https://www.basketball-reference.com/) per-game and advanced team-aggregate tables, 2025 NBA regular season. The CSV included in `data/` preserves the figures used in the PASV v0.1 pre-registration filing (methodology-hash discipline).

The 30-team CSV includes:
- Team abbreviation
- TS% (Shot Diet Quality, SDQ)
- AST/FGM (Team-level Option Preservation, OPC_team)
- FTA/FGA (Forcing Function Score, FFS)
- TOV/FGA (Turnover Penalty)
- WEV_v3 reference composite for sensitivity testing

---

## The pre-registration discipline

This framework operates on a public-pre-registration commitment. The May 26, 2026 filing (`pre_registration/PASV_v01_PreRegistration_2026-05-26.md`) specified PASV v0.1 series predictions for the 2026 NBA Conference Finals before the WCF resolved and before NBA Finals tipped off.

The grading (`pre_registration/PASV_v01_Receipts_2026-06-03.md`) was filed honestly after series resolution. **The framework recorded two consecutive misses against pre-registered series predictions (ECF and WCF).** The grading document publishes those misses, identifies the v0.2 development priorities derived from the forensic analysis of why the framework missed, and commits to filing the v0.2 specification publicly before any 2026-27 season predictions.

The misses are documented here, not hidden. Section 5.5 of the paper folds the grading verbatim into the empirical validation as a methodological commitment.

---

## What this paper claims (and does not claim)

**Claims:**
- PASV is a novel, basketball-native, per-shot signed scalar that does not currently exist in the literature
- The Holding-Math Theorem is a closed-form derivation grounded in elementary probability
- OPC is a meaningful player-level construct, with Jokić's 50.3% AST% in 2022-23 establishing the modern center-position ceiling
- The PASV v0.1 team-aggregate proxy correlates with the WEV v3 composite at r ≈ 0.81 across 30 NBA teams in 2025 (bundled data; original pre-registration computed r ≈ 0.61 on the source pipeline)
- The pre-registration discipline is a methodological commitment

**Does not claim:**
- That PASV v0.1 has been validated as an NBA playoff series predictor (the 2026 pre-registration sample shows two consecutive misses; the framework's claim is documented honestly)
- That the framework replaces existing frameworks (it explicitly builds on Skinner 2012 and Cervone 2014)
- That the AST% proxy substitutes for full possession-tracking-data operationalization (the proxy is a conservative lower-bound estimator)

---

## Citation

```bibtex
@inproceedings{morong2027pasv,
  title={Every Shot Is a Measurement: A Theory of Possibility Cost in NBA Possession Value},
  author={Morong, Bobby},
  booktitle={Proceedings of the MIT Sloan Sports Analytics Conference 2027},
  year={2027},
  note={Submission package: https://github.com/GrobeStreet/pasv}
}
```

---

## License

MIT. See `LICENSE`.

---

## Acknowledgements

This work builds explicitly on Brian Skinner's *The Problem of Shot Selection in Basketball* (PLOS ONE, 2012) and Cervone, D'Amour, Bornn, and Goldsberry's *A Multiresolution Stochastic Process Model for Predicting Basketball Possession Outcomes* (Journal of Quantitative Analysis in Sports, 2014). Both papers established foundational frameworks that PASV extends rather than competes with. The intellectual debt is significant and acknowledged in Section 3 of the paper.

The framework's cross-disciplinary scaffolding draws from Bastiat's opportunity-cost economics, von Neumann and Nash's game theory, Bellman's dynamic programming, Markowitz's portfolio theory, Feynman's path-integral formulation of quantum mechanics, and DeepMind's AlphaGo Monte Carlo Tree Search algorithm.

---

*Built by a single independent researcher using public data sources, open-source statistical tooling, and AI-assisted synthesis. The work is its own evidence.*

— Bobby Morong, DataDunkNBA · 2026-06-03
