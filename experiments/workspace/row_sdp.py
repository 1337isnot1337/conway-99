"""Feasibility of the root-edge second moments including the exact row-profile hull."""
from pathlib import Path
import argparse
import numpy as np
import scipy.sparse as sp
import scs
from outer_moments import OrbitModel,dense


def solve(k,maxiters):
    model=OrbitModel(k)
    eq,ineq=model.constraints()
    blocks=model.moment_blocks()
    d=model.dim
    if k==14:
        data=np.load(Path(__file__).with_name('row-profiles.npz'))
        H=data['H'];columns=data['columns'];den=data['den']
    else:
        H=np.empty((0,0));columns=[];den=[]
    h=len(H)
    def pad(A):
        return sp.hstack([sp.csr_matrix(A),sp.csr_matrix((A.shape[0],h))],format='csr')
    eq0=pad(dense(eq,d)); rows=[eq0]; rhs=[np.zeros(eq0.shape[0])]
    rows.append(sp.csr_matrix(([1],([0],[0])),shape=(1,d+h)));rhs.append([1])
    if h:
        Y=sp.csr_matrix((np.array(den,dtype=float),(np.arange(len(den)),columns)),shape=(len(den),d))
        rows.append(sp.hstack([Y,-sp.csr_matrix(H.T,dtype=float)]));rhs.append(np.zeros(len(den)))
        rows.append(sp.csr_matrix((np.ones(h),(np.zeros(h),np.arange(d,d+h))),shape=(1,d+h)));rhs.append([1])
    z=sum(a.shape[0] for a in rows)
    inequalities=-pad(dense(ineq,d));rows.extend([inequalities,-sp.eye(d+h)]);rhs.extend([np.zeros(inequalities.shape[0]),np.zeros(d+h)])
    l=inequalities.shape[0]+d+h
    for _,n,T in blocks:
        j,i=np.triu_indices(n)
        pos=i*(i+1)//2+j
        weight=np.sqrt((1+(i!=j))/np.asarray(T.sum(axis=1)).ravel()[pos])
        rows.append(-pad(sp.diags(weight)@T[pos]));rhs.append(np.zeros(len(i)))
    A=sp.vstack(rows,format='csc'); b=np.concatenate(rhs)
    c=np.zeros(d+h)
    print('SDP variables',len(c),'constraints',A.shape,'cone',z,l,[n for _,n,_ in blocks],flush=True)
    out=scs.solve(dict(A=A,b=b,c=c),dict(z=z,l=l,s=[n for _,n,_ in blocks]),max_iters=maxiters,eps_abs=2e-7,eps_rel=2e-7,verbose=False)
    print('status',out['info'],flush=True)
    x=out['x']
    if np.all(np.isfinite(x)):
        residual=A@x-b
        print('direct residuals: linear equations',abs(residual[:z]).max(),'inequality violation',max(0,residual[z:z+l].max()),flush=True)
        for mark,n,T in blocks:
            lo=np.tril_indices(n); M=np.zeros((n,n))
            M[lo]=(T@x[:d])/np.sqrt(np.asarray(T.sum(axis=1)).ravel())
            M.T[lo]=M[lo]
            print('block',int(mark),'minimum eigenvalue',float(np.linalg.eigvalsh(M)[0]),flush=True)
    np.savez_compressed('row-sdp-%d.npz'%k,x=x,y=out['y'],s=out['s'])


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--degree',type=int,default=14);p.add_argument('--iters',type=int,default=2400)
    args=p.parse_args();solve(args.degree,args.iters)
