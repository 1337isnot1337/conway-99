"""Recover admissible axis characters for each linear-connection representative."""
from itertools import combinations, product
import json
from pathlib import Path
import numpy as np
from matching_cover import axes, edges, ei, index


def maps(signs,t):
    m=np.full((21,21,3),-1,dtype=int)
    for (a,b),s,d in zip(edges,signs,t):
        for x in range(3):
            y=(s*x+d)%3
            m[a,b,x]=y
            m[b,a,y]=x
    return m


def axis_profiles(m,i):
    six=[b for b in range(21) if i in axes[b]]
    tests=[]
    for a in range(21):
        if a in six: continue
        tests.append([(j,[1<<int(c) for c in m[b,a]]) for j,b in enumerate(six) if m[b,a,0]>=0])
    allowed=[]
    for choice in product(range(3),repeat=6):
        for test in tests:
            parity=0
            for j,lookup in test: parity ^= lookup[choice[j]]
            if parity: break
        else:
            allowed.append(dict(zip(six,choice)))
    return allowed


def frame_sets(m,profiles):
    assignment = [{} for _ in range(7)]
    # Two coincident cells share the character chosen for the common axis
    # in the matrix of two-step paths. It must occur at least twice.
    def allowed_axis(prof):
        for a,b in combinations(prof,2):
            c,d=prof[a],prof[b]
            if not any(m[a,z,0]>=0 and m[z,b,0]>=0 and m[z,b,m[a,z,c]]==d for z in range(21)):
                return False
        return True
    good=[[p for p in group if allowed_axis(p)] for group in profiles]
    order=sorted(range(7), key=lambda i:len(good[i]))
    def rec(j):
        if j==7:
            yield tuple((assignment[a][i],assignment[b][i],3-assignment[a][i]-assignment[b][i]) for i,(a,b) in enumerate(axes))
            return
        i=order[j]
        for p in good[i]:
            if any(assignment[h].get(b)==c for b,c in p.items() for h in axes[b] if h!=i):
                continue
            assignment[i]=p
            yield from rec(j+1)
            assignment[i]={}
    return good,rec(0)


if __name__=='__main__':
    root=Path(__file__).parent
    for rep in json.loads((root/'cover-classes.json').read_text()):
        for j,t in enumerate(rep['survivors']):
            m=maps(rep['signs'],t)
            prof=[axis_profiles(m,i) for i in range(7)]
            good,frames=frame_sets(m,prof)
            from itertools import islice
            batch=list(islice(frames,1001))
            print('orbit',rep['size'],'lift',j,'axis domain',[len(p) for p in prof],'after concurrence',[len(p) for p in good],'frames first 1001',len(batch),flush=True)
