"""Set-ups for machines, cables, bands, cardio machines and held implements
whose generic versions put the athlete through the equipment or lost the
implement.  Each override applies to the rows it is written for (by the
row's data) and hands every other row to the archetype it replaces."""
from .templates import REG, E, H, seg, PLATE_R, X, Y, Z, np, math, SIDES, rz
from .poses import SOLE, PAD_SINK, SKIN_FLOOR
from .rig import unit, orth
from . import fam, kit
from .fam import arm_fk, arm_ik
from .spec3 import P
from .tpl_lower import eqw
from . import eq_c  # noqa: F401  (registers the equipment kinds)


def override(name, view=None, lens=None):
    """Replace REG[name]'s function; the wrapped one is passed as `prev`."""
    t = REG[name]
    prev = t.fn

    def deco(fn):
        def wrapped(c, tt, L, row):
            return fn(c, tt, L, row, prev)
        wrapped.prev = prev
        t.fn = wrapped
        return fn
    return deco


def name_of(row):
    return (row.get("name_en") or "").lower()


def add_eq(fr, extra):
    """Append equipment (list or callable(spec, eq, ex) -> list) to a frame."""
    b = fr.build

    def build():
        spec, eq, ex = b()
        more = extra(spec, eq, ex) if callable(extra) else extra
        return spec, list(eq) + list(more), ex
    fr.build = build
    return fr


def filter_eq(fr, drop):
    b = fr.build

    def build():
        spec, eq, ex = b()
        return spec, [e for e in eq if not drop(e)], ex
    fr.build = build
    return fr


def reach(c, sh, p, k=0.985):
    """p pulled toward the shoulder sh until a straight arm reaches it."""
    d = p - sh
    n = np.linalg.norm(d)
    lim = c.Lh * k
    return sh + d * (lim / n) if n > lim else p


# ================================================================== lever row machines
@override("machine_row")
def machine_row(c, t, L, row, prev):
    """Chest-supported lever row (axle overhead in front) and high row (axle
    low in front, handles start above the head).  The handles travel on the
    lever's arc, so the lever arms keep their length every frame."""
    high = "high" in name_of(row)
    if high:
        piv, Lv, a0, a1 = np.array([1.0, 0.92]), 0.80, 45.0, 4.0       # (y, z), length, start / end angle
        xs = 0.22
    else:
        piv, Lv, a0, a1 = np.array([0.55, 1.62]), 0.785, (15.4 if c.g == "m" else 8.0), -20.0
        xs = 0.2
    a = math.radians(L(a0, a1))

    def grip_yz(a):
        if high:
            return piv + Lv * np.array([-math.cos(a), math.sin(a)])
        return piv + Lv * np.array([math.sin(a), -math.cos(a)])
    gy, gz = grip_yz(a)

    def tgt(D, Hp, c_, sd):
        return reach(c, fam.shoulder(D, Hp, c, sd), np.array([SIDES[sd] * xs, gy, gz]))
    neutral = (P(row, "grip") or "neutral") == "neutral"
    arms = arm_ik(tgt, (0, 0, 1) if neutral else (-1, 0, 0), (0.6, -1, 0.3) if not high else (0.7, -0.6, -0.4),
                  curl=0.9)
    seat_h = 0.5
    eq = [E("row_machine", (0, 0, 0), eid="mach", seat_h=seat_h, chest=False, thigh=high,
            pivot=(float(piv[0]), float(piv[1])), front_y=1.15 if not high else 1.2),
          E("lever_hub", (0, piv[0], piv[1]), eid="hub", dyn=True)]       # axle inside the picture
    if not high:
        # chest pad on the chest (it does not move), stem forward-down to the column
        bone, pt = c.lm["chest"]
        eq.append(dict(kind="chest_pad", M=np.eye(4), id="cpad", shape={}, bone=bone,
                       bone_pt=pt + np.array([0, 0.004, -0.06])))
        eq.append(seg("cstem", lambda pts, D, Hp, c_: c_.lmk(D, Hp, "chest") + np.array([0, 0.13, -0.08]),
                      np.array([0, 1.15, 0.62]), 0.03, "frame"))
    for sd in "LR":
        s = SIDES[sd]
        eq += kit.lever((s * 0.33, piv[0], piv[1]), sd, eid="arm")
        eq.append(H("machine_handles", sd, "db", eid=f"hnd{sd}", width=0.0))
    if high:
        fr = fam.seated(c, seat_h=seat_h, seat_y=0.0, pitch=L(-2, 4), arms=arms, equip=eq, spine=(L(-4, -2), 0, 0))
    else:
        fr = fam.seated(c, seat_h=seat_h, seat_y=0.0, pitch=6, arms=arms, equip=eq)
    return fr


# ================================================================== preacher curls
def _preacher_pad_eq(c, spec, u, top=0.07, length=0.36, arm_r=0.05):
    """Pad under the upper arms: its face is the plane the upper arms lie on
    (direction u, both shoulders), its top edge just below the armpits, its
    column straight down to the base.  Evaluated from the current torso so
    the pad follows the solved shoulders exactly."""
    D, Hp = c.torso(spec)
    m = 0.5 * (Hp[c.r.bi("upperarm01.L")] + Hp[c.r.bi("upperarm01.R")])
    u = unit(np.asarray(u, float))
    nrm = unit(np.cross(X, u))           # up-forward face normal
    if nrm[2] < 0:
        nrm = -nrm
    face0 = m - nrm * arm_r + u * (top + length / 2)
    R = np.stack([X, u, nrm], axis=1)
    out = [dict(kind="preacher_pad", M=_mx(face0, R), id="ppad", shape=dict(length=length), dyn=False)]
    under = face0 - nrm * 0.09
    out.append(seg("ppost", under, np.array([0, under[1], 0.05]), 0.035, "frame"))
    return out, under[1]


def _mx(p, R):
    M = np.eye(4)
    M[:3, :3] = R
    M[:3, 3] = p
    return M


@override("preacher_curl")
def preacher_curl(c, t, L, row, prev):
    """Seated behind the pad: the pad lies under the upper arms with its top
    edge in the armpits, the torso upright behind it, and at the top of the
    curl the forearms stand near vertical in front of the face (never in it)."""
    n = eqw(row)
    single = "single" in n or "one-arm" in n or "concentration" in n
    machine = "machine" in n
    seat_h = 0.585
    v = np.array([0.07, 0.70, -0.71])
    arms = arm_fk(tuple(v), elbow=L(14, 96), thumb="sup", bend=(0, 0.7, 0.7), curl=0.88, world=True)
    # EZ bar (the spec allows it for barbell preacher curls): its short sleeves keep the plates beside the
    # forearms instead of across the face in the side view
    eq = [H("ezbar", "C", "bar", eid="bar")]
    if "dumbbell" in n or single:
        eq = [H("dumbbell", "L"), H("dumbbell", "R")]
    if "cable" in n:
        eq = kit.cable_kit(np.array([0, 1.05, 0.3]), "bar", face=np.array([0, -1, 0]))
    if machine:
        eq = [H("machine_handles", "C", "ball", eid="hnd", width=0.0)]
    if single or P(row, "freeze") == "L":
        # the free arm rests on the pad, hand open beside the working arm
        arms["L"] = arm_fk(tuple(v * np.array([1.6, 1, 1])), elbow=20, sides="L", world=True, thumb="sup", curl=0.3)["L"]
        eq = [e for e in eq if e.get("hand") != "L" and e.get("kind") != "ezbar"]
        if not any(e.get("hand") == "R" for e in eq):
            eq.append(H("dumbbell", "R"))
    feet = {sd: dict(ball=np.array([SIDES[sd] * 0.13, 0.33, 0.13 + SOLE]), yaw=8, heel=0, surf=0.13,
                     pole=np.array([SIDES[sd] * 0.2, 1, 0.5])) for sd in "LR"}
    fr = fam.seated(c, seat_h=seat_h, seat_y=0.0, pitch=8, arms=arms, legs=feet, equip=eq,
                    spine=(5, 0, 0), neck=(L(-4, -8), 0, 0))
    b = fr.build
    vm = v * np.array([0, 1, 1])

    def build():
        spec, eqs, ex = b()
        pad, py = _preacher_pad_eq(c, spec, vm)
        eqs = list(eqs) + pad + [E("preacher_base", (0, 0, 0), eid="pb", height=0.55, foot=0.13, foot_y=0.36,
                                   pad_y=float(py))]
        if machine:
            for sd in "LR":
                s = SIDES[sd]

                def piv(pts, D, Hp, c_, sd=sd, s=s):
                    e = Hp[c.r.bi(f"lowerarm01.{sd}")]
                    return np.array([s * 0.3, e[1], e[2]])

                def tip(pts, D, Hp, c_, sd=sd, s=s):
                    g = pts[f"grip{sd}"]
                    return np.array([s * 0.3, g[1], g[2]])
                eqs += [seg(f"pl{sd}", piv, tip, 0.022, "frame"), seg(f"ph{sd}", tip, f"grip{sd}", 0.016, "rubber")]
        return spec, eqs, ex
    fr.build = build
    return fr


# seen a little from behind the side: the near plate / handle projects in front
# of the face instead of across it at the top of the curl
REG["preacher_curl"].view = (100, 6)


# ================================================================== cable tower beside the athlete
def _smooth(u):
    u = min(max(u, 0.0), 1.0)
    return u * u * (3 - 2 * u)


def tower_kit(pul, face, eid="t", frame=True):
    """Cable column whose pulley wheel is at pul, the column's front facing
    `face` (xy direction from the column toward the athlete).  frame=True:
    the column is part of the camera fit, so the cable never runs out of the
    picture to a machine that is not shown."""
    base, R = kit.tower_at(pul, face)
    return [E("cable_tower", base, R=R, eid=f"tower{eid}", pulley_h=float(pul[2]), dyn=frame)]


def one_handle(pul, eid="p"):
    """Both hands on one D handle, cable from the pulley to the handle."""
    return [dict(H("d_handle", "C", "aim", eid=f"{eid}d"), aim=np.asarray(pul, float)),
            seg(f"{eid}cable", np.asarray(pul, float), ("toward", "gripC", 0.135), kit.CABLE_R, "darksteel")]


@override("pallof_press")
def pallof_press(c, t, L, row, prev):
    """Standing side-on to the column at arm's length (column to the right):
    press out from the sternum; '... and twist' then turns the trunk away from
    the column with the arms straight; 'walk out' side-steps away from the
    column and back with the arms pressed out."""
    n = name_of(row)
    if "kneel" in n or "supine" in n or "partner" in n or "band" in eqw(row):
        return prev(c, t, L, row)
    twist = "twist" in n
    walk = "walk" in n
    if twist:
        tp, tr = _smooth(t / 0.5), _smooth((t - 0.5) / 0.5)
    elif walk:
        tp, tr = 1.0, 0.0
    else:
        tp, tr = t, 0.0
    shift = 0.0

    def tgt(D, Hp, c_, sd):
        Rt = D[c.r.bi("spine01")]
        a = c.lmk(D, Hp, "chest") + Rt @ Y * 0.1
        b = fam.within(c, fam.sh_mid(D, Hp, c), Rt @ Y * c.Lh * 0.95 - Rt @ Z * 0.12, 0.9)
        return a * (1 - tp) + b * tp + Rt @ X * SIDES[sd] * 0.03
    arms = arm_ik(tgt, lambda D, Hp, c_, sd: D[c.r.bi("spine01")] @ Z, (1, -0.5, -0.4), curl=0.9)
    pul = np.array([0.95, 0.35, 1.15 * c.S])
    eq = column(pul, (-1, 0, 0)) + one_handle(pul)
    legs = c.feet(w=c.hw * 1.5, toe=8)
    if walk:
        # two side steps away from the column: the far (left) foot steps, the near foot
        # closes, twice; one foot is always on the floor and the hips stay between the feet
        step = 0.2
        win = {"L": ((0.0, 0.25), (0.5, 0.75)), "R": ((0.25, 0.5), (0.75, 1.0))}
        dx = {}
        for sd in "LR":
            off, lift = 0.0, 0.0
            for a, b in win[sd]:
                u = (t - a) / (b - a)
                off -= step * _smooth(u)
                if 0.0 < u < 1.0:
                    lift = 0.06 * math.sin(math.pi * u)
            dx[sd] = off
            legs[sd]["ball"] = legs[sd]["ball"] + np.array([off, 0, lift])
        shift = 0.5 * (dx["L"] + dx["R"])
        planted = [sd for sd in "LR" if legs[sd]["ball"][2] < SOLE + 0.01]
    else:
        planted = ["L", "R"]
    return c.stand(legs, hk=0.94, px=shift, pel=(6, 0, -10 * tr), spine=(0, 0, -30 * tr), arms=arms,
                   equip=eq, planted=planted or ["L", "R"])


def column(pul, face, eid="t"):
    """Cable column at pul; only its pulley block joins the camera fit (the
    column may rise out of the top of the picture, its pulley stays in)."""
    base, R = kit.tower_at(pul, face)
    return [E("cable_tower", base, R=R, eid=f"tower{eid}", pulley_h=float(pul[2])),
            E("pulley_block", base, R=R, eid=f"pblock{eid}", h=float(pul[2]), dyn=True)]


# ================================================================== cable crunches
@override("crunch")
def crunch(c, t, L, row, prev):
    n = name_of(row)
    if n == "cable crunch":
        # kneeling a long step from the column: the head ends well in front of it
        from .tpl_floor import kneeling
        pul = np.array([0, 1.0, 2.1 * c.S])

        def tgt(D, Hp, c_, sd):
            return c.lmk(D, Hp, "forehead") + X * SIDES[sd] * 0.09 + Y * 0.02 - Z * 0.05
        arms = arm_ik(tgt, (0, 1, 0), (1, 0.5, -1), curl=0.9, fing=(0, 0, 1))

        def junction(pts, D, Hp, c_, p=pul):
            g = pts["gripC"]
            return g + unit(p - g) * 0.22
        eq = column(pul, (0, -1, 0)) + [seg("ccable", pul, junction, kit.CABLE_R, "darksteel")]
        for sd in "LR":
            eq += [seg(f"crope{sd}", junction, f"grip{sd}", 0.012, "ropew"),
                   H("rope_knob", sd, "db", eid=f"cknob{sd}", off=(0, -0.045, 0))]
        return kneeling(c, t, L, row, arms=arms, equip=eq, pitch=L(15, 30), spine=(L(5, 55), 0, 0))
    if n == "cable oblique crunch":
        # standing side-on, column to the right; the right hand holds the handle beside the
        # head and the trunk bends down and sideways toward the column
        pul = np.array([0.75, 0.0, 2.05 * c.S])

        def tgt(D, Hp, c_, sd):
            Rh = D[c.r.bi("head")]
            return c.lmk(D, Hp, "forehead") + Rh @ np.array([0.13, -0.06, -0.02])
        arms = arm_ik(tgt, lambda D, Hp, c_, sd: D[c.r.bi("head")] @ np.array([0, 1.0, 0]), (1, -0.3, -0.5),
                      curl=0.9, sides="R")
        arms.update(arm_fk((0.25, 0.05, -1), elbow=70, bend=(0, 1, 0.5), thumb="fwd", curl=0.4, sides="L"))
        eq = tower_kit(pul, (-1, 0, 0)) + [dict(H("d_handle", "R", "aim", eid="ocd"), aim=pul),
                                            seg("ocable", pul, ("toward", "gripR", 0.135), kit.CABLE_R, "darksteel")]
        legs = c.feet(w=c.hw * 1.6, toe=8)
        return c.stand(legs, hk=0.97, spine=(L(4, 22), L(0, 26), 0), neck=(L(0, 6), L(0, 6), 0), arms=arms,
                       equip=eq)
    return prev(c, t, L, row)


@override("reverse_crunch")
def reverse_crunch(c, t, L, row, prev):
    """Cable reverse crunch: feet toward a low pulley beyond them, straps on
    both ankles joined to the cable."""
    if "cable" not in name_of(row):
        return prev(c, t, L, row)
    fr = prev(c, t, L, row)
    pul = np.array([0, 1.55, 0.12])

    def ring(sd):
        def f(pts, D, Hp, c_):
            r = c_.r
            i = r.bi(f"lowerleg02.{sd}")
            a = r.joint(f"foot.{sd}") + np.array([0, 0, 0.07])
            return Hp[i] + D[i] @ (a - r.H[i])
        return f

    def knot(pts, D, Hp, c_):
        m = 0.5 * (ring("L")(pts, D, Hp, c_) + ring("R")(pts, D, Hp, c_))
        return m + unit(pul - m) * 0.12
    eq = column(pul, (0, -1, 0)) + [seg("rcable", pul, knot, kit.CABLE_R, "darksteel")]
    for sd in "LR":
        eq += [dict(kind="ankle_cuff", M=np.eye(4), id=f"rcuff{sd}", shape={}, bone=f"lowerleg02.{sd}",
                    bone_pt=None, _ankle=sd),
               seg(f"rstrap{sd}", knot, ring(sd), 0.008, "strap")]
    return add_eq(fr, eq)


# ================================================================== high cable curl (crossover)
@override("barbell_curl")
def barbell_curl(c, t, L, row, prev):
    """High cable curl: standing between two high pulleys, upper arms out to
    the sides at shoulder height, palms up; the hands curl to the ears while
    the upper arms stay level.  Both columns are in the picture."""
    if name_of(row) != "high cable curl":
        return prev(c, t, L, row)
    arms = arm_fk((1.0, 0.04, 0.06), elbow=L(10, 140), thumb="sup", bend=(0.0, 0.1, 1.0), curl=0.88, world=True)
    pz = 1.5 * c.S
    eq = []
    for sd in "LR":
        s = SIDES[sd]
        p = np.array([s * 1.05, 0.0, pz])
        eq += tower_kit(p, (-s, 0, 0), eid=sd)
        eq += [dict(H("d_handle", sd, "aim", eid=f"hd{sd}"), aim=p),
               seg(f"hc{sd}", p, ("toward", f"grip{sd}", 0.135), kit.CABLE_R, "darksteel")]
    legs = c.feet(w=c.hw * 1.35, toe=8)
    return c.stand(legs, pel=(2, 0, 0), arms=arms, equip=eq)


# ================================================================== standing hip adduction with a cable / band
@override("hip_adduction_standing")
def hip_adduction_standing(c, t, L, row, prev):
    """The working (left) leg starts out toward the column / anchor on the
    left and is pulled across in front of the standing leg; the strap is on
    the working ankle.  With a cable the near hand holds the column."""
    n = eqw(row)
    cable = "cable" in n
    band = "band" in n
    if not (cable or band):
        return prev(c, t, L, row)
    from .tpl_lower import one_leg_stand
    leg = dict(thigh=np.array([-L(0.38, -0.14), 0.1, -1]), knee=4, kbend=np.array([0, -1, 0]),
               fdir=np.array([0.1, 1, -0.2]))
    if cable:
        pul = np.array([-0.62, 0.0, 0.14])
        eq = column(pul, (1, 0, 0), eid="a") + kit.ankle_cable(pul, "L", eid="a")
        up = np.array([-0.62 - 0.12 - 0.05, 0.16])        # front upright of the column

        def hold(D, Hp, c_, sd):
            sh = fam.shoulder(D, Hp, c, sd)
            return reach(c, sh, np.array([up[0] + 0.05, up[1], sh[2] - 0.18]), 0.97)
        arms = arm_ik(hold, (0, 0, 1), (-0.3, -1, -0.5), curl=0.9, sides="L")
        arms.update(arm_fk((0.3, 0.1, -1), elbow=95, bend=(0, 0.2, 1), thumb="fwd", curl=0.5, sides="R"))
        fr = one_leg_stand(c, t, L, row, leg, hold="none", arms=arms, pel=(2, L(-4, 0), 0), equip=eq)
        return fr
    anchor = np.array([-0.85, 0.05, 0.2])

    def ring(pts, D, Hp, c_):
        r = c_.r
        i = r.bi("lowerleg02.L")
        a = r.joint("foot.L") + np.array([0, 0, 0.07])
        return Hp[i] + D[i] @ (a - r.H[i])
    eq = [E("band_post", (anchor[0] - 0.05, anchor[1], 0), eid="bpost", h=float(anchor[2]), dyn=True),
          dict(kind="ankle_cuff", M=np.eye(4), id="bcuff", shape={}, bone="lowerleg02.L", bone_pt=None, _ankle="L"),
          seg("bband", anchor, ring, 0.008, "band")]
    return one_leg_stand(c, t, L, row, leg, hold="hips", pel=(2, L(-4, 0), 0), equip=eq)


# ================================================================== cable wrist curl
@override("wrist_curl")
def wrist_curl(c, t, L, row, prev):
    fr = prev(c, t, L, row)
    if "cable" not in eqw(row):
        return fr
    pul = np.array([0, 0.95, 0.12])
    fr = filter_eq(fr, lambda e: e["kind"] in ("dumbbell", "barbell"))
    return add_eq(fr, [H("cable_bar", "C", "bar", eid="wbar"),
                       seg("wcable", pul, "gripC", kit.CABLE_R, "darksteel")] + column(pul, (0, -1, 0), eid="w"))


# ================================================================== cable russian twist
@override("russian_twist")
def russian_twist(c, t, L, row, prev):
    """Cable Russian twist: seated beside a low pulley (left), handle at the
    chest turned toward the column, then the trunk turns away from it."""
    if "cable" not in eqw(row):
        return prev(c, t, L, row)
    tw = L(-22, 40)            # column on the left (away from the camera): turn toward it, then away
    legs = {sd: dict(ball=np.array([SIDES[sd] * 0.1 * c.S, 0.48 * c.S, SOLE + 0.08]), yaw=0,
                     heel=-20, pole=np.array([0, 0.3, 1])) for sd in "LR"}
    ext = L(0.10, 0.30)

    def tgt(D, Hp, c_, sd):
        Rt = D[c.r.bi("spine01")]
        return c.lmk(D, Hp, "goblet") + Rt @ Y * ext - Z * 0.08 + Rt @ X * SIDES[sd] * 0.03
    arms = arm_ik(tgt, lambda D, Hp, c_, sd: D[c.r.bi("spine01")] @ Z, (1, -0.4, -0.6), curl=0.9)
    pul = np.array([-1.0, 0.25, 0.3])
    eq = column(pul, (1, 0, 0), eid="r") + one_handle(pul, eid="r")
    from .tpl_floor import MAT
    fr = fam.floor_body(c, pitch=-48, yaw=tw * 0.25, legs=legs, arms=arms, spine=(10, 0, tw * 0.75), py=0.0,
                        equip=[MAT(0.1)] + eq)
    fr.planted = []
    return fr


# ================================================================== squat family set-ups
def _zercher(c, t, L, row):
    """Bar in the elbow crooks: the arms are posed first (FK) and the bar is
    put in the crooks they form, every frame."""
    from .tpl_lower import platform
    ua_v, elbow, bend_v = (0.22, 0.55, -0.8), 128.0, (0.0, 0.6, 1.0)

    def arm(sd):
        def f(D, Hp, c_):
            up, fwd = D[c.r.bi("spine01")] @ Z, D[c.r.bi("spine01")] @ Y
            return dict(ua=c.arm_dir(D, ua_v, sd), elbow=elbow, bend=unit(up + fwd), thumb="up", curl=0.6)
        return f
    arms = {sd: arm(sd) for sd in "LR"}

    def bar(D, Hp, c_, ex):
        up, fwd = D[c.r.bi("spine01")] @ Z, D[c.r.bi("spine01")] @ Y
        crooks = []
        for sd in "LR":
            ua = c.arm_dir(D, ua_v, sd)
            el = fam.shoulder(D, Hp, c, sd) + ua * c.r.dims[sd]["L1"]
            b = unit(orth(unit(up + fwd), ua))
            a = math.radians(elbow)
            fa = math.cos(a) * ua + math.sin(a) * b          # forearm direction
            crooks.append(el + unit(fa - ua) * 0.062)
        m = 0.5 * (crooks[0] + crooks[1])
        ex["bar"] = m
        return E("barbell", m, None, eid="bar", dyn=True)
    legs = c.feet(w=c.hw * 1.3 + 0.08, toe=22)
    legs, peq = platform(c, row, legs)
    return c.stand(legs, hk=L(0.985, 0.56), pel=(L(3, 26), 0, 0), spine=(L(0, 4), 0, 0), neck=(L(0, -18), 0, 0),
                   arms=arms, load=0.5, equip=[bar] + peq)


def _bar_assisted_dome(c, t, L, row):
    """Squat on the dome holding a fixed bar in front at chest height."""
    from .tpl_lower import platform
    bar_y, bar_z = 0.47 * c.S, 0.98 * c.S + 0.21
    legs = c.feet(w=c.hw * 1.2 + 0.06, toe=14)
    legs, peq = platform(c, row, legs)

    def tgt(D, Hp, c_, sd):
        sh = fam.shoulder(D, Hp, c, sd)
        g = np.array([SIDES[sd] * 0.24, bar_y, bar_z])
        return g
    arms = arm_ik(tgt, (-1, 0, 0), (0.4, -0.3, -1), curl=0.9)
    eq = [E("fixed_bar", (0, bar_y, 0), eid="fbar", h=float(bar_z), width=1.7, dyn=True)] + peq
    return c.stand(legs, hk=L(0.985, 0.6), pel=(L(2, 26), 0, 0), spine=(L(0, 4), 0, 0), neck=(L(0, -14), 0, 0),
                   arms=arms, balance=None, equip=eq)


def _cable_row_squat(c, t, L, row):
    """Squat with straight arms on the handle (first half), then rise while
    rowing it to the stomach (second half); the column stands in front."""
    sq = math.sin(math.pi * min(max(t, 0.0), 1.0))
    rw = _smooth((t - 0.5) / 0.5)
    pul = np.array([0, 1.35, 1.0])

    def tgt(D, Hp, c_, sd):
        m = fam.sh_mid(D, Hp, c)
        far = m + unit(pul - m) * c.Lh * 0.95
        near = c.lmk(D, Hp, "chest") - Z * 0.16 + Y * 0.12
        return far * (1 - rw) + near * rw + X * SIDES[sd] * 0.03
    arms = arm_ik(tgt, (0, 0, 1), (0.6, -1, -0.3), curl=0.9)
    legs = c.feet(w=c.hw * 1.3 + 0.08, toe=18)
    eq = tower_kit(pul, (0, -1, 0), eid="q") + one_handle(pul, eid="q")
    return c.stand(legs, hk=0.985 - 0.4 * sq, pel=(3 + 24 * sq, 0, 0), spine=(4 * sq, 0, 0), neck=(-14 * sq, 0, 0),
                   arms=arms, equip=eq, load=0.15)


@override("squat")
def squat(c, t, L, row, prev):
    n = name_of(row)
    if "zercher" in n:
        return _zercher(c, t, L, row)
    if "bar assisted dome" in n:
        return _bar_assisted_dome(c, t, L, row)
    if n == "cable row with squat":
        return _cable_row_squat(c, t, L, row)
    return prev(c, t, L, row)


# ================================================================== balance trainer always in the picture
from .templates import Tpl as _Tpl  # noqa: E402

_pose0 = _Tpl.pose


def _pose_dome_in_frame(self, ctx, t, row, warm=None):
    """A balance trainer is part of the camera fit (it stood below the feet
    and was cut by the bottom edge of the picture)."""
    p = _pose0(self, ctx, t, row, warm=warm)
    for e in p.equip:
        if e["kind"] == "bosu":
            e["dyn"] = True
    return p


_Tpl.pose = _pose_dome_in_frame


# ================================================================== cardio machines
@override("rower")
def rower(c, t, L, row, prev):
    """Air rower: the seat rides on the monorail with the hips, the feet are
    strapped on the footplates and the handle hangs on the chain."""
    fr = prev(c, t, L, row)
    seat_y = L(0.25, -0.35)
    fr = filter_eq(fr, lambda e: e["kind"] == "rower" or e["id"] == "chain")
    return add_eq(fr, [E("rower_frame", (0, 0, 0), eid="rwf", dyn=True),
                       E("rower_seat", (0, seat_y, 0.43), eid="rws", dyn=True),
                       H("row_handle", "C", "bar", eid="rwh"),
                       seg("rwchain", np.array([0, 0.98, 0.47]), "gripC", 0.005, "darksteel")])


@override("bike")
def bike(c, t, L, row, prev):
    """Stationary bike: saddle, handlebar the hands hold, flywheel, and the
    cranks with pedals under the feet turning with them."""
    if name_of(row) != "stationary bike":
        return prev(c, t, L, row)
    crank = np.array([0, 0.3, 0.42])
    rc = 0.17
    a = 2 * math.pi * t
    seat = np.array([0, -0.2, 0.93])
    bars = np.array([0.52, 1.17])
    legs, pins = {}, {}
    for sd, ph in (("R", a), ("L", a + math.pi)):
        s = SIDES[sd]
        p = crank + np.array([s * 0.14, rc * math.cos(ph), rc * math.sin(ph)])
        pins[sd] = p
        legs[sd] = dict(ankle=p + np.array([0, -0.085, 0.075]), fdir=np.array([0, 1, -0.15]),
                        pole=np.array([s * 0.1, 1, 0.3]))
    arms = arm_ik(lambda D, Hp, c_, sd: np.array([SIDES[sd] * 0.22, bars[0] - 0.02, bars[1] + 0.02]),
                  (-1, 0, 0), (0.6, -0.6, -0.6), curl=0.92)
    eq = [E("bike_frame", (0, 0, 0), eid="bk", dyn=True, crank=(float(crank[1]), float(crank[2])),
            seat=(float(seat[1]), float(seat[2]) - 0.03), bars=(float(bars[0]), float(bars[1])))]
    for sd, p in pins.items():
        s = SIDES[sd]
        hub = crank + np.array([s * 0.07, 0, 0])
        eq += [seg(f"crank{sd}", hub, p - np.array([s * 0.02, 0, 0]), 0.016, "darksteel"),
               E("pedal", p + np.array([0, 0.01, -0.005]), eid=f"ped{sd}")]
    return c.stand(legs, pz=seat[2] + 0.1, py=seat[1], pel=(22, 0, 0), spine=(8, 0, 0), arms=arms, balance=None,
                   reach=False, planted=(), equip=eq,
                   settle=[("plane", seat + np.array([0, 0, 0.03]), Z, X, 0.1, Y, 0.14, PAD_SINK, "pelvis")])


@override("elliptical")
def elliptical(c, t, L, row, prev):
    """Elliptical: feet on pedals carried by rails from the rear crank to
    rollers on the front ramps; hands on handle arms pivoting at the column."""
    s = L(1, -1)
    base = np.array([0, 0.0, 0.32])
    legs = {sd: dict(ball=base + np.array([SIDES[sd] * 0.12, 0.25 * s * SIDES[sd], 0.06 * s * SIDES[sd] + 0.04]),
                     yaw=0, heel=8) for sd in "LR"}

    def hand(D, Hp, c_, sd):
        sh = fam.shoulder(D, Hp, c, sd)
        return fam.within(c, sh, np.array([SIDES[sd] * 0.05, 0.36 - 0.13 * s * SIDES[sd], -0.3]), 0.85)
    arms = arm_ik(hand, (0, 0, 1), (0.4, -1, -0.3), curl=0.9)
    eq = [E("elliptical_frame", (0, 0, 0), eid="elf", dyn=True)]
    for sd in "LR":
        sg = SIDES[sd]
        u = s * sg
        ball = legs[sd]["ball"]
        ped = ball + np.array([0, -0.07, -SOLE - 0.012])
        pin = np.array([sg * 0.13, -0.72 + 0.2 * u, 0.38 + 0.12 * sg * math.sqrt(max(0.0, 1 - u * u))])
        roller = np.array([sg * 0.18, 0.56, 0.16])
        eq += [seg(f"elr{sd}a", pin, ped - np.array([0, 0.12, 0.02]), 0.022, "frame"),
               seg(f"elr{sd}b", ped - np.array([0, 0.12, 0.02]), roller, 0.022, "frame"),
               E("pedal", ped, eid=f"elp{sd}", w=0.13, length=0.36),
               seg(f"elh{sd}", np.array([sg * 0.12, 0.74, 0.62]), f"grip{sd}", 0.02, "frame")]
    return c.stand(legs, hk=None, pz=c.pz * 0.97 + 0.36, pel=(6, 0, 0), arms=arms, balance=None,
                   equip=eq, planted=())


@override("treadmill_run")
def treadmill_run(c, t, L, row, prev):
    """Brisk walking: a walking stride on the floor (always one foot down,
    knees nearly straight at heel strike, arms bent and swinging)."""
    if "walk" not in name_of(row):
        return prev(c, t, L, row)
    ph = 2 * math.pi * t
    step = 0.62 * c.S

    def foot(sd, off):
        q = (t + off) % 1.0     # noqa
        # stance 0..0.6 (foot on the floor moving back under the body), swing 0.6..1 (forward, lifted)
        if q < 0.6:
            u = q / 0.6
            y = step / 2 - step * u
            heel = max(0.0, (u - 0.7) / 0.3) * 35
            toe_up = max(0.0, 1 - u / 0.12) * 12
            z = 0.19 * math.sin(math.radians(toe_up))     # heel strike: toes up, the heel stays on the floor
        else:
            u = (q - 0.6) / 0.4
            y = -step / 2 + step * _smooth(u)
            heel = 30 * (1 - u) ** 2
            z = 0.075 * math.sin(math.pi * min(1.0, u * 1.15)) + 0.03 * (1 - u) * (u > 0)
            toe_up = 0.0
        L_ = c.foot(SIDES[sd] * c.hw * 0.48, y, 6, heel, z)
        if toe_up:
            L_["heel"] = -toe_up
        return L_, q < 0.6
    legs, planted = {}, []
    for sd, off in (("R", 0.0), ("L", 0.5)):
        lg, down = foot(sd, off)
        legs[sd] = lg
        if down:
            planted.append(sd)
    sw = math.sin(ph + math.pi / 2)
    arms = {"R": arm_fk((0.1, 0.45 * sw, -0.85), elbow=85, sides="R")["R"],
            "L": arm_fk((0.1, -0.45 * sw, -0.85), elbow=85, sides="L")["L"]}
    return c.stand(legs, hk=0.985, pel=(4, 0, 0), arms=arms, balance="com", planted=planted)


# ================================================================== sled drag / pull
@override("sled_push")
def sled_push(c, t, L, row, prev):
    n = name_of(row)
    if not ("drag" in n or "pull" in n):
        return prev(c, t, L, row)
    step = 0.45 * c.S
    if "drag" in n:
        # facing the sled, arms straight on the rope, leaning back, short backward steps
        legs = {"R": c.foot(c.hw * 0.55, L(step / 2, -step / 2), 8, L(0, 25)),
                "L": c.foot(-c.hw * 0.55, L(-step / 2, step / 2), 8, L(25, 0))}
        sled = np.array([0, 1.55, 0])
        arms = fam.arm_fk((0.1, 0.55, -0.85), elbow=5, thumb="in", world=True)
        eq = [E("sled", sled, eid="sled", dyn=True),
              seg("ropeL", "gripL", sled + np.array([-0.08, -0.47, 0.1]), 0.012, "rope"),
              seg("ropeR", "gripR", sled + np.array([0.08, -0.47, 0.1]), 0.012, "rope")]
        return c.stand(legs, hk=0.8, pel=(-12, 0, 0), arms=arms, equip=eq, planted=(), balance=None,
                       neck=(10, 0, 0))
    # sled pull: back to the sled, harness straps from the hips, leaning forward, walking forward
    legs = {"R": c.foot(c.hw * 0.55, L(step / 2, -step / 2), 8, L(10, 55)),
            "L": c.foot(-c.hw * 0.55, L(-step / 2, step / 2), 8, L(55, 10))}
    sled = np.array([0, -1.75, 0])
    sw = L(1, -1)
    arms = {"R": arm_fk((0.1, -0.5 * sw, -0.8), elbow=85, sides="R")["R"],
            "L": arm_fk((0.1, 0.5 * sw, -0.8), elbow=85, sides="L")["L"]}

    def belt(sd):
        def f(pts, D, Hp, c_):
            r = c_.r
            i = r.bi("root")
            p = r.joint("root") + np.array([SIDES[sd] * 0.15, -0.1, 0.05])
            return Hp[i] + D[i] @ (p - r.H[i])
        return f
    eq = [E("sled", sled, eid="sled", dyn=True)]
    for sd in "LR":
        eq.append(seg(f"hs{sd}", belt(sd), sled + np.array([SIDES[sd] * 0.08, 0.45, 0.1]), 0.014, "strap"))
    eq.append(seg("hbelt", belt("L"), belt("R"), 0.02, "strap"))
    return c.stand(legs, hk=0.82, pel=(24, 0, 0), arms=arms, equip=eq, planted=(), balance=None,
                   neck=(-16, 0, 0))


# ================================================================== band rear delt fly
@override("rear_delt_raise")
def rear_delt_raise(c, t, L, row, prev):
    """Band reverse fly standing upright facing a band anchored at shoulder
    height: hands start crossed in front, arms open out in line with the body."""
    n = eqw(row)
    if "band" not in n or "seated" in n or "bent" in name_of(row) or "fly" not in name_of(row):
        return prev(c, t, L, row)
    arms = {"R": arm_fk((L(-0.12, 1.0), L(1.0, 0.05), L(0.0, 0.02)), elbow=L(14, 10), thumb=(0, 0, 1), curl=0.88,
                        world=True, bend=(0, 0, 1), sides="R")["R"],
            "L": arm_fk((L(-0.18, 1.0), L(1.0, 0.05), L(-0.03, 0.02)), elbow=L(14, 10), thumb=(0, 0, 1), curl=0.88,
                        world=True, bend=(0, 0, 1), sides="L")["L"]}
    zs = c.z_sh - 0.02
    anchor = np.array([0, 1.15, zs])
    eq = [E("band_post", (0, anchor[1] + 0.05, 0), eid="rpost", h=float(zs), dyn=True),
          seg("rbandL", anchor + np.array([-0.03, 0, 0]), "gripL", 0.008, "band"),
          seg("rbandR", anchor + np.array([0.03, 0, 0]), "gripR", 0.008, "band")]
    legs = c.feet(w=c.hw * 1.2, toe=8)
    return c.stand(legs, hk=0.97, pel=(2, 0, 0), arms=arms, equip=eq, balance="com")


# ================================================================== wall knee drives
@override("standing_knee_raise")
def standing_knee_raise(c, t, L, row, prev):
    """Wall knee drive: leaning into the wall on straight arms, the left knee
    drives up.  The knee bends toward -Y/-Z, a direction never parallel to
    the thigh (the old bend direction flipped the shin as the thigh came level),
    and the wall casts no shadow across the floor."""
    if "wall" not in name_of(row):
        return prev(c, t, L, row)
    wall_y = 0.78 * c.S
    lean = dict(thigh=np.array([-0.05, L(-0.25, 0.85), L(-1, 0.1)]), knee=L(10, 100),
                kbend=unit(np.array([0, -1, -1])), fdir=np.array([0, L(0.3, 0.2), -1]))
    legs = {"R": c.foot(c.hw * 0.4, -0.18 * c.S, 8, 35), "L": lean}
    arms = arm_ik(lambda D, Hp, c_, sd: np.array([SIDES[sd] * 0.22, wall_y - 0.035, 1.3 * c.S]), (-1, 0, 0),
                  (0.4, -1, -0.3), key="palm", curl=0.0, fing=(0, 0.1, 1))
    fr = c.stand(legs, hk=0.97, pel=(22, 0, 0), arms=arms, balance=None, planted=["R"],
                 equip=[E("wall", (0, wall_y, 0), R=rz(180), eid="wall", shadow=False)])
    fr.cons.append(("reach_arms", Y, ["L", "R"]))
    return fr


# ================================================================== lateral step-up with knee drive
@override("step_up")
def step_up(c, t, L, row, prev):
    """Lateral step-up with knee drive: the left foot leaves the floor, comes
    up beside the box and drives on into a high knee in front; one continuous
    foot path (the old one switched from a foot target to a thigh angle at
    mid-rep and the foot jumped)."""
    n = eqw(row)
    if not ("lateral" in n and "knee drive" in n):
        return prev(c, t, L, row)
    box_h = 0.45 * c.S
    up = dict(ball=np.array([c.hw * 0.5 + 0.38, c.ball_y - 0.05, box_h + SOLE]), yaw=8, heel=0)
    pz0, pz1 = c.pz * 0.98 - 0.02, c.pz * 0.99 + box_h
    x0 = -c.hw * 0.5
    x1 = c.hw * 0.5 + 0.38 - c.hw * 0.95
    u1 = _smooth(t / 0.55)
    u2 = _smooth((t - 0.45) / 0.55)
    kd_y, kd_z = 0.36 * c.S, pz1 - 0.66 * c.S
    x = x0 + (x1 - x0) * u1
    y = kd_y * u2
    z = (box_h * 0.55) * u1 + 0.12 * math.sin(math.pi * u1) * (1 - u2) + (kd_z - box_h * 0.55) * u2
    heel = 28 * math.sin(math.pi * min(t / 0.55, 1.0)) * (1 - u2) + 30 * u2
    left = c.foot(x, y, 8, heel, z=max(z, 0.0))
    legs = {"L": left, "R": up}
    box = E("plyo_box", (up["ball"][0], up["ball"][1] - 0.05, 0), eid="box", size=(0.6, 0.5, box_h))
    return c.stand(legs, hk=None, pz=pz0 + (pz1 - pz0) * _smooth(t / 0.8), px=(up["ball"][0] - 0.12) * _smooth(t / 0.8),
                   pel=(L(14, 4), 0, 0),
                   hold="none", hold2="fwd", mix=L(0, 0.6), equip=[box], planted=["R"],
                   wsupport=(L(0.4, 0.0), L(0.6, 1.0)), neck=(L(-10, 0), 0, 0))


# ================================================================== bounds
def _cyc(keys, q):
    """Cyclic smooth interpolation over [(phase, value)] keys (phase 0..1)."""
    ks = sorted(keys)
    ks2 = ks + [(ks[0][0] + 1.0, ks[0][1])]
    for (a, va), (b, vb) in zip(ks2[:-1], ks2[1:]):
        if a <= q < b or (q < ks[0][0] and False):
            w = _smooth((q - a) / (b - a))
            return np.asarray(va, float) * (1 - w) + np.asarray(vb, float) * w
    q = q + 1.0
    for (a, va), (b, vb) in zip(ks2[:-1], ks2[1:]):
        if a <= q < b:
            w = _smooth((q - a) / (b - a))
            return np.asarray(va, float) * (1 - w) + np.asarray(vb, float) * w
    return np.asarray(ks[0][1], float)


@override("broad_jump")
def broad_jump(c, t, L, row, prev):
    """Bounds (cycle): push off the right foot with the left knee driven high,
    a long flight with the legs split, land on the left foot, then the same
    to the other side; running arms.  Shown on the spot (the stance foot
    travels back under the body)."""
    if "bound" not in name_of(row):
        return prev(c, t, L, row)
    q = t % 1.0
    S = c.S
    # pelvis: low at mid-stance, high in the flights
    pz = c.pz * 0.9 + 0.13 * max(0.0, math.sin(2 * math.pi * (q - 0.25) * 2 + math.pi / 2)) * 0 + \
        0.12 * (0.5 - 0.5 * math.cos(4 * math.pi * (q - 0.125)))
    legs = {}
    planted = []
    for sd, off in (("R", 0.0), ("L", 0.5)):
        s = SIDES[sd]
        p = (q - off) % 1.0
        if p < 0.25:            # stance: lands in front, pushes off behind
            u = p / 0.25
            y = 0.28 * S - 0.62 * S * u
            heel = 45 * max(0.0, (u - 0.55) / 0.45)
            legs[sd] = c.foot(s * c.hw * 0.45, y, 6, heel, 0.0)
            planted.append(sd)
        else:
            # swing: trail behind, knee drive high in front, reach to land
            th = _cyc([(0.25, (0, -0.6, -1.0)), (0.45, (0, -0.35, -1.0)), (0.62, (0, 0.6, -0.55)),
                       (0.78, (0, 1.0, 0.05)), (0.97, (0, 0.45, -1.0))], p)
            kn = float(_cyc([(0.25, (15,)), (0.45, (95,)), (0.62, (115,)), (0.78, (95,)), (0.97, (12,))], p)[0])
            legs[sd] = dict(thigh=unit(np.array([s * 0.06, th[1], th[2]])), knee=kn, kbend=unit(np.array([0, -1, -1])),
                            fdir=np.array([0, 0.5, -1]))
    sw = math.cos(2 * math.pi * q)
    arms = {"R": arm_fk((0.12, 0.75 * sw, -0.7), elbow=80, sides="R")["R"],
            "L": arm_fk((0.12, -0.75 * sw, -0.7), elbow=80, sides="L")["L"]}
    fr = c.stand(legs, pz=pz, pel=(14, 0, 0), arms=arms, balance=None, reach=bool(planted), planted=planted)
    fr.free_legs = [sd for sd in "LR" if sd not in planted]
    return fr


# ================================================================== balance trainer: kneeling good morning
@override("good_morning")
def good_morning(c, t, L, row, prev):
    """Single-leg kneeling good morning on a balance trainer: the right knee
    on the dome, the left leg straight forward on its heel, hands behind the
    head; the hips hinge forward over the straight leg."""
    n = name_of(row)
    if not ("kneeling" in n and ("balance" in n or "bosu" in eqw(row))):
        return prev(c, t, L, row)
    dome = 0.21
    T1 = c.r.dims["R"]["T1"]
    knee = dict(thigh=np.array([0.06, -0.02, -1]), knee=62, kbend=np.array([0, -1, 0.0]),
                fdir=np.array([0, -1, -0.6]), fup=np.array([0, 0.3, 1]))
    front = c.foot(-c.hw * 0.5, 0.5 * c.S, 4, -30, 0.083)
    front["surf"] = 0.0          # toes up: the heel is on the floor
    legs = {"R": knee, "L": front}
    eq = [E("bosu", (c.hw * 0.5, -0.03, 0), eid="bosu", dyn=True), E("mat", (0, 0.0, 0), eid="mat")]
    return c.stand(legs, pz=dome + T1 - 0.04, py=0.0, pel=(L(4, 50), 0, 0), spine=(L(0, 4), 0, 0),
                   neck=(L(0, -18), 0, 0), hold="head", balance=None, reach=True, planted=["L"], equip=eq)


# ================================================================== balance trainer: lying toe tap
@override("dead_bug")
def dead_bug(c, t, L, row, prev):
    """Balance trainer lying toe tap: bridge with both feet on the dome; the
    right foot leaves it, taps the floor beside the trainer and returns while
    the hips stay up (alternating sides)."""
    if "toe tap" not in name_of(row):
        return prev(c, t, L, row)
    from .tpl_floor import MAT, palms_floor
    fy = 0.58 * c.S
    top = 0.215
    u = L(0.0, 1.0)
    legs = {}
    for sd in "LR":
        s = SIDES[sd]
        legs[sd] = dict(ball=np.array([s * 0.1, fy, top + SOLE]), yaw=4, heel=0, surf=top, pole=np.array([s * 0.1, 0.2, 1]))
    x = 0.1 + 0.32 * u
    z = (top + SOLE) * (1 - u) + SOLE * u + 0.12 * math.sin(math.pi * u)
    legs["R"] = dict(ball=np.array([x, fy + 0.04 * u, z]), yaw=4 + 10 * u, heel=0, surf=top * (1 - u),
                     pole=np.array([0.4, 0.2, 1]))
    arms = palms_floor(c, 0.02, w=0.25)
    eq = [MAT(0.1), E("bosu", (0, fy - 0.05, 0), eid="bosu", dyn=True)]
    fr = fam.floor_body(c, pitch=-118, legs=legs, arms=arms, py=0.0, equip=eq,
                        cons=[("joint", "upperarm01.R", 1, -0.38 * c.S)])
    fr.planted = ["L"] if u > 1e-3 else ["L", "R"]
    return fr


# ================================================================== balance trainer (dome down) under the hands
def _pike_hands_up(c, hand_y, hz, feet_y, heel, guess):
    """Pitch and pelvis with straight legs (ankles at feet_y on the floor)
    and straight arms to palms at (hand_y, hz): for each pitch the hip joint
    lies where a leg-length circle around the ankle meets an arm-length
    circle around the hand (shifted by the trunk); the pitch nearest `guess`
    with a solution wins."""
    from .rig import body_rot
    sh_r = c.r.joint("upperarm01.R")
    hj_r = c.r.joint("upperleg01.R")
    an_r = c.r.joint("foot.R")
    leg = np.linalg.norm(hj_r - an_r) * 0.99
    arm = c.Lpf * 0.97
    a_h = math.radians(heel)
    A = np.array([feet_y + c.ball_y * 0 - c.ball_y * math.cos(a_h) + c.ball_y, an_r[2] * math.cos(a_h) + c.ball_y * math.sin(a_h)])
    best = None
    for pitch in np.linspace(60, 175, 231):
        R = body_rot(pitch, 0, 0)
        oh = (R @ (hj_r - c.r.pc_rest))[[1, 2]]
        os_ = (R @ (sh_r - c.r.pc_rest))[[1, 2]]
        B = np.array([hand_y, hz]) - (os_ - oh)          # hip must be `arm` from here
        d = np.linalg.norm(B - A)
        if d > leg + arm or d < abs(leg - arm) or d < 1e-6:
            continue
        x = (leg * leg - arm * arm + d * d) / (2 * d)
        h = math.sqrt(max(leg * leg - x * x, 0.0))
        e = (B - A) / d
        nrm = np.array([-e[1], e[0]])
        Hs = [A + e * x + nrm * h, A + e * x - nrm * h]
        Hj = max(Hs, key=lambda q: q[1 if False else 1])
        pel = np.array([0.0, Hj[0] - oh[0], Hj[1] - oh[1]])
        if pel[2] < 0.3:
            continue
        err = abs(pitch - guess)
        if best is None or err < best[0]:
            best = (err, pitch, pel)
    return best[1], best[2]


@override("walkout")
def walkout(c, t, L, row, prev):
    """Balance trainer walk-out: hands grip the edges of the upturned trainer;
    the feet walk back in small alternating steps from a hinge (hips high,
    feet near the trainer) to a straight plank, and in again."""
    if not ("balance" in name_of(row) or "bosu" in eqw(row)):
        return prev(c, t, L, row)
    hz = 0.25
    hand_y = 0.0
    near, far = 0.78 * c.S, 1.27 * c.S
    # three steps per foot, alternating (right, left, ...), one foot always down
    nst = 3
    fy, lift = {}, {}
    for sd, k0 in (("R", 0), ("L", 1)):
        off, lf = 0.0, 0.0
        for k in range(nst):
            a = (2 * k + k0) / (2 * nst)
            b = a + 1.0 / (2 * nst)
            u = (t - a) / (b - a)
            off += (far - near) / nst * _smooth(u)
            if 0.0 < u < 1.0:
                lf = 0.05 * math.sin(math.pi * u)
        fy[sd] = hand_y - near - off
        lift[sd] = lf
    feet_y = 0.5 * (fy["L"] + fy["R"])
    heel = 30 - 10 * t
    pitch, pel = _pike_hands_up(c, hand_y, hz, feet_y + c.ball_y * 0, heel, 128 - 52 * _smooth(t))
    hw = 0.42
    arms = arm_ik(lambda D, Hp, c_, sd: np.array([SIDES[sd] * hw / 2, hand_y, hz + 0.004]), (-1, 0.2, 0),
                  (0.2, -0.3, 1.0), key="palm", curl=0.35, fing=(0, 1, 0))
    legs = {sd: c.foot(SIDES[sd] * 0.1 * c.S, fy[sd] - c.ball_y, 0, heel, lift[sd]) for sd in "LR"}
    eq = [E("bosu", (0, hand_y, hz), R=fam.rx(180), eid="bosu", dyn=True), E("mat", (0, -0.6, 0), eid="mat")]
    return c.stand(legs, pz=pel[2], py=pel[1], pel=(pitch, 0, 0), arms=arms, balance=None, reach=False,
                   equip=eq, neck=(20, 0, 0), planted=["L", "R"])


@override("pike")
def pike(c, t, L, row, prev):
    """Stability-ball knee tuck with the hands on an upturned balance trainer:
    shins on the ball, the knees pull in toward the chest and the ball rolls
    in under the shins."""
    n = name_of(row)
    if not ("knee tuck" in n and ("balance" in n or "bosu" in eqw(row))):
        return prev(c, t, L, row)
    hz = 0.25
    u = L(0.0, 1.0)
    r_ball = 0.33

    ay = (-1.33 + 0.5 * u) * c.S
    az = 2 * r_ball + 0.05
    legs_over = {sd: dict(ankle=np.array([SIDES[sd] * 0.12, ay, az]), fdir=np.array([0, -1, -0.2 - 0.6 * u]),
                          fup=np.array([0, -0.2, -1]), pole=np.array([SIDES[sd] * 0.2, 0.4, -1.0]))
                 for sd in "LR"}

    def shin_ball(D, Hp):
        return np.array([0.0, ay + 0.1, r_ball])

    eq = [E("bosu", (0, 0.0, hz), R=fam.rx(180), eid="bosu", dyn=True), E("mat", (0, -0.6, 0), eid="mat")]
    fr = fam.plank(c, down=0.0, hand_w=0.42, hands_h=hz, feet_h=0.5, equip=eq, hands_on=True,
                   hip_raise=0.0, legs_over=legs_over)
    fr.planted = []
    fr.free_feet_ok = True
    b = fr.build

    def build():
        spec, eqs, ex = b()
        D, Hp = c.torso(spec)
        return spec, list(eqs) + [E("stability_ball", shin_ball(D, Hp) - np.array([0, 0, r_ball]), eid="sb",
                                    dyn=True)], ex
    fr.build = build
    return fr


# ================================================================== dumbbell cleans and snatches
@override("kb_clean")
def kb_clean(c, t, L, row, prev):
    """Dumbbell clean / hang snatch: the bells start at the sides of the
    thighs (one bell: between the knees) and travel up in front of the body
    to the rack or overhead, never through the trunk."""
    n = eqw(row)
    if "dumbbell" not in n or "kettlebell" in n or "jerk" in n or "press" in n:
        return prev(c, t, L, row)
    snatch = "snatch" in n
    single = "single" in n
    sides = "R" if single else "LR"
    legs = c.feet(w=c.hw * 1.6, toe=14)
    u = L(0, 1)

    def tgt(D, Hp, c_, sd):
        m = fam.shoulder(D, Hp, c, sd)
        Rt = D[c.r.bi("spine01")]
        root = c.J(D, Hp, "root")
        hang_y = max(root[1] + 0.16, m[1] + 0.02)          # under the shoulders, in front of the thighs
        if single:
            lo = np.array([root[0] + 0.02, hang_y, c.z_hip * 0.5])
        else:
            lo = np.array([m[0] + SIDES[sd] * 0.05, hang_y - 0.06, c.z_hip * 0.55])
        hi = m + Z * c.Lh * 0.95 + Y * 0.02 if snatch else m + Y * 0.12 - Z * 0.06 + X * SIDES[sd] * 0.02
        ctrl = np.array([m[0] + SIDES[sd] * 0.04, m[1] + 0.42, 0.5 * (lo[2] + hi[2]) - 0.05])
        p = lo * (1 - u) ** 2 + 2 * ctrl * u * (1 - u) + hi * u * u        # out in front, not through the trunk
        d = p - m
        return m + unit(d) * min(np.linalg.norm(d), c.Lh * 0.96)

    def fing(D, Hp, c_, sd):
        a = math.pi * u
        return unit(-Z * math.cos(a) + Y * math.sin(a) * 0.9 + 1e-6 * Y)
    # thumbs point in toward the midline: never along the fingers, which turn from down to
    # forward to up (thumb and fingers parallel gave the dumbbell a flat matrix: it vanished)
    arms = arm_ik(tgt, (-1, 0, 0.15), (1, -0.5, -0.3), curl=0.9, sides=sides, fing=fing)
    if single:
        arms.update(arm_fk((0.3, 0.1, -1), elbow=12, sides="L"))
    eq = [H("dumbbell", sd) for sd in sides]
    return c.stand(legs, hk=L(0.8, 0.95 if snatch else 0.92), pel=(L(42, 2), 0, 0), arms=arms, equip=eq,
                   balance="com", load=0.15, neck=(L(-22, 0), 0, 0))


# ================================================================== dumbbell punches
@override("chest_press_standing")
def chest_press_standing(c, t, L, row, prev):
    fr = prev(c, t, L, row)
    if "dumbbell" not in eqw(row):
        return fr

    def add(spec, eq, ex):
        if any(e["kind"] == "dumbbell" for e in eq):
            return []
        return [H("dumbbell", sd, eid=f"pdb{sd}", head=0.045) for sd in spec.get("arm", {})]
    return add_eq(fr, add)


# ================================================================== seal row
@override("barbell_row")
def barbell_row(c, t, L, row, prev):
    """Seal row: lying prone on a high flat bench, arms hanging straight
    down to the bar, which is rowed up to the underside of the bench."""
    if "seal" not in name_of(row):
        return prev(c, t, L, row)
    bh = 0.78
    u = L(0, 1)
    gw = c.sw * 1.35

    def tgt(D, Hp, c_, sd):
        sh = fam.shoulder(D, Hp, c, sd)
        lo = reach(c, sh, np.array([SIDES[sd] * gw / 2, sh[1] + 0.02, sh[2] - c.Lh]), 0.82)
        hi = np.array([SIDES[sd] * gw / 2, sh[1] - 0.06, bh - 0.15])
        return lo * (1 - u) + hi * u
    arms = arm_ik(tgt, lambda D, Hp, c_, sd: -SIDES[sd] * X, (0.5, -0.4, 0.8), curl=0.85,
                  fing=lambda D, Hp, c_, sd: -Y)
    legs = {sd: dict(thigh=np.array([SIDES[sd] * 0.04, -1.0, 0.02]), knee=8, kbend=np.array([0, 0, 1.0]),
                     fdir=np.array([0, -0.3, -1])) for sd in "LR"}
    from .rig import body_rot
    pitch = 90.0
    eq = [E("bench", (0, -0.15, 0), eid="sbench", height=bh, length=1.5), H("barbell", "C", "bar", eid="bar")]
    fr = c.stand(legs, pz=bh + 0.12, py=-0.45, pel=(pitch, 0, 0), neck=(-25, 0, 0), arms=arms, balance=None,
                 reach=False, planted=(), equip=eq,
                 settle=[("plane", np.array([0, -0.15, bh]), Z, X, 0.15, Y, 0.7, PAD_SINK)])
    fr.free_feet_ok = True
    return fr


# ================================================================== lighter plates where they covered the athlete
def _plates(fr, r):
    b = fr.build

    def build():
        spec, eq, ex = b()
        out = []
        for e in eq:
            if e["kind"] in ("barbell", "smith_bar"):
                e = dict(e, shape=dict(e.get("shape", {}), plate_r=r))
            out.append(e)
        return spec, out, ex
    fr.build = build
    return fr


@override("glute_bridge")
def glute_bridge(c, t, L, row, prev):
    fr = prev(c, t, L, row)
    return _plates(fr, 0.17) if "smith" in eqw(row) else fr


@override("hip_thrust")
def hip_thrust(c, t, L, row, prev):
    fr = prev(c, t, L, row)
    return _plates(fr, 0.17) if "smith" in eqw(row) else fr


_wc = REG["wrist_curl"].fn


def _wrist_curl_light(c, t, L, row):
    fr = _wc(c, t, L, row)
    n = eqw(row)
    return _plates(fr, 0.13) if "barbell" in n and "cable" not in n else fr


_wrist_curl_light.prev = _wc.prev
REG["wrist_curl"].fn = _wrist_curl_light


# ================================================================== renegade row
RENEGADE_FING = (0.35, 0.0, -1.0)      # fingers down and out: the wrist sits over the handle


@override("plank")
def plank(c, t, L, row, prev):
    """Renegade row: both hands grip the dumbbell handles from above (wrist
    over the handle, knuckles out), the right one rows to the ribs; the
    support hand holds its dumbbell the whole time."""
    if "renegade" not in name_of(row):
        return prev(c, t, L, row)
    from .tpl_floor import MAT
    u = L(0.0, 1.0)
    hw = c.sw * 1.15
    g_z = 0.062

    def rt(D, Hp, c_, sd):
        base = np.array([SIDES[sd] * hw / 2, 0.0, g_z])
        if sd == "L":
            return base
        sh = fam.shoulder(D, Hp, c, "R")
        top = sh + np.array([0.06, -0.14, -0.2])
        return base * (1 - u) + top * u
    arms_over = arm_ik(rt, (0, 1, 0), (0.2, -0.6, 0.8), curl=0.92, key="grip", fing=RENEGADE_FING, sides="LR")
    eq = [MAT(-0.4), H("dumbbell", "R"), H("dumbbell", "L")]
    return fam.plank(c, down=0.0, elbows=False, hands_h=0.095, equip=eq, arms_over=arms_over,
                     feet_w=0.45 * c.S, hands_on=True)


# ================================================================== balance trainer lateral floor toe tap
@override("lateral_hop")
def lateral_hop(c, t, L, row, prev):
    """Standing on the middle of the dome, feet together; the right knee
    bends (single-leg squat) while the left foot reaches out to the side and
    taps the floor beside the trainer, then returns (sides alternate)."""
    if "toe tap" not in name_of(row):
        return prev(c, t, L, row)
    dome = 0.21
    u = L(0.0, 1.0)
    stand = c.foot(c.hw * 0.3, 0.0, 6, 0, dome)
    x0, x1 = -c.hw * 0.3, -0.5 * c.S
    tap = c.foot(x0 + (x1 - x0) * u, 0.02, 6 + 10 * u, 25 * u, (dome) * (1 - u) + 0.06 * math.sin(math.pi * u))
    tap["surf"] = dome * (1 - u)
    legs = {"R": stand, "L": tap}
    eq = [E("bosu", (0, -0.05, 0), eid="bosu", dyn=True)]
    arms = arm_fk((0.25, 0.55, -0.6), elbow=L(20, 40), thumb="up", curl=0.6)
    return c.stand(legs, hk=None, pz=c.pz * L(0.985, 0.8) + dome, px=L(0.0, 0.06), pel=(L(2, 22), 0, 0),
                   arms=arms, equip=eq, planted=["R"] if u > 1e-3 else ["L", "R"], balance="com")
