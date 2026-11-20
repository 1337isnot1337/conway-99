"""Independent terminal replay of one frozen Boolean shared-model query.

Only standard protobuf decoders and Python integer arithmetic are used.
No query/model producer, CpModel, CpSolver, or native solver is imported.
The accepted full-model cold is reused by hash, without rebuilding its proof.
"""
import argparse
import gzip
import hashlib
import importlib.metadata
import json
import math
from pathlib import Path
import re
import resource
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
SECONDS, OWNER_SECONDS = 120, 135
CONFIGURATION = {"path":"experiments/logs/root-prism-free/f0-boolean-shared-query-configuration01.json",
                 "sha256":"dcd8e3f99c8773e5150deb2542600a34e56058f5ca3144f7f537b7c1e64ac693"}
PREFLIGHT = {"path":"experiments/logs/root-prism-free/f0-boolean-shared-query-preparation01/report.json",
             "sha256":"2a40d71a0ea8ac7030fdd598df89d9bd8f9bd17355d6b0c27d5e07490573bff5"}
PREFLIGHT_OWNER = {"path":"experiments/logs/root-prism-free/f0-boolean-shared-query-preparation01/owner.json",
                   "sha256":"cec3baf75378a2f8a40be96a45d64ce1d187f5bd4e7540dbff5831cb69c0f674"}
QUERY_SOURCE = {"path":"experiments/workspace/root_prism_free_f0_boolean_shared_query.py",
                "sha256":"d4f08d6eb893b88ec33dcbef50ddae90799cbca5d49f8d6b5bd7332f0ad09999"}


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(",",":"),allow_nan=False).encode()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def reference(path):
    with path.open("rb") as stream:
        value = hashlib.file_digest(stream,"sha256").hexdigest()
    return {"path":str(path.relative_to(ROOT)),"sha256":value}


def read(binding):
    raw = (ROOT/binding["path"]).read_bytes()
    assert sha(raw) == binding["sha256"]
    return json.loads(gzip.decompress(raw) if binding["path"].endswith(".gz") else raw)


def write(path,value):
    with path.open("xb") as stream:
        stream.write(canonical(value)+b"\n")
    return reference(path)


def intervals_contain(domain,value):
    assert len(domain) > 0 and len(domain)%2 == 0
    for at in range(0,len(domain),2):
        assert domain[at] <= domain[at+1]
        if domain[at] <= value and value <= domain[at+1]:
            return True
    return False


def check_vector(model,vector,check=lambda:None):
    assert isinstance(vector,list)
    exact = all(type(value) is int for value in vector)
    result = {"status":"REJECTED_RETURNED_VECTOR","values":len(vector),"variables":len(model.variables),
              "all_values_exact_Python_int":exact,"variable_domains_checked":0,"linear_rows_checked":0,
              "domain_violations":[],"linear_row_violations":[]}
    if len(vector) != len(model.variables) or not exact:
        return result,[]
    for i in range(len(vector)):
        if not intervals_contain(model.variables[i].domain,vector[i]):
            result["domain_violations"].append(i)
    result["variable_domains_checked"] = len(vector)
    activities = []
    for r,constraint in enumerate(model.constraints):
        if r%4096 == 0:
            check()
        assert constraint.WhichOneof("constraint") == "linear" and not constraint.enforcement_literal
        row = constraint.linear
        assert len(row.vars) == len(row.coeffs)
        total = 0
        for at in range(len(row.vars)):
            j,c = row.vars[at],row.coeffs[at]
            assert 0 <= j < len(vector)
            total += c*vector[j]
        activities.append(total)
        if not intervals_contain(row.domain,total):
            result["linear_row_violations"].append(r)
    result["linear_rows_checked"] = len(model.constraints)
    if not result["domain_violations"] and not result["linear_row_violations"]:
        result["status"] = "PASS_EXACT_INTEGER_VECTOR_ALL_DOMAINS_AND_ROWS"
    return result,activities


def response_vectors(response):
    vectors = [("candidate",list(response.solution))] if response.solution else []
    for i,extra in enumerate(response.additional_solutions):
        vectors.append(("additional-candidate-%03d"%i,list(extra.values)))
    return vectors


def check_runtime_and_parameters(cfg,directory,record):
    from google.protobuf import text_format
    from ortools.sat import sat_parameters_pb2 as sp
    runtime = cfg["runtime"]
    distribution = importlib.metadata.distribution("ortools")
    assert distribution.version == runtime["ortools_version"] == "9.15.6755"
    assert importlib.metadata.version("protobuf") == runtime["protobuf_version"]
    wrapper = Path(distribution.locate_file("ortools/sat/python/cp_model.py"))
    with wrapper.open("rb") as stream:
        assert hashlib.file_digest(stream,"sha256").hexdigest() == runtime["cp_model_sha256"]
    binaries = [entry for entry in distribution.files if str(entry).startswith("ortools/sat/python/cp_model_helper") and str(entry).endswith(".so")]
    assert len(binaries) == 1
    with Path(distribution.locate_file(binaries[0])).open("rb") as stream:
        assert hashlib.file_digest(stream,"sha256").hexdigest() == runtime["native_helper_sha256"]
    schema = (directory/"parameter-schema.pb").read_bytes()
    assert schema == sp.DESCRIPTOR.serialized_pb and sha(schema) == runtime["parameter_schema_sha256"]
    expected = sp.SatParameters()
    for name,value in cfg["parameters"].items():
        setattr(expected,name,value)
    wire = (directory/"parameters.pb").read_bytes()
    text = (directory/"parameters.pbtxt").read_text()
    decoded = sp.SatParameters(); text_format.Parse(text,decoded)
    assert wire == expected.SerializeToString() == decoded.SerializeToString()
    expected_record = {"parameters_sha256":sha(text.encode()),"parameters_wire_sha256":sha(wire),
                       "schema_sha256":sha(schema),"runtime":runtime,"all_explicit_parameters":cfg["parameters"],
                       "defaults_preserved_in_descriptor":True}
    assert record == expected_record
    return expected_record


def accepted_model(cfg):
    from ortools.sat import cp_model_pb2 as pb
    for binding in cfg["sources"].values():
        assert reference(ROOT/binding["path"]) == binding
    assert reference(ROOT/QUERY_SOURCE["path"]) == QUERY_SOURCE and cfg["source_sha256"] == QUERY_SOURCE["sha256"]
    records = {name:read(binding) for name,binding in cfg["inputs"].items() if name != "model"}
    prepared,owner,cold,cold_owner = [records[k] for k in ("model_preparation","model_preparation_owner","model_cold","model_cold_owner")]
    assert owner["report_accepted"] and owner["report_sha256"] == cfg["inputs"]["model_preparation"]["sha256"]
    assert owner["status"] == prepared["status"] == "PASS_COMPLETE_BOOLEAN_SHARED_MODEL_NATIVE_PREPARATION"
    assert prepared["source_sha256"] == owner["source_sha256"] == cfg["sources"]["model_producer"]["sha256"]
    assert prepared["configuration_sha256"] == cfg["inputs"]["model_configuration"]["sha256"]
    assert owner["deadline_overrun_seconds"] == 0 and owner["supervision"]["child_reaped"] and owner["supervision"]["returncode"] == 0
    assert cold["status"] == "PASS_INDEPENDENT_COMPLETE_BOOLEAN_SHARED_MODEL"
    assert cold["source"] == cold_owner["source"] == cfg["sources"]["model_cold"]
    assert cold["configuration"] == cfg["inputs"]["model_configuration"]
    assert cold_owner["status"] == "OWNED_COMPLETE_BOOLEAN_SHARED_MODEL_COLD_ACCEPTED" and cold_owner["report_accepted"]
    assert cold_owner["report"] == cfg["inputs"]["model_cold"] and cold_owner["root_gate"] == cfg["inputs"]["model_cold_root_gate"]
    assert cold_owner["supervision"]["exit_code"] == 0 and cold_owner["supervision"]["child_reaped"] and not cold_owner["supervision"]["hard_timeout"]
    assert cold["complete_parent_bytes_checked"] and cold["all_appended_rows_compared_exactly"] == 150888
    for cold_key,config_key in (("report","model_preparation"),("owner","model_preparation_owner"),("model","model")):
        assert cold["preparation_inputs"][cold_key] == cfg["inputs"][config_key]
    archive = (ROOT/cfg["inputs"]["model"]["path"]).read_bytes()
    assert sha(archive) == cfg["inputs"]["model"]["sha256"]
    raw = gzip.decompress(archive)
    assert sha(raw) == cfg["model_raw_sha256"] == cold["native_raw_model_sha256"] == prepared["model"]["raw_sha256"]
    assert len(raw) == cold["native_raw_model_bytes"] == 33451907
    model = pb.CpModelProto(); model.ParseFromString(raw)
    assert model.SerializeToString() == raw and len(model.variables) == 68934 and len(model.constraints) == 168050
    assert {field.name for field,_ in model.ListFields()} <= {"name","variables","constraints"}
    assert all(c.WhichOneof("constraint") == "linear" and not c.enforcement_literal for c in model.constraints)
    edges = []
    for variable in model.variables[540:]:
        a,b = map(int,variable.name.removeprefix("shared_edge_").split("_"))
        assert 0 <= a < b < 480 and variable.name == "shared_edge_%03d_%03d"%(a,b)
        edges.append([a,b])
    assert sha(canonical(edges)) == cold["inventory"]["edge_domain_sha256"]
    return model,edges


def controls():
    from ortools.sat import cp_model_pb2 as pb
    model = pb.CpModelProto()
    for domain in ([0,1],[-2,-1,2,3],[0,1]):
        model.variables.add().domain.extend(domain)
    large = (1<<54)+3
    for variables,coefficients,domain in (([0,2],[1,-1],[0,0]),([1],[large],[-2*large,-large,2*large,3*large]),([],[],[0,0])):
        row = model.constraints.add().linear; row.vars.extend(variables); row.coeffs.extend(coefficients); row.domain.extend(domain)
    positive,activities = check_vector(model,[1,2,1])
    assert positive["status"].startswith("PASS") and activities == [0,2*large,0]
    assert check_vector(model,[0,-1,0])[0]["status"].startswith("PASS")
    gap = check_vector(model,[1,0,1])[0]
    assert gap["domain_violations"] == [1] and gap["linear_row_violations"] == [1]
    assert check_vector(model,[0,2,1])[0]["linear_row_violations"] == [0]
    assert not check_vector(model,[1,2.0,1])[0]["all_values_exact_Python_int"]
    assert check_vector(model,[1,2])[0]["linear_rows_checked"] == 0
    response = pb.CpSolverResponse(status=pb.UNKNOWN,solution=[1,2,1])
    response.additional_solutions.add().values.extend([0,-1,0]); response.additional_solutions.add()
    assert response_vectors(response) == [("candidate",[1,2,1]),("additional-candidate-000",[0,-1,0]),("additional-candidate-001",[])]
    assert check_vector(model,[])[0]["status"] == "REJECTED_RETURNED_VECTOR"
    assert "ortools.sat.python.cp_model" not in sys.modules
    return {"status":"PASS_INDEPENDENT_BOOLEAN_QUERY_COLD_CONTROLS","integer_above_binary64_exact_range":large,
            "union_domain_gap_and_negative_values_checked":True,"empty_row_and_wrong_length_checked":True,
            "primary_and_all_additional_vectors_including_empty_retained":True,
            "producer_imports":0,"CpModel_constructed":False,"CpSolver_constructed":False,"optimizer_calls":0}


def run(directory,result_sha256,owner_sha256,output):
    from google.protobuf import text_format
    from ortools.sat import cp_model_pb2 as pb
    started = time.monotonic()
    def check():
        if time.monotonic()-started >= SECONDS:
            raise TimeoutError("independent Boolean query cold deadline")
    cfg = read(CONFIGURATION)
    assert cfg["schema"] == "conway99.f0.boolean-shared-one-call-configuration.v1"
    assert (cfg["maximum_native_calls"],cfg["native_seconds"],cfg["owner_seconds"],cfg["finalization_reserve"]) == (1,180,300,60)
    model,edges = accepted_model(cfg)
    result_ref,owner_ref = reference(directory/"result.json"),reference(directory/"owner.json")
    assert result_ref["sha256"] == result_sha256 and owner_ref["sha256"] == owner_sha256
    result,owner = read(result_ref),read(owner_ref)
    assert owner["mode"] == "run" and owner["maximum_seconds"] == 300
    assert owner["report_accepted"] and owner["report_sha256"] == result_sha256
    assert owner["source_sha256"] == result["source_sha256"] == QUERY_SOURCE["sha256"]
    assert owner["configuration_sha256"] == result["configuration_sha256"] == CONFIGURATION["sha256"]
    assert owner["status"] == result["status"] and owner["deadline_overrun_seconds"] == 0
    assert owner["supervision"]["status"] == "CHILD_EXITED" and owner["supervision"]["returncode"] == 0
    assert owner["supervision"]["child_reaped"] and owner["supervision"]["owned_process_group_stopped"]
    assert result["model_raw_sha256"] == cfg["model_raw_sha256"]
    assert not result["graph_constructed"] and not result["whole_component_excluded"] and result["independent_query_cold_required"]
    preflight,preflight_owner = read(PREFLIGHT),read(PREFLIGHT_OWNER)
    assert preflight_owner["report_accepted"] and preflight_owner["report_sha256"] == PREFLIGHT["sha256"]
    assert preflight_owner["supervision"]["returncode"] == 0 and preflight_owner["supervision"]["child_reaped"] and preflight_owner["deadline_overrun_seconds"] == 0
    assert preflight["status"] == preflight_owner["status"] == "PASS_BOOLEAN_SHARED_ONE_CALL_QUERY_PREFLIGHT"
    assert preflight["source_sha256"] == preflight_owner["source_sha256"] == QUERY_SOURCE["sha256"]
    assert preflight["configuration_sha256"] == preflight_owner["configuration_sha256"] == CONFIGURATION["sha256"]
    assert preflight["production_solve_calls"] == 0 and not preflight["CpSolver_constructed"]
    assert result["preflight_report_sha256"] == PREFLIGHT["sha256"] and result["preflight_owner_sha256"] == PREFLIGHT_OWNER["sha256"]
    assert result["parameters"] == preflight["parameters"]
    parameter_record = check_runtime_and_parameters(cfg,directory,result["parameters"])
    assert reference(directory/"model.pb")["sha256"] == cfg["model_raw_sha256"]
    transport = result["native_transport"]
    assert transport["native_raw_sha256"] == cfg["model_raw_sha256"] and transport["native_raw_bytes"] == 33451907
    assert transport["public_parse_return"] is True and transport["native_validation"] == "" and transport["complete_byte_comparison"]
    checks,activity_rows,valid = [],0,[]
    calls = result["production_solve_calls"]
    if calls == 0:
        assert result["status"] == "UNKNOWN_INSUFFICIENT_REMAINING_OWNER_BUDGET_NO_CALL"
        assert not result["CpSolver_constructed"] and result["returned_vectors"] == []
        assert not (directory/"response.pb").exists() and not (directory/"response.pbtxt").exists()
        vectors = []
        native_status = None
    else:
        assert calls == 1 and result["CpSolver_constructed"]
        assert result["native_allowance_seconds"] == 180 and result["remaining_owner_at_call"] >= 240
        assert math.isfinite(result["native_seconds"]) and result["native_seconds"] >= 0
        assert result["native_overrun_seconds"] == max(0,result["native_seconds"]-180)
        text = (directory/"response.pbtxt").read_text(); wire = (directory/"response.pb").read_bytes()
        assert sha(text.encode()) == result["response_sha256"] and sha(wire) == result["response_wire_sha256"]
        response = pb.CpSolverResponse(); response.ParseFromString(wire)
        decoded = pb.CpSolverResponse(); text_format.Parse(text,decoded)
        assert decoded.SerializeToString() == response.SerializeToString() == wire
        native_status = pb.CpSolverStatus.Name(response.status)
        assert native_status == result["native_status"] and response.wall_time == result["native_reported_wall_seconds"]
        vectors = response_vectors(response)
        assert len(vectors) == len(result["returned_vectors"])
        for (name,vector),saved in zip(vectors,result["returned_vectors"]):
            check()
            candidate_ref = reference(directory/(name+".json")); candidate = read(candidate_ref)
            assert canonical(candidate) == canonical(vector)
            assert candidate_ref["sha256"] == saved["candidate_sha256"] and sha(canonical(candidate)) == saved["candidate_values_sha256"]
            exact,activities = check_vector(model,candidate,check)
            check_ref = reference(directory/(name+"-check.json"))
            assert check_ref["sha256"] == saved["check_sha256"] and read(check_ref) == exact
            path = directory/(name+"-row-activities.json.gz"); compressed = path.read_bytes(); activity_raw = gzip.decompress(compressed)
            assert sha(compressed) == saved["activities_sha256"] and sha(activity_raw) == saved["activities_raw_sha256"]
            assert activity_raw == canonical(activities)
            assert saved == {"name":name,"candidate_sha256":candidate_ref["sha256"],"candidate_values_sha256":sha(canonical(candidate)),
                "check_sha256":check_ref["sha256"],"activities_sha256":sha(compressed),"activities_raw_sha256":sha(activity_raw),
                "check_status":exact["status"],"values":len(candidate)}
            checks.append({"name":name,"candidate":candidate_ref,"status":exact["status"],
                           "variable_domains_checked":exact["variable_domains_checked"],"linear_rows_checked":exact["linear_rows_checked"]})
            activity_rows += len(activities)
            if exact["status"] == "PASS_EXACT_INTEGER_VECTOR_ALL_DOMAINS_AND_ROWS":
                valid.append(name)
                if name == "candidate":
                    selection = [a for a in range(480) if candidate[a] == 1]
                    edge_ids = [e for e in range(68394) if candidate[540+e] == 1]
                    selection_ref = reference(directory/"selection.json"); edge_ref = reference(directory/"selected-edges.json")
                    assert selection_ref["sha256"] == result["selection_sha256"] and read(selection_ref) == selection
                    assert edge_ref["sha256"] == result["selected_edges_sha256"] and read(edge_ref) == {"edge_ids":edge_ids,"edges":[edges[e] for e in edge_ids]}
        if result["native_overrun_seconds"] > 0:
            expected_status = "UNKNOWN_NATIVE_BUDGET_OVERRUN"
        elif any(c["status"] != "PASS_EXACT_INTEGER_VECTOR_ALL_DOMAINS_AND_ROWS" for c in checks):
            expected_status = "ERROR_EXACT_RETURNED_VECTOR_CHECK_FAILED"
        elif response.status in (pb.FEASIBLE,pb.OPTIMAL):
            expected_status = "EXACT_BOOLEAN_MODEL_VECTOR_AWAITING_INDEPENDENT_COLD" if response.solution else "ERROR_NATIVE_SAT_WITHOUT_VECTOR"
        elif response.status == pb.INFEASIBLE:
            expected_status = "UNPROVED_NATIVE_INFEASIBLE"
        elif response.status == pb.MODEL_INVALID:
            expected_status = "ERROR_NATIVE_MODEL_INVALID"
        else:
            expected_status = "UNKNOWN_BOOLEAN_SHARED_NATIVE"
        assert result["status"] == expected_status
    actual_vector_files = {p.stem for p in directory.iterdir() if p.is_file() and (p.name == "candidate.json" or re.fullmatch(r"additional-candidate-[0-9]{3,}\.json",p.name))}
    assert actual_vector_files == {name for name,vector in vectors}
    check()
    assert "ortools.sat.python.cp_model" not in sys.modules and "highspy" not in sys.modules
    answer = {"status":"PASS_INDEPENDENT_BOOLEAN_SHARED_QUERY_TERMINAL_REPLAY","source":reference(Path(__file__).resolve()),
              "configuration":CONFIGURATION,"run_result":result_ref,"run_owner":owner_ref,
              "accepted_model_cold":cfg["inputs"]["model_cold"],"model_raw_sha256":cfg["model_raw_sha256"],
              "run_status_preserved":result["status"],"native_status_preserved":native_status,"production_solve_calls_checked":calls,
              "full_parameters_and_runtime_bindings_checked":True,"parameters":parameter_record,
              "all_returned_vectors_checked":checks,"valid_model_vector_names":valid,"row_activities_checked":activity_rows,
              "native_infeasibility_is_not_a_proof":True,"pair_caps_and_residuals_not_certified":True,
              "graph_constructed":False,"whole_component_excluded":False,"producer_imports":0,
              "CpModel_constructed":False,"CpSolver_constructed":False,"optimizer_calls":0,
              "seconds":time.monotonic()-started,"peak_rss_KiB":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    write(output,answer)
    return answer


if __name__ == "__main__":
    assert __debug__
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode",choices=("controls","run"))
    parser.add_argument("--directory",type=Path)
    parser.add_argument("--result-sha256")
    parser.add_argument("--owner-sha256")
    parser.add_argument("--output",type=Path,required=True)
    args = parser.parse_args()
    if args.mode == "controls":
        result = controls(); result["source"] = reference(Path(__file__).resolve()); write(args.output.resolve(),result)
    else:
        assert args.directory is not None and args.result_sha256 is not None and args.owner_sha256 is not None
        result = run(args.directory.resolve(),args.result_sha256,args.owner_sha256,args.output.resolve())
    print(json.dumps({"status":result["status"],"seconds":result.get("seconds")}),flush=True)
