#!/bin/sh
# render_range.sh START END [THREADS] - render rows START..END-1 of data/v3/render-all.csv
# (both genders, v4 style) on one machine; several machines each take their own range.
#
# Fresh machine (Linux, Python 3.11, ~6 GB free disk):
#   git clone -b exercise-art-v3 https://github.com/noorimanesh/progym-android.git art && cd art
#   python3.11 -m venv venv && venv/bin/pip install "bpy==4.5.*" numpy pillow
#   python3 tools/fetch_assets.py                 # CC0 MakeHuman files (pinned commit)
#   venv/bin/python -m artgen.body_model          # build the male / female bodies (cached)
#   nohup tools/render_range.sh 0 230 > range-0.log 2>&1 &
#
# Outputs to collect (copy the whole folder back): out_v4/
#   <key>.webp <key>.f.webp <key>.thumb.webp <key>.f.thumb.webp   the files that ship
#   _qa/<key>[.f].json   automatic checks (the pack gate reads them)
#   _sheet/<key>[.f].<0..2>.png   contact-sheet frames for review
# Merge: copy every machine's out_v4/ into one out_v4/ (keys never overlap), then
#   python3 tools/review3.py issues out_v4
#   python3 tools/make_dist3.py --moves data/v3/moves.csv --renders out_v4 --dist dist/ex3d --pack dist/ex3d-v4.tar.gz
# The run resumes (--skip-existing): if a machine stops, start the same command again.
set -e
START="${1:?start row}"
END="${2:?end row (exclusive)}"
THREADS="${3:-$(nproc)}"
MOVES=data/v3/render-all.csv
OUT=out_v4
for G in m f; do
  nice -n 10 venv/bin/python -m artgen.render3 --moves "$MOVES" --gender "$G" --out "$OUT" \
       --style v4 --threads "$THREADS" --start "$START" --end "$END" --skip-existing 2>&1 \
       | grep --line-buffered -E '^\[|^done|Error|Traceback|File "'
done
echo "range $START-$END done"
