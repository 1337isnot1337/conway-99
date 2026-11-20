"""Exact necessary interface model for seven all-red rook bases.

Root matchings are gauged to identity. Remaining labels are the eleven
rook automorphisms with no move to a rook neighbor. The model imposes all
visible common-neighbor bounds and the exact red-triangle count. SAT is
only a partial-interface witness, not a 99-vertex graph.
"""
from __future__ import annotations

import argparse
import hashlib
from itertools import combinations, permutations, product
import json
from pathlib import Path
from threading import Timer
import time

import numpy as np
from pysat.card import CardEnc, EncType
from pysat.formula import CNF, IDPool
from pysat.solvers import Solver


def compose(p, q):
    return tuple(p[q[i]] for i in range(len(p)))


def inverse(p):
    return tuple(p.index(i) for i in range(len(p)))


def data():
    points = list(product(range(3), repeat=2))
    rook = np.array([[int(x != y and (x[0] == y[0] or x[1] == y[1]))
                      for y in points] for x in points], dtype=np.int16)
    group = {tuple(3*sigma[b if swap else a]+tau[a if swap else b] for a, b in points)
             for sigma, tau, swap in product(permutations(range(3)), permutations(range(3)), (0, 1))}
    assert len(group) == 72
    allowed = sorted(p for p in group if not any(rook[x, p[x]] for x in range(9)))
    assert len(allowed) == 11
    identity = allowed.index(tuple(range(9)))
    diagonal = [((x+y) % 3, (x-y) % 3) for x, y in points]
    family, fixed = [], []
    for p in allowed:
        unchanged = [all(diagonal[p[x]][a] == diagonal[x][a] for x in range(9)) for a in range(2)]
        assert any(unchanged)
        family.append('identity' if all(unchanged) else 'u' if unchanged[1] else 'v')
        fixed.append(sum(x == p[x] for x in range(9)))
    assert sorted(family).count('u') == sorted(family).count('v') == 5
    index = {p: i for i, p in enumerate(allowed)}
    triangle = {}
    for a, b, c in product(range(11), repeat=3):
        holonomy = compose(inverse(allowed[c]), compose(allowed[b], allowed[a]))
        triangle[a, b, c] = index.get(holonomy)
    return rook, allowed, identity, family, fixed, triangle


def build(y, bases=7, require_both=True):
    assert y is None or (bases == 7 and y in (18, 27, 36))
    assert not require_both or bases >= 7
    rook, allowed, identity, family, fixed, triangle = data()
    pool = IDPool(); cnf = CNF()
    labels = {(i, j): [pool.id(('label', i, j, a)) for a in range(11)]
              for i, j in combinations(range(1, bases), 2)}
    for choices in labels.values():
        cnf.extend(CardEnc.equals(choices, 1, vpool=pool, encoding=EncType.pairwise).clauses)
    # If one diagonal coordinate is unused, its rook(-2) bundle gives
    # the forbidden eigenvalue b-3=4. Both factors must occur.
    if require_both:
        for name in ('u', 'v'):
            cnf.append([v for choices in labels.values() for a, v in enumerate(choices) if family[a] == name])

    faces = {}
    for i, j, k in combinations(range(bases), 3):
        if i == 0:
            faces[i, j, k] = labels[j, k]
            continue
        face = [pool.id(('face', i, j, k, a)) for a in range(11)]
        faces[i, j, k] = face
        cnf.extend(CardEnc.equals(face, 1, vpool=pool, encoding=EncType.pairwise).clauses)
        for (a, b, c), result in triangle.items():
            clause = [-labels[i, j][a], -labels[j, k][b], -labels[i, k][c]]
            if result is not None:
                clause.append(face[result])
            cnf.append(clause)

    # Sum of fixed-point counts over unordered base triples is t_R.
    # Divide by3: an identity contributes3, a reflection1, a translation0.
    count_terms = []
    for key, choices in faces.items():
        for a, v in enumerate(choices):
            if fixed[a] == 3:
                count_terms.append(v)
            elif fixed[a] == 9:
                count_terms.append(v)
                for copy in range(2):
                    w = pool.id(('identity-copy', key, copy))
                    cnf.extend([[-w, v], [w, -v]])
                    count_terms.append(w)
    if y is not None:
        cnf.extend(CardEnc.equals(count_terms, 9+y//9, vpool=pool, encoding=EncType.seqcounter).clauses)

    size = 9*bases
    A = [[False]*size for _ in range(size)]
    for i in range(bases):
        for x, z in combinations(range(9), 2):
            if rook[x, z]:
                A[9*i+x][9*i+z] = A[9*i+z][9*i+x] = True
    for j in range(1, bases):
        for x in range(9):
            A[x][9*j+x] = A[9*j+x][x] = True
    for (i, j), choices in labels.items():
        for x, z in product(range(9), repeat=2):
            disjunction = [choices[a] for a in range(11) if allowed[a][x] == z]
            if not disjunction:
                continue
            if len(disjunction) == 1:
                literal = disjunction[0]
            else:
                literal = pool.id(('adjacency', i, j, x, z))
                cnf.extend([[-v, literal] for v in disjunction])
                cnf.append([-literal, *disjunction])
            A[9*i+x][9*j+z] = A[9*j+z][9*i+x] = literal
    cache = {}
    def both(a, b):
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
    for i, j in combinations(range(bases), 2):
        for x, z in product(range(9), repeat=2):
            u, v = 9*i+x, 9*j+z
            terms = [A[u][v]]+[both(A[u][w], A[v][w]) for w in range(size)]
            bound = 2-sum(t is True for t in terms)
            literals = [t for t in terms if t is not True and t is not False]
            if bound < 0:
                cnf.append([])
            elif bound < len(literals):
                cnf.extend(CardEnc.atmost(literals, bound, vpool=pool, encoding=EncType.seqcounter).clauses)
    metadata = {'y': y, 'bases': bases, 'require_both_coordinates': require_both,
                'variables': cnf.nv, 'clauses': len(cnf.clauses),
                'allowed_maps': [list(p) for p in allowed], 'coordinate_families': family,
                'allowed_triangle_assignments': sum(v is not None for v in triangle.values())}
    return cnf, labels, metadata


def witness(selected, y, bases=7):
    rook, allowed, identity, family, fixed, triangle = data()
    size = 9*bases
    A = np.zeros((size, size), dtype=np.int64)
    maps = {}
    for i in range(bases):
        A[9*i:9*i+9, 9*i:9*i+9] = rook
    for i, j in combinations(range(bases), 2):
        p = tuple(range(9)) if i == 0 else allowed[selected[i, j]]
        maps[i, j], maps[j, i] = p, inverse(p)
        for x, z in enumerate(p):
            A[9*i+x, 9*j+z] = A[9*j+z, 9*i+x] = 1
    assert np.array_equal(A, A.T) and np.all(A.sum(axis=0) == bases+3)
    C = A@A+A
    assert all(C[i, j] <= 2 for i, j in combinations(range(size), 2))
    assert np.all(np.diag(C) == bases+3)
    counts = {'identity': 0, 'reflection': 0, 'translation': 0}
    for i, j, k in combinations(range(bases), 3):
        p = compose(maps[k, i], compose(maps[j, k], maps[i, j]))
        assert p in allowed
        f = sum(x == p[x] for x in range(9))
        counts['identity' if f == 9 else 'reflection' if f == 3 else 'translation'] += 1
    if y is not None:
        assert counts['reflection']+3*counts['identity'] == 9+y//9
    assert int(np.trace(A@A@A))//6 == 6*bases+3*counts['reflection']+9*counts['identity']
    gram = 12*np.eye(size, dtype=np.int64)-A@A-A+2*np.ones((size, size), dtype=np.int64)
    eigenvalues, vectors = np.linalg.eigh(gram)
    ray = None
    if eigenvalues[0] < -1e-7:
        for scale in (10, 100, 1000, 10000):
            candidate = np.rint(scale*vectors[:, 0]).astype(np.int64)
            value = sum(int(candidate[i])*int(gram[i, j])*int(candidate[j])
                        for i in range(size) for j in range(size))
            if value < 0:
                ray = {'vector': candidate.tolist(), 'value': value}
                break
    return {'labels': [[i, j, a] for (i, j), a in selected.items()],
            'face_counts': counts, 'minimum_gram_eigenvalue_approximate': float(eigenvalues[0]),
            'exact_negative_gram_vector': ray}


def controls():
    rook, allowed, identity, *_ = data()
    cnf, labels, _ = build(None, bases=3, require_both=False)
    with Solver(name='glucose4', bootstrap_with=cnf.clauses) as solver:
        for a in range(11):
            assert solver.solve(assumptions=[labels[1, 2][a]])
            witness({(1, 2): a}, None, bases=3)
    cnf, labels, _ = build(None, bases=4, require_both=False)
    with Solver(name='glucose4', bootstrap_with=cnf.clauses) as solver:
        assert solver.solve()
        positive = set(v for v in solver.get_model() if v > 0)
        selected = {edge: next(a for a, v in enumerate(choices) if v in positive)
                    for edge, choices in labels.items()}
        four = witness(selected, None, bases=4)
    result = {'three_base_maps_checked': 11, 'four_base_witness': four}
    print(json.dumps(result), flush=True)
    return result


def run(y, seconds, limit, output, require_both=True, proof_prefix=None, stop_first=False):
    begin = time.monotonic()
    cnf, labels, metadata = build(y, require_both=require_both)
    metadata['build_seconds'] = time.monotonic()-begin
    print(json.dumps({'built': metadata}), flush=True)
    records = []
    start = time.monotonic()
    status = 'model_limit'
    if proof_prefix:
        assert limit == 1
        proof_prefix.parent.mkdir(parents=True, exist_ok=True)
        cnf_path = proof_prefix.with_suffix('.cnf')
        cnf.to_file(cnf_path)
        metadata.update(cnf=str(cnf_path), cnf_sha256=hashlib.sha256(cnf_path.read_bytes()).hexdigest())
    with Solver(name='glucose4', bootstrap_with=cnf.clauses, with_proof=bool(proof_prefix)) as solver:
        for _ in range(limit):
            remaining = seconds-(time.monotonic()-start)
            if remaining <= 0:
                status = 'unknown'; break
            timer = Timer(remaining, solver.interrupt); timer.start()
            try:
                answer = solver.solve_limited(expect_interrupt=True)
            finally:
                timer.cancel()
            if answer is not True:
                status = 'solver_unsat' if answer is False else 'unknown'
                if answer is False and proof_prefix:
                    proof_path = proof_prefix.with_suffix('.drat')
                    proof_path.write_text('\n'.join(solver.get_proof())+'\n')
                    metadata.update(proof=str(proof_path), proof_sha256=hashlib.sha256(proof_path.read_bytes()).hexdigest())
                break
            positive = set(v for v in solver.get_model() if v > 0)
            selected = {edge: next(a for a, v in enumerate(choices) if v in positive)
                        for edge, choices in labels.items()}
            record = witness(selected, y)
            records.append(record)
            print(json.dumps({'model': len(records), 'gram_min': record['minimum_gram_eigenvalue_approximate'],
                              'exact_gram_obstruction': record['exact_negative_gram_vector'] is not None}), flush=True)
            if stop_first or record['exact_negative_gram_vector'] is None:
                status = 'partial_interface_witness'; break
            solver.add_clause([-labels[edge][a] for edge, a in selected.items()])
    result = {**metadata, 'status': status, 'seconds': time.monotonic()-start, 'models': records}
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({'status': status, 'models': len(records), 'seconds': result['seconds']}), flush=True)
    return result


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--y', type=int, choices=(18, 27, 36))
    p.add_argument('--seconds', type=float, default=30)
    p.add_argument('--limit', type=int, default=20)
    p.add_argument('--output', type=Path)
    p.add_argument('--controls', action='store_true')
    p.add_argument('--no-both-coordinates', action='store_true')
    p.add_argument('--no-face-count', action='store_true')
    p.add_argument('--stop-first', action='store_true')
    p.add_argument('--proof-prefix', type=Path)
    args = p.parse_args()
    if args.controls:
        result = controls()
        if args.output:
            args.output.write_text(json.dumps(result, indent=2)+'\n')
    else:
        assert args.y is not None or args.no_face_count
        run(None if args.no_face_count else args.y, args.seconds, args.limit, args.output,
            not args.no_both_coordinates, args.proof_prefix, args.stop_first)
