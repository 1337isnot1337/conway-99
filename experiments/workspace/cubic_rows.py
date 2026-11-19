"""All third-order full-row histograms for the second neighborhood of an arbitrary vertex."""
from itertools import combinations
import numpy as np
import pynauty

from row_profiles import pairings,templates
from triple_moments import Triples,pack,tmp


def certificate(edges):
    g={i:[] for i in range(21)}
    for a,b in edges:
        a=int(a);b=int(b);g[a].append(b);g[b].append(a)
    for a in range(14):
        v=14+a//2;g[a].append(v);g[v].append(a)
    return pynauty.certificate(pynauty.Graph(21,adjacency_dict=g,vertex_coloring=[{0,2},{1,3},set(range(4,14)),set(range(14,21))]))


def catalogue(m):
    matching=np.array(list(pairings(list(range(4,14)))))
    maps=np.tile(np.arange(14),(len(matching),1))
    maps[np.arange(len(matching))[:,None],matching.reshape(-1,10)]=np.arange(4,14)
    representatives={}
    for edges,divisor in templates():
        labels=maps[:,edges]
        for s in labels[np.all((labels[:,:,0]^1)!=labels[:,:,1],axis=1)]:
            key=certificate(s)
            if key not in representatives:representatives[key]=m.iidx[s[:,0],s[:,1]].copy()
    return np.array(list(representatives.values()),dtype=np.uint8)


def build():
    t=Triples(14);m=t.model;incident=m.edges[0,1:];ix=np.arange(len(incident));lookup=np.zeros((83,83,83),dtype=np.int32)
    for i,x in enumerate(incident):
        v=t.move[x,incident]
        lookup[i]=t.table[t.type[x]][t.pairs[t.type[x]][pack(v[:,None],v[None,:])]]
    # Repeated indices stand for monomials of lower degree; each distinct set occurs exactly once.
    i3=np.array(list(combinations(range(83),3)))
    i2=np.array(list(combinations(range(83),2)))
    whole=np.r_[lookup[ix,ix,ix],lookup[i2[:,0],i2[:,0],i2[:,1]],lookup[*i3.T]]
    columns,den=np.unique(whole,return_counts=True)
    pos=np.full(t.d,-1);pos[columns]=np.arange(len(columns))
    rows=catalogue(m)
    i3=np.array(list(combinations(range(12),3)));i2=np.array(list(combinations(range(12),2)))
    H=np.zeros((len(rows),len(columns)),np.uint16)
    for j,r in enumerate(rows):
        w=r-1
        occ=np.r_[lookup[w,w,w],lookup[w[i2[:,0]],w[i2[:,0]],w[i2[:,1]]],lookup[*w[i3].T]]
        H[j]=np.bincount(pos[occ],minlength=len(columns))
    assert np.all(H.sum(axis=1)==298)
    print('row types',len(rows),'columns',len(columns),'distinct cubic histograms',len(np.unique(H,axis=0)),flush=True)
    np.savez_compressed(tmp/'cubic-rows.npz',rows=rows,columns=columns,den=den,H=H)


if __name__=='__main__':build()
