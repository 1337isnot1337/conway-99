"""Enumerate every exterior attachment at a two-full-axis core and filter by integral nullspace."""
import numpy as np
from itertools import combinations,product
from collections import Counter
from flint import fmpz_mat
from two_full_axes import core,pairs,tmp

def signatures(B,f):
    relevant=[15+4*i for i,e in enumerate(pairs) if not set(f)&set(e)]
    assert len(relevant)==7
    choices=np.array(list(product(range(4),repeat=7)),dtype=int)+relevant
    n=len(choices);p,q=f
    for a,b in product(range(2),repeat=2):
        anchors=np.column_stack((np.full(n,1+2*p+a),np.full(n,1+2*q+b),choices))
        yield anchors

def checks(B):
    M=12*np.eye(len(B),dtype=int)+2-B-B@B
    K,null=fmpz_mat(M.tolist()).nullspace()
    K=np.array(K.tolist(),dtype=object)[:,:null].T
    import math
    K=np.array([[int(x)//math.gcd(*(int(y) for y in row)) for x in row] for row in K],dtype=np.int64)
    assert np.max(np.abs(K))*9<2**60 and not np.any(K@M)
    return M,K

def eligible(B,f,M,K):
    n=len(B)
    for anchors in signatures(B,f):
        ok=np.ones(len(anchors),bool)
        for k in K:
            if not np.any(ok):break
            ids=np.flatnonzero(ok);ok[ids]=np.sum(k[anchors[ids]],axis=1)==0
        anchors=anchors[ok]
        for i,j in combinations(range(9),2):anchors=anchors[M[anchors[:,i],anchors[:,j]]>0]
        if len(anchors):
            R=np.zeros((len(anchors),n),dtype=np.int16);R[np.arange(len(anchors))[:,None],anchors]=1
            R=R[np.all(R@(B+np.eye(n,dtype=int))<=2,axis=1)]
        else:R=np.empty((0,n),dtype=np.int16)
        yield R

if __name__=='__main__':
    for q in np.load(tmp/'two-full-cores.npy'):
        B=core(q);M,K=checks(B);print('core',q,'rank',len(B)-len(K),flush=True)
        out=[]
        for f in combinations(range(2,7),2):
            D=list(eligible(B,f,M,K));out.extend(D);print(f,list(map(len,D)),flush=True)
        np.savez_compressed(tmp/'two-full-signatures.npz',B=B,Y=np.vstack(out),sizes=np.array(list(map(len,out))))
