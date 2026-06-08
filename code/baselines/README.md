# Baselines

External baseline implementations used by Section 5 of the PASV paper
for head-to-head empirical comparison. These are *not* PASV. They are
the established frameworks PASV is benchmarked against.

## Skinner 2012 (`skinner_baseline.py`)

Closed-form reimplementation of Brian Skinner's optimal shot-selection
cutoff from:

> Skinner, B. (2012). "The Problem of Shot Selection in Basketball."
> *PLOS ONE* 7(1): e30776.

The module exposes:

- `cutoff_uniform(f_max, clock)` — the closed-form recursion under the
  uniform shot-quality distribution Skinner uses as his pedagogical
  example.
- `cutoff_from_samples(samples, clock)` — the empirical variant that
  consumes a real xPTS distribution sampled from NBA play-by-play.
  This is the version used in **Study 1** of `PASV_Empirical_Validation_Plan_2026-06-05.md`.
- `grade_shot(xpts, t, cutoffs)` — per-shot grader returning a `ShotGrade`
  dataclass.
- `grade_shots(xpts, times, cutoffs)` — vectorized grader returning the
  signed per-shot margins. PASV's own per-shot scalar is compared
  against these margins in the Study 1 R² test.

### Quick sanity check (CLI)

```bash
cd code/baselines
python skinner_baseline.py --f_max 3.0 --clock 24 --plot
```

This prints the cutoff schedule and (if matplotlib is available)
writes a plot of the curve to `results/skinner_cutoff.png`.

### Tests

```bash
cd code/baselines
python test_skinner_baseline.py
```

Verifies:
- The cutoff schedule is monotone in t.
- The cutoff converges to `f_max` as the clock grows (Skinner Eq. 4).
- The empirical variant matches the closed-form within sampling noise
  when fed uniform samples.
- The shot grader API behaves correctly at edge cases.

### How this connects to Study 1

The PASV empirical validation plan calls for a head-to-head comparison
of PASV's per-shot signed scalar against Skinner's threshold-only
framing. The methodology, briefly:

1. Train an xPTS model on 2023-24 play-by-play.
2. Use the calibrated xPTS samples to construct the **empirical**
   Skinner cutoff schedule via `cutoff_from_samples(...)`.
3. On the held-out 2024-25 sample, compute for each shot:
   - The signed Skinner margin via `grade_shots(...)`.
   - The PASV per-shot signed scalar via the existing PASV code.
4. Aggregate to player-season. Compute R² of each against the
   player's team's per-possession scoring rate when on floor.
5. Report the R² delta. If PASV's R² is meaningfully higher than
   Skinner's, the signed-magnitude information PASV exposes is
   carrying real predictive value.

The expected R² lift is modest (+0.04 to +0.10 percentage points).
This is sufficient to claim PASV adds information; the framing is
"PASV captures decision-level magnitude information that Skinner's
threshold-only framing loses."

---

*— Bobby Morong / DataDunkNBA / 2026-06-05*
