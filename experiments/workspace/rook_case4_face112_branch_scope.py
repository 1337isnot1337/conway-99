"""Complete Boolean branch cover on the proved 112-zero incidence face.

Preparation checks all 40 difference-set pairs against every original native
row box. It does not run branch propagation, a solver, or an optimizer.
"""
import argparse
from collections import Counter
import hashlib
from itertools import product
import json
from pathlib import Path
import time

import rook_case4_face112_primary_closure_v3 as base

ROOT = Path(__file__).resolve().parents[2]
BASE_SHA = "405f732445043762db0c52cbc0cfdc159dcb945351925afdcc57af7c9606b3f9"
RULE_SHA = "3e4b8a5118c0ee8e37aee03d5f265128b53af9ae8ffc169393fe2d731062d8f7"
BASE_PREPARATION = "experiments/logs/grids-and-triangles/rook-case4-face112-primary-closure-preparation03.json"
BASE_PREPARATION_SHA = "b005a338bd10a61769718afb0f6cab7c39b2f7b86bf46cee228a951398fd585c"
BOUND_REPORT = "experiments/logs/grids-and-triangles/rook-case4-face111-native-bounds-independent-replay.json"
BOUND_REPORT_SHA = "5e1e01b8c5f3c5747292d65e6938263afe7a72bfff68b00ee29cf2f41b23b2a3"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def save_new(path, value):
    with path.open("x") as f:
        json.dump(value, f, indent=2, allow_nan=False)
        f.write("\n")


def literal_cover(H1, H2):
    common = sorted(set(H1) & set(H2))
    A, B = sorted(set(H1) - set(H2)), sorted(set(H2) - set(H1))
    patterns = [[a] for a in common] + [sorted([a, b]) for a in A for b in B]
    assert len(set(map(tuple, patterns))) == len(patterns)
    return common, A, B, patterns


def controls():
    checks = satisfying = 0
    for common_size, a_size, b_size in product(range(4), range(3), range(3)):
        common = list(range(common_size))
        A = list(range(common_size, common_size + a_size))
        B = list(range(common_size + a_size, common_size + a_size + b_size))
        H1, H2 = common + A, common + B
        _, _, _, patterns = literal_cover(H1, H2)
        for values in product((0, 1), repeat=common_size + a_size + b_size):
            feasible = sum(values[j] for j in H1) == sum(values[j] for j in H2) == 1
            matching = [P for P in patterns if all(values[j] for j in P)]
            if feasible:
                assert len(matching) == 1
                assert [j for j, v in enumerate(values) if v] == matching[0]
                satisfying += 1
            # Branches alone do not impose zeros outside their support.
            checks += 1
    return {"complete_small_Boolean_assignments": checks,
            "feasible_unit_sum_assignments": satisfying,
            "unique_cover_pattern_for_every_feasible_assignment": True,
            "production_branch_propagations": 0}


def box(row, zero_columns, positive_columns):
    fixed = sum(c for a, c in row["terms"] if a in positive_columns)
    free = [c for a, c in row["terms"] if a not in zero_columns and a not in positive_columns]
    return fixed + sum(min(c, 0) for c in free), fixed + sum(max(c, 0) for c in free)


def derive(root):
    assert sha(Path(base.__file__).read_bytes()) == BASE_SHA
    assert sha(Path(base.rules.__file__).read_bytes()) == RULE_SHA
    prior = (root/BASE_PREPARATION).read_bytes()
    assert sha(prior) == BASE_PREPARATION_SHA
    saved = json.loads(prior)
    record, native, rows, raw, units, seed = base.load(root)
    assert all(saved[k] == value for k, value in record.items())
    assert len(native) == 2277 and len(rows) == 2389
    assert len(raw) == 178533 * 154
    assert not saved["production_propagation_run"]
    report_raw = (root/BOUND_REPORT).read_bytes()
    assert sha(report_raw) == BOUND_REPORT_SHA
    independent = json.loads(report_raw)
    S = independent["short_identity"]["S"]
    assert len(S) == 86 and independent["short_identity"]["identity_on_proved_face"] == "3*x_663 + sum_{a in S} x_a = 2"
    assert 663 in seed and not(set(S) & set(seed))
    sum_row = base.rules.row([[a, 1] for a in S], 2, 2,
                             "proved_663_identity_after_zero", BOUND_REPORT_SHA)
    full_rows = rows + [sum_row]

    prior_zeros, zeros = set(record["old111_zero_columns"]), set(seed)
    H_before = [sorted(a for a, c in native[2271+k]["terms"] if a not in prior_zeros)
                for k in range(2)]
    assert all(c == 1 for k in range(2) for a, c in native[2271+k]["terms"])
    assert all(native[2271+k]["lower"] == native[2271+k]["upper"] == 1 for k in range(2))
    common, A, B, patterns = literal_cover(*H_before)
    assert (len(common), len(A), len(B), len(patterns)) == (32, 4, 10, 72)
    assert A == [259, 260, 261, 262]
    known_pairs = {tuple(pair) for pair in record["certified_pair_AMO_rows"]}
    assert known_pairs == {(259, 590), (259, 591), (259, 593), (259, 732)}
    pair_checks = []
    by_pair = {}
    for a in A:
        for b in B:
            positive = {a, b}
            assert not (positive & zeros)
            violations = []
            for row_id, row in enumerate(native[:2271]):
                lo, hi = box(row, zeros, positive)
                if lo > row["upper"] or hi < row["lower"]:
                    violations.append({
                        "original_native_row": row_id, "family": row["family"],
                        "source": row["source"], "row_sha256": sha(canonical(row)),
                        "minimum": lo, "maximum": hi,
                        "lower": row["lower"], "upper": row["upper"],
                    })
            item = {"positive_columns": sorted(positive), "original_native_rows_checked": 2271,
                    "known_certified_pair": tuple(sorted(positive)) in known_pairs,
                    "direct_box_contradictions": violations}
            pair_checks.append(item)
            by_pair[tuple(sorted(positive))] = item
    assert len(pair_checks) == 40

    ledger = []
    for branch_id, pattern in enumerate(patterns):
        zero_hits = sorted(set(pattern) & zeros)
        pair = tuple(pattern)
        direct = by_pair.get(pair, {}).get("direct_box_contradictions", [])
        if zero_hits:
            disposition = "excluded_by_proved_zero"
        elif pair in known_pairs:
            disposition = "excluded_by_certified_pair"
        elif direct:
            disposition = "excluded_by_original_native_box"
        else:
            disposition = "retained_for_bounded_branch_propagation"
        assumption_rows = [base.rules.row([[a, 1]], 1, 1, "branch_positive_assumption",
                                          {"branch_id": branch_id, "column": a})
                           for a in pattern]
        ledger.append({
            "branch_id": branch_id,
            "positive_columns": pattern,
            "disposition": disposition,
            "proved_zero_hits": zero_hits,
            "original_native_box_witnesses": direct,
            "assumption_rows": assumption_rows,
            "augmented_row_count": len(full_rows) + len(assumption_rows),
            "augmented_rows_sha256": sha(canonical(full_rows + assumption_rows)),
        })
    survivors = [r["branch_id"] for r in ledger if r["disposition"] == "retained_for_bounded_branch_propagation"]
    counts = dict(Counter(r["disposition"] for r in ledger))
    assert counts["excluded_by_proved_zero"] == 1 and counts["excluded_by_certified_pair"] == 4
    assert ledger[patterns.index([663])]["disposition"] == "excluded_by_proved_zero"
    return {
        "schema": "conway99.rook-case4-face112-branch-scope.v1",
        "source_sha256": sha(Path(__file__).read_bytes()),
        "closure_source_sha256": BASE_SHA,
        "unchanged_rule_and_trace_checker_sha256": RULE_SHA,
        "base_preparation": {"path": BASE_PREPARATION, "sha256": BASE_PREPARATION_SHA},
        "short_identity_report": {"path": BOUND_REPORT, "sha256": BOUND_REPORT_SHA},
        "complete_input_bindings": record,
        "original_primary_variables": 1214,
        "original_native_rows": 2271,
        "all_registered_coordinate_covers": 178533,
        "registry_raw_sha256": sha(raw),
        "seed_zero_columns": seed,
        "initial_cover_unit_ids": units,
        "unit_sum_supports_before_663": H_before,
        "common_before_663": common, "A": A, "B": B,
        "original_cover_pattern_count": 72,
        "known_five_excluded_patterns": [[663], *map(list, sorted(known_pairs))],
        "all40_pair_box_checks": pair_checks,
        "pair_box_row_evaluations": 40 * 2271,
        "direct_pair_box_incompatible_count": sum(bool(r["direct_box_contradictions"]) for r in pair_checks),
        "full_branch_ledger": ledger,
        "disposition_counts": counts,
        "retained_branch_ids": survivors,
        "retained_branch_count": len(survivors),
        "fixed_branch_order": "Increasing original pattern ID: sorted common singletons, then A-major/B-minor sorted pairs.",
        "base_augmented_rows": len(full_rows),
        "base_augmented_rows_sha256": sha(canonical(full_rows)),
        "added_sum_two_row": sum_row,
        "base_and_sum_two_term_occurrences": sum(len(row["terms"]) for row in full_rows),
        "maximum_branch_assumption_rows": 2,
        "proposed_total_forward_batch_seconds": 60,
        "proposed_separate_total_cold_batch_seconds": 60,
        "cooperative_forward_timer": "The existing engine checks every native row and every 128 cover records; completed traces and an interrupted prefix remain explicit.",
        "no_branch_negatives_assumed": True,
        "branch_rows_are_conditional_not_global": True,
        "coverage_proof": "When both unit sums equal one, either one common variable is selected and both differences are empty, or the common part is empty and each difference contains one selected variable.",
        "all72_pattern_dispositions_accounted_for": len(ledger) == 72,
        "production_branch_propagations": 0,
        "solver_calls": 0, "optimizer_calls": 0,
        "case4_excluded": False,
    }, full_rows, raw, units


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=("prepare", "replay"))
    p.add_argument("--root", type=Path, default=ROOT)
    p.add_argument("--preparation", type=Path)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    assert not a.output.exists()
    started = time.monotonic()
    record, _, _, _ = derive(a.root)
    control = controls()
    if a.mode == "prepare":
        output = dict(record, status="PREPARED: complete branch cover and direct pair-box census; no propagation",
                      controls=control, preparation_seconds=time.monotonic()-started)
    else:
        assert a.preparation is not None
        saved = json.loads(a.preparation.read_bytes())
        assert all(saved[k] == value for k, value in record.items())
        assert saved["controls"] == control
        output = {"status": "PASS: complete branch-cover and direct-pair-box preparation replay",
                  "source_sha256": record["source_sha256"],
                  "preparation_sha256": sha(a.preparation.read_bytes()),
                  "all72_pattern_dispositions_checked": True,
                  "all40_pair_box_checks_rebuilt": True,
                  "retained_branch_count": record["retained_branch_count"],
                  "production_branch_propagations": 0,
                  "solver_calls": 0, "optimizer_calls": 0,
                  "seconds": time.monotonic()-started}
    save_new(a.output, output)
    print(json.dumps({k: output[k] for k in
          ("status", "source_sha256", "retained_branch_count", "disposition_counts",
           "direct_pair_box_incompatible_count", "base_augmented_rows",
           "base_and_sum_two_term_occurrences", "preparation_seconds", "seconds") if k in output},
          indent=2))


if __name__ == "__main__":
    main()
