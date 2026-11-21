"""Gym equipment modelled from primitives.

Each kind is a function returning a Geo (local geometry grouped by
material).  Local frames: Z up, the user side is +Y unless noted; bars and
handles run along local X.  build() turns a Geo into Blender objects under
one empty; per frame the empty gets a world matrix.
"""
import math

import numpy as np

STEEL = ("steel", (0.62, 0.63, 0.65), 0.28, 1.0)
DARKSTEEL = ("darksteel", (0.16, 0.165, 0.175), 0.35, 0.6)
FRAME = ("frame", (0.055, 0.058, 0.064), 0.42, 0.35)
PAD = ("pad", (0.022, 0.023, 0.026), 0.5, 0.0)
RUBBER = ("rubber", (0.03, 0.031, 0.034), 0.72, 0.0)
WOOD = ("wood", (0.46, 0.31, 0.17), 0.62, 0.0)
BALL = ("ball", (0.42, 0.47, 0.53), 0.45, 0.0)
MEDBALL = ("medball", (0.07, 0.075, 0.085), 0.6, 0.0)
BAND = ("band", (0.09, 0.27, 0.62), 0.55, 0.0)
ROPE = ("rope", (0.19, 0.17, 0.14), 0.85, 0.0)
STRAP = ("strap", (0.035, 0.035, 0.04), 0.7, 0.0)
GREY = ("grey", (0.32, 0.33, 0.35), 0.5, 0.0)
MAT = ("mat", (0.11, 0.14, 0.18), 0.8, 0.0)
PVC = ("pvc", (0.62, 0.45, 0.28), 0.5, 0.0)      # wooden dowel tone: reads against the light floor
WALL = ("wall", (0.78, 0.785, 0.79), 0.9, 0.0)
SCREEN = ("screen", (0.02, 0.025, 0.03), 0.2, 0.0)

PLATE_R = 0.225


class Geo:
    def __init__(self):
        self.parts = {}

    def _add(self, mat, v, f):
        P = self.parts.setdefault(mat, [[], [], 0])
        P[0].append(v)
        P[1].extend([[i + P[2] for i in face] for face in f])
        P[2] += len(v)

    def box(self, mat, c, size, R=None):
        sx, sy, sz = np.asarray(size) / 2
        v = np.array([[x, y, z] for x in (-sx, sx) for y in (-sy, sy) for z in (-sz, sz)])
        if R is not None:
            v = v @ np.asarray(R).T
        v = v + np.asarray(c)
        f = [[0, 1, 3, 2], [4, 6, 7, 5], [0, 4, 5, 1], [2, 3, 7, 6], [0, 2, 6, 4], [1, 5, 7, 3]]
        self._add(mat, v, f)

    def cyl(self, mat, p0, p1, r, n=16, cap=True, r1=None):
        p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
        a = p1 - p0
        L = np.linalg.norm(a)
        if L < 1e-6:
            return
        a /= L
        u = np.cross(a, [0, 0, 1] if abs(a[2]) < 0.9 else [1, 0, 0])
        u /= np.linalg.norm(u)
        w = np.cross(a, u)
        r1 = r if r1 is None else r1
        ang = np.linspace(0, 2 * math.pi, n, endpoint=False)
        ring = np.outer(np.cos(ang), u) + np.outer(np.sin(ang), w)
        v = np.concatenate([p0 + r * ring, p1 + r1 * ring])
        f = [[i, (i + 1) % n, n + (i + 1) % n, n + i] for i in range(n)]
        if cap:
            f.append(list(range(n))[::-1])
            f.append(list(range(n, 2 * n)))
        self._add(mat, v, f)

    def tube(self, mat, pts, r, n=10):
        for a, b in zip(pts[:-1], pts[1:]):
            self.cyl(mat, a, b, r, n=n, cap=True)
        for p in pts[1:-1]:
            self.sphere(mat, p, r, seg=n, rings=5)

    def sphere(self, mat, c, r, seg=24, rings=12, scale=(1, 1, 1), zmin=-1.0):
        v, f = [], []
        lats = np.linspace(-math.pi / 2, math.pi / 2, rings + 1)
        lats = lats[np.sin(lats) >= zmin - 1e-9] if zmin > -1 else lats
        if zmin > -1:
            lats = np.concatenate([[math.asin(zmin)], lats[lats > math.asin(zmin)]])
        for la in lats:
            for k in range(seg):
                lo = 2 * math.pi * k / seg
                v.append([math.cos(la) * math.cos(lo), math.cos(la) * math.sin(lo), math.sin(la)])
        nr = len(lats)
        for i in range(nr - 1):
            for k in range(seg):
                a, b = i * seg + k, i * seg + (k + 1) % seg
                f.append([a, b, b + seg, a + seg])
        if zmin > -1:
            f.append(list(range(seg))[::-1])
        v = np.array(v) * r * np.asarray(scale) + np.asarray(c)
        self._add(mat, v, f)

    def torus(self, mat, c, R, r, axis=(0, 0, 1), seg=32, sides=10, arc=2 * math.pi, start=0.0):
        axis = np.asarray(axis, float) / np.linalg.norm(axis)
        u = np.cross(axis, [0, 0, 1] if abs(axis[2]) < 0.9 else [1, 0, 0])
        u /= np.linalg.norm(u)
        w = np.cross(axis, u)
        closed = arc >= 2 * math.pi - 1e-6
        ns = seg if closed else seg + 1
        v = []
        for i in range(ns):
            a = start + arc * i / seg
            cdir = math.cos(a) * u + math.sin(a) * w
            for j in range(sides):
                b = 2 * math.pi * j / sides
                v.append(np.asarray(c) + (R + r * math.cos(b)) * cdir + r * math.sin(b) * axis)
        f = []
        for i in range(seg):
            i2 = (i + 1) % ns if closed else i + 1
            for j in range(sides):
                j2 = (j + 1) % sides
                f.append([i * sides + j, i2 * sides + j, i2 * sides + j2, i * sides + j2])
        self._add(mat, np.array(v), f)

    def merge(self, other, M=None):
        for mat, (vs, fs, n) in other.parts.items():
            v = np.concatenate(vs)
            if M is not None:
                v = v @ M[:3, :3].T + M[:3, 3]
            self._add(mat, v, fs)


def Mx(pos=(0, 0, 0), R=None):
    M = np.eye(4)
    if R is not None:
        M[:3, :3] = R
    M[:3, 3] = pos
    return M


def rz(deg):
    t = math.radians(deg)
    return np.array([[math.cos(t), -math.sin(t), 0], [math.sin(t), math.cos(t), 0], [0, 0, 1]])


def rx(deg):
    t = math.radians(deg)
    return np.array([[1, 0, 0], [0, math.cos(t), -math.sin(t)], [0, math.sin(t), math.cos(t)]])


def ry(deg):
    t = math.radians(deg)
    return np.array([[math.cos(t), 0, math.sin(t)], [0, 1, 0], [-math.sin(t), 0, math.cos(t)]])


# ---------------------------------------------------------------- free weights
def plate(g, x, r=PLATE_R, th=0.055, axis_sign=1):
    g.cyl(RUBBER, (x, 0, 0), (x + axis_sign * th, 0, 0), r, n=40)
    g.cyl(STEEL, (x - axis_sign * 0.004, 0, 0), (x + axis_sign * (th + 0.004), 0, 0), 0.05, n=20)


def barbell(plates=1, length=2.2, plate_r=PLATE_R, **_):
    g = Geo()
    g.cyl(STEEL, (-0.66, 0, 0), (0.66, 0, 0), 0.0145, n=14)
    for s in (-1, 1):
        g.cyl(STEEL, (s * 0.66, 0, 0), (s * 0.70, 0, 0), 0.04, n=18)
        g.cyl(STEEL, (s * 0.70, 0, 0), (s * length / 2, 0, 0), 0.025, n=18)
        x = 0.705
        for k in range(plates):
            th = 0.06 if plate_r >= 0.2 else 0.035
            g.cyl(RUBBER, (s * x, 0, 0), (s * (x + th), 0, 0), plate_r if k == 0 else plate_r * 0.85, n=40)
            x += th + 0.003
        g.cyl(DARKSTEEL, (s * x, 0, 0), (s * (x + 0.035), 0, 0), 0.034, n=16)
    return g


def ezbar(plates=1, **_):
    g = Geo()
    pts = [(-0.62, 0, 0), (-0.3, 0, 0), (-0.22, 0, 0.025), (-0.14, 0, -0.012), (-0.06, 0, 0.0),
           (0.06, 0, 0.0), (0.14, 0, -0.012), (0.22, 0, 0.025), (0.3, 0, 0), (0.62, 0, 0)]
    g.tube(STEEL, [np.array(p) for p in pts], 0.0145)
    for s in (-1, 1):
        g.cyl(STEEL, (s * 0.38, 0, 0), (s * 0.42, 0, 0), 0.035, n=16)
        g.cyl(RUBBER, (s * 0.425, 0, 0), (s * 0.465, 0, 0), 0.15, n=32)
        g.cyl(DARKSTEEL, (s * 0.47, 0, 0), (s * 0.5, 0, 0), 0.03, n=14)
    return g


def dumbbell(head=0.062, **_):
    """Hex dumbbell, handle along X centred on the origin (the grip point)."""
    g = Geo()
    g.cyl(STEEL, (-0.075, 0, 0), (0.075, 0, 0), 0.0155, n=14)
    for s in (-1, 1):
        g.cyl(RUBBER, (s * 0.068, 0, 0), (s * 0.165, 0, 0), head, n=6)
        g.cyl(STEEL, (s * 0.066, 0, 0), (s * 0.072, 0, 0), 0.024, n=14)
    return g


def kettlebell(**_):
    """Handle along X at the origin (grip), bell hangs toward -Z."""
    g = Geo()
    g.sphere(RUBBER, (0, 0, -0.165), 0.105, scale=(1, 1, 0.95), zmin=-0.8)
    g.tube(RUBBER, [np.array(p) for p in [(-0.065, 0, -0.1), (-0.07, 0, -0.035), (-0.045, 0, 0.0),
                                           (0.045, 0, 0.0), (0.07, 0, -0.035), (0.065, 0, -0.1)]], 0.0165, n=12)
    return g


def medball(r=0.115, **_):
    g = Geo()
    g.sphere(MEDBALL, (0, 0, 0), r, seg=28, rings=14)
    return g


def plate_held(**_):
    g = Geo()
    g.cyl(RUBBER, (0, -0.02, 0), (0, 0.02, 0), 0.17, n=36)
    g.cyl(STEEL, (0, -0.024, 0), (0, 0.024, 0), 0.03, n=14)
    return g


def cable_bar(length=0.52, **_):
    """Straight cable attachment: knurled bar, end collars, centre swivel."""
    g = Geo()
    g.cyl(STEEL, (-length / 2, 0, 0), (length / 2, 0, 0), 0.0145, n=14)
    for s in (-1, 1):
        g.cyl(DARKSTEEL, (s * (length / 2 - 0.03), 0, 0), (s * length / 2, 0, 0), 0.022, n=14)
    g.cyl(DARKSTEEL, (0, 0, 0), (0, 0, 0.05), 0.012, n=10)
    return g


def pvc(length=1.5, **_):
    g = Geo()
    g.cyl(PVC, (-length / 2, 0, 0), (length / 2, 0, 0), 0.016, n=12)
    return g


def trapbar(**_):
    g = Geo()
    hexr = 0.42
    pts = [np.array([hexr * math.cos(math.radians(a)), hexr * 0.62 * math.sin(math.radians(a)), 0])
           for a in range(0, 361, 60)]
    g.tube(STEEL, pts, 0.016)
    for s in (-1, 1):
        g.cyl(STEEL, (s * 0.29, -0.12, 0), (s * 0.29, 0.12, 0), 0.017, n=12)  # handles along Y
        g.cyl(STEEL, (s * hexr, 0, 0), (s * 0.85, 0, 0), 0.025, n=14)
        g.cyl(RUBBER, (s * 0.5, 0, 0), (s * 0.56, 0, 0), PLATE_R, n=40)
    return g


def landmine_bar(length=1.9, **_):
    """Bar from origin (pivot end) along +X; sleeve with plate at the far end."""
    g = Geo()
    g.cyl(STEEL, (0, 0, 0), (length - 0.35, 0, 0), 0.0145, n=12)
    g.cyl(STEEL, (length - 0.35, 0, 0), (length, 0, 0), 0.025, n=14)
    g.cyl(RUBBER, (length - 0.33, 0, 0), (length - 0.28, 0, 0), 0.115, n=32)
    return g


def landmine_base(**_):
    g = Geo()
    g.box(FRAME, (0, 0, 0.01), (0.3, 0.3, 0.02))
    g.cyl(FRAME, (0, 0, 0.0), (0, 0, 0.07), 0.04)
    return g


# ------------------------------------------------------------------ benches
def bench(length=1.2, height=0.44, incline=0.0, decline=0.0, seat=True, **_):
    """Flat / incline / decline bench.  Pad top at `height`, long axis along Y.
    The head end is -Y.  incline: back pad angle (deg) raised at the -Y end,
    pivot at y=-0.05.  decline: whole pad tilted head-down."""
    g = Geo()
    th = 0.065
    w = 0.28
    if incline > 0:
        seat_len = 0.36
        g.box(PAD, (0, 0.17, height - th / 2), (w, seat_len, th))
        back_len = 0.82
        R = rx(-incline)
        piv = np.array([0, -0.02, height])
        c = piv + R @ np.array([0, -back_len / 2, -th / 2])
        g.box(PAD, c, (w, back_len, th), R)
        top = piv + R @ np.array([0, -back_len * 0.75, -th])
        g.cyl(FRAME, top, (0, top[1], 0.05), 0.025)
        g.box(FRAME, (0, 0.05, 0.03), (0.06, 0.95, 0.06))
        g.box(FRAME, (0, 0.42, 0.03), (0.42, 0.06, 0.06))
        g.box(FRAME, (0, -0.45, 0.03), (0.42, 0.06, 0.06))
        g.cyl(FRAME, (0, 0.17, height - th), (0, 0.17, 0.06), 0.03)
    elif decline > 0:
        R = rx(decline)
        c = np.array([0, 0.0, height])
        g.box(PAD, c + R @ np.array([0, 0, -th / 2]), (w, length, th), R)
        high = c + R @ np.array([0, length / 2, -th])
        low = c + R @ np.array([0, -length / 2, -th])
        g.cyl(FRAME, high, (0, high[1], 0.05), 0.03)
        g.cyl(FRAME, low, (0, low[1], 0.05), 0.03)
        g.box(FRAME, (0, 0, 0.03), (0.06, length, 0.06))
        roll = c + R @ np.array([0, length / 2 + 0.12, 0.05])
        g.cyl(FRAME, high, roll + np.array([0, 0, -0.04]), 0.022)
        g.cyl(PAD, roll + np.array([-0.18, 0, 0]), roll + np.array([0.18, 0, 0]), 0.055, n=20)
        g.cyl(PAD, roll + np.array([-0.18, -0.14, -0.13]), roll + np.array([0.18, -0.14, -0.13]), 0.05, n=20)
    else:
        g.box(PAD, (0, 0, height - th / 2), (w, length, th))
        for y in (-length / 2 + 0.12, length / 2 - 0.12):
            g.cyl(FRAME, (0, y, height - th), (0, y, 0.05), 0.03)
            g.box(FRAME, (0, y, 0.025), (0.42, 0.06, 0.05))
        g.box(FRAME, (0, 0, height - th - 0.03), (0.06, length - 0.2, 0.05))
    return g


def preacher(height=0.62, foot=0.0, foot_y=0.3, **_):
    g = Geo()
    g.box(PAD, (0, 0.0, height), (0.32, 0.32, 0.07))  # seat at -Y side
    R = rx(-50)
    c = np.array([0, 0.33, 1.02])
    g.box(PAD, c, (0.44, 0.34, 0.07), R)
    g.cyl(FRAME, (0, 0.0, height - 0.04), (0, 0.0, 0.05), 0.035)
    g.cyl(FRAME, (0, 0.38, 0.95), (0, 0.38, 0.05), 0.035)
    g.box(FRAME, (0, 0.2, 0.03), (0.5, 0.7, 0.05))
    if foot:     # foot bar in front of the seat post
        g.box(DARKSTEEL, (0, foot_y, foot), (0.42, 0.14, 0.03))
        g.cyl(FRAME, (0, foot_y, foot - 0.015), (0, foot_y, 0.05), 0.02)
    return g


def roman_chair(angle=45, **_):
    """45-degree back extension: hip pad at the origin facing up-back, user faces +Y."""
    g = Geo()
    R = rx(angle)
    hip = np.array([0, 0.0, 0.0])
    g.box(PAD, hip + R @ np.array([0, 0, -0.05]), (0.4, 0.22, 0.09), R)
    foot = hip + R @ np.array([0, 0, -0.0]) + np.array([0, -0.62, -0.62]) * 1.0
    g.cyl(PAD, foot + np.array([-0.15, 0.07, 0.07]), foot + np.array([0.15, 0.07, 0.07]), 0.045)
    g.box(FRAME, foot + np.array([0, 0.0, -0.02]), (0.34, 0.25, 0.03))
    g.cyl(FRAME, hip + R @ np.array([0, 0, -0.1]), foot + np.array([0, 0.0, -0.02]), 0.03)
    g.cyl(FRAME, hip + R @ np.array([0, 0, -0.1]), np.array([0, 0.1, -1.0 + 0.03]) + hip * 0, 0.03)
    return g


def plyo_box(size=(0.6, 0.5, 0.5), **_):
    g = Geo()
    g.box(WOOD, (0, 0, size[2] / 2), size)
    return g


def step(height=0.2, **_):
    g = Geo()
    g.box(GREY, (0, 0, height / 2), (0.8, 0.36, height))
    return g


def mat(**_):
    g = Geo()
    g.box(MAT, (0, 0, 0.004), (0.62, 1.85, 0.008))
    return g


def wall(**_):
    g = Geo()
    g.box(WALL, (0, -0.05, 1.3), (2.2, 0.1, 2.6))
    return g


def stability_ball(r=0.33, **_):
    g = Geo()
    g.sphere(BALL, (0, 0, r), r, seg=36, rings=18)
    return g


def bosu(**_):
    g = Geo()
    g.sphere(BALL, (0, 0, 0.03), 0.32, scale=(1, 1, 0.6), zmin=0.0)
    g.cyl(RUBBER, (0, 0, 0), (0, 0, 0.03), 0.325, n=40)
    return g


def foam_roller(**_):
    g = Geo()
    g.cyl(RUBBER, (-0.45, 0, 0.075), (0.45, 0, 0.075), 0.075, n=28)
    return g


# ------------------------------------------------------------------- stations
def upright(g, x, y, h, w=0.07):
    g.box(FRAME, (x, y, h / 2), (w, w, h))


def rack(height=2.2, width=1.2, hooks=1.35, safeties=0.6, **_):
    g = Geo()
    for x in (-width / 2, width / 2):
        for y in (-0.3, 0.3):
            upright(g, x, y, height)
        g.box(FRAME, (x, 0, 0.03), (0.08, 0.75, 0.06))
        g.box(FRAME, (x, 0, height - 0.04), (0.08, 0.7, 0.07))
        g.box(DARKSTEEL, (x * 0.94, 0.33, hooks - 0.03), (0.06, 0.08, 0.04))
        if safeties:
            g.box(DARKSTEEL, (x, 0, safeties), (0.05, 0.75, 0.04))
    g.box(FRAME, (0, -0.3, height - 0.04), (width, 0.07, 0.07))
    g.box(FRAME, (0, -0.3, 0.03), (width, 0.08, 0.06))
    return g


def pullup_station(height=2.3, width=1.2, **_):
    g = Geo()
    for x in (-width / 2, width / 2):
        upright(g, x, -0.35, height + 0.1)
        g.box(FRAME, (x, -0.1, 0.03), (0.08, 0.9, 0.06))
        g.cyl(FRAME, (x, -0.35, height), (x, 0.0, height), 0.03)
    g.cyl(STEEL, (-width / 2, 0.0, height), (width / 2, 0.0, height), 0.016)
    return g


def dip_station(height=1.2, gap=0.55, **_):
    g = Geo()
    for x in (-gap / 2, gap / 2):
        g.cyl(STEEL, (x, -0.35, height), (x, 0.35, height), 0.022)
        for y in (-0.3, 0.3):
            g.cyl(FRAME, (x, y, height - 0.02), (x * 1.25, y * 1.3, 0.04), 0.028)
    g.box(FRAME, (0, -0.42, 0.03), (gap * 1.4, 0.08, 0.06))
    return g


def cable_tower(pulley_h=1.0, **_):
    """Single column at local origin, user side +Y; pulley at local (0,0.12,h)."""
    g = Geo()
    upright(g, -0.16, -0.05, 2.25, 0.08)
    upright(g, 0.16, -0.05, 2.25, 0.08)
    g.box(FRAME, (0, -0.05, 2.22), (0.42, 0.12, 0.08))
    g.box(FRAME, (0, -0.2, 0.03), (0.6, 0.6, 0.06))
    g.box(DARKSTEEL, (0, -0.12, 0.45), (0.22, 0.1, 0.5))  # stack
    g.box(FRAME, (0, 0.04, 1.12), (0.08, 0.06, 2.1))  # carriage rail
    g.box(DARKSTEEL, (0, 0.08, pulley_h), (0.1, 0.08, 0.14))
    g.cyl(STEEL, (-0.025, 0.12, pulley_h), (0.025, 0.12, pulley_h), 0.045, n=20)
    return g


def lat_station(**_):
    """Seat at local origin top z=0.5, user faces +Y... knee pads above thighs."""
    g = Geo()
    g.box(PAD, (0, 0, 0.48), (0.36, 0.38, 0.08))
    g.cyl(FRAME, (0, 0, 0.44), (0, 0, 0.05), 0.04)
    g.box(FRAME, (0, -0.1, 0.03), (0.6, 0.9, 0.06))
    for x in (-0.13, 0.13):
        g.cyl(PAD, (x - 0.08, 0.2, 0.69), (x + 0.08, 0.2, 0.69), 0.05, n=18)
    g.cyl(FRAME, (0, 0.2, 0.69), (0, 0.5, 0.69), 0.025)
    upright(g, 0, 0.5, 2.3, 0.09)
    g.cyl(FRAME, (0, 0.5, 2.28), (0, 0.15, 2.28), 0.035)
    g.cyl(STEEL, (-0.025, 0.12, 2.25), (0.025, 0.12, 2.25), 0.05, n=20)
    g.box(DARKSTEEL, (0, 0.62, 0.5), (0.22, 0.1, 0.6))
    return g


def smith(height=2.2, **_):
    g = Geo()
    for x in (-0.62, 0.62):
        g.cyl(STEEL, (x, 0, 0.06), (x, 0, height - 0.05), 0.022)
        for y in (-0.35, 0.35):
            upright(g, x * 1.08, y, height)
        g.box(FRAME, (x * 1.08, 0, 0.03), (0.08, 0.8, 0.06))
        g.box(FRAME, (x * 1.08, 0, height - 0.035), (0.08, 0.8, 0.07))
    g.box(FRAME, (0, -0.35, height - 0.035), (1.42, 0.07, 0.07))
    return g


def smith_bar(plates=1, plate_r=PLATE_R, **_):
    g = barbell(plates=plates, plate_r=plate_r)
    for s in (-1, 1):
        g.box(DARKSTEEL, (s * 0.62, 0, 0), (0.07, 0.07, 0.08))
    return g


def leg_press(**_):
    """45-degree leg press.  Seat back at the -Y end, sled slides up +Y/+Z.
    Local origin: seat-back pivot on the floor."""
    g = Geo()
    g.box(FRAME, (0, 0.6, 0.04), (0.8, 2.2, 0.08))
    R = rx(45)
    for x in (-0.36, 0.36):
        g.cyl(STEEL, (x, 0.15, 0.3), np.array([x, 0.15, 0.3]) + R @ np.array([0, 1.7, 0]), 0.025)
    g.box(PAD, (0, -0.2, 0.42), (0.5, 0.4, 0.08))  # seat
    Rb = rx(-62)
    g.box(PAD, (0, -0.48, 0.66), (0.5, 0.65, 0.08), Rb)  # back
    g.cyl(FRAME, (0, -0.2, 0.38), (0, -0.2, 0.08), 0.04)
    g.cyl(FRAME, (0, -0.55, 0.6), (0, -0.55, 0.08), 0.04)
    return g


def leg_press_sled(**_):
    """Foot platform: local origin at the platform centre, face normal -Y-ish."""
    g = Geo()
    R = rx(45)
    g.box(DARKSTEEL, (0, 0.03, 0), (0.75, 0.04, 0.55), R)
    # carriage behind the platform; the weight horns sit on it up the rails,
    # clear of the feet (plates beside the platform covered the legs)
    for s in (-1, 1):
        g.box(FRAME, R @ np.array([s * 0.33, 0.12, 0.0]), (0.05, 0.22, 0.5), R)
        a = R @ np.array([s * 0.36, 0.22, 0.12])
        g.cyl(STEEL, a, a + np.array([s * 0.16, 0, 0]), 0.025)
        g.cyl(RUBBER, a + np.array([s * 0.05, 0, 0]), a + np.array([s * 0.1, 0, 0]), 0.17, n=32)
    return g


def leg_machine(**_):
    """Leg extension / seated leg curl frame; user sits facing +Y.
    Local origin: knee axis at (0,0,0.5)."""
    g = Geo()
    g.box(PAD, (0, -0.24, 0.47), (0.42, 0.46, 0.08))
    g.box(PAD, (0, -0.5, 0.82), (0.42, 0.08, 0.6), rx(-12))
    g.box(FRAME, (0, -0.25, 0.03), (0.7, 0.9, 0.06))
    g.cyl(FRAME, (0, -0.24, 0.43), (0, -0.24, 0.06), 0.045)
    upright(g, -0.32, -0.05, 1.1, 0.07)
    g.cyl(DARKSTEEL, (-0.33, 0, 0.5), (-0.25, 0, 0.5), 0.07, n=24)
    for s in (-1, 1):
        g.cyl(PAD, (-0.2, -0.24, 0.58), (-0.2, -0.24, 0.72) if s < 0 else (-0.2, -0.24, 0.72), 0.0, n=4)
    return g


def leg_lever(**_):
    """Lever arm rotating about local X at origin; roller pad at -Z 0.4."""
    g = Geo()
    g.cyl(DARKSTEEL, (-0.28, 0, 0), (-0.28, 0, -0.42), 0.022)
    g.cyl(DARKSTEEL, (-0.28, 0, -0.42), (0.0, 0, -0.42), 0.018)
    g.cyl(PAD, (-0.17, 0, -0.42), (0.17, 0, -0.42), 0.05, n=20)
    return g


def lying_curl(**_):
    """Prone leg curl bench, user lies face down, head toward +Y.  Pad top z=0.62"""
    g = Geo()
    g.box(PAD, (0, 0.15, 0.6), (0.36, 1.2, 0.07), rx(4))
    g.box(FRAME, (0, 0.15, 0.03), (0.6, 1.4, 0.06))
    for y in (-0.3, 0.6):
        g.cyl(FRAME, (0, y, 0.56), (0, y, 0.06), 0.04)
    for x in (-0.12, 0.12):
        g.cyl(STEEL, (x, 0.65, 0.66), (x, 0.65, 0.8), 0.014)
    upright(g, -0.33, -0.48, 0.8, 0.07)
    return g


def seat_machine(seat_h=0.5, back=True, **_):
    """Generic plate-loaded / selectorised upper-body machine frame.  User sits
    facing +Y, seat centre at origin."""
    g = Geo()
    g.box(PAD, (0, 0, seat_h - 0.04), (0.42, 0.42, 0.08))
    if back:
        g.box(PAD, (0, -0.24, seat_h + 0.38), (0.42, 0.08, 0.66), rx(-8))
    g.cyl(FRAME, (0, 0, seat_h - 0.08), (0, 0, 0.06), 0.045)
    g.box(FRAME, (0, 0.05, 0.03), (0.9, 1.1, 0.06))
    for x in (-0.42, 0.42):
        upright(g, x, -0.3, 1.9, 0.08)
    g.box(FRAME, (0, -0.3, 1.9), (0.92, 0.08, 0.08))
    g.box(DARKSTEEL, (0, -0.42, 0.6), (0.24, 0.1, 0.8))
    return g


def machine_handles(width=0.6, **_):
    g = Geo()
    for s in (-1, 1):
        g.cyl(PAD, (s * width / 2, 0, -0.07), (s * width / 2, 0, 0.07), 0.018)
    return g


def lever_pair(**_):
    g = Geo()
    return g


def calf_block(**_):
    g = Geo()
    g.box(RUBBER, (0, 0, 0.04), (0.6, 0.22, 0.08))
    return g


def hip_machine(**_):
    """Seated abductor/adductor: user sits facing +Y on seat at origin."""
    g = Geo()
    g.box(PAD, (0, 0, 0.5), (0.45, 0.42, 0.08))
    g.box(PAD, (0, -0.25, 0.85), (0.45, 0.08, 0.6), rx(-20))
    g.box(FRAME, (0, 0.1, 0.03), (0.9, 1.1, 0.06))
    g.cyl(FRAME, (0, 0, 0.46), (0, 0, 0.06), 0.045)
    return g


def hip_pad(**_):
    g = Geo()
    g.box(PAD, (0, 0, 0), (0.07, 0.3, 0.16))
    return g


def kickback_machine(**_):
    g = Geo()
    g.box(PAD, (0, 0.3, 1.0), (0.32, 0.35, 0.08), rx(-30))  # chest pad
    g.box(PAD, (0, 0.05, 0.62), (0.3, 0.3, 0.07))  # knee/forearm pad
    g.box(FRAME, (0, 0, 0.03), (0.8, 1.2, 0.06))
    g.cyl(FRAME, (0, 0.3, 0.95), (0, 0.3, 0.06), 0.04)
    for x in (-0.15, 0.15):
        g.cyl(PAD, (x, 0.45, 0.9), (x, 0.45, 1.05), 0.016)
    return g


def trx_anchor(h=2.4, **_):
    g = Geo()
    g.box(FRAME, (0, 0, h + 0.05), (0.8, 0.08, 0.08))
    g.cyl(DARKSTEEL, (0, 0, h), (0, 0, h - 0.12), 0.012)
    return g


def battle_rope_anchor(**_):
    g = Geo()
    g.cyl(FRAME, (0, 0, 0), (0, 0, 0.25), 0.05)
    g.box(FRAME, (0, 0, 0.01), (0.3, 0.3, 0.02))
    return g


def sled(**_):
    g = Geo()
    for x in (-0.25, 0.25):
        g.box(DARKSTEEL, (x, 0, 0.02), (0.05, 0.9, 0.04))
        g.cyl(DARKSTEEL, (x, -0.45, 0.02), (x, -0.5, 0.08), 0.02)
    g.box(DARKSTEEL, (0, 0, 0.06), (0.55, 0.6, 0.03))
    for x in (-0.22, 0.22):
        g.cyl(STEEL, (x, 0.0, 0.07), (x, 0.0, 1.05), 0.022)
    g.cyl(STEEL, (0, 0, 0.07), (0, 0, 0.35), 0.025)
    g.cyl(RUBBER, (0, 0, 0.08), (0, 0, 0.14), PLATE_R, n=40)
    return g


def tire(**_):
    g = Geo()
    g.torus(RUBBER, (0, 0, 0.0), 0.5, 0.17, axis=(0, 0, 1), seg=40, sides=14)
    return g


def rower(**_):
    g = Geo()
    g.box(FRAME, (0, 0.1, 0.18), (0.08, 2.4, 0.06))
    g.box(PAD, (0, -0.1, 0.4), (0.3, 0.3, 0.06))  # seat (moves; static approx)
    g.cyl(DARKSTEEL, (-0.12, 1.15, 0.45), (0.12, 1.15, 0.45), 0.22, n=32)
    for x in (-0.12, 0.12):
        g.box(DARKSTEEL, (x, 0.85, 0.2), (0.14, 0.26, 0.03), rx(-50))
    g.cyl(FRAME, (0, -1.0, 0.18), (0, -1.0, 0.04), 0.03)
    g.cyl(FRAME, (0, 1.1, 0.18), (0, 1.1, 0.04), 0.03)
    return g


def treadmill(**_):
    g = Geo()
    g.box(RUBBER, (0, 0.1, 0.1), (0.6, 1.7, 0.08))
    g.box(FRAME, (0, 0.1, 0.05), (0.72, 1.8, 0.1))
    for x in (-0.36, 0.36):
        g.cyl(FRAME, (x, 0.85, 0.12), (x, 1.0, 1.25), 0.03)
        g.cyl(FRAME, (x, 0.95, 1.05), (x, 0.55, 1.05), 0.022)
    g.box(SCREEN, (0, 1.02, 1.3), (0.6, 0.12, 0.25), rx(25))
    return g


def bike(**_):
    g = Geo()
    g.box(FRAME, (0, 0, 0.03), (0.5, 1.0, 0.06))
    g.cyl(FRAME, (0, -0.25, 0.06), (0, -0.2, 0.86), 0.035)  # seat post
    g.box(PAD, (0, -0.2, 0.9), (0.18, 0.28, 0.06))
    g.cyl(FRAME, (0, 0.38, 0.06), (0, 0.32, 1.05), 0.035)
    g.cyl(FRAME, (-0.22, 0.32, 1.05), (0.22, 0.32, 1.05), 0.02)
    g.cyl(DARKSTEEL, (-0.03, 0.3, 0.42), (0.03, 0.3, 0.42), 0.22, n=32)
    g.cyl(FRAME, (0, -0.2, 0.86), (0, 0.32, 0.42), 0.03)
    return g


def elliptical(**_):
    g = Geo()
    g.box(FRAME, (0, 0.0, 0.05), (0.6, 1.8, 0.1))
    g.cyl(DARKSTEEL, (-0.05, -0.75, 0.35), (0.05, -0.75, 0.35), 0.28, n=32)
    g.box(FRAME, (0, 0.85, 0.75), (0.12, 0.1, 1.5))        # console post (the handle arms move with the hands)
    g.box(SCREEN, (0, 0.8, 1.35), (0.4, 0.1, 0.22), rx(25))
    return g



# ============================================================ v3 additions
CHROME = ("chrome", (0.8, 0.81, 0.83), 0.18, 1.0)
ROPEW = ("ropew", (0.13, 0.13, 0.14), 0.9, 0.0)
CUFF = ("cuff", (0.06, 0.06, 0.07), 0.75, 0.0)


def bench_rack(hooks=1.05, width=1.1, **_):
    """Bench-press uprights with J-hooks, standing behind the head end of a
    bench (local origin on the floor between the uprights, user side +Y)."""
    g = Geo()
    for x in (-width / 2, width / 2):
        g.box(FRAME, (x, 0, (hooks + 0.12) / 2), (0.06, 0.06, hooks + 0.12))
        g.box(FRAME, (x, 0.05, 0.025), (0.08, 0.55, 0.05))
        g.box(DARKSTEEL, (x * 0.96, 0.05, hooks - 0.02), (0.05, 0.09, 0.03))
        g.box(DARKSTEEL, (x * 0.96, 0.085, hooks + 0.015), (0.05, 0.02, 0.05))
    g.box(FRAME, (0, -0.02, 0.025), (width, 0.06, 0.05))
    return g


def lat_bar(length=1.2, **_):
    """Lat pulldown bar: straight middle, ends angled down, ring on top."""
    g = Geo()
    half = length / 2
    g.cyl(STEEL, (-0.34, 0, 0), (0.34, 0, 0), 0.0145, n=14)
    for s in (-1, 1):
        g.cyl(STEEL, (s * 0.34, 0, 0), (s * half, 0, -0.07), 0.0145, n=14)
        g.cyl(RUBBER, (s * (half - 0.13), 0, -0.052), (s * half, 0, -0.07), 0.018, n=14)
    g.cyl(DARKSTEEL, (0, 0, 0), (0, 0, 0.05), 0.01, n=10)
    g.torus(DARKSTEEL, (0, 0, 0.065), 0.016, 0.004, axis=(1, 0, 0), seg=16, sides=6)
    return g


def v_handle(**_):
    """Close neutral-grip (V / double D) row handle.  Local X joins the two
    hands, +Y points toward the cable, handles run along Z."""
    g = Geo()
    for s in (-1, 1):
        g.cyl(RUBBER, (s * 0.05, 0, -0.06), (s * 0.05, 0, 0.06), 0.016, n=14)
        g.cyl(STEEL, (s * 0.05, 0, 0.06), (0, 0.15, 0.0), 0.009, n=10)
        g.cyl(STEEL, (s * 0.05, 0, -0.06), (0, 0.15, 0.0), 0.009, n=10)
    g.torus(DARKSTEEL, (0, 0.165, 0), 0.016, 0.004, axis=(0, 0, 1), seg=16, sides=6)
    return g


def d_handle(**_):
    """Single stirrup handle.  Grip along local X, +Y toward the cable."""
    g = Geo()
    g.cyl(RUBBER, (-0.06, 0, 0), (0.06, 0, 0), 0.016, n=14)
    for s in (-1, 1):
        g.cyl(STRAP, (s * 0.065, 0, 0), (0, 0.12, 0), 0.008, n=8)
    g.torus(DARKSTEEL, (0, 0.135, 0), 0.016, 0.004, axis=(0, 0, 1), seg=16, sides=6)
    return g


def rope_knob(**_):
    g = Geo()
    g.sphere(RUBBER, (0, 0, 0), 0.022, seg=14, rings=8)
    return g


def ankle_cuff(**_):
    """Cuff around the ankle (local Z along the shin) with a D-ring at +Y."""
    g = Geo()
    g.cyl(CUFF, (0, 0, -0.03), (0, 0, 0.03), 0.054, n=20)
    g.torus(DARKSTEEL, (0, 0.07, 0), 0.016, 0.004, axis=(1, 0, 0), seg=16, sides=6)
    return g


def band_anchor(h=1.2, **_):
    """Sturdy post (rack upright) a band is looped around at height h."""
    g = Geo()
    g.box(FRAME, (0, 0, 1.1), (0.07, 0.07, 2.2))
    g.box(FRAME, (0, 0, 0.025), (0.5, 0.5, 0.05))
    g.torus(BAND, (0, 0, h), 0.05, 0.009, axis=(0, 0, 1), seg=20, sides=8)
    return g


def door_anchor(h=1.0, **_):
    g = Geo()
    g.box(WALL, (0, -0.06, 1.05), (0.9, 0.08, 2.1))
    g.box(STRAP, (0, -0.01, h), (0.04, 0.03, 0.06))
    return g


def ab_wheel(**_):
    """Wheel with handles on both sides, handle axis local X at the origin."""
    g = Geo()
    g.cyl(RUBBER, (-0.04, 0, 0), (0.04, 0, 0), 0.09, n=36)
    g.cyl(GREY, (-0.045, 0, 0), (0.045, 0, 0), 0.05, n=24)
    for s in (-1, 1):
        g.cyl(STEEL, (s * 0.045, 0, 0), (s * 0.075, 0, 0), 0.01, n=10)
        g.cyl(RUBBER, (s * 0.075, 0, 0), (s * 0.19, 0, 0), 0.016, n=14)
    return g


def hack_frame(angle=45, **_):
    """Hack squat: footplate and rails.  User stands on the plate (origin at
    the plate centre on the floor), back toward -Y, rails at `angle` from
    the floor rising toward -Y."""
    g = Geo()
    R = rx(-angle)
    g.box(FRAME, (0, -0.4, 0.04), (0.9, 1.9, 0.08))
    g.box(DARKSTEEL, (0, 0.0, 0.12), (0.7, 0.55, 0.04), rx(-18))
    for x in (-0.3, 0.3):
        a = np.array([x, -0.35, 0.2])
        g.cyl(STEEL, a, a + R @ np.array([0, -1.9, 0]) * -1 * -1, 0.028)
    for x in (-0.3, 0.3):
        top = np.array([x, -0.35, 0.2]) + R @ np.array([0, -1.9, 0])
        g.cyl(FRAME, top, (x, top[1], 0.05), 0.035)
    return g


def hack_sled(**_):
    """Back pad + shoulder pads, local origin at the shoulder line; pad face
    normal +Y (toward the user's back), up along +Z."""
    g = Geo()
    g.box(PAD, (0, -0.04, -0.35), (0.4, 0.07, 0.8))
    for s in (-1, 1):
        g.box(PAD, (s * 0.13, 0.06, 0.04), (0.11, 0.2, 0.08))
        g.cyl(DARKSTEEL, (s * 0.3, -0.06, 0.0), (s * 0.3, -0.06, -0.5), 0.03)
        g.cyl(STEEL, (s * 0.3, -0.06, -0.3), (s * 0.48, -0.06, -0.3), 0.025)
        g.cyl(RUBBER, (s * 0.4, -0.06, -0.3), (s * 0.45, -0.06, -0.3), PLATE_R, n=40)
    return g


def row_station(pulley_h=0.42, seat_h=0.42, **_):
    """Seated cable row: long low seat (user faces +Y, seat centre at the
    origin), foot plate at +Y and the pulley in front."""
    g = Geo()
    g.box(PAD, (0, -0.1, seat_h - 0.035), (0.32, 0.8, 0.07))
    g.box(FRAME, (0, 0.25, 0.04), (0.14, 1.9, 0.08))
    g.cyl(FRAME, (0, -0.1, seat_h - 0.07), (0, -0.1, 0.06), 0.035)
    fp = np.array([0, 0.78, 0.2])
    g.box(DARKSTEEL, fp, (0.48, 0.03, 0.28), rx(-25))
    g.cyl(FRAME, fp + np.array([0, 0.05, -0.12]), (0, 0.85, 0.06), 0.03)
    g.box(FRAME, (0, 1.22, 1.05), (0.12, 0.12, 2.1))
    g.box(DARKSTEEL, (0, 1.36, 0.6), (0.24, 0.12, 0.8))
    g.box(DARKSTEEL, (0, 1.12, pulley_h), (0.1, 0.1, 0.14))
    g.cyl(STEEL, (-0.025, 1.08, pulley_h), (0.025, 1.08, pulley_h), 0.045, n=20)
    return g


def press_machine(seat_h=0.46, back_angle=10, **_):
    """Selectorised seated press frame (chest / shoulder press): seat at the
    origin, user faces +Y, back pad, weight stack and lever pivot posts
    behind.  Moving arms are drawn as segments by the template."""
    g = Geo()
    g.box(PAD, (0, 0.02, seat_h - 0.04), (0.42, 0.4, 0.08))
    g.box(PAD, (0, -0.24, seat_h + 0.42), (0.42, 0.08, 0.72), rx(-back_angle))
    g.cyl(FRAME, (0, 0, seat_h - 0.08), (0, 0, 0.06), 0.045)
    g.box(FRAME, (0, -0.1, 0.03), (1.0, 1.1, 0.06))
    for x in (-0.46, 0.46):
        upright(g, x, -0.38, 1.75, 0.08)
    g.box(FRAME, (0, -0.38, 1.75), (1.0, 0.08, 0.08))
    g.box(DARKSTEEL, (0, -0.52, 0.65), (0.26, 0.12, 0.9))
    return g


def assist_frame(height=2.3, **_):
    """Assisted pull-up machine: tall frame with handles at `height`, knee
    platform rail; the moving knee pad is a separate dynamic part."""
    g = Geo()
    for x in (-0.45, 0.45):
        upright(g, x, -0.3, height + 0.1, 0.08)
        g.cyl(FRAME, (x, -0.3, height), (x * 0.95, 0.12, height), 0.03)
        g.cyl(RUBBER, (x * 0.95, 0.12, height), (x * 0.95, 0.12 + 0.02, height - 0.14), 0.018)
    g.box(FRAME, (0, -0.3, height + 0.1), (0.98, 0.08, 0.08))
    g.box(FRAME, (0, -0.15, 0.03), (1.0, 0.8, 0.06))
    g.box(DARKSTEEL, (0, -0.45, 0.7), (0.26, 0.12, 1.0))
    for x in (-0.2, 0.2):
        g.box(DARKSTEEL, (x, 0.05, 0.45), (0.16, 0.3, 0.05))   # steps
    return g


def knee_pad(**_):
    g = Geo()
    g.box(PAD, (0, 0, -0.035), (0.42, 0.34, 0.07))
    for x in (-0.18, 0.18):
        g.cyl(DARKSTEEL, (x, -0.12, -0.07), (x, -0.32, -0.45), 0.02)
    return g


def pec_frame(seat_h=0.46, **_):
    """Pec deck / rear-delt machine frame: seat, back pad, tall column with the
    arm pivots above the shoulders."""
    g = Geo()
    g.box(PAD, (0, 0.02, seat_h - 0.04), (0.42, 0.4, 0.08))
    g.box(PAD, (0, -0.22, seat_h + 0.42), (0.36, 0.08, 0.76), rx(-6))
    g.cyl(FRAME, (0, 0, seat_h - 0.08), (0, 0, 0.06), 0.045)
    g.box(FRAME, (0, -0.15, 0.03), (0.9, 1.0, 0.06))
    upright(g, 0, -0.42, 2.0, 0.1)
    g.box(FRAME, (0, -0.25, 1.98), (0.12, 0.42, 0.08))
    g.box(DARKSTEEL, (0, -0.56, 0.7), (0.26, 0.12, 1.0))
    return g


def leg_curl_seated(**_):
    """Seated leg curl frame (user faces +Y, knee axis at local (0,0,0.5)):
    seat, back pad, thigh hold-down pad above the knees."""
    g = leg_machine()
    g.cyl(PAD, (-0.2, 0.0, 0.66), (0.2, 0.0, 0.66), 0.05, n=20)
    g.cyl(DARKSTEEL, (-0.32, 0.0, 0.66), (-0.2, 0.0, 0.66), 0.02)
    g.cyl(DARKSTEEL, (-0.32, 0.0, 0.66), (-0.32, -0.02, 0.5), 0.022)
    return g


def stair_climber(**_):
    g = Geo()
    g.box(FRAME, (0, 0.0, 0.05), (0.75, 1.3, 0.1))
    for k in range(5):
        g.box(DARKSTEEL, (0, -0.4 + 0.2 * k, 0.15 + 0.2 * k), (0.62, 0.26, 0.04))
    for x in (-0.36, 0.36):
        g.cyl(FRAME, (x, -0.55, 0.1), (x, 0.55, 1.2), 0.03)
        g.cyl(FRAME, (x, 0.3, 1.05), (x, -0.25, 1.05), 0.022)
    g.box(SCREEN, (0, 0.62, 1.35), (0.5, 0.1, 0.24), rx(25))
    return g


def ski_erg(**_):
    g = Geo()
    g.box(FRAME, (0, 0.0, 0.03), (0.9, 0.7, 0.06))
    g.box(FRAME, (0, 0.2, 1.1), (0.16, 0.12, 2.1))
    g.cyl(DARKSTEEL, (-0.03, 0.2, 1.9), (0.03, 0.2, 1.9), 0.22, n=32)
    g.box(SCREEN, (0, 0.13, 1.55), (0.22, 0.04, 0.16))
    return g


def battle_rope_pair(**_):
    g = Geo()
    return g


def gym_rings(**_):
    g = Geo()
    g.torus(WOOD, (0, 0, 0), 0.09, 0.014, axis=(1, 0, 0), seg=28, sides=10)
    return g


def parallettes(**_):
    g = Geo()
    for s in (-1, 1):
        g.cyl(WOOD, (s * 0.0, -0.15, 0.2), (s * 0.0, 0.15, 0.2), 0.017)
    return g


def captain_station(height=1.45, **_):
    """Vertical knee raise station: back pad, forearm pads with handles at
    `height` (forearm top), foot steps; user faces +Y, back pad at -Y."""
    g = Geo()
    for x in (-0.3, 0.3):
        upright(g, x, -0.25, height + 0.35, 0.07)
        g.box(PAD, (x * 0.95, 0.0, height - 0.02), (0.11, 0.42, 0.06))
        g.cyl(RUBBER, (x * 0.95, 0.22, height + 0.0), (x * 0.95, 0.22, height + 0.13), 0.017)
        g.box(DARKSTEEL, (x * 1.1, -0.05, 0.3), (0.14, 0.22, 0.04))     # foot steps beside the legs
        g.cyl(FRAME, (x, -0.25, height - 0.02), (x * 0.95, 0.15, height - 0.02), 0.022)   # pad arms
    g.box(PAD, (0, -0.2, height - 0.05), (0.36, 0.07, 0.62))
    g.box(FRAME, (0, -0.25, height + 0.33), (0.67, 0.07, 0.07))
    g.box(FRAME, (0, -0.2, 0.03), (0.8, 0.7, 0.06))
    return g

CONE = ("cone", (0.95, 0.42, 0.08), 0.5, 0.0)


def cone(h=0.23, **_):
    """Training cone on a square base."""
    g = Geo()
    g.box(CONE, (0, 0, 0.006), (0.2, 0.2, 0.012))
    g.cyl(CONE, (0, 0, 0.012), (0, 0, h), 0.075, n=20, r1=0.012)
    return g


# ------------------------------------------------------------------ 5.4 (moves that had no picture)
def hurdle(h=0.42, w=0.7, **_):
    """Low training hurdle: two feet, two posts and a crossbar along X at height h."""
    g = Geo()
    for s in (-1, 1):
        g.box(CONE, (s * w / 2, 0, 0.01), (0.04, 0.34, 0.02))
        g.cyl(CONE, (s * w / 2, 0, 0.0), (s * w / 2, 0, h), 0.013, n=10)
    g.cyl(CONE, (-w / 2, 0, h), (w / 2, 0, h), 0.016, n=12)
    return g


def recumbent(**_):
    """Recumbent bike: low seat with a reclined backrest, side handles, the crank in front at hip height."""
    g = Geo()
    g.box(FRAME, (0, 0.1, 0.03), (0.5, 1.5, 0.06))
    g.box(PAD, (0, -0.25, 0.52), (0.42, 0.42, 0.08))
    g.box(PAD, (0, -0.52, 0.85), (0.42, 0.08, 0.6), rx(-22))
    g.cyl(FRAME, (0, -0.25, 0.06), (0, -0.25, 0.48), 0.035)
    for s_ in (-1, 1):
        g.cyl(RUBBER, (s_ * 0.3, -0.35, 0.58), (s_ * 0.3, -0.1, 0.58), 0.018, n=10)
        g.cyl(FRAME, (s_ * 0.3, -0.25, 0.1), (s_ * 0.3, -0.25, 0.58), 0.02)
    g.cyl(FRAME, (0, 0.0, 0.3), (0, 0.62, 0.45), 0.04)
    g.cyl(DARKSTEEL, (-0.03, 0.62, 0.45), (0.03, 0.62, 0.45), 0.2, n=32)
    g.cyl(FRAME, (0, 0.62, 0.45), (0, 0.72, 1.0), 0.03)
    g.box(SCREEN, (0, 0.72, 1.05), (0.3, 0.06, 0.18), rx(30))
    return g


def rail(h=1.0, **_):
    """Machine handle post: an upright with a short handle on top running along Y."""
    g = Geo()
    g.box(FRAME, (0, 0, 0.01), (0.2, 0.2, 0.02))
    g.box(FRAME, (0, 0, h / 2), (0.06, 0.06, h))
    g.cyl(RUBBER, (0, -0.16, h), (0, 0.08, h), 0.018, n=12)
    return g


def gripper(**_):
    """Hand gripper: two handles joined by a coil at the top (held upright in one hand, origin at the coil)."""
    g = Geo()
    g.cyl(STEEL, (-0.012, 0, 0), (0.012, 0, 0), 0.012, n=12)
    g.cyl(RUBBER, (0, -0.012, -0.01), (0, -0.03, -0.11), 0.011, n=10)
    g.cyl(RUBBER, (0, 0.012, -0.01), (0, 0.03, -0.11), 0.011, n=10)
    return g


def wrist_roller(length=0.42, drop=0.55, **_):
    """Wrist roller: a bar along X, a cord from its middle down to a small plate."""
    g = Geo()
    g.cyl(WOOD, (-length / 2, 0, 0), (length / 2, 0, 0), 0.018, n=14)
    g.cyl(ROPE, (0, 0, -0.018), (0, 0, -drop), 0.004, n=6)
    g.cyl(RUBBER, (0, -0.012, -drop - 0.11), (0, 0.012, -drop - 0.11), 0.11, n=28)
    return g


def ssb(**_):
    """Safety squat bar: straight bar along X with two handles that come forward over the shoulders and a pad."""
    g = Geo()
    g.cyl(STEEL, (-1.0, 0, 0), (1.0, 0, 0), 0.016, n=12)
    g.cyl(PAD, (-0.25, 0.01, 0.01), (0.25, 0.01, 0.01), 0.05, n=18)
    for s in (-1, 1):
        g.cyl(STEEL, (s * 0.13, 0, 0), (s * 0.13, 0.42, -0.12), 0.015, n=10)
        g.cyl(RUBBER, (s * 0.13, 0.32, -0.09), (s * 0.13, 0.44, -0.13), 0.019, n=10)
        g.cyl(RUBBER, (s * 0.72, 0, 0), (s * 0.78, 0, 0), PLATE_R, n=40)
    return g

def shrug_machine(**_):
    """Standing shrug machine: foot platform, two posts behind the athlete with a top beam, a weight stack
    behind; the lever arms come forward to handles at the sides of the thighs (drawn as segments)."""
    g = Geo()
    g.box(FRAME, (0, 0.05, 0.03), (1.0, 0.8, 0.06))
    for x in (-0.5, 0.5):
        g.cyl(FRAME, (x, -0.42, 0.06), (x, -0.42, 1.55), 0.035)
        g.cyl(FRAME, (x, -0.42, 1.2), (x * 0.86, -0.32, 1.2), 0.03)
    g.box(FRAME, (0, -0.42, 1.57), (1.08, 0.08, 0.08))
    g.box(FRAME, (0, -0.62, 0.7), (0.3, 0.16, 1.3))
    g.box(DARKSTEEL, (0, -0.52, 0.45), (0.24, 0.05, 0.5))
    return g


def ghd(**_):
    """Glute-ham developer: long frame along Y, a round hip pad, a foot plate with ankle rollers in front."""
    g = Geo()
    g.box(FRAME, (0, 0.35, 0.05), (0.14, 1.7, 0.1))
    for y in (-0.45, 1.15):
        g.box(FRAME, (0, y, 0.03), (0.7, 0.1, 0.06))
    g.cyl(FRAME, (0, 0.0, 0.1), (0, 0.0, 0.84), 0.04)
    g.cyl(PAD, (-0.2, 0.0, 0.88), (0.2, 0.0, 0.88), 0.11, n=24)
    g.cyl(FRAME, (0, 0.8, 0.1), (0, 0.8, 0.7), 0.04)
    g.box(FRAME, (0, 0.86, 0.6), (0.36, 0.04, 0.28), rx(20))
    for z, y in ((0.56, 0.78), (0.7, 0.8)):
        g.cyl(PAD, (-0.17, y, z), (0.17, y, z), 0.045, n=18)
    return g


def tbar_chest(**_):
    """Chest-supported T-bar row: foot platform, an inclined chest pad on a post, the lever pivot low in front."""
    g = Geo()
    g.box(FRAME, (0, -0.1, 0.03), (0.6, 1.6, 0.06))
    g.box(FRAME, (0, -0.55, 0.2), (0.55, 0.4, 0.06), rx(-12))
    g.cyl(FRAME, (0, 0.2, 0.06), (0, 0.2, 1.05), 0.04)
    g.box(PAD, (0, 0.05, 1.06), (0.32, 0.5, 0.08), rx(34))
    g.cyl(FRAME, (0, 0.75, 0.06), (0, 0.75, 0.18), 0.05)
    return g

def bosu_dn(**_):
    """Balance trainer dome-down: origin at the middle of the flat platform (now on top)."""
    g = bosu()
    for mat, P in g.parts.items():
        P[0] = [np.asarray(v) * np.array([1, 1, -1]) for v in P[0]]
        P[1] = [list(f)[::-1] for f in P[1]]
    return g


KINDS = {k: v for k, v in globals().items()
         if callable(v) and not k.startswith("_") and k not in
         ("Geo", "Mx", "rz", "rx", "ry", "plate", "upright")
         and not isinstance(v, type)}


# ---------------------------------------------------------- blender build
_MATS = {}


def build(kind, name, **shape):
    import bpy
    from .scene import flat_material
    g = KINDS[kind](**shape)
    root = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(root)
    for mat, (vs, fs, n) in g.parts.items():
        v = np.concatenate(vs)
        me = bpy.data.meshes.new(f"{name}_{mat[0]}")
        me.from_pydata(v.tolist(), [], fs)
        me.update()
        try:
            me.set_sharp_from_angle(angle=math.radians(35))
        except Exception:
            me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
        ob = bpy.data.objects.new(f"{name}_{mat[0]}", me)
        bpy.context.scene.collection.objects.link(ob)
        ob.parent = root
        me.materials.append(flat_material(mat[0], mat[1], rough=mat[2], metal=mat[3]))
        if shape.get("shadow") is False:      # large flat props (a wall seen edge-on) would darken the floor
            ob.visible_shadow = False
    return root


def cylinder_between(name, p0, p1, r, matdef=ROPE):
    """Dynamic straight segment (cables, bands, straps)."""
    import bpy
    from .scene import flat_material
    ob = bpy.data.objects.get(name)
    if ob is None:
        g = Geo()
        g.cyl(matdef, (0, 0, 0), (0, 0, 1), 1.0, n=10)
        vs, fs, _ = g.parts[matdef]
        me = bpy.data.meshes.new(name)
        me.from_pydata(np.concatenate(vs).tolist(), [], fs)
        me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
        ob = bpy.data.objects.new(name, me)
        bpy.context.scene.collection.objects.link(ob)
        me.materials.append(flat_material(matdef[0], matdef[1], rough=matdef[2], metal=matdef[3]))
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
    a = p1 - p0
    L = max(np.linalg.norm(a), 1e-4)
    z = a / L
    x = np.cross(z, [0, 0, 1] if abs(z[2]) < 0.9 else [1, 0, 0])
    x /= np.linalg.norm(x)
    y = np.cross(z, x)
    from mathutils import Matrix
    M = np.eye(4)
    M[:3, 0], M[:3, 1], M[:3, 2], M[:3, 3] = x * r, y * r, z * L, p0
    ob.matrix_world = Matrix(M.tolist())
    return ob
