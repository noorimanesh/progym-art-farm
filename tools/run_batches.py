#!/usr/bin/env python3
"""Render the whole work list in batches, both genders in parallel.

  python3 tools/run_batches.py --csv data/worklist.csv --out out --batch 100 [--from 0] [--to N]

Per batch: one render process per gender (1 thread each), then a contact
sheet (start/mid/end of every exercise, both genders), then the batch's
WebPs + thumbnails are packed into a tar.gz (<= 90 MB) and copied to the
archive folder (and uploaded to the GitHub release when that is permitted).
Already rendered files are skipped, so the script can be resumed.
"""
import argparse
import csv
import os
import shutil
import subprocess
import sys
import tarfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PY = os.environ.get("ART_PYTHON", sys.executable)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default=os.path.join(ROOT, "data", "worklist.csv"))
    ap.add_argument("--out", default=os.path.join(ROOT, "out"))
    ap.add_argument("--batch", type=int, default=100)
    ap.add_argument("--from", dest="start", type=int, default=0)
    ap.add_argument("--to", type=int, default=10 ** 9)
    ap.add_argument("--samples", type=int, default=8)
    ap.add_argument("--archive", default="")
    ap.add_argument("--upload", action="store_true")
    ap.add_argument("--serial", action="store_true", help="one render process at a time (male, then female)")
    ap.add_argument("--threads", type=int, default=1)
    ap.add_argument("--pack", default="exercise-art-v1", help="pack name prefix; empty = no packs")
    a = ap.parse_args()
    rows = list(csv.DictReader(open(a.csv, encoding="utf-8")))
    end = min(len(rows), a.to)
    os.makedirs(a.out, exist_ok=True)
    sheets = os.path.join(a.out, "_sheets")
    os.makedirs(sheets, exist_ok=True)
    for b0 in range(a.start, end, a.batch):
        b1 = min(b0 + a.batch, end)
        name = f"b{b0:04d}-{b1 - 1:04d}"
        t0 = time.time()
        procs = []
        for g in ("m", "f"):
            log = open(os.path.join(a.out, f"_log_{g}_{b0}.txt"), "a")
            procs.append(subprocess.Popen([PY, "-m", "artgen.render", "--csv", a.csv, "--gender", g, "--out", a.out,
                                           "--start", str(b0), "--end", str(b1), "--threads", str(a.threads),
                                           "--samples", str(a.samples), "--skip-existing"],
                                          cwd=ROOT, stdout=log, stderr=subprocess.STDOUT))
            if a.serial:
                procs[-1].wait()
        for p in procs:
            p.wait()
        slugs = [r["slug"] for r in rows[b0:b1]]
        sys.path.insert(0, ROOT)
        from artgen.contact import sheet
        for k in range(0, len(slugs), 25):
            sheet(a.out, os.path.join(sheets, f"{name}_{k // 25}.png"), slugs[k:k + 25], scale=0.4)
        files = []
        for s in slugs:
            for suf in ("", ".f"):
                for ext in (".webp", ".thumb.jpg"):
                    f = os.path.join(a.out, s + suf + ext)
                    if os.path.exists(f):
                        files.append(f)
        if not a.pack:
            print(f"{name}: {len(files)} files, {time.time() - t0:.0f}s", flush=True)
            continue
        tgz = os.path.join(a.out, "_packs", f"{a.pack}-{name}.tar.gz")
        os.makedirs(os.path.dirname(tgz), exist_ok=True)
        with tarfile.open(tgz, "w:gz") as t:
            for f in files:
                t.add(f, arcname=os.path.basename(f))
        if a.archive:
            os.makedirs(a.archive, exist_ok=True)
            shutil.copy(tgz, a.archive)
        if a.upload:
            subprocess.run([sys.executable, os.path.join(HERE, "upload_release.py"), "--name", name, tgz])
        print(f"{name}: {len(files)} files, {os.path.getsize(tgz) // 1024} KB, {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
