"""Eliminate all affine-offset parity equations for a three-character connection."""
from itertools import combinations,product
from collections import defaultdict
import numpy as np
from root_grid_cover import Cover


def reduce_system(C,Q,domains):
    offsets={};b=1
    for h,dom in enumerate(domains):
        for j in range(len(dom)):offsets[h,j]=1<<b;b+=1
    def phase(i,j,c):
        if i>j:return phase(j,i,int(Q[i,j,c]))
        return (1,2,3)[c]<<(2*C.idx[i,j])
    def axis(h,p,c):
        return sum(offsets[h,k] for k,q in enumerate(domains[h]) if q[p]==c)
    rows=[]
    for i,j in combinations(range(21),2):
        common=[k for k in range(21) if tuple(sorted((i,k))) in C.idx and tuple(sorted((j,k))) in C.idx]
        adjacent=(i,j) in C.idx
        for c in range(3):
            for d in range(3):
                paths=[k for k in common if Q[k,j,Q[i,k,c]]==d]
                a=0;r=0
                for k in paths:
                    a^=phase(i,k,c)^phase(k,j,int(Q[i,k,c]))
                if adjacent:
                    if int(Q[i,j,c])!=d:
                        assert len(paths)%2==0
                        rows.append((int(a),(len(paths)//2)%2))
                        continue
                    assert len(paths) in (1,3)
                    r=((len(paths)+1)//2)%2
                    a^=phase(i,j,c)
                    # Each product-char indicator is one plus the two coordinate indicators in F2.
                    for h in C.cells[i]:r^=axis(h,i,c)
                    for h in C.cells[j]:r^=axis(h,j,d)
                else:
                    h,=set(C.cells[i])&set(C.cells[j])
                    assert len(paths)%2==0
                    r=(len(paths)//2)%2
                    for z,q in enumerate(domains[h]):
                        if (q[i],q[j])==(c,d):r^=offsets[h,z]
                rows.append((int(a),int(r)))
    basis={};checks={}
    for a,r in rows:
        while a:
            j=a.bit_length()-1
            if j not in basis:basis[j]=(a,r);break
            aa,rr=basis[j];a^=aa;r^=rr
        if not a:
            while r:
                j=r.bit_length()-1
                if j not in checks:checks[j]=r;break
                r^=checks[j]
    syn=lambda x:sum(((x&r).bit_count()%2)<<j for j,r in enumerate(checks.values()))
    sig=[[syn(offsets[h,k]) for k in range(len(domains[h]))] for h in range(7)]
    return sig,syn(1),len(basis),len(checks)


def find(D,S,t):
    def side(ids):
        for v in product(*(range(len(D[h])) for h in ids)):
            mask=0;x=0
            for h,k in zip(ids,v):
                y=sum(1<<(3*i+c) for i,c in D[h][k].items())
                if y&mask:break
                mask|=y;x^=S[h][k]
            else:yield x,mask,v
    bins=defaultdict(list)
    for x,m,v in side(range(3)):bins[x].append((m,v))
    for x,m,v in side(range(3,7)):
        for n,w in bins.get(t^x,[]):
            if not n&m:yield w+v


if __name__=='__main__':
    C=Cover();P=C.connection();D=C.roots(P)
    S,t,r,s=reduce_system(C,(P[:,:,None]+np.arange(3))%3,D)
    print('unknown offset bits',210,'coefficient rank',r,'independent assignment checks',s,flush=True)
    num=0;passed=0
    for v in find(D,S,t):
        num+=1
        a=[D[h][v[h]] for h in range(7)]
        anti=[3-sum(a[h][i] for h in edge) for i,edge in enumerate(C.cells)]
        if C.face_problem(P,anti) is not None:passed+=1
    print('root labelings satisfying all outer parity constraints',num,'with triangle voltages',passed,flush=True)
