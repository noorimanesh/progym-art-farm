"""v3 archetypes: set-ups read from the move row's data (spec3.P) instead of
words in the name.  Registered after the older template modules, so a name
defined here replaces the older one."""
from .templates import tpl, E, H, seg, PLATE_R, X, Y, Z, np, math, SIDES, rz
from .poses import SOLE, PAD_SINK, SKIN_FLOOR
from .rig import unit, orth, rot, body_rot
from . import fam, kit
from .fam import arm_fk, arm_ik, legs_fk, press_bar, press_db, supine_on_bench, BENCH_H
from .spec3 import P
from .tpl_lower import eqw, has, platform


def words(row):
    return eqw(row)


def bench_of(row, default="flat"):
    """(kind, angle) from the data, falling back to words."""
    b = P(row, "bench")
    if b:
        ang = float(P(row, "bench_angle", {"incline": 30, "decline": 18, "upright": 82}.get(b, 0)))
        return b, ang
    n = words(row)
    if "incline" in n:
        return "incline", 45.0 if "45" in n else 30.0
    if "decline" in n:
        return "decline", 18.0
    if "floor" in n:
        return "floor", 0.0
    return default, 0.0


def width_of(row, c, default):
    w = P(row, "width")
    if w is None:
        n = words(row)
        w = "close" if "close" in n or "narrow" in n else ("wide" if "wide" in n else None)
    if isinstance(w, (int, float)):
        return c.sw * float(w)
    return c.sw * {"close": 1.0, "narrow": 1.0, "shoulder": 1.35, "wide": 2.05}.get(w, default)


def grip_of(row, default="pro"):
    g = P(row, "grip")
    if g:
        return g
    n = words(row)
    if "reverse" in n or "underhand" in n or "supinated" in n:
        return "sup"
    if "neutral" in n or "hammer" in n:
        return "neutral"
    return default


# ================================================================== bench presses
@tpl("bench_press", (58, 26))
def bench_press(c, t, L, row):
    kind, ang = bench_of(row)
    gw = width_of(row, c, 1.75)
    grip = grip_of(row)
    smith = has(row, "smith")
    arms, eq = press_bar(c, L(0, 1), "bench", gw=gw, grip="sup" if grip == "sup" else "pro",
                         bar="smith_bar" if smith else "barbell")
    extra = []
    if smith:
        extra.append(E("smith", (0, -0.05, 0), eid="smith"))
    elif kind != "floor" and P(row, "rack", True):
        extra.append(kit.bench_rack_for(kind, ang, 0.0, c))
    return supine_on_bench(c, kind, ang, arms=arms, hold_eq=eq, extra_eq=extra,
                           legs="decline" if kind == "decline" else "floor")


@tpl("db_bench_press", (70, 16))
def db_bench_press(c, t, L, row):
    kind, ang = bench_of(row)
    n = words(row)
    squeeze = "squeeze" in n or "svend" in n
    neutral = grip_of(row) == "neutral" or squeeze
    arms, eq = press_db(c, L(0, 1), "bench", w0=c.sw * (0.6 if squeeze else 1.55),
                        w1=c.sw * (0.55 if squeeze else 0.95), thumb_mode="neutral" if neutral else "pro")
    if "kettlebell" in n:
        eq = [H("kettlebell", "L", "kb_up"), H("kettlebell", "R", "kb_up")]
    return supine_on_bench(c, kind, ang, arms=arms, hold_eq=eq, legs="decline" if kind == "decline" else "floor")


# ================================================================== band drills
@tpl("band_pull_apart", (25, 10))
def band_pull_apart(c, t, L, row):
    """Band held at shoulder height with straight arms, pulled apart to a T."""
    n = words(row)
    over = "overhead" in n
    legs = c.feet(w=c.hw * 1.1, toe=8)
    legs, peq = platform(c, row, legs)
    a = L(0.0, 1.0)
    if over:
        v = lambda a: (0.18 + 0.75 * a, 0.12, 1.0 - 0.75 * a)
    else:
        v = lambda a: (0.13 + 0.87 * a, 1.0 - 0.95 * a, 0.06)
    grip = grip_of(row, "pro")
    arms = arm_fk(v(a), elbow=6, thumb="up" if grip == "neutral" else (0, 0, -1) if grip == "sup" else "in",
                  bend=(0, 0, 1) if not over else (0, 1, 0), curl=0.85,
                  fing=None)
    return c.stand(legs, pel=(2, 0, 0), arms=arms, equip=peq + kit.band_between_hands())


# ================================================================== quad stretch
@tpl("quad_stretch_standing", (70, 8))
def quad_stretch_standing(c, t, L, row):
    k = L(150, 157)
    legs = {"R": c.foot(c.hw * 0.3, 0, 6),
            "L": dict(thigh=np.array([-0.04, L(0.06, -0.04), -1]), knee=k, kbend=np.array([0, -1, 0]),
                      fdir=np.array([0, -0.35, 1.0]))}

    def holdL(D, Hp, c_):
        r = c.r
        a = c.J(D, Hp, "foot.L")
        Rf = D[r.bi("foot.L")]
        return dict(grip=a + Rf @ np.array([0, 0.0, 0.03]), thumb=Y, fing=-Z, pole=-Y + Z * 0.2 - X * 0.3,
                    curl=0.8)
    arms = {"L": holdL, "R": arm_fk((0.75, 0.3, -0.35), elbow=12, thumb="fwd", sides="R")["R"]}
    if has(row, "wall"):
        arms["R"] = lambda D, Hp, c_: dict(palm=np.array([0.55, 0.05, 1.25 * c.S]), thumb=Y, fing=Z, pole=-Y,
                                           curl=0.0)
    return c.stand(legs, hk=0.99, pel=(L(4, 0), 0, 0), arms=arms, planted=("R",), balance="com",
                   neck=(-4, 0, 0))


# ================================================================== cable rows
@tpl("cable_row", (82, 10))
def cable_row(c, t, L, row):
    """Seated cable row: long seat, feet on the plate, cable from the low
    front pulley to the handle at the stomach."""
    n = words(row)
    attach = P(row, "attach") or ("bar" if "wide" in n or "straight bar" in n else ("d" if "one-arm" in n or "single" in n else "v"))
    single = attach == "d" or "one-arm" in n or "single" in n
    seat_h = 0.42
    pul = np.array([0, 1.08, 0.42])
    gw = c.sw * (1.45 if attach == "bar" else 0.38)

    def tgt(D, Hp, c_, sd):
        m = fam.sh_mid(D, Hp, c)
        sh = fam.shoulder(D, Hp, c, sd)
        lat = X * SIDES[sd] * (gw / 2 if not single else 0.1)
        # arms long in front (within reach of the shoulder), handle pulled to the stomach
        far = fam.within(c, sh, (m + lat + unit(np.array([0, 1, -0.32])) * c.Lh * 0.97) - sh, 0.93)
        near = c.lmk(D, Hp, "chest") - Z * 0.13 + Y * 0.07 + lat
        return far * (1 - L(0, 1)) + near * L(0, 1)
    thumb = (0, 0, 1) if attach in ("v", "d") else None
    sides = "R" if single else "LR"
    arms = arm_ik(tgt, thumb if thumb else (lambda D, Hp, c_, sd: -SIDES[sd] * X),
                  lambda D, Hp, c_, sd: X * SIDES[sd] * 0.35 - Z * 0.9 - Y * 0.2,
                  curl=0.9, fing=lambda D, Hp, c_, sd: -Z * 0.2 + Y * 0.3 - X * SIDES[sd] * 0.1 if attach in ("v", "d")
                  else -Z, sides=sides)
    if single:
        arms.update(arm_ik(lambda D, Hp, c_, sd: 0.4 * c.J(D, Hp, "upperleg02.L") + 0.6 * c.J(D, Hp, "lowerleg01.L")
                           + Z * 0.075,
                           (0, 1, 0), (-1, -0.3, -0.3), key="palm", curl=0.3, sides="L"))
    lg = {}
    for sd in "LR":
        s = SIDES[sd]
        lg[sd] = dict(ankle=np.array([s * 0.13, 0.7, 0.24]), fdir=np.array([0, 0.42, 0.9]),
                      fup=np.array([0, -0.9, 0.42]), pole=np.array([s * 0.15, 0.3, 1.0]))
    eq = [E("row_station", (0, 0, 0), eid="rs", pulley_h=pul[2], seat_h=seat_h)]
    eq += kit.cable_kit(pul, attach, sides="R" if single else "C", tower=False)
    fr = fam.seated(c, seat_h=seat_h, seat_y=-0.15, pitch=L(14, -4), arms=arms, legs=lg, equip=eq, planted=(),
                    spine=(L(6, -4), 0, 0), neck=(L(-6, 2), 0, 0))
    return fr


# ================================================================== wrappers around older archetypes
from .templates import REG as _REG  # noqa: E402
_REG_OLD = {k: v.fn for k, v in _REG.items()}


def _wrap_build(fr, post):
    b = fr.build

    def build():
        spec, eq, ex = b()
        eq = post(spec, eq, ex)
        return spec, eq, ex
    fr.build = build
    return fr


_old_lat = _REG["lat_pulldown"].fn


@tpl("lat_pulldown", (78, 8))
def lat_pulldown(c, t, L, row):
    n = words(row)
    fr = _old_lat(c, t, L, row)
    attach = P(row, "attach") or ("v" if "v-bar" in n or "close" in n or "neutral" in n else
                                  ("d" if "single" in n or "one-arm" in n else "lat"))
    if "band" in n:
        return fr
    pul = np.array([0, 0.12, 2.25])

    def post(spec, eq, ex):
        eq = [e for e in eq if e["kind"] not in ("barbell", "machine_handles", "_seg")]
        sd = "R" if attach == "d" else "C"
        return eq + kit.cable_kit(pul, attach, sides=sd, tower=False)
    return _wrap_build(fr, post)


_old_cross = _REG["cable_crossover"].fn


@tpl("cable_crossover", (24, 12))
def cable_crossover(c, t, L, row):
    n = words(row)
    fr = _old_cross(c, t, L, row)
    if "band" in n:
        return fr
    pz = {"low": 0.15, "mid": 1.25, "high": 2.1 * c.S}.get(P(row, "pulley") or (
        "low" if "low" in n else ("mid" if "mid" in n else "high")))
    single = "single" in n or "one-arm" in n
    pulleys = {sd: np.array([SIDES[sd] * 1.05, -0.05, pz]) for sd in ("R" if single else "LR")}

    def post(spec, eq, ex):
        eq = [e for e in eq if e["kind"] not in ("_seg",)]
        for sd, p in pulleys.items():
            eq += kit.cable_kit(None, "d", sides=sd, tower=False, pulleys={sd: p}, eid=f"x{sd}")
        return eq
    return _wrap_build(fr, post)


_old_mcp = _REG["machine_chest_press"].fn


@tpl("machine_chest_press", (70, 10))
def machine_chest_press(c, t, L, row):
    """Selectorised seated press: seat, back pad, lever arms from pivots
    behind the shoulders to the handles."""
    n = words(row)
    shoulder = "shoulder" in n
    fr = _old_mcp(c, t, L, row)

    def post(spec, eq, ex):
        eq = [e for e in eq if e["kind"] not in ("seat_machine",)]
        eq.append(E("press_machine", (0, 0, 0), eid="pm", seat_h=0.47 * c.S))
        for sd in "LR":
            s = SIDES[sd]
            if shoulder:
                piv = np.array([s * 0.42, -0.3, 1.75])
                elbow = None
            else:
                piv = np.array([s * 0.46, -0.38, 1.55])
                elbow = np.array([s * 0.5, 0.05, 1.2])
            eq += kit.lever(piv, sd, eid="arm", elbow=elbow)
        return eq
    return _wrap_build(fr, post)


# ================================================================== leg machines with moving levers
def _shin_pad(front=True, up=0.07, side=None):
    """Callable point on the shins (both legs averaged, or one side): above
    the ankle by `up`, in front of (or behind) the shin."""
    def f(pts, D, Hp, c, k=0.0):
        sides = [side] if side else ["L", "R"]
        acc = np.zeros(3)
        for sd in sides:
            K = Hp[c.r.bi(f"lowerleg01.{sd}")]
            A = Hp[c.r.bi(f"foot.{sd}")]
            sh = unit(K - A)
            fwd = orth(Y if front else -Y, sh)
            nrm = unit(np.cross(X, sh))      # sagittal normal of the shin (points to the shin front)
            if np.dot(nrm, fwd) < 0:
                nrm = -nrm
            acc += A + sh * up + nrm * 0.075
        p = acc / len(sides)
        return p
    return f


def _lever_parts(pad_fn, pivot, eid="lev", half=0.19):
    """Pad roller across the shins + lever arm from the pivot to the pad."""
    piv = np.asarray(pivot, float)

    def pad_a(pts, D, Hp, c):
        return pad_fn(pts, D, Hp, c) + X * -half

    def pad_b(pts, D, Hp, c):
        return pad_fn(pts, D, Hp, c) + X * half

    def arm_end(pts, D, Hp, c):
        p = pad_fn(pts, D, Hp, c)
        return np.array([piv[0], p[1], p[2]])
    return [seg(f"{eid}pad", pad_a, pad_b, 0.05, "pad"),
            seg(f"{eid}arm", piv, arm_end, 0.022, "darksteel"),
            seg(f"{eid}stub", arm_end, pad_b, 0.018, "darksteel")]


def _leg_machine(c, t, L, row, curl=False):
    n = words(row)
    single = "single" in n or "one-leg" in n or "single-leg" in n
    seat_y, seat_h = -0.24, 0.51
    k0, k1 = (8, 100) if curl else (92, 5)

    def lg(sd, ang):
        return dict(thigh=np.array([SIDES[sd] * 0.08, 1.0, -0.02]), knee=ang, kbend=np.array([0, 0, -1]),
                    fdir=np.array([0, 0.3, 1]) if not curl else np.array([0, 0.8, 0.6]))
    legs = {"R": lg("R", L(k0, k1)), "L": lg("L", k0 if single else L(k0, k1))}
    arms = arm_ik(lambda D, Hp, c_, sd: np.array([SIDES[sd] * 0.245 * c.S, seat_y + 0.05, 0.5]), (0, 1, 0),
                  (1, -0.3, 0), curl=0.85)
    eq = [E("leg_curl_seated" if curl else "leg_machine", (0, 0, 0), eid="lm")]
    fr = fam.seated(c, seat_h=seat_h, seat_y=seat_y, legs=legs, arms=arms, equip=eq, planted=(),
                    back=(np.array([0, -0.48, 0.82]), np.array([0, 1, 0.2])))

    def post(spec, eqs, ex):
        r = c.r
        pivot = np.array([0.33, 0.0, 0.5])
        return eqs + _lever_parts(_shin_pad(front=not curl, up=0.08, side="R" if single else None), pivot)
    return _wrap_build(fr, post)


@tpl("leg_extension", (72, 8))
def leg_extension(c, t, L, row):
    if has(row, "band"):
        return _REG_OLD["leg_extension"](c, t, L, row)
    return _leg_machine(c, t, L, row, curl=False)


@tpl("seated_leg_curl", (72, 8))
def seated_leg_curl(c, t, L, row):
    return _leg_machine(c, t, L, row, curl=True)


# ================================================================== preacher curl
@tpl("preacher_curl", (80, 6))
def preacher_curl(c, t, L, row):
    n = words(row)
    single = "single" in n or "one-arm" in n or "concentration" in n
    seat_h = 0.585
    arms = arm_fk((0.07, 0.62, -0.78), elbow=L(12, 128), thumb="sup", bend=(0, 0.6, 0.8), curl=0.88, world=True)
    eq = [H("ezbar", "C", "bar", eid="bar")] if "barbell" not in n else [H("barbell", "C", "bar", eid="bar", plate_r=0.15)]
    if "dumbbell" in n or single:
        eq = [H("dumbbell", "L"), H("dumbbell", "R")]
    extra = []
    if "cable" in n:
        eq = []
        extra = kit.cable_kit(np.array([0, 0.95, 0.3]), "bar", face=np.array([0, -1, 0]))
    if "machine" in n:
        eq = [H("machine_handles", "C", "ball", eid="hnd", width=0.0)]
    if single:
        arms["L"] = arm_fk((0.15, 0.45, -0.85), elbow=25, sides="L", world=True, thumb="sup")["L"]
        eq = [H("dumbbell", "R")]
    feet = {sd: dict(ball=np.array([SIDES[sd] * 0.13, 0.33 + c.ball_y * 0, 0.13 + SOLE]), yaw=8, heel=0, surf=0.13,
                     pole=np.array([SIDES[sd] * 0.2, 1, 0.5])) for sd in "LR"}
    return fam.seated(c, seat_h=seat_h, seat_y=0.0, pitch=16, arms=arms, legs=feet,
                      equip=eq + extra + [E("preacher", (0, 0, 0), eid="pb", height=0.55, foot=0.13, foot_y=0.36)],
                      spine=(10, 0, 0), neck=(L(-8, -14), 0, 0))


# ================================================================== key-framed full-body moves
def _interp(keys, u):
    """keys: list of (time, dict); values interpolated with ease between
    neighbouring keys; u wraps for cyclic moves."""
    from .motion import ease
    u = u % 1.0 if keys[-1][0] <= 1.0 else u
    for (t0, a), (t1, b) in zip(keys[:-1], keys[1:]):
        if t0 <= u <= t1:
            w = ease((u - t0) / max(t1 - t0, 1e-9))
            out = {}
            for k in a:
                va, vb = a[k], b.get(k, a[k])
                if isinstance(va, (tuple, list, np.ndarray)):
                    out[k] = np.asarray(va, float) * (1 - w) + np.asarray(vb, float) * w
                else:
                    out[k] = va * (1 - w) + vb * w
            return out
    return dict(keys[-1][1])


def keyed_stand(c, kv, equip=(), arms=None):
    """Standing / jumping body from interpolated key values:
    fL, fR: ball xyz; hL, hR: heel lift deg; pz, py: pelvis; pitch; ua: right
    arm direction (body frame); el: elbow; neck."""
    legs = {}
    for sd in "LR":
        b = np.asarray(kv["f" + sd], float)
        legs[sd] = dict(ball=b + np.array([0, c.ball_y, SOLE]), yaw=8, heel=float(kv.get("h" + sd, 0.0)),
                        surf=float(kv.get("s" + sd, b[2])))
    planted = [sd for sd in "LR" if kv.get("g" + sd, 1.0) > 0.5]
    if arms is None:
        arms = arm_fk(tuple(kv["ua"]), elbow=float(kv.get("el", 15)), thumb="neutral", bend=(0, 1, 1), curl=0.4)
    fr = c.stand(legs, pz=float(kv["pz"]), py=float(kv.get("py", 0.0)), px=float(kv.get("px", 0.0)),
                 pel=(float(kv["pitch"]), 0, 0),
                 neck=(float(kv.get("neck", 0.0)), 0, 0), spine=(float(kv.get("spine", 0.0)), 0, 0), arms=arms,
                 balance=None, reach=False, planted=planted, equip=list(equip))
    return fr


@tpl("box_jump", (82, 8), fast=True)
def box_jump(c, t, L, row):
    """Cyclic: dip, jump, land softly on the box, stand, step down backward."""
    bh = float(P(row, "box_h", 0.5 * c.S))
    d = P(row, "dir", "fwd")
    dist = 0.62 * c.S if d == "fwd" else (0.55 * c.S if d == "lat" else -0.6 * c.S)
    ax = np.array([1.0, 0.0]) if d == "lat" else np.array([0.0, 1.0])
    by = dist
    w = c.hw * 0.6
    z0 = c.pz
    sq = lambda k: c.pz * k
    K = [
        (0.00, dict(fL=(-w, 0, 0), fR=(w, 0, 0), pz=sq(0.97), py=0.0, pitch=4, ua=(0.12, 0.1, -1), el=15, neck=0)),
        (0.14, dict(fL=(-w, 0, 0), fR=(w, 0, 0), pz=sq(0.72), py=-0.04, pitch=38, ua=(0.15, -0.55, -0.8), el=10, neck=-20)),
        (0.26, dict(fL=(-w, by * 0.35, 0.16), fR=(w, by * 0.35, 0.16), hL=45, hR=45, gL=0, gR=0, pz=sq(0.99) + 0.2, py=by * 0.4,
                    pitch=8, ua=(0.12, 0.9, 0.35), el=20, neck=-5)),
        (0.38, dict(fL=(-w, by, bh), fR=(w, by, bh), pz=sq(0.7) + bh, py=by - 0.04, pitch=34, ua=(0.15, 0.8, -0.2), el=25,
                    neck=-15, sL=bh, sR=bh)),
        (0.52, dict(fL=(-w, by, bh), fR=(w, by, bh), pz=sq(0.97) + bh, py=by, pitch=3, ua=(0.12, 0.1, -1), el=15, neck=0,
                    sL=bh, sR=bh)),
        (0.68, dict(fL=(-w, by, bh), fR=(w, 0.0, 0.0), sL=bh, sR=0, pz=sq(0.9) + bh * 0.62, py=by * 0.45, pitch=10,
                    ua=(0.12, 0.1, -1), el=15, neck=-5)),
        (0.84, dict(fL=(-w, 0.0, 0.0), fR=(w, 0.0, 0.0), pz=sq(0.97), py=0.02, pitch=4, ua=(0.12, 0.1, -1), el=15,
                    neck=0)),
        (1.00, dict(fL=(-w, 0, 0), fR=(w, 0, 0), pz=sq(0.97), py=0.0, pitch=4, ua=(0.12, 0.1, -1), el=15, neck=0)),
    ]
    for _, d in K:
        for k in ("hL", "hR", "gL", "gR", "sL", "sR"):
            d.setdefault(k, {"gL": 1.0, "gR": 1.0}.get(k, 0.0))
    kv = _interp(K, t)
    # the stepping foot clears the box edge
    if 0.52 < t % 1 < 0.68:
        kv["fR"] = kv["fR"] + np.array([0, 0, 0.06 * math.sin(math.pi * (t - 0.52) / 0.16)])
        kv["gR"] = 0
    if d == "lat":       # same jump travelling sideways (+X): swap the travel axis
        for k in ("fL", "fR"):
            v = np.asarray(kv[k], float)
            kv[k] = np.array([v[0] + v[1], 0.0, v[2]])
        kv["px"], kv["py"] = kv.get("py", 0.0), 0.0
        kv["pitch"] = min(kv["pitch"], 30)
        box = E("plyo_box", (by + 0.3, 0, 0), R=rz(90), eid="box", size=(0.6, 0.5, bh))
    else:
        box = E("plyo_box", (0, by + (0.05 if by > 0 else -0.05), 0), eid="box", size=(0.6, 0.5, bh))
    return keyed_stand(c, kv, equip=[box])


_old_bbcurl = _REG["barbell_curl"].fn


@tpl("barbell_curl", (55, 8))
def barbell_curl(c, t, L, row):
    fr = _old_bbcurl(c, t, L, row)

    def post(spec, eq, ex):   # curls use a lighter bar: smaller plates
        out = []
        for e in eq:
            if e["kind"] == "barbell":
                e = dict(e, shape=dict(e.get("shape", {}), plate_r=0.16))
            out.append(e)
        return out
    return _wrap_build(fr, post)


# ================================================================== standing band row
@tpl("standing_band_row", (70, 10))
def standing_band_row(c, t, L, row):
    """Facing a band anchored at chest height, row the handles to the stomach."""
    n = words(row)
    single = "one-arm" in n or "single" in n
    legs = c.feet(w=c.hw * 1.15, toe=8, split=0.0)
    legs, peq = platform(c, row, legs)
    anchor = np.array([0, 1.25, 1.05 * c.S])

    def tgt(D, Hp, c_, sd):
        m = fam.sh_mid(D, Hp, c)
        far = m + unit(np.array([0, 1, -0.25])) * c.Lh * 0.96
        near = c.lmk(D, Hp, "chest") - Z * 0.12 + Y * 0.08
        return far * (1 - L(0, 1)) + near * L(0, 1) + X * SIDES[sd] * 0.13
    sides = "R" if single else "LR"
    arms = arm_ik(tgt, (0, 0, 1), lambda D, Hp, c_, sd: X * SIDES[sd] * 0.4 - Z * 0.9 - Y * 0.2, curl=0.9,
                  fing=(0, 0.3, -0.2), sides=sides)
    if single:
        arms.update(arm_fk((0.15, 0.05, -1), elbow=12, sides="L"))
    eq = kit.band_kit(anchor, sides=sides)
    return c.stand(legs, hk=0.96, pel=(L(8, 4), 0, 0), arms=arms, equip=eq + peq)


# ================================================================== jump rope
@tpl("jump_rope", (40, 8), linear=True)
def jump_rope(c, t, L, row):
    """Cyclic: small bounce on the balls of the feet while the wrists turn
    the rope one full turn per hop."""
    u = t % 1.0
    hop = max(0.0, math.sin(2 * math.pi * u)) * 0.06
    legs = c.feet(w=c.hw * 0.75, toe=6)
    for sd in legs:
        legs[sd]["ball"] = legs[sd]["ball"] + np.array([0, 0, hop])
        legs[sd]["heel"] = 25 + 160 * hop
    ang = 2 * math.pi * u
    arms = arm_fk((0.32, 0.18, -1), elbow=55, thumb="fwd", bend=(0, 1, 0), curl=0.85)
    fr = c.stand(legs, pz=c.pz * 0.975 + hop * 0.9, pel=(3, 0, 0), arms=arms, planted=(), balance=None, reach=False)

    def rope_pts():
        pts = []
        R, H0 = 0.95 * c.S, 0.95 * c.S
        for k in range(17):
            s = k / 16.0
            x = -0.36 + 0.72 * s
            sag = math.sin(math.pi * s)
            # rope loop turning about the line between the hands (x axis)
            yz = np.array([math.sin(ang + math.pi), -math.cos(ang + math.pi)]) * (0.05 + R * 0.5 * sag)
            pts.append(np.array([x, yz[0] * 0.9, H0 * 0.55 + yz[1] * (1.0 if yz[1] > 0 else 0.62) * sag + 0.02]))
        return pts

    def post(spec, eq, ex):
        pts = rope_pts()
        out = list(eq)
        for i in range(len(pts) - 1):
            out.append(seg(f"jr{i}", pts[i], pts[i + 1], 0.005, "ropew"))
        out.append(seg("jrL", "gripL", pts[0], 0.006, "ropew"))
        out.append(seg("jrR", "gripR", pts[-1], 0.006, "ropew"))
        for sd in "LR":
            out.append(H("rope_knob", sd, "db", eid=f"jh{sd}", off=(0, 0, 0)))
        return out
    return _wrap_build(fr, post)


# ================================================================== olympic lifts (key-framed)
def json_key(row):
    import json
    return json.dumps(row.get("_p") or {}, sort_keys=True)


def _seg_of(keys, u):
    from .motion import ease
    for (t0, a), (t1, b) in zip(keys[:-1], keys[1:]):
        if t0 <= u <= t1:
            return a, b, ease((u - t0) / max(t1 - t0, 1e-9))
    return keys[-1][1], keys[-1][1], 0.0


def _mix(a, b, w, k, d=0.0):
    va, vb = a.get(k, d), b.get(k, a.get(k, d))
    return va * (1 - w) + vb * w


@tpl("olympic", (62, 8), fast=True)
def olympic(c, t, L, row):
    """Clean / snatch family from the data: start (floor | hang | low_hang |
    blocks), lift (clean | snatch | pull | high_pull), catch (power | squat |
    split | muscle), then (none | front_squat | ohs | jerk | split_jerk | press).
    Keys: start -> extension (on the toes, shrug) -> turnover -> catch -> stand."""
    lift = P(row, "lift", "clean")
    start = P(row, "start", "floor")
    catch = P(row, "catch", "power")
    then = P(row, "then", "none")
    imp = P(row, "implement", "barbell")
    snatch = lift == "snatch" or (lift in ("pull", "high_pull") and P(row, "snatch_grip"))
    gw = c.sw * (2.25 if snatch else (0.62 if P(row, "width") == "close" else 1.3))
    sumo = P(row, "sumo")
    w = c.hw * (2.4 if sumo else 1.15)
    hang = "pvc_hang" if imp == "pvc" else "bar_hang"
    oh = "oh_pvc" if imp == "pvc" else "oh_bar"
    top_bar = c.z_sh - c.Lh - 0.012
    z0 = {"floor": PLATE_R, "blocks": 0.5 * c.S, "hang": top_bar - 0.16, "low_hang": 0.5 * c.S, "rack": 0}[start]
    if imp == "pvc" and start == "floor":
        z0 = 0.2
    if start == "rack":      # push press / push jerk / split jerk from the front rack
        oh_ = "oh_pvc" if imp == "pvc" else "oh_bar"
        jerk = then in ("jerk", "split_jerk")
        K = [(0.0, dict(hold="front_bar", pitch=2, heel=0, neck=0, hk=0.99)),
             (0.3, dict(hold="front_bar", pitch=3, heel=0, neck=0, hk=0.9)),
             (0.5, dict(hold="front_bar", pitch=0, heel=25, neck=-4, hk=1.0)),
             (0.78, dict(hold=oh_, pitch=0, heel=0, neck=0, hk=0.86 if jerk else 0.99,
                         split=0.75 if then == "split_jerk" else 0.0)),
             (1.0, dict(hold=oh_, pitch=0, heel=0, neck=0, hk=0.99))]
        ext = K[2][1]
    K = K if start == "rack" else []
    p0 = {"floor": 40, "blocks": 32, "hang": 22, "low_hang": 34, "rack": 0}[start]
    hk0 = None if start in ("floor", "blocks", "low_hang") else 0.88
    if start != "rack":
        K.append((0.0, dict(hold=hang, bar_z=z0, pitch=p0, heel=0, neck=-25, arm_ang=-6)))
    if start != "rack":
        if start in ("floor", "blocks"):
            K.append((0.22, dict(hold=hang, bar_z=0.5 * c.S if start == "floor" else 0.58 * c.S, pitch=32, heel=0, neck=-20,
                                 arm_ang=-8)))
        ext = dict(hold=hang, bar_z=top_bar + 0.035, pitch=-6, heel=30, neck=-4, arm_ang=2, hk=1.0)
        if lift == "pull":
            K.append((1.0, ext))
        elif lift == "high_pull":
            K.append((0.55, ext))
            K.append((1.0, dict(hold="high_pull", pitch=-3, heel=10, neck=0, hk=0.995)))
        else:
            K.append((0.42, ext))
            rack = oh if snatch else ("front_bar" if imp != "kb" else "kb_rack")
            depth = {"power": 0.82, "squat": 0.56, "split": 0.8, "muscle": 0.995}[catch]
            K.append((0.58, dict(hold="high_pull", pitch=4, heel=0, neck=-5, hk=min(0.97, depth + 0.1))))
            K.append((0.74, dict(hold=rack, pitch=20 if catch == "squat" else 10, heel=0, neck=-8, hk=depth,
                                 split=0.75 if catch == "split" else 0.0)))
            if then == "none":
                K.append((1.0, dict(hold=rack, pitch=2, heel=0, neck=0, hk=0.99)))
            elif then in ("front_squat", "ohs"):
                K.append((0.84, dict(hold=rack, pitch=4, heel=0, neck=0, hk=0.99)))
                K.append((1.0, dict(hold=rack, pitch=24, heel=0, neck=-8, hk=0.56)))
            else:   # jerk / split jerk / press
                K.append((0.82, dict(hold="front_bar", pitch=2, heel=0, neck=0, hk=0.99)))
                K.append((0.9, dict(hold="front_bar", pitch=2, heel=0, neck=0, hk=0.92 if then != "press" else 0.99)))
                K.append((1.0, dict(hold=oh, pitch=0, heel=0, neck=0, hk=0.86 if then != "press" else 0.99,
                                    split=0.75 if then == "split_jerk" else 0.0)))
    # after the extension the pelvis is driven by knee bend: start that from
    # the pelvis height the bar-height constraint gave at the extension key
    t_ext = next(tk for tk, d in K if d is ext)
    if t > t_ext + 1e-6 and start != "rack":
        ck = ("oly_ext", c.g, row.get("name_en"), json_key(row))
        cache = c.__dict__.setdefault("_cache", {})
        if ck not in cache:
            fr_e = olympic(c, t_ext, lambda a_, b_: a_, row)
            pe = c.run(fr_e)
            cache[ck] = pe.Hp[c.r.bi("root")][2]
        ext["hk"] = None
        ext["pz"] = cache[ck]
    a, b, wgt = _seg_of(K, t)
    hold_a, hold_b = a["hold"], b["hold"]
    split = _mix(a, b, wgt, "split")
    heel = _mix(a, b, wgt, "heel")
    legs = c.feet(w=w, toe=30 if sumo else 12, split=split * c.S)
    for sd in legs:
        legs[sd]["heel"] = heel
        if split > 0.05 and sd == "L":
            legs[sd]["heel"] = 50 * split / 0.75
    clav = _mix(a, b, wgt, "clav")

    def hk_of(d):
        return d.get("hk")
    bz = None
    pz = None
    if "bar_z" in a and "bar_z" in b and t <= t_ext + 1e-6:
        bz = _mix(a, b, wgt, "bar_z")
        hk = None
    else:
        za = a["pz"] if a.get("pz") is not None else c.pz * (a.get("hk") or 0.92)
        zb = b["pz"] if b.get("pz") is not None else c.pz * (b.get("hk") or 0.92)
        pz = za * (1 - wgt) + zb * wgt
        hk = None
    arm_ang = _mix(a, b, wgt, "arm_ang", -4)

    def H_(h):
        if h in ("bar_hang", "pvc_hang"):
            return (h, dict(arm_ang=arm_ang, gw=gw))
        if h in ("oh_bar", "oh_pvc"):
            return (h, dict(gw=gw))
        if h == "high_pull":
            return ("high_pull", dict(gw=gw))
        return h
    fr = c.stand(legs, hk=hk, pz=pz, pel=(_mix(a, b, wgt, "pitch"), 0, 0), neck=(_mix(a, b, wgt, "neck"), 0, 0),
                 hold=H_(hold_a), hold2=H_(hold_b), mix=wgt, load=0.4, bar_z=bz,
                 balance="bar" if bz is not None else "com", planted=() if split > 0.05 else ("L", "R"),
                 clav={"L": (clav, 0), "R": (clav, 0)} if clav else None)
    if start == "blocks":
        b0 = fr.build

        def build():
            spec, eq, ex = b0()
            for sd in "LR":
                eq.append(E("plyo_box", (SIDES[sd] * 0.62, 0.06, 0), eid=f"blk{sd}", size=(0.3, 0.4, 0.5 * c.S - PLATE_R)))
            return spec, eq, ex
        fr.build = build
    return fr


# ================================================================== handstands
@tpl("handstand", (85, 6))
def handstand(c, t, L, row):
    """Inverted on straight (or bending) arms, hands on the floor, body
    vertical; heels on a wall when the data says so.  depth: 0 = hold,
    1 = head lowered to the mat (handstand push-up)."""
    n = words(row)
    push = "push-up" in n or "push up" in n or P(row, "push")
    wall = "wall" in n
    down = L(0.0, 1.0) if push else L(0.0, 0.04)
    hw = c.sw * 1.15
    sh_top = c.Lpf * 0.94
    sh_bot = 0.395 * c.S
    sz = sh_top * (1 - down) + sh_bot * down
    sh_r = c.r.joint("upperarm01.R")
    sh_mid_r = np.array([0, sh_r[1], sh_r[2]])
    R = body_rot(180, 0, 0)
    S = np.array([0, -0.02, sz])
    pel = S - R @ (sh_mid_r - c.r.pc_rest)
    arms = arm_ik(lambda D, Hp, c_, sd: np.array([SIDES[sd] * hw / 2, 0.0, 0.004]), (-1, 0.15, 0), (0.25, 1.0, -0.2),
                  curl=0.05, key="palm", fing=(0, 1, 0))
    legs = legs_fk((0.04, -0.06, 1), knee=4, kbend=(0, 1, 0), fdir=(0, -0.3, 1))   # legs straight up
    eq = [E("mat", (0, -0.2, 0), eid="mat")]
    if wall:
        eq.append(E("wall", (0, -0.42, 0), eid="wall"))
    fr = c.stand(legs, pz=pel[2], py=pel[1], pel=(180, 0, 0), neck=(-25, 0, 0), arms=arms, balance=None,
                 reach=False, planted=(), equip=eq)
    fr.cons.append(("reach_arms", -Z, ["L", "R"]))
    return fr


# ================================================================== depth jump
@tpl("depth_jump", (82, 8), fast=True)
def depth_jump(c, t, L, row):
    """Cyclic: stand on the box, step off, land softly, jump straight up,
    land, step back onto the box."""
    bh = float(P(row, "box_h", 0.4 * c.S))
    by = -0.55 * c.S
    w = c.hw * 0.6
    sq = lambda k: c.pz * k
    std = dict(ua=(0.12, 0.1, -1), el=15, neck=0)
    K = [
        (0.00, dict(fL=(-w, by, bh), fR=(w, by, bh), sL=bh, sR=bh, pz=sq(0.97) + bh, py=by, pitch=3, **std)),
        (0.16, dict(fL=(-w, by, bh), fR=(w, by * 0.45, bh * 0.4), gR=0, sL=bh, sR=bh, pz=sq(0.95) + bh * 0.8,
                    py=by * 0.75, pitch=6, **std)),
        (0.28, dict(fL=(-w, 0, 0), fR=(w, 0, 0), sL=0, sR=0, pz=sq(0.68), py=-0.04, pitch=36, ua=(0.15, -0.5, -0.8),
                    el=12, neck=-18)),
        (0.44, dict(fL=(-w, 0, 0.32), fR=(w, 0, 0.32), hL=50, hR=50, gL=0, gR=0, sL=0, sR=0, pz=sq(1.0) + 0.36, py=0.0,
                    pitch=0, ua=(0.12, 0.25, 1.0), el=10, neck=0)),
        (0.58, dict(fL=(-w, 0, 0), fR=(w, 0, 0), sL=0, sR=0, pz=sq(0.74), py=-0.03, pitch=28, ua=(0.15, 0.7, -0.4),
                    el=20, neck=-12)),
        (0.72, dict(fL=(-w, 0, 0), fR=(w, 0, 0), sL=0, sR=0, pz=sq(0.97), py=0.0, pitch=3, **std)),
        (0.86, dict(fL=(-w, 0, 0), fR=(w, by, bh), gR=0, sL=0, sR=bh, pz=sq(0.9) + bh * 0.6, py=by * 0.5, pitch=12,
                    **std)),
        (1.00, dict(fL=(-w, by, bh), fR=(w, by, bh), sL=bh, sR=bh, pz=sq(0.97) + bh, py=by, pitch=3, **std)),
    ]
    for _, d in K:
        for k in ("hL", "hR", "gL", "gR"):
            d.setdefault(k, {"gL": 1.0, "gR": 1.0}.get(k, 0.0))
    kv = _interp(K, t)
    return keyed_stand(c, kv, equip=[E("plyo_box", (0, by - 0.02, 0), eid="box", size=(0.6, 0.5, bh))])


# ================================================================== assisted pull-up machine
@tpl("assisted_pull_up", (36, 10))
def assisted_pull_up(c, t, L, row):
    """Kneeling on the counterweighted pad, pulling from the machine handles."""
    n = words(row)
    grip = "sup" if "chin" in n else ("neutral" if "neutral" in n else "pro")
    gw = c.sw * (1.0 if grip == "sup" else (0.9 if grip == "neutral" else (1.9 if "wide" in n else 1.55)))
    legs = legs_fk((0.06, -0.05, -1), knee=95, kbend=(0, -1, 0), fdir=(0, -1, -0.2))
    fr = fam.hang(c, pull=L(0, 1), gw=gw, grip=grip, legs=legs, eq=False, bar_h=2.35 * c.S, spine=(L(0, -5), 0, 0),
                  neck=(L(0, -12), 0, 0),
                  extra_eq=[dict(E("assist_frame", (0, 0.05, 0), eid="af", height=2.35 * c.S), fit=True)])

    def post(spec, eq, ex):
        return eq + [dict(kind="knee_pad", M=np.eye(4), id="kpad", shape={}, bone="lowerleg01.R",
                          bone_pt=c.r.joint("lowerleg01.R") + np.array([-c.r.joint("lowerleg01.R")[0], 0.02, -0.06]),
                          bone_R=np.eye(3))]
    return _wrap_build(fr, post)


# ================================================================== chest-supported (prone on an incline bench)
@tpl("chest_supported", (70, 12))
def chest_supported(c, t, L, row):
    """Chest on a 30-45 deg incline bench, feet on the floor behind; arms do
    a row (default), a Y raise or a reverse fly (P arm=row|y|fly)."""
    n = words(row)
    arm = P(row, "arm") or ("y" if "y-raise" in n or "y raise" in n else ("fly" if "fly" in n or "reverse" in n else "row"))
    ang = 35.0
    # bench turned round: the raised pad faces +Y; the user lies on it facing down
    Rb = fam.rx(ang)
    piv = np.array([0, 0.02, BENCH_H])
    n_pad = Rb @ Z
    lean = 90 - ang
    if "curl" in n:
        arm = "curl"
    if arm == "row":
        arms, eq = fam.row_db(c, L(0, 1), sides="LR", thumb="neutral" if "neutral" in n or "row" in n else "pro")
    elif arm == "curl":      # spider curl: upper arms hang straight down, elbows flex
        arms = arm_fk((0.08, 0.05, -1), elbow=L(8, 128), thumb="sup", bend=(0, 1, 0), curl=0.88, world=True)
        eq = [H("ezbar", "C", "bar", eid="bar")] if "dumbbell" not in n else [H("dumbbell", "L"), H("dumbbell", "R")]
    elif arm == "y":
        arms = arm_fk((L(0.15, 0.55), L(0.1, 0.35), L(-1, 0.75)), elbow=8, thumb="up", curl=0.85, world=True)
        eq = [H("dumbbell", "L"), H("dumbbell", "R")]
    else:
        arms = arm_fk((L(0.12, 1.0), L(0.05, -0.05), L(-1, -0.05)), elbow=L(12, 18), thumb=(0, 1, 0), curl=0.85, world=True)
        eq = [H("dumbbell", "L"), H("dumbbell", "R")]
    if "kettlebell" in n:
        eq = [H("kettlebell", "L", "kb"), H("kettlebell", "R", "kb")]
    legs = {sd: dict(ball=np.array([SIDES[sd] * 0.14, -0.78 * c.S, SOLE]), yaw=6, heel=55, surf=0.0,
                     pole=np.array([SIDES[sd] * 0.1, 1, 0.3])) for sd in "LR"}
    fr = c.stand(legs, pz=BENCH_H + 0.62 * c.S, py=0.05, pel=(lean, 0, 0), neck=(-10, 0, 0), arms=arms, balance=None,
                 reach=True, planted=("L", "R"),
                 equip=eq + [E("bench", (0, 0, 0), R=fam.rz(180), eid="bench", incline=ang)],
                 settle=[("plane", piv + Rb @ np.array([0, 0.4, 0]), n_pad, X, 0.14, Rb @ Y, 0.38, PAD_SINK)])
    return fr


# ================================================================== push-up / plank supports from the data
def _plank_supports(row, c):
    """hands_h, feet_h and equipment from the spec support words."""
    w = words(row)
    eq, hh, fh = [], 0.0, 0.0
    if "blocks (hands)" in w or "push-up handles" in w or "deficit" in w:
        hh = 0.12
        eq += [E("plyo_box", (SIDES[sd] * c.sw * 0.58, 0.0, 0), eid=f"blk{sd}", size=(0.12, 0.2, 0.11)) for sd in "LR"]
    if "flat bench (hands)" in w or "bench_flat (hands)" in w or "(elevated)" in w:
        hh = BENCH_H
        eq.append(E("bench", (0, 0.09, 0), R=fam.rz(90), eid="bench"))      # palms on the near edge of the pad
    if "ball (shins)" in w:
        fh = 0.55
    if "bench/box (feet)" in w or "box (feet)" in w:
        fh = BENCH_H
    if any(k in w for k in ("straps (feet", "straps (toes", "straps (heels", "straps (shins")) or \
            (("suspension" in w or "trx" in w) and "plank_hands" in w and "floor (feet)" not in w
             and "on handles" not in w):
        fh = 0.45                     # feet in the suspension cradles (straps drawn by the overlay)
    bosu = "bosu" in w or "balance trainer" in w or "balance_trainer" in w
    hands_on = "plank" in w and "(feet" not in w and "feet on" not in w and "(lifted" not in w
    flat = any(k in w for k in ("bosu (flat side)", "dome down", "bosu (hands)", "edges", "platform"))
    if bosu and hands_on and flat:
        hh = 0.25                     # hands on the flat side of an upturned trainer
        eq.append(E("bosu", (0, 0.0, 0.25), R=fam.rx(180), eid="bosu"))
    elif bosu and hands_on:
        hh = 0.12 if "wide" in w else 0.2       # hands on the dome (edges when wide)
        eq.append(E("bosu", (0, 0.0, 0), eid="bosu"))
    return hh, fh, eq


_old_push = _REG_OLD.get("push_up")
_old_plank = _REG_OLD.get("plank")


@tpl("push_up", (70, 10))
def push_up(c, t, L, row):
    hh, fh, eq = _plank_supports(row, c)
    n = words(row)
    nm = (row.get("name_en") or "").lower()
    if ("single-arm" in nm or "one-arm" in nm or "one arm" in nm) and "medicine" not in nm:
        # right hand under the chest, left hand on the low back, feet wide for balance
        arms_over = arm_fk((0.2, -0.9, 0.12), elbow=95, bend=(-1, 0, -0.3), thumb="up", sides="L", world=True)
        return fam.plank(c, down=L(0, 0.7), hand_w=c.sw * 0.55, feet_w=0.62 * c.S, equip=[E("mat", (0, -0.4, 0), eid="mat")],
                         arms_over=arms_over, neck=(-10, 0, 0), hands_on=True)
    if "archer" in nm and not eq and not fh:
        # hands very wide; the chest lowers toward the right hand (that elbow
        # bends) while the left arm slides out straight to the side
        fr = fam.plank(c, down=L(0, 0.72), hand_w=c.sw * 2.3, equip=[E("mat", (0, -0.4, 0), eid="mat")],
                       neck=(-10, 0, 0), hands_on=True, feet_w=0.42 * c.S)
        b0 = fr.build
        shift = L(0.0, 0.22) * c.S

        def build():
            spec, eq_, ex = b0()
            spec["pelvis"] = np.asarray(spec["pelvis"], float) + np.array([shift, 0.0, 0.0])
            return spec, eq_, ex
        fr.build = build
        return fr
    if not eq and not fh or "pike" in n or "handstand" in n or "medicine" in n:
        return _old_push(c, t, L, row)
    hw = c.sw * (1.6 if "wide" in n else (0.45 if "diamond" in n or "close" in n else 1.15))
    if any(e["kind"] == "bosu" for e in eq):
        hw = 0.5 if "wide" in n else 0.44       # the hands stay on the trainer
    extra = list(eq)
    if fh and "ball (shins)" in n:
        extra.append(E("stability_ball", (0, -0.98 * c.S, 0), eid="sb"))
    elif fh and not ("suspension" in n or "trx" in n):
        extra.append(E("bench", (0, -1.05 * c.S, 0), R=fam.rz(90), eid="fbench"))
    bot = 0.7 if any(e["kind"] == "bosu" for e in eq) else 1.0     # chest stops at the trainer
    legs_over = None
    if "spiderman" in (row.get("name_en") or "").lower():
        k = L(0.0, 1.0)            # the right knee drives out toward the right elbow as the chest lowers
        a = math.radians(95 * k)

        def knee(D, k=k, a=a):
            R0 = D[c.r.bi("root")]
            return dict(thigh=unit(R0 @ np.array([0.45 * k, 0.3 * math.sin(a), -math.cos(a)])), knee=10 + 95 * k,
                        kbend=R0 @ np.array([0, -1, 0]), fdir=R0 @ np.array([0.3, 0.3, -1]))
        legs_over = {"R": knee}
    fr = fam.plank(c, down=L(0, bot), hand_w=hw, hands_h=hh, feet_h=fh, equip=[E("mat", (0, -0.4, 0), eid="mat")] + extra,
                   neck=(-10, 0, 0), hands_on=True, legs_over=legs_over)
    if legs_over:
        fr.planted = ["L"]
    return fr


@tpl("plank", (65, 12))
def plank(c, t, L, row):
    hh, fh, eq = _plank_supports(row, c)
    n = words(row)
    if not eq and not fh:
        return _old_plank(c, t, L, row)
    elbows = "plank_elbows" in n and "plank_hands" not in n
    nm = (row.get("name_en") or "").lower()
    if "tap" in nm and not elbows:
        # the right hand lifts off the support and taps the left shoulder
        u = L(0.0, 1.0)
        hw = 0.44 if any(e["kind"] == "bosu" for e in eq) else c.sw * 1.15

        def tap(D, Hp, c_, sd):
            base = np.array([hw / 2, 0.0, hh + 0.004])
            top = fam.shoulder(D, Hp, c, "L") + np.array([0.03, 0.0, 0.06])
            return base * (1 - u) + top * u + Z * 0.08 * math.sin(math.pi * u)
        th = unit(np.array([-1 + u * 0.6, 0.15, u]))
        arms_over = arm_ik(tap, tuple(th), (0.6, -0.5, 0.4), curl=0.05 + 0.3 * u, key="palm", sides="R",
                           fing=(-0.8 * u, 1 - 0.6 * u, 0.4 * u))
        return fam.plank(c, down=0.0, hand_w=hw, hands_h=hh, feet_h=fh, equip=eq, hands_on=True, arms_over=arms_over,
                         feet_w=0.4 * c.S)
    if fh and "ball (shins)" in n:
        eq = list(eq) + [E("stability_ball", (0, -1.12 * c.S, 0), eid="sb")]
    return fam.plank(c, down=0.0, elbows=elbows, hands_h=hh, feet_h=fh, equip=eq, hands_on=True)


# ================================================================== hack squat machine
@tpl("hack_squat_machine", (80, 10))
def hack_squat_machine(c, t, L, row):
    """Back against the sled, shoulders under the pads, feet on the angled
    plate; the body travels down the 45 deg rails."""
    pitch = -24.0
    down = np.array([0, 0.62, -0.78])
    top = np.array([0, -0.32, 0.93 * c.S])
    pel = top + down * L(0.0, 0.42) * c.S
    legs = {sd: dict(ball=np.array([SIDES[sd] * 0.15, 0.3, 0.17 + SOLE]), yaw=10, heel=-14, surf=0.17,
                     pole=np.array([SIDES[sd] * 0.3, 1, 0.3])) for sd in "LR"}

    def tgt(D, Hp, c_, sd):
        Rt = D[c.r.bi("spine01")]
        return fam.shoulder(D, Hp, c, sd) + Rt @ Z * 0.11 + Rt @ Y * 0.06 + Rt @ X * SIDES[sd] * 0.03
    arms = arm_ik(tgt, (0, 1, 0), (1, -0.6, -0.4), curl=0.9, fing=(0, 0.2, -1))
    sled = dict(kind="hack_sled", M=np.eye(4), id="sled", shape={}, bone="spine01",
                bone_pt=np.array([0, c.r.joint("spine01")[1] - 0.13, c.z_sh]))
    eq = [E("hack_frame", (0, 0.3, 0), eid="hf"), sled]
    return c.stand(legs, pz=pel[2], py=pel[1], pel=(pitch, 0, 0), neck=(8, 0, 0), arms=arms, balance=None,
                   reach=True, planted=("L", "R"), equip=eq)


# ================================================================== battle ropes (waves travel down the ropes)
@tpl("battle_ropes", (40, 12), linear=True)
def battle_ropes(c, t, L, row):
    """Cyclic: athletic half squat, hands drive the rope ends; each rope is a
    polyline with a travelling wave from the hand to the anchor (alternating
    waves, both-hand slams or lateral whips from the data / name)."""
    n = words(row)
    mode = P(row, "rope") or ("slam" if "slam" in n else ("lateral" if "lateral" in n or "whip" in n else
                              ("spiral" if "spiral" in n or "circle" in n else "alt")))
    u = t % 1.0
    legs = c.feet(w=c.hw * 1.6, toe=15)
    anchor = np.array([0, 3.0, 0.14])
    ph = 2 * math.pi * u

    def hand_off(sd):
        s = SIDES[sd]
        if mode == "slam":
            # overhead -> slam down (to the right side for outside slams); kept within reach
            out = 0.32 * (1 - math.cos(ph)) / 2 if "outside" in n else 0.0
            return np.array([out - 0.04 * s * 0, 0.26, 0.42 * math.cos(ph) + 0.06])
        if mode == "lateral":
            return np.array([0.18 * math.sin(ph) * s * 0 + 0.18 * math.sin(ph), 0.42, -0.35])
        if mode == "spiral":
            return np.array([s * (0.12 + 0.1 * math.cos(ph)), 0.42, -0.3 + 0.12 * math.sin(ph)])
        k = 0 if sd == "R" else math.pi
        return np.array([0, 0.42, -0.32 + 0.2 * math.sin(ph + k)])

    def tgt(D, Hp, c_, sd):
        off = hand_off(sd) + X * SIDES[sd] * 0.04
        k = np.linalg.norm(off)
        lim = c.Lpf * 0.86         # grip point: always within reach (smaller athletes too)
        if k > lim:
            off = off * lim / k
        return fam.shoulder(D, Hp, c, sd) + off

    arms = arm_ik(tgt, (0, 0, 1), (1, -0.6, -0.4), curl=0.9, fing=(0, 1, -0.3))
    hk = 0.82 if mode != "slam" else 0.86 - 0.06 * max(0.0, -math.cos(ph))
    fr = c.stand(legs, hk=hk, pel=(20, 0, 0), arms=arms, neck=(-10, 0, 0),
                 equip=[E("battle_rope_anchor", anchor, eid="anch")])

    def post(spec, eq, ex):
        out = list(eq)
        for sd in "LR":
            def pt(k, sd=sd):
                def f(pts, D, Hp, c_):
                    g = pts[f"grip{sd}"] + np.array([0, 0.06, -0.02])
                    a = anchor + np.array([SIDES[sd] * 0.06, 0, 0])
                    w = k / 14.0
                    base = g * (1 - w) + a * w
                    base[2] = (g[2] * (1 - w) + a[2] * w) - 0.25 * math.sin(math.pi * w) * (1 - w) * 0 - 0.12 * math.sin(math.pi * w)
                    base[2] = max(base[2], 0.02)
                    kk = 0 if (sd == "R" or mode in ("slam", "lateral")) else math.pi
                    amp = (0.16 if mode != "lateral" else 0.0) * (1 - w) ** 1.3
                    lat = (0.16 if mode == "lateral" else 0.0) * (1 - w) ** 1.3
                    wave = math.sin(ph + kk - w * 3 * 2 * math.pi)
                    return base + np.array([lat * wave, 0, amp * wave * (1 if base[2] > 0.05 else 0.3)])
                return f
            for k in range(14):
                out.append(seg(f"br{sd}{k}", pt(k), pt(k + 1), 0.018, "rope"))
        return out
    return _wrap_build(fr, post)


# ================================================================== burpee (key-framed, cyclic)
@tpl("burpee", (75, 12), fast=True)
def burpee(c, t, L, row):
    """Stand, squat and plant the hands, jump the feet back to a plank,
    (push-up), jump the feet in, jump up with the arms overhead, land."""
    n = words(row)
    push = "push-up" in n or "push up" in n or P(row, "push")
    w = c.hw * 0.6
    hy = 0.36 * c.S
    fy_back = -0.8 * c.S
    S = c.S
    stand = dict(fL=(-w, 0, 0), fR=(w, 0, 0), pz=c.pz * 0.97, py=0.0, pitch=3, hw=0.0, ua=(0.12, 0.05, -1), el=12,
                 neck=0, hL=0, hR=0)
    tor = 0.5 * S                                   # pelvis -> shoulder line
    def over_hands(pitch, sh_z):                    # pelvis so the shoulders sit right above the hands
        a = math.radians(pitch)
        return dict(py=hy - tor * math.sin(a), pz=sh_z - tor * math.cos(a), pitch=pitch)
    squat = dict(fL=(-w, 0, 0), fR=(w, 0, 0), hw=1.0, ua=(0.1, 0.6, -0.8), el=10, neck=-25, hL=30, hR=30,
                 **over_hands(76, c.Lpf * 0.95))
    plank = dict(fL=(-w * 0.8, hy - 1.38 * S, 0), fR=(w * 0.8, hy - 1.38 * S, 0), hw=1.0, ua=(0.1, 0.3, -1), el=5,
                 neck=-15, hL=70, hR=70, **over_hands(76, c.Lpf * 0.97))
    bottom = dict(plank, **over_hands(84, 0.3 * S))
    jump = dict(fL=(-w, 0, 0.22), fR=(w, 0, 0.22), pz=c.pz + 0.26, py=0.0, pitch=-2, hw=0.0, ua=(0.15, 0.1, 1.0),
                el=8, neck=0, hL=45, hR=45, gL=0, gR=0)
    mid = dict(plank, fL=(-w * 0.9, (hy - 1.38 * S) * 0.5, 0.12), fR=(w * 0.9, (hy - 1.38 * S) * 0.5, 0.12), gL=0, gR=0,
               hL=50, hR=50, **dict(over_hands(72, c.Lpf * 0.96), pz=over_hands(72, c.Lpf * 0.96)["pz"] + 0.12))
    K = [(0.0, stand), (0.14, squat), (0.21, mid), (0.28, dict(plank, gL=0, gR=0)), (0.36, plank)]
    if push:
        K += [(0.46, bottom), (0.56, plank)]
    t_in = K[-1][0] + 0.12
    K += [(t_in - 0.06, mid), (t_in, dict(squat, gL=0, gR=0)), (t_in + 0.12, dict(jump, pz=c.pz * 0.9)), (min(0.95, t_in + 0.24), jump),
          (1.0, stand)]
    for _, d in K:
        for k in ("gL", "gR"):
            d.setdefault(k, 1.0)
    kv = _interp(K, t)
    hw = float(kv["hw"])

    def mk(sd):
        def f(D, Hp, c_):
            sh = fam.shoulder(D, Hp, c, sd)
            v = np.array(kv["ua"], float)
            if sd == "L":
                v[0] = -v[0]
            air = sh + unit(D[c.r.bi("spine01")] @ v) * c.Lh * 0.96
            flo = np.array([SIDES[sd] * c.sw * 0.6, hy, 0.004])
            if hw > 0.98:
                return dict(palm=flo, thumb=np.array([-SIDES[sd], 0.15, 0]), fing=Y, pole=np.array([SIDES[sd] * 0.25, -1, 0.25]),
                            curl=0.05)
            p = air * (1 - hw) + (flo + np.array([0, 0, 0.1])) * hw
            d = p - sh
            p = sh + unit(d) * min(np.linalg.norm(d), c.Lh * 0.97)     # never beyond reach
            return dict(grip=p, thumb=Y * (1 - hw) + Z * 0.0 + np.array([-SIDES[sd] * hw, 0, 0]) + 1e-3 * Z,
                        pole=np.array([SIDES[sd] * 0.4, -1, 0.2]), curl=0.4 * (1 - hw))
        return f
    arms = {"L": mk("L"), "R": mk("R")}
    fr = keyed_stand(c, kv, arms=arms, equip=[E("mat", (0, -0.2, 0), eid="mat")])
    if hw > 0.3:   # hands reach the floor: the body lowers / slides toward them as needed
        fr.cons.append(("reach_arms", -Z, ["L", "R"]))
    return fr


# ================================================================== pec deck / reverse fly machine
@tpl("pec_deck", (25, 16))
def pec_deck(c, t, L, row):
    """Seated, back on the pad; hands on vertical handles at the ends of two
    lever arms pivoting above the shoulders.  Fly: arms open -> hands meet in
    front.  Reverse (P reverse or name): hands in front -> arms open."""
    n = words(row)
    rev = P(row, "reverse") or "reverse" in n or "rear" in n
    seat_h = 0.46 * c.S
    a = math.radians(L(8, 86) if not rev else L(86, 2))

    def tgt(D, Hp, c_, sd):
        s = SIDES[sd]
        sh = fam.shoulder(D, Hp, c, sd)
        r = c.Lh * 0.8
        return sh + np.array([s * math.cos(a) * r - s * 0.06 * math.sin(a), math.sin(a) * r, -0.06])

    arms = arm_ik(tgt, (0, 0, 1), (0.3, -0.4, -1), curl=0.9,
                  fing=lambda D, Hp, c_, sd: np.array([SIDES[sd] * math.cos(a) * 0.6 - SIDES[sd] * math.sin(a) * 0.5, 0.8, 0]))
    fr = fam.seated(c, seat_h=seat_h, seat_y=0.02, pitch=-4, arms=arms, equip=[E("pec_frame", (0, 0, 0), eid="pf", seat_h=seat_h)],
                    back=(np.array([0, -0.18, seat_h + 0.42]), np.array([0, 1, 0.1])), feet_y=0.48 * c.S)

    def post(spec, eq, ex):
        out = list(eq)
        for sd in "LR":
            s = SIDES[sd]

            def piv(pts, D, Hp, c_, s=s, sd=sd):
                sh = Hp[c.r.bi(f"upperarm01.{sd}")]
                return np.array([s * 0.13, sh[1] - 0.02, sh[2] + 0.32])

            def top(pts, D, Hp, c_, sd=sd):
                return pts[f"grip{sd}"] + np.array([0, 0, 0.09])

            def bot(pts, D, Hp, c_, sd=sd):
                return pts[f"grip{sd}"] - np.array([0, 0, 0.08])
            out.append(seg(f"pa{sd}", piv, top, 0.02, "frame"))
            out.append(seg(f"ph{sd}", top, bot, 0.017, "rubber"))
        return out
    return _wrap_build(fr, post)


_REG["reverse_fly_machine"] = _REG["pec_deck"]


_old_lying_curl = _REG_OLD["lying_leg_curl"]


@tpl("lying_leg_curl", (78, 12))
def lying_leg_curl(c, t, L, row):
    """Prone leg curl machine: roller pad behind the ankles on a lever that
    pivots at the knees (old set-up drew no lever)."""
    n = words(row)
    fr = _old_lying_curl(c, t, L, row)
    if "band" in n or "ball" in n:
        return fr

    def piv(pts, D, Hp, c_):
        k = 0.5 * (Hp[c.r.bi("lowerleg01.L")] + Hp[c.r.bi("lowerleg01.R")])
        return np.array([0.33, k[1], k[2]])

    def post(spec, eq, ex):
        pad = _shin_pad(front=False, up=0.06)

        def pad_back(pts, D, Hp, c_):
            # behind the heels: opposite side of the shin from the front
            r = c.r
            acc = np.zeros(3)
            for sd in "LR":
                K = Hp[r.bi(f"lowerleg01.{sd}")]
                A = Hp[r.bi(f"foot.{sd}")]
                sh = unit(K - A)
                nrm = unit(np.cross(X, sh))
                fwd = Rf = D[r.bi(f"foot.{sd}")] @ r.foot_rest[sd]["F"][:, 0]
                if np.dot(nrm, fwd) > 0:
                    nrm = -nrm
                acc += A + sh * 0.05 + nrm * 0.07
            return acc / 2
        out = list(eq)
        a = lambda pts, D, Hp, c_: pad_back(pts, D, Hp, c_) - X * 0.19
        b = lambda pts, D, Hp, c_: pad_back(pts, D, Hp, c_) + X * 0.19
        e = lambda pts, D, Hp, c_: np.array([0.33] + list(pad_back(pts, D, Hp, c_)[1:]))
        out += [seg("lcpad", a, b, 0.05, "pad"), seg("lcarm", piv, e, 0.022, "darksteel"),
                seg("lcstub", e, b, 0.018, "darksteel")]
        return out
    return _wrap_build(fr, post)


# ================================================================== nordic / glute-ham raise
_old_kneeling = None


@tpl("glute_ham_raise", (85, 8))
def glute_ham_raise(c, t, L, row):
    """Tall kneeling with the ankles locked under a padded bar; the body
    lowers forward as one straight line to the hands-catch (Nordic), or
    leans back (reverse Nordic)."""
    from .tpl_floor import kneeling
    n = words(row)
    rev = "reverse" in n
    if rev:
        arms = arm_fk((0.15, 0.4, -0.6), elbow=20, thumb="up")
        return kneeling(c, t, L, row, arms=arms, pitch=L(2, -32), spine=(0, 0, 0))
    a = L(4, 72)
    # hands come forward to catch near the bottom
    arms = arm_fk((0.15, L(0.3, 0.95), L(-0.9, -0.1)), elbow=L(70, 25), thumb="up")
    fr = kneeling(c, t, L, row, arms=arms, pitch=a, spine=(0, 0, 0))

    def post(spec, eq, ex):
        def heel_bar(pts, D, Hp, c_, s=1):
            pL = Hp[c.r.bi("foot.L")]
            pR = Hp[c.r.bi("foot.R")]
            m = 0.5 * (pL + pR)
            return m + np.array([0.0, 0.0, 0.07])
        a_ = lambda pts, D, Hp, c_: heel_bar(pts, D, Hp, c_) - X * 0.2
        b_ = lambda pts, D, Hp, c_: heel_bar(pts, D, Hp, c_) + X * 0.2
        post_ = lambda pts, D, Hp, c_: heel_bar(pts, D, Hp, c_) * np.array([1, 1, 0]) + np.array([0, -0.12, 0])
        top_ = lambda pts, D, Hp, c_: heel_bar(pts, D, Hp, c_) + np.array([0, -0.12, 0])
        return list(eq) + [seg("nbar", a_, b_, 0.045, "pad"), seg("npost", post_, top_, 0.03, "frame")]
    return _wrap_build(fr, post)


_preacher_v3 = _REG["preacher_curl"].fn


@tpl("preacher_curl", (80, 6))
def preacher_curl_m(c, t, L, row):
    """Preacher curl; on a machine the handles sit on lever arms pivoting
    beside the elbows."""
    n = words(row)
    fr = _preacher_v3(c, t, L, row)
    if "machine" not in n:
        return fr

    def post(spec, eq, ex):
        out = list(eq)
        for sd in "LR":
            s = SIDES[sd]

            def piv(pts, D, Hp, c_, sd=sd, s=s):
                e = Hp[c.r.bi(f"lowerarm01.{sd}")]
                return np.array([s * 0.3, e[1], e[2]])

            def tip(pts, D, Hp, c_, sd=sd, s=s):
                g = pts[f"grip{sd}"]
                return np.array([s * 0.3, g[1], g[2]])
            out += [seg(f"pl{sd}", piv, tip, 0.022, "frame"), seg(f"ph{sd}", tip, f"grip{sd}", 0.016, "rubber")]
        return out
    return _wrap_build(fr, post)


# ================================================================== side bend with one dumbbell
@tpl("side_bend", (12, 8))
def side_bend(c, t, L, row):
    n = words(row)
    legs = c.feet(w=c.hw * 1.15, toe=8)
    legs, peq = platform(c, row, legs)
    bend = L(-8, 26)                      # toward the loaded side and back over
    arms = {"R": arm_fk((0.1, 0.0, -1), elbow=6, thumb="fwd", curl=0.88, sides="R", world=True)["R"]}
    if "dowel" in n or "pvc" in n:
        arms = arm_fk((0.25, 0.0, 1.0), elbow=6, thumb="in", curl=0.8)
        eq = [H("pvc", "C", "bar", eid="bar")]
    else:
        arms.update(fam.arm_ik(lambda D, Hp, c_, sd: c.bp(D, Hp, "root", np.array([-0.16 * c.S, 0.0, c.z_hip + 0.1])),
                               (0, -1, 0), (-1, -0.3, 0.3), key="palm", curl=0.2, sides="L"))
        eq = [H("dumbbell", "R")] if "dumbbell" in n or "kettlebell" in n else []
        if "kettlebell" in n:
            eq = [H("kettlebell", "R", "kb")]
    return c.stand(legs, hk=0.99, pel=(0, L(-3, 6), 0), spine=(0, bend, 0), arms=arms, equip=eq + peq, balance="com",
                   load=0.1)


# ================================================================== lying hamstring stretch with a strap
@tpl("lying_hamstring_stretch", (85, 14))
def lying_hamstring_stretch(c, t, L, row):
    """On the back, one leg straight up held by a strap (or the hands behind
    the thigh), the other leg flat or bent."""
    n = words(row)
    a = math.radians(L(62, 84))
    legs = {"R": dict(thigh=np.array([0.04, math.cos(a), math.sin(a)]), knee=4, kbend=np.array([0, 1, 0]),
                      fdir=np.array([0, 1, 0.2])),
            "L": dict(thigh=np.array([-0.08, 1.0, -0.02]), knee=4, kbend=np.array([0, 0, 1]), fdir=np.array([0, 0.2, 1]))}
    strap = not ("partner" in n)

    def tgt(D, Hp, c_, sd):
        ft = Hp[c.r.bi("foot.R")]
        sh = fam.shoulder(D, Hp, c, sd)
        d = ft - sh
        return sh + unit(d) * min(np.linalg.norm(d) - 0.1, c.Lh * 0.9) + X * SIDES[sd] * 0.02
    arms = arm_ik(tgt, (0, 0, 1), (1, -0.3, -0.6), curl=0.9)
    from .tpl_floor import MAT
    fr = fam.floor_body(c, pitch=-90, legs=legs, arms=arms, equip=[MAT(0.1)], neck=(10, 0, 0))

    def post(spec, eq, ex):
        if not strap:
            return eq
        def sole(pts, D, Hp, c_):
            r = c.r
            return r.bone_point(D, Hp, "foot.R", r.foot_rest["R"]["ball"]) + np.array([0, 0.03, 0.02])
        return list(eq) + [seg("strapL", "gripL", sole, 0.009, "strap"), seg("strapR", "gripR", sole, 0.009, "strap")]
    return _wrap_build(fr, post)


_old_arm_stretch = _REG_OLD["arm_stretch"]


@tpl("arm_stretch", "front3q")
def arm_stretch(c, t, L, row):
    """Standing arm / shoulder stretches; adds the wall / doorframe chest
    stretch and the behind-the-back biceps stretch to the older set."""
    n = words(row)
    legs = c.feet(w=c.hw * 1.1, toe=8)
    if "biceps" in n or "bicep" in n:
        # hands together behind the back, straight arms lifted back and up
        def tgt(D, Hp, c_, sd):
            r = fam.sh_mid(D, Hp, c)
            return r + np.array([SIDES[sd] * 0.04, -0.15 - 0.12 * L(0, 1), -c.Lh * (0.86 - 0.18 * L(0, 1))])
        arms = arm_ik(tgt, (0, -1, 0.2), (1, 0.3, 0), curl=0.6, fing=(0, -0.2, -1))
        return c.stand(legs, pel=(L(0, 8), 0, 0), arms=arms, neck=(0, 0, 0))
    if "chest and shoulder" in n or "doorway" in n or "door" in n or "wall" in n and "chest" in n:
        # wall on the athlete's left so the camera (front, from the right) sees the stretched arm
        wall_x = -0.62 * c.S
        sp = L(0, 22)

        def tgtL(D, Hp, c_):
            sh = fam.shoulder(D, Hp, c, "L")
            return dict(palm=np.array([wall_x + 0.03, sh[1] - 0.02, sh[2] + 0.18]), thumb=-Y, fing=Z,
                        pole=-Z * 0.8 - X * 0.2, curl=0.0)
        arms = {"L": tgtL, "R": arm_fk((0.15, 0.1, -1), elbow=15, sides="R")["R"]}
        lg = c.feet(w=c.hw * 1.1, toe=8, split=-0.32 * c.S)
        return c.stand(lg, pel=(2, 0, sp * 0.4), spine=(0, 0, sp * 0.6), arms=arms,
                       equip=[E("wall", (wall_x - 0.05, 0, 0), R=fam.rz(-90), eid="wall")])
    return _old_arm_stretch(c, t, L, row)


_old_pull_up = _REG_OLD["pull_up"]


def _bone_pt(c, bone, pt):
    """World point of a rest-pose point carried by a bone (for segment ends)."""
    i = c.r.bi(bone)
    pt = np.asarray(pt, float)
    return lambda pts, D, Hp, c_: Hp[i] + D[i] @ (pt - c.r.H[i])


def _dip_belt(c):
    """Dip belt round the waist, two chains down the front to a plate that
    hangs between the thighs; everything moves with the pelvis."""
    r = c.r
    zb = c.z_hip + 0.075 * c.S
    v = r.verts
    m = (np.abs(v[:, 2] - zb) < 0.015) & (np.abs(v[:, 0]) < 0.25)
    xr = float(np.abs(v[m, 0]).max()) + 0.012
    y0, y1 = float(v[m, 1].min()) - 0.012, float(v[m, 1].max()) + 0.012
    yc, yr = 0.5 * (y0 + y1), 0.5 * (y1 - y0)
    ring = [np.array([xr * math.cos(a), yc + yr * math.sin(a), zb]) for a in np.linspace(0, 2 * math.pi, 13)]
    out = []
    for i in range(12):
        out.append(seg(f"belt{i}", _bone_pt(c, "root", ring[i]), _bone_pt(c, "root", ring[i + 1]), 0.022, "strap"))
    hook = np.array([0.0, y1 + 0.1, c.z_hip - 0.2 * c.S])
    for s_ in (-1, 1):
        a = np.array([s_ * xr * 0.55, yc + yr * 0.85, zb - 0.01])
        out.append(seg(f"chain{s_}", _bone_pt(c, "root", a), _bone_pt(c, "root", hook), 0.007, "darksteel"))
    out.append(dict(kind="plate_held", M=np.eye(4), id="beltplate", shape={}, bone="root",
                    bone_pt=hook + np.array([0, 0, -0.15]), bone_R=np.eye(3)))
    return out


def _v_bar_pull_up(c, t, L, row):
    """V-handle hooked over a bar that runs front to back above the athlete;
    neutral close grip, the head passes beside the bar at the top."""
    pull = L(0, 1)
    gh = fam.hang_bar_h(c)                 # grip height
    ring = 0.165
    bar_h = gh + ring + 0.02
    gw = 0.1
    grip = np.array([0, 0.0, gh])
    arms = arm_ik(lambda D, Hp, c_, sd: grip + X * SIDES[sd] * gw / 2, lambda D, Hp, c_, sd: Y,
                  lambda D, Hp, c_, sd: -Z * 0.5 + Y * 0.8 + X * SIDES[sd] * 0.2, curl=0.9,
                  fing=lambda D, Hp, c_, sd: Z)
    legs = legs_fk((0.06, L(0.05, 0.12), -1), knee=L(15, 40), kbend=(0, -1, 0), fdir=(0, 0.4, -1))
    eq = [dict(E("pullup_station", (0, 0, 0), R=rz(90), eid="station", height=bar_h, width=1.3), fit=True),
          dict(H("v_handle", "C", "aim", eid="vbar"), aim=np.array([0, 0.0, bar_h + 1.0]))]
    fr = fam.hang(c, pull=pull, gw=gw, grip="neutral", bar_h=gh, legs=legs, eq=False, extra_eq=eq, arms=arms,
                  spine=(L(0, -6), 0, 0), neck=(L(0, -10), 0, L(0, 14)), px=L(0.0, 0.13 * c.S))
    return fr


def _archer_pull_up(c, t, L, row):
    """Very wide grip; the body rises toward one hand (row side) while the
    other arm straightens out along the bar."""
    sd = row.get("_side") or "R"
    s_ = SIDES[sd]
    pull = L(0, 1)
    gw = c.sw * 2.4
    hk = 0.95
    top_d = 0.26 * c.S
    dx = math.sqrt(max((c.Lh * hk) ** 2 - top_d ** 2, 0.01))
    xs = min(gw / 2, dx + c.sw / 2 - gw / 2)
    legs = legs_fk((0.06, L(0.05, 0.1), -1), knee=L(15, 30), kbend=(0, -1, 0), fdir=(0, 0.4, -1))
    hang_d = math.sqrt(max((c.Lh * 0.985) ** 2 - max(gw / 2 - c.sw / 2, 0) ** 2, 0.01))
    d = hang_d * (1 - pull) + top_d * pull
    return fam.hang(c, pull=pull, gw=gw, grip="pro", legs=legs, px=s_ * xs * pull, d=d,
                    spine=(L(0, -4), L(0, -s_ * 8), 0), neck=(L(0, -12), 0, L(0, s_ * 10)),
                    pel=(0, L(0, -s_ * 6), 0))


def _butterfly_pull_up(c, t, L, row):
    """Cyclic kipping pull-up: the body travels a continuous loop - hollow
    swing forward at the bottom, hips drive, chin over the bar, push away and
    drop back - without stopping in a dead hang."""
    a = 2 * math.pi * t
    pull = 0.5 - 0.5 * math.cos(a)
    sw_ = math.sin(a)                      # +: body swung forward (in front of the bar)
    gw = c.sw * 1.75
    hang_d = math.sqrt(max((c.Lh * 0.985) ** 2 - max(gw / 2 - c.sw / 2, 0) ** 2, 0.01))
    d = hang_d * (1 - pull) + 0.21 * c.S * pull
    hip = 25 * math.sin(a - 0.6)           # hips flex (knees up) on the way up, extend behind on the way down
    legs = legs_fk((0.06, 0.15 + 0.28 * (1 + math.sin(a - 0.6)), -1), knee=25 + 18 * (1 + math.sin(a - 0.3)),
                   kbend=(0, -1, 0), fdir=(0, 0.4, -1))
    return fam.hang(c, pull=pull, gw=gw, grip="pro", legs=legs, d=d, py=-0.03 - 0.16 * c.S * sw_,
                    pel=(-12 * sw_ + 0.3 * hip, 0, 0), spine=(-8 * sw_ - 4 * pull, 0, 0),
                    neck=(-10 * pull, 0, 0))


@tpl("pull_up", "back3q")
def pull_up(c, t, L, row):
    """Pull-up family; neutral-grip variants hang from parallel handles (or a
    V-handle over the bar) instead of the straight bar."""
    n = words(row)
    name = (row.get("name_en") or "").lower()
    if "muscle" in n or "muscle" in name:
        return muscle_up(c, t, L, row)
    if "v-bar" in name or "v_handle" in n or "v-bar handle" in n:
        return _v_bar_pull_up(c, t, L, row)
    if "archer" in name:
        return _archer_pull_up(c, t, L, row)
    if "butterfly" in name:
        return _butterfly_pull_up(c, t, L, row)
    fr = _old_pull_up(c, t, L, row)
    if "weighted" in name:
        belt = _dip_belt(c)
        b1 = fr.build

        def build_w():
            spec, eq, ex = b1()
            return spec, list(eq) + belt, ex
        fr.build = build_w
    if not ("neutral" in n or "parallel" in n):
        return fr

    def post(spec, eq, ex):
        out = list(eq)
        for sd in "LR":
            def a(pts, D, Hp, c_, sd=sd):
                return pts[f"grip{sd}"] + np.array([0, -0.1, 0])

            def b(pts, D, Hp, c_, sd=sd):
                return pts[f"grip{sd}"] + np.array([0, 0.1, 0])

            def up(pts, D, Hp, c_, sd=sd):
                return pts[f"grip{sd}"] + np.array([0, -0.1, 0.12])
            out += [seg(f"nh{sd}", a, b, 0.016, "rubber"), seg(f"nhp{sd}", a, up, 0.014, "frame")]
        return out
    return _wrap_build(fr, post)


# ================================================================== sissy squat
_old_squat = _REG_OLD["squat"]


@tpl("squat", (62, 8))
def squat(c, t, L, row):
    """Squat family; the sissy squat rises on the toes, drives the knees
    forward and leans the straight hip-to-shoulder line back, one hand on a post."""
    n = words(row)
    if "kneeling" in (row.get("name_en") or "").lower():
        return kneeling_squat(c, t, L, row)
    if "sissy" not in n:
        return _old_squat(c, t, L, row)
    u = L(0, 1)
    legs = c.feet(w=c.hw * 1.0, toe=6, heel=(10 + 45 * u, 10 + 45 * u))
    post = np.array([-0.42 * c.S, 0.12, 0.0])

    def hold(D, Hp, c_, sd):
        sh = fam.shoulder(D, Hp, c, "L")
        return np.array([post[0] + 0.03, post[1] - 0.02, sh[2] - 0.3])
    arms = arm_ik(hold, (0, 1, 0), (-1, -0.4, -0.3), curl=0.9, sides="L")
    arms.update(arm_fk((0.15, 0.9, -0.2), elbow=10, thumb="in", sides="R"))
    return c.stand(legs, hk=L(0.985, 0.6), pel=(L(0, -32), 0, 0), spine=(L(0, 4), 0, 0), arms=arms,
                   balance="com", equip=[E("band_anchor", post, eid="post", h=1.2)])


# ================================================================== world's greatest stretch
_old_forward_lunge = _REG_OLD["forward_lunge"]


@tpl("forward_lunge", (88, 6))
def forward_lunge(c, t, L, row):
    """Forward lunge family; the world's greatest stretch holds a deep lunge
    with the left hand planted inside the front foot, drops the right elbow
    toward the instep, then turns the chest and reaches the right arm up."""
    name = (row.get("name_en") or "").lower()
    if "greatest" not in name:
        return _old_forward_lunge(c, t, L, row)
    split = 1.15 * c.S
    legs = c.feet(w=c.hw * 1.0, toe=6, split=split, heel=(70, 0))
    front_y = legs["R"]["ball"][1]
    u = L(0, 1)
    k_dn = min(1.0, u / 0.45)
    k_up = max(0.0, (u - 0.45) / 0.55)
    k_up = 0.5 - 0.5 * math.cos(math.pi * k_up)

    def palm_l(D, Hp, c_, sd):
        return fam.floor_palm(c, D, Hp, "L", c.hw * 0.05, front_y - 0.05)
    arms = arm_ik(palm_l, (-1, 0.2, 0), (0.2, -1, 0.3), key="palm", curl=0.05, fing=(0, 1, 0), sides="L")

    def arm_r(D, Hp, c_, sd):
        sh = fam.shoulder(D, Hp, c, "R")
        base = fam.floor_palm(c, D, Hp, "R", c.hw * 1.3, front_y - 0.12)
        if k_up <= 0:
            return base
        # swing about the shoulder from the floor up to the ceiling
        d0, l0 = unit(base - sh), np.linalg.norm(base - sh)
        d1, l1 = unit(np.array([0.2, -0.05, 1.0])), c.Lpf * 0.85
        dm = unit(d0 * (1 - k_up) + d1 * k_up + np.array([0.5, 0, 0]) * math.sin(math.pi * k_up))
        return sh + dm * min(l0 * (1 - k_up) + l1 * k_up, c.Lpf * 0.88)
    fg = unit(np.array([0, 1.0, 0]) * (1 - k_up) + np.array([0.1, 0, 1.0]) * k_up)
    th = unit(np.array([-1.0, 0.2, 0]) * (1 - k_up) + np.array([0, 1.0, 0]) * k_up)
    arms.update(arm_ik(arm_r, tuple(th), (0.4, -1, 0.0), key="palm", curl=0.05 + 0.2 * k_up, fing=tuple(fg),
                       sides="R"))
    tw = -45 * k_up
    return c.stand(legs, hk=0.49, pel=(88, 0, tw * 0.3), spine=(10, 0, tw * 0.7), neck=(-10, 0, tw * 0.4),
                   arms=arms, balance=None, wsupport=(0.4, 0.6))



def muscle_up(c, t, L, row):
    """Pull from a dead hang to the chest, turn the elbows over the bar and
    press to a straight-arm support above it."""
    u = L(0.0, 1.0)
    gw = c.sw * 1.3
    bar_h = fam.hang_bar_h(c)
    bar = np.array([0, 0.0, bar_h])
    k = max(0.0, min(1.0, (u - 0.45) / 0.55))
    k = 0.5 - 0.5 * math.cos(math.pi * k)
    hang_d = math.sqrt(max(c.Lh ** 2 - max(gw / 2 - c.sw / 2, 0) ** 2, 0.01)) * 0.98
    pull = min(1.0, u / 0.45)
    d = hang_d * (1 - pull) + 0.21 * c.S * pull          # shoulders below the bar
    d = d * (1 - k) + (-c.Lh * 0.78) * k                   # ... then above it (straight-arm support)
    sh_rest = c.r.joint("upperarm01.R")
    lean = 18 * math.sin(math.pi * k)

    def pole(D, Hp, c_, sd):
        s_ = SIDES[sd]
        a = -Z * 0.5 + X * s_ * 0.8
        b = -Y * 1.0 + X * s_ * 0.3
        kk = min(1.0, k * 2.5)               # the elbows turn back early, while still bent
        return unit(a * (1 - kk) + b * kk)
    arms = arm_ik(lambda D, Hp, c_, sd: bar + X * SIDES[sd] * gw / 2, lambda D, Hp, c_, sd: -SIDES[sd] * X,
                  pole, curl=0.9, fing=lambda D, Hp, c_, sd: Z * math.cos(math.radians(125 * k)) + Y * math.sin(math.radians(125 * k)))
    legs = legs_fk((0.06, 0.05 + 0.25 * k, -1), knee=15 + 30 * k, kbend=(0, -1, 0), fdir=(0, 0.4, -1))
    return c.stand(legs, pz=bar_h - d - (sh_rest[2] - c.pz), py=-0.03 + 0.16 * math.sin(math.pi * k), pel=(lean, 0, 0), arms=arms,
                   balance=None, reach=False, planted=(),
                   equip=[dict(E("pullup_station", (0, 0, 0), eid="station", height=bar_h, width=1.3), fit=True)],
                   neck=(-10 * (1 - k), 0, 0))


# ================================================================== standing mobility
_old_standing_still = _REG_OLD["standing_still"]


@tpl("standing_still", "front3q")
def standing_still(c, t, L, row):  # noqa: C901
    """Static standing holds; ankle circles lift one foot and circle it,
    neck stretches tilt the head to the side with the hand resting on it."""
    name = (row.get("name_en") or "").lower()
    if "ankle" in name and "circle" in name:
        from .tpl_lower import one_leg_stand
        a = 2 * math.pi * t
        leg = dict(thigh=np.array([-0.15, 0.85, -0.55]), knee=35, kbend=np.array([0, -1, 0]),
                   fdir=np.array([0.35 * math.cos(a), 1.0, -0.35 + 0.35 * math.sin(a)]))
        return one_leg_stand(c, t, L, row, leg, hold="hips")
    if "neck" in name and ("isometric" in name or "hold" in name):
        # palm against the forehead, the neck pushes into it without moving
        def fh(D, Hp, c_, sd):
            Rt = D[c.r.bi("spine01")]
            return c.lmk(D, Hp, "head_top") + Rt @ Y * 0.11 - Z * 0.07
        arms = arm_ik(fh, (0, 0, 1), (0.3, -0.3, -1), key="palm", curl=0.2, fing=(0, 0.2, 1), sides="R")
        arms.update(arm_fk((0.12, 0.0, -1), elbow=10, thumb="fwd", sides="L"))
        return c.stand(c.feet(w=c.hw * 1.1, toe=8), arms=arms, neck=(L(0, -4), 0, 0))
    if "neck" in name:
        tilt = L(0, 45)
        def hand(D, Hp, c_, sd):
            return c.lmk(D, Hp, "head_top") + X * 0.0 - Z * 0.02
        arms = arm_ik(hand, (0, 1, 0), (-0.2, 0.3, 1), key="palm", curl=0.2, fing=(1, 0, 0.3), sides="L")
        arms.update(arm_fk((0.12, 0.0, -1), elbow=10, thumb="fwd", sides="R"))
        return c.stand(c.feet(w=c.hw * 1.1, toe=8), arms=arms, neck=(0, tilt, 0))
    return _old_standing_still(c, t, L, row)


# ================================================================== side-lying shoulder / thoracic mobility
_old_arm_stretch2 = _REG["arm_stretch"].fn


@tpl("arm_stretch", "front3q")
def arm_stretch_side(c, t, L, row):
    name = (row.get("name_en") or "").lower()
    if "wall shoulder" in name:
        # facing a wall, hands high on it, the chest sinks toward the wall (shoulder flexion stretch)
        legs = c.feet(w=c.hw * 1.1, toe=6)
        wall_y = 0.62 * c.S

        def hands(D, Hp, c_, sd):
            return np.array([SIDES[sd] * 0.2, wall_y - 0.035, 1.78 * c.S])
        arms = arm_ik(hands, (-1, 0, 0), (0.3, -1, -0.3), key="palm", curl=0.05, fing=(0, 0.1, 1))
        fr = c.stand(legs, hk=0.97, pel=(L(10, 30), 0, 0), spine=(L(0, -14), 0, 0), neck=(-10, 0, 0), arms=arms,
                     balance=None, equip=[E("wall", (0, wall_y, 0), R=fam.rz(180), eid="wall")])
        fr.cons.append(("reach_arms", Y, ["L", "R"]))
        return fr
    if "bent over shoulder" in name or "bent-over shoulder" in name:
        # hinge to a level torso, straight arms with the hands on a box top; the chest sinks
        legs = c.feet(w=c.hw * 1.1, toe=6)
        top_z = 0.92 * c.S
        box_y = 1.05 * c.S

        def hands(D, Hp, c_, sd):
            return np.array([SIDES[sd] * 0.2, box_y - 0.12, top_z + 0.004])
        arms = arm_ik(hands, (-1, 0.2, 0), (0.3, -1, 0.3), key="palm", curl=0.05, fing=(0, 1, 0))
        fr = c.stand(legs, hk=0.97, pel=(L(55, 82), 0, 0), spine=(L(0, -12), 0, 0), neck=(-20, 0, 0), arms=arms,
                     balance=None, equip=[E("plyo_box", (0, box_y, 0), eid="box", size=(0.6, 0.4, top_z))])
        fr.cons.append(("reach_arms", Y, ["L", "R"]))
        return fr
    if "open book" not in name and "sleeper" not in name:
        return _old_arm_stretch2(c, t, L, row)
    from .tpl_floor import side_lying
    legs_spec = {sd: dict(thigh=np.array([SIDES[sd] * 0.05, 0.8, -0.6]), knee=90, kbend=np.array([0, -0.2, -1]),
                          fdir=np.array([0, -0.8, -0.3])) for sd in "LR"}
    book = "open book" in name
    u = L(0.0, 1.0)
    fr = side_lying(c, {}, arms=None, spine=(0, 0, 0) if not book else (0, 0, -35 * u))
    b0 = fr.build

    def build():
        spec, eq, ex = b0()
        D, Hp = c.torso(spec)
        spec["leg"] = fam.legs_rel(c, D, legs_spec)
        R0 = D[c.r.bi("root")]
        if book:
            a = math.radians(170 * u)
            spec["arm"] = {"L": dict(ua=unit(R0 @ np.array([-0.05, 1.0, 0.1])), elbow=6, bend=R0 @ Z, thumb=R0 @ X,
                                     curl=0.3),
                           "R": dict(ua=unit(R0 @ np.array([math.sin(a), math.cos(a), 0.12])), elbow=8,
                                     bend=R0 @ Z, thumb=R0 @ Z, curl=0.3)}
        else:
            b = math.radians(70 * u)
            sh = c.J(D, Hp, "upperarm01.L")
            ua = unit(R0 @ np.array([0.0, 1.0, 0.0]))
            fa = unit(R0 @ np.array([math.cos(b), 0.0, -math.sin(b)]))
            el = sh + ua * c.r.dims["L"]["L1"]
            wr = el + fa * c.r.dims["L"]["L2"]
            spec["arm"] = {"L": dict(ua=ua, elbow=90, bend=fa, thumb=-ua, curl=0.4),
                           "R": dict(palm=wr - fa * 0.04 + R0 @ X * 0.04, thumb=R0 @ Y, fing=-fa,
                                     pole=R0 @ np.array([1.0, -0.3, 0.3]), curl=0.2)}
        return spec, eq, ex
    fr.build = build
    return fr



def kneeling_squat(c, t, L, row):
    """Tall kneeling with a back-racked bar: the hips sit back toward the
    heels and drive forward to full extension; shins stay flat on the floor."""
    from .tpl_floor import MAT, SKIN_FLOOR
    u = L(0.0, 1.0)
    T1 = c.r.dims["R"]["T1"]
    # the knees stay where they are on the pad: the hips travel on the arc of
    # the thighs about the knees, back and down toward the heels
    a = math.radians(50 * u)
    kz = 0.074
    hip = np.array([0.0, -T1 * math.sin(a), kz + T1 * math.cos(a)])
    legs = {sd: dict(ankle=np.array([SIDES[sd] * 0.15, -0.46 * c.S, 0.097]), fdir=np.array([0, -1, -0.15]),
                     fup=np.array([0, 0.15, 1]), pole=np.array([0, 1, -0.05])) for sd in "LR"}
    hold = "back_bar" if "barbell" in n_words(row) or "smith" in n_words(row) else ("goblet" if "dumbbell" in n_words(row)
                                                                                   or "kettlebell" in n_words(row) else "head")
    return c.stand(legs, pz=hip[2], py=hip[1], pel=(4 + 26 * u, 0, 0), spine=(4, 0, 0), hold=hold,
                   load=0.3 if hold == "back_bar" else 0.0, balance=None, reach=False, equip=[MAT(0.0)],
                   settle=[("floor_part", c._region("noarms"), SKIN_FLOOR)], planted=())


def n_words(row):
    return words(row) + " " + (row.get("name_en") or "").lower()


# ================================================================== kneeling hamstring stretch
_old_seated_forward_bend = _REG_OLD["seated_forward_bend"]


@tpl("seated_forward_bend", "side")
def seated_forward_bend(c, t, L, row):
    name = (row.get("name_en") or "").lower()
    if "kneeling" not in name:
        return _old_seated_forward_bend(c, t, L, row)
    # half kneeling on the left knee, right leg straight in front on the heel; the hips shift back
    # and the chest folds over the straight leg, hands on the floor either side of it
    from .tpl_floor import MAT, SKIN_FLOOR
    T1 = c.r.dims["R"]["T1"]
    u = L(0.0, 1.0)
    legs = {"L": dict(thigh=unit(np.array([-0.08, -0.25 * u, -1.0])), knee=92 - 10 * u, kbend=np.array([0, -1, 0.0]),
                      fdir=np.array([0, -1, -0.2]), fup=np.array([0, 0.2, 1])),
            "R": dict(thigh=unit(np.array([0.06, 0.8, -0.6])), knee=4, kbend=np.array([0, 0, -1]),
                      fdir=np.array([0, 0.25, 1]), fup=np.array([0, -1, 0.25]))}

    def palm(D, Hp, c_, sd):
        # both hands slide down the front shin as far as they reach
        k = 0.5 * (c.J(D, Hp, "lowerleg01.R") + c.J(D, Hp, "upperleg02.R"))
        a = c.J(D, Hp, "foot.R")
        sh = fam.shoulder(D, Hp, c, sd)
        v = 0.2 + 0.7 * u

        def at(w):
            return k * (1 - w) + a * w + Z * 0.06 + X * SIDES[sd] * 0.05
        R = c.Lpf * 0.93
        if np.linalg.norm(at(v) - sh) > R:      # continuous: largest reachable point down the leg
            lo, hi = 0.0, v
            for _ in range(20):
                mid = 0.5 * (lo + hi)
                if np.linalg.norm(at(mid) - sh) <= R:
                    lo = mid
                else:
                    hi = mid
            v = lo
        p = at(v)
        return p
    arms = arm_ik(palm, (0, 0, 1), (1, -0.4, 0.5), key="palm", curl=0.4, fing=(0, 1, -0.3))
    return c.stand(legs, pz=T1 + 0.08 - 0.06 * u, py=-0.12 * u, pel=(32 + 28 * u, 0, 0), spine=(8 + 18 * u, 0, 0),
                   neck=(10, 0, 0), arms=arms, balance=None, reach=False, equip=[MAT(0.0)],
                   settle=[("floor_part", c._region("noarms"), SKIN_FLOOR)], planted=())


# ================================================================== carioca
_old_high_knees = _REG_OLD["high_knees"]


@tpl("high_knees", (70, 8))
def high_knees(c, t, L, row):
    """High knees; carioca crosses the trailing (left) foot over in front of
    the right while the hips turn, then steps it back out."""
    name = (row.get("name_en") or "").lower()
    if "carioca" not in name:
        return _old_high_knees(c, t, L, row)
    u = L(0.0, 1.0)
    hk = "high knee" in name
    w = c.hw * 1.2
    legs = {"R": c.foot(w / 2, 0.0, 6)}
    lift = math.sin(math.pi * u)
    if hk:
        legs["L"] = dict(thigh=unit(np.array([0.1 + 0.5 * u, 0.25 + 0.75 * lift, -1.0 + 1.0 * lift])),
                         knee=20 + 70 * lift, kbend=np.array([0, -1, 0]), fdir=np.array([0, 0.4, -1]))
    else:
        legs["L"] = c.foot(-w / 2 + (w * 0.95) * u, 0.2 * c.S * u, 6 + 25 * u, 20 * lift, z=0.07 * lift)
    arms = arm_fk((0.25, 0.25 - 0.5 * u, -1), elbow=60, thumb="in")
    return c.stand(legs, hk=0.93, pel=(6, 0, -28 * u), spine=(0, 0, 12 * u), arms=arms, balance="com",
                   planted=["R"], wsupport=(0.0, 1.0))


# ================================================================== two-part combos (RDL / calf raise -> row, high pull, shrug, calf raise)
def _combo_kind(row):
    name = (row.get("name_en") or "").lower()
    if " to " not in name:
        return None
    first, second = name.split(" to ", 1)
    a = "rdl" if ("romanian" in first or "deadlift" in first) else ("calf" if "calf raise" in first else None)
    if a is None:
        return None
    for key, b in (("row", "row"), ("high pull", "high_pull"), ("shrug", "shrug"), ("calf raise", "calf")):
        if key in second:
            return a, b
    return None


def combo(c, t, L, row, kind):
    """First movement in the first half of the rep, the second one after it:
    RDL hinge then (at the bottom) a bent-over row, or back up and a high
    pull / shrug / calf raise; calf raise then high pull / shrug."""
    first, second = kind
    name = (row.get("name_en") or "").lower()
    dbs = "dumbbell" in name or "kettlebell" in name
    u = t % 1.0
    sm = lambda x: 0.5 - 0.5 * math.cos(math.pi * max(0.0, min(1.0, x)))

    def bump(a, b):          # 0 -> 1 -> 0 over [a, b], smooth at both ends
        x = (u - a) / (b - a)
        return 0.5 - 0.5 * math.cos(2 * math.pi * x) if 0.0 <= x <= 1.0 else 0.0
    # one pass (cycle): first movement, then the second, back to the start
    if first == "rdl" and second == "row":
        hinge = sm(u / 0.3) * (1 - sm((u - 0.8) / 0.2))
        k = bump(0.32, 0.78)
        heel = 0.0
    elif first == "rdl":
        hinge = bump(0.0, 0.48)
        k = bump(0.48, 1.0)
        heel = 0.0
    else:
        hinge = 0.0
        heel = 28 * bump(0.0, 0.45)
        k = bump(0.45, 1.0)
    if second == "calf":
        heel, k2 = 28 * k, 0.0
    else:
        k2 = k
    gw = c.sw * 1.15
    clav = None
    if second == "shrug":
        e = 22 * k2
        clav = {"L": (e, -3), "R": (e, -3)}

    def tgt(D, Hp, c_, sd):
        s = SIDES[sd]
        Rt = D[c.r.bi("spine01")]
        sh = fam.shoulder(D, Hp, c, sd)
        lat = X * s * (0.06 if dbs else (gw / 2 - c.sw / 2))
        hang = sh - Z * c.Lh * 0.93 + lat + Y * 0.04 * (1 - hinge)
        if second == "row":
            top = c.bp(D, Hp, "spine02", np.array([s * 0.15 * c.S, c.r.joint("spine02")[1] + 0.08, c.z_nip - 0.1]))
        elif second == "high_pull":
            top = c.lmk(D, Hp, "chest_hi") + Rt @ Y * 0.06 + X * s * (0.14 if dbs else gw / 2) - Z * 0.04
        else:
            top = hang + Z * 0.06          # the shrug lifts the hands with the shoulders
        return hang * (1 - k2) + top * k2

    def pole(D, Hp, c_, sd):
        s = SIDES[sd]
        Rt = D[c.r.bi("spine01")]
        if second == "high_pull":
            return unit((-Y * 0.3 + X * s * 0.6) * (1 - k2) + (Z * 0.9 + X * s * 0.6 - Y * 0.2) * k2)
        if second == "row":
            return unit(Z + X * s * 0.15 - Y * 0.3)
        return unit(-Y * 0.3 + X * s * 0.6)
    thumb = (lambda D, Hp, c_, sd: Y * 1.0 + Z * 0.1) if dbs else (lambda D, Hp, c_, sd: -SIDES[sd] * X)
    arms = arm_ik(tgt, thumb, pole, curl=0.85, fing=lambda D, Hp, c_, sd: -Z)
    eq = [H("dumbbell", sd) for sd in "LR"] if dbs else [H("barbell", "C", "bar", eid="bar")]
    legs = c.feet(w=c.hw * 1.0 + 0.02, toe=6)
    for sd in legs:
        legs[sd]["heel"] = heel
    return c.stand(legs, hk=0.985 - 0.105 * hinge, pel=(2 + 64 * hinge, 0, 0), spine=(6 * hinge, 0, 0),
                   neck=(-30 * hinge, 0, 0), arms=arms, clav=clav, balance="com", load=0.25, equip=eq)


_old_rdl = _REG_OLD["romanian_deadlift"]
_old_calf_raise = _REG_OLD["calf_raise"]


@tpl("romanian_deadlift", (62, 8))
def romanian_deadlift(c, t, L, row):
    k = _combo_kind(row)
    return combo(c, t, L, row, k) if k else _old_rdl(c, t, L, row)


@tpl("calf_raise", (70, 6))
def calf_raise(c, t, L, row):
    if "tibialis" in (row.get("name_en") or "").lower():
        # back against a wall, heels down, the toes and forefoot lift toward the shins
        a = L(0, 28)
        zb = (c.ball_y - c.heel_y) * math.sin(math.radians(a))    # the heel stays down: the ball rises
        legs = c.feet(w=c.hw * 0.95, toe=6, y=0.22 * c.S, z=(zb, zb))
        for sd in legs:
            legs[sd]["heel"] = -a
            legs[sd]["surf"] = 0.0
        fr = c.stand(legs, hk=0.985, pel=(-6, 0, 0), hold="none", balance=None,
                     equip=[E("wall", (0, -0.2 * c.S, 0), eid="wall")])
        fr.planted = []          # the forefoot lifts on purpose (heels stay on the floor)
        return fr
    k = _combo_kind(row)
    return combo(c, t, L, row, k) if k else _old_calf_raise(c, t, L, row)


# ================================================================== Z press (seated on the floor)
_old_overhead_press = _REG_OLD["overhead_press"]


@tpl("overhead_press", (60, 8))
def overhead_press(c, t, L, row):
    name = (row.get("name_en") or "").lower()
    if "z press" not in name and "z-press" not in name:
        return _old_overhead_press(c, t, L, row)
    # sitting tall on the floor, legs straight in front; bar from the front rack to lockout
    from .tpl_floor import MAT
    legs = legs_fk((0.1, 1.0, 0.0), knee=3, kbend=(0, 0, -1), fdir=(0, 0.1, 1))
    db = "dumbbell" in name or "kettlebell" in name
    if db:
        arms, eq = fam.press_db(c, L(0, 1), "oh", w0=c.sw * 1.45, w1=c.sw * 1.0)
    else:
        from .tpl_upper import press_bar
        arms, eq = press_bar(c, L(0, 1), "oh", gw=c.sw * 1.3)
    return fam.floor_body(c, pitch=-2, legs=legs, arms=arms, spine=(0, 0, 0), equip=[MAT(0.0)] + list(eq))


# ================================================================== prone hip circle
_old_fire_hydrant = _REG_OLD["fire_hydrant"]


@tpl("fire_hydrant", (70, 14))
def fire_hydrant(c, t, L, row):
    name = (row.get("name_en") or "").lower()
    if "prone" not in name:
        return _old_fire_hydrant(c, t, L, row)
    # face down on the forearms; the right knee, bent to 90, lifts and circles out to the side
    from .tpl_floor import MAT
    a = 2 * math.pi * (t % 1.0)
    rx_ = 0.9 * (0.5 - 0.5 * math.cos(a))
    rz_ = 0.2 + 0.25 * math.sin(a)
    legs = {"L": dict(thigh=np.array([-0.06, -1, 0.02]), knee=4, kbend=np.array([0, 0, 1]), fdir=np.array([0, 0.2, 1]),
                      fup=np.array([0, -1, 0.3])),
            "R": dict(thigh=unit(np.array([0.06 + rx_, -1, rz_])), knee=90, kbend=np.array([0, 0, 1]),
                      fdir=np.array([0, 0.2, 1]))}
    arms = arm_fk((0.3, 0.25, -1.0), elbow=95, bend=(0, 1, 0), thumb="up", world=True)
    return fam.floor_body(c, pitch=82, legs=legs, arms=arms, spine=(-8, 0, 0), neck=(-12, 0, 0), equip=[MAT(0.0)])


# ================================================================== half-kneeling mini-band curl / row
def _half_kneel_band(c, t, L, row, mode):
    """Half kneeling (right foot forward), a mini band from under the front foot to the hands."""
    from .tpl_floor import kneeling
    u = L(0.0, 1.0)
    foot = np.array([c.hw * 0.55, 0.45 * c.S + c.ball_y * 0.3, 0.02])
    if mode == "curl":
        arms = arm_fk((0.08, 0.05, -1), elbow=L(8, 135), thumb="sup", bend=(0, 1, 0), curl=0.88)
    else:
        def tgt(D, Hp, c_, sd):
            sh = fam.shoulder(D, Hp, c, sd)
            far = fam.within(c, sh, foot + np.array([SIDES[sd] * 0.08 - (sh[0] - 0), 0, 0.25]) - sh, 0.92)
            near = c.bp(D, Hp, "spine02", np.array([SIDES[sd] * 0.15 * c.S, c.r.joint("spine02")[1] + 0.08,
                                                   c.z_nip - 0.1]))
            return far * (1 - u) + near * u
        arms = arm_ik(tgt, lambda D, Hp, c_, sd: unit(Y + Z * 0.3), lambda D, Hp, c_, sd: unit(Z - Y * 0.6 + X * SIDES[sd] * 0.3),
                      curl=0.85, fing=lambda D, Hp, c_, sd: unit(-Z + X * -SIDES[sd] * 0.2))
    eq = [seg(f"mb{sd}", foot + np.array([SIDES[sd] * 0.04, 0, 0]), f"grip{sd}", 0.007, "band") for sd in "LR"]
    return kneeling(c, t, L, row, arms=arms, equip=eq, half=True, pitch=4 if mode == "curl" else 20)


_old_db_curl = _REG_OLD["db_curl"]
_old_barbell_row = _REG_OLD["barbell_row"]


@tpl("db_curl", (55, 8))
def db_curl(c, t, L, row):
    if "kneeling" in (row.get("name_en") or "").lower() and "band" in words(row):
        return _half_kneel_band(c, t, L, row, "curl")
    return _old_db_curl(c, t, L, row)


@tpl("barbell_row", (60, 9))
def barbell_row(c, t, L, row):
    if "kneeling" in (row.get("name_en") or "").lower() and "band" in words(row):
        return _half_kneel_band(c, t, L, row, "row")
    return _old_barbell_row(c, t, L, row)


# ================================================================== hanging leg / knee raises
def _leg_dir(a_deg, side_deg=0.0):
    """World thigh direction: a_deg from straight down toward the front
    (0 = hanging, 90 = horizontal, 180 = straight up), swung side_deg about
    the vertical toward the athlete's left (+) / right (-)."""
    a = math.radians(a_deg)
    s = math.radians(side_deg)
    h = math.sin(a)
    return (-h * math.sin(s), h * math.cos(s), -math.cos(a))


def _legs_dir(a_deg, side_deg, knee, spread=0.04, **kw):
    """Both legs pointing the same world direction (legs_fk mirrors x for
    the left leg, so a sideways swing is undone per leg), a little apart."""
    out = {}
    for sd in "LR":
        d = list(_leg_dir(a_deg, side_deg))
        d[0] = d[0] * SIDES[sd] + spread
        out.update(legs_fk(tuple(d), knee=knee, kbend=(0, -1, 0), sides=sd, **kw))
    return out


@tpl("hanging_leg_raise", (60, 8))
def hanging_leg_raise(c, t, L, row):
    """Hanging from the bar on straight arms, feet off the floor the whole
    time.  Variants from the name: knee raise, leg raise (to parallel), pike /
    toes-to-bar (toes to the bar: the torso tips back under the bar),
    kipping (a kip swing feeds the toes-to-bar), oblique knee raise
    (alternating, knees to one shoulder), windshield wiper (legs held up near
    the bar, swung side to side); the captain's chair versions rest on the
    forearm pads with the back on the pad."""
    from .tpl_misc import captain_chair
    name = (row.get("name_en") or "").lower()
    n = words(row)
    if "captain" in n or "vertical" in name:
        return captain_chair(c, t, L, row)
    u = L(0, 1)
    gw = c.sw * (1.75 if "wide" in n else 1.45)
    lean = 0.0                 # torso tips back (negative pitch) as the legs come up high
    py = -0.03
    spine = 0.0
    side = 0.0
    yaw = 0.0
    hk = 0.985
    if "windshield" in name or "oblique" in name:
        hk = 0.97              # a little slack: the turned hips load one arm more
    if "windshield" in name:
        # legs held up near the bar, swung from one side to the other (cycle)
        w = 60 * math.sin(2 * math.pi * t)
        legs = _legs_dir(140, w, 6)
        lean, spine, yaw = -38, 18, -0.25 * w
        py = 0.12 * c.S
    elif "pike" in name or "toes" in name:
        knee = 22 if "toes" in name else 4
        a = 4 + 158 * u
        kip = 0.0
        if "kipping" in name:
            kip = math.sin(math.pi * min(1.0, u / 0.4))        # kip swing early in the rep
            a = 4 + 158 * max(0.0, (u - 0.2) / 0.8) - 25 * kip
        legs = legs_fk(_leg_dir(a), knee=knee + 25 * kip, kbend=(0, -1, 0), fdir=(0, 0.4, -1))
        k = max(0.0, (u - 0.25) / 0.75)
        lean = -62 * k + 14 * kip                              # chest through on the kip, then tip back
        spine = 22 * k - 8 * kip
        py = -0.03 + 0.2 * c.S * k - 0.08 * kip
    elif "knee" in name:
        if "oblique" in name:
            side = (1 if (row.get("_side") or "R") == "R" else -1) * 50 * u
        legs = _legs_dir(5 + 110 * u, side, 10 + 100 * u)
        lean, spine, yaw = -14 * u, 22 * u, -0.35 * side
        py = -0.03 + 0.05 * u
    else:                                                       # straight-leg raise to (above) parallel
        legs = legs_fk(_leg_dir(5 + 95 * u), knee=6, kbend=(0, -1, 0))
        lean, spine = -18 * u, 16 * u
        py = -0.03 + 0.08 * u
    return fam.hang(c, pull=0.0, gw=gw, legs=legs, py=py, pel=(lean, 0, yaw), spine=(spine, 0, 0.4 * yaw),
                    neck=(-0.4 * spine, 0, 0), hang_k=hk,
                    fit="windshield" not in name)     # legs held high: frame the athlete, not the whole station


# ================================================================== suspension straps, standing lean-back
TRX_H = 2.45


def _strap_eq(anchor, sides="LR"):
    """Anchor (fitted whole, so straps and hands stay in the picture) and one
    strap per gripping hand."""
    out = [dict(E("trx_anchor", anchor * np.array([1, 1, 0]), eid="trx", h=float(anchor[2])), fit=True)]
    for sd in sides:
        out.append(seg(f"strap{sd}", anchor, f"grip{sd}", 0.012, "strap"))
    return out


def _lean_body(c, lean, feet_y=0.0, yaw=0.0):
    """Straight body pivoting back about the ankles (lean deg from vertical,
    heels on the floor).  Returns pelvis (y, z) and the legs spec."""
    a = math.radians(lean)
    an = c.r.joint("foot.R")
    v = c.r.pc_rest - an                    # ankle -> pelvis, rest
    pel = np.array([0, feet_y, an[2]]) + np.array([0, -v[2] * math.sin(a) + v[1] * math.cos(a),
                                                     v[2] * math.cos(a) + v[1] * math.sin(a)])
    legs = {sd: dict(ankle=np.array([SIDES[sd] * c.hw * 0.55, feet_y, an[2]]), fdir=np.array([0, 1.0, 0.0]),
                     fup=Z, pole=np.array([0, 1, 0.2])) for sd in "LR"}
    return pel, legs


def _anchor_for(c, lean0, feet_y=0.0, above=25.0):
    """Anchor at TRX_H on the line of the straight arms (arm + strap in one
    line under load), the arms `above` deg higher than perpendicular to the
    leaning body so the straps keep a normal length."""
    a = math.radians(lean0)
    an = c.r.joint("foot.R")
    hs = c.z_sh - an[2]
    sh = np.array([0, feet_y - hs * math.sin(a), an[2] + hs * math.cos(a)])
    b = a + math.radians(above)
    d = np.array([0, math.cos(b), math.sin(b)])
    s = (TRX_H - sh[2]) / d[2]
    return np.array([0, sh[1] + d[1] * s, TRX_H])


def _suspension_stand(c, t, L, row, kind):
    """Facing the anchor, body straight and leaning back on the straps.
    curl: straight arms at shoulder height -> fists to the forehead (palms up),
    body rises.  clock: straight arms open to 9-3, 10-2 and 12 o'clock in turn
    (cycle).  power: one strap in the right hand, torso turned left with the
    left hand reaching down -> row and turn right, left arm to the ceiling."""
    lean0 = 50.0 if kind == "row" else 38.0
    anchor = _anchor_for(c, lean0, above=10.0 if kind == "row" else 25.0)
    reach = c.Lh * 1.08          # aim a little beyond the hand: the arms end straight (shoulders reach forward)
    if kind == "clock":
        ph = (t * 3.0) % 1.0 if t < 1.0 - 1e-9 else 0.0
        idx = min(2, int(t * 3.0 + 1e-9))
        op = math.sin(math.pi * ph)
        lean = lean0 - 14 * op
    else:
        u = L(0, 1)
        lean = lean0 - {"curl": 18, "row": 10}.get(kind, 14) * u
    pel, legs = _lean_body(c, lean)

    def toward(D, Hp, sd):
        sh = fam.shoulder(D, Hp, c, sd)
        return sh, unit(anchor + X * SIDES[sd] * 0.12 - sh)

    if kind == "curl":
        def tgt(D, Hp, c_, sd):
            sh, d = toward(D, Hp, sd)
            straight = sh + d * reach
            fh = c.lmk(D, Hp, "forehead") + X * SIDES[sd] * 0.09 + d * 0.1
            return straight * (1 - u) + fh * u
        arms = arm_ik(tgt, lambda D, Hp, c_, sd: SIDES[sd] * X,
                      lambda D, Hp, c_, sd: toward(D, Hp, sd)[1] * 0.6 - Z * 0.4, curl=0.9)
        return c.stand(legs, pz=pel[2], py=pel[1], pel=(-lean, 0, 0), neck=(lean * 0.5, 0, 0), arms=arms,
                       equip=_strap_eq(anchor), balance=None, reach=False, planted=())
    if kind == "clock":
        ang = [(88, 0), (60, 38), (12, 80)][idx]      # (out to the side, up) at full opening

        def tgt(D, Hp, c_, sd):
            sh, d = toward(D, Hp, sd)
            Rb = D[c.r.bi("spine01")]
            side = Rb @ (X * SIDES[sd])
            up = Rb @ Z
            o, v = math.radians(ang[0] * op), math.radians(ang[1] * op)
            w = unit(d * math.cos(o) * math.cos(v) + side * math.sin(o) * math.cos(v) + up * math.sin(v))
            return sh + w * reach
        arms = arm_ik(tgt, lambda D, Hp, c_, sd: Z, lambda D, Hp, c_, sd: -Z * 0.5 - Y * 0.5, curl=0.9)
        return c.stand(legs, pz=pel[2], py=pel[1], pel=(-lean, 0, 0), neck=(lean * 0.5, 0, 0), arms=arms,
                       equip=_strap_eq(anchor), balance=None, reach=False, planted=())
    if kind == "row":
        def tgt(D, Hp, c_, sd):
            sh, d = toward(D, Hp, sd)
            Rb = D[c.r.bi("spine01")]
            rowed = sh + Rb @ (Y * 0.12 + X * SIDES[sd] * 0.08 - Z * 0.1)     # handles at the sides of the chest
            return (sh + d * reach) * (1 - u) + rowed * u
        arms = arm_ik(tgt, lambda D, Hp, c_, sd: Z, lambda D, Hp, c_, sd: -Z * 0.6 + X * SIDES[sd] * 0.6 - Y * 0.3,
                      curl=0.9)
        return c.stand(legs, pz=pel[2], py=pel[1], pel=(-lean, 0, 0), neck=(lean * 0.4, 0, 0), arms=arms,
                       equip=_strap_eq(anchor), balance=None, reach=False, planted=())
    # power pull: right hand on the strap
    yaw = L(-40, 25)                                 # - turned left, + turned right

    def tgt_r(D, Hp, c_, sd):
        sh, d = toward(D, Hp, "R")
        straight = sh + d * reach
        rowed = sh + D[c.r.bi("spine01")] @ (Y * 0.12 + X * 0.08 - Z * 0.1)     # fist at the side of the chest
        return straight * (1 - u) + rowed * u

    def tgt_l(D, Hp, c_, sd):
        sh = fam.shoulder(D, Hp, c, "L")
        down = unit(np.array([0.35, 0.6, -0.75]))
        upw = unit(np.array([-0.15, -0.2, 1.0]))
        w = unit(down * (1 - u) + upw * u + np.array([0, 0.3, 0]) * math.sin(math.pi * u))
        return sh + w * c.Lh * 0.95
    arms = arm_ik(tgt_r, lambda D, Hp, c_, sd: Z, lambda D, Hp, c_, sd: -Z * 0.3 + X * 0.6 - Y * 0.4, curl=0.9,
                  sides="R")
    arms.update(arm_ik(tgt_l, lambda D, Hp, c_, sd: Y, lambda D, Hp, c_, sd: -Y * 0.5 - X * 0.5, curl=0.2,
                       sides="L"))
    return c.stand(legs, pz=pel[2], py=pel[1], pel=(-lean * 0.8, 0, yaw * 0.4), spine=(-lean * 0.2, 0, yaw * 0.6),
                   neck=(lean * 0.5, 0, yaw * 0.2), arms=arms, equip=_strap_eq(anchor, "R"), balance=None,
                   reach=False, planted=())


_old_inverted_row = _REG_OLD["inverted_row"]


@tpl("inverted_row", "side")
def inverted_row(c, t, L, row):
    """Inverted row under a bar or on straps; the standing lean-back strap
    moves (biceps curl, clock pull, power pull) have their own motion."""
    name = (row.get("name_en") or "").lower()
    if "suspension" in name or "trx" in name:
        if "curl" in name:
            return _suspension_stand(c, t, L, row, "curl")
        if "clock" in name:
            return _suspension_stand(c, t, L, row, "clock")
        if "power pull" in name:
            return _suspension_stand(c, t, L, row, "power")
        if name.endswith(" row"):
            return _suspension_stand(c, t, L, row, "row")
    fr = _old_inverted_row(c, t, L, row)
    b = fr.build

    def build():
        spec, eq, ex = b()
        out = []
        for e in eq:                       # the whole bar / strap anchor stays in the picture
            if e.get("kind") in ("trx_anchor", "barbell"):
                e = dict(e, fit=True)
            out.append(e)
        return spec, out, ex
    fr.build = build
    return fr


# ================================================================== pistol squat family (one leg the whole time)
@tpl("pistol_squat", (70, 8))
def pistol_squat(c, t, L, row):
    """Standing on the right leg the whole rep; the free left leg is held
    straight out in front and rises with the descent so it never touches
    the floor.  Variants: kettlebell at the chest, holding suspension straps,
    holding a locked Smith bar, on a balance-trainer dome (the dome is added
    under the standing foot), and the glute drop (a small single-leg sit-back)."""
    name = (row.get("name_en") or "").lower()
    n = words(row)
    drop = "glute drop" in name
    hk = L(0.98, 0.74 if drop else 0.42)
    pitch = L(4, 24 if drop else 42)
    pz = c.pz * hk
    dome = "bosu" in n or "balance trainer" in name
    # on a dome the standing foot is on its top; the pelvis is lifted by the
    # generic dome step (templates._raise_on_dome), which leaves feet to a
    # template that draws its own dome
    from .templates import DOME_H
    legs = {"R": c.foot(c.hw * 0.2, 0.0, 8, z=DOME_H if dome else 0.0)}
    # free leg: straight, angle from straight down so the foot (ankle + shoe)
    # stays >= 9 cm above the floor; a dome under the standing foot raises the hip
    hip = pz - (c.pz - c.z_hip) + (DOME_H if dome else 0.0)
    ratio = max(-1.0, min(1.0, (hip - 0.12) / (c.leg + 0.16)))
    a = max(math.radians(26 if not drop else 35), math.acos(ratio))     # glute drop: foot clear of the dome
    if not drop:
        a = max(a, math.radians(L(26, 84)))
    lf = dict(thigh=np.array([-0.06, math.sin(a), -math.cos(a)]), knee=4, kbend=np.array([0, -1, 0]),
              fdir=np.array([0, 0.25, 1]))
    legs["L"] = lf
    neck = (L(0, -14), 0, 0)
    if "kettlebell" in name or n.strip().startswith("kettlebell"):
        fr = c.stand(legs, pz=pz, pel=(pitch, 0, 0), hold="kb_goblet", load=0.2, wsupport=None, neck=neck)
    elif "smith" in n:
        # the machine stands beside the athlete (bar running front to back on
        # the right), so the free leg reaches forward clear of the frame; the
        # right hand holds the locked, unloaded bar, the left arm reaches forward
        bar_x, bar_h = 0.62 * c.S, 0.98 * c.S
        Rz = ((0, -1, 0), (1, 0, 0), (0, 0, 1))
        bar = np.array([bar_x, 0.04 * c.S, bar_h])
        armR = arm_ik(lambda D, Hp, c_, sd: bar, lambda D, Hp, c_, sd: Y, (0.3, -1, -0.4), curl=0.9,
                      fing=(0, 0, 1), sides="R")["R"]
        armL = arm_fk((0.1, 1, L(-0.15, 0.1)), elbow=5, thumb="up", sides="L")["L"]
        eq = [E("smith", (bar_x, 0, 0), R=Rz, eid="smith"), E("smith_bar", bar, R=Rz, eid="sbar", plates=0)]
        fr = c.stand(legs, pz=pz, pel=(pitch, 0, 0), arms={"L": armL, "R": armR}, equip=eq, neck=neck, balance=None)
    elif "suspension" in n or "trx" in n:
        anchor = np.array([0, 0.95 * c.S, TRX_H])

        def tgt(D, Hp, c_, sd):
            sh = fam.shoulder(D, Hp, c, sd)
            return sh + unit(anchor + X * SIDES[sd] * 0.12 - sh) * c.Lh * L(0.9, 0.97)
        arms = arm_ik(tgt, lambda D, Hp, c_, sd: Z, lambda D, Hp, c_, sd: -Z * 0.6 + X * SIDES[sd] * 0.5, curl=0.9)
        fr = c.stand(legs, pz=pz, pel=(pitch * 0.8, 0, 0), arms=arms, equip=_strap_eq(anchor), neck=neck,
                     balance=None)
    else:
        arms = arm_fk((0.1, 1, L(-0.15, 0.1)), elbow=5, thumb="up")
        if drop:
            arms = arm_fk((0.25, 0.6, -0.6), elbow=20, thumb="up")
        fr = c.stand(legs, pz=pz, pel=(pitch, 0, 0), arms=arms, neck=neck)
    if dome:
        # the dome under the standing foot is part of the picture (the camera fits it whole)
        dome = dict(E("bosu", (c.hw * 0.2, c.ball_y - 0.06, 0), eid="bosu"), fit=True)
        b = fr.build

        def build():
            spec, eq, ex = b()
            return spec, list(eq) + [dome], ex
        fr.build = build
    fr.free_legs = ["L"]
    return fr


# ================================================================== one-arm Smith upright row
_old_upright_row = _REG_OLD["upright_row"]


@tpl("upright_row", (40, 8))
def upright_row(c, t, L, row):
    """Upright row family; the one-arm Smith version holds the middle of the
    bar with the right hand (body shifted left so the hand is in front of the
    sternum, turned a little side-on) and pulls it straight up the guide rails
    to chest height with the elbow high; the bar stays level on the rails and
    the left arm hangs free."""
    name = (row.get("name_en") or "").lower()
    if not ("smith" in name and ("one-arm" in name or "single-arm" in name or "one arm" in name)):
        return _old_upright_row(c, t, L, row)
    u = L(0, 1)
    px = -0.11 * c.S
    by = 0.17
    sx = px + c.sw / 2                 # right shoulder, across from the hand at x = 0
    z0 = c.z_sh - math.sqrt(max((1.02 * c.Lh) ** 2 - sx ** 2 - by ** 2, 0.01))    # arm hanging straight
    z1 = c.z_clav - 0.1 * c.S
    grip = np.array([0.0, by, z0 * (1 - u) + z1 * u])
    arms = arm_ik(lambda D, Hp, c_, sd: grip, (-1, 0, 0), (1, -0.4, 0.6), curl=0.9, fing=(0, 0, -1), sides="R")
    arms.update(arm_fk((-0.12, 0.02, -1), elbow=12, thumb="fwd", curl=0.4, sides="L"))
    legs = c.feet(w=c.hw * 1.15, toe=8, dx=px)
    for sd in legs:
        legs[sd]["yaw"] = legs[sd].get("yaw", 8) - 12
    eq = [E("smith", (0, by - 0.02, 0), eid="smith"), H("smith_bar", "R", ((1, 0, 0), (0, 1, 0), (0, 0, 1)), eid="sbar")]   # level on the rails
    return c.stand(legs, px=px, pel=(2, 0, -12), spine=(0, 0, -4 * u), arms=arms, equip=eq, load=0.1, balance=None)


# ================================================================== landmine rotation: plate end in the picture
_old_standing_twist = _REG_OLD["standing_twist"]


@tpl("standing_twist", "front")
def standing_twist(c, t, L, row):
    """Standing twists; with a landmine the plate-loaded sleeve end is kept
    inside the picture (the camera fits it, the floor pivot may leave)."""
    fr = _old_standing_twist(c, t, L, row)
    if "landmine" not in words(row):
        return fr
    return _wrap_build(fr, lambda spec, eq, ex: [dict(e, fit="far") if e["kind"] == "landmine_bar" else e for e in eq])


# ================================================================== suspension reverse plank: heels in the cradles
_old_reverse_plank = _REG_OLD["reverse_plank"]
CRADLE_H = 0.3


@tpl("reverse_plank", (80, 8))
def reverse_plank(c, t, L, row):
    """Reverse plank family; on suspension straps the heels rest in the foot
    cradles about 30 cm off the floor under the anchor, hands on the floor
    behind the hips, hips lifted to a straight body."""
    name = (row.get("name_en") or "").lower()
    if not ("suspension" in name or "trx" in name):
        return _old_reverse_plank(c, t, L, row)
    from .tpl_floor import MAT
    arms = arm_ik(lambda D, Hp, c_, sd: np.array([SIDES[sd] * 0.2 * c.S, -0.42 * c.S, 0.004]), (1, 0, 0),
                  (0, -1, 0.0), key="palm", curl=0.05, fing=(0, -1, 0))
    fy = 0.85 * c.S
    legs = {sd: dict(ankle=np.array([SIDES[sd] * 0.1, fy, CRADLE_H + 0.075]), fdir=np.array([0, 0.25, 1]),
                     fup=np.array([0, -1, 0.1]), pole=np.array([0, 0, 1])) for sd in "LR"}
    pitch = L(-81, -84)                 # a hold: body straight from the start, breathing only
    pz = L(0.49, 0.52) * c.S - (0.03 if c.g == "f" else 0.0)    # shorter arms: hands stay on the floor
    anchor = np.array([0, fy + 0.05, TRX_H])
    eq = [MAT(0.2), E("trx_anchor", anchor * np.array([1, 1, 0]), eid="trx", h=TRX_H)]   # straps run up out of the picture
    r = c.r
    for sd in "LR":
        i = r.bi(f"foot.{sd}")
        heel = r.joint(f"foot.{sd}") + np.array([0, -0.06, -0.06])

        def cradle(pts, D, Hp, c_, i=i, heel=heel, s_=SIDES[sd]):
            return Hp[i] + D[i] @ (heel - r.H[i])

        def c0(pts, D, Hp, c_, i=i, heel=heel):
            return Hp[i] + D[i] @ (heel + np.array([-0.05, 0.0, 0.0]) - r.H[i])

        def c1(pts, D, Hp, c_, i=i, heel=heel):
            return Hp[i] + D[i] @ (heel + np.array([0.05, 0.0, 0.0]) - r.H[i])
        eq.append(seg(f"strap{sd}", anchor, cradle, 0.012, "strap"))
        eq.append(seg(f"cradle{sd}", c0, c1, 0.02, "strap"))
    return c.stand(legs, pz=pz, py=0.0, pel=(pitch, 0, 0), arms=arms, balance=None, reach=False,
                   equip=eq, neck=(L(20, -10), 0, 0), planted=())


# ================================================================== suspension jump squat: hands stay on the handles
_old_jump_squat = _REG_OLD["jump_squat"]


@tpl("jump_squat", (55, 8))
def jump_squat(c, t, L, row):
    """Jump squat family; with suspension straps the hands hold the handles
    in front of the chest the whole time (squat, drive, airborne)."""
    fr = _old_jump_squat(c, t, L, row)
    n = words(row)
    if not ("suspension" in n or "trx" in n):
        return fr
    anchor = np.array([0, 0.95 * c.S, TRX_H])

    def tgt(D, Hp, c_, sd):
        sh = fam.shoulder(D, Hp, c, sd)
        return sh + unit(anchor + X * SIDES[sd] * 0.12 - sh) * c.Lh * 0.8
    arms = arm_ik(tgt, lambda D, Hp, c_, sd: Z, lambda D, Hp, c_, sd: -Z * 0.6 + X * SIDES[sd] * 0.5, curl=0.9)
    b = fr.build

    def build():
        spec, eq, ex = b()
        D, Hp = c.torso(spec)
        spec["arm"] = {sd: arms[sd](D, Hp, c) for sd in "LR"}
        return spec, list(eq) + _strap_eq(anchor), ex
    fr.build = build
    return fr
