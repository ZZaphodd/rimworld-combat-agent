import sys, math
sys.path.insert(0, 'tools')
from hands_rc import *
from rca import sight
g = fire_grid()
cells = [(x, z) for x in range(142, 153) for z in range(105, 115)]
ruin = set((x, z) for x in range(144, 151) for z in range(107, 113))
for c in cells:
    if g.blocks(*c):
        continue
    tot = sw = 0
    for dx in range(-26, 27):
        for dz in range(-26, 27):
            o = (c[0] + dx, c[1] + dz)
            if o in ruin or g.blocks(*o) or math.hypot(dx, dz) > 25.9 or math.hypot(dx, dz) < 2:
                continue
            if sight.shoot_line(g, o, c, 25.9):
                tot += 1
                a = sight.angle_flat(c, o)
                if 180 <= a <= 270:
                    sw += 1
    print(c, 'blocks' if g.blocks(*c) else '', 'cover' if g.cover(*c) else '', 'tot', tot, 'SW', sw)
