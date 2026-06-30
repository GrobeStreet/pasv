import json, statistics as st
panel=json.load(open('_npss_panel.json'))
def corr(xs,ys):
    pts=[(x,y) for x,y in zip(xs,ys) if x is not None and y is not None]
    if len(pts)<5: return None
    xs=[p[0] for p in pts]; ys=[p[1] for p in pts]; mx,my=st.mean(xs),st.mean(ys)
    num=sum((x-mx)*(y-my) for x,y in pts); den=(sum((x-mx)**2 for x in xs)*sum((y-my)**2 for y in ys))**0.5
    return num/den if den else None

# ---- v0.2 design ----
# Step 1: regression-EXPECTED playoff AQI. Fit po_aqi ~ a + b*rs_aqi on full panel (this is the honest
#         baseline: most "decline" is regression). v0.2 must beat THIS.
sv=[p for p in panel if p['po_aqi'] is not None and p['aqi'] is not None]
xs=[p['aqi'] for p in sv]; ys=[p['po_aqi'] for p in sv]
mx,my=st.mean(xs),st.mean(ys)
b=sum((x-mx)*(y-my) for x,y in zip(xs,ys))/sum((x-mx)**2 for x in xs); a=my-b*mx
print(f"Regression baseline: expected_PO_AQI = {a:.3f} + {b:.3f}*RS_AQI")

# Step 2: apply the TWO validated flags as additional penalties on top of the regression expectation.
# Fit the flag penalties from the data (mean residual for flagged players), so it's empirical not guessed.
for p in sv:
    p['exp']=a+b*p['aqi']           # regression-expected PO AQI
    p['resid']=p['po_aqi']-p['exp'] # how much they beat/miss expectation
hunt_flag=[p for p in sv if (p['hunt'] or 0)>=0.3]
sch_flag=[p for p in sv if p['schemable']==1]
hunt_pen=st.mean([p['resid'] for p in hunt_flag])      # avg extra miss for hunt-exposed
sch_pen=st.mean([p['resid'] for p in sch_flag])
print(f"Hunt-exposed extra residual (penalty): {hunt_pen:+.3f}  (n={len(hunt_flag)})")
print(f"Schemable-big extra residual (penalty): {sch_pen:+.3f}  (n={len(sch_flag)})")

def npss_v2(p):
    if p['aqi'] is None: return None
    val=a+b*p['aqi']
    if (p['hunt'] or 0)>=0.3: val+=hunt_pen
    if p['schemable']==1: val+=sch_pen
    return round(val,3)
for p in sv: p['npss2']=npss_v2(p)

# ---- HEAD-TO-HEAD BACKTEST: predict actual PO AQI ----
print("\n=== BACKTEST: predicting actual PLAYOFF AQI (n=%d) ===" % len(sv))
print(f"  raw RS AQI        r = {corr([p['aqi'] for p in sv],[p['po_aqi'] for p in sv]):.4f}")
print(f"  NPSS v0.1         r = {corr([p['npss'] for p in sv],[p['po_aqi'] for p in sv]):.4f}")
print(f"  regression-only   r = {corr([p['exp'] for p in sv],[p['po_aqi'] for p in sv]):.4f}")
print(f"  NPSS v0.2         r = {corr([p['npss2'] for p in sv],[p['po_aqi'] for p in sv]):.4f}")
# MAE comparison (does v0.2 reduce prediction error?)
def mae(pred): return st.mean([abs(p['po_aqi']-p[pred]) for p in sv])
print(f"\n  MAE raw AQI={mae('aqi'):.3f} | regression={mae('exp'):.3f} | v0.2={mae('npss2'):.3f}")

# ---- STAR-TIER collapse detection (the actual claim) ----
stars=[p for p in sv if p['aqi']>=2.0]
for p in stars: p['flagged_v2']= ((p['hunt'] or 0)>=0.3) or (p['schemable']==1)
fl=[p for p in stars if p['flagged_v2']]; nf=[p for p in stars if not p['flagged_v2']]
def crate(g): return 100*sum(p['po_aqi']<1.75 for p in g)/len(g) if g else float('nan')
print(f"\n=== STAR collapse detection (PO AQI<1.75), n_stars={len(stars)} ===")
print(f"  v0.2 FLAGGED (hunt OR schemable): n={len(fl)}  collapse={crate(fl):.0f}%  mean drop={st.mean([p['po_aqi']-p['aqi'] for p in fl]):+.2f}")
print(f"  v0.2 not flagged:                 n={len(nf)}  collapse={crate(nf):.0f}%  mean drop={st.mean([p['po_aqi']-p['aqi'] for p in nf]):+.2f}")
# precision/recall on collapse
collapsers=[p for p in stars if p['po_aqi']<1.75]
caught=[p for p in collapsers if p['flagged_v2']]
print(f"  Recall: v0.2 flags {len(caught)}/{len(collapsers)} = {100*len(caught)/len(collapsers):.0f}% of actual star collapses")
json.dump(panel,open('_npss_panel.json','w'))
