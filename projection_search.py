"""Alternating reflections between binary outer matrices and the exact SRG spectrum."""
import argparse,json
from pathlib import Path
from itertools import combinations,product
import numpy as np
from threadpoolctl import threadpool_limits
from root_search import verify

BASE=Path(__file__).parent


class Geometry:
    def __init__(self,k):
        self.k=k
        self.labels=[p for p in combinations(range(k),2) if p[0]^1!=p[1]]
        n=len(self.labels)
        self.tri=np.triu_indices(n,1)
        self.m=n*(k-2)//2
        C=np.zeros((k,n))
        for j,(a,b) in enumerate(self.labels):C[a,j]=C[b,j]=1.
        self.C=C
        mate=np.eye(k)[np.arange(k)^1]
        # For each column enforce C B = 2J - (I+mate) C.
        self.fixed=np.linalg.pinv(C)@(2-(np.eye(k)+mate)@C)
        self.U=np.linalg.svd(C,full_matrices=True)[2][np.linalg.matrix_rank(C):].T.copy(order='C')
        self.lo=(-1-np.sqrt(4*k-7))/2
        self.hi=-1-self.lo
        self.mult=round((-np.trace(self.fixed)-self.lo*self.U.shape[1])/(self.hi-self.lo))
        self.base=self.fixed+self.lo*(self.U@self.U.T)

    def spectral(self,X):
        compressed=self.U.T@X@self.U
        _,basis=np.linalg.eigh(compressed)
        vectors=self.U@basis[:,-self.mult:] if self.mult else self.U[:,:0]
        return self.base+(self.hi-self.lo)*(vectors@vectors.T)

    def discrete(self,X):
        weights=X[self.tri]
        keep=np.argpartition(weights,-self.m)[-self.m:]
        B=np.zeros_like(X)
        a,b=self.tri
        B[a[keep],b[keep]]=B[b[keep],a[keep]]=1
        return B

    def full(self,B):
        k=self.k
        n=1+k+len(B)
        A=np.zeros((n,n),dtype=np.int16)
        A[0,1:1+k]=A[1:1+k,0]=1
        A[1+np.arange(k),1+(np.arange(k)^1)]=1
        A[1:1+k,1+k:]=self.C
        A[1+k:,1:1+k]=self.C.T
        A[1+k:,1+k:]=B.astype(np.int16)
        return A

    def score(self,B):
        A=self.full(B)
        err=A@A+A-2
        np.fill_diagonal(err,A.sum(axis=1)-self.k)
        d=err.diagonal()
        bad=(np.count_nonzero(err)+np.count_nonzero(d))//2
        penalty=(np.square(err,dtype=np.int64).sum()+d@d)//2
        if bad==0:
            verify([sum(1<<int(j) for j in np.flatnonzero(row)) for row in A],self.k)
        return bad,penalty


def run(k,steps,seed,beta,out):
    g=Geometry(k)
    rng=np.random.default_rng(seed)
    n=len(g.labels)
    X=rng.normal(size=(n,n))
    X=(X+X.T)/2
    if k==14:
        seedfile=BASE/'anchor-seed.json'
        if seedfile.exists():
            rows=list(map(int,json.loads(seedfile.read_text())))
            X=.3*X+np.array([[(r>>i)&1 for i in range(n)] for r in rows])
    best=None
    for step in range(steps):
        B=g.discrete(X)
        if step%10==0:
            score=g.score(B)
            if best is None or score[1]<best[1]:
                best=score
                if out:
                    np.save(out,B.astype(np.uint8))
                print('iteration',step,'incorrect degree/pair counts',score[0],'squared discrepancy',score[1],flush=True)
                if best[0]==0:return
        proj=g.spectral(2*B-X)
        residual=proj-B
        if np.max(abs(residual))<1e-7:
            assert g.score(B)[0]==0
            if out:np.save(out,B.astype(np.uint8))
            print('verified solution at',step,flush=True)
            return
        X+=beta*residual


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('k',type=int)
    p.add_argument('--steps',type=int,default=20000)
    p.add_argument('--seed',type=int,default=17)
    p.add_argument('--beta',type=float,default=.4)
    p.add_argument('--out',type=Path)
    a=p.parse_args()
    with threadpool_limits(limits=1):
        run(a.k,a.steps,a.seed,a.beta,a.out)
