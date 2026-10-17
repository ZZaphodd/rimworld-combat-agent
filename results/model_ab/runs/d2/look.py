import sys
sys.path.insert(0, 'tools')
from hands_rc import *
import io, contextlib
def look(full=True):
    st()
    rows, _ = snap(include=("weapon",), life=["standing", "downed"])
    ours = [r for r in rows if r.get('side') == 'player' and not r.get('downed')]
    for r in ours:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            out = targets(r['id'])
        if out or full:
            print('  ', buf.getvalue().strip())
    them = [r for r in rows if r.get('side') == 'hostile' and not r.get('downed')]
    for r in them:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            out = targets(r['id'])
        if out:
            print('  T', buf.getvalue().strip())
