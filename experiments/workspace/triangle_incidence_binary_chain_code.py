"""Bound the binary triangle kernel using star and three-triangle-chain words.

The earlier degree-three/four/six bound remains frozen. This model adds
the independently justified star-subset counts. One bounded LP may choose
supports; every accepted bound is checked exactly in all seven columns.
"""
import argparse
from fractions import Fraction
import hashlib
from itertools import combinations
import json
from math import comb
from pathlib import Path
import time

import triangle_incidence_binary_code as base

BASE_SHA = "c2cf228e0e6858b56d642c42227bed5d21913fe2ff2f88b15d82d03d4c35a001"
LOWER = {3: 231, 4: 2079, 5: 23868, 6: 24486, 7: 3465, 8: 3465,
         11: 2079, 12: 693, 15: 99}


CHAIN_SOURCE_SHA = "34bfb0832a6f1bf49db3ee6e39dd68baf4e1ce650f62723992f344f6421bed57"
CHAIN_REPORT_SHA = "c2e4fcda3a4f578a75ed2c01a47e816807c4ac4ee4a50d3518fb2c4d479937ef"


def bindings():
    assert base.digest(Path(base.__file__).read_bytes()) == BASE_SHA
    chain_source = Path(__file__).with_name("triangle_chain_binary_words.py")
    chain_report = Path(__file__).resolve().parents[1]/"logs/grids-and-triangles/triangle-chain-binary-words-census.json"
    assert base.digest(chain_source.read_bytes()) == CHAIN_SOURCE_SHA
    assert base.digest(chain_report.read_bytes()) == CHAIN_REPORT_SHA
    return {"source_sha256": base.digest(Path(__file__).read_bytes()),
            "exact_arithmetic_helper_sha256": BASE_SHA,
            "chain_collision_source_sha256": CHAIN_SOURCE_SHA,
            "chain_collision_report_sha256": CHAIN_REPORT_SHA}


def model():
    return {"length": 99, "allowed_nonzero_weights": base.WEIGHTS,
            "row_degrees": list(range(1, 100)),
            "coefficients": [[LOWER.get(j, 0)-base.krawtchouk(99, j, w) for w in base.WEIGHTS]
                             for j in range(1, 100)],
            "upper_bounds": [comb(99, j)-LOWER.get(j, 0) for j in range(1, 100)],
            "variable_lower_bounds": [0]*7, "objective": "maximize 1+sum(A_w)",
            "forced_dual_weight_lower_bounds": [[j, n] for j, n in sorted(LOWER.items())]}


def star_controls():
    triangles = [1 | (1 << (2*i+1)) | (1 << (2*i+2)) for i in range(7)]
    words = {}
    for k in range(8):
        values = set()
        for subset in combinations(triangles, k):
            word = 0
            for triangle in subset:
                word ^= triangle
            assert word.bit_count() == 2*k + k % 2
            assert word not in values
            values.add(word)
        assert len(values) == comb(7, k)
        words[k] = values
    assert len(set().union(*words.values())) == 128
    expected = {3: 99*7//3, 6: comb(231, 2)-99*comb(7, 2)}
    for k in range(2, 8):
        expected[2*k+k%2] = 99*comb(7, k)
    expected[5] = 231*3*6**2 - 9*120
    assert expected == LOWER
    return {"all_star_subsets_checked": 128, "distinct_star_words": 128,
            "all_nine_population_formulas_checked": True, "optimizer_calls": 0}


def prepare(path):
    mathematical = model()
    # The old positive dual need not be optimal for the stronger model.
    # Its proposed active equations have a unique exact solution; retain
    # the failure of primal nonnegativity as a reason for a new query.
    active = list(range(1, 8))
    x = base.unique_solution([mathematical["coefficients"][i] for i in active],
                             [mathematical["upper_bounds"][i] for i in active], 7)
    assert x is not None
    record = {"status": "PREPARED_FORCED_STAR_AND_CHAIN_DUAL_WORD_MODEL_NO_OPTIMIZER",
              **bindings(), "model": mathematical,
              "model_sha256": base.digest(base.canonical(mathematical)),
              "controls": star_controls(),
              "old_active_degrees": [i+1 for i in active],
              "old_active_equations_exact_primal": list(map(str, x)),
              "old_active_primal_nonnegative": all(v >= 0 for v in x),
              "query_limits": {"optimizer_calls": 1, "solver_seconds": 10},
              "graph_existence_resolved": False}
    assert not record["old_active_primal_nonnegative"]
    base.save(path, record)
    return record


def checked(path):
    prepared = json.loads(path.read_text())
    for k, v in bindings().items():
        assert prepared[k] == v
    assert prepared["model"] == model()
    assert prepared["model_sha256"] == base.digest(base.canonical(model()))
    assert prepared["controls"] == star_controls()
    return prepared


def query(preparation, output):
    import numpy as np
    from scipy.optimize import linprog

    start = time.monotonic()
    prepared = checked(preparation)
    mathematical = prepared["model"]
    A, b = mathematical["coefficients"], mathematical["upper_bounds"]
    assert all(v > 0 for v in b)
    scaled = np.asarray([[a / rhs for a in row] for row, rhs in zip(A, b)], dtype=float)
    proposal = linprog(-np.ones(7), A_ub=scaled, b_ub=np.ones(99), bounds=(0, None),
                       method="highs", options={"time_limit": 10})
    result = {"status": "UNKNOWN_NO_EXACT_CODE_BOUND", **bindings(),
              "preparation_sha256": base.digest(preparation.read_bytes()),
              "model_sha256": prepared["model_sha256"], "optimizer_calls": 1,
              "numerical_status": int(proposal.status), "numerical_message": str(proposal.message),
              "attempts": [], "unrestricted_graph_existence_resolved": False}
    if proposal.x is not None:
        result["numerical_primal"] = list(map(float, proposal.x))
    marginal = getattr(proposal.ineqlin, "marginals", None)
    if marginal is not None:
        result["numerical_scaled_dual"] = list(map(float, -marginal))
    if proposal.success and marginal is not None:
        for cutoff in (1e-7, 1e-9, 1e-11, 0.0):
            rows = [i for i, value in enumerate(-marginal) if value > cutoff]
            columns = [j for j, value in enumerate(proposal.x) if value > cutoff]
            active = base.unique_solution([[A[i][j] for i in rows] for j in columns],
                                          [1]*len(columns), len(rows))
            attempt = {"cutoff": cutoff, "degrees": [i+1 for i in rows],
                       "weights": [base.WEIGHTS[j] for j in columns]}
            result["attempts"].append(attempt)
            if active is None:
                attempt["status"] = "NO_EXACT_DUAL"
                continue
            dual = [Fraction(0)]*99
            for i, value in zip(rows, active):
                dual[i] = value
            try:
                certificate = base.exact_check(mathematical, dual)
            except AssertionError:
                attempt["status"] = "EXACT_DUAL_REJECTED"
                continue
            active_primal = base.unique_solution([[A[i][j] for j in columns] for i in rows],
                                                 [b[i] for i in rows], len(columns))
            if active_primal is not None:
                primal = [Fraction(0)]*7
                for j, value in zip(columns, active_primal):
                    primal[j] = value
                try:
                    certificate = base.exact_check(mathematical, dual, primal)
                    result["exact_primal"] = list(map(str, primal))
                except AssertionError:
                    pass
            result.update(status="EXACT_FORCED_STAR_AND_CHAIN_CODE_BOUND", exact_dual=list(map(str, dual)),
                          certificate=certificate)
            attempt["status"] = "EXACT_DUAL_ACCEPTED"
            break
    result["seconds"] = time.monotonic()-start
    base.save(output, result)
    return result


def replay(preparation, result_path, output):
    prepared = checked(preparation)
    result = json.loads(result_path.read_text())
    for k, v in bindings().items():
        assert result[k] == v
    assert result["preparation_sha256"] == base.digest(preparation.read_bytes())
    assert result["model_sha256"] == prepared["model_sha256"]
    assert result["status"] == "EXACT_FORCED_STAR_AND_CHAIN_CODE_BOUND"
    dual = list(map(Fraction, result["exact_dual"]))
    primal = list(map(Fraction, result["exact_primal"])) if "exact_primal" in result else None
    certificate = base.exact_check(prepared["model"], dual, primal)
    assert certificate == result["certificate"]
    report = {"status": "PASS_EXACT_FORCED_STAR_AND_CHAIN_CODE_BOUND_REPLAY", **bindings(),
              "result_sha256": base.digest(result_path.read_bytes()),
              "preparation_sha256": base.digest(preparation.read_bytes()),
              "certificate": certificate, "optimizer_calls": 0}
    base.save(output, report)
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=["prepare", "query", "replay"])
    p.add_argument("--preparation", type=Path, required=True)
    p.add_argument("--output", type=Path)
    p.add_argument("--result", type=Path)
    a = p.parse_args()
    if a.mode == "prepare":
        report = prepare(a.preparation)
        report = {k: v for k, v in report.items() if k != "model"}
    elif a.mode == "query":
        assert a.output
        report = query(a.preparation, a.output)
    else:
        assert a.output and a.result
        report = replay(a.preparation, a.result, a.output)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
