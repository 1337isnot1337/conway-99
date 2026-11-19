"""Fix only a canonical Z forest, with every H/Z and low incidence free.

This is a separate builder.  It does not contain the old ordering of Z
vertices by their H-neighborhoods.  The three forests and independent H
are justified for the two surviving doubled-edge support templates.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
from itertools import combinations
import json
from pathlib import Path
import subprocess
from threading import Timer
import time

from pysat.card import CardEnc, EncType
from pysat.formula import CNF, IDPool
from pysat.solvers import Solver

from coupled_shells_incidence import verify
from coupled_shells_low import low_labels
from coupled_zero_completion import matrices
from coupled_zero_structure import add_lex, forests


FOREST_IDS = ('e0_a5_b0_c0_d0', 'e0_a3_b1_c0_d0', 'e0_a1_b2_c0_d0')


def build(block, orbit_index, forest_index, order_low=True):
    assert block['core'] == 0 and orbit_index in (1, 2)
    forest = next(f for f in forests() if f['id'] == FOREST_IDS[forest_index])
    orbit = block['orbits'][orbit_index]
    labels = low_labels(orbit['single']); assert len(labels) == 64
    pool = IDPool(); cnf = CNF()
    A = [[False for _ in range(99)] for _ in range(99)]
    def put(i, j, value):
        assert i != j and A[i][j] is False
        A[i][j] = A[j][i] = value
    for p in range(8):
        for n in range(8):
            if (block['rows'][p] >> n) & 1:
                put(p, n+8, True)
    for h, (pp, nn) in enumerate(orbit['high'], 16):
        for p in pp:
            put(h, p, True)
        for n in nn:
            put(h, n+8, True)
    for l, (p, n) in enumerate(labels, 35):
        put(l, p, True); put(l, n+8, True)
    for z, w in forest['edges']:
        put(z+24, w+24, True)
    hz = {(h, z): pool.id(('hz', h, z)) for h in range(8) for z in range(11)}
    hl = {(h, l): pool.id(('hl', h, l)) for h in range(8) for l in range(64)}
    zl = {(z, l): pool.id(('zl', z, l)) for z in range(11) for l in range(64)}
    for (h, z), v in hz.items():
        put(h+16, z+24, v)
    for (h, l), v in hl.items():
        put(h+16, l+35, v)
    for (z, l), v in zl.items():
        put(z+24, l+35, v)
    cache = {}
    def AND(a, b):
        if a is False or b is False:
            return False
        if a is True:
            return b
        if b is True or a == b:
            return a
        key = tuple(sorted((a, b)))
        if key not in cache:
            v = pool.id(('and', *key)); cache[key] = v
            cnf.extend([[-v, a], [-v, b], [v, -a, -b]])
        return cache[key]
    def count(expressions, bound, exact):
        expressions = list(expressions)
        bound -= sum(x is True for x in expressions)
        literals = [x for x in expressions if x is not True and x is not False]
        if bound < 0 or (exact and bound > len(literals)):
            cnf.append([])
        elif exact:
            cnf.extend(CardEnc.equals(literals, bound=bound, vpool=pool,
                                     encoding=EncType.seqcounter).clauses)
        elif bound < len(literals):
            cnf.extend(CardEnc.atmost(literals, bound=bound, vpool=pool,
                                     encoding=EncType.seqcounter).clauses)
    # Every core vertex has complete degree fourteen.
    for i in range(35):
        count(A[i], 14, True)
    # Complete common-neighbor equations on the 35-vertex core.
    for i, j in combinations(range(35), 2):
        terms = [A[i][j]]+[AND(A[i][k], A[j][k]) for k in range(99)]
        count(terms, 2, True)
    # Necessary common-neighbor upper bounds on all remaining pairs.
    for i in range(35):
        for l in range(35, 99):
            terms = [A[i][l]]+[AND(A[i][k], A[l][k]) for k in range(35)]
            count(terms, 2, False)
    for l, m in combinations(range(35, 99), 2):
        count([AND(A[l][k], A[m][k]) for k in range(35)], 2, False)
    # Forced exterior degrees from the norm-16 partition.
    for h in range(8):
        count([hz[h, z] for z in range(11)], 4, True)
        count([hl[h, l] for l in range(64)], 6, True)
    zd = [sum(z in edge for edge in forest['edges']) for z in range(11)]
    for z in range(11):
        count([hz[h, z] for h in range(8)], zd[z]+2, True)
    for l in range(64):
        # Complement the eight H/L literals: d_Z(l)-d_H(l)=1.
        count([zl[z, l] for z in range(11)]+[-hl[h, l] for h in range(8)], 9, True)
    # L vertices with the same P/N signature remain interchangeable.
    # No symmetry condition is imposed on H/Z neighborhoods of Z vertices.
    if order_low:
        groups = defaultdict(list)
        for l, label in enumerate(labels):
            groups[tuple(label)].append(l)
        for label, group in groups.items():
            for l, m in zip(group, group[1:]):
                left = [zl[z, l] for z in range(11)]+[hl[h, l] for h in range(8)]
                right = [zl[z, m] for z in range(11)]+[hl[h, m] for h in range(8)]
                add_lex(cnf, pool, left, right, ('duplicate-low', label, l, m))
    return cnf, hz, hl, zl, forest


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_certificate(manifest, checker):
    r = json.loads(manifest.read_text())
    block = {'core': r['core'], 'rows': r['rows'],
             'orbits': [None]*(r['orbit']+1)}
    block['orbits'][r['orbit']] = r['template']
    cnf, *_ = build(block, r['orbit'], r['forest_index'], r['order_low'])
    core = manifest.parent/r['core_file']; proof = manifest.parent/r['proof_file']
    assert digest(core) == r['core_cnf_sha256'] and digest(proof) == r['proof_sha256']
    original = {tuple(sorted(c)) for c in cnf.clauses}
    assert all(tuple(sorted(c)) in original for c in CNF(from_file=core).clauses)
    run = subprocess.run([str(checker), str(core), str(proof), '-w'],
                         capture_output=True, text=True, timeout=60, check=False)
    assert run.returncode == 0 and 's VERIFIED' in run.stdout, (run.stdout, run.stderr)
    print('PASS: exact fixed-forest exclusion', r['core'], r['orbit'], r['forest_index'])


def solve(block, orbit_index, forest_index, seconds, destination, checker, order_low=True):
    start = time.monotonic()
    cnf, hz, hl, zl, forest = build(block, orbit_index, forest_index, order_low)
    result = {'core': block['core'], 'orbit': orbit_index, 'forest_index': forest_index,
              'forest': forest['id'], 'order_low': order_low, 'variables': cnf.nv,
              'clauses': len(cnf.clauses), 'build_seconds': time.monotonic()-start}
    print('Built:', result, flush=True)
    if len(cnf.clauses) > 1500000:
        return dict(result, status='build_budget')
    start = time.monotonic()
    with Solver(name='glucose4', bootstrap_with=cnf.clauses, with_proof=True) as solver:
        timer = Timer(seconds, solver.interrupt); timer.start()
        try:
            status = solver.solve_limited(expect_interrupt=True)
        finally:
            timer.cancel()
        result.update(status='sat' if status is True else 'solver_unsat' if status is False else 'unknown',
                      seconds=time.monotonic()-start)
        if status:
            truth = {v for v in solver.get_model() if v > 0}
            oe = [[z+8, w+8] for z, w in forest['edges']]
            oe += [[h, z+8] for (h, z), v in hz.items() if v in truth]
            he = [[h, l] for (h, l), v in hl.items() if v in truth]
            ze = [[z+8, l] for (z, l), v in zl.items() if v in truth]
            orbit = block['orbits'][orbit_index]
            verify(block['rows'], orbit, oe, he, ze)
            B, N = matrices(block, orbit, {'edges': oe, 'low_edges': he})
            for z, l in ze:
                N[z+16, l] = 1
            result.update(edges=oe, high_low_edges=he, zero_low_edges=ze,
                          B=B.tolist(), N=N.tolist())
        elif status is False:
            prefix = destination/f'coupled-zero-forest-0-{orbit_index}-{forest_index}'
            full = prefix.with_name(prefix.name+'-full.cnf')
            raw = prefix.with_name(prefix.name+'-raw.drat')
            cnf.to_file(full); raw.write_text('\n'.join(solver.get_proof())+'\n')
            result.update(full_cnf=str(full), raw_proof=str(raw),
                          full_cnf_sha256=digest(full), raw_proof_sha256=digest(raw))
    if result['status'] == 'solver_unsat' and checker:
        core = prefix.with_name(prefix.name+'-core.cnf'); proof = prefix.with_suffix('.drat')
        run = subprocess.run([str(checker), str(full), str(raw), '-w', '-c', str(core),
                              '-l', str(proof)], capture_output=True, text=True,
                             timeout=60, check=False)
        assert run.returncode == 0 and 's VERIFIED' in run.stdout, (run.stdout, run.stderr)
        manifest = prefix.with_name(prefix.name+'-certificate.json')
        record = {k: result[k] for k in ('core', 'orbit', 'forest_index', 'order_low', 'full_cnf_sha256')}
        record.update(rows=block['rows'], template=block['orbits'][orbit_index],
                      core_file=core.name, proof_file=proof.name,
                      core_cnf_sha256=digest(core), proof_sha256=digest(proof),
                      checker_revision='2e3b2dc0ecf938addbd779d42877b6ed69d9a985')
        manifest.write_text(json.dumps(record, indent=2)+'\n')
        check_certificate(manifest, checker)
        result.update(status='unsat_checked', certificate=str(manifest),
                      core_bytes=core.stat().st_size, proof_bytes=proof.stat().st_size)
    return result


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--orbits', type=Path,
                   default=Path('experiments/logs/eigenlattices/coupled-shells-orbits.json'))
    p.add_argument('--orbit', type=int, choices=(1, 2), required=True)
    p.add_argument('--forest', type=int, choices=(0, 1, 2), required=True)
    p.add_argument('--seconds', type=float, default=60)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--destination', type=Path, default=Path('experiments/workspace'))
    p.add_argument('--drat-trim', type=Path)
    p.add_argument('--no-low-order', action='store_true')
    p.add_argument('--verify-certificate', type=Path)
    a = p.parse_args()
    if a.verify_certificate:
        assert a.drat_trim is not None
        check_certificate(a.verify_certificate, a.drat_trim.resolve()); return
    block = next(b for b in json.loads(a.orbits.read_text()) if b['core'] == 0)
    result = solve(block, a.orbit, a.forest, a.seconds, a.destination.resolve(),
                   a.drat_trim.resolve() if a.drat_trim else None, not a.no_low_order)
    a.output.write_text(json.dumps(result, indent=2)+'\n')
    print({k: v for k, v in result.items() if k not in
           ('edges', 'high_low_edges', 'zero_low_edges', 'B', 'N')}, flush=True)


if __name__ == '__main__':
    main()
