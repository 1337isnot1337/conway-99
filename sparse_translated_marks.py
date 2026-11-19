"""Translated one- and two-coordinate distributions of distinct sparse projected vectors."""
from collections import defaultdict
from fractions import Fraction as F
from functools import cache
from itertools import product,permutations
from pathlib import Path
import json,numpy as np
from core_counts import reduce_counts
from subgraph_counts import build

@cache
def lifts(n):
    B=np.array(list(product((-2,-1,0,1,2),repeat=n)),dtype=np.int64)
    m=B.sum(axis=1);nn=(B!=0).sum(axis=1)
    return B[(m>=0)&(m<=11)&(nn>0)&(nn>=n-2)&(nn<=5)]

def make(cap):
    data=build(6);graphs,levels,*_=data;cores,fac,_,ind=reduce_counts(data,99,14);assert len(cores)==1
    buckets=[defaultdict(lambda:[0,0]) for _ in range(3)]
    def record(tab,code,weights):
        for key,mult in zip(*np.unique(code,return_counts=True)):
            v=tab[int(key)]
            for k in (0,1):v[k]+=int(weights[k])*int(mult)
    for n in range(1,7):
        B0=lifts(n)
        for ix in levels[n]:
            G=np.array([[(r>>i)&1 for i in range(n)] for r in graphs[ix]],dtype=int)
            a0=3*B0-B0@G;m0=B0.sum(axis=1)
            d0=(9*(B0*a0).sum(axis=1)+m0*m0)//2
            ok=d0<=cap;B=B0[ok];m=m0[ok];d=d0[ok];t=(9*a0[ok]+m[:,None])
            t=t*np.where(m%9<=4,1,-1)[:,None];nn=(B!=0).sum(axis=1)
            assert np.all(abs(t)<128)
            md=512*m+d
            record(buckets[0],md[nn==n],ind[ix])
            for i in range(n):
                match=(nn==n-(B[:,i]==0).astype(int))
                record(buckets[1],(md*256+t[:,i]+128)[match],ind[ix])
            for i,j in permutations(range(n),2):
                match=(nn<=4)&(nn==n-(B[:,i]==0).astype(int)-(B[:,j]==0).astype(int))
                code=((md*2+G[i,j])*256+t[:,i]+128)*256+t[:,j]+128
                record(buckets[2],code[match],ind[ix])
    doc=[[],[],[]];P={};counts={}
    for k,table in enumerate(buckets):
        for key,vs in sorted(table.items()):
            args=[]
            if k==2:
                key,u=divmod(key,256);key,t=divmod(key,256);key,e=divmod(key,2);args=[e,t-128,u-128]
            elif k==1:key,t=divmod(key,256);args=[t-128]
            m,d=divmod(key,512);v=[F(x,fac) for x in vs]
            doc[k].append([m,d,*args,*map(str,v)])
            if k==0:counts[m,d]=v
            if k==1:
                target=P.setdefault((m,d),[0,0,0,0])
                for i in (0,1):target[i]+=v[i];target[i+2]+=args[0]**2*v[i]
    for key,v in counts.items():
        assert P[key]==[99*x for x in v]+[126*key[1]*x for x in v]
    Path('sparse-translated-marks.json').write_text(json.dumps(doc)+'\n')
    print('shell, point, ordered pair rows',list(map(len,doc)),flush=True)
if __name__=='__main__':make(180)
