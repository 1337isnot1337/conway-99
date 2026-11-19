"""Enumerate all signed cube decompositions of each norm-sixteen core."""
from itertools import combinations
from pathlib import Path
from collections import Counter
import json
def cubes(R):
    res=[]
    for I in combinations(range(8),4):
        for J in combinations(range(8),4):
            x=sum(1<<i for i in I);y=sum(1<<j for j in J)
            if all((R[j]&x).bit_count()==3 for j in J) and all(sum(R[j]>>i&1 for j in J)==3 for i in I):
                res.append((x,y))
    return res
def verify():
    for k,R in enumerate(json.loads(Path('signed-eight-cores.json').read_text())):
        C=cubes(R)
        for x,y in C:
            assert (255^x,255^y) in C
            for j,row in enumerate(R):
                assert (row&(x if y>>j&1 else 255^x)).bit_count()==3
        assert len(C)==(8,4,2,4,2)[k]
        print('core',k,'unordered cube decompositions',len(C)//2)
if __name__=='__main__':verify()
