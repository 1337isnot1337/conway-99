"""One bounded native feasibility call, exact certificate, and cold replay.

Only exact rational mixture weights or exact signed endpoint separation are
accepted.  Native infeasibility alone remains unresolved.  Every child is
owned and reaped; no retry, alternate solver, or hidden dual-ray solve occurs.
"""

import argparse
from fractions import Fraction
import importlib.metadata
import json
import math
import os
from pathlib import Path
import platform
import signal
import subprocess
import sys
from threading import Event, Timer
import time

import rook_case4_box_hull_membership as helper


ROOT, LIMITS = helper.ROOT, helper.LIMITS
SOURCES = {
    "helper": ("experiments/workspace/rook_case4_box_hull_membership.py",
               "54330f430c0c4dae03a0298533121ce43482ceb295f54df715ad2f2180d3503c"),
    "replay": ("experiments/workspace/rook_case4_box_hull_membership_replay.py",
               "0db0c7f9acb6e1b5bd5429e6dd26fce813bc53fa9c33fb1111494e0d8f7d0d61"),
}
PREPARATION = (helper.BASE + "rook-case4-box-hull-membership-preparation01/preparation.json",
               "7e3477a1f4c323affcea0a4721d2333bdf4373384ddbe330970c9059359bc760")
PREPARATION_OWNER = (helper.BASE + "rook-case4-box-hull-membership-preparation01-owner/supervisor.json",
                     "e7f214fb1f149f0d4ec4a29239ed925d6128826f3e2e3fa0c17c03d85cd1d6ba")
OPTIONS = {"solver": "simplex", "presolve": "off", "threads": 1,
           "parallel": "off", "random_seed": 0, "simplex_strategy": 1,
           "output_flag": True}


def source_bindings():
    bindings = {key: list(value) for key, value in SOURCES.items()}
    for key, (name, digest) in bindings.items():
        assert helper.sha((ROOT / name).read_bytes()) == digest, key
    assert Path(helper.__file__).resolve() == ROOT / SOURCES["helper"][0]
    bindings["query"] = [str(Path(__file__).resolve().relative_to(ROOT)), helper.sha(Path(__file__).read_bytes())]
    return bindings


def read_ref(reference):
    path = (ROOT / reference["path"]).resolve()
    assert path.is_relative_to(ROOT) and path.stat().st_size == reference["bytes"]
    return helper.read((reference["path"], reference["sha256"]))


def prepare(output):
    started = time.monotonic()
    prep, owner = helper.read(PREPARATION), helper.read(PREPARATION_OWNER)
    assert prep["status"] == "PREPARED_191_WEIGHT_BOX_HULL_MEMBERSHIP_NO_OPTIMIZER"
    assert prep["source_sha256"] == SOURCES["helper"][1]
    assert owner["status"] == "CHILD_COMPLETE" and owner["exit_code"] == 0
    assert owner["child_reaped"] and not owner["hard_timeout"]
    assert any(r["path"] == PREPARATION[0] and r["sha256"] == PREPARATION[1] for r in owner["artifacts"])
    controls, model = read_ref(prep["controls"]), read_ref(prep["model"])
    assert controls["status"] == "PASS_EXACT_BOX_MEMBERSHIP_CONTROLS"
    domain = helper.load_inputs()
    # JSON-normalized comparison handles tuple/list serialization explicitly.
    assert helper.canonical(model) == helper.canonical(helper.build_model(domain))
    assert all(r["satisfied"] for r in domain["prior_seven_row_checks"])
    assert model["nonzeros"] == 38333 and len(model["matrix"]["rows"]) == 2205
    result = {
        "schema": "conway99.rook-case4.box-hull-membership-query.v1",
        "status": "PREPARED_ONE_BOX_HULL_NATIVE_CALL_NO_SOLVE",
        "sources": source_bindings(), "inputs": {k: list(v) for k, v in helper.INPUTS.items()},
        "preparation": list(PREPARATION), "preparation_owner": list(PREPARATION_OWNER),
        "model": prep["model"], "matrix_sha256": model["matrix_sha256"],
        "definition_sha256": model["definition_sha256"], "limits": LIMITS,
        "native_options": OPTIONS, "variables": 191, "rows": 2205, "nonzeros": 38333,
        "point_key": domain["point_key"], "point_denominator": str(domain["denominator"]),
        "full_native_transport_required_before_run": True,
        "saved_basis_used_only_as_a_proposal": True,
        "existing_dual_ray_required_before_getDualRay": True,
        "native_INFEASIBLE_is_not_a_certificate": True,
        "failed_exact_reconstruction_is_unresolved": True,
        "no_Boolean_or_original_model_solution_from_membership": True,
        "optimizer_calls": 0, "native_imports": 0, "seconds": time.monotonic() - started,
    }
    helper.write(output, result)
    return result


def load(configuration):
    config = json.loads(configuration.read_bytes())
    assert config["status"] == "PREPARED_ONE_BOX_HULL_NATIVE_CALL_NO_SOLVE"
    assert config["sources"] == source_bindings()
    assert config["inputs"] == {k: list(v) for k, v in helper.INPUTS.items()}
    assert config["limits"] == LIMITS and config["native_options"] == OPTIONS
    assert config["preparation"] == list(PREPARATION) and config["preparation_owner"] == list(PREPARATION_OWNER)
    prep = helper.read(PREPARATION)
    assert config["model"] == prep["model"]
    model = read_ref(config["model"])
    assert helper.sha(helper.canonical(model["matrix"])) == config["matrix_sha256"] == model["matrix_sha256"]
    assert helper.sha(helper.canonical(model["definition"])) == config["definition_sha256"] == model["definition_sha256"]
    domain = helper.load_inputs()
    assert config["point_key"] == domain["point_key"] and config["point_denominator"] == str(domain["denominator"])
    assert model["matrix"]["original_column_ids"] == domain["original_column_ids"]
    assert helper.canonical(model["matrix"]["rows"]) == helper.canonical(
        helper.build_rows(domain["states"], domain["numerators"], domain["denominator"], domain["original_column_ids"]))
    return config, model, domain


def native_model(model, directory):
    import highspy
    matrix = model["matrix"]
    n, rows, den = matrix["variable_count"], matrix["rows"], matrix["rhs_denominator"]
    assert n == 191 and len(rows) == 2205 and den == 2594289631
    starts, indices = [0], []
    for row in rows:
        assert row["columns"] == sorted(set(row["columns"]))
        indices.extend(row["columns"])
        starts.append(len(indices))
    assert len(indices) == 38333
    lower = [r["lower_numerator"] / den for r in rows]
    upper = [r["upper_numerator"] / den for r in rows]
    lp = highspy.HighsLp()
    lp.num_col_, lp.num_row_ = n, len(rows)
    lp.col_cost_, lp.col_lower_, lp.col_upper_ = [0.0] * n, [0.0] * n, [1.0] * n
    lp.row_lower_, lp.row_upper_ = lower, upper
    a = lp.a_matrix_
    a.format_ = highspy.MatrixFormat.kRowwise
    a.num_col_, a.num_row_ = n, len(rows)
    a.start_, a.index_, a.value_ = starts, indices, [1.0] * len(indices)
    h = highspy.Highs()
    for name, value in OPTIONS.items():
        assert h.setOptionValue(name, value) == highspy.HighsStatus.kOk
    assert h.setOptionValue("log_file", str((directory / "highs.log").resolve())) == highspy.HighsStatus.kOk
    h.HandleUserInterrupt = True
    assert h.HandleUserInterrupt
    assert h.passModel(lp) == highspy.HighsStatus.kOk
    actual = h.getLp()
    assert actual.num_col_ == n and actual.num_row_ == len(rows)
    assert list(actual.col_cost_) == [0.0] * n and list(actual.col_lower_) == [0.0] * n
    assert list(actual.col_upper_) == [1.0] * n
    assert list(actual.row_lower_) == lower and list(actual.row_upper_) == upper
    a = actual.a_matrix_
    restored = [[] for _ in rows]
    assert len(a.index_) == len(a.value_) == len(indices)
    if a.format_ == highspy.MatrixFormat.kRowwise:
        assert len(a.start_) == len(rows) + 1
        for i in range(len(rows)):
            for k in range(a.start_[i], a.start_[i + 1]):
                assert a.value_[k] == 1.0 and 0 <= a.index_[k] < n
                restored[i].append(int(a.index_[k]))
    else:
        assert a.format_ == highspy.MatrixFormat.kColwise and len(a.start_) == n + 1
        for j in range(n):
            for k in range(a.start_[j], a.start_[j + 1]):
                assert a.value_[k] == 1.0 and 0 <= a.index_[k] < len(rows)
                restored[int(a.index_[k])].append(j)
    assert [sorted(r) for r in restored] == [r["columns"] for r in rows]
    assert all(len(r) == len(set(r)) for r in restored)
    existence = h.getDualRayExist()
    assert existence[0] == highspy.HighsStatus.kOk and not existence[1]
    runtime = {"python": platform.python_version(), "highspy_package": importlib.metadata.version("highspy"),
               "native_HiGHS": h.version(), "helper_source_sha256": SOURCES["helper"][1],
               "one_thread": True, "empty_existing_ray_guard_passed": True}
    return h, highspy, runtime


def numerical(configuration, directory):
    started = time.monotonic()
    config, model, domain = load(configuration)
    h, highspy, runtime = native_model(model, directory)
    common = {"configuration": helper.reference(configuration), "model": config["model"],
              "point_key": domain["point_key"], "runtime": runtime,
              "all38333_coefficients_and_2205_row_bounds_checked": True,
              "all191_column_bounds_and_zero_objective_checked": True}
    helper.write(directory / "native-start.json", {**common, "status": "NATIVE_TRANSPORT_PASS_BEFORE_RUN"})
    assert h.setOptionValue("time_limit", LIMITS["native_seconds"]) == highspy.HighsStatus.kOk
    interrupted = Event()

    def cancel():
        interrupted.set()
        h.cancelSolve()

    timer = Timer(LIMITS["native_seconds"], cancel)
    native_started = time.monotonic()
    timer.start()
    try:
        run_status = h.run()
    finally:
        timer.cancel()
        timer.join()
    native_seconds = time.monotonic() - native_started
    status, solution, basis, info = h.getModelStatus(), h.getSolution(), h.getBasis(), h.getInfo()
    columns = list(map(float, solution.col_value))
    finite_vector = len(columns) == 191 and all(math.isfinite(v) for v in columns)
    numerical = {
        **common, "status": "SAVED_NUMERICAL_PROPOSAL_ONLY", "native_calls": 1,
        "native_seconds": native_seconds, "native_budget_overrun": native_seconds > LIMITS["native_seconds"],
        "run_status": int(run_status), "model_status": int(status), "model_status_text": str(status),
        "model_status_codes": {"optimal": int(highspy.HighsModelStatus.kOptimal),
                               "infeasible": int(highspy.HighsModelStatus.kInfeasible)},
        "interrupt_event": interrupted.is_set(), "simplex_iterations": int(info.simplex_iteration_count),
        "solution_value_valid": bool(solution.value_valid), "finite_column_vector": finite_vector,
        "column_values_hex": [v.hex() for v in columns],
        "basis": {"valid": bool(basis.valid), "column_status": [int(v) for v in basis.col_status],
                  "row_status": [int(v) for v in basis.row_status]},
        "basis_codes": {name: int(getattr(highspy.HighsBasisStatus, name))
                        for name in ("kLower", "kBasic", "kUpper", "kZero", "kNonbasic")},
    }
    # Preserve the complete vector/basis before attempting optional ray export.
    helper.write(directory / "native-vector.json", numerical)
    existing = h.getDualRayExist()
    ray = {"existence_status": int(existing[0]), "exists": bool(existing[1]), "ray_export_calls": 0,
           "hidden_optimizer_calls": 0, "values_hex": None}
    if existing[0] == highspy.HighsStatus.kOk and existing[1]:
        answer = h.getDualRay()
        ray["ray_export_calls"] = 1
        if answer[0] == highspy.HighsStatus.kOk and answer[1]:
            values = list(map(float, answer[2]))
            if len(values) == 2205 and all(math.isfinite(v) for v in values):
                ray["values_hex"] = [v.hex() for v in values]
    helper.write(directory / "existing-ray.json", ray)
    result = {**common, "status": "NUMERICAL_PROPOSALS_SAVED", "native_calls": 1,
              "native_seconds": native_seconds, "native_budget_overrun": numerical["native_budget_overrun"],
              "model_status": int(status), "model_status_text": str(status),
              "vector": helper.reference(directory / "native-vector.json"),
              "ray": helper.reference(directory / "existing-ray.json"),
              "native_status_is_not_a_certificate": True, "seconds": time.monotonic() - started}
    helper.write(directory / "result.json", result)
    h.clear()
    return result


def exact(configuration, directory, numeric_path):
    started = time.monotonic()
    config, model, domain = load(configuration)
    numeric = json.loads(numeric_path.read_bytes())
    assert numeric["configuration"] == helper.reference(configuration) and numeric["model"] == config["model"]
    assert not numeric["native_budget_overrun"] and numeric["native_calls"] == 1
    vector, ray = read_ref(numeric["vector"]), read_ref(numeric["ray"])
    assert vector["configuration"] == helper.reference(configuration) and vector["model"] == config["model"]
    result = {"status": "UNKNOWN_NO_EXACT_CERTIFICATE", "configuration": helper.reference(configuration),
              "numerical_result": helper.reference(numeric_path), "model": config["model"],
              "optimizer_calls": 0, "linear_solve_calls": 0, "certificate": None, "attempts": []}
    base = {"configuration": helper.reference(configuration), "model": config["model"],
            "point_key": domain["point_key"], "box_ids": domain["box_ids"],
            "helper_source_sha256": SOURCES["helper"][1], "case4_excluded": False}
    try:
        if (vector["model_status"] == vector["model_status_codes"]["optimal"]
                and vector["solution_value_valid"] and vector["finite_column_vector"] and vector["basis"]["valid"]):
            system = helper.basis_system(model["matrix"], vector)
            helper.write(directory / "basis-proposal.json.gz", system)
            result["basis_proposal"] = helper.reference(directory / "basis-proposal.json.gz")
            if system["dimension"]:
                import flint
                a = flint.fmpq_mat(system["coefficients"])
                b = flint.fmpq_mat([[v] for v in system["rhs"]])
                solve_started = time.monotonic()
                result["linear_solve_calls"] = 1
                solved = a.solve(b, algorithm="dixon")
                values = [Fraction(int(solved[j, 0].numerator), int(solved[j, 0].denominator))
                          for j in range(system["dimension"])]
                result["linear_solve"] = {"dimension": system["dimension"], "algorithm": "fmpq_mat.solve dixon",
                                          "seconds": time.monotonic() - solve_started,
                                          "temporary_integer_bit_cap_claimed": False}
            else:
                values = []
            if time.monotonic() - started >= LIMITS["exact_seconds"]:
                raise TimeoutError("exact phase cooperative deadline")
            masses, mass_den = helper.masses_from_solution(model["matrix"], system, values)
            check = helper.inspect_masses(domain["states"], domain["numerators"], domain["denominator"], masses, mass_den)
            certificate = {**base, "kind": "rational_box_hull_membership",
                           "lambda_numerators": list(map(str, masses)), "lambda_denominator": str(mass_den),
                           "owner_check": check, "basis_is_only_a_proposal": True,
                           "Boolean_or_original_model_solution_claimed": False}
            result["status"] = "EXACT_BOX_HULL_MEMBER_OWNER_CHECKED"
        elif (vector["model_status"] == vector["model_status_codes"]["infeasible"]
              and ray["values_hex"] is not None):
            certificate = None
            for proposal in helper.rounded_ray_proposals(ray["values_hex"], 1102):
                if time.monotonic() - started >= LIMITS["exact_seconds"]:
                    raise TimeoutError("exact separator cooperative deadline")
                checked = helper.separator_certificate(domain, proposal["coefficients"])
                result["attempts"].append({"scale": proposal["scale"], "orientation": proposal["orientation"],
                                           "lower": checked["lower"], "deficit_numerator": checked["deficit_numerator"]})
                if checked["status"] == "EXACT_BOX_HULL_SEPARATOR":
                    certificate = {**base, "kind": "signed_box_hull_separator", "separator": checked,
                                   "rounding": {"scale": proposal["scale"], "orientation": proposal["orientation"]},
                                   "native_ray_is_only_a_coefficient_proposal": True}
                    result["status"] = "EXACT_BOX_HULL_SEPARATOR_OWNER_CHECKED"
                    break
        else:
            certificate = None
            result["reason"] = "No eligible complete basis or existing infeasibility ray"
        if time.monotonic() - started >= LIMITS["exact_seconds"]:
            raise TimeoutError("exact phase cooperative deadline before acceptance")
        if certificate is not None:
            helper.write(directory / "certificate.json", certificate)
            result["certificate"] = helper.reference(directory / "certificate.json")
    except Exception as error:
        result["status"] = "UNKNOWN_EXACT_EXCEPTION"
        result["error_type"], result["error"] = type(error).__name__, str(error)
    result["seconds"] = time.monotonic() - started
    helper.write(directory / "result.json", result)
    return result


def owned(command, directory, seconds, label, new_group=False):
    directory.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONOPTIMIZE="0",
               OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1")
    with (directory / (label + ".stdout.log")).open("xb") as stdout, (directory / (label + ".stderr.log")).open("xb") as stderr:
        process = subprocess.Popen(command, stdout=stdout, stderr=stderr, cwd=ROOT, env=env,
                                   start_new_session=new_group)
        try:
            code = process.wait(timeout=seconds)
            timeout = False
        except subprocess.TimeoutExpired:
            if new_group:
                os.killpg(process.pid, signal.SIGKILL)
            else:
                # Inner phases import no subprocess-producing backend and inherit
                # the outer process group, so the whole-owner kill also reaches them.
                process.kill()
            code = process.wait()
            timeout = True
    return {"command": list(map(str, command)), "exit_code": code, "hard_timeout": timeout,
            "child_reaped": True, "new_process_group": new_group, "hard_seconds": seconds,
            "seconds": time.monotonic() - started,
            "artifacts": [helper.reference(p) for p in sorted(directory.iterdir()) if p.is_file()]}


def success(record):
    return record["exit_code"] == 0 and not record["hard_timeout"] and record["child_reaped"]


def controller(configuration, directory):
    started = time.monotonic()
    config, _, _ = load(configuration)
    result = {"status": "UNKNOWN", "configuration": helper.reference(configuration), "limits": LIMITS,
              "stages": [], "certificate": None, "cold": None, "native_calls": 0,
              "point_rejected_by_exact_box_cut": False, "box_hull_membership_proved": False,
              "case4_excluded": False, "Boolean_or_original_model_solution_claimed": False}
    executable = str(Path(__file__).resolve())
    numeric_dir, exact_dir, cold_dir = (directory / k for k in ("native", "exact", "cold"))
    stage = owned([sys.executable, executable, "_native", "--configuration", str(configuration.resolve()),
                   "--directory", str(numeric_dir.resolve())], numeric_dir, LIMITS["native_owner_seconds"], "native")
    result["stages"].append(stage)
    if success(stage) and (numeric_dir / "result.json").exists():
        numeric = json.loads((numeric_dir / "result.json").read_bytes())
        result["native_calls"], result["native_seconds"] = numeric["native_calls"], numeric["native_seconds"]
        assert result["native_calls"] == 1
        if not numeric["native_budget_overrun"]:
            stage = owned([sys.executable, executable, "_exact", "--configuration", str(configuration.resolve()),
                           "--directory", str(exact_dir.resolve()), "--numeric-result", str((numeric_dir / "result.json").resolve())],
                          exact_dir, LIMITS["exact_owner_seconds"], "exact")
            result["stages"].append(stage)
            if success(stage) and (exact_dir / "result.json").exists():
                exact_result = json.loads((exact_dir / "result.json").read_bytes())
                if exact_result["certificate"] is not None:
                    result["certificate"] = exact_result["certificate"]
                    cert_path = ROOT / exact_result["certificate"]["path"]
                    stage = owned([sys.executable, str(ROOT / SOURCES["replay"][0]),
                                   "--configuration", str(configuration.resolve()), "--certificate", str(cert_path.resolve()),
                                   "--output", str((cold_dir / "result.json").resolve())],
                                  cold_dir, LIMITS["cold_owner_seconds"], "cold")
                    result["stages"].append(stage)
                    if success(stage) and (cold_dir / "result.json").exists():
                        checked = json.loads((cold_dir / "result.json").read_bytes())
                        assert checked["certificate"] == result["certificate"]
                        assert checked["configuration"] == helper.reference(configuration)
                        result["cold"] = helper.reference(cold_dir / "result.json")
                        if checked["status"] == "PASS_INDEPENDENT_BOX_HULL_MEMBERSHIP":
                            result["status"] = "EXACT_POINT_IN_CONVEX_HULL_OF191_BOXES"
                            result["box_hull_membership_proved"] = True
                        elif checked["status"] == "PASS_INDEPENDENT_BOX_HULL_SEPARATOR":
                            result["status"] = "EXACT_SIGNED_BOX_HULL_CUT"
                            result["point_rejected_by_exact_box_cut"] = True
                        else:
                            raise ValueError("unexpected cold outcome")
        else:
            result["status"] = "UNKNOWN_NATIVE_BUDGET_OVERRUN"
    result["sources"] = source_bindings()
    result["seconds"] = time.monotonic() - started
    helper.write(directory / "result.json", result)
    return result


def run(configuration, directory):
    load(configuration)
    directory.mkdir(parents=True, exist_ok=False)
    command = [sys.executable, str(Path(__file__).resolve()), "_controller", "--configuration", str(configuration.resolve()),
               "--directory", str(directory.resolve())]
    owner = owned(command, directory, LIMITS["whole_owner_seconds"], "controller", new_group=True)
    owner.update(configuration=helper.reference(configuration), sources=source_bindings(),
                 automatic_retries=0, status="OWNED_BOX_HULL_RUN_COMPLETE" if success(owner) else "UNKNOWN_OWNER_FAILURE")
    if (directory / "result.json").exists():
        owner["child_result"] = helper.reference(directory / "result.json")
    helper.write(directory / "supervisor.json", owner)
    return owner


def verify(configuration, directory, output):
    config = json.loads(configuration.read_bytes())
    assert config["sources"] == source_bindings()
    owner = json.loads((directory / "supervisor.json").read_bytes())
    assert owner["configuration"] == helper.reference(configuration) and owner["sources"] == source_bindings()
    records = list(owner["artifacts"])
    if "child_result" in owner:
        child = read_ref(owner["child_result"])
        assert child["configuration"] == helper.reference(configuration)
        records += [r for stage in child["stages"] for r in stage["artifacts"]]
        if child["cold"] is not None:
            cold = read_ref(child["cold"])
            assert cold["certificate"] == child["certificate"]
    for record in records:
        assert helper.reference(ROOT / record["path"]) == record
    result = {"status": "PASS_BOX_HULL_TERMINAL_BINDINGS", "configuration": helper.reference(configuration),
              "supervisor": helper.reference(directory / "supervisor.json"), "artifact_bindings_checked": len(records),
              "optimizer_or_exact_solve_or_arithmetic_repeated": False}
    helper.write(output, result)
    return result


if __name__ == "__main__":
    assert __debug__
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("prepare", "run", "verify", "_controller", "_native", "_exact"))
    parser.add_argument("--configuration", type=Path)
    parser.add_argument("--directory", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--numeric-result", type=Path)
    args = parser.parse_args()
    if args.mode == "prepare":
        result = prepare(args.output)
    elif args.mode == "run":
        result = run(args.configuration, args.directory)
    elif args.mode == "verify":
        result = verify(args.configuration, args.directory, args.output)
    elif args.mode == "_controller":
        result = controller(args.configuration, args.directory)
    elif args.mode == "_native":
        result = numerical(args.configuration, args.directory)
    else:
        result = exact(args.configuration, args.directory, args.numeric_result)
    print(json.dumps({"status": result["status"], "seconds": result.get("seconds")}))
