"""Exact three-grid census with two rook-isomorphic matching interfaces.

Enumerates every third-interface permutation, quotients only by explicit
rook conjugation and inversion, and replays binary incidence propagation.
The sole surviving class has a verified outside-incidence witness.
This program does not choose any edges among the outside vertices.
"""

import argparse
from collections import Counter
from itertools import combinations, permutations, product
import json
from pathlib import Path


def rook(i, j):
    return i != j and (i // 3 == j // 3 or i % 3 == j % 3)


def inverse(p):
    return tuple(p.index(i) for i in range(9))


def automorphisms():
    maps = set()
    for a, b in product(permutations(range(3)), repeat=2):
        maps.add(tuple(3*a[x]+b[y] for x, y in product(range(3), repeat=2)))
        maps.add(tuple(3*a[y]+b[x] for x, y in product(range(3), repeat=2)))
    assert len(maps) == 72
    assert all(all(rook(i, j) == rook(p[i], p[j])
                   for i, j in combinations(range(9), 2)) for p in maps)
    return sorted(maps)


def classes():
    allowed = {p for p in permutations(range(9))
               if all(not rook(i, p[i]) for i in range(9))}
    assert len(allowed) == 2720
    autos = [(q, inverse(q)) for q in automorphisms()]
    left = set(allowed)
    result = []
    while left:
        p = min(left)
        pi = inverse(p)
        orbit = set()
        for q, qi in autos:
            orbit.add(tuple(q[p[qi[i]]] for i in range(9)))
            orbit.add(tuple(q[pi[qi[i]]] for i in range(9)))
        assert orbit <= left
        left -= orbit
        result.append((p, sorted(orbit)))
    assert len(result) == 59 and sum(len(orbit) for _, orbit in result) == 2720
    return result


def core(mapping):
    rows = [set() for _ in range(27)]
    for base in range(3):
        for i, j in combinations(range(9), 2):
            if rook(i, j):
                rows[9*base+i].add(9*base+j)
                rows[9*base+j].add(9*base+i)
    for a, b in combinations(range(3), 2):
        p = mapping if (a, b) == (1, 2) else tuple(range(9))
        for x, y in enumerate(p):
            rows[9*a+x].add(9*b+y)
            rows[9*b+y].add(9*a+x)
    assert all(len(row) == 6 for row in rows)
    gram = [[12*int(i == j)+2-int(j in rows[i])-len(rows[i] & rows[j])
             for j in range(27)] for i in range(27)]
    assert min(min(row) for row in gram) >= 0
    assert all(gram[i][i] == 8 and sum(gram[i]) == 24 for i in range(27))
    return rows, gram


def signatures(rows, gram):
    pair_count = 0
    accepted = []
    for x, y, z in product(range(9), repeat=3):
        signature = (x, 9+y, 18+z)
        if any(gram[i][j] == 0 for i, j in combinations(signature, 2)):
            continue
        pair_count += 1
        selected = set(signature)
        if all(len(row & selected)+int(i in selected) <= 2 for i, row in enumerate(rows)):
            accepted.append(signature)
    return pair_count, accepted


def equations(gram, accepted):
    result = []
    for i in range(27):
        for j in range(i, 27):
            if gram[i][j]:
                candidates = [k for k, s in enumerate(accepted) if i in s and j in s]
                result.append(((i, j), gram[i][j], candidates))
    return result


def propagate(eqs):
    fixed = {}
    trace = []
    while True:
        changed = False
        for pair, rhs, candidates in eqs:
            ones = sum(fixed.get(k) == 1 for k in candidates)
            unknown = [k for k in candidates if k not in fixed]
            residual = rhs-ones
            if residual < 0 or residual > len(unknown):
                trace.append({'kind': 'contradiction', 'pair': list(pair),
                              'rhs': rhs, 'minimum': ones, 'maximum': ones+len(unknown)})
                return trace, fixed, True
            if unknown and residual in (0, len(unknown)):
                value = int(residual > 0)
                trace.append({'kind': 'force', 'pair': list(pair),
                              'value': value, 'signatures': unknown})
                fixed.update((k, value) for k in unknown)
                changed = True
        if not changed:
            return trace, fixed, False


def replay_trace(eqs, trace):
    """Check each saved implication without assuming the propagation scan order."""
    by_pair = {pair: (rhs, candidates) for pair, rhs, candidates in eqs}
    known = {}
    for step_index, step in enumerate(trace):
        rhs, candidates = by_pair[tuple(step['pair'])]
        lower = sum(known.get(k) == 1 for k in candidates)
        free = sorted(set(candidates)-known.keys())
        upper = lower+len(free)
        if step['kind'] == 'contradiction':
            assert step_index == len(trace)-1
            assert rhs < lower or rhs > upper
            assert (step['rhs'], step['minimum'], step['maximum']) == (rhs, lower, upper)
            return True
        assert step['kind'] == 'force' and step['signatures'] == free and free
        value = step['value']
        assert value in (0, 1)
        assert (rhs == lower if value == 0 else rhs == upper)
        known.update((k, value) for k in free)
    return False


def audit(witness):
    class_data = classes()
    results = []
    for index, (p, orbit) in enumerate(class_data):
        rows, gram = core(p)
        pair_count, accepted = signatures(rows, gram)
        eqs = equations(gram, accepted)
        initial_deficit = any(len(candidates) < rhs for _, rhs, candidates in eqs)
        immediately_forced = {k for _, rhs, candidates in eqs if len(candidates) == rhs
                              for k in candidates}
        initial_overflow = any(len(set(candidates) & immediately_forced) > rhs
                               for _, rhs, candidates in eqs)
        trace, fixed, contradiction = propagate(eqs)
        assert replay_trace(eqs, trace) == contradiction
        stage = ('initial quota deficit' if initial_deficit else
                 'initial forcing overflow' if initial_overflow else
                 'iterated forcing' if contradiction else 'incidence survives')
        entry = {'class': index, 'representative': list(p), 'orbit_size': len(orbit),
                 'pair_admissible': pair_count, 'mixed_admissible': len(accepted),
                 'positive_equations': len(eqs), 'status': stage,
                 'propagation_trace': trace, 'fixed_variables': len(fixed)}
        if not contradiction:
            assert index == 48 and len(orbit) == 18
            assert list(p) == witness['map']
            assert [list(s) for s in accepted] == witness['signatures']
            selected_indices = witness['selected']
            assert len(set(selected_indices)) == len(selected_indices) == 72
            assert all(0 <= k < len(accepted) for k in selected_indices)
            selected = [accepted[k] for k in selected_indices]
            for i in range(27):
                for j in range(27):
                    assert sum(i in s and j in s for s in selected) == gram[i][j]
            assert all(int(k in selected_indices) == value for k, value in fixed.items())
            entry['orbit_members'] = [list(q) for q in orbit]
            entry['witness_selected_indices'] = selected_indices
            entry['witness_gram_verified'] = True
        results.append(entry)
    counts = Counter(row['status'] for row in results)
    assert counts == {'initial quota deficit': 29, 'initial forcing overflow': 25,
                      'iterated forcing': 4, 'incidence survives': 1}
    assert sum(row['orbit_size'] for row in results if row['status'] == 'incidence survives') == 18
    return {'complete': True, 'all_permutations_checked': 362880,
            'neighbor_avoiding_permutations': 2720, 'symmetry_classes': 59,
            'class_status_counts': dict(counts), 'excluded_classes': 58,
            'surviving_classes': 1, 'excluded_permutations': 2702,
            'surviving_permutations': 18,
            'scope': '27-core boundary incidence only; outside adjacencies are not assigned',
            'classes': results}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--witness', type=Path, default=Path(
        'experiments/logs/grids-and-triangles/two-rook-interfaces-incidence.json'))
    parser.add_argument('--output', type=Path)
    parser.add_argument('--verify', type=Path)
    args = parser.parse_args()
    result = audit(json.loads(args.witness.read_text()))
    if args.verify:
        assert json.loads(args.verify.read_text()) == result
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'classes'}), flush=True)
