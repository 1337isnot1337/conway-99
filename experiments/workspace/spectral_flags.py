"""Root-conditioned projector matrices on all neighborhood classes of a root."""
import argparse,pickle
from functools import lru_cache
from itertools import combinations
import numpy as np
import scipy.sparse as sp
from pynauty import certificate
from flag_moments import BASE,cache9
from subgraph_counts import nauty,extensions


def matrices(pack,r,schur=False):
    graphs,levels,*_=pack
    lookup={(len(g),certificate(nauty(g))):j for j,g in enumerate(graphs) if g}
    @lru_cache(maxsize=100000)
    def gid(g):
        for a,ra in enumerate(g):
            for b in range(a):
                if (ra&g[b]).bit_count()>2-(ra>>b&1):return -1
        return lookup[len(g),certificate(nauty(g))]
    output=[]
    for root in levels[r]:
        g=graphs[root]
        options=list(extensions(g))
        n=(0 if schur else r)+len(options)
        paths=[gid(q) for _,q in options]
        # Vectors indicator of a root vertex or a full outside neighborhood class.
        ii=[];jj=[];wminus=[];wplus=[]
        def add(row,id,diagonal,adj):
            if id<0:return
            ii.append(row);jj.append(id)
            wminus.append(27*diagonal-9*adj+1)
            wplus.append(44*diagonal+11*adj-2)
        def projection_coefficients():
            from flint import fmpq_mat
            import math
            masks=np.array([[(mask>>i)&1 for i in range(r)] for mask,_ in options],dtype=np.int64)
            A=np.array([[(row>>i)&1 for i in range(r)] for row in g],dtype=np.int64)
            result=[]
            for diag,edge,constant in ((27,-9,1),(44,11,-2)):
                gram=diag*np.eye(r,dtype=np.int64)+edge*A+constant
                inv=fmpq_mat(gram.tolist()).inv()
                denominator=math.lcm(*(int(v.q) for v in inv.entries()))
                inverse=np.array([[int(inv[i,j]*denominator) for j in range(r)] for i in range(r)],dtype=np.int64)
                crosses=constant+edge*masks
                prod=crosses@inverse@crosses.T
                divisor=math.gcd(denominator,*(int(z) for z in prod.flat))
                result.append((denominator//divisor,prod//divisor))
            return result
        if schur:
            (dm,pm),(dp,pp)=projection_coefficients()
        for i in range(0 if schur else r):
            for j in range(i+1):
                add(i*(i+1)//2+j,root,i==j,(g[i]>>j)&1)
        for i,(u,left) in enumerate(options):
            x=(0 if schur else r)+i
            for j in range(0 if schur else r):
                add(x*(x+1)//2+j,paths[i],False,(u>>j)&1)
            for j,(v,_) in enumerate(options[:i+1]):
                row=x*(x+1)//2+(0 if schur else r)+j
                def append(id,diagonal,adj):
                    if id<0:return
                    add(row,id,diagonal,adj)
                    if schur:
                        wminus[-1]=wminus[-1]*dm-int(pm[i,j])
                        wplus[-1]=wplus[-1]*dp-int(pp[i,j])
                if i==j:append(paths[i],True,False)
                q=tuple(left[a]|(((v>>a)&1)<<(r+1)) for a in range(r))+(u,v)
                id=gid(q)
                if id<0:continue
                append(id,False,False)
                q=q[:r]+(u|(1<<(r+1)),v|(1<<r))
                append(gid(q),False,True)
        for weights in (wminus,wplus):
            mat=sp.csr_matrix((weights,(ii,jj)),shape=(n*(n+1)//2,len(graphs)),dtype=np.int64)
            output.append((root,range(n),mat))
    return output


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('r',type=int)
    p.add_argument('--schur',action='store_true')
    a=p.parse_args()
    g=matrices(cache9(),a.r,a.schur)
    file=BASE/('induced-spectral-%d.pickle'%a.r)
    if a.schur:file=file.with_name('induced-schur-%d.pickle'%a.r)
    with file.open('wb') as f:pickle.dump(g,f)
    print(file.name,'blocks',len(g),'entries',sum(t.shape[0] for _,_,t in g),flush=True)
