"""Exact bit-sliced elimination over the seven-element field. Column zero is one."""
import argparse
import numpy as np
import scipy.sparse as sp
from triple_moments import tmp


def scale(x,a):
    if a in (3,5,6):
        u=x[0]|x[1]|x[2];x=(u^x[0],u^x[1],u^x[2]);a=7-a
    if a==2:return x[2],x[0],x[1]
    if a==4:return x[1],x[2],x[0]
    return x


def add(x,y):
    a,b,c=x;d,e,f=y
    h=a^d;p=a&d;i=b^e;q=(b&e)|(p&i);j=c^f;r=(c&f)|(q&j)
    a=h^r;b=(i^p)^(h&r);c=(j^q)^((i^p)&h&r)
    z=a&b&c
    return a^z,b^z,c^z


def solve(A,verbose=False):
    A=A.copy().tocsr();A.sum_duplicates()
    piv={}
    order=np.argsort(np.diff(A.indptr),kind='stable')
    for step,i in enumerate(order):
        a,b=A.indptr[i:i+2];d=A.data[a:b]%7;ix=A.indices[a:b]
        row=tuple(sum(1<<int(j) for j in ix[d&(1<<s)!=0]) for s in range(3))
        while True:
            h=max(v.bit_length() for v in row)-1
            if h<0:break
            if h==0:return None
            coef=sum(1<<j for j,v in enumerate(row) if v.bit_length()==h+1)
            if h not in piv:
                piv[h]=scale(row,pow(coef,-1,7));break
            row=add(row,scale(piv[h],7-coef))
        if verbose and step%20000==19999:print('rows',step+1,'pivots',len(piv),flush=True)
    w=[1,0,0]
    for j,row in sorted(piv.items()):
        z=-sum((1<<(t+s))*(a&b).bit_count() for t,a in enumerate(row) for s,b in enumerate(w))%7
        for t in range(3):
            if z>>t&1:w[t]|=1<<j
    x=np.zeros(A.shape[1],dtype=np.int64)
    for s,z in enumerate(w):
        bits=np.frombuffer(z.to_bytes((len(x)+7)//8,'little'),dtype=np.uint8)
        x+=np.unpackbits(bits,bitorder='little')[:len(x)].astype(np.int64)<<s
    assert x[0]==1 and not np.any((A@x)%7)
    return len(piv),x


def test():
    from flint import nmod_mat
    rng=np.random.default_rng(123)
    for _ in range(120):
        a=rng.integers(-13,14,(50,int(rng.integers(25,75))))
        if rng.integers(2):a[:,0]=(a[:,1:]@rng.integers(0,7,size=a.shape[1]-1))%7
        expected=nmod_mat(a.tolist(),7).rank()==nmod_mat(a[:,1:].tolist(),7).rank()
        out=solve(sp.csr_matrix(a))
        assert expected==(out is not None)
    print('120 finite field controls passed',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--test',action='store_true');p.add_argument('--global-system',action='store_true');a=p.parse_args()
    if a.test:test()
    elif a.global_system:
        from global_lift import system
        A=system(4,0,prime=7);sp.save_npz(tmp/'global-field7.npz',A)
        out=solve(A,True);print('modulo seven rank',out[0] if out else 'inconsistent',flush=True)
        if out:np.save(tmp/'global-field7-witness.npy',out[1])
