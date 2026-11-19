"""Check triangle-star shells with positive Gram bounds and exact-square determinants."""
import argparse,math
from itertools import islice
from pathlib import Path
import numpy as np
from flint import fmpz_mat,nmod_mat
from triple_moments import tmp

def modular_dets(batch,p):
    A=batch.copy()%p;det=np.ones(len(A),dtype=np.int64);inv=np.array([0]+[pow(i,-1,p) for i in range(1,p)],dtype=np.int64)
    allrows=np.arange(len(A))
    for i in range(A.shape[1]):
        j=i+(A[:,i:,i]!=0).argmax(axis=1);x=A[allrows,j,:].copy()
        A[allrows,j,:]=A[:,i,:];A[:,i,:]=x
        pivot=A[:,i,i];det=(det*pivot*(1-2*(j!=i)))%p
        v=A[:,i+1:,i]*inv[pivot,None]%p
        A[:,i+1:,i+1:]=(A[:,i+1:,i+1:]-v[:,:,None]*A[:,None,i,i+1:])%p
    return det

def check(seed,trial,limit,suffix):
    fn=tmp/('triangle-star-%d-%d'%(seed,trial));D=np.load(fn.with_suffix('.npz'));B=D['B'];center=D['x'][3:];T=B[3:,3:]
    with fn.with_suffix('.in').open() as f:
        next(f);next(f);rows=np.array(sorted(map(int,f.readlines())),dtype=np.int64)
    A=((rows[:,None]>>np.arange(36))&1).astype(np.int64)
    Q=A@(np.eye(36,dtype=int)+T)+center
    F=27*np.eye(36,dtype=int)-9*T+1;C=1-9*A;L=C@np.linalg.inv(F)
    assert np.linalg.matrix_rank(F)==36
    primes=(5,7,11,13,17,19,23,29,31,37,41,43,47,53,59,61,67,71,73,79,83,89,97,101)
    mods=[];full_d=int(fmpz_mat(F.tolist()).det())
    for p in primes:
        if full_d%p==0:continue
        J=np.array(nmod_mat(F.tolist(),p).inv().tolist(),dtype=np.int64)
        mods.append((p,(C@J)%p,np.array([i in {x*x%p for x in range(p)} for i in range(p)])))
    num=local=positive=tested=square=0;best=-1000
    fname=fn.with_suffix(suffix)
    with fname.open() as f:
        while num<limit:
            data=list(islice(f,min(600,limit-num)))
            if not data:break
            masks=np.fromstring(''.join(data),dtype=np.int64,sep=' ').reshape(-1,8);num+=len(masks)
            ix=np.searchsorted(rows,masks)
            ov=A[ix]@center;assert np.all(np.sort(ov,axis=1)==np.array([0,0,1,1,1,1,1,1]))
            zero=np.argsort(ov,axis=1)[:,:2];idx=np.arange(len(ix))
            u,v=(ix[idx,zero[:,j]] for j in range(2))
            ok=np.all((Q[u]+A[v]<=2)&(Q[v]+A[u]<=2),axis=1)
            ix=ix[ok];zero=zero[ok];local+=len(ix)
            if not len(ix):continue
            idx=np.arange(len(ix));Y=np.broadcast_to(27*np.eye(8,dtype=int)+1,(len(ix),8,8)).copy()
            Y[idx,zero[:,0],zero[:,1]]-=9;Y[idx,zero[:,1],zero[:,0]]-=9
            E=Y-L[ix]@C[ix].transpose(0,2,1)
            ev=np.linalg.eigvalsh(E)[:,0];best=max(best,float(ev.max()));ok=ev>=-1e-7
            Y=Y[ok];ix=ix[ok];positive+=len(ix)
            for p,Lp,good in mods:
                if not len(ix):break
                M=Y-Lp[ix]@C[ix].transpose(0,2,1)
                d=(full_d%p)*modular_dets(M,p)%p;ok=good[d]
                ix=ix[ok];Y=Y[ok]
            for i,y in zip(ix,Y):
                tested+=1;D44=np.block([[F,C[i].T],[C[i],y]])
                det=int(fmpz_mat(D44.tolist()).det())
                if det>=0 and math.isqrt(det)**2==det:
                    square+=1;np.savez_compressed(tmp/('triangle-star-square-%d-%d-%d.npz'%(seed,trial,square)),B=B,x=center,stars=A[i],Y=y)
    print('covers',num,'all local caps',local,'positive negative-eigenvalue Gram',positive,'best minimum eigenvalue',best,'exact determinants',tested,'squares',square,flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--seed',type=int,default=0);p.add_argument('--trial',type=int,default=1);p.add_argument('--limit',type=int,default=100000);p.add_argument('--suffix',default='.covers');a=p.parse_args();check(a.seed,a.trial,a.limit,a.suffix)
