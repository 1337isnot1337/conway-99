"""Direct five-Gram parity cover and its sparse equivalent; no optimizer.

Every coefficient is expanded on the original1214 columns. The proof uses
the old99 zero certificate and the previously checked twelve-zero theorem.
Column663 need not be zero for this new inequality.
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
    "native": (BASE+"complement-rook-35core-case0004-native-cpsat-model.json", "a9004e97a2d166bf8b162609cfb538eae0dd4d26942b6df5119b6a88d65ec476"),
    "old99": (BASE+"rook-case4-transportation-seed-certificate.json", "64d8e375280bc067097913de2dd6e2995c19de2a4807f63cecdcd80b811a85cf"),
    "twelve_zero_proof": (BASE+"rook-case4-face99-parity-face-certificate.json", "717c3e4103dd56bdd260f52b0f50c5a06f4245b834d92194357481d3163e229e"),
    "unit_sums": (BASE+"rook-case4-face111-two-parity-equalities-certificate.json", "6272996ff8c38af719b057dea6f6796efb895fdb678c69b82cc3eaff757ec606"),
    "scan_cut": (BASE+"rook-case4-face112-parity-run01/cuts.jsonl", "7e85b3d3a84c4b7e9489c1ab1f91717d372a399a62b55843b169f9a6e9e64a5b"),
    "scan_cold": (BASE+"rook-case4-face112-parity-run01-replay.json", "7d5f64961f83c7714804fad3521d13c5deb1924f804a6f2b8227897bf509e710"),
    "point": (BASE+"rook-case4-face112-basis-run01/candidate.json", "bb81664e8ea9faec6878ee98ec36c5ae844535e805f78fabe7c475a1f83d8ebb"),
    "point_cold": (BASE+"rook-case4-face112-basis-run01-replay.json", "cda50fcd87c9e5009243b76442a953a0f1f6b6461baead3ecf296cce508a0c59"),
}
GRAM_IDS = [124, 214, 320, 344, 582]
U_SUPPORT = [401, 402, 405, 590, 591, 592, 593, 594, 595]


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def read_inputs():
    data = {}
    for key, (name, expected) in INPUTS.items():
        raw = (ROOT/name).read_bytes()
        assert sha(raw) == expected, key
        data[key] = json.loads(raw)
    inventory = data["native"]["primary_inventory"]
    assert sha(canonical(inventory)) == data["native"]["primary_inventory_sha256"]
    return data, inventory


def gram(inventory, combination):
    vector, rhs, records = [0]*1214, 0, []
    assert len({i for i, m in combination}) == len(combination)
    for i, multiplier in combination:
        assert type(i) is type(multiplier) is int and 0 <= i < 630
        a, b, quota, members = inventory["Gram_rows"][i]
        rhs += multiplier*quota
        for column in members:
            vector[column] += multiplier
        records.append({"original_Gram_row": i, "core_pair": [a, b],
                        "quota": quota, "multiplier": multiplier})
    return vector, rhs, records


def prior_face(data, inventory):
    zeros = set(data["old99"]["seed_zero_columns"])
    assert len(zeros) == 99
    prior = data["twelve_zero_proof"]
    assert sorted(zeros) == prior["prior_zero_columns"]
    combination = [[r["original_native_row"], r["multiplier"]]
                   for r in prior["original_Gram_combination"]]
    coefficient, rhs, records = gram(inventory, combination)
    assert len(records) == 42 and rhs == 1 and coefficient == prior["full_original_coefficients"]
    new = set(prior["new_zero_columns"])
    h2 = set(prior["H2_support"])
    assert len(new) == 12 and not (new & zeros) and not (new & h2)
    for a in range(1214):
        if a not in zeros:
            assert coefficient[a] == int(a in h2) + 2*int(a in new)
    # Nonnegative integrality gives all twelve zeros, and then H2=1.
    zeros |= new
    units = data["unit_sums"]
    assert sorted(zeros) == units["proved_zero_columns"] and len(zeros) == 111 and 663 not in zeros
    h1, h2_saved = map(set, units["original_cover_supports"])
    assert h2 == h2_saved
    combination = [[r["original_native_row"], r["multiplier"]]
                   for r in units["H1_original_Gram_combination"]]
    first, odd_rhs, odd_records = gram(inventory, combination)
    assert len(odd_records) == 33 and odd_rhs == units["H1_original_right_hand_side"] == 45
    assert first == units["H1_full_original_integer_coefficients"]
    assert all((first[a]-int(a in h1)) % 2 == 0 for a in range(1214) if a not in zeros)
    h1, h2 = h1-zeros, h2-zeros
    assert sorted(h1-h2) == [259, 260, 261, 262]
    assert sorted(h2-h1) == [590, 591, 592, 593, 594, 595, 730, 731, 732, 733]
    signature, members = inventory["original_signature_rows"][51]
    assert signature == 96 and members == [258, 259, 260, 261, 262] and 258 in zeros
    # H1-H2=A-B, A<=1, B>=0, H2=1, so0<=H1<=2.
    # The33-row identity makes H1 odd, hence H1=1.
    return zeros, h1, h2


def build():
    data, inventory = read_inputs()
    zeros, h1, h2 = prior_face(data, inventory)
    cut, cold = data["scan_cut"], data["scan_cold"]
    assert cold["complete"] and cold["evaluated_candidates"] == 41041 and cold["violated_inequalities"] == 1
    assert cut["candidate_id"] == 23 and cut["basis_indices"] == [23]
    encoded = int(cut["lift"]["original_native_row_combination_hex"], 16)
    assert [a for a in range(encoded.bit_length()) if encoded >> a & 1] == GRAM_IDS
    coefficient, rhs, rows = gram(inventory, [[i, 1] for i in GRAM_IDS])
    assert all(r["quota"] == 1 and 25 in r["core_pair"] for r in rows) and rhs == 5
    assert sha(canonical(coefficient)) == cut["lift"]["full_integer_coefficients_sha256"]
    assert rhs == cut["lift"]["full_integer_right_hand_side"]
    support = [a for a, c in enumerate(coefficient) if c % 2 and a not in zeros]
    odd_zeros = [a for a, c in enumerate(coefficient) if c % 2 and a in zeros]
    assert len(support) == 27 and 663 not in support and coefficient[663] == 0
    assert hex(sum(1 << a for a in support)) == cut["row"]["support_original_hex"]
    assert int(cut["row"]["positive_original_hex"], 16) == 0 and cut["row"]["upper"] == -1
    assert odd_zeros == cut["lift"]["removed_proved_zero_odd_columns"]
    assert all(c >= 0 for c in coefficient)
    # All integral incidences make sum_H x odd. Nonnegativity implies >=1.
    # Its upper bound5 also follows from this positive sum of five rows.
    identity, identity_rhs, identity_rows = gram(inventory, [[582, 1], [214, 1], [344, -1]])
    assert identity_rhs == 1
    for a in h1:
        identity[a] += 1
    for a in h2:
        identity[a] -= 1
    for a in U_SUPPORT:
        identity[a] += 2
    identity[803] -= 2
    corrections = [[a, int(a in support)-identity[a]] for a in range(1214)
                   if int(a in support) != identity[a]]
    assert all(a in zeros for a, c in corrections)
    # H3 =1+2*(U-x803), because H1=H2=1.
    upper_vector, upper_rhs, upper_rows = gram(inventory, [[344, 1]])
    assert upper_rhs == 1
    for a in h2:
        upper_vector[a] += 1
    for a in h1:
        upper_vector[a] -= 1
    residual = [upper_vector[a]-int(a in U_SUPPORT) for a in range(1214)]
    assert all(c >= 0 or a in zeros for a, c in enumerate(residual))
    extras = [[a, c] for a, c in enumerate(residual) if c and a not in zeros]
    assert extras == [[a, 1] for a in [399, 403, 406, 730, 731, 732, 733, 761, 762, 763, 764, 765]]
    # U+sum_extras=1, so U<=1. Thus H3<=3 using x803>=0.
    point = data["point"]
    assert data["point_cold"]["exact_point_replayed"] and data["point_cold"]["candidate_sha256"] == INPUTS["point"][1]
    den = int(point["common_denominator"])
    numerators = list(map(int, point["exact_check"]["original1214_selector_numerators"]))
    assert len(numerators) == 1214 and den == 145446009
    value, sparse = sum(numerators[a] for a in support), numerators[803]-sum(numerators[a] for a in U_SUPPORT)
    assert den-value == cut["exact_violation_numerator"] == 23652796 == 2*sparse
    return {
        "status": "PASS: direct five-Gram odd cover and sparse equivalent on the111-zero integer face",
        "source_sha256": sha(Path(__file__).read_bytes()),
        "inputs": {k: {"path": p, "sha256": h} for k, (p, h) in INPUTS.items()},
        "inherited99_zero_proofs_rederived": False,
        "all111_zero_and_two_unit_sum_derivations_reexpanded": True,
        "prior111_zero_columns": sorted(zeros), "zero663_required": False,
        "five_original_Gram_rows": rows, "full_original_integer_coefficients": coefficient,
        "full_Gram_right_hand_side": rhs, "odd_zero_columns": odd_zeros,
        "cover_support": support, "cover_terms": [[a, 1] for a in support],
        "new_cover_lower": 1, "unit_box_upper": 27,
        "original_Gram_upper_bound": 5, "proved_upper_with_unit_sums": 3,
        "odd_integer_cover_values_allowed_by_these_bounds": [1, 3],
        "sparse_equivalent": {"target": 803, "positive_support": U_SUPPORT,
            "terms": sorted([[803, 1]]+[[a, -1] for a in U_SUPPORT]), "upper": 0},
        "sparse_identity": {"statement": "H3=1+2*(U-x803)",
            "original_Gram_combination": identity_rows, "H1_multiplier": 1, "H2_multiplier": -1,
            "full_original_comparison_vector": identity,
            "corrections_on_prior_zeros": corrections},
        "U_upper_certificate": {"original_Gram_combination": upper_rows,
            "H1_multiplier": -1, "H2_multiplier": 1,
            "full_original_coefficients": upper_vector, "rhs": 1,
            "nonnegative_extras_on_proved_face": extras, "upper": 1},
        "point_evaluation": {"denominator": den, "cover_numerator": value,
            "cover_violation_numerator": den-value, "sparse_violation_numerator": sparse},
        "all1214_coefficients_checked": True, "optimizer_calls": 0,
        "new_forced_zero_claimed": False, "case4_excluded": False,
    }


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=("prepare", "replay"))
    p.add_argument("--certificate", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    assert not args.output.exists()
    started = time.monotonic()
    current = build()
    if args.mode == "prepare":
        assert not args.certificate.exists()
        args.certificate.write_text(json.dumps(current, indent=2)+"\n")
    else:
        assert json.loads(args.certificate.read_bytes()) == current
    result = {"status": "PASS: five-row H3 and sparse identity "+args.mode,
        "source_sha256": sha(Path(__file__).read_bytes()),
        "certificate_sha256": sha(args.certificate.read_bytes()),
        "cover_size": 27, "sparse_terms": 10, "cover_range": [1, 3],
        "point_cover_violation": current["point_evaluation"],
        "full1214_original_expansion": True, "prior_zero_count": 111,
        "zero663_required": False, "optimizer_calls": 0, "case4_excluded": False,
        "seconds": time.monotonic()-started}
    args.output.write_text(json.dumps(result, indent=2)+"\n")
    print(json.dumps(result, indent=2))
