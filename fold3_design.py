"""Orbit profiles in an auxiliary order-three symmetry of the actual order-three quotient.

The auxiliary action fixes its six triangle nodes and permutes the 27 remaining
nodes freely. It is imposed only on the quotient, not on the sought signed lift.
"""
from itertools import combinations
from pathlib import Path
import json
import pynauty

def designs():
    allrows=[sum(1<<j for j in c) for c in combinations(range(9),4)]
    chosen=[15,51]  # the first two rows share positions 0 and 1
    cand=[r for r in allrows if all((r&q).bit_count()==2 for q in chosen)]
    best={}
    def visit(selected,opts):
        if len(selected)==6:
            adj={i:[6+j for j in range(9) if r>>j&1] for i,r in enumerate(selected)}
            G=pynauty.Graph(15,adjacency_dict=adj,vertex_coloring=[set(range(6)),set(range(6,15))])
            key=pynauty.certificate(G)
            best.setdefault(key,selected)
            return
        for t,r in enumerate(opts):
            after=[x for x in opts[t+1:] if (x&r).bit_count()==2]
            if len(after)+len(selected)+1>=6:
                visit(selected+[r],after)
    visit(chosen,cand)
    return list(best.values())

def row_options(H,i):
    # For each column i the six equations H R = 6 J - 3 H specify
    # six sums on quartets of the nine unknown entries.
    import numpy as np
    from flint import fmpq_mat
    from itertools import product
    mat=np.array([[(r>>j)&1 for j in range(9)] for r in H],dtype=int)
    col=mat[:,i]
    h=int(col.sum())
    a=np.vstack((mat,np.ones((1,9),dtype=int)))
    rhs=np.r_[6-3*col,14-h]
    red,rank=fmpq_mat(np.column_stack((a,rhs)).tolist()).rref()
    piv=[]
    for r in range(rank):
        first=next(j for j in range(10) if red[r,j])
        if first==9:return []
        piv.append(first)
    free=[j for j in range(9) if j not in piv]
    # Each entry is a sum over three orbit nodes, each of valency at most two.
    result=[]
    for xs in product(range(7),repeat=len(free)):
        v=[0]*9
        for j,x in zip(free,xs):v[j]=x
        for r,j in enumerate(piv):
            x=red[r,9]-sum(red[r,u]*v[u] for u in free)
            if x.q!=1 or x<0 or x>6:break
            v[j]=int(x)
        else:
            if v[i] in (0,2,4) and sum(x*x for x in v)+v[i]==30-3*h:
                result.append(v)
    return result

def fold(H):
    opts=[row_options(H,i) for i in range(9)]
    col=[sum(((r>>i)&1)<<j for j,r in enumerate(H)) for i in range(9)]
    order=sorted(range(9),key=lambda i:len(opts[i]))
    chosen={}
    def rec(t):
        if t==9:
            return [[chosen[i] for i in range(9)]]
        i=order[t]
        out=[]
        for v in opts[i]:
            if any(v[j]!=w[i] or sum(a*b for a,b in zip(v,w))+v[j]!=18-3*(col[i]&col[j]).bit_count() for j,w in chosen.items()):continue
            chosen[i]=v;out.extend(rec(t+1));del chosen[i]
        return out
    return rec(0),[len(x) for x in opts]

if __name__=='__main__':
    ds=designs()
    print('designs',len(ds),flush=True)
    solutions=[]
    for H in ds:
        rows,counts=fold(H)
        print(H,'options',counts,'quotients',len(rows),flush=True)
        solutions.extend({'H':H,'R':R} for R in rows)
    Path(__file__).with_name('fold3-designs.json').write_text(json.dumps(solutions)+'\n')
