"""
NPSS held-out temporal validation.
Train window: 2017-2022. Test window: 2023-2025 (unseen).

IMPORTANT CORRECTION (2026-08-26): the original held-out script used Python
truthiness for the continuous `hunt` score (`r.get("hunt") or ...`). That
incorrectly treated every non-zero hunt score as Hunt-Exposed and produced an
inflated 100% held-out recall claim. The canonical v0.2 rule is
`hunt >= 0.30`. This script now implements that threshold explicitly.

The flags are rule-based from regular-season data. Penalty magnitudes are not
used for the collapse-screen evaluation below.
"""
import json
import statistics as st

P = json.load(open("data/npss_panel.json"))
ANCHOR = 1.75
STAR = 2.0
HUNT_THRESHOLD = 0.30


def split(rows, lo, hi):
    return [r for r in rows if lo <= r["year"] <= hi]


def hunt_exposed(r):
    try:
        return float(r.get("hunt") or 0.0) >= HUNT_THRESHOLD
    except (TypeError, ValueError):
        return False


def schemable_big(r):
    return r.get("schemable") == 1


def flagged_v02(r):
    return hunt_exposed(r) or schemable_big(r)


def schemable_sep(rows):
    """Mean RS->PO AQI change for schemable vs non-schemable bigs."""
    sch = [r for r in rows if schemable_big(r)]
    nonsch = [
        r for r in rows
        if r.get("schemable") == 0 and "big" in str(r.get("arch", "")).lower()
    ]

    def drop(rs):
        ds = [
            r["po_aqi"] - r["aqi"]
            for r in rs
            if r.get("po_aqi") is not None and r.get("aqi") is not None
        ]
        return (st.mean(ds), len(ds)) if ds else (float("nan"), 0)

    return drop(sch), drop(nonsch)


def collapse_screen(rows):
    """Among RS stars, collapse = playoff AQI < 1.75. Evaluate canonical v0.2 flags."""
    stars = [
        r for r in rows
        if r.get("aqi", 0) >= STAR and r.get("po_aqi") is not None
    ]
    flagged = [r for r in stars if flagged_v02(r)]
    notf = [r for r in stars if not flagged_v02(r)]

    def rate(rs):
        if not rs:
            return (float("nan"), 0, float("nan"))
        col = [r for r in rs if r["po_aqi"] < ANCHOR]
        drops = [r["po_aqi"] - r["aqi"] for r in rs]
        return (len(col) / len(rs), len(rs), st.mean(drops))

    fr = rate(flagged)
    nr = rate(notf)
    all_collapses = [r for r in stars if r["po_aqi"] < ANCHOR]
    caught = [r for r in all_collapses if flagged_v02(r)]
    recall = len(caught) / len(all_collapses) if all_collapses else float("nan")
    lift = fr[0] / nr[0] if nr[0] == nr[0] and nr[0] > 0 else float("nan")

    tp = len(caught)
    fn = len(all_collapses) - tp
    fp = len([r for r in flagged if r["po_aqi"] >= ANCHOR])
    tn = len([r for r in notf if r["po_aqi"] >= ANCHOR])
    precision = tp / (tp + fp) if tp + fp else float("nan")
    specificity = tn / (tn + fp) if tn + fp else float("nan")

    return fr, nr, recall, lift, len(stars), tp, fp, fn, tn, precision, specificity


def report(label, rows):
    print(f"\n===== {label} (n={len(rows)} player-seasons) =====")
    (sd, sn), (nd, nn) = schemable_sep(rows)
    print(
        f"  schemable-big RS->PO AQI change: {sd:+.3f} (n={sn})   "
        f"non-schemable big: {nd:+.3f} (n={nn})"
    )
    fr, nr, recall, lift, ns, tp, fp, fn, tn, precision, specificity = collapse_screen(rows)
    print(f"  RS stars (AQI>={STAR:.1f}): n={ns}")
    print(f"  flagged collapse rate: {fr[0]:.1%} (n={fr[1]}, mean change {fr[2]:+.3f})")
    print(f"  not-flagged collapse rate: {nr[0]:.1%} (n={nr[1]}, mean change {nr[2]:+.3f})")
    print(f"  base-rate lift (flagged/not): {lift:.2f}x")
    print(f"  recall: {recall:.1%}")
    print(f"  precision: {precision:.1%}")
    print(f"  specificity: {specificity:.1%}")
    print(f"  confusion matrix: TP={tp} FP={fp} FN={fn} TN={tn}")


print("NPSS HELD-OUT TEMPORAL VALIDATION — CORRECTED v0.2 RULE")
print("=" * 72)
report("TRAIN 2017-2022", split(P, 2017, 2022))
report("TEST 2023-2025 (HELD OUT)", split(P, 2023, 2025))
report("FULL 2017-2025 (REFERENCE)", split(P, 2017, 2025))
