from fractions import Fraction
from functools import reduce
from math import gcd,lcm
from pathlib import Path
import sys
p=Path(sys.argv[1])
with p.open() as f,p.with_suffix('.lp').open('w') as g:
    next(f);next(f);m,n,_=next(f).split();n=int(n)-1
    print('Minimize\n obj: 0 x0\nSubject To',file=g)
    for i in range(int(m)):
        row=list(map(Fraction,next(f).split()))
        if not any(row[1:]):
            assert row[0]>=0;continue
        scale=max(abs(v) for v in row);co=[v/scale for v in row]
        print(' r%d:'%i,*('%s %s x%d'%('+' if v>0 else '-',abs(v),j) for j,v in enumerate(co[1:]) if v),'>=',-co[0],file=g)
    print('Bounds',file=g)
    for i in range(n):print(' x%d free'%i,file=g)
    print('End',file=g)
