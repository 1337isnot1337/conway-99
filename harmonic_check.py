"""Check harmonic and elliptic transformations on explicit positive definite lattices."""
from fractions import Fraction as F
from math import isqrt
from harmonic_theta import basis,gegen
from level_seven_check import independent,mul,power

def run(n=28):
    th,e4,e47,_=independent(n)
    # Six binary factors and four E8 factors; keep one binary factor explicit.
    r=30;otherL=mul(power(th,5),mul(e4,power(e47,3)))
    otherK=mul(power(th,5),mul(power(e4,3),e47))
    B=[[{} for i in range(n+1)] for _ in range(2)]
    # g in the dual binary factor of H, corresponding to the first basis vector
    # in the 7-scaled dual K. Its squared norm before scaling is 4/7.
    for side in (0,1):
        for x in range(-2*isqrt(n)-2,2*isqrt(n)+3):
            for y in range(-2*isqrt(n)-2,2*isqrt(n)+3):
                j=x*x+x*y+2*y*y if side==0 else 2*x*x-x*y+y*y
                if j>n:continue
                t=x if side==0 else 4*x-y
                for i in range(j,n+1):
                    bb=B[side][i];bb[t]=bb.get(t,0)+(otherK if side else otherL)[i-j]
        d=1 if side else 7
        for i,dist in enumerate(B[side]):
            for t,val in dist.items():
                k=min(t%4,(-t)%4);j=i-d*((t*t-k*k)//8)
                assert val==B[side][j].get(k,0)
    for h in (0,2,4,6,8,10,12,14):
        Y=[]
        for side in (0,1):
            out=[]
            for i,dist in enumerate(B[side]):
                p=gegen(h,i*(14 if side else 2),F(4,7))
                out.append(sum(c*sum(t**(2*k)*v for t,v in dist.items()) for k,c in enumerate(p)))
            Y.append(out)
        b=basis(h,n);d=len(b)-1;x=[];res=Y[0].copy()
        for j,col in enumerate(b):
            c=res[j];x.append(c);res=[a-v*c for a,v in zip(res,col)]
        assert not any(res)
        for i in range(n+1):
            assert Y[1][i]==sum((-1)**(h//2)*F(7)**(r//2-11+d-2*j+h//2)*x[j]*b[d-j][i] for j in range(d+1)),(h,i)
    print('exact harmonic transforms through degree 14, both elliptic recurrences and order',n)
if __name__=='__main__':run()
