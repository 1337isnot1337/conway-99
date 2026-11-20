"""Exact necessary residual-incidence tests for a fully specified exterior graph.

No solver is imported. A pass does not construct the second incidence.
The three central triangle vertices have zero incidence to the sixty exterior
vertices; exactly eighteen unmodelled incidence rows remain.
"""
import argparse
from fractions import Fraction
import gzip
import hashlib
from itertools import combinations
import json
from math import gcd, lcm
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[2]
BASELINE = "experiments/logs/root-prism-free/f0-boolean-fractional-model.json.gz"
BASELINE_SHA = "703206929c9c85a40ac4ddcbfb1708c716c288482cf50c77a32249404e35b782"
MODEL_SOURCE_SHA = "2c8a0f7f2bc2a219c994f42618585879e16a6d3a5809627b9aea25be40798160"
RANK_CAP = 18


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(canonical(value) + b"\n")


def symmetric(matrix):
    n = len(matrix)
    assert 0 <= n <= 60 and all(len(row) == n for row in matrix)
    assert all(type(x) is int for row in matrix for x in row)
    assert all(matrix[i][j] == matrix[j][i] for i in range(n) for j in range(n))
    return n


def determinant(matrix):
    """Independent integer Bareiss determinant, with row pivoting."""
    n = len(matrix)
    if n == 0:
        return 1
    a, previous, sign = [list(row) for row in matrix], 1, 1
    for k in range(n - 1):
        pivot_row = next((i for i in range(k, n) if a[i][k]), None)
        if pivot_row is None:
            return 0
        if pivot_row != k:
            a[k], a[pivot_row] = a[pivot_row], a[k]
            sign = -sign
        pivot = a[k][k]
        for i in range(k + 1, n):
            for j in range(k + 1, n):
                numerator = pivot * a[i][j] - a[i][k] * a[k][j]
                assert numerator % previous == 0
                a[i][j] = numerator // previous
            a[i][k] = 0
        previous = pivot
    return sign * a[-1][-1]


def integer_vector(vector, primitive=False):
    scale = lcm(*(x.denominator for x in vector)) if vector else 1
    values = [int(x * scale) for x in vector]
    if primitive:
        divisor = gcd(*(abs(x) for x in values))
        assert divisor > 0
        values = [x // divisor for x in values]
    return values, scale


def negative_certificate(matrix, vector):
    values, _ = integer_vector(vector, primitive=True)
    value = sum(values[i] * matrix[i][j] * values[j]
                for i in range(len(values)) for j in range(len(values)))
    assert value < 0
    return {"kind": "negative_quadratic", "vector": [str(x) for x in values],
            "value": str(value)}


def linear_certificate(matrix, rank_cap=RANK_CAP):
    """At most rank_cap+1 positive pivots; exact rational Schur arithmetic."""
    n = symmetric(matrix)
    assert type(rank_cap) is int and 0 <= rank_cap <= 60
    schur = [[Fraction(x) for x in row] for row in matrix]
    basis = [[Fraction(i == j) for i in range(n)] for j in range(n)]
    active, pivots, factors, principal_det = list(range(n)), [], [], Fraction(1)
    while active:
        negative = next((i for i in active if schur[i][i] < 0), None)
        if negative is not None:
            return negative_certificate(matrix, basis[negative])
        pivot = next((i for i in active if schur[i][i] > 0), None)
        if pivot is None:
            pair = next(((i, j) for i, j in combinations(active, 2) if schur[i][j]), None)
            if pair is not None:
                i, j = pair
                sign = 1 if schur[i][j] > 0 else -1
                return negative_certificate(matrix, [a - sign * b for a, b in zip(basis[i], basis[j])])
            break
        d = schur[pivot][pivot]
        u = [schur[i][pivot] for i in range(n)]
        values, scale = integer_vector(u)
        weight = Fraction(1, 1) / (d * scale * scale)
        factors.append({"vector": [str(x) for x in values],
                        "weight": [str(weight.numerator), str(weight.denominator)]})
        pivots.append(pivot)
        principal_det *= d
        assert principal_det.denominator == 1
        if len(pivots) > rank_cap:
            return {"kind": "rank_minor", "indices": pivots,
                    "determinant": str(principal_det.numerator)}
        remaining = [i for i in active if i != pivot]
        for j in remaining:
            coefficient = schur[pivot][j] / d
            basis[j] = [x - coefficient * y for x, y in zip(basis[j], basis[pivot])]
        for i in remaining:
            for j in remaining:
                schur[i][j] -= u[i] * u[j] / d
        for i in range(n):
            schur[i][pivot] = schur[pivot][i] = Fraction(0)
        active = remaining
    return {"kind": "positive_factorization", "rank": len(pivots), "indices": pivots,
            "principal_determinant": str(principal_det.numerator), "factors": factors}


def verify_linear(matrix, certificate, rank_cap=RANK_CAP):
    n = symmetric(matrix)
    kind = certificate["kind"]
    if kind == "negative_quadratic":
        vector = list(map(int, certificate["vector"]))
        assert len(vector) == n and any(vector)
        value = sum(vector[i] * matrix[i][j] * vector[j] for i in range(n) for j in range(n))
        assert value == int(certificate["value"]) < 0
        return False
    indices = certificate["indices"]
    assert all(type(i) is int and 0 <= i < n for i in indices)
    assert len(indices) == len(set(indices))
    minor = [[matrix[i][j] for j in indices] for i in indices]
    det = determinant(minor)
    if kind == "rank_minor":
        assert len(indices) == rank_cap + 1 and det == int(certificate["determinant"]) != 0
        return False
    assert kind == "positive_factorization"
    rank = certificate["rank"]
    assert type(rank) is int and rank == len(indices) <= rank_cap
    assert det == int(certificate["principal_determinant"]) > 0
    assert len(certificate["factors"]) == rank
    restored = [[Fraction(0) for _ in range(n)] for _ in range(n)]
    for factor in certificate["factors"]:
        vector = list(map(int, factor["vector"]))
        numerator, denominator = map(int, factor["weight"])
        assert len(vector) == n and denominator > 0
        weight = Fraction(numerator, denominator)
        assert weight > 0
        for i in range(n):
            for j in range(n):
                restored[i][j] += weight * vector[i] * vector[j]
    assert restored == matrix
    return True


def certify_residual(matrix):
    n = symmetric(matrix)
    entries = 0
    for i in range(n):
        for j in range(i, n):
            entries += 1
            value = matrix[i][j]
            if (i == j and value != 3) or (i != j and not 0 <= value <= 2):
                return {"kind": "intersection_entry", "indices": [i, j], "value": value,
                        "entries_checked": entries, "matrix_sha256": sha(canonical(matrix))}
    triples = 0
    for u in range(n):
        for v, w in combinations([i for i in range(n) if i != u], 2):
            triples += 1
            gap = matrix[u][v] + matrix[u][w] - matrix[v][w] - 3
            if gap > 0:
                return {"kind": "triple_metric", "indices": [u, v, w], "gap": gap,
                        "entries_checked": entries, "triples_checked": triples,
                        "matrix_sha256": sha(canonical(matrix))}
    result = linear_certificate(matrix)
    result.update(entries_checked=entries, triples_checked=triples,
                  matrix_sha256=sha(canonical(matrix)))
    return result


def verify_residual(matrix, certificate):
    n = symmetric(matrix)
    assert certificate["matrix_sha256"] == sha(canonical(matrix))
    if certificate["kind"] == "intersection_entry":
        i, j = certificate["indices"]
        assert 0 <= i <= j < n and matrix[i][j] == certificate["value"]
        assert (i == j and matrix[i][j] != 3) or (i != j and not 0 <= matrix[i][j] <= 2)
        return False
    if certificate["kind"] == "triple_metric":
        u, v, w = certificate["indices"]
        assert len({u, v, w}) == 3 and all(0 <= i < n for i in (u, v, w))
        assert matrix[u][u] == 3
        assert matrix[u][v] + matrix[u][w] - matrix[v][w] - 3 == certificate["gap"] > 0
        return False
    valid = verify_linear(matrix, certificate)
    if valid:
        assert certificate["entries_checked"] == n * (n + 1) // 2
        assert certificate["triples_checked"] == n * (n - 1) * (n - 2) // 2
        assert all(matrix[i][i] == 3 for i in range(n))
        assert all(0 <= matrix[i][j] <= 2 for i, j in combinations(range(n), 2))
        assert all(matrix[u][v] + matrix[u][w] - matrix[v][w] <= 3
                   for u in range(n) for v, w in combinations([i for i in range(n) if i != u], 2))
    return valid


def residual_matrix(first_masks, adjacency, alpha=12, beta=2):
    n = len(first_masks)
    assert len(adjacency) == n
    assert all(type(x) is int and x >= 0 for x in first_masks)
    assert all(type(row) is int and 0 <= row < 1 << n for row in adjacency)
    assert all(not (adjacency[i] >> i & 1) for i in range(n))
    assert all((adjacency[i] >> j & 1) == (adjacency[j] >> i & 1)
               for i in range(n) for j in range(n))
    return [[alpha * (i == j) + beta - (first_masks[i] & first_masks[j]).bit_count()
             - (adjacency[i] & adjacency[j]).bit_count() - (adjacency[i] >> j & 1)
             for j in range(n)] for i in range(n)]


def fixed_input(model_path, adjacency_path):
    baseline_raw = (ROOT / BASELINE).read_bytes()
    assert sha(baseline_raw) == BASELINE_SHA
    baseline = json.loads(gzip.decompress(baseline_raw))["validation"]
    model_raw, adjacency_raw = model_path.read_bytes(), adjacency_path.read_bytes()
    model, adjacency = json.loads(model_raw), json.loads(adjacency_raw)
    assert model["definition"]["source_sha256"] == MODEL_SOURCE_SHA and model["CNF_built"]
    assert model["definition"]["inputs"]["baseline"]["sha256"] == BASELINE_SHA
    data, core, universe = model["data"], baseline["core"], baseline["triples"]
    ids = data["design_source_indices"]
    assert len(ids) == 60 and all(type(a) is int and 0 <= a < 480 for a in ids)
    assert ids == sorted(set(ids))
    design = [universe[a] for a in ids]
    assert design == data["design"]
    masks = [sum(1 << i for i in h) for h in design]
    assert len(set(masks)) == 60 and all(m.bit_count() == 3 for m in masks)
    assert masks == data["masks"]
    component = [(row >> 3) & ((1 << 18) - 1) for row in core[3:21]]
    assert component == data["component_adjacency_rows"]
    for i in range(18):
        for j in range(i, 18):
            expected = 12 * (i == j) + 2 - (core[i + 3] & core[j + 3]).bit_count() - (core[i + 3] >> (j + 3) & 1)
            assert sum((m >> i & 1) * (m >> j & 1) for m in masks) == expected
    matrix = residual_matrix(masks, adjacency)
    assert len(adjacency) == 60 and all(row.bit_count() == 8 for row in adjacency)
    for v in range(60):
        for i in range(18):
            supplied = sum((adjacency[v] >> w & 1) * (masks[w] >> i & 1) for w in range(60))
            target = 2 - (masks[v] >> i & 1) - (component[i] & masks[v]).bit_count()
            assert target == data["targets"][v][i] == supplied
    for u, v in combinations(range(60), 2):
        assert (adjacency[u] & adjacency[v]).bit_count() + (masks[u] & masks[v]).bit_count() + (adjacency[u] >> v & 1) <= 2
    binding = {"model_sha256": sha(model_raw), "adjacency_file_sha256": sha(adjacency_raw),
               "baseline_sha256": BASELINE_SHA, "model_producer_sha256": MODEL_SOURCE_SHA,
               "selection_sha256": model["selection_sha256"], "original_selector_equations": 172,
               "degree_rows": 60, "mixed_rows": 1080, "pair_caps": 1770,
               "central_triangle_to_exterior_is_zero": True, "unmodelled_incidence_rows": 18}
    return matrix, binding


def controls():
    cases = [[], [[0, 0], [0, 0]], [[3, 2], [2, 3]], [[-1]], [[0, 2], [2, 3]],
             [[0, 2], [2, 0]], [[(3 if i == j else 0) for j in range(19)] for i in range(19)]]
    cases += [[[3 * (2 ** 100 + 7), 2 ** 100 + 7], [2 ** 100 + 7, 3 * (2 ** 100 + 7)]]]
    results = []
    for matrix in cases:
        certificate = linear_certificate(matrix)
        results.append({"dimension": len(matrix), "kind": certificate["kind"],
                        "passes": verify_linear(matrix, certificate)})
    bad_metric = [[3, 2, 2], [2, 3, 0], [2, 0, 3]]
    positive = linear_certificate(bad_metric)
    assert verify_linear(bad_metric, positive) and determinant(bad_metric) == 3
    bad = certify_residual(bad_metric)
    assert bad["kind"] == "triple_metric" and not verify_residual(bad_metric, bad)
    for matrix in [[[2]], [[3, -1], [-1, 3]]]:
        assert verify_linear(matrix, linear_certificate(matrix))
        entry = certify_residual(matrix)
        assert entry["kind"] == "intersection_entry" and not verify_residual(matrix, entry)
    metric_but_indefinite = [[3 if i == j else (2 if (i < 3) != (j < 3) else 1)
                             for j in range(6)] for i in range(6)]
    negative = certify_residual(metric_but_indefinite)
    assert negative["kind"] == "negative_quadratic" and negative["triples_checked"] == 60
    assert not verify_residual(metric_but_indefinite, negative)
    high_rank = certify_residual(cases[6])
    assert high_rank["kind"] == "rank_minor" and not verify_residual(cases[6], high_rank)
    triples = [tuple(sorted((i, (i + 1) % 18, (i + 3) % 18))) for i in range(18)]
    for h in combinations(range(18), 3):
        if h not in triples:
            triples.append(h)
        if len(triples) == 60:
            break
    masks = [sum(1 << i for i in h) for h in triples]
    gram = [[(a & b).bit_count() for b in masks] for a in masks]
    certificate = certify_residual(gram)
    assert verify_residual(gram, certificate) and certificate["rank"] == 18
    assert certificate["triples_checked"] == 102660
    rook = [sum(1 << j for j in range(9) if i != j and (i // 3 == j // 3 or i % 3 == j % 3)) for i in range(9)]
    for start in range(9):
        outside = [(start + i) % 9 for i in range(4)]
        known = [(start + i) % 9 for i in (4, 5)]
        hidden = [i for i in range(9) if i not in outside + known]
        first = [sum(1 << i for i, v in enumerate(known) if rook[u] >> v & 1) for u in outside]
        adjacency = [sum(1 << j for j, v in enumerate(outside) if rook[u] >> v & 1) for u in outside]
        residual = residual_matrix(first, adjacency, alpha=2)
        direct = [[sum((rook[u] >> v & 1) * (rook[w] >> v & 1) for v in hidden)
                   for w in outside] for u in outside]
        assert residual == direct
        assert verify_linear(residual, linear_certificate(residual, rank_cap=len(hidden)), rank_cap=len(hidden))
    mutations = 0
    for matrix, original, kind in [
        ([[-1]], linear_certificate([[-1]]), "negative"),
        (cases[6], linear_certificate(cases[6]), "rank"),
        ([[3, 2], [2, 3]], linear_certificate([[3, 2], [2, 3]]), "factor")]:
        changed = json.loads(canonical(original))
        if kind == "negative":
            changed["vector"] = ["0"]
        elif kind == "rank":
            changed["determinant"] = str(int(changed["determinant"]) + 1)
        else:
            changed["factors"][0]["weight"][0] = "-" + changed["factors"][0]["weight"][0]
        try:
            verify_linear(matrix, changed)
        except AssertionError:
            mutations += 1
        else:
            raise AssertionError("mutated certificate accepted")
    return {"status": "PASS: synthetic exact residual controls", "linear_cases": results,
            "PSD_metric_counterexample": {"matrix": bad_metric, "determinant": 3, "metric_gap": bad["gap"]},
            "PSD_entry_bound_counterexamples": 2,
            "metric_passing_indefinite_control": {"matrix": metric_but_indefinite, "certificate": negative},
            "entry_metric_passing_rank19_control": high_rank,
            "binary_18_by60_control": {"columns": 60, "rank": 18, "entry_checks": 1830, "triple_checks": 102660},
            "literal_rook_block_controls": 9, "certificate_mutations_rejected": mutations,
            "arithmetic": "Python integers and exact Fraction only",
            "production_candidates_checked": 0, "optimizer_calls": 0}


def main():
    if not __debug__:
        raise RuntimeError("assertions are required")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "inspect", "replay"))
    parser.add_argument("--model", type=Path)
    parser.add_argument("--adjacency", type=Path)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    started = time.monotonic()
    if args.mode == "prepare":
        report = controls()
        report.update(source_sha256=sha(Path(__file__).read_bytes()), baseline_sha256=BASELINE_SHA,
                      required_model_producer_sha256=MODEL_SOURCE_SHA)
    else:
        assert args.model is not None and args.adjacency is not None
        matrix, binding = fixed_input(args.model, args.adjacency)
        if args.mode == "inspect":
            certificate = certify_residual(matrix)
            passed = verify_residual(matrix, certificate)
            report = {"status": "PASS_NECESSARY_RESIDUAL_TESTS_ONLY" if passed else "EXACT_FIXED_EXTERIOR_RESIDUAL_OBSTRUCTION",
                      "source_sha256": sha(Path(__file__).read_bytes()), "binding": binding,
                      "residual_matrix": matrix, "certificate": certificate,
                      "second_incidence_constructed": False, "full_graph_constructed": False,
                      "whole_F0_excluded": False, "optimizer_calls": 0}
        else:
            assert args.report is not None
            raw = args.report.read_bytes()
            old = json.loads(raw)
            assert old["source_sha256"] == sha(Path(__file__).read_bytes())
            assert old["binding"] == binding and old["residual_matrix"] == matrix
            passed = verify_residual(matrix, old["certificate"])
            assert old["status"] == ("PASS_NECESSARY_RESIDUAL_TESTS_ONLY" if passed else "EXACT_FIXED_EXTERIOR_RESIDUAL_OBSTRUCTION")
            assert not old["second_incidence_constructed"] and not old["full_graph_constructed"] and not old["whole_F0_excluded"]
            report = {"status": "PASS: independent residual/certificate replay",
                      "report_sha256": sha(raw), "binding": binding, "optimizer_calls": 0}
    report["seconds"] = time.monotonic() - started
    save(args.output, report)
    print(json.dumps({"status": report["status"], "sha256": sha(args.output.read_bytes()),
                      "seconds": report["seconds"]}))


if __name__ == "__main__":
    main()
