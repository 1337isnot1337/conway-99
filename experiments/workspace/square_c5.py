"""A fivefold symmetry of the square neighborhood alone; the exterior is unrestricted."""
import argparse
from collections import Counter
from itertools import combinations
from math import isqrt
from pathlib import Path
import numpy as np
from flint import fmpz_mat
from square_ball import metrics


def shell(voltage):
    A=np.zeros((48,48),dtype=np.int16)
    def edge(a,b):A[a,b]=A[b,a]=1
    def v(i,b,t):return 8+10*i+2*(t%5)+b
    t=np.arange(5)
    for i in range(4):
        edge(i,(i+1)%4);edge(4+i,i);edge(4+i,(i+1)%4)
        if i<2:edge(4+i,6+i)
        edge(i,np.arange(8+10*i,18+10*i));edge(v(i,0,t),v(i,1,t))
        for b in range(2):
            shift=voltage[i] if i<3 and b else 0
            if i==3:shift=voltage[3+b]
            edge(v(i,b,t),v((i+1)%4,b^(i==3),t+shift))
    for i in range(2):
        for a in range(2):
            for b in range(2):
                edge(v(i,a,t),v(i+2,b,t+voltage[5+4*i+2*a+b]))
    return A


def find(total,goal):
    c=Counter();rng=np.random.default_rng(1975)
    for i in range(total):
        voltage=rng.integers(5,size=13)
        A=shell(voltage)
        if np.any(np.triu(A@A+A,1)>2):continue
        c['codegree']+=1
        _,g,h=metrics(A)
        if min(g[0],h[0])< -1e-8:continue
        c['spectral']+=1
        B=A[4:,4:]
        det=int(fmpz_mat((27*np.eye(44,dtype=int)-9*B+1).tolist()).det())
        assert det>=0 and isqrt(det)**2==det
        if not det:continue
        c['positive']+=1
        np.save('square-c5-%d.npy'%c['positive'],A)
        print(i,c,voltage.tolist(),flush=True)
        if c['positive']==goal:break
    print('sample',i+1,c,flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--rounds',type=int,default=50000);p.add_argument('--goal',type=int,default=5)
    a=p.parse_args();find(a.rounds,a.goal)
