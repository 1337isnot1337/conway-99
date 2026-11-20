"""Exact selector-row rank and quota-one witnesses for second-moment reduction.

Generate may use python-flint only to propose an RREF. Replay uses integers
and the standard library: literal row identities give the rank upper bound,
and a nonzero minor modulo the stated prime gives the lower bound.
"""
import argparse
from fractions import Fraction
import gzip
import hashlib
import json
import math
from pathlib import Path
import signal
import time

MODEL_FILE_SHA256 = "404d91da35c798ba248887c22a7500957947e24b71d5197dc44432460e6d219e"
PRIME = 65521
SECONDS = 120


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canon(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def save_new(path, value):
    assert not path.exists()
    raw = json.dumps(value, indent=2).encode()+b"\n"
    path.write_bytes(gzip.compress(raw, mtime=0) if path.suffix == ".gz" else raw)


def load(path):
    raw = path.read_bytes()
    assert sha(raw) == MODEL_FILE_SHA256
    model = json.loads(gzip.decompress(raw))
    rows = model["original_selector_equalities"]
    assert len(rows) == 172
    matrix = [[int(a in row["support"]) for a in range(480)] for row in rows]
    assert all(row["support"] == sorted(set(row["support"])) for row in rows)
    rhs = [row["quota"] for row in rows]
    return model, matrix, rhs


def modular_pivots(matrix, prime):
    a = [[v % prime for v in row] for row in matrix]
    rank, columns = 0, []
    for col in range(len(a[0]) if a else 0):
        pivot = next((i for i in range(rank, len(a)) if a[i][col]), None)
        if pivot is None:
            continue
        a[rank], a[pivot] = a[pivot], a[rank]
        inv = pow(a[rank][col], -1, prime)
        a[rank] = [(v*inv) % prime for v in a[rank]]
        for i in range(rank+1, len(a)):
            coefficient = a[i][col]
            if coefficient:
                a[i] = [(v-coefficient*w) % prime for v, w in zip(a[i], a[rank])]
        columns.append(col)
        rank += 1
        if rank == len(a):
            break
    return columns


def determinant_mod(matrix, prime):
    n = len(matrix)
    assert all(len(row) == n for row in matrix)
    a = [[v % prime for v in row] for row in matrix]
    determinant = 1
    for col in range(n):
        pivot = next((i for i in range(col, n) if a[i][col]), None)
        if pivot is None:
            return 0
        if pivot != col:
            a[col], a[pivot] = a[pivot], a[col]
            determinant = -determinant
        value = a[col][col]
        determinant = determinant*value % prime
        inverse = pow(value, -1, prime)
        for i in range(col+1, n):
            factor = a[i][col]*inverse % prime
            if factor:
                for j in range(col, n):
                    a[i][j] = (a[i][j]-factor*a[col][j]) % prime
    return determinant % prime


def check_dependencies(matrix, rhs, basis, relations):
    assert len(relations) == len(matrix)
    assert basis == sorted(set(basis))
    for row, relation in enumerate(relations):
        denominator = relation["denominator"]
        terms = relation["terms"]
        assert type(denominator) is int and denominator > 0
        assert terms == sorted(terms) and len({j for j, c in terms}) == len(terms)
        assert all(j in basis and type(c) is int and c for j, c in terms)
        for column in range(len(matrix[0])):
            assert denominator*matrix[row][column] == sum(c*matrix[j][column] for j, c in terms)
        assert denominator*rhs[row] == sum(c*rhs[j] for j, c in terms)
    return True


def coverage(model):
    rows = model["original_selector_equalities"]
    supports = [[r for r, row in enumerate(rows) if row["quota"] == 1 and b in row["support"]]
                for b in range(480)]
    chosen = [min(s) if s else None for s in supports]
    uncovered = [b for b, s in enumerate(supports) if not s]
    diagonal = [i for i, row in enumerate(rows) if row.get("core_pair", [-1, -2])[0] == row.get("core_pair", [-1, -2])[1]]
    triples = [[rows[r]["core_pair"][0] for r in diagonal if b in rows[r]["support"]] for b in uncovered]
    assert all(len(h) == 3 for h in triples)
    assert all(bool(supports[b]) == bool(supports[action[b]])
               for action in model["selector_actions"] for b in range(480))
    return {"all_support_rows": supports, "chosen_row_for_each_signature": chosen,
            "covered_signatures": sum(bool(s) for s in supports),
            "uncovered_signatures": uncovered, "uncovered_triples": triples,
            "coverage_preserved_by_all12_actions": True}


def controls():
    a = [[1, 0, 1], [0, 1, 1], [1, 1, 2]]
    rhs = [2, 3, 5]
    relation = [{"denominator": 1, "terms": [[0, 1]]},
                {"denominator": 1, "terms": [[1, 1]]},
                {"denominator": 1, "terms": [[0, 1], [1, 1]]}]
    assert check_dependencies(a, rhs, [0, 1], relation)
    assert modular_pivots(a[:2], PRIME) == [0, 1]
    assert determinant_mod([[1, 0], [0, 1]], PRIME) == 1
    assert determinant_mod([[0, 1], [1, 0]], PRIME) == PRIME-1
    assert determinant_mod([[1, 1], [2, 2]], PRIME) == 0
    try:
        check_dependencies(a, [2, 3, 6], [0, 1], relation)
    except AssertionError:
        pass
    else:
        raise AssertionError("wrong RHS dependency accepted")
    return {"status": "PASS", "exact_dependency_control": True, "wrong_RHS_rejected": True,
            "nonsingular_swapped_and_singular_minors_checked": True, "optimizer_calls": 0}


def verify(model, matrix, rhs, certificate):
    assert certificate["schema"] == "f0-second-moments-selector-rank-v1"
    assert certificate["source_sha256"] == sha(Path(__file__).read_bytes())
    assert certificate["model_file_sha256"] == MODEL_FILE_SHA256
    basis = certificate["basis_original_rows"]
    assert check_dependencies(matrix, rhs, basis, certificate["original_row_dependencies"])
    minor = certificate["minor"]
    prime = minor["prime"]
    assert prime == PRIME and all(prime % d for d in range(2, math.isqrt(prime)+1))
    assert minor["rows"] == basis
    columns = minor["columns"]
    assert columns == sorted(set(columns)) and len(columns) == len(basis)
    assert all(0 <= j < 480 for j in columns)
    determinant = determinant_mod([[matrix[i][j] for j in columns] for i in basis], prime)
    assert determinant == minor["nonzero_determinant_mod_prime"] and determinant != 0
    assert certificate["exact_rank"] == len(basis)
    assert certificate["quota_one_coverage"] == coverage(model)
    assert certificate["controls"] == controls()
    return {"status": "PASS: exact rank bounded above and below; all RHS and coverage witnesses checked",
            "rank": len(basis), "original_rows": len(matrix), "columns": 480,
            "row_dependencies_checked": len(matrix), "integer_coefficient_positions_checked": 172*481,
            "prime": prime, "nonzero_minor": determinant,
            "covered_signatures": certificate["quota_one_coverage"]["covered_signatures"],
            "uncovered_signatures": len(certificate["quota_one_coverage"]["uncovered_signatures"]),
            "optimizer_calls": 0, "numerical_rank_used": False}


def generate(model, matrix, rhs):
    from flint import fmpq_mat
    rref, rank = fmpq_mat([[matrix[j][a] for j in range(172)] for a in range(480)]).rref()
    basis = []
    for i in range(rank):
        pivot = next(j for j in range(172) if rref[i, j])
        basis.append(pivot)
    assert basis == sorted(set(basis))
    relations = []
    for j in range(172):
        coefficients = [Fraction(str(rref[i, j])) for i in range(rank)]
        denominator = math.lcm(*(c.denominator for c in coefficients))
        terms = [[basis[i], c.numerator*(denominator//c.denominator)]
                 for i, c in enumerate(coefficients) if c]
        relations.append({"denominator": denominator, "terms": terms})
    assert check_dependencies(matrix, rhs, basis, relations)
    columns = modular_pivots([matrix[i] for i in basis], PRIME)
    assert len(columns) == rank
    determinant = determinant_mod([[matrix[i][j] for j in columns] for i in basis], PRIME)
    assert determinant
    certificate = {"schema": "f0-second-moments-selector-rank-v1",
                   "source_sha256": sha(Path(__file__).read_bytes()),
                   "model_file_sha256": MODEL_FILE_SHA256,
                   "exact_rank": rank, "basis_original_rows": basis,
                   "original_row_dependencies": relations,
                   "minor": {"prime": PRIME, "rows": basis, "columns": columns,
                             "nonzero_determinant_mod_prime": determinant},
                   "quota_one_coverage": coverage(model), "controls": controls(),
                   "proof": "All172 literal coefficient rows and RHS values are exact combinations of the chosen rows; their integer minor is nonzero modulo the verified prime.",
                   "optimizer_calls": 0}
    verify(model, matrix, rhs, certificate)
    return certificate


def main():
    p = argparse.ArgumentParser()
    p.add_argument("mode", choices=["generate", "replay"])
    p.add_argument("--model", type=Path, required=True)
    p.add_argument("--certificate", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    started = time.monotonic()
    def stop(signum, frame):
        raise TimeoutError("exact selector-rank preparation limit")
    previous = signal.signal(signal.SIGALRM, stop)
    signal.setitimer(signal.ITIMER_REAL, SECONDS)
    try:
        model, matrix, rhs = load(a.model)
        if a.mode == "generate":
            certificate = generate(model, matrix, rhs)
            save_new(a.certificate, certificate)
        else:
            raw = a.certificate.read_bytes()
            certificate = json.loads(gzip.decompress(raw) if a.certificate.suffix == ".gz" else raw)
        report = verify(model, matrix, rhs, certificate)
        report.update(source_sha256=sha(Path(__file__).read_bytes()),
                      certificate_sha256=sha(a.certificate.read_bytes()),
                      elapsed_seconds=time.monotonic()-started)
        save_new(a.output, report)
        print(json.dumps(report, indent=2))
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


if __name__ == "__main__":
    main()

