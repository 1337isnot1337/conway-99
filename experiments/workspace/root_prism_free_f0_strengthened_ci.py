"""Run one frozen native preparation and a separately owned protobuf replay.

The workflow owns this driver. The frozen preparation and replay have separate
process groups and deadlines. This driver never constructs an optimizer.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode() + b"\n"


def read(ref):
    data = (ROOT / ref["path"]).read_bytes()
    assert sha(data) == ref["sha256"], ref["path"]
    assert "bytes" not in ref or len(data) == ref["bytes"], ref["path"]
    return data


def binding(path):
    path = Path(path).resolve()
    data = path.read_bytes()
    return {"path": str(path.relative_to(ROOT)), "sha256": sha(data), "bytes": len(data)}


def save(path, value):
    with path.open("xb") as stream:
        stream.write(canonical(value))


def module(ref):
    read(ref)
    spec = importlib.util.spec_from_file_location("strengthened_ci_supervisor", ROOT / ref["path"])
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def accepted_owner(path, status):
    owner = json.loads(path.read_bytes())
    assert owner["status"] == status and owner["report_accepted"] is True
    assert owner["optimizer_calls"] == 0 and owner["CpSolver_constructed"] is False
    supervision = owner["supervision"]
    assert supervision["status"] == "CHILD_EXITED" and supervision["returncode"] == 0
    assert supervision["child_reaped"] is True and supervision["owned_process_group_stopped"] is True
    assert owner["seconds"] <= owner["maximum_seconds"]
    return owner


def cold_step(supervisor, request, directory, mode, command, seconds, report_path, expected_status):
    step_directory = directory / mode
    step_directory.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    supervision = supervisor.supervise(command, step_directory, started + seconds)
    elapsed = time.monotonic() - started
    owner = {"schema": "conway99.f0.strengthened-independent-ci-owner.v1",
             "status": supervision["status"], "mode": mode, "supervision": supervision,
             "maximum_seconds": seconds, "seconds": elapsed, "report_accepted": False,
             "source": request["cold_source"], "configuration": request["configuration"],
             "optimizer_calls": 0, "CpSolver_constructed": False, "automatic_retries": 0}
    if (supervision["status"] == "CHILD_EXITED" and supervision["returncode"] == 0
            and supervision["child_reaped"] is True and supervision["owned_process_group_stopped"] is True
            and elapsed <= seconds and report_path.is_file()):
        report = json.loads(report_path.read_bytes())
        assert report["status"] == expected_status and report["optimizer_calls"] == 0
        owner.update(status=expected_status, report_accepted=True, report=binding(report_path))
    save(step_directory / "owner.json", owner)
    assert owner["report_accepted"], owner
    return owner


def run(request_path):
    request = json.loads(request_path.read_bytes())
    read(request["driver_source"])
    assert request["driver_source"]["sha256"] == sha(Path(__file__).read_bytes())
    gate = json.loads(read(request["gate"]))
    assert gate["status"] == "AUTHORIZE_ONE_STRENGTHENED_NATIVE_PREPARATION_AND_SEPARATE_COLD"
    assert gate["optimizer_calls_allowed"] == request["optimizer_calls_allowed"] == 0
    assert gate["native_query_allowed"] is False and request["native_query_allowed"] is False
    assert request["mode"] == "one-preparation-and-independent-cold"
    for name in ("driver_source", "producer_source", "cold_source", "configuration"):
        assert request[name] == gate[name]
        read(request[name])
    for ref in gate["dependencies"]:
        read(ref)
    cfg = json.loads(read(request["configuration"]))
    assert cfg["source_sha256"] == request["producer_source"]["sha256"]
    assert cfg["optimizer_calls"] == 0 and cfg["native_query_authorized"] is False
    supervisor = module(cfg["sources"]["supervisor"])
    configuration_path = ROOT / request["configuration"]["path"]
    producer = ROOT / request["producer_source"]["path"]
    cold = ROOT / request["cold_source"]["path"]
    dirs = {name: ROOT / value for name, value in request["directories"].items()}
    assert set(dirs) == {"controls", "prepare", "cold"}
    assert len(set(dirs.values())) == 3 and all(not p.exists() for p in dirs.values())
    result_path = ROOT / request["result_path"]
    assert not result_path.exists()
    started = time.monotonic()
    result = {"schema": "conway99.f0.strengthened-native-ci-result.v1",
              "request": binding(request_path), "driver": binding(__file__),
              "status": "UNACCEPTED_CI_PIPELINE", "optimizer_calls": 0,
              "native_query_run": False, "automatic_retries": 0}
    try:
        for mode, directory, status in (
            ("controls", dirs["controls"], "PASS_PUBLIC_NATIVE_TEXT_TRANSPORT_EXACT_BYTES_AND_INVALID_INDEX_REJECTION"),
            ("prepare", dirs["prepare"], "PASS_COMPLETE_STRENGTHENED_LITERAL_NATIVE_PREPARATION")):
            command = [sys.executable, str(producer), mode, "--configuration",
                       str(configuration_path), "--directory", str(directory)]
            subprocess.run(command, check=True)
            accepted_owner(directory / "owner.json", status)
        dirs["cold"].mkdir(parents=True, exist_ok=False)
        controls_output = dirs["cold"] / "controls.json"
        cold_step(supervisor, request, dirs["cold"], "controls",
                  [sys.executable, str(cold), "controls", "--output", str(controls_output)],
                  15, controls_output, "PASS_STRENGTHENED_APPEND_NATIVE_ROW_CONTROLS")
        preparation_report = binding(dirs["prepare"] / "report.json")
        preparation_owner = binding(dirs["prepare"] / "owner.json")
        cold_output = dirs["cold"] / "report.json"
        command = [sys.executable, str(cold), "run", "--configuration", str(configuration_path),
                   "--configuration-sha256", request["configuration"]["sha256"],
                   "--directory", str(dirs["prepare"]), "--report-sha256", preparation_report["sha256"],
                   "--owner-sha256", preparation_owner["sha256"], "--output", str(cold_output)]
        cold_step(supervisor, request, dirs["cold"], "run", command, 105,
                  cold_output, "PASS_INDEPENDENT_COMPLETE_STRENGTHENED_LITERAL_NATIVE_APPEND")
        result.update(status="PASS_ONE_NATIVE_PREPARATION_AND_INDEPENDENT_COLD",
                      preparation_report=preparation_report, preparation_owner=preparation_owner,
                      cold_report=binding(cold_output), cold_owner=binding(dirs["cold"] / "run" / "owner.json"),
                      controls_owner=binding(dirs["controls"] / "owner.json"),
                      cold_controls=binding(controls_output), native_model_builds=1)
    except Exception as error:
        result["error"] = {"type": type(error).__name__, "message": str(error)}
        raise
    finally:
        result["seconds"] = time.monotonic() - started
        save(result_path, result)
        print(json.dumps(result, sort_keys=True), flush=True)


if __name__ == "__main__":
    if not __debug__:
        raise RuntimeError("assertions are required")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", required=True, type=Path)
    run(parser.parse_args().request.resolve())
