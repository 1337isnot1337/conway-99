"""Solve an exact row-set compatibility problem for a prescribed maximum-coclique incidence matrix."""
import argparse,subprocess
from collections import deque
import numpy as np
from triple_moments import tmp


def domains(C,k,step,tag):
    h,n=C.shape;name=tmp/('coclique-%s'%tag)
    points=[sum(1<<int(j) for j in np.flatnonzero(c)) for c in C.T]
    inp=name.with_suffix('.in');out=name.with_suffix('.out')
    inp.write_text(' '.join(map(str,[k,h,n,step,*points])))
    subprocess.run([str(tmp/'coclique_rows'),str(inp),str(out)],check=True)
    L=[[] for _ in range(n)];lines=iter(out.read_text().splitlines())
    def rotate(x,s):
        result=0
        while x:
            i=(x&-x).bit_length()-1;x&=x-1;result|=1<<(i//step*step+(i+s)%step)
        return result
    for line in lines:
        i,z=map(int,line.split())
        for _ in range(z):
            a,b=map(int,next(lines).split());v=a+(b<<64)
            for t in range(step):L[i+t].append(rotate(v,t))
    return L


def search(C,L):
    n=len(L);intersection=C.T@C
    # A pair of complete rows fixes both their mutual edge and their entire common-neighbor count.
    def compatible(i,x,j,y):
        a=(x>>j)&1
        return a==((y>>i)&1) and (x&y).bit_count()==2-int(intersection[i,j])-a
    def branch(D):
        if any(not x for x in D):return None
        q=deque(sorted(((i,j) for i in range(n) for j in range(n) if i!=j),key=lambda ij:len(D[ij[1]])))
        while q:
            i,j=q.popleft()
            new=[x for x in D[i] if any(compatible(i,x,j,y) for y in D[j])]
            if len(new)==len(D[i]):continue
            if not new:return None
            D[i]=new
            q.extend((t,i) for t in range(n) if t not in (i,j))
        choices=[i for i in range(n) if len(D[i])>1]
        if not choices:return [d[0] for d in D]
        i=min(choices,key=lambda j:len(D[j]))
        for x in D[i]:
            new=D.copy();new[i]=[x];res=branch(new)
            if res is not None:return res
        return None
    return branch([s.copy() for s in L])


def finish(C,k,step,tag):
    L=domains(C,k,step,tag);print('root domains',[len(s) for s in L[::step]],flush=True)
    if step>1:
        # The orbit shortcut is valid for the incidence input only. Choices of completed rows are unrestricted.
        for i in range(C.shape[1]):
            ci=C[:,i].reshape(2,11)
            assert np.array_equal(np.roll(ci,1,axis=1).ravel(),C[:,i//11*11+(i+1)%11])
    sol=search(C,L)
    if sol is None:return None
    H=np.array([[(x>>j)&1 for j in range(len(L))] for x in sol],dtype=np.int16)
    h=len(C);G=np.block([[np.zeros((h,h),np.int16),C],[C.T,H]])
    assert np.all(G==G.T) and np.all(np.diag(G)==0) and np.all(G.sum(0)==k)
    assert np.all(G@G+G==(k-2)*np.eye(len(G),dtype=int)+2)
    return G


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--control',action='store_true');p.add_argument('--seed',type=int,default=1);a=p.parse_args()
    if a.control:
        R=np.array([[i!=j and (i//3==j//3 or i%3==j%3) for j in range(9)] for i in range(9)],np.int16)
        I=[0,4,8];O=sorted(set(range(9))-set(I));C=R[np.ix_(I,O)]
        assert finish(C,4,1,'rook') is not None
        print('reconstructed and verified nine-vertex graph')
    else:
        C=np.load(tmp/('coclique-design-%d.npy'%a.seed));G=finish(C,14,11,str(a.seed))
        print('full completion exists',G is not None,flush=True)
        if G is not None:np.save('verified-conway-99.npy',G)
