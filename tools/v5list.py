"""v5list.py: the whole library for the 5.5 render (data/v5/all-moves.csv): every move rendered so far (data/v3/render-all.csv
keys, rows from data/v3/moves.csv) plus the 150 drawings of 5.4 (data/v5/x54.csv overrides applied)."""
import csv, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
mv = list(csv.DictReader(open(os.path.join(ROOT, 'data/v3/moves.csv'), encoding='utf-8')))
done = {r['key'] for r in csv.DictReader(open(os.path.join(ROOT, 'data/v3/render-all.csv'), encoding='utf-8'))}
ov = {r['key']: r for r in csv.DictReader(open(os.path.join(ROOT, 'data/v5/x54.csv'), encoding='utf-8'))}
out = []
for r in mv:
    if r['key'] in ov:
        r = dict(r)
        for k in ('template', 'view', 'tempo', 'thumb', 'equipment'):
            if ov[r['key']].get(k):
                r[k] = ov[r['key']][k]
        out.append(r)
    elif r['key'] in done:
        out.append(r)
w = csv.DictWriter(open(os.path.join(ROOT, 'data/v5/all-moves.csv'), 'w', encoding='utf-8', newline=''), fieldnames=list(mv[0].keys()))
w.writeheader(); w.writerows(out)
print(len(out), 'moves;', len(ov), 'from 5.4;', len(done), 'rendered before')
