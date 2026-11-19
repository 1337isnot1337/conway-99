"""Three exterior vertices with all points of a distinguished maximal coclique retained."""
import argparse
from itertools import permutations,product
from math import comb
import numpy as np
import scipy.sparse as sp
from scipy.optimize import linprog

from triple_moments import tmp


def build(h,maximum=False,degree=14,freq=None):
    k=degree;v=1+k*k//2;m=v-h;maxsize=min(k//2,h)
    sizes=[d for d in range(1,maxsize+1) if freq is None or freq[d-1]>0];I=[];J=[];V=[];rhs=[]
    def row(terms,target=0):
        i=len(rhs);rhs.append(target)
        for j,c in terms:
            if c:I.append(i);J.append(j);V.append(c)
    singles={d:i for i,d in enumerate(sizes)}
    count=len(singles);pairs={};allpairs={}
    for d,f in product(sizes,repeat=2):
        if freq is not None and d==f and freq[d-1]<2:continue
        for u in range(max(0,d+f-h),min(d,f,2)+1):
            for e in range(2):
                if u+e>2 or (e and (d==k//2 or f==k//2) and u!=1):continue
                if maximum and d+f-u<2 and not e:continue
                key=(min(d,f),max(d,f),u,e)
                if key not in pairs:pairs[key]=count;count+=1
                allpairs[d,f,u,e]=pairs[key]
    row([(singles[d],1) for d in sizes],m)
    row([(singles[d],d) for d in sizes],h*k)
    row([(singles[d],comb(d,2)) for d in sizes],h*(h-1))
    def equations(base,target,events):
        # events is a list of (variable, vector of per-extension statistics).
        for j,c in enumerate(target):row([(i,ex[j]) for i,ex in events]+[(base,-c)])
    for d in sizes:
        if freq is not None:row([(singles[d],1)],freq[d-1])
        c=h-d
        tar=[m-1,d*(k-1),c*k,comb(d,2),2*d*c,2*comb(c,2),k-d,d,2*c]
        ev=[]
        for (a,b,u,e),j in allpairs.items():
            if a==d:
                t=b-u;ev.append((j,[1,u,t,comb(u,2),u*t,comb(t,2),e,e*u,e*t]))
        equations(singles[d],tar,ev)
        if freq is not None:
            for g in sizes:row([(j,1) for (a,bb,u,e),j in allpairs.items() if a==d and bb==g]+[(singles[d],-freq[g-1]+int(g==d))])
    perms=list(permutations(range(3)));triples={}
    # The ordered isomorphism type is encoded by the three sizes and three encoded pair relations.
    def triple(ds,ab,ac,bc,w):
        nonlocal count
        links=((0,ab,ac),(ab,0,bc),(ac,bc,0))
        key=min((ds[i],ds[j],ds[l],links[i][j],links[i][l],links[j][l],w) for i,j,l in perms)
        if key not in triples:triples[key]=count;count+=1
        return triples[key]
    for (d,f,u,e),base in allpairs.items():
        if d>f:continue # swapped identities are equivalent after permuting the cell labels
        # Cell order: outside both blocks, first only, second only, both.
        a=(h-d-f+u,d-u,f-u,u)
        cellpairs=[(i,j) for i in range(4) for j in range(i,4) if (a[i]>=2 if i==j else a[i]*a[j]>0)]
        tar=[m-2,k-d-e,k-f-e,2-u-e]
        for i,aa in enumerate(a):
            p=i&1;q=i>>1
            tar.extend([aa*(k-p-q),aa*(2-p-e*q),aa*(2-q-e*p)])
        for i,j in cellpairs:
            remaining=2-((i&j)&1)-((i&j)>>1)
            tar.append((comb(a[i],2) if i==j else a[i]*a[j])*remaining)
        ev=[];by_size={g:[] for g in sizes}
        for g in sizes:
            if freq is not None and freq[g-1]<=int(g==d)+int(g==f):continue
            for y in range(min(2,d,g)+1):
                for z in range(min(2,f,g)+1):
                    for w in range(min(u,y,z,1)+1):
                        b=(g-y-z+w,y-w,z-w,w)
                        if any(t<0 or t>aa for t,aa in zip(b,a)):continue
                        for p,q in product(range(2),repeat=2):
                            if (d,g,y,p) not in allpairs or (f,g,z,q) not in allpairs:continue
                            if max(u+e+p*q,y+p+e*q,z+q+e*p)>2:continue
                            if w and ((p and q) or (p and e) or (q and e)):continue
                            if maximum and not(e or p or q) and h-a[0]+b[0]<3:continue
                            val=[1,p,q,p*q]
                            for t in b:val.extend([t,t*p,t*q])
                            for i,j in cellpairs:val.append(comb(b[i],2) if i==j else b[i]*b[j])
                            v_id=triple((d,f,g),2*u+e,2*y+p,2*z+q,w)
                            ev.append((v_id,val));by_size[g].append(v_id)
        equations(base,tar,ev)
        if freq is not None:
            for g,ids in by_size.items():row([(i,1) for i in ids]+[(base,-freq[g-1]+int(g==d)+int(g==f))])
    A=sp.csr_matrix((np.array(V,dtype=np.int64),(I,J)),shape=(len(rhs),count));A.eliminate_zeros()
    return A,np.array(rhs),singles,pairs,triples


def run(h,maximum,seconds):
    A,b,s,p,t=build(h,maximum)
    lower=np.zeros(A.shape[1]);upper=np.full(A.shape[1],np.inf)
    if not maximum:lower[s[7]]=1
    res=linprog(np.zeros(len(lower)),A_eq=A,b_eq=b,bounds=np.stack([lower,upper],axis=1),method='highs',options={'time_limit':seconds})
    print(h,'maximum' if maximum else 'contains transversal',A.shape,len(p),len(t),res.message,flush=True)
    if res.x is not None:print('block frequencies',np.round(res.x[:len(s)],3),'max error',max(abs(A@res.x-b)),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--h',type=int,default=14);p.add_argument('--maximal-only',action='store_true');p.add_argument('--seconds',type=int,default=45);a=p.parse_args();run(a.h,not a.maximal_only,a.seconds)
