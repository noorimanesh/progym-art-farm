#!/bin/sh
# x54render.sh KEYS: full renders (male, then female) of the given 5.4 keys into out_x54 (resumes)
cd "$(dirname "$0")/.." || exit 1
python3 tools/x54.py build "$1" >/dev/null
for G in m f; do
  nice -n 15 venv/bin/python -m artgen.render3 --moves data/v5/x54-moves.csv --gender $G --out out_x54 --style v4 --threads 2 --skip-existing 2>&1 | grep --line-buffered -E '^\[|^done|Error|Traceback'
done
