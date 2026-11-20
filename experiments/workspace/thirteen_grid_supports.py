"""Classify the eight missing axis pairs at a root with thirteen grids."""

import pynauty

from root_cell_profiles import RootCells


def certificate(size, edges):
    adj = {i: [] for i in range(size)}
    for a, b in edges:
        adj[a].append(b)
        adj[b].append(a)
    return pynauty.certificate(pynauty.Graph(size, adjacency_dict=adj))


def unlabelled_graphs():
    # Delete the last vertex to see that extending all smaller graphs is exhaustive.
    graphs = [()]
    for n in range(1, 8):
        found = {}
        for old in graphs:
            for mask in range(1 << (n - 1)):
                edges = old + tuple((j, n - 1) for j in range(n - 1) if mask & (1 << j))
                found.setdefault(certificate(n, edges), edges)
        graphs = found.values()
    assert len(graphs) == 1044
    return graphs


def bipartite_components(edges):
    adj = [set() for _ in range(7)]
    for a, b in edges:
        adj[a].add(b)
        adj[b].add(a)
    colors = {}
    count = 0
    for root in range(7):
        if root in colors:
            continue
        colors[root] = 0
        stack = [root]
        bipartite = True
        while stack:
            a = stack.pop()
            for b in adj[a]:
                if b not in colors:
                    colors[b] = 1 - colors[a]
                    stack.append(b)
                elif colors[a] == colors[b]:
                    bipartite = False
        count += bipartite
    return count


def main():
    bipartite_24 = tuple((a, b) for a in range(2) for b in range(2, 6))
    bipartite_33_minus_edge = tuple((a, b) for a in range(3) for b in range(3, 6)
                                     if (a, b) != (0, 3))
    exceptions = {certificate(7, edges) for edges in (bipartite_24, bipartite_33_minus_edge)}
    supports = skipped = populations = 0
    for edges in unlabelled_graphs():
        if len(edges) != 8 or len({a for e in edges for a in e}) < 6:
            continue
        rank_defect = bipartite_components(edges)
        if any(bipartite_components(edges[:i] + edges[i+1:]) != rank_defect
               for i in range(8)):
            continue
        supports += 1
        if certificate(7, edges) in exceptions:
            skipped += 1
            continue
        cells = RootCells(sorted(edges))
        domains = [cells.cell_options(i) for i in range(21)]
        for p in cells.populations(domains):
            populations += 1
            assert not all(cells.permits_eigenvectors(p, i, tuple(range(8))) for i in range(21))
        cells.contributions.cache_clear()
    assert (supports, skipped, populations) == (12, 2, 2)
    print('Eight missing edges: 12 supports, 10 excluded, leaving K2,4 and K3,3 minus an edge.')


if __name__ == '__main__':
    main()
