"""Exclude a balanced six-axis frame in the even far quotient of an involution."""

import argparse
from collections import Counter
from dataclasses import dataclass
from itertools import combinations, permutations

from ortools.sat.python import cp_model


AXES = range(6)
ALL = 63
LABELS = tuple((1 << a) | (1 << b) for a, b in combinations(range(7), 2))
LABEL_ROWS = tuple(label for label in LABELS for _ in range(2))
ARCS = tuple(permutations(AXES, 2))


def bits(mask):
    while mask:
        bit = mask & -mask
        yield bit.bit_length()-1
        mask ^= bit


@dataclass(frozen=True)
class Cut:
    label: int
    raised: int
    arcs: int

    def kind(self):
        return (-self.arcs.bit_count(), self.raised.bit_count(),
                (self.label & ALL).bit_count())


def cuts():
    for label in LABELS:
        outside = ALL & ~label
        for raised in range(1, ALL):
            if raised & ~outside or raised == outside:
                continue
            arcs = sum(1 << j for j, (a, b) in enumerate(ARCS)
                       if raised & (1 << a) and (outside ^ raised) & (1 << b))
            yield Cut(label, raised, arcs)


def covers():
    events = list(cuts())
    by_arc = [sum(1 << j for j, e in enumerate(events) if e.arcs & (1 << i))
              for i in range(len(ARCS))]
    by_label = {label: sum(1 << j for j, e in enumerate(events) if e.label == label)
                for label in LABELS}
    conflicts = [sum(1 << j for j, other in enumerate(events) if e.arcs & other.arcs)
                 for e in events]
    full = (1 << len(ARCS))-1

    def extend(unused, allowed, used_labels, chosen):
        if not unused:
            yield chosen
            return
        choices = min((allowed & by_arc[i] for i in bits(unused)), key=int.bit_count)
        for j in bits(choices):
            event = events[j]
            banned = conflicts[j]
            if event.label in used_labels:
                banned |= by_label[event.label]
            yield from extend(unused ^ event.arcs, allowed & ~banned,
                              used_labels | {event.label}, chosen + (event,))

    # S6 is transitive on each kind. Fix one event of the earliest kind present.
    for kind in sorted({e.kind() for e in events}):
        first = next(j for j, e in enumerate(events) if e.kind() == kind)
        allowed = sum(1 << j for j, e in enumerate(events) if e.kind() >= kind)
        e = events[first]
        yield from extend(full ^ e.arcs, allowed & ~conflicts[first], {e.label}, (e,))


def complete_constant_rows(chosen):
    """Recover the number of all-raised rows at each label from U times H."""
    count = [[sum(1 for e in chosen if e.label & (1 << i) and e.raised & (1 << j))
              for j in AXES] for i in range(7)]
    used = Counter(e.label for e in chosen)
    full_rows = {}
    for i in AXES:
        outside = (1 << i) | 64
        possible = [(y, (25-sum(count[i])-y)//4) for y in range(3-used[outside])
                    if (25-sum(count[i])-y) % 4 == 0]
        if not possible:
            return
        (full_rows[outside], degree), = possible
        for j in AXES:
            if j == i:
                continue
            label = (1 << i) | (1 << j)
            x = degree-5+count[i][j]
            if x != full_rows.get(label, x) or not 0 <= x <= 2-used[label]:
                return
            full_rows[label] = x

    if len({count[6][i]-full_rows[(1 << i) | 64] for i in AXES}) != 1:
        return
    rows = []
    for label in LABELS:
        values = [e.raised for e in chosen if e.label == label]
        values += [ALL & ~label]*full_rows[label]
        values += [0]*(2-len(values))
        rows.extend(sorted(values))
    return tuple(rows)


def orbit(rows):
    for perm in permutations(AXES):
        image = [sum(1 << (perm[i] if i < 6 else 6) for i in bits(mask))
                 for mask in range(128)]
        for flip in (False, True):
            result = [0]*42
            for i, label in enumerate(LABELS):
                offset = 2*LABELS.index(image[label])
                shift = (ALL & ~label) if flip else 0
                result[offset:offset+2] = sorted(image[k ^ shift] for k in rows[2*i:2*i+2])
            yield tuple(result)


def row_model(rows, selected):
    """Impose the quotient equations only on the selected one or two rows."""
    model = cp_model.CpModel()
    adjacency, positive, double = {}, {}, {}
    h = [[1 if label & (1 << a) else 2*((raised >> a) & 1) for a in AXES]
         for label, raised in zip(LABEL_ROWS, rows)]
    for i in selected:
        for j in range(42):
            if i == j or (i, j) in adjacency:
                continue
            positive[i, j] = positive[j, i] = model.new_bool_var('positive')
            double[i, j] = double[j, i] = model.new_bool_var('double')
            model.add(double[i, j] <= positive[i, j])
            adjacency[i, j] = adjacency[j, i] = model.new_int_var(0, 2, 'weight')
            model.add(adjacency[i, j] == positive[i, j]+double[i, j])

    for i in selected:
        model.add(sum(positive[i, j] for j in range(42) if j != i) == 11)
        model.add(sum(double[i, j] for j in range(42) if j != i) == 1)
        for a in range(7):
            model.add(sum(adjacency[i, j] for j in range(42) if j != i and
                          LABEL_ROWS[j] & (1 << a)) == 4-2*((LABEL_ROWS[i] >> a) & 1))
        for a in range(1, 6):
            model.add(sum(adjacency[i, j]*(h[j][a]-h[j][0]) for j in range(42)
                          if j != i) == -4*(h[i][a]-h[i][0]))
    for i, j in combinations(selected, 2):
        products = []
        for k in range(42):
            if k in (i, j):
                continue
            # Each quotient column has only one double entry.
            term = model.new_int_var(0, 2, 'product')
            model.add_multiplication_equality(term, (adjacency[i, k], adjacency[j, k]))
            products.append(term)
        model.add(sum(products)+adjacency[i, j] == 4-(LABEL_ROWS[i] & LABEL_ROWS[j]).bit_count())
    solver = cp_model.CpSolver()
    solver.parameters.num_workers = 1
    return solver.solve(model) == cp_model.INFEASIBLE


def obstruction(rows):
    h = [[1 if label & (1 << a) else 2*((raised >> a) & 1) for a in AXES]
         for label, raised in zip(LABEL_ROWS, rows)]
    spikes = []
    for a, b in combinations(AXES, 2):
        f = [v[a]-v[b] for v in h]
        assert sum(x*x for x in f) == 28
        assert all(sum(x for x, label in zip(f, LABEL_ROWS) if label & (1 << j)) == 0
                   for j in range(7))
        spikes.append(tuple(i for i, x in enumerate(f) if abs(x) == 2))
    for i in sorted({i for pair in spikes for i in pair}):
        if row_model(rows, (i,)):
            return (i,)
    for pair in sorted(set(spikes)):
        if row_model(rows, pair):
            return pair
    raise AssertionError("no local contradiction found")


def verify(certificate_tools=None):
    total = completions = 0
    pool = set()
    for choice in covers():
        total += 1
        rows = complete_constant_rows(choice)
        if rows is not None:
            completions += 1
            pool.add(rows)
    assert (total, completions) == (8028, 800)
    counts = Counter()
    while pool:
        rows = min(pool)
        pool.difference_update(orbit(rows))
        selected = obstruction(rows)
        counts[len(selected)] += 1
        if certificate_tools:
            from involution_frame_certificates import certify
            certify(rows, selected, *certificate_tools)
    assert counts == {1: 23, 2: 3}
    print("Six-axis frames: 8028 covers, 800 completions, 26 classes.")
    print("23 classes fail one quotient row and the other three fail a pair of rows.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--certify", nargs=2, metavar=("CADICAL", "DRAT_TRIM"))
    verify(parser.parse_args().certify)
