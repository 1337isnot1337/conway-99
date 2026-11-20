"""CI driver for one gated triangle-incidence query and one terminal replay.

The query owns its 720-second worker process group. Each independent cold child
has a separate, pinned process-group owner. This driver never prepares a model,
imports the query/cold implementation, constructs a solver, or retries a phase.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parents[2]
QUERY_SHA = "d7e5307f0554cc308dbdf26dd3225b3cdb9d2628b9261b9896bbb9698ec83d0e"
COLD_SHA = "303a8b8c7e032a6f4eaaeb5cc745fe087f55ce1d1e04ca56a32e1c3c041494e4"
SUPERVISOR_SHA = "bbe476e5a7a13800c08265d4db541b7e8c7edf2277be03f6d06db134926891e3"
VARIABLES, ROWS = 80730, 300795
LIMITS = {"query_owner_seconds": 720, "cold_controls_owner_seconds": 15,
          "cold_main_owner_seconds": 135, "driver_seconds": 900}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(item):
    return json.dumps(item, sort_keys=True, separators=(",", ":"), allow_nan=False).encode() + b"\n"


def resolve(relative):
    path = (ROOT / relative).resolve()
    path.relative_to(ROOT)
    return path


def read(ref):
    raw = resolve(ref["path"]).read_bytes()
    assert sha(raw) == ref["sha256"], ref["path"]
    assert "bytes" not in ref or len(raw) == ref["bytes"], ref["path"]
    return raw


def binding(path):
    path = Path(path).resolve()
    raw = path.read_bytes()
    return {"path": str(path.relative_to(ROOT)), "sha256": sha(raw), "bytes": len(raw)}


def same_ref(first, second):
    assert first["path"] == second["path"] and first["sha256"] == second["sha256"]
    for ref in (first, second):
        if "bytes" in ref:
            assert resolve(ref["path"]).stat().st_size == ref["bytes"]


def save(path, item):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(canonical(item))


def owner_pass(owner, limit):
    assert owner["report_accepted"] is True and owner["maximum_seconds"] == limit
    assert 0 <= owner["seconds"] <= limit and owner.get("deadline_overrun_seconds", 0) == 0
    supervision = owner["supervision"]
    assert supervision["status"] == "CHILD_EXITED" and supervision["returncode"] == 0
    assert supervision["child_reaped"] is True and supervision["owned_process_group_stopped"] is True


def supervisor_module(ref):
    assert ref["sha256"] == SUPERVISOR_SHA
    read(ref)
    spec = importlib.util.spec_from_file_location("strengthened_query_ci_supervisor", resolve(ref["path"]))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def owned_cold(supervisor, request, cold_directory, mode, command, seconds, report_path, expected_status):
    directory = cold_directory / mode
    directory.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    owner = {"schema": "conway99.f0.triangle-incidence-query-independent-ci-owner.v1",
             "status": "UNKNOWN_BEFORE_CHILD", "mode": mode, "maximum_seconds": seconds,
             "report_accepted": False, "source": request["terminal_cold_source"],
             "configuration": request["query_configuration"], "root_gate": request["query_gate"],
             "automatic_retries": 0, "optimizer_calls": 0, "CpSolver_constructed": False,
             "graph_constructed": False, "whole_component_excluded": False}
    save(directory / "owned-start.json", owner)
    try:
        supervision = supervisor.supervise(command, directory, started + seconds)
        save(directory / "owned-supervision.json", supervision)
        owner.update(status=supervision["status"], supervision=supervision,
                     preliminary_receipt=binding(directory / "owned-start.json"),
                     supervision_receipt=binding(directory / "owned-supervision.json"))
        assert supervision["status"] == "CHILD_EXITED" and supervision["returncode"] == 0
        assert supervision["child_reaped"] is True and supervision["owned_process_group_stopped"] is True
        assert time.monotonic() - started <= seconds
        report_ref = binding(report_path)
        report = json.loads(read(report_ref))
        assert report["status"] == expected_status and report["optimizer_calls"] == 0
        assert report["producer_imports"] == report["native_imports"] == 0
        assert report["CpModel_constructed"] is False and report["CpSolver_constructed"] is False
        if mode == "run":
            same_ref(report["source"], request["terminal_cold_source"])
            same_ref(report["configuration"], request["query_configuration"])
            same_ref(report["root_gate"], request["query_gate"])
            assert report["maximum_seconds"] == 120
            assert report["graph_constructed"] is False and report["whole_component_excluded"] is False
        owner.update(status=expected_status, report=report_ref, report_accepted=True)
    except Exception as error:
        owner.update(status="ERROR_INDEPENDENT_QUERY_COLD_OWNER", report_accepted=False,
                     error={"type": type(error).__name__, "message": str(error), "traceback": traceback.format_exc()})
    finally:
        owner.update(seconds=time.monotonic() - started,
                     deadline_overrun_seconds=max(0, time.monotonic() - started - seconds))
        if owner["deadline_overrun_seconds"]:
            owner.update(status="UNKNOWN_INDEPENDENT_QUERY_COLD_OWNER_OVERRUN", report_accepted=False)
        save(directory / "owner.json", owner)
    owner_pass(owner, seconds)
    return owner


def run(args):
    started = time.monotonic()
    request_ref = binding(args.request)
    assert request_ref["sha256"] == args.request_sha256
    request = json.loads(read(request_ref))
    assert request["schema"] == "conway99.f0.triangle-incidence-query-ci-request.v1"
    report_path = resolve(request["driver_report"])
    assert not report_path.exists()
    query_directory, cold_directory = resolve(request["query_directory"]), resolve(request["cold_directory"])
    result = {"schema": "conway99.f0.triangle-incidence-query-ci-result.v1",
              "status": "UNACCEPTED_QUERY_CI_PIPELINE", "source": binding(__file__), "request": request_ref,
              "query_invocations": 0, "cold_controls_invocations": 0, "cold_main_invocations": 0,
              "automatic_retries": 0, "maximum_native_calls": 1, "driver_optimizer_calls": 0,
              "model_preparations": 0, "graph_constructed": False, "whole_component_excluded": False}
    try:
        assert request["maximum_native_calls"] == 1 and request["automatic_retries"] == 0
        assert request["limits"] == LIMITS
        same_ref(request["source"], binding(__file__))
        assert request["query_source"]["sha256"] == QUERY_SHA
        assert request["terminal_cold_source"]["sha256"] == COLD_SHA
        # The exact future configuration is bound by the root gate below.
        assert request["supervisor_source"]["sha256"] == SUPERVISOR_SHA
        for name in ("source", "query_source", "terminal_cold_source", "query_configuration",
                     "query_gate", "preflight_report", "preflight_owner", "supervisor_source"):
            read(request[name])
        cfg = json.loads(read(request["query_configuration"]))
        gate = json.loads(read(request["query_gate"]))
        assert cfg["schema"] == "conway99.f0.triangle-incidence-query-configuration.v1"
        assert cfg["variables"] == VARIABLES and cfg["rows"] == ROWS
        assert cfg["source_sha256"] == QUERY_SHA and cfg["maximum_native_calls"] == 1 and cfg["automatic_retries"] == 0
        assert cfg["model_raw_sha256"] == request["model_raw_sha256"] and cfg["native_query_authorized_by_configuration_alone"] is False
        assert gate["status"] == "AUTHORIZE_ONE_TRIANGLE_INCIDENCE_MODEL_QUERY"
        for gate_key, request_key in (("source", "query_source"), ("configuration", "query_configuration"),
                                     ("terminal_cold_source", "terminal_cold_source"), ("ci_driver_source", "source"),
                                     ("preflight_report", "preflight_report"), ("preflight_owner", "preflight_owner")):
            same_ref(gate[gate_key], request[request_key])
        same_ref(gate["model_cold"], cfg["inputs"]["model_cold"])
        same_ref(cfg["sources"]["supervisor"], request["supervisor_source"])
        assert gate["model_raw_sha256"] == request["model_raw_sha256"] and gate["parameters"] == cfg["parameters"]
        assert gate["limits"] == cfg["limits"] and gate["maximum_native_calls"] == 1 and gate["automatic_retries"] == 0
        assert gate["independent_terminal_cold_required"] is True
        preflight_directory = resolve(request["preflight_directory"])
        same_ref(request["preflight_report"], binding(preflight_directory / "report.json"))
        same_ref(request["preflight_owner"], binding(preflight_directory / "owner.json"))
        preflight, pre_owner = json.loads(read(request["preflight_report"])), json.loads(read(request["preflight_owner"]))
        assert preflight["status"] == pre_owner["status"] == "PASS_TRIANGLE_INCIDENCE_QUERY_PREFLIGHT"
        owner_pass(pre_owner, 75)
        same_ref(pre_owner["report"], request["preflight_report"])
        for record in (preflight, pre_owner):
            same_ref(record["source"], request["query_source"])
            same_ref(record["configuration"], request["query_configuration"])
            assert record["optimizer_calls"] == record["production_solve_calls"] == 0
            assert record["CpSolver_constructed"] is False
        assert preflight["model_raw_sha256"] == request["model_raw_sha256"]
        assert query_directory != cold_directory and not query_directory.exists() and not cold_directory.exists()
        assert preflight_directory not in (query_directory, cold_directory)
        for first, second in ((query_directory, cold_directory), (query_directory, preflight_directory),
                              (cold_directory, preflight_directory)):
            assert first not in second.parents and second not in first.parents
        assert query_directory not in report_path.parents and cold_directory not in report_path.parents
        supervisor = supervisor_module(request["supervisor_source"])
        query_command = [sys.executable, str(resolve(request["query_source"]["path"])), "run",
                         "--configuration", str(resolve(request["query_configuration"]["path"])),
                         "--directory", str(query_directory), "--preparation", str(preflight_directory),
                         "--gate", str(resolve(request["query_gate"]["path"])),
                         "--gate-sha256", request["query_gate"]["sha256"]]
        result.update(query_source=request["query_source"], terminal_cold_source=request["terminal_cold_source"],
                      configuration=request["query_configuration"], query_gate=request["query_gate"],
                      preflight_report=request["preflight_report"], preflight_owner=request["preflight_owner"])
        stdout = report_path.with_name(report_path.stem + "-query.stdout.log")
        stderr = report_path.with_name(report_path.stem + "-query.stderr.log")
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with stdout.open("xb") as out, stderr.open("xb") as err:
            result["query_invocations"] = 1
            # The frozen query runner supplies its own 720-second process-group
            # owner. subprocess.run waits for and reaps that owner process.
            completed = subprocess.run(query_command, stdout=out, stderr=err, cwd=ROOT, check=False)
        result.update(query_owner_process_returncode=completed.returncode, query_owner_process_reaped=True,
                      query_stdout=binding(stdout), query_stderr=binding(stderr))
        assert completed.returncode == 0
        query_result_ref, query_owner_ref = binding(query_directory / "result.json"), binding(query_directory / "owner.json")
        query_result, query_owner = json.loads(read(query_result_ref)), json.loads(read(query_owner_ref))
        owner_pass(query_owner, 720)
        same_ref(query_owner["report"], query_result_ref)
        same_ref(query_result["root_gate"], request["query_gate"])
        assert query_owner["mode"] == "run" and query_result["status"] == query_owner["status"]
        for record in (query_result, query_owner):
            same_ref(record["source"], request["query_source"])
            same_ref(record["configuration"], request["query_configuration"])
            assert record["graph_constructed"] is False and record["whole_component_excluded"] is False
        assert query_result["production_solve_calls"] in (0, 1)
        assert query_result["optimizer_calls"] == query_owner["optimizer_calls"] == query_result["production_solve_calls"]
        result.update(query_result=query_result_ref, query_owner=query_owner_ref,
                      query_outcome_status=query_result["status"], native_calls=query_result["production_solve_calls"])
        cold_directory.mkdir(parents=True, exist_ok=False)
        cold_source = resolve(request["terminal_cold_source"]["path"])
        controls_output = cold_directory / "controls.json"
        result["cold_controls_invocations"] = 1
        owned_cold(supervisor, request, cold_directory, "controls",
                   [sys.executable, str(cold_source), "controls", "--output", str(controls_output)], 15,
                   controls_output, "PASS_TRIANGLE_INCIDENCE_QUERY_INDEPENDENT_INTEGER_AND_RESPONSE_CONTROLS")
        result.update(cold_controls=binding(controls_output),
                      cold_controls_owner=binding(cold_directory / "controls" / "owner.json"))
        cold_output = cold_directory / "report.json"
        cold_command = [sys.executable, str(cold_source), "run",
                        "--configuration", str(resolve(request["query_configuration"]["path"])),
                        "--configuration-sha256", request["query_configuration"]["sha256"],
                        "--directory", str(query_directory), "--result-sha256", query_result_ref["sha256"],
                        "--owner-sha256", query_owner_ref["sha256"],
                        "--gate", str(resolve(request["query_gate"]["path"])), "--gate-sha256", request["query_gate"]["sha256"],
                        "--output", str(cold_output)]
        result["cold_main_invocations"] = 1
        owned_cold(supervisor, request, cold_directory, "run", cold_command, 135, cold_output,
                   "PASS_INDEPENDENT_TRIANGLE_INCIDENCE_QUERY_TERMINAL_REPLAY")
        cold_report = json.loads(cold_output.read_bytes())
        same_ref(cold_report["query_result"], query_result_ref)
        same_ref(cold_report["query_owner"], query_owner_ref)
        assert cold_report["query_native_calls"] == query_result["production_solve_calls"]
        assert cold_report["native_answer_classification"] == query_result["status"]
        result.update(status="PASS_ONE_BOUNDED_QUERY_AND_INDEPENDENT_TERMINAL_REPLAY",
                      cold_report=binding(cold_output), cold_owner=binding(cold_directory / "run" / "owner.json"),
                      returned_vectors_independently_checked=cold_report["returned_vectors_independently_checked"],
                      original_pair_caps_checked=False, second_component_completion_checked=False,
                      native_INFEASIBLE_is_unproved=True)
    except Exception as error:
        result.update(status="ERROR_QUERY_CI_PIPELINE",
                      error={"type": type(error).__name__, "message": str(error), "traceback": traceback.format_exc()})
    finally:
        retained = []
        for directory, names in ((query_directory, ("result.json", "owner.json", "error.json", "response-native.pbtxt",
                                                     "response-reconstructed.pb", "native-vectors.json")),
                                 (cold_directory, ("controls.json", "report.json", "report.json.error.json",
                                                   "controls/owner.json", "run/owner.json"))):
            for name in names:
                path = directory / name
                if path.is_file():
                    retained.append(binding(path))
        result.update(retained_terminal_artifacts=retained, seconds=time.monotonic() - started,
                      maximum_seconds=LIMITS["driver_seconds"])
        if result["seconds"] >= LIMITS["driver_seconds"]:
            result["status"] = "UNKNOWN_QUERY_CI_DRIVER_BUDGET_OVERRUN"
        save(report_path, result)
        print(json.dumps(result, sort_keys=True), flush=True)
    if result["status"] != "PASS_ONE_BOUNDED_QUERY_AND_INDEPENDENT_TERMINAL_REPLAY":
        raise SystemExit(1)


if __name__ == "__main__":
    if not __debug__:
        raise RuntimeError("assertions are required")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--request-sha256", required=True)
    run(parser.parse_args())
