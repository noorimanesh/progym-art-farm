"""Blender scene: studio lights, shadow-catcher floor, camera and the body
objects (skin mesh + shoe and hair shells).  Requires bpy."""
import math

import bpy
import numpy as np

from . import paint
from .paint import LIME, srgb
HL5 = False                 # 5.5: target muscles glow red with the effort of each frame, secondary muscles orange
RED = srgb("#e8352e")
ORANGE = srgb("#f39a2b")

BG = (0.905, 0.91, 0.918)  # light neutral grey (sRGB) used when compositing
STYLE = "v3"


def background(size):
    """Backdrop the transparent render is composited on: flat grey (v3) or a
    soft studio gradient - a lighter centre fading to the edges, the floor
    half a touch darker - identical for every exercise (v4)."""
    from PIL import Image
    W, H = size
    if STYLE != "v4":
        return Image.new("RGBA", size, tuple(int(round(c * 255)) for c in BG) + (255,))
    ys = (np.arange(H) + 0.5) / H
    xs = (np.arange(W) + 0.5) / W
    top = np.array([0.93, 0.935, 0.942])
    mid = np.array([0.905, 0.91, 0.918])
    flo = np.array([0.86, 0.865, 0.872])
    t = np.clip((ys - 0.55) / 0.35, 0, 1)[:, None]
    col = (top * (1 - ys[:, None] / 0.55).clip(0, 1) + mid * (ys[:, None] / 0.55).clip(0, 1))
    col = np.where(ys[:, None] < 0.55, col, mid * (1 - t) + flo * t)
    img = np.repeat(col[:, None, :], W, axis=1)
    vig = 1 - 0.035 * (((xs[None, :] - 0.5) / 0.5) ** 2 + ((ys[:, None] - 0.45) / 0.6) ** 2)
    img = img * vig[:, :, None]
    a = np.concatenate([np.clip(img * 255, 0, 255), np.full((H, W, 1), 255.0)], axis=2).astype(np.uint8)
    return Image.fromarray(a, "RGBA")


def init(threads=1, samples=20, res=(480, 320)):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    cy = sc.cycles
    cy.device = "CPU"
    cy.samples = samples
    cy.use_adaptive_sampling = True
    cy.adaptive_threshold = 0.03
    cy.use_denoising = True
    try:
        cy.denoiser = "OPENIMAGEDENOISE"
        cy.denoising_prefilter = "FAST"
        cy.denoising_input_passes = "RGB"
        cy.denoising_quality = "FAST"
    except Exception:
        pass
    cy.max_bounces = 3
    cy.diffuse_bounces = 1
    cy.glossy_bounces = 1
    cy.transmission_bounces = 0
    cy.transparent_max_bounces = 2
    cy.caustics_reflective = False
    cy.caustics_refractive = False
    cy.blur_glossy = 1.0
    sc.render.threads_mode = "FIXED"
    sc.render.threads = threads
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    sc.render.film_transparent = True
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGBA"
    sc.view_settings.view_transform = "AgX"
    try:
        sc.view_settings.look = "AgX - Base Contrast"
    except Exception:
        pass
    sc.render.use_persistent_data = True

    world = bpy.data.worlds.new("World")
    sc.world = world
    world.use_nodes = True
    bgn = world.node_tree.nodes["Background"]
    bgn.inputs[0].default_value = (0.8, 0.81, 0.83, 1)
    bgn.inputs[1].default_value = 0.35

    def area(name, loc, target, size, power, color=(1, 1, 1)):
        ld = bpy.data.lights.new(name, "AREA")
        ld.size = size
        ld.energy = power
        ld.color = color
        ob = bpy.data.objects.new(name, ld)
        sc.collection.objects.link(ob)
        ob.location = loc
        d = np.array(target) - np.array(loc)
        ob.rotation_euler = _look_euler(d)
        return ob

    if STYLE == "v4":
        sc.view_settings.exposure = -0.35
        try:
            sc.view_settings.look = "AgX - Medium High Contrast"
        except Exception:
            pass
        # soft three-point studio light: large warm key, broad cool fill, two rims;
        # the lights follow the camera (see set_camera) so every exercise is lit the same
        bgn.inputs[1].default_value = 0.16
        area("key", (3.2, 3.4, 4.2), (0, 0, 0.9), 2.2, 1900, (1.0, 0.975, 0.94))
        area("fill", (-3.8, 1.6, 2.0), (0, 0, 0.9), 5.0, 190, (0.94, 0.97, 1.0))
        area("rim", (-1.5, -4.0, 3.6), (0, 0, 1.1), 2.5, 800)
        area("rim2", (2.5, -3.5, 3.0), (0, 0, 1.1), 2.5, 420)
        cy.diffuse_bounces = 2          # light bounced off the floor: soft contact shading under feet and hands
        cy.max_bounces = 4
    else:
        area("key", (3.2, 3.4, 4.2), (0, 0, 0.9), 3.0, 1300, (1.0, 0.98, 0.95))
        area("fill", (-3.8, 1.6, 2.4), (0, 0, 0.9), 4.0, 420, (0.95, 0.97, 1.0))
        area("rim", (-1.5, -4.0, 3.6), (0, 0, 1.1), 2.0, 700)
        area("rim2", (2.5, -3.5, 3.0), (0, 0, 1.1), 2.0, 350)

    bpy.ops.mesh.primitive_plane_add(size=7, location=(0, 0, 0))
    floor = bpy.context.active_object
    floor.name = "floor"
    floor.is_shadow_catcher = True
    m = bpy.data.materials.new("floor")
    m.use_nodes = True
    m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.8, 0.8, 0.8, 1)
    floor.data.materials.append(m)

    cam_d = bpy.data.cameras.new("cam")
    cam_d.lens = 50
    cam_d.sensor_width = 36
    cam = bpy.data.objects.new("cam", cam_d)
    sc.collection.objects.link(cam)
    sc.camera = cam
    return sc


def _look_euler(d):
    from mathutils import Vector
    return Vector(d).to_track_quat("-Z", "Y").to_euler()


def set_camera(loc, target, lens=50):
    cam = bpy.data.objects["cam"]
    cam.location = loc
    cam.rotation_euler = _look_euler(np.array(target) - np.array(loc))
    cam.data.lens = lens
    if STYLE == "v4":
        # the light rig turns with the camera, so every view gets the same key / fill / rim layout
        t = np.array(target, float)
        d = np.array(loc, float) - t
        az = math.atan2(d[1], d[0])
        for name, da, dist, h, size in (("key", math.radians(50), 5.0, 4.2, 2.2),
                                        ("fill", math.radians(-65), 5.0, 1.6, 6.0),
                                        ("rim", math.radians(165), 4.5, 3.2, 2.5),
                                        ("rim2", math.radians(-150), 4.5, 2.8, 2.5)):
            ob = bpy.data.objects.get(name)
            if ob is None:
                continue
            p = np.array([t[0] + dist * math.cos(az + da), t[1] + dist * math.sin(az + da), h])
            ob.location = p
            ob.rotation_euler = _look_euler(np.array([t[0], t[1], 0.9]) - p)


# ------------------------------------------------------------------ materials
def attr_material(name, rough_skin=0.48, rough_cloth=0.78, sss=0.12):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    N = nt.nodes
    Lk = nt.links
    bsdf = N["Principled BSDF"]
    a_col = N.new("ShaderNodeAttribute"); a_col.attribute_name = "paint"
    a_hl = N.new("ShaderNodeAttribute"); a_hl.attribute_name = "hl"
    a_sk = N.new("ShaderNodeAttribute"); a_sk.attribute_name = "skinf"
    mix = N.new("ShaderNodeMix"); mix.data_type = "RGBA"; mix.blend_type = "MIX"
    mul = N.new("ShaderNodeMath"); mul.operation = "MULTIPLY"; mul.inputs[1].default_value = 0.62
    Lk.new(a_hl.outputs["Fac"], mul.inputs[0])
    Lk.new(mul.outputs[0], mix.inputs["Factor"])
    Lk.new(a_col.outputs["Color"], mix.inputs[6])
    mix.inputs[7].default_value = (*LIME, 1)
    Lk.new(mix.outputs[2], bsdf.inputs["Base Color"])
    rmix = N.new("ShaderNodeMapRange")
    rmix.inputs["To Min"].default_value = rough_cloth
    rmix.inputs["To Max"].default_value = rough_skin
    Lk.new(a_sk.outputs["Fac"], rmix.inputs["Value"])
    Lk.new(rmix.outputs[0], bsdf.inputs["Roughness"])
    smul = N.new("ShaderNodeMath"); smul.operation = "MULTIPLY"; smul.inputs[1].default_value = sss
    Lk.new(a_sk.outputs["Fac"], smul.inputs[0])
    Lk.new(smul.outputs[0], bsdf.inputs["Subsurface Weight"])
    bsdf.inputs["Subsurface Radius"].default_value = (1.0, 0.45, 0.28)
    bsdf.inputs["Subsurface Scale"].default_value = 0.012
    emul = N.new("ShaderNodeMath"); emul.operation = "MULTIPLY"; emul.inputs[1].default_value = 0.10
    Lk.new(a_hl.outputs["Fac"], emul.inputs[0])
    bsdf.inputs["Emission Color"].default_value = (*LIME, 1)
    Lk.new(emul.outputs[0], bsdf.inputs["Emission Strength"])
    try:
        bsdf.inputs["Specular IOR Level"].default_value = 0.4
    except KeyError:
        pass
    if STYLE == "v4":
        _v4_nodes(m, bsdf, a_sk, a_hl, mix, mul, emul, rmix, smul, rough_skin, rough_cloth)
        if HL5:
            _v5_hl(m, bsdf, a_col, mix, mul, emul)
    # the faint lime glow must not turn the body into a mesh light (slow light tree)
    m.cycles.emission_sampling = "NONE"
    return m


def _v4_nodes(m, bsdf, a_sk, a_hl, mix, mul, emul, rmix, smul, rough_skin, rough_cloth):
    """v4 look on top of the v3 attribute material:
    - skin: subsurface a little stronger, roughness varies over the surface (fine noise), concave
      folds between muscles shade darker (baked cavity), so muscle definition reads softly;
    - cloth: matte with a fine knit bump;
    - target muscles: a soft lime glow (colour mix eased in, gentle emission), not a flat patch."""
    nt = m.node_tree
    N, Lk = nt.nodes, nt.links
    # ---- highlight: eased factor (smoothstep) for the colour, softer and wider emission
    a_hl2 = N.new("ShaderNodeAttribute"); a_hl2.attribute_name = "hl"
    ease_ = N.new("ShaderNodeMapRange"); ease_.interpolation_type = "SMOOTHSTEP"
    ease_.inputs["From Min"].default_value = 0.0
    ease_.inputs["From Max"].default_value = 1.0
    Lk.new(a_hl2.outputs["Fac"], ease_.inputs["Value"])
    Lk.new(ease_.outputs[0], mul.inputs[0])
    mul.inputs[1].default_value = 0.48
    Lk.new(ease_.outputs[0], emul.inputs[0])
    emul.inputs[1].default_value = 0.22
    # ---- cavity darkening of the base colour (skin and cloth folds)
    a_cv = N.new("ShaderNodeAttribute"); a_cv.attribute_name = "cav"
    cmap = N.new("ShaderNodeMapRange")
    cmap.inputs["From Min"].default_value = 0.0
    cmap.inputs["From Max"].default_value = 1.0
    cmap.inputs["To Min"].default_value = 1.0
    cmap.inputs["To Max"].default_value = 0.78
    Lk.new(a_cv.outputs["Fac"], cmap.inputs["Value"])
    cmul = N.new("ShaderNodeMix"); cmul.data_type = "RGBA"; cmul.blend_type = "MULTIPLY"
    cmul.inputs["Factor"].default_value = 1.0
    Lk.new(mix.outputs[2], cmul.inputs[6])
    comb = N.new("ShaderNodeCombineColor")
    for k in ("Red", "Green", "Blue"):
        Lk.new(cmap.outputs[0], comb.inputs[k])
    Lk.new(comb.outputs[0], cmul.inputs[7])
    Lk.new(cmul.outputs[2], bsdf.inputs["Base Color"])
    # ---- roughness variation on skin (fine noise), cloth stays matte
    tc = N.new("ShaderNodeTexCoord")
    nz = N.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 140.0
    nz.inputs["Detail"].default_value = 3.0
    Lk.new(tc.outputs["Object"], nz.inputs["Vector"])
    rv = N.new("ShaderNodeMapRange")
    rv.inputs["To Min"].default_value = rough_skin - 0.07
    rv.inputs["To Max"].default_value = rough_skin + 0.07
    Lk.new(nz.outputs["Fac"], rv.inputs["Value"])
    rmix.inputs["To Min"].default_value = rough_cloth
    Lk.new(rv.outputs[0], rmix.inputs["To Max"])
    smul.inputs[1].default_value = 0.22
    bsdf.inputs["Subsurface Radius"].default_value = (1.0, 0.42, 0.25)
    bsdf.inputs["Subsurface Scale"].default_value = 0.015
    # ---- fine knit bump on cloth (skin gets almost none)
    nz2 = N.new("ShaderNodeTexNoise")
    nz2.inputs["Scale"].default_value = 900.0
    nz2.inputs["Detail"].default_value = 2.0
    Lk.new(tc.outputs["Object"], nz2.inputs["Vector"])
    bstr = N.new("ShaderNodeMapRange")
    bstr.inputs["To Min"].default_value = 0.06
    bstr.inputs["To Max"].default_value = 0.01
    Lk.new(a_sk.outputs["Fac"], bstr.inputs["Value"])
    bump = N.new("ShaderNodeBump")
    bump.inputs["Distance"].default_value = 0.0015
    Lk.new(bstr.outputs[0], bump.inputs["Strength"])
    Lk.new(nz2.outputs["Fac"], bump.inputs["Height"])
    Lk.new(bump.outputs["Normal"], bsdf.inputs["Normal"])


def _v5_hl(m, bsdf, a_col, mix, mul, emul):
    """5.5: the working (target) muscles turn red and glow with the effort of the frame (the "hl" attribute is set
    per frame), the helping (secondary) muscles warm to orange ("hs"); stronger than the v4 lime tint."""
    nt = m.node_tree
    N, Lk = nt.nodes, nt.links
    mix.inputs[7].default_value = (*RED, 1)
    bsdf.inputs["Emission Color"].default_value = (*RED, 1)
    mul.inputs[1].default_value = 0.85
    emul.inputs[1].default_value = 0.9
    a_hs = N.new("ShaderNodeAttribute"); a_hs.attribute_name = "hs"
    e2 = N.new("ShaderNodeMapRange"); e2.interpolation_type = "SMOOTHSTEP"
    Lk.new(a_hs.outputs["Fac"], e2.inputs["Value"])
    m2 = N.new("ShaderNodeMath"); m2.operation = "MULTIPLY"; m2.inputs[1].default_value = 0.5
    Lk.new(e2.outputs[0], m2.inputs[0])
    mix0 = N.new("ShaderNodeMix"); mix0.data_type = "RGBA"; mix0.blend_type = "MIX"
    Lk.new(m2.outputs[0], mix0.inputs["Factor"])
    Lk.new(a_col.outputs["Color"], mix0.inputs[6])
    mix0.inputs[7].default_value = (*ORANGE, 1)
    Lk.new(mix0.outputs[2], mix.inputs[6])


def flat_material(name, color, rough=0.5, metal=0.0, coat=0.0):
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if coat:
        b.inputs["Coat Weight"].default_value = coat
    return m


# --------------------------------------------------------------------- body
def bun_frame(rig):
    """Rest centre and radii of the female hair bun (head bone space)."""
    hi = rig.bi("head")
    rest = rig.H[hi] + np.array([0, -0.085, 0.115]) * (rig.height / 1.67)
    return hi, rest, np.array([0.052, 0.046, 0.044]) * (rig.height / 1.67)


def bun_points(rig, D, Hp, n=26):
    """Surface samples of the hair bun in a solved pose (the camera fit must
    keep it in the frame: it is a separate object, not part of the skin)."""
    hi, rest, sc = bun_frame(rig)
    k = np.arange(n) + 0.5
    phi = np.arccos(1 - 2 * k / n)
    th = math.pi * (1 + 5 ** 0.5) * k
    s = np.stack([np.cos(th) * np.sin(phi), np.sin(th) * np.sin(phi), np.cos(phi)], 1)
    return Hp[hi] + (D[hi] @ ((s * sc) + (rest - rig.H[hi])).T).T


class BodyObjects:
    def __init__(self, rig, gender):
        self.rig = rig
        self.gender = gender
        pt = paint.load(gender)
        self.pt = pt
        v = rig.verts.astype(np.float32)
        faces = rig.faces
        self.faces = faces
        mat = attr_material("body_mat")
        self.body = self._mesh_obj("body", v, faces, mat)
        self._set_attr(self.body, "paint", pt["col"], color=True)
        self._set_attr(self.body, "skinf", pt["skin"])
        self._set_attr(self.body, "hl", np.zeros(len(v), np.float32))
        self._set_attr(self.body, "hs", np.zeros(len(v), np.float32))
        self._set_attr(self.body, "cav", np.clip(pt["cav"], 0, 1))
        pal = paint.PALETTE[gender] if STYLE != "v4" else paint.PALETTE4[gender]
        # shells
        self.shells = []
        for key, off, colf in (("shoe", 0.007, None), ("hair", 0.0055 if gender == "m" else 0.009, pal["hair"])):
            mask = pt[key]
            fsel = faces[mask[faces].all(axis=1)]
            used = np.unique(fsel)
            remap = -np.ones(len(v), np.int64)
            remap[used] = np.arange(len(used))
            sm = attr_material(f"{key}_mat", rough_cloth=0.55 if key == "shoe" else 0.85, sss=0.0)
            ob = self._mesh_obj(key, v[used], remap[fsel], sm)
            if key == "shoe":
                c = np.tile(pal["shoe"], (len(used), 1))
                sole = rig.verts[used, 2] < 0.022
                c[sole] = pal["sole"]
                if STYLE == "v4":       # a darker mid-sole band and a side stripe read as a real trainer
                    zz = rig.verts[used, 2]
                    c[(zz >= 0.022) & (zz < 0.034)] = pal["accent"]
            else:
                c = np.tile(colf, (len(used), 1))
            self._set_attr(ob, "paint", c.astype(np.float32), color=True)
            self._set_attr(ob, "skinf", np.zeros(len(used), np.float32))
            self._set_attr(ob, "hl", np.zeros(len(used), np.float32))
            self._set_attr(ob, "hs", np.zeros(len(used), np.float32))
            self._set_attr(ob, "cav", np.zeros(len(used), np.float32))
            self.shells.append((ob, used, off))
        self.bun = None
        if gender == "f":
            bpy.ops.mesh.primitive_uv_sphere_add(radius=1, segments=24, ring_count=12)
            b = bpy.context.active_object
            b.name = "bun"
            bpy.ops.object.shade_smooth()
            b.data.materials.append(flat_material("hair_flat", pal["hair"], rough=0.85))
            self.bun = b
            _, self.bun_rest, self.bun_scale = bun_frame(rig)

    def _mesh_obj(self, name, v, faces, mat):
        me = bpy.data.meshes.new(name)
        me.from_pydata(v.tolist(), [], faces.tolist())
        me.update()
        me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
        ob = bpy.data.objects.new(name, me)
        bpy.context.scene.collection.objects.link(ob)
        me.materials.append(mat)
        mod = ob.modifiers.new("sub", "SUBSURF")
        mod.levels = 0
        mod.render_levels = 1
        return ob

    @staticmethod
    def _set_attr(ob, name, data, color=False):
        me = ob.data
        if name in me.attributes:
            me.attributes.remove(me.attributes[name])
        if color:
            a = me.attributes.new(name, "FLOAT_COLOR", "POINT")
            rgba = np.ones((len(data), 4), np.float32)
            rgba[:, :3] = data
            a.data.foreach_set("color", rgba.ravel())
        else:
            a = me.attributes.new(name, "FLOAT", "POINT")
            a.data.foreach_set("value", data.astype(np.float32).ravel())

    def set_highlight(self, keys, weights=None, k=1.0):
        """k: 5.5 effort of this frame (0..1): scales the red of the target muscles and the orange of the helpers."""
        hl = np.zeros(len(self.rig.verts), np.float32)
        hs = np.zeros(len(self.rig.verts), np.float32)
        for i, key in enumerate(keys):
            wgt = 1.0 if weights is None else weights[i]
            if HL5 and wgt < 0.99:
                hs = np.maximum(hs, self.pt["muscles"][key])
            else:
                hl = np.maximum(hl, wgt * self.pt["muscles"][key])
        if HL5:
            hs = np.where(hl > 0.25, 0.0, hs)
        self.body.data.attributes["hl"].data.foreach_set("value", (hl * k).astype(np.float32))
        self.body.data.attributes["hs"].data.foreach_set("value", (hs * k).astype(np.float32))

    def show(self, on=True):
        for o in [self.body] + [ob for ob, _, _ in self.shells] + ([self.bun] if self.bun is not None else []):
            o.hide_render = not on

    def update(self, verts, D=None, Hp=None):
        me = self.body.data
        me.vertices.foreach_set("co", verts.astype(np.float32).ravel())
        me.update()
        nrm = paint.vertex_normals(verts.astype(np.float64), self.faces)
        for ob, used, off in self.shells:
            vv = verts[used] + nrm[used] * off
            ob.data.vertices.foreach_set("co", vv.astype(np.float32).ravel())
            ob.data.update()
        if self.bun is not None and D is not None:
            hi = self.rig.bi("head")
            p = Hp[hi] + D[hi] @ (self.bun_rest - self.rig.H[hi])
            from mathutils import Matrix
            M = np.eye(4)
            M[:3, :3] = D[hi] @ np.diag(self.bun_scale)
            M[:3, 3] = p
            self.bun.matrix_world = Matrix(M.tolist())


def render_png(path):
    sc = bpy.context.scene
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
