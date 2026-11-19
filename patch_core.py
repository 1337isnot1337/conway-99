"""Exact necessary core constraints after completing every star of a nine-vertex patch."""
import argparse,json
from itertools import combinations
import numpy as np
from ortools.sat.python import cp_model
from patch_layers import patch,tmp

def solve(B,S,n=99,k=14,actual=None,sec=10):
    m=len(B);nr=len(S)
    incidence=np.array([[(s>>h)&1 for h in range(m)] for s in S],dtype=int).reshape((-1,m))
    ns=k-B.sum(axis=0)-incidence.sum(axis=0)
    nz=int(n-m-nr-ns.sum())
    assert nz>=0 and min(ns)>=0
    nh=nr+nz;I=np.vstack((incidence,np.zeros((nz,m),int)))
    model=cp_model.CpModel();E={}
    def fixed(a):return isinstance(a,(int,np.integer))
    def and_(a,b):
        if fixed(a):return b if a else 0
        if fixed(b):return a if b else 0
        t=model.new_bool_var('');model.add(t<=a);model.add(t<=b);model.add(t>=a+b-1);return t
    for i in range(nh):
        E[i,i]=0
        for j in range(i):
            cap=int(2-I[i]@I[j])
            if actual is not None:edge=int(actual[i,j])
            elif cap==0:edge=0
            else:edge=model.new_bool_var('')
            E[i,j]=E[j,i]=edge
    b={};B2={}
    for i in range(nh):
        for h in range(m):
            cap=int(2-I[i,h]-I[i]@B[:,h])
            b[i,h]=model.new_int_var(0,min(cap,int(ns[h])),'')
            model.add(b[i,h]+sum(E[i,j] for j in range(nr) if I[j,h])==cap)
            B2[i,h]=model.new_bool_var('')
            model.add(b[i,h]==2).only_enforce_if(B2[i,h])
            model.add(b[i,h]<=1).only_enforce_if(B2[i,h].Not())
        model.add(sum(b[i,h] for h in range(m))+sum(E[i,j] for j in range(nh))==k-int(I[i].sum()))
    if actual is None:
        for i in range(nr,nh-1):
            model.add(sum((1<<j)*E[i,j] for j in range(nr))<=sum((1<<j)*E[i+1,j] for j in range(nr)))
    for i,j in combinations(range(nh),2):
        cap=int(2-I[i]@I[j])
        model.add(sum(and_(E[i,l],E[j,l]) for l in range(nh))+E[i,j]<=cap)
    M={}
    for h in range(m):
        for g in range(m):
            M[h,g]=int(ns[h])*(2-int(h==g)-int(B[h,g]))-sum(b[i,h] for i in range(nr) if I[i,g])
            model.add(M[h,g]>=0)
        edges=model.new_int_var(0,int(ns[h])//2,'');model.add(M[h,h]==2*edges)
        model.add(sum(B2[i,h] for i in range(nh))+edges<=int(ns[h])*(int(ns[h])-1)//2)
        model.add(sum(M[h,g] for g in range(m))+sum(b[i,h] for i in range(nh))==(k-1)*int(ns[h]))
    for h,g in combinations(range(m),2):model.add(M[h,g]==M[g,h])
    solver=cp_model.CpSolver();solver.parameters.max_time_in_seconds=sec;solver.parameters.num_workers=1
    res=solver.solve(model)
    return len(S),nz,solver.status_name(res),solver.num_branches

def control():
    from triangle_ball import golay
    G=golay()[0]
    for vertices in (list(range(9)),[0,1,2,3,4,5,9,27,81]):
        B=G[np.ix_(vertices,vertices)];H=G[:,vertices];outside=[x for x in range(len(G)) if x not in vertices]
        masks={x:sum(int(v)<<h for h,v in enumerate(H[x])) for x in outside}
        large=[x for x in outside if masks[x].bit_count()>=2];empty=[x for x in outside if not masks[x]]
        U=large+empty
        out=solve(B,[masks[x] for x in large],len(G),int(G[0].sum()),actual=G[np.ix_(U,U)])
        assert out[2]=='OPTIMAL';print('Golay control',out,flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('kinds',nargs='*',type=int);p.add_argument('--time',type=float,default=15);p.add_argument('--control',action='store_true');a=p.parse_args()
    if a.control:control()
    for k in a.kinds:
        B=patch(k)
        for i,S in enumerate(json.loads((tmp/('patch-layers-%d.json'%k)).read_text())):
            print(k,i,solve(B,S,sec=a.time),flush=True)
