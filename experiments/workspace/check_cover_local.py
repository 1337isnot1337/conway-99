"""Independent four-symbol enumeration for the triangle transport parity argument."""
from itertools import combinations_with_replacement, permutations, product
from collections import Counter

points=range(4)
perms=list(permutations(points))
def action(p):
    return tuple(p[0]^p[x] for x in (1,2,3))

for d,e in product((1,2,3),repeat=2):
    target=[tuple(sorted((i,i^d,i^e))) for i in points]
    valid=0
    for triple in combinations_with_replacement(perms,3):
        if any(tuple(sorted(p[i] for p in triple))!=target[i] for i in points):
            continue
        valid+=1
        parts=Counter(action(p) for p in triple)
        for a,c in parts.items():
            if a!=(1,2,3):
                assert c==2 and sum(x==y for x,y in zip(a,(1,2,3)))==1
    assert valid>0
    print('oppositions',d,e,'unordered decompositions',valid)
