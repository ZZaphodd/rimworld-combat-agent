import sys, math
sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parents[4] / 'tools'))
from hands import *
def q(jobs=True):
    t = rm.call("get_status")["ticksGame"] - 383
    ours = pawns("player"); foes = pawns("hostile")
    print("t", t)
    for p in ours:
        g = rm.call("get_pawn", id=p["id"])
        print(f"  {short_name(p['label'])[:9]:9} @{p['x']},{p['z']} {g.get('health')}%{' DOWN' if p.get('downed') else ''} | {(g.get('job') or '')[:34]}")
    for h in foes:
        g = rm.call("get_pawn", id=h["id"])
        d = min((math.dist((h['x'], h['z']), (p['x'], p['z'])) for p in ours if not p.get('downed')), default=0)
        print(f"  * {short_name(h['label'])[:8]:8} @{h['x']},{h['z']} {g.get('health')}%{' DOWN' if h.get('downed') else ''} d{d:.0f} | {(g.get('job') or '')[:24]} | {h.get('targeting') or ''}")

def until_throw(maxt=120, dt=10, targets=None, throwers=('Pigork', 'Poinis', 'Moinork'), close=5):
    hp0 = {short_name(p['label']): rm.call('get_pawn', id=p['id']).get('health') for p in pawns('player')}
    t = 0
    while t < maxt:
        wait(dt); t += dt
        foes = [h for h in pawns('hostile') if not h.get('downed')]
        ours = [p for p in pawns('player') if not p.get('downed')]
        names = [short_name(h['label']) for h in foes if (targets is None or short_name(h['label']) in targets)]
        ok = {}
        for h in names:
            fs = [n for n in throwers if fireable(n, h)]
            if fs: ok[h] = fs
        near = [(short_name(h['label']), short_name(p['label'])) for h in foes for p in ours
                if math.dist((h['x'], h['z']), (p['x'], p['z'])) <= close]
        down = [short_name(p['label']) for p in pawns('player') if p.get('downed')]
        if ok or near or down:
            print('stop', t, ok, near, down); break
    q()

GUNS = ['Furr', 'Curly', 'Trev', 'Poinlaoik', 'Paul']
def engage(guns=GUNS, prio=()):
    """Guns not already attacking a standing raider fire at the first fireable of prio, else the nearest fireable."""
    foes = [h for h in pawns('hostile') if not h.get('downed')]
    ours = {short_name(p['label']): p for p in pawns('player') if not p.get('downed')}
    fn = [short_name(h['label']) for h in foes]
    for n in guns:
        if n not in ours: continue
        job = (rm.call('get_pawn', id=ours[n]['id']).get('job') or '').lower()
        cur = next((t for t in fn if f'attacking {t.lower()}' in job), None)
        if cur and (not prio or cur in prio[:1]): continue
        me = ours[n]
        order = [t for t in prio if t in fn] + sorted(fn, key=lambda t: math.dist((me['x'], me['z']), next((h['x'], h['z']) for h in foes if short_name(h['label']) == t)))
        for t in order:
            if t == cur: break
            if fire(n, t):
                print('  ', n, '->', t); break
def step(dt=15, prio=()):
    wait(dt); engage(prio=prio); q(); print(projectiles())

def hold(assign, total=60, dt=15):
    """assign: {pawn: [targets in priority]}. Every dt ticks: a pawn whose job doesn't name a standing
    target of its list gets the first fireable one. Stops early on a downed pawn of ours or a raider gone."""
    f0 = {short_name(h['label']) for h in pawns('hostile') if not h.get('downed')}
    d0 = {short_name(p['label']) for p in pawns('player') if p.get('downed')}
    t = 0
    while t < total:
        wait(dt); t += dt
        foes = {short_name(h['label']) for h in pawns('hostile') if not h.get('downed')}
        ours = {short_name(p['label']): p for p in pawns('player')}
        for n, lst in assign.items():
            if n not in ours or ours[n].get('downed'): continue
            job = (rm.call('get_pawn', id=ours[n]['id']).get('job') or '').lower()
            if any(f'attacking {x.lower()}' in job for x in lst if x in foes): continue
            for x in lst:
                if x in foes and fire(n, x):
                    print('   ', n, '->', x); break
        d1 = {n for n, p in ours.items() if p.get('downed')}
        if foes != f0 or d1 - d0:
            print('event', f0 - foes, d1 - d0); break
    q(); print(projectiles())

def auto(total=60, dt=10, guns=('Trev', 'Curly', 'Paul', 'Poinlaoik', 'Furr'), throwers=(), prio=()):
    """Every dt: idle guns ('watching'/'standing') fire at the first fireable raider in prio, else the nearest fireable.
    Stops on a pawn of ours down or a raider down/gone."""
    f0 = {short_name(h['label']) for h in pawns('hostile') if not h.get('downed')}
    d0 = {short_name(p['label']) for p in pawns('player') if p.get('downed')}
    t = 0
    while t < total:
        wait(dt); t += dt
        foes = [h for h in pawns('hostile') if not h.get('downed')]
        fn = {short_name(h['label']): h for h in foes}
        ours = {short_name(p['label']): p for p in pawns('player')}
        for n in list(guns) + list(throwers):
            p = ours.get(n)
            if not p or p.get('downed'): continue
            job = (rm.call('get_pawn', id=p['id']).get('job') or '').lower()
            if not any(k in job for k in ('watching', 'standing')) and not any(f'attacking {x.lower()}' in job and x not in fn for x in f0):
                continue
            order = [x for x in prio if x in fn] + sorted(fn, key=lambda x: math.dist((p['x'], p['z']), (fn[x]['x'], fn[x]['z'])))
            for x in order:
                if fire(n, x):
                    print('   t', rm.call('get_status')['ticksGame'] - 383, n, '->', x); break
        d1 = {n for n, p in ours.items() if p.get('downed')}
        if set(fn) != f0 or d1 - d0:
            print('event', f0 - set(fn), d1 - d0); break
    q(); print(projectiles())
