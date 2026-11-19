"""Complete outside incidence types for the five norm-16 biplane cores."""
from itertools import combinations
from collections import Counter
from functools import cache
from pathlib import Path
import json
import numpy as np

def designs(rows):
    B=np.array([[(r>>j)&1 for j in range(8)] for r in rows])
    sides=[]
    for M in (B.T@B,B@B.T):
        pairs=tuple((1<<a)|(1<<b) for a,b in combinations(range(8),2) for _ in range(2-int(M[a,b])))
        assert len(pairs)==8
        layouts=[tuple(sorted(pairs))]
        poss=[sum(1<<j for j in c) for c in combinations(range(8),3) if all((1<<a|1<<b) in pairs for a,b in combinations(c,2))]
        for c in range(1,len(poss)+1):
            for blocks in combinations(poss,c):
                small=list(pairs)
                for trip in blocks:
                    for edge in [x for x in pairs if x&trip==x]:small.remove(edge)
                layouts.append(tuple(sorted(small+list(blocks),key=lambda x:(-x.bit_count(),x))))
        sides.append(layouts)
    cells=[]
    def compatible(p,n):
        for j,r in enumerate(rows):
            if (p&r).bit_count()+int(bool(n>>j&1))>2:return False
        for i in range(8):
            if sum((n>>j & rows[j]>>i)&1 for j in range(8))+int(bool(p>>i&1))>2:return False
        return True
    for P in sides[0]:
        for N in sides[1]:
            if len(P)!=len(N):continue
            def visit(k,rem):
                if k==len(P):yield tuple(cells);return
                p=P[k];seen=set()
                for j,n in enumerate(N):
                    if rem>>j&1==0 or n in seen or n.bit_count()!=p.bit_count():continue
                    seen.add(n)
                    if k and P[k-1]==p and n<cells[-1][1]:continue
                    if not compatible(p,n) or any((p&a).bit_count()+(n&b).bit_count()>2 for a,b in cells):continue
                    cells.append((p,n));yield from visit(k+1,rem^(1<<j));cells.pop()
            yield from visit(0,(1<<len(P))-1)

def profiles(rows):
    for cells in designs(rows):
        mask=[(p|(n<<8)) for p,n in cells]
        for p in range(8):
            for n in range(8):
                count=2-(rows[n]>>p&1)-sum((a>>p & b>>n)&1 for a,b in cells)
                if count<0:break
                mask += [(1<<p)|(1<<(8+n))]*count
            else:continue
            break
        else:
            yield tuple(mask+[0]*(83-len(mask)))

def run():
    for idx,rows in enumerate(json.loads(Path('signed-eight-cores.json').read_text())):
        ps=list(profiles(rows))
        print(idx,'profiles',len(ps),'heavy counts',Counter(sum(t.bit_count()>=4 for t in p) for p in ps),flush=True)
        np.save('/tmp/conway99-tools/signed8-profiles-%d.npy'%idx,np.array(ps,dtype=np.uint16).reshape(-1,83))
if __name__=='__main__':run()
