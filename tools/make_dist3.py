"""Assemble dist/ex3d from v3 renders and pack it.

  python3 tools/make_dist3.py --moves data/v3/moves.csv --renders out_v3 --dist dist/ex3d \
          [--pack dist/ex3d-v3.tar.gz]

dist/ex3d gets <key>.webp, <key>.f.webp, <key>.thumb.webp, <key>.f.thumb.webp
for every move and manifest.json:
  {"v": 2, "names": {"<name_en>": "<key>"}, "thumb": "webp", "size": [480, 320]}
Rows listed in data/v3/excluded.csv (name_en, reason: art that does not yet
match the exercise's own steps) are left out of the files and the manifest.
The pack has the top folder ex3d/; packs over 95 MB are split into
<pack>.part-aa, -ab, ... (split -b 90m) and the single file is removed.
"""
import argparse
import csv
import json
import os
import shutil
import subprocess
import tarfile

SUFFIXES = (".webp", ".f.webp", ".thumb.webp", ".f.thumb.webp")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--moves", required=True)
    ap.add_argument("--renders", required=True)
    ap.add_argument("--dist", required=True)
    ap.add_argument("--pack", default="")
    ap.add_argument("--accept", default="data/v3/qa-accepted.csv",
                    help="CSV key,gender,issue,reason of QA findings reviewed and accepted by eye")
    ap.add_argument("--size", default="",
                    help="WxH for the manifest; default: read from the first animation (v3 480x320, v4 600x400)")
    ap.add_argument("--exclude", default="data/v3/excluded.csv",
                    help="CSV name_en,reason of rows left out of the pack (art not right yet)")
    a = ap.parse_args()
    excl = set()
    if os.path.exists(a.exclude):
        excl = {r["name_en"] for r in csv.DictReader(open(a.exclude, encoding="utf-8"))}
    rows_all = list(csv.DictReader(open(a.moves, encoding="utf-8")))
    excl_keys = {r["key"] for r in rows_all if r["name_en"] in excl}
    # QA gate: every render must be clean or explicitly accepted after review
    acc = set()
    if os.path.exists(a.accept):
        acc = {(r["key"], r["gender"]) for r in csv.DictReader(open(a.accept, encoding="utf-8"))}
    blocked = []
    qa_dir = os.path.join(a.renders, "_qa")
    for fn in sorted(os.listdir(qa_dir)) if os.path.isdir(qa_dir) else []:
        d = json.load(open(os.path.join(qa_dir, fn)))
        if d["key"] in excl_keys:
            continue
        if d["issues"] and (d["key"], d["gender"]) not in acc:
            blocked.append(f"{d['key']}[{d['gender']}]: {' '.join(d['issues'])}")
    if blocked:
        print(len(blocked), "renders with open QA issues; not packing:")
        for b in blocked[:50]:
            print("  ", b)
        raise SystemExit(1)
    rows = [r for r in rows_all if r["key"] not in excl_keys]
    print(len(rows_all) - len(rows), "rows excluded")
    os.makedirs(a.dist, exist_ok=True)
    names, missing = {}, []
    for r in rows:
        k = r["key"]
        ok = True
        for sfx in SUFFIXES:
            src = os.path.join(a.renders, k + sfx)
            if os.path.exists(src):
                shutil.copyfile(src, os.path.join(a.dist, k + sfx))
            else:
                ok = False
        if not ok:
            missing.append(k)
        names[r["name_en"]] = k
    if a.size:
        size = [int(v) for v in a.size.split("x")]
    else:
        from PIL import Image
        first = next((os.path.join(a.dist, r["key"] + ".webp") for r in rows
                      if os.path.exists(os.path.join(a.dist, r["key"] + ".webp"))), None)
        size = list(Image.open(first).size) if first else [480, 320]
    man = {"v": 2, "names": names, "thumb": "webp", "size": size}
    with open(os.path.join(a.dist, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(man, f, ensure_ascii=False, indent=0, sort_keys=True)
    print(len(names), "names;", len(missing), "with missing files", missing[:10])
    if a.pack:
        top = os.path.basename(os.path.normpath(a.dist))
        with tarfile.open(a.pack, "w:gz") as tf:
            keep = {"manifest.json"} | {r["key"] + sfx for r in rows for sfx in SUFFIXES}
            for fn in sorted(os.listdir(a.dist)):
                if fn in keep:          # only the rows in the manifest (never leftovers of an older build)
                    tf.add(os.path.join(a.dist, fn), arcname=f"{top}/{fn}")
        size = os.path.getsize(a.pack)
        print(a.pack, size // (1024 * 1024), "MB")
        if size > 95 * 1024 * 1024:
            subprocess.check_call(["split", "-b", "90m", a.pack, a.pack + ".part-"])
            os.remove(a.pack)
            print("split into", sorted(p for p in os.listdir(os.path.dirname(a.pack) or ".")
                                       if p.startswith(os.path.basename(a.pack) + ".part-")))


if __name__ == "__main__":
    main()
