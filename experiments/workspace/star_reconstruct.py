"""Read a 99-graph cut, run the star extender, and independently check any full answer."""
import argparse,subprocess
import numpy as np
from triple_moments import tmp
from root_search import verify


def solve(B,N,forbidden,tag,budget,cap,seed,k):
    b=len(B);c=N.shape[1];n=b+c
    A=np.block([[B,N],[N.T,-forbidden.astype(np.int16)]])
    inp=tmp/('star-'+tag+'.in');out=tmp/('star-'+tag+'.out')
    with inp.open('w') as f:
        print(n,k,b,file=f);np.savetxt(f,A,fmt='%d')
    if out.exists():out.unlink()
    subprocess.run([str(tmp/'star_reconstruct'),str(inp),str(out),str(budget),str(cap),str(seed)],check=True)
    if out.exists():
        G=np.loadtxt(out,dtype=np.int16)
        verify([sum(1<<int(j) for j in np.flatnonzero(row)) for row in G],k)
        if k==14:np.save('verified-conway-99.npy',G)
        return True
    return False


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--control',action='store_true');p.add_argument('--seed',type=int,default=1);p.add_argument('--rows',type=int,default=7);p.add_argument('--budget',type=int,default=500);p.add_argument('--cap',type=int,default=14);a=p.parse_args()
    if a.control:
        from itertools import combinations
        G=np.array([[int(i!=j and (i//3==j//3 or i%3==j%3)) for j in range(9)] for i in range(9)],np.int16)
        idx=[0,*np.flatnonzero(G[0])];rest=sorted(set(range(9))-set(idx))
        assert solve(G[np.ix_(idx,idx)],G[np.ix_(idx,rest)],np.zeros((4,4),bool),'rook',1000,100,1,4)
    else:
        tag='%d-%d'%(a.seed,a.rows);z=np.load(tmp/('hemi-'+tag+'.npz'));B,N,rest,I=[z[j] for j in ('B','N','rest','I')]
        excluded=np.isin(rest,I);ban=excluded[:,None]&excluded[None,:]
        solve(B,N,ban,tag,a.budget,a.cap,a.seed,14)
