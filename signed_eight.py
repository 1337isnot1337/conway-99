"""Enumerate the bipartite cores of integral negative eigenvectors of squared norm 16."""
from itertools import combinations
from functools import cache
from collections import Counter
import pynauty
import argparse,math
from pathlib import Path
import json

def graph(rows):
    n=8+len(rows);g={i:[] for i in range(n)}
    for j,r in enumerate(rows,8):
        for i in range(8):
            if r>>i&1:g[i].append(j);g[j].append(i)
    return pynauty.Graph(n,adjacency_dict=g,vertex_coloring=[set(range(8)),set(range(8,n))])

def census():
    masks=[sum(1<<i for i in s) for s in combinations(range(8),4)]
    states=[(masks[0],)]
    for k in range(1,8):
        reps={}
        for rows in states:
            deg=[sum(r>>i&1 for r in rows) for i in range(8)]
            hi=sum(1<<i for i,d in enumerate(deg) if d==4)
            lo=sum(1<<i for i,d in enumerate(deg) if d==4-(8-k))
            ex=[(1<<i)|(1<<j) for i,j in combinations(range(8),2) if sum((r>>i & r>>j)&1 for r in rows)==2]
            for m in masks:
                if m&hi or lo&~m or any(e&m==e for e in ex) or any((m&r).bit_count()>2 for r in rows):continue
                rr=rows+(m,);cert=pynauty.certificate(graph(rr))
                if cert not in reps:reps[cert]=rr
        states=list(reps.values());print('rows',k+1,'classes',len(states),flush=True)
    Path('signed-eight-cores.json').write_text(json.dumps(states)+'\n')
    return states

def count_bound(rows):
    g=graph(rows)
    ng=[sum(1<<j for j in g.adjacency_dict[i]) for i in range(16)]
    auto=pynauty.autgrp(g);order=round(auto[1])*10**auto[2]
    # Assign any still-unknown site with two or more known neighbors.
    # In an embedding its domain is at most two; every common neighbor already
    # assigned other than the new site subtracts one from that bound.
    full=(1<<16)-1
    @cache
    def extend(seen):
        if seen==full:return 0
        best=100
        for i,b in enumerate(ng):
            if seen>>i&1:continue
            old=[j for j in range(16) if b&seen & (1<<j)]
            if len(old)<2:continue
            forced=len(old)>=3 or any(ng[j]&ng[k]&seen for j,k in combinations(old,2))
            best=min(best,(not forced)+extend(seen|1<<i))
            if best==0:break
        return best
    bounds=[]
    # An ordered pair of nonadjacent vertices has two common neighbors.
    for a,b in combinations(range(8),2):
        forks=extend(1<<a|1<<b)
        if forks<100:bounds.append((99*84*2**forks,'pair',forks))
    # A star with center and prescribed ordered neighbors from independent mate axes.
    for a in range(16):
        for k in (2,3,4):
            for near in combinations(g.adjacency_dict[a],k):
                forks=extend((1<<a)|sum(1<<j for j in near))
                if forks<100:bounds.append((99*math.perm(7,k)*2**(k+forks),'star'+str(k),forks))
    # A same-side triple, with or without a marked common neighbor.
    for tri in combinations(range(8),3):
        if ng[tri[0]]&ng[tri[1]]&ng[tri[2]]:continue
        forks=extend(sum(1<<i for i in tri))
        if forks<100:bounds.append((6*98406*2**forks,'triple',forks))
    return min(bounds),order

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--regenerate',action='store_true');a=p.parse_args()
    states=census() if a.regenerate else json.loads(Path('signed-eight-cores.json').read_text())
    total=0
    for i,s in enumerate(states):
        (bound,kind,cost),order=count_bound(s)
        total+=bound//order
        print('core',i,'aut',order,'seed',kind,'forks',cost,'bound',bound//order,flush=True)
    print('signed vector upper bound',total,flush=True)
