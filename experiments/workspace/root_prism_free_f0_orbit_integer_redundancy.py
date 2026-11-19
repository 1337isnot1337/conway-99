"""Original Gram/RLT equality certificate for the sole retained orbit cut.

The three disjoint Gram supports make L=N6+N7=3. Summing their products
with all24 selectors in the union gives R=L^2-3L=0. The candidate row is
2*(L-3)-R/2=0, so its positive dyadic gap is numerical equality residual.
"""
from collections import Counter
from fractions import Fraction
import gzip
import hashlib
import json
from math import gcd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOGS = ROOT / "experiments/logs/root-prism-free"
INPUTS = {
    "scan": ("f0-orbit-integer-quadratics-scan01.json.gz", "5491abae33fb6faa79b006fe8b789df801ad289ec42167d3c53ec9041627aa51"),
    "domain": ("f0-boolean-fractional-model.json.gz", "703206929c9c85a40ac4ddcbfb1708c716c288482cf50c77a32249404e35b782"),
    "moments": ("f0-second-moments-preparation02.json.gz", "404d91da35c798ba248887c22a7500957947e24b71d5197dc44432460e6d219e"),
    "reduced": ("f0-second-moments-reduced-model.json.gz", "73a50b431ac69ad57e10cff9aabe5c0b7d69ee075e95710b461f62b33fe2bbcf"),
    "parent": ("f0-joint-psd-clique-model01.json.gz", "43fff7283308cc2ed1be0936fae4b4f7b264c5961f6e6a4c9a81d123836e4f69"),
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read(name):
    path, expected = INPUTS[name]
    raw = (LOGS / path).read_bytes()
    assert sha(raw) == expected
    return json.loads(gzip.decompress(raw))


def normalized(terms, rhs):
    terms = sorted((j, c) for j, c in terms.items() if c)
    divisor = gcd(abs(rhs), *(abs(c) for j, c in terms)) or 1
    if (terms[0][1] if terms else rhs) < 0:
        divisor = -divisor
    return (tuple((j, c // divisor) for j, c in terms), rhs // divisor), divisor


def main():
    scan, domain, moments, reduced, parent = [read(name) for name in INPUTS]
    assert len(scan["cuts"]) == 1 and len(scan["attempts"]) == 1764
    cut = scan["cuts"][0]
    assert cut["form"] == [[6, 1], [7, 1]] and cut["k"] == 3
    validation = domain["validation"]
    xmap = {a: i for i, orbit in enumerate(validation["selector_orbits"]) for a in orbit}
    selected = sorted(validation["selector_orbits"][6] + validation["selector_orbits"][7])
    assert len(selected) == len(set(selected)) == 24
    source_rows = moments["original_selector_equalities"]
    gram = [i for i, row in enumerate(source_rows)
            if row["family"] == "Gram" and row["core_pair"] in ([0, 5], [1, 3], [2, 4])]
    assert len(gram) == 3
    assert all(source_rows[i]["quota"] == 1 and len(source_rows[i]["support"]) == 8 for i in gram)
    assert sorted(a for i in gram for a in source_rows[i]["support"]) == selected
    reverse = {old: new for new, old in enumerate(reduced["kept_original_variables"])}
    fixed = {j for j, proof in reduced["fixed_zero_original_variables"]}
    assert len(reverse) == 15200 and len(fixed) == 389
    eqs = parent["matrix"]["equalities"]
    index = {}
    for i, row in enumerate(eqs):
        key, scale = normalized(dict(row["terms"]), row["rhs"])
        index.setdefault(key, (i, scale))
    multipliers = Counter()
    witnesses = []

    def match(terms, rhs, weight, origin):
        key, scale = normalized(terms, rhs)
        if not key[0]:
            assert not key[1]
            witnesses.append({"origin": origin, "zero_after389_proved_substitutions": True})
            return
        assert key in index, (origin, key)
        row_id, parent_scale = index[key]
        factor = Fraction(scale, parent_scale)
        assert all(Fraction(terms.get(j, 0)) == factor * dict(eqs[row_id]["terms"]).get(j, 0)
                   for j in set(terms) | dict(eqs[row_id]["terms"]).keys())
        assert Fraction(rhs) == factor * eqs[row_id]["rhs"]
        multipliers[row_id] += weight * factor
        witnesses.append({"origin": origin, "parent_equality_row": row_id,
                          "exact_factor": str(factor), "combination_weight": str(weight)})

    for row_id in gram:
        row = source_rows[row_id]
        match(Counter(xmap[a] for a in row["support"]), row["quota"], Fraction(2),
              {"original_Gram_row": row_id, "core_pair": row["core_pair"]})
        for a in selected:
            terms = Counter({xmap[a]: -row["quota"]})
            for b in row["support"]:
                if a == b:
                    terms[xmap[a]] += 1
                else:
                    u, v = sorted((a, b))
                    pair_id = u * (959 - u) // 2 + v - u - 1
                    old = 5847 + moments["pair_to_orbit"][pair_id]
                    if old not in fixed:
                        terms[reverse[old]] += 1
            match(terms, 0, Fraction(-1, 2),
                  {"original_Gram_row": row_id, "anchor": a, "full_RLT_row": 172 * a + row_id})
    combined, rhs = Counter(), Fraction(0)
    for row_id, factor in multipliers.items():
        for j, c in eqs[row_id]["terms"]:
            combined[j] += factor * c
        rhs += factor * eqs[row_id]["rhs"]
    target = dict(cut["row"]["terms"])
    assert all(combined.get(j, 0) == target.get(j, 0) for j in range(15200))
    assert rhs == cut["row"]["rhs"] == 6
    result = {"status": "PASS: the sole retained orbit-population candidate is an existing exact equality consequence",
              "source_sha256": sha(Path(__file__).read_bytes()),
              "inputs": {k: {"path": str(Path("experiments/logs/root-prism-free") / p), "sha256": h}
                         for k, (p, h) in INPUTS.items()},
              "selected_orbit_union": [6, 7], "literal_support": selected,
              "original_Gram_rows": gram, "original_lifted_rows": 72,
              "population_identity": "L=3", "lifted_identity": "R=L^2-3L=2P-2L=0",
              "target_identity": "3L-P-6=2*(L-3)-R/2=0",
              "all_literal_to_parent_matches": witnesses,
              "parent_equality_multipliers": [[i, str(c)] for i, c in sorted(multipliers.items()) if c],
              "all15200_target_coefficients_checked": True, "rhs_checked": True,
              "dyadic_gap": str(Fraction(int(cut["exact_gap_numerator"]), int(scan["common_denominator"]))),
              "new_nonredundant_rows_retained": 0, "optimizer_calls": 0,
              "conclusion": "The complete1764-form scan gives no new retained inequality; one tiny equality residual is explained exactly."}
    out = LOGS / "f0-orbit-integer-quadratics-scan01-redundancy.json"
    with out.open("x") as handle:
        json.dump(result, handle, indent=2)
        handle.write("\n")
    print(json.dumps({"status": result["status"], "sha256": sha(out.read_bytes()),
                      "parent_rows": len(result["parent_equality_multipliers"]),
                      "exact_gap": result["dyadic_gap"]}, indent=2))


if __name__ == "__main__":
    main()
