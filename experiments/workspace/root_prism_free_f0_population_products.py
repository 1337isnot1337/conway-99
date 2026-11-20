"""Exact deterministic orbit-population products; preparation only.

No optimizer is imported or called. All 42 selector populations stay free.
This is a necessary count model, not a graph construction or exclusion.
"""
import argparse
from collections import Counter, defaultdict
import gzip
import hashlib
from itertools import combinations
import json
import math
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[2]
LOGS = ROOT / "experiments/logs/root-prism-free"
INPUTS = {
    "domains": ("f0-orbit-populations02-domains.json.gz", "4f079468530dba0746512cc4afce01666b2a63a2c8f35f66a4660a4fe3bab8ab"),
    "linear": ("f0-orbit-populations02-model.json.gz", "aa46e2ca9df7a5838926385e06a86acda041c8455ac3422ae1e7b0a5c4ce5437"),
    "linear_replay": ("f0-orbit-populations02-independent-replay.json", "a8bb55cbf773ea75a8cd1d5a18b50281ecbe08f6074cea04fb2d75799138273a"),
    "refinements": ("f0-selector-integer-refinements01.json.gz", "68d5ea0ca4a9906e74319770924eb91f880e46cec0c3ed2ab269bb1debe7b339"),
    "refinement_replay": ("f0-selector-integer-refinements-independent-audit.json", "8a45a87eccb55fa4e5362e967ce925f38bfde25a943bb12a1a804cb4fa573cbc"),
    "full_parent": ("f0-joint-psd-clique-model01.json.gz", "43fff7283308cc2ed1be0936fae4b4f7b264c5961f6e6a4c9a81d123836e4f69"),
}
PRIMARY, SELECTORS, PAIR_OFFSET = 15038, 42, 5847


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def read(name):
    path, expected = INPUTS[name]
    raw = (LOGS / path).read_bytes()
    assert sha(raw) == expected, name
    return json.loads(gzip.decompress(raw) if path.endswith(".gz") else raw)


def save(path, value):
    raw = canonical(value) + b"\n"
    if str(path).endswith(".gz"):
        raw = gzip.compress(raw, mtime=0)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(raw)
    return {"path": str(path.relative_to(ROOT)), "sha256": sha(raw),
            "canonical_sha256": sha(canonical(value)), "bytes": len(raw)}


def tick(deadline):
    if time.monotonic() >= deadline:
        raise TimeoutError("cooperative population-product preparation limit")


def reconstruct_pairs(domain):
    """Independent literal pair enumeration, including proved-zero pairs."""
    actions, orbits = domain["signature_actions"], domain["selector_orbits"]
    assert len(actions) == 12 and len(orbits) == SELECTORS
    assert sorted(a for o in orbits for a in o) == list(range(480))
    owner = [-1] * 480
    for i, members in enumerate(orbits):
        for a in members:
            owner[a] = i
    pairs = list(combinations(range(480), 2))
    where = {ab: p for p, ab in enumerate(pairs)}
    seen, members = set(), []
    for p, (a, b) in enumerate(pairs):
        if p in seen:
            continue
        current = sorted({where[tuple(sorted((g[a], g[b])))] for g in actions})
        assert p == current[0] and not seen.intersection(current)
        q = len(members)
        blocks = {tuple(sorted((owner[pairs[k][0]], owner[pairs[k][1]]))) for k in current}
        assert blocks == {tuple(domain["pair_orbit_selector_blocks"][q])}
        assert len(current) == domain["original15589_orbit_sizes"][PAIR_OFFSET + q]
        members.append(current)
        seen.update(current)
    assert len(members) == 9742 and len(seen) == 114960
    assert sha(canonical(members)) == domain["literal_orbit_member_hashes"]["pair"]
    return pairs, members


def product_blocks(domain):
    sizes = domain["new15038_orbit_sizes"]
    original = domain["new15038_to_original15589"]
    reverse = {old: j for j, old in enumerate(original)}
    assert len(original) == PRIMARY and original[:SELECTORS] == list(range(SELECTORS))
    blocks = {(i, j): {"selector_orbits": [i, j], "retained_pair_variables": [],
                       "proved_zero_pair_orbits": [], "all_pair_orbits": []}
              for i in range(SELECTORS) for j in range(i, SELECTORS)}
    for q, (i, j) in enumerate(domain["pair_orbit_selector_blocks"]):
        block = blocks[i, j]
        block["all_pair_orbits"].append(q)
        old = PAIR_OFFSET + q
        if old in reverse:
            block["retained_pair_variables"].append(reverse[old])
        else:
            assert old in domain["original_Z_zero_columns"]
            block["proved_zero_pair_orbits"].append(q)
    result, links = [], []
    for index, ((i, j), block) in enumerate(blocks.items()):
        si, sj = sizes[i], sizes[j]
        complete_pairs = si * sj if i != j else si * (si - 1) // 2
        assert sum(domain["original15589_orbit_sizes"][PAIR_OFFSET + q]
                   for q in block["all_pair_orbits"]) == complete_pairs
        product = PRIMARY + index
        coefficients = {v: 1 if i != j else 2 for v in block["retained_pair_variables"]}
        coefficients[product] = -1
        if i == j:
            coefficients[i] = coefficients.get(i, 0) + 1
        links.append({"family": "deterministic selector-orbit pair population",
                      "block": index, "rhs": 0,
                      "terms": [[v, c] for v, c in sorted(coefficients.items()) if c]})
        block.update(index=index, product_variable=product, product_factors=[i, j],
                     product_upper=si * sj, all_literal_pairs=complete_pairs,
                     retained_literal_pair_capacity=sum(sizes[v] for v in block["retained_pair_variables"]),
                     identity=("sum(P)=N_i*N_j" if i != j else "2*sum(P)=N_i*N_i-N_i"))
        result.append(block)
    assert len(result) == 903
    all_variables = [v for block in result for v in block["retained_pair_variables"]]
    assert len(all_variables) == len(set(all_variables)) == 9353
    assert set(all_variables) == {j for j, old in enumerate(original) if old >= PAIR_OFFSET}
    return result, links


def refinement_rows(domain, certificate):
    oldmap = domain["old15200_to_original15589"]
    reverse = {old: j for j, old in enumerate(domain["new15038_to_original15589"])}
    sizes = domain["new15038_orbit_sizes"]
    rows, witnesses = [], []
    assert len(certificate["refinements"]) == 25
    for index, record in enumerate(certificate["refinements"]):
        assert record["disposition"] == "RETAIN_VALID_INTEGER_REFINEMENT"
        source = record["row"]
        assert sha(canonical(source)) == record["row_sha256"]
        terms = Counter()
        omitted = []
        for old, c in source["terms"]:
            original = oldmap[old]
            if original not in reverse:
                assert original in domain["original_Y_zero_columns"]
                omitted.append([old, c])
                continue
            j = reverse[original]
            assert 12 % sizes[j] == 0
            terms[j] += c * (12 // sizes[j])
        rhs = 12 * source["rhs"]
        divisor = math.gcd(abs(rhs), *(abs(c) for c in terms.values())) or 1
        row = {"family": "certified selector integer refinement", "refinement": index,
               "terms": [[j, c // divisor] for j, c in sorted(terms.items()) if c], "rhs": rhs // divisor}
        for old, c in source["terms"]:
            original = oldmap[old]
            if original in reverse:
                j = reverse[original]
                assert dict(row["terms"])[j] * divisor * sizes[j] == 12 * c
        assert divisor * row["rhs"] == 12 * source["rhs"]
        rows.append(row)
        witnesses.append({"refinement": index, "positive_divisor": divisor,
                          "original_row_sha256": record["row_sha256"],
                          "omitted_proved_zero_terms": omitted, "lifted_row_sha256": sha(canonical(row))})
    return rows, witnesses


def box(row, upper):
    lo = sum(c * upper[j] for j, c in row["terms"] if c < 0)
    hi = sum(c * upper[j] for j, c in row["terms"] if c > 0)
    return lo, hi


def binary_adder_estimate(rows, upper):
    """Count a generic independent full-adder network, without emitting CNF.

    Each count is represented by its ordinary bits. Negative terms use
    complemented bits and an exact constant shift. Every weighted bit is
    bucketed by weight. This estimate does not assume beneficial aliases.
    """
    stats = Counter()
    max_width = 0
    for row in rows:
        buckets = Counter()
        raw_max = 0
        for j, c in row["terms"]:
            nbits = upper[j].bit_length()
            weight = abs(c)
            raw_max += weight * ((1 << nbits) - 1)
            stats["weighted_literal_occurrences"] += nbits
            positions = [k for k in range(weight.bit_length()) if weight >> k & 1]
            stats["initial_weight_bit_occurrences"] += nbits * len(positions)
            for b in range(nbits):
                for k in positions:
                    buckets[b + k] += 1
        k = 0
        while k <= max(buckets, default=-1):
            count = buckets[k]
            full = max(0, (count - 1) // 2)
            if full:
                buckets[k] -= 2 * full
                buckets[k + 1] += full
                stats["compressor_full_adders"] += full
            assert buckets[k] <= 2
            k += 1
        carry = 0
        for k in range(max(buckets, default=-1) + 2):
            count = buckets[k] + carry
            if count == 3:
                stats["ripple_full_adders"] += 1
                carry = 1
            elif count == 2:
                stats["ripple_half_adders"] += 1
                carry = 1
            else:
                carry = 0
        assert not carry
        width = raw_max.bit_length()
        max_width = max(max_width, width)
        stats["output_width_sum"] += width
        stats["rows"] += 1
    full = stats["compressor_full_adders"] + stats["ripple_full_adders"]
    half = stats["ripple_half_adders"]
    stats["adder_auxiliary_upper_bound"] = 2 * (full + half)
    stats["adder_clause_upper_bound"] = 14 * full + 7 * half
    stats["comparison_auxiliary_upper_bound"] = 2 * stats["output_width_sum"]
    stats["comparison_clause_upper_bound"] = 8 * stats["output_width_sum"]
    stats["maximum_unsigned_sum_width"] = max_width
    return dict(stats)


def controls(domain, blocks, pairs, members):
    selections = [set(), set(range(480)), set(range(0, 480, 2)), set(range(1, 480, 3)),
                  {o[0] for o in domain["selector_orbits"]},
                  {a for a in range(480) if (37 * a + 11) % 101 < 39}]
    identities = 0
    for selected in selections:
        counts = [sum(a in selected for a in orbit) for orbit in domain["selector_orbits"]]
        pc = [sum(pairs[p][0] in selected and pairs[p][1] in selected for p in orbit) for orbit in members]
        for block in blocks:
            i, j = block["selector_orbits"]
            actual = sum(pc[q] for q in block["all_pair_orbits"])
            expected = counts[i] * counts[j] if i != j else counts[i] * (counts[i] - 1) // 2
            assert actual == expected
            identities += 1
    assignments = 0
    for sa, sb in ((6, 6), (6, 12), (12, 12)):
        for a in range(sa + 1):
            for b in range(sb + 1):
                target = a * b
                assert 0 <= target <= sa * sb
                assert target == a * b and target + 1 != a * b
                assignments += 1
    for size in (6, 12):
        for n in range(size + 1):
            target, p = n * n, n * (n - 1) // 2
            assert 2 * p == target - n and 2 * (p + 1) != target - n
            assignments += 1
    return {"arbitrary_binary_selection_controls": len(selections),
            "complete_literal_block_identities_checked": identities,
            "product_and_diagonal_assignment_checks": assignments,
            "controls_use_all_pair_orbits_including_zero_orbits": True,
            "control_whole_model_feasibility_claimed": False, "solver_calls": 0}


def build(deadline):
    domain, linear, replay, refined, refined_replay = [read(k) for k in
        ("domains", "linear", "linear_replay", "refinements", "refinement_replay")]
    assert replay["status"].startswith("PASS") and refined_replay["status"].startswith("PASS")
    assert linear["matrix_sha256"] == sha(canonical(linear["matrix"]))
    assert linear["counts"]["physical_PSD_directions"] == 92
    pairs, members = reconstruct_pairs(domain)
    blocks, links = product_blocks(domain)
    refined_rows, witnesses = refinement_rows(domain, refined)
    control = controls(domain, blocks, pairs, members)
    del pairs, members
    tick(deadline)
    upper = domain["new15038_orbit_sizes"] + [b["product_upper"] for b in blocks]
    matrix = linear["matrix"]
    rows = matrix["equalities"] + matrix["inequalities"] + refined_rows + links
    assert len(rows) == 28647 and len(upper) == 15941
    maximum = max(max(abs(v) for v in (*box(r, upper), r["rhs"])) for r in rows)
    absolute_sum = max(sum(abs(c) * upper[j] for j, c in r["terms"]) for r in rows)
    assert max(maximum, absolute_sum) < (1 << 62)
    estimate = binary_adder_estimate(rows, upper)
    tick(deadline)
    small_bounds = []
    for b in blocks:
        i, j = b["selector_orbits"]
        if i == j:
            derived = max(n for n in range(upper[i] + 1) if n * (n - 1) // 2 <= b["retained_literal_pair_capacity"])
            if derived < upper[i]:
                small_bounds.append({"orbit": i, "old_upper": upper[i], "derived_upper": derived,
                                     "pair_capacity": b["retained_literal_pair_capacity"]})
    return {
        "schema": "conway99.f0-deterministic-orbit-population-products.v1",
        "inputs": {k: {"path": str((LOGS / p).relative_to(ROOT)), "sha256": h} for k, (p, h) in INPUTS.items()},
        "parent_count_matrix_sha256": linear["matrix_sha256"],
        "primary_variables": PRIMARY, "variables_with_product_auxiliaries": len(upper),
        "upper_by_variable": upper, "all_variables_integer": True,
        "blocks": blocks, "product_link_equalities": links,
        "selector_integer_refinement_rows": refined_rows, "refinement_lift_witnesses": witnesses,
        "inherited_linear_equalities": len(matrix["equalities"]),
        "inherited_linear_inequalities": len(matrix["inequalities"]),
        "linear_rows_including_links": len(rows), "native_product_constraints": len(blocks),
        "native_constraints": len(rows) + len(blocks),
        "linear_nonzeros": sum(len(r["terms"]) for r in rows),
        "refinement_nonzeros": sum(len(r["terms"]) for r in refined_rows),
        "block_link_nonzeros": sum(len(r["terms"]) for r in links),
        "pair_block_support_histogram": dict(sorted(Counter(len(b["retained_pair_variables"]) for b in blocks).items())),
        "within_block_capacity_upper_bounds": small_bounds,
        "maximum_absolute_finite_linear_bound_or_rhs": maximum,
        "maximum_linear_absolute_box_sum": absolute_sum,
        "maximum_product_upper": max(b["product_upper"] for b in blocks),
        "signed64_arithmetic_safe_from_explicit_domains": True,
        "inherited92_PSD_row_indices": linear["row_lift"]["all92_PSD_combined_row_indices"],
        "binary_count_primary_bits": sum(s.bit_length() for s in domain["new15038_orbit_sizes"]),
        "binary_product_target_bits": sum(b["product_upper"].bit_length() for b in blocks),
        "binary_adder_estimate": estimate, "controls": control,
        "scope": {"all42_selector_populations_free": True, "all480_signatures_retained_through_complete_orbits": True,
                  "graph_automorphism_assumed": False, "selector_orbit_subset_tables_imposed": False,
                  "all92_PSD_directions_retained": True, "all25_integer_refinements_retained": True,
                  "optimizer_calls": 0, "feasibility_or_exclusion_claimed": False,
                  "conditional_case": "global P=F=0, split18+18, component zero; second component remains unspecified"},
    }


def inspect(primary, specification, linear=None, domain=None):
    """Full exact candidate acceptance; no solver status is used."""
    linear = read("linear") if linear is None else linear
    domain = read("domains") if domain is None else domain
    assert len(primary) == PRIMARY and all(type(v) is int for v in primary)
    sizes = domain["new15038_orbit_sizes"]
    assert all(0 <= v <= sizes[j] for j, v in enumerate(primary))
    totals = Counter()
    for kind in ("equalities", "inequalities"):
        for row in linear["matrix"][kind]:
            value = sum(c * primary[j] for j, c in row["terms"])
            assert value == row["rhs"] if kind == "equalities" else value <= row["rhs"]
            totals[kind] += 1
    for row in specification["selector_integer_refinement_rows"]:
        assert sum(c * primary[j] for j, c in row["terms"]) <= row["rhs"]
    for block in specification["blocks"]:
        i, j = block["selector_orbits"]
        total = sum(primary[v] for v in block["retained_pair_variables"])
        assert total == (primary[i] * primary[j] if i != j else primary[i] * (primary[i] - 1) // 2)
    reverse = {old: j for j, old in enumerate(domain["new15038_to_original15589"])}
    scaled = [0 if old not in reverse else (12 // domain["original15589_orbit_sizes"][old]) * primary[reverse[old]]
              for old in domain["old15200_to_original15589"]]
    assert len(scaled) == 15200 and all(0 <= v <= 12 for v in scaled)
    parent = read("full_parent")
    for kind in ("equalities", "inequalities"):
        for row in parent["matrix"][kind]:
            value = sum(c * scaled[j] for j, c in row["terms"])
            assert value == 12 * row["rhs"] if kind == "equalities" else value <= 12 * row["rhs"]
            totals["full_parent_" + kind] += 1
    for record in read("refinements")["refinements"]:
        row = record["row"]
        assert sum(c * scaled[j] for j, c in row["terms"]) <= 12 * row["rhs"]
    return {"status": "PASS: exact bounded orbit-count witness only", **totals,
            "count_bounds": PRIMARY, "full_parent_bounds": 15200,
            "deterministic_population_identities": 903, "integer_refinements": 25,
            "graph_or_literal_incidence_reconstruction_claimed": False}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-prefix", type=Path, required=True)
    parser.add_argument("--seconds", type=float, default=120)
    args = parser.parse_args()
    started = time.monotonic()
    spec = build(started + args.seconds)
    spec["source_sha256"] = sha(Path(__file__).read_bytes())
    artifact = save(Path(str(args.output_prefix) + "-specification.json.gz"), spec)
    report = {"status": "PREPARED: exact903 deterministic products; no optimizer",
              "source_sha256": spec["source_sha256"], "specification": artifact,
              "counts": {k: spec[k] for k in ("primary_variables", "variables_with_product_auxiliaries", "linear_rows_including_links", "native_product_constraints", "native_constraints", "linear_nonzeros", "refinement_nonzeros", "block_link_nonzeros")},
              "controls": spec["controls"], "binary_adder_estimate": spec["binary_adder_estimate"],
              "maximum_linear_absolute_box_sum": spec["maximum_linear_absolute_box_sum"],
              "maximum_product_upper": spec["maximum_product_upper"], "optimizer_calls": 0,
              "seconds": time.monotonic() - started, "cooperative_limit_seconds": args.seconds}
    save(Path(str(args.output_prefix) + "-preparation.json"), report)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
