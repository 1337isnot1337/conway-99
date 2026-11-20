"""Own one triangle-gap model preparation and separate complete protobuf replay.

All executed sources and inputs are bound by a root gate and request. Producer
modes own their child groups. This driver owns each independent checker worker.
No solver query, retry, producer import or mathematical constructor belongs here.
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
SUPERVISOR_SHA = "bbe476e5a7a13800c08265d4db541b7e8c7edf2277be03f6d06db134926891e3"
BASE_RAW_SHA = "56f6be31b4714825fb6d546ca79420e0ee0d25da05231a0eea322e514473bed8"
BASE_RAW_BYTES = 39512348
VARIABLES, ROWS = 80730, 303951
TOTAL_TERMS = 3340452
FAMILY_COUNTS = {"gap_triangle_zero": 3156}
FAMILY_TERMS = {"gap_triangle_zero": 3156}
LIMITS = {"controls_owner_seconds": 15, "prepare_owner_seconds": 135,
          "cold_controls_owner_seconds": 15, "cold_main_owner_seconds": 135,
          "driver_seconds": 420}
CONTROL_PASS = "PASS_TRIANGLE_GAP_MODEL_CONTROLS"
PREPARE_PASS = "PASS_COMPLETE_TRIANGLE_GAP_NATIVE_PREPARATION"
COLD_CONTROL_PASS = "PASS_TRIANGLE_GAP_INDEPENDENT_REPLAY_CONTROLS"
COLD_PASS = "PASS_INDEPENDENT_COMPLETE_TRIANGLE_GAP_NATIVE_MODEL"
COLD_OWNER_PASS = "PASS_TRIANGLE_GAP_EXTERNAL_COLD_REPLAY"
COLD_CONTROL_OWNER_PASS = "PASS_TRIANGLE_GAP_EXTERNAL_COLD_CONTROLS"


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


def owner_pass(owner, seconds, status):
    assert owner["status"] == status and owner["report_accepted"] is True
    assert owner["maximum_seconds"] == seconds and 0 <= owner["seconds"] <= seconds
    assert owner.get("deadline_overrun_seconds", 0) == 0
    assert owner["optimizer_calls"] == 0 and owner["CpSolver_constructed"] is False
    supervision = owner["supervision"]
    assert supervision["status"] == "CHILD_EXITED" and supervision["returncode"] == 0
    assert supervision["child_reaped"] is True and supervision["owned_process_group_stopped"] is True


def supervisor_module(ref):
    assert ref["sha256"] == SUPERVISOR_SHA
    read(ref)
    spec = importlib.util.spec_from_file_location("triangle_gap_ci_supervisor", resolve(ref["path"]))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def owned_cold(supervisor, request, directory, mode, command, seconds, report_path, expected_status):
    directory.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    owner = {"schema": "conway99.f0.triangle-gap-external-cold-owner.v1",
             "status": "UNKNOWN_BEFORE_CHILD", "mode": mode, "maximum_seconds": seconds,
             "report_accepted": False, "source": request["cold_source"],
             "configuration": request["configuration"], "root_gate": request["gate"],
             "automatic_retries": 0, "optimizer_calls": 0, "CpSolver_constructed": False,
             "graph_constructed": False, "whole_component_excluded": False}
    save(directory / "owned-start.json", owner)
    final_status = COLD_CONTROL_OWNER_PASS if mode == "controls" else COLD_OWNER_PASS
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
        assert report["native_model_builds"] == 0
        assert report["native_optimizer_constructed"] is False and report["native_query_run"] is False
        assert report["CpModel_constructed"] is False and report["CpSolver_constructed"] is False
        same_ref(report["source"], request["cold_source"])
        same_ref(report["configuration"], request["configuration"])
        assert report["maximum_seconds"] == (10 if mode == "controls" else 120)
        if mode == "replay":
            assert report["spectral_producer_or_literal_checker_imported"] is False
            assert report["native_transport_or_preparation_producer_imported"] is False
            assert report["variables"] == VARIABLES and report["rows"] == ROWS
            assert report["graph_constructed"] is False and report["whole_component_excluded"] is False
        owner.update(status=final_status, report=report_ref, report_accepted=True)
    except Exception as error:
        owner.update(status="ERROR_INDEPENDENT_TRIANGLE_GAP_MODEL_OWNER", report_accepted=False,
                     error={"type": type(error).__name__, "message": str(error),
                            "traceback": traceback.format_exc()})
    finally:
        elapsed = time.monotonic() - started
        owner.update(seconds=elapsed, deadline_overrun_seconds=max(0, elapsed - seconds))
        if owner["deadline_overrun_seconds"]:
            owner.update(status="UNKNOWN_INDEPENDENT_TRIANGLE_GAP_MODEL_OWNER_OVERRUN", report_accepted=False)
        save(directory / "owner.json", owner)
    owner_pass(owner, seconds, final_status)
    return owner


def run(args):
    started = time.monotonic()
    request_ref = binding(args.request)
    assert request_ref["sha256"] == args.request_sha256
    request = json.loads(read(request_ref))
    assert request["schema"] == "conway99.f0.triangle-gap-native-ci-request.v1"
    result_path = resolve(request["result_path"])
    assert not result_path.exists()
    dirs = {name: resolve(value) for name, value in request["directories"].items()}
    result = {"schema": "conway99.f0.triangle-gap-native-ci-result.v1",
              "status": "UNACCEPTED_TRIANGLE_GAP_MODEL_CI_PIPELINE", "driver": binding(__file__),
              "request": request_ref, "controls_invocations": 0, "prepare_invocations": 0,
              "cold_controls_invocations": 0, "cold_main_invocations": 0,
              "automatic_retries": 0, "optimizer_calls": 0, "native_query_run": False,
              "graph_constructed": False, "whole_component_excluded": False}
    try:
        assert request["mode"] == "one-preparation-and-independent-cold"
        assert request["limits"] == LIMITS and request["automatic_retries"] == 0
        assert request["native_model_builds_allowed"] == 1 and request["optimizer_calls_allowed"] == 0
        assert request["native_query_allowed"] is False and request["base_model_raw_sha256"] == BASE_RAW_SHA
        same_ref(request["driver_source"], binding(__file__))
        gate = json.loads(read(request["gate"]))
        assert gate["status"] == "AUTHORIZE_ONE_TRIANGLE_GAP_NATIVE_PREPARATION_AND_SEPARATE_COLD"
        assert gate["limits"] == LIMITS and gate["automatic_retries"] == 0
        assert gate["native_model_builds_allowed"] == 1 and gate["optimizer_calls_allowed"] == 0
        assert gate["native_query_allowed"] is False and gate["base_model_raw_sha256"] == BASE_RAW_SHA
        assert gate["variables"] == VARIABLES and gate["rows"] == ROWS
        for name in ("driver_source", "producer_source", "cold_source", "configuration", "supervisor_source"):
            same_ref(request[name], gate[name])
            read(request[name])
        assert request["supervisor_source"]["sha256"] == SUPERVISOR_SHA
        dependencies = gate["dependencies"]
        assert len({ref["path"] for ref in dependencies}) == len(dependencies)
        for ref in dependencies:
            read(ref)
        cfg = json.loads(read(request["configuration"]))
        assert cfg["schema"] == "conway99.f0.triangle-gap-native-configuration.v1"
        assert set(dirs) == {"controls", "prepare", "cold_controls", "cold_replay",
                             "cold_controls_owner", "cold_replay_owner"}
        values = list(dirs.values())
        assert len(set(values)) == len(values) and all(not p.exists() for p in values)
        for i, first in enumerate(values):
            assert first not in result_path.parents and result_path != first
            for second in values[i + 1:]:
                assert first not in second.parents and second not in first.parents
        result.update(root_gate=request["gate"], configuration=request["configuration"],
                      producer_source=request["producer_source"], cold_source=request["cold_source"])
        supervisor = supervisor_module(request["supervisor_source"])
        producer = resolve(request["producer_source"]["path"])
        cold = resolve(request["cold_source"]["path"])
        configuration = resolve(request["configuration"]["path"])
        for mode, status, seconds in (("controls", CONTROL_PASS, 15), ("prepare", PREPARE_PASS, 135)):
            assert LIMITS["driver_seconds"] - (time.monotonic() - started) >= seconds + 20
            command = [sys.executable, str(producer), mode, "--configuration", str(configuration),
                       "--configuration-sha256", request["configuration"]["sha256"],
                       "--directory", str(dirs[mode])]
            stdout = result_path.with_name(result_path.stem + "-" + mode + ".stdout.log")
            stderr = result_path.with_name(result_path.stem + "-" + mode + ".stderr.log")
            result_path.parent.mkdir(parents=True, exist_ok=True)
            with stdout.open("xb") as out, stderr.open("xb") as err:
                result[mode + "_invocations"] = 1
                completed = subprocess.run(command, stdout=out, stderr=err, cwd=ROOT, check=False)
            result[mode + "_owner_process"] = {"returncode": completed.returncode, "reaped": True,
                                              "stdout": binding(stdout), "stderr": binding(stderr)}
            assert completed.returncode == 0
            report_ref, owner_ref = binding(dirs[mode] / "report.json"), binding(dirs[mode] / "owner.json")
            report, owner = json.loads(read(report_ref)), json.loads(read(owner_ref))
            owner_pass(owner, seconds, status)
            same_ref(owner["report"], report_ref)
            for record in (owner, report):
                same_ref(record["source"], request["producer_source"])
                same_ref(record["configuration"], request["configuration"])
                assert record["optimizer_calls"] == 0 and record["CpSolver_constructed"] is False
            assert report["status"] == status and report["native_query_run"] is False
            assert report["native_optimizer_constructed"] is False
            assert report["CpModel_constructed"] is (mode == "prepare")
            if mode == "prepare":
                assert report["variables"] == VARIABLES and report["rows"] == ROWS
            result[mode + "_report"], result[mode + "_owner"] = report_ref, owner_ref
        result["native_model_builds"] = 1
        preparation = json.loads(read(result["prepare_report"]))
        assert LIMITS["driver_seconds"] - (time.monotonic() - started) >= 15 + 135 + 20
        controls_command = [sys.executable, str(cold), "controls", "--configuration", str(configuration),
                            "--configuration-sha256", request["configuration"]["sha256"],
                            "--directory", str(dirs["cold_controls"])]
        result["cold_controls_invocations"] = 1
        owned_cold(supervisor, request, dirs["cold_controls_owner"], "controls", controls_command, 15,
                   dirs["cold_controls"] / "report.json", COLD_CONTROL_PASS)
        result.update(cold_controls_report=binding(dirs["cold_controls"] / "report.json"),
                      cold_controls_owner=binding(dirs["cold_controls_owner"] / "owner.json"))
        command = [sys.executable, str(cold), "replay", "--configuration", str(configuration),
                   "--configuration-sha256", request["configuration"]["sha256"],
                   "--preparation-directory", str(dirs["prepare"]),
                   "--report-sha256", result["prepare_report"]["sha256"],
                   "--owner-sha256", result["prepare_owner"]["sha256"],
                   "--directory", str(dirs["cold_replay"])]
        assert LIMITS["driver_seconds"] - (time.monotonic() - started) >= 135 + 20
        result["cold_main_invocations"] = 1
        owned_cold(supervisor, request, dirs["cold_replay_owner"], "replay", command, 135,
                   dirs["cold_replay"] / "report.json", COLD_PASS)
        cold_report_ref = binding(dirs["cold_replay"] / "report.json")
        cold_report = json.loads(read(cold_report_ref))
        same_ref(cold_report["preparation_report"], result["prepare_report"])
        same_ref(cold_report["preparation_owner"], result["prepare_owner"])
        for record in (preparation, cold_report):
            assert record["total_terms"] == TOTAL_TERMS
            assert record["family_counts"] == FAMILY_COUNTS and record["family_terms"] == FAMILY_TERMS
            assert record["preservation"]["complete_original_parent_bytes_recovered"] is True
            assert record["preservation"]["all_original_variable_messages_preserved"] is True
            assert record["preservation"]["all_original_constraint_messages_preserved"] is True
        assert cold_report["row_keys_sha256"] == preparation["row_keys_sha256"]
        assert cold_report["gap_check"] == preparation["gap_check"]
        assert cold_report["model_raw_sha256"] == preparation["model_raw_sha256"]
        assert cold_report["model_raw_bytes"] == preparation["model_raw_bytes"]
        assert cold_report["base_restoration_sha256"] == BASE_RAW_SHA
        assert cold_report["base_restoration_bytes"] == BASE_RAW_BYTES
        for ref in dependencies:
            read(ref)
        result.update(status="PASS_ONE_TRIANGLE_GAP_NATIVE_PREPARATION_AND_INDEPENDENT_COLD",
                      cold_report=cold_report_ref,
                      cold_owner=binding(dirs["cold_replay_owner"] / "owner.json"),
                      model_raw_sha256=preparation["model_raw_sha256"],
                      model_raw_bytes=preparation["model_raw_bytes"], variables=VARIABLES, rows=ROWS,
                      total_terms=TOTAL_TERMS, family_counts=FAMILY_COUNTS, family_terms=FAMILY_TERMS,
                      complete_base_restoration_checked=True, protected_dependencies_unchanged=True)
    except Exception as error:
        result.update(status="ERROR_TRIANGLE_GAP_MODEL_CI_PIPELINE",
                      error={"type": type(error).__name__, "message": str(error),
                             "traceback": traceback.format_exc()})
    finally:
        retained = []
        for name, directory in dirs.items():
            for filename in ("report.json", "owner.json", "error.json", "restoration-manifest.json",
                             "model.pb.gz", "suffix.pb.gz", "append-rows.json.gz",
                             "owned-start.json", "owned-supervision.json", "initial-owner.json",
                             "owned-receipt.json", "supervisor.json", "stages.json"):
                path = directory / filename
                if path.is_file():
                    retained.append(binding(path))
        result.update(retained_terminal_artifacts=retained, seconds=time.monotonic() - started,
                      maximum_seconds=LIMITS["driver_seconds"])
        if result["seconds"] >= LIMITS["driver_seconds"]:
            result["status"] = "UNKNOWN_TRIANGLE_GAP_MODEL_CI_DRIVER_OVERRUN"
        save(result_path, result)
        print(json.dumps(result, sort_keys=True), flush=True)
    if result["status"] != "PASS_ONE_TRIANGLE_GAP_NATIVE_PREPARATION_AND_INDEPENDENT_COLD":
        raise SystemExit(1)


if __name__ == "__main__":
    if not __debug__:
        raise RuntimeError("assertions are required")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--request-sha256", required=True)
    run(parser.parse_args())
