"""Automatic checks on a solved v3 loop.

Contacts (millimetres)
  grip      posed grip / palm point vs. the requested contact point on the
            implement (bar, handle, dumbbell, floor, bench ...)
  foot      planted feet: sliding of the ball over the loop and the gap
            between the sole and the surface it stands on
  support   every body-support plane (bench pads, seats, floor, wall): gap
            between the body region and the surface (+ = floating,
            - = sinking in; pads may compress a few mm)
  floor     lowest body point below the floor
Motion
  pop       joint speed in phase space jumping between neighbouring steps
            (a limb snapping or the solver switching branch)
  twist     a hand / foot / head / forearm turning on its parent segment more than 50 degrees between two
            neighbouring unique poses
Ranges
  knee / elbow flexion beyond 160 degrees, elbow or knee bent the wrong way
"""
import math

import numpy as np

from .rig import SIDES, unit

JOINTS = ["wrist.L", "wrist.R", "lowerarm01.L", "lowerarm01.R", "lowerleg01.L", "lowerleg01.R",
          "foot.L", "foot.R", "head", "upperarm01.L", "upperarm01.R", "root"]
MIN_FRAME = 0.55      # athlete bounding box: share of the frame height (or width)
LIM = dict(grip=8.0, foot_slide=6.0, foot_gap_lo=-12.0, foot_gap_hi=10.0, support=9.0, floor=8.0)


def _grip_err(ctx, p):
    r = ctx.r
    worst, which = 0.0, ""
    for sd, A in p.info["spec"].get("arm", {}).items():
        for k in ("grip", "palm"):
            if k not in A:
                continue
            hr = r.hand_rest[sd]
            w = p.Hp[r.bi(f"wrist.{sd}")]
            g = w + p.D[r.bi(f"wrist.{sd}")] @ hr[k]
            e = float(np.linalg.norm(g - np.asarray(A[k])))
            if e > worst:
                worst, which = e, f"{k}{sd}"
    return worst * 1000, which


def _support_gaps(ctx, p):
    out = []
    for s in p.info.get("settle", []):
        kind = s[0]
        if kind == "floor":
            gap = s[1] if len(s) > 1 else -0.002
            out.append(("floor", (p.verts[:, 2].min() - gap) * 1000))
        elif kind == "floor_part":
            out.append(("floor_part", (p.verts[s[1], 2].min() - s[2]) * 1000))
        elif kind == "plane":
            _, p0, n, u, hu, w, hw, gap = s[:8]
            vm = ctx._region(s[8] if len(s) > 8 else "noarms")
            n, u, w = unit(n), unit(u), unit(w)
            rel = p.verts - p0
            m = (np.abs(rel @ u) < hu) & (np.abs(rel @ w) < hw) & (rel @ n > -0.25) & vm
            if not m.any():
                out.append(("plane", 999.0))
                continue
            out.append(("plane", ((rel[m] @ n).min() - gap) * 1000))
    return out


def _foot(ctx, poses):
    r = ctx.r
    res = {}
    planted = poses[0].info.get("planted", [])
    for sd in planted:
        if not all(sd in p.info.get("planted", []) for p in poses):
            continue
        balls, gaps = [], []
        m = ctx._foot_mask(sd)
        for p in poses:
            L = p.info["spec"]["leg"].get(sd, {})
            if "ball" not in L:
                continue
            surf = float(L.get("surf", float(L["ball"][2]) - 0.008))
            fp = r.bone_point(p.D, p.Hp, f"toe3-1.{sd}", r.foot_rest[sd]["ball"])   # floor contact under the ball
            balls.append(fp)
            # sole: lowest foot vertices (heel raised feet rest on the ball)
            # sole under the ball only: a heel may hang over a step edge
            near = m & (np.linalg.norm(p.verts[:, :2] - fp[:2], axis=1) < 0.07)
            gaps.append((p.verts[near if near.any() else m, 2].min() - 0.007 - surf) * 1000)   # shoe shell 7 mm
        if balls:
            B = np.array(balls)
            res[sd] = dict(slide=float(np.linalg.norm((B - B[0])[:, :2], axis=1).max() * 1000),
                           gap_min=float(min(gaps)), gap_max=float(max(gaps)))
    return res


def _rot_angle(A, B):
    R = A.T @ B
    c = max(-1.0, min(1.0, (np.trace(R) - 1) / 2))
    return math.degrees(math.acos(c))


def _motion(ctx, poses, tl):
    r = ctx.r
    src = [i for i, u in enumerate(tl.unique) if u[2] != "L"]
    src.sort(key=lambda i: tl.unique[i][1])
    ph = np.array([tl.unique[i][1] for i in src])
    P = np.array([[poses[i].Hp[r.bi(j)] for j in JOINTS] for i in src])  # (k, J, 3)
    pops = []
    if len(src) >= 4:
        d = np.linalg.norm(np.diff(P, axis=0), axis=2)          # (k-1, J)
        dph = np.maximum(np.diff(ph), 1e-6)[:, None]
        s = d / dph                                              # speed per unit phase
        smax = s.max(0) + 1e-6
        for k in range(1, len(s) - 1):
            for j in range(len(JOINTS)):
                neigh = max(s[k - 1, j], s[k + 1, j])
                if d[k, j] > 0.015 and s[k, j] > 1.8 * neigh + 0.1 * smax[j]:
                    pops.append(f"{JOINTS[j]}@{ph[k]:.2f}:{d[k, j] * 1000:.0f}mm")
    twists = []
    parent = {"wrist.L": "lowerarm02.L", "wrist.R": "lowerarm02.R", "foot.L": "lowerleg02.L",
              "foot.R": "lowerleg02.R", "head": "neck03", "lowerarm01.L": "upperarm02.L",
              "lowerarm01.R": "upperarm02.R"}
    for b in ("wrist.L", "wrist.R", "foot.L", "foot.R", "head", "lowerarm01.L", "lowerarm01.R"):
        bi, pi = r.bi(b), r.bi(parent[b])
        for a, c in zip(src[:-1], src[1:]):
            # rotation of the part relative to the segment it hangs on (a snap,
            # not a fast swing of the whole limb)
            ang = _rot_angle(poses[a].D[pi].T @ poses[a].D[bi], poses[c].D[pi].T @ poses[c].D[bi])
            if ang > 60:
                twists.append(f"{b}@{tl.unique[c][1]:.2f}:{ang:.0f}deg")
    return pops, twists


def _ranges(ctx, poses):
    r = ctx.r
    bad = []
    for p in poses:
        for sd in "LR":
            for a, b, c, nm in (("upperarm01", "lowerarm01", "wrist", "elbow"),
                                ("upperleg01", "lowerleg01", "foot", "knee")):
                A = p.Hp[r.bi(f"{a}.{sd}")]
                B = p.Hp[r.bi(f"{b}.{sd}")]
                C = p.Hp[r.bi(f"{c}.{sd}")]
                u, v = unit(B - A), unit(C - B)
                flex = math.degrees(math.acos(max(-1, min(1, float(u @ v)))))
                if flex > 165:
                    bad.append(f"{nm}{sd}:{flex:.0f}")
    return sorted(set(bad))


_GEO = {}


def _equip_zmin(e):
    """Lowest point of the actual geometry (not its bounding box)."""
    from . import equipment as EQ
    k = (e["kind"], repr(sorted((e.get("shape") or {}).items())))
    if k not in _GEO:
        g = EQ.KINDS[e["kind"]](**(e.get("shape") or {}))
        _GEO[k] = np.concatenate([np.concatenate(vs) for vs, fs, n in g.parts.values()]) if g.parts else np.zeros((1, 3))
    v = _GEO[k]
    M = np.asarray(e["M"])
    return float((v @ M[:3, :3].T + M[:3, 3])[:, 2].min())


def check(ctx, poses, tl, tpl, row):
    real = [p for p in poses if not p.info.get("mirrored")]
    issues = []
    g = [_grip_err(ctx, p) for p in real]
    grip = max(g, key=lambda x: x[0]) if g else (0.0, "")
    if grip[0] > LIM["grip"]:
        issues.append(f"grip:{grip[1]}:{grip[0]:.0f}mm")
    feet = _foot(ctx, real)
    for sd, f in feet.items():
        if f["slide"] > LIM["foot_slide"]:
            issues.append(f"foot_slide{sd}:{f['slide']:.0f}mm")
        if f["gap_min"] < LIM["foot_gap_lo"]:
            issues.append(f"foot_sink{sd}:{f['gap_min']:.0f}mm")
        if f["gap_max"] > LIM["foot_gap_hi"]:
            issues.append(f"foot_float{sd}:{f['gap_max']:.0f}mm")
    sup = []
    for p in real:
        sup.append(_support_gaps(ctx, p))
    worst_sup = 0.0
    for gl in sup:
        for kind, v in gl:
            if abs(v) > abs(worst_sup):
                worst_sup = v
    if abs(worst_sup) > LIM["support"]:
        issues.append(f"support:{worst_sup:+.0f}mm")
    zmin = min(p.verts[:, 2].min() for p in real) * 1000
    if zmin < -LIM["floor"] and not tpl.allow_below_floor:
        issues.append(f"floor:{zmin:.0f}mm")
    emin = 0.0
    for p in real:
        for e in p.equip:
            if e["kind"] == "_seg":
                continue
            emin = min(emin, _equip_zmin(e))
    if emin < -0.01:
        issues.append(f"equip_floor:{emin * 1000:.0f}mm")
    pops, twists = _motion(ctx, poses, tl)
    if pops and not getattr(tpl, "fast", False):
        issues.append("pop:" + ",".join(pops[:3]))
    if twists and not getattr(tpl, "fast", False):
        issues.append("twist:" + ",".join(twists[:3]))
    rng = _ranges(ctx, real)
    if rng:
        issues.append("range:" + ",".join(rng[:4]))
    return dict(issues=issues, grip_mm=round(grip[0], 1), feet=feet,
                support_mm=round(worst_sup, 1), floor_mm=round(zmin, 1), pops=pops, twists=twists, ranges=rng)
