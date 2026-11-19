"""Antipodal packing bounds for short shells in the integral eigenspace."""
from fractions import Fraction as F
from math import floor
from shell_bounds import polynomials
from level_seven_exact import expr
import z3
def upper(N,h,caps):
    # For each fixed point the signed dot distribution is symmetric.
    m=N-7
    ts=[F(t,N) for t in range(m+1)];rows=list(polynomials(44,ts,h))
    v=z3.Reals(' '.join('b'+str(i) for i in range(m+1)))
    s=z3.Optimize();s.add(*(x>=0 for x in v))
    for k in range(2,h+1,2):s.add(expr(rows[k],v)>=-2)
    for t,x in enumerate(v):
        if 2*(N-t) in caps:s.add(x<=(2 if t else 1)*caps[2*(N-t)])
    sol=s.maximize(2+sum(v));assert s.check()==z3.sat
    return floor(F(str(sol.value())))
if __name__=='__main__':
    caps={14:990,16:148995}
    for k in range(18,31,2):
        caps[k]=upper(k,40,caps);print(k,caps[k],flush=True)
