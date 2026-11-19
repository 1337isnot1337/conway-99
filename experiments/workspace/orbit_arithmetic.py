"""Integral moment counts for a single root, including exact parity checks."""
import argparse
from math import factorial,comb
from pathlib import Path
import numpy as np
import scipy.sparse as sp
from triple_moments import Triples,pack,tmp


def orbit_sizes(t):
    sizes=np.zeros(t.d,dtype=np.int64)
    m=t.model;sizes[0]=1
    for j,mark in enumerate(t.marks):
        multiplicity=np.count_nonzero(t.type==j)
        pt=t.pairs[j];cnt=np.bincount(pt);n=len(cnt)
        i=np.arange(m.m,dtype=np.int32)
        diag=pt[pack(i,i)]
        mark_row=pt[pack(np.int32(mark),i)]
        constant_row=pt[pack(np.int32(0),i)]
        ok=np.ones(n,dtype=bool)
        ok[diag]=False;ok[mark_row]=False;ok[constant_row]=False
        amounts=cnt*multiplicity
        if mark:
            sizes[t.value(0,0,mark)]=multiplicity
            ids=t.table[j][ok];np.add.at(sizes,ids,amounts[ok])
        else:np.add.at(sizes,t.table[0][ok],amounts[ok])
    levels=np.array([len(set((int(a),int(b),int(c)))-{0}) for a,b,c in t.reps])
    # The retained representative generally has no zero for degree three.
    sizes[levels==3]//=3
    group=2**(m.k//2)*factorial(m.k//2)
    assert np.all(sizes>0) and np.all(group%sizes==0)
    assert [sizes[levels==s].sum() for s in range(4)]==[comb(m.m-1,s) for s in range(4)]
    return sizes,group


def integral(E,sizes,group):
    A=E.astype(np.int64).copy()
    A.data*=group//sizes[A.indices]
    g=np.gcd.reduceat(abs(A.data),A.indptr[:-1])
    A.data//=np.repeat(g,np.diff(A.indptr))
    return A


def parity(A):
    rows=[(0,np.array([0],dtype=np.int32))]
    for i in range(A.shape[0]):
        start,end=A.indptr[i:i+2]
        z=A.indices[start:end][A.data[start:end]%2!=0]
        if len(z):rows.append((i+1,z))
    # Column zero is the normalization z_empty=1. Treat it as the augmented bit.
    pivots={};n=A.shape[1]
    for i,indices in sorted(rows[1:],key=lambda row:len(row[1])):
        value=sum(1<<int(j) for j in indices)
        while value>1:
            col=value.bit_length()-1
            if col not in pivots:
                pivots[col]=value;break
            value^=pivots[col]
        if value==1:return False,len(pivots),i
    return True,len(pivots),None


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--degree',type=int,default=14);args=p.parse_args()
    t=Triples(args.degree);sizes,group=orbit_sizes(t)
    E=sp.load_npz(tmp/('outer3-%d-eq.npz'%args.degree))
    A=integral(E,sizes,group);print('group',group,'orbit sizes',np.unique(sizes).tolist(),flush=True)
    print('mod 2 consistent, rank, first failure',parity(A),flush=True)
    sp.save_npz(tmp/('outer3-%d-integral.npz'%args.degree),A)
    np.save(tmp/('outer3-%d-sizes.npy'%args.degree),sizes)
