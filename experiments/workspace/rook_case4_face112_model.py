"""Complete case4 selector LP after 112 proved zeros and four pair bounds.

All original native rows and coordinate covers are reconstructed from the
frozen inputs. H1=H2=1 and the four certified pair capacities are explicit.
Only proved zeros and exact real unit-box tautologies are removed. This is
preparation/replay only; no optimizer or numerical support is used.
"""
import argparse
from array import array
from collections import Counter
import hashlib
from itertools import product
import json
from pathlib import Path
import resource
import signal
import sys
import time

import numpy as np

import rook_case4_face112_primary_closure_v3 as closure
import rook_case4_complete_lp_recovery as recovery

ROOT = Path(__file__).resolve().parents[2]
BASE = "experiments/logs/grids-and-triangles/"
CLOSURE_SHA = "405f732445043762db0c52cbc0cfdc159dcb945351925afdcc57af7c9606b3f9"
RECOVERY_SHA = "e577327c9cc2471f119c755a49a179b9f94f1004a22de80152a4114787a7eec6"
INPUTS = {
    "closure_preparation": (BASE + "rook-case4-face112-primary-closure-preparation03.json", "b005a338bd10a61769718afb0f6cab7c39b2f7b86bf46cee228a951398fd585c"),
    "closure_result": (BASE + "rook-case4-face112-primary-closure-run01.json", "4fad34cba7217bba4f9e985041adde5cf48435059ae29d494ebfdceeb8976fb9"),
    "closure_cold": (BASE + "rook-case4-face112-primary-closure-run01-replay.json", "69a38cff18f06a7b476e08cc3078925923865b744f9f46c59f23671d3d3c3d45"),
    "bound_audit": (BASE + "rook-case4-face111-native-bounds-independent-replay.json", "5e1e01b8c5f3c5747292d65e6938263afe7a72bfff68b00ee29cf2f41b23b2a3"),
    "previous_model": (BASE + "rook-case4-face99-parity-model01/model.json", "f2e73a9ea39927f3c42bec4648cffbbc2c98b2c2bfd1effd688a08d980d0b41a"),
    "previous_cold": (BASE + "rook-case4-face99-parity-model01-cold-replay.json", "fade3415a4d0b49fb7ae06eac9d8bfab99b26ef973bb851cae61460d32bb7e13"),
}
SELECTORS, ROWS, NONZEROS = 1102, 166010, 10767167
NATIVE_ROWS, NATIVE_NONZEROS, COVERS = 1960, 25654, 164044
NONPARITY_ROWS, NONPARITY_NONZEROS = 166004, 10767083
PARITY_ROWS, PAIR_ROWS = 2, 4
SECONDS, RSS_KIB = 180, 1048576
EXPECTED_COUNTS = {
    "tautological_Gram": 234, "retained_Gram": 396,
    "retained_original_signature": 184, "tautological_original_signature": 2,
    "retained_core_triple": 1320, "tautological_core_triple": 45,
    "retained_Gram_conflict": 2, "tautological_Gram_conflict": 28,
    "retained_uncapped_row_cut": 58, "tautological_uncapped_row_cut": 2,
    "retained_cover": 164044, "tautological_cover": 14489,
    "retained_integer_parity_cover": 2, "retained_certified_native_bound_pair": 4,
}


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def source_bindings():
    assert digest(Path(closure.__file__).read_bytes()) == CLOSURE_SHA
    assert digest(Path(recovery.__file__).read_bytes()) == RECOVERY_SHA
    return {"builder_sha256": digest(Path(__file__).read_bytes()),
            "complete_premise_loader_sha256": CLOSURE_SHA,
            "published_input_recovery_sha256": RECOVERY_SHA,
            "unchanged_rule_checker_sha256": closure.previous.RULE_SHA}


def checked_premises(root):
    binding = source_bindings()
    saved = {}
    for key, (name, expected) in INPUTS.items():
        raw = (root / name).read_bytes()
        assert digest(raw) == expected, key
        saved[key] = json.loads(raw)
    native, all_rows, raw, units, seed = closure.checked(root / INPUTS["closure_preparation"][0], root)
    # checked() rederives the original 111 zeros/equalities and all five
    # exact bounds. No production propagation or numerical call occurs.
    assert len(seed) == 112 and seed == sorted(set(seed)) and 663 in seed
    assert len(native) == 2277 and len(all_rows) == 2389
    assert native[:2271] == all_rows[:2271]
    assert [row["family"] for row in native[2271:]] == ["integer_parity_cover"] * 2 + ["certified_native_bound_pair"] * 4
    assert [[row["lower"], row["upper"]] for row in native[2271:]] == [[1, 1], [1, 1]] + [[0, 1]] * 4
    assert [[a for a, c in row["terms"]] for row in native[2273:]] == closure.PAIRS
    result, cold = saved["closure_result"], saved["closure_cold"]
    assert result["source_bindings"] == cold["source_bindings"] == closure.bindings()
    assert result["preparation_sha256"] == cold["preparation_sha256"] == INPUTS["closure_preparation"][1]
    assert cold["result_sha256"] == INPUTS["closure_result"][1]
    assert cold["status"].startswith("PASS:") and cold["checked"]["complete_fixed_point_rechecked"]
    assert not cold["checked"]["contradiction"]
    assert result["new_zero_columns_beyond112"] == cold["new_zero_columns_beyond112"] == []
    assert result["new_one_columns"] == cold["new_one_columns"] == []
    assert result["trace"]["values"] == [0 if a in set(seed) else -1 for a in range(1214)]
    assert result["dimensions"] == cold["dimensions"]
    assert cold["dimensions"]["fixed_zero_columns"] == seed
    assert cold["dimensions"]["complete_original_row_inventory"] == EXPECTED_COUNTS
    # The only fixed values are already rederived global premises; the saved
    # trace is not used to introduce any additional coordinate assumption.
    old = saved["previous_model"]
    assert (old["columns"], old["rows"], old["nonzeros"]) == (1115, 167937, 11012142)
    assert saved["previous_cold"]["model_sha256"] == INPUTS["previous_model"][1]
    assert saved["previous_cold"]["status"].startswith("PASS:")
    old_zeros = old["fixed_zero_columns"]
    assert len(old_zeros) == 99 and set(old_zeros) < set(seed)
    assert sorted(set(seed) - set(old_zeros)) == [663, 1062, 1063, 1064, 1065, 1066, 1067, 1125, 1126, 1127, 1128, 1129, 1130]
    assert saved["bound_audit"]["new_Boolean_zero"] == 663
    assert saved["bound_audit"]["pair_requiring_integer_rounding"] == [259, 590]
    assert saved["bound_audit"]["short_identity"]["identity_on_proved_face"] == "3*x_663 + sum_{a in S} x_a = 2"
    return binding, native, raw, seed, old, saved


def build(root):
    assert sys.byteorder == "little"
    binding, native, registry, zeros, old, saved = checked_premises(root)
    kept = [a for a in range(1214) if a not in set(zeros)]
    assert len(kept) == SELECTORS
    position = {a: j for j, a in enumerate(kept)}
    active = sum(1 << a for a in kept)
    coefficients, indices, pointers = array("q"), array("i"), array("q", [0])
    lower_bounds, upper_bounds = array("q"), array("q")
    kinds, identifiers = array("B"), array("i")
    counts, omitted_native, omitted_covers = Counter(), [], []
    stream = hashlib.sha256()
    maximum_coefficient = 0

    def append(kind, identifier, lower, upper, terms):
        nonlocal maximum_coefficient
        assert terms and terms == sorted(terms) and len({a for a, _ in terms}) == len(terms)
        assert all(0 <= a < SELECTORS and type(c) is int and c and -(1 << 63) < c < 1 << 63 for a, c in terms)
        assert -(1 << 63) <= lower <= upper < 1 << 63
        stream.update(recovery.HEADER.pack(kind, identifier, lower, upper, len(terms)))
        stream.update(b"".join(recovery.TERM.pack(a, c) for a, c in terms))
        coefficients.extend(c for _, c in terms)
        indices.extend(a for a, _ in terms)
        pointers.append(len(indices))
        lower_bounds.append(lower)
        upper_bounds.append(upper)
        kinds.append(kind)
        identifiers.append(identifier)
        maximum_coefficient = max(maximum_coefficient, max(abs(c) for _, c in terms))

    for identifier, row in enumerate(native[:2271]):
        terms, minimum, maximum, omitted = recovery.projected(row["terms"], row["lower"], row["upper"], position)
        if omitted:
            counts["tautological_" + row["family"]] += 1
            omitted_native.append({"original_row": identifier, "family": row["family"],
                                   "box_minimum": minimum, "box_maximum": maximum,
                                   "original_lower": row["lower"], "original_upper": row["upper"]})
        else:
            counts["retained_" + row["family"]] += 1
            append(0, identifier, row["lower"], row["upper"], terms)
    assert len(lower_bounds) == NATIVE_ROWS and len(indices) == NATIVE_NONZEROS
    for identifier in range(178533):
        target, bits = recovery.registry_entry(registry, identifier)
        if target not in position:
            counts["tautological_cover"] += 1
            omitted_covers.append([identifier, target])
            continue
        support = bits & active
        assert support and not (support >> target & 1)
        terms = sorted([[position[target], -1]] + [[position[a], 1] for a in recovery.members(support)])
        counts["retained_cover"] += 1
        append(1, identifier, 0, support.bit_count(), terms)
    assert len(lower_bounds) == NONPARITY_ROWS and len(indices) == NONPARITY_NONZEROS
    live_parity = []
    for identifier, row in enumerate(native[2271:2273]):
        terms, minimum, maximum, omitted = recovery.projected(row["terms"], row["lower"], row["upper"], position)
        assert not omitted and len(terms) == [35, 41][identifier]
        assert all(c == 1 for _, c in terms)
        live_parity.append([kept[a] for a, _ in terms])
        counts["retained_" + row["family"]] += 1
        append(2, identifier, 1, 1, terms)
    for identifier, row in enumerate(native[2273:]):
        terms, minimum, maximum, omitted = recovery.projected(row["terms"], row["lower"], row["upper"], position)
        assert not omitted and len(terms) == 2 and all(c == 1 for _, c in terms)
        assert [kept[a] for a, _ in terms] == closure.PAIRS[identifier]
        counts["retained_" + row["family"]] += 1
        append(3, identifier, 0, 1, terms)
    assert dict(counts) == EXPECTED_COUNTS
    assert len(lower_bounds) == ROWS and len(coefficients) == len(indices) == NONZEROS
    assert len(pointers) == ROWS + 1
    assert len(omitted_native) == 311 and len(omitted_covers) == 14489

    old_kept = [a for a in range(1214) if a not in set(old["fixed_zero_columns"])]
    old_column_to_new = [position.get(a, -1) for a in old_kept]
    assert len(old_kept) == 1115 and old_column_to_new.count(-1) == 13
    old_omitted_native = {r["original_row"] for r in old["omitted_native_rows_exact_box_witnesses"]}
    old_omitted_covers = {r[0] for r in old["omitted_covers_fixed_zero_target_witnesses"]}
    old_origins = ([(0, i) for i in range(2271) if i not in old_omitted_native]
                   + [(1, i) for i in range(178533) if i not in old_omitted_covers] + [(2, 0), (2, 1)])
    assert len(old_origins) == 167937
    old_by_origin = {origin: i for i, origin in enumerate(old_origins)}
    new_origins = list(zip(kinds, identifiers))
    new_by_origin = {origin: i for i, origin in enumerate(new_origins)}
    assert len(new_by_origin) == ROWS
    assert set(new_by_origin) - set(old_by_origin) == {(3, i) for i in range(4)}
    old_row_to_new = [new_by_origin.get(origin, -1) for origin in old_origins]
    new_row_to_old = [old_by_origin.get(origin, -1) for origin in new_origins]
    assert old_row_to_new.count(-1) == 1931 and new_row_to_old[-4:] == [-1] * 4
    assert all(old_row_to_new[old_id] == new_id for new_id, old_id in enumerate(new_row_to_old) if old_id >= 0)
    arrays = {
        "coefficients": np.frombuffer(coefficients, dtype="<i8"),
        "column_indices": np.frombuffer(indices, dtype="<i4"),
        "row_pointers": np.frombuffer(pointers, dtype="<i8"),
        "row_lower": np.frombuffer(lower_bounds, dtype="<i8"),
        "row_upper": np.frombuffer(upper_bounds, dtype="<i8"),
        "row_origin_kind": np.frombuffer(kinds, dtype="u1"),
        "row_origin_index": np.frombuffer(identifiers, dtype="<i4"),
        "original_column_ids": np.asarray(kept, dtype="<u2"),
        "previous_column_to_current": np.asarray(old_column_to_new, dtype="<i4"),
        "previous_row_to_current": np.asarray(old_row_to_new, dtype="<i4"),
        "current_row_to_previous": np.asarray(new_row_to_old, dtype="<i4"),
    }
    record = {
        "status": "complete112-zero-face LP with both unit sums and four pair capacities; no optimizer",
        "source_bindings": binding, "input_bindings": {k: list(v) for k, v in INPUTS.items()},
        "proof_input_bindings": saved["closure_preparation"]["proof_input_bindings"],
        "primary_inventory_sha256": recovery.PRIMARY_SHA,
        "complete_cover_registry_sha256": digest(registry),
        "fixed_zero_columns": zeros, "fixed_one_columns": [],
        "prior99_zero_columns": old["fixed_zero_columns"],
        "new13_zero_columns": sorted(set(zeros) - set(old["fixed_zero_columns"])),
        "zero663_uses_nonnegative_integrality": True,
        "case_index": 4, "original_columns": 1214,
        "columns": SELECTORS, "rows": ROWS, "nonzeros": NONZEROS,
        "retained_original_primary_rows": NATIVE_ROWS, "retained_native_nonzeros": NATIVE_NONZEROS,
        "retained_coordinate_covers": COVERS,
        "added_integer_covers": 2, "added_integer_cover_nonzeros": 76,
        "added_integer_cover_row_ids": [NONPARITY_ROWS, NONPARITY_ROWS + 1],
        "integer_cover_live_original_supports": live_parity, "integer_cover_ranges": [[1, 1], [1, 1]],
        "added_pair_rows": closure.PAIRS, "added_pair_row_ids": list(range(ROWS - 4, ROWS)),
        "three_pair_rows_already_implied_by_original_Gram580": closure.PAIRS[1:],
        "pair_requiring_integer_rounding": [259, 590],
        "short86_sum_two_added_as_a_row": False,
        "parent_real_feasible_set_preservation_claimed": False,
        "scope": "Every actual case4 incidence satisfies this real necessary system. Only the proved112 zeros and exact box tautologies are removed; both integer unit sums and all four certified pairs remain.",
        "all2271_native_rows_and178533_covers_covered": True,
        "all60_uncapped_exterior_row_cuts_accounted_for": True,
        "row_inventory": dict(counts),
        "omitted_native_rows_exact_box_witnesses": omitted_native,
        "omitted_covers_fixed_zero_target_witnesses": omitted_covers,
        "cover_upper_endpoints_are_unit_box_tautologies": True,
        "previous_model_rows": 167937, "previous_model_columns": 1115,
        "previous_rows_omitted_by_exact_zero_substitution": 1931,
        "new_rows_without_previous_origin": 4,
        "column_transport_removed_original_ids": [a for a, j in zip(old_kept, old_column_to_new) if j < 0],
        "row_and_column_transports_saved_in_arrays": True,
        "canonical_integer_stream_format": "<BIqqI header(kind,original_id,lower,upper,nterms), then <Iq(reduced_column,coefficient); kind0 native, kind1 coordinate cover, kind2 integer cover, kind3 certified pair",
        "canonical_integer_stream_sha256": stream.hexdigest(),
        "maximum_absolute_integer_coefficient": maximum_coefficient,
        "finite_variable_bounds": {"lower": 0, "upper": 1}, "row_bounds_are_finite_integers": True,
        "array_sha256": {name: digest(value.tobytes(order="C")) for name, value in arrays.items()},
        "uncompressed_array_bytes": sum(value.nbytes for value in arrays.values()),
        "numpy_version": np.__version__, "python_version": sys.version,
        "optimizer_or_solver_called": False, "integer_incidence_or_graph_constructed": False, "case4_excluded": False,
    }
    assert record["column_transport_removed_original_ids"] == record["new13_zero_columns"]
    return record, arrays


def controls():
    checks = 0
    for values in product((0, 1), repeat=3):
        terms = [[0, -2], [1, 3], [2, 1]]
        if values[1] == 0:
            kept = {0: 0, 2: 1}
            reduced, lo, hi, omitted = recovery.projected(terms, -2, 1, kept)
            assert sum(c * values[a] for a, c in terms) == sum(c * (values[0], values[2])[j] for j, c in reduced)
            assert (lo, hi, omitted) == (-2, 1, True)
            checks += 1
    return {"zero_substitution_controls": checks, "inherited_integer_row_controls": recovery.controls()}


def load(model_path, arrays_path=None):
    model = json.loads(model_path.read_bytes())
    assert model["source_bindings"] == source_bindings()
    assert model["input_bindings"] == {k: list(v) for k, v in INPUTS.items()}
    assert (model["columns"], model["rows"], model["nonzeros"]) == (SELECTORS, ROWS, NONZEROS)
    assert model["row_inventory"] == EXPECTED_COUNTS
    assert model["integer_cover_ranges"] == [[1, 1], [1, 1]] and model["added_pair_rows"] == closure.PAIRS
    assert len(model["fixed_zero_columns"]) == 112 and not model["fixed_one_columns"]
    arrays_path = arrays_path or model_path.parent / model["arrays"]["path"]
    assert digest(arrays_path.read_bytes()) == model["arrays"]["sha256"]
    with np.load(arrays_path, allow_pickle=False) as archive:
        arrays = {name: archive[name] for name in archive.files}
    assert {name: digest(value.tobytes(order="C")) for name, value in arrays.items()} == model["array_sha256"]
    assert all(value.dtype.kind in "iu" for value in arrays.values())
    kept = list(map(int, arrays["original_column_ids"]))
    assert kept == [a for a in range(1214) if a not in set(model["fixed_zero_columns"])]
    assert len(arrays["coefficients"]) == len(arrays["column_indices"]) == NONZEROS
    assert len(arrays["row_pointers"]) == ROWS + 1 and arrays["row_pointers"][0] == 0 and arrays["row_pointers"][-1] == NONZEROS
    assert all(len(arrays[name]) == ROWS for name in ("row_lower", "row_upper", "row_origin_kind", "row_origin_index"))
    assert np.all(arrays["row_origin_kind"][:NATIVE_ROWS] == 0)
    assert np.all(arrays["row_origin_kind"][NATIVE_ROWS:NONPARITY_ROWS] == 1)
    assert list(map(int, arrays["row_origin_kind"][NONPARITY_ROWS:])) == [2, 2, 3, 3, 3, 3]
    for i, support in enumerate(model["integer_cover_live_original_supports"] + model["added_pair_rows"]):
        r = NONPARITY_ROWS + i
        a, b = map(int, arrays["row_pointers"][r:r + 2])
        assert b - a == [35, 41, 2, 2, 2, 2][i] and np.all(arrays["coefficients"][a:b] == 1)
        assert [kept[j] for j in arrays["column_indices"][a:b]] == support
        assert [int(arrays["row_lower"][r]), int(arrays["row_upper"][r])] == ([1, 1] if i < 2 else [0, 1])
    assert len(arrays["previous_column_to_current"]) == 1115
    assert len(arrays["previous_row_to_current"]) == 167937 and len(arrays["current_row_to_previous"]) == ROWS
    assert np.count_nonzero(arrays["previous_column_to_current"] < 0) == 13
    assert np.count_nonzero(arrays["previous_row_to_current"] < 0) == 1931
    assert np.array_equal(arrays["current_row_to_previous"][-4:], [-1] * 4)
    assert np.array_equal(arrays["previous_row_to_current"][arrays["current_row_to_previous"][:-4]], np.arange(ROWS - 4))
    return model, arrays


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "replay"))
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--directory", type=Path)
    parser.add_argument("--model", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    started = time.monotonic()

    def deadline(_signum, _frame):
        raise TimeoutError("bounded180second exact112-face preparation/replay")

    previous_handler = signal.signal(signal.SIGALRM, deadline)
    signal.setitimer(signal.ITIMER_REAL, SECONDS)
    try:
        if args.mode == "prepare":
            assert args.directory is not None and not args.directory.exists()
            args.directory.mkdir(parents=True)
            tested = controls()
            record, arrays = build(args.root.resolve())
            path = args.directory / "arrays.npz"
            with (args.directory / "arrays.npz.partial").open("wb") as stream:
                np.savez_compressed(stream, **arrays)
            (args.directory / "arrays.npz.partial").rename(path)
            record["arrays"] = {"path": "arrays.npz", "sha256": digest(path.read_bytes()), "bytes": path.stat().st_size}
            record["controls"] = tested
            record["preparation_seconds"] = time.monotonic() - started
            record["peak_rss_kib"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            assert record["peak_rss_kib"] <= RSS_KIB
            model_path = args.directory / "model.json"
            recovery.write_json(model_path, record)
            loaded, stored = load(model_path, path)
            for name, value in arrays.items():
                assert np.array_equal(value, stored[name])
            output = args.directory / "preparation.json"
            status = "PASS: full112-zero face, both parity equalities, four pair capacities and exact transports prepared"
        else:
            assert args.model is not None and args.output is not None
            model_path = args.model
            saved, stored = load(model_path)
            record, arrays = build(args.root.resolve())
            for key, value in record.items():
                if key not in ("numpy_version", "python_version"):
                    assert saved[key] == value, ("cold model field", key)
            assert set(stored) == set(arrays)
            for name, value in arrays.items():
                assert np.array_equal(stored[name], value), ("cold112-face array", name)
            output = args.output
            record["arrays"] = saved["arrays"]
            status = "PASS: all original rows/covers and112-zero/two-equality/four-pair proofs cold rebuilt"
        report = {"status": status, "source_bindings": source_bindings(),
                  "model_sha256": digest(model_path.read_bytes()),
                  "columns": SELECTORS, "rows": ROWS, "nonzeros": NONZEROS,
                  "canonical_integer_stream_sha256": record["canonical_integer_stream_sha256"],
                  "row_inventory": record["row_inventory"], "integer_cover_ranges": [[1, 1], [1, 1]],
                  "added_pair_rows": closure.PAIRS, "all_omission_witnesses_replayed": True,
                  "all_row_column_transports_checked": True, "arrays": record["arrays"],
                  "seconds": time.monotonic() - started,
                  "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                  "optimizer_or_solver_called": False, "case4_excluded": False}
        assert report["peak_rss_kib"] <= RSS_KIB
        recovery.write_json(output, report)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous_handler)
    print(json.dumps(report, indent=2), flush=True)


if __name__ == "__main__":
    main()
