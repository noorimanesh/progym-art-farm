"""Move rows (data/v3/moves.csv) -> what the templates and the renderer read.

A move row describes one exercise as data:

  key        file key, Laravel Str::slug(name_en) (+ -2/-3 for duplicates)
  name_en    exercise identity
  template   movement archetype (templates.REG); one archetype serves every
             exercise with the same movement, the row's data sets it up
  equipment  implement / support words, ';' separated (barbell; incline bench 30; ...)
  params     JSON object of set-up values the archetype reads with P():
             bench ("flat" | "incline" | "decline" | "upright" | "floor"),
             bench_angle (deg), grip ("pro" | "sup" | "neutral" | "mixed"),
             width ("close" | "shoulder" | "wide" or a factor of shoulder width),
             sides ("both" | "one" | "alt"), stance, pulley ("low" | "mid" | "high"),
             attach ("rope" | "bar" | "v" | "d" | "ankle" | "lat"), depth, ...
  tempo      rep | alt | cycle | hold | flight
  first      ecc (first half lowers the load) | con | even
  view       camera: name from templates.VIEWS or "azimuth,elevation"
  lens       focal length (mm), optional
  thumb      start | mid | end | phase 0..1: the pose used for the thumbnail
  muscles / muscles2   highlight keys (primary / secondary)
"""
import json

from .templates import VIEWS

DEFAULT_TEMPO = dict(kind="rep", first="even")


def P(row, k, d=None):
    return (row.get("_p") or {}).get(k, d)


def expand(row):
    row = dict(row)
    try:
        row["_p"] = json.loads(row.get("params") or "{}")
    except ValueError:
        row["_p"] = {}
    kind = (row.get("tempo") or "rep").strip() or "rep"
    first = (row.get("first") or "even").strip() or "even"
    t = dict(kind=kind, first=first)
    if row["_p"].get("ratio"):
        t["ratio"] = float(row["_p"]["ratio"])
    if row["_p"].get("hold_b") is not None:
        t["hold_b"] = int(row["_p"]["hold_b"])
    if row["_p"].get("hold_a") is not None:
        t["hold_a"] = int(row["_p"]["hold_a"])
    row["_tempo"] = t
    fz = row["_p"].get("freeze")
    if fz:
        row["_freeze"] = fz
    v = (row.get("view") or "").strip()
    if v in VIEWS:
        row["_view"] = VIEWS[v]
    elif "," in v:
        a, e = v.split(",")[:2]
        row["_view"] = (float(a), float(e))
    else:
        row["_view"] = None
    return row


def thumb_index(row, tl):
    th = (row.get("thumb") or "end").strip()
    src = [i for i, u in enumerate(tl.unique) if u[2] != "L"]
    if th == "start":
        ph = 0.0
    elif th == "mid":
        return tl.mid_index()
    elif th == "end":
        ph = 1.0 if tl.kind != "cycle" else 0.25
    else:
        try:
            ph = float(th)
        except ValueError:
            ph = 1.0
    return min(src, key=lambda i: abs(tl.unique[i][1] - ph))
