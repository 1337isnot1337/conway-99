"""Exact triangle-replacement identities for binary incidence dual words.

Every edge must belong to one triangle and every point to r triangles.
For any binary code orthogonal to those triangles, its dual counts satisfy
B2 >= r*B1 and B3 >= number_of_triangles + r*(B2-B1).
"""
import argparse
from collections import Counter
import hashlib
from itertools import combinations
import json
from pathlib import Path


def graph(n, edges):
    rows = [0]*n
    for a, b in edges:
        rows[a] |= 1 << b
        rows[b] |= 1 << a
    return rows


def hosts():
    rook = graph(9, [(a, b) for a, b in combinations(range(9), 2)
                     if a//3 == b//3 or a % 3 == b % 3])
    pairs = list(combinations(range(6), 2))
    doily = graph(15, [(a, b) for a, b in combinations(range(15), 2)
                       if set(pairs[a]).isdisjoint(pairs[b])])
    two_triangles = graph(6, [(a, b) for a, b in combinations(range(6), 2) if a//3 == b//3])
    return [("two_disjoint_triangles", two_triangles), ("rook_3_by_3", rook),
            ("doily_Kneser_6_2", doily)]


def all_subspaces(words):
    zero = frozenset([0]); seen = {zero}; queue = [zero]
    for space in queue:
        for w in words:
            if w in space:
                continue
            enlarged = space | frozenset(v ^ w for v in space)
            if enlarged not in seen:
                seen.add(enlarged); queue.append(enlarged)
    return sorted(seen, key=lambda x: (len(x), sorted(x)))


def controls():
    records = []
    totals = Counter()
    for name, rows in hosts():
        n = len(rows)
        edges = [(a, b) for a, b in combinations(range(n), 2) if (rows[a] >> b) & 1]
        assert all((rows[a] & rows[b]).bit_count() == 1 for a, b in edges)
        degree = rows[0].bit_count()
        assert degree % 2 == 0 and all(row.bit_count() == degree for row in rows)
        r = degree//2
        triangles = [T for T in combinations(range(n), 3)
                     if all((rows[a] >> b) & 1 for a, b in combinations(T, 2))]
        triangle_set = set(triangles)
        masks = [sum(1 << v for v in T) for T in triangles]
        assert all(sum(v in T for T in triangles) == r for v in range(n))
        words = [w for w in range(1 << n) if all((w & mask).bit_count() % 2 == 0 for mask in masks)]
        spaces = all_subspaces(words)
        cases = []
        for code in spaces:
            ordered = sorted(code)
            labels = [sum(((word >> v) & 1) << i for i, word in enumerate(ordered)) for v in range(n)]
            populations = Counter(labels)
            B1 = populations[0]
            B2 = sum(m*(m-1)//2 for m in populations.values())
            equal_edges = sum(labels[a] == labels[b] for a, b in edges)
            assert equal_edges == r*B1
            dual_triples = [T for T in combinations(range(n), 3)
                            if labels[T[0]] ^ labels[T[1]] ^ labels[T[2]] == 0]
            B3 = len(dual_triples)
            by_edges = Counter(sum((rows[a] >> b) & 1 for a, b in combinations(T, 2))
                               for T in dual_triples if T not in triangle_set)
            assert not by_edges[3]
            replacements = Counter()
            for T in triangles:
                for a in T:
                    for b in range(n):
                        if b not in T and labels[a] == labels[b]:
                            U = tuple(sorted((set(T)-{a}) | {b}))
                            assert U not in triangle_set and U in dual_triples
                            replacements[U] += 1
            for T in dual_triples:
                if T in triangle_set:
                    continue
                count = sum((rows[a] >> b) & 1 for a, b in combinations(T, 2))
                assert replacements[T] == count
            assert sum(replacements.values()) == 2*r*(B2-B1) == by_edges[1]+2*by_edges[2]
            assert B2 >= r*B1
            assert B3 >= len(triangles)+r*(B2-B1)
            assert 2*(B3-len(triangles)-r*(B2-B1)) == 2*by_edges[0]+by_edges[1]
            cases.append({"code_size": len(code), "B1": B1, "B2": B2, "B3": B3,
                          "nontriangle_word_edge_counts": [by_edges[i] for i in range(3)],
                          "replacements": sum(replacements.values())})
        totals["subcodes"] += len(spaces)
        totals["literal_replacements"] += sum(c["replacements"] for c in cases)
        totals["dual_weight_three_words"] += sum(c["B3"] for c in cases)
        records.append({"host": name, "vertices": n, "triangles": len(triangles),
                        "triangles_per_vertex": r, "full_binary_kernel_size": len(words),
                        "all_kernel_subcodes": len(spaces), "cases": cases})
    return {"status": "PASS_EXACT_REPLACEMENT_IDENTITIES_ON_ALL_CONTROL_SUBCODES",
            "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "identities": ["equal-column edges = r*B1",
                           "2*r*(B2-B1) = n1+2*n2",
                           "2*(B3-T-r*(B2-B1)) = 2*n0+n1"],
            "totals": dict(totals), "hosts": records, "optimizer_calls": 0,
            "hypothetical_graph_values": {"r": 7, "triangles": 231}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    result = controls()
    args.output.write_text(json.dumps(result, indent=2)+"\n")
    print(json.dumps({k: v for k, v in result.items() if k != "hosts"}, indent=2))


if __name__ == "__main__":
    main()
