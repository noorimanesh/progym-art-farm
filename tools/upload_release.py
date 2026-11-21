#!/usr/bin/env python3
"""Pack rendered files into tar.gz chunks (<= 90 MB) and upload them as
assets of the GitHub release `exercise-art-v1` (created on first use).

  python3 tools/upload_release.py --name batch01 FILE_OR_DIR [...]

Uses the `gh api` CLI for the GitHub REST API.  Existing assets with the
same name are replaced.
"""
import argparse
import json
import os
import subprocess
import tarfile

REPO = "noorimanesh/progym-android"
TAG = "exercise-art-v1"
LIMIT = 90 * 1024 * 1024


def gh(args, data=None):
    r = subprocess.run(["gh", "api"] + args, input=data, capture_output=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.decode() + r.stdout.decode())
    out = r.stdout.decode()
    return json.loads(out) if out.strip() else None


def release_id():
    try:
        return gh([f"repos/{REPO}/releases/tags/{TAG}"])["id"]
    except RuntimeError:
        body = json.dumps({"tag_name": TAG, "target_commitish": "exercise-art", "name": TAG,
                           "body": "Generated exercise illustrations (animated WebP + JPEG thumbnails), "
                                   "male `<slug>.webp` and female `<slug>.f.webp`. See LICENSES.md on the "
                                   "exercise-art branch.", "draft": False, "prerelease": True}).encode()
        return gh(["-X", "POST", f"repos/{REPO}/releases", "--input", "-"], data=body)["id"]


def pack(files, base):
    chunks, cur, size = [], [], 0
    for f in files:
        s = os.path.getsize(f)
        if cur and size + s > LIMIT * 0.97:
            chunks.append(cur)
            cur, size = [], 0
        cur.append(f)
        size += s
    if cur:
        chunks.append(cur)
    outs = []
    for i, ch in enumerate(chunks):
        name = f"{base}-{i + 1:02d}.tar.gz" if len(chunks) > 1 else f"{base}.tar.gz"
        path = os.path.join("/tmp" if not os.environ.get("PACK_DIR") else os.environ["PACK_DIR"], name)
        with tarfile.open(path, "w:gz") as t:
            for f in ch:
                t.add(f, arcname=os.path.join(os.path.basename(os.path.dirname(f)), os.path.basename(f)))
        outs.append(path)
    return outs


def upload(rid, path):
    name = os.path.basename(path)
    for a in gh([f"repos/{REPO}/releases/{rid}/assets", "--paginate"]) or []:
        if a["name"] == name:
            gh(["-X", "DELETE", f"repos/{REPO}/releases/assets/{a['id']}"])
    r = subprocess.run(["gh", "api", "-X", "POST",
                        f"https://uploads.github.com/repos/{REPO}/releases/{rid}/assets?name={name}",
                        "-H", "Content-Type: application/gzip", "--input", path], capture_output=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.decode() + r.stdout.decode())
    return json.loads(r.stdout.decode())["browser_download_url"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", required=True)
    ap.add_argument("paths", nargs="+")
    a = ap.parse_args()
    files = []
    for p in a.paths:
        if os.path.isdir(p):
            files += sorted(os.path.join(p, f) for f in os.listdir(p)
                            if f.endswith((".webp", ".jpg", ".csv", ".png", ".tar.gz")) and not f.startswith("_"))
        else:
            files.append(p)
    rid = release_id()
    ready = [f for f in files if f.endswith(".tar.gz")]
    for path in ready:
        print(upload(rid, path), os.path.getsize(path))
    rest = [f for f in files if not f.endswith(".tar.gz")]
    for path in (pack(rest, f"{TAG}-{a.name}") if rest else []):
        print(upload(rid, path), os.path.getsize(path))
        os.remove(path)


if __name__ == "__main__":
    main()
