"""Exact four-cell Fourier parity audit for the projective transport classes."""
from root_cover_linear import Cover,sign_cases,rotations,test_paths
from root_cover_parity import reduce_system,find
from itertools import product
import numpy as np

C=Cover()
for j,(s,size,faces) in enumerate(sign_cases(C)):
    M,paths,(sgn,A)=rotations(C,s)
    for u in product(range(3),repeat=len(M)):
        offs=(np.array(u)@M)%3
        if not test_paths(paths,offs):continue
        Q=(sgn[:,:,None]*np.arange(3)+(A@offs)[:,:,None])%3
        D=C.root_domains(Q)
        assert all(Q[b,a,Q[a,b,c]]==c for a,b in C.edges for c in range(3))
        S,t,r,z=reduce_system(C,Q,D)
        n=sum(1 for _ in find(D,S,t))
        print('sign class',j,'size',size,'offset',u,'domains',list(map(len,D)),'rank',r,'checks',z,'survivors',n,flush=True)
