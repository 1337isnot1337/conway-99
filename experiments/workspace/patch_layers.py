"""Classify first bootstrap layers of a rooted two-axis nine-vertex patch."""
from itertools import combinations
from collections import Counter
from pathlib import Path
import numpy as np
import pynauty
from percolation_layers import plans
from triple_moments import tmp

def patch(kind):
    opts=[[],[(0,1)],[(0,3)],[(0,1),(0,2)],[(0,1),(2,3)],[(0,3),(1,2)],[(0,1),(0,2),(1,3),(2,3)]]
    B=np.zeros((9,9),np.int16)
    for p,q in [(0,h) for h in (1,2,3,4)]+[(1,2),(3,4)]+[(5+u,h) for u in range(4) for h in (1+u//2,3+u%2)]+[(5+u,5+v) for u,v in opts[kind]]:B[p,q]=B[q,p]=1
    return B

def canon(B,S):
    # Relabel the two axes and their signs, fixing the root.
    moves=[]
    for swap in range(2):
        for f in range(4):
            def h(i):return 2*(i//2^swap)+(i%2^(f>>(i//2)&1))
            p=[0]+[1+h(i) for i in range(4)]
            for u in range(4):
                a,b=sorted([h(u//2),h(2+u%2)]);p.append(5+2*a+b%2)
            if np.array_equal(B[np.ix_(p,p)],B):moves.append(p)
    return min(tuple(sorted(sum(1<<p[i] for i in range(9) if s>>i&1) for s in S)) for p in moves)

def catalog(kind):
    B=patch(kind)
    return sorted({canon(B,s) for s in plans(B)})

if __name__=='__main__':
    import argparse,json
    arg=argparse.ArgumentParser();arg.add_argument('kinds',nargs='*',type=int,default=list(range(7)));a=arg.parse_args()
    for k in a.kinds:
        d=catalog(k)
        print(k,len(d),'large signatures',sorted(Counter(tuple(sorted(Counter(s.bit_count() for s in S).items())) for S in d).items()),flush=True)
        (tmp/('patch-layers-%d.json'%k)).write_text(json.dumps(d))
