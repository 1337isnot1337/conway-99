"""Build a rooted linear-shell seed using a sevenfold relabeling, then release it."""
import json
from itertools import combinations
from pathlib import Path
from pysat.solvers import Solver

def make(k=14):
    labels=[(a,b) for a,b in combinations(range(k),2) if a^1!=b]
    ind={e:i for i,e in enumerate(labels)}
    n=len(labels)
    rotation=[ind[tuple(sorted(((a+2)%k,(b+2)%k)))] for a,b in labels]
    orbs={}
    variables=0
    for i,j in combinations(range(n),2):
        if (i,j) in orbs: continue
        variables+=1
        x,y=i,j
        while tuple(sorted((x,y))) not in orbs:
            orbs[tuple(sorted((x,y)))]=variables
            x,y=rotation[x],rotation[y]
    with Solver(name='mc') as s:
        for i,e in enumerate(labels):
            for a in range(k):
                lits=[orbs[tuple(sorted((i,j)))] for j,f in enumerate(labels) if i!=j and a in f]
                count=2-int(a in e)-int((a^1) in e)
                # Native MiniCard accepts repeated literals as repeated summands.
                s.add_atmost(lits,count)
                s.add_atmost([-x for x in lits],len(lits)-count)
        s.conf_budget(500000)
        res=s.solve_limited()
        print('rotation quotient',variables,'variables status',res,'conflicts',s.accum_stats()['conflicts'],flush=True)
        if res is not True: return
        pos=set(z for z in s.get_model() if z>0)
    rows=[0]*n
    for (i,j),v in orbs.items():
        if v in pos:
            rows[i]|=1<<j
            rows[j]|=1<<i
    for i,e in enumerate(labels):
        for a in range(k):
            assert sum((rows[i]>>j)&1 for j,f in enumerate(labels) if a in f)==2-int(a in e)-int((a^1) in e)
    # Canonical orientation of the alternating cycles at coordinate 0.
    mate={}
    for a in range(2,k):
        i=ind[0,a]
        mate[a],=(b for b in range(2,k) if rows[i]>>ind[0,b]&1)
    cycles=[]
    unseen=set(mate)
    while unseen:
        a=min(unseen)
        cycle=[]
        while a in unseen:
            cycle.extend([a,a^1])
            unseen.difference_update([a,a^1])
            a=mate[a^1]
        cycles.append(cycle)
    cycles.sort(key=lambda c:(len(c),c))
    order=[0,1]+sum(cycles,[])
    perm=[ind[tuple(sorted((order[a],order[b])))] for a,b in labels]
    norm=[sum(1<<j for j,p in enumerate(perm) if rows[o]>>p&1) for o in perm]
    Path(__file__).with_name('anchor-seed.json').write_text(json.dumps([str(x) for x in norm])+'\n')
    print('canonical matching lengths',[len(c)//2 for c in cycles],'validated all incidence totals',flush=True)

if __name__=='__main__':
    make()
