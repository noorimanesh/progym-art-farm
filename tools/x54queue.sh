#!/bin/sh
# x54queue.sh: renders (male and female, full) every key listed in data/v5/queue.txt that has no finished
# pictures in out_x54 yet; waits for new keys; stops when data/v5/queue.stop exists.
cd "$(dirname "$0")/.." || exit 1
while [ ! -f data/v5/queue.stop ]; do
  todo=""
  for k in $(cat data/v5/queue.txt 2>/dev/null); do
    [ -f "out_x54/$k.webp" ] && [ -f "out_x54/$k.f.webp" ] && continue
    todo="$todo,$k"
  done
  todo=${todo#,}
  if [ -z "$todo" ]; then sleep 30; continue; fi
  python3 tools/x54.py build "$todo" >/dev/null
  for G in m f; do
    nice -n 15 venv/bin/python -m artgen.render3 --moves data/v5/x54-moves.csv --gender $G --out out_x54 --style v4 --threads 2 --skip-existing 2>&1 | grep --line-buffered -E '^\[|^done|Error|Traceback'
  done
done
