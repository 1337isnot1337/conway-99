"""Enumerate the seven-edge graphs on the seven unused signed neighbors, up to axis permutation."""
from itertools import combinations
from math import factorial
import json
import pynauty
from triple_moments import tmp


def cases():
    edges=list(combinations(range(7),2));catalog={}
    for chosen in combinations(edges,7):
        adj={j:[] for j in range(7)}
        for i,j in chosen:adj[i].append(j);adj[j].append(i)
        G=pynauty.Graph(7,adjacency_dict=adj);key=pynauty.certificate(G)
        if key not in catalog:
            _,order,p,*_=pynauty.autgrp(G);catalog[key]=[chosen,0,int(round(order*10**p))]
        catalog[key][1]+=1
    assert all(n*aut==factorial(7) for _,n,aut in catalog.values())
    return sorted(catalog.values(),key=lambda x:(-x[2],x[0]))


if __name__=='__main__':
    c=cases();print('unlabelled cases',len(c),'labelled patterns',sum(x[1] for x in c),flush=True)
    (tmp/'hemisphere-cases.json').write_text(json.dumps(c))
