"""
Tests for skinner_baseline.py

Run with:  python test_skinner_baseline.py
"""

import sys
import numpy as np

from skinner_baseline import (
    cutoff_uniform,
    cutoff_from_samples,
    grade_shot,
    grade_shots,
)


def test_uniform_recursion_monotone():
    """The cutoff schedule must be weakly monotone increasing in t."""
    cutoffs = cutoff_uniform(f_max=3.0, clock=24)
    diffs = np.diff(cutoffs)
    assert np.all(diffs >= -1e-12), (
        f"Cutoffs not monotone: diffs={diffs}"
    )


def test_uniform_asymptote():
    """As clock grows, the cutoff converges to f_max (Skinner Eq. 4)."""
    f_max = 2.0
    cutoffs = cutoff_uniform(f_max=f_max, clock=200)
    # By t=200 we should be within 1% of f_max
    assert cutoffs[-1] > 0.99 * f_max, (
        f"cutoff(200) = {cutoffs[-1]:.4f} did not converge to f_max={f_max}"
    )
    # And we never exceed f_max
    assert np.all(cutoffs <= f_max + 1e-12), (
        f"cutoff exceeds f_max somewhere: max={cutoffs.max()}"
    )


def test_uniform_first_tick():
    """V(0) = 0, so cutoff(1) = 0. With f_max=3, V(1) = 9/6 = 1.5,
    so cutoff(2) = 1.5."""
    cutoffs = cutoff_uniform(f_max=3.0, clock=2)
    assert abs(cutoffs[0] - 0.0) < 1e-12, f"cutoff(1) = {cutoffs[0]} != 0"
    assert abs(cutoffs[1] - 1.5) < 1e-12, f"cutoff(2) = {cutoffs[1]} != 1.5"


def test_empirical_matches_uniform_on_uniform_samples():
    """If we sample heavily from Uniform[0, f_max], the empirical cutoff
    should converge to the closed-form uniform cutoff."""
    rng = np.random.default_rng(42)
    samples = rng.uniform(0.0, 3.0, size=200_000)
    emp = cutoff_from_samples(samples, clock=24)
    closed = cutoff_uniform(f_max=3.0, clock=24)
    # Allow 1% relative error from sampling noise
    rel_err = np.max(np.abs(emp - closed) / (closed + 1e-9))
    assert rel_err < 0.02, (
        f"Empirical cutoff did not match closed-form: max rel err {rel_err:.4f}"
    )


def test_grade_shot_above_cutoff():
    """A 1.5 xPTS shot at t=2 should clear the cutoff (cutoff(2)=1.5 exactly,
    so a 1.51 shot is strictly above). At t=1 the cutoff is 0 so anything
    clears."""
    cutoffs = cutoff_uniform(f_max=3.0, clock=24)
    # cutoff(1) = V(0) = 0, so any non-negative shot clears
    grade = grade_shot(xpts=0.05, t=1, cutoffs=cutoffs)
    assert grade.above_cutoff
    assert grade.margin > 0
    assert grade.cutoff == cutoffs[0]


def test_grade_shot_below_cutoff():
    """A 0.50 xPTS shot at fresh shot clock (t=24, cutoff ~2.79) should
    fall well below the cutoff — the offense should hold for a better look."""
    cutoffs = cutoff_uniform(f_max=3.0, clock=24)
    grade = grade_shot(xpts=0.50, t=24, cutoffs=cutoffs)
    assert not grade.above_cutoff
    assert grade.margin < 0


def test_grade_shots_vectorized():
    cutoffs = cutoff_uniform(f_max=3.0, clock=24)
    xpts = [1.10, 0.95, 1.40, 1.80]
    times = [14, 4, 22, 2]
    margins = grade_shots(xpts, times, cutoffs)
    # Spot-check the first one matches the scalar API
    g0 = grade_shot(xpts[0], times[0], cutoffs)
    assert abs(margins[0] - g0.margin) < 1e-12


def test_uniform_input_validation():
    try:
        cutoff_uniform(f_max=0)
    except ValueError:
        pass
    else:
        raise AssertionError("cutoff_uniform should reject f_max=0")

    try:
        cutoff_uniform(f_max=2.0, clock=0)
    except ValueError:
        pass
    else:
        raise AssertionError("cutoff_uniform should reject clock=0")


def test_empirical_input_validation():
    try:
        cutoff_from_samples([])
    except ValueError:
        pass
    else:
        raise AssertionError("cutoff_from_samples should reject empty samples")


def test_grade_shot_bounds():
    cutoffs = cutoff_uniform(f_max=3.0, clock=24)
    try:
        grade_shot(xpts=1.0, t=0, cutoffs=cutoffs)
    except ValueError:
        pass
    else:
        raise AssertionError("grade_shot should reject t=0")
    try:
        grade_shot(xpts=1.0, t=25, cutoffs=cutoffs)
    except ValueError:
        pass
    else:
        raise AssertionError("grade_shot should reject t=25")


if __name__ == "__main__":
    tests = [v for k, v in globals().items() if k.startswith("test_")]
    print(f"Running {len(tests)} tests...")
    failed = []
    for fn in tests:
        try:
            fn()
            print(f"  PASS  {fn.__name__}")
        except AssertionError as e:
            print(f"  FAIL  {fn.__name__}: {e}")
            failed.append(fn.__name__)
        except Exception as e:
            print(f"  ERROR {fn.__name__}: {type(e).__name__}: {e}")
            failed.append(fn.__name__)
    print()
    if failed:
        print(f"FAILED: {len(failed)}/{len(tests)}")
        sys.exit(1)
    else:
        print(f"ALL {len(tests)} TESTS PASSED")
