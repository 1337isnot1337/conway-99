"""Intersect reduced theta coordinates with their exact integrality and parity lattice."""
from collections import Counter
from fractions import Fraction as F
from math import gcd,lcm
from functools import reduce
from flint import fmpz_mat,fmpq_mat,fmpq
from pathlib import Path
import argparse,json,z3
from level_seven_exact import expr
def modulus(k):
    if k.startswith('c') and k.split('_')[1]=='0':return 2
    if k.startswith('f') and int(k.split('_')[-1]) in (0,14):return 2
    return 1

def solve(file,secs):
    with open(file+'.coordinates') as f:
        names=json.loads(next(f));rows={}
        for line in f:
            k,*a=line.split();rows[k]=[F(v) for v in a]
    assert names[-1]=='$constant' and all(k in rows for k in names[:-1])
    n=len(names)
    vectors=[]
    for k,row in rows.items():
        d=modulus(k);vectors.append([v/d for v in row])
    vectors.extend([[F(i==j) for j in range(n)] for i in range(n)])
    denom=lcm(*(v.denominator for row in vectors for v in row))
    # HNF on bounded batches handles large denominators without a large square workspace.
    H=fmpz_mat(n,n)
    for i in range(n):H[i,i]=denom
    for off in range(0,len(vectors),40):
        a=H.tolist()+[[int(denom*v) for v in row] for row in vectors[off:off+40]]
        raw=fmpz_mat(a).hnf();H=fmpz_mat(raw.tolist()[:n])
    B=H.inv()*denom
    assert all(x.q==1 for row in B.tolist() for x in row)
    if B[n-1,n-1]!=1:
        print('integral affine system impossible; constant period',B[n-1,n-1]);return
    assert all(B[n-1,i]==0 for i in range(n-1))
    # LLL preserves the column lattice. Remove a large particular translate with Babai rounding.
    Z=fmpz_mat([[int(B[j,i]) for j in range(n-1)] for i in range(n-1)]).lll()
    Z=Z.transpose()
    p=fmpz_mat([[int(B[j,n-1])] for j in range(n-1)])
    r=Z.solve(p);z=fmpz_mat([[round(F(str(row[0])))] for row in r.tolist()]);p=p-Z*z
    T=fmpz_mat([[Z[i,j] if i<n-1 and j<n-1 else (p[i,0] if i<n-1 else int(j==n-1)) for j in range(n)] for i in range(n)])
    det=abs(int(Z.det()))
    print('integer lattice in',n-1,'free coordinates; index',det,'affine congruences consistent',flush=True)
    with open(file) as f:
        next(f);next(f);m,n1,_=next(f).split();assert int(n1)==n
        U=[]
        for _ in range(int(m)):
            v=next(f).split();U.append([fmpq(x) for x in v[1:]+v[:1]])
    if 'prism' in rows:U.append([fmpq(str(-x+1386*(j==n-1))) for j,x in enumerate(rows['prism'])])
    Q=fmpq_mat(U)*T
    v=[z3.Int('v'+str(i)) for i in range(n-1)]
    s=z3.SolverFor('QF_LIA');s.set(timeout=secs*1000)
    clean=[]
    for row in Q.tolist():
        d=lcm(*(int(x.q) for x in row));a=[int(x*d) for x in row];h=reduce(gcd,a)
        if h==0:continue
        a=[x//h for x in a];clean.append(a)
        s.add(z3.Sum([c*w for c,w in zip(a,v) if c])+a[-1]>=0)
    with open(file+'.integer.json','w') as f:json.dump({'names':names,'T':[[int(x) for x in row] for row in T.tolist()],'inequalities':clean},f)
    res=s.check();print('integer inequalities',res,s.reason_unknown() if res==z3.unknown else '',flush=True)
    if res==z3.sat:
        witness=[s.model().eval(w,model_completion=True).as_long() for w in v]+[1]
        assert all(sum(x*y for x,y in zip(a,witness))>=0 for a in clean)
        x=(T*fmpz_mat([[i] for i in witness])).tolist()
        print('free integer counts',dict(zip(names,[int(v[0]) for v in x])),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('file');p.add_argument('--seconds',type=int,default=100);a=p.parse_args();solve(a.file,a.seconds)
