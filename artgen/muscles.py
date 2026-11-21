"""Muscle names -> the 22 highlight keys."""
import re

from .paint import MUSCLES

# words (English and Persian) -> keys
ALIASES = [
    (r"upper chest|incline chest|clavicular|بالا ?سینه", ["upper_chest"]),
    (r"lower chest|decline chest|پایین ?سینه", ["lower_chest"]),
    (r"chest|pec|سینه", ["mid_chest"]),
    (r"front delt|anterior delt|جلو ?سرشانه", ["front_delts"]),
    (r"side delt|lateral delt|medial delt|کنار ?سرشانه", ["side_delts"]),
    (r"rear delt|posterior delt|پشت ?سرشانه", ["rear_delts"]),
    (r"shoulder|delt|سرشانه|شانه", ["front_delts", "side_delts"]),
    (r"bicep|جلو ?بازو", ["biceps"]),
    (r"tricep|پشت ?بازو", ["triceps"]),
    (r"forearm|grip|wrist|brachiorad|ساعد", ["forearms"]),
    (r"trap|کول|ذوزنقه", ["traps"]),
    (r"rhomboid|upper back|mid back|middle back|میانه پشت|بالا ?پشت", ["upper_back"]),
    (r"lat|latissimus|زیربغل|^back$|^پشت$", ["lats", "upper_back"]),
    (r"lower back|erector|spinal|پایین ?کمر|کمر", ["lower_back"]),
    (r"oblique|مورب|پهلو", ["obliques"]),
    (r"abs|abdom|core|rectus|شکم", ["abs"]),
    (r"glute|butt|باسن|سرین", ["glutes"]),
    (r"quad|چهارسر|جلو ?ران", ["quads"]),
    (r"hamstring|پشت ?پا|پشت ?ران", ["hamstrings"]),
    (r"adductor|inner thigh|داخل ?ران", ["adductors"]),
    (r"abductor|outer thigh|hip abd|خارج ?ران|ابداکتور", ["abductors"]),
    (r"calf|calves|soleus|gastro|ساق", ["calves"]),
    (r"neck|گردن", ["neck"]),
    (r"hip flexor|خم.?کننده", ["quads"]),
]


def canon(text):
    """Free text muscle list -> ordered unique keys."""
    out = []
    if not text:
        return out
    for part in re.split(r"[;,،/|]+", str(text)):
        p = part.strip().lower()
        if not p:
            continue
        if p in MUSCLES:
            keys = [p]
        else:
            keys = []
            for pat, ks in ALIASES:
                if re.search(pat, p):
                    keys = ks
                    break
        for k in keys:
            if k not in out:
                out.append(k)
    return out


def highlight(row):
    prim = [k for k in (row.get("muscles") or "").split(";") if k in MUSCLES]
    sec = [k for k in (row.get("muscles2") or "").split(";") if k in MUSCLES and k not in prim]
    return prim + sec, [1.0] * len(prim) + [0.5] * len(sec)
