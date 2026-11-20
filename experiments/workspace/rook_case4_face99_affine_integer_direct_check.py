"""Artifact-only native-equality check of a full signed integer vector.

Standard library only. This checker imports no construction, elimination,
optimizer, or solver source. It does not accept a binary-incidence claim.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import time

ROOT = Path(__file__).resolve().parents[2]
BASE = "experiments/logs/grids-and-triangles/"
INPUTS = {
    "native": (BASE+"complement-rook-35core-case0004-native-cpsat-model.json",
        "a9004e97a2d166bf8b162609cfb538eae0dd4d26942b6df5119b6a88d65ec476"),
    "zeros": (BASE+"rook-case4-transportation-seed-certificate.json",
        "64d8e375280bc067097913de2dd6e2995c19de2a4807f63cecdcd80b811a85cf"),
    "rational_control": (BASE+"rook-case4-face99-basis-run01/candidate.json",
        "0b627484317e65562500fbbbbd594e4a95dbfa809576fae52f6c7ccdbe7191e7"),
}
PRIMARY_SHA = "5a6af30f47826df629a3795ceea0a0a91b853cf8149860355ce1bd17ac0094b2"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def number(value):
    if type(value) is int:
        return value
    assert isinstance(value, str) and re.fullmatch(r"0|-?[1-9][0-9]*", value)
    return int(value)


def inputs():
    loaded = {}
    for key, (relative, expected) in INPUTS.items():
        raw = (ROOT/relative).read_bytes()
        assert sha(raw) == expected
        loaded[key] = json.loads(raw)
    native = loaded["native"]["primary_inventory"]
    raw = json.dumps(native, sort_keys=True, separators=(",", ":")).encode()
    assert sha(raw) == PRIMARY_SHA
    assert loaded["native"]["complete"] and loaded["native"]["case_index"] == 4
    zeros = loaded["zeros"]["seed_zero_columns"]
    assert zeros == sorted(set(zeros)) and len(zeros) == 99
    assert all(type(a) is int and 0 <= a < 1214 for a in zeros)
    return native, zeros, loaded["rational_control"]


def check(native, zeros, values, denominator):
    assert len(values) == 1214 and all(type(v) is int for v in values)
    assert type(denominator) is int and denominator > 0
    assert max([denominator.bit_length()]+[abs(v).bit_length() for v in values]) <= 4096
    assert all(values[a] == 0 for a in zeros)
    gram = native["Gram_rows"]
    assert [(i, j) for i, j, quota, support in gram] == [(i, j) for i in range(35) for j in range(i, 35)]
    masks = [0]*1214
    for i, j, quota, support in gram:
        assert type(quota) is int and quota >= 0
        assert support == sorted(set(support)) and all(type(a) is int and 0 <= a < 1214 for a in support)
        if i == j:
            for a in support:
                masks[a] |= 1 << i
        assert sum(values[a] for a in support) == quota*denominator, ("Gram", i, j)
    for i, j, quota, support in gram:
        assert support == [a for a, mask in enumerate(masks) if mask >> i & 1 and mask >> j & 1]
    assert len(native["original_signature_rows"]) == 186
    assert len(native["triple_rows"]) == 1365
    assert len(native["Gram_conflict_clauses"]) == 30
    # These three families have unequal endpoints 0 and1. They contribute
    # no equality to this affine task, even if a chosen point saturates one.
    cuts = native["uncapped_integer_cuts"]
    assert len(cuts) == 60
    empty = []
    for index, cut in enumerate(cuts):
        target, demand = cut["target_column"], cut["positive_demand"]
        assert type(target) is int and 0 <= target < 1214
        assert type(demand) is int and demand > 0
        assert all(type(a) is int and 0 <= a < 1214 and type(w) is int and w > 0
                   for a, w in cut["positive_terms"])
        # The native upper endpoint is sum of the positive weights. It
        # equals its zero lower endpoint exactly for empty positive support.
        if not cut["positive_terms"]:
            assert -demand*values[target] == 0
            empty.append({"cut_index": index, "target_column": target, "demand": demand})
    assert len(empty) == 2
    return {"original_coordinates": 1214, "Gram_entries": 630,
        "empty_support_row_equalities": empty, "original_equality_rows": 632,
        "proved_zero_coordinates": 99, "all_supports_rebuilt_from_Gram_diagonals": True,
        "common_denominator": str(denominator), "integral": denominator == 1,
        "negative_coordinates": sum(v < 0 for v in values),
        "positive_coordinates": sum(v > 0 for v in values),
        "zero_coordinates": sum(v == 0 for v in values),
        "binary_or_nonnegative_feasibility_claimed": False,
        "inequality_or_cover_feasibility_claimed": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--point", type=Path)
    parser.add_argument("--control", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists() and ((args.point is None) != (not args.control))
    started = time.monotonic()
    native, zeros, rational = inputs()
    if args.control:
        kept = [a for a in range(1214) if a not in set(zeros)]
        proposed = list(map(number, rational["extended_numerators"]))
        assert len(proposed) == 1116
        values = [0]*1214
        for a, value in zip(kept, proposed[:-1]):
            values[a] = value
        denominator = number(rational["common_denominator"])
        checked = check(native, zeros, values, denominator)
        rejected = 0
        for a in (kept[0], zeros[0]):
            bad = values.copy(); bad[a] += 1
            try:
                check(native, zeros, bad, denominator)
            except AssertionError:
                rejected += 1
        assert rejected == 2
        report = {"status": "PASS: saved rational control and two forged vectors rejected; no integer point tested",
                  "forged_vectors_rejected": rejected, "exact_check": checked}
    else:
        raw = args.point.read_bytes(); point = json.loads(raw)
        assert point["common_denominator"] == "1"
        values = list(map(number, point["integers"]))
        checked = check(native, zeros, values, 1)
        report = {"status": "PASS: direct signed-integer affine certificate", "point_sha256": sha(raw),
                  "exact_check": checked}
    report.update(source_sha256=sha(Path(__file__).read_bytes()),
        input_bindings={k: {"path": p, "sha256": h} for k, (p, h) in INPUTS.items()},
        constructor_or_solver_imported=False, elimination_calls=0, optimizer_calls=0,
        case4_excluded=False, seconds=time.monotonic()-started)
    args.output.write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
