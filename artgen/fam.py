"""Higher-level body set-ups built on Ctx.stand (the generic builder):
benches, floor lying, planks, hanging, seated machines.  All positions in
metres, character facing +Y, right = +X."""
import math

import numpy as np

from .poses import E, H, seg, frame3, SOLE, PAD_SINK, SKIN_FLOOR, _bar_R, _landmine
from .rig import X, Y, Z, SIDES, unit, orth, rot, body_rot
from .equipment import PLATE_R, rx, ry, rz

BENCH_H = 0.44


# --------------------------------------------------------------- arm helpers
def arm_fk(v, elbow=10, thumb="fwd", bend=(0, 1, 0), curl=0.3, bone="spine01", world=False, fing=None,
           sides="LR"):
    """FK arms; v/bend/thumb are given for the right arm (x = out) and mirrored
    for the left.  world=True uses world axes instead of the torso frame."""
    def mk(sd):
        def f(D, Hp, c):
            def m(vec):
                vec = np.array(vec, float)
                if world:
                    if sd == "L":
                        vec[0] = -vec[0]
                    return unit(vec)
                return c.arm_dir(D, vec, sd, bone)
            a = dict(ua=m(v), elbow=elbow, bend=m(bend), curl=curl,
                     thumb=thumb if isinstance(thumb, str) else m(thumb))
            if fing is not None:
                a["fing"] = m(fing)
            return a
        return f
    return {sd: mk(sd) for sd in sides}


def arm_ik(target_fn, thumb, pole, curl=0.85, key="grip", fing=None, sides="LR"):
    """IK arms; target_fn(D, Hp, c, sd) -> point; thumb/pole: callables or
    vectors in the right-arm convention (x mirrored for the left)."""
    def mk(sd):
        s = SIDES[sd]

        def f(D, Hp, c):
            def m(vec):
                if callable(vec):
                    return np.asarray(vec(D, Hp, c, sd), float)
                vec = np.array(vec, float)
                vec[0] *= s
                return vec
            a = {key: target_fn(D, Hp, c, sd), "thumb": m(thumb), "pole": m(pole), "curl": curl}
            if fing is not None:
                a["fing"] = m(fing)
            return a
        return f
    return {sd: mk(sd) for sd in sides}


def tf(D, c, vec, bone="spine01", sd="R"):
    """torso-frame vector (right-arm convention) -> world."""
    v = np.array(vec, float)
    if sd == "L":
        v[0] = -v[0]
    return D[c.r.bi(bone)] @ v


def shoulder(D, Hp, c, sd):
    return c.J(D, Hp, f"upperarm01.{sd}")


def within(c, base, off, k=0.85):
    """base + off, the offset shortened to at most k arm lengths."""
    off = np.asarray(off, float)
    n = np.linalg.norm(off)
    lim = c.Lpf * k
    return base + (off * lim / n if n > lim else off)


def floor_palm(c, D, Hp, sd, x, y, z=0.004, k=0.97):
    """Palm point on a surface at height z near (x, y), pulled toward the
    shoulder just enough to stay within the arm's reach."""
    sh = shoulder(D, Hp, c, sd)
    p = np.array([x, y, z], float)
    R = c.Lpf * k
    if np.linalg.norm(p - sh) <= R:
        return p
    h = sh[2] - z
    v = p[:2] - sh[:2]
    nv = np.linalg.norm(v)
    if h >= R or nv < 1e-6:
        return np.array([sh[0], sh[1], z])
    v = v / nv * math.sqrt(R * R - h * h)
    return np.array([sh[0] + v[0], sh[1] + v[1], z])


def sh_mid(D, Hp, c):
    return 0.5 * (c.J(D, Hp, "upperarm01.L") + c.J(D, Hp, "upperarm01.R"))


# -------------------------------------------------------------------- legs
def legs_fk(thigh, knee, kbend=(0, -1, 0), fdir=None, fup=None, world=True, sides="LR", toe=0.0):
    """FK legs, thigh/kbend in the right-leg convention (x mirrored)."""
    out = {}
    for sd in sides:
        s = SIDES[sd]
        th = np.array(thigh, float); th[0] *= s
        kb = np.array(kbend, float); kb[0] *= s
        L = dict(thigh=th, knee=knee, kbend=kb, toe=toe)
        if fdir is not None:
            fd = np.array(fdir, float); fd[0] *= s
            L["fdir"] = fd
        if fup is not None:
            fu = np.array(fup, float); fu[0] *= s
            L["fup"] = fu
        out[sd] = L
    return out


def legs_rel(c, D, legs):
    """Map FK leg vectors given in the pelvis frame to world."""
    R0 = D[c.r.bi("root")]
    out = {}
    for sd, L in legs.items():
        L = dict(L)
        for k in ("thigh", "kbend", "fdir", "fup"):
            if k in L:
                L[k] = R0 @ L[k]
        out[sd] = L
    return out


# ------------------------------------------------------------- holds (IK)
def press_bar(c, press, kind="bench", gw=None, plates=1, bar="barbell", grip="pro", lockz=None):
    """Barbell pressed from the chest (or front rack) to lockout along the
    torso front ('bench') or up ('oh').  press 0 = bottom, 1 = lockout."""
    gw = c.sw * 1.75 if gw is None else gw

    def center(D, Hp):
        Rt = D[c.r.bi("spine01")]
        if kind == "bench":
            bot = c.lmk(D, Hp, "chest")
            dirv = Rt @ Y
        else:
            bot = c.lmk(D, Hp, "front_rack") + Rt @ Y * 0.02
            dirv = Rt @ Z
        mid = sh_mid(D, Hp, c)
        h = math.sqrt(max(c.Lh ** 2 - max(gw / 2 - c.sw / 2, 0) ** 2, 0.01)) * 0.975
        top = mid + dirv * h
        if kind == "oh":
            top = top - Rt @ Y * 0.03
        return bot * (1 - press) + top * press, Rt

    def tgt(D, Hp, c_, sd):
        p, Rt = center(D, Hp)
        return p + Rt @ X * SIDES[sd] * gw / 2

    def thumb(D, Hp, c_, sd):
        Rt = D[c.r.bi("spine01")]
        return -SIDES[sd] * (Rt @ X) * (1 if grip == "pro" else -1)

    def pole(D, Hp, c_, sd):
        Rt = D[c.r.bi("spine01")]
        s = SIDES[sd]
        if kind == "bench":
            return -(Rt @ Y) * 0.8 + Rt @ X * s * 0.7 - Rt @ Z * 0.25
        return -(Rt @ Z) * 0.7 + Rt @ Y * 0.5 + Rt @ X * s * 0.45

    def fing(D, Hp, c_, sd):
        Rt = D[c.r.bi("spine01")]
        return Rt @ Y if kind == "bench" else Rt @ Z

    arms = arm_ik(tgt, thumb, pole, curl=0.85, fing=fing)
    eq = [H(bar, "C", "bar", eid="bar", plates=plates)]
    return arms, eq


def press_db(c, press, kind="bench", w0=None, w1=None, thumb_mode="pro", rot_end=None):
    """Dumbbells pressed from beside the chest/shoulders to lockout."""
    w0 = c.sw * 1.45 if w0 is None else w0
    w1 = c.sw * 0.95 if w1 is None else w1

    def tgt(D, Hp, c_, sd):
        Rt = D[c.r.bi("spine01")]
        s = SIDES[sd]
        mid = sh_mid(D, Hp, c)
        if kind == "bench":
            bot = c.lmk(D, Hp, "chest") + Rt @ Y * 0.03 + Rt @ Z * 0.0
            dirv = Rt @ Y
        else:
            bot = c.lmk(D, Hp, "front_rack") + Rt @ Y * 0.0 + Rt @ Z * 0.04
            dirv = Rt @ Z
        w = w0 * (1 - press) + w1 * press
        h = math.sqrt(max(c.Lh ** 2 - max(w / 2 - c.sw / 2, 0) ** 2, 0.01)) * 0.975
        top = mid + dirv * h
        p = bot * (1 - press) + top * press
        return p + Rt @ X * s * (w / 2) - (Rt @ X * s) @ (p - mid) * 0 * Rt @ X

    def thumb(D, Hp, c_, sd):
        Rt = D[c.r.bi("spine01")]
        s = SIDES[sd]
        pro = -s * (Rt @ X)
        head = Rt @ Z if kind == "bench" else Rt @ Y
        if thumb_mode == "neutral":
            return head
        if thumb_mode == "arnold":  # palms toward the face -> pronated
            a = math.radians(90 * press)
            return unit(-pro * math.cos(a) * 0 + head * math.cos(a) + pro * math.sin(a) + 1e-6 * Z) if False else \
                unit((s * (Rt @ X)) * math.cos(a) + pro * math.sin(a) * 1.0 + head * 0.15)
        return pro

    def pole(D, Hp, c_, sd):
        Rt = D[c.r.bi("spine01")]
        s = SIDES[sd]
        if kind == "bench":
            return -(Rt @ Y) * 0.8 + Rt @ X * s * 0.8
        return -(Rt @ Z) * 0.8 + Rt @ X * s * 0.6 + Rt @ Y * 0.15

    arms = arm_ik(tgt, thumb, pole, curl=0.85)
    eq = [H("dumbbell", "L"), H("dumbbell", "R")]
    return arms, eq


def row_bar(c, pull, gw=None, kind="barbell", grip="pro", touch="belly"):
    """Barbell from hanging (gravity) to touching the torso."""
    gw = c.sw * 1.3 if gw is None else gw

    def center(D, Hp):
        Rt = D[c.r.bi("spine01")]
        mid = sh_mid(D, Hp, c)
        hang = mid - Z * math.sqrt(max(c.Lh ** 2 - max(gw / 2 - c.sw / 2, 0) ** 2, 0.01)) * 0.98
        lm = "hip_front" if touch == "belly" else "chest"
        top = c.lmk(D, Hp, lm) - Z * 0.02
        if touch == "belly":
            top = top + (c.lmk(D, Hp, "chest") - top) * 0.45
        return hang * (1 - pull) + top * pull

    def tgt(D, Hp, c_, sd):
        return center(D, Hp) + X * SIDES[sd] * gw / 2

    arms = arm_ik(tgt, lambda D, Hp, c_, sd: -SIDES[sd] * X * (1 if grip == "pro" else -1),
                  lambda D, Hp, c_, sd: Z * 0.8 - (D[c.r.bi("spine01")] @ Z) * 0.6 + X * SIDES[sd] * 0.25,
                  curl=0.85, fing=lambda D, Hp, c_, sd: -Z)
    return arms, [H(kind, "C", "bar", eid="bar")]


def row_db(c, pull, sides="LR", spread=0.0, thumb="neutral", elbow_out=0.15):
    """Dumbbell(s) from hanging to beside the ribs."""
    def tgt(D, Hp, c_, sd):
        s = SIDES[sd]
        Rt = D[c.r.bi("spine01")]
        sh = shoulder(D, Hp, c, sd)
        hang = sh - Z * c.Lh * 0.98 + X * s * spread
        top = c.bp(D, Hp, "spine02", np.array([s * 0.14 * c.S, c.r.joint("spine02")[1] + 0.06, c.z_nip - 0.08]))
        top = top - Z * 0.03
        return hang * (1 - pull) + top * pull

    def th(D, Hp, c_, sd):
        Rt = D[c.r.bi("spine01")]
        if thumb == "neutral":
            return Rt @ Z * 0.2 + Y * 1.0
        return -SIDES[sd] * X

    arms = arm_ik(tgt, th, lambda D, Hp, c_, sd: Z + X * SIDES[sd] * elbow_out - Y * 0.3, curl=0.85,
                  fing=lambda D, Hp, c_, sd: -Z, sides=sides)
    return arms, [H("dumbbell", sd) for sd in sides]


# ------------------------------------------------------------------ benches
def bench_eq(kind="flat", y=0.0, angle=0.0):
    if kind == "flat":
        return E("bench", (0, y, 0), eid="bench")
    if kind == "incline":
        return E("bench", (0, y, 0), eid="bench", incline=angle)
    if kind == "decline":
        return E("bench", (0, y, 0), eid="bench", decline=angle)
    return None


def supine_on_bench(c, kind="flat", angle=0.0, arms=None, hold_eq=(), legs="floor", extra_eq=(),
                    spine=(0, 0, 0), neck=(0, 0, 0), by=0.0, pel_extra=0.0, feet_y=None):
    """Lying on a bench (head toward -Y).  Flat / incline (back pad raised
    by `angle`) / decline (head down by `angle`) / floor (no bench)."""
    if kind == "flat":
        pitch = -90 + pel_extra
        sup = [("plane", np.array([0, by, BENCH_H]), Z, X, 0.14, Y, 0.6, PAD_SINK)]
        pz = BENCH_H + 0.11
        py = by + 0.22
    elif kind == "incline":
        pitch = -(90 - angle) + pel_extra
        Rb = rx(-angle)
        piv = np.array([0, by - 0.02, BENCH_H])
        n = Rb @ Z
        sup = [("plane", piv + Rb @ np.array([0, -0.4, 0]), n, X, 0.14, Rb @ Y, 0.42, PAD_SINK),
               ("plane", np.array([0, by + 0.17, BENCH_H]), Z, X, 0.15, Y, 0.17, PAD_SINK)]
        pz = BENCH_H + 0.12
        py = by + 0.1
    elif kind == "decline":
        pitch = -90 - angle + pel_extra
        Rb = rx(angle)
        sup = [("plane", np.array([0, by, BENCH_H]), Rb @ Z, X, 0.14, Rb @ Y, 0.6, PAD_SINK)]
        pz = BENCH_H + 0.11 + 0.15
        py = by + 0.32
    else:  # floor
        pitch = -90 + pel_extra
        sup = [("floor", SKIN_FLOOR)]
        pz = 0.12
        py = by + 0.15
    if legs == "floor":
        fy = (py + 0.5 * c.S ** 2) if feet_y is None else feet_y
        if kind == "incline":
            fy = py + 0.62 * c.S ** 2 if feet_y is None else feet_y
        lg = {sd: dict(ball=np.array([SIDES[sd] * 0.27 * c.S, fy, SOLE]), yaw=18, heel=0,
                       pole=np.array([SIDES[sd] * 0.3, 0.6, 1.0])) for sd in "LR"}
        if kind == "floor":
            lg = {sd: dict(ball=np.array([SIDES[sd] * 0.16 * c.S, py + 0.62 * c.S, SOLE]), yaw=8, heel=0,
                           pole=np.array([SIDES[sd] * 0.1, 0.2, 1.0])) for sd in "LR"}
    elif legs == "decline":
        lg = {sd: dict(thigh=np.array([SIDES[sd] * 0.12, 0.75, 0.65]), knee=95, kbend=np.array([0, -0.3, -1]))
              for sd in "LR"}
    else:  # tucked up on the bench
        lg = {sd: dict(thigh=np.array([SIDES[sd] * 0.1, 0.35, 0.95]), knee=85, kbend=np.array([0, 1, -0.4]))
              for sd in "LR"}
    eqs = [bench_eq(kind, by, angle)] if kind != "floor" else []
    eqs += list(hold_eq) + list(extra_eq)
    return c.stand(lg, pz=pz, py=py, pel=(pitch, 0, 0), spine=spine, neck=neck, arms=arms, balance=None,
                   equip=eqs, reach=False, settle=sup, planted=("L", "R") if legs == "floor" else ())


# -------------------------------------------------------------------- plank
def plank(c, down=0.0, hand_w=None, hand_y=0.0, hands_h=0.0, feet_h=0.0, feet_w=None, knees=False,
          elbows=False, legs_over=None, arms_over=None, equip=(), hands_on=None, spine=(0, 0, 0),
          hip_raise=0.0, foot_heel=72.0, top_down=0.0, neck=(0, 0, 0), fingers="fwd"):
    """Prone plank / push-up: hands (palms) at hand_y on a surface of height
    hands_h, toes on a surface of height feet_h; the body stays a straight
    line pivoting about the toes (or knees).  down: 0 = arms straight,
    1 = chest just above the hands."""
    hand_w = c.sw * 1.15 if hand_w is None else hand_w
    feet_w = 0.2 * c.S if feet_w is None else feet_w
    r = c.r
    sh_r = r.joint("upperarm01.R")
    an_r = r.joint("foot.R")
    kn_r = r.joint("lowerleg01.R")
    pc = r.pc_rest

    def shoulder_h(dn):
        if elbows:
            return hands_h + c.r.dims["R"]["L1"] + 0.09
        top = hands_h + c.Lpf * 0.985 * math.sqrt(max(1 - ((hand_w - c.sw) / 2 / c.Lpf) ** 2, 0.5))
        bottom = hands_h + 0.235 * c.S
        return top * (1 - dn) + bottom * dn

    piv_rest = kn_r if knees else an_r
    blen = np.linalg.norm((sh_r - piv_rest)[[1, 2]])
    if knees:
        piv_z = feet_h + 0.055
    else:
        heel = math.radians(foot_heel)
        piv_z = feet_h + SOLE + 0.03 + (an_r[2] - 0.03) * 0.25 + c.foot_len * 0.45 * math.sin(heel) * 0.62
    # pivot fixed from the top pose
    s_top = shoulder_h(top_down)
    sy = hand_y + (0.02 if not elbows else 0.0)
    py_piv = sy - math.sqrt(max(blen ** 2 - (s_top - piv_z) ** 2, 0.01))

    def solve_body(dn):
        sz = shoulder_h(dn)
        dz = sz - piv_z
        dy = math.sqrt(max(blen ** 2 - dz ** 2, 0.01))
        S = np.array([0.0, py_piv + dy, sz])
        v0 = (sh_r - piv_rest)[[1, 2]]
        a0 = math.atan2(v0[1], v0[0])
        a1 = math.atan2(dz, dy)
        pitch = math.degrees(a0 - a1)
        R = body_rot(pitch, 0, 0)
        pel = S - R @ (sh_r - pc)
        return pel, pitch

    pel, pitch = solve_body(down)
    pel = pel + np.array([0, 0, hip_raise])
    # hands
    def hand_tgt(D, Hp, c_, sd):
        return np.array([SIDES[sd] * hand_w / 2, hand_y, hands_h + 0.004])

    if elbows:
        arms = {}
        for sd in "LR":
            s = SIDES[sd]

            def f(D, Hp, c_, sd=sd, s=s):
                sh = shoulder(D, Hp, c, sd)
                el = np.array([sh[0] * 0.95, hand_y, hands_h + 0.05])
                ua = unit(el - sh)
                return dict(ua=ua, elbow=88, bend=np.array([-s * 0.15, 1, 0]), thumb=Z, curl=0.55,
                            fing=np.array([-s * 0.25, 1, 0.12]), thumb_curl=0.2)
            arms[sd] = f
    else:
        fing_v = (0, 1, 0) if fingers == "fwd" else (-0.6, 0.6, 0)
        arms = arm_ik(hand_tgt, (-1, 0.15, 0), (0.25, -1.0, 0.25), curl=0.05, key="palm", fing=fing_v)
    if arms_over:
        arms.update(arms_over)
    lg = {}
    for sd in "LR":
        s = SIDES[sd]
        if knees:
            lg[sd] = dict(thigh=None, knee=None)
        else:
            ball_y = py_piv - c.foot_len * 0.25 + 0.035
            lg[sd] = dict(ball=np.array([s * feet_w / 2, ball_y, feet_h + SOLE]), surf=feet_h, yaw=0, heel=foot_heel,
                          pole=np.array([0, -0.2, -1.0]))
    if knees:
        def kn(sd):
            def f(D):
                R0 = D[c.r.bi("root")]
                th = unit(R0 @ (kn_r - r.joint("upperleg01.R")))
                return dict(thigh=th, knee=100, kbend=R0 @ np.array([0, -1, 0.2]), fdir=-Y + Z * 0.3, fup=Z)
            return f
        lg = {sd: kn(sd) for sd in "LR"}
    if legs_over:
        lg.update(legs_over)

    def build_legs(D):
        return {sd: (L(D) if callable(L) else L) for sd, L in lg.items()}

    settle = [("floor", SKIN_FLOOR)] if (hands_h == 0 and feet_h == 0 and not hands_on) else []
    fr = c.stand({}, pz=pel[2], py=pel[1], px=0.0, pel=(pitch, 0, 0), spine=spine, neck=neck, arms=arms,
                 balance=None, reach=False, equip=list(equip), planted=())
    b0 = fr.build

    def build():
        spec, eq, ex = b0()
        D, Hp = c.torso(spec)
        spec["leg"] = build_legs(D)
        return spec, eq, ex
    fr.build = build
    fr.planted = [sd for sd, L in lg.items() if isinstance(L, dict) and "ball" in L]
    if fr.planted:   # straight legs: slide the body along its axis until the toes are reached exactly
        fr.cons.append(("reach_legs", unit(np.array([0, -1.0, -0.2])), list(fr.planted)))
    return fr


# ------------------------------------------------------------------ hanging
HANG_CLEAR = 0.55    # feet above the floor in a dead hang (m, scaled with the athlete)


def hang_bar_h(c, clear=HANG_CLEAR):
    """Bar height for a hanging athlete: overhead reach (shoulder height plus
    the straight arm to the grip) plus a clearance, so the feet hang clearly
    off the floor for every body size and gender."""
    return c.z_sh + c.Lh + clear * c.S


def shoulder_level(c, z_fn):
    """Constraint: move the pelvis vertically until the mean shoulder joint
    sits at z_fn() (the real shoulder, including the shrug of overhead arms),
    so a dead hang is on straight arms instead of bent ones."""
    def f(spec, D, Hp, info, extra):
        z = 0.5 * (Hp[c.r.bi("upperarm01.L")][2] + Hp[c.r.bi("upperarm01.R")][2])
        e = z_fn() - z
        return np.array([0.0, 0.0, 0.9 * e]) if abs(e) > 3e-4 else np.zeros(3)
    return ("call", f)


def hang(c, pull=0.0, gw=None, grip="pro", bar_h=None, legs=None, eq=True, rings=False, spine=(0, 0, 0),
         neck=(0, 0, 0), pel=(0, 0, 0), extra_eq=(), arms=None, hang_k=0.985, px=0.0, py=-0.03, d=None, fit=True):
    """Hanging from a bar at bar_h; pull 0 = dead hang, 1 = chin over bar."""
    gw = c.sw * 1.45 if gw is None else gw
    bar_h = hang_bar_h(c) if bar_h is None else bar_h
    bar = np.array([0, 0.0, bar_h])
    if arms is None:
        arms = arm_ik(lambda D, Hp, c_, sd: bar + X * SIDES[sd] * gw / 2,
                      lambda D, Hp, c_, sd: -SIDES[sd] * X * (1 if grip == "pro" else -1) if grip != "neutral" else Y,
                      lambda D, Hp, c_, sd: (-Z * 0.5 + Y * 0.8 + X * SIDES[sd] * 0.2) if grip == "neutral" else
                      (-Z * 0.5 + X * SIDES[sd] * 0.8 + (-Y * 0.6 if grip == "sup" else Y * 0.0)),
                      curl=0.9, fing=lambda D, Hp, c_, sd: Z)
    # shoulder height below bar (straight arms at pull 0)
    hang_d = math.sqrt(max((c.Lh * hang_k) ** 2 - max(gw / 2 - c.sw / 2, 0) ** 2, 0.01))
    top_d = 0.21 * c.S
    if d is None:
        d = hang_d * (1 - pull) + top_d * pull
    sh_rest = c.r.joint("upperarm01.R")
    pz0 = bar_h - d - (sh_rest[2] - c.pz)
    lg = legs if legs is not None else legs_fk((0.05, 0.08, -1), 15, kbend=(0, -1, 0), fdir=(0, 0.5, -1))
    eqs = []
    if eq:
        eqs.append(dict(E("pullup_station", (0, 0, 0), eid="station", height=bar_h, width=1.3), fit=fit))
    eqs += list(extra_eq)
    fr = c.stand(lg, pz=pz0, py=py, px=px, pel=pel, spine=spine, neck=neck, arms=arms, balance=None, reach=False,
                 equip=eqs, planted=())
    fr.cons.append(shoulder_level(c, lambda: bar_h - d))
    fr.cons.append(("reach_arms", Z, ["L", "R"]))
    fr.bar_h = bar_h
    return fr


# ------------------------------------------------------------------ seated
def seated(c, seat_h=0.47, seat_y=0.0, pitch=0.0, arms=None, hold=None, hold2=None, mix=0.0, legs=None,
           feet_y=None, feet_w=None, back=None, equip=(), spine=(0, 0, 0), neck=(0, 0, 0), toe=12,
           planted=("L", "R"), seat_x=0.0, seat_w=0.2, seat_d=0.2):
    """Sitting on a seat of height seat_h (top surface) centred at seat_y."""
    fy = seat_y + 0.5 * c.S if feet_y is None else feet_y
    fw = 0.34 * c.S if feet_w is None else feet_w
    lg = legs if legs is not None else {
        sd: dict(ball=np.array([seat_x + SIDES[sd] * fw / 2, fy, SOLE]), yaw=toe, heel=0,
                 pole=np.array([SIDES[sd] * 0.15, 1.0, 0.6])) for sd in "LR"}
    sup = [("plane", np.array([seat_x, seat_y, seat_h]), Z, X, seat_w, Y, seat_d, PAD_SINK, "hips")]
    if back is not None:
        p0, n = back
        sup.append(("plane", np.asarray(p0), unit(n), X, 0.2, unit(np.cross(X, n)), 0.35, PAD_SINK))
    return c.stand(lg, pz=seat_h + 0.12, py=seat_y - 0.02, px=seat_x, pel=(pitch, 0, 0), spine=spine, neck=neck,
                   hold=hold or "none", hold2=hold2, mix=mix, arms=arms, balance=None, reach=False,
                   equip=list(equip), settle=sup, planted=[s for s in planted if s in lg and "ball" in lg[s]])


# ------------------------------------------------------------- floor lying
def floor_body(c, pitch=-90, roll=0.0, yaw=0.0, legs=None, arms=None, spine=(0, 0, 0), neck=(0, 0, 0),
               py=0.0, px=0.0, equip=(), hold="none", hold2=None, mix=0.0, settle=None, planted=None, pz=0.15,
               cons=()):
    """Body resting on the floor (supine pitch -90, prone +90, seated ~0)."""
    lg = legs or {}
    pl = [sd for sd, L in lg.items() if isinstance(L, dict) and "ball" in L] if planted is None else planted
    fr = c.stand(lg, pz=pz, py=py, px=px, pel=(pitch, roll, yaw), spine=spine, neck=neck, arms=arms, hold=hold,
                 hold2=hold2, mix=mix, balance=None, reach=False, equip=list(equip),
                 settle=[("floor", SKIN_FLOOR)] if settle is None else settle, planted=pl)
    fr.cons += list(cons)
    return fr


def knees_floor(c, D, sides="LR", spread=0.1, shin_back=True):
    """Kneeling leg spec: thighs straight down from the hips, shins back on
    the floor (evaluated with the pelvis frame)."""
    out = {}
    R0 = D[c.r.bi("root")]
    for sd in sides:
        s = SIDES[sd]
        out[sd] = dict(thigh=unit(np.array([s * spread, 0.0, -1.0])), knee=92,
                       kbend=np.array([0, -1, 0.05]), fdir=np.array([0, -1, -0.15]), fup=np.array([0, 0.1, 1]))
    return out
