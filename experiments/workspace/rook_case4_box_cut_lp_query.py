"""One bounded complete-pool LP round with five parity cuts and one box cut.

The seed point satisfies the first five appended rows and violates the new
11-term capacity. Preparation and native transport do not run a solver.
Production preserves numerical records, then uses one exact stage and one
separate cold stage. No parity scan or second LP round is exposed.
"""
import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

import rook_case4_box_cut_lp_adapter as adapter

ROOT, LOG = adapter.ROOT, adapter.LOGS
exact, proof = adapter.exact, adapter.box_proof
save, read, ref, checked = adapter.save, adapter.read_record, adapter.record_ref, adapter.checked_ref
sha, canonical = exact.sha, exact.canonical
SOURCES = {
    "adapter": ("experiments/workspace/rook_case4_box_cut_lp_adapter.py", "7f574542d4fef61915337696bd6061d98ee4bdc3eb57709b7a698b3f4cb1ed07"),
    "proof": ("experiments/workspace/rook_case4_box_cut_lp_proof.py", "091946b8444aa1c3b49f2955b076e00f7241a96926a9b9d2a4afb210fe4067c3"),
    "reuse_source": ("experiments/workspace/rook_case4_box_cut_lp_adapter_reuse.py", "6d09bcd0b12fe937d8aa0f108b0a4c9747565bef6382ea8b5cd3b60688f1fae3"),
}
REUSE = (LOG + "rook-case4-box-cut-lp-adapter-reuse.json", "0aa11f61bdaab6976cdbdc2d01b524a2462239645a50c7ea8a75e726fde96f1d")
LIMITS = {"LP_rounds": 1, "native_calls": 30, "cumulative_native_seconds": 120,
          "numerical_phase_seconds": 180, "exact_seconds": 60, "cold_seconds": 60,
          "declared_production_child_seconds": 300, "production_owner_seconds": 360,
          "preparation_seconds": 60, "preflight_seconds": 60, "preparation_owner_seconds": 90,
          "maximum_basis_dimension": 512, "maximum_exact_output_bits": 4096,
          "threads": 1, "automatic_retries": 0}
ROWS, NONZEROS, OLD_ROWS, OLD_NNZ = 167121, 10769766, 167120, 10769755


def bindings():
    for name, (path, digest) in SOURCES.items():
        assert sha((ROOT / path).read_bytes()) == digest, name
    assert Path(adapter.__file__).resolve() == ROOT / SOURCES["adapter"][0]
    assert Path(proof.__file__).resolve() == ROOT / SOURCES["proof"][0]
    raw = (ROOT / REUSE[0]).read_bytes()
    assert sha(raw) == REUSE[1]
    ledger = json.loads(raw)
    assert ledger["status"] == "PASS_COMPLETE_SOURCE_EXTRACTION_AND_EXPLICIT_TWO_FUNCTION_DELTA"
    assert ledger["adapter"]["sha256"] == SOURCES["adapter"][1] and ledger["identical_functions"] == 23
    return {"controller_sha256": sha(Path(__file__).read_bytes()), "sources": {k: list(v) for k, v in SOURCES.items()},
            "reuse_control": list(REUSE), "kernel_source_bindings": adapter.source_bindings(),
            "proof_bindings": proof.bindings()}


def seed():
    registry = proof.frozen_registry()
    point = proof.source_point()
    cold = checked(point["cold"])
    assert cold["status"].startswith("PASS:") and cold["exact_point_replayed"]
    state = checked(cold["state"])
    numeric = checked(state["numerical_result"])
    assert state["cuts"] == registry[:5]
    assert numeric["complete"] and numeric["registry_sha256"] == sha(canonical(registry[:5]))
    assert numeric["matrix_binding"] == checked(point["candidate"])["matrix_binding"]
    carried = numeric["carried_covers_after"]
    assert carried == sorted(set(carried))
    assert all(adapter.NATIVE_ROWS <= r < adapter.COVER_END for r in carried)
    return registry, point, carried, state["numerical_result"]


def definition():
    registry, point, carried, numeric = seed()
    assert adapter.SELECTORS == 1102 and adapter.VARIABLES == 1103
    assert adapter.PREFIX_ROWS == 167115 and adapter.PREFIX_NNZ == 10769496
    for key, expected in (("cumulative_native_seconds", 120), ("native_calls_per_round", 30),
                          ("numerical_phase_seconds", 180), ("exact_seconds", 60), ("exact_cold_seconds", 60),
                          ("maximum_dynamic_exact_dimension", 512), ("maximum_exact_output_bits", 4096)):
        assert adapter.LIMITS[key] == expected
    assert len(registry) == 6 and "proof_kind" not in registry[4] and registry[5]["proof_kind"] == proof.PROOF_KIND
    return {"bindings": bindings(), "limits": LIMITS, "variables": 1103, "selector_variables": 1102,
            "global_zero_premises": 112, "immutable_prefix_rows": OLD_ROWS, "immutable_prefix_nonzeros": OLD_NNZ,
            "extended_rows": ROWS, "nonzeros": NONZEROS, "new_row_id": OLD_ROWS,
            "new_original_capacity_support": proof.SUPPORT, "new_range": [0, 1],
            "complete_retained_cover_pool": [adapter.NATIVE_ROWS, adapter.COVER_END],
            "complete_retained_cover_count": adapter.COVER_END - adapter.NATIVE_ROWS,
            "registry_sha256": sha(canonical(registry)), "initial_point": point,
            "initial_point_accepted_cut_count": 5, "target_cut_count": 6,
            "initial_carried_covers": carried, "carried_covers_source": numeric,
            "no_original_row_or_column_removed": True, "only_one_new_capacity_appended": True,
            "new_cut_has_distinct_box_cover_proof_kind": True,
            "full_original_coordinate_acceptance_retained": True,
            "basis_aliases_and_fixed_coordinates_are_proposals_only": True,
            "parity_or_hull_separation_calls": 0}


def prepare(output):
    assert not output.exists()
    started = time.monotonic()
    value = definition()
    registry, point, carried, numeric = seed()
    data = adapter.with_point(adapter.domain(started + 60), point)
    adapter.validate_registry(data, registry, started + 60)
    nums, den = adapter.point_data(point)
    values = []
    for i, entry in enumerate(registry):
        row = entry["certificate"]["inequality"]
        activity = sum(c * nums[a] for a, c in row["terms"])
        excess = activity - row["upper"] * den
        assert (excess <= 0) if i < 5 else (excess == 37621464 > 0)
        values.append({"registry_index": i, "terms": len(row["terms"]), "upper": row["upper"],
                       "value_numerator": str(activity), "excess_numerator": str(excess)})
    assert time.monotonic() - started <= 60
    report = {"status": "PREPARED_ONE_SIX_CUT_LP_ROUND_NO_OPTIMIZER", "definition": value,
              "definition_sha256": sha(canonical(value)), "registry": registry,
              "source_point_row_evaluation": values, "point_denominator": str(den),
              "all191_box_capacity_maxima_replayed": True, "three_Gram_identity_replayed": True,
              "no_native_model_or_full_matrix_constructed": True, "optimizer_calls": 0,
              "seconds": time.monotonic() - started}
    save(output, report)
    return report


def checked_preparation(path):
    result = read(path)
    value = definition()
    assert result["status"] == "PREPARED_ONE_SIX_CUT_LP_ROUND_NO_OPTIMIZER"
    assert result["definition"] == value and result["definition_sha256"] == sha(canonical(value))
    assert result["registry"] == seed()[0] and result["optimizer_calls"] == 0
    return result


def preflight(preparation, output):
    import highspy
    import numpy as np
    from scipy.sparse import csr_matrix, csc_matrix
    assert not output.exists()
    started = time.monotonic()
    prep = checked_preparation(preparation)
    deadline = started + 60
    data = adapter.domain(deadline)
    old, arrays, pool = adapter.load_matrix(data, prep["registry"], deadline)
    assert len(arrays["row_lower"]) == ROWS and len(arrays["coefficients"]) == NONZEROS
    assert pool == list(range(adapter.NATIVE_ROWS, adapter.COVER_END))
    original_point = checked(prep["definition"]["initial_point"]["candidate"])
    previous = original_point["matrix_binding"]
    for name, item in previous.items():
        size = item["shape"][0]
        prefix = arrays[name][:size]
        assert str(prefix.dtype) == item["dtype"] and list(prefix.shape) == item["shape"]
        assert sha(prefix.tobytes(order="C")) == item["sha256"], ("immutable167120-row prefix", name)
    assert exact.row_terms(arrays, OLD_ROWS) == [[data["kept"].index(a), 1] for a in proof.SUPPORT]
    assert int(arrays["row_lower"][OLD_ROWS]) == 0 and int(arrays["row_upper"][OLD_ROWS]) == 1
    rows = adapter.initial_rows(6, prep["definition"]["initial_carried_covers"])
    assert len(rows) == len(set(rows)) and OLD_ROWS in rows and len(rows) == 3077
    matrix = adapter.float_matrix(arrays)
    h = highspy.Highs()
    for name, value in old.OPTIONS:
        assert h.setOptionValue(name, value) == highspy.HighsStatus.kOk
    old.set_model(h, matrix, arrays, rows, 1103)
    native = h.getLp()
    assert native.num_col_ == 1103 and native.num_row_ == len(rows)
    assert list(native.col_lower_) == [0.0] * 1103 and list(native.col_upper_) == [1.0] * 1103
    assert list(native.col_cost_) == [0.0] * 1102 + [-1.0]
    assert np.array_equal(np.asarray(native.row_lower_), arrays["row_lower"][rows])
    assert np.array_equal(np.asarray(native.row_upper_), arrays["row_upper"][rows])
    a = native.a_matrix_
    constructor = csr_matrix if a.format_ == highspy.MatrixFormat.kRowwise else csc_matrix
    assert a.format_ in (highspy.MatrixFormat.kRowwise, highspy.MatrixFormat.kColwise)
    actual = constructor((a.value_, a.index_, a.start_), shape=(len(rows), 1103)).tocsr()
    expected = matrix[np.asarray(rows, dtype=np.int64)].tocsr()
    difference = actual - expected
    difference.eliminate_zeros()
    assert difference.nnz == 0 and actual.nnz == expected.nnz
    runtime = old.runtime_binding()
    assert runtime == checked(seed()[3])["runtime_binding"]
    h.clear()
    exact.tick(deadline)
    report = {"status": "PASS_CACHED_PREFIX_AND_SIX_CUT_NATIVE_TRANSPORT_NO_SOLVE",
              "preparation": ref(preparation), "bindings": bindings(), "source_bindings": adapter.source_bindings(),
              "definition_sha256": prep["definition_sha256"], "matrix_binding": exact.matrix_binding(arrays),
              "rows": ROWS, "nonzeros": NONZEROS, "variables": 1103, "initial_native_rows": len(rows),
              "initial_native_nonzeros": int(expected.nnz), "every_initial_native_coefficient_and_bound_checked": True,
              "all167120_old_rows_byte_identical": True, "unchanged_cover_pool_size": len(pool),
              "appended_original_row": prep["registry"][-1]["certificate"]["inequality"],
              "runtime_binding": runtime, "optimizer_calls": 0, "native_model_transports": 1,
              "original_cover_supports_reconstructed": False, "seconds": time.monotonic() - started}
    save(output, report)
    return report


def checked_flight(preparation, flight_path):
    prep = checked_preparation(preparation)
    flight = read(flight_path)
    assert flight["status"] == "PASS_CACHED_PREFIX_AND_SIX_CUT_NATIVE_TRANSPORT_NO_SOLVE"
    assert flight["preparation"] == ref(preparation) and flight["bindings"] == bindings()
    assert flight["source_bindings"] == adapter.source_bindings()
    assert flight["definition_sha256"] == prep["definition_sha256"] and flight["optimizer_calls"] == 0
    assert flight["rows"] == ROWS and flight["nonzeros"] == NONZEROS
    return prep, flight


def state_payload(preparation, flight_path):
    prep, flight = checked_flight(preparation, flight_path)
    state = adapter.state_payload(prep["definition"]["initial_point"], prep["registry"], 0,
                                  prep["definition"]["initial_carried_covers"], 0)
    state["native_preflight"] = ref(flight_path)
    state["box_cut_context"] = {"bindings": bindings(), "limits": LIMITS,
                                "preparation": ref(preparation), "preflight": ref(flight_path)}
    return state


def check_envelope(path):
    state = read(path)
    context = state["box_cut_context"]
    assert context["bindings"] == bindings() and context["limits"] == LIMITS
    prep, flight = checked_flight(ROOT / context["preparation"]["path"], ROOT / context["preflight"]["path"])
    assert ref(ROOT / context["preparation"]["path"]) == context["preparation"]
    assert ref(ROOT / context["preflight"]["path"]) == context["preflight"]
    assert state["source_bindings"] == adapter.source_bindings() and state["limits"] == adapter.LIMITS
    assert state["cuts"] == prep["registry"] and state["point"] == prep["definition"]["initial_point"]
    assert state["native_seconds_before"] == 0 and state["carried_covers"] == prep["definition"]["initial_carried_covers"]
    assert state["native_preflight"] == context["preflight"]
    return state


def owned_stage(mode, state, directory, seconds):
    directory.mkdir(parents=True, exist_ok=True)
    label, started = mode.removeprefix("_"), time.monotonic()
    with (directory / (label + ".stdout.log")).open("xb") as out, (directory / (label + ".stderr.log")).open("xb") as err:
        try:
            done = subprocess.run([sys.executable, str(Path(__file__).resolve()), mode,
                                   "--state", str(state.resolve()), "--directory", str(directory.resolve())],
                                  stdout=out, stderr=err, timeout=seconds, check=False)
            result = {"exit_code": done.returncode, "hard_timeout": False, "child_reaped": True}
        except subprocess.TimeoutExpired:
            result = {"exit_code": None, "hard_timeout": True, "child_reaped": True}
    result.update(mode=mode, state=ref(state), hard_seconds=seconds, seconds=time.monotonic() - started,
                  artifacts=[ref(p) for p in sorted(directory.iterdir()) if p.is_file()])
    return result


def stage_ok(stage):
    return not stage["hard_timeout"] and stage["exit_code"] == 0 and stage["child_reaped"]


def controller(preparation, flight_path, directory):
    started = time.monotonic()
    prep, flight = checked_flight(preparation, flight_path)
    result = {"status": "RUNNING", "bindings": bindings(), "limits": LIMITS,
              "preparation": ref(preparation), "preflight": ref(flight_path), "registry": prep["registry"],
              "stages": [], "LP_rounds": 0, "native_calls": 0, "native_seconds": 0.0,
              "latest_exact_point": prep["definition"]["initial_point"], "latest_point_accepted_cuts": 5,
              "exact_zero_face_found": False, "case4_exclusion_verified": False, "whole_graph_problem_resolved": False}
    target = directory / "result.json"
    save(target, result)
    try:
        state = state_payload(preparation, flight_path)
        state_path = directory / "state-numeric.json"
        save(state_path, state)
        numeric_dir = directory / "numeric"
        stage = owned_stage("_numeric", state_path, numeric_dir, 180)
        result["stages"].append(stage); result["LP_rounds"] = 1
        if (numeric_dir / "result.json").exists():
            numeric = read(numeric_dir / "result.json")
            result["native_calls"], result["native_seconds"] = numeric["native_calls"], numeric["native_seconds"]
        else:
            numeric = None
        assert result["native_calls"] <= 30
        save(target, result)
        if not stage_ok(stage) or numeric is None or not numeric["complete"] or not numeric["iterations"]:
            result["status"] = "UNRESOLVED_NUMERICAL_STAGE"; return result
        exact_state = dict(state, numerical_result=ref(numeric_dir / "result.json"))
        exact_path = directory / "state-exact.json"
        save(exact_path, exact_state)
        exact_dir = directory / "exact"
        stage = owned_stage("_exact", exact_path, exact_dir, 60)
        result["stages"].append(stage); save(target, result)
        if not stage_ok(stage) or not (exact_dir / "result.json").exists():
            result["status"] = "UNRESOLVED_EXACT_STAGE"; return result
        outcome = read(exact_dir / "result.json")
        stage = owned_stage("_exact_cold", exact_path, exact_dir, 60)
        result["stages"].append(stage); save(target, result)
        if not stage_ok(stage) or not (exact_dir / "cold.json").exists():
            result["status"] = "UNRESOLVED_COLD_STAGE"; return result
        cold = read(exact_dir / "cold.json")
        assert cold["status"].startswith("PASS:") and cold["result"] == ref(exact_dir / "result.json")
        if outcome["exact_certificate_found"]:
            assert cold["exact_certificate_replayed"]
            result["exact_certificate"] = outcome["certificate"]
            result["exact_certificate_cold"] = ref(exact_dir / "cold.json")
            result["case4_exclusion_verified"] = cold["kind"] == "exact_infeasibility"
            result["exact_zero_face_found"] = cold["kind"] == "exact_zero_face"
            result["status"] = "EXACT_CASE4_RELAXATION_INFEASIBLE" if result["case4_exclusion_verified"] else "EXACT_NEW_ZERO_FACE"
        elif outcome["exact_point_found"]:
            assert cold["exact_point_replayed"] and cold["full_face_rows_checked"] == ROWS
            result["latest_exact_point"] = {"candidate": outcome["candidate"], "cold": ref(exact_dir / "cold.json")}
            result["latest_point_accepted_cuts"] = 6
            result["status"] = "EXACT_SIX_CUT_POSITIVE_SELECTOR_POINT"
        else:
            result["status"] = "UNRESOLVED_NO_EXACT_OUTCOME"
    except Exception as error:
        result.update(status="UNRESOLVED_CONTROLLER_ERROR", error_type=type(error).__name__, reason=str(error))
    finally:
        result["seconds"] = time.monotonic() - started
        save(target, result)
    return result


def run(preparation, flight_path, directory):
    assert not directory.exists()
    directory.mkdir(parents=True)
    started, timeout = time.monotonic(), False
    with (directory / "controller.stdout.log").open("xb") as out, (directory / "controller.stderr.log").open("xb") as err:
        child = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), "_controller",
                                  "--preparation", str(preparation.resolve()), "--preflight", str(flight_path.resolve()),
                                  "--directory", str(directory.resolve())], stdout=out, stderr=err, start_new_session=True)
        try:
            code = child.wait(timeout=360)
        except subprocess.TimeoutExpired:
            timeout = True; os.killpg(child.pid, signal.SIGKILL); code = child.wait()
        except BaseException:
            if child.poll() is None:
                os.killpg(child.pid, signal.SIGKILL)
            child.wait(); raise
    report = {"status": "OWNED_SIX_CUT_ROUND_COMPLETE" if code == 0 and not timeout else "UNKNOWN_OWNER_FAILURE",
              "bindings": bindings(), "preparation": ref(preparation), "preflight": ref(flight_path),
              "exit_code": code, "hard_timeout": timeout, "child_reaped": True, "hard_seconds": 360,
              "automatic_retries": 0, "seconds": time.monotonic() - started}
    if (directory / "result.json").exists():
        report["result"] = ref(directory / "result.json")
    save(directory / "supervisor.json", report)
    return report


def verify(preparation, flight_path, directory, output):
    assert not output.exists()
    checked_flight(preparation, flight_path)
    owner = read(directory / "supervisor.json")
    assert owner["bindings"] == bindings() and owner["preparation"] == ref(preparation)
    assert owner["preflight"] == ref(flight_path) and owner["hard_seconds"] == 360 and owner["child_reaped"]
    count = 0
    if "result" in owner:
        result = checked(owner["result"])
        assert result["bindings"] == bindings() and result["limits"] == LIMITS
        assert result["registry"] == proof.frozen_registry()
        assert result["LP_rounds"] <= 1 and result["native_calls"] <= 30
        modes = [s["mode"] for s in result["stages"]]
        assert modes == ["_numeric", "_exact", "_exact_cold"][:len(modes)]
        for stage in result["stages"]:
            assert stage["hard_seconds"] == {"_numeric": 180, "_exact": 60, "_exact_cold": 60}[stage["mode"]]
            assert ref(ROOT / stage["state"]["path"]) == stage["state"]
            check_envelope(ROOT / stage["state"]["path"])
            for item in stage["artifacts"]:
                assert sha((ROOT / item["path"]).read_bytes()) == item["sha256"]
                count += 1
        if result["latest_point_accepted_cuts"] == 6:
            cold = checked(result["latest_exact_point"]["cold"])
            point = checked(result["latest_exact_point"]["candidate"])
            assert cold["exact_point_replayed"] and cold["full_face_rows_checked"] == ROWS
            assert cold["candidate_sha256"] == result["latest_exact_point"]["candidate"]["sha256"]
            assert point["registry_sha256"] == sha(canonical(result["registry"]))
        if result["case4_exclusion_verified"] or result["exact_zero_face_found"]:
            cold = checked(result["exact_certificate_cold"])
            assert cold["exact_certificate_replayed"]
            assert result["case4_exclusion_verified"] == (cold["kind"] == "exact_infeasibility")
            assert result["exact_zero_face_found"] == (cold["kind"] == "exact_zero_face")
    report = {"status": "PASS_SIX_CUT_TERMINAL_BINDINGS", "bindings": bindings(),
              "supervisor": ref(directory / "supervisor.json"), "stage_artifacts_bound": count,
              "optimizer_or_exact_solve_or_full_inspection_repeated": False}
    save(output, report)
    return report


def main():
    assert not sys.flags.optimize
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "preflight", "run", "verify", "_controller", "_numeric", "_exact", "_exact_cold"))
    for name in ("preparation", "preflight", "state", "directory", "output"):
        parser.add_argument("--" + name, type=Path)
    args = parser.parse_args()
    if args.mode == "prepare": result = prepare(args.output)
    elif args.mode == "preflight": result = preflight(args.preparation, args.output)
    elif args.mode == "run": result = run(args.preparation, args.preflight, args.directory)
    elif args.mode == "verify": result = verify(args.preparation, args.preflight, args.directory, args.output)
    elif args.mode == "_controller": result = controller(args.preparation, args.preflight, args.directory)
    else:
        check_envelope(args.state)
        result = getattr(adapter, {"_numeric": "numeric_stage", "_exact": "exact_stage", "_exact_cold": "exact_cold"}[args.mode])(args.state, args.directory)
    print(json.dumps({"status": result["status"], "seconds": result.get("seconds")}), flush=True)


if __name__ == "__main__":
    main()
