"""Exclude a prism index pair forming off-triangle grids at all three roots."""

from collections import Counter
from itertools import combinations, permutations, product

import numpy as np
import pynauty

from central_grid_neighborhood import gram_possible

CORNERS = (4, 5, 7, 8)
AXES = (0, 1, 2, 3, 6)
LAYERS = [tuple(range(9*t, 9*t+9)) for t in range(3)]
FIRST_GRIDS = [{9*t+v for t in range(3) for v in axis} for axis in ((0,1,2), (0,3,6))]
TRIANGLE = {0,9,18}


def residual(a):
    return 12*np.eye(len(a), dtype=np.int64)+2-a-a@a


def cores():
    base = np.zeros((27,27), dtype=np.int64)
    for layer in LAYERS:
        for u,v in combinations(layer,2):
            if u % 9 // 3 == v % 9 // 3 or u % 3 == v % 3:
                base[u,v] = base[v,u] = 1
    connections = []
    for t,s in combinations(range(3),2):
        for v in AXES:
            u,w = 9*t+v,9*s+v
            base[u,w] = base[w,u] = 1
        connections.append([(np.array(CORNERS)+9*t, np.array(p)+9*s)
                            for p in permutations(CORNERS)])
    seen = set()
    for interfaces in product(*connections):
        a = base.copy()
        for left,right in interfaces:
            a[left,right] = a[right,left] = 1
        m = residual(a)
        if m.min() < 0:
            continue
        rows = {i:v.nonzero()[0].tolist() for i,v in enumerate(a)}
        graph = pynauty.Graph(27, adjacency_dict=rows,
                             vertex_coloring=[TRIANGLE, set(range(27))-TRIANGLE])
        cert = pynauty.certificate(graph)
        if cert not in seen:
            seen.add(cert)
            yield a,m


def triple_rows(a,m):
    for row in product(*LAYERS):
        if any(len(set(row) & g) != 1 for g in FIRST_GRIDS):
            continue
        if any(m[u,v] == 0 for u,v in combinations(row,2)):
            continue
        if np.any(a[:,row].sum(axis=1)+np.isin(np.arange(27),row) > 2):
            continue
        yield row


def admits_incidence(rows,m):
    """Select distinct binary rows with the exact Gram matrix m."""
    masks = {}
    for k,row in enumerate(rows):
        bit = 1 << k
        for i in row:
            masks[i,i] = masks.get((i,i),0) | bit
        for i,j in combinations(row,2):
            masks[i,j] = masks.get((i,j),0) | bit
    quotas = [(masks.get((i,j),0), int(m[i,j])) for j in range(len(m)) for i in range(j+1)
              if m[i,j] or (i,j) in masks]
    if any(mask.bit_count() < n for mask,n in quotas):
        return False

    def search(chosen,free):
        while free:
            zero = one = 0
            branch = None
            for mask,n in quotas:
                need = n-(mask & chosen).bit_count()
                candidates = mask & free
                size = candidates.bit_count()
                if need < 0 or need > size:
                    return False
                if not need:
                    zero |= candidates
                elif size == need:
                    one |= candidates
                elif branch is None or size < branch[0]:
                    branch = (size,candidates)
            if zero & one:
                return False
            if not (zero | one):
                bit = branch[1] & -branch[1]
                return search(chosen | bit,free ^ bit) or search(chosen,free ^ bit)
            free &= ~(zero | one)
            chosen |= one
        return all((mask & chosen).bit_count() == n for mask,n in quotas)

    return search(0,(1 << len(rows))-1)


def prism_partitions(m):
    # A residual common neighbor of two corners in different layers is a
    # neighbor of T in the third fiber. Keep separate copies of repeated pairs.
    edges = [(9*t+u,9*s+v) for t,s in combinations(range(3),2) for u,v in product(CORNERS,repeat=2)
             for _ in range(m[9*t+u,9*s+v])]
    assert len(edges) == 24
    sites = sorted({i for e in edges for i in e})
    star = {i:sum(1 << j for j,e in enumerate(edges) if i in e) for i in sites}
    all_edges = (1 << len(edges))-1

    def match(free,remaining,chosen):
        if not remaining:
            yield chosen
            return
        u = min(remaining,key=lambda v:(free & star[v]).bit_count())
        choices = free & star[u]
        while choices:
            bit = choices & -choices
            choices ^= bit
            u,v = edges[bit.bit_length()-1]
            yield from match(free & ~(star[u] | star[v]), remaining-{u,v}, chosen | bit)

    matchings = list(match(all_edges,set(sites),0))
    by_edge = [[m for m in matchings if (m >> i) & 1] for i in range(len(edges))]
    def partition(free,selected):
        if not free:
            yield selected
            return
        first = (free & -free).bit_length()-1
        for m in by_edge[first]:
            if m & free == m:
                yield from partition(free ^ m,selected+(m,))
    seen = set()
    for cover in partition(all_edges,()):
        groups = tuple(sorted(tuple(sorted(e for k,e in enumerate(edges) if (m >> k) & 1))
                              for m in cover))
        if groups not in seen:
            seen.add(groups)
            yield groups


def ordered_prisms(a,groups):
    # Within each prism fix the names of its two transversal triangles in
    # fiber zero. The assignments of its other two signed pairs remain free.
    base = np.zeros((51,51), dtype=np.int64)
    base[:27,:27] = a
    orientations = []
    for h,group in enumerate(groups):
        pairs = [[e for e in group if all(v//9 != t for v in e)] for t in range(3)]
        assert list(map(len,pairs)) == [2,2,2]
        offset = 27+6*h
        for i,j in combinations(range(6),2):
            if i//2 == j//2 or i%2 == j%2:
                base[offset+i,offset+j] = base[offset+j,offset+i] = 1
        choices = []
        for signs in product(range(2),repeat=2):
            sites,neighbors = [],[]
            for t,flip in enumerate((0,)+signs):
                for s,edge in enumerate(pairs[t]):
                    sites.extend([offset+2*t+(s^flip)]*3)
                    neighbors.extend((9*t,*edge))
            choices.append((sites,neighbors))
        orientations.append(choices)
    for assignment in product(*orientations):
        h = base.copy()
        for u,v in assignment:
            h[u,v] = h[v,u] = 1
        yield h


def exterior_templates(triples):
    rows = []
    for r in triples:
        if any(i in TRIANGLE for i in r):
            continue
        fibers = [v//9 for v in r if v%9 in AXES]
        assert len(fibers) == len(set(fibers)) == 2
        required = [t for t in range(3) for _ in range(2-fibers.count(t))]
        for ordered in sorted(set(permutations(required))):
            for signs in product(range(2),repeat=4):
                rows.append(r+tuple(27+6*k+2*t+s for k,(t,s) in enumerate(zip(ordered,signs))))
    return np.array(rows,dtype=int)


def verify():
    counts = Counter()
    for a,m in cores():
        counts['cores'] += 1
        triples = list(triple_rows(a,m))
        if not admits_incidence(triples,m):
            continue
        counts['triple covers'] += 1
        templates = exterior_templates(triples)
        within = tuple(combinations(range(7),2))
        for groups in prism_partitions(m):
            counts['partitions'] += 1
            for h in ordered_prisms(a,groups):
                counts['layouts'] += 1
                rest = residual(h)
                if rest.min() < 0:
                    continue
                counts['nonnegative'] += 1
                if not gram_possible(rest):
                    continue
                counts['psd'] += 1
                allowed = np.ones(len(templates),dtype=bool)
                for u,v in within:
                    allowed &= rest[templates[:,u],templates[:,v]] > 0
                rows = templates[allowed]
                # The outside point and any of its selected core neighbors
                # have one fewer common neighbor available through adjacency.
                incidence = np.zeros((len(rows),51),dtype=np.int64)
                incidence[np.arange(len(rows))[:,None],rows] = 1
                rows = rows[np.max(incidence@h+incidence,axis=1) <= 2]
                assert not admits_incidence(rows.tolist(),rest)
    assert counts == dict(cores=93, **{'triple covers':7}, partitions=468, layouts=119808,
                          nonnegative=3000, psd=753), counts
    print('Full triangle common pair: 93 marked cores, seven with triple allocations, '
          '468 prism partitions, 119,808 layouts, 753 positive semidefinite exterior Grams, '
          'no exterior incidence.')


if __name__ == '__main__':
    verify()
