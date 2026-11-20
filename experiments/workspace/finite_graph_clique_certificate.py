"""Exact clique numbers for simple graphs of at most twelve vertices.

The certificate stores the elementary deletion/neighborhood recurrence on
only the subsets visited.  Replay checks every recurrence without search.
This helper has no graph-domain, optimization, or symmetry assumptions.
"""
from itertools import combinations


def validate(adjacency):
    n = len(adjacency)
    assert 0 <= n <= 12
    assert all(type(row) is int and 0 <= row < (1 << n) for row in adjacency)
    assert all(not (adjacency[i] >> i) & 1 for i in range(n))
    assert all(((adjacency[i] >> j) & 1) == ((adjacency[j] >> i) & 1)
               for i in range(n) for j in range(n))
    return n


def is_clique(adjacency, vertices):
    return all(adjacency[a] & (1 << b) for a, b in combinations(vertices, 2))


def maximum_clique(adjacency, check=lambda: None):
    n = validate(adjacency)
    values = {0: 0}

    def visit(mask):
        if mask in values:
            return values[mask]
        if len(values) % 32 == 0:
            check()
        bit = mask & -mask
        vertex = bit.bit_length() - 1
        rest = mask ^ bit
        values[mask] = max(visit(rest), 1 + visit(rest & adjacency[vertex]))
        return values[mask]

    check()
    mask = (1 << n) - 1
    optimum = visit(mask)
    clique = []
    while mask:
        bit = mask & -mask
        vertex = bit.bit_length() - 1
        rest = mask ^ bit
        neighbors = rest & adjacency[vertex]
        if 1 + values[neighbors] >= values[rest]:
            clique.append(vertex)
            mask = neighbors
        else:
            mask = rest
    certificate = {"vertex_count": n, "maximum": optimum, "clique": clique,
                   "subset_values": [[mask, values[mask]] for mask in sorted(values)]}
    verify(adjacency, certificate)
    return certificate


def verify(adjacency, certificate):
    n = validate(adjacency)
    assert certificate["vertex_count"] == n
    rows = certificate["subset_values"]
    assert all(len(row) == 2 and all(type(x) is int for x in row) for row in rows)
    assert rows == sorted(rows) and len({row[0] for row in rows}) == len(rows)
    values = dict(rows)
    assert values.get(0) == 0
    assert all(0 <= mask < (1 << n) and 0 <= value <= mask.bit_count()
               for mask, value in rows)
    reachable = set()
    stack = [(1 << n) - 1]
    while stack:
        mask = stack.pop()
        if mask in reachable:
            continue
        reachable.add(mask)
        assert mask in values
        if not mask:
            continue
        bit = mask & -mask
        vertex = bit.bit_length() - 1
        rest = mask ^ bit
        neighbors = rest & adjacency[vertex]
        assert rest in values and neighbors in values
        assert values[mask] == max(values[rest], 1 + values[neighbors])
        stack.extend((rest, neighbors))
    assert reachable == set(values)
    optimum = values[(1 << n) - 1]
    assert type(certificate["maximum"]) is int and certificate["maximum"] == optimum
    clique = certificate["clique"]
    assert clique == sorted(set(clique)) and all(type(v) is int and 0 <= v < n for v in clique)
    assert len(clique) == optimum and is_clique(adjacency, clique)
    return optimum


def controls():
    checked_graphs = checked_subsets = 0
    for n in range(6):
        edges = list(combinations(range(n), 2))
        for edge_bits in range(1 << len(edges)):
            adjacency = [0] * n
            for i, (a, b) in enumerate(edges):
                if (edge_bits >> i) & 1:
                    adjacency[a] |= 1 << b
                    adjacency[b] |= 1 << a
            exact = 0
            for mask in range(1 << n):
                vertices = [v for v in range(n) if (mask >> v) & 1]
                if all((edge_bits >> edges.index((a, b))) & 1
                       for a, b in combinations(vertices, 2)):
                    exact = max(exact, len(vertices))
                checked_subsets += 1
            certificate = maximum_clique(adjacency)
            assert verify(adjacency, certificate) == exact
            checked_graphs += 1
    # A changed top value and a missing necessary recurrence must be rejected.
    sample = maximum_clique([2, 1, 0])
    for altered in [dict(sample, maximum=3), dict(sample, subset_values=sample["subset_values"][1:])]:
        try:
            verify([2, 1, 0], altered)
        except AssertionError:
            pass
        else:
            raise AssertionError("corrupted clique certificate accepted")
    assert checked_graphs == 1100
    return {"complete_graphs_through_five_vertices": checked_graphs,
            "independent_exhaustive_subsets": checked_subsets,
            "corrupted_certificates_rejected": 2, "optimizer_calls": 0}
