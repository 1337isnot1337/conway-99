"""Exact local tip-neighborhood certificates for two isomorphic rook grids.

This is a necessary local projection, not an edge-completion solver.
Only the Python standard library is required.  Each forbidden mask has
an explicit Hall cut; each admitted mask has an integral flow witness.
"""

import argparse
from collections import Counter, deque
from itertools import product
import json
from pathlib import Path


POINTS = tuple(range(1, 9))


def rook(p, q):
    return p != q and (p // 3 == q // 3 or p % 3 == q % 3)


CELLS = tuple((p, q) for p, q in product(POINTS, repeat=2)
              if p != q and not rook(p, q))


def demands(mask):
    assert 0 <= mask < 256
    return {p: 2-int(rook(0, p))-((mask >> (p-1)) & 1)
            for p in POINTS}


def find_flow(mask):
    """Return an integral matrix, or None; no external graph library."""
    demand = demands(mask)
    source, sink = 0, 18
    residual = {}
    for p in POINTS:
        residual[source, p] = demand[p]
        residual[p+9, sink] = demand[p]
    for p, q in CELLS:
        residual[p, q+9] = 1
    for a, b in list(residual):
        residual.setdefault((b, a), 0)
    neighbors = [[] for _ in range(19)]
    for a, b in residual:
        neighbors[a].append(b)
    value = 0
    while True:
        parent = {source: None}
        queue = deque([source])
        while queue and sink not in parent:
            a = queue.popleft()
            for b in neighbors[a]:
                if b not in parent and residual[a, b]:
                    parent[b] = a
                    queue.append(b)
        if sink not in parent:
            break
        b = sink
        while parent[b] is not None:
            a = parent[b]
            residual[a, b] -= 1
            residual[b, a] += 1
            b = a
        value += 1
    if value != sum(demand.values()):
        return None
    return [[p, q] for p, q in CELLS if residual[p, q+9] == 0]


def hall_cut(mask):
    """Find the shortest left set giving a positive Hall deficit."""
    demand = demands(mask)
    witnesses = []
    for subset in range(1, 256):
        left = [p for p in POINTS if subset >> (p-1) & 1]
        counts = {q: sum((p, q) in CELLS for p in left) for q in POINTS}
        right = [q for q in POINTS if counts[q] > demand[q]]
        lhs = sum(demand[p] for p in left)
        rhs = sum(demand[q] for q in right)
        rhs += sum(p in left and q not in right for p, q in CELLS)
        assert rhs == sum(min(demand[q], counts[q]) for q in POINTS)
        if lhs > rhs:
            witnesses.append((len(left), -lhs+rhs, left, right, lhs, rhs))
    if not witnesses:
        return None
    _, _, left, right, lhs, rhs = min(witnesses)
    return {'left': left, 'right': right, 'demand': lhs,
            'cut_capacity': rhs, 'deficit': lhs-rhs}


def mask_degrees(mask):
    return [sum((mask >> (p-1)) & 1 for p in POINTS if rook(0, p)),
            sum((mask >> (p-1)) & 1 for p in POINTS if not rook(0, p))]


def compact_rules(mask):
    """Nine necessary Hall inequalities; the witnesses prove sufficiency here."""
    z = {p: (mask >> (p-1)) & 1 for p in POINTS}
    near, far = mask_degrees(mask)
    lines = ((3, 4, 5), (6, 7, 8), (1, 4, 7), (2, 5, 8))
    horns = ((1, 3, 8), (2, 3, 7), (1, 6, 5), (2, 6, 4))
    return ([near <= far]
            + [sum(z.values())-2*sum(z[p] for p in line) <= 2 for line in lines]
            + [z[a]+z[b]-z[c] <= 1 for a, b, c in horns])


def translate(point, tip):
    """A fixed rook automorphism carrying tip to zero."""
    return 3*((point//3-tip//3) % 3)+(point % 3-tip % 3) % 3


def verify(record):
    assert record['scope'] == 'one tip, mixed equations and duplicate-pair packing only'
    assert record['point_order'] == list(POINTS)
    assert record['candidate_cells'] == [list(cell) for cell in CELLS]
    rows = record['masks']
    assert [row['mask'] for row in rows] == list(range(256))
    admitted, forbidden, extra = [], [], []
    degree_counts = Counter()
    for row in rows:
        mask, demand = row['mask'], demands(row['mask'])
        assert row['admitted'] == all(compact_rules(mask))
        near, far = mask_degrees(mask)
        assert row['tip_near_degree'] == near
        assert row['tip_far_degree'] == far
        if row['admitted']:
            cells = [tuple(cell) for cell in row['flow_cells']]
            assert len(set(cells)) == len(cells)
            assert all(cell in CELLS for cell in cells)
            assert all(sum(a == p for a, _ in cells) == demand[p] for p in POINTS)
            assert all(sum(b == p for _, b in cells) == demand[p] for p in POINTS)
            assert near <= far
            admitted.append(mask)
        else:
            cut = row['hall_cut']
            left, right = cut['left'], cut['right']
            assert sorted(set(left)) == left and set(left) <= set(POINTS)
            assert sorted(set(right)) == right and set(right) <= set(POINTS)
            lhs = sum(demand[p] for p in left)
            rhs = sum(demand[q] for q in right)
            rhs += sum(p in left and q not in right for p, q in CELLS)
            assert cut['demand'] == lhs > rhs == cut['cut_capacity']
            assert cut['deficit'] == lhs-rhs
            forbidden.append(mask)
            if near <= far:
                extra.append(mask)
        degree_counts[near, far, row['admitted']] += 1
    assert len(admitted) == 103 and len(forbidden) == 153 and len(extra) == 60
    assert record['admitted_masks'] == admitted
    assert record['forbidden_masks'] == forbidden
    assert record['forbidden_beyond_near_le_far'] == extra
    for tip in range(9):
        permutation = [translate(point, tip) for point in range(9)]
        assert sorted(permutation) == list(range(9))
        assert permutation[tip] == 0
        assert all(rook(p, q) == rook(permutation[p], permutation[q])
                   for p, q in product(range(9), repeat=2))
    return {'status': 'all 256 exact local certificates verified',
            'admitted_masks': len(admitted), 'forbidden_masks': len(forbidden),
            'masks_admitted_by_near_le_far': 163,
            'additional_forbidden_masks': len(extra),
            'clauses_for_all_nine_tips': 9*len(forbidden),
            'equivalent_compact_inequalities_per_tip': 9,
            'masks_admitted_before_four_horn_inequalities':
                sum(all(compact_rules(mask)[:5]) for mask in range(256)),
            'degree_counts': [[near, far, good, count]
                              for (near, far, good), count in sorted(degree_counts.items())]}


def generate():
    record = {'scope': 'one tip, mixed equations and duplicate-pair packing only',
              'point_order': list(POINTS),
              'candidate_cells': [list(cell) for cell in CELLS], 'masks': []}
    admitted, forbidden, extra = [], [], []
    for mask in range(256):
        flow, cut = find_flow(mask), hall_cut(mask)
        assert (flow is None) == (cut is not None)
        near, far = mask_degrees(mask)
        row = {'mask': mask, 'tip_near_degree': near, 'tip_far_degree': far,
               'admitted': flow is not None}
        if flow is not None:
            row['flow_cells'] = flow
            admitted.append(mask)
        else:
            row['hall_cut'] = cut
            forbidden.append(mask)
            if near <= far:
                extra.append(mask)
        record['masks'].append(row)
    record.update(admitted_masks=admitted, forbidden_masks=forbidden,
                  forbidden_beyond_near_le_far=extra)
    verify(record)
    return record


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--certificate', type=Path, required=True)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    if args.write:
        certificate = generate()
        args.certificate.parent.mkdir(parents=True, exist_ok=True)
        args.certificate.write_text(json.dumps(certificate, indent=2)+'\n')
    result = verify(json.loads(args.certificate.read_text()))
    print(json.dumps(result, indent=2))
