"""Exact forest census and necessary H/Z incidence tests for norm-16 cores.

This module is separate from the frozen coupled_shells certificate builders.
It uses only the forced degrees and pair-codegree capacities.  The sixteen
P/N core vertices enter through an unknown weighted overlap matrix C with
row sums four and entries in {0,1,2}; actual core incidence is not assumed.
"""
from __future__ import annotations

import argparse
from collections import Counter
from itertools import combinations, product
import json
from pathlib import Path
from threading import Timer
import time

from pysat.card import CardEnc, EncType
from pysat.formula import CNF, IDPool
from pysat.solvers import Solver


SHAPES = {
    'edge': (2, [(0, 1)]),
    'p3': (3, [(0, 1), (1, 2)]),
    'star3': (4, [(0, 1), (0, 2), (0, 3)]),
    'p4': (4, [(0, 1), (1, 2), (2, 3)]),
}


def forests():
    output = []
    for e in (0, 1):
        for a, b, c, d in product(range(7), repeat=4):
            if a + 2*b + 3*c + 3*d != 5 + e:
                continue
            vertices = 2*a + 3*b + 4*c + 4*d
            wedges = b + 3*c + 2*d
            if vertices > 11 or wedges > (9 if e == 0 else 4):
                continue
            edges = []
            offset = 0
            for name, count in zip(SHAPES, (a, b, c, d)):
                order, part = SHAPES[name]
                for _ in range(count):
                    edges += [(offset+i, offset+j) for i, j in part]
                    offset += order
            output.append({'id': f'e{e}_a{a}_b{b}_c{c}_d{d}', 'high_edges': e,
                           'counts': dict(zip(SHAPES, (a, b, c, d))),
                           'isolates': 11-vertices, 'wedges': wedges, 'edges': edges})
    return output


def graph(edges, order):
    adjacent = [set() for _ in range(order)]
    for i, j in edges:
        adjacent[i].add(j); adjacent[j].add(i)
    return adjacent


def add_lex(cnf, pool, left, right, name):
    prefix = None
    for k, (a, b) in enumerate(zip(reversed(left), reversed(right))):
        cnf.append(([-prefix] if prefix else []) + [-a, b])
        if k == len(left)-1: break
        same = pool.id(('lex', name, k))
        if prefix:
            cnf.extend([[-same, prefix], [-same, -a, b], [-same, a, -b],
                        [-prefix, a, b, same], [-prefix, -a, -b, same]])
        else:
            cnf.extend([[-same, -a, b], [-same, a, -b], [same, a, b], [same, -a, -b]])
        prefix = same


def build(forest, common_matrix=None, endpoints=None):
    e = forest['high_edges']
    endpoints = tuple(endpoints if endpoints is not None else ((0, 1) if e else ()))
    assert len(endpoints) == 2*e
    Z = graph(forest['edges'], 11)
    degree = [len(ns) for ns in Z]
    pool = IDPool(); cnf = CNF()
    x = {(h, z): pool.id(('incidence', h, z)) for h in range(8) for z in range(11)}
    overlap = {(i, j): [pool.id(('overlap', i, j, q)) for q in range(2)]
               for i, j in combinations(range(8), 2)}
    def C(i, j): return overlap[tuple(sorted((i, j)))];
    def equal(lits, rhs):
        cnf.extend(CardEnc.equals(lits, bound=rhs, vpool=pool, encoding=EncType.seqcounter).clauses)
    def atmost(lits, rhs):
        cnf.extend(CardEnc.atmost(lits, bound=rhs, vpool=pool, encoding=EncType.seqcounter).clauses)
    def both(a, b, name):
        v = pool.id(name)
        cnf.extend([[-v, a], [-v, b], [v, -a, -b]])
        return v
    for h in range(8):
        equal([x[h, z] for z in range(11)], 4 + int(h in endpoints))
        equal([q for k in range(8) if k != h for q in C(h, k)], 4)
    for z in range(11):
        equal([x[h, z] for h in range(8)], degree[z] + 2)
    for (h, k), (c1, c2) in overlap.items():
        cnf.append([-c2, c1])
        terms = [c1, c2]
        terms += [both(x[h,z], x[k,z], ('high-common',h,k,z)) for z in range(11)]
        atmost(terms, 2-int((h,k) == tuple(sorted(endpoints))))
    for z, w in combinations(range(11), 2):
        terms = [both(x[h,z], x[h,w], ('zero-common',h,z,w)) for h in range(8)]
        atmost(terms, 2-int(w in Z[z])-len(Z[z] & Z[w]))
    for h in range(8):
        for z in range(11):
            terms = [x[h,z]] + [x[h,w] for w in sorted(Z[z])]
            if h in endpoints:
                partner = endpoints[1] if h == endpoints[0] else endpoints[0]
                terms.append(x[partner,z])
            atmost(terms, 2)
    if common_matrix is not None:
        for (h,k),(c1,c2) in overlap.items():
            cnf.append([c1 if common_matrix[h][k] >= 1 else -c1])
            cnf.append([c2 if common_matrix[h][k] >= 2 else -c2])
    groups = ([range(8)] if e == 0 else [endpoints, [h for h in range(8) if h not in endpoints]]) if common_matrix is None else []
    for group in groups:
        for h,k in zip(group,list(group)[1:]):
            add_lex(cnf,pool,[x[h,z] for z in range(11)],[x[k,z] for z in range(11)],(h,k))
    return cnf, x, overlap


def verify(forest, masks, common, endpoints=None):
    assert len(masks) == 8
    e = forest['high_edges']; Z = graph(forest['edges'],11)
    endpoints = tuple(endpoints if endpoints is not None else ((0,1) if e else ()))
    N = [{z for z in range(11) if mask>>z&1} for mask in masks]
    for h in range(8):
        assert len(N[h]) == 4+int(h in endpoints)
        assert sum(common[h][k] for k in range(8)) == 4
        assert common[h][h] == 0
        assert sum(len(Z[z]) for z in N[h]) <= 6-2*int(h in endpoints)
    for z in range(11): assert sum(z in ns for ns in N) == len(Z[z])+2
    for h,k in combinations(range(8),2):
        assert common[h][k] == common[k][h] and 0 <= common[h][k] <= 2
        assert common[h][k]+len(N[h]&N[k])+int((h,k)==tuple(sorted(endpoints))) <= 2
    for z,w in combinations(range(11),2):
        assert sum(z in ns and w in ns for ns in N)+len(Z[z]&Z[w])+int(w in Z[z]) <= 2
    for h in range(8):
        for z in range(11):
            known = len(N[h] & Z[z]) + int(z in N[h])
            if h in endpoints:
                partner = endpoints[1] if h == endpoints[0] else endpoints[0]
                known += int(z in N[partner])
            assert known <= 2


def solve(forest, seconds=10, proof_prefix=None, common_matrix=None, endpoints=None):
    cnf,x,c=build(forest,common_matrix,endpoints);start=time.monotonic()
    with Solver(name='glucose4', bootstrap_with=cnf.clauses, with_proof=bool(proof_prefix)) as solver:
        timer=Timer(seconds,solver.interrupt);timer.start()
        try: status=solver.solve_limited(expect_interrupt=True)
        finally:timer.cancel()
        record=dict(forest)
        record.update(status='sat' if status is True else 'unsat' if status is False else 'unknown',
                      seconds=round(time.monotonic()-start,4),variables=cnf.nv,clauses=len(cnf.clauses))
        if status:
            truth={v for v in solver.get_model() if v>0}
            masks=[sum(1<<z for z in range(11) if x[h,z] in truth) for h in range(8)]
            common=[[0]*8 for _ in range(8)]
            for (h,k),bits in c.items():common[h][k]=common[k][h]=sum(v in truth for v in bits)
            verify(forest,masks,common,endpoints);record.update(masks=masks,common=common,endpoints=list(endpoints if endpoints is not None else ((0,1) if forest["high_edges"] else ())))
        elif status is False and proof_prefix:
            cnf.to_file(str(proof_prefix)+'.cnf')
            Path(str(proof_prefix)+'.drat').write_text('\n'.join(solver.get_proof())+'\n')
    return record


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path);p.add_argument('--seconds',type=float,default=10)
    p.add_argument('--proof-directory',type=Path)
    a=p.parse_args();out=[]
    for f in forests():
        prefix=a.proof_directory/f['id'] if a.proof_directory else None
        r=solve(f,a.seconds,prefix);out.append(r)
        print(f"{r['id']}: {r['status']} {r['seconds']}s; {r['isolates']} isolates, {r['wedges']} wedges",flush=True)
        if a.output:a.output.write_text(json.dumps(out,indent=2)+'\n')
    print(dict(Counter((r['high_edges'],r['status']) for r in out)),flush=True)


if __name__=='__main__':main()
