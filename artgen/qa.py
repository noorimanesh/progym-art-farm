"""Automatic contact / anatomy checks on solved poses (reported in qa csv)."""
import numpy as np


def check(ctx, poses, tpl):
    r = ctx.r
    issues = []
    zmin = min(p.verts[:, 2].min() for p in poses)
    if zmin < -0.012 and not tpl.allow_below_floor:
        issues.append(f"floor_pen:{-zmin:.3f}")
    ik = max(p.info.get("ik_err", 0) for p in poses)
    if ik > 0.012:
        issues.append(f"reach:{ik:.3f}")
    # planted feet must not slide
    planted = poses[0].info.get("planted", [])
    for sd in planted:
        if not all(sd in p.info.get("planted", []) for p in poses):
            continue
        pts = [r.bone_point(p.D, p.Hp, f"toe3-1.{sd}", r.joint(f"toe3-1.{sd}")) for p in poses]
        d = max(np.linalg.norm(a - pts[0]) for a in pts)
        if d > 0.012:
            issues.append(f"foot_slide_{sd}:{d:.3f}")
    # grips: posed grip point vs requested
    worst = 0.0
    for p in poses:
        arms = p.info["spec"].get("arm", {})
        for sd, A in arms.items():
            if "grip" not in A:
                continue
            hr = r.hand_rest[sd]
            w = p.Hp[r.bi(f"wrist.{sd}")]
            g = w + p.D[r.bi(f"wrist.{sd}")] @ hr["grip"]
            worst = max(worst, np.linalg.norm(g - np.asarray(A["grip"])))
    if worst > 0.015:
        issues.append(f"grip_off:{worst:.3f}")
    # equipment below the floor
    from .render import equip_points
    emin = 0.0
    for p in poses:
        for e in p.equip:
            if e["kind"] in ("_seg",):
                continue
            emin = min(emin, equip_points(e)[:, 2].min())
    if emin < -0.01:
        issues.append(f"equip_floor:{-emin:.3f}")
    return issues
