"""Recover all signed norm-18 cores from the bipartite incidence census."""
from itertools import combinations
from pathlib import Path
from collections import Counter
import json,networkx as nx

def internal(deg):
    total=sum(deg)//2
    possible=list(combinations([i for i,d in enumerate(deg) if d],2))
    for E in combinations(possible,total):
        if [sum(i in edge for edge in E) for i in range(9)]==deg:yield E
def census():
    ans=[]
    for n in (36,38,40):
        for line in Path(f'/tmp/conway99-tools/signed9-{n}.g6').read_bytes().splitlines():
            G=nx.from_graph6_bytes(line)
            assert not any((a<9)==(b<9) for a,b in G.edges)
            if any(len(G[a].keys()&G[b].keys())>2 for a,b in combinations(range(18),2)):continue
            for pos in internal([G.degree(i)-4 for i in range(9)]):
                for neg in internal([G.degree(9+i)-4 for i in range(9)]):
                    H=G.copy();H.add_edges_from(pos);H.add_edges_from((9+i,9+j) for i,j in neg)
                    if any(len(H[a].keys()&H[b].keys())+int(b in H[a])>2 for a,b in combinations(range(18),2)):continue
                    rr=[sum(1<<j for j in H[i]) for i in range(18)]
                    cores=[]
                    for U in combinations(range(9),4):
                        if any(H.has_edge(i,j) for i,j in combinations(U,2)):continue
                        M=[j for j in range(9,18) if sum(j in H[i] for i in U)==3]
                        for V in combinations(M,4):
                            if any(H.has_edge(i,j) for i,j in combinations(V,2)):continue
                            if all(sum(j in H[i] for j in V)==3 for i in U):cores.append(U+V)
                    ans.append((rr,cores))
    Path('signed-nine-cores.json').write_text(json.dumps(ans)+'\n')
    print('signed types by number of internal edges and aligned cubes',Counter((sum((r&511).bit_count() for r in g[:9])//2,len(C)) for g,C in ans))
if __name__=='__main__':census()
