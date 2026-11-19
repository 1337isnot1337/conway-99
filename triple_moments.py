"""Third-order Boolean moments of the 84-vertex rooted graph, averaged over all axis labelings."""
import argparse
from collections import deque,Counter
from itertools import product,permutations,combinations
from functools import reduce
from pathlib import Path
from math import gcd
import subprocess
import numpy as np
import scipy.sparse as sp
from scipy.optimize import linprog
from outer_moments import OrbitModel

tmp=Path('/tmp/conway99-tools')
def pack(a,b):
    hi=np.maximum(a,b).astype(np.int32)
    return hi*(hi+1)//2+np.minimum(a,b)


def perms(m,mark):
    k=m.k; base=np.arange(k)
    lab=np.array(m.labels); pairs=np.array(m.pairs[1:])
    def lift(g):
        y=g[lab];p=m.iidx[y[:,0],y[:,1]][pairs]
        return np.r_[0,m.edges[p[:,0],p[:,1]]].astype(np.uint16)
    res=[]
    support=[] if not mark else sorted({i//2 for u in m.pairs[mark] for i in m.labels[u]})
    for p in permutations(support):
        for flips in product((0,1),repeat=len(support)):
            g=base.copy()
            for i,j,b in zip(support,p,flips):g[2*i:2*i+2]=[2*j+b,2*j+1-b]
            if mark and lift(g)[mark]==mark and np.any(g!=base):res.append(g)
    # The support group has order at most eight here. Keep only generators.
    group={tuple(base)};gens=[]
    for g in res:
        if tuple(g) in group:continue
        gens.append(g);queue=deque(group)
        while queue:
            v=np.array(queue.popleft())
            for h in gens:
                w=tuple(h[v])
                if w not in group:group.add(w);queue.append(w)
    rest=sorted(set(range(k//2))-set(support))
    if rest:
        g=base.copy();a=rest[0]*2;g[a:a+2]=[a+1,a];gens.append(g)
    for i,j in zip(rest,rest[1:]):
        g=base.copy();g[2*i:2*i+2]=[2*j,2*j+1];g[2*j:2*j+2]=[2*i,2*i+1];gens.append(g)
    return [lift(g) for g in gens]


class Triples:
    def __init__(self,k):
        m=self.model=OrbitModel(k);self.marks=np.array(m.marks)
        self.generators=perms(m,0)
        maps=np.empty((m.m,m.m),dtype=np.uint16)
        self.type=np.full(m.m,-1)
        for idx,r in enumerate(self.marks):
            self.type[r]=idx;maps[r]=np.arange(m.m)
            q=deque([r])
            while q:
                a=q.popleft()
                for g in self.generators:
                    b=g[a]
                    if self.type[b]>=0:continue
                    self.type[b]=idx;maps[b]=g[maps[a]];q.append(b)
        assert min(self.type)>=0
        self.move=np.argsort(maps,axis=1).astype(np.uint16)
        ptab=[];first=[];starts=[]
        for mark in self.marks:
            prefix=tmp/('triple-%d-%d'%(k,mark));out=prefix.with_suffix('.bin')
            if mark==0:
                orig=tmp/('pair-orbits.bin' if k==14 else 'pair-orbits-%d.bin'%k)
                c=np.fromfile(orig,dtype=np.uint16)
            else:
                if not out.exists():
                    pfile=prefix.with_suffix('.gens');np.array(perms(m,mark),dtype=np.uint16).tofile(pfile)
                    subprocess.run([str(tmp/'stabilizer_pairs'),str(m.m),str(pfile),str(out)],check=True)
                c=np.memmap(out,dtype=np.uint32,mode='r')
            starts.append(sum(len(z) for z in first))
            # IDs are allocated in first-appearance order.
            n=int(max(c)) if len(c)<10000 else int(c.max())
            ids,index=np.unique(c,return_index=True)
            assert n+1==len(ids)
            first.append(index);ptab.append(c)
        starts=np.array(starts)
        def raw(a,b,c):
            t=self.type[a];mb=self.move[a,b];mc=self.move[a,c]
            return starts[t]+ptab[t][pack(mb,mc)]
        ii=[];jj=[];examples=[]
        for s,(r,index) in enumerate(zip(self.marks,first)):
            a=((np.sqrt(8*index+1).astype(np.int64)-1)//2).astype(np.int32);b=(index-a*(a+1)//2).astype(np.int32)
            for j,(x,y) in enumerate(zip(a,b)):
                x=int(x);y=int(y)
                src=starts[s]+j
                for v in [raw(x,r,y),raw(y,r,x)]:
                    ii.append(src);jj.append(v)
                if x==r or x==y:ii.append(src);jj.append(raw(0,r,y))
                if y==r:ii.append(src);jj.append(raw(0,r,x))
                examples.append((int(r),x,y))
        n=len(examples)
        _,label=sp.csgraph.connected_components(sp.coo_matrix((np.ones(len(ii)),(ii,jj)),shape=(n,n)),directed=False)
        self.table=[label[start:start+len(z)] for start,z in zip(starts,first)]
        self.pairs=ptab
        _,reps=np.unique(label,return_index=True)
        self.reps=np.array(examples,dtype=np.int32)[reps];self.d=len(reps)
        assert int(self.value(0,0,0))==0
        print('root degree',k,'raw marked types',n,'Boolean moments',self.d,flush=True)

    def value(self,a,b,c):
        t=self.type[a];u=self.move[a,b];v=self.move[a,c]
        return self.table[t][self.pairs[t][pack(u,v)]]


class Rows:
    def __init__(self):
        self.rows=set()
    def add(self,terms,eq):
        counts=Counter()
        for i,v in terms:counts[int(i)]+=int(v)
        counts={i:v for i,v in counts.items() if v}
        if not counts:return
        d=reduce(gcd,counts.values(),0)
        if eq and counts[min(counts)]<0:d=-d
        self.rows.add(tuple(sorted((i,v//d) for i,v in counts.items())))
    def matrix(self,n):
        ii=[];jj=[];vv=[]
        for i,row in enumerate(self.rows):
            for j,v in row:ii.append(i);jj.append(j);vv.append(v)
        return sp.csr_matrix((vv,(ii,jj)),shape=(len(self.rows),n),dtype=float)


def linear(t):
    m=t.model;eq=Rows();ge=Rows()
    V=t.value
    for a,b,c in t.reps:
        x=V(a,b,c);ab=V(0,a,b);ac=V(0,a,c);bc=V(0,b,c)
        xa,xb,xc=[V(0,0,y) for y in (a,b,c)]
        for p in (ab,ac,bc):ge.add([(p,1),(x,-1)],False)
        for p,q,s in ((ab,ac,xa),(ab,bc,xb),(ac,bc,xc)):
            ge.add([(s,1),(p,-1),(q,-1),(x,1)],False)
        ge.add([(0,1),(xa,-1),(xb,-1),(xc,-1),(ab,1),(ac,1),(bc,1),(x,-1)],False)
    row=[]
    for i,outer in enumerate(m.labels):
        for h in range(m.k):
            vs=np.array([m.edges[i,j] for j,f in enumerate(m.labels) if j!=i and h in f])
            row.append((vs,2-int(h in outer)-int((h^1) in outer)))
    for a,b in m.reps:
        y=V(0,a,b)
        for vs,co in row:
            terms=[(z,1) for z in V(a,b,vs)]
            eq.add(terms+[(y,-co)],True)
    for a in m.marks:
        baseline=V(0,0,a)
        for v,(i,j) in enumerate(m.pairs[1:],1):
            ix=np.delete(np.arange(m.n),[i,j])
            vals=V(a,m.edges[i,ix],m.edges[j,ix])
            eq.add([(z,1) for z in vals]+[(V(0,a,v),1),(baseline,len(set(m.labels[i])&set(m.labels[j]))-2)],True)
    E=eq.matrix(t.d);F=ge.matrix(t.d)
    print('eq',E.shape,E.nnz,'inequalities',F.shape,F.nnz,flush=True)
    return E,F

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--degree',type=int,default=14);p.add_argument('--solve',action='store_true')
    args=p.parse_args();t=Triples(args.degree)
    prefix=tmp/('outer3-%d'%args.degree)
    ep=str(prefix)+'-eq.npz';fp=str(prefix)+'-ge.npz'
    if Path(ep).exists() and Path(fp).exists():E=sp.load_npz(ep);F=sp.load_npz(fp)
    else:
        E,F=linear(t);sp.save_npz(ep,E);sp.save_npz(fp,F)
    if args.solve:
        res=linprog(np.zeros(t.d),A_ub=-F,b_ub=np.zeros(F.shape[0]),A_eq=E,b_eq=np.zeros(E.shape[0]),bounds=[(1,1)]+[(0,1)]*(t.d-1),method='highs',options={'time_limit':180})
        print(res.status,res.message,flush=True)
        if res.success:
            print('actual violations',np.abs(E@res.x).max(),min(F@res.x),flush=True)
            np.save(str(prefix)+'-point.npy',res.x)
