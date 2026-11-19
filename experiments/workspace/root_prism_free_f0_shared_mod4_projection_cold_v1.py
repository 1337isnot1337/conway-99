"""Independent direct Z/4 contractions and original-Gram membership checks.

No projection producer, bit-plane core, or domain producer is imported.
Coefficient-state masks directly contract original rows. Dense unit row
elimination independently tests the 172-row Gram module. A reversed-order
binary reconstruction checks unit rank and every saved even rank witness.
"""
import argparse
import gzip
import hashlib
from itertools import product
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[2]


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def reference(path):
    raw = path.read_bytes()
    return {"path": str(path.relative_to(ROOT)), "sha256": digest(raw)}


def read(binding):
    raw = (ROOT / binding["path"]).read_bytes()
    assert digest(raw) == binding["sha256"]
    return json.loads(gzip.decompress(raw) if binding["path"].endswith(".gz") else raw)


def write(path, value):
    raw = canonical(value) + b"\n"
    with path.open("xb") as stream:
        stream.write(raw)
    return reference(path)


def positions(bits):
    while bits:
        bit = bits & -bits
        yield bit.bit_length() - 1
        bits ^= bit


def decode(value, dimension):
    assert set(value) == {"low_hex", "high_hex"}
    result = []
    for name in ("low_hex", "high_hex"):
        text = value[name]
        assert type(text) is str and 1 <= len(text) <= (dimension + 3) // 4
        number = int(text, 16)
        assert text == format(number, "x") and 0 <= number < (1 << dimension)
        result.append(number)
    return tuple(result)


def entries(value):
    low, high = value
    for i in positions(low | high):
        yield i, ((low >> i) & 1) + 2 * ((high >> i) & 1)


def add_mask(states, mask, coefficient):
    """Add coefficient at all mask coordinates using disjoint residue classes."""
    coefficient %= 4
    if not coefficient:
        return states
    one, two, three = states
    old = (mask & ~(one | two | three), mask & one, mask & two, mask & three)
    keep = ~mask
    return tuple((states[i - 1] & keep) | old[(i - coefficient) % 4] for i in (1, 2, 3))


def binary_basis(vectors, check=lambda: None):
    basis = {}
    for value in vectors:
        check()
        while value:
            pivot = (value & -value).bit_length() - 1
            if pivot not in basis:
                basis[pivot] = value
                break
            value ^= basis[pivot]
    return basis


def binary_reduce(value, basis):
    for pivot in sorted(basis):
        if value >> pivot & 1:
            value ^= basis[pivot]
    return value


def dense_module(vectors):
    """Independent unit Gauss-Jordan, followed by a binary even residual basis."""
    matrix = [list(row) for row in vectors]
    width = len(matrix[0])
    assert all(len(row) == width and all(type(c) is int and 0 <= c < 4 for c in row) for row in matrix)
    pivots, at = [], 0
    for column in range(width):
        candidate = next((r for r in range(at, len(matrix)) if matrix[r][column] & 1), None)
        if candidate is None:
            continue
        matrix[at], matrix[candidate] = matrix[candidate], matrix[at]
        inv = matrix[at][column]
        matrix[at] = [(x * inv) % 4 for x in matrix[at]]
        for r in range(len(matrix)):
            if r != at and matrix[r][column]:
                c = matrix[r][column]
                matrix[r] = [(x - c * y) % 4 for x, y in zip(matrix[r], matrix[at])]
        pivots.append(column)
        at += 1
    assert all(not (c & 1) for row in matrix[at:] for c in row)
    even = binary_basis([sum(1 << i for i, c in enumerate(row) if c == 2) for row in matrix[at:]])
    assert all(matrix[r][p] == int(r == j) for r in range(at) for j, p in enumerate(pivots))
    return list(zip(pivots, matrix[:at])), even


def member(vector, module):
    current = list(vector)
    units, even = module
    for pivot, row in units:
        c = current[pivot]
        if c:
            current = [(x - c * y) % 4 for x, y in zip(current, row)]
    if any(x & 1 for x in current):
        return False
    half = sum(1 << i for i, c in enumerate(current) if c == 2)
    return binary_reduce(half, even) == 0


def controls():
    started = time.monotonic()
    vectors = list(product(range(4), repeat=3))
    pair_count = 0
    for a in vectors:
        initial = tuple(sum(1 << i for i, c in enumerate(a) if c == k) for k in (1, 2, 3))
        for b in vectors:
            actual = initial
            for c in (1, 2, 3):
                actual = add_mask(actual, sum(1 << i for i, value in enumerate(b) if value == c), c)
            expected = tuple(sum(1 << i for i, (x, y) in enumerate(zip(a, b)) if (x + y) % 4 == c) for c in (1, 2, 3))
            assert actual == expected
            pair_count += 1
    matrices = checks = 0
    v2 = list(product(range(4), repeat=2))
    for values in product(range(4), repeat=4):
        rows = [values[:2], values[2:]]
        module = dense_module(rows)
        span = {tuple(sum(v[r] * rows[r][j] for r in range(2)) % 4 for j in range(2)) for v in v2}
        for vector in v2:
            assert member(vector, module) == (vector in span)
            checks += 1
        matrices += 1
    return {"status": "PASS_INDEPENDENT_MOD4_COLD_ARITHMETIC_AND_DENSE_MODULE_CONTROLS",
            "disjoint_state_vector_pairs": pair_count, "two_by_two_matrices": matrices,
            "membership_checks": checks, "seconds": time.monotonic() - started,
            "optimizer_calls": 0, "native_imports": 0}


def domain(config):
    saved = read(config["inputs"]["domain"])
    core, triples = saved["component_core_rows"], saved["signature_domain"]
    assert len(core) == 21 and all(type(x) is int and 0 <= x < (1 << 21) for x in core)
    assert all(not (core[i] >> i & 1) for i in range(21))
    assert all((core[i] >> j & 1) == (core[j] >> i & 1) for i in range(21) for j in range(21))
    assert len(triples) == 480 and len(set(map(tuple, triples))) == 480
    assert all(h == sorted(set(h)) and len(h) == 3 and all(type(i) is int and 0 <= i < 18 for i in h) for h in triples)
    targets = [[2 - int(i in h) - sum((core[3+i] >> (3+j)) & 1 for j in h) for i in range(18)] for h in triples]
    assert targets == saved["row_targets"] and all(sum(q) == 24 and min(q) >= 0 for q in targets)
    signatures = [set(h) for h in triples]
    edges, neighbors = [], [[] for _ in triples]
    for a in range(480):
        for b in range(a + 1, 480):
            if len(signatures[a] & signatures[b]) <= 1 and all(targets[a][i] for i in triples[b]) and all(targets[b][i] for i in triples[a]):
                edges.append([a, b])
                neighbors[a].append(b)
                neighbors[b].append(a)
    assert len(edges) == 68394 and neighbors == saved["possible_neighbor_signature_ids"]
    gram = []
    for i in range(18):
        for j in range(i, 18):
            quota = 12 * int(i == j) + 2 - (core[3+i] & core[3+j]).bit_count() - ((core[3+i] >> (3+j)) & 1)
            gram.append({"core_pair": [i, j], "support": [a for a, h in enumerate(triples) if i in h and j in h], "rhs": quota})
    gram.append({"core_pair": None, "support": list(range(480)), "rhs": 60})
    hashes = {name: digest(canonical(value)) for name, value in (("triples", triples), ("targets", targets), ("edges", edges), ("gram", gram))}
    rows = [0] * 9120
    for e, (a, b) in enumerate(edges):
        bit = 1 << e
        rows[19*a] |= bit
        rows[19*b] |= bit
        for i in triples[b]:
            rows[19*a + 1 + i] |= bit
        for i in triples[a]:
            rows[19*b + 1 + i] |= bit
    return rows, targets, gram, hashes


def contract(proof, rows, targets, check):
    states, rhs = (0, 0, 0), [0] * 481
    for n, (row, c) in enumerate(entries(proof)):
        if n % 256 == 0:
            check()
        states = add_mask(states, rows[row], c)
        a, offset = divmod(row, 19)
        rhs[a] = (rhs[a] + c * (8 if offset == 0 else targets[a][offset - 1])) % 4
    return states, rhs


def check_configuration(path):
    config = json.loads(path.read_bytes())
    assert config["schema"] == "conway99.f0.shared-mod4-configuration.v1"
    assert config["sources"]["cold"] == reference(Path(__file__).resolve())
    for group in (config["sources"], config["inputs"]):
        for binding in group.values():
            p = ROOT / binding["path"]
            assert reference(p) == binding
    assert config["dimensions"] == {"selectors": 480, "sites": 18, "edges": 68394, "degree_rows": 480, "mixed_rows": 8640, "gram_rows": 172}
    assert config["limits"] == {"preparation_seconds": 30, "preparation_owner_seconds": 45, "main_seconds": 120, "main_owner_seconds": 135, "cold_seconds": 120, "cold_owner_seconds": 135, "maximum_raw_certificate_bytes": 134217728}
    return config


def run(configuration, run_directory, output):
    started = time.monotonic()
    config = check_configuration(configuration)
    def check():
        if time.monotonic() - started >= config["limits"]["cold_seconds"]:
            raise TimeoutError("mod4 independent cold deadline")
    owner = json.loads((run_directory / "owner.json").read_bytes())
    report_ref = reference(run_directory / "report.json")
    report = read(report_ref)
    assert owner["report_accepted"] and owner["report"] == report_ref
    assert owner["configuration"] == reference(configuration) and owner["source_sha256"] == config["sources"]["producer"]["sha256"]
    assert owner["supervision"]["child_reaped"] and not owner["supervision"]["hard_timeout"] and owner["supervision"]["exit_code"] == 0
    assert report["status"] == "COMPLETE_EXACT_MOD4_SHARED_PROJECTION_AWAITING_INDEPENDENT_COLD"
    assert report["configuration"] == reference(configuration)
    saved = read(report["certificates"])
    assert saved["configuration"] == reference(configuration)
    rows, targets, gram, hashes = domain(config)
    assert hashes == report["inventory"]["domain_hashes"] == saved["domain_hashes"]
    assert len(saved["obligations"]) == report["obligations"] == 9120 - report["unit_rank"]
    assert len(saved["even_rank_witnesses"]) == report["even_rank"]
    unit_basis = binary_basis(reversed(rows), check)
    assert sorted(unit_basis) == saved["unit_pivots"] and len(unit_basis) == report["unit_rank"] == 7713
    even_residuals = []
    for item in saved["even_rank_witnesses"]:
        proof = decode(item["original_row_multipliers"], 9120)
        expected_half = int(item["edge_half_hex"], 16)
        assert item["edge_half_hex"] == format(expected_half, "x") and 0 < expected_half < (1 << 68394)
        assert item["pivot"] == (expected_half & -expected_half).bit_length() - 1
        actual, rhs = contract(proof, rows, targets, check)
        assert actual == (0, expected_half, 0)
        assert rhs == [dict(entries(decode(item["selector_rhs"], 481))).get(j, 0) for j in range(481)]
        even_residuals.append(binary_reduce(expected_half, unit_basis))
    independent_even = binary_basis(even_residuals, check)
    assert len(independent_even) == report["even_rank"]
    dense_gram = [[int(j in row["support"]) for j in range(480)] + [(-row["rhs"]) % 4] for row in gram]
    module = dense_module(dense_gram)
    assert len(module[0]) == report["gram_unit_rank"] and len(module[1]) == report["gram_even_rank"]
    nonzero = new = zero_kind = doubled_kind = 0
    membership = []
    for index, item in enumerate(saved["obligations"]):
        check()
        assert item["index"] == index and item["kind"] in ("zero_residual", "doubled_even")
        zero_kind += int(item["kind"] == "zero_residual")
        doubled_kind += int(item["kind"] == "doubled_even")
        proof = decode(item["original_row_multipliers"], 9120)
        actual, rhs = contract(proof, rows, targets, check)
        assert actual == (0, 0, 0), "original edge contraction is nonzero modulo four"
        proposed_rhs = dict(entries(decode(item["selector_rhs"], 481)))
        assert rhs == [proposed_rhs.get(j, 0) for j in range(481)]
        gram_proof = list(entries(decode(item["gram_row_multipliers"], 172)))
        remainder = dict(entries(decode(item["remainder"], 481)))
        expected = [(rhs[j] - sum(c * dense_gram[r][j] for r, c in gram_proof)) % 4 for j in range(481)]
        assert expected == [remainder.get(j, 0) for j in range(481)]
        implied = member(rhs, module)
        assert type(item["implied_by_original_gram"]) is bool and implied == item["implied_by_original_gram"] == (not any(expected))
        assert item["nonzero_selector_congruence"] == any(rhs)
        nonzero += int(any(rhs)); new += int(not implied)
        membership.append({"index": index, "implied": implied, "original_edge_contraction_zero": True})
    assert zero_kind == report["zero_residual_count"] and doubled_kind == report["even_rank"]
    assert nonzero == report["nonzero_selector_congruences"] and new == report["not_implied_by_original_gram"]
    check()
    assert not any(name.split(".")[0] in {"highspy", "ortools", "numpy", "scipy"} for name in sys.modules)
    result = {"status": "PASS_INDEPENDENT_ALL_MOD4_OBLIGATIONS_AND_GRAM_MEMBERSHIP",
              "source": reference(Path(__file__).resolve()), "configuration": reference(configuration),
              "producer_report": report_ref, "producer_owner": reference(run_directory / "owner.json"),
              "certificates": report["certificates"], "unit_rank_recomputed": len(unit_basis),
              "even_rank_witnesses_directly_contracted_and_independent": len(independent_even),
              "all68394_edge_coefficients_checked_per_obligation": True,
              "obligations_checked": len(membership), "nonzero_selector_congruences": nonzero,
              "not_implied_by_original_gram": new, "gram_unit_rank": len(module[0]), "gram_even_rank": len(module[1]),
              "membership_checks": membership, "generator_completeness_from_reviewed_producer_algorithm": True,
              "whole_component_excluded": False, "integer_or_all_prime_feasibility_claimed": False,
              "optimizer_calls": 0, "native_imports": 0, "seconds": time.monotonic() - started}
    write(output, result)
    return result


if __name__ == "__main__":
    assert __debug__
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--configuration", type=Path, required=True)
    parser.add_argument("--run-directory", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.configuration.resolve(), args.run_directory.resolve(), args.output.resolve())
    print(json.dumps({"status": result["status"], "seconds": result["seconds"]}), flush=True)
