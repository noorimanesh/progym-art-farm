#!/usr/bin/env python3
"""Merge the template-match review list with the automatic render checks.

  python3 tools/make_review.py data/worklist.csv out/ data/review.csv

A row is listed when its template is approximate / a fallback, or when the
render checks reported something for either gender.  `doubt` ranks rows
(higher = more doubtful) so the worst ones come first.
"""
import csv
import glob
import os
import sys


def main(work, outdir, dest):
    rows = list(csv.DictReader(open(work, encoding="utf-8")))
    qa = {}
    for f in glob.glob(os.path.join(outdir, "qa*.csv")):
        g = "f" if os.path.basename(f).startswith("qa.f") else "m"
        for r in csv.reader(open(f, encoding="utf-8")):
            if len(r) >= 6 and r[5]:
                qa.setdefault(r[0], {})[g] = r[5]
    out = []
    for r in rows:
        score = {"rule": 0, "approx": 2, "fallback": 4}.get(r["match"], 0)
        issues = qa.get(r["slug"], {})
        for txt in issues.values():
            for it in txt.split(";"):
                k, _, v = it.partition(":")
                try:
                    val = float(v)
                except ValueError:
                    val = 0.0
                if val > 0.05:
                    score += 1
        if score == 0 and not issues:
            continue
        out.append(dict(slug=r["slug"], name_en=r["name_en"], template=r["template"], match=r["match"],
                        note=r["note"], qa_male=issues.get("m", ""), qa_female=issues.get("f", ""), doubt=score))
    out.sort(key=lambda x: (-x["doubt"], x["slug"]))
    with open(dest, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["slug", "name_en", "template", "match", "note", "qa_male", "qa_female",
                                          "doubt"])
        w.writeheader()
        w.writerows(out)
    print(len(out), "rows ->", dest)


if __name__ == "__main__":
    main(*sys.argv[1:4])
