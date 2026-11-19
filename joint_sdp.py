"""Separate valid cubic positive-semidefinite cuts while satisfying the linear moment constraints."""
import argparse
import numpy as np
import scipy.sparse as sp
from scipy.optimize import minimize
from localized_outer import blocks,tmp
from relax_outer3 import setup


def main(rounds,iterations):
    E,G,alive=setup()
    x=np.load(tmp/'outer3-14-interior.npy')[alive]
    mats=[]
    for name,n,B in blocks(14,'conditional')+blocks(14,'projectors'):
        lo=np.tril_indices(n)
        T=B[:,alive].tocsr();diag=(T@x)[lo[0]==lo[1]]
        d=np.sqrt(np.maximum(.0001,diag))
        T=(sp.diags(1/(d[lo[0]]*d[lo[1]]))@T).tocsr()
        mats.append((name,n,T,lo))
    path=tmp/'outer3-14-separation.npz'
    cutfile=tmp/'outer3-14-cuts.npz'
    cuts=sp.csr_matrix((0,len(x)))
    if path.exists() and cutfile.exists():
        prev=np.load(path);x=prev['x'];cuts=sp.load_npz(cutfile)
    for it in range(rounds):
        add=[];worsts=[]
        for name,n,T,lo in mats:
            M=np.zeros((n,n));M[lo]=T@x;M.T[lo]=M[lo]
            e,U=np.linalg.eigh(M);worsts.append(e[0])
            for j in range(sum(e< -1e-7)):
                v=U[:,j]
                row=T.T@(v[lo[0]]*v[lo[1]]*(1+(lo[0]!=lo[1])))
                row/=np.linalg.norm(row)
                add.append(sp.csr_matrix(row))
        print(it,'worst scaled eigen',min(worsts),'cuts',len(add),'linear max error',np.abs(E@x).max(),'inequalities',min(G@x),flush=True)
        if not add:break
        cuts=sp.vstack([cuts,*add],format='csr')
        def fun(x):
            e=E@x;g=np.minimum(G@x,0);v=np.minimum(cuts@x,0)
            return (e@e+g@g+v@v)/2,E.T@e+G.T@g+cuts.T@v
        sol=minimize(fun,x,jac=True,method='L-BFGS-B',bounds=[(1,1)]+[(0,1)]*(len(x)-1),options={'maxiter':iterations,'ftol':1e-17,'gtol':1e-12,'maxcor':12})
        x=sol.x;sp.save_npz(cutfile,cuts);np.savez_compressed(path,x=x)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--rounds',type=int,default=15);p.add_argument('--iterations',type=int,default=240)
    a=p.parse_args();main(a.rounds,a.iterations)
