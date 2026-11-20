"""One proof-enabled query for a frozen fixed-selection exterior CNF.

Only the new fixed-selection adapter supplies data and the three reused pure
functions. No historical incidence loader is called. A SAT answer describes
an exterior partial graph. A direct DRAT pass still needs the separate cold
rebuild, retained-input check and second DRAT pass before a selector cut exists.
"""
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import resource
import signal
import subprocess
import sys
import threading
import time

ROOT = Path(__file__).resolve().parents[2]
ADAPTER = ("experiments/workspace/root_prism_free_f0_fixed_selection_exterior.py",
           "2c8a0f7f2bc2a219c994f42618585879e16a6d3a5809627b9aea25be40798160")
OWNER_SECONDS, NATIVE_SECONDS, CHECKER_SECONDS = 180, 60, 60
PREPARATION_SECONDS, COLD_SECONDS, RESERVE = 60, 60, 2
MAX_CNF_BYTES, MAX_PROOF_BYTES = 64 << 20, 256 << 20


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def digest(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def save(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(canonical(value) + b"\n")
    temporary.replace(path)


def read_bound(item, binary=False):
    path = ROOT / item["path"]
    raw = path.read_bytes()
    assert sha(raw) == item["sha256"], item["path"]
    return raw if binary else json.loads(raw)


def adapter_module():
    path = ROOT / ADAPTER[0]
    assert digest(path) == ADAPTER[1]
    spec = importlib.util.spec_from_file_location("frozen_fixed_exterior", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def remaining(deadline, maximum, reserve=RESERVE):
    return max(0.0, min(maximum, deadline - time.monotonic() - reserve))


def verified_checker(returncode, stdout, timed_out, seconds, budget):
    return (not timed_out and returncode == 0 and 0 <= seconds <= budget
            and re.search(r"(?m)^s VERIFIED[ \t]*$", stdout.replace("\r", "\n")) is not None)


def controls():
    cases = [(0, "s VERIFIED\n", False, 1, 2, True),
             (0, "\rs VERIFIED\n", False, 1, 2, True),
             (0, "c VERIFIED derivation\n", False, 1, 2, False),
             (0, "s NOT VERIFIED\n", False, 1, 2, False),
             (0, "s VERIFIED\n", True, 1, 2, False),
             (1, "s VERIFIED\n", False, 1, 2, False),
             (0, "s VERIFIED\n", False, 3, 2, False)]
    for *args, expected in cases:
        assert verified_checker(*args) is expected
    return {"checker_acceptance_cases": len(cases), "production_solver_calls": 0}


def definition(config_path):
    config = json.loads(config_path.read_bytes())
    assert config["schema"] == "conway99.f0.fixed-exterior-query-inputs.v1"
    required = {"model", "cnf", "selection", "builder_preparation", "model_cold", "model_cold_owner"}
    assert set(config["inputs"]) == required
    for item in [*config["inputs"].values(), *config["evidence"].values(),
                 config["checker"], config["checker_source"], *config["native_files"].values()]:
        assert digest(ROOT / item["path"]) == item["sha256"], item["path"]
    assert config["pysat_version"] == "1.9.dev23"
    adapter = adapter_module()
    return {"schema": "conway99.f0.fixed-exterior-query.v1", "source_sha256": digest(__file__),
            "configuration_sha256": digest(config_path), "configuration": config,
            "adapter_definition": adapter.definition(),
            "owner_seconds": OWNER_SECONDS, "native_seconds_including_initialization": NATIVE_SECONDS,
            "maximum_direct_checker_seconds": CHECKER_SECONDS, "cold_owner_seconds": COLD_SECONDS,
            "maximum_cold_checker_seconds": CHECKER_SECONDS, "preparation_owner_seconds": PREPARATION_SECONDS,
            "single_production_solve": True, "solver": "Glucose4", "with_proof": True,
            "assumptions": [], "solver_threads": 1, "model_modified": False,
            "retained_inputs_checked_against_complete_CNF": True,
            "selector_cut_requires_accepted_cold_owner": True,
            "historical_input_loader_called": False, "second_component_fixed": False,
            "maximum_CNF_bytes": MAX_CNF_BYTES, "maximum_saved_proof_bytes": MAX_PROOF_BYTES}


def load_model(conf):
    config = conf["configuration"]
    inputs = config["inputs"]
    model, selected, prepared, cold, owner = [read_bound(inputs[k]) for k in
        ("model", "selection", "builder_preparation", "model_cold", "model_cold_owner")]
    assert prepared["definition"] == model["definition"] == cold["definition"] == conf["adapter_definition"]
    assert prepared["status"].startswith("PASS") and model["CNF_built"] is True
    assert model["preparation_sha256"] == inputs["builder_preparation"]["sha256"]
    assert owner["status"] == "PASS" and owner["report_accepted"] is True
    assert owner["report_sha256"] == inputs["model_cold"]["sha256"]
    assert owner["seconds"] <= owner["maximum_seconds"] == 60
    assert owner["supervision"]["status"] == "CHILD_EXITED" and owner["supervision"]["child_reaped"]
    assert owner["supervision"]["returncode"] == 0
    assert cold["status"] == "PASS: independent input, whole data and complete CNF/capacity reconstruction"
    assert cold["model_sha256"] == inputs["model"]["sha256"]
    assert cold["selection_sha256"] == model["selection_sha256"] == inputs["selection"]["sha256"]
    assert model["data"]["design_source_indices"] == selected
    assert selected == sorted(set(selected)) and len(selected) == 60
    assert model["canonical_selection_sha256"] == sha(canonical(selected))
    assert model["cnf_sha256"] == inputs["cnf"]["sha256"]
    assert (ROOT / inputs["cnf"]["path"]).stat().st_size == model["cnf_bytes"] <= MAX_CNF_BYTES
    assert model["second_component_fixed"] is False and model["solver_calls"] == 0
    assert model["pysat_version"] == config["pysat_version"]
    return model, selected


def native_api(conf):
    import pysat
    import pysat.solvers
    import pysolvers
    assert pysat.__version__ == conf["configuration"]["pysat_version"]
    expected = conf["configuration"]["native_files"]
    assert digest(pysat.solvers.__file__) == expected["solvers"]["sha256"]
    assert digest(pysolvers.__file__) == expected["extension"]["sha256"]
    return adapter_module().reused_api(), pysat.solvers.Glucose4


def parsed_cnf(conf, model):
    from pysat.formula import CNF
    path = ROOT / conf["configuration"]["inputs"]["cnf"]["path"]
    assert digest(path) == model["cnf_sha256"]
    cnf = CNF(from_file=str(path))
    formula = model["formula"]
    assert cnf.nv == formula["variables"] and len(cnf.clauses) == formula["clauses"]
    assert sum(map(len, cnf.clauses)) == formula["literals"]
    assert all(all(type(v) is int and 1 <= abs(v) <= cnf.nv for v in row) for row in cnf.clauses)
    return cnf


def exact_candidate(api, cnf, model, assignment):
    assert isinstance(assignment, list) and all(type(v) is int and 1 <= abs(v) <= cnf.nv for v in assignment)
    assert len(assignment) == cnf.nv and len({abs(v) for v in assignment}) == cnf.nv
    literals = set(assignment)
    assert all(any(v in literals for v in row) for row in cnf.clauses)
    chosen = [i for i in range(model["formula"]["primary_variables"]) if i + 1 in literals]
    return api["inspect"](chosen, model["data"])


def retained_subset(api, full_clauses, path):
    needed = Counter(tuple(sorted(row)) for row in api["read_clauses"](path))
    count = sum(needed.values())
    available = Counter(tuple(sorted(row)) for row in full_clauses)
    assert not (needed - available)
    return count


def checker_call(conf, cnf, proof, directory, deadline, retain):
    checker = conf["configuration"]["checker"]
    assert digest(ROOT / checker["path"]) == checker["sha256"]
    budget = remaining(deadline, CHECKER_SECONDS)
    if budget < 1:
        return {"verified": False, "status": "UNKNOWN_NO_CHECKER_BUDGET", "budget": budget}
    command = [str((ROOT / checker["path"]).resolve()), str(cnf.resolve()), str(proof.resolve()),
               "-t", str(max(1, math.floor(budget))), "-w"]
    if retain:
        command += ["-c", str((directory / "retained.cnf").resolve()),
                    "-l", str((directory / "retained.drat").resolve())]
    out_path, err_path = directory / "checker.stdout.log", directory / "checker.stderr.log"
    started, timed_out, process = time.monotonic(), False, None
    with out_path.open("xb") as stdout, err_path.open("xb") as stderr:
        try:
            process = subprocess.Popen(command, stdout=stdout, stderr=stderr)
            process.wait(timeout=max(0.001, budget - (time.monotonic() - started)))
        except subprocess.TimeoutExpired:
            timed_out = True
        finally:
            if process is not None:
                if process.poll() is None:
                    process.kill()
                process.wait()
    elapsed = time.monotonic() - started
    assert process is not None
    stdout = out_path.read_text(errors="replace")
    return {"verified": verified_checker(process.returncode, stdout, timed_out, elapsed, budget),
            "returncode": process.returncode, "timed_out": timed_out, "child_reaped": True,
            "seconds": elapsed, "budget": budget, "checker_sha256": checker["sha256"],
            "stdout_sha256": digest(out_path), "stderr_sha256": digest(err_path)}


def checked_preparation(config_path, directory):
    conf = definition(config_path)
    report, owner = [json.loads((directory / name).read_bytes()) for name in ("report.json", "owner.json")]
    assert report["status"] == "PASS_PREFLIGHT_NO_SOLVER" and report["definition"] == conf
    assert owner["report_accepted"] and owner["status"] == report["status"]
    assert owner["report_sha256"] == digest(directory / "report.json")
    assert owner["deadline_overrun_seconds"] == 0 and owner["supervision"]["child_reaped"]
    assert owner["source_sha256"] == digest(__file__) and owner["maximum_seconds"] == PREPARATION_SECONDS
    assert owner["supervision"]["status"] == "CHILD_EXITED" and owner["supervision"]["returncode"] == 0
    return conf


def prepare(config_path, directory, deadline, stage):
    conf = definition(config_path)
    model, selected = load_model(conf)
    adapter = adapter_module()
    assert adapter.derive(selected, adapter.context()) == model["data"]
    api, _ = native_api(conf)
    stage("native_import_and_full_data_checked")
    cnf = parsed_cnf(conf, model)
    stage("complete_CNF_parsed_without_solver")
    return {"status": "PASS_PREFLIGHT_NO_SOLVER", "definition": conf, "controls": controls(),
            "formula": model["formula"], "selection": selected, "native_imported": True,
            "solver_constructed": False, "production_solve_calls": 0,
            "model_cold_authority_sha256": conf["configuration"]["inputs"]["model_cold"]["sha256"]}


def run(config_path, preparation, directory, deadline, stage):
    conf = checked_preparation(config_path, preparation)
    model, _ = load_model(conf)
    result = {"status": "UNKNOWN_BEFORE_NATIVE", "definition": conf,
              "query_preparation_sha256": digest(preparation / "report.json"), "production_solve_calls": 0,
              "fixed_selection_excluded": False, "full_graph_constructed": False,
              "whole_component_excluded": False, "second_component_fixed": False}
    save(directory / "result.json", result)
    native_started = time.monotonic()
    native_budget = remaining(deadline, NATIVE_SECONDS)
    api, Glucose4 = native_api(conf)
    cnf = parsed_cnf(conf, model)
    with Glucose4(bootstrap_with=cnf.clauses, with_proof=True) as solver:
        stage("proof_solver_initialized")
        left = min(native_budget - (time.monotonic() - native_started), remaining(deadline, NATIVE_SECONDS))
        result.update(native_budget=native_budget, initialization_seconds=time.monotonic() - native_started)
        if left <= 0.1:
            result["status"] = "UNKNOWN_NATIVE_INITIALIZATION_LIMIT"
        else:
            timer = threading.Timer(left - 0.05, solver.interrupt)
            timer.daemon = True
            result["production_solve_calls"] = 1
            save(directory / "result.json", result)
            timer.start()
            try:
                answer = solver.solve_limited(expect_interrupt=True)
            finally:
                timer.cancel()
                timer.join()
            elapsed = time.monotonic() - native_started
            result.update(native_phase_seconds=elapsed, native_overrun_seconds=max(0, elapsed - native_budget),
                          solver_statistics=solver.accum_stats())
            if answer is True:
                assignment = solver.get_model()
                save(directory / "assignment.json", assignment)
                result.update(raw_answer="SAT", assignment_sha256=digest(directory / "assignment.json"))
            elif answer is False:
                proof = solver.get_proof()
                assert isinstance(proof, list) and all(isinstance(line, str) for line in proof)
                appended = not proof or proof[-1].strip() != "0"
                if appended:
                    proof.append("0")
                size = sum(len(line.encode("ascii")) + 1 for line in proof)
                assert size <= MAX_PROOF_BYTES
                with (directory / "raw.drat").open("x", encoding="ascii") as stream:
                    for line in proof:
                        stream.write(line + "\n")
                result.update(raw_answer="UNSAT", raw_proof_sha256=digest(directory / "raw.drat"),
                              raw_proof_bytes=size, terminal_empty_clause_appended=appended)
            else:
                assert answer is None
                result["raw_answer"] = "UNKNOWN"
            save(directory / "result.json", result)
            if elapsed > native_budget:
                result["status"] = "UNKNOWN_NATIVE_BUDGET_OVERRUN"
            elif answer is True:
                witness = exact_candidate(api, cnf, model, assignment)
                save(directory / "candidate-check.json", witness)
                result.update(status="SAT_EXACT_PARTIAL_EXTERIOR", candidate_check_sha256=digest(directory / "candidate-check.json"))
            elif answer is False:
                result["status"] = "UNSAT_UNVERIFIED"
            else:
                result["status"] = "UNKNOWN_INTERRUPTED"
    save(directory / "result.json", result)
    if result["status"] == "UNSAT_UNVERIFIED":
        stage("raw_proof_saved_before_direct_check")
        cnf_path = ROOT / conf["configuration"]["inputs"]["cnf"]["path"]
        checked = checker_call(conf, cnf_path, directory / "raw.drat", directory, deadline, True)
        result["direct_checker"] = checked
        if checked["verified"]:
            retained, proof = directory / "retained.cnf", directory / "retained.drat"
            assert retained.stat().st_size <= MAX_CNF_BYTES and proof.stat().st_size <= MAX_PROOF_BYTES
            count = retained_subset(api, cnf.clauses, retained)
            result.update(status="UNSAT_DIRECT_DRAT_PASS_COLD_REQUIRED", retained_input_clauses=count,
                          retained_cnf_sha256=digest(retained), retained_proof_sha256=digest(proof))
    return result


def cold(config_path, preparation, saved_directory, directory, deadline, stage):
    conf = checked_preparation(config_path, preparation)
    model, selected = load_model(conf)
    owner = json.loads((saved_directory / "owner.json").read_bytes())
    assert owner["source_sha256"] == digest(__file__) and owner["maximum_seconds"] == OWNER_SECONDS
    accepted = owner["report_accepted"] is True
    result_path = saved_directory / "result.json"
    result_raw = result_path.read_bytes() if result_path.exists() else None
    result = json.loads(result_raw) if result_raw is not None else {}
    if result:
        assert result["definition"] == conf and result["query_preparation_sha256"] == digest(preparation / "report.json")
        assert result["production_solve_calls"] in (0, 1) and not result["fixed_selection_excluded"]
    if accepted:
        assert result_raw is not None
        assert owner["report_sha256"] == sha(result_raw) and owner["status"] == result["status"]
        assert owner["deadline_overrun_seconds"] == 0 and owner["supervision"]["status"] == "CHILD_EXITED"
        assert owner["supervision"]["child_reaped"] and owner["supervision"]["returncode"] == 0
    adapter = adapter_module()
    ctx = adapter.context()
    data = adapter.derive(selected, ctx)
    assert data == model["data"] and adapter.capacity_obstruction(data, ctx) is None
    api, _ = native_api(conf)
    cnf, formula = api["build"](data)
    assert formula == model["formula"]
    cnf.to_file(directory / "rebuilt.cnf")
    assert digest(directory / "rebuilt.cnf") == model["cnf_sha256"]
    stage("complete_domain_and_CNF_rebuilt")
    report = {"status": "PASS_COLD_BINDINGS_NO_EXCLUSION", "definition": conf,
              "run_result_sha256": sha(result_raw) if result_raw is not None else None,
              "run_owner_sha256": digest(saved_directory / "owner.json"),
              "full_CNF_sha256": model["cnf_sha256"], "run_owner_accepted": accepted,
              "production_solve_calls": 0, "fixed_selection_excluded": False, "full_graph_constructed": False}
    for name, key in (("assignment.json", "assignment_sha256"), ("raw.drat", "raw_proof_sha256")):
        if key in result:
            assert digest(saved_directory / name) == result[key]
    if accepted and result["status"] in ("SAT_EXACT_PARTIAL_EXTERIOR", "UNSAT_DIRECT_DRAT_PASS_COLD_REQUIRED"):
        assert result["production_solve_calls"] == 1 and result["native_overrun_seconds"] == 0
        assert 0 <= result["native_phase_seconds"] <= result["native_budget"] <= NATIVE_SECONDS
        if result["status"] == "SAT_EXACT_PARTIAL_EXTERIOR":
            witness = exact_candidate(api, cnf, model, json.loads((saved_directory / "assignment.json").read_bytes()))
            assert digest(saved_directory / "candidate-check.json") == result["candidate_check_sha256"]
            assert witness == json.loads((saved_directory / "candidate-check.json").read_bytes())
            save(directory / "candidate-check.json", witness)
            report.update(status="PASS_COLD_EXACT_PARTIAL_EXTERIOR", candidate_check_sha256=digest(directory / "candidate-check.json"))
        else:
            direct = result["direct_checker"]
            assert direct["verified"] is True and direct["checker_sha256"] == conf["configuration"]["checker"]["sha256"]
            out, err = saved_directory / "checker.stdout.log", saved_directory / "checker.stderr.log"
            assert digest(out) == direct["stdout_sha256"] and digest(err) == direct["stderr_sha256"]
            assert verified_checker(direct["returncode"], out.read_text(errors="replace"), direct["timed_out"], direct["seconds"], direct["budget"])
            assert 0 < direct["budget"] <= CHECKER_SECONDS and direct["child_reaped"]
            retained, proof = saved_directory / "retained.cnf", saved_directory / "retained.drat"
            assert digest(retained) == result["retained_cnf_sha256"] and digest(proof) == result["retained_proof_sha256"]
            count = retained_subset(api, cnf.clauses, retained)
            assert count == result["retained_input_clauses"]
            checked = checker_call(conf, retained, proof, directory, deadline, False)
            report.update(cold_checker=checked, retained_input_clauses=count,
                          retained_cnf_sha256=digest(retained), retained_proof_sha256=digest(proof))
            if checked["verified"]:
                report.update(status="PASS_COLD_REBUILD_RETAINED_INPUTS_AND_DRAT", selection=selected,
                              positive_selector_cut={"terms": [[a, 1] for a in selected], "rhs": 59},
                              cut_requires_accepted_cold_owner=True, population_premise=60)
            else:
                report["status"] = "UNKNOWN_COLD_PROOF_UNVERIFIED"
    return report


def supervise(command, directory, deadline):
    """Own one process group, including any direct checker child."""
    started = time.monotonic()
    report = {"status": "UNKNOWN_BEFORE_CHILD", "child_reaped": False}
    save(directory / "supervisor.json", report)
    process = None
    with (directory / "child.stdout.log").open("xb") as out, (directory / "child.stderr.log").open("xb") as err:
        try:
            process = subprocess.Popen(command, stdout=out, stderr=err, cwd=ROOT, start_new_session=True)
            process.wait(timeout=max(0.001, deadline - time.monotonic()))
            report["status"] = ("UNKNOWN_HARD_DEADLINE" if time.monotonic() > deadline else
                                "CHILD_EXITED" if process.returncode == 0 else "ERROR_CHILD_EXIT")
        except subprocess.TimeoutExpired:
            report["status"] = "UNKNOWN_HARD_DEADLINE"
            save(directory / "supervisor.json", report)
        finally:
            if process is not None:
                if process.poll() is None:
                    save(directory / "supervisor.json", report)
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                process.wait()
                report.update(returncode=process.returncode, child_reaped=True, owned_process_group_stopped=True)
            report["seconds"] = time.monotonic() - started
            save(directory / "supervisor.json", report)
    return report


def worker(mode, config_path, preparation, saved_directory, directory, deadline):
    started, stages = time.monotonic(), []
    def stage(name):
        stages.append({"stage": name, "seconds": time.monotonic() - started,
                       "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss})
        save(directory / "stages.json", {"stages": stages})
        if time.monotonic() > deadline:
            raise TimeoutError("fixed exterior phase deadline")
    try:
        stage("started")
        if mode == "prepare":
            report = prepare(config_path, directory, deadline, stage)
        elif mode == "run":
            report = run(config_path, preparation, directory, deadline, stage)
        else:
            report = cold(config_path, preparation, saved_directory, directory, deadline, stage)
        report.update(seconds=time.monotonic() - started,
                      peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        save(directory / ("result.json" if mode == "run" else "report.json"), report)
    except Exception as error:
        save(directory / "error.json", {"type": type(error).__name__, "message": str(error)})
        raise


def owned(mode, config_path, directory, preparation=None, saved_directory=None):
    started = time.monotonic()
    limit = OWNER_SECONDS if mode == "run" else COLD_SECONDS if mode == "cold" else PREPARATION_SECONDS
    deadline = started + limit
    directory.mkdir(parents=True, exist_ok=False)
    command = [sys.executable, str(Path(__file__).resolve()), "_" + mode,
               "--configuration", str(config_path.resolve()), "--directory", str(directory.resolve()),
               "--deadline", str(deadline)]
    if preparation is not None:
        command += ["--preparation", str(preparation.resolve())]
    if saved_directory is not None:
        command += ["--saved-directory", str(saved_directory.resolve())]
    save(directory / "owner.json", {"status": "UNKNOWN_BEFORE_CHILD", "report_accepted": False})
    supervision = supervise(command, directory, deadline)
    owner = {"status": supervision["status"], "supervision": supervision, "report_accepted": False,
             "source_sha256": digest(__file__), "maximum_seconds": limit, "fixed_selection_excluded": False}
    path = directory / ("result.json" if mode == "run" else "report.json")
    if supervision["status"] == "CHILD_EXITED" and time.monotonic() <= deadline:
        report = json.loads(path.read_bytes())
        owner.update(status=report["status"], report_sha256=digest(path), report_accepted=True)
    owner.update(seconds=time.monotonic() - started, deadline_overrun_seconds=max(0, time.monotonic() - deadline))
    if owner["deadline_overrun_seconds"]:
        owner.update(status="UNKNOWN_HARD_DEADLINE", report_accepted=False)
    if mode == "cold" and owner["report_accepted"] and owner["status"] == "PASS_COLD_REBUILD_RETAINED_INPUTS_AND_DRAT":
        owner["fixed_selection_excluded"] = True
    save(directory / "owner.json", owner)
    if mode == "cold" and owner["report_accepted"] and owner["status"] == "PASS_COLD_REBUILD_RETAINED_INPUTS_AND_DRAT":
        save(directory / "certified-selector-cut.json", {
            "status": "CERTIFIED_FIXED_SELECTION_EXCLUSION", "cut": report["positive_selector_cut"],
            "population_premise": 60, "cold_report_sha256": digest(path),
            "accepted_cold_owner_sha256": digest(directory / "owner.json"),
            "run_result_sha256": report["run_result_sha256"], "run_owner_sha256": report["run_owner_sha256"],
            "scope": "One specified first-component incidence; the second component remains free.",
            "whole_component_excluded": False, "full_graph_constructed": False})
    print(json.dumps(owner, sort_keys=True), flush=True)


if __name__ == "__main__":
    if not __debug__:
        raise RuntimeError("assertions are required")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "run", "cold", "_prepare", "_run", "_cold"))
    parser.add_argument("--configuration", type=Path, required=True)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--preparation", type=Path)
    parser.add_argument("--saved-directory", type=Path)
    parser.add_argument("--deadline", type=float)
    args = parser.parse_args()
    if args.mode.startswith("_"):
        assert args.deadline is not None
        worker(args.mode[1:], args.configuration, args.preparation, args.saved_directory, args.directory, args.deadline)
    else:
        assert args.mode == "prepare" or args.preparation is not None
        assert args.mode != "cold" or args.saved_directory is not None
        owned(args.mode, args.configuration, args.directory, args.preparation, args.saved_directory)
