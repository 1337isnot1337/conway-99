"""Enumerate rooted outer-neighborhood shapes and their edge-moment histograms."""
from collections import Counter
from itertools import combinations
from pathlib import Path
import numpy as np
from outer_moments import OrbitModel


def pairings(items):
    if not items:
        yield ()
        return
    a,*tail=items
    for j,b in enumerate(tail):
        for rest in pairings(tail[:j]+tail[j+1:]):
            yield ((a,b),)+rest


def cycle_parts(n,lo=3):
    if not n:
        yield ()
    for t in range(lo,n+1):
        for rest in cycle_parts(n-t,t):
            yield (t,)+rest


def templates():
    for endpairs in pairings(list(range(4))):
        for s in range(11):
            for t in range(11-s):
                for cycles in cycle_parts(10-s-t):
                    edges=[]
                    start=4
                    divisor=1
                    for (a,b),n in zip(endpairs,(s,t)):
                        path=[a,*range(start,start+n),b]
                        edges.extend(zip(path,path[1:]))
                        start+=n
                    for n in cycles:
                        edges.extend((start+i,start+(i+1)%n) for i in range(n))
                        start+=n
                        divisor*=2*n
                    from math import factorial
                    for mult in Counter(cycles).values(): divisor*=factorial(mult)
                    if all(tuple(sorted(e)) not in ((0,1),(2,3),(0,2)) for e in edges):
                        yield np.array(edges),divisor


def build():
    from math import factorial
    m=OrbitModel(14)
    root=0
    assert m.labels[root]==(0,2)
    incident=m.edges[root]
    possible=incident[np.arange(m.n)!=root]
    u,v=np.tril_indices(len(possible),-1)
    den=np.bincount(np.r_[m.C[0,possible],m.C[possible[u],possible[v]]],minlength=m.dim)
    columns=np.flatnonzero(den)
    class_code=np.full(m.dim,-1);class_code[columns]=np.arange(len(columns))
    matchings=np.array(list(pairings(list(range(4,14)))))
    maps=np.tile(np.arange(14),(len(matchings),1))
    maps[np.arange(len(matchings))[:,None],matchings.reshape(-1,10)]=np.arange(4,14)
    row_pair=np.tril_indices(12,-1)
    profiles=set();shapes=0;weighted=0;templates_count=0
    for edges,divisor in templates():
        templates_count+=1
        labels=maps[:,edges]
        good=np.all((labels[:,:,0]^1)!=labels[:,:,1],axis=1)
        labels=labels[good]
        if not len(labels):continue
        shapes+=len(labels)
        count=len(labels)*3840
        assert count%divisor==0
        weighted+=count//divisor
        selected=incident[m.iidx[labels[:,:,0],labels[:,:,1]]]
        c=class_code[np.column_stack((m.C[0,selected],m.C[selected[:,row_pair[0]],selected[:,row_pair[1]]]))]
        histogram=np.zeros((len(c),len(columns)),np.uint8)
        np.add.at(histogram,(np.arange(len(c))[:,None],c),1)
        profiles.update(row.tobytes() for row in histogram)
    H=np.array([np.frombuffer(data,np.uint8) for data in sorted(profiles)])
    assert weighted==56011010 and np.all(H.sum(axis=1)==78)
    print('templates',templates_count,'labeled rows',weighted,'shape candidates',shapes,'distinct profiles',len(H),'moment columns',len(columns),flush=True)
    np.savez_compressed(Path(__file__).with_name('row-profiles.npz'),H=H,columns=columns,den=den[columns])


if __name__=='__main__':build()
