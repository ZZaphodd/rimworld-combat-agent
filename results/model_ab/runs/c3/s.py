import sys, math
sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parents[4] / 'tools'))
sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parent))
from hands_rc import *
from geo import los
def look():
    rows, tick = snap(life=["standing", "downed"])
    ours = [p for p in rows if p.get('side') == 'player']
    them = [p for p in rows if p.get('side') == 'hostile']
    print('tick', tick)
    for p in ours: print('  ', row_line(p))
    tg = {h['id']: h.get('targeting') for h in pawns('hostile')}
    for h in them:
        vis = [(o['shortName'][:6], round(math.dist((o['x'], o['z']), (h['x'], h['z'])))) for o in ours
               if not o.get('downed') and los((h['x'], h['z']), (o['x'], o['z']))]
        print('  ', row_line(h), '|', tg.get(h['id']) or '-', '| sees', sorted(vis, key=lambda v: v[1])[:4])

GUNS = ['Cowan', 'Mocha', 'Manning', 'Diana', 'Carol', 'Roach']
def engage(prio, guns=GUNS, keep=True, verbose=True):
    """Each gunner: keep its current target if it is in prio and still fireable, else the first fireable of prio."""
    hs = {short_name(p['label']): p['id'] for p in pawns('hostile') if not p.get('downed')}
    I = ids()
    jobs = {p['shortName']: ((p.get('job') or {}).get('jobText') or '') for p in snap('player')[0]}
    out = {}
    for n in guns:
        if n not in I: continue
        job = jobs.get(n, '').lower()
        cur = next((e for e in prio if f'attacking {e.lower()}' in job), None)
        opts_cache = {}
        def ok(e):
            if e not in hs: return None
            opts = rm.call('order_pawn', id=I[n], targetId=hs[e]).get('options', [])
            return next((o for o in opts if o['label'].lower() == f'fire at {e}'.lower() and not o['disabled']), None)
        if keep and cur and cur in hs:
            # keep the current target unless a higher-priority one is fireable
            better = None
            for e in prio:
                if e == cur: break
                m = ok(e)
                if m: better = (e, m); break
            if not better:
                out[n] = cur + '(kept)'; continue
            e, m = better
            rm.call('order_pawn', id=I[n], targetId=hs[e], index=m['index']); out[n] = e; continue
        for e in prio:
            m = ok(e)
            if m:
                rm.call('order_pawn', id=I[n], targetId=hs[e], index=m['index']); out[n] = e; break
        else:
            out[n] = None
    if verbose: print('engage', out)
    return out

def brief_line():
    rows, tick = snap(life=["standing", "downed"])
    f = lambda p: f"{p['shortName'][:6]}{'' if not p.get('downed') else '(D)'}@{p['x']},{p['z']}:{round((p.get('summaryHealth') or 0)*100)}"
    o = ' '.join(f(p) for p in rows if p.get('side') == 'player')
    t = ' '.join(f(p) for p in rows if p.get('side') == 'hostile')
    return tick, rows, f"t{tick} US {o}\n      THEM {t}"

def step(total=120, dt=30):
    """advance in dt chunks; stop on a downed/dead change on either side or an HP drop >= 15 of ours"""
    _, r0, _ = brief_line()
    st0 = {p['id']: (p.get('downed'), p.get('summaryHealth') or 0, p.get('side')) for p in r0}
    t = 0
    while t < total:
        advance(dt); t += dt
        tick, rows, line = brief_line()
        ids_now = {p['id'] for p in rows}
        ev = []
        for p in rows:
            d0, h0, s0 = st0.get(p['id'], (None, 1, None))
            if p.get('downed') and not d0: ev.append(f"{p['shortName']} DOWN")
            if p.get('side') == 'player' and h0 - (p.get('summaryHealth') or 0) >= 0.15: ev.append(f"{p['shortName']} hp {round(h0*100)}->{round((p.get('summaryHealth') or 0)*100)}")
        for i, (d0, h0, s0) in st0.items():
            if i not in ids_now: ev.append(f"{i} gone/dead ({s0})")
        if ev:
            print(line); print('   EVENT', ev); return ev
    print(line)
    return []

def watch(total=600, dt=60, rng=37):
    """advance until a raider has (approx) LOS to one of ours within rng, a raider moves >4 cells, or events"""
    rows, t0 = snap(life=["standing", "downed"])
    pos0 = {p['id']: (p['x'], p['z']) for p in rows if p.get('side') == 'hostile'}
    t = 0
    while t < total:
        ev = step(dt, dt)
        t += dt
        rows, tick = snap(life=["standing", "downed"])
        ours = [p for p in rows if p.get('side') == 'player' and not p.get('downed')]
        them = [p for p in rows if p.get('side') == 'hostile' and not p.get('downed')]
        why = []
        for h in them:
            if h['id'] in pos0 and math.dist(pos0[h['id']], (h['x'], h['z'])) > 4: why.append(f"{h['shortName']} moved to {h['x']},{h['z']}")
            for o in ours:
                d = math.dist((o['x'], o['z']), (h['x'], h['z']))
                if d <= rng and los((h['x'], h['z']), (o['x'], o['z'])): why.append(f"{h['shortName']} sees {o['shortName']} {d:.0f}"); break
        if ev or why:
            print('   WATCH stop', why); return why or ev
    return []
