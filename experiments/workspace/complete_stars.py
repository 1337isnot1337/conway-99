"""Extend a speculative core by whole neighborhoods until its rank determines every exterior signature."""
from collections import Counter
from itertools import combinations
from pathlib import Path
import numpy as np
from pysat.solvers import Minicard
from core_extensions import lifts,cover
from root_search import verify
from row_profiles import pairings
import json

tmp=Path('/tmp/conway99-tools')


def finish(A,Y):
    # If exactly one copy of every candidate is forced, test the uniquely determined adjacency matrix.
    from scipy.linalg import qr
    if len(Y)!=99-len(A) or len(set(map(tuple,Y)))!=len(Y):return False
    n=len(A);G=3*np.eye(n)-A+1/9
    U=np.linalg.pinv(G,hermitian=True);q=1/9-Y
    gram=q@U@q.T
    F=3*np.eye(len(Y))+1/9-gram
    if np.max(abs(F-np.rint(F)))>1e-8:return False
    F=np.rint(F).astype(int)
    if np.min(F)<0 or np.max(F)>1 or np.any(np.diag(F)):return False
    B=np.block([[A,Y.T],[Y,F]])
    rows=[sum(1<<int(j) for j in np.flatnonzero(row)) for row in B]
    try:verify(rows,14)
    except AssertionError:return False
    Path('verified-construction.json').write_text(json.dumps(list(map(str,rows))))
    return True


def additions(A,Y,p,limit,stats):
    n=len(A);cap=12*np.eye(n,dtype=int)+2-A-A@A;R=cap[p];mask=Y[:,p]>0
    Z=Y[mask]
    ok=np.all((Z==0)|(R>0),axis=1);Z=Z[ok]
    if not len(Z):return
    K=A[p]>0;fixed=Z[:,K].sum(axis=1)
    with Minicard() as s:
        m=len(Z);ids=np.arange(1,m+1)
        groups=[]
        for j in range(n):
            literals=ids[Z[:,j]>0].tolist();h=int(R[j])
            if h>len(literals):return
            if h<len(literals):s.add_atmost(literals,h)
            if h:s.add_atmost([-l for l in literals],len(literals)-h)
        for i,j in combinations(range(n),2):
            d=ids[(Z[:,i]*Z[:,j])!=0].tolist()
            if len(d)>cap[i,j]:s.add_atmost(d,int(cap[i,j]))
        # Two new neighbors have p in common and at most one more common vertex.
        P=Z@Z.T
        allow=[np.ones((m,m),bool) for _ in range(2)]
        for d,adj,c in ((3,-1,1/9),(4,1,-2/11)):
            G=d*np.eye(n)+adj*A+c;B=adj*Z+c
            T=B@np.linalg.pinv(G,hermitian=True)@B.T
            residual=d+c-T.diagonal();bound=np.sqrt(np.maximum(0,residual[:,None]*residual[None,:]))
            for a in (0,1):allow[a]&=np.abs(c+adj*a-T)<=bound+1e-8
        pair_ok=allow[0]|(allow[1]&(fixed[:,None]==0)&(fixed[None,:]==0)&(P==1))
        for i,j in zip(*np.where(np.triu((P>2)|(~pair_ok),1))):s.add_clause([-int(i+1),-int(j+1)])
        for iteration in range(limit):
            if not s.solve():
                stats["star domains exhausted"]+=1;return
            stats["star assignments examined"]+=1
            idx=np.array([l-1 for l in s.get_model() if 0<l<=m],dtype=int)
            s.add_clause([int(-j-1) for j in idx])
            X=Z[idx]
            unpaired=np.flatnonzero(fixed[idx]==0).tolist()
            if len(unpaired)%2:continue
            for matching in pairings(unpaired):
                F=np.zeros((len(X),len(X)),dtype=np.int16)
                for a,b in matching:F[a,b]=F[b,a]=1
                if np.any(np.triu((F==0)&(~allow[0][np.ix_(idx,idx)]),1)):continue
                if np.any((F>0)&(~allow[1][np.ix_(idx,idx)])):continue
                B=np.block([[A,X.T],[X,F]])
                if np.any(np.triu(B@B+B,1)>2):continue
                G=3*np.eye(len(B))-B+1/9;H=4*np.eye(len(B))+B-2/11
                g=np.linalg.eigvalsh(G);h=np.linalg.eigvalsh(H)
                if min(g[0],h[0]) < -1e-8 or sum(g>1e-7)>44 or sum(h>1e-7)>54:continue
                yield B,int(sum(g>1e-7))


def run(A,Y,stats,depth,limit,rng):
    pvals=[p for p in range(8,14) if A[p].sum()<14]
    if not pvals:return
    # Complete the star with fewest candidate signatures per required neighbor.
    p=min(pvals,key=lambda p: Y[:,p].sum()/(14-A[p].sum()))
    S=[tuple(np.flatnonzero(row)) for row in Y]
    for B,rank in additions(A,Y,p,limit,stats):
        stats['stars passing Gram']+=1
        Z=lifts(A,B,S,[p],[range(len(A),len(B))])
        if not len(Z):continue
        if rank==44:
            stats['rank 44']+=1
            if len(Z)<99-len(B):
                # Duplicates cannot represent distinct vertices with identical full projections.
                continue
            if finish(B,Z):raise SystemExit('FULL CONSTRUCTION VERIFIED')
        if cover(B,Z)[0]:continue
        stats['all positive cell capacities supplied']+=1
        if depth:
            run(B,Z,stats,depth-1,min(limit,12),rng)


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--samples',type=int,default=20);p.add_argument('--cores',type=int,default=25);args=p.parse_args()
    stats=Counter();rng=np.random.default_rng(250)
    for j in range(args.cores):
        if (tmp/('grid39-dual-0-%d.npz'%j)).exists():continue
        A=np.load(tmp/('grid-core39-0-%d.npy'%j));Y=np.load(tmp/('grid39-signatures-0-%d.npz'%j))['Y']
        run(A,Y,stats,2,args.samples,rng)
        print('core',j,'cumulative',dict(stats),flush=True)
