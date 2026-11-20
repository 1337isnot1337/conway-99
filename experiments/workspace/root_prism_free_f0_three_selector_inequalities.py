"""Point-independent preparation of three-selector Boolean moment rows.

The triangle row is Z_ab+Z_bc-Z_ac-x_b<=0. The perimeter row is
x_a+x_b+x_c-Z_ab-Z_ac-Z_bc<=1. All three selectors are distinct.
This preparation proves the finite Boolean formulas, validates the actual
core quotient, and covers the full family with42 center representatives.
It does not inspect a fractional point or perform a separator scan.
"""
import argparse
from collections import Counter
import gzip
import hashlib
from itertools import combinations, product
import json
from math import comb
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[2]
BASE = "experiments/logs/root-prism-free/"
INPUTS = {
    "domain": (BASE+"f0-boolean-fractional-model.json.gz", "703206929c9c85a40ac4ddcbfb1708c716c288482cf50c77a32249404e35b782"),
    "moments": (BASE+"f0-second-moments-preparation02.json.gz", "404d91da35c798ba248887c22a7500957947e24b71d5197dc44432460e6d219e"),
    "reduction": (BASE+"f0-second-moments-reduced-model.json.gz", "73a50b431ac69ad57e10cff9aabe5c0b7d69ee075e95710b461f62b33fe2bbcf"),
    "core_actions": (BASE+"f0-graph-schur-kernels01.json.gz", "65f1ad0d0015a6eff3d97c676fb0e188f57f9dee00e9245758a28bab2069b40d"),
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def pair_id(a, b):
    assert 0 <= a < 480 and 0 <= b < 480 and a != b
    a, b = sorted((a, b))
    return a*(959-a)//2+b-a-1


def literal_row(family, a, b, c, data):
    assert len({a, b, c}) == 3
    counts = Counter()
    if family == "triangle":
        x_terms = [(b, -1)]
        pair_terms = [(a, b, 1), (b, c, 1), (a, c, -1)]
        rhs = 0
    else:
        assert family == "perimeter"
        x_terms = [(a, 1), (b, 1), (c, 1)]
        pair_terms = [(a, b, -1), (b, c, -1), (a, c, -1)]
        rhs = 1
    for v, coefficient in x_terms:
        counts[data["reverse"][data["xmap"][v]]] += coefficient
    for u, v, coefficient in pair_terms:
        original = 5847+data["pair_to_orbit"][pair_id(u, v)]
        if original not in data["fixed"]:
            counts[data["reverse"][original]] += coefficient
    terms = [[j, v] for j, v in sorted(counts.items()) if v]
    assert all(0 <= j < 15200 and type(v) is int for j, v in terms)
    return {"terms": terms, "rhs": rhs}


def boolean_controls():
    truth = []
    for a, b, c in product((0, 1), repeat=3):
        triangle_slack = b+a*c-a*b-b*c
        perimeter_slack = 1-a-b-c+a*b+a*c+b*c
        assert triangle_slack == ((1-a)*(1-c) if b else a*c)
        assert perimeter_slack == int(a+b+c in (0, 3))
        assert triangle_slack in (0, 1) and perimeter_slack in (0, 1)
        truth.append([a, b, c, triangle_slack, perimeter_slack])
    # Arbitrary integer coincidences must be summed, including cancellation.
    quotient_checks = 0
    for xlabels in product(range(3), repeat=3):
        for plabels in product(range(3, 6), repeat=3):
            fake = {"xmap": dict(enumerate(xlabels)),
                    "pair_to_orbit": [-1]*114960,
                    "reverse": {j: j for j in range(6)}, "fixed": set()}
            for (u, v), label in zip(((0, 1), (1, 2), (0, 2)), plabels):
                fake["pair_to_orbit"][pair_id(u, v)] = label-5847
            values = [2, 3, 5, 7, 11, 13]
            for family in ("triangle", "perimeter"):
                row = literal_row(family, 0, 1, 2, fake)
                got = sum(k*values[j] for j, k in row["terms"])
                x0, x1, x2 = [values[j] for j in xlabels]
                p01, p12, p02 = [values[j] for j in plabels]
                expected = p01+p12-p02-x1 if family == "triangle" else x0+x1+x2-p01-p12-p02
                assert got == expected
                quotient_checks += 1
    return {"all_eight_binary_assignments": truth,
            "both_slacks_are_exact_zero_or_one": True,
            "quotient_alias_and_cancellation_checks": quotient_checks}


def cycles(g):
    seen = set(); counts = Counter()
    for v in range(len(g)):
        if v in seen:
            continue
        u = v; size = 0
        while u not in seen:
            seen.add(u); size += 1; u = g[u]
        assert u == v
        counts[size] += 1
    return counts


def load_domain():
    loaded = {}
    for name, (path, digest) in INPUTS.items():
        raw = (ROOT/path).read_bytes()
        assert sha(raw) == digest
        loaded[name] = json.loads(gzip.decompress(raw))
    d = loaded["domain"]["validation"]
    core, triples = d["core"], d["triples"]
    assert len(core) == 21 and len(triples) == 480 and len(set(map(tuple, triples))) == 480
    moments, reduced = loaded["moments"], loaded["reduction"]
    assert moments["selector_pair_order"] == "lexicographic(a,b),0<=a<b<480"
    assert moments["selector_orbits"] == d["selector_orbits"]
    xmap = {a: o for o, group in enumerate(d["selector_orbits"]) for a in group}
    assert len(xmap) == 480 and len(d["selector_orbits"]) == 42
    pairs = list(combinations(range(480), 2))
    assert len(pairs) == 114960 and all(pair_id(a, b) == i for i, (a, b) in enumerate(pairs))
    pmap = moments["pair_to_orbit"]
    assert len(pmap) == 114960 and len(moments["pair_orbits"]) == 9742
    kept = reduced["kept_original_variables"]
    fixed = {j for j, proof_row in reduced["fixed_zero_original_variables"]}
    for j, proof_row in reduced["fixed_zero_original_variables"]:
        row = moments["matrix"]["equalities"][proof_row]
        assert row["terms"] == [[j, 1]] and row["rhs"] == 0
    reverse = {j: i for i, j in enumerate(kept)}
    assert len(kept) == len(reverse) == 15200 and len(fixed) == 389
    assert set(kept).isdisjoint(fixed) and set(kept) | fixed == set(range(15589))
    assert all(reverse[j] == j for j in range(5847))
    actions = moments["selector_actions"]
    core_actions = loaded["core_actions"]["domain"]["reconstructed21_core_actions"]
    assert len(actions) == len(core_actions) == 12
    assert len(set(map(tuple, actions))) == len(set(map(tuple, core_actions))) == 12
    core_index = {tuple(move): i for i, move in enumerate(core_actions)}
    assert tuple(range(21)) in core_index
    for g, move in zip(actions, core_actions):
        assert sorted(g) == list(range(480)) and sorted(move) == list(range(21))
        assert set(move[:3]) == set(range(3))
        assert all(((core[u] >> v) & 1) == ((core[move[u]] >> move[v]) & 1)
                   for u in range(21) for v in range(21))
        assert all(sorted(move[j+3]-3 for j in h) == triples[g[a]] for a, h in enumerate(triples))
    for i, left in enumerate(core_actions):
        for j, right in enumerate(core_actions):
            k = core_index[tuple(left[right[v]] for v in range(21))]
            assert all(actions[k][a] == actions[i][actions[j][a]] for a in range(480))
    for group in d["selector_orbits"]:
        assert sorted({g[group[0]] for g in actions}) == group
    for orbit, group in enumerate(moments["pair_orbits"]):
        a, b = pairs[group[0]]
        assert sorted({pair_id(g[a], g[b]) for g in actions}) == group
        assert all(pmap[p] == orbit for p in group)
    representatives = [group[0] for group in d["selector_orbits"]]
    center_transports = []
    for b in range(480):
        representative = representatives[xmap[b]]
        gi = next(i for i, g in enumerate(actions) if g[b] == representative)
        center_transports.append([b, representative, gi])
    return {"xmap": xmap, "pair_to_orbit": pmap, "reverse": reverse, "fixed": fixed,
            "actions": actions, "representatives": representatives,
            "center_transports": center_transports}


def preparation():
    data = load_domain()
    control = boolean_controls()
    burns = []
    for g in data["actions"]:
        cc = cycles(g); f, two, three = cc[1], cc[2], cc[3]
        triangles = f*(comb(f-1, 2)+two) if f else 0
        perimeters = comb(f, 3)+f*two+three
        burns.append({"cycle_counts": [list(t) for t in sorted(cc.items())], "fixed_triangle_rows": triangles,
                      "fixed_perimeter_rows": perimeters})
    ttotal = sum(row["fixed_triangle_rows"] for row in burns)
    ptotal = sum(row["fixed_perimeter_rows"] for row in burns)
    assert ttotal % 12 == ptotal % 12 == 0
    return {"status": "PREPARED_COMPLETE_THREE_SELECTOR_BOOLEAN_ROW_SCOPE_NO_SCAN",
            "source_sha256": sha(Path(__file__).read_bytes()),
            "inputs": {k: {"path": p, "sha256": h} for k, (p, h) in INPUTS.items()},
            "variables": 15200, "selectors": 480, "pair_orbits": 9742, "fixed_zero_pair_orbits": 389,
            "center_representatives": data["representatives"], "center_transports": data["center_transports"],
            "actual_core_actions": 12, "group_compositions_checked": 144,
            "selector_and_pair_orbits_checked_exactly": True,
            "controls": control, "Burnside": burns,
            "literal_triangle_rows": 480*comb(479, 2),
            "literal_perimeter_rows": comb(480, 3),
            "triangle_row_orbits_before_coefficient_coincidences": ttotal//12,
            "perimeter_row_orbits_before_coefficient_coincidences": ptotal//12,
            "planned_anchor_pair_evaluations_per_family": 42*comb(479, 2),
            "perimeter_anchor_coverage_allows_duplicates": True,
            "planned_maximum_numeric_candidates_per_anchor_and_family": 8,
            "planned_maximum_exact_retained_rows_per_family": 64,
            "proposed_scan_seconds": 30,
            "dense480_matrix_bytes_per_float64_array": 8*480*480,
            "point_binding_and_integer_bit_bounds_require_separate_preparation": True,
            "numeric_scan_calls": 0, "optimizer_calls": 0, "point_loaded": False,
            "whole_three_selector_cone_enforced": False,
            "scope": "All three-selector triangle and perimeter formulas. At most42 anchors suffice for invariant moment assignments; no numerical or exact point acceptance is claimed."}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=("prepare", "replay"))
    p.add_argument("--record", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    assert not args.output.exists()
    start = time.monotonic()
    record = preparation(); raw = canonical(record)
    if args.mode == "prepare":
        assert not args.record.exists()
        args.record.write_text(json.dumps(record, indent=2)+"\n")
    else:
        assert canonical(json.loads(args.record.read_text())) == raw
    report = {"status": "PASS: three-selector Boolean scope "+args.mode,
              "source_sha256": record["source_sha256"], "record_sha256": sha(args.record.read_bytes()),
              "record_canonical_sha256": sha(raw),
              "literal_triangle_rows": record["literal_triangle_rows"],
              "literal_perimeter_rows": record["literal_perimeter_rows"],
              "triangle_orbits": record["triangle_row_orbits_before_coefficient_coincidences"],
              "perimeter_orbits": record["perimeter_row_orbits_before_coefficient_coincidences"],
              "anchor_pair_evaluations_per_family": record["planned_anchor_pair_evaluations_per_family"],
              "numeric_scan_calls": 0, "optimizer_calls": 0, "point_loaded": False,
              "seconds": time.monotonic()-start}
    args.output.write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
