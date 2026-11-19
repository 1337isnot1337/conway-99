"""Check two complete cut records from an incomplete parity discovery run.

Standard library only. No imports from the discovery implementation, no RREF,
no family scan, and no optimizer. Prior zero and point acceptance are explicit
hash-bound premises. This checker does not claim search exhaustion.
"""
import argparse
import hashlib
import itertools
import json
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[2]
LOG = "experiments/logs/grids-and-triangles/"
INPUTS = {
    "native": (LOG+"complement-rook-35core-case0004-native-cpsat-model.json",
               "a9004e97a2d166bf8b162609cfb538eae0dd4d26942b6df5119b6a88d65ec476"),
    "model": (LOG+"rook-case4-face112-weighted-parity-model01/model.json",
              "c6cd72c995ce1a47db90fe7263f643131bc555ed50e329c7734536f5cf870ac3"),
    "model_cold": (LOG+"rook-case4-face112-weighted-parity-model01-cold-replay.json",
                   "567185c755134fcf7c15bb7be762bb2a70a503254259b2eb44a92f91abb39156"),
    "point": (LOG+"rook-case4-face112-weighted-parity-basis-run01/candidate.json",
              "3cd4d391e5b372f6ff0d2df11ebd16fccec1b7122527864fef76e33eae72312b"),
    "point_cold": (LOG+"rook-case4-face112-weighted-parity-basis-run01-replay.json",
                   "e6b8cacf16a38b4529f73d96aa7212ac6f71244846f8d0f38973cd865667c0d4"),
    "cuts": (LOG+"rook-case4-parity-cycle-run01/scan-00/cuts.jsonl",
             "9cba12a6030d06de531107cf0e28010cd81011319e0e98d363d4146349e85cd1"),
    "partial_terminal": (LOG+"rook-case4-parity-cycle-run01/result.json",
                         "56fd0e4dc684dc39ff11c969608596145f865f61c3c8b17d13c546663646c735"),
    "bindings_audit": (LOG+"rook-case4-parity-cycle-run01-bindings.json",
                       "e861f181aaf82602fe3ab65586c83b9caea3ec77c53bfb9866f3eeb2e1d7a93c"),
}
EXPECTED_RAW_IDS = [73296, 76530]
SECONDS = 10


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"))+"\n").encode()


def tick(deadline):
    if time.monotonic() >= deadline:
        raise TimeoutError("ten-second direct two-record proof budget")


def integer(value):
    if type(value) is int:
        result = value
    else:
        assert type(value) is str and value and value == str(int(value))
        result = int(value)
    assert abs(result).bit_length() <= 4096
    return result


def bound_inputs():
    out = {}
    for name, (path, expected) in INPUTS.items():
        raw = (ROOT/path).read_bytes()
        assert digest(raw) == expected, ("changed input", name)
        out[name] = [json.loads(line) for line in raw.splitlines()] if name == "cuts" else json.loads(raw)
    return out


def signed_row(support, forbidden):
    assert support == sorted(set(support)) and forbidden == sorted(set(forbidden))
    assert set(forbidden) <= set(support)
    one = set(forbidden)
    return {"terms": [[a, 1 if a in one else -1] for a in support],
            "upper": len(forbidden)-1}


def direct_record(cut, gram, zeros, nums, den, deadline):
    ids = cut["original_Gram_row_ids"]
    assert ids == sorted(set(ids)) and ids
    assert all(type(i) is int and 0 <= i < len(gram) for i in ids)
    coefficients = [0]*len(nums)
    rhs = 0
    for i in ids:
        tick(deadline)
        left, right, quota, sites = gram[i]
        assert type(quota) is int and quota >= 0
        assert sites == sorted(set(sites))
        assert all(type(a) is int and 0 <= a < len(nums) for a in sites)
        rhs += quota
        for a in sites:
            coefficients[a] += 1
    assert coefficients == cut["full_original1214_integer_coefficients"]
    assert rhs == cut["original_Gram_rhs_sum"]
    assert sum(c*n for c, n in zip(coefficients, nums)) == rhs*den
    zero_set = set(zeros)
    support = [a for a, c in enumerate(coefficients) if c % 2 and a not in zero_set]
    removed = [a for a, c in enumerate(coefficients) if c % 2 and a in zero_set]
    assert all(nums[a] == 0 for a in zero_set)
    assert removed == cut["removed_proved_zero_odd_columns"]
    assert cut["active_original_support_hex"] == hex(sum(1 << a for a in support))
    parity_rhs = rhs % 2
    assert cut["parity_rhs"] == parity_rhs
    saved = cut["forbidden_vertex_certificate"]
    forbidden = saved["forbidden_ones"]
    assert saved["support"] == support and saved["parity_rhs"] == parity_rhs
    row = signed_row(support, forbidden)
    assert len(forbidden) % 2 != parity_rhs, "the Boolean vertex must be forbidden"
    assert row == cut["inequality"]
    one = set(forbidden)
    distance = sum(den-nums[a] if a in one else nums[a] for a in support)
    deficit = sum(c*nums[a] for a, c in row["terms"])-row["upper"]*den
    assert deficit == den-distance and deficit > 0
    assert saved["denominator"] == den and saved["distance_numerator"] == distance
    assert cut["exact_violation_numerator"] == deficit and saved["strictly_violated"] is True
    # These are covers, so also expose the equivalent rounded-capacity proof.
    assert parity_rhs == 1 and forbidden == [] and all(c >= 0 for c in coefficients)
    floor_terms = [[a, c//2] for a, c in enumerate(coefficients) if a not in zero_set and c >= 2]
    cover_value = sum(nums[a] for a in support)
    floor_value = sum(c*nums[a] for a, c in floor_terms)
    assert cover_value+2*floor_value == rhs*den
    assert 2*(floor_value-((rhs-1)//2)*den) == deficit
    tick(deadline)
    return {"raw_candidate_id": cut["raw_candidate_id"],
            "original_Gram_rows": [[i, gram[i][0], gram[i][1], gram[i][2]] for i in ids],
            "original_Gram_rhs_sum": rhs,
            "full_original1214_integer_coefficients": coefficients,
            "active_original_support": support,
            "removed_proved_zero_odd_columns": removed,
            "support_size": len(support), "parity_rhs": parity_rhs,
            "signed_inequality": row,
            "cover_range": [1, min(len(support), rhs)],
            "equivalent_rounded_capacity": {"terms": floor_terms, "upper": (rhs-1)//2},
            "identity": "sum_H x + 2*sum_a floor(c_a/2)*x_a = original_Gram_rhs_sum on the proved zero face",
            "point_cover_value_numerator": cover_value,
            "point_denominator": den, "exact_cover_deficit_numerator": deficit,
            "exact_capacity_excess_numerator_over_2D": deficit}


def controls():
    checked = 0
    for size in range(6):
        support = list(range(size))
        for bits in itertools.product((0, 1), repeat=size):
            forbidden = [i for i, b in enumerate(bits) if b]
            rhs = 1-sum(bits) % 2
            row = signed_row(support, forbidden)
            for z in itertools.product((0, 1), repeat=size):
                if sum(z) % 2 == rhs:
                    lhs = sum(c*z[a] for a, c in row["terms"])
                    assert lhs <= row["upper"]
                    assert row["upper"]-lhs == sum(z[i] != bits[i] for i in support)-1
                    checked += 1
    # A real point satisfies these 0/1 equalities but violates their odd cover.
    gram = [[0, 0, 1, [0, 1, 2]], [0, 1, 1, [1, 3]], [1, 1, 1, [2, 3]]]
    cut = {"original_Gram_row_ids": [0, 1, 2], "full_original1214_integer_coefficients": [1, 2, 2, 2],
           "original_Gram_rhs_sum": 3, "removed_proved_zero_odd_columns": [],
           "active_original_support_hex": "0x1", "parity_rhs": 1,
           "forbidden_vertex_certificate": {"support": [0], "parity_rhs": 1, "forbidden_ones": [],
               "denominator": 2, "distance_numerator": 0, "strictly_violated": True},
           "inequality": {"terms": [[0, -1]], "upper": -1},
           "exact_violation_numerator": 2, "raw_candidate_id": 0}
    result = direct_record(cut, gram, [], [0, 1, 1, 1], 2, time.monotonic()+10)
    assert result["equivalent_rounded_capacity"] == {"terms": [[1, 1], [2, 1], [3, 1]], "upper": 1}
    rejected = 0
    for key, bad in [("original_Gram_rhs_sum", 5), ("exact_violation_numerator", 1),
                     ("full_original1214_integer_coefficients", [1, 2, 2, 1]),
                     ("active_original_support_hex", "0x3")]:
        changed = dict(cut); changed[key] = bad
        try:
            direct_record(changed, gram, [], [0, 1, 1, 1], 2, time.monotonic()+10)
        except AssertionError:
            rejected += 1
        else:
            raise AssertionError("tampered proof accepted")
    return {"Boolean_inequality_assignments": checked, "literal_Gram_point_control": 1,
            "tampered_record_rejections": rejected, "production_records_checked": 0}


def prepare():
    inputs = bound_inputs()
    cuts = inputs["cuts"]
    assert [c["raw_candidate_id"] for c in cuts] == EXPECTED_RAW_IDS
    return {"status": "PREPARED: two-record direct proof replay, case arithmetic unrun",
            "source_sha256": digest(Path(__file__).read_bytes()), "inputs": INPUTS,
            "limits": {"seconds": SECONDS, "records": 2, "original_columns": 1214,
                       "original_Gram_rows": 630},
            "saved_proposals": [{"raw_candidate_id": c["raw_candidate_id"],
                "original_Gram_row_ids": c["original_Gram_row_ids"],
                "saved_rhs": c["original_Gram_rhs_sum"],
                "saved_support_size": len(c["forbidden_vertex_certificate"]["support"]),
                "saved_deficit_numerator": c["exact_violation_numerator"]} for c in cuts],
            "controls": controls(), "case_RREF_or_scan_or_optimizer": False,
            "search_exhaustion_claimed": False}


def replay(preparation):
    started = time.monotonic(); deadline = started+SECONDS
    assert preparation["source_sha256"] == digest(Path(__file__).read_bytes())
    assert canonical(preparation["inputs"]) == canonical(INPUTS)
    inputs = bound_inputs(); tick(deadline)
    model, model_cold = inputs["model"], inputs["model_cold"]
    assert model_cold["model_sha256"] == INPUTS["model"][1]
    assert model_cold["status"].startswith("PASS:")
    zeros = model["fixed_zero_columns"]
    assert zeros == sorted(set(zeros)) and len(zeros) == 112
    assert all(type(a) is int and 0 <= a < 1214 for a in zeros)
    point, cold = inputs["point"], inputs["point_cold"]
    assert cold["candidate_sha256"] == INPUTS["point"][1] and cold["exact_point_replayed"] is True
    assert cold["status"].startswith("PASS:")
    den = integer(point["common_denominator"])
    nums = [integer(v) for v in point["exact_check"]["original1214_selector_numerators"]]
    assert len(nums) == 1214 and den == 337510679 and all(0 <= n <= den for n in nums)
    assert all(nums[a] == 0 for a in zeros)
    gram = inputs["native"]["primary_inventory"]["Gram_rows"]
    assert len(gram) == 630
    for left, right, quota, sites in gram:
        tick(deadline)
        assert type(quota) is int and quota >= 0
        assert sites == sorted(set(sites)) and all(type(a) is int and 0 <= a < 1214 for a in sites)
        assert sum(nums[a] for a in sites) == quota*den
    terminal = inputs["partial_terminal"]
    assert terminal["new_cut_registry"] == [] and terminal["native_calls"] == 0
    assert inputs["bindings_audit"]["result"]["sha256"] == INPUTS["partial_terminal"][1]
    cuts = inputs["cuts"]
    assert [c["raw_candidate_id"] for c in cuts] == EXPECTED_RAW_IDS
    checked = [direct_record(c, gram, zeros, nums, den, deadline) for c in cuts]
    return {"status": "PASS: two complete necessary cuts and their exact point deficits",
            "source_sha256": digest(Path(__file__).read_bytes()), "inputs": INPUTS,
            "proved_zero_premises": zeros, "original_Gram_rows_point_checked": 630,
            "cuts": checked, "seconds": time.monotonic()-started,
            "new_scan_RREF_elimination_optimizer_calls": 0,
            "original_cycle_artifacts_modified": False,
            "scope": "individual binary necessary inequalities; prior accepted112-zero face",
            "search_exhaustion_claimed": False, "case4_excluded": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "replay"))
    parser.add_argument("--preparation")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    path = Path(args.output).resolve(); assert not path.exists(), "immutable outputs"
    try:
        result = prepare() if args.mode == "prepare" else replay(json.loads(Path(args.preparation).read_text()))
    except Exception as exc:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"status": "UNRESOLVED: direct checker error", "error": repr(exc),
            "source_sha256": digest(Path(__file__).read_bytes()), "case4_excluded": False}, indent=2)+"\n")
        raise
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, sort_keys=True, indent=2)+"\n")
    print(json.dumps({"status": result["status"], "output": str(path), "sha256": digest(path.read_bytes())}))


if __name__ == "__main__":
    main()
