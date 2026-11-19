"""Numerical feasibility with exact replay of a candidate active system."""
import sys
import numpy as np
from fractions import Fraction as F
from scipy.optimize import linprog
from flint import fmpq,fmpq_mat

def run(path):
    with open(path) as f:
        next(f);next(f);m,n,_=next(f).split();M=[list(map(F,next(f).split())) for _ in range(int(m))]
    keep=[]
    for i,row in enumerate(M):
        if max(abs(x) for x in row[1:]):keep.append(i)
        else:assert row[0]>=0
    A=np.array([[float(x) for x in M[i]] for i in keep])
    for mag in (1,1e4,1e8,1e12):
        scale=np.full(A.shape[1],mag,dtype=float);scale[0]=1
        R=A*scale
        for _ in range(12):
            R/=np.maximum(np.max(abs(R),axis=1),1e-250)[:,None]
            col=np.maximum(np.max(abs(R),axis=0),1e-250);col[0]=1;R/=col;scale/=col
        b=R[:,0];L=R[:,1:];nv=L.shape[1]
        res=linprog(np.r_[np.zeros(nv),-1],A_ub=np.column_stack((-L,np.ones(len(L)))),b_ub=b,bounds=[(None,None)]*nv+[(None,1)],method='highs-ds',options={'primal_feasibility_tolerance':1e-9,'dual_feasibility_tolerance':1e-9})
        print(mag,res.status,res.fun,res.message,flush=True)
        if res.success:
            weights=-res.ineqlin.marginals;act=np.flatnonzero(weights>1e-11)
            if res.fun>1e-9:
                import z3,json
                from level_seven_exact import expr
                for supp in (np.flatnonzero(weights>0),np.flatnonzero(res.ineqlin.residual<1e-8)):
                    ix0=[keep[i] for i in supp]
                    print('active rows',len(ix0),'positive weights',np.count_nonzero(weights>0),flush=True)
                    if len(ix0)>260:continue
                    v=[z3.Real('w'+str(i)) for i in ix0];ss=z3.SolverFor('QF_LRA');ss.set(timeout=8000)
                    ss.add(*(q>=0 for q in v))
                    for j in range(nv+1):ss.add(expr([M[i][j] for i in ix0],v)==(-1 if not j else 0))
                    rr0=ss.check();print('exact support',rr0,flush=True)
                    if rr0==z3.sat:
                        mm=ss.model();cert={ix0[j]:str(mm.eval(q)) for j,q in enumerate(v) if not z3.is_true(z3.simplify(mm.eval(q)==0))}
                        assert all(sum(F(w)*M[i][j] for i,w in cert.items())==(-1 if not j else 0) for j in range(nv+1))
                        with open(path+'.certificate.json','w') as f:json.dump(cert,f)
                        print('exact Farkas certificate',len(cert),flush=True);return
                ix=[keep[i] for i in act];aa=fmpq_mat([[fmpq(str(x)) for x in M[i]] for i in ix]).transpose()
                tar=fmpq_mat([[-1]]+[[0]]*nv);aug=fmpq_mat([[aa[i,j] for j in range(len(ix))]+[tar[i,0]] for i in range(nv+1)])
                rr,r=aug.rref()
                if r==len(ix) and all(rr[j,j]==1 for j in range(r)) and all(rr[j,r]>=0 for j in range(r)):
                    w=fmpq_mat([[rr[j,r]] for j in range(r)])
                    if aa*w==tar:
                        print('exact Farkas certificate',len(ix),flush=True)
                        import json
                        with open(path+'.certificate.json','w') as f:json.dump({i:str(w[j,0]) for j,i in enumerate(ix)},f)
                        return
            if res.fun < -1e-12:
                x=[F(str(float(v))) for v in (res.x[:-1]*scale[1:])]
                if all(row[0]+sum(a*b for a,b in zip(row[1:],x))>=0 for row in M):
                    print('exact feasible point',flush=True);return
if __name__=='__main__':run(sys.argv[1])
