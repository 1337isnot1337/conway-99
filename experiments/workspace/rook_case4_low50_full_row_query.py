"""One bounded complete-row LP call for each of the 50 remaining low boxes.

Only an independently replayed integer row combination excludes a branch.
The model is loaded once; every variable bound, including t=0, is reset.
No added branch assumption, feedback, retry, or hidden ray solve is used.
"""
import argparse
import importlib.metadata
import json
import math
import os
from pathlib import Path
import platform
import resource
import shutil
import sys
import time

import rook_case4_low50_full_row_exact as exact
import rook_case4_full_native_transport as transport

ROOT,LIMITS = exact.ROOT,exact.LIMITS
EXACT_SHA = "660d57964f06933cc193496fb81d5d12305df2efe97d78a4878e73487090f5b7"
REPLAY = "experiments/workspace/rook_case4_low50_full_row_replay.py"
REPLAY_SHA = "5220f81f611050cf4ffdb4f1ed364367fa04d2f4c8c26486180fefc49fc5108d"
OWNER = "experiments/workspace/rook_case4_box_hull_membership_query.py"
OWNER_SHA = "aa557c7b99ec3de71e9ecde3f6f7dfa3ca71066a835086cdd3b3f2eb7be558e5"
OWNER_HELPER = "experiments/workspace/rook_case4_box_hull_membership.py"
OWNER_HELPER_SHA = "54330f430c0c4dae03a0298533121ce43482ceb295f54df715ad2f2180d3503c"
PREFLIGHT_GATE = {"path":"experiments/logs/grids-and-triangles/rook-case4-low50-full-row-preflight-root-gate01.json",
    "sha256":"27032eff81ea8497df5b3e368b924ce638d272ef48acbdeefc0a24a7a25fe329"}


def source_bindings():
    refs = exact.source_bindings()
    assert refs["helper"]["sha256"] == EXACT_SHA
    assert refs["transport"] == exact.reference(Path(transport.__file__))
    refs["query"] = exact.reference(Path(__file__))
    for key,path,digest in (("cold",REPLAY,REPLAY_SHA),("owner",OWNER,OWNER_SHA),
            ("owner_helper",OWNER_HELPER,OWNER_HELPER_SHA)):
        refs[key] = exact.reference(ROOT/path)
        assert refs[key]["sha256"] == digest
    return refs


def used_bytes(directory):
    return sum(p.stat().st_size for p in directory.iterdir() if p.is_file())


def reserve(directory,additional):
    assert used_bytes(directory)+additional <= LIMITS["maximum_transcript_bytes"], "transcript capacity"
    assert shutil.disk_usage(directory).free >= additional+LIMITS["safety_disk_reserve_bytes"], "disk reserve"


def write_record(directory,name,value):
    reserve(directory,len(exact.canonical(value))+1)
    return exact.write(directory/name,value)


def save_arrays(directory,name,arrays):
    import numpy as np
    assert set(arrays) == {"ray","column_values","column_status","row_status"}
    assert all(a.ndim == 1 and a.flags.c_contiguous for a in arrays.values())
    assert all(arrays[k].dtype == np.dtype("float64") for k in ("ray","column_values"))
    assert all(arrays[k].dtype == np.dtype("int8") for k in ("column_status","row_status"))
    reserve(directory,LIMITS["maximum_numeric_record_bytes"])
    path,temporary = directory/name,directory/(name+".partial")
    assert not path.exists() and not temporary.exists()
    with temporary.open("xb") as stream:
        np.savez_compressed(stream,**arrays)
        stream.flush();os.fsync(stream.fileno())
    assert temporary.stat().st_size <= LIMITS["maximum_numeric_record_bytes"]
    assert used_bytes(directory) <= LIMITS["maximum_transcript_bytes"]
    temporary.replace(path)
    return exact.reference(path),{k:exact.array_binding(v) for k,v in arrays.items()}


def controls(directory):
    import numpy as np
    started = time.monotonic()
    directory.mkdir(parents=True,exist_ok=False)
    arrays = {"ray":np.asarray([0.0,-0.0,2**-1022,2**100,-0.125],dtype=np.float64),
        "column_values":np.asarray([0.0,0.5,1.0,float("inf"),float("nan")],dtype=np.float64),
        "column_status":np.asarray([0,1,2,3,4],dtype=np.int8),"row_status":np.asarray([],dtype=np.int8)}
    saved,binding = save_arrays(directory,"synthetic.npz",arrays)
    with np.load(ROOT/saved["path"],allow_pickle=False) as replay:
        assert set(replay.files) == set(arrays)
        for k,a in arrays.items():
            assert replay[k].dtype == a.dtype and replay[k].tobytes() == a.tobytes()
            assert exact.array_binding(replay[k]) == binding[k]
    report = {"status":"PASS_LOSSLESS_COMPRESSED_NUMERIC_FORMAT_NO_NATIVE",
        "sources":source_bindings(),"saved":saved,"array_bindings":binding,
        "signed_zero_subnormal_large_float_NaN_and_infinity_preserved":True,
        "full_matrix_loaded":False,"native_imports":0,"optimizer_calls":0,"seconds":time.monotonic()-started}
    exact.write(directory/"result.json",report)
    return report


def configure(preflight_directory,exact_controls,numeric_controls,cold_controls,output):
    started = time.monotonic()
    flight = exact.load_preflight(preflight_directory)
    math_ref,format_ref = exact.reference(exact_controls),exact.reference(numeric_controls/"result.json")
    checked,fmt = exact.read(math_ref),exact.read(format_ref)
    assert checked["status"] == "PASS_CSR_SIGNED_BOX_CERTIFICATE_CONTROLS_NO_NATIVE"
    assert checked["source"] == exact.reference(Path(exact.__file__))
    assert checked["optimizer_calls"] == 0 and not checked["full_matrix_loaded"]
    assert fmt["status"] == "PASS_LOSSLESS_COMPRESSED_NUMERIC_FORMAT_NO_NATIVE" and fmt["sources"] == source_bindings()
    assert fmt["optimizer_calls"] == 0 and not fmt["full_matrix_loaded"]
    cold_ref = exact.reference(cold_controls)
    cold_checked = exact.read(cold_ref)
    assert cold_checked["status"] == "PASS_ACTUAL_INDEPENDENT_COLD_CERTIFICATE_CONTROLS"
    assert cold_checked["cold_source"] == source_bindings()["cold"] and cold_checked["optimizer_calls"] == 0
    gate = exact.read(PREFLIGHT_GATE)
    assert gate["optimizer_calls_authorized"] == 0
    assert gate["configuration"]["sha256"] == flight["terminal"]["configuration"]["sha256"]
    domain = flight["domain"]
    required_disk = LIMITS["maximum_transcript_bytes"]+LIMITS["maximum_numeric_record_bytes"]+LIMITS["maximum_metadata_bytes"]+LIMITS["safety_disk_reserve_bytes"]
    free = shutil.disk_usage(ROOT).free
    assert free >= required_disk
    config = {"status":"PREPARED_ONE_FULL50_CONDITIONAL_LP_BATCH_NO_SOLVE",
        "source_bindings":source_bindings(),"preflight_terminal":flight["terminal_ref"],
        "preflight_gate":PREFLIGHT_GATE,"model":flight["report"]["matrix"],"arrays":flight["model"]["arrays"],
        "matrix_binding":flight["model"]["matrix_binding"],"exact_controls":math_ref,"numeric_controls":format_ref,"cold_controls":cold_ref,
        "limits":LIMITS,"options":transport.OPTIONS,"runtime":flight["report"]["runtime"],
        "variables":1103,"selector_variables":1102,"rows":167127,"nonzeros":10769860,
        "original_column_ids":domain["ids"],"proved_zero_columns":domain["zeros"],
        "selected_branch_count":50,"selected_whole_cover_indices":[b["index"] for b in domain["branches"]],
        "branch_ancestor_bindings":domain["branch_ancestor_bindings"],"whole_cover":domain["whole_cover"],
        "prior_four_low_exclusions":domain["prior_excluded_indices"],"unqueried_high_boxes":137,
        "partition":domain["partition"],"calls_per_branch":1,"native_matrix_loads":1,
        "all1103_bounds_reset_per_branch":True,"floor_bounds":[0,0],"all_objective_coefficients":0,
        "native_ray_requires_existing_ray_check":True,"native_feasibility_never_accepted":True,
        "individual_singleton_nogood_is_a_global_zero":True,"all50_refutations_with_prior4_imply_Q_zero":True,
        "full_matrix_numerical_vectors_saved_as_lossless_compressed_arrays":True,
        "required_new_disk_bytes_including_reserve":required_disk,"observed_free_disk_bytes":free,
        "production_queries":0,"full_matrix_loaded_during_this_configuration":False,
        "seconds":time.monotonic()-started}
    exact.write(output,config)
    return config


def load(configuration):
    cfg = exact.read(exact.reference(configuration))
    assert cfg["status"] == "PREPARED_ONE_FULL50_CONDITIONAL_LP_BATCH_NO_SOLVE"
    assert cfg["source_bindings"] == source_bindings() and cfg["limits"] == LIMITS
    assert cfg["options"] == transport.OPTIONS and cfg["production_queries"] == 0
    flight = exact.load_preflight((ROOT/cfg["preflight_terminal"]["path"]).parent)
    assert flight["terminal_ref"] == cfg["preflight_terminal"]
    assert flight["report"]["matrix"] == cfg["model"] and flight["model"]["arrays"] == cfg["arrays"]
    assert flight["model"]["matrix_binding"] == cfg["matrix_binding"]
    assert flight["report"]["runtime"] == cfg["runtime"]
    assert cfg["original_column_ids"] == flight["domain"]["ids"]
    assert cfg["proved_zero_columns"] == flight["domain"]["zeros"]
    assert cfg["selected_whole_cover_indices"] == [b["index"] for b in flight["domain"]["branches"]]
    assert cfg["branch_ancestor_bindings"] == flight["domain"]["branch_ancestor_bindings"]
    assert exact.read(cfg["exact_controls"])["source"] == cfg["source_bindings"]["helper"]
    assert exact.read(cfg["numeric_controls"])["sources"] == cfg["source_bindings"]
    assert exact.read(cfg["cold_controls"])["cold_source"] == cfg["source_bindings"]["cold"]
    return cfg,flight


def runtime():
    import highspy
    import highspy._core
    import numpy as np
    return {"python":platform.python_version(),"python_executable":sys.executable,
        "highspy":importlib.metadata.version("highspy"),"numpy":np.__version__,
        "highs_version":highspy.Highs().version(),
        "native_extension_sha256":exact.sha(Path(highspy._core.__file__).read_bytes())}


def forward(configuration,directory):
    started = time.monotonic()
    deadline = started+LIMITS["forward_seconds"]
    directory.mkdir(parents=True,exist_ok=False)
    result = {"status":"RUNNING","configuration":exact.reference(configuration),
        "source_bindings":source_bindings(),"limits":LIMITS,"records":[],"native_calls":0,
        "cumulative_native_seconds":0.0,"exact_exclusions":0,"complete50_prefix":False,
        "resource_overrun":False,"automatic_retries":0,"case4_excluded":False,
        "whole_graph_problem_resolved":False}
    h = None

    def milestone(stage,**details):
        value = {"stage":stage,"seconds":time.monotonic()-started,**details}
        with (directory/"milestones.jsonl").open("ab") as stream:
            stream.write(exact.canonical(value)+b"\n");stream.flush();os.fsync(stream.fileno())
        print(json.dumps(value),flush=True)

    try:
        milestone("binding")
        cfg,flight = load(configuration)
        import highspy
        import numpy as np
        assert runtime() == cfg["runtime"]
        milestone("reading_cached_exact_arrays")
        arrays = exact.load_arrays(flight,deadline)
        milestone("native_load")
        lo,hi = [0]*1103,[1]*1102+[0]
        h = transport.build_native(arrays,1103,lo,hi,deadline)
        milestone("bounded_native_coefficient_audit")
        audit = transport.audit_native(h,arrays,1103,lo,hi,deadline)
        write_record(directory,"initialization.json",{"model":cfg["model"],"runtime":cfg["runtime"],
            "audit":audit,"seconds":time.monotonic()-started})
        milestone("branch_calls_ready")
        with (directory/"records.jsonl").open("xb") as transcript:
            for k,branch in enumerate(flight["domain"]["branches"]):
                assert result["native_calls"] == k
                remaining = min(deadline-time.monotonic(),LIMITS["cumulative_native_seconds"]-result["cumulative_native_seconds"])
                if remaining <= 0:
                    result["stop_reason"] = "phase_or_cumulative_native_budget"
                    break
                reserve(directory,LIMITS["maximum_numeric_record_bytes"]+65536)
                lower,upper = exact.state_bounds(branch["state"])
                reset = transport.reset_box(h,lower,upper)
                allowance = min(LIMITS["requested_native_seconds_per_branch"],remaining)
                previous = float(h.getRunTime())
                assert math.isfinite(previous) and previous >= 0
                absolute = previous+allowance
                assert h.setOptionValue("time_limit",absolute) == highspy.HighsStatus.kOk
                native_started = time.monotonic()
                status = h.run()  # Sole native solve for this branch.
                model_status = h.getModelStatus()
                ray = np.asarray([],dtype=np.float64)
                exists,requested = False,False
                ray_status = None
                if model_status == highspy.HighsModelStatus.kInfeasible:
                    existence_status,found = h.getDualRayExist()
                    exists = bool(existence_status == highspy.HighsStatus.kOk and found)
                    if exists:
                        requested = True
                        rs,found,values = h.getDualRay()
                        ray_status = str(rs)
                        if rs == highspy.HighsStatus.kOk and found:
                            ray = np.asarray(values,dtype=np.float64)
                            assert ray.ndim == 1 and len(ray) == 167127
                elapsed = time.monotonic()-native_started
                result["native_calls"] += 1
                result["cumulative_native_seconds"] += elapsed
                solution,basis = h.getSolution(),h.getBasis()
                saved_arrays = {"ray":ray,
                    "column_values":np.asarray(solution.col_value if solution.value_valid else [],dtype=np.float64),
                    "column_status":np.asarray([int(v) for v in basis.col_status] if basis.valid else [],dtype=np.int8),
                    "row_status":np.asarray([int(v) for v in basis.row_status] if basis.valid else [],dtype=np.int8)}
                assert len(saved_arrays["column_values"]) in (0,1103)
                assert len(saved_arrays["column_status"]) in (0,1103) and len(saved_arrays["row_status"]) in (0,167127)
                numeric_arrays,bindings = save_arrays(directory,f"numeric-{k:02d}.npz",saved_arrays)
                numeric = {"configuration":result["configuration"],"low50_index":k,
                    "whole_cover_box_index":branch["index"],"state_sha256":branch["state_sha256"],
                    "bounds_sha256":reset,"model":cfg["model"],"requested_seconds":allowance,
                    "native_absolute_time_limit":absolute,"native_seconds":elapsed,"run_status":str(status),
                    "model_status":str(model_status),"numerically_optimal":model_status == highspy.HighsModelStatus.kOptimal,
                    "numerically_infeasible":model_status == highspy.HighsModelStatus.kInfeasible,
                    "existing_ray":exists,"getDualRay_called":requested,"getDualRay_status":ray_status,
                    "complete_ray_saved":len(ray) == 167127,"ray_all_finite":bool(np.isfinite(ray).all()),
                    "solution_value_valid":bool(solution.value_valid),"basis_valid":bool(basis.valid),
                    "arrays":numeric_arrays,"array_bindings":bindings,
                    "row_order":"fixed original matrix row IDs 0..167126",
                    "native_feasibility_is_not_accepted":True,"extra_native_calls":0}
                numeric_ref = write_record(directory,f"numeric-{k:02d}.json",numeric)
                proof_ref,attempts = None,[]
                if len(ray) == 167127 and numeric["ray_all_finite"]:
                    try:
                        for proposal in exact.rounded_proposals(ray):
                            exact.deadline_check(deadline)
                            proof = exact.exclusion(flight,arrays,k,proposal["multipliers"],deadline)
                            attempts.append({"scale":proposal["scale"],"orientation":proposal["orientation"],"accepted":proof is not None})
                            if proof is not None:
                                proof.update(configuration=result["configuration"],numeric=numeric_ref,
                                    rounding={"scale":proposal["scale"],"orientation":proposal["orientation"]})
                                proof_ref = write_record(directory,f"certificate-{k:02d}.json",proof)
                                break
                    except TimeoutError:
                        result["stop_reason"] = "exact_proposal_phase_deadline"
                record = {"low50_index":k,"whole_cover_box_index":branch["index"],"state_sha256":branch["state_sha256"],
                    "numeric":numeric_ref,"certificate":proof_ref,"rounding_attempts":attempts,
                    "status":"EXACT_EXCLUSION_OWNER_CHECKED" if proof_ref else "UNRESOLVED",
                    "numerical_status_is_not_a_certificate":True}
                record_ref = write_record(directory,f"branch-{k:02d}.json",record)
                transcript.write(exact.canonical(record_ref)+b"\n");transcript.flush();os.fsync(transcript.fileno())
                result["records"].append(record_ref)
                result["exact_exclusions"] += int(proof_ref is not None)
                milestone("branch_complete",index=k,box=branch["index"],status=record["status"],native_seconds=elapsed)
                if status == highspy.HighsStatus.kError:
                    result["stop_reason"] = "native_error_no_retry"
                    break
                if time.monotonic() >= deadline or result["cumulative_native_seconds"] >= LIMITS["cumulative_native_seconds"]:
                    result.setdefault("stop_reason","phase_or_cumulative_native_budget")
                    break
        result["complete50_prefix"] = len(result["records"]) == 50
        result["status"] = "TERMINAL_COMPLETE50" if result["complete50_prefix"] else "TERMINAL_PARTIAL"
    except Exception as error:
        result.update(status="ERROR_PARTIAL_PREFIX_PRESERVED",error_type=type(error).__name__,error=str(error))
    finally:
        if h is not None: h.clear()
        result["seconds"] = time.monotonic()-started
        result["peak_rss_KiB"] = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        result["resource_overrun"] = result["seconds"] > LIMITS["forward_seconds"] or result["cumulative_native_seconds"] > LIMITS["cumulative_native_seconds"]
        result["retained_file_bytes_before_terminal"] = used_bytes(directory)
        exact.write(directory/"result.json",result)
    return result


def run(configuration,directory):
    cfg,flight = load(configuration)
    directory.mkdir(parents=True,exist_ok=False)
    import rook_case4_box_hull_membership_query as owner
    assert exact.reference(Path(owner.__file__))["sha256"] == OWNER_SHA
    started = time.monotonic()
    receipt = owner.owned([sys.executable,str(Path(__file__).resolve()),"_forward","--configuration",str(configuration),
        "--directory",str(directory/"forward")],directory,LIMITS["forward_owner_seconds"],"forward",True)
    exact.write(directory/"forward-owner.json",receipt)
    cold_owner = owner.owned([sys.executable,str(ROOT/REPLAY),"--configuration",str(configuration),
        "--directory",str(directory),"--output",str(directory/"cold.json")],directory,LIMITS["cold_owner_seconds"],"cold",True)
    exact.write(directory/"cold-owner.json",cold_owner)
    cold_path = directory/"cold.json"
    cold = json.loads(cold_path.read_bytes()) if cold_path.exists() else None
    accepted = bool(owner.success(cold_owner) and cold and cold["status"] == "PASS")
    result = {"status":"ACCEPTED_EXACT_PREFIX" if accepted else "UNRESOLVED_COLD_NOT_ACCEPTED",
        "configuration":exact.reference(configuration),"source_bindings":source_bindings(),"limits":LIMITS,
        "forward_owner":exact.reference(directory/"forward-owner.json"),"cold_owner":exact.reference(directory/"cold-owner.json"),
        "cold":exact.reference(cold_path) if cold_path.exists() else None,
        "exact_exclusions":cold["exact_exclusions"] if accepted else 0,
        "all54_low_branches_excluded":bool(accepted and cold["all54_low_branches_excluded"]),
        "new_global_zero_columns":cold["new_global_zero_columns"] if accepted else [],
        "automatic_retries":0,"case4_excluded":False,"whole_graph_problem_resolved":False,
        "seconds":time.monotonic()-started}
    exact.write(directory/"result.json",result)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode",choices=("controls","configure","_forward","run"))
    parser.add_argument("--directory",type=Path)
    parser.add_argument("--preflight-directory",type=Path)
    parser.add_argument("--exact-controls",type=Path)
    parser.add_argument("--numeric-controls",type=Path)
    parser.add_argument("--cold-controls",type=Path)
    parser.add_argument("--configuration",type=Path)
    parser.add_argument("--output",type=Path)
    a = parser.parse_args()
    if a.mode == "controls": answer = controls(a.directory.resolve())
    elif a.mode == "configure": answer = configure(a.preflight_directory.resolve(),a.exact_controls.resolve(),a.numeric_controls.resolve(),a.cold_controls.resolve(),a.output.resolve())
    elif a.mode == "_forward": answer = forward(a.configuration.resolve(),a.directory.resolve())
    else: answer = run(a.configuration.resolve(),a.directory.resolve())
    print(json.dumps({k:answer[k] for k in ("status","seconds","exact_exclusions","all54_low_branches_excluded") if k in answer}),flush=True)
