"""Unrestricted integral re-rooting identities and graph homomorphism parity reductions."""
from collections import Counter
import pickle
import numpy as np
import scipy.sparse as sp
from pynauty import autgrp,certificate
from hom_moments import Reduce,nauty,tmp
from orbit_arithmetic import parity
from relax_outer3 import setup


def involution(g):
    gens,order,exp,*_=autgrp(nauty(g))
    if round(order*10**exp)%2:return None
    iden=tuple(range(len(g)))
    seen={iden};todo=[iden]
    for a in todo:
        for h in gens:
            x=tuple(h[v] for v in a)
            if x in seen:continue
            if all(x[x[v]]==v for v in iden):return x
            seen.add(x);todo.append(x)
    raise ArithmeticError('even group without involution')

def quotient(g,sigma):
    mp=[min(i,j) for i,j in enumerate(sigma)];ids={v:j for j,v in enumerate(sorted(set(mp)))}
    u=[ids[v] for v in mp];out=[0]*len(ids)
    for i,row in enumerate(g):
        for j in range(i):
            if row>>j&1:
                a,b=u[i],u[j]
                if a==b:return None
                out[a]|=1<<b;out[b]|=1<<a
    return tuple(out)


def run(limit):
    records,graphs=pickle.load(open(tmp/('hom-14-%d.pickle'%limit),'rb'))
    rr=Reduce(14)
    for i,g in enumerate(graphs[1:],1):
        key=certificate(nauty(g));rr.coreid[key]=i;rr.cores[key]=g
    _,_,alive=setup();pop=np.load(tmp/'outer3-14-sizes.npy')
    idx=np.cumsum(alive)-1;n=int(alive.sum())
    # Modulo two the global sum of 99 normalized empty events equals one.
    rows=[]
    for i,(den,c) in records.items():
        q,r=divmod(den,99*int(pop[i]))
        if r:raise ArithmeticError('orbit normalization')
        pairs=[(0,-c.get(0,0))]
        if alive[i]:pairs.append((int(idx[i]),99*q if i==0 else q))
        pairs.extend((n+j-1,-v) for j,v in c.items() if j)
        m=Counter()
        for j,v in pairs:m[j]+=v
        vals=[v for v in m.values() if v]
        if vals:
            div=np.gcd.reduce(vals)
            rows.append([j for j,v in m.items() if (v//div)%2])
    # New cores returned by a reduction are appended in ID order.
    glist=list(graphs);ng=len(glist)
    for i,g in enumerate(glist):
        if not g:continue
        s=involution(g)
        if s is None:continue
        expr=rr.reduce(quotient(g,s))
        if len(rr.cores)>ng:
            glist.extend(list(rr.cores.values())[ng:]);ng=len(glist)
        cols={n+i-1}
        for j,coef in expr:
            if coef%2:cols.symmetric_difference_update([0 if j==0 else n+j-1])
        rows.append(list(cols))
    A=sp.load_npz(tmp/'outer3-14-integral.npz')[:,alive].tocsr()
    A=A[np.diff(A.indptr)>0];h=np.gcd.reduceat(abs(A.data),A.indptr[:-1]);A.data//=np.repeat(h,np.diff(A.indptr))
    w=n+ng-1;ii=[];jj=[]
    for i,row in enumerate(rows):ii.extend([i]*len(row));jj.extend(row)
    extra=sp.csr_matrix((np.ones(len(ii),dtype=np.int8),(ii,jj)),shape=(len(rows),w))
    allrows=sp.vstack([sp.hstack([A,sp.csr_matrix((A.shape[0],ng-1))]),extra],format='csr')
    print('global system',allrows.shape,'hom cores',ng,'additional equations',len(rows),flush=True)
    print('modulo 2',parity(allrows),flush=True)


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--axes',type=int,default=4);a=p.parse_args();run(a.axes)
