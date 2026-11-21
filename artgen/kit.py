"""v3 set-up kits: cables with their attachments, bands with anchors,
machine lever arms, bench + rack.  Each returns a list of equipment entries
(E / H / seg) ready to append to a Frame's equipment.

Cable attachments (attach=)
  bar    straight bar, cable at its centre swivel
  lat    long lat bar with dropped ends
  rope   triceps rope: cable to a junction, two rope tails to the fists
  v      V / double-D close neutral handle
  d      single D handle per hand (sides "L", "R" or "LR" = one cable each)
  ankle  ankle cuff on the given leg
"""
import numpy as np

from .poses import E, H, seg
from .rig import X, Y, Z, SIDES, unit, orth
from .equipment import rz

CABLE_R = 0.0045


def tower_at(pulley, face):
    """Cable column whose pulley sits at `pulley`, the column facing the
    direction `face` (unit xy vector from the column toward the user)."""
    face = unit(np.array([face[0], face[1], 0.0]))
    ang = np.degrees(np.arctan2(-face[0], face[1]))   # local +Y -> face
    base = np.array([pulley[0], pulley[1], 0.0]) - face * 0.12
    return base, rz(ang)


def cable_kit(pulley, attach="bar", sides="C", face=None, eid="c", tower=True, pulleys=None):
    """pulley: xyz of the pulley wheel (or pulleys={'L': xyz, 'R': xyz} for
    two columns); face: direction from the column toward the user."""
    out = []
    pul = {"C": np.asarray(pulley, float)} if pulleys is None else {k: np.asarray(v, float) for k, v in pulleys.items()}
    if tower:
        for k, p in pul.items():
            f = face if face is not None else -np.array([p[0], p[1], 0.0])
            if np.linalg.norm(f[:2]) < 1e-6:
                f = np.array([0, -1.0, 0])
            base, R = tower_at(p, f)
            out.append(E("cable_tower", base, R=R, eid=f"tower{eid}{k}", pulley_h=float(p[2])))
    if attach in ("bar", "lat"):
        p = pul.get("C", next(iter(pul.values())))
        kind = "cable_bar" if attach == "bar" else "lat_bar"
        out.append(H(kind, "C", "bar", eid=f"{eid}bar"))
        out.append(seg(f"{eid}cable", p, "gripC", CABLE_R, "darksteel"))
    elif attach == "rope":
        p = pul.get("C", next(iter(pul.values())))

        def junction(pts, D, Hp, c, p=p):
            g = pts["gripC"]
            return g + unit(p - g) * 0.2
        out.append(seg(f"{eid}cable", p, junction, CABLE_R, "darksteel"))
        for sd in "LR":
            out.append(seg(f"{eid}rope{sd}", junction, f"grip{sd}", 0.012, "ropew"))
            out.append(H("rope_knob", sd, "db", eid=f"{eid}knob{sd}", off=(0, -0.045, 0)))
    elif attach == "v":
        p = pul.get("C", next(iter(pul.values())))
        out.append(dict(H("v_handle", "C", "aim", eid=f"{eid}v"), aim=p))
        out.append(seg(f"{eid}cable", p, ("toward", "gripC", 0.165), CABLE_R, "darksteel"))
    elif attach == "d":
        for sd in (["L", "R"] if sides in ("LR", "C") else [sides]):
            p = pul.get(sd, pul.get("C"))
            out.append(dict(H("d_handle", sd, "aim", eid=f"{eid}d{sd}"), aim=p))
            out.append(seg(f"{eid}cable{sd}", p, ("toward", f"grip{sd}", 0.135), CABLE_R, "darksteel"))
    elif attach == "ankle":
        sd = sides if sides in ("L", "R") else "R"
        p = pul.get(sd, pul.get("C"))
        out += ankle_cable(p, sd, eid)
    return out


def ankle_cable(p, sd, eid="c"):
    def ring(pts, D, Hp, c, sd=sd):
        r = c.r
        i = r.bi(f"lowerleg02.{sd}")
        a = r.joint(f"foot.{sd}") + np.array([0, 0, 0.07])
        return Hp[i] + D[i] @ (a - r.H[i])
    return [dict(kind="ankle_cuff", M=np.eye(4), id=f"{eid}cuff", shape={}, bone=f"lowerleg02.{sd}",
                 bone_pt=None, _ankle=sd),
            seg(f"{eid}cable", np.asarray(p, float), ring, CABLE_R, "darksteel")]


def band_kit(anchor, sides="LR", eid="b", post=True, door=False, ends=None):
    """Band from an anchor point to each hand (ends: grip names)."""
    out = []
    a = np.asarray(anchor, float)
    if post:
        out.append(E("band_anchor", (a[0], a[1] - 0.04, 0), eid=f"{eid}post", h=float(a[2])))
    if door:
        out.append(E("door_anchor", (a[0], a[1], 0), eid=f"{eid}door", h=float(a[2])))
    for sd in (ends or [f"grip{s}" for s in sides]):
        out.append(seg(f"{eid}{sd}", a, sd, 0.007, "band"))
    return out


def band_between_hands(eid="b"):
    """A loop band held between the hands (pull-aparts)."""
    return [seg(f"{eid}band", "gripL", "gripR", 0.008, "band"),
            seg(f"{eid}band2", ("gripL", (0, 0, -0.012)), ("gripR", (0, 0, -0.012)), 0.008, "band")]


def lever(pivot, sd, eid="lv", r=0.024, elbow=None):
    """Machine lever arm from a fixed pivot to the hand (optionally through
    an elbow point so the arm wraps around the body)."""
    p = np.asarray(pivot, float)
    if elbow is None:
        return [seg(f"{eid}{sd}", p, f"grip{sd}", r, "frame")]
    q = np.asarray(elbow, float)
    return [seg(f"{eid}{sd}a", p, q, r, "frame"), seg(f"{eid}{sd}b", q, f"grip{sd}", r, "frame")]


def bench_rack_for(kind, angle, by, c, hooks=None):
    """Bench-press uprights behind the head end of a flat / incline / decline bench."""
    if kind == "incline":
        y, h = by - 0.62, hooks or 1.35 * c.S
    elif kind == "decline":
        y, h = by - 0.72, hooks or 0.95 * c.S
    else:
        y, h = by - 0.72, hooks or 1.02 * c.S
    return E("bench_rack", (0, y, 0), eid="brack", hooks=h)
