"""Exact defect-edge templates for norm-16 negative eigenvectors.

Only the five pre-existing 8-by-8 core representatives are input.  This checks
local common-neighbor necessities, not the existence of a 99-vertex completion.
Run from anywhere; input/output paths are explicit.
"""
from __future__ import annotations

import argparse
from collections import Counter
from itertools import combinations, permutations
import json
from pathlib import Path


def deficit_edges(rows: tuple[int, ...]) -> tuple[tuple[int, int], ...]:
    """Unordered pairs repeated by their missing common-neighbor multiplicity."""
    return tuple((i, j) for i, j in combinations(range(8), 2)
                 for _ in range(2 - (rows[i] & rows[j]).bit_count()))


def transpose(rows: tuple[int, ...]) -> tuple[int, ...]:
    return tuple(sum(((rows[i] >> j) & 1) << i for i in range(8))
                 for j in range(8))


def verify_core(rows: tuple[int, ...]) -> tuple[tuple[tuple[int, int], ...], ...]:
    cols = transpose(rows)
    assert all(x.bit_count() == 4 for x in rows + cols)
    for side in (rows, cols):
        assert all((side[i] & side[j]).bit_count() <= 2
                   for i, j in combinations(range(8), 2))
    edges = (deficit_edges(rows), deficit_edges(cols))
    for side, pairs in zip((rows, cols), edges):
        assert len(pairs) == 8
        degrees = Counter(v for pair in pairs for v in pair)
        assert all(degrees[v] == 2 for v in range(8))
        support = set(pairs)
        unseen = set(range(8))
        while unseen:
            component = {min(unseen)}
            while True:
                more = {v for edge in support if component.intersection(edge) for v in edge}
                if more <= component:
                    break
                component |= more
            assert len(component) % 2 == 0
            assert all(sum((side[v] >> j) & 1 for v in component) == len(component) // 2
                       for j in range(8))
            unseen -= component
        assert not any(all(tuple(sorted(pair)) in support
                           for pair in combinations(triple, 2))
                       for triple in combinations(range(8), 3))
    return edges


def enumerate_templates(rows: tuple[int, ...], callback=None) -> dict:
    """Pair the two eight-edge deficit multisets; unnamed exterior rows.

    The row side is P.  Each template consists of eight (P-pair,N-pair)
    rectangles.  Repeated P pairs are assigned in nondecreasing N-pair order
    so each unordered multiset is counted exactly once.  Remaining 1+1 row
    multiplicities are then forced by the P/N common-neighbor equations.
    """
    pedges, nedges = verify_core(rows)
    ntypes = sorted(set(nedges))
    remaining = Counter(nedges)
    residual = [[2 - ((rows[p] >> n) & 1) for n in range(8)]
                for p in range(8)]
    choices = []
    for pp in pedges:
        allowed = []
        for nn in ntypes:
            # The four core neighbors of an exterior point induce a matching.
            if any(sum((rows[p] >> n) & 1 for n in nn) > 1 for p in pp):
                continue
            if any(sum((rows[p] >> n) & 1 for p in pp) > 1 for n in nn):
                continue
            allowed.append(nn)
        choices.append(allowed)
    chosen = []
    counts = Counter()
    representatives = {}
    excluded = 0

    def visit(k: int) -> None:
        nonlocal excluded
        if k == 8:
            assert sum(map(sum, residual)) == 64
            # A repeated 1+1 row can occur only at a nonedge and at most twice.
            assert all(0 <= residual[p][n] <= 2 - ((rows[p] >> n) & 1)
                       for p in range(8) for n in range(8))
            # Distinct exterior vertices with three core common neighbors
            # have already been rejected; residual 1+1 rows contribute only 2.
            high_edges = []
            for i, j in combinations(range(8), 2):
                p, n = chosen[i]
                q, m = chosen[j]
                overlap = len(set(p) & set(q)) + len(set(n) & set(m))
                if overlap <= 1:
                    high_edges.append((i, j))
            fingerprint = (len(high_edges), sum(v == 2 for row in residual for v in row))
            if four_high_obstruction(chosen) is not None:
                excluded += 1
            if callback is not None:
                callback(tuple(chosen), tuple(tuple(row) for row in residual))
            counts[fingerprint] += 1
            representatives.setdefault(fingerprint, list(chosen))
            return
        pp = pedges[k]
        previous = chosen[-1][1] if k and pp == pedges[k - 1] else None
        pset = set(pp)
        for nn in choices[k]:
            if not remaining[nn] or (previous is not None and nn < previous):
                continue
            if any(residual[p][n] == 0 for p in pp for n in nn):
                continue
            nset = set(nn)
            if any(len(pset & set(q)) + len(nset & set(m)) > 2 for q, m in chosen):
                continue
            remaining[nn] -= 1
            for p in pp:
                for n in nn:
                    residual[p][n] -= 1
            chosen.append((pp, nn))
            visit(k + 1)
            chosen.pop()
            for p in pp:
                for n in nn:
                    residual[p][n] += 1
            remaining[nn] += 1

    visit(0)
    return {
        "core_rows": list(rows),
        "positive_deficit_edges": [list(x) for x in pedges],
        "negative_deficit_edges": [list(x) for x in nedges],
        "templates": sum(counts.values()),
        "excluded_by_four_high": excluded,
        "remaining_templates": sum(counts.values()) - excluded,
        "profiles": [
            {"allowed_high_edges": key[0], "doubled_single_signatures": key[1],
             "templates": value, "representative": representatives[key]}
            for key, value in sorted(counts.items())
        ],
    }


def four_high_obstruction(chosen):
    """Return an explicit four-vertex certificate of 16 <= 15, or None."""
    masks = [sum(1 << p for p in pp) + sum(1 << (n + 8) for n in nn)
             for pp, nn in chosen]
    common = [[(a & b).bit_count() for b in masks] for a in masks]
    for selected in combinations(range(8), 4):
        pair_sum = sum(common[i][j] for i, j in combinations(selected, 2))
        if pair_sum < 8:
            continue
        # k <= 1 + binom(k, 2) for every nonnegative integer k.
        upper = 11 + 12 - pair_sum
        assert upper < 16
        return {"vertices": list(selected), "core_pair_sum": pair_sum,
                "incidence_lower": 16, "incidence_upper": upper}
    return None


def independent_count(rows):
    """Independent exhaustive permutation replay using full incidence products."""
    import numpy as np
    pedges, nedges = verify_core(rows)
    B = np.array([[row >> j & 1 for j in range(8)] for row in rows], dtype=np.int64)
    A = np.block([[np.zeros((8, 8), dtype=np.int64), B],
                  [B.T, np.zeros((8, 8), dtype=np.int64)]])
    result = 0
    for assignment in set(permutations(nedges)):
        if any(pedges[i] == pedges[i - 1] and assignment[i] < assignment[i - 1]
               for i in range(1, 8)):
            continue
        N = np.zeros((16, 8), dtype=np.int64)
        for h, (pp, nn) in enumerate(zip(pedges, assignment)):
            N[list(pp), h] = 1
            N[[n + 8 for n in nn], h] = 1
        high_common = N.T @ N
        np.fill_diagonal(high_common, 0)
        if high_common.max() > 2 or (A @ N + N).max() > 2:
            continue
        residual = 2 - B - N[:8] @ N[8:].T
        if residual.min() < 0:
            continue
        assert residual.sum() == 64
        result += 1
    return result


def orbit_collector(rows):
    """Canonicalize the colored 24-vertex core under side-preserving maps."""
    import pynauty
    representatives = {}
    def collect(chosen, residual):
        adjacent = {i: [] for i in range(24)}
        for p in range(8):
            for n in range(8):
                if rows[p] >> n & 1:
                    adjacent[p].append(n + 8)
                    adjacent[n + 8].append(p)
        for h, (pp, nn) in enumerate(chosen, 16):
            for p in pp:
                adjacent[p].append(h)
                adjacent[h].append(p)
            for n in nn:
                adjacent[n + 8].append(h)
                adjacent[h].append(n + 8)
        graph = pynauty.Graph(24, adjacency_dict=adjacent,
                              vertex_coloring=[set(range(8)), set(range(8, 16)), set(range(16, 24))])
        key = pynauty.certificate(graph)
        representatives.setdefault(key, {"high": chosen, "single": residual,
                                         "four_high_obstruction": four_high_obstruction(chosen),
                                         "labeled_templates": 0})
        representatives[key]["labeled_templates"] += 1
    return representatives, collect


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cores", type=Path,
                        default=Path(__file__).with_name("signed-eight-cores.json"))
    parser.add_argument("--output", type=Path)
    parser.add_argument("--orbits", type=Path)
    parser.add_argument("--independent", action="store_true")
    args = parser.parse_args()
    data = json.loads(args.cores.read_text())
    assert len(data) == 5
    result = []
    orbit_data = []
    for i, values in enumerate(data):
        rows = tuple(values)
        representatives, callback = orbit_collector(rows) if args.orbits else ({}, None)
        record = enumerate_templates(rows, callback)
        if args.independent:
            replay = independent_count(rows)
            assert replay == record["templates"]
            record["independent_count"] = replay
        if args.orbits:
            record["orbits"] = len(representatives)
            record["excluded_orbits"] = sum(v["four_high_obstruction"] is not None for v in representatives.values())
            record["remaining_orbits"] = record["orbits"] - record["excluded_orbits"]
            orbit_data.append({"core": i, "rows": list(rows), "orbits": list(representatives.values())})
        record["core"] = i
        result.append(record)
        print(f"core {i}: {record['templates']} deficit-edge templates; "
              f"{record['excluded_by_four_high']} excluded by four-high count; "
              f"{record['remaining_templates']} remain"
              + (f"; {len(representatives)} orbits, {record['remaining_orbits']} survive" if args.orbits else "")
              + ("; independent replay agrees" if args.independent else ""),
              flush=True)
    print("every core: 8 exterior vertices of type 2+2, 64 of type 1+1, 11 of type 0+0", flush=True)
    if args.orbits:
        args.orbits.write_text(json.dumps(orbit_data, indent=2) + "\n")
    if args.output:
        args.output.write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main()
