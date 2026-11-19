"""Arithmetic coverage and conditional-literal summary of the frozen branch batch.

This does not propagate, replay a reason, call a solver, or promote a literal.
It reads only records already accepted by the separate cold checker.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOGS = "experiments/logs/grids-and-triangles/"
SCOPE = LOGS + "rook-case4-face112-branch-preparation01.json"
SCOPE_SHA = "5e8bf7a32063cda146b18de2a4b3ee7c4b2a043d5076a5d4a9a9e4ca678144c2"
FORWARD = LOGS + "rook-case4-face112-branch-batch01/result.json"
FORWARD_SHA = "186df7589b3baf14adda7fcce8409e89e149b5268ff432f12128b7301d09ab4b"
COLD = LOGS + "rook-case4-face112-branch-batch01-cold/result.json"
RUNNER_SHA = "cda346ce4bb34a9ccc1f5fc603485124bc0cb389b8b9cc48d169b08297a6bd60"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def run(root, output):
    def read(path, expected=None):
        encoded = (root/path).read_bytes()
        if expected is not None:
            assert sha(encoded) == expected, path
        return json.loads(encoded), sha(encoded)

    scope, _ = read(SCOPE, SCOPE_SHA)
    forward, _ = read(FORWARD, FORWARD_SHA)
    cold, cold_sha = read(COLD)
    assert cold["forward_result"] == {"path": FORWARD, "sha256": FORWARD_SHA}
    assert cold["source_sha256"] == forward["source_sha256"] == RUNNER_SHA
    assert cold["preparation_sha256"] == forward["preparation_sha256"]
    assert cold["scope_preparation_sha256"] == forward["scope_preparation_sha256"] == SCOPE_SHA
    assert not forward["case4_excluded"] and not forward["accepted_branch_exclusions"]
    assert forward["saved_complete_outcomes"] == {"exact interval and guarded-cover fixed point": 50}
    assert forward["saved_partial_branch_ids"] == [55]
    assert not cold["verified_contradiction_branch_ids"] and not cold["case4_excluded"]

    forward_records = {}
    for item in forward["saved_file_bindings"]:
        record, _ = read(item["path"], item["sha256"])
        assert record["source_sha256"] == RUNNER_SHA
        assert record["preparation_sha256"] == forward["preparation_sha256"]
        assert record["branch_id"] not in forward_records
        forward_records[record["branch_id"]] = record
    assert list(forward_records) == forward["saved_complete_branch_ids"] + [55]
    seeds = set(scope["seed_zero_columns"])
    conditional = []
    zeros_intersection = ones_intersection = None
    independent_candidates = {}
    for item in cold["saved_file_bindings"]:
        checked, _ = read(item["path"], item["sha256"])
        branch_id = checked["branch_id"]
        record = forward_records[branch_id]
        trace = record["trace"]
        expected_path = LOGS + "rook-case4-face112-branch-batch01/branch%02d.json" % branch_id
        _, record_sha = read(expected_path)
        assert checked["forward_record_sha256"] == record_sha
        assert checked["positive_columns"] == record["positive_columns"]
        assert checked["augmented_rows_sha256"] == record["augmented_rows_sha256"]
        assert checked["exact_reason_replay"] == {
            "all_records_checked": len(trace["records"]),
            "contradiction": False, "complete_fixed_point_rechecked": True}
        assert trace["complete"] and trace["status"] == "exact interval and guarded-cover fixed point"
        zeros = {i for i, v in enumerate(trace["values"]) if v == 0}
        ones = {i for i, v in enumerate(trace["values"]) if v == 1}
        assert seeds <= zeros and set(record["positive_columns"]) <= ones
        zeros_intersection = zeros if zeros_intersection is None else zeros_intersection & zeros
        ones_intersection = ones if ones_intersection is None else ones_intersection & ones
        conditional.append({
            "branch_id": branch_id, "positive_columns": record["positive_columns"],
            "zero_count": len(zeros), "one_count": len(ones),
            "unassigned_count": 1214-len(zeros)-len(ones),
            "new_zero_columns_beyond112": sorted(zeros-seeds),
            "one_columns": sorted(ones),
            "assumption_rows_are_conditional": True,
        })
        independent = []
        for index, reason in enumerate(trace["records"]):
            assert reason["kind"] == "assignment"
            parents = reason["prior_assignment_indices"]
            assert all(0 <= i < index for i in parents)
            origin = reason["origin"]
            assert origin["family"] in ("base_row", "cover")
            uses_branch = origin["family"] == "base_row" and origin["id"] >= 2390
            safe = not uses_branch and all(independent[i] for i in parents)
            independent.append(safe)
            a, value = reason["variable"], reason["value"]
            if safe and (value == 1 or a not in seeds):
                key = (a, value)
                independent_candidates.setdefault(key, {"column": a, "value": value,
                                                        "branch_id": branch_id,
                                                        "record_index": index})
    ids = [r["branch_id"] for r in conditional]
    assert ids == cold["verified_fixed_point_branch_ids"]
    assert ids == cold["verified_complete_branch_ids"]
    original = scope["full_branch_ledger"]
    partition = Counter()
    complete = set(forward["saved_complete_branch_ids"])
    partial = set(forward["saved_partial_branch_ids"])
    unqueried = set(forward["unqueried_branch_ids"])
    checked_ids = set(ids)
    dispositions = []
    for branch in original:
        i = branch["branch_id"]
        if i not in scope["retained_branch_ids"]:
            status = branch["disposition"]
        elif i in checked_ids:
            status = "cold_checked_fixed_point_not_feasibility"
        elif i in complete:
            status = "forward_fixed_point_not_cold_checked"
        elif i in partial:
            status = "partial_forward_trace_not_cold_checked"
        elif i in unqueried:
            status = "unqueried"
        else:
            assert i == forward["active_branch_without_saved_trace"]
            status = "active_without_saved_trace"
        partition[status] += 1
        dispositions.append({"branch_id": i, "positive_columns": branch["positive_columns"], "status": status})
    assert sum(partition.values()) == 72
    remaining = [r for r in dispositions if not r["status"].startswith("excluded_by_")]
    assert len(remaining) == 64
    report = {
        "status": "EXACT COVERAGE AND CONDITIONAL-LITERAL SUMMARY; NO NEW EXCLUSION",
        "source_sha256": sha(Path(__file__).read_bytes()),
        "inputs": {"scope": {"path": SCOPE, "sha256": SCOPE_SHA},
                   "forward": {"path": FORWARD, "sha256": FORWARD_SHA},
                   "cold": {"path": COLD, "sha256": cold_sha}},
        "all72_pattern_partition": dict(partition), "all72_pattern_dispositions": dispositions,
        "remaining64_patterns": remaining,
        "cold_checked_conditional_assignments": conditional,
        "conditional_zero_count_histogram": dict(Counter(r["zero_count"] for r in conditional)),
        "conditional_one_count_histogram": dict(Counter(r["one_count"] for r in conditional)),
        "literals_uniform_only_over_checked_fixed_points": {
            "branch_ids": ids, "zero_columns": sorted(zeros_intersection or []),
            "new_zero_columns_beyond112": sorted((zeros_intersection or set())-seeds),
            "one_columns": sorted(ones_intersection or []),
            "complete_remaining_cover_checked": len(ids) == 64,
            "global_promotion_performed": False,
        },
        "candidate_literals_with_no_branch_assumption_in_record_ancestry": sorted(
            independent_candidates.values(), key=lambda r: (r["column"], r["value"])),
        "candidate_ancestry_scope": "Bookkeeping on checked traces only; no separate global certificate is claimed.",
        "branch_propagations_called": 0, "reason_checker_calls": 0,
        "solver_calls": 0, "optimizer_calls": 0,
        "global_coordinate_assignments_claimed": [], "case4_excluded": False,
        "whole_graph_problem_resolved": False,
    }
    with output.open("x") as handle:
        json.dump(report, handle, indent=2, allow_nan=False)
        handle.write("\n")
    summary = {k: report[k] for k in ("status", "all72_pattern_partition",
               "conditional_zero_count_histogram", "conditional_one_count_histogram",
               "candidate_literals_with_no_branch_assumption_in_record_ancestry")}
    summary["checked_fixed_points"] = len(ids)
    summary["uniform_new_zeros_only_within_checked_branches"] = report[
        "literals_uniform_only_over_checked_fixed_points"]["new_zero_columns_beyond112"]
    summary["uniform_ones_only_within_checked_branches"] = report[
        "literals_uniform_only_over_checked_fixed_points"]["one_columns"]
    summary["report_sha256"] = sha(output.read_bytes())
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, default=ROOT)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    run(a.root, a.output)
