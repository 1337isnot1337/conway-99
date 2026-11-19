"""Spherical linear bounds for a shell of a fixed residue in the anisotropic seven-plane."""
from fractions import Fraction as F
from functools import cache
from math import floor
from pathlib import Path
import json,z3,argparse
from shell_bounds import polynomials
from level_seven_exact import expr
@cache
def bound(d,degree,root_count=44):
    R=F(2*d,63);num=floor(2*R)
    if num==0:return 1,None
    ts=[1-F(a)/R for a in range(1,num+1)]
    # Find a polynomial majorant with nonnegative Gegenbauer coefficients.
    # The primal distance distribution has at most num variables.
    p=list(polynomials(44,ts,degree));v=[z3.Real('a'+str(i)) for i in range(num)]
    s=z3.Optimize();s.add(*(x>=0 for x in v),v[0]<=min(num,root_count))
    for k in range(1,degree+1):s.add(expr(p[k],v)>=-1)
    sol=s.maximize(1+sum(v));assert s.check()==z3.sat;B=F(str(sol.value()))
    # A standalone dual certificate, normalized to constant Gegenbauer coefficient 1.
    dual=z3.SolverFor('QF_LRA');y=[z3.Real('y'+str(k)) for k in range(1,degree+1)];z=z3.Real('rootterm')
    dual.add(*(x>=0 for x in y),z>=0)
    for i in range(num):dual.add(expr([p[k][i] for k in range(1,degree+1)],y)-(z if i==0 else 0)<=-1)
    dual.add(1+sum(y)+min(num,root_count)*z==z3.RealVal(str(B)));assert dual.check()==z3.sat
    mod=dual.model();w=[F(str(mod.eval(x))) for x in y];zr=F(str(mod.eval(z)))
    assert all(1+sum(c*p[k][i] for k,c in enumerate(w,1))<=zr*(i==0) for i in range(num))
    assert all(x>=0 for x in w) and zr>=0 and B==1+sum(w)+min(num,root_count)*zr
    cert=dict(root=str(zr),coeff={k:str(x) for k,x in enumerate(w,1) if x},per_class=str(B))
    return floor(B),cert
def run(limit,degree,root_count):
    doc={}
    for d in range(1,limit+1):
        if not any(d%9==8*j*j%9 for j in range(5)):continue
        a,c=bound(d,degree,root_count);mult=8 if d%7 else 1
        doc[d]={'upper':a*mult,'certificate':c}
        if d%9==0:print('squared norm',2*d//9,'upper',a*mult,flush=True)
    Path('anisotropic-shell-bounds'+('' if root_count==44 else '-roots'+str(root_count))+'.json').write_text(json.dumps(doc)+'\n')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--limit',type=int,default=180);p.add_argument('--degree',type=int,default=18);p.add_argument('--root-count',type=int,default=44);a=p.parse_args();run(a.limit,a.degree,a.root_count)
