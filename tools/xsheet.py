"""xsheet.py OUT DEST.jpg key1,key2,... [sfx]: start / middle / end frames of each key in rows, labelled."""
import os, sys
from PIL import Image, ImageDraw
out, dest, keys = sys.argv[1], sys.argv[2], [k for k in sys.argv[3].split(",") if k]
sfx = sys.argv[4] if len(sys.argv) > 4 else ""
N = int(os.environ.get("ARTGEN_PREV_N") or 3)
W, H = (240, 160) if N <= 3 else (160, 107)
sheet = Image.new("RGB", (W * N + 10, (H + 16) * len(keys)), "white")
d = ImageDraw.Draw(sheet)
for i, k in enumerate(keys):
    y = i * (H + 16)
    d.text((4, y + 2), k + sfx, fill="black")
    for j in range(N):
        p = os.path.join(out, "_sheet", f"{k}{sfx}.{j}.png")
        if os.path.exists(p):
            im = Image.open(p).convert("RGB"); im.thumbnail((W, H))
            sheet.paste(im, (j * W, y + 14))
sheet.save(dest, quality=82)
print(dest)
