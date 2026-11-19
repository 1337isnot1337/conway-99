"""Check one proved H3 row on all saved branch intervals; no propagation.

Each result is conditional on that branch. A direct enumeration of all
assignments on the ten row coordinates independently checks every interval
minimum, contradiction, and forced literal. No other row is propagated.
"""
import argparse
import hashlib
import itertools
import json
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[2]
BASE = "experiments/logs/grids-and-triangles/"
INPUTS = {
    "h3_source": ("experiments/workspace/rook_case4_face112_third_parity_cover.py",
        "9da8c7edc60429b6a7bee6cd15da447e08a6ae1656a4be5b77b1dd2f5ba5bdb3"),
    "h3_certificate": (BASE+"rook-case4-face112-third-parity-cover-certificate.json",
        "4ab891e2d809847804b4b3d3626f9c4e498d32788d90ddb865da2ed4c98b6ef7"),
    "h3_cold": (BASE+"rook-case4-face112-third-parity-cover-replay.json",
        "a3b57893b112ed96a5e3dc812dfd9dd5ed0776284dbe59165335167214983a76"),
    "branches": (BASE+"rook-case4-face112-disjoint-guard-cuts01.json",
        "9ef2b90b12a08911970952fca73da4d788f99997e71349433d54429c02c49efc"),
    "branches_cold": (BASE+"rook-case4-face112-disjoint-guard-cuts01-replay.json",
        "1300434903fa41f05f993eb1bc9943947e65a061920033f22767c783dfe6429c"),
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read_bound(root, binding):
    path, expected = binding
    raw = (root/path).read_bytes()
    assert sha(raw) == expected, path
    return raw


def interval(terms, values, fixed=None):
    low = high = 0
    for column, coefficient in terms:
        value = fixed[1] if fixed and fixed[0] == column else values[column]
        if value == -1:
            low += min(0, coefficient)
            high += max(0, coefficient)
        else:
            assert value in (0, 1)
            low += coefficient*value
            high += coefficient*value
    return low, high


def build(root):
    raw = {key: read_bound(root, value) for key, value in INPUTS.items()}
    data = {key: json.loads(value) for key, value in raw.items() if key != "h3_source"}
    h3 = data["h3_certificate"]
    cold = data["h3_cold"]
    assert cold["source_sha256"] == INPUTS["h3_source"][1]
    assert cold["certificate_sha256"] == INPUTS["h3_certificate"][1]
    assert cold["status"].startswith("PASS") and cold["full1214_original_expansion"]
    terms = h3["sparse_equivalent"]["terms"]
    upper = h3["sparse_equivalent"]["upper"]
    support = [401, 402, 405, 590, 591, 592, 593, 594, 595]
    assert terms == sorted([[803, 1]]+[[a, -1] for a in support]) and upper == 0
    assert h3["zero663_required"] is False
    certificate = data["branches"]["certificate"]
    assert certificate["all64_retained_branches_cold_checked"]
    assert data["branches_cold"]["status"].startswith("PASS")
    records = certificate["all64_conditional_assignment_records"]
    expected_ids = sorted(set(range(72))-{16, 32, 33, 35, 40, 66, 67, 71})
    assert [r["branch_id"] for r in records] == expected_ids and len(records) == 64
    results, tested = [], 0
    for record in records:
        zero, one = record["zero_columns"], record["one_columns"]
        assert zero == sorted(set(zero)) and one == sorted(set(one)) and not set(zero)&set(one)
        assert len(zero) == record["zero_count"] and len(one) == record["one_count"]
        assert len(zero)+len(one)+record["unassigned_count"] == 1214
        assert set(record["positive_columns"]) <= set(one)
        values = [-1]*1214
        for a in zero:
            values[a] = 0
        for a in one:
            values[a] = 1
        forward, replay = [
            json.loads(read_bound(root, (record[key]["path"], record[key]["sha256"])))
            for key in ("forward_record", "cold_record")]
        assert forward["branch_id"] == replay["branch_id"] == record["branch_id"]
        assert forward["positive_columns"] == replay["positive_columns"] == record["positive_columns"]
        assert replay["forward_record_sha256"] == record["forward_record"]["sha256"]
        assert replay["exact_reason_replay"]["complete_fixed_point_rechecked"]
        assert not replay["exact_reason_replay"]["contradiction"] and not replay["branch_excluded"]
        low, high = interval(terms, values)
        unknown = [a for a, c in terms if values[a] == -1]
        forced = []
        if low <= upper:
            for a in unknown:
                rejected = [value for value in (0, 1)
                            if interval(terms, values, (a, value))[0] > upper]
                assert len(rejected) <= 1
                if rejected:
                    forced.append({"column": a, "value": 1-rejected[0],
                                   "rejected_value": rejected[0],
                                   "rejected_minimum": interval(terms, values, (a, rejected[0]))[0]})
        # Cold arithmetic cross-check: enumerate only the ten-coordinate row box.
        all_values, feasible = [], []
        coefficients = dict(terms)
        fixed = sum(c*values[a] for a, c in terms if values[a] != -1)
        for assignment in itertools.product((0, 1), repeat=len(unknown)):
            value = fixed+sum(coefficients[a]*v for a, v in zip(unknown, assignment))
            all_values.append(value)
            if value <= upper:
                feasible.append(assignment)
        tested += len(all_values)
        assert (min(all_values), max(all_values)) == (low, high)
        assert (not feasible) == (low > upper)
        expected_forced = ([] if not feasible else
            [[a, feasible[0][i]] for i, a in enumerate(unknown)
             if all(row[i] == feasible[0][i] for row in feasible)])
        assert [[item["column"], item["value"]] for item in forced] == expected_forced
        results.append({
            "branch_id": record["branch_id"], "positive_columns": record["positive_columns"],
            "forward_record": record["forward_record"], "cold_record": record["cold_record"],
            "row_coordinates": [[a, values[a]] for a, c in terms],
            "minimum": low, "maximum": high, "upper": upper,
            "immediate_contradiction": low > upper, "new_conditional_literals": forced,
            "ten_coordinate_completions_checked": len(all_values),
            "row_feasible_completions": len(feasible),
        })
    return {
        "status": "PASS: exact one-row diagnostic on all64 saved branch intervals",
        "source_sha256": sha(Path(__file__).read_bytes()),
        "inputs": {key: {"path": p, "sha256": h} for key, (p, h) in INPUTS.items()},
        "row": {"terms": terms, "upper": upper},
        "complete_branch_ids": expected_ids, "branch_count": len(results),
        "immediate_contradictions": [r["branch_id"] for r in results if r["immediate_contradiction"]],
        "branches_with_new_literals": [r["branch_id"] for r in results if r["new_conditional_literals"]],
        "new_literal_occurrences": sum(len(r["new_conditional_literals"]) for r in results),
        "ten_coordinate_completions_checked": tested, "branches": results,
        "all_new_literals_are_branch_conditional": True,
        "new_branch_propagations": 0, "new_reason_replays": 0,
        "optimizer_calls": 0, "global_literal_claims": [], "case4_excluded": False,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    started = time.monotonic()
    result = build(args.root)
    result["seconds"] = time.monotonic()-started
    args.output.write_text(json.dumps(result, indent=2)+"\n")
    print(json.dumps({k: v for k, v in result.items() if k not in ("branches", "inputs")}, indent=2))
