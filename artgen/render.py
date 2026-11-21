"""Render worker: one gender, a slice of the work list.

  python -m artgen.render --csv data/worklist.csv --gender m --out out/m \
         --start 0 --end 50 [--threads 1] [--samples 8] [--keep-frames]

Writes <slug>.webp / <slug>.thumb.jpg (male) or <slug>.f.webp /
<slug>.f.thumb.jpg (female), plus qa_<gender>_<start>.csv with contact checks.
Rows whose render key (template, equipment, muscles) was already rendered
in this output folder are copied instead of re-rendered.
"""
import argparse
import csv
import hashlib
import json
import math
import os
import shutil
import sys
import time

import numpy as np

PHASES = [0.0, 0.156, 0.5, 0.844, 1.0]
SEQ = [0, 0, 1, 2, 3, 4, 4, 4, 3, 2, 1, 0]
FRAME_MS = 167


def ease(t):
    return t * t * (3 - 2 * t)


def encode(frames_rgba, out_webp, out_thumb, max_kb=45):
    from PIL import Image
    from .scene import BG
    bg = tuple(int(round(c * 255)) for c in BG)
    rgb = []
    for im in frames_rgba:
        base = Image.new("RGBA", im.size, bg + (255,))
        base.alpha_composite(im)
        rgb.append(base.convert("RGB"))
    seq = []
    for j, i in enumerate(SEQ):
        # keep all 12 frames: libwebp merges identical consecutive frames, so
        # every frame gets its own faint 4-pixel code in the top-left corner
        im = rgb[i].copy()
        px = im.load()
        for k in range(4):
            r_, g_, b_ = px[k, 0]
            px[k, 0] = (max(r_ - (10 if (j + 1) >> k & 1 else 0), 0), g_, b_)
        seq.append(im)
    q = 82
    while True:
        seq[0].save(out_webp, save_all=True, append_images=seq[1:], duration=FRAME_MS, loop=0,
                    quality=q, method=6)
        if os.path.getsize(out_webp) <= max_kb * 1024 or q <= 20:
            break
        q -= 6
    th = rgb[-1].resize((160, 107), Image.LANCZOS)
    th.save(out_thumb, quality=84, optimize=True, progressive=True)
    return q, os.path.getsize(out_webp)


def fit_camera(points, az, el, lens=55, aspect=1.5, margin=0.07, margin_v=None):
    """Camera position / target so all points fit (az from +Y toward +X).
    margin: free share of the half frame across the width (and the height,
    unless margin_v sets it apart)."""
    mv = margin if margin_v is None else margin_v
    a, e = math.radians(az), math.radians(el)
    d = np.array([math.sin(a) * math.cos(e), math.cos(a) * math.cos(e), math.sin(e)])  # toward camera
    right = np.cross(-d, [0, 0, 1])
    right /= np.linalg.norm(right)
    up = np.cross(right, -d)
    tan_h = 18 / lens
    tan_v = tan_h / aspect
    tgt = points.mean(0)
    for _ in range(4):
        rel = points - tgt
        r_, u_, z_ = rel @ right, rel @ up, rel @ d
        need = np.maximum(np.abs(r_) / (tan_h * (1 - margin)), np.abs(u_) / (tan_v * (1 - mv))) + z_
        dist = need.max()
        depth = dist - z_
        pr, pu = r_ / depth, u_ / depth
        cr, cu = 0.5 * (pr.max() + pr.min()), 0.5 * (pu.max() + pu.min())
        tgt = tgt + right * cr * dist + up * cu * dist
    rel = points - tgt
    z_ = rel @ d
    need = np.maximum(np.abs(rel @ right) / (tan_h * (1 - margin)), np.abs(rel @ up) / (tan_v * (1 - mv))) + z_
    dist = need.max()
    return tgt + d * dist, tgt


def render_key(row, gender):
    k = "|".join([gender, row["template"], row.get("name_en", ""), row.get("equipment", ""), row.get("muscles", ""),
                  row.get("muscles2", ""), row.get("variant", ""), row.get("view", "")])
    return hashlib.sha1(k.encode()).hexdigest()[:16]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True)
    ap.add_argument("--gender", required=True, choices=["m", "f"])
    ap.add_argument("--out", required=True)
    ap.add_argument("--start", type=int, default=0)
    ap.add_argument("--end", type=int, default=10 ** 9)
    ap.add_argument("--only", default="")
    ap.add_argument("--threads", type=int, default=1)
    ap.add_argument("--samples", type=int, default=10)
    ap.add_argument("--keep-frames", action="store_true")
    ap.add_argument("--skip-existing", action="store_true")
    ap.add_argument("--no-dedupe", action="store_true", help="always render (needed when re-rendering)")
    ap.add_argument("--debug-phases", default="", help="e.g. 0,0.5,1: render only these phases to a sheet")
    ap.add_argument("--res", default="480x320")
    args = ap.parse_args()

    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import bpy
    from PIL import Image
    from . import scene, equipment as EQ, templates, muscles, qa
    from .poses import Ctx

    rows = list(csv.DictReader(open(args.csv, encoding="utf-8")))
    rows = rows[args.start:args.end]
    if args.only:
        keep = set(args.only.split(","))
        rows = [r for r in rows if r["slug"] in keep or r["template"] in keep]
    os.makedirs(args.out, exist_ok=True)
    frames_dir = os.path.join(args.out, "_frames")
    os.makedirs(frames_dir, exist_ok=True)
    suffix = "" if args.gender == "m" else ".f"
    keyfile = os.path.join(args.out, f"_keys{suffix}.json")
    keys = json.load(open(keyfile)) if os.path.exists(keyfile) else {}

    res = tuple(int(v) for v in args.res.split("x"))
    scene.init(threads=args.threads, samples=args.samples, res=res)
    global PHASES
    debug = bool(args.debug_phases)
    if debug:
        PHASES = [float(v) for v in args.debug_phases.split(",")]
        sheet_rows = []
    ctx = Ctx(args.gender)
    body = scene.BodyObjects(ctx.r, args.gender)
    qa_path = os.path.join(args.out, f"qa{suffix}_{args.start}.csv")
    qf = open(qa_path, "a", newline="", encoding="utf-8")
    qw = csv.writer(qf)
    t_all = time.time()
    n_done = 0
    for row in rows:
        slug = row["slug"]
        webp = os.path.join(args.out, f"{slug}{suffix}.webp")
        thumb = os.path.join(args.out, f"{slug}{suffix}.thumb.jpg")
        if args.skip_existing and os.path.exists(webp) and os.path.exists(thumb):
            continue
        rk = render_key(row, args.gender)
        if not args.no_dedupe and rk in keys and keys[rk] != slug and os.path.exists(os.path.join(args.out, keys[rk] + suffix + ".webp")) and not args.keep_frames:
            src = keys[rk]
            shutil.copyfile(os.path.join(args.out, src + suffix + ".webp"), webp)
            shutil.copyfile(os.path.join(args.out, src + suffix + ".thumb.jpg"), thumb)
            qw.writerow([slug, row["template"], "copy:" + src, "", "", ""])
            continue
        t0 = time.time()
        tpl = templates.get(row["template"])
        poses = []
        for ph in PHASES:
            poses.append(tpl.pose(ctx, ease(ph) if not tpl.linear else ph, row))
        hl_keys, hl_w = muscles.highlight(row)
        body.set_highlight(hl_keys, hl_w)
        # equipment objects
        made = {}
        pts = [p.verts[::7] for p in poses]
        for p in poses:
            for e in p.equip:
                pts.append(equip_points(e))
        pts = np.concatenate([q for q in pts if len(q)])
        pts = pts[pts[:, 2] < max(p.verts[:, 2].max() for p in poses) + 0.35]
        pts = np.concatenate([pts, pts[:1] * [1, 1, 0]])
        view = templates.VIEWS.get(row.get("view") or "", None) or tpl.view_angles()
        cam, tgt = fit_camera(pts, *view, lens=tpl.lens)
        scene.set_camera(cam, tgt, tpl.lens)
        set_border(bpy, pts)
        fl = bpy.data.objects["floor"]
        fl.location = (float(pts[:, 0].mean()), float(pts[:, 1].mean()), 0.0)
        imgs = []
        for i, p in enumerate(poses):
            body.update(p.verts, p.D, p.Hp)
            seen = set()
            for e in p.equip:
                seen.add(e["id"])
                place_equipment(e, made, EQ)
            for eid, ob in made.items():
                hide = eid not in seen
                for o in [ob] + list(ob.children):
                    o.hide_render = hide
            fp = os.path.join(frames_dir, f"{slug}{suffix}_{i}.png")
            scene.render_png(fp)
            imgs.append(Image.open(fp).convert("RGBA"))
        if debug:
            sheet_rows.append((slug + " [" + row["template"] + "] " + " ".join(qa.check(ctx, poses, tpl)), imgs))
            for ob in made.values():
                for o in list(ob.children) + [ob]:
                    bpy.data.objects.remove(o, do_unlink=True)
            print(slug, flush=True)
            continue
        q, size = encode(imgs, webp, thumb)
        if not args.keep_frames:
            for i in range(len(PHASES)):
                try:
                    os.remove(os.path.join(frames_dir, f"{slug}{suffix}_{i}.png"))
                except OSError:
                    pass
        for ob in made.values():
            for o in list(ob.children) + [ob]:
                bpy.data.objects.remove(o, do_unlink=True)
        for m in list(bpy.data.meshes):
            if m.users == 0:
                bpy.data.meshes.remove(m)
        issues = qa.check(ctx, poses, tpl)
        dt = time.time() - t0
        qw.writerow([slug, row["template"], f"{dt:.1f}", q, size, ";".join(issues)])
        qf.flush()
        keys[rk] = slug
        json.dump(keys, open(keyfile, "w"))
        n_done += 1
        print(f"[{args.gender}] {slug} {row['template']} {dt:.1f}s q={q} {size // 1024}KB {';'.join(issues)}", flush=True)
    qf.close()
    if debug:
        debug_sheet(sheet_rows, os.path.join(args.out, f"debug{suffix}_{args.start}.png"))
    print(f"done {n_done} in {time.time() - t_all:.0f}s", flush=True)


def debug_sheet(rows, dest, per=40):
    from PIL import Image, ImageDraw
    from .scene import BG
    bg = tuple(int(round(c * 255)) for c in BG)
    for k in range(0, len(rows), per):
        chunk = rows[k:k + per]
        w, h = chunk[0][1][0].size
        n = max(len(r[1]) for r in chunk)
        cols = 2
        img = Image.new("RGB", (cols * n * w, ((len(chunk) + cols - 1) // cols) * (h + 12)), (255, 255, 255))
        d = ImageDraw.Draw(img)
        for i, (label, ims) in enumerate(chunk):
            x0 = (i % cols) * n * w
            y0 = (i // cols) * (h + 12)
            d.text((x0 + 3, y0), label[:90], fill=(0, 0, 0))
            for j, im in enumerate(ims):
                b = Image.new("RGBA", im.size, bg + (255,))
                b.alpha_composite(im)
                img.paste(b.convert("RGB"), (x0 + j * w, y0 + 12))
        img.save(dest.replace(".png", f"_{k // per}.png"))


def set_border(bpy, pts):
    """Render only the region around the subject (plus room for its floor
    shadow); the rest of the frame is plain background anyway."""
    from bpy_extras.object_utils import world_to_camera_view
    from mathutils import Vector
    sc = bpy.context.scene
    cam = sc.camera
    bpy.context.view_layer.update()
    sel = pts[:: max(1, len(pts) // 600)]
    shadow = sel.copy()
    shadow[:, 2] = 0.0
    uv = np.array([tuple(world_to_camera_view(sc, cam, Vector(p)))[:2] for p in np.concatenate([sel, shadow])])
    x0, y0 = uv.min(0)
    x1, y1 = uv.max(0)
    sc.render.use_border = True
    sc.render.use_crop_to_border = False
    sc.render.border_min_x = float(max(0.0, x0 - 0.1))
    sc.render.border_max_x = float(min(1.0, x1 + 0.1))
    sc.render.border_min_y = float(max(0.0, y0 - 0.08))
    sc.render.border_max_y = float(min(1.0, y1 + 0.05))


def equip_points(e):
    from . import equipment as EQ
    if e["kind"] == "_seg":
        return np.array([e["p0"], e["p1"]])
    g = EQ.KINDS[e["kind"]](**e.get("shape", {}))
    v = np.concatenate([np.concatenate(vs) for vs, fs, n in g.parts.values()])
    lo, hi = v.min(0), v.max(0)
    box = np.array([[x, y, z] for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])])
    M = e["M"]
    return box @ M[:3, :3].T + M[:3, 3]


def place_equipment(e, made, EQ):
    from mathutils import Matrix
    if e["kind"] == "_seg":
        mat = getattr(EQ, e.get("mat", "rope").upper(), EQ.ROPE)
        ob = EQ.cylinder_between("seg_" + e["id"], e["p0"], e["p1"], e["r"], mat)
        made.setdefault(e["id"], ob)
        return
    ob = made.get(e["id"])
    if ob is None:
        ob = EQ.build(e["kind"], "eq_" + e["id"], **e.get("shape", {}))
        made[e["id"]] = ob
    ob.matrix_world = Matrix(e["M"].tolist())


if __name__ == "__main__":
    main()
