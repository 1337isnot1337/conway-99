"""Solve far-pair sign parities for the nontrivial flat character cover."""
from itertools import combinations,product
from pathlib import Path
from collections import defaultdict
import json

from cover_frames import maps,axis_profiles,frame_sets
from matching_cover import axes,edges,index,ei,reduce_binary


def equations(m,profiles):
    masks=[]
    rhs=0
    delta=[[0 for _ in p] for p in profiles]
    def sign(a,b,c):
        if a>b:
            c=int(m[a,b,c])
        return (1,2,3)[c] << (2*index(a,b))
    for a,b in combinations(range(21),2):
        shared=set(axes[a])&set(axes[b])
        via=[z for z in range(21) if m[a,z,0]>=0 and m[z,b,0]>=0]
        for c,d in product(range(3),repeat=2):
            paths=[z for z in via if m[z,b,m[a,z,c]]==d]
            linked=not shared and m[a,b,c]==d
            if not paths and not linked:
                continue
            row=0
            for z in paths:
                row ^= sign(a,z,c)^sign(z,b,int(m[a,z,c]))
            if linked: row ^= sign(a,b,c)
            bit=1<<len(masks)
            masks.append(row)
            if (len(paths)+int(linked))//2 % 2: rhs ^= bit
            if linked:
                # Indicators of the third character at the two ends add.
                # Their two constant bits cancel, leaving the four axis choices.
                for cell,ch in [(a,c),(b,d)]:
                    for i in axes[cell]:
                        for j,spec in enumerate(profiles[i]):
                            if spec[cell]==ch: delta[i][j] ^= bit
            elif shared:
                i,=shared
                for j,spec in enumerate(profiles[i]):
                    if spec[a]==c and spec[b]==d: delta[i][j] ^= bit
    return masks,rhs,delta


def compatible(profiles,code):
    return all(profiles[a][code[a]][j]!=profiles[b][code[b]][j] for j,(a,b) in enumerate(axes))


def main():
    root=Path(__file__).parent
    data=json.loads((root/'cover-classes.json').read_text())[0]
    m=maps(data['signs'],data['survivors'][1])
    profiles=[axis_profiles(m,i) for i in range(7)]
    masks,rhs,delta=equations(m,profiles)
    cols=[sum(1<<i for i,row in enumerate(masks) if row>>j&1) for j in range(210)]
    pivots,ker=reduce_binary(cols)
    keys=sorted(pivots,reverse=True)
    def syndrome(x):
        for k in keys:
            if (x>>k)&1:
                x ^= pivots[k][0]
        return x
    test=syndrome(rhs)
    d=[[syndrome(y) for y in axis] for axis in delta]
    left=defaultdict(list)
    for a,b,c in product(range(18),repeat=3):
        left[d[0][a]^d[1][b]^d[2][c]].append((a,b,c))
    survivors=[]
    raw=0
    for a,b,c,e in product(range(18),repeat=4):
        for init in left.get(test^d[3][a]^d[4][b]^d[5][c]^d[6][e],()):
            raw+=1
            code=init+(a,b,c,e)
            if compatible(profiles,code):
                survivors.append(code)
    print('equations',len(masks),'sign rank',len(pivots),'kernel',len(ker),'raw compatible syndromes',raw,'legal frames',len(survivors),flush=True)
    (root/'cover-sign-frames.json').write_text(json.dumps(survivors)+'\n')


if __name__=='__main__':
    main()
