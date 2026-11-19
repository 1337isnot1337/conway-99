"""Complete internal rook grids around a nine-fiber finite-field matching pattern."""
from functools import lru_cache
from itertools import combinations,permutations
from pathlib import Path
import argparse
import numpy as np
from triple_moments import tmp


def gf(a,b,multiply=False):
    x,y=divmod(a,3);z,w=divmod(b,3)
    if multiply:return ((x*w+y*z)%3)*3+(y*w-x*z)%3
    return ((x+z)%3)*3+(y+w)%3


class Grids:
    def __init__(self):
        self.edges=list(combinations(range(9),2));self.pos={p:i for i,p in enumerate(self.edges)}
        R={(i,j) for i,j in self.edges if i//3==j//3 or i%3==j%3}
        self.grids=sorted({sum(1<<z for z,(i,j) in enumerate(self.edges) if tuple(sorted((f[i],f[j]))) in R) for f in permutations(range(9))})
        assert len(self.grids)==5040
        self.all=(1<<5040)-1
        self.edgebits=[sum(1<<k for k,M in enumerate(self.grids) if M>>z&1) for z in range(36)]
        self.refl=np.array([[gf(t,gf(x,x)) for x in range(9)] for t in range(9)])
        self.moves=np.array([[self.pos[tuple(sorted((p[a],p[b])))] for a,b in self.edges] for p in self.refl])
        self.forbidden={}
    def build(self,cells,twists=None):
        self.cells=list(cells);self.P={}
        for i,j in combinations(self.cells,2):
            v=gf(i,j,True) if twists is None else twists[i,j];self.P[i,j]=self.P[j,i]=self.refl[v]
        for i in self.cells:
            for j in self.cells:
                if i==j:continue
                p=self.P[i,j];limit=np.full((9,9),2,np.int16)-np.eye(9,dtype=np.int16)
                for k in self.cells:
                    if k in (i,j):continue
                    q=p[self.P[k,j][self.P[i,k]]];limit[np.arange(9),q]-=1
                assert np.array_equal(limit,limit.T)
                if limit.min()<0:return False
                self.forbidden[i,j]=[(z,self.pos[tuple(sorted((p[x],p[y])))],int(limit[x,y])) for z,(x,y) in enumerate(self.edges)]
        self.allowed.cache_clear()
        return True
    @lru_cache(maxsize=100000)
    def allowed(self,i,j,g):
        M=self.grids[g];bad=0
        for x,y,k in self.forbidden[i,j]:
            if M>>x&1:
                if k==0:return 0
                if k==1:bad|=self.edgebits[y]
            elif k==0:bad|=self.edgebits[y]
        return self.all^bad
    def search(self,limit,initial=None):
        todo={i:self.all for i in self.cells};solution={};nodes=0;depth=0
        if initial is not None:todo[self.cells[0]]=1<<initial
        def visit(candidates):
            nonlocal nodes,depth
            if limit and nodes>=limit:return
            nodes+=1;depth=max(depth,len(solution))
            if not candidates:yield solution.copy();return
            i=min(candidates,key=lambda i:candidates[i].bit_count());bits=candidates[i]
            while bits and (not limit or nodes<limit):
                p=bits&-bits;g=p.bit_length()-1;bits^=p
                other={}
                for j,c in candidates.items():
                    if i==j:continue
                    u=c&self.allowed(i,j,g)
                    if not u:break
                    other[j]=u
                else:
                    solution[i]=g;yield from visit(other);del solution[i]
        yield from visit(todo)
        self.stats=(nodes,depth)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--groups',type=int,default=9);p.add_argument('--limit',type=int,default=0);a=p.parse_args()
    m=Grids();assert m.build(range(a.groups))
    found=0
    for grids in m.search(a.limit):
        found+=1;print('complete internal assignment',grids,flush=True)
        if found>=10:break
    print('solutions observed',found,'search',getattr(m,'stats','stopped at ten survivors'),flush=True)
