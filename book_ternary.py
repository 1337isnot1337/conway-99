"""Enumerate local color-cycle quotients for a complete six-grid book."""
from itertools import product,combinations,permutations
import numpy as np
from ortools.sat.python import cp_model
from triple_moments import tmp

def types():
    return np.array([w for w in product(range(3),repeat=6) if w[0]==0 and all(w.count(i)==2 for i in range(3))],dtype=np.int16)
def enumerate_counts():
    W=types();look={tuple(w):j for j,w in enumerate(W)};maps=[]
    for p in permutations(range(6)):
        for s in (1,-1):
            M=s*(W[:,p]-W[:,p[0],None])%3
            maps.append([look[tuple(w)] for w in M])
    maps=np.array(maps,dtype=int);m=cp_model.CpModel();x=[m.new_int_var(0,4,'') for _ in W]
    for p,q in combinations(range(6),2):
        for d,k in enumerate((4,8,8)):m.add(sum(v for w,v in zip(W,x) if (w[p]-w[q])%3==d)==k)
    class Call(cp_model.CpSolverSolutionCallback):
        def __init__(self):super().__init__();self.seen=set();self.reps=[];self.n=0
        def on_solution_callback(self):
            self.n+=1;a=np.array([self.value(v) for v in x],dtype=np.uint8)
            if a.tobytes() in self.seen:return
            self.reps.append(a);self.seen.update(row.tobytes() for row in a[maps])
    cb=Call();s=cp_model.CpSolver();s.parameters.num_workers=1;s.parameters.enumerate_all_solutions=True;status=s.solve(m,cb)
    assert status==cp_model.OPTIMAL and len(cb.seen)==cb.n
    print('unsigned assignments',cb.n,'orbits',len(cb.reps),flush=True)
    np.save(tmp/'book-ternary-counts.npy',cb.reps)
    with (tmp/'book-ternary.in').open('w') as out:
        for r in cb.reps:
            words=W.repeat(r,axis=0);assert words.shape==(20,6)
            print(*words.flat,file=out)
if __name__=='__main__':enumerate_counts()
