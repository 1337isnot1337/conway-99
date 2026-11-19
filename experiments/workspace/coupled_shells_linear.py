"""Aggregate H-neighborhood counts and integer Farkas certificates.

This is a necessary relaxation of the norm-16 high/low completion model.
Replay uses integer arithmetic and finite mask enumeration, without a solver.
"""
from __future__ import annotations

import argparse
from collections import Counter, deque
from itertools import combinations
import json
from pathlib import Path

import numpy as np
from scipy import sparse as sp


def matching_possible(capacity, pdeg, ndeg):
    """Integral bipartite capacity matching, by an independent max-flow replay."""
    if min([*pdeg, *ndeg]) < 0 or sum(pdeg) != sum(ndeg):
        return False
    target = sum(pdeg)
    residual = [[0] * 18 for _ in range(18)]
    for p in range(8):
        residual[16][p] = int(pdeg[p])
        for n in range(8):
            residual[p][8 + n] = int(capacity[p][n])
    for n in range(8):
        residual[8 + n][17] = int(ndeg[n])
    flow = 0
    while flow < target:
        previous = [-1] * 18
        previous[16] = 16
        queue = deque([16])
        while queue and previous[17] == -1:
            u = queue.popleft()
            for v in range(18):
                if residual[u][v] and previous[v] == -1:
                    previous[v] = u
                    queue.append(v)
        if previous[17] == -1:
            return False
        amount, v = target - flow, 17
        while v != 16:
            u = previous[v]
            amount = min(amount, residual[u][v])
            v = u
        v = 17
        while v != 16:
            u = previous[v]
            residual[u][v] -= amount
            residual[v][u] += amount
            v = u
        flow += amount
    return True


class Context:
    def __init__(self, rows, template):
        assert len(rows) == 8 and all(isinstance(r, int) and 0 <= r < 256 for r in rows)
        assert len(template['high']) == 8
        self.rows, self.template = rows, template
        self.core = np.zeros((16, 16), dtype=np.int16)
        for p in range(8):
            for n in range(8):
                self.core[p, n + 8] = self.core[n + 8, p] = (rows[p] >> n) & 1
        self.high = np.zeros((8, 16), dtype=np.int16)
        for h, (pp, nn) in enumerate(template['high']):
            assert len(set(pp)) == len(set(nn)) == 2
            assert all(0 <= p < 8 for p in pp) and all(0 <= n < 8 for n in nn)
            self.high[h, pp] = 1
            self.high[h, [n + 8 for n in nn]] = 1
        self.common = self.high @ self.high.T
        B = self.core[:8, 8:]
        assert np.all(B.sum(axis=0) == 4) and np.all(B.sum(axis=1) == 4)
        assert np.all(B @ B.T - 4 * np.eye(8, dtype=np.int16) <= 2)
        assert np.all(B.T @ B - 4 * np.eye(8, dtype=np.int16) <= 2)
        assert np.all(self.high.sum(axis=0) == 2)
        assert np.all(self.common - 4 * np.eye(8, dtype=np.int16) <= 2)
        singles = np.array(template['single'], dtype=np.int16)
        assert np.array_equal(singles, 2 - B - self.high[:, :8].T @ self.high[:, 8:])
        assert np.all(singles >= 0) and int(singles.sum()) == 64
        self.base_need = 2 - self.high - self.high @ self.core
        self.classes = [(p, n, int(template['single'][p][n]))
                        for p in range(8) for n in range(8) if template['single'][p][n]]
        self.pairs = list(combinations(range(8), 2))
        self.bits = np.array([[(mask >> h) & 1 for h in range(8)] for mask in range(256)], dtype=np.int16)
        self.mask_core = self.bits @ self.high
        # The e(H) <= 1 theorem makes degree-zero and degree-one rows exhaustive.
        # These domains use only max-flow, independently of the SAT model code.
        self.high_domains = []
        for h in range(8):
            capacity = [[0 if self.high[h, p] and self.high[h, 8 + n]
                         else int(template['single'][p][n])
                         for n in range(8)] for p in range(8)]
            allowed = []
            for mask in [0, *(1 << k for k in range(8) if k != h and self.common[h, k] <= 1)]:
                need = self.base_need[h] - self.mask_core[mask]
                if matching_possible(capacity, need[:8], need[8:]):
                    allowed.append(mask)
            self.high_domains.append(allowed)
        self.zero_domains = []
        for mask in range(256):
            if mask.bit_count() < 2:
                continue
            if any((mask >> h & 1) and (mask >> k & 1) and self.common[h, k] >= 2
                   for h, k in self.pairs):
                continue
            need = 2 - self.mask_core[mask]
            if matching_possible(template['single'], need[:8], need[8:]):
                self.zero_domains.append(mask)

    def high_choices(self):
        for edge in [None, *self.pairs]:
            E = self.high_matrix(edge)
            if all(sum(int(E[h, j]) << j for j in range(8)) in self.high_domains[h] for h in range(8)):
                yield edge

    @staticmethod
    def high_matrix(edge):
        E = np.zeros((8, 8), dtype=np.int16)
        if edge is not None:
            E[tuple(edge)] = E[tuple(reversed(edge))] = 1
        return E


def build(context, edge):
    E = context.high_matrix(edge)
    base = len(context.classes)
    pair_start = base + 128 + 9
    row_labels = [('low_class', p, n) for p, n, _ in context.classes]
    row_labels += [('high_core', h, p) for h in range(8) for p in range(16)]
    row_labels += [('zero_high', h) for h in range(8)] + [('zero_total',)]
    row_labels += [('high_pair', h, k) for h, k in context.pairs]
    eq_count = len(row_labels)
    columns, labels, class_index, masks = [], [], [], []
    upper_bounds = []
    pair_allowed = np.ones(256, dtype=bool)
    for h, k in context.pairs:
        if context.common[h, k] + E[h, k] >= 2:
            pair_allowed &= ~((context.bits[:, h] != 0) & (context.bits[:, k] != 0))
    high_common = context.bits @ E

    def pair_entries(column, mask):
        for i, (h, k) in enumerate(context.pairs):
            if (mask >> h & 1) and (mask >> k & 1):
                column[pair_start + i] = 1

    for cl, (p, n, multiplicity) in enumerate(context.classes):
        overlap = context.high[:, p] + context.high[:, n + 8]
        core_cap = 2 - context.core[:, p] - context.core[:, n + 8]
        core_cap = core_cap.copy()
        core_cap[p] -= 1
        core_cap[n + 8] -= 1
        allowed = pair_allowed & np.all(context.bits + high_common + overlap <= 2, axis=1)
        allowed &= np.all(context.mask_core <= core_cap, axis=1)
        for mask in map(int, np.flatnonzero(allowed)):
            column = {cl: 1}
            for h in range(8):
                if mask >> h & 1:
                    column[base + 16 * h + p] = 1
                    column[base + 16 * h + n + 8] = 1
            pair_entries(column, mask)
            columns.append(column)
            labels.append(('low', p, n, mask))
            class_index.append(cl)
            masks.append(mask)
            upper_bounds.append(None)
    for mask in context.zero_domains:
        if not pair_allowed[mask]:
            continue
        column = {base + 128 + 8: 1}
        for h in range(8):
            if mask >> h & 1:
                column[base + 128 + h] = 1
        pair_entries(column, mask)
        columns.append(column)
        labels.append(('zero', mask))
        class_index.append(-1)
        masks.append(mask)
        upper_bounds.append(2 if mask.bit_count() == 2 else 1)

    need = context.base_need - E @ context.high
    rhs = [m for _, _, m in context.classes] + need.ravel().tolist()
    rhs += (4 + E.sum(axis=1)).tolist() + [11]
    rhs += [int(2 - context.common[h, k] - E[h, k]) for h, k in context.pairs]
    duplicate_rows = {}
    for cl, (p, n, multiplicity) in enumerate(context.classes):
        if multiplicity > 1:
            for h in range(8):
                duplicate_rows[cl, h] = len(row_labels)
                row_labels.append(('duplicate_low_high', p, n, h))
                rhs.append(1)
    for i, column in enumerate(columns):
        cl, mask = class_index[i], masks[i]
        for h in range(8):
            if (cl, h) in duplicate_rows and (mask >> h & 1):
                column[duplicate_rows[cl, h]] = 1
        if upper_bounds[i] is not None:
            column[len(row_labels)] = 1
            row_labels.append(('zero_bound', mask))
            rhs.append(upper_bounds[i])
    row_indices, col_indices, values = [], [], []
    for col, entries in enumerate(columns):
        for row, value in entries.items():
            row_indices.append(row)
            col_indices.append(col)
            values.append(value)
    raw = sp.csc_matrix((np.array(values, dtype=np.int64), (row_indices, col_indices)),
                        shape=(len(row_labels), len(columns)))
    inequalities = len(row_labels) - eq_count
    slacks = sp.vstack((sp.csc_matrix((eq_count, inequalities), dtype=np.int64),
                        sp.eye(inequalities, dtype=np.int64)), format='csc')
    augmented = sp.hstack((raw, slacks), format='csc')
    return augmented, np.array(rhs, dtype=np.int64), labels, row_labels, eq_count


def check_ray(A, b, ray):
    assert len(ray) == len(b)
    right = sum(int(x) * int(y) for x, y in zip(ray, b))
    assert right < 0
    for column in range(A.shape[1]):
        left = sum(int(ray[A.indices[t]]) * int(A.data[t])
                   for t in range(A.indptr[column], A.indptr[column + 1]))
        assert left >= 0, column
    return right


def search_case(manifest, seconds=5):
    from scipy.optimize import linprog
    from completion_constraints import exact_farkas
    context = Context(manifest['rows'], manifest['template'])
    output = {k: manifest[k] for k in ('core', 'orbit', 'rows', 'template')}
    output['edge_cases'] = []
    output['status'] = 'exact exclusion'
    for edge in context.high_choices():
        A, b, labels, row_labels, eq_count = build(context, edge)
        result = linprog(np.zeros(A.shape[1]), A_eq=A, b_eq=b, bounds=(0, None),
                         method='highs', options={'time_limit': seconds})
        record = {'edge': list(edge) if edge is not None else None,
                  'variables': A.shape[1], 'mask_variables': len(labels), 'rows': len(b),
                  'lp_status': int(result.status)}
        if result.status == 2:
            ray = exact_farkas(A, b)
            if ray is not None:
                record.update(status='exact exclusion', ray=ray, rhs=check_ray(A, b, ray),
                              nonzero_terms=[[list(row_labels[i]), value] for i, value in enumerate(ray) if value])
            else:
                record['status'] = 'unverified infeasibility'
        elif result.success:
            record['status'] = 'floating feasible'
        else:
            record['status'] = 'unknown'
        output['edge_cases'].append(record)
        print(json.dumps({'core': output['core'], 'orbit': output['orbit'], 'edge': record['edge'],
                          'status': record['status'], 'ray_terms': len(record.get('nonzero_terms', []))}), flush=True)
        if record['status'] != 'exact exclusion':
            output['status'] = 'not excluded'
            break
    return output


def replay(record):
    context = Context(record['rows'], record['template'])
    expected = {tuple(e) if e is not None else None for e in context.high_choices()}
    actual = {tuple(e['edge']) if e['edge'] is not None else None for e in record['edge_cases']}
    assert len(actual) == len(record['edge_cases'])
    assert actual <= expected
    if record['status'] == 'exact exclusion':
        assert expected == actual
        assert all(e['status'] == 'exact exclusion' for e in record['edge_cases'])
    checked = 0
    for edge_record in record['edge_cases']:
        if edge_record['status'] != 'exact exclusion':
            continue
        A, b, labels, row_labels, eq_count = build(context, edge_record['edge'])
        assert (A.shape[1], len(labels), len(b)) == (edge_record['variables'], edge_record['mask_variables'], edge_record['rows'])
        assert edge_record['status'] == 'exact exclusion'
        assert check_ray(A, b, edge_record['ray']) == edge_record['rhs']
        assert [[list(row_labels[i]), value] for i, value in enumerate(edge_record['ray']) if value] == edge_record['nonzero_terms']
        checked += 1
    return checked


def project_witness(rows, template, witness):
    context = Context(rows, template)
    high_edges = [(i, j) for i, j in witness['edges'] if j < 8]
    assert len(high_edges) <= 1
    edge = high_edges[0] if high_edges else None
    assert edge in list(context.high_choices())
    A, b, labels, row_labels, eq_count = build(context, edge)
    low_labels = [(p, n) for p, n, multiplicity in context.classes for _ in range(multiplicity)]
    low_masks = [0] * 64
    for h, l in witness['low_edges']:
        low_masks[l] |= 1 << h
    zero_masks = [0] * 11
    for i, j in witness['edges']:
        if i < 8 <= j:
            zero_masks[j - 8] |= 1 << i
    population = Counter(('low', p, n, mask) for (p, n), mask in zip(low_labels, low_masks))
    population.update(('zero', mask) for mask in zero_masks)
    index = {label: i for i, label in enumerate(labels)}
    x = np.zeros(A.shape[1], dtype=np.int64)
    for label, multiplicity in population.items():
        assert label in index, label
        x[index[label]] = multiplicity
    remainder = b - A @ x
    assert np.all(remainder[:eq_count] == 0)
    assert np.all(remainder[eq_count:] >= 0)
    x[len(labels):] = remainder[eq_count:]
    assert np.array_equal(A @ x, b)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--manifest', type=Path, nargs='*')
    p.add_argument('--out', type=Path)
    p.add_argument('--seconds', type=float, default=5)
    p.add_argument('--replay', type=Path)
    p.add_argument('--orbits', type=Path)
    p.add_argument('--witnesses', type=Path)
    args = p.parse_args()
    if args.replay:
        data = json.loads(args.replay.read_text())
        assert data['model_version'] == 1
        if args.orbits:
            blocks = {b['core']: b for b in json.loads(args.orbits.read_text())}
            for record in data['cases']:
                block = blocks[record['core']]
                assert record['rows'] == block['rows']
                for key in ('high', 'single'):
                    assert record['template'][key] == block['orbits'][record['orbit']][key]
        total = branches_total = 0
        for record in data['cases']:
            branches = replay(record)
            total += record['status'] == 'exact exclusion'
            branches_total += branches
            print(json.dumps({'core': record['core'], 'orbit': record['orbit'], 'exact_branches_replayed': branches}), flush=True)
        print(json.dumps({'exact_template_exclusions_replayed': total,
                          'exact_branch_certificates_replayed': branches_total}), flush=True)
    if args.manifest:
        result = {'model_version': 1, 'cases': []}
        for path in args.manifest:
            result['cases'].append(search_case(json.loads(path.read_text()), args.seconds))
            if args.out:
                args.out.write_text(json.dumps(result, indent=2) + '\n')
    if args.witnesses:
        blocks = {b['core']: b for b in json.loads(args.orbits.read_text())}
        checked = 0
        for record in json.loads(args.witnesses.read_text()):
            if record['status'] != 'sat':
                continue
            block = blocks[record['core']]
            project_witness(block['rows'], block['orbits'][record['orbit']], record)
            checked += 1
            if checked % 50 == 0:
                print(json.dumps({'partial_witnesses_projected': checked}), flush=True)
        print(json.dumps({'exact_partial_witness_projections': checked}), flush=True)


if __name__ == '__main__':
    main()
