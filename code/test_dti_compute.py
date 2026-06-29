"""
test_dti_compute.py — Unit tests for the DTI v0.1 computation engine.

Run with:
    python -m unittest test_dti_compute -v
or
    python test_dti_compute.py
"""

from __future__ import annotations

import unittest

import numpy as np
import pandas as pd

from dti_compute import (
    KNOWN_TARGETS_2026,
    compute_all_layers,
    compute_dti_def,
    compute_dti_hunt,
    compute_dti_poss,
    validate_against_known_targets,
)


# ---------------------------------------------------------------------------
# Synthetic fixtures
# ---------------------------------------------------------------------------

def _baseline() -> pd.DataFrame:
    """Action-type league baseline PPP — three actions + 'Other' fallback."""
    return pd.DataFrame({
        "action_type": ["PnR_BH", "Iso", "Post", "Other"],
        "league_PPP":   [1.00,     0.90,  1.05,   0.95],
    })


def _make_poss(n_per_def: int = 250, seed: int = 7) -> pd.DataFrame:
    """
    Build a synthetic possession-level table with three defenders:
      - 'Surrender Sam'  -> consistently gives up 1.20 PPP on PnR_BH
                            (DTI_def +0.20 over 1.00 baseline)
      - 'Suppress Sue'   -> consistently gives up 0.50 PPP on Iso
                            (DTI_def -0.40 over 0.90 baseline)
      - 'Average Al'     -> roughly at baseline 1.05 on Post

    And three hunters:
      - 'Hunter Hank'    -> attacks Sam on PnR, scores 1.30 PPP
      - 'Hunter Hal'     -> attacks Sue on Iso, scores 0.50 (cold)
      - 'Hunter Hugo'    -> attacks Al on Post, scores 1.05
    """
    rng = np.random.default_rng(seed)
    rows = []
    triples = [
        # defender,             action,    hunter,        mean_pts
        ((1, "Surrender Sam"),  "PnR_BH", (101, "Hunter Hank"), 1.20),
        ((2, "Suppress Sue"),   "Iso",    (102, "Hunter Hal"),  0.50),
        ((3, "Average Al"),     "Post",   (103, "Hunter Hugo"), 1.05),
    ]
    poss_id = 0
    for (def_id, def_name), action, (hunter_id, hunter_name), mean in triples:
        for _ in range(n_per_def):
            poss_id += 1
            # Discretize to NBA-realistic 0/2/3 points draws around the mean.
            base = float(rng.normal(loc=mean, scale=0.05))
            rows.append({
                "poss_id": f"poss_{poss_id}",
                "game_id": "g1",
                "season": "2025-26",
                "season_type": "Playoffs",
                "period": 1,
                "seconds_remaining": 600.0,
                "offense_team_id": 10,
                "defense_team_id": 20,
                "hunter_id": hunter_id,
                "hunter_name": hunter_name,
                "defender_id": def_id,
                "defender_name": def_name,
                "action_type": action,
                "points_scored": base,
                "is_targeted": True,
                "possessions_used": 1.0,
            })
    df = pd.DataFrame(rows)
    return df


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestDTIPoss(unittest.TestCase):

    def test_per_possession_math(self):
        """DTI_poss = points - baseline_PPP for each row."""
        poss = pd.DataFrame({
            "poss_id": ["a", "b", "c", "d"],
            "hunter_id": [1, 1, 2, 2],
            "defender_id": [9, 9, 9, 9],
            "hunter_name": ["H"] * 4,
            "defender_name": ["D"] * 4,
            "action_type": ["PnR_BH", "Iso", "Post", "Unknown_Action"],
            "points_scored": [2.0, 0.0, 3.0, 1.0],
        })
        out = compute_dti_poss(poss, _baseline())

        # baselines: PnR_BH 1.00, Iso 0.90, Post 1.05, Other (fallback) 0.95
        expected = np.array([2.0 - 1.00, 0.0 - 0.90, 3.0 - 1.05, 1.0 - 0.95])
        np.testing.assert_allclose(out["DTI_poss"].to_numpy(), expected)

        # Unknown action types should be bucketed as 'Other'.
        self.assertEqual(out.iloc[3]["action_type"], "Other")
        self.assertAlmostEqual(out.iloc[3]["baseline_PPP"], 0.95)

    def test_missing_columns_raises(self):
        bad = pd.DataFrame({"poss_id": ["a"]})
        with self.assertRaises(KeyError):
            compute_dti_poss(bad, _baseline())


class TestDTIDef(unittest.TestCase):

    def test_defender_aggregation_signs(self):
        """Sam should be POSITIVE, Sue should be NEGATIVE, Al ~0."""
        poss = _make_poss(n_per_def=300, seed=11)
        poss_dti = compute_dti_poss(poss, _baseline())
        def_lb = compute_dti_def(poss_dti, min_targeted_possessions=200)

        self.assertEqual(len(def_lb), 3)
        # Sam is rank 1 (most-hunted).
        self.assertEqual(def_lb.iloc[0]["defender_name"], "Surrender Sam")
        self.assertGreater(def_lb.iloc[0]["DTI_def"], 0.15)
        # Sue is rank 3 (last — most suppressing).
        self.assertEqual(def_lb.iloc[-1]["defender_name"], "Suppress Sue")
        self.assertLess(def_lb.iloc[-1]["DTI_def"], -0.30)
        # Al is in the middle, near zero.
        al = def_lb[def_lb["defender_name"] == "Average Al"].iloc[0]
        self.assertLess(abs(al["DTI_def"]), 0.05)

    def test_per100_is_per100(self):
        poss = _make_poss(n_per_def=250, seed=3)
        poss_dti = compute_dti_poss(poss, _baseline())
        def_lb = compute_dti_def(poss_dti, min_targeted_possessions=100)
        np.testing.assert_allclose(
            def_lb["DTI_def_per100"].to_numpy(),
            def_lb["DTI_def"].to_numpy() * 100.0,
        )


class TestDTIHunt(unittest.TestCase):

    def test_hunter_aggregation(self):
        """Hank hunts Sam well — Hank should be #1 hunter."""
        poss = _make_poss(n_per_def=300, seed=21)
        poss_dti = compute_dti_poss(poss, _baseline())
        hunt_lb = compute_dti_hunt(poss_dti, min_hunting_possessions=200)

        self.assertEqual(len(hunt_lb), 3)
        # Hank is rank 1 — attacking Sam, +0.20 expected per poss.
        self.assertEqual(hunt_lb.iloc[0]["hunter_name"], "Hunter Hank")
        self.assertGreater(hunt_lb.iloc[0]["DTI_hunt"], 0.15)
        # Hal is rank 3 — attacking Sue (cold) at -0.40 below baseline.
        self.assertEqual(hunt_lb.iloc[-1]["hunter_name"], "Hunter Hal")
        self.assertLess(hunt_lb.iloc[-1]["DTI_hunt"], -0.30)

    def test_hunting_flag_fallback(self):
        """When is_targeted is missing, the heuristic still works."""
        poss = _make_poss(n_per_def=300, seed=33)
        poss = poss.drop(columns=["is_targeted"])
        poss_dti = compute_dti_poss(poss, _baseline())
        hunt_lb = compute_dti_hunt(poss_dti, min_hunting_possessions=100)
        # Should still produce a sorted leaderboard, sourced from fallback.
        self.assertGreaterEqual(len(hunt_lb), 1)
        self.assertEqual(
            hunt_lb.attrs.get("hunting_flag_source"),
            "fallback:top-third-surrenderers",
        )


class TestSampleSizeFilter(unittest.TestCase):

    def test_min_possessions_cutoff(self):
        """Defenders below the min cutoff drop off the leaderboard."""
        poss = _make_poss(n_per_def=100, seed=5)
        poss_dti = compute_dti_poss(poss, _baseline())

        # With 100 possessions each, raising the threshold to 200 should
        # zero out the leaderboard.
        empty = compute_dti_def(poss_dti, min_targeted_possessions=200)
        self.assertEqual(len(empty), 0)

        # Lower threshold returns all three.
        full = compute_dti_def(poss_dti, min_targeted_possessions=50)
        self.assertEqual(len(full), 3)


class TestNormalizationEdgeCases(unittest.TestCase):

    def test_unknown_action_bucketed_other(self):
        """Action types not in vocab get the 'Other' baseline."""
        poss = pd.DataFrame({
            "poss_id": ["a", "b"],
            "hunter_id": [1, 1],
            "hunter_name": ["H", "H"],
            "defender_id": [9, 9],
            "defender_name": ["D", "D"],
            "action_type": ["fancy_new_action", None],
            "points_scored": [2.0, 0.0],
        })
        out = compute_dti_poss(poss, _baseline())
        self.assertEqual(set(out["action_type"]), {"Other"})
        # 2.0 - 0.95 and 0.0 - 0.95
        np.testing.assert_allclose(
            out["DTI_poss"].to_numpy(), np.array([1.05, -0.95])
        )

    def test_no_other_fallback_raises(self):
        """Missing baseline with no 'Other' row should raise."""
        baseline = pd.DataFrame({
            "action_type": ["PnR_BH"],
            "league_PPP": [1.00],
        })
        poss = pd.DataFrame({
            "poss_id": ["a"],
            "hunter_id": [1],
            "hunter_name": ["H"],
            "defender_id": [9],
            "defender_name": ["D"],
            "action_type": ["Iso"],  # not in baseline, no 'Other' fallback
            "points_scored": [2.0],
        })
        with self.assertRaises(ValueError):
            compute_dti_poss(poss, baseline)


class TestValidation(unittest.TestCase):

    def test_known_targets_found(self):
        """A leaderboard that includes a known target name flags it FOUND."""
        df = pd.DataFrame([
            {
                "rank": 1,
                "defender_id": 100,
                "defender_name": "Devin Booker",
                "team_id": 1610612756,
                "possessions_targeted": 500.0,
                "raw_PPP_against": 1.30,
                "expected_PPP_against": 1.00,
                "DTI_def": 0.30,
                "DTI_def_per100": 30.0,
            },
            {
                "rank": 2,
                "defender_id": 200,
                "defender_name": "Random Guy",
                "team_id": 9,
                "possessions_targeted": 300.0,
                "raw_PPP_against": 1.10,
                "expected_PPP_against": 1.00,
                "DTI_def": 0.10,
                "DTI_def_per100": 10.0,
            },
        ])
        val = validate_against_known_targets(df, top_n=30)
        booker = val[val["player_name"] == "Devin Booker"].iloc[0]
        self.assertTrue(bool(booker["in_top_n"]))
        self.assertEqual(int(booker["observed_rank"]), 1)
        # Players not on the leaderboard report n/a.
        wemby_row = val[val["player_name"] == "Nikola Jokic"].iloc[0]
        self.assertFalse(bool(wemby_row["in_top_n"]))


class TestEndToEnd(unittest.TestCase):

    def test_compute_all_layers_smoke(self):
        """compute_all_layers wires the three layers together end-to-end."""
        poss = _make_poss(n_per_def=300, seed=99)
        bundle = compute_all_layers(
            poss, _baseline(),
            min_targeted_possessions=200,
            min_hunting_possessions=200,
        )
        self.assertEqual(len(bundle.defender), 3)
        self.assertEqual(len(bundle.hunter), 3)
        self.assertIn("DTI_poss", bundle.poss.columns)


if __name__ == "__main__":
    unittest.main(verbosity=2)
