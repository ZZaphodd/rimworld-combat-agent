"""Fixed-assignment fire loop: each shooter keeps a target list; re-order when its target falls.
Stops on events (ours down / big HP drop / raider down)."""
import sys
sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parents[4] / 'tools'))
from hands import *

ASSIGN = {
    'Roach': ['Vector', 'Banshee', 'Lynx', 'Diver', 'Smog'],
    'Mocha': ['Vector', 'Lynx', 'Banshee', 'Diver', 'Smog'],
    'Carol': ['Lynx', 'Vector', 'Banshee', 'Diver', 'Smog'],
    'Cowan': ['Lynx', 'Vector', 'Banshee', 'Diver', 'Smog'],
    'Manning': ['Lynx', 'Vector', 'Banshee', 'Diver', 'Smog'],
}


def reorder(assign=ASSIGN):
    foes = {short_name(p['label']) for p in pawns('hostile') if not p.get('downed')}
    ours = {short_name(p['label']) for p in pawns('player') if not p.get('downed')}
    out = {}
    for n, lst in assign.items():
        if n not in ours:
            continue
        job = (rm.call('get_pawn', id=ids()[n]).get('job') or '').lower()
        want = [t for t in lst if t in foes]
        if want and f'attacking {want[0].lower()}' in job:
            out[n] = want[0]
            continue
        for t in want:
            if fire(n, t):
                out[n] = t + '+'
                break
        else:
            out[n] = job[:20]
    return out


if __name__ == '__main__':
    steps = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    for i in range(steps):
        print(reorder())
        ev = guard(n=3, dt=15, quiet=True)
        if ev:
            break
    st()
    aims()
