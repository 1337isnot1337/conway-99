"""Necessary symmetric eight-vertex extension tests for norm-16 templates.

The input is a list of 24-vertex incidence-template representatives generated
by coupled_shells.py.  SAT here is a partial-completion witness only.
"""
from __future__ import annotations

import argparse
from functools import lru_cache
from itertools import combinations
import json
from pathlib import Path

import z3


def matching_possible(capacity, pdeg, ndeg):
    if min(pdeg + ndeg) < 0 or sum(pdeg) != sum(ndeg):
        return False
    ps = sorted((p for p in range(8) if pdeg[p]),
                key=lambda p: sum(capacity[p][n] > 0 and ndeg[n] > 0 for n in range(8)))

    @lru_cache(None)
    def visit(k, residual):
        if k == len(ps):
            return not any(residual)
        p = ps[k]
        need = pdeg[p]
        choices = [n for n in range(8) if capacity[p][n] and residual[n]]
        if need == 1:
            candidates = [(n,) for n in choices]
        elif need == 2:
            candidates = list(combinations(choices, 2))
            candidates += [(n, n) for n in choices if capacity[p][n] >= 2 and residual[n] >= 2]
        elif need == 0:
            candidates = [()]
        else:
            raise AssertionError(need)
        for ns in candidates:
            rest = list(residual)
            for n in ns:
                rest[n] -= 1
            if min(rest) >= 0 and visit(k + 1, tuple(rest)):
                return True
        return False

    return visit(0, tuple(ndeg))


def row_domains(rows, chosen, residual):
    B = [[row >> n & 1 for n in range(8)] for row in rows]
    sets = [(set(p), set(n)) for p, n in chosen]
    domains = []
    overlap = [[len(p & q) + len(n & m) for q, m in sets] for p, n in sets]
    for x, (pp, nn) in enumerate(sets):
        rP = [2 - int(p in pp) - sum(B[p][n] for n in nn) for p in range(8)]
        rN = [2 - int(n in nn) - sum(B[p][n] for p in pp) for n in range(8)]
        assert sum(rP) == sum(rN) == 6
        capacity = [[0 if p in pp and n in nn else residual[p][n] for n in range(8)]
                    for p in range(8)]
        allowed = [y for y in range(8) if x != y and overlap[x][y] <= 1]
        domain = []
        for degree in range(4):
            for neighbors in combinations(allowed, degree):
                pdeg, ndeg = rP[:], rN[:]
                for y in neighbors:
                    for p in sets[y][0]:
                        pdeg[p] -= 1
                    for n in sets[y][1]:
                        ndeg[n] -= 1
                if matching_possible(capacity, pdeg, ndeg):
                    domain.append(sum(1 << y for y in neighbors))
        domains.append(domain)
    return domains, overlap


def feasible_high_graph(rows, chosen, residual, timeout_ms=3000):
    domains, overlap = row_domains(rows, chosen, residual)
    if any(not d for d in domains):
        return {"status": "empty_row", "domain_sizes": list(map(len, domains))}
    solver = z3.Solver()
    solver.set(timeout=timeout_ms)
    edges = {(i, j): z3.Bool(f"e{i}_{j}") for i, j in combinations(range(8), 2)}
    def edge(i, j):
        return edges[tuple(sorted((i, j)))]
    for i, masks in enumerate(domains):
        solver.add(z3.Or(*[z3.And(*[edge(i, j) == bool(mask >> j & 1)
                                   for j in range(8) if i != j]) for mask in masks]))
    for i, j in combinations(range(8), 2):
        common = z3.Sum([z3.If(z3.And(edge(i, k), edge(j, k)), 1, 0)
                         for k in range(8) if k not in (i, j)])
        solver.add(common + z3.If(edge(i, j), 1, 0) <= 2 - overlap[i][j])
    status = solver.check()
    result = {"status": str(status), "domain_sizes": list(map(len, domains))}
    if status == z3.sat:
        model = solver.model()
        result["edges"] = [[i, j] for (i, j), var in edges.items() if z3.is_true(model.eval(var))]
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--timeout-ms", type=int, default=3000)
    args = parser.parse_args()
    data = json.loads(args.input.read_text())
    from collections import Counter
    results = []
    for core in data:
        counts = Counter()
        block = {"core": core["core"], "results": []}
        for i, orbit in enumerate(core["orbits"]):
            result = feasible_high_graph(core["rows"], orbit["high"], orbit["single"], args.timeout_ms)
            result["orbit"] = i
            counts[result["status"]] += 1
            block["results"].append(result)
        results.append(block)
        print(f"core {core['core']}: {dict(counts)}", flush=True)
    if args.output:
        args.output.write_text(json.dumps(results, indent=2) + "\n")


if __name__ == "__main__":
    main()
