"""Direct integer-Gram proofs for the two discovered42-column covers.

This verifier reads no modular basis and repeats no parity scan. It expands
the33/35 original Gram equations and verifies every one of1214 coefficients.
The resulting inequalities hold for all nonnegative integer incidences.
"""
import argparse
import hashlib
import json
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[2]
BASE = "experiments/logs/grids-and-triangles/"
INPUTS = {
    "native": (BASE+"complement-rook-35core-case0004-native-cpsat-model.json",
        "a9004e97a2d166bf8b162609cfb538eae0dd4d26942b6df5119b6a88d65ec476"),
    "zeros": (BASE+"rook-case4-transportation-seed-certificate.json",
        "64d8e375280bc067097913de2dd6e2995c19de2a4807f63cecdcd80b811a85cf"),
    "point": (BASE+"rook-case4-face99-basis-run01/candidate.json",
        "0b627484317e65562500fbbbbd594e4a95dbfa809576fae52f6c7ccdbe7191e7"),
    "point_replay": (BASE+"rook-case4-face99-basis-run01-replay.json",
        "2804da9ac0e976d7dc566b3be9cabef861ed24727221db72d4fc5da26f3a438d"),
    "cuts": (BASE+"rook-case4-face99-parity-run01/cuts.jsonl",
        "b0d0c7151774793e6e2c219f3bf038ffa2cb5ac85e52bef6adb52408bfa6fec2"),
}
DENOMINATOR = 1661041997


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def sites(mask):
    assert type(mask) is int and mask >= 0
    return [i for i in range(mask.bit_length()) if mask >> i & 1]


def prove():
    loaded = {}
    for name, (path, expected) in INPUTS.items():
        raw = (ROOT/path).read_bytes()
        assert sha(raw) == expected, name
        loaded[name] = [json.loads(line) for line in raw.splitlines()] if name == "cuts" else json.loads(raw)
    gram = loaded["native"]["primary_inventory"]["Gram_rows"]
    assert [(i, j) for i, j, quota, support in gram] == [(i, j) for i in range(35) for j in range(i, 35)]
    zeros = loaded["zeros"]["seed_zero_columns"]
    assert zeros == sorted(set(zeros)) and len(zeros) == 99
    zero_set = set(zeros)
    kept = [a for a in range(1214) if a not in zero_set]
    values = list(map(int, loaded["point"]["extended_numerators"]))
    denominator = int(loaded["point"]["common_denominator"])
    assert denominator == DENOMINATOR and len(values) == 1116
    full = [0]*1214
    for a, value in zip(kept, values[:-1]):
        assert 0 < value < denominator
        full[a] = value
    assert loaded["point_replay"]["exact_point_replayed"]
    assert loaded["point_replay"]["candidate_sha256"] == INPUTS["point"][1]
    masks = [0]*1214
    for i, j, quota, support in gram:
        assert type(quota) is int and quota >= 0
        assert support == sorted(set(support)) and all(0 <= a < 1214 for a in support)
        if i == j:
            for a in support:
                masks[a] |= 1 << i
        assert sum(full[a] for a in support) == quota*denominator
    for i, j, quota, support in gram:
        assert support == [a for a, mask in enumerate(masks) if mask >> i & 1 and mask >> j & 1]
    expected = [(15917, 33, 45, 214021056), (16018, 35, 47, 428042112)]
    assert len(loaded["cuts"]) == len(expected) == 2
    proofs = []
    for cut, (identifier, count, rhs_expected, gap_expected) in zip(loaded["cuts"], expected):
        assert cut["candidate_id"] == identifier
        original_ids = sites(int(cut["lift"]["original_native_row_combination_hex"], 16))
        assert len(original_ids) == count and max(original_ids) < 630
        coefficients, rhs, row_list = [0]*1214, 0, []
        for index in original_ids:
            i, j, quota, support = gram[index]
            rhs += quota
            row_list.append({"original_native_row": index, "core_pair": [i, j], "coefficient": 1, "quota": quota})
            for a in support:
                coefficients[a] += 1
        assert rhs == rhs_expected == cut["lift"]["full_integer_right_hand_side"]
        assert sha(canonical(coefficients)) == cut["lift"]["full_integer_coefficients_sha256"]
        support = [a for a in kept if coefficients[a] % 2]
        assert len(support) == 42
        assert support == sites(int(cut["row"]["support_original_hex"], 16))
        assert int(cut["row"]["positive_original_hex"], 16) == 0 and cut["row"]["upper"] == -1
        zero_terms = [[a, coefficients[a]] for a in zeros if coefficients[a]]
        zero_odd = [a for a in zeros if coefficients[a] % 2]
        assert zero_odd == cut["lift"]["removed_proved_zero_odd_columns"]
        even = [0 if a in zero_set else coefficients[a]//2 for a in range(1214)]
        support_set, zero_coefficients = set(support), dict(zero_terms)
        assert all(coefficients[a] == 2*even[a]+int(a in support_set)+zero_coefficients.get(a, 0)
                   for a in range(1214))
        assert rhs % 2 == 1 and all(type(v) is int and v >= 0 for v in even)
        cover_sum = sum(full[a] for a in support)
        even_sum = sum(even[a]*full[a] for a in range(1214))
        assert 2*even_sum+cover_sum == rhs*denominator
        assert denominator-cover_sum == cut["exact_violation_numerator"] == gap_expected
        assert cover_sum == cut["distance_numerator"] and 0 <= cover_sum < denominator
        proofs.append({"candidate_id": identifier, "original_Gram_row_sum": row_list,
            "full_original_integer_coefficients": coefficients,
            "original_right_hand_side": rhs, "removed_proved_zero_terms": zero_terms,
            "removed_odd_zero_terms": zero_odd,
            "even_integer_form_terms": [[a, v] for a, v in enumerate(even) if v],
            "cover_support": support, "cover_lower_bound": 1,
            "real_unit_box_upper_bound": 42,
            "all1214_coefficients_checked": True,
            "integer_identity": "2*even_form(x)+sum_cover(x)=original_right_hand_side after the99 proved zeros",
            "integer_rounding_bound": (rhs-1)//2,
            "necessary_domain": "nonnegative integer coordinates satisfying the original Gram equations and the99 proved zeros",
            "saved_point_cover_sum_numerator": cover_sum,
            "saved_point_denominator": denominator, "saved_point_violation_numerator": gap_expected})
    return {"status": "PASS: two direct integer-Gram parity-cover proofs",
        "source_sha256": sha(Path(__file__).read_bytes()),
        "input_bindings": {k: {"path": p, "sha256": h} for k, (p, h) in INPUTS.items()},
        "proofs": proofs, "new_linear_rows": [{"terms": [[a, 1] for a in p["cover_support"]],
            "lower": 1, "upper": 42} for p in proofs],
        "modular_source_imported": False, "parity_scan_repeated": False,
        "optimizer_calls": 0, "case4_excluded": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "replay"))
    parser.add_argument("--certificate", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    started = time.monotonic()
    certificate = prove()
    if args.mode == "prepare":
        assert not args.certificate.exists()
        args.certificate.write_text(json.dumps(certificate, indent=2)+"\n")
    else:
        assert json.loads(args.certificate.read_bytes()) == certificate
    report = {"status": "PASS: direct integer-Gram covers "+args.mode,
        "source_sha256": certificate["source_sha256"], "certificate_sha256": sha(args.certificate.read_bytes()),
        "original_equation_counts": [len(p["original_Gram_row_sum"]) for p in certificate["proofs"]],
        "odd_right_hand_sides": [p["original_right_hand_side"] for p in certificate["proofs"]],
        "support_sizes": [len(p["cover_support"]) for p in certificate["proofs"]],
        "violation_numerators": [p["saved_point_violation_numerator"] for p in certificate["proofs"]],
        "denominator": DENOMINATOR, "optimizer_calls": 0, "parity_scan_repeated": False,
        "case4_excluded": False, "seconds": time.monotonic()-started}
    args.output.write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps(report, indent=2))
