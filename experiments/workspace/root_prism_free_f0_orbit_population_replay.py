"""Independent literal replay of F0 count scaling and modular certificates.

Imports no model builder or modular helper. Rank lower bounds are checked
by ordinary sparse integer combinations of original rows; rank upper
bounds use a separate bit-plane reduction against the saved echelon rows.
"""
import argparse
from collections import Counter
import gzip
import hashlib
from itertools import combinations
import json
import math
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[2]
BASE = "experiments/logs/root-prism-free/"
INPUTS = {
    "preparation": (BASE + "f0-orbit-populations02-preparation.json", "239b8ae3651fe4fa327151e50a3214680079c6c07de589c6a27b43f20aeac34a"),
    "domains": (BASE + "f0-orbit-populations02-domains.json.gz", "4f079468530dba0746512cc4afce01666b2a63a2c8f35f66a4660a4fe3bab8ab"),
    "model": (BASE + "f0-orbit-populations02-model.json.gz", "aa46e2ca9df7a5838926385e06a86acda041c8455ac3422ae1e7b0a5c4ce5437"),
    "arithmetic": (BASE + "f0-orbit-populations02-arithmetic.json.gz", "78c2bd93cfd70f8129b628a291a6416e275188c692403c3cb4a3b9bce5ea9d2e"),
    "baseline": (BASE + "f0-boolean-fractional-model.json.gz", "703206929c9c85a40ac4ddcbfb1708c716c288482cf50c77a32249404e35b782"),
    "moments": (BASE + "f0-second-moments-preparation02.json.gz", "404d91da35c798ba248887c22a7500957947e24b71d5197dc44432460e6d219e"),
    "old_reduction": (BASE + "f0-second-moments-reduced-model.json.gz", "73a50b431ac69ad57e10cff9aabe5c0b7d69ee075e95710b461f62b33fe2bbcf"),
    "zero": (BASE + "f0-joint-psd-clique-zero-model01.json.gz", "da9b2062f9102a0487bc5fb88b2e009c1a228cbc2d2c39264135808bb3467ffb"),
    "parent": (BASE + "f0-joint-psd-clique-model01.json.gz", "43fff7283308cc2ed1be0936fae4b4f7b264c5961f6e6a4c9a81d123836e4f69"),
    "actions": (BASE + "f0-fractional-structural-recovery-input.json", "ef4018f26c48e9eb90bf544d41678778d71b587994096383023c8836e70bca6e"),
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def load(key):
    name, expected = INPUTS[key]
    raw = (ROOT / name).read_bytes()
    assert sha(raw) == expected, key
    return json.loads(gzip.decompress(raw) if name.endswith(".gz") else raw)


def tick(deadline):
    if time.monotonic() >= deadline:
        raise TimeoutError("120-second independent orbit-population replay")


def bits(value):
    while value:
        bit = value & -value
        yield bit.bit_length() - 1
        value ^= bit


def pair_id(a, b):
    a, b = sorted((a, b))
    assert a < b
    return a * (959 - a) // 2 + b - a - 1


def decode(planes, length, prime):
    out = {}
    for coefficient, plane in enumerate(planes, 1):
        assert 0 <= plane < (1 << length)
        for j in bits(plane):
            assert j not in out and coefficient < prime
            out[j] = coefficient
    return out


def encode(row, variables, prime):
    planes = [0] * (prime - 1)
    for j, c in row["terms"] + [[variables, row["rhs"]]]:
        coefficient = c % prime
        if coefficient:
            planes[coefficient - 1] |= 1 << j
    return tuple(planes)


def ternary_sum(a, b):
    # This xor/intersection expression is separate from the proposing helper.
    a1, a2 = a
    b1, b2 = b
    return (((a1 ^ b1) & ~(a2 | b2)) | (a2 & b2),
            ((a2 ^ b2) & ~(a1 | b1)) | (a1 & b1))


def check_field(rows, variables, record, deadline):
    prime = record["prime"]
    assert prime in (2, 3) and record["status"].startswith("CONSISTENT:")
    assert record["processed_equalities"] == record["total_equalities"] == len(rows)
    point = record["point"]
    assert len(point) == variables and all(type(v) is int and 0 <= v < prime for v in point)
    for row in rows:
        assert (sum(c * point[j] for j, c in row["terms"]) - row["rhs"]) % prime == 0
    echelon = record["echelon_certificate"]
    assert sha(canonical(echelon)) == record["echelon_sha256"]
    assert len(echelon) == record["computed_rank"]
    basis, combinations_checked, terms_checked = {}, 0, 0
    for item in echelon:
        pivot = item["pivot"]
        assert 0 <= pivot < variables and pivot not in basis
        planes = tuple(int(s, 16) for s in item["augmented_row_planes_hex"])
        provenance = tuple(int(s, 16) for s in item["original_row_combination_planes_hex"])
        assert len(planes) == len(provenance) == prime - 1
        target = decode(planes, variables + 1, prime)
        combo = decode(provenance, len(rows), prime)
        assert max(j for j in target if j < variables) == pivot and target[pivot] == 1
        actual = Counter()
        for original, coefficient in combo.items():
            for j, c in rows[original]["terms"]:
                actual[j] += coefficient * (c % prime)
            actual[variables] += coefficient * (rows[original]["rhs"] % prime)
            terms_checked += len(rows[original]["terms"]) + 1
        assert {j: c % prime for j, c in actual.items() if c % prime} == target
        basis[pivot] = planes
        combinations_checked += len(combo)
        if len(basis) % 128 == 0:
            tick(deadline)
    assert sorted(basis) == record["pivot_columns"]
    # The echelon rows are independent, are original-row combinations, and
    # span every original row. These three exact checks prove the rank.
    mask = (1 << variables) - 1
    reductions = 0
    for index, original in enumerate(rows):
        value = encode(original, variables, prime)
        while True:
            occupied = value[0] if prime == 2 else value[0] | value[1]
            remaining = occupied & mask
            if not remaining:
                assert not occupied
                break
            pivot = remaining.bit_length() - 1
            other = basis[pivot]
            if prime == 2:
                value = (value[0] ^ other[0],)
            else:
                if value[0] >> pivot & 1:
                    other = (other[1], other[0])
                value = ternary_sum(value, other)
                assert not (value[0] & value[1])
            reductions += 1
            if reductions % 4096 == 0:
                tick(deadline)
        if index % 128 == 0:
            tick(deadline)
    return {"prime": prime, "status": "PASS: complete modular point and both exact rank bounds",
            "all_equalities_checked": len(rows), "rank": len(basis),
            "original_row_combination_terms": combinations_checked,
            "ordinary_sparse_integer_terms_accumulated": terms_checked,
            "rank_upper_bound_reductions": reductions,
            "integer_or_bounded_count_feasibility_claimed": False}


def replay(seconds):
    started = time.monotonic()
    deadline = started + seconds
    prep, domain, model, field = (load(k) for k in ("preparation", "domains", "model", "arithmetic"))
    for name, value in (("domains", domain), ("model", model), ("arithmetic", field)):
        assert prep["artifacts"][name]["sha256"] == INPUTS[name][1]
        assert prep["artifacts"][name]["canonical_sha256"] == sha(canonical(value))
    assert domain["source_sha256"] == model["source_sha256"] == prep["source_sha256"] == "f02edb406adbd3d2e3fbcf6b68b917cf4eb6fe9cffad6778b1e94a5f85122e7d"
    baseline, moments = load("baseline")["validation"], load("moments")
    original_actions = load("actions")["component_actions"]
    assert original_actions == domain["actual_core_actions"]
    core, triples = baseline["core"], baseline["triples"]
    positions = {tuple(v): i for i, v in enumerate(triples)}
    actions = []
    for permutation in original_actions:
        near = [permutation[6 * f] // 6 for f in range(3)]
        whole = near + [3 + v for v in permutation]
        assert sorted(whole) == list(range(21))
        assert all((core[i] >> j & 1) == (core[whole[i]] >> whole[j] & 1) for i in range(21) for j in range(21))
        actions.append([positions[tuple(sorted(permutation[i] for i in h))] for h in triples])
    assert actions == domain["signature_actions"] == moments["selector_actions"]
    group = {tuple(p) for p in actions}
    assert len(group) == 12 and tuple(range(480)) in group
    assert all(tuple(a[b[i]] for i in range(480)) in group for a in actions for b in actions)
    edges, pairs = baseline["edges"], list(combinations(range(480), 2))
    edge_index = {tuple(e): i for i, e in enumerate(edges)}
    families = [baseline["selector_orbits"], baseline["edge_orbits"], moments["pair_orbits"]]
    sizes = []
    for kind, orbits in enumerate(families):
        total = [480, 68394, 114960][kind]
        assert sorted(i for members in orbits for i in members) == list(range(total))
        for members in orbits:
            if kind == 0:
                images = Counter(p[members[0]] for p in actions)
            elif kind == 1:
                a, b = edges[members[0]]
                images = Counter(edge_index[tuple(sorted((p[a], p[b])))] for p in actions)
            else:
                a, b = pairs[members[0]]
                images = Counter(pair_id(p[a], p[b]) for p in actions)
            assert set(images) == set(members) and set(images.values()) == {12 // len(members)}
            sizes.append(len(members))
    assert sizes == domain["original15589_orbit_sizes"]
    old = load("old_reduction")
    zero = load("zero")
    kept = old["kept_original_variables"]
    latest = [kept[j] for j in zero["new_to_old_columns"]]
    assert kept == domain["old15200_to_original15589"] and latest == domain["new15038_to_original15589"]
    assert [sizes[j] for j in kept] == domain["old15200_orbit_sizes"]
    bound = [sizes[j] for j in latest]
    assert bound == domain["new15038_orbit_sizes"] == model["matrix"]["upper_by_variable"]
    assert model["matrix"]["variables"] == len(bound) == 15038
    assert model["matrix"]["lower"] == 0 and model["matrix"]["all_variables_required_integer"] is True
    divisors = model["row_lift"]["positive_primitive_divisor_per_combined_row"]
    parent_rows = zero["matrix"]["equalities"] + zero["matrix"]["inequalities"]
    rows = model["matrix"]["equalities"] + model["matrix"]["inequalities"]
    assert len(rows) == len(parent_rows) == len(divisors) == 27719
    max_box_abs = 0
    for i, (before, after, divisor) in enumerate(zip(parent_rows, rows, divisors)):
        assert type(divisor) is int and divisor > 0
        assert len(before["terms"]) == len(after["terms"])
        assert after["rhs"] * divisor == 12 * before["rhs"]
        assert dict(before, terms=after["terms"], rhs=after["rhs"]) == after
        for (j, c), (k, d) in zip(before["terms"], after["terms"]):
            assert j == k and d * divisor * bound[j] == 12 * c
        assert math.gcd(abs(after["rhs"]), *(abs(c) for _, c in after["terms"])) in (0, 1)
        box = sum(abs(c) * bound[j] for j, c in after["terms"])
        max_box_abs = max(max_box_abs, box, abs(after["rhs"]))
        if i % 512 == 0:
            tick(deadline)
    assert sum(len(r["terms"]) for r in rows) == 1079832
    assert sha(canonical(model["matrix"])) == model["matrix_sha256"]
    old2newrow = {old_id: i for i, old_id in enumerate(zero["new_to_old_rows"])}
    psd = [old2newrow[i] for i in zero["protected_old_PSD_rows"]]
    assert psd == model["row_lift"]["all92_PSD_combined_row_indices"] and len(psd) == 92
    assert zero["numerical_row_scales"] == model["row_lift"]["old_positive_numerical_row_scales_preserved_as_provenance"]
    # Independently clear each full15200 equality with its own actual LCM,
    # rather than the proposing source's uniform multiplier12.
    full = load("parent")["matrix"]["equalities"]
    old_sizes = domain["old15200_orbit_sizes"]
    transformed = []
    for row in full:
        denominator = math.lcm(*(old_sizes[j] for j, c in row["terms"])) if row["terms"] else 1
        terms = [[j, c * (denominator // old_sizes[j])] for j, c in row["terms"]]
        rhs = denominator * row["rhs"]
        factor = math.gcd(abs(rhs), *(abs(c) for j, c in terms)) or 1
        transformed.append(dict(row, terms=[[j, c // factor] for j, c in terms], rhs=rhs // factor))
    assert len(transformed) == 6135
    assert sha(canonical(transformed)) == model["row_lift"]["all15200_integer_equalities_sha256"]
    assert not model["row_lift"]["individual_equality_gcd_contradictions"]
    for row in model["matrix"]["equalities"]:
        divisor = math.gcd(*(abs(c) for j, c in row["terms"])) if row["terms"] else 0
        assert (row["rhs"] % divisor == 0) if divisor else row["rhs"] == 0
    print(json.dumps({"phase": "orbits_and_lift", "seconds": time.monotonic() - started}), flush=True)
    for a in range(3):
        for b in range(3):
            assert ternary_sum((int(a == 1), int(a == 2)), (int(b == 1), int(b == 2))) == (int((a + b) % 3 == 1), int((a + b) % 3 == 2))
    assert [r["prime"] for r in field["results"]] == [2, 3]
    checks = []
    for record in field["results"]:
        check = check_field(model["matrix"]["equalities"], 15038, record, deadline)
        checks.append(check)
        print(json.dumps({"phase": "rank", **check, "seconds_total": time.monotonic() - started}), flush=True)
    return {"status": "PASS: independent full orbit/lift/point/rank replay",
            "source_sha256": sha(Path(__file__).read_bytes()),
            "inputs": {k: {"path": p, "sha256": h} for k, (p, h) in INPUTS.items()},
            "all15589_orbit_sizes_and_both_column_maps_checked": True,
            "all27719_rows_and1079832_terms_checked_by_integer_cross_products": True,
            "all6135_full15200_equalities_checked_by_independent_denominator_clearing": True,
            "all92_PSD_directions_retained": True,
            "maximum_absolute_row_box_sum_or_rhs": str(max_box_abs),
            "maximum_row_box_sum_bits": max_box_abs.bit_length(),
            "individual_gcd_contradictions": [], "finite_fields": checks,
            "subject_builder_or_modular_helper_imported": False,
            "optimizer_calls": 0, "eigendecompositions": 0,
            "integer_model_feasibility_or_exclusion_claimed": False,
            "seconds": time.monotonic() - started, "cooperative_limit_seconds": seconds}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--seconds", type=float, default=120)
    args = parser.parse_args()
    assert not args.output.exists() and 0 < args.seconds <= 120
    result = replay(args.seconds)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2), flush=True)


if __name__ == "__main__":
    main()
