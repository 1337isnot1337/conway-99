"""Rational spherical linear programming bounds for shells in a rank-44 even lattice."""
from fractions import Fraction as F
from math import floor
from functools import cache
from level_seven_exact import expr
import z3,argparse

def polynomials(d,t,h):
    last=[F(1) for x in t];cur=t
    yield last;yield cur
    for j in range(2,h+1):
        a=[((2*j+d-4)*x*y-(j-1)*z)/(j+d-3) for x,y,z in zip(t,cur,last)]
        yield a;last,cur=cur,a

def bound(n,h,prev):
    ts=[F(i,2*n) for i in range(2*n)]
    z=z3.Reals(' '.join('c'+str(i) for i in range(2*n)))
    s=z3.Optimize();s.add(*(i>=0 for i in z))
    for j,p in enumerate(polynomials(44,ts,h)):
        if j%2==0 and j:s.add(expr(p,z)>=-2)
    s.add(z[-1]<=8*n)
    for i,v in prev.items():
        if i<2*n:s.add(z[2*n-i]<=2*v)
    result=s.maximize(2+sum(z));status=s.check()
    if status==z3.sat:
        co=F(str(result.value()));ans=floor(co)
        print(n,'Lp upper',ans,'nonzero frequencies',[(i,round(float(F(str(s.model().eval(v)))),1)) for i,v in enumerate(z) if s.model().eval(v).as_string()!='0'],flush=True)
        return ans
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--n',nargs='+',type=int,default=list(range(2,8)));p.add_argument('--degree',type=int,default=48);a=p.parse_args()
    prev={1:88}
    for n in a.n:prev[n]=bound(n,a.degree,prev)
