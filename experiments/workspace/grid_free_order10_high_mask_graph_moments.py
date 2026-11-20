"""Direct exact moments for all 200 induced high-graph row patterns.

The independent normalization check counts literal ordered root embeddings
in each pattern graph. The construction uses only the small catalogue and
the bound integer count point, with no product tensor or optimizer.
"""

import argparse
from collections import Counter, defaultdict
from functools import lru_cache
import hashlib
from itertools import combinations, permutations
import json
from pathlib import Path
import pickle
import resource
import signal
import time

import numpy as np
import pynauty


ROOT = Path(__file__).resolve().parents[2]
LOGS = ROOT/'experiments/logs/moments-and-counts'
PATTERNS = LOGS/'order10-high-mask-graph-patterns.json'
PATTERNS_SHA = '86248876874c7b3ded078aec9e189de6f9728302137bb857ffe1500ad519400b'
PATTERN_SOURCE = ROOT/'experiments/workspace/grid_free_order10_high_mask_graph_patterns.py'
PATTERN_SOURCE_SHA = '9e5714d7570536c347159072456aae2b6bf2d6e90c71a0ae2e58a018f69ca829'
CATALOGUE = Path('/tmp/conway99-order10-catalogue.pickle')
CATALOGUE_SHA = '1e1afe93518b0b3707031eed987b19e49bb237ea85e9165ae0f25f2b07a82057'
POINT = LOGS/'prism-zero-order10-all-flags-x521-face-loop01-round0-rounded-counts.json'
POINT_SHA = '0b78eb2cfc0966f66d72b083f71315e4a079e4b25f59f276c58dd93d189b49df'
PRESENCE = LOGS/'order10-high-mask-packing-orbits01.json'
PRESENCE_SHA = 'a6ca65e8edeb1d4545e89c28833bf7526c693ce6066ec5b6f15a47d31853c61d'
ROOT_ORDERS = tuple(permutations(range(6)))
HIGH = tuple(mask for mask in range(64) if mask.bit_count() >= 3)
HIGH_INDEX = {mask: i for i, mask in enumerate(HIGH)}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_json(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode()


def valid(rows):
    return all((rows[i]&rows[j]).bit_count()+((rows[i] >> j)&1) <= 2
               for i in range(len(rows)) for j in range(i))


def adjacency(masks, code):
    n = 6+len(masks)
    free_pairs = {pair: bit for bit, pair in enumerate(combinations(range(len(masks)), 2))}
    rows = [0]*n
    for i, j in combinations(range(n), 2):
        if j < 6:
            edge = 0
        elif i < 6:
            edge = (masks[j-6] >> i)&1
        else:
            edge = (code >> free_pairs[i-6, j-6])&1
        if edge:
            rows[i] |= 1 << j
            rows[j] |= 1 << i
    return tuple(rows)


def induced(rows, vertices):
    return tuple(sum(((rows[a] >> b)&1) << j for j, b in enumerate(vertices))
                 for a in vertices)


def signature(rows):
    return len(rows), tuple(sorted(row.bit_count() for row in rows))


@lru_cache(maxsize=60000)
def canonical(rows):
    graph = pynauty.Graph(len(rows), directed=False,
        adjacency_dict={i: [j for j in range(len(rows)) if row >> j & 1]
                        for i, row in enumerate(rows)})
    return len(rows), pynauty.certificate(graph)


def outside_classes(rows, root_order):
    root_set = set(root_order)
    answer = {}
    for vertex in range(len(rows)):
        if vertex in root_set:
            continue
        mask = sum(((rows[vertex] >> root_order[i])&1) << i for i in range(6))
        if mask.bit_count() >= 3:
            assert mask not in answer
            answer[mask] = vertex
    return answer


def graph_code(rows, ordered_vertices):
    return sum(((rows[a] >> b)&1) << bit
               for bit, (a, b) in enumerate(combinations(ordered_vertices, 2)))


def root_pattern_key(rows, root_order):
    classes = outside_classes(rows, root_order)
    if len(classes) != len(rows)-6:
        return None
    masks = tuple(sorted(classes))
    return masks, graph_code(rows, [classes[mask] for mask in masks])


def literal_pattern_audit(record):
    masks = tuple(record['high_masks'])
    q, code = len(masks), record['canonical_free_graph_code']
    assert 0 <= q <= 4 and masks == tuple(sorted(set(masks)))
    assert all(mask in HIGH_INDEX for mask in masks)
    assert record['free_vertices'] == q
    assert record['high_class_code'] == sum(1 << HIGH_INDEX[mask] for mask in masks)
    assert record['free_pair_order'] == [list(pair) for pair in combinations(range(q), 2)]
    rows = adjacency(masks, code)
    assert list(rows) == record['core_plus_free_adjacency_rows'] and valid(rows)
    target = masks, code
    images = Counter(root_pattern_key(rows, order) for order in ROOT_ORDERS)
    assert None not in images
    assert len(images) == record['root_label_orbit_size']
    assert images[target] == record['root_stabilizer_size']
    assert set(images.values()) == {record['root_stabilizer_size']}
    assert len(images)*images[target] == 720
    fixed_mask_codes = sorted(edge_code for (image_masks, edge_code) in images if image_masks == masks)
    assert fixed_mask_codes == record['graph_codes_in_atom_stabilizer_orbit']
    assert len(fixed_mask_codes) == record['free_graph_orbit_size_under_atom_stabilizer']
    root_sets, matching_root_sets, embeddings, checked_orders = [], [], 0, 0
    for root_set in combinations(range(len(rows)), 6):
        if any(rows[a] >> b & 1 for a, b in combinations(root_set, 2)):
            continue
        root_sets.append(list(root_set))
        if root_set == tuple(range(6)):
            count = images[target]
            checked_orders += 720
        else:
            count = 0
            for order in permutations(root_set):
                count += root_pattern_key(rows, order) == target
                checked_orders += 1
        if count:
            assert count == images[target]
            matching_root_sets.append(list(root_set))
            embeddings += count
    assert embeddings == len(matching_root_sets)*images[target]
    assert embeddings > 0
    return {'row': record['row'], 'literal_root_orbit_size': len(images),
        'literal_root_stabilizer_size': images[target],
        'root_orbit_key_sha256': hashlib.sha256(canonical_json(sorted(images))).hexdigest(),
        'independent_six_sets': root_sets, 'six_sets_in_target_rooted_orbit': matching_root_sets,
        'ordered_root_embeddings_checked': checked_orders,
        'literal_pattern_indicator_sum_on_itself': embeddings,
        'independently_derived_full_graph_automorphism_order': embeddings,
        'free_class_uniqueness_verified': True}, rows, set(images)


def literal_indicator_sum(host, masks, code):
    answer, root_orders = 0, 0
    assert valid(host)
    for root_set in combinations(range(len(host)), 6):
        if any(host[a] >> b & 1 for a, b in combinations(root_set, 2)):
            continue
        for order in permutations(root_set):
            classes = outside_classes(host, order)
            if all(mask in classes for mask in masks):
                answer += graph_code(host, [classes[mask] for mask in masks]) == code
            root_orders += 1
    return answer, root_orders


def extended_host_controls(records):
    selected = [records[0]]
    for q in (1, 2):
        selected.append(next(r for r in records if r['free_vertices'] == q and
                             r['canonical_free_graph_code'] == 0))
    answer = []
    for record in selected:
        rows = tuple(record['core_plus_free_adjacency_rows'])
        host = rows+(0,)
        target = canonical(rows)
        copies = sum(canonical(induced(host, subset)) == target
                     for subset in combinations(range(len(host)), len(rows)))
        observed, orders = literal_indicator_sum(host, record['high_masks'],
                                                record['canonical_free_graph_code'])
        expected = record['catalogue_automorphism_order']*copies
        assert observed == expected
        answer.append({'pattern_row': record['row'], 'host_rows': list(host),
            'induced_copies_of_pattern_graph': copies, 'literal_root_orders_checked': orders,
            'literal_pattern_indicator_sum': observed, 'aut_times_induced_copies': expected})
    return answer


def prepare(result):
    assert digest(PATTERNS) == PATTERNS_SHA and digest(PATTERN_SOURCE) == PATTERN_SOURCE_SHA
    assert digest(CATALOGUE) == CATALOGUE_SHA and digest(POINT) == POINT_SHA
    assert digest(PRESENCE) == PRESENCE_SHA
    patterns = json.loads(PATTERNS.read_text())
    assert patterns['complete'] and patterns['source_sha256'] == PATTERN_SOURCE_SHA
    assert patterns['root_adjacency_rows'] == [0]*6
    assert patterns['root_permutations'] == [list(p) for p in ROOT_ORDERS]
    assert [r['row'] for r in patterns['rows']] == list(range(200))
    assert len(patterns['lookup_tables']) == 73
    point = json.loads(POINT.read_text())
    counts = point['induced_counts']
    assert len(counts) == 48965 and all(type(value) is int and value >= 0 for value in counts)
    assert point['exact_count_and_held_cut_witness'] and point['x521_zero']
    catalogue = pickle.loads(CATALOGUE.read_bytes())
    assert len(catalogue[0]) == len(catalogue[2]) == 48965
    presence = json.loads(PRESENCE.read_text())
    assert presence['complete'] and presence['integer_count_point_sha256'] == POINT_SHA
    array_path = ROOT/presence['arrays']['path']
    assert digest(array_path) == presence['arrays']['sha256']
    with np.load(array_path, allow_pickle=False) as saved:
        old = {name: saved[name] for name in saved.files}
    for name, array in old.items():
        assert hashlib.sha256(array.tobytes(order='C')).hexdigest() == presence['array_sha256'][name]

    audits, graphs, images = [], [], []
    all_images = set()
    for record in patterns['rows']:
        audit, graph, orbit = literal_pattern_audit(record)
        assert not all_images.intersection(orbit)
        all_images.update(orbit)
        audits.append(audit); graphs.append(graph); images.append(orbit)
    needed_signatures = {signature(graph) for graph in graphs}
    buckets = defaultdict(list)
    for index, rows in enumerate(catalogue[0]):
        key = signature(rows)
        if key in needed_signatures:
            buckets[key].append(index)
    ids = {}
    for indices in buckets.values():
        for index in indices:
            key = canonical(tuple(catalogue[0][index]))
            assert key not in ids
            ids[key] = index
    row_of_code = {int(code): i for i, code in enumerate(old['row_monomial_codes'])}
    records = []
    for original, audit, graph in zip(patterns['rows'], audits, graphs):
        index = ids[canonical(graph)]
        automorphisms = int(catalogue[2][index])
        assert automorphisms == audit['independently_derived_full_graph_automorphism_order']
        assert canonical(tuple(catalogue[0][index])) == canonical(graph)
        atom_orbit = original['presence_atom_orbit']
        local_atom = int(old['atom_representatives'][atom_orbit])
        class_code = int(old['visible_atom_codes'][local_atom])
        assert class_code == original['high_class_code']
        old_row = int(old['row_labels'][row_of_code[class_code]])
        old_size = int(old['row_sizes'][old_row])
        assert old_size == int(old['atom_sizes'][atom_orbit])
        fixed_moment = automorphisms*counts[index]
        rhs = original['root_label_orbit_size']*fixed_moment
        assert 0 <= fixed_moment <= presence['root_labelled_embedding_mass']
        assert original['root_label_orbit_size'] == old_size*len(original['graph_codes_in_atom_stabilizer_orbit'])
        record = {**original, 'catalogue_type': index, 'catalogue_automorphism_order': automorphisms,
            'saved_induced_count': counts[index], 'fixed_pattern_moment': fixed_moment,
            'quotient_row_rhs': rhs, 'labelled_root_orbit_coefficient': original['root_label_orbit_size']*automorphisms,
            'direct_induced_count_form': [[index, original['root_label_orbit_size']*automorphisms]],
            'old_presence_row_orbit': old_row, 'old_presence_row_orbit_size': old_size,
            'independent_literal_audit': audit}
        records.append(record)
    # Independently check every possible mutual-edge prescription on each
    # fixed presence representative, including all forbidden prescriptions.
    graph_choices = 0
    for table in patterns['lookup_tables']:
        masks = tuple(table['high_masks'])
        lookup = table['free_graph_code_to_row']
        assert len(lookup) == 1 << (len(masks)*(len(masks)-1)//2)
        for code, row in enumerate(lookup):
            allowed = valid(adjacency(masks, code))
            assert allowed == (row >= 0)
            if allowed:
                assert records[row]['presence_atom_orbit'] == table['presence_atom_orbit']
                assert (masks, code) in images[row]
                assert code in records[row]['graph_codes_in_atom_stabilizer_orbit']
                graph_choices += 1
    assert graph_choices == 279

    aggregations = []
    by_presence = defaultdict(list)
    for record in records:
        by_presence[record['old_presence_row_orbit']].append(record)
    assert sorted(by_presence) == old['active_quotient_rows'].tolist()
    for row in old['active_quotient_rows']:
        row = int(row)
        entries = by_presence[row]
        new_rhs = sum(r['quotient_row_rhs'] for r in entries)
        expected = int(old['quotient_rhs'][row])
        assert new_rhs == expected
        fixed_sum = sum(r['free_graph_orbit_size_under_atom_stabilizer']*r['fixed_pattern_moment']
                        for r in entries)
        assert fixed_sum*int(old['row_sizes'][row]) == expected
        aggregations.append({'old_presence_row_orbit': row,
            'presence_atom_orbit': entries[0]['presence_atom_orbit'],
            'decorated_rows': [r['row'] for r in entries], 'summed_decorated_rhs': new_rhs,
            'old_presence_rhs': expected, 'fixed_mask_moment_sum': fixed_sum,
            'old_presence_orbit_size': int(old['row_sizes'][row]), 'exact_match': True})
    controls = extended_host_controls(records)
    result.update(complete=True, status='complete direct decorated-pattern moments and literal normalization audit',
        rows=records, aggregations=aggregations, extended_host_controls=controls,
        quotient_rhs=[r['quotient_row_rhs'] for r in records],
        summary={'pattern_row_orbits': 200, 'labelled_decorations_on_presence_representatives': 279,
            'full_root_labelled_pattern_count': len(all_images),
            'literal_root_order_checks': sum(a['ordered_root_embeddings_checked'] for a in audits),
            'catalogue_candidates_canonicalized': len(ids),
            'distinct_unrooted_catalogue_types': len({r['catalogue_type'] for r in records}),
            'direct_automorphism_order_matches': 200, 'presence_rhs_aggregations': 73,
            'zero_decorated_rows_at_point': sum(r['quotient_row_rhs'] == 0 for r in records),
            'maximum_rhs': max(r['quotient_row_rhs'] for r in records),
            'root_labelled_embedding_mass': presence['root_labelled_embedding_mass'],
            'coefficient_histogram': dict(Counter(str(r['labelled_root_orbit_coefficient']) for r in records)),
            'independent_six_set_count_histogram': dict(Counter(str(len(a['independent_six_sets'])) for a in audits))},
        cache_product_tensors_loaded=False, reduced_count_matrix_loaded=False,
        full_graph_domain_coefficient_aggregation_checked=False,
        moment_forms_are_single_induced_count_coordinates=True,
        free_label_or_root_stabilizer_division_applied=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--replay', type=Path)
    parser.add_argument('--seconds', type=int, default=60)
    args = parser.parse_args()
    assert 0 < args.seconds <= 60 and not args.output.exists()
    started = time.monotonic()
    result = {'status': 'running direct high-graph moment preparation', 'complete': False,
        'source_sha256': digest(Path(__file__)), 'pattern_sha256': PATTERNS_SHA,
        'pattern_source_sha256': PATTERN_SOURCE_SHA, 'catalogue_sha256': CATALOGUE_SHA,
        'integer_count_point_sha256': POINT_SHA, 'presence_orbit_result_sha256': PRESENCE_SHA,
        'requested_seconds': args.seconds, 'optimizer_or_solver_called': False,
        'new_product_tensor_generated': False, 'graph_existence_resolved': False}
    def deadline(_signum, _frame):
        raise TimeoutError('bounded direct graph-pattern moment preparation')
    previous = signal.signal(signal.SIGALRM, deadline)
    signal.setitimer(signal.ITIMER_REAL, args.seconds)
    error, timed_out = None, False
    try:
        prepare(result)
        if args.replay:
            expected = json.loads(args.replay.read_text())
            for key, value in result.items():
                assert expected[key] == value
            result = {'status': 'PASS: cold direct moment and literal normalization replay',
                'complete': True, 'source_sha256': digest(Path(__file__)),
                'replayed_result_sha256': digest(args.replay), 'summary': result['summary'],
                'optimizer_or_solver_called': False, 'graph_existence_resolved': False}
    except TimeoutError:
        timed_out = True
        result.update(status='UNKNOWN: incomplete direct moment preparation', complete=False)
    except Exception as problem:
        error = repr(problem)
        result.update(status='ERROR: direct moment preparation failed', complete=False, error=error)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)
    result.update(seconds=time.monotonic()-started, timed_out=timed_out,
                  peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k: v for k, v in result.items() if k not in
                     ('rows', 'aggregations', 'extended_host_controls', 'quotient_rhs')}, indent=2), flush=True)
    print('output_sha256', digest(args.output), flush=True)
    raise SystemExit(int(error is not None))


if __name__ == '__main__':
    main()
