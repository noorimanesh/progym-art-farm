"""Movement template registry.

A template is a function (c, t, L, row) -> Frame, where t is the eased phase
0..1 (start pose at 0, end pose at 1) and L(a, b) interpolates any value
between its start and end.  The families live in poses.py.
"""
import math

import numpy as np

from .poses import E, H, seg, frame3, SOLE, PAD_SINK
from .rig import X, Y, Z, SIDES, unit, orth, rot
from .equipment import PLATE_R, rx, ry, rz

REG = {}
VIEWS = {"side": (90, 7), "side_hi": (90, 16), "3q": (42, 9), "3q_hi": (40, 18), "front": (6, 6),
         "back3q": (140, 10), "front3q": (20, 8), "side_l": (-90, 8), "top": (70, 35)}


class Tpl:
    def __init__(self, name, fn, view="side", lens=55, linear=False, below=False, doc="", fast=False):
        self.name, self.fn, self.view, self.lens = name, fn, view, lens
        self.fast = fast      # explosive move: fast limb whips are expected (QA reports them as info)
        self.linear = linear
        self.allow_below_floor = below
        self.doc = doc

    def view_angles(self):
        return VIEWS[self.view] if isinstance(self.view, str) else self.view

    def pose(self, ctx, t, row, warm=None):
        def L(a, b):
            if isinstance(a, (tuple, list)):
                return tuple(np.asarray(a, float) * (1 - t) + np.asarray(b, float) * t)
            return a * (1 - t) + b * t
        row = row or {}
        fr = self.fn(ctx, t, L, row)
        fr = _raise_on_dome(ctx, fr, row)
        ctx.r.sec_offsets = _secondary(t, row, self.fast) if SECONDARY else None
        hold = row.get("_freeze")      # "L": that arm stays in its start pose (one-arm / alternating reps)
        if hold and t > 1e-6:
            fr0 = self.fn(ctx, 0.0, lambda a, b: tuple(a) if isinstance(a, (tuple, list)) else a, row)
            fr = _freeze_side(fr, fr0, hold)
        pose = ctx.run(fr, warm=warm)
        from . import overlay
        pose = overlay.apply(ctx, pose, row)
        # implement named in the exercise wins over the template's default bar
        name = (row or {}).get("name_en", "").lower()
        words0 = ((row or {}).get("equipment") or "").lower().split(";")[0]
        sub = "pvc" if "pvc" in name or "dowel" in name or words0.strip().startswith(("pvc", "dowel")) else ("ezbar" if "ez" in name.replace("-", " ").split() or "ez-bar" in name
                                                              or words0.strip().startswith("ez bar") else None)
        if sub:
            for e in pose.equip:
                if e["kind"] in ("barbell", "smith_bar") and "pivot" not in e:
                    e["kind"] = sub
                    e["shape"] = {}
        return pose


DOME_H = 0.21
SECONDARY = False       # v4: small secondary motion (head follow, breathing, torso counter-move)


def _secondary(t, row, fast):
    """Small secondary motion layered on any archetype (v4), returned as
    (spine, neck) angle offsets the rig adds to every solve of this pose (so the
    torso, the holds and the arm targets all see the same body):
    - the head follows the movement: the neck eases a few degrees with the effort
      (most at the middle of the rep) instead of staying locked to the spine;
    - holds breathe: a slow chest rise and fall (spine extension) over the loop;
    - a slight torso counter-move: the upper spine leans a touch against the
      direction of the rep (largest mid-rep, zero at the key poses).
    Offsets are a few degrees; arms and legs are re-solved to their contacts."""
    kind = ((row or {}).get("_tempo") or {}).get("kind", "rep")
    s = math.sin(math.pi * min(max(t, 0.0), 1.0))
    if kind == "hold":
        return (-1.6 * s, 0.0, 0.0), (-1.0 * s, 0.0, 0.0)          # breathing
    if kind == "cycle" or fast:
        ph = 2 * math.pi * t
        return ((0.8 * math.sin(ph), 0.0, 0.6 * math.sin(ph + 0.6)),
                (-1.2 * math.sin(ph - 0.5), 0.0, -0.8 * math.sin(ph + 0.6)))   # head lags the trunk
    return (1.2 * s, 0.0, 0.0), (-2.4 * s, 0.0, 0.0)               # counter-move, head follows


def _raise_on_dome(ctx, fr, row):
    """Spec puts the feet on a balance trainer the archetype does not draw:
    lift the planted feet and the body onto a dome (exact foot contact)."""
    w = (row.get("equipment") or "").lower()
    if not ("bosu" in w or "balance trainer" in w or "balance_trainer" in w):
        return fr
    if not fr.planted or any(k in w for k in ("bosu (hands", "bosu (lower back", "bosu (seated", "(flat side)",
                                                 "plank", "(lifted", "dome down")):
        return fr
    b = fr.build
    state = {}

    def build():
        ctx.adj = ctx.adj + np.array([0, 0, DOME_H])
        try:
            spec, eq, ex = b()
        finally:
            ctx.adj = ctx.adj - np.array([0, 0, DOME_H])
        if any(e["kind"] == "bosu" for e in eq):
            return spec, eq, ex
        pts = []
        for sd, L in spec.get("leg", {}).items():
            if "ball" in L and sd in fr.planted:
                L["ball"] = np.asarray(L["ball"], float) + np.array([0, 0, DOME_H])
                L["surf"] = L.get("surf", 0.0) + DOME_H
                pts.append(L["ball"])
        if pts:
            m = np.mean(pts, axis=0)
            eq = list(eq) + [E("bosu", (m[0], m[1] - 0.06, 0), eid="bosu")]
        return spec, eq, ex
    fr.build = build
    return fr


def _freeze_side(fr, fr0, sd):
    """Frame whose arm on side sd (and what that hand holds) comes from fr0."""
    b, b0 = fr.build, fr0.build

    def build():
        spec, eq, ex = b()
        spec0, eq0, ex0 = b0()
        if sd in spec0.get("arm", {}):
            spec.setdefault("arm", {})[sd] = spec0["arm"][sd]
        eq = [e for e in eq if e.get("hand") != sd] + [e for e in eq0 if e.get("hand") == sd]
        return spec, eq, ex
    fr.build = build
    return fr


def tpl(name, view="side", **kw):
    def deco(fn):
        REG[name] = Tpl(name, fn, view, **kw)
        return fn
    return deco


def get(name):
    if name not in REG:
        raise KeyError(f"unknown template {name}")
    return REG[name]


# ------------------------------------------------------------------ helpers
def fk(v, elbow=10, thumb="fwd", bend=(0, 1, 0), curl=0.3, bone="spine01", fing=None):
    """FK arm in body frame for the right arm (x out, y fwd, z up); mirrored
    for the left.  Returns {side: callable}."""
    def mk(sd):
        def f(D, Hp, c):
            a = dict(ua=c.arm_dir(D, v, sd, bone), elbow=elbow, bend=c.arm_dir(D, bend, sd, bone),
                     thumb=thumb if isinstance(thumb, str) else c.arm_dir(D, thumb, sd, bone), curl=curl)
            if fing is not None:
                a["fing"] = c.arm_dir(D, fing, sd, bone)
            return a
        return f
    return {"L": mk("L"), "R": mk("R")}


def one(arms, sd):
    return {sd: arms[sd]}


def both(a, b=None):
    out = dict(a)
    if b:
        out.update(b)
    return out


from . import tpl_lower, tpl_upper, tpl_floor, tpl_misc  # noqa: E402,F401  (registers templates)
from . import tpl_v3  # noqa: E402,F401  (v3 archetypes replace older ones of the same name)
from . import tpl_x54  # noqa: E402,F401  (5.4: the moves that had no picture, one drawing each)
from . import tpl_x54b  # noqa: E402,F401  (5.4: the last 41, machines and partner exercises)

# explosive / ballistic archetypes: fast limb whips are part of the movement
for _n in ("leg_swing", "jump_squat", "high_knees", "mountain_climber", "burpee", "broad_jump", "skater_jump", "jumping_jack",
           "tuck_jump", "treadmill_run", "split_jump", "lateral_hop", "kb_clean", "thruster", "medball_slam",
           "kb_swing", "power_clean", "bike", "battle_ropes", "jump_rope"):
    if _n in REG:
        REG[_n].fast = True
from . import tpl_c  # noqa: E402,F401  (machine / cable / cardio / held-implement set-ups)
