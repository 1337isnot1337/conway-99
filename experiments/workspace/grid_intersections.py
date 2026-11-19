"""Exact seven-axis profile check and both four-corner matching types."""
from collections import Counter
from itertools import combinations, permutations

import numpy as np


def main():
    edges=list(combinations(range(7),2))
    graph=np.arange(1<<len(edges),dtype=np.uint32)
    k=np.bitwise_count(graph).astype(int)
    match=np.zeros(len(k),dtype=np.int16)
    for i,e in enumerate(edges):
        previous=sum(1<<j for j,f in enumerate(edges[:i]) if set(e).isdisjoint(f))
        match+=((graph>>i)&1)*np.bitwise_count(graph&previous)
    assert np.all(match>=5*k-35)
    assert np.all(4*match>=25*k-195)
    tight=graph[(match==5*k-35)&(4*match==25*k-195)]
    models=set()
    for a,b in edges:
        models.add(sum(1<<i for i,e in enumerate(edges) if a in e or b in e))
    assert set(map(int,tight))==models
    four={tuple(sorted((i,(i+1)%4))) for i in range(4)}
    overlap=Counter(len(four&{tuple(sorted((p[a],p[b]))) for a,b in four}) for p in permutations(range(4)))
    assert overlap=={2:16,4:8}
    print('seven-axis labeled graphs',len(graph),'joint equality models',len(models),'four-cycle overlaps',dict(overlap))
    print('minimum disjoint pairs by size',[int(match[k==i].min()) for i in range(22)])


if __name__=='__main__':main()
