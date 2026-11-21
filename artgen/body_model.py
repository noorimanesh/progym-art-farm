"""Athletic male / female body built from the CC0 MakeHuman base mesh.

Produces, per gender, a cached npz with:
  verts (N,3) rest positions in metres, Z up, character facing +Y, right = +X
  faces (F,4) quads of the body surface
  joints: bone head/tail positions, parents, weights (N, B) dense
The posing / skinning itself lives in rig.py (pure numpy).
"""
import json
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ASSETS = os.path.join(ROOT, "assets", "mh")
CACHE = os.path.join(ROOT, "work", "cache")

# macro settings (MakeHuman modifier scale 0..1)
PROFILES = {
    "m": dict(gender=1.0, muscle=0.88, weight=0.46, height_m=1.79,
              local={
                  "torso/torso-vshape-incr": 0.55,
                  "torso/torso-muscle-pectoral-incr": 0.45,
                  "torso/torso-muscle-dorsi-incr": 0.45,
                  "stomach/stomach-pregnant-decr": 0.6,
                  "bodyshapes/bodyshapes-elvs-man-invert-triangle": 0.35,
                  "armslegs/{s}-upperarm-muscle-incr": 0.45,
                  "armslegs/{s}-upperarm-shoulder-muscle-incr": 0.45,
                  "armslegs/{s}-lowerarm-muscle-incr": 0.3,
                  "armslegs/{s}-upperleg-muscle-incr": 0.35,
                  "armslegs/{s}-lowerleg-muscle-incr": 0.3,
              }),
    "f": dict(gender=0.0, muscle=0.72, weight=0.42, height_m=1.67,
              local={
                  "stomach/stomach-pregnant-decr": 0.6,
                  "buttocks/buttocks-volume-incr": 0.35,
                  "bodyshapes/bodyshapes-elvs-fem-neat-hourglass": 0.3,
                  "torso/torso-muscle-dorsi-incr": 0.2,
                  "armslegs/{s}-upperarm-shoulder-muscle-incr": 0.25,
                  "armslegs/{s}-upperarm-muscle-incr": 0.2,
                  "armslegs/{s}-upperleg-muscle-incr": 0.3,
                  "armslegs/{s}-lowerleg-muscle-incr": 0.25,
              }),
}


def _split(v):
    """MakeHuman 0..1 macro value -> weights of (min, average, max)."""
    if v < 0.5:
        return {"min": 1 - v / 0.5, "average": v / 0.5, "max": 0.0}
    return {"min": 0.0, "average": 1 - (v - 0.5) / 0.5, "max": (v - 0.5) / 0.5}


def load_obj(path):
    verts, faces, groups = [], [], {}
    g = None
    with open(path) as f:
        for line in f:
            if line.startswith("v "):
                verts.append([float(x) for x in line.split()[1:4]])
            elif line.startswith("g "):
                g = line.split()[1]
            elif line.startswith("f "):
                idx = [int(t.split("/")[0]) - 1 for t in line.split()[1:]]
                groups.setdefault(g, []).append(idx)
    return np.array(verts, dtype=np.float64), groups


def load_target(path, n):
    d = np.zeros((n, 3))
    with open(path) as f:
        for line in f:
            if not line.strip() or line.startswith("#"):
                continue
            p = line.split()
            d[int(p[0])] = [float(p[1]), float(p[2]), float(p[3])]
    return d


def build(gender):
    prof = PROFILES[gender]
    v, groups = load_obj(os.path.join(ASSETS, "3dobjs", "base.obj"))
    n = len(v)
    tg = os.path.join(ASSETS, "targets")
    gname = "male" if gender == "m" else "female"
    mw = _split(prof["muscle"])
    ww = _split(prof["weight"])
    # gender is 0 or 1 here, so only one gender's targets contribute
    for m in ("average", "max"):
        for w in ("min", "average"):
            k = mw[m] * ww[w]
            if k <= 0:
                continue
            v += k * load_target(os.path.join(tg, "macrodetails", f"universal-{gname}-young-{m}muscle-{w}weight.target"), n)
            v += k * load_target(os.path.join(tg, "macrodetails", "proportions",
                                              f"{gname}-young-{m}muscle-{w}weight-idealproportions.target"), n)
    for r in ("african", "asian", "caucasian"):
        v += (1 / 3) * load_target(os.path.join(tg, "macrodetails", f"{r}-{gname}-young.target"), n)
    for key, k in prof["local"].items():
        sides = ("l", "r") if "{s}" in key else (None,)
        for s in sides:
            rel = key.format(s=s) if s else key
            v += k * load_target(os.path.join(tg, rel + ".target"), n)

    # MakeHuman: Y up, decimetres, faces +Z, left side at +x.
    # Ours: Z up, metres, character faces +Y, its right side at +X (left = -X).
    v = np.stack([-v[:, 0], v[:, 2], v[:, 1]], axis=1) * 0.1
    body_faces = np.array(groups["body"], dtype=np.int64)
    body_idx = np.unique(body_faces)
    nb = int(body_idx.max()) + 1          # body vertices are the first block
    feet_z = v[:nb, 2].min()
    v[:, 2] -= feet_z
    height = v[:nb, 2].max()
    v *= prof["height_m"] / height
    cx = 0.5 * (v[:nb, 0].min() + v[:nb, 0].max())
    v[:, 0] -= cx
    # centre the feet (ankle region) on y=0
    low = v[:nb][v[:nb, 2] < 0.12]
    v[:, 1] -= 0.5 * (low[:, 1].min() + low[:, 1].max())

    skel = json.load(open(os.path.join(ASSETS, "rigs", "default.mhskel")))
    joints = {k: v[idx].mean(axis=0) for k, idx in skel["joints"].items()}
    names = list(skel["bones"].keys())
    # topological order
    order, seen = [], set()

    def visit(b):
        if b in seen:
            return
        p = skel["bones"][b]["parent"]
        if p:
            visit(p)
        seen.add(b)
        order.append(b)

    for b in names:
        visit(b)
    heads = np.array([joints[skel["bones"][b]["head"]] for b in order])
    tails = np.array([joints[skel["bones"][b]["tail"]] for b in order])
    parents = np.array([order.index(skel["bones"][b]["parent"]) if skel["bones"][b]["parent"] else -1
                        for b in order])

    wj = json.load(open(os.path.join(ASSETS, "rigs", "default_weights.mhw")))["weights"]
    W = np.zeros((nb, len(order)), dtype=np.float32)
    for b, lst in wj.items():
        if b not in order:
            continue
        j = order.index(b)
        for vi, w in lst:
            if vi < nb:
                W[vi, j] += w
    s = W.sum(axis=1, keepdims=True)
    s[s == 0] = 1
    W /= s

    os.makedirs(CACHE, exist_ok=True)
    out = os.path.join(CACHE, f"body_{gender}.npz")
    np.savez_compressed(out, verts=v[:nb].astype(np.float32), faces=body_faces,
                        heads=heads, tails=tails, parents=parents,
                        names=np.array(order), W=W)
    return out


def load(gender):
    path = os.path.join(CACHE, f"body_{gender}.npz")
    if not os.path.exists(path):
        build(gender)
    d = np.load(path, allow_pickle=False)
    return {k: d[k] for k in d.files}


if __name__ == "__main__":
    for g in ("m", "f"):
        p = build(g)
        d = load(g)
        v = d["verts"]
        print(g, p, v.shape, d["faces"].shape, "bbox", v.min(0).round(3), v.max(0).round(3))
        nm = list(d["names"])
        for b in ("root", "spine05", "spine01", "neck01", "head", "upperarm01.L", "lowerarm01.L", "wrist.L",
                  "upperleg01.L", "lowerleg01.L", "foot.L", "toe3-1.L", "finger3-1.L"):
            i = nm.index(b)
            print("  ", b, d["heads"][i].round(3), d["tails"][i].round(3))
