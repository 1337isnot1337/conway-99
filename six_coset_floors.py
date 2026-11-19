"""Six-site lower bounds in every translated lattice; only opposite-sign prisms permit a collision."""
from collections import defaultdict
from fractions import Fraction as F
from itertools import product
from pathlib import Path
from flint import fmpz_mat
import numpy as np,json
from core_counts import reduce_counts
from subgraph_counts import build
def make(limit=270):
    data=build(6);graphs,levels,*_=data;cores,fac,_,ind=reduce_counts(data,99,14);assert len(cores)==1
    ans=defaultdict(lambda:[0,0])
    for n in range(1,7):
        V=np.array([b for b in product((-3,-2,-1,1,2,3),repeat=n) if 0<=sum(b)<=11],dtype=np.int64);m=V.sum(axis=1);same=abs(V).min(axis=1)==abs(V).max(axis=1)
        for ix in levels[n]:
            G=np.array([[(r>>j)&1 for j in range(n)] for r in graphs[ix]],dtype=np.int64)
            if n==6 and ix!=cores[0]:
                Z=3*np.eye(6,dtype=int)-G
                assert all(fmpz_mat(Z[:i,:i].tolist()).det()>0 for i in range(1,7))
            signs=V>0;cross=np.any((signs@G>0)&(~signs),axis=1)
            unsafe=(n==6)&same&(~cross)&(m%2==0)
            if ix!=cores[0]:unsafe&=~np.all(signs,axis=1)
            d=(9*((3*V-V@G)*V).sum(axis=1)+m*m)//2
            good=(d<=limit)
            for bad,mult in ((False,16),(True,1)):
                mask=good&(unsafe==bad)
                for z,f in zip(*np.unique(1024*m[mask]+d[mask],return_counts=True)):
                    key=divmod(int(z),1024);a=ans[key]
                    for i in range(2):a[i]+=int(f)*mult*int(ind[ix,i])
    # Each row expresses a lower bound, for one fixed lift mass, in terms of the prism count.
    D=[[min(m%9,-m%9),d,m,str(F(a,16*fac)),str(F(b,16*fac))] for (m,d),(a,b) in sorted(ans.items())]
    Path('six-coset-floors.json').write_text(json.dumps(D)+'\n')
    print('six-site lower bounds',len(D),flush=True)
if __name__=='__main__':make()
