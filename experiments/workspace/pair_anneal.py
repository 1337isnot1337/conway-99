"""Generate and independently verify a two-center incidence assembly."""
import argparse,subprocess
import numpy as np
from pair_cover import tmp,sample,prepare,validate


def run(seed,epochs):
    B=sample(seed);sides,_,_,Q=prepare(B)
    P=np.flatnonzero(B[0]*(1-B[1]));U=np.flatnonzero(B[1]*(1-B[0]));shared=np.flatnonzero(B[0]*B[1])
    name=tmp/('switch-%d'%seed)
    with name.with_suffix('.in').open('w') as f:
        print(len(sides[0]),len(P),file=f)
        for catalog,private in zip(sides,(P,U)):
            for pair in catalog:
                print(sum(1<<i for i,a in enumerate(shared) if a in pair),sum(1<<i for i,a in enumerate(private) if a in pair),file=f)
        print(*Q[np.ix_(P,U)].ravel(),file=f)
    out=name.with_suffix('.out')
    subprocess.run([str(tmp/'pair_switch'),str(name.with_suffix('.in')),str(out),str(seed),str(epochs)],check=True)
    numbers=list(map(int,out.read_text().split()));nei=[]
    for i,j in enumerate(numbers[1:]):
        v=np.zeros(len(B),np.int16);v[list(sides[0][i]+sides[1][j])]=1;nei.append(v)
    N=np.array(nei).T.copy();defect=N@N.T-Q
    actual=int((defect.astype(int)**2).sum()//2)
    assert actual==numbers[0]
    if actual==0:
        assert validate(B,N);np.savez_compressed(tmp/('pair-cover-%d.npz'%seed),B=B,N=N)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--seed',type=int,default=1);p.add_argument('--epochs',type=int,default=140);a=p.parse_args();run(a.seed,a.epochs)
