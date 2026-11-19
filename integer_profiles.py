"""Integer cubic-row statistics of all 84 distinct outer neighborhoods of a single root."""
from pathlib import Path
from math import factorial
import numpy as np
import scipy.sparse as sp
from scipy.optimize import milp,Bounds,LinearConstraint
from outer_moments import OrbitModel,dense


def build():
    m=OrbitModel(14);eq,ge=m.constraints()
    E=dense(eq,m.dim).astype(np.int64);F=dense(ge,m.dim).astype(np.int64)
    p=np.fromfile('/tmp/conway99-tools/pair-orbits.bin',dtype=np.uint16)
    sizes=np.bincount(p)
    common=2**7*factorial(7)
    def integral(A):
        A=A*(common//sizes)
        return A//np.gcd.reduce(abs(A),axis=1)[:,None]
    profile=np.load(Path(__file__).with_name('row-profiles.npz'));H=profile['H'].astype(int)
    cols=profile['columns'];den=profile['den'];h=len(H);d=m.dim
    assert np.all((den*84)%sizes[cols]==0)
    E1=sp.hstack([sp.csr_matrix(integral(E)),sp.csr_matrix((len(E),h))])
    F1=sp.hstack([sp.csr_matrix(integral(F)),sp.csr_matrix((len(F),h))])
    Y=sp.csr_matrix((den*84//sizes[cols],(np.arange(len(cols)),cols)),shape=(len(cols),d))
    R=sp.hstack([Y,-H.T])
    O=sp.csr_matrix((np.ones(h),(np.zeros(h),np.arange(d,d+h))),shape=(1,d+h))
    A=sp.vstack([E1,R,O,F1],format='csr')
    rhs=np.r_[np.zeros(len(E)+len(cols)),84,np.zeros(len(F))]
    ub=rhs.copy();ub[-len(F):]=np.inf
    lower=np.zeros(d+h);upper=np.r_[sizes,np.full(h,84)]
    lower[0]=upper[0]=1
    return A,rhs,ub,lower,upper,d


if __name__=='__main__':
    A,b,u,lo,hi,d=build()
    result=milp(np.zeros(len(lo)),integrality=np.ones(len(lo)),bounds=Bounds(lo,hi),constraints=LinearConstraint(A,b,u),options={'time_limit':110,'mip_rel_gap':0})
    print(result.message,flush=True)
    if result.x is not None:
        z=np.rint(result.x).astype(np.int64);v=A.astype(np.int64)@z
        assert np.all(v>=b) and np.all(v<=u) and np.all(z>=lo) and np.all(z<=hi)
        print('verified integral root populations',len(z),'nonzero row profiles',sum(z[d:]>0),'sum',sum(z[d:]),flush=True)
        np.save('integer-profile-witness.npy',z)
