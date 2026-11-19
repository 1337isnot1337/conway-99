"""Unrestricted incidence trades preserving the pair parameters of a coclique design."""
from collections import defaultdict,Counter
from itertools import combinations
import numpy as np
from triple_moments import tmp


def trades(blocks):
    sums=defaultdict(list);seen=set()
    for i,j in combinations(range(len(blocks)),2):
        v=blocks[i]^blocks[j]
        for a,b in sums[v]:
            ids=tuple(sorted((i,j,a,b)))
            if ids in seen:continue
            seen.add(ids);old=[blocks[k] for k in ids]
            fixed=old[0]&old[1]&old[2]&old[3];all_=old[0]|old[1]|old[2]|old[3]
            new=[fixed|(all_^x) for x in old]
            if set(new)==set(old):continue
            if any((m&x).bit_count()>2 for k,x in enumerate(blocks) if k not in ids for m in new):continue
            yield ids,new
        sums[v].append((i,j))


def developed(base):
    def shift(x,s):return sum(1<<(i//11*11+(i+s)%11) for i in range(22) if x>>i&1)
    return [shift(x,s) for x in base for s in range(11)]


def C_matrix(blocks):
    C=np.array([[(b>>i)&1 for b in blocks] for i in range(22)],np.int16)
    assert np.all(C.sum(0)==4) and np.all(C@C.T==12*np.eye(22,dtype=int)+2)
    assert np.max(np.triu(C.T@C,1))<=2
    return C


if __name__=='__main__':
    from coclique_finish import finish
    rng=np.random.default_rng(314)
    data=np.loadtxt(tmp/'coclique-families.txt',dtype=np.int32);cnt=Counter()
    for j in range(35):
        b=developed(data[rng.integers(len(data))].tolist())
        for s in range(4):
            choices=list(trades(b));cnt[len(choices)]+=1
            if not choices:break
            idx,new=choices[rng.integers(len(choices))]
            for i,v in zip(idx,new):b[i]=v
            C=C_matrix(b);G=finish(C,14,1,'traded')
            if G is not None:
                np.save('verified-conway-99.npy',G);raise SystemExit
    print('trade availability',cnt)
