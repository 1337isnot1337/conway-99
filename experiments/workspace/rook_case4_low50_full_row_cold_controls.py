"""Tiny direct controls of the independent cold certificate function only."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import time

import rook_case4_low50_full_row_replay as cold

ROOT = Path(__file__).resolve().parents[2]
COLD_SHA = "5220f81f611050cf4ffdb4f1ed364367fa04d2f4c8c26486180fefc49fc5108d"


def run(output):
    started = time.monotonic()
    cold_ref = cold.reference(Path(cold.__file__))
    assert cold_ref["sha256"] == COLD_SHA
    # Local column zero is original column112; local1102 is the fixed floor.
    ids,zeros = list(range(112,1214)),list(range(112))
    arrays = {"coefficients":[1,2,3,-1,1,-2],"column_indices":[0,1,1102,0,1,1102],
        "row_pointers":[0,3,6],"row_lower":[-1,0],"row_upper":[0,2]}
    state = "1"+"?"*1101
    branch = {"index":7,"prior_branch_id":19,"raw_id":23,"state":state,"selected":[112],
        "state_sha256":cold.sha(bytes([1]+[255]*1101)),"proof_binding":{"synthetic_control":True}}
    domain = {"ids":ids,"zeros":zeros,"arrays":arrays}
    model_ref = {"synthetic_control":True}
    lower,upper = [0]*1214,[0]*1214
    for a,s in zip(ids,state):
        lower[a],upper[a] = int(s == "1"),int(s != "0")

    def proof(multipliers,c112,c113,floor,minimum,terms):
        vector = [0]*1214
        vector[112],vector[113] = c112,c113
        return {"kind":"EXACT_FULL_ROW_CONDITIONAL_BOX_EXCLUSION","low50_index":0,
            "whole_cover_box_index":7,"prior_branch_id":19,"raw_pattern_id":23,
            "state_sha256":branch["state_sha256"],"cold_branch_proof":branch["proof_binding"],
            "preflight_model":model_ref,"proved_zero_columns":zeros,"floor_bounds":[0,0],
            "coordinate_lift":"projected row combination representative modulo the 112 proved zero equalities",
            "row_multipliers":multipliers,"full1214_coefficients":list(map(str,vector)),
            "floor_coefficient":str(floor),"terms_contracted":terms,"combined_row_upper":"0",
            "minimum_over_entire_box":str(minimum),"positive_gap":str(minimum),
            "full1214_bounds_sha256":cold.sha(cold.canonical([lower,upper])),
            "conditional_guards":[112],"implied_Boolean_nogood":{"terms":[[112,1]],"upper":0},
            "numerical_ray_feasibility_assumed":False,"case4_excluded":False}

    # Positive row0: x112+2x113+3t<=0. With x112=1, its box minimum is1.
    first = proof([[0,"1"]],1,2,3,1,3)
    one = cold.certificate(first,domain,branch,0,model_ref,time.monotonic()+10)
    assert (one["minimum"],one["upper"],one["gap"]) == ("1","0","1")
    # row0 minus row1: 2x112+x113+5t<=0; the lower endpoint of row1 is used.
    signed = proof([[0,"1"],[1,"-1"]],2,1,5,2,6)
    two = cold.certificate(signed,domain,branch,0,model_ref,time.monotonic()+10)
    assert (two["minimum"],two["upper"],two["gap"]) == ("2","0","2")
    # Enumerate the two live Boolean coordinates, with x112=1 and t=0.
    assert all(2+v >= 2 for v in (0,1))
    assert not any(-1 <= 1+2*v <= 0 and 0 <= -1+v <= 2 for v in (0,1))
    altered = []
    for key,value in (("positive_gap","1"),("combined_row_upper","1"),
            ("floor_coefficient","6"),("conditional_guards",[113])):
        bad = copy.deepcopy(signed);bad[key] = value;altered.append((key,bad))
    bad = copy.deepcopy(signed);bad["full1214_coefficients"][112] = "3";altered.append(("coefficient",bad))
    bad = copy.deepcopy(signed);bad["row_multipliers"] = [[0,"-1"],[1,"1"]];altered.append(("multiplier_orientation",bad))
    bad = copy.deepcopy(signed);bad["implied_Boolean_nogood"]["terms"] = [[113,1]];altered.append(("guard_nogood",bad))
    rejected = []
    for name,bad in altered:
        try:
            cold.certificate(bad,domain,branch,0,model_ref,time.monotonic()+10)
        except (AssertionError,IndexError):
            rejected.append(name)
        else:
            raise AssertionError("altered proof accepted: "+name)
    assert len(rejected) == 7
    report = {"status":"PASS_ACTUAL_INDEPENDENT_COLD_CERTIFICATE_CONTROLS",
        "source":cold.reference(Path(__file__)),"cold_source":cold_ref,
        "accepted_positive_and_signed_proofs":[one,two],"rejected_alterations":rejected,
        "nonidentity_original_coordinate_map":[[0,112],[1,113]],"fixed_floor_local_column":1102,
        "all1214_coefficients_and_bounds_checked":True,"synthetic_branch_only":True,
        "native_imports":0,"full_matrix_loaded":False,"old_trace_replay_repeated":False,
        "optimizer_calls":0,"seconds":time.monotonic()-started}
    assert not output.exists()
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_bytes(cold.canonical(report)+b"\n")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.output.resolve())),flush=True)
