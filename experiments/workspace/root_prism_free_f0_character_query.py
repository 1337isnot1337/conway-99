"""One owned, 180-second CP-SAT count query; infeasibility is unproved.

The deadline includes child imports, public model construction, serialization,
the single solve call, and exact acceptance. No model or source is modified.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
LOGS = ROOT / "experiments/logs/root-prism-free"
SOURCES = {
    "model": ("root_prism_free_f0_character_cpsat.py", "879cdb9be48f9377dd6bccd078f26a568d12467385e9ecb1d5b260cc56ff64e7"),
    "profile": ("root_prism_free_f0_population_profile_cpsat.py", "a5b4485f4f30cdcb640d7cb63a5d4b1df4828e8f092f164fdad5a4a21260a67b"),
    "products": ("root_prism_free_f0_population_products_cpsat.py", "528f480b08adc5f1040807eec3eb96a75a8ea755eee28aec234f9d660034ff42"),
    "mathematics": ("root_prism_free_f0_population_products.py", "147ad92071ced273139993b09633c298b7a4a8ed9298e68103f970a8f01b7a66"),
    "supervisor": ("root_prism_free_f0_local_neighbors_batch.py", "b8e5323f92fa105ff2c0ed5b1667ac25d7c92f85f8cac45b170ddc56208f8278"),
}
INPUTS = {
    "model_preparation": ("f0-character-cpsat01/report.json", "e15c4bfcf7adaabb60258e3cffa8046eb0cd97843ae8787a24b356011d7b8a5f"),
    "model_cold": ("f0-character-cpsat01-cold/report.json", "fd86705f404e899869234d67916c2178d77acfb9c2b847571fb897cc5f785e18"),
    "coordinator_model_review": ("f0-character-cpsat-root-source-review.json", "46712ba2491fd0066e8ea79d0ebba094cfd18b7a8be069c966e73bbf85f0402a"),
    "model_archive": ("f0-character-cpsat01/model.pb.gz", "81acda719e5d7a65ccfeb95bcd956785ee9283d60630aed2f8933599933f3f57"),
}
MODEL_SHA = "5b43e3c026dbe71fcc8d072aa1790b80f7a81312e7b1ebf36a37612b2f726eeb"
CP_MODEL_SHA = "b5f2a3ae5c418d11af23cb77a766fa10103c8bb71703dafa1ecad74823603f25"
SECONDS = 180
FINALIZATION_RESERVE = 8


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def save(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(canonical(value) + b"\n")
    temporary.replace(path)


def load_source(key):
    name, expected = SOURCES[key]
    path = ROOT / "experiments/workspace" / name
    assert sha(path.read_bytes()) == expected
    spec = importlib.util.spec_from_file_location("frozen_character_query_" + key, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def configuration():
    sources = {}
    for key, (name, expected) in SOURCES.items():
        path = ROOT / "experiments/workspace" / name
        assert sha(path.read_bytes()) == expected
        sources[key] = {"path": str(path.relative_to(ROOT)), "sha256": expected}
    inputs, records = {}, {}
    for key, (name, expected) in INPUTS.items():
        path = LOGS / name
        raw = path.read_bytes()
        assert sha(raw) == expected
        inputs[key] = {"path": str(path.relative_to(ROOT)), "sha256": expected}
        if key != "model_archive":
            records[key] = json.loads(raw)
            assert records[key]["status"].startswith("PASS")
    assert records["model_preparation"]["source_sha256"] == SOURCES["model"][1]
    assert records["model_preparation"]["raw_proto_sha256"] == records["model_cold"]["raw_proto_sha256"] == MODEL_SHA
    assert records["model_preparation"]["raw_proto_bytes"] == 12498481
    return {"schema": "conway99.f0-character-count-query.v1", "runner_source_sha256": sha(Path(__file__).read_bytes()),
            "sources": sources, "inputs": inputs, "model_proto_sha256": MODEL_SHA,
            "native_variables": 18444, "native_constraints": 34436,
            "native_linear_rows": 31064, "native_products": 3288, "native_tables": 84,
            "ortools_version": "9.15.6755", "installed_cp_model_source_sha256": CP_MODEL_SHA,
            "maximum_owned_child_seconds": SECONDS, "finalization_reserve_seconds": FINALIZATION_RESERVE,
            "maximum_production_solve_calls": 1, "num_search_workers": 1, "random_seed": 0,
            "all_imports_build_serialization_solve_acceptance_in_child_deadline": True,
            "native_model_built_with_public_constructors": True,
            "native_model_hash_checked_before_solve": True, "late_or_failed_child_never_accepted": True,
            "all_primary_signed_and_auxiliary_values_saved_as_integers": True,
            "native_infeasibility_has_no_independent_certificate": True,
            "exact_feasible_outcome_scope": "Necessary count/product/table model only; no literal incidence or graph is certified.",
            "graph_automorphism_assumed": False, "full_PSD_enforced": False,
            "original92_PSD_directions_and25_integer_refinements_retained": True,
            "automatic_retry": False}


def check_preparation(path):
    raw = path.read_bytes()
    preparation = json.loads(raw)
    assert preparation["status"] == "PASS: one-query preparation; no production solve"
    assert preparation["definition"] == configuration()
    assert preparation["controls"]["status"] == "PASS"
    assert preparation["optimizer_calls"] == preparation["CpSolver_constructed"] == 0
    return preparation, sha(raw)


def native_parameters(cmh, seconds):
    assert 0 < seconds <= SECONDS
    params = cmh.SatParameters()
    params.num_search_workers = 1
    params.random_seed = 0
    params.max_time_in_seconds = seconds
    params.log_search_progress = True
    params.log_to_stdout = True
    return params


def controls(directory):
    from google.protobuf import text_format
    from ortools.sat import cp_model_pb2, sat_parameters_pb2
    from ortools.sat.python import cp_model
    import ortools
    assert ortools.__version__ == "9.15.6755"
    assert sha(Path(cp_model.__file__).read_bytes()) == CP_MODEL_SHA
    params = native_parameters(cp_model.cmh, 17.25)
    copied = sat_parameters_pb2.SatParameters()
    text_format.Parse(str(params), copied)
    assert copied.num_search_workers == 1 and copied.random_seed == 0
    assert copied.max_time_in_seconds == 17.25 and copied.log_search_progress and copied.log_to_stdout
    # Actual pybind response serialization, without a solver or a native call.
    native = cp_model.cmh.CpSolverResponse()
    native.status = cp_model.OPTIMAL
    native.solution.extend([0, -6, 36, 144])
    response = cp_model_pb2.CpSolverResponse()
    text_format.Parse(str(native), response)
    assert list(response.solution) == [0, -6, 36, 144] and response.status == cp_model_pb2.OPTIMAL
    supervisor = load_source("supervisor")
    runs = []
    for name, code, seconds, expected in [
        ("normal", "pass", 3, "CHILD_EXITED"),
        ("failed", "raise SystemExit(3)", 3, "ERROR_CHILD_EXIT"),
        ("deadline", "import time; time.sleep(2)", 0.15, "UNKNOWN_HARD_DEADLINE"),
    ]:
        sub = directory / name
        sub.mkdir()
        result = supervisor.supervise([sys.executable, "-c", code], sub, time.monotonic() + seconds)
        assert result["status"] == expected and result["child_reaped"]
        runs.append({"name": name, "status": result["status"], "child_reaped": True})
    return {"status": "PASS", "native_parameter_roundtrip": True, "signed_integer_response_roundtrip": True,
            "owned_child_stop_controls": runs, "optimizer_calls": 0, "CpSolver_constructed": 0}


def worker(preparation_path, directory, deadline):
    started = time.monotonic()
    preparation, preparation_sha = check_preparation(preparation_path)
    result = {"status": "UNKNOWN_BEFORE_INITIALIZATION", "preparation_sha256": preparation_sha,
              "model_proto_sha256": MODEL_SHA, "production_solve_calls": 0,
              "count_feasibility_claimed": False, "graph_or_incidence_claimed": False, "F0_excluded": False}
    save(directory / "progress.json", result)
    try:
        model_source = load_source("model")
        data = model_source.read_inputs()
        model = model_source.build(data)
        path = directory / "constructed-model.pb"
        assert model.export_to_file(str(path))
        assert sha(path.read_bytes()) == MODEL_SHA
        result["model_construction_seconds"] = time.monotonic() - started
        from ortools.sat.python import cp_model
        import ortools
        assert ortools.__version__ == preparation["definition"]["ortools_version"]
        assert sha(Path(cp_model.__file__).read_bytes()) == CP_MODEL_SHA
        remaining = deadline - time.monotonic() - FINALIZATION_RESERVE
        if remaining <= 0:
            result["status"] = "UNKNOWN_INITIALIZATION_LIMIT"
            return
        params = native_parameters(cp_model.cmh, min(SECONDS, remaining))
        (directory / "parameters.pbtxt").write_text(str(params))
        result["parameters_sha256"] = sha((directory / "parameters.pbtxt").read_bytes())
        solver = cp_model.CpSolver()
        solver.parameters = params
        result.update(status="UNKNOWN_SOLVE_ACTIVE", production_solve_calls=1,
                      native_max_time_seconds=remaining)
        save(directory / "progress.json", result)
        search_started = time.monotonic()
        status = solver.solve(model)
        result["solve_wall_seconds"] = time.monotonic() - search_started
        from google.protobuf import text_format
        from ortools.sat import cp_model_pb2
        response_text = str(solver.response_proto)
        (directory / "response.pbtxt").write_text(response_text)
        response = cp_model_pb2.CpSolverResponse()
        text_format.Parse(response_text, response)
        result.update(native_status=status.name, native_status_code=int(response.status),
                      response_sha256=sha((directory / "response.pbtxt").read_bytes()),
                      native_wall_seconds=response.wall_time, native_conflicts=response.num_conflicts,
                      native_branches=response.num_branches, native_booleans=response.num_booleans,
                      native_integer_propagations=response.num_integer_propagations)
        assert cp_model_pb2.CpSolverStatus.Name(response.status) == status.name
        point = list(response.solution)
        if point:
            assert all(type(v) is int for v in point)
            save(directory / "candidate.json", point)
            result["candidate_sha256"] = sha((directory / "candidate.json").read_bytes())
            result["candidate_values"] = len(point)
        if status.name in ("FEASIBLE", "OPTIMAL"):
            assert len(point) == 18444
            exact = model_source.inspect(point, data)
            save(directory / "exact-point-check.json", exact)
            result.update(status="EXACT_COUNT_WITNESS", count_feasibility_claimed=True,
                          exact_point_check_sha256=sha((directory / "exact-point-check.json").read_bytes()))
        elif status.name == "INFEASIBLE":
            assert not point
            result["status"] = "UNPROVED_NATIVE_INFEASIBLE"
        elif status.name == "MODEL_INVALID":
            result["status"] = "ERROR_NATIVE_MODEL_INVALID"
        else:
            assert status.name == "UNKNOWN"
            result["status"] = "UNKNOWN_NATIVE_LIMIT"
        if time.monotonic() > deadline:
            result.update(status="UNKNOWN_LATE_CHILD", count_feasibility_claimed=False)
    except Exception as error:
        result.update(status="ERROR_NO_ACCEPTED_OUTCOME", count_feasibility_claimed=False,
                      error_type=type(error).__name__, message=str(error))
        raise
    finally:
        result["child_seconds"] = time.monotonic() - started
        save(directory / "child-result.json", result)


def run(preparation_path, directory):
    _, preparation_sha = check_preparation(preparation_path)
    supervisor = load_source("supervisor")
    directory.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    deadline = started + SECONDS
    result = {"status": "UNKNOWN_BEFORE_CHILD", "preparation_sha256": preparation_sha,
              "model_proto_sha256": MODEL_SHA, "runner_source_sha256": sha(Path(__file__).read_bytes()),
              "maximum_owned_child_seconds": SECONDS, "count_feasibility_claimed": False,
              "graph_or_incidence_claimed": False, "F0_excluded": False, "automatic_retry": False}
    save(directory / "result.json", result)
    command = [sys.executable, str(Path(__file__).resolve()), "_worker", "--preparation", str(preparation_path.resolve()),
               "--directory", str(directory.resolve()), "--deadline", str(deadline)]
    supervision = supervisor.supervise(command, directory, deadline)
    result["supervision"] = supervision
    if supervision["status"] == "CHILD_EXITED":
        raw = (directory / "child-result.json").read_bytes()
        child = json.loads(raw)
        assert child["preparation_sha256"] == preparation_sha and child["model_proto_sha256"] == MODEL_SHA
        assert child["production_solve_calls"] in (0, 1)
        assert not child["F0_excluded"] and not child["graph_or_incidence_claimed"]
        assert child["status"] in ("EXACT_COUNT_WITNESS", "UNPROVED_NATIVE_INFEASIBLE", "ERROR_NATIVE_MODEL_INVALID",
                                   "UNKNOWN_NATIVE_LIMIT", "UNKNOWN_INITIALIZATION_LIMIT", "UNKNOWN_LATE_CHILD")
        result.update(status=child["status"], child_result_sha256=sha(raw),
                      production_solve_calls=child["production_solve_calls"],
                      count_feasibility_claimed=child["status"] == "EXACT_COUNT_WITNESS")
    else:
        result["status"] = supervision["status"]
    result["owner_seconds"] = time.monotonic() - started
    result["deadline_overrun_seconds"] = max(0, time.monotonic() - deadline)
    save(directory / "result.json", result)
    print(json.dumps(result, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "run", "_worker"))
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--preparation", type=Path)
    parser.add_argument("--deadline", type=float)
    args = parser.parse_args()
    directory = args.directory.resolve()
    if args.mode == "prepare":
        started = time.monotonic()
        directory.mkdir(parents=True, exist_ok=False)
        definition = configuration()
        control = controls(directory)
        result = {"status": "PASS: one-query preparation; no production solve", "definition": definition,
                  "controls": control, "optimizer_calls": 0, "CpSolver_constructed": 0,
                  "seconds": time.monotonic() - started}
        save(directory / "preparation.json", result)
        print(json.dumps(result, indent=2))
    elif args.mode == "run":
        assert args.preparation is not None
        run(args.preparation, directory)
    else:
        assert args.preparation is not None and args.deadline is not None
        worker(args.preparation, directory, args.deadline)


if __name__ == "__main__":
    main()
