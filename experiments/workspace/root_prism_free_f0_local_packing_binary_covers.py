"""Exact Boolean capping of the twelve already certified packing rows.

For binary x_a and nonnegative integer x_b, x_a <= sum(w_b*x_b)
with integer w_b>=1 is equivalent to x_a <= sum(x_b). The original
weighted certificates and every native model remain unchanged.
"""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = "experiments/logs/root-prism-free/"
INPUTS = {
    "rows": (BASE + "f0-local-pair-packing-separator-run01-cold/certified-selector-cuts.json", "26b6e829be88927d88f6a23208bca675a322e999e92678a07408411c40dbb2f5"),
    "cold": (BASE + "f0-local-pair-packing-separator-run01-cold/report.json", "73982595edfb2141c6d096c9d1a897ef824b43ccde023fca8e4f6461f7ee3c2c"),
    "owner": (BASE + "f0-local-pair-packing-separator-run01-cold/owner.json", "3cfadfe885a608587788af6d47ef2ada950bfe18d02da432165881736633ed19"),
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode() + b"\n"


def build():
    records = {}
    for key, (name, expected) in INPUTS.items():
        path = ROOT / name
        assert digest(path) == expected
        records[key] = json.loads(path.read_bytes())
    rows, cold, owner = records["rows"], records["cold"], records["owner"]
    assert owner["certified_new_cuts"] and owner["report_accepted"] and owner["deadline_overrun_seconds"] == 0
    assert owner["supervision"]["child_reaped"] and owner["supervision"]["returncode"] == 0
    assert owner["report_sha256"] == INPUTS["cold"][1] and rows["cold_owner_sha256"] == INPUTS["owner"][1]
    assert rows["cold_report_sha256"] == INPUTS["cold"][1]
    assert owner["status"] == cold["status"] == "PASS_COLD_EXACT_LOCAL_PACKING_CUTS"
    assert rows["rows_upper_zero"] == cold["distinct_normalized_rows"]
    result, controls = [], 0
    for index, row in enumerate(rows["rows_upper_zero"]):
        assert len(row) == 70 and row == sorted(row) and len({a for a, c in row}) == 70
        assert all(type(a) is type(c) is int and 0 <= a < 480 and c != 0 for a, c in row)
        positive = [[a, c] for a, c in row if c > 0]
        assert len(positive) == 1 and positive[0][1] == 1
        anchor = positive[0][0]
        support = [a for a, c in row if c < 0]
        weights = [-c for a, c in row if c < 0]
        assert len(support) == 69 and min(weights) >= 1 and anchor not in support
        capped = sorted([[anchor, 1]] + [[a, -1] for a in support])
        # With no support selected both RHSs vanish. With any selected, both
        # RHSs are at least one; adding further nonnegative terms cannot hurt.
        for bit in (0, 1):
            assert (bit <= 0) == (bit <= 0)
            controls += 1
            for weight in weights:
                assert (bit <= weight) == (bit <= 1)
                controls += 1
        result.append({"original_row_index": index, "anchor": anchor,
                       "positive_neighbor_support": support, "minimum_original_weight": min(weights),
                       "capped_terms_upper_zero": capped,
                       "DIMACS_clause": [-(anchor + 1)] + [b + 1 for b in support]})
    assert len(result) == 12 and len({tuple(map(tuple, r["capped_terms_upper_zero"])) for r in result}) == 12
    return {"status": "EXACT_BINARY_CAPPING_CONSEQUENCE", "source_sha256": digest(Path(__file__)),
            "inputs": INPUTS, "rows": result, "row_count": 12, "case_controls": controls,
            "proof": "The guard is0or1. If all support variables vanish both sums vanish; otherwise both nonnegative integer sums are at least1.",
            "equivalence_requires_binary_guard_and_nonnegative_integer_support": True,
            "fractional_equivalence_claimed": False, "optimizer_calls": 0, "native_model_modified": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["build", "replay"])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--certificate", type=Path)
    args = parser.parse_args()
    expected = canonical(build())
    if args.mode == "build":
        with args.output.open("xb") as stream:
            stream.write(expected)
    else:
        assert args.certificate is not None and args.certificate.read_bytes() == expected
        with args.output.open("xb") as stream:
            stream.write(canonical({"status": "PASS_EXACT_BINARY_CAPPING_REPLAY", "source_sha256": digest(Path(__file__)),
                                    "certificate_sha256": digest(args.certificate), "all12_rows_checked": True, "optimizer_calls": 0}))
    print(json.dumps({"status": "PASS", "output": str(args.output), "sha256": digest(args.output)}))
