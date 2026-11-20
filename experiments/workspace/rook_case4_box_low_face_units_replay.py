"""Independent artifact-only replay of the H27 low-face x23 cut.

No subject imports, NumPy, original row-pool reconstruction, propagation,
optimizer, or prior trace-reason replay. A final box is authenticated by
its cold-checked original record's state hash, then inspected literally.
"""
import argparse
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import struct
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
B = "experiments/logs/grids-and-triangles/"
S = B + "rook-case4-box-low-face-scan01/"
F = B + "rook-case4-three-gram-full-rows-run01/"
C = B + "rook-case4-three-gram-full-rows-run01-cold/"
P = B + "rook-case4-full-span-cycle-run01/exact-01/"
INPUTS = {
    "source": ("experiments/workspace/rook_case4_box_low_face_units.py", "9b35c0f0bc655ba9248ae33fb3309c7bb7c965c92c744a591d0cbe92e595e05c"),
    "helper": ("experiments/workspace/rook_case4_box_hull_separator.py", "1a0cfb65dba5f7e68b7afcb3d494287309db9f8b1a1064585ca530688afc1b66"),
    "result": (S + "child/result.json", "d5d69b0155c9f60c90164ab7e6e7bc01268bbc706c448e70796727236c3a7c9d"),
    "boxes": (S + "child/box-inputs.json.gz", "29fbaf96aa14a89089136a30951f4f597f068ae0481ab1b1f87c297395ec4aab"),
    "owner": (S + "supervisor.json", "9ea224dd7139d3b8e437ec38e9bfb6f1a64ce51b9220c621bc8560d0d087d59f"),
    "forward": (F + "child-result.json", "5e6699c39de0ab165fa6396108ce8c11a9a9e4ca250ef557b7d3f16e7a1ac180"),
    "forward_owner": (F + "supervisor.json", "88e1fdee61b3edabd758cc76321cd4aafd468bb327989f49f360db0a868e609b"),
    "cold": (C + "child-result.json", "cda4f7a1b27b991827cd794c917a1a9ed9442e3b77bb6044f1d191f4f084399e"),
    "cold_owner": (C + "supervisor.json", "76f32ef2fb7c0d105eb49037ba3cc8522e78a47e4d39984c6107252b2c3723cd"),
    "scope": (B + "rook-case4-three-gram-branches-preparation01/preparation.json", "ad3f2b14fd4f60b0d411cd5d920ec461cffed3ab7a0ddf68861b9500cad95ba3"),
    "native": (B + "complement-rook-35core-case0004-native-cpsat-model.json", "a9004e97a2d166bf8b162609cfb538eae0dd4d26942b6df5119b6a88d65ec476"),
    "point": (P + "candidate.json", "819d0e909ecf7e357404eb063ba744bc8e4c0e38e0ee63848b1712b02b248b04"),
    "point_cold": (P + "cold.json", "cd59a3db0586c02a204fe8e3f23df4970b72416ff235319060a8fa1cb34e5bb8"),
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read(key):
    path, digest = INPUTS[key]
    raw = (ROOT / path).read_bytes()
    assert sha(raw) == digest, key
    if key in ("source", "helper"):
        return None
    return json.loads(gzip.decompress(raw) if path.endswith(".gz") else raw)


def read_ref(reference, expected):
    assert reference["path"] == expected
    raw = (ROOT / expected).read_bytes()
    assert len(raw) == reference["bytes"] and sha(raw) == reference["sha256"]
    return json.loads(raw)


def main(output):
    start = time.monotonic()
    d = {key: read(key) for key in INPUTS}
    result, spec, scope = d["result"], d["boxes"], d["scope"]
    for key in ("owner", "forward_owner", "cold_owner"):
        owner = d[key]
        assert owner["status"] == "CHILD_COMPLETE" and owner["exit_code"] == 0
        assert owner["child_reaped"] and not owner["hard_timeout"]
    assert d["owner"]["source_sha256"] == INPUTS["source"][1]
    assert d["owner"]["child/result.json"]["sha256"] == INPUTS["result"][1]
    assert d["owner"]["child/box-inputs.json.gz"]["sha256"] == INPUTS["boxes"][1]
    assert d["cold_owner"]["child_result"]["sha256"] == INPUTS["cold"][1]
    assert d["forward_owner"]["child_result"]["sha256"] == INPUTS["forward"][1]
    assert d["cold"]["status"] == "PASS" and d["cold"]["all260_nonpartial_branches_checked"]
    assert d["cold"]["all_saved_records_checked"] and d["cold"]["checked"] == 260
    assert d["cold"]["checked_partial"] == 0
    assert d["cold"]["prior184_contradictions_and_complete_original_branch_cover_bound"]
    assert d["cold"]["forward_owner"]["sha256"] == INPUTS["forward_owner"][1]
    assert d["forward_owner"]["records_preserved"] == d["forward"]["records"]
    assert d["cold_owner"]["replay_checks_preserved"] == d["cold"]["checks"]
    zeros = scope["identity"]["proved_zero_columns"]
    assert len(zeros) == len(set(zeros)) == 112 and spec["proved_zero_columns"] == zeros
    ids = sorted(set(range(1214)) - set(zeros))
    assert ids == spec["original_column_ids"] and len(ids) == 1102
    positions = {a: j for j, a in enumerate(ids)}
    coefficient = [0] * 1214
    rhs = 0
    for rid in (214, 344, 582):
        i, j, quota, members = d["native"]["primary_inventory"]["Gram_rows"][rid]
        assert type(quota) is int and len(members) == len(set(members))
        rhs += quota
        for a in members:
            coefficient[a] += 1
    assert rhs == 3 and coefficient == scope["identity"]["full1214_coefficients"]
    assert coefficient == result["identity"]["full1214_coefficients"]
    h = [a for a in ids if coefficient[a] % 2]
    q = [a for a in ids if coefficient[a] // 2]
    assert len(h) == 27 and len(q) == 10 and all(coefficient[a] // 2 == 1 for a in q)
    assert h == result["identity"]["H27_support"] and [[a, 1] for a in q] == result["identity"]["Q_terms"]
    positive = sorted(set(h) | set(q))
    boxes = {b["index"]: b for b in spec["boxes"]}
    assert len(boxes) == len(spec["boxes"]) == 191
    counts, low, high, states = Counter(), [], [], {}
    assert len(d["forward"]["records"]) == len(d["cold"]["checks"]) == 260
    for index in range(260):
        reference = d["forward"]["records"][index]
        record = read_ref(reference, F + f"branch-{index:03d}.json")
        check = read_ref(d["cold"]["checks"][index], C + f"check-{index:03d}.json")
        assert record["index"] == check["index"] == index and check["status"] == "PASS"
        assert record["prior_branch_id"] == check["prior_branch_id"]
        assert check["original_record"] == reference and check["forces"] == len(record["trace"])
        status = record["terminal"]["status"]
        assert status == check["terminal"]
        if status.startswith("contradiction"):
            assert index not in boxes
            counts["contradiction"] += 1
            continue
        assert status == "fixed_point" and index in boxes
        counts[status] += 1
        box, state = boxes[index], boxes[index]["state"]
        assert len(state) == 1102 and set(state) <= set("01?")
        raw = bytes(255 if x == "?" else int(x) for x in state)
        assert sha(raw) == box["state_sha256"] == record["final_state_sha256"]
        assert box["prior_branch_id"] == record["prior_branch_id"] and box["selected"] == record["selected"]
        assert all(state[positions[a]] != "?" for a in positive)
        selected = [a for a in positive if state[positions[a]] == "1"]
        assert selected == box["selected"] and sum(coefficient[a] for a in selected) == 3
        hv = sum(int(state[positions[a]]) for a in h)
        qv = sum(int(state[positions[a]]) for a in q)
        assert hv + 2 * qv == 3 and hv in (1, 3)
        (low if hv == 1 else high).append(index)
        states[index] = state
    assert counts == {"contradiction": 69, "fixed_point": 191}
    assert len(low) == 54 and len(high) == 137 and low == result["low_box_indices"] and high == result["high_box_indices"]
    common = {v: [a for a in ids if all(states[i][positions[a]] == str(v) for i in low)] for v in (0, 1)}
    assert common == {0: [23], 1: []}
    assert common[0] == result["common_low_zero_columns"] and common[1] == result["common_low_one_columns"]
    point, pc = d["point"], d["point_cold"]
    assert pc["status"] == "PASS: full exact selector point and positive t replayed" and pc["exact_point_replayed"]
    assert pc["candidate_sha256"] == INPUTS["point"][1]
    assert point["matrix_binding"]["original_column_ids"]["sha256"] == sha(struct.pack("<" + "H" * 1102, *ids))
    denominator = int(point["common_denominator"])
    numerators = list(map(int, point["exact_check"]["original1214_selector_numerators"]))
    assert denominator == 3461944222 and len(numerators) == 1214
    assert all(numerators[a] == 0 for a in zeros) and all(0 <= n <= denominator for n in numerators)
    assert [numerators[a] for a in ids] == list(map(int, point["extended_numerators"][:-1]))
    assert sum(coefficient[a] * numerators[a] for a in range(1214)) == 3 * denominator
    assert sum(numerators[a] for a in h) == sum(numerators[a] for a in q) == denominator
    signed = [int(a in h) - 2 * int(a == 23) for a in range(1214)]
    cap = [int(a in q) + int(a == 23) for a in range(1214)]
    assert all(signed[a] + 2 * cap[a] == coefficient[a] for a in ids)
    assert all(signed[a] == cap[a] == 0 for a in zeros)
    cap_support = [a for a, c in enumerate(cap) if c]
    assert cap_support == [23, 260, 399, 403, 406, 761, 762, 763, 764, 765, 803]
    bounds = []
    for index in sorted(states):
        state = states[index]
        lower = sum(signed[a] for a in ids if state[positions[a]] == "1" or (state[positions[a]] == "?" and signed[a] < 0))
        upper = sum(cap[a] for a in ids if state[positions[a]] in "1?")
        assert lower >= 1 and upper <= 1
        bounds.append({"index": index, "signed_minimum": lower, "capacity_maximum": upper})
    signed_value = sum(c * n for c, n in zip(signed, numerators))
    cap_value = sum(c * n for c, n in zip(cap, numerators))
    assert denominator - signed_value == 2 * (cap_value - denominator) == 75242928
    assert len(result["cuts"]) == result["violated_cuts"] == 1
    expected = [[a, c] for a, c in enumerate(signed) if c]
    assert result["cuts"][0]["terms"] == expected and result["cuts"][0]["lower"] == 1
    assert result["cuts"][0]["all191_box_minima"] == [b["signed_minimum"] for b in bounds]
    assert time.monotonic() - start < 30
    report = {"status": "PASS_INDEPENDENT_H27_LOW_FACE_CUT_AND_CAPACITY_EQUIVALENCE", "inputs": INPUTS,
              "source_sha256": sha(Path(__file__).read_bytes()), "all260_cold_record_bindings_checked": True,
              "conditional_zero_on_all54_low_boxes": 23, "high_boxes": 137, "common_low_ones": [],
              "signed_inequality": {"terms": expected, "lower": 1},
              "equivalent_capacity": {"terms": [[a, 1] for a in cap_support], "lower": 0, "upper": 1},
              "full1214_identity": {"original_Gram_rows": [214, 344, 582], "rhs": 3,
                                    "removed_zero_terms": [[a, coefficient[a]] for a in zeros if coefficient[a]],
                                    "form": "signed_row + 2*capacity_row + removed_zero_terms = three_Gram_sum"},
              "all191_box_bounds": bounds, "denominator": str(denominator),
              "signed_deficit_numerator": str(denominator - signed_value),
              "capacity_excess_numerator": str(cap_value - denominator),
              "case4_excluded": False, "global_x23_zero_claimed": False,
              "subject_imports": 0, "old_trace_reason_checks": 0, "large_matrix_rebuilds": 0, "optimizer_calls": 0,
              "seconds": time.monotonic() - start}
    with output.open("x") as stream:
        json.dump(report, stream, sort_keys=True, separators=(",", ":")); stream.write("\n")
    print(json.dumps({k: report[k] for k in ("status", "conditional_zero_on_all54_low_boxes", "high_boxes", "signed_deficit_numerator", "capacity_excess_numerator", "seconds")}, sort_keys=True))


if __name__ == "__main__":
    assert not sys.flags.optimize
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    main(parser.parse_args().output)
