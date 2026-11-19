"""Enumerate projective S3 matching data at a root with 21 incident rook grids."""
from itertools import combinations,product
from collections import Counter
import numpy as np
from root_grid_cover import Cover,kernel
from triple_moments import tmp


def bases(C):
    F=np.zeros((105,105),int)
    for k,(a,b,c) in enumerate(C.face):F[k,[C.idx[a,b],C.idx[b,c],C.idx[a,c]]]=1
    st={0};tree=[]
    while len(st)<21:
        p=next(p for p in C.edges if (p[0] in st)!=(p[1] in st));st.update(p);row=np.zeros(105,int);row[C.idx[p]]=1;tree.append(row)
    return F,np.array(tree)


def sign_cases(C):
    F,tree=bases(C);sol=kernel(np.vstack((F.T@F,tree)),2)
    cs=np.array(list(product(range(2),repeat=len(sol))));bits=cs@sol%2;t=bits@F.T%2
    def pack(x):return sum(1<<int(i) for i in np.flatnonzero(x))
    index={pack(f):i for i,f in enumerate(t)};assert len(index)==256
    moves=[]
    for i in range(6):
        p=list(range(7));p[i],p[i+1]=p[i+1],p[i]
        s=[C.cells.index(tuple(sorted(p[j] for j in e))) for e in C.cells]
        mv=[C.face.index(tuple(sorted(s[j] for j in e))) for e in C.face]
        moves.append([index[pack(f[mv])] for f in t])
    seen=set();out=[]
    for a in range(256):
        if a in seen:continue
        orbit={a};stack=[a]
        while stack:
            b=stack.pop()
            for m in moves:
                z=m[b]
                if z not in orbit:orbit.add(z);stack.append(z)
        seen.update(orbit);out.append((bits[a],len(orbit),t[a]))
    return out


def rotations(C,S):
    _,tree=bases(C);sig=np.ones((21,21),int);A=np.zeros((21,21,105),int)
    for i,j in C.edges:
        k=C.idx[i,j];sig[i,j]=sig[j,i]=1-2*int(S[k]);A[i,j,k]=1;A[j,i,k]=-sig[i,j]
    rows=list(tree);paths={}
    for i,j in combinations(range(21),2):
        nbs=[k for k in range(21) if tuple(sorted((i,k))) in C.idx and tuple(sorted((j,k))) in C.idx]
        sign=np.array([sig[i,k]*sig[k,j] for k in nbs])
        distance=np.array([sig[k,j]*A[i,k]+A[k,j] for k in nbs])
        paths[i,j]=(sign,distance)
        if (i,j) in C.idx:
            same=sign==sig[i,j]
            assert sum(same) in (1,3)
            rows.extend(distance[same]-A[i,j])
            if sum(~same):
                x,y=distance[~same];rows.append(x-y)
        elif sum(sign==-1) in (1,5):
            return None,None,None
    M=kernel(np.array(rows),3)
    return M,paths,(sig,A)


def test_paths(paths,t):
    for (i,j),(sgn,coef) in paths.items():
        if len(sgn)==3:continue
        d=coef@t%3
        valid=True
        for c in range(3):
            if np.any(np.bincount((sgn*c+d)%3,minlength=3)%2):valid=False;break
        if not valid:return False
    return True


if __name__=='__main__':
    C=Cover();D=sign_cases(C);print('sign orbit sizes',[s for _,s,_ in D],flush=True)
    for case,(S,z,f) in enumerate(D):
        M,paths,P=rotations(C,S)
        if M is None:print(case,'sign orbit rejected by six paths',flush=True);continue
        n=len(M);print(case,'negative triangles',sum(f),'offset dimension',n,flush=True)
        if n>12:continue
        kept=[]
        for x in product(range(3),repeat=n):
            t=np.array(x)@M%3 if n else np.zeros(105,int)
            if test_paths(paths,t):kept.append(t)
        print(case,'six-path projective solutions',len(kept),flush=True)
        np.savez_compressed(tmp/('root-linear-%d.npz'%case),sign=S,trans=np.array(kept),sig=P[0],A=P[1])
