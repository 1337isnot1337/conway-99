"""Compare independent homomorphism reductions of local patterns in a putative SRG."""
from collections import Counter
from functools import reduce
from math import gcd
import argparse,pickle
import numpy as np
from pynauty import certificate
from itertools import combinations
from hom_moments import Reduce,bits,merge,link,delete,identify,nauty,shape,pattern,partitions,tmp,Triples


def reductions(g,k):
    for i,r in enumerate(g):
        neighbors=list(bits(r))
        if len(neighbors)>2:continue
        h=delete(g,i)
        if len(neighbors)<2:yield ((h,k if neighbors else 1+k*k//2),);continue
        a,b=[v-(v>i) for v in neighbors]
        yield ((h,2),(link(h,a,b),-1),(merge(h,a,b),k-2))
    for a,b in combinations(range(len(g)),2):
        common=list(bits(g[a]&g[b]))
        if g[a]>>b&1:
            for c,d in combinations(common,2):yield ((merge(g,c,d),1),)
        else:
            for c,d,e in combinations(common,3):
                sig=[([(a,b)],1)]
                for pair in ((c,d),(c,e),(d,e)):sig.extend([([pair],1),([(a,b),pair],-1)])
                sig.extend([([(c,d,e)],-2),([(a,b),(c,d,e)],2)])
                yield tuple((identify(g,parts),coef) for parts,coef in sig)


def data(k,maxaxes):
    rng=np.random.default_rng(712)
    t=Triples(k);rr=Reduce(k);forms=set();seen=set()
    nn=0
    for r in t.reps:
        labels,edges,s=shape(t.model,r)
        if s>maxaxes:continue
        # Include every uncontracted cubic pattern, and single-axis coincidences.
        for codes,_ in partitions(s):
            if len({c//2 for c in codes})<s-1:continue
            g=pattern(labels,edges,codes);key=certificate(nauty(g))
            if key in seen:continue
            seen.add(key);primary=rr.reduce(g)
            for terms in reductions(g,k):
                nn+=1
                d=Counter(dict(primary))
                for sub,z in terms:
                    for j,w in rr.reduce(sub):d[j]-=w*z
                ds=tuple((j,w) for j,w in sorted(d.items()) if w)
                if ds:
                    div=reduce(gcd,(v for _,v in ds))
                    if ds[0][1]<0:div=-div
                    forms.add(tuple((j,v//div) for j,v in ds))
        if len(seen)%2000==0:pass
    print('axis limit',maxaxes,'pattern graphs',len(seen),'distinct reductions tried',nn,'different nonzero identities',len(forms),'cores',len(rr.cores),flush=True)
    with (tmp/('ambiguities-%d-%d.pickle'%(k,maxaxes))).open('wb') as f:pickle.dump((list(rr.cores.values()),list(forms)),f)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--degree',type=int,default=14);p.add_argument('--axes',type=int,default=3);a=p.parse_args();data(a.degree,a.axes)
