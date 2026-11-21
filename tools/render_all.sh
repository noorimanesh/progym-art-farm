#!/bin/sh
# render_all.sh MOVES OUT [extra render3 args]: male and female in parallel
# (1 thread each, niced), skipping finished keys; logs keep only result lines
M="$1"; O="$2"; shift 2
F='^\[|^done|Error|Traceback|File "'
(nice -n 10 venv/bin/python -m artgen.render3 --moves "$M" --gender m --out "$O" --threads 1 --skip-existing "$@" 2>&1 | grep --line-buffered -E "$F" > "$O.m.log") &
P1=$!
(nice -n 10 venv/bin/python -m artgen.render3 --moves "$M" --gender f --out "$O" --threads 1 --skip-existing "$@" 2>&1 | grep --line-buffered -E "$F" > "$O.f.log") &
P2=$!
wait $P1 $P2
echo all-done >> "$O.m.log"
