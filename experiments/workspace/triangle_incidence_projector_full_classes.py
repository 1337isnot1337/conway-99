"""Extend the four-root triangle-projector blocks to every triangle class.

The old disjoint-triangle tensor is an exact principal submatrix. New
entries only use induced graphs of orders four through nine. Preparation
does not load a count point. No optimizer is used anywhere in this file.
"""
import argparse
from collections import Counter
import gzip
from itertools import combinations, combinations_with_replacement
import json
from pathlib import Path
import time

from flint import fmpz_mat
import pynauty

import triangle_incidence_projector_moments as base

BASE_SOURCE_SHA = '1e7a8b7380314d6dfd8ff05954a13662bc011378f5759ad675ec1bc281fa19e9'
BASE_MODEL_SHA = '2df4f8ad6453ec7af232692518b651f964289b57c752a8881b4f57054e84c17a'


def check_base(directory):
    assert base.digest(Path(base.__file__).read_bytes()) == BASE_SOURCE_SHA
    report = json.loads((directory / 'preparation.json').read_text())
    compressed = (directory / 'model.json.gz').read_bytes()
    raw = gzip.decompress(compressed)
    assert base.digest(raw) == BASE_MODEL_SHA == report['model_raw_sha256']
    assert base.digest(compressed) == report['model_gzip_sha256']
    assert report['source_sha256'] == BASE_SOURCE_SHA
    return json.loads(raw)


def class_key(record):
    return record['root_intersection_mask'], tuple(record['outside_masks'])


def full_classify(rows, triangle, labelled_root):
    root_set = set(labelled_root)
    inside = sum(1 << i for i, v in enumerate(labelled_root) if v in triangle)
    outside = tuple(sorted(sum(((rows[v] >> u) & 1) << i
                               for i, u in enumerate(labelled_root))
                           for v in triangle if v not in root_set))
    assert inside.bit_count() + len(outside) == 3
    return inside, outside


def extension(root, inside, masks):
    vertices = [i for i in range(4) if (inside >> i) & 1]
    assert len(vertices) + len(masks) == 3
    if not all((root[a] >> b) & 1 for a, b in combinations(vertices, 2)):
        return None
    if not all(mask & inside == inside for mask in masks):
        return None
    rows = list(root) + [0] * len(masks)
    for j, mask in enumerate(masks, 4):
        rows[j] = mask
        for i in range(4):
            if (mask >> i) & 1:
                rows[i] |= 1 << j
    for a, b in combinations(range(4, len(rows)), 2):
        rows[a] |= 1 << b
        rows[b] |= 1 << a
    return tuple(rows)


def full_domains(old):
    domains = []
    for item in old['domains']:
        classes = [{'root_intersection_mask': 0, 'outside_masks': c['masks']}
                   for c in item['classes']]
        disjoint = len(classes)
        for size in (1, 2, 3):
            for vertices in combinations(range(4), size):
                inside = sum(1 << v for v in vertices)
                eligible = [m for m in range(16) if m & inside == inside]
                for masks in combinations_with_replacement(eligible, 3-size):
                    rows = extension(item['root_rows'], inside, masks)
                    if rows is not None and base.cap_valid(rows):
                        classes.append({'root_intersection_mask': inside,
                                        'outside_masks': list(masks)})
        assert len({class_key(c) for c in classes}) == len(classes)
        for c in classes:
            rows = extension(item['root_rows'], *class_key(c))
            assert rows is not None and base.cap_valid(rows)
            triangle = tuple(i for i in range(4) if c['root_intersection_mask'] & (1 << i)) + tuple(range(4, len(rows)))
            assert triangle in base.triangles(rows)
            assert full_classify(rows, triangle, tuple(range(4))) == class_key(c)
        domains.append({k: v for k, v in item.items() if k != 'classes'} |
                       {'classes': classes, 'disjoint_principal_order': disjoint,
                        'class_intersection_census': dict(sorted(Counter(c['root_intersection_mask'].bit_count() for c in classes).items()))})
    return domains


def construct(data, old, deadline):
    graphs, levels, aut, _ = data
    original_domains, root_maps = base.domains_and_root_maps(graphs, levels, aut)
    assert original_domains == old['domains']
    domains = full_domains(old)
    class_maps = {d['root_type']: {class_key(c): i for i, c in enumerate(d['classes'])}
                  for d in domains}
    tensors = {block['root_type']: Counter({(entry, graph): value for entry, graph, value in block['terms']})
               for block in old['blocks']}
    census = Counter()
    samples = {}
    for order in range(4, 10):
        for graph_id in levels[order]:
            if graph_id % 128 == 0:
                base.check_time(deadline)
            rows = graphs[graph_id]
            ts = base.triangles(rows)
            for ti, left in enumerate(ts):
                for right in ts[:ti+1]:
                    union = set(left) | set(right)
                    extra_count = 4 + len(union) - order
                    if extra_count <= 0 or extra_count > min(4, len(union)):
                        continue
                    rest = tuple(v for v in range(order) if v not in union)
                    value = base.kernel(rows, left, right)
                    for extra in combinations(sorted(union), extra_count):
                        root = tuple(sorted(rest + extra))
                        assert len(root) == 4 and set(root) | union == set(range(order))
                        root_id, maps = root_maps[base.graph_code(base.induced(rows, root))]
                        ls, rs = len(set(left) & set(root)), len(set(right) & set(root))
                        assert max(ls, rs) > 0
                        tag = ('diagonal' if left == right else 'intersection' if len(set(left) & set(right)) == 1
                               else 'disjoint_' + str((value+6)//7)) + '_root_' + str(min(ls, rs)) + '_' + str(max(ls, rs))
                        samples.setdefault(tag, graph_id)
                        census[tag] += 1
                        for p in maps:
                            labelled = tuple(root[i] for i in p)
                            a = class_maps[root_id][full_classify(rows, left, labelled)]
                            b = class_maps[root_id][full_classify(rows, right, labelled)]
                            if a < b:
                                a, b = b, a
                            multiplier = 2 if left != right and a == b else 1
                            tensors[root_id][(a*(a+1)//2+b, graph_id)] += multiplier * value
                            census['new_root_labelled_decompositions'] += 1
    blocks = []
    for d, original in zip(domains, old['blocks']):
        n = len(d['classes'])
        terms = [[entry, graph, value] for (entry, graph), value in sorted(tensors[d['root_type']].items()) if value]
        assert all(0 <= entry < n*(n+1)//2 for entry, _, _ in terms)
        lower_old = d['disjoint_principal_order']*(d['disjoint_principal_order']+1)//2
        assert [row for row in terms if row[0] < lower_old] == original['terms']
        blocks.append({'root_type': d['root_type'], 'order': n,
                       'lower_entries': n*(n+1)//2, 'terms': terms})
    return {'schema': 'conway99.triangle-projector-full-classes.v1',
            'catalogue_sha256': base.CATALOGUE_SHA, 'original_disjoint_model_raw_sha256': BASE_MODEL_SHA,
            'kernel_scale': 210, 'kernel_entries': old['kernel_entries'], 'normalization': old['normalization'],
            'domains': domains, 'blocks': blocks, 'census': dict(sorted(census.items())),
            'control_graph_ids': samples, 'base_control_graph_ids': old['control_graph_ids'],
            'all_triangle_classes_included': True, 'original_disjoint_principal_tensors_preserved': True,
            'count_point_loaded': False, 'optimizer_called': False}, root_maps


def direct_host(rows, specification, root_maps):
    matrices = {d['root_type']: [[0]*len(d['classes']) for _ in d['classes']]
                for d in specification['domains']}
    classes = {d['root_type']: {class_key(c): i for i, c in enumerate(d['classes'])}
               for d in specification['domains']}
    ts = base.triangles(rows)
    for root in combinations(range(len(rows)), 4):
        root_id, maps = root_maps[base.graph_code(base.induced(rows, root))]
        for p in maps:
            labelled = tuple(root[i] for i in p)
            labels = [classes[root_id][full_classify(rows, t, labelled)] for t in ts]
            M = matrices[root_id]
            for i, left in enumerate(ts):
                for j, right in enumerate(ts):
                    M[labels[i]][labels[j]] += base.kernel(rows, left, right)
    return matrices


def controls(data, specification, root_maps, deadline):
    graphs, levels, _, _ = data
    sample_ids = sorted(set(specification['control_graph_ids'].values()) |
                        set(specification['base_control_graph_ids'].values()))
    lookup = {(len(graphs[i]), pynauty.certificate(base.nauty(graphs[i]))): i
              for n in range(4, 10) for i in levels[n]}
    report = []
    for graph_id in sample_ids:
        base.check_time(deadline)
        rows = graphs[graph_id]
        counts = [0]*len(graphs)
        for size in range(4, len(rows)+1):
            for subset in combinations(range(len(rows)), size):
                pos = graph_id if size == len(rows) else lookup[size, pynauty.certificate(base.nauty(base.induced(rows, subset)))]
                counts[pos] += 1
        direct = direct_host(rows, specification, root_maps)
        computed = base.contract(specification, counts)
        assert direct == computed, (graph_id, 'induced-subset normalization')
        report.append({'host_graph_type': graph_id, 'host_order': len(rows),
                       'ordered_triangle_pairs': True, 'all_nine_full_blocks_equal': True})
    return report


def prepare(catalogue, base_directory, directory, seconds):
    start = time.monotonic()
    deadline = start + seconds
    assert not directory.exists()
    old = check_base(base_directory)
    data = base.load_catalogue(catalogue)
    specification, maps = construct(data, old, deadline)
    checks = controls(data, specification, maps, deadline)
    raw = base.canonical(specification)
    compressed = gzip.compress(raw, mtime=0)
    directory.mkdir(parents=True)
    (directory / 'model.json.gz').write_bytes(compressed)
    report = {'status': 'COMPLETE_POINT_INDEPENDENT_ALL_TRIANGLE_CLASSES_PREPARATION',
              'source_sha256': base.digest(Path(__file__).read_bytes()), 'base_source_sha256': BASE_SOURCE_SHA,
              'original_disjoint_model_raw_sha256': BASE_MODEL_SHA, 'catalogue_sha256': base.CATALOGUE_SHA,
              'model_raw_sha256': base.digest(raw), 'model_gzip_sha256': base.digest(compressed),
              'model_raw_bytes': len(raw), 'model_gzip_bytes': len(compressed),
              'block_orders': [b['order'] for b in specification['blocks']],
              'classes': sum(b['order'] for b in specification['blocks']),
              'lower_entries': sum(b['lower_entries'] for b in specification['blocks']),
              'tensor_nonzeros': sum(len(b['terms']) for b in specification['blocks']),
              'class_intersection_census': [d['class_intersection_census'] for d in specification['domains']],
              'new_decomposition_census': specification['census'], 'small_host_controls': checks,
              'original_disjoint_principal_tensors_preserved': True,
              'count_point_loaded': False, 'optimizer_called': False,
              'query_requires_separate_review': True, 'seconds': time.monotonic()-start}
    (directory / 'preparation.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2), flush=True)


def query(directory, point_path, output, seconds):
    start = time.monotonic()
    deadline = start + seconds
    assert not output.exists()
    report = json.loads((directory / 'preparation.json').read_text())
    assert report['source_sha256'] == base.digest(Path(__file__).read_bytes())
    assert report['base_source_sha256'] == BASE_SOURCE_SHA == base.digest(Path(base.__file__).read_bytes())
    compressed = (directory / 'model.json.gz').read_bytes()
    raw = gzip.decompress(compressed)
    assert base.digest(raw) == report['model_raw_sha256'] and base.digest(compressed) == report['model_gzip_sha256']
    specification = json.loads(raw)
    point_raw = point_path.read_bytes()
    assert base.digest(point_raw) == base.POINT_SHA
    counts = json.loads(point_raw)['induced_counts']
    assert len(counts) == 48965 and all(type(x) is int and x >= 0 for x in counts)
    matrices = base.contract(specification, counts)
    results = []
    for domain, block in zip(specification['domains'], specification['blocks']):
        base.check_time(deadline)
        M = matrices[block['root_type']]
        vectors = [[1]*len(M)] + [[int(c['root_intersection_mask'] & (1 << j) != 0)
                                  for c in domain['classes']] for j in range(4)]
        null_checks = [all(sum(row[i]*v[i] for i in range(len(M))) == 0 for row in M) for v in vectors]
        # These relations are consequences of QB^T=0 in a real graph. Save
        # failures as exact constraints rather than assuming the point has them.
        polynomial = list(map(int, fmpz_mat([[-x for x in row] for row in M]).charpoly()))
        assert polynomial[-1] == 1
        result = {'root_type': block['root_type'], 'order': len(M),
                  'matrix': [[str(x) for x in row] for row in M],
                  'det_tI_plus_matrix_coefficients': list(map(str, polynomial)),
                  'exact_positive_semidefinite': all(x >= 0 for x in polynomial),
                  'constant_and_four_root_incidence_null_checks': null_checks}
        if not result['exact_positive_semidefinite']:
            vector, value = base.exact_negative_vector(M, deadline)
            form = Counter()
            for entry, graph_id, coefficient in block['terms']:
                a = 0
                while (a+1)*(a+2)//2 <= entry:
                    a += 1
                b = entry-a*(a+1)//2
                form[graph_id] += coefficient*vector[a]*vector[b]*(1 if a == b else 2)
            form = {i: c for i, c in form.items() if c}
            assert sum(c*counts[i] for i, c in form.items()) == value < 0
            g = 0
            for c in form.values():
                g = base.gcd(g, abs(c))
            result.update(integer_negative_vector=list(map(str, vector)), quadratic_value=str(value),
                          primitive_induced_count_inequality=[[i, str(c//g)] for i, c in sorted(form.items())],
                          primitive_value=str(value//g))
        results.append(result)
    terminal = {'status': 'EXACT_FULL_TRIANGLE_PROJECTOR_SEPARATORS' if any(not r['exact_positive_semidefinite'] for r in results)
                else 'EXACT_ALL_NINE_FULL_TRIANGLE_PROJECTOR_BLOCKS_PSD',
                'source_sha256': base.digest(Path(__file__).read_bytes()), 'base_source_sha256': BASE_SOURCE_SHA,
                'preparation_sha256': base.digest((directory/'preparation.json').read_bytes()),
                'model_raw_sha256': base.digest(raw), 'point_sha256': base.POINT_SHA,
                'blocks': results, 'seconds': time.monotonic()-start,
                'all_triangle_classes_included': True, 'optimizer_called': False,
                'unrestricted_existence_resolved': False}
    output.write_text(json.dumps(terminal, indent=2)+'\n')
    print(json.dumps({k: v for k, v in terminal.items() if k != 'blocks'}, indent=2), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='mode', required=True)
    prep = commands.add_parser('prepare')
    prep.add_argument('--catalogue', type=Path, required=True)
    prep.add_argument('--base-directory', type=Path, required=True)
    prep.add_argument('--directory', type=Path, required=True)
    prep.add_argument('--seconds', type=float, default=120)
    ask = commands.add_parser('query')
    ask.add_argument('--directory', type=Path, required=True)
    ask.add_argument('--point', type=Path, required=True)
    ask.add_argument('--output', type=Path, required=True)
    ask.add_argument('--seconds', type=float, default=60)
    args = parser.parse_args()
    if args.mode == 'prepare':
        prepare(args.catalogue, args.base_directory, args.directory, args.seconds)
    else:
        query(args.directory, args.point, args.output, args.seconds)


if __name__ == '__main__':
    main()
