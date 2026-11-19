"""Exact candidate exterior signatures when a square shell spans the 44-dimensional projection."""
from itertools import combinations,product
import argparse
import numpy as np
from flint import nmod_mat,fmpz_mat


def signatures(A,k=14):
    from math import isqrt
    r=(isqrt(4*k-7)-1)//2
    gamma=(1+k*k//2)//(k-r)
    shell=len(A)-4
    width=k-4
    assert shell==4+4*width
    G=gamma*(r*np.eye(len(A),dtype=int)-A)+1
    required=gamma*r+1
    dimension=((1+k*k//2-1)*r+k)//(2*r+1)
    basis=np.arange(4,len(A))
    def principal(ix):return fmpz_mat(G[np.ix_(ix,ix)].tolist())
    M=principal(basis)
    if len(basis)!=dimension or not M.det():
        from scipy.linalg import qr
        if fmpz_mat(G.tolist()).rank()!=dimension:
            raise ValueError('square neighborhood does not span the eigenspace')
        _,_,order=qr(G,pivoting=True)
        basis=order[:dimension];M=principal(basis)
    det=int(M.det())
    if det<=0:raise ValueError('requires positive definite basis Gram matrix')
    modulus=next(p for p in (1009,1013,1019,1021,1031,1033,1039) if det%p)
    inv=np.zeros(G.shape,dtype=np.int64)
    inv[np.ix_(basis,basis)]=np.array(nmod_mat(M.tolist(),modulus).inv().tolist(),dtype=np.int64)
    cross=fmpz_mat(G[:,basis].tolist())
    capacity=2-A-A@A
    avail=capacity[4:,4:]>0
    exact_inv=M.inv()
    answer=[]
    for mask in range(16):
        tips=[i for i in range(4) if mask>>i&1]
        if any(not avail[i,j] for i,j in combinations(tips,2)):continue
        x0=np.ones(len(A),dtype=np.int64);x0[[4+j for j in tips]]=1-gamma
        lists=[]
        for i in range(4):
            cnt=2-int(i in tips)-int((i-1)%4 in tips)
            items=[c for c in combinations(range(4+width*i,4+width*(i+1)),cnt)
                   if all(avail[a,b] for a,b in combinations(c,2)) and all(avail[a,b] for a in c for b in tips)]
            lists.append(items)
        if any(not x for x in lists):continue
        shapes=[len(z) for z in lists]
        score=np.full(shapes,(x0@inv@x0)-required,dtype=np.int64);eligible=np.ones(shapes,dtype=bool)
        matrices=[]
        for i,choices in enumerate(lists):
            P=np.zeros((len(choices),len(A)),dtype=np.int64)
            for j,c in enumerate(choices):P[j,[4+vtx for vtx in c]]=-gamma
            matrices.append(P)
            idx=[1]*4;idx[i]=len(P)
            score+=((P@inv*(P+2*x0)).sum(axis=1)).reshape(idx)
        for i,j in combinations(range(4),2):
            idx=[1]*4;idx[i]=shapes[i];idx[j]=shapes[j]
            X,Y=matrices[i],matrices[j]
            score+=(2*X@inv@Y.T).reshape(idx)
            eligible&=((X[:,4:]@(~avail).astype(np.int64)@Y[:,4:].T)==0).reshape(idx)
        for sig in np.argwhere(eligible&(score%modulus==0)):
            v=x0.copy()
            for i,j in enumerate(sig):v+=matrices[i][j]
            b=fmpz_mat(1,dimension,v[basis].tolist())
            coeff=exact_inv*b.transpose()
            if (b*coeff)[0,0]==required and cross*coeff==fmpz_mat(len(A),1,v.tolist()):
                answer.append(tuple(np.flatnonzero(v[4:]==1-gamma).tolist()))
    return answer


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('inputs',nargs='+');args=p.parse_args()
    for name in args.inputs:
        ans=signatures(np.load(name))
        print(name,'exact signatures',len(ans),'by tip count',np.bincount([sum(i<4 for i in x) for x in ans],minlength=5).tolist(),flush=True)
