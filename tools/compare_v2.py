"""Side-by-side sheet: v2 drawing (if any) vs v3 male, start / middle / end.

  python3 tools/compare_v2.py V2_DIST V3_OUT DEST_PREFIX key1,key2,...
"""
import os
import sys

from PIL import Image, ImageDraw


def v2_frames(path):
    im = Image.open(path)
    n = getattr(im, "n_frames", 1)
    out = []
    for i in (0, n // 4, n // 2):
        im.seek(i)
        out.append(im.convert("RGB").copy())
    return out


def main():
    v2, v3, dest, keys = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4].split(",")
    w, h = 240, 160
    per = 8
    for p in range(0, len(keys), per):
        chunk = keys[p:p + per]
        img = Image.new("RGB", (6 * w + 10, len(chunk) * (h + 16)), (255, 255, 255))
        d = ImageDraw.Draw(img)
        for j, k in enumerate(chunk):
            y = j * (h + 16)
            d.text((4, y + 2), f"{k}   [left: v2   |   right: v3]", fill=(0, 0, 0))
            p2 = os.path.join(v2, k + ".webp")
            if os.path.exists(p2):
                for i, fr in enumerate(v2_frames(p2)):
                    img.paste(fr.resize((w, h), Image.LANCZOS), (i * w, y + 16))
            else:
                d.text((20, y + 80), "v2: no drawing", fill=(160, 0, 0))
            for i in range(3):
                q = os.path.join(v3, "_sheet", f"{k}.{i}.png")
                if os.path.exists(q):
                    img.paste(Image.open(q).convert("RGB").resize((w, h), Image.LANCZOS), (3 * w + 10 + i * w, y + 16))
        out = f"{dest}-{p // per + 1}.png"
        img.save(out)
        print(out)


if __name__ == "__main__":
    main()
