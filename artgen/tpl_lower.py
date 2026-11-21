"""Lower-body standing templates: squats, lunges, hinges, step-ups, calves,
standing hip work, jumps and leg machines."""
from .templates import tpl, E, H, seg, PLATE_R, X, Y, Z, np, math, SIDES
from .poses import SOLE, PAD_SINK, _bar_R
from . import fam
from .fam import arm_fk, arm_ik, legs_fk


ALIASES = (("suspension", "trx"), ("bent-over", "bent over"), ("bent_over", "bent over"), ("ez_bar", "ez bar"), ("ez-bar", "ez bar"), ("trap_bar", "trap bar"),
           ("balance_trainer", "balance trainer"), ("stability_ball", "stability ball"), ("medicine_ball", "medicine ball"),
           ("pvc_dowel", "pvc dowel"), ("foam_roller", "foam roller"), ("pullup_bar", "pull-up bar"),
           ("kettlebell_x", "kettlebell "), ("dumbbell_x", "dumbbell "))


def eqw(row):
    s = (row.get("equipment") or "").lower() + " " + (row.get("name_en") or "").lower()
    for a, b in ALIASES:
        if a in s:
            s += " " + b
    return s


def has(row, *words):
    s = eqw(row)
    return any(w in s for w in words)


def platform(c, row, legs, extra=None):
    """Balance trainer (dome) under the feet when the row asks for it."""
    eq = []
    if has(row, "balance trainer", "bosu"):
        for sd in legs:
            if "ball" in legs[sd]:
                legs[sd] = dict(legs[sd])
                legs[sd]["ball"] = legs[sd]["ball"] + np.array([0, 0, 0.21])
                legs[sd]["surf"] = legs[sd].get("surf", 0.0) + 0.21
        xs = [L["ball"][0] for L in legs.values() if "ball" in L]
        ys = [L["ball"][1] for L in legs.values() if "ball" in L]
        eq.append(E("bosu", (np.mean(xs), np.mean(ys) - 0.05, 0), eid="bosu"))
    return legs, eq


def band_to_feet(c, legs, sides="LR"):
    out = []
    for sd in sides:
        b = legs[sd]["ball"] if "ball" in legs.get(sd, {}) else np.array([SIDES[sd] * 0.15, 0, 0])
        out.append(seg(f"band{sd}", f"grip{sd}", b + np.array([0, -0.05, 0.004]), 0.008, "band"))
    return out


def squat_hold(c, row, default="fwd"):
    """Pick the arm hold from the equipment / name."""
    n = eqw(row)
    if "overhead" in n:
        if "pvc" in n:
            return "oh_pvc", 0.2
        if "dumbbell" in n:
            return ("db_oh1" if "single" in n else "db_oh"), 0.3
        if "kettlebell" in n:
            return "kb_oh1", 0.3
        if "medicine" in n:
            return "medball", 0.2
        return "oh_bar", 0.4
    if "zercher" in n:
        return "zercher", 0.5
    if "landmine" in n:
        return "landmine", 0.3
    if "smith" in n:
        return "smith_bar", 0.5
    if "band" in n:
        return "band_sh", 0.0
    if "front squat" in n or "front rack" in n or "racked" in n:
        if "kettlebell" in n:
            return "kb_rack", 0.3
        return "front_bar", 0.5
    if "goblet" in n or "sumo" in n and "dumbbell" in n:
        return ("kb_goblet" if "kettlebell" in n else "goblet"), 0.25
    if "kettlebell" in n:
        return ("kb_goblet" if "single" in n or "goblet" in n else "kb_rack"), 0.3
    if "dumbbell" in n:
        return "db_side", 0.3
    if "medicine" in n or "wall ball" in n:
        return "medball", 0.15
    if "plate" in n:
        return "plate_chest", 0.15
    if "barbell" in n or "back squat" in n or "olympic" in n or "pause" in n and "squat" in n or \
            "machine" in n and "squat" in (row.get("name_en") or "").lower():
        return "back_bar", 0.6
    return default, 0.0


# ================================================================== squats
def squat_base(c, t, L, row, w=None, toe=22, depth=0.56, pitch=33, hold=None, view_jump=0.0, spine=6, neck=-25):
    h, load = (hold, 0.4) if hold else squat_hold(c, row)
    legs = c.feet(w=w if w is not None else c.hw * 1.3 + 0.08, toe=toe)
    legs, peq = platform(c, row, legs)
    extra = list(peq)
    if h == "band_sh":
        extra += band_to_feet(c, legs)
    if h == "smith_bar":
        extra.append(E("smith", (0, 0.0, 0), eid="smith"))
    if h in ("goblet", "kb_goblet", "medball", "plate_chest", "landmine"):
        pitch *= 0.75
    if h in ("oh_bar", "oh_pvc"):
        pitch *= 0.55
    return c.stand(legs, hk=L(0.985, depth), pel=(L(3, pitch), 0, 0), spine=(L(0, spine), 0, 0),
                   neck=(L(0, neck), 0, 0), hold=h, load=load, equip=extra)


@tpl("back_squat", (62, 8))
def back_squat(c, t, L, row):
    h, _ = squat_hold(c, row, default="back_bar")
    return squat_base(c, t, L, row, hold=h)


@tpl("squat", (62, 8))
def squat(c, t, L, row):
    return squat_base(c, t, L, row)


@tpl("front_squat", (62, 8))
def front_squat(c, t, L, row):
    h = "kb_rack" if has(row, "kettlebell") else "front_bar"
    return squat_base(c, t, L, row, hold=h, pitch=24, spine=2, neck=-10)


@tpl("goblet_squat", (50, 8))
def goblet_squat(c, t, L, row):
    return squat_base(c, t, L, row, hold="kb_goblet" if has(row, "kettlebell") else "goblet", pitch=30, depth=0.53)


@tpl("bodyweight_squat", (50, 8))
def bodyweight_squat(c, t, L, row):
    legs = c.feet(w=c.hw * 1.3 + 0.06, toe=20)
    legs, peq = platform(c, row, legs)
    return c.stand(legs, hk=L(0.985, 0.56), pel=(L(3, 38), 0, 0), spine=(L(0, 6), 0, 0), neck=(L(0, -22), 0, 0),
                   hold="none", hold2="fwd", mix=L(0, 1), equip=peq)


@tpl("sumo_squat", "front3q")
def sumo_squat(c, t, L, row):
    legs = c.feet(w=c.hw * 2.6 + 0.1, toe=38)
    legs, peq = platform(c, row, legs)
    if has(row, "dumbbell", "kettlebell"):
        kb = has(row, "kettlebell")

        def tgt(D, Hp, c_, sd):
            m = fam.sh_mid(D, Hp, c)
            return m - Z * (c.Lh * 0.97) + X * SIDES[sd] * 0.035
        arms = arm_ik(tgt, (0, 1, 0), (1, -0.3, 0), curl=0.85, fing=(0, 0, -1))
        eq = [H("kettlebell" if kb else "dumbbell", "C", "kb" if kb else "vert", eid="w",
                off=(0, 0, 0) if kb else (0, 0, -0.1))]
        return c.stand(legs, hk=L(0.985, 0.6), pel=(L(2, 22), 0, 0), arms=arms, equip=eq + peq, load=0.2,
                       neck=(L(0, -10), 0, 0))
    h, load = squat_hold(c, row, default="clasp")
    return c.stand(legs, hk=L(0.985, 0.6), pel=(L(2, 22), 0, 0), hold=h, load=load, equip=peq,
                   neck=(L(0, -10), 0, 0))


@tpl("overhead_squat", (60, 9))
def overhead_squat(c, t, L, row):
    h = "oh_pvc" if has(row, "pvc") else ("db_oh1" if has(row, "dumbbell") else (
        "kb_oh1" if has(row, "kettlebell") else ("medball" if has(row, "ball") else "oh_bar")))
    if h == "medball":
        legs = c.feet(w=c.hw * 1.3 + 0.08, toe=22)
        legs, peq = platform(c, row, legs)
        arms = fam.arm_ik(lambda D, Hp, c_, sd: fam.sh_mid(D, Hp, c) + (D[c.r.bi("spine01")] @ Z) * c.Lp * 0.95
                          + X * SIDES[sd] * 0.12, (0, 1, 0), (1, -0.5, 0), key="palm", curl=0.2, fing=(0, 0, 1))
        return c.stand(legs, hk=L(0.985, 0.57), pel=(L(2, 26), 0, 0), arms=arms,
                       equip=peq + [H("medball", "C", "ball", eid="mb", off=(0, 0, 0.1))])
    return squat_base(c, t, L, row, hold=h, pitch=30, spine=0, neck=-10)


@tpl("jump_squat", (55, 8))
def jump_squat(c, t, L, row):
    jz = 0.16 * max(0, (t - 0.55) / 0.45)
    legs = c.feet(w=c.hw * 1.3 + 0.04, toe=18)
    for sd in legs:
        legs[sd]["ball"] = legs[sd]["ball"] + np.array([0, 0, jz])
        legs[sd]["heel"] = 45 * min(1, jz / 0.08)
        legs[sd]["surf"] = jz          # in the air: no floor contact expected
    h, load = squat_hold(c, row, default="none")
    hk = 0.58 + 0.42 * min(1.0, t / 0.55)          # continuous: drive up, then leave the floor
    pz = c.pz * min(hk, 0.995) + jz
    return c.stand(legs, pz=pz, pel=(L(36, 2), 0, 0), hold=h if h != "none" else "none",
                   arms=None if h != "none" else arm_fk((L(0.2, 0.25), L(-0.6, 0.0), L(-0.8, -1)), elbow=L(20, 10)),
                   load=load, neck=(L(-20, 0), 0, 0))


@tpl("box_squat", (62, 8))
def box_squat(c, t, L, row):
    h, load = squat_hold(c, row, default="fwd")
    legs = c.feet(w=c.hw * 1.6 + 0.08, toe=26)
    box_h = c.pz * 0.52
    fr = c.stand(legs, hk=L(0.985, 0.56), pel=(L(3, 34), 0, 0), hold=h, load=load, neck=(L(0, -20), 0, 0),
                 equip=[E("plyo_box", (0, -0.42, 0), eid="box", size=(0.5, 0.45, box_h))])
    return fr


@tpl("wall_sit", (75, 8))
def wall_sit(c, t, L, row):
    legs = c.feet(w=c.hw * 1.2, toe=10, y=0.5 * c.S)
    h, load = squat_hold(c, row, default="none")
    if h == "none":
        h = "none"
    wall = np.array([0, -0.08, 0])
    fr = c.stand(legs, hk=L(0.72, 0.5), pel=(L(-2, -6), 0, 0), hold=h, balance=None, neck=(0, 0, 0),
                 equip=[E("wall", wall, eid="wall")],
                 settle=[("plane", wall + np.array([0, 0, 1.2]), Y, X, 0.25, Z, 0.6, -0.002)])
    fr.cons = [cn for cn in fr.cons if cn[0] != "com"]
    return fr


@tpl("pistol_squat", (70, 8))
def pistol_squat(c, t, L, row):
    legs = {"R": c.foot(c.hw * 0.25, 0.0, 10)}
    lf = dict(thigh=np.array([-0.08, L(0.5, 0.97), L(-0.85, -0.05)]), knee=L(25, 4), kbend=np.array([0, -1, 0]),
              fdir=np.array([0, 0.3, 1]))
    legs["L"] = lf
    arms = arm_fk((0.1, 1, 0.1), elbow=5, thumb="up")
    h = []
    if has(row, "kettlebell"):
        return c.stand(legs, hk=L(0.98, 0.42), pel=(L(5, 42), 0, 0), hold="kb_goblet", load=0.2,
                       wsupport=None, neck=(L(0, -15), 0, 0))
    eq = []
    if has(row, "trx"):
        eq = trx_straps(c)
        arms = trx_arms(c, L(0.55, 0.3))
    return c.stand(legs, hk=L(0.98, 0.42), pel=(L(5, 42), 0, 0), arms=arms, equip=eq, neck=(L(0, -15), 0, 0))


@tpl("cossack_squat", "front")
def cossack_squat(c, t, L, row):
    w = c.hw * 3.0 + 0.2
    legs = {"L": c.foot(-w / 2, 0, 30), "R": c.foot(w / 2, 0, L(25, 60))}
    legs["R"]["heel"] = 0
    return c.stand(legs, hk=L(0.82, 0.45), px=L(0, w * 0.32), pel=(L(5, 25), L(0, -6), 0),
                   hold="clasp", wsupport=(L(1, 0.25), L(1, 1)), balance="com", neck=(L(0, -10), 0, 0),
                   equip=trx_straps(c) if has(row, "trx") else [])


# ================================================================== lunges
def lunge_core(c, t, L, row, split, back_heel=55, depth=0.6, front="R", move=None, lateral=False, cross=0.0,
               hold=None, pitch=6, rear_on=None):
    h, load = (hold, 0.3) if hold else squat_hold(c, row, default="hips")
    if h == "back_bar":
        load = 0.4
    s = 1 if front == "R" else -1
    w = c.hw * 1.05
    fpos = {"R": np.array([w / 2, split / 2]), "L": np.array([-w / 2, -split / 2])}
    if front == "L":
        fpos = {"L": np.array([-w / 2, split / 2]), "R": np.array([w / 2, -split / 2])}
    back = "L" if front == "R" else "R"
    fpos[back][0] += cross * (1 if back == "L" else -1)
    legs = {sd: c.foot(p[0], p[1], 8, 0.0) for sd, p in fpos.items()}
    legs[back]["heel"] = back_heel
    if rear_on is not None:  # rear foot laid on a bench (bulgarian)
        bz, by = rear_on
        legs[back] = dict(ankle=np.array([fpos[back][0] * 0.8, by, bz + 0.075]), fdir=np.array([0, -1, -0.35]),
                          fup=np.array([0, -0.3, -1]), pole=np.array([0, 0.3, -1]))
    planted = [front, back] if move is None else [front]
    legs, peq = platform(c, row, legs)
    extra = list(peq)
    if h == "band_sh":
        extra += band_to_feet(c, legs, sides=front)
    wsup = (0.42, 0.58) if front == "R" else (0.58, 0.42)
    return legs, dict(hk=L(0.985, depth) if move is None else None, pel=(L(2, pitch), 0, 0), hold=h, load=load,
                      equip=extra, planted=planted, wsupport=wsup, neck=(L(0, -8), 0, 0))


@tpl("split_squat", (88, 6))
def split_squat(c, t, L, row):
    legs, kw = lunge_core(c, t, L, row, split=0.92 * c.S, depth=0.585)
    if has(row, "smith"):
        kw["hold"] = "smith_bar"
        kw["equip"].append(E("smith", (0, 0.0, 0), eid="smith"))
    if has(row, "trx"):
        kw["hold"] = "none"
        kw["arms"] = trx_arms(c, 0.55)
        kw["equip"] += trx_straps(c)
    return c.stand(legs, **kw)


@tpl("bulgarian_split_squat", (88, 6))
def bulgarian_split_squat(c, t, L, row):
    bench_y = -0.72 * c.S
    legs, kw = lunge_core(c, t, L, row, split=0.0, rear_on=(fam.BENCH_H, bench_y + 0.1), depth=0.56, pitch=10)
    kw["hk"] = L(0.95, 0.56)          # the rear knee stays bent at the top
    legs["R"] = c.foot(c.hw * 0.5, 0.12 * c.S, 8)
    kw["equip"].append(E("bench", (0, bench_y - 0.45, 0), eid="bench"))
    kw["wsupport"] = (0.05, 1.0)
    kw["planted"] = ["R"]
    if "jump" in eqw(row) or "jump" in (row.get("name_en") or "").lower():
        # explosive drive: around the top the front foot leaves the floor and
        # the body rises; the rear foot stays on the bench
        lift = 0.11 * max(0.0, 1 - t / 0.3) ** 2
        legs["R"] = c.foot(c.hw * 0.5, 0.12 * c.S, 8, 25 * max(0.0, 1 - t / 0.3), z=lift)
        kw["hk"] = None
        kw["pz"] = c.pz * L(0.95, 0.56) + lift * 0.9
        kw["planted"] = []
        kw["balance"] = None
    return c.stand(legs, **kw)


@tpl("forward_lunge", (88, 6))
def forward_lunge(c, t, L, row):
    split = 0.95 * c.S
    legs, kw = lunge_core(c, t, L, row, split=split, depth=0.56, move="R")
    # right foot steps from beside the left to the front position
    y0 = legs["L"]["ball"][1]
    yR = y0 + (split) * t
    legs["L"]["ball"] = legs["L"]["ball"] + np.array([0, split / 2, 0])
    legs["L"]["heel"] = 55 * min(1, t * 1.4)
    legs["R"] = c.foot(c.hw * 0.52, yR + split / 2 - split / 2 - c.ball_y + split * 0.0, 8, 0, z=0.07 * math.sin(math.pi * t))
    legs["R"]["ball"][1] = legs["L"]["ball"][1] + split * t
    kw["hk"] = L(0.985, 0.57)
    kw["wsupport"] = (L(1.0, 0.45), L(0.0, 0.55))
    kw["planted"] = ["L"]
    if has(row, "twist", "rotation"):
        kw["spine"] = (0, 0, L(0, 35))
    return c.stand(legs, **kw)


@tpl("reverse_lunge", (88, 6))
def reverse_lunge(c, t, L, row):
    split = 0.95 * c.S
    legs, kw = lunge_core(c, t, L, row, split=split, depth=0.56, move="L")
    yF = legs["R"]["ball"][1] - split / 2
    legs["R"]["ball"] = legs["R"]["ball"] - np.array([0, split / 2, 0])
    legs["L"] = c.foot(-c.hw * 0.52, 0, 8, L(0, 55), z=0.06 * math.sin(math.pi * t))
    legs["L"]["ball"][1] = legs["R"]["ball"][1] - split * t
    kw["hk"] = L(0.985, 0.57)
    kw["wsupport"] = (L(0.0, 0.42), L(1.0, 0.58))
    kw["planted"] = ["R"]
    return c.stand(legs, **kw)


@tpl("lateral_lunge", "front")
def lateral_lunge(c, t, L, row):
    w = c.hw * 3.2 + 0.2
    legs = {"L": c.foot(-w / 2, 0, 20), "R": c.foot(w / 2, 0, 20)}
    h, load = squat_hold(c, row, default="clasp")
    eq = trx_straps(c) if has(row, "trx") else []
    return c.stand(legs, hk=L(0.86, 0.55), px=L(0, w * 0.3), pel=(L(4, 30), L(0, -4), 0), hold=h, load=load,
                   wsupport=(L(1, 0.2), L(1, 1)), neck=(L(0, -12), 0, 0), equip=eq)


@tpl("curtsy_lunge", (40, 8))
def curtsy_lunge(c, t, L, row):
    legs, kw = lunge_core(c, t, L, row, split=0.55 * c.S, depth=0.6, cross=0.42 * c.S, back_heel=60)
    return c.stand(legs, **kw)


@tpl("step_up", (75, 8))
def step_up(c, t, L, row):
    box_h = 0.45 * c.S
    box_y = 0.3 * c.S
    lat = has(row, "lateral")
    h, load = squat_hold(c, row, default="none")
    up = dict(ball=np.array([c.hw * 0.5, box_y + c.ball_y - 0.05, box_h + SOLE]), yaw=8, heel=0)
    if lat:
        up = dict(ball=np.array([c.hw * 0.5 + 0.38, c.ball_y - 0.05, box_h + SOLE]), yaw=8, heel=0)
    yL = L(0.0, box_y - 0.05) if not lat else 0.0
    zL = L(0, box_h) + 0.1 * math.sin(math.pi * t)
    xL = -c.hw * 0.5 if not lat else L(-c.hw * 0.5, c.hw * 0.5 + 0.38 - c.hw * 0.95)
    knee_drive = has(row, "knee drive")
    left = c.foot(xL, yL, 8, 28 * math.sin(math.pi * t), z=zL)   # toe-off then flat on the box (continuous)
    if knee_drive and t > 0.5:
        left = dict(thigh=np.array([-0.05, L(-0.3, 1.0), L(-1, 0.05)]), knee=L(20, 95), kbend=np.array([0, -1, 0]))
    legs = {"L": left, "R": up}
    box = E("plyo_box", (up["ball"][0] - 0.1 if not lat else up["ball"][0], up["ball"][1] - 0.05, 0), eid="box",
            size=(0.6, 0.5, box_h))
    return c.stand(legs, hk=None, pz=L(c.pz * 0.98 - 0.02, c.pz * 0.99 + box_h), pel=(L(14, 2), 0, 0), hold=h,
                   load=load, equip=[box], planted=["R"], wsupport=(L(0.4, 0.0), L(0.6, 1.0)),
                   neck=(L(-10, 0), 0, 0))


# ================================================================== hinges
@tpl("deadlift", (62, 8))
def deadlift(c, t, L, row):
    n = eqw(row)
    if "trap bar" in n or "hex" in n:
        legs = c.feet(w=c.hw * 1.15, toe=10)
        return c.stand(legs, pel=(L(32, 1), 0, 0), neck=(L(-25, 0), 0, 0), hold="trap", balance="bar",
                       bar_z=L(PLATE_R, c.z_sh - c.Lh - 0.012))
    if "dumbbell" in n or "kettlebell" in n:
        if "suitcase" in n or "single" in n:
            legs = c.feet(w=c.hw * 1.0, toe=8)
            return c.stand(legs, pel=(L(30, 1), 0, 0), spine=(L(8, 0), 0, 0), neck=(L(-25, 0), 0, 0),
                           hold="suitcase" if "kettlebell" in n else "db_side", balance="com", hk=L(0.66, 0.99))
        legs = c.feet(w=c.hw * 1.2, toe=10)
        return c.stand(legs, pel=(L(42, 1), 0, 0), neck=(L(-30, 0), 0, 0),
                       hold=("db_side", dict(fy=0.0, spread=0.12)) if "kettlebell" not in n else "kb_side",
                       balance="shoulder", hk=L(0.66, 0.99))
    w = c.hw * 1.0 + 0.04
    gw = None
    toe = 8
    if "sumo" in n:
        w, toe, gw = c.hw * 2.6, 35, c.sw * 0.75
    if "snatch" in n:
        gw = c.sw * 2.2
    legs = c.feet(w=w, toe=toe)
    k = dict(arm_ang=L(-9, 0))
    if gw:
        k["gw"] = gw
    start_z = PLATE_R
    eq = []
    if "elevated" in n or "deficit" in n:
        for sd in legs:
            legs[sd]["ball"] = legs[sd]["ball"] + np.array([0, 0, 0.1])
            legs[sd]["surf"] = 0.1
        eq.append(E("step", (0, 0.0, 0), eid="plat", height=0.1))
    if "rack pull" in n:
        start_z = 0.5 * c.S
        eq.append(E("rack", (0, 0.05, 0), eid="rack", safeties=start_z - 0.04, hooks=1.3 * c.S))
    if "band" in n:
        legs2 = legs
        return c.stand(legs, pel=(L(45, 1), 0, 0), neck=(L(-30, 0), 0, 0), hold=("bar_hang", dict(arm_ang=L(-6, 0), noeq="barbell" not in n)),
                       balance="bar", hk=L(0.68, 0.99), equip=band_to_feet(c, legs))
    hold = "bar_hang"
    if "pvc" in n:
        hold = "pvc_hang"
    return c.stand(legs, pel=(L(52 if "sumo" not in n else 34, 1), 0, 0), neck=(L(-38, 0), 0, 0),
                   hold=(hold, k), balance="bar", bar_z=L(start_z, c.z_sh - c.Lh - 0.012), equip=eq)


@tpl("romanian_deadlift", (62, 8))
def romanian_deadlift(c, t, L, row):
    n = eqw(row)
    legs = c.feet(w=c.hw * 1.0 + 0.02, toe=6)
    stiff = "stiff" in n
    hold = ("bar_hang", dict(arm_ang=L(0, -4)))
    if "dumbbell" in n:
        hold = ("db_side", dict(spread=0.1, fy=0.06))
    elif "kettlebell" in n or "medicine" in n:
        hold = "kb_side" if "kettlebell" in n else "medball"
    elif "pvc" in n:
        hold = ("pvc_hang", dict(arm_ang=L(0, -4)))
    elif "landmine" in n:
        hold = "landmine"
    elif "band" in n and "barbell" not in n:
        hold = ("bar_hang", dict(arm_ang=L(0, -4), noeq=True))   # band under the feet, handles in the hands
    eq = []
    if "band" in n:
        eq = band_to_feet(c, legs)
    if "smith" in n:
        eq.append(E("smith", (0, 0.05, 0), eid="smith"))
        hold = ("bar_hang", dict(arm_ang=L(0, -4)))
    return c.stand(legs, hk=L(0.985, 0.93 if stiff else 0.88), pel=(L(2, 72 if stiff else 66), 0, 0),
                   spine=(L(0, 6), 0, 0), neck=(L(0, -30), 0, 0), hold=hold, balance="com", load=0.25, equip=eq)


@tpl("good_morning", (62, 8))
def good_morning(c, t, L, row):
    legs = c.feet(w=c.hw * 1.2, toe=10)
    n = eqw(row)
    hold = "back_bar" if "barbell" in n else ("head" if "pvc" not in n and "kettlebell" not in n else "back_bar")
    if "kettlebell" in n or "dumbbell" in n:
        hold = "goblet" if "dumbbell" in n else "kb_goblet"
    eq = []
    if "band" in n:
        hold = "band_sh"
        eq = band_to_feet(c, legs)
    if "pvc" in n:
        hold = "back_bar"
    return c.stand(legs, hk=L(0.985, 0.9), pel=(L(2, 72), 0, 0), spine=(L(0, 4), 0, 0), neck=(L(0, -25), 0, 0),
                   hold=hold, balance="com", load=0.3, equip=eq)


@tpl("single_leg_rdl", (80, 8))
def single_leg_rdl(c, t, L, row):
    legs = {"R": c.foot(c.hw * 0.22, 0, 6)}
    legs["L"] = dict(thigh=np.array([-0.04, L(-0.15, -0.95), L(-1, -0.2)]), knee=L(25, 4), kbend=np.array([0, -1, 0]),
                     fdir=np.array([0, L(0.6, -0.2), L(-0.6, -1)]))
    n = eqw(row)
    hold = "none"
    arms = None
    if "dumbbell" in n:
        hold = "db_side"
    elif "kettlebell" in n:
        hold = "kb_side"
    elif "medicine" in n:
        hold = "medball"
    elif "landmine" in n:
        hold = "landmine"
    else:
        arms = arm_fk((L(0.15, 0.2), L(0.0, 0.3), -1), elbow=8)
    return c.stand(legs, hk=L(0.99, 0.96), pel=(L(2, 82), 0, 0), spine=(L(0, 4), 0, 0), neck=(L(0, -30), 0, 0),
                   hold=hold, arms=arms, balance="com", load=0.15)


@tpl("kb_swing", "side")
def kb_swing(c, t, L, row):
    legs = c.feet(w=c.hw * 1.6, toe=18)
    single = "single" in eqw(row) or "alternating" in eqw(row)
    american = "american" in eqw(row)
    ang = L(-0.9, 0.0 if not american else 1.0)  # arm direction: back between legs -> forward/up

    def tgt(D, Hp, c_, sd):
        m = fam.sh_mid(D, Hp, c)
        a = math.atan2(1, 1)
        th = math.radians(L(-28, 92 if not american else 175))
        d = np.array([0, math.sin(th), -math.cos(th)])
        return m + d * c.Lh * 0.97 + X * SIDES[sd] * 0.03

    sides = "R" if single else "LR"
    arms = arm_ik(tgt, (0, 0, 1), (1, 0, 0.3), curl=0.9, sides=sides)
    if single:
        arms.update(arm_fk((0.2, 0.0, -1), elbow=10, sides="L"))
    eq = [H("kettlebell", "R" if single else "C", "kb", eid="kb", off=(0, 0, 0.02))]
    return c.stand(legs, hk=L(0.8, 0.99), pel=(L(62, -2), 0, 0), spine=(L(4, 0), 0, 0), neck=(L(-30, 0), 0, 0),
                   arms=arms, equip=eq, balance="com", load=0.1)


@tpl("cable_pull_through", "side")
def cable_pull_through(c, t, L, row):
    legs = c.feet(w=c.hw * 1.6, toe=15, y=0.25)
    pul = np.array([0, -1.1, 0.12])

    def tgt(D, Hp, c_, sd):
        m = fam.sh_mid(D, Hp, c)
        return m - Z * c.Lh * 0.92 + Y * L(-0.18, 0.12) + X * SIDES[sd] * 0.03
    arms = arm_ik(tgt, (0, 1, 0), (1, 0, 0), curl=0.9)
    return c.stand(legs, hk=L(0.86, 0.99), pel=(L(62, 0), 0, 0), neck=(L(-28, 0), 0, 0), arms=arms,
                   equip=[E("cable_tower", pul * [1, 1, 0] + np.array([0, -0.12, 0]), eid="tower", pulley_h=0.12),
                          seg("cable", pul, "gripC", 0.006, "darksteel")], balance="com")


# ================================================================== calves
@tpl("calf_raise", (70, 6))
def calf_raise(c, t, L, row):
    n = eqw(row)
    single = "single" in n or "one-leg" in n
    block = 0.0 if "floor" in n else 0.09
    legs = c.feet(w=c.hw * 0.95, toe=6, z=(block, block))
    for sd in legs:
        legs[sd]["heel"] = L(-12 if block else 0, 28)
    if single:
        legs["L"] = dict(thigh=np.array([-0.05, -0.15, -1]), knee=70, kbend=np.array([0, -1, 0]))
    hold = "none"
    eq = [E("calf_block", (0, c.ball_y - 0.05, 0), eid="block")] if block else []
    if "dumbbell" in n:
        hold = "db_side"
    elif "kettlebell" in n:
        hold = "kb_side"
    elif "smith" in n:
        hold = "smith_bar"
        eq.append(E("smith", (0, 0.0, 0), eid="smith"))
    elif "barbell" in n:
        hold = "back_bar"
    elif "machine" in n:
        hold = "back_bar"
    pz = c.pz * 0.99 + block + c.ankle_rise(legs["R"]["heel"])
    return c.stand(legs, pz=pz, hold=hold, equip=eq, load=0.3, planted=("R",) if single else ("L", "R"))


@tpl("seated_calf_raise", "side")
def seated_calf_raise(c, t, L, row):
    legs = {sd: dict(ball=np.array([SIDES[sd] * 0.12 * c.S, 0.5 * c.S, 0.09 + SOLE]), yaw=4, heel=L(-10, 26))
            for sd in "LR"}

    def tgt(D, Hp, c_, sd):
        k = c.J(D, Hp, f"lowerleg01.{sd}")
        return k + Z * 0.07 + Y * 0.04
    arms = arm_ik(tgt, (-1, 0, 0), (0.6, -1, 0.2), curl=0.85, fing=(0, 1, -0.4))
    eq = [E("calf_block", (0, 0.5 * c.S + c.ball_y - 0.05, 0), eid="block")]
    n = eqw(row)
    if "machine" in n:
        eq.append(E("seat_machine", (0, 0, 0), eid="mach", back=False))
    else:
        eq.append(E("bench", (0, -0.05, 0), eid="bench", length=0.7))
    if "dumbbell" in n:
        eq += [H("dumbbell", "L"), H("dumbbell", "R")]
    elif "barbell" in n:
        eq += [H("barbell", "C", "bar", eid="bar")]
    fr = fam.seated(c, seat_h=fam.BENCH_H + 0.0, seat_y=0.0, legs=legs, arms=arms, equip=eq, pitch=8)
    return fr


# ================================================================ standing hip
def one_leg_stand(c, t, L, row, leg, arms=None, hold="hips", equip=(), pel=(2, 0, 0), spine=(0, 0, 0), px=0.0):
    leg = dict(leg)
    leg.setdefault("fdir", np.array([0, 1, -0.35]))
    leg["knee"] = max(leg.get("knee", 0), 14)
    legs = {"R": c.foot(c.hw * 0.25, 0, 8), "L": leg}
    legs, peq = platform(c, row, legs)
    return c.stand(legs, hk=0.99, px=px, pel=pel, spine=spine, hold=hold, arms=arms, equip=list(equip) + peq,
                   planted=("R",), balance="com")


def ankle_cable(c, side, pulley):
    return [E("cable_tower", pulley * [1, 1, 0] + np.array([0, -0.12, 0]), eid="tower",
              pulley_h=pulley[2]),
            seg("cable", pulley, ("gripR", (0, 0, 0)), 0.0, "darksteel")]


@tpl("hip_abduction_standing", "front")
def hip_abduction_standing(c, t, L, row):
    leg = dict(thigh=np.array([-L(0.08, 0.62), 0.02, -1]), knee=4, kbend=np.array([0, -1, 0]),
               fdir=np.array([-0.1, 1, -0.2]))
    eq = []
    if has(row, "cable", "band"):
        eq = [seg("band", np.array([0.35, 0.0, 0.08]), np.array([-0.2, 0.0, 0.1]), 0.0, "band")]
    return one_leg_stand(c, t, L, row, leg, pel=(2, L(0, -6), 0), hold="hips", equip=[])


@tpl("hip_adduction_standing", "front")
def hip_adduction_standing(c, t, L, row):
    leg = dict(thigh=np.array([-L(0.35, -0.12), 0.08, -1]), knee=4, kbend=np.array([0, -1, 0]),
               fdir=np.array([0.1, 1, -0.2]))
    return one_leg_stand(c, t, L, row, leg, hold="hips", pel=(2, L(-4, 0), 0))


@tpl("standing_kickback", "side")
def standing_kickback(c, t, L, row):
    leg = dict(thigh=np.array([-0.06, L(-0.1, -0.75), -1]), knee=L(30, 10), kbend=np.array([0, -1, 0]),
               fdir=np.array([0, L(0.6, 0.2), -1]))
    arms = None
    eq = []
    hold = "hips"
    if has(row, "cable", "machine"):
        hold = "fwd"
    return one_leg_stand(c, t, L, row, leg, hold=hold, pel=(L(8, 18), 0, 0), equip=eq)


@tpl("standing_leg_curl", "side")
def standing_leg_curl(c, t, L, row):
    leg = dict(thigh=np.array([-0.05, -0.05, -1]), knee=L(5, 105), kbend=np.array([0, -1, 0]))
    return one_leg_stand(c, t, L, row, leg, hold="hips", pel=(4, 0, 0))


@tpl("standing_knee_raise", (60, 8))
def standing_knee_raise(c, t, L, row):
    leg = dict(thigh=np.array([-0.05, L(0.0, 1.0), L(-1, 0.0)]), knee=L(5, 95), kbend=np.array([0, -1, 0]))
    n = eqw(row)
    if "crunch" in n or "elbow" in n:
        return one_leg_stand(c, t, L, row, leg, hold="head", spine=(L(0, 25), 0, L(0, 25)))
    if "wall" in (row.get("name_en") or "").lower():
        # body leaning into a wall on straight arms; the left knee drives up toward the chest
        wall_y = 0.78 * c.S
        lean = dict(thigh=np.array([-0.05, L(-0.25, 0.85), L(-1, 0.1)]), knee=L(10, 100), kbend=np.array([0, -1, 0]))
        legs = {"R": c.foot(c.hw * 0.4, -0.18 * c.S, 8, 35), "L": lean}
        arms = arm_ik(lambda D, Hp, c_, sd: np.array([SIDES[sd] * 0.22, wall_y - 0.035, 1.3 * c.S]), (-1, 0, 0),
                      (0.4, -1, -0.3), key="palm", curl=0.0, fing=(0, 0.1, 1))
        fr = c.stand(legs, hk=0.97, pel=(22, 0, 0), arms=arms, balance=None, planted=["R"],
                     equip=[E("wall", (0, wall_y, 0), R=fam.rz(180), eid="wall")])
        fr.cons.append(("reach_arms", Y, ["L", "R"]))
        return fr
    return one_leg_stand(c, t, L, row, leg, hold="hips")


@tpl("leg_swing", "side")
def leg_swing(c, t, L, row):
    lat = has(row, "lateral", "side")
    if lat:
        leg = dict(thigh=np.array([L(0.45, -0.45), 0.1, -1]), knee=5, kbend=np.array([0, -1, 0]))
    else:
        y = L(-0.6, 1.0)
        # the swinging foot passes just over the floor: a soft knee where the leg is vertical
        leg = dict(thigh=np.array([-0.05, y, L(-1, -0.4)]), knee=5 + 32 * math.exp(-(y / 0.38) ** 2),
                   kbend=np.array([0, -1, 0]))
    return one_leg_stand(c, t, L, row, leg, hold="hips")


@tpl("hip_circle_standing", (40, 8))
def hip_circle_standing(c, t, L, row):
    a = t * math.pi
    leg = dict(thigh=np.array([-0.05 - 0.5 * math.sin(a), 0.6 * math.cos(a) * 0.8 + 0.3, -0.7]), knee=85,
               kbend=np.array([0, -1, 0]))
    return one_leg_stand(c, t, L, row, leg, hold="hips")


# ================================================================== machines
@tpl("leg_press", (118, 24))
def leg_press(c, t, L, row):
    """45-degree sled: hips on the seat, feet on the platform that slides
    along the rails."""
    calf = has(row, "calf")
    R45 = np.array([0, math.cos(math.radians(45)), math.sin(math.radians(45))])
    seat = np.array([0, -0.2, 0.46])
    travel = L(0.0, 0.34) if not calf else 0.0
    plat0 = np.array([0, 0.14, 0.82]) * c.S
    plat = plat0 + R45 * (0.35 * c.S - travel)    # knees keep a soft bend at the top
    nrm = -R45  # platform faces the user
    heel = L(-10, 25) if calf else 0.0
    legs = {}
    for sd in "LR":
        s = SIDES[sd]
        ball = plat + np.array([s * 0.15 * c.S, 0, 0]) + R45 * 0.06 + nrm * 0.0
        fdir = np.array([0, -math.sin(math.radians(45)), math.cos(math.radians(45))])
        ank = ball - fdir * (c.ball_y - c.r.foot_rest["R"]["ankle"][1]) * 1.0 + nrm * 0.075
        legs[sd] = dict(ankle=ank, fdir=fdir, fup=nrm * -1 * -1, pole=np.array([s * 0.25, 0.2, 1.0]))
    back = (np.array([0, -0.48, 0.66]), np.array([0, math.sin(math.radians(62)), math.cos(math.radians(62))]))
    eq = [E("leg_press", (0, 0, 0), eid="lp"), E("leg_press_sled", plat + R45 * 0.0, eid="sled", dyn=True)]
    arms = arm_ik(lambda D, Hp, c_, sd: np.array([SIDES[sd] * 0.3, -0.18, 0.48]), (0, 1, 0), (1, -0.5, 0),
                  curl=0.8)
    fr = fam.seated(c, seat_h=0.46, seat_y=-0.2, pitch=-38, legs=legs, back=back, arms=arms, equip=eq,
                    spine=(0, 0, 0), neck=(15, 0, 0))
    return fr


@tpl("leg_extension", "side")
def leg_extension(c, t, L, row):
    single = "single" in eqw(row)
    knee_y = 0.02
    kz = 0.5
    seat_y = -0.24

    def lg(sd, ang):
        return dict(thigh=np.array([SIDES[sd] * 0.08, 1.0, -0.02]), knee=ang, kbend=np.array([0, 0, -1]),
                    fdir=np.array([0, 0.3, 1]))
    legs = {"R": lg("R", L(92, 5)), "L": lg("L", 92 if single else L(92, 5))}
    arms = arm_ik(lambda D, Hp, c_, sd: np.array([SIDES[sd] * 0.27, seat_y + 0.05, 0.5]), (0, 1, 0), (1, -0.3, 0),
                  curl=0.85)
    ang = math.radians(L(92, 5))
    lever_R = np.array([[1, 0, 0], [0, math.cos(math.pi / 2 - ang), -math.sin(math.pi / 2 - ang)],
                        [0, math.sin(math.pi / 2 - ang), math.cos(math.pi / 2 - ang)]])
    eq = [E("leg_machine", (0, 0, 0), eid="lm"),
          E("leg_lever", (0.14, knee_y, kz), R=fam.rx(L(0, 87)), eid="lever", dyn=True)]
    if has(row, "band"):
        eq = []
        # seat height leaves the feet just clear of the floor at the start
        legs = {"R": lg("R", L(66, 5)), "L": lg("L", 66 if single else L(66, 5))}
        fr = fam.seated(c, seat_h=fam.BENCH_H, seat_y=-0.2, legs=legs, arms=arms,
                        equip=[E("bench", (0, -0.25, 0), eid="bench", length=0.8)], planted=())
        return fr
    return fam.seated(c, seat_h=0.51, seat_y=seat_y, legs=legs, arms=arms, equip=eq, planted=(),
                      back=(np.array([0, -0.48, 0.82]), np.array([0, 1, 0.2])))


@tpl("seated_leg_curl", "side")
def seated_leg_curl(c, t, L, row):
    def lg(sd):
        return dict(thigh=np.array([SIDES[sd] * 0.08, 1.0, -0.02]), knee=L(8, 100), kbend=np.array([0, 0, -1]),
                    fdir=np.array([0, 0.3, 1]))
    legs = {sd: lg(sd) for sd in "LR"}
    arms = arm_ik(lambda D, Hp, c_, sd: np.array([SIDES[sd] * 0.27, -0.19, 0.5]), (0, 1, 0), (1, -0.3, 0),
                  curl=0.85)
    eq = [E("leg_machine", (0, 0, 0), eid="lm"),
          E("leg_lever", (0.14, 0.02, 0.5), R=fam.rx(L(85, 0)) @ fam.rx(180) @ fam.rx(-0), eid="lever", dyn=True)]
    return fam.seated(c, seat_h=0.51, seat_y=-0.24, legs=legs, arms=arms, equip=eq, planted=(),
                      back=(np.array([0, -0.48, 0.82]), np.array([0, 1, 0.2])))


@tpl("hip_abductor_machine", "front")
def hip_abductor_machine(c, t, L, row):
    add = "adduct" in eqw(row)
    a0, a1 = (0.45, 0.05) if add else (0.06, 0.45)

    def lg(sd):
        return dict(thigh=np.array([SIDES[sd] * L(a0, a1), 1.0, -0.05]), knee=88, kbend=np.array([0, 0, -1]),
                    fdir=np.array([0, 0.3, 0.2]))
    legs = {sd: lg(sd) for sd in "LR"}
    def handle(D, Hp, c_, sd):
        sh = fam.shoulder(D, Hp, c, sd)
        return fam.within(c, sh, np.array([SIDES[sd] * 0.26, -0.05, 0.52]) - sh, 0.95)
    arms = arm_ik(handle, (0, 1, 0), (1, -0.3, 0), curl=0.85)
    eq = [E("hip_machine", (0, 0, 0), eid="hm")]
    for sd in "LR":
        eq.append(E("hip_pad", (SIDES[sd] * (0.11 + 0.38 * L(a0, a1)), 0.3, 0.6), eid=f"pad{sd}", dyn=True))
    return fam.seated(c, seat_h=0.54, seat_y=0.0, legs=legs, arms=arms, equip=eq, planted=(), pitch=-12,
                      back=(np.array([0, -0.28, 0.85]), np.array([0, 1, 0.35])))


@tpl("glute_kickback_machine", "side")
def glute_kickback_machine(c, t, L, row):
    return quad_kick(c, t, L, row, machine=True)


def quad_kick(c, t, L, row, machine=False):
    from .tpl_floor import quadruped
    leg = dict(thigh=np.array([-0.03, L(0.15, -1.0), L(-1, 0.25)]), knee=L(95, 20), kbend=np.array([0, -1, 0.3]))
    return quadruped(c, t, L, row, legs_over={"R": leg})


# ============================================================ jumps / agility
def airborne(c, t, L, row, legsA, legsB, lift, hk=(0.75, 0.98), pel=((25, 0, 0), (2, 0, 0)), arms=None,
             hold="none", equip=(), view=None, px=(0, 0), py=(0, 0)):
    jz = lift * math.sin(math.pi * t)
    legs = {}
    for sd in "LR":
        A, B = legsA[sd], legsB[sd]
        if "ball" in A and "ball" in B:
            legs[sd] = dict(A)
            legs[sd]["ball"] = np.asarray(A["ball"]) * (1 - t) + np.asarray(B["ball"]) * t + np.array([0, 0, jz])
            legs[sd]["heel"] = A.get("heel", 0) * (1 - t) + B.get("heel", 0) * t + 40 * math.sin(math.pi * t)
        else:
            legs[sd] = B if t > 0.5 else A
    pz = c.pz * L(*hk) + jz
    return c.stand(legs, pz=pz, px=L(*px), py=L(*py), pel=(L(pel[0][0], pel[1][0]), L(pel[0][1], pel[1][1]), 0),
                   hold=hold, arms=arms, equip=list(equip), planted=(), balance="com")


@tpl("box_jump", (80, 8))
def box_jump(c, t, L, row):
    bh = 0.5 * c.S
    by = 0.62 * c.S
    A = c.feet(w=c.hw * 1.2, toe=12)
    B = c.feet(w=c.hw * 1.2, toe=12, y=by, z=(bh, bh))
    jz = 0.25 * math.sin(math.pi * t)
    legs = {}
    for sd in "LR":
        legs[sd] = dict(A[sd])
        legs[sd]["ball"] = A[sd]["ball"] * (1 - t) + B[sd]["ball"] * t + np.array([0, 0, jz])
    pz = L(c.pz * 0.7, c.pz * 0.72 + bh) + jz + 0.2 * math.sin(math.pi * t)
    arms = arm_fk((0.15, L(-0.5, 0.9), L(-0.85, 0.1)), elbow=L(15, 25), thumb="fwd")
    return c.stand(legs, pz=pz, py=L(0, by), pel=(L(35, 28), 0, 0), arms=arms, planted=(),
                   equip=[E("plyo_box", (0, by + 0.05, 0), eid="box", size=(0.6, 0.5, bh))], balance=None,
                   neck=(L(-20, -10), 0, 0))


@tpl("broad_jump", (88, 8))
def broad_jump(c, t, L, row):
    d = 1.0 * c.S
    A = c.feet(w=c.hw * 1.2, toe=10)
    B = c.feet(w=c.hw * 1.2, toe=10, y=d)
    arms = arm_fk((0.15, L(-0.6, 0.9), L(-0.8, 0.2)), elbow=L(15, 25), thumb="fwd")
    return airborne(c, t, L, row, A, B, 0.3, hk=(0.72, 0.74), pel=((35, 0, 0), (30, 0, 0)), arms=arms,
                    py=(0, d))


@tpl("tuck_jump", (60, 8))
def tuck_jump(c, t, L, row):
    jz = 0.42 * t
    legs = legs_fk((0.05, L(0.0, 0.9), L(-1, -0.25)), knee=L(10, 120), kbend=(0, -1, 0), fdir=(0, 0.3, -1))
    if t < 0.15:
        legs = c.feet(w=c.hw * 1.1, toe=8)
    arms = arm_fk((0.15, L(0.0, 0.8), L(-1, -0.2)), elbow=L(15, 80), thumb="up")
    return c.stand(legs, pz=c.pz * 0.97 + jz, pel=(L(4, 10), 0, 0), arms=arms, planted=(), balance=None)


@tpl("jumping_jack", "front")
def jumping_jack(c, t, L, row):
    jz = 0.06 * math.sin(math.pi * t)
    w = L(c.hw * 1.0, c.hw * 2.8)
    legs = c.feet(w=w, toe=L(6, 20))
    for sd in legs:
        legs[sd]["ball"] = legs[sd]["ball"] + np.array([0, 0, jz])
        legs[sd]["heel"] = 30 * math.sin(math.pi * t)
    star = has(row, "star")
    arms = arm_fk((L(0.15, 0.7), 0.05, L(-1, 0.75 if not star else 0.35)), elbow=8, thumb="fwd")
    return c.stand(legs, hk=0.985, pz=c.pz * 0.975 + jz, arms=arms, planted=(), balance="com")


@tpl("high_knees", (70, 8))
def high_knees(c, t, L, row):
    jz = 0.04 * math.sin(math.pi * t)
    up = dict(thigh=np.array([0.05, 1.0, -0.15]), knee=100, kbend=np.array([0, -1, 0]), fdir=np.array([0, 0.4, -1]))
    down = c.foot(0, 0, 6, 25)
    a = t
    R_up = dict(thigh=np.array([0.05, L(1.0, -0.1), L(-0.15, -1)]), knee=L(100, 15), kbend=np.array([0, -1, 0]))
    L_up = dict(thigh=np.array([-0.05, L(-0.1, 1.0), L(-1, -0.15)]), knee=L(15, 100), kbend=np.array([0, -1, 0]))
    legs = {"R": R_up, "L": L_up}
    if has(row, "butt kick"):
        legs = {"R": dict(thigh=np.array([0.05, -0.05, -1]), knee=L(130, 15), kbend=np.array([0, -1, 0])),
                "L": dict(thigh=np.array([-0.05, -0.05, -1]), knee=L(15, 130), kbend=np.array([0, -1, 0]))}
    arms = {"R": arm_fk((0.1, L(-0.5, 0.6), -0.8), elbow=90, sides="R")["R"],
            "L": arm_fk((0.1, L(0.6, -0.5), -0.8), elbow=90, sides="L")["L"]}
    fr = c.stand(legs, pz=c.pz * 0.985 + jz, pel=(4, 0, 0), arms=arms, planted=(), balance=None,
                 settle=[("floor", SOLE * 0)])
    return fr


@tpl("lateral_hop", "front")
def lateral_hop(c, t, L, row):
    d = 0.45
    A = c.feet(w=c.hw * 0.9, toe=6, dx=-d / 2)
    B = c.feet(w=c.hw * 0.9, toe=6, dx=d / 2)
    single = "1-foot" in eqw(row) or "single" in eqw(row)
    if single:
        A["L"] = B["L"] = dict(thigh=np.array([-0.05, -0.2, -1]), knee=80, kbend=np.array([0, -1, 0]))
    arms = arm_fk((0.2, 0.3, -0.9), elbow=70)
    cone = "cone" in eqw(row) or "cone" in (row.get("name_en") or "").lower()
    fr = airborne(c, t, L, row, A, B, 0.3 if cone else 0.12, hk=(0.86, 0.86), pel=((15, 0, 0), (15, 0, 0)),
                  arms=arms, px=(-d / 2, d / 2))
    if cone:                 # hop sideways over a cone between the two landing spots
        b0 = fr.build

        def build():
            spec, eq, ex = b0()
            return spec, list(eq) + [E("cone", (0, 0.02, 0), eid="cone", h=0.2)], ex
        fr.build = build
    return fr


@tpl("skater_jump", "front")
def skater_jump(c, t, L, row):
    d = 0.9 * c.S
    A = {"L": c.foot(-d / 2, 0, 10), "R": dict(thigh=np.array([-0.4, -0.3, -1]), knee=40, kbend=np.array([0, -1, 0]))}
    B = {"R": c.foot(d / 2, 0, 10), "L": dict(thigh=np.array([0.4, -0.3, -1]), knee=40, kbend=np.array([0, -1, 0]))}
    jz = 0.12 * math.sin(math.pi * t)
    legs = {}
    if t < 0.5:
        legs = dict(A)
        legs["L"] = dict(A["L"]); legs["L"]["ball"] = A["L"]["ball"] + np.array([0, 0, jz])
    else:
        legs = dict(B)
        legs["R"] = dict(B["R"]); legs["R"]["ball"] = B["R"]["ball"] + np.array([0, 0, jz])
    arms = arm_fk((L(0.6, -0.3), 0.3, -0.6), elbow=20)
    return c.stand(legs, hk=0.8, pz=c.pz * 0.8 + jz, px=L(-d / 2, d / 2), pel=(25, L(8, -8), 0), arms=arms,
                   planted=(), balance=None)


@tpl("split_jump", (85, 6))
def split_jump(c, t, L, row):
    split = 0.85 * c.S
    jz = 0.18 * math.sin(math.pi * t)
    fwdR = L(1, -1)
    legs = {"R": c.foot(c.hw * 0.5, fwdR * split / 2, 8, L(0, 55)), "L": c.foot(-c.hw * 0.5, -fwdR * split / 2, 8, L(55, 0))}
    for sd in legs:
        legs[sd]["ball"] = legs[sd]["ball"] + np.array([0, 0, jz])
    arms = arm_fk((0.15, L(0.4, -0.4), -0.85), elbow=60)
    return c.stand(legs, pz=c.pz * 0.62 + jz + 0.2 * math.sin(math.pi * t), pel=(6, 0, 0), arms=arms, planted=(),
                   balance=None)


# ================================================================== sled / carry
@tpl("sled_push", (80, 8))
def sled_push(c, t, L, row):
    step = 0.55 * c.S
    legs = {"R": c.foot(c.hw * 0.55, L(step / 2, -step / 2), 8, L(10, 60)),
            "L": c.foot(-c.hw * 0.55, L(-step / 2, step / 2), 8, L(60, 10))}
    pull = has(row, "drag", "pull")
    if pull:
        arms = fam.arm_fk((0.1, 0.3, -1), elbow=5, thumb="in")
        eq = [E("sled", (0, 1.9, 0), eid="sled"), seg("strapL", "gripL", np.array([-0.1, 1.5, 0.3]), 0.012, "strap"),
              seg("strapR", "gripR", np.array([0.1, 1.5, 0.3]), 0.012, "strap")]
        return c.stand(legs, hk=0.8, pel=(-12, 0, 0), arms=arms, equip=eq, planted=(), balance=None,
                       neck=(10, 0, 0))
    sled_y = 1.05 * c.S

    def tgt(D, Hp, c_, sd):
        return np.array([SIDES[sd] * 0.22, sled_y, 1.0])
    arms = arm_ik(tgt, (-1, 0, 0), (0.4, -0.3, -1), curl=0.85, fing=(0, 0, 1))
    return c.stand(legs, hk=0.78, py=0.1, pel=(48, 0, 0), arms=arms, planted=(),
                   equip=[E("sled", (0, sled_y, 0), eid="sled")], balance=None, neck=(-30, 0, 0))


@tpl("farmer_walk", (55, 8))
def farmer_walk(c, t, L, row):
    step = 0.42 * c.S
    legs = {"R": c.foot(c.hw * 0.5, L(step / 2, -step / 2), 8, L(0, 35)),
            "L": c.foot(-c.hw * 0.5, L(-step / 2, step / 2), 8, L(35, 0))}
    n = eqw(row)
    hold = "kb_side" if "kettlebell" in n else "db_side"
    if "single" in n:
        hold = "suitcase"
    if "pinch" in n and "plate" in n:
        # a weight plate pinched by its rim at each side, the disc in the sagittal plane
        Rp = ((0.0, 1.0, 0.0), (-1.0, 0.0, 0.0), (0.0, 0.0, 1.0))
        arms = arm_fk((0.17, 0.0, -1), elbow=6, thumb="fwd", curl=0.5)
        eq = [dict(kind="plate_held", M=np.eye(4), id=f"pl{sd}", shape={}, hand=sd, hand_R=Rp, off=(0, 0, -0.14))
              for sd in "LR"]
        return c.stand(c.feet(w=c.hw * 1.1, toe=8), hk=0.99, arms=arms, equip=eq, load=0.2, balance="com")
    if "overhead" in (row.get("name_en") or "").lower() or "overhead" in n:
        # the bell locked out overhead in the right hand (the left arm hangs relaxed)
        hold = "kb_oh1" if "kettlebell" in n else "db_oh1"
        if "single" not in n and "one" not in (row.get("name_en") or "").lower():
            hold = "kb_oh" if "kettlebell" in n else "db_oh"
    return c.stand(legs, hk=None, pz=c.pz * 0.985, hold=hold, planted=(), load=0.3, balance="com")


# ================================================================ helpers TRX
def trx_straps(c, anchor=None, y=0.55):
    a = np.array([0, y, 2.4]) if anchor is None else anchor
    return [E("trx_anchor", a * [1, 1, 0], eid="trx", h=a[2]),
            seg("strapL", a, "gripL", 0.012, "strap"), seg("strapR", a, "gripR", 0.012, "strap")]


def trx_arms(c, reach=0.6):
    def tgt(D, Hp, c_, sd):
        sh = fam.shoulder(D, Hp, c, sd)
        return sh + Y * c.Lh * reach + Z * 0.05 + X * SIDES[sd] * -0.03
    return arm_ik(tgt, (-0.2, 0, 1), (0.5, -0.5, -1), curl=0.85)


@tpl("lying_leg_curl", "side")
def lying_leg_curl(c, t, L, row):
    n = eqw(row)
    pad_z = 0.64
    k = L(5, 110)

    def lg(sd):
        return dict(thigh=np.array([SIDES[sd] * 0.06, -1, -0.04]), knee=k, kbend=np.array([0, 0, 1]),
                    fdir=np.array([0, -0.3, -1]))
    arms = arm_ik(lambda D, Hp, c_, sd: np.array([SIDES[sd] * 0.12, 0.65, 0.8]), (-1, 0, 0), (0.4, -1, 0.6),
                  curl=0.9, fing=(0, 0, 1))
    if "band" in n and "ball" not in n:
        # prone on the mat, forehead on the folded forearms; one ankle curls
        # against a band running back to a low post behind the feet
        from .tpl_floor import MAT
        legs = {sd: dict(lg(sd), thigh=np.array([SIDES[sd] * 0.06, -1, -0.1]), fdir=np.array([0, -1.0, -0.3]))
                for sd in "LR"}
        legs["L"]["knee"] = 5
        arms = fam.arm_ik(lambda D, Hp, c_, sd: np.array([SIDES[sd] * 0.06, 0.74 * c.S, 0.075]), (0, 1, 0),
                          (1, -0.3, 0.25), key="palm", curl=0.2, fing=(-1, 0.3, 0))
        post_y = -1.3 * c.S        # a heavy kettlebell on the floor behind the feet holds the band

        def ank(pts, D, Hp, c_):
            return Hp[c.r.bi("foot.R")] + np.array([0.0, 0.0, 0.035])
        eq = [MAT(0.2), E("kettlebell", (0.14, post_y, 0.27), eid="lc_post"),
              seg("lc_band", np.array([0.14, post_y, 0.275]), ank, 0.007, "band")]
        return c.stand(legs, pz=0.15, pel=(90, 0, 0), arms=arms, neck=(-24, 0, 0), balance=None, reach=False,
                       equip=eq, settle=[("floor_part", c._region("noarms"), -0.002)], planted=())
    if "band" in n or "ball" in n:
        from .tpl_floor import MAT
        return c.stand({sd: lg(sd) for sd in "LR"}, pz=0.15, pel=(90, 0, 0), arms=fam.arm_fk((0.4, 0.8, -0.3), elbow=100),
                       balance=None, reach=False, equip=[MAT(0.2)], settle=[("floor", -0.002)], planted=())
    eq = [E("lying_curl", (0, 0, 0), eid="lc")]
    sup = [("plane", np.array([0, 0.15, pad_z]), Z, X, 0.16, Y, 0.55, PAD_SINK)]
    return c.stand({sd: lg(sd) for sd in "LR"}, pz=pad_z + 0.12, py=-0.05, pel=(88, 0, 0), spine=(-6, 0, 0),
                   neck=(-20, 0, 0), arms=arms, balance=None, reach=False, equip=eq, settle=sup, planted=())
