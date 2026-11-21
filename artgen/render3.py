"""v3 render worker: one gender, a slice of the v3 move list.

  python -m artgen.render3 --moves data/v3/moves.csv --gender m --out out_v3 \
         [--only key1,key2] [--start 0 --end 50] [--threads 2] [--samples 8]

Per move it solves the unique phases of the loop (motion.timeline) in order
with warm starts, fits one camera over the whole loop, renders each unique
pose once, encodes a 24-frame animated WebP with per-frame durations, a
160x107 JPEG thumbnail of the most telling pose, and writes
  <out>/<key><sfx>.webp, <key><sfx>.thumb.webp (480x320 still of the most telling pose)
  <out>/_sheet/<key><sfx>.<i>.png     start / middle / end frames (contact sheets)
  <out>/_qa/<key><sfx>.json            automatic checks (qa3)
"""
import argparse
import csv
import json
import math
import os
import sys
import time

import numpy as np

MAX_KB = 90


ENC = dict(max_kb=MAX_KB, target_kb=MAX_KB, q0=86, q_floor=30, sharpen=False, thumb_size=None)


def encode(imgs, frames, out_webp, out_thumb, thumb_idx, max_kb=None):
    """Animated WebP (per-frame durations) + still WebP thumbnail, both with the
    corner mark and copyright metadata.  v3: <= 90 KB at 480x320.  v4: quality
    lowered only until ~target_kb (120), never above max_kb (220), frames lightly
    sharpened after the denoiser."""
    from PIL import Image, ImageFilter
    from .scene import background
    from . import mark
    max_kb = ENC["max_kb"] if max_kb is None else max_kb
    used = [im for im in imgs if im is not None]
    au = np.zeros((used[0].size[1], used[0].size[0]), np.float32)
    for im in used:
        au = np.maximum(au, np.asarray(im)[:, :, 3] / 255.0)
    ov = mark.make_overlay(used[0].size, au)
    def compose(sharpen):
        out = []
        for im in imgs:
            if im is None:
                out.append(None)
                continue
            base = background(im.size)
            base.alpha_composite(im)
            if sharpen:          # crisp edges after the denoiser (the mark is added after, unsharpened)
                base = base.filter(ImageFilter.UnsharpMask(radius=0.9, percent=45, threshold=2))
            base.alpha_composite(ov)
            out.append(base.convert("RGB"))
        return out
    rgb = compose(ENC["sharpen"])
    def build_seq(src):
        seq, durs = [], []
        for j, (u, ms) in enumerate(frames):
            im = src[u].copy()
            # libwebp merges identical consecutive frames; a faint per-frame code in
            # the top-left corner keeps the frame count stable for players
            px = im.load()
            for k in range(5):
                r_, g_, b_ = px[k, 0]
                px[k, 0] = (max(r_ - (8 if (j + 1) >> k & 1 else 0), 0), g_, b_)
            seq.append(im)
            durs.append(int(ms))
        return seq, durs
    seq, durs = build_seq(rgb)
    meta = dict(exif=mark.exif_bytes(), xmp=mark.xmp_bytes())
    q = ENC["q0"]
    soft = False
    while True:          # WebP method 5: as fast as 4, a little smaller (method 6 is 25x slower)
        seq[0].save(out_webp, save_all=True, append_images=seq[1:], duration=durs, loop=0,
                    quality=q, method=5, **meta)
        size = os.path.getsize(out_webp)
        if size <= ENC["target_kb"] * 1024 or q <= 30:
            break
        if q - 3 < ENC["q_floor"] and size <= max_kb * 1024:
            break                  # keep the quality floor while within the hard maximum
        if q - 3 < ENC["q_floor"] and not soft and ENC["sharpen"]:
            # over the hard maximum at the quality floor: drop the sharpening (its
            # extra fine detail costs ~10-15 % of the file) and start again before
            # giving up quality - below the floor the floor shadows turn blocky
            rgb = compose(False)
            seq, durs = build_seq(rgb)
            soft = True
            q = ENC["q0"]
            continue
        q -= 3
    th = rgb[thumb_idx]
    if ENC["thumb_size"] and th.size != tuple(ENC["thumb_size"]):
        th = th.resize(tuple(ENC["thumb_size"]), Image.LANCZOS)
    th.save(out_thumb, "WEBP", quality=82, method=6, **meta)
    return q, os.path.getsize(out_webp), rgb


def effort(kind, ph):
    """5.5: how hard the target muscles work in a frame (0.3..1): rises toward the end pose of a rep (the
    contracted / loaded position), steady in holds, pulsing in cycles."""
    from .motion import ease
    ph = min(max(float(ph), 0.0), 1.0)
    if kind == "hold":
        return 1.0
    if kind == "cycle":
        return 0.7 + 0.3 * math.sin(math.pi * ph * 2) ** 2
    return 0.3 + 0.7 * ease(ph)


def encode_video(imgs, frames, out_mp4, out_thumb, thumb_idx, fps=24, crf=24):
    """5.5: H.264 MP4 at a constant 24 fps (each unique frame repeated for its duration), with the corner mark,
    no audio, fast start; plus the still WebP thumbnail. Returns (crf, bytes, frames with the mark)."""
    import shutil
    import subprocess
    import tempfile
    from PIL import Image, ImageFilter
    from .scene import background
    from . import mark
    used = [im for im in imgs if im is not None]
    au = np.zeros((used[0].size[1], used[0].size[0]), np.float32)
    for im in used:
        au = np.maximum(au, np.asarray(im)[:, :, 3] / 255.0)
    ov = mark.make_overlay(used[0].size, au)
    rgb = []
    for im in imgs:
        if im is None:
            rgb.append(None)
            continue
        b = background(im.size)
        b.alpha_composite(im)
        b = b.filter(ImageFilter.UnsharpMask(radius=0.9, percent=40, threshold=2))
        b.alpha_composite(ov)
        rgb.append(b.convert("RGB"))
    tmp = tempfile.mkdtemp(prefix="v5enc")
    try:
        n, carry = 0, 0.0
        for u, ms in frames:
            carry += ms * fps / 1000.0
            reps = int(round(carry))
            carry -= reps
            for _ in range(max(0, reps)):
                rgb[u].save(os.path.join(tmp, f"{n:05d}.png"), compress_level=1)
                n += 1
        ff = os.environ.get("FFMPEG", "ffmpeg")
        cmd = [ff, "-v", "error", "-y", "-framerate", str(fps), "-i", os.path.join(tmp, "%05d.png"), "-c:v", "libx264",
               "-preset", "slow", "-crf", str(crf), "-pix_fmt", "yuv420p", "-profile:v", "high", "-movflags", "+faststart",
               "-metadata", "copyright=ProGym", "-an", out_mp4]
        subprocess.run(cmd, check=True)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    if out_thumb:
        rgb[thumb_idx].save(out_thumb, "WEBP", quality=84, method=6, exif=mark.exif_bytes(), xmp=mark.xmp_bytes())
    return crf, os.path.getsize(out_mp4), rgb


def feather(im, rs, px=28):
    """Fade the alpha out toward the edges of the rendered border region so
    the faint floor shading inside it does not show as a rectangle."""
    if not rs.use_border:
        return im
    W, H = im.size
    x0, x1 = rs.border_min_x * W, rs.border_max_x * W
    y0, y1 = (1 - rs.border_max_y) * H, (1 - rs.border_min_y) * H
    xs = np.arange(W) + 0.5
    ys = np.arange(H) + 0.5
    fx = np.clip(np.minimum(xs - x0, x1 - xs) / px, 0, 1)
    fy = np.clip(np.minimum(ys - y0, y1 - ys) / px, 0, 1)
    if x0 <= 0.5:
        fx = np.where(xs < W / 2, 1.0, fx)
    if x1 >= W - 0.5:
        fx = np.where(xs > W / 2, 1.0, fx)
    if y0 <= 0.5:
        fy = np.where(ys < H / 2, 1.0, fy)
    if y1 >= H - 0.5:
        fy = np.where(ys > H / 2, 1.0, fy)
    m = np.outer(fy, fx)
    m = m * m * (3 - 2 * m)
    a = np.asarray(im, dtype=np.float32)
    al = a[:, :, 3] / 255.0
    w = np.clip((0.75 - al) / 0.35, 0, 1)      # only faint (shadow) pixels fade, never the subject
    a[:, :, 3] *= 1 - w * (1 - m)
    from PIL import Image
    return Image.fromarray(a.clip(0, 255).astype(np.uint8), "RGBA")


def _border_points(poses, pts):
    """Everything that may show in the frame (all equipment too), so the
    render region never cuts an object that is inside the picture."""
    from .render import equip_points
    extra = []
    for p in poses[:: max(1, len(poses) // 4)]:
        for e in p.equip:
            if e["kind"] == "_seg":
                extra.append(np.array([e["p0"], e["p1"]]))
            else:
                extra.append(equip_points(e))
    return np.concatenate([pts] + extra) if extra else pts


def set_border_np(bpy, pts, cam, tgt, lens, aspect=1.5):
    """Render region around every point (and its floor shadow), projected
    exactly (all points, no subsampling, so implement extremes stay in)."""
    d = (np.asarray(cam) - np.asarray(tgt))
    d = d / np.linalg.norm(d)
    right = np.cross(-d, [0, 0, 1.0])
    right /= np.linalg.norm(right)
    up = np.cross(right, -d)
    allp = np.concatenate([pts, pts * np.array([1, 1, 0])])
    rel = allp - cam
    z = rel @ (-d)
    th = 18.0 / lens
    u = (rel @ right) / z / th          # -1..1 across the width
    v = (rel @ up) / z / (th / aspect)
    x0, x1 = (u.min() + 1) / 2, (u.max() + 1) / 2
    y0, y1 = (v.min() + 1) / 2, (v.max() + 1) / 2
    sc = bpy.context.scene
    sc.render.use_border = True
    sc.render.use_crop_to_border = False
    sc.render.border_min_x = float(max(0.0, x0 - 0.1))
    sc.render.border_max_x = float(min(1.0, x1 + 0.1))
    sc.render.border_min_y = float(max(0.0, y0 - 0.08))
    sc.render.border_max_y = float(min(1.0, y1 + 0.06))


def camera_points(poses, rig=None, gender="m", fit_equip=()):
    """The camera is fitted to the athlete over the whole loop (with the hair
    bun) plus what the hands hold and moving parts attached to the body (bar,
    dumbbells, sled, handles).  Benches, machines, towers, straps, cables and
    bands are not part of the fit: they may run out of the frame, the athlete
    stays large, unless the row names them in params "fit_equip" (ids or
    kinds), for a support the picture must show whole (feet on a bench).
    Equipment marked "fit" (a hanging athlete's bar station) is fitted whole."""
    from .render import equip_points
    body = [p.verts[::2] for p in poses]
    if gender == "f" and rig is not None:
        from .scene import bun_points
        body += [bun_points(rig, p.D, p.Hp) for p in poses if p.D is not None]
    body = np.concatenate(body)
    held = []
    for p in poses:
        for e in p.equip:
            if e.get("fit") == "far" and e["kind"] != "_seg":     # only the far end (a landmine sleeve with its plate)
                q = equip_points(e)
                r = np.linalg.norm(q - np.asarray(e["M"])[:3, 3], axis=1)
                held.append(q[r > 0.75 * r.max()])
                continue
            if e["kind"] in ("_seg", "landmine_bar"):    # the landmine sleeve is in the hands; its pivot may leave the frame
                continue
            if e.get("hand") or e.get("bone") or e.get("dyn") or e.get("fit") or e["id"] in fit_equip or e["kind"] in fit_equip:
                held.append(equip_points(e))
    return np.concatenate([body] + held) if held else body


def project(pts, cam, tgt, lens, aspect=1.5):
    d = (np.asarray(cam) - np.asarray(tgt))
    d = d / np.linalg.norm(d)
    right = np.cross(-d, [0, 0, 1.0])
    right /= np.linalg.norm(right)
    up = np.cross(right, -d)
    rel = pts - cam
    z = rel @ (-d)
    th = 18.0 / lens
    return (rel @ right) / z / th, (rel @ up) / z / (th / aspect)


def pose_hash(poses, cam=None):
    """Fingerprint of a solved loop (body at 2 mm, implements at 2 mm, camera):
    a later run with changed code re-renders only moves whose loop changed."""
    import hashlib
    h = hashlib.sha1()
    for p in poses:
        h.update(np.round(p.verts[::11] / 0.002).astype(np.int32).tobytes())
        for e in p.equip:
            if e["kind"] == "_seg":
                h.update(np.round(np.concatenate([e["p0"], e["p1"]]) / 0.002).astype(np.int32).tobytes())
            else:
                h.update(e["kind"].encode())
                h.update(np.round(np.asarray(e["M"])[:3, :] / 0.002).astype(np.int32).tobytes())
    if cam is not None:
        h.update(np.round(np.asarray(cam) / 0.005).astype(np.int32).tobytes())
    return h.hexdigest()[:16]


def athlete_fraction(poses, cam, tgt, lens):
    """Largest share of the frame height or width the athlete's bounding box
    (over the whole loop) covers."""
    B = np.concatenate([p.verts[::3] for p in poses])
    u, v = project(B, cam, tgt, lens)
    return float(max((v.max() - v.min()) / 2.0, (u.max() - u.min()) / 2.0))


FIT_MARGIN = 0.05      # share of the half frame kept free above / below the athlete ...
FIT_MARGIN_H = 0.08    # ... and left / right (long floor bodies reached the side edges)
DEPTH_TRIGGER = 1.52   # farthest / nearest body depth above which the near end balloons ...
DEPTH_TARGET = 1.42    # ... and the camera backs off (longer lens) until about this
LENS_MAX = 135.0
DEEP_MARGIN = 0.08     # those deep views also keep a wider free border (near hands / feet at the edge)


def depth_ratio(pts, cam, tgt):
    d = np.asarray(cam) - np.asarray(tgt)
    d = d / np.linalg.norm(d)
    z = (pts - cam) @ (-d)
    return float(z.max() / max(z.min(), 1e-3))


def fit_view(poses, row, tpl, rig=None, gender="m"):
    """Camera over the whole loop.  When the body is deep along the view (lying
    toward the camera, legs reaching at it) a close camera makes the near end
    (head or feet) huge and soft: the camera then backs off with a longer lens
    (same frame fill) until the body's depth ratio is about DEPTH_TARGET.
    Views with a body depth ratio up to DEPTH_TRIGGER keep the row's /
    template's lens exactly."""
    from .render import fit_camera
    pts = camera_points(poses, rig, gender, tuple((row.get("_p") or {}).get("fit_equip") or ()))
    body = np.concatenate([p.verts[::9] for p in poses])
    view = row["_view"] or tpl.view_angles()
    lens = float(row.get("lens") or tpl.lens)
    m_row = float((row.get("_p") or {}).get("fit_margin") or 0.0)      # a row may ask for a wider free border
    cam, tgt = fit_camera(pts, *view, lens=lens, margin=max(FIT_MARGIN_H, m_row), margin_v=max(FIT_MARGIN, m_row))
    if depth_ratio(body, cam, tgt) > DEPTH_TRIGGER:
        for _ in range(16):
            if depth_ratio(body, cam, tgt) <= DEPTH_TARGET or lens >= LENS_MAX:
                break
            lens = min(LENS_MAX, lens * 1.08)
            cam, tgt = fit_camera(pts, *view, lens=lens, margin=max(DEEP_MARGIN, FIT_MARGIN_H, m_row),
                                  margin_v=max(DEEP_MARGIN, m_row))
    return pts, cam, tgt, lens


MAT_LEN, MAT_W = 1.85, 0.62


def align_mats(poses, min_deg=25.0):
    """Exercise mats are laid out by the templates along +Y; side-lying and
    sideways bodies lie along X, so the mat ran across the body, away from
    the camera, and looked like a slab standing up behind the athlete.  When
    a low (floor) body is clearly elongated in plan (over the whole loop) and
    the mat is more than min_deg off its long axis, the mat is turned to that
    axis and centred under the body (one placement for the whole loop)."""
    mats = [e for p in poses for e in p.equip if e["kind"] == "mat"]
    if not mats:
        return False
    v = np.concatenate([p.verts[::7] for p in poses[:: max(1, len(poses) // 6)]])
    if np.percentile(v[:, 2], 90) > 0.95:          # standing / kneeling tall: the mat stays as placed
        return False
    xy = v[:, :2]
    c = xy.mean(0)
    w, vec = np.linalg.eigh(np.cov((xy - c).T))
    a = vec[:, 1]
    b = np.array([-a[1], a[0]])
    s = (xy - c) @ a
    t = (xy - c) @ b
    if (s.max() - s.min()) < 1.4 * (t.max() - t.min()):
        return False
    M0 = np.asarray(mats[0]["M"], float)
    ay = M0[:2, 1] / max(np.linalg.norm(M0[:2, 1]), 1e-9)
    ang = math.degrees(math.acos(min(1.0, abs(float(ay @ a)))))
    if ang < min_deg:
        return False
    ctr = c + a * 0.5 * (s.max() + s.min()) + b * 0.5 * (t.max() + t.min())
    if a[1] < 0:
        a = -a
    M = np.eye(4)
    M[:2, 0] = (a[1], -a[0])
    M[:2, 1] = a
    M[:3, 3] = (ctr[0], ctr[1], M0[2, 3])
    for e in mats:
        e["M"] = M.copy()
    return True


def solve_loop(tpl, ctx, tl, row, mirror):
    """Solve the unique phases; alternating sides reuse the right-side
    solution mirrored (exactly symmetric reps)."""
    poses = [None] * len(tl.unique)
    warm = None
    ctx.r._twist = {}            # forearm-twist continuity starts fresh for every move (deterministic)
    ctx.__dict__.pop("_cache", None)
    order = sorted(range(len(tl.unique)), key=lambda i: (tl.unique[i][2] == "L", tl.unique[i][1]))
    solved = {}
    # settle the starting pose once before the loop so the first two frames
    # come from the same (converged) solution
    r0 = dict(row)
    r0["_side"], r0["_phase"] = "R", tl.unique[order[0]][1]
    warm = tpl.pose(ctx, tl.unique[order[0]][1], r0).info.get("adj")
    for i in order:
        key, ph, side = tl.unique[i]
        if side == "L":
            src = solved.get(("R", round(ph, 6)))
            if src is not None:
                poses[i] = mirror.pose(src)
                continue
        r = dict(row)
        r["_side"] = side or "R"
        r["_phase"] = ph
        p = tpl.pose(ctx, ph, r, warm=warm)
        warm = p.info.get("adj")
        poses[i] = p
        solved[(side or "R", round(ph, 6))] = p
    return poses


_CTX2 = {}


class _Both:
    """Main pose with the partner's body and equipment added (camera fit and render border)."""
    def __init__(self, p, q):
        self.verts = np.concatenate([p.verts, q.verts]) if q is not None else p.verts
        self.D, self.Hp, self.info = p.D, p.Hp, p.info
        self.equip = list(p.equip) + (list(q.equip) if q is not None else [])


def solve_partner(row, poses, tl, gender):
    """Second person of a partner exercise (tpl_x54.PARTNER): one pose per unique phase, solved on its own
    rig after the athlete (the partner may hold the athlete's ankles or a band from the athlete's hands)."""
    from . import tpl_x54b as tpl_x54
    from .poses import Ctx
    if row["key"] not in tpl_x54.PARTNER:
        return None, None
    if gender not in _CTX2:
        _CTX2[gender] = Ctx(gender)
    c2 = _CTX2[gender]
    c2.r._twist = {}
    c2.__dict__.pop("_cache", None)
    out, warm = [], None
    for i, (_, ph, side) in enumerate(tl.unique):
        q = tpl_x54.partner_pose(c2, ph, row, poses[i], side or "R", warm)
        warm = q.info.get("adj")
        out.append(q)
    return c2, out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--moves", required=True)
    ap.add_argument("--gender", required=True, choices=["m", "f"])
    ap.add_argument("--out", required=True)
    ap.add_argument("--start", type=int, default=0)
    ap.add_argument("--end", type=int, default=10 ** 9)
    ap.add_argument("--only", default="")
    ap.add_argument("--threads", type=int, default=2)
    ap.add_argument("--samples", type=int, default=2)
    ap.add_argument("--skip-existing", action="store_true")
    ap.add_argument("--res", default="")
    ap.add_argument("--style", default="v3", choices=["v3", "v4", "v5"],
                    help="v4: 600x400, 36 frames, sportswear, studio light, secondary motion, 120-220 KB")
    ap.add_argument("--preview", action="store_true", help="render only the start / middle / end poses (sheets, no WebP)")
    args = ap.parse_args()

    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import bpy
    from PIL import Image
    from . import scene, equipment as EQ, templates, muscles, motion, qa3, spec3
    from .poses import Ctx
    from .render import fit_camera, place_equipment
    from .mirror import Mirror

    rows = list(csv.DictReader(open(args.moves, encoding="utf-8")))
    rows = rows[args.start:args.end]
    if args.only:
        keep = set(args.only.split(","))
        rows = [r for r in rows if r["key"] in keep or r["name_en"] in keep or r["template"] in keep]
    os.makedirs(args.out, exist_ok=True)
    frames_dir = os.path.join(args.out, "_frames")
    sheet_dir = os.path.join(args.out, "_sheet")
    qa_dir = os.path.join(args.out, "_qa")
    for d in (frames_dir, sheet_dir, qa_dir):
        os.makedirs(d, exist_ok=True)
    sfx = "" if args.gender == "m" else ".f"

    from . import paint
    v5 = args.style == "v5"
    if v5:                     # 5.5: the v4 look, larger, 48 frames, red effort highlight, MP4 video
        args.style = "v4"
        scene.HL5 = True
    if args.style == "v4":
        paint.set_style("v4")
        scene.STYLE = "v4"
        templates.SECONDARY = True
        motion.set_frames(48 if v5 else 36)
        ENC.update(max_kb=220, target_kb=120, q0=90, q_floor=72, sharpen=True, thumb_size=None)
    res = tuple(int(v) for v in (args.res or ("900x600" if v5 else ("600x400" if args.style == "v4" else "480x320"))).split("x"))
    if args.style == "v4" and args.samples == 2:
        args.samples = 4          # 2 samples leave stair-stepped hair / limb edges at 600x400
    scene.init(threads=args.threads, samples=args.samples, res=res)
    cy = bpy.context.scene.cycles
    try:  # albedo + normal guided denoising: crisp edges at few samples
        cy.denoising_input_passes = "RGB_ALBEDO_NORMAL"
        v4 = args.style == "v4"     # v4: accurate prefilter keeps cloth / hair / face detail (no smearing)
        cy.denoising_prefilter = os.environ.get("ARTGEN_PREFILTER", "ACCURATE" if v4 else "FAST")
        cy.denoising_quality = os.environ.get("ARTGEN_DNQ", "BALANCED" if v4 else "FAST")
    except Exception:
        pass
    bpy.data.objects["floor"].scale = (9.0, 9.0, 1.0)   # floor edge far beyond the horizon of any camera
    ctx = Ctx(args.gender)
    body = scene.BodyObjects(ctx.r, args.gender)
    body2 = None
    mirror = Mirror(ctx.r)
    t_all = time.time()
    n_done = 0
    for row in rows:
        key = row["key"]
        webp = os.path.join(args.out, f"{key}{sfx}.webp")
        mp4 = os.path.join(args.out, f"{key}{sfx}.mp4")
        thumb = os.path.join(args.out, f"{key}{sfx}.thumb.webp")
        if args.skip_existing and os.path.exists(webp) and os.path.exists(thumb) and (not v5 or os.path.exists(mp4)):
            continue
        t0 = time.time()
        row = spec3.expand(row)
        try:
            tpl = templates.get(row["template"])
        except KeyError as e:
            print(f"[{args.gender}] {key} ERROR {e}", flush=True)
            continue
        tl = motion.timeline(**row["_tempo"], linear=tpl.linear)
        poses = solve_loop(tpl, ctx, tl, row, mirror)
        align_mats(poses)
        c2, pposes = solve_partner(row, poses, tl, args.gender)
        if pposes and body2 is None:
            body2 = scene.BodyObjects(c2.r, args.gender)
            body2.set_highlight([])
        if body2 is not None:
            body2.show(bool(pposes))
        both = [_Both(p, pposes[i] if pposes else None) for i, p in enumerate(poses)]
        t_pose = time.time() - t0
        hl_keys, hl_w = muscles.highlight(row)
        body.set_highlight(hl_keys, hl_w)
        kind = (row.get("_tempo") or {}).get("kind", "rep")
        pts, cam, tgt, lens = fit_view(both, row, tpl, ctx.r, args.gender)
        view = row["_view"] or tpl.view_angles()
        scene.set_camera(cam, tgt, lens)
        set_border_np(bpy, _border_points(both, pts), cam, tgt, lens)
        bpy.data.objects["floor"].location = (float(pts[:, 0].mean()), float(pts[:, 1].mean()), 0.0)
        made = {}
        imgs = []
        sheet_idx = tl.sheet_indices()
        if args.preview and os.environ.get("ARTGEN_PREV_N"):
            nprev = int(os.environ["ARTGEN_PREV_N"])
            sheet_idx = sorted(set(int(round(v)) for v in np.linspace(0, len(poses) - 1, nprev)))
        for i, p in enumerate(poses):
            if args.preview and i not in sheet_idx:
                imgs.append(None)
                continue
            body.update(p.verts, p.D, p.Hp)
            if v5:
                body.set_highlight(hl_keys, hl_w, effort(kind, tl.unique[i][1]))
            if pposes:
                body2.update(pposes[i].verts, pposes[i].D, pposes[i].Hp)
            seen = set()
            for e in both[i].equip:
                seen.add(e["id"])
                place_equipment(e, made, EQ)
            for eid, ob in made.items():
                hide = eid not in seen
                for o in [ob] + list(ob.children):
                    o.hide_render = hide
            fp = os.path.join(frames_dir, f"{key}{sfx}_{i}.png")
            scene.render_png(fp)
            imgs.append(feather(Image.open(fp).convert("RGBA"), bpy.context.scene.render))
        thumb_idx = spec3.thumb_index(row, tl)
        marked = None
        if args.preview:
            q, size = 0, 0
        elif v5:
            # 900x600 MP4 for the new site and app, plus the 600x400 animated WebP and still for older apps
            _, vsize, _ = encode_video(imgs, tl.frames, mp4, None, thumb_idx)
            small = [im.resize((600, 400), Image.LANCZOS) if im is not None else None for im in imgs]
            q, size, marked = encode(small, tl.frames, webp, thumb, thumb_idx)
            size += vsize
        else:
            q, size, marked = encode(imgs, tl.frames, webp, thumb, thumb_idx)
        for j, u in enumerate(sheet_idx if args.preview else tl.sheet_indices()):
            if marked is not None:
                marked[u].save(os.path.join(sheet_dir, f"{key}{sfx}.{j}.png"))
                continue
            b = scene.background(imgs[u].size)
            b.alpha_composite(imgs[u])
            b.convert("RGB").save(os.path.join(sheet_dir, f"{key}{sfx}.{j}.png"))
        for i in range(len(poses)):
            if imgs[i] is None:
                continue
            try:
                os.remove(os.path.join(frames_dir, f"{key}{sfx}_{i}.png"))
            except OSError:
                pass
        for ob in made.values():
            for o in list(ob.children) + [ob]:
                bpy.data.objects.remove(o, do_unlink=True)
        for m in list(bpy.data.meshes):
            if m.users == 0:
                bpy.data.meshes.remove(m)
        rep = qa3.check(ctx, poses, tl, tpl, row)
        frac = athlete_fraction(poses, cam, tgt, lens)
        rep["athlete_frac"] = round(frac, 2)
        if frac < qa3.MIN_FRAME:
            rep["issues"].append(f"frame:{frac:.2f}")
        rep["thumb"] = f"{row.get('thumb') or 'end'}@{tl.unique[thumb_idx][1]:.2f}"
        rep["pose_hash"] = pose_hash(poses, cam)
        rep["view"] = list(view) if not isinstance(view, str) else view
        dt = time.time() - t0
        rep.update(key=key, name_en=row["name_en"], template=row["template"], gender=args.gender,
                   seconds=round(dt, 1), pose_seconds=round(t_pose, 1), quality=q, bytes=size,
                   frames=len(tl.frames), unique=len(tl.unique))
        json.dump(rep, open(os.path.join(qa_dir, f"{key}{sfx}.json"), "w"), indent=1)
        n_done += 1
        print(f"[{args.gender}] {key} {row['template']} {dt:.1f}s q={q} {size // 1024}KB "
              f"{' '.join(rep['issues'])}", flush=True)
    print(f"done {n_done} in {time.time() - t_all:.0f}s", flush=True)


if __name__ == "__main__":
    main()
