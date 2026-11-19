"""Exact dyadic evaluation of the frozen time-limited joint-PSD/clique proposal.

Every mathematical row and unit-box bound is evaluated literally.  Stored
positive row scales are used only for additional residual-size descriptions.
No numerical status is interpreted as feasibility, and no optimizer runs.
"""
import argparse
from collections import Counter
from fractions import Fraction
import gzip
import hashlib
import json
import math
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[2]
LOGS = ROOT / "experiments/logs/root-prism-free"
INPUTS = {
    "model": ("f0-joint-psd-clique-model01.json.gz", "43fff7283308cc2ed1be0936fae4b4f7b264c5961f6e6a4c9a81d123836e4f69"),
    "numerical": ("f0-joint-psd-clique-query-run01/numerical.json", "c55a4e3e65df053a05dca2530d152a1d35fa18c653cdd2523443834885b1d594"),
    "result": ("f0-joint-psd-clique-query-run01/result.json", "d0439012c0e44e05db6b84f0a4442b82c26a9b3bd8dfc0849f10bcdb545e575a"),
    "cold": ("f0-joint-psd-clique-query-run01-cold-replay.json", "3bdd7baa5aab64a52a8b30c32ad6048d3682b0531389d7962c098ffb8fcbeb00"),
}
MODEL_SHA = "e5aee717846cf7bb1b2e6072438d49b38627119fed65408d2159212f876ec21d"
MATRIX_SHA = "607b3a6b1939b70538cbaf5e5d6e395b746745bf50ced097f12d81035723a234"
SCALES_SHA = "ab1b87424535ab03a530119b0ac5f306c5f9b2b8e038d999ffcca2dc183ebf1a"
THRESHOLDS = (Fraction(1,10**6), Fraction(1,10**8), Fraction(1,10**9),
              Fraction(1,10**12), Fraction(1,10**15))
TOP = 20


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def fraction_record(value):
    return {"numerator": str(value.numerator), "denominator": str(value.denominator),
            "float_description": float(value)}


def common_dyadic(hex_values):
    values = [float.fromhex(v) for v in hex_values]
    assert all(math.isfinite(v) for v in values)
    ratios = [v.as_integer_ratio() for v in values]
    assert all(d > 0 and d & (d-1) == 0 for n, d in ratios)
    denominator = max(d for n, d in ratios)
    numerators = [n*(denominator//d) for n, d in ratios]
    assert all(Fraction(n, denominator) == Fraction(v) for n, v in zip(numerators, values))
    return denominator, numerators


def residual(row, numerators, denominator):
    return sum(c*numerators[j] for j, c in row["terms"]) - row["rhs"]*denominator


def controls():
    row = {"terms": [[0, 3], [1, -2]], "rhs": 1}
    D, nums = common_dyadic([float(0.5).hex(), float(0.25).hex()])
    assert residual(row, nums, D) == 0
    D, nums = common_dyadic([(0.5+2**-40).hex(), (0.25).hex()])
    r = residual(row, nums, D)
    assert Fraction(r, D) == Fraction(3, 2**40)
    assert Fraction(r, D*2**10) == Fraction(3, 2**50)
    large = {"terms": [[0, 1298137088], [1, -9]], "rhs": 7}
    assert Fraction(residual(large, nums, D), D) == 1298137088*Fraction(nums[0],D)-9*Fraction(nums[1],D)-7
    for value in (-2**-80, 0.0, 2**-60+2**-112, 1.0, 1.0+2**-50):
        d, a = common_dyadic([float(value).hex()])
        assert (0 <= a[0] <= d) == (0 <= value <= 1)
    assert not Fraction(1,10**8) > THRESHOLDS[1]
    assert Fraction(1,10**8)+Fraction(1,2**100) > THRESHOLDS[1]
    return {"exact_hex_roundtrip": True, "signed_and_large_coefficient_controls": True,
            "positive_dyadic_scale_control": True, "strict_threshold_boundary_control": True,
            "optimizer_calls": 0}


def build():
    inputs = {}
    for key, (name, expected) in INPUTS.items():
        raw = (LOGS/name).read_bytes()
        assert sha(raw) == expected
        inputs[key] = json.loads(gzip.decompress(raw) if name.endswith(".gz") else raw)
    model, numerical, terminal, cold = (inputs[k] for k in ("model", "numerical", "result", "cold"))
    assert sha(canonical(model)) == MODEL_SHA
    matrix, scales = model["matrix"], model["numerical_row_scales"]
    assert sha(canonical(matrix)) == MATRIX_SHA and sha(canonical(scales)) == SCALES_SHA
    assert numerical["model_sha256"] == terminal["model_sha256"] == cold["model_sha256"] == MODEL_SHA
    assert cold["preserved_parent_status"] == terminal["status"]
    assert terminal["status"] == "UNKNOWN: numerical proposal only; no existing dual ray"
    assert cold["status"].startswith("PASS") and not cold["primal_feasibility_claimed"]
    assert numerical["numerical_status"] == "HighsModelStatus.kTimeLimit"
    assert numerical["optimizer_calls"] == 1 and terminal["exact_phase_calls"] == 0
    assert matrix["variables"] == 15200 and matrix["lower"] == 0 and matrix["upper"] == 1
    assert len(numerical["col_value_hex"]) == 15200
    denominator, numerators = common_dyadic(numerical["col_value_hex"])
    bounds = [[i, "lower", str(-n)] if n < 0 else [i, "upper", str(n-denominator)]
              for i, n in enumerate(numerators) if n < 0 or n > denominator]
    equalities, inequalities = matrix["equalities"], matrix["inequalities"]
    assert (len(equalities), len(inequalities), len(scales)) == (6135,21908,28043)
    assert len(numerical["row_value_hex"]) == len(scales)
    rows, details, families = equalities+inequalities, [], {}
    native_differences = []
    singleton_zeros = []
    for i, (row, scale) in enumerate(zip(rows, scales)):
        assert type(scale) is int and scale > 0 and scale & (scale-1) == 0
        equality = i < len(equalities)
        r = residual(row, numerators, denominator)
        gap = abs(r) if equality else max(r,0)
        raw_gap, scaled_gap = Fraction(gap,denominator), Fraction(gap,denominator*scale)
        family = row.get("family", "unlabelled")
        if family not in families:
            families[family] = {"rows":0,"equality_rows":0,"inequality_rows":0,
                "exact_violations":0,"max_raw":Fraction(0),"max_scaled":Fraction(0)}
        f = families[family]
        f["rows"] += 1
        f["equality_rows" if equality else "inequality_rows"] += 1
        f["exact_violations"] += bool(gap)
        f["max_raw"] = max(f["max_raw"],raw_gap)
        f["max_scaled"] = max(f["max_scaled"],scaled_gap)
        if equality and row["rhs"] == 0 and len(row["terms"]) == 1:
            singleton_zeros.append({"combined_row":i,"column":row["terms"][0][0],"signed_residual_numerator":str(r)})
        details.append({"combined_row":i,"kind":"equality" if equality else "inequality",
            "within_kind_row":i if equality else i-len(equalities),"family":family,
            "terms":len(row["terms"]),"scale":scale,"signed_residual_numerator":str(r),
            "raw_violation":raw_gap,"scaled_violation":scaled_gap})
        reported = Fraction(float.fromhex(numerical["row_value_hex"][i]))
        exact_lhs_scaled = Fraction(r+row["rhs"]*denominator,denominator*scale)
        native_differences.append((abs(reported-exact_lhs_scaled),i))

    def shown(item):
        return {k:(fraction_record(v) if isinstance(v,Fraction) else v) for k,v in item.items()}

    summaries = {}
    for kind in ("equality","inequality"):
        group = [v for v in details if v["kind"] == kind]
        summaries[kind] = {
            "rows":len(group),"exact_violations":sum(v["raw_violation"] > 0 for v in group),
            "largest_raw": [shown(v) for v in sorted(group,key=lambda v:(-v["raw_violation"],v["combined_row"]))[:TOP]],
            "largest_scaled": [shown(v) for v in sorted(group,key=lambda v:(-v["scaled_violation"],v["combined_row"]))[:TOP]],
            "threshold_counts": [{"threshold":str(t),
                "raw_strictly_above":sum(v["raw_violation"] > t for v in group),
                "scaled_strictly_above":sum(v["scaled_violation"] > t for v in group)} for t in THRESHOLDS],
        }
    for f in families.values():
        f["max_raw"],f["max_scaled"] = fraction_record(f["max_raw"]),fraction_record(f["max_scaled"])
    above = [shown(v) for v in details if v["scaled_violation"] > Fraction(1,10**8)]
    maximum_native_error, native_row = max(native_differences)
    return {"schema":"f0-complete-exact-dyadic-point-audit-v1",
        "status":"PASS: all mathematical residuals evaluated exactly; terminal UNKNOWN unchanged",
        "source_sha256":sha(Path(__file__).read_bytes()),"inputs":INPUTS,
        "model_sha256":MODEL_SHA,"matrix_sha256":MATRIX_SHA,"scales_sha256":SCALES_SHA,
        "controls":controls(),"denominator":str(denominator),
        "numerators":[str(n) for n in numerators],"denominator_is_power_of_two":True,
        "variables":15200,"rows":28043,"nonzeros":sum(len(r["terms"]) for r in rows),
        "bound_violations":bounds,"bounds_all_hold":not bounds,
        "minimum_coordinate":fraction_record(Fraction(min(numerators),denominator)),
        "maximum_coordinate":fraction_record(Fraction(max(numerators),denominator)),
        "by_kind":summaries,"by_family":families,
        "all_row_residual_numerators":[v["signed_residual_numerator"] for v in details],
        "all_singleton_zero_equality_checks":singleton_zeros,
        "descriptive_scaled_threshold":"1/100000000",
        "rows_above_descriptive_scaled_threshold":above,
        "threshold_is_not_exact_acceptance_or_cause_classification":True,
        "native_reported_scaled_row_lhs_consistency":{
            "rows_differing_exactly":sum(v>0 for v,i in native_differences),
            "maximum_absolute_difference":fraction_record(maximum_native_error),
            "combined_row_at_maximum":native_row},
        "numeric_value_valid":numerical["value_valid"],"numeric_dual_valid":numerical["dual_valid"],
        "exact_matrix_and_box_feasible_at_this_vector":not bounds and not any(v["raw_violation"] for v in details),
        "terminal_status_preserved":terminal["status"],"full_graph_or_PSD_feasibility_claimed":False,
        "optimizer_calls":0,"eigendecompositions":0}


if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode",choices=("audit","replay"))
    parser.add_argument("--record",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    assert not args.output.exists()
    started=time.monotonic()
    result=build()
    raw=canonical(result)
    if args.mode == "audit":
        assert not args.record.exists()
        args.record.write_bytes(gzip.compress(raw,mtime=0))
    else:
        assert canonical(json.loads(gzip.decompress(args.record.read_bytes()))) == raw
    summary={"status":result["status"],"mode":args.mode,"source_sha256":result["source_sha256"],
        "record_sha256":sha(args.record.read_bytes()),"record_canonical_sha256":sha(raw),
        "rows":result["rows"],"variables":result["variables"],"bounds_all_hold":result["bounds_all_hold"],
        "exact_matrix_and_box_feasible_at_this_vector":result["exact_matrix_and_box_feasible_at_this_vector"],
        "by_kind":{k:{key:value for key,value in v.items() if key not in ("largest_raw","largest_scaled")}
                   for k,v in result["by_kind"].items()},
        "largest_raw":{k:v["largest_raw"][0] for k,v in result["by_kind"].items()},
        "largest_scaled":{k:v["largest_scaled"][0] for k,v in result["by_kind"].items()},
        "substantive_by_descriptive_threshold":len(result["rows_above_descriptive_scaled_threshold"]),
        "terminal_status_preserved":result["terminal_status_preserved"],
        "optimizer_calls":0,"eigendecompositions":0,"seconds":time.monotonic()-started}
    args.output.write_text(json.dumps(summary,indent=2,allow_nan=False)+"\n")
    print(json.dumps(summary,indent=2))
