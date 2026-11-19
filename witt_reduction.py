"""Select a quadruple from each hexad of the Witt design for a candidate 22-coclique."""
import argparse
from itertools import combinations
from collections import Counter
import numpy as np
import pynauty
from ortools.sat.python import cp_model
from triple_moments import tmp


def hexads():
    generator=sum(1<<i for i in (0,1,5,6,7,9,11));octads=[]
    for m in range(4096):
        w=0
        for j in range(12):
            if m>>j&1:w^=generator<<j
        w|=(w.bit_count()%2)<<23
        if w.bit_count()==8:octads.append(w)
    assert len(octads)==759
    H=sorted(w&((1<<22)-1) for w in octads if w>>22==3)
    assert len(H)==77 and len({t for h in H for t in combinations([i for i in range(22) if h>>i&1],3)})==1540
    return H


def point_action(H,order):
    if order==1:return tuple(range(22))
    N={22+j:[i for i in range(22) if h>>i&1] for j,h in enumerate(H)}
    G=pynauty.Graph(99,adjacency_dict=N,vertex_coloring=[set(range(22)),set(range(22,99))])
    gs=np.array(pynauty.autgrp(G)[0])[:,:22];ident=np.arange(22);rng=np.random.default_rng(42);perm=ident.copy()
    for _ in range(5000):
        perm=gs[rng.integers(len(gs))][perm];powers=[ident]
        x=perm
        while not np.array_equal(x,ident):powers.append(x);x=perm[x]
        if len(powers)%order==0:return tuple(powers[len(powers)//order])
    raise ValueError(order)


def run(order,seconds,count):
    H=hexads();act=point_action(H,order)
    def shift(m):return sum(1<<int(act[i]) for i in range(22) if m>>i&1)
    available={(j,sum(1<<i for i in q)) for j,h in enumerate(H) for q in combinations([i for i in range(22) if h>>i&1],4)}
    index={h:j for j,h in enumerate(H)};orbits=[]
    while available:
        a=min(available);o=[]
        while a in available:
            available.remove(a);o.append(a);a=index[shift(H[a[0]])],shift(a[1])
        if len({i for i,m in o})==len(o):orbits.append(o)
    model=cp_model.CpModel();xs=[model.new_bool_var('') for _ in orbits]
    shapes=[[] for _ in H];pairs={p:[] for p in combinations(range(22),2)}
    for x,o in zip(xs,orbits):
        for j,m in o:
            shapes[j].append(x)
            for p in combinations([i for i in range(22) if m>>i&1],2):pairs[p].append(x)
    for v in shapes:model.add_exactly_one(v)
    for v in pairs.values():model.add(sum(v)==2)
    solver=cp_model.CpSolver();solver.parameters.num_workers=2;solver.parameters.max_time_in_seconds=seconds
    print('order',order,'quadruple orbit choices',len(orbits),flush=True)
    if count==0:
        solver.parameters.num_workers=1;solver.parameters.enumerate_all_solutions=True
        with (tmp/('witt-census-%d.txt'%order)).open('w') as out:
            class Collect(cp_model.CpSolverSolutionCallback):
                number=0
                def on_solution_callback(self):
                    M=[m for x,o in zip(xs,orbits) if self.value(x) for _,m in o]
                    assert len(M)==77
                    print(*M,file=out);self.number+=1
            cb=Collect();status=solver.solve(model,cb)
            print('census',solver.status_name(status),'solutions',cb.number,flush=True)
        return
    for n in range(count):
        status=solver.solve(model);print('design search',n,solver.status_name(status),'branches',solver.num_branches,flush=True)
        if status not in (cp_model.OPTIMAL,cp_model.FEASIBLE):break
        sel=[i for i,x in enumerate(xs) if solver.value(x)];M=[m for i in sel for j,m in orbits[i]]
        assert len(M)==77 and len(set(M))==77 and all((a&b).bit_count()<=2 for a,b in combinations(M,2))
        N=np.array([[(m>>i)&1 for m in M] for i in range(22)],np.int16)
        assert np.array_equal(N@N.T,12*np.eye(22)+2)
        np.savez_compressed(tmp/('witt-reduction-%d-%d.npz'%(order,n)),N=N)
        model.add_bool_or([~xs[i] for i in sel])


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('order',type=int);p.add_argument('--seconds',type=int,default=30);p.add_argument('--count',type=int,default=1);a=p.parse_args();run(a.order,a.seconds,a.count)
