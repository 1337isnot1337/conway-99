"""Standalone literal row-map check of the162-Y-zero equivalent reduction.

This checker imports no builder, numerical helper or optimizer. It verifies
every retained row, every omitted-row witness and the exact zero embedding.
"""
import argparse
from collections import Counter
import gzip
import hashlib
import json
from math import gcd
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[2]
LOGS = ROOT / "experiments/logs/root-prism-free"
BUILDER_SHA = "3dfa11d839993206d59cc76d48f77881320ee8fd13e956fd247e17f2fc0ef120"
PARENT_FILE_SHA = "43fff7283308cc2ed1be0936fae4b4f7b264c5961f6e6a4c9a81d123836e4f69"
PARENT_SHA = "e5aee717846cf7bb1b2e6072438d49b38627119fed65408d2159212f876ec21d"
FILE_SHA = "da9b2062f9102a0487bc5fb88b2e009c1a228cbc2d2c39264135808bb3467ffb"
MODEL_SHA = "7793e51627f1559aa041ababce08f68f2899f3984afa1e92dd039d9e4871a6cf"
MATRIX_SHA = "af8df1fdd52c5dc0ec760914bb27c2d10d1f2761c6cc957edfc6ede87f319816"
SCALES_SHA = "84c35e927e99e96bffdbd5d03bdfe574ddaaeb447e0868a295215518365e71bb"


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def packed(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def read(name, expected):
    encoded = (LOGS / name).read_bytes()
    assert digest(encoded) == expected
    return json.loads(gzip.decompress(encoded))


def replay():
    old = read("f0-joint-psd-clique-model01.json.gz",PARENT_FILE_SHA)
    new = read("f0-joint-psd-clique-zero-model01.json.gz",FILE_SHA)
    assert digest(packed(old)) == PARENT_SHA
    assert digest(packed(new)) == MODEL_SHA
    assert digest(Path(__file__).with_name("root_prism_free_f0_joint_psd_clique_zero_reduction.py").read_bytes()) == BUILDER_SHA
    assert new["source_sha256"] == BUILDER_SHA and new["parent_model_sha256"] == PARENT_SHA
    A,B = old["matrix"],new["matrix"]
    assert A["variables"] == 15200 and B["variables"] == 15038
    assert A["lower"] == B["lower"] == 0 and A["upper"] == B["upper"] == 1
    assert digest(packed(B)) == new["matrix_sha256"] == MATRIX_SHA
    assert digest(packed(new["numerical_row_scales"])) == new["numerical_row_scales_sha256"] == SCALES_SHA
    old_rows = A["equalities"]+A["inequalities"]
    rows = B["equalities"]+B["inequalities"]
    assert (len(old_rows),len(A["equalities"]),len(rows),len(B["equalities"])) == (28043,6135,27719,5973)
    old_scales,scales = old["numerical_row_scales"],new["numerical_row_scales"]
    assert len(old_scales) == len(old_rows) and len(scales) == len(rows)
    proofs=[]
    for i,row in enumerate(A["equalities"]):
        if row["rhs"] == 0 and len(row["terms"]) == 1:
            j,c = row["terms"][0]
            assert type(j) is type(c) is int and 42 <= j < 5847 and c != 0
            proofs.append({"old_equality_row":i,"old_variable":j,"coefficient":c,"rhs":0})
    assert proofs == new["zero_proofs"] and len(proofs) == 162
    zeros = {v["old_variable"] for v in proofs}
    assert len(zeros) == 162 and sorted(zeros) == new["eliminated_columns"]
    kept = [j for j in range(15200) if j not in zeros]
    forward = [-1]*15200
    for j,old_j in enumerate(kept):
        forward[old_j]=j
    assert kept == new["new_to_old_columns"] and forward == new["old_to_new_columns"]
    assert all(j in kept for j in range(42))
    assert all(j in kept for j in range(5847,15200))

    def project(row):
        return {**row,"terms":[[forward[j],c] for j,c in row["terms"] if j not in zeros]}

    reverse=new["new_to_old_rows"]
    assert len(reverse) == len(rows) and len(set(reverse)) == len(rows)
    for i,old_i in enumerate(reverse):
        assert 0 <= old_i < len(old_rows)
        assert rows[i] == project(old_rows[old_i])
        assert scales[i] == old_scales[old_i]
        assert (i<5973) == (old_i<6135)
        assert type(scales[i]) is int and scales[i]>0 and scales[i]&(scales[i]-1)==0
    maps=new["old_row_map"]
    assert len(maps)==len(old_rows)
    counts=Counter()
    for old_i,item in enumerate(maps):
        row=old_rows[old_i]
        is_eq=old_i<6135
        assert item["old_combined_row"]==old_i and item["old_scale"]==old_scales[old_i]
        assert item["old_kind"]==("equality" if is_eq else "inequality")
        assert item["removed_zero_terms"]==[[j,c] for j,c in row["terms"] if j in zeros]
        projected=project(row)
        tag=item["disposition"]
        counts[tag]+=1
        if tag=="unit_box_tautology":
            lo=sum(c for j,c in projected["terms"] if c<0)
            hi=sum(c for j,c in projected["terms"] if c>0)
            assert (lo,hi,projected["rhs"])==(item["box_minimum"],item["box_maximum"],item["right_hand_side"])
            if is_eq:
                assert lo==hi==projected["rhs"]
            else:
                assert hi<=projected["rhs"]
            assert not item["protected_PSD_direction"]
            continue
        at=item["new_combined_row"]
        assert 0<=at<len(rows)
        target=rows[at]
        target_eq=at<5973
        assert item["new_kind"]==("equality" if target_eq else "inequality")
        assert item["new_within_kind_row"]==at-(0 if target_eq else 5973)
        numerator,denominator=item["affine_ratio"]
        assert type(numerator) is type(denominator) is int and denominator>0 and numerator!=0
        assert gcd(abs(numerator),denominator)==1
        left=dict(projected["terms"]);right=dict(target["terms"])
        for j in left.keys()|right.keys():
            assert denominator*left.get(j,0)==numerator*right.get(j,0)
        assert denominator*projected["rhs"]==numerator*target["rhs"]
        if tag in ("retained","retained_protected_PSD"):
            assert reverse[at]==old_i and is_eq==target_eq and [numerator,denominator]==[1,1]
        elif tag=="duplicate_equality":
            assert is_eq and target_eq
        elif tag=="duplicate_inequality":
            assert not is_eq and not target_eq and numerator>0
        else:
            assert tag=="equality_half" and not is_eq and target_eq
    assert counts=={"retained":27627,"retained_protected_PSD":92,"unit_box_tautology":324}
    families={"augmented selector PSD":32,"old_scan: plus":16,"old_scan: minus":1,
              "full_scan: plus":16,"full_scan: minus":6,"joint PSD":21}
    psd_old=[i for i,row in enumerate(old_rows) if row.get("family") in families]
    assert Counter(old_rows[i]["family"] for i in psd_old)==families
    assert psd_old==new["protected_old_PSD_rows"]
    assert [i for i,v in enumerate(maps) if v["protected_PSD_direction"]]==psd_old
    psd_new=[maps[i]["new_combined_row"] for i in psd_old]
    assert len(set(psd_new))==92
    assert all(maps[i]["disposition"]=="retained_protected_PSD" for i in psd_old)
    omitted_eq=[i for i,v in enumerate(maps) if v["disposition"]=="unit_box_tautology" and i<6135]
    omitted_iq=[i for i,v in enumerate(maps) if v["disposition"]=="unit_box_tautology" and i>=6135]
    assert omitted_eq==[v["old_equality_row"] for v in proofs]
    assert len(omitted_iq)==162
    assert all(old_rows[i]["family"]=="Y bounded by selector pair moment" for i in omitted_iq)
    return {"status":"PASS: standalone literal zero-embedding and all original-row obligation replay",
        "source_sha256":digest(Path(__file__).read_bytes()),"builder_sha256":BUILDER_SHA,
        "parent_file_sha256":PARENT_FILE_SHA,"parent_model_sha256":PARENT_SHA,
        "model_file_sha256":FILE_SHA,"model_sha256":MODEL_SHA,"matrix_sha256":MATRIX_SHA,
        "scales_sha256":SCALES_SHA,"exact_zero_columns":162,"retained_variables":15038,
        "original_rows_checked":28043,"retained_rows_checked":27719,
        "retained_nonzeros":sum(len(r["terms"]) for r in rows),"row_dispositions":dict(counts),
        "all92_PSD_directions_physically_retained":True,"all_Z_columns_retained":True,
        "retained_coefficients_and_scales_unchanged":True,
        "omitted_equalities_are_exact162_zero_axioms":True,
        "omitted_inequalities_are162_Y_le_Z_box_tautologies":True,
        "all_old_rows_have_exact_embedding_witnesses":True,
        "all_new_rows_have_original_premises":True,
        "no_extra_duplicate_reductions_found":True,
        "equivalence":"Projection deletes only variables forced zero by original equalities; the inverse inserts zeros. Every original row follows from its retained-row identity or exact unit-box bound, and every retained row is a projected original row.",
        "subject_sources_imported":False,"numerical_point_used":False,"optimizer_calls":0,"eigendecompositions":0,
        "model_feasibility_or_exclusion_claimed":False}


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    assert not args.output.exists()
    started=time.monotonic()
    report=replay()
    report["seconds"]=time.monotonic()-started
    args.output.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))
