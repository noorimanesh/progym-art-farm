"""Per-vertex paint for the body: skin, painted athletic clothing, shells
(shoe / hair regions) and the 22 soft muscle-highlight regions.

Everything is computed on the rest mesh from geometry + bone weights, so it
works for both body shapes.  Results are cached next to the body cache.
"""
import os

import numpy as np

from . import body_model

MUSCLES = [
    "upper_chest", "mid_chest", "lower_chest", "front_delts", "side_delts", "rear_delts",
    "biceps", "triceps", "forearms", "upper_back", "traps", "lats", "lower_back", "abs",
    "obliques", "glutes", "quads", "hamstrings", "adductors", "abductors", "calves", "neck",
]


def srgb(h):
    h = h.lstrip("#")
    c = np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)])
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


SKIN = srgb("#c99a80")
LIME = srgb("#d5ec5c")
STYLE = "v3"          # "v4": sportswear that covers more (t-shirt + shorts / t-shirt + leggings), cavity shading


def set_style(style):
    global STYLE
    STYLE = style


SKIN4 = srgb("#c08d72")       # a touch warmer and deeper than v3 (reads less plastic under the studio key)
PALETTE4 = {
    "m": dict(top=srgb("#33404f"), bottom=srgb("#1d2026"), shoe=srgb("#e4e6ea"), sole=srgb("#2e3136"),
              accent=srgb("#8a929c"), hair=srgb("#241912")),
    "f": dict(top=srgb("#3d4a5a"), bottom=srgb("#1d2026"), shoe=srgb("#e6e7ea"), sole=srgb("#2e3136"),
              accent=srgb("#9aa2ac"), hair=srgb("#33200f")),
}
PALETTE = {
    "m": dict(top=srgb("#2b2f36"), bottom=srgb("#1b1e24"), shoe=srgb("#d9dbde"), sole=srgb("#3a3d42"),
              hair=srgb("#2a1d16")),
    "f": dict(top=srgb("#30353d"), bottom=srgb("#1c1f25"), shoe=srgb("#dcdde0"), sole=srgb("#3a3d42"),
              hair=srgb("#3b2618")),
}


def vertex_normals(v, faces):
    fn = np.cross(v[faces[:, 2]] - v[faces[:, 0]], v[faces[:, 3]] - v[faces[:, 1]])
    n = np.zeros_like(v)
    for k in range(4):
        np.add.at(n, faces[:, k], fn)
    return n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)


def adjacency(faces, nv):
    e = np.concatenate([faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 3]], faces[:, [3, 0]]])
    e = np.concatenate([e, e[:, ::-1]])
    return e


def smooth(field, edges, nv, it=4, keep=0.5):
    f = field.astype(np.float64)
    deg = np.bincount(edges[:, 0], minlength=nv).astype(np.float64)
    deg[deg == 0] = 1
    for _ in range(it):
        acc = np.bincount(edges[:, 0], weights=f[edges[:, 1]], minlength=nv)
        f = keep * f + (1 - keep) * acc / deg
    return f


def ss(x, a, b):
    """smoothstep from a to b (a<b gives rising edge, a>b falling)."""
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def band(x, lo, hi, soft):
    return ss(x, lo - soft, lo + soft) * ss(x, hi + soft, hi - soft)


def compute(gender):
    d = body_model.load(gender)
    v = d["verts"].astype(np.float64)
    faces = d["faces"]
    W = d["W"]
    names = [str(n) for n in d["names"]]
    H = d["heads"]
    J = lambda b: H[names.index(b)]
    w = lambda *bs: sum(W[:, names.index(b)] for b in bs if b in names)
    nv = len(v)
    n = vertex_normals(v, faces)
    edges = adjacency(faces, nv)
    x, y, z = v[:, 0], v[:, 1], v[:, 2]
    ax = np.abs(x)
    nx, ny, nz = n[:, 0], n[:, 1], n[:, 2]
    nlat = nx * np.sign(x + 1e-9)          # + = pointing away from the midline
    S = body_model.PROFILES[gender]["height_m"] / 1.79

    z_sh = J("upperarm01.R")[2]
    x_sh = J("upperarm01.R")[0]
    z_neck = J("neck01")[2]
    z_clav = J("clavicle.R")[2]
    z_nip = d["tails"][names.index("breast.R")][2]
    z_waist = J("spine03")[2]
    z_hip = J("upperleg01.R")[2]
    z_knee = J("lowerleg01.R")[2]
    z_ank = J("foot.R")[2]

    arm_w = w("upperarm01.L", "upperarm01.R", "upperarm02.L", "upperarm02.R")
    fore_w = w("lowerarm01.L", "lowerarm01.R", "lowerarm02.L", "lowerarm02.R")
    hand_w = 1 - np.clip(1 - sum(W[:, i] for i, nm in enumerate(names)
                                 if nm.startswith(("wrist", "finger", "metacarpal"))), 0, 1)
    limb_arm = arm_w + fore_w + hand_w
    thigh_w = w("upperleg01.L", "upperleg01.R", "upperleg02.L", "upperleg02.R")
    shin_w = w("lowerleg01.L", "lowerleg01.R", "lowerleg02.L", "lowerleg02.R")
    foot_w = 1 - np.clip(1 - sum(W[:, i] for i, nm in enumerate(names)
                                 if nm.startswith(("foot", "toe"))), 0, 1)
    neck_w = w("neck01", "neck02", "neck03")
    head_w = 1 - np.clip(1 - sum(W[:, i] for i, nm in enumerate(names)
                                 if not nm.startswith(("spine", "neck", "clav", "shoulder", "upper", "lower",
                                                       "wrist", "finger", "metacarpal", "pelvis", "root",
                                                       "foot", "toe", "breast"))), 0, 1)
    torso = np.clip(1 - limb_arm - thigh_w * ss(z, z_hip - 0.02, z_hip - 0.12) - shin_w - foot_w - head_w, 0, 1)
    torso *= ss(ax, x_sh + 0.02, x_sh - 0.03)

    front = ss(ny, 0.05, 0.35)
    back = ss(ny, -0.05, -0.35)
    m = {}
    chest_lo, chest_hi = z_nip - 0.075 * S, z_clav - 0.015 * S
    chest = torso * front * band(z, chest_lo, chest_hi, 0.02) * ss(ax, x_sh * 0.95, x_sh * 0.7)
    span = chest_hi - chest_lo
    m["upper_chest"] = chest * ss(z, chest_lo + 0.5 * span, chest_lo + 0.68 * span)
    m["mid_chest"] = chest * band(z, chest_lo + 0.3 * span, chest_lo + 0.68 * span, 0.02)
    m["lower_chest"] = chest * ss(z, chest_lo + 0.5 * span, chest_lo + 0.3 * span)
    m["abs"] = torso * front * band(z, z_hip + 0.035 * S, chest_lo - 0.005, 0.02) * ss(ax, 0.095 * S, 0.065 * S)
    m["obliques"] = torso * band(z, z_hip + 0.06 * S, chest_lo + 0.02, 0.025) * ss(np.abs(nx), 0.3, 0.6) * ss(ny, -0.45, -0.1)
    m["traps"] = (1 - limb_arm) * band(z, z_sh - 0.02, z_neck + 0.07 * S, 0.02) * ss(ny, 0.25, -0.1) * \
        ss(ax, x_sh * 0.95, x_sh * 0.75) * (1 - head_w)
    m["upper_back"] = torso * back * band(z, z_nip - 0.03, z_sh - 0.01, 0.025) * ss(ax, 0.15 * S, 0.11 * S)
    m["lats"] = torso * ss(ny, 0.15, -0.15) * band(z, z_waist - 0.03, z_sh - 0.11 * S, 0.03) * ss(ax, 0.05, 0.09)
    m["lower_back"] = torso * back * band(z, z_hip + 0.03, z_waist + 0.06 * S, 0.025) * ss(ax, 0.1 * S, 0.07 * S)

    # deltoids: around each shoulder joint
    delt = np.zeros(nv)
    dvec = np.zeros_like(v)
    for sd in ("L", "R"):
        c = J(f"upperarm01.{sd}")
        dd = v - c
        dist = np.linalg.norm(dd, axis=1)
        side = (np.sign(x) == np.sign(c[0]))
        wgt = ss(dist, 0.125 * S, 0.085 * S) * side * ss(np.abs(x), np.abs(c[0]) - 0.04, np.abs(c[0]) - 0.01)
        wgt *= ss(z, c[2] - 0.17 * S, c[2] - 0.08 * S)
        delt = np.maximum(delt, wgt)
        dvec[side] = dd[side]
    dn = dvec / np.maximum(np.linalg.norm(dvec, axis=1, keepdims=True), 1e-9)
    m["front_delts"] = delt * ss(dn[:, 1], 0.15, 0.45)
    m["rear_delts"] = delt * ss(dn[:, 1], -0.15, -0.45)
    m["side_delts"] = delt * band(dn[:, 1], -0.25, 0.25, 0.15)

    # upper arm: anterior (biceps) vs posterior (triceps) relative to the
    # elbow-crease direction of the rest arm
    bic = np.zeros(nv)
    tri = np.zeros(nv)
    fore = np.zeros(nv)
    for sd in ("L", "R"):
        Sj, Ej, Wj = J(f"upperarm01.{sd}"), J(f"lowerarm01.{sd}"), J(f"wrist.{sd}")
        a = (Ej - Sj) / np.linalg.norm(Ej - Sj)
        fwd = (Wj - Ej) - a * np.dot(Wj - Ej, a)
        fwd /= np.linalg.norm(fwd)
        t = (v - Sj) @ a / np.linalg.norm(Ej - Sj)
        r = v - Sj - np.outer((v - Sj) @ a, a)
        r /= np.maximum(np.linalg.norm(r, axis=1, keepdims=True), 1e-9)
        cosf = r @ fwd
        sel = arm_w * (np.sign(x) == np.sign(Sj[0]))
        bic += sel * band(t, 0.3, 0.9, 0.08) * ss(cosf, 0.0, 0.45)
        tri += sel * band(t, 0.18, 0.92, 0.08) * ss(cosf, -0.1, -0.5)
        a2 = (Wj - Ej) / np.linalg.norm(Wj - Ej)
        t2 = (v - Ej) @ a2 / np.linalg.norm(Wj - Ej)
        fore += fore_w * (np.sign(x) == np.sign(Sj[0])) * band(t2, 0.04, 0.78, 0.07)
    m["biceps"], m["triceps"], m["forearms"] = bic, tri, fore

    m["glutes"] = (torso + thigh_w) * back * band(z, z_hip - 0.17 * S, z_hip + 0.075 * S, 0.025) * ss(ax, 0.0, 0.03)
    m["quads"] = thigh_w * ss(ny, -0.25, 0.15) * ss(nlat, -0.55, -0.3) * band(z, z_knee + 0.05 * S, z_hip - 0.07 * S, 0.03)
    m["hamstrings"] = thigh_w * ss(ny, -0.1, -0.4) * band(z, z_knee + 0.05 * S, z_hip - 0.16 * S, 0.03)
    m["adductors"] = thigh_w * ss(nlat, -0.25, -0.55) * band(z, z_knee + 0.16 * S, z_hip - 0.05 * S, 0.03)
    m["abductors"] = (torso + thigh_w) * ss(nlat, 0.35, 0.65) * band(z, z_hip - 0.1 * S, z_hip + 0.11 * S, 0.03)
    m["calves"] = shin_w * ss(ny, 0.1, -0.25) * band(z, z_ank + 0.12 * S, z_knee - 0.03, 0.03)
    m["neck"] = neck_w * (1 - head_w) * ss(z, z_clav + 0.0, z_clav + 0.04) * ss(ny, 0.5, 0.2) * 0 + \
        band(z, z_clav + 0.02 * S, z_neck + 0.09 * S, 0.015) * ss(ax, 0.075 * S, 0.05 * S) * (1 - limb_arm)

    for k in list(m):
        m[k] = np.clip(smooth(np.clip(m[k], 0, 1), edges, nv, it=6, keep=0.4), 0, 1)

    # ---------------------------------------------------------- clothing
    pal = PALETTE[gender]
    col = np.tile(SKIN if STYLE != "v4" else SKIN4, (nv, 1))
    skin = np.ones(nv)
    if gender == "m":
        top = torso * band(z, z_hip + 0.02 * S, z_neck, 0.006)
        neckline = ss(z, z_clav - 0.07 * S, z_clav - 0.05 * S) * ss(ax, 0.10 * S, 0.075 * S) * front
        armhole = ss(np.abs(x), x_sh - 0.09 * S, x_sh - 0.06 * S) * ss(z, z_sh - 0.17 * S, z_sh - 0.15 * S)
        top = top * (1 - neckline) * (1 - armhole) * ss(z, z_neck - 0.005, z_neck - 0.02)
        short_lo = z_knee + 0.15 * S
    else:
        band_lo = z_nip - 0.085 * S
        top = torso * band(z, band_lo, z_neck, 0.005)
        neckline = ss(z, z_clav - 0.1 * S, z_clav - 0.08 * S) * ss(ax, 0.085 * S, 0.06 * S) * front
        armhole = ss(np.abs(x), x_sh - 0.07 * S, x_sh - 0.045 * S) * ss(z, z_sh - 0.15 * S, z_sh - 0.13 * S)
        racer = back * ss(ax, 0.075 * S, 0.095 * S) * ss(z, z_nip - 0.02, z_nip + 0.0)
        top = top * (1 - neckline) * (1 - armhole) * (1 - racer) * ss(z, z_neck - 0.005, z_neck - 0.025)
        short_lo = z_knee + 0.2 * S
    if STYLE == "v4":
        # v4 sportswear: a fitted crew-neck t-shirt with short sleeves (both), shorts above the
        # knee (men) / full-length leggings (women); modest cut, the torso fully covered
        pal = PALETTE4[gender]
        sleeve = np.zeros(nv)
        for sd in ("L", "R"):
            Sj, Ej = J(f"upperarm01.{sd}"), J(f"lowerarm01.{sd}")
            a = (Ej - Sj) / np.linalg.norm(Ej - Sj)
            t = (v - Sj) @ a / np.linalg.norm(Ej - Sj)
            sleeve += arm_w * (np.sign(x) == np.sign(Sj[0])) * ss(t, 0.62 if gender == "m" else 0.66, 0.55)
        # crew neck: the shirt covers the shoulders and the base of the neck; only a round
        # neck opening (a little lower in front) is left
        r_hole = 0.068 * S
        hole_f = front * ss(ax, r_hole + 0.01 * S, r_hole) * ss(z, z_clav - 0.025 * S, z_clav - 0.008 * S)
        hole = np.maximum(hole_f, ss(ax, r_hole + 0.006 * S, r_hole - 0.004 * S) * ss(z, z_neck - 0.03 * S, z_neck - 0.012 * S))
        hole = np.maximum(hole, ss(z, z_neck + 0.005 * S, z_neck + 0.02 * S))
        top = np.clip(torso * ss(z, z_hip - 0.01 * S, z_hip + 0.03 * S) + sleeve * (1 - head_w), 0, 1) * (1 - hole)
        top = top * (1 - head_w)
        if gender == "m":
            short_lo = z_knee + 0.11 * S
        else:
            short_lo = z_ank + 0.03 * S         # leggings to the ankle
    top = ss(smooth(top, edges, nv, it=2, keep=0.5), 0.3, 0.7)
    shorts = ss(torso + thigh_w + (shin_w if (STYLE == "v4" and gender == "f") else 0), 0.2, 0.4) * \
        band(z, short_lo, z_hip + 0.075 * S, 0.004)
    shorts = ss(smooth(shorts, edges, nv, it=2, keep=0.5), 0.3, 0.7)
    col = col * (1 - top[:, None]) + pal["top"] * top[:, None]
    col = col * (1 - shorts[:, None]) + pal["bottom"] * shorts[:, None]
    skin = skin * (1 - top) * (1 - shorts)

    if STYLE == "v4" and "eye.R" in names:
        # face detail: eyebrows, eyes and lips (soft vertex colour, read at 600x400)
        fr = head_w * ss(ny, 0.25, 0.6)
        ezs = []
        for sd in ("L", "R"):
            e = J(f"eye.{sd}")
            dx = (x - e[0]) / (0.024 * S)
            brow = fr * np.exp(-dx ** 2 * 1.2) * band(z - (e[2] + 0.022 * S + 0.006 * S * np.exp(-dx ** 2)),
                                                      -0.0045 * S, 0.0045 * S, 0.002 * S) * (np.abs(dx) < 1.3)
            eye = fr * np.exp(-((x - e[0]) / (0.011 * S)) ** 2 - ((z - e[2]) / (0.0055 * S)) ** 2) * (y > e[1])
            col = col * (1 - 0.8 * brow[:, None]) + pal["hair"] * 0.8 * brow[:, None]
            col = col * (1 - 0.85 * eye[:, None]) + srgb("#2b211c") * 0.85 * eye[:, None]
            ezs.append(e[2])
        mz = np.mean(ezs) - 0.073 * S
        lip = fr * np.exp(-(x / (0.02 * S)) ** 4 - ((z - mz) / (0.0065 * S)) ** 2)
        col = col * (1 - 0.55 * lip[:, None]) + srgb("#a8645c") * 0.55 * lip[:, None]

    # shoe region (shell) and hair region (shell)
    shoe = (z < z_ank + 0.035 * S).astype(float)
    hs = J("head")
    scalp = head_w * (((z - (hs[2] + 0.05 * S)) + 0.6 * (-(y - hs[1])) * ss(y, hs[1] + 0.02, hs[1] - 0.04)) > 0)
    hairline_front = ss(y - hs[1], 0.075 * S, 0.06 * S)
    hair = (scalp * hairline_front) > 0.5
    hair = hair | ((head_w > 0.5) & (y < hs[1] - 0.035) & (z > hs[2] - 0.0))
    # cavity: concave skin folds (between muscles, at joints) shade a little darker
    lap = np.zeros_like(v)
    cnt = np.zeros(nv)
    np.add.at(lap, edges[:, 0], v[edges[:, 1]])
    np.add.at(lap, edges[:, 1], v[edges[:, 0]])
    np.add.at(cnt, edges[:, 0], 1)
    np.add.at(cnt, edges[:, 1], 1)
    lap = lap / np.maximum(cnt, 1)[:, None] - v
    cav = (lap * n).sum(1)                 # > 0: concave
    cav = smooth(cav, edges, nv, it=2, keep=0.5)
    sc = np.percentile(np.abs(cav), 95) + 1e-9
    cav = np.clip(cav / sc, -1, 1)
    return dict(col=col.astype(np.float32), skin=skin.astype(np.float32), muscles=m,
                shoe=shoe.astype(bool), hair=hair.astype(bool), normals=n, cav=cav.astype(np.float32))


def load(gender):
    path = os.path.join(body_model.CACHE, f"paint_{gender}.npz" if STYLE == "v3" else f"paint4_{gender}.npz")
    if not os.path.exists(path):
        r = compute(gender)
        np.savez_compressed(path, col=r["col"], skin=r["skin"], shoe=r["shoe"], hair=r["hair"], cav=r["cav"],
                            **{"mus_" + k: v.astype(np.float32) for k, v in r["muscles"].items()})
    d = np.load(path)
    return dict(col=d["col"], skin=d["skin"], shoe=d["shoe"], hair=d["hair"],
                cav=d["cav"] if "cav" in d.files else np.zeros(len(d["skin"]), np.float32),
                muscles={k: d["mus_" + k] for k in MUSCLES})
