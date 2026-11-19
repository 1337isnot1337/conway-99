"""Exact Delsarte bounds for the binary point-triangle kernel code.

The seven allowed nonzero weights follow from the separate combinatorial
proof. Preparation and replay use integers/rationals only. One bounded LP
call may propose supports; its status alone proves nothing.
"""
import argparse
from fractions import Fraction
import hashlib
import json
from math import comb
from pathlib import Path
import time

from flint import fmpq_mat

N = 99
WEIGHTS = [36, 40, 44, 48, 52, 56, 60]


def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def save(path, value):
    assert not path.exists(), path
    path.write_text(json.dumps(value, indent=2) + "\n")


def krawtchouk(n, degree, weight):
    return sum((-1)**j * comb(weight, j) * comb(n - weight, degree - j)
               for j in range(max(0, degree - (n - weight)), min(degree, weight) + 1))


def model():
    return {"length": N, "allowed_nonzero_weights": WEIGHTS,
            "row_degrees": list(range(1, N + 1)),
            "coefficients": [[-krawtchouk(N, j, w) for w in WEIGHTS]
                             for j in range(1, N + 1)],
            "upper_bounds": [comb(N, j) for j in range(1, N + 1)],
            "variable_lower_bounds": [0] * len(WEIGHTS),
            "objective": "maximize 1 + sum(A_w)",
            "meaning": "A_w is the number of words of weight w in a binary linear code",
            "proof": "sum_w A_w K_j(w) = |C| times the number of weight-j words in C-perp; A_0=1"}


def controls():
    cases = 0
    for n in range(1, 12):
        values = [[krawtchouk(n, j, w) for w in range(n + 1)] for j in range(n + 1)]
        assert values[0] == [1] * (n + 1)
        assert values[1] == [n - 2*w for w in range(n + 1)]
        for j in range(n + 1):
            assert values[j][0] == comb(n, j)
            for k in range(n + 1):
                actual = sum(comb(n, w) * values[j][w] * values[k][w] for w in range(n + 1))
                assert actual == (2**n * comb(n, j) if j == k else 0)
                cases += 1
    # The [7,3,4] simplex code has seven nonzero words, all weight four.
    words = [sum((((a & b).bit_count() % 2) << (b-1)) for b in range(1, 8))
             for a in range(8)]
    assert len(set(words)) == 8 and sorted(x.bit_count() for x in words) == [0] + [4]*7
    for j in range(8):
        transformed = sum(krawtchouk(7, j, x.bit_count()) for x in words)
        dual_count = sum(y.bit_count() == j and all((y & x).bit_count() % 2 == 0 for x in words)
                         for y in range(128))
        assert transformed == 8 * dual_count
    assert krawtchouk(7, 1, 0) == 7 and -krawtchouk(7, 1, 4) == 1
    return {"exact_Krawtchouk_orthogonality_checks": cases,
            "simplex_code_MacWilliams_degrees": 8,
            "simplex_code_exact_dual_bound": 8,
            "optimizer_calls": 0}


def prepare(path):
    mathematical = model()
    record = {"status": "PREPARED_NO_OPTIMIZER",
              "source_sha256": digest(Path(__file__).read_bytes()),
              "model": mathematical, "model_sha256": digest(canonical(mathematical)),
              "controls": controls(),
              "query_limits": {"optimizer_calls": 1, "solver_seconds": 10},
              "scope": "necessary binary-incidence-code bound; no graph existence conclusion"}
    save(path, record)
    return record


def load_preparation(path):
    record = json.loads(path.read_text())
    assert record["source_sha256"] == digest(Path(__file__).read_bytes())
    assert record["model"] == model()
    assert record["model_sha256"] == digest(canonical(record["model"]))
    assert record["controls"] == controls()
    return record


def rational(value):
    return Fraction(str(value))


def unique_solution(rows, rhs, columns):
    """Exact RREF, with all free coordinates set to zero if necessary."""
    if not rows:
        return None
    augmented = fmpq_mat([list(row) + [b] for row, b in zip(rows, rhs)])
    reduced, rank = augmented.rref()
    result = [Fraction(0)] * columns
    for i in range(rank):
        pivot = next((j for j in range(columns + 1) if reduced[i, j]), None)
        if pivot == columns:
            return None
        if pivot is not None:
            result[pivot] = rational(reduced[i, columns])
    if any(sum(Fraction(a) * x for a, x in zip(row, result)) != b for row, b in zip(rows, rhs)):
        return None
    return result


def exact_check(mathematical, dual, primal=None):
    A, b = mathematical["coefficients"], mathematical["upper_bounds"]
    assert len(dual) == 99 and all(y >= 0 for y in dual)
    columns = [sum(dual[i] * A[i][j] for i in range(99)) for j in range(7)]
    assert all(value >= 1 for value in columns)
    upper = 1 + sum(dual[i] * b[i] for i in range(99))
    assert upper >= 1
    dimension = (upper.numerator // upper.denominator).bit_length() - 1
    assert Fraction(2**dimension) <= upper < 2**(dimension+1)
    out = {"exact_code_size_upper_bound": str(upper),
           "integer_code_size_upper_bound": upper.numerator // upper.denominator,
           "binary_kernel_dimension_upper_bound": dimension,
           "binary_incidence_rank_lower_bound": N - dimension,
           "dual_column_slacks": [str(x - 1) for x in columns],
           "all_99_dual_signs_and_seven_columns_checked": True}
    if primal is not None:
        assert len(primal) == 7 and all(x >= 0 for x in primal)
        slacks = [Fraction(b[i]) - sum(A[i][j] * primal[j] for j in range(7)) for i in range(99)]
        assert all(value >= 0 for value in slacks)
        value = 1 + sum(primal)
        assert value <= upper
        out.update(exact_primal_objective=str(value), exact_LP_optimum=value == upper,
                   all_99_primal_constraints_and_seven_bounds_checked=True)
    return out


def query(preparation, output):
    import numpy as np
    from scipy.optimize import linprog

    start = time.monotonic()
    prepared = load_preparation(preparation)
    mathematical = prepared["model"]
    A, b = mathematical["coefficients"], mathematical["upper_bounds"]
    scaled = np.asarray([[a / bound for a in row] for row, bound in zip(A, b)], dtype=float)
    result = linprog(-np.ones(7), A_ub=scaled, b_ub=np.ones(99), bounds=(0, None),
                     method="highs", options={"time_limit": 10})
    terminal = {"status": "UNKNOWN_NO_EXACT_BOUND", "source_sha256": prepared["source_sha256"],
                "preparation_sha256": digest(preparation.read_bytes()),
                "model_sha256": prepared["model_sha256"],
                "optimizer_calls": 1, "numerical_status": int(result.status),
                "numerical_message": str(result.message), "attempts": [],
                "unrestricted_graph_existence_resolved": False}
    if result.x is not None:
        terminal["numerical_primal"] = list(map(float, result.x))
    marginal = getattr(result.ineqlin, "marginals", None)
    if marginal is not None:
        terminal["numerical_scaled_row_duals"] = list(map(float, -marginal))
    if result.success and marginal is not None:
        for cutoff in (1e-7, 1e-9, 1e-11, 0.0):
            active_rows = [i for i, y in enumerate(-marginal) if y > cutoff]
            active_columns = [j for j, x in enumerate(result.x) if x > cutoff]
            y = unique_solution([[A[i][j] for i in active_rows] for j in active_columns],
                                [1] * len(active_columns), len(active_rows))
            attempt = {"cutoff": cutoff, "positive_dual_degrees": [i+1 for i in active_rows],
                       "positive_primal_weights": [WEIGHTS[j] for j in active_columns]}
            terminal["attempts"].append(attempt)
            if y is None:
                attempt["status"] = "NO_EXACT_ACTIVE_DUAL"
                continue
            dual = [Fraction(0)] * 99
            for i, value in zip(active_rows, y):
                dual[i] = value
            try:
                checked = exact_check(mathematical, dual)
            except AssertionError:
                attempt["status"] = "EXACT_DUAL_REJECTED"
                continue
            x = unique_solution([[A[i][j] for j in active_columns] for i in active_rows],
                                [b[i] for i in active_rows], len(active_columns))
            primal = None
            if x is not None:
                proposal = [Fraction(0)] * 7
                for j, value in zip(active_columns, x):
                    proposal[j] = value
                try:
                    checked = exact_check(mathematical, dual, proposal)
                    primal = proposal
                except AssertionError:
                    pass
            terminal.update(status="EXACT_BINARY_CODE_SIZE_BOUND", certificate=checked,
                            exact_dual=[str(value) for value in dual])
            if primal is not None:
                terminal["exact_primal"] = [str(value) for value in primal]
            attempt["status"] = "EXACT_DUAL_ACCEPTED"
            break
    terminal["seconds"] = time.monotonic() - start
    save(output, terminal)
    return terminal


def replay(preparation, result_path, output):
    prepared = load_preparation(preparation)
    result = json.loads(result_path.read_text())
    assert result["source_sha256"] == prepared["source_sha256"]
    assert result["preparation_sha256"] == digest(preparation.read_bytes())
    assert result["model_sha256"] == prepared["model_sha256"]
    assert result["status"] == "EXACT_BINARY_CODE_SIZE_BOUND"
    dual = list(map(Fraction, result["exact_dual"]))
    primal = list(map(Fraction, result["exact_primal"])) if "exact_primal" in result else None
    checked = exact_check(prepared["model"], dual, primal)
    assert checked == result["certificate"]
    record = {"status": "PASS_EXACT_BINARY_CODE_BOUND_REPLAY", "certificate": checked,
              "source_sha256": prepared["source_sha256"],
              "preparation_sha256": digest(preparation.read_bytes()),
              "result_sha256": digest(result_path.read_bytes()), "optimizer_calls": 0}
    save(output, record)
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["prepare", "query", "replay"])
    parser.add_argument("--preparation", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--result", type=Path)
    args = parser.parse_args()
    if args.mode == "prepare":
        out = prepare(args.preparation)
        out = {k: v for k, v in out.items() if k != "model"}
    elif args.mode == "query":
        assert args.output
        out = query(args.preparation, args.output)
    else:
        assert args.output and args.result
        out = replay(args.preparation, args.result, args.output)
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
