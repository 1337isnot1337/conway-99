"""Exact formal enumerator with no zero coordinate, at dimension eleven.

This is a stronger, separately frozen proposal after the first formal
enumerator failed the elementary zero-coordinate closure B2 >= C(B1,2).
It constructs no code. Numerical infeasibility is never a certificate.
"""
import argparse
import json
from math import comb
from pathlib import Path
import time

import triangle_incidence_binary_integer_enumerator as helper

HELPER_SHA = "fedcc51699ebfde75ef279123730ba7354a2018bccc4fbef9eb3566cd7061378"
PARENT_PREP_SHA = "350adad3c86bcd0e651c12ebbbaea4aba67c07ddbbfb017234d9a44363d197c4"
PARENT_RESULT_SHA = "21097ac59a4dba22c6a6877a5ed896a05fb86aef4706792fb11015d9eda00b4c"
LOGS = Path(__file__).resolve().parents[1]/"logs/grids-and-triangles"


def bindings():
    assert helper.sha(Path(helper.__file__).read_bytes()) == HELPER_SHA
    prep = LOGS/"triangle-incidence-binary-integer-enumerator-preparation.json"
    prior = LOGS/"triangle-incidence-binary-integer-enumerator-query01.json"
    assert helper.sha(prep.read_bytes()) == PARENT_PREP_SHA
    assert helper.sha(prior.read_bytes()) == PARENT_RESULT_SHA
    parent = helper.prepared(prep)
    result = json.loads(prior.read_text())
    checked = helper.accept(result["rounded_nonzero_counts"])
    assert checked == result["certificate"]
    dual = checked["dual_weight_counts"]
    assert dual[1] == 20 and dual[2] == 189 < comb(dual[1], 2)
    return {"source_sha256": helper.sha(Path(__file__).read_bytes()),
            "helper_source_sha256": HELPER_SHA, "parent_preparation_sha256": PARENT_PREP_SHA,
            "parent_result_sha256": PARENT_RESULT_SHA,
            "parent_model_sha256": parent["model_sha256"]}


def model():
    result = helper.model()
    result["additional_exact_condition"] = {"dual_degree": 1, "value": 0,
        "coefficients": result["full_krawtchouk_rows"][1], "rhs": -helper.N}
    return result


def checked(preparation):
    prepared = json.loads(preparation.read_text())
    assert prepared["bindings"] == bindings()
    assert prepared["model"] == model()
    assert prepared["model_sha256"] == helper.sha(helper.canonical(model()))
    return prepared


def accept(values):
    result = helper.accept(values)
    assert result["dual_weight_counts"][1] == 0
    result["zero_coordinates"] = 0
    result["elementary_zero_coordinate_closure_passes"] = True
    return result


def query(preparation, output):
    import numpy as np
    from scipy.optimize import Bounds, LinearConstraint, milp

    start = time.monotonic()
    prepared = checked(preparation)
    m = prepared["model"]; width = m["variable_count"]
    rows = [[1]*7+[0]*(width-7)]
    lower = [helper.SIZE-1]; upper = [helper.SIZE-1]
    extra = m["additional_exact_condition"]
    rows.append(extra["coefficients"]+[0]*(width-7))
    lower.append(extra["rhs"]); upper.append(extra["rhs"])
    for i, record in enumerate(m["integrality_congruences"]):
        row = record["residues"]+[0]*(width-7)
        row[7+i] = -helper.SIZE
        rows.append(row); lower.append(record["rhs"]); upper.append(record["rhs"])
    for j in m["numerical_inequality_degrees"]:
        rows.append(m["full_krawtchouk_rows"][j]+[0]*(width-7))
        lower.append(helper.SIZE*helper.LOWER.get(j, 0)-comb(helper.N, j)); upper.append(np.inf)
    proposal = milp(np.zeros(width), integrality=np.ones(width),
        bounds=Bounds(m["variable_lower_bounds"], m["variable_upper_bounds"]),
        constraints=LinearConstraint(np.array(rows, dtype=float), lower, upper),
        options={"time_limit": 15, "mip_rel_gap": 0})
    result = {"status": "UNKNOWN_NO_ACCEPTED_FULL_SUPPORT_ENUMERATOR", "bindings": bindings(),
        "preparation_sha256": helper.sha(preparation.read_bytes()),
        "model_sha256": prepared["model_sha256"], "optimizer_calls": 1,
        "numerical_status": int(proposal.status), "numerical_message": str(proposal.message),
        "numerical_infeasibility_is_not_an_exclusion": True,
        "actual_code_constructed": False, "actual_graph_constructed": False}
    if proposal.x is not None:
        result["numerical_values_hex"] = [float(v).hex() for v in proposal.x]
        values = [int(round(float(v))) for v in proposal.x[:7]]
        result["rounded_nonzero_counts"] = values
        try:
            certificate = accept(values)
            result.update(status="EXACT_FORMAL_FULL_SUPPORT_DIMENSION_ELEVEN_ENUMERATOR",
                          certificate=certificate)
        except AssertionError as error:
            result["exact_rejection"] = str(error)
    result["seconds"] = time.monotonic()-start
    helper.save(output, result)
    return result


def replay(preparation, result_path, output):
    prepared = checked(preparation)
    result = json.loads(result_path.read_text())
    assert result["bindings"] == bindings()
    assert result["model_sha256"] == prepared["model_sha256"]
    assert result["preparation_sha256"] == helper.sha(preparation.read_bytes())
    assert result["status"] == "EXACT_FORMAL_FULL_SUPPORT_DIMENSION_ELEVEN_ENUMERATOR"
    assert accept(result["rounded_nonzero_counts"]) == result["certificate"]
    report = {"status": "PASS_EXACT_FULL_SUPPORT_ENUMERATOR_REPLAY", "bindings": bindings(),
        "result_sha256": helper.sha(result_path.read_bytes()),
        "nonzero_weight_counts": result["rounded_nonzero_counts"],
        "all100_dual_counts_checked": True, "formal_dimension": helper.DIMENSION,
        "zero_coordinates": 0, "optimizer_calls": 0, "actual_code_constructed": False}
    helper.save(output, report)
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
        result = {"status": "PREPARED_NO_OPTIMIZER", "bindings": bindings(), "model": m,
            "model_sha256": helper.sha(helper.canonical(m)),
            "new_condition": "B1=0, equivalently no identically zero code coordinate",
            "parent_formal_point_rejected_by_zero_coordinate_closure": True,
            "controls_reused_from_hash_bound_parent": True,
            "limits": {"optimizer_calls": 1, "solver_seconds": 15},
            "actual_code_constructed": False}
        helper.save(args.preparation, result)
    elif args.mode == "query":
        assert args.output
        result = query(args.preparation, args.output)
    else:
        assert args.result and args.output
        result = replay(args.preparation, args.result, args.output)
    print(json.dumps({k: v for k, v in result.items() if k not in ("model", "certificate")}, indent=2))


if __name__ == "__main__":
    main()
