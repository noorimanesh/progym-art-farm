"""Solve every template at a few phases (no rendering) and print QA issues."""
import sys, os, time, traceback
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from artgen import templates, qa
from artgen.poses import Ctx
g = sys.argv[1] if len(sys.argv) > 1 else "m"
only = sys.argv[2].split(",") if len(sys.argv) > 2 else None
c = Ctx(g)
t0 = time.time()
for name, tp in sorted(templates.REG.items()):
    if only and name not in only:
        continue
    row = {"name_en": name.replace("_", " "), "equipment": ""}
    try:
        ts = time.time()
        poses = [tp.pose(c, t, row) for t in (0.0, 0.156, 0.5, 0.844, 1.0)]
        iss = qa.check(c, poses, tp)
        print(f"{name:28s} {time.time()-ts:5.2f}s {' '.join(iss)}")
    except Exception as e:
        print(f"{name:28s} ERROR {type(e).__name__}: {e}")
        traceback.print_exc(limit=3)
print("total", round(time.time() - t0, 1))
