"""Enumerate the 27-vertex cores forced by an incomplete eight-vertex rook grid."""
from itertools import combinations,permutations
from collections import Counter
import numpy as np
import scipy.sparse as sp
from scipy.optimize import linprog
from pathlib import Path

pairs=list(combinations(range(4),2))
edges=list(combinations(range(6),2))
def initial(pedge):
    B=np.zeros((14,14),dtype=np.int16)
    def e(i,j):B[i,j]=B[j,i]=1
    for i in range(4):
        e(i,(i+1)%4);e(i,4+i);e((i+1)%4,4+i)
    e(4,6);e(5,7)
    for i,(a,b) in enumerate(pairs,8):e(4+a,i);e(4+b,i)
    e(8+pedge[0],8+pedge[1])
    return B


def designs(pedge):
    B=initial(pedge);C=2-B-B@B
    if np.min(C[np.triu_indices(14,1)])<0:return
    cap=[int(C[8+i,8+j]) for i,j in edges]
    deg=np.array([4+int(i in pedge) for i in range(6)])
    # Pairs not taken as neighbors of an X vertex account for only four common-neighbor occurrences.
    target=[sum(cap[l] for l,e in enumerate(edges) if i in e)-deg[i] for i in range(6)]
    def rec(k,left,deletions):
        if k==len(edges):
            if not any(left):
                yield tuple(a-b for a,b in zip(cap,deletions))
            return
        i,j=edges[k]
        for n in range(min(cap[k],left[i],left[j])+1):
            left[i]-=n;left[j]-=n
            if all(left[z]>=0 and left[z]<=sum(cap[l] for l in range(k+1,len(edges)) if z in edges[l]) for z in (i,j)):
                yield from rec(k+1,left,deletions+[n])
            left[i]+=n;left[j]+=n
    for counts in rec(0,list(target),[]):
        cols=[e for e,n in zip(edges,counts) for _ in range(n)]
        assert len(cols)==13
        A=np.zeros((27,27),dtype=np.int16);A[:14,:14]=B
        for i,e in enumerate(cols,14):
            for j in e:A[i,8+j]=A[8+j,i]=1
        if np.max(np.triu(A@A+A,1))<=2:yield counts,A


def canonical_cases():
    perms=[]
    for s in (1,-1):
        for a in range(4):
            g=[(a+s*i)%4 for i in range(4)]
            g2=[pairs.index(tuple(sorted((g[i],g[j])))) for i,j in pairs]
            perms.append(np.array([edges.index(tuple(sorted((g2[i],g2[j])))) for i,j in edges]))
    seen=set()
    for z,pe in enumerate(edges):
        for counts,A in designs(pe):
            key=min((p[z],tuple(np.array(counts)[np.argsort(p)])) for p in perms)
            if key in seen:continue
            seen.add(key);yield pe,counts,A


def single_signatures(A):
    cap=2-A-A@A
    for v in range(8):
        for k in range(4):
            for pp in combinations(range(8,14),k):
                seq=(v,)+pp
                if any(cap[i,j]<=0 for i,j in combinations(seq,2)):continue
                xc=[j for j in range(14,27) if all(cap[i,j]>0 for i in seq)]
                for xx in combinations(xc,k+2-int(v>=4)):
                    if all(cap[i,j]>0 for i,j in combinations(xx,2)):
                        yield seq+xx


def extensions(A):
    n=len(A);cap=12*np.eye(n,dtype=int)+2-A-A@A;S=list(single_signatures(A))
    incidence=np.zeros((len(S),n),dtype=np.int16)
    for i,s in enumerate(S):incidence[i,list(s)]=1
    ok=np.all(incidence@(A+np.eye(n,dtype=np.int16))<=2,axis=1)
    for diag,adj,constant in [(3,-1,1/9),(4,1,-2/11)]:
        G=diag*np.eye(n)+adj*A+constant
        val,U=np.linalg.eigh(G);active=val>1e-7
        q=adj*incidence+constant
        if not np.all(active):
            ok&=np.max(np.abs(q@U[:,~active]),axis=1)<1e-7
        residual=diag+constant-np.sum((q@U[:,active])**2/val[active],axis=1)
        ok&=residual>=-1e-8
    S=[s for s,keep in zip(S,ok) if keep]
    row,col=np.tril_indices(n)
    ix=np.empty((n,n),dtype=int);ix[row,col]=ix[col,row]=np.arange(len(row))
    ii=[];jj=[]
    for j,s in enumerate(S):
        for k,a in enumerate(s):
            ii.extend(ix[a,list(s[:k+1])]);jj.extend([j]*(k+1))
    M=sp.csr_matrix((np.ones(len(ii)),(ii,jj)),shape=(len(row),len(S)))
    E=sp.vstack([M,np.ones((1,len(S)))],format='csr');b=np.r_[cap[row,col],72]
    return S,E,b


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--solve',action='store_true');p.add_argument('--limit',type=int,default=0);a=p.parse_args()
    totals=Counter()
    for i,(pe,c,A) in enumerate(canonical_cases()):
        g=np.linalg.eigvalsh(3*np.eye(27)-A+1/9);h=np.linalg.eigvalsh(4*np.eye(27)+A-2/11)
        if min(g[0],h[0])< -1e-8:totals['spectral violation']+=1;continue
        totals['interlace pass']+=1
        if a.solve and (not a.limit or i<a.limit):
            S,E,b=extensions(A)
            sol=linprog(np.zeros(len(S)),A_eq=E,b_eq=b,bounds=(0,None),method='highs',options={'time_limit':12})
            totals['LP '+str(sol.status)]+=1
            print(i,pe,'signatures',len(S),'LP',sol.status,flush=True)
            if sol.success and not Path('broken-grid-core.npy').exists():np.save('broken-grid-core.npy',A)
    print(totals,flush=True)
