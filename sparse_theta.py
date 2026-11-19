"""Count distinct short projected integral vectors using induced types through five vertices."""
from collections import Counter
from itertools import product
from math import comb
from core_counts import reduce_counts
from subgraph_counts import build

def lower(max_entry=3,cutoff=18):
    data=build(5);graphs,levels,*_=data
    cores,fac,inj,ind=reduce_counts(data,99,14)
    assert not cores
    result=Counter()
    for n in range(1,6):
        assigns=[]
        for v in product([i for i in range(-max_entry,max_entry+1) if i],repeat=n):
            m=sum(v);a=sum(i>0 for i in v);b=n-a
            if m==0 and max(a,b)<=2 or m==3 and a<=4 and b<=1:
                assigns.append((v,m))
        total=0
        for index in levels[n]:
            rows=graphs[index]; edges=[(i,j) for i in range(n) for j in range(i) if rows[i]>>j&1]
            num,rem=divmod(ind[index,0],fac);assert not rem;total+=num
            for v,m in assigns:
                q=3*sum(i*i for i in v)+m*m//9-2*sum(v[i]*v[j] for i,j in edges)
                assert q>0 and q%2==0
                if q<=2*cutoff:result[q//2]+=int(num)*(1+(m!=0))
        assert total==comb(99,n)
    return dict(sorted(result.items()))
if __name__=='__main__':print(lower())
