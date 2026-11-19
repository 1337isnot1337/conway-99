"""A fixed small norm-six profile experiment, with no global count query.

Preparation selects at most three pairs of frozen profiles on selector orbits
2 and 3. Scan mode exhausts only their declared four-character-coset count
compositions. A locally rejected composition is not a full-model point.
"""
import argparse
from collections import Counter
import gzip
from hashlib import sha256
from itertools import product
import json
from math import comb, isqrt
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "experiments/logs/root-prism-free"
INPUTS = {
    "scope": ("f0-two-dimensional-moments-scope01.json", "948e256945fc817cc75ea46c969c055b21e61832a4f2177c481884e73338223f"),
    "inverse": ("f0-character-literal-lift-preparation01.json.gz", "241cd14c61b465025c72ffcaa65af8e5c48e9e5a0eda7ea7d252e9d74b22db1e"),
    "characters": ("f0-character-populations01.json.gz", "139d06a3383f8fc79d677972ce052ce29966e8b3406e7d1e7d1077aea7c2cef6"),
    "target_plan": ("f0-character-y-domain-overlay01/plan.json.gz", "4d3a13718cdac9fcf68b119a1cd1ba009edeb21c7257d4498d5ebdf18954acc4"),
    "target_preparation": ("f0-character-y-domain-overlay01/report.json", "a4a543b35bdd22357eef39524ff8015e0d4d274547c046205c806a5f52e92061"),
}
SCOPE_SOURCE = ("root_prism_free_f0_two_dimensional_moments.py", "31793743ba11fb56f42bcc9f383fe8b3268dae1cd8ebf6ec0271160a1d58d2fd")
TARGET_PROTO = "a738d318b6b8de471ee7383f1e6ea11949eed8f8ccf4892814fa2eac268ed153"
LIMITS = {"seconds_per_stage": 30, "maximum_profile_pairs": 3,
          "maximum_compositions_per_pair": 2160, "maximum_saved_examples_per_pair": 4,
          "maximum_raw_record_bytes": 4 << 20, "optimizer_calls": 0}
COSETS = [[1, 1, 1], [1, -1, -1], [-1, 1, -1], [-1, -1, 1]]


def sha(raw):
    return sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def tick(deadline):
    if time.monotonic() >= deadline:
        raise TimeoutError("small profile-pair stage deadline")


def read(key):
    name, expected = INPUTS[key]
    raw = (BASE/name).read_bytes()
    assert sha(raw) == expected
    return json.loads(gzip.decompress(raw) if name.endswith(".gz") else raw)


def contains(domain, value):
    return any(domain[i] <= value <= domain[i+1] for i in range(0, len(domain), 2))


def norm(v):
    a, b = v
    return 2*(a*a-a*b+b*b)


def inner(u, v):
    return 2*u[0]*v[0]-u[0]*v[1]-u[1]*v[0]+2*u[1]*v[1]


def square_status(a, b, c):
    d = a*c-b*b
    if d < 0:
        return "negative_determinant"
    if d % 3:
        return "not_divisible_by_three"
    q = d//3
    return "square_pass" if isqrt(q)**2 == q else "not_three_times_an_integer_square"


def controls():
    vectors = [[1, -1], [1, 2], [-2, -1], [-1, 1], [-1, -2], [2, 1]]
    values = Counter()
    for u, v in product(vectors, repeat=2):
        assert norm(u) == norm(v) == 6
        b = inner(u, v)
        area = u[0]*v[1]-u[1]*v[0]
        assert 36-b*b == 3*area*area and square_status(6, b, 6) == "square_pass"
        values[b] += 1
    assert sorted(values) == [-6, -3, 3, 6]
    assert square_status(6, 0, 6) == "not_three_times_an_integer_square"
    # This enumerates mass allocations, not selector subsets or count points.
    allocations = [(a, b, c, 9-a-b-c) for a in range(10) for b in range(10-a)
                   for c in range(10-a-b)]
    assert len(allocations) == 220
    maximum = max(__import__("math").prod(comb(m+2, 2) for m in row) for row in allocations)
    assert maximum == LIMITS["maximum_compositions_per_pair"]
    return {"norm_six_integer_vector_pairs": 36, "possible_integer_inner_products": sorted(values),
            "zero_inner_product_PSD_but_square_rejected": True,
            "mass_allocations_of_nine_into_four_parts": 220,
            "maximum_unrestricted_count_compositions": maximum,
            "local_count_compositions_scanned": 0}


def prepare(deadline):
    raw_source = (ROOT/"experiments/workspace"/SCOPE_SOURCE[0]).read_bytes()
    assert sha(raw_source) == SCOPE_SOURCE[1]
    scope, inverse, chars, plan, target = [read(k) for k in INPUTS]
    assert scope["source_sha256"] == SCOPE_SOURCE[1]
    assert target["outputs"]["target"]["raw_sha256"] == TARGET_PROTO
    assert target["outputs"]["plan"]["sha256"] == INPUTS["target_plan"][1]
    native_domains = plan["target_variable_domains"]
    assert len(native_domains) == 18444
    columns = scope["three_constructed_plus_columns"][:2]
    assert [c["selector_orbit"] for c in columns] == [2, 3]
    forms = {tuple(r["matrix_entry"]): r for r in scope["six_exact_entry_forms"]}
    tables = [inverse["inverse_tables"][i] for i in (2, 3)]
    signing = []
    pools, inventories = [], []
    for ci, (column, table) in enumerate(zip(columns, tables)):
        tick(deadline)
        assert table["literal_selectors"] == column["literal_selectors"]
        signs = [chars["signed_populations"][j] for j in table["signed_population_columns"]]
        assert [s["character"] for s in signs] == [1, 2, 3]
        assert all(s["literal_selectors"] == table["literal_selectors"] for s in signs)
        signing.append(signs)
        first_by_signed = {}
        norm_six = current_valid = 0
        for profile in table["profiles"]:
            values = profile["counts_and_signed_populations"]
            if values[0] != 3:
                continue
            count_values = dict(zip(table["count_columns"], values))
            diagonal = sum(c*count_values[j] for j, c in forms[ci, ci]["native_count_terms"])
            if diagonal != 6:
                continue
            norm_six += 1
            signed = values[len(table["count_columns"]):]
            specified = list(count_values.items()) + [(15941+j, v) for j, v in zip(table["signed_population_columns"], signed)]
            if not all(contains(native_domains[j], v) for j, v in specified):
                continue
            current_valid += 1
            vectors = []
            for mask in profile["local_masks"]:
                assert mask.bit_count() == 3
                vector = [sum(column["vectors"][a][k] for a in range(len(column["vectors"]))
                              if mask >> a & 1) for k in range(2)]
                assert norm(vector) == 6
                vectors.append(vector)
            first_by_signed.setdefault(tuple(signed), {
                "selector_orbit": table["selector_orbit"], "tuple_index": profile["tuple_index"],
                "count_columns": table["count_columns"], "signed_population_columns": table["signed_population_columns"],
                "counts_and_signed_populations": values, "local_masks": profile["local_masks"],
                "local_integer_vectors": vectors, "N": 3, "signed_values": signed, "Gram_diagonal": 6})
        pools.append(list(first_by_signed.values()))
        inventories.append({"selector_orbit": table["selector_orbit"], "norm_six_population_three_profiles": norm_six,
                            "profiles_in_current_native_domains": current_valid,
                            "first_profile_retained_per_distinct_signed_triple": len(first_by_signed)})
    assert all(pools)
    block = next(b for b in inverse["cross_pair_blocks"] if b["selector_orbits"] == [2, 3])
    assert len(block["original_pair_orbits"]) == 12
    old_to_new = {old: new for new, old in enumerate(inverse["new15038_to_original15589"])}
    cross_coeff = dict(forms[0, 1]["original_pair_terms"])
    pair_character, visits = {}, Counter()
    for a in range(12):
        for b in range(12):
            po = block["literal_pair_orbit_grid"][a][b]
            values = [signing[0][k]["signs"][a]*signing[1][k]["signs"][b] for k in range(3)]
            assert values in COSETS and (po not in pair_character or pair_character[po] == values)
            pair_character[po] = values; visits[po] += 1
    assert all(visits[po] == 12 for po in block["original_pair_orbits"])
    for po in block["original_pair_orbits"]:
        assert all(sum(x == po for x in row) == 1 for row in block["literal_pair_orbit_grid"])
        assert all(sum(row[b] == po for row in block["literal_pair_orbit_grid"]) == 1 for b in range(12))
    cross_variables = []
    for po in block["original_pair_orbits"]:
        native = old_to_new.get(5847+po)
        if native is None:
            assert po in inverse["original_zero_pair_orbits"]
        domain = [0, 0] if native is None else native_domains[native]
        effective = [v for v in range(4) if contains(domain, v)]
        cross_variables.append({"original_pair_orbit": po, "native_count_column": native,
            "current_exact_domain": domain, "values_after_N3_endpoint_activation": effective,
            "character_coset": pair_character[po], "Gram_cross_coefficient": cross_coeff[po]})
    coset_indices = [[i for i, v in enumerate(cross_variables) if v["character_coset"] == coset] for coset in COSETS]
    assert all(len(x) == 3 for x in coset_indices)
    possible = []
    for left, right in product(*pools):
        targets = [9] + [a*b for a, b in zip(left["signed_values"], right["signed_values"])]
        numerators = [targets[0]+sum(a*b for a, b in zip(coset, targets[1:])) for coset in COSETS]
        assert all(x >= 0 and x % 4 == 0 for x in numerators)
        masses = [x//4 for x in numerators]
        assert sum(masses) == 9
        bound = __import__("math").prod(comb(m+2, 2) for m in masses)
        assert bound <= 2160
        possible.append({"profiles": [left, right], "four_product_targets": targets,
                         "coset_masses": masses, "unrestricted_composition_bound": bound})
    possible.sort(key=lambda c: (-c["unrestricted_composition_bound"], c["profiles"][0]["tuple_index"], c["profiles"][1]["tuple_index"]))
    chosen, used_targets = [], set()
    for case in possible:
        key = tuple(case["four_product_targets"])
        if key not in used_targets:
            used_targets.add(key); case["case_index"] = len(chosen); chosen.append(case)
            if len(chosen) == LIMITS["maximum_profile_pairs"]:
                break
    assert 1 <= len(chosen) <= 3
    tick(deadline)
    return {"schema": "conway99.f0.norm-six-profile-pair-preparation.v1", "status": "PREPARED: no local composition scan",
        "source_sha256": sha(Path(__file__).read_bytes()), "inputs": INPUTS, "scope_source": SCOPE_SOURCE,
        "target_proto_sha256": TARGET_PROTO, "limits": LIMITS, "selector_orbits": [2, 3],
        "profile_inventory": inventories, "selection_rule": "First current-domain-valid N3/norm6 profile per signed triple; then descending unrestricted composition bound, tuple-index tie-break, distinct four-product target vectors; first at most three.",
        "cross_variables": cross_variables, "cosets": COSETS, "coset_variable_positions": coset_indices,
        "literal_pair_coefficient_checks": 144, "all_twelve_cross_orbits_are_literal_perfect_matchings": True,
        "cases": chosen,
        "total_unrestricted_composition_bound": sum(c["unrestricted_composition_bound"] for c in chosen),
        "controls": controls(), "production_count_candidates_evaluated": 0,
        "local_count_compositions_scanned": 0, "new_local_subset_censuses": 0, "optimizer_calls": 0,
        "declared_coarse_checks": ["both frozen local profiles including within-orbit counts and signed values",
            "all their currently specified native coordinate domains", "all twelve cross-coordinate exact domains and prior zeros",
            "each regular pair-orbit activation bound P<=min(Ni,Nj)=3",
            "one trivial and three signed cross-product equalities"],
        "scope": "A local count composition passing these declared checks is not a complete native/F0 count point. The square condition is necessary for literal realization; full-model nonredundancy is not asserted."}


def compositions(m):
    return [(a, b, m-a-b) for a in range(m+1) for b in range(m-a+1)]


def scan(preparation, deadline):
    records = []
    for case in preparation["cases"]:
        counts = Counter({key: 0 for key in ("unrestricted_compositions", "rejected_by_domains_zeros_or_activation",
            "coarse_pass", "negative_determinant", "not_divisible_by_three", "square_pass",
            "not_three_times_an_integer_square")})
        examples, stream = {}, sha256()
        groups = [compositions(m) for m in case["coset_masses"]]
        for parts in product(*groups):
            tick(deadline)
            counts["unrestricted_compositions"] += 1
            values = [0]*12
            for positions, part in zip(preparation["coset_variable_positions"], parts):
                for i, v in zip(positions, part):
                    values[i] = v
            if any(v not in rec["values_after_N3_endpoint_activation"] for v, rec in zip(values, preparation["cross_variables"])):
                counts["rejected_by_domains_zeros_or_activation"] += 1
                continue
            observed = [sum(values)] + [sum(v*rec["character_coset"][k] for v, rec in zip(values, preparation["cross_variables"])) for k in range(3)]
            assert observed == case["four_product_targets"]
            b = sum(v*rec["Gram_cross_coefficient"] for v, rec in zip(values, preparation["cross_variables"]))
            outcome = square_status(6, b, 6)
            counts["coarse_pass"] += 1; counts[outcome] += 1
            stream.update(canonical([values, b, outcome])+b"\n")
            if outcome != "square_pass" and outcome not in examples and len(examples) < LIMITS["maximum_saved_examples_per_pair"]:
                examples[outcome] = {"cross_counts_in_saved_order": values, "four_product_checks": observed,
                    "Gram": [[6, b], [b, 6]], "determinant": 36-b*b, "square_status": outcome,
                    "full_model_point_claimed": False}
        assert counts["unrestricted_compositions"] == case["unrestricted_composition_bound"]
        records.append({"case_index": case["case_index"], "counts": dict(counts),
                        "coarse_pass_stream_sha256": stream.hexdigest(),
                        "rejected_local_examples": [examples[k] for k in sorted(examples)]})
    return {"status": "COMPLETE: fixed local norm-six count-composition scan", "records": records,
            "all_prepared_cases_checked": True, "production_count_candidates_evaluated": 0,
            "optimizer_calls": 0, "new_local_subset_censuses": 0,
            "full_model_or_graph_feasibility_claimed": False, "full_model_nonredundancy_claimed": False}


def save(path, value):
    raw = canonical(value)+b"\n"
    assert len(raw) <= LIMITS["maximum_raw_record_bytes"]
    with path.open("xb") as out:
        out.write(raw)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "scan", "replay"))
    parser.add_argument("--preparation", type=Path)
    parser.add_argument("--record", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    start = time.monotonic(); deadline = start + LIMITS["seconds_per_stage"]
    if args.mode == "prepare":
        result = prepare(deadline)
    else:
        raw = args.preparation.read_bytes(); preparation = json.loads(raw)
        assert preparation["source_sha256"] == sha(Path(__file__).read_bytes())
        assert preparation["inputs"] == {k: list(v) for k, v in INPUTS.items()} and preparation["limits"] == LIMITS
        # The saved preparation binds every local profile, domain and coefficient.
        result = scan(preparation, deadline)
        result["preparation_sha256"] = sha(raw)
        result["source_sha256"] = sha(Path(__file__).read_bytes())
        if args.mode == "replay":
            old_raw = args.record.read_bytes(); saved = json.loads(old_raw)
            assert {k: v for k, v in saved.items() if k != "seconds"} == result
            result = {"status": "PASS: complete fixed local composition replay", "record_sha256": sha(old_raw),
                      "preparation_sha256": sha(raw), "source_sha256": sha(Path(__file__).read_bytes()),
                      "checked_cases": len(preparation["cases"]), "optimizer_calls": 0}
    tick(deadline)
    result["seconds"] = time.monotonic()-start
    save(args.output, result)
    print(json.dumps({k: result[k] for k in ("status", "seconds", "total_unrestricted_composition_bound") if k in result}))


if __name__ == "__main__":
    main()
