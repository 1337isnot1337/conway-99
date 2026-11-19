"""Prove x663=0 from the original Gram rows, one capacity and prior99 zeros.

Previously saved multipliers are proposal data only. Final acceptance expands
every coefficient on all1214 columns from the original inventory. Neither
parity equality nor any of the twelve later zeros is a proof premise.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[2]
BASE = "experiments/logs/grids-and-triangles/"
INPUTS = {
    "native": (BASE + "complement-rook-35core-case0004-native-cpsat-model.json", "a9004e97a2d166bf8b162609cfb538eae0dd4d26942b6df5119b6a88d65ec476"),
    "seed": (BASE + "rook-case4-transportation-seed-certificate.json", "64d8e375280bc067097913de2dd6e2995c19de2a4807f63cecdcd80b811a85cf"),
    "H2_Gram_proposal": (BASE + "rook-case4-face99-parity-face-certificate.json", "717c3e4103dd56bdd260f52b0f50c5a06f4245b834d92194357481d3163e229e"),
    "663_Gram_proposal": (BASE + "rook-case4-face111-native-bounds-independent-replay.json", "5e1e01b8c5f3c5747292d65e6938263afe7a72bfff68b00ee29cf2f41b23b2a3"),
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def inputs():
    data = {}
    for key, (name, expected) in INPUTS.items():
        raw = (ROOT / name).read_bytes()
        assert sha(raw) == expected
        data[key] = json.loads(raw)
    assert sha(canonical(data["native"]["primary_inventory"])) == data["native"]["primary_inventory_sha256"]
    return data


def expand(native, weights):
    inventory = native["primary_inventory"]
    gram = inventory["Gram_rows"]
    assert [(i, j) for i, j, q, s in gram] == [(i, j) for i in range(35) for j in range(i, 35)]
    coefficient, rhs, records = [0] * 1214, 0, []
    for row, multiplier in sorted(weights.items()):
        if not multiplier:
            continue
        assert type(row) is type(multiplier) is int and 0 <= row < 630
        i, j, quota, members = gram[row]
        assert members == sorted(set(members))
        rhs += multiplier * quota
        for a in members:
            coefficient[a] += multiplier
        records.append({"original_Gram_row": row, "core_pair": [i, j],
                        "quota": quota, "multiplier": multiplier})
    signature, support = inventory["original_signature_rows"][51]
    assert signature == 96 and support == [258, 259, 260, 261, 262]
    for a in support:
        coefficient[a] += 1
    return coefficient, rhs + 1, records, {"original_signature_row": 51,
        "original_native_row": 681, "signature": signature, "support": support,
        "multiplier": 1, "lower": 0, "upper": 1}


def build(data):
    weights = Counter()
    skipped = []
    for family, row, multiplier in data["663_Gram_proposal"]["short_identity"]["original_row_combination"]:
        if family == "Gram":
            weights[row] += multiplier
        else:
            skipped.append([family, row, multiplier])
    assert skipped == [["H1", 0, 1]]
    for item in data["H2_Gram_proposal"]["original_Gram_combination"]:
        weights[item["original_native_row"]] += item["multiplier"]
    full, upper, gram_rows, capacity = expand(data["native"], weights)
    zeros = data["seed"]["seed_zero_columns"]
    assert zeros == sorted(set(zeros)) and len(zeros) == 99 and 663 not in zeros
    assert zeros == data["H2_Gram_proposal"]["prior_zero_columns"]
    surviving = [a for a in range(1214) if a not in set(zeros)]
    assert len(gram_rows) == 143 and upper == 5 and full[663] == 6
    assert all(full[a] >= 0 for a in surviving)
    negative = [[a, c] for a, c in enumerate(full) if c < 0]
    assert all(a in zeros for a, c in negative)
    return {
        "status": "PASS: original143 Gram rows plus signature capacity force x663=0 on the prior99-zero face",
        "source_sha256": sha(Path(__file__).read_bytes()),
        "inputs": {k: {"path": p, "sha256": h} for k, (p, h) in INPUTS.items()},
        "authoritative_final_premises": ["original630 Gram equations", "original signature96 capacity row51", "prior99 certified zero columns", "nonnegative coordinates", "integer coordinate x663"],
        "prior99_zero_columns": zeros,
        "original_Gram_combination": gram_rows,
        "original_capacity": capacity,
        "full_original_integer_coefficients": full,
        "combined_upper_bound": upper,
        "target_column": 663, "target_coefficient": 6,
        "negative_original_coefficients_on_prior_zeros_only": negative,
        "surviving_nonnegative_terms": [[a, full[a]] for a in surviving if full[a]],
        "surviving_coefficient_histogram": {str(k): v for k, v in sorted(Counter(full[a] for a in surviving).items())},
        "exact_target_real_upper_bound": [5, 6],
        "integer_consequence": "6*x663 <= 5 and x663 is nonnegative integer, hence x663=0",
        "H1_equality_used_as_premise": False, "H2_equality_used_as_premise": False,
        "twelve_later_zeros_used_as_premises": False,
        "other_coordinate_upper_bounds_used": False,
        "proposal_multipliers_must_be_trusted_for_acceptance": False,
        "all1214_original_coefficients_checked": True,
        "old99_zero_proofs_rederived": False,
        "optimizer_calls": 0, "numerical_point_used": False, "case4_excluded": False,
    }


def verify(data, certificate):
    # This check needs only original rows, prior zeros and the saved integer
    # combination; neither proposal certificate enters its arithmetic.
    weights = Counter()
    for record in certificate["original_Gram_combination"]:
        row, multiplier = record["original_Gram_row"], record["multiplier"]
        assert row not in weights and multiplier
        weights[row] = multiplier
    full, upper, rows, capacity = expand(data["native"], weights)
    assert rows == certificate["original_Gram_combination"] and capacity == certificate["original_capacity"]
    assert full == certificate["full_original_integer_coefficients"] and upper == certificate["combined_upper_bound"] == 5
    zero = data["seed"]["seed_zero_columns"]
    assert zero == certificate["prior99_zero_columns"] and len(zero) == 99 and 663 not in zero
    assert full[663] == certificate["target_coefficient"] == 6
    assert all(c >= 0 or a in zero for a, c in enumerate(full))
    assert certificate["target_column"] == 663 and certificate["exact_target_real_upper_bound"] == [5, 6]
    return {"all1214_coefficients_reexpanded": True, "original_Gram_rows": len(rows),
            "original_capacities": 1, "prior_zero_count": 99,
            "additional_parity_equalities_or_later_zeros_used": False,
            "upper_bound": 5, "target_coefficient": 6, "optimizer_calls": 0}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "replay"))
    parser.add_argument("--certificate", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    assert not args.output.exists()
    started = time.monotonic()
    data = inputs()
    if args.mode == "prepare":
        assert not args.certificate.exists()
        proof = build(data)
        args.certificate.write_text(json.dumps(proof, indent=2) + "\n")
    else:
        proof = json.loads(args.certificate.read_bytes())
        assert proof["source_sha256"] == sha(Path(__file__).read_bytes())
        assert proof["inputs"] == {k: {"path": p, "sha256": h} for k, (p, h) in INPUTS.items()}
    checked = verify(data, proof)
    report = {"status": "PASS: original99-face Gram/capacity zero663 " + args.mode,
              "source_sha256": sha(Path(__file__).read_bytes()),
              "certificate_sha256": sha(args.certificate.read_bytes()), "checked": checked,
              "seconds": time.monotonic() - started, "case4_excluded": False}
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
