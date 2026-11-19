"""Exact low-weight triangle-toggle controls for binary incidence codes.

All code subspaces on three regular lambda-one control graphs are checked.
Five-vertex edge bounds additionally require common-neighbor cap two.
"""
import argparse
from collections import Counter
import hashlib
from itertools import combinations
import json
from pathlib import Path

import triangle_incidence_binary_replacement_words as previous

PREVIOUS_SHA = "993fcdb85f2e4c50e5bb86a86d4a8a5a2ae75b3e0bac85453a25f6b4234e3c62"


def controls():
    assert hashlib.sha256(Path(previous.__file__).read_bytes()).hexdigest() == PREVIOUS_SHA
    reports = []
    totals = Counter()
    for name, rows in previous.hosts():
        n = len(rows); r = rows[0].bit_count()//2
        triangles = [T for T in combinations(range(n), 3)
                     if all((rows[a] >> b) & 1 for a, b in combinations(T, 2))]
        masks = [sum(1 << v for v in T) for T in triangles]
        number = len(triangles)
        pair_words = set()
        disjoint_pairs = 0
        cross_counts = Counter()
        for i, left in enumerate(triangles):
            for right in triangles[:i]:
                intersection = set(left) & set(right)
                assert len(intersection) in (0, 1)
                if intersection:
                    word = tuple(sorted(set(left) ^ set(right)))
                    assert len(word) == 4
                    assert sum((rows[a] >> b) & 1 for a, b in combinations(word, 2)) == 2
                    assert word not in pair_words
                    pair_words.add(word)
                else:
                    disjoint_pairs += 1
                    cross_counts[sum((rows[a] >> b) & 1 for a in left for b in right)] += 1
        assert len(pair_words) == n*r*(r-1)//2
        assert disjoint_pairs == number*(number-1)//2-len(pair_words)
        cap_two = all((rows[a] & rows[b]).bit_count() <= 2 for a, b in combinations(range(n), 2))
        profiles = {}
        for size in range(1, min(6, n)+1):
            records = []
            for subset in combinations(range(n), size):
                mask = sum(1 << v for v in subset)
                edges = sum((rows[a] >> b) & 1 for a, b in combinations(subset, 2))
                contained = sum(t & mask == t for t in masks)
                assert contained <= (2 if size >= 5 else 1 if size >= 3 else 0)
                if size == 5 and cap_two:
                    assert 0 <= edges-3*contained <= 5
                records.append((subset, edges, contained))
            profiles[size] = records
        if cap_two:
            c4 = sum(edges == 4 and not t for _, edges, t in profiles[4])
            assert cross_counts[2]+3*cross_counts[3] == 2*c4
        words = [w for w in range(1 << n) if all((w & t).bit_count() % 2 == 0 for t in masks)]
        codes = previous.all_subspaces(words)
        cases = []
        for code in codes:
            labels = [sum(((w >> v) & 1) << i for i, w in enumerate(sorted(code))) for v in range(n)]
            B, E, T = [1]+[0]*6, [0]*7, [0]*7
            triple_sets = {}
            for size, records in profiles.items():
                included = []
                for subset, edges, contained in records:
                    label = 0
                    for v in subset:
                        label ^= labels[v]
                    if not label:
                        B[size] += 1; E[size] += edges; T[size] += contained
                        included.append((subset, edges, contained))
                triple_sets[size] = included
            assert E[2] == r*B[1]
            assert T[3] == number
            assert E[3] == 3*number+2*r*(B[2]-B[1])
            assert T[4] == (number-r)*B[1]
            assert T[5] == (number-2*r)*B[2]+r*B[1]
            assert T[6] == (number-3*r)*B[3]+E[3]-number
            s4 = E[4]-3*T[4]
            assert s4 == 3*r*B[3]-4*r*B[2]+4*r*B[1]-3*number
            s5 = E[5]-3*T[5]
            assert s5 == 4*r*B[4]-6*r*B[3]+8*r*B[2]-(5*r+3*number)*B[1]+6*number
            triangle4 = Counter(edges-3*t for _, edges, t in triple_sets[4] if t)
            assert triangle4[1] == 2*r*(r-1)*B[1]
            assert triangle4[0] == (number-r-2*r*(r-1))*B[1]
            assert set(pair_words) <= {S for S, _, _ in triple_sets[4]}
            assert s4 <= 4*B[4]-2*len(pair_words)-(4*(number-r)-2*r*(r-1))*B[1]
            two_triangles5 = sum(t == 2 for _, _, t in triple_sets[5])
            assert two_triangles5 == r*(r-1)//2*B[1]
            triangle5 = sum(t > 0 for _, _, t in triple_sets[5])
            assert triangle5 == (number-2*r)*B[2]+(r-r*(r-1)//2)*B[1]
            two_triangles6 = sum(t == 2 for _, _, t in triple_sets[6])
            assert two_triangles6 == disjoint_pairs+r*(r-1)*(B[2]-2*B[1])
            triangle6 = sum(t > 0 for _, _, t in triple_sets[6])
            assert triangle6 == ((number-3*r)*B[3]+2*number-disjoint_pairs
                                 +r*(3-r)*B[2]+2*r*(r-2)*B[1])
            assert B[6] >= triangle6
            cases.append({"code_size": len(code), "B1_to_B6": B[1:],
                "weight4_e_minus_3t": s4, "weight5_e_minus_3t": s5,
                "triangle_containing_weight5": triangle5,
                "two_triangle_weight6": two_triangles6,
                "triangle_containing_weight6": triangle6})
        totals["all_subcodes"] += len(codes)
        totals["literal_dual_supports"] += sum(sum(c["B1_to_B6"]) for c in cases)
        reports.append({"host": name, "vertices": n, "r": r, "triangles": number,
                        "intersecting_triangle_pairs": len(pair_words),
                        "disjoint_triangle_pairs": disjoint_pairs,
                        "common_neighbor_cap_two": cap_two,
                        "all_kernel_subcodes": len(codes), "cases": cases})
    return {"status": "PASS_EXACT_TRIANGLE_TOGGLE_AND_CONTAINMENT_IDENTITIES",
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "previous_source_sha256": PREVIOUS_SHA, "totals": dict(totals), "hosts": reports,
        "target_formulas": {
            "S4": "21B3-28B2+28B1-693",
            "S5": "28B4-42B3+56B2-728B1+1386",
            "triangle_containing_dual_weight5": "217B2-14B1",
            "triangle_containing_dual_weight6": "210B3-28B2+70B1-24024"},
        "optimizer_calls": 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    report = controls()
    args.output.write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps({k: v for k, v in report.items() if k != "hosts"}, indent=2))


if __name__ == "__main__":
    main()
