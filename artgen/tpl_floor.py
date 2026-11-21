"""Floor templates: core, bridges, planks / push-ups, quadruped, side-lying,
prone, stability-ball and foam-roller work."""
from .templates import tpl, E, H, seg, PLATE_R, X, Y, Z, np, math, SIDES
from .poses import SOLE, PAD_SINK, SKIN_FLOOR
from .rig import unit, orth, rot, body_rot
from . import fam
from .fam import arm_fk, arm_ik, legs_fk, BENCH_H
from .tpl_lower import eqw, has, trx_straps

MAT = lambda y=0.0: E("mat", (0, y, 0), eid="mat")


def palms_floor(c, py_off, w=0.3, sides="LR", fing=(0, 1, 0), y_abs=None):
    """Palms flat on the floor beside the body (supine/seated)."""
    def tgt(D, Hp, c_, sd):
        pel = c.J(D, Hp, "root")
        y = pel[1] + py_off if y_abs is None else y_abs
        return np.array([SIDES[sd] * w * c.S, y, 0.004])
    return arm_ik(tgt, (-1, 0, 0), (1, 0, 0.5), key="palm", curl=0.05, fing=fing, sides=sides)


def supine_knees(c, t, L, row, arms=None, equip=(), spine=(0, 0, 0), hold="none", pitch=-90, feet_d=0.62,
                 feet_w=0.2, neck=(0, 0, 0), legs_over=None, cons=()):
    py = 0.0
    legs = {sd: dict(ball=np.array([SIDES[sd] * feet_w / 2 * c.S, py + feet_d * c.S, SOLE]), yaw=4, heel=0,
                     pole=np.array([SIDES[sd] * 0.1, 0.2, 1.0])) for sd in "LR"}
    if legs_over:
        legs.update(legs_over)
    return fam.floor_body(c, pitch=pitch, legs=legs, arms=arms, hold=hold, spine=spine, neck=neck, py=py,
                          equip=[MAT(0.1)] + list(equip), cons=cons)


def supine_legs(c, legs, arms=None, spine=(0, 0, 0), pitch=-90, equip=(), hold="none", neck=(0, 0, 0), py=0.0):
    return fam.floor_body(c, pitch=pitch, legs=legs, arms=arms, spine=spine, hold=hold, py=py, neck=neck,
                          equip=[MAT(0.1)] + list(equip))


# ================================================================== crunches
@tpl("crunch", "side_hi")
def crunch(c, t, L, row):
    n = eqw(row)
    hold = "head"
    arms = None
    if "toss" in n or "medicine" in n or "weighted" in n or "plate" in n:
        hold = "medball"
    if "reach" in n or "toe" in n:
        hold = "none"
        arms = arm_fk((0.1, L(0.5, 0.95), L(-0.8, -0.2)), elbow=5, thumb="up")
    sp = (L(0, 38), 0, L(0, 30) if "oblique" in n or "cross" in n or "elbow to knee" in n else 0)
    nm = (row.get("name_en") or "").lower()
    if "heel touch" in nm:
        # shoulders held just off the mat, arms long by the sides; the trunk
        # side-bends so one hand slides down to touch that heel (alternating)
        sgn = 1.0 if row.get("_side", "R") == "R" else -1.0
        k = L(0.0, 1.0)
        arms = {}
        for sd in "LR":
            near = (sd == "R") == (sgn > 0)
            arms.update(arm_fk((0.12 + (0.1 * k if near else 0.0), 0.12, -1.0), elbow=4, thumb="fwd", sides=sd))
        return supine_knees(c, t, L, row, hold="none", arms=arms, spine=(24, sgn * 24 * k, 0), neck=(18, 0, 0),
                            feet_d=0.5, feet_w=0.34)
    if "balance trainer" in nm and "cable" not in nm:
        return dome_crunch(c, t, L, row)
    if "ball" in n and "medicine" not in n:
        return ball_crunch(c, t, L, row)
    if "machine" in n:
        return fam.seated(c, seat_h=0.5, pitch=L(-4, 12), spine=(L(0, 30), 0, 0), hold="cross",
                          equip=[E("seat_machine", (0, 0, 0), eid="mach", back=True)])
    if "cable" in n or "band" in n:
        return cable_crunch(c, t, L, row)
    if "decline" in n:
        return decline_situp(c, t, L, row, crunch=True)
    if "tuck" in n or "cocoon" in n or "jackknife" in n:
        return v_up(c, t, L, row)
    eq = []
    if hold == "medball":
        eq = [H("medball", "C", "ball", eid="mb")]
    return supine_knees(c, t, L, row, hold=hold, arms=arms, spine=sp, neck=(L(0, 15), 0, 0), equip=eq)


def cable_crunch(c, t, L, row):
    pul = np.array([0, 0.62, 2.1 * c.S])

    def tgt(D, Hp, c_, sd):
        return c.lmk(D, Hp, "forehead") + X * SIDES[sd] * 0.09 + Y * 0.02 - Z * 0.05
    arms = arm_ik(tgt, (0, 1, 0), (1, 0.5, -1), curl=0.9, fing=(0, 0, 1))
    eq = [E("cable_tower", pul * [1, 1, 0] + np.array([0, 0.12, 0]), R=fam.rz(180), eid="tower", pulley_h=pul[2]),
          seg("ropeL", pul, "gripL", 0.012, "rope"), seg("ropeR", pul, "gripR", 0.012, "rope")]
    return kneeling(c, t, L, row, arms=arms, equip=eq, pitch=L(15, 30), spine=(L(5, 55), 0, 0))


def kneeling(c, t, L, row, arms=None, equip=(), half=False, pitch=4.0, spine=(0, 0, 0), hold="none", hk=None,
             neck=(0, 0, 0)):
    """Tall kneeling (both knees down) or half kneeling (right foot forward)."""
    kz = 0.05
    pz = c.r.dims["R"]["T1"] + kz + 0.02 if hk is None else hk

    def kn(sd, D=None):
        return dict(thigh=np.array([SIDES[sd] * 0.08, 0.0, -1]), knee=92, kbend=np.array([0, -1, 0.0]),
                    fdir=np.array([0, -1, -0.25]), fup=np.array([0, 0.25, 1]))
    legs = {"L": kn("L"), "R": kn("R")}
    if half:
        legs["R"] = c.foot(c.hw * 0.55, 0.45 * c.S, 8)
    return c.stand(legs, pz=pz, pel=(pitch, 0, 0), spine=spine, neck=neck, arms=arms, hold=hold, balance=None,
                   reach=False, equip=[MAT(0.0)] + list(equip), settle=[("floor", SKIN_FLOOR)],
                   planted=("R",) if half else ())


@tpl("sit_up", "side_hi")
def sit_up(c, t, L, row):
    n = eqw(row)
    if "decline" in n:
        return decline_situp(c, t, L, row)
    hold = "cross"
    eq = []
    if "medicine" in n or "weighted" in n or "kettlebell" in n:
        hold = "medball"
        eq = [H("medball", "C", "ball", eid="mb")]
        if "overhead" in n or "press" in n:
            hold = "none"
    arms = None
    if "overhead" in n or "press" in n:
        arms = arm_fk((0.1, L(0.0, 0.2), 1.0), elbow=8, thumb="fwd")
    return supine_knees(c, t, L, row, hold=hold, arms=arms, equip=eq, pitch=L(-90, -28),
                        spine=(L(0, 22), 0, 0), feet_d=0.6)


def decline_situp(c, t, L, row, crunch=False):
    ang = 22
    Rb = fam.rx(ang)
    hold = "cross" if "medicine" not in eqw(row) else "medball"
    lg = {sd: dict(thigh=np.array([SIDES[sd] * 0.12, 0.75, 0.62]), knee=100, kbend=np.array([0, -0.2, -1]),
                   fdir=np.array([0, 0.4, -1])) for sd in "LR"}
    sup = [("plane", np.array([0, 0, BENCH_H]), Rb @ Z, X, 0.14, Rb @ Y, 0.6, PAD_SINK)]
    pitch = -90 - ang + (L(0, 68) if not crunch else L(0, 15))
    eq = [E("bench", (0, 0.0, 0), eid="bench", decline=ang)]
    if hold == "medball":
        eq.append(H("medball", "C", "ball", eid="mb"))
    return c.stand(lg, pz=BENCH_H + 0.3, py=0.32, pel=(pitch, 0, 0), spine=(L(0, 25), 0, L(0, 25) if "oblique" in eqw(row) or "twist" in eqw(row) else 0),
                   hold=hold, balance=None, reach=False, equip=eq, settle=sup, planted=())


@tpl("reverse_crunch", "side_hi")
def reverse_crunch(c, t, L, row):
    legs = legs_fk((0.05, L(0.35, 0.05), 1.0), knee=L(95, 105), kbend=(0, 1, -0.3), fdir=(0, 1, 0.2))
    if "decline" in eqw(row):
        return decline_situp(c, t, L, row, crunch=True)
    return supine_legs(c, legs, arms=palms_floor(c, -0.12), pitch=L(-90, -118), spine=(L(0, 15), 0, 0))


@tpl("leg_raise", "side_hi")
def leg_raise(c, t, L, row):
    n = eqw(row)
    a = math.radians(L(8, 88))
    legs = legs_fk((0.05, math.cos(a), math.sin(a)), knee=6, kbend=(0, 0, -1), fdir=(0, -math.sin(a), math.cos(a)))
    if "pull-in" in n or "pull in" in n:
        legs = legs_fk((0.05, L(0.9, 0.4), L(0.2, 0.9)), knee=L(10, 110), kbend=(0, 0, -1))
    if "alternating" in (row.get("name_en") or "").lower():
        a0 = math.radians(8)       # the left leg stays low; the right one rises (sides swap via the mirror)
        legs["L"] = legs_fk((0.05, math.cos(a0), math.sin(a0)), knee=6, kbend=(0, 0, -1),
                            fdir=(0, -math.sin(a0), math.cos(a0)), sides="L")["L"]
    eq = []
    if "hollow" in n or "hollow" in (row.get("name_en") or "").lower():
        # hollow body: low back pressed down, legs and shoulders just off the floor, arms reaching past the head
        b = L(0.0, 1.0)
        legs = legs_fk((0.05, 0.96, 0.12 + 0.06 * b), knee=4, kbend=(0, 0, -1), fdir=(0, -0.1, 1))
        arms = arm_fk((0.12, -1.0, 0.12 + 0.05 * b), elbow=6, thumb="up", world=True)
        return fam.floor_body(c, pitch=-90, legs=legs, arms=arms, spine=(22 + 4 * b, 0, 0), neck=(12, 0, 0),
                              equip=[MAT(0.1)])
    if "ball" in n and "medicine" not in n:
        eq = [E("stability_ball", (0, 0.95, 0.0), eid="sb", dyn=True)]
    if "partner" in (row.get("name_en") or "").lower():
        # hands overhead gripping (the standing partner's ankles, not drawn)
        arms = arm_fk((0.16, -1.0, 0.32), elbow=22, bend=(0, 0, 1), thumb="up", curl=0.85, world=True)
        return supine_legs(c, legs, arms=arms, equip=eq)
    return supine_legs(c, legs, arms=palms_floor(c, -0.12), equip=eq)


@tpl("flutter_kick", "side_hi")
def flutter_kick(c, t, L, row):
    scissor = "scissor" in eqw(row) or "crossover" in eqw(row)
    if scissor:
        legs = {"L": legs_fk((L(0.2, -0.12), 0.97, 0.25), knee=4, kbend=(0, 0, -1), sides="L")["L"],
                "R": legs_fk((L(-0.12, 0.2), 0.97, 0.25), knee=4, kbend=(0, 0, -1), sides="R")["R"]}
    else:
        legs = {"L": legs_fk((0.06, 0.95, L(0.12, 0.42)), knee=4, kbend=(0, 0, -1), sides="L")["L"],
                "R": legs_fk((0.06, 0.95, L(0.42, 0.12)), knee=4, kbend=(0, 0, -1), sides="R")["R"]}
    return supine_legs(c, legs, arms=palms_floor(c, -0.12), spine=(10, 0, 0), neck=(15, 0, 0))


@tpl("bicycle_crunch", "side_hi")
def bicycle_crunch(c, t, L, row):
    legs = {"L": legs_fk((0.05, L(0.35, 0.95), L(0.85, 0.3)), knee=L(105, 10), kbend=(0, 0, -1), sides="L")["L"],
            "R": legs_fk((0.05, L(0.95, 0.35), L(0.3, 0.85)), knee=L(10, 105), kbend=(0, 0, -1), sides="R")["R"]}
    return supine_legs(c, legs, hold="head", spine=(30, 0, L(-30, 30)), neck=(10, 0, 0))


@tpl("v_up", "side_hi")
def v_up(c, t, L, row):
    n = eqw(row)
    tuck = "tuck" in n or "cocoon" in n
    a = L(10, 50)
    legs = legs_fk((0.05, math.cos(math.radians(a)), math.sin(math.radians(a))), knee=L(5, 100 if tuck else 5),
                   kbend=(0, 0, -1))
    arms = arm_fk((0.1, L(-0.1, 0.9), L(1.0, 0.3)), elbow=6, thumb="up")
    eq = []
    if "medicine" in n or "pass" in n or "ball" in n:
        eq = [H("medball", "C", "ball", eid="mb")]
    return supine_legs(c, legs, arms=arms, pitch=L(-90, -45), spine=(L(0, 25), 0, 0), equip=eq)


@tpl("dead_bug", "side_hi")
def dead_bug(c, t, L, row):
    legs = {"L": legs_fk((0.05, 0.05, 1.0), knee=88, kbend=(0, -1, 0), sides="L", fdir=(0, 0.1, 1))["L"],
            "R": legs_fk((0.05, L(0.05, 0.98), L(1.0, 0.15)), knee=L(88, 5), kbend=(0, -1, 0), sides="R")["R"]}
    arms = {"R": arm_fk((0.08, 0.98, 0.1), elbow=5, thumb="in", sides="R")["R"],
            "L": arm_fk((0.08, L(0.98, 0.05), L(0.1, 1.0)), elbow=5, thumb="in", sides="L")["L"]}
    return supine_legs(c, legs, arms=arms)


def torture_twist(c, t, L, row):
    """Torture twist: supine on a flat bench, hands gripping the bench behind
    the head, legs straight up; the legs lower to one side, then the other,
    the hips turning with them while the shoulders stay down."""
    sw = L(-1.0, 1.0)
    by = -0.15
    legs = legs_fk((0.0, 0.0, 1.0), knee=6, kbend=(0, 0, -1))
    for sd in legs:
        legs[sd]["thigh"] = unit(np.array([1.45 * sw + SIDES[sd] * 0.04, 0.05, 1.0]))
    arms = arm_ik(lambda D, Hp, c_, sd: np.array([SIDES[sd] * 0.11, by - 0.6, BENCH_H - 0.01]), (0, 0, 1),
                  (1, 0.2, 0.4), curl=0.9, fing=(0, -0.3, -1))
    sup = [("plane", np.array([0, by, BENCH_H]), Z, X, 0.14, Y, 0.6, PAD_SINK)]
    return c.stand(legs, pz=BENCH_H + 0.12, py=0.0, pel=(-90, 0, 0), spine=(0, 0, -16 * sw), arms=arms, balance=None,
                   reach=False, equip=[E("bench", (0, by, 0), eid="bench")], settle=sup, planted=())


@tpl("russian_twist", "front3q")
def russian_twist(c, t, L, row):
    n = eqw(row)
    nm = (row.get("name_en") or "").lower()
    if nm == "torture twist":
        return torture_twist(c, t, L, row)
    if "standing" in n and "medicine" in n:
        # standing (back to the partner's back), ball held out at chest height on
        # long arms; a full trunk rotation carries it to one side, then the other
        tw2 = L(-1.0, 1.0)

        def tgt_s(D, Hp, c_, sd):
            Rt = D[c.r.bi("spine01")]
            return c.lmk(D, Hp, "chest") + Rt @ Y * 0.33 - Rt @ Z * 0.08 + Rt @ X * SIDES[sd] * 0.1
        arms_s = arm_ik(tgt_s, (0, 0, 1), (1, -0.4, -0.6), key="palm", curl=0.3, fing=(0, 1, 0.3))
        return c.stand(c.feet(w=c.hw * 1.5, toe=8), hk=0.97, pel=(4, 0, 30 * tw2), spine=(2, 0, 50 * tw2),
                       neck=(0, 0, 10 * tw2), arms=arms_s, balance="com",
                       equip=[H("medball", "C", "ball", eid="mb", off=(0, 0.0, 0))])
    if nm == "partner russian twist":
        tw = L(-58, 58)       # a big turn: the ball goes out wide to the partner's side
    tw = L(-38, 38)
    raised = "decline" not in n
    legs = {sd: dict(ball=np.array([SIDES[sd] * 0.1 * c.S, 0.48 * c.S, SOLE + (0.08 if raised else 0)]), yaw=0,
                     heel=-20 if raised else 0, pole=np.array([0, 0.3, 1])) for sd in "LR"}

    reach = 0.36 if nm == "partner russian twist" else 0.14       # handing it over: arms long

    def tgt(D, Hp, c_, sd):
        Rt = D[c.r.bi("spine01")]
        return c.lmk(D, Hp, "goblet") + Rt @ Y * reach - Z * 0.08 + Rt @ X * SIDES[sd] * 0.08
    arms = arm_ik(tgt, (0, 0, 1), (1, -0.4, -0.6), key="palm", curl=0.3, fing=(0, 1, 0.3))
    eq = [H("medball", "C", "ball", eid="mb", off=(0, 0.0, 0))] if "medicine" in n or "weighted" in n or "plate" in n or "dumbbell" in n else []
    if "ball" in n and "medicine" not in n and "balance" not in n:
        return ball_crunch(c, t, L, row, twist=True)
    if "cable" in n or "band" in n:
        eq = [seg("cable", np.array([1.3, 0.4, 0.4]), "gripC", 0.006, "band" if "band" in n else "darksteel")]
    if "decline bench" in n:
        # feet hooked under the pads of a decline bench, trunk held about 45 deg
        # back from upright, rotating side to side (as decline_situp's set-up)
        ang = 22
        Rb = fam.rx(ang)
        lg = {sd: dict(thigh=np.array([SIDES[sd] * 0.12, 0.75, 0.62]), knee=100, kbend=np.array([0, -0.2, -1]),
                       fdir=np.array([0, 0.4, -1])) for sd in "LR"}
        sup = [("plane", np.array([0, 0, BENCH_H]), Rb @ Z, X, 0.14, Rb @ Y, 0.6, PAD_SINK)]
        return c.stand(lg, pz=BENCH_H + 0.3, py=0.32, pel=(-90 - ang + 52, 0, tw * 0.15), spine=(10, 0, tw * 0.75),
                       arms=arms, balance=None, reach=False, equip=[E("bench", (0, 0.0, 0), eid="bench", decline=ang)] + eq,
                       settle=sup, planted=())
    if "balance" in n:
        eq.append(E("bosu", (0, -0.05, 0), eid="bosu"))
    fr = fam.floor_body(c, pitch=-48, yaw=tw * 0.25, legs=legs, arms=arms, spine=(10, 0, tw * 0.75), py=0.0,
                        equip=[MAT(0.1)] + eq,
                        settle=[("floor", SKIN_FLOOR)] if "balance" not in n else
                        [("plane", np.array([0, -0.05, 0.22]), Z, X, 0.2, Y, 0.2, PAD_SINK)])
    if raised:
        fr.planted = []     # feet hover just above the floor (heels may brush it)
    return fr


@tpl("windshield_wiper", "front3q")
def windshield_wiper(c, t, L, row):
    n = eqw(row)
    if "hanging" in n:
        from .tpl_misc import hanging_leg_raise
        return hanging_leg_raise(c, t, L, row)
    s = L(-0.55, 0.55)
    legs = legs_fk((0.05, s * 0.0, 1.0), knee=6, kbend=(0, 0, -1))
    for sd in legs:
        th = np.array([s + SIDES[sd] * 0.04, 0.0, 1.0])
        legs[sd]["thigh"] = th
    arms = arm_fk((1.0, -0.05, -0.1), elbow=5, thumb="up", world=True)
    return supine_legs(c, legs, arms=arms)


# ================================================================== bridges
def hip_band(c, y=0.0, half=0.58, z=0.27):
    """Long band across the front of the hips, its ends looped round the
    handles of two heavy kettlebells on the floor either side of the athlete
    (band-resisted bridges / thrusts)."""
    bone, p = c.lm["hip_front"]

    def side(sd):
        q = np.asarray(p, float) + np.array([SIDES[sd] * 0.15 * c.S, -0.03, 0.0])
        return lambda pts, D, Hp, ctx: c.bp(D, Hp, bone, q)
    eq = [E("kettlebell", (SIDES[sd] * half, y, z), R=fam.rz(90), eid=f"hb_kb{sd}") for sd in "LR"]
    eq += [seg("hb_bandL", np.array([-half, y, z + 0.005]), side("L"), 0.008, "band"),
           seg("hb_bandC", side("L"), side("R"), 0.008, "band"),
           seg("hb_bandR", side("R"), np.array([half, y, z + 0.005]), 0.008, "band")]
    return eq


@tpl("glute_bridge", "side")
def glute_bridge(c, t, L, row):
    n = eqw(row)
    single = "single" in (row.get("name_en") or "").lower()      # one leg (not "dumbbell single")
    feet_d = 0.55
    lift = L(0, 1)
    # keep the shoulders where they are while the hips rise
    legs_over = None
    if single:
        legs_over = {"L": legs_fk((0.05, 0.95, 0.35), knee=5, kbend=(0, 0, -1), sides="L")["L"]}
    if "march" in n:
        # from the planted bridge leg (t = 0.5) the knee lifts smoothly toward the chest
        k = max(0.0, min(1.0, (t - 0.5) / 0.5))
        k = 0.5 - 0.5 * math.cos(math.pi * k)
        th = np.array([0.05, 0.69 + (0.3 - 0.69) * k, 0.73 + (0.95 - 0.73) * k])
        legs_over = {"L": legs_fk(tuple(th), knee=134 - 44 * k, kbend=(0, 0, -1), sides="L")["L"]} if t > 0.5 else None
    eq = []
    hold = "none"
    arms = palms_floor(c, 0.02, w=0.25)
    if "barbell" in n or "smith" in n:
        arms = arm_ik(lambda D, Hp, c_, sd: c.lmk(D, Hp, "hip_front") + Z * 0.0 + X * SIDES[sd] * 0.28,
                      (-1, 0, 0), (1, 0, 0.3), curl=0.9)
        eq = [H("barbell", "C", "bar", eid="bar")]
        if "smith" in n:
            eq.append(E("smith", (0, 0.4, 0), eid="smith"))
    elif "dumbbell" in n or "medicine" in n:
        arms = arm_ik(lambda D, Hp, c_, sd: c.lmk(D, Hp, "hip_front") + X * SIDES[sd] * 0.06,
                      (0, 1, 0), (1, 0, 0.3), curl=0.9)
        eq = [H("dumbbell", "C", "db", eid="db")] if "dumbbell" in n else [H("medball", "C", "ball", eid="mb")]
    nm = (row.get("name_en") or "").lower()
    if "band" in n and "mini" not in n and "mini band" not in nm:
        eq = eq + hip_band(c)
    pitch = L(-90, -118)
    shift = None
    if "side to side" in nm:
        # bridge held at the top; the hips shift a few cm to one side, then the other
        shift = (1.0 if row.get("_side", "R") == "R" else -1.0) * L(0.0, 0.09)
        pitch = -118.0
    if "alternating leg raise" in nm:
        # bridge held at the top; one knee straightens (thighs stay level), then the other
        sd = row.get("_side", "R")
        k = L(0.0, 1.0)
        legs_over = {sd: legs_fk((0.05, 0.96, 0.22), knee=118 - 112 * k, kbend=(0, 0, -1), sides=sd,
                                 fdir=(0.0, 1.0 - 0.75 * k, 0.05 + k))[sd]}   # thighs stay level; toes turn up as the knee straightens
        pitch = -118.0
    if "ball" in n and "medicine" not in n:
        return ball_bridge(c, t, L, row)
    foam = "foam" in n or "foam" in (row.get("name_en") or "").lower()
    if "trx" in n:
        return trx_bridge(c, t, L, row)
    if "elevated" in n or "box" in n or foam:
        fz = 0.15 if foam else 0.4         # soles on a foam roller / on a bench
        legs = {sd: dict(ball=np.array([SIDES[sd] * 0.1 * c.S, 0.58 * c.S, fz + SOLE]), yaw=4, heel=0 if not foam else 10,
                         pole=np.array([0, 0.2, 1])) for sd in "LR"}
        if foam:
            eq.append(E("foam_roller", (0, 0.6 * c.S, 0), eid="fr"))
        else:
            eq.append(E("bench", (0, 0.62 * c.S, 0), eid="bench", length=0.5, height=0.4))
        if legs_over:
            legs.update(legs_over)
        return fam.floor_body(c, pitch=L(-90, -125), legs=legs, arms=arms, hold=hold, py=0.0,
                              equip=[MAT(0.1)] + eq, cons=[("joint", "upperarm01.R", 1, -0.38 * c.S)])
    frog = "frog" in n
    fw = 0.32 if frog else 0.2
    if frog:
        legs_over = {sd: dict(ball=np.array([SIDES[sd] * 0.04, feet_d * c.S * 0.75, SOLE]), yaw=60, heel=0,
                              pole=np.array([SIDES[sd] * 1.0, 0, 0.6])) for sd in "LR"}
    fr = supine_knees(c, t, L, row, arms=arms, hold=hold, equip=eq, pitch=pitch, feet_d=feet_d,
                      feet_w=fw, legs_over=legs_over, cons=[("joint", "upperarm01.R", 1, -0.36 * c.S)])
    if legs_over and "alternating leg raise" in nm:
        fr.planted = [s_ for s_ in "LR" if s_ not in legs_over]
    if shift is not None:
        b0 = fr.build

        def build():
            spec, eq_, ex = b0()
            spec["pelvis"] = np.asarray(spec["pelvis"], float) + np.array([shift, 0.0, 0.0])
            return spec, eq_, ex
        fr.build = build
    return fr


@tpl("hip_thrust", "side")
def hip_thrust(c, t, L, row):
    n = eqw(row)
    single = "single" in (row.get("name_en") or "").lower()      # one leg (not "dumbbell single")
    by = -0.1
    edge = by + 0.6
    arms = arm_fk((0.9, -0.3, -0.2), elbow=60, thumb="up", world=True)
    eq = [E("bench", (0, by, 0), R=fam.rz(0), eid="bench")]
    if "barbell" in n or "smith" in n:
        arms = arm_ik(lambda D, Hp, c_, sd: c.lmk(D, Hp, "hip_front") + X * SIDES[sd] * 0.3, (-1, 0, 0), (1, 0, 0.3),
                      curl=0.9)
        eq.append(H("barbell", "C", "bar", eid="bar"))
    elif "dumbbell" in n or "medicine" in n or "kettlebell" in n:
        arms = arm_ik(lambda D, Hp, c_, sd: c.lmk(D, Hp, "hip_front") + X * SIDES[sd] * 0.06, (0, 1, 0), (1, 0, 0.3),
                      curl=0.9)
        eq.append(H("dumbbell", "C", "db", eid="db") if "medicine" not in n else H("medball", "C", "ball", eid="mb"))
    if "ball" in n and "medicine" not in n:
        return ball_bridge(c, t, L, row, thrust=True)
    if "foam" in n:
        eq = [E("foam_roller", (0, edge, 0.3), eid="fr")] + eq[1:]
    if "band" in n and "mini" not in n:
        eq = eq + hip_band(c, y=edge + 0.38, half=0.62)      # band across the hips, posts low either side
    legs = {sd: dict(ball=np.array([SIDES[sd] * 0.13 * c.S, edge + 0.82 * c.S, SOLE]), yaw=10, heel=0,
                     pole=np.array([SIDES[sd] * 0.15, 0.3, 1])) for sd in "LR"}
    if single:
        legs["L"] = legs_fk((0.05, 0.6, 0.6), knee=90, kbend=(0, 0, -1), sides="L")["L"]
    # upper back on the bench edge: shoulders pinned at the edge
    sup = [("plane", np.array([0, by, BENCH_H]), Z, X, 0.14, Y, 0.6, PAD_SINK)]
    fr = c.stand(legs, pz=L(0.18, BENCH_H + 0.05), py=edge + 0.35, pel=(L(-60, -92), 0, 0), spine=(L(8, 0), 0, 0),
                 neck=(L(10, 30), 0, 0), arms=arms, balance=None, reach=False, equip=eq, settle=sup,
                 planted=[s for s in legs if "ball" in legs[s]])
    fr.cons.append(("joint", "upperarm01.R", 1, edge - 0.08))
    return fr


def trx_bridge(c, t, L, row):
    a = np.array([0, 1.1, 2.4])
    legs = {sd: dict(ankle=np.array([SIDES[sd] * 0.1, 0.95 * c.S, 0.5]), fdir=np.array([0, 0.3, 1]),
                     fup=np.array([0, -1, 0.3]), pole=np.array([0, 0, 1])) for sd in "LR"}
    eq = [E("trx_anchor", a * [1, 1, 0], eid="trx", h=a[2]),
          seg("strapL", a, np.array([-0.1, 0.95 * c.S, 0.5]), 0.012, "strap"),
          seg("strapR", a, np.array([0.1, 0.95 * c.S, 0.5]), 0.012, "strap")]
    return fam.floor_body(c, pitch=L(-90, -112), legs=legs, arms=palms_floor(c, -0.3), equip=[MAT(0.1)] + eq,
                          cons=[("joint", "upperarm01.R", 1, -0.36 * c.S)])


# ================================================================== planks
@tpl("push_up", (70, 10))
def push_up(c, t, L, row):
    n = eqw(row)
    hw = c.sw * 1.15
    if "wide" in n:
        hw = c.sw * 1.6
    if "diamond" in n or "tricep" in n or "narrow" in n or "close" in n:
        hw = c.sw * 0.45
    hands_h, feet_h = 0.0, 0.0
    eq = []
    if "incline" in n or "wall" in n:
        hands_h = BENCH_H
        eq.append(E("bench", (0, 0.35, 0), R=fam.rz(90), eid="bench"))
    if "decline" in n:
        feet_h = BENCH_H
        eq.append(E("bench", (0, -1.05 * c.S, 0), R=fam.rz(90), eid="bench"))
    if "ball" in n and "medicine" not in n and "balance" not in n:
        hands_h = 0.0
    if "medicine" in n:
        hands_h = 0.22
        eq.append(E("medball", (0, 0.0, 0.115), eid="mb", r=0.115))
        hw = c.sw * 0.5
    if "balance" in n:
        hands_h = 0.2
        eq.append(E("bosu", (0, -0.0, 0), R=fam.rx(180) @ fam.rx(180), eid="bosu"))
    knees = "knee" in n
    if "pike" in n or "handstand" in n:
        return pike(c, t, L, row, press=True)
    fr = fam.plank(c, down=L(0, 0.9 if knees else 1), hand_w=hw, hands_h=hands_h, feet_h=feet_h, knees=knees, equip=[MAT(-0.4)] + eq,
                   neck=(-10, 0, 0), hands_on=hands_h > 0)
    return fr


@tpl("plank", (65, 12))
def plank(c, t, L, row):
    n = eqw(row)
    elbows = "elbow" in n or ("plank" in n and "high" not in n and "extended" not in n and "jack" not in n
                              and "tap" not in n and "row" not in n and "up and down" not in n and "walk" not in n)
    if "bear" in n:      # bear plank: all fours with the knees hovering just off the floor
        return quadruped(c, t, L, row, hover=True)
    if "up and down" in n or "up-down" in n or "up down" in n:
        # forearms -> hands one arm at a time (right first), shoulders rise in two steps
        u = L(0.0, 1.0)
        kR = min(1.0, max(0.0, u / 0.5))
        kL = min(1.0, max(0.0, (u - 0.5) / 0.5))
        kR, kL = [0.5 - 0.5 * math.cos(math.pi * k) for k in (kR, kL)]
        hw = c.sw * 1.0
        def palm(sd, k):
            def f(D, Hp, c_, sd_):
                sh = fam.shoulder(D, Hp, c, sd)
                fore = np.array([SIDES[sd] * hw * 0.42, sh[1] + c.r.dims["R"]["L2"] * 0.85, 0.004])
                under = np.array([SIDES[sd] * hw / 2, sh[1] + 0.02, 0.004])
                return fore * (1 - k) + under * k
            return f
        arms_over = {}
        for sd, k in (("R", kR), ("L", kL)):
            arms_over.update(arm_ik(palm(sd, k), (-1, 0.15, 0), (0.25, -1.0 + 0.6 * (1 - k), -0.9 * (1 - k) + 0.25 * k),
                                    curl=0.05, key="palm", fing=(0, 1, 0), sides=sd))
        return fam.plank(c, down=0.62 * (1 - 0.5 * (kR + kL)), top_down=0.0, hand_w=hw, equip=[MAT(-0.4)],
                         arms_over=arms_over, hands_on=True)
    feet_h = 0.0
    eq = []
    if "elevated" in n:
        feet_h = 0.0
    arms_over = None
    legs_over = None
    if "tap" in n and "balance" not in n:
        # the right hand lifts off the floor and taps the left shoulder
        u = L(0.0, 1.0)
        hw = c.sw * 1.15

        def tap(D, Hp, c_, sd):
            base = np.array([hw / 2, 0.0, 0.004])
            top = fam.shoulder(D, Hp, c, "L") + np.array([0.03, 0.0, 0.06])
            return base * (1 - u) + top * u + Z * 0.08 * math.sin(math.pi * u)
        th = unit(np.array([-1 + u * 0.6, 0.15, u]))
        arms_over = arm_ik(tap, tuple(th), (0.6, -0.5, 0.4), curl=0.05 + 0.3 * u, key="palm", sides="R",
                           fing=(-0.8 * u, 1 - 0.6 * u, 0.4 * u))
        return fam.plank(c, down=0.0, elbows=False, equip=[MAT(-0.4)] + eq, arms_over=arms_over,
                         feet_w=0.4 * c.S, hands_on=True)
    if "pull through" in n or "pull-through" in n or "pull through" in (row.get("name_en") or "").lower():
        # high plank, feet wide: the right hand reaches under the body and drags the dumbbell
        # from the left side across to the right
        u = L(0.0, 1.0)
        hw = c.sw * 1.15

        def drag(D, Hp, c_, sd):
            if sd == "L":
                return np.array([-hw / 2, 0.0, 0.004])
            a = np.array([-0.16 * c.S, -0.16, 0.075])
            b = np.array([hw / 2 + 0.08, -0.16, 0.075])
            return a * (1 - u) + b * u + Z * 0.03 * math.sin(math.pi * u)
        arms_over = arm_ik(drag, (0, 1, 0), (0.6, -0.4, 0.6), curl=0.9, key="grip", fing=(0, 0, -1), sides="R")
        arms_over.update(arm_ik(drag, (-1, 0.15, 0), (0.25, -1.0, 0.25), curl=0.05, key="palm", fing=(0, 1, 0),
                                sides="L"))
        return fam.plank(c, down=0.0, elbows=False, equip=[MAT(-0.4), H("dumbbell", "R")], arms_over=arms_over,
                         feet_w=0.5 * c.S, hands_on=True, hand_w=hw)
    if "reach" in n or "row" in n:
        # the right hand leaves the floor: rows pull it to the ribs, reaches
        # extend it forward at shoulder height; the left hand stays planted
        u = L(0.0, 1.0)
        hw = c.sw * 1.15
        rowing = "row" in n
        reneg = "renegade" in n
        g_z = 0.06 if reneg else (0.075 if rowing and "band" not in n else (0.035 if rowing else 0.004))

        def rt(D, Hp, c_, sd):
            base = np.array([SIDES[sd] * hw / 2, 0.0, g_z])
            if sd == "L":
                return base
            sh = fam.shoulder(D, Hp, c, "R")
            top = sh + (np.array([0.06, -0.14, -0.2]) if rowing else np.array([0.04, 0.6 * c.S, 0.04]))
            return base * (1 - u) + top * u + Z * (0.06 * math.sin(math.pi * u) if not rowing else 0.0)
        key = "grip" if rowing else "palm"
        if rowing:
            arms_over = arm_ik(rt, (0, 1, 0), (0.2, -0.6, 0.8), curl=0.9, key="grip", fing=(-0.4, 0, -1),
                               sides="LR" if reneg else "R")
            if "band" not in n:
                eq.append(H("dumbbell", "R"))
            if reneg:
                eq.append(H("dumbbell", "L"))
        else:
            th = unit(np.array([-1 + u, 0.15 * (1 - u), 1.2 * u]))
            arms_over = arm_ik(rt, tuple(th), (0.25, -1.0, 0.25 + u), curl=0.05 + 0.2 * u, key="palm",
                               fing=(0, 1, -0.2 * u * 0), sides="R")
        hh = 0.095 if reneg else 0.0
        return fam.plank(c, down=0.0, elbows=False, hands_h=hh, equip=[MAT(-0.4)] + eq, arms_over=arms_over,
                         feet_w=(0.45 if reneg or rowing else 0.3) * c.S, hands_on=True)
    if "jack" in n:
        w = L(0.12, 0.95)          # feet jump from together to well outside the shoulders
        legs_over = None
        fr = fam.plank(c, down=0.0, elbows="elbows" in n, feet_w=w * c.S, equip=[MAT(-0.4)] + eq)
        fr.planted = []          # the feet jump apart and together
        return fr
    if "leg" in n and ("lift" in n or "extension" in n or "kickback" in n):
        legs_over = {"L": dict(thigh=np.array([-0.05, -1.0, L(-0.5, 0.15)]), knee=5, kbend=np.array([0, 0, -1]))}
    if "hip dip" in n:
        pass
    if "ball" in n and "medicine" not in n and "balance" not in n:
        eq.append(E("stability_ball", (0, 0.12, 0), eid="sb"))
        return fam.plank(c, down=0.0, elbows=True, hands_h=0.6, equip=eq, hands_on=True)
    if "balance" in n:
        eq.append(E("bosu", (0, -0.0, 0), eid="bosu"))
        return fam.plank(c, down=0.0, elbows=elbows, hands_h=0.21, equip=eq, hands_on=True, arms_over=arms_over)
    if "trx" in n:
        return trx_plank(c, t, L, row)
    if "saw" in n:
        fr = fam.plank(c, down=0.0, elbows=True, hand_y=L(0.0, -0.1), equip=[MAT(-0.4)])
        fr.planted = []       # the body saws back over rolling toes
        return fr
    fr = fam.plank(c, down=0.0, elbows=elbows, equip=[MAT(-0.4)] + eq, arms_over=arms_over, legs_over=legs_over,
                   hip_raise=L(0, 0.02))
    return fr


def trx_plank(c, t, L, row, pike_amt=None):
    a = np.array([0, -1.05, 2.4])
    n = eqw(row)
    pk = "pike" in n
    tuck = "tuck" in n or "climber" in n or "pull-in" in n or "runner" in n
    if pk:
        return elev_pike(c, L(0.0, 1.0), row, "straps")
    hip = 0.0
    fr = fam.plank(c, down=0.0, feet_h=0.45, equip=[MAT(-0.4)], hip_raise=hip, hands_on=True)
    return fr


SP_TILT = {"m": 5.7, "f": 3.6}   # extra tilt: the rest spine and hips are not one straight line
SP_DROP = {"m": 32.0, "f": 24.0}     # side-lying start of the side plank lift: torso tip (deg) ...
SP_LEG = {"m": 1.58, "f": 1.5}      # ... and the legs turned back up toward the floor line


@tpl("side_plank", "front3q")
def side_plank(c, t, L, row):
    """Side plank on the right forearm (left side up), facing +Y."""
    n = eqw(row)
    straight = "star" in n or "lift" in n and "clam" not in n
    knees = "knees bent" in n or "(knees" in n or "knees bent" in (row.get("name_en") or "").lower()
    elev = L(0.0, 0.08) if "dip" in n or "lift" in n else 0.06
    sh_r = c.r.joint("upperarm01.R")
    an_r = c.r.joint("foot.R")
    blen = abs(sh_r[2] - an_r[2]) - 0.0
    sz = c.r.dims["R"]["L1"] + 0.05
    az = 0.07
    ang = math.degrees(math.asin((sz - az) / blen))
    roll = 90 - ang - SP_TILT.get(c.g, 5.0)   # bottom foot on the floor, forearm down
    # side-lying to side plank: the hips start on the floor (the torso tips
    # down about the propped shoulder, the legs stay on the floor) and lift
    hip_up = "side_lying to side_plank" in n or (row.get("name_en") or "").lower() == "side plank lift"
    drop = SP_DROP[c.g] * (1 - t) if hip_up else 0.0
    if hip_up:
        elev = 0.0
    roll -= drop
    R = body_rot(0, roll, 0)
    S = np.array([0.0, 0.0, sz])
    pel = S - R @ (sh_r - c.r.pc_rest) + np.array([0, 0, elev])
    arms = {"R": arm_fk((0.0, 0.0, -1), elbow=90, bend=(0, 1, 0), thumb="up", curl=0.3, world=True, sides="R")["R"]}
    arms["R"] = lambda D, Hp, c_: dict(ua=-Z, elbow=88, bend=Y, thumb=Z, curl=0.3, fing=Y + X * 0.3)
    arms.update(arm_fk((0.05, 0.0, 1.0), elbow=5, thumb="fwd", world=False, sides="L") if straight else
                fam.arm_ik(lambda D, Hp, c_, sd: c.bp(D, Hp, "root", np.array([-0.17, 0.0, c.z_hip + 0.08])),
                           (0, -1, 0), (-1, -0.5, 0.3), key="palm", curl=0.2, sides="L"))
    lg = {}
    for sd in "LR":
        lg[sd] = dict(thigh=None)

    def lfk(sd):
        def f(D):
            R0 = D[c.r.bi("root")]
            lift = (L(0.0, 0.5) if ("leg" in n and "lift" in n) or "star" in n else 0.0) if sd == "L" else 0.0
            lift += math.tan(math.radians(drop * SP_LEG[c.g]))
            return dict(thigh=unit(R0 @ np.array([0.0 - lift, 0.0, -1])),
                        knee=90 if knees else 3, kbend=R0 @ -Y, fdir=R0 @ (Y * 0.6 - Z * 0.8))
        return f
    fr = c.stand({}, pz=pel[2], py=pel[1], px=pel[0], pel=(0, roll, 0), arms=arms, balance=None, reach=False,
                 equip=[MAT(0.0)], planted=())
    b0 = fr.build

    def build():
        spec, eq, ex = b0()
        D, Hp = c.torso(spec)
        spec["leg"] = {sd: lfk(sd)(D) for sd in "LR"}
        return spec, eq, ex
    fr.build = build
    fr.settle = [("floor", SKIN_FLOOR)]
    return fr


@tpl("mountain_climber", (70, 12))
def mountain_climber(c, t, L, row):
    n = eqw(row)
    cross = "cross" in n or "spiderman" in n
    def knee(sd, a):
        return dict(thigh=np.array([SIDES[sd] * (0.25 if cross else 0.05) * (-1 if "cross" in n else 1), a, -0.6]),
                    knee=110, kbend=np.array([0, -1, 0]), fdir=np.array([0, -0.5, -0.3]))
    legs_over = {"R": knee("R", 0.8)} if True else {}
    kk = abs(t - 0.5) * 2
    # hips rise a little while the knee passes under the body (clears the floor)
    from .tpl_v3 import _plank_supports
    hh, fh, seq = _plank_supports(row, c)
    hw = None
    if any(e["kind"] == "bosu" for e in seq):
        hw = 0.44
    fr = fam.plank(c, down=0.12, equip=[MAT(-0.4)] + seq, spine=(14 * kk, 0, 0), legs_over=None, hands_h=hh, feet_h=fh, hand_w=hw,
                   hands_on=bool(seq) or None,
                   hip_raise=(0.015 + 0.08 * kk) * (0.3 if hh or fh else 1.0))
    b0 = fr.build

    def build():
        spec, eq, ex = b0()
        D, Hp = c.torso(spec)
        R0 = D[c.r.bi("root")]
        side = "R" if t > 0.5 else "L"
        k = abs(t - 0.5) * 2
        a = math.radians(100 * k)
        # knee drives toward the chest, under the body but clear of the floor
        spec["leg"][side] = dict(thigh=unit(R0 @ np.array([SIDES[side] * (0.3 if cross else 0.06) * k,
                                                           0.3 * math.sin(a), -math.cos(a)])),
                                 knee=10 + 100 * k, kbend=R0 @ np.array([0, -1, 0]), fdir=R0 @ np.array([0, 0.3, -1]))
        return spec, eq, ex
    fr.build = build
    # the supporting foot stays planted; the driving foot may only touch the floor, never sink into it
    fr.planted = ["L" if t > 0.5 else "R"]
    if "trx" in n and not fh:
        return trx_plank(c, t, L, row)
    return fr


@tpl("pike", (75, 10))
def pike(c, t, L, row, press=False, walk=False, dist=None, hip_h=None, heel=None):
    """Inverted-V: hands and feet on the floor, hips high.  press: pike
    push-up; walk: inchworm/walkout (hands walk forward to a plank)."""
    n = eqw(row)
    if "ball" in n and "medicine" not in n:
        return ball_pike(c, t, L, row)
    if "trx" in n:
        return trx_plank(c, t, L, row)
    feet_y = 0.0
    if dist is None:
        dist = 1.3 * c.S if not walk else L(0.9, 1.5) * c.S
    hand_y = feet_y + dist
    if hip_h is None:
        hip_h = L(1.05, 1.0) * c.S if not walk else L(1.1, 0.8) * c.S
    if press and hip_h is None:
        hip_h = 1.0 * c.S
    hw = c.sw * 1.2
    sh_r = c.r.joint("upperarm01.R")
    best = None
    pel = np.array([0, feet_y + dist * 0.42, hip_h])
    # straight legs reach the floor exactly: the pelvis height follows from the
    # leg length for each torso pitch (keeps the head clear of the floor)
    hl0 = (L(15, 25) if not walk else L(0, 40)) if heel is None else heel
    hj_r = c.r.joint("upperleg01.R")
    an_r = c.r.joint("foot.R")
    leg = np.linalg.norm(hj_r - an_r) * 0.99
    a_h = math.radians(hl0)
    ank = np.array([feet_y - c.ball_y * math.cos(a_h), an_r[2] * math.cos(a_h) + c.ball_y * math.sin(a_h)])
    pz_of = {}
    for pitch in np.linspace(60, 175, 461):
        R = body_rot(pitch, 0, 0)
        off = R @ (hj_r - c.r.pc_rest)
        dy = pel[1] + off[1] - ank[0]
        if abs(dy) < leg:
            pel = np.array([0, pel[1], ank[1] + math.sqrt(leg ** 2 - dy ** 2) - off[2]])
        pz_of[pitch] = pel[2]
        S = pel + R @ (sh_r - c.r.pc_rest)
        want = c.Lpf * (0.98 if not press else L(0.98, 0.55))
        d = np.linalg.norm((S - np.array([S[0], hand_y, 0.0]))[[1, 2]])
        # small pull toward a pitch that falls as the hands walk out: picks the
        # same branch from frame to frame when two pitches reach equally well
        guess = 175 - 55 * min(1.0, dist / (1.5 * c.S))
        err = abs(d - want) + 0.3 * max(0, S[1] - hand_y - 0.05) + 0.0008 * abs(pitch - guess)
        if best is None or err < best[0]:
            best = (err, pitch)
    pitch = best[1]
    hip_h = pz_of[pitch]
    arms = arm_ik(lambda D, Hp, c_, sd: np.array([SIDES[sd] * hw / 2, hand_y, 0.004]), (-1, 0.2, 0),
                  (0.2, -0.3, 1.0), key="palm", curl=0.05, fing=(0, 1, 0))
    hl = (L(15, 25) if not walk else L(0, 40)) if heel is None else heel
    legs = {sd: c.foot(SIDES[sd] * 0.1 * c.S, feet_y - c.ball_y, 0, hl) for sd in "LR"}
    return c.stand(legs, pz=hip_h, py=pel[1], pel=(pitch, 0, 0), arms=arms, balance=None, reach=True,
                   equip=[MAT(0.4)], neck=(25, 0, 0), planted=("L", "R"))


@tpl("walkout", (75, 10))
def walkout(c, t, L, row):
    return pike(c, t, L, row, walk=True)


@tpl("downward_dog", (75, 10))
def downward_dog(c, t, L, row):
    if "push" in eqw(row):
        return pike(c, t, L, row, press=True)
    return pike(c, t, L, row)


@tpl("bear_crawl", (60, 10))
def bear_crawl(c, t, L, row):
    """Knees hovering; the right hand and the left foot step forward together
    (the loop steps them back), the other hand and foot stay planted."""
    n = eqw(row) + " " + (row.get("name_en") or "").lower()
    u = L(0.0, 1.0)
    d = 0.16 * (-1 if "reverse" in n else 1)
    lift = math.sin(math.pi * u)
    T1 = c.r.dims["R"]["T1"]
    pz = T1 + 0.06 + 0.08
    sh_r = c.r.joint("upperarm01.R")
    dd = np.linalg.norm((sh_r - c.r.pc_rest)[[1, 2]])
    pitch = 90 - math.degrees(math.asin(max(-0.9, min(0.9, (c.Lpf * 0.96 - pz) / dd))))
    hand_y = (body_rot(pitch, 0, 0) @ (sh_r - c.r.pc_rest))[1] + 0.03

    def hand_r(D, Hp, c_, sd):
        return np.array([c.sw * 0.55, hand_y + d * u, 0.004 + 0.06 * lift])
    arms_over = arm_ik(hand_r, (-1, 0.2, 0), (0.2, -1, 0.3), key="palm", curl=0.05, fing=(0, 1, 0), sides="R")
    wide = 0.3 * c.S if "spider" in n else 0.0
    legs_over = {"L": dict(ball=np.array([-0.1 * c.S - wide * lift, -0.42 * c.S + d * u, SOLE + 0.07 * lift]), yaw=0,
                           heel=75, pole=np.array([-0.3 if wide else 0, 1, -0.2]))}
    fr = quadruped(c, t, L, row, hover=True, arms_over=arms_over, legs_over=legs_over)
    fr.planted = ["R"]
    return fr


@tpl("reverse_plank", (80, 8))
def reverse_plank(c, t, L, row):
    """Supine bridge on hands and heels (reverse plank / crab)."""
    n = eqw(row)
    crab = "crab" in n or "table" in n
    elbows = "elbow" in n
    hip_up = L(0.0, 1.0)
    arms = arm_ik(lambda D, Hp, c_, sd: np.array([SIDES[sd] * 0.2 * c.S, -0.42 * c.S, 0.004]), (1, 0, 0),
                  (0, -1, 0.0), key="palm", curl=0.05, fing=(0, -1, 0))
    if elbows:
        arms = {sd: (lambda D, Hp, c_, sd=sd: dict(ua=-Z + Y * 0.0, elbow=90, bend=-Y, thumb=-X * SIDES[sd],
                                                   curl=0.3)) for sd in "LR"}
    if crab:
        legs = {sd: dict(ball=np.array([SIDES[sd] * 0.15 * c.S, 0.45 * c.S, SOLE]), yaw=8, heel=0,
                         pole=np.array([0, 0.3, 1])) for sd in "LR"}
        pitch = L(-60, -88)
        pz = L(0.2, 0.52) * c.S
    else:
        legs = {sd: dict(ankle=np.array([SIDES[sd] * 0.1, 0.8 * c.S, 0.075]), fdir=np.array([0, 0.3, 1]),
                         fup=np.array([0, -1, 0.1]), pole=np.array([0, 0, 1])) for sd in "LR"}
        pitch = L(-50, -78)
        pz = L(0.18, 0.42) * c.S
    spine = (0, 0, 0)
    if elbows and not crab:
        # forearms flat on the mat under the shoulders: the shoulder height is
        # set by the upper arm, the pelvis follows from the trunk angle
        sz = c.r.dims["R"]["L1"] + 0.07
        sh_r = c.r.joint("upperarm01.R")
        pitch = L(-71, -85)
        legs = {sd: dict(ankle=np.array([SIDES[sd] * 0.1, 0.9 * c.S, 0.075]), fdir=np.array([0, 0.3, 1]),
                         fup=np.array([0, -1, 0.1]), pole=np.array([0, 0, 1])) for sd in "LR"}
        off = body_rot(pitch, 0, 0) @ (sh_r - c.r.pc_rest)
        pz = sz - off[2]
        py0 = -0.42 * c.S - off[1]
        arms = {sd: (lambda D, Hp, c_, sd=sd: dict(ua=unit(-Z - Y * 0.08), elbow=88, bend=-Y, thumb=Z,
                                                   fing=-Y, curl=0.3)) for sd in "LR"}
        return c.stand(legs, pz=pz, py=py0, pel=(pitch, 0, 0), arms=arms, balance=None, reach=False,
                       equip=[MAT(0.2)], neck=(L(20, -10), 0, 0), planted=())
    if crab and "reach" in n:
        # hips drive up while the right arm sweeps overhead toward the left
        u = L(0.0, 1.0)
        pitch = L(-60, -78)
        pz = L(0.2, 0.47) * c.S

        def reach_t(D, Hp, c_, sd):
            sh = fam.shoulder(D, Hp, c, "R")
            base = np.array([0.2 * c.S, -0.42 * c.S, 0.004])
            if u <= 1e-6:
                return base
            # swing about the shoulder (direction and distance blended) so the
            # hand never has to reach past the arm's length on the way up
            d0, l0 = unit(base - sh), np.linalg.norm(base - sh)
            d1, l1 = unit(np.array([-0.5, -0.1, 0.85])), c.Lpf * 0.8
            dm = unit(d0 * (1 - u) + d1 * u + np.array([0.6, 0, 0]) * math.sin(math.pi * u))
            return sh + dm * min(l0 * (1 - u) + l1 * u, c.Lpf * 0.85)
        def fg(D, Hp, c_, sd):
            ad = unit(reach_t(D, Hp, c_, sd) - fam.shoulder(D, Hp, c, "R"))
            return unit(np.array([0, -1.0, 0]) * (1 - u) + ad * u)

        def tb(D, Hp, c_, sd):
            f = fg(D, Hp, c_, sd)
            v = np.array([1.0, 0, 0]) * (1 - u) + np.array([0, 1.0, 0.1]) * u
            return unit(v - f * np.dot(v, f))
        arms["R"] = arm_ik(reach_t, tb, (0, -1, 0.0), key="palm", curl=0.05 + 0.15 * u, fing=fg, sides="R")["R"]
        spine = (0, 0, -15 * u)
    return c.stand(legs, pz=pz, py=0.0, pel=(pitch, 0, 0), arms=arms, balance=None, reach=False, spine=spine,
                   equip=[MAT(0.2)], neck=(L(20, -10), 0, 0), planted=())


# ================================================================ quadruped
def quadruped(c, t, L, row, legs_over=None, arms_over=None, spine=(0, 0, 0), hover=False, sit_back=0.0,
              equip=(), neck=(-5, 0, 0), drop=0.0):
    T1 = c.r.dims["R"]["T1"]
    pz = T1 + 0.06 + (0.08 if hover else 0)
    sh_r = c.r.joint("upperarm01.R")
    d = np.linalg.norm((sh_r - c.r.pc_rest)[[1, 2]])
    sz = c.Lpf * 0.96 - drop
    pitch = 90 - math.degrees(math.asin(max(-0.9, min(0.9, (sz - pz) / d))))
    R = body_rot(pitch, 0, 0)
    S = R @ (sh_r - c.r.pc_rest)
    hand_y = S[1] + 0.03
    arms = arm_ik(lambda D, Hp, c_, sd: fam.floor_palm(c, D, Hp, sd, SIDES[sd] * c.sw * 0.55, hand_y), (-1, 0.2, 0),
                  (0.2, -1, 0.3), key="palm", curl=0.05, fing=(0, 1, 0))
    if arms_over:
        arms.update(arms_over)

    def kn(sd):
        return dict(thigh=np.array([SIDES[sd] * 0.07, 0.0, -1]), knee=92 if not hover else 95,
                    kbend=np.array([0, -1, 0.0]), fdir=np.array([0, -1, -0.2]) if not hover else np.array([0, 0.3, -1]),
                    fup=np.array([0, 0.2, 1]) if not hover else None)
    legs = {sd: kn(sd) for sd in "LR"}
    for sd in legs:
        if legs[sd]["fup"] is None:
            legs[sd].pop("fup")
    if hover:
        legs = {sd: dict(ball=np.array([SIDES[sd] * 0.1 * c.S, -0.42 * c.S, SOLE]), yaw=0, heel=75,
                         pole=np.array([0, 1, -0.2])) for sd in "LR"}
    if legs_over:
        legs.update(legs_over)
    settle = [("floor_part", c._region("noarms"), SKIN_FLOOR)] if not hover else []
    moving = [sd for sd in (legs_over or {})]
    if moving and not hover:
        # rest on the hands and the supporting knee only; a moving leg that would
        # reach the floor bends its knee instead of lifting the whole body
        r = c.r
        cols = [i for i, nm in enumerate(r.names) if any(nm.endswith("." + sd) and nm.startswith(("upperleg", "lowerleg", "foot", "toe"))
                                                         for sd in moving)]
        mask = r.W[:, cols].sum(1) < 0.5
        settle = [("floor_part", mask, SKIN_FLOOR)]
    fr = c.stand(legs, pz=pz, py=0.0, pel=(pitch - sit_back, 0, 0), spine=spine, neck=neck, arms=arms,
                 balance=None, reach=False, equip=[MAT(0.1)] + list(equip), settle=settle, planted=())
    if moving:
        fr.free_legs = moving
    return fr


@tpl("bird_dog", (70, 14))
def bird_dog(c, t, L, row):
    leg = {"L": dict(thigh=np.array([-0.06, L(0.0, -1.0), L(-1, 0.05)]), knee=L(92, 4), kbend=np.array([0, -1, 0]),
                     fdir=np.array([0, -0.2, -1]))}
    u = L(0.0, 1.0)

    def reach(D, Hp, c_):     # the hand peels off the floor and reaches forward on one smooth path
        sh = fam.shoulder(D, Hp, c, "R")
        floor = np.array([c.sw * 0.55, sh[1] + 0.03, 0.004])
        far = sh + np.array([0.08, 1.0, 0.1]) * c.Lp * 0.95 / np.linalg.norm([0.08, 1.0, 0.1])
        lift = np.array([0, 0, 0.12 * math.sin(math.pi * min(1.0, u * 1.6))])
        p = floor * (1 - u) + far * u + lift
        return dict(palm=p, thumb=np.array([-1, 0.2, 0]) * (1 - u) + Z * u + 1e-3 * Y, fing=Y,
                    pole=np.array([0.2, -1, 0.3]) * (1 - u) + np.array([0.4, 0, -1]) * u, curl=0.05 + 0.2 * u)
    return quadruped(c, t, L, row, legs_over=leg, arms_over={"R": reach})


@tpl("donkey_kick", "side")
def donkey_kick(c, t, L, row):
    straight = "straight" in eqw(row)
    leg = {"R": dict(thigh=np.array([0.06, L(0.05, -0.95), L(-1, 0.35)]), knee=L(92, 5 if straight else 90),
                     kbend=np.array([0, -1, 0.0]), fdir=np.array([0, 0.1, 1]) if not straight else np.array([0, -1, -0.2]))}
    return quadruped(c, t, L, row, legs_over=leg)


@tpl("fire_hydrant", (35, 14))
def fire_hydrant(c, t, L, row):
    circle = "circle" in eqw(row)
    if circle:
        a = math.pi * 2 * t
        th = np.array([0.06 + 0.5 * (0.5 - 0.5 * math.cos(a)), -0.35 * math.sin(a), -1 + 0.6 * (0.5 - 0.5 * math.cos(a))])
    else:
        th = np.array([L(0.07, 1.0), 0.0, L(-1, -0.15)])
    leg = {"R": dict(thigh=th, knee=92, kbend=np.array([0, -1, 0.0]), fdir=np.array([0, -1, -0.2]))}
    return quadruped(c, t, L, row, legs_over=leg)


@tpl("cat_cow", (80, 8))
def cat_cow(c, t, L, row):
    if "needle" in eqw(row) or "needle" in (row.get("name_en") or "").lower():
        return thread_needle(c, t, L, row)
    sp = L(-22, 28)
    # the pelvis tilts against the spine so the shoulders stay over the hands
    return quadruped(c, t, L, row, spine=(sp, 0, 0), neck=(L(-30, 30), 0, 0), sit_back=0.8 * sp, drop=0.05)


def thread_needle(c, t, L, row):
    """All fours: the right arm opens to the ceiling (chest turns right), then
    sweeps down and threads under the body to the left, palm up, as the
    chest turns left; the left hand stays planted."""
    u = L(0.0, 1.0)
    T1 = c.r.dims["R"]["T1"]

    def rt(D, Hp, c_, sd):
        sh = fam.shoulder(D, Hp, c, "R")
        up = sh + np.array([0.12, 0.0, c.Lpf * 0.85])
        side = np.array([sh[0] + 0.08, sh[1] + 0.02, 0.14])
        under = np.array([-0.2 * c.S, sh[1] - 0.02, 0.06])
        if u < 0.45:
            k = u / 0.45
            return up * (1 - k) + side * k + np.array([0.18, 0, 0]) * math.sin(math.pi * k)
        k = (u - 0.45) / 0.55
        return side * (1 - k) + under * k + np.array([0, 0, 0.04]) * math.sin(math.pi * k)
    a = math.radians(270 * u)
    arms_over = arm_ik(rt, (0, 1, 0), (0.3, -1, 0.0), curl=0.25, key="grip", sides="R",
                       fing=(math.sin(a), 0.0, math.cos(a)))
    k_up = max(0.0, 1 - u / 0.45)
    tw = 30 * k_up - 10 * (1 - k_up)
    k_dn = max(0.0, (u - 0.45) / 0.55)
    fr = quadruped(c, t, L, row, spine=(0, 0, tw), neck=(-5, 0, tw * 0.6), arms_over=arms_over,
                   drop=0.04 + 0.2 * (0.5 - 0.5 * math.cos(math.pi * k_dn)))
    fr.free_legs = None
    return fr


def adductor_rockback(c, t, L, row):
    """All fours with the right leg straight out to the side, foot flat; the
    hips rock back toward the left heel and return (hands stay planted)."""
    T1 = c.r.dims["R"]["T1"]
    u = L(0.0, 1.0)
    th = unit(np.array([-0.12, 0.55 * u, -1.0 + 0.35 * u]))
    legs = {"L": dict(thigh=th, knee=92 + 45 * u, kbend=np.array([0, -1, 0.0]), fdir=np.array([0, -1, -0.1]),
                      fup=np.array([0, 0.1, 1])),
            "R": dict(ball=np.array([0.72 * c.S, -0.05 * c.S, SOLE]), yaw=0, heel=0, pole=np.array([0, 0.2, 1.0]))}
    sh_r = c.r.joint("upperarm01.R")
    d = np.linalg.norm((sh_r - c.r.pc_rest)[[1, 2]])
    pz0 = T1 + 0.06
    pitch0 = 90 - math.degrees(math.asin(max(-0.9, min(0.9, (c.Lpf * 0.96 - pz0) / d))))
    S0 = body_rot(pitch0, 0, 0) @ (sh_r - c.r.pc_rest)
    hand_y = S0[1] + 0.03
    arms = arm_ik(lambda D, Hp, c_, sd: np.array([SIDES[sd] * c.sw * 0.55, hand_y, 0.004]), (-1, 0.2, 0),
                  (0.2, -1, 0.3), key="palm", curl=0.05, fing=(0, 1, 0))
    r = c.r
    cols = [i for i, nm in enumerate(r.names) if nm.endswith(".R") and nm.startswith(("upperleg", "lowerleg", "foot", "toe"))]
    mask = r.W[:, cols].sum(1) < 0.5
    fr = c.stand(legs, pz=pz0 - 0.07 * u, py=-0.24 * u * c.S, pel=(pitch0 + 6 * u, 0, 0), spine=(0, 0, 0),
                 neck=(-5, 0, 0), arms=arms, balance=None, reach=False, equip=[MAT(0.1)],
                 settle=[("floor_part", mask, SKIN_FLOOR)], planted=("R",))
    fr.free_legs = ["R"]
    return fr


@tpl("child_pose", (80, 8))
def child_pose(c, t, L, row):
    """From all fours, sit back onto the heels and fold forward."""
    T1 = c.r.dims["R"]["T1"]
    if "adductor" in (row.get("name_en") or "").lower():
        return adductor_rockback(c, t, L, row)
    th = np.array([0, L(0.0, 0.78), L(-1, -0.62)])

    def kn(sd):
        ang = math.degrees(math.acos(np.clip(np.dot(unit(th), np.array([0, -1, 0.05])), -1, 1)))
        # shins stay flat on the floor: the knee angle follows the thigh
        return dict(thigh=th + np.array([SIDES[sd] * 0.12, 0, 0]), knee=ang,
                    kbend=np.array([0, -1, 0.0]), fdir=np.array([0, -1, -0.1]), fup=np.array([0, 0.1, 1]))
    legs = {sd: kn(sd) for sd in "LR"}
    hy = 0.5 * c.S             # the hands stay where they were planted
    arms = arm_ik(lambda D, Hp, c_, sd: fam.floor_palm(c, D, Hp, sd, SIDES[sd] * c.sw * 0.5, hy),
                  (-1, 0, 0), (0.2, 0, 1), key="palm", curl=0.0, fing=(0, 1, 0))
    sh_r = c.r.joint("upperarm01.R")
    d = np.linalg.norm((sh_r - c.r.pc_rest)[[1, 2]])
    p0 = 90 - math.degrees(math.asin(max(-0.9, min(0.9, (c.Lpf * 0.93 - T1 - 0.06) / d))))   # all-fours start
    return c.stand(legs, pz=L(T1 + 0.06, 0.3), py=L(0.0, -0.32), pel=(L(p0, 80), 0, 0), spine=(L(0, 26), 0, 0),
                   neck=(L(0, 15), 0, 0), arms=arms, balance=None, reach=False, equip=[MAT(0.1)],
                   settle=[("floor_part", c._region("noarms"), SKIN_FLOOR)], planted=())


@tpl("cobra", (75, 10))
def cobra(c, t, L, row):
    """Prone, chest lifts on straight arms (cobra / up-dog)."""
    lift = L(0, 1)
    legs = {sd: dict(thigh=np.array([SIDES[sd] * 0.05, -1, L(0.0, 0.1)]), knee=3, kbend=np.array([0, 0, 1]),
                     fdir=np.array([0, -0.3, -1]) * -1 * -1, fup=np.array([0, -1, 0.3])) for sd in "LR"}
    arms = arm_ik(lambda D, Hp, c_, sd: np.array([SIDES[sd] * c.sw * 0.6, 0.42 * c.S, 0.004]), (-1, 0, 0),
                  (0.1, -1, 0.2), key="palm", curl=0.05, fing=(0, 1, 0))
    return fam.floor_body(c, pitch=L(90, 85), legs=legs, arms=arms, spine=(L(0, -58), 0, 0), neck=(L(0, -25), 0, 0),
                          equip=[MAT(0.2)])


@tpl("superman", (80, 10))
def superman(c, t, L, row):
    n = eqw(row)
    alt = "alternating" in n
    lift = L(0, 1)
    legs = {sd: dict(thigh=np.array([SIDES[sd] * 0.06, -1, 0.02 + 0.25 * lift * (1 if not alt or sd == "L" else 0)]),
                     knee=4, kbend=np.array([0, 0, 1]), fdir=np.array([0, -0.2, -1]) * -1, fup=np.array([0, -1, 0.3]))
            for sd in "LR"}
    y_t = (0.0, 0.0)
    if "y" in n.split() or "prone y" in n or "scaption" in n:
        arms = arm_fk((0.55, 0.85, 0.03 + 0.3 * lift), elbow=4, thumb="up", world=True)
    elif "prone t" in n:
        arms = arm_fk((1.0, 0.0, 0.02 + 0.35 * lift), elbow=4, thumb="up", world=True)
    elif "prone w" in n:
        arms = arm_fk((0.8, -0.2, 0.05 + 0.35 * lift), elbow=95, bend=(0, 1, 0), thumb="up", world=True)
    elif "prone i" in n:
        arms = arm_fk((0.15, -1.0, 0.03 + 0.35 * lift), elbow=4, thumb="up", world=True)
    else:
        arms = arm_fk((0.25, 1.0, 0.03 + 0.3 * lift * (1 if not alt else 1)), elbow=6, thumb="up", world=True)
    eq = [MAT(0.2)]
    if "dumbbell" in n:
        eq.append(H("dumbbell", "C", "db", eid="db"))
    if "medicine" in n:
        eq.append(H("medball", "C", "ball", eid="mb"))
    if "ball" in n and "medicine" not in n:
        return ball_back_ext(c, t, L, row)
    nm = (row.get("name_en") or "").lower()
    if "reverse leg raise" in nm and "band" in n:
        # prone, forehead on the stacked hands; one straight leg lifts a few cm
        # against a band looped round the ankle and anchored low behind the feet
        legs = {sd: dict(thigh=np.array([SIDES[sd] * 0.06, -1, -0.1 + (0.24 * lift if sd == "R" else 0.0)]),
                         knee=4, kbend=np.array([0, 0, 1]), fdir=np.array([0, -1.0, -0.3])) for sd in "LR"}
        arms = arm_ik(lambda D, Hp, c_, sd: np.array([SIDES[sd] * 0.06, 0.74 * c.S, 0.075]), (0, 1, 0),
                      (1, -0.3, 0.25), key="palm", curl=0.2, fing=(-1, 0.3, 0))
        post_y = -1.3 * c.S        # a heavy kettlebell on the floor behind the feet holds the band

        def ank(pts, D, Hp, c_):
            return Hp[c.r.bi("foot.R")] + np.array([0.0, 0.0, 0.035])
        eq = [MAT(0.2), E("kettlebell", (0.12, post_y, 0.27), eid="rl_post"),
              seg("rl_band", np.array([0.12, post_y, 0.275]), ank, 0.007, "band")]
        return c.stand(legs, pz=0.15, pel=(90, 0, 0), arms=arms, neck=(-24, 0, 0), balance=None, reach=False,
                       equip=eq, settle=[("floor_part", c._region("noarms"), -0.002)], planted=())
    if "neck" in nm:      # prone, forehead lifts off the mat; arms and legs stay down
        legs = {sd: dict(thigh=np.array([SIDES[sd] * 0.06, -1, 0.02]), knee=4, kbend=np.array([0, 0, 1]),
                         fdir=np.array([0, 0.2, 1]), fup=np.array([0, -1, 0.3])) for sd in "LR"}
        arms = arm_fk((0.15, -1.0, 0.03), elbow=6, thumb="in", world=True)
        return fam.floor_body(c, pitch=90, legs=legs, arms=arms, spine=(L(0, -6), 0, 0), neck=(L(10, -35), 0, 0),
                              equip=eq)
    swim = "swimming" in nm or "australian crawl" in nm
    if swim or alt:
        # opposite arm and leg: swimming flutters side to side with the chest held up,
        # the alternating superman lifts the right arm with the left leg
        sw = L(-1.0, 1.0) if swim else lift
        up = {"R": max(0.0, sw), "L": max(0.0, -sw) if swim else 0.0}
        legs = {sd: dict(thigh=np.array([SIDES[sd] * 0.06, -1, 0.02 + 0.28 * up["L" if sd == "R" else "R"]]),
                         knee=4, kbend=np.array([0, 0, 1]), fdir=np.array([0, 0.2, 1]), fup=np.array([0, -1, 0.3]))
                for sd in "LR"}
        arms = {}
        for sd in "LR":
            arms.update(arm_fk((0.25, 1.0, 0.03 + 0.32 * up[sd]), elbow=6, thumb="up", world=True, sides=sd))
        return fam.floor_body(c, pitch=90, legs=legs, arms=arms,
                              spine=(-16 if swim else L(0, -14), 0, 0), neck=(-12 if swim else L(0, -10), 0, 0), equip=eq)
    return fam.floor_body(c, pitch=90, legs=legs, arms=arms, spine=(L(0, -22), 0, 0), neck=(L(0, -15), 0, 0),
                          equip=eq)


# ================================================================ side lying
def side_lying(c, legs, arms=None, roll=-90, equip=(), spine=(0, 0, 0), knees=None):
    """Lying on the left side (right side up), facing +Y."""
    return fam.floor_body(c, pitch=0, roll=roll, legs=legs, arms=arms, spine=spine, equip=[MAT(0)] + list(equip))


@tpl("clam", (10, 30))
def clam(c, t, L, row):
    """Clamshell: side-lying on the left side, hips flexed ~45 deg, knees bent
    ~90 deg so the heels sit behind, in line with the trunk.  The top (right)
    knee opens by hip external rotation while the heels stay together: the
    top leg is solved to an ankle target resting on the bottom ankle, its knee
    turned up by the opening angle."""
    hf, kn = math.radians(48), 92
    th0 = np.array([0.0, math.sin(hf), -math.cos(hf)])
    sh0 = np.array([0.0, -math.cos(hf), -math.sin(hf)])        # shin back toward the heels
    open_deg = L(0.0, 40.0)
    fr = side_lying(c, {}, arms=None)
    b0 = fr.build

    def build():
        spec, eq, ex = b0()
        D, Hp = c.torso(spec)
        R0 = D[c.r.bi("root")]
        dmL = c.r.dims["L"]
        hipL = Hp[c.r.bi("upperleg01.L")]
        thL = R0 @ unit(th0 + np.array([-0.3, 0, 0]))         # the bottom knee rests on the mat
        shL = R0 @ unit(sh0 + np.array([0.02, 0, 0]))
        ankL = hipL + dmL["T1"] * thL + dmL["T2"] * shL
        up = R0 @ X                                             # pelvis right = up while lying on the left side
        toes = R0 @ unit(np.array([0.0, math.cos(hf), -math.sin(hf)]))      # foot square to the shin
        legs = {"L": dict(thigh=thL, knee=kn, kbend=shL, fdir=toes, fup=-shL)}
        tgt = ankL + up * 0.085
        hipR = Hp[c.r.bi("upperleg01.R")]
        kneeL = hipL + dmL["T1"] * thL
        ax = unit(tgt - hipR)
        p0 = orth(kneeL + up * 0.115 - hipR, ax)            # closed: top knee resting on the bottom knee
        pole = rot(ax, open_deg) @ p0
        if (rot(ax, 10.0) @ p0) @ up < p0 @ up:
            pole = rot(ax, -open_deg) @ p0
        legs["R"] = dict(ankle=tgt, fdir=toes, fup=-shL, pole=pole)
        spec["leg"] = legs
        spec["arm"] = {"L": dict(ua=unit(R0 @ np.array([-0.1, 0.1, 1.0])), elbow=110, bend=R0 @ np.array([1, 0.2, 0]),
                                 thumb=R0 @ Y, curl=0.3),
                       "R": dict(palm=c.bp(D, Hp, "root", np.array([0.0, 0.18, c.z_hip + 0.12])) + Z * 0.0,
                                 thumb=-Z, fing=R0 @ Y, pole=R0 @ np.array([1, -0.5, 0]), curl=0.1)}
        return spec, eq, ex
    fr.build = build
    return fr


@tpl("side_leg_raise", (10, 30))
def side_leg_raise(c, t, L, row):
    def leg(sd, up):
        return dict(thigh=np.array([SIDES[sd] * (0.04 + up), 0.05, -1]), knee=4, kbend=np.array([0, -1, 0]),
                    fdir=np.array([0, 1, -0.2]))
    fr = side_lying(c, {})
    b0 = fr.build
    circle = "circle" in eqw(row)

    def build():
        spec, eq, ex = b0()
        D, Hp = c.torso(spec)
        up = L(0.0, 0.85)
        lr = {"L": leg("L", 0.0), "R": leg("R", up)}
        if circle:
            a = 2 * math.pi * t
            lr["R"] = dict(thigh=np.array([0.3 + 0.2 * math.sin(a), 0.25 * math.cos(a), -1]), knee=4,
                           kbend=np.array([0, -1, 0]))
        spec["leg"] = fam.legs_rel(c, D, lr)
        R0 = D[c.r.bi("root")]
        spec["arm"] = {"L": dict(ua=unit(R0 @ np.array([-0.1, 0.1, 1.0])), elbow=110, bend=R0 @ np.array([1, 0.2, 0]),
                                 thumb=R0 @ Y, curl=0.3),
                       "R": dict(palm=c.J(D, Hp, "upperarm01.R") * np.array([1, 1, 0]) + np.array([0.15, 0.2, 0.004]), thumb=-X, fing=Y,
                                 pole=np.array([0, -0.3, 1]), curl=0.1)}
        return spec, eq, ex
    fr.build = build
    return fr


# ============================================================ back extension
@tpl("back_extension", "side")
def back_extension(c, t, L, row):
    n = eqw(row)
    if "seated" in n:
        return fam.seated(c, seat_h=0.5, pitch=L(25, -5), spine=(L(15, 0), 0, 0), hold="cross",
                          equip=[E("seat_machine", (0, 0, 0), eid="mach")])
    if "ball" in n:
        return ball_back_ext(c, t, L, row)
    if "reverse" in n:
        return reverse_hyper(c, t, L, row)
    hip = np.array([0, 0.0, 1.0])
    R45 = fam.rx(-45)
    legs = {sd: dict(ankle=hip + np.array([SIDES[sd] * 0.11, -0.55, -0.55]) * c.S + np.array([0, 0.0, 0.0]),
                     fdir=np.array([0, 0.3, -0.2]), fup=np.array([0, 0.7, 0.7]), pole=np.array([0, 1, 0.3]))
            for sd in "LR"}
    hold = "cross"
    eq = [E("roman_chair", hip, eid="rc")]
    if "dumbbell" in n or "weighted" in n or "plate" in n:
        hold = "medball" if "medicine" in n else "plate_chest"
        eq.append(H("plate_held", "C", "ball", eid="pl"))
    sup = [("plane", hip, np.array([0, -0.7, 0.7]), X, 0.2, np.array([0, 0.7, 0.7]), 0.14, PAD_SINK, "hips")]
    pc = hip + np.array([0, -0.7, 0.7]) * 0.11
    return c.stand(legs, pz=pc[2], py=pc[1], pel=(L(110, 46), 0, 0), spine=(L(15, -4), 0, 0),
                   hold=hold, balance=None, reach=False, equip=eq, settle=sup, planted=())


def reverse_hyper(c, t, L, row):
    lift = L(0, 1)
    legs = {sd: dict(thigh=np.array([SIDES[sd] * 0.06, -0.8 - 0.2 * lift, -0.5 + 0.6 * lift]), knee=4,
                     kbend=np.array([0, 0, 1])) for sd in "LR"}
    arms = arm_ik(lambda D, Hp, c_, sd: np.array([SIDES[sd] * 0.2, 0.62, BENCH_H - 0.02]), (-1, 0, 0),
                  (0.3, -1, 0.5), curl=0.9, fing=(0, 0, -1))
    sup = [("plane", np.array([0, 0.3, BENCH_H]), Z, X, 0.14, Y, 0.6, PAD_SINK)]
    return c.stand(legs, pz=BENCH_H + 0.1, py=-0.15, pel=(90, 0, 0), arms=arms, balance=None, reach=False,
                   equip=[E("bench", (0, 0.3, 0), eid="bench")], settle=sup, planted=())


@tpl("glute_ham_raise", "side")
def glute_ham_raise(c, t, L, row):
    """Kneeling (nordic) lowering from tall kneeling toward the floor."""
    arms = arm_fk((0.15, 0.6, -0.5), elbow=60, thumb="up")
    return kneeling(c, t, L, row, arms=arms, pitch=L(5, 55), spine=(0, 0, 0))


# ================================================================ ab wheel
@tpl("ab_rollout", (80, 10))
def ab_rollout(c, t, L, row):
    """Kneeling roll-out: hands on a wheel/bar that rolls forward while the
    hips extend.  The wheel is placed at straight-arm reach from the
    shoulders, so the hands never leave it."""
    n = eqw(row)
    if "trx" in n or "fallout" in n:
        eq = trx_straps(c, np.array([0, 1.2, 2.4]))
        arms = arm_fk((0.1, 0.9, L(-0.3, 0.6)), elbow=5, thumb="in", world=True)
        legs = c.feet(w=c.hw, toe=5, y=-0.2)
        for sd in legs:
            legs[sd]["heel"] = L(0, 35)
        return c.stand(legs, pz=c.pz * 0.97, pel=(L(12, 42), 0, 0), arms=arms, equip=eq, balance=None, reach=True)
    ball = "ball" in n
    wheel_z = PLATE_R if "barbell" in n else (0.33 if ball else 0.09)
    T1 = c.r.dims["R"]["T1"]

    def kn(sd):
        return dict(thigh=np.array([SIDES[sd] * 0.08, L(0.15, 0.55), L(-1, -0.7)]), knee=L(100, 140),
                    kbend=np.array([0, -1, 0.0]), fdir=np.array([0, -1, -0.15]), fup=np.array([0, 0.2, 1]))
    legs = {sd: kn(sd) for sd in "LR"}

    def grip(D, Hp, c_, sd):
        m = fam.sh_mid(D, Hp, c)
        dz = m[2] - wheel_z - (0.0 if not ball else 0.15)
        lh = c.Lh * 0.985 if not ball else c.r.dims["R"]["L1"] + 0.1
        dy = math.sqrt(max(lh ** 2 - dz ** 2, 0.0))
        return np.array([SIDES[sd] * (0.2 if "barbell" in n else 0.06), m[1] + dy, m[2] - min(dz, lh)])
    arms = arm_ik(grip, lambda D, Hp, c_, sd: -SIDES[sd] * X, (0.3, -0.4, 1), curl=0.9, fing=(0, 1, 0))
    if ball:
        eq = [H("stability_ball", "C", "ball", eid="sb", off=(0, 0.05, -0.36))]
    elif "barbell" in n:
        eq = [H("barbell", "C", "bar", eid="w")]
    else:
        eq = [H("dumbbell", "C", "bar", eid="w")]
    return c.stand(legs, pz=T1 + 0.08, py=0.0, pel=(L(58, 76), 0, 0), spine=(L(30, 2), 0, 0), neck=(-10, 0, 0),
                   arms=arms, balance=None, reach=False, equip=[MAT(0.1)] + eq,
                   settle=[("floor_part", c.r.verts[:, 2] < 0.6, SKIN_FLOOR)], planted=())


# ================================================================ stability ball
def dome_crunch(c, t, L, row):
    """Lower back over the dome of a balance trainer, feet flat on the floor."""
    top = 0.23
    legs = {sd: dict(ball=np.array([SIDES[sd] * 0.18 * c.S, 0.55 * c.S, SOLE]), yaw=10, heel=0,
                     pole=np.array([SIDES[sd] * 0.2, 0.3, 1])) for sd in "LR"}
    nm = (row.get("name_en") or "").lower()
    eq = [E("bosu", (0, 0.0, 0), eid="bosu")]
    hold, arms = "head", None
    if "overhead" in nm or "weighted" in nm:
        hold = "none"
        arms = arm_fk((0.08, -0.35 + 0.6 * L(0, 1), 1.0), elbow=8, thumb="in", world=False)
        eq.append(H("medball", "C", "ball", eid="mb"))
    sup = [("plane", np.array([0, 0.0, top]), Z, X, 0.15, Y, 0.16, -0.02)]
    return c.stand(legs, pz=top + 0.12, py=0.12, pel=(L(-82, -74), 0, 0), spine=(L(-12, 26), 0, 0), hold=hold,
                   arms=arms, balance=None, reach=False, equip=eq, settle=sup, planted=("L", "R"),
                   neck=(L(0, 12), 0, 0))


def ball_crunch(c, t, L, row, twist=False):
    bz = 0.33
    ball = np.array([0, 0.0, bz])
    legs = {sd: dict(ball=np.array([SIDES[sd] * 0.2 * c.S, 0.68 * c.S, SOLE]), yaw=10, heel=0,
                     pole=np.array([SIDES[sd] * 0.2, 0.3, 1])) for sd in "LR"}
    n = eqw(row)
    hold = "head" if not twist else "clasp"
    sup = [("plane", ball + np.array([0, 0, bz]), Z, X, 0.15, Y, 0.18, -0.03)]
    return c.stand(legs, pz=2 * bz + 0.1, py=0.15, pel=(L(-75, -70), 0, 0),
                   spine=(L(-10, 28), 0, L(-30, 30) if twist or "oblique" in n else 0), hold=hold, balance=None,
                   reach=False, equip=[E("stability_ball", (0, 0.0, 0), eid="sb")], settle=sup, planted=("L", "R"))


def ball_bridge(c, t, L, row, thrust=False):
    n = eqw(row)
    if thrust:
        bz = 0.33
        legs = {sd: dict(ball=np.array([SIDES[sd] * 0.13 * c.S, 0.95 * c.S, SOLE]), yaw=8, heel=0,
                         pole=np.array([0, 0.3, 1])) for sd in "LR"}
        if "single" in n:
            legs["L"] = legs_fk((0.05, 0.6, 0.6), knee=90, kbend=(0, 0, -1), sides="L")["L"]
        sup = [("plane", np.array([0, 0.0, 2 * bz]), Z, X, 0.15, Y, 0.12, -0.03)]
        fr = c.stand(legs, pz=L(0.3, 0.68), py=0.45, pel=(L(-60, -88), 0, 0), arms=arm_fk((0.6, 0.0, 0.3), elbow=80),
                     balance=None, reach=False, equip=[E("stability_ball", (0, -0.02, 0), eid="sb")], settle=sup,
                     planted=("R",))
        fr.cons.append(("joint", "upperarm01.R", 1, -0.02))
        return fr
    # supine, heels on the ball (ball leg curl / ball hip bridge)
    curl = "curl" in n or "pull in" in n
    roll = L(0.0, 0.32) if curl else 0.0
    ball_y = 0.98 * c.S - roll
    legs = {sd: dict(ankle=np.array([SIDES[sd] * 0.08, ball_y - 0.12, 0.62]), fdir=np.array([0, 0.3, 1]),
                     fup=np.array([0, -1, 0.1]), pole=np.array([0, 0.2, 1])) for sd in "LR"}
    return fam.floor_body(c, pitch=-90 - (28 if curl else L(0, 28)), legs=legs, arms=palms_floor(c, -0.35, w=0.3),
                          equip=[MAT(0.1), E("stability_ball", (0, ball_y, 0), eid="sb", dyn=True)],
                          cons=[("joint", "upperarm01.R", 1, -0.36 * c.S)])


def elev_pike(c, u, row, mode):
    """Hands planted under the shoulders, feet supported high (on a ball or in
    suspension straps): u 0 = straight plank, 1 = hips piked high with
    straight legs; the feet roll / swing toward the hands."""
    r = c.r
    hw = c.sw * 1.15
    sh_r = r.joint("upperarm01.R")
    hj_r = r.joint("upperleg01.R")
    an_r = r.joint("foot.R")
    pc = r.pc_rest
    tl = np.linalg.norm((sh_r - hj_r)[[1, 2]])
    leg = np.linalg.norm(hj_r - an_r) * 0.99
    S = np.array([0.0, 0.02, c.Lpf * 0.975 * math.sqrt(max(1 - ((hw - c.sw) / 2 / c.Lpf) ** 2, 0.5))])
    ank_z = 0.68 if mode == "ball" else 0.47
    # straight plank: hips on the line from the shoulders to the ankles
    dz = S[2] - ank_z
    zh0 = S[2] - dz * tl / (tl + leg)
    zh1 = S[2] + tl * 0.78
    zh = zh0 + (zh1 - zh0) * u
    Hj = np.array([0.0, S[1] - math.sqrt(max(tl ** 2 - (zh - S[2]) ** 2, 1e-4)), zh])
    v0 = (sh_r - hj_r)[[1, 2]]
    v1 = (S - Hj)[[1, 2]]
    pitch = math.degrees(math.atan2(v0[1], v0[0]) - math.atan2(v1[1], v1[0]))
    R = body_rot(pitch, 0, 0)
    pel = Hj - R @ (hj_r - pc)
    ldz = zh - ank_z
    ldy = math.sqrt(max(leg ** 2 - ldz ** 2, 1e-4))
    th = unit(np.array([0.0, -ldy, -ldz]))
    A = Hj + th * leg
    legs = legs_fk((0.04, th[1], th[2]), knee=4, kbend=(0, 0, -1),
                   fdir=tuple(unit(th + np.array([0, -0.2, 0]) * 0) * 1.0) if mode == "ball" else (0, -0.4, -1))
    arms = arm_ik(lambda D, Hp, c_, sd: np.array([SIDES[sd] * hw / 2, 0.0, 0.004]), (-1, 0.15, 0),
                  (0.25, -1.0, 0.25), curl=0.05, key="palm", fing=(0, 1, 0))
    eq = [MAT(0.0)]
    if mode == "ball":
        R_b = 0.33
        eq.append(E("stability_ball", (0, A[1] + 0.06, 0), eid="sb", dyn=True))
    fr = c.stand({}, pz=pel[2], py=pel[1], pel=(pitch, 0, 0), arms=arms, balance=None, reach=False,
                 equip=eq, planted=(), neck=(-10 + 30 * u, 0, 0))
    b0 = fr.build

    def build():
        spec, e, ex = b0()
        spec["leg"] = {sd: dict(L) for sd, L in legs.items()}
        return spec, e, ex
    fr.build = build
    return fr


def ball_pike(c, t, L, row):
    n = eqw(row)
    tuck = "tuck" in n or "pull in" in n or "pull-in" in n or "climber" in n
    if ("pull in" in n or "pull-in" in n) and "pike" not in n:
        return ball_pull_in(c, t, L, row)
    if "pike" in n and not tuck:
        return elev_pike(c, L(0.0, 1.0), row, "ball")
    by = -0.95 * c.S + (L(0, 0.35) if tuck or "pike" in n else 0)
    eq = [E("stability_ball", (0, by, 0), eid="sb", dyn=True)]
    fr = fam.plank(c, down=0.0, feet_h=0.55, equip=[MAT(0.0)] + eq, hands_on=True,
                   hip_raise=L(0, 0.35) if "pike" in n else 0.0)
    return fr


def ball_pull_in(c, t, L, row):
    """Stability-ball pull-in (knee tuck): from a straight-arm plank with the
    shins on the ball, the knees bend in under the hips, the hips rise and the
    ball rolls forward until it sits under the insteps; shoulders stay over
    the hands."""
    u = L(0.0, 1.0)
    hw = c.sw * 1.15
    sh_r = c.r.joint("upperarm01.R")
    sz = c.Lpf * 0.97
    pitch = 101.0 + 33.0 * u
    R = body_rot(pitch, 0, 0)
    S = np.array([sh_r[0], 0.0, sz])
    pel = S - R @ (sh_r - c.r.pc_rest)
    ball_y = (-0.95 + 0.2 * u) * c.S
    ank_y = (-1.31 + 0.57 * u) * c.S          # knees a touch soft at the start: no flip at the straight leg
    ank_z = 0.33 * 2 + 0.075
    legs = {sd: dict(ankle=np.array([SIDES[sd] * 0.09, ank_y, ank_z]),
                     fdir=np.array([0.0, -1.0, -0.35 * u]), fup=np.array([0.0, -0.3 * u, -1.0]),
                     pole=np.array([0.0, 0.25 + 0.6 * u, -1.0])) for sd in "LR"}
    arms = arm_ik(lambda D, Hp, c_, sd: np.array([SIDES[sd] * hw / 2, 0.0, 0.004]), (-1, 0.2, 0),
                  (0.2, -0.3, 1.0), key="palm", curl=0.05, fing=(0, 1, 0))
    eq = [MAT(-0.4), E("stability_ball", (0, ball_y, 0), eid="sb", dyn=True)]
    return c.stand(legs, pz=pel[2], py=pel[1], pel=(pitch, 0, 0), arms=arms, balance=None, reach=False,
                   equip=eq, neck=(-8, 0, 0), planted=())


def ball_back_ext(c, t, L, row):
    """Prone over a stability ball: the hips rest on top of the ball, the
    toes reach the floor behind, the trunk lowers over the ball and extends."""
    bz = 0.33
    r = c.r
    pitch = L(104, 80)
    R = body_rot(pitch, 0, 0)
    hj_r = r.joint("upperleg01.R")
    hj = np.array([0.0, -0.04, 2 * bz + 0.12])          # hip joints just behind the top of the ball
    off = R @ (hj_r - r.pc_rest)
    pel = np.array([0.0, hj[1] - off[1], hj[2] - off[2]])
    lg = np.linalg.norm(hj_r - r.joint("foot.R"))
    az = r.joint("foot.R")[2] * 0.7 + c.ball_y * math.sin(math.radians(45)) * 0.5 + 0.02
    dy = math.sqrt(max((0.97 * lg) ** 2 - (hj[2] - az) ** 2, 0.04))
    legs = {sd: c.foot(SIDES[sd] * 0.18 * c.S, hj[1] - dy, 0, 45) for sd in "LR"}
    n = eqw(row)
    hold, eq = "head", [E("stability_ball", (0, 0.0, 0), eid="sb")]
    if "plate" in n or "weighted" in n:
        hold = "plate_chest"
        eq.append(H("plate_held", "C", "ball", eid="pl"))
    return c.stand(legs, pz=pel[2], py=pel[1], pel=(pitch, 0, 0), spine=(L(22, -10), 0, 0), hold=hold,
                   balance=None, reach=False, equip=eq, planted=("L", "R"))


# ================================================================ foam roller
def foam_roll_glute(c, t, L, row, ry, roll):
    """Seated on the roller (right glute), hands on the floor behind, left
    foot flat, right ankle crossed over the left knee; the body leans onto the
    right glute and rolls a little back and forth."""
    from .tpl_misc import _knee_of
    roll = roll * 0.5            # small back-and-forth roll
    lean = L(4.0, 16.0)
    ballL = np.array([-0.13 * c.S, 0.5 * c.S, SOLE])          # the planted foot stays put while the body rolls
    poleL = np.array([-0.15, 0.4, 1.0])

    def palm_behind(D, Hp, c_, sd):
        sh = fam.shoulder(D, Hp, c, sd)
        reach = c.Lpf * 0.97
        d = math.sqrt(max(reach ** 2 - (sh[2] - 0.004) ** 2, 0.0025))
        return np.array([sh[0] * 1.15, sh[1] - d, 0.004])
    arms = arm_ik(palm_behind, (1, 0, 0), (0, -1, 0.3), key="palm", curl=0.05, fing=(0, -1, 0))
    seat = np.array([0.03, ry + roll, 0.15])
    fr = c.stand({"L": dict(ball=ballL, yaw=8, heel=0, pole=poleL)}, pz=0.3, py=ry + roll + 0.02,
                 pel=(-52, lean, 0), arms=arms, balance=None, reach=False,
                 equip=[E("foam_roller", (0, ry + roll, 0), eid="fr", dyn=True)],
                 settle=[("plane", seat, Z, X, 0.3, Y, 0.1, -0.01)], planted=("L",))
    b0 = fr.build

    def build():
        spec, eq, ex = b0()
        D, Hp = c.torso(spec)
        dm = c.r.dims["L"]
        hipL = Hp[c.r.bi("upperleg01.L")]
        # left knee from the foot (ankle above the ball) for the crossing target
        ankL = ballL + np.array([0.0, -0.12 * c.S, 0.09])
        kL = _knee_of(hipL, ankL, poleL, dm["T1"], dm["T2"])
        spec["leg"]["R"] = dict(ankle=kL + np.array([0.02, 0.0, 0.085]), fdir=np.array([-0.5, 0.6, 0.6]),
                                fup=np.array([0.3, -0.3, 1.0]), pole=np.array([1.0, 0.3, 0.5]))
        return spec, eq, ex
    fr.build = build
    return fr


@tpl("foam_roll", (80, 10))
def foam_roll(c, t, L, row):
    n = eqw(row)
    roll = L(-0.12, 0.12)
    if "quad" in n or "hip flexor" in n or "adductor" in n:
        legs = {sd: dict(thigh=np.array([SIDES[sd] * 0.08, -1, 0.0]), knee=8, kbend=np.array([0, 0, 1]),
                         fdir=np.array([0, -0.3, -1])) for sd in "LR"}
        arms = {sd: (lambda D, Hp, c_, sd=sd: dict(ua=-Z + Y * 0.1, elbow=88, bend=Y, thumb=Z, curl=0.3))
                for sd in "LR"}
        eq = [E("foam_roller", (0, -0.25 + roll, 0), eid="fr", dyn=True)]
        return c.stand(legs, pz=0.33, py=0.0 + roll, pel=(80, 0, 0), arms=arms, balance=None, reach=False,
                       equip=eq, settle=[("floor", SKIN_FLOOR)], planted=())
    if "upper back" in n or "lat" in n or "lower back" in n or "chest" in n:
        upper = "upper" in n or "lat" in n
        legs = {sd: dict(ball=np.array([SIDES[sd] * 0.15 * c.S, 0.68 * c.S, SOLE]), yaw=8, heel=0,
                         pole=np.array([0, 0.3, 1])) for sd in "LR"}
        sup = [("plane", np.array([0, -0.1 + roll, 0.15]), Z, X, 0.3, Y, 0.08, -0.01)]
        fr = c.stand(legs, pz=0.4, py=0.25 + roll, pel=(-78 if upper else -85, 0, 0), hold="cross" if upper else "head",
                     balance=None, reach=False, equip=[E("foam_roller", (0, -0.1 + roll, 0), eid="fr", dyn=True)],
                     settle=sup, planted=("L", "R"))
        return fr
    # hamstrings / calves / glutes: seated on the roller with hands behind
    part = "calf" if "calv" in n or "calf" in n else ("glute" if "glute" in n or "abductor" in n else "ham")
    ry = {"calf": 0.55, "ham": 0.32, "glute": 0.08}[part] * c.S
    legs = {sd: dict(thigh=np.array([SIDES[sd] * 0.06, 1, 0.02]), knee=4, kbend=np.array([0, 0, -1]),
                     fdir=np.array([0, 0.2, 1])) for sd in "LR"}
    if part == "glute":
        return foam_roll_glute(c, t, L, row, ry, roll)
    def palm_behind(D, Hp, c_, sd):
        # hands planted behind the shoulders where the straight arms reach the floor
        sh = fam.shoulder(D, Hp, c, sd)
        reach = c.Lpf * 0.97
        d = math.sqrt(max(reach ** 2 - (sh[2] - 0.004) ** 2, 0.0025))
        return np.array([sh[0] * 1.15, sh[1] - d, 0.004])
    arms = arm_ik(palm_behind, (1, 0, 0), (0, -1, 0.3), key="palm", curl=0.05, fing=(0, -1, 0))
    fr = c.stand(legs, pz=0.3, py=roll, pel=(-56, 0, 0), arms=arms, balance=None, reach=False,
                 equip=[E("foam_roller", (0, ry + roll, 0), eid="fr", dyn=True)],
                 settle=[("floor_part", c._region("noarms"), 0.15) if part != "glute" else ("floor", SKIN_FLOOR)],
                 planted=())
    return fr
