"""Classify heavy-signature overlaps and test the necessary zero-vertex incidences."""
from itertools import combinations
from functools import cache
from collections import Counter
import numpy as np,pynauty
from ortools.sat.python import cp_model
def classify():
    classes={}
    for i in range(5):
        for row in np.load('/tmp/conway99-tools/signed8-profiles-%d.npy'%i):
            m=list(map(int,row[:8]));a=np.array([[(x&y).bit_count() if x!=y else 0 for y in m] for x in m]);g={k:[] for k in range(8)};double=set()
            for j,k in combinations(range(8),2):
                if a[j,k]:
                    g[j].append(k);g[k].append(j)
                    if a[j,k]==2:
                        h=len(g);double.add(h);g[h]=[j,k];g[j].append(h);g[k].append(h)
            cols=[set(range(8))]+([double] if double else [])
            key=pynauty.certificate(pynauty.Graph(len(g),adjacency_dict=g,vertex_coloring=cols))
            if key not in classes:classes[key]=(a,Counter())
            classes[key][1][i]+=1
    return list(classes.values())
def test(a,edge):
    m=cp_model.CpModel();ij=list(combinations(range(8),2));D=([] if edge==() else list(edge))
    masks=[z for z in range(1,256) if 2<=z.bit_count()<=5 and all(not (z>>i&z>>j&1) or a[i,j]+int((i,j)==edge)<2 for i,j in ij)]
    v=[m.new_int_var(0,2,'z'+str(z)) for z in masks]
    m.add(sum(v)==11)
    for i in range(8):m.add(sum(x for x,z in zip(v,masks) if z>>i&1)==4+int(i in D))
    for i,j in ij:m.add(sum(x for x,z in zip(v,masks) if z>>i&z>>j&1)<=2-int((i,j)==edge)-int(a[i,j]))
    s=cp_model.CpSolver();s.parameters.num_search_workers=1;s.parameters.max_time_in_seconds=1
    return s.StatusName(s.solve(m))
if __name__=='__main__':
    K=classify();print('overlap graph classes',len(K),flush=True)
    for i,(a,counts) in enumerate(K):print(i,counts,'no heavy edges',test(a,()),flush=True)
