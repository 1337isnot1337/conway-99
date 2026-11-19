"""Orbit-averaged outer-edge moment constraints, with no graph automorphism assumption."""
import argparse
from collections import Counter
from functools import reduce
from itertools import combinations,permutations,product
from math import gcd
from pathlib import Path
import json
import numpy as np
import scipy.sparse as sp
from scipy.optimize import linprog
from threadpoolctl import threadpool_limits


class OrbitModel:
    def __init__(self,k):
        self.k=k
        self.labels=list(p for p in combinations(range(k),2) if p[0]^1!=p[1])
        self.n=len(self.labels)
        self.pairs=[(-1,-1),*combinations(range(self.n),2)]
        self.m=len(self.pairs)
        self.edges=np.zeros((self.n,self.n),dtype=np.int32)
        for i,(a,b) in enumerate(self.pairs[1:],1):self.edges[a,b]=self.edges[b,a]=i
        self.iidx=np.zeros((k,k),dtype=np.int32)
        for i,(a,b) in enumerate(self.labels):self.iidx[a,b]=self.iidx[b,a]=i
        path=Path('/tmp/conway99-tools')/('pair-orbits.bin' if k==14 else 'pair-orbits-%d.bin'%k)
        p=np.fromfile(path,dtype=np.uint16)
        self.C=np.empty((self.m,self.m),dtype=np.uint16)
        for i in range(self.m):
            self.C[i,:i+1]=self.C[:i+1,i]=p[i*(i+1)//2:(i+1)*(i+2)//2]
        self.types,reps=np.unique(p,return_index=True)
        self.dim=len(reps)
        self.reps=[]
        for pos in reps:
            a=(int(np.sqrt(8*pos+1))-1)//2
            self.reps.append((a,int(pos-a*(a+1)//2)))
        _,self.marks=np.unique(self.C[0],return_index=True)

    def suborbits(self,mark):
        if not mark:return np.unique(self.C[0],return_inverse=True)[1]
        k=self.k
        e,f=self.pairs[mark]
        support=sorted(set(i//2 for i in self.labels[e]+self.labels[f]))
        rest=sorted(set(range(k//2))-set(support))
        actions=[]
        for p in permutations(support):
            for flips in product((0,1),repeat=len(support)):
                action=np.arange(k)
                for i,j,s in zip(support,p,flips):
                    action[2*i]=2*j+s;action[2*i+1]=2*j+1-s
                def label(h):
                    a,b=self.labels[h];return self.iidx[action[a],action[b]]
                if self.edges[label(e),label(f)]==mark:actions.append(action)
        if rest:
            action=np.arange(k);a=2*rest[0];action[a],action[a+1]=a+1,a;actions.append(action)
        for i,j in zip(rest,rest[1:]):
            action=np.arange(k)
            action[2*i:2*i+2]=[2*j,2*j+1]; action[2*j:2*j+2]=[2*i,2*i+1]
            actions.append(action)
        labels=np.array(self.labels)
        edges=np.array(self.pairs[1:])
        orb=np.arange(self.m)
        for act in actions:
            y=act[labels]
            vperm=self.iidx[y[:,0],y[:,1]]
            u=vperm[edges]
            perm=np.r_[0,self.edges[u[:,0],u[:,1]]]
            edges2=sp.coo_matrix((np.ones(len(perm)),(orb,orb[perm])),shape=(self.m,self.m))
            _,comp=sp.csgraph.connected_components(edges2,directed=False)
            orb=comp[orb]
        return np.unique(orb,return_inverse=True)[1]

    def moment_blocks(self):
        blocks=[]
        for mark in self.marks:
            orb=self.suborbits(mark)
            groups=[np.flatnonzero(orb==z) for z in range(orb.max()+1)]
            ii=[];jj=[];vv=[]
            for i,g in enumerate(groups):
                p=g[0]
                for j,f in enumerate(groups[:i+1]):
                    classes,counts=np.unique(self.C[p,f],return_counts=True)
                    ii.extend([i*(i+1)//2+j]*len(classes))
                    jj.extend(classes)
                    vv.extend(len(g)*counts)
            blocks.append((mark,len(groups),sp.csr_matrix((vv,(ii,jj)),shape=(len(groups)*(len(groups)+1)//2,self.dim),dtype=np.int64)))
        return blocks

    def constraints(self):
        eq=set();ineq=set()
        def add(collection,terms):
            v=Counter()
            for col,c in terms:v[int(col)]+=int(c)
            v={j:c for j,c in v.items() if c}
            if v:
                d=reduce(gcd,v.values(),0)
                if collection is eq and v[min(v)]<0:d=-d
                collection.add(tuple(sorted((j,c//d) for j,c in v.items())))
        for a,b in self.reps:
            if a and b:
                q=self.C[a,b];p=self.C[0,a];r=self.C[0,b]
                add(ineq,[(p,1),(q,-1)])
                add(ineq,[(r,1),(q,-1)])
                add(ineq,[(0,1),(q,1),(p,-1),(r,-1)])
        for v in self.marks:
            add(eq,[(self.C[v,v],1),(self.C[0,v],-1)])
            for i,e in enumerate(self.labels):
                for a in range(self.k):
                    d=2-int(a in e)-int((a^1) in e)
                    terms=[(self.C[v,self.edges[i,j]],1) for j,f in enumerate(self.labels) if a in f and j!=i]
                    add(eq,terms+[(self.C[0,v],-d)])
        for p in self.marks:
            if not p:continue
            i,j=self.pairs[p]
            terms=[(self.C[self.edges[i,z],self.edges[j,z]],1) for z in range(self.n) if z not in (i,j)]
            add(eq,terms+[(self.C[0,p],1),(0,len(set(self.labels[i])&set(self.labels[j]))-2)])
        return eq,ineq


def dense(rows,d):
    mat=np.zeros((len(rows),d),dtype=float)
    for i,row in enumerate(rows):
        for j,c in row:mat[i,j]=c
    return mat


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--degree',type=int,default=14)
    p.add_argument('--rounds',type=int,default=100)
    a=p.parse_args()
    model=OrbitModel(a.degree)
    eq,ineq=model.constraints();blocks=model.moment_blocks()
    print('dimension',model.dim,'eq',len(eq),'ineq',len(ineq),'fixed-vector block sizes',[n for _,n,_ in blocks],flush=True)
    E=dense(eq,model.dim);A=list(dense(ineq,model.dim));bounds=[(1,1)]+[(0,1)]*(model.dim-1)
    rng=np.random.default_rng(120)
    # A random objective selects a reproducible extremal point. Later rounds
    # blend feasible LP points to look for a PSD interior.
    objective=rng.normal(size=model.dim)
    pool=[]
    for it in range(a.rounds):
        sol=linprog(objective,A_ub=-np.array(A),b_ub=np.zeros(len(A)),A_eq=E,b_eq=np.zeros(len(E)),bounds=bounds,method='highs')
        if not sol.success:
            print('LP status requires exact certificate:',sol.message,flush=True);return
        x=sol.x
        pool.append(x)
        if len(pool)>12:pool.pop(0)
        xs=[x,np.mean(pool,axis=0)]
        worsts=[]
        for q,z in enumerate(xs):
            worst=0
            for _,n,T in blocks:
                lo=np.tril_indices(n)
                M=np.zeros((n,n));M[lo]=T@z;M.T[lo]=M[lo]
                d=np.sqrt(np.maximum(.01,np.diag(M)))
                val,vec=np.linalg.eigh(M/d[:,None]/d[None,:])
                worst=min(worst,float(val[0]))
                if q:continue
                for j in range(min(3,n)):
                    if val[j]>=-1e-8:break
                    w=vec[:,j]/d;w/=max(abs(w))
                    for fac in (4,32,256,2048,65536):
                        v=np.rint(w*fac).astype(np.int64)
                        if v@M@v>=-1e-9:continue
                        row=T.T@(v[lo[0]]*v[lo[1]]*(1+(lo[0]!=lo[1])))
                        A.append(row/max(abs(row)))
                        break
            worsts.append(worst)
            if worst>-1e-8:
                print('numerical feasibility, worst',worst,'iteration',it,flush=True)
                np.save(Path(__file__).with_name('outer-point-%d.npy'%a.degree),z)
                return
        if it%10==0:print('iteration',it,'rows',len(A),'worst eigenvalues',worsts,flush=True)
        if it%6==5: objective=rng.normal(size=model.dim)
    print('cut budget reached',flush=True)

if __name__=='__main__':
    with threadpool_limits(limits=1):main()
