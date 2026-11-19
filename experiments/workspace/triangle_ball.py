"""Project vertices outside a triangle ball against both integral SRG Gram matrices."""
import argparse
from itertools import combinations,product
from pathlib import Path
import numpy as np

def local_ball(n,matching,twist):
    A=np.zeros((3+3*n,3+3*n),dtype=np.int16)
    def edge(i,j): A[i,j]=A[j,i]=1
    for a,b in combinations(range(3),2):edge(a,b)
    def v(s,i):return 3+n*s+i
    for s in range(3):
        for i,j in enumerate(matching[s]):
            edge(s,v(s,i));edge(v(s,i),v(s,j))
    for i,j in enumerate(twist):
        edge(v(0,i),v(1,i));edge(v(0,i),v(2,i));edge(v(1,i),v(2,j))
    return A

def outside_pairs(A):
    n=(len(A)-3)//3
    return [np.array([(3+s*n+i,3+s*n+j) for i,j in combinations(range(n),2) if not A[3+s*n+i,3+s*n+j]]) for s in range(3)]

def projection(A,k):
    # Spectral projectors scaled to have integer entries, with trivial space removed.
    r=int((np.sqrt(4*k-7)-1)/2);s=-1-r;N=k*k//2+1
    # v = 1 + k + k(k-2)/2 = 1 + k^2/2.
    projectors=((r,-1,(k-r)/N),(-s,1,-(k-s)/N))
    E=outside_pairs(A)
    nn=len(A); ix=np.eye(nn)
    masks=[np.sum(ix[p],axis=1) for p in E]
    score=[];constraint=[]
    for diag,adj,allones in projectors:
        G=diag*ix+adj*A+allones
        eig,U=np.linalg.eigh(G)
        if eig[0]<-1e-7:return None
        zero=eig<1e-8
        vectors=U[:,~zero]/np.sqrt(eig[~zero])
        # Projected squared length is the squared norm of a sum of three vectors.
        for transform,is_null in ((vectors,False),(U[:,zero],True)):
            q=[((allones/3)+adj*M)@transform for M in masks]
            d=[(z*z).sum(axis=1) for z in q]
            V=d[0][:,None,None]+d[1][None,:,None]+d[2][None,None,:]
            for a,b in combinations(range(3),2):
                pair=2*q[a]@q[b].T
                V+=np.expand_dims(pair,axis=3-a-b)
            if is_null:constraint.append(V<1e-8)
            else:score.append(diag+allones-V)
    return E,score,constraint

def evaluate(A,k):
    codeg=A@A
    if np.any(np.triu(codeg+A,1)>2):return 'common',None
    proj=projection(A,k)
    if proj is None:return 'eigen',None
    E,score,constraint=proj
    allowed=(score[0]>-1e-8)&(score[1]>-1e-8)&constraint[0]&constraint[1]
    # An outside vertex consumes one common neighbor between each of its six anchors.
    left=2-A-codeg
    for a,b in combinations(range(3),2):
        compatibility=np.all(left[E[a][:,None,:,None],E[b][None,:,None,:]]>0,axis=(2,3))
        allowed&=np.expand_dims(compatibility,axis=3-a-b)
    minimum=min(np.min(allowed.sum(axis=((s+1)%3,(s+2)%3))) for s in range(3))
    return (int(allowed.sum()),int(minimum)),(E,allowed)

def golay():
    # Enumerate the additive field of order 243, using a degree-five factor of Phi_11.
    for coefficients in product(range(3),repeat=5):
        if not coefficients[0]:continue
        poly=np.array(coefficients)
        a=np.array([1,0,0,0,0]);steps=[]
        for _ in range(11):
            steps.extend([a,(-a)%3])
            a=(np.r_[0,a[:-1]]-a[-1]*poly)%3
        if list(a)==[1,0,0,0,0]:break
    else:raise ArithmeticError("no factor of Phi_11")
    points=np.array(list(product(range(3),repeat=5)))
    index={tuple(p):i for i,p in enumerate(points)}
    A=np.zeros((243,243),np.int16)
    for i,p in enumerate(points):
        A[i,[index[tuple((p+d)%3)] for d in steps]]=1
    assert np.all(A@A+A==20*np.eye(243,dtype=int)+2)
    i=0;j=np.flatnonzero(A[i])[0];h=np.flatnonzero(A[i]*A[j])[0];tri=[i,j,h]
    layers=[sorted(set(np.flatnonzero(A[z]))-set(tri)) for z in tri]
    idx=tri+sum(layers,[]); B=A[np.ix_(idx,idx)]
    return A,B,idx

def run(rounds):
    rng=np.random.default_rng(901)
    def matching():
        p=rng.permutation(12);q=p.copy();q[p]=p[np.arange(12)^1];return q
    for i in range(rounds):
        M=[matching() for _ in range(3)]
        twist=rng.permutation(12)
        A=local_ball(12,M,twist);status,_=evaluate(A,14)
        print(i,status,flush=True)
        if isinstance(status,tuple) and not Path('triangle-example.npy').exists():np.save('triangle-example.npy',A)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--golay',action='store_true');p.add_argument('--rounds',type=int,default=4)
    opt=p.parse_args()
    if opt.golay:
        A,B,idx=golay()
        status,ans=evaluate(B,22)
        E,ok=ans
        lookup=[{tuple(pair):j for j,pair in enumerate(M)} for M in E]
        for v in set(range(243))-set(idx):
            near=np.flatnonzero(A[v,idx]);triple=tuple(lookup[s][tuple(near[2*s:2*s+2])] for s in range(3))
            assert ok[triple]
        print('verified all 180 outside vertices of the Golay graph',status,flush=True)
    else:run(opt.rounds)
