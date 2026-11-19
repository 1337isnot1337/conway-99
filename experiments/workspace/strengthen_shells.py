"""Add certified short-shell bounds to a reduced maximal theta feasibility problem."""
from fractions import Fraction as F
import json
from pathlib import Path
import argparse

def strengthen(source, target):
    source = Path(source)
    target = Path(target)
    inputs = source.with_suffix('.ine.coordinates')
    bounds = json.loads(Path('anisotropic-shell-bounds.json').read_text())
    lifts = json.loads(Path('six-coset-floors.json').read_text())
    with inputs.open() as stream:
        names = json.loads(next(stream))
        rows = {}
        for line in stream:
            key, _, rest = line.partition(' ')
            if key == 'prism' or key.startswith(('c0_', 'c1_')):
                rows[key] = [F(v) for v in rest.split()]
    assert names[-1] == '$constant'
    prism = rows['prism']
    added = []
    for key, row in rows.items():
        if not key.startswith('c0_'):
            continue
        d = key.split('_')[-1]
        if d in bounds:
            a = [-x for x in row]
            a[-1] += bounds[d]['upper']
            added.append(a)
    for j, d, mass, offset, slope in lifts:
        key = f'c1_{j}_{d}'
        if key in rows:
            a = [x - F(slope)*y for x,y in zip(rows[key],prism)]
            a[-1] -= F(offset)
            added.append(a)
    a = [-x for x in prism]
    a[-1] += 1386
    added.append(a)
    with source.open() as f, target.open('w') as g:
        g.write(next(f));g.write(next(f))
        m,n,kind = next(f).split()
        print(int(m)+len(added),n,kind,file=g)
        for _ in range(int(m)):
            g.write(next(f))
        for row in added:
            print(row[-1],*row[:-1],file=g)
        g.write(f.read())
    target.with_suffix('.ine.coordinates').symlink_to(inputs.resolve())
    print('added shell inequalities',len(added),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('source');p.add_argument('target')
    args=p.parse_args()
    strengthen(args.source,args.target)
