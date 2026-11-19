"""Joint signed coordinates of a vertex and a triangle across all nine lattice translates."""
from itertools import product,combinations_with_replacement
from functools import cache
from math import isqrt
import z3

@cache
def residue(g,t,u):
    c=3*g;det=28*36-c*c
    v=3*u
    a=(36*t-c*v)//det;b=(28*v-c*t)//det
    x=t-28*a-c*b;y=v-c*a-36*b
    def norm(x,y):return 36*x*x+28*y*y-2*c*x*y
    low,tx,vy=closest(g,x,y)
    delta,rem=divmod(norm(t,v)-low,2*det);assert rem==0 and vy%3==0
    return norm(t,v),det,delta,tx,vy//3
@cache
def closest(g,t,y):
    c=3*g;best=None
    for a,b in product(range(-1,3),repeat=2):
        x=t-28*a-c*b;v=y-c*a-36*b
        q=36*x*x+28*v*v-2*c*x*v;x,v=min((x,v),(-x,-v))
        prop=(q,x,v)
        if best is None or prop<best:best=prop
    return best

def add(s,side,n,rank,entry,point,line,triangles=True):
    scale=7 if side else 1;coef=1 if side else 7
    lookup={};tri_vars={};alltri={}
    from coset_triple_flags import reduction
    for j in range(5):
        for d in range((5 if side else 8)*j*j%9,9*n+1,9):
            lim=isqrt(8*scale*d);ts=[t for t in range(-lim,lim+1) if t%9==j]
            l=isqrt(8*scale*d//7);us=[u for u in range(-l,l+1) if u%3==j%3]
            vals={}
            for t,u,g in product(ts,us,(4,-2,1)):
                q,det,delta,x,y=residue(g,t,u);dd=d-coef*delta
                if q*coef>2*det*d or dd<0:v=0
                elif dd==0:v={4:693,-2:8316,1:13860}[g] if x==y==0 else 0
                elif isinstance(entry(side,x,dd),int):v=0
                else:
                    ds=side
                    if rank==42 and not side and dd%7==0:dd//=7;ds=1
                    key=ds,dd,g,x,y
                    if key not in lookup:
                        v=z3.Real('m'+'_'.join(map(str,key)));lookup[key]=v;s.add(v>=0)
                    v=lookup[key]
                vals[t,u,g]=v
            for t in ts:
                f=point(d,t)
                for g,num,w in [(4,7,1),(-2,84,-6),(1,140,5)]:
                    s.add(sum(vals[t,u,g] for u in us)==num*f,sum(u*vals[t,u,g] for u in us)==w*t*f)
                s.add(sum(u*u*vals[t,u,g] for u in us for g in (4,-2,1))==6*d*scale*f)
            for u in us:
                f=line[j,d,u]
                for g,num,w in [(4,3,3),(-2,36,-18),(1,60,15)]:
                    s.add(sum(vals[t,u,g] for t in ts)==num*f,sum(t*vals[t,u,g] for t in ts)==w*u*f)
                s.add(sum(t*t*vals[t,u,g] for t in ts for g in (4,-2,1))==18*d*scale*f)
            if not triangles:continue
            hist={}
            # Use ordered triangles; the same variable represents each permutation of a mark triple.
            for tri in combinations_with_replacement(ts,3):
                u=sum(tri)//3
                if u not in us:continue
                q,det,delta,rep=reduction((1,1,1),tri);dd=d-coef*delta
                if q*coef>2*det*d or dd<0:continue
                if dd==0:
                    if rep!=(0,0,0):continue
                    v=1386
                elif isinstance(entry(side,rep[0],dd),int):continue
                else:
                    ds=side
                    if rank==42 and not side and dd%7==0:dd//=7;ds=1
                    key=(ds,dd)+rep
                    if key not in tri_vars:
                        v=z3.Real('T'+'_'.join(map(str,key)));tri_vars[key]=v;s.add(v>=0)
                    v=tri_vars[key]
                alltri[j,d,tri]=v
                for t in set(tri):
                    rest=list(tri);rest.remove(t)
                    hist.setdefault((t,u),[]).append(v*(1+(rest[0]!=rest[1])))
            for t,u in product(ts,us):s.add(sum(hist.get((t,u),[]))==2*vals[t,u,4])
    print('joint vertex-line flags',side,len(lookup),'triangle flags',len(tri_vars),flush=True)
    return alltri
