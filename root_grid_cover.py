"""Projective transport on the 21 four-cells when all root squares lie in grids."""
import argparse
from collections import Counter
from itertools import combinations,product
import numpy as np
from triple_moments import tmp


def kernel(M,p):
    A=np.asarray(M,int).copy()%p;m,n=A.shape;r=0;piv=[]
    for j in range(n):
        indices=np.flatnonzero(A[r:,j])
        if len(indices)==0:continue
        k=r+indices[0];A[[r,k]]=A[[k,r]];A[r]=(A[r]*pow(int(A[r,j]),-1,p))%p
        c=A[:,j].copy();c[r]=0;A=(A-c[:,None]*A[r])%p;piv.append(j);r+=1
    out=[]
    for k in sorted(set(range(n))-set(piv)):
        x=np.zeros(n,int);x[k]=1;x[piv]=-A[:r,k]%p;out.append(x)
    assert all(not np.any(M@x%p) for x in out)
    return np.array(out)


class Cover:
    def __init__(self):
        self.cells=list(combinations(range(7),2));self.groups=[[i for i,p in enumerate(self.cells) if h in p] for h in range(7)]
        self.edges=[(i,j) for i,j in combinations(range(21),2) if set(self.cells[i]).isdisjoint(self.cells[j])]
        self.idx={p:i for i,p in enumerate(self.edges)}
        self.face=[(i,j,k) for i,j,k in combinations(range(21),3) if (i,j) in self.idx and (j,k) in self.idx and (i,k) in self.idx]
        self.link={p:[h for h,t in enumerate(self.face) if set(p)<=set(t)] for p in self.edges}
        assert len(self.edges)==len(self.face)==105
        n=len(self.edges);rows=[];tree={0}
        for i,j,k in self.face:
            v=np.zeros(n,int);v[[self.idx[i,j],self.idx[j,k],self.idx[i,k]]]=[1,1,-1];rows.append(v)
        while len(tree)<21:
            p=next((i,j) for i,j in self.edges if (i in tree)!=(j in tree))
            tree.update(p);v=np.zeros(n,int);v[self.idx[p]]=1;rows.append(v)
        self.hom=kernel(np.array(rows),3);assert self.hom.shape==(1,105)

    def connection(self):
        P=np.zeros((21,21),int)
        for (i,j),a in zip(self.edges,self.hom[0]):P[i,j]=a;P[j,i]=-a%3
        # Projective character c in i is c + P[i,j] in j.
        for i,j in combinations(range(21),2):
            if (i,j) in self.idx:continue
            common=[k for k in range(21) if tuple(sorted((i,k))) in self.idx and tuple(sorted((j,k))) in self.idx]
            cnt=Counter((P[i,k]+P[k,j])%3 for k in common)
            assert not any(v%2 for v in cnt.values())
        return P

    def roots(self,P):
        return self.root_domains((P[:,:,None]+np.arange(3))%3)

    def root_domains(self,Q):
        domains=[]
        for h,sites in enumerate(self.groups):
            allowed=[]
            for colors in product(range(3),repeat=6):
                col=dict(zip(sites,colors))
                for j,p in enumerate(self.cells):
                    if h in p:continue
                    counts=Counter(Q[i,j,c] for i,c in col.items() if tuple(sorted((i,j))) in self.idx)
                    if any(z%2 for z in counts.values()):break
                else:allowed.append(col)
            domains.append(allowed)
        return domains

    def choose(self,domains):
        used=[set() for _ in self.cells];chosen=[]
        def dfs(h):
            if h==7:
                yield [next(iter({0,1,2}-s)) for s in used],chosen.copy();return
            for x in domains[h]:
                if all(c not in used[i] for i,c in x.items()):
                    for i,c in x.items():used[i].add(c)
                    chosen.append(x);yield from dfs(h+1);chosen.pop()
                    for i,c in x.items():used[i].remove(c)
        yield from dfs(0)

    def face_problem(self,P,anti):
        # Over F2 the unique vector annihilated by a nonzero character is nonzero,
        # so we can index an antipodal translation by the product character that annihilates it.
        from ortools.sat.python import cp_model
        model=cp_model.CpModel();active=[model.new_bool_var('') for _ in self.face];colors=[]
        for z,t in enumerate(self.face):
            i=t[0];a=[(anti[j]+P[j,i])%3 for j in t];v=max(a,key=a.count)
            if a.count(v)<2:model.add(active[z]==0)
            colors.append(v)
        for i,j in self.edges:
            fs=self.link[i,j];model.add(sum(active[z] for z in fs)==2)
            need=Counter([anti[i],(anti[j]+P[j,i])%3])
            for v in range(3):
                model.add(sum(active[z] for z in fs if (colors[z]+P[self.face[z][0],i])%3==v)==need[v])
        solver=cp_model.CpSolver();solver.parameters.num_workers=1
        result=solver.solve(model)
        if result==cp_model.INFEASIBLE:return None
        assert result in (cp_model.FEASIBLE,cp_model.OPTIMAL)
        return [colors[i] if solver.value(t) else -1 for i,t in enumerate(active)]


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--limit',type=int,default=10000);a=p.parse_args()
    C=Cover();P=C.connection();D=C.roots(P);print('gauged flat C3 transports',C.hom.shape[0],'anchor domains',list(map(len,D)),flush=True)
    checked=0;found=0
    for anti,assign in C.choose(D):
        checked+=1
        if C.face_problem(P,anti) is not None:
            found+=1;print('triangle voltage assignments possible',checked,flush=True);break
        if checked>=a.limit:break
    print('tested',checked,'surviving',found,flush=True)
