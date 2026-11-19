"""Join the full neighborhoods of two nonadjacent vertices along all remaining vertices."""
import argparse
from itertools import combinations
from pathlib import Path
import numpy as np
from ortools.sat.python import cp_model

from triangle_ball import golay
from triple_moments import tmp
from row_profiles import pairings


def neighborhood(k,labels,m):
    # Vertex order: o, e, common anchors 0,2, other first anchors, remaining second anchors.
    base=[0,2,*[i for i in range(k) if i not in (0,2)]]
    pos={v:2+i for i,v in enumerate(base)};end=k+2
    B=np.zeros((2*k,2*k),np.int16)
    def edge(i,j):B[i,j]=B[j,i]=1
    for a in base:
        edge(0,pos[a])
        if a%2==0:edge(pos[a],pos[a+1])
    for a in (0,2):edge(1,pos[a])
    for j,(a,b) in enumerate(labels):
        v=end+j;edge(1,v);edge(pos[a],v);edge(pos[b],v)
    for i,j in m:edge(end+i,end+j)
    return B


def sample(seed):
    rng=np.random.default_rng(seed)
    z=np.load(tmp/'cubic-rows.npz');allpairs=[p for p in combinations(range(14),2) if p[0]^1!=p[1]]
    labels=[allpairs[j] for j in z['rows'][rng.integers(len(z['rows']))]]
    rest=[i for i,p in enumerate(labels) if not set(p)&{0,2}]
    choices=[m for m in pairings(rest) if all(set(labels[i]).isdisjoint(labels[j]) for i,j in m)]
    return neighborhood(14,labels,choices[rng.integers(len(choices))])


def prepare(B):
    k=len(B)//2;v=1+k*k//2
    quota=(k-2)*np.eye(len(B),dtype=int)+2-B-B@B
    assert np.all(quota>=0) and not np.any(quota[:2])
    sides=[]
    for root in range(2):
        neigh=np.flatnonzero(B[root]);catalog=[]
        for i,j in combinations(neigh,2):
            if not B[i,j] and B[i]@B[j]==1:catalog.append((int(i),int(j)))
        assert len(catalog)==v-len(B)
        sides.append(catalog)
    shared=set(np.flatnonzero(B[0]*B[1]));R=[];pairs=[]
    for i,p in enumerate(sides[0]):
        for j,q in enumerate(sides[1]):
            if set(p)&shared!=set(q)&shared:continue
            u=sorted(set(p+q))
            if any(quota[a,b]==0 for a,b in combinations(u,2)):continue
            r=np.zeros(len(B),np.int16);r[u]=1;R.append(r);pairs.append((i,j))
    return sides,np.array(pairs),np.array(R),quota


def validate(B,R):
    k=len(B)//2
    return np.array_equal(B@B+B+R@R.T,(k-2)*np.eye(len(B),dtype=int)+2)


def control():
    G,_,_=golay()
    a=0;b=next(i for i in range(1,len(G)) if not G[a,i]);idx=[a,b,*np.flatnonzero(G[a]+G[b])]
    ext=sorted(set(range(len(G)))-set(idx));B=G[np.ix_(idx,idx)];true=G[np.ix_(idx,ext)]
    sides,pairs,R,Q=prepare(B)
    assert validate(B,true)
    candidates={r.tobytes() for r in R}
    assert all(r.tobytes() in candidates for r in true.T)
    print('Golay exact square and all',len(ext),'actual incidence columns checked; candidate signatures',len(R),flush=True)


def model_cover(B,secs):
    sides,pairs,R,Q=prepare(B)
    model=cp_model.CpModel();xs=[model.new_bool_var('') for _ in R]
    for c in range(2):
        for i in range(len(sides[c])):model.add_exactly_one(xs[j] for j in np.flatnonzero(pairs[:,c]==i))
    for i,j in combinations(range(len(B)),2):
        ix=np.flatnonzero(R[:,i]*R[:,j])
        if len(ix):model.add(sum(xs[t] for t in ix)==int(Q[i,j]))
        elif Q[i,j]:return 'IMPOSSIBLE',None
    solver=cp_model.CpSolver();solver.parameters.max_time_in_seconds=secs;solver.parameters.num_workers=2
    status=solver.solve(model)
    if status not in (cp_model.FEASIBLE,cp_model.OPTIMAL):return solver.status_name(status),None
    chosen=np.array([solver.value(v) for v in xs],bool);N=R[chosen].T.copy()
    assert validate(B,N)
    return 'SAT',N


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--control',action='store_true');p.add_argument('--seed',type=int,default=1);p.add_argument('--seconds',type=int,default=30);a=p.parse_args()
    if a.control:control()
    else:
        B=sample(a.seed);status,N=model_cover(B,a.seconds);print(a.seed,status,flush=True)
        if N is not None:np.savez_compressed(tmp/('pair-cover-%d.npz'%a.seed),B=B,N=N)
