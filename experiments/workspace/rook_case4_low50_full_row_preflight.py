"""Prepare and audit the complete low50 matrix without any optimizer call.

Configuration and tiny controls do not read the large matrix coefficients.
The full preflight is a distinct, separately gated owned action.
"""
from pathlib import Path
import argparse
import gzip
import hashlib
import json
import os
import resource
import shutil
import sys
import time

import rook_case4_full_native_transport as transport

ROOT = Path(__file__).resolve().parents[2]
LOG = ROOT/"experiments/logs/grids-and-triangles"
TRANSPORT_SHA = "70b08007e9d9cfc527731cb79ae4d35b6c634880c8096047246a4f056dcb4b86"
OWNER_SHA = "aa557c7b99ec3de71e9ecde3f6f7dfa3ca71066a835086cdd3b3f2eb7be558e5"
OWNER_HELPER_SHA = "54330f430c0c4dae03a0298533121ce43482ceb295f54df715ad2f2180d3503c"
CORE = ("coefficients","column_indices","row_pointers","row_lower","row_upper","original_column_ids")
INPUTS = {
    "scope": ("rook-case4-low50-full-row-scope01.json","2e04787dc089be866fa25d766e7c55f965411941a7d1cce94caa0d0aacf98e84"),
    "small_spec": ("rook-case4-low54-native-lp-preparation02/specification.json.gz","b037035bb6756bcb259cc06fc6ae22781f343fedeb38c8ec923dcb19fdb50164"),
    "small_cold": ("rook-case4-low54-native-lp-run01/cold.json","ea492ec530c512759b93d25afc6900a2468d1f221f75aac2eb39092bd8af73f3"),
    "small_analysis": ("rook-case4-low54-native-lp-run01-analysis.json","0e1cc245793cd1174699bd831355b92f72f7476570c083b1146515995dd6eaa6"),
    "old_state": ("rook-case4-box-cut-lp-run01/state-numeric.json","0d9427431e87f4a9c1f02030e3a80c23d0f3d53faacbe3ff7767d5dc6f3d6a14"),
    "old_point": ("rook-case4-box-cut-lp-run01/exact/candidate.json","7fda72c6a212a6ebe504c03a17f66c05c8545d33e4aebc651f42f817cc3a4bd9"),
    "old_point_cold": ("rook-case4-box-cut-lp-run01/exact/cold.json","b69a3a38aeb911c45657871544f21897bc4f9bb6201675c1eab5f45ca8a5c317"),
    "old_model": ("rook-case4-face112-weighted-parity-model01/model.json","c6cd72c995ce1a47db90fe7263f643131bc555ed50e329c7734536f5cf870ac3"),
    "old_model_cold": ("rook-case4-face112-weighted-parity-model01-cold-replay.json","567185c755134fcf7c15bb7be762bb2a70a503254259b2eb44a92f91abb39156"),
    "old_archive": ("rook-case4-face112-weighted-parity-model01/arrays.npz","59a06470793e6959a67ae30dfb29ecf0de4c8aa74661e1335d7676aa612c1e7e"),
    "old_native_configuration": ("rook-case4-low54-native-lp-query-configuration01.json","a0ac53ac6969ceeaaeedd2fabfa38d8944dd856c85bb461113a70cd92784c272"),
    "tiny_native_controls": ("rook-case4-full-native-transport-controls02.json","e45d07c9547c7995c9d4700aee4cf7af47cdfe72a844c72001013a26eb8dd800"),
}
LIMITS = {"preflight_seconds":60,"preflight_owner_seconds":90,
    "metadata_bytes":8*1024**2,"safety_disk_reserve_bytes":64*1024**2,
    "future_transcript_bytes":128*1024**2,"future_branch_temporary_bytes":4*1024**2,
    "future_metadata_bytes":16*1024**2,"native_solver_calls":0}


def sha(b):
    return hashlib.sha256(b).hexdigest()


def file_ref(path):
    path = Path(path).resolve()
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024**2),b""):
            h.update(chunk)
    return {"path":str(path.relative_to(ROOT)),"bytes":path.stat().st_size,"sha256":h.hexdigest()}


def read_ref(ref):
    p = ROOT/ref["path"]
    actual = file_ref(p)
    assert all(actual[k] == ref[k] for k in ref)
    b = p.read_bytes()
    return json.loads(gzip.decompress(b) if p.suffix == ".gz" else b)


def write(path,value):
    assert not path.exists()
    b = (json.dumps(value,sort_keys=True,indent=2)+"\n").encode()
    assert len(b) <= LIMITS["metadata_bytes"]
    with path.open("xb") as f:
        f.write(b);f.flush();os.fsync(f.fileno())


def source_bindings():
    assert file_ref(Path(transport.__file__))["sha256"] == TRANSPORT_SHA
    owner = ROOT/"experiments/workspace/rook_case4_box_hull_membership_query.py"
    owner_helper = ROOT/"experiments/workspace/rook_case4_box_hull_membership.py"
    assert file_ref(owner)["sha256"] == OWNER_SHA and file_ref(owner_helper)["sha256"] == OWNER_HELPER_SHA
    return {"preflight":file_ref(Path(__file__)),"transport":file_ref(Path(transport.__file__)),
        "owner":file_ref(owner),"owner_helper":file_ref(owner_helper)}


def context():
    refs, data = {}, {}
    for name,(path,expected) in INPUTS.items():
        p = LOG/path
        actual = file_ref(p)
        assert actual["sha256"] == expected
        refs[name] = actual
        if name != "old_archive":
            data[name] = read_ref(actual)
    scope, spec, cold = data["scope"],data["small_spec"],data["small_cold"]
    assert cold["status"] == "PASS" and cold["exact_exclusions"] == 4
    excluded = {c["whole_cover_box_index"] for c in cold["checks"]}
    branches = [x for x in spec["selected54_boxes"] if x["index"] not in excluded]
    assert len(branches) == 50 and len(spec["all191_boxes"]) == 191
    assert [x["index"] for x in branches] == scope["selected_whole_cover_indices"]
    assert [x["index"] for x in branches] == data["small_analysis"]["unexcluded_whole_cover_indices"]
    ids = spec["original_column_ids"]
    assert len(ids) == len(set(ids)) == 1102 and len(spec["proved_zero_columns"]) == 112
    for b in branches:
        assert len(b["state"]) == 1102 and set(b["state"]) <= set("01?")
        assert sha(bytes({"0":0,"1":1,"?":255}[x] for x in b["state"])) == b["state_sha256"]
        assert all(b["state"][ids.index(a)] == "1" for a in b["selected"])
    old = data["old_state"]["cuts"]
    assert len(old) == 6 and data["old_point_cold"]["exact_point_replayed"]
    assert data["old_point_cold"]["candidate_sha256"] == refs["old_point"]["sha256"]
    assert data["old_point_cold"]["full_face_rows_checked"] == 167121
    assert data["old_point"]["registry_sha256"] == data["old_point_cold"]["registry_sha256"]
    assert sha((json.dumps(old,sort_keys=True,separators=(",",":"))+"\n").encode()) == data["old_point"]["registry_sha256"]
    for a,b in zip(old[:5],spec["rows"][2280:2285]):
        assert a["certificate"]["inequality"]["terms"] == b["original_terms"]
        assert a["certificate"]["inequality"]["upper"] == b["upper"]
    assert old[5]["certificate"]["inequality"]["terms"] == spec["rows"][2287]["original_terms"]
    assert old[5]["certificate"]["inequality"]["upper"] == 1
    added = []
    for index,family in ((2285,"proved_H42_upper_five"),(2286,"proved_strengthened_H")):
        row = spec["rows"][index]
        assert row["family"] == family
        added.append({"family":family,"terms":row["original_terms"],"lower":row["lower"],
            "upper":row["upper"],"source_small_row":index})
    for c in cold["checks"]:
        added.append({"family":"exact_low54_pair_nogood","terms":c["nogood"]["terms"],
            "lower":0,"upper":1,"certificate":c["certificate"],
            "whole_cover_box_index":c["whole_cover_box_index"]})
    assert [len(x["terms"]) for x in added] == [42,44,2,2,2,2]
    assert data["tiny_native_controls"]["source_sha256"] == TRANSPORT_SHA
    assert data["tiny_native_controls"]["status"] == "PASS_TINY_SIGNED_RAW_ARRAY_TRANSPORT_NO_SOLVE"
    assert data["tiny_native_controls"]["native_solver_calls"] == 0
    return {"inputs":refs,"data":data,"ids":ids,"branches":branches,"old_registry":old,"added":added}


def suffix(ids,base_nonzeros,old_rows,extra_rows):
    inverse = {int(a):j for j,a in enumerate(ids)}
    assert len(inverse) == len(ids)
    n = len(ids)
    records = [{"terms":[[j,1],[n,-1]],"lower":0,"upper":1} for j in range(n)]
    for original in old_rows+extra_rows:
        terms = original["terms"]
        assert terms == sorted(terms) and len({a for a,c in terms}) == len(terms)
        assert all(type(a) is type(c) is int and a in inverse and c != 0 for a,c in terms)
        lower = original.get("lower",sum(min(c,0) for a,c in terms))
        upper = original["upper"]
        assert type(lower) is type(upper) is int and lower <= upper
        records.append({"terms":[[inverse[a],c] for a,c in terms],"lower":lower,"upper":upper})
    tails = {k:[] for k in CORE if k != "original_column_ids"}
    offset = base_nonzeros
    for row in records:
        for j,c in row["terms"]:
            tails["column_indices"].append(j);tails["coefficients"].append(c)
        offset += len(row["terms"])
        tails["row_pointers"].append(offset)
        tails["row_lower"].append(row["lower"]);tails["row_upper"].append(row["upper"])
    return tails,records


def array_binding(value):
    assert value.flags.c_contiguous
    return {"dtype":str(value.dtype),"shape":list(value.shape),
        "sha256":hashlib.sha256(memoryview(value).cast("B")).hexdigest()}


def stitch_archive(path,base_hashes,tails,checkpoint,deadline):
    import numpy as np
    arrays = {}
    with np.load(path,allow_pickle=False) as archive:
        for name in CORE:
            transport.deadline_check(deadline)
            base = archive[name]
            assert base.ndim == 1 and base.flags.c_contiguous and base.dtype.kind in "iu"
            assert array_binding(base)["sha256"] == base_hashes[name]
            addition = tails.get(name,[])
            if addition:
                out = np.empty(len(base)+len(addition),dtype=base.dtype)
                out[:len(base)] = base
                out[len(base):] = np.asarray(addition,dtype=base.dtype)
            else:
                out = base
            old = checkpoint[name]
            assert len(old["shape"]) == 1
            assert array_binding(out[:old["shape"][0]]) == old, ("old prefix",name)
            arrays[name] = out
            del base
    return arrays


def budget():
    rows,nnz,n = 167127,10769860,1102
    primary = 8*nnz+4*nnz+8*(rows+1)+16*rows+2*n
    # ZIP/NPY overhead and worst-case compression expansion reserve.
    archive_ceiling = primary+1024**2
    preflight_disk = archive_ceiling+LIMITS["metadata_bytes"]+LIMITS["safety_disk_reserve_bytes"]
    future_disk = archive_ceiling+LIMITS["future_transcript_bytes"]+LIMITS["future_branch_temporary_bytes"]+LIMITS["future_metadata_bytes"]+LIMITS["safety_disk_reserve_bytes"]
    return {"primary_integer_array_RAM_bytes":primary,
        "one_input_base_coefficient_RAM_bytes":8*10767292,
        "largest_native_float64_coefficient_argument_RAM_bytes":8*nnz,
        "nominal_native_value_and_index_payload_RAM_bytes":12*nnz,
        "maximum_row_getter_payload_bytes":transport.BLOCK_ROWS*(1103*12+20)+4,
        "actual_native_internal_RSS_requires_measurement":True,
        "new_compressed_archive_ceiling_bytes":archive_ceiling,
        "uncompressed_matrix_written_to_disk":False,
        "native_matrix_copies_written_to_disk":False,
        "preflight_additional_disk_requirement_including_reserve":preflight_disk,
        "future_total_additional_disk_requirement_including_reserve":future_disk,
        "archive_atomic_rename_creates_no_second_complete_copy":True}


def controls(directory):
    import numpy as np
    directory.mkdir(parents=True,exist_ok=False)
    ids = [2,5,8]
    base = {"coefficients":np.asarray([1,1],dtype=np.int64),
        "column_indices":np.asarray([0,2],dtype=np.int32),"row_pointers":np.asarray([0,2],dtype=np.int64),
        "row_lower":np.asarray([0],dtype=np.int64),"row_upper":np.asarray([1],dtype=np.int64),
        "original_column_ids":np.asarray(ids,dtype=np.uint16)}
    old = [{"terms":[[2,-1],[8,1]],"upper":0}]
    extra = [{"terms":[[5,2],[8,1]],"lower":0,"upper":2}]
    tails,rows = suffix(ids,2,old,extra)
    expected = {
        "coefficients":[1,1,1,-1,1,-1,1,-1,-1,1,2,1],
        "column_indices":[0,2,0,3,1,3,2,3,0,2,1,2],
        "row_pointers":[0,2,4,6,8,10,12],
        "row_lower":[0,0,0,0,-1,0],"row_upper":[1,1,1,1,0,2],
        "original_column_ids":ids}
    expected = {k:np.asarray(v,dtype=base[k].dtype) for k,v in expected.items()}
    lengths = {"coefficients":10,"column_indices":10,"row_pointers":6,"row_lower":5,"row_upper":5,"original_column_ids":3}
    checkpoint = {k:array_binding(v[:lengths[k]]) for k,v in expected.items()}
    path = directory/"tiny-base.npz"
    np.savez_compressed(path,**base)
    hashes = {k:array_binding(v)["sha256"] for k,v in base.items()}
    built = stitch_archive(path,hashes,tails,checkpoint,time.monotonic()+10)
    assert all(np.array_equal(built[k],expected[k]) for k in CORE)
    assert rows[-1]["terms"] == [[1,2],[2,1]]
    rejected = 0
    for bad in [
        {"terms":[[5,1],[5,2]],"upper":2},
        {"terms":[[7,1]],"upper":1},
        {"terms":[[5,0]],"upper":1},
        {"terms":[[5,1]],"lower":2,"upper":1}]:
        try: suffix(ids,2,old,[bad])
        except AssertionError: rejected += 1
        else: raise AssertionError("invalid suffix accepted")
    broken = {k:dict(v) for k,v in checkpoint.items()}
    broken["coefficients"]["sha256"] = "0"*64
    try: stitch_archive(path,hashes,tails,broken,time.monotonic()+10)
    except AssertionError: rejected += 1
    else: raise AssertionError("wrong old prefix accepted")
    report = {"status":"PASS_TINY_STREAMED_CSR_SUFFIX_CONTROLS_NO_NATIVE",
        "source":file_ref(Path(__file__)),"matrix_arrays_checked":6,"malformed_inputs_rejected":rejected,
        "signed_coefficients_and_coefficient_two_checked":True,"original_ids_nonidentity":ids,
        "hand_specified_old_prefix_and_full_output":True,
        "tiny_base":file_ref(path),"native_imports":0,"optimizer_calls":0,"full_matrix_loaded":False}
    write(directory/"report.json",report)
    return report


def configure(controls_directory,output):
    ctx = context()
    controls_ref = file_ref(controls_directory/"report.json")
    ctl = read_ref(controls_ref)
    assert ctl["status"] == "PASS_TINY_STREAMED_CSR_SUFFIX_CONTROLS_NO_NATIVE"
    assert ctl["source"] == file_ref(Path(__file__))
    disk = budget()
    free = shutil.disk_usage(ROOT).free
    assert free >= disk["preflight_additional_disk_requirement_including_reserve"]
    value = {"status":"PREPARED_ZERO_SOLVE_FULL50_NATIVE_PREFLIGHT_NO_FULL_MATRIX_LOADED",
        "source_bindings":source_bindings(),"inputs":ctx["inputs"],"suffix_controls":controls_ref,
        "limits":LIMITS,"disk_and_memory_plan":disk,"observed_free_disk_bytes":free,
        "rows":167127,"nonzeros":10769860,"variables":1103,
        "old_prefix_rows":167121,"old_prefix_nonzeros":10769766,
        "bound_resets":50,"selected_whole_cover_indices":[x["index"] for x in ctx["branches"]],
        "new_original_rows":ctx["added"],"all_objective_coefficients":0,"t_bounds":[0,0],
        "runtime":ctx["data"]["old_native_configuration"]["runtime"],
        "native_solver_calls_permitted":0,
        "future_query_requires_distinct_driver_configuration_and_root_gate":True}
    write(output,value)
    return value


def load_configuration(path):
    value = json.loads(path.read_bytes())
    assert value["status"] == "PREPARED_ZERO_SOLVE_FULL50_NATIVE_PREFLIGHT_NO_FULL_MATRIX_LOADED"
    assert value["source_bindings"] == source_bindings() and value["limits"] == LIMITS
    assert value["disk_and_memory_plan"] == budget() and value["native_solver_calls_permitted"] == 0
    ctx = context()
    assert value["inputs"] == ctx["inputs"] and value["new_original_rows"] == ctx["added"]
    assert value["selected_whole_cover_indices"] == [x["index"] for x in ctx["branches"]]
    ctl = read_ref(value["suffix_controls"])
    assert ctl["source"] == file_ref(Path(__file__)) and ctl["status"] == "PASS_TINY_STREAMED_CSR_SUFFIX_CONTROLS_NO_NATIVE"
    return value,ctx


def child(configuration,directory):
    started = time.monotonic()
    deadline = started+LIMITS["preflight_seconds"]
    directory.mkdir(parents=True,exist_ok=False)
    report = {"status":"UNRESOLVED_PREFLIGHT_NOT_COMPLETE","configuration":file_ref(configuration),
        "native_solver_calls":0,"stage":"binding"}
    h = None
    try:
        cfg,ctx = load_configuration(configuration)
        assert shutil.disk_usage(ROOT).free >= budget()["preflight_additional_disk_requirement_including_reserve"]
        report["stage"] = "imports"
        import numpy as np
        import highspy
        import highspy._core
        import importlib.metadata
        import platform
        runtime = {"python":platform.python_version(),"python_executable":sys.executable,
            "highspy":importlib.metadata.version("highspy"),"numpy":np.__version__,
            "highs_version":highspy.Highs().version(),
            "native_extension_sha256":sha(Path(highspy._core.__file__).read_bytes())}
        assert runtime == cfg["runtime"]
        report["stage"] = "streamed_prefix_and_suffix"
        old_rows = [x["certificate"]["inequality"] for x in ctx["old_registry"]]
        tails,records = suffix(ctx["ids"],10767292,old_rows,ctx["added"])
        arrays = stitch_archive(ROOT/ctx["inputs"]["old_archive"]["path"],
            ctx["data"]["old_model"]["array_sha256"],tails,
            ctx["data"]["old_point"]["matrix_binding"],deadline)
        assert len(arrays["row_lower"]) == 167127 and len(arrays["coefficients"]) == 10769860
        assert arrays["original_column_ids"].tolist() == ctx["ids"]
        for k,row in enumerate(records):
            r = 166013+k
            lo,hi = map(int,arrays["row_pointers"][r:r+2])
            actual = [[int(j),int(c)] for j,c in zip(arrays["column_indices"][lo:hi],arrays["coefficients"][lo:hi])]
            assert actual == row["terms"]
            assert int(arrays["row_lower"][r]) == row["lower"] and int(arrays["row_upper"][r]) == row["upper"]
        binding = {k:array_binding(v) for k,v in arrays.items()}
        report["stage"] = "raw_array_native_load"
        lower,upper = [0]*1103,[1]*1102+[0]
        h = transport.build_native(arrays,1103,lower,upper,deadline)
        report["stage"] = "bounded_native_coefficient_audit"
        audit = transport.audit_native(h,arrays,1103,lower,upper,deadline)
        report["stage"] = "all50_bound_resets"
        resets = []
        for index,b in enumerate(ctx["branches"]):
            transport.deadline_check(deadline)
            lo = [int(c=="1") for c in b["state"]]+[0]
            hi = [int(c!="0") for c in b["state"]]+[0]
            reset = transport.reset_box(h,lo,hi)
            resets.append({"low50_index":index,"whole_cover_box_index":b["index"],
                "state_sha256":b["state_sha256"],"positive_guard":b["selected"],"bounds_sha256":reset})
        assert h.getRunTime() == 0 and not h.getSolution().value_valid
        h.clear();h = None
        report["stage"] = "durable_cached_arrays"
        transport.deadline_check(deadline)
        path = directory/"arrays.npz"
        temporary = directory/"arrays.partial.npz"
        assert not path.exists() and not temporary.exists()
        with temporary.open("xb") as f:
            np.savez_compressed(f,**arrays)
            f.flush();os.fsync(f.fileno())
        assert temporary.stat().st_size <= budget()["new_compressed_archive_ceiling_bytes"]
        temporary.replace(path)
        transport.deadline_check(deadline)
        model = {"status":"EXACT_FROZEN_SIX_CUT_PREFIX_PLUS_SIX_ACCEPTED_ROWS",
            "configuration":file_ref(configuration),"matrix_binding":binding,"arrays":file_ref(path),
            "rows":167127,"nonzeros":10769860,"variables":1103,"selector_variables":1102,
            "artificial_t_fixed_zero":True,"old_exact_matrix_prefix":ctx["data"]["old_point"]["matrix_binding"],
            "new_original_rows":ctx["added"],"base_archive":ctx["inputs"]["old_archive"],
            "prior_point_cold":ctx["inputs"]["old_point_cold"],"prior_branch_cold":ctx["inputs"]["small_cold"],
            "all164044_retained_covers_preserved":True,"original_cover_supports_rebuilt":False}
        write(directory/"model.json",model)
        report.update(status="PASS_COMPLETE_FULL50_NATIVE_TRANSPORT_AND_BOUND_RESETS_NO_SOLVE",
            runtime=runtime,native_audit=audit,bound_resets=resets,
            matrix=file_ref(directory/"model.json"),arrays=file_ref(path),matrix_binding=binding,
            free_disk_bytes_after=shutil.disk_usage(ROOT).free,full_case_matrix_loaded=True)
    except Exception as error:
        report.update(status="UNRESOLVED_PREFLIGHT_ERROR",error_type=type(error).__name__,error=str(error))
    finally:
        if h is not None: h.clear()
        report["seconds"] = time.monotonic()-started
        report["peak_rss_KiB"] = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        write(directory/"result.json",report)
    return report


def preflight(configuration,directory):
    cfg,ctx = load_configuration(configuration)
    assert not directory.exists()
    directory.mkdir(parents=True)
    import rook_case4_box_hull_membership_query as owner
    assert file_ref(Path(owner.__file__))["sha256"] == OWNER_SHA
    receipt = owner.owned([sys.executable,str(Path(__file__).resolve()),"_child",
        "--configuration",str(configuration),"--directory",str(directory/"child")],
        directory,LIMITS["preflight_owner_seconds"],"preflight",True)
    write(directory/"supervisor.json",receipt)
    path = directory/"child/result.json"
    accepted = owner.success(receipt) and path.exists()
    report = json.loads(path.read_bytes()) if path.exists() else None
    accepted = bool(accepted and report["status"] == "PASS_COMPLETE_FULL50_NATIVE_TRANSPORT_AND_BOUND_RESETS_NO_SOLVE"
        and report["seconds"] <= LIMITS["preflight_seconds"])
    result = {"status":"ACCEPTED_ZERO_SOLVE_PREFLIGHT" if accepted else "UNRESOLVED_PREFLIGHT",
        "configuration":file_ref(configuration),"supervisor":file_ref(directory/"supervisor.json"),
        "report":file_ref(path) if path.exists() else None,"accepted":accepted,
        "native_solver_calls":0,"automatic_retries":0}
    write(directory/"result.json",result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode",choices=("controls","configure","preflight","_child"))
    parser.add_argument("--configuration",type=Path)
    parser.add_argument("--directory",type=Path)
    parser.add_argument("--controls-directory",type=Path)
    parser.add_argument("--output",type=Path)
    a = parser.parse_args()
    if a.mode == "controls": result = controls(a.directory.resolve())
    elif a.mode == "configure": result = configure(a.controls_directory.resolve(),a.output.resolve())
    elif a.mode == "preflight": result = preflight(a.configuration.resolve(),a.directory.resolve())
    else: result = child(a.configuration.resolve(),a.directory.resolve())
    print(json.dumps({k:result[k] for k in ("status","accepted","seconds","native_solver_calls") if k in result}),flush=True)


if __name__ == "__main__":
    main()

