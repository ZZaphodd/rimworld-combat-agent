"""One decision step for a3: give fire orders to idle shooters by priority, then guard."""
import sys, math
sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parents[4] / 'tools'))
from hands import *

SHOOTERS = ['Mocha', 'Cowan', 'Roach', 'Diana', 'Manning', 'Carol']
PRIO = ['Diver', 'Lynx', 'Banshee', 'Smog', 'Vector', 'Linaly', 'Vera', 'Hexad']
MELEE = {'Linaly', 'Vera', 'Hexad'}


def decide(switch_to=None, verbose=True):
    ours = {short_name(p['label']): p for p in pawns('player') if not p.get('downed')}
    foes = {short_name(p['label']): p for p in pawns('hostile') if not p.get('downed')}
    # melee raiders close to any of ours go first
    close = sorted((min(math.dist((f['x'], f['z']), (o['x'], o['z'])) for o in ours.values()), n)
                   for n, f in foes.items() if n in MELEE)
    prio = [n for d, n in close if d <= 7] + [n for n in PRIO if n in foes]
    prio = list(dict.fromkeys(prio))
    if switch_to:
        prio = [switch_to] + [p for p in prio if p != switch_to]
    out = {}
    for n in SHOOTERS:
        if n not in ours:
            continue
        job = (rm.call('get_pawn', id=ids()[n]).get('job') or '').lower()
        cur = job.split('attacking ', 1)[1].rstrip('.').strip() if 'attacking' in job else None
        if cur and cur.lower() in {p.lower() for p in foes}:
            # keep, unless a higher-priority foe (or forced switch) is fireable
            ci = next((i for i, p in enumerate(prio) if p.lower() == cur.lower()), 99)
            better = [p for p in prio[:ci] if p in foes]
            if switch_to and cur.lower() != switch_to.lower() and fire(n, switch_to):
                out[n] = switch_to + '*'
                continue
            # melee-close override
            cur_close = any(d <= 7 and m.lower() == cur.lower() for d, m in close)
            mc = [p for p in better if p in MELEE and any(d <= 7 and m == p for d, m in close)]
            if mc and not cur_close and fire(n, mc[0]):
                out[n] = mc[0] + '!'
                continue
            out[n] = cur
            continue
        for t in prio:
            if fire(n, t):
                out[n] = t + '+'
                break
        else:
            out[n] = '-'
    if verbose:
        print('orders', out)
    return out


if __name__ == '__main__':
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 6
    dt = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    sw = sys.argv[3] if len(sys.argv) > 3 else None
    decide(sw)
    guard(n=n, dt=dt)
    st()
    aims()
