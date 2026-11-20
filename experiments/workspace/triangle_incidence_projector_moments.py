"""Complete order-ten triangle-incidence projector moments.

Preparation uses no count point. Coefficients count root-labelled
decompositions inside one induced graph, with unlabelled triangle sets.
The query uses exact integer characteristic polynomials and separators.
"""
import argparse
from collections import Counter
from fractions import Fraction
from itertools import combinations, combinations_with_replacement, permutations
import gzip
import hashlib
import json
from math import gcd, lcm
from pathlib import Path
import pickle
import time

import numpy as np
import pynauty
from flint import fmpz_mat
from subgraph_counts import nauty

CATALOGUE_SHA = '1e1afe93518b0b3707031eed987b19e49bb237ea85e9165ae0f25f2b07a82057'
POINT_SHA = '0b78eb2cfc0966f66d72b083f71315e4a079e4b25f59f276c58dd93d189b49df'
LEVELS = [1, 1, 2, 4, 9, 21, 62, 208, 916, 5311, 42430]
ROOT_EDGES = list(combinations(range(4), 2))
PERMUTATIONS = list(permutations(range(4)))


def digest(data):
    return hashlib.sha256(data).hexdigest()


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(',', ':')).encode()


def check_time(deadline):
    if time.monotonic() > deadline:
        raise TimeoutError('Bounded exact triangle-projector phase expired')


def graph_code(rows):
    return sum(((rows[a] >> b) & 1) << i for i, (a, b) in enumerate(ROOT_EDGES))


def cap_valid(rows):
    return all((rows[a] & rows[b]).bit_count() + ((rows[a] >> b) & 1) <= 2
               for a, b in combinations(range(len(rows)), 2))


def induced(rows, vertices):
    return tuple(sum(((rows[a] >> b) & 1) << j for j, b in enumerate(vertices))
                 for a in vertices)


def triangles(rows):
    return [t for t in combinations(range(len(rows)), 3)
            if all((rows[a] >> b) & 1 for a, b in combinations(t, 2))]


def triangle_extension(root, masks):
    rows = list(root) + [0] * 3
    for j, mask in enumerate(masks, 4):
        rows[j] = mask
        for i in range(4):
            if (mask >> i) & 1:
                rows[i] |= 1 << j
    for a, b in combinations(range(4, 7), 2):
        rows[a] |= 1 << b
        rows[b] |= 1 << a
    return tuple(rows)


def domains_and_root_maps(graphs, levels, aut):
    domains = []
    for root_id in levels[4]:
        root = graphs[root_id]
        classes = []
        for masks in combinations_with_replacement(range(16), 3):
            if any(a & b for a, b in combinations(masks, 2)):
                continue
            if cap_valid(triangle_extension(root, masks)):
                zeros = masks.count(0)
                classes.append({'masks': list(masks),
                    'free_label_stabilizer': 6 if zeros == 3 else 2 if zeros == 2 else 1})
        assert len({tuple(c['masks']) for c in classes}) == len(classes)
        canon = min(graph_code(induced(root, p)) for p in PERMUTATIONS)
        domains.append({'root_type': root_id, 'root_rows': list(root),
                        'root_automorphisms': aut[root_id], 'canonical_root_code': canon,
                        'classes': classes})
    expected = {0: 51, 1: 51, 3: 44, 7: 33, 11: 27, 12: 51, 13: 39, 15: 23, 30: 33}
    assert {d['canonical_root_code']: len(d['classes']) for d in domains} == expected
    lookup = {}
    for code in range(64):
        rows = tuple(sum(((code >> k) & 1) << (b if i == a else a)
                         for k, (a, b) in enumerate(ROOT_EDGES) if i in (a, b))
                     for i in range(4))
        if not cap_valid(rows):
            continue
        matches = []
        for d in domains:
            maps = [p for p in PERMUTATIONS if induced(rows, p) == tuple(d['root_rows'])]
            if maps:
                assert len(maps) == d['root_automorphisms']
                matches.append((d['root_type'], maps))
        assert len(matches) == 1
        lookup[code] = matches[0]
    assert len(lookup) == 57 and sum(len(d['classes']) for d in domains) == 352
    assert sum(len(d['classes']) * (len(d['classes']) + 1) // 2 for d in domains) == 7524
    return domains, lookup


def classify(rows, triangle, ordered_root):
    return tuple(sorted(sum(((rows[v] >> u) & 1) << i for i, u in enumerate(ordered_root))
                        for v in triangle))


def kernel(rows, left, right, d=7):
    overlap = len(set(left) & set(right))
    if overlap == 3:
        assert left == right
        return (d - 1) * (d - 2) * (d - 3)
    if overlap == 1:
        return -(d - 2) * (d - 3)
    assert overlap == 0, 'Distinct triangles cannot share an edge'
    cross = sum((rows[a] >> b) & 1 for a in left for b in right)
    assert 0 <= cross <= 3
    return d * cross - 6


def construct(graphs, levels, aut, deadline):
    domains, root_maps = domains_and_root_maps(graphs, levels, aut)
    class_maps = {d['root_type']: {tuple(c['masks']): i for i, c in enumerate(d['classes'])}
                  for d in domains}
    tensors = {d['root_type']: Counter() for d in domains}
    census = Counter()
    samples = {}
    for order in (7, 9, 10):
        for graph_id in levels[order]:
            if graph_id % 256 == 0:
                check_time(deadline)
            rows = graphs[graph_id]
            ts = triangles(rows)
            pairs = [(t, t) for t in ts] if order == 7 else combinations(ts, 2)
            for left, right in pairs:
                union = set(left) | set(right)
                if len(union) != order - 4:
                    continue
                rest = tuple(v for v in range(order) if v not in union)
                root_id, maps = root_maps[graph_code(induced(rows, rest))]
                value = kernel(rows, left, right)
                tag = 'diagonal' if order == 7 else 'intersection' if order == 9 else 'disjoint_' + str((value + 6) // 7)
                samples.setdefault(tag, graph_id)
                census[tag] += 1
                for p in maps:
                    labelled_root = tuple(rest[i] for i in p)
                    a = class_maps[root_id][classify(rows, left, labelled_root)]
                    b = class_maps[root_id][classify(rows, right, labelled_root)]
                    if a < b:
                        a, b = b, a
                    multiplier = 2 if left != right and a == b else 1
                    tensors[root_id][(a * (a + 1) // 2 + b, graph_id)] += multiplier * value
                    census['root_labelled_decompositions'] += 1
    blocks = []
    for d in domains:
        terms = [[entry, graph_id, value] for (entry, graph_id), value in sorted(tensors[d['root_type']].items()) if value]
        n = len(d['classes'])
        assert all(0 <= entry < n * (n + 1) // 2 and type(c) is int for entry, _, c in terms)
        blocks.append({'root_type': d['root_type'], 'order': n, 'lower_entries': n * (n + 1) // 2, 'terms': terms})
    assert set(samples) == {'diagonal', 'intersection', 'disjoint_0', 'disjoint_1', 'disjoint_2', 'disjoint_3'}
    return {'schema': 'conway99.triangle-projector-moments.v1', 'domains': domains, 'blocks': blocks,
            'catalogue_sha256': CATALOGUE_SHA, 'kernel_scale': 210,
            'kernel_entries': {'diagonal': 120, 'one_vertex_intersection': -20, 'disjoint': '7*cross_edges-6'},
            'normalization': 'Unlabelled triangle sets and every labelled root map inside each induced graph; coefficients multiply unlabelled induced counts with no further factor.',
            'census': dict(sorted(census.items())), 'control_graph_ids': samples,
            'count_point_loaded': False, 'optimizer_called': False}, root_maps


def contract(specification, counts):
    out = {}
    for block in specification['blocks']:
        n = block['order']
        lower = [0] * block['lower_entries']
        for entry, graph_id, coefficient in block['terms']:
            lower[entry] += coefficient * counts[graph_id]
        M = [[0] * n for _ in range(n)]
        for a in range(n):
            for b in range(a + 1):
                M[a][b] = M[b][a] = lower[a * (a + 1) // 2 + b]
        out[block['root_type']] = M
    return out


def direct_host(rows, specification, root_maps):
    matrices = {d['root_type']: [[0] * len(d['classes']) for _ in d['classes']]
                for d in specification['domains']}
    classes = {d['root_type']: {tuple(c['masks']): i for i, c in enumerate(d['classes'])}
               for d in specification['domains']}
    ts = triangles(rows)
    for rest in combinations(range(len(rows)), 4):
        root_id, maps = root_maps[graph_code(induced(rows, rest))]
        outside = [t for t in ts if not (set(t) & set(rest))]
        for p in maps:
            labelled = tuple(rest[i] for i in p)
            labels = [classes[root_id][classify(rows, t, labelled)] for t in outside]
            M = matrices[root_id]
            # Ordered pairs here are independent of the unordered tensor constructor.
            for i, left in enumerate(outside):
                for j, right in enumerate(outside):
                    M[labels[i]][labels[j]] += kernel(rows, left, right)
    return matrices


def small_host_controls(data, specification, root_maps, deadline):
    graphs, levels, _, _ = data
    lookup = {(len(graphs[i]), pynauty.certificate(nauty(graphs[i]))): i
              for n in (7, 9) for i in levels[n]}
    reports = []
    for tag, graph_id in sorted(specification['control_graph_ids'].items()):
        check_time(deadline)
        rows = graphs[graph_id]
        counts = [0] * len(graphs)
        for n in (7, 9, 10):
            for vertices in combinations(range(len(rows)), n):
                pos = graph_id if n == len(rows) else lookup[n, pynauty.certificate(nauty(induced(rows, vertices)))]
                counts[pos] += 1
        direct = direct_host(rows, specification, root_maps)
        computed = contract(specification, counts)
        assert direct == computed, (tag, graph_id, 'induced-subset normalization control')
        reports.append({'kind': tag, 'graph_type': graph_id, 'host_order': len(rows),
                        'all_9_blocks_equal': True, 'root_labelled_ordered_triangle_pairs_used': True})
    return reports


def golay_projector_control(deadline):
    from triangle_ball import golay
    A = golay()[0].astype(np.int64)
    assert A.shape == (243, 243) and np.all(A @ A + A == 20 * np.eye(243, dtype=np.int64) + 2)
    rows = tuple(sum(int(x) << j for j, x in enumerate(row)) for row in A)
    ts = triangles(rows)
    assert len(ts) == 891
    B = np.zeros((243, 891), dtype=np.int64)
    for j, t in enumerate(ts):
        B[list(t), j] = 1
    M = 11 * np.eye(243, dtype=np.int64) + A
    assert np.array_equal(B @ B.T, M)
    K = 33 * (10 * np.eye(243, dtype=np.int64) - A) + 2
    assert np.array_equal(M @ K, 2970 * np.eye(243, dtype=np.int64))
    P = 2970 * np.eye(891, dtype=np.int64) - B.T @ K @ B
    assert np.all(P % 3 == 0)
    Q = P // 3
    checked = 0
    for i, left in enumerate(ts):
        if i % 64 == 0:
            check_time(deadline)
        for j in range(i + 1):
            assert int(Q[i, j]) == kernel(rows, left, ts[j], d=11)
            checked += 1
    assert int(np.trace(Q)) == 990 * 648 and np.array_equal(Q, Q.T)
    return {'status': 'PASS: actual Golay point-triangle incidence and inverse identities',
            'vertices': 243, 'triangles': 891, 'projector_rank': 648,
            'projector_scale': 990, 'literal_lower_entries_checked': checked,
            'exact_integer_matrix_arithmetic': True, 'optimizer_called': False}


def load_catalogue(path):
    raw = path.read_bytes()
    assert digest(raw) == CATALOGUE_SHA
    data = pickle.loads(raw)
    assert list(map(len, data[1])) == LEVELS and len(data[0]) == len(data[2]) == 48965
    return data


def prepare(catalogue, directory, seconds):
    started = time.monotonic()
    deadline = started + seconds
    assert not directory.exists()
    data = load_catalogue(catalogue)
    specification, maps = construct(*data[:3], deadline)
    controls = small_host_controls(data, specification, maps, deadline)
    golay = golay_projector_control(deadline)
    raw = canonical(specification)
    compressed = gzip.compress(raw, mtime=0)
    directory.mkdir(parents=True)
    (directory / 'model.json.gz').write_bytes(compressed)
    report = {'status': 'COMPLETE_POINT_INDEPENDENT_TRIANGLE_PROJECTOR_PREPARATION',
              'source_sha256': digest(Path(__file__).read_bytes()), 'catalogue_sha256': CATALOGUE_SHA,
              'model_raw_sha256': digest(raw), 'model_gzip_sha256': digest(compressed),
              'model_raw_bytes': len(raw), 'model_gzip_bytes': len(compressed),
              'root_types': 9, 'classes': 352, 'lower_entries': 7524,
              'tensor_nonzeros': sum(len(b['terms']) for b in specification['blocks']),
              'block_orders': [b['order'] for b in specification['blocks']],
              'census': specification['census'], 'small_host_controls': controls,
              'golay_control': golay, 'seconds': time.monotonic() - started,
              'count_point_loaded': False, 'optimizer_called': False,
              'query_requires_separate_review': True}
    (directory / 'preparation.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2), flush=True)


def exact_negative_vector(M, deadline):
    n = len(M)
    S = [[Fraction(x) for x in row] for row in M]
    T = [[Fraction(i == j) for j in range(n)] for i in range(n)]
    remaining = list(range(n))
    while remaining:
        check_time(deadline)
        negative = next((i for i in remaining if S[i][i] < 0), None)
        if negative is not None:
            v = T[negative]
            break
        pivot = next((i for i in remaining if S[i][i] > 0), None)
        if pivot is None:
            pair = next(((i, j) for i, j in combinations(remaining, 2) if S[i][j]), None)
            assert pair is not None, 'A matrix known non-PSD must expose a negative direction'
            i, j = pair
            sign = -1 if S[i][j] > 0 else 1
            v = [a + sign * b for a, b in zip(T[i], T[j])]
            break
        others = [i for i in remaining if i != pivot]
        ratios = {i: S[i][pivot] / S[pivot][pivot] for i in others}
        for i in others:
            T[i] = [a - ratios[i] * b for a, b in zip(T[i], T[pivot])]
        for i in others:
            for j in others:
                S[i][j] -= ratios[i] * S[pivot][j]
        remaining = others
    else:
        raise AssertionError('Expected an exact negative direction')
    denominator = lcm(*(x.denominator for x in v))
    vector = [int(x * denominator) for x in v]
    divisor = 0
    for x in vector:
        divisor = gcd(divisor, abs(x))
    vector = [x // divisor for x in vector]
    value = sum(vector[i] * M[i][j] * vector[j] for i in range(n) for j in range(n))
    assert value < 0
    return vector, value


def query(directory, point_path, output, seconds):
    started = time.monotonic()
    deadline = started + seconds
    assert not output.exists()
    report = json.loads((directory / 'preparation.json').read_text())
    assert report['source_sha256'] == digest(Path(__file__).read_bytes())
    compressed = (directory / 'model.json.gz').read_bytes()
    raw = gzip.decompress(compressed)
    assert digest(compressed) == report['model_gzip_sha256'] and digest(raw) == report['model_raw_sha256']
    specification = json.loads(raw)
    point_raw = point_path.read_bytes()
    assert digest(point_raw) == POINT_SHA
    point = json.loads(point_raw)
    counts = point['induced_counts']
    assert len(counts) == 48965 and all(type(x) is int and x >= 0 for x in counts)
    matrices = contract(specification, counts)
    results = []
    for block in specification['blocks']:
        check_time(deadline)
        M = matrices[block['root_type']]
        polynomial = list(map(int, fmpz_mat([[-x for x in row] for row in M]).charpoly()))
        assert polynomial[-1] == 1
        result = {'root_type': block['root_type'], 'order': len(M),
                  'matrix': [[str(x) for x in row] for row in M],
                  'det_tI_plus_matrix_coefficients': list(map(str, polynomial)),
                  'exact_positive_semidefinite': all(x >= 0 for x in polynomial)}
        if not result['exact_positive_semidefinite']:
            vector, value = exact_negative_vector(M, deadline)
            form = Counter()
            for entry, graph_id, coefficient in block['terms']:
                a = 0
                while (a + 1) * (a + 2) // 2 <= entry:
                    a += 1
                b = entry - a * (a + 1) // 2
                form[graph_id] += coefficient * vector[a] * vector[b] * (1 if a == b else 2)
            form = {i: c for i, c in form.items() if c}
            assert sum(c * counts[i] for i, c in form.items()) == value < 0
            g = 0
            for c in form.values():
                g = gcd(g, abs(c))
            result.update(integer_negative_vector=list(map(str, vector)),
                          quadratic_value=str(value),
                          primitive_induced_count_inequality=[[i, str(c // g)] for i, c in sorted(form.items())],
                          primitive_value=str(value // g))
        results.append(result)
    terminal = {'status': 'EXACT_TRIANGLE_PROJECTOR_SEPARATORS' if any(not r['exact_positive_semidefinite'] for r in results) else 'EXACT_ALL_NINE_TRIANGLE_PROJECTOR_BLOCKS_PSD',
                'source_sha256': digest(Path(__file__).read_bytes()),
                'preparation_sha256': digest((directory / 'preparation.json').read_bytes()),
                'model_raw_sha256': digest(raw), 'point_sha256': POINT_SHA,
                'blocks': results, 'seconds': time.monotonic() - started,
                'optimizer_called': False, 'unrestricted_existence_resolved': False}
    output.write_text(json.dumps(terminal, indent=2) + '\n')
    print(json.dumps({k: v for k, v in terminal.items() if k != 'blocks'}, indent=2), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='mode', required=True)
    prep = commands.add_parser('prepare')
    prep.add_argument('--catalogue', type=Path, required=True)
    prep.add_argument('--directory', type=Path, required=True)
    prep.add_argument('--seconds', type=float, default=120)
    ask = commands.add_parser('query')
    ask.add_argument('--directory', type=Path, required=True)
    ask.add_argument('--point', type=Path, required=True)
    ask.add_argument('--output', type=Path, required=True)
    ask.add_argument('--seconds', type=float, default=60)
    args = parser.parse_args()
    if args.mode == 'prepare':
        prepare(args.catalogue, args.directory, args.seconds)
    else:
        query(args.directory, args.point, args.output, args.seconds)


if __name__ == '__main__':
    main()
