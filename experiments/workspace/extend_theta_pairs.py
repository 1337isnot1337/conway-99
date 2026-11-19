"""Add graph-pair marks to a previously eliminated one-coordinate system."""
from fractions import Fraction as F
import json,argparse
from pathlib import Path
import z3
from level_seven_exact import expr
from theta_linear import reduce_solver
from coset_pair_flags import add_pairs

def extend(base,rank,order,save,triple,mixed,only):
    s=z3.SolverFor('QF_LRA')
    with open(base+'.coordinates') as f:
        names=json.loads(next(f))
        free=[z3.Real('y'+str(i)) for i in range(len(names)-1)]
        V={}
        for line in f:
            name,*raw=line.split();co=list(map(F,raw));v=z3.Real(name)
            s.add(v==expr(co[:-1],free)+z3.RealVal(str(co[-1])));V[name]=v
    with open(base) as f:
        next(f);next(f);m,_,_=next(f).split()
        for _ in range(int(m)):
            b,*row=map(F,next(f).split());s.add(expr(row,free)>=z3.RealVal(str(-b)))
    def entry(side,j,d):
        j=min(j%9,(-j)%9)
        if d==0:return int(j==0)
        return V.get('c%d_%d_%d'%(side,j,d),0)
    for side in (0,1):
        def flag(d,t):
            k=min(t%28,(-t)%28);j=d-(1 if side else 7)*((t*t-k*k)//56)
            if j==0 and k==0:return 99
            return V.get('f%d_%d_%d'%(side,j,k),0)
        if not only:tab=add_pairs(s,entry,flag,side,order,('edge','nonedge'),rank)
        if mixed:
            from line_cosets import line_flags
            from point_line_flags import add as add_mixed
            lt=line_flags(s,side,order,entry,rank);tri=add_mixed(s,side,order,rank,entry,flag,lt)
            if not only:
                from math import isqrt
                scale=7 if side else 1
                for j in range(5):
                    for d in range((5 if side else 8)*j*j%9,9*order+1,9):
                        limit=isqrt(8*scale*d);ts=[t for t in range(-limit,limit+1) if t%9==j]
                        for a in ts:
                            for k in ts[1:-1]:
                                rs=sum(2*(t-k)*tab['nonedge',d,a,t] for t in ts if t>k)
                                ls=sum(max(0,-4*i-a-y-12*k)*tri.get((j,d,tuple(sorted((a,i,y)))),0) for i in ts for y in ts if -4*i-a-y>12*k)
                                s.add(rs>=ls)
        if triple:
            from coset_triple_flags import add
            add(s,side,triple,rank,entry,flag,tab)
    print(reduce_solver(s,0,save),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('base');p.add_argument('save');p.add_argument('--order',type=int,default=14);p.add_argument('--rank',type=int,default=42);p.add_argument('--triple',type=int,default=0);p.add_argument('--mixed',action='store_true');p.add_argument('--only-mixed',action='store_true');a=p.parse_args();extend(a.base,a.rank,a.order,a.save,a.triple,a.mixed or a.only_mixed,a.only_mixed)
