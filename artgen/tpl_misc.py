"""Other templates: hanging, dips, burpees, cardio machines, kettlebell and
olympic lifts, battle ropes, medicine balls, tire, stretches, yoga."""
from .templates import tpl, E, H, seg, PLATE_R, X, Y, Z, np, math, SIDES
from .poses import SOLE, PAD_SINK, SKIN_FLOOR
from .rig import unit, orth, rot, body_rot
from . import fam
from .fam import arm_fk, arm_ik, legs_fk, BENCH_H, press_bar, press_db
from .tpl_lower import eqw, has, platform, squat_hold, trx_straps, trx_arms, band_to_feet
from .tpl_floor import quadruped, kneeling, supine_knees, MAT, pike


# ================================================================== hanging
@tpl("pull_up", "back3q")
def pull_up(c, t, L, row):
    n = eqw(row)
    grip = "sup" if "chin" in n or "reverse" in n else ("neutral" if "neutral" in n or "v-bar" in n else "pro")
    gw = c.sw * (1.0 if grip == "sup" else (0.55 if grip == "neutral" else (1.85 if "wide" in n else 1.5)))
    pull = L(0, 1)
    if "dead hang" in n:
        pull = 0.0
    if "scapular" in n:
        pull = L(0, 0.08)
    if "muscle up" in n:
        pull = L(0, 1.15)
    if "negative" in n:
        pull = L(1, 0)
    legs = legs_fk((0.06, L(0.05, 0.12), -1), knee=L(15, 40), kbend=(0, -1, 0), fdir=(0, 0.4, -1))
    eq = []
    if "band" in n:
        # knees in front of the body, shins down: the band looped on the bar (overlay)
        # hangs in front of the chest to the loop under the knees
        legs = legs_fk((0.06, L(0.6, 0.65), -0.8), knee=L(80, 85), kbend=(0, -1, 0), fdir=(0, 0.1, -1))
    if "rope climb" in n:
        rope = np.array([0, 0.08, 0])
        eq = [seg("rope", rope + np.array([0, 0, 0.02]), rope + np.array([0, 0, 3.4]), 0.018, "rope")]
        arms = {"R": arm_ik(lambda D, Hp, c_, sd: rope + np.array([0, 0, L(2.35, 2.55) * c.S]), (0, 0, 1), (1, 0, -1),
                            curl=0.9, sides="R")["R"],
                "L": arm_ik(lambda D, Hp, c_, sd: rope + np.array([0, 0, L(2.05, 1.95) * c.S]), (0, 0, 1),
                            (1, 0, -1), curl=0.9, sides="L")["L"]}
        fr = c.stand(legs_fk((0.1, 0.5, -0.8), knee=80), pz=1.4 * c.S, py=-0.15, arms=arms, balance=None,
                     reach=False, equip=eq, planted=())
        fr.cons.append(("reach_arms", Z, ["L", "R"]))
        return fr
    if "archer" in n:
        gw = c.sw * 2.4
    if "australian" in n or "inverted" in n:
        from .tpl_upper import inverted_row
        return inverted_row(c, t, L, row)
    return fam.hang(c, pull=pull, gw=gw, grip=grip, legs=legs, extra_eq=eq,
                    spine=(L(0, -6), 0, 0), neck=(L(0, -15), 0, 0))


@tpl("hanging_leg_raise", (65, 6))
def hanging_leg_raise(c, t, L, row):
    n = eqw(row)
    knee = "knee" in n
    toes = "toes to bar" in n
    a = math.radians(L(5, 95 if not knee else 100))
    th = (0.06, math.sin(a), -math.cos(a))
    legs = legs_fk(th, knee=L(10, 90) if knee else 8, kbend=(0, -1, 0))
    tw = 0.0
    if "oblique" in n or "windshield" in n:
        tw = 30.0
    if toes:
        legs = legs_fk((0.06, math.sin(math.radians(L(5, 150))), -math.cos(math.radians(L(5, 150)))), knee=8,
                       kbend=(0, -1, 0))
    if "vertical" in n or "captain" in n:
        return captain_chair(c, t, L, row)
    return fam.hang(c, pull=0.0 if not toes else L(0, 0.2), legs=legs, pel=(0, 0, L(0, tw)),
                    spine=(L(0, 25 if not toes else 35), 0, 0))


def captain_chair(c, t, L, row):
    """Vertical knee/leg raise on dip-station forearm pads."""
    knee = "knee" in eqw(row)
    a = math.radians(L(5, 112 if knee else 92))
    legs = legs_fk((0.06, math.sin(a), -math.cos(a)), knee=L(10, 110) if knee else 6,
                   kbend=(0, -math.cos(a), -math.sin(a)))     # shin folds under the thigh at every angle
    arms = {sd: (lambda D, Hp, c_, sd=sd: dict(ua=-Z * 1 + Y * 0.05, elbow=90, bend=Y, thumb=Z, curl=0.85))
            for sd in "LR"}
    h = 1.62 * c.S           # forearm pads: the legs hang clearly above the floor and the foot steps
    fr = c.stand(legs, pz=h - 0.22 * c.S, py=-0.05, arms=arms, balance=None, reach=False, planted=(),
                 equip=[dict(E("captain_station", (0, 0.0, 0), eid="cc", height=h), fit=True)], spine=(L(0, 10), 0, 0),
                 settle=[("plane", np.array([0, -0.165, h - 0.1]), Y, X, 0.15, Z, 0.25, -0.004)])
    return fr


@tpl("l_sit", (70, 8))
def l_sit(c, t, L, row):
    h = 1.2 * c.S
    gap = 0.5
    legs = legs_fk((0.05, 1.0, L(-0.3, 0.05)), knee=4, kbend=(0, -1, 0))
    arms = arm_ik(lambda D, Hp, c_, sd: np.array([SIDES[sd] * gap / 2, 0.0, h]), (0, 1, 0), (0.2, -1, 0.0),
                  curl=0.9, fing=(0, 0, -1))
    fr = c.stand(legs, pz=h - 0.35 * c.S, py=-0.06, pel=(-8, 0, 0), arms=arms, balance=None, reach=False,
                 planted=(), equip=[E("dip_station", (0, 0, 0), eid="dip", height=h, gap=gap)])
    fr.cons.append(("reach_arms", Z, ["L", "R"]))
    return fr


@tpl("dip", (75, 8))
def dip(c, t, L, row):
    n = eqw(row)
    if "bench" in n or "chair" in n:
        return bench_dip(c, t, L, row)
    if "machine" in n and "assisted" not in n:
        from .tpl_upper import triceps_pushdown
        return triceps_pushdown(c, t, L, row)
    h = 1.25 * c.S
    gap = 0.52 * (c.S if c.g == "m" else 0.9)
    down = L(0, 1)
    arms = arm_ik(lambda D, Hp, c_, sd: np.array([SIDES[sd] * gap / 2, 0.0, h]), (0, 1, 0),
                  (0.25, -1, 0.0) if "chest" not in n else (0.6, -1, 0.0), curl=0.9, fing=(0, 0, -1))
    sh_drop = c.Lh * 0.97 * (1 - down) + 0.08 * down
    sh_r = c.r.joint("upperarm01.R")
    pitch = L(4, 22 if "chest" in n else 10)
    R = body_rot(pitch, 0, 0)
    pz = h + sh_drop - 0.04 - (R @ (sh_r - c.r.pc_rest))[2] - 0.28 * 0
    pz = h - sh_drop * 0 + 0.0
    legs = legs_fk((0.05, -0.3, -1), knee=85, kbend=(0, -1, 0), fdir=(0, 0.2, -1))
    eq = [E("dip_station", (0, 0, 0), eid="dip", height=h, gap=gap)]
    if "ring" in n:
        eq = [seg("ringL", np.array([-gap / 2, 0, 2.6]), np.array([-gap / 2, 0, h + 0.08]), 0.012, "strap"),
              seg("ringR", np.array([gap / 2, 0, 2.6]), np.array([gap / 2, 0, h + 0.08]), 0.012, "strap")]
    if "assisted" in n:     # knees rest on the assistance pad that rises and falls with them
        eq.append(dict(kind="knee_pad", M=np.eye(4), id="kpad", shape={}, bone="lowerleg01.R",
                       bone_pt=c.r.joint("lowerleg01.R") * np.array([0, 1, 1]) + np.array([0, 0.0, -0.06])))
    fr = c.stand(legs, pz=h - 0.5 * c.S - sh_drop * 0.0, py=-0.03, pel=(pitch, 0, 0), arms=arms, balance=None,
                 reach=False, planted=(), equip=eq)
    # shoulders sit sh_drop above the bars at the top, just above at the bottom
    bot = 0.13 if "chest" in n else 0.07
    fr.cons.append(("joint", "upperarm01.R", 2, h + (c.Lh * 0.95 - bot) * (1 - down) + bot * down))
    return fr


def bench_dip(c, t, L, row):
    by = -0.12
    down = L(0, 1)
    edge = by + 0.58
    arms = arm_ik(lambda D, Hp, c_, sd: np.array([SIDES[sd] * 0.2 * c.S, by + 0.5, BENCH_H + 0.03]), (0, 1, 0),
                  (0, -1, 0.1), curl=0.9, fing=(0, 1, -0.5))
    legs = {sd: dict(ankle=np.array([SIDES[sd] * 0.12, edge + 0.95 * c.S, 0.075]), fdir=np.array([0, 0.3, 1]),
                     fup=np.array([0, -1, 0.1]), pole=np.array([0, 0.3, 1])) for sd in "LR"}
    if "wall sit" in eqw(row):
        pass
    fr = c.stand(legs, pz=BENCH_H - 0.05 - 0.25 * down, py=edge + 0.12, pel=(-6, 0, 0), arms=arms, balance=None,
                 reach=False, planted=(), equip=[E("bench", (0, by, 0), R=fam.rz(90), eid="bench")])
    fr.cons.append(("reach_arms", Z, ["L", "R"]))
    return fr


# ================================================================== burpee
@tpl("burpee", (70, 10))
def burpee(c, t, L, row):
    """Squat-thrust: crouch with hands on the floor -> feet jumped back to a
    plank (hands stay planted)."""
    return pike(c, t, L, row, dist=L(0.5, 1.38) * c.S, hip_h=L(0.55, 0.6) * c.S, heel=L(35, 70))


# ================================================================== cardio
@tpl("treadmill_run", (80, 8))
def treadmill_run(c, t, L, row):
    s = math.cos(2 * math.pi * t)        # one full stride per loop (periodic)
    legs = {"R": dict(thigh=np.array([0.05, 0.6 * s, -1]), knee=20 + 70 * max(0, -s), kbend=np.array([0, -1, 0])),
            "L": dict(thigh=np.array([-0.05, -0.6 * s, -1]), knee=20 + 70 * max(0, s), kbend=np.array([0, -1, 0]))}
    arms = {"R": arm_fk((0.1, -0.5 * s, -0.8), elbow=90, sides="R")["R"],
            "L": arm_fk((0.1, 0.5 * s, -0.8), elbow=90, sides="L")["L"]}
    fr = c.stand(legs, pz=c.pz * 0.97 + 0.1, pel=(8, 0, 0), arms=arms, balance=None, reach=False, planted=(),
                 equip=[E("treadmill", (0, 0.0, 0), eid="tm")], settle=[("floor", 0.1 + 0.005)])
    return fr


@tpl("bike", "side")
def bike(c, t, L, row):
    crank = np.array([0, 0.3, 0.42])
    a = 2 * math.pi * t                  # one crank turn per loop (periodic)
    seat = np.array([0, -0.2, 0.93])
    legs = {}
    for sd, ph in (("R", a), ("L", a + math.pi)):
        p = crank + np.array([SIDES[sd] * 0.12, 0.17 * math.cos(ph), 0.17 * math.sin(ph)])
        legs[sd] = dict(ankle=p + np.array([0, -0.08, 0.07]), fdir=np.array([0, 1, -0.2]),
                        pole=np.array([SIDES[sd] * 0.1, 1, 0.3]))
    arms = arm_ik(lambda D, Hp, c_, sd: np.array([SIDES[sd] * 0.2, 0.32, 1.05]), (0, 0, 1), (0.3, -1, -0.5),
                  curl=0.9)
    return c.stand(legs, pz=seat[2] + 0.1, py=seat[1], pel=(25, 0, 0), arms=arms, balance=None, reach=False,
                   planted=(), equip=[E("bike", (0, 0, 0), eid="bike")],
                   settle=[("plane", seat + np.array([0, 0, 0.03]), Z, X, 0.1, Y, 0.14, PAD_SINK, "pelvis")])


@tpl("rower", "side")
def rower(c, t, L, row):
    seat_y = L(0.25, -0.35)
    seat = np.array([0, seat_y, 0.43])
    foot = np.array([0, 0.85, 0.25])

    def hand(D, Hp, c_, sd):
        m = fam.sh_mid(D, Hp, c)
        far = np.array([0, 0.72, 0.55])
        near = c.lmk(D, Hp, "chest") - Z * 0.1 + Y * 0.04
        return far * (1 - L(0, 1)) + near * L(0, 1) + X * SIDES[sd] * 0.1
    arms = arm_ik(hand, (0, 0, 1), (0.4, -1, 0.2), curl=0.9)
    legs = {sd: dict(ankle=foot + np.array([SIDES[sd] * 0.11, -0.04, 0.06]), fdir=np.array([0, 0.5, 0.86]),
                     fup=np.array([0, -0.86, 0.5]), pole=np.array([SIDES[sd] * 0.1, 0.2, 1])) for sd in "LR"}
    eq = [E("rower", (0, 0, 0), eid="rw"), seg("chain", np.array([0, 1.0, 0.45]), "gripC", 0.005, "darksteel")]
    return c.stand(legs, pz=0.55, py=seat_y, pel=(L(28, -25), 0, 0), arms=arms, balance=None, reach=False,
                   planted=(), equip=eq,
                   settle=[("plane", seat, Z, X, 0.15, Y, 0.15, PAD_SINK)])


@tpl("elliptical", (70, 8))
def elliptical(c, t, L, row):
    s = L(1, -1)
    base = np.array([0, 0.0, 0.32])
    legs = {sd: dict(ball=base + np.array([SIDES[sd] * 0.12, 0.25 * s * SIDES[sd], 0.06 * s * SIDES[sd] + 0.04]),
                     yaw=0, heel=8) for sd in "LR"}
    def hand(D, Hp, c_, sd):
        sh = fam.shoulder(D, Hp, c, sd)
        return fam.within(c, sh, np.array([SIDES[sd] * 0.05, 0.36 - 0.13 * s * SIDES[sd], -0.3]), 0.85)
    arms = arm_ik(hand, (0, 0, 1), (0.4, -1, -0.3), curl=0.9)
    eq = [E("elliptical", (0, 0.1, 0), eid="el")]
    for sd in "LR":     # moving handle arms: pivot low in front, up through the grip
        eq.append(seg(f"elh{sd}", np.array([SIDES[sd] * 0.22, 0.95, 0.55]), f"grip{sd}", 0.02, "frame"))
    return c.stand(legs, hk=None, pz=c.pz * 0.97 + 0.36, pel=(6, 0, 0), arms=arms, balance=None,
                   equip=eq, planted=())


# ================================================================ kettlebell / olympic
@tpl("kb_clean", (55, 8))
def kb_clean(c, t, L, row):
    n = eqw(row)
    snatch = "snatch" in n
    jerk_ = "jerk" in n or "and press" in n or "to press" in n
    legs = c.feet(w=c.hw * 1.6, toe=18)
    single = "single" in n or "kettlebell" in n and "double" not in n and "dual" not in n
    sides = "R" if single else "LR"

    def tgt(D, Hp, c_, sd):
        m = fam.shoulder(D, Hp, c, sd)
        lo = c.J(D, Hp, "root") * np.array([1, 1, 0]) + np.array([SIDES[sd] * 0.05, 0.05, c.z_hip * 0.55])
        if snatch:
            hi = m + Z * c.Lh * 0.95
        else:
            hi = m + Y * 0.13 - Z * 0.07          # rack: fist in front of the shoulder, bell on the forearm
        u = L(0, 1)
        if jerk_ and not snatch:          # clean to the rack, then drive it overhead
            if u < 0.6:
                p = lo * (1 - u / 0.6) + hi * (u / 0.6)
            else:
                w = (u - 0.6) / 0.4
                p = hi * (1 - w) + (m + Z * c.Lh * 0.95) * w
        else:
            p = lo * (1 - u) + hi * u
        d = p - m
        return m + unit(d) * min(np.linalg.norm(d), c.Lh * 0.96)       # always within reach

    def fing(D, Hp, c_, sd):     # fingers turn from down to up through forward (no flip)
        a = math.pi * L(0, 1)
        return unit(-Z * math.cos(a) + Y * math.sin(a) * 0.9 + 1e-6 * Y)
    arms = arm_ik(tgt, (0, 1, 0), (1, -0.5, -0.3), curl=0.9, sides=sides, fing=fing)
    if single:
        arms.update(arm_fk((0.3, 0.1, -1), elbow=12, sides="L"))
    kind = "kettlebell" if "kettlebell" in n else "dumbbell"
    # the bell stays on the back of the forearm side of the fist the whole way (racks without a jump)
    eq = [H(kind, sd, "kb") if kind == "kettlebell" else H("dumbbell", sd) for sd in sides]
    return c.stand(legs, hk=L(0.82, 0.92 if not snatch else 0.95), pel=(L(48, 2), 0, 0), arms=arms, equip=eq,
                   balance="com", load=0.15, neck=(L(-25, 0), 0, 0))


@tpl("power_clean", (55, 8))
def power_clean(c, t, L, row):
    """Barbell from the hang/floor to the front rack (or overhead for
    snatch/jerk variants)."""
    n = eqw(row)
    snatch = "snatch" in n
    jerk = "jerk" in n or "press" in n
    high_pull = "high pull" in n or "pull" in n and "high" in n
    legs = c.feet(w=c.hw * 1.2, toe=12)
    if snatch:
        h1, h2 = ("bar_hang_wide", dict(arm_ang=-4)), "oh_bar"
    elif jerk:
        h1, h2 = "front_bar", ("oh_bar_n", {})
    elif high_pull:
        h1, h2 = ("bar_hang", dict(arm_ang=-4)), None
    else:
        h1, h2 = ("bar_hang", dict(arm_ang=-4)), "front_bar"
    if "pvc" in n:
        h1 = ("pvc_hang", dict(arm_ang=-4)) if not jerk else h1
        h2 = "oh_pvc" if snatch or jerk else h2
    if high_pull:
        def tgt(D, Hp, c_, sd):
            m = fam.sh_mid(D, Hp, c)
            lo = m - Z * c.Lh * 0.97
            hi = c.lmk(D, Hp, "front_rack") + Z * 0.04 + Y * 0.05
            return lo * (1 - L(0, 1)) + hi * L(0, 1) + X * SIDES[sd] * c.sw * 0.55
        kb = "kettlebell" in n
        if kb:          # one kettlebell held by the handle in both hands, feet wide (sumo)
            legs = c.feet(w=c.hw * 2.2, toe=30)

            def tgt(D, Hp, c_, sd):
                m = fam.sh_mid(D, Hp, c)
                lo = m - Z * c.Lh * 0.95
                hi = c.lmk(D, Hp, "chest_hi") + Y * 0.08
                return lo * (1 - L(0, 1)) + hi * L(0, 1) + X * SIDES[sd] * 0.045
        arms = arm_ik(tgt, (-1, 0, 0), (1, -0.3, 0.8), curl=0.9, fing=(0, 0, -1))
        eq = [H("kettlebell", "C", "kb", eid="kb")] if kb else [H("barbell", "C", "bar", eid="bar")]
        return c.stand(legs, hk=L(0.8 if kb else 0.88, 0.99), pel=(L(25, -2), 0, 0), arms=arms,
                       equip=eq, neck=(L(-15, 0), 0, 0))
    if jerk:
        dip = 0.06 * math.sin(math.pi * min(1, t * 1.5))
        split = "split" in n
        if split:
            legs = c.feet(w=c.hw * 1.2, toe=10, split=L(0, 0.7))
            for sd in legs:
                legs[sd]["heel"] = 0 if sd == "R" else L(0, 50)
        return c.stand(legs, hk=0.985 - dip - (L(0, 0.12) if split else 0), pel=(0, 0, 0), hold=h1, hold2=h2,
                       mix=L(0, 1), load=0.4, planted=() if split else ("L", "R"))
    catch = 0.62 if "squat" in n or snatch and "power" not in n else 0.86
    return c.stand(legs, hk=L(0.88, catch), pel=(L(25, 16 if catch > 0.8 else 24), 0, 0), hold=h1, hold2=h2,
                   mix=L(0, 1), load=0.4, neck=(L(-15, -5), 0, 0))


@tpl("turkish_get_up", (35, 12))
def turkish_get_up(c, t, L, row):
    """Supine with the bell pressed up -> seated on the left elbow/hand."""
    legs = {"R": dict(ball=np.array([0.15, 0.55 * c.S, SOLE]), yaw=10, heel=0, pole=np.array([0.3, 0.2, 1])),
            "L": dict(thigh=np.array([-0.25, 1.0, L(0.05, 0.15)]), knee=5, kbend=np.array([0, 0, -1]))}
    arms = {"R": lambda D, Hp, c_: dict(grip=fam.shoulder(D, Hp, c, "R") + Z * c.Lh * 0.97, thumb=Y, fing=Z,
                                        pole=-Z + X * 0.5, curl=0.9),
            "L": lambda D, Hp, c_: dict(palm=np.array([-0.45 * c.S, L(-0.15, 0.05), 0.004]), thumb=Y, fing=-X + Y * 0.3,
                                        pole=Z + Y * 0.2, curl=0.05)}
    return fam.floor_body(c, pitch=L(-90, -35), roll=L(0, -18), legs=legs, arms=arms, spine=(L(0, 10), L(0, -10), 0),
                          equip=[MAT(0.1), H("kettlebell", "R", "kb_up")])


@tpl("kb_windmill", "front")
def kb_windmill(c, t, L, row):
    legs = c.feet(w=c.hw * 1.8, toe=0)
    legs["L"]["yaw"] = 45
    arms = {"R": lambda D, Hp, c_: dict(grip=fam.shoulder(D, Hp, c, "R") + (D[c.r.bi("spine01")] @ Z) * c.Lh * 0.97
                                        if False else fam.shoulder(D, Hp, c, "R") + Z * c.Lh * 0.97,
                                        thumb=-X * 0 + Y, fing=Z, pole=-Z + Y * 0.2, curl=0.9),
            "L": arm_fk((0.0, 0.0, -1), elbow=5, thumb="fwd", world=True, sides="L")["L"]}
    eq = [H("kettlebell", "R", "kb_up")] if "kettlebell" in eqw(row) else []
    if "pvc" in eqw(row) or not eq:
        arms["R"] = arm_fk((0.0, 0.0, 1.0), elbow=5, world=True, sides="R")["R"]
    return c.stand(legs, hk=0.97, px=L(0, 0.08), pel=(L(2, 30), L(0, -25), L(0, -40)), spine=(L(0, 20), L(0, -25), 0),
                   arms=arms, equip=eq, balance="com")


@tpl("kb_halo", "front3q")
def kb_halo(c, t, L, row):
    a = 2 * math.pi * t
    legs = c.feet(w=c.hw * 1.3)

    def tgt(D, Hp, c_, sd):
        hd = c.lmk(D, Hp, "head_top") - Z * 0.1
        return hd + np.array([0.18 * math.sin(a), 0.18 * math.cos(a) - 0.0, 0.0]) + X * SIDES[sd] * 0.03
    def pole(D, Hp, c_, sd):    # elbows out to the side and away from where the bell is
        return unit(np.array([SIDES[sd] * 0.8, 0, -0.4]) - np.array([math.sin(a), math.cos(a), 0]) * 0.45)
    arms = arm_ik(tgt, (0, 0, 1), pole, curl=0.9)
    eq = [H("kettlebell", "C", "kb_up", eid="kb")]
    if "plate" in eqw(row):
        eq = [H("plate_held", "C", "ball", eid="pl")]
    if "dumbbell" in eqw(row):
        eq = [H("dumbbell", "C", "vert", eid="db")]
    return c.stand(legs, arms=arms, equip=eq)


@tpl("thruster", (55, 8))
def thruster(c, t, L, row):
    n = eqw(row)
    legs = c.feet(w=c.hw * 1.3 + 0.08, toe=22)
    legs, peq = platform(c, row, legs)
    if "dumbbell" in n:
        h1, h2 = "db_shoulder", "db_oh"
    elif "kettlebell" in n:
        h1, h2 = "kb_rack", "kb_oh"
    elif "medicine" in n or "wall ball" in n:
        h1, h2 = "medball", None
    elif "band" in n:
        h1, h2 = "band_sh", None
    elif "landmine" in n:
        h1, h2 = "landmine", None
    else:
        h1, h2 = "front_bar", ("oh_bar_n", {})
    # squat at the start, stand + press at the end
    extra = []
    if "band" in n:
        extra = band_to_feet(c, legs)
        arms, _ = press_db(c, 0.08 + 0.92 * L(0, 1), "oh", w0=c.sw * 1.4, w1=c.sw * 1.0)   # rack not folded shut
        return c.stand(legs, hk=L(0.58, 0.99), pel=(L(32, 0), 0, 0), arms=arms, equip=extra + peq)
    if h1 == "medball":
        def tgt(D, Hp, c_, sd):
            lo = c.lmk(D, Hp, "goblet") + Y * 0.04
            hi = fam.sh_mid(D, Hp, c) + Z * c.Lp * 0.9 + Y * 0.1
            return lo * (1 - L(0, 1)) + hi * L(0, 1) + X * SIDES[sd] * 0.12
        arms = arm_ik(tgt, (0, 0, 1), (1, -0.5, -0.5), key="palm", curl=0.2, fing=(0, 0.3, 1))
        eq = [H("medball", "C", "ball", eid="mb", off=(0, 0, 0))]
        if "wall" in n:
            eq.append(E("wall", (0, 0.9, 0), R=fam.rz(180), eid="wall"))
        return c.stand(legs, hk=L(0.56, 0.99), pel=(L(30, 0), 0, 0), arms=arms, equip=eq + peq, load=0.1)
    if h1 == "landmine":
        from .tpl_upper import landmine_press
        return landmine_press(c, t, L, row)
    return c.stand(legs, hk=L(0.57, 0.99), pel=(L(30, 0), 0, 0), hold=h1, hold2=h2, mix=L(0, 1), load=0.4,
                   equip=peq)


@tpl("battle_ropes", (40, 10))
def battle_ropes(c, t, L, row):
    n = eqw(row)
    legs = c.feet(w=c.hw * 1.6, toe=15)
    alt = "slam" not in n and "outside" not in n
    anchor = np.array([0, 3.2, 0.12])

    def tgt(D, Hp, c_, sd):
        m = fam.shoulder(D, Hp, c, sd)
        up = L(0, 1) if (not alt or sd == "R") else L(1, 0)
        return m + Y * 0.42 + Z * (-0.45 + 0.55 * up) + X * SIDES[sd] * 0.05
    arms = arm_ik(tgt, (0, 0, 1), (1, -0.6, -0.4), curl=0.9)
    eq = [E("battle_rope_anchor", anchor, eid="anch")]
    for sd in "LR":
        pts = []
        for k in range(9):
            u = k / 8
            amp = 0.12 * math.sin(u * math.pi * 3 + t * math.pi * 2 + (0 if sd == "R" else math.pi)) * (1 - u)
            pts.append(u)
        eq.append(seg(f"rope{sd}", f"grip{sd}", anchor + np.array([SIDES[sd] * 0.05, 0, 0]), 0.018, "rope"))
    return c.stand(legs, hk=0.82, pel=(22, 0, 0), arms=arms, equip=eq, neck=(-10, 0, 0))


@tpl("medball_slam", (50, 8))
def medball_slam(c, t, L, row):
    legs = c.feet(w=c.hw * 1.4, toe=12)

    def tgt(D, Hp, c_, sd):
        hi = fam.sh_mid(D, Hp, c) + Z * c.Lp * 0.9 + Y * 0.05
        lo = fam.within(c, fam.sh_mid(D, Hp, c), np.array([0, 0.3, -0.52]), 0.82)
        return hi * (1 - L(0, 1)) + lo * L(0, 1) + X * SIDES[sd] * 0.12
    u = L(0, 1)
    fz = 1 - 2 * u           # fingers swing from up (overhead) to down (at the floor) with the arms
    arms = arm_ik(tgt, (0, fz, -0.3), (1, -0.5, -0.5), key="palm", curl=0.2, fing=(0, 0.3, fz))
    eq = [H("medball", "C", "ball", eid="mb")]
    if "chest pass" in eqw(row) or "toss" in eqw(row) or "throw" in eqw(row):
        def tgt2(D, Hp, c_, sd):
            a = c.lmk(D, Hp, "goblet") + Y * 0.05
            b = fam.sh_mid(D, Hp, c) + Y * c.Lp * 0.9 - Z * 0.08
            return a * (1 - L(0, 1)) + b * L(0, 1) + X * SIDES[sd] * 0.12
        arms = arm_ik(tgt2, (0, 0, 1), (1, -0.5, -0.5), key="palm", curl=0.2, fing=(0, 0.3, 1))
        return c.stand(c.feet(w=c.hw * 1.3, split=0.3), hk=0.95, pel=(8, 0, 0), arms=arms, equip=eq)
    return c.stand(legs, hk=L(0.99, 0.72), pel=(L(-5, 45), 0, 0), spine=(L(-5, 15), 0, 0), arms=arms, equip=eq,
                   balance="com")


@tpl("tire_flip", (55, 8))
def tire_flip(c, t, L, row):
    """Hands under the near lip of a flat tyre; drive up and forward so the
    tyre tips over its far edge (the far edge stays on the floor)."""
    legs = c.feet(w=c.hw * 1.5, toe=15)
    lift = L(0, 1)
    ang = 6 + 50 * lift          # the lip is first pried a hand-width off the floor
    R = fam.rx(-ang)
    near_y = 0.3 * c.S
    P = np.array([0, near_y + 1.34, 0.0])                # far bottom edge: the pivot
    tire_c = P + R @ np.array([0, -0.67, 0.17])

    def tgt(D, Hp, c_, sd):
        return P + R @ np.array([SIDES[sd] * 0.3, -1.25, 0.04])
    arms = arm_ik(tgt, (1, 0, 0), (1, -0.6, -0.4), curl=0.9,
                  fing=tuple(R @ np.array([0, 1, 0.5])))
    eq = [E("tire", tire_c, R=R, eid="tire", dyn=True)]
    return c.stand(legs, hk=L(0.47, 0.85), py=L(0.0, 0.25), pel=(L(70, 25), 0, 0), arms=arms, equip=eq, balance=None,
                   reach=True, neck=(-25, 0, 0))


# ================================================================== stretches
@tpl("standing_forward_bend", "side")
def standing_forward_bend(c, t, L, row):
    n = eqw(row)
    if "standing splits" in (row.get("name_en") or "").lower():
        # forward fold on the right leg, hands on the floor either side of the
        # foot; the left leg lifts straight back and up, hips kept square
        u = L(0.0, 1.0)
        b = math.radians(-86 + 166 * u)          # back leg from beside the standing leg to high behind
        legs = {"R": c.foot(0.0, 0.0, 6),
                "L": dict(thigh=unit(np.array([-0.04, -math.cos(b) * 0.98 - 0.03 * (1 - u), math.sin(b)])), knee=4,
                          kbend=np.array([0, 0, -1]),
                          fdir=np.array([0.0, math.cos(b + math.pi / 2), -math.sin(b + math.pi / 2)]))}   # foot turns with the leg

        def palm(D, Hp, c_, sd):
            return fam.floor_palm(c, D, Hp, sd, SIDES[sd] * 0.17 * c.S, 0.22 * c.S)
        arms = arm_ik(palm, (-1, 0.2, 0), (0.2, -1, 0.3), key="palm", curl=0.05, fing=(0, 1, 0))
        return c.stand(legs, hk=0.99, pel=(L(100, 118), 0, 0), spine=(L(36, 26), 0, 0), neck=(L(10, -6), 0, 0),
                       arms=arms, balance=None, planted=("R",))
    legs = c.feet(w=c.hw * (1.0 if "cross" not in n else 0.3), toe=4)
    if "wide" in n or "pancake" in n:
        legs = c.feet(w=c.hw * 3.0, toe=10)
    if "single leg" in n or "lunge" in n:
        legs = c.feet(w=c.hw * 1.0, split=0.55)
        legs["R"]["heel"] = -25
    arms = arm_fk((0.15, 0.25, -1), elbow=8, thumb="fwd", world=True)
    return c.stand(legs, hk=0.985, pel=(L(5, 75), 0, 0), spine=(L(0, 40), 0, 0), neck=(L(0, 25), 0, 0), arms=arms,
                   balance="com")


def straddle_fold(c, t, L, row, side=None):
    """Seated wide straddle, knees and toes up.  side None (pancake): the
    pelvis tips forward and the chest folds to the centre with a long back,
    hands walking forward on the floor.  side "R"/"L" (fan stretch): the
    trunk turns and folds over that leg, both hands reaching along it."""
    u = L(0.0, 1.0)
    legs = legs_fk((0.72, 1.0, 0.0), knee=3, kbend=(0, 0, -1), fdir=(0, 0.1, 1))
    if side is None:
        def tgt(D, Hp, c_, sd):
            sh = fam.shoulder(D, Hp, c, sd)
            p = np.array([SIDES[sd] * 0.2 * c.S, (0.32 + 0.3 * u) * c.S, 0.006])
            d = p - sh
            R = c.Lpf * 0.96
            if np.linalg.norm(d) > R:        # the hands stay where the arms reach
                p = sh + d / np.linalg.norm(d) * R
                p[2] = max(p[2], 0.006)
            return p
        arms = arm_ik(tgt, (0, 0, 1), (1, -0.4, 0.5), key="palm", curl=0.08, fing=(0, 1, 0))
        return fam.floor_body(c, pitch=L(-6, 40), legs=legs, arms=arms, spine=(L(0, 16), 0, 0), neck=(L(0, 6), 0, 0),
                              equip=[MAT(0.2)])
    s = SIDES[side]

    def tgt(D, Hp, c_, sd):
        a = c.J(D, Hp, f"foot.{side}")
        k = 0.5 * (c.J(D, Hp, f"lowerleg01.{side}") + c.J(D, Hp, f"upperleg02.{side}"))
        sh = fam.shoulder(D, Hp, c, sd)
        off = Z * 0.06 + (Y * 0.06 if sd == side else -Y * 0.04)

        def at(w):
            return k * (1 - w) + a * w + off
        w = 0.15 + 0.85 * u
        R = c.Lpf * 0.95
        if np.linalg.norm(at(w) - sh) > R:        # continuous: farthest reachable point along the leg
            lo, hi = 0.0, w
            for _ in range(20):
                mid = 0.5 * (lo + hi)
                if np.linalg.norm(at(mid) - sh) <= R:
                    lo = mid
                else:
                    hi = mid
            w = lo
        return at(w)
    arms = arm_ik(tgt, (0, 0, 1), (1, -0.4, 0.5), key="palm", curl=0.4, fing=(0, 1, -0.3))
    return fam.floor_body(c, pitch=L(-6, 22), yaw=s * L(0, 38), legs=legs, arms=arms,
                          spine=(L(0, 30), s * L(0, 12), s * L(0, 16)), neck=(L(0, 12), 0, 0), equip=[MAT(0.2)])


@tpl("seated_forward_bend", "side")
def seated_forward_bend(c, t, L, row):
    n = eqw(row)
    nm = (row.get("name_en") or "").lower()
    if nm == "pancake":
        return straddle_fold(c, t, L, row)
    if nm == "fan stretch":
        return straddle_fold(c, t, L, row, side=row.get("_side", "R"))
    wide = "pancake" in n or "straddle" in n or "fan" in n or "center split" in n
    spread = 0.55 if wide else 0.06
    legs = legs_fk((spread, 1.0, 0.0), knee=3, kbend=(0, 0, -1), fdir=(0, 0.1, 1))

    def tgt(D, Hp, c_, sd):
        a = c.J(D, Hp, f"foot.{sd}")
        k = 0.5 * (c.J(D, Hp, f"lowerleg01.{sd}") + c.J(D, Hp, f"upperleg02.{sd}"))     # from mid-thigh
        sh = fam.shoulder(D, Hp, c, sd)
        u = L(0, 1)
        # slide down the shin only as far as the arms reach (shorter athletes stop higher)
        for _ in range(12):
            p = k * (1 - u) + a * u + Z * 0.05
            if np.linalg.norm(p - sh) <= c.Lpf * 0.95 or u <= 0:
                break
            u -= 0.08
        return k * (1 - max(u, 0)) + a * max(u, 0) + Z * 0.05
    arms = arm_ik(tgt, (0, 0, 1), (1, -0.4, 0.5), key="palm", curl=0.4, fing=(0, 1, -0.3))
    return fam.floor_body(c, pitch=L(-5, 45), legs=legs, arms=arms, spine=(L(5, 35), 0, 0), neck=(L(0, 20), 0, 0),
                          equip=[MAT(0.2)])


@tpl("butt_scoot", (60, 10))
def butt_scoot(c, t, L, row):
    """Seated on the floor, legs long: one hip and knee drive forward while the
    other side pulls back, arms swinging like running (alternates each half)."""
    def leg(sd, a):           # a = 1: this side drives (knee bends, hip forward)
        s = SIDES[sd]
        return dict(thigh=np.array([s * 0.07, 1.0, 0.12 * a]), knee=5 + 40 * a, kbend=np.array([0, 0, -1]),
                    fdir=np.array([0, 0.15, 1]))
    legs = {"R": leg("R", L(1, 0)), "L": leg("L", L(0, 1))}
    arms = {"R": arm_fk((0.12, L(-0.55, 0.45), -0.8), elbow=90, bend=(0, 1, 0.2), thumb="in", sides="R")["R"],
            "L": arm_fk((0.12, L(0.45, -0.55), -0.8), elbow=90, bend=(0, 1, 0.2), thumb="in", sides="L")["L"]}
    return fam.floor_body(c, pitch=-8, yaw=L(8, -8), roll=L(3, -3), legs=legs, arms=arms, spine=(4, 0, L(-6, 6)),
                          equip=[MAT(0.2)])


def _knee_of(hip, ank, pole, a, b):
    """Knee of a two-bone leg from hip to ankle bending toward pole."""
    d = ank - hip
    n = np.linalg.norm(d)
    u_ = d / n
    n = min(n, a + b - 1e-4)
    along = (a * a - b * b + n * n) / (2 * n)
    h = math.sqrt(max(a * a - along * along, 0.0))
    return hip + u_ * along + unit(orth(pole, u_)) * h


def side_lying_groin(c, t, L, row):
    """Side-lying groin stretch: on the left side, head on the lower arm, the
    bottom leg long; the top foot stands on the mat in front of the bottom
    knee and the top hand draws that knee open toward the ceiling and back."""
    from .tpl_floor import side_lying
    op = math.radians(L(5.0, 70.0))
    fr = side_lying(c, {}, arms=None)
    b0 = fr.build

    def build():
        spec, eq, ex = b0()
        D, Hp = c.torso(spec)
        R0 = D[c.r.bi("root")]
        up, fwd, head = R0 @ X, R0 @ Y, R0 @ Z
        dmL, dmR = c.r.dims["L"], c.r.dims["R"]
        hipL, hipR = Hp[c.r.bi("upperleg01.L")], Hp[c.r.bi("upperleg01.R")]
        thL = unit(R0 @ np.array([-0.22, 0.12, -1.0]))
        legs = {"L": dict(thigh=thL, knee=6, kbend=R0 @ -Y, fdir=unit(fwd * 0.9 - head * 0.4))}
        kneeL = hipL + dmL["T1"] * thL
        ank = kneeL + fwd * 0.2 * c.S
        ank = ank - up * (float(ank @ Z) - 0.09) / max(float(up @ Z), 0.3)
        pole = unit(math.cos(op) * unit(fwd + head * 0.6) + math.sin(op) * up)
        legs["R"] = dict(ankle=ank, fdir=unit(fwd * 0.6 - head * 0.8), fup=unit(-up * 0.2 + fwd * 0.2 + head * 0.9), pole=pole)
        spec["leg"] = legs
        kR = _knee_of(hipR, ank, pole, dmR["T1"], dmR["T2"])
        spec["arm"] = {"L": dict(ua=unit(R0 @ np.array([-0.1, 0.1, 1.0])), elbow=110, bend=R0 @ np.array([1, 0.2, 0]),
                                 thumb=R0 @ Y, curl=0.3),
                       "R": dict(palm=hipR + L(0.72, 0.42) * (kR - hipR) + up * 0.07, thumb=head, fing=-up,
                                 pole=unit(-fwd + up * 0.3), curl=0.6)}
        return spec, eq, ex
    fr.build = build
    return fr


def frog_stretch(c, t, L, row):
    """Frog stretch: on the forearms, knees wide on the mat in line with the
    hips, knees bent 90 deg with the shins parallel behind, feet turned out;
    the hips rock back toward the heels."""
    u = L(0.0, 1.0)
    kx = 0.52 * c.S
    T1 = c.r.dims["R"]["T1"]
    pz = 0.17 - 0.03 * u
    py = -0.16 * u
    sz = c.r.dims["R"]["L1"] + 0.07
    sh_r = c.r.joint("upperarm01.R")
    d = np.linalg.norm((sh_r - c.r.pc_rest)[[1, 2]])
    pitch = 90 - math.degrees(math.asin(max(-0.9, min(0.9, (sz - pz) / d))))
    legs = {sd: dict(ankle=np.array([SIDES[sd] * kx, -0.42 * c.S, 0.075]), fdir=np.array([SIDES[sd] * 1.0, -0.15, 0.0]),
                     fup=np.array([0.0, 1.0, 0.3]), pole=np.array([SIDES[sd] * 1.0, 0.25, -0.6])) for sd in "LR"}
    arms = {sd: (lambda D, Hp, c_: dict(ua=unit(np.array([0.0, 0.08, -1.0])), elbow=88, bend=Y, thumb=Z, curl=0.3,
                                        fing=Y)) for sd in "LR"}
    from .tpl_floor import MAT as _MAT
    return c.stand(legs, pz=pz, py=py, pel=(pitch, 0, 0), spine=(L(0, 6), 0, 0), neck=(-12, 0, 0), arms=arms,
                   balance=None, reach=False, equip=[_MAT(0.0)], settle=[("floor", SKIN_FLOOR)], planted=())


@tpl("butterfly_stretch", "front3q")
def butterfly_stretch(c, t, L, row):
    n = eqw(row)
    frog = "frog" in n
    if frog:
        return frog_stretch(c, t, L, row)
    if "side_lying" in n or "side-lying" in n:
        return side_lying_groin(c, t, L, row)
    # soles together in front of the groin, knees falling out to the sides
    legs = {sd: dict(ankle=np.array([SIDES[sd] * 0.07, 0.36 * c.S, 0.1]), pole=np.array([SIDES[sd] * 1.0, 0.3, L(0.5, 0.15)]),
                     fdir=np.array([0, 1.0, 0.2]), fup=np.array([SIDES[sd] * 1.0, 0, 0.4])) for sd in "LR"}
    arms = arm_ik(lambda D, Hp, c_, sd: (c.J(D, Hp, "foot.L") + c.J(D, Hp, "foot.R")) / 2 + X * SIDES[sd] * 0.05 + Z * 0.05
                  + Y * 0.05, (0, 1, 0), (1, -0.3, 0.2), curl=0.85)
    return fam.floor_body(c, pitch=L(-5, 20), legs=legs, arms=arms, spine=(L(5, 20), 0, 0), equip=[MAT(0.2)])


@tpl("hip_flexor_stretch", (85, 8))
def hip_flexor_stretch(c, t, L, row):
    n = eqw(row)
    if "standing" in n:
        legs = c.feet(w=c.hw * 1.1, split=0.85 * c.S)
        legs["L"]["heel"] = 60
        return c.stand(legs, hk=L(0.9, 0.8), pel=(L(2, -6), 0, 0), hold="hips", balance="com")
    if "couch" in n or "shin box" in n:
        pass
    return kneeling(c, t, L, row, half=True, pitch=L(2, -8), hold="hips", hk=None)


@tpl("pigeon_pose", (40, 14))
def pigeon_pose(c, t, L, row):
    legs = {"R": dict(thigh=np.array([0.15, 1.0, -0.15]), knee=110, kbend=np.array([-1, -0.3, 0]),
                      fdir=np.array([-1, 0.1, 0]), fup=np.array([0, -0.2, 1])),
            "L": dict(thigh=np.array([-0.1, -1.0, -0.15]), knee=5, kbend=np.array([0, 0, 1]),
                      fdir=np.array([0, -0.2, -1]) * -1, fup=np.array([0, -1, 0.2]))}
    if "90/90" in (row.get("name_en") or ""):
        return ninety_ninety(c, t, L, row)
    if "lying" in eqw(row) or "figure four" in eqw(row) or "seated" in eqw(row):
        return figure_four(c, t, L, row)
    arms = arm_ik(lambda D, Hp, c_, sd: fam.floor_palm(c, D, Hp, sd, SIDES[sd] * c.sw * 0.5, L(0.3, 0.7) * c.S), (-1, 0, 0), (0.2, -1, 0.5),
                  key="palm", curl=0.05, fing=(0, 1, 0))
    return fam.floor_body(c, pitch=L(40, 60), legs=legs, arms=arms, spine=(L(0, 20), 0, 0), equip=[MAT(0.2)])


def ninety_ninety(c, t, L, row):
    """Seated 90/90: the right leg in front (thigh forward, knee 90 deg, shin
    across the front on the mat), the left leg out to the side (thigh to the
    side, knee 90 deg, shin pointing back); sitting tall with the hands beside
    the hips, then a long-backed lean over the front shin."""
    u = L(0.0, 1.0)
    S_ = c.S
    legs = {"R": dict(ankle=np.array([-0.2 * S_, 0.46 * S_, 0.075]), pole=np.array([1.0, 0.7, -0.1]),
                      fdir=np.array([-1.0, 0.1, 0.0]), fup=np.array([0.0, 1.0, 0.25])),
            "L": dict(ankle=np.array([-0.56 * S_, -0.4 * S_, 0.075]), pole=np.array([-1.0, 0.25, -0.1]),
                      fdir=np.array([-0.1, -1.0, 0.0]), fup=np.array([-0.7, 0.0, 0.7]))}

    def palm(D, Hp, c_, sd):
        # hands rest on the front shin (knee / ankle), then walk forward on the mat as the chest leans over it
        dm = c.r.dims["R"]
        an = legs["R"]["ankle"]
        kn = _knee_of(c.J(D, Hp, "upperleg01.R"), an, legs["R"]["pole"], dm["T1"], dm["T2"])   # legs not solved yet
        on = (kn if sd == "R" else an) + Z * 0.07
        fwd = np.array([on[0] * 0.8, on[1] + 0.22 * c.S, 0.004])
        return on * (1 - u) + fwd * u
    arms = arm_ik(palm, (-1, 0, 0), (0.3, -1, 0.4), key="palm", curl=0.06, fing=(0, 1, 0.08))
    return fam.floor_body(c, pitch=L(-4, 32), yaw=L(0, 12), legs=legs, arms=arms, spine=(L(0, 10), 0, L(0, 6)),
                          neck=(L(0, 8), 0, 0), equip=[MAT(0.2)],
                          settle=[("floor_part", c._region("hips"), SKIN_FLOOR)])   # sit on the mat; feet are IK-pinned


def figure_four(c, t, L, row):
    if "seated" in (row.get("name_en") or "").lower():
        # on a chair: left ankle over the right knee, chest leans forward over the shin
        legs = {"R": dict(ball=np.array([0.12 * c.S, 0.5 * c.S, SOLE]), yaw=8, heel=0, pole=np.array([0.2, 1, 0.6])),
                "L": dict(thigh=unit(np.array([-0.55, 0.8, 0.12])), knee=105, kbend=np.array([1.0, 0.15, 0.0]),
                          fdir=np.array([0.3, 0.3, 1.0]))}
        arms = arm_ik(lambda D, Hp, c_, sd: c.J(D, Hp, "lowerleg01.L") + Z * 0.06 if sd == "L"
                      else c.J(D, Hp, "foot.L") + Z * 0.06, (0, 1, 0), (1, -0.3, -0.2), key="palm", curl=0.4,
                      fing=(0, 0.3, -1))
        return fam.seated(c, seat_h=0.46, seat_y=-0.1, pitch=L(5, 32), legs=legs, arms=arms, planted=("R",),
                          equip=[E("bench", (0, -0.15, 0), eid="chair", length=0.45)])
    legs = {"L": dict(ball=np.array([-0.15, 0.55 * c.S, SOLE]), yaw=4, heel=0, pole=np.array([0, 0.2, 1])),
            "R": dict(thigh=np.array([0.6, 0.4, 0.75]), knee=110, kbend=np.array([-1, 0, -0.2]),
                      fdir=np.array([-1, 0, 0.2]))}
    if t > 0.01:
        legs["L"] = legs_fk((-0.05, L(0.3, 0.55), L(0.95, 0.8)), knee=95, kbend=(0, 0, -1), sides="L")["L"]
    return supine_legs_wrap(c, legs)


def supine_legs_wrap(c, legs):
    from .tpl_floor import supine_legs
    return supine_legs(c, legs, arms=None, hold="none")


@tpl("knee_to_chest", "side_hi")
def knee_to_chest(c, t, L, row):
    legs = {"L": legs_fk((-0.05, 1.0, 0.05), knee=4, kbend=(0, 0, -1), sides="L")["L"],
            "R": legs_fk((0.08, L(-0.3, -0.62), L(0.95, 0.78)), knee=L(112, 135), kbend=(0, 1, -0.3), sides="R")["R"]}
    arms = arm_ik(lambda D, Hp, c_, sd: c.J(D, Hp, "lowerleg01.R") + Z * 0.06 - Y * 0.05 + X * SIDES[sd] * 0.05,
                  (0, 1, 0), (1, 0, 0.5), curl=0.85)
    from .tpl_floor import supine_legs
    return supine_legs(c, legs, arms=arms)


@tpl("quad_stretch_standing", (70, 8))
def quad_stretch_standing(c, t, L, row):
    legs = {"R": c.foot(c.hw * 0.25, 0, 6),
            "L": dict(thigh=np.array([-0.05, L(-0.05, -0.15), -1]), knee=L(60, 150), kbend=np.array([0, -1, 0]))}
    arms = {"L": lambda D, Hp, c_: dict(grip=c.J(D, Hp, "foot.L") + Z * 0.04 - Y * 0.04, thumb=Y, fing=-Z,
                                        pole=-Y + Z * 0.3, curl=0.8),
            "R": arm_fk((0.6, 0.1, 0.2), elbow=10, sides="R")["R"]}
    return c.stand(legs, hk=0.985, pel=(2, 0, 0), arms=arms, planted=("R",), balance="com")


@tpl("arm_stretch", "front3q")
def arm_stretch(c, t, L, row):
    """Cross-body shoulder / overhead triceps / wrist stretches."""
    n = eqw(row)
    legs = c.feet()

    def fk_point(arm_fn, which):
        """Where the FK right arm puts its elbow / hand (the torso solve does
        not pose the arms, so read it from the arm spec itself)."""
        def f(D, Hp):
            A = arm_fn(D, Hp, c)
            sh = c.J(D, Hp, "upperarm01.R")
            ua = unit(A["ua"])
            E_ = sh + c.r.dims["R"]["L1"] * ua
            if which == "elbow":
                return E_
            return c._hand_point(A, D, Hp, "R")[0]
        return f
    if "tricep" in n:
        arms = arm_fk((0.15, -0.1, 1.0), elbow=L(60, 150), bend=(0, -1, 0), thumb="fwd", sides="R")
        el = fk_point(arms["R"], "elbow")
        arms.update(arm_ik(lambda D, Hp, c_, sd: el(D, Hp) + Z * 0.05 - X * 0.03, (0, 1, 0),
                           (-1, 0.3, -0.2), key="palm", curl=0.3, sides="L"))
    elif "wrist" in n or "forearm" in n:
        arms = arm_fk((-0.55, 1.0, -0.25), elbow=14, thumb="in", sides="R",
                      fing=(0, L(0.2, 0.0), L(-0.4, -1.0)) if "extension" in n else (0, 0.3, L(0.3, 1.0)))
        hp = fk_point(arms["R"], "hand")
        arms.update(arm_ik(lambda D, Hp, c_, sd: hp(D, Hp) + Y * 0.02 + Z * 0.03, (0, 0, 1),
                           (-1, -0.5, -0.4), key="palm", curl=0.3, sides="L"))
    elif "chest" in n or "doorway" in n or "wall" in n or "pectoral" in n:
        arms = arm_fk((1.0, L(0.0, -0.4), 0.1), elbow=90, bend=(0, 0, 1), thumb="back")
        return c.stand(legs, arms=arms, pel=(L(0, 6), 0, 0))
    elif "overhead" in n or "side bend" in n or "lateral bend" in n or "helicopter" in n:
        arms = arm_fk((0.3, 0.05, 1.0), elbow=8, thumb="in")
        return c.stand(c.feet(w=c.hw * 1.5), pel=(0, L(0, 18), 0), spine=(0, L(0, 22), 0), arms=arms, balance="com")
    else:  # cross-body
        arms = arm_fk((L(0.3, -0.85), 1.0, 0.0), elbow=8, thumb="up", sides="R")
        el = fk_point(arms["R"], "elbow")
        arms.update(arm_ik(lambda D, Hp, c_, sd: el(D, Hp) + Y * 0.03 - X * 0.02, (0, 0, 1),
                           (-1, -0.6, -0.4), key="palm", curl=0.4, sides="L"))
    return c.stand(legs, arms=arms)


@tpl("arm_circles", "front3q")
def arm_circles(c, t, L, row):
    a = 2 * math.pi * t * (1 if "backward" not in eqw(row) else -1)
    legs = c.feet(w=c.hw * 1.2)
    arms = arm_fk((1.0, 0.25 * math.cos(a), 0.25 * math.sin(a)), elbow=5, thumb="fwd")
    return c.stand(legs, arms=arms)


@tpl("warrior_pose", "front")
def warrior_pose(c, t, L, row):
    w = 1.2 * c.S
    legs = {"L": c.foot(-w / 2, 0, 80), "R": c.foot(w / 2, 0, 5)}
    arms = arm_fk((1.0, 0.0, L(-0.6, 0.0)), elbow=5, thumb="up")
    return c.stand(legs, hk=L(0.9, 0.72), px=L(0, w * 0.15), pel=(0, 0, 0), arms=arms, balance="com",
                   wsupport=(1, 1), neck=(0, 0, L(0, 60)))


@tpl("tree_pose", "front")
def tree_pose(c, t, L, row):
    legs = {"R": c.foot(c.hw * 0.15, 0, 6),
            "L": dict(thigh=np.array([-0.9, 0.35, -0.5]), knee=130, kbend=np.array([0.6, -1, 0]),
                      fdir=np.array([0.8, 0, 0.3]))}
    arms = arm_fk((0.1, L(0.4, 0.05), L(-0.2, 1.0)), elbow=L(60, 10), thumb="in")
    return c.stand(legs, hk=0.985, arms=arms, planted=("R",), balance="com")


@tpl("calf_stretch", (75, 8))
def calf_stretch(c, t, L, row):
    legs = c.feet(w=c.hw * 1.0, split=0.7 * c.S)
    legs["R"]["heel"] = 0
    wall_y = 0.76 * c.S
    arms = arm_ik(lambda D, Hp, c_, sd: np.array([SIDES[sd] * 0.22, wall_y - 0.035, 1.3 * c.S]), (-1, 0, 0),
                  (0.4, -1, -0.3), key="palm", curl=0.0, fing=(0, 0.1, 1))
    fr = c.stand(legs, hk=L(0.98, 0.92), pel=(L(10, 20), 0, 0), arms=arms,
                 equip=[E("wall", (0, wall_y, 0), R=fam.rz(180), eid="wall")], balance=None)
    fr.cons.append(("reach_arms", Y, ["L", "R"]))     # lean in until the palms meet the wall
    return fr


@tpl("standing_still", "front3q")
def standing_still(c, t, L, row):
    """Breathing / vacuum / static holds."""
    legs = c.feet()
    return c.stand(legs, hold="hips", spine=(0, 0, 0), pel=(L(0, 2), 0, 0))
