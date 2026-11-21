#!/bin/sh
# x54prev.sh KEYS [m|f]: preview renders (start / middle / end) of 5.4 keys into out_x54p and a contact sheet
cd "$(dirname "$0")/.." || exit 1
G=${2:-m}; S=${SHEET:-out_x54p/sheet.jpg}
python3 tools/x54.py build "$1" >/dev/null
for k in $(echo "$1" | tr ',' ' '); do rm -f out_x54p/_sheet/$k.[0-9].png out_x54p/_sheet/$k.f.[0-9].png; done
venv/bin/python -m artgen.render3 --moves data/v5/x54-moves.csv --gender $G --out out_x54p --style v4 --threads ${T:-4} --preview 2>&1 | grep -E '^\[|Error|Traceback|File "/home' | tail -40
SF=""; [ "$G" = f ] && SF=.f
python3 tools/xsheet.py out_x54p "$S" "$1" $SF >/dev/null
