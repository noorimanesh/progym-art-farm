"""musclemap.py OUT [m,f]: 5.5 realistic muscle map from the same 3D body as the exercise art.

For each gender and view (front, back) it renders
  OUT/<g>-<view>.webp           the body as a light clay figure (no clothes colours, no hair or shoes), 520x1040
  OUT/<g>-<view>-<key>.webp     a grey mask (white = that muscle, soft edges) for each of the 22 body-map keys
The site colours each muscle by drawing its mask over the figure (CSS mask), so heat, recovery and focus maps show on a
real body. Keys follow the site's body map (assets/body/bodymap.json); "chest" joins the mid and lower chest, and
"tibialis" has no area on this body (left out).
Run with the venv python:  venv/bin/python tools/musclemap.py out_map m,f
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import numpy as np  # noqa: E402

SITE_KEYS = {
    "neck": ["neck"], "traps": ["traps"], "front_delt": ["front_delts"], "side_delt": ["side_delts"], "rear_delt": ["rear_delts"],
    "upper_chest": ["upper_chest"], "chest": ["mid_chest", "lower_chest"], "lats": ["lats"], "upper_back": ["upper_back"],
    "lower_back": ["lower_back"], "biceps": ["biceps"], "triceps": ["triceps"], "forearms": ["forearms"], "abs": ["abs"],
    "obliques": ["obliques"], "glutes": ["glutes"], "abductors": ["abductors"], "adductors": ["adductors"], "quads": ["quads"],
    "hamstrings": ["hamstrings"], "calves": ["calves"],
}
VIEWS = {"front": 0.0, "back": 180.0}
W, H = 520, 1040


def main():
    out = sys.argv[1]
    genders = (sys.argv[2] if len(sys.argv) > 2 else "m,f").split(",")
    os.makedirs(out, exist_ok=True)
    import bpy
    from PIL import Image
    from artgen import scene, paint
    from artgen.poses import Ctx
    from artgen.fam import arm_fk
    from artgen.render import fit_camera
    paint.set_style("v4")
    scene.STYLE = "v4"
    for g in genders:
        scene.init(threads=int(os.environ.get("THREADS", "2")), samples=16, res=(W, H))
        sc = bpy.context.scene
        bpy.data.objects["floor"].hide_render = True
        c = Ctx(g)
        fr = c.stand(c.feet(w=c.hw * 1.25, toe=8), arms=arm_fk((0.42, 0.04, -1), elbow=10, thumb="fwd", curl=0.25),
                     pel=(1, 0, 0), balance=None)
        p = c.run(fr)
        body = scene.BodyObjects(c.r, g)
        body.update(p.verts, p.D, p.Hp)
        # clay figure: one light neutral colour everywhere, matte; hair and shoes hidden
        n = len(c.r.verts)
        body._set_attr(body.body, "paint", np.tile(np.array([0.62, 0.6, 0.58], np.float32), (n, 1)), color=True)
        body._set_attr(body.body, "skinf", np.ones(n, np.float32) * 0.6)
        for ob, _, _ in body.shells:
            ob.hide_render = True
        if body.bun is not None:
            body.bun.hide_render = True
        clay = body.body.data.materials[0]
        # mask material: emission of the "hl" attribute, nothing else
        mm = bpy.data.materials.new("mask")
        mm.use_nodes = True
        N, Lk = mm.node_tree.nodes, mm.node_tree.links
        for nd in list(N):
            N.remove(nd)
        at = N.new("ShaderNodeAttribute"); at.attribute_name = "hl"
        em = N.new("ShaderNodeEmission")
        Lk.new(at.outputs["Fac"], em.inputs["Strength"])
        em.inputs["Color"].default_value = (1, 1, 1, 1)
        mo = N.new("ShaderNodeOutputMaterial")
        Lk.new(em.outputs[0], mo.inputs["Surface"])
        pts = p.verts[::3]
        for view, az in VIEWS.items():
            cam, tgt = fit_camera(pts, az, 3.0, lens=85, aspect=W / H, margin=0.06, margin_v=0.04)
            scene.set_camera(cam, tgt, 85)
            # the figure
            body.body.data.materials[0] = clay
            body.set_highlight([], None)
            sc.cycles.samples = 16
            sc.cycles.use_denoising = True
            sc.view_settings.view_transform = "AgX"
            for w in bpy.data.worlds:
                w.node_tree.nodes["Background"].inputs[1].default_value = 0.16
            f = os.path.join(out, f"_{g}-{view}.png")
            scene.render_png(f)
            Image.open(f).save(os.path.join(out, f"{g}-{view}.webp"), "WEBP", quality=88, method=6)
            os.remove(f)
            # the masks (flat emission, no light, no noise)
            body.body.data.materials[0] = mm
            sc.cycles.samples = 2
            sc.cycles.use_denoising = False
            sc.view_settings.view_transform = "Standard"
            for w in bpy.data.worlds:
                w.node_tree.nodes["Background"].inputs[1].default_value = 0.0
            for key, parts in SITE_KEYS.items():
                body.set_highlight(parts, [1.0] * len(parts))
                f = os.path.join(out, f"_{g}-{view}-{key}.png")
                scene.render_png(f)
                im = Image.open(f).convert("RGBA")
                a = np.asarray(im)
                m = (a[:, :, 0].astype(np.float32) * (a[:, :, 3] / 255.0)).clip(0, 255).astype(np.uint8)
                os.remove(f)
                if m.max() < 40:
                    continue          # not seen from this side
                Image.fromarray(m, "L").save(os.path.join(out, f"{g}-{view}-{key}.webp"), "WEBP", quality=80, method=6)
            print(g, view, "done", flush=True)


if __name__ == "__main__":
    main()
