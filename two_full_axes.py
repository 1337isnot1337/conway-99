"""Test locally cyclic matchings of the fifty-nine vertex core of two full axes."""
import argparse
from itertools import combinations,product,permutations
from collections import Counter,defaultdict
import numpy as np
from triple_moments import tmp

perm=list(permutations(range(4)))
bits=np.array([[1 if not(a&c).bit_count()%2 else -1 for c in (2,1,3)] for a in range(4)])
trans=np.array([bits.T@bits[list(p)]//4 for p in perm])
pairs=[(0,1)]+[(i,j) for i in (0,1) for j in range(2,7)]

def candidates():
    # The signed-near vectors of both full axes must cancel at every other spoke.
    sig=[np.r_[bits[np.argsort(p),0],bits[list(p),0]] for p in perm]
    bins=defaultdict(list)
    for x,y in product(range(24),repeat=2):bins[tuple(sig[x]+sig[y])].append((x,y))
    for key,q in bins.items():
        for a,b in product(q,bins[tuple(-x for x in key)]):yield a+b

def moves(q):
    # Simultaneous signed relabelings preserving the local order-five action and the two-axis family.
    for a,b,c in product(range(2),repeat=3):
        u=(a<<1)|c;v=(b<<1)|c
        projected=[perm.index(tuple(perm[k][i^u]^v for i in range(4))) for k in q]
        for mult in range(1,5):
            s=tuple(projected[(i*mult)%5-1] for i in range(1,5))
            yield s
            yield tuple(perm.index(tuple(np.argsort(perm[k]))) for k in s[::-1])

def core(q):
    m=59;B=np.zeros((m,m),np.int16)
    def edge(i,j):B[i,j]=B[j,i]=1
    for i in range(14):edge(0,1+i)
    for h in range(7):edge(2*h+1,2*h+2)
    for i,(h,k) in enumerate(pairs):
        for z in range(4):
            t=15+4*i+z;edge(t,1+2*h+z//2);edge(t,1+2*k+z%2)
            for bit in (1,2):edge(t,15+4*i+(z^bit))
    for i in range(5):
        for d,k in enumerate(q,1):
            j=(i+d)%5
            for u,v in enumerate(perm[k]):edge(19+i*4+u,39+j*4+v)
    return B

def eigen_blocks(q):
    for freq in range(3):
        n=12 if not freq else 7
        H=np.zeros((n,n),complex)
        def put(i,j,x):H[i,j]=x;H[j,i]=np.conj(x)
        u,v=n-6,n-3
        H[u+2,u+2]=H[v+2,v+2]=-2
        H[u:u+3,v:v+3]=sum(trans[k]*np.exp(2j*np.pi*freq*d/5) for d,k in enumerate(q,1))
        H[v:v+3,u:u+3]=H[u:u+3,v:v+3].conj().T
        if not freq:
            H[0,0]=H[1,1]=H[5,5]=-1;H[5,5]=-2
            H[2,2]=-1
            put(0,3,np.sqrt(2));put(1,4,np.sqrt(2));put(0,u,np.sqrt(10));put(1,v,np.sqrt(10))
        r=2 if not freq else 0
        H[r,r]=-1;put(r,u+1,np.sqrt(2));put(r,v+1,np.sqrt(2))
        yield freq,np.linalg.eigvalsh(H)

def exact_status(B):
    # A numerical suggestion is accepted only with an integral negative quadratic form
    # or a full-rank minor detected by finite-field elimination.
    from flint import nmod_mat
    for M,rank in [(27*np.eye(59,dtype=int)-9*B+1,44),(44*np.eye(59,dtype=int)+11*B-2,54)]:
        e,U=np.linalg.eigh(M)
        if e[0]<-1e-7:
            v=np.rint(100000*U[:,0]).astype(np.int64)
            if v@M@v<0:return 'negative form'
        if nmod_mat(M.tolist(),1009).rank()>rank:return 'rank violation'
    return 'pass'

def main():
    seen=set();results=Counter();good=[];allq=0
    for q in candidates():
        allq+=1
        if q in seen:continue
        orbit=set(moves(q));seen.update(orbit);B=core(q)
        if np.max(np.triu(B@B+B,1))>2:results['codegree']+=1;continue
        status=exact_status(B);results[status]+=1
        if status=='pass':good.append(q)
    assert len(seen)==allq
    print('balanced ordered quadruples',allq,'orbit outcomes',results,flush=True)
    np.save(tmp/'two-full-cores.npy',np.array(good,dtype=int))
if __name__=='__main__':main()
