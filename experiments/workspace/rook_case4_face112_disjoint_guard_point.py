"""One exact evaluation of the227 certified disjoint-guard rows."""
import argparse
import hashlib
import json
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[2]
L = "experiments/logs/grids-and-triangles/"
INPUTS = {
    "cuts": (L+"rook-case4-face112-disjoint-guard-cuts01.json",
             "9ef2b90b12a08911970952fca73da4d788f99997e71349433d54429c02c49efc"),
    "cut_replay": (L+"rook-case4-face112-disjoint-guard-cuts01-replay.json",
                   "1300434903fa41f05f993eb1bc9943947e65a061920033f22767c783dfe6429c"),
    "point": (L+"rook-case4-face112-basis-run01/candidate.json",
              "bb81664e8ea9faec6878ee98ec36c5ae844535e805f78fabe7c475a1f83d8ebb"),
    "point_replay": (L+"rook-case4-face112-basis-run01-replay.json",
                     "cda50fcd87c9e5009243b76442a953a0f1f6b6461baead3ecf296cce508a0c59"),
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def run(root, output):
    started = time.monotonic()
    data = {}
    for key, (path, expected) in INPUTS.items():
        encoded = (root/path).read_bytes()
        assert sha(encoded) == expected, path
        data[key] = json.loads(encoded)
    assert data["cut_replay"]["status"].startswith("PASS:")
    assert data["cut_replay"]["certificate_sha256"] == INPUTS["cuts"][1]
    assert data["point_replay"]["status"].startswith("PASS:")
    assert data["point_replay"]["candidate_sha256"] == INPUTS["point"][1]
    assert data["point_replay"]["exact_point_replayed"]
    certificate = data["cuts"]["certificate"]
    assert certificate["all64_retained_branches_cold_checked"]
    cuts = certificate["retained_cuts"]
    assert [row["cut_id"] for row in cuts] == list(range(227))
    assert sum(len(row["terms"]) for row in cuts) == 1681
    point = data["point"]
    denominator = point["common_denominator"]
    assert denominator == point["exact_check"]["common_denominator"] == 145446009
    assert type(denominator) is int and denominator > 0
    numerators = point["exact_check"]["original1214_selector_numerators"]
    assert len(numerators) == 1214
    assert all(type(n) is int and 0 <= n <= denominator for n in numerators)
    margins, violations = [], []
    for row in cuts:
        terms, upper = row["terms"], row["upper"]
        assert terms == sorted(terms) and len({a for a, c in terms}) == len(terms)
        assert all(type(a) is type(c) is int and 0 <= a < 1214 and c in (-1, 1)
                   for a, c in terms)
        assert upper in (0, 1)
        left = sum(c*numerators[a] for a, c in terms)
        gap = left-upper*denominator
        for proof in row["proofs"]:
            guards, target, forced = proof["guards"], proof["target"], proof["forced_value"]
            assert target not in guards and len(guards) == len(set(guards))
            expected = sorted([[g, 1] for g in guards]+[[target, 1 if forced == 0 else -1]])
            assert expected == terms and upper == (1 if forced == 0 else 0)
            alternate = sum(numerators[g] for g in guards)
            alternate += numerators[target]-denominator if forced == 0 else -numerators[target]
            assert alternate == gap
        item = {"cut_id": row["cut_id"], "left_numerator": left,
                "upper_times_denominator": upper*denominator,
                "violation_numerator": gap}
        margins.append(item)
        if gap > 0:
            violations.append({**item, "terms": terms, "upper": upper,
                               "proof_reference_cut_id": row["cut_id"]})
    report = {
        "status": ("EXACT_RATIONAL_POINT_SEPARATED" if violations
                   else "ALL227_CERTIFIED_GUARD_ROWS_PASS_EXACT_RATIONAL_POINT"),
        "source_sha256": sha(Path(__file__).read_bytes()),
        "inputs": {k: {"path": p, "sha256": h} for k, (p, h) in INPUTS.items()},
        "common_denominator": denominator, "rows_evaluated": len(cuts),
        "term_occurrences": 1681, "all_integer_contractions_cross_checked_with_guard_forms": True,
        "violated_rows": len(violations),
        "tight_rows": sum(row["violation_numerator"] == 0 for row in margins),
        "strictly_satisfied_rows": sum(row["violation_numerator"] < 0 for row in margins),
        "maximum_violation_numerator": max(row["violation_numerator"] for row in margins),
        "minimum_violation_numerator": min(row["violation_numerator"] for row in margins),
        "margins": margins, "violations": violations,
        "seven_guard_535_row": margins[certificate["positive_target535_cut_id"]],
        "point_scope": "One exact nonnegative fractional selector point, not Boolean incidence or a graph.",
        "new_optimizer_calls": 0, "new_propagation_calls": 0, "new_reason_replays": 0,
        "case4_excluded": False, "whole_graph_problem_resolved": False,
        "seconds": time.monotonic()-started,
    }
    with output.open("x") as handle:
        json.dump(report, handle, indent=2, allow_nan=False)
        handle.write("\n")
    print(json.dumps({k: report[k] for k in ("status", "rows_evaluated", "violated_rows",
                       "tight_rows", "strictly_satisfied_rows", "maximum_violation_numerator",
                       "minimum_violation_numerator", "seven_guard_535_row", "seconds")}, indent=2))
    print(json.dumps({"result_sha256": sha(output.read_bytes())}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run(args.root, args.output)
