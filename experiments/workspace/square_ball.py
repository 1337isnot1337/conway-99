"""Construct and test induced neighborhoods of a square, with the four corner rows complete."""
from collections import Counter
from itertools import product,combinations
import argparse
import numpy as np


def square_ball(cross,rng):
    n=10
    B=np.zeros((48,48),dtype=np.int16)
    def edge(a,b):B[a,b]=B[b,a]=1
    private=[np.arange(8+n*i,8+n*(i+1)) for i in range(4)]
    for i,X in enumerate(private):
        edge(i,(i+1)%4);edge(4+i,i);edge(4+i,(i+1)%4)
        edge(i,X);edge(X[::2],X[1::2])
    for i in range(2):
        if cross[i]:
            edge(4+i,6+i)
        else:
            for t in (i,i+2):
                for j in ((t+2)%4,(t+3)%4):
                    edge(4+t,rng.choice(private[j]))
    for i,j in combinations(range(4),2):
        X,Y=private[i],private[j]
        degrees_x=2-(B[X]@B[j])
        degrees_y=2-(B[Y]@B[i])
        assert np.all(degrees_x>=0) and np.all(degrees_y>=0)
        xx=np.repeat(X,degrees_x);yy=np.repeat(Y,degrees_y)
        assert len(xx)==len(yy)
        while True:
            rng.shuffle(yy)
            if len(set(zip(xx,yy)))==len(xx): break
        edge(xx,yy)
    # The strong-regularity equations with either endpoint in the square are exact.
    assert np.all((B@B+B)[:4]==(12*np.eye(48,dtype=int)+2)[:4])
    return B


def metrics(A,k=14):
    n=len(A)
    common=A@A
    violation=int(np.maximum(0,np.triu(common+A,1)-2).sum())
    r=int((np.sqrt(4*k-7)-1)//2);s=-1-r;v=1+k*k//2
    G=r*np.eye(n)-A+(k-r)/v
    H=-s*np.eye(n)+A-(k-s)/v
    g=np.linalg.eigvalsh(G);h=np.linalg.eigvalsh(H)
    return violation,g,h

def control():
    from triangle_ball import golay
    A,_,_=golay();a=0
    for b in np.flatnonzero(A[a]):
        c=next(c for c in np.flatnonzero(A[b]) if not A[a,c] and c!=a)
        d=next(d for d in np.flatnonzero(A[c]*A[a]) if d!=b)
        core=[a,b,c,d];break
    inner=sorted(set(np.flatnonzero(A[core].sum(axis=0)))-set(core))
    tips=[];private=[]
    for j in range(4):
        t=next(v for v in inner if A[core[j],v] and A[core[(j+1)%4],v]);tips.append(t)
        private.extend(v for v in inner if A[core[j],v] and A[core,v].sum()==1)
    idx=core+tips+private;B=A[np.ix_(idx,idx)]
    assert len(set(idx))==80 and np.all((B@B+B)[:4]==(20*np.eye(80,dtype=int)+2)[:4])
    err,g,h=metrics(B,22)
    assert err==0 and min(g[0],h[0])>-1e-8
    exterior=sorted(set(range(243))-set(idx));E=A[np.ix_(idx,exterior)]
    assert np.all(B@B+B+E@E.T==20*np.eye(80,dtype=int)+2)
    print('Golay square ball',len(idx),'outside',len(exterior),'ranks',sum(g>1e-8),sum(h>1e-8),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--rounds',type=int,default=1000);p.add_argument('--control',action='store_true')
    args=p.parse_args()
    if args.control:control()
    else:
        rng=np.random.default_rng(1501)
        for cross in [(0,0),(0,1),(1,1)]:
            counts=Counter();best=100
            for rep in range(args.rounds):
                A=square_ball(cross,rng)
                err,g,h=metrics(A)
                counts['codegree_OK']+=err==0
                counts['spectrum_OK']+=min(g[0],h[0])>-1e-8
                counts['both']+=err==0 and min(g[0],h[0])>-1e-8
                score=err+max(0,-g[0])+max(0,-h[0])
                if score<best:
                    best=score;np.save('square-%d%d-best.npy'%cross,A)
            print(cross,dict(counts),'sample',args.rounds,'best cost',best,flush=True)
