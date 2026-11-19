"""One IPM/crossover query on the equivalent reduced second-moment model.

Production makes at most one Highs.run() call. Ray extraction is allowed
only after getDualRayExist confirms a ray already exists. No model retry,
feasibility relaxation, IIS query or hidden ray-generating solve is used.
"""
import argparse
import importlib.metadata
import importlib.util
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time

for _name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[_name] = "1"

HELPER_SHA256 = "0ade9c2f04415b325e7f217023dd072abaf4b8cdf60cd9fe07a2cfe93e416536"
VERSIONS = {"numpy": "2.3.5", "scipy": "1.17.0", "highspy": "1.16.0", "python-flint": "0.9.0"}

def helper():
    import hashlib
    path = Path(__file__).with_name("root_prism_free_f0_second_moments_reduced_exact.py")
    assert hashlib.sha256(path.read_bytes()).hexdigest() == HELPER_SHA256
    spec = importlib.util.spec_from_file_location("f0_second_moments_reduced_exact", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def version_check():
    actual = {name: importlib.metadata.version(name) for name in VERSIONS}
    assert actual == VERSIONS
    return actual

def numerical(model_path, output_path, seconds):
    started = time.monotonic()
    exact = helper()
    report = {"status": "RUNNING: native second-moment linear numerical phase",
              "model_sha256": exact.MODEL_SHA256, "source_sha256": exact.digest(__file__),
              "helper_source_sha256": HELPER_SHA256, "requested_seconds": seconds,
              "optimizer_calls": 0, "fixed_selectors": False,
              "numerical_method": "ipm", "run_crossover": "on",
              "output_reserve_seconds": 3.0,
              "terminal_selector_cut_registry_included": True,
              "full_Boolean_selector_rows": 4416, "PSD_constraints_enforced": False}
    exact.save(output_path, report)
    try:
        report["dependency_versions"] = version_check()
        import highspy
        import numpy as np
        from scipy import sparse
        model = exact.load_model(model_path)
        matrix = model["matrix"]
        rows = matrix["equalities"] + matrix["inequalities"]
        n, m = matrix["variables"], len(rows)
        ri, ci, coefficients = [], [], []
        for i, row in enumerate(rows):
            for j, value in row["terms"]:
                assert float(value).as_integer_ratio() == (value, 1)
                ri.append(i); ci.append(j); coefficients.append(float(value))
            assert float(row["rhs"]).as_integer_ratio() == (row["rhs"], 1)
        numerical_matrix = sparse.csc_matrix((np.asarray(coefficients), (ri, ci)), shape=(m, n))
        numerical_matrix.sort_indices()
        assert numerical_matrix.nnz == 183702
        rhs = np.asarray([row["rhs"] for row in rows], dtype=float)
        lower = rhs.copy()
        lower[len(matrix["equalities"]):] = -highspy.kHighsInf
        lp = highspy.HighsLp()
        lp.num_col_, lp.num_row_ = n, m
        lp.col_cost_ = np.zeros(n)
        lp.col_lower_, lp.col_upper_ = np.zeros(n), np.ones(n)
        lp.row_lower_, lp.row_upper_ = lower, rhs
        lp.a_matrix_.format_ = highspy.MatrixFormat.kColwise
        lp.a_matrix_.start_ = numerical_matrix.indptr
        lp.a_matrix_.index_ = numerical_matrix.indices
        lp.a_matrix_.value_ = numerical_matrix.data
        solver = highspy.Highs()
        for name, value in (("output_flag", True), ("threads", 1), ("solver", "ipm"),
                            ("run_crossover", "on"),
                            ("presolve", "on"), ("random_seed", 0)):
            assert solver.setOptionValue(name, value) == highspy.HighsStatus.kOk
        assert solver.passModel(lp) == highspy.HighsStatus.kOk
        remaining = seconds - (time.monotonic() - started) - 3.0
        if remaining <= 0:
            report["status"] = "UNKNOWN: numerical setup exhausted the budget"
        else:
            assert solver.setOptionValue("time_limit", remaining) == highspy.HighsStatus.kOk
            report.update(optimizer_calls=1, requested_optimizer_seconds=remaining,
                          variables=n, rows=m, nonzeros=numerical_matrix.nnz,
                          numerical_coefficients_are_exact_integers=True)
            exact.save(output_path, report)
            returned = solver.run()
            status = solver.getModelStatus()
            report.update(status="NUMERICAL_ONLY: exact arithmetic has not run",
                          run_return=str(returned), numerical_status=str(status),
                          optimizer_return_seconds=time.monotonic() - started)
            solution = solver.getSolution()
            values = list(map(float, solution.col_value))
            report["value_valid"] = bool(getattr(solution, "value_valid", False))
            report["dual_valid"] = bool(getattr(solution, "dual_valid", False))
            if len(values) == n and all(math.isfinite(v) for v in values):
                report["col_value_hex"] = [v.hex() for v in values]
            row_values = list(map(float, solution.row_value))
            if len(row_values) == m and all(math.isfinite(v) for v in row_values):
                report["row_value_hex"] = [v.hex() for v in row_values]
            basis = solver.getBasis()
            report["basis_valid"] = bool(getattr(basis, "valid", False))
            report["column_basis_status"] = list(map(str, basis.col_status))
            report["row_basis_status"] = list(map(str, basis.row_status))
            info = solver.getInfo()
            report["simplex_iterations"] = int(info.simplex_iteration_count)
            report["ipm_iterations"] = int(info.ipm_iteration_count)
            report["crossover_iterations"] = int(info.crossover_iteration_count)
            report["primal_solution_status"] = str(info.primal_solution_status)
            report["dual_solution_status"] = str(info.dual_solution_status)
            report["existing_ray_query"] = "not requested for a non-infeasible numerical status"
            if status == highspy.HighsModelStatus.kInfeasible:
                exists_status, exists = solver.getDualRayExist()
                assert exists_status == highspy.HighsStatus.kOk
                report["existing_ray_query"] = bool(exists)
                if exists:
                    ray_status, still_exists, ray = solver.getDualRay()
                    assert ray_status == highspy.HighsStatus.kOk and still_exists
                    values = list(map(float, ray))
                    assert len(values) == m and all(math.isfinite(v) for v in values)
                    report["existing_dual_ray_hex"] = [v.hex() for v in values]
                else:
                    report["ray_generation_skipped"] = "getDualRay could otherwise solve an additional LP"
    except Exception as error:
        report.update(status="ERROR: native numerical phase stopped",
                      error_type=type(error).__name__, error_message=str(error))
        raise
    finally:
        report["elapsed_seconds"] = time.monotonic() - started
        report["cooperative_overrun_seconds"] = max(0, report["elapsed_seconds"] - seconds)
        exact.save(output_path, report)
    return report

def owned_child(arguments, stdout_path, stderr_path, hard_seconds):
    started = time.monotonic()
    with Path(stdout_path).open("w") as stdout, Path(stderr_path).open("w") as stderr:
        try:
            completed = subprocess.run(arguments, stdout=stdout, stderr=stderr,
                                       timeout=hard_seconds, check=False)
            return {"exit_code": completed.returncode, "hard_timeout": False,
                    "elapsed_seconds": time.monotonic() - started}
        except subprocess.TimeoutExpired:
            return {"exit_code": None, "hard_timeout": True,
                    "elapsed_seconds": time.monotonic() - started}

def preparation(model_path, output):
    exact = helper()
    assert not Path(output).exists()
    model = exact.load_model(model_path)
    versions = version_check()
    control = exact.controls()
    import highspy
    solver = highspy.Highs()
    for option, value in (("solver", "ipm"), ("run_crossover", "on")):
        assert solver.setOptionValue(option, value) == highspy.HighsStatus.kOk
        assert solver.getOptionValue(option) == (highspy.HighsStatus.kOk, value)
    status, exists = solver.getDualRayExist()
    assert status == highspy.HighsStatus.kOk and not exists and solver.getRunTime() == 0
    matrix = model["matrix"]
    record = {"status": "PASS: one-call IPM/crossover second-moment query prepared; no optimizer",
              "source_sha256": exact.digest(__file__), "helper_source_sha256": HELPER_SHA256,
              "model_file_sha256": exact.digest(model_path), "model_sha256": exact.MODEL_SHA256,
              "matrix_sha256": exact.MATRIX_SHA256, "dependency_versions": versions,
              "counts": {"variables": matrix["variables"], "equalities": len(matrix["equalities"]),
                         "inequalities": len(matrix["inequalities"]),
                         "nonzeros": sum(len(r["terms"]) for r in matrix["equalities"]+matrix["inequalities"]),
                         "full_rows_required_for_point_acceptance": 650350,
                         "full_bounds_required_for_point_acceptance": 183834},
              "controls": control, "empty_existing_ray_guard_control": True,
              "limits": {"production_Highs_run_calls": 1,
                         "lp_seconds_including_setup": 180, "owned_lp_child_hard_seconds": 180,
                         "numerical_output_reserve_seconds": 3,
                         "exact_phase_calls": 1, "owned_exact_child_hard_seconds": 60},
              "numerical_basis_saved": True,
              "numerical_method": "ipm", "run_crossover": "on",
              "active_face_is_only_a_proposal": True,
              "PSD_constraints_enforced": False, "optimizer_calls": 0}
    exact.save(output, record)
    return record


def checked_preparation(path, model_path):
    exact = helper()
    record = json.loads(Path(path).read_text())
    assert record["status"] == "PASS: one-call IPM/crossover second-moment query prepared; no optimizer"
    assert record["source_sha256"] == exact.digest(__file__) and record["helper_source_sha256"] == HELPER_SHA256
    assert record["model_file_sha256"] == exact.digest(model_path)
    assert record["model_sha256"] == exact.MODEL_SHA256 and record["matrix_sha256"] == exact.MATRIX_SHA256
    assert record["dependency_versions"] == version_check()
    assert record["controls"] == exact.controls()
    assert record["empty_existing_ray_guard_control"] is True and record["optimizer_calls"] == 0
    assert record["limits"] == {"production_Highs_run_calls": 1,
        "lp_seconds_including_setup": 180, "owned_lp_child_hard_seconds": 180,
                         "numerical_output_reserve_seconds": 3,
        "exact_phase_calls": 1, "owned_exact_child_hard_seconds": 60}
    assert record["PSD_constraints_enforced"] is False and record["numerical_basis_saved"] is True
    assert record["numerical_method"] == "ipm" and record["run_crossover"] == "on"
    return record


def query(preparation_path, model_path, directory, lp_seconds, exact_seconds):
    assert 0 < lp_seconds <= 180 and 0 < exact_seconds <= 60
    prepared = checked_preparation(preparation_path, model_path)
    exact = helper()
    model_path, directory = Path(model_path).resolve(), Path(directory).resolve()
    assert not directory.exists(), "fresh query directory required"
    directory.mkdir(parents=True)
    exact.load_model(model_path)
    output = directory / "result.json"
    result = {"status": "RUNNING: one native second-moment linear query",
              "model_sha256": exact.MODEL_SHA256, "model_file_sha256": exact.digest(model_path),
              "source_sha256": exact.digest(__file__), "helper_source_sha256": HELPER_SHA256,
              "requested_lp_seconds": lp_seconds, "lp_hard_limit_seconds": lp_seconds,
              "numerical_method": "ipm", "run_crossover": "on",
              "numerical_output_reserve_seconds": 3,
              "requested_exact_seconds": exact_seconds, "exact_hard_limit_seconds": exact_seconds,
              "production_optimizer_calls_authorized": 1, "exact_phase_calls_authorized": 1,
              "baseline_only": False, "fixed_selector_point": False,
              "second_selector_moment_linear_system": True, "PSD_constraints_enforced": False,
              "equivalent_reduced_representation": True,
              "original_full_point_acceptance_retained": True,
              "preparation_file_sha256": exact.digest(preparation_path),
              "no_component_exclusion_without_independent_exact_replay": True}
    exact.save(output, result)
    started = time.monotonic()
    numeric_path, exact_path = directory / "numerical.json", directory / "exact.json"
    try:
        result["numerical_process"] = owned_child(
            [sys.executable, str(Path(__file__).resolve()), "_numerical",
             "--model", str(model_path), "--output", str(numeric_path), "--seconds", str(lp_seconds)],
            directory / "numerical.stdout.log", directory / "numerical.stderr.log", lp_seconds)
        if numeric_path.exists():
            numerical_report = json.loads(numeric_path.read_text())
            result["numerical_file_sha256"] = exact.digest(numeric_path)
            result["optimizer_calls_recorded"] = numerical_report["optimizer_calls"]
            result["numerical_status"] = numerical_report.get("numerical_status")
        else:
            numerical_report = None
        process = result["numerical_process"]
        if process["hard_timeout"] or process["exit_code"] != 0 or numerical_report is None:
            result["status"] = "UNKNOWN: numerical process timeout" if process["hard_timeout"] else "ERROR: numerical process failed"
            return result
        assert not numerical_report["status"].startswith("RUNNING")
        result["exact_process"] = owned_child(
            [sys.executable, str(Path(__file__).resolve()), "_exact",
             "--model", str(model_path), "--numerical", str(numeric_path),
             "--output", str(exact_path), "--seconds", str(exact_seconds)],
            directory / "exact.stdout.log", directory / "exact.stderr.log", exact_seconds)
        process = result["exact_process"]
        if exact_path.exists():
            exact_report = json.loads(exact_path.read_text())
            result["exact_file_sha256"] = exact.digest(exact_path)
        else:
            exact_report = None
        if process["hard_timeout"]:
            result["status"] = "UNKNOWN: exact phase hard time limit"
        elif process["exit_code"] != 0 or exact_report is None:
            result["status"] = "ERROR: exact phase failed"
        elif exact_report["kind"] == "point":
            result["status"] = "EXACT_LINEAR_POINT_FOUND: independent full replay pending"
        elif exact_report["kind"] == "farkas":
            result["status"] = "EXACT_LINEAR_FARKAS_FOUND: independent full replay pending"
        else:
            result["status"] = "UNKNOWN: no exact point or infeasibility certificate"
        return result
    finally:
        result["elapsed_seconds"] = time.monotonic() - started
        exact.save(output, result)

def controls(output):
    exact = helper()
    versions = version_check()
    report = exact.controls()
    import highspy
    solver = highspy.Highs()
    for option, value in (("solver", "ipm"), ("run_crossover", "on")):
        assert solver.setOptionValue(option, value) == highspy.HighsStatus.kOk
        assert solver.getOptionValue(option) == (highspy.HighsStatus.kOk, value)
    status, exists = solver.getDualRayExist()
    assert status == highspy.HighsStatus.kOk and not exists
    # This existence-only API calls C++ getDualRay with a null output buffer.
    # No Highs.run(), getDualRay(), or optimizer is invoked in controls.
    report.update(source_sha256=exact.digest(__file__), helper_source_sha256=HELPER_SHA256,
                  dependency_versions=versions, empty_existing_ray_check=True)
    assert not Path(output).exists()
    exact.save(output, report)

def main():
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="mode", required=True)
    p = commands.add_parser("controls")
    p.add_argument("--output", type=Path, required=True)
    p = commands.add_parser("prepare")
    p.add_argument("--model", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p = commands.add_parser("query")
    p.add_argument("--preparation", type=Path, required=True)
    p.add_argument("--model", type=Path, required=True)
    p.add_argument("--directory", type=Path, required=True)
    p.add_argument("--lp-seconds", type=float, default=180)
    p.add_argument("--exact-seconds", type=float, default=60)
    p = commands.add_parser("_numerical")
    p.add_argument("--model", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--seconds", type=float, required=True)
    p = commands.add_parser("_exact")
    p.add_argument("--model", type=Path, required=True)
    p.add_argument("--numerical", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--seconds", type=float, required=True)
    args = parser.parse_args()
    if args.mode == "controls":
        controls(args.output)
    elif args.mode == "prepare":
        report = preparation(args.model, args.output)
        print(json.dumps(report, indent=2), flush=True)
    elif args.mode == "query":
        query(args.preparation, args.model, args.directory, args.lp_seconds, args.exact_seconds)
    elif args.mode == "_numerical":
        assert 0 < args.seconds <= 180 and not args.output.exists()
        numerical(args.model, args.output, args.seconds)
    else:
        assert 0 < args.seconds <= 60 and not args.output.exists()
        helper().exact_phase(args.model, args.numerical, args.output, args.seconds)

if __name__ == "__main__":
    main()

