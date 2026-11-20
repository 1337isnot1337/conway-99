"""Independent arithmetic and finite controls for the triangle-replacement bound.

No subject source is imported, and no optimizer is called.  The source review
and general counting proof are recorded in the accompanying research note.
"""
import argparse
from collections import Counter, deque
from fractions import Fraction
import hashlib
from itertools import combinations
import json
from math import comb
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SUBJECT = "experiments/workspace/triangle_incidence_binary_integer_enumerator.py"
SUBJECT_SHA = "fedcc51699ebfde75ef279123730ba7354a2018bccc4fbef9eb3566cd7061378"
BOUND_SOURCE = "experiments/workspace/triangle_incidence_binary_replacement_code.py"
BOUND_SOURCE_SHA = "5badcf9c720073f7ea4bd38ec30763c948848e9f64beaa2f851b3714661ceaf3"
BOUND_PREPARATION = "experiments/logs/grids-and-triangles/triangle-incidence-binary-replacement-code-preparation.json"
BOUND_PREPARATION_SHA = "051c9f2f343088015e3f1f48aca64320f47b9088c3b9eed2512a7ea38de9f7df"
BOUND_RESULT = "experiments/logs/grids-and-triangles/triangle-incidence-binary-replacement-code-query01.json"
BOUND_RESULT_SHA = "ac9a7b4647cd1b216612ca63e7f83ccbcdb6c0b3a1ae697f8968dda21d9f1c0d"
POINTS = [
    ("experiments/logs/grids-and-triangles/triangle-incidence-binary-integer-enumerator-query01.json",
     "21097ac59a4dba22c6a6877a5ed896a05fb86aef4706792fb11015d9eda00b4c",
     [627, 1330, 1, 21, 1, 0, 67]),
    ("experiments/logs/grids-and-triangles/triangle-incidence-binary-full-support-enumerator-query01.json",
     "2b152a24ffd3defb86b79aff59bf4a3c8da5594ad3d0fb18a2d6853f04144fe2",
     [475, 0, 597, 1, 1, 118, 855]),
]


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def krawtchouk(n, j, w):
    return sum((-1)**s * comb(w, s) * comb(n-w, j-s)
               for s in range(max(0, j-(n-w)), min(j, w)+1))


def point_checks(root):
    reports = []
    for path, digest, nonzero in POINTS:
        raw = (root/path).read_bytes()
        assert sha(raw) == digest
        record = json.loads(raw)
        assert record["rounded_nonzero_counts"] == nonzero
        primal = [0]*100
        primal[0] = 1
        for w, a in zip([36, 40, 44, 48, 52, 56, 60], nonzero):
            primal[w] = a
        assert sum(primal) == 2048
        numerators = [sum(a*krawtchouk(99, j, w) for w, a in enumerate(primal) if a)
                      for j in range(100)]
        assert all(v % 2048 == 0 for v in numerators)
        dual = [v//2048 for v in numerators]
        assert dual == record["certificate"]["dual_weight_counts"]
        assert primal == record["certificate"]["primal_weight_counts"]
        assert all(v >= 0 for v in dual) and sum(dual) == 2**88
        required = 231 + 7*(dual[2]-dual[1])
        reports.append({"path": path, "sha256": digest,
                        "nonzero_counts": nonzero, "all100_dual_counts_checked": True,
                        "B1": dual[1], "B2": dual[2], "B3": dual[3],
                        "zero_coordinate_closure_gap_B2_minus_binomial_B1_2": dual[2]-comb(dual[1], 2),
                        "triangle_replacement_required_B3": required,
                        "triangle_replacement_gap_B3_minus_required": dual[3]-required,
                        "actual_code_constructed": False})
    assert reports[0]["zero_coordinate_closure_gap_B2_minus_binomial_B1_2"] == -1
    assert (reports[1]["B1"], reports[1]["B2"], reports[1]["B3"]) == (0, 152, 239)
    assert reports[1]["triangle_replacement_gap_B3_minus_required"] == -1056
    return reports


def bound_checks(root):
    assert sha((root/BOUND_SOURCE).read_bytes()) == BOUND_SOURCE_SHA
    prep_raw = (root/BOUND_PREPARATION).read_bytes()
    result_raw = (root/BOUND_RESULT).read_bytes()
    assert sha(prep_raw) == BOUND_PREPARATION_SHA
    assert sha(result_raw) == BOUND_RESULT_SHA
    prep, result = json.loads(prep_raw), json.loads(result_raw)
    m = prep["model"]
    assert prep["bindings"]["source_sha256"] == BOUND_SOURCE_SHA
    assert result["bindings"] == prep["bindings"]
    assert result["preparation_sha256"] == BOUND_PREPARATION_SHA
    canonical = (json.dumps(m, sort_keys=True, separators=(",", ":"))+"\n").encode()
    assert sha(canonical) == prep["model_sha256"] == result["model_sha256"]
    weights = [36, 40, 44, 48, 52, 56, 60]
    lower = {3: 231, 4: 2079, 5: 23868, 6: 24486, 7: 3465,
             8: 3465, 11: 2079, 12: 693, 15: 99}
    A = [[lower.get(j, 0)-krawtchouk(99, j, w) for w in weights]
         for j in range(1, 100)]
    b = [comb(99, j)-lower.get(j, 0) for j in range(1, 100)]
    labels = ["dual_weight_"+str(j) for j in range(1, 100)]
    additions = [("equal_column_edges", {2: 1, 1: -7}, 0),
                 ("triangle_replacements", {3: 1, 2: -7, 1: 7}, 231)]
    pullbacks = []
    for label, coefficients, demand in additions:
        row = [demand-sum(c*krawtchouk(99, j, w) for j, c in coefficients.items())
               for w in weights]
        upper = sum(c*comb(99, j) for j, c in coefficients.items())-demand
        A.append(row); b.append(upper); labels.append(label)
        pullbacks.append({"label": label, "dual_coefficients": [[j, c] for j, c in sorted(coefficients.items())],
                          "dual_lower_bound": demand, "primal_coefficients": row,
                          "primal_upper_bound": upper})
    assert A == m["coefficients"] and b == m["upper_bounds"] and labels == m["row_labels"]
    assert m["forced_dual_weight_lower_bounds"] == [[j, lower[j]] for j in sorted(lower)]
    assert m["allowed_nonzero_weights"] == weights and m["variable_lower_bounds"] == [0]*7
    primal = list(map(Fraction, result["exact_primal"]))
    dual = list(map(Fraction, result["exact_dual"]))
    assert len(primal) == 7 and len(dual) == 101
    assert all(v >= 0 for v in primal+dual)
    slacks = [Fraction(rhs)-sum(a*x for a, x in zip(row, primal)) for row, rhs in zip(A, b)]
    assert all(s >= 0 for s in slacks)
    dual_slacks = [sum(dual[i]*A[i][j] for i in range(101))-1 for j in range(7)]
    assert all(s >= 0 for s in dual_slacks)
    primal_value = 1+sum(primal)
    dual_value = 1+sum(y*rhs for y, rhs in zip(dual, b))
    assert primal_value == dual_value == Fraction(560594944, 189229)
    assert 2**11 <= dual_value < 2**12
    assert list(map(str, dual_slacks)) == result["certificate"]["dual_column_slacks"]
    assert str(dual_value) == result["certificate"]["exact_code_size_upper_bound"]
    active_dual = [[labels[i], str(y)] for i, y in enumerate(dual) if y]
    assert active_dual == [["dual_weight_4", "61/1703061"],
                           ["dual_weight_5", "65/1703061"],
                           ["equal_column_edges", "3868/1703061"],
                           ["triangle_replacements", "407/567687"]]
    # The two new rows must pull back to M times their literal dual-count gap.
    point_pullbacks = []
    for path, digest, nonzero in POINTS:
        record = json.loads((root/path).read_bytes())
        counts = record["certificate"]["dual_weight_counts"]
        gaps = []
        for offset, (_, coefficients, demand) in enumerate(additions, start=99):
            gap = sum(c*counts[j] for j, c in coefficients.items())-demand
            assert b[offset]-sum(a*x for a, x in zip(A[offset], nonzero)) == 2048*gap
            gaps.append(gap)
        point_pullbacks.append({"point_sha256": digest, "literal_dual_row_gaps": gaps})
    return {"source_sha256": BOUND_SOURCE_SHA, "preparation_sha256": BOUND_PREPARATION_SHA,
            "result_sha256": BOUND_RESULT_SHA, "model_sha256": prep["model_sha256"],
            "both_added_rows_independently_pulled_back": pullbacks,
            "all101_original_primal_slacks": list(map(str, slacks)),
            "all_seven_dual_column_slacks": list(map(str, dual_slacks)),
            "nonzero_dual_rows": active_dual, "point_pullback_checks": point_pullbacks,
            "exact_primal_and_dual_objective": str(dual_value),
            "dimension_bound": 11, "incidence_rank_bound": 88,
            "parent_forced_word_bounds_preserved_not_reproved_here": True,
            "numerical_LP_called": False}


def subspaces(words):
    words = sorted(words)
    seen = {frozenset([0])}
    queue = deque(seen)
    while queue:
        space = queue.popleft()
        for word in words:
            if word in space:
                continue
            larger = space | frozenset(word ^ old for old in space)
            if larger not in seen:
                seen.add(larger)
                queue.append(larger)
    return sorted(seen, key=lambda s: (len(s), tuple(sorted(s))))


def literal_controls():
    graphs = [
        ("rook9", 9, {(u, v) for u in range(9) for v in range(u+1, 9)
                      if u//3 == v//3 or u % 3 == v % 3}, 67),
        ("two_disjoint_triangles", 6, {(u, v) for u in range(6) for v in range(u+1, 6)
                                      if u//3 == v//3}, 67),
        ("triangle", 3, set(combinations(range(3), 2)), 5),
    ]
    reports = []
    for name, n, edges, expected_count in graphs:
        triangles = {tuple(t) for t in combinations(range(n), 3)
                     if all(tuple(e) in edges for e in combinations(t, 2))}
        triangle_masks = [sum(1 << u for u in t) for t in triangles]
        degree = [sum(u in edge for edge in edges) for u in range(n)]
        assert len(set(degree)) == 1 and degree[0] % 2 == 0
        r = degree[0]//2
        assert all(sum(set(edge) <= set(t) for t in triangles) == 1 for edge in edges)
        assert all(sum(u in t for t in triangles) == r for u in range(n))
        kernel = [w for w in range(1 << n)
                  if all((w & t).bit_count() % 2 == 0 for t in triangle_masks)]
        spaces = subspaces(kernel)
        assert len(spaces) == expected_count
        signatures = Counter()
        for space in spaces:
            words = sorted(space)
            labels = [sum(((word >> v) & 1) << k for k, word in enumerate(words))
                      for v in range(n)]
            b1 = labels.count(0)
            equal_pairs = [edge for edge in combinations(range(n), 2)
                           if labels[edge[0]] == labels[edge[1]]]
            b2 = len(equal_pairs)
            equal_edges = set(equal_pairs) & edges
            assert len(equal_edges) == r*b1
            assert b2 >= r*b1
            dual_triples = {t for t in combinations(range(n), 3)
                            if labels[t[0]] ^ labels[t[1]] ^ labels[t[2]] == 0}
            assert triangles <= dual_triples
            replacements = Counter()
            for t in triangles:
                for old in t:
                    for new in range(n):
                        if new not in t and labels[old] == labels[new]:
                            replacements[tuple(sorted((set(t)-{old}) | {new}))] += 1
            assert not (set(replacements) & triangles)
            histogram = Counter()
            for t in dual_triples-triangles:
                edge_count = sum(tuple(e) in edges for e in combinations(t, 2))
                assert 0 <= edge_count <= 2
                assert replacements[t] == edge_count
                histogram[edge_count] += 1
            assert sum(replacements.values()) == 2*r*(b2-b1)
            assert histogram[1]+2*histogram[2] == 2*r*(b2-b1)
            assert len(dual_triples) >= len(triangles)+r*(b2-b1)
            signatures[(b1, b2, len(dual_triples), histogram[0], histogram[1], histogram[2])] += 1
        reports.append({"graph": name, "vertices": n, "triangles": len(triangles),
                        "triangles_per_vertex": r, "all_subspaces_checked": len(spaces),
                        "literal_replacement_multiplicity_and_identity": True,
                        "count_profiles": [{"B1_B2_B3_n0_n1_n2": list(k), "subspaces": v}
                                           for k, v in sorted(signatures.items())]})
    return reports


def calculate(root):
    assert sha((root/SUBJECT).read_bytes()) == SUBJECT_SHA
    return {"status": "PASS: replacement proof,139 literal code controls, formal-point rejection and exact101-row LP certificate",
            "source_sha256": sha(Path(__file__).read_bytes()),
            "reviewed_enumerator_source_sha256": SUBJECT_SHA,
            "formal_point_checks": point_checks(root), "literal_controls": literal_controls(),
            "replacement_LP_certificate_checks": bound_checks(root),
            "general_identity": "14(B2-B1)=n1+2*n2",
            "necessary_graph_code_inequality": "B3>=231+7(B2-B1)",
            "equal_column_edge_inequality": "B2>=7B1",
            "source_review": {
                "full_original_enumerator_source_read": True,
                "all99_congruences_retained_by_exact_deduplication": True,
                "quotient_bounds_0_to_2047_are_valid": True,
                "numerical_rows_only_propose_values": True,
                "all100_exact_transform_checks_are_acceptance_gate": True,
                "formal_enumerator_does_not_establish_code_existence": True},
            "optimizer_calls": 0, "subject_source_imported": False,
            "all_codes_or_graphs_excluded": False}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=("write", "replay"))
    p.add_argument("--root", type=Path, default=ROOT)
    p.add_argument("--certificate", type=Path, required=True)
    p.add_argument("--output", type=Path)
    args = p.parse_args()
    report = calculate(args.root)
    if args.mode == "write":
        assert not args.certificate.exists()
        args.certificate.write_text(json.dumps(report, indent=2)+"\n")
    else:
        assert report == json.loads(args.certificate.read_bytes())
        assert args.output is not None and not args.output.exists()
        args.output.write_text(json.dumps({"status": "PASS: independent replacement audit replay",
                                          "source_sha256": report["source_sha256"],
                                          "certificate_sha256": sha(args.certificate.read_bytes()),
                                          "optimizer_calls": 0}, indent=2)+"\n")
    print(json.dumps({"status": report["status"],
                      "certificate_sha256": sha(args.certificate.read_bytes()),
                      "point_low_counts": [{k: q[k] for k in ("B1", "B2", "B3", "triangle_replacement_gap_B3_minus_required")}
                                           for q in report["formal_point_checks"]]}, indent=2))


if __name__ == "__main__":
    main()
