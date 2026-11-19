"""Couple both sets of nine lattice translates by gluing to index-three auxiliary lattices."""
import argparse,json
from collections import defaultdict
from functools import cache
from fractions import Fraction as F
from math import isqrt
from pathlib import Path
import z3
from harmonic_theta import basis,expr
from sparse_theta import lower

def blocks(kind):
    # v has squared length eight. Each block is D_d^+ in dimension divisible by eight.
    short=[1,1,0,0,0,0,0,0];four=[2,0,0,0,0,0,0,0];six=[2,1,1,0,0,0,0,0]
    vs={'control':[[3,1,0,0,0,0,0,0]],'root':[[2,2,0,0,0,0,0,0]],'prim':[[2,1,1,1,1,0,0,0]],
        '16a':[short,six],'16b':[four,four],'24a':[short,short,four],
        '32a':[short]*4,'d16':[[1]*8+[0]*8],'d24':[[1]*8+[0]*16]}
    return vs[kind]

@cache
def auxiliary(kind,n):
    vs=blocks(kind);cap=72*n;lim=isqrt(cap)
    allcosets=[]
    for j in range(5):
        acc={(0,0):1}
        for v in vs:
            block=defaultdict(int)
            for parity in (0,1):
                dp={(0,0,0):1}
                for c in v:
                    choices=defaultdict(int)
                    for x in range((-lim-2*j*c)//3-1,(lim-2*j*c)//3+2):
                        k=(3*x+2*j*c)**2
                        if x%2==parity and k<=cap:choices[k,x%4,(x*c)%6]+=1
                    nxt=defaultdict(int)
                    for (k,a,b),z in dp.items():
                        for (kk,aa,bb),zz in choices.items():
                            if k+kk<=cap:nxt[k+kk,(a+aa)%4,(b+bb)%6]+=z*zz
                    dp=nxt
                for (k,a,b),z in dp.items():
                    if a==0:block[k,b]+=z
            nxt=defaultdict(int)
            for (k,b),z in acc.items():
                for (kk,bb),zz in block.items():
                    if k+kk<=cap:nxt[k+kk,(b+bb)%6]+=z*zz
            acc=nxt
        q={}
        for (k,b),z in acc.items():
            if b==0:
                assert k%8==0 and k//8%9==(5 if kind=='control' else 4)*j*j%9
                q[k//8]=z
        allcosets.append(q)
    return allcosets

def coset_floor(dual,j):
    if dual:return [0,14,11,18,17][j]
    return [0,89,77,99,110][j]
def solve(r,n,kinds,flags,seconds,reduce,save,pairs,moments,point_degree,line_degree):
    s=z3.SolverFor('QF_LRA')
    if seconds:s.set(timeout=seconds*1000)
    C={}
    def entry(dual,j,d):
        j=min(j%9,(-j)%9)
        if d<0 or d%9!=(5 if dual else 8)*j*j%9:return 0
        if d==0:return int(j==0)
        if d<coset_floor(dual,j) or (not dual and j==0 and d<63):return 0
        key=(dual,j,d)
        if key not in C:
            c=z3.Real('c%d_%d_%d'%key);s.add(c>=0);C[key]=c
        return C[key]
    def form(tag,dim,left,right,h=0,raw=0):
        weight=22+dim//2+2*h;b=basis(dim//2+2*h,max(n,2*(weight//3),7*12 if r==42 else 0));d=len(b)-1
        v=z3.Reals(' '.join('%sv%d'%(tag,j) for j in range(len(b))))
        for i in range(n+1):
            s.add(expr([bb[i] for bb in b],v)==left[i])
            s.add(expr([(-1)**h*F(7)**(r//2-11+dim//4+d-2*j+raw)*b[d-j][i] for j in range(d+1)],v)==right[i])
            if r==42 and i<=12:s.add(expr([bb[7*i] for bb in b],v)==7**(h-raw)*right[i])
    scalar=[]
    for dual in (0,1):
        scalar.append([entry(dual,0,9*i)+2*entry(dual,3,9*i) for i in range(n+1)])
    form('base',0,*scalar)
    # These three low-norm shells consist of integral coordinates in H.
    s.add(scalar[0][7]<=990,scalar[0][8]<=148995,scalar[1][1]<=88)
    for i,k in lower().items():
        if i<=n:s.add(scalar[1][i]>=k)
    s.add(entry(1,1,14)>=99,entry(0,1,98)>=99)
    from coset_floors import counts
    for (j,d),k in counts(9*n).items():s.add(entry(1,j,d)>=k)
    for kind in kinds:
        Q=auxiliary(kind,n);dim=sum(map(len,blocks(kind)))
        for h in range(moments+1):
            hp=[F(1)]
            for l in range(h):
                hp.append(-hp[-1]*F((h-l)*(2*(h-l)+dim-2),(l+1)*(2*l+44)))
            @cache
            def axial(x,y):
                return z3.RealVal(str(sum(v*x**l*y**(h-l) for l,v in enumerate(hp))))
            V=[]
            for dual in (0,1):
                a=1 if dual else 7
                V.append([sum((1+(j!=0))*mult*axial(9*i-a*k,a*k)*entry(dual,j,9*i-a*k) for j,qs in enumerate(Q) for k,mult in qs.items() if a*k<=9*i) for i in range(n+1)])
            form(kind+'h'+str(h),dim,*V,h)
    for j in range(5):
        for d in range(1,9*n//7+1):
            left=entry(0,j,7*d);right=entry(1,j,d)
            s.add(left==right if r==42 else left>=right)
            s.add(entry(1,7*j,7*d)>=entry(0,j,d))
    harmonic={}
    if flags:
        sparse={(i,t):(a,b) for i,t,a,b in json.loads(Path('sparse-theta-flags.json').read_text())}
        prism=z3.Real('prism');s.add(prism>=0)
        for dual in (0,1):
            coeff=1 if dual else 7;scale=7 if dual else 1
            Fg={}
            def flag(d,t):
                t0=min(t%28,(-t)%28)
                dd=d-coeff*((t*t-t0*t0)//56)
                if dd<0:return 0
                if dd==0:return 99 if t0==0 else 0
                c=entry(dual,t0,dd)
                if isinstance(c,int) and c==0:return 0
                if (dd,t0) not in Fg:
                    z=z3.Real('f%d_%d_%d'%(dual,dd,t0));s.add(z>=0);Fg[dd,t0]=z
                return Fg[dd,t0]
            for j in range(5):
                for d in range((5 if dual else 8)*j*j%9,9*n+1,9):
                    cnt=entry(dual,j,d);lim=isqrt(8*scale*d)
                    tlist=[t for t in range(-lim,lim+1) if t%9==j]
                    vals=[flag(d,t) for t in tlist]
                    from local_energy import minimum
                    for t,v in zip(tlist,vals):
                        if minimum(t,9,18*9*n*scale)>18*d*scale:s.add(v==0)
                    s.add(sum(vals)==99*cnt,sum(t*v for t,v in zip(tlist,vals))==0,sum(t*t*v for t,v in zip(tlist,vals))==18*d*scale*cnt)
                    if point_degree:
                        from harmonic_theta import gegen
                        for h in range(4,point_degree+1,2):
                            polynomial=gegen(h,8*scale*d,1)
                            cs=[sum(b*t**(2*k) for k,b in enumerate(polynomial)) for t in tlist]
                            harmonic[dual,j,d,h]=sum(z3.RealVal(str(b))*v for b,v in zip(cs,vals) if b)
                    if j==0 and ((not dual and d in (63,72,81,90)) or (dual and d==9)):
                        for t,v in zip(tlist,vals):
                            if abs(t)>9:s.add(v==0)
            if pairs:
                from coset_pair_flags import add_pairs
                add_pairs(s,entry,flag,dual,n,pairs)
            if dual:
                # Signed doubling cancels the distinction between ± one-third for the aggregate.
                for (i,t),(a,b) in sparse.items():
                    if i<=n:
                        total=sum(flag(9*i,u) for u in ({3*t,-3*t} if t else {0}))
                        s.add(total>=a+b*prism)
    if point_degree:
        for h in range(4,point_degree+1,2):
            for kind in ['base']+kinds:
                dim=0 if kind=='base' else sum(map(len,blocks(kind)))
                Q=[{0:1},{},{},{0:1},{}] if kind=='base' else auxiliary(kind,n)
                V=[]
                for dual in (0,1):
                    a=1 if dual else 7
                    V.append([sum((1+(j!=0))*mult*harmonic.get((dual,j,9*i-a*k,h),0) for j,qs in enumerate(Q) for k,mult in qs.items() if a*k<=9*i) for i in range(n+1)])
                form('point'+kind+'D'+str(h),dim,*V,h//2,h//2)
    if line_degree>=0:
        from line_cosets import line_flags
        from harmonic_theta import gegen
        ln={}
        for side in (0,1):
            tab=line_flags(s,side,n,entry,r);scale=7 if side else 1
            for (j,d,t),v in tab.items():
                for h in range(4,line_degree+1,2):
                    coef=gegen(h,F(8*scale*d,7),1)
                    value=sum(x*t**(2*k) for k,x in enumerate(coef))
                    ln.setdefault((side,j,d,h),[]).append(z3.RealVal(str(value))*v)
        sums={k:sum(vals) for k,vals in ln.items()}
        for h in range(4,line_degree+1,2):
            for kind in ['base']+kinds:
                dim=0 if kind=='base' else sum(map(len,blocks(kind)))
                Q=[{0:1},{},{},{0:1},{}] if kind=='base' else auxiliary(kind,n)
                V=[]
                for side in (0,1):
                    a=1 if side else 7
                    V.append([sum((1+(j!=0))*mult*sums.get((side,j,9*i-a*k,h),0) for j,qs in enumerate(Q) for k,mult in qs.items() if a*k<=9*i) for i in range(n+1)])
                form('line'+kind+'D'+str(h),dim,*V,h//2,h//2)
    print('built',r,n,kinds,'flags',flags,'shells',len(C),flush=True)
    if reduce or save:
        from theta_linear import reduce_solver
        ans=reduce_solver(s,seconds,save)
    else:ans=s.check()
    print('rank',r,'nine cosets',ans,flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--r',type=int,nargs='+',default=[34]);p.add_argument('--order',type=int,default=17);p.add_argument('--aux',nargs='*',default=['prim','root','16a','16b']);p.add_argument('--flags',action='store_true');p.add_argument('--seconds',type=int,default=0);p.add_argument('--reduce',action='store_true');p.add_argument('--save');p.add_argument('--point-degree',type=int,default=0);p.add_argument('--line-degree',type=int,default=-1);p.add_argument('--moments',type=int,default=0);p.add_argument('--pairs',nargs='*',default=[]);a=p.parse_args()
    for r in a.r:solve(r,a.order,a.aux,a.flags,a.seconds,a.reduce,a.save,a.pairs,a.moments,a.point_degree,a.line_degree)
