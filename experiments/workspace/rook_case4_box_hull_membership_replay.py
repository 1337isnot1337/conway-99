"""Independent arithmetic replay of a box mixture or a signed separator.

No producer import, numerical model, optimizer, basis solve, branch trace, or
clique enumeration is used.  The complete box-cover ancestry and the already
accepted real point are bound before checking the proposed certificate.
"""

import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path
import struct
import time


ROOT = Path(__file__).resolve().parents[2]
EXPECTED = {
    "boxes": "29fbaf96aa14a89089136a30951f4f597f068ae0481ab1b1f87c297395ec4aab",
    "box_replay": "69fb21a3589bed904b859f1a8272aa26116ad7ab59931a4513ab16ffa60d91b0",
    "box_replay_owner": "b4698735b836178796a30c8594e5ee8145e280bcbe39b635b7d0fb750cac34fa",
    "full_cold": "cda4f7a1b27b991827cd794c917a1a9ed9442e3b77bb6044f1d191f4f084399e",
    "full_cold_owner": "76f32ef2fb7c0d105eb49037ba3cc8522e78a47e4d39984c6107252b2c3723cd",
    "point": "7fda72c6a212a6ebe504c03a17f66c05c8545d33e4aebc651f42f817cc3a4bd9",
    "point_cold": "b69a3a38aeb911c45657871544f21897bc4f9bb6201675c1eab5f45ca8a5c317",
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def reference(path):
    raw = path.read_bytes()
    return {"path": str(path.resolve().relative_to(ROOT)), "sha256": sha(raw), "bytes": len(raw)}


def integer(value):
    assert type(value) in (int, str)
    if type(value) is str:
        assert value == str(int(value))
    return int(value)


def bound(binding):
    name, digest = binding
    path = (ROOT / name).resolve()
    assert path.is_relative_to(ROOT)
    raw = path.read_bytes()
    assert len(raw) <= 16 * 1024 * 1024 and sha(raw) == digest
    raw = gzip.decompress(raw) if name.endswith(".gz") else raw
    assert len(raw) <= 16 * 1024 * 1024
    return json.loads(raw)


def replay(configuration, certificate):
    started = time.monotonic()
    config = json.loads(configuration.read_bytes())
    cert = json.loads(certificate.read_bytes())
    assert config["status"] == "PREPARED_ONE_BOX_HULL_NATIVE_CALL_NO_SOLVE"
    assert config["sources"]["helper"][1] == "54330f430c0c4dae03a0298533121ce43482ceb295f54df715ad2f2180d3503c"
    for key, (name, digest) in config["sources"].items():
        assert sha((ROOT / name).read_bytes()) == digest, key
    assert config["sources"]["replay"] == [str(Path(__file__).resolve().relative_to(ROOT)),
                                            sha(Path(__file__).read_bytes())]
    assert cert["configuration"] == reference(configuration)
    assert cert["model"] == config["model"]
    assert sha((ROOT / config["model"]["path"]).read_bytes()) == config["model"]["sha256"]
    assert all(config["inputs"][key][1] == value for key, value in EXPECTED.items())
    data = {key: bound(config["inputs"][key]) for key in EXPECTED}
    boxes, accepted, owner = (data[k] for k in ("boxes", "box_replay", "box_replay_owner"))
    assert accepted["status"] == "PASS_INDEPENDENT_H27_LOW_FACE_CUT_AND_CAPACITY_EQUIVALENCE"
    assert accepted["all260_cold_record_bindings_checked"]
    assert accepted["inputs"]["boxes"] == config["inputs"]["boxes"]
    assert owner["status"] == "CHILD_COMPLETE" and owner["exit_code"] == 0
    assert owner["child_reaped"] and not owner["hard_timeout"]
    assert owner["independent-replay.json"]["sha256"] == EXPECTED["box_replay"]
    cold, cold_owner = data["full_cold"], data["full_cold_owner"]
    assert cold["status"] == "PASS" and cold["checked"] == 260
    assert cold["checked_fixed_points"] == 191 and cold["checked_contradictions"] == 69
    assert cold["checked_partial"] == 0 and cold["all260_nonpartial_branches_checked"]
    assert cold["prior184_contradictions_and_complete_original_branch_cover_bound"]
    assert cold_owner["status"] == "CHILD_COMPLETE" and cold_owner["exit_code"] == 0
    assert cold_owner["child_reaped"] and not cold_owner["hard_timeout"]
    assert cold_owner["child_result"]["sha256"] == EXPECTED["full_cold"]
    assert boxes["coverage"]["remaining_boxes"] == 191 and boxes["coverage"]["partial_or_missing"] == 0
    ancestry = boxes["all260_proof_bindings"]
    assert len(ancestry) == 260 and [r["index"] for r in ancestry] == list(range(260))
    assert [r["cold_check"] for r in ancestry] == cold["checks"]
    box_ids = [r["index"] for r in ancestry if r["terminal"] == "fixed_point"]
    assert box_ids == [b["index"] for b in boxes["boxes"]] == cert["box_ids"]
    assert len(box_ids) == 191
    ids, zeros = boxes["original_column_ids"], boxes["proved_zero_columns"]
    assert ids == sorted(set(range(1214)) - set(zeros)) and len(ids) == 1102 and len(zeros) == 112
    states = []
    for box in boxes["boxes"]:
        state = box["state"]
        assert len(state) == 1102 and set(state) <= set("01?")
        assert sha(bytes(255 if s == "?" else int(s) for s in state)) == box["state_sha256"]
        states.append(state)
    point, point_cold = data["point"], data["point_cold"]
    assert point_cold["exact_point_replayed"] and point_cold["candidate_sha256"] == EXPECTED["point"]
    assert point_cold["full_face_rows_checked"] == 167121
    assert point_cold["registry_sha256"] == point["registry_sha256"]
    assert point_cold["point_key"] == point["exact_check"]["point_key"] == cert["point_key"]
    assert point["matrix_binding"]["original_column_ids"] == {
        "dtype": "uint16", "shape": [1102], "sha256": sha(struct.pack("<1102H", *ids))}
    den = integer(point["common_denominator"])
    full = list(map(integer, point["exact_check"]["original1214_selector_numerators"]))
    nums = [full[j] for j in ids]
    assert den == 2594289631 and len(full) == 1214
    assert all(full[j] == 0 for j in zeros) and all(0 < v <= den for v in nums)
    summary = {}
    if cert["kind"] == "rational_box_hull_membership":
        mass_den = integer(cert["lambda_denominator"])
        masses = list(map(integer, cert["lambda_numerators"]))
        assert len(masses) == 191 and mass_den > 0 and all(0 <= m <= mass_den for m in masses)
        assert sum(masses) == mass_den and math.gcd(mass_den, *masses) == 1
        assert max([mass_den.bit_length()] + [m.bit_length() for m in masses]) <= 2048
        slacks, fixed_intervals = [], 0
        for j, n in enumerate(nums):
            lower = sum(m for m, state in zip(masses, states) if state[j] == "1")
            upper = sum(m for m, state in zip(masses, states) if state[j] != "0")
            left, right = n * mass_den - den * lower, den * upper - n * mass_den
            assert 0 <= lower <= upper <= mass_den and left >= 0 and right >= 0
            assert left + right == den * (upper - lower)
            if lower == upper:
                assert left == right == 0
                fixed_intervals += 1
            slacks.append([str(left), str(right)])
            assert time.monotonic() - started < 60
        assert cert["owner_check"]["cross_multiplied_endpoint_slacks"] == slacks
        summary = {"status": "PASS_INDEPENDENT_BOX_HULL_MEMBERSHIP",
                   "mixture_weights_checked": 191, "positive_masses": sum(m > 0 for m in masses),
                   "coordinate_endpoint_bounds_checked": 2204, "fixed_zero_coordinates_checked": 112,
                   "degenerate_weighted_intervals": fixed_intervals,
                   "coordinatewise_interpolation_proved": True,
                   "no_linear_cut_valid_on_all191_boxes_rejects_this_point": True}
    elif cert["kind"] == "signed_box_hull_separator":
        row = cert["separator"]
        coefficients = list(map(integer, row["coefficients"]))
        assert len(coefficients) == 1102 and any(coefficients)
        assert max(map(abs, coefficients)) <= 1 << 20
        assert row["original1214_terms"] == [[a, c] for a, c in zip(ids, coefficients) if c]
        minima = []
        for state in states:
            value = 0
            for flag, c in zip(state, coefficients):
                if flag == "1" or (flag == "?" and c < 0):
                    value += c
            minima.append(value)
            assert time.monotonic() - started < 60
        alpha = min(minima)
        point_value = sum(c * n for c, n in zip(coefficients, nums))
        gap = alpha * den - point_value
        assert row["all_box_minima"] == minima and integer(row["lower"]) == alpha
        assert row["point_value_numerator"] == str(point_value) and row["point_denominator"] == str(den)
        assert row["deficit_numerator"] == str(gap) and gap > 0
        summary = {"status": "PASS_INDEPENDENT_BOX_HULL_SEPARATOR", "box_minima_checked": 191,
                   "original_coordinates": 1214, "nonzero_terms": sum(c != 0 for c in coefficients),
                   "lower": alpha, "deficit_numerator": str(gap), "point_denominator": str(den),
                   "native_ray_sign_or_feasibility_used": False}
    else:
        raise ValueError("unknown certificate kind")
    summary.update(source_sha256=sha(Path(__file__).read_bytes()),
                   configuration=reference(configuration), certificate=reference(certificate),
                   original_point=config["inputs"]["point"], boxes=config["inputs"]["boxes"],
                   optimizer_calls=0, numerical_models=0, linear_solves=0, producer_imports=0,
                   branch_trace_replays=0, boolean_or_original_model_solution_claimed=False,
                   case4_excluded=False, seconds=time.monotonic() - started)
    return summary


if __name__ == "__main__":
    assert __debug__
    parser = argparse.ArgumentParser()
    parser.add_argument("--configuration", type=Path, required=True)
    parser.add_argument("--certificate", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = replay(args.configuration, args.certificate)
    with args.output.open("x") as stream:
        json.dump(result, stream, sort_keys=True, indent=2)
        stream.write("\n")
    print(json.dumps({"status": result["status"], "seconds": result["seconds"],
                      "sha256": sha(args.output.read_bytes())}))
