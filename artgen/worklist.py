"""Build the render work list (CSV) from an exercise source.

  python -m artgen.worklist --json exercises.json  --out data/worklist.csv --review data/review.csv
  python -m artgen.worklist --csv  exercises.csv   --out data/worklist.csv --review data/review.csv

The CSV source is the ProGym exercise table export with columns
name_en, muscle, target_muscles, secondary_targets, equipment,
equipment_tags, pattern, force, mechanic (extra columns are ignored).
Every row gets: slug (Laravel Str::slug of name_en), name_en, muscle_group,
equipment, template, muscles, muscles2, match, note.
"""
import argparse
import csv
import json
import re
import unicodedata

from . import muscles as M

# ------------------------------------------------------------------ slug
def str_slug(title, sep="-"):
    """Port of Laravel Illuminate\\Support\\Str::slug (language 'en')."""
    t = unicodedata.normalize("NFKD", str(title))
    t = "".join(ch for ch in t if not unicodedata.combining(ch))
    t = t.replace("’", "'").replace("‘", "'")
    t = t.encode("ascii", "ignore").decode("ascii")
    t = t.replace("_", sep)
    t = t.replace("@", f"{sep}at{sep}")
    t = re.sub(r"[^\-\w\s]+", "", t.lower())
    t = t.replace("_", "")
    t = re.sub(r"[\-\s]+", sep, t)
    return t.strip(sep)


# ------------------------------------------------------------ equipment
EQUIP = [
    ("smith machine", r"\bsmith\b"), ("trap bar", r"trap bar|hex bar"), ("ez bar", r"\bez[- ]?bar\b|\bez\b"),
    ("landmine", r"landmine"), ("kettlebell", r"kettlebell|\bkb\b"), ("dumbbell", r"dumbbell|\bdb\b"),
    ("barbell", r"barbell|\bbar\b(?! assisted)|^deadlift$|^(pause |olympic |pulse )?(back |front )?squat$|back squat|"
                r"front squat|zercher|overhead squat$|bench press|clean|snatch|jerk|pendlay|good morning|rack pull|"
                r"^thruster$|push press|skullcrusher|skull crusher|close-grip bench|rack pulls|stiff-legged deadlift$|"
                r"^romanian deadlift$|^sumo deadlift|bent over barbell"),
    ("cable", r"cable|pulldown|pull down|face pull|crossover"), ("machine", r"machine|hammerstrength|freemotion|"
                                                                          r"leg press|leg extension|leg curl|hack squat|pec deck|calf press"),
    ("band", r"band"), ("suspension straps", r"\btrx\b"), ("stability ball", r"stability ball|exercise ball|swiss ball"),
    ("medicine ball", r"medicine ball|wall ball|med ball"), ("balance trainer", r"balance trainer|bosu|dome"),
    ("foam roller", r"foam roll"), ("pvc pipe", r"\bpvc\b"), ("plate", r"\bplate\b"), ("plyo box", r"\bbox\b"),
    ("sled", r"\bsled\b"), ("tire", r"\btire\b"), ("battle ropes", r"battle rope"), ("pull-up bar",
                                                                                     r"pull[- ]?up|chin[- ]?up|hanging|toes to bar|muscle up|dead hang"),
    ("dip bars", r"\bdips?\b"), ("bench", r"\bbench\b"), ("rope", r"rope climb"),
]


def equipment_of(name, given=""):
    n = name.lower()
    out = []
    other = re.search(r"dumbbell|kettlebell|band|trx|medicine|pvc|machine|cable|plate|landmine|trap bar|ball", n)
    for canon, pat in EQUIP:
        if canon == "barbell" and other and "barbell" not in n:
            continue
        if re.search(pat, n) and canon not in out:
            out.append(canon)
    for g in re.split(r"[;,،/|]+", given or ""):
        g = g.strip().lower()
        if g and g not in out:
            out.append(g)
    return ";".join(out) if out else "bodyweight"


# ------------------------------------------------------------ templates
# (regex on the lower-cased English name, template, confidence)
RULES = [
    # --- explicit specials first
    (r"curl to (shoulder |front )?press|hammer curl to", "db_curl", 1),
    (r"leg swing|walking front kick", "leg_swing", 1), (r"side bridge", "side_plank", 1),
    (r"wrist extension stretch|forearm stretch", "arm_stretch", 1), (r"chest pass|squat and throw", "medball_slam", 0),
    (r"calf raise to|deadlift to calf|standing machine calf|toe walk", "calf_raise", 1),
    (r"(romanian deadlift|rdl) to high pull", "romanian_deadlift", 0),
    (r"snatch deadlift|snatch-grip deadlift|clean deadlift", "deadlift", 1),
    (r"(kettlebell|dumbbell).*(clean|snatch|jerk)", "kb_clean", 1),
    (r"hip thrusters?|hip raise", "hip_thrust", 1), (r"plank with dumbbell pull through|plank hip dip|body ?saw", "plank", 1),
    (r"bicycle kick", "bicycle_crunch", 0), (r"hip lift march", "glute_bridge", 1), (r"lower body crawl", "bear_crawl", 0),
    (r"lateral bound", "skater_jump", 0), (r"trx hamstring runner", "glute_bridge", 1),
    (r"glute[- ]ham", "glute_ham_raise", 1), (r"cluster", "thruster", 0), (r"partner band jump", "jump_squat", 0),
    (r"(single leg|pistol|glute drop).*squat|single leg glute drop|trx single leg squat", "pistol_squat", 0),
    (r"single arm overhead kettlebell squat", "overhead_squat", 0),
    (r"stability ball (abdominal|seated) twist|full twist", "russian_twist", 0),
    (r"leg crunch|v-pass|seated toe tap|leg pull-in|frog kicks", "v_up", 1),
    (r"leg throw down", "leg_raise", 1), (r"lower back stretch|supine back stretch", "knee_to_chest", 0),
    (r"dumbbell kickbacks?$", "triceps_kickback", 1), (r"cable crossover lat pulldown", "lat_pulldown", 1),
    (r"single arm cable press", "chest_press_standing", 1), (r"trx (t|w|y) deltoid fly|banded y fly", "rear_delt_raise", 1),
    (r"trx hammer pull", "inverted_row", 1), (r"(machine|hammerstrength) (bench|chest)|machine bench", "machine_chest_press", 1),
    (r"smith machine overhead shoulder press", "overhead_press", 1),
    (r"(dumbbell|kettlebell|band|cable).*(shoulder|overhead|front) press|single arm (overhead|kettlebell) press|seated dumbbell front press|kettlebell overhead press|single arm overhead press", "db_shoulder_press", 1),
    (r"turkish get ?up", "turkish_get_up", 1), (r"windmill", "kb_windmill", 1), (r"\bhalo\b", "kb_halo", 1),
    (r"battle rope", "battle_ropes", 1), (r"tire flip", "tire_flip", 1), (r"sled (push|drag|pull)", "sled_push", 1),
    (r"farmer|suitcase carry|waiter walk|carry", "farmer_walk", 1), (r"burpee", "burpee", 1),
    (r"treadmill|\brun\b|sprint", "treadmill_run", 0), (r"\bbike\b|cycling|bicycle(?! crunch)", "bike", 0),
    (r"rowing machine|\browe?r\b", "rower", 1), (r"elliptical", "elliptical", 1),
    (r"foam roll", "foam_roll", 1), (r"rollout|roll out|fallout|ab wheel", "ab_rollout", 1),
    # --- hanging / bars
    (r"toes to bar|hanging (knee|leg|oblique)|windshield wiper.*hang|hanging windshield", "hanging_leg_raise", 1),
    (r"vertical (knee|leg) raise|captain", "hanging_leg_raise", 1),
    (r"pull[- ]?up|chin[- ]?up|muscle up|dead hang|rope climb|scapular pull", "pull_up", 1),
    (r"\bl[- ]sit\b", "l_sit", 1), (r"bench dip|(?<!hip )\bdips?\b", "dip", 1),
    # --- olympic / kettlebell ballistic
    (r"kettlebell swing|\bswing\b", "kb_swing", 1),
    (r"(?<!hip )thruster|wall ball|squat to (shoulder )?press|squat and throw", "thruster", 1),
    (r"(kettlebell|dumbbell).*(clean|snatch)(?!.*(jerk|thruster))", "kb_clean", 1),
    (r"bottoms-up kettlebell clean", "kb_clean", 1),
    (r"clean|snatch|jerk|push press|high pull", "power_clean", 1),
    # --- lower body
    (r"leg press|calf press|heel press", "leg_press", 1), (r"hack squat|machine squat", "squat", 1),
    (r"^(?!.*plank).*leg extension", "leg_extension", 1), (r"quadruped plank with leg", "bird_dog", 0),
    (r"lying (hamstrings? )?curl|prone .*curl|lying leg curl", "lying_leg_curl", 1),
    (r"seated leg curl", "seated_leg_curl", 1),
    (r"standing (leg|loop band hamstring) curl|single leg curl|standing loop band hamstring", "standing_leg_curl", 1),
    (r"stability ball leg curl|ball leg curl", "glute_bridge", 1),
    (r"hip abductor|hip adductor", "hip_abductor_machine", 1),
    (r"kickback machine|glute kickback", "glute_kickback_machine", 0),
    (r"seated .*calf|calf raise.*seated|barbell seated calf", "seated_calf_raise", 1),
    (r"calf raise|calf press|toe walk|reverse calf", "calf_raise", 1),
    (r"pistol", "pistol_squat", 1), (r"cossack", "cossack_squat", 1),
    (r"bulgarian", "bulgarian_split_squat", 1),
    (r"split jump|lunge jump", "split_jump", 1),
    (r"split squat|static lunge|pulse lunge|kneel(ing)? to stand", "split_squat", 1),
    (r"lateral lunge|side lunge|lateral lunge stretch", "lateral_lunge", 1),
    (r"curtsy", "curtsy_lunge", 1), (r"reverse lunge|rear lunge|deficit reverse", "reverse_lunge", 1),
    (r"lunge", "forward_lunge", 1),
    (r"step[- ]?up|step down", "step_up", 1),
    (r"box jump|depth jump|box drop|reverse box jump", "box_jump", 1),
    (r"broad jump|bounds?\b|power skip", "broad_jump", 1), (r"tuck jump", "tuck_jump", 1),
    (r"star jump|jumping jack|plank jack|stance jack", "jumping_jack", 1),
    (r"skips?\b|high knee|butt kick|carioca|grape ?vine|march", "high_knees", 1),
    (r"line hop|cone hop|lateral (box )?(shuffle|jump|bound)|box shuffle|cross jumps|lateral jumps|toe taps",
     "lateral_hop", 1),
    (r"ice skater|skater", "skater_jump", 1),
    (r"jump squat|squat jump|sumo squat jump", "jump_squat", 1),
    (r"wall sit|wall squat", "wall_sit", 1), (r"box squat", "box_squat", 1),
    (r"overhead squat|snatch balance", "overhead_squat", 1), (r"zercher", "squat", 1),
    (r"front squat", "front_squat", 1), (r"goblet", "goblet_squat", 1), (r"sumo squat", "sumo_squat", 1),
    (r"back squat|barbell squat|smith machine squat|pause squat|olympic squat|pulse back squat|landmine squat", "back_squat", 1),
    (r"air squat|bodyweight squat|squat hold|knee up squat|squat side kick|squat with rotation|duck walk", "bodyweight_squat", 1),
    (r"squat", "squat", 1),
    (r"single leg (romanian |rdl|kettlebell )?deadlift|single leg rdl|airplane", "single_leg_rdl", 1),
    (r"stiff-legged barbell good morning", "good_morning", 1), (r"romanian|\brdl\b|stiff[- ]leg", "romanian_deadlift", 1),
    (r"good morning|hip hinge", "good_morning", 1),
    (r"pull through", "cable_pull_through", 1),
    (r"deadlift|rack pull", "deadlift", 1),
    (r"hip thrust|hip raise|glute thrust", "hip_thrust", 1),
    (r"glute bridge|hip bridge|frog pump|bridge|hip lift march|trx hip drop", "glute_bridge", 1),
    (r"glute ham|nordic", "glute_ham_raise", 1),
    (r"reverse hyper", "back_extension", 1), (r"back extension|hyperextension", "back_extension", 1),
    (r"superman|prone (i|t|w|y)[’'`]?s|australian crawl|swimmer", "superman", 1),
    (r"donkey|kickback(?!.*tricep)|glute raise|rear glute", "donkey_kick", 1),
    (r"fire hydrant|hip circle", "fire_hydrant", 1), (r"clam", "clam", 1),
    (r"side leg (raise|kick|lift)|side-lying hip abduction|lying .*abduction|side leg hip circle", "side_leg_raise", 1),
    (r"(standing|cable|band).*hip abduction|lateral walk|side step|lateral leg swing|standing leg side", "hip_abduction_standing", 1),
    (r"hip adduction", "hip_adduction_standing", 1),
    (r"hip extension|standing kickback|cable kickback|straight leg kickback|single leg kickback", "standing_kickback", 1),
    (r"leg swing|walking front kick|hurdle", "leg_swing", 1),
    (r"knee drive|hip flexion|standing (elbow to knee|oblique) crunch", "standing_knee_raise", 1),
    # --- chest
    (r"pull ?over", "pullover", 1),
    (r"skull ?crusher|tate press|lying tricep", "skull_crusher", 1),
    (r"(dumbbell|kettlebell).*(bench|floor) press|dumbbell .*press.*(incline|decline)|squeeze press|larson", "db_bench_press", 1),
    (r"bench press|floor press|close-grip bench|smith machine .*(bench|decline|incline) press|smith machine decline", "bench_press", 1),
    (r"machine reverse fly", "reverse_fly_machine", 1),
    (r"rear delt|reverse fly|back fly|rear deltoid", "rear_delt_raise", 1),
    (r"pec deck|machine fly", "pec_deck", 1), (r"overhead fly", "lateral_raise", 0), (r"trx chest fly", "chest_press_standing", 1),
    (r"crossover (flat|incline) bench fly", "db_fly", 1),
    (r"cable crossover|crossover fly|cable fly|low cable|single arm cable crossover|band pec fly|band single arm fly", "cable_crossover", 1),
    (r"\bfly\b|flye|around the worlds|hug a ball", "db_fly", 1),
    (r"(machine|hammerstrength|freemotion).*(chest|bench|shoulder) press|machine shoulder press", "machine_chest_press", 1),
    (r"chest press|svend|chest pass|standing chest", "chest_press_standing", 1),
    (r"handstand|pike push", "push_up", 0),
    (r"push[- ]?ups?|pushup", "push_up", 1),
    # --- shoulders
    (r"arnold", "arnold_press", 1), (r"landmine press", "landmine_press", 1),
    (r"overhead press|military|shoulder press|front press|seated barbell shoulder|behind the neck", "overhead_press", 0),
    (r"face pull", "face_pull", 1),
    (r"external rotation|internal rotation|cuban", "external_rotation", 1),
    (r"rear delt|reverse fly|back fly|bent over reverse fly|rear deltoid", "rear_delt_raise", 1),
    (r"lateral raise|side lateral|shoulder raise", "lateral_raise", 1),
    (r"front raise|forward raise|plate raise|front plate", "front_raise", 1),
    (r"upright row|high pull", "upright_row", 1), (r"shrug", "shrug", 1),
    (r"arm circle", "arm_circles", 1),
    # --- back
    (r"straight[- ]arm", "straight_arm_pulldown", 1),
    (r"pulldown|pull down|pull-down", "lat_pulldown", 1),
    (r"inverted row|ring row|trx row|australian|trx power pull|trx clock|trx swimmer", "inverted_row", 1),
    (r"renegade", "plank", 1),
    (r"seated (cable )?row|cable row|loop band seated", "cable_row", 1),
    (r"machine row|hammerstrength .*row|iso row|high row", "machine_row", 1),
    (r"t-bar|landmine row|meadow", "tbar_row", 1),
    (r"(dumbbell|kettlebell|shotgun|gorilla|incline dumbbell) rows?|kettlebell alternating row|single arm.*row|bird dog row", "db_row", 1),
    (r"\brows?\b", "barbell_row", 1),
    # --- arms
    (r"preacher|spider curl", "preacher_curl", 1), (r"concentration", "concentration_curl", 1),
    (r"overhead cable (bicep )?curl", "overhead_cable_curl", 1),
    (r"wrist curl|wrist extension", "wrist_curl", 1),
    (r"(barbell|ez[- ]?bar|cable).*curl|21|drag curl", "barbell_curl", 1),
    (r"curl", "db_curl", 1),
    (r"pushdown|push down|tricep extension.*cable|cable.*tricep|machine tricep", "triceps_pushdown", 1),
    (r"kickback", "triceps_kickback", 1),
    (r"overhead .*extension|tricep extension|tricep press|triceps extension|tricep overhead", "overhead_triceps_extension", 1),
    # --- core
    (r"woodchop|wood chop|chopper", "woodchop", 1), (r"pallof", "pallof_press", 1),
    (r"russian twist|seated twist|v-sit cross|torture twist", "russian_twist", 1),
    (r"core rotation|core twist|ab twist|resisted rotation|landmine rotation|standing cable core", "standing_twist", 1),
    (r"side plank|side bridge|side star", "side_plank", 1),
    (r"mountain climber|climbers|cross body mountain", "mountain_climber", 1),
    (r"bear crawl", "bear_crawl", 1), (r"crab|reverse plank|reverse table", "reverse_plank", 1),
    (r"downward dog push", "downward_dog", 1), (r"walkout to push", "walkout", 1),
    (r"pike|knee tuck|pull in|pull-in", "pike", 1),
    (r"inchworm|walkout|walk out", "walkout", 1),
    (r"plank", "plank", 1),
    (r"dead bug", "dead_bug", 1), (r"bird dog", "bird_dog", 1),
    (r"bicycle", "bicycle_crunch", 1), (r"v-?up|jackknife|v-sit|tuck crunch|cocoon", "v_up", 1),
    (r"reverse crunch", "reverse_crunch", 1),
    (r"flutter|scissor", "flutter_kick", 1),
    (r"windshield", "windshield_wiper", 1),
    (r"leg raise|leg lift|leg toss|leg throw|leg pull", "leg_raise", 1),
    (r"sit[- ]?up", "sit_up", 1), (r"crunch|toe touch|heel touch|toe tap", "crunch", 1),
    (r"side bend|lateral bend|helicopter", "arm_stretch", 1),
    (r"stomach vacuum|breathing", "standing_still", 0),
    # --- stretches / mobility / yoga
    (r"cat cow", "cat_cow", 1), (r"child", "child_pose", 1), (r"cobra|up dog|upward dog", "cobra", 1),
    (r"downward dog|down dog", "downward_dog", 1), (r"pigeon|figure four", "pigeon_pose", 1),
    (r"butterfly stretch|frog stretch", "butterfly_stretch", 1),
    (r"knee to chest", "knee_to_chest", 1),
    (r"hip flexor|couch stretch|shin box", "hip_flexor_stretch", 1),
    (r"quad(ricep)? stretch|standing quad", "quad_stretch_standing", 1),
    (r"calf stretch|deficit calf", "calf_stretch", 1),
    (r"seated forward bend|pancake|center split|fan stretch|hamstring stretch|leg up stretch", "seated_forward_bend", 1),
    (r"forward bend|standing splits|lunge to hamstring", "standing_forward_bend", 1),
    (r"stretch|open book|reach behind|t-spine|wall slide|shoulder flexion|around the world|iron cross|chest expansion", "arm_stretch", 1),
    (r"warrior", "warrior_pose", 1), (r"tree pose", "tree_pose", 1),
    (r"medicine ball slam|slam", "medball_slam", 1),
    (r"punch", "chest_press_standing", 1),
    (r"plate (flip|pinch)", "farmer_walk", 0),
    (r"stir the pot", "plank", 1), (r"hip flow|ankle circle|point and flex", "standing_still", 0),
    (r"wheelbarrow", "push_up", 0),
]

# Rules for the 3.2.0 exercise table; tried before RULES.  Names in that table
# say "Suspension" for TRX and "Dowel" for PVC, which infer_template also maps.
TABLE_RULES = [
    (r"butt scoot", "butt_scoot", 1),
    (r"nordic|glute[- ]ham raise$|glute ham raise$", "glute_ham_raise", 1),
    (r"glute ham raise sit", "sit_up", 0),
    (r"standing toe touch", "standing_forward_bend", 1),
    (r"shoulder dislocate|shoulder cars", "arm_circles", 0), (r"hip cars", "hip_circle_standing", 1),
    (r"triceps? kickback", "triceps_kickback", 1),
    (r"lying (dumbbell )?triceps? extension", "skull_crusher", 1),
    (r"reverse machine fly", "reverse_fly_machine", 1),
    (r"machine biceps curl", "preacher_curl", 1),
    (r"smith machine (shoulder|overhead) press", "overhead_press", 1),
    (r"smith machine (close grip )?bench press|smith machine (incline|decline) press", "bench_press", 1),
    (r"hip (abduction|adduction) machine", "hip_abductor_machine", 1),
    (r"standing side leg raise", "hip_abduction_standing", 1),
    (r"hanging pike", "hanging_leg_raise", 1), (r"seated knee tuck", "v_up", 0),
    (r"plank jack", "plank", 1),
    (r"(band |standing band |mini band )?(leg|hamstring) curl", None, 0),   # resolved below by the name
    (r"world's greatest stretch", "forward_lunge", 0),
    (r"side lying groin stretch", "butterfly_stretch", 0),
    (r"close grip dumbbell press", "db_bench_press", 1), (r"\bjm press", "bench_press", 0),
    (r"jumping lunge", "split_jump", 1),
    (r"hamstring slide", "glute_bridge", 0),
    (r"monster walk|lateral walk", "hip_abduction_standing", 0),
    (r"spider crawl", "bear_crawl", 0),
    (r"wrist roller", "front_raise", 0), (r"finger curl|hand gripper|wrist rotation", "wrist_curl", 0),
    (r"kettlebell figure 8", "kb_swing", 0),
    (r"hug knees to chest", "knee_to_chest", 1),
    (r"knee across the body|supine spinal twist", "knee_to_chest", 0),
    (r"seated spinal twist", "russian_twist", 0),
    (r"hollow body", "leg_raise", 0), (r"dragon flag", "leg_raise", 0),
    (r"tibialis raise", "calf_raise", 0),
    (r"shadow boxing", "chest_press_standing", 0),
    (r"90/90 hip|figure[- ]4 glute", "pigeon_pose", 1),
    (r"seated barbell press|\bz press", "overhead_press", 0),
    (r"suspension biceps curl", "inverted_row", 0),
    (r"cable pull[- ]?over", "straight_arm_pulldown", 1),
    (r"stair climber", "step_up", 0), (r"ski ergometer", "straight_arm_pulldown", 0),
    (r"^running$|brisk walking", "treadmill_run", 0), (r"^swimming$", "superman", 0),
    (r"man maker|devil press", "burpee", 0),
    (r"lying neck flexion", "crunch", 0), (r"lying neck extension", "superman", 0),
    (r"neck (stretch|isometric)|chin tuck", "standing_still", 0),
    (r"pogo hop", "lateral_hop", 0),
    (r"thread the needle", "cat_cow", 0), (r"adductor rockback", "child_pose", 0),
    (r"knee to wall ankle", "calf_stretch", 0),
    (r"jefferson curl", "standing_forward_bend", 0),
    (r"reverse snow angel|prone y t w|reverse leg crossover", "superman", 0),
    (r"dumbbell scaption|cable y raise", "front_raise", 0),
    (r"incline y raise|band y raise|band overhead pull apart", "rear_delt_raise", 0),
    (r"wall angel", "arm_stretch", 0),
    (r"suspension hip drop", "side_plank", 0),
    (r"braced frog kick", "reverse_crunch", 0),
    (r"slow climber|speed climber", "mountain_climber", 1),
    (r"band side plank row", "side_plank", 0), (r"band plank row", "plank", 0),
    (r"balance trainer toe tap", "high_knees", 0), (r"lateral floor toe tap", "lateral_hop", 0),
    (r"lying toe tap", "dead_bug", 0), (r"mini band toe touch", "v_up", 0),
    (r"dowel helicopter", "standing_twist", 0),
    (r"mini band triceps press", "triceps_pushdown", 0),
    (r"cobra triceps", "cobra", 0),
    (r"isometric biceps", "db_curl", 0),
    (r"suspension (clock|power) pull", "inverted_row", 0),
    (r"scapular retraction|shoulder squeeze", "rear_delt_raise", 0), (r"archer pull$", "face_pull", 0),
    (r"cross ?over jump|front back cross jump", "lateral_hop", 0),
    (r"partner hook squat", "squat", 0), (r"partner wall sit and triceps dip", "wall_sit", 0),
    (r"partner plank hold and jump", "plank", 0),
    (r"partner wheelbarrow push", "push_up", 0),
    (r"partner handstand", "push_up", 0),
    (r"partner banded reverse leg raise", "superman", 0),
    (r"single leg cycles", "flutter_kick", 0),
    (r"banded leg drive", "standing_knee_raise", 0),
    (r"mini band hip flexor", "standing_knee_raise", 0),
    (r"bottoms up kettlebell press", "db_shoulder_press", 1),
    (r"incline cable fly", "db_fly", 1),
    (r"barbell hack squat", "deadlift", 0),
    (r"safety bar squat", "back_squat", 1),
    (r"suspension (y|t|w) deltoid fly", "rear_delt_raise", 1),
    (r"suspension chest fly", "chest_press_standing", 1),
]

LEG_CURL = [(r"standing|stand", "standing_leg_curl"), (r"seated", "seated_leg_curl"),
            (r"suspension|trx|ball", "glute_bridge"), (r"", "lying_leg_curl")]

# template -> movement patterns of the table it is consistent with
TPL_PATTERNS = {
    "squat": "squat", "back_squat": "squat", "front_squat": "squat", "goblet_squat": "squat", "box_squat": "squat",
    "sumo_squat": "squat", "overhead_squat": "squat", "bodyweight_squat": "squat mobility", "jump_squat": "squat",
    "wall_sit": "squat", "leg_press": "squat isolation", "pistol_squat": "squat lunge", "thruster": "squat vertical_push",
    "forward_lunge": "lunge mobility", "reverse_lunge": "lunge", "split_squat": "lunge", "curtsy_lunge": "lunge",
    "lateral_lunge": "lunge mobility", "bulgarian_split_squat": "lunge", "step_up": "lunge squat",
    "deadlift": "hinge", "romanian_deadlift": "hinge", "single_leg_rdl": "hinge", "good_morning": "hinge",
    "hip_thrust": "hinge", "glute_bridge": "hinge isolation", "kb_swing": "hinge", "power_clean": "hinge vertical_push squat vertical_pull",
    "kb_clean": "hinge vertical_push", "back_extension": "hinge", "superman": "hinge isolation",
    "bench_press": "horizontal_push", "db_bench_press": "horizontal_push", "push_up": "horizontal_push vertical_push",
    "chest_press_standing": "horizontal_push", "machine_chest_press": "horizontal_push vertical_push", "dip": "horizontal_push vertical_push",
    "overhead_press": "vertical_push", "db_shoulder_press": "vertical_push", "arnold_press": "vertical_push",
    "landmine_press": "vertical_push", "pull_up": "vertical_pull", "lat_pulldown": "vertical_pull",
    "straight_arm_pulldown": "vertical_pull isolation", "barbell_row": "horizontal_pull", "db_row": "horizontal_pull",
    "cable_row": "horizontal_pull", "machine_row": "horizontal_pull", "tbar_row": "horizontal_pull",
    "inverted_row": "horizontal_pull", "face_pull": "horizontal_pull isolation", "upright_row": "vertical_pull horizontal_pull isolation",
    "plank": "anti_rotation", "side_plank": "anti_rotation", "pallof_press": "anti_rotation rotation",
    "russian_twist": "rotation", "woodchop": "rotation", "standing_twist": "rotation", "bicycle_crunch": "rotation isolation anti_rotation",
    "mountain_climber": "anti_rotation rotation cardio", "farmer_walk": "carry", "sled_push": "carry squat",
    "bear_crawl": "carry", "high_knees": "cardio", "jumping_jack": "cardio", "treadmill_run": "cardio",
    "bike": "cardio", "rower": "cardio", "elliptical": "cardio", "battle_ropes": "cardio", "lateral_hop": "cardio squat",
    "skater_jump": "cardio lunge", "box_jump": "squat", "broad_jump": "squat cardio lunge", "tuck_jump": "squat",
    "burpee": "squat cardio",
}

PATTERN_FALLBACK = {
    "squat": "squat", "lunge": "split_squat", "hinge": "romanian_deadlift", "horizontal_push": "push_up",
    "vertical_push": "db_shoulder_press", "horizontal_pull": "db_row", "vertical_pull": "lat_pulldown",
    "anti_rotation": "plank", "rotation": "standing_twist", "carry": "farmer_walk", "cardio": "high_knees",
    "mobility": "arm_stretch",
}

# table equipment tags -> words the templates look for
TAG_WORDS = {
    "balance_trainer": "balance trainer", "suspension": "suspension straps;trx", "pullup_bar": "pull-up bar",
    "ez_bar": "ez bar", "trap_bar": "trap bar", "foam_roller": "foam roller", "smith": "smith machine",
    "box": "plyo box", "plate": "plate", "landmine": "landmine", "sled": "sled", "bench": "bench",
    "machine": "machine", "cable": "cable", "band": "band", "kettlebell": "kettlebell", "dumbbell": "dumbbell",
    "barbell": "barbell",
}

# muscles of the target-less cardio rows, per template
CARDIO_MUSCLES = {
    "battle_ropes": "front_delts;side_delts;abs", "chest_press_standing": "front_delts;abs;obliques",
    "rower": "lats;upper_back;quads", "straight_arm_pulldown": "lats;triceps;abs", "superman": "lats;upper_back;front_delts",
    "jumping_jack": "quads;calves;side_delts", "mountain_climber": "abs;quads;front_delts",
}


GROUP_FALLBACK = {
    "abs": "crunch", "lower_back": "back_extension", "back": "barbell_row", "quads": "squat",
    "adductors": "hip_adduction_standing", "glutes": "glute_bridge", "calves": "calf_raise",
    "hamstrings": "romanian_deadlift", "shoulders": "db_shoulder_press", "traps": "shrug", "chest": "push_up",
    "abductors": "hip_abduction_standing", "triceps": "triceps_pushdown", "forearms": "wrist_curl",
    "biceps": "db_curl",
}

FA_GROUP = {
    "شکم": "abs", "پایین کمر": "lower_back", "پشت": "back", "چهارسر ران": "quads", "داخل ران": "adductors",
    "باسن": "glutes", "ساق پا": "calves", "پشت پا": "hamstrings", "سرشانه": "shoulders", "کول": "traps",
    "سینه": "chest", "خارج ران": "abductors", "پشت بازو": "triceps", "ساعد": "forearms", "جلو بازو": "biceps",
}

GROUP_KEYS = {
    "abs": ["abs"], "lower_back": ["lower_back"], "back": ["lats", "upper_back"], "quads": ["quads"],
    "adductors": ["adductors"], "glutes": ["glutes"], "calves": ["calves"], "hamstrings": ["hamstrings"],
    "shoulders": ["front_delts", "side_delts"], "traps": ["traps"], "chest": ["mid_chest"],
    "abductors": ["abductors"], "triceps": ["triceps"], "forearms": ["forearms"], "biceps": ["biceps"],
}

# typical secondary muscles per template (used when the source has none)
SECONDARY = {
    "back_squat": ["glutes", "hamstrings", "lower_back"], "squat": ["glutes", "hamstrings"],
    "front_squat": ["glutes", "abs"], "goblet_squat": ["glutes"], "deadlift": ["glutes", "lower_back", "traps", "forearms"],
    "romanian_deadlift": ["glutes", "lower_back"], "bench_press": ["front_delts", "triceps"],
    "db_bench_press": ["front_delts", "triceps"], "push_up": ["front_delts", "triceps", "abs"],
    "overhead_press": ["triceps", "traps"], "db_shoulder_press": ["triceps"], "barbell_row": ["biceps", "rear_delts"],
    "db_row": ["biceps", "rear_delts"], "pull_up": ["biceps", "forearms"], "lat_pulldown": ["biceps"],
    "forward_lunge": ["glutes", "hamstrings"], "reverse_lunge": ["glutes", "hamstrings"], "hip_thrust": ["hamstrings"],
    "glute_bridge": ["hamstrings"], "dip": ["mid_chest", "front_delts"], "kb_swing": ["glutes", "lower_back"],
}


APPROX = (r"handstand|skip|carioca|grape ?vine|crawl|sprint|cycles|hip flow|butt scoot|rocket|figure four squat|clock|"
          r"swimmer|around the world|iron cross|cuban|traveling|rolling|kipping|muscle up|archer|butterfly pull|"
          r"21|waiter|no money|pjr|larson|svend|chest expansion|reach behind|open book|t-spine|stir the pot|"
          r"plate flip|plate pinch|step down|duck walk|kneeling squat|lateral walk|side step|hip drop|hesitation|"
          r"lunge to lateral reach|ankle grab|shotgun|gorilla|bird dog row|curl handoff|hi-five|toss|throw|"
          r"star plank|leg crossover|up and down|surrender|hip throw|power pull|rotation \d|leg drive|sprinter|"
          r"crossing balance|figure four|cobra triceps|helicopter|scaption|halo to|cross jab|knee up|side kick|"
          r"with rotation|lateral dome|bar assisted|front-back|hurdle|walk out plank|dome planks|reverse leg crossover|"
          r"loop band shoulder squeeze|scapular retraction|shoulder squeeze|archer pull|wall knee|triple knee|"
          r"butt kick|hip lift march|bridge walk|up up down down|side to side|lateral cone|box shuffle|toe taps|"
          r"heel press|seated point|ankle circles|vacuum|plank jack|stance jack|power skips|bounds|airplane|"
          r"overhead weighted crunch|single leg crunches|frog kicks|speed climbers|slow climbers|walking side kicks")


def name_forms(name):
    n = name.lower().replace("’", "'")
    n2 = re.sub(r"\s+", " ", n.replace("-", " "))    # "Cat-Cow" also matches "cat cow"
    n3 = n2.replace("suspension", "trx").replace("dowel", "pvc")
    return n, n2, n3


def infer_template(name, rules=None):
    forms = name_forms(name)
    for pat, tplname, conf in (rules or RULES):
        if any(re.search(pat, f) for f in forms):
            return tplname, conf, pat
    return None, 0, ""


def infer_table_template(name):
    """3.2.0 table rules first, then the general rules."""
    t, conf, pat = infer_template(name, TABLE_RULES)
    if pat and t is None:          # leg / hamstring curls: pick the body position
        n = name_forms(name)[2]
        for p2, t2 in LEG_CURL:
            if re.search(p2, n):
                return t2, 1, pat
    if t is not None:
        return t, conf, pat
    return infer_template(name)


def equipment_from_tags(name, tags):
    """Equipment words for the templates from the table's equipment_tags,
    plus implements the name spells out."""
    n = name_forms(name)[2]
    out = []
    for tg in re.split(r"[;,]+", tags or ""):
        tg = tg.strip().lower()
        if not tg or tg in ("none", "bodyweight"):
            continue
        if tg == "ball":
            med = re.search(r"medicine|wall ball|toss|throw|chest pass|slam|weighted|partner (russian|medicine)", n)
            words = "medicine ball" if med else "stability ball"
        else:
            words = TAG_WORDS.get(tg, tg.replace("_", " "))
        for w in words.split(";"):
            if w not in out:
                out.append(w)
    if "pvc" in n and "pvc pipe" not in out:
        out.append("pvc pipe")
    for w in equipment_of(name).split(";"):
        if w == "bodyweight" or w in out:
            continue
        # the tags are authoritative for the main implement; the name adds the rest
        if w in ("barbell",) and any(k in out for k in ("dumbbell", "kettlebell", "band", "cable", "landmine",
                                                          "trap bar", "ez bar", "medicine ball", "pvc pipe")):
            continue
        out.append(w)
    return ";".join(out) if out else "bodyweight"


def fix_by_equipment(tplname, equip, name):
    """Correct name-rule templates whose implement contradicts the tags."""
    e = set(equip.split(";"))
    n = name.lower()
    if tplname == "bench_press" and e & {"dumbbell", "kettlebell"} and not e & {"barbell", "smith machine", "ez bar"}:
        return "db_bench_press"
    if tplname == "db_bench_press" and e & {"barbell", "smith machine"} and not e & {"dumbbell", "kettlebell"}:
        return "bench_press"
    if tplname == "barbell_curl" and e & {"dumbbell", "kettlebell"} and not e & {"barbell", "ez bar", "cable"} \
            and "drag" not in n:
        return "db_curl"
    if tplname == "db_curl" and e & {"barbell", "ez bar", "cable"} and not e & {"dumbbell", "kettlebell", "band"}:
        return "barbell_curl"
    if tplname == "squat" and "barbell" in e and not re.search(r"hack|zercher|kneeling", n):
        return "back_squat"
    return tplname


def refine_muscles(group, name, listed):
    """Primary muscle keys from the group + name; secondaries from the list."""
    n = name.lower()
    prim = list(GROUP_KEYS.get(group, []))
    if group == "chest":
        if "incline" in n or "low cable" in n or "low to high" in n:
            prim = ["upper_chest", "mid_chest"]
        elif "decline" in n or "dip" in n or "high cable" in n:
            prim = ["lower_chest", "mid_chest"]
        else:
            prim = ["mid_chest", "upper_chest", "lower_chest"] if "fly" in n or "press" in n or "push" in n else ["mid_chest"]
    if group == "shoulders":
        if re.search(r"lateral|side|upright|\by\b", n):
            prim = ["side_delts"]
        elif re.search(r"rear|reverse fly|back fly|face pull|external|pull apart|t deltoid|w deltoid", n):
            prim = ["rear_delts"]
        elif re.search(r"front raise|forward raise|plate raise", n):
            prim = ["front_delts"]
        else:
            prim = ["front_delts", "side_delts"]
    if group == "abs" and re.search(r"oblique|twist|side|russian|woodchop|wood chop|rotation|windmill|wiper|bicycle", n):
        prim = ["obliques", "abs"]
    if group == "back" and re.search(r"row|face|rear", n):
        prim = ["upper_back", "lats"]
    sec = []
    for k in M.canon(";".join(listed)):
        if k not in prim and k not in sec:
            sec.append(k)
    return prim, sec


def build_rows(records):
    rows, review, seen = [], [], {}
    for rec in records:
        name = rec["name_en"].strip()
        slug = str_slug(name)
        if slug in seen:
            seen[slug] += 1
            slug = f"{slug}-{seen[slug]}"
        else:
            seen[slug] = 1
        group = rec.get("group", "")
        tplname, conf, pat = infer_template(name)
        note = ""
        if rec.get("template"):
            tplname, conf, note = rec["template"], 1, "given"
        if tplname is None:
            tplname = GROUP_FALLBACK.get(group, "standing_still")
            conf = -1
            note = "no name rule; muscle-group fallback"
        prim, sec = refine_muscles(group, name, rec.get("listed", []))
        if rec.get("prim"):
            prim = M.canon(rec["prim"]) or prim
        if rec.get("sec"):
            sec = [k for k in M.canon(rec["sec"]) if k not in prim]
        if not sec:
            sec = [k for k in SECONDARY.get(tplname, []) if k not in prim]
        if re.search(APPROX, name.lower()):
            conf = min(conf, 0)
            note = (note + "; " if note else "") + "stand-in pose for a complex or travelling drill"
        partner = "partner" in name.lower()
        if partner:
            conf = min(conf, 0)
            note = (note + "; " if note else "") + "partner drill shown solo"
        match = {1: "rule", 0: "approx", -1: "fallback"}[max(-1, min(1, conf))]
        row = dict(slug=slug, name_en=name, muscle_group=group, equipment=equipment_of(name, rec.get("equipment", "")),
                   template=tplname, muscles=";".join(prim), muscles2=";".join(sec), match=match, note=note)
        rows.append(row)
        if match != "rule":
            review.append(dict(slug=slug, name_en=name, template=tplname, match=match,
                               reason=note or f"approximate rule: {pat}"))
    return rows, review


def from_json(path):
    d = json.load(open(path, encoding="utf-8"))
    out = []
    for e in d["exercises"]:
        out.append(dict(name_en=e["name_en"], group=FA_GROUP.get(e.get("muscle_group", ""), ""),
                        listed=e.get("listed_muscles") or []))
    return out


TABLE_MUSCLE = {"front_delt": "front_delts", "side_delt": "side_delts", "rear_delt": "rear_delts",
                "chest": "mid_chest", "tibialis": ""}


def table_muscles(text):
    parts = []
    for p in re.split(r"[;,]+", text or ""):
        p = p.strip().lower()
        p = TABLE_MUSCLE.get(p, p)
        if p:
            parts.append(p)
    return M.canon(";".join(parts))


def from_csv(path):
    out = []
    for r in csv.DictReader(open(path, encoding="utf-8-sig")):
        grp = M.canon(r.get("muscle", ""))
        g = ""
        txt = (r.get("muscle") or "").lower()
        for k, keys in GROUP_KEYS.items():
            if k.replace("_", " ") in txt or (grp and grp[0] in keys):
                g = k
                break
        out.append(dict(id=r.get("id", ""), name_en=r["name_en"], group=g, muscle=txt,
                        prim=r.get("target_muscles", ""), sec=r.get("secondary_targets", ""),
                        tags=r.get("equipment_tags", "") or r.get("equipment", ""),
                        pattern=(r.get("pattern") or "").strip(), force=(r.get("force") or "").strip(),
                        mechanic=(r.get("mechanic") or "").strip(), listed=[], template=r.get("template", "")))
    return out


def build_table_rows(records):
    """Work list rows for the exercise table (has id, pattern, force, mechanic, tags).

    key = Str::slug(name_en); a later row whose key is taken gets <key>-<id>."""
    rows, review, seen = [], [], set()
    for rec in records:
        name = rec["name_en"].strip()
        key = str_slug(name)
        if key in seen:
            key = f"{key}-{rec['id']}"
        seen.add(key)
        pattern = rec.get("pattern", "")
        equip = equipment_from_tags(name, rec.get("tags", ""))
        tplname, conf, pat = infer_table_template(name)
        note = ""
        if rec.get("template"):
            tplname, conf, note = rec["template"], 1, "given"
        if tplname is None:
            tplname = PATTERN_FALLBACK.get(pattern) or GROUP_FALLBACK.get(rec.get("group", ""), "standing_still")
            if pattern == "isolation":
                tplname = GROUP_FALLBACK.get(rec.get("group", ""), "standing_still")
            conf = -1
            note = f"no name rule; fallback from pattern {pattern or '-'}"
        fixed = fix_by_equipment(tplname, equip, name)
        if fixed != tplname:
            note = (note + "; " if note else "") + f"{tplname} -> {fixed} by equipment"
            tplname = fixed
        if conf == 1 and pattern and tplname in TPL_PATTERNS and pattern not in TPL_PATTERNS[tplname].split() \
                and pattern not in ("isolation", "mobility"):
            conf = 0
            note = (note + "; " if note else "") + f"template {tplname} vs table pattern {pattern}"
        prim, sec = refine_muscles(rec.get("group", ""), name, [])
        tp = table_muscles(rec.get("prim", ""))
        if tp:
            if tp == ["mid_chest"] and prim and set(prim) <= {"upper_chest", "mid_chest", "lower_chest"}:
                tp = prim
            elif "mid_chest" in tp and re.search(r"incline|low to high|low cable", name.lower()):
                tp = ["upper_chest" if k == "mid_chest" else k for k in tp]
            elif "mid_chest" in tp and re.search(r"decline|\bdips?\b", name.lower()):
                tp = ["lower_chest" if k == "mid_chest" else k for k in tp]
            prim = tp
        elif rec.get("muscle") in ("cardio", "mobility", "fullbody", "legs"):
            prim = (CARDIO_MUSCLES.get(tplname) or "quads;glutes;calves").split(";")
        sec = [k for k in table_muscles(rec.get("sec", "")) if k not in prim]
        if not sec:
            sec = [k for k in SECONDARY.get(tplname, []) if k not in prim]
        if re.search(APPROX, name.lower()):
            conf = min(conf, 0)
            note = (note + "; " if note else "") + "stand-in pose for a complex or travelling drill"
        if "partner" in name.lower():
            conf = min(conf, 0)
            note = (note + "; " if note else "") + "partner drill shown solo"
        view = ""
        if tplname in ("bulgarian_split_squat", "split_squat", "forward_lunge", "reverse_lunge", "split_jump",
                       "step_up") and "barbell" in equip.split(";") and "overhead" not in name.lower():
            view = "3q"        # a back-loaded bar seen end-on from the side hides the head
        match = {1: "rule", 0: "approx", -1: "fallback"}[max(-1, min(1, conf))]
        row = dict(id=rec.get("id", ""), slug=key, name_en=name, muscle_group=rec.get("group", ""),
                   pattern=pattern, force=rec.get("force", ""), mechanic=rec.get("mechanic", ""),
                   equipment=equip, template=tplname, view=view, muscles=";".join(prim), muscles2=";".join(sec),
                   match=match, note=note)
        rows.append(row)
        if match != "rule":
            review.append(dict(slug=key, name_en=name, template=tplname, match=match,
                               reason=note or f"approximate rule: {pat}"))
    return rows, review


FIELDS = ["slug", "name_en", "muscle_group", "equipment", "template", "muscles", "muscles2", "match", "note"]
TABLE_FIELDS = ["id", "slug", "name_en", "muscle_group", "pattern", "force", "mechanic", "equipment", "template",
                "view", "muscles", "muscles2", "match", "note"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json")
    ap.add_argument("--csv")
    ap.add_argument("--out", required=True)
    ap.add_argument("--review", required=True)
    a = ap.parse_args()
    recs = from_json(a.json) if a.json else from_csv(a.csv)
    table = bool(recs) and "pattern" in recs[0] and any(r.get("id") for r in recs)
    rows, review = build_table_rows(recs) if table else build_rows(recs)
    from . import templates
    for r in rows:
        if r["template"] not in templates.REG:
            raise SystemExit(f"unknown template {r['template']} for {r['name_en']}")
    with open(a.out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=TABLE_FIELDS if table else FIELDS)
        w.writeheader()
        w.writerows(rows)
    with open(a.review, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["slug", "name_en", "template", "match", "reason"])
        w.writeheader()
        w.writerows(review)
    from collections import Counter
    print(len(rows), "rows;", len(review), "to review;", Counter(r["match"] for r in rows))
    print(Counter(r["template"] for r in rows).most_common(12))


if __name__ == "__main__":
    main()
