"""Left/right mirror of a solved pose (for alternating reps).

The MakeHuman base mesh is left/right symmetric, so every vertex has a
partner on the other side; the mirrored pose takes each vertex from its
partner and reflects it across x = 0.  Triangle winding stays correct.
Bones swap .L/.R the same way; equipment matrices are conjugated with the
reflection (a proper rotation, so geometry is not turned inside out).
"""
import numpy as np

from .poses import Pose

S = np.diag([-1.0, 1.0, 1.0])


OBJ_FLIP_Y = {"landmine_bar"}


class Mirror:
    def __init__(self, rig):
        self.r = rig
        v = rig.verts
        refl = v * np.array([-1.0, 1.0, 1.0])
        part = np.empty(len(v), np.int64)
        for a in range(0, len(v), 1500):
            d = ((refl[a:a + 1500, None, :] - v[None, :, :]) ** 2).sum(-1)
            part[a:a + 1500] = d.argmin(1)
        self.part = part
        names = rig.names
        idx = {n: i for i, n in enumerate(names)}

        def other(n):
            if n.endswith(".L"):
                return n[:-2] + ".R"
            if n.endswith(".R"):
                return n[:-2] + ".L"
            return n
        self.bpart = np.array([idx.get(other(n), i) for i, n in enumerate(names)])

    def pose(self, p):
        verts = p.verts[self.part] * np.array([-1.0, 1.0, 1.0])
        D = np.einsum("ij,bjk,kl->bil", S, p.D[self.bpart], S)
        Hp = p.Hp[self.bpart] * np.array([-1.0, 1.0, 1.0])
        eq = []
        for e in p.equip:
            e = dict(e)
            if e["kind"] == "_seg":
                e["p0"] = np.asarray(e["p0"]) * np.array([-1.0, 1, 1])
                e["p1"] = np.asarray(e["p1"]) * np.array([-1.0, 1, 1])
            else:
                M = np.array(e["M"], float)
                M4 = np.eye(4)
                M4[:3, :3] = S
                # reflect the world, then reflect the object about a plane it is
                # symmetric in (x for bells and bars; the landmine bar runs along
                # its own x from the pivot, so it is flipped in y instead)
                Mo = np.eye(4)
                Mo[:3, :3] = np.diag([1.0, -1.0, 1.0]) if e["kind"] in OBJ_FLIP_Y else S
                e["M"] = M4 @ M @ Mo
            eq.append(e)
        info = dict(p.info)
        info["mirrored"] = True
        return Pose(D, Hp, verts, eq, info)
