"""Check the far-pair four-cycle certificate in the complementary Fano incidence graph."""
from itertools import permutations
B=[{(x+i)%7 for x in (2,4,5,6)} for i in range(7)]
checks=0
for y,S in enumerate(B):
    for x in set(range(7))-S:
        E=[S&T for i,T in enumerate(B) if x in T]
        assert len(E)==4 and all(len(e)==2 for e in E)
        assert len(set(map(frozenset,E)))==4
        assert all(sum(i in e for e in E)==2 for i in S)
        checks+=1
assert checks==21
print('all 21 ordered opposite nonincidences in a Fano core give a four-cycle')
