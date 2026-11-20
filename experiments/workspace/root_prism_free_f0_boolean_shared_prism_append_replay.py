"""Independent protobuf-only replay of the complete literal prism append.

Reuse both accepted finite family proofs, reconstruct every appended row,
and compare all retained parent bytes. Import no producer or native model.
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import resource
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
CONFIG = {"path":"experiments/logs/root-prism-free/f0-boolean-shared-prism-append-configuration01.json",
          "sha256":"2d6a00399df059c0052fb64de499d8d8e7874bd212a9e49cb0d6891eebfc3932"}
REVIEW = {"path":"experiments/logs/root-prism-free/f0-boolean-shared-prism-append-independent-source-review01.json",
          "sha256":"2119286c426acc0e48eed2c12e02825202bfe4941391012cf5afc00c7e5cd981"}
PRODUCER_SHA = "ea8d691cff1ae7fe9b134700dd0f10bda173d8cbde00c0e92ee7bc26d29a2803"
PARENT_ROWS, ONE_ROWS, PATH_ROWS, FOUR_ROWS = 168050, 1224, 57996, 72468
VARIABLES, FINAL_ROWS, NEW_TERMS = 68934, 299738, 1426932
CHECK_SECONDS, OWNER_SECONDS = 120, 135


def sha(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(",",":"),allow_nan=False).encode()


def reference(path):
    path = Path(path).resolve(); data = path.read_bytes()
    return {"path":str(path.relative_to(ROOT)),"sha256":sha(data),"bytes":len(data)}


def bound_bytes(ref):
    path = ROOT/ref["path"]; data = path.read_bytes()
    assert sha(data) == ref["sha256"]
    assert "bytes" not in ref or len(data) == ref["bytes"]
    return data


def read(ref):
    data = bound_bytes(ref)
    return json.loads(gzip.decompress(data) if ref["path"].endswith(".gz") else data)


def same(left,right):
    assert (left["path"],left["sha256"]) == (right["path"],right["sha256"])
    for ref in (left,right):
        if "bytes" in ref:
            assert type(ref["bytes"]) is int and (ROOT/ref["path"]).stat().st_size == ref["bytes"]


def check_time(deadline):
    if time.monotonic() >= deadline:
        raise TimeoutError("independent literal prism append replay deadline")


def save(path,value):
    with path.open("xb") as stream:
        stream.write(canonical(value)+b"\n")


def expected_row(pb,variables,coefficients,lower,upper):
    assert len(variables) == len(coefficients) and lower <= upper
    assert all(type(x) is int for x in variables+coefficients+[lower,upper])
    row = pb.ConstraintProto()
    row.linear.vars.extend(variables); row.linear.coeffs.extend(coefficients)
    row.linear.domain.extend([lower,upper])
    return row


def exact_row(pb,actual,variables,coefficients,lower,upper):
    wanted = expected_row(pb,variables,coefficients,lower,upper)
    assert actual.SerializeToString() == wanted.SerializeToString()


def controls():
    from ortools.sat import cp_model_pb2 as pb
    rows = [([4,547],[1,1],0,1),([5,546,549],[-1,1,1],-1,0),
            ([1,2,550,551,552],[-1,-1,1,1,1],-2,0)]
    rejected = 0
    for specification in rows:
        actual = expected_row(pb,*specification)
        exact_row(pb,actual,*specification)
        for mutation in range(8):
            bad = pb.ConstraintProto(); bad.CopyFrom(actual)
            if mutation == 0: bad.linear.vars[0] += 1
            elif mutation == 1: bad.linear.coeffs[0] *= -1
            elif mutation == 2: bad.linear.domain[0] -= 1
            elif mutation == 3: bad.linear.domain[1] += 1
            elif mutation == 4: bad.enforcement_literal.append(0)
            elif mutation == 5: bad.name = "unexpected row name"
            elif mutation == 6: bad.bool_or.literals.append(0)
            else: bad.MergeFromString(bytes([128,6,1]))
            try:
                exact_row(pb,bad,*specification)
            except AssertionError:
                rejected += 1
            else:
                raise AssertionError("mutated row accepted")
    assert rejected == 24 and "ortools.sat.python.cp_model" not in sys.modules
    return {"status":"PASS_LITERAL_PRISM_NATIVE_ROW_REPLAY_CONTROLS","valid_row_types":3,
            "rejected_row_mutations":rejected,"unknown_protobuf_field_rejected":True,
            "CpModel_constructed":False,"CpSolver_constructed":False,"optimizer_calls":0}


def family_authorities(cfg,loaded):
    model,model_owner = loaded["model_cold"],loaded["model_cold_owner"]
    three,three_owner = loaded["transfer_cold"],loaded["transfer_cold_owner"]
    for report,owner,rname,sname,status,owner_status in [
        (model,model_owner,"model_cold","model_cold","PASS_INDEPENDENT_COMPLETE_BOOLEAN_SHARED_MODEL","OWNED_COMPLETE_BOOLEAN_SHARED_MODEL_COLD_ACCEPTED"),
        (three,three_owner,"transfer_cold","transfer_cold","PASS_INDEPENDENT_COMPLETE_LITERAL_PRISM_TRANSFER","OWNED_COMPLETE_LITERAL_PRISM_TRANSFER_COLD_ACCEPTED")]:
        assert report["status"] == status and owner["status"] == owner_status and owner["report_accepted"] is True
        same(report["source"],cfg["sources"][sname]); same(owner["source"],cfg["sources"][sname])
        same(owner["report"],cfg["inputs"][rname])
        supervision = owner["supervision"]
        assert supervision["exit_code"] == 0 and supervision["child_reaped"] and supervision["new_process_group"]
        assert not supervision["hard_timeout"] and report["optimizer_calls"] == 0
    four,failed,resolution,root_review = [loaded[k] for k in
        ("four_cold","four_cold_owner","four_owner_resolution","four_root_acceptance")]
    assert four["status"] == "PASS_INDEPENDENT_COMPLETE_FOUR_EXTERIOR_PRISM_INVENTORY"
    assert failed["status"] == "ERROR_COLD_OWNER" and failed["report_accepted"] is False
    assert resolution["status"] == "PASS_METADATA_ONLY_COLD_OWNER_RESOLUTION" and resolution["report_accepted"] is True
    assert root_review["status"] == "ROOT_ACCEPTS_PRESERVED_COLD_WITH_EXPLICIT_METADATA_RESOLUTION"
    for name,key in (("four_cold_owner","original_owner"),("four_cold","report")):
        same(resolution[key],cfg["inputs"][name])
    for name,key in (("four_cold_owner","actual_error_owner_preserved"),("four_cold","actual_cold_report"),
                     ("four_owner_resolution","resolution")):
        same(root_review[key],cfg["inputs"][name])
    same(four["source"],cfg["sources"]["four_cold"]); same(resolution["source"],cfg["sources"]["four_resolution"])
    assert resolution["supervision"] == failed["supervision"]
    supervision = resolution["supervision"]
    assert supervision["exit_code"] == 0 and supervision["child_reaped"] and supervision["new_process_group"]
    assert not supervision["hard_timeout"] and resolution["no_main_computation_repeated"]
    same(model["preparation_inputs"]["model"],cfg["inputs"]["parent_model"])
    for report,name in ((three,"complete_inventory"),(four,"four_inventory")):
        same(report["accepted_model_cold"],cfg["inputs"]["model_cold"])
        same(report["complete_inventory"],cfg["inputs"][name])
    assert model["inventory"]["variables"] == VARIABLES and model["inventory"]["rows"] == PARENT_ROWS
    assert model["complete_parent_bytes_checked"] and model["all_appended_rows_compared_exactly"] == 150888
    assert three["all_current_native_receipts_and_complete_origins_checked"]
    assert three["all_saved_six_site_graphs_and_forced_nonedge_premises_checked"]
    assert four["complete_duplicate_origins_checked"] and four["six_site_theorem_reused_by_source_bound_review"]
    decision = loaded["four_family_decision"]
    assert decision["status"] == "USE_ORIGINAL_INDEPENDENTLY_ACCEPTED_FOUR_EXTERIOR_FAMILY"
    assert not decision["shortening_used_by_native_model"] and decision["rows_to_append"] == FOUR_ROWS
    assert decision["terms_to_append"] == 1250496 and decision["combined_following_rows"] == FINAL_ROWS
    return model,three,four


def replay(directory,report_sha,owner_sha,output):
    from ortools.sat import cp_model_pb2 as pb
    started = time.monotonic(); deadline = started+CHECK_SECONDS
    cfg,review = read(CONFIG),read(REVIEW)
    assert cfg["source_sha256"] == PRODUCER_SHA == review["source"]["sha256"]
    assert review["status"] == "PASS_SOURCE_BOUND_COMPLETE_LITERAL_PRISM_APPEND_REVIEW"
    same(review["configuration"],CONFIG)
    assert cfg["family_order"] == ["three_exterior_one_edge","three_exterior_path","four_exterior"]
    assert cfg["uses_original_full_four_exterior_family"] and not cfg["optional_reduction_used"]
    for binding in cfg["sources"].values(): bound_bytes(binding)
    bound_bytes(review["source"])
    loaded = {name:read(ref) for name,ref in cfg["inputs"].items() if name != "parent_model"}
    model_cold,three_cold,four_cold = family_authorities(cfg,loaded)
    parent_raw = gzip.decompress(bound_bytes(cfg["inputs"]["parent_model"]))
    assert sha(parent_raw) == cfg["parent_raw_sha256"] == model_cold["native_raw_model_sha256"] == three_cold["model_raw_sha256"]
    assert len(parent_raw) == model_cold["native_raw_model_bytes"] == 33451907
    producer_report,producer_owner = reference(directory/"report.json"),reference(directory/"owner.json")
    assert producer_report["sha256"] == report_sha and producer_owner["sha256"] == owner_sha
    report,owner = read(producer_report),read(producer_owner)
    status = "PASS_LITERAL_PRISM_STRENGTHENED_BOOLEAN_NATIVE_PREPARATION"
    assert report["status"] == owner["status"] == status and owner["report_accepted"] is True
    assert owner["report_sha256"] == report_sha
    assert report["source_sha256"] == owner["source_sha256"] == PRODUCER_SHA
    assert report["configuration_sha256"] == owner["configuration_sha256"] == CONFIG["sha256"]
    supervision = owner["supervision"]
    assert supervision["status"] == "CHILD_EXITED" and supervision["returncode"] == 0
    assert supervision["child_reaped"] and supervision["owned_process_group_stopped"]
    assert owner["maximum_seconds"] == 120 and 0 <= owner["seconds"] <= 120 and owner["deadline_overrun_seconds"] == 0
    stages = json.loads((directory/"stages.json").read_bytes())
    assert stages == report["stages"] and [s["name"] for s in stages] == [
        "accepted_parent_and_both_independent_family_replays_bound","three_exterior_literal_family_appended_in_accepted_order",
        "both_complete_families_appended_and_all_parent_bytes_preserved","full_public_native_transport_and_byte_comparison_passed"]
    stage_seconds = [s["seconds"] for s in stages]
    assert stage_seconds == sorted(stage_seconds) and 0 <= stage_seconds[0] <= stage_seconds[-1] <= 90
    assert stage_seconds[-1] <= report["seconds"] <= owner["seconds"]
    raw = (directory/"model.pb").read_bytes(); compressed = (directory/"model.pb.gz").read_bytes()
    assert gzip.decompress(compressed) == raw
    model_digest = sha(raw)
    assert report["model"] == {"raw_sha256":model_digest,"raw_bytes":len(raw),"archive_sha256":sha(compressed),"archive_bytes":len(compressed)}
    native = report["native_transport"]
    assert native["native_raw_sha256"] == model_digest and native["native_raw_bytes"] == len(raw)
    assert native["public_parse_return"] is True and native["public_parse_return_type"] == "bool"
    assert native["complete_byte_comparison"] is True and native["native_validation"] == ""
    assert native["CpSolver_constructed"] is False and native["optimizer_calls"] == 0
    assert report["CpSolver_constructed"] is False and report["optimizer_calls"] == 0 and report["native_query_run"] is False
    assert not report["graph_constructed"] and not report["whole_component_excluded"]
    assert report["parent_rows"] == PARENT_ROWS and report["variables"] == VARIABLES and report["rows"] == FINAL_ROWS
    assert report["new_one_edge_rows"] == ONE_ROWS and report["new_path_rows"] == PATH_ROWS and report["new_four_exterior_rows"] == FOUR_ROWS
    assert report["new_nonzeros"] == NEW_TERMS and report["complete_parent_bytes_preserved"]
    assert report["parent_raw_bytes"] == len(parent_raw) and report["parent_raw_sha256"] == sha(parent_raw)
    assert raw.startswith(parent_raw)
    model = pb.CpModelProto(); model.ParseFromString(raw)
    assert model.SerializeToString() == raw and len(model.variables) == VARIABLES and len(model.constraints) == FINAL_ROWS
    assert {field.name for field,value in model.ListFields()} <= {"name","variables","constraints"}
    edges = []
    for variable in model.variables[540:]:
        prefix,kind,left,right = variable.name.split("_")
        a,b = int(left),int(right)
        assert (prefix,kind) == ("shared","edge") and 0 <= a < b < 480
        assert variable.name == "shared_edge_%03d_%03d" % (a,b) and list(variable.domain) == [0,1]
        edges.append([a,b])
    assert len(edges) == 68394 and sha(canonical(edges)) == model_cold["inventory"]["edge_domain_sha256"]
    assert all(list(v.domain) == [0,1] for v in model.variables[:480])
    three,four = loaded["complete_inventory"],loaded["four_inventory"]
    assert sha(canonical(three)) == three_cold["inventory_raw_sha256"]
    assert sha(canonical(four)) == four_cold["raw_sha256"]
    one,paths,rows = three["proposed_one_edge"],three["proposed_paths"],four["rows"]
    assert len(one) == ONE_ROWS and len(paths) == PATH_ROWS and len(rows) == FOUR_ROWS
    assert one == sorted(one) and paths == sorted(paths)
    assert sha(canonical(one)) == three_cold["proposed_one_edge_sha256"]
    assert sha(canonical(paths)) == three_cold["proposed_paths_sha256"]
    assert sha(canonical(rows)) == four_cold["rows_value_sha256"]
    assert sha(canonical([[r["centers"][0],r["centers"][1],r["positive_edges"]] for r in rows])) == four_cold["ordered_row_keys_sha256"]
    assert sorted([e,c,w] for e,c,w,reason,premises in three["one_edge_ledger"] if reason == 4) == one
    assert sorted([a,e,f,p] for a,e,f,p,reason,premises in three["path_ledger"] if reason == 4) == paths
    total_terms = 0
    for offset,(edge,third,witness) in enumerate(one):
        assert type(edge) is type(third) is type(witness) is int
        assert 0 <= third < 480 and 0 <= edge < 68394 and third not in edges[edge] and 0 <= witness < 9360
        exact_row(pb,model.constraints[PARENT_ROWS+offset],[third,540+edge],[1,1],0,1)
        total_terms += 2
    for offset,(center,left,right,path_id) in enumerate(paths):
        assert all(type(x) is int for x in (center,left,right,path_id))
        assert 0 <= center < 480 and 0 <= left < right < 68394 and 0 <= path_id < 107418
        assert center in edges[left] and center in edges[right]
        exact_row(pb,model.constraints[PARENT_ROWS+ONE_ROWS+offset],[center,540+left,540+right],[-1,1,1],-1,0)
        total_terms += 3
        if offset % 4096 == 0: check_time(deadline)
    all_origins = 0
    for rid,row in enumerate(rows):
        assert row["row_id"] == rid and row["origin_ids"]
        a,b = row["centers"]; positive = row["positive_edges"]
        assert type(a) is type(b) is int and 0 <= a < b < 480
        assert positive == sorted(set(positive)) and all(type(e) is int and 0 <= e < 68394 for e in positive)
        for origin in row["origin_ids"]:
            assert type(origin) is int and 0 <= origin < 73404
            e,c,d,i,j,reason,old_id = four["complete_ledger"][origin]
            assert [a,b] == [c,d] == edges[e] and reason == "retained" and old_id == rid and e in positive
            all_origins += 1
        exact_row(pb,model.constraints[PARENT_ROWS+ONE_ROWS+PATH_ROWS+rid],
                  [a,b]+[540+e for e in positive],[-1,-1]+[1]*len(positive),-2,0)
        total_terms += len(positive)+2
        if rid % 4096 == 0: check_time(deadline)
    assert total_terms == NEW_TERMS
    del model.constraints[PARENT_ROWS:]
    assert model.SerializeToString() == parent_raw
    receipt_ref = reference(directory/"append-receipt.json")
    assert receipt_ref["sha256"] == report["append_receipt_sha256"]
    receipt = read(receipt_ref)
    expected_receipt = {"schema":"conway99.f0.literal-prism-native-append-receipt.v1",
        "configuration_sha256":CONFIG["sha256"],"complete_inventory":cfg["inputs"]["complete_inventory"],
        "transfer_cold":cfg["inputs"]["transfer_cold"],"four_inventory":cfg["inputs"]["four_inventory"],
        "four_cold":cfg["inputs"]["four_cold"],"parent_raw_sha256":cfg["parent_raw_sha256"],
        "parent_rows":PARENT_ROWS,"one_edge_row_start":PARENT_ROWS,"one_edge_rows":ONE_ROWS,
        "path_row_start":PARENT_ROWS+ONE_ROWS,"path_rows":PATH_ROWS,
        "four_exterior_row_start":PARENT_ROWS+ONE_ROWS+PATH_ROWS,"four_exterior_rows":FOUR_ROWS,"final_rows":FINAL_ROWS,
        "variables":VARIABLES,"new_nonzeros":NEW_TERMS,"one_edge_value_sha256":sha(canonical(one)),
        "path_value_sha256":sha(canonical(paths)),"four_rows_value_sha256":sha(canonical(rows)),
        "one_edge_native_definition":"[third,540+edge] coefficients [1,1], domain [0,1]",
        "path_native_definition":"[center,540+edge_min,540+edge_max] coefficients [-1,1,1], domain [-1,0]",
        "four_native_definition":"[b,c]+[540+e for e in positive_edges] coefficients [-1,-1]+[1]*len(positive_edges), domain [-2,0]",
        "complete_parent_bytes_preserved":True,"parent_raw_is_complete_byte_prefix":True,
        "no_variable_added_or_removed":True,"no_selector_or_graph_symmetry_fix":True,
        "no_objective_hint_or_assumption":True,"native_expected_raw_sha256":model_digest}
    assert receipt == expected_receipt
    check_time(deadline)
    assert "ortools.sat.python.cp_model" not in sys.modules and "highspy" not in sys.modules
    result = {"schema":"conway99.f0.literal-prism-native-append-independent-cold.v1",
        "status":"PASS_INDEPENDENT_COMPLETE_LITERAL_PRISM_NATIVE_APPEND",
        "source":reference(__file__),"configuration":CONFIG,"source_review":REVIEW,
        "producer_report":producer_report,"producer_owner":producer_owner,"append_receipt":receipt_ref,
        "model":reference(directory/"model.pb"),"model_archive":reference(directory/"model.pb.gz"),
        "model_raw_sha256":model_digest,"model_raw_bytes":len(raw),"parent_model":cfg["inputs"]["parent_model"],
        "parent_model_cold":cfg["inputs"]["model_cold"],"three_inventory":cfg["inputs"]["complete_inventory"],
        "three_cold":cfg["inputs"]["transfer_cold"],"four_inventory":cfg["inputs"]["four_inventory"],
        "four_cold":cfg["inputs"]["four_cold"],"four_cold_resolution":cfg["inputs"]["four_owner_resolution"],
        "four_cold_root_acceptance":cfg["inputs"]["four_root_acceptance"],"variables":VARIABLES,"rows":FINAL_ROWS,
        "parent_rows":PARENT_ROWS,"one_edge_rows_checked":ONE_ROWS,"path_rows_checked":PATH_ROWS,
        "four_exterior_rows_checked":FOUR_ROWS,"all_appended_rows_compared_exactly":ONE_ROWS+PATH_ROWS+FOUR_ROWS,
        "all_appended_terms_checked":total_terms,"four_original_origins_checked":all_origins,
        "complete_parent_bytes_checked":True,"complete_parent_raw_byte_prefix_checked":True,
        "all_variable_domains_names_and_metadata_preserved":True,"accepted_family_order_and_full_provenance_checked":True,
        "three_and_four_censuses_reexecuted":False,"optional_reduction_used":False,
        "producer_imports":0,"protobuf_decoder_only":True,"native_model_decodes":1,"native_model_builds":0,
        "CpModel_constructed":False,"CpSolver_constructed":False,"optimizer_calls":0,
        "all_exterior_pair_common_neighbor_caps_claimed":False,"graph_constructed":False,"whole_component_excluded":False,
        "seconds":time.monotonic()-started,"peak_rss_KiB":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    save(output,result)
    return result


if __name__ == "__main__":
    assert __debug__
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode",choices=("controls","run")); parser.add_argument("--directory",type=Path)
    parser.add_argument("--report-sha256"); parser.add_argument("--owner-sha256")
    parser.add_argument("--output",type=Path,required=True); args = parser.parse_args()
    if args.mode == "controls":
        result = controls(); result["source"] = reference(__file__); save(args.output.resolve(),result)
    else:
        assert args.directory is not None and args.report_sha256 and args.owner_sha256
        result = replay(args.directory.resolve(),args.report_sha256,args.owner_sha256,args.output.resolve())
    print(json.dumps({"status":result["status"],"seconds":result.get("seconds")}),flush=True)
