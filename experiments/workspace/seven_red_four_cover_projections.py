"""Bounded necessary-projection search for connected four-cover survivors.

Seven all-red bases with a common triangle system induce seven projections
of the same cubic graph onto K3,3. This program uses only their fibers and
the necessary edges of the residual cubic graph. It does not construct or
decide a strongly regular graph unless a separate full check says so.
"""

import argparse
from collections import Counter
from itertools import combinations, permutations, product
import json
from pathlib import Path
import time

import pynauty


def cover(voltages):
    perms = list(permutations(range(4)))
    adjacency = [set() for _ in range(24)]
    for i, j in product(range(3), repeat=2):
        perm = perms[voltages[2*(i-1)+j-1]] if i and j else perms[0]
        for sheet in range(4):
            a, b = 4*i+sheet, 12+4*j+perm[sheet]
            adjacency[a].add(b)
            adjacency[b].add(a)
    return adjacency


def cover_classes(source):
    assert source['complete'] and source['normalized_covers'] == 24**4
    classes = {}
    for row in source['survivors']:
        adjacency = cover(row['voltages'])
        certificate = pynauty.certificate(pynauty.Graph(
            24, adjacency_dict={i: sorted(n) for i, n in enumerate(adjacency)}))
        if certificate not in classes:
            classes[certificate] = {'representative': row, 'count': 0,
                                    'adjacency': [sorted(n) for n in adjacency]}
        classes[certificate]['count'] += 1
    return {'connected_surviving_assignments': len(source['survivors']),
            'underlying_graph_classes': len(classes), 'classes': list(classes.values())}


def partitions(adjacency, vertices):
    full = frozenset(vertices)
    valid = [frozenset(c) for c in combinations(vertices, 4)
             if len(set.union(*(set(adjacency[v]) for v in c))) == 12]
    valid_set = set(valid)
    answer = []
    for i, a in enumerate(valid):
        for b in valid[i+1:]:
            if a & b:
                continue
            c = full-a-b
            if c in valid_set and tuple(sorted(c)) > tuple(sorted(b)):
                answer.append((a, b, c))
    assert len(answer) == len(set(answer))
    return answer


def model(adjacency):
    edges = [(a, b) for a in range(12) for b in adjacency[a]]
    assert len(edges) == 36
    line = [sum(1 << j for j, f in enumerate(edges) if i != j and set(e) & set(f))
            for i, e in enumerate(edges)]
    assert all(row.bit_count() == 4 for row in line)
    initial = [sum(1 << j for j in range(36)
                   if i != j and not (line[i] >> j & 1) and not (line[i] & line[j]))
               for i in range(36)]
    left, right = partitions(adjacency, range(12)), partitions(adjacency, range(12, 24))
    projections = []
    for a, b in product(left, right):
        labels = [(next(i for i, block in enumerate(a) if u in block),
                   next(j for j, block in enumerate(b) if v in block)) for u, v in edges]
        fibers = [sum(1 << k for k, label in enumerate(labels) if label == (i, j))
                  for i, j in product(range(3), repeat=2)]
        assert all(fiber.bit_count() == 4 for fiber in fibers)
        equal = [(u, v) for u, v in combinations(range(36), 2) if labels[u] == labels[v]]
        assert len(equal) == 54
        allowed = [sum(1 << v for v in range(36) if u != v and
                       (labels[u] == labels[v] or
                        (labels[u][0] != labels[v][0] and labels[u][1] != labels[v][1])))
                   for u in range(36)]
        projections.append({'fibers': fibers, 'equal': equal, 'allowed': allowed,
                            'labels': labels})
    compatible = [0]*len(projections)
    for i, j in combinations(range(len(projections)), 2):
        if all((a & b).bit_count() <= 2
               for a in projections[i]['fibers'] for b in projections[j]['fibers']):
            compatible[i] |= 1 << j
            compatible[j] |= 1 << i
    return edges, line, initial, left, right, projections, compatible


def coloring_data(classes):
    """Produce small certificates; the verifier does not call a colorer."""
    import networkx as nx
    records = []
    for row in classes['classes']:
        *_, projections, compatible = model(row['adjacency'])
        graph = nx.Graph()
        graph.add_nodes_from(range(len(projections)))
        graph.add_edges_from((i, j) for i, j in combinations(range(len(projections)), 2)
                             if compatible[i] >> j & 1)
        colors = nx.coloring.greedy_color(graph, strategy='saturation_largest_first')
        records.append({'voltages': row['representative']['voltages'],
                        'normalized_assignments': row['count'],
                        'compatibility_rows': compatible,
                        'colors': [colors[i] for i in range(len(projections))],
                        'color_count': len(set(colors.values()))})
    return {'scope': 'connected four-covers only', 'classes': records}


def verify_colorings(classes, certificate):
    assert len(classes['classes']) == len(certificate['classes']) == 3
    assert classes['connected_surviving_assignments'] == 2736
    summary = []
    for row, saved in zip(classes['classes'], certificate['classes']):
        assert row['representative']['voltages'] == saved['voltages']
        assert row['count'] == saved['normalized_assignments']
        *_, projections, compatible = model(row['adjacency'])
        assert compatible == saved['compatibility_rows']
        colors = saved['colors']
        assert len(colors) == len(projections) == 64
        assert all(isinstance(c, int) and c >= 0 for c in colors)
        assert len(set(colors)) == saved['color_count'] <= 4
        for i, j in combinations(range(64), 2):
            if compatible[i] >> j & 1:
                assert colors[i] != colors[j]
        summary.append({'normalized_assignments': row['count'],
                        'projections': 64, 'verified_color_count': saved['color_count']})
    return {'classes': summary,
            'conclusion': 'no connected four-cover admits seven compatible projections'}


def search(adjacency, seconds=45, node_limit=2000000):
    edges, line, initial, left, right, projections, compatible = model(adjacency)
    begin = time.monotonic()
    visits = Counter()
    prunes = Counter()
    stop = False
    witness = None
    counts = [[0]*36 for _ in range(36)]

    def visit(chosen, candidates, allowed):
        nonlocal stop, witness
        visits[len(chosen)] += 1
        if sum(visits.values()) > node_limit or time.monotonic()-begin > seconds:
            stop = True
            return
        if len(chosen)+candidates.bit_count() < 7:
            prunes['not_enough_projections'] += 1
            return
        if len(chosen) == 7:
            final = [sum(1 << v for v in range(36) if allowed[u] >> v & 1 and counts[u][v] == 1)
                     for u in range(36)]
            if min(map(int.bit_count, final)) < 3:
                prunes['final_residual_degree'] += 1
                return
            witness = {'projection_indices': chosen,
                       'residual_allowed_rows': final,
                       'residual_allowed_degrees': list(map(int.bit_count, final))}
            return
        while candidates and not stop and witness is None:
            bit = candidates & -candidates
            candidates ^= bit
            index = bit.bit_length()-1
            projection = projections[index]
            updated = [allowed[u] & projection['allowed'][u] for u in range(36)]
            overflow = False
            for u, v in projection['equal']:
                counts[u][v] += 1
                counts[v][u] += 1
                if counts[u][v] >= 2:
                    updated[u] &= ~(1 << v)
                    updated[v] &= ~(1 << u)
                if counts[u][v] > 2:
                    overflow = True
            if overflow:
                prunes['three_common_base_neighbors'] += 1
            elif min(map(int.bit_count, updated)) < 3:
                prunes['partial_residual_degree'] += 1
            else:
                visit(chosen+[index], candidates & compatible[index], updated)
            for u, v in projection['equal']:
                counts[u][v] -= 1
                counts[v][u] -= 1

    visit([], (1 << len(projections))-1, initial)
    return {'left_partitions': len(left), 'right_partitions': len(right),
            'projections': len(projections),
            'visits_by_depth': dict(sorted(visits.items())), 'prunes': dict(prunes),
            'status': 'necessary_projection_witness' if witness else
                      ('UNKNOWN' if stop else 'excluded_by_necessary_projection_constraints'),
            'exhaustive': not stop and witness is None, 'witness': witness,
            'seconds': time.monotonic()-begin}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=Path(
        'experiments/logs/grids-and-triangles/seven-red-four-cover-scout.json'))
    parser.add_argument('--output', type=Path)
    parser.add_argument('--seconds', type=float, default=45)
    parser.add_argument('--node-limit', type=int, default=2000000)
    parser.add_argument('--make-colorings', type=Path)
    parser.add_argument('--verify-colorings', type=Path)
    args = parser.parse_args()
    classes = cover_classes(json.loads(args.source.read_text()))
    if args.make_colorings or args.verify_colorings:
        if args.make_colorings:
            certificate = coloring_data(classes)
            args.make_colorings.write_text(json.dumps(certificate, indent=2)+'\n')
        else:
            certificate = json.loads(args.verify_colorings.read_text())
        summary = verify_colorings(classes, certificate)
        print(json.dumps(summary), flush=True)
        if args.output:
            args.output.write_text(json.dumps(summary, indent=2)+'\n')
        raise SystemExit(0)
    for index, row in enumerate(classes['classes']):
        row['projection_search'] = search(row['adjacency'], args.seconds, args.node_limit)
        print(json.dumps({'case': index, **row['projection_search']}), flush=True)
    if args.output:
        args.output.write_text(json.dumps(classes, indent=2)+'\n')
