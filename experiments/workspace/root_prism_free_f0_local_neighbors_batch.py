"""One bounded batch for the 41 unqueried F0 local-neighbor models.

An owned child gets at most five wall seconds, including imports and loading.
The parent launches no child after its sixty-second batch deadline. A separate
cold replay rebuilds every formula; only checked DRAT can produce selector zeros.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
import threading
import time

ROOT = Path(__file__).resolve().parents[2]
BUILDER = "experiments/workspace/root_prism_free_f0_local_neighbors.py"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def save(path, value):
    temporary = path.with_suffix(path.suffix+".tmp")
    temporary.write_text(json.dumps(value, indent=2)+"\n")
    temporary.replace(path)


def import_builder(expected):
    assert sha((ROOT/BUILDER).read_bytes()) == expected
    spec = importlib.util.spec_from_file_location("frozen_local41_builder", ROOT/BUILDER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def configuration(models):
    models = models.resolve()
    raw = (models/"preparation.json").read_bytes()
    index = json.loads(raw)
    assert index["status"] == "COMPLETE_41_LOCAL_MODELS_NO_PRODUCTION_QUERY"
    assert index["new_representatives"] == 41 and index["all_representatives"] == 42
    assert index["all_literal_centers_covered"] == 480 and index["new_literal_centers_covered"] == 468
    assert index["centers"][0] == 336 and 355 not in index["centers"]
    assert len(index["centers"]) == len(set(index["centers"])) == 41
    assert [x["center"] for x in index["models"]] == index["centers"]
    assert index["production_queries"] == 0 and not index["matching_constraints_added"]
    assert index["quotient_equalities_imposed"] == 0
    assert sha((ROOT/BUILDER).read_bytes()) == index["builder_source_sha256"]
    assert sha((ROOT/index["encoder"]["path"]).read_bytes()) == index["encoder"]["sha256"]
    for entry in index["models"]:
        for name, key in (("instance.json", "instance_file_sha256"), ("model.json", "model_file_sha256"),
                          ("model.cnf", "cnf_sha256")):
            assert sha((models/entry["directory"]/name).read_bytes()) == entry[key]
    return {"schema": "conway99.f0-local41-batch-preparation.v1",
            "runner_source_sha256": sha(Path(__file__).read_bytes()),
            "builder": {"path": BUILDER, "sha256": index["builder_source_sha256"]},
            "models_directory": str(models.relative_to(ROOT)), "models_preparation_sha256": sha(raw),
            "ordered_centers": index["centers"], "reused_center": 355,
            "reused_result_binding": index["inputs"]["old_result"],
            "reused_replay_binding": index["inputs"]["old_replay"],
            "maximum_seconds_per_child": 5, "maximum_batch_seconds": 60,
            "maximum_production_solve_calls": 41, "maximum_calls_per_center": 1,
            "solver": "Glucose4", "proof_enabled": True, "threads_per_child": 1,
            "child_deadline_includes_imports_loading_initialization_and_raw_writes": True,
            "batch_deadline_includes_parent_native_checks": True,
            "preflight_file_hash_checks_outside_batch_clock": True,
            "UNKNOWN_persisted_before_kill_and_reap": True,
            "partial_proofs_never_accepted": True, "matching_constraints_added": False,
            "literal_neighbor_bits_untied": True,
            "UNSAT_requires_fresh_CNF_and_separate_DRAT_check": True,
            "scope": "Complete 41 unqueried local projections; SAT is not graph completion."}


def supervise(command, directory, deadline):
    started = time.monotonic()
    report = {"status": "UNKNOWN_BEFORE_CHILD", "production_outcome_accepted": False}
    save(directory/"supervisor.json", report)
    process = None
    with (directory/"child.stdout.log").open("wb") as out, (directory/"child.stderr.log").open("wb") as err:
        try:
            process = subprocess.Popen(command, stdout=out, stderr=err, cwd=ROOT)
            left = deadline-time.monotonic()
            if left <= 0:
                raise subprocess.TimeoutExpired(command, 0)
            process.wait(timeout=left)
            report["status"] = ("UNKNOWN_HARD_DEADLINE" if time.monotonic() > deadline else
                                "CHILD_EXITED" if process.returncode == 0 else "ERROR_CHILD_EXIT")
        except subprocess.TimeoutExpired:
            report["status"] = "UNKNOWN_HARD_DEADLINE"
            save(directory/"supervisor.json", report)
        except Exception as error:
            report.update(status="ERROR_SUPERVISION", error_type=type(error).__name__, message=str(error))
            save(directory/"supervisor.json", report)
            raise
        finally:
            if process is not None:
                if process.poll() is None:
                    if report["status"] == "UNKNOWN_BEFORE_CHILD":
                        report["status"] = "UNKNOWN_HARD_DEADLINE"
                    save(directory/"supervisor.json", report)
                    process.kill()
                process.wait()
                report.update(returncode=process.returncode, child_reaped=process.poll() is not None)
            report["seconds"] = time.monotonic()-started
            save(directory/"supervisor.json", report)
    return report


def read_case(conf, center):
    models = ROOT/conf["models_directory"]
    index_raw = (models/"preparation.json").read_bytes()
    assert sha(index_raw) == conf["models_preparation_sha256"]
    index = json.loads(index_raw)
    entry = next(x for x in index["models"] if x["center"] == center)
    sub = models/entry["directory"]
    raw, native_raw, model_raw = [(sub/name).read_bytes() for name in ("model.cnf", "instance.json", "model.json")]
    assert sha(raw) == entry["cnf_sha256"] and sha(native_raw) == entry["instance_file_sha256"]
    assert sha(model_raw) == entry["model_file_sha256"]
    return index, entry, json.loads(native_raw), json.loads(model_raw), raw


def worker(preparation, center, directory, deadline):
    started = time.monotonic()
    conf = json.loads(preparation.read_bytes())
    assert conf["runner_source_sha256"] == sha(Path(__file__).read_bytes())
    assert center in conf["ordered_centers"] and center != 355
    result = {"status": "UNKNOWN_BEFORE_INITIALIZATION", "center": center,
              "production_solve_calls": 0, "proof_enabled": True}
    try:
        _, entry, _, model, raw = read_case(conf, center)
        result["cnf_sha256"] = entry["cnf_sha256"]
        import pysat
        from pysat.formula import CNF
        from pysat.solvers import Glucose4
        assert pysat.__version__ == model["pysat_version"]
        cnf = CNF(from_string=raw.decode())
        assert cnf.nv == entry["total_variables"] and len(cnf.clauses) == entry["clauses"]
        if time.monotonic() >= deadline:
            result["status"] = "UNKNOWN_INITIALIZATION_LIMIT"
        else:
            with Glucose4(bootstrap_with=cnf.clauses, with_proof=True) as solver:
                result["initialization_seconds"] = time.monotonic()-started
                left = deadline-time.monotonic()
                if left <= 0.05:
                    result["status"] = "UNKNOWN_INITIALIZATION_LIMIT"
                else:
                    timer = threading.Timer(max(0.001, left-0.05), solver.interrupt)
                    timer.daemon = True
                    timer.start()
                    search_started = time.monotonic()
                    try:
                        result["production_solve_calls"] = 1
                        answer = solver.solve_limited(expect_interrupt=True)
                    finally:
                        timer.cancel()
                        timer.join()
                    result["search_seconds"] = time.monotonic()-search_started
                    if answer is True:
                        artifact = canonical(solver.get_model())+b"\n"
                        (directory/"assignment.json").write_bytes(artifact)
                        result.update(status="RAW_SAT", assignment_sha256=sha(artifact))
                    elif answer is False:
                        lines = solver.get_proof()
                        assert isinstance(lines, list) and all(isinstance(s, str) for s in lines)
                        artifact = ("\n".join(lines)+("\n" if lines else "")).encode()
                        (directory/"proof.drat").write_bytes(artifact)
                        result.update(status="RAW_UNSAT_UNVERIFIED", proof_sha256=sha(artifact), proof_bytes=len(artifact))
                    else:
                        assert answer is None
                        result["status"] = "UNKNOWN_INTERRUPTED"
    except Exception as error:
        result.update(status="ERROR_NO_VALIDATED_OUTCOME", error_type=type(error).__name__, message=str(error))
        raise
    finally:
        result["worker_seconds"] = time.monotonic()-started
        save(directory/"child-result.json", result)


def exact_sat(builder, instance, core, raw, variables, assignment):
    from pysat.formula import CNF
    literals = set(assignment)
    assert all(type(v) is int and 1 <= abs(v) <= variables for v in assignment)
    assert len(literals) == len(assignment) and not any(-v in literals for v in literals)
    assert all((v in literals) != (-v in literals) for v in range(1, variables+1))
    cnf = CNF(from_string=raw.decode())
    assert cnf.nv == variables and all(any(v in literals for v in row) for row in cnf.clauses)
    selected = [v for v in range(1, instance["primitive_variables"]+1) if v in literals]
    return builder.inspect(instance, core, selected)

def run(conf, preparation, directory, preflight_seconds):
    assert not directory.exists()
    directory.mkdir(parents=True)
    builder = import_builder(conf["builder"]["sha256"])
    records, attempted = [], []
    started = time.monotonic()
    deadline = started+60
    result = {"status": "INCOMPLETE_BATCH", "centers": conf["ordered_centers"],
              "records": records, "attempted_centers": attempted,
              "selector_zeros_claimed": [], "graph_completion_claimed": False,
              "runner_source_sha256": conf["runner_source_sha256"],
              "query_preparation_sha256": sha(preparation.read_bytes()),
              "models_preparation_sha256": conf["models_preparation_sha256"],
              "preflight_hash_validation_seconds": preflight_seconds}
    save(directory/"result.json", result)
    try:
        for center in conf["ordered_centers"]:
            if time.monotonic() >= deadline:
                break
            sub = directory/("center-"+str(center))
            sub.mkdir()
            attempted.append(center)
            save(directory/"result.json", result)
            case_deadline = min(deadline, time.monotonic()+5)
            command = [sys.executable, str(Path(__file__).resolve()), "_worker",
                       "--preparation", str(preparation.resolve()), "--center", str(center),
                       "--directory", str(sub.resolve()), "--deadline", str(case_deadline)]
            supervision = supervise(command, sub, case_deadline)
            record = {"center": center, "supervisor": supervision,
                      "status": supervision["status"], "accepted_proof": False}
            if supervision["status"] == "CHILD_EXITED":
                child_raw = (sub/"child-result.json").read_bytes()
                child = json.loads(child_raw)
                index, entry, instance, model, raw = read_case(conf, center)
                assert child["center"] == center and child["cnf_sha256"] == entry["cnf_sha256"]
                assert child["production_solve_calls"] in (0, 1)
                record.update(child_result_sha256=sha(child_raw), production_solve_calls=child["production_solve_calls"],
                              initialization_seconds=child.get("initialization_seconds"),
                              search_seconds=child.get("search_seconds"))
                if child["status"] == "RAW_SAT":
                    assignment_raw = (sub/"assignment.json").read_bytes()
                    assert sha(assignment_raw) == child["assignment_sha256"]
                    witness = exact_sat(builder, instance, index["core_rows"], raw, model["total_variables"],
                                        json.loads(assignment_raw))
                    record.update(status="SAT_EXACT_LOCAL_WITNESS", witness=witness,
                                  assignment_sha256=sha(assignment_raw))
                elif child["status"] == "RAW_UNSAT_UNVERIFIED":
                    proof = (sub/"proof.drat").read_bytes()
                    assert sha(proof) == child["proof_sha256"] and len(proof) == child["proof_bytes"]
                    record.update(status="SOLVER_UNSAT_AWAITING_CHECKED_PROOF",
                                  proof_sha256=sha(proof), proof_bytes=len(proof))
                else:
                    assert child["status"].startswith(("UNKNOWN", "ERROR"))
                    record["status"] = child["status"]
            records.append(record)
            result["seconds"] = time.monotonic()-started
            save(directory/"result.json", result)
            if record["status"].startswith("ERROR"):
                result["stop_reason"] = "child error; remaining centers left unqueried"
                break
        result["status"] = ("COMPLETE_BATCH_RECORD" if len(records) == 41 else
                            "PARTIAL_BATCH_ERROR" if "stop_reason" in result else
                            "PARTIAL_BATCH_BUDGET_EXHAUSTED")
    except Exception as error:
        result.update(status="ERROR_PARTIAL_BATCH_PRESERVED", error_type=type(error).__name__, message=str(error))
        raise
    finally:
        result["unqueried_centers"] = conf["ordered_centers"][len(attempted):]
        result["seconds"] = time.monotonic()-started
        result["completed_center_records"] = len(records)
        result["SAT_centers"] = [r["center"] for r in records if r["status"] == "SAT_EXACT_LOCAL_WITNESS"]
        result["unverified_UNSAT_centers"] = [r["center"] for r in records if r["status"] == "SOLVER_UNSAT_AWAITING_CHECKED_PROOF"]
        save(directory/"result.json", result)
        print(json.dumps({k: v for k, v in result.items() if k != "records"}, indent=2))


def replay(conf, preparation, run_directory, directory, checker, seconds):
    assert not directory.exists() and 0 < seconds <= 60
    directory.mkdir(parents=True)
    started = time.monotonic()
    deadline = started+seconds
    reports = []
    report = {"status": "INCOMPLETE_REPLAY", "records": reports, "production_solver_calls": 0,
              "selector_zeros_from_checked_proofs": [], "graph_completion_claimed": False}
    save(directory/"result.json", report)
    try:
        raw_result = (run_directory/"result.json").read_bytes()
        saved = json.loads(raw_result)
        assert saved["runner_source_sha256"] == conf["runner_source_sha256"]
        assert saved["query_preparation_sha256"] == sha(preparation.read_bytes())
        assert saved["models_preparation_sha256"] == conf["models_preparation_sha256"]
        assert saved["centers"] == conf["ordered_centers"] and not saved["selector_zeros_claimed"]
        centers = [r["center"] for r in saved["records"]]
        assert centers == conf["ordered_centers"][:len(centers)] and len(set(centers)) == len(centers)
        assert saved["attempted_centers"] == conf["ordered_centers"][:len(saved["attempted_centers"])]
        assert set(centers) <= set(saved["attempted_centers"])
        builder = import_builder(conf["builder"]["sha256"])
        before = time.monotonic()
        bundle = builder.load()
        report["input_initialization_seconds"] = time.monotonic()-before
        report["run_result_sha256"] = sha(raw_result)
        for center in conf["ordered_centers"]:
            if time.monotonic() >= deadline:
                raise TimeoutError("Cold replay deadline reached")
            instance, clauses, variables, raw, model = builder.build(bundle, center)
            index, entry, expected_native, expected_model, expected_raw = read_case(conf, center)
            assert instance == expected_native and model == expected_model and raw == expected_raw
            row = {"center": center, "fresh_native_and_CNF_rebuilt": True, "cnf_sha256": sha(raw)}
            saved_row = next((r for r in saved["records"] if r["center"] == center), None)
            if saved_row is None:
                row["status"] = ("UNKNOWN_INTERRUPTED_RECORD" if center in saved["attempted_centers"]
                                 else "UNQUERIED_MODEL_BOUND")
            elif saved_row["status"] == "SAT_EXACT_LOCAL_WITNESS":
                sub = run_directory/("center-"+str(center))
                assignment_raw = (sub/"assignment.json").read_bytes()
                assert sha(assignment_raw) == saved_row["assignment_sha256"]
                witness = exact_sat(builder, instance, bundle["core"], raw, variables, json.loads(assignment_raw))
                assert witness == saved_row["witness"]
                row.update(status="PASS_EXACT_SAT_REPLAY", witness=witness)
            elif saved_row["status"] == "SOLVER_UNSAT_AWAITING_CHECKED_PROOF":
                proof = run_directory/("center-"+str(center))/"proof.drat"
                assert sha(proof.read_bytes()) == saved_row["proof_sha256"]
                row.update(status="UNSAT_UNVERIFIED_NO_SELECTOR_ZERO", proof_sha256=saved_row["proof_sha256"])
                if checker is not None:
                    assert checker.is_file()
                    sub = directory/("center-"+str(center))
                    sub.mkdir()
                    cnf_path = sub/"model.cnf"
                    cnf_path.write_bytes(raw)
                    left = min(30, deadline-time.monotonic())
                    assert left > 0
                    process = subprocess.run([str(checker.resolve()), str(cnf_path.resolve()), str(proof.resolve())],
                                             capture_output=True, text=True, timeout=left, check=False)
                    log = process.stdout+process.stderr
                    (sub/"drat-check.log").write_text(log)
                    assert process.returncode == 0 and re.search(r"(?m)^s VERIFIED(?:\s|$)", process.stdout)
                    row.update(status="PASS_CHECKED_UNSAT_PROOF", checker_sha256=sha(checker.read_bytes()),
                               checker_log_sha256=sha(log.encode()),
                               excluded_center_orbit=instance["center_selector_orbit"])
                    report["selector_zeros_from_checked_proofs"] += instance["center_selector_orbit"]
            else:
                row["status"] = "UNKNOWN_OR_ERROR_NO_PROOF_ACCEPTED"
            reports.append(row)
            save(directory/"result.json", report)
        assert len(reports) == 41
        report["status"] = "PASS_COMPLETE_MODEL_AND_AVAILABLE_CERTIFICATE_REPLAY"
    except Exception as error:
        report.update(status="INCOMPLETE_REPLAY_NO_NEW_CLAIM", error_type=type(error).__name__, message=str(error))
        raise
    finally:
        report["seconds"] = time.monotonic()-started
        report["runner_source_sha256"] = conf["runner_source_sha256"]
        save(directory/"result.json", report)
        print(json.dumps({k: v for k, v in report.items() if k != "records"}, indent=2))


def prepare(models, preparation, controls_directory):
    assert not preparation.exists() and not controls_directory.exists()
    before = time.monotonic()
    conf = configuration(models)
    conf["preparation_initialization_seconds"] = time.monotonic()-before
    controls_directory.mkdir(parents=True)
    controls = []
    for name, command, limit, expected in (
        ("exit0", [sys.executable, "-c", "print('owned child control')"], 2, "CHILD_EXITED"),
        ("exit3", [sys.executable, "-c", "raise SystemExit(3)"], 2, "ERROR_CHILD_EXIT"),
        ("deadline", [sys.executable, "-c", "import time; time.sleep(10)"], 0.1, "UNKNOWN_HARD_DEADLINE")):
        sub = controls_directory/name
        sub.mkdir()
        control = supervise(command, sub, time.monotonic()+limit)
        assert control["status"] == expected and control["child_reaped"]
        controls.append({"name": name, **control})
    conf["supervisor_controls"] = controls
    conf["production_queries"] = 0
    save(preparation, conf)
    print(json.dumps({"status": "PREPARED_41_CENTER_BATCH_NO_QUERY",
                      "source_sha256": conf["runner_source_sha256"],
                      "preparation_sha256": sha(preparation.read_bytes()),
                      "centers": conf["ordered_centers"], "production_queries": 0}, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "run", "replay", "_worker"))
    parser.add_argument("--models", type=Path)
    parser.add_argument("--preparation", type=Path, required=True)
    parser.add_argument("--controls-directory", type=Path)
    parser.add_argument("--directory", type=Path)
    parser.add_argument("--run-directory", type=Path)
    parser.add_argument("--checker", type=Path)
    parser.add_argument("--center", type=int)
    parser.add_argument("--deadline", type=float)
    parser.add_argument("--seconds", type=float, default=60)
    args = parser.parse_args()
    if args.mode == "prepare":
        assert args.models is not None and args.controls_directory is not None
        prepare(args.models, args.preparation, args.controls_directory)
    elif args.mode == "_worker":
        worker(args.preparation, args.center, args.directory, args.deadline)
    else:
        before = time.monotonic()
        saved = json.loads(args.preparation.read_bytes())
        fresh = configuration(ROOT/saved["models_directory"])
        assert all(saved[k] == v for k, v in fresh.items())
        assert saved["production_queries"] == 0
        preflight = time.monotonic()-before
        if args.mode == "run":
            run(saved, args.preparation, args.directory, preflight)
        else:
            replay(saved, args.preparation, args.run_directory, args.directory, args.checker, args.seconds)


if __name__ == "__main__":
    main()
