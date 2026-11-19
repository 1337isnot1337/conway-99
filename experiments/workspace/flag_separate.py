"""Separate finite rooted PSD constraints in the 57-variable order-nine relaxation."""
from glob import glob
from math import gcd
from functools import reduce
from pathlib import Path
import argparse,pickle,json,time
import numpy as np
from scipy.optimize import linprog
from threadpoolctl import threadpool_limits

from flag_moments import BASE,cache9


def prim(row):
    vals=[int(v) for v in row]
    d=reduce(gcd,vals,0)
    return tuple(v//d for v in vals) if d else ()


def cuts(blocks,inj,x,integer=False):
    embeds=inj@x
    result=[]
    worst=0
    for h,fs,T in blocks:
        n=len(fs)
        low=np.tril_indices(n)
        gram=np.empty((n,n))
        raw=T @ embeds
        gram[low]=raw
        gram[(low[1],low[0])]=raw
        # Positive diagonals set natural scales. At zero diagonals use a
        # modest floor from the base flag count for numerical stability.
        d=np.sqrt(np.maximum(gram.diagonal(),max(1.,1e-7*abs(gram[0,0]))))
        val,vec=np.linalg.eigh(gram/d[:,None]/d[None,:])
        worst=min(worst,val[0])
        for j in range(min(n,2)):
            if val[j]>=-1e-7:break
            w=vec[:,j]/d
            w=w/max(abs(w))
            for fac in (4,16,128,4096,1000000):
                v=np.rint(w*fac).astype(np.int64)
                if float(v@gram@v)>=-1e-4:continue
                z=v[low[0]]*v[low[1]]*(1+(low[0]!=low[1]))
                if (int(np.max(abs(z))) * int(np.max(abs(T.data))) * len(z)) < 2**62:
                    row=np.asarray(T.T@z)
                else:
                    row=np.zeros(T.shape[1],dtype=object)
                    for t in np.flatnonzero(z):
                        lo,hi=T.indptr[t:t+2]
                        ix=T.indices[lo:hi]
                        row[ix]+=int(z[t])*T.data[lo:hi].astype(object)
                inds=np.flatnonzero(row)
                coeff=sum((int(row[i])*inj[i].astype(object) for i in inds),start=np.zeros(inj.shape[1],dtype=object))
                # The cut coefficients are exact integers. Only selection of
                # the separating test vector uses a numerical eigensolver.
                key=prim(coeff)
                if key:result.append((val[j],key))
                break
    result.sort(key=lambda a:a[0])
    return worst,result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--rounds',type=int,default=15)
    p.add_argument('--store',default='flag-cuts.json')
    p.add_argument('--cache-name',default='moments-?-?-512.pickle')
    p.add_argument('--induced',action='store_true')
    args=p.parse_args()
    _,_,_,cores,_,inji,ind=cache9()
    assert np.max(abs(inji))<2**63
    inj=np.asarray(inji,dtype=np.int64)
    # Keep exact coefficients for every inequality until constructing the LP.
    forms={prim(row) for row in ind}
    forms.discard(())
    forms={row for row in forms if any(row[1:]) or row[0]<0}
    blocks=[]
    if args.induced:
        _,_,aut,_,scale,_,_=cache9()
        assert not np.any(ind % scale)
        rated=(ind//scale)*np.array(aut,dtype=object)[:,None]
        assert np.max(abs(rated))<2**63
        inj=np.asarray(rated,dtype=np.int64)
    for name in sorted(BASE.glob(('induced-' if args.induced else '')+args.cache_name)):
        with name.open('rb') as f: blocks.extend(pickle.load(f))
    out=BASE/args.store
    saved=set(tuple(r) for r in json.loads(out.read_text())) if out.exists() else set()
    forms |= saved
    print('moment blocks',len(blocks),'core variables',len(cores),'base+cut rows',len(forms),flush=True)
    for it in range(args.rounds):
        raw=np.array(list(forms),dtype=float)
        a=raw[:,1:]
        norms=np.maximum(np.max(abs(a),axis=1),1)
        A=a/norms[:,None]
        b=raw[:,0]/norms
        # Maximize the distance from normalized affine bounding planes.
        goal=np.zeros(len(cores)+1);goal[-1]=-1
        sol=linprog(goal,A_ub=np.column_stack((-A,np.ones(len(b)))),b_ub=b,bounds=[(0,None)]*len(cores)+[(None,None)],method='highs')
        if not sol.success:
            print('LP status',sol.message,'requires independent exact audit',flush=True);return
        x=np.r_[1,sol.x[:-1]]
        worst,found=cuts(blocks,inj,x)
        fresh={row for _,row in found if row not in forms}
        print('iteration',it,'normalized LP margin',sol.x[-1],'worst scaled eigenvalue',worst,'new cuts',len(fresh),flush=True)
        if sol.x[-1]<-1e-5:
            print('infeasibility candidate; exact certificate required',flush=True);return
        if not fresh:
            np.save(BASE/'flag-point.npy',x)
            print('numerical feasible candidate',flush=True);return
        forms |= fresh; saved |= fresh
        tmp=out.with_suffix('.new')
        tmp.write_text(json.dumps(sorted(saved))+'\n');tmp.replace(out)


if __name__=='__main__':
    with threadpool_limits(limits=1):main()
