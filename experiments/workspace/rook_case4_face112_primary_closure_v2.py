"""One exact closure from 112 proved zeros, two unit sums and four pair AMOs.

The complete original 2271 native rows and 178533 registered covers remain.
Only the audited 663 zero, H1 upper bound and four pair bounds are added to
the earlier 111-zero closure. The propagation and reason checker are frozen.
"""
import argparse
import hashlib
from itertools import product
import json
from pathlib import Path
import time

import rook_case4_face111_primary_closure_v2 as previous
import rook_case4_face111_two_parity_equalities as equalities
import rook_case4_face111_native_bounds_independent_replay as audit

ROOT = Path(__file__).resolve().parents[2]
BASE = "experiments/logs/grids-and-triangles/"
PREVIOUS_SHA = "983d62f91f4bd7ce53e1a11897d41dbf3a093b7fd426659fce4069973caa169e"
EQUALITY_SHA = "195b5fc78cb6895ee7797ebf1926f1cd19d990d992d5a9e9638d44f24aa984c6"
AUDIT_SHA = "17f92ce409b0ccdef54c4321eaec7ccb09206a4d2f3af61122051960b53df348"
AUDIT_REPORT = BASE + "rook-case4-face111-native-bounds-independent-replay.json"
AUDIT_REPORT_SHA = "5e1e01b8c5f3c5747292d65e6938263afe7a72bfff68b00ee29cf2f41b23b2a3"
PAIRS = [[259, 590], [259, 591], [259, 593], [259, 732]]
SECONDS = 60
rules = previous.rules


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def save(path, value):
    with path.open("x") as handle:
        json.dump(value, handle, indent=2, allow_nan=False)
        handle.write("\n")


def bindings():
    modules = [(previous, PREVIOUS_SHA), (equalities, EQUALITY_SHA), (audit, AUDIT_SHA)]
    for module, expected in modules:
        assert sha(Path(module.__file__).read_bytes()) == expected
    assert sha(Path(rules.__file__).read_bytes()) == previous.RULE_SHA
    return {"wrapper_sha256": sha(Path(__file__).read_bytes()),
            "previous_closure_wrapper_sha256": PREVIOUS_SHA,
            "unchanged_rule_and_reason_checker_sha256": previous.RULE_SHA,
            "two_equality_proof_source_sha256": EQUALITY_SHA,
            "independent_bound_checker_sha256": AUDIT_SHA,
            "independent_bound_report_sha256": AUDIT_REPORT_SHA}


def load(root):
    bound_sources = bindings()
    old_record, old_native, old_rows, raw, units, old_seed = previous.load(
        root, root / (BASE + "rook-case4-face99-parity-face-certificate.json"))
    data = {}
    for key, (name, expected) in audit.INPUTS.items():
        encoded = (root / name).read_bytes()
        assert sha(encoded) == expected
        data[key] = [json.loads(line) for line in encoded.splitlines()] if key == "certificates" else json.loads(encoded)
    equality = equalities.prove(root)
    assert canonical(equality) == canonical(data["equalities"])
    assert equality["proved_zero_columns"] == old_seed and len(old_seed) == 111
    assert equality["new_integer_cover_ranges"] == [[1, 1], [1, 1]]
    original, bound_rows, kept, index = audit.reconstruct(data["native"], equality, data["model"])
    checked = [audit.check_bound(p, bound_rows, kept, index, data["model"])[0]
               for p in data["certificates"]]
    refined, multipliers, residual = audit.check_bound(data["refined663"], bound_rows, kept, index, data["model"])
    identity = audit.short_identity(original, bound_rows, equality, kept, multipliers, residual)
    report_raw = (root / AUDIT_REPORT).read_bytes()
    assert sha(report_raw) == AUDIT_REPORT_SHA
    report = json.loads(report_raw)
    assert canonical(checked) == canonical(report["certificates"]) and canonical(refined) == canonical(report["refined_663"])
    assert identity == report["short_identity"]
    assert refined["original_columns"] == [663] and refined["upper_bound"] == "2/3"
    assert [v["original_columns"] for v in checked[1:]] == PAIRS
    assert all(v["upper_numerator"] < 2 * v["denominator"] for v in checked[1:])
    assert 663 not in old_seed

    # This exact comparison is the complete mathematical delta from v2.
    native = json.loads(json.dumps(old_native))
    assert len(native) == 2273
    assert native[:2271] == old_rows[:2271]
    assert [{k: r[k] for k in ("terms", "lower", "upper", "family")} for r in native[:2271]] == original
    for k in range(2):
        assert native[2271 + k]["terms"] == [[a, 1] for a in equality["original_cover_supports"][k]]
        assert native[2271 + k]["lower"] == 1
    assert [r["upper"] for r in native[2271:]] == [42, 1]
    native[2271]["upper"] = 1
    assert native[:2271] == old_native[:2271]
    for k, pair in enumerate(PAIRS):
        native.append(rules.row([[a, 1] for a in pair], 0, 1, "certified_native_bound_pair", k))
    assert len(native) == 2277
    seed = sorted(old_seed + [663])
    assert len(seed) == 112 and len(set(seed)) == 112
    axioms = [rules.row([[a, 1]], 0, 0, "proved_integer_zero", a) for a in seed]
    rows = native + axioms
    assert len(rows) == 2389
    record = {
        "source_bindings": bound_sources,
        "prior_source_bindings": old_record["source_bindings"],
        "proof_input_bindings": {k: {"path": p, "sha256": h} for k, (p, h) in audit.INPUTS.items()},
        "primary_inventory_sha256": previous.recovery.PRIMARY_SHA,
        "original_native_rows": 2271, "proved_parity_equalities": 2,
        "certified_pair_AMO_rows": PAIRS, "all_original_registered_covers": 178533,
        "all_original_rows_bytewise_unchanged_as_JSON": True,
        "prior_original_rows_sha256": old_record["original_integer_rows_sha256"],
        "complete_raw_registry_sha256": sha(raw),
        "native_and_added_rows_sha256": sha(canonical(native)),
        "augmented_integer_rows_sha256": sha(canonical(rows)),
        "native_and_added_row_count": 2277, "total_augmented_row_count": 2389,
        "verified_zero_axiom_columns": seed, "verified_zero_axiom_rows": 112,
        "old111_zero_columns": old_seed, "new_bound_zero_columns": [663],
        "integer_cover_ranges": [[1, 1], [1, 1]],
        "delta_from_previous_closure": {"H1_upper": [42, 1], "new_zero": 663, "new_pair_rows": PAIRS,
                                        "all_other_native_rows_unchanged": True, "registry_unchanged": True},
        "three_pair_rows_already_follow_from_Gram580": PAIRS[1:],
        "initial_cover_unit_ids": units,
        "initial_cover_unit_columns": old_record["initial_cover_unit_columns"],
        "requested_forward_seconds": SECONDS,
        "maximum_assignments": 1214, "maximum_records": 1215, "maximum_sweeps": 1215,
        "no_assumptions_or_probing": True, "optimizer_called": False,
        "short_663_equality_added_as_separate_row": False,
    }
    return record, native, rows, raw, units, seed


def delta_controls():
    checked = 0
    # The one new coordinate zero and guarded pair capacities are Boolean
    # consequences of the exact rational bounds, including strict <2.
    for a, b in product((0, 1), repeat=2):
        if 65536 * (a + b) <= 125548:
            assert a + b <= 1
        if 3 * a <= 2:
            assert a == 0
        pair_row = rules.row([[0, 1], [1, 1]], 0, 1, "pair", 0)
        total = sum(c * (a, b)[j] for j, c in pair_row["terms"])
        assert (pair_row["lower"] <= total <= pair_row["upper"]) == (not (a and b))
        checked += 1
    for values in product((0, 1), repeat=5):
        common, A, B, target, other = values
        H1, H2 = common + A, common + B
        strengthened = H1 == H2 == 1 and target == 0 and A + other <= 1
        original = 1 <= H1 <= 42 and H2 == 1
        if strengthened:
            assert original
        checked += 1
    return {"complete_tiny_delta_assignments": checked, "bound_rounding_and_pair_signs_checked": True,
            "old_rule_controls_reused": previous.earlier.controls()}


def prepare(root, output):
    record, *_ = load(root)
    record.update(status="PREPARED: complete 112-zero/two-equality/four-pair closure; no production propagation",
                  delta_controls=delta_controls(), production_propagation_run=False, case4_excluded=False)
    save(output, record)
    print(json.dumps({"status": record["status"], "sha256": sha(output.read_bytes()),
                      "source_sha256": bindings()["wrapper_sha256"]}, indent=2))


def checked(preparation, root):
    saved = json.loads(preparation.read_bytes())
    record, native, rows, raw, units, seed = load(root)
    for key, value in record.items():
        assert saved[key] == value, key
    assert not saved["production_propagation_run"] and not saved["case4_excluded"]
    return native, rows, raw, units, seed


def run(preparation, root, output):
    started = time.monotonic()
    native, rows, raw, units, seed = checked(preparation, root)
    before = time.monotonic()
    trace = rules.propagate(1214, rows, raw, units, SECONDS)
    forward_seconds = time.monotonic() - before
    before = time.monotonic()
    check = rules.verify_trace(1214, rows, raw, trace)
    scope = previous.earlier.real_scope(rows, raw, trace)
    scope["relative_to_augmented_integer_derived_premises_only"] = True
    complete = trace["complete"] and not check["contradiction"]
    if complete:
        assert set(seed) <= {a for a, v in enumerate(trace["values"]) if v == 0}
    dimensions = previous.earlier.dimensions(native, raw, trace["values"]) if complete else None
    result = {"status": trace["status"], "source_bindings": bindings(),
              "preparation_sha256": sha(preparation.read_bytes()), "trace": trace,
              "exact_reason_replay": check, "relative_real_scope": scope, "dimensions": dimensions,
              "new_zero_columns_beyond112": [a for a, v in enumerate(trace["values"]) if v == 0 and a not in set(seed)],
              "new_one_columns": [a for a, v in enumerate(trace["values"]) if v == 1],
              "forward_seconds": forward_seconds, "replay_and_inventory_seconds": time.monotonic() - before,
              "total_seconds": time.monotonic() - started, "optimizer_called": False,
              "failed_literal_probes": False, "case4_exclusion_verified_by_cold_replay": False,
              "whole_graph_problem_resolved": False}
    save(output, result)
    print(json.dumps({k: v for k, v in result.items() if k != "trace"}, indent=2))


def replay(preparation, root, result_path, output):
    started = time.monotonic()
    native, rows, raw, units, seed = checked(preparation, root)
    result = json.loads(result_path.read_bytes())
    assert result["source_bindings"] == bindings()
    assert result["preparation_sha256"] == sha(preparation.read_bytes())
    trace = result["trace"]
    assert len(trace["values"]) == 1214 and len(trace["records"]) <= 1215 and trace["sweeps"] <= 1215
    check = rules.verify_trace(1214, rows, raw, trace)
    assert check == result["exact_reason_replay"]
    scope = previous.earlier.real_scope(rows, raw, trace)
    scope["relative_to_augmented_integer_derived_premises_only"] = True
    assert scope == result["relative_real_scope"]
    complete = trace["complete"] and not check["contradiction"]
    if complete:
        assert set(seed) <= {a for a, v in enumerate(trace["values"]) if v == 0}
    dimensions = previous.earlier.dimensions(native, raw, trace["values"]) if complete else None
    assert dimensions == result["dimensions"]
    new_zeros = [a for a, v in enumerate(trace["values"]) if v == 0 and a not in set(seed)]
    new_ones = [a for a, v in enumerate(trace["values"]) if v == 1]
    assert new_zeros == result["new_zero_columns_beyond112"] and new_ones == result["new_one_columns"]
    report = {"status": "PASS: 112 proved zeros, both equalities, all four pair proofs and full sequential/fixed-point replay",
              "source_bindings": bindings(), "preparation_sha256": sha(preparation.read_bytes()),
              "result_sha256": sha(result_path.read_bytes()), "checked": check,
              "relative_real_scope": scope, "dimensions": dimensions,
              "new_zero_columns_beyond112": new_zeros, "new_one_columns": new_ones,
              "optimizer_called": False, "case4_exclusion_verified": check["contradiction"],
              "whole_graph_problem_resolved": False, "seconds": time.monotonic() - started}
    save(output, report)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "run", "replay"))
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--preparation", type=Path)
    parser.add_argument("--result", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.mode == "prepare":
        prepare(args.root, args.output)
    elif args.mode == "run":
        assert args.preparation is not None
        run(args.preparation, args.root, args.output)
    else:
        assert args.preparation is not None and args.result is not None
        replay(args.preparation, args.root, args.result, args.output)
