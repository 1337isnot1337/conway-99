"""Exact sparse sizing for case4 with shared undirected exterior edges.

Preparation only: no optimizer, SAT query, or sparse solver allocation.
The complete row stream is hashed with signed integer coefficients.
"""

import argparse
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import resource
import struct
import time

import complement_rook_35core_case0004_row_loop as previous


ROOT, LOGS = previous.ROOT, previous.LOGS
LOOP_SOURCE_SHA = 'b8992691bf5e56bfdc84450de64c36f43dbd3c0927973f334e00ce2d50f0c16a'
RESULT = LOGS / 'complement-rook-35core-case0004-row-loop-run01.json'
RESULT_SHA = '9b0713b668e2c0ae47139007cdf6ad8961be2fb0e9caf2b42e0193a5528ecaa6'
REPLAY = LOGS / 'complement-rook-35core-case0004-row-loop-replay01.json'
REPLAY_SHA = '0de66ba641844b5ff0b942cc0d1f5c79c5236d41a6eee48b26d3a6694c22ba93'
digest, canonical, portable = previous.digest, previous.canonical, previous.portable


def sha(data):
    return hashlib.sha256(data).hexdigest()


def load_inputs():
    assert digest(Path(previous.__file__)) == LOOP_SOURCE_SHA
    assert digest(RESULT) == RESULT_SHA and digest(REPLAY) == REPLAY_SHA
    original, row_model, seed = previous.load_inputs()
    result, replay = json.loads(RESULT.read_text()), json.loads(REPLAY.read_text())
    assert result['source_sha256'] == LOOP_SOURCE_SHA
    assert replay['source_sha256'] == LOOP_SOURCE_SHA and replay['result_sha256'] == RESULT_SHA
    assert replay['status'] == 'complete base/row-domain and all integer cuts/rays replay PASS'
    assert not replay['exact_case4_exclusion_verified']
    cuts = result['exact_cuts']
    assert cuts[:2] == seed and len(cuts) == 60
    for cut in cuts:
        previous.verify_cut(row_model, cut)
    return original, row_model, cuts


def shared_edges(neighbors, n):
    edges = [(a, b) for a, row in enumerate(neighbors) for b in row if a < b]
    incident = [[] for _ in range(n)]
    for edge_index, (a, b) in enumerate(edges):
        variable = n + edge_index
        incident[a].append((b, variable))
        incident[b].append((a, variable))
    assert edges == sorted(set(edges))
    assert all([b for b, variable in row] == neighbors[a] for a, row in enumerate(incident))
    assert all([variable for b, variable in row] == sorted(variable for b, variable in row) for row in incident)
    return edges, incident


def row_stream(original, row_model, cuts, edges, incident):
    """Yield (kind, label, sense, rhs, sorted(variable, coefficient)).

    sense0 denotes equality; sense1 is an upper inequality. All variables
    are nonnegative. Every y variable is shared by both endpoint rows.
    """
    base_rows, equalities = previous.all_rows(original, cuts)
    for index, row in enumerate(base_rows):
        yield row['kind'], row['label'], int(index >= equalities), row['rhs'], row['terms']
    masks, targets = row_model['column_masks35'], row_model['row_targets36']
    n = len(masks)
    for a in range(n):
        for i in range(35):
            members = [(variable, 1) for b, variable in incident[a] if masks[b] >> i & 1]
            quota = targets[a][i]
            if quota == 0:
                assert not members
                continue  # Exactly the identity0=0; coverage is counted separately.
            yield 'mixed exterior row', [a, i], 0, 0, [(a, -quota)] + members
        yield 'exterior degree row', [a], 0, 0, [(a, -targets[a][-1])] + [(v, 1) for b, v in incident[a]]
    for index, (a, b) in enumerate(edges):
        variable = n + index
        yield 'first endpoint activation', [a, b], 1, 0, [(a, -1), (variable, 1)]
        yield 'second endpoint activation', [a, b], 1, 0, [(b, -1), (variable, 1)]


def controls():
    adjacent = lambda a, b: a != b and (a // 3 == b // 3 or a % 3 == b % 3)
    core_sites, outside = [0, 1, 3, 4, 8], [2, 5, 6, 7]
    core = [sum(1 << j for j, b in enumerate(core_sites) if adjacent(a, b)) for a in core_sites]
    masks = [sum(1 << j for j, b in enumerate(core_sites) if adjacent(a, b)) for a in outside]
    targets, neighbors = previous.separator.prepared.row_domains(core, masks, 4)
    edges, incident = shared_edges(neighbors, 4)
    values = [1] * 4 + [int(adjacent(outside[a], outside[b])) for a, b in edges]
    mixed = degree = activation = 0
    for a in range(4):
        for i in range(5):
            assert sum(values[v] for b, v in incident[a] if masks[b] >> i & 1) == targets[a][i] * values[a]
            mixed += 1
        assert sum(values[v] for b, v in incident[a]) == targets[a][-1] * values[a]
        degree += 1
    for j, (a, b) in enumerate(edges):
        assert values[4+j] <= values[a] and values[4+j] <= values[b]
        activation += 2
    assert sum(sum(values[v] for b, v in row) for row in incident) == 2 * sum(values[4:])
    # A path with three unit degree demands has separate row-box witnesses,
    # but symmetric edge degrees imply y01=y12=1 and y01+y12=1, impossible.
    path_edges, path_incident = shared_edges([[1], [0, 2], [1]], 3)
    assert path_edges == [(0, 1), (1, 2)]
    dual = [1, -1, 1]
    assert all(dual[a] + dual[b] == 0 for a, b in path_edges)
    assert sum(dual) == 1
    return {'rook9_complete_shared_edge_control': True, 'rook9_mixed_equations_checked': mixed,
            'rook9_degree_equations_checked': degree, 'rook9_endpoint_inequalities_checked': activation,
            'each_shared_edge_counted_at_exactly_two_endpoints': True,
            'strictly_stronger_than_independent_degree_boxes_control': True,
            'path_control_is_only_an_algebraic_example_not_a_Conway_core': True,
            'optimizer_or_solver_called': False}


def calculate():
    original, row_model, cuts = load_inputs()
    n = len(row_model['column_masks35'])
    neighbors = row_model['eligible_neighbor_column_ids']
    edges, incident = shared_edges(neighbors, n)
    assert n == 1214 and len(edges) == 275578
    primary_variables = n + len(edges)
    family_rows, family_nnz = Counter(), Counter()
    sense_counts = Counter()
    stream_hash = hashlib.sha256()
    bound_hash = hashlib.sha256()
    row_count = nonzeros = maximum_coefficient = 0
    empty_positive_mixed = []
    for kind, label, sense, rhs, terms in row_stream(original, row_model, cuts, edges, incident):
        assert sense in (0, 1) and type(rhs) is int
        assert [b for b, w in terms] == sorted({b for b, w in terms})
        assert all(type(b) is int and 0 <= b < primary_variables and type(w) is int and w != 0 for b, w in terms)
        maximum_coefficient = max([maximum_coefficient] + [abs(w) for b, w in terms])
        if kind == 'mixed exterior row' and len(terms) == 1:
            empty_positive_mixed.append(label)
        # Signed64-bit little-endian records: sense,rhs,nnz,(column,coefficient)*.
        values = [sense, rhs, len(terms)]
        for b, w in terms:
            values.extend((b, w))
        assert all(-(1 << 63) <= v < 1 << 63 for v in values)
        stream_hash.update(struct.pack('<' + 'q' * len(values), *values))
        bound_hash.update(canonical([kind, label]) + b'\n')
        family_rows[kind] += 1
        family_nnz[kind] += len(terms)
        sense_counts[sense] += 1
        row_count += 1
        nonzeros += len(terms)
    assert maximum_coefficient < 2**53
    targets = row_model['row_targets36']
    trivial = sum(q == 0 for t in targets for q in t[:35])
    assert family_rows['mixed exterior row'] + trivial == 35 * n
    assert family_rows['exterior degree row'] == n
    assert family_rows['first endpoint activation'] == family_rows['second endpoint activation'] == len(edges)
    assert family_nnz['first endpoint activation'] + family_nnz['second endpoint activation'] == 4 * len(edges)
    assert family_nnz['exterior degree row'] == 2 * len(edges) + n
    directed_mixed_entries = sum(len(neighbors[b]) * row_model['column_masks35'][b].bit_count() for b in range(n))
    assert family_nnz['mixed exterior row'] == directed_mixed_entries + family_rows['mixed exterior row']
    assert primary_variables < 2**31 and row_count < 2**31 and nonzeros < 2**31
    basic_vectors = 8 * (3 * primary_variables + 2 * row_count)
    compressed32 = 12 * nonzeros + 4 * (primary_variables + 1)
    compressed64 = 16 * nonzeros + 8 * (primary_variables + 1)
    coo32 = 16 * nonzeros
    inequalities = sense_counts[1]
    return {'status': 'complete exact case4 symmetric exterior-edge LP sizing; no query',
            'source_sha256': digest(Path(__file__)), 'previous_source_sha256': LOOP_SOURCE_SHA,
            'row_loop_result_sha256': RESULT_SHA, 'row_loop_exact_replay_sha256': REPLAY_SHA,
            'row_domain_sha256': previous.separator.MODEL_SHA,
            'original_CNF_sha256': row_model['original_CNF_sha256'],
            'original_real_model_sha256': previous.BASE_SHA,
            'primary_selector_variables': n, 'shared_edge_variables': len(edges),
            'total_LP_variables_without_explicit_slacks': primary_variables,
            'zero_based_edge_variable_rule': 'variable1214+index for edges[index]',
            'complete_eligible_edges': edges, 'edge_domain_sha256': sha(canonical(edges)),
            'retained_exact_row_cut_count': 60, 'retained_binary_no_good_count': 30,
            'counts': {'physical_rows': row_count, 'equalities': sense_counts[0], 'upper_inequalities': inequalities,
                       'physical_matrix_nonzeros': nonzeros, 'zero_mixed_identities_omitted': trivial,
                       'all_mixed_positions_covered': 35 * n, 'all_degree_positions_covered': n,
                       'maximum_absolute_integer_coefficient': maximum_coefficient,
                       'positive_mixed_quotas_with_empty_y_support': empty_positive_mixed,
                       'family_rows': dict(sorted(family_rows.items())), 'family_nonzeros': dict(sorted(family_nnz.items()))},
            'integer_row_stream_sha256': stream_hash.hexdigest(), 'row_label_stream_sha256': bound_hash.hexdigest(),
            'row_stream_format': 'per row: little-endian signed64(sense,rhs,nnz,(column,coefficient)*); sense0 equality,1 upper',
            'variable_lower_bounds': 0, 'explicit_variable_upper_bounds': 'none; selector upper rows plus edge activation imply<=1',
            'explicit_slack_standard_form': {'rows': row_count, 'variables': primary_variables + inequalities,
                                             'nonzeros': nonzeros + inequalities, 'nonnegative_slacks': inequalities},
            'array_memory_bytes': {'CSC_float64_int32': compressed32, 'CSC_float64_int64': compressed64,
                                   'cost_and_column_and_row_bounds_float64': basic_vectors,
                                   'COO_float64_int32_if_materialized': coo32,
                                   'CSC32_plus_basic_vectors': compressed32 + basic_vectors,
                                   'COO32_plus_CSC32_plus_basic_vectors': coo32 + compressed32 + basic_vectors,
                                   'excludes_solver_internal_copies_factorization_and_Python_objects': True},
            'all_coefficients_exactly_representable_in_float64': True,
            'complete_general_row_stream_recomputed': True, 'sparse_solver_matrix_allocated': False,
            'symmetry_equalities_on_graph_or_incidence': False,
            'edge_symmetry': 'One variable per unordered pair, reused at both endpoints',
            'pair_caps_added': False, 'LP_or_SAT_query_called': False,
            'sixty_cut_SAT_alternative_preserved_without_encoding_or_query': True,
            'controls': controls(),
            'scope': 'Necessary fractional relaxation of actual completions of indexed35-core case4; '
                     'all original margins/capacities,30 binary no-goods and60 row cuts retained. '
                     'No feasibility or exclusion claim.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--replay', type=Path)
    args = parser.parse_args()
    assert not args.output.exists()
    started = time.monotonic()
    result = calculate()
    if args.replay:
        expected = json.loads(gzip.decompress(args.replay.read_bytes()))
        assert json.loads(canonical(result)) == expected
        result = {'status': 'complete sparse row/edge inventory replay PASS; no optimizer',
                  'source_sha256': result['source_sha256'], 'preparation_sha256': digest(args.replay),
                  'integer_row_stream_sha256': result['integer_row_stream_sha256'], 'counts': result['counts']}
    raw = canonical(result) + b'\n'
    args.output.write_bytes(gzip.compress(raw, mtime=0) if args.output.suffix == '.gz' else raw)
    print(json.dumps({key: value for key, value in result.items() if key != 'complete_eligible_edges'}, indent=2))
    print('output_sha256', digest(args.output))
    print('elapsed_seconds', time.monotonic() - started)
    print('peak_rss_kib', resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
