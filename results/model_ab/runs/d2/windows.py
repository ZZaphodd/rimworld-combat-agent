import sys, math
sys.path.insert(0, 'tools')
from hands_rc import *
from rca import sight
g = fire_grid()
ours = [(146,108),(148,108),(145,109),(146,109),(148,109),(147,109),(149,108),(149,109)]
R = 25.9
x0, x1, z0, z1 = 120, 175, 85, 136
rows = []
for z in range(z1, z0 - 1, -1):
    row = ''
    for x in range(x0, x1 + 1):
        if (x, z) in ours:
            row += 'O'; continue
        if g.blocks(x, z):
            row += '#'; continue
        n = sum(1 for c in ours if math.dist(c, (x, z)) >= 1.5 and sight.shoot_line(g, (x, z), c, R, held_open=ours))
        row += ('.' if n == 0 else (str(n) if n < 10 else '+')) if not g.cover(x, z) else ('c' if n == 0 else 'C')
    rows.append(f'{z:3d} ' + row)
print('    ' + ''.join(str(x % 10) for x in range(x0, x1 + 1)))
print('\n'.join(rows))
