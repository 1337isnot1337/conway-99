"""Couple each graph rank to its average over all maximal isotropic extensions."""
from fractions import Fraction as F
from itertools import product
from pathlib import Path
import argparse,json,z3
from level_seven_exact import constraints,expr
from level_seven_theta import series_basis
from theta_linear import reduce_solver

def control(q):
    # Hyperbolic plane and an anisotropic plane. Compare every perpendicular point count.
    nonres=next(x for x in range(1,q) if x not in {i*i%q for i in range(q)})
    space=list(product(range(q),repeat=4))
    def norm(x):return (x[0]*x[1]+x[2]**2-nonres*x[3]**2)%q
    def ip(x,y):return (x[0]*y[1]+x[1]*y[0]+2*x[2]*y[2]-2*nonres*x[3]*y[3])%q
    lines=[x for x in space[1:] if norm(x)==0 and next(v for v in x if v)==1]
    assert len(lines)==1+q*q
    for x in space[1:]:
        assert sum(ip(x,y)==0 for y in lines)==(1 if norm(x)==0 else q+1)
    print('finite-plane probability check',q,len(lines),'lines',flush=True)

def run(base,r,out,n):
    s=z3.SolverFor('QF_LRA')
    with open(base+'.coordinates') as f:
        names=json.loads(next(f));v=z3.Reals(' '.join('s'+str(i) for i in range(len(names)-1)));C={}
        for line in f:
            key,_,rest=line.partition(' ')
            if key.startswith(('c0_0_','c1_0_','c0_3_','c1_3_')):
                a=list(map(F,rest.split()));C[key]=expr(a[:-1],v)+z3.RealVal(str(a[-1]))
    with open(base) as f:
        next(f);next(f);m,_,_=next(f).split()
        for _ in range(int(m)):
            b,*a=map(F,next(f).split());s.add(expr(a,v)>=z3.RealVal(str(-b)))
    coeff=z3.Reals(' '.join('av'+str(i) for i in range(15)));fac=7**((44-r)//2)+1
    B=series_basis(7*n);D=B[:,::-1]*[F(7)**(3+r//2-2*j) for j in range(15)]
    rows=constraints(r,n,{7:990,8:148995},True)
    for a,b in rows.values():s.add(expr(a,coeff)>=z3.RealVal(str(b)))
    bounds=json.loads(Path('anisotropic-shell-bounds.json').read_text())
    for k in range(1,n+1):
        def get(side,idx):
            return C.get(f'c{side}_0_{9*idx}',0)+2*C.get(f'c{side}_3_{9*idx}',0)
        V=get(1,k);U=get(0,k)
        s.add(fac*V==expr(B[7*k]+(fac-1)*D[k],coeff))
        if k%7:s.add(fac*U==8*expr(B[k],coeff))
        else:s.add(U==get(1,k//7))
        if str(9*k) in bounds:s.add(U<=bounds[str(9*k)]['upper'])
    print('coupled rank',r,'factor',fac,flush=True)
    print(reduce_solver(s,0,out),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('base',nargs='?');p.add_argument('output',nargs='?');p.add_argument('--rank',type=int,default=34);p.add_argument('--order',type=int,default=20);p.add_argument('--control',action='store_true');a=p.parse_args()
    if a.control:control(3);control(7)
    else:run(a.base,a.rank,a.output,a.order)
