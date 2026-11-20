#!/usr/bin/env python3
"""Scan the exact x521-zero integer count witness with two frozen families.

Only exact integer-to-float conversions are used for the scanners' input
interface. Every accepted integer vector is replayed exactly. No LP is
called, no count witness is repaired, and no passing block is asserted
PSD without a separate exact certificate.
"""

from __future__ import annotations

import argparse
import gc
import json
from pathlib import Path
import resource
import time

from threadpoolctl import threadpool_limits

import root_prism_free_x521_face as face
import grid_free_order10_moments as old
import grid_free_order10_r8s1_scan as new


ROOT = Path(__file__).resolve().parents[2]
COUNTS = face.COUNTS
PREFIX = ROOT / "experiments/logs/moments-and-counts/prism-zero-order10-x521-integer-moments"
FACE_SHA = "cc89194289b24882bf22f7a5945516fa57897c9d2607e527d94100ab5e9d57dd"
WITNESS = ROOT / "experiments/logs/moments-and-counts/prism-zero-order10-x521-face-rounded-counts.json"
WITNESS_SHA = "ee8e22f070e0529be5be8bf14c853c6ad9ed97127570223abf6e1529ab8857f9"
FACE_REPLAY = ROOT / "experiments/logs/moments-and-counts/prism-zero-order10-x521-face-full-replay.log"
FACE_REPLAY_SHA = "dea8da85b270fdbb9f5361a108ffd23a35d56c0dfcb6e2bad9d1a60474438ebb"
OLD_SHA = "4c6886bd8d5dffa711aa20991af3bb87495262bd01d8227d2f64caac0040bbae"
NEW_SHA = "71f06ef752adff6d49f88136b9e82f054f6485a2b2867c2cd4ef9f7ef7f82887"
OLD_REFERENCE = ROOT / "experiments/logs/moments-and-counts/prism-zero-order10-ipm-zero-closure-round0-old-separation.json"
OLD_REFERENCE_SHA = "ab00d7993524d1c8768f2b25c0a850fe6adb54d370fcfea827871614abbe6bba"


def output(suffix):
    return PREFIX.with_name(PREFIX.name + "-" + suffix)


def bindings():
    assert COUNTS.digest(Path(face.__file__)) == FACE_SHA
    assert COUNTS.digest(Path(old.__file__)) == OLD_SHA
    assert COUNTS.digest(Path(new.__file__)) == NEW_SHA
    assert COUNTS.digest(WITNESS) == WITNESS_SHA
    assert COUNTS.digest(FACE_REPLAY) == FACE_REPLAY_SHA
    assert COUNTS.digest(OLD_REFERENCE) == OLD_REFERENCE_SHA
    reference = json.loads(OLD_REFERENCE.read_text())
    assert reference["source_sha256"] == OLD_SHA
    assert reference["blocks_examined"] == 1416
    cache_hashes = {record["file"]: record["sha256"] for record in reference["caches"]}
    assert len(cache_hashes) == 12
    assert {path.name for path, _ in old.cache_files()} == set(cache_hashes)
    for path, _ in old.cache_files():
        assert COUNTS.digest(path) == cache_hashes[path.name]
    forms_path = Path(old.__file__).with_name("moments-order9.pickle")
    assert COUNTS.digest(forms_path) == reference["order_nine_cache_sha256"]
    return {"face_source_sha256": FACE_SHA, "witness_path": face.relative(WITNESS),
            "witness_sha256": WITNESS_SHA, "full_face_replay_sha256": FACE_REPLAY_SHA,
            "old_scanner_sha256": OLD_SHA, "new_scanner_sha256": NEW_SHA,
            "old_cache_hashes": cache_hashes,
            "old_forms_sha256": reference["order_nine_cache_sha256"],
            "new_full_cache_sha256": new.CACHE_SHA,
            "new_construction_source_sha256": new.CONSTRUCTION_SHA}


def input_proposal(witness, active):
    point = witness["rounded_core_values"]
    assert len(point) == 550 and all(type(value) is int for value in point)
    assert point[0] == 1 and point[1] == point[56] == point[57] == point[521] == 0
    assert active == [j for j in range(1, 550) if j not in (56, 57)]
    assert witness["exact_count_and_25_cut_witness"]
    assert witness["original_equations_checked"] == 180445
    assert len(witness["induced_counts"]) == 48965
    assert witness["negative_induced_rows"] == witness["nonintegral_induced_rows"] == 0
    assert not witness["first_original_equation_violations"]
    assert not witness["bad_level_totals"] and not witness["bad_zero_types"]
    assert witness["negative_held_cuts"] == 0 and witness["required_zeros_hold"]
    assert len(witness["required_zero_coordinates"]) == 59
    for value in point:
        assert 0 <= value < 2 ** 53
        assert float(value).as_integer_ratio() == (value, 1)
    return {"status": "verified integer count witness represented exactly as scanner floats",
            "source_sha256": COUNTS.digest(Path(__file__)),
            "witness_path": face.relative(WITNESS), "witness_sha256": WITNESS_SHA,
            "case_index": 1, "fixed_order_nine_point": False,
            "x521_zero_face": True, "numerical_precursor_used": False,
            "exact_integer_conversion": {"coordinates_checked": 550,
                                         "strict_upper_bound": 2 ** 53,
                                         "maximum_value": max(point),
                                         "all_as_integer_ratio_equal_integer_over_one": True},
            "real_proposal": {"active_coordinates": active,
                              "ordinary_core_values": [float(point[j]) for j in active],
                              "exact_real_feasibility_certified": True,
                              "scope": "count equations, bounds, 59 zeros and 25 retained cuts only"},
            "PSD_feasibility_certified": False, "graph_constructed": False}


def exact_input_controls(proposal, point):
    _, numerator, denominator = old.point_from_proposal(proposal)
    assert numerator == point[:58] and denominator == 1
    _, numerator, denominator = new.exact_point(proposal)
    assert numerator == point and denominator == 1
    return {"old_prefix_exactly_matches_58_integer_coordinates": True,
            "new_family_exactly_matches_all_550_integer_coordinates": True,
            "both_exact_point_denominators": 1,
            "numerical_precursor_used": False}


def combined_cuts(older, newer, point, held):
    rows, index = [], {}
    existing = {tuple(cut["coefficients"]) for cut in held}
    for family, records in (("old1416", older["unique_integer_cuts"]),
                            ("complete-r8s1", newer["unique_core_cuts"])):
        for number, record in enumerate(records):
            coefficients = record["coefficients"]
            if family == "old1416":
                assert len(coefficients) == 58
                coefficients = coefficients + [0] * 492
            assert len(coefficients) == 550 and all(type(c) is int for c in coefficients)
            value = sum(a * x for a, x in zip(coefficients, point))
            assert value < 0 and record["exact_value_at_proposal"] == [value, 1]
            key = tuple(coefficients)
            assert key not in existing, "a proved satisfied seed cannot be negative at this exact point"
            if key not in index:
                index[key] = len(rows)
                rows.append({"coefficients": coefficients, "exact_integer_value_at_witness": value,
                             "origins": []})
            rows[index[key]]["origins"].append({"family": family, "cut_index": number})
    return rows


def scan(rebuild=False):
    started = time.monotonic()
    target = output("result.json")
    assert not target.exists(), "refusing to overwrite an existing moment scan"
    bound = bindings()
    prepared, bundle = face.load_prepared(face.DEFAULT_PREPARATION, rebuild=rebuild)
    witness = json.loads(WITNESS.read_text())
    assert witness["source_sha256"] == FACE_SHA
    assert witness["preparation_sha256"] == COUNTS.digest(face.DEFAULT_PREPARATION)
    assert witness["numerical_model_sha256"] == prepared["model"]["numerical_model_sha256"]
    point = witness["rounded_core_values"]
    proposal = output("input.json")
    COUNTS.save(proposal, input_proposal(witness, bundle["metadata"]["active_core_coordinates"]))
    controls = exact_input_controls(proposal, point)
    record = {"status": "running two moment scans on the exact x521-zero integer witness",
              "source_sha256": COUNTS.digest(Path(__file__)), "bindings": bound,
              "proposal_path": face.relative(proposal), "proposal_sha256": COUNTS.digest(proposal),
              "exact_input_controls": controls, "LP_called": False,
              "PSD_feasibility_certified": False, "graph_constructed": False,
              "input_count_witness_modified": False}
    COUNTS.save(target, record)
    older_path = output("old1416.json")
    older = old.scan(proposal, older_path)
    assert older["blocks_examined"] == 1416
    old_replay = old.replay(older_path)
    COUNTS.save(output("old1416-replay.json"), old_replay)
    record["old_family"] = {"certificate_path": face.relative(older_path),
                            "certificate_sha256": COUNTS.digest(older_path),
                            "blocks_scanned": older["blocks_examined"],
                            "exact_negative_blocks": older["exact_negative_block_count"],
                            "unique_integer_cuts": older["unique_integer_cut_count"],
                            "unconfirmed_numeric_negatives": older["numerical_negatives_without_exact_cut"],
                            "exact_replay": old_replay, "seconds": older["seconds"]}
    COUNTS.save(target, record)
    gc.collect()
    parent_saved = face.read_parent()
    scanner = new.FullScanner(bundle["data"], bundle["raw"], bundle["scale"],
                              Path(parent_saved["inputs"]["full_cache"]),
                              bundle["metadata"]["reduced_cache_sha256"])
    assert scanner.count_numerators(point) == witness["induced_counts"]
    newer_path = output("r8s1.json")
    newer = scanner.scan(proposal, newer_path, seconds=180)
    assert newer["point_numerators"] == point and newer["point_denominator"] == 1
    assert newer["negative_exact_induced_forms"] == 0
    new_replay = scanner.replay(newer_path)
    COUNTS.save(output("r8s1-replay.json"), new_replay)
    record["new_family"] = {"certificate_path": face.relative(newer_path),
                            "certificate_sha256": COUNTS.digest(newer_path),
                            "blocks_scanned": newer["blocks_scanned"],
                            "complete_scan": newer["complete_scan"], "timed_out": newer["timed_out"],
                            "exact_negative_blocks": newer["exact_negative_block_count"],
                            "unique_integer_cuts": newer["unique_integer_cut_count"],
                            "unconfirmed_numeric_negatives": newer["unconfirmed_numeric_negatives"],
                            "exact_zero_rows_removed": newer["exact_zero_rows_removed"],
                            "exact_replay": new_replay, "seconds": newer["seconds"]}
    cuts = combined_cuts(older, newer, point, bundle["seed"])
    record.update(unique_fresh_core_cuts=cuts, unique_fresh_core_cut_count=len(cuts),
                  all_accepted_integer_vectors_replayed=True,
                  all_48965_integer_counts_reproduced=True,
                  no_model_constraints_added=True,
                  seconds=time.monotonic() - started,
                  peak_process_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    if cuts:
        record["status"] = "exact integer moment violations found and replayed"
    elif newer["complete_scan"]:
        record["status"] = "no exact violation in either complete scan; PSD not certified"
    else:
        record["status"] = "bounded new-family scan incomplete; no PSD conclusion"
    COUNTS.save(target, record)
    print(json.dumps({k: record[k] for k in ("status", "unique_fresh_core_cut_count",
                      "all_accepted_integer_vectors_replayed", "seconds", "peak_process_rss_kib")}, indent=2), flush=True)
    return record


def replay(rebuild=False):
    saved = json.loads(output("result.json").read_text())
    assert saved["source_sha256"] == COUNTS.digest(Path(__file__))
    assert saved["bindings"] == bindings()
    _, bundle = face.load_prepared(face.DEFAULT_PREPARATION, rebuild=rebuild)
    witness = json.loads(WITNESS.read_text())
    point = witness["rounded_core_values"]
    proposal = ROOT / saved["proposal_path"]
    assert COUNTS.digest(proposal) == saved["proposal_sha256"]
    assert json.loads(proposal.read_text()) == input_proposal(witness, bundle["metadata"]["active_core_coordinates"])
    assert exact_input_controls(proposal, point) == saved["exact_input_controls"]
    older_path = ROOT / saved["old_family"]["certificate_path"]
    assert COUNTS.digest(older_path) == saved["old_family"]["certificate_sha256"]
    assert old.replay(older_path) == saved["old_family"]["exact_replay"]
    parent_saved = face.read_parent()
    scanner = new.FullScanner(bundle["data"], bundle["raw"], bundle["scale"],
                              Path(parent_saved["inputs"]["full_cache"]),
                              bundle["metadata"]["reduced_cache_sha256"])
    assert scanner.count_numerators(point) == witness["induced_counts"]
    newer_path = ROOT / saved["new_family"]["certificate_path"]
    assert COUNTS.digest(newer_path) == saved["new_family"]["certificate_sha256"]
    assert scanner.replay(newer_path) == saved["new_family"]["exact_replay"]
    older, newer = json.loads(older_path.read_text()), json.loads(newer_path.read_text())
    cuts = combined_cuts(older, newer, point, bundle["seed"])
    assert cuts == saved["unique_fresh_core_cuts"] and len(cuts) == saved["unique_fresh_core_cut_count"]
    result = {"status": "exact integer-witness two-family moment replay PASS",
              "source_sha256": COUNTS.digest(Path(__file__)), "witness_sha256": WITNESS_SHA,
              "old_negative_blocks": older["exact_negative_block_count"],
              "new_negative_blocks": newer["exact_negative_block_count"],
              "unique_fresh_core_cuts": len(cuts), "LP_called": False,
              "numerical_eigensystems_recomputed": False, "PSD_feasibility_certified": False}
    print(json.dumps(result, indent=2), flush=True)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("scan", "replay"))
    parser.add_argument("--rebuild", action="store_true")
    args = parser.parse_args()
    with threadpool_limits(limits=1):
        scan(args.rebuild) if args.command == "scan" else replay(args.rebuild)


if __name__ == "__main__":
    main()
