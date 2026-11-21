"""Upper-body templates: bench work, presses, raises, curls, triceps, rows,
pulldowns, cable work and upper-body machines."""
from .templates import tpl, E, H, seg, PLATE_R, X, Y, Z, np, math, SIDES
from .poses import SOLE, PAD_SINK
from .rig import unit, orth, rot
from . import fam
from .fam import arm_fk, arm_ik, press_bar, press_db, row_bar, row_db, supine_on_bench, BENCH_H
from .tpl_lower import eqw, has, platform, band_to_feet, trx_straps, trx_arms


def bench_kind(row, default="flat"):
    n = eqw(row)
    if "incline" in n:
        return "incline", 35.0
    if "decline" in n:
        return "decline", 18.0
    if "floor" in n:
        return "floor", 0.0
    return default, 0.0


def stand_feet(c, row, w=None, toe=8, y=0.0, split=0.0):
    legs = c.feet(w=w, toe=toe, y=y, split=split)
    return platform(c, row, legs)


# ================================================================== bench
@tpl("bench_press", (58, 18))
def bench_press(c, t, L, row):
    kind, ang = bench_kind(row)
    n = eqw(row)
    gw = c.sw * (1.05 if "close" in n else 1.75)
    grip = "sup" if "reverse grip" in n else "pro"
    arms, eq = press_bar(c, L(0, 1), "bench", gw=gw, grip=grip)
    extra = []
    if "smith" in n:
        extra.append(E("smith", (0, -0.05, 0), eid="smith"))
    return supine_on_bench(c, kind, ang, arms=arms, hold_eq=eq, extra_eq=extra,
                           legs="decline" if kind == "decline" else "floor")


@tpl("db_bench_press", "side_hi")
def db_bench_press(c, t, L, row):
    kind, ang = bench_kind(row)
    n = eqw(row)
    single = "single" in n or "alternating" in n
    squeeze = "squeeze" in n or "svend" in n
    arms, eq = press_db(c, L(0, 1), "bench", w0=c.sw * (0.6 if squeeze else 1.5), w1=c.sw * (0.55 if squeeze else 1.0),
                        thumb_mode="neutral" if squeeze else "pro")
    if single:
        other = press_db(c, 1.0, "bench")[0]
        arms["L"] = other["L"]
    if "kettlebell" in n:
        eq = [H("kettlebell", "L", "kb_up"), H("kettlebell", "R", "kb_up")]
    return supine_on_bench(c, kind, ang, arms=arms, hold_eq=eq, legs="decline" if kind == "decline" else "floor")


def hug_ball(c, t, L, row):
    """Standing tall, a big ball held against the chest with both forearms
    wrapped around it, elbows out at chest height; an isometric squeeze."""
    rb = 0.27
    sq = L(0.0, 1.0)

    def centre(D, Hp):
        Rt = D[c.r.bi("spine01")]
        return c.lmk(D, Hp, "chest") + Rt @ Y * (rb + 0.02) - Rt @ Z * 0.04

    def hand(D, Hp, c_, sd):
        Rt = D[c.r.bi("spine01")]
        return centre(D, Hp) + Rt @ X * SIDES[sd] * (0.2 - 0.015 * sq) + Rt @ Y * 0.06 + Rt @ Z * 0.02
    arms = arm_ik(hand, (0, 0, 1), (1, -0.2, 0.0), key="palm", curl=0.2, fing=(-1, 0.6, 0))
    ball = lambda D, Hp, c_, ex: E("stability_ball", centre(D, Hp) - np.array([0, 0, rb]), eid="hug_ball", r=rb)
    return c.stand(c.feet(w=c.hw * 1.1, toe=6), hk=0.99, pel=(2, 0, 0), arms=arms, balance="com", equip=[ball])


@tpl("db_fly", "side_hi")
def db_fly(c, t, L, row):
    if "hug" in (row.get("name_en") or "").lower():
        return hug_ball(c, t, L, row)
    kind, ang = bench_kind(row)
    arms = arm_fk((L(0.18, 0.96), L(0.98, 0.12), L(0.05, -0.1)), elbow=L(12, 25), thumb=(0, 0, 1),
                  bend=(-1, 0.2, 0), curl=0.85)
    eq = [H("dumbbell", "L"), H("dumbbell", "R")]
    n = eqw(row)
    extra = []
    if "cable" in n:
        eq = []
        for sd in "LR":
            p = np.array([SIDES[sd] * 0.95, 0.15, 0.12])
            extra.append(E("cable_tower", p + np.array([0, 0, -0.12]) * 0 - np.array([0, 0.12, 0]), R=fam.rz(-90 * SIDES[sd]),
                           eid=f"tower{sd}", pulley_h=0.12))
            extra.append(seg(f"cable{sd}", p, f"grip{sd}", 0.006, "darksteel"))
    if "band" in n:
        eq = []
    return supine_on_bench(c, kind, ang, arms=arms, hold_eq=eq, extra_eq=extra,
                           legs="decline" if kind == "decline" else "floor")


@tpl("pullover", "side_hi")
def pullover(c, t, L, row):
    n = eqw(row)

    def tgt(D, Hp, c_, sd):
        Rt = D[c.r.bi("spine01")]
        m = fam.sh_mid(D, Hp, c)
        a = math.radians(L(5, 100))
        d = Rt @ np.array([0, math.cos(a), math.sin(a)])
        return m + d * c.Lh * 0.9 + Rt @ X * SIDES[sd] * (0.05 if "ez" not in n and "bar" not in n else 0.2)
    arms = arm_ik(tgt, lambda D, Hp, c_, sd: -(D[c.r.bi("spine01")] @ X) * SIDES[sd],
                  lambda D, Hp, c_, sd: (D[c.r.bi("spine01")] @ X) * SIDES[sd] - (D[c.r.bi("spine01")] @ Z) * 0.3,
                  curl=0.6)
    if "ez" in n or "bar" in n:
        eq = [H("ezbar", "C", "bar", eid="bar")]
    else:
        eq = [H("dumbbell", "C", "vert", eid="db", off=(0, 0, -0.08))]
    legs = "floor"
    return supine_on_bench(c, "flat", 0, arms=arms, hold_eq=eq, legs=legs)


@tpl("skull_crusher", (60, 18))
def skull_crusher(c, t, L, row):
    kind, ang = bench_kind(row)
    n = eqw(row)
    db = "dumbbell" in n or "tate" in n
    tate = "tate" in n
    arms = arm_fk((0.12, 0.85, 0.35), elbow=L(10, 115), bend=(0, 0.2, 1) if not tate else (-1, 0, 0.3),
                  thumb=(-1, 0, 0) if not db else (0, 0, 1), curl=0.85)
    eq = [H("ezbar", "C", "bar", eid="bar")] if not db else [H("dumbbell", "L"), H("dumbbell", "R")]
    if "smith" in n:
        arms, eq = press_bar(c, L(0, 1), "bench", gw=c.sw * 0.9)
    return supine_on_bench(c, kind, ang, arms=arms, hold_eq=eq, legs="decline" if kind == "decline" else "floor")


@tpl("spider_curl", "side")
def spider_curl(c, t, L, row):
    arms = arm_fk((0.05, 0.0, -1), elbow=L(5, 125), thumb="sup", bend=(0, 1, 0), curl=0.85, world=True)
    eq = [H("dumbbell", "L"), H("dumbbell", "R")]
    lg = {sd: dict(ball=np.array([SIDES[sd] * 0.16, -0.95 * c.S, SOLE]), yaw=8, heel=50) for sd in "LR"}
    piv = np.array([0, -0.02, BENCH_H])
    Rb = fam.rx(-45)
    return c.stand(lg, pz=1.0 * c.S, py=-0.35, pel=(48, 0, 0), arms=arms, balance=None, reach=True,
                   equip=eq + [E("bench", (0, 0.0, 0), R=fam.rz(180), eid="bench", incline=45)],
                   settle=[("plane", np.array([0, 0.3, 0.95]), np.array([0, -0.7, 0.7]), X, 0.15,
                            np.array([0, 0.7, 0.7]), 0.3, PAD_SINK)])


# ================================================================== presses
def seat_bench_upright(c, arms=None, hold=None, hold2=None, mix=0.0, equip=(), angle=82):
    Rb = fam.rx(-angle)
    piv = np.array([0, -0.02, BENCH_H])
    back = (piv + Rb @ np.array([0, -0.45, 0]), Rb @ Z)
    eq = [E("bench", (0, 0, 0), eid="bench", incline=angle)] + list(equip)
    return fam.seated(c, seat_h=BENCH_H, seat_y=0.15, pitch=-4, arms=arms, hold=hold, hold2=hold2, mix=mix,
                      equip=eq, back=back, feet_y=0.62 * c.S)


@tpl("overhead_press", (55, 8))
def overhead_press(c, t, L, row):
    n = eqw(row)
    seated = "seated" in n
    push = "push press" in n or "jerk" in n
    arms, eq = press_bar(c, L(0, 1), "oh", gw=c.sw * 1.3)
    if "behind" in n:
        arms, eq = press_bar(c, L(0, 1), "oh", gw=c.sw * 1.7)
    extra = []
    if "smith" in n:
        extra.append(E("smith", (0, -0.12, 0), eid="smith"))
    if seated:
        return seat_bench_upright(c, arms=arms, equip=eq + extra)
    legs, peq = stand_feet(c, row, w=c.hw * 1.2, toe=10)
    dip = 0.0
    if push:
        dip = 0.07 * math.sin(math.pi * min(1, t * 1.6))
    return c.stand(legs, hk=0.99 - dip, pel=(-2, 0, 0), neck=(L(-8, 0), 0, 0), arms=arms, equip=eq + extra + peq,
                   load=0.3)


@tpl("db_shoulder_press", "front3q")
def db_shoulder_press(c, t, L, row):
    n = eqw(row)
    single = "single" in n or "one-arm" in n or "alternating" in n
    kb = "kettlebell" in n
    arms, eq = press_db(c, L(0, 1), "oh", w0=c.sw * 1.6, w1=c.sw * 1.0,
                        thumb_mode="neutral" if "front press" in n or "hammer" in n else "pro")
    if kb:
        eq = [H("kettlebell", "L", "kb_up"), H("kettlebell", "R", "kb_up")]
    if single:
        arms.pop("L")
        arms.update(arm_fk((0.25, 0.05, -1), elbow=12, sides="L"))
        eq = [e for e in eq if e.get("hand") != "L"]
    if "band" in n:
        eq = []
    if "seated" in n:
        return seat_bench_upright(c, arms=arms, equip=eq)
    legs, peq = stand_feet(c, row, w=c.hw * 1.15)
    extra = band_to_feet(c, legs) if "band" in n else []
    return c.stand(legs, hk=0.99, pel=(-2, 0, 0), arms=arms, equip=eq + peq + extra, load=0.2)


@tpl("arnold_press", "front3q")
def arnold_press(c, t, L, row):
    arms, eq = press_db(c, L(0, 1), "oh", w0=c.sw * 0.75, w1=c.sw * 1.05, thumb_mode="arnold")
    if "seated" in eqw(row) or "standing" not in eqw(row):
        return seat_bench_upright(c, arms=arms, equip=eq)
    legs, peq = stand_feet(c, row)
    return c.stand(legs, hk=0.99, arms=arms, equip=eq + peq)


@tpl("landmine_press", (60, 8))
def landmine_press(c, t, L, row):
    single = "single" in eqw(row) or "catch" in eqw(row) or bool(row.get("_freeze"))
    legs, peq = stand_feet(c, row, w=c.hw * 1.3, split=0.35 if single else 0.0)
    pivot = np.array([0, 1.75 * c.S, 0.06])

    def tgt(D, Hp, c_, sd):
        Rt = D[c.r.bi("spine01")]
        m = c.lmk(D, Hp, "goblet") + Rt @ Y * 0.02
        top = fam.sh_mid(D, Hp, c) + unit(np.array([0, 1.0, 0.85])) * c.Lh * 0.95
        p = m * (1 - L(0, 1)) + top * L(0, 1)
        return p + X * SIDES[sd] * 0.02
    sides = "R" if single else "LR"
    arms = arm_ik(tgt, (0, 0, 1), (1, -0.4, -0.6), curl=0.85, sides=sides)
    if single:
        arms.update(arm_fk((0.3, 0.1, -1), elbow=12, sides="L"))

    def lm(D, Hp, c_, ex):
        return None
    fr = c.stand(legs, hk=0.97, pel=(12, 0, 0), arms=arms, equip=peq, load=0.2)
    b = fr.build

    def build():
        spec, eqs, ex = b()
        return spec, eqs + [dict(kind="landmine_base", M=fam.E("landmine_base", pivot)["M"], id="base", shape={})], ex
    fr.build = build
    fr2 = fr
    # bar itself follows the hands after solving
    fr.build = _with_landmine(build, pivot, "R" if single else "C")
    return fr


def _with_landmine(build, pivot, hand):
    def b():
        spec, eqs, ex = build()
        eqs.append(dict(kind="landmine_bar", M=np.eye(4), id="lm", shape=dict(length=1.95), hand=hand,
                        hand_R=None, pivot=pivot))
        return spec, eqs, ex
    return b


# ================================================================== raises
@tpl("lateral_raise", "front3q")
def lateral_raise(c, t, L, row):
    n = eqw(row)
    single = "single" in n or "cable" in n
    seated = "seated" in n or "machine" in n
    arms = arm_fk((L(0.2, 1.0), L(0.08, 0.14), L(-1, 0.02)), elbow=L(12, 18), thumb="fwd", curl=0.85)
    eq = [H("dumbbell", "L"), H("dumbbell", "R")]
    extra = []
    if "kettlebell" in n:
        eq = [H("kettlebell", "L", "kb"), H("kettlebell", "R", "kb")]
    if "plate" in n:
        eq = []
    if "cable" in n:
        arms = arm_fk((L(-0.25, 1.0), L(0.1, 0.12), L(-1, 0.02)), elbow=L(12, 18), thumb="fwd", curl=0.85, sides="R")
        arms.update(arm_fk((0.2, 0.15, -1), elbow=60, sides="L"))
        pul = np.array([-0.45, 0.05, 0.15])
        eq = [H("dumbbell", "R", eid="h", shape_head=0.0)] if False else []
        extra = [E("cable_tower", pul + np.array([0, -0.12, -0.15]), eid="tower", pulley_h=0.15),
                 seg("cable", pul, "gripR", 0.006, "darksteel")]
    if "band" in n:
        eq = []
    if "machine" in n:
        eq = []
        extra = [E("seat_machine", (0, 0, 0), eid="mach", back=False)]
        return fam.seated(c, seat_h=0.5, arms=arms, equip=extra)
    if "to front" in n:
        a = math.pi * t
        arms = arm_fk((L(0.2, 0.6), L(0.08, 0.8), L(-1, 0.02)), elbow=14, thumb="fwd", curl=0.85)
    if seated:
        return seat_bench_upright(c, arms=arms, equip=eq)
    legs, peq = stand_feet(c, row)
    if "band" in n:
        extra += band_to_feet(c, legs)
    return c.stand(legs, pel=(4, 0, 0), arms=arms, equip=eq + extra + peq)


@tpl("front_raise", (60, 8))
def front_raise(c, t, L, row):
    n = eqw(row)
    sup = "underhand" in n
    plate = "plate" in n
    bar = "barbell" in n
    legs, peq = stand_feet(c, row)
    if plate or bar or "medicine" in n:
        arms = arm_fk((0.12, L(0.1, 1.0), L(-1, 0.05)), elbow=8, thumb=(-1, 0, 0) if bar else (0, 0, 1),
                      curl=0.85 if bar else 0.4)
        eq = [H("barbell", "C", "bar", eid="bar")] if bar else [H("plate_held", "C", "ball", eid="pl")]
        if not bar:
            arms = arm_ik(lambda D, Hp, c_, sd: fam.sh_mid(D, Hp, c) + unit(np.array([0, math.sin(math.radians(L(5, 95))),
                                                                                  -math.cos(math.radians(L(5, 95)))]))
                          * c.Lp * 0.95 + X * SIDES[sd] * 0.15, (0, math.cos(math.radians(L(5, 95))),
                                                                  math.sin(math.radians(L(5, 95)))),
                          (1, 0, -0.5), key="palm", curl=0.3,
                          fing=(0, math.sin(math.radians(L(5, 95))), -math.cos(math.radians(L(5, 95)))))
        return c.stand(legs, pel=(3, 0, 0), arms=arms, equip=eq + peq, load=0.1)
    th = "sup" if sup else ("up" if "hammer" in n else "pro")
    arms = arm_fk((0.15, L(0.1, 1.0), L(-1, 0.05)), elbow=10, thumb=th, curl=0.85)
    if "y-raise" in n or "y raise" in n:      # arms rise in a Y: up and out, thumbs up
        arms = arm_fk((L(0.15, 0.55), L(0.1, 0.45), L(-1, 0.75)), elbow=8, thumb="up", curl=0.85)
        th = "up"
    eq = [H("dumbbell", "L"), H("dumbbell", "R")]
    extra = []
    if "cable" in n or "band" in n:
        eq = []
        extra = band_to_feet(c, legs) if "band" in n else [
            E("cable_tower", np.array([0, -0.75, 0]), eid="tower", pulley_h=0.15),
            seg("cableL", np.array([0, -0.63, 0.15]), "gripL", 0.006, "darksteel"),
            seg("cableR", np.array([0, -0.63, 0.15]), "gripR", 0.006, "darksteel")]
        if "cable" in n:
            extra += [H("d_handle", sd, "db") for sd in "LR"]
    return c.stand(legs, pel=(3, 0, 0), arms=arms, equip=eq + extra + peq)


@tpl("rear_delt_raise", (70, 12))
def rear_delt_raise(c, t, L, row):
    n = eqw(row)
    if "scapular retraction" in (row.get("name_en") or "").lower():
        # standing tall, elbows bent 90 deg in front with the forearms level
        # (mini band on the wrists); the shoulder blades squeeze back and
        # down, drawing the elbows back and the hands slightly apart
        u = L(0.0, 1.0)
        arms = arm_fk((0.16 + 0.06 * u, 0.32 - 0.3 * u, -1.0), elbow=92, bend=(-0.1 + 0.12 * u, 1.0, 0.0), thumb="up",
                      curl=0.5, world=True)
        return c.stand(c.feet(w=c.hw * 1.1, toe=6), hk=0.99, pel=(1, 0, 0), spine=(-4 * u, 0, 0), neck=(-3 * u, 0, 0),
                       clav=None, arms=arms, balance="com")
    arms = arm_fk((L(0.15, 1.0), L(0.0, -0.05), L(-1, 0.0)), elbow=L(15, 20), thumb=(0, 1, 0), curl=0.85,
                  world=True)
    eq = [H("dumbbell", "L"), H("dumbbell", "R")]
    if "band" in n or "cable" in n or "bodyweight" in n or "trx" in n:
        eq = []
    if "seated" in n:
        return fam.seated(c, seat_h=BENCH_H, seat_y=0.0, pitch=58, arms=arms, equip=eq + [E("bench", (0, 0, 0), eid="bench")],
                          feet_y=0.5 * c.S, spine=(18, 0, 0), neck=(-20, 0, 0))
    legs, peq = stand_feet(c, row, w=c.hw * 1.15)
    return c.stand(legs, hk=0.9, pel=(62, 0, 0), spine=(6, 0, 0), neck=(-25, 0, 0), arms=arms, equip=eq + peq,
                   balance="com")


@tpl("reverse_fly_machine", "side")
def reverse_fly_machine(c, t, L, row):
    machine = "machine" in eqw(row)
    arms = arm_fk((L(0.1, 0.95), L(1.0, 0.0), L(0.0, 0.0)), elbow=8, thumb=(0, 0, 1), curl=0.85)
    if machine:
        eq = [E("seat_machine", (0, 0, 0), eid="mach", back=False)]
        return fam.seated(c, seat_h=0.5, arms=arms, equip=eq, pitch=4)
    legs, peq = stand_feet(c, row)
    return c.stand(legs, arms=arms, equip=peq)


@tpl("upright_row", (40, 8))
def upright_row(c, t, L, row):
    n = eqw(row)
    gw = c.sw * 0.7
    legs, peq = stand_feet(c, row)

    def tgt(D, Hp, c_, sd):
        m = fam.sh_mid(D, Hp, c)
        lo = m - Z * c.Lh * 0.97 + Y * 0.06
        hi = c.lmk(D, Hp, "front_rack") + Y * 0.04 + Z * 0.02
        return lo * (1 - L(0, 1)) + hi * L(0, 1) + X * SIDES[sd] * gw / 2
    arms = arm_ik(tgt, (-1, 0, 0), (1, -0.4, 0.6), curl=0.9, fing=(0, 0, -1))
    eq = [H("barbell", "C", "bar", eid="bar")]
    if "dumbbell" in n:
        eq = [H("dumbbell", "L"), H("dumbbell", "R")]
    elif "kettlebell" in n:
        eq = [H("kettlebell", "C", "kb", eid="kb")]
    elif "cable" in n:
        eq = [H("cable_bar", "C", "bar", eid="bar")]
        eq += [E("cable_tower", np.array([0, 0.75, 0]), R=fam.rz(180), eid="tower", pulley_h=0.15),
               seg("cable", np.array([0, 0.63, 0.15]), "gripC", 0.006, "darksteel")]
    elif "band" in n:
        eq = band_to_feet(c, legs)
    if "smith" in n:
        eq.append(E("smith", (0, 0.12, 0), eid="smith"))
    return c.stand(legs, pel=(2, 0, 0), arms=arms, equip=eq + peq, load=0.15)


@tpl("shrug", (40, 8))
def shrug(c, t, L, row):
    n = eqw(row)
    legs, peq = stand_feet(c, row)
    e = L(0, 22)
    clav = {"L": (e, -3), "R": (e, -3)}
    behind = "behind" in n
    if "dumbbell" in n or "kettlebell" in n or "cable" in n or "machine" in n or "trap" in n:
        arms = arm_fk((0.17, 0.0, -1), elbow=6, thumb="fwd", curl=0.9)
        eq = [H("kettlebell" if "kettlebell" in n else "dumbbell", sd, "kb" if "kettlebell" in n else "db")
              for sd in "LR"] if "trap" not in n else [H("trapbar", "C", "bar", eid="trap")]
    else:
        arms = arm_fk((0.12, -0.12 if behind else 0.1, -1), elbow=6, thumb="pro", curl=0.9)
        eq = [H("barbell", "C", "bar", eid="bar")]
    if "smith" in n:
        eq.append(E("smith", (0, 0.1, 0), eid="smith"))
    if "cable" in n:      # D-handles on low cables from both sides
        eq = [H("d_handle", sd, "db") for sd in "LR"]
        for sd in "LR":
            pul = np.array([SIDES[sd] * 0.75, 0.0, 0.15])
            eq.append(E("cable_tower", pul * [1, 1, 0] + np.array([SIDES[sd] * 0.12, 0, 0]), R=fam.rz(-90 * SIDES[sd]),
                        eid=f"tower{sd}", pulley_h=0.15))
            eq.append(seg(f"cable{sd}", pul, f"grip{sd}", 0.0045, "darksteel"))
    fr = c.stand(legs, pel=(2, 0, 0), arms=arms, clav=clav, equip=eq + peq, load=0.3)
    return fr


@tpl("face_pull", (60, 10))
def face_pull(c, t, L, row):
    legs, peq = stand_feet(c, row, split=0.25)
    pul = np.array([0, 1.25, 1.7 * c.S])

    def tgt(D, Hp, c_, sd):
        Rt = D[c.r.bi("spine01")]
        head = c.lmk(D, Hp, "forehead")
        a = head + Y * 0.12 + X * SIDES[sd] * 0.2 - Z * 0.03
        b = fam.sh_mid(D, Hp, c) + Y * c.Lh * 0.9 + Z * 0.12 + X * SIDES[sd] * 0.08
        return b * (1 - L(0, 1)) + a * L(0, 1)
    arms = arm_ik(tgt, (0, 0, 1), (1, -0.6, 0.4), curl=0.9)
    eq = [E("cable_tower", pul * [1, 1, 0] + np.array([0, 0.12, 0]), R=fam.rz(180), eid="tower", pulley_h=pul[2]),
          seg("ropeL", pul, "gripL", 0.012, "rope"), seg("ropeR", pul, "gripR", 0.012, "rope")]
    if "band" in eqw(row):
        eq = [seg("bandL", pul, "gripL", 0.008, "band"), seg("bandR", pul, "gripR", 0.008, "band")]
    return c.stand(legs, pel=(-4, 0, 0), arms=arms, equip=eq + peq)


@tpl("external_rotation", "front3q")
def external_rotation(c, t, L, row):
    n = eqw(row)
    at90 = "90" in n
    internal = "internal" in n
    legs, peq = stand_feet(c, row)
    if at90:
        arms = arm_fk((1.0, 0.0, 0.0), elbow=90, bend=(0, L(1, 0.0) if not internal else L(0, 1), L(0, 1) if not internal else L(1, 0)),
                      thumb=(-1, 0, 0), curl=0.85, sides="R")
    else:
        a = math.radians(L(-20, 70) if not internal else L(70, -20))
        arms = arm_fk((0.05, 0.0, -1), elbow=90, bend=(math.sin(a), math.cos(a), 0), thumb="up", curl=0.85,
                      sides="R")
    arms.update(arm_fk((0.15, 0.05, -1), elbow=12, sides="L"))
    pul = np.array([-0.7, 0.3, 1.05 * c.S])
    tw_pos, tw_rot = pul * [1, 1, 0] - np.array([0.12, 0, 0]), fam.rz(-90)
    if at90:      # the line comes from in front at shoulder height
        pul = np.array([0.42, 1.0, 1.3 * c.S])
        tw_pos, tw_rot = pul * [1, 1, 0] + np.array([0, 0.12, 0]), fam.rz(180)
        if internal:  # internal rotation: pulled from behind
            pul = np.array([0.42, -0.95, 1.3 * c.S])
            tw_pos, tw_rot = pul * [1, 1, 0] - np.array([0, 0.12, 0]), fam.rz(0)
    eq = [seg("cable", pul, "gripR", 0.006, "band" if "band" in n else "darksteel")]
    if "cable" in n:
        eq.append(E("cable_tower", tw_pos, R=tw_rot, eid="tower", pulley_h=pul[2]))
    elif "band" in n:
        eq.append(E("band_anchor", pul * [1, 1, 0], eid="post", h=pul[2]))
    if "dumbbell" in n:
        eq = [H("dumbbell", "R")]
    return c.stand(legs, arms=arms, equip=eq + peq)


# ================================================================== curls
def curl_arms(L, thumb="sup", sides="LR", elbow=(8, 135), ua=(0.06, 0.05, -1), bend=(0, 1, 0)):
    return arm_fk(ua, elbow=L(*elbow), thumb=thumb, bend=bend, curl=0.88, sides=sides)


@tpl("barbell_curl", (55, 8))
def barbell_curl(c, t, L, row):
    n = eqw(row)
    legs, peq = stand_feet(c, row)
    rev = "reverse" in n
    wide = "wide" in n
    close = "close" in n
    ua = (0.2 if wide else (0.02 if close else 0.08), 0.05, -1)
    arms = curl_arms(L, "pro" if rev else "sup", ua=ua)
    ez = "ez" in n
    eq = [H("ezbar" if ez else "barbell", "C", "bar", eid="bar")]
    if "cable" in n:
        eq = [H("cable_bar", "C", "bar", eid="bar"), E("cable_tower", np.array([0, 0.75, 0]), R=fam.rz(180), eid="tower",
                                                pulley_h=0.15),
              seg("cable", np.array([0, 0.63, 0.15]), "gripC", 0.006, "darksteel")]
    if "band" in n:
        eq = band_to_feet(c, legs)
    if "incline" in n:
        return incline_curl(c, t, L, row, arms, eq)
    if "drag" in n:
        arms = curl_arms(L, "sup", ua=(0.08, L(0.05, -0.55), -1), elbow=(8, 110))
        if "dumbbell" in n:
            eq = [H("dumbbell", sd) for sd in "LR"]
    return c.stand(legs, pel=(2, 0, 0), arms=arms, equip=eq + peq, load=0.1)


@tpl("db_curl", (55, 8))
def db_curl(c, t, L, row):
    n = eqw(row)
    th = "sup"
    if "hammer" in n or "neutral" in n:
        th = "neutral"
    if "reverse" in n:
        th = "pro"
    if "zottman" in n:
        th = "sup" if t < 0.5 else "pro"
    single = "single" in n or "alternating" in n or "concentration" in n
    wide = "wide" in n
    cross = "cross body" in n
    ua = (0.25 if wide else 0.06, 0.05, -1)
    arms = curl_arms(L, th, ua=ua, bend=(-0.6, 0.8, 0) if cross else (0, 1, 0))
    eq = [H("dumbbell", "L"), H("dumbbell", "R")]
    if "kettlebell" in n:
        eq = [H("kettlebell", "L", "kb"), H("kettlebell", "R", "kb")]
    if "cable" in n or "band" in n:
        eq = []
    if single:
        arms["L"] = arm_fk(ua, elbow=10, thumb="neutral", sides="L")["L"]
    if "isometric" in n:     # hold half way up: the curl's own arm path between 45 and 55 %
        def lerp(a, b, u):
            if isinstance(a, (tuple, list)):
                return tuple(np.asarray(a, float) * (1 - u) + np.asarray(b, float) * u)
            return a * (1 - u) + b * u
        arms = curl_arms(lambda a, b: lerp(a, b, L(0.45, 0.55)), th, ua=ua)
    if "incline" in n:
        return incline_curl(c, t, L, row, arm_fk((0.08, -0.25, -1), elbow=L(8, 130), thumb=th, curl=0.88,
                                                 world=True), eq)
    if "seated" in n:
        return seat_bench_upright(c, arms=arms, equip=eq, angle=85)
    if "press" in n:  # curl to press
        return curl_press(c, t, L, row)
    legs, peq = stand_feet(c, row)
    extra = band_to_feet(c, legs) if "band" in n else []
    return c.stand(legs, pel=(2, 0, 0), arms=arms, equip=eq + extra + peq, load=0.1)


def curl_press(c, t, L, row):
    legs, peq = stand_feet(c, row)
    if t < 0.5:
        arms = curl_arms(lambda a, b: a + (b - a) * min(1, t * 2), "neutral")
    else:
        arms, _ = press_db(c, (t - 0.5) * 2, "oh", w0=c.sw * 1.0, w1=c.sw * 1.0, thumb_mode="neutral")
    return c.stand(legs, arms=arms, equip=[H("dumbbell", "L"), H("dumbbell", "R")] + peq)


def incline_curl(c, t, L, row, arms, eq):
    Rb = fam.rx(-55)
    piv = np.array([0, -0.02, BENCH_H])
    back = (piv + Rb @ np.array([0, -0.45, 0]), Rb @ Z)
    return fam.seated(c, seat_h=BENCH_H, seat_y=0.17, pitch=-35, arms=arms, back=back,
                      equip=list(eq) + [E("bench", (0, 0, 0), eid="bench", incline=55)], feet_y=0.72 * c.S)


@tpl("preacher_curl", "side")
def preacher_curl(c, t, L, row):
    n = eqw(row)
    single = "single" in n
    arms = arm_fk((0.06, 0.62, -0.78), elbow=L(15, 128), thumb="sup", bend=(0, 0.6, 0.8), curl=0.88, world=True)
    eq = [H("ezbar", "C", "bar", eid="bar")]
    if "dumbbell" in n or single:
        eq = [H("dumbbell", "L"), H("dumbbell", "R")]
    if "cable" in n:
        eq = [H("cable_bar", "C", "bar", eid="bar"),
              E("cable_tower", np.array([0, 1.0, 0]), R=fam.rz(180), eid="tower", pulley_h=0.3),
              seg("cable", np.array([0, 0.88, 0.3]), "gripC", 0.006, "darksteel")]
    if "machine" in n:
        eq = []
    if single:
        arms["L"] = arm_fk((0.1, 0.4, -0.9), elbow=30, sides="L", world=True)["L"]
        eq = [H("dumbbell", "R")]
    return fam.seated(c, seat_h=0.585, seat_y=0.0, pitch=18, arms=arms,
                      equip=eq + [E("preacher", (0, 0, 0), eid="pb", height=0.55)], feet_y=0.32 * c.S, spine=(10, 0, 0),
                      neck=(-10, 0, 0))


@tpl("concentration_curl", (45, 10))
def concentration_curl(c, t, L, row):
    arms = arm_fk((0.18, 0.25, -1), elbow=L(10, 130), thumb="sup", bend=(-0.6, 0.7, 0), curl=0.88, sides="R",
                  world=True)
    arms.update(arm_ik(lambda D, Hp, c_, sd: c.J(D, Hp, "lowerleg01.L") + Z * 0.08 + Y * 0.05, (0, 1, 0),
                       (-1, -0.3, 0.3), key="palm", curl=0.3, sides="L", fing=(0.6, 0.6, 0)))
    return fam.seated(c, seat_h=BENCH_H, seat_y=0.0, pitch=38, arms=arms, feet_w=0.6 * c.S, spine=(18, 0, 0),
                      neck=(-15, 0, 0), equip=[H("dumbbell", "R"), E("bench", (0, -0.1, 0), eid="bench", length=0.9)])


@tpl("overhead_cable_curl", "front")
def overhead_cable_curl(c, t, L, row):
    legs, peq = stand_feet(c, row)
    arms = arm_fk((1.0, 0.0, 0.12), elbow=L(10, 120), thumb="up", bend=(0, 0, 1), curl=0.88)
    eq = []
    for sd in "LR":
        p = np.array([SIDES[sd] * 1.25, 0.0, 1.75 * c.S])
        eq.append(E("cable_tower", p * [1, 1, 0] + np.array([SIDES[sd] * 0.12, 0, 0]), R=fam.rz(90 * SIDES[sd]),
                    eid=f"tower{sd}", pulley_h=p[2]))
        eq.append(seg(f"cable{sd}", p, f"grip{sd}", 0.006, "darksteel"))
    return c.stand(legs, arms=arms, equip=eq + peq)


# ================================================================== triceps
@tpl("triceps_pushdown", (55, 8))
def triceps_pushdown(c, t, L, row):
    n = eqw(row)
    rope = "rope" in n
    under = "underhand" in n
    single = "one arm" in n or "single" in n
    legs, peq = stand_feet(c, row, w=c.hw * 1.15)
    arms = arm_fk((0.12 if not rope else 0.1, 0.12, -1), elbow=L(100, 8), thumb="neutral" if rope else (
        "sup" if under else "pro"), bend=(0, 1, 0.1), curl=0.9)
    pul = np.array([0, 0.55, 2.05 * c.S])
    eq = [E("cable_tower", pul * [1, 1, 0] + np.array([0, 0.12, 0]), R=fam.rz(180), eid="tower", pulley_h=pul[2])]
    if rope:
        eq += [seg("ropeL", pul, "gripL", 0.012, "rope"), seg("ropeR", pul, "gripR", 0.012, "rope")]
    elif single:
        arms["L"] = arm_fk((0.15, 0.05, -1), elbow=12, sides="L")["L"]
        eq += [seg("cable", pul, "gripR", 0.006, "darksteel")]
    else:
        eq += [H("ezbar" if under else "barbell", "C", "bar", eid="bar", plates=0) if False else
               H("pvc", "C", "bar", eid="bar", length=0.5), seg("cable", pul, "gripC", 0.006, "darksteel")]
    if "band" in n:
        eq = [seg("bandL", pul, "gripL", 0.008, "band"), seg("bandR", pul, "gripR", 0.008, "band")]
    if "machine" in n:
        return fam.seated(c, seat_h=0.5, arms=arm_fk((0.15, 0.1, -0.8), elbow=L(100, 10), thumb="neutral", curl=0.9),
                          equip=[E("seat_machine", (0, 0, 0), eid="mach", back=False)])
    return c.stand(legs, hk=0.97, pel=(14, 0, 0), arms=arms, equip=eq + peq)


@tpl("overhead_triceps_extension", (60, 8))
def overhead_triceps_extension(c, t, L, row):
    n = eqw(row)
    single = "single" in n
    arms = arm_fk((0.12, 0.12, 1.0), elbow=L(140, 10), thumb="neutral", bend=(0, -1, 0), curl=0.85)
    eq = [H("dumbbell", "C", "vert", eid="db", off=(0, 0, -0.08))]
    if "ez" in n:
        eq = [H("ezbar", "C", "bar", eid="bar")]
        arms = arm_fk((0.18, 0.12, 1.0), elbow=L(140, 10), thumb="pro", bend=(0, -1, 0), curl=0.85)
    if "rope" in n or "cable" in n:
        pul = np.array([0, -0.65, 0.4])
        eq = [E("cable_tower", pul * [1, 1, 0] - np.array([0, 0.12, 0]), eid="tower", pulley_h=pul[2]),
              seg("ropeL", pul, "gripL", 0.012, "rope"), seg("ropeR", pul, "gripR", 0.012, "rope")]
    if "band" in n:
        eq = []
    if single:
        arms = arm_fk((0.1, 0.1, 1.0), elbow=L(140, 10), thumb="neutral", bend=(0, -1, 0), curl=0.85, sides="R")
        arms.update(arm_fk((0.2, 0.05, -1), elbow=12, sides="L"))
        eq = [H("dumbbell", "R")]
    if "seated" in n:
        return seat_bench_upright(c, arms=arms, equip=eq, angle=85)
    legs, peq = stand_feet(c, row)
    return c.stand(legs, pel=(0, 0, 0), arms=arms, equip=eq + peq)


@tpl("triceps_kickback", "side")
def triceps_kickback(c, t, L, row):
    arms = arm_fk((0.08, -0.85, 0.15), elbow=L(95, 4), thumb="neutral", bend=(0, 0, -1), curl=0.88, world=True)
    legs, peq = stand_feet(c, row, w=c.hw * 1.1, split=0.3)
    eq = [H("dumbbell", "L"), H("dumbbell", "R")]
    if "cable" in eqw(row):
        eq = []
    return c.stand(legs, hk=0.9, pel=(60, 0, 0), spine=(8, 0, 0), neck=(-25, 0, 0), arms=arms, equip=eq + peq)


@tpl("wrist_curl", "side")
def wrist_curl(c, t, L, row):
    n = eqw(row)
    down = "down" in n or "extension" in n
    arms = {}
    for sd in "LR":
        s = SIDES[sd]

        def f(D, Hp, c_, sd=sd, s=s):
            k = c.J(D, Hp, f"lowerleg01.{sd}")
            el = k + np.array([-s * 0.02, -0.33, 0.1])
            wr = k + np.array([-s * 0.02, 0.06, 0.07])
            ua = unit(el - fam.shoulder(D, Hp, c, sd))
            ang = math.degrees(math.acos(np.clip(np.dot(ua, unit(wr - el)), -1, 1)))
            th = -s * X if not down else s * X
            wf = L(-40, 45) if not down else L(40, -45)
            fing = rot(np.cross(Y, Z if not down else -Z) * 0 + X * s * (1 if not down else -1), 0) @ Y
            fing = unit(Y * math.cos(math.radians(wf)) + Z * math.sin(math.radians(wf)))
            return dict(ua=ua, elbow=ang, bend=Y + Z * 0.3, thumb=-s * X if not down else s * X, curl=0.88, fing=fing)
        arms[sd] = f
    eq = [H("barbell", "C", "bar", eid="bar")] if "barbell" in n else [H("dumbbell", "L"), H("dumbbell", "R")]
    return fam.seated(c, seat_h=BENCH_H, seat_y=0.0, pitch=30, arms=arms, equip=eq + [E("bench", (0, -0.1, 0),
                                                                                     eid="bench", length=0.9)],
                      spine=(20, 0, 0), neck=(-10, 0, 0))


# ================================================================== rows
@tpl("barbell_row", (60, 9))
def barbell_row(c, t, L, row):
    n = eqw(row)
    legs, peq = stand_feet(c, row, w=c.hw * 1.15, toe=10)
    grip = "sup" if "reverse" in n or "underhand" in n else "pro"
    pendlay = "pendlay" in n
    arms, eq = row_bar(c, L(0, 1), grip=grip)
    if "smith" in n:
        eq.append(E("smith", (0, 0.1, 0), eid="smith"))
    if "trap" in n:
        arms, eq = row_db(c, L(0, 1), spread=0.06, thumb="neutral")
        eq = [H("trapbar", "C", "bar", eid="trap")]
    if "band" in n:
        eq = band_to_feet(c, legs)
    return c.stand(legs, hk=0.84 if not pendlay else 0.86, pel=(68 if not pendlay else 82, 0, 0), spine=(4, 0, 0),
                   neck=(-28, 0, 0), arms=arms, equip=eq + peq, balance="com", load=0.25)


@tpl("db_row", (75, 10))
def db_row(c, t, L, row):
    """One-arm dumbbell row with the left hand and knee on a bench."""
    n = eqw(row)
    if "bent over" in n or "elbows out" in n or "kettlebell alternating" in n:
        legs, peq = stand_feet(c, row, w=c.hw * 1.15)
        arms, eq = row_db(c, L(0, 1), elbow_out=0.7 if "elbows" in n else 0.15,
                          thumb="pro" if "elbows" in n else "neutral")
        if "kettlebell" in n:
            eq = [H("kettlebell", "L", "kb"), H("kettlebell", "R", "kb")]
        return c.stand(legs, hk=0.86, pel=(66, 0, 0), spine=(4, 0, 0), neck=(-28, 0, 0), arms=arms, equip=eq + peq,
                       balance="com")
    bench_y = 0.15
    arms, eq = row_db(c, L(0, 1), sides="R")
    if "kettlebell" in n:
        eq = [H("kettlebell", "R", "kb")]
    if ("cable" in n or "band" in n) and "dumbbell" not in n:
        eq = [H("d_handle", "R", "db")] if "cable" in n else []     # the overlay draws the cable / band
    arms.update(arm_ik(lambda D, Hp, c_, sd: fam.shoulder(D, Hp, c, "L") * np.array([1, 1, 0]) +
                       np.array([0.08, 0.06, BENCH_H + 0.005]), (1, 0.1, 0),
                       (-0.3, -1, 0.2), key="palm", curl=0.1, fing=(0, 1, 0), sides="L"))
    legs = {"R": c.foot(0.3 * c.S, -0.3 * c.S, 10),
            "L": dict(thigh=np.array([0.05, -0.1, -1]), knee=95, kbend=np.array([0, -1, 0]),
                      fdir=np.array([0, -1, -0.1]), fup=np.array([0, 0, 1]))}
    fr = c.stand(legs, hk=None, pz=BENCH_H + 0.455 * c.S, py=-0.25, px=-0.06, pel=(80, 0, 10), spine=(0, 0, 6),
                 neck=(-25, 0, 0), arms=arms, equip=eq + [E("bench", (-0.1, bench_y, 0), eid="bench")],
                 balance=None, reach=False, planted=("R",),
                 settle=[("plane", np.array([-0.1, bench_y, BENCH_H]), Z, X, 0.14, Y, 0.6, -0.003)])
    return fr


@tpl("tbar_row", "side")
def tbar_row(c, t, L, row):
    n = eqw(row)
    legs, peq = stand_feet(c, row, w=c.hw * 1.3, toe=12)
    single = "single" in n or "meadow" in n
    pivot = np.array([0, 1.35, 0.06]) if not single else np.array([0.45, 1.3, 0.06])

    def tgt(D, Hp, c_, sd):
        m = fam.sh_mid(D, Hp, c)
        lo = m - Z * c.Lh * 0.97
        hi = c.lmk(D, Hp, "chest") - Z * 0.05
        return lo * (1 - L(0, 1)) + hi * L(0, 1) + X * SIDES[sd] * 0.035
    sides = "R" if single else "LR"
    arms = arm_ik(tgt, (0, 1, 0), (0.3, -0.5, 1), curl=0.9, sides=sides)
    if single:
        arms.update(arm_ik(lambda D, Hp, c_, sd: c.J(D, Hp, "lowerleg01.L") + Z * 0.12 + Y * 0.04, (0, 1, 0),
                           (-1, -0.3, 0), key="palm", curl=0.3, sides="L"))
    fr = c.stand(legs, hk=0.82, pel=(58, 0, 0), spine=(4, 0, 0), neck=(-25, 0, 0), arms=arms, equip=peq,
                 balance="com")
    fr.build = _with_landmine(fr.build, pivot, "R" if single else "C")
    return fr


@tpl("cable_row", "side")
def cable_row(c, t, L, row):
    """Seated cable row on a low bench, feet on the foot plate."""
    n = eqw(row)
    if "band" in n:
        return band_row(c, t, L, row)
    pul = np.array([0, 1.15 * c.S, 0.42])

    def tgt(D, Hp, c_, sd):
        m = fam.sh_mid(D, Hp, c)
        far = m + unit(np.array([0, 1, -0.08])) * c.Lh * 0.98
        near = c.lmk(D, Hp, "chest") - Z * 0.1 + Y * 0.05
        return far * (1 - L(0, 1)) + near * L(0, 1) + X * SIDES[sd] * 0.04
    arms = arm_ik(tgt, (0, 0, 1), (0.4, -1, 0.4), curl=0.9)
    lg = {sd: dict(ankle=np.array([SIDES[sd] * 0.14, 0.8 * c.S, 0.2]), fdir=np.array([0, 0.3, 1]),
                   fup=np.array([0, -1, 0.3]), pole=np.array([0, 0.3, 1])) for sd in "LR"}
    eq = [E("cable_tower", pul * [1, 1, 0] + np.array([0, 0.25, 0]), R=fam.rz(180), eid="tower", pulley_h=pul[2]),
          E("bench", (0, 0.1, 0), eid="bench", height=0.3, length=1.4),
          E("plyo_box", (0, 0.8 * c.S + 0.12, 0), eid="foot", size=(0.45, 0.05, 0.32)),
          seg("cable", pul, "gripC", 0.006, "darksteel")]
    return fam.seated(c, seat_h=0.3, seat_y=0.0, pitch=L(18, -6), arms=arms, legs=lg, equip=eq, planted=())


def band_row(c, t, L, row):
    return cable_row.__wrapped__(c, t, L, row) if hasattr(cable_row, "__wrapped__") else machine_row(c, t, L, row)


@tpl("machine_row", "side")
def machine_row(c, t, L, row):
    def tgt(D, Hp, c_, sd):
        m = fam.sh_mid(D, Hp, c)
        far = m + unit(np.array([0, 1, -0.15])) * c.Lh * 0.97
        near = m + Y * 0.12 - Z * 0.2
        return far * (1 - L(0, 1)) + near * L(0, 1) + X * SIDES[sd] * 0.2
    arms = arm_ik(tgt, (0, 0, 1), (0.6, -1, 0.3), curl=0.9)
    eq = [E("seat_machine", (0, 0, 0), R=fam.rz(180), eid="mach", back=True)]
    chest = (np.array([0, 0.33, 1.05]), np.array([0, -1, 0]))
    fr = fam.seated(c, seat_h=0.5, seat_y=0.0, pitch=6, arms=arms, equip=eq, back=chest)
    b = fr.build

    def build():
        spec, eqs, ex = b()
        return spec, eqs + [H("machine_handles", "C", "ball", eid="hnd", width=0.0)], ex
    fr.build = build
    return fr


@tpl("inverted_row", "side")
def inverted_row(c, t, L, row):
    """Body straight under a bar (or straps), heels on the floor."""
    n = eqw(row)
    trx = "trx" in n or "ring" in n
    bar_h = 1.05 * c.S
    bar = np.array([0, 0.0, bar_h])
    chin = "chin" in n
    gw = c.sw * (1.0 if chin else 1.45)
    # body angle from heels to shoulders; shoulders hang below the bar
    pull = L(0, 1)
    hang_d = c.Lh * (0.84 if not chin else 0.78) * (1 - pull) + (0.25 if trx else 0.16) * pull
    heel = np.array([0, 1.05 * c.S, 0.03])
    sh_r = c.r.joint("upperarm01.R")
    an_r = c.r.joint("foot.R")
    blen = np.linalg.norm((sh_r - an_r)[[1, 2]])
    S = np.array([0, -0.04, bar_h - hang_d])
    dy = math.sqrt(max(blen ** 2 - (S[2] - heel[2] - 0.05) ** 2, 0.01))
    feet_y = S[1] + dy
    v0 = (sh_r - an_r)[[1, 2]]
    a0 = math.atan2(v0[1], v0[0])
    a1 = math.atan2(S[2] - 0.08, -dy)
    pitch = math.degrees(a0 - a1)
    from .rig import body_rot
    R = body_rot(pitch, 0, 0)
    pel = S - R @ (sh_r - c.r.pc_rest)
    arms = arm_ik(lambda D, Hp, c_, sd: bar + X * SIDES[sd] * gw / 2 + (Y * 0.0),
                  lambda D, Hp, c_, sd: -SIDES[sd] * X * (1 if not chin else -1),
                  (1, 0.2, -1) if not chin else (0.25, 1.0, -0.6), curl=0.9,
                  fing=(0, -1, 0))
    legs = {sd: dict(ankle=np.array([SIDES[sd] * 0.1, feet_y, 0.075]), fdir=np.array([0, 0.3, 1]),
                     fup=np.array([0, -1, 0.1]), pole=np.array([0, 0, 1])) for sd in "LR"}
    eq = [E("rack", (0, -0.0, 0), eid="rack", hooks=bar_h, safeties=0)] if not trx else trx_straps(c, np.array([0, 0, 2.4]))
    if not trx:
        eq.append(E("barbell", bar, eid="bar", plates=0))
    else:
        arms = arm_ik(lambda D, Hp, c_, sd: np.array([SIDES[sd] * 0.17, 0.0, bar_h]), (0, -1, 0), (1, 0.2, -1),
                      curl=0.9, fing=(0, 0, 1))
    return c.stand(legs, pz=pel[2], py=pel[1], pel=(pitch, 0, 0), arms=arms, equip=eq, balance=None, reach=False,
                   planted=())


# ================================================================== pulldowns
@tpl("lat_pulldown", "side")
def lat_pulldown(c, t, L, row):
    n = eqw(row)
    close = "v-bar" in n or "close" in n or "neutral" in n
    rev = "reverse" in n or "underhand" in n
    single = "single" in n
    wide = "wide" in n
    gw = c.sw * (0.45 if close else (1.0 if rev else (2.1 if wide else 1.8)))
    pul = np.array([0, 0.12, 2.25])

    def center(D, Hp):
        Rt = D[c.r.bi("spine01")]
        m = fam.sh_mid(D, Hp, c)
        h = math.sqrt(max(c.Lh ** 2 - max(gw / 2 - c.sw / 2, 0) ** 2, 0.01)) * 0.97
        top = m + Z * h + Y * 0.1
        bot = c.lmk(D, Hp, "chest_hi") + Y * 0.06 + Z * 0.06
        return top * (1 - L(0, 1)) + bot * L(0, 1)
    sides = "R" if single else "LR"
    arms = arm_ik(lambda D, Hp, c_, sd: center(D, Hp) + X * SIDES[sd] * (gw / 2 if not single else 0.0),
                  lambda D, Hp, c_, sd: (Y if close else -SIDES[sd] * X * (1 if not rev else -1)),
                  (1, -0.4, -1), curl=0.9, fing=(0, 0, 1), sides=sides)
    if single:
        arms.update(arm_ik(lambda D, Hp, c_, sd: c.J(D, Hp, "lowerleg01.L") + Z * 0.1, (0, 1, 0), (-1, -0.4, 0),
                           key="palm", curl=0.3, sides="L"))
    lg = {sd: dict(ball=np.array([SIDES[sd] * 0.18 * c.S, 0.48 * c.S, SOLE]), yaw=10, heel=0,
                   pole=np.array([SIDES[sd] * 0.2, 1, 0.6])) for sd in "LR"}
    eq = [E("lat_station", (0, 0, 0), eid="lat"), seg("cable", pul, "gripC" if not single else "gripR", 0.006,
                                                       "darksteel")]
    if not single:
        eq.append(H("barbell", "C", "bar", eid="bar", plates=0) if not close else H("machine_handles", "C", "ball",
                                                                                     eid="vb", width=0.0))
    if "band" in n or "handle band" in n:
        eq = [seg("bandL", np.array([0, 0.1, 2.3]), "gripL", 0.008, "band"),
              seg("bandR", np.array([0, 0.1, 2.3]), "gripR", 0.008, "band")]
        return c.stand(c.feet(w=c.hw * 1.2), pz=c.pz * 0.55, pel=(-8, 0, 0), arms=arms, equip=eq,
                       settle=[("floor_kneel", 0)], balance=None) if False else \
            fam.seated(c, seat_h=BENCH_H, seat_y=0.0, pitch=L(-6, -16), arms=arms,
                       equip=eq + [E("bench", (0, 0.0, 0), eid="bench", length=0.8)])
    return fam.seated(c, seat_h=0.52, seat_y=0.0, pitch=L(-6, -16), arms=arms, legs=lg, equip=eq)


@tpl("straight_arm_pulldown", "side")
def straight_arm_pulldown(c, t, L, row):
    legs, peq = stand_feet(c, row, w=c.hw * 1.2)
    pul = np.array([0, 0.85, 2.05 * c.S])
    arms = arm_fk((0.12, L(0.75, 0.05), L(0.55, -1)), elbow=12, thumb="pro", curl=0.9, world=True)
    eq = [E("cable_tower", pul * [1, 1, 0] + np.array([0, 0.12, 0]), R=fam.rz(180), eid="tower", pulley_h=pul[2]),
          H("pvc", "C", "bar", eid="bar", length=0.6), seg("cable", pul, "gripC", 0.006, "darksteel")]
    if "band" in eqw(row):
        eq = [seg("bandL", pul, "gripL", 0.008, "band"), seg("bandR", pul, "gripR", 0.008, "band")]
    return c.stand(legs, hk=0.95, pel=(25, 0, 0), arms=arms, equip=eq + peq)


# ================================================================== chest misc
@tpl("cable_crossover", "front3q")
def cable_crossover(c, t, L, row):
    n = eqw(row)
    low = "low" in n
    mid = "mid" in n
    single = "single" in n
    hz = 0.15 if low else (1.25 if mid else 2.1 * c.S)
    legs, peq = stand_feet(c, row, split=0.3)
    zf = (L(-0.3, 0.25) if low else (L(0.0, 0.0) if mid else L(0.35, -0.45)))
    arms = arm_fk((L(1.0, 0.25), L(0.15, 1.0), zf), elbow=18, thumb=(0, 0, 1) if not low else (0, 0, 1),
                  bend=(-1, 0.3, 0), curl=0.88, sides="R" if single else "LR")
    if single:
        arms.update(arm_fk((0.2, 0.05, -1), elbow=40, sides="L"))
    eq = []
    for sd in ("R" if single else "LR"):
        p = np.array([SIDES[sd] * 1.05, -0.05, hz])
        eq.append(E("cable_tower", p * [1, 1, 0] + np.array([SIDES[sd] * 0.12, 0, 0]), R=fam.rz(90 * SIDES[sd]),
                    eid=f"tower{sd}", pulley_h=hz))
        eq.append(seg(f"cable{sd}", p, f"grip{sd}", 0.006, "darksteel"))
    if "band" in n:
        eq = []
    return c.stand(legs, pel=(14 if not low else 6, 0, 0), arms=arms, equip=eq + peq)


@tpl("chest_press_standing", (60, 8))
def chest_press_standing(c, t, L, row):
    n = eqw(row)
    single = "single" in n
    legs, peq = stand_feet(c, row, split=0.35)
    up = 0.35 if "incline" in n else (-0.3 if "decline" in n else 0.0)

    def tgt(D, Hp, c_, sd):
        Rt = D[c.r.bi("spine01")]
        m = fam.sh_mid(D, Hp, c)
        a = c.lmk(D, Hp, "chest") + Y * 0.08 + X * SIDES[sd] * c.sw * 0.55
        b = m + unit(np.array([0, 1, up])) * c.Lh * 0.95 + X * SIDES[sd] * c.sw * 0.3
        return a * (1 - L(0, 1)) + b * L(0, 1)
    sides = "R" if single else "LR"
    arms = arm_ik(tgt, (0, 0, 1) if "svend" not in n else (0, 1, 0), (1, -0.7, -0.3), curl=0.88, sides=sides)
    if single:
        arms.update(arm_fk((0.2, 0.05, -1), elbow=40, sides="L"))
    eq = []
    if "cable" in n:
        for sd in sides:
            p = np.array([SIDES[sd] * 0.6, -0.6, 1.25])
            eq.append(E("cable_tower", p * [1, 1, 0] - np.array([0, 0.12, 0]), eid=f"tower{sd}", pulley_h=p[2]))
            eq.append(seg(f"cable{sd}", p, f"grip{sd}", 0.006, "darksteel"))
    elif "band" in n:
        for sd in sides:
            eq.append(seg(f"band{sd}", np.array([SIDES[sd] * 0.3, -0.5, 1.2]), f"grip{sd}", 0.008, "band"))
    elif "plate" in n or "svend" in n:
        arms = arm_ik(lambda D, Hp, c_, sd: (c.lmk(D, Hp, "chest") + Y * 0.12) * (1 - L(0, 1)) +
                      (fam.sh_mid(D, Hp, c) + Y * c.Lp * 0.9 - Z * 0.06) * L(0, 1) + X * SIDES[sd] * 0.05,
                      (0, 0, 1), (1, -0.5, -0.4), key="palm", curl=0.2, fing=(0, 1, 0.2))
        eq = [H("plate_held", "C", "ball", eid="pl", off=(0, 0, 0))]
    elif "medicine" in n:
        eq = [H("medball", "C", "ball", eid="mb")]
    return c.stand(legs, pel=(8, 0, 0), arms=arms, equip=eq + peq)


@tpl("machine_chest_press", "side")
def machine_chest_press(c, t, L, row):
    n = eqw(row)
    up = 0.35 if "incline" in n else (-0.25 if "decline" in n else 0.0)
    shoulder_press = "shoulder" in n

    def tgt(D, Hp, c_, sd):
        Rt = D[c.r.bi("spine01")]
        m = fam.sh_mid(D, Hp, c)
        if shoulder_press:
            a = m + Z * 0.08 + Y * 0.08 + X * SIDES[sd] * c.sw * 0.75
            b = m + Z * c.Lh * 0.95 + Y * 0.08 + X * SIDES[sd] * c.sw * 0.4
        else:
            a = c.lmk(D, Hp, "chest") + Y * 0.06 + X * SIDES[sd] * c.sw * 0.7
            b = m + unit(np.array([0, 1, up])) * c.Lh * 0.95 + X * SIDES[sd] * c.sw * 0.4
        return a * (1 - L(0, 1)) + b * L(0, 1)
    arms = arm_ik(tgt, (0, 0, 1) if not shoulder_press else (0, 1, 0), (1, -0.6, -0.4), curl=0.88)
    eq = [E("seat_machine", (0, 0, 0), eid="mach", back=True)]
    fr = fam.seated(c, seat_h=0.47 * c.S, seat_y=0.0, pitch=-6, arms=arms, equip=eq,
                    back=(np.array([0, -0.2, 0.88]), np.array([0, 1, 0.14])))
    b = fr.build

    def build():
        spec, eqs, ex = b()
        return spec, eqs + [H("machine_handles", "L", "ball", eid="hL", width=0.0),
                            H("machine_handles", "R", "ball", eid="hR", width=0.0)], ex
    fr.build = build
    return fr


@tpl("pec_deck", "front3q")
def pec_deck(c, t, L, row):
    arms = arm_fk((1.0, L(0.0, 0.95), 0.0), elbow=L(80, 70), bend=(0, 0, 1), thumb=(0, 0, 1), curl=0.6)
    eq = [E("seat_machine", (0, 0, 0), eid="mach", back=True)]
    return fam.seated(c, seat_h=0.5, seat_y=0.0, pitch=-6, arms=arms, equip=eq,
                      back=(np.array([0, -0.2, 0.88]), np.array([0, 1, 0.14])))


# ================================================================== core cable
@tpl("woodchop", (20, 8))
def woodchop(c, t, L, row):
    n = eqw(row)
    low_high = "low to high" in n
    legs, peq = stand_feet(c, row, w=c.hw * 1.7, toe=15)
    a, b = (np.array([0.42, 0.3, 0.3]), np.array([-0.32, 0.38, -0.55]))
    if low_high:
        a, b = np.array([0.35, 0.35, -0.55]), np.array([-0.3, 0.35, 0.3])

    def tgt(D, Hp, c_, sd):
        p = a * (1 - L(0, 1)) + b * L(0, 1)
        return fam.within(c, fam.sh_mid(D, Hp, c), p * c.S * 0.82, 0.86) + X * SIDES[sd] * 0.04
    arms = arm_ik(tgt, (0, 0, 1), (1, -0.2, -0.6), curl=0.9)
    tw = L(35, -30) if not low_high else L(30, -30)
    pul = np.array([1.2, 0.35, (1.9 if not low_high else 0.2) * c.S])
    eq = [E("cable_tower", pul * [1, 1, 0] + np.array([0.12, 0, 0]), R=fam.rz(90), eid="tower", pulley_h=pul[2]),
          seg("cable", pul, "gripC", 0.006, "darksteel")]
    if "medicine" in n or "dumbbell" in n or "balance" in n:
        eq = [H("medball", "C", "ball", eid="mb")]
    return c.stand(legs, hk=L(0.98, 0.86), pel=(L(5, 18), 0, tw * 0.3), spine=(L(4, 10), L(-6, 6), tw * 0.7),
                   arms=arms, equip=eq + peq, balance="com")


@tpl("pallof_press", (25, 10))
def pallof_press(c, t, L, row):
    n = eqw(row)
    kneel = "kneeling" in n or "half" in n

    def tgt(D, Hp, c_, sd):
        Rt = D[c.r.bi("spine01")]          # chest frame: press straight out from the sternum (any body position)
        a = c.lmk(D, Hp, "chest") + Rt @ Y * 0.1
        b = fam.within(c, fam.sh_mid(D, Hp, c), Rt @ Y * c.Lh * 0.95 - Rt @ Z * 0.12, 0.9)
        return a * (1 - L(0, 1)) + b * L(0, 1) + Rt @ X * SIDES[sd] * 0.03
    arms = arm_ik(tgt, lambda D, Hp, c_, sd: D[c.r.bi("spine01")] @ Z, (1, -0.5, -0.4), curl=0.9)
    sup_ = "supine" in n
    pul = np.array([-1.3 if sup_ else 1.3, 0.1 if sup_ else 0.35, 0.55 if sup_ else (1.15 * c.S if not kneel else 0.8)])
    eq = [E("cable_tower", pul * [1, 1, 0] + np.array([-0.12 if sup_ else 0.12, 0, 0]), R=fam.rz(-90 if sup_ else 90),
            eid="tower", pulley_h=pul[2]),
          seg("cable", pul, "gripC", 0.006, "darksteel" if "band" not in n else "band")]
    if "supine" in n:
        from .tpl_floor import supine_knees
        return supine_knees(c, t, L, row, arms=arms, equip=eq)
    if kneel:
        from .tpl_floor import kneeling
        return kneeling(c, t, L, row, arms=arms, equip=eq, half="half" in n)
    legs, peq = stand_feet(c, row, w=c.hw * 1.5)
    return c.stand(legs, hk=0.94, pel=(6, 0, 0), arms=arms, equip=eq + peq)


@tpl("standing_twist", "front")
def standing_twist(c, t, L, row):
    legs, peq = stand_feet(c, row, w=c.hw * 1.6)
    tw = L(-40, 40)

    def tgt(D, Hp, c_, sd):
        Rt = D[c.r.bi("spine01")]
        return fam.sh_mid(D, Hp, c) + Rt @ Y * c.Lh * 0.9 - Z * 0.15 + Rt @ X * SIDES[sd] * 0.04
    arms = arm_ik(tgt, (0, 0, 1), (1, -0.4, -0.4), curl=0.85)
    eq = []
    n = eqw(row)
    if "medicine" in n:
        eq = [H("medball", "C", "ball", eid="mb")]
    elif "cable" in n or "band" in n:
        pul = np.array([1.2, 0.3, 1.2])
        eq = [seg("cable", pul, "gripC", 0.006, "band" if "band" in n else "darksteel")]
    elif "landmine" in n:
        return landmine_rotation(c, t, L, row)
    elif "pvc" in n:
        arms = arm_fk((1.0, 0.0, 0.05), elbow=5, thumb="up", curl=0.6)
    return c.stand(legs, hk=0.97, pel=(4, 0, tw * 0.35), spine=(2, 0, tw * 0.65), arms=arms, equip=eq + peq)


def landmine_rotation(c, t, L, row):
    legs, peq = stand_feet(c, row, w=c.hw * 1.6)
    pivot = np.array([0, 1.6 * c.S, 0.06])
    sw = L(-1, 1)

    def tgt(D, Hp, c_, sd):
        m = fam.sh_mid(D, Hp, c)
        off = np.array([0.42 * sw, 0.45, 0.2 - 0.32 * abs(sw)]) * c.S     # arc: high in front, low at the hips
        k = np.linalg.norm(off)
        if k > c.Lpf * 0.8:
            off = off * c.Lpf * 0.8 / k
        return m + off + X * SIDES[sd] * 0.02
    arms = arm_ik(tgt, (0, 0, 1), (1, -0.4, -0.6), curl=0.88)
    fr = c.stand(legs, hk=0.95, pel=(6, 0, sw * 18), spine=(4, 0, sw * 30), arms=arms, equip=peq)
    fr.build = _with_landmine(fr.build, pivot, "C")
    return fr
