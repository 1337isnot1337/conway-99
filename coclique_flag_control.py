"""Check every aggregated incidence identity against all triples of a known graph."""
import argparse
from itertools import combinations,permutations
from collections import Counter
import numpy as np
from coclique_flags import build
from triangle_ball import golay


def check(G,I):
    h=len(I);k=int(G[0].sum());outside=sorted(set(range(len(G)))-set(I))
    C=G[np.ix_(I,outside)];H=G[np.ix_(outside,outside)];d=C.sum(axis=0)
    assert np.all(d>0) and not np.any(G[np.ix_(I,I)])
    A,b,s,p,t=build(h,False,k);x=np.zeros(A.shape[1],np.int64)
    for j in d:x[s[j]]+=1
    common=C.T@C;l=2*common+H
    for i,j in combinations(range(len(outside)),2):
        x[p[min(d[i],d[j]),max(d[i],d[j]),common[i,j],H[i,j]]]+=1+int(d[i]==d[j])
    masks=[sum(1<<int(i) for i in np.flatnonzero(c)) for c in C.T]
    perms=list(permutations(range(3)))
    # Count each raw representative in bulk before normalizing its six permutations.
    raw=Counter()
    for i,j in combinations(range(len(outside)),2):
        if j+1==len(outside):continue
        h1=masks[i]&masks[j];q=np.arange(j+1,len(outside))
        w=np.fromiter(((h1&masks[z]).bit_count() for z in q),np.int16)
        v=(((d[q]*6+l[i,q])*6+l[j,q])*2+w)
        uq,freq=np.unique(v,return_counts=True)
        for z,f in zip(uq,freq):
            z,w=divmod(int(z),2);z,bc=divmod(z,6);g,ac=divmod(z,6)
            raw[int(d[i]),int(d[j]),g,int(l[i,j]),ac,bc,w]+=int(f)
    for (a,b1,c,ab,ac,bc,w),count in raw.items():
        ds=[a,b1,c];link=((0,ab,ac),(ab,0,bc),(ac,bc,0))
        keys=[(ds[i],ds[j],ds[k],link[i][j],link[i][k],link[j][k],w) for i,j,k in perms]
        key=min(keys);x[t[key]]+=keys.count(key)*count
    y=A@x-b
    assert not np.any(y),[(int(j),int(y[j])) for j in np.flatnonzero(y)[:12]]
    print('known graph',len(G),'maximal coclique',h,'verified equations',len(y),'nonzero coordinates',np.count_nonzero(x),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--golay',action='store_true');a=p.parse_args()
    if a.golay:
        G,_,_=golay();I=[]
        for i in range(len(G)):
            if not any(G[i,j] for j in I):I.append(i)
    else:
        G=np.array([[int(i!=j and (i//3==j//3 or i%3==j%3)) for j in range(9)] for i in range(9)],np.int16);I=[0,4,8]
    check(G,I)
