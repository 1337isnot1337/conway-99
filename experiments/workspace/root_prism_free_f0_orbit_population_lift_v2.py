"""Complete F0 orbit-population integer lift and bounded exact arithmetic.

All work is point-independent except a scoped old selector/RLT control.
No optimizer, SAT solver, eigensolver or graph automorphism is assumed.
The real row change is exact; requiring integer orbit populations is an
additional necessary condition for a single hypothetical graph.
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

import root_prism_free_f0_orbit_population_modular as modular

ROOT = Path(__file__).resolve().parents[2]
LOGS = ROOT / "experiments/logs/root-prism-free"
MODULAR_SHA = "947ff977b8b060296f05fbbae6734c67e73534c6fc371becda064f36047e9bf0"
INPUTS = {
    "baseline": ("f0-boolean-fractional-model.json.gz", "703206929c9c85a40ac4ddcbfb1708c716c288482cf50c77a32249404e35b782"),
    "moments": ("f0-second-moments-preparation02.json.gz", "404d91da35c798ba248887c22a7500957947e24b71d5197dc44432460e6d219e"),
    "first_reduction": ("f0-second-moments-reduced-model.json.gz", "73a50b431ac69ad57e10cff9aabe5c0b7d69ee075e95710b461f62b33fe2bbcf"),
    "joint": ("f0-joint-psd-clique-model01.json.gz", "43fff7283308cc2ed1be0936fae4b4f7b264c5961f6e6a4c9a81d123836e4f69"),
    "zero_reduction": ("f0-joint-psd-clique-zero-model01.json.gz", "da9b2062f9102a0487bc5fb88b2e009c1a228cbc2d2c39264135808bb3467ffb"),
    "zero_replay": ("f0-joint-psd-clique-zero-model01-standalone-replay.json", "c3ef825b6177d7b545f6827545e4650c4febb6c56928487b9b6f859656e9f94d"),
    "core_actions": ("f0-fractional-structural-recovery-input.json", "ef4018f26c48e9eb90bf544d41678778d71b587994096383023c8836e70bca6e"),
    "selector_control": ("f0-incidence-case00-run01/result.json", "64d5411e04764b0d7e7157c47b67d759e536a401fee8fe36e274943f2fda4abf"),
}
N, GROUP_ORDER = 480, 12


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def load(name):
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
    return {"path": str(path.relative_to(ROOT)), "sha256": sha(raw), "bytes": len(raw),
            "canonical_sha256": sha(canonical(value))}


def tick(deadline):
    if time.monotonic() >= deadline:
        raise TimeoutError("bounded orbit-population exact preparation")


def pair_id(a, b):
    assert a != b and 0 <= a < N and 0 <= b < N
    a, b = sorted((a, b))
    return a * (959 - a) // 2 + b - a - 1


def inventory(sizes, ids):
    out = {}
    for family, low, high in (("selector", 0, 42), ("edge", 42, 5847), ("pair", 5847, 15589)):
        chosen = [i for i in ids if low <= i < high]
        out[family] = {"orbits": len(chosen),
                       "size_histogram": {str(k): v for k, v in sorted(Counter(sizes[i] for i in chosen).items())},
                       "literal_positions": sum(sizes[i] for i in chosen)}
    return out


def domains(baseline, moments, old, reduced, deadline):
    data = baseline["validation"]
    core, triples, edges = data["core"], data["triples"], data["edges"]
    assert len(core) == 21 and len(triples) == 480 and len(edges) == 68394
    assert edges == sorted(edges) and len({tuple(e) for e in edges}) == len(edges)
    positions = {tuple(h): i for i, h in enumerate(triples)}
    assert len(positions) == N
    component_actions = load("core_actions")["component_actions"]
    actions = []
    for move in component_actions:
        assert sorted(move) == list(range(18))
        fibers = [move[6 * f] // 6 for f in range(3)]
        assert sorted(fibers) == list(range(3))
        assert all(move[i] // 6 == fibers[i // 6] for i in range(18))
        whole = fibers + [3 + j for j in move]
        assert sorted(whole) == list(range(21))
        assert all((core[i] >> j & 1) == (core[whole[i]] >> whole[j] & 1)
                   for i in range(21) for j in range(21))
        actions.append([positions[tuple(sorted(move[i] for i in h))] for h in triples])
    assert actions == moments["selector_actions"] and len(actions) == GROUP_ORDER
    group = {tuple(p) for p in actions}
    assert len(group) == GROUP_ORDER and tuple(range(N)) in group
    assert all(tuple(a[b[i]] for i in range(N)) in group for a in actions for b in actions)
    selectors = data["selector_orbits"]
    assert selectors == moments["selector_orbits"] and len(selectors) == 42
    assert sorted(i for o in selectors for i in o) == list(range(N))
    xof = [-1] * N
    for o, members in enumerate(selectors):
        for a in members:
            xof[a] = o
        images = Counter(p[members[0]] for p in actions)
        assert set(images) == set(members)
        assert set(images.values()) == {GROUP_ORDER // len(members)}
    edge_index = {tuple(e): i for i, e in enumerate(edges)}
    edge_orbits = data["edge_orbits"]
    assert len(edge_orbits) == 5805
    assert sorted(e for o in edge_orbits for e in o) == list(range(len(edges)))
    edge_blocks, edge_pair_orbits = [], []
    for members in edge_orbits:
        a, b = edges[members[0]]
        images = Counter(edge_index[tuple(sorted((p[a], p[b])))] for p in actions)
        assert set(images) == set(members)
        assert set(images.values()) == {GROUP_ORDER // len(members)}
        blocks = {tuple(sorted((xof[u], xof[v]))) for e in members for u, v in [edges[e]]}
        assert len(blocks) == 1
        edge_blocks.append(list(blocks.pop()))
        pair_orbits = {moments["pair_to_orbit"][pair_id(*edges[e])] for e in members}
        assert len(pair_orbits) == 1
        edge_pair_orbits.append(pair_orbits.pop())
    pairs = list(combinations(range(N), 2))
    assert len(pairs) == 114960 and all(pair_id(*p) == i for i, p in enumerate(pairs))
    pair_orbits = moments["pair_orbits"]
    assert len(pair_orbits) == 9742
    assert sorted(p for o in pair_orbits for p in o) == list(range(len(pairs)))
    pair_blocks = []
    for oi, members in enumerate(pair_orbits):
        a, b = pairs[members[0]]
        images = Counter(pair_id(p[a], p[b]) for p in actions)
        assert set(images) == set(members)
        assert set(images.values()) == {GROUP_ORDER // len(members)}
        assert all(moments["pair_to_orbit"][p] == oi for p in members)
        blocks = {tuple(sorted((xof[u], xof[v]))) for p in members for u, v in [pairs[p]]}
        assert len(blocks) == 1
        pair_blocks.append(list(blocks.pop()))
    burnside = []
    for p in actions:
        fixed = sum(p[a] == a for a in range(N))
        exchanged = sum(p[a] != a and p[p[a]] == a for a in range(N)) // 2
        fixed_edges = sum(tuple(sorted((p[a], p[b]))) == (a, b) for a, b in edges)
        burnside.append({"selectors": fixed, "edges": fixed_edges,
                         "pairs": fixed * (fixed - 1) // 2 + exchanged})
    assert [sum(v[k] for v in burnside) for k in ("selectors", "edges", "pairs")] == [12 * 42, 12 * 5805, 12 * 9742]
    tick(deadline)
    sizes = list(map(len, selectors)) + list(map(len, edge_orbits)) + list(map(len, pair_orbits))
    assert len(sizes) == 15589 and set(sizes) == {3, 6, 12}
    zeros_z = [5847 + o for o in moments["zero_pair_orbits"]]
    zero_entries = old["fixed_zero_original_variables"]
    assert zeros_z == [variable for variable, original_equality in zero_entries]
    for variable, original_equality in zero_entries:
        row = moments["matrix"]["equalities"][original_equality]
        assert row["family"] == "certified zero selector moment"
        assert row["rhs"] == 0 and row["terms"] == [[variable, 1]]
    old_kept = old["kept_original_variables"]
    assert old_kept == [j for j in range(15589) if j not in set(zeros_z)]
    assert len(old_kept) == 15200
    latest = [old_kept[j] for j in reduced["new_to_old_columns"]]
    assert latest == sorted(set(latest)) and len(latest) == 15038
    zeros_y = [old_kept[j] for j in reduced["eliminated_columns"]]
    assert len(zeros_y) == 162 and all(42 <= j < 5847 for j in zeros_y)
    assert all(reduced["old_to_new_columns"][j] == i for i, j in enumerate(reduced["new_to_old_columns"]))
    result = {
        "schema": "conway99.f0-orbit-population-domains.v1", "group_order": GROUP_ORDER,
        "actual_core_actions": component_actions, "signature_actions": actions,
        "selector_orbits": selectors, "edge_orbit_selector_blocks": edge_blocks,
        "edge_orbit_pair_orbits": edge_pair_orbits, "pair_orbit_selector_blocks": pair_blocks,
        "original15589_orbit_sizes": sizes,
        "old15200_to_original15589": old_kept, "new15038_to_original15589": latest,
        "old15200_orbit_sizes": [sizes[j] for j in old_kept],
        "new15038_orbit_sizes": [sizes[j] for j in latest],
        "original_Z_zero_columns": zeros_z, "original_Y_zero_columns": zeros_y,
        "inventory": {"original15589": inventory(sizes, range(15589)),
                      "old15200": inventory(sizes, old_kept),
                      "new15038": inventory(sizes, latest),
                      "removed_Z": inventory(sizes, zeros_z),
                      "removed_Y": inventory(sizes, zeros_y)},
        "literal_orbit_member_hashes": {"selector": sha(canonical(selectors)),
                                        "edge": sha(canonical(edge_orbits)),
                                        "pair": sha(canonical(pair_orbits))},
        "Burnside": burnside,
        "all_orbit_stabilizer_counts_checked": True,
        "all15200_and15038_actual_sizes_derived": True,
        "graph_automorphism_assumed": False,
        "nonlinear_block_population_identities_imposed": False,
        "population_formula": "Each invariant coordinate is the number of its active literal objects divided by its actual orbit size. Averaging uses all12 relabelings; every orbit object occurs with multiplicity12/orbit_size.",
    }
    return result, pairs


def lifted_row(row, sizes):
    terms = [[j, c * (GROUP_ORDER // sizes[j])] for j, c in row["terms"]]
    rhs = GROUP_ORDER * row["rhs"]
    divisor = math.gcd(abs(rhs), *(abs(c) for _, c in terms)) or 1
    result = dict(row, terms=[[j, c // divisor] for j, c in terms], rhs=rhs // divisor)
    coefficient_gcd = math.gcd(*(abs(c) for _, c in result["terms"])) if terms else 0
    assert all(type(c) is int and c for _, c in result["terms"])
    return result, divisor, coefficient_gcd


def lifted_matrix(parent, domain, deadline):
    sizes = domain["new15038_orbit_sizes"]
    old = parent["matrix"]
    assert old["variables"] == len(sizes) == 15038
    new = {"variables": len(sizes), "lower": 0, "upper_by_variable": sizes,
           "all_variables_required_integer": True, "equalities": [], "inequalities": []}
    divisors, contradictions, gcds = [], [], Counter()
    for kind in ("equalities", "inequalities"):
        for i, row in enumerate(old[kind]):
            changed, divisor, coefficient_gcd = lifted_row(row, sizes)
            new[kind].append(changed)
            divisors.append(divisor)
            if kind == "equalities":
                gcds[coefficient_gcd] += 1
                if (not coefficient_gcd and changed["rhs"]) or (coefficient_gcd and changed["rhs"] % coefficient_gcd):
                    contradictions.append({"row": i, "family": row["family"],
                                           "coefficient_gcd": coefficient_gcd, "rhs": changed["rhs"]})
            if i % 256 == 0:
                tick(deadline)
    assert (len(new["equalities"]), len(new["inequalities"])) == (5973, 21746)
    assert sum(len(r["terms"]) for k in ("equalities", "inequalities") for r in new[k]) == 1079832
    protected = parent["protected_old_PSD_rows"]
    assert len(protected) == 92
    old_to_new = {old_id: i for i, old_id in enumerate(parent["new_to_old_rows"])}
    protected_new = [old_to_new[i] for i in protected]
    assert len(set(protected_new)) == 92
    return new, {
        "positive_global_denominator_multiplier": GROUP_ORDER,
        "positive_primitive_divisor_per_combined_row": divisors,
        "coefficient_gcd_histogram_after_primitive_reduction": {str(k): v for k, v in sorted(gcds.items())},
        "individual_equality_gcd_contradictions": contradictions,
        "all92_PSD_combined_row_indices": protected_new,
        "old_positive_numerical_row_scales_preserved_as_provenance": parent["numerical_row_scales"],
        "numerical_scaling_for_new_count_variables_prepared": False,
        "maximum_integer_coefficient_bits": max(abs(c).bit_length() for k in ("equalities", "inequalities") for r in new[k] for j, c in r["terms"]),
        "all_rows_real_equivalent_under_count_scaling": True,
        "integrality_is_additional_necessary_condition": True,
    }


def selector_control(baseline, moments, domain, pairs, matrix):
    selected = set(load("selector_control")["incidence_witness"]["selected_columns"])
    assert len(selected) == 60
    data = baseline["validation"]
    sizes = domain["original15589_orbit_sizes"]
    counts = [sum(a in selected for a in orbit) for orbit in data["selector_orbits"]]
    counts += [0] * 5805
    counts += [sum(pairs[p][0] in selected and pairs[p][1] in selected for p in orbit)
               for orbit in moments["pair_orbits"]]
    assert all(0 <= n <= size for n, size in zip(counts, sizes))
    assert all(counts[j] == 0 for j in domain["original_Z_zero_columns"] + domain["original_Y_zero_columns"])
    image_sets = [{p[a] for a in selected} for p in domain["signature_actions"]]
    for oi, orbit in enumerate(data["selector_orbits"]):
        assert all(sum(a in image for image in image_sets) * len(orbit) == 12 * counts[oi] for a in orbit)
    for oi, orbit in enumerate(moments["pair_orbits"]):
        p = orbit[0]
        a, b = pairs[p]
        assert sum(a in image and b in image for image in image_sets) * len(orbit) == 12 * counts[5847 + oi]
    current = [counts[j] for j in domain["new15038_to_original15589"]]
    checked = Counter()
    for row in matrix["equalities"]:
        if row["family"] == "mixed":
            continue
        assert row["family"] in ("Gram", "population", "selector RLT equality")
        assert sum(c * current[j] for j, c in row["terms"]) == row["rhs"]
        checked[row["family"]] += 1
    return {"status": "PASS: old binary incidence controls only the selector/RLT/count-averaging block",
            "selected_columns": sorted(selected), "integer_selector_orbit_counts": counts[:42],
            "checked_equality_families": dict(checked),
            "all_complete_pair_population_counts_integer": True,
            "hypothetical_edge_control_is_all_zero": True,
            "mixed_equations_checked": False, "4416_selector_cuts_checked": False,
            "all92_PSD_rows_checked": False, "whole_model_feasibility_claimed": False}


def prepare(prefix, seconds):
    started = time.monotonic()
    deadline = started + seconds
    assert sha(Path(modular.__file__).read_bytes()) == MODULAR_SHA
    bindings = {k: {"path": "experiments/logs/root-prism-free/" + p, "sha256": h} for k, (p, h) in INPUTS.items()}
    controls = modular.controls()
    baseline, moments = load("baseline"), load("moments")
    old, joint, reduced = load("first_reduction"), load("joint"), load("zero_reduction")
    cold = load("zero_replay")
    assert cold["status"].startswith("PASS:") and cold["model_file_sha256"] == INPUTS["zero_reduction"][1]
    assert joint["matrix"]["equalities"][:5973] == old["matrix"]["equalities"]
    assert joint["matrix"]["inequalities"][:15719] == old["matrix"]["inequalities"]
    assert reduced["parent_matrix_sha256"] == sha(canonical(joint["matrix"]))
    domain, pairs = domains(baseline, moments, old, reduced, deadline)
    domain.update({"source_sha256": sha(Path(__file__).read_bytes()), "inputs": bindings})
    domain_artifact = save(Path(str(prefix) + "-domains.json.gz"), domain)
    print(json.dumps({"phase": "domains", "seconds": time.monotonic() - started,
                      "inventory": domain["inventory"]}), flush=True)
    matrix, arithmetic = lifted_matrix(reduced, domain, deadline)
    all15200_eq = [lifted_row(row, domain["old15200_orbit_sizes"])[0] for row in joint["matrix"]["equalities"]]
    arithmetic["all15200_integer_equality_rows"] = len(all15200_eq)
    arithmetic["all15200_integer_equalities_sha256"] = sha(canonical(all15200_eq))
    arithmetic["all15038_integer_equalities_sha256"] = sha(canonical(matrix["equalities"]))
    control = selector_control(baseline, moments, domain, pairs, matrix)
    model = {
        "schema": "conway99.f0-complete-integer-orbit-population-lift.v1",
        "source_sha256": sha(Path(__file__).read_bytes()), "modular_source_sha256": MODULAR_SHA,
        "inputs": bindings, "domain_artifact": domain_artifact,
        "matrix": matrix, "matrix_sha256": sha(canonical(matrix)), "row_lift": arithmetic,
        "controls": {"modular_bit_planes": controls, "selector_RLT": control},
        "counts": {"variables": 15038, "equalities": 5973, "inequalities": 21746,
                   "rows": 27719, "nonzeros": 1079832, "physical_PSD_directions": 92},
        "scope": {"global_prism_and_F_free_split18_component0_only": True,
                  "second_component_or_alignment_fixed": False,
                  "all480_selector_signatures_retained": True,
                  "actual_graph_automorphism_assumed": False,
                  "single_graph_orbit_populations_required_integer": True,
                  "nonlinear_population_block_identities_imposed": False,
                  "optimizer_calls": 0, "eigendecompositions": 0, "graph_constructed_or_excluded": False},
        "interpretation": "N_j=s_j*v_j is the number of active literal selector, exterior-edge or distinct-selector-pair objects in orbit j. Each parent row is multiplied by12 and divided by its stated positive primitive divisor after substitution v_j=N_j/s_j.",
    }
    model_artifact = save(Path(str(prefix) + "-model.json.gz"), model)
    print(json.dumps({"phase": "integer_lift", "seconds": time.monotonic() - started,
                      "gcd_contradictions": arithmetic["individual_equality_gcd_contradictions"],
                      "matrix_sha256": model["matrix_sha256"]}), flush=True)
    results = []
    for prime in (2, 3):
        result = modular.eliminate(matrix["equalities"], matrix["variables"], prime, deadline)
        results.append(result)
        print(json.dumps({"phase": "modular", "prime": prime, "status": result["status"],
                          "rank": result.get("computed_rank", result.get("prefix_rank")),
                          "processed": result["processed_equalities"], "seconds": result["seconds"]}), flush=True)
        if result["status"].startswith("INCONSISTENT"):
            break
    field = {"schema": "conway99.f0-orbit-population-finite-field-checks.v1",
             "source_sha256": sha(Path(__file__).read_bytes()), "modular_source_sha256": MODULAR_SHA,
             "model_artifact": model_artifact, "equality_sha256": arithmetic["all15038_integer_equalities_sha256"],
             "results": results, "optimizer_calls": 0,
             "consistency_does_not_prove_bounded_integer_or_graph_feasibility": True}
    field_artifact = save(Path(str(prefix) + "-arithmetic.json.gz"), field)
    report = {"status": "PREPARED: exact complete orbit-population lift and bounded arithmetic checks",
              "source_sha256": sha(Path(__file__).read_bytes()), "modular_source_sha256": MODULAR_SHA,
              "artifacts": {"domains": domain_artifact, "model": model_artifact, "arithmetic": field_artifact},
              "inventory": domain["inventory"], "counts": model["counts"],
              "controls": model["controls"],
              "individual_equality_gcd_contradictions": arithmetic["individual_equality_gcd_contradictions"],
              "modular_summary": [{k: r[k] for k in ("prime", "status", "processed_equalities", "total_equalities", "computed_rank", "prefix_rank", "seconds") if k in r} for r in results],
              "declared_total_seconds": seconds, "seconds": time.monotonic() - started,
              "optimizer_calls": 0, "independent_arithmetic_replay_required": True,
              "whole_component_exclusion_claimed": False}
    save(Path(str(prefix) + "-preparation.json"), report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-prefix", required=True, type=Path)
    parser.add_argument("--seconds", type=float, default=120)
    args = parser.parse_args()
    assert 0 < args.seconds <= 120
    report = prepare(args.output_prefix.resolve(), args.seconds)
    print(json.dumps(report, indent=2), flush=True)


if __name__ == "__main__":
    main()
