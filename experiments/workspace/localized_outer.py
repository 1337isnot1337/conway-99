"""Third-moment semidefinite restrictions for conditioning on a bit and on both graph projectors."""
import argparse
from pathlib import Path
import numpy as np
import scipy.sparse as sp
from triple_moments import Triples,tmp


def compressed(n,rows,d):
    ii=[];jj=[];vv=[]
    for i,col,coef in rows:
        unique,sums=np.unique(col,return_inverse=True)
        totals=np.bincount(sums,weights=coef)
        ok=totals!=0
        ii.extend([i]*sum(ok));jj.extend(unique[ok]);vv.extend(totals[ok])
    return sp.csr_matrix((vv,(ii,jj)),shape=(n*(n+1)//2,d))


def conditioned(t):
    m=t.model
    for a in m.marks:
        orbits=m.suborbits(a)
        groups=[np.where(orbits==j)[0] for j in range(orbits.max()+1)]
        n=len(groups)
        for positive in [True,False] if a else [True]:
            def rows():
                for i,g in enumerate(groups):
                    u=g[0]
                    for j,h in enumerate(groups[:i+1]):
                        ids=t.value(a,u,h);vv=np.ones(len(h))*np.sqrt(len(g)/len(h))
                        if not positive:
                            ids=np.r_[ids,t.value(0,u,h)];vv=np.r_[-vv,vv]
                        yield i*(i+1)//2+j,ids,vv
            yield ('conditional-%d-%d'%(a,positive),n,compressed(n,rows(),t.d))


def projectors(t):
    m=t.model;k=m.k;N=1+k+m.n;d=t.d
    # Orbit of (vertex, Boolean variable) by a connected component pass on generator permutations.
    # Identify lifts on vertices from the image of edges between outer vertices.
    edge_pairs=np.array(m.pairs)
    outerlab=list(map(set,m.labels))
    gen_actions=[]
    for g in t.generators:
        # Reconstruct images of outer-vertex stars, then of near labels via their incidence sets.
        w=[]
        for i in range(m.n):
            e,f=m.edges[i,np.arange(m.n)!=i][:2]
            point=set(m.pairs[g[e]])&set(m.pairs[g[f]])
            w.append(point.pop())
        near=[]
        for i in range(k):
            inside=[w[j] for j,lab in enumerate(outerlab) if i in lab]
            u=set.intersection(*(outerlab[j] for j in inside));near.append(u.pop())
        gen_actions.append(np.r_[0,1+np.array(near),1+k+np.array(w)])
    ids=np.arange(N*m.m,dtype=np.int32)
    oi=ids.copy()
    for vertex,edge in zip(gen_actions,t.generators):
        perm=(vertex[:,None]*m.m+edge).ravel()
        data=sp.coo_matrix((np.ones(len(ids),np.int8),(oi,oi[perm])),shape=(len(ids),len(ids)))
        _,c=sp.csgraph.connected_components(data,directed=False)
        oi=c[oi]
    _,reps,orbits,sz=np.unique(oi,return_inverse=True,return_index=True,return_counts=True);n=len(reps)
    pvertex=ids//m.m;pbit=ids%m.m
    fixed=np.zeros((N,N),dtype=np.int8);loc=np.zeros((N,N),dtype=np.int32)
    fixed[0,1:1+k]=fixed[1:1+k,0]=1
    fixed[np.arange(1,k+1),1+(np.arange(k)^1)]=1
    for i,(u,v) in enumerate(m.labels,1+k):fixed[i,[1+u,1+v]]=fixed[[1+u,1+v],i]=1
    loc[1+k:,1+k:]=m.edges
    r=int((np.sqrt(4*k-7)-1)/2);s=-1-r
    for name,diag,adj,one in [('minus',r,-1,(k-r)/N),('plus',-s,1,-(k-s)/N)]:
        rr=[];cc=[];vv=[]
        for i,rep in enumerate(reps):
            v,a=divmod(rep,m.m);keep=orbits<=i
            j=orbits[keep];u=pvertex[keep];b=pbit[keep]
            base=t.value(0,a,b)
            coeff=diag*(u==v)+adj*fixed[v,u]+one
            mark=loc[v,u];has=mark!=0
            z=t.value(a,b[has],mark[has])
            key=np.r_[j*d+base,j[has]*d+z];weight=np.r_[coeff,np.full(len(z),adj)]
            keys,ix=np.unique(key,return_inverse=True)
            total=np.bincount(ix,weights=weight)
            jx=keys//d;cx=keys%d;total*=np.sqrt(sz[i]/sz[jx])
            nnz=np.abs(total)>1e-9
            rr.extend(i*(i+1)//2+jx[nnz]);cc.extend(cx[nnz]);vv.extend(total[nnz])
        yield 'projector-'+name,n,sp.csr_matrix((vv,(rr,cc)),shape=(n*(n+1)//2,d))


def blocks(k,kind):
    import pickle
    path=tmp/('outer3-%d-%s.pickle'%(k,kind))
    if path.exists():return pickle.load(path.open('rb'))
    t=Triples(k)
    out=list(conditioned(t) if kind=='conditional' else projectors(t))
    with path.open('wb') as f:pickle.dump(out,f)
    return out

def test(data,x):
    out=[]
    for name,n,B in data:
        lo=np.tril_indices(n);A=np.zeros((n,n));A[lo]=B@x;A.T[lo]=A[lo]
        ev=np.linalg.eigvalsh(A)
        print(name,n,'min',ev[0],'neg',sum(ev < -1e-7),flush=True)
        out.append(ev[0])
    return out

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--degree',type=int,default=14);p.add_argument('--kind',choices=['projectors','conditional'],default='projectors')
    a=p.parse_args();f='point' if a.degree==4 else 'interior';test(blocks(a.degree,a.kind),np.load(tmp/('outer3-%d-%s.npy'%(a.degree,f))))
