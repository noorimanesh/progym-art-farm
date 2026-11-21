"""5.4 moves that had no picture (data/v3/excluded.csv): one function per exercise key, reached through the
templates "x54" (ordinary) and "x54f" (explosive: fast limb whips are part of the move).  Each one draws what
the steps describe, with the equipment the earlier archetype left out.  Registered after tpl_v3."""
from .templates import tpl, E, H, seg, X, Y, Z, np, math, SIDES, rz, REG
from .equipment import rx, ry
from .poses import SOLE
from .rig import unit
from . import fam
from .fam import arm_fk, arm_ik
from .tpl_v3 import keyed_stand, _interp

X54 = {}
DOME = 0.21          # top of a balance trainer (dome up) above the floor


def x(*keys):
    def deco(fn):
        for k in keys:
            X54[k] = fn
        return fn
    return deco


def _run(c, t, L, row):
    fn = X54.get(row.get("key") or "")
    if fn is None:
        raise KeyError(f"x54: no drawing for {row.get('key')}")
    return fn(c, t, L, row)


@tpl("x54", (80, 8))
def x54(c, t, L, row):
    return _run(c, t, L, row)


@tpl("x54f", (80, 8), fast=True)
def x54f(c, t, L, row):
    return _run(c, t, L, row)


def _keys(K, defaults=None):
    """Fill the optional key values of keyed_stand (heel lifts, planted flags, surfaces)."""
    d0 = {"hL": 0.0, "hR": 0.0, "gL": 1.0, "gR": 1.0, "sL": 0.0, "sR": 0.0}
    d0.update(defaults or {})
    for _, d in K:
        for k, v in d0.items():
            d.setdefault(k, v)
    return K


def _with_eq(fr, extra):
    """Frame with more equipment (a list, or a function (spec, eq, ex) -> list)."""
    b0 = fr.build

    def build():
        spec, eq, ex = b0()
        more = extra(spec, eq, ex) if callable(extra) else extra
        return spec, list(eq) + list(more), ex
    fr.build = build
    return fr


ARMS_RUN = dict(ua=(0.15, 0.35, -0.9), el=80)
ARMS_DOWN = dict(ua=(0.12, 0.1, -1), el=15)


# ================================================================== side to side over a box / a balance trainer
@x("box-shuffle", "lateral-box-shuffle", "balance-trainer-lateral-cross-over-jump")
def box_shuffle(c, t, L, row):
    """One foot on top of the box (or dome), the other on the floor beside it; a small hop sideways over it
    switches feet (cycle: right foot up, hop left over, left foot up, hop back)."""
    dome = "balance" in row["key"]
    h = DOME if dome else 0.3 * c.S
    w = (0.42 if dome else 0.28) * c.S   # foot on the floor this far from the box (dome) centre
    z0 = c.pz * 0.9
    K = _keys([
        (0.00, dict(fL=(-w, 0, 0), fR=(0.04, 0, h), sR=h, pz=z0 + h * 0.5, px=-0.1, pitch=12, **ARMS_RUN)),
        (0.25, dict(fL=(-w * 0.4, 0, 0.12), fR=(w * 0.4, 0, h + 0.1), gL=0, gR=0, sR=h, pz=z0 + h * 0.5 + 0.12, px=0.0, pitch=10,
                    ua=(0.3, 0.25, -0.8), el=70)),
        (0.50, dict(fL=(-0.04, 0, h), fR=(w, 0, 0), sL=h, pz=z0 + h * 0.5, px=0.1, pitch=12, ua=(0.15, -0.2, -0.9), el=80)),
        (0.75, dict(fL=(-w * 0.4, 0, h + 0.1), fR=(w * 0.4, 0, 0.12), gL=0, gR=0, sL=h, pz=z0 + h * 0.5 + 0.12, px=0.0, pitch=10,
                    ua=(0.3, 0.25, -0.8), el=70)),
        (1.00, dict(fL=(-w, 0, 0), fR=(0.04, 0, h), sR=h, pz=z0 + h * 0.5, px=-0.1, pitch=12, **ARMS_RUN)),
    ])
    kv = _interp(K, min(t, 0.9999))
    eq = [E("bosu", (0, -0.05, 0), eid="bosu")] if dome else [E("plyo_box", (0, -0.02, 0), eid="box", size=(0.36, 0.62, h))]
    return keyed_stand(c, kv, equip=eq)


@x("balance-trainer-lateral-jump")
def bt_lateral_jump(c, t, L, row):
    """Jump sideways onto the dome with both feet, then off to the other side and back (cycle)."""
    d = 0.5 * c.S
    w = c.hw * 0.55
    z = c.pz
    sq = dict(pitch=24, ua=(0.15, -0.3, -0.9), el=20)
    K = _keys([
        (0.00, dict(fL=(-d - w, 0, 0), fR=(-d + w, 0, 0), pz=z * 0.8, px=-d, **sq)),
        (0.13, dict(fL=(-d / 2 - w, 0, DOME + 0.12), fR=(-d / 2 + w, 0, DOME + 0.12), gL=0, gR=0, hL=30, hR=30, pz=z * 0.97 + DOME, px=-d / 2,
                    pitch=6, ua=(0.15, 0.5, 0.5), el=20)),
        (0.25, dict(fL=(-w, 0, DOME), fR=(w, 0, DOME), sL=DOME, sR=DOME, pz=z * 0.8 + DOME, px=0.0, **sq)),
        (0.38, dict(fL=(d / 2 - w, 0, DOME + 0.12), fR=(d / 2 + w, 0, DOME + 0.12), gL=0, gR=0, hL=30, hR=30, pz=z * 0.97 + DOME, px=d / 2,
                    pitch=6, ua=(0.15, 0.5, 0.5), el=20)),
        (0.50, dict(fL=(d - w, 0, 0), fR=(d + w, 0, 0), pz=z * 0.8, px=d, **sq)),
        (0.63, dict(fL=(d / 2 - w, 0, DOME + 0.12), fR=(d / 2 + w, 0, DOME + 0.12), gL=0, gR=0, hL=30, hR=30, pz=z * 0.97 + DOME, px=d / 2,
                    pitch=6, ua=(0.15, 0.5, 0.5), el=20)),
        (0.75, dict(fL=(-w, 0, DOME), fR=(w, 0, DOME), sL=DOME, sR=DOME, pz=z * 0.8 + DOME, px=0.0, **sq)),
        (0.88, dict(fL=(-d / 2 - w, 0, DOME + 0.12), fR=(-d / 2 + w, 0, DOME + 0.12), gL=0, gR=0, hL=30, hR=30, pz=z * 0.97 + DOME, px=-d / 2,
                    pitch=6, ua=(0.15, 0.5, 0.5), el=20)),
        (1.00, dict(fL=(-d - w, 0, 0), fR=(-d + w, 0, 0), pz=z * 0.8, px=-d, **sq)),
    ])
    kv = _interp(K, min(t, 0.9999))
    return keyed_stand(c, kv, equip=[E("bosu", (0, -0.04, 0), eid="bosu")])


@x("balance-trainer-front-back-cross-jump")
def bt_front_back(c, t, L, row):
    """Jump forward onto the dome, then on over it, and back the same way (cycle, side view)."""
    d = 0.45 * c.S
    w = c.hw * 0.55
    z = c.pz
    sq = dict(pitch=14, ua=(0.15, -0.3, -0.9), el=20)
    air = dict(gL=0, gR=0, hL=30, hR=30, pitch=8, ua=(0.15, 0.6, 0.4), el=20)
    K = _keys([
        (0.00, dict(fL=(-w, -d, 0), fR=(w, -d, 0), pz=z * 0.8, py=-d, **sq)),
        (0.13, dict(fL=(-w, -d / 2, DOME + 0.14), fR=(w, -d / 2, DOME + 0.14), pz=z * 0.97 + DOME, py=-d / 2, **air)),
        (0.25, dict(fL=(-w, 0, DOME), fR=(w, 0, DOME), sL=DOME, sR=DOME, pz=z * 0.8 + DOME, py=0.0, **sq)),
        (0.38, dict(fL=(-w, d / 2, DOME + 0.14), fR=(w, d / 2, DOME + 0.14), pz=z * 0.97 + DOME, py=d / 2, **air)),
        (0.50, dict(fL=(-w, d, 0), fR=(w, d, 0), pz=z * 0.8, py=d, **sq)),
        (0.63, dict(fL=(-w, d / 2, DOME + 0.14), fR=(w, d / 2, DOME + 0.14), pz=z * 0.97 + DOME, py=d / 2, **air)),
        (0.75, dict(fL=(-w, 0, DOME), fR=(w, 0, DOME), sL=DOME, sR=DOME, pz=z * 0.8 + DOME, py=0.0, **sq)),
        (0.88, dict(fL=(-w, -d / 2, DOME + 0.14), fR=(w, -d / 2, DOME + 0.14), pz=z * 0.97 + DOME, py=-d / 2, **air)),
        (1.00, dict(fL=(-w, -d, 0), fR=(w, -d, 0), pz=z * 0.8, py=-d, **sq)),
    ])
    kv = _interp(K, min(t, 0.9999))
    return keyed_stand(c, kv, equip=[E("bosu", (0, -0.04, 0), eid="bosu")])


@x("balance-trainer-toe-tap")
def bt_toe_tap(c, t, L, row):
    """Facing the dome, the toes tap its top one foot at a time, a quick skip in between (cycle)."""
    w = c.hw * 0.55
    y = 0.36 * c.S
    z = c.pz * 0.97
    tap = lambda sd: dict(pitch=6, ua=(0.15, 0.35, -0.85) if sd == "R" else (0.15, -0.35, -0.85), el=85)
    K = _keys([
        (0.00, dict(fL=(-w, 0, 0), fR=(w * 0.7, y, DOME), sR=DOME, hR=25, pz=z, py=0.04, **tap("R"))),
        (0.25, dict(fL=(-w, 0.04, 0.06), fR=(w, 0.04, 0.08), gL=0, gR=0, pz=z + 0.05, py=0.04, pitch=6, ua=(0.15, 0.0, -0.9), el=85)),
        (0.50, dict(fL=(-w * 0.7, y, DOME), fR=(w, 0, 0), sL=DOME, hL=25, pz=z, py=0.04, **tap("L"))),
        (0.75, dict(fL=(-w, 0.04, 0.08), fR=(w, 0.04, 0.06), gL=0, gR=0, pz=z + 0.05, py=0.04, pitch=6, ua=(0.15, 0.0, -0.9), el=85)),
        (1.00, dict(fL=(-w, 0, 0), fR=(w * 0.7, y, DOME), sR=DOME, hR=25, pz=z, py=0.04, **tap("R"))),
    ])
    kv = _interp(K, min(t, 0.9999))
    return keyed_stand(c, kv, equip=[E("bosu", (0, y - 0.04, 0), eid="bosu")])


# ================================================================== hurdle
@x("hurdle-step-over")
def hurdle_step_over(c, t, L, row):
    """Standing beside a low hurdle: the right knee lifts high and out, the leg steps over and lands on the
    far side, the left leg follows; then back the same way (cycle, front view)."""
    hh = 0.42 * c.S
    w = c.hw * 0.6
    d = 0.32 * c.S                    # each foot lands this far from the hurdle
    z = c.pz * 0.97
    up = dict(pitch=4, ua=(0.25, 0.0, -0.9), el=60)
    K = _keys([
        (0.00, dict(fL=(-d - 2 * w, 0, 0), fR=(-d, 0, 0), pz=z, px=-d - w, **up)),
        (0.12, dict(fL=(-d - 2 * w, 0, 0), fR=(-0.02, 0.05, hh + 0.12), gR=0, pz=z - 0.02, px=-d - w * 0.7, **up)),
        (0.25, dict(fL=(-d - 2 * w, 0, 0), fR=(d, 0, 0), pz=z - 0.08, px=-w * 0.3, **up)),
        (0.37, dict(fL=(0.02, 0.05, hh + 0.12), fR=(d, 0, 0), gL=0, pz=z - 0.02, px=d - w * 0.3, **up)),
        (0.50, dict(fL=(d, 0, 0), fR=(d + 2 * w, 0, 0), pz=z, px=d + w, **up)),
        (0.62, dict(fL=(-0.02 + 0.0, 0.05, hh + 0.12), fR=(d + 2 * w, 0, 0), gL=0, pz=z - 0.02, px=d + w * 0.7, **up)),
        (0.75, dict(fL=(-d, 0, 0), fR=(d + 2 * w, 0, 0), pz=z - 0.08, px=w * 0.3, **up)),
        (0.87, dict(fL=(-d, 0, 0), fR=(-0.02, 0.05, hh + 0.12), gR=0, pz=z - 0.02, px=-d + w * 0.3, **up)),
        (1.00, dict(fL=(-d - 2 * w, 0, 0), fR=(-d, 0, 0), pz=z, px=-d - w, **up)),
    ])
    kv = _interp(K, min(t, 0.9999))
    return keyed_stand(c, kv, equip=[E("hurdle", (0, 0.02, 0), R=rz(90), eid="hurdle", h=hh)])


# ================================================================== step / boxes
@x("step-up-to-deficit-reverse-lunge", "bodyweight-step-up-to-deficit-reverse-lunge")
def step_deficit_lunge(c, t, L, row):
    """Standing tall on a low step, the right foot steps back down to the floor into a deep reverse lunge (the
    front foot stays on the step), then drives back up onto the step."""
    sh = 0.18 * c.S
    w = c.hw * 0.5
    db = "dumbbell" in (row.get("equipment") or "")
    K = _keys([
        (0.00, dict(fL=(-w, 0, sh), fR=(w, 0.0, sh), sL=sh, sR=sh, pz=c.pz * 0.99 + sh, py=0.0, pitch=2, **ARMS_DOWN)),
        (0.30, dict(fL=(-w, 0, sh), fR=(w, -0.45 * c.S, 0.08), gR=0, sL=sh, pz=c.pz * 0.9 + sh * 0.6, py=-0.12, pitch=6, **ARMS_DOWN)),
        (1.00, dict(fL=(-w, 0, sh), fR=(w, -0.78 * c.S, 0), hR=70, sL=sh, pz=c.pz * 0.55 + sh * 0.35, py=-0.3 * c.S, pitch=10, **ARMS_DOWN)),
    ])
    kv = _interp(K, min(t, 0.9999))
    legs = {}
    for sd in "LR":
        b = np.asarray(kv["f" + sd], float)
        legs[sd] = dict(ball=b + np.array([0, c.ball_y, SOLE]), yaw=6, heel=float(kv["h" + sd]), surf=float(kv["s" + sd]))
    planted = [sd for sd in "LR" if kv["g" + sd] > 0.5]
    eq = [E("step", (0, 0.0, 0), eid="step", height=sh)]
    return c.stand(legs, pz=float(kv["pz"]), py=float(kv["py"]), pel=(float(kv["pitch"]), 0, 0), hold="db_side" if db else "none",
                   arms=None if db else arm_fk((0.15, 0.1, -1), elbow=15), balance=None, reach=False, planted=planted, equip=eq)


@x("2-box-depth-jump")
def two_box_depth_jump(c, t, L, row):
    """Step off the first box, land between the boxes and rebound at once onto the second box; step down
    behind it and walk back (cycle, side view)."""
    bh = 0.4 * c.S
    b1, b2 = -0.6 * c.S, 0.62 * c.S
    w = c.hw * 0.6
    sq = lambda k: c.pz * k
    std = dict(ua=(0.12, 0.1, -1), el=15, neck=0)
    K = _keys([
        (0.00, dict(fL=(-w, b1, bh), fR=(w, b1, bh), sL=bh, sR=bh, pz=sq(0.97) + bh, py=b1, pitch=3, **std)),
        (0.14, dict(fL=(-w, b1, bh), fR=(w, b1 * 0.5, bh * 0.4), gR=0, sL=bh, pz=sq(0.95) + bh * 0.8, py=b1 * 0.78, pitch=6, **std)),
        (0.28, dict(fL=(-w, 0, 0), fR=(w, 0, 0), pz=sq(0.68), py=-0.04, pitch=36, ua=(0.15, -0.5, -0.8), el=12, neck=-18)),
        (0.42, dict(fL=(-w, b2 * 0.45, bh + 0.16), fR=(w, b2 * 0.45, bh + 0.16), gL=0, gR=0, hL=40, hR=40, pz=sq(0.99) + bh + 0.18,
                    py=b2 * 0.5, pitch=8, ua=(0.12, 0.9, 0.35), el=20, neck=-5)),
        (0.56, dict(fL=(-w, b2, bh), fR=(w, b2, bh), sL=bh, sR=bh, pz=sq(0.72) + bh, py=b2 - 0.04, pitch=32, ua=(0.15, 0.8, -0.2), el=25, neck=-15)),
        (0.70, dict(fL=(-w, b2, bh), fR=(w, b2, bh), sL=bh, sR=bh, pz=sq(0.97) + bh, py=b2, pitch=3, **std)),
        (0.85, dict(fL=(-w, b2 * 0.5, bh), fR=(w, b1 * 0.5, bh), sL=bh, sR=bh, pz=sq(0.97) + bh, py=0.0, pitch=3, **std)),
        (1.00, dict(fL=(-w, b1, bh), fR=(w, b1, bh), sL=bh, sR=bh, pz=sq(0.97) + bh, py=b1, pitch=3, **std)),
    ])
    # 0.70 -> 1.00 is the walk back on top of a bridge of the two boxes? no: the athlete steps down and walks
    # back on the floor; drawn as a short stride on the floor between the boxes
    K[6] = (0.85, dict(fL=(-w, 0.05, 0), fR=(w, -0.05, 0), sL=0, sR=0, gL=1, gR=1, hL=0, hR=0, pz=sq(0.97), py=0.0, pitch=3, **std))
    kv = _interp(K, min(t, 0.9999))
    return keyed_stand(c, kv, equip=[E("plyo_box", (0, b1 - 0.02, 0), eid="box1", size=(0.6, 0.5, bh)),
                                     E("plyo_box", (0, b2 + 0.04, 0), eid="box2", size=(0.6, 0.5, bh))])


# ================================================================== dowel moves
def _ext(a, b, d):
    """End point beyond grip a, away from grip b, by d (resolved after solving)."""
    def f(pts, D, Hp, ctx):
        pa, pb = np.asarray(pts[a], float), np.asarray(pts[b], float)
        return pa + unit(pa - pb) * d
    return f


def _dowel(a="gripL", b="gripR", da=0.15, db=0.15):
    """A PVC dowel through both grips, a little longer on each side."""
    return seg("dowel", _ext(a, b, da), _ext(b, a, db), 0.014, "pvc")


@x("dowel-helicopter")
def dowel_helicopter(c, t, L, row):
    """Dowel across the upper back, hands wide on it; the torso turns from side to side (cycle) with the
    hips facing forward."""
    yaw = 45 * math.sin(2 * math.pi * t)
    legs = c.feet(w=c.hw * 1.1, toe=8)
    gw = c.sw * 1.05

    def bar(D, Hp, c_, sd):
        Rb = D[c.r.bi("spine01")]
        return c.lmk(D, Hp, "back_bar") + Rb @ (X * SIDES[sd] * gw - Y * 0.01)
    arms = arm_ik(bar, lambda D, Hp, c_, sd: D[c.r.bi("spine01")] @ (Y * -0.2 + Z), lambda D, Hp, c_, sd: D[c.r.bi("spine01")] @ np.array([SIDES[sd] * 0.2, -0.3, -1]),
                  curl=0.85, fing=(0, 0, 1))
    return c.stand(legs, hk=0.99, pel=(4, 0, yaw * 0.2), spine=(0, 0, yaw * 0.8), neck=(0, 0, yaw * 0.1), arms=arms,
                   balance="com", equip=[_dowel(da=0.12, db=0.12)])


@x("hip-hinge")
def hip_hinge(c, t, L, row):
    """Dowel held vertically along the spine (right hand behind the neck, left hand at the low back); the hips
    push back with soft knees until the torso is near horizontal, the dowel touching head, upper back and
    sacrum the whole way."""
    hinge = L(4, 70)
    legs = c.feet(w=c.hw * 0.9, toe=6)
    J = c.r.joint
    nape = c.lm["nape"][1]
    sac = np.array([0.0, J("root")[1] - 0.13, c.z_hip + 0.07])

    def top(D, Hp, c_, sd):
        return c.bp(D, Hp, "neck01", nape + np.array([0.0, -0.06, -0.02]))

    def low(D, Hp, c_, sd):
        return c.bp(D, Hp, "root", sac + np.array([0.0, -0.05, 0.0]))
    armR = arm_ik(top, lambda D, Hp, c_, sd: D[c.r.bi("spine01")] @ Z, lambda D, Hp, c_, sd: D[c.r.bi("spine01")] @ np.array([1, 0.2, 0.3]), curl=0.9, sides="R")
    armL = arm_ik(low, lambda D, Hp, c_, sd: D[c.r.bi("spine01")] @ Z, lambda D, Hp, c_, sd: D[c.r.bi("spine01")] @ np.array([-1, -0.2, -0.4]), curl=0.9, sides="L")
    arms = dict(armR, **armL)
    fr = c.stand(legs, hk=L(0.995, 0.94), pel=(hinge, 0, 0), spine=(L(0, -4), 0, 0), neck=(L(0, -8), 0, 0), arms=arms,
                 balance="com")
    return _with_eq(fr, [_dowel("gripR", "gripL", 0.22, 0.2)])


@x("dowel-triceps-stretch")
def dowel_triceps(c, t, L, row):
    """Right hand behind the head holding the top of a dowel that hangs down the back; the left hand behind the
    back pulls the bottom end down, so the right elbow points up and the triceps stretches."""
    legs = c.feet(w=c.hw * 0.9, toe=8)
    pull = L(0.0, 1.0)
    J = c.r.joint
    nape = c.lm["nape"][1]
    mid = np.array([0.0, J("spine03")[1] - 0.14, J("spine03")[2] - 0.02])

    def topg(D, Hp, c_, sd):
        return c.bp(D, Hp, "neck01", nape + np.array([0.035, -0.08, -0.06 - 0.03 * pull]))

    def lowg(D, Hp, c_, sd):
        return c.bp(D, Hp, "spine03", mid + np.array([0.03, -0.02, -0.05 - 0.05 * pull]))
    armR = arm_ik(topg, lambda D, Hp, c_, sd: D[c.r.bi("spine01")] @ -Z, lambda D, Hp, c_, sd: D[c.r.bi("spine01")] @ np.array([0.3, 0.3, 1]), curl=0.9, sides="R")
    armL = arm_ik(lowg, lambda D, Hp, c_, sd: D[c.r.bi("spine01")] @ Z, lambda D, Hp, c_, sd: D[c.r.bi("spine01")] @ np.array([-0.8, -0.1, -0.8]), curl=0.9, sides="L")
    fr = c.stand(legs, hk=0.995, pel=(2, 0, 0), neck=(-6, 0, 0), arms=dict(armR, **armL), balance="com")
    return _with_eq(fr, [_dowel("gripR", "gripL", 0.1, 0.12)])


@x("overhead-dowel-shoulder-stretch")
def oh_dowel_stretch(c, t, L, row):
    """Dowel in a very wide overhand grip, arms straight overhead; the arms ease back behind the head while
    the ribs stay down (front-quarter view)."""
    legs = c.feet(w=c.hw * 0.9, toe=8)
    back = L(0.0, 1.0)

    def g(D, Hp, c_, sd):
        sh = fam.shoulder(D, Hp, c, sd)
        d = unit(np.array([SIDES[sd] * 0.55, -0.45 * back, 1.0]))
        return sh + d * c.Lh * 0.97
    arms = arm_ik(g, lambda D, Hp, c_, sd: -Y, (0, -1, 0.2), curl=0.85, fing=(0, 0, 1))
    fr = c.stand(legs, hk=0.995, pel=(1, 0, 0), arms=arms, balance="com")
    return _with_eq(fr, [_dowel(da=0.12, db=0.12)])


@x("dowel-forearm-stretch")
def dowel_forearm(c, t, L, row):
    """Right hand holds a dowel by its middle, upright beside the body, forearm forward; the hand turns the
    dowel forward (and back) so the forearm rotates and stretches."""
    legs = c.feet(w=c.hw * 0.9, toe=8)
    rot = L(0.0, 1.0)

    def g(D, Hp, c_, sd):
        sh = fam.shoulder(D, Hp, c, "R")
        return sh + np.array([0.12, 0.28, -0.3])
    # the fist points forward; the dowel tilts forward with the forearm's turn (radius over ulna)
    a = math.radians(-80 * rot)
    th = np.array([0.0, math.sin(-a) * 0.0, 1.0])
    thumb = unit(np.array([0.0, -math.sin(a), math.cos(a)]))
    armR = arm_ik(g, lambda D, Hp, c_, sd, thumb=thumb: thumb, (0.6, -0.2, -1), curl=0.9, sides="R")
    armL = arm_fk((0.08, 0.05, -1), elbow=12, sides="L")
    fr = c.stand(legs, hk=0.995, pel=(2, 0, 0), arms=dict(armR, **armL), balance="com")

    def stick(pts, D, Hp, ctx, k):
        g0 = np.asarray(pts["gripR"], float)
        return g0 + thumb * 0.42 * k
    return _with_eq(fr, [seg("dowel", lambda p, D, Hp, cx: stick(p, D, Hp, cx, 1.0), lambda p, D, Hp, cx: stick(p, D, Hp, cx, -1.0), 0.014, "pvc")])


# ================================================================== side planks
from .rig import body_rot  # noqa: E402
from .poses import SKIN_FLOOR  # noqa: E402

SP_TILT = {"m": 5.7, "f": 3.6}
SP_LEG = {"m": 1.58, "f": 1.5}


def side_plank_x(c, t, L, drop=0.0, elev=0.06, knees=False, top_arm="hip", top_leg=0.0, hand_h=0.0, feet_h=0.0,
                 equip=(), hand="forearm", leg_fn=None, arms_extra=None):
    """Side plank on the right forearm (or hand), left side up, facing +Y.
    drop: degrees the hips sink toward the floor (the torso tips about the propped shoulder, the legs turn back up);
    hand_h: the forearm on a support this high; feet_h: the top foot on a support this high (bench, straps);
    top_arm: 'hip' | 'up' | callable arm spec; top_leg: lift of the top leg (0..0.6)."""
    sh_r = c.r.joint("upperarm01.R")
    an_r = c.r.joint("foot.R")
    kn_r = c.r.joint("lowerleg01.R")
    straight_arm = hand == "hand"
    sz = (c.Lpf * 0.97 if straight_arm else c.r.dims["R"]["L1"] + 0.05) + hand_h
    if knees:
        blen, az = abs(sh_r[2] - kn_r[2]), 0.06
    else:
        blen, az = abs(sh_r[2] - an_r[2]), 0.07 + feet_h
    ang = math.degrees(math.asin(max(-0.99, min(0.99, (sz - az) / blen))))
    roll = 90 - ang - SP_TILT.get(c.g, 5.0) - drop
    R = body_rot(0, roll, 0)
    S = np.array([0.0, 0.0, sz])
    pel = S - R @ (sh_r - c.r.pc_rest) + np.array([0, 0, elev])
    if straight_arm:
        arms = {"R": lambda D, Hp, c_: dict(ua=-Z, elbow=4, bend=Y, thumb=Y, curl=0.1, fing=Y * 0.3 + X)}
    else:
        arms = {"R": lambda D, Hp, c_: dict(ua=-Z, elbow=88, bend=Y, thumb=Z, curl=0.3, fing=Y + X * 0.3)}
    if top_arm == "up":
        arms.update(arm_fk((0.05, 0.0, 1.0), elbow=5, thumb="fwd", world=False, sides="L"))
    elif callable(top_arm):
        arms["L"] = top_arm
    else:
        arms.update(fam.arm_ik(lambda D, Hp, c_, sd: c.bp(D, Hp, "root", np.array([-0.17, 0.0, c.z_hip + 0.08])),
                               (0, -1, 0), (-1, -0.5, 0.3), key="palm", curl=0.2, sides="L"))
    if arms_extra:
        arms.update(arms_extra)

    def lfk(sd, D):
        R0 = D[c.r.bi("root")]
        lift = top_leg if sd == "L" else 0.0
        lift += math.tan(math.radians(drop * SP_LEG[c.g]))
        if leg_fn:
            out = leg_fn(sd, D, lift)
            if out is not None:
                return out
        return dict(thigh=unit(R0 @ np.array([0.0 - lift, 0.0, -1])), knee=90 if knees else 3, kbend=R0 @ -Y,
                    fdir=R0 @ (Y * 0.6 - Z * 0.8))
    fr = c.stand({}, pz=pel[2], py=pel[1], px=pel[0], pel=(0, roll, 0), arms=arms, balance=None, reach=False,
                 equip=[E("mat", (0, 0.0, 0), eid="mat")] + list(equip), planted=())
    b0 = fr.build

    def build():
        spec, eq, ex = b0()
        D, Hp = c.torso(spec)
        spec["leg"] = {sd: lfk(sd, D) for sd in "LR"}
        return spec, eq, ex
    fr.build = build
    fr.settle = [("floor", SKIN_FLOOR)]
    fr.sp_R, fr.sp_S = R, S            # for placing a support under the feet
    return fr


def _sp_ankle(c, R, S, sd="L"):
    """Where the ankle of a straight-leg side plank is (before solving)."""
    return S + R @ (c.r.joint(f"foot.{sd}") - c.r.joint("upperarm01.R"))


@x("side-plank-hip-dip")
def sp_hip_dip(c, t, L, row):
    """Side plank on the forearm, feet stacked: the hips lower slowly toward the floor and lift back up."""
    return side_plank_x(c, t, L, drop=L(0.0, 30.0), elev=L(0.06, 0.0))


@x("side-plank-with-knees-bent")
def sp_knees(c, t, L, row):
    """Side plank on the forearm with both knees bent 90 degrees and resting on the floor, hips lifting from the
    floor until the body is straight from head to knees."""
    return side_plank_x(c, t, L, drop=L(20.0, 0.0), elev=L(0.0, 0.05), knees=True)


@x("balance-trainer-side-star-plank")
def bt_side_star(c, t, L, row):
    """Lower hand in the middle of the flat side of an upturned balance trainer, arm straight; the top arm
    reaches to the ceiling and the top leg lifts (star)."""
    hh = 0.25
    fr = side_plank_x(c, t, L, hand="hand", hand_h=hh, top_arm="up", top_leg=L(0.0, 0.55),
                      equip=[E("bosu", (0, 0.02, hh), R=rx(180), eid="bosu")])
    return fr


@x("copenhagen-plank")
def copenhagen(c, t, L, row):
    """Side plank on the forearm with the top leg resting on a bench at the ankle; the hips lift until the body
    is straight, the bottom leg hangs under the bench."""
    bh = 0.44
    fr0 = side_plank_x(c, 0.0, lambda a, b: a, feet_h=bh - 0.07)
    ank = _sp_ankle(c, fr0.sp_R, fr0.sp_S, "L")

    def leg(sd, D, lift):
        if sd != "R":
            return None
        R0 = D[c.r.bi("root")]
        return dict(thigh=unit(R0 @ np.array([0.45, 0.05, -1])), knee=12, kbend=R0 @ -Y, fdir=R0 @ (Y * 0.6 - Z * 0.8))
    return side_plank_x(c, t, L, feet_h=bh - 0.07, drop=0.0, elev=L(0.0, 0.04), leg_fn=leg,
                        equip=[E("bench", (ank[0] - 0.05, 0.0, 0), eid="bench", height=bh, length=0.9)])


@x("suspension-hip-drop")
def susp_hip_drop(c, t, L, row):
    """Feet stacked in the suspension cradles about 30 cm off the floor, side plank on the forearm: the hips
    sink a few centimetres toward the floor and lift back."""
    fh = 0.32
    fr0 = side_plank_x(c, 0.0, lambda a, b: a, feet_h=fh)
    ank = _sp_ankle(c, fr0.sp_R, fr0.sp_S, "L")
    anchor = np.array([ank[0] - 0.35, 0.0, 2.4])
    fr = side_plank_x(c, t, L, feet_h=fh, drop=L(0.0, 14.0), elev=L(0.05, 0.0))
    return _with_eq(fr, lambda spec, eq, ex: [dict(E("trx_anchor", anchor * np.array([1, 1, 0]), eid="trx", h=2.4), fit=False),
                                              seg("strapL", anchor, ank + np.array([0, 0.0, 0.06]), 0.012, "strap"),
                                              seg("strapR", anchor, ank + np.array([0, -0.05, 0.02]), 0.012, "strap")])


@x("band-side-plank-row")
def band_sp_row(c, t, L, row):
    """Side plank on the forearm facing a low band anchor in front; the top hand rows the band, elbow driving
    back until the hand reaches the chest."""
    u = L(0.0, 1.0)
    anchor = np.array([0.0, 1.1, 0.12])

    def arm(D, Hp, c_):
        sh = fam.shoulder(D, Hp, c, "L")
        reach = sh + unit(anchor - sh) * c.Lh * 0.95
        Rb = D[c.r.bi("spine01")]
        rowed = sh + Rb @ np.array([0.05, 0.1, -0.12])
        g = reach * (1 - u) + rowed * u
        return dict(grip=g, thumb=Rb @ Z, pole=Rb @ np.array([0.3, -0.6, -0.6]), curl=0.9)
    fr = side_plank_x(c, t, L, top_arm=arm)
    return _with_eq(fr, [E("band_anchor", anchor * np.array([1, 1, 0]) + np.array([0, 0.05, 0]), eid="post", h=anchor[2]),
                         seg("band", anchor, ("gripL", (0, 0, 0)), 0.008, "band")])


@x("balance-trainer-star-plank-knee-to-elbow")
def bt_star_knee(c, t, L, row):
    """Side plank with the lower hand on the flat side of an upturned balance trainer: from a star (top arm up,
    top leg lifted) the top knee and top elbow come together over the hips, then open again."""
    hh = 0.25
    k = L(0.0, 1.0)

    def arm(D, Hp, c_):
        Rb = D[c.r.bi("spine01")]
        up = dict(ua=Rb @ unit(np.array([-0.05, 0.0, 1.0])), elbow=5, bend=Rb @ Y, thumb="fwd", curl=0.3)
        if k < 1e-3:
            return up
        return dict(ua=Rb @ unit(np.array([-0.35 * k, 0.15 * k, 1.0 - 1.2 * k])), elbow=5 + 110 * k, bend=Rb @ Y, thumb="fwd", curl=0.5)

    def leg(sd, D, lift):
        if sd != "L":
            return None
        R0 = D[c.r.bi("root")]
        return dict(thigh=unit(R0 @ np.array([-0.55 * (1 - k) - 0.2 * k, 0.75 * k, -1.0 + 0.5 * k])), knee=4 + 100 * k, kbend=R0 @ -Y,
                    fdir=R0 @ (Y * 0.6 - Z * 0.8))
    return side_plank_x(c, t, L, hand="hand", hand_h=hh, top_arm=arm, leg_fn=leg,
                        equip=[E("bosu", (0, 0.02, hh), R=rx(180), eid="bosu")])


# ================================================================== front planks
def _roll_body(fr, roll, spine_k=0.7):
    b0 = fr.build

    def build():
        spec, eq, ex = b0()
        p = spec.get("pel", (0, 0, 0))
        spec["pel"] = (p[0], p[1] + roll, p[2])
        s = spec.get("spine", (0, 0, 0))
        spec["spine"] = (s[0], s[1] - roll * spine_k, s[2])
        return spec, eq, ex
    fr.build = build
    return fr


@x("plank-hip-dip")
def plank_hip_dip(c, t, L, row):
    """Forearm plank, feet together: the hips turn so one hip moves toward the floor while the shoulders stay
    still (alternating sides)."""
    fr = fam.plank(c, elbows=True, feet_w=0.1 * c.S, equip=[E("mat", (0, -0.4, 0), eid="mat")], hands_on=True)
    return _roll_body(fr, L(0.0, 30.0), 0.8)


@x("plank-surrender")
def plank_surrender(c, t, L, row):
    """Forearm plank: one knee lowers gently to the floor, then presses back up (alternating lead leg)."""
    k = L(0.0, 1.0)

    def knee(D):
        R0 = D[c.r.bi("root")]
        # the thigh turns down to the floor, the shin folds back along it (knee bend toward the feet)
        a = math.radians(44 * k)          # the knee just reaches the floor; the shin lies back along it
        return dict(thigh=unit(R0 @ np.array([0.03, math.sin(a), -math.cos(a)])), knee=4 + 44 * k, kbend=R0 @ np.array([0, -0.3, -1]),
                    fdir=R0 @ np.array([0, -0.2, -1]))
    fr = fam.plank(c, elbows=True, feet_w=0.16 * c.S, equip=[E("mat", (0, -0.4, 0), eid="mat")], hands_on=True,
                   legs_over={"R": knee}, hip_raise=-0.02 * k)
    fr.planted = ["L"]
    return fr


@x("mini-band-around-the-world-plank")
def miniband_atw(c, t, L, row):
    """Forearm plank with a mini band round the ankles: one foot steps out wide to the side and comes back,
    then the other (alternating)."""
    k = L(0.0, 1.0)

    def out(D):
        R0 = D[c.r.bi("root")]
        a = math.sin(math.pi * k) * 0.06
        return dict(thigh=unit(R0 @ np.array([0.48 * k, 0.0, -1.0])), knee=4 + 10 * math.sin(math.pi * k), kbend=R0 @ np.array([0, -1, 0]),
                    fdir=R0 @ np.array([0.1, -0.4 - a, -1]))
    fr = fam.plank(c, elbows=True, feet_w=0.14 * c.S, equip=[E("mat", (0, -0.4, 0), eid="mat")], hands_on=True,
                   legs_over={"R": out})
    fr.planted = ["L"]

    def band(spec, eq, ex):
        def ank(sd):
            return lambda pts, D, Hp, cx: np.asarray(Hp[c.r.bi(f"foot.{sd}")], float) + np.array([0, 0.0, 0.02])
        return [seg("mbA", ank("L"), ank("R"), 0.012, "band")]
    return _with_eq(fr, band)


@x("stir-the-pot")
def stir_pot(c, t, L, row):
    """Forearms on a stability ball, toes on the floor, body straight: the forearms draw small circles on the
    ball (cycle)."""
    a = 2 * math.pi * t
    hy = 0.07 * math.cos(a)
    bh = 0.58
    fr = fam.plank(c, elbows=True, hands_h=bh, hand_y=hy, feet_w=0.3 * c.S, equip=[E("mat", (0, -0.6, 0), eid="mat"),
                   E("stability_ball", (0.0, -0.02, 0), eid="ball")], hands_on=True)
    return _roll_body(fr, 6 * math.sin(a), 0.3)


@x("suspension-bodysaw")
def susp_bodysaw(c, t, L, row):
    """Toes in the suspension cradles about 30 cm off the floor, forearm plank: the forearms push the body back
    and forth (the shoulders move behind the elbows and back over them)."""
    d = L(0.0, 0.2 * c.S)
    fh = 0.3
    fr = fam.plank(c, elbows=True, feet_h=fh, equip=[E("mat", (0, -0.4, 0), eid="mat")], hands_on=True)
    b0 = fr.build

    def build():
        spec, eq, ex = b0()
        spec["pelvis"] = np.asarray(spec["pelvis"], float) + np.array([0, -d, 0])
        for sd, Lg in spec.get("leg", {}).items():
            if isinstance(Lg, dict) and "ball" in Lg:
                Lg["ball"] = np.asarray(Lg["ball"], float) + np.array([0, -d, 0])
        return spec, eq, ex
    fr.build = build
    anchor = np.array([0, -1.0 * c.S - 0.2, 2.4])

    def straps(spec, eq, ex):
        def foot(sd):
            return lambda pts, D, Hp, cx: np.asarray(Hp[c.r.bi(f"foot.{sd}")], float) + np.array([0, -0.04, 0.03])
        return [dict(E("trx_anchor", anchor * np.array([1, 1, 0]), eid="trx", h=2.4), fit=False),
                seg("strapL", anchor, foot("L"), 0.012, "strap"), seg("strapR", anchor, foot("R"), 0.012, "strap")]
    return _with_eq(fr, straps)


@x("balance-trainer-leg-crossover-plank")
def bt_leg_crossover(c, t, L, row):
    """Straight-arm plank with the hands on the edges of an upturned balance trainer: one leg crosses under the
    body and the toes tap the floor past the other foot (alternating)."""
    hh = 0.25
    k = L(0.0, 1.0)

    def cross(D):
        R0 = D[c.r.bi("root")]
        return dict(thigh=unit(R0 @ np.array([-0.45 * k, 0.32 * k, -1.0])), knee=4 + 18 * k, kbend=R0 @ np.array([0, 0.4, -1]),
                    fdir=R0 @ np.array([0, -0.3, -1]))
    fr = fam.plank(c, down=0.0, hand_w=0.5, hands_h=hh, feet_w=0.24 * c.S, hands_on=True, legs_over={"R": cross},
                   hip_raise=0.03 * k, equip=[E("mat", (0, -0.4, 0), eid="mat"), E("bosu", (0, 0.0, hh), R=rx(180), eid="bosu")])
    fr.planted = ["L"]
    return fr


# ================================================================== push-ups
MATP = lambda: E("mat", (0, -0.4, 0), eid="mat")


@x("deficit-push-up")
def deficit_push_up(c, t, L, row):
    """Hands on two blocks a little wider than the shoulders: the chest lowers a little below the level of the
    hands."""
    hh = 0.12
    hw = c.sw * 1.3
    eq = [E("plyo_box", (SIDES[sd] * hw / 2, 0.0, 0), eid=f"blk{sd}", size=(0.13, 0.22, hh)) for sd in "LR"]
    return fam.plank(c, down=L(0.0, 1.32), hand_w=hw, hands_h=hh, equip=[MATP()] + eq, neck=(-10, 0, 0), hands_on=True)


@x("rotation-push-up")
def rotation_push_up(c, t, L, row):
    """A push-up, then at the top the body turns onto the right hand into a side plank with the left arm
    reaching to the ceiling; back down and the next push-up turns the other way (cycle of one side)."""
    if t <= 0.5:
        k = math.sin(math.pi * t / 0.5)
        return fam.plank(c, down=0.9 * k, feet_w=0.28 * c.S, equip=[MATP()], neck=(-10, 0, 0), hands_on=True)
    k = math.sin(math.pi * (t - 0.5) / 0.5)
    hw = c.sw * 1.15

    def armL(D, Hp, c_, sd):
        floor = np.array([-hw / 2, 0.0, 0.004 + 0.1 * math.sin(math.pi * min(1.0, k * 1.6))])
        sh = fam.shoulder(D, Hp, c, "L")
        up = sh + np.array([0.0, 0.0, 1.0]) * c.Lh * 0.98
        return floor * (1 - k) + up * k
    arms_over = arm_ik(armL, (0, 1, 0), (-1, 0, 0.3), curl=0.1 + 0.2 * k, key="palm" if k < 0.15 else "grip", sides="L",
                       fing=(0, 1, 0))
    fr = fam.plank(c, down=0.0, feet_w=0.28 * c.S, equip=[MATP()], neck=(-10, 0, 0), hands_on=True, arms_over=arms_over)
    fr.cons = [cn for cn in fr.cons if not (cn[0] == "reach_arms")]
    return _roll_body(fr, 75 * k, 0.1)


@x("alternating-medicine-ball-push-up")
def alt_medball_push_up(c, t, L, row):
    """One hand on a medicine ball, the other on the floor: a push-up with the uneven hands (the next rep rolls
    the ball to the other hand; alternating)."""
    br = 0.115
    top = 2 * br + 0.004

    def hand_ball(D, Hp, c_, sd):
        return np.array([c.sw * 0.62, 0.0, top])
    arms_over = arm_ik(hand_ball, (-1, 0.15, 0), (0.25, -1.0, 0.25), curl=0.3, key="palm", fing=(0, 1, 0), sides="R")
    fr = fam.plank(c, down=L(0.0, 0.8), hands_h=top * 0.5, equip=[MATP(), E("medball", (c.sw * 0.62, 0.0, br), eid="mb")],
                   neck=(-10, 0, 0), hands_on=True, arms_over=arms_over, feet_w=0.3 * c.S)
    return _roll_body(fr, -6.0, 0.5)


@x("band-push-up")
def band_push_up(c, t, L, row):
    """A band across the upper back, its ends pinned under the palms: a full push-up against it."""
    fr = fam.plank(c, down=L(0.0, 1.0), equip=[MATP()], neck=(-10, 0, 0), hands_on=True)

    def band(spec, eq, ex):
        def back(sd):
            def f(pts, D, Hp, cx):
                Rb = D[c.r.bi("spine01")]
                return np.asarray(c.lmk(D, Hp, "back_bar"), float) + Rb @ (X * SIDES[sd] * 0.17 - Y * 0.03)
            return f

        def palm(sd):
            return lambda pts, D, Hp, cx: np.asarray(pts["grip" + sd], float) + np.array([0, 0, -0.02])
        return [seg("bandL", palm("L"), back("L"), 0.01, "band"), seg("bandR", palm("R"), back("R"), 0.01, "band"),
                seg("bandC", back("L"), back("R"), 0.01, "band")]
    return _with_eq(fr, band)


def _strap_lean(c, t, L, down, hands_h=0.95):
    """Leaning push-up in suspension straps: feet on the floor, hands in the handles held about hip height."""
    fr = fam.plank(c, down=down, hands_h=hands_h, feet_w=0.24 * c.S, equip=[], neck=(-6, 0, 0), hands_on=True,
                   fingers="fwd")
    anchor = np.array([0.0, -0.75, 2.45])          # behind the athlete: the straps come over the shoulders
    return _with_eq(fr, [dict(E("trx_anchor", anchor * np.array([1, 1, 0]), eid="trx", h=2.45), fit=True),
                         seg("strapL", anchor, ("gripL", (0, 0, 0)), 0.012, "strap"),
                         seg("strapR", anchor, ("gripR", (0, 0, 0)), 0.012, "strap")])


@x("suspension-push-up-plus")
def susp_push_up_plus(c, t, L, row):
    """Body leaning forward on the straps, arms straight: the chest lowers between the handles and pushes back
    up, and at the top the handles push further away (shoulder blades spread)."""
    return _strap_lean(c, t, L, L(0.0, 0.85), hands_h=0.72)


@x("suspension-scapular-push-up")
def susp_scap_push_up(c, t, L, row):
    """Leaning on the straps with straight arms: only the shoulder blades move (the chest sinks a little, then
    the handles push away)."""
    return _strap_lean(c, t, L, L(0.0, 0.14), hands_h=0.72)


# ================================================================== squats
@x("balance-trainer-lateral-dome-squat")
def bt_lateral_dome_squat(c, t, L, row):
    """Side-on to the trainer, the near (right) foot on the middle of the dome and the left foot on the floor:
    a squat to near-parallel thighs (front view)."""
    w = 0.3 * c.S
    legs = {"L": c.foot(-w, 0, 12), "R": dict(c.foot(w, 0, 12), ball=np.array([w, c.ball_y, DOME + SOLE]), surf=DOME)}
    return c.stand(legs, pz=L(c.pz * 0.98, c.pz * 0.66) + DOME * 0.5, px=w * 0.12, pel=(L(4, 30), L(-6, -3), 0), hold="clasp",
                   balance="com", equip=[E("bosu", (w, -0.04, 0), eid="bosu")])


@x("machine-squat", "pendulum-squat")
def machine_squat(c, t, L, row):
    """Back against the pad, shoulders under the top pads, feet on the platform: the body travels down the
    machine's path (the hack-squat drawing)."""
    return REG["hack_squat_machine"].fn(c, t, L, row)


@x("belt-squat")
def belt_squat(c, t, L, row):
    """Belt round the hips clipped to a chain that hangs to the loaded lever between the feet; standing on the
    raised platform, hands on the rails in front: an upright squat."""
    ph = 0.22
    w = c.hw * 1.2
    legs = {sd: dict(ball=np.array([SIDES[sd] * w, c.ball_y, ph + SOLE]), yaw=14, heel=0, surf=ph) for sd in "LR"}
    rail_h = 1.02

    def rail(D, Hp, c_, sd):
        return np.array([SIDES[sd] * 0.32, 0.5, rail_h])
    arms = arm_ik(rail, (0, 0, 1), (0.6, -0.2, -1), curl=0.9, fing=(0, 1, -0.2))
    fr = c.stand(legs, pz=L(c.pz * 0.98, c.pz * 0.64) + ph, py=L(0.0, -0.04), pel=(L(3, 16), 0, 0), arms=arms,
                 balance=None, reach=True, equip=[E("step", (0, 0.0, 0), eid="plat", height=ph),
                                                 E("rail", (-0.32, 0.5, 0), eid="railL", h=rail_h),
                                                 E("rail", (0.32, 0.5, 0), eid="railR", h=rail_h)])

    def chain(spec, eq, ex):
        hip = lambda pts, D, Hp, cx: np.asarray(c.lmk(D, Hp, "hip_front"), float) + np.array([0, 0.02, -0.06])
        low = lambda pts, D, Hp, cx: np.array([0.0, 0.08, ph + 0.05])
        return [seg("chain", hip, low, 0.016, "darksteel"), E("kettlebell", (0.0, 0.1, ph), eid="wt")]
    return _with_eq(fr, chain)


@x("spanish-squat")
def spanish_squat(c, t, L, row):
    """A heavy band round a post at knee height and behind both knees: the hips sit back and down while the
    shins stay vertical (side view)."""
    w = c.hw * 0.62
    legs = {sd: dict(c.foot(SIDES[sd] * w, 0, 8)) for sd in "LR"}
    post = np.array([0.0, 0.75 * c.S, 0.0])
    kz = 0.5 * c.S
    fr = c.stand(legs, pz=L(c.pz * 0.98, c.pz * 0.6), py=L(0.0, -0.2 * c.S), pel=(L(3, 22), 0, 0),
                 arms=arm_fk((0.12, 1.0, -0.05), elbow=8, thumb="up"), balance=None, reach=True,
                 equip=[E("band_anchor", post, eid="post", h=kz)])

    def band(spec, eq, ex):
        def knee(sd):
            return lambda pts, D, Hp, cx: np.asarray(Hp[c.r.bi(f"lowerleg01.{sd}")], float) + np.array([0, -0.06, 0.02])
        a = post + np.array([0, 0, kz])
        return [seg("bandL", a, knee("L"), 0.012, "band"), seg("bandR", a, knee("R"), 0.012, "band"),
                seg("bandB", knee("L"), knee("R"), 0.012, "band")]
    return _with_eq(fr, band)


def _handles(c, anchor, sides="LR"):
    return [dict(E("trx_anchor", anchor * np.array([1, 1, 0]), eid="trx", h=float(anchor[2])), fit=True)] + \
        [seg(f"strap{sd}", anchor, (f"grip{sd}", (0, 0, 0)), 0.012, "strap") for sd in sides]


@x("suspension-squat-and-row")
def susp_squat_row(c, t, L, row):
    """Facing the anchor with straight arms: squat until the thighs are near parallel, then stand and row the
    handles to the chest; arms straight again for the next squat (cycle)."""
    anchor = np.array([0.0, 1.4, 2.45])
    K = [(0.0, dict(sq=0.0, rw=0.0)), (0.35, dict(sq=1.0, rw=0.0)), (0.7, dict(sq=0.0, rw=1.0)), (1.0, dict(sq=0.0, rw=0.0))]
    kv = _interp(K, min(t, 0.9999))
    sq, rw = kv["sq"], kv["rw"]
    legs = c.feet(w=c.hw * 1.0, toe=10)

    def tgt(D, Hp, c_, sd):
        sh = fam.shoulder(D, Hp, c, sd)
        straight = sh + unit(anchor + X * SIDES[sd] * 0.12 - sh) * c.Lh * 1.02
        Rb = D[c.r.bi("spine01")]
        rowed = sh + Rb @ np.array([SIDES[sd] * 0.08, 0.14, -0.1])
        return straight * (1 - rw) + rowed * rw
    arms = arm_ik(tgt, (0, 0, 1), lambda D, Hp, c_, sd: np.array([SIDES[sd] * 0.6, -0.3, -0.6]), curl=0.9)
    return c.stand(legs, pz=c.pz * (0.98 - 0.32 * sq), py=-0.12 * sq - 0.05 * rw, pel=(4 + 22 * sq - 6 * rw, 0, 0), arms=arms,
                   balance=None, reach=True, equip=_handles(c, anchor))


@x("suspension-figure-four-squat")
def susp_fig4(c, t, L, row):
    """Facing the anchor holding the handles, the right ankle crossed over the left knee (figure four): sit back
    and down on the left leg, arms long to the straps."""
    anchor = np.array([0.0, 1.35, 2.45])
    legs = {"L": c.foot(-c.hw * 0.35, 0, 8)}

    def fig4(D):
        R0 = D[c.r.bi("root")]
        return dict(thigh=unit(R0 @ np.array([0.9, 0.55, -0.25])), knee=110, kbend=R0 @ np.array([-1, 0.1, -0.3]),
                    fdir=R0 @ np.array([-0.3, 0.6, 0.2]))

    def tgt(D, Hp, c_, sd):
        sh = fam.shoulder(D, Hp, c, sd)
        return sh + unit(anchor + X * SIDES[sd] * 0.12 - sh) * c.Lh * 1.02
    arms = arm_ik(tgt, (0, 0, 1), lambda D, Hp, c_, sd: np.array([SIDES[sd] * 0.6, -0.3, -0.6]), curl=0.9)
    fr = c.stand(legs, pz=L(c.pz * 0.97, c.pz * 0.62), px=-c.hw * 0.2, py=L(0.0, -0.22 * c.S), pel=(L(6, 34), 0, 0), arms=arms,
                 balance=None, reach=True, planted=("L",), equip=_handles(c, anchor))
    b0 = fr.build

    def build():
        spec, eq, ex = b0()
        D, Hp = c.torso(spec)
        spec["leg"]["R"] = fig4(D)
        return spec, eq, ex
    fr.build = build
    return fr


# ================================================================== standing: neck, shoulders, straps, bands
from .tpl_v3 import _lean_body, _anchor_for, _strap_eq  # noqa: E402


def _stand(c, t, L, arms=None, hold="sides", neck=(0, 0, 0), spine=(0, 0, 0), pel=(2, 0, 0), equip=(), w=0.9, hk=0.995, legs=None, **kw):
    legs = legs or c.feet(w=c.hw * w, toe=8)
    return c.stand(legs, hk=hk, pel=pel, spine=spine, neck=neck, hold=hold if arms is None else "none", arms=arms,
                   balance="com", equip=list(equip), **kw)


@x("chin-tuck")
def chin_tuck(c, t, L, row):
    """Standing tall, eyes level: the chin draws straight back (a double chin), then relaxes (side view)."""
    fr = _stand(c, t, L, neck=(L(0, 20), 0, 0))
    b0 = fr.build

    def build():
        spec, eq, ex = b0()
        h = spec.get("head", None)
        return spec, eq, ex
    fr.build = build
    return fr


@x("neck-isometric-hold")
def neck_iso(c, t, L, row):
    """Standing tall, the right palm on the forehead: the head presses into the hand without moving."""
    def palm(D, Hp, c_, sd):
        Rh = D[c.r.bi("head")]
        return c.lmk(D, Hp, "forehead") + Rh @ np.array([0.0, 0.035, 0.0])
    arm = arm_ik(palm, lambda D, Hp, c_, sd: D[c.r.bi("head")] @ Z, lambda D, Hp, c_, sd: np.array([1, 0, -0.6]), key="palm", curl=0.1,
                 fing=lambda D, Hp, c_, sd: D[c.r.bi("head")] @ np.array([-0.3, 0, 1]), sides="R")
    arm.update(arm_fk((0.08, 0.05, -1), elbow=12, sides="L"))
    return _stand(c, t, L, arms=arm, neck=(L(-2, 4), 0, 0))


@x("shoulder-squeeze")
def shoulder_squeeze(c, t, L, row):
    """Standing tall, arms by the sides: the shoulder blades draw back and down toward each other (back view)."""
    k = L(0.0, 1.0)
    arms = arm_fk((0.12 + 0.06 * k, -0.08 - 0.22 * k, -1), elbow=12 + 8 * k, thumb="fwd", curl=0.3)
    return _stand(c, t, L, arms=arms, clav=(0, -14 * k, -6 * k) if False else None, spine=(-4 * k, 0, 0), neck=(-2 * k, 0, 0))


def _strap_fly(c, t, L, shape):
    """Facing the anchor, leaning back on the straps with straight arms in front: the arms open into a T, a Y
    (overhead) or a W (elbows pulled down to the ribs) and the body rises."""
    lean0 = 34.0
    anchor = _anchor_for(c, lean0, above=25.0)
    u = L(0.0, 1.0)
    lean = lean0 - 16 * u
    pel, legs = _lean_body(c, lean)
    reach = c.Lh * 1.04

    def tgt(D, Hp, c_, sd):
        sh = fam.shoulder(D, Hp, c, sd)
        d0 = unit(anchor + X * SIDES[sd] * 0.12 - sh)
        Rb = D[c.r.bi("spine01")]
        side, up, fwd = Rb @ (X * SIDES[sd]), Rb @ Z, Rb @ Y
        if shape == "t":
            w = unit(d0 * (1 - u) + side * u * 1.1 + up * 0.05 * u)
            return sh + w * reach
        if shape == "y":
            w = unit(d0 * (1 - u) + (side * 0.55 + up * 0.85) * u)
            return sh + w * reach
        # W: elbows down beside the ribs, hands up beside the head
        straight = sh + d0 * reach
        wpos = sh + side * 0.2 + up * 0.12 + fwd * 0.05
        return straight * (1 - u) + wpos * u
    pole = (lambda D, Hp, c_, sd: D[c.r.bi("spine01")] @ np.array([SIDES[sd] * 0.4, -0.2, -1])) if shape == "w" else \
        (lambda D, Hp, c_, sd: -Z * 0.6 - Y * 0.4)
    arms = arm_ik(tgt, lambda D, Hp, c_, sd: D[c.r.bi("spine01")] @ Z if shape != "y" else -Y, pole, curl=0.9)
    return c.stand(legs, pz=pel[2], py=pel[1], pel=(-lean, 0, 0), neck=(lean * 0.5, 0, 0), arms=arms,
                   equip=_strap_eq(anchor), balance=None, reach=False, planted=())


@x("suspension-t-deltoid-fly")
def susp_t(c, t, L, row):
    return _strap_fly(c, t, L, "t")


@x("suspension-y-deltoid-fly")
def susp_y(c, t, L, row):
    return _strap_fly(c, t, L, "y")


@x("suspension-w-deltoid-fly")
def susp_w(c, t, L, row):
    return _strap_fly(c, t, L, "w")


@x("suspension-resisted-rotation")
def susp_rot(c, t, L, row):
    """Side-on to the anchor (on the right), both hands together on the handles with straight arms in front of
    the chest, leaning away on the straps: the torso turns toward the anchor and back."""
    lean = 22.0
    a = math.radians(lean)
    anchor = np.array([1.6 * c.S, 0.15, 2.4])
    yaw = L(25.0, -55.0)
    legs = {sd: dict(ball=np.array([SIDES[sd] * c.hw * 0.75, c.ball_y, SOLE]), yaw=4, heel=0) for sd in "LR"}

    def tgt(D, Hp, c_, sd):
        Rb = D[c.r.bi("spine01")]
        mid = (fam.shoulder(D, Hp, c, "L") + fam.shoulder(D, Hp, c, "R")) / 2
        return mid + Rb @ np.array([SIDES[sd] * 0.03, c.Lh * 0.95, -0.06])
    arms = arm_ik(tgt, lambda D, Hp, c_, sd: D[c.r.bi("spine01")] @ Z, lambda D, Hp, c_, sd: np.array([SIDES[sd], -0.3, -0.5]), curl=0.9)
    fr = c.stand(legs, hk=0.99, px=-0.12, pel=(2, -lean, yaw * 0.3), spine=(0, lean * 0.3, yaw * 0.7), arms=arms, balance=None,
                 reach=True)
    return _with_eq(fr, [dict(E("trx_anchor", anchor * np.array([1, 1, 0]), eid="trx", h=2.4), fit=True),
                         seg("strapC", anchor, ("gripR", (0, 0, 0)), 0.012, "strap")])


@x("lean-away-lateral-raise")
def lean_away_raise(c, t, L, row):
    """Standing beside a post, the left hand holding it and the body leaning away to the right; the right hand
    raises a dumbbell out to the side until the upper arm is level."""
    post = np.array([-0.62 * c.S, 0.04, 0.0])
    lean = 14.0

    def hold_post(D, Hp, c_, sd):
        return post + np.array([0.0, 0.0, 1.05 * c.S])
    armL = arm_ik(hold_post, (0, 0, 1), (-0.3, -0.8, -0.6), curl=0.9, sides="L")
    up = L(0.0, 1.0)
    armR = arm_fk((math.cos(math.radians(80 * up)) * 0.15 + math.sin(math.radians(80 * up)), 0.12, -math.cos(math.radians(80 * up))),
                  elbow=12, thumb="fwd", sides="R")
    legs = {sd: dict(c.foot(SIDES[sd] * c.hw * 0.4 - 0.08, 0, 8)) for sd in "LR"}
    return c.stand(legs, hk=0.995, px=0.06, pel=(1, lean, 0), spine=(0, -lean * 0.2, 0), arms=dict(armL, **armR), balance=None,
                   reach=True, equip=[E("band_anchor", post, eid="post", h=1.6), H("dumbbell", "R")])


@x("band-calf-raise")
def band_calf_raise(c, t, L, row):
    """The band under the balls of both feet, its handles held at the shoulders: rise onto the toes."""
    heel = L(0.0, 55.0)
    legs = {sd: dict(c.foot(SIDES[sd] * c.hw * 0.45, 0, 6), heel=heel) for sd in "LR"}

    def hand(D, Hp, c_, sd):
        return fam.shoulder(D, Hp, c, sd) + np.array([SIDES[sd] * 0.05, 0.12, -0.02])
    arms = arm_ik(hand, (0, 0, 1), lambda D, Hp, c_, sd: np.array([SIDES[sd] * 0.3, -0.2, -1]), curl=0.9)
    fr = c.stand(legs, hk=0.995, pel=(1, 0, 0), arms=arms, balance="com")

    def band(spec, eq, ex):
        def foot(sd):
            return lambda pts, D, Hp, cx: np.asarray(Hp[c.r.bi(f"toe1-1.{sd}")], float) + np.array([0, -0.02, -0.03])
        return [seg("bandL", foot("L"), ("gripL", (0, 0, 0)), 0.01, "band"), seg("bandR", foot("R"), ("gripR", (0, 0, 0)), 0.01, "band"),
                seg("bandF", foot("L"), foot("R"), 0.01, "band")]
    return _with_eq(fr, band)


@x("donkey-calf-raise")
def donkey_calf(c, t, L, row):
    """Balls of the feet on the edge of a step, hinged forward until the torso is nearly level with the hands on a
    bench in front: the heels sink and rise (side view)."""
    sh = 0.12
    heel = L(-20.0, 45.0)
    legs = {sd: dict(ball=np.array([SIDES[sd] * c.hw * 0.45, c.ball_y + 0.06, sh + SOLE]), yaw=4, heel=heel, surf=sh) for sd in "LR"}

    def hand(D, Hp, c_, sd):
        return np.array([SIDES[sd] * 0.2, 0.95 * c.S, 0.47])
    arms = arm_ik(hand, (-1, 0.2, 0), (0.2, -1, 0.2), key="palm", curl=0.1, fing=(0, 1, 0))
    return c.stand(legs, hk=0.97, pel=(78, 0, 0), neck=(-20, 0, 0), arms=arms, balance=None, reach=True,
                   equip=[E("step", (0, 0.04, 0), eid="step", height=sh), E("bench", (0, 1.05 * c.S, 0), R=rz(90), eid="bench")])


@x("shoulder-dislocates")
def dislocates(c, t, L, row):
    """A light stick in a very wide overhand grip, arms straight: it travels from the thighs up over the head
    to behind the back and returns (cycle)."""
    a = math.radians(-10 + 220 * (0.5 - 0.5 * math.cos(2 * math.pi * t)))

    def g(D, Hp, c_, sd):
        sh = fam.shoulder(D, Hp, c, sd)
        d = unit(np.array([SIDES[sd] * 0.75, math.sin(a), -math.cos(a)]))
        return sh + d * c.Lh * 0.97
    arms = arm_ik(g, lambda D, Hp, c_, sd: -X * SIDES[sd], lambda D, Hp, c_, sd: np.array([SIDES[sd], 0, 0]), curl=0.85)
    return _stand(c, t, L, arms=arms, equip=[_dowel(da=0.1, db=0.1)])


@x("band-overhead-shoulder-stretch")
def band_oh_stretch(c, t, L, row):
    """A band anchored above head height in the right hand: stepped back, the hips sit back and the torso
    lowers so the band draws the straight arm overhead."""
    anchor = np.array([0.0, 1.15 * c.S, 2.1])
    k = L(0.0, 1.0)

    def g(D, Hp, c_, sd):
        sh = fam.shoulder(D, Hp, c, "R")
        return sh + unit(anchor - sh) * c.Lh * 0.97
    armR = arm_ik(g, (0, 0, 1), (1, -0.3, 0), curl=0.9, sides="R")
    armL = arm_fk((0.15, 0.25, -1), elbow=20, sides="L")
    legs = c.feet(w=c.hw * 0.9, toe=8)
    fr = c.stand(legs, hk=L(0.995, 0.86), py=L(0.0, -0.08), pel=(L(5, 52), 0, 0), neck=(L(0, -20), 0, 0), arms=dict(armR, **armL),
                 balance="com", equip=[E("band_anchor", anchor * np.array([1, 1, 0]), eid="post", h=float(anchor[2]))])
    return _with_eq(fr, [seg("band", anchor, ("gripR", (0, 0, 0)), 0.009, "band")])


@x("wall-angel")
def wall_angel(c, t, L, row):
    """Back, hips and head against a wall, arms on the wall in a 'hands up' position with the elbows at 90
    degrees: the arms slide up overhead and back down (front-quarter view)."""
    u = L(0.0, 1.0)
    wy = -0.17

    def g(D, Hp, c_, sd):
        sh = fam.shoulder(D, Hp, c, sd)
        lo = sh + np.array([SIDES[sd] * 0.3, -0.06, 0.28])
        hi = sh + np.array([SIDES[sd] * 0.18, -0.06, c.Lh * 0.92])
        return lo * (1 - u) + hi * u
    arms = arm_ik(g, (0, -1, 0), lambda D, Hp, c_, sd: np.array([SIDES[sd], -0.4, -0.3 + 0.0 * u]), curl=0.2, fing=(0, 0, 1))
    legs = c.feet(w=c.hw * 0.9, toe=8, y=0.1)
    return c.stand(legs, hk=0.99, py=0.0, pel=(-3, 0, 0), arms=arms, balance=None, reach=True,
                   equip=[E("wall", (0, wy - 0.12, 0), eid="wall")])


@x("mini-band-triceps-press")
def mb_triceps_press(c, t, L, row):
    """A mini band looped between the hands in front of the chest, elbows bent: the hands press down and apart
    until the arms are straight."""
    u = L(0.0, 1.0)

    def g(D, Hp, c_, sd):
        Rb = D[c.r.bi("spine01")]
        sh = fam.shoulder(D, Hp, c, sd)
        a = sh + Rb @ np.array([-SIDES[sd] * 0.06, 0.32, -0.2])
        b = sh + Rb @ np.array([SIDES[sd] * 0.1, 0.3, -0.55])
        return a * (1 - u) + b * u
    arms = arm_ik(g, (0, 0, 1), lambda D, Hp, c_, sd: np.array([SIDES[sd] * 0.3, -1, -0.3]), curl=0.85)
    return _stand(c, t, L, arms=arms, equip=[seg("mbH", ("gripL", (0, 0, 0)), ("gripR", (0, 0, 0)), 0.012, "band")])


@x("band-single-arm-triceps-extension")
def band_oh_ext(c, t, L, row):
    """Standing on one end of a band, the other end in the right hand behind the head, elbow up by the ear: the
    forearm extends until the arm is straight overhead."""
    u = L(0.0, 1.0)
    armR = arm_fk((0.12, 0.05, 1.0), elbow=140 * (1 - u) + 4, bend=(0, -1, 0), thumb="fwd", curl=0.9, sides="R")
    armL = arm_fk((0.1, 0.05, -1), elbow=12, sides="L")
    legs = {"L": c.foot(-c.hw * 0.45, 0, 8), "R": c.foot(c.hw * 0.45, -0.05, 8)}
    fr = c.stand(legs, hk=0.995, pel=(2, 0, 0), arms=dict(armR, **armL), balance="com")

    def band(spec, eq, ex):
        foot = lambda pts, D, Hp, cx: np.asarray(Hp[c.r.bi("foot.R")], float) + np.array([0, -0.06, -0.06])
        return [seg("band", foot, ("gripR", (0, 0, 0)), 0.009, "band")]
    return _with_eq(fr, band)


@x("cuban-press", "dumbbell-cuban-shoulder-rotation")
def cuban(c, t, L, row):
    """Light dumbbells: an upright row to chest height (elbows high), the forearms rotate up so the weights sit
    above the elbows, then press overhead (cuban press); the rotation version stops after the turn."""
    press = row["key"] == "cuban-press"
    if press:
        K = [(0.0, dict(r=0.0, e=0.0, p=0.0)), (0.33, dict(r=1.0, e=0.0, p=0.0)), (0.66, dict(r=1.0, e=1.0, p=0.0)), (1.0, dict(r=1.0, e=1.0, p=1.0))]
    else:
        K = [(0.0, dict(r=1.0, e=0.0, p=0.0)), (1.0, dict(r=1.0, e=1.0, p=0.0))]
    kv = _interp(K, min(t, 0.9999))
    r, e, p = kv["r"], kv["e"], kv["p"]

    def arm(sd):
        def f(D, Hp, c_):
            Rb = D[c.r.bi("spine01")]
            s = SIDES[sd]
            if p > 0:
                ua = unit(np.array([s * (0.9 - 0.6 * p), 0.0, 0.1 + 0.9 * p]))
                return dict(ua=Rb @ ua, elbow=90 * (1 - p) + 6, bend=Rb @ unit(np.array([-s * 0.2 * (1 - p), 0, 1])), thumb=Rb @ -X * s, curl=0.85)
            ua = unit(np.array([s * (0.15 + 0.75 * r), 0.05, -1 + 1.0 * r]))
            # forearm: hanging down (rows) or turned up (externally rotated)
            bend = unit(np.array([0, 0.3 * (1 - e), -1 + 2 * e]))
            return dict(ua=Rb @ ua, elbow=8 + 82 * r, bend=Rb @ bend, thumb=Rb @ (-X * s), curl=0.85)
        return f
    return _stand(c, t, L, arms={"L": arm("L"), "R": arm("R")}, equip=[H("dumbbell", "L"), H("dumbbell", "R")])


# ================================================================== lying and kneeling
from .tpl_floor import supine_legs, supine_knees, palms_floor, quadruped, MAT  # noqa: E402
from .fam import legs_fk  # noqa: E402


@x("hug-knees-to-chest")
def hug_knees(c, t, L, row):
    """On the back, both knees drawn to the chest and hugged with the arms round the shins."""
    k = L(0.0, 1.0)
    legs = legs_fk((0.06, -0.25 - 0.45 * k, 0.95 - 0.25 * k), knee=125 + 20 * k, kbend=(0, 1, -1))
    arms = arm_ik(lambda D, Hp, c_, sd: c.J(D, Hp, f"lowerleg01.{sd}") + Z * 0.05 + Y * 0.06 + X * SIDES[sd] * 0.04,
                  (0, 1, 0), (1, 0, 0.5), curl=0.85)
    return supine_legs(c, legs, arms=arms, spine=(6 * k, 0, 0), neck=(6 * k, 0, 0))


@x("supine-spinal-twist")
def supine_twist(c, t, L, row):
    """On the back with the arms out to the sides, knees bent: both knees fall to one side toward the floor and
    the head turns the other way."""
    k = L(0.0, 1.0)
    a = math.radians(70 * k)
    th = (math.sin(a) * 0.75 + 0.03, -0.35, math.cos(a) * 0.95)
    legs = legs_fk(th, knee=100, kbend=(math.sin(a) * 0.4, 1, -math.cos(a)))
    arms = arm_fk((1.0, 0.0, 0.02), elbow=6, thumb="up", world=True)
    return fam.floor_body(c, pitch=-90, roll=-18 * k, legs=legs, arms=arms, spine=(0, 0, -10 * k), neck=(0, 0, -50 * k), equip=[MAT(0.1)])


@x("single-leg-glute-bridge-with-external-rotation")
def sl_bridge_er(c, t, L, row):
    """On the back, the right ankle crossed over the left knee with the right knee open: the left heel drives the
    hips up and lowers them."""
    def fig4(D):
        R0 = D[c.r.bi("root")]
        return dict(thigh=unit(R0 @ np.array([0.7, 0.6, -0.45])), knee=95, kbend=R0 @ np.array([-1, 0.0, -0.25]),
                    fdir=R0 @ np.array([-0.4, 0.5, -0.4]))
    fr = REG["glute_bridge"].fn(c, t, L, dict(row, name_en="Glute Bridge", equipment="mat ; supine"))
    b0 = fr.build

    def build():
        spec, eq, ex = b0()
        D, Hp = c.torso(spec)
        spec["leg"]["R"] = fig4(D)
        return spec, eq, ex
    fr.build = build
    fr.planted = ["L"]
    return fr


@x("leg-raises-with-stability-ball")
def leg_raise_ball(c, t, L, row):
    """On the back, a stability ball held between the ankles: the legs rise with soft knees to vertical and
    lower slowly."""
    a = math.radians(L(8, 86))
    legs = legs_fk((0.06, math.cos(a), math.sin(a)), knee=10, kbend=(0, 0, -1), fdir=(0, -math.sin(a), math.cos(a)))
    fr = supine_legs(c, legs, arms=palms_floor(c, -0.12))

    def ball(spec, eq, ex):
        return []
    b0 = fr.build

    def build():
        spec, eq, ex = b0()
        return spec, eq, ex
    fr.build = build
    # the ball sits between the feet (resolved after solving)
    return _with_eq(fr, [dict(kind="_ball_feet", id="sb")]) if False else _ball_between_feet(c, fr)


def _ball_between_feet(c, fr, r=0.3):
    """A stability ball held between the feet: placed after solving from both ankles."""
    def place(spec, D, Hp, ex, eqs):
        pass
    b0 = fr.build

    def build():
        spec, eq, ex = b0()
        D, Hp = c.torso(spec)
        # torso solve does not place the legs; estimate the ankles from the leg spec (FK legs: hip + thigh*T1 + shin*T2)
        dm = c.r.dims["R"]
        pts = []
        for sd in "LR":
            Lg = spec["leg"][sd]
            if "thigh" in Lg and Lg.get("thigh") is not None:
                hip = Hp[c.r.bi(f"upperleg01.{sd}")]
                th = unit(np.asarray(Lg["thigh"], float))
                pts.append(hip + th * (dm["T1"] + dm["T2"] * 0.95))
        if pts:
            m = np.mean(pts, axis=0)
            th = unit(np.asarray(spec["leg"]["L"]["thigh"], float))
            m = m + th * 0.08
            eq = list(eq) + [E("stability_ball", m - np.array([0, 0, r * 0.95]), eid="sb", dyn=True, r=r)]
        return spec, eq, ex
    fr.build = build
    return fr


@x("dragon-flag")
def dragon_flag(c, t, L, row):
    """Lying on a bench gripping its edge behind the head: the body, straight and rigid from the shoulders,
    lowers from nearly vertical to just above the bench."""
    bh = 0.44
    a = math.radians(L(80, 12))
    # pivot on the upper back at the head end of the bench; the whole body rotates as one line
    legs = legs_fk((0.04, math.cos(a), math.sin(a)), knee=4, kbend=(0, 0, -1), fdir=(0, -math.sin(a), math.cos(a)))

    def grip(D, Hp, c_, sd):
        return np.array([SIDES[sd] * 0.12, -0.62, bh - 0.02])
    arms = arm_ik(grip, (0, 0, 1), (SIDES["R"], 0.3, 1), curl=0.9)
    d = 0.5 * c.S
    S0 = np.array([0.0, -0.42, bh + 0.11])
    fr = fam.floor_body(c, pitch=-90 - math.degrees(a), legs=legs, arms=arms, py=S0[1] + d * math.cos(a), pz=S0[2] + d * math.sin(a),
                        equip=[E("bench", (0, -0.2, 0), eid="bench", height=bh)], settle=[("plane", np.array([0, -0.45, bh]), Z, X, 0.2, Y, 0.18, 0.01)])
    return fr


@x("band-leg-press")
def band_leg_press(c, t, L, row):
    """On the back, a band under both feet with the ends held at the chest: from knees to the chest the legs
    press out and up against it."""
    u = L(0.0, 1.0)
    a = math.radians(55 - 15 * u)
    legs = legs_fk((0.06, -0.2 * (1 - u) + math.cos(a) * u, 0.98 * (1 - u) + math.sin(a) * u), knee=120 * (1 - u) + 10,
                   kbend=(0, 1, -0.3) if u < 0.5 else (0, 0, -1), fdir=(0, 0.2, 1))
    arms = arm_ik(lambda D, Hp, c_, sd: c.lmk(D, Hp, "chest") + Z * 0.08 + X * SIDES[sd] * 0.12, (0, 1, 0), (1, 0, 0.3), curl=0.9)
    fr = supine_legs(c, legs, arms=arms)

    def band(spec, eq, ex):
        def foot(sd):
            return lambda pts, D, Hp, cx: np.asarray(Hp[c.r.bi(f"toe1-1.{sd}")], float) + np.array([0, 0.02, 0.0])
        return [seg("bandL", foot("L"), ("gripL", (0, 0, 0)), 0.009, "band"), seg("bandR", foot("R"), ("gripR", (0, 0, 0)), 0.009, "band"),
                seg("bandF", foot("L"), foot("R"), 0.009, "band")]
    return _with_eq(fr, band)


@x("lying-neck-extension")
def lying_neck_ext(c, t, L, row):
    """Face down along a bench with the head past its end: the head lowers gently and lifts back in line with the
    body (side view)."""
    bh = 0.44
    legs = legs_fk((0.06, -1.0, 0.0), knee=5, kbend=(0, 0, 1), fdir=(0, 0, -1))
    arms = arm_fk((0.35, 0.0, -1.0), elbow=20, thumb="fwd", world=True)
    fr = fam.floor_body(c, pitch=90, legs=legs, arms=arms, py=0.0, pz=bh + 0.12, neck=(L(40, -6), 0, 0),
                        equip=[E("bench", (0, -0.5, 0), eid="bench", height=bh)],
                        settle=[("plane", np.array([0, -0.5, bh]), Z, X, 0.2, Y, 0.55, 0.01)])
    return fr


@x("seated-spinal-twist")
def seated_twist(c, t, L, row):
    """Sitting tall with the left leg straight, the right foot outside the left knee: the torso turns right with
    the left elbow outside the right knee and the right hand behind on the floor."""
    k = L(0.0, 1.0)
    legs = {"L": legs_fk((-0.04, 1.0, -0.02), knee=3, kbend=(0, 0, -1), fdir=(0, -0.1, 1), sides="L")["L"],
            "R": legs_fk((-0.12, 0.6, 0.78), knee=125, kbend=(0, 0.2, -1), sides="R")["R"]}

    def elbow(D, Hp, c_, sd):
        return c.J(D, Hp, "lowerleg01.R") + np.array([0.12, 0.02, 0.0])
    armL = arm_ik(elbow, (0, 0, 1), (0, 1, 0), curl=0.6, sides="L")

    def behind(D, Hp, c_, sd):
        return np.array([0.18, -0.38, 0.004])
    armR = arm_ik(behind, (-1, 0, 0), (1, -0.3, 0.3), key="palm", curl=0.05, fing=(0.3, -1, 0), sides="R")
    return fam.floor_body(c, pitch=-4, legs=legs, arms=dict(armL, **armR), spine=(0, 0, -45 * k), neck=(0, 0, -25 * k), py=0.0, pz=0.12,
                          equip=[MAT(0.1)])


@x("kneeling-lat-stretch")
def kneeling_lat(c, t, L, row):
    """Kneeling in front of a bench, elbows on its edge and palms together behind the head: the hips push back
    and the chest sinks toward the floor."""
    k = L(0.0, 1.0)
    bh = 0.44
    bench_y = 0.75 * c.S

    def elb(D, Hp, c_, sd):
        return c.bp(D, Hp, "head", c.lm["nape"][1]) + np.array([SIDES[sd] * 0.04, -0.04, 0.02])
    arms = arm_ik(elb, lambda D, Hp, c_, sd: -Y, lambda D, Hp, c_, sd: np.array([SIDES[sd] * 0.3, 1, 0.2]), curl=0.2,
                  fing=lambda D, Hp, c_, sd: np.array([0, 0, 1]))
    fr = quadruped(c, t, L, row, arms_over=arms, sit_back=0.15 + 0.2 * k, neck=(10, 0, 0),
                   equip=[E("bench", (0, bench_y, 0), R=rz(90), eid="bench", height=bh)])
    return fr


@x("reach-behind-and-open")
def reach_open(c, t, L, row):
    """On all fours, the right hand behind the head: the elbow turns open toward the ceiling, the eyes following
    it, and back toward the left hand."""
    k = L(0.0, 1.0)

    def hand(D, Hp, c_):
        Rh = D[c.r.bi("head")]
        p = c.bp(D, Hp, "head", c.lm["nape"][1]) + Rh @ np.array([0.02, -0.03, 0.0])
        return dict(palm=p, thumb=Rh @ -Z, fing=Rh @ np.array([-1, 0, 0]), pole=D[c.r.bi("spine01")] @ np.array([1, 0, 0.3]), curl=0.2)
    return quadruped(c, t, L, row, arms_over={"R": hand}, spine=(0, 0, L(-15, 55)), neck=(-5, 0, L(-10, 35)))


@x("front-rack-stretch")
def front_rack_stretch(c, t, L, row):
    """Facing a wall, the right elbow high on the wall with that palm behind the shoulder, the left hand on the
    elbow: the chest leans gently toward the wall."""
    k = L(0.0, 1.0)
    wy = 0.3 * c.S
    armR = {"R": lambda D, Hp, c_: dict(ua=unit(np.array([0.15, 0.35, 1.0])), elbow=150, bend=unit(np.array([-0.2, -1, -0.2])), thumb="up", curl=0.3)}

    def on_elbow(D, Hp, c_, sd):
        return c.J(D, Hp, "lowerarm01.R") + np.array([-0.02, -0.04, -0.04])
    armL = arm_ik(on_elbow, (0, 0, 1), (-1, -0.3, -0.4), curl=0.4, sides="L")
    legs = c.feet(w=c.hw * 0.9, toe=8, y=-0.08)
    return c.stand(legs, hk=0.99, pel=(L(4, 14), 0, 0), spine=(L(0, 6), 0, 0), arms=dict(armR, **armL), balance="com",
                   equip=[E("wall", (0, wy + 0.12, 0), R=rz(180), eid="wall")])


@x("band-crunch")
def band_crunch(c, t, L, row):
    """Kneeling facing a band anchored high on a door, handles held beside the head: the torso curls down with
    the abs until the elbows near the thighs."""
    k = L(0.0, 1.0)
    anchor = np.array([0.0, 0.55 * c.S, 2.0])

    def g(D, Hp, c_, sd):
        return c.lmk(D, Hp, "forehead") + D[c.r.bi("head")] @ np.array([SIDES[sd] * 0.11, 0.0, -0.06])
    arms = arm_ik(g, lambda D, Hp, c_, sd: D[c.r.bi("head")] @ -Y, lambda D, Hp, c_, sd: np.array([SIDES[sd] * 0.4, 0.3, -1]), curl=0.9)
    T1 = c.r.dims["R"]["T1"]
    legs = {sd: dict(thigh=np.array([SIDES[sd] * 0.07, 0.15 * k, -1]), knee=92, kbend=np.array([0, -1, 0.0]), fdir=np.array([0, -1, -0.2]),
                     fup=np.array([0, 0.2, 1])) for sd in "LR"}
    fr = c.stand(legs, pz=T1 + 0.08, pel=(10 + 25 * k, 0, 0), spine=(40 * k, 0, 0), neck=(15 * k, 0, 0), arms=arms, balance=None,
                 reach=False, planted=(), equip=[MAT(0.0), E("wall", (0, anchor[1] + 0.1, 0), R=rz(180), eid="door")])
    fr.settle = [("floor", SKIN_FLOOR)]
    return _with_eq(fr, [seg("bandL", anchor, ("gripL", (0, 0, 0)), 0.009, "band"), seg("bandR", anchor, ("gripR", (0, 0, 0)), 0.009, "band")])


@x("bodyweight-kneeling-banded-deadlift")
def kneeling_banded_dl(c, t, L, row):
    """Kneeling on a mat with a band from a low anchor in front looped round the hips: the hips sit back toward
    the heels with the torso tipping forward, then drive forward to tall kneeling."""
    k = L(0.0, 1.0)
    T1 = c.r.dims["R"]["T1"]
    pz, py = T1 + 0.08 - 0.24 * k, -0.28 * k
    legs = {}
    for sd in "LR":
        hip = np.array([SIDES[sd] * 0.09, py, pz + 0.05])
        kn = np.array([SIDES[sd] * 0.1, 0.02, 0.07])
        d = unit(kn - hip)
        shin = np.array([0.0, -1.0, -0.02])
        flex = math.degrees(math.acos(max(-1.0, min(1.0, float(np.dot(d, shin))))))
        legs[sd] = dict(thigh=d, knee=flex, kbend=shin, fdir=np.array([0, -1, -0.2]), fup=np.array([0, 0.2, 1]))
    anchor = np.array([0.0, 0.95 * c.S, 0.15])
    fr = c.stand(legs, pz=pz, py=py, pel=(8 + 35 * k, 0, 0), arms=arm_fk((0.15, 0.25, -1), elbow=25), balance=None,
                 reach=False, planted=(), equip=[MAT(0.0), E("band_anchor", anchor * np.array([1, 1, 0]), eid="post", h=anchor[2])])
    fr.settle = [("floor", SKIN_FLOOR)]

    def band(spec, eq, ex):
        hip = lambda pts, D, Hp, cx: np.asarray(c.lmk(D, Hp, "hip_front"), float) + np.array([0, 0.03, 0])
        return [seg("band", anchor, hip, 0.012, "band")]
    return _with_eq(fr, band)


# ================================================================== lunges, standing legs (keyframes)
def _strap_arms(c, anchor, bent=0.15):
    def tgt(D, Hp, c_, sd):
        sh = fam.shoulder(D, Hp, c, sd)
        return sh + unit(anchor + X * SIDES[sd] * 0.12 - sh) * c.Lh * (1.0 - bent * 0.4)
    return arm_ik(tgt, (0, 0, 1), lambda D, Hp, c_, sd: np.array([SIDES[sd] * 0.6, -0.3, -0.6]), curl=0.9)


def _knee_up(sd, k):
    """Free leg spec with the knee driven up (0 = hanging, 1 = thigh level)."""
    return dict(thigh=unit(np.array([SIDES[sd] * 0.05, 0.05 + 0.95 * k, -1 + 1.0 * k])), knee=10 + 85 * k, kbend=np.array([0, -1, 0.0]),
                fdir=np.array([0, 1, -0.4]))


def _lunge_keys(c, depth=0.7, back=-0.72):
    w = c.hw * 0.5
    up = dict(fL=(-w, 0, 0), fR=(w, 0, 0), pz=c.pz * 0.98, py=0.0, pitch=4)
    bottom = dict(fL=(-w, 0, 0), fR=(w, back * c.S, 0), hR=70, pz=c.pz * (1 - 0.42 * depth), py=back * 0.32 * c.S, pitch=8)
    return up, bottom


def _keyed_free(c, kv, arms, equip, free=None):
    """keyed_stand with a free (FK) leg replacing a foot."""
    fr = keyed_stand(c, kv, equip=equip, arms=arms)
    if free:
        sd, spec_fn = free
        b0 = fr.build

        def build():
            spec, eq, ex = b0()
            spec["leg"][sd] = spec_fn
            return spec, eq, ex
        fr.build = build
        fr.planted = [s for s in fr.planted if s != sd]
    return fr


@x("suspension-reverse-lunge-to-knee-drive", "suspension-reverse-lunge-to-jump")
def susp_lunge_knee(c, t, L, row):
    """Facing the anchor holding the handles: the right foot steps back into a reverse lunge, then the body stands
    fast and drives the right knee up (the jump version leaves the floor off the front foot)."""
    jump = "jump" in row["key"]
    anchor = np.array([0.0, 1.35, 2.45])
    up, bottom = _lunge_keys(c)
    arms_d = dict(ua=(0.1, 0.6, 0.5), el=10)
    K = _keys([(0.0, dict(up, **arms_d)), (0.4, dict(bottom, **arms_d)), (0.7, dict(up, gR=0, **arms_d)),
               (0.85, dict(up, gR=0, gL=0 if jump else 1, pz=c.pz * 0.98 + (0.16 if jump else 0.0), hL=40 if jump else 0,
                           fL=(-c.hw * 0.5, 0, 0.14 if jump else 0), **arms_d)),
               (1.0, dict(up, gR=0, **arms_d))])
    kv = _interp(K, min(t, 0.9999))
    kup = 0.0
    if t > 0.45:
        kup = min(1.0, max(0.0, (t - 0.45) / 0.35)) if t < 0.95 else max(0.0, 1 - (t - 0.95) / 0.05)
    fr = _keyed_free(c, kv, _strap_arms(c, anchor), _handles(c, anchor), free=("R", _knee_up("R", kup)) if kup > 0.02 else None)
    return fr


@x("suspension-crossing-balance-lunge")
def susp_cross_lunge(c, t, L, row):
    """Facing the anchor holding the handles: the right foot steps diagonally behind the left (curtsy) and the
    body lowers, then stands and lifts the right knee to balance (cycle)."""
    anchor = np.array([0.0, 1.35, 2.45])
    w = c.hw * 0.5
    arms_d = dict(ua=(0.1, 0.6, 0.5), el=10)
    up = dict(fL=(-w, 0, 0), fR=(w, 0, 0), pz=c.pz * 0.98, py=0.0, pitch=4, **arms_d)
    cross = dict(fL=(-w, 0, 0), fR=(-w - 0.32 * c.S, -0.55 * c.S, 0), hR=70, pz=c.pz * 0.7, py=-0.15, px=-0.08, pitch=10, **arms_d)
    K = _keys([(0.0, up), (0.4, cross), (0.7, dict(up, gR=0)), (1.0, up)])
    kv = _interp(K, min(t, 0.9999))
    kup = math.sin(math.pi * min(1.0, max(0.0, (t - 0.55) / 0.45)))
    return _keyed_free(c, kv, _strap_arms(c, anchor), _handles(c, anchor), free=("R", _knee_up("R", kup)) if kup > 0.02 else None)


@x("mini-band-lunge-kickback")
def mb_lunge_kick(c, t, L, row):
    """A mini band round the ankles: a reverse lunge, then standing on the front leg the back leg kicks straight
    back against the band (cycle)."""
    up, bottom = _lunge_keys(c)
    arms_d = dict(ua=(0.15, 0.2, -0.9), el=70)
    K = _keys([(0.0, dict(up, **arms_d)), (0.4, dict(bottom, **arms_d)), (0.7, dict(up, gR=0, pitch=14, **arms_d)), (1.0, dict(up, **arms_d))])
    kv = _interp(K, min(t, 0.9999))
    kk = math.sin(math.pi * min(1.0, max(0.0, (t - 0.55) / 0.45)))
    kick = dict(thigh=unit(np.array([0.05, -0.55 * kk, -1])), knee=6, kbend=np.array([0, -1, 0]), fdir=np.array([0, 0.4, -1]))
    return _keyed_free(c, kv, None, [], free=("R", kick) if kk > 0.02 else None)


@x("lunge-to-hamstring-stretch")
def lunge_ham(c, t, L, row):
    """Low lunge with the back knee down and the hands beside the front foot: the hips shift forward (hip flexor),
    then back as the front leg straightens with the toes up (hamstring) (cycle)."""
    T1 = c.r.dims["R"]["T1"]
    fy = 0.62 * c.S
    K = [(0.0, dict(f=0.0)), (0.35, dict(f=1.0)), (0.75, dict(f=-1.0)), (1.0, dict(f=0.0))]
    f = _interp(K, min(t, 0.9999))["f"]
    fwd, back = max(0.0, f), max(0.0, -f)
    py = 0.18 * c.S + 0.08 * fwd - 0.32 * back
    pz = T1 * 0.85 - 0.05 * fwd + 0.06 * back
    knee_r = np.array([c.hw * 0.4, py - 0.38 * c.S * (1 - 0.3 * back), 0.07])
    front = dict(ball=np.array([-c.hw * 0.45, fy + c.ball_y, SOLE]), yaw=4, heel=-25 * back, surf=0.0)
    hipR = np.array([c.hw * 0.45, py, pz])
    d = unit(knee_r - hipR)
    shin = np.array([0.0, -1.0, -0.03])
    flex = math.degrees(math.acos(max(-1.0, min(1.0, float(np.dot(d, shin))))))
    legs = {"L": front, "R": dict(thigh=d, knee=flex, kbend=shin, fdir=np.array([0, -1, -0.2]), fup=np.array([0, 0.2, 1]))}

    def palm(D, Hp, c_, sd):
        return np.array([-c.hw * 0.45 + SIDES[sd] * 0.2, fy - 0.05, 0.004])
    arms = arm_ik(palm, (-1, 0.2, 0), (0.2, -1, 0.3), key="palm", curl=0.05, fing=(0, 1, 0))
    return c.stand(legs, pz=pz, py=py, pel=(55 + 25 * back - 10 * fwd, 0, 0), neck=(-25, 0, 0), arms=arms, balance=None, reach=True,
                   planted=("L",), equip=[MAT(0.2)])


@x("lunge-with-ankle-grab", "couch-stretch")
def lunge_ankle(c, t, L, row):
    """Half kneeling on the right knee: the right hand holds the back ankle (couch stretch: the back shin rests up
    against a wall) and the torso rises upright, hips pressing forward."""
    couch = row["key"] == "couch-stretch"
    k = L(0.0, 1.0)
    T1 = c.r.dims["R"]["T1"]
    fy = 0.55 * c.S
    py = 0.1 * c.S + 0.06 * k
    pz = T1 * 0.95 + 0.05
    knee_r = np.array([c.hw * 0.4, py - 0.18, 0.07])
    hipR = np.array([c.hw * 0.45, py, pz])
    d = unit(knee_r - hipR)
    shin = unit(np.array([0.0, -0.25, 1.0]))        # the shin rises behind (foot toward the glutes)
    flex = math.degrees(math.acos(max(-1.0, min(1.0, float(np.dot(d, shin))))))
    legs = {"L": dict(ball=np.array([-c.hw * 0.45, fy + c.ball_y, SOLE]), yaw=4, heel=0, surf=0.0),
            "R": dict(thigh=d, knee=flex, kbend=shin, fdir=np.array([0, -0.3, 1]), fup=np.array([0, -1, 0.2]))}
    armR = arm_ik(lambda D, Hp, c_, sd: c.J(D, Hp, "foot.R") + np.array([0.05, 0.02, 0.02]), (0, 0, 1), (1, -0.3, -0.2), curl=0.9, sides="R")
    armL = arm_ik(lambda D, Hp, c_, sd: c.J(D, Hp, "lowerleg01.L") + np.array([-0.02, 0.0, 0.08]), (-1, 0.2, 0), (-0.2, -1, 0.3), key="palm",
                  curl=0.1, fing=(0, 1, -0.2), sides="L")
    eq = [MAT(0.1)]
    if couch:
        eq.append(E("wall", (0, py - 0.36 - 0.12, 0), eid="wall"))
        armR = arm_fk((0.2, 0.1, -1), elbow=15, sides="R")
    fr = c.stand(legs, pz=pz, py=py, pel=(L(28, 2), 0, 0), spine=(L(10, -6), 0, 0), arms=dict(armR, **armL), balance=None, reach=True,
                 planted=("L",), equip=eq)
    return fr


@x("knee-to-wall-ankle-mobilization")
def knee_wall(c, t, L, row):
    """Half kneeling facing a wall with the front toes about 10 cm from it: the front knee drives forward to touch
    the wall while the heel stays down (side view)."""
    k = L(0.0, 1.0)
    T1 = c.r.dims["R"]["T1"]
    fy = 0.45 * c.S
    py = 0.0 + 0.1 * k
    pz = T1 * 0.95 + 0.04
    knee_r = np.array([c.hw * 0.4, py - 0.2, 0.07])
    hipR = np.array([c.hw * 0.45, py, pz])
    d = unit(knee_r - hipR)
    shin = np.array([0.0, -1.0, -0.03])
    flex = math.degrees(math.acos(max(-1.0, min(1.0, float(np.dot(d, shin))))))
    legs = {"L": dict(ball=np.array([-c.hw * 0.45, fy + c.ball_y, SOLE]), yaw=0, heel=0, surf=0.0),
            "R": dict(thigh=d, knee=flex, kbend=shin, fdir=np.array([0, -1, -0.2]), fup=np.array([0, 0.2, 1]))}

    def wallhand(D, Hp, c_, sd):
        return np.array([SIDES[sd] * 0.2, fy + 0.22, 0.95])
    arms = arm_ik(wallhand, (0, -1, 0), (1, -0.3, -0.5), key="palm", curl=0.1, fing=(0, 0, 1))
    return c.stand(legs, pz=pz, py=py, pel=(8, 0, 0), arms=arms, balance=None, reach=True, planted=("L",),
                   equip=[MAT(0.0), E("wall", (0, fy + 0.25 + 0.12, 0), R=rz(180), eid="wall")])


@x("deficit-calf-stretch")
def deficit_calf(c, t, L, row):
    """Balls of the feet on the edge of a step, hand on a rail: the weight shifts to the right foot and its heel
    sinks below the step."""
    sh = 0.18
    heel = L(0.0, -32.0)
    legs = {"L": dict(ball=np.array([-c.hw * 0.45, c.ball_y + 0.05, sh + SOLE]), yaw=6, heel=0, surf=sh),
            "R": dict(ball=np.array([c.hw * 0.45, c.ball_y + 0.05, sh + SOLE]), yaw=6, heel=heel, surf=sh)}
    armR = arm_ik(lambda D, Hp, c_, sd: np.array([0.45, 0.15, 1.0]), (0, 0, 1), (1, -0.3, -0.5), curl=0.9, sides="R")
    armL = arm_fk((0.12, 0.05, -1), elbow=12, sides="L")
    return c.stand(legs, hk=0.99, px=0.03, pel=(2, 0, 0), arms=dict(armR, **armL), balance=None, reach=True,
                   equip=[E("step", (0, 0.06, 0), eid="step", height=sh), E("rail", (0.45, 0.25, 0), eid="rail", h=1.0)])


@x("single-leg-cycles")
def sl_cycles(c, t, L, row):
    """Side-on to a wall holding it with the left hand: the right leg runs in a circle — knee up and forward, foot
    out, claw back under the body, heel to the glutes (cycle)."""
    a = 2 * math.pi * t
    th = unit(np.array([0.04, 0.35 + 0.55 * math.cos(a), -1 + 0.55 * (0.5 + 0.5 * math.cos(a))]))
    knee = 60 + 50 * math.sin(a + 0.6)
    leg = dict(thigh=th, knee=knee, kbend=np.array([0, -1, 0]), fdir=np.array([0, 1, -0.4]))
    armL = arm_ik(lambda D, Hp, c_, sd: np.array([-0.55, 0.05, 1.15]), (0, 1, 0), (-1, -0.3, -0.4), key="palm", curl=0.1, fing=(0, 0, 1), sides="L")
    armR = arm_fk((0.15, 0.1, -1), elbow=60, sides="R")
    legs = {"L": c.foot(-c.hw * 0.3, 0, 6), "R": leg}
    return c.stand(legs, hk=0.99, pel=(4, 0, 0), arms=dict(armL, **armR), planted=("L",), balance="com",
                   equip=[E("wall", (-0.68 - 0.12, 0, 0), R=rz(90), eid="wall")])


@x("duck-walk")
def duck_walk(c, t, L, row):
    """Deep squat, torso upright, hands forward: short steps forward without rising (cycle: right step, left step)."""
    w = c.hw * 0.7
    s = 0.22 * c.S
    z = c.pz * 0.5
    arms_d = dict(ua=(0.15, 0.95, -0.1), el=10)
    K = _keys([(0.0, dict(fL=(-w, 0, 0), fR=(w, 0, 0), pz=z, py=0.04, pitch=22, **arms_d)),
               (0.25, dict(fL=(-w, 0, 0), fR=(w, s * 0.5, 0.06), gR=0, pz=z + 0.02, py=s * 0.2, px=-0.04, pitch=22, **arms_d)),
               (0.5, dict(fL=(-w, 0, 0), fR=(w, s, 0), pz=z, py=s * 0.5 + 0.04, pitch=22, **arms_d)),
               (0.75, dict(fL=(-w, s * 0.5, 0.06), fR=(w, s, 0), gL=0, pz=z + 0.02, py=s * 0.7, px=0.04, pitch=22, **arms_d)),
               (1.0, dict(fL=(-w, s, 0), fR=(w, s, 0), pz=z, py=s + 0.04, pitch=22, **arms_d))], {"hL": 25, "hR": 25})
    kv = _interp(K, min(t, 0.9999))
    return keyed_stand(c, kv)


@x("squat-side-kick")
def squat_side_kick(c, t, L, row):
    """Hands at the chest: a squat, then standing on the left leg the right leg kicks out to the side; back into
    the next squat (front view, alternating)."""
    w = c.hw * 0.75
    arms_d = dict(ua=(0.2, 0.6, -0.4), el=130)
    K = _keys([(0.0, dict(fL=(-w, 0, 0), fR=(w, 0, 0), pz=c.pz * 0.98, pitch=4, **arms_d)),
               (0.45, dict(fL=(-w, 0, 0), fR=(w, 0, 0), pz=c.pz * 0.66, pitch=26, **arms_d)),
               (0.75, dict(fL=(-w, 0, 0), fR=(w, 0, 0.1), gR=0, pz=c.pz * 0.98, px=-0.08, pitch=6, **arms_d)),
               (1.0, dict(fL=(-w, 0, 0), fR=(w, 0, 0), pz=c.pz * 0.98, pitch=4, **arms_d))])
    kv = _interp(K, min(t, 0.9999))
    kk = math.sin(math.pi * min(1.0, max(0.0, (t - 0.55) / 0.45)))
    kick = dict(thigh=unit(np.array([0.95 * kk + 0.08, 0.05, -1 + 0.6 * kk])), knee=6, kbend=np.array([0, -1, 0]),
                fdir=np.array([0.2, 1, 0.1]))
    fr = _keyed_free(c, kv, None, [], free=("R", kick) if kk > 0.03 else None)
    return fr


@x("walking-front-kick")
def walking_front_kick(c, t, L, row):
    """Arms forward: the right leg kicks straight up in front and the left hand reaches toward its toes, then the
    foot lands a step ahead (cycle of one kick)."""
    kk = math.sin(math.pi * t)
    leg = dict(thigh=unit(np.array([0.04, 0.05 + 1.0 * kk, -1 + 1.35 * kk])), knee=6, kbend=np.array([0, -1, 0]), fdir=np.array([0, 0.3, 1]))

    def reachL(D, Hp, c_, sd):
        sh = fam.shoulder(D, Hp, c, "L")
        fwd = sh + np.array([0.12, 0.65, -0.1])
        toe = c.J(D, Hp, "foot.R") + np.array([-0.04, 0.12, 0.06])
        p = fwd * (1 - kk) + toe * kk
        d = p - sh
        return sh + unit(d) * min(np.linalg.norm(d), c.Lh * 0.97)
    armL = arm_ik(reachL, (0, 0, 1), (-0.5, -0.3, -1), curl=0.3, sides="L")
    armR = arm_fk((0.25, 0.9, 0.0), elbow=8, sides="R")
    legs = {"L": c.foot(-c.hw * 0.3, 0, 6), "R": leg}
    return c.stand(legs, hk=0.99, pel=(6 + 8 * kk, 0, 0), spine=(8 * kk, 0, -10 * kk), arms=dict(armL, **armR), planted=("L",), balance="com")


@x("power-skip")
def power_skip(c, t, L, row):
    """A skip: a short hop on the left foot while the right knee and the left arm drive up hard (flight, side
    view)."""
    kk = math.sin(math.pi * t)
    leg = _knee_up("R", kk)
    z = c.pz * 0.98 + 0.22 * kk
    legs = {"L": dict(c.foot(-c.hw * 0.3, 0, 6), ball=np.array([-c.hw * 0.3, c.ball_y, SOLE + 0.2 * kk]), heel=40 * kk), "R": leg}
    armL = arm_fk((0.12, 0.2 + 0.8 * kk, -1 + 1.4 * kk), elbow=90, sides="L")
    armR = arm_fk((0.12, -0.5 * kk, -1), elbow=80, sides="R")
    return c.stand(legs, pz=z, pel=(8, 0, 0), arms=dict(armL, **armR), planted=("L",) if kk < 0.2 else (), balance=None, reach=kk < 0.2)


@x("balance-trainer-alternating-lunge-jump")
def bt_lunge_jump(c, t, L, row):
    """Split stance with the front foot on the dome: jump, switch legs in the air and land with the other foot
    on the dome (cycle, side view)."""
    w = c.hw * 0.5
    fy, by = 0.36 * c.S, -0.5 * c.S
    low = c.pz * 0.62 + DOME * 0.5
    arms_a = dict(ua=(0.12, 0.6, -0.5), el=70)
    K = _keys([(0.0, dict(fL=(-w, fy, DOME), sL=DOME, fR=(w, by, 0), hR=70, pz=low, py=0.0, pitch=6, **arms_a)),
               (0.25, dict(fL=(-w, 0.1, DOME + 0.2), fR=(w, -0.05, 0.25), gL=0, gR=0, pz=c.pz * 0.95 + 0.25, py=0.0, pitch=4, ua=(0.12, 0.2, 0.6), el=40)),
               (0.5, dict(fL=(-w, by, 0), hL=70, fR=(w, fy, DOME), sR=DOME, pz=low, py=0.0, pitch=6, **arms_a)),
               (0.75, dict(fL=(-w, -0.05, 0.25), fR=(w, 0.1, DOME + 0.2), gL=0, gR=0, pz=c.pz * 0.95 + 0.25, py=0.0, pitch=4, ua=(0.12, 0.2, 0.6), el=40)),
               (1.0, dict(fL=(-w, fy, DOME), sL=DOME, fR=(w, by, 0), hR=70, pz=low, py=0.0, pitch=6, **arms_a))])
    kv = _interp(K, min(t, 0.9999))
    return keyed_stand(c, kv, equip=[E("bosu", (0, fy - 0.04, 0), eid="bosu")])


# ================================================================== cardio machines
@x("stair-climber")
def stair_climber_m(c, t, L, row):
    """On the stair climber, hands light on the rails: the feet climb the moving steps one after the other (cycle)."""
    w = c.hw * 0.5
    st = lambda k: (-0.4 + 0.2 * k, 0.15 + 0.2 * k + 0.02)
    y1, z1 = st(1)
    y2, z2 = st(2)
    base = c.pz * 0.97
    rails = lambda D, Hp, c_, sd: np.array([SIDES[sd] * 0.36, 0.05, 1.05])
    arms = arm_ik(rails, (0, 0, 1), (0.6, -0.3, -1), curl=0.6)
    K = _keys([(0.0, dict(fL=(-w, y1, z1), sL=z1, fR=(w, y2, z2), sR=z2, pz=base + z1 + 0.08, py=y1 + 0.08, pitch=10)),
               (0.5, dict(fL=(-w, y2, z2), sL=z2, fR=(w, y1, z1), sR=z1, pz=base + z1 + 0.08, py=y1 + 0.08, pitch=10)),
               (1.0, dict(fL=(-w, y1, z1), sL=z1, fR=(w, y2, z2), sR=z2, pz=base + z1 + 0.08, py=y1 + 0.08, pitch=10))])
    kv = _interp(K, min(t, 0.9999))
    for sd, ph in (("L", 0.0), ("R", 0.5)):     # the stepping foot lifts over the step edge
        q = (t - ph) % 1.0
        if q < 0.5:
            kv["f" + sd] = np.asarray(kv["f" + sd], float) + np.array([0, 0, 0.07 * math.sin(math.pi * q / 0.5)])
            kv["g" + sd] = 0.0
    kv.update(ua=(0.1, 0.1, -1), el=20)
    return keyed_stand(c, kv, arms=arms, equip=[E("stair_climber", (0, 0, 0), eid="sc")])


@x("ski-ergometer")
def ski_erg_m(c, t, L, row):
    """Facing the ski erg, both handles held overhead: the arms pull down while the hips hinge and the knees bend,
    hands finishing by the thighs; then back up (rep)."""
    u = L(0.0, 1.0)
    legs = c.feet(w=c.hw * 0.8, toe=6, y=-0.55)
    top = lambda sd: np.array([SIDES[sd] * 0.09, -0.12, 1.95])

    def g(D, Hp, c_, sd):
        sh = fam.shoulder(D, Hp, c, sd)
        up = sh + unit(np.array([SIDES[sd] * 0.1, 0.45, 1.0])) * c.Lh * 0.96
        Rb = D[c.r.bi("spine01")]
        low = c.lmk(D, Hp, "hip_front") + Rb @ np.array([SIDES[sd] * 0.2, 0.18, -0.1])
        return up * (1 - u) + low * u
    arms = arm_ik(g, (0, 0, 1), lambda D, Hp, c_, sd: np.array([SIDES[sd] * 0.5, -0.3, -0.8]), curl=0.9)
    fr = c.stand(legs, hk=0.99 - 0.12 * u, py=-0.55 - 0.05 * u, pel=(4 + 42 * u, 0, 0), arms=arms, balance=None, reach=True,
                 equip=[E("ski_erg", (0, -0.0, 0), eid="erg")])
    return _with_eq(fr, [seg("cordL", np.array([-0.04, 0.0, 1.9]), ("gripL", (0, 0, 0)), 0.006, "darksteel"),
                         seg("cordR", np.array([0.04, 0.0, 1.9]), ("gripR", (0, 0, 0)), 0.006, "darksteel")])


@x("recumbent-bike", "air-bike")
def bikes(c, t, L, row):
    """Recumbent: reclined against the backrest, hands on the side handles, pedalling in front (cycle).
    Air bike: upright, the moving arm handles pushed and pulled in time with the pedals (cycle)."""
    if row["key"] == "air-bike":
        fr = REG["bike"].fn(c, t, L, row)
        a = 2 * math.pi * t

        def handle(sd, ph):
            return np.array([SIDES[sd] * 0.24, 0.3 + 0.12 * math.cos(ph), 1.12])
        hands = {"R": handle("R", a), "L": handle("L", a + math.pi)}
        arms = arm_ik(lambda D, Hp, c_, sd: hands[sd], (0, 0, 1), (0.4, -1, -0.5), curl=0.9)
        b0 = fr.build

        def build():
            spec, eq, ex = b0()
            D, Hp = c.torso(spec)
            for sd in "LR":
                spec["arm"][sd] = arms[sd](D, Hp, c)
            eq = list(eq) + [seg(f"lever{sd}", np.array([SIDES[sd] * 0.22, 0.32, 0.42]), hands[sd] + np.array([0, 0, -0.03]), 0.02, "frame") for sd in "LR"]
            return spec, eq, ex
        fr.build = build
        return fr
    crank = np.array([0, 0.62, 0.45])
    a = 2 * math.pi * t
    seat = np.array([0, -0.25, 0.56])
    legs = {}
    for sd, ph in (("R", a), ("L", a + math.pi)):
        p = crank + np.array([SIDES[sd] * 0.13, 0.17 * math.cos(ph), 0.17 * math.sin(ph)])
        legs[sd] = dict(ankle=p + np.array([0, -0.09, 0.05]), fdir=np.array([0, 0.3, 1.0]), fup=np.array([0, -1, 0.3]),
                        pole=np.array([SIDES[sd] * 0.1, 0.3, 1.0]))
    arms = arm_ik(lambda D, Hp, c_, sd: np.array([SIDES[sd] * 0.3, -0.2, 0.6]), (0, 1, 0), (0.6, 0, 1), curl=0.9)
    return c.stand(legs, pz=seat[2] + 0.1, py=seat[1], pel=(-24, 0, 0), arms=arms, balance=None, reach=False, planted=(),
                   equip=[E("recumbent", (0, 0, 0), eid="rb")],
                   settle=[("plane", seat + np.array([0, 0, 0.04]), Z, X, 0.1, Y, 0.14, 0.01, "pelvis")])


# ================================================================== one-arm rows and the cable kickback
def _row_one(c, t, L, stance, src, palm_up=False, kneel=False):
    """One-arm row of a handle from a point in front (src): the right elbow drives back to the hip."""
    u = L(0.0, 1.0)

    def g(D, Hp, c_, sd):
        sh = fam.shoulder(D, Hp, c, "R")
        reach = sh + unit(src - sh) * c.Lh * 0.98
        Rb = D[c.r.bi("spine01")]
        rowed = sh + Rb @ np.array([0.1, -0.02, -0.33])
        return reach * (1 - u) + rowed * u
    thumb = (lambda D, Hp, c_, sd: D[c.r.bi("spine01")] @ unit(np.array([0, 0.2, 1]) * (1 - u) + np.array([1, 0, 0]) * u)) if palm_up else (0, 0, 1)
    armR = arm_ik(g, thumb, (0.5, -0.4, -1), curl=0.9, sides="R")
    armL = arm_fk((0.15, 0.3, -1), elbow=40, sides="L")
    if kneel:
        T1 = c.r.dims["R"]["T1"]
        legs = {"R": dict(ball=np.array([-c.hw * 0.4, 0.42 * c.S + c.ball_y, SOLE]), yaw=4, heel=0),
                "L": dict(thigh=unit(np.array([0.08, -0.2, -1])), knee=92, kbend=np.array([0, -1, 0]), fdir=np.array([0, -1, -0.2]), fup=np.array([0, 0.2, 1]))}
        # left knee down, right foot forward (opposite foot forward to the rowing arm)
        legs = {"L": dict(ball=np.array([-c.hw * 0.45, 0.42 * c.S + c.ball_y, SOLE]), yaw=4, heel=0),
                "R": dict(thigh=unit(np.array([0.06, -0.2, -1])), knee=92, kbend=np.array([0, -1, 0]), fdir=np.array([0, -1, -0.2]), fup=np.array([0, 0.2, 1]))}
        fr = c.stand(legs, pz=T1 + 0.1, py=0.05, pel=(8 + 4 * u, 0, L(0, 14)), spine=(0, 0, L(-12, 10)), arms=dict(armR, **armL), balance=None,
                     reach=True, planted=("L",), equip=[MAT(0.1)])
        return fr
    legs = stance
    return c.stand(legs, hk=0.96, pel=(L(28, 18), 0, L(-6, 12)), spine=(0, 0, L(-14, 10)), arms=dict(armR, **armL), balance="com")


@x("single-arm-band-row")
def sa_band_row(c, t, L, row):
    """A band anchored at waist height in front, the end in the right hand: the elbow drives back until the hand
    reaches the side."""
    anchor = np.array([0.0, 1.25 * c.S, 1.0])
    fr = _row_one(c, t, L, c.feet(w=c.hw * 0.9, toe=8), anchor)
    return _with_eq(fr, [E("band_anchor", anchor * np.array([1, 1, 0]), eid="post", h=float(anchor[2])),
                         seg("band", anchor, ("gripR", (0, 0, 0)), 0.009, "band")])


@x("shotgun-row", "half-kneeling-shotgun-row")
def shotgun_row(c, t, L, row):
    """A low cable handle in the right hand with the left foot forward (or half kneeling on the right knee): reach
    forward to stretch the lat, then drive the elbow back to the hip turning the palm up."""
    kneel = "kneeling" in row["key"]
    pul = np.array([0.0, 1.35 * c.S, 0.35 if not kneel else 0.5])
    stance = {"L": c.foot(-c.hw * 0.45, 0.25 * c.S, 6), "R": dict(c.foot(c.hw * 0.45, -0.3 * c.S, 10), heel=45)}
    fr = _row_one(c, t, L, stance, pul, palm_up=True, kneel=kneel)
    return _with_eq(fr, [E("cable_tower", np.array([0.0, pul[1] + 0.12, 0.0]), R=rz(180), eid="tower", pulley_h=float(pul[2])),
                         seg("cable", pul, ("gripR", (0, 0, 0)), 0.005, "darksteel")])


@x("cable-glute-kickback")
def cable_kickback(c, t, L, row):
    """Facing the cable machine holding its frame with both hands, an ankle strap on the right ankle from the low
    pulley: hinged slightly forward, the right leg drives back and up."""
    u = L(0.0, 1.0)
    tower_y = 0.75 * c.S
    leg = dict(thigh=unit(np.array([0.05, -0.75 * u + 0.05, -1])), knee=8 + 6 * u, kbend=np.array([0, -1, 0]), fdir=np.array([0, 0.3, -1]))
    arms = arm_ik(lambda D, Hp, c_, sd: np.array([SIDES[sd] * 0.18, tower_y - 0.12, 1.15]), (0, 0, 1), (0.5, -0.4, -1), curl=0.9)
    legs = {"L": c.foot(-c.hw * 0.3, 0, 6), "R": leg}
    fr = c.stand(legs, hk=0.97, pel=(L(14, 22), 0, 0), arms=arms, planted=("L",), balance="com",
                 equip=[E("cable_tower", np.array([0.0, tower_y + 0.1, 0.0]), R=rz(180), eid="tower", pulley_h=0.12)])
    ank = lambda pts, D, Hp, cx: np.asarray(Hp[c.r.bi("foot.R")], float) + np.array([0, 0.02, 0.05])
    return _with_eq(fr, [seg("cable", np.array([0.0, tower_y - 0.02, 0.12]), ank, 0.005, "darksteel")])


# ================================================================== small implements, machines
@x("wrist-roller")
def wrist_roller_m(c, t, L, row):
    """Arms straight out in front at shoulder height holding the roller bar overhand: the wrists turn one after the
    other, winding the cord until the plate rises (cycle)."""
    a = 2 * math.pi * t

    def g(D, Hp, c_, sd):
        sh = fam.shoulder(D, Hp, c, sd)
        return sh + np.array([-SIDES[sd] * 0.06, c.Lh * 0.95, -0.04])
    curls = {sd: 0.85 for sd in "LR"}
    armsik = arm_ik(g, (0, 0, 1), lambda D, Hp, c_, sd: np.array([SIDES[sd] * 0.4, -0.2, -1]), curl=0.85,
                    fing=lambda D, Hp, c_, sd: np.array([0, 0.4 * math.cos(a + (0 if sd == "R" else math.pi)), -1]))
    fr = _stand(c, t, L, arms=armsik)
    drop = 0.55 - 0.25 * t

    def roller(spec, eq, ex):
        mid = lambda pts, D, Hp, cx: 0.5 * (np.asarray(pts["gripL"], float) + np.asarray(pts["gripR"], float))
        low = lambda pts, D, Hp, cx: mid(pts, D, Hp, cx) - np.array([0, 0, drop])
        return [_dowel(da=0.04, db=0.04), seg("cord", mid, low, 0.004, "rope"),
                seg("plate", lambda p, D, Hp, cx: low(p, D, Hp, cx) + np.array([0, -0.012, -0.1]), lambda p, D, Hp, cx: low(p, D, Hp, cx) + np.array([0, 0.012, -0.1]), 0.1, "rubber")]
    return _with_eq(fr, roller)


@x("finger-curl")
def finger_curl(c, t, L, row):
    """Standing, a barbell held palms up at the thighs: the bar rolls down to the fingertips and the fingers curl
    it back into the palms, then the wrists curl up."""
    u = L(0.0, 1.0)
    fr = _stand(c, t, L, hold="bar_hang_sup")
    b0 = fr.build

    def build():
        spec, eq, ex = b0()
        for sd, A in spec.get("arm", {}).items():
            if isinstance(A, dict):
                A["curl"] = 0.95 * u + 0.25
        return spec, eq, ex
    fr.build = build
    return fr


@x("hand-gripper")
def hand_gripper(c, t, L, row):
    """Standing, the forearm bent in front with a hand gripper in the right hand: the hand squeezes the handles
    together and opens slowly."""
    u = L(0.0, 1.0)
    armR = arm_fk((0.15, 0.25, -1), elbow=95, bend=(0, 1, 0.2), thumb="up", curl=0.4 + 0.55 * u, sides="R")
    armL = arm_fk((0.1, 0.05, -1), elbow=12, sides="L")
    return _stand(c, t, L, arms=dict(armR, **armL), equip=[H("gripper", "R", off=(0, 0, 0.04))])


@x("plate-flips")
def plate_flips(c, t, L, row):
    """A light plate pinched by its top rim in front of the thigh: a small toss turns it half a rotation and the
    hand catches it by the rim again (cycle)."""
    a = math.pi * t
    hop = 0.12 * math.sin(math.pi * t)
    armR = arm_fk((0.08, 0.35 + 0.2 * math.sin(math.pi * t), -1), elbow=25 + 25 * math.sin(math.pi * t), thumb="fwd", curl=0.5, sides="R")
    armL = arm_fk((0.1, 0.05, -1), elbow=12, sides="L")
    fr = _stand(c, t, L, arms=dict(armR, **armL))

    def plate(spec, eq, ex):
        def ctr(pts, D, Hp, cx, s):
            g = np.asarray(pts["gripR"], float)
            c0 = g + np.array([0, 0.0, -0.14 + hop])
            ax = np.array([0, math.cos(a), math.sin(a)]) * 0.03 * s
            return c0 + ax
        return [seg("plate", lambda p, D, Hp, cx: ctr(p, D, Hp, cx, 1), lambda p, D, Hp, cx: ctr(p, D, Hp, cx, -1), 0.14, "rubber")]
    return _with_eq(fr, plate)


@x("kettlebell-figure-8")
def kb_fig8(c, t, L, row):
    """Wide stance, knees soft, hinged with a flat back: the kettlebell passes between the legs from the right hand
    to the left round the front of the leg (cycle of a figure eight)."""
    a = 2 * math.pi * t
    legs = c.feet(w=c.hw * 1.5, toe=14)
    # the bell follows a figure eight round the knees: x = sin(a), y = sin(2a)
    bx = 0.32 * math.sin(a)
    by = 0.12 * math.sin(2 * a) + 0.02

    def g(D, Hp, c_, sd):
        return np.array([bx + SIDES[sd] * 0.02, by + 0.06, 0.56])
    hold = "R" if math.cos(a) > 0 else "L"
    armsik = arm_ik(g, (0, 0, 1), lambda D, Hp, c_, sd: np.array([SIDES[sd] * 0.4, -0.2, -1]), curl=0.85)
    free = arm_fk((0.35, 0.1, -0.9), elbow=30)
    arms = {hold: armsik[hold], ("L" if hold == "R" else "R"): free["L" if hold == "R" else "R"]}
    return c.stand(legs, hk=0.86, pel=(52, 0, 0), neck=(-25, 0, 0), arms=arms, balance="com",
                   equip=[H("kettlebell", hold)])


@x("single-leg-leg-press")
def sl_leg_press(c, t, L, row):
    """The 45-degree leg press with only the right foot on the middle of the platform; the left foot rests down on
    the frame."""
    fr = REG["leg_press"].fn(c, t, L, row)
    b0 = fr.build

    def build():
        spec, eq, ex = b0()
        D, Hp = c.torso(spec)
        R0 = D[c.r.bi("root")]
        spec["leg"]["L"] = dict(thigh=unit(R0 @ np.array([-0.15, 0.85, -0.4])), knee=95, kbend=R0 @ np.array([0, -0.2, -1]),
                               fdir=R0 @ np.array([0, 0.4, -1]))
        if "ball" in spec["leg"].get("R", {}):
            spec["leg"]["R"]["ball"] = np.asarray(spec["leg"]["R"]["ball"], float) + np.array([-0.12, 0, 0])
        if "ankle" in spec["leg"].get("R", {}):
            spec["leg"]["R"]["ankle"] = np.asarray(spec["leg"]["R"]["ankle"], float) + np.array([-0.13, 0, 0])
        return spec, eq, ex
    fr.build = build
    fr.planted = []
    return fr


@x("dumbbell-v-sit-cross-jab")
def vsit_jab(c, t, L, row):
    """Sitting leaned back in a V with the knees bent and the feet up, light dumbbells by the face: the right hand
    punches across the body with a small turn (alternating)."""
    k = L(0.0, 1.0)
    legs = legs_fk((0.06, 0.55, 0.55), knee=80, kbend=(0, 1, -1))

    def gR(D, Hp, c_, sd):
        sh = fam.shoulder(D, Hp, c, "R")
        Rb = D[c.r.bi("spine01")]
        guard = c.lmk(D, Hp, "forehead") + Rb @ np.array([0.12, 0.12, -0.12])
        punch = sh + Rb @ unit(np.array([-0.35, 1.0, 0.05])) * c.Lh * 0.95
        return guard * (1 - k) + punch * k
    armR = arm_ik(gR, lambda D, Hp, c_, sd: D[c.r.bi("spine01")] @ np.array([-1, 0, 0.3]), (1, -0.3, -0.6), curl=0.9, sides="R")
    armL = arm_ik(lambda D, Hp, c_, sd: c.lmk(D, Hp, "forehead") + D[c.r.bi("spine01")] @ np.array([-0.12, 0.12, -0.12]),
                  (0, 0, 1), (-1, -0.3, -0.6), curl=0.9, sides="L")
    return fam.floor_body(c, pitch=-35, legs=legs, arms=dict(armR, **armL), spine=(10, 0, -22 * k), py=0.0, pz=0.12,
                          equip=[MAT(0.1), H("dumbbell", "L"), H("dumbbell", "R")])


# ================================================================== more floor moves (part I)
@x("walkout-to-push-up")
def walkout_push(c, t, L, row):
    """Fold from the hips, walk the hands out to a push-up position, one push-up, walk back and stand (the walk and
    the push-up in one loop)."""
    wk = REG["walkout"].fn
    if t < 0.6:
        u = t / 0.6
        return wk(c, u, lambda a, b: (tuple(np.asarray(a, float) * (1 - u) + np.asarray(b, float) * u) if isinstance(a, (tuple, list)) else a * (1 - u) + b * u), row)
    k = math.sin(math.pi * (t - 0.6) / 0.4)
    return fam.plank(c, down=0.95 * k, equip=[MATP()], neck=(-10, 0, 0), hands_on=True)


@x("spider-crawl")
def spider_crawl(c, t, L, row):
    """Low push-up position: the right knee turns out and drives up to the right elbow as the chest lowers, as in a
    crawling step (alternating)."""
    return REG["push_up"].fn(c, t, L, dict(row, name_en="Spiderman Push-up", equipment="mat ; plank_hands ; pronated"))


@x("mini-band-plank-with-straight-leg-kickback")
def mb_plank_kick(c, t, L, row):
    """Forearm plank with a mini band round the ankles: one straight leg lifts back and up against the band and
    lowers (alternating)."""
    k = L(0.0, 1.0)

    def kick(D):
        R0 = D[c.r.bi("root")]
        return dict(thigh=unit(R0 @ np.array([0.04, -0.42 * k, -1.0])), knee=4, kbend=R0 @ np.array([0, -1, 0]), fdir=R0 @ np.array([0, -0.3, -1]))
    fr = fam.plank(c, elbows=True, feet_w=0.14 * c.S, equip=[MATP()], hands_on=True, legs_over={"R": kick})
    fr.planted = ["L"]
    return fr


@x("seated-point-and-flex")
def seated_point_flex(c, t, L, row):
    """Sitting tall on the mat with straight legs, a band round the balls of the feet held in both hands: the feet
    point away and pull back (flex)."""
    p = L(-0.45, 0.85)                          # foot direction: -: pulled back (flex), +: pointed
    legs = legs_fk((0.0, 1.0, -0.02), knee=3, kbend=(0, 0, -1), fdir=(0, p, 1 - abs(p) * 0.6))
    arms = arm_ik(lambda D, Hp, c_, sd: c.lmk(D, Hp, "chest") + np.array([SIDES[sd] * 0.16, 0.22, -0.18]), (0, 0, 1), (1, -0.3, -0.6), curl=0.9)
    fr = fam.floor_body(c, pitch=-8, legs=legs, arms=arms, py=0.0, pz=0.12, equip=[MAT(0.2)])

    def band(spec, eq, ex):
        def foot(sd):
            return lambda pts, D, Hp, cx: np.asarray(Hp[c.r.bi(f"toe1-1.{sd}")], float) + np.array([0, 0.03, 0.0])
        return [seg("bandL", foot("L"), ("gripL", (0, 0, 0)), 0.009, "band"), seg("bandR", foot("R"), ("gripR", (0, 0, 0)), 0.009, "band"),
                seg("bandF", foot("L"), foot("R"), 0.009, "band")]
    return _with_eq(fr, band)


@x("mini-band-hip-flexor")
def mb_hip_flexor(c, t, L, row):
    """On the back with a mini band round both feet: one knee drives toward the chest against the band while the
    other leg stays long (alternating)."""
    k = L(0.0, 1.0)
    legs = {"L": legs_fk((0.04, 1.0, 0.08), knee=4, kbend=(0, 0, -1), sides="L")["L"],
            "R": legs_fk((0.06, 1.0 - 1.25 * k, 0.08 + 0.92 * k), knee=4 + 100 * k, kbend=(0, 1, -0.3), sides="R")["R"]}
    return supine_legs(c, legs, arms=palms_floor(c, -0.12))


def _ninety(front_sd, lift=0.0, lean=0.0):
    """90/90 seat: the front leg's thigh forward with the shin across, the back leg's thigh out to the side with the
    shin behind (world FK specs)."""
    s = SIDES[front_sd]
    other = "L" if front_sd == "R" else "R"
    front = dict(thigh=unit(np.array([s * 0.35, 1.0, -0.05 - lift])), knee=92, kbend=np.array([-s, 0.0, -0.05]), fdir=np.array([-s, 0.2, -0.1]),
                 fup=np.array([0, 0, 1]))
    back = dict(thigh=unit(np.array([-s * 1.0, 0.25, -0.05 - lift])), knee=92, kbend=np.array([0.0, -1.0, -0.05]), fdir=np.array([0, -1, -0.1]),
                fup=np.array([0, 0, 1]))
    return {front_sd: front, other: back}


@x("shin-box-quad-stretch")
def shin_box_quad(c, t, L, row):
    """Sitting in a 90/90, hands on the floor behind: the hips push forward and the torso leans back a little so the
    front of the back hip stretches."""
    k = L(0.0, 1.0)
    arms = arm_ik(lambda D, Hp, c_, sd: np.array([SIDES[sd] * 0.22, -0.32, 0.004]), (-1, 0, 0), lambda D, Hp, c_, sd: np.array([SIDES[sd], -0.3, 0.3]),
                  key="palm", curl=0.05, fing=(0, -1, 0))
    return fam.floor_body(c, pitch=-12 - 14 * k, legs=_ninety("R"), arms=arms, py=0.04 * k, pz=0.12 + 0.06 * k, equip=[MAT(0.1)])


@x("shin-box-hip-flexor")
def shin_box_hip(c, t, L, row):
    """From a 90/90 seat the hips lift off the floor onto the shins and drive forward, glutes squeezed, torso tall;
    then sit back down."""
    k = L(0.0, 1.0)
    T1 = c.r.dims["R"]["T1"]
    legs = _ninety("R", lift=0.9 * k)
    arms = arm_fk((0.25, 0.25, -0.9), elbow=25)
    fr = fam.floor_body(c, pitch=-4 - 6 * k, legs=legs, arms=arms, py=0.06 * k, pz=0.12 + (T1 * 0.75) * k, equip=[MAT(0.1)])
    return fr


@x("hip-flow")
def hip_flow(c, t, L, row):
    """Sitting with the hands on the floor behind, knees bent and up: both knees turn over to one side into a 90/90
    and the torso leans over the front shin (alternating sides)."""
    k = L(0.0, 1.0)
    up = {sd: dict(thigh=unit(np.array([SIDES[sd] * 0.3, 0.75, 0.6])), knee=95, kbend=np.array([0, 0.2, -1]), fdir=np.array([0, 1, -0.3]),
                   fup=np.array([0, 0, 1])) for sd in "LR"}
    side = _ninety("R")
    legs = {}
    for sd in "LR":
        a, b = up[sd], side[sd]
        legs[sd] = dict(thigh=unit(np.asarray(a["thigh"]) * (1 - k) + np.asarray(b["thigh"]) * k), knee=a["knee"] * (1 - k) + b["knee"] * k,
                        kbend=unit(np.asarray(a["kbend"]) * (1 - k) + np.asarray(b["kbend"]) * k + 1e-6),
                        fdir=unit(np.asarray(a["fdir"]) * (1 - k) + np.asarray(b["fdir"]) * k + 1e-6), fup=np.array([0, 0, 1]))
    arms = arm_ik(lambda D, Hp, c_, sd: np.array([SIDES[sd] * 0.22, -0.34, 0.004]), (-1, 0, 0), lambda D, Hp, c_, sd: np.array([SIDES[sd], -0.3, 0.3]),
                  key="palm", curl=0.05, fing=(0, -1, 0))
    return fam.floor_body(c, pitch=-20 + 12 * k, legs=legs, arms=arms, spine=(6 * k, 0, 12 * k), py=0.0, pz=0.12, equip=[MAT(0.1)])


# ================================================================== balance trainer seated, straps (part J)
def _dome_seat(c, legs, k_lean=0.0):
    """Sitting on the top of a balance trainer, leaning back with the hands on its edge behind the hips."""
    arms = arm_ik(lambda D, Hp, c_, sd: np.array([SIDES[sd] * 0.2, -0.24, 0.05]), (-1, 0, 0), lambda D, Hp, c_, sd: np.array([SIDES[sd], -0.3, 0.3]),
                  key="palm", curl=0.1, fing=(0, -1, 0))
    return fam.floor_body(c, pitch=-30 - 8 * k_lean, legs=legs, arms=arms, py=0.0, pz=DOME + 0.1,
                          equip=[E("bosu", (0, -0.04, 0), eid="bosu")],
                          settle=[("plane", np.array([0, -0.02, DOME]), Z, X, 0.15, Y, 0.15, 0.01, "pelvis")])


@x("balance-trainer-braced-bicycle-kick")
def bt_bicycle(c, t, L, row):
    """Sitting on the dome, hands on its edge behind, feet off the floor: one knee draws to the chest while the other
    leg straightens forward, pedalling (cycle)."""
    a = 2 * math.pi * t
    legs = {}
    for sd, ph in (("R", a), ("L", a + math.pi)):
        k = 0.5 + 0.5 * math.cos(ph)       # 1: knee in, 0: leg long
        legs[sd] = dict(thigh=unit(np.array([SIDES[sd] * 0.08, 0.9 - 0.4 * k, 0.15 + 0.75 * k])), knee=8 + 105 * k, kbend=np.array([0, 0.3, -1]),
                        fdir=np.array([0, 0.5, 1]))
    return _dome_seat(c, legs)


@x("balance-trainer-braced-frog-kick")
def bt_frog(c, t, L, row):
    """Sitting on the dome, hands behind, heels together: the knees draw in toward the chest, then both legs kick
    out straight together."""
    k = L(1.0, 0.0)
    legs = {sd: dict(thigh=unit(np.array([SIDES[sd] * (0.06 + 0.25 * k), 0.9 - 0.4 * k, 0.2 + 0.75 * k])), knee=6 + 105 * k,
                     kbend=np.array([-SIDES[sd] * 0.3 * k, 0.3, -1]), fdir=np.array([0, 0.5, 1])) for sd in "LR"}
    return _dome_seat(c, legs)


@x("balance-trainer-single-leg-lift")
def bt_sl_lift(c, t, L, row):
    """Sitting on the dome leaning back, hands on its edge: one straight leg lifts and lowers while the other foot
    rests on the floor (alternating)."""
    k = L(0.0, 1.0)
    legs = {"L": dict(thigh=unit(np.array([-0.1, 0.85, -0.25])), knee=85, kbend=np.array([0, 0.1, -1]), fdir=np.array([0, 1, -0.2])),
            "R": dict(thigh=unit(np.array([0.08, 0.9, 0.0 + 0.6 * k])), knee=5, kbend=np.array([0, 0, -1]), fdir=np.array([0, 0.3, 1]))}
    return _dome_seat(c, legs)


@x("balance-trainer-reverse-hyperextension")
def bt_rev_hyper(c, t, L, row):
    """Face down over the dome with the hips on top and the forearms on the floor: the straight legs lift to body level
    and lower."""
    k = L(0.0, 1.0)
    legs = legs_fk((0.0, -0.95, -0.3 + 0.42 * k), knee=4, kbend=(0, 0, 1), fdir=(0, 0, -1))
    arms = arm_ik(lambda D, Hp, c_, sd: np.array([SIDES[sd] * 0.2, 0.62, 0.004]), (-1, 0.2, 0), (0.3, -1, 0.3), key="palm", curl=0.1, fing=(0, 1, 0))
    return fam.floor_body(c, pitch=72, legs=legs, arms=arms, py=0.0, pz=DOME + 0.12, equip=[MAT(0.0), E("bosu", (0, 0.0, 0), eid="bosu")],
                          settle=[("plane", np.array([0, 0.0, DOME]), Z, X, 0.15, Y, 0.15, 0.01, "pelvis")])


@x("suspension-sprinter-start")
def susp_sprinter(c, t, L, row):
    """Facing away from the anchor with the handles at the chest, leaning forward on the taut straps in a sprint
    start: the back knee drives forward and up, then steps back."""
    anchor = np.array([0.0, -1.2, 2.45])
    k = L(0.0, 1.0)

    def chest(D, Hp, c_, sd):
        return c.lmk(D, Hp, "chest") + D[c.r.bi("spine01")] @ np.array([SIDES[sd] * 0.16, 0.1, 0.05])
    arms = arm_ik(chest, (0, 0, 1), lambda D, Hp, c_, sd: np.array([SIDES[sd] * 0.8, -0.6, -0.4]), curl=0.9)
    knee = dict(thigh=unit(np.array([0.05, -0.55 + 1.5 * k, -1 + 0.95 * k])), knee=30 + 60 * k, kbend=np.array([0, -1, 0]), fdir=np.array([0, 1, -0.4]))
    legs = {"L": dict(c.foot(-c.hw * 0.4, 0.15, 6), heel=20), "R": knee}
    fr = c.stand(legs, hk=0.95, py=0.12, pel=(28, 0, 0), spine=(4, 0, 0), arms=arms, balance=None, reach=True, planted=("L",),
                 equip=[dict(E("trx_anchor", anchor * np.array([1, 1, 0]), eid="trx", h=2.45), fit=False)])
    return _with_eq(fr, [seg("strapL", anchor, ("gripL", (0, 0, 0)), 0.012, "strap"), seg("strapR", anchor, ("gripR", (0, 0, 0)), 0.012, "strap")])


@x("balance-trainer-suspension-squat-jump")
def bt_susp_squat_jump(c, t, L, row):
    """Standing on the flat side of an upturned balance trainer facing the anchor, holding the handles: squat, a small
    jump, a soft landing on the platform (cycle)."""
    anchor = np.array([0.0, 1.35, 2.45])
    hh = 0.25
    w = c.hw * 0.55
    K = _keys([(0.0, dict(fL=(-w, 0, hh), fR=(w, 0, hh), sL=hh, sR=hh, pz=c.pz * 0.97 + hh, pitch=4)),
               (0.35, dict(fL=(-w, 0, hh), fR=(w, 0, hh), sL=hh, sR=hh, pz=c.pz * 0.68 + hh, pitch=26)),
               (0.55, dict(fL=(-w, 0, hh + 0.14), fR=(w, 0, hh + 0.14), gL=0, gR=0, hL=35, hR=35, pz=c.pz * 0.99 + hh + 0.15, pitch=2)),
               (0.75, dict(fL=(-w, 0, hh), fR=(w, 0, hh), sL=hh, sR=hh, pz=c.pz * 0.74 + hh, pitch=22)),
               (1.0, dict(fL=(-w, 0, hh), fR=(w, 0, hh), sL=hh, sR=hh, pz=c.pz * 0.97 + hh, pitch=4))])
    kv = _interp(K, min(t, 0.9999))
    kv.update(ua=(0.1, 0.6, 0.4), el=10)
    return keyed_stand(c, kv, arms=_strap_arms(c, anchor), equip=_handles(c, anchor) + [E("bosu", (0, 0.0, hh), R=rx(180), eid="bosu")])


@x("suspension-hamstring-runner")
def susp_ham_runner(c, t, L, row):
    """On the back with the heels in the straps and the hips lifted: one heel pulls in toward the glutes while the
    other leg stays straight (alternating)."""
    k = L(0.0, 1.0)
    fh = 0.45
    anchor = np.array([0.0, 1.6, 2.45])
    legs = {"L": legs_fk((0.05, 0.96, 0.1), knee=4, kbend=(0, 0, -1), fdir=(0, -0.2, 1), sides="L")["L"],
            "R": legs_fk((0.06, 0.96 - 0.55 * k, 0.1 + 0.6 * k), knee=4 + 110 * k, kbend=(0, 0.2, -1), fdir=(0, -0.2, 1), sides="R")["R"]}
    fr = fam.floor_body(c, pitch=-72, legs=legs, arms=palms_floor(c, -0.12), py=0.0, pz=0.32, equip=[MAT(0.2)],
                        settle=[("floor", SKIN_FLOOR)])

    def straps(spec, eq, ex):
        def heel(sd):
            return lambda pts, D, Hp, cx: np.asarray(Hp[c.r.bi(f"foot.{sd}")], float) + np.array([0, -0.03, -0.02])
        return [dict(E("trx_anchor", anchor * np.array([1, 1, 0]), eid="trx", h=2.45), fit=False),
                seg("strapL", anchor, heel("L"), 0.012, "strap"), seg("strapR", anchor, heel("R"), 0.012, "strap")]
    return _with_eq(fr, straps)
