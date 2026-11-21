"""5.4 drawings, second set: the last 41 exercises without a picture (new machines, a balance trainer held in
the hands, suspension straps on the floor, foam roller positions, and partner exercises with a second person).
Registered in the same x54 table as tpl_x54 (templates "x54" / "x54f")."""
from .templates import E, H, seg, X, Y, Z, np, math, SIDES, REG
from .equipment import rx
from .poses import SOLE, _bar_R
from .rig import unit
from . import fam
from .fam import arm_fk, arm_ik, legs_fk
from .tpl_v3 import keyed_stand, _interp
from .tpl_x54 import x, _keys, _with_eq, MATP, DOME, ARMS_RUN
from .tpl_floor import supine_legs, palms_floor, quadruped, MAT

PARTNER = {}


def partner(*keys):
    """Second person of a partner exercise: fn(c2, t, L, row) -> (frame, yaw_deg, offset); row["_main"] is the
    athlete's solved pose for the same phase (world positions; use local() to bring them into the partner's
    frame)."""
    def deco(fn):
        for k in keys:
            PARTNER[k] = fn
        return fn
    return deco


def _Rz(deg):
    a = math.radians(deg)
    return np.array([[math.cos(a), -math.sin(a), 0], [math.sin(a), math.cos(a), 0], [0, 0, 1.0]])


def local(p, yaw, off):
    """World point -> the partner's frame (before its yaw / offset)."""
    return _Rz(-yaw) @ (np.asarray(p, float) - np.asarray(off, float))


def joint(pose, c, name):
    return np.asarray(pose.Hp[c.r.bi(name)], float)


def partner_pose(c2, t, row, main, side, warm):
    from .templates import Tpl
    fn = PARTNER[row["key"]]
    r = {"key": row["key"], "name_en": "", "equipment": "", "_tempo": row.get("_tempo"), "_side": side, "_phase": t,
         "_main": main, "_view": row.get("_view")}
    box = {}

    def run(c, t_, L, rr):
        fr, yaw, off = fn(c, t_, L, rr)
        box["pl"] = (yaw, np.asarray(off, float))
        return fr
    p = Tpl("_partner", run).pose(c2, t, r, warm=warm)
    yaw, off = box["pl"]
    R = _Rz(yaw)
    p.verts = p.verts @ R.T + off
    p.Hp = p.Hp @ R.T + off
    p.D = np.einsum("ij,bjk->bik", R, p.D)
    T = np.eye(4)
    T[:3, :3] = R
    T[:3, 3] = off
    eq = []
    for e in p.equip:
        e = dict(e)
        e["id"] = "p_" + e["id"]
        if e["kind"] == "_seg":
            e["p0"] = R @ np.asarray(e["p0"], float) + off
            e["p1"] = R @ np.asarray(e["p1"], float) + off
        else:
            e["M"] = T @ np.asarray(e["M"], float)
        eq.append(e)
    p.equip = eq
    return p


# ================================================================== machines and bars
@x("safety-bar-squat")
def ssb_squat(c, t, L, row):
    """Safety squat bar on the upper back, hands on the two handles in front of the shoulders: a squat to
    parallel with the torso upright."""
    def handle(sd):
        def A(D, Hp, cx):
            Rt = D[c.r.bi("spine01")]
            lat, up, fwd = Rt @ X, Rt @ Z, Rt @ Y
            M = _bar_R(lat)
            g = np.asarray(c.lmk(D, Hp, "back_bar"), float) + M @ np.array([SIDES[sd] * 0.13, 0.4, -0.115])
            return dict(grip=g, thumb=unit(fwd - up * 0.3), pole=-up + lat * SIDES[sd] * 0.35, curl=0.9)
        return A

    def post(spec, D, Hp, ex, eqs):
        for e in eqs:
            if e["kind"] == "barbell":
                e["kind"] = "ssb"
                e["shape"] = {}
    legs = c.feet(w=c.hw * 1.3 + 0.08, toe=22)
    return c.stand(legs, hk=L(0.985, 0.56), pel=(L(3, 26), 0, 0), spine=(L(0, 4), 0, 0), neck=(L(0, -18), 0, 0),
                   hold="back_bar", load=0.4, arms={"L": handle("L"), "R": handle("R")}, post=post)


@x("machine-shrug")
def machine_shrug(c, t, L, row):
    """Standing on the shrug machine's platform, the handles at the sides of the thighs in straight arms: the
    shoulders shrug straight up and lower slowly."""
    e = L(0, 22)
    clav = {"L": (e, -3), "R": (e, -3)}
    arms = arm_fk((0.2, 0.0, -1), elbow=6, thumb="fwd", curl=0.9)
    legs = c.feet(w=c.hw * 1.15, toe=8)
    eq = [H("d_handle", sd, "db") for sd in "LR"] + [E("shrug_machine", (0, 0.0, 0), eid="sm")]
    for sd in "LR":
        piv = np.array([SIDES[sd] * 0.43, -0.32, 1.2])
        eq.append(seg(f"lever{sd}", piv, (f"grip{sd}", (0, 0, 0.04)), 0.022, "frame"))
    return c.stand(legs, hk=0.995, pel=(2, 0, 0), arms=arms, clav=clav, equip=eq, load=0.3)


@x("cable-shoulder-press")
def cable_shoulder_press(c, t, L, row):
    """Seated upright between two low pulleys, a handle in each hand at the shoulders: both handles press
    overhead to straight arms and come back down slowly."""
    from .tpl_upper import seat_bench_upright
    arms, _ = fam.press_db(c, L(0, 1), "oh", w0=c.sw * 1.6, w1=c.sw * 1.0, thumb_mode="pro")
    eq = [H("d_handle", sd, "db") for sd in "LR"]
    for sd in "LR":
        pul = np.array([SIDES[sd] * 0.85, 0.1, 0.15])
        eq.append(E("cable_tower", pul * [1, 1, 0] + np.array([SIDES[sd] * 0.12, 0, 0]), R=fam.rz(-90 * SIDES[sd]),
                    eid=f"tower{sd}", pulley_h=0.15))
        eq.append(seg(f"cable{sd}", pul, f"grip{sd}", 0.0045, "darksteel"))
    return seat_bench_upright(c, arms=arms, equip=eq)


@x("chest-supported-t-bar-row")
def cs_tbar_row(c, t, L, row):
    """Chest on the inclined pad, feet on the platform, hands on the lever handles below the pad: the handles
    are pulled to the stomach (shoulder blades squeezed) and lowered to straight arms."""
    ang = 34.0
    piv = np.array([0, 0.75, 0.18])          # lever pivot, low in front
    k = L(0, 1)

    def tgt(D, Hp, c_, sd):
        m = fam.sh_mid(D, Hp, c)
        lo = m - Z * c.Lh * 0.96
        hi = c.lmk(D, Hp, "chest") - Z * 0.12 - Y * 0.08
        return lo * (1 - k) + hi * k + X * SIDES[sd] * 0.16
    arms = arm_ik(tgt, (0, 1, 0), (0.6, -0.6, 0.6), curl=0.9)
    legs = {sd: dict(ball=np.array([SIDES[sd] * 0.15, -0.62, 0.2 + SOLE]), yaw=6, heel=10, surf=0.2,
                     pole=np.array([SIDES[sd] * 0.1, 1, 0.3])) for sd in "LR"}
    Rb = rx(ang)
    pad_c = np.array([0, 0.05, 1.06])
    n_pad = Rb @ Z

    def lever(spec, eq, ex):
        def mid(pts, D, Hp, cx):
            return 0.5 * (np.asarray(pts["gripL"], float) + np.asarray(pts["gripR"], float))
        return [seg("lever", piv, mid, 0.025, "frame"), seg("hbar", ("gripL", (0, 0, 0)), ("gripR", (0, 0, 0)), 0.016, "steel")]
    fr = c.stand(legs, pz=0.92, py=-0.4, pel=(90 - ang, 0, 0), neck=(-12, 0, 0), arms=arms, balance=None, reach=True,
                 planted=("L", "R"), equip=[E("tbar_chest", (0, 0, 0), eid="tbc")],
                 settle=[("plane", pad_c + n_pad * 0.04, n_pad, X, 0.16, Rb @ Y, 0.25, 0.01)])
    return _with_eq(fr, lever)


@x("glute-kickback-machine")
def kickback_machine_m(c, t, L, row):
    """Forearms on the machine's pad, standing on the left foot, the right foot against the plate: the right
    leg pushes back and up until the thigh is in line with the body, then returns."""
    k = L(0, 1)
    legs = {"L": c.foot(-c.hw * 0.5, -0.05, 6),
            "R": dict(thigh=unit(np.array([0.02, 0.35 - 1.25 * k, -1.0 + 1.05 * k])), knee=95 - 45 * k,
                      kbend=np.array([0, -1, 0.2]), fdir=np.array([0, -0.3, -1]))}

    def pad(D, Hp, c_, sd):
        return np.array([SIDES[sd] * 0.15, 0.48, 1.0])
    arms = arm_ik(pad, (0, 0, 1), (SIDES["R"] * 0.3, -1, -0.3), curl=0.9)
    fr = c.stand(legs, pz=c.pz * 0.95, py=-0.05, pel=(55, 0, 0), neck=(-20, 0, 0), arms=arms, balance=None, reach=True,
                 planted=("L",), equip=[E("kickback_machine", (0, 0.12, 0), eid="kbm")])
    return fr


@x("glute-ham-raise-sit-up")
def ghd_sit_up(c, t, L, row):
    """Sitting face-up on the glute-ham bench, hips on the round pad and feet locked under the rollers, arms
    crossed on the chest: the torso leans back to a little below level and sits back up."""
    a = L(-15, -98)
    legs = legs_fk((0.06, 1.0, -0.12), knee=18, kbend=(0, 0, -1), fdir=(0, 0.3, 1))
    fr = fam.seated(c, seat_h=0.99, seat_y=0.0, pitch=a, hold="cross", legs=legs,
                    equip=[E("ghd", (0, 0.05, 0), eid="ghd")])
    return fr


# ================================================================== keyed whole-body sequences (burpee family)
def _seq_defaults(K, c):
    d0 = {"hL": 0.0, "hR": 0.0, "gL": 1.0, "gR": 1.0, "sL": 0.0, "sR": 0.0, "neck": 0.0, "px": 0.0,
          "uL": (0.12, 0.05, -1.0), "uR": (0.12, 0.05, -1.0), "pL": (-0.2, 0.3, 0.0), "pR": (0.2, 0.3, 0.0),
          "mL": 0.0, "mR": 0.0, "palm": 0.0, "el": 12.0}
    for _, d in K:
        for k, v in d0.items():
            d.setdefault(k, v)
    return K


def _seq_arms(c, kv, dbs=False):
    """Arms from interpolated keys: per side a direction from the shoulder (u, body frame, right side; mirrored
    for the left) blended by m into a world point p; palm > 0.5 puts the palm flat on p."""
    def mk(sd):
        s = SIDES[sd]

        def f(D, Hp, c_):
            sh = fam.shoulder(D, Hp, c, sd)
            v = np.array(kv["u" + sd], float)
            air = sh + unit(D[c.r.bi("spine01")] @ v) * c.Lh * 0.96
            pt = np.asarray(kv["p" + sd], float)
            m = float(kv["m" + sd])
            if kv["palm"] > 0.5 and m > 0.98:
                return dict(palm=pt, thumb=np.array([-s, 0.15, 0]), fing=Y, pole=np.array([s * 0.25, -1, 0.25]), curl=0.05)
            p = air * (1 - m) + pt * m
            d = p - sh
            p = sh + unit(d) * min(np.linalg.norm(d), c.Lh * 0.97)
            if dbs:
                return dict(grip=p, thumb=unit(Y * 0.9 + Z * 0.1 * (1 - m)), pole=np.array([s * 0.5, -1, 0.1]), curl=0.9)
            return dict(grip=p, thumb=unit(Y * (1 - m) - X * s * m + Z * 1e-3), pole=np.array([s * 0.4, -1, 0.2]),
                        curl=0.4 * (1 - m) + 0.5)
        return f
    return {"L": mk("L"), "R": mk("R")}


def _mirror_u(K):
    """u values are written for the right arm; the left arm mirrors x."""
    for _, d in K:
        if "uL" in d:
            u = list(d["uL"])
            u[0] = -abs(u[0]) if u[0] > 0 else u[0]
            d["uL"] = tuple(u)
    return K


def _over(c, hy, pitch, sh_z):
    tor = 0.5 * c.S
    a = math.radians(pitch)
    return dict(py=hy - tor * math.sin(a), pz=sh_z - tor * math.cos(a), pitch=pitch)


def _bt_burpee(c, t, L, row, push):
    """Balance trainer burpee: the trainer held by its edges overhead (dome down), set on the floor in a squat,
    feet jumped back to a plank with the hands on its edges (a push-up), feet jumped in, stand and lift it."""
    S, w, H0 = c.S, c.hw * 0.6, 0.222
    hy = 0.36 * S
    fb = hy - 1.38 * S
    edge = {sd: (SIDES[sd] * 0.29, hy, H0 + 0.004) for sd in "LR"}
    up = dict(uL=(0.25, 0.05, 1.0), uR=(0.25, 0.05, 1.0), mL=0.0, mR=0.0, el=8)
    floor = dict(pL=edge["L"], pR=edge["R"], mL=1.0, mR=1.0)
    stand = dict(fL=(-w, 0, 0), fR=(w, 0, 0), pz=c.pz * 0.97, py=0.0, pitch=3, **up)
    squat = dict(fL=(-w, 0, 0), fR=(w, 0, 0), neck=-25, hL=30, hR=30, **floor, **_over(c, hy, 70, H0 + c.Lpf * 0.95))
    plank = dict(fL=(-w * 0.8, fb, 0), fR=(w * 0.8, fb, 0), neck=-15, hL=70, hR=70, palm=1.0, **floor,
                 **_over(c, hy, 76, H0 + c.Lpf * 0.97))
    bottom = dict(plank, **_over(c, hy, 82, H0 + 0.3 * S))
    mid = dict(plank, fL=(-w * 0.9, fb * 0.5, 0.12), fR=(w * 0.9, fb * 0.5, 0.12), gL=0, gR=0, hL=50, hR=50,
               **dict(_over(c, hy, 72, H0 + c.Lpf * 0.96)))
    mid["pz"] += 0.12
    lift = dict(stand, pz=c.pz * 0.8, pitch=30, uL=(0.2, 0.8, 0.0), uR=(0.2, 0.8, 0.0), el=10)
    K = [(0.0, stand), (0.12, lift), (0.22, dict(squat, palm=0.0)), (0.27, dict(squat, palm=1.0)), (0.33, mid), (0.40, plank)]
    if push:
        K += [(0.50, bottom), (0.60, plank)]
    t_in = K[-1][0] + 0.1
    K += [(t_in - 0.05, mid), (t_in, dict(squat, palm=1.0)), (t_in + 0.06, dict(squat, palm=0.0)),
          (min(0.9, t_in + 0.2), lift), (1.0, stand)]
    K = _mirror_u(_seq_defaults(K, c))
    kv = _interp(K, t)
    held = kv["palm"] < 0.5 and not (kv["mL"] > 0.98 and t > 0.2 and t < t_in + 0.06)
    if held:
        eq = [H("bosu_dn", "C", "bar", eid="bt")]
    else:
        eq = [E("bosu_dn", (0, hy, H0), eid="bt")]
    fr = keyed_stand(c, kv, arms=_seq_arms(c, kv), equip=eq + [E("mat", (0, -0.25, 0), eid="mat")])
    if kv["mL"] > 0.3:
        fr.cons.append(("reach_arms", -Z, ["L", "R"]))
    return fr


@x("balance-trainer-burpee")
def bt_burpee(c, t, L, row):
    return _bt_burpee(c, t, L, row, push=False)


@x("balance-trainer-burpee-with-push-up")
def bt_burpee_push(c, t, L, row):
    return _bt_burpee(c, t, L, row, push=True)


def _db_floor(c, hy, sd):
    return (SIDES[sd] * c.sw * 0.62, hy, 0.115)


@x("devil-press")
def devil_press(c, t, L, row):
    """Hands on two dumbbells: a chest-to-floor burpee, feet jumped in, the dumbbells swung back between the
    legs and driven overhead in one move, then lowered to the floor."""
    S, w = c.S, c.hw * 0.75
    hy = 0.36 * S
    fb = hy - 1.38 * S
    dbp = {sd: _db_floor(c, hy, sd) for sd in "LR"}
    on = dict(pL=dbp["L"], pR=dbp["R"], mL=1.0, mR=1.0)
    plank = dict(fL=(-w * 0.7, fb, 0), fR=(w * 0.7, fb, 0), neck=-15, hL=70, hR=70, **on, **_over(c, hy, 76, 0.11 + c.Lpf * 0.97))
    bottom = dict(plank, **_over(c, hy, 86, 0.11 + 0.22 * S))
    squat = dict(fL=(-w, 0, 0), fR=(w, 0, 0), neck=-25, hL=20, hR=20, **on, **_over(c, hy, 62, 0.11 + c.Lpf * 0.9))
    mid = dict(plank, fL=(-w * 0.9, fb * 0.5, 0.12), fR=(w * 0.9, fb * 0.5, 0.12), gL=0, gR=0, hL=50, hR=50)
    mid["pz"] += 0.12
    swing = dict(fL=(-w, 0, 0), fR=(w, 0, 0), pz=c.pz * 0.82, py=-0.12, pitch=62, neck=-20, uL=(0.05, -0.55, -0.85),
                 uR=(0.05, -0.55, -0.85), mL=0.0, mR=0.0, el=5)
    drive = dict(fL=(-w, 0, 0), fR=(w, 0, 0), pz=c.pz * 0.99, py=0.0, pitch=0, uL=(0.12, 0.9, 0.3), uR=(0.12, 0.9, 0.3),
                 mL=0.0, mR=0.0, el=30, hL=20, hR=20)
    top = dict(fL=(-w, 0, 0), fR=(w, 0, 0), pz=c.pz * 0.98, py=0.0, pitch=2, uL=(0.12, 0.05, 1.0), uR=(0.12, 0.05, 1.0),
               mL=0.0, mR=0.0, el=6)
    K = [(0.0, plank), (0.12, bottom), (0.24, plank), (0.32, mid), (0.40, squat), (0.55, swing), (0.68, drive), (0.78, top),
         (0.92, squat), (0.96, mid), (1.0, plank)]
    K = _mirror_u(_seq_defaults(K, c))
    kv = _interp(K, t)
    fr = keyed_stand(c, kv, arms=_seq_arms(c, kv, dbs=True), equip=[H("dumbbell", "L"), H("dumbbell", "R"),
                                                                     E("mat", (0, -0.25, 0), eid="mat")])
    if kv["mL"] > 0.3:
        fr.cons.append(("reach_arms", -Z, ["L", "R"]))
    return fr


@x("man-maker")
def man_maker(c, t, L, row):
    """Plank on two dumbbells: a push-up, a row with each arm, feet jumped in, the dumbbells cleaned to the
    shoulders, a squat that drives into an overhead press, then back down to the plank."""
    S, w = c.S, c.hw * 0.75
    hy = 0.36 * S
    fb = hy - 1.38 * S
    dbp = {sd: _db_floor(c, hy, sd) for sd in "LR"}
    on = dict(pL=dbp["L"], pR=dbp["R"], mL=1.0, mR=1.0)
    plank = dict(fL=(-w * 0.9, fb, 0), fR=(w * 0.9, fb, 0), neck=-15, hL=70, hR=70, **on, **_over(c, hy, 76, 0.11 + c.Lpf * 0.97))
    bottom = dict(plank, **_over(c, hy, 84, 0.11 + 0.3 * S))
    rowR = dict(plank, pR=(dbp["R"][0] + 0.03, hy - 0.22, 0.42), mR=1.0)
    rowL = dict(plank, pL=(dbp["L"][0] - 0.03, hy - 0.22, 0.42), mL=1.0)
    squat = dict(fL=(-w, 0, 0), fR=(w, 0, 0), neck=-25, hL=20, hR=20, **on, **_over(c, hy, 62, 0.11 + c.Lpf * 0.9))
    mid = dict(plank, fL=(-w * 0.9, fb * 0.5, 0.12), fR=(w * 0.9, fb * 0.5, 0.12), gL=0, gR=0, hL=50, hR=50)
    mid["pz"] += 0.12
    rack = dict(fL=(-w, 0, 0), fR=(w, 0, 0), pz=c.pz * 0.97, py=0.0, pitch=3, uL=(0.35, 0.55, 0.1), uR=(0.35, 0.55, 0.1),
                mL=0.0, mR=0.0, el=140)
    deep = dict(rack, pz=c.pz * 0.6, pitch=28, neck=-10)
    press = dict(rack, uL=(0.12, 0.05, 1.0), uR=(0.12, 0.05, 1.0), el=6)
    K = [(0.0, plank), (0.08, bottom), (0.16, plank), (0.22, rowR), (0.28, plank), (0.34, rowL), (0.40, plank), (0.46, mid),
         (0.52, squat), (0.60, rack), (0.68, deep), (0.78, press), (0.86, rack), (0.93, squat), (1.0, plank)]
    K = _mirror_u(_seq_defaults(K, c))
    kv = _interp(K, t)
    fr = keyed_stand(c, kv, arms=_seq_arms(c, kv, dbs=True), equip=[H("dumbbell", "L"), H("dumbbell", "R"),
                                                                     E("mat", (0, -0.25, 0), eid="mat")])
    if kv["mL"] > 0.3 and kv["mR"] > 0.3:
        fr.cons.append(("reach_arms", -Z, ["L", "R"]))
    return fr


# ================================================================== balance trainer: planks, crunches, squat
H_DN = 0.222       # flat platform of a dome-down trainer above the floor


def _dome_z(dx, dy=0.0):
    r = math.hypot(dx, dy)
    return 0.03 + 0.192 * math.sqrt(max(0.0, 1 - (r / 0.32) ** 2)) if r < 0.32 else 0.004


@x("balance-trainer-up-and-down-plank")
def bt_up_down_plank(c, t, L, row):
    """Forearms on the edges of the flat side of a dome-down trainer, feet back in a plank: the right arm
    straightens onto its hand, then the left, to a straight-arm plank (and back down)."""
    u = L(0.0, 1.0)
    kR = min(1.0, max(0.0, u / 0.5))
    kL = min(1.0, max(0.0, (u - 0.5) / 0.5))
    kR, kL = [0.5 - 0.5 * math.cos(math.pi * k) for k in (kR, kL)]
    hw = c.sw * 1.0

    def palm(sd, k):
        def f(D, Hp, c_, sd_):
            sh = fam.shoulder(D, Hp, c, sd)
            fore = np.array([SIDES[sd] * hw * 0.42, sh[1] + c.r.dims["R"]["L2"] * 0.85, H_DN + 0.004])
            under = np.array([SIDES[sd] * hw / 2, sh[1] + 0.02, H_DN + 0.004])
            return fore * (1 - k) + under * k
        return f
    arms_over = {}
    for sd, k in (("R", kR), ("L", kL)):
        arms_over.update(arm_ik(palm(sd, k), (-1, 0.15, 0), (0.25, -1.0 + 0.6 * (1 - k), -0.9 * (1 - k) + 0.25 * k),
                                curl=0.05, key="palm", fing=(0, 1, 0), sides=sd))
    return fam.plank(c, down=0.62 * (1 - 0.5 * (kR + kL)), top_down=0.0, hand_w=hw, hands_h=H_DN,
                     equip=[MATP(), E("bosu_dn", (0, 0.05, H_DN), eid="bt")], arms_over=arms_over, hands_on=True)


@x("balance-trainer-traveling-dome-plank")
def bt_travel_plank(c, t, L, row):
    """Straight-arm plank beside a dome-up trainer: the right hand steps onto the dome, the left joins it, the
    right steps down on the far side and the left follows (the feet shuffle along), then back the same way."""
    s = (t % 1.0) * 2
    back = s > 1
    s = 2 - s if back else s
    # world x of the left / right hand and of the body; the dome sits at x = 0
    K = [(0.0, dict(l=-0.86, r=-0.36, b=-0.61)), (0.25, dict(l=-0.86, r=-0.1, b=-0.48)),
         (0.5, dict(l=-0.12, r=0.12, b=0.0)), (0.75, dict(l=0.1, r=0.86, b=0.48)), (1.0, dict(l=0.36, r=0.86, b=0.61))]
    kv = _interp(K, min(s, 0.9999)) if s < 1 else dict(K[-1][1])
    b = float(kv["b"])
    lift = {}
    for sd, key in (("L", "l"), ("R", "r")):
        for (t0, a), (t1, bb) in zip(K[:-1], K[1:]):
            if t0 <= s <= t1 and abs(a[key] - bb[key]) > 1e-3:
                lift[sd] = 0.07 * math.sin(math.pi * (s - t0) / (t1 - t0))
    hx = {"L": float(kv["l"]) - b, "R": float(kv["r"]) - b}

    def palm(D, Hp, c_, sd):
        wx = hx[sd] + b
        return np.array([hx[sd], 0.0, _dome_z(wx) + 0.004 + lift.get(sd, 0.0)])
    arms_over = arm_ik(palm, (-1, 0.15, 0), (0.25, -1.0, 0.25), curl=0.05, key="palm", fing=(0, 1, 0))
    hh = 0.5 * (_dome_z(hx["L"] + b) + _dome_z(hx["R"] + b))
    fr = fam.plank(c, down=0.0, hand_w=c.sw * 1.1, hands_h=hh, feet_w=0.28 * c.S, arms_over=arms_over, hands_on=True,
                   equip=[E("bosu", (-b, 0.0, 0), eid="bt")], neck=(-10, 0, 0))
    fr.cons = [cn for cn in fr.cons if cn[0] != "reach_arms"]
    return fr


def _dome_back(c, t, L, legs=None, spine=(0, 0, 0), hold="head", arms=None, equip=(), neck=(0, 0, 0)):
    top = 0.23
    lg = {sd: dict(ball=np.array([SIDES[sd] * 0.18 * c.S, 0.55 * c.S, SOLE]), yaw=10, heel=0,
                   pole=np.array([SIDES[sd] * 0.2, 0.3, 1])) for sd in "LR"}
    lg.update(legs or {})
    sup = [("plane", np.array([0, 0.0, top]), Z, X, 0.15, Y, 0.16, -0.02)]
    return c.stand(lg, pz=top + 0.12, py=0.12, pel=(L(-82, -74), 0, 0), spine=spine, hold=hold, arms=arms,
                   balance=None, reach=False, equip=[E("bosu", (0, 0.0, 0), eid="bosu")] + list(equip), settle=sup,
                   planted=[sd for sd in "LR" if "ball" in lg[sd]], neck=neck)


@x("balance-trainer-single-leg-crunch")
def bt_sl_crunch(c, t, L, row):
    """Lower back on the dome, left foot on the floor, the right leg held straight up off the floor: the
    shoulders curl up and lower."""
    legs = legs_fk((0.06, 0.75, 0.62), knee=8, kbend=(0, 0, -1), sides="R")
    return _dome_back(c, t, L, legs=legs, spine=(L(-12, 26), 0, 0), neck=(L(0, 12), 0, 0))


@x("balance-trainer-cable-crunch-with-side-bends")
def bt_cable_crunch_bend(c, t, L, row):
    """Lower back on the dome in front of a low pulley, rope held beside the head: the shoulders crunch up and
    bend to one side, return and lower (the next rep bends to the other side)."""
    pul = np.array([0, -1.25, 0.18])
    sgn = 1.0 if row.get("_side", "R") == "R" else -1.0

    def tgt(D, Hp, c_, sd):
        return c.lmk(D, Hp, "forehead") + X * SIDES[sd] * 0.11 - Y * 0.02 + Z * 0.02
    arms = arm_ik(tgt, (0, 1, 0), lambda D, Hp, c_, sd: np.array([SIDES[sd], 0.2, 0.4]), curl=0.9, fing=(0, -1, 0))
    eq = [E("cable_tower", np.array([0, pul[1] - 0.12, 0]), R=fam.rz(0), eid="tower", pulley_h=pul[2]),
          seg("ropeL", pul, "gripL", 0.012, "rope"), seg("ropeR", pul, "gripR", 0.012, "rope")]
    return _dome_back(c, t, L, spine=(L(-12, 22), L(0, 18 * sgn), 0), hold="none", arms=arms, equip=eq,
                      neck=(L(0, 10), 0, 0))


@x("balance-trainer-stability-ball-overhead-squat")
def bt_ball_oh_squat(c, t, L, row):
    """Standing on the dome with a stability ball held overhead in straight arms: a slow squat with the ball
    staying overhead, then stand."""
    w = c.hw * 0.55
    legs = {sd: dict(ball=np.array([SIDES[sd] * w, c.ball_y - 0.02, DOME + SOLE]), yaw=10, heel=0, surf=DOME) for sd in "LR"}

    def tgt(D, Hp, c_, sd):
        m = fam.sh_mid(D, Hp, c)
        return m + Z * c.Lh * 0.9 + X * SIDES[sd] * 0.27 - Y * 0.04
    arms = arm_ik(tgt, (0, 0, 1), lambda D, Hp, c_, sd: np.array([SIDES[sd], 0.2, -0.3]), key="palm", curl=0.2,
                  fing=(0, 0, 1))

    def ball(D, Hp, cx, ex):
        m = fam.sh_mid(D, Hp, c)
        return E("stability_ball", m + Z * (c.Lh * 0.9 - 0.3 + 0.27) - Y * 0.04, eid="sb", dyn=True, r=0.3)
    return c.stand(legs, pz=L(c.pz * 0.98, c.pz * 0.7) + DOME, pel=(L(2, 24), 0, 0), spine=(L(0, -4), 0, 0), arms=arms,
                   equip=[E("bosu", (0, -0.04, 0), eid="bosu"), ball], balance="com")


@x("balance-trainer-rear-glute-raise")
def bt_rear_glute(c, t, L, row):
    """Hands on the dome, knees on the floor: the right leg, straight back, lifts to body level and lowers."""
    leg = dict(thigh=np.array([0.03, -1.0, L(-0.55, 0.12)]), knee=6, kbend=np.array([0, -1, 0.2]), fdir=np.array([0, -0.3, -1]))

    def on_dome(D, Hp, c_, sd):
        sh = fam.shoulder(D, Hp, c, sd)
        return np.array([SIDES[sd] * 0.15, sh[1] + 0.02, _dome_z(0.15, 0.05) + 0.01])
    arms = arm_ik(on_dome, (-1, 0.2, 0), (0.2, -1, 0.3), key="palm", curl=0.05, fing=(0, 1, 0))
    fr = quadruped(c, t, L, row, legs_over={"R": leg}, arms_over=arms, drop=-0.17,
                   equip=[E("bosu", (0, 0.62 * c.S * 0.9, 0), eid="bosu")])
    return fr


# ================================================================== abs on the floor
@x("stability-ball-v-pass")
def ball_v_pass(c, t, L, row):
    """On the back, a stability ball in the hands overhead: arms and legs rise together into a V and the ball
    goes from the hands to between the ankles; the legs lower with the ball as the arms go back overhead (the
    next rep takes it back)."""
    k = math.sin(math.pi * min(max(t, 0.0), 1.0))
    a = 8 + 62 * k
    legs = legs_fk((0.06, math.cos(math.radians(a)), math.sin(math.radians(a))), knee=6, kbend=(0, 0, -1))
    up = 0.5 * (1 - math.cos(math.pi * min(max(t, 0.0), 1.0)))
    held = t < 0.5
    arms = arm_fk((0.18, -0.95 + 1.75 * k, 0.25 + 0.6 * k), elbow=8, thumb="in", curl=0.2)
    eq = [H("stability_ball", "C", "ball", eid="sb", r=0.3)] if held else []
    fr = supine_legs(c, legs, arms=arms, pitch=-90 + 40 * k, spine=(30 * k, 0, 0), equip=eq)
    if not held:
        from .tpl_x54 import _ball_between_feet
        fr = _ball_between_feet(c, fr)
    return fr


@x("dumbbell-halo-to-oblique-crunch")
def db_halo_oblique(c, t, L, row):
    """A light dumbbell held by both ends circles once round the head; then the right knee lifts out to the
    side and the torso bends down toward it (the next rep circles the other way to the left side)."""
    if t < 0.6:
        u = t / 0.6
        return REG["kb_halo"].fn(c, u, lambda a, b: (tuple(np.asarray(a, float) * (1 - u) + np.asarray(b, float) * u)
                                                     if isinstance(a, (tuple, list)) else a * (1 - u) + b * u),
                                 dict(row, equipment="dumbbell"))
    k = math.sin(math.pi * (t - 0.6) / 0.4)
    legs = c.feet(w=c.hw * 1.3)
    legs["R"] = dict(thigh=unit(np.array([0.7 * k + 0.05, 0.1 + 0.4 * k, -1 + 1.0 * k])), knee=10 + 80 * k,
                     kbend=unit(np.array([0, -1 + k, -k])), fdir=np.array([0.2, 0.7, -0.6]))

    def tgt(D, Hp, c_, sd):
        hd = c.lmk(D, Hp, "head_top") - Z * 0.1
        return hd + np.array([0.0, 0.18, 0.0]) + X * SIDES[sd] * 0.03
    arms = arm_ik(tgt, (0, 0, 1), lambda D, Hp, c_, sd: np.array([SIDES[sd] * 0.8, -0.45, -0.4]), curl=0.9)
    fr = c.stand(legs, arms=arms, spine=(10 * k, -28 * k, 0), equip=[H("dumbbell", "C", "vert", eid="db")], planted=("L",))
    return fr


# ================================================================== fixes of earlier drafts
TW = -70.0


@x("rotation-push-up")
def rotation_push_up(c, t, L, row):
    """A push-up; at the top the body turns onto the right hand into a side plank with the left arm reaching
    to the ceiling, then back down (the next rep turns the other way)."""
    if t <= 0.5:
        dn, k = 0.9 * math.sin(math.pi * t / 0.5), 0.0
    else:
        dn, k = 0.0, math.sin(math.pi * (t - 0.5) / 0.5)
    hw = c.sw * 1.15

    def armL(D, Hp, c_, sd):
        flo = np.array([-hw / 2, 0.0, 0.004])
        sh = fam.shoulder(D, Hp, c, "L")
        up = sh + Z * c.Lh * 0.95
        return flo * (1 - k) + up * k + Z * 0.06 * math.sin(math.pi * min(1.0, k * 2))
    arms_over = arm_ik(armL, (-1, 0.15, 0.0), lambda D, Hp, c_, sd: np.array([-0.3, -1.0 + 0.5 * k, 0.3 + 0.5 * k]),
                       curl=0.05 + 0.2 * k, key="palm", sides="L", fing=(0, 1, 0))

    fr = fam.plank(c, down=dn, hand_w=hw, feet_w=0.3 * c.S, equip=[MATP()], neck=(-10, 0, 0), hands_on=True,
                   arms_over=arms_over)
    fr.cons = [cn for cn in fr.cons if cn[0] != "reach_arms"] + [("reach_arms", -Z, ["R"] if k > 0 else ["L", "R"])]
    b0 = fr.build

    def build():
        spec, eq, ex = b0()
        spec["twist"] = TW * k
        return spec, eq, ex
    fr.build = build
    return fr


@x("walkout-to-push-up")
def walkout_push(c, t, L, row):
    """Stand, fold from the hips until the hands reach the floor, walk the hands out to a push-up position, one
    push-up, walk the hands back to the feet and stand (cycle)."""
    S, w = c.S, c.hw * 0.55
    hy = 1.38 * S - 0.06
    feet = dict(fL=(-w, 0, 0), fR=(w, 0, 0))

    def hands(y, lift=(0.0, 0.0)):
        return dict(pL=(-c.sw * 0.6, y, 0.004 + lift[0]), pR=(c.sw * 0.6, y, 0.004 + lift[1]), mL=1.0, mR=1.0, palm=1.0)
    stand = dict(feet, pz=c.pz * 0.97, py=0.0, pitch=3)
    fold = dict(feet, pz=c.pz * 0.84, py=-0.1, pitch=112, neck=20, hL=0, hR=0, **hands(0.42))
    walk1 = dict(feet, pz=c.pz * 0.86, py=0.05, pitch=95, neck=10, **hands(0.8))
    walk2 = dict(feet, pz=c.pz * 0.7, py=0.3, pitch=82, neck=0, hL=30, hR=30, **hands(1.1))
    plank = dict(feet, hL=70, hR=70, neck=-15, **hands(hy), **_over(c, hy, 76, c.Lpf * 0.97))
    plank["fL"], plank["fR"] = (-w * 0.8, 0, 0), (w * 0.8, 0, 0)
    bottom = dict(plank, **_over(c, hy, 84, 0.3 * S))
    K = [(0.0, stand), (0.12, dict(fold, palm=0.0, mL=0.6, mR=0.6)), (0.18, fold), (0.27, walk1), (0.34, walk2), (0.42, plank),
         (0.52, bottom), (0.62, plank), (0.70, walk2), (0.77, walk1), (0.84, fold), (0.9, dict(fold, palm=0.0, mL=0.6, mR=0.6)),
         (1.0, stand)]
    K = _mirror_u(_seq_defaults(K, c))
    kv = _interp(K, t)
    fr = keyed_stand(c, kv, arms=_seq_arms(c, kv), equip=[E("mat", (0, 0.4, 0), eid="mat")])
    if kv["mL"] > 0.9:
        fr.cons.append(("reach_arms", -Z, ["L", "R"]))
    return fr


@x("single-leg-glute-bridge-with-external-rotation")
def sl_bridge_er(c, t, L, row):
    """On the back, the right ankle crossed over the left knee with the right knee open: the left heel drives the
    hips up and lowers them."""
    fr = REG["glute_bridge"].fn(c, t, L, dict(row, name_en="Glute Bridge", equipment="mat ; supine"))
    b0 = fr.build

    def build():
        spec, eq, ex = b0()
        D, Hp = c.torso(spec)
        hip = Hp[c.r.bi("upperleg01.L")]
        ball = np.asarray(spec["leg"]["L"]["ball"], float)
        ank = ball - Y * 0.1 + Z * 0.07
        mid = 0.5 * (hip + ank)
        dn = np.linalg.norm(hip - ank)
        knee = mid + Z * math.sqrt(max(0.0, (c.leg * 0.5) ** 2 - (dn * 0.5) ** 2))
        spec["leg"]["R"] = dict(ankle=knee + Z * 0.1 + X * 0.03, fdir=unit(np.array([-0.8, 0.3, 0.2])), fup=Z,
                                pole=unit(np.array([1.0, 0.4, 0.5])))
        return spec, eq, ex
    fr.build = build
    fr.planted = ["L"]
    return fr


# ================================================================== suspension straps
def _straps(anchor):
    return [dict(E("trx_anchor", np.asarray(anchor) * np.array([1, 1, 0]), eid="trx", h=float(anchor[2])), fit=False),
            seg("strapL", anchor, ("gripL", (0, 0, 0)), 0.012, "strap"),
            seg("strapR", anchor, ("gripR", (0, 0, 0)), 0.012, "strap")]


@x("suspension-leg-raise")
def susp_leg_raise(c, t, L, row):
    """On the back under the anchor, the handles held above the head in straight arms: the legs rise to vertical
    and the hips peel a little off the floor, then lower slowly."""
    anchor = np.array([0.0, -0.55, 2.3])
    a = math.radians(L(6, 92))
    legs = legs_fk((0.05, math.cos(a), math.sin(a)), knee=L(4, 10), kbend=(0, 0, -1), fdir=(0, -math.sin(a), math.cos(a)))

    def tgt(D, Hp, c_, sd):
        sh = fam.shoulder(D, Hp, c, sd)
        return sh + unit(anchor + X * SIDES[sd] * 0.1 - sh) * c.Lh * 0.96
    arms = arm_ik(tgt, (0, 0, 1), lambda D, Hp, c_, sd: np.array([SIDES[sd], 0.3, 0.2]), curl=0.9)
    return supine_legs(c, legs, arms=arms, pitch=L(-90, -78), spine=(L(0, 8), 0, 0), equip=_straps(anchor))


@x("suspension-kneeling-oblique-rollout")
def susp_kneel_oblique(c, t, L, row):
    """Kneeling with the back to the anchor, handles in straight arms in front: the body leans forward from the
    knees as the arms reach diagonally forward and up over the left shoulder, then back (alternating sides)."""
    from .tpl_floor import kneeling
    anchor = np.array([0.0, -0.9, 2.35])
    sgn = 1.0 if row.get("_side", "R") == "R" else -1.0
    k = L(0.0, 1.0)

    def tgt(D, Hp, c_, sd):
        m = fam.sh_mid(D, Hp, c)
        d = unit(np.array([-0.45 * sgn * k, 1.0, -0.35 + 0.95 * k]))
        return m + d * c.Lh * 0.95 + X * SIDES[sd] * 0.09
    arms = arm_ik(tgt, (0, 0, 1), lambda D, Hp, c_, sd: np.array([SIDES[sd], -0.2, -0.5]), curl=0.9)
    return kneeling(c, t, L, row, arms=arms, equip=_straps(anchor), pitch=L(8, 45), spine=(0, 0, L(0, -14 * sgn)))


@x("suspension-swimmer-pull")
def susp_swimmer(c, t, L, row):
    """Facing the anchor, leaning back with the handles overhead in straight arms and the body straight: the
    straight arms sweep down to the thighs and the body rises toward upright, then lowers back."""
    anchor = np.array([0.0, 1.5, 2.4])
    k = L(0.0, 1.0)
    legs = c.feet(w=c.hw * 1.0, toe=6)
    for sd in legs:
        legs[sd]["heel"] = 0

    def tgt(D, Hp, c_, sd):
        sh = fam.shoulder(D, Hp, c, sd)
        Rt = D[c.r.bi("spine01")]
        over = sh + unit(Rt @ np.array([SIDES[sd] * 0.1, 0.25, 1.0])) * c.Lh * 0.96
        low = sh + unit(Rt @ np.array([SIDES[sd] * 0.12, 0.15, -1.0])) * c.Lh * 0.96
        a = math.radians(180 * k)
        d = unit(over - sh) * math.cos(a / 2) ** 2 + unit(low - sh) * math.sin(a / 2) ** 2
        fwd = Rt @ Y
        p = sh + unit(d + fwd * 0.9 * math.sin(a)) * c.Lh * 0.96
        return p
    arms = arm_ik(tgt, (0, 0, 1), lambda D, Hp, c_, sd: np.array([SIDES[sd], -0.3, 0]), curl=0.9)
    return c.stand(legs, hk=0.995, pel=(L(-32, -12), 0, 0), arms=arms, balance=None, reach=True, equip=_straps(anchor))


# ================================================================== foam roller on the side
@x("foam-roll-lats")
def foam_roll_lats(c, t, L, row):
    """Lying on the right side with the roller under the armpit and the bottom arm straight overhead, feet on
    the floor: the body rolls slowly from the armpit down the side and back."""
    from .tpl_x54 import side_plank_x
    from .rig import body_rot
    roll = L(0.0, 0.14)
    arm_up = arm_fk((0.0, 0.05, 1.0), elbow=8, thumb="fwd", world=False, sides="R")
    fr = side_plank_x(c, t, L, hand_h=-0.13, drop=18.0, elev=0.0, top_arm="hip", arms_extra=arm_up)
    S, R = fr.sp_S, fr.sp_R
    return _with_eq(fr, [E("foam_roller", (S[0] - 0.05 - roll, 0.0, 0.0), R=fam.rz(90), eid="fr", dyn=True)])


@x("foam-roll-hip-abductors")
def foam_roll_abd(c, t, L, row):
    """On the right forearm with the roller under the outer right hip: the body rocks and rolls a few centimetres
    along the outer hip."""
    from .tpl_x54 import side_plank_x
    roll = L(-0.06, 0.06)
    fr = side_plank_x(c, t, L, drop=30.0, elev=0.0)
    S, R = fr.sp_S, fr.sp_R
    pel = S - R @ (c.r.joint("upperarm01.R") - c.r.pc_rest)
    return _with_eq(fr, [E("foam_roller", (pel[0] + roll, 0.0, 0.0), R=fam.rz(90), eid="fr", dyn=True)])


@x("single-leg-foam-roll-hip-thrust")
def sl_foam_thrust(c, t, L, row):
    """Shoulder blades on a bench, the right heel on a foam roller and the left leg lifted: the hips drive up and
    lower."""
    fr = REG["hip_thrust"].fn(c, t, L, dict(row, name_en="Single-Leg Hip Thrust", equipment="bench ; flat bench"))
    b0 = fr.build
    box = {}

    def build():
        spec, eq, ex = b0()
        Lg = spec["leg"].get("R")
        if isinstance(Lg, dict) and "ball" in Lg:
            b = np.asarray(Lg["ball"], float) + np.array([0, 0.02, 0.15])
            Lg["ball"] = b
            Lg["surf"] = 0.15
            Lg["heel"] = -10
            box["fr"] = b
        eq = list(eq) + [E("foam_roller", (box.get("fr", np.zeros(3))[0] - 0.05, box.get("fr", np.zeros(3))[1] - 0.07, 0), eid="fr")]
        return spec, eq, ex
    fr.build = build
    return fr


# ================================================================== prone and inverted
@x("reverse-leg-crossover")
def rev_leg_crossover(c, t, L, row):
    """Face down with the arms out to the sides: the right knee bends and the hips turn so the right foot swings
    behind the body toward the left hand, then back (alternating legs)."""
    k = L(0.0, 1.0)
    legs = legs_fk((0.06, -1.0, 0.0), knee=4, kbend=(0, 0, 1), fdir=(0, -0.2, -1))
    legs["R"] = dict(thigh=unit(np.array([0.1 - 0.75 * k, -1.0 + 0.4 * k, 0.15 + 0.45 * k])), knee=10 + 80 * k,
                     kbend=unit(np.array([-0.2 * k, 0, 1.0])), fdir=np.array([-0.5 * k, -0.3, -0.8]))
    arms = arm_fk((1.0, 0.0, -0.05), elbow=5, thumb="fwd", world=True)
    return fam.floor_body(c, pitch=90, roll=L(0, 28), legs=legs, arms=arms, neck=(-8, 0, L(0, 20)), equip=[MAT(0.1)])


@x("handstand-walk")
def handstand_walk(c, t, L, row):
    """Kicked up to a handstand, body straight: short alternating steps forward on the hands (one hand shifts,
    the other follows; cycle of two steps)."""
    from .rig import body_rot
    s = t % 1.0
    hw = c.sw * 1.15
    step = 0.12
    # hand y over the loop: right steps (0-0.25), left follows (0.25-0.5), then both walk on (the camera follows)
    def hy(sd):
        if sd == "R":
            u = min(1.0, max(0.0, s / 0.25)) if s < 0.5 else 1.0 + min(1.0, max(0.0, (s - 0.5) / 0.25))
        else:
            u = min(1.0, max(0.0, (s - 0.25) / 0.25)) if s < 0.75 else 1.0 + min(1.0, max(0.0, (s - 0.75) / 0.25))
        return u * step
    yb = 0.5 * (hy("L") + hy("R"))
    lift = {sd: 0.05 * math.sin(math.pi * ((hy(sd) / step) % 1.0)) for sd in "LR"}
    sz = c.Lpf * 0.94
    sh_r = c.r.joint("upperarm01.R")
    sh_mid_r = np.array([0, sh_r[1], sh_r[2]])
    R = body_rot(180, 0, 0)
    S = np.array([0, -0.02 + yb - step, sz])
    pel = S - R @ (sh_mid_r - c.r.pc_rest)
    arms = arm_ik(lambda D, Hp, c_, sd: np.array([SIDES[sd] * hw / 2, hy(sd) - step, 0.004 + lift[sd]]), (-1, 0.15, 0),
                  (0.25, 1.0, -0.2), curl=0.05, key="palm", fing=(0, 1, 0))
    legs = legs_fk((0.04, -0.12, 1), knee=6, kbend=(0, 1, 0), fdir=(0, -0.3, 1))
    fr = c.stand(legs, pz=pel[2], py=pel[1], pel=(172, 0, 0), neck=(-25, 0, 0), arms=arms, balance=None,
                 reach=False, planted=(), equip=[E("mat", (0, -0.2 - yb, 0), eid="mat")])
    fr.cons.append(("reach_arms", -Z, ["L", "R"]))
    return fr


@x("reverse-lunge-with-half-kneeling-pallof-press")
def rev_lunge_pallof(c, t, L, row):
    """Side-on to a pulley at chest height, the handle at the chest: the leg nearest the machine steps back into a
    lunge, at the bottom the handle presses straight out and holds, comes back, and the front foot drives up."""
    from .tpl_x54 import _lunge_keys
    up, bottom = _lunge_keys(c, depth=0.95)
    K = _keys([(0.0, up), (0.35, bottom), (0.65, bottom), (1.0, up)])
    kv = _interp(K, min(t, 0.9999) if t < 1 else 0.9999)
    p = 0.0 if t < 0.35 or t > 0.65 else math.sin(math.pi * (t - 0.35) / 0.3)
    pul = np.array([-1.1, 0.0, 1.1])

    def tgt(D, Hp, c_, sd):
        ch = c.lmk(D, Hp, "chest") + Y * 0.12
        return ch + Y * (c.Lh * 0.75 * p) + X * SIDES[sd] * 0.02
    arms = arm_ik(tgt, (0, 0, 1), lambda D, Hp, c_, sd: np.array([SIDES[sd] * 0.8, -0.3, -0.6]), curl=0.9)
    eq = [H("d_handle", "C", "db", eid="dh"), E("cable_tower", (pul[0] - 0.12, 0, 0), R=fam.rz(-90), eid="tower", pulley_h=pul[2]),
          seg("cable", pul, "gripC", 0.0045, "darksteel")]
    return keyed_stand(c, kv, arms=arms, equip=eq)


# ================================================================== partner exercises (second person in tpl PARTNER)
def _hands_mid(pose, c):
    a = joint(pose, c, "finger3-1.L")
    b = joint(pose, c, "finger3-1.R")
    return 0.5 * (a + b)


@x("partner-pallof-twist")
def partner_pallof(c, t, L, row):
    """Standing side-on to the partner, who holds the other end of the band at chest height: the hands press
    straight out from the chest, hold, and come back."""
    def tgt(D, Hp, c_, sd):
        Rt = D[c.r.bi("spine01")]
        a = c.lmk(D, Hp, "chest") + Rt @ Y * 0.1
        b = fam.within(c, fam.sh_mid(D, Hp, c), Rt @ Y * c.Lh * 0.95 - Rt @ Z * 0.12, 0.9)
        return a * (1 - L(0, 1)) + b * L(0, 1) + Rt @ X * SIDES[sd] * 0.03
    arms = arm_ik(tgt, lambda D, Hp, c_, sd: D[c.r.bi("spine01")] @ Z, (1, -0.5, -0.4), curl=0.9)
    legs = c.feet(w=c.hw * 1.5, toe=8)
    return c.stand(legs, hk=0.94, pel=(6, 0, 0), arms=arms)


@partner("partner-pallof-twist")
def _p_pallof(c, t, L, row):
    main = row["_main"]
    yaw, off = 90.0, np.array([1.55, 0.25, 0.0])
    hm = local(_hands_mid(main, c), yaw, off)

    def tgt(D, Hp, c_, sd):
        return c.lmk(D, Hp, "chest") + Y * 0.3 + X * SIDES[sd] * 0.03 - Z * 0.05
    arms = arm_ik(tgt, (0, 0, 1), (1, -0.4, -0.6), curl=0.9)
    legs = c.feet(w=c.hw * 1.4, toe=8)
    for sd in legs:
        legs[sd]["ball"] = np.asarray(legs[sd]["ball"]) + np.array([0, -0.1 if sd == "L" else 0.12, 0])
    fr = c.stand(legs, hk=0.93, pel=(-4, 0, 0), arms=arms,
                 equip=[seg("band", ("gripR", (0, 0, 0)), hm, 0.008, "band")])
    return fr, yaw, off


def _run_legs(c, s, stride=0.6):
    return {"R": dict(thigh=np.array([0.05, stride * s, -1]), knee=20 + 70 * max(0, -s), kbend=np.array([0, -1, 0])),
            "L": dict(thigh=np.array([-0.05, -stride * s, -1]), knee=20 + 70 * max(0, s), kbend=np.array([0, -1, 0]))}


@x("partner-band-sprint")
def partner_band_sprint(c, t, L, row):
    """A band round the waist, the partner holding both ends behind: a hard forward-leaning sprint against the
    light resistance (cycle of one stride)."""
    s = math.cos(2 * math.pi * t)
    legs = _run_legs(c, s, 0.75)
    arms = {"R": arm_fk((0.1, -0.6 * s, -0.75), elbow=95, sides="R")["R"],
            "L": arm_fk((0.1, 0.6 * s, -0.75), elbow=95, sides="L")["L"]}
    fr = c.stand(legs, pz=c.pz * 0.95 + 0.04 * abs(math.sin(2 * math.pi * t)), pel=(24, 0, 0), arms=arms, balance=None,
                 reach=False, planted=(), settle=[("floor", 0.005)])
    return fr


@partner("partner-band-sprint")
def _p_band_sprint(c, t, L, row):
    main = row["_main"]
    yaw, off = 0.0, np.array([0.0, -1.45, 0.0])
    s = math.cos(2 * math.pi * t + 1.2)
    hips = [local(joint(main, c, f"upperleg01.{sd}") + np.array([0, 0.0, 0.05]), yaw, off) for sd in "LR"]
    legs = _run_legs(c, s, 0.4)

    def tgt(D, Hp, c_, sd):
        m = fam.sh_mid(D, Hp, c)
        return m + Y * 0.42 - Z * 0.25 + X * SIDES[sd] * 0.14
    arms = arm_ik(tgt, (0, 1, 0), (1, -0.6, -0.4), curl=0.9)
    eq = [seg(f"band{sd}", (f"grip{sd}", (0, 0, 0)), hips[i], 0.008, "band") for i, sd in enumerate("LR")]
    eq.append(seg("bandW", hips[0], hips[1], 0.008, "band"))
    fr = c.stand(legs, pz=c.pz * 0.96, pel=(-6, 0, 0), arms=arms, balance=None, reach=False, planted=(),
                 settle=[("floor", 0.005)], equip=eq)
    return fr, yaw, off


@x("partner-wall-sit-and-triceps-dip")
def partner_wall_sit(c, t, L, row):
    """Holding a wall sit, thighs level, back flat on the wall (the partner dips on the knees in front)."""
    legs = c.feet(w=c.hw * 1.2, toe=10, y=0.5 * c.S)
    wall = np.array([0, -0.08, 0])
    fr = c.stand(legs, hk=0.5, pel=(-4, 0, 0), hold="none", balance=None, equip=[E("wall", wall, eid="wall")],
                 settle=[("plane", wall + np.array([0, 0, 1.2]), Y, X, 0.25, Z, 0.6, -0.002)])
    fr.cons = [cn for cn in fr.cons if cn[0] != "com"]
    return fr


@partner("partner-wall-sit-and-triceps-dip")
def _p_wall_dip(c, t, L, row):
    main = row["_main"]
    kn = {sd: joint(main, c, f"lowerleg01.{sd}") for sd in "LR"}
    ky = max(kn["L"][1], kn["R"][1])
    yaw, off = 0.0, np.array([0.0, ky + 0.12, 0.0])
    pts = {sd: local(kn[sd] + np.array([0, 0.02, 0.06]), yaw, off) for sd in "LR"}

    def tgt(D, Hp, c_, sd):
        return pts[sd]
    arms = arm_ik(tgt, (0, 1, 0), (SIDES["R"] * 0.2, -1, 0.2), key="palm", curl=0.4, fing=(0, 1, 0))
    legs = {sd: dict(ball=np.array([SIDES[sd] * 0.16, 0.95, SOLE]), yaw=6, heel=0, pole=np.array([0, 1, 0.4])) for sd in "LR"}
    top = pts["R"][2] - 0.02
    fr = c.stand(legs, pz=L(top - 0.06, top - 0.32), py=0.12, pel=(L(4, 10), 0, 0), arms=arms, balance=None, reach=False)
    fr.cons.append(("reach_arms", -Z, ["L", "R"]))
    return fr, yaw, off


@x("partner-plank-hold-and-jump")
def partner_plank_jump(c, t, L, row):
    """Holding a forearm plank while the partner jumps sideways over the lower legs and back."""
    return fam.plank(c, down=0.0, elbows=True, equip=[MATP()], neck=(-10, 0, 0))


@partner("partner-plank-hold-and-jump")
def _p_plank_jump(c, t, L, row):
    main = row["_main"]
    sh = [joint(main, c, f"lowerleg02.{sd}") for sd in "LR"]
    sy = 0.5 * (sh[0][1] + sh[1][1])
    yaw, off = 0.0, np.array([0.0, sy - c.ball_y - 0.05, 0.0])
    d = 0.45
    w = c.hw * 0.45
    z = c.pz
    sq = dict(pitch=22, ua=(0.15, -0.3, -0.9), el=20)
    K = _keys([
        (0.00, dict(fL=(-d - w, 0, 0), fR=(-d + w, 0, 0), pz=z * 0.82, px=-d, **sq)),
        (0.25, dict(fL=(-w, 0, 0.32), fR=(w, 0, 0.32), gL=0, gR=0, hL=30, hR=30, pz=z * 0.96 + 0.3, px=0.0, pitch=6,
                    ua=(0.15, 0.5, 0.4), el=20)),
        (0.50, dict(fL=(d - w, 0, 0), fR=(d + w, 0, 0), pz=z * 0.82, px=d, **sq)),
        (0.75, dict(fL=(-w, 0, 0.32), fR=(w, 0, 0.32), gL=0, gR=0, hL=30, hR=30, pz=z * 0.96 + 0.3, px=0.0, pitch=6,
                    ua=(0.15, 0.5, 0.4), el=20)),
        (1.00, dict(fL=(-d - w, 0, 0), fR=(-d + w, 0, 0), pz=z * 0.82, px=-d, **sq)),
    ])
    kv = _interp(K, min(t % 1.0, 0.9999))
    return keyed_stand(c, kv), yaw, off


@x("partner-rolling-ball-push-up")
def partner_ball_push(c, t, L, row):
    """Two people face each other in push-up positions: one does a push-up and rolls the ball across to the
    other, who stops it, does a push-up and rolls it back (cycle)."""
    s = t % 1.0
    dn = 0.9 * math.sin(math.pi * s / 0.35) if s < 0.35 else 0.0
    gap = 1.75
    hw = c.sw * 1.15
    a = np.array([hw / 2 + 0.16, 0.05, 0.115])
    b = np.array([-(hw / 2 + 0.16), gap - 0.05, 0.115])
    if s < 0.35:
        bp = a
    elif s < 0.5:
        u = (s - 0.35) / 0.15
        bp = a * (1 - u) + b * u
    elif s < 0.85:
        bp = b
    else:
        u = (s - 0.85) / 0.15
        bp = b * (1 - u) + a * u
    return fam.plank(c, down=dn, hand_w=hw, equip=[MATP(), E("medball", tuple(bp), eid="mb", dyn=True)], neck=(-12, 0, 0),
                     hands_on=True)


@partner("partner-rolling-ball-push-up")
def _p_ball_push(c, t, L, row):
    s = t % 1.0
    dn = 0.9 * math.sin(math.pi * (s - 0.5) / 0.35) if 0.5 <= s < 0.85 else 0.0
    return fam.plank(c, down=dn, hand_w=c.sw * 1.15, equip=[], neck=(-12, 0, 0), hands_on=True), 180.0, np.array([0.0, 1.75, 0.0])


def _wheelbarrow(c, t, L, row, walk):
    fh = 0.78
    if walk:
        s = t % 1.0
        hw = c.sw * 1.1
        step = 0.16

        def hy(sd):
            u = min(1.0, max(0.0, s / 0.5)) if sd == "R" else min(1.0, max(0.0, (s - 0.5) / 0.5))
            return u * step - step / 2

        def palm(D, Hp, c_, sd):
            return np.array([SIDES[sd] * hw / 2, hy(sd), 0.004 + 0.05 * math.sin(math.pi * (hy(sd) / step + 0.5))])
        arms_over = arm_ik(palm, (-1, 0.15, 0), (0.25, -1.0, 0.25), curl=0.05, key="palm", fing=(0, 1, 0))
        return fam.plank(c, down=0.0, hand_w=hw, feet_h=fh, feet_w=0.32 * c.S, arms_over=arms_over, hands_on=True,
                         neck=(-14, 0, 0))
    return fam.plank(c, down=L(0.0, 0.85), feet_h=fh, feet_w=0.32 * c.S, hands_on=True, neck=(-14, 0, 0))


@x("partner-wheelbarrow-push-up")
def partner_wb_push(c, t, L, row):
    """Push-up with the ankles held up at hip height by the partner standing behind: the chest lowers close to the
    floor and pushes back up."""
    return _wheelbarrow(c, t, L, row, False)


@x("partner-wheelbarrow-walk")
def partner_wb_walk(c, t, L, row):
    """Push-up position with the ankles held up by the partner: the hands walk forward in short steps while the
    partner follows (cycle of two hand steps)."""
    return _wheelbarrow(c, t, L, row, True)


@partner("partner-wheelbarrow-push-up", "partner-wheelbarrow-walk")
def _p_wheelbarrow(c, t, L, row):
    main = row["_main"]
    ank = {sd: joint(main, c, f"foot.{sd}") for sd in "LR"}
    fy = min(ank["L"][1], ank["R"][1])
    yaw, off = 0.0, np.array([0.0, fy - 0.42, 0.0])
    pts = {sd: local(ank[sd] - np.array([0, 0.03, 0.0]), yaw, off) for sd in "LR"}
    walk = row["key"].endswith("walk")
    s = math.sin(2 * math.pi * t) if walk else 0.0

    def tgt(D, Hp, c_, sd):
        return pts[sd]
    arms = arm_ik(tgt, (0, 1, 0), lambda D, Hp, c_, sd: np.array([SIDES[sd] * 0.7, -0.5, -0.5]), curl=0.9)
    legs = c.feet(w=c.hw * 1.2, toe=8)
    if walk:
        legs["R"] = dict(legs["R"], ball=np.asarray(legs["R"]["ball"]) + np.array([0, 0.1 * s, 0]))
        legs["L"] = dict(legs["L"], ball=np.asarray(legs["L"]["ball"]) + np.array([0, -0.1 * s, 0]))
    fr = c.stand(legs, hk=0.97, pel=(8, 0, 0), arms=arms, balance=None)
    return fr, yaw, off
