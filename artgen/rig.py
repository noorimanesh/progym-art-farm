"""Pure-numpy posing and skinning of the MakeHuman default skeleton.

Coordinates: metres, Z up, the character faces +Y, its right side is +X.
Side sign s: right = +1, left = -1.

A pose spec is a dict (see Rig.solve).  Limbs are solved with analytic
two-bone IK and pole vectors; hands and feet get full orientation frames.
Skinning is linear blend skinning with the MakeHuman default weights.
"""
import math

import numpy as np

from . import body_model

X = np.array([1.0, 0, 0])
Y = np.array([0, 1.0, 0])
Z = np.array([0, 0, 1.0])
SIDES = {"L": -1, "R": 1}


def unit(v):
    v = np.asarray(v, dtype=float)
    n = np.linalg.norm(v)
    return v / n if n > 1e-9 else v * 0


def orth(v, axis):
    v = np.asarray(v, dtype=float)
    a = unit(axis)
    return unit(v - a * np.dot(v, a))


def rot(axis, deg):
    a = unit(axis)
    t = math.radians(deg)
    c, s = math.cos(t), math.sin(t)
    x, y, z = a
    C = 1 - c
    return np.array([[c + x * x * C, x * y * C - z * s, x * z * C + y * s],
                     [y * x * C + z * s, c + y * y * C, y * z * C - x * s],
                     [z * x * C - y * s, z * y * C + x * s, c + z * z * C]])


def rot_between(a, b):
    a, b = unit(a), unit(b)
    c = np.cross(a, b)
    s = np.linalg.norm(c)
    d = float(np.dot(a, b))
    if s < 1e-8:
        if d > 0:
            return np.eye(3)
        p = orth(X if abs(a[0]) < 0.9 else Y, a)
        return rot(p, 180)
    return rot(c, math.degrees(math.atan2(s, d)))


def frame(a, b):
    """Orthonormal frame with first axis a and second axis in the a-b plane."""
    a = unit(a)
    b = orth(b, a)
    return np.stack([a, b, np.cross(a, b)], axis=1)


def body_rot(pitch=0.0, roll=0.0, yaw=0.0):
    """pitch + = top tips forward (+Y); roll + = top tips to the right (+X);
    yaw + = turn to the right (front toward +X)."""
    return rot(Z, -yaw) @ rot(X, -pitch) @ rot(Y, roll)


def slerp_rot(R, t):
    """Fraction t of rotation R (axis-angle scaling)."""
    ang = math.degrees(math.acos(max(-1.0, min(1.0, (np.trace(R) - 1) / 2))))
    if ang < 1e-6:
        return np.eye(3)
    axis = np.array([R[2, 1] - R[1, 2], R[0, 2] - R[2, 0], R[1, 0] - R[0, 1]])
    if np.linalg.norm(axis) < 1e-9:
        w, V = np.linalg.eig(R)
        axis = np.real(V[:, np.argmin(abs(w - 1))])
    return rot(axis, ang * t)


SEG_MASS = {  # fraction of body mass, approximate
    "head": 0.081, "trunk": 0.497, "ua": 0.028, "fa": 0.016, "hand": 0.006,
    "thigh": 0.1, "shin": 0.0465, "foot": 0.0145,
}


class Rig:
    def __init__(self, gender):
        d = body_model.load(gender)
        self.gender = gender
        self.verts = d["verts"].astype(np.float64)
        self.faces = d["faces"]
        self.H = d["heads"].astype(np.float64)
        self.T = d["tails"].astype(np.float64)
        self.P = d["parents"]
        self.names = [str(n) for n in d["names"]]
        self.W = d["W"].astype(np.float32)
        self.idx = {n: i for i, n in enumerate(self.names)}
        self.nb = len(self.names)
        J = self.joint
        self.pc_rest = 0.5 * (J("upperleg01.L") + J("upperleg01.R"))
        self.dims = {}
        for sd in "LR":
            S, E, Wr = J(f"upperarm01.{sd}"), J(f"lowerarm01.{sd}"), J(f"wrist.{sd}")
            Hp, K, A = J(f"upperleg01.{sd}"), J(f"lowerleg01.{sd}"), J(f"foot.{sd}")
            self.dims[sd] = dict(L1=np.linalg.norm(E - S), L2=np.linalg.norm(Wr - E),
                                 T1=np.linalg.norm(K - Hp), T2=np.linalg.norm(A - K))
        self.hand_rest = {sd: self._hand_frame_rest(sd) for sd in "LR"}
        self.foot_rest = {sd: self._foot_rest(sd) for sd in "LR"}
        v = self.verts
        self.height = v[:, 2].max()
        self.shoulder_w = abs(J("upperarm01.R")[0] - J("upperarm01.L")[0])
        self.hip_w = abs(J("upperleg01.R")[0] - J("upperleg01.L")[0])
        self.pelvis_h = self.pc_rest[2]
        # children lists for FK
        self.order = list(range(self.nb))  # names are stored topologically

    # ------------------------------------------------------------------ rest
    def joint(self, name):
        return self.H[self.idx[name]].copy()

    def _hand_frame_rest(self, sd):
        J = self.joint
        s = SIDES[sd]
        w = J(f"wrist.{sd}")
        k2, k5 = J(f"finger2-1.{sd}"), J(f"finger5-1.{sd}")
        km = J(f"finger3-1.{sd}")
        y = unit(km - w)
        t = orth(k2 - k5, y)
        F = self.hand_axes(y, t, sd)
        kmid = 0.5 * (k2 + k5)
        n = F[:, 2]
        # grip centre (where a bar sits in a closed fist) and palm contact
        grip = kmid + 0.034 * n - 0.004 * y
        palm = w + 0.55 * (kmid - w) + 0.028 * n
        return dict(F=F, grip=grip - w, palm=palm - w, wrist=w)

    @staticmethod
    def hand_axes(y, t, sd):
        """Hand frame: y fingers, t thumb side, n palm normal (out of palm)."""
        y = unit(y)
        t = orth(t, y)
        n = np.cross(y, t) * (1 if sd == "L" else -1)
        return np.stack([y, t, n], axis=1)

    def _foot_rest(self, sd):
        J = self.joint
        a = J(f"foot.{sd}")
        ball = 0.5 * (J(f"toe1-1.{sd}") + J(f"toe5-1.{sd}"))
        ball[2] = 0.0
        heel_idx = np.where((np.abs(self.verts[:, 0] - a[0]) < 0.05) & (self.verts[:, 2] < 0.05))[0]
        heel_y = self.verts[heel_idx, 1].min()
        heel = np.array([a[0], heel_y, 0.0])
        fwd = unit(np.array([ball[0] - a[0], ball[1] - a[1], 0]))
        F = np.stack([fwd, np.cross(Z, fwd), Z], axis=1)  # fwd, left-ish, up
        toe_tip = self.verts[np.abs(self.verts[:, 0] - ball[0]) < 0.05][:, 1].max()
        return dict(F=F, ankle=a, ball=ball, heel=heel, toe_len=toe_tip - ball[1])

    # ------------------------------------------------------------ helpers
    def bi(self, name):
        return self.idx[name]

    # ---------------------------------------------------------------- solve
    def solve(self, spec):
        """spec keys (all optional except pelvis):
        pelvis: xyz of pelvis centre (midpoint of hip joints)
        pel: (pitch, roll, yaw) of pelvis, degrees
        spine: (flex, side, twist) total over the lumbar/thoracic chain
        neck: (flex, side, twist)
        clav: {'L': (elev, protract)}  added to automatic shoulder girdle motion
        arm: {'L': dict(grip=xyz | palm=xyz | wrist=xyz, thumb=dir, fing=dir,
                        pole=dir, curl=0..1, ua=dir, elbow=deg, bend=dir)}
        leg: {'L': dict(ball=xyz, yaw=deg, heel=deg, pole=dir) or
                   dict(ankle=xyz, fdir=dir, fup=dir, pole=dir) or
                   dict(thigh=dir, knee=deg, kbend=dir, fdir=dir, fup=dir),
                   toe=deg}
        """
        nb = self.nb
        Dloc = {}  # explicit world-rotation overrides by bone index
        R0 = body_rot(*spec.get("pel", (0, 0, 0)))
        if spec.get("twist"):           # turn about the body's own long axis (rotation push-up, T push-up)
            R0 = R0 @ rot(Z, float(spec["twist"]))
        D = np.repeat(np.eye(3)[None], nb, axis=0)
        Hp = np.zeros((nb, 3))
        pelvis = np.asarray(spec["pelvis"], dtype=float)
        info = {"ik_err": 0.0}

        sp = spec.get("spine", (0, 0, 0))
        nk = spec.get("neck", (0, 0, 0))
        sec = getattr(self, "sec_offsets", None)       # v4 secondary motion (templates._secondary)
        if sec is not None:
            sp = tuple(float(a) + b for a, b in zip(sp, sec[0]))
            nk = tuple(float(a) + b for a, b in zip(nk, sec[1]))
        spine_frac = {"spine05": 0.16, "spine04": 0.2, "spine03": 0.22, "spine02": 0.22, "spine01": 0.2}
        twist_frac = {"spine05": 0.1, "spine04": 0.15, "spine03": 0.2, "spine02": 0.25, "spine01": 0.3}
        neck_frac = {"neck01": 0.3, "neck02": 0.3, "neck03": 0.2, "head": 0.2}
        local = {}
        for b, f in spine_frac.items():
            local[b] = body_rot(sp[0] * f, sp[1] * f, sp[2] * twist_frac[b])
        for b, f in neck_frac.items():
            local[b] = body_rot(nk[0] * f, nk[1] * f, nk[2] * f)

        def fk(upto=None):
            for i in range(nb):
                p = self.P[i]
                name = self.names[i]
                if p < 0:
                    D[i] = R0
                    Hp[i] = pelvis + R0 @ (self.H[i] - self.pc_rest)
                    continue
                Hp[i] = Hp[p] + D[p] @ (self.H[i] - self.H[p])
                if i in Dloc:
                    D[i] = Dloc[i]
                elif name in local:
                    D[i] = D[p] @ local[name]
                else:
                    D[i] = D[p]

        fk()
        arms = spec.get("arm", {})
        legs = spec.get("leg", {})
        clav = spec.get("clav", {})
        torso_R = D[self.bi("spine01")].copy()
        pelvis_R = R0

        # ---------------- legs
        for sd, L in legs.items():
            self._solve_leg(sd, L, D, Hp, Dloc, pelvis_R, info)
        # ---------------- arms (two passes: girdle depends on arm direction)
        for sd, A in arms.items():
            s = SIDES[sd]
            ce, cp = clav.get(sd, (0.0, 0.0))
            auto_e, auto_p = 0.0, 0.0
            for it in range(2):
                ic = self.bi(f"clavicle.{sd}")
                Rc = body_rot(0, 0, 0)
                # elevation: rotate about the torso forward axis; protraction about up
                e, pr = ce + auto_e, cp + auto_p
                Rc = rot(torso_R @ Y, -s * e) @ rot(torso_R @ Z, s * pr)
                Dloc[ic] = Rc @ torso_R
                Dloc[self.bi(f"shoulder01.{sd}")] = Dloc[ic]
                fk()
                ua_dir = self._solve_arm(sd, A, D, Hp, Dloc, torso_R, info)
                fk()
                loc = torso_R.T @ ua_dir
                elev = math.degrees(math.asin(max(-1, min(1, loc[2]))))
                auto_e = float(np.clip(0.3 * (elev + 15), 0, 22))
                auto_p = float(np.clip(12 * loc[1], -6, 10))
        fk()
        # fingers / toes
        for sd, A in arms.items():
            cu = A.get("curl", 0.0)
            if "palm" in A and cu < 0.15:
                cu = -0.14  # flat hand on a surface: fingers straight, not curled into it
            self._curl(sd, cu, D, Dloc, A.get("thumb_curl", -0.7 if "palm" in A else None))
        for sd, L in legs.items():
            pass
        fk()
        self._last = (D.copy(), Hp.copy())
        info["com"] = self.com(D, Hp)
        return D.copy(), Hp.copy(), info

    # ------------------------------------------------------------- limbs
    def _ik(self, S, T, L1, L2, pole):
        d_vec = T - S
        d = np.linalg.norm(d_vec)
        dmax, dmin = (L1 + L2) * 0.9995, abs(L1 - L2) + 1e-3
        err = max(0.0, d - dmax)
        dc = min(max(d, dmin), dmax)
        u = unit(d_vec)
        a = (L1 * L1 - L2 * L2 + dc * dc) / (2 * dc)
        h = math.sqrt(max(0.0, L1 * L1 - a * a))
        q = orth(pole, u)
        if np.linalg.norm(q) < 1e-6:
            q = orth(Z if abs(u[2]) < 0.9 else Y, u)
        E = S + a * u + h * q
        Tc = S + dc * u
        return E, Tc, err

    def _solve_arm(self, sd, A, D, Hp, Dloc, torso_R, info):
        s = SIDES[sd]
        dm = self.dims[sd]
        S = Hp[self.bi(f"upperarm01.{sd}")]
        hr = self.hand_rest[sd]
        Sr, Er, Wr = self.joint(f"upperarm01.{sd}"), self.joint(f"lowerarm01.{sd}"), self.joint(f"wrist.{sd}")
        if "ua" in A:  # forward kinematic spec
            ua = unit(A["ua"])
            bend = orth(A.get("bend", torso_R @ Y), ua)
            if np.linalg.norm(bend) < 1e-6:
                bend = orth(torso_R @ Y, ua)
            E = S + dm["L1"] * ua
            fa = rot(np.cross(ua, bend), A.get("elbow", 10)) @ ua
            Wt = E + dm["L2"] * fa
            pole = -bend
            fing = A.get("fing", fa)
            thumb = self._thumb(A.get("thumb", "neutral"), sd, fa, ua, bend, torso_R)
            Fh = self.hand_axes(fing, thumb, sd)
        else:
            pole = A.get("pole", torso_R @ (-Y))
            target0 = A.get("grip", A.get("palm", A.get("wrist")))
            thumb = self._thumb(A.get("thumb", torso_R @ Y), sd, unit(target0 - S), None, None, torso_R)
            fing = A.get("fing")
            target = A.get("grip", A.get("palm", A.get("wrist")))
            key = "grip" if "grip" in A else ("palm" if "palm" in A else "wrist")
            fa_guess = unit(target - S)
            for _ in range(3):
                Fh = self.hand_axes(fing if fing is not None else fa_guess, thumb, sd)
                Rh = Fh @ hr["F"].T
                Wt = target - (Rh @ hr[key] if key != "wrist" else 0)
                E, Wc, err = self._ik(S, Wt, dm["L1"], dm["L2"], pole)
                fa_guess = unit(Wc - E)
        E, Wc, err = self._ik(S, Wt, dm["L1"], dm["L2"], pole)
        info["ik_err"] = max(info["ik_err"], err)
        info.setdefault("arm_err", {})[sd] = err
        Rh = Fh @ hr["F"].T
        # upper arm
        a0, b0 = unit(Er - Sr), orth(Wr - Er, unit(Er - Sr))
        a1 = unit(E - S)
        b1 = orth(Wc - E, a1)
        if np.linalg.norm(b1) < 1e-6:
            b1 = orth(-pole, a1)
        Rua = frame(a1, b1) @ frame(a0, b0).T
        for b in ("upperarm01", "upperarm02"):
            Dloc[self.bi(f"{b}.{sd}")] = Rua
        # shoulder01 bone: half-way between clavicle and arm for smoother deltoid
        ic = self.bi(f"clavicle.{sd}")
        Dloc[self.bi(f"shoulder01.{sd}")] = Dloc.get(ic, torso_R)
        # forearm: hinge then distribute twist toward the hand
        n0 = np.cross(a0, b0)
        n1 = np.cross(a1, b1)
        f0 = unit(Wr - Er)
        f1 = unit(Wc - E)
        Rh_hinge = frame(f1, np.cross(n1, f1)) @ frame(f0, np.cross(n0, f0)).T
        t_rest = orth(hr["F"][:, 1], f0)
        t_hinge = orth(Rh_hinge @ t_rest, f1)
        t_goal = orth(Fh[:, 1], f1)
        ang = math.degrees(math.atan2(np.dot(np.cross(t_hinge, t_goal), f1), np.dot(t_hinge, t_goal)))
        # forearm twist near +-180 degrees: keep the branch closest to the
        # previous solve so the forearm does not spin round between frames
        last = getattr(self, "_twist", {}).get(sd)
        if last is not None:
            for alt in (ang + 360.0, ang - 360.0):
                if abs(alt) <= 260 and abs(alt - last) < abs(ang - last):
                    ang = alt
        self.__dict__.setdefault("_twist", {})[sd] = ang
        Dloc[self.bi(f"lowerarm01.{sd}")] = rot(f1, ang * 0.3) @ Rh_hinge
        Dloc[self.bi(f"lowerarm02.{sd}")] = rot(f1, ang * 0.8) @ Rh_hinge
        Dloc[self.bi(f"wrist.{sd}")] = Rh
        return a1

    @staticmethod
    def _thumb(spec, sd, fa, ua, bend, torso_R):
        """Thumb direction from a vector or a name: neutral (hammer), sup
        (palm forward/up, thumb lateral), pro (thumb medial), or a body
        direction word fwd/back/up/down/in/out."""
        s = SIDES[sd]
        if not isinstance(spec, str):
            return np.asarray(spec, dtype=float)
        lat = torso_R @ (s * X)
        words = {"fwd": torso_R @ Y, "back": torso_R @ -Y, "up": torso_R @ Z, "down": torso_R @ -Z,
                 "out": lat, "in": -lat, "sup": lat, "pro": -lat}
        if spec == "neutral":
            if ua is not None and bend is not None:
                n = np.cross(ua, bend)
                v = np.cross(n, fa)
                if np.linalg.norm(v) > 1e-6:
                    return unit(v)
            return torso_R @ Y
        return words[spec]

    def _curl(self, sd, c, D, Dloc, thumb_c=None):
        s = SIDES[sd]
        Rh = Dloc.get(self.bi(f"wrist.{sd}"))
        if Rh is None:
            return
        F = Rh @ self.hand_rest[sd]["F"]
        y, t, n = F[:, 0], F[:, 1], F[:, 2]
        k = np.cross(y, n)
        angs = (62 * c, 88 * c, 58 * c)
        for f in (2, 3, 4, 5):
            acc = 0
            for j in (1, 2, 3):
                acc += angs[j - 1]
                Dloc[self.bi(f"finger{f}-{j}.{sd}")] = rot(k, acc) @ Rh
        tc = c if thumb_c is None else thumb_c
        acc = 0
        for j, a in zip((1, 2, 3), (25 * tc, 30 * tc, 35 * tc)):
            acc += a
            Dloc[self.bi(f"finger1-{j}.{sd}")] = rot(y, -s * acc * 0.6) @ rot(k, acc * 0.5) @ Rh

    def _solve_leg(self, sd, L, D, Hp, Dloc, pelvis_R, info):
        dm = self.dims[sd]
        fr = self.foot_rest[sd]
        Hj = Hp[self.bi(f"upperleg01.{sd}")]
        Hr, Kr, Ar = self.joint(f"upperleg01.{sd}"), self.joint(f"lowerleg01.{sd}"), self.joint(f"foot.{sd}")
        toe_local = None
        if "ball" in L:
            yaw = L.get("yaw", 0.0) * SIDES[sd]  # positive = toes out
            Rf = rot(Z, -yaw) @ rot(X, -L.get("heel", 0.0))
            Rf = rot(Z, L.get("turn", 0.0)) @ Rf
            ball = np.asarray(L["ball"], dtype=float).copy()
            # on the toes the skinned toe crease dips below the ball joint:
            # lift the ball so the shoe tip rests on the surface, not in it
            ball[2] += 0.0 * math.sin(math.radians(max(0.0, L.get("heel", 0.0)))) ** 2
            toe_local = rot(X, L.get("heel", 0.0))
            # the ball contact rides on the (flat) toes: toe joint above it,
            # ankle placed from the toe joint through the tilted foot
            Th = self.joint(f"toe3-1.{sd}")
            At = ball - (Rf @ toe_local) @ (fr["ball"] - Th) - Rf @ (Th - Ar)
            pole = L.get("pole", rot(Z, -yaw) @ Y + np.array([0, 0, 0.0]))
        elif "ankle" in L:
            fdir, fup = unit(L["fdir"]), L.get("fup", Z)
            Rf = frame(fdir, np.cross(orth(fup, fdir), fdir)) @ frame(fr["F"][:, 0], fr["F"][:, 1]).T
            At = np.asarray(L["ankle"], dtype=float)
            pole = L.get("pole", pelvis_R @ Y)
        else:  # FK: thigh direction + knee angle
            th = unit(L["thigh"])
            kb_in = np.asarray(L.get("kbend", pelvis_R @ -Y), float)
            raw = kb_in - th * np.dot(kb_in, th)
            # anatomical bend direction (shin folds behind the thigh); blended in
            # when the requested direction runs along the thigh (no flip there)
            anat = unit(np.cross(th, pelvis_R @ X))
            rn = unit(raw) if np.linalg.norm(raw) > 1e-6 else anat
            # degenerate (requested bend along the thigh) or bending the knee the wrong
            # way (shin up in front): fall back to the anatomical direction, continuously
            w = min(1.0, np.linalg.norm(raw) / max(np.linalg.norm(kb_in), 1e-9) / 0.4)
            w *= min(1.0, max(0.0, (float(np.dot(rn, anat)) + 0.4) / 0.4))
            kb = unit(rn * w + anat * (1 - w)) if w < 1 else rn
            K = Hj + dm["T1"] * th
            sh = rot(np.cross(th, kb), L.get("knee", 0)) @ th
            At = K + dm["T2"] * sh
            pole = -kb
            fdir = L.get("fdir")
            if fdir is None:
                # toes keep pointing forward-ish; fall back to the knee direction only
                # where forward runs along the shin
                fwd = pelvis_R @ Y
                cand = fwd - sh * np.dot(fwd, sh)
                fdir = unit(cand) if np.linalg.norm(cand) > 0.35 else orth(-kb if L.get("knee", 0) > 1 else fwd, sh)
            fdir = unit(fdir)
            fup = L.get("fup", -sh)
            Rf = frame(fdir, np.cross(orth(fup, fdir), fdir)) @ frame(fr["F"][:, 0], fr["F"][:, 1]).T
        K, Ac, err = self._ik(Hj, At, dm["T1"], dm["T2"], pole)
        info["ik_err"] = max(info["ik_err"], err)
        info.setdefault("leg_err", {})[sd] = err
        a0, b0 = unit(Kr - Hr), orth(-Y, unit(Kr - Hr))
        a1 = unit(K - Hj)
        b1 = orth(Ac - K, a1)
        if np.linalg.norm(b1) < 1e-6:
            b1 = orth(-np.asarray(pole), a1)
        Rth = frame(a1, b1) @ frame(a0, b0).T
        Dloc[self.bi(f"upperleg01.{sd}")] = Rth
        Dloc[self.bi(f"upperleg02.{sd}")] = Rth
        n0, n1 = np.cross(a0, b0), np.cross(a1, b1)
        s0, s1 = unit(Ar - Kr), unit(Ac - K)
        Rsh = frame(s1, np.cross(n1, s1)) @ frame(s0, np.cross(n0, s0)).T
        fx_rest = orth(fr["F"][:, 0], s0)
        fx_h = orth(Rsh @ fx_rest, s1)
        fx_goal = orth(Rf @ fr["F"][:, 0], s1)
        ang = 0.0
        if np.linalg.norm(fx_h) > 1e-6 and np.linalg.norm(fx_goal) > 1e-6:
            ang = math.degrees(math.atan2(np.dot(np.cross(fx_h, fx_goal), s1), np.dot(fx_h, fx_goal)))
        Dloc[self.bi(f"lowerleg01.{sd}")] = rot(s1, ang * 0.35) @ Rsh
        Dloc[self.bi(f"lowerleg02.{sd}")] = rot(s1, ang * 0.75) @ Rsh
        Dloc[self.bi(f"foot.{sd}")] = Rf
        tl = toe_local if toe_local is not None else rot(X, L.get("toe", 0.0))
        for i, nm in enumerate(self.names):
            if nm.startswith("toe") and nm.endswith("." + sd) and self.names[self.P[i]] == f"foot.{sd}":
                Dloc[i] = Rf @ tl
        for i, nm in enumerate(self.names):
            if nm.startswith("toe") and nm.endswith("." + sd) and self.names[self.P[i]] != f"foot.{sd}":
                Dloc[i] = Rf @ tl

    # ------------------------------------------------------------ outputs
    def com(self, D, Hp):
        segs = {
            "head": ["head"], "trunk": ["spine05", "spine03", "spine01"],
        }
        tot, acc = 0.0, np.zeros(3)
        mid = lambda b: Hp[self.bi(b)] + D[self.bi(b)] @ (self.T[self.bi(b)] - self.H[self.bi(b)]) * 0.5
        acc += SEG_MASS["head"] * mid("head"); tot += SEG_MASS["head"]
        for b in ("spine05", "spine04", "spine03", "spine02", "spine01"):
            acc += SEG_MASS["trunk"] / 5 * mid(b); tot += SEG_MASS["trunk"] / 5
        for sd in "LR":
            for b, m in (("upperarm02", "ua"), ("lowerarm01", "fa"), ("wrist", "hand"),
                         ("upperleg02", "thigh"), ("lowerleg01", "shin"), ("foot", "foot")):
                acc += SEG_MASS[m] * mid(f"{b}.{sd}"); tot += SEG_MASS[m]
        return acc / tot

    def skin(self, D, Hp):
        nb = self.nb
        M = np.zeros((nb, 3, 4))
        M[:, :, :3] = D
        M[:, :, 3] = Hp - np.einsum("bij,bj->bi", D, self.H)
        Mv = (self.W @ M.reshape(nb, 12).astype(np.float32)).reshape(-1, 3, 4)
        v = self.verts.astype(np.float32)
        return np.einsum("vij,vj->vi", Mv[:, :, :3], v) + Mv[:, :, 3]

    def joints_posed(self, D, Hp):
        return {n: Hp[i] for i, n in enumerate(self.names)}

    def bone_point(self, D, Hp, bone, rest_point):
        i = self.bi(bone)
        return Hp[i] + D[i] @ (np.asarray(rest_point) - self.H[i])
