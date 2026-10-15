# PASV — Possibility-Adjusted Shot Value

**Every Shot Is a Measurement: Possibility-Adjusted Shot Value for NBA Decision Quality**

Open-source code, data, pre-registration history, and validation artifacts for the MIT Sloan Sports Analytics Conference 2027 Basketball-track submission.

**Author:** Robert “Bobby” Morong ([DataDunkNBA](https://datadunknba.substack.com))  
**Contact:** bobby@trainingties.com  
**Current SSAC27 abstract:** [`paper/SSAC27_PASV_Abstract_v4_2026-08-26.md`](paper/SSAC27_PASV_Abstract_v4_2026-08-26.md)  
**Historical full manuscript:** [`paper/SSAC27_PASV_PAPER_FULL_v1.md`](paper/SSAC27_PASV_PAPER_FULL_v1.md)  
**License:** MIT

> **Current evidence state (Sept. 2026):** PASV remains an interpretable counterfactual shot-decision framework. In the held-out per-shot study, the current public-event continuation term does **not** add predictive information beyond shot quality. The negative result is part of the contribution and defines the richer-state research frontier.

---

## Core idea

PASV grades a shot against the value of continuing the possession:

`PASV = xPTS(shot) - V*(s*)`

where `xPTS(shot)` is expected points from the shot taken and `V*(s*)` is the estimated value of declining that shot and preserving the possession's best available continuation.

The research question is not merely whether a shot was good. It is whether the shot was good **relative to the alternatives it ended**.

PASV is explicitly downstream of prior work on shot selection and possession value. See **Related work** below.

---

## Current empirical result

The v4 Sloan abstract uses the held-out per-shot Study 1 as the empirical spine:

- Calibration: **219,527 field-goal attempts** from the 2024-25 NBA regular season.
- Held-out test: **14,377 playoff attempts**.
- Within-player R² on the playoffs:
  - xPTS: **0.0231**
  - PASV: **0.0216**
  - public-event Skinner comparison: **0.0125**
- Adding PASV to xPTS + player fixed effects: **Delta R² ≈ 0.00007**, nested-test **p = 0.31**, cluster-robust **p = 0.24**, with worse AIC.
- PASV is approximately **0.97–0.98 correlated with xPTS within player** at current public-event resolution.

### Interpretation

PASV improves on the repository's coarse public-event implementation of the classical cutoff benchmark, but **does not beat xPTS**. The current `V*(s*)` varies too little shot-to-shot to create independent signal.

That means the next test is not “tune the same proxy harder.” It is to measure continuation value with richer possession state: defender positioning, help configuration, spacing, transition state, action history, and true shot-clock context.

---

## What the project claims

- A shot decision can be expressed as a signed counterfactual comparison between the chosen shot and preserved continuation value.
- PASV is an interpretable framework for that comparison.
- The current public-event continuation implementation is empirically near-collinear with xPTS.
- The held-out null is informative because it localizes what additional state is required for possibility cost to become independently measurable.
- The pre-registration and failure receipts are part of the research record rather than being hidden.

## What it does **not** claim

- PASV does **not** currently outperform xPTS/shot quality.
- The current clock/public-event continuation proxy does **not** establish independent predictive value.
- The two 2026 preregistered series misses are not retroactively reinterpreted as wins.
- The public Skinner comparison is not a claim of superiority over a fully observed shot-clock implementation.
- Holding Math is a conditional mechanism model, not an observed universal NBA law.
- The AST%-style OPC proxy is not a validated substitute for tracking-grade option preservation.

---

## Repository map

```text
.
├── README.md
├── LICENSE
├── requirements.txt
├── paper/
│   ├── SSAC27_PASV_Abstract_v4_2026-08-26.md      # current Sloan abstract framing
│   ├── SSAC27_PASV_Abstract_v3_2026-06-29.md      # historical submission version
│   ├── SSAC27_PASV_Section_5_v2_2026-06-29.md     # updated empirical section
│   ├── SSAC27_PASV_PAPER_FULL_v1.md               # historical full manuscript; not current empirical authority
│   └── SSAC27_PASV_Holding_Math_Theorem_v2_2026-06-13.md
├── code/                                           # PASV, baselines, sensitivity, DTI/continuation work
├── data/                                           # bundled public-data artifacts where redistribution is allowed
├── notebooks/                                      # reproduction notes/specifications
├── pre_registration/                               # immutable pre-tip predictions + grading receipts
├── results/                                        # held-out Study 1 and other receipts
└── npss/                                           # separate playoff-fragility subproject; see its own correction history
```

The historical full manuscript remains in the repository for auditability, but its June framing should not be treated as the current empirical authority where it conflicts with the later Section 5 / v4 abstract.

---

## Related work

PASV builds on, and must be read against, four prior lines of work:

- **Skinner, B. (2012).** The problem of shot selection in basketball. *PLOS ONE* 7(1): e30776. https://doi.org/10.1371/journal.pone.0030776. The optimal-stopping frame PASV uses.
- **Cervone, D., D'Amour, A., Bornn, L., & Goldsberry, K. (2016).** A multiresolution stochastic process model for predicting basketball possession outcomes. *Journal of the American Statistical Association* 111(514). arXiv:1408.0777. Expected possession value as a continuously updated quantity.
- **Sandholtz, N., & Bornn, L. (2020).** Markov decision processes with dynamic transition probabilities: an analysis of shooting strategies in basketball. *Annals of Applied Statistics* 14(3): 1122–1145. https://doi.org/10.1214/20-AOAS1348. Region-level expected points inside an MDP of shot policy; names defender-conditioned action values as future work.
- **Duma, N., & Benaharon, L. (2026).** Efficient frontier optimization of NBA shot selection using Markov reward processes. arXiv:2607.02933. A static shot-diet frontier finding the league near-efficient, with gains from more rim attempts; names missing personnel identification as a limitation.

The shot-value ladder in this repository (dunk 1.81, rim 1.26, corner three 1.17, above-the-break three 1.07, mid-range and paint non-rim 0.86) reproduces public values and is pipeline validation, not a contribution. The direction "more rim, less mid-range" is Duma & Benaharon's published result. PASV's open question is the state-contingent one: whether conditioning on defender identity changes the value of continuing a possession.

## Pre-registration record

The May 26, 2026 filing committed PASV v0.1 to playoff-series predictions before the outcomes resolved. The subsequent grading recorded **two consecutive misses**. Those misses remain immutable research history.

The project treats this as methodology, not embarrassment: claims are graded against the version that existed before the result was known.

The pre-registration files are frozen under git tag [`prereg-pasv-v0.1`](https://github.com/GrobeStreet/pasv/tree/prereg-pasv-v0.1), which points at commit `7019298`, the first commit containing them (2026-06-08). The filing itself is dated 2026-05-26 and the grading receipts 2026-06-03; the tag proves the files have not changed since 2026-06-08, not the earlier filing date.

---

## Related NPSS correction

The repository also contains the NPSS / Schemable Big subproject. Its original held-out implementation treated every non-zero continuous `hunt` value as truthy and therefore inflated the earlier **100% recall** claim. That claim is retired. With the corrected `hunt >= 0.30` rule, held-out recall is **66.7% (4 of 6)** and the held-out schemable-big decline is **−0.190 AQI**; the full table and raw output are in [`npss/results/`](npss/results/Validation_NPSS_HeldOut_2026-10-15.md).

---

## Reproducibility note

The repository contains both early team-aggregate PASV work and the later per-shot validation work. When reproducing the Sloan v4 result, use the files referenced by the v4 abstract / Study 1 receipt rather than assuming the original `pasv_v01.py` team-aggregate quick start reproduces the held-out per-shot study.

A remaining hardening task is to make the full per-shot Study 1 input pipeline self-contained or regenerable from frozen source manifests, with all Python/parquet dependencies pinned. The regeneration path is documented in [`DATA.md`](DATA.md); the possession parquets themselves are not bundled.

---

## Citation

Until conference acceptance, cite this as a submitted/open-source research project rather than as accepted proceedings:

```bibtex
@misc{morong2026pasv,
  title={Every Shot Is a Measurement: Possibility-Adjusted Shot Value for NBA Decision Quality},
  author={Morong, Robert},
  year={2026},
  note={Submitted to the MIT Sloan Sports Analytics Conference 2027; open-source research repository},
  url={https://github.com/GrobeStreet/pasv}
}
```

---

## License

MIT. See `LICENSE`.

---

## Acknowledgements

PASV builds on Brian Skinner's *The Problem of Shot Selection in Basketball* (2012) and Cervone, D'Amour, Bornn, and Goldsberry's work on Expected Possession Value (2014). The framework extends those ideas by making the foreclosed continuation explicit in the shot-decision score.

*Independent DataDunkNBA research. The evidence record includes positive findings, nulls, implementation corrections, and failed predictions.*
