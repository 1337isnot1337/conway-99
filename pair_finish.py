"""Test the remaining graph after specifying two vertex neighborhoods and their incidence with the exterior."""
import argparse
from itertools import combinations
import numpy as np
import scipy.sparse as sp
from scipy.optimize import linprog
from ortools.sat.python import cp_model
from pair_cover import tmp,validate


def equations(B,N):
    assert validate(B,N)
    k=len(B)//2;n=N.shape[1];need=2-(B+np.eye(len(B),dtype=int))@N
    need=np.vstack([need,k-N.sum(axis=0)])
    alln=np.vstack([N,np.ones(n,dtype=int)])
    common=N.T@N
    available=[];rr=[];cc=[]
    for i,j in combinations(range(n),2):
        if common[i,j]>1 or np.any(alln[:,j]>need[:,i]) or np.any(alln[:,i]>need[:,j]):continue
        v=len(available);available.append((i,j))
        for x,y in ((i,j),(j,i)):
            u=np.flatnonzero(alln[:,y]);rr.extend((x*(len(B)+1)+u).tolist());cc.extend([v]*len(u))
    E=sp.csr_matrix((np.ones(len(cc),dtype=int),(rr,cc)),shape=(need.size,len(available)))
    return available,E,need.T.ravel().astype(int)


def finish(B,N,seconds=60):
    pairs,E,rhs=equations(B,N);n=N.shape[1]
    rowlen=np.diff(E.indptr);impossible=np.flatnonzero((rhs<0)|(rowlen<rhs))
    print('external edge candidates',len(pairs),'immediate deficient rows',len(impossible),flush=True)
    if len(impossible):return 'inconsistent row',None
    opt=linprog(np.zeros(E.shape[1]),A_eq=E,b_eq=rhs,bounds=(0,1),method='highs',options={'time_limit':seconds})
    print('edge incidence LP',opt.message,flush=True)
    if opt.status==2:return 'LP infeasible',None
    model=cp_model.CpModel();xs=[model.new_bool_var('') for _ in pairs]
    for i in range(E.shape[0]):
        if rowlen[i]:model.add(sum(xs[j] for j in E.indices[E.indptr[i]:E.indptr[i+1]])==int(rhs[i]))
    edge={e:x for e,x in zip(pairs,xs)}
    def ev(i,j):return edge.get((min(i,j),max(i,j)))
    common=N.T@N
    for i,j in combinations(range(n),2):
        terms=[]
        for l in range(n):
            a=ev(i,l);b=ev(j,l)
            if a is None or b is None:continue
            z=model.new_bool_var('');model.add_multiplication_equality(z,[a,b]);terms.append(z)
        e=ev(i,j)
        if e is not None:terms.append(e)
        model.add(sum(terms)==2-int(common[i,j]))
    solver=cp_model.CpSolver();solver.parameters.max_time_in_seconds=seconds;solver.parameters.num_workers=2
    status=solver.solve(model)
    if status not in (cp_model.OPTIMAL,cp_model.FEASIBLE):return solver.status_name(status),None
    H=np.zeros((n,n),np.int16)
    for (i,j),x in zip(pairs,xs):H[i,j]=H[j,i]=solver.value(x)
    G=np.block([[B,N],[N.T,H]])
    assert np.all(G.sum(0)==len(B)//2) and np.all(G@G+G==(len(B)//2-2)*np.eye(len(G),dtype=int)+2)
    return 'verified graph',G


def control():
    from triangle_ball import golay
    G,_,_=golay();a=0;b=next(i for i in range(1,len(G)) if not G[a,i])
    idx=[a,b,*np.flatnonzero(G[a]+G[b])];rest=sorted(set(range(len(G)))-set(idx))
    B=G[np.ix_(idx,idx)];N=G[np.ix_(idx,rest)];H=G[np.ix_(rest,rest)]
    pairs,E,r=equations(B,N);x=np.array([H[i,j] for i,j in pairs])
    assert x.sum()*2==H.sum() and np.array_equal(E@x,r)
    print('Golay exterior edges',int(x.sum()),'all recovered and checked in linear incidence system',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--control',action='store_true');p.add_argument('--seed',type=int,default=1);p.add_argument('--seconds',type=int,default=45);a=p.parse_args()
    if a.control:control()
    else:
        d=np.load(tmp/('pair-cover-%d.npz'%a.seed));status,G=finish(d['B'],d['N'],a.seconds);print(status,flush=True)
        if G is not None:np.save('verified-conway-99.npy',G)
