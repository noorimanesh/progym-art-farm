"""Spec rows (data/spec/part-*.csv) -> data/v3/moves.csv: one row of set-up
data per exercise (see artgen/spec3.py for the columns).

  python3 tools/make_moves.py            # writes data/v3/moves.csv and data/v3/moves-review.csv

Template: the archetype that rendered the exercise correctly before when the
auditors marked the drawing ok, otherwise the name rules of artgen/worklist,
then the spec rules and per-exercise choices below.  Implements, support,
position and grip of the spec become the equipment words and parameters the
archetype reads; sides set the tempo (alternating reps, one-arm freeze);
camera, tempo direction and thumbnail pose come from tables per archetype.
"""
import csv
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from artgen.worklist import str_slug  # noqa: E402

FIELDS = ["key", "name_en", "template", "equipment", "params", "tempo", "first", "view", "lens", "thumb",
          "muscles", "muscles2", "status", "note"]

# archetypes whose phase 0 -> 1 lifts the load (concentric first)
CON_FIRST = {
    "bench_press", "db_bench_press", "overhead_press", "db_shoulder_press", "arnold_press", "landmine_press",
    "machine_chest_press", "chest_press_standing", "barbell_curl", "db_curl", "preacher_curl", "concentration_curl",
    "spider_curl", "overhead_cable_curl", "lateral_raise", "front_raise", "rear_delt_raise", "upright_row", "shrug",
    "face_pull", "barbell_row", "db_row", "tbar_row", "cable_row", "machine_row", "inverted_row", "lat_pulldown",
    "straight_arm_pulldown", "pull_up", "deadlift", "hip_thrust", "glute_bridge", "calf_raise", "seated_calf_raise",
    "leg_extension", "seated_leg_curl", "lying_leg_curl", "standing_leg_curl", "crunch", "sit_up", "reverse_crunch",
    "leg_raise", "hanging_leg_raise", "v_up", "back_extension", "cable_crossover", "pec_deck", "triceps_pushdown",
    "triceps_kickback", "overhead_triceps_extension", "skull_crusher", "wrist_curl", "kb_swing", "cable_pull_through",
    "band_pull_apart", "external_rotation", "reverse_fly_machine", "hip_abductor_machine", "glute_kickback_machine",
    "superman", "power_clean", "kb_clean", "thruster", "olympic", "step_up", "db_fly", "pullover", "dip",
    "hip_abduction_standing", "hip_adduction_standing", "standing_kickback", "donkey_kick", "fire_hydrant",
    "clam", "side_leg_raise", "standing_knee_raise", "standing_band_row", "chest_supported", "assisted_pull_up",
    "side_bend", "pec_deck",
}
CYCLE = {"jump_rope": "0.25", "box_jump": "0.38", "depth_jump": "0.28", "bike": "0.25", "treadmill_run": "0.25", "battle_ropes": "0.25", "burpee": "0.32"}
THUMB_PHASE = {"olympic": "0.74"}
VIEW_FIX = {"pallof_press": "68,12"}      # archetype camera hid the movement     # periodic archetypes and their thumbnail phase
ECC_FIRST = {
    "back_squat", "squat", "front_squat", "goblet_squat", "bodyweight_squat", "sumo_squat", "overhead_squat",
    "box_squat", "pistol_squat", "cossack_squat", "split_squat", "bulgarian_split_squat", "forward_lunge",
    "reverse_lunge", "lateral_lunge", "curtsy_lunge", "romanian_deadlift", "good_morning", "single_leg_rdl",
    "push_up", "leg_press", "ab_rollout", "glute_ham_raise", "hack_squat_machine",
}
# thumbnail at phase 0 (hardest / most telling point is the start pose of the archetype)
THUMB_START = {"bench_press", "db_bench_press", "overhead_press", "db_shoulder_press", "arnold_press",
               "machine_chest_press", "chest_press_standing", "deadlift", "landmine_press", "db_fly"}
VIEW_AZ = {"side": 90, "front": 15, "three_quarter": 45, "back": 150, "top": 60}

FREEZE_ARM = {"db_curl", "barbell_curl", "db_shoulder_press", "arnold_press", "lateral_raise", "front_raise",
              "rear_delt_raise", "overhead_triceps_extension", "triceps_kickback", "triceps_pushdown",
              "db_bench_press", "db_fly", "chest_press_standing", "cable_crossover", "upright_row",
              "external_rotation", "face_pull", "machine_chest_press", "preacher_curl", "lat_pulldown",
              "cable_row", "db_row", "overhead_cable_curl", "wrist_curl", "shrug", "landmine_press", "kb_swing",
              "band_pull_apart", "straight_arm_pulldown"}

# per-exercise choices where the spec needs a different archetype than the name rules give
OVERRIDES = {
    "Band Pull-apart": "band_pull_apart",
    "Australian Chin-up": "inverted_row",
    "Side Plank Hip Dip": "side_plank",
    "Copenhagen Plank": "side_plank",
    "Standing Hip Circles": "hip_circle_standing",
    "Prone Calf Stretch": "downward_dog",
    "Band Overhead Pull-apart": "band_pull_apart",
    "Band Overhead Pull Apart": "band_pull_apart",
    "Spiderman Plank Crunch": "mountain_climber",
    "Walkout to Push-up": "walkout",
    "Single-Leg Dumbbell Calf Raise": "seated_calf_raise",
    "Foam Roll Glute Bridge": "glute_bridge",
    "Side Leg Hip Circle": "side_leg_raise",
    "Stiff-Leg Barbell Good Morning": "good_morning",
    "Incline Dumbbell Press": "db_bench_press",
    "Band Row": "standing_band_row",
    "Jump Rope": "jump_rope",
    "Handstand Push-up": "handstand",
    "Handstand Hold": "handstand",
    "Kipping Handstand Push-up": "handstand",
    "Partner Handstand": "handstand",
    "Handstand Walk": "handstand",
    "Wall Handstand Hold": "handstand",
    "Assisted Pull-up Machine": "assisted_pull_up",
    "Assisted Wide Grip Pull-up": "assisted_pull_up",
    "Assisted Neutral Grip Pull-up": "assisted_pull_up",
    "Assisted Chin-up": "assisted_pull_up",
    "Chest-Supported Dumbbell Row": "chest_supported",
    "Incline Y-Raise": "chest_supported",
    "Dumbbell Bent-Over Row": "db_row",
    "Hack Squat": "hack_squat_machine",
    "Machine Fly": "pec_deck",
    "Reverse Machine Fly": "pec_deck",
    "Cable Glute Kickback": "standing_kickback",
    "Cable Hip Abduction": "hip_abduction_standing",
    "Cable Hip Adduction": "hip_adduction_standing",
    "Cable Knee Drive": "standing_knee_raise",
    "Spider Curl": "chest_supported",
    "Dumbbell Side Bend": "side_bend",
    "Side Bend Stretch": "side_bend",
    "Dowel Lateral Bend": "side_bend",
    "Lying Hamstring Stretch": "lying_hamstring_stretch",
    "Partner Hamstring Stretch": "lying_hamstring_stretch",
}


def olympic_params(name, sp):
    """Barbell / dowel clean-snatch family -> parameters of the olympic archetype."""
    n = name.lower()
    imp = (sp.get("implements") or "").lower()
    if not re.search(r"clean|snatch|jerk|high pull|push press", n) or "kettlebell" in n or "dumbbell" in n:
        return None
    if re.search(r"push press|^(push |split )?jerk$|behind the neck", n) and "clean" not in n:
        return {"implement": "barbell", "lift": "clean", "start": "rack", "catch": "power",
                "then": "split_jerk" if "split" in n else ("jerk" if "jerk" in n else "press")}
    if "snatch balance" in n or "deadlift" in n and "high pull" not in n:
        return None
    p = {}
    p["implement"] = "pvc" if "dowel" in n or "pvc" in imp else "barbell"
    p["lift"] = "snatch" if "snatch" in n else "clean"
    if "high pull" in n:
        p["lift"] = "high_pull"
    elif re.search(r"\bpull\b", n) and not re.search(r"pull to|to hang", n):
        p["lift"] = "pull"
    if "snatch" in n and p["lift"] in ("pull", "high_pull"):
        p["snatch_grip"] = 1
    p["start"] = "blocks" if "block" in n else ("low_hang" if "low hang" in n else ("hang" if "hang" in n else "floor"))
    p["catch"] = "split" if "split" in n else ("muscle" if "muscle" in n else (
        "power" if "power" in n or "and press" in n else "squat"))
    if "jerk" in n:
        p["then"] = "split_jerk" if "clean and jerk" in n or "split jerk" in n else "jerk"
    elif "and press" in n or "to press" in n:
        p["then"] = "press"
    elif "front squat" in n:
        p["then"] = "front_squat"
    elif "overhead squat" in n:
        p["then"] = "ohs"
    if "sumo" in n:
        p["sumo"] = 1
    return p


def words_of(sp):
    """Spec implements / support / position / grip -> equipment words."""
    parts = []
    for col in ("implements", "support", "position", "grip"):
        v = (sp.get(col) or "").lower()
        if v and v not in ("none", "floor"):
            parts.append(v)
    s = " ; ".join(parts)
    rep = [("bench_incline_30 to 45", "incline bench 30"), ("bench_incline_30", "incline bench 30"),
           ("bench_incline_45", "incline bench 45"), ("bench_decline", "decline bench"),
           ("bench_flat", "flat bench"), ("bench_upright", "upright bench seated"), ("_x2", " pair"),
           ("_x1", " single"), ("suspension_straps", "suspension straps trx"), ("pullup_bar", "pull-up bar"),
           ("cable_low", "cable low pulley"), ("cable_mid", "cable mid pulley"), ("cable_high", "cable high pulley"),
           ("d_handle", "d-handle"), ("v_handle", "v-bar handle"), ("straight_bar", "straight bar"),
           ("ankle_strap", "ankle strap"), ("ez_bar", "ez bar"), ("trap_bar", "trap bar"), ("pvc_dowel", "pvc dowel"),
           ("medicine_ball", "medicine ball"), ("stability_ball", "stability ball"), ("foam_roller", "foam roller"),
           ("balance_trainer", "balance trainer bosu"), ("mini_band", "mini band"), ("band_feet", "band under feet"),
           ("leg_press_45", "leg press"), ("dip_bars", "dip bars"), ("preacher_bench", "preacher bench"),
           ("machine_seat", "machine seat")]
    for a, b in rep:
        s = s.replace(a, b)
    return s


def params_of(sp, tpl):
    p = {}
    sup = (sp.get("support") or "").lower()
    imp = (sp.get("implements") or "").lower()
    grip = (sp.get("grip") or "").lower()
    pos = (sp.get("position") or "").lower()
    if "bench_incline" in sup or "incline" in pos and "bench" in sup:
        p["bench"] = "incline"
        p["bench_angle"] = 45 if "45" in sup and "30" not in sup else 30
    elif "bench_decline" in sup or "decline" in pos and "bench" in sup:
        p["bench"], p["bench_angle"] = "decline", 18
    elif "bench_upright" in sup:
        p["bench"], p["bench_angle"] = "upright", 82
    elif "bench_flat" in sup and tpl in ("bench_press", "db_bench_press", "db_fly", "skull_crusher"):
        p["bench"] = "flat"
    elif sup.startswith("floor") and tpl in ("bench_press", "db_bench_press", "db_fly") and "supine" in pos:
        p["bench"] = "floor"
    if re.search(r"supinat|underhand|palms? (up|facing (up|you|toward))", grip):
        p["grip"] = "sup"
    elif re.search(r"neutral|hammer|palms facing each other", grip):
        p["grip"] = "neutral"
    elif re.search(r"pronat|overhand", grip):
        p["grip"] = "pro"
    if re.search(r"close|narrow", grip):
        p["width"] = "close"
    elif re.search(r"wide", grip) and not re.search(r"slightly wider|shoulder", grip):
        p["width"] = "wide"
    m = re.search(r"cable_(low|mid|high)", imp)
    if m:
        p["pulley"] = m.group(1)
    for k, v in (("rope", "rope"), ("straight_bar", "bar"), ("v_handle", "v"), ("d_handle", "d"),
                 ("ankle_strap", "ankle"), ("lat_bar", "lat")):
        if k in imp:
            p["attach"] = v
            break
    return p


def tempo_of(sp, tpl, p):
    sides = (sp.get("sides") or "").lower()
    motion = " ".join((sp.get(k) or "") for k in ("motion", "start", "end")).lower()
    first = "con" if tpl in CON_FIRST else ("ecc" if tpl in ECC_FIRST else "even")
    kind = "rep"
    if tpl in CYCLE:
        return "cycle", "even"
    nm = (sp.get("name_en") or "").lower()
    if " to " in nm and re.search(r"(romanian|deadlift|calf raise).* to .*(row|high pull|shrug|calf raise)", nm):
        return "cycle", "even"          # two-part combos: one pass through both movements, uniform timing
    if tpl in ("leg_raise", "superman") and "alternating" in nm:
        return "alt", "even"            # one leg, then the other (mirrored)
    if sides.startswith("alternating") and tpl in FREEZE_ARM:
        kind = "alt"
        p["freeze"] = "L"
    elif sides.startswith("one_side") and tpl in FREEZE_ARM:
        p["freeze"] = "L"
    if re.search(r"\b(hold|isometric|static)\b", motion) and not re.search(r"\b(lower|raise|press|pull|curl|row)\b",
                                                                          sp.get("motion", "").lower()):
        kind, first = "hold", "even"
    return kind, first


def view_of(sp, tpl_view):
    cam = (sp.get("camera") or "").strip()
    az = tpl_view[0] if isinstance(tpl_view, tuple) else None
    if cam not in VIEW_AZ or az is None:
        return ""
    want = VIEW_AZ[cam]
    if abs(abs(az) - want) <= 35 or (cam == "side" and 45 <= abs(az) <= 100):
        return ""          # the archetype's own camera already shows it this way
    el = {"top": 35, "front": 8, "side": 8, "three_quarter": 12, "back": 10}[cam]
    return f"{want},{el}"


def main():
    from artgen import templates
    specs = []
    for i in (1, 2, 3):
        specs += list(csv.DictReader(open(os.path.join(ROOT, f"data/spec/part-{i}.csv"), encoding="utf-8")))
    wl = {r["name_en"]: r for r in csv.DictReader(open(os.path.join(ROOT, "data/v3/worklist-full.csv"), encoding="utf-8"))}
    table = [r["name_en"] for r in csv.DictReader(open(os.path.join(ROOT, "data/table-full.csv"), encoding="utf-8"))]
    by_name = {s["name_en"]: s for s in specs}
    keys, out, review = {}, [], []
    for name in table:
        sp = by_name.get(name)
        w = wl[name]
        k = str_slug(name)
        if k in keys:
            n = 2
            while f"{k}-{n}" in keys:
                n += 1
            k = f"{k}-{n}"
        keys[k] = name
        tpl = OVERRIDES.get(name, w["template"])
        if re.search(r"depth jump|drop jump", name.lower()):
            tpl = "depth_jump"
        oly = olympic_params(name, sp or {}) if tpl in ("power_clean", "thruster", "deadlift", "overhead_press") else None
        if oly and (not (sp or {}).get("current", "").startswith("ok") or oly.get("start") == "rack"):
            tpl = "olympic"
        if sp is None:
            review.append(dict(key=k, name_en=name, reason="no spec row"))
            sp = {}
        p = params_of(sp, tpl)
        extra_words = ""
        if tpl in ("barbell_curl", "db_curl", "preacher_curl", "concentration_curl") and p.get("grip") == "pro":
            extra_words = " ; reverse grip"
        elif tpl in ("db_curl", "preacher_curl") and p.get("grip") == "neutral":
            extra_words = " ; hammer grip"
        if tpl == "olympic" and oly:
            p.update(oly)
        if tpl == "box_jump":
            nl = name.lower()
            if "lateral" in nl:
                p["dir"] = "lat"
            elif "reverse" in nl or "backward" in nl:
                p["dir"] = "back"
        kind, first = tempo_of(sp, tpl, p)
        view = view_of(sp, templates.get(tpl).view_angles()) if tpl in templates.REG else ""
        if tpl in ("bench_press", "db_bench_press", "db_fly", "skull_crusher") and p.get("bench") == "decline":
            view = "42,30"           # the head-down bench hides the athlete behind the plates from the side
        if tpl in VIEW_FIX and not (sp.get("current") or "").startswith("ok"):
            view = VIEW_FIX[tpl]
        if "wrong_camera" in (sp.get("current") or ""):
            view = "15,10" if sp.get("camera") == "front" else "38,14"
        if tpl == "inverted_row" and not any(k in (sp.get("implements") or "").lower() + name.lower()
                                             for k in ("suspension", "trx", "ring")):
            view = "-60,20"          # from the feet side: the rack upright and plate never hide the athlete
        if "wall ball" in name.lower() or (tpl == "standing_knee_raise" and "wall" in name.lower()) or \
                "wall shoulder stretch" in name.lower():
            view = "88,10"           # from the side: the wall in front never hides the athlete
        thumb = "start" if tpl in THUMB_START else CYCLE.get(tpl, THUMB_PHASE.get(tpl, "end"))
        if kind == "cycle" and tpl not in CYCLE:     # two-part combos: the peak of the second movement
            thumb = "0.74"
        status = (sp.get("current") or "").split(";")[0].split()[0] if sp.get("current") else ""
        out.append(dict(key=k, name_en=name, template=tpl, equipment=(words_of(sp) or w["equipment"]) + extra_words,
                        params=json.dumps(p, sort_keys=True), tempo=kind, first=first, view=view, lens="",
                        thumb=thumb, muscles=w["muscles"], muscles2=w["muscles2"], status=status,
                        note=(sp.get("confidence") or "")))
        if (sp.get("confidence") or "high") != "high":
            review.append(dict(key=k, name_en=name, reason=f"confidence {sp.get('confidence')}"))
    dest = os.path.join(ROOT, "data/v3/moves.csv")
    with open(dest, "w", newline="", encoding="utf-8") as f:
        wr = csv.DictWriter(f, fieldnames=FIELDS)
        wr.writeheader()
        wr.writerows(out)
    with open(os.path.join(ROOT, "data/v3/moves-review.csv"), "w", newline="", encoding="utf-8") as f:
        wr = csv.DictWriter(f, fieldnames=["key", "name_en", "reason"])
        wr.writeheader()
        wr.writerows(review)
    print(dest, len(out), "rows;", len(review), "to review")


if __name__ == "__main__":
    main()
