"""Check profile enumeration and local equations using explicit rook and Golay eigenvectors."""
from collections import Counter
from itertools import combinations_with_replacement
import numpy as np
from triangle_ball import golay
from shell_profiles import neighborhoods,profiles

def test(G,lam,neg):
    N=len(G);degree=int(G[0].sum())
    for sites,weights in (([0],[1]),([0,1],[1,-1]),([0,1,5],[1,1,1]),([0,3,7],[1,-2,2])):
        b=np.zeros(N,dtype=int);b[sites]=weights
        a=lam*b-G@b;j=int(b.sum());assert np.all(G@a+neg*a==-2*j)
        p=dict(sorted(Counter(a.tolist()).items()));vals=tuple(p);n=list(p.values())
        M=np.array([a==t for t in vals],dtype=int).T
        D=G@M;E=M.T@D
        assert np.array_equal(D.T@D+E,2*np.outer(n,n)+(degree-2)*np.diag(n))
        for i,h in enumerate(vals):
            assert set(map(tuple,D[a==h])).issubset(neighborhoods(h,vals,n,j,degree,neg))
    print('four direct profiles pass on graph of order',N)

def enumeration():
    for j in range(5):
        for d in range(181):
            for p in profiles(j,d):
                assert sum(p.values())==99
                assert sum((9*a+j)*n for a,n in p.items())==0
                assert sum((9*a+j)**2*n for a,n in p.items())==18*d
    print('all enumerated profile moments checked through index 180')

if __name__=='__main__':
    rook=np.array([[int(i!=j and (i%3==j%3 or i//3==j//3)) for j in range(9)] for i in range(9)])
    test(rook,1,2);test(golay()[0],4,5);enumeration()
