import json, heapq, math, sys
T = json.load(open(__import__('pathlib').Path(__file__).with_name('terrain.json')))
G = {tuple(map(int, k.split(','))): v for k, v in T.items()}
BLOCK = set('%#')
def passable(c): return G.get(c, '%') not in BLOCK and G.get(c) != '~'
def los(a, b):
    (x0, z0), (x1, z1) = a, b
    n = max(abs(x1 - x0), abs(z1 - z0))
    for i in range(1, n):
        x = round(x0 + (x1 - x0) * i / n); z = round(z0 + (z1 - z0) * i / n)
        if G.get((x, z)) in BLOCK: return False
    return True
def path(s, t):
    D = {s: 0}; P = {}; q = [(0, s)]
    while q:
        d, c = heapq.heappop(q)
        if c == t: break
        if d > D[c]: continue
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                if dx == dz == 0: continue
                n = (c[0] + dx, c[1] + dz)
                if not passable(n): continue
                if dx and dz and (not passable((c[0] + dx, c[1])) or not passable((c[0], c[1] + dz))): continue
                nd = d + (1.414 if dx and dz else 1) + (0.5 if G.get(n) == '*' else 0)
                if nd < D.get(n, 1e9): D[n] = nd; P[n] = c; heapq.heappush(q, (nd, n))
    out = [t]
    while out[-1] != s: out.append(P[out[-1]])
    return out[::-1]
def first_seen(pth, pos):
    for c in pth:
        if los(c, pos): return c, round(math.dist(c, pos), 1)
    return None, None
if __name__ == '__main__':
    start = tuple(map(int, sys.argv[1].split(',')))
    tgt = tuple(map(int, sys.argv[2].split(',')))
    cands = [tuple(map(int, a.split(','))) for a in sys.argv[3:]]
    p = path(start, tgt)
    print('path len', len(p), 'via', p[::max(1, len(p)//15)])
    for c in cands:
        print(c, G.get(c), 'first seen from', first_seen(p, c))
