"""Phase-1 test set: 30 exercises of different kinds -> data/v3/test-moves.csv
(set-up values written as data, the way the spec rows will drive them)."""
import csv
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

# name_en: (template or None = inferred, params, tempo, first, view, thumb, equipment words)
TEST = {
    "Barbell Bench Press": ("bench_press", dict(bench="flat"), "rep", "ecc", "", "end", "barbell;flat bench;rack"),
    "Incline Barbell Bench Press": ("bench_press", dict(bench="incline", bench_angle=30), "rep", "ecc", "", "end", "barbell;incline bench 30;rack"),
    "Decline Barbell Bench Press": ("bench_press", dict(bench="decline", bench_angle=18), "rep", "ecc", "", "end", "barbell;decline bench;rack"),
    "Dumbbell Bench Press": ("db_bench_press", dict(bench="flat"), "rep", "ecc", "", "end", "dumbbell;flat bench"),
    "Incline Dumbbell Press": ("db_bench_press", dict(bench="incline", bench_angle=30), "rep", "ecc", "", "end", "dumbbell;incline bench 30"),
    "Decline Dumbbell Bench Press": ("db_bench_press", dict(bench="decline", bench_angle=18), "rep", "ecc", "", "end", "dumbbell;decline bench"),
    "Dumbbell Fly": ("db_fly", dict(bench="flat"), "rep", "ecc", "", "end", "dumbbell;flat bench"),
    "Barbell Squat": ("back_squat", dict(), "rep", "ecc", "", "end", "barbell;rack"),
    "Deadlift": ("deadlift", dict(), "rep", "con", "", "start", "barbell"),
    "Romanian Deadlift": ("romanian_deadlift", dict(), "rep", "ecc", "", "end", "barbell"),
    "Pull-up": ("pull_up", dict(grip="pro"), "rep", "con", "", "end", "pull-up bar"),
    "Lat Pulldown": ("lat_pulldown", dict(attach="lat", grip="pro"), "rep", "con", "", "end", "cable;lat pulldown machine;lat bar"),
    "Cable Crossover": ("cable_crossover", dict(pulley="high", attach="d"), "rep", "con", "", "end", "cable;high pulley;d-handle"),
    "Seated Cable Row": ("cable_row", dict(attach="v"), "rep", "con", "", "end", "cable;seated row machine;v-handle"),
    "Leg Press": ("leg_press", dict(), "rep", "ecc", "", "end", "machine;45 degree leg press"),
    "Barbell Curl": ("barbell_curl", dict(grip="sup"), "rep", "con", "", "end", "barbell"),
    "Hammer Curl": ("db_curl", dict(grip="neutral", freeze="L"), "alt", "con", "", "end", "dumbbell"),
    "Preacher Curl": ("preacher_curl", dict(), "rep", "con", "", "end", "ez bar;preacher bench"),
    "Dumbbell Lunge": ("forward_lunge", dict(), "rep", "ecc", "", "end", "dumbbell"),
    "Plank": ("plank", dict(), "hold", "even", "", "end", "mat"),
    "Push-up": ("push_up", dict(), "rep", "ecc", "", "end", "bodyweight"),
    "Band Pull-apart": ("band_pull_apart", dict(), "rep", "con", "", "end", "band"),
    "Suspension Row": ("inverted_row", dict(), "rep", "con", "", "end", "suspension straps;anchor"),
    "Leg Extension": ("leg_extension", dict(), "rep", "con", "", "end", "machine;leg extension machine"),
    "Machine Chest Press": ("machine_chest_press", dict(), "rep", "con", "", "end", "machine;chest press machine"),
    "Seated Leg Curl": ("seated_leg_curl", dict(), "rep", "con", "", "end", "machine;seated leg curl machine"),
    "Box Jump": ("box_jump", dict(), "cycle", "even", "", "0.38", "plyo box"),
    "Kettlebell Swing": ("kb_swing", dict(), "rep", "con", "", "end", "kettlebell"),
    "Standing Quad Stretch": ("quad_stretch_standing", dict(), "hold", "even", "", "end", "bodyweight"),
    "Overhead Press": ("overhead_press", dict(), "rep", "con", "", "end", "barbell"),
}

FIELDS = ["key", "name_en", "template", "equipment", "params", "tempo", "first", "view", "lens", "thumb",
          "muscles", "muscles2", "status", "note"]


def main():
    wl = {r["name_en"]: r for r in csv.DictReader(open(os.path.join(ROOT, "data/v3/worklist-full.csv"), encoding="utf-8"))}
    out = []
    for name, (tpl, prm, tempo, first, view, thumb, eq) in TEST.items():
        w = wl[name]
        out.append(dict(key=w["slug"], name_en=name, template=tpl or w["template"], equipment=eq,
                        params=json.dumps(prm), tempo=tempo, first=first, view=view, lens="", thumb=thumb,
                        muscles=w["muscles"], muscles2=w["muscles2"], status="test", note=""))
    dest = os.path.join(ROOT, "data/v3/test-moves.csv")
    with open(dest, "w", newline="", encoding="utf-8") as f:
        wr = csv.DictWriter(f, fieldnames=FIELDS)
        wr.writeheader()
        wr.writerows(out)
    print(dest, len(out))


if __name__ == "__main__":
    main()
