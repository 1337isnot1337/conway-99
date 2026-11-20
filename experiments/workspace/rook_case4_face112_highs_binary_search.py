"""One bounded HiGHS binary incidence search with exact external covers.

An owned child has 180 wall seconds including imports, native initialization,
cover scans, and result writes. It makes at most 30 native calls. Every proposed
Boolean point is checked on all original rows and 178,533 covers before it can
be accepted. Numerical infeasibility never excludes this case.
"""
import argparse
import gzip
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import resource
import sys
import time

import rook_case4_face112_highs_binary_model as exact

ROOT = Path(__file__).resolve().parents[2]
BASE = "experiments/logs/grids-and-triangles/"
MODEL = BASE+"rook-case4-face112-highs-binary-model01.json"
MODEL_SHA = "195bf6c2c274100686087fd71a22f488f7aaee28025e39e490d7751bffcbceb6"
BUILDER_SHA = "3869c9aa63a596421a7fefebc492d90159b6ac8edf0739a0995254bcfd5c4301"
SUPERVISOR = "experiments/workspace/root_prism_free_f0_local_neighbors_batch.py"
SUPERVISOR_SHA = "b8e5323f92fa105ff2c0ed5b1667ac25d7c92f85f8cac45b170ddc56208f8278"
SUPERVISOR_PREP = "experiments/logs/root-prism-free/f0-local41-batch02-preparation.json"
SUPERVISOR_PREP_SHA = "57bf84bdf102444aad209bf9c7fd5e62c1fc4f7bf584fa3fac8d0b75e71627ae"
SUPERVISOR_REVIEW = "experiments/logs/root-prism-free/f0-local41-batch-independent-source-review.json"
SUPERVISOR_REVIEW_SHA = "56c3f59565b6b211e4f659f3310f50676160b0631701e2addae323a0ab43bad4"
LIMITS = {
    "maximum_owned_search_wall_seconds": 180,
    "maximum_native_calls": 30,
    "maximum_new_covers_per_returned_point": 512,
    "maximum_added_covers": 29*512,
    "cold_owned_wall_seconds": 60,
    "threads": 1,
    "proposed_binary_rounding_tolerance": 1e-6,
}
OPTIONS = [
    ["output_flag", True], ["log_to_console", False], ["threads", 1],
    ["parallel", "off"], ["solver", "choose"], ["presolve", "on"],
    ["random_seed", 0], ["mip_rel_gap", 0.0], ["mip_abs_gap", 0.0],
    ["mip_feasibility_tolerance", 1e-9], ["primal_feasibility_tolerance", 1e-9],
    ["small_matrix_value", 1e-9],
]


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def save(path, value):
    temporary = path.with_suffix(path.suffix+".tmp")
    temporary.write_bytes(json.dumps(value, indent=2, allow_nan=False).encode()+b"\n")
    temporary.replace(path)


def save_new(path, value):
    assert not path.exists(), path
    save(path, value)


def bind(path, root=ROOT):
    return {"path": str(path.resolve().relative_to(root.resolve())), "sha256": sha(path.read_bytes())}


def save_gzip(path, value, root=ROOT):
    assert not path.exists(), path
    path.write_bytes(gzip.compress(canonical(value)+b"\n", mtime=0))
    return bind(path, root)


def source_bindings(root):
    assert sha(Path(exact.__file__).read_bytes()) == BUILDER_SHA
    assert sha((root/MODEL).read_bytes()) == MODEL_SHA
    for name, expected in ((SUPERVISOR, SUPERVISOR_SHA), (SUPERVISOR_PREP, SUPERVISOR_PREP_SHA),
                           (SUPERVISOR_REVIEW, SUPERVISOR_REVIEW_SHA)):
        assert sha((root/name).read_bytes()) == expected, name
    return {
        "driver": {"path": "experiments/workspace/"+Path(__file__).name, "sha256": sha(Path(__file__).read_bytes())},
        "exact_builder": {"path": "experiments/workspace/"+Path(exact.__file__).name, "sha256": BUILDER_SHA},
        "model": {"path": MODEL, "sha256": MODEL_SHA},
        "owned_child_supervisor": {"path": SUPERVISOR, "sha256": SUPERVISOR_SHA},
        "inherited_supervisor_controls": {"path": SUPERVISOR_PREP, "sha256": SUPERVISOR_PREP_SHA},
        "supervisor_review": {"path": SUPERVISOR_REVIEW, "sha256": SUPERVISOR_REVIEW_SHA},
    }


def runtime_binding():
    import highspy
    import highspy._core
    import numpy as np
    binary = Path(highspy._core.__file__)
    return {"highs_version": highspy.Highs().version(), "numpy_version": np.__version__,
            "highspy_core_path": str(binary), "highspy_core_sha256": sha(binary.read_bytes()),
            "python_executable": sys.executable, "python_version": sys.version}


def csr_arrays(rows):
    import numpy as np
    pointers, indices, values = [0], [], []
    for row in rows:
        terms = row["terms"]
        assert terms == sorted(terms) and len({a for a, c in terms}) == len(terms)
        for a, c in terms:
            assert type(a) is type(c) is int and c and abs(c) < 2**53
            indices.append(a)
            values.append(float(c))
        pointers.append(len(indices))
        assert type(row["lower"]) is type(row["upper"]) is int
        assert abs(row["lower"]) < 2**53 and abs(row["upper"]) < 2**53
    assert len(indices) < 2**31 and len(rows) < 2**31
    return (np.asarray(pointers, dtype=np.int32), np.asarray(indices, dtype=np.int32),
            np.asarray(values, dtype=np.float64),
            np.asarray([r["lower"] for r in rows], dtype=np.float64),
            np.asarray([r["upper"] for r in rows], dtype=np.float64))


def native_audit(h, rows, columns, costs=None):
    import highspy
    lp = h.getLp()
    assert lp.num_col_ == columns and lp.num_row_ == len(rows)
    assert list(map(int, lp.integrality_)) == [int(highspy.HighsVarType.kInteger)]*columns
    assert list(lp.col_lower_) == [0.0]*columns and list(lp.col_upper_) == [1.0]*columns
    assert list(lp.col_cost_) == list(costs or [0.0]*columns)
    assert lp.offset_ == 0.0 and lp.sense_ == highspy.ObjSense.kMinimize
    assert list(lp.row_lower_) == [float(r["lower"]) for r in rows]
    assert list(lp.row_upper_) == [float(r["upper"]) for r in rows]
    matrix = lp.a_matrix_
    recovered = [[] for _ in rows]
    starts, indices, values = matrix.start_, matrix.index_, matrix.value_
    if matrix.format_ == highspy.MatrixFormat.kRowwise:
        assert len(starts) == len(rows)+1
        for r in range(len(rows)):
            for k in range(starts[r], starts[r+1]):
                value = values[k]
                assert math.isfinite(value) and value == int(value)
                recovered[r].append([int(indices[k]), int(value)])
    else:
        assert matrix.format_ == highspy.MatrixFormat.kColwise and len(starts) == columns+1
        for a in range(columns):
            for k in range(starts[a], starts[a+1]):
                value = values[k]
                assert math.isfinite(value) and value == int(value)
                recovered[int(indices[k])].append([a, int(value)])
    assert [sorted(row) for row in recovered] == [r["terms"] for r in rows]
    return {"columns": columns, "binary_integer_columns": columns, "rows": len(rows),
            "nonzeros": len(values), "all_native_coefficients_bounds_costs_integrality_checked": True,
            "exact_rows_sha256": sha(canonical(rows)), "runtime_before_any_solve": float(h.getRunTime())}


def native_setup(rows, columns, log_path, costs=None):
    import highspy
    import numpy as np
    h = highspy.Highs()
    for name, value in OPTIONS+[["log_file", str(log_path)]]:
        assert h.setOptionValue(name, value) == highspy.HighsStatus.kOk, name
    pointers, indices, values, lower, upper = csr_arrays(rows)
    lp = highspy.HighsLp()
    lp.num_col_, lp.num_row_ = columns, len(rows)
    lp.col_cost_ = np.asarray(costs or [0.0]*columns, dtype=np.float64)
    lp.col_lower_ = np.zeros(columns, dtype=np.float64)
    lp.col_upper_ = np.ones(columns, dtype=np.float64)
    lp.row_lower_, lp.row_upper_ = lower, upper
    lp.integrality_ = [highspy.HighsVarType.kInteger]*columns
    lp.a_matrix_.format_ = highspy.MatrixFormat.kRowwise
    lp.a_matrix_.num_col_, lp.a_matrix_.num_row_ = columns, len(rows)
    lp.a_matrix_.start_, lp.a_matrix_.index_, lp.a_matrix_.value_ = pointers, indices, values
    assert h.passModel(lp) == highspy.HighsStatus.kOk
    return h, native_audit(h, rows, columns, costs)


def native_append(h, rows):
    import highspy
    pointers, indices, values, lower, upper = csr_arrays(rows)
    assert h.addRows(len(rows), lower, upper, len(values), pointers, indices, values) == highspy.HighsStatus.kOk


def decode_binary(values, kept, original_count):
    if len(values) != len(kept) or len(kept) != len(set(kept)):
        return None, "wrong dimension"
    point = [0]*original_count
    maximum_error = 0.0
    for a, value in zip(kept, values):
        if value is None or not math.isfinite(value):
            return None, "nonfinite coordinate"
        nearest = int(value >= 0.5)
        error = abs(value-nearest)
        maximum_error = max(maximum_error, error)
        if error > LIMITS["proposed_binary_rounding_tolerance"]:
            return None, "no integral proposal"
        point[a] = nearest
    return point, {"maximum_rounding_error": maximum_error, "rounding_is_not_acceptance": True}


def clean_number(value):
    if isinstance(value, int):
        return value
    number = float(value)
    return number if math.isfinite(number) else None


def controls(directory):
    import highspy
    directory.mkdir(parents=True, exist_ok=False)
    # Native integrality must matter: 2*x=1 has a real but no Boolean solution.
    impossible = [{"terms": [[0, 2]], "lower": 1, "upper": 1}]
    h, first = native_setup(impossible, 1, directory/"integer-infeasible.log")
    assert h.setOptionValue("time_limit", 2.0) == highspy.HighsStatus.kOk
    assert h.run() == highspy.HighsStatus.kOk
    assert h.getModelStatus() == highspy.HighsModelStatus.kInfeasible
    assert all(2*x != 1 for x in (0, 1))
    # A cover omitted from the initial matrix rejects the first optimum.
    rows = [{"terms": [[0, 1]], "lower": 1, "upper": 1},
            {"terms": [[1, 1], [2, 1]], "lower": 1, "upper": 1}]
    costs = [0.0, 1.0, 0.0]
    h, before = native_setup(rows, 3, directory/"cover-sequence.log", costs)
    assert h.setOptionValue("time_limit", 2.0) == highspy.HighsStatus.kOk
    assert h.run() == highspy.HighsStatus.kOk
    assert h.getModelStatus() == highspy.HighsModelStatus.kOptimal
    point, decoded = decode_binary(list(h.getSolution().col_value), [0, 1, 2], 3)
    assert point == [1, 0, 1] and point[0] > point[1]
    first_runtime = float(h.getRunTime())
    cover_row = {"terms": [[0, -1], [1, 1]], "lower": 0, "upper": 1}
    native_append(h, [cover_row])
    rows.append(cover_row)
    after = native_audit(h, rows, 3, costs)
    assert h.setOptionValue("time_limit", 2.0) == highspy.HighsStatus.kOk
    assert h.run() == highspy.HighsStatus.kOk
    assert h.getModelStatus() == highspy.HighsModelStatus.kOptimal
    point, decoded = decode_binary(list(h.getSolution().col_value), [0, 1, 2], 3)
    assert point == [1, 1, 0] and point[0] <= point[1]
    for row in rows:
        assert row["lower"] <= sum(c*point[a] for a, c in row["terms"]) <= row["upper"]
    assert decode_binary([0.5], [0], 1)[0] is None
    assert decode_binary([float("nan")], [0], 1)[0] is None
    assert decode_binary([1.1], [0], 1)[0] is None
    lifted, detail = decode_binary([1.0, 0.0], [1, 3], 5)
    assert lifted == [0, 1, 0, 0, 0]
    return {"tiny_native_calls": 3, "production_native_calls": 0,
            "binary_infeasible_control": first,
            "external_cover_rejection_then_native_append": True,
            "native_before_append": before, "native_after_append": after,
            "first_runtime": first_runtime, "second_runtime": float(h.getRunTime()),
            "fractional_nonfinite_outside_box_rejected": True,
            "removed_zero_coordinate_lift_checked": True,
            "owned_supervisor_controls_reused_without_repetition": True}


def preparation(preparation_path, root):
    document = json.loads(preparation_path.read_bytes())
    assert document["source_bindings"] == source_bindings(root)
    assert document["limits"] == LIMITS and document["options"] == OPTIONS
    assert document["runtime"] == runtime_binding()
    assert document["model_sha256"] == MODEL_SHA
    assert document["status"] == "PREPARED: binary search; no production call"
    return document


def prepare(directory, root):
    started = time.monotonic()
    directory.mkdir(parents=True, exist_ok=False)
    bindings = source_bindings(root)
    model, data = exact.load_model(root/MODEL, root)
    h, audit = native_setup(model["initial_rows"], exact.LIVE, directory/"native-preflight.log")
    assert h.getRunTime() == 0.0
    assert audit["nonzeros"] == 27515 and audit["rows"] == 2195
    runtime = runtime_binding()
    assert runtime["highs_version"] == "1.16.0"
    tiny = controls(directory/"tiny-controls")
    record = {
        "schema": "conway99.rook-face112-highs-binary-query-preparation.v1",
        "status": "PREPARED: binary search; no production call",
        "source_bindings": bindings, "model_sha256": MODEL_SHA,
        "runtime": runtime, "options": OPTIONS, "limits": LIMITS,
        "native_preflight": audit, "tiny_controls": tiny,
        "original_rows_checked_on_acceptance": 2618,
        "original_covers_checked_on_acceptance": 178533,
        "external_retained_cover_pool": 164044,
        "all1102_primary_variables_binary_and_untied": True,
        "initial_production_objective": "zero feasibility",
        "native_time_limit_each_call": "remaining owned wall time; parent hard deadline is authoritative",
        "selection_rule": "first512 violated unseen original cover IDs in increasing order",
        "only_exact_original_covers_can_be_appended": True,
        "integral_proposal_requires_full_original_integer_acceptance": True,
        "numerical_infeasibility_is_always_UNKNOWN": True,
        "partial_or_late_child_never_accepted": True,
        "no_automatic_dual_or_backend_retry": True,
        "inherited_supervisor_controls_repeated": False,
        "production_optimizer_calls": 0, "seconds": time.monotonic()-started,
    }
    save_new(directory/"preparation.json", record)
    print(json.dumps({k: v for k, v in record.items() if k not in ("source_bindings", "tiny_controls")}, indent=2))


def worker(preparation_path, directory, root, deadline):
    started = time.monotonic()
    assert 0 < deadline-started <= LIMITS["maximum_owned_search_wall_seconds"]
    result_path = directory/"child-result.json"
    result = {"status": "UNKNOWN_INITIALIZING", "preparation": bind(preparation_path, root),
              "source_bindings": source_bindings(root), "limits": LIMITS,
              "calls_started": 0, "completed_calls": 0, "iterations": [],
              "added_cover_ids": [], "exact_incidence_accepted": False,
              "case4_excluded": False, "whole_graph_problem_resolved": False}
    save(result_path, result)
    try:
        prepared = preparation(preparation_path, root)
        exact.checked_time(deadline)
        model, data = exact.load_model(root/MODEL, root, deadline)
        result["input_replay_seconds"] = time.monotonic()-started
        rows = list(model["initial_rows"])
        position = {a: j for j, a in enumerate(model["original_column_ids"])}
        pool = set(model["external_cover_pool"])
        active = set()
        import highspy
        h, audit = native_setup(rows, exact.LIVE, directory/"highs.log")
        result["initial_native_audit"] = audit
        result["native_initialization_seconds"] = time.monotonic()-started-result["input_replay_seconds"]
        for call in range(LIMITS["maximum_native_calls"]):
            remaining = deadline-time.monotonic()
            if remaining <= 0:
                result["status"] = "UNKNOWN_WALL_BUDGET"
                break
            assert h.setOptionValue("time_limit", remaining) == highspy.HighsStatus.kOk
            result["calls_started"] = call+1
            result["status"] = "UNKNOWN_NATIVE_CALL_ACTIVE"
            save(result_path, result)
            before = time.monotonic()
            runtime_before = float(h.getRunTime())
            run_status = h.run()
            call_seconds = time.monotonic()-before
            solution, info = h.getSolution(), h.getInfo()
            numeric = {
                "call_index": call, "active_rows": len(rows),
                "active_cover_ids": sorted(active), "time_limit_option": remaining,
                "run_status": str(run_status), "model_status": str(h.getModelStatus()),
                "solution_value_valid": bool(solution.value_valid),
                "column_values": [clean_number(v) for v in solution.col_value],
                "native_runtime_before": runtime_before, "native_runtime_after": float(h.getRunTime()),
                "native_wall_seconds": call_seconds,
                "info": {key: clean_number(getattr(info, key)) for key in (
                    "mip_node_count", "mip_gap", "mip_dual_bound", "objective_function_value",
                    "max_integrality_violation", "max_primal_infeasibility", "primal_solution_status")},
                "numerical_status_is_not_an_exclusion": True,
            }
            item = {"call_index": call, "native": save_gzip(directory/f"call{call:02d}-native.json.gz", numeric, root),
                    "scan": None, "appended_cover_ids": []}
            result["iterations"].append(item)
            result["completed_calls"] = len(result["iterations"])
            result["status"] = "UNKNOWN_NATIVE_PROPOSAL_SAVED"
            save(result_path, result)
            exact.checked_time(deadline)
            if not solution.value_valid:
                result["status"] = "UNKNOWN_NO_NATIVE_PRIMAL"
                break
            point, rounding = decode_binary(numeric["column_values"], model["original_column_ids"], exact.N)
            if point is None:
                result["status"], result["proposal_rejection"] = "UNKNOWN_NO_INTEGRAL_PROPOSAL", rounding
                break
            scan = exact.inspect_binary(point, data, deadline)
            scan["rounding"] = rounding
            scan["original1214_binary_coordinates"] = point
            item["scan"] = save_gzip(directory/f"call{call:02d}-exact-scan.json.gz", scan, root)
            save(result_path, result)
            if scan["row_violations"]:
                result["status"] = "UNKNOWN_INTEGRAL_PROPOSAL_FAILS_EXACT_NATIVE_ROWS"
                break
            violated = scan["cover_violations"]
            assert set(violated) <= pool
            if active.intersection(violated):
                result["status"] = "UNKNOWN_INTEGRAL_PROPOSAL_FAILS_ACTIVE_EXACT_COVERS"
                break
            if scan["accepted_exact_incidence"]:
                exact.checked_time(deadline)
                witness = {"status": "EXACT_BINARY_INCIDENCE_WITNESS",
                    "model_sha256": MODEL_SHA, "source_bindings": source_bindings(root),
                    "preparation": bind(preparation_path, root), "native": item["native"],
                    "exact_scan": item["scan"],
                    "original1214_binary_coordinates": point,
                    "selected_original_columns": scan["selected_columns"],
                    "full_graph_completion_claimed": False}
                result["witness"] = save_gzip(directory/"exact-incidence-witness.json.gz", witness, root)
                result["exact_incidence_accepted"] = True
                result["status"] = "EXACT_BINARY_INCIDENCE_WITNESS"
                break
            if call+1 == LIMITS["maximum_native_calls"]:
                result["status"] = "UNKNOWN_CALL_BUDGET_WITH_VIOLATED_COVERS"
                break
            exact.checked_time(deadline)
            selected = violated[:LIMITS["maximum_new_covers_per_returned_point"]]
            assert selected and not active.intersection(selected)
            assert len(active)+len(selected) <= LIMITS["maximum_added_covers"]
            additional = [exact.cover_row(data["registry"], i, position) for i in selected]
            native_append(h, additional)
            rows.extend(additional)
            active.update(selected)
            item["appended_cover_ids"] = selected
            item["post_append_native_audit"] = native_audit(h, rows, exact.LIVE)
            result["added_cover_ids"] = sorted(active)
            result["status"] = "UNKNOWN_EXACT_COVERS_APPENDED"
            save(result_path, result)
        else:
            result["status"] = "UNKNOWN_NATIVE_CALL_LIMIT"
    except TimeoutError as error:
        result["status"] = "UNKNOWN_WALL_BUDGET"
        result["timeout_message"] = str(error)
    except Exception as error:
        result["status"] = "ERROR_NO_OUTCOME_ACCEPTED"
        result["exact_incidence_accepted"] = False
        result["error_type"], result["error_message"] = type(error).__name__, str(error)
        raise
    finally:
        result["elapsed_seconds"] = time.monotonic()-started
        result["peak_rss_kib"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        save(result_path, result)


def import_supervisor(root):
    assert sha((root/SUPERVISOR).read_bytes()) == SUPERVISOR_SHA
    spec = importlib.util.spec_from_file_location("frozen_owned_supervisor", root/SUPERVISOR)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run(preparation_path, directory, root):
    source_bindings(root)
    # Only small source/model identity checks precede the owned process clock.
    prepared = json.loads(preparation_path.read_bytes())
    assert prepared["source_bindings"] == source_bindings(root) and prepared["limits"] == LIMITS
    supervisor = import_supervisor(root)
    directory.mkdir(parents=True, exist_ok=False)
    result = {"status": "UNKNOWN_BEFORE_CHILD", "preparation": bind(preparation_path, root),
              "source_bindings": source_bindings(root), "limits": LIMITS,
              "exact_incidence_accepted": False, "case4_excluded": False,
              "whole_graph_problem_resolved": False}
    save(directory/"result.json", result)
    started = time.monotonic()
    deadline = started+LIMITS["maximum_owned_search_wall_seconds"]
    command = [sys.executable, str(Path(__file__).resolve()), "worker", "--root", str(root),
               "--preparation", str(preparation_path.resolve()), "--directory", str(directory.resolve()),
               "--deadline", repr(deadline)]
    supervised = supervisor.supervise(command, directory, deadline)
    result["supervision"] = supervised
    child_path = directory/"child-result.json"
    if child_path.exists():
        result["child_result"] = bind(child_path, root)
        child = json.loads(child_path.read_bytes())
        result["calls_started"] = child["calls_started"]
        result["completed_calls"] = child["completed_calls"]
        if supervised["status"] == "CHILD_EXITED":
            result["status"] = child["status"]
            result["exact_incidence_accepted"] = child["exact_incidence_accepted"]
            if child["exact_incidence_accepted"]:
                assert child["status"] == "EXACT_BINARY_INCIDENCE_WITNESS"
                result["witness"] = child["witness"]
        else:
            result["status"] = supervised["status"]
    else:
        result["status"] = supervised["status"]
    result["elapsed_seconds"] = time.monotonic()-started
    save(directory/"result.json", result)
    print(json.dumps(result, indent=2))


def read_artifact(root, binding):
    raw = (root/binding["path"]).read_bytes()
    assert sha(raw) == binding["sha256"]
    return json.loads(gzip.decompress(raw) if binding["path"].endswith(".gz") else raw)


def cold_worker(preparation_path, result_path, directory, root, deadline):
    started = time.monotonic()
    assert 0 < deadline-started <= LIMITS["cold_owned_wall_seconds"]
    prepared = preparation(preparation_path, root)
    model, data = exact.load_model(root/MODEL, root, deadline)
    result = json.loads(result_path.read_bytes())
    assert result["source_bindings"] == source_bindings(root) and result["limits"] == LIMITS
    assert result["preparation"] == bind(preparation_path, root) and not result["case4_excluded"]
    records, active, rows = [], set(), list(model["initial_rows"])
    position = {a: j for j, a in enumerate(model["original_column_ids"])}
    if "child_result" in result:
        child = read_artifact(root, result["child_result"])
        assert child["preparation"] == result["preparation"]
        assert child["source_bindings"] == result["source_bindings"]
        assert 0 <= child["completed_calls"] <= child["calls_started"] <= LIMITS["maximum_native_calls"]
        assert child["completed_calls"] == len(child["iterations"])
        for i, item in enumerate(child["iterations"]):
            exact.checked_time(deadline)
            numeric = read_artifact(root, item["native"])
            assert item["call_index"] == numeric["call_index"] == i
            assert numeric["active_rows"] == len(rows) and numeric["active_cover_ids"] == sorted(active)
            checked_scan = None
            if item["scan"] is not None:
                saved = read_artifact(root, item["scan"])
                point, rounding = decode_binary(numeric["column_values"], model["original_column_ids"], exact.N)
                assert point is not None and saved["original1214_binary_coordinates"] == point
                checked_scan = exact.inspect_binary(point, data, deadline, literal_cover_check=True)
                assert saved == dict(checked_scan, rounding=rounding, original1214_binary_coordinates=point)
                added = item["appended_cover_ids"]
                if added:
                    assert not checked_scan["row_violations"] and not active.intersection(checked_scan["cover_violations"])
                    assert added == checked_scan["cover_violations"][:LIMITS["maximum_new_covers_per_returned_point"]]
                    assert i+1 < LIMITS["maximum_native_calls"]
                    active.update(added)
                    rows.extend(exact.cover_row(data["registry"], a, position) for a in added)
                    audit = item["post_append_native_audit"]
                    assert audit["exact_rows_sha256"] == sha(canonical(rows))
                    assert audit["binary_integer_columns"] == exact.LIVE and audit["rows"] == len(rows)
                assert len(active) <= LIMITS["maximum_added_covers"]
            else:
                assert not item["appended_cover_ids"]
            records.append({"call_index": i, "full_exact_scan_replayed": checked_scan is not None,
                            "appended_original_covers_checked": len(item["appended_cover_ids"])})
        assert child["added_cover_ids"] == sorted(active)
        if result["exact_incidence_accepted"]:
            assert result["supervision"]["status"] == "CHILD_EXITED"
            assert result["status"] == child["status"] == "EXACT_BINARY_INCIDENCE_WITNESS"
            assert child["exact_incidence_accepted"] and result["witness"] == child["witness"]
            witness = read_artifact(root, result["witness"])
            assert witness["model_sha256"] == MODEL_SHA
            assert witness["source_bindings"] == source_bindings(root)
            accepted = exact.inspect_binary(witness["original1214_binary_coordinates"], data,
                                             deadline, literal_cover_check=True)
            assert accepted["accepted_exact_incidence"]
            assert witness["selected_original_columns"] == accepted["selected_columns"]
    else:
        assert not result["exact_incidence_accepted"]
    exact.checked_time(deadline)
    report = {"status": "PASS: cold original-row and literal-cover replay",
              "source_bindings": source_bindings(root), "result": bind(result_path, root),
              "preparation": bind(preparation_path, root), "completed_calls_replayed": records,
              "exact_incidence_accepted": result["exact_incidence_accepted"],
              "all2618_original_integer_rows_checked_per_saved_point": True,
              "all178533_original_covers_checked_per_saved_point": True,
              "new_optimizer_calls": 0, "case4_excluded": False,
              "full_graph_completion_claimed": False, "seconds": time.monotonic()-started}
    save_new(directory/"cold-report.json", report)


def cold(preparation_path, result_path, directory, root):
    source_bindings(root)
    supervisor = import_supervisor(root)
    directory.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    deadline = started+LIMITS["cold_owned_wall_seconds"]
    command = [sys.executable, str(Path(__file__).resolve()), "cold-worker", "--root", str(root),
               "--preparation", str(preparation_path.resolve()), "--result", str(result_path.resolve()),
               "--directory", str(directory.resolve()), "--deadline", repr(deadline)]
    supervised = supervisor.supervise(command, directory, deadline)
    record = {"status": supervised["status"], "supervision": supervised,
              "result": bind(result_path, root), "new_optimizer_calls": 0,
              "cold_replay_complete": False, "case4_excluded": False}
    if supervised["status"] == "CHILD_EXITED":
        report = directory/"cold-report.json"
        data = json.loads(report.read_bytes())
        assert data["status"].startswith("PASS")
        record["status"] = data["status"]
        record["cold_replay_complete"] = True
        record["report"] = bind(report, root)
    record["seconds"] = time.monotonic()-started
    save_new(directory/"result.json", record)
    print(json.dumps(record, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "run", "worker", "cold", "cold-worker"))
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--preparation", type=Path)
    parser.add_argument("--result", type=Path)
    parser.add_argument("--deadline", type=float)
    args = parser.parse_args()
    if args.mode == "prepare":
        prepare(args.directory, args.root)
    elif args.mode == "run":
        run(args.preparation, args.directory, args.root)
    elif args.mode == "worker":
        worker(args.preparation, args.directory, args.root, args.deadline)
    elif args.mode == "cold":
        cold(args.preparation, args.result, args.directory, args.root)
    else:
        cold_worker(args.preparation, args.result, args.directory, args.root, args.deadline)
