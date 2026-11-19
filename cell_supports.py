"""Check integral projected row and Gram conditions for a specified root support."""
import argparse
from itertools import combinations, product
from functools import lru_cache
import networkx as nx
from ortools.sat.python import cp_model

cells=list(combinations(range(7),2))
def touch(e,f):return len(set(e)&set(f))

def profiles(F,f):
    inc=[[k for k,e in enumerate(F) if h in e] for h in range(7)]
    bounds=[]
    for e in F:
        t=touch(e,f)
        if t==2:bounds.append((0,2))
        elif t==1:bounds.append((-2,0) if f in F else (0,0))
        else:bounds.append((-3,1))
    def rec(b):
        while True:
            changed=False
            for ring in inc:
                low=sum(b[k][0] for k in ring);hi=sum(b[k][1] for k in ring)
                if low>0 or hi<0:return
                for k in ring:
                    a,c=b[k];z=(max(a,c-hi),min(c,a-low))
                    if z!=b[k]:
                        b[k]=z;changed=True
            if not changed:break
        ids=[k for k,(a,c) in enumerate(b) if a!=c]
        if not ids:
            yield tuple(a for a,_ in b);return
        k=min(ids,key=lambda k:b[k][1]-b[k][0])
        for v in range(b[k][0],b[k][1]+1):
            row=b.copy();row[k]=(v,v);yield from rec(row)
    return sorted(set(rec(bounds)))

def mask_cases(n):
    for idx,G in enumerate(nx.graph_atlas_g()):
        if len(G)!=7 or G.number_of_edges()!=n:continue
        F=[e for e in cells if G.has_edge(*e)]
        def rank(G):return 7-sum(nx.is_bipartite(G.subgraph(c)) for c in nx.connected_components(G))
        r=rank(G)
        if all(rank(nx.restricted_view(G,[],[e]))==r for e in F):yield idx,F

def internal():
    near=[{0,2},{0,3},{1,2},{1,3}]
    pairs=list(combinations(range(4),2))
    for x in product(range(2),repeat=6):
        if sum(x)>2:continue
        adj=[set() for _ in range(9)]
        for p,q in [(8,h) for h in range(4)]+[(0,1),(2,3)]+[(u+4,h) for u,s in enumerate(near) for h in s]+[(u+4,v+4) for (u,v),b in zip(pairs,x) if b]:
            adj[p].add(q);adj[q].add(p)
        if all(len(adj[p]&adj[q])<=2-int(q in adj[p]) for p,q in combinations(range(9),2)):
            yield tuple(4-len(t) for t in adj[4:8]),x

def solve(F,sec,extended):
    model=cp_model.CpModel();l=len(F);D={f:profiles(F,f) for f in cells}
    active=[f for f in cells if len(D[f])>1 or any(D[f][0])]
    if any(max(t[k] for t in D[f])==0 for k,f in enumerate(F)):
        return len(active),max(map(len,D.values())),'ZERO DIAGONAL',0
    x={}; indicators={};mom={}
    for f in active:
        d=D[f];i=cells.index(f)
        for u in range(4):
            y=[model.new_bool_var('') for t in d]
            model.add_exactly_one(y);indicators[f,u]=y
            for k in range(l):
                v=[t[k] for t in d]
                if len(set(v))==1:x[f,u,k]=v[0]
                else:
                    x[f,u,k]=model.new_int_var(min(v),max(v),'');model.add(x[f,u,k]==sum(a*b for a,b in zip(v,y) if a))
        for k in range(l):
            for j in range(k,l):
                m=[t[k]*t[j] for t in d]
                if any(m):
                    mom[f,k,j]=sum(a*b for u in range(4) for a,b in zip(m,indicators[f,u]) if a)
        if f in F:
            k=F.index(f);var=[x[f,u,k] for u in range(4)]
            model.add_allowed_assignments(var,list(set(t for t,b in internal())))
        else:
            for k in range(l):model.add(sum(x[f,u,k] for u in range(4))==0)
    for k,j in combinations(range(l),2):
        model.add(sum(x[F[k],u,j] for u in range(4))==sum(x[F[j],u,k] for u in range(4)))
    for k in range(l):
        for j in range(k,l):
            model.add(sum(mom.get((f,k,j),0) for f in active)==7*sum(x[F[k],u,j] for u in range(4)))
    def bit(u,pos):return (u>>(1-pos))&1
    for h in range(7):
        for k in range(l):
            for b in range(2):model.add(sum(x[f,u,k] for f in active if h in f for u in range(4) if bit(u,f.index(h))==b)==0)
    if extended:
        vertices=[(f,u) for f in active for u in range(4)]
        def anchors(v):return {(h,bit(v[1],s)) for s,h in enumerate(v[0])}
        E={}
        for p,(f,u) in enumerate(vertices):
            for q in range(p):
                g,v=vertices[q];t=touch(f,g)
                if t==2 and f not in F:flag=int((u^v) in (1,2))
                elif t==1 and (f not in F or g not in F):flag=0
                else:flag=model.new_bool_var('')
                E[p,q]=E[q,p]=flag
            E[p,p]=0
        omitted=[f for f in cells if f not in active]
        for p,(f,u) in enumerate(vertices):
            for g in active:
                n=sum(E[p,q] for q,w in enumerate(vertices) if g==w[0]);t=touch(f,g)
                model.add(n==(2 if t==2 else 1-t)-(x[f,u,F.index(g)] if g in F else 0))
            for h,b in product(range(7),range(2)):
                cap=1 if h in f else 2
                known=sum(E[p,q] for q,w in enumerate(vertices) if (h,b) in anchors(w))
                extra=sum(h in g and not touch(f,g) for g in omitted)
                model.add(known<=cap);model.add(known>=cap-extra)
        def mul(e,v,lo,hi):
            if isinstance(e,int):return e*v
            if isinstance(v,int):return v*e
            a=model.new_int_var(min(lo,0),max(hi,0),'')
            model.add(a==v).only_enforce_if(e);model.add(a==0).only_enforce_if(e.Not());return a
        for p,(f,u) in enumerate(vertices):
            for k in range(l):
                model.add(sum(mul(E[p,q],x[g,v,k],-3,2) for q,(g,v) in enumerate(vertices))==-4*x[f,u,k])
        residual={}
        for p,q in combinations(range(len(vertices)),2):
            f,u=vertices[p];g,v=vertices[q];cap=2-len(anchors(vertices[p])&anchors(vertices[q]))
            extra=0 if f==g else sum(not touch(f,z) and not touch(g,z) for z in omitted)
            rem=model.new_int_var(0,min(cap,extra),'') if extra else 0
            residual[p,q]=residual[q,p]=rem
            model.add(sum(mul(E[p,r],E[q,r],0,1) for r in range(len(vertices)))+E[p,q]+rem==cap)
        for p,(f,u) in enumerate(vertices):
            for g in active:
                if f!=g:
                    extra=sum(not touch(f,z) and not touch(g,z) for z in omitted)
                    model.add(sum(residual[p,q] for q,(h,v) in enumerate(vertices) if h==g)==extra)
    solver=cp_model.CpSolver();solver.parameters.max_time_in_seconds=sec;solver.parameters.num_workers=1
    result=solver.solve(model)
    return len(active),max(map(len,D.values())),solver.status_name(result),solver.num_branches

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('n',type=int);p.add_argument('--time',type=float,default=15);p.add_argument('--extended',action='store_true');p.add_argument('--case',type=int);args=p.parse_args()
    for idx,F in mask_cases(args.n):
        if args.case is not None and idx!=args.case:continue
        print(idx,F,solve(F,args.time,args.extended),flush=True)
