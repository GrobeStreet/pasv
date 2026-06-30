"""
NPSS held-out temporal validation.
Train window: 2017-2022 (define/fit on these). Test window: 2023-2025 (UNSEEN).
Tests whether the schemable-big + hunt collapse-detection survives out-of-sample.

The flags are RULE-BASED (binary, from raw stats), so "fitting" = (a) confirming the
schemable-big separation exists on TRAIN, then (b) measuring collapse detection on TEST
with the flags computed identically. Penalties aren't needed for the collapse-screen
claim (that's a classification result, not the point-prediction). We report the screen
metrics on train vs held-out test.
"""
import json, statistics as st

P = json.load(open("data/npss_panel.json"))
ANCHOR = 1.75          # collapse = playoff AQI falls below this
STAR = 2.0             # regular-season star threshold

def split(rows, lo, hi):
    return [r for r in rows if lo <= r["year"] <= hi]

def schemable_sep(rows):
    """mean RS->PO AQI drop for schemable vs non-schemable bigs (the core discovery)."""
    # identify 'bigs' the same way the framework does: archetype big OR has the flag's inputs
    sch = [r for r in rows if r.get("schemable") == 1]
    # non-schemable bigs: archetype contains 'big' but not flagged
    nonsch = [r for r in rows if r.get("schemable") == 0 and "big" in str(r.get("arch","")).lower()]
    def drop(rs):
        ds = [r["po_aqi"] - r["aqi"] for r in rs if r.get("po_aqi") is not None and r.get("aqi") is not None]
        return (st.mean(ds), len(ds)) if ds else (float("nan"), 0)
    return drop(sch), drop(nonsch)

def collapse_screen(rows):
    """Among RS stars (AQI>=2.0): collapse = po_aqi < 1.75. Compare flagged vs not."""
    stars = [r for r in rows if r.get("aqi", 0) >= STAR and r.get("po_aqi") is not None]
    flagged = [r for r in stars if r.get("hunt") or r.get("schemable")]
    notf = [r for r in stars if not (r.get("hunt") or r.get("schemable"))]
    def rate(rs):
        if not rs: return (float("nan"), 0, float("nan"))
        col = [r for r in rs if r["po_aqi"] < ANCHOR]
        drops = [r["po_aqi"] - r["aqi"] for r in rs]
        return (len(col)/len(rs), len(rs), st.mean(drops))
    fr = rate(flagged); nr = rate(notf)
    # recall: of all actual star collapses, how many were flagged
    all_collapses = [r for r in stars if r["po_aqi"] < ANCHOR]
    caught = [r for r in all_collapses if r.get("hunt") or r.get("schemable")]
    recall = len(caught)/len(all_collapses) if all_collapses else float("nan")
    lift = (fr[0]/nr[0]) if (nr[0] and nr[0]==nr[0] and nr[0]>0) else float("nan")
    return fr, nr, recall, lift, len(stars)

def report(label, rows):
    print(f"\n===== {label}  (n={len(rows)} player-seasons) =====")
    (sd, sn), (nd, nn) = schemable_sep(rows)
    print(f"  schemable-big RS->PO AQI drop: {sd:+.3f} (n={sn})   non-schemable big: {nd:+.3f} (n={nn})")
    fr, nr, recall, lift, ns = collapse_screen(rows)
    print(f"  RS stars (AQI>=2.0): n={ns}")
    print(f"  flagged collapse rate: {fr[0]:.1%} (n={fr[1]}, mean drop {fr[2]:+.3f})")
    print(f"  not-flagged collapse rate: {nr[0]:.1%} (n={nr[1]}, mean drop {nr[2]:+.3f})")
    print(f"  base-rate LIFT (flagged/not): {lift:.2f}x")
    print(f"  RECALL (collapses caught): {recall:.1%}")

print("NPSS HELD-OUT TEMPORAL VALIDATION")
print("="*60)
report("TRAIN 2017-2022 (in-sample)", split(P,2017,2022))
report("TEST 2023-2025 (HELD OUT, unseen)", split(P,2023,2025))
report("FULL 2017-2025 (reference, matches the doc)", split(P,2017,2025))
