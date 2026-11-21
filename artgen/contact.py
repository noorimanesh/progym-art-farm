"""Contact sheets: start / mid / end frames of animated WebPs, one row per
exercise (male and female side by side when both exist).

  python -m artgen.contact OUT_DIR SHEET.png [slug ...] [--cols-from webp]
"""
import os
import sys

from PIL import Image, ImageDraw


def frames_of(path, idx=(0, 3, 6)):
    im = Image.open(path)
    out = []
    for i in idx:
        im.seek(i)
        out.append(im.convert("RGB").copy())
    return out


def sheet(out_dir, dest, slugs, scale=0.5, label=True):
    cells = []
    for s in slugs:
        row = []
        for suf in ("", ".f"):
            p = os.path.join(out_dir, f"{s}{suf}.webp")
            if os.path.exists(p):
                row += frames_of(p)
        if row:
            cells.append((s, row))
    if not cells:
        return None
    w, h = int(480 * scale), int(320 * scale)
    ncol = max(len(r) for _, r in cells)
    img = Image.new("RGB", (ncol * w, len(cells) * (h + 14)), (255, 255, 255))
    d = ImageDraw.Draw(img)
    for j, (s, row) in enumerate(cells):
        y = j * (h + 14)
        d.text((4, y), s, fill=(0, 0, 0))
        for i, fr in enumerate(row):
            img.paste(fr.resize((w, h), Image.LANCZOS), (i * w, y + 14))
    img.save(dest)
    return dest


if __name__ == "__main__":
    out_dir, dest = sys.argv[1], sys.argv[2]
    slugs = sys.argv[3:]
    if not slugs:
        slugs = sorted({f.split(".")[0] for f in os.listdir(out_dir) if f.endswith(".webp")})
    print(sheet(out_dir, dest, slugs))
