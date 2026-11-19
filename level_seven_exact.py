"""Exact rational Fourier-coefficient feasibility with independently checked linear certificates."""
from fractions import Fraction as F
import argparse,json,math
from functools import reduce
from pathlib import Path
from level_seven_theta import series_basis
import z3

def constraints(r,n,limits,sparse=False):
    from sparse_theta import lower
    floors=lower() if sparse else {2:462,3:24948,4:1386}
    B=series_basis(7*n);D=B[:,::-1]*[F(7)**(3+r//2-2*j) for j in range(15)]
    rows={}
    def ge(name,row,b=0):rows[name]=(list(map(F,row)),F(b))
    ge('mass_L',B[0],1);ge('mass_L_rev',-B[0],-1)
    ge('mass_K',D[0],1);ge('mass_K_rev',-D[0],-1)
    for i in range(1,7):ge('zero_L'+str(i),-B[i])
    for i,a in limits.items():ge('bound_L'+str(i),-B[i],-a)
    ge('bound_K1',-D[1],-88)
    for i in range(1,n+1):
        ge('L'+str(i),B[i]);ge('K'+str(i),D[i],floors.get(i,0))
        ge('incl_L'+str(i),B[7*i]-D[i]);ge('incl_K'+str(i),D[7*i]-B[i])
        if r==42:ge('maximal'+str(i),D[i]-B[7*i])
    return rows

def expr(row,v):
    return z3.Sum([z3.RealVal(str(a))*x for a,x in zip(row,v) if a])
def solve(r,n,limits,sparse):
    rows=constraints(r,n,limits,sparse)
    x=z3.Reals(' '.join('b'+str(j) for j in range(15)));s=z3.SolverFor('QF_LRA')
    for k,(a,b) in rows.items():s.assert_and_track(expr(a,x)>=z3.RealVal(str(b)),k)
    status=s.check();print('rank',r,'order',n,status,flush=True)
    if status!=z3.unsat:return
    core=list(map(str,s.unsat_core()));dual=z3.SolverFor('QF_LRA');w=z3.Reals(' '.join('w'+str(i) for i in range(len(core))))
    dual.add(*(v>=0 for v in w))
    for j in range(15):dual.add(expr([rows[k][0][j] for k in core],w)==0)
    dual.add(expr([rows[k][1] for k in core],w)==1)
    assert dual.check()==z3.sat;m=dual.model()
    coeff={k:F(m[v].as_fraction()) for k,v in zip(core,w) if m[v].as_fraction()}
    verify(rows,coeff)
    path=Path('level-seven-certificate-%d.json'%r)
    path.write_text(json.dumps(dict(rank=r,order=n,sparse=sparse,limits=limits,weights={k:str(v) for k,v in coeff.items()}),indent=2)+'\n')
    print('exact nonnegative identity 0 >= 1 from',len(coeff),'terms:',list(coeff),flush=True)

def verify(rows,coeff):
    assert all(c>=0 for c in coeff.values())
    assert all(sum(c*rows[k][0][j] for k,c in coeff.items())==0 for j in range(15))
    assert sum(c*rows[k][1] for k,c in coeff.items())==1

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--r',type=int,nargs='+',default=[28,30,32]);p.add_argument('--order',type=int,default=15);p.add_argument('--verify',nargs='*');p.add_argument('--limit',nargs='*',default=['7=990','8=148995']);p.add_argument('--sparse',action='store_true');a=p.parse_args()
    if a.verify is None:
        limits={int(x.split('=')[0]):int(x.split('=')[1]) for x in a.limit}
        for r in a.r:solve(r,a.order,limits,a.sparse)
    else:
        for file in a.verify:
            data=json.loads(Path(file).read_text());rows=constraints(data['rank'],data['order'],{int(k):v for k,v in data['limits'].items()},data.get('sparse',False));verify(rows,{k:F(v) for k,v in data['weights'].items()});print(file,'verified',flush=True)
