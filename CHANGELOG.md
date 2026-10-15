# Changelog

All notable changes to the PASV research repository. Dates are the work dates, not git-commit dates.

## The r ≈ 0.61 vs r ≈ 0.81 question (read this first)

Two correlation figures for the PASV v0.1 team-aggregate proxy against the WEV v3 composite appear across the project's history. They are **the same method on two different input snapshots**, not two different methods:

- **r ≈ 0.61** — reported in the original 2026-05-26 pre-registration, computed on the source-data pipeline (an earlier season-aggregate snapshot with different intermediate rounding/inclusion).
- **r ≈ 0.81** — the figure produced by the **bundled, reproducible dataset** in this repo (`data/pasv_v01_2025_team_aggregate.csv`) run through `code/pasv_v01.py`. Independently recomputed: **r = 0.8100**. Moderate ±0.05 weight perturbation gives r ∈ [0.73, 0.86]; aggressive ±0.15 gives r ∈ [0.45, 0.91].

**The bundled, reproducible number is 0.81.** That is what `notebooks/validation.md` now prints and what the README and paper Section 5.3 report. The pre-registration's 0.61 is preserved verbatim in `pre_registration/` as the historical, timestamped record — we do not alter filed pre-registrations. Any "expected ≈0.61" language in the validation notebook has been corrected to reflect the bundled dataset (this was a documentation-drift bug, fixed 2026-06-29).

Separately: a v0.2 attempt to add a DTI component to the team aggregate was a **documented negative result** — a TS%-deviation fallback appeared to lift r to ≈0.85, but the real DTI leaderboard produced r ≈ 0.62 (below v0.1's 0.81). The DTI team-aggregate extension is rejected; DTI retains value at the possession level only. See paper Section 5.3.3.

---

## 2026-10-15
### Fixed
- **NPSS README:** replaced the retired 100% held-out recall with the corrected figures from `npss/code/_npss_heldout.py` (held-out recall 66.7%, 4 of 6; precision 36.4%; specificity 53.3%). Added the held-out comparison-big change (−0.108), which narrows the schemable-vs-comparison contrast out of sample.
- **NPSS results:** committed `npss/results/Validation_NPSS_HeldOut_2026-10-15.md` and the raw script output. The README previously cited a results file that was never committed.
- **NPSS AQI naming:** documented that this subproject's AQI is a BPM-based proxy (BPM × usage × TS%/0.550; star tier 2.0, collapse below 1.75), distinct from DataDunkNBA's net-rating AQI with its 1.73 floor.

### Added
- **Related work** in the root README: Skinner (2012), Cervone et al. (2016), Sandholtz & Bornn (2020), Duma & Benaharon (2026).
- `DATA.md`: how to regenerate the Study 1 possession parquets.
- Git tag `prereg-pasv-v0.1` on the first commit containing the pre-registration files.

### Repository hygiene
- `.gitignore` contained unresolved merge-conflict markers and ignored every `results/` directory, which is why the NPSS results file was never committed. Results are receipts and are now tracked; regenerated parquet inputs are ignored instead. Removed committed `__pycache__` files.

### Still open
- The Study 1 possession parquets (219,527 calibration shots; 14,377 held-out shots) are not bundled.
- Pre-registered tests T1–T5 have not been run.

## [unreleased] — 2026-06-29
### Added
- **Per-shot PASV engine** (`code/pasv_per_shot.py`) and **Study 1** (`code/run_study1.py`, `code/study1_within_player.py`, `code/study1_within_player_confirm.py`) — the first per-shot, out-of-sample validation of PASV on public event data. Calibrated on 2024-25 regular season (219,527 attempts), tested on held-out 2024-25 playoffs (14,377 attempts).
- **Study 1 result:** PASV beats the Skinner (2012) MDP-cutoff baseline within-player (R² 0.0216 vs 0.0125) but is statistically equivalent to a calibrated shot-quality model (ΔR² −0.0014; nested F-test p=0.31). Robust across five estimators. Honest reading: PASV is a valid per-shot decision scalar that beats the classical baseline; separating its possibility-cost term from shot quality requires tracking-resolution data (the frontier).
- **Abstract v3** (`paper/SSAC27_PASV_Abstract_v3_2026-06-29.md`) — reframed around Study 1; 500 words; interpretability-as-feature framing.
- **Section 5 v2** (`paper/SSAC27_PASV_Section_5_v2_2026-06-29.md`) — per-shot study as headline; team-aggregate demoted to robustness; DTI negative recorded; OPC + pre-registration grading carried forward.
- This `CHANGELOG.md` and `CITATION.cff`.

### Fixed
- **Documentation drift:** `notebooks/validation.md` previously expected r ≈ 0.61 and a [0.55, 0.64] sensitivity range; corrected to the bundled-data figures (r ≈ 0.81; ±0.05 → [0.73, 0.86]).

### Known / deferred (hardening roadmap — for the December full-paper stage, not required for the October abstract)
- Add `tests/` (component math, 30-row output, 0–10 normalization bounds, no-NaN, bundled-correlation-within-tolerance).
- Add CI (GitHub Actions: install, test, run `pasv_v01.py` and `sensitivity.py`).
- Add the actual `notebooks/validation.ipynb` or rename the spec to `validation_spec.md`.
- Pin the environment (`requirements-lock.txt` or `environment.yml`) + record the Python version used.
- Consider renaming `code/` → `src/pasv/` to avoid shadowing Python's stdlib `code` module on import.

## [pre-registration] — 2026-05-26
### Added
- PASV v0.1 team-aggregate proxy, OPC AST% proxy, weights locked (30/25/25/−20).
- Public timestamped pre-registration of 2026 Conference Finals series predictions (`pre_registration/`). Graded verbatim post-resolution — documented misses included.
- Full paper v1, abstract v1/v2, README, LICENSE.
