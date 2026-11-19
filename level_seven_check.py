"""Independent eta-product and Fricke-transform checks, including a known lattice family."""
from fractions import Fraction as F
from itertools import combinations
from math import comb,isqrt
from pathlib import Path
import json
from level_seven_theta import series_basis

def mul(a,b):
    n=len(a)
    return [sum(a[j]*b[i-j] for j in range(i+1)) for i in range(n)]
def power(a,k):
    out=[1]+[0]*(len(a)-1)
    for _ in range(k):out=mul(out,a)
    return out

def independent(n):
    th=[0]*(n+1)
    for y in range(-isqrt(4*n//7),isqrt(4*n//7)+1):
        for z in range(-isqrt(4*n-7*y*y),isqrt(4*n-7*y*y)+1):
            if (y-z)%2==0:th[(7*y*y+z*z)//4]+=1
    e4=[1]+[240*sum(d**3 for d in range(1,i+1) if i%d==0) for i in range(1,n+1)]
    e47=[e4[i//7] if i%7==0 else 0 for i in range(n+1)]
    basis=[]
    for j in range(15):
        q=th.copy()
        for t,exp in ((1,49-4*j),(7,4*j-7)):
            for k in range(t,n+1,t):
                v=[0]*(n+1)
                for i in range(n//k+1):
                    v[k*i]=(-1)**i*(comb(exp,i) if i<=exp else 0) if exp>=0 else comb(i-exp-1,i)
                q=mul(q,v)
        basis.append([0]*j+q[:n+1-j])
    return th,e4,e47,basis

def test(n=28):
    th,e4,e47,basis=independent(n)
    assert basis==series_basis(n).T.tolist()
    for s in range(5):
        L=mul(power(th,6),mul(power(e4,4-s),power(e47,s)))
        K=mul(power(th,6),mul(power(e4,s),power(e47,4-s)))
        r=6+8*s
        residue=L.copy();coords=[]
        for j,b in enumerate(basis):
            x=residue[j];coords.append(x);residue=[a-x*c for a,c in zip(residue,b)]
        assert not any(residue)
        for i in range(n+1):
            assert K[i]==sum(F(7)**(3+r//2-2*j)*coords[j]*basis[14-j][i] for j in range(15))
    print('direct eta expansions and five rank-44 positive controls through Fourier order',n)
    # Use ambient common-neighbor closure on all triples of one biplane side.
    blocks=[{(s+j)%7 for j in (2,4,5,6)} for s in range(7)]
    adj=[{7+i for i,b in enumerate(blocks) if x in b} for x in range(7)]+blocks
    for triple in combinations(range(7),3):
        seen=set(triple)
        while True:
            add=set().union(*(adj[x]&adj[y] for x,y in combinations(seen,2) if x//7==y//7))
            if add<=seen:break
            seen|=add
        assert len(seen)==14
    print('all 35 Fano-complement triples generate the oriented core')
    base={2:462,3:24948,4:1386}
    for path in sorted(Path('.').glob('level-seven-certificate-*.json')):
        data=json.loads(path.read_text());r=data['rank'];rows=[F(0)]*15;rhs=F(0)
        floors=dict(base)
        if data.get('sparse'):
            from sparse_theta import lower
            floors=lower()
        for tag,w in data['weights'].items():
            w=F(w);assert w>=0
            if tag in ('mass_L','mass_L_rev','mass_K','mass_K_rev'):
                side=tag[5];i=0;val=1;sign=-1 if tag.endswith('rev') else 1
            elif tag.startswith(('zero_L','bound_L')):
                side='L';i=int(tag.split('L')[1]);val=data['limits'].get(str(i),0);sign=-1
            elif tag[0] in 'KL' and tag[1:].isdigit():
                side=tag[0];i=int(tag[1:]);val=floors.get(i,0) if side=='K' else 0;sign=1
            else:raise ValueError(tag)
            for j in range(15):rows[j]+=w*sign*(basis[j][i] if side=='L' else F(7)**(3+r//2-2*j)*basis[14-j][i])
            rhs+=w*sign*val
        assert not any(rows) and rhs==1
        print(path,'independently verified')
if __name__=='__main__':test()
