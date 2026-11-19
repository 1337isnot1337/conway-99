"""Eliminate labels globally via signed axis partitions and the SRG homomorphism identities."""
from collections import Counter,defaultdict
from functools import lru_cache
from itertools import combinations
from math import factorial,perm
from pathlib import Path
import argparse,pickle
import numpy as np
from pynauty import certificate
from subgraph_counts import nauty
from triple_moments import Triples,tmp


@lru_cache(None)
def partitions(s):
    # Each entry is twice the block number plus its orientation relative to the first axis in the block.
    if s==0:return (((),1),)
    result=[]
    for codes,_ in partitions(s-1):
        n=1+max((i//2 for i in codes),default=-1)
        for v in range(2*n+1):
            p=codes+(v,);sizes=Counter(z//2 for z in p)
            coefficient=(-1)**(s-len(sizes))
            for size in sizes.values():coefficient*=factorial(size-1)
            result.append((p,coefficient))
    return tuple(result)


def bits(x):
    while x:
        z=x&-x;yield z.bit_length()-1;x^=z

def delete(g,i):
    lo=(1<<i)-1
    return tuple((r&lo)|((r>>(i+1))<<i) for j,r in enumerate(g) if i!=j)

def link(g,a,b):
    r=list(g);r[a]|=1<<b;r[b]|=1<<a;return tuple(r)

def merge(g,a,b):
    if g[a]&(1<<b):return None
    r=list(g)
    for i in bits(g[b]):
        r[i]|=1<<a;r[a]|=1<<i
    return delete(r,b)

def identify(g,classes):
    p=list(range(len(g)))
    for group in classes:
        for i in group:p[i]=group[0]
    vals={v:j for j,v in enumerate(sorted(set(p)))}
    image=[vals[x] for x in p];out=[0]*len(vals)
    for i,r in enumerate(g):
        for j in bits(r):
            a,b=image[i],image[j]
            if a==b:return None
            out[a]|=1<<b
    return tuple(out)


class Reduce:
    def __init__(self,k):
        self.k=k;self.v=1+k*k//2;self.cores={b'':()};self.coreid={b'':0};self.cache={}
    def reduce(self,g):
        if g is None:return ()
        if not g:return ((0,1),)
        key=certificate(nauty(g))
        if key in self.cache:return self.cache[key]
        deg=[r.bit_count() for r in g];i=min(range(len(g)),key=deg.__getitem__)
        if deg[i]>=3:
            repeated=None
            for a,b in combinations(range(len(g)),2):
                common=g[a]&g[b]
                if (g[a]>>b)&1 and common.bit_count()>=2:
                    c,d,*_=bits(common)
                    result=self.reduce(merge(g,c,d))
                    self.cache[key]=result
                    return result
                if common.bit_count()>=3 and repeated is None:
                    c,d,e,*_=bits(common);repeated=(a,b,c,d,e)
            if repeated is not None:
                a,b,c,d,e=repeated;terms=Counter()
                sig=[([(a,b)],1)]
                for pair in ((c,d),(c,e),(d,e)):
                    sig.extend([([pair],1),([(a,b),pair],-1)])
                sig.extend([([(c,d,e)],-2),([(a,b),(c,d,e)],2)])
                for parts,coef in sig:
                    for x,y in self.reduce(identify(g,parts)):terms[x]+=coef*y
                result=tuple((j,n) for j,n in sorted(terms.items()) if n)
            else:
                if key not in self.coreid:self.coreid[key]=len(self.cores);self.cores[key]=g
                result=((self.coreid[key],1),)
        else:
            h=delete(g,i)
            if deg[i]<2:
                coef=self.v if not deg[i] else self.k
                result=tuple((j,coef*n) for j,n in self.reduce(h))
            else:
                a,b=[u-(u>i) for u in bits(g[i])]
                d=Counter()
                # Sum over the removed vertex via A^2 = (k-2)I - A + 2J.
                for f,c in ((merge(h,a,b),self.k-2),(link(h,a,b),-1),(h,2)):
                    for j,n in self.reduce(f):d[j]+=c*n
                result=tuple((j,n) for j,n in sorted(d.items()) if n)
        self.cache[key]=result
        return result

def shape(m,rep):
    selected=sorted(set(int(x) for x in rep if x))
    outer=sorted({y for x in selected for y in m.pairs[x]})
    labels=[m.labels[i] for i in outer]
    axes=sorted({a//2 for pair in labels for a in pair})
    first={v:next(a%2 for pair in labels for a in pair if a//2==v) for v in axes}
    labels=[tuple(2*axes.index(a//2)+(a%2^first[a//2]) for a in pair) for pair in labels]
    edges=[tuple(outer.index(i) for i in m.pairs[x]) for x in selected]
    return labels,edges,len(axes)

def pattern(labels,edges,codes):
    images=[tuple(codes[a//2]^(a%2) for a in pair) for pair in labels]
    near=sorted({v for pair in images for v in pair})
    idx={a:i+1 for i,a in enumerate(near)};start=1+len(near)
    g=[0]*(start+len(images))
    def add(i,j):g[i]|=1<<j;g[j]|=1<<i
    for a,i in idx.items():
        add(0,i)
        if not a%2 and a+1 in idx:add(i,idx[a+1])
    for f,pair in enumerate(images):
        for v in pair:add(start+f,idx[v])
    for i,j in edges:add(start+i,start+j)
    return tuple(g)

def run(k,limit):
    t=Triples(k);rr=Reduce(k)
    records={}
    for j,rep in enumerate(t.reps):
        labels,edges,s=shape(t.model,rep)
        if s>limit:continue
        d=Counter()
        for codes,mob in partitions(s):
            for c,v in rr.reduce(pattern(labels,edges,codes)):d[c]+=mob*v
        records[j]=(rr.v*2**s*perm(k//2,s),{c:v for c,v in d.items() if v})
    print('axes',limit,'moments',len(records),'canonical reductions',len(rr.cache),'cores',Counter(map(len,rr.cores.values())),flush=True)
    with (tmp/('hom-%d-%d.pickle'%(k,limit))).open('wb') as f:pickle.dump((records,list(rr.cores.values())),f)
    if k==4:
        rook=np.array([[int(i!=j and (i//3==j//3 or i%3==j%3)) for j in range(9)] for i in range(9)])
        def hom(g):
            def rec(im):
                i=len(im)
                if i==len(g):return 1
                return sum(rec(im+(v,)) for v in range(9) if all(rook[im[q],v] for q in bits(g[i]) if q<i))
            return rec(())
        h=[hom(g) for g in rr.cores.values()];x=np.load(tmp/'outer3-4-point.npy')
        for j,(a,b) in records.items():assert round(x[j]*a)==sum(h[q]*v for q,v in b.items())
        print('all rook homomorphism expansions independently verified',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--degree',type=int,default=14);p.add_argument('--axes',type=int,default=3)
    args=p.parse_args();run(args.degree,args.axes)
