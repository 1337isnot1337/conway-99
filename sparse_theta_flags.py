"""Exact coordinate histograms of the guaranteed lattice vectors from supports of size at most five."""
from collections import defaultdict
from itertools import product
from functools import cache
import json
from pathlib import Path
import numpy as np
from core_counts import reduce_counts
from subgraph_counts import build

@cache
def assignments(n):
    vec=[]
    for b in product((-3,-2,-1,1,2,3),repeat=n):
        m=sum(b);pos=sum(i>0 for i in b);neg=n-pos
        if m==0 and max(pos,neg)<=2 or m==3 and pos<=4 and neg<=1:vec.append(b)
    return np.array(vec,dtype=int)

def make():
    data=build(6);graphs,levels,*_=data
    cores,fac,inj,ind=reduce_counts(data,99,14);assert len(cores)==1
    prism=graphs[cores[0]]
    assert len(prism)==6 and all(i.bit_count()==3 for i in prism) and sum((prism[i]&prism[j]).bit_count() for i in range(6) for j in range(i) if prism[i]>>j&1)==6
    H=defaultdict(lambda:np.zeros(2,dtype=object))
    for n in range(1,7):
        for ix in levels[n]:
            G=np.array([[(r>>i)&1 for i in range(n)] for r in graphs[ix]],dtype=int)
            for pos in range(n+1):
                if pos<n and n==1 or pos==n and n==6:continue
                if pos==n:B=assignments(n)
                else:B=np.insert(assignments(n-1),pos,0,axis=1)
                a=3*B-B@G;m=B.sum(axis=1)
                q=(B*a).sum(axis=1)+m*m//9
                assert not np.any(q%2)
                sites=range(n) if pos==n else [pos]
                for j in sites:
                    t=abs(3*a[:,j]+m//3);codes=(q//2)*128+t
                    for zz,v in enumerate(np.bincount(codes,weights=1+(m!=0))):
                        if v and zz//128<=18:H[divmod(zz,128)]+=int(v)*ind[ix]
    result=[]
    for (i,t),vals in sorted(H.items()):
        assert not any(v%fac for v in vals)
        result.append([i,t,*[int(v//fac) for v in vals]])
    from sparse_theta import lower
    floor=lower()
    for i,f in floor.items():
        entries=[v for v in result if v[0]==i]
        assert sum(a for _,t,a,b in entries)==99*f and sum(b for _,t,a,b in entries)==0
        assert sum(t*t*a for _,t,a,b in entries)==126*i*f and sum(t*t*b for _,t,a,b in entries)==0
    Path('sparse-theta-flags.json').write_text(json.dumps(result)+'\n')
    print(len(result),'shell-coordinate counts verified')
if __name__=='__main__':make()
