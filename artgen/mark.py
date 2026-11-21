"""The "© ProGym" mark and the copyright metadata.

The letters are drawn from stroke definitions in this file (no font files),
supersampled and downscaled, with a soft shadow, and placed in a bottom
corner where no frame of the animation has the athlete or equipment.
"""
import math

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

RIGHTS = "© ProGym. All rights reserved."
CREATOR = "ProGym"


def _arc(cx, cy, rx, ry, a0, a1, n=24):
    return [(cx + rx * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
             cy + ry * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]


# glyph: (advance width, list of polylines); units: cap height 1, baseline 0, y up
GLYPHS = {
    "©": (1.04, [_arc(0.5, 0.5, 0.5, 0.5, 0, 360, 40), _arc(0.5, 0.5, 0.23, 0.23, 45, 315, 24)]),
    " ": (0.34, []),
    "P": (0.66, [[(0, 0), (0, 1)], [(0, 1), (0.36, 1)] + _arc(0.36, 0.74, 0.26, 0.26, 90, -90, 18)[1:] + [(0, 0.48)]]),
    "r": (0.46, [[(0, 0), (0, 0.72)], _arc(0.34, 0.38, 0.34, 0.34, 180, 90, 12) + [(0.42, 0.72)]]),
    "o": (0.74, [_arc(0.36, 0.36, 0.33, 0.36, 0, 360, 32)]),
    "G": (1.02, [_arc(0.5, 0.5, 0.48, 0.5, 42, 360, 36) + [(0.6, 0.5)]]),
    "y": (0.7, [[(0, 0.72), (0.34, 0.06)], [(0.68, 0.72), (0.2, -0.28), (0.1, -0.28)]]),
    "m": (1.0, [[(0, 0), (0, 0.72)], [(0, 0.5)] + _arc(0.22, 0.5, 0.22, 0.22, 180, 0, 12) + [(0.44, 0)],
                [(0.44, 0.5)] + _arc(0.66, 0.5, 0.22, 0.22, 180, 0, 12) + [(0.88, 0)]]),
}
TEXT = "© ProGym"


def text_mask(cap_px, ss=6):
    """Alpha mask (L image) of TEXT with cap height cap_px."""
    s = cap_px * ss
    stroke = 0.15 * s
    gap = 0.08 * s
    width = sum(GLYPHS[ch][0] * s + gap for ch in TEXT) + 2 * stroke
    asc, desc = 1.0 * s, 0.32 * s
    W, H = int(width + 2 * stroke), int(asc + desc + 2 * stroke)
    im = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(im)
    x = stroke
    base = stroke + asc
    for ch in TEXT:
        adv, lines = GLYPHS[ch]
        sw = stroke * (0.7 if ch == "©" else 1.0)
        for pl in lines:
            pts = [(x + px * s, base - py * s) for px, py in pl]
            d.line(pts, fill=255, width=max(1, int(round(sw))), joint="curve")
            r = sw / 2
            for px_, py_ in (pts[0], pts[-1]):
                d.ellipse([px_ - r, py_ - r, px_ + r, py_ + r], fill=255)
        x += adv * s + gap
    out = im.resize((max(1, W // ss), max(1, H // ss)), Image.LANCZOS)
    return out


def corner(alpha_union, mw, mh, margin):
    """Pick the bottom corner (right first) whose box is free of the subject."""
    H, W = alpha_union.shape
    cands = [(W - mw - margin, H - mh - margin), (margin, H - mh - margin),
             (W - mw - margin, margin), (margin, margin)]
    best, best_v = cands[0], 1e9
    for x, y in cands:
        pad = 4
        box = alpha_union[max(0, y - pad):y + mh + pad, max(0, x - pad):x + mw + pad]
        v = float((box > 0.35).mean())
        if v < 0.002:
            return x, y
        if v < best_v:
            best, best_v = (x, y), v
    return best


def make_overlay(size, alpha_union, frac=0.035):
    """RGBA overlay (same for every frame): white text ~60 % with soft shadow."""
    W, H = size
    cap = max(7, int(round(H * frac)))
    m = text_mask(cap)
    mw, mh = m.size
    x, y = corner(alpha_union, mw, mh, margin=int(round(H * 0.03)))
    ov = Image.new("RGBA", size, (0, 0, 0, 0))
    sh = Image.new("L", size, 0)
    sh.paste(m, (x + 1, y + 1))
    sh = sh.filter(ImageFilter.GaussianBlur(0.9)).point(lambda v: int(min(255, v * 0.38)))
    ov.paste((70, 74, 82, 255), (0, 0), sh)
    txt = m.point(lambda v: int(v * 0.65))
    white = Image.new("RGBA", (mw, mh), (255, 255, 255, 255))
    lay = Image.new("RGBA", size, (0, 0, 0, 0))
    lay.paste(white, (x, y), txt)
    return Image.alpha_composite(ov, lay)


def exif_bytes():
    ex = Image.Exif()
    ex[0x013B] = CREATOR          # Artist
    ex[0x8298] = RIGHTS           # Copyright
    return ex.tobytes()


def xmp_bytes():
    x = ('<?xpacket begin="﻿" id="W5M0MpCehiHzreSzNTczkc9d"?>'
         '<x:xmpmeta xmlns:x="adobe:ns:meta/"><rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">'
         '<rdf:Description rdf:about="" xmlns:dc="http://purl.org/dc/elements/1.1/" '
         'xmlns:xmpRights="http://ns.adobe.com/xap/1.0/rights/">'
         f'<dc:rights><rdf:Alt><rdf:li xml:lang="x-default">{RIGHTS}</rdf:li></rdf:Alt></dc:rights>'
         f'<dc:creator><rdf:Seq><rdf:li>{CREATOR}</rdf:li></rdf:Seq></dc:creator>'
         '<xmpRights:Marked>True</xmpRights:Marked>'
         '</rdf:Description></rdf:RDF></x:xmpmeta><?xpacket end="w"?>')
    return x.encode("utf-8")
