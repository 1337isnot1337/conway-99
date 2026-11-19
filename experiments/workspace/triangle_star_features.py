from triangle_star import tmp
import argparse,numpy as np
def write(seed,trial):
    fn=tmp/('triangle-star-%d-%d'%(seed,trial));B=np.load(fn.with_suffix('.npz'))['B'];T=B[3:,3:]
    with fn.with_suffix('.in').open() as f:
        next(f);masks=np.array([int(next(f))]+[int(v) for v in f],dtype=np.int64)
    N=(masks[:,None]>>np.arange(36))&1
    features=[]
    for d,a,c in [(3,-1,1/9),(4,1,-2/11)]:
        M=d*np.eye(36)+a*T+c;L=(a*N+c)@np.linalg.inv(M)
        features.append(np.column_stack((c*(1-L.sum(axis=1)),(-a)*L)))
    np.stack(features,axis=1).astype(np.float64).tofile(fn.with_suffix('.features'))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('seed',type=int);p.add_argument('trial',type=int);a=p.parse_args();write(a.seed,a.trial)
