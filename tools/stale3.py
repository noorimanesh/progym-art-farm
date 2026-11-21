"""List renders whose solved loop no longer matches the current code / data
(pose hash differs or is missing) -> keys to render again.

  venv/bin/python tools/stale3.py data/v3/moves.csv out_v3 [--gender m] [--requa] > data/v3/stale.txt

--requa: for renders whose poses still match, recompute the QA findings with
the current checks and rewrite them in the QA json (no re-render needed).
"""
import csv
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from artgen import templates, motion, spec3, qa3  # noqa: E402
from artgen.poses import Ctx  # noqa: E402
from artgen.mirror import Mirror  # noqa: E402
from artgen.render3 import solve_loop, fit_view, pose_hash, athlete_fraction  # noqa: E402


def main():
    a = sys.argv[1:]
    g = "m"
    if "--gender" in a:
        i = a.index("--gender")
        g = a[i + 1]
        del a[i:i + 2]
    requa = "--requa" in a
    if requa:
        a.remove("--requa")
    moves, out = a[0], a[1]
    sfx = "" if g == "m" else ".f"
    ctx = Ctx(g)
    mir = Mirror(ctx.r)
    for row in csv.DictReader(open(moves, encoding="utf-8")):
        q = os.path.join(out, "_qa", f"{row['key']}{sfx}.json")
        if not os.path.exists(q):
            continue
        d = json.load(open(q))
        old = d.get("pose_hash")
        row = spec3.expand(row)
        tpl = templates.get(row["template"])
        tl = motion.timeline(**row["_tempo"], linear=tpl.linear)
        poses = solve_loop(tpl, ctx, tl, row, mir)
        _, cam, tgt, lens = fit_view(poses, row, tpl)
        if pose_hash(poses, cam) != old:
            print(row["key"], flush=True)
        elif requa:
            rep = qa3.check(ctx, poses, tl, tpl, row)
            frac = athlete_fraction(poses, cam, tgt, lens)
            if frac < qa3.MIN_FRAME:
                rep["issues"].append(f"frame:{frac:.2f}")
            if rep["issues"] != d["issues"]:
                d.update({k: v for k, v in rep.items()})
                d["athlete_frac"] = round(frac, 2)
                json.dump(d, open(q, "w"), indent=1)


if __name__ == "__main__":
    main()
