"""Use the binary projection orbit, and check the rank, graph, and integer defect of the saved matrix."""
import argparse,subprocess
import numpy as np
from binary_seeds import rank2,tmp

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--rank',type=int,default=62);p.add_argument('--seed',type=int,default=1);p.add_argument('--iterations',type=int,default=60000);a=p.parse_args()
    name=tmp/('binary-walk-%d-%d'%(a.rank,a.seed));inp=name.with_suffix('.in');out=name.with_suffix('.out')
    np.savetxt(inp,np.load(tmp/('binary-seed-%d.npy'%a.rank)),fmt='%d')
    subprocess.run([str(tmp/'binary_switch'),str(inp),str(out),str(a.seed),str(a.iterations),str(a.rank)],check=True)
    G=np.loadtxt(out,dtype=np.int16);assert rank2(G)==54 and not np.any(G!=G.T) and not np.any(np.diag(G)) and np.all((G@G+G)%2==0)
    q=G@G+G-12*np.eye(99,dtype=int)-2
    print('verified modulo 2 rank and integer defect',int((q*q).sum()),flush=True)
    if not np.any(q):np.save('verified-conway-99.npy',G)
