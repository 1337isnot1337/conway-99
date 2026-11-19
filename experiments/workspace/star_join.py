"""Join the two halves of a six-neighbor star by their exact incidence sums."""
from collections import defaultdict
from itertools import product,combinations
import numpy as np
from broken_grid import canonical_cases,extensions


def stars(A,S,p):
    R=(12*np.eye(len(A),dtype=int)+2-A-A@A)[p];K=np.flatnonzero(A[p])
    free=[v for v in K if not sum(A[v,K])]
    assert len(free) in (4,6)
    D=[s for s in S if p in s and all(R[j]>0 for j in s)]
    mask=[sum(1<<j for j in s) for s in D];key=[sum(1<<(3*j) for j in s) for s in D]
    target=sum(int(k)<<(3*j) for j,k in enumerate(R))
    pools=[[i for i,s in enumerate(D) if v in s] for v in free]
    if len(free)==4:
        extras=[i for i,s in enumerate(D) if not set(s).intersection(free)]
        pools.extend([extras,extras])
    pools=sorted(enumerate(pools),key=lambda x:len(x[1]))
    P=pools[::2];Q=pools[1::2]
    def halves(groups):
        for triple in product(*(g for _,g in groups)):
            a,b,c=triple
            if all((mask[i]&mask[j]).bit_count()<=2 for i,j in ((a,b),(a,c),(b,c))):
                yield key[a]+key[b]+key[c],triple
    lookup=defaultdict(list)
    for k,z in halves(P):lookup[k].append(z)
    for k,z in halves(Q):
        for w in lookup.get(target-k,()):
            if len(free)==4:
                canon={j:i for (j,_),i in zip(P+Q,w+z)}
                if canon[4]>=canon[5]:continue
            if all((mask[i]&mask[j]).bit_count()<=2 for i in z for j in w):
                yield tuple(mask[i] for i in w+z)


if __name__=='__main__':
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument('--case',type=int,default=0);args=ap.parse_args()
    i=args.case;pe,c,A=list(canonical_cases())[i];S,_,_=extensions(A)
    for p in np.array(pe)+8:
        results=np.array(list(stars(A,S,p)),dtype=np.uint32).reshape(-1,6)
        print(i,p,'exact star choices',len(results),flush=True)
        np.save('/tmp/conway99-tools/grid-star-%d-%d.npy'%(i,p),results)
