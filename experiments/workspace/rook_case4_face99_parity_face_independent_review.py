"""Independent saved-row arithmetic audit of the case-4 face99 theorem.

No subject import, optimizer, seed rederivation, or matrix regeneration.
The previously certified 99-zero premise is bound by its frozen hash.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import time

SUBJECT = "experiments/workspace/rook_case4_face99_parity_face.py"
SUBJECT_SHA = "52621284ad3b8344c5b64e99b028a8e5e063f32e91468399ad69ab4ee69e93cc"
CERTIFICATE = "experiments/logs/grids-and-triangles/rook-case4-face99-parity-face-certificate.json"
CERTIFICATE_SHA = "717c3e4103dd56bdd260f52b0f50c5a06f4245b834d92194357481d3163e229e"
ROOT = Path(__file__).resolve().parents[2]


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def checked_json(root, path, expected):
    raw = (root / path).read_bytes()
    assert digest(raw) == expected, path
    return json.loads(raw)


def audit(root):
    assert digest((root / SUBJECT).read_bytes()) == SUBJECT_SHA
    cert = checked_json(root, CERTIFICATE, CERTIFICATE_SHA)
    assert cert["source_sha256"] == SUBJECT_SHA
    inputs = {}
    for name in ("native", "seed", "covers"):
        binding = cert["input_bindings"][name]
        inputs[name] = checked_json(root, binding["path"], binding["sha256"])
    native = inputs["native"]
    inventory = native["primary_inventory"]
    assert digest(canonical(inventory)) == native["primary_inventory_sha256"]
    gram = inventory["Gram_rows"]
    assert len(gram) == 630
    assert [r[:2] for r in gram] == [[i, j] for i in range(35) for j in range(i, 35)]
    masks = [0] * 1214
    for i, j, quota, support in gram:
        assert type(quota) is int and quota >= 0
        assert len(support) == len(set(support))
        assert all(type(a) is int and 0 <= a < 1214 for a in support)
        if i == j:
            for a in support:
                masks[a] |= 1 << i
    for i, j, quota, support in gram:
        expected = [a for a, h in enumerate(masks) if h & (1 << i) and h & (1 << j)]
        assert support == expected
    zeros = cert["prior_zero_columns"]
    assert zeros == inputs["seed"]["seed_zero_columns"]
    assert len(zeros) == len(set(zeros)) == 99
    zero_set = set(zeros)
    covers = []
    for saved in inputs["covers"]["proofs"]:
        values = [0] * 1214
        rhs = 0
        for row in saved["original_Gram_row_sum"]:
            i, j, quota, support = gram[row["original_native_row"]]
            assert [i, j] == row["core_pair"] and quota == row["quota"]
            assert row["coefficient"] == 1
            rhs += quota
            for a in support:
                values[a] += 1
        assert values == saved["full_original_integer_coefficients"]
        assert rhs == saved["original_right_hand_side"] and rhs % 2 == 1
        odd = [a for a, value in enumerate(values) if a not in zero_set and value % 2]
        assert odd == saved["cover_support"] and len(odd) == 42
        assert saved["cover_lower_bound"] == 1
        covers.append({"odd_support": odd, "odd_right_hand_side": rhs})
    assert len(covers) == 2
    H2 = set(cert["H2_support"])
    new = set(range(1062, 1068)) | set(range(1125, 1131))
    assert cert["new_zero_columns"] == sorted(new)
    assert sorted(H2) == covers[1]["odd_support"]
    assert len(H2) == 42 and len(new) == 12
    assert H2.isdisjoint(new) and H2.isdisjoint(zero_set) and new.isdisjoint(zero_set)
    coefficients = [0] * 1214
    rhs = 0
    records = cert["original_Gram_combination"]
    identifiers = [r["original_native_row"] for r in records]
    assert len(records) == 42 and identifiers == sorted(set(identifiers))
    for row in records:
        i, j, quota, support = gram[row["original_native_row"]]
        assert [i, j] == row["core_pair"] and quota == row["quota"]
        multiplier = row["multiplier"]
        assert type(multiplier) is int and multiplier != 0
        rhs += multiplier * quota
        for a in support:
            coefficients[a] += multiplier
    assert rhs == cert["original_Gram_right_hand_side"] == 1
    assert coefficients == cert["full_original_coefficients"]
    removed = [[a, coefficients[a]] for a in zeros if coefficients[a]]
    assert removed == cert["known_zero_terms"]
    for a in range(1214):
        if a not in zero_set:
            assert coefficients[a] == (a in H2) + 2 * (a in new)
    assert cert["all_zero_columns"] == sorted(zero_set | new)
    assert not cert["case4_excluded"]
    return {
        "status": "PASS: source review and independent original-row arithmetic",
        "subject": {"path": SUBJECT, "sha256": SUBJECT_SHA},
        "certificate": {"path": CERTIFICATE, "sha256": CERTIFICATE_SHA},
        "input_bindings": {k: cert["input_bindings"][k] for k in ("native", "seed", "covers")},
        "original_Gram_rows_checked": 630,
        "signed_Gram_rows_expanded": 42,
        "original_coordinates_checked": 1214,
        "known_zero_terms_removed": removed,
        "remaining_coefficient_histogram": dict(sorted(Counter(coefficients[a] for a in range(1214) if a not in zero_set).items())),
        "right_hand_side": 1,
        "new_zero_columns": sorted(new),
        "H2_support": sorted(H2),
        "prior_zero_count": 99,
        "new_zero_count": 12,
        "total_zero_count": 111,
        "independent_conclusion": "sum_H2(x) + 2 sum_new12(x) = 1 on the certified face; nonnegative integrality gives each new x = 0 and sum_H2(x) = 1.",
        "real_relaxation_caveat": "Without integrality the identity alone does not force the twelve zeros. The additional proved H2 >= 1 cover does.",
        "prior_99_zero_derivation_repeated": False,
        "both_saved_odd_cover_row_identities_checked": True,
        "subject_source_imported": False,
        "optimizer_calls": 0,
        "matrix_regeneration": False,
        "case4_exclusion_claimed": False,
        "reviewer_source_sha256": digest(Path(__file__).read_bytes()),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    started = time.monotonic()
    result = audit(args.root)
    result["seconds"] = time.monotonic() - started
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))

