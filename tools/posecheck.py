"""Solve moves and run the automatic checks without rendering (fast).

  venv/bin/python tools/posecheck.py data/v3/test-moves.csv [key ...] [--gender f]
"""
import csv
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from artgen import templates, motion, qa3, spec3  # noqa: E402
from artgen.poses import Ctx  # noqa: E402
from artgen.mirror import Mirror  # noqa: E402
from artgen.render3 import solve_loop, fit_view, athlete_fraction  # noqa: E402


def main():
    args = sys.argv[1:]
    g = "m"
    if "--gender" in args:
        i = args.index("--gender")
        g = args[i + 1]
        del args[i:i + 2]
    path, keys = args[0], set(args[1:])
    rows = [r for r in csv.DictReader(open(path, encoding="utf-8")) if not keys or r["key"] in keys]
    ctx = Ctx(g)
    mir = Mirror(ctx.r)
    bad = 0
    for row in rows:
        t0 = time.time()
        row = spec3.expand(row)
        tpl = templates.get(row["template"])
        tl = motion.timeline(**row["_tempo"], linear=tpl.linear)
        try:
            poses = solve_loop(tpl, ctx, tl, row, mir)
        except Exception as e:  # report and continue
            print(f"{row['key']:40s} ERROR {type(e).__name__}: {e}")
            bad += 1
            continue
        rep = qa3.check(ctx, poses, tl, tpl, row)
        _, cam, tgt, lens = fit_view(poses, row, tpl)
        frac = athlete_fraction(poses, cam, tgt, lens)
        if frac < qa3.MIN_FRAME:
            rep["issues"].append(f"frame:{frac:.2f}")
        bad += bool(rep["issues"])
        print(f"{row['key']:40s} {row['template']:22s} {time.time() - t0:4.1f}s grip {rep['grip_mm']:4.0f} "
              f"sup {rep['support_mm']:+5.0f} frame {frac:.2f} {' '.join(rep['issues'])}")
    print(f"{len(rows)} moves, {bad} with issues")


if __name__ == "__main__":
    main()
