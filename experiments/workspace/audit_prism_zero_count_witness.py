"""Independent exact replay of the saved prism-zero order-ten count point.

No finder, repair routine, optimizer, or moment verifier is imported. The
saved induced counts are checked directly against the original identities.
The optional reduction replay also reconstructs all counts from the core
coordinates. This finite count witness is not an adjacency matrix.
"""

import argparse
import hashlib
from itertools import combinations
import json
from math import comb
from pathlib import Path
import pickle
import time

from subgraph_counts import identities


WITNESS_SHA = '62faca107e3f5a7f560c009133e2da563aa16619382b7778f7ff53aa1cd75db7'
CACHE_SHA = '0ad45482ea273b3412e8d308d47eabab366678f4a7e446e4a9f32791c563af65'
CATALOGUE_SHA = '1e1afe93518b0b3707031eed987b19e49bb237ea85e9165ae0f25f2b07a82057'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def has_prism(rows):
    triangles = []
    for a, b, c in combinations(range(len(rows)), 3):
        if rows[a] >> b & 1 and rows[a] >> c & 1 and rows[b] >> c & 1:
            triangles.append((1 << a) | (1 << b) | (1 << c))
    for left, right in combinations(triangles, 2):
        if left & right:
            continue
        if all((rows[i] & right).bit_count() == 1 for i in range(len(rows)) if left >> i & 1):
            if all((rows[i] & left).bit_count() == 1 for i in range(len(rows)) if right >> i & 1):
                return True
    return False


def audit(witness, catalogue, cache=None):
    started = time.monotonic()
    assert digest(witness) == WITNESS_SHA
    assert digest(catalogue) == CATALOGUE_SHA
    saved = json.loads(witness.read_text())
    counts, point = saved['induced_counts'], saved['rounded_core_values']
    assert len(counts) == 48965 and len(point) == 550
    assert all(type(value) is int and value >= 0 for value in counts+point)
    assert point[0] == 1 and point[1] == point[56] == point[57] == 0
    with catalogue.open('rb') as stream:
        data = pickle.load(stream)
    graphs, levels, automorphisms = data[:3]
    assert len(graphs) == len(counts) and len(levels) == 11
    for order, indices in enumerate(levels):
        assert all(len(graphs[i]) == order for i in indices)
        assert sum(counts[i] for i in indices) == comb(99, order)
    checked = 0
    for equation in identities(data, 99, 14):
        assert sum(coefficient*(counts[i-1] if i else 1)
                   for i, coefficient in equation.items()) == 0
        checked += 1
    assert checked == 180445
    containing_prism = [i for i, rows in enumerate(graphs) if has_prism(rows)]
    assert containing_prism and all(counts[i] == 0 for i in containing_prism)
    rebuilt = 0
    if cache is not None:
        assert digest(cache) == CACHE_SHA
        with cache.open('rb') as stream:
            reduced_data, cores, scale, injective, induced = pickle.load(stream)
        assert reduced_data == data and scale == 3628800 and len(cores) == 549
        assert len(graphs[cores[0]]) == 6 and has_prism(graphs[cores[0]])
        for i, row in enumerate(induced):
            numerator = sum(int(coefficient)*point[j] for j, coefficient in enumerate(row) if coefficient)
            assert numerator == scale*counts[i]
            rebuilt += 1
        for j, core in enumerate(cores, 1):
            numerator = sum(int(coefficient)*point[k] for k, coefficient in enumerate(injective[core]) if coefficient)
            assert numerator == automorphisms[core]*point[j]
    return {'status': 'independent exact prism-zero count replay PASS',
            'source_sha256': digest(Path(__file__)), 'witness_sha256': digest(witness),
            'catalogue_sha256': digest(catalogue),
            'reduction_sha256': digest(cache) if cache is not None else None,
            'nonnegative_integral_counts': len(counts), 'original_equations_checked': checked,
            'level_totals_checked': len(levels), 'prism_containing_types_checked_zero': len(containing_prism),
            'counts_reconstructed_from_core_coordinates': rebuilt,
            'ordinary_core_coordinates_reconstructed': 549 if cache is not None else 0,
            'optimizer_called': False, 'finder_imported': False, 'PSD_claimed': False,
            'graph_constructed': False, 'seconds': time.monotonic()-started}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--witness', type=Path, required=True)
    parser.add_argument('--catalogue', type=Path, required=True)
    parser.add_argument('--cache', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.witness, args.catalogue, args.cache)
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2), flush=True)
