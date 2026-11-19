"""Integral lower norm bound at a marked vertex, optionally with one marked neighbor."""
from functools import cache
from math import isqrt
@cache
def pair_costs(t,mod,norm_cap):
    r=t%mod;lim=isqrt(norm_cap)
    v=range(-lim+(r+lim)%mod,lim+1,mod)
    def small(s,k):
        z,rem=divmod(s-k*r,mod);assert rem==0
        q,m=divmod(z,k);return (k-m)*(r+q*mod)**2+m*(r+(q+1)*mod)**2
    pairs={};fixed={}
    for i in v:
        for j in v:
            if i*i+j*j>norm_cap:continue
            cost=2*(i*i+j*j)+small(-4*i-t-j,12)+small(-4*j-t-i,12)
            pairs[i+j]=min(pairs.get(i+j,10**15),cost)
            fixed.setdefault(i,{})[i+j]=cost
    def iterate(dp):
        nd={}
        for k,c in dp.items():
            for l,w in pairs.items():
                y=c+w
                if y<=2*norm_cap:nd[k+l]=min(nd.get(k+l,10**15),y)
        return nd
    dp={0:0}
    for _ in range(6):dp=iterate(dp)
    return dp,pairs,fixed
@cache
def minimum(t,mod,norm_cap,neighbor=None):
    if t<0:return minimum(-t,mod,norm_cap,None if neighbor is None else -neighbor)
    dp,pairs,fixed=pair_costs(t,mod,norm_cap)
    costs=pairs if neighbor is None else fixed.get(neighbor,{})
    val=min((v+dp.get(-4*t-k,10**15) for k,v in costs.items()),default=10**15)
    return t*t+(val+1)//2
if __name__=='__main__':
    from harmonic_theta import coord_energy
    for t in range(1,15):assert minimum(t,3,720)==coord_energy(t,80)
    print('third-coordinate control passed')
