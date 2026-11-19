"""Enumerate six-orbit row-sum matrices for a cyclic action on a folded quotient."""
from itertools import permutations,product
from collections import Counter
import json
from pathlib import Path

def row_types():
    bydiag={}
    for d in (0,2,4):
        possibilities=[]
        for tail in product(range(6),repeat=5):
            if d+sum(tail)==12 and d*d+sum(a*a for a in tail)==36-d:
                possibilities.append(tail)
        bydiag[d]=possibilities
    return bydiag

def build():
    rows=row_types()
    allmat=[]
    for diag in ((0,0,0,2,2,2),(0,0,0,0,2,4)):
        opts=[[r[:i]+(d,)+r[i:] for r in rows[d]] for i,d in enumerate(diag)]
        relabel=[p for p in permutations(range(6)) if all(diag[i]==diag[p[i]] for i in range(6))]
        canon=set()
        def rec(matrix):
            i=len(matrix)
            if i==6:
                key=min(tuple(tuple(matrix[x][y] for y in p) for x in p) for p in relabel)
                canon.add(key)
                return
            for r in opts[i]:
                if any(r[j]!=s[i] or sum(a*b for a,b in zip(r,s))+r[j]!=24 for j,s in enumerate(matrix)):
                    continue
                rec(matrix+[r])
        rec([])
        print('diagonal',diag,'classes',len(canon),flush=True)
        allmat.extend(sorted(canon))
    return allmat

if __name__=='__main__':
    mats=build()
    Path(__file__).with_name('quotient-rows.json').write_text(json.dumps(mats)+'\n')
    for mat in mats: print(' '.join(''.join(map(str,r)) for r in mat))
