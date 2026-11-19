"""Condition the full one-root edge and three-vertex marginal equations on a certified independent pattern."""
import argparse,json
from collections import Counter,deque
from itertools import combinations
from functools import reduce
from math import gcd
import numpy as np
import scipy.sparse as sp
from scipy.optimize import linprog
import pynauty
from triple_moments import tmp


def construct(L,axes):
    nsign=2*axes
    labels=np.array([p for p in combinations(range(nsign),2) if p[0]^1!=p[1]],dtype=int)
    n=len(labels);li={tuple(p):i for i,p in enumerate(labels)};special=[li[tuple(sorted((2*a,2*b)))] for a,b in L]
    graph=pynauty.Graph(axes,adjacency_dict={i:[b if a==i else a for a,b in L if i in (a,b)] for i in range(axes)})
    generators,size,ex,*_=pynauty.autgrp(graph);group=[tuple(range(axes))];seen=set(group)
    for a in group:
        for p in generators:
            u=tuple(p[v] for v in a)
            if u not in seen:seen.add(u);group.append(u)
    assert len(group)==round(size*10**ex)
    def pidx(a,b):
        v=np.maximum(a,b);return v*(v-1)//2+np.minimum(a,b)
    def tidx(a,b,c):return a+b*(b-1)//2+c*(c-1)*(c-2)//6
    ed=np.array(sorted(combinations(range(n),2),key=lambda p:pidx(*p)))
    tr=np.array(sorted(combinations(range(n),3),key=lambda p:tidx(*p)))
    a,b,c=tr.T
    emin=np.arange(len(ed));tmin=np.arange(len(tr));wmin=np.arange(3*len(tr)).reshape(-1,3)
    for g in group[1:]:
        signed=np.array([2*g[j//2]+j%2 for j in range(nsign)])
        move=np.array([li[tuple(sorted(p))] for p in signed[labels]])
        emin=np.minimum(emin,pidx(*move[ed].T))
        target=move[tr];ordered=np.sort(target,axis=1);t=tidx(*ordered.T)
        sortedpos=(target[:,:,None]>target[:,None,:]).sum(axis=2)
        tmin=np.minimum(tmin,t);wmin=np.minimum(wmin,3*t[:,None]+sortedpos)
    def compress(values,offset):
        _,rep,ix,sz=np.unique(values.ravel(),return_inverse=True,return_counts=True,return_index=True)
        return (ix+offset).reshape(values.shape),sz,rep
    xmap,sx,ex=compress(emin,1);qmap,sq,eq=compress(wmin,1+len(sx));tmap,st,et=compress(tmin,1+len(sx)+len(sq))
    sizes=np.r_[1,sx,sq,st];D=len(sizes)
    X=np.zeros((n,n),int);X[ed[:,0],ed[:,1]]=X[ed[:,1],ed[:,0]]=xmap
    Q=np.zeros((n,n,n),np.int32)
    for i,j,k in [(0,1,2),(1,2,0),(2,0,1)]:
        aa,bb,cc=tr[:,i],tr[:,j],tr[:,k]
        Q[aa,bb,cc]=Q[aa,cc,bb]=qmap[:,i];Q[aa,bb,bb]=X[aa,bb]
    for i,j in ed:Q[i,j,j]=Q[j,i,i]=X[i,j]
    eqs=set();ineq=set()
    def row(terms,equality=True):
        d=Counter()
        for a,b in terms:d[int(a)]+=int(b)
        r=tuple(sorted((a,b) for a,b in d.items() if b))
        if not r:return
        common=reduce(gcd,[v for _,v in r],0);sign=-1 if equality and r[0][1]<0 else 1
        (eqs if equality else ineq).add(tuple((a,sign*b//common) for a,b in r))
    for i,j in combinations(special,2):row([(X[i,j],1)])
    for i,label in enumerate(labels):
        for a in range(nsign):
            d=2-int(a in label)-int(a^1 in label);N=[u for u in np.flatnonzero(np.any(labels==a,axis=1)) if u!=i]
            row([(X[i,u],1) for u in N]+[(0,-d)])
            for j in range(n):
                if i!=j:row([(Q[i,j,u],1) for u in N]+[(X[i,j],-d)])
    for pos in ex:
        i,j=ed[pos];u=len(set(labels[i])&set(labels[j]));others=[v for v in range(n) if v not in (i,j)]
        ti=tmap[[tidx(*sorted((i,j,v))) for v in others]]
        row([(Q[v,i,j],1) for v in others]+[(X[i,j],1),(0,u-2)])
        row([(v,1) for v in ti]+[(X[i,j],u-1)])
    for idx in et:
        i,j,k=tr[idx];x=[X[i,j],X[i,k],X[j,k]];q=[Q[i,j,k],Q[j,i,k],Q[k,i,j]];t=tmap[idx]
        forms={0:0,1:x[0],2:x[1],4:x[2],3:q[0],5:q[1],6:q[2],7:t}
        for mask in range(8):
            row([(col,(-1)**((s^mask).bit_count())) for s,col in forms.items() if s&mask==mask],False)
    def sparse(group):
        ii=[];jj=[];vv=[]
        for i,r in enumerate(group):
            for j,v in r:ii.append(i);jj.append(j);vv.append(v)
        return sp.csr_matrix((np.array(vv,np.int64),(ii,jj)),shape=(len(group),D))
    return sparse(eqs),sparse(ineq),sizes,(X,Q,tmap,tr,labels)


def rootcontrol():
    E,G,s,(X,Q,T,tr,labels)=construct([(0,1)],2)
    # With two axes, the outside induces a four-cycle with edges joining labels that share an anchor.
    e=np.array([[int(i!=j and len(set(a)&set(b))==1) for j,b in enumerate(labels)] for i,a in enumerate(labels)])
    x=np.zeros(len(s));x[0]=1
    for i,j in combinations(range(4),2):x[X[i,j]]+=e[i,j]
    for n,(i,j,k) in enumerate(tr):
        for a,b,c in ((i,j,k),(j,k,i),(k,i,j)):x[Q[a,b,c]]+=e[a,b]*e[a,c]
        x[T[n]]+=e[i,j]*e[i,k]*e[j,k]
    y=x/s;assert np.max(abs(E@y))<1e-8 and np.min(G@y)>-1e-8
    print('rook conditional marginal control passed',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--case',type=int,default=0);p.add_argument('--control',action='store_true');a=p.parse_args()
    if a.control:rootcontrol()
    else:
        c=json.loads((tmp/'hemisphere-cases.json').read_text());E,G,s,_=construct(c[a.case][0],7)
        print('case',a.case,'equations',E.shape,'inequalities',G.shape,flush=True)
        prefix=tmp/('hemi-marginal-%d'%a.case)
        sp.save_npz(str(prefix)+'-eq.npz',E);sp.save_npz(str(prefix)+'-ge.npz',G);np.save(str(prefix)+'-size.npy',s)
