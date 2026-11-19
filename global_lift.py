"""Link root populations, homomorphism counts, domain automorphisms and small subgraph counts modulo 2^e."""
from collections import Counter
from functools import lru_cache,reduce
from itertools import combinations
from math import gcd
import argparse,pickle

import numpy as np
import scipy.sparse as sp
from pynauty import autgrp,certificate

from core_counts import exact_conditions
from hom_moments import Reduce,bits,nauty,tmp
from power_two import solve
from relax_outer3 import setup


def compose(a,b):return tuple(a[x] for x in b)


def group(g):
    generators,order,exponent,*_=autgrp(nauty(g))
    one=tuple(range(len(g)));all_=[one];seen={one}
    for a in all_:
        for b in generators:
            u=compose(a,b)
            if u not in seen:seen.add(u);all_.append(u)
    assert len(all_)==round(order*10**exponent)
    return all_


def two_subgroups(g,limit):
    full=group(g);one=full[0];sub=[frozenset([one])];seen=set(sub)
    for h in sub:
        if len(h)>=limit:continue
        # Every nontrivial finite 2-group is an index-two extension of a normal subgroup.
        for s in full[1:]:
            if s in h or compose(s,s) not in h:continue
            coset={compose(s,t) for t in h}
            if coset!={compose(t,s) for t in h}:continue
            new=h|coset
            if new not in seen:seen.add(new);sub.append(new)
    return sub[1:]


def project(g,p):
    n=max(p)+1;out=[0]*n
    for i,row in enumerate(g):
        for j in bits(row):
            a,b=p[i],p[j]
            if a==b:return None
            out[a]|=1<<b
    return tuple(out)


def fixed(g,perm):
    labels=[-1]*len(g);m=0
    for i in range(len(g)):
        if labels[i]!=-1:continue
        j=i
        while labels[j]==-1:labels[j]=m;j=perm[j]
        m+=1
    return project(g,labels)


def kernel_partitions(g):
    # Bell partitions whose blocks are independent sets. Each is one possible kernel of a homomorphism.
    labels=[];classes=[]
    def rec(i):
        if i==len(g):yield project(g,labels);return
        for q,mask in enumerate(classes):
            if g[i]&mask:continue
            classes[q]|=1<<i;labels.append(q)
            yield from rec(i+1)
            labels.pop();classes[q]=mask
        labels.append(len(classes));classes.append(1<<i)
        yield from rec(i+1)
        classes.pop();labels.pop()
    yield from rec(0)


def system(axes,e,prime=None):
    mod=prime if prime is not None else 2**e;rows=set()
    def add(terms,divisor=0):
        d=Counter()
        for i,c in terms:d[int(i)]+=int(c)
        common=reduce(gcd,d.values(),divisor)
        if not common:return
        # An integral equality may be divided by the coefficient gcd, even if it is even.
        if divisor:
            m=gcd(mod,divisor//common)
            if m==1:return
            factor=mod//m
        else:factor=1
        row=tuple(sorted((i,(v//common*factor)%mod) for i,v in d.items() if (v//common*factor)%mod))
        if row:rows.add(row)
    _,_,live=setup();idx=np.cumsum(live)-1;n=int(live.sum())
    A=sp.load_npz(tmp/'outer3-14-integral.npz')[:,live].tocsr();A=A[np.diff(A.indptr)>0]
    h=np.gcd.reduceat(abs(A.data),A.indptr[:-1]);A.data//=np.repeat(h,np.diff(A.indptr))
    A.data[A.indices==0]*=99
    rec,graphs=pickle.load(open(tmp/('hom-14-%d.pickle'%axes),'rb'));pop=np.load(tmp/'outer3-14-sizes.npy')
    rr=Reduce(14)
    for j,g in enumerate(graphs[1:],1):
        key=certificate(nauty(g));rr.coreid[key]=j;rr.cores[key]=g
    def hcol(j):return n-1+j if j else 0
    for i,(den,c) in rec.items():
        q,r=divmod(den,99*int(pop[i]));assert r==0
        v=[(hcol(j),-val) for j,val in c.items()]
        if live[i]:v.append((int(idx[i]),q*(99 if i==0 else 1)))
        add(v)
    print('root-hom rows',len(rows),flush=True)
    j=1
    while j<len(graphs):
        g=graphs[j];one=tuple(range(len(g)));fix={one:((j,1),)}
        for H in (two_subgroups(g,mod) if prime is None else []):
            for s in H:
                if s not in fix:fix[s]=rr.reduce(fixed(g,s))
            add(((hcol(i),v) for s in H for i,v in fix[s]),len(H))
        if len(graphs)<len(rr.cores):graphs.extend(list(rr.cores.values())[len(graphs):])
        j+=1
    base=n+len(graphs)-1
    def small(i):return base+i-1 if i else 0
    print('with domain groups',len(rows),flush=True)
    gs,levels,aut,cores,scale,inj,ind=pickle.load(open('moments-order9.pickle','rb'))
    ids={certificate(nauty(g)):j for j,g in enumerate(gs) if g}
    @lru_cache(maxsize=100000)
    def lookup(g):return ids.get(certificate(nauty(g)),-1)
    for j,g in enumerate(graphs):
        if not g or len(g)>9:continue
        cnt=Counter(lookup(x) for x in kernel_partitions(g))
        cnt.pop(-1,None)
        coeff=sum((v*inj[q] for q,v in cnt.items()),start=np.zeros(inj.shape[1],dtype=object))
        add([(hcol(j),-1)]+[(small(i),c) for i,c in enumerate(coeff) if c])
    for q,g in enumerate(gs):
        add(((small(i),c) for i,c in enumerate(inj[q]) if c),int(aut[q]))
        if len(g)==9 and sum(x.bit_count() for x in g)==34:
            add((small(i),c) for i,c in enumerate(ind[q]) if c)
    # All catalogue counts are integral and satisfy every original SRG extension identity.
    from subgraph_counts import build
    for eq in exact_conditions(build(9),99,14,scale,ind):
        add((small(i),v) for i,v in enumerate(eq) if v)
    M=np.load(tmp/'reroot-9.npz')
    for i,v,den in zip(M['ids'],M['H'],M['den']):
        i=int(i);q,r=divmod(int(den),99*int(pop[i]));assert not r
        terms=[(small(j),-int(c)) for j,c in enumerate(v) if c]
        if live[i]:terms.append((int(idx[i]),q*(99 if i==0 else 1)))
        add(terms)
    x=[];y=[];z=[]
    for i,row in enumerate(sorted(rows)):
        for j,c in row:x.append(i);y.append(j);z.append(c)
    cols=base+len(cores)
    B=sp.csr_matrix((np.array(z,dtype=np.int64),(x,y)),shape=(len(rows),cols))
    A=sp.vstack((sp.hstack((A,sp.csr_matrix((A.shape[0],cols-n),dtype=np.int64))),B),format='csr')
    print('combined',A.shape,A.nnz,flush=True)
    return A


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--bits',type=int,default=3);p.add_argument('--axes',type=int,default=4);a=p.parse_args()
    A=system(a.axes,a.bits);sp.save_npz(tmp/('global-%d-%d.npz'%(a.axes,a.bits)),A)
    point=solve(A,a.bits,True);print('verified solution exists',point is not None,flush=True)
    if point is not None:np.save(tmp/('global-%d-%d-witness.npy'%(a.axes,a.bits)),point)
