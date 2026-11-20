"""Complete 200-row induced-pattern matrix on every high-graph decoration.

Columns with identical exact feature vectors may share one nonnegative
mass. The saved inverse map retains every original graph column. No
optimizer or host-graph symmetry assumption is used.
"""

import argparse
from functools import lru_cache
import hashlib
from itertools import combinations
import json
from math import comb
from pathlib import Path
import resource
import signal
import time

import numpy as np
import pynauty

import grid_free_order10_high_mask_graph_patterns as patterns


ROOT, LOGS = patterns.ROOT, patterns.LOGS
PATTERNS = LOGS / 'order10-high-mask-graph-patterns.json'
PATTERNS_SHA = '86248876874c7b3ded078aec9e189de6f9728302137bb857ffe1500ad519400b'
DOMAIN = LOGS / 'order10-high-mask-graph-domain.json'
DOMAIN_SHA = '39fb9f237327616f83917a15644c36a2f397d5c938720b4dff9278d4262d94f8'
ORBITS = LOGS / 'order10-high-mask-packing-orbits01.json'
ORBITS_SHA = 'a6ca65e8edeb1d4545e89c28833bf7526c693ce6066ec5b6f15a47d31853c61d'
PATTERN_SOURCE_SHA = '9e5714d7570536c347159072456aae2b6bf2d6e90c71a0ae2e58a018f69ca829'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def array_sha(array):
    return hashlib.sha256(array.tobytes(order='C')).hexdigest()


def load_arrays(record):
    path = ROOT / record['arrays']['path']
    assert sha(path) == record['arrays']['sha256']
    with np.load(path, allow_pickle=False) as saved:
        arrays = {name: saved[name] for name in saved.files}
    assert set(arrays) == set(record['array_sha256'])
    assert all(array_sha(value) == record['array_sha256'][name] for name, value in arrays.items())
    return arrays


@lru_cache(maxsize=200000)
def colored_certificate(masks, graph_code):
    rows = patterns.adjacency(masks, graph_code)
    coloring = [set(range(6))]
    if masks:
        coloring.append(set(range(6, len(rows))))
    graph = pynauty.Graph(len(rows), directed=False,
                         adjacency_dict={a: [b for b in range(len(rows)) if row >> b & 1]
                                         for a, row in enumerate(rows)},
                         vertex_coloring=coloring)
    return len(rows), pynauty.certificate(graph)


def prepare(output, arrays_path):
    assert not output.exists() and not arrays_path.exists()
    started = time.monotonic()
    assert sha(Path(patterns.__file__)) == PATTERN_SOURCE_SHA
    for path, expected in ((PATTERNS, PATTERNS_SHA), (DOMAIN, DOMAIN_SHA), (ORBITS, ORBITS_SHA)):
        assert sha(path) == expected
    pattern, domain, orbits = (json.loads(path.read_text()) for path in (PATTERNS, DOMAIN, ORBITS))
    assert pattern['complete'] and domain['complete'] and orbits['complete']
    assert pattern['induced_pattern_row_orbits'] == 200 and domain['graph_decorations'] == 157711
    saved, old = load_arrays(domain), load_arrays(orbits)
    graph_codes, offsets, edges = saved['graph_codes'], saved['atom_offsets'], saved['edge_tables']
    rows = pattern['rows']
    assert len(graph_codes) == 157711 and len(offsets) == 250
    assert [row['row'] for row in rows] == list(range(200))
    tables = {entry['presence_atom_orbit']: entry for entry in pattern['lookup_tables']}
    high = [mask for mask in range(64) if mask.bit_count() >= 3]
    high_index = {mask: i for i, mask in enumerate(high)}
    atom_index = {int(code): i for i, code in enumerate(old['visible_atom_codes'])}
    row_index = {int(code): i for i, code in enumerate(old['row_monomial_codes'])}
    root_generators = old['root_generators']

    @lru_cache(maxsize=None)
    def subset_lookup(masks):
        code = sum(1 << high_index[mask] for mask in masks)
        at = atom_index[code]
        atom_orbit = int(old['atom_labels'][at])
        assert atom_orbit in tables
        permutation = list(range(6))
        current = at
        while old['atom_predecessor'][current] >= 0:
            g = int(old['atom_generator_step'][current])
            permutation = [int(root_generators[g, i]) for i in permutation]
            current = int(old['atom_predecessor'][current])
        assert current == old['atom_representatives'][atom_orbit]
        representative_masks = tables[atom_orbit]['high_masks']
        moved = [patterns.move_mask(mask, permutation) for mask in masks]
        assert sorted(moved) == representative_masks
        vertex_map = [representative_masks.index(mask) for mask in moved]
        table = tables[atom_orbit]['free_graph_code_to_row']
        lookup = np.asarray([table[patterns.move_graph(g, vertex_map)] for g in range(len(table))],
                            dtype=np.int32)
        return atom_orbit, lookup

    matrix = np.zeros((200, len(graph_codes)), dtype=np.uint16)
    row_degrees = np.asarray([row['free_vertices'] for row in rows], dtype=np.int8)
    row_presence = np.asarray([row['presence_atom_orbit'] for row in rows], dtype=np.int32)
    old_row_for_presence = {}
    for identifier, table in tables.items():
        code = sum(1 << high_index[mask] for mask in table['high_masks'])
        old_row_for_presence[identifier] = int(old['row_labels'][row_index[code]])
    assert len(set(old_row_for_presence.values())) == 73
    assert set(old_row_for_presence.values()) == set(map(int, old['active_quotient_rows']))
    subset_tables_used = 0
    control_columns = set()
    for atom in domain['records']:
        identifier = atom['atom_orbit']
        masks = atom['selected_high_masks']
        start, stop = map(int, offsets[identifier:identifier+2])
        codes = graph_codes[start:stop]
        columns = np.arange(start, stop)
        eligible = [tuple(map(int, pair)) for pair in edges[identifier, :atom['eligible_edge_count']]]
        edge_index = {pair: i for i, pair in enumerate(eligible)}
        for degree in range(min(4, len(masks))+1):
            for vertices in combinations(range(len(masks)), degree):
                _, lookup = subset_lookup(tuple(masks[a] for a in vertices))
                small_code = np.zeros(len(codes), dtype=np.uint8)
                for bit, (a, b) in enumerate(combinations(vertices, 2)):
                    if (a, b) in edge_index:
                        small_code |= (((codes >> edge_index[a, b]) & 1) << bit).astype(np.uint8)
                row_ids = lookup[small_code]
                assert np.all(row_ids >= 0)
                matrix[row_ids, columns] += 1
                subset_tables_used += 1
        for degree in range(5):
            expected = comb(len(masks), degree) if degree <= len(masks) else 0
            assert np.all(matrix[row_degrees == degree, start:stop].sum(axis=0) == expected)
        for presence, old_row in old_row_for_presence.items():
            actual = matrix[row_presence == presence, start:stop].sum(axis=0)
            assert np.all(actual == old['quotient_coefficients'][old_row, identifier])
        if len(masks) <= 4:
            control_columns.update(range(start, stop))
        else:
            control_columns.add(start)
            control_columns.add(start+max(range(len(codes)), key=lambda i: int(codes[i]).bit_count()))
        if (identifier+1) % 32 == 0:
            print(json.dumps({'atom_orbits_completed': identifier+1,
                              'graph_columns_completed': stop,
                              'seconds': time.monotonic()-started}), flush=True)
    assert np.all(matrix[0] == 1) and int(matrix.max()) <= 210
    # Independent graph-color canonicalization does not use the root
    # transport paths, subset lookups, or atom-stabilizer tables.
    pattern_index = {colored_certificate(tuple(row['high_masks']), row['canonical_free_graph_code']): row['row']
                     for row in rows}
    assert len(pattern_index) == 200
    literal_subsets = 0
    for column in sorted(control_columns):
        identifier = int(np.searchsorted(offsets, column, side='right')-1)
        atom = domain['records'][identifier]
        masks, code = atom['selected_high_masks'], int(graph_codes[column])
        adjacency = [0]*len(masks)
        for bit, (a, b) in enumerate(edges[identifier, :atom['eligible_edge_count']]):
            a, b = int(a), int(b)
            if code >> bit & 1:
                adjacency[a] |= 1 << b
                adjacency[b] |= 1 << a
        literal = np.zeros(200, dtype=np.uint16)
        for degree in range(min(4, len(masks))+1):
            for vertices in combinations(range(len(masks)), degree):
                free_code = sum(1 << bit for bit, (a, b) in enumerate(combinations(vertices, 2))
                                if adjacency[a] >> b & 1)
                key = colored_certificate(tuple(masks[a] for a in vertices), free_code)
                literal[pattern_index[key]] += 1
                literal_subsets += 1
        assert np.array_equal(literal, matrix[:, column])
    unique, representatives, inverse, multiplicities = np.unique(
        matrix.T, axis=0, return_index=True, return_inverse=True, return_counts=True)
    assert np.array_equal(unique[inverse].T, matrix)
    coefficients = np.ascontiguousarray(unique.T)
    rank_columns = []
    for row in rows:
        identifier = row['presence_atom_orbit']
        pairs = {tuple(pair): bit for bit, pair in enumerate(row['free_pair_order'])}
        atom = domain['records'][identifier]
        code = sum(1 << bit for bit, pair in enumerate(edges[identifier, :atom['eligible_edge_count']])
                   if row['canonical_free_graph_code'] >> pairs[tuple(map(int, pair))] & 1)
        start, stop = map(int, offsets[identifier:identifier+2])
        local = int(np.searchsorted(graph_codes[start:stop], code))
        assert local < stop-start and graph_codes[start+local] == code
        rank_columns.append(int(inverse[start+local]))
    assert len(set(rank_columns)) == 200
    minor = coefficients[:, rank_columns]
    assert np.all(np.diag(minor) == 1)
    for i in range(200):
        for j in range(200):
            if row_degrees[i] > row_degrees[j] or (row_degrees[i] == row_degrees[j] and i != j):
                assert minor[i, j] == 0
    arrays = {'coefficients': coefficients,
              'full_graph_column_to_distinct': inverse.astype(np.uint32),
              'representative_full_graph_columns': representatives.astype(np.uint32),
              'feature_column_multiplicities': multiplicities.astype(np.uint32),
              'row_presence_atom_orbits': row_presence,
              'row_old_presence_equations': np.asarray([old_row_for_presence[int(i)] for i in row_presence], dtype=np.int32),
              'root_label_orbit_sizes': np.asarray([row['root_label_orbit_size'] for row in rows], dtype=np.uint16),
              'row_free_vertices': row_degrees,
              'unimodular_minor_columns': np.asarray(rank_columns, dtype=np.uint32)}
    np.savez_compressed(arrays_path, **arrays)
    report = {'status': 'complete induced-pattern matrix on every graph decoration; no optimizer',
              'complete': True, 'source_sha256': sha(Path(__file__)),
              'pattern_source_sha256': PATTERN_SOURCE_SHA, 'patterns_sha256': PATTERNS_SHA,
              'graph_domain_sha256': DOMAIN_SHA, 'presence_orbits_sha256': ORBITS_SHA,
              'full_matrix_shape': list(matrix.shape), 'distinct_feature_matrix_shape': list(coefficients.shape),
              'full_matrix_nonzeros': int(np.count_nonzero(matrix)),
              'distinct_matrix_nonzeros': int(np.count_nonzero(coefficients)),
              'full_matrix_sha256': array_sha(matrix), 'maximum_integer_coefficient': int(matrix.max()),
              'complete_presence_aggregation_columns_checked': len(graph_codes),
              'presence_equations_checked_per_column': 73,
              'row_degree_partition_checked_on_every_column': True,
              'independent_colored_graph_control_columns': len(control_columns),
              'independent_colored_graph_control_subsets': literal_subsets,
              'colored_canonicalizer': 'pynauty with separate root and free color classes',
              'subset_tables_used': subset_tables_used, 'distinct_subset_tables': subset_lookup.cache_info().currsize,
              'exact_row_rank': 200, 'unimodular_minor_checked': True,
              'quotient_variable': 'total nonnegative mass assigned to a graph feature column',
              'uniform_lift': 'average each representative graph over all 720 root label permutations',
              'row_coefficient': 'number of free-vertex subsets whose induced rooted pattern lies in the row orbit',
              'individual_pattern_lift': 'coefficient divided by the row orbit size',
              'identical_columns_merged_without_domain_loss': True,
              'every_full_graph_has_a_saved_distinct_column_id': True,
              'arrays': {'path': str(arrays_path.resolve().relative_to(ROOT)),
                         'bytes': arrays_path.stat().st_size, 'sha256': sha(arrays_path)},
              'array_sha256': {name: array_sha(value) for name, value in arrays.items()},
              'moments_or_product_tensors_generated': False,
              'host_graph_automorphism_assumed': False, 'optimizer_or_solver_called': False,
              'graph_existence_resolved': False, 'seconds': time.monotonic()-started,
              'peak_rss_kib': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    output.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2), flush=True)
    print('result_sha256', sha(output))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--arrays', type=Path, required=True)
    args = parser.parse_args()
    def deadline(_signum, _frame):
        raise TimeoutError('complete induced-pattern matrix exceeded sixty seconds')
    signal.signal(signal.SIGALRM, deadline)
    signal.setitimer(signal.ITIMER_REAL, 60)
    try:
        prepare(args.output, args.arrays)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
