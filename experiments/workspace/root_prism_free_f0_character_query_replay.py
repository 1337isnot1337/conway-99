"""Cold model/preparation and terminal arithmetic replay; never a solve."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import time

from google.protobuf import text_format
from ortools.sat import cp_model_pb2, sat_parameters_pb2

import root_prism_free_f0_character_query as query

ROOT = Path(__file__).resolve().parents[2]
QUERY_SHA = "847d85ee005899924b3b79a094389a1a799de57c0e6e16f3f68721a8f24acee2"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def cold_model(preparation_path):
    assert sha(Path(query.__file__).read_bytes()) == QUERY_SHA
    preparation, preparation_sha = query.check_preparation(preparation_path)
    source = query.load_source("model")
    data = source.read_inputs()
    archive_info = preparation["definition"]["inputs"]["model_archive"]
    archive = (ROOT / archive_info["path"]).read_bytes()
    assert sha(archive) == archive_info["sha256"]
    raw = gzip.decompress(archive)
    assert sha(raw) == query.MODEL_SHA and len(raw) == 12498481
    proto = cp_model_pb2.CpModelProto()
    proto.ParseFromString(raw)
    checked = source.check_proto(proto, data)
    model_preparation = json.loads((ROOT / preparation["definition"]["inputs"]["model_preparation"]["path"]).read_bytes())
    assert checked == model_preparation["checks"]
    return preparation, preparation_sha, source, data, proto, checked


def replay(preparation_path, run_directory=None):
    started = time.monotonic()
    preparation, preparation_sha, source, data, proto, checked = cold_model(preparation_path)
    report = {"status": "PASS: cold query preflight", "replay_source_sha256": sha(Path(__file__).read_bytes()),
              "query_source_sha256": QUERY_SHA, "query_preparation_sha256": preparation_sha,
              "model_proto_sha256": query.MODEL_SHA, "literal_model_checks": checked,
              "optimizer_calls": 0, "CpSolver_constructed": False,
              "full_original28043_rows_retained": True, "original92_PSD_directions_retained": True,
              "graph_or_incidence_claimed": False, "F0_excluded": False}
    if run_directory is not None:
        raw = (run_directory / "result.json").read_bytes()
        result = json.loads(raw)
        supervision_raw = (run_directory / "supervisor.json").read_bytes()
        supervision = json.loads(supervision_raw)
        assert result["supervision"] == supervision
        assert result["runner_source_sha256"] == QUERY_SHA
        assert result["preparation_sha256"] == preparation_sha and result["model_proto_sha256"] == query.MODEL_SHA
        assert result["maximum_owned_child_seconds"] == 180 and not result["automatic_retry"]
        assert not result["graph_or_incidence_claimed"] and not result["F0_excluded"]
        assert supervision["child_reaped"]
        assert result["count_feasibility_claimed"] == (result["status"] == "EXACT_COUNT_WITNESS")
        artifacts = {}
        for name in ("child-result.json", "progress.json", "response.pbtxt", "candidate.json", "parameters.pbtxt",
                     "constructed-model.pb", "exact-point-check.json", "child.stdout.log", "child.stderr.log"):
            path = run_directory / name
            if path.exists():
                payload = path.read_bytes()
                artifacts[name] = {"sha256": sha(payload), "bytes": len(payload)}
        report.update(status="PASS: exact cold terminal replay", terminal_status=result["status"],
                      result_sha256=sha(raw), supervisor_sha256=sha(supervision_raw), artifacts=artifacts,
                      count_feasibility_claimed=result["count_feasibility_claimed"])
        if supervision["status"] == "CHILD_EXITED":
            assert supervision["returncode"] == 0
            child_raw = (run_directory / "child-result.json").read_bytes()
            assert sha(child_raw) == result["child_result_sha256"]
            child = json.loads(child_raw)
            assert child["status"] == result["status"]
            assert child["production_solve_calls"] == result["production_solve_calls"] in (0, 1)
            assert child["preparation_sha256"] == preparation_sha and child["model_proto_sha256"] == query.MODEL_SHA
            assert not child["F0_excluded"] and not child["graph_or_incidence_claimed"]
            assert artifacts["constructed-model.pb"]["sha256"] == query.MODEL_SHA
            if child["production_solve_calls"]:
                parameters_raw = (run_directory / "parameters.pbtxt").read_bytes()
                assert sha(parameters_raw) == child["parameters_sha256"]
                parameters = sat_parameters_pb2.SatParameters()
                text_format.Parse(parameters_raw.decode(), parameters)
                assert parameters.num_search_workers == 1 and parameters.random_seed == 0
                assert 0 < parameters.max_time_in_seconds <= 180
                assert parameters.max_time_in_seconds == child["native_max_time_seconds"]
                response_raw = (run_directory / "response.pbtxt").read_bytes()
                assert sha(response_raw) == child["response_sha256"]
                response = cp_model_pb2.CpSolverResponse()
                text_format.Parse(response_raw.decode(), response)
                assert response.status == child["native_status_code"]
                assert cp_model_pb2.CpSolverStatus.Name(response.status) == child["native_status"]
                if response.solution:
                    candidate_raw = (run_directory / "candidate.json").read_bytes()
                    assert sha(candidate_raw) == child["candidate_sha256"]
                    point = json.loads(candidate_raw)
                    assert point == list(response.solution) and all(type(v) is int for v in point)
                if result["status"] == "EXACT_COUNT_WITNESS":
                    assert response.status in (cp_model_pb2.FEASIBLE, cp_model_pb2.OPTIMAL)
                    assert len(point) == 18444
                    assert source.evaluate_proto(proto, point)
                    exact = source.inspect(point, data)
                    exact_raw = (run_directory / "exact-point-check.json").read_bytes()
                    assert sha(exact_raw) == child["exact_point_check_sha256"]
                    assert json.loads(exact_raw) == exact
                    report["all_native_constraints_evaluated_with_Python_integers"] = True
                    report["full_exact_point_check"] = exact
                elif result["status"] == "UNPROVED_NATIVE_INFEASIBLE":
                    assert response.status == cp_model_pb2.INFEASIBLE and not response.solution
                    report["infeasibility_remains_unproved"] = True
                elif result["status"] == "ERROR_NATIVE_MODEL_INVALID":
                    assert response.status == cp_model_pb2.MODEL_INVALID
                else:
                    assert result["status"] in ("UNKNOWN_NATIVE_LIMIT", "UNKNOWN_LATE_CHILD")
                    assert not result["count_feasibility_claimed"]
            else:
                assert result["status"] == "UNKNOWN_INITIALIZATION_LIMIT"
        else:
            assert supervision["status"] in ("UNKNOWN_HARD_DEADLINE", "ERROR_CHILD_EXIT", "ERROR_SUPERVISION")
            assert result["status"] == supervision["status"] and not result["count_feasibility_claimed"]
            report["partial_or_late_child_not_accepted"] = True
    report["seconds"] = time.monotonic() - started
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preparation", type=Path, required=True)
    parser.add_argument("--run-directory", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = replay(args.preparation, args.run_directory)
    with args.output.open("xb") as stream:
        stream.write(query.canonical(result) + b"\n")
    print(json.dumps(result, indent=2))
