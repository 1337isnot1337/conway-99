"""Exact certificates for the 50 remaining low boxes on the complete matrix.

The cached matrix is the independently accepted six-cut prefix plus six
already proved rows.  The artificial floor variable is fixed to zero.
A numerical ray is only a proposal for an integer row combination.
"""
from pathlib import Path
import argparse
from collections import Counter
import gzip
import hashlib
from itertools import product
import json
from math import gcd, isfinite
import os
import time

ROOT = Path(__file__).resolve().parents[2]
LOG = ROOT/"experiments/logs/grids-and-triangles"
PREFLIGHT_SOURCE = ("experiments/workspace/rook_case4_low50_full_row_preflight.py",
    "f994cf266882974325dd64c5516e639a5f54827f0a74f1813095661e84b80193")
TRANSPORT_SOURCE = ("experiments/workspace/rook_case4_full_native_transport.py",
    "70b08007e9d9cfc527731cb79ae4d35b6c634880c8096047246a4f056dcb4b86")
CORE = ("coefficients","column_indices","row_pointers","row_lower","row_upper","original_column_ids")
SCALES = (1,2,4,8,16,64,256,4096,65536,1000000)
LIMITS = {"branches":50,"calls_per_branch":1,"requested_native_seconds_per_branch":2.0,
    "cumulative_native_seconds":120.0,"forward_seconds":240,"forward_owner_seconds":300,
    "cold_seconds":120,"cold_owner_seconds":150,"maximum_transcript_bytes":128*1024**2,
    "maximum_numeric_record_bytes":4*1024**2,"maximum_metadata_bytes":16*1024**2,
    "safety_disk_reserve_bytes":64*1024**2,"maximum_exact_integer_bits":4096,
    "threads":1,"automatic_retries":0,"extra_ray_solves":0,"branch_feedback":False}


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


def write(path,value):
    path = Path(path)
    assert not path.exists()
    path.parent.mkdir(parents=True,exist_ok=True)
    raw = canonical(value)+b"\n"
    assert len(raw) <= LIMITS["maximum_metadata_bytes"]
    temporary = path.with_name(path.name+".partial")
    with temporary.open("xb") as stream:
        stream.write(raw);stream.flush();os.fsync(stream.fileno())
    temporary.replace(path)
    return reference(path)


def deadline_check(deadline):
    if deadline is not None and time.monotonic() >= deadline:
        raise TimeoutError("full50 exact arithmetic deadline")


def source_bindings():
    result = {"helper":reference(Path(__file__))}
    for name,(path,digest) in (("preflight",PREFLIGHT_SOURCE),("transport",TRANSPORT_SOURCE)):
        result[name] = reference(ROOT/path)
        assert result[name]["sha256"] == digest
    return result


def state_bounds(state,with_floor=True):
    assert type(state) is str and set(state) <= set("01?")
    lower = [int(v == "1") for v in state]
    upper = [int(v != "0") for v in state]
    return (lower+[0],upper+[0]) if with_floor else (lower,upper)


def coverage(specification,previous_cold):
    """Bind the whole cover before using a low branch's conditional box."""
    spec = specification
    data = {name:read({"path":path,"sha256":digest})
        for name,(path,digest) in spec["input_bindings"].items()}
    compact, cold, owner = data["boxes"],data["box_cold"],data["box_cold_owner"]
    assert cold["status"] == "PASS" and cold["checked"] == 260
    assert (cold["checked_fixed_points"],cold["checked_contradictions"],cold["checked_partial"]) == (191,69,0)
    assert cold["all260_nonpartial_branches_checked"]
    assert cold["prior184_contradictions_and_complete_original_branch_cover_bound"]
    assert owner["exit_code"] == 0 and owner["child_reaped"] and not owner["hard_timeout"]
    assert owner["child_result"]["sha256"] == spec["input_bindings"]["box_cold"][1]
    ids,zeros = spec["original_column_ids"],spec["proved_zero_columns"]
    assert ids == sorted(set(range(1214))-set(zeros)) and len(ids) == 1102 and len(zeros) == 112
    assert compact["original_column_ids"] == ids and compact["proved_zero_columns"] == zeros
    assert compact["boxes"] == spec["all191_boxes"] and len(compact["boxes"]) == 191
    weights,rhs = [0]*1214,0
    native_gram = data["native"]["primary_inventory"]["Gram_rows"]
    for r in (214,344,582):
        _,_,quota,support = native_gram[r]
        assert type(quota) is int
        rhs += quota
        for a in support:
            weights[a] += 1
    assert rhs == 3
    live = {a:weights[a] for a in ids if weights[a]}
    assert Counter(live.values()) == {1:26,2:9,3:1}
    assert spec["partition"]["H27"] == [a for a in ids if weights[a] % 2]
    assert spec["partition"]["Q"] == [a for a in ids if weights[a]//2]
    position = {a:j for j,a in enumerate(ids)}
    proofs = {b["index"]:b for b in compact["all260_proof_bindings"]}
    low,high = [],[]
    for b in compact["boxes"]:
        state = b["state"]
        assert len(state) == 1102 and set(state) <= set("01?")
        assert sha(bytes(255 if v == "?" else int(v) for v in state)) == b["state_sha256"]
        assert all(state[position[a]] != "?" for a in live)
        selected = [a for a in live if state[position[a]] == "1"]
        assert selected == b["selected"] and sum(live[a] for a in selected) == 3
        odd = sum(live[a] % 2 for a in selected)
        assert odd in (1,3)
        if odd == 1:
            assert len(selected) in (1,2)
            low.append({**b,"pilot_index":len(low),"proof_binding":proofs[b["index"]]})
        else:
            high.append(b)
    assert len(low) == 54 and len(high) == 137 and low == spec["selected54_boxes"]
    assert previous_cold["status"] == "PASS" and previous_cold["completed_native_records"] == 54
    assert previous_cold["exact_exclusions"] == len(previous_cold["checks"]) == 4
    assert not previous_cold["incomplete_transcript_tail_bytes"]
    old = {x["whole_cover_box_index"]:x for x in previous_cold["checks"]}
    assert sorted(old) == [10,11,15,64]
    for b in low:
        if b["index"] in old:
            assert old[b["index"]]["nogood"] == {"terms":[[a,1] for a in b["selected"]],"upper":len(b["selected"])-1}
    remaining = [b for b in low if b["index"] not in old]
    assert len(remaining) == 50
    return {"ids":ids,"zeros":zeros,"branches":remaining,"all191_boxes":compact["boxes"],
        "partition":spec["partition"],"prior_excluded_indices":sorted(old),
        "branch_ancestor_bindings":spec["input_bindings"],"whole_cover":spec["whole_cover"]}


def load_preflight(directory):
    directory = Path(directory).resolve()
    terminal_ref = reference(directory/"result.json")
    terminal = read(terminal_ref)
    assert terminal["status"] == "ACCEPTED_ZERO_SOLVE_PREFLIGHT" and terminal["accepted"]
    assert terminal["native_solver_calls"] == terminal["automatic_retries"] == 0
    report,owner,cfg = read(terminal["report"]),read(terminal["supervisor"]),read(terminal["configuration"])
    assert owner["exit_code"] == 0 and owner["child_reaped"] and not owner["hard_timeout"]
    assert report["status"] == "PASS_COMPLETE_FULL50_NATIVE_TRANSPORT_AND_BOUND_RESETS_NO_SOLVE"
    assert report["native_solver_calls"] == 0 and report["seconds"] <= 60
    assert report["configuration"] == terminal["configuration"]
    assert cfg["source_bindings"]["preflight"]["sha256"] == PREFLIGHT_SOURCE[1]
    assert cfg["source_bindings"]["transport"]["sha256"] == TRANSPORT_SOURCE[1]
    for ref in cfg["source_bindings"].values():
        assert reference(ROOT/ref["path"]) == ref
    model = read(report["matrix"])
    assert model["configuration"] == terminal["configuration"]
    assert (model["rows"],model["nonzeros"],model["variables"],model["selector_variables"]) == (167127,10769860,1103,1102)
    assert model["artificial_t_fixed_zero"] and model["all164044_retained_covers_preserved"]
    assert model["arrays"] == report["arrays"] and model["matrix_binding"] == report["matrix_binding"]
    assert model["new_original_rows"] == cfg["new_original_rows"]
    spec,cold = read(cfg["inputs"]["small_spec"]),read(cfg["inputs"]["small_cold"])
    domain = coverage(spec,cold)
    assert cfg["selected_whole_cover_indices"] == [b["index"] for b in domain["branches"]]
    assert len(report["bound_resets"]) == 50
    for k,b in enumerate(domain["branches"]):
        lower,upper = state_bounds(b["state"])
        assert report["bound_resets"][k] == {"low50_index":k,"whole_cover_box_index":b["index"],
            "state_sha256":b["state_sha256"],"positive_guard":b["selected"],
            "bounds_sha256":sha(canonical([lower,upper]))}
    audit = report["native_audit"]
    assert (audit["variables"],audit["rows"],audit["nonzeros"]) == (1103,167127,10769860)
    assert audit["exact_all_native_coefficients_and_bounds"] and audit["native_solver_calls"] == 0
    return {"terminal_ref":terminal_ref,"terminal":terminal,"configuration":cfg,
        "report":report,"model":model,"domain":domain,"small_spec":spec}


def array_binding(value):
    assert value.flags.c_contiguous
    return {"dtype":str(value.dtype),"shape":list(value.shape),"sha256":sha(memoryview(value).cast("B"))}


def load_arrays(preflight,deadline):
    import numpy as np
    model = preflight["model"]
    ref = model["arrays"]
    assert reference(ROOT/ref["path"]) == ref
    arrays = {}
    with np.load(ROOT/ref["path"],allow_pickle=False) as archive:
        assert set(archive.files) == set(CORE)
        for name in CORE:
            deadline_check(deadline)
            value = archive[name]
            assert value.ndim == 1 and value.dtype.kind in "iu"
            assert array_binding(value) == model["matrix_binding"][name]
            previous = model["old_exact_matrix_prefix"][name]
            assert array_binding(value[:previous["shape"][0]]) == previous
            arrays[name] = value
    assert arrays["original_column_ids"].tolist() == preflight["domain"]["ids"]
    inverse = {a:j for j,a in enumerate(preflight["domain"]["ids"])}
    for k,row in enumerate(model["new_original_rows"]):
        r = 167121+k
        begin,end = map(int,arrays["row_pointers"][r:r+2])
        assert [[int(j),int(c)] for j,c in zip(arrays["column_indices"][begin:end],arrays["coefficients"][begin:end])] == [[inverse[a],c] for a,c in row["terms"]]
        assert int(arrays["row_lower"][r]) == row["lower"] and int(arrays["row_upper"][r]) == row["upper"]
    deadline_check(deadline)
    return arrays


def combination(arrays,multipliers,lower,upper,deadline=None):
    assert len(lower) == len(upper)
    assert all(type(a) is type(b) is int and 0 <= a <= b <= 1 for a,b in zip(lower,upper))
    assert multipliers == sorted(multipliers) and len({r for r,v in multipliers}) == len(multipliers)
    c,j,p = arrays["coefficients"],arrays["column_indices"],arrays["row_pointers"]
    l,u = arrays["row_lower"],arrays["row_upper"]
    vector,bound,terms = [0]*len(lower),0,0
    for r,value in multipliers:
        deadline_check(deadline)
        assert type(r) is type(value) is int and 0 <= r < len(l) and value != 0
        assert abs(value).bit_length() <= LIMITS["maximum_exact_integer_bits"]
        bound += value*int(u[r] if value > 0 else l[r])
        for k in range(int(p[r]),int(p[r+1])):
            col,coefficient = int(j[k]),int(c[k])
            assert 0 <= col < len(vector)
            vector[col] += value*coefficient
            terms += 1
            if terms % 8192 == 0:
                deadline_check(deadline)
    minimum = sum(v*(lo if v >= 0 else hi) for v,lo,hi in zip(vector,lower,upper))
    assert all(abs(v).bit_length() <= LIMITS["maximum_exact_integer_bits"] for v in vector+[bound,minimum])
    return vector,bound,minimum,terms


def exclusion(preflight,arrays,index,multipliers,deadline=None):
    domain = preflight["domain"]
    branch = domain["branches"][index]
    lower,upper = state_bounds(branch["state"])
    assert len(lower) == 1103 and lower[-1] == upper[-1] == 0
    vector,bound,minimum,terms = combination(arrays,multipliers,lower,upper,deadline)
    if minimum <= bound:
        return None
    full,full_lower,full_upper = [0]*1214,[0]*1214,[0]*1214
    for j,a in enumerate(domain["ids"]):
        full[a],full_lower[a],full_upper[a] = vector[j],lower[j],upper[j]
    assert sum(min(c*lo,c*hi) for c,lo,hi in zip(full,full_lower,full_upper)) == minimum
    guards = branch["selected"]
    assert len(guards) in (1,2) and all(full_lower[a] == 1 for a in guards)
    return {"kind":"EXACT_FULL_ROW_CONDITIONAL_BOX_EXCLUSION","low50_index":index,
        "whole_cover_box_index":branch["index"],"prior_branch_id":branch["prior_branch_id"],
        "raw_pattern_id":branch["raw_id"],"state_sha256":branch["state_sha256"],
        "cold_branch_proof":branch["proof_binding"],"preflight_model":preflight["report"]["matrix"],
        "row_multipliers":[[r,str(v)] for r,v in multipliers],"terms_contracted":terms,
        "combined_row_upper":str(bound),"minimum_over_entire_box":str(minimum),
        "positive_gap":str(minimum-bound),"full1214_coefficients":list(map(str,full)),
        "full1214_bounds_sha256":sha(canonical([full_lower,full_upper])),
        "coordinate_lift":"projected row combination representative modulo the 112 proved zero equalities",
        "proved_zero_columns":domain["zeros"],"floor_coefficient":str(vector[-1]),"floor_bounds":[0,0],
        "conditional_guards":guards,"implied_Boolean_nogood":{"terms":[[a,1] for a in guards],"upper":len(guards)-1},
        "numerical_ray_feasibility_assumed":False,"whole_case_cover_used":191,
        "case4_excluded":False,"whole_graph_problem_resolved":False}


def rounded_proposals(values):
    sparse = [(r,float(v)) for r,v in enumerate(values) if float(v) != 0.0]
    assert all(isfinite(v) for r,v in sparse)
    if not sparse:
        return
    maximum = max(abs(v) for r,v in sparse)
    normalized = [(r,v/maximum) for r,v in sparse]
    seen = set()
    for scale in SCALES:
        integers = [(r,int(round(v*scale))) for r,v in normalized]
        divisor = 0
        for r,v in integers:
            divisor = gcd(divisor,v)
        if not divisor:
            continue
        for orientation in (1,-1):
            proposed = tuple((r,orientation*(v//divisor)) for r,v in integers if v)
            if proposed not in seen:
                seen.add(proposed)
                yield {"scale":scale,"orientation":orientation,"multipliers":[list(v) for v in proposed]}


def controls(output):
    started = time.monotonic()
    # Hand-written CSR includes an empty row and a nonzero fixed-floor column.
    arrays = {"coefficients":[1,-2,3,2,1],"column_indices":[0,1,3,1,2],
        "row_pointers":[0,3,3,5],"row_lower":[-1,0,1],"row_upper":[1,0,2]}
    checked,empty = 0,0
    for state in product("01?",repeat=3):
        lower,upper = state_bounds("".join(state))
        vertices = list(product(*(range(a,b+1) for a,b in zip(lower,upper))))
        feasible = [x for x in vertices if -1 <= x[0]-2*x[1]+3*x[3] <= 1 and 1 <= 2*x[1]+x[2] <= 2]
        for a,b in product(range(-2,3),repeat=2):
            multipliers = [[r,v] for r,v in ((0,a),(2,b)) if v]
            vector,bound,minimum,terms = combination(arrays,multipliers,lower,upper)
            assert vector == [a,-2*a+2*b,b,3*a]
            assert bound == a*(1 if a >= 0 else -1)+b*(2 if b >= 0 else 1)
            assert minimum == min(sum(c*v for c,v in zip(vector,x)) for x in vertices)
            assert all(sum(c*v for c,v in zip(vector,x)) <= bound for x in feasible)
            if minimum > bound:
                assert not feasible
                empty += 1
            checked += 1
    rejected = 0
    for bad in ([[0,1],[0,2]],[[0,0]],[[3,1]],[[0,0.5]],[[2,1],[0,1]]):
        try: combination(arrays,bad,[0]*4,[1,1,1,0])
        except (AssertionError,IndexError): rejected += 1
        else: raise AssertionError("invalid multiplier accepted")
    # Zero omission must not change dense normalization/rounding or row IDs.
    values = [0.0,-2.0,0.0,1.0,0.0]
    proposals = list(rounded_proposals(values))
    assert proposals[0]["multipliers"] == [[1,-1]]
    assert any(x["multipliers"] == [[1,-2],[3,1]] for x in proposals)
    report = {"status":"PASS_CSR_SIGNED_BOX_CERTIFICATE_CONTROLS_NO_NATIVE",
        "source":reference(Path(__file__)),"signed_ranged_box_controls":checked,
        "contradictions_cross_checked_by_all_Boolean_vertices":empty,"malformed_multiplier_rejections":rejected,
        "fixed_floor_and_empty_row_checked":True,"sparse_rounding_keeps_original_row_ids":True,
        "native_imports":0,"full_matrix_loaded":False,"optimizer_calls":0,"seconds":time.monotonic()-started}
    write(output,report)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--controls",type=Path,required=True)
    args = parser.parse_args()
    print(json.dumps(controls(args.controls.resolve())),flush=True)
