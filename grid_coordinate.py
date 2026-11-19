"""Check the orientation and triangle-count restrictions on a preserved nonzero dual direction."""
from collections import Counter
from itertools import combinations
import json
from triple_moments import tmp


def check():
    for pattern in json.loads((tmp/'grid-sign-types.json').read_text()):
        negative=pattern['triangles'];counts=Counter(p for tri in negative for p in combinations(tri,2));edges=list(combinations(range(11),2))
        assert all(counts[p]%3==0 for p in edges)
        kept=0
        for number in (2,9):
            for pp in combinations(range(11),number):
                P=set(pp);sums=0;ok=True
                for i,j in edges:
                    a=1 if i in P else -2;b=1 if j in P else -2
                    bias=-1-a-b;total=9-counts[i,j]
                    c0,r=divmod(total+2*bias,3);c1,t=divmod(total-bias,3)
                    assert not r and not t
                    if min(c0,c1)<0:ok=False;break
                    sums+=c0
                if ok and not negative and sums%3:ok=False
                kept+=ok
        print('negative triangles',len(negative),'remaining diagonal sets',kept,flush=True)
        assert kept==0


if __name__=='__main__':check()
