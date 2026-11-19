"""Inspect already cold-checked branch boxes; no propagation or model import."""
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOG = ROOT / "experiments/logs/grids-and-triangles"
BINDINGS = {
    "preparation": ("rook-case4-three-gram-branches-preparation01/preparation.json", "ad3f2b14fd4f60b0d411cd5d920ec461cffed3ab7a0ddf68861b9500cad95ba3"),
    "forward": ("rook-case4-three-gram-branch-batch-v2-run01/child-result.json", "43c2ad18e26f0a8a0fe7e8247a53a68e300c333e773ef721c98c8e115fe441e2"),
    "owner": ("rook-case4-three-gram-branch-batch-v2-run01/supervisor.json", "7d15aaba5028b03baddbcc1ce9930640f3d9964e8cad018c4f3d636b50496f4b"),
    "cold": ("rook-case4-three-gram-branch-batch-v2-run01-cold/child-result.json", "881ea0aaccd5e29cd80e1133b1a74a483e819390edfa7f5dd7bab2fc388cc411"),
    "cold_owner": ("rook-case4-three-gram-branch-batch-v2-run01-cold/supervisor.json", "5c0c3e0b2617e6a309c8e54a3359f3c13dba571fc05373c32937b6d1ddcbaedc"),
    "upper_five": ("rook-case4-full-span-cover-upper-five01.json", "1655bac4e5a5a558e58e0a685aa4dc94489ef5bfb8f065afe43ac8a6ddcd3b1f"),
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def main():
    data = {}
    for key, (name, expected) in BINDINGS.items():
        raw = (LOG / name).read_bytes()
        assert sha(raw) == expected, key
        data[key] = json.loads(raw)
    prep, forward, owner, cold, cold_owner = (data[k] for k in ("preparation", "forward", "owner", "cold", "cold_owner"))
    for record in (owner, cold_owner):
        assert record["status"] == "CHILD_COMPLETE" and record["exit_code"] == 0
        assert record["child_reaped"] and not record["hard_timeout"]
    assert owner["child_result"]["sha256"] == BINDINGS["forward"][1]
    assert cold_owner["child_result"]["sha256"] == BINDINGS["cold"][1]
    assert forward["complete"] and forward["recorded"] == 444 and forward["partial"] == 0
    assert cold["status"] == "PASS" and cold["all444_branches_checked"] and cold["all_saved_records_checked"]
    assert owner["records_preserved"] == forward["records"] and len(cold["checks"]) == 444
    zeros = set(prep["identity"]["proved_zero_columns"])
    positive = set(prep["identity"]["positive_support"])
    assert len(zeros) == 112 and len(positive) == 36
    H = data["upper_five"]["H"]
    assert len(H) == len(set(H)) == 42
    survivors, details = [], []
    terminal_by_kind, h42_counts, conditional_counts = Counter(), Counter(), Counter()
    total_forces = 0
    for i, (branch, reference, check) in enumerate(zip(prep["retained"], owner["records_preserved"], cold["checks"])):
        path = Path(reference["path"])
        assert path.parent == LOG / "rook-case4-three-gram-branch-batch-v2-run01"
        assert path.name == f"branch-{i:03d}.json"
        raw = path.read_bytes()
        assert sha(raw) == reference["sha256"] and len(raw) == reference["bytes"]
        record = json.loads(raw)
        assert record["index"] == check["index"] == branch["branch_id"] == i
        assert record["raw_id"] == check["raw_id"] == branch["raw_id"]
        assert record["selected"] == branch["selected"]
        fixed_zero = sorted(zeros | (positive - set(branch["selected"])))
        assert sha(canonical({"zeros": fixed_zero, "ones": branch["selected"]})) == record["initial_box_sha256"] == branch["initial_box_sha256"]
        state = [-1] * 1214
        for a in fixed_zero:
            state[a] = 0
        for a in branch["selected"]:
            assert state[a] == -1
            state[a] = 1
        for row, a, value in record["trace"]:
            assert type(row) is type(a) is type(value) is int
            assert 0 <= row < 2278 and 0 <= a < 1214 and value in (0, 1)
            assert state[a] == -1
            state[a] = value
        assert len(record["trace"]) == check["forces"]
        terminal = record["terminal"]["status"]
        assert terminal == check["terminal"] and terminal in ("contradiction", "fixed_point")
        terminal_by_kind[(branch["kind"], terminal)] += 1
        total_forces += check["forces"]
        if terminal == "contradiction":
            continue
        survivors.append(state)
        ones = [a for a in H if state[a] == 1]
        free = [a for a in H if state[a] == -1]
        lower, upper = len(ones), len(ones) + len(free)
        possible = [v for v in (1, 3, 5) if lower <= v <= upper]
        h42_counts[tuple(possible)] += 1
        conditional_counts[(branch["kind"], tuple(possible))] += 1
        details.append({"index": i, "raw_id": branch["raw_id"], "kind": branch["kind"],
                        "selected": branch["selected"], "trace_sha256": reference["sha256"],
                        "forced_literals": check["forces"], "final_box_json_sha256": sha(canonical(state)),
                        "H42_fixed_ones": ones, "H42_free_columns": free,
                        "H42_raw_lower": lower, "H42_raw_upper": upper,
                        "H42_possible_odd_values_from_box": possible})
    assert len(survivors) == cold["surviving_boxes"] == 260
    common_zero = [a for a in range(1214) if all(state[a] == 0 for state in survivors)]
    common_one = [a for a in range(1214) if all(state[a] == 1 for state in survivors)]
    new_zero = sorted(set(common_zero) - zeros)
    assert new_zero == cold["global_zero_columns"] and common_one == cold["global_one_columns"]
    report = {
        "status": "PASS: artifact-only branch-box intersection and H42 inspection",
        "source_sha256": sha(Path(__file__).read_bytes()), "bindings": BINDINGS,
        "all444_saved_trace_bindings_checked": True, "all444_prior_exact_cold_checks_bound": True,
        "contradictions": 184, "surviving_fixed_point_boxes": len(survivors), "total_replayed_forces": total_forces,
        "terminal_by_kind": [{"kind": k, "terminal": t, "count": n} for (k, t), n in sorted(terminal_by_kind.items())],
        "global_zero_columns": new_zero, "global_one_columns": common_one,
        "H42_value_set_counts": [{"possible_values": list(k), "count": n} for k, n in sorted(h42_counts.items())],
        "H42_value_set_counts_by_kind": [{"kind": k, "possible_values": list(v), "count": n} for (k, v), n in sorted(conditional_counts.items())],
        "H42_empty_odd_interval_branch_indices": [v["index"] for v in details if not v["H42_possible_odd_values_from_box"]],
        "surviving_branches": details,
        "H42_intervals_are_necessary_box_projections_not_feasibility_witnesses": True,
        "no_extra_branch_deduction_applied_to_global_intersection": True,
        "prior_cold_reason_and_fixed_point_checks_repeated": False,
        "model_imports": 0, "case_propagation_calls": 0, "optimizer_calls": 0, "case4_excluded": False,
    }
    path = LOG / "rook-case4-three-gram-branch-batch-v2-run01-analysis.json"
    assert not path.exists()
    path.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")
    print(json.dumps({k: report[k] for k in ("status", "source_sha256", "total_replayed_forces", "terminal_by_kind", "global_zero_columns", "global_one_columns", "H42_value_set_counts", "H42_value_set_counts_by_kind", "H42_empty_odd_interval_branch_indices")}, sort_keys=True))
    print(json.dumps({"path": str(path.relative_to(ROOT)), "sha256": sha(path.read_bytes())}))


if __name__ == "__main__":
    main()
