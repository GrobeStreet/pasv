import json, statistics as st
panel=json.load(open('_npss_panel.json'))
def corr(xs,ys):
    pts=[(x,y) for x,y in zip(xs,ys) if x is not None and y is not None]
    if len(pts)<5: return None
    xs=[p[0] for p in pts]; ys=[p[1] for p in pts]
    mx,my=st.mean(xs),st.mean(ys)
    num=sum((x-mx)*(y-my) for x,y in pts); den=(sum((x-mx)**2 for x in xs)*sum((y-my)**2 for y in ys))**0.5
    return num/den if den else None

stars=[p for p in panel if p['aqi'] and p['aqi']>=2.0 and p['po_aqi'] is not None]
# define "collapse" = PO AQI falls below the 1.75 anchor floor despite RS star level
for p in stars:
    p['collapsed']= p['po_aqi'] < 1.75
    p['discount_pct']= (p['aqi']-(p['npss'] or p['aqi']))/p['aqi'] if p['aqi'] else 0
n_collapse=sum(p['collapsed'] for p in stars)
print(f"STAR TIER n={len(stars)}; collapsed (PO AQI<1.75 anchor floor): {n_collapse} ({100*n_collapse/len(stars):.0f}%)")

# Does heavy NPSS discount flag collapsers better than chance?
big=[p for p in stars if p['discount_pct']>=0.15]
sml=[p for p in stars if p['discount_pct']<0.15]
def rate(g): return 100*sum(x['collapsed'] for x in g)/len(g) if g else float('nan')
print(f"\nHeavily NPSS-discounted stars (>=15%): n={len(big)}  collapse rate={rate(big):.0f}%")
print(f"Lightly discounted stars (<15%):       n={len(sml)}  collapse rate={rate(sml):.0f}%")

# Does ANYTHING predict the collapse among stars? test candidate flags
print("\n=== What flags collapse among stars? (collapse rate by flag) ===")
def split(cond,label):
    g=[p for p in stars if cond(p)]; ng=[p for p in stars if not cond(p)]
    print(f"  {label:32} yes(n={len(g):2})={rate(g):3.0f}%   no(n={len(ng):2})={rate(ng):3.0f}%")
split(lambda p:p['arch'] in('playmaking_big','foul_drawer','3pt_heavy_creator'),"bad-PDR archetype")
split(lambda p:(p['hunt'] or 0)>=0.3,"high hunt-exposure >=0.3")
split(lambda p:(p['gpi'] or 0)>=0.3,"high GPI >=0.3")
split(lambda p:p['rs_usg'] and p['rs_usg']>=30,"very high usage >=30%")
split(lambda p:p['aqi']>=3.5,"elite RS AQI >=3.5 (regression)")

# the cleanest real signal: usage. Test corr of RS usage with drop among stars
print(f"\ncorr(RS usage, AQI drop) among stars = {corr([p['rs_usg'] for p in stars],[p['po_aqi']-p['aqi'] for p in stars])}")
print(f"corr(RS AQI, AQI drop) among stars    = {corr([p['aqi'] for p in stars],[p['po_aqi']-p['aqi'] for p in stars])}")
