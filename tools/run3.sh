#!/bin/sh
# run3.sh MOVES OUT [extra args]: render male then female (niced, 2 threads each)
M="$1"; O="$2"; shift 2
nice -n 10 venv/bin/python -m artgen.render3 --moves "$M" --gender m --out "$O" "$@" 2>&1 | grep -E "^\[|^done|Error|Traceback|File " 
nice -n 10 venv/bin/python -m artgen.render3 --moves "$M" --gender f --out "$O" "$@" 2>&1 | grep -E "^\[|^done|Error|Traceback|File "
