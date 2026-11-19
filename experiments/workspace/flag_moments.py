"""Finite rooted moment blocks for (99,14,1,2), integer coefficients in core counts."""
from collections import Counter
from functools import lru_cache
from itertools import combinations,permutations,product
import argparse
import pickle
from pathlib import Path

import numpy as np
import scipy.sparse as sp
from pynauty import certificate
from core_counts import reduce_counts
from subgraph_counts import build,extensions,members,nauty

BASE=Path(__file__).parent


def cache9():
    cache=BASE/'moments-order9.pickle'
    if cache.exists():
        with cache.open('rb') as f:
            return pickle.load(f)
    data=build(9)
    cores,scale,inj,induced=reduce_counts(data,99,14)
    pack=data[0],data[1],data[2],cores,scale,inj,induced
    with cache.open('wb') as f:pickle.dump(pack,f)
    return pack


def attached(root,extra):
    rows=list(root)+[0]*len(extra)
    for i,mask in enumerate(extra,len(root)):
        rows[i]=mask
        for j in members(mask):rows[j] |= 1 << i
    return tuple(rows)


def flags(root,size):
    layer=[root]
    out=[root]
    r=len(root)
    for s in range(1,size+1):
        layer=[h for g in layer for _,h in extensions(g)]
        # Variables count labelled extensions; permuting free labels gives
        # literally the same variable. Keep one labeled pattern per orbit.
        seen=set()
        for g in layer:
            if any(x.bit_count()<3 for x in g[r:]): continue
            if g in seen:continue
            out.append(g)
            for p in permutations(range(r,len(g))):
                perm=tuple(range(r))+p
                seen.add(tuple(sum(1<<j for j,b in enumerate(perm) if g[a]>>b&1) for a in perm))
    return out


@lru_cache(None)
def overlap_maps(r,s,t):
    choices=[]
    for q in range(min(s,t)+1):
        for overlap in combinations(range(t),q):
            for images in permutations(range(r,r+s),q):
                table=dict(zip(overlap,images))
                fresh=iter(range(r+s,r+s+t-q))
                choices.append(tuple(range(r))+tuple(table[i] if i in table else next(fresh) for i in range(t)))
    return choices


def make_blocks(pack,r,s,limit,induced_root=False):
    graphs,levels,aut,cores,scale,inj,induced=pack
    ids={(len(g),certificate(nauty(g))):i for i,g in enumerate(graphs) if g}
    @lru_cache(maxsize=150000)
    def ident(g):
        # Saturated forbidden pairs have zero injective copies.
        for a,ra in enumerate(g):
            for b in range(a):
                if (ra&g[b]).bit_count()>2-((ra>>b)&1):return -1
        return ids[len(g),certificate(nauty(g))]
    blocks=[]
    for h in levels[r]:
        fs=flags(graphs[h],s)
        if len(fs)<=1 or len(fs)>limit:continue
        ii,jj,vv=[],[],[]
        tags=[[(i,j) for i in range(r,len(g)) for j in members(g[i]&((1<<i)-1))] for g in fs]
        for i,left in enumerate(fs):
            for j,right in enumerate(fs[:i+1]):
                acc=Counter()
                for mapping in overlap_maps(r,len(left)-r,len(right)-r):
                    n=max(len(left),max(mapping)+1)
                    rows=list(left)+[0]*(n-len(left))
                    for a,b in tags[j]:
                        u,v=mapping[a],mapping[b]
                        rows[u]|=1<<v
                        rows[v]|=1<<u
                    if not induced_root:
                        pos=ident(tuple(rows))
                        if pos>=0:acc[pos]+=1
                        continue
                    # Both sides prescribe their own induced graph. After
                    # checking their common vertices, only cross edges between
                    # the two nonoverlapping sets of free vertices are unknown.
                    shared=[i for i,y in enumerate(mapping) if y<len(left)]
                    if any(((left[mapping[u]]>>mapping[v])&1)!=((right[u]>>v)&1)
                           for u,v in combinations(shared,2) if v>=r):
                        continue
                    new_left=set(range(r,len(left)))-set(mapping)
                    new_right=set(mapping)-set(range(len(left)))
                    free=list(product(new_left,new_right))
                    base=tuple(rows)
                    if ident(base)<0:continue
                    def complete(t,current):
                        if t==len(free):
                            acc[ident(current)]+=1
                            return
                        complete(t+1,current)
                        a,b=free[t]
                        changed=list(current)
                        changed[a]|=1<<b
                        changed[b]|=1<<a
                        changed=tuple(changed)
                        if ident(changed)>=0:
                            complete(t+1,changed)
                    complete(0,base)
                for pos,count in acc.items():
                    ii.append(i*(i+1)//2+j)
                    jj.append(pos)
                    vv.append(count)
        lookup=sp.csr_matrix((vv,(ii,jj)),shape=(len(fs)*(len(fs)+1)//2,len(graphs)),dtype=np.int64)
        blocks.append((h,fs,lookup))
    return blocks


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('r',type=int)
    p.add_argument('s',type=int)
    p.add_argument('--limit',type=int,default=512)
    p.add_argument('--induced',action='store_true')
    a=p.parse_args()
    assert a.r+2*a.s<=9
    pack=cache9()
    blocks=make_blocks(pack,a.r,a.s,a.limit,a.induced)
    dest=BASE/('moments-%d-%d-%d.pickle'%(a.r,a.s,a.limit))
    if a.induced:dest=dest.with_name('induced-'+dest.name)
    with dest.open('wb') as f:pickle.dump(blocks,f)
    print(dest.name, 'blocks',len(blocks),'entries',sum(u.shape[0] for _,_,u in blocks),'nonzeros',sum(u.nnz for _,_,u in blocks),flush=True)


if __name__=='__main__':main()
