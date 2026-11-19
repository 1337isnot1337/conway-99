"""Unsigned exterior words of a six-page book, and their admissible pair margins."""
from itertools import permutations,combinations
from collections import Counter
from triple_moments import tmp
import numpy as np

def words():
    F={tuple(sorted([(i,5)]+[tuple(sorted(((i-j)%5,(i+j)%5))) for j in (1,2)])) for i in range(5)}
    S=[]
    for perm in permutations(range(6)):
        parts=[tuple(sorted(perm[2*i:2*i+2])) for i in range(3)]
        if any(perm[2*i]>perm[2*i+1] for i in range(3)) or tuple(sorted(parts)) in F:continue
        S.append(tuple(next(i for i in range(3) if p in parts[i]) for p in range(6)))
    return np.array(sorted(set(S)),np.int16)

def write(W,file):
    I=np.array([W[:,p]==c for p in range(6) for c in range(3)],dtype=np.int16)
    assert I.shape==(18,60) and np.all(I.sum(axis=1)==20)
    G=I@I.T
    for i,j in combinations(range(18),2):
        assert G[i,j]==(0 if i//3==j//3 else 4 if i%3==j%3 else 8)
    file.write_text(' '.join(str(sum(int(b)<<i for i,b in enumerate(r))) for r in I)+'\n')
if __name__=='__main__':write(words(),tmp/'book-unsigned.txt')
