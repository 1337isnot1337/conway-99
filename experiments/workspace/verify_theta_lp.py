"""Replay primal points of reduced rational LPs independently of the solver."""
from fractions import Fraction as F
from pathlib import Path
import re,sys
def check(base):
    with open(base+'.ine') as f:
        next(f);next(f);m,n,_=next(f).split();rows=[list(map(F,next(f).split())) for _ in range(int(m))]
    text=Path(base+'.spx').read_text()
    if 'SoPlex status       : problem is solved [optimal]' not in text:
        print('No optimal primal witness in output');return
    x={int(i):F(v) for i,v in re.findall(r'^x(\d+)\s+([-\d/]+)$',text,re.M)}
    assert all(row[0]+sum(a*x.get(i,0) for i,a in enumerate(row[1:]))>=0 for row in rows)
    print('exactly feasible:',len(rows),'inequalities,',int(n)-1,'variables',flush=True)
if __name__=='__main__':check(sys.argv[1])
