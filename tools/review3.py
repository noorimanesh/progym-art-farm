"""Review helpers for the v3 renders.

  python3 tools/review3.py issues OUT          # renders whose QA has open issues (minus accepted)
  python3 tools/review3.py sheets OUT DEST [--status ok|missing|wrong] [--per 12] [--scale 0.35]
       contact sheets of finished renders, in move-list order, for review by eye
"""
import csv
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


def accepted():
    p = os.path.join(ROOT, "data/v3/qa-accepted.csv")
    return {(r["key"], r["gender"]) for r in csv.DictReader(open(p, encoding="utf-8"))} if os.path.exists(p) else set()


def issues(out):
    acc = accepted()
    rows = []
    for fn in sorted(os.listdir(os.path.join(out, "_qa"))):
        d = json.load(open(os.path.join(out, "_qa", fn)))
        if d["issues"] and (d["key"], d["gender"]) not in acc:
            rows.append(d)
    for d in rows:
        print(f"{d['key']}[{d['gender']}] {d['template']}: {' '.join(d['issues'])}")
    print(len(rows), "open")


def sheets(out, dest, status=None, per=12, scale=0.35):
    from artgen.sheet3 import build
    moves = list(csv.DictReader(open(os.path.join(ROOT, "data/v3/moves.csv"), encoding="utf-8")))
    keys = []
    for r in moves:
        st = "wrong" if r["status"] not in ("ok", "missing") else r["status"]
        if status and st != status:
            continue
        if os.path.exists(os.path.join(out, "_sheet", f"{r['key']}.f.2.png")):
            keys.append(r["key"])
    for p in build(out, dest, keys, per, scale):
        print(p)


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[0] == "issues":
        issues(a[1])
    else:
        kw = {}
        if "--status" in a:
            kw["status"] = a[a.index("--status") + 1]
        if "--per" in a:
            kw["per"] = int(a[a.index("--per") + 1])
        if "--scale" in a:
            kw["scale"] = float(a[a.index("--scale") + 1])
        sheets(a[1], a[2], **kw)
