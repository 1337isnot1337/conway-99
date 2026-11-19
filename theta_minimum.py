"""Test vanishing of early integral eigenspace shells in the maximal relaxation."""
from fractions import Fraction as F
from pathlib import Path
import json,argparse,z3
from level_seven_exact import expr
from theta_linear import reduce_solver

def test(file,limit,objective,extra):
    with open(file+'.coordinates') as f:
        names=json.loads(next(f));v=z3.Reals(' '.join('y'+str(i) for i in range(len(names)-1)))
        funcs={}
        for line in f:
            k,*raw=line.split();a=list(map(F,raw));funcs[k]=expr(a[:-1],v)+z3.RealVal(str(a[-1]))
    s=z3.SolverFor('QF_LRA')
    with open(file) as f:
        next(f);next(f);m,_,_=next(f).split()
        for _ in range(int(m)):
            b,*a=map(F,next(f).split());s.add(expr(a,v)>=z3.RealVal(str(-b)))
    for k in range(7,limit+1):
        if 'c0_0_'+str(9*k) in funcs:s.add(funcs['c0_0_'+str(9*k)]==0)
    for k in extra:s.add(funcs[k]==0)
    print('forbidding integral lengths through',2*limit,flush=True)
    if objective:
        name=objective.replace('=','_')
        out=file+'.vanish'+str(limit)+name+'.lp'
    else:out=file+'.vanish'+str(limit)+'.lp'
    print(reduce_solver(s,0,out),out,flush=True)
    if objective:
        k,ub=objective.split('=');src=Path(out).read_text().replace('Bounds',' '+ 'extra: '+str(funcs[k])+' <= '+ub+'\nBounds');raise NotImplementedError('use exact linear rows')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('file');p.add_argument('limit',type=int);p.add_argument('--extra',nargs='*',default=[]);a=p.parse_args();test(a.file,a.limit,None,a.extra)
