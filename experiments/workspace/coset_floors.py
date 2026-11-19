"""Lower bounds in each of the first five translates, counting short sparse lifts."""
from itertools import product
from collections import Counter
import numpy as np
from core_counts import reduce_counts
from subgraph_counts import build

def counts(cut=270):
    data=build(5);graphs,levels,*_=data;cores,fac,_,ind=reduce_counts(data,99,14);assert not cores
    counts=Counter()
    for n in range(1,6):
        V=[]
        for b in product((-3,-2,-1,1,2,3),repeat=n):
            m=sum(b);p=sum(x>0 for x in b);q=n-p
            if (m==0 and max(p,q)<=2 or m in (1,2) and p<=3 and q<=2 or m in (3,4) and p<=4 and q<=1):V.append(b)
        V=np.array(V);m=V.sum(axis=1)
        for ix in levels[n]:
            G=np.array([[(r>>i)&1 for i in range(n)] for r in graphs[ix]])
            d=(9*((3*V-V@G)*V).sum(axis=1)+m*m)//2
            for code,freq in zip(*np.unique(m*1024+d,return_counts=True)):
                j,i=divmod(int(code),1024)
                assert i%9==5*j*j%9
                if i<=cut:counts[j,i]+=int(ind[ix,0]//fac)*int(freq)
    return counts
if __name__=='__main__':print(sorted(counts(80).items()))
