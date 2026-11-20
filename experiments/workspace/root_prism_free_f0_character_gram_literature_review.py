"""Independent retained-witness review of the character-Gram appendix.

The subject source is not imported. The 32 saved integer combinations are
expanded directly in the original 480 selector coordinates. Rational ranks
are checked with Fraction, without repeating the 516 projection census.
"""
from collections import Counter
from fractions import Fraction
import gzip
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = "experiments/logs/root-prism-free/"
BINDINGS = {
    "subject": ("experiments/workspace/root_prism_free_f0_character_gram.py",
        "5de0969699b445286b437deec69fb31cfcdab22400c6fbfa959b488117808c8b"),
    "record": (BASE+"f0-character-Gram-equalities01.json",
        "084764b528f9a75269c8e21bb0b55b480a552022b024db72a4357aca083770c7"),
    "cold": (BASE+"f0-character-Gram-equalities01-cold.json",
        "482ccc5f26d4668ef1f45fab6200eeb2328b92e0b949b7e026052c1354cd1f7f"),
    "characters": (BASE+"f0-character-populations01.json.gz",
        "139d06a3383f8fc79d677972ce052ce29966e8b3406e7d1e7d1077aea7c2cef6"),
    "character_review": (BASE+"f0-character-populations-literature-review.json",
        "f5164ac7a59cd75c9fdd3c74364e772701038c9c8347c15ae9b6c7990c110149"),
    "moments": (BASE+"f0-second-moments-preparation02.json.gz",
        "404d91da35c798ba248887c22a7500957947e24b71d5197dc44432460e6d219e"),
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def rank(matrix):
    rows = [[Fraction(x) for x in row] for row in matrix]
    pivots = 0
    for column in range(len(rows[0])):
        found = next((i for i in range(pivots, len(rows)) if rows[i][column]), None)
        if found is None:
            continue
        rows[pivots], rows[found] = rows[found], rows[pivots]
        divisor = rows[pivots][column]
        rows[pivots] = [x/divisor for x in rows[pivots]]
        for i in range(pivots+1, len(rows)):
            multiplier = rows[i][column]
            if multiplier:
                rows[i] = [x-multiplier*y for x, y in zip(rows[i], rows[pivots])]
        pivots += 1
        if pivots == len(rows):
            break
    return pivots


def main():
    data = {}
    for key, (name, expected) in BINDINGS.items():
        raw = (ROOT/name).read_bytes()
        assert sha(raw) == expected, name
        if key != "subject":
            data[key] = json.loads(gzip.decompress(raw) if name.endswith(".gz") else raw)
    record, cold, chars, moments = [data[k] for k in ("record", "cold", "characters", "moments")]
    assert record["source_sha256"] == cold["source_sha256"] == BINDINGS["subject"][1]
    assert cold["record_sha256"] == BINDINGS["record"][1] and cold["status"].startswith("PASS")
    equations = record["equations"]
    assert len(equations) == record["retained_equations"] == 32
    assert [e["equation"] for e in equations] == list(range(32))
    originals = moments["original_selector_equalities"]
    assert len(originals) == 172
    populations = {p["signed_population"]: p for p in chars["signed_populations"]}
    checks = []
    matrices = {}
    for character in (1, 2, 3):
        ids = [p["signed_population"] for p in chars["signed_populations"] if p["character"] == character]
        index = {j: i for i, j in enumerate(ids)}
        dense = []
        for equation in equations:
            if equation["character"] != character:
                continue
            left, rhs = [0]*480, 0
            combination = equation["original_Gram_integer_combination"]
            assert combination == sorted(combination) and len({i for i, c in combination}) == len(combination)
            for i, multiplier in combination:
                assert type(i) is type(multiplier) is int and 0 <= i < 172 and multiplier
                row = originals[i]
                rhs += multiplier*row["quota"]
                for a in row["support"]:
                    left[a] += multiplier
            terms, right, row = equation["signed_population_terms"], [0]*480, [0]*len(ids)
            assert terms == sorted(terms) and len({j for j, c in terms}) == len(terms)
            for j, coefficient in terms:
                assert type(j) is type(coefficient) is int and coefficient
                p = populations[j]
                assert p["character"] == character
                row[index[j]] = coefficient
                for a, sign in zip(p["literal_selectors"], p["signs"]):
                    right[a] += coefficient*sign
            divisor = equation["primitive_signed_divisor"]
            assert type(divisor) is int and divisor
            assert rhs == equation["rhs"] == equation["original_rhs_checked"] == 0
            assert left == [divisor*x for x in right]
            assert math.gcd(*row) == 1 and next(x for x in row if x) > 0
            dense.append(row)
            checks.append({"equation": equation["equation"], "character": character,
                           "original_row_count": len(combination), "signed_divisor": divisor,
                           "literal_coefficients_checked": 480, "homogeneous_rhs_checked": True})
        saved = next(r for r in record["character_ranks"] if r["character"] == character)
        assert dense == saved["dense_primitive_matrix"]
        computed = rank(dense)
        assert computed == saved["exact_rational_rank"]
        matrices[character] = {"rows": len(dense), "columns": len(ids), "rational_rank": computed}
    assert [matrices[c]["rational_rank"] for c in (1, 2, 3)] == [9, 9, 10]
    mapping = record["original_row_projection_map"]
    assert len(mapping) == 516
    assert {(r["character"], r["original_Gram_row"]) for r in mapping} == {
        (c, i) for c in (1, 2, 3) for i in range(172)}
    result = {
        "status": "PASS: character-Gram source review and 32 independent literal witnesses",
        "reviewer_source_sha256": sha(Path(__file__).read_bytes()),
        "bindings": {k: {"path": p, "sha256": h} for k, (p, h) in BINDINGS.items()},
        "entire134_line_subject_source_read": True,
        "source_and_mathematical_checks": [
            "Each transported support is looked up as an original equality with the same quota. Duplicate identical rows may use the first occurrence without changing the equation.",
            "The nontrivial character has sum zero, so the signed sum of the 12 transported right-hand sides is zero.",
            "For a compatible signing, the coefficient on orbit O_i is (12/|O_i|) times the signed intersection with the original support. This follows by summing the stabilizer coset mapping a selected orbit point to the anchor.",
            "Incompatible stabilizers give zero projection. The source compares all 480 expanded coefficients, including these unsupported orbits.",
            "A nonzero signed gcd may be divided out of a homogeneous equation. Negative divisors only choose the canonical first-positive orientation.",
            "The saved equations use the signed-population namespace, not the count-variable namespace. No graph automorphism or orbit equality of literal selectors is assumed.",
        ],
        "independent_retained_witnesses": checks,
        "literal_coefficient_checks": 32*480,
        "homogeneous_rhs_checks": 32,
        "independent_Fraction_ranks": matrices,
        "complete_projection_map_metadata_checked": 516,
        "strength_scope": "These are useful explicit propagation equations. With complete original selector-RLT equalities and the new same-character rank-one identities C=L L^T, they already follow from alpha^T C alpha=(alpha^T L)^2=0. Independent additional strength is not claimed.",
        "subject_imported": False, "subject_executed": False,
        "all516_projection_census_repeated": False, "Flint_rank_used_in_this_review": False,
        "native_binary_query_repeated": False, "previous_controls_repeated": False,
        "optimizer_calls": 0, "F0_excluded": False,
    }
    path = ROOT/(BASE+"f0-character-Gram-literature-review.json")
    assert not path.exists()
    path.write_text(json.dumps(result, indent=2)+"\n")
    print(json.dumps({"status": result["status"], "source_sha256": result["reviewer_source_sha256"],
                      "report_sha256": sha(path.read_bytes()), "literal_checks": 32*480,
                      "ranks": [matrices[c]["rational_rank"] for c in (1, 2, 3)]}, indent=2))


if __name__ == "__main__":
    main()
