"""Pose families and the constraint pipeline.

A template (templates.py) calls a family builder on Ctx with values already
interpolated for the current phase.  A builder returns a Frame: a closure that
produces a rig spec + equipment for a given pelvis adjustment, plus the
constraints the pipeline must satisfy (balance over the feet, limb reach,
support contact with floor / pads, bar height, ...).  The pipeline iterates
until the constraints hold, then skins the mesh.
"""
import math

import numpy as np

from .rig import Rig, X, Y, Z, SIDES, unit, orth, rot, body_rot, frame
from .equipment import Mx, rx, ry, rz, PLATE_R

SOLE = 0.008      # shoe sole thickness: foot targets sit this far above the floor
PAD_SINK = -0.004 # bodies sink this much into padded supports
SKIN_FLOOR = -0.002


def E(kind, pos=(0, 0, 0), R=None, eid=None, dyn=False, **shape):
    return dict(kind=kind, M=Mx(pos, R), id=eid or kind, shape=shape, dyn=dyn)


def seg(eid, p0, p1, r, mat="rope"):
    """Straight dynamic segment; an end may be 'gripL'/'gripR'/'gripC' (resolved
    after solving) optionally as a (name, offset) tuple."""
    d = dict(kind="_seg", id=eid, r=r, mat=mat)
    for k, v in (("p0", p0), ("p1", p1)):
        if callable(v):                       # f(points, D, Hp, ctx) -> xyz, resolved after solving
            d[k + "f"] = v
            d[k] = np.zeros(3)
        elif isinstance(v, tuple) and v and v[0] == "toward":
            d[k + "t"] = (v[1], float(v[2]))
            d[k] = np.zeros(3)
        elif isinstance(v, tuple) and isinstance(v[0], str):
            d[k + "s"], d[k + "o"] = v[0], np.asarray(v[1], float)
            d[k] = np.zeros(3)
        elif isinstance(v, str):
            d[k + "s"] = v
            d[k] = np.zeros(3)
        else:
            d[k] = np.asarray(v, float)
    return d


def H(kind, sd, R="db", eid=None, off=(0, 0, 0), **shape):
    """Implement held in a hand (sd = 'L', 'R' or 'C' for both)."""
    return dict(kind=kind, M=np.eye(4), id=eid or f"{kind}{sd}", shape=shape, hand=sd, hand_R=R, off=off)


class Frame:
    def __init__(self, build, cons=(), settle=(), planted=()):
        self.build = build
        self.cons = list(cons)
        self.settle = list(settle)
        self.planted = list(planted)


class Pose:
    def __init__(self, D, Hp, verts, equip, info):
        self.D, self.Hp, self.verts, self.equip, self.info = D, Hp, verts, equip, info


class Ctx:
    def __init__(self, gender):
        self.g = gender
        r = self.r = Rig(gender)
        J = r.joint
        self.S = r.height / 1.79
        self.pz = r.pc_rest[2]
        self.hw = r.hip_w
        self.sw = r.shoulder_w
        fr = r.foot_rest["R"]
        self.ball_y = fr["ball"][1]
        self.heel_y = fr["heel"][1]
        self.foot_len = self.ball_y - self.heel_y + fr["toe_len"]
        self.mid_off = 0.5 * (self.heel_y + self.ball_y) - self.ball_y  # midfoot rel. ball
        self.ankle_h = fr["ankle"][2]
        d = r.dims["R"]
        self.arm = d["L1"] + d["L2"]
        self.leg = d["T1"] + d["T2"]
        # straight-arm shoulder->grip length
        hr = r.hand_rest["R"]
        F = r.hand_axes(-Z, Y, "R")
        Rh = F @ hr["F"].T
        self.Lh = np.linalg.norm(np.array([0, 0, -self.arm]) + Rh @ hr["grip"])
        self.Lpf = self.arm + 0.024   # straight arm, hand flat on a surface (wrist extended)
        self.Lp = np.linalg.norm(np.array([0, 0, -self.arm]) + r.hand_axes(-Z, -X, "R") @ hr["F"].T @ hr["palm"])
        v = r.verts
        self.v = v

        def surf_y(z, xlo, xhi, front=True, dz=0.012):
            m = (np.abs(v[:, 2] - z) < dz) & (np.abs(v[:, 0]) >= xlo) & (np.abs(v[:, 0]) <= xhi)
            return v[m, 1].max() if front else v[m, 1].min()

        self.z_neck = J("neck01")[2]
        self.z_clav = J("clavicle.R")[2]
        self.z_sh = J("upperarm01.R")[2]
        self.z_nip = r.T[r.bi("breast.R")][2]
        self.z_hip = J("upperleg01.R")[2]
        self.z_head = J("head")[2]
        zb = self.z_neck - 0.055 * self.S
        self.lm = {
            "back_bar": ("spine01", np.array([0, surf_y(zb, 0, 0.05, False) - 0.02, zb])),
            "front_rack": ("spine01", np.array([0, surf_y(self.z_clav - 0.03, 0.06, 0.14) + 0.03, self.z_clav - 0.025])),
            "chest": ("spine02", np.array([0, surf_y(self.z_nip - 0.01, 0, 0.05) + 0.017, self.z_nip - 0.01])),
            "chest_hi": ("spine01", np.array([0, surf_y(self.z_clav - 0.07, 0, 0.05) + 0.017, self.z_clav - 0.07])),
            "hip_front": ("root", np.array([0, surf_y(self.z_hip - 0.04, 0, 0.12) + 0.035, self.z_hip - 0.04])),
            "goblet": ("spine02", np.array([0, surf_y(self.z_nip + 0.03, 0, 0.05) + 0.09, self.z_nip + 0.0])),
            "head_top": ("head", np.array([0, J("head")[1], r.height])),
            "nape": ("head", np.array([0, surf_y(self.z_head + 0.05, 0, 0.03, False) - 0.02, self.z_head + 0.05])),
            "forehead": ("head", np.array([0, surf_y(self.z_head + 0.09 * self.S, 0, 0.03) + 0.02, self.z_head + 0.09 * self.S])),
            "thigh_front": ("upperleg02.R", np.array([0, 0, 0])),
        }
        self.adj = np.zeros(3)

    # ------------------------------------------------------------ helpers
    def P(self, x=0.0, y=0.0, z=None):
        return np.array([x, y, self.pz if z is None else z]) + self.adj

    def lmk(self, D, Hp, name):
        bone, p = self.lm[name]
        return self.r.bone_point(D, Hp, bone, p)

    def bp(self, D, Hp, bone, rest_point):
        return self.r.bone_point(D, Hp, bone, rest_point)

    def J(self, D, Hp, name):
        return Hp[self.r.bi(name)].copy()

    def torso(self, spec):
        s = {k: v for k, v in spec.items() if k != "arm"}
        D, Hp, _ = self.r.solve(s)
        return D, Hp

    def ankle_rise(self, heel):
        fr = self.r.foot_rest["R"]
        v = fr["ankle"] - fr["ball"]
        return (rot(X, -heel) @ v)[2] - v[2]

    def foot(self, x, y, yaw=0.0, heel=0.0, z=0.0, pole=None, turn=0.0):
        # on the toes the skinned toe crease dips below the ball joint: lift
        # the ball target so the shoe tip rests on the surface instead of in it
        L = dict(ball=np.array([x, y + self.ball_y, z + SOLE]), yaw=yaw, heel=heel, turn=turn, surf=z)
        if pole is not None:
            L["pole"] = pole
        return L

    def feet(self, w=None, toe=10.0, y=0.0, split=0.0, heel=(0, 0), z=(0, 0), dx=0.0):
        """Both feet: w = distance between ball centres, split = front/back
        distance (right foot forward if > 0)."""
        w = self.hw * 1.05 if w is None else w
        return {"L": self.foot(-w / 2 + dx, y - split / 2, toe, heel[0], z[0]),
                "R": self.foot(w / 2 + dx, y + split / 2, toe, heel[1], z[1])}

    def midfoot(self, legs, weights=None):
        pts = []
        for sd, L in legs.items():
            if "ball" in L:
                yaw = math.radians(L.get("yaw", 0) * SIDES[sd] + L.get("turn", 0) * 0)
                d = np.array([-math.sin(-yaw), math.cos(-yaw), 0])
                pts.append(L["ball"] + d * self.mid_off * (1 - L.get("heel", 0) / 90))
        if not pts:
            return None
        w = np.ones(len(pts)) if weights is None else np.asarray(weights, float)
        return (np.array(pts) * w[:, None]).sum(0) / w.sum()

    def arm_dir(self, D, v, sd, bone="spine01"):
        """Body-frame direction for the RIGHT arm (x out, y fwd, z up),
        mirrored for the left, mapped by the given torso bone."""
        v = np.array(v, float)
        if sd == "L":
            v[0] = -v[0]
        return unit(D[self.r.bi(bone)] @ v)

    # ------------------------------------------------------------ pipeline
    def run(self, fr, iters=7, warm=None):
        r = self.r
        self.adj = np.zeros(3) if warm is None else np.asarray(warm, float).copy()
        if warm is not None:
            iters = max(iters, 10)
        D = Hp = None
        for outer in range(10 if fr.settle else 1):
            for it in range(iters):
                spec, equip, extra = fr.build()
                D, Hp, info = r.solve(spec)
                delta = np.zeros(3)
                for c in fr.cons:
                    delta += self._cons(c, spec, D, Hp, info, extra)
                if np.linalg.norm(delta) < 5e-4:
                    break
                self.adj = self.adj + delta
            if not fr.settle:
                break
            verts = r.skin(D, Hp)
            # all supports at once: smallest pelvis move that makes every
            # contact gap exact (least squares over the support normals)
            rows_n, rows_g = [], []
            for s_ in fr.settle:
                ng = self._settle_ng(s_, verts, extra)
                if ng is not None:
                    rows_n.append(ng[0])
                    rows_g.append(ng[1])
            if not rows_n:
                break
            A = np.array(rows_n)
            b = np.array(rows_g)
            delta = A.T @ np.linalg.solve(A @ A.T + 1e-6 * np.eye(len(b)), b)
            if np.abs(b).max() < 6e-4:
                break
            self.adj = self.adj + delta
        spec, equip, extra = fr.build()
        D, Hp, info = r.solve(spec)
        verts = r.skin(D, Hp)
        # a free (FK) leg must not dig its foot into the floor: bend the knee
        # by the smallest angle that clears it (bisection, so the correction
        # changes continuously from frame to frame instead of in steps)
        free = getattr(fr, "free_legs", None)
        for sd, Lg in list(spec.get("leg", {}).items()):
            if "thigh" not in Lg or getattr(fr, "free_feet_ok", False):
                continue
            if free is not None:
                if sd not in free:
                    continue
            elif not any(sd2 in fr.planted for sd2 in spec["leg"]) and fr.settle:
                continue
            m = self._foot_mask(sd)
            if verts[m, 2].min() >= 0.004 or verts[:, 2].min() < -0.5:
                continue
            k0 = Lg.get("knee", 0)
            lo, hi = 0.0, 70.0
            for _ in range(12):
                mid = 0.5 * (lo + hi)
                Lg["knee"] = k0 + mid
                D, Hp, info = r.solve(spec)
                verts = r.skin(D, Hp)
                if verts[m, 2].min() < 0.004:
                    lo = mid
                else:
                    hi = mid
            Lg["knee"] = k0 + hi
            D, Hp, info = r.solve(spec)
            verts = r.skin(D, Hp)
        equip = self._attach(equip, D, Hp)
        info["spec"] = spec
        info["extra"] = extra
        info["planted"] = fr.planted
        info["settle"] = list(fr.settle)
        info["adj"] = self.adj.copy()
        info["contacts"] = list(getattr(fr, "contacts", []))
        return Pose(D, Hp, verts, equip, info)

    def _region(self, name):
        if not hasattr(self, "_rg"):
            self._rg = {}
        if name not in self._rg:
            r = self.r
            pre = {"noarms": ("upperarm", "lowerarm", "wrist", "finger", "metacarpal"),
                   "seat": ("upperarm", "lowerarm", "wrist", "finger", "metacarpal", "lowerleg", "foot", "toe",
                            "spine02", "spine01", "neck", "head", "clavicle", "shoulder", "breast")}[name] \
                if name in ("noarms", "seat") else None
            if name == "pelvis":     # buttocks only (saddles: the thighs move past the seat)
                cols = [i for i, n in enumerate(r.names) if n.startswith(("root", "pelvis"))]
                self._rg[name] = r.W[:, cols].sum(1) > 0.5
            elif name == "hips":
                cols = [i for i, n in enumerate(r.names) if n.startswith(("root", "pelvis", "upperleg", "spine05"))]
                self._rg[name] = r.W[:, cols].sum(1) > 0.5
            else:
                cols = [i for i, n in enumerate(r.names) if n.startswith(pre)]
                self._rg[name] = r.W[:, cols].sum(1) < 0.5
        return self._rg[name]

    def _foot_mask(self, sd):
        if not hasattr(self, "_fm"):
            self._fm = {}
        if sd not in self._fm:
            r = self.r
            cols = [i for i, n in enumerate(r.names) if n.endswith("." + sd) and n.startswith(("foot", "toe", "lowerleg02"))]
            self._fm[sd] = r.W[:, cols].sum(1) > 0.5
        return self._fm[sd]

    def grip_frame(self, D, Hp, sd):
        """Posed grip point and hand axes (fingers, thumb, palm normal)."""
        r = self.r
        hr = r.hand_rest[sd]
        i = r.bi(f"wrist.{sd}")
        return Hp[i] + D[i] @ hr["grip"], D[i] @ hr["F"]

    def _attach(self, equip, D, Hp):
        out = []
        grips = {sd: self.grip_frame(D, Hp, sd) for sd in "LR"}
        pts = {f"grip{sd}": g[0] for sd, g in grips.items()}
        pts["gripC"] = 0.5 * (pts["gripL"] + pts["gripR"])
        for e in equip:
            if e["kind"] == "_seg":
                e = dict(e)
                for k in ("p0", "p1"):
                    if isinstance(e.get(k + "s"), str):
                        e[k] = pts[e[k + "s"]] + e.get(k + "o", 0)
                for k in ("p0", "p1"):
                    if e.get(k + "f") is not None:
                        e[k] = np.asarray(e[k + "f"](pts, D, Hp, self), float)
                for k in ("p0", "p1"):   # ("toward", grip, dist): from the grip toward the other end
                    tw = e.get(k + "t")
                    if tw is not None:
                        g0 = pts[tw[0]]
                        other = e["p1" if k == "p0" else "p0"]
                        e[k] = g0 + unit(np.asarray(other) - g0) * tw[1]
                out.append(e)
                continue
            if e.get("bone"):          # attached to a body part (ankle cuff, ...)
                i = self.r.bi(e["bone"])
                Rb = D[i] @ np.asarray(e.get("bone_R", np.eye(3)))
                bp = e.get("bone_pt")
                if bp is None and e.get("_ankle"):
                    bp = self.r.joint(f"foot.{e['_ankle']}") + np.array([0, 0, 0.07])
                pos = Hp[i] + D[i] @ (np.asarray(bp) - self.r.H[i])
                out.append(dict(e, M=Mx(pos, Rb)))
                continue
            if e.get("pivot") is not None:  # landmine: bar from the floor pivot through the hands
                h = e.get("hand") or "C"
                g = pts["gripC"] if h == "C" else grips[h][0]
                piv = np.asarray(e["pivot"])
                d = g - piv
                Ld = np.linalg.norm(d)
                R = frame3(d, Z)
                e = dict(e, M=Mx(piv, R), shape=dict(length=Ld + 0.33))
                out.append(e)
                out.append(dict(kind="landmine_base", M=Mx(piv * np.array([1, 1, 0])), id="lmbase", shape={}))
                continue
            h = e.get("hand")
            if h:
                g, F = (grips[h] if h in "LR" else (pts["gripC"], grips["R"][1]))
                y, t, n = F[:, 0], F[:, 1], F[:, 2]
                loc = e.get("hand_R", "db")
                if loc == "db":      # handle along thumb axis
                    R = np.stack([t, y, np.cross(t, y)], axis=1)
                elif loc == "kb":    # handle along thumb axis, bell beyond the fist
                    R = np.stack([t, np.cross(-y, t), -y], axis=1)
                elif loc == "kb_up":  # bottoms-up / racked: bell above the fist
                    R = np.stack([t, np.cross(y, t), y], axis=1)
                elif loc == "ball":
                    R = np.eye(3)
                elif loc == "bar":    # bar through both fists
                    xa = unit(pts["gripR"] - pts["gripL"])
                    za = orth(Z, xa)
                    if np.linalg.norm(za) < 1e-6:
                        za = orth(Y, xa)
                    R = np.stack([xa, np.cross(za, xa), za], axis=1)
                elif loc == "aim":    # handle across the hands (C) or along the thumb, +Y toward e["aim"]
                    xa = unit(pts["gripR"] - pts["gripL"]) if h == "C" else t
                    ya = orth(np.asarray(e["aim"]) - g, xa)
                    if np.linalg.norm(ya) < 1e-6:
                        ya = orth(Y, xa)
                    R = np.stack([xa, ya, np.cross(xa, ya)], axis=1)
                elif loc == "vert":   # one implement held upright by both hands
                    za = unit(grips["R"][1][:, 0] + grips["L"][1][:, 0]) * -1
                    xa = orth(X, za)
                    R = np.stack([xa, np.cross(za, xa), za], axis=1)
                else:
                    R = np.asarray(loc)
                e = dict(e)
                e["M"] = Mx(g + R @ np.asarray(e.get("off", (0, 0, 0))), R)
            out.append(e)
        return out

    def _cons(self, c, spec, D, Hp, info, extra):
        kind = c[0]
        if kind == "reach_legs":
            e = max(info.get("leg_err", {}).get(sd, 0) for sd in c[2]) if info.get("leg_err") else 0
            return np.asarray(c[1]) * e * 1.02 if e > 2e-4 else np.zeros(3)
        if kind == "reach_arms":
            e = max(info.get("arm_err", {}).get(sd, 0) for sd in c[2]) if info.get("arm_err") else 0
            return np.asarray(c[1]) * e * 1.02 if e > 2e-4 else np.zeros(3)
        if kind == "com":
            target, axes, loads = c[1], c[2], c[3]
            com = info["com"]
            tot, acc = 1.0, com.copy()
            for p, m in loads:
                p = extra.get(p) if isinstance(p, str) else p
                if p is None:
                    continue
                acc = acc + m * np.asarray(p)
                tot += m
            com = acc / tot
            d = np.zeros(3)
            for a in axes:
                d[a] = (target[a] - com[a]) * 0.9
            return d
        if kind == "call":   # a frame adjusts its own targets (returns a pelvis delta, usually zero)
            return np.asarray(c[1](spec, D, Hp, info, extra), float)
        if kind == "joint":  # move pelvis so a joint coordinate hits a value
            name, axis, val = c[1], c[2], c[3]
            p = Hp[self.r.bi(name)] if name in self.r.idx else extra[name]
            d = np.zeros(3)
            d[axis] = val - p[axis]
            return d * 0.95
        return np.zeros(3)

    def _settle_ng(self, s, verts, extra):
        """(normal, signed distance to move along it) for one support."""
        kind = s[0]
        if kind == "floor":
            gap = s[1] if len(s) > 1 else SKIN_FLOOR
            return Z.copy(), gap - verts[:, 2].min()
        if kind == "floor_part":
            return Z.copy(), s[2] - verts[s[1], 2].min()
        if kind == "plane":
            _, p0, n, u, hu, w, hw, gap = s[:8]
            vm = self._region(s[8] if len(s) > 8 else "noarms")
            n, u, w = unit(n), unit(u), unit(w)
            rel = verts - p0
            m = (np.abs(rel @ u) < hu) & (np.abs(rel @ w) < hw) & (rel @ n > -0.25) & vm
            if not m.any():
                return None
            return n, gap - (rel[m] @ n).min()
        return None

    def _settle(self, s, verts, extra):
        kind = s[0]
        if kind == "floor":
            gap = s[1] if len(s) > 1 else SKIN_FLOOR
            return np.array([0, 0, gap - verts[:, 2].min()])
        if kind == "floor_part":  # only the given vertex mask may touch
            return np.array([0, 0, s[2] - verts[s[1], 2].min()])
        if kind == "plane":
            _, p0, n, u, hu, w, hw, gap = s[:8]
            vm = self._region(s[8] if len(s) > 8 else "noarms")
            n, u, w = unit(n), unit(u), unit(w)
            rel = verts - p0
            m = (np.abs(rel @ u) < hu) & (np.abs(rel @ w) < hw) & (rel @ n > -0.25) & vm
            if not m.any():
                return np.zeros(3)
            dmin = (rel[m] @ n).min()
            return n * (gap - dmin)
        return np.zeros(3)

    # ================================================================ HOLDS
    def hold(self, name, D, Hp, k=None):
        """Return (arm specs, equipment list, extra points) for a named hold.
        k: dict of options (grip width 'gw', implement, ...)."""
        k = k or {}
        r = self.r
        Rt = D[r.bi("spine01")]
        lat = Rt @ X
        fwd = Rt @ Y
        up = Rt @ Z
        sh = {sd: self.J(D, Hp, f"upperarm01.{sd}") for sd in "LR"}
        arms, eq, ex = {}, [], {}
        gw = k.get("gw", self.sw * 1.35)
        curl = 0.85

        def bar_grips(center, axis, width, grip="pro", pole=None, fing=None):
            for sd in "LR":
                s = SIDES[sd]
                g = center + axis * s * width / 2
                th = -s * axis if grip == "pro" else s * axis
                a = dict(grip=g, thumb=th, curl=curl)
                if pole is not None:
                    a["pole"] = pole(sd) if callable(pole) else pole
                if fing is not None:
                    a["fing"] = fing
                arms[sd] = a

        if name in ("none", "sides"):
            for sd in "LR":
                arms[sd] = dict(ua=self.arm_dir(D, (0.12, 0.02, -1), sd), elbow=k.get("elbow", 12),
                                bend=fwd, thumb="fwd", curl=0.3)
        elif name == "hips":
            for sd in "LR":
                s = SIDES[sd]
                p = self.bp(D, Hp, "root", np.array([s * 0.15 * self.S, 0.0, self.z_hip + 0.1]))
                arms[sd] = dict(palm=p + lat * s * 0.02, thumb=-fwd, fing=-up * 0.3 + fwd, pole=lat * s - fwd * 0.3,
                                curl=0.2)
        elif name == "fwd":
            for sd in "LR":
                arms[sd] = dict(ua=self.arm_dir(D, (0.05, 1, 0.05), sd), elbow=5, bend=up, thumb="up", curl=0.1)
        elif name == "clasp":
            c = self.lmk(D, Hp, "goblet") + fwd * 0.02
            for sd in "LR":
                s = SIDES[sd]
                arms[sd] = dict(palm=c + lat * s * 0.02, thumb=up, fing=fwd + up * 0.5,
                                pole=-up + lat * s * 0.6, curl=0.4)
        elif name == "cross":
            for sd in "LR":
                s = SIDES[sd]
                p = self.lmk(D, Hp, "chest_hi") - lat * s * 0.1 + fwd * 0.03
                arms[sd] = dict(palm=p, thumb=up, fing=-lat * s, pole=-up + fwd * 0.2, curl=0.2)
        elif name == "head":
            for sd in "LR":
                s = SIDES[sd]
                p = self.bp(D, Hp, "head", np.array([s * 0.075 * self.S, self.r.joint("head")[1] - 0.02, self.z_head + 0.07]))
                arms[sd] = dict(palm=p, thumb=-up * 0.3 - fwd, fing=up * 0.6 - lat * s, pole=lat * s + up * 0.2,
                                curl=0.15)
        elif name in ("back_bar", "smith_bar"):
            c = self.lmk(D, Hp, "back_bar")
            bar_grips(c, lat, k.get("gw", self.sw * 1.7), "pro", pole=-up * 0.9 - fwd * 0.4)
            eq.append(E("barbell" if name == "back_bar" else "smith_bar", c, Rt @ rz(0) * 0 + _bar_R(lat),
                        eid="bar", dyn=True, plates=k.get("plates", 1)))
            ex["bar"] = c
        elif name == "front_bar":
            c = self.lmk(D, Hp, "front_rack")
            for sd in "LR":
                s = SIDES[sd]
                g = c + lat * s * self.sw * 0.6 - up * 0.01
                arms[sd] = dict(grip=g, thumb=-s * lat, fing=up * 0.6 - fwd, pole=fwd * 1.0 - up * 0.15 + lat * s * 0.3,
                                curl=0.45)
            eq.append(E("barbell", c, _bar_R(lat), eid="bar", dyn=True, plates=k.get("plates", 1)))
            ex["bar"] = c
        elif name in ("oh_bar", "oh_pvc", "oh_bar_n"):
            mid = 0.5 * (sh["L"] + sh["R"])
            w = k.get("gw", self.sw * (2.3 if name != "oh_bar_n" else 1.3))
            h = math.sqrt(max(self.Lh ** 2 - max(w / 2 - self.sw / 2, 0) ** 2, 0.01)) * 0.965
            c = mid + Z * h - fwd * 0.02 + Z * 0.0
            bar_grips(c, lat, w, "pro", pole=lambda sd: -fwd + lat * SIDES[sd] * 0.4 - Z * 0.3)
            eq.append(E("pvc" if name == "oh_pvc" else "barbell", c, _bar_R(lat), eid="bar", dyn=True,
                        plates=k.get("plates", 1)))
            ex["bar"] = c
        elif name in ("goblet", "kb_goblet"):
            c = self.lmk(D, Hp, "goblet")
            for sd in "LR":
                s = SIDES[sd]
                arms[sd] = dict(palm=c + lat * s * 0.055 + up * 0.04, thumb=up, fing=fwd * 0.6 - lat * s,
                                pole=-up + lat * s * 0.35, curl=0.35)
            if name == "goblet":
                eq.append(E("dumbbell", c, frame3(up, fwd), eid="db", dyn=True))
            else:
                eq.append(E("kettlebell", c + up * 0.05, frame3(lat, fwd), eid="kb", dyn=True))
            ex["load"] = c
        elif name in ("medball", "plate_chest"):
            c = self.lmk(D, Hp, "goblet") + fwd * 0.04
            for sd in "LR":
                s = SIDES[sd]
                arms[sd] = dict(palm=c + lat * s * 0.11, thumb=up, fing=fwd,     # palms on the sides of the ball
                                pole=-up + lat * s * 0.5, curl=0.25)
            eq.append(E("medball" if name == "medball" else "plate_held", c, frame3(lat, fwd), eid="mb", dyn=True))
            ex["load"] = c
        elif name in ("db_side", "kb_side", "trap", "suitcase"):
            for sd in "LR":
                s = SIDES[sd]
                if name == "suitcase" and sd == "L":
                    arms[sd] = dict(ua=self.arm_dir(D, (0.12, 0.0, -1), sd), elbow=10, bend=fwd, thumb="fwd", curl=0.3)
                    continue
                spread = k.get("spread", 0.16)
                p = sh[sd] + lat * s * spread * self.S - Z * self.Lh * 0.985 + fwd * k.get("fy", 0.0)
                p = sh[sd] + unit(p - sh[sd]) * self.Lh * 0.975
                th = fwd if name != "trap" else fwd
                arms[sd] = dict(grip=p, thumb=th, pole=-fwd * 0.6 + lat * s * 0.4, curl=0.85, fing=-Z)
                kind = {"db_side": "dumbbell", "kb_side": "kettlebell", "suitcase": "kettlebell", "trap": None}[name]
                if kind:
                    eq.append(H(kind, sd, "db" if kind == "dumbbell" else "kb"))
                ex[f"grip{sd}"] = p
            if name == "trap":
                c = 0.5 * (ex["gripL"] + ex["gripR"])
                eq.append(E("trapbar", c, _bar_R(lat), eid="trap", dyn=True))
                ex["bar"] = c
        elif name in ("bar_hang", "db_front", "bar_hang_sup", "bar_hang_wide", "pvc_hang"):
            w = {"bar_hang_wide": self.sw * 2.0}.get(name, k.get("gw", self.sw * 1.15))
            mid = 0.5 * (sh["L"] + sh["R"])
            arm_ang = math.radians(k.get("arm_ang", 0.0))  # + = bar in front of shoulders
            horiz = Y * 1.0
            hd = math.sqrt(max(self.Lh ** 2 - max(w / 2 - self.sw / 2, 0) ** 2, 0.01)) * 0.99
            c = mid - Z * hd * math.cos(arm_ang) + horiz * hd * math.sin(arm_ang)
            c = c + k.get("bar_off", np.zeros(3))
            gtype = "sup" if name == "bar_hang_sup" else "pro"
            bar_grips(c, X if k.get("world_axis", True) else lat, w, gtype,
                      pole=lambda sd: -fwd * 0.3 + lat * SIDES[sd] * 0.6 + Z * 0.2)
            if name == "db_front":
                arms.clear()
                for sd in "LR":
                    s = SIDES[sd]
                    g = c + X * s * self.sw * 0.42
                    arms[sd] = dict(grip=g, thumb=-s * X, curl=0.85, pole=lat * s - fwd * 0.2)
                    eq.append(H("dumbbell", sd))
            elif not k.get("noeq"):     # noeq: same hand path, nothing held (band handles)
                eq.append(E("pvc" if name == "pvc_hang" else ("ezbar" if k.get("ez") else "barbell"), c,
                            _bar_R(X), eid="bar", dyn=True, plates=k.get("plates", 1)))
            ex["bar"] = c
        elif name == "high_pull":   # bar pulled to the lower chest, elbows high and out
            c = self.lmk(D, Hp, "chest_hi") + fwd * 0.05 - up * 0.04
            bar_grips(c, lat, k.get("gw", self.sw * 1.3), "pro", pole=lambda sd: up * 0.9 + lat * SIDES[sd] * 0.6 - fwd * 0.2)
            eq.append(E("barbell", c, _bar_R(lat), eid="bar", dyn=True, plates=k.get("plates", 1)))
            ex["bar"] = c
        elif name == "zercher":
            c = self.lmk(D, Hp, "goblet") + fwd * 0.05 - up * 0.12
            for sd in "LR":
                s = SIDES[sd]
                arms[sd] = dict(ua=self.arm_dir(D, (0.25, 0.55, -0.8), sd), elbow=125, bend=up + fwd, thumb="up", curl=0.6)
            eq.append(E("barbell", c, _bar_R(lat), eid="bar", dyn=True))
            ex["bar"] = c
        elif name in ("db_shoulder", "kb_rack"):
            for sd in "LR":
                s = SIDES[sd]
                p = sh[sd] + fwd * 0.11 + up * 0.03 + lat * s * 0.03     # elbow not folded past ~155 deg
                arms[sd] = dict(grip=p, thumb=-lat * s * 0.2 + fwd * 1.0, fing=up, pole=-up + fwd * 0.6 + lat * s * 0.2,
                                curl=0.85)
                eq.append(H("dumbbell", sd) if name == "db_shoulder" else H("kettlebell", sd, "kb_up"))
        elif name in ("db_oh", "kb_oh", "db_oh1", "kb_oh1"):
            for sd in "LR":
                s = SIDES[sd]
                if name.endswith("1") and sd == "L":
                    arms[sd] = dict(ua=self.arm_dir(D, (0.9, 0.1, 0.1), sd), elbow=10, bend=fwd, thumb="fwd", curl=0.1)
                    continue
                p = sh[sd] + up * self.Lh * 0.97 + lat * s * 0.07
                arms[sd] = dict(grip=p, thumb=fwd, fing=up, pole=lat * s * 0.6 - fwd * 0.6, curl=0.85)
                kind = "dumbbell" if name.startswith("db") else "kettlebell"
                eq.append(H(kind, sd, "db" if kind == "dumbbell" else "kb_up"))
        elif name == "landmine":
            c = self.lmk(D, Hp, "goblet") + fwd * 0.03
            for sd in "LR":
                s = SIDES[sd]
                arms[sd] = dict(grip=c + lat * s * 0.02, thumb=up, fing=fwd, pole=-up + lat * s * 0.4, curl=0.85)
            ex["bar"] = c
            eq.append(_landmine(c, k.get("pivot")))
        elif name == "band_sh":
            for sd in "LR":
                s = SIDES[sd]
                p = sh[sd] + fwd * 0.08 + up * 0.02
                arms[sd] = dict(grip=p, thumb=-lat * s, fing=up, pole=-up + fwd * 0.5, curl=0.85)
                ex[f"grip{sd}"] = p
        return arms, eq, ex

    # ================================================================ FAMILIES
    def stand(self, legs, pz=None, py=0.0, px=0.0, pel=(0, 0, 0), spine=(0, 0, 0), neck=(0, 0, 0),
              hold="none", hold2=None, mix=0.0, hk=None, arms=None, clav=None, balance="com", load=0.0,
              bar_z=None, shoulder_y=None, equip=(), planted=("L", "R"), reach=True, settle=(), wsupport=None,
              free_legs=None, post=None):
        """Generic standing family.  legs: per-side foot specs (planted) or
        FK leg specs.  pz: pelvis height (default from hk*standing).
        hold/hold2/mix: arm holds blended in hand space.  balance: 'com' keeps
        the centre of mass (with load) over the feet, 'shoulder' puts the
        shoulders over mid-foot (bar path for pulls)."""
        hk = 0.995 if hk is None and pz is None else hk
        z = pz if pz is not None else self.pz * hk

        def build():
            spec = dict(pelvis=self.P(px, py, z), pel=pel, spine=spine, neck=neck,
                        leg={k: dict(v) for k, v in legs.items()})
            if clav:
                spec["clav"] = clav
            D, Hp = self.torso(spec)
            a, eq, ex = self._holds(hold, hold2, mix, D, Hp)
            if arms:
                for sd, A in arms.items():
                    a[sd] = A(D, Hp, self) if callable(A) else A
            spec["arm"] = a
            eqs = list(eq)
            for e in equip:
                eqs.append(e(D, Hp, self, ex) if callable(e) else e)
            if post:
                post(spec, D, Hp, ex, eqs)
            return spec, [e for e in eqs if e is not None], ex

        cons = []
        planted_sides = [sd for sd in legs if "ball" in legs[sd] and sd in planted]
        if reach and planted_sides:
            cons.append(("reach_legs", -Z, planted_sides))
        if bar_z is not None:
            cons.append(("joint", "bar", 2, bar_z))
        mf = self.midfoot({k: v for k, v in legs.items() if "ball" in v}, wsupport)
        if balance == "com" and mf is not None:
            loads = [("bar", load), ("load", load), ("gripL", load / 2), ("gripR", load / 2)] if load else []
            cons.append(("com", mf, [1], loads))
        elif balance == "bar" and mf is not None:
            cons.append(("joint", "bar", 1, mf[1] + (shoulder_y or 0.0)))
        elif balance == "shoulder" and mf is not None:
            cons.append(("joint", "upperarm01.R", 1, mf[1] + (shoulder_y or 0.0)))
        return Frame(build, cons, settle=list(settle), planted=planted_sides)

    def _holds(self, h1, h2, mix, D, Hp):
        def one(h):
            if isinstance(h, tuple):
                return self.hold(h[0], D, Hp, h[1])
            return self.hold(h, D, Hp)
        a1, e1, x1 = one(h1)
        if h2 is None or mix <= 1e-6:
            return a1, e1, x1
        a2, e2, x2 = one(h2)
        # (no shortcut at mix == 1: the blended form is used up to the end so the
        # hand does not jump between the two arm descriptions on the last frame)
        # blend in hand space: resolve FK arms to positions first
        out = {}
        for sd in set(a1) | set(a2):
            A, B = a1.get(sd), a2.get(sd)
            if A is None or B is None:
                out[sd] = A or B
                continue
            pa, pb = self._hand_point(A, D, Hp, sd), self._hand_point(B, D, Hp, sd)
            ta, tb = self._thumb_vec(A, D, sd), self._thumb_vec(B, D, sd)
            g = pa[0] * (1 - mix) + pb[0] * mix
            sh = self.J(D, Hp, f"upperarm01.{sd}")
            dg = g - sh
            g = sh + unit(dg) * min(np.linalg.norm(dg), self.Lh * 0.96)   # blended paths stay within reach
            o = dict(grip=g)
            o["thumb"] = unit(ta * (1 - mix) + tb * mix + 1e-6 * Y)
            o["pole"] = unit(np.asarray(A.get("pole", pa[1])) * (1 - mix) + np.asarray(B.get("pole", pb[1])) * mix)
            o["curl"] = A.get("curl", 0.5) * (1 - mix) + B.get("curl", 0.5) * mix
            if "fing" in A or "fing" in B:
                fa = np.asarray(A.get("fing", pa[2])); fb = np.asarray(B.get("fing", pb[2]))
                o["fing"] = unit(fa * (1 - mix) + fb * mix)
            out[sd] = o
        ex = {}
        for k in set(x1) | set(x2):
            if k in x1 and k in x2:
                ex[k] = x1[k] * (1 - mix) + x2[k] * mix
            else:
                ex[k] = x1.get(k, x2.get(k))
        # equipment: take from the hold that has it, moved with the hands
        eqs = []
        byid = {e["id"]: e for e in e1}
        for e in e2:
            byid.setdefault(e["id"], e)
        for eid, e in byid.items():
            ea = next((q for q in e1 if q["id"] == eid), None)
            eb = next((q for q in e2 if q["id"] == eid), None)
            if ea is not None and eb is not None:
                M = ea["M"].copy()
                M[:3, 3] = ea["M"][:3, 3] * (1 - mix) + eb["M"][:3, 3] * mix
                Ra, Rb = ea["M"][:3, :3], eb["M"][:3, :3]
                M[:3, :3] = _blend_R(Ra, Rb, mix)
                e = dict(ea, M=M)
            eqs.append(e)
        return out, eqs, ex

    def _hand_point(self, A, D, Hp, sd):
        """Grip point, pole and finger hint for an arm spec (resolving FK)."""
        if "grip" in A or "palm" in A:
            # no finger hint: fingers continue the reach direction (as the IK does on its own)
            g = np.asarray(A["grip"] if "grip" in A else A["palm"])
            reach = unit(g - self.J(D, Hp, f"upperarm01.{sd}"))
            return g, A.get("pole", -Y), A.get("fing", reach)
        sh = self.J(D, Hp, f"upperarm01.{sd}")
        d = self.r.dims[sd]
        ua = unit(A["ua"])
        bend = orth(A.get("bend", Y), ua)
        E_ = sh + d["L1"] * ua
        fa = rot(np.cross(ua, bend), A.get("elbow", 10)) @ ua
        return E_ + fa * (d["L2"] + 0.075), -bend, fa

    def _thumb_vec(self, A, D, sd):
        t = A.get("thumb", "fwd")
        if isinstance(t, str):
            Rt = D[self.r.bi("spine01")]
            s = SIDES[sd]
            words = {"fwd": Rt @ Y, "back": -(Rt @ Y), "up": Rt @ Z, "down": -(Rt @ Z), "out": Rt @ X * s,
                     "in": -(Rt @ X) * s, "sup": Rt @ X * s, "pro": -(Rt @ X) * s, "neutral": Rt @ Y}
            return words[t]
        return np.asarray(t, float)


def frame3(xaxis, yhint):
    x = unit(xaxis)
    y = orth(yhint, x)
    return np.stack([x, y, np.cross(x, y)], axis=1)


def _bar_R(axis):
    """Rotation whose local X is the given bar axis, local Z roughly up."""
    x = unit(axis)
    z = orth(Z, x)
    if np.linalg.norm(z) < 1e-6:
        z = orth(Y, x)
    return np.stack([x, np.cross(z, x), z], axis=1)


def _blend_R(Ra, Rb, t):
    from .rig import slerp_rot
    return slerp_rot(Rb @ Ra.T, t) @ Ra


def _landmine(c, pivot=None):
    pivot = np.array([0, 1.6, 0.06]) if pivot is None else np.asarray(pivot)
    d = c - pivot
    L = np.linalg.norm(d)
    x = d / L
    R = frame3(x, Z)
    # bar from the pivot through the hands; sleeve end beyond the hands
    return E("landmine_bar", pivot, R, eid="lm", dyn=True, length=L + 0.35)
