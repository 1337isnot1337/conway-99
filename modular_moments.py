"""Check integral orbit equations after nonnegative zero propagation over F2 and F3."""
from pathlib import Path
import argparse
import numpy as np
import scipy.sparse as sp
from relax_outer3 import setup
from orbit_arithmetic import parity


def ternary(A):
    polys=[];weights=np.diff(A.indptr)
    for i in np.argsort(weights):
        a,b=A.indptr[i:i+2];d=A.data[a:b]%3;j=A.indices[a:b]
        x=sum(1<<int(k) for k in j[d==1]);y=sum(1<<int(k) for k in j[d==2])
        if x or y:polys.append((x,y))
    pivots={}
    for x,y in polys:
        while (x|y)>1:
            p=max(x.bit_length(),y.bit_length())-1
            live=pivots.get(p)
            top_one=x.bit_length()==p+1
            if live is None:
                pivots[p]=(x,y) if top_one else (y,x)
                break
            v,u=live if top_one else live[::-1]
            z=~(x|y);w=~(u|v)
            x,y=(x&w)|(z&u)|(y&v),(y&w)|(z&v)|(x&u)
        else:
            if x|y:return False,len(pivots)
    # Free entries are zero; the constant is one. This verifies the whole result with an explicit point.
    ones=1;twos=0
    for p,(a,b) in sorted(pivots.items()):
        s=((ones&a).bit_count()+(twos&b).bit_count()-(ones&b).bit_count()-(twos&a).bit_count())%3
        if s==1:twos|=1<<p
        if s==2:ones|=1<<p
    result=np.fromiter((((ones>>i)&1)+2*((twos>>i)&1) for i in range(A.shape[1])),dtype=np.int64)
    assert result[0]==1 and np.all((A@result)%3==0)
    np.save('/tmp/conway99-tools/outer3-14-mod3-witness.npy',result)
    return True,len(pivots)


if __name__=='__main__':
    import os
    t=Path('/tmp/conway99-tools');_,_,alive=setup()
    E=sp.load_npz(t/'outer3-14-integral.npz')[:,alive].tocsr()
    E=E[np.diff(E.indptr)>0];g=np.gcd.reduceat(abs(E.data),E.indptr[:-1])
    E.data//=np.repeat(g,np.diff(E.indptr))
    print('post-propagation',E.shape,'modulo two',parity(E),flush=True)
    print('modulo three',ternary(E),flush=True)
