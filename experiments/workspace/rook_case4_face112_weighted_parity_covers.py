"""Two direct nonnegative-integer Gram cuts from the weighted parity census.

This file imports no subject model builder, parity separator, or optimizer.
It expands the saved row sums on all1214 original columns. Only the prior99
proved zeros are needed for the odd-cover statements. The current112-zero
face is used solely to choose a shorter equivalent row for the next model.
"""
import argparse
from collections import Counter
import hashlib
import itertools
import json
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[2]
BASE = "experiments/logs/grids-and-triangles/"
INPUTS = {
    "native": (BASE+"complement-rook-35core-case0004-native-cpsat-model.json", "a9004e97a2d166bf8b162609cfb538eae0dd4d26942b6df5119b6a88d65ec476"),
    "old99": (BASE+"rook-case4-transportation-seed-certificate.json", "64d8e375280bc067097913de2dd6e2995c19de2a4807f63cecdcd80b811a85cf"),
    "model": (BASE+"rook-case4-face112-h3-model02/model.json", "1928eb76274865e219747f631fee2d7a327ed7acd3a845986844be13c9e34265"),
    "model_cold": (BASE+"rook-case4-face112-h3-model02-cold-replay.json", "56864810924bacb6b331db728a4ce32810d8e6f2dfe7c196e0a73e0b2f583a97"),
    "scan": (BASE+"rook-case4-face112-h3-weighted-parity-run01/result.json", "0b6dc921a9f8228f7758d77fce1b25e2b1cfda3f41e9901bd70d69d2f0b7d159"),
    "scan_cold": (BASE+"rook-case4-face112-h3-weighted-parity-run01-replay.json", "1cc5086c7d1b5102c9df8825127e8dfd06317c03517402cb85fdf49678069544"),
    "cuts": (BASE+"rook-case4-face112-h3-weighted-parity-run01/cuts.jsonl", "67a0e3ff1c0c4e9decc3f82ba3d492fa5ff88dc87e857d7f23ed0d3971e8ab5e"),
    "point": (BASE+"rook-case4-face112-h3-basis-run01/candidate.json", "cecacaaa1cb6974dd898f1d2b69be32a06e44e9b89a1b45e35717bc347d3b4e8"),
    "point_check": (BASE+"rook-case4-face112-h3-point-direct-check01.json", "f20cb9ffe3768591cd255dd9b148881d7c3df8df80fb881a7c59a75c6758395c"),
}
WITNESSES = [
    {"raw_candidate_id": 69760, "rows": [180,264,405,444,462,517,521],
     "rhs": 9, "cover_size": 70, "gap": 16558664},
    {"raw_candidate_id": 72900, "rows": [151,181,210,291,385,426,445,463,531,532,533,534,535,537],
     "rhs": 17, "cover_size": 50, "gap": 8455479910},
]


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def inputs(root):
    data = {}
    for key, (name, expected) in INPUTS.items():
        raw = (root/name).read_bytes()
        assert sha(raw) == expected, key
        data[key] = [json.loads(line) for line in raw.splitlines()] if key == "cuts" else json.loads(raw)
    return data


def controls():
    assignments = odd = 0
    for n in range(1,5):
        for coefficient in itertools.product(range(4), repeat=n):
            for x in itertools.product(range(3), repeat=n):
                rhs = sum(c*a for c,a in zip(coefficient,x))
                cover = sum(a for c,a in zip(coefficient,x) if c % 2)
                floor = sum((c//2)*a for c,a in zip(coefficient,x))
                assert cover+2*floor == rhs and 0 <= cover <= rhs
                if rhs % 2:
                    assert cover >= 1 and floor <= (rhs-1)//2
                    odd += 1
                assignments += 1
    assert assignments == 22620
    return {"nonnegative_integer_assignments": assignments,
            "odd_right_hand_sides": odd,
            "identity": "H+2F=b; odd b and integral nonnegative H imply H>=1 and F<=(b-1)/2"}


def build(root=ROOT):
    data = inputs(root)
    native = data["native"]["primary_inventory"]
    assert sha(canonical(native)) == data["native"]["primary_inventory_sha256"]
    rows = native["Gram_rows"]
    assert len(rows) == 630
    prior = set(data["old99"]["seed_zero_columns"])
    face = set(data["model"]["fixed_zero_columns"])
    assert len(prior) == 99 and len(face) == 112 and prior <= face
    assert data["model"]["columns"] == 1102 and data["model"]["original_columns"] == 1214
    assert data["model"]["fixed_one_columns"] == []
    assert data["scan"]["complete"] and data["scan"]["raw_prefix"] == 123123
    assert data["scan"]["retained_cuts"] == data["scan_cold"]["retained_cuts_checked"] == 2
    assert data["scan_cold"]["complete_declared_families"]
    assert data["scan_cold"]["result_sha256"] == INPUTS["scan"][1]
    point = data["point"]
    den = int(point["common_denominator"])
    numerators = list(map(int, point["exact_check"]["original1214_selector_numerators"]))
    assert den == 27131679103 and len(numerators) == 1214
    assert all(0 <= a <= den for a in numerators)
    assert all(numerators[a] == 0 for a in face)
    for i,j,q,members in rows:
        assert sum(numerators[a] for a in members) == q*den
    assert len(data["cuts"]) == len(WITNESSES) == 2
    certificates = []
    for expected, cut in zip(WITNESSES, data["cuts"]):
        assert cut["raw_candidate_id"] == expected["raw_candidate_id"]
        assert cut["original_Gram_row_ids"] == expected["rows"]
        coefficient, rhs, row_records = [0]*1214, 0, []
        for row in expected["rows"]:
            assert 0 <= row < 630
            i,j,q,members = rows[row]
            assert q >= 0 and len(members) == len(set(members))
            rhs += q
            for a in members:
                coefficient[a] += 1
            row_records.append({"original_Gram_row": row, "core_pair": [i,j], "quota": q, "multiplier": 1})
        assert rhs == expected["rhs"] == cut["original_Gram_rhs_sum"] and rhs % 2
        assert coefficient == cut["full_original1214_integer_coefficients"]
        assert all(c >= 0 for c in coefficient)
        support = [a for a,c in enumerate(coefficient) if c % 2 and a not in prior]
        odd_zeros = [a for a,c in enumerate(coefficient) if c % 2 and a in prior]
        assert len(support) == expected["cover_size"]
        assert all(a not in face for a in support)
        assert odd_zeros == cut["removed_proved_zero_odd_columns"]
        assert support == cut["forbidden_vertex_certificate"]["support"]
        assert cut["forbidden_vertex_certificate"]["forbidden_ones"] == []
        assert cut["inequality"] == {"terms": [[a,-1] for a in support], "upper": -1}
        floor_prior = [[a,c//2] for a,c in enumerate(coefficient) if c//2 and a not in prior]
        floor_face = [[a,c//2] for a,c in enumerate(coefficient) if c//2 and a not in face]
        for zero_set, floor in ((prior,floor_prior),(face,floor_face)):
            f = dict(floor)
            assert all((0 if a in zero_set else coefficient[a]) == int(a in support)+2*f.get(a,0)
                       for a in range(1214))
        cover_value = sum(numerators[a] for a in support)
        floor_value = sum(c*numerators[a] for a,c in floor_face)
        cap = (rhs-1)//2
        gap = den-cover_value
        assert gap == expected["gap"] == cut["exact_violation_numerator"] > 0
        assert cover_value+2*floor_value == rhs*den
        assert 2*(floor_value-cap*den) == gap
        use_floor = len(floor_face) < len(support)
        chosen = {"representation": "rounded_capacity" if use_floor else "odd_cover",
                  "terms": floor_face if use_floor else [[a,1] for a in support],
                  "lower": 0 if use_floor else 1,
                  "upper": cap if use_floor else rhs}
        # Floor lower0 and cover upperrhs follow from nonnegative coefficients.
        assert chosen["terms"] and all(a not in face and c > 0 for a,c in chosen["terms"])
        certificates.append({
            "raw_candidate_id": expected["raw_candidate_id"],
            "original_Gram_rows": row_records,
            "full_original1214_integer_coefficients": coefficient,
            "original_right_hand_side": rhs,
            "odd_proved_zero_columns": odd_zeros,
            "cover_support": support, "cover_bounds": [1,rhs],
            "floor_capacity_on_prior99_face": {"terms": floor_prior,"upper": cap},
            "floor_capacity_on_current112_face": {"terms": floor_face,"upper": cap},
            "identity_on_either_proved_face": "sum_H x +2*sum_floor x = original_right_hand_side",
            "additional_floor_terms_removed_on_current_face": [[a,c] for a,c in floor_prior if a in face],
            "all1214_identity_coordinates_checked": True,
            "chosen_equivalent_append_row": chosen,
            "point_evaluation": {"denominator": den, "cover_numerator": cover_value,
                "cover_deficit_numerator": gap, "capacity_numerator": floor_value,
                "capacity_excess_numerator": floor_value-cap*den},
        })
    return {"status": "PASS: two direct integer Gram covers and equivalent rounded capacities",
        "source_sha256": sha(Path(__file__).read_bytes()),
        "inputs": {k:{"path":p,"sha256":h} for k,(p,h) in INPUTS.items()},
        "prior99_zero_columns": sorted(prior), "current112_zero_columns": sorted(face),
        "prior_zero_derivations_repeated": False,
        "scope": "Nonnegative integer selectors satisfying all original Gram equations and the prior99 proved zeros obey both covers. Current112 zeros only shorten equivalent capacity rows.",
        "cuts": certificates, "controls": controls(),
        "original_Gram_point_rows_checked": 630,
        "optimizer_calls": 0, "new_zero_claimed": False, "case4_excluded": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode",choices=("prepare","replay"))
    parser.add_argument("--root",type=Path,default=ROOT)
    parser.add_argument("--certificate",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    start = time.monotonic()
    current = build(args.root)
    if args.mode == "prepare":
        assert not args.certificate.exists()
        args.certificate.write_text(json.dumps(current,indent=2)+"\n")
    else:
        assert json.loads(args.certificate.read_bytes()) == current
    report = {"status":"PASS: direct two-cut "+args.mode,
        "source_sha256":current["source_sha256"],
        "certificate_sha256":sha(args.certificate.read_bytes()),
        "all_original_coordinates_checked":1214,"prior_zero_count":99,
        "cover_sizes":[len(c["cover_support"]) for c in current["cuts"]],
        "chosen_rows":[{"representation":c["chosen_equivalent_append_row"]["representation"],
            "terms":len(c["chosen_equivalent_append_row"]["terms"]),
            "bounds":[c["chosen_equivalent_append_row"]["lower"],c["chosen_equivalent_append_row"]["upper"]]}
            for c in current["cuts"]],
        "optimizer_calls":0,"case4_excluded":False,"seconds":time.monotonic()-start}
    args.output.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))
