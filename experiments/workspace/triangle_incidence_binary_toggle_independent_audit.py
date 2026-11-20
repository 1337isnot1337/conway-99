"""Independent109-row triangle-toggle bound audit; no subject import or LP."""
import argparse
from fractions import Fraction
import hashlib
import json
from math import comb
from pathlib import Path

import triangle_incidence_binary_replacement_independent_audit as prior

ROOT = Path(__file__).resolve().parents[2]
PRIOR_SHA = "edd93ff11804deaacdf73998c666d73d7a70a64bc24ca822946a46a49ecc0208"
SOURCE = "experiments/workspace/triangle_incidence_binary_toggle_code.py"
SOURCE_SHA = "90fa29ba6d87c1ba7ce4d2cda98ffad70a1be7cf17b2c48415fbfb332978e139"
PREP = "experiments/logs/grids-and-triangles/triangle-incidence-binary-toggle-code-preparation.json"
PREP_SHA = "a19d6da3b7159cf66a41e31f1abcb05e01487c6e5a744d762fc0ab2fa3d95402"
RESULT = "experiments/logs/grids-and-triangles/triangle-incidence-binary-toggle-code-query01.json"
RESULT_SHA = "9248b18c7da13191fe2250c0efc83c5c4d742848940c93cd6e830dc898e7a610"
NOTE = "research/grids-and-triangles/triangle_incidence_binary_toggle_review.md"
NOTE_SHA = "675a6162ed7ed227cc77d49dc7d65d211f8ee0f997e1e99bf5473505b76c2b78"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def polynomial(*parts):
    out = {}
    for coefficient, terms in parts:
        for degree, value in terms.items():
            out[degree] = out.get(degree, 0)+coefficient*value
    return {j: v for j, v in out.items() if v}


def checked_identities():
    s3 = {2: 14, 1: -14}
    s4 = polynomial((21, {3: 1}), (-2, s3), (-3, {0: 231}))
    assert s4 == {3: 21, 2: -28, 1: 28, 0: -693}
    s5 = polynomial((28, {4: 1}), (-2, s4), (-3, {1: 224}))
    assert s5 == {4: 28, 3: -42, 2: 56, 1: -728, 0: 1386}
    t5 = {2: 217, 1: 7}
    s6 = polynomial((35, {5: 1}), (-2, s5), (-3, t5))
    assert s6 == {5: 35, 4: -56, 3: 84, 2: -763, 1: 1435, 0: -2772}
    t6 = {3: 210, 0: 462, 2: 14, 1: -14}
    any_t6 = polynomial((1, t6), (-1, {0: 24486, 2: 42, 1: -84}))
    assert any_t6 == {3: 210, 2: -28, 1: 70, 0: -24024}
    assert 2*24948+2*4158 == 58212
    assert 5*24948-58212 == 66528
    assert 58212-36*120-1386 == 52506
    assert 66528-9*120+1386 == 66834
    assert 7*24486-24948 == 146454
    assert 24948+2772 == 27720 and 146454-2772 == 143682
    return {name: [[j, p[j]] for j in sorted(p)]
            for name, p in (("S3", s3), ("S4", s4), ("S5", s5), ("S6", s6),
                            ("T5", t5), ("T6", t6), ("six_sets_with_any_triangle", any_t6))}


def calculate(root):
    assert sha(Path(prior.__file__).read_bytes()) == PRIOR_SHA
    for path, digest in ((SOURCE, SOURCE_SHA), (PREP, PREP_SHA), (RESULT, RESULT_SHA), (NOTE, NOTE_SHA)):
        assert sha((root/path).read_bytes()) == digest
    prep = json.loads((root/PREP).read_bytes())
    result = json.loads((root/RESULT).read_bytes())
    model = prep["model"]
    assert result["preparation_sha256"] == PREP_SHA
    assert result["bindings"] == prep["bindings"]
    assert prep["bindings"]["source_sha256"] == SOURCE_SHA
    for path, digest in prep["bindings"]["additional_controls"].items():
        assert sha((root/path).read_bytes()) == digest
    encoded = (json.dumps(model, sort_keys=True, separators=(",", ":"))+"\n").encode()
    assert sha(encoded) == prep["model_sha256"] == result["model_sha256"]
    weights = [36, 40, 44, 48, 52, 56, 60]
    lower = {3: 231, 4: 2079, 5: 23868, 6: 24486, 7: 3465,
             8: 3465, 11: 2079, 12: 693, 15: 99}
    additions = [
        ("equal_column_edges", {2: 1, 1: -7}, 0),
        ("triangle_replacements", {3: 1, 2: -7, 1: 7}, 231),
        ("triangle_containing_weight_four", {4: 1, 1: -224}, 2079),
        ("weight_four_toggle", {4: 4, 3: -21, 2: 28, 1: -840}, 3465),
        ("chain_weight_five_edge_lower", {4: 28, 3: -42, 2: 56, 1: -728}, 52506),
        ("chain_weight_five_edge_upper", {5: 5, 4: -28, 3: 42, 2: -56, 1: 728}, 66834),
        ("triangle_and_chain_weight_five", {5: 1, 2: -217, 1: 14}, 23868),
        ("triangle_containing_weight_six", {6: 1, 3: -210, 2: 28, 1: -70}, -24024),
        ("disjoint_pair_weight_six_edge_lower", {5: 35, 4: -56, 3: 84, 2: -763, 1: 1435}, 27720),
        ("disjoint_pair_weight_six_edge_upper", {6: 7, 5: -35, 4: 56, 3: -84, 2: 763, 1: -1435}, 143682),
    ]
    A = [[lower.get(j, 0)-prior.krawtchouk(99, j, w) for w in weights] for j in range(1, 100)]
    b = [comb(99, j)-lower.get(j, 0) for j in range(1, 100)]
    labels = ["dual_weight_"+str(j) for j in range(1, 100)]
    pulled_rows = []
    for label, terms, demand in additions:
        row = [demand-sum(c*prior.krawtchouk(99, j, w) for j, c in terms.items()) for w in weights]
        rhs = sum(c*comb(99, j) for j, c in terms.items())-demand
        A.append(row); b.append(rhs); labels.append(label)
        pulled_rows.append({"label": label, "weighted_degrees": [[j, terms[j]] for j in sorted(terms)],
                            "lower": demand, "coefficients": row, "upper": rhs})
    assert A == model["coefficients"] and b == model["upper_bounds"] and labels == model["row_labels"]
    assert model["additional_dual_count_constraints"] == [
        {k: row[k] for k in ("label", "weighted_degrees", "lower")} for row in pulled_rows]
    primal = list(map(Fraction, result["exact_primal"]))
    dual = list(map(Fraction, result["exact_dual"]))
    assert len(primal) == 7 and len(dual) == 109 and all(x >= 0 for x in primal+dual)
    primal_slack = [rhs-sum(c*x for c, x in zip(row, primal)) for row, rhs in zip(A, b)]
    dual_slack = [sum(dual[i]*A[i][j] for i in range(109))-1 for j in range(7)]
    assert all(x >= 0 for x in primal_slack+dual_slack)
    primal_value, dual_value = 1+sum(primal), 1+sum(x*rhs for x, rhs in zip(dual, b))
    assert primal_value == dual_value == Fraction(52183040, 17817)
    assert 2**11 <= dual_value < 2**12
    assert str(dual_value) == result["certificate"]["exact_code_size_upper_bound"]
    assert list(map(str, dual_slack)) == result["certificate"]["dual_column_slacks"]
    active = [[labels[i], str(x)] for i, x in enumerate(dual) if x]
    assert active == [["equal_column_edges", "1108331/413710740"],
                      ["triangle_replacements", "49/71268"],
                      ["chain_weight_five_edge_lower", "1457/153226200"],
                      ["chain_weight_five_edge_upper", "412/57459825"],
                      ["triangle_and_chain_weight_five", "109/206855370"]]
    formal_gaps = []
    for path, digest, values in prior.POINTS:
        raw = (root/path).read_bytes(); assert sha(raw) == digest
        point = json.loads(raw)["certificate"]["dual_weight_counts"]
        gaps = []
        for i, (label, terms, demand) in enumerate(additions, start=99):
            gap = sum(c*point[j] for j, c in terms.items())-demand
            assert b[i]-sum(c*x for c, x in zip(A[i], values)) == 2048*gap
            gaps.append({"row": label, "exact_dual_gap": gap, "violated": gap < 0})
        formal_gaps.append({"point_sha256": digest, "additional_row_gaps": gaps})
    return {"status": "PASS: independent109-row exact primal/dual and all10 new pullbacks",
            "source_sha256": sha(Path(__file__).read_bytes()), "reviewed_subject_source_sha256": SOURCE_SHA,
            "prior_independent_checker_sha256": PRIOR_SHA, "preparation_sha256": PREP_SHA,
            "result_sha256": RESULT_SHA, "proof_note_sha256": NOTE_SHA,
            "model_sha256": prep["model_sha256"], "symbolic_count_identities": checked_identities(),
            "all10_pulled_back_rows": pulled_rows, "all109_primal_slacks": list(map(str, primal_slack)),
            "all_seven_dual_column_slacks": list(map(str, dual_slack)), "all109_dual_signs_checked": True,
            "nonzero_dual_rows": active, "exact_primal_and_dual_objective": str(dual_value),
            "dimension_upper_bound": 11, "incidence_rank_lower_bound": 88,
            "saved_formal_point_gaps": formal_gaps, "optimizer_calls": 0,
            "subject_source_imported": False, "literal_controls_repeated": False,
            "all_codes_or_graphs_excluded": False,
            "inherited_weight_support_and_forced_word_bounds_preserved_not_reproved_here": True}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=("write", "replay"))
    p.add_argument("--root", type=Path, default=ROOT)
    p.add_argument("--certificate", type=Path, required=True)
    p.add_argument("--output", type=Path)
    args = p.parse_args()
    report = calculate(args.root)
    if args.mode == "write":
        assert not args.certificate.exists()
        args.certificate.write_text(json.dumps(report, indent=2)+"\n")
    else:
        assert report == json.loads(args.certificate.read_bytes())
        assert args.output is not None and not args.output.exists()
        args.output.write_text(json.dumps({"status": "PASS: independent109-row certificate replay",
                                          "source_sha256": report["source_sha256"],
                                          "certificate_sha256": sha(args.certificate.read_bytes()),
                                          "optimizer_calls": 0}, indent=2)+"\n")
    print(json.dumps({k: report[k] for k in ("status", "source_sha256", "exact_primal_and_dual_objective", "dimension_upper_bound")}, indent=2))


if __name__ == "__main__":
    main()
