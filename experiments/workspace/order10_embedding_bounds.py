"""Exact sequential embedding bounds that subtract already used vertices.

Every factor is an upper bound for an injective ordinary embedding into
an SRG(v,k,1,2). Pattern nonedges are never assumed to be host nonedges.
The minimum over vertex orders is computed by subset dynamic programming.
"""

import argparse
import hashlib
from itertools import combinations, permutations
import json
from pathlib import Path
import time


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def factor(rows, selected, vertex, vertices, degree):
    bound = vertices-selected.bit_count()
    neighbors = [i for i in range(len(rows)) if selected >> i & 1 and rows[vertex] >> i & 1]
    for u in neighbors:
        bound = min(bound, degree-(rows[u] & selected).bit_count())
    for u, w in combinations(neighbors, 2):
        # If uw is a pattern nonedge, its images might still be adjacent.
        # Two is an upper bound in either host case; an edge forces one.
        quota = 2-int(bool(rows[u] >> w & 1))
        used_common = (rows[u] & rows[w] & selected).bit_count()
        bound = min(bound, quota-used_common)
    return max(0, bound)


def bound(rows, vertices=99, degree=14):
    size = 1 << len(rows)
    costs, last = [None]*size, [None]*size
    costs[0] = 1
    for selected in range(size):
        for vertex in range(len(rows)):
            if selected >> vertex & 1:
                continue
            target = selected | (1 << vertex)
            candidate = costs[selected]*factor(rows, selected, vertex, vertices, degree)
            if costs[target] is None or candidate < costs[target]:
                costs[target], last[target] = candidate, vertex
    order = []
    selected = size-1
    while selected:
        vertex = last[selected]
        order.append(vertex)
        selected ^= 1 << vertex
    order.reverse()
    factors, selected, product = [], 0, 1
    for vertex in order:
        current = factor(rows, selected, vertex, vertices, degree)
        factors.append(current)
        product *= current
        selected |= 1 << vertex
    assert product == costs[-1]
    return product, order, factors


def controls():
    rook = [sum(1 << j for j in range(9) if i != j and (i//3 == j//3 or i % 3 == j % 3))
            for i in range(9)]
    checked = 0
    for order in range(5):
        pairs = list(combinations(range(order), 2))
        for mask in range(1 << len(pairs)):
            rows = [0]*order
            edges = []
            for bit, (i, j) in enumerate(pairs):
                if mask >> bit & 1:
                    rows[i] |= 1 << j
                    rows[j] |= 1 << i
                    edges.append((i, j))
            embeddings = sum(all(rook[image[i]] >> image[j] & 1 for i, j in edges)
                             for image in permutations(range(9), order))
            upper, best, factors = bound(rows, 9, 4)
            assert embeddings <= upper
            # Check every order on this small complete pattern catalogue.
            for choice in permutations(range(order)):
                selected, product = 0, 1
                for vertex in choice:
                    product *= factor(rows, selected, vertex, 9, 4)
                    selected |= 1 << vertex
                assert embeddings <= product and upper <= product
            checked += 1
    assert checked == 76
    return checked


def run(preparation, witness):
    started = time.monotonic()
    base = json.loads(preparation.read_text())
    point = json.loads(witness.read_text())['rounded_core_values']
    assert len(point) == 550 and point[0] == 1
    checked = controls()
    records, violations = [], []
    for j, entry in enumerate(base['upper_bounds'], 1):
        rows = entry['rows']
        product, order, factors = bound(rows)
        aut = entry['automorphisms']
        refined = product//aut
        previous = entry['ordinary_count_upper_bound']
        assert refined <= previous
        assert entry['coordinate'] == j
        record = {'coordinate': j, 'catalogue_type': entry['catalogue_type'], 'rows': rows,
                  'automorphisms': aut, 'optimal_order': order, 'factors': factors,
                  'labelled_embedding_bound': product, 'ordinary_count_upper_bound': refined,
                  'previous_upper_bound': previous, 'saved_count': point[j]}
        records.append(record)
        if point[j] > refined:
            violations.append({'coordinate': j, 'count': point[j], 'upper_bound': refined})
    assert len(records) == 549
    return {'status': 'exact injective embedding bounds computed',
            'source_sha256': digest(Path(__file__)), 'preparation_sha256': digest(preparation),
            'witness_sha256': digest(witness), 'rook_control_patterns': checked,
            'core_coordinates': len(records),
            'strictly_improved_bounds': sum(row['ordinary_count_upper_bound'] < row['previous_upper_bound'] for row in records),
            'witness_bound_violations': violations, 'bounds': records,
            'optimizer_called': False, 'seconds': time.monotonic()-started,
            'scope': 'Necessary individual ordinary-count bounds; no graph-existence conclusion.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--preparation', type=Path, required=True)
    parser.add_argument('--witness', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = run(args.preparation, args.witness)
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({key: value for key, value in result.items() if key != 'bounds'}, indent=2), flush=True)
