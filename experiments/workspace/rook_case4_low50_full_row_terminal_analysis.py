"""Read-only terminal accounting; no matrix, numerical solve, or proof replay."""
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def reference(path):
    path = Path(path).resolve()
    raw = path.read_bytes()
    return {"path":str(path.relative_to(ROOT)),"bytes":len(raw),"sha256":hashlib.sha256(raw).hexdigest()}


def read(ref):
    path = ROOT/ref["path"]
    actual = reference(path)
    assert all(actual[k] == v for k,v in ref.items())
    return json.loads(path.read_bytes())


def inspect(directory,output):
    result_ref = reference(directory/"result.json")
    result = read(result_ref)
    cfg = read(result["configuration"])
    assert result["source_bindings"] == cfg["source_bindings"] and result["limits"] == cfg["limits"]
    forward_owner,cold_owner = read(result["forward_owner"]),read(result["cold_owner"])
    assert forward_owner["child_reaped"] and cold_owner["child_reaped"]
    cold = read(result["cold"]) if result["cold"] is not None else None
    accepted = bool(cold and cold["status"] == "PASS" and cold_owner["exit_code"] == 0 and not cold_owner["hard_timeout"])
    assert (result["status"] == "ACCEPTED_EXACT_PREFIX") == accepted
    forward_ref = reference(directory/"forward/result.json")
    forward = read(forward_ref)
    assert forward["configuration"] == result["configuration"] and forward["source_bindings"] == cfg["source_bindings"]
    raw = (directory/"forward/records.jsonl").read_bytes()
    complete,tail = raw.rsplit(b"\n",1) if b"\n" in raw else (b"",raw)
    refs = [json.loads(s) for s in complete.splitlines() if s]
    assert refs == forward["records"] and len(refs) <= forward["native_calls"] <= 50
    records,statuses,run_statuses = [],Counter(),Counter()
    native_sum = 0.0
    binary_bytes,bases,points,rays = 0,0,0,0
    for k,ref in enumerate(refs):
        record = read(ref)
        numeric = read(record["numeric"])
        assert record["low50_index"] == numeric["low50_index"] == k
        box = cfg["selected_whole_cover_indices"][k]
        assert record["whole_cover_box_index"] == numeric["whole_cover_box_index"] == box
        assert numeric["configuration"] == result["configuration"] and numeric["model"] == cfg["model"]
        assert reference(ROOT/numeric["arrays"]["path"]) == numeric["arrays"]
        assert numeric["extra_native_calls"] == 0 and (not numeric["getDualRay_called"] or numeric["existing_ray"])
        elapsed,requested = numeric["native_seconds"],numeric["requested_seconds"]
        assert math.isfinite(elapsed) and elapsed >= 0 and 0 < requested <= 2
        native_sum += elapsed
        statuses[numeric["model_status"]] += 1
        run_statuses[numeric["run_status"]] += 1
        binary_bytes += numeric["arrays"]["bytes"]
        bases += int(numeric["basis_valid"])
        points += int(numeric["solution_value_valid"])
        rays += int(numeric["complete_ray_saved"])
        if record["certificate"] is not None:
            read(record["certificate"])
        records.append({"low50_index":k,"whole_cover_box_index":box,"status":record["status"],
            "model_status":numeric["model_status"],"native_seconds":elapsed,"requested_seconds":requested,
            "basis_valid":numeric["basis_valid"],"numerical_values_saved":numeric["solution_value_valid"],
            "complete_ray_saved":numeric["complete_ray_saved"],"certificate":record["certificate"]})
    assert forward["cumulative_native_seconds"] >= native_sum
    if forward["native_calls"] == len(refs):
        assert forward["cumulative_native_seconds"] == native_sum
    measured_overrun = forward["seconds"] > cfg["limits"]["forward_seconds"] or forward["cumulative_native_seconds"] > cfg["limits"]["cumulative_native_seconds"]
    assert forward["resource_overrun"] == measured_overrun
    if accepted:
        assert cold["completed_native_records"] == len(refs) and cold["incomplete_transcript_tail_bytes"] == len(tail)
        assert result["exact_exclusions"] == cold["exact_exclusions"]
        assert result["new_global_zero_columns"] == cold["new_global_zero_columns"]
    report = {"status":"PASS_ARTIFACT_ONLY_TERMINAL_ACCOUNTING",
        "source":reference(Path(__file__)),"terminal":result_ref,"forward":forward_ref,
        "configuration":result["configuration"],"cold":result["cold"],
        "forward_owner":result["forward_owner"],"cold_owner":result["cold_owner"],
        "cold_prefix_accepted":accepted,"completed_native_records":len(refs),"native_calls":forward["native_calls"],
        "model_status_counts":dict(statuses),"run_status_counts":dict(run_statuses),
        "cumulative_native_seconds":forward["cumulative_native_seconds"],"cumulative_native_limit":120,
        "cumulative_native_overrun_seconds":max(0.0,forward["cumulative_native_seconds"]-120),
        "forward_seconds":forward["seconds"],"forward_owner_seconds":forward_owner["seconds"],
        "cold_seconds":cold["seconds"] if cold else None,"cold_owner_seconds":cold_owner["seconds"],
        "wrapper_seconds":result["seconds"],"peak_forward_RSS_KiB":forward["peak_rss_KiB"],
        "owner_timeouts":{"forward":forward_owner["hard_timeout"],"cold":cold_owner["hard_timeout"]},
        "new_exact_exclusions":result["exact_exclusions"],"new_global_zero_columns":result["new_global_zero_columns"],
        "all54_low_branches_excluded":result["all54_low_branches_excluded"],
        "unprocessed_whole_cover_indices":cfg["selected_whole_cover_indices"][len(refs):],
        "unqueried_high_boxes":137,"prior_four_exclusions_preserved":cfg["prior_four_low_exclusions"],
        "complete_numerical_bases":bases,"numerical_value_vectors":points,"complete_existing_rays":rays,
        "compressed_numeric_archive_bytes":binary_bytes,"incomplete_transcript_tail_bytes":len(tail),
        "branches":records,"no_numerical_feasibility_or_infeasibility_accepted":True,
        "full_matrix_loaded":False,"old_trace_replay_repeated":False,"proof_arithmetic_repeated":False,
        "optimizer_calls":0,"case4_excluded":False,"whole_graph_problem_resolved":False}
    assert not output.exists()
    output.write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args = parser.parse_args()
    report = inspect(args.directory.resolve(),args.output.resolve())
    print(json.dumps({k:report[k] for k in ("status","completed_native_records","new_exact_exclusions","cumulative_native_seconds","cumulative_native_overrun_seconds")}),flush=True)
