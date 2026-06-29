"""
PASV per-shot engine + Study 1 (PASV vs Skinner 2012)
=====================================================

Implements the per-shot Possibility-Adjusted Shot Value defined in the SSAC27
paper Math Appendix Section 4.1:

    PASV(shot) = xPTS(shot) - V*(s*)

where
    xPTS(shot)  = expected points of the shot taken, from a calibrated
                  shot-quality model (distance x shot-type cells)
    V*(s*)      = continuation value of the possession had the shot NOT been
                  taken = the publicly-reproducible EPV-substitute: the expected
                  points the offense would realize by continuing from game-state
                  s* (binned by game clock / period context).

Study 1 compares PASV against the Skinner (2012) MDP cutoff baseline
(code/baselines/skinner_2012.py), which produces the signed gap xPTS - f*(tau).

Design / honesty notes
----------------------
* Possession-level data exists for 2024-25 RS (284,382 poss) and the five
  playoff seasons. There is NO 2023-24 RS possession parquet, so the train/test
  split is:  CALIBRATE on 2024-25 Regular Season  ->  TEST out-of-sample on
  2024-25 Playoffs (a genuinely held-out, different-context sample the xPTS and
  V* models never saw). This is a legitimate OOS design; it is labeled as such.
* `clock` in the parquet is the GAME clock (PT%dM%fS), not the shot clock. We
  use it to derive a possession-context bin and a shot-clock PROXY (see
  derive_tau). Skinner's f*(tau) is therefore evaluated on a proxy tau; this is
  stated as a limitation, not hidden.
* Ground truth for the R^2 comparison is each primary offensive player's
  on-ball realized points-per-shot-attempt (PPP_player), computed from the
  held-out playoff sample. Both PASV and Skinner are aggregated to the same
  player level and regressed against the SAME ground truth, so the comparison
  is apples-to-apples.

Author: Bobby Morong / DataDunkNBA — sole author
License: MIT
Version: v0.1 — 2026-06-25
"""

import glob
import os
import re

import numpy as np
import pandas as pd

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "baselines"))
from skinner_2012 import compute_cutoff_schedule  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
DTI = os.path.join(ROOT, "dti_data")

# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------
def load_poss(path: str) -> pd.DataFrame:
    df = pd.read_parquet(path)
    # keep only true field-goal attempts (PASV grades shot decisions)
    fg = df[df["is_field_goal"]].copy()
    return fg


def parse_game_clock_seconds(clock: str) -> float:
    """PT11M43.00S -> seconds remaining in the period (0..720)."""
    if not isinstance(clock, str):
        return np.nan
    m = re.match(r"PT(?:(\d+)M)?([\d.]+)S", clock)
    if not m:
        return np.nan
    minutes = int(m.group(1)) if m.group(1) else 0
    seconds = float(m.group(2))
    return minutes * 60 + seconds


def derive_tau(seconds_left_period: float) -> int:
    """
    Shot-clock PROXY. We do not have a true shot clock. Skinner's cutoff only
    needs an ordinal 'how much clock pressure' signal. We map late-period /
    late-game pressure to low tau and open-period play to a neutral mid tau.
    Most half-court possessions resolve in the 12-18s shot-clock band, so the
    proxy centers there and compresses toward 1-4 only under end-of-period
    pressure (< 8s left in the period).
    """
    if np.isnan(seconds_left_period):
        return 14
    if seconds_left_period <= 3:
        return 2
    if seconds_left_period <= 8:
        return 5
    if seconds_left_period <= 24:
        return 10
    return 14


# ---------------------------------------------------------------------------
# xPTS shot-quality model (calibrated on training season)
# ---------------------------------------------------------------------------
def shot_cell(row) -> str:
    """Distance x type cell used as the xPTS lookup key."""
    is3 = str(row["shot_outcome"]).endswith("3") or row["shot_distance"] >= 22
    d = row["shot_distance"]
    if is3:
        if d >= 27:
            return "3_deep"
        return "3_reg"
    if d <= 3:
        return "2_rim"
    if d <= 10:
        return "2_short"
    if d <= 16:
        return "2_mid"
    return "2_long"


def fit_xpts(train: pd.DataFrame) -> dict:
    """
    xPTS per cell = mean realized points on FG attempts in that cell
    (made_2 -> 2, made_3 -> 3, miss -> 0). This is the expected points of
    *taking* the shot from that cell. Calibrated on training season only.
    """
    t = train.copy()
    t["cell"] = t.apply(shot_cell, axis=1)
    # realized points on the FG attempt itself (exclude and-1 FT, which live in
    # separate Free Throw rows): made_2=2, made_3=3, else 0
    pts = t["shot_outcome"].map({"made_2": 2, "made_3": 3}).fillna(0.0)
    t["fg_pts"] = pts.values
    table = t.groupby("cell")["fg_pts"].mean().to_dict()
    return table


def apply_xpts(df: pd.DataFrame, table: dict, fallback: float) -> pd.Series:
    cells = df.apply(shot_cell, axis=1)
    return cells.map(table).fillna(fallback)


# ---------------------------------------------------------------------------
# V*(s*) continuation value — the EPV-substitute
# ---------------------------------------------------------------------------
def fit_continuation(train: pd.DataFrame) -> dict:
    """
    V*(s*) = the continuation value of DECLINING this shot and continuing the
    possession. Theory-faithful construction (Math Appendix 4.1): V* must depend
    on possession context that Skinner's clock-only f*(tau) CANNOT see, otherwise
    PASV is just an affine restatement of Skinner (audit 2026-06-25 found
    corr(PASV,Skinner)=0.997 when V* was keyed on the same tau axis).

    We condition V* on the OFFENSE'S on-floor teammate scoring environment:
    the value of "pass instead of shoot" is high next to efficient teammates and
    low otherwise. Concretely, for each offensive lineup we estimate the team's
    expected points-per-FG-attempt from the OTHER four players on the floor
    (the alternative shooters the ball could go to). This is a publicly-
    reproducible coarse-EPV analog: no spatial tracking, only who is on the floor
    and how efficient they are.

    Returns dict keyed by primary_offensive_player_id -> teammate-environment V*.
    Players not in the table fall back to the league mean.
    """
    t = train.copy()
    t["fg_pts"] = t["shot_outcome"].map({"made_2": 2, "made_3": 3}).fillna(0.0)
    # each player's own realized points-per-FGA (their value as a shooter)
    own = t.groupby("primary_offensive_player_id")["fg_pts"].agg(["mean", "size"])
    league_mean = t["fg_pts"].mean()
    # teammate environment: for each shot, the mean own-value of the OTHER four
    # offensive players on the floor (the continuation/pass alternatives).
    own_map = own["mean"].to_dict()

    def lineup_alt_value(row):
        ids = row["off_lineup_ids"]
        shooter = row["primary_offensive_player_id"]
        if ids is None or len(ids) == 0:
            return np.nan
        vals = [own_map.get(int(p), league_mean) for p in ids if int(p) != shooter]
        return float(np.mean(vals)) if vals else np.nan

    t["alt_val"] = t.apply(lineup_alt_value, axis=1)
    # V*(player) = mean over that player's shots of the teammate alternative value
    tab = t.groupby("primary_offensive_player_id")["alt_val"].mean().to_dict()
    tab["_league_mean_"] = float(league_mean)
    return tab


def fit_continuation_playervalue(train: pd.DataFrame) -> dict:
    """
    Calibrate each player's own realized points-per-FGA on the TRAIN season.
    Returns {player_id -> own_value, '_league_mean_' -> league mean}. The
    teammate-environment V* for a given test shot is then the mean own-value of
    the OTHER four offensive players on that shot's lineup (computed at apply
    time from the test possession's off_lineup_ids). This keeps player values
    out-of-sample-clean (from RS) while letting lineup composition vary per
    test possession.
    """
    t = train.copy()
    t["fg_pts"] = t["shot_outcome"].map({"made_2": 2, "made_3": 3}).fillna(0.0)
    own = t.groupby("primary_offensive_player_id")["fg_pts"].mean().to_dict()
    own["_league_mean_"] = float(t["fg_pts"].mean())
    return own


def apply_continuation(df: pd.DataFrame, table: dict, fallback: float) -> pd.Series:
    """
    V* per shot = mean own-value of the other 4 offensive players on the floor.
    Requires off_lineup_ids on df. Falls back to league mean if absent.
    """
    fb = table.get("_league_mean_", fallback)
    if "off_lineup_ids" not in df.columns:
        return df["primary_offensive_player_id"].map(
            lambda p: table.get(p, fb)).astype(float)

    def alt(row):
        ids = row["off_lineup_ids"]
        shooter = row["primary_offensive_player_id"]
        if ids is None or len(ids) == 0:
            return fb
        vals = [table.get(int(p), fb) for p in ids if int(p) != shooter]
        return float(np.mean(vals)) if vals else fb

    return df.apply(alt, axis=1).astype(float)


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------
def prepare(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["sec_left"] = df["clock"].apply(parse_game_clock_seconds)
    df["tau"] = df["sec_left"].apply(derive_tau)
    df["fg_pts"] = df["shot_outcome"].map({"made_2": 2, "made_3": 3}).fillna(0.0)
    return df


def compute_scores(df: pd.DataFrame, xpts_tab, cont_tab, cutoffs, fb_x, fb_v):
    df = df.copy()
    df["xPTS"] = apply_xpts(df, xpts_tab, fb_x)
    df["Vstar"] = apply_continuation(df, cont_tab, fb_v)
    # PASV per shot = xPTS - continuation value of NOT shooting
    df["PASV"] = df["xPTS"] - df["Vstar"]
    # Skinner signed gap = xPTS - f*(tau)
    fstar = df["tau"].map(cutoffs)
    df["Skinner_gap"] = df["xPTS"] - fstar
    return df
