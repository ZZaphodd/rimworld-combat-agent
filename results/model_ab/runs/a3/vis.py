import sys, math
L = open(__import__('pathlib').Path(__file__).with_name('fullmap.txt')).read().split('\n')
def c(x, z): return L[249 - z][x]
def line(x0, z0, x1, z1):
    pts = []; dx = abs(x1 - x0); dz = abs(z1 - z0); sx = 1 if x1 > x0 else -1; sz = 1 if z1 > z0 else -1
    err = dx - dz; x, z = x0, z0
    while True:
        pts.append((x, z))
        if (x, z) == (x1, z1): break
        e2 = 2 * err
        if e2 > -dz: err -= dz; x += sx
        if e2 < dx: err += dx; z += sz
    return pts
def los(a, b):
    return all(c(x, z) not in '%#' for x, z in line(*a, *b)[1:-1])
def vismap(S, R=37, x0=None, x1=None, z0=None, z1=None):
    x0 = x0 or S[0] - 40; x1 = x1 or S[0] + 40; z0 = z0 or S[1] - 15; z1 = z1 or S[1] + 40
    for z in range(z1, z0 - 1, -2):
        row = ''
        for x in range(x0, x1, 1):
            ch = c(x, z)
            if (x, z) == S: row += '@'; continue
            if ch in '%#': row += ch; continue
            d = math.dist((x, z), S)
            if d > R: row += ' '; continue
            row += ('o' if d <= 15 else ':' if d <= 26 else '-') if los(S, (x, z)) else '.'
        print(f'{z:3d} ' + row)
if __name__ == '__main__':
    S = (int(sys.argv[1]), int(sys.argv[2]))
    vismap(S)
