"""Independent integer replay for complete-row conditional box exclusions.

No subject module, native optimizer, numerical ray arithmetic, old trace
checker, or cover census is imported.  The frozen matrix prefix and complete
branch-cover receipts are bound before any conditional proof is accepted.
"""
import argparse
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[2]
CORE = ("coefficients","column_indices","row_pointers","row_lower","row_upper","original_column_ids")


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(",",":")).encode()


def reference(path):
    path = Path(path).resolve()
    assert path.is_relative_to(ROOT)
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda:stream.read(1024**2),b""):
            h.update(block)
    return {"path":str(path.relative_to(ROOT)),"bytes":path.stat().st_size,"sha256":h.hexdigest()}


def read(ref):
    path = ROOT/ref["path"]
    actual = reference(path)
    assert all(actual[k] == v for k,v in ref.items())
    raw = path.read_bytes()
    return json.loads(gzip.decompress(raw) if path.suffix == ".gz" else raw)


def integer(value):
    assert type(value) is str
    result = int(value)
    assert str(result) == value
    return result


def deadline_check(deadline):
    if time.monotonic() >= deadline:
        raise TimeoutError("full50 cold replay deadline")


def array_binding(value):
    assert value.ndim == 1 and value.flags.c_contiguous
    return {"dtype":str(value.dtype),"shape":list(value.shape),"sha256":sha(memoryview(value).cast("B"))}


def domain(config,deadline):
    import numpy as np
    for ref in config["source_bindings"].values():
        assert reference(ROOT/ref["path"]) == ref
    assert config["source_bindings"]["cold"] == reference(Path(__file__))
    assert config["status"] == "PREPARED_ONE_FULL50_CONDITIONAL_LP_BATCH_NO_SOLVE"
    assert config["production_queries"] == 0 and config["selected_branch_count"] == 50
    terminal = read(config["preflight_terminal"])
    assert terminal["status"] == "ACCEPTED_ZERO_SOLVE_PREFLIGHT" and terminal["accepted"]
    assert terminal["native_solver_calls"] == 0
    flight,owner,cfg = read(terminal["report"]),read(terminal["supervisor"]),read(terminal["configuration"])
    assert owner["exit_code"] == 0 and owner["child_reaped"] and not owner["hard_timeout"]
    assert flight["status"] == "PASS_COMPLETE_FULL50_NATIVE_TRANSPORT_AND_BOUND_RESETS_NO_SOLVE"
    assert flight["seconds"] <= 60 and flight["native_solver_calls"] == 0
    assert config["model"] == flight["matrix"] and config["arrays"] == flight["arrays"]
    model = read(config["model"])
    assert model["arrays"] == config["arrays"] and model["matrix_binding"] == config["matrix_binding"] == flight["matrix_binding"]
    assert (model["variables"],model["rows"],model["nonzeros"]) == (1103,167127,10769860)
    assert model["artificial_t_fixed_zero"] and model["all164044_retained_covers_preserved"]
    assert cfg["source_bindings"]["preflight"] == config["source_bindings"]["preflight"]
    assert cfg["source_bindings"]["transport"] == config["source_bindings"]["transport"]
    spec = read(cfg["inputs"]["small_spec"])
    old_cold = read(cfg["inputs"]["small_cold"])
    data = {name:read({"path":p,"sha256":h}) for name,(p,h) in spec["input_bindings"].items()}
    compact,box_cold,box_owner = data["boxes"],data["box_cold"],data["box_cold_owner"]
    assert box_cold["status"] == "PASS" and box_cold["checked"] == 260
    assert (box_cold["checked_fixed_points"],box_cold["checked_contradictions"],box_cold["checked_partial"]) == (191,69,0)
    assert box_cold["all260_nonpartial_branches_checked"]
    assert box_cold["prior184_contradictions_and_complete_original_branch_cover_bound"]
    assert box_owner["exit_code"] == 0 and box_owner["child_reaped"] and not box_owner["hard_timeout"]
    assert box_owner["child_result"]["sha256"] == spec["input_bindings"]["box_cold"][1]
    ids,zeros = spec["original_column_ids"],spec["proved_zero_columns"]
    assert ids == sorted(set(range(1214))-set(zeros)) and len(ids) == 1102 and len(zeros) == 112
    assert compact["original_column_ids"] == ids and compact["proved_zero_columns"] == zeros
    assert compact["boxes"] == spec["all191_boxes"] and len(compact["boxes"]) == 191
    assert ids == config["original_column_ids"] and zeros == config["proved_zero_columns"]
    assert config["branch_ancestor_bindings"] == spec["input_bindings"]
    # Independently expand the three original equalities defining each guard.
    native = data["native"]["primary_inventory"]["Gram_rows"]
    weights,rhs = [0]*1214,0
    for r in (214,344,582):
        _,_,demand,support = native[r]
        rhs += demand
        for a in support:
            weights[a] += 1
    assert rhs == 3
    positive = {a:weights[a] for a in ids if weights[a]}
    assert Counter(positive.values()) == {1:26,2:9,3:1}
    H,Q = [a for a in ids if weights[a] % 2],[a for a in ids if weights[a]//2]
    assert H == spec["partition"]["H27"] and Q == spec["partition"]["Q"]
    proof_refs = {b["index"]:b for b in compact["all260_proof_bindings"]}
    positions = {a:j for j,a in enumerate(ids)}
    low,high = [],[]
    for b in compact["boxes"]:
        s = b["state"]
        assert len(s) == 1102 and set(s) <= set("01?")
        assert sha(bytes(255 if v == "?" else int(v) for v in s)) == b["state_sha256"]
        assert all(s[positions[a]] != "?" for a in positive)
        selected = [a for a in positive if s[positions[a]] == "1"]
        assert selected == b["selected"] and sum(positive[a] for a in selected) == 3
        odd = sum(positive[a] % 2 for a in selected)
        assert odd in (1,3)
        if odd == 1:
            assert len(selected) in (1,2)
            low.append({**b,"pilot_index":len(low),"proof_binding":proof_refs[b["index"]]})
        else:
            high.append(b)
    assert len(low) == 54 and len(high) == 137 and low == spec["selected54_boxes"]
    assert old_cold["status"] == "PASS" and old_cold["exact_exclusions"] == len(old_cold["checks"]) == 4
    assert old_cold["completed_native_records"] == 54 and not old_cold["incomplete_transcript_tail_bytes"]
    excluded = {p["whole_cover_box_index"]:p for p in old_cold["checks"]}
    assert sorted(excluded) == [10,11,15,64]
    for b in low:
        if b["index"] in excluded:
            assert excluded[b["index"]]["nogood"] == {"terms":[[a,1] for a in b["selected"]],"upper":len(b["selected"])-1}
    branches = [b for b in low if b["index"] not in excluded]
    assert len(branches) == 50 and [b["index"] for b in branches] == config["selected_whole_cover_indices"]
    assert model["prior_branch_cold"] == cfg["inputs"]["small_cold"]
    # The whole original row/cover prefix already has an accepted exact replay.
    point,point_cold = read(cfg["inputs"]["old_point"]),read(cfg["inputs"]["old_point_cold"])
    assert point_cold["exact_point_replayed"] and point_cold["full_face_rows_checked"] == 167121
    assert point_cold["candidate_sha256"] == cfg["inputs"]["old_point"]["sha256"]
    assert model["old_exact_matrix_prefix"] == point["matrix_binding"]
    extra = [spec["rows"][r] for r in (2285,2286)]
    expected_extra = [(r["original_terms"],r["lower"],r["upper"]) for r in extra]
    expected_extra += [(p["nogood"]["terms"],0,1) for p in old_cold["checks"]]
    assert [(r["terms"],r["lower"],r["upper"]) for r in model["new_original_rows"]] == expected_extra
    assert reference(ROOT/config["arrays"]["path"]) == config["arrays"]
    arrays = {}
    with np.load(ROOT/config["arrays"]["path"],allow_pickle=False) as archive:
        assert set(archive.files) == set(CORE)
        for name in CORE:
            deadline_check(deadline)
            a = archive[name]
            assert a.dtype.kind in "iu"
            assert array_binding(a) == config["matrix_binding"][name]
            old = point["matrix_binding"][name]
            assert array_binding(a[:old["shape"][0]]) == old
            arrays[name] = a
    assert arrays["original_column_ids"].tolist() == ids
    for k,(terms,lower,upper) in enumerate(expected_extra):
        r = 167121+k
        begin,end = map(int,arrays["row_pointers"][r:r+2])
        restored = [[ids[int(arrays["column_indices"][p])],int(arrays["coefficients"][p])] for p in range(begin,end)]
        assert restored == terms and (int(arrays["row_lower"][r]),int(arrays["row_upper"][r])) == (lower,upper)
    return {"ids":ids,"zeros":zeros,"branches":branches,"Q":Q,"model":model,
        "arrays":arrays,"prior_excluded_indices":sorted(excluded)}


def certificate(proof,domain,branch,index,model_ref,deadline):
    assert proof["kind"] == "EXACT_FULL_ROW_CONDITIONAL_BOX_EXCLUSION"
    for name,value in (("low50_index",index),("whole_cover_box_index",branch["index"]),
        ("prior_branch_id",branch["prior_branch_id"]),("raw_pattern_id",branch["raw_id"]),
        ("state_sha256",branch["state_sha256"]),("cold_branch_proof",branch["proof_binding"]),
        ("preflight_model",model_ref)):
        assert proof[name] == value
    assert proof["proved_zero_columns"] == domain["zeros"] and proof["floor_bounds"] == [0,0]
    assert proof["coordinate_lift"] == "projected row combination representative modulo the 112 proved zero equalities"
    multipliers = [[r,integer(v)] for r,v in proof["row_multipliers"]]
    assert multipliers == sorted(multipliers) and len({r for r,v in multipliers}) == len(multipliers)
    arrays = domain["arrays"]
    vector,endpoint,terms = [0]*1214,0,0
    floor = 0
    for r,value in multipliers:
        deadline_check(deadline)
        assert type(r) is int and 0 <= r < 167127 and value != 0 and abs(value).bit_length() <= 4096
        endpoint += value*int(arrays["row_upper"][r] if value > 0 else arrays["row_lower"][r])
        start,end = int(arrays["row_pointers"][r]),int(arrays["row_pointers"][r+1])
        for k in range(start,end):
            j,c = int(arrays["column_indices"][k]),int(arrays["coefficients"][k])
            assert 0 <= j <= 1102
            if j == 1102:
                floor += value*c
            else:
                vector[domain["ids"][j]] += value*c
            terms += 1
            if terms % 8192 == 0:
                deadline_check(deadline)
    lower,upper = [0]*1214,[0]*1214
    for a,s in zip(domain["ids"],branch["state"]):
        lower[a],upper[a] = int(s == "1"),int(s != "0")
    minimum = sum(min(c*lo,c*hi) for c,lo,hi in zip(vector,lower,upper))
    assert minimum > endpoint
    assert all(abs(v).bit_length() <= 4096 for v in vector+[endpoint,minimum,floor])
    assert [str(v) for v in vector] == proof["full1214_coefficients"]
    assert str(floor) == proof["floor_coefficient"] and terms == proof["terms_contracted"]
    assert sha(canonical([lower,upper])) == proof["full1214_bounds_sha256"]
    assert (str(endpoint),str(minimum),str(minimum-endpoint)) == (proof["combined_row_upper"],proof["minimum_over_entire_box"],proof["positive_gap"])
    guard = branch["selected"]
    assert len(guard) in (1,2) and all(lower[a] == 1 for a in guard)
    nogood = {"terms":[[a,1] for a in guard],"upper":len(guard)-1}
    assert proof["conditional_guards"] == guard and proof["implied_Boolean_nogood"] == nogood
    assert not proof["numerical_ray_feasibility_assumed"] and not proof["case4_excluded"]
    return {"low50_index":index,"whole_cover_box_index":branch["index"],"nogood":nogood,
        "gap":str(minimum-endpoint),"minimum":str(minimum),"upper":str(endpoint),
        "row_multipliers":len(multipliers),"terms_contracted":terms,"original_coordinates":1214,
        "floor_fixed_zero_checked":True,"conditional_branch_ancestry_bound":True}


def replay(configuration,directory,output):
    started = time.monotonic()
    config_ref = reference(configuration)
    config = read(config_ref)
    deadline = started+config["limits"]["cold_seconds"]
    report = {"status":"RUNNING","configuration":config_ref,"checks":[],"exact_exclusions":0,
        "completed_native_records":0,"all54_low_branches_excluded":False,"new_global_zero_columns":[],
        "case4_excluded":False,"whole_graph_problem_resolved":False,
        "old_trace_replay_repeated":False,"optimizer_imported":False,"optimizer_calls":0}
    try:
        import numpy as np
        d = domain(config,deadline)
        owner = read(reference(directory/"forward-owner.json"))
        assert owner["child_reaped"]
        report["forward_owner"] = reference(directory/"forward-owner.json")
        transcript = directory/"forward/records.jsonl"
        raw = transcript.read_bytes() if transcript.exists() else b""
        complete,tail = raw.rsplit(b"\n",1) if b"\n" in raw else (b"",raw)
        refs = [json.loads(line) for line in complete.splitlines() if line]
        assert len(refs) <= 50
        report["incomplete_transcript_tail_bytes"] = len(tail)
        native_seconds = 0.0
        for k,ref in enumerate(refs):
            deadline_check(deadline)
            record,branch = read(ref),d["branches"][k]
            assert record["low50_index"] == k and record["whole_cover_box_index"] == branch["index"]
            assert record["state_sha256"] == branch["state_sha256"]
            numeric = read(record["numeric"])
            assert numeric["configuration"] == config_ref and numeric["low50_index"] == k
            assert numeric["whole_cover_box_index"] == branch["index"] and numeric["model"] == config["model"]
            assert numeric["extra_native_calls"] == 0 and numeric["row_order"] == "fixed original matrix row IDs 0..167126"
            lower = [int(v == "1") for v in branch["state"]]+[0]
            upper = [int(v != "0") for v in branch["state"]]+[0]
            assert numeric["bounds_sha256"] == sha(canonical([lower,upper]))
            assert 0 < numeric["requested_seconds"] <= 2.0
            assert not numeric["getDualRay_called"] or numeric["existing_ray"]
            assert reference(ROOT/numeric["arrays"]["path"]) == numeric["arrays"]
            assert numeric["arrays"]["bytes"] <= config["limits"]["maximum_numeric_record_bytes"]
            with np.load(ROOT/numeric["arrays"]["path"],allow_pickle=False) as saved:
                assert set(saved.files) == {"ray","column_values","column_status","row_status"}
                for name in saved.files:
                    a = saved[name]
                    assert array_binding(a) == numeric["array_bindings"][name]
                    assert len(a) in ((0,167127) if name in ("ray","row_status") else (0,1103))
                assert len(saved["ray"]) == (167127 if numeric["complete_ray_saved"] else 0)
                assert all(saved[name].dtype.kind == "f" for name in ("ray","column_values"))
                assert all(saved[name].dtype.kind in "iu" for name in ("row_status","column_status"))
            native_seconds += numeric["native_seconds"]
            if record["certificate"] is not None:
                proof = read(record["certificate"])
                assert record["status"] == "EXACT_EXCLUSION_OWNER_CHECKED"
                assert proof["configuration"] == config_ref and proof["numeric"] == record["numeric"]
                checked = certificate(proof,d,branch,k,config["model"],deadline)
                report["checks"].append({**checked,"certificate":record["certificate"]})
            else:
                assert record["status"] == "UNRESOLVED"
            report["completed_native_records"] += 1
        terminal_path = directory/"forward/result.json"
        if terminal_path.exists():
            terminal = read(reference(terminal_path))
            assert terminal["configuration"] == config_ref and terminal["source_bindings"] == config["source_bindings"]
            assert terminal["limits"] == config["limits"] and terminal["records"] == refs
            assert len(refs) <= terminal["native_calls"] <= 50
            assert terminal["exact_exclusions"] == len(report["checks"])
            assert terminal["cumulative_native_seconds"] >= native_seconds
            report["forward_terminal"] = reference(terminal_path)
            report["reported_native_calls"] = terminal["native_calls"]
            report["reported_native_seconds"] = terminal["cumulative_native_seconds"]
            report["reported_resource_overrun"] = terminal["resource_overrun"]
        report["exact_exclusions"] = len(report["checks"])
        all_low = len(refs) == len(report["checks"]) == 50 and not tail
        report["all54_low_branches_excluded"] = all_low
        singleton_zeros = [c["nogood"]["terms"][0][0] for c in report["checks"] if c["nogood"]["upper"] == 0]
        report["new_global_zero_columns"] = sorted(set(d["Q"] if all_low else singleton_zeros))
        report["prior_four_low_exclusions"] = d["prior_excluded_indices"]
        report["unresolved_attempted_branches"] = len(refs)-len(report["checks"])
        report["unprocessed_low_branches"] = 50-len(refs)
        report["unqueried_high_branches"] = 137
        deadline_check(deadline)
        report["status"] = "PASS"
    except Exception as error:
        report.update(status="ERROR_NO_UNCHECKED_PREFIX_ACCEPTED",error_type=type(error).__name__,error=str(error),
            exact_exclusions=0,all54_low_branches_excluded=False,new_global_zero_columns=[])
    report["seconds"] = time.monotonic()-started
    assert not output.exists()
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_bytes(canonical(report)+b"\n")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--configuration",type=Path,required=True)
    parser.add_argument("--directory",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args = parser.parse_args()
    result = replay(args.configuration.resolve(),args.directory.resolve(),args.output.resolve())
    print(json.dumps({k:result[k] for k in ("status","exact_exclusions","completed_native_records","seconds")}),flush=True)
    if result["status"] != "PASS": raise SystemExit(1)
