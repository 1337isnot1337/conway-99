"""Interior search on the equality section of the third-moment polytope."""
import numpy as np
import scipy.sparse as sp
from scipy.optimize import minimize
from scipy.sparse.linalg import lsmr
from triple_moments import tmp


def setup():
    E=sp.load_npz(tmp/'outer3-14-eq.npz').tocsr()
    G=sp.load_npz(tmp/'outer3-14-ge.npz').tocsr()
    alive=np.ones(E.shape[1],dtype=bool)
    while True:
        R=E.multiply(alive).tocsr();R.eliminate_zeros()
        neg=np.asarray((R<0).sum(axis=1)).ravel();pos=np.asarray((R>0).sum(axis=1)).ravel()
        cols=np.unique(R[((neg==0)^(pos==0))].indices)
        if not len(cols):break
        alive[cols]=False
    if not alive[0]:raise ArithmeticError('positive variable forced zero')
    R=E[:,alive];Y=G[:,alive]
    def norm(A):
        w=np.sqrt(np.asarray(A.power(2).sum(axis=1)).ravel());idx=w>0
        return (sp.diags(1/w[idx])@A[idx]).tocsr()
    return norm(R),norm(Y),alive


def main():
    E,G,alive=setup()
    print('forced zero',sum(~alive),'remaining eq/ineq',E.shape,G.shape,flush=True)
    # Minimize squared equality residual and squared violations of all inequalities.
    # Variables are constrained to [0,1]. The empty event equals one.
    def fun(x):
        y=E@x;z=np.minimum(G@x,0.)
        return (y@y+z@z)/2,E.T@y+G.T@z
    x=np.full(E.shape[1],.005);x[0]=1
    state=tmp/'outer3-14-interior.npy'
    if state.exists():x=np.load(state)[alive]
    for r in range(3):
        sol=minimize(fun,x,jac=True,method='L-BFGS-B',bounds=[(1,1)]+[(0,1)]*(len(x)-1),options={'maxiter':400,'ftol':1e-16,'gtol':1e-12,'maxcor':14})
        x=sol.x;print(r,sol.fun,max(abs(E@x)),min(G@x),sol.message,flush=True)
        full=np.zeros(len(alive));full[alive]=x;np.save(state,full)


if __name__=='__main__':main()
