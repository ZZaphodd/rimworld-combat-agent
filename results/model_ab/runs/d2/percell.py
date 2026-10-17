import sys, math
sys.path.insert(0, 'tools')
from hands_rc import *
from rca import sight
g = fire_grid()
cands = [(146,108),(148,108),(149,108),(145,109),(146,109),(147,109),(148,109),(149,109),(146,110),(148,110),(149,110),(145,111),(146,111),(147,111),(148,111)]
ruin = set((x, z) for x in range(144, 151) for z in range(107, 113))
for c in cands:
    sec = {'NW': [0,0], 'N': [0,0], 'E': [0,0], 'SE': [0,0]}
    for dx in range(-26, 27):
        for dz in range(-26, 27):
            o = (c[0]+dx, c[1]+dz)
            d = math.hypot(dx, dz)
            if o in ruin or g.blocks(*o) or d > 25.9 or d < 2: continue
            if not sight.shoot_line(g, c, o, 25.9): continue
            k = 'NW' if o[0] < 145 and o[1] > 110 else 'N' if o[1] > 112 else 'SE' if o[1] < 109 else 'E'
            sec[k][0] += 1
            if d <= 12.9: sec[k][1] += 1
    print(c, '  '.join(f'{k}:{v[0]}/{v[1]}' for k, v in sec.items()))
