"""Conditional-unit cuts from the H27=1 subfamily of 191 proved boxes.

This is an exact finite scan, not a new propagation or LP run. The previously
checked branch traces are bound and their assignments restored once. The
three original Gram rows are independently summed on all 1214 coordinates.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
BASE = "experiments/logs/grids-and-triangles/"
HELPER = ("experiments/workspace/rook_case4_box_hull_separator.py",
          "1a0cfb65dba5f7e68b7afcb3d494287309db9f8b1a1064585ca530688afc1b66")
INPUTS = {
    "scope": (BASE + "rook-case4-three-gram-branches-preparation01/preparation.json",
              "ad3f2b14fd4f60b0d411cd5d920ec461cffed3ab7a0ddf68861b9500cad95ba3"),
    "scope_cold": (BASE + "rook-case4-three-gram-branches-preparation01-replay.json",
                   "769a2536abf223d5b9f6aac27b50b0623f0976e955d153165e4c7b1fceac7e2c"),
    "native": (BASE + "complement-rook-35core-case0004-native-cpsat-model.json",
               "a9004e97a2d166bf8b162609cfb538eae0dd4d26942b6df5119b6a88d65ec476"),
    "cut": (BASE + "rook-case4-full-span-cycle-run01/separation-00/cut.json",
            "498058a2dbf5eab0e8460f7e46af29c5ce10ea42894d755ae846d0c24c2efa07"),
}
SECONDS = 30


def helper():
    path = ROOT / HELPER[0]
    assert hashlib.sha256(path.read_bytes()).hexdigest() == HELPER[1]
    spec = importlib.util.spec_from_file_location("frozen_191_box_inputs", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.ROOT == ROOT
    return module


def controls():
    inequalities = 0
    for h, x in itertools.product((1, 3), (0, 1)):
        if h != 1 or x == 0:
            assert h - 2 * x >= 1
            inequalities += 1
        if h != 1 or x == 1:
            assert h + 2 * x >= 3
            inequalities += 1
    # The low-face premise is necessary: neither conditional unit is global.
    assert 1 - 2 * 1 < 1 and 1 + 2 * 0 < 3
    vectors = 0
    for bits in itertools.product((0, 1), repeat=6):
        weights = (1, 1, 1, 2, 2, 3)
        if sum(c * v for c, v in zip(weights, bits)) != 3:
            continue
        h = sum(v for c, v in zip(weights, bits) if c % 2)
        q = sum((c // 2) * v for c, v in zip(weights, bits))
        assert h + 2 * q == 3 and h in (1, 3)
        vectors += 1
    return {"status": "PASS", "literal_conditional_inequalities": inequalities,
            "weighted_partition_vectors": vectors, "conditional_premise_counterexamples": 2,
            "optimizer_calls": 0}


def calculate():
    started = time.monotonic()
    m = helper()
    spec = m.recover_inputs()
    data = {}
    for key, (path, digest) in INPUTS.items():
        raw = (ROOT / path).read_bytes()
        assert m.sha(raw) == digest
        data[key] = json.loads(raw)
    scope, cold, native, old_cut = (data[k] for k in ("scope", "scope_cold", "native", "cut"))
    assert scope["status"] == "PREPARED_COMPLETE_WEIGHTED_BRANCH_COVER"
    assert cold["status"] == "PASS" and cold["preparation_sha256"] == INPUTS["scope"][1]
    assert cold["raw_patterns_checked"] == scope["raw_patterns"] == 2835
    assert scope["capacity_refuted_patterns"] == 2391 and scope["retained_patterns"] == 444
    assert scope["identity"]["proved_zero_columns"] == spec["proved_zero_columns"]
    assert scope["all_other_positive_support_coordinates_zero_in_each_branch"]
    zeros = set(spec["proved_zero_columns"])
    coefficients = [0] * 1214
    rhs, row_witnesses = 0, []
    for rid in (214, 344, 582):
        i, j, quota, members = native["primary_inventory"]["Gram_rows"][rid]
        assert type(quota) is int and quota >= 0 and len(set(members)) == len(members)
        assert all(type(a) is int and 0 <= a < 1214 for a in members)
        rhs += quota
        for a in members:
            coefficients[a] += 1
        row_witnesses.append({"native_Gram_row": rid, "core_pair": [i, j], "rhs": quota, "members": members})
    assert rhs == 3 and coefficients == scope["identity"]["full1214_coefficients"]
    assert coefficients == old_cut["full_original1214_integer_coefficients"]
    assert old_cut["original_Gram_row_ids"] == scope["identity"]["original_Gram_rows"] == [214, 344, 582]
    assert min(coefficients) >= 0 and max(coefficients) == 3
    h = [a for a, c in enumerate(coefficients) if a not in zeros and c % 2]
    q = [[a, c // 2] for a, c in enumerate(coefficients) if a not in zeros and c // 2]
    positive = [a for a, c in enumerate(coefficients) if a not in zeros and c]
    assert len(h) == 27 and len(q) == 10 and len(positive) == 36
    assert positive == scope["identity"]["positive_support"]
    expected_classes = {str(w): [a for a in positive if coefficients[a] == w] for w in (1, 2, 3)}
    assert expected_classes == scope["identity"]["weight_classes"]
    ids = spec["original_column_ids"]
    pos = {a: j for j, a in enumerate(ids)}
    classified, low, high = [], [], []
    for box in spec["boxes"]:
        state = box["state"]
        assert all(state[pos[a]] in "01" for a in positive)
        selected = [a for a in positive if state[pos[a]] == "1"]
        assert selected == box["selected"]
        assert sum(coefficients[a] for a in selected) == 3
        h_value = sum(int(state[pos[a]]) for a in h)
        q_value = sum(c * int(state[pos[a]]) for a, c in q)
        assert h_value + 2 * q_value == 3 and h_value in (1, 3)
        expected = 3 if box["kind"] == "three_weight1" else 1
        assert box["kind"] in ("three_weight1", "weight3_singleton", "weight1_weight2_pair") and h_value == expected
        classified.append({"index": box["index"], "prior_branch_id": box["prior_branch_id"],
                           "kind": box["kind"], "H27": h_value, "Q": q_value,
                           "state_sha256": box["state_sha256"]})
        (low if h_value == 1 else high).append(box)
    denominator = int(spec["point"]["denominator"])
    full = list(map(int, spec["point"]["original1214_numerators"]))
    assert sum(c * x for c, x in zip(coefficients, full)) == 3 * denominator
    assert sum(full[a] for a in h) == denominator
    assert sum(c * full[a] for a, c in q) == denominator
    common_zero = [a for a in ids if low and all(b["state"][pos[a]] == "0" for b in low)]
    common_one = [a for a in ids if low and all(b["state"][pos[a]] == "1" for b in low)]
    global_zero = [a for a in ids if all(b["state"][pos[a]] == "0" for b in spec["boxes"])]
    global_one = [a for a in ids if all(b["state"][pos[a]] == "1" for b in spec["boxes"])]
    assert not global_zero and not global_one
    cuts = []
    for value, common in ((0, common_zero), (1, common_one)):
        for a in common:
            c = [int(j in h) for j in ids]
            c[pos[a]] += 2 if value else -2
            lower = 3 if value else 1
            minima = [m.box_minimum(c, b["state"]) for b in spec["boxes"]]
            assert min(minima) >= lower
            point_value = sum(v * full[j] for v, j in zip(c, ids))
            deficit = lower * denominator - point_value
            assert deficit == 2 * (denominator - full[a] if value else full[a])
            cuts.append({"target_column": a, "conditional_value_on_H27_equal_one": value,
                         "terms": [[j, v] for j, v in zip(ids, c) if v], "lower": lower,
                         "all191_box_minima": minima, "minimum_over_boxes": min(minima),
                         "point_value_numerator": str(point_value), "deficit_numerator": str(deficit),
                         "violated_at_current_point": deficit > 0})
    assert time.monotonic() - started <= SECONDS
    result = {"status": "COMPLETE_H27_LOW_FACE_CONDITIONAL_UNIT_SCAN", "source_sha256": m.file_sha(Path(__file__)),
              "input_helper": HELPER, "inputs": INPUTS, "coverage": spec["coverage"],
              "identity": {"original_Gram_rows": row_witnesses, "full1214_coefficients": coefficients,
                           "rhs": 3, "proved_zero_columns": spec["proved_zero_columns"],
                           "removed_zero_terms": [[a, coefficients[a]] for a in sorted(zeros) if coefficients[a]],
                           "H27_support": h, "Q_terms": q, "identity_on_proved_face": "H27 + 2 Q = 3",
                           "binary_H27_values": [1, 3]},
              "classified_boxes": classified, "low_boxes": len(low), "high_boxes": len(high),
              "low_box_indices": [b["index"] for b in low], "high_box_indices": [b["index"] for b in high],
              "surviving_by_kind": dict(Counter(b["kind"] for b in spec["boxes"])),
              "H27_equal_one_has_surviving_boxes": bool(low),
              "common_low_zero_columns": common_zero, "common_low_one_columns": common_one,
              "no_global_unit_promoted": True, "cuts": cuts,
              "violated_cuts": sum(c["violated_at_current_point"] for c in cuts),
              "point": {"candidate_sha256": m.INPUTS["point"][1], "cold_sha256": m.INPUTS["point_cold"][1],
                        "denominator": str(denominator), "H27_numerator": str(denominator), "Q_numerator": str(denominator)},
              "controls": controls(), "large_matrix_loaded": False, "optimizer_calls": 0,
              "new_propagation_or_trace_reason_replay": False, "case4_excluded": False,
              "whole_graph_problem_resolved": False, "seconds": time.monotonic() - started}
    return m, spec, result


def main():
    assert not sys.flags.optimize
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", type=Path, required=True)
    args = parser.parse_args()
    args.directory.mkdir(parents=True, exist_ok=False)
    m, spec, result = calculate()
    m.write(args.directory / "box-inputs.json.gz", spec)
    result["box_inputs"] = m.ref(args.directory / "box-inputs.json.gz")
    m.write(args.directory / "result.json", result)
    print(json.dumps({k: result[k] for k in ("status", "low_boxes", "high_boxes", "surviving_by_kind", "common_low_zero_columns", "common_low_one_columns", "violated_cuts", "seconds")}, sort_keys=True))


if __name__ == "__main__":
    main()
