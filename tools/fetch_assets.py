#!/usr/bin/env python3
"""Download the CC0 MakeHuman base assets used by the generator.

All files come from github.com/makehumancommunity/makehuman at a pinned commit
(see LICENSES.md).  They are cached under assets/mh/ which is not committed.
"""
import os
import sys
import urllib.request

COMMIT = "a8bc2d54ff0ac92e78ff71431b1023eda42bf482"
BASE = f"https://raw.githubusercontent.com/makehumancommunity/makehuman/{COMMIT}/makehuman/data/"

T = "targets/"
FILES = [
    "3dobjs/base.obj",
    "rigs/default.mhskel",
    "rigs/default_weights.mhw",
]
for g in ("male", "female"):
    for m in ("averagemuscle", "maxmuscle"):
        for w in ("minweight", "averageweight"):
            FILES.append(f"{T}macrodetails/universal-{g}-young-{m}-{w}.target")
            FILES.append(f"{T}macrodetails/proportions/{g}-young-{m}-{w}-idealproportions.target")
    for r in ("african", "asian", "caucasian"):
        FILES.append(f"{T}macrodetails/{r}-{g}-young.target")
FILES += [
    f"{T}torso/torso-vshape-incr.target",
    f"{T}torso/torso-muscle-pectoral-incr.target",
    f"{T}torso/torso-muscle-dorsi-incr.target",
    f"{T}stomach/stomach-pregnant-decr.target",
    f"{T}buttocks/buttocks-volume-incr.target",
    f"{T}bodyshapes/bodyshapes-elvs-man-invert-triangle.target",
    f"{T}bodyshapes/bodyshapes-elvs-fem-neat-hourglass.target",
]
for s in ("l", "r"):
    FILES += [
        f"{T}armslegs/{s}-upperarm-muscle-incr.target",
        f"{T}armslegs/{s}-upperarm-shoulder-muscle-incr.target",
        f"{T}armslegs/{s}-lowerarm-muscle-incr.target",
        f"{T}armslegs/{s}-upperleg-muscle-incr.target",
        f"{T}armslegs/{s}-lowerleg-muscle-incr.target",
    ]


def main(dest):
    for rel in FILES:
        out = os.path.join(dest, rel)
        if os.path.exists(out) and os.path.getsize(out) > 0:
            continue
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with urllib.request.urlopen(BASE + rel) as r:
            data = r.read()
        with open(out + ".part", "wb") as f:
            f.write(data)
        os.replace(out + ".part", out)
        print("fetched", rel, len(data))


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, "..", "assets", "mh"))
