"""Complete staged common-neighbor exclusion of five isomorphic rook interfaces.

Gauge 01=12=23=34=I and02=P. Write04=r,03=t*r,14=r*w,13=q,24=s,
where r is one of72 rook automorphisms and q,t,w,s range over the18-map
orbit from the three-grid classification. Check23328 four-cores first,
then only2592 extensions of their eight survivors.
"""

import argparse
from itertools import combinations, permutations, product
import json
from pathlib import Path


IDENTITY = tuple(range(9))
P = (0, 5, 7, 8, 6, 1, 4, 2, 3)


def rook(i, j):
    return i != j and (i // 3 == j // 3 or i % 3 == j % 3)


def compose(p, q):
    return tuple(p[q[i]] for i in range(9))


def domains():
    autos = set()
    for a, b in product(permutations(range(3)), repeat=2):
        autos.add(tuple(3*a[x]+b[y] for x, y in product(range(3), repeat=2)))
        autos.add(tuple(3*a[y]+b[x] for x, y in product(range(3), repeat=2)))
    assert len(autos) == 72
    orbit = set()
    for q in autos:
        qi = tuple(q.index(i) for i in range(9))
        orbit.add(compose(q, compose(P, qi)))
    assert len(orbit) == 18
    assert all(compose(p, p) == IDENTITY for p in orbit)
    return sorted(orbit), sorted(autos)


def internal_rows(bases):
    rows = [0]*(9*bases)
    for base in range(bases):
        for x, y in combinations(range(9), 2):
            if rook(x, y):
                rows[9*base+x] |= 1 << (9*base+y)
                rows[9*base+y] |= 1 << (9*base+x)
    return rows


def add(rows, a, b, mapping):
    for x, y in enumerate(mapping):
        rows[9*a+x] |= 1 << (9*b+y)
        rows[9*b+y] |= 1 << (9*a+x)


def first_violation(rows):
    for i, j in combinations(range(len(rows)), 2):
        if (rows[i] & rows[j]).bit_count()+((rows[i] >> j) & 1) > 2:
            return len(rows)*i+j
    return -1


def replay_code(rows, code):
    if code == -1:
        assert first_violation(rows) == -1
        return
    i, j = divmod(code, len(rows))
    assert 0 <= i < j < len(rows)
    # Direct membership counting verifies the witness independently of
    # the intersection/popcount operation that selected the pair.
    common = sum(((rows[i] >> k) & 1)*((rows[j] >> k) & 1)
                 for k in range(len(rows)))
    assert common+((rows[i] >> j) & 1) > 2


def four_base(q):
    rows = internal_rows(4)
    for a, b, p in ((0, 1, IDENTITY), (0, 2, P),
                    (1, 2, IDENTITY), (1, 3, q), (2, 3, IDENTITY)):
        add(rows, a, b, p)
    return rows


def five_base(case, orbit, autos):
    q, t, r = orbit[case['q']], orbit[case['t']], autos[case['r']]
    rows = internal_rows(5)
    for a, b, p in ((0, 1, IDENTITY), (0, 2, P), (0, 3, compose(t, r)),
                    (0, 4, r), (1, 2, IDENTITY), (1, 3, q),
                    (2, 3, IDENTITY), (3, 4, IDENTITY)):
        add(rows, a, b, p)
    return rows


def audit(classification):
    orbit, autos = domains()
    survivor, = [row for row in classification['classes'] if row['status'] == 'incidence survives']
    assert classification['complete'] and classification['excluded_classes'] == 58
    assert survivor['representative'] == list(P)
    assert survivor['orbit_members'] == [list(p) for p in orbit]

    four_codes = []
    four_survivors = []
    early_q = []
    full_four_count = 0
    for qi, q in enumerate(orbit):
        partial = four_base(q)
        early_code = first_violation(partial)
        if early_code >= 0:
            early_q.append(qi)
        for ti, t in enumerate(orbit):
            for ri, r in enumerate(autos):
                if early_code >= 0:
                    code = early_code
                else:
                    rows = partial.copy()
                    add(rows, 0, 3, compose(t, r))
                    assert all(row.bit_count() == 7 for row in rows)
                    full_four_count += 1
                    code = first_violation(rows)
                four_codes.append(code)
                if code == -1:
                    four_survivors.append({'q': qi, 't': ti, 'r': ri})
    assert early_q == [0, 1] and full_four_count == 20736
    assert len(four_codes) == 23328 and len(four_survivors) == 8

    five_codes = []
    early_base_count = early_w_count = full_five_count = 0
    for case in four_survivors:
        base = five_base(case, orbit, autos)
        code0 = first_violation(base)
        if code0 >= 0:
            early_base_count += 1
        r = autos[case['r']]
        for w in orbit:
            if code0 >= 0:
                five_codes.extend([code0]*18)
                continue
            partial = base.copy()
            add(partial, 1, 4, compose(r, w))
            code1 = first_violation(partial)
            if code1 >= 0:
                early_w_count += 1
                five_codes.extend([code1]*18)
                continue
            for s in orbit:
                rows = partial.copy()
                add(rows, 2, 4, s)
                assert all(row.bit_count() == 8 for row in rows)
                full_five_count += 1
                code = first_violation(rows)
                assert code >= 0
                five_codes.append(code)
    assert (early_base_count, early_w_count, full_five_count) == (4, 68, 72)
    assert len(five_codes) == 2592 and min(five_codes) >= 0
    assert 324*early_base_count+18*early_w_count+full_five_count == 2592
    return {
        'status': 'all five-cycles of rook-isomorphic interfaces excluded',
        'complete': True,
        'fixed_diagonal': list(P),
        'orbit_maps': [list(p) for p in orbit],
        'rook_automorphisms': [list(p) for p in autos],
        'full_assignment_space_after_gauge': 72*18**4,
        'four_core_assignments': 23328,
        'four_core_partial_q_rejections': early_q,
        'four_core_full_checks': full_four_count,
        'four_core_survivors': four_survivors,
        'four_core_certificate_codes': four_codes,
        'five_core_extensions': 2592,
        'five_core_partial_base_rejections': early_base_count,
        'five_core_partial_w_rejections': early_w_count,
        'five_core_full_checks': full_five_count,
        'five_core_certificate_codes': five_codes,
        'surviving_five_cores': 0,
        'certificate_code_convention': 'code=n*i+j records a violating pair; -1 is a fully checked four-core survivor',
        'four_core_order': 'q, then t, then r in their sorted domains',
        'five_core_order': 'saved four-core survivor, then w, then s in sorted orbit order',
        'partner_graph_consequence': 'maximum degree two; cycles have length at least six',
        'scope': 'uses the separate exact three-grid classification and disjoint-partner lemma; no red assumption',
    }


def replay(result):
    """Rebuild every complete core, including those rejected early during discovery."""
    orbit, autos = domains()
    assert result['orbit_maps'] == [list(p) for p in orbit]
    assert result['rook_automorphisms'] == [list(p) for p in autos]
    assert len(result['four_core_certificate_codes']) == 23328
    found = []
    for qi, q in enumerate(orbit):
        partial = four_base(q)
        for ti, t in enumerate(orbit):
            for ri, r in enumerate(autos):
                rows = partial.copy()
                add(rows, 0, 3, compose(t, r))
                assert all(row.bit_count() == 7 for row in rows)
                index = (qi*18+ti)*72+ri
                code = result['four_core_certificate_codes'][index]
                replay_code(rows, code)
                if code == -1:
                    found.append({'q': qi, 't': ti, 'r': ri})
    assert found == result['four_core_survivors'] and len(found) == 8
    assert len(result['five_core_certificate_codes']) == 2592
    for case_index, case in enumerate(found):
        base = five_base(case, orbit, autos)
        r = autos[case['r']]
        for wi, w in enumerate(orbit):
            partial = base.copy()
            add(partial, 1, 4, compose(r, w))
            for si, s in enumerate(orbit):
                rows = partial.copy()
                add(rows, 2, 4, s)
                assert all(row.bit_count() == 8 for row in rows)
                code = result['five_core_certificate_codes'][(case_index*18+wi)*18+si]
                assert code >= 0
                replay_code(rows, code)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--classification', type=Path, default=Path(
        'experiments/logs/grids-and-triangles/two-rook-interfaces.json'))
    parser.add_argument('--output', type=Path)
    parser.add_argument('--verify', type=Path)
    args = parser.parse_args()
    result = audit(json.loads(args.classification.read_text()))
    if args.verify:
        saved = json.loads(args.verify.read_text())
        replay(saved)
        assert saved == result
    else:
        replay(result)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2)+'\n')
    hidden = {'orbit_maps', 'rook_automorphisms', 'four_core_certificate_codes',
              'five_core_certificate_codes'}
    print(json.dumps({k: v for k, v in result.items() if k not in hidden}), flush=True)
