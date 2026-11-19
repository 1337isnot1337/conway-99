"""Enforce sparse flag lower bounds and test the remaining points against admissible profiles."""
from collections import defaultdict
from fractions import Fraction as F
from math import isqrt
from pathlib import Path
import argparse,json
from profile_facets import facets
from coset_pair_flags import reduce_mark

def apply(base,out,cap):
    with open(base+'.coordinates') as f:
        names=json.loads(next(f));n=len(names);rows={}
        for line in f:
            key,_,rest=line.partition(' ')
            if key=='prism' or key.startswith(('c1_','f1_','pedge_1_','pnonedge_1_')):
                rows[key]=list(map(F,rest.split()))
    zero=[F(0)]*n;one=zero.copy();one[-1]=1;prism=rows['prism'];add=set()
    def append(v):
        scale=next((abs(x) for x in v if x),None)
        if scale:add.add(tuple(x/scale for x in v))
    def point(d,t):
        x=min(t%28,(-t)%28);dd=d-(t*t-x*x)//56
        return [99*a for a in one] if dd==x==0 else rows.get(f'f1_{dd}_{x}',zero)
    def pair(d,t,u,e):
        dx,x,y=reduce_mark(-8 if e else 1,t,u);dd=d-dx;degree=14 if e else 84
        if dd==x==y==0:return [99*degree*a for a in one]
        return rows.get('p'+('edge' if e else 'nonedge')+f'_1_{dd}_{x}_{y}')
    def subtract(vec,a,b):
        diff=[x-F(b)*y for x,y in zip(vec,prism)];diff[-1]-=F(a)
        return diff
    S,P,Q=json.loads(Path('sparse-translated-marks.json').read_text())
    profiles=json.loads(Path('shell-profiles-refined-164.json').read_text())
    flags=defaultdict(dict)
    for m,d,t,a,b in P:
        diff=subtract(point(d,t),a,b);flags[m,d][t]=diff;append(diff)
    for m,d,e,t,u,a,b in Q:
        if d>cap:continue
        vec=pair(d,t,u,e)
        if vec is not None:append(subtract(vec,a,b))
    for m,d,a,b in S:
        j=min(m%9,-m%9);size=rows.get(f'c1_{j}_{d}',zero)
        diff=subtract(size,a,b);append(diff)
        key=f'{j}_{7*d}';ps=profiles.get(key)
        if not ps:continue
        lim=isqrt(56*d);ts=[t for t in range(-lim,lim+1) if t%9==j]
        points=[[p.get(str((t-j)//9),0) for t in ts] for p in ps]
        vecs=[diff]+[flags[m,d].get(t,point(d,t)) for t in ts]
        for row in facets(points):append([sum(x*v[i] for x,v in zip(row,vecs)) for i in range(n)])
    with open(base) as f,open(out,'w') as g:
        g.write(next(f));g.write(next(f));m,c,kind=next(f).split();print(int(m)+len(add),c,kind,file=g)
        for _ in range(int(m)):g.write(next(f))
        for v in sorted(add):print(v[-1],*v[:-1],file=g)
        g.write(f.read())
    Path(out+'.coordinates').symlink_to(Path(base+'.coordinates').resolve())
    print('sparse point and pair lower bounds and residual facets',len(add),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('base');p.add_argument('out');p.add_argument('--pair-cap',type=int,default=0);a=p.parse_args();apply(a.base,a.out,a.pair_cap)
