"""Search for square shells satisfying interlacing and common-neighbor bounds."""
import argparse
from math import isqrt
import numpy as np
from flint import fmpz_mat
from square_ball import square_ball


def search(cross,steps,seed):
    rng=np.random.default_rng(seed)
    pairs=[(i,j) for i in range(4) for j in range(i)]
    record=1e4;good=0
    visited=set()
    for run in range(steps//5000+1):
        A=square_ball(cross,rng)
        def blocks():
            return [np.argwhere(A[8+i*10:18+i*10,8+j*10:18+j*10])+[8+i*10,8+j*10] for i,j in pairs]
        edge=blocks()
        def cost():
            excess=np.maximum(0,np.triu(A@A+A,1)-2).sum()
            B=A[4:,4:]
            g=np.linalg.eigvalsh(3*np.eye(44)-B+1/9)
            h=np.linalg.eigvalsh(4*np.eye(44)+B-2/11)
            spectral=sum(np.minimum(g,0)**2)+sum(np.minimum(h,0)**2)
            return excess*.22+spectral
        curr=cost()
        for step in range(min(5000,steps-run*5000)):
            z=int(rng.integers(len(edge)))
            U=edge[z]
            s,t=rng.choice(len(U),2,replace=False)
            a,b=U[s];c,d=U[t]
            if a==c or b==d or A[a,d] or A[c,b]:continue
            A[a,b]=A[b,a]=A[c,d]=A[d,c]=0;A[a,d]=A[d,a]=A[c,b]=A[b,c]=1
            val=cost()
            temp=.065*(1-step/5000)**2+.001
            if val<=curr or rng.random()<np.exp(min(0,(curr-val)/temp)):
                U[s,1]=d;U[t,1]=b;curr=val
                if curr<record:
                    record=curr
                    np.save('square-%d%d-optimized.npy'%cross,A)
                if curr<1e-16:
                    B=A[4:,4:]
                    det=int(fmpz_mat((27*np.eye(44,dtype=int)-9*B+1).tolist()).det())
                    if det not in visited:
                        visited.add(det);good+=1
                        ok=det>=0 and isqrt(det)**2==det
                        print('admissible shell',cross,run,step,'determinant square',ok,'zero',det==0,flush=True)
                        if ok:np.save('square-%d%d-square-%d.npy'%(*cross,good),A)
            else:
                A[a,b]=A[b,a]=A[c,d]=A[d,c]=1;A[a,d]=A[d,a]=A[c,b]=A[b,c]=0
        if run%4==0:print('run',run,'best',record,'distinct admissible determinants',good,flush=True)
    return record,good


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--cross',default='00');p.add_argument('--steps',type=int,default=50000);p.add_argument('--seed',type=int,default=81289)
    a=p.parse_args();print(search(tuple(map(int,a.cross)),a.steps,a.seed))
