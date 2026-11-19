"""Classify linear holonomy on the matching complex for a root contained in 21 grids."""
from itertools import combinations, permutations
from collections import Counter
import numpy as np

axes = list(combinations(range(7), 2))
edges = [(a,b) for a,b in combinations(range(21),2) if set(axes[a]).isdisjoint(axes[b])]
ei = {e:i for i,e in enumerate(edges)}
faces = [f for f in combinations(range(21),3) if all(e in ei for e in combinations(f,2))]
fi = {f:i for i,f in enumerate(faces)}
boundary = [sum(1 << ei[e] for e in combinations(f,2)) for f in faces]
stars = [sum(1<<i for i,x in enumerate(boundary) if x>>j & 1) for j in range(105)]


def reduce_binary(images):
    pivots = {}
    kernel = []
    for i,x in enumerate(images):
        preimage = 1 << i
        while x:
            top = x.bit_length()-1
            if top not in pivots:
                pivots[top] = (x,preimage)
                break
            y,z = pivots[top]
            x ^= y
            preimage ^= z
        if not x:
            kernel.append(preimage)
    return pivots,kernel


def image(x, images):
    y = 0
    while x:
        b = x & -x
        y ^= images[b.bit_length()-1]
        x ^= b
    return y


def bicycle_classes():
    gram = [image(s, boundary) for s in stars]
    _,ker = reduce_binary(gram)
    pivots,_ = reduce_binary([image(k,stars) for k in ker])
    possible = {0}
    for x,_ in pivots.values():
        possible |= {y^x for y in possible}
    actions = []
    for i in range(6):
        perm = list(range(7))
        perm[i],perm[i+1] = perm[i+1],perm[i]
        lift = [axes.index(tuple(sorted(perm[x] for x in a))) for a in axes]
        actions.append([1<<fi[tuple(sorted(lift[x] for x in f))] for f in faces])
    reps = []
    while possible:
        h = min(possible)
        orbit, todo = {h},[h]
        while todo:
            g = todo.pop()
            for act in actions:
                u = image(g,act)
                if u not in orbit:
                    orbit.add(u)
                    todo.append(u)
        possible -= orbit
        reps.append((h,len(orbit)))
    return reps


def signs_for(h):
    pivots,_ = reduce_binary(stars)
    z = 0
    while h:
        x,y = pivots[h.bit_length()-1]
        h ^= x
        z ^= y
    return [1-2*((z>>i)&1) for i in range(105)]


def index(a,b):
    return ei[min(a,b),max(a,b)]


def gf3kernel(rows, width):
    mat = np.array(rows,dtype=np.int16).reshape(-1,width) % 3
    pivots = []
    for j in range(width):
        r = len(pivots)
        nz = np.flatnonzero(mat[r:,j])
        if not len(nz):
            continue
        p = r+int(nz[0])
        mat[[r,p]] = mat[[p,r]]
        mat[r] = mat[r]*mat[r,j]%3
        factors = mat[:,j].copy()
        factors[r] = 0
        mat = (mat-factors[:,None]*mat[r])%3
        pivots.append(j)
    free = [j for j in range(width) if j not in pivots]
    out = np.zeros((len(free),width),dtype=np.int16)
    for i,j in enumerate(free):
        out[i,j] = 1
        out[i,pivots] = -mat[:len(pivots),j]%3
    return out


def shifts(h, signs):
    # t_ab is the additive constant in the affine map from a to b.
    def t(a,b):
        row = np.zeros(105,dtype=np.int16)
        i = index(a,b)
        row[i] = 1 if a<b else -signs[i]
        return row
    def path(a,b,c):
        return signs[index(b,c)]*t(a,b)+t(b,c)
    rows = []
    # Choose a vertex-translation gauge by setting shifts on a spanning tree to zero.
    seen,todo={0},[0]
    while todo:
        a=todo.pop()
        for b in range(21):
            if b not in seen and (min(a,b),max(a,b)) in ei:
                seen.add(b)
                todo.append(b)
                rows.append(t(a,b))
    for a,b in edges:
        twisted = []
        for c in set(range(21))-{a,b}:
            f = fi.get(tuple(sorted((a,b,c))))
            if f is None:
                continue
            row = path(a,c,b)
            if h>>f & 1:
                twisted.append(row)
            else:
                rows.append(row-t(a,b))
        if twisted:
            assert len(twisted)==2
            rows.append(twisted[0]-twisted[1])
    return gf3kernel(rows,105)


def shared_ok(signs,t):
    def perm(a,b,c):
        i = index(a,b)
        return (signs[i]*c+(t[i] if a<b else -signs[i]*t[i]))%3
    for a,b in combinations(range(21),2):
        if (a,b) in ei:
            continue
        via=[c for c in range(21) if (min(a,c),max(a,c)) in ei and (min(b,c),max(b,c)) in ei]
        for x in range(3):
            parity=0
            for c in via:
                parity ^= 1<<int(perm(c,b,perm(a,c,x)))
            if parity:
                return False
    return True


if __name__=='__main__':
    from itertools import product
    from pathlib import Path
    import json
    reps=bicycle_classes()
    print('bicycle orbits',len(reps),'total',sum(g for _,g in reps),flush=True)
    result=[]
    for h,m in reps:
        signs=signs_for(h)
        basis=shifts(h,signs)
        valid=[]
        if len(basis)<=10:
            for co in product(range(3),repeat=len(basis)):
                vec=np.array(co,dtype=np.int16)@basis%3
                if shared_ok(signs,vec):
                    valid.append(list(map(int,vec)))
        print('weight',h.bit_count(),'orbit',m,'gauge-fixed dimension',len(basis),'shared survivors',len(valid) if len(basis)<=10 else 'unexamined',flush=True)
        result.append(dict(face_mask=str(h),size=m,signs=signs,dimension=len(basis),survivors=valid))
    Path(__file__).with_name('cover-classes.json').write_text(json.dumps(result)+'\n')
