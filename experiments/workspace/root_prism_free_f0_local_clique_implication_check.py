"""Independent coefficient check of saved clique implication certificates."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[2]
BASE = "experiments/logs/root-prism-free/"
INPUTS = {
    "model": (BASE+"f0-schur-path-model03.json.gz", "ad046fc05a4247a081b3cabb16693682fa5539ff557dd7b599f3c3a63e7303dd"),
    "rows": (BASE+"f0-local-clique-scan01.json", "f19b34f16e23f3cef0ec764935c5d43fb0fda638fb80e1c074b15ef3207cc9c5"),
    "proof": (BASE+"f0-local-clique-scan01-redundancy.json", "909fcb07b6c161c0f13feaa49c3a9eeb2051ac2fddae90dbbdf4f2f50f508af5"),
}


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(); started = time.monotonic()
    assert not args.output.exists()
    data = {}
    for key, (path, expected) in INPUTS.items():
        raw = (ROOT/path).read_bytes(); assert digest(raw) == expected
        data[key] = json.loads(gzip.decompress(raw) if path.endswith(".gz") else raw)
    matrix = data["model"]["matrix"]
    assert matrix["variables"] == 15200 and matrix["lower"] == 0
    rows = data["rows"]["rows"]
    proof = data["proof"]
    assert len(rows) == proof["target_rows"] == proof["implied_rows"] == 128
    assert proof["unmatched_rows"] == []
    covered = set(); exact_equalities = 0; checked_coefficients = 0
    for certificate in proof["certificates"]:
        i = certificate["target_row"]
        assert type(i) is int and 0 <= i < len(rows) and i not in covered
        covered.add(i)
        target = rows[i]; kind = certificate["parent_family"]
        assert kind in ("equalities", "inequalities")
        parent = matrix[kind][certificate["parent_row"]]
        sign = certificate["parent_orientation"]
        scale = certificate["positive_target_multiplier"]
        assert sign in (1, -1) and (kind == "equalities" or sign == 1)
        assert type(scale) is int and scale > 0
        assert parent["rhs"] == target["rhs"] == 0
        difference = [0]*15200
        for j, coefficient in parent["terms"]:
            difference[j] += sign*coefficient
        for j, coefficient in target["terms"]:
            difference[j] -= scale*coefficient
        for j, coefficient in certificate["nonnegative_coordinate_residual"]:
            assert type(coefficient) is int and coefficient >= 0
            difference[j] -= coefficient
        for j, coefficient, reason_row in certificate["proved_zero_terms_and_equality_rows"]:
            equation = matrix["equalities"][reason_row]
            assert equation["rhs"] == 0 and len(equation["terms"]) == 1
            variable, multiplier = equation["terms"][0]
            assert variable == j and type(multiplier) is int and multiplier != 0
            difference[j] -= coefficient
        assert all(coefficient == 0 for coefficient in difference)
        checked_coefficients += len(difference)
        equality = kind == "equalities" and not certificate["nonnegative_coordinate_residual"]
        assert certificate["exact_equality_after_zero_substitution"] == equality
        exact_equalities += equality
    assert covered == set(range(128)) and exact_equalities == 128
    report = {
        "status": "PASS: all128 retained clique rows are existing exact equalities on the proved zero face",
        "source_sha256": digest(Path(__file__).read_bytes()),
        "inputs": {k: {"path": p, "sha256": h} for k, (p, h) in INPUTS.items()},
        "retained_rows_checked": 128, "coefficients_checked": checked_coefficients,
        "exact_parent_equality_consequences": exact_equalities,
        "owner_source_imported": False, "clique_search_repeated": False,
        "optimizer_calls": 0, "seconds": time.monotonic()-started,
        "scope": "The128 retained rows provide no new restriction. No independence claim is made for unretained candidates or unsearched cliques.",
    }
    args.output.write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
