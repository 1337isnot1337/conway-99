"""Independent arithmetic review of the two parity-support equalities.

The prior 111-zero theorem is hash-bound. No subject source is imported,
no optimizer or parity search is run, and no graph exclusion is claimed.
"""
import argparse
import hashlib
import json
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[2]
BASE = "experiments/logs/grids-and-triangles/"
SUBJECT = "experiments/workspace/rook_case4_face111_two_parity_equalities.py"
SUBJECT_SHA = "195b5fc78cb6895ee7797ebf1926f1cd19d990d992d5a9e9638d44f24aa984c6"
CERTIFICATE = BASE+"rook-case4-face111-two-parity-equalities-certificate.json"
CERTIFICATE_SHA = "6272996ff8c38af719b057dea6f6796efb895fdb678c69b82cc3eaff757ec606"
PREVIOUS = BASE+"rook-case4-face99-parity-face-certificate.json"
PREVIOUS_SHA = "717c3e4103dd56bdd260f52b0f50c5a06f4245b834d92194357481d3163e229e"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def load(root, path, expected):
    raw = (root/path).read_bytes()
    assert sha(raw) == expected, path
    return json.loads(raw)


def audit(root):
    assert sha((root/SUBJECT).read_bytes()) == SUBJECT_SHA
    cert = load(root, CERTIFICATE, CERTIFICATE_SHA)
    prior = load(root, PREVIOUS, PREVIOUS_SHA)
    assert cert["source_sha256"] == SUBJECT_SHA and cert["prior_certificate_sha256"] == PREVIOUS_SHA
    native = load(root, cert["native_input"]["path"], cert["native_input"]["sha256"])
    covers = load(root, cert["odd_cover_input"]["path"], cert["odd_cover_input"]["sha256"])
    inv = native["primary_inventory"]
    canonical = json.dumps(inv, sort_keys=True, separators=(",", ":")).encode()
    assert sha(canonical) == native["primary_inventory_sha256"]
    zeros = set(prior["all_zero_columns"])
    assert len(zeros) == 111 and sorted(zeros) == cert["proved_zero_columns"]
    full = []
    for row in prior["both_integer_cover_rows"]:
        assert all(c == 1 for a, c in row["terms"])
        support = [a for a, c in row["terms"]]
        assert len(support) == len(set(support)) == 42
        full.append(support)
    assert full == cert["original_cover_supports"]
    assert full == [row["cover_support"] for row in covers["proofs"]]
    assert full[1] == prior["H2_support"]
    live = [sorted(set(s)-zeros) for s in full]
    assert live == cert["live_cover_supports"] and list(map(len, live)) == [36, 42]
    A, B = sorted(set(live[0])-set(live[1])), sorted(set(live[1])-set(live[0]))
    assert A == [259, 260, 261, 262] == cert["positive_difference_A"]
    assert B == [590, 591, 592, 593, 594, 595, 730, 731, 732, 733] == cert["negative_difference_B"]
    signature, capacity_support = inv["original_signature_rows"][51]
    assert signature == 96 and capacity_support == [258, 259, 260, 261, 262]
    assert sorted(set(capacity_support)-zeros) == A and 258 in zeros
    assert cert["original_signature_capacity"] == {
        "row": 51, "signature": 96, "support": capacity_support,
        "upper": 1, "proved_zero_members": [258], "remaining_support": A}
    gram = inv["Gram_rows"]
    coeff = [0]*1214
    rhs = 0
    rows = cert["H1_original_Gram_combination"]
    assert len(rows) == 33 and len({r["original_native_row"] for r in rows}) == 33
    for row in rows:
        i, j, q, support = gram[row["original_native_row"]]
        assert row["core_pair"] == [i, j] and row["quota"] == q and row["multiplier"] == 1
        rhs += q
        for a in support:
            coeff[a] += 1
    assert rhs == 45 == cert["H1_original_right_hand_side"]
    assert coeff == cert["H1_full_original_integer_coefficients"]
    assert coeff == covers["proofs"][0]["full_original_integer_coefficients"]
    H1, H2 = set(live[0]), set(live[1])
    half = []
    for a, c in enumerate(coeff):
        if a not in zeros:
            remainder = c-int(a in H1)
            assert remainder >= 0 and remainder % 2 == 0
            if remainder:
                half.append([a, remainder//2])
        assert int(a in H1)-int(a in H2) == int(a in A)-int(a in B)
    assert half == cert["H1_live_integer_half_coefficients"]
    # Re-expand the inherited H2 identity directly from its original rows.
    c2, rhs2 = [0]*1214, 0
    for row in prior["original_Gram_combination"]:
        i, j, q, support = gram[row["original_native_row"]]
        assert [i, j] == row["core_pair"] and q == row["quota"]
        rhs2 += row["multiplier"]*q
        for a in support:
            c2[a] += row["multiplier"]
    assert rhs2 == 1
    assert all(c2[a] == int(a in H2) for a in range(1214) if a not in zeros)
    assert cert["H1_exact_value"] == cert["H2_exact_value"] == 1
    return {
        "status": "PASS: full-source review and independent original-row arithmetic",
        "subject": {"path": SUBJECT, "sha256": SUBJECT_SHA},
        "certificate": {"path": CERTIFICATE, "sha256": CERTIFICATE_SHA},
        "prior_111_zero_premise": {"path": PREVIOUS, "sha256": PREVIOUS_SHA},
        "native_input": cert["native_input"], "odd_cover_input": cert["odd_cover_input"],
        "H1_signed_rows_checked": 33, "H2_signed_rows_checked": 42,
        "original_coordinates_checked": 1214, "live_support_sizes": [36, 42],
        "capacity_row": 51, "capacity_original_signature": 96, "live_capacity_support": A,
        "H1_minus_H2": {"positive": A, "negative": B},
        "exact_conclusion": "H2=1; capacity gives A<=1; H1=1+A-B is nonnegative and at most2; original integer Gram identity makes it odd; hence H1=1 and A=B<=1.",
        "prior_zero_derivation_repeated": False,
        "integrality_required": True, "old_real_feasible_region_preserved": False,
        "new_zero_columns_claimed": [], "new_one_columns_claimed": [],
        "case4_excluded": False, "subject_imported": False, "optimizer_calls": 0,
        "reviewer_source_sha256": sha(Path(__file__).read_bytes())}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, default=ROOT)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    assert not a.output.exists()
    started = time.monotonic()
    result = audit(a.root)
    result["seconds"] = time.monotonic()-started
    a.output.write_text(json.dumps(result, indent=2)+"\n")
    print(json.dumps(result, indent=2))
