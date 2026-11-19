"""Exact rational rank and complete left kernel of the shared mixed rows.

This uses the accepted modulo-three edge rank only as a rational lower
bound. It makes no conclusion about other primes, Smith torsion, edge
signs, capacity bounds, integrality or graph existence.
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[2]
INPUTS = {
    "domain": ("experiments/logs/root-prism-free/f0-exterior-row-domains02.json.gz", "665563b75fa6fc23caa9a002621cc4047809af28543b52b5c2a7ffa592d05dd4"),
    "mod3_independent": ("experiments/logs/root-prism-free/f0-shared-mod3-projection-independent01.json", "c9708a77fa7aa80e5fa31d4b9d4929766bf5656b7b7c901aa29a74c975035124"),
    "mod3_source": ("experiments/workspace/root_prism_free_f0_shared_prime_projection_independent.py", "8a02c4ffcf473df48bbd0f55001f5d8ccc4cda0ec9b9ded62e650708095f5696"),
    "mod3_original": ("experiments/logs/root-prism-free/f0-shared-mod3-projection01/report.json", "5f0ea9fa1e83856e24637eaa736625ccd0a38b56f70c7a3cce9403d255e96512"),
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def read(kind):
    name, expected = INPUTS[kind]
    raw = (ROOT / name).read_bytes()
    assert sha(raw) == expected
    return json.loads(gzip.decompress(raw) if name.endswith(".gz") else raw)


def run():
    started = time.monotonic()
    deadline = started + 60
    data, lower, original = read("domain"), read("mod3_independent"), read("mod3_original")
    assert sha((ROOT / INPUTS["mod3_source"][0]).read_bytes()) == INPUTS["mod3_source"][1]
    assert lower["status"] == "PASS_INDEPENDENT_COMPLETE_AUGMENTED_RANK_NO_NEW_SELECTOR_CONGRUENCES"
    assert lower["source_sha256"] == INPUTS["mod3_source"][1]
    assert lower["modulus"] == 3 and lower["edge_rank"] == original["edge_pivots_found"] == 7731
    assert lower["original_rows_processed"] == original["processed_rows"] == 9120
    assert lower["inputs"]["report"] == list(INPUTS["mod3_original"])
    assert lower["domain"] == list(INPUTS["domain"])
    core, triples = data["component_core_rows"], data["signature_domain"]
    assert len(core) == 21 and len(triples) == 480
    sets = [set(h) for h in triples]
    assert all(len(h) == 3 for h in sets)
    adjacency = [[core[i + 3] >> (j + 3) & 1 for j in range(18)] for i in range(18)]
    targets = [[2 - int(i in h) - sum(adjacency[i][j] for j in h) for i in range(18)] for h in triples]
    assert targets == data["row_targets"] and all(sum(q) == 24 for q in targets)
    neighbors = [[b for b in range(480) if a != b and len(sets[a] & sets[b]) <= 1
                  and all(targets[a][i] > 0 for i in triples[b])
                  and all(targets[b][i] > 0 for i in triples[a])] for a in range(480)]
    assert neighbors == data["possible_neighbor_signature_ids"]
    edges = [(a, b) for a in range(480) for b in neighbors[a] if a < b]
    assert len(edges) == 68394
    covered = [set().union(*(sets[b] for b in ns)) if ns else set() for ns in neighbors]
    empty = [18 * a + i for a in range(480) for i in range(18) if i not in covered[a]]
    assert len(empty) == 756
    assert all(targets[a][i] == 0 for a, i in (divmod(row, 18) for row in empty))
    nonempty = sorted(set(range(8640)) - set(empty))
    active_mask = sum(1 << r for r in nonempty)
    pairs = [(i, j) for i in range(18) for j in range(i, 18)]
    pair_id = {pair: n for n, pair in enumerate(pairs)}
    gram = []
    for i, j in pairs:
        quota = 12 * int(i == j) + 2 - (core[i + 3] & core[j + 3]).bit_count() - adjacency[i][j]
        gram.append({"site_pair": [i, j], "selector_support": [a for a, h in enumerate(sets) if i in h and j in h], "rhs": quota})
    gram.append({"site_pair": None, "selector_support": list(range(480)), "rhs": 60})
    kernels, projected_binary, basis, pivots = [], [], {}, []
    checked_edges = 0
    for i in range(18):
        for j in range(i + 1, 18):
            assert time.monotonic() < deadline
            coefficients = {}
            for a, h in enumerate(sets):
                if j in h:
                    coefficients[18 * a + i] = 1
                if i in h:
                    coefficients[18 * a + j] = -1
            # Directly contract the two possible site terms at both endpoints.
            for a, b in edges:
                weight = (coefficients.get(18 * a + i, 0) * int(i in sets[b])
                          + coefficients.get(18 * a + j, 0) * int(j in sets[b])
                          + coefficients.get(18 * b + i, 0) * int(i in sets[a])
                          + coefficients.get(18 * b + j, 0) * int(j in sets[a]))
                assert weight == 0
                checked_edges += 1
            rhs = [int(j in h) * targets[a][i] - int(i in h) * targets[a][j] for a, h in enumerate(sets)]
            g = {}

            def add_pair(a, b, c):
                index = pair_id[tuple(sorted((a, b)))]
                g[index] = g.get(index, 0) + c

            add_pair(j, j, 2)
            add_pair(i, i, -2)
            for k in range(18):
                if adjacency[i][k]:
                    add_pair(j, k, -1)
                if adjacency[j][k]:
                    add_pair(i, k, 1)
            combination = [[r, c] for r, c in sorted(g.items()) if c]
            from_gram = [0] * 480
            for r, c in combination:
                for a in gram[r]["selector_support"]:
                    from_gram[a] += c
            assert rhs == from_gram
            constant = sum(c * gram[r]["rhs"] for r, c in combination)
            assert constant == 0
            vector = sum(1 << r for r, c in coefficients.items() if c & 1) & active_mask
            projected_binary.append(vector)
            while vector:
                pivot = vector.bit_length() - 1
                if pivot not in basis:
                    basis[pivot] = vector
                    pivots.append(pivot)
                    break
                vector ^= basis[pivot]
            assert vector, "projected skew vectors need a different independence proof"
            kernels.append({"site_pair": [i, j], "mixed_row_terms": [[r, c] for r, c in sorted(coefficients.items())],
                            "selector_rhs_terms": [[a, c] for a, c in enumerate(rhs) if c],
                            "gram_combination": combination, "gram_constant": constant})
    assert len(kernels) == len(basis) == len(pivots) == 153
    # Retain a small nonsingular minor, independently eliminable by a checker.
    minor = [sum(((vector >> pivot) & 1) << k for k, pivot in enumerate(pivots)) for vector in projected_binary]
    minor_basis = {}
    for value in minor:
        while value:
            pivot = (value & -value).bit_length() - 1
            if pivot not in minor_basis:
                minor_basis[pivot] = value
                break
            value ^= minor_basis[pivot]
    assert len(minor_basis) == 153
    nullity = len(empty) + len(kernels)
    rank_upper = 8640 - nullity
    assert rank_upper == lower["edge_rank"] == 7731
    assert checked_edges == 153 * 68394
    assert time.monotonic() < deadline
    return {"status": "EXACT_RATIONAL_MIXED_RANK_AND_COMPLETE_KERNEL_CERTIFICATE",
            "source_sha256": sha(Path(__file__).read_bytes()), "inputs": INPUTS,
            "mixed_rows": 8640, "edge_columns": 68394, "empty_mixed_row_ids": empty,
            "all_empty_rows_have_zero_selector_rhs": True, "original_gram_rows": gram,
            "skew_kernel_vectors": kernels, "projected_skew_rank_mod2": 153,
            "independence_minor": {"column_mixed_row_ids": pivots, "binary_rows_hex": [hex(r) for r in minor],
                                   "rank_mod2": 153, "determinant_mod2": 1},
            "integer_edge_coefficients_checked": checked_edges,
            "integer_selector_rhs_coefficients_checked": 153 * 480,
            "all_gram_combination_constants_zero": True,
            "rational_left_nullity": nullity, "rational_mixed_rank_lower": lower["edge_rank"],
            "rational_mixed_rank_upper": rank_upper, "rational_mixed_rank": rank_upper,
            "degree_reduction": "Over Q each degree row, including RHS8*x_a, equals one-third the sum of its18 mixed rows because every triple has weight3 and sum(q_a)=24.",
            "kernel_completeness": "The756 empty-row coordinate vectors and153 independent integer skew vectors form a Q-basis of the complete left kernel.",
            "equality_compatibility": "For every rational selector vector satisfying the original Gram equations, the unrestricted mixed and degree equalities have a rational edge solution; the analogous statement holds over R.",
            "scope_exclusions": ["No sign or upper-capacity bounds on edge variables are asserted.",
                                 "No integral edge solution, Boolean incidence, graph or component exclusion is asserted.",
                                 "No all-prime congruence or Smith-torsion conclusion follows from this rational theorem."],
            "optimizer_calls": 0, "native_imports": 0, "producer_imports": 0,
            "deadline_seconds": 60, "seconds": time.monotonic() - started}


if __name__ == "__main__":
    assert __debug__
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run()
    raw = canonical(result) + b"\n"
    encoded = gzip.compress(raw, mtime=0)
    with args.output.open("xb") as stream:
        stream.write(encoded)
    print(json.dumps({"status": result["status"], "rational_mixed_rank": result["rational_mixed_rank"],
                      "rational_left_nullity": result["rational_left_nullity"], "seconds": result["seconds"],
                      "sha256": sha(encoded), "raw_sha256": sha(raw), "bytes": len(encoded)}, sort_keys=True))
