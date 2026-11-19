"""One bounded 54-box native LP pilot; only exact row-box gaps exclude.

One native matrix load, one run per selected branch, all variable bounds reset.
The native internal time limit is cumulative. No per-call cancel flag is used;
an independent owned process supplies the hard wall bound. An existing ray is
read only after getDualRayExist succeeds. No full cover scan or primal claim.
"""

import argparse
import importlib.metadata
import json
import math
import os
from pathlib import Path
import platform
import sys
import time

for _name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[_name] = "1"

import rook_case4_low54_native_lp as exact
import rook_case4_box_hull_membership_query as supervisor

ROOT, LIMITS = exact.ROOT, exact.LIMITS
HELPER_SHA = "174c084dc9df3e3e0eed5e028ad18b6c89957c51b4ddfe7c0e4bbeaaa70d5380"
OWNER_SHA = "aa557c7b99ec3de71e9ecde3f6f7dfa3ca71066a835086cdd3b3f2eb7be558e5"
OWNER_HELPER_SHA = "54330f430c0c4dae03a0298533121ce43482ceb295f54df715ad2f2180d3503c"
REPLAY = "experiments/workspace/rook_case4_low54_native_lp_replay.py"
OPTIONS = {"solver": "simplex", "presolve": "off", "threads": 1,
           "parallel": "off", "random_seed": 0, "simplex_strategy": 1,
           "output_flag": True, "log_to_console": False}


def bindings():
    assert exact.sha(Path(exact.__file__).read_bytes()) == HELPER_SHA
    assert exact.sha(Path(supervisor.__file__).read_bytes()) == OWNER_SHA
    assert exact.sha(Path(supervisor.helper.__file__).read_bytes()) == OWNER_HELPER_SHA
    return {"helper": exact.reference(Path(exact.__file__)),
            "query": exact.reference(Path(__file__)),
            "cold": exact.reference(ROOT/REPLAY),
            "owner": exact.reference(Path(supervisor.__file__)),
            "owner_helper": exact.reference(Path(supervisor.helper.__file__))}


def runtime():
    import highspy
    import highspy._core
    import numpy
    return {"python": platform.python_version(), "python_executable": sys.executable,
            "highspy": importlib.metadata.version("highspy"), "numpy": numpy.__version__,
            "highs_version": highspy.Highs().version(),
            "native_extension_sha256": exact.sha(Path(highspy._core.__file__).read_bytes())}


def audit_sparse(matrix, storage, starts, indices, values):
    n, m = matrix["variables"], matrix["rows"]
    assert storage in ("rowwise", "colwise")
    assert len(indices) == len(values) == len(matrix["coefficients"])
    assert len(starts) == (m if storage == "rowwise" else n)+1
    assert all(type(v) is int for v in starts+indices)
    assert starts[0] == 0 and starts[-1] == len(indices) and starts == sorted(starts)
    restored = [[] for _ in range(m)]
    if storage == "rowwise":
        for r in range(m):
            for k in range(starts[r], starts[r+1]):
                assert 0 <= indices[k] < n
                restored[r].append([indices[k], values[k]])
    else:
        for j in range(n):
            for k in range(starts[j], starts[j+1]):
                assert 0 <= indices[k] < m
                restored[indices[k]].append([j, values[k]])
    p, idx, val = matrix["row_pointers"], matrix["column_indices"], matrix["coefficients"]
    expected = [[[idx[k], val[k]] for k in range(p[r], p[r+1])] for r in range(m)]
    assert [sorted(row) for row in restored] == expected
    assert all(len(row) == len({j for j, value in row}) for row in restored)
    return {"storage": storage, "entries": len(values), "all_signed_entries_exact": True}


def native(specification, directory):
    import highspy
    import numpy as np
    matrix = specification["matrix"]
    n, m = matrix["variables"], matrix["rows"]
    assert (n, m) == (1102, 2288)
    h = highspy.Highs()
    for name, value in {**OPTIONS, "log_file": str(directory/"highs.log")}.items():
        assert h.setOptionValue(name, value) == highspy.HighsStatus.kOk
    lp = highspy.HighsLp()
    lp.num_col_, lp.num_row_ = n, m
    lp.col_cost_ = np.zeros(n, dtype=np.float64)
    lp.col_lower_, lp.col_upper_ = np.zeros(n, dtype=np.float64), np.ones(n, dtype=np.float64)
    lp.row_lower_ = np.asarray(matrix["row_lower"], dtype=np.float64)
    lp.row_upper_ = np.asarray(matrix["row_upper"], dtype=np.float64)
    a = lp.a_matrix_
    a.format_, a.num_col_, a.num_row_ = highspy.MatrixFormat.kRowwise, n, m
    a.start_ = np.asarray(matrix["row_pointers"], dtype=np.int32)
    a.index_ = np.asarray(matrix["column_indices"], dtype=np.int32)
    a.value_ = np.asarray(matrix["coefficients"], dtype=np.float64)
    assert h.passModel(lp) == highspy.HighsStatus.kOk
    restored = h.getLp()
    ra = restored.a_matrix_
    # Native getters return whole Python lists. Cache each vector exactly once.
    starts, indices, values = list(ra.start_), list(ra.index_), list(ra.value_)
    row_lower, row_upper = list(restored.row_lower_), list(restored.row_upper_)
    costs = list(restored.col_cost_)
    col_lower, col_upper = list(restored.col_lower_), list(restored.col_upper_)
    assert (restored.num_col_, restored.num_row_) == (n, m)
    assert ra.format_ in (highspy.MatrixFormat.kRowwise, highspy.MatrixFormat.kColwise)
    transport = audit_sparse(matrix, "rowwise" if ra.format_ == highspy.MatrixFormat.kRowwise else "colwise",
                             starts, indices, values)
    assert row_lower == matrix["row_lower"] and row_upper == matrix["row_upper"]
    assert costs == [0]*n and col_lower == [0]*n and col_upper == [1]*n
    assert h.getRunTime() == 0
    audit = {"variables": n, "rows": m, "nonzeros": len(values),
             "matrix_sha256": specification["matrix_sha256"],
             "native_matrix_loads": 1, "native_sparse_transport": transport,
             "every_native_coefficient_and_endpoint_checked": True,
             "native_vector_getters_cached_once": True, "all_zero_objective": True}
    return h, audit


def reset_box(h, branch):
    import highspy
    import numpy as np
    lower, upper = exact.state_bounds(branch["state"])
    assert len(lower) == len(upper) == 1102
    assert h.changeColsBounds(1102, np.arange(1102, dtype=np.int32),
                              np.asarray(lower, dtype=np.float64), np.asarray(upper, dtype=np.float64)) == highspy.HighsStatus.kOk
    native_lp = h.getLp()
    actual_lower, actual_upper = list(native_lp.col_lower_), list(native_lp.col_upper_)
    assert actual_lower == lower and actual_upper == upper
    return {"variables_reset": 1102, "whole_cover_box_index": branch["index"],
            "state_sha256": branch["state_sha256"],
            "lower_upper_sha256": exact.sha(exact.canonical([lower, upper]))}


def preflight_child(preparation, directory):
    started = time.monotonic()
    assert not directory.exists()
    directory.mkdir(parents=True)
    report, spec = exact.load(preparation)
    h, audit = native(spec, directory)
    resets = [reset_box(h, branch) for branch in spec["selected54_boxes"]]
    assert h.getRunTime() == 0 and not h.getSolution().value_valid
    h.clear()
    result = {"status": "PASS_NATIVE_TRANSPORT_AND_ALL54_BOUND_RESETS_NO_SOLVE",
              "source_bindings": bindings(), "preparation": exact.reference(preparation),
              "specification": report["specification"], "runtime": runtime(), "options": OPTIONS,
              "limits": LIMITS, "audit": audit, "resets": resets,
              "native_calls": 0, "seconds": time.monotonic()-started}
    assert result["seconds"] < LIMITS["prepare_seconds"]
    exact.write(directory/"result.json", result)
    print(json.dumps({"status": result["status"], "seconds": result["seconds"]}), flush=True)
    return result


def preflight(preparation, directory):
    assert not directory.exists()
    directory.mkdir(parents=True)
    record = supervisor.owned([sys.executable, str(Path(__file__).resolve()), "preflight-child",
        "--preparation", str(preparation), "--directory", str(directory/"child")],
        directory, LIMITS["prepare_owner_seconds"], "preflight", True)
    exact.write(directory/"supervisor.json", record)
    return record


def prepare(preparation, preflight_directory, output):
    report, spec = exact.load(preparation)
    owner = json.loads((preflight_directory/"supervisor.json").read_bytes())
    assert supervisor.success(owner)
    flight = json.loads((preflight_directory/"child/result.json").read_bytes())
    assert flight["status"] == "PASS_NATIVE_TRANSPORT_AND_ALL54_BOUND_RESETS_NO_SOLVE"
    assert flight["source_bindings"] == bindings() and flight["options"] == OPTIONS
    assert flight["limits"] == LIMITS and flight["native_calls"] == 0
    assert flight["specification"] == report["specification"]
    assert flight["preparation"] == exact.reference(preparation)
    result = {"status": "PREPARED_ONE_LOW54_NATIVE_LP_PILOT_NO_QUERY",
        "source_bindings": bindings(), "preparation": exact.reference(preparation),
        "specification": report["specification"], "preflight": exact.reference(preflight_directory/"child/result.json"),
        "preflight_owner": exact.reference(preflight_directory/"supervisor.json"),
        "runtime": flight["runtime"], "limits": LIMITS, "options": OPTIONS,
        "selected_whole_cover_indices": [b["index"] for b in spec["selected54_boxes"]],
        "one_native_matrix_load": True, "native_columns_all_reset_per_branch": 1102,
        "calls_per_branch": 1, "external_per_call_cancellation_used": False,
        "internal_native_time_limit_is_cumulative": True, "no_hidden_ray_solve": True,
        "full_cover_pool_scans": 0, "feasible_and_unchecked_native_outcomes_are_unresolved": True,
        "complete_native_family": 54, "whole_case_boxes": 191, "production_queries": 0}
    exact.write(output, result)
    return result


def load(configuration, require_runtime=False):
    config = json.loads(configuration.read_bytes())
    assert config["source_bindings"] == bindings()
    assert config["limits"] == LIMITS and config["options"] == OPTIONS and config["production_queries"] == 0
    report = exact.read(config["preparation"])
    spec = exact.read(config["specification"])
    assert config["specification"] == report["specification"]
    assert spec["matrix_sha256"] == report["matrix_sha256"] == exact.sha(exact.canonical(spec["matrix"]))
    assert config["selected_whole_cover_indices"] == [b["index"] for b in spec["selected54_boxes"]]
    flight, owner = exact.read(config["preflight"]), exact.read(config["preflight_owner"])
    assert supervisor.success(owner) and flight["source_bindings"] == bindings()
    assert flight["runtime"] == config["runtime"] and flight["native_calls"] == 0
    if require_runtime:
        assert runtime() == config["runtime"]
    return config, spec


def finite_hex(values):
    return [float(v).hex() if math.isfinite(float(v)) else None for v in values]


def forward(configuration, directory):
    started = time.monotonic()
    import highspy
    deadline = started+LIMITS["forward_seconds"]
    assert not directory.exists()
    directory.mkdir(parents=True)
    result = {"status": "RUNNING", "configuration": exact.reference(configuration),
        "source_bindings": bindings(), "limits": LIMITS, "records": [], "native_calls": 0,
        "cumulative_native_seconds": 0.0, "exact_exclusions": 0, "complete54_native_prefix": False,
        "case4_excluded": False, "whole_graph_problem_resolved": False, "automatic_retries": 0}
    h = None
    try:
        config, spec = load(configuration, True)
        h, audit = native(spec, directory)
        exact.write(directory/"initialization.json", {**audit, "runtime": config["runtime"],
                                                     "seconds": time.monotonic()-started})
        with (directory/"records.jsonl").open("xb") as transcript:
            for branch in spec["selected54_boxes"]:
                k = branch["pilot_index"]
                assert k == result["native_calls"]
                remaining = min(deadline-time.monotonic(),
                    LIMITS["cumulative_native_seconds"]-result["cumulative_native_seconds"])
                if remaining <= 0:
                    result["stop_reason"] = "phase_or_cumulative_native_budget"
                    break
                assert sum(p.stat().st_size for p in directory.iterdir() if p.is_file()) < LIMITS["maximum_transcript_bytes"]
                reset = reset_box(h, branch)
                allowance = min(LIMITS["requested_native_seconds_per_branch"], remaining)
                previous_runtime = max(0.0, float(h.getRunTime()))
                assert math.isfinite(previous_runtime)
                absolute_limit = previous_runtime+allowance
                assert h.setOptionValue("time_limit", absolute_limit) == highspy.HighsStatus.kOk
                native_started = time.monotonic()
                run_status = h.run()  # Exactly one run for this branch.
                status = h.getModelStatus()
                ray_values = None
                ray_exists, ray_requested = False, False
                if status == highspy.HighsModelStatus.kInfeasible:
                    call_status, exists = h.getDualRayExist()
                    ray_exists = bool(call_status == highspy.HighsStatus.kOk and exists)
                    if ray_exists:
                        ray_requested = True
                        call_status, exists, values = h.getDualRay()
                        if call_status == highspy.HighsStatus.kOk and exists:
                            values = list(values)
                            if len(values) == len(spec["rows"]) and all(math.isfinite(float(v)) for v in values):
                                ray_values = finite_hex(values)
                native_seconds = time.monotonic()-native_started
                result["native_calls"] += 1
                result["cumulative_native_seconds"] += native_seconds
                solution = h.getSolution()
                basis = h.getBasis()
                numeric = {"configuration": exact.reference(configuration), "pilot_index": k,
                    "whole_cover_box_index": branch["index"], "bounds_reset": reset,
                    "matrix_sha256": spec["matrix_sha256"], "requested_seconds": allowance,
                    "native_absolute_time_limit": absolute_limit, "native_seconds": native_seconds,
                    "run_status": str(run_status), "model_status": str(status),
                    "numerically_infeasible": status == highspy.HighsModelStatus.kInfeasible,
                    "numerically_optimal": status == highspy.HighsModelStatus.kOptimal,
                    "solution_value_valid": bool(solution.value_valid), "solution_dual_valid": bool(solution.dual_valid),
                    "column_values_hex": finite_hex(list(solution.col_value)) if solution.value_valid else None,
                    "row_duals_hex": finite_hex(list(solution.row_dual)) if solution.dual_valid else None,
                    "existing_ray": ray_exists, "getDualRay_called": ray_requested, "ray_hex": ray_values,
                    "basis": {"valid": bool(basis.valid), "columns": [str(v) for v in list(basis.col_status)],
                              "rows": [str(v) for v in list(basis.row_status)]},
                    "native_feasibility_is_not_accepted": True, "extra_native_calls": 0}
                numeric_ref = exact.write(directory/f"numeric-{k:02d}.json", numeric)
                proof_ref, proposals = None, []
                if ray_values is not None:
                    for proposal in exact.rounded_proposals(ray_values):
                        if time.monotonic() >= deadline:
                            break
                        proof = exact.exclusion(spec, k, proposal["multipliers"])
                        proposals.append({"scale": proposal["scale"], "orientation": proposal["orientation"],
                                          "accepted": proof is not None})
                        if proof is not None:
                            proof.update(configuration=exact.reference(configuration), specification=config["specification"],
                                         numeric=numeric_ref, rounding={"scale": proposal["scale"], "orientation": proposal["orientation"]})
                            proof_ref = exact.write(directory/f"certificate-{k:02d}.json", proof)
                            result["exact_exclusions"] += 1
                            break
                record = {"pilot_index": k, "whole_cover_box_index": branch["index"],
                    "state_sha256": branch["state_sha256"], "numeric": numeric_ref,
                    "certificate": proof_ref, "rounding_attempts": proposals,
                    "status": "EXACT_EXCLUSION_OWNER_CHECKED" if proof_ref else "UNRESOLVED",
                    "numerical_status_is_not_a_certificate": True}
                record_ref = exact.write(directory/f"branch-{k:02d}.json", record)
                transcript.write(exact.canonical(record_ref)+b"\n"); transcript.flush(); os.fsync(transcript.fileno())
                result["records"].append(record_ref)
                print(json.dumps({"branch": k, "box": branch["index"], "status": record["status"],
                                  "native_seconds": native_seconds}), flush=True)
                if run_status == highspy.HighsStatus.kError:
                    result["stop_reason"] = "native_error_no_retry"
                    break
                if result["cumulative_native_seconds"] >= LIMITS["cumulative_native_seconds"]:
                    result["stop_reason"] = "cumulative_native_budget_reached"
                    break
        result["complete54_native_prefix"] = len(result["records"]) == 54
        result["status"] = "TERMINAL_COMPLETE54" if result["complete54_native_prefix"] else "TERMINAL_PARTIAL"
    except Exception as error:
        result.update(status="ERROR_PARTIAL_PREFIX_PRESERVED", error_type=type(error).__name__, error=str(error))
    finally:
        if h is not None:
            h.clear()
        result["seconds"] = time.monotonic()-started
        exact.write(directory/"result.json", result)
    return result


def run(configuration, directory):
    load(configuration)
    assert not directory.exists()
    directory.mkdir(parents=True)
    started = time.monotonic()
    forward_owner = supervisor.owned([sys.executable, str(Path(__file__).resolve()), "forward",
        "--configuration", str(configuration), "--directory", str(directory/"forward")],
        directory, LIMITS["forward_owner_seconds"], "forward", True)
    exact.write(directory/"forward-owner.json", forward_owner)
    cold_owner = supervisor.owned([sys.executable, str(ROOT/REPLAY),
        "--configuration", str(configuration), "--directory", str(directory),
        "--output", str(directory/"cold.json")], directory,
        LIMITS["cold_owner_seconds"], "cold", True)
    exact.write(directory/"cold-owner.json", cold_owner)
    accepted = supervisor.success(cold_owner) and (directory/"cold.json").exists()
    cold = json.loads((directory/"cold.json").read_bytes()) if accepted else None
    accepted = bool(accepted and cold["status"] == "PASS")
    result = {"status": "ACCEPTED_EXACT_PREFIX" if accepted and cold["status"] == "PASS" else "UNRESOLVED_COLD_NOT_ACCEPTED",
        "configuration": exact.reference(configuration), "source_bindings": bindings(), "limits": LIMITS,
        "forward_owner": exact.reference(directory/"forward-owner.json"),
        "cold_owner": exact.reference(directory/"cold-owner.json"),
        "cold": exact.reference(directory/"cold.json") if (directory/"cold.json").exists() else None,
        "exact_exclusions": cold["exact_exclusions"] if accepted else 0,
        "all54_low_branches_excluded": bool(accepted and cold["all54_low_branches_excluded"]),
        "case4_excluded": False, "whole_graph_problem_resolved": False,
        "automatic_retries": 0, "seconds": time.monotonic()-started}
    exact.write(directory/"result.json", result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("preflight-child", "preflight", "prepare", "forward", "run"))
    parser.add_argument("--preparation", type=Path)
    parser.add_argument("--preflight-directory", type=Path)
    parser.add_argument("--configuration", type=Path)
    parser.add_argument("--directory", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.mode == "preflight-child":
        answer = preflight_child(args.preparation.resolve(), args.directory.resolve())
    elif args.mode == "preflight":
        answer = preflight(args.preparation.resolve(), args.directory.resolve())
    elif args.mode == "prepare":
        answer = prepare(args.preparation.resolve(), args.preflight_directory.resolve(), args.output.resolve())
    elif args.mode == "forward":
        answer = forward(args.configuration.resolve(), args.directory.resolve())
    else:
        answer = run(args.configuration.resolve(), args.directory.resolve())
    print(json.dumps({k: answer[k] for k in ("status", "seconds", "exit_code", "hard_timeout") if k in answer}), flush=True)


if __name__ == "__main__":
    main()
