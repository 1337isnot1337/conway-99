"""Classify the seven deleted lines at one point of the Witt design and fix them in the search."""
from collections import Counter
from itertools import combinations
import argparse
import numpy as np
from ortools.sat.python import cp_model
import pynauty
from witt_reduction import hexads
from triple_moments import tmp


def cases(H):
    lines=[h for h in H if h&1];neighborhood={22+j:[i for i in range(22) if h>>i&1] for j,h in enumerate(H)}
    G=pynauty.Graph(99,adjacency_dict=neighborhood,vertex_coloring=[{0},set(range(1,22)),set(range(22,99))])
    generators=pynauty.autgrp(G)[0];maps=[[lines.index(H[g[22+H.index(h)]-22]) for h in lines] for g in generators]
    idx={tuple(z):i for i,z in enumerate(combinations(range(21),7))}
    raw=np.array(list(idx),np.int16);valid=np.ones(len(raw),bool)
    for p in range(1,22):valid&=(np.array([(h>>p)&1 for h in lines])[raw].sum(axis=1)<=3)
    from scipy.sparse.csgraph import connected_components
    from scipy.sparse import coo_matrix
    rows=[];cols=[]
    for g in maps:
        t=np.sort(np.array(g)[raw],axis=1)
        js=np.array([idx[tuple(z)] for z in t],int);assert np.array_equal(valid,valid[js])
        rows.extend(np.flatnonzero(valid));cols.extend(js[valid])
    _,cc=connected_components(coo_matrix((np.ones(len(rows),np.int8),(rows,cols)),shape=(len(raw),len(raw))),directed=False)
    vs=np.flatnonzero(valid);names,rep,sz=np.unique(cc[vs],return_index=True,return_counts=True)
    C=[([lines[i] for i in raw[vs[r]]],int(s)) for r,s in zip(rep,sz)]
    return sorted(C,key=lambda z:z[1])


def solve(H,removed,seconds,seed,tag,warm=None):
    model=cp_model.CpModel();xs={};rows=[];pairs={p:[] for p in combinations(range(22),2)}
    for j,h in enumerate(H):
        choices=[]
        for p in combinations([i for i in range(22) if h>>i&1],4):
            if h&1 and ((0 not in p)!=(h in removed)):continue
            b=sum(1<<i for i in p);v=model.new_bool_var('');xs[b]=v;choices.append(v)
            for ij in combinations(p,2):pairs[ij].append(v)
        model.add_exactly_one(choices)
    for v in pairs.values():model.add(sum(v)==2)
    if warm:
        for b,x in xs.items():model.add_hint(x,int(b in warm))
        model.add(sum(xs[b] for b in warm if b in xs)<=76)
    solver=cp_model.CpSolver();solver.parameters.num_workers=2;solver.parameters.random_seed=seed;solver.parameters.max_time_in_seconds=seconds
    s=solver.solve(model);print(tag,solver.status_name(s),solver.num_branches,flush=True)
    if s not in (cp_model.OPTIMAL,cp_model.FEASIBLE):return None
    M=[b for b,v in xs.items() if solver.value(v)];N=np.array([[(b>>i)&1 for b in M] for i in range(22)],np.int16)
    assert len(M)==77 and np.array_equal(N@N.T,12*np.eye(22)+2)
    np.savez_compressed(tmp/('witt-local-%s.npz'%tag),N=N)
    return M


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--case',type=int);p.add_argument('--seconds',type=int,default=12);p.add_argument('--warm',action='store_true');a=p.parse_args()
    H=hexads()
    if a.warm:
        b=set(map(int,(tmp/'witt-census-7.txt').read_text().splitlines()[0].split()))
        removed=[h for h in H if h&1 and not next(z for z in b if z&h==z)&1]
        solve(H,removed,a.seconds,761,'warm',b)
    else:
        C=cases(H);print('point-stabilizer cases',len(C),'orbit sizes',[n for _,n in C],flush=True)
        for j,(r,n) in enumerate(C):
            if a.case is None or a.case==j:solve(H,r,a.seconds,741+j,str(j))
