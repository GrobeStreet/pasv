import csv, json, statistics as st
def norm(n):
    n=n.strip().lower().replace('.','').replace(chr(39),'').replace('-',' ')
    for s in [' jr',' sr',' ii',' iii',' iv']:
        if n.endswith(s): n=n[:-len(s)]
    return ' '.join(n.split())
def f(x):
    try: return float(x)
    except: return None
def corr(xs,ys):
    pts=[(x,y) for x,y in zip(xs,ys) if x is not None and y is not None]
    if len(pts)<5: return None
    xs=[p[0] for p in pts]; ys=[p[1] for p in pts]; mx,my=st.mean(xs),st.mean(ys)
    num=sum((x-mx)*(y-my) for x,y in pts); den=(sum((x-mx)**2 for x in xs)*sum((y-my)**2 for y in ys))**0.5
    return num/den if den else None

panel=json.load(open('_npss_panel.json'))
# reload RS advanced for blk/drb/tpr/pos
rsadv={}
for y in range(2017,2026):
    try:
        for r in csv.DictReader(open(f'scrape_output/{y}_advanced.csv')):
            rsadv[(y,norm(r['name_display']))]=dict(blk=f(r.get('blk_pct')),drb=f(r.get('drb_pct')),
                tpr=f(r.get('fg3a_per_fga_pct')),pos=r.get('pos'),usg=f(r.get('usg_pct')),stl=f(r.get('stl_pct')))
    except FileNotFoundError: pass

# SCHEMABLE BIG: an interior anchor (big position OR high blk/drb) whose game is paint-bound
# (low 3PT rate) -> can be (a) pulled out of drop coverage on D and (b) walled off / spaced against on O.
def schemable_big(p):
    a=rsadv.get((p['year'],p['nm']))
    if not a: return None
    pos=(a['pos'] or '').upper()
    big = pos in ('C','PF') or (a['blk'] or 0)>=2.5 or (a['drb'] or 0)>=20
    if not big: return 0
    paintbound = (a['tpr'] or 0) < 0.20      # takes few threes -> non-stretch, schemable
    anchor = (a['blk'] or 0)>=2.0 or (a['drb'] or 0)>=18  # rim/glass anchor (drop-coverage type)
    return 1 if (paintbound and anchor) else 0
for p in panel: p['schemable']=schemable_big(p)

# TEST: among bigs, do schemable bigs collapse more?
bigs=[p for p in panel if p['schemable'] is not None and (rsadv.get((p['year'],p['nm']),{}).get('pos','') in ('C','PF'))]
sch=[p for p in panel if p['schemable']==1 and p['po_aqi'] is not None]
nonsch_big=[p for p in panel if p['schemable']==0 and (rsadv.get((p['year'],p['nm']),{}).get('pos','') in ('C','PF')) and p['po_aqi'] is not None]
def dropstat(g): 
    d=[p['po_aqi']-p['aqi'] for p in g if p['aqi'] is not None]
    return st.mean(d), len(d)
ms,ns=dropstat(sch); mn,nn=dropstat(nonsch_big)
print(f"=== SCHEMABLE BIG flag validity ===")
print(f"Schemable bigs:      n={ns}  mean AQI drop RS->PO = {ms:+.2f}")
print(f"Non-schem. bigs:     n={nn}  mean AQI drop RS->PO = {mn:+.2f}")
# among STARS specifically
stars=[p for p in panel if p['aqi'] and p['aqi']>=2.0 and p['po_aqi'] is not None]
sst=[p for p in stars if p['schemable']==1]; nst=[p for p in stars if p['schemable']==0]
def crate(g): return 100*sum(p['po_aqi']<1.75 for p in g)/len(g) if g else float('nan')
print(f"\n=== Among STARS (AQI>=2.0): collapse rate (PO AQI<1.75) ===")
print(f"Schemable-big stars:  n={len(sst)}  collapse={crate(sst):.0f}%  mean drop={st.mean([p['po_aqi']-p['aqi'] for p in sst]):+.2f}")
print(f"Non-schemable stars:  n={len(nst)}  collapse={crate(nst):.0f}%  mean drop={st.mean([p['po_aqi']-p['aqi'] for p in nst]):+.2f}")
# does it catch the marquee collapses?
print(f"\n=== Marquee collapsers — does the flag catch them? ===")
for nm,yr in [('joel embiid',2022),('joel embiid',2023),('rudy gobert',2025),('giannis antetokounmpo',2023),('kevin durant',2022)]:
    hit=[p for p in panel if p['nm']==nm and p['year']==yr]
    if hit: 
        p=hit[0]; a=rsadv.get((yr,nm),{})
        print(f"  {p['name'][:18]:19}{yr}  schemable={p['schemable']}  (3Pr={a.get('tpr')}, blk={a.get('blk')}, drb={a.get('drb')})")
json.dump(panel,open('_npss_panel.json','w'))
