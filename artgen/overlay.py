"""Implements the spec names but an archetype does not draw itself: added to
a solved pose from the body's posed joints, so they touch the body exactly.

  mini band (knees / ankles / wrists / feet / thighs)  loop around both limbs
  suspension straps                                    anchor overhead, straps to the hands (or feet)
  band low / mid / high / under feet                   band from its anchor to the hands
  cable low / mid / high                               column + cable to the hands
  Smith machine                                        guided frame around a held barbell
  one dumbbell / kettlebell                            drop the left one when the spec holds a single bell
"""
import numpy as np

from .rig import unit
from .equipment import Mx, rz


def _seg(eid, p0, p1, r, mat):
    return dict(kind="_seg", id=eid, p0=np.asarray(p0, float), p1=np.asarray(p1, float), r=r, mat=mat)


def _has(eq, pred):
    return any(pred(e) for e in eq)


def _grip(ctx, p, sd):
    return ctx.grip_frame(p.D, p.Hp, sd)[0]


def _J(ctx, p, name):
    return p.Hp[ctx.r.bi(name)]


def mini_band(ctx, p, where):
    r = ctx.r
    leg_ax = None
    if where == "ankles":
        a, b = _J(ctx, p, "foot.L") + np.array([0, 0, 0.05]), _J(ctx, p, "foot.R") + np.array([0, 0, 0.05])
        shin = unit(_J(ctx, p, "lowerleg01.L") - _J(ctx, p, "foot.L") + _J(ctx, p, "lowerleg01.R") - _J(ctx, p, "foot.R"))
        if shin[2] < 0.8:
            # lying / legs not upright: the loop sits up the shins from the ankles, not above them
            a = _J(ctx, p, "foot.L") + unit(_J(ctx, p, "lowerleg01.L") - _J(ctx, p, "foot.L")) * 0.06
            b = _J(ctx, p, "foot.R") + unit(_J(ctx, p, "lowerleg01.R") - _J(ctx, p, "foot.R")) * 0.06
            leg_ax = shin
    elif where == "wrists":
        a, b = _J(ctx, p, "wrist.L"), _J(ctx, p, "wrist.R")
    elif where == "feet":
        a = 0.5 * (_J(ctx, p, "foot.L") + _J(ctx, p, "toe3-1.L"))
        b = 0.5 * (_J(ctx, p, "foot.R") + _J(ctx, p, "toe3-1.R"))
    elif where == "thighs":
        a = 0.5 * (_J(ctx, p, "upperleg02.L") + _J(ctx, p, "lowerleg01.L"))
        b = 0.5 * (_J(ctx, p, "upperleg02.R") + _J(ctx, p, "lowerleg01.R"))
    else:   # just above the knees
        a = _J(ctx, p, "lowerleg01.L") * 0.85 + _J(ctx, p, "upperleg02.L") * 0.15
        b = _J(ctx, p, "lowerleg01.R") * 0.85 + _J(ctx, p, "upperleg02.R") * 0.15
    ax = unit(b - a)
    # the loop wraps the outside of both limbs: two strands, front and back
    up = np.array([0, 0, 1.0]) if abs(ax[2]) < 0.9 else np.array([0, 1.0, 0])
    if leg_ax is not None and np.linalg.norm(np.cross(leg_ax, ax)) > 0.3:
        up = leg_ax           # strands in front of / behind the legs, across the leg line
    fwd = unit(np.cross(up, ax))
    out = []
    rr = 0.055
    for k, s in (("f", 1), ("b", -1)):
        out.append(_seg(f"mb{k}", a + fwd * s * rr - ax * 0.05, b + fwd * s * rr + ax * 0.05, 0.007, "band"))
    return out


def apply(ctx, pose, row):
    w = (row.get("equipment") or "").lower()
    name = (row.get("name_en") or "").lower()
    eq = pose.equip
    add = []
    segs = [e for e in eq if e["kind"] == "_seg"]
    # ---- mini bands
    if "mini band" in w or "mini_band" in w or "mini band" in name:
        where = "knees"
        for k in ("ankles", "wrists", "feet", "thigh"):
            if k in w:
                where = "thighs" if k == "thigh" else k
                break
        # a mini band is a small loop: drop long bands / band posts an archetype drew for "band"
        eq = [e for e in eq if not (e["kind"] == "band_anchor" or
                                    (e["kind"] == "_seg" and e.get("mat") == "band" and not e["id"].startswith("mb")))]
        pose.equip = eq
        segs = [e for e in eq if e["kind"] == "_seg"]
        if not _has(eq, lambda e: e["id"].startswith("mb")):
            add += mini_band(ctx, pose, where)
    # ---- suspension straps
    if ("suspension" in w or "trx" in w) and not _has(eq, lambda e: e.get("mat") == "strap" or e["kind"] == "trx_anchor"):
        feet = any(k in w for k in ("straps (feet", "straps (toes", "(toes)", "straps (shins", "strap (rear foot",
                                    "+ straps (feet", "feet in straps", "cradle"))
        if row.get("template") in ("pike", "push_up", "mountain_climber", "plank", "side_plank") and \
                not any(k in w for k in ("floor (feet)", "straps (hands)", "standing", "on handles")):
            feet = True        # prone / side planks on straps: the feet are in the cradles
        pts = []
        if feet:
            for sd in "LR":
                pts.append(_J(ctx, pose, f"foot.{sd}") + np.array([0, 0, 0.02]))
        else:
            for sd in "LR":
                pts.append(_grip(ctx, pose, sd))
        c = np.mean(pts, axis=0)
        anchor = np.array([c[0], c[1] + (0.0 if feet else 0.0), 2.45])
        if not feet and c[2] < 1.6:
            # straps lean toward the anchor in front / behind of the body's line
            anchor = np.array([c[0], c[1], 2.45])
        add.append(dict(kind="trx_anchor", M=Mx(anchor * np.array([1, 1, 0])), id="ov_trx", shape=dict(h=2.45)))
        for i, q in enumerate(pts):
            add.append(_seg(f"ov_strap{i}", anchor, q, 0.012, "strap"))
    # ---- assistance band looped on a pull-up bar under the knees
    has_band = _has(segs, lambda e: e.get("mat") == "band")
    if row.get("template") == "pull_up" and "band" in w and not has_band:
        bar = np.mean([_grip(ctx, pose, sd) for sd in "LR"], axis=0)
        kn = np.mean([_J(ctx, pose, f"lowerleg01.{sd}") for sd in "LR"], axis=0) + np.array([0, -0.06, -0.03])
        add.append(_seg("ov_bandA", bar + np.array([-0.04, 0, 0]), kn + np.array([-0.06, 0, 0]), 0.008, "band"))
        add.append(_seg("ov_bandB", bar + np.array([0.04, 0, 0]), kn + np.array([0.06, 0, 0]), 0.008, "band"))
        add.append(_seg("ov_bandC", kn + np.array([-0.07, 0, 0]), kn + np.array([0.07, 0, 0]), 0.008, "band"))
        has_band = True
    # ---- band looped around the ankles and the seat's rear leg (seated leg extension)
    if row.get("template") == "leg_extension" and "band" in w and not has_band:
        for sd in "LR":
            a = _J(ctx, pose, f"foot.{sd}") + np.array([0, 0.02, 0.03])
            add.append(_seg(f"ov_lext{sd}", np.array([a[0] * 0.6, -0.5, 0.06]), a, 0.007, "band"))
        has_band = True
    # ---- long bands with an anchor or under the feet
    has_strap = _has(segs, lambda e: e.get("mat") == "strap")
    if not has_band and not has_strap and ("band" in w and "mini band" not in w):
        grips = [_grip(ctx, pose, sd) for sd in "LR"]
        if "under feet" in w or "band_feet" in w or "band under" in w:
            for i, sd in enumerate("LR"):
                foot = 0.5 * (_J(ctx, pose, f"foot.{sd}") + _J(ctx, pose, f"toe3-1.{sd}"))
                foot[2] = 0.012
                add.append(_seg(f"ov_band{sd}", foot, grips[i], 0.007, "band"))
        else:
            z = 0.25 if "band_low" in w or "band low" in w else (2.0 if "band_high" in w or "band high" in w else 1.15)
            behind = "behind" in w
            c = np.mean(grips, axis=0)
            anchor = np.array([0.0, c[1] + (-0.9 if behind else 0.9), z])
            add.append(dict(kind="band_anchor", M=Mx(anchor * np.array([1, 1, 0]) + np.array([0, 0.04 if not behind else -0.04, 0])),
                            id="ov_post", shape=dict(h=z)))
            one_arm = any(k in name for k in ("single-arm", "one-arm", "single arm", "one arm"))
            for i, sd in enumerate("LR"):
                if one_arm and sd == "L":
                    continue
                add.append(_seg(f"ov_band{sd}", anchor, grips[i], 0.007, "band"))
    # ---- cable to an ankle cuff (kickbacks, abductions, knee drives)
    if ("ankle strap" in w or "ankle_strap" in w) and not _has(eq, lambda e: e["kind"] == "ankle_cuff"):
        r = ctx.r
        sd = "R"
        i = r.bi(f"lowerleg02.{sd}")
        bp = r.joint(f"foot.{sd}") + np.array([0, 0, 0.07])
        ring = pose.Hp[i] + pose.D[i] @ (bp - r.H[i])
        M = np.eye(4)
        M[:3, :3] = pose.D[i]
        M[:3, 3] = ring
        add.append(dict(kind="ankle_cuff", M=M, id="ov_cuff", shape={}))
        name_l = name
        if "kickback" in name_l or "extension" in name_l:
            pul = np.array([ring[0], ring[1] + 0.9, 0.15])            # pulley in front, leg pulls back
        elif "abduction" in name_l:
            pul = np.array([ring[0] - 1.0, ring[1], 0.15])           # pulley on the other side
        elif "adduction" in name_l:
            pul = np.array([ring[0] + 1.0, ring[1], 0.15])
        else:
            pul = np.array([ring[0], ring[1] - 0.9, 0.15])           # knee drive: pulley behind
        f = unit(np.array([ring[0] - pul[0], ring[1] - pul[1], 0]))
        ang = np.degrees(np.arctan2(-f[0], f[1]))
        add.append(dict(kind="cable_tower", M=Mx(pul * np.array([1, 1, 0]) - f * 0.12, rz(ang)), id="ov_ctower",
                        shape=dict(pulley_h=0.15)))
        add.append(_seg("ov_acable", pul, ring + np.array([0, 0, -0.0]), 0.0045, "darksteel"))
        w = w.replace("cable", "")      # handled
    # ---- cables
    if "cable" in w and not _has(segs, lambda e: e.get("mat") == "darksteel") and \
            not _has(eq, lambda e: e["kind"] in ("cable_tower", "lat_station", "row_station")):
        z = 0.15 if "low" in w else (2.1 if "high" in w else 1.2)
        grips = [_grip(ctx, pose, sd) for sd in "LR"]
        c = np.mean(grips, axis=0)
        one = "one_side" in w or "single" in w or "one-arm" in name or "single-arm" in name
        pul = np.array([0.0, c[1] + 0.95, z])
        add.append(dict(kind="cable_tower", M=Mx(np.array([0, pul[1] + 0.12, 0]), rz(180)), id="ov_tower",
                        shape=dict(pulley_h=z)))
        add.append(_seg("ov_cable", pul, grips[1] if one else c, 0.0045, "darksteel"))
    # ---- Smith machine
    if ("smith" in w or "smith" in name) and not _has(eq, lambda e: e["kind"] == "smith"):
        bar = [e for e in eq if e["kind"] in ("barbell", "smith_bar")]
        if bar:
            b = bar[0]["M"][:3, 3]
            bar[0]["kind"] = "smith_bar"
            add.append(dict(kind="smith", M=Mx(np.array([0, b[1], 0])), id="ov_smith", shape={}))
    # ---- one bell instead of two
    single = ("dumbbell single" in w or "kettlebell single" in w) and "both hands" not in w
    if single:
        held = [e for e in eq if e.get("hand") in ("L", "R") and e["kind"] in ("dumbbell", "kettlebell")]
        if len(held) == 2:
            pose.equip = [e for e in eq if not (e.get("hand") == "L" and e["kind"] in ("dumbbell", "kettlebell"))]
    pose.equip = pose.equip + add
    return pose
