"""x54.py build|apply [keys]: moves for the 5.4 drawings (data/v5/x54.csv overrides the move rows).
  build  -> data/v5/x54-moves.csv (only the overridden rows, for rendering)
  apply  -> writes the overrides into data/v3/moves.csv (status ok)"""
import csv, sys, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
mv = list(csv.DictReader(open(os.path.join(ROOT, 'data/v3/moves.csv'), encoding='utf-8')))
ov = {r['key']: r for r in csv.DictReader(open(os.path.join(ROOT, 'data/v5/x54.csv'), encoding='utf-8'))}
only = set(sys.argv[2].split(',')) if len(sys.argv) > 2 and sys.argv[2] else None
out = []
for r in mv:
    o = ov.get(r['key'])
    if not o:
        continue
    r = dict(r)
    for k in ('template', 'view', 'tempo', 'thumb', 'equipment'):
        if o.get(k):
            r[k] = o[k]
    if only is None or r['key'] in only:
        out.append(r)
missing = set(ov) - {r['key'] for r in mv}
if missing:
    print('not in moves.csv:', ' '.join(sorted(missing)))
if sys.argv[1] == 'build':
    w = csv.DictWriter(open(os.path.join(ROOT, 'data/v5/x54-moves.csv'), 'w', encoding='utf-8', newline=''), fieldnames=list(mv[0].keys()))
    w.writeheader(); w.writerows(out)
    print(len(out), 'rows')
