"""Contact sheets for v3 renders: start / middle / end of each exercise,
male and female side by side, with the automatic QA results printed under
the name.

  python -m artgen.sheet3 OUT_DIR DEST_PREFIX [--keys k1,k2] [--per 6] [--scale 0.5]

Writes DEST_PREFIX-1.png, DEST_PREFIX-2.png, ... (`per` exercises a page).
"""
import argparse
import json
import os

from PIL import Image, ImageDraw

LABEL_H = 30


def cells(out_dir, key):
    row, notes = [], []
    for sfx, g in (("", "m"), (".f", "f")):
        ims = []
        for j in range(3):
            p = os.path.join(out_dir, "_sheet", f"{key}{sfx}.{j}.png")
            if os.path.exists(p):
                ims.append(Image.open(p).convert("RGB"))
        row += ims
        q = os.path.join(out_dir, "_qa", f"{key}{sfx}.json")
        if os.path.exists(q):
            d = json.load(open(q))
            iss = " ".join(d["issues"]) or "ok"
            notes.append(f"{g}: {d['bytes'] // 1024}KB {d['seconds']:.0f}s frame {d.get('athlete_frac', 0):.2f} "
                         f"thumb {d.get('thumb', '?')} grip {d['grip_mm']:.0f}mm support {d['support_mm']:+.0f}mm | {iss}")
    return row, notes


def build(out_dir, dest_prefix, keys, per=6, scale=0.5):
    pages = []
    for k0 in range(0, len(keys), per):
        chunk = []
        for key in keys[k0:k0 + per]:
            row, notes = cells(out_dir, key)
            if row:
                name = key
                q = os.path.join(out_dir, "_qa", f"{key}.json")
                if os.path.exists(q):
                    name = json.load(open(q)).get("name_en", key) + f"  [{json.load(open(q))['template']}]"
                chunk.append((name, notes, row))
        if not chunk:
            continue
        w, h = int(480 * scale), int(320 * scale)
        ncol = max(len(r) for _, _, r in chunk)
        img = Image.new("RGB", (ncol * w, len(chunk) * (h + LABEL_H)), (255, 255, 255))
        d = ImageDraw.Draw(img)
        for j, (name, notes, row) in enumerate(chunk):
            y = j * (h + LABEL_H)
            d.text((4, y + 1), name, fill=(0, 0, 0))
            d.text((4, y + 11), "   ".join(notes)[:260], fill=(150, 30, 30) if any("ok" != n.split("| ")[-1] for n in notes) else (40, 110, 40))
            for i, fr in enumerate(row):
                img.paste(fr.resize((w, h), Image.LANCZOS), (i * w, y + LABEL_H))
            for i in range(1, ncol):
                d.line([(i * w, y + LABEL_H), (i * w, y + LABEL_H + h)], fill=(255, 255, 255), width=1)
        dest = f"{dest_prefix}-{k0 // per + 1}.png"
        img.save(dest)
        pages.append(dest)
    return pages


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out_dir")
    ap.add_argument("dest_prefix")
    ap.add_argument("--keys", default="")
    ap.add_argument("--per", type=int, default=6)
    ap.add_argument("--scale", type=float, default=0.5)
    a = ap.parse_args()
    keys = [k for k in a.keys.split(",") if k] if a.keys else sorted(
        {f.rsplit(".", 2)[0].replace(".f", "") for f in os.listdir(os.path.join(a.out_dir, "_sheet"))})
    for p in build(a.out_dir, a.dest_prefix, keys, a.per, a.scale):
        print(p)


if __name__ == "__main__":
    main()
