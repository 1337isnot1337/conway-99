"""Derive exact disjoint-guard inequalities from already cold-checked branches.

No propagation or reason replay is repeated. Each implication is linked to
its literal record in a complete trace accepted by the frozen cold checker.
"""
import argparse
from collections import Counter
import hashlib
from itertools import product
import json
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[2]
L = "experiments/logs/grids-and-triangles/"
OLD_SOURCE = "cda346ce4bb34a9ccc1f5fc603485124bc0cb389b8b9cc48d169b08297a6bd60"
NEW_SOURCE = "71e27c5a8b0ff9e268979637d45f6e919806e3653228ece88b69764834d9f478"
OLD_PREP = "47ebe7180723ab95bdf5370c29a0be6abe80005dc5e0bd7e3df51926282b87ea"
NEW_PREP = "6d307ce3cea403d8ba4f37b3b1acd78bf9bc7111ab620a3a22c275f7d49e7ca5"
INPUTS = {
    "scope": (L+"rook-case4-face112-branch-preparation01.json",
              "5e8bf7a32063cda146b18de2a4b3ee7c4b2a043d5076a5d4a9a9e4ca678144c2"),
    "rows": (L+"rook-case4-face112-branch-batch-preparation01/rows.json",
             "361f04e0176d0ac53bed09ff9c7cdf33d76608b99c3a2426f0cf35345da46a55"),
    "old_forward": (L+"rook-case4-face112-branch-batch01/result.json",
                    "186df7589b3baf14adda7fcce8409e89e149b5268ff432f12128b7301d09ab4b"),
    "new_forward": (L+"rook-case4-face112-branch-continuation01-forward/result.json",
                    "6d42fa285b24ca5c0e646922934576ea5d9b0bb0a0b90cbaff7bbdddd95cbd49"),
    "old_cold": (L+"rook-case4-face112-branch-batch01-cold/result.json",
                 "b789fc8ee377e1899d4de553ad7c48019fdea8913599fb3c8605bf28cb80205e"),
    "old_cold_continuation": (L+"rook-case4-face112-branch-continuation01-cold-old/result.json",
                              "acbc2fde9ed1f342e6d33ef9dd24f600f70e23be8623cfdd09a4947475db3c5b"),
    "new_cold": (L+"rook-case4-face112-branch-continuation01-cold-new/result.json", "4329b386b6fb5a7493a7159f18c90332cd0765e68cff4e16b67f3456728198e0"),
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def read(root, path, expected):
    raw = (root/path).read_bytes()
    assert sha(raw) == expected, path
    return json.loads(raw)


def controls():
    checks = satisfying = 0
    for n in range(9):
        for values in product((0, 1), repeat=n+1):
            target, guards = values[0], values[1:]
            for forced in (0, 1):
                premise = sum(guards) <= 1 and all(not g or target == forced for g in guards)
                if premise:
                    if forced == 0:
                        assert sum(guards)+target <= 1
                    else:
                        assert sum(guards) <= target
                    satisfying += 1
                checks += 1
    return {"complete_Boolean_guard_assignments": checks,
            "satisfying_implication_and_at_most_one_assignments": satisfying,
            "zero_and_one_target_inequalities_checked": True,
            "target_is_distinct_from_every_nontrivial_guard": True}


def load_checked(root):
    data = {k: read(root, path, expected) for k, (path, expected) in INPUTS.items()}
    scope = data["scope"]
    rows = data["rows"]["rows"]
    assert sha(canonical(rows)) == scope["base_augmented_rows_sha256"]
    assert len(rows) == 2390 and len(scope["retained_branch_ids"]) == 64
    forward = {}
    for key, expected_source, expected_prep in (
            ("old_forward", OLD_SOURCE, OLD_PREP), ("new_forward", NEW_SOURCE, NEW_PREP)):
        result = data[key]
        assert result["source_sha256"] == expected_source
        assert result["preparation_sha256"] == expected_prep
        complete = result["saved_complete_branch_ids"]
        references = {}
        for binding in result["saved_file_bindings"]:
            record = read(root, binding["path"], binding["sha256"])
            assert record["source_sha256"] == expected_source
            assert record["preparation_sha256"] == expected_prep
            i = record["branch_id"]
            references[i] = binding
            if i not in complete:
                assert key == "old_forward" and i == 55 and not record["trace"]["complete"]
                continue
            assert i not in forward
            branch = scope["full_branch_ledger"][i]
            assert record["positive_columns"] == branch["positive_columns"]
            assert record["augmented_rows_sha256"] == branch["augmented_rows_sha256"]
            assert record["trace"]["complete"]
            assert record["trace"]["status"] == "exact interval and guarded-cover fixed point"
            forward[i] = (record, binding)
        assert set(complete) <= set(references)
    assert set(forward) == set(scope["retained_branch_ids"])
    cold = {}
    for key, expected_source, expected_prep in (
            ("old_cold", OLD_SOURCE, OLD_PREP),
            ("old_cold_continuation", NEW_SOURCE, NEW_PREP),
            ("new_cold", NEW_SOURCE, NEW_PREP)):
        result = data[key]
        assert result["source_sha256"] == expected_source
        assert result["preparation_sha256"] == expected_prep
        done = result["verified_complete_branch_ids"] if key == "old_cold" else result["verified_branch_ids"]
        checked = []
        for binding in result["saved_file_bindings"]:
            record = read(root, binding["path"], binding["sha256"])
            i = record["branch_id"]
            assert i not in cold
            assert record["source_sha256"] == expected_source
            assert record["preparation_sha256"] == expected_prep
            prior, reference = forward[i]
            if key == "old_cold":
                assert record["forward_record_sha256"] == reference["sha256"]
            else:
                assert record["forward_record"] == reference
            assert record["positive_columns"] == prior["positive_columns"]
            assert record["augmented_rows_sha256"] == prior["augmented_rows_sha256"]
            assert record["exact_reason_replay"] == {
                "all_records_checked": len(prior["trace"]["records"]),
                "contradiction": False, "complete_fixed_point_rechecked": True}
            assert not record["branch_excluded"]
            cold[i] = (record, binding)
            checked.append(i)
        assert checked == done
    assert set(cold) == set(scope["retained_branch_ids"])
    return scope, rows, forward, cold


def derive(root):
    scope, rows, forward, cold = load_checked(root)
    seed = set(scope["seed_zero_columns"])
    common = set(scope["common_before_663"])-seed
    assert len(common) == 31
    unit = rows[2271]
    assert unit["lower"] == unit["upper"] == 1
    assert all(coefficient == 1 for _, coefficient in unit["terms"])
    assert common <= {a for a, _ in unit["terms"]}
    branch_inventory, guard_ledger = [], {}
    uniform_zero, uniform_one = set(range(1214)), set(range(1214))
    for i in scope["retained_branch_ids"]:
        record, ref = forward[i]
        _, cold_ref = cold[i]
        values = record["trace"]["values"]
        assert len(values) == 1214 and all(v in (-1, 0, 1) for v in values)
        indices = {}
        for index, event in enumerate(record["trace"]["records"]):
            assert event["kind"] == "assignment" and event["variable"] not in indices
            assert values[event["variable"]] == event["value"]
            indices[event["variable"]] = index
        zeros = {a for a, value in enumerate(values) if value == 0}
        ones = {a for a, value in enumerate(values) if value == 1}
        assert seed <= zeros and set(record["positive_columns"]) <= ones
        uniform_zero &= zeros
        uniform_one &= ones
        branch_inventory.append({
            "branch_id": i, "positive_columns": record["positive_columns"],
            "zero_count": len(zeros), "one_count": len(ones),
            "unassigned_count": 1214-len(zeros)-len(ones),
            "zero_columns": sorted(zeros), "one_columns": sorted(ones),
            "forward_record": ref, "cold_record": cold_ref})
        if len(record["positive_columns"]) == 1:
            guard = record["positive_columns"][0]
            assert guard in common and guard not in guard_ledger
            guard_ledger[guard] = {"branch_id": i, "forward_record": ref, "cold_record": cold_ref,
                                   "values": values, "record_indices": indices}
    assert set(guard_ledger) == common

    capacities = []
    for i, row in enumerate(rows):
        live = [(a, c) for a, c in row["terms"] if a not in seed]
        if row["upper"] == 1 and live and all(c == 1 for _, c in live):
            capacities.append((i, {a for a, _ in live}))
    cuts, dispositions, seen = [], [], {}
    for target in range(1214):
        for forced in (0, 1):
            guards = [g for g in sorted(common) if guard_ledger[g]["values"][target] == forced]
            self_guard_removed = target in guards
            if forced == 1 and self_guard_removed:
                guards.remove(target)
            assert target not in guards
            entry = {"target": target, "forced_value": forced, "guards": guards,
                     "self_guard_tautology_omitted": self_guard_removed}
            if not guards:
                entry["disposition"] = "no_nontrivial_guard_implication"
            elif forced == 0 and target in seed:
                entry["disposition"] = "redundant_by_proved_zero_and_guard_unit_sum"
            else:
                terms = [[g, 1] for g in guards] + [[target, 1 if forced == 0 else -1]]
                terms.sort()
                upper = 1 if forced == 0 else 0
                support = {a for a, _ in terms}
                capacity = next((i for i, s in capacities if support <= s), None) if forced == 0 else None
                if capacity is not None:
                    entry.update(disposition="already_implied_by_retained_native_capacity",
                                 native_capacity_row=capacity,
                                 native_capacity_row_sha256=sha(canonical(rows[capacity])))
                else:
                    witnesses = []
                    for guard in guards:
                        ledger = guard_ledger[guard]
                        index = ledger["record_indices"][target]
                        witnesses.append({"guard": guard, "branch_id": ledger["branch_id"],
                                          "target_literal_record_index": index})
                    key = canonical({"terms": terms, "upper": upper})
                    proof = {"target": target, "forced_value": forced, "guards": guards,
                             "literal_witnesses": witnesses}
                    if key in seen:
                        identifier = seen[key]
                        cuts[identifier]["proofs"].append(proof)
                        entry.update(disposition="duplicate_exact_inequality", cut_id=identifier)
                    else:
                        identifier = len(cuts)
                        seen[key] = identifier
                        cuts.append({"cut_id": identifier, "terms": terms, "upper": upper,
                                     "proofs": [proof]})
                        entry.update(disposition="retained_exact_guard_inequality", cut_id=identifier)
            dispositions.append(entry)
    assert len(dispositions) == 2428
    assert not any(g == p["target"] for row in cuts for p in row["proofs"] for g in p["guards"])
    special_terms = sorted([[a, 1] for a in [74, 75, 76, 77, 176, 177, 178]]+[[535, -1]])
    seven = {74, 75, 76, 77, 176, 177, 178}
    special = [row["cut_id"] for row in cuts if row["upper"] == 0
               and dict(row["terms"]).get(535) == -1
               and seven <= {a for a, c in row["terms"] if c == 1}]
    assert len(special) == 1
    return {
        "schema": "conway99.face112-disjoint-guard-cuts.v1",
        "source_sha256": sha(Path(__file__).read_bytes()),
        "inputs": {k: {"path": p, "sha256": h} for k, (p, h) in INPUTS.items()},
        "all64_retained_branches_cold_checked": True,
        "all64_outcomes": "Complete interval-and-cover fixed points, not Boolean feasibility.",
        "all64_conditional_assignment_records": branch_inventory,
        "uniform_literals_across_all64": {
            "zero_columns": sorted(uniform_zero),
            "new_zero_columns_beyond112": sorted(uniform_zero-seed),
            "one_columns": sorted(uniform_one),
            "separate_global_promotion_performed": False},
        "guard_unit_sum_row": {"native_row_id": 2271, "row": unit,
                               "row_sha256": sha(canonical(unit))},
        "complete_common_guard_columns": sorted(common),
        "guard_trace_bindings": {str(g): {k: v for k, v in r.items()
                                         if k in ("branch_id", "forward_record", "cold_record")}
                                  for g, r in sorted(guard_ledger.items())},
        "complete_target_value_ledger": dispositions,
        "disposition_counts": dict(Counter(r["disposition"] for r in dispositions)),
        "retained_cuts": cuts, "retained_cut_count": len(cuts),
        "retained_term_occurrences": sum(len(r["terms"]) for r in cuts),
        "positive_target535_cut_id": special[0],
        "seven_guard_535_subinequality": {"terms": special_terms, "upper": 0,
                                         "implied_by_retained_cut": special[0]},
        "proof": {
            "scope": "Boolean completions on the proved112-zero case4 face.",
            "zero": "At most one guard is selected. If the target is one, every guard forcing zero is absent. Hence sum(guards)+target<=1.",
            "one": "If the target is zero, every guard forcing one is absent. If it is one, the guard sum is at most one. Hence sum(guards)<=target.",
            "coverage": "Each cut uses certified implications only; it does not require every common guard to be present.",
            "native_pruning": "After the112 proved zeros, a retained nonnegative unit-coefficient capacity row bounds every subset of its support by one.",
        },
        "controls": controls(),
        "new_branch_propagations": 0, "new_reason_replays": 0,
        "point_evaluations": 0, "optimizer_calls": 0, "case4_excluded": False,
        "whole_graph_problem_resolved": False,
    }


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=("prepare", "replay"))
    p.add_argument("--root", type=Path, default=ROOT)
    p.add_argument("--certificate", type=Path)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    assert not a.output.exists()
    started = time.monotonic()
    record = derive(a.root)
    if a.mode == "prepare":
        result = {"status": "PREPARED: complete branch aggregation and exact guard-cut derivations",
                  "certificate": record, "seconds": time.monotonic()-started}
    else:
        assert a.certificate is not None
        saved = json.loads(a.certificate.read_bytes())
        assert canonical(saved["certificate"]) == canonical(record)
        result = {"status": "PASS: all64 bindings, complete target ledger and exact guard-cut derivations",
                  "source_sha256": record["source_sha256"],
                  "certificate_sha256": sha(a.certificate.read_bytes()),
                  "retained_cut_count": record["retained_cut_count"],
                  "new_reason_replays": 0, "point_evaluations": 0,
                  "seconds": time.monotonic()-started}
    with a.output.open("x") as handle:
        json.dump(result, handle, indent=2, allow_nan=False)
        handle.write("\n")
    summary = {k: record[k] for k in ("retained_cut_count", "retained_term_occurrences",
               "disposition_counts", "positive_target535_cut_id", "uniform_literals_across_all64")}
    summary.update(status=result["status"], seconds=result["seconds"],
                   output_sha256=sha(a.output.read_bytes()))
    print(json.dumps(summary, indent=2))
