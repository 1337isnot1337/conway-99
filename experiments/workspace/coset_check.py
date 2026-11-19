"""Independent gluing controls from an index-three copy of E8 and determinant-seven binary factors."""
from nine_cosets import auxiliary,blocks,basis
from level_seven_check import independent,mul,power
from fractions import Fraction as F
from itertools import product

def check(n=23):
    th,e4,e47,_=independent(n)
    source=auxiliary('control',n)
    for s in (0,1,2,3,4):
        # Remaining 36 dimensions: two binary factors and four E8 factors.
        # The doubled binary condition uses the seven-dual isometry.
        K=mul(power(th,2),mul(power(e4,4-s),power(e47,s)))
        H=mul(power(th,2),mul(power(e4,s),power(e47,4-s)))
        r=8+2+8*(4-s)
        for kind in ('root','prim','16a','16b','d16'):
            T=auxiliary(kind,n);dim=sum(map(len,blocks(kind)))
            L=[0]*(n+1);D=[0]*(n+1)
            for j in range(5):
                for x,c in source[j].items():
                    for y,b in T[j].items():
                        k,z=divmod(x+y,9);assert not z
                        if k<=n:D[k]+=c*b*(1+(j!=0))
                        if 7*k<=n:L[7*k]+=c*b*(1+(j!=0))
            L=mul(L,H);D=mul(D,K)
            b=basis(dim//2,n);d=len(b)-1;coords=[];res=L.copy()
            for j,col in enumerate(b):
                v=res[j];coords.append(v);res=[a-c*v for a,c in zip(res,col)]
            assert not any(res)
            for i in range(n+1):
                assert D[i]==sum(F(7)**(r//2-11+dim//4+d-2*j)*coords[j]*b[d-j][i] for j in range(d+1)),(s,kind,i)
    print('five discriminants by five auxiliary lattices: all 25 glued forms match at both cusps through order',n,flush=True)
if __name__=='__main__':check()
