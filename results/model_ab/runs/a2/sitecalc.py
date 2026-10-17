import sys, math, heapq
rows = open(__import__('pathlib').Path(__file__).with_name('map.txt')).read().split('\n')
def cell(x, z):
    if not (0 <= x < 250 and 0 <= z < 250): return '#'
    return rows[249 - z][x]
def passable(x, z): return cell(x, z) not in '#%~'
def blocks(x, z): return cell(x, z) in '#%+'
def los(a, b):
    (x0, z0), (x1, z1) = a, b
    dx, dz = abs(x1 - x0), -abs(z1 - z0)
    sx, sz = (1 if x0 < x1 else -1), (1 if z0 < z1 else -1)
    err, x, z = dx + dz, x0, z0
    while (x, z) != (x1, z1):
        e2 = 2 * err
        if e2 >= dz: err += dz; x += sx
        if e2 <= dx: err += dx; z += sz
        if (x, z) != (x1, z1) and blocks(x, z): return False
    return True
def path(s, g):
    dist = {s: 0}; prev = {}; pq = [(0, s)]
    while pq:
        d, c = heapq.heappop(pq)
        if c == g: break
        if d > dist[c]: continue
        x, z = c
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                if dx == dz == 0: continue
                n = (x + dx, z + dz)
                if not passable(*n): continue
                if dx and dz and not (passable(x + dx, z) and passable(x, z + dz)): continue
                cost = (1.414 if dx and dz else 1) + (0.5 if cell(*n) == '*' else 0)
                nd = d + cost
                if nd < dist.get(n, 1e9):
                    dist[n] = nd; prev[n] = c; heapq.heappush(pq, (nd, n))
    p = [g]
    while p[-1] != s: p.append(prev[p[-1]])
    return p[::-1]
def assess(c, s=(32, 3)):
    p = path(s, c)
    first = None; g13 = None
    for i, q in enumerate(p):
        d = math.dist(q, c)
        if d <= 25.9 and first is None and los(q, c): first = (q, round(d, 1), len(p) - i)
        if d <= 12.9 and g13 is None and los(q, c): g13 = (q, round(d, 1))
    return first, g13
if __name__ == '__main__':
    for c in [tuple(map(int, a.split(','))) for a in sys.argv[1:]]:
        print(c, cell(*c), assess(c))
