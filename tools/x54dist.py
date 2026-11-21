"""x54dist.py OLD_MANIFEST OUT_DIR: the 5.4 drawings that are finished (all four files in out_x54) copied to
OUT_DIR with the full manifest (the old one plus the new names)."""
import csv, json, os, shutil, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
old, out = sys.argv[1], sys.argv[2]
SUF = (".webp", ".f.webp", ".thumb.webp", ".f.thumb.webp")
m = json.load(open(old, encoding="utf-8"))
mv = {r["key"]: r for r in csv.DictReader(open(os.path.join(ROOT, "data/v3/moves.csv"), encoding="utf-8"))}
keys = [r["key"] for r in csv.DictReader(open(os.path.join(ROOT, "data/v5/x54.csv"), encoding="utf-8"))]
os.makedirs(out, exist_ok=True)
done, missing = [], []
for k in keys:
    src = [os.path.join(ROOT, "out_x54", k + s) for s in SUF]
    if not all(os.path.isfile(p) for p in src):
        missing.append(k)
        continue
    for p in src:
        shutil.copy2(p, out)
    m["names"][mv[k]["name_en"]] = k
    done.append(k)
json.dump(m, open(os.path.join(out, "manifest.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print(len(done), "new pictures;", len(m["names"]), "names in the manifest")
if missing:
    print("not finished:", " ".join(missing))
