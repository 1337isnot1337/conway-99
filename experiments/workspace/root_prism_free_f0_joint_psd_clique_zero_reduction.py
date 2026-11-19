"""Exact equivalent reduction by162 proved Y zeros and literal row witnesses.

Only these162 columns are eliminated. Retained rows keep their original
integer coefficients and positive dyadic scales. All92 PSD directions stay
physically present, even when duplicate or box-implied. No optimizer runs.
"""
import argparse
from collections import Counter
from fractions import Fraction
import gzip
import hashlib
from itertools import product
import json
from math import gcd
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[2]
LOGS = ROOT / "experiments/logs/root-prism-free"
INPUTS = {
    "parent": ("f0-joint-psd-clique-model01.json.gz", "43fff7283308cc2ed1be0936fae4b4f7b264c5961f6e6a4c9a81d123836e4f69"),
    "parent_cold": ("f0-joint-psd-clique-query-preflight01.json", "7bc800b968c4d2d5ed0224d83e6337880ea8376c8490e05c8bcb89588ca0a17b"),
}
PARENT_SHA = "e5aee717846cf7bb1b2e6072438d49b38627119fed65408d2159212f876ec21d"
PARENT_MATRIX_SHA = "607b3a6b1939b70538cbaf5e5d6e395b746745bf50ced097f12d81035723a234"
PARENT_SCALES_SHA = "ab1b87424535ab03a530119b0ac5f306c5f9b2b8e038d999ffcca2dc183ebf1a"
PSD_FAMILIES = {"augmented selector PSD":32, "old_scan: plus":16, "old_scan: minus":1,
                "full_scan: plus":16, "full_scan: minus":6, "joint PSD":21}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def primitive(row, orient):
    divisor = abs(row["rhs"])
    for j, coefficient in row["terms"]:
        divisor = gcd(divisor, abs(coefficient))
    divisor = divisor or 1
    leading = row["terms"][0][1] if row["terms"] else row["rhs"]
    sign = -1 if orient and leading < 0 else 1
    key = (tuple((j, sign*c//divisor) for j,c in row["terms"]), sign*row["rhs"]//divisor)
    return key, sign*divisor


def box_range(row):
    return sum(min(c,0) for j,c in row["terms"]), sum(max(c,0) for j,c in row["terms"])


def reduce_matrix(original, old_scales, zero_columns, protected):
    n = original["variables"]
    assert original["lower"] == 0 and original["upper"] == 1
    zeros = set(zero_columns)
    assert len(zeros) == len(zero_columns) and all(type(j) is int and 0 <= j < n for j in zeros)
    kept = [j for j in range(n) if j not in zeros]
    old_to_new = [-1]*n
    for j, old in enumerate(kept):
        old_to_new[old] = j
    old_rows = original["equalities"] + original["inequalities"]
    assert len(old_rows) == len(old_scales)
    protected = set(protected)
    assert all(len(original["equalities"]) <= i < len(old_rows) for i in protected)
    new_eq, new_ineq, eq_scales, ineq_scales = [], [], [], []
    row_map, reverse_eq, reverse_ineq = [], [], []
    equality_index, inequality_index = {}, {}
    for old_i, (old, scale) in enumerate(zip(old_rows,old_scales)):
        equality = old_i < len(original["equalities"])
        row = {**old, "terms":[[old_to_new[j],c] for j,c in old["terms"] if j not in zeros]}
        assert row["terms"] == sorted(row["terms"])
        assert len({j for j,c in row["terms"]}) == len(row["terms"])
        assert all(type(c) is int and c for j,c in row["terms"])
        low, high = box_range(row)
        item = {"old_combined_row":old_i, "old_kind":"equality" if equality else "inequality",
                "old_scale":scale, "protected_PSD_direction":old_i in protected,
                "removed_zero_terms":[[j,c] for j,c in old["terms"] if j in zeros]}
        tautology = low == high == row["rhs"] if equality else high <= row["rhs"]
        if tautology and old_i not in protected:
            item.update(disposition="unit_box_tautology", box_minimum=low, box_maximum=high,
                        right_hand_side=row["rhs"])
            row_map.append(item)
            continue
        key, multiplier = primitive(row, orient=equality)
        if equality:
            index = equality_index
            new_rows, new_scales, reverse = new_eq, eq_scales, reverse_eq
            if key in index:
                at, other_multiplier = index[key]
                ratio = Fraction(multiplier,other_multiplier)
                item.update(disposition="duplicate_equality", new_kind="equality", new_within_kind_row=at,
                            affine_ratio=[ratio.numerator,ratio.denominator])
                row_map.append(item)
                continue
        else:
            index = inequality_index
            new_rows, new_scales, reverse = new_ineq, ineq_scales, reverse_ineq
            eq_key, eq_multiplier = primitive(row,orient=True)
            if old_i not in protected and eq_key in equality_index:
                at, other_multiplier = equality_index[eq_key]
                ratio = Fraction(eq_multiplier,other_multiplier)
                item.update(disposition="equality_half", new_kind="equality", new_within_kind_row=at,
                            affine_ratio=[ratio.numerator,ratio.denominator])
                row_map.append(item)
                continue
            if old_i not in protected and key in index:
                at, other_multiplier = index[key]
                ratio = Fraction(multiplier,other_multiplier)
                assert ratio > 0
                item.update(disposition="duplicate_inequality", new_kind="inequality", new_within_kind_row=at,
                            affine_ratio=[ratio.numerator,ratio.denominator])
                row_map.append(item)
                continue
        at = len(new_rows)
        new_rows.append(row)
        new_scales.append(scale)
        reverse.append(old_i)
        if key not in index:
            index[key] = (at,multiplier)
        item.update(disposition="retained_protected_PSD" if old_i in protected else "retained",
                    new_kind="equality" if equality else "inequality", new_within_kind_row=at,
                    affine_ratio=[1,1])
        if old_i in protected:
            item["box_tautological_but_retained"] = tautology
        row_map.append(item)
    for item in row_map:
        if "new_within_kind_row" in item:
            item["new_combined_row"] = item["new_within_kind_row"] + (0 if item["new_kind"] == "equality" else len(new_eq))
    matrix = {"variables":len(kept), "lower":0, "upper":1, "equalities":new_eq, "inequalities":new_ineq}
    return {"matrix":matrix, "numerical_row_scales":eq_scales+ineq_scales,
            "old_to_new_columns":old_to_new, "new_to_old_columns":kept,
            "eliminated_columns":zero_columns, "old_row_map":row_map,
            "new_to_old_rows":reverse_eq+reverse_ineq,
            "protected_old_PSD_rows":sorted(protected)}


def verify_reduction(original, old_scales, result):
    """Check literal cross-multiplied row identities without canonical-key lookup."""
    matrix = result["matrix"]
    old_rows = original["equalities"] + original["inequalities"]
    rows = matrix["equalities"] + matrix["inequalities"]
    zero = set(result["eliminated_columns"])
    kept = result["new_to_old_columns"]
    assert kept == [i for i in range(original["variables"]) if i not in zero]
    assert matrix["variables"] == len(kept) and matrix["lower"] == original["lower"] == 0
    assert matrix["upper"] == original["upper"] == 1
    old_to_new = result["old_to_new_columns"]
    assert len(old_to_new) == original["variables"]
    assert [old_to_new[j] for j in kept] == list(range(len(kept)))
    assert all(old_to_new[j] == -1 for j in zero)
    assert len(result["old_row_map"]) == len(old_rows)
    assert len(result["new_to_old_rows"]) == len(rows) == len(result["numerical_row_scales"])
    for new_i, old_i in enumerate(result["new_to_old_rows"]):
        old, row = old_rows[old_i], rows[new_i]
        assert row == {**old,"terms":[[old_to_new[j],c] for j,c in old["terms"] if j not in zero]}
        assert (new_i < len(matrix["equalities"])) == (old_i < len(original["equalities"]))
        assert result["numerical_row_scales"][new_i] == old_scales[old_i]
    dispositions = Counter()
    for old_i, (old,item) in enumerate(zip(old_rows,result["old_row_map"])):
        assert item["old_combined_row"] == old_i and item["old_scale"] == old_scales[old_i]
        equality = old_i < len(original["equalities"])
        assert item["old_kind"] == ("equality" if equality else "inequality")
        terms = {old_to_new[j]:c for j,c in old["terms"] if j not in zero}
        assert item["removed_zero_terms"] == [[j,c] for j,c in old["terms"] if j in zero]
        tag = item["disposition"]
        dispositions[tag] += 1
        if tag == "unit_box_tautology":
            lo,hi = sum(min(c,0) for c in terms.values()),sum(max(c,0) for c in terms.values())
            assert (lo,hi,old["rhs"]) == (item["box_minimum"],item["box_maximum"],item["right_hand_side"])
            assert lo == hi == old["rhs"] if equality else hi <= old["rhs"]
            assert not item["protected_PSD_direction"]
            continue
        new_i = item["new_combined_row"]
        assert 0 <= new_i < len(rows)
        new_is_eq = new_i < len(matrix["equalities"])
        assert item["new_kind"] == ("equality" if new_is_eq else "inequality")
        assert item["new_within_kind_row"] == new_i-(0 if new_is_eq else len(matrix["equalities"]))
        num,den = item["affine_ratio"]
        assert type(num) is type(den) is int and num != 0 and den > 0 and gcd(abs(num),den) == 1
        other = dict(rows[new_i]["terms"])
        for j in terms.keys() | other.keys():
            assert den*terms.get(j,0) == num*other.get(j,0)
        assert den*old["rhs"] == num*rows[new_i]["rhs"]
        if tag in ("retained","retained_protected_PSD"):
            assert (num,den) == (1,1) and equality == new_is_eq
            assert result["new_to_old_rows"][new_i] == old_i
        elif tag == "duplicate_equality":
            assert equality and new_is_eq
        elif tag == "duplicate_inequality":
            assert not equality and not new_is_eq and num > 0
        else:
            assert tag == "equality_half" and not equality and new_is_eq
    protected = result["protected_old_PSD_rows"]
    assert [i for i,item in enumerate(result["old_row_map"]) if item["protected_PSD_direction"]] == protected
    protected_new = []
    for old_i in protected:
        item = result["old_row_map"][old_i]
        assert item["disposition"] == "retained_protected_PSD"
        protected_new.append(item["new_combined_row"])
    assert len(set(protected_new)) == len(protected)
    return {"all_original_row_obligations_checked":len(old_rows), "all_retained_rows_have_original_premises":len(rows),
            "all_retained_coefficients_and_scales_unchanged":True, "dispositions":dict(dispositions),
            "protected_PSD_rows_physically_retained":len(protected), "protected_new_PSD_rows":protected_new}


def feasible(matrix, point):
    return (all(0 <= value <= 1 for value in point)
            and all(sum(c*point[j] for j,c in r["terms"]) == r["rhs"] for r in matrix["equalities"])
            and all(sum(c*point[j] for j,c in r["terms"]) <= r["rhs"] for r in matrix["inequalities"]))


def controls():
    def row(terms,rhs,family="control"):
        return {"terms":terms,"rhs":rhs,"family":family}
    eq=[row([[1,1]],0),row([[4,-3]],0),row([[0,1],[2,1]],1),
        row([[0,-2],[2,-2]],-2),row([[1,1],[4,1]],0),row([[3,1],[5,-1]],0)]
    iq=[row([[0,2],[2,2]],2),row([[0,-1],[2,-1]],-1),row([[0,1],[3,1]],1),
        row([[0,3],[3,3],[4,7]],3),row([[0,-1]],0),row([[0,1]],1),
        row([[0,1],[2,1]],2),row([[0,-1],[3,-1]],-1),
        row([[1,1],[5,1]],1,"protected"),row([[0,4],[3,4]],4,"protected")]
    old={"variables":6,"lower":0,"upper":1,"equalities":eq,"inequalities":iq}
    scales=[2**(i%4) for i in range(len(eq)+len(iq))]
    reduced=reduce_matrix(old,scales,[1,4],[14,15])
    check=verify_reduction(old,scales,reduced)
    assert check["protected_PSD_rows_physically_retained"] == 2
    values=(Fraction(0),Fraction(1,3),Fraction(2,3),Fraction(1))
    cases=0
    for point in product(values,repeat=4):
        lifted=[Fraction(0)]*6
        for j,old_j in enumerate(reduced["new_to_old_columns"]):
            lifted[old_j]=point[j]
        assert feasible(old,lifted) == feasible(reduced["matrix"],point)
        cases+=1
    contradiction={"variables":2,"lower":0,"upper":1,"equalities":[row([[0,1]],0)],
                   "inequalities":[row([[0,1]],-1)]}
    wrong=reduce_matrix(contradiction,[1,1],[0],[])
    verify_reduction(contradiction,[1,1],wrong)
    assert wrong["matrix"]["inequalities"][0]["terms"] == []
    assert all(not feasible(wrong["matrix"],[value]) for value in values)
    return {"complete_rational_grid_equivalence_cases":cases,"false_empty_row_retained":True,
            "signed_equality_duplicates_and_both_inequality_orientations_checked":True,
            "protected_duplicate_and_box_rows_retained":True,"optimizer_calls":0}


def build():
    data={}
    for name,(file,expected) in INPUTS.items():
        raw=(LOGS/file).read_bytes()
        assert sha(raw)==expected
        data[name]=json.loads(gzip.decompress(raw) if file.endswith(".gz") else raw)
    parent,cold=data["parent"],data["parent_cold"]
    assert sha(canonical(parent)) == PARENT_SHA and cold["model_sha256"] == PARENT_SHA
    assert sha(canonical(parent["matrix"])) == PARENT_MATRIX_SHA and cold["matrix_sha256"] == PARENT_MATRIX_SHA
    assert sha(canonical(parent["numerical_row_scales"])) == PARENT_SCALES_SHA
    assert cold["status"].startswith("PASS")
    original,old_scales=parent["matrix"],parent["numerical_row_scales"]
    assert original["variables"]==15200 and len(original["equalities"])==6135
    old_rows=original["equalities"]+original["inequalities"]
    assert len(old_rows)==28043 and sum(len(r["terms"]) for r in old_rows)==1086559
    zeros=[]
    zero_proofs=[]
    for i,row in enumerate(original["equalities"]):
        if row["rhs"]==0 and len(row["terms"])==1:
            column,coefficient=row["terms"][0]
            assert 42<=column<5847 and coefficient!=0
            zeros.append(column)
            zero_proofs.append({"old_equality_row":i,"old_variable":column,"coefficient":coefficient,"rhs":0})
    assert len(zeros)==len(set(zeros))==162
    protected=[i for i,row in enumerate(old_rows) if row.get("family") in PSD_FAMILIES]
    assert Counter(old_rows[i]["family"] for i in protected)==PSD_FAMILIES and len(protected)==92
    reduced=reduce_matrix(original,old_scales,sorted(zeros),protected)
    check=verify_reduction(original,old_scales,reduced)
    assert reduced["matrix"]["variables"]==15038
    matrix,scales=reduced["matrix"],reduced["numerical_row_scales"]
    all_rows=matrix["equalities"]+matrix["inequalities"]
    empty_contradictions=[i for i,row in enumerate(all_rows) if not row["terms"] and
        (row["rhs"]!=0 if i<len(matrix["equalities"]) else row["rhs"]<0)]
    counts={"old_variables":15200,"variables":15038,"eliminated_proved_Y_columns":162,
        "old_rows":28043,"equalities":len(matrix["equalities"]),"inequalities":len(matrix["inequalities"]),
        "rows":len(all_rows),"old_nonzeros":1086559,"nonzeros":sum(len(row["terms"]) for row in all_rows),
        "PSD_directions_physically_retained":92,"empty_contradictions_retained":len(empty_contradictions)}
    return {"schema":"f0-equivalent162Y-zero-reduction-v1","source_sha256":sha(Path(__file__).read_bytes()),
        "inputs":INPUTS,"parent_model_sha256":PARENT_SHA,"parent_matrix_sha256":PARENT_MATRIX_SHA,
        "parent_scales_sha256":PARENT_SCALES_SHA,"zero_proofs":zero_proofs,**reduced,
        "matrix_sha256":sha(canonical(matrix)),"numerical_row_scales_sha256":sha(canonical(scales)),
        "counts":counts,"equivalence_check":check,"controls":controls(),
        "empty_contradiction_rows":empty_contradictions,
        "scope":{"all480_original_selectors_retained":True,"all_Z_coordinates_retained":True,
            "only162_explicit_Y_zeros_eliminated":True,"all_original_obligations_represented":True,
            "all92_PSD_directions_physically_retained":True,"retained_coefficients_and_scales_unchanged":True,
            "primitive_normalization_used_only_for_duplicate_detection":True,
            "affine_equivalence_on_proved_zero_face":True,"numerical_proposal_used":False,
            "new_graph_assumption":False,"optimizer_calls":0,"eigendecompositions":0,
            "model_feasibility_or_exclusion_claimed":False}}


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode",choices=("prepare","replay"))
    parser.add_argument("--model",type=Path,required=True)
    parser.add_argument("--report",type=Path,required=True)
    args=parser.parse_args()
    assert not args.report.exists()
    started=time.monotonic()
    result=build()
    raw=canonical(result)
    if args.mode=="prepare":
        assert not args.model.exists()
        args.model.write_bytes(gzip.compress(raw,mtime=0))
    else:
        assert canonical(json.loads(gzip.decompress(args.model.read_bytes())))==raw
    report={"status":"PASS: exact equivalent162Y-zero reduction "+args.mode,
        "source_sha256":result["source_sha256"],"model_file_sha256":sha(args.model.read_bytes()),
        "model_sha256":sha(raw),"matrix_sha256":result["matrix_sha256"],
        "numerical_row_scales_sha256":result["numerical_row_scales_sha256"],
        "counts":result["counts"],"equivalence_check":result["equivalence_check"],"controls":result["controls"],
        "optimizer_calls":0,"eigendecompositions":0,"seconds":time.monotonic()-started}
    args.report.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))
