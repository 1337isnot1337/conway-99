"""Exact parent-row implication check for the 128 saved greedy clique rows.

After proved coordinate zeros, a positive multiple of a target row may
be componentwise bounded above by an existing inequality. Nonnegative
coordinates then prove the implication. Equalities permit both signs.
Unmatched rows are reported without an independence claim.
"""
import argparse
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[2]
BASE = "experiments/logs/root-prism-free/"
INPUTS = {
    "model": (BASE+"f0-schur-path-model03.json.gz", "ad046fc05a4247a081b3cabb16693682fa5539ff557dd7b599f3c3a63e7303dd"),
    "cliques": (BASE+"f0-local-clique-scan01.json", "f19b34f16e23f3cef0ec764935c5d43fb0fda638fb80e1c074b15ef3207cc9c5"),
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def prove():
    loaded = {}
    for name, (path, expected) in INPUTS.items():
        raw = (ROOT/path).read_bytes(); assert sha(raw) == expected
        loaded[name] = json.loads(gzip.decompress(raw) if path.endswith(".gz") else raw)
    matrix = loaded["model"]["matrix"]
    zeros = {}
    for i, row in enumerate(matrix["equalities"]):
        if row["rhs"] == 0 and len(row["terms"]) == 1:
            j, c = row["terms"][0]; assert type(c) is int and c != 0
            zeros.setdefault(j, i)
    candidates = {}
    for family, signs in (("equalities", (1, -1)), ("inequalities", (1,))):
        for i, row in enumerate(matrix[family]):
            for sign in signs:
                if sign*row["rhs"] != 0:
                    continue
                coefficients = {j: sign*c for j, c in row["terms"] if j not in zeros and c}
                negative = [(j, c) for j, c in coefficients.items() if c < 0]
                if len(negative) != 1 or not 0 <= negative[0][0] < 42:
                    continue
                center, negative_coefficient = negative[0]
                candidates.setdefault(center, []).append((family, i, sign, -negative_coefficient, coefficients))
    certificates, unmatched = [], []
    for index, row in enumerate(loaded["cliques"]["rows"]):
        target = dict(row["terms"])
        negative = [(j, c) for j, c in target.items() if c < 0]
        assert len(negative) == 1 and negative[0][1] == -1 and row["rhs"] == 0
        assert not set(target).intersection(zeros)
        accepted = None
        for family, i, sign, multiplier, coefficients in candidates.get(negative[0][0], []):
            difference = {j: coefficients.get(j, 0)-multiplier*target.get(j, 0)
                          for j in set(coefficients) | set(target)}
            if any(c < 0 for c in difference.values()):
                continue
            parent = matrix[family][i]
            # An independently inspectable coefficient identity:
            # sign*parent = multiplier*target + nonnegative_box_terms
            #               + proved_zero_terms.
            residual = [[j, c] for j, c in sorted(difference.items()) if c]
            removed = [[j, sign*c, zeros[j]] for j, c in parent["terms"] if j in zeros]
            reconstructed = Counter({j: multiplier*c for j, c in row["terms"]})
            reconstructed.update(dict(residual))
            reconstructed.update({j: c for j, c, proof in removed})
            assert {j: c for j, c in reconstructed.items() if c} == {j: sign*c for j, c in parent["terms"] if c}
            assert all(c >= 0 for j, c in residual) and multiplier > 0
            accepted = {"target_row": index, "parent_family": family, "parent_row": i,
                        "parent_orientation": sign, "positive_target_multiplier": multiplier,
                        "nonnegative_coordinate_residual": residual,
                        "proved_zero_terms_and_equality_rows": removed,
                        "exact_equality_after_zero_substitution": family == "equalities" and not residual}
            break
        if accepted is None:
            unmatched.append(index)
        else:
            certificates.append(accepted)
    return {"status": "COMPLETE_EXACT_LISTED_PARENT_IMPLICATION_CHECK",
            "source_sha256": sha(Path(__file__).read_bytes()),
            "inputs": {k: {"path": p, "sha256": h} for k, (p, h) in INPUTS.items()},
            "target_rows": len(loaded["cliques"]["rows"]),
            "implied_rows": len(certificates), "unmatched_rows": unmatched,
            "zero_equations_used_as_available_premises": len(zeros),
            "exact_parent_equality_rows": sum(c["exact_equality_after_zero_substitution"] for c in certificates),
            "certificates": certificates, "optimizer_calls": 0,
            "scope": "Only the128 retained greedy clique rows; an unmatched row is not proved independent. Numerical gaps are not used in the implication proof."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--record", type=Path, required=True)
    parser.add_argument("--replay", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(); started = time.monotonic()
    assert not args.output.exists()
    result = prove()
    if args.replay:
        assert result == json.loads(args.record.read_bytes())
    else:
        assert not args.record.exists(); args.record.write_text(json.dumps(result, indent=2)+"\n")
    summary = {k: v for k, v in result.items() if k != "certificates"}
    summary["record_sha256"] = sha(args.record.read_bytes())
    summary["seconds"] = time.monotonic()-started
    summary["replay"] = args.replay
    args.output.write_text(json.dumps(summary, indent=2)+"\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
