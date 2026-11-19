from triangle_cyclic import designs,point_intersections,tmp,local_ball
from itertools import product
import numpy as np

def batch():
    with (tmp/'triangle-paired.txt').open('w') as out:
        for t in (0,4):
            A=local_ball(12,[[(i+6)%12 for i in range(12)]]*3,[(i+t)%12 for i in range(12)])
            M=point_intersections(A)
            for idx,L in enumerate(designs(list(map(int,M[3,15:27])))):
                V=[(x,(x+i)%12,12+(x+a)%12,12+(x+a+j)%12) for i,(j,a) in enumerate(L,1) for x in range(12)]
                print(t,idx,*(sum(1<<z for z in s) for s in V),file=out)
if __name__=='__main__':batch()
