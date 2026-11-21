#!/usr/bin/env python3
"""Assemble the deliverable folder for the exercise table.

  python3 tools/make_dist.py --work data/worklist-3.2.0.csv --new out3 --old out \
      --dist dist/ex3d --review data/review-3.2.0.csv

For every row of the work list (columns id, slug = key, ...) the four files
<key>.webp, <key>.f.webp, <key>.thumb.jpg, <key>.f.thumb.jpg are copied from
the new render folder when present there, else from the old one.  The dist
folder ends up holding exactly those files plus manifest.json
({"v":1,"items":{"<id>":"<key>"}}).  The review CSV lists every row with its
template, match and flags (render checks and notes).
"""
import argparse
import csv
import glob
import json
import os
import shutil

SUFFIXES = (".webp", ".f.webp", ".thumb.jpg", ".f.thumb.jpg")


def qa_flags(folder):
    out = {}
    for f in glob.glob(os.path.join(folder, "qa*.csv")):
        g = "f" if os.path.basename(f).startswith("qa.f") else "m"
        for r in csv.reader(open(f, encoding="utf-8")):
            if len(r) >= 6 and r[5]:
                bad = []
                for it in r[5].split(";"):
                    k, _, v = it.partition(":")
                    try:
                        if float(v) > 0.05:
                            bad.append(f"{g}:{k}")
                    except ValueError:
                        bad.append(f"{g}:{it}")
                if bad:
                    out.setdefault(r[0], {})[g] = bad
                else:
                    out.setdefault(r[0], {}).pop(g, None)
            elif len(r) >= 1:
                out.setdefault(r[0], {}).pop(g, None)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--work", required=True)
    ap.add_argument("--new", required=True)
    ap.add_argument("--old", required=True)
    ap.add_argument("--dist", required=True)
    ap.add_argument("--review", required=True)
    a = ap.parse_args()
    rows = list(csv.DictReader(open(a.work, encoding="utf-8")))
    os.makedirs(a.dist, exist_ok=True)
    want, items, missing, src_count = set(), {}, [], {"new": 0, "old": 0}
    qa_new, qa_old = qa_flags(a.new), qa_flags(a.old)
    review = []
    for r in rows:
        key = r["slug"]
        items[r["id"]] = key
        src = a.new if all(os.path.exists(os.path.join(a.new, key + s)) for s in SUFFIXES) else a.old
        ok = True
        for s in SUFFIXES:
            fp = os.path.join(src, key + s)
            if not os.path.exists(fp):
                ok = False
                continue
            want.add(key + s)
            dst = os.path.join(a.dist, key + s)
            if not os.path.exists(dst) or os.path.getsize(dst) != os.path.getsize(fp) or \
                    os.path.getmtime(dst) < os.path.getmtime(fp):
                shutil.copy2(fp, dst)
        if not ok:
            missing.append(key)
        src_count["new" if src == a.new else "old"] += ok
        qa = (qa_new if src == a.new else qa_old).get(key, {})
        flags = [x for v in qa.values() for x in v]
        if r.get("note"):
            flags.append(r["note"])
        if not ok:
            flags.append("MISSING")
        review.append(dict(id=r["id"], key=key, name_en=r["name_en"], template=r["template"], match=r["match"],
                           flags=" | ".join(flags)))
    with open(os.path.join(a.dist, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump({"v": 1, "items": items}, f, ensure_ascii=False, separators=(",", ":"))
    want.add("manifest.json")
    extra = [f for f in os.listdir(a.dist) if f not in want]
    for f in extra:
        os.remove(os.path.join(a.dist, f))
    with open(a.review, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["id", "key", "name_en", "template", "match", "flags"])
        w.writeheader()
        w.writerows(review)
    print(f"{len(rows)} rows, {len(set(items.values()))} keys; from new {src_count['new']}, from old "
          f"{src_count['old']}; missing {len(missing)}; removed {len(extra)} stray files")
    if missing:
        print("missing:", " ".join(missing[:40]))


if __name__ == "__main__":
    main()
