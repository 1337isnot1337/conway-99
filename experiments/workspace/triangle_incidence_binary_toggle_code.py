"""Binary coding bound with exact triangle-toggle and containment inequalities.

Ten added rows include equal-column replacements, weighted chain words,
and exact triangle-containing word populations through weight six.
One numerical LP proposes a support; all certificates use exact rationals.
"""
import argparse
from fractions import Fraction
import json
from math import comb
from pathlib import Path
import time

import triangle_incidence_binary_chain_code as parent

base = parent.base
PARENT_SHA = "8befdefb75ff4b4fbaee717d6ad5255f441f4ad2eed62bc8464f3efe6ff5025b"
CONTROL_SOURCE_SHA = "993fcdb85f2e4c50e5bb86a86d4a8a5a2ae75b3e0bac85453a25f6b4234e3c62"
CONTROL_REPORT_SHA = "e3014b321d39dd444d66427b3b24633a5743c99b31ebc846c064e803b4f500c5"


def bindings():
    assert base.digest(Path(parent.__file__).read_bytes()) == PARENT_SHA
    source = Path(__file__).with_name("triangle_incidence_binary_replacement_words.py")
    report = Path(__file__).resolve().parents[1]/"logs/grids-and-triangles/triangle-incidence-binary-replacement-controls.json"
    assert base.digest(source.read_bytes()) == CONTROL_SOURCE_SHA
    assert base.digest(report.read_bytes()) == CONTROL_REPORT_SHA
    extra = {
        "experiments/workspace/triangle_incidence_binary_toggle_words.py": "98b30dc02d75849886167c48360586dfb8ac7086ab367a9212adbca6036dfd80",
        "experiments/logs/grids-and-triangles/triangle-incidence-binary-toggle-controls.json": "017bb982b0129ae80140ea17cc26fdaa826ae012fbc3afab57e88e3fe5c016ce",
        "experiments/workspace/triangle_incidence_binary_toggle_six_controls.py": "d3f8cffd6e762779c26802881a4e5811103b7771277000bd71ea36d85f500486",
        "experiments/logs/grids-and-triangles/triangle-incidence-binary-toggle-six-controls.json": "9daf7e574e7cf1bfdfe08034a0e4943950ae67ed24c26ec79f4877fa58ce0d68",
    }
    root = Path(__file__).resolve().parents[2]
    for path, expected in extra.items():
        assert base.digest((root/path).read_bytes()) == expected
    return {"source_sha256": base.digest(Path(__file__).read_bytes()),
            "parent_bindings": parent.bindings(), "replacement_source_sha256": CONTROL_SOURCE_SHA,
            "replacement_controls_sha256": CONTROL_REPORT_SHA, "additional_controls": extra}


def model():
    result = parent.model()
    result["row_labels"] = ["dual_weight_"+str(j) for j in range(1, 100)]
    del result["row_degrees"]
    additions = [
        ("equal_column_edges", {2: 1, 1: -7}, 0),
        ("triangle_replacements", {3: 1, 2: -7, 1: 7}, 231),
        ("triangle_containing_weight_four", {4: 1, 1: -224}, 2079),
        ("weight_four_toggle", {4: 4, 3: -21, 2: 28, 1: -840}, 3465),
        ("chain_weight_five_edge_lower", {4: 28, 3: -42, 2: 56, 1: -728}, 52506),
        ("chain_weight_five_edge_upper", {5: 5, 4: -28, 3: 42, 2: -56, 1: 728}, 66834),
        ("triangle_and_chain_weight_five", {5: 1, 2: -217, 1: 14}, 23868),
        ("triangle_containing_weight_six", {6: 1, 3: -210, 2: 28, 1: -70}, -24024),
        ("disjoint_pair_weight_six_edge_lower", {5: 35, 4: -56, 3: 84, 2: -763, 1: 1435}, 27720),
        ("disjoint_pair_weight_six_edge_upper", {6: 7, 5: -35, 4: 56, 3: -84, 2: 763, 1: -1435}, 143682),
    ]
    for label, weights, lower in additions:
        result["coefficients"].append([
            lower-sum(c*base.krawtchouk(99, j, w) for j, c in weights.items())
            for w in base.WEIGHTS])
        result["upper_bounds"].append(sum(c*comb(99, j) for j, c in weights.items())-lower)
        result["row_labels"].append(label)
    assert result["upper_bounds"][99:101] == [4158, 123354]
    assert all(rhs > 0 for rhs in result["upper_bounds"])
    assert len(result["coefficients"]) == 109
    result["additional_dual_count_constraints"] = [{"label": name, "weighted_degrees": [[j, c] for j, c in sorted(weights.items())], "lower": lower} for name, weights, lower in additions]
    return result


def check_certificate(m, dual, primal=None):
    A, b = m["coefficients"], m["upper_bounds"]
    length = len(A)
    assert len(dual) == length == 109 and all(y >= 0 for y in dual)
    columns = [sum(dual[i]*A[i][j] for i in range(length)) for j in range(7)]
    assert all(value >= 1 for value in columns)
    upper = 1+sum(y*rhs for y, rhs in zip(dual, b))
    assert upper >= 1
    dimension = (upper.numerator//upper.denominator).bit_length()-1
    assert 2**dimension <= upper < 2**(dimension+1)
    out = {"exact_code_size_upper_bound": str(upper),
           "binary_kernel_dimension_upper_bound": dimension,
           "binary_incidence_rank_lower_bound": 99-dimension,
           "dual_column_slacks": list(map(str, (x-1 for x in columns))),
           "all109_dual_signs_and_seven_columns_checked": True}
    if primal is not None:
        assert len(primal) == 7 and all(x >= 0 for x in primal)
        assert all(sum(a*x for a, x in zip(row, primal)) <= rhs for row, rhs in zip(A, b))
        objective = 1+sum(primal)
        assert objective <= upper
        out.update(exact_primal_objective=str(objective), exact_LP_optimum=objective == upper,
                   all109_primal_rows_and_seven_bounds_checked=True)
    return out


def prepared(path):
    result = json.loads(path.read_text())
    assert result["bindings"] == bindings()
    assert result["model"] == model()
    assert result["model_sha256"] == base.digest(base.canonical(model()))
    return result


def query(preparation, output):
    import numpy as np
    from scipy.optimize import linprog

    start = time.monotonic(); record = prepared(preparation); m = record["model"]
    A, b = m["coefficients"], m["upper_bounds"]
    assert all(rhs > 0 for rhs in b)
    matrix = np.asarray([[a/rhs for a in row] for row, rhs in zip(A, b)], dtype=float)
    proposal = linprog(-np.ones(7), A_ub=matrix, b_ub=np.ones(len(A)), bounds=(0, None),
                       method="highs", options={"time_limit": 10})
    result = {"status": "UNKNOWN_NO_EXACT_TRIANGLE_TOGGLE_BOUND", "bindings": bindings(),
              "preparation_sha256": base.digest(preparation.read_bytes()),
              "model_sha256": record["model_sha256"], "optimizer_calls": 1,
              "numerical_status": int(proposal.status), "numerical_message": str(proposal.message),
              "attempts": [], "graph_existence_resolved": False}
    if proposal.x is not None:
        result["numerical_primal"] = list(map(float, proposal.x))
    marginals = getattr(proposal.ineqlin, "marginals", None)
    if marginals is not None:
        result["numerical_scaled_dual"] = list(map(float, -marginals))
    if proposal.success and marginals is not None:
        for cutoff in (1e-7, 1e-9, 1e-11, 0.0):
            rows = [i for i, value in enumerate(-marginals) if value > cutoff]
            columns = [j for j, value in enumerate(proposal.x) if value > cutoff]
            exact = base.unique_solution([[A[i][j] for i in rows] for j in columns],
                                         [1]*len(columns), len(rows))
            attempt = {"cutoff": cutoff, "rows": [m["row_labels"][i] for i in rows],
                       "weights": [base.WEIGHTS[j] for j in columns]}
            result["attempts"].append(attempt)
            if exact is None:
                attempt["status"] = "NO_EXACT_DUAL"; continue
            dual = [Fraction(0)]*len(A)
            for i, value in zip(rows, exact):
                dual[i] = value
            try:
                certificate = check_certificate(m, dual)
            except AssertionError:
                attempt["status"] = "EXACT_DUAL_REJECTED"; continue
            exact_primal = base.unique_solution([[A[i][j] for j in columns] for i in rows],
                                               [b[i] for i in rows], len(columns))
            if exact_primal is not None:
                primal = [Fraction(0)]*7
                for j, value in zip(columns, exact_primal):
                    primal[j] = value
                try:
                    certificate = check_certificate(m, dual, primal)
                    result["exact_primal"] = list(map(str, primal))
                except AssertionError:
                    pass
            result.update(status="EXACT_TRIANGLE_TOGGLE_CODE_BOUND", exact_dual=list(map(str, dual)),
                          certificate=certificate)
            attempt["status"] = "EXACT_DUAL_ACCEPTED"
            break
    result["seconds"] = time.monotonic()-start
    base.save(output, result)
    return result


def replay(preparation, result_path, output):
    m = prepared(preparation)["model"]
    result = json.loads(result_path.read_text())
    assert result["status"] == "EXACT_TRIANGLE_TOGGLE_CODE_BOUND" and result["bindings"] == bindings()
    assert result["preparation_sha256"] == base.digest(preparation.read_bytes())
    assert result["model_sha256"] == base.digest(base.canonical(m))
    primal = list(map(Fraction, result["exact_primal"])) if "exact_primal" in result else None
    certificate = check_certificate(m, list(map(Fraction, result["exact_dual"])), primal)
    assert certificate == result["certificate"]
    report = {"status": "PASS_EXACT_TRIANGLE_TOGGLE_CODE_BOUND_REPLAY", "bindings": bindings(),
              "result_sha256": base.digest(result_path.read_bytes()),
              "certificate": certificate, "optimizer_calls": 0}
    base.save(output, report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "query", "replay"))
    parser.add_argument("--preparation", type=Path, required=True)
    parser.add_argument("--result", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.mode == "prepare":
        m = model()
        result = {"status": "PREPARED_TRIANGLE_TOGGLE_CODE_MODEL_NO_OPTIMIZER", "bindings": bindings(),
                  "model": m, "model_sha256": base.digest(base.canonical(m)),
                  "limits": {"optimizer_calls": 1, "solver_seconds": 10}}
        base.save(args.preparation, result)
    elif args.mode == "query":
        assert args.output
        result = query(args.preparation, args.output)
    else:
        assert args.result and args.output
        result = replay(args.preparation, args.result, args.output)
    print(json.dumps({k: v for k, v in result.items() if k != "model"}, indent=2))


if __name__ == "__main__":
    main()
