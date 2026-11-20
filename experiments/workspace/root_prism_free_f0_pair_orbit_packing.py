"""Preparation and bounded exact packing bounds for every retained F0 Z orbit.

Pair objects retain their literal endpoint unions, including overlaps.
Only previously proved-zero selector pairs define incompatibility.
Preparation does not construct or solve the complete compatibility family.
The separate scan and certificate replay have fixed 60-second budgets.
"""
import argparse
from collections import Counter
import gzip
import hashlib
from itertools import combinations
import json
from pathlib import Path
import time

import finite_graph_clique_certificate as clique

ROOT = Path(__file__).resolve().parents[2]
BASE = "experiments/logs/root-prism-free/"
HELPER_SHA = "ef97e243a4140ca741097cb8c237d080e926d5f47f2ccca01abc662ff042834b"
INPUTS = {
    "domains": ("f0-orbit-populations02-domains.json.gz", "4f079468530dba0746512cc4afce01666b2a63a2c8f35f66a4660a4fe3bab8ab"),
    "domain_cold": ("f0-orbit-populations02-independent-replay.json", "a8bb55cbf773ea75a8cd1d5a18b50281ecbe08f6074cea04fb2d75799138273a"),
    "moments": ("f0-second-moments-preparation02.json.gz", "404d91da35c798ba248887c22a7500957947e24b71d5197dc44432460e6d219e"),
    "moment_cold": ("f0-second-moments-preparation02-cold-replay.json", "e495dbc7281f420caab1f3be88e9263ab8273da6ae88a7ea4e1e72c30eaa1fcd"),
    "current_plan": ("f0-character-pool-model01/plan.json.gz", "b3179e520d5913530c7d3cfae27529b5717be26c763de024b725c38959aa2aef"),
    "two_proofs": ("f0-pair-population-two-proof01.json", "59663e63423ef0aaf8bc01024dc7c95e4f87735a72f151c477dba9a184eace5f"),
    "two_proofs_cold": ("f0-pair-population-two-proof01-cold.json", "fc4b4be2992388e1ac9c6f2a4f2fe11ef86756321d8d729bcb6e42b0d658b312"),
}
LIMITS = {"preparation_seconds": 30, "scan_seconds": 60, "cold_seconds": 60,
          "uncompressed_ledger_bytes": 64 * 1024 * 1024,
          "optimizer_calls": 0, "automatic_retries": 0}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def tick(deadline):
    if time.monotonic() >= deadline:
        raise TimeoutError("pair-orbit packing cooperative deadline")


def pair_id(a, b):
    a, b = sorted((a, b))
    assert 0 <= a < b < 480
    return a * (959 - a) // 2 + b - a - 1


def load(root, deadline):
    assert sha(Path(clique.__file__).read_bytes()) == HELPER_SHA
    data = {}
    for key, (name, digest) in INPUTS.items():
        tick(deadline)
        raw = (root / BASE / name).read_bytes()
        assert sha(raw) == digest, key
        decoded = json.loads(gzip.decompress(raw) if name.endswith(".gz") else raw)
        if key == "moments":
            decoded = {k: decoded[k] for k in ("selector_actions", "selector_orbits", "pair_to_orbit",
                       "pair_orbits", "zero_pair_orbits", "zero_moment_certificates", "original_selector_equalities")}
        elif key == "current_plan":
            decoded = {k: decoded[k] for k in ("source_sha256", "old_to_target_columns",
                       "target_to_old_columns", "target_variable_domains")}
        data[key] = decoded
    for key in ("domain_cold", "moment_cold", "two_proofs_cold"):
        assert data[key]["status"].startswith("PASS")
    assert data["moment_cold"]["artifact_sha256"] == INPUTS["moments"][1]
    assert data["two_proofs_cold"]["record_sha256"] == INPUTS["two_proofs"][1]
    return data


def zero_neighbors(size, forbidden):
    adjacency = [0] * size
    for a, b in forbidden:
        assert 0 <= a < b < size
        adjacency[a] |= 1 << b
        adjacency[b] |= 1 << a
    return adjacency


def compatibility(pairs, forbidden_neighbors):
    """Bitset construction; never regards a repeated endpoint as a conflict."""
    n = len(pairs)
    adjacency, witnesses = [0] * n, []
    for a, b in pairs:
        assert a < b and not (forbidden_neighbors[a] >> b) & 1
    for i, (a, b) in enumerate(pairs):
        for j in range(i + 1, n):
            c, d = pairs[j]
            forbidden = (forbidden_neighbors[a] | forbidden_neighbors[b]) & ((1 << c) | (1 << d))
            if not forbidden:
                adjacency[i] |= 1 << j
                adjacency[j] |= 1 << i
            else:
                union = sorted({a, b, c, d})
                witness = next((u, v) for u, v in combinations(union, 2)
                               if (forbidden_neighbors[u] >> v) & 1)
                witnesses.append([i, j, list(witness)])
    clique.validate(adjacency)
    return adjacency, witnesses


def endpoint_controls():
    pairs = list(combinations(range(4), 2))
    checked = assignments = shared_endpoint_cases = 0
    for zero_mask in range(1 << len(pairs)):
        forbidden = {p for i, p in enumerate(pairs) if (zero_mask >> i) & 1}
        allowed = [p for p in pairs if p not in forbidden]
        for mask in range(1 << len(allowed)):
            objects = [p for i, p in enumerate(allowed) if (mask >> i) & 1]
            adjacency, witnesses = compatibility(objects, zero_neighbors(4, forbidden))
            optimum = clique.maximum_clique(adjacency)["maximum"]
            literal_maximum = 0
            for selected_mask in range(16):
                selected = {i for i in range(4) if (selected_mask >> i) & 1}
                if not any({a, b}.issubset(selected) for a, b in forbidden):
                    active = sum({a, b}.issubset(selected) for a, b in objects)
                    assert active <= optimum
                    literal_maximum = max(literal_maximum, active)
                assignments += 1
            assert literal_maximum == optimum
            for i, j, witness in witnesses:
                assert tuple(witness) in forbidden and set(witness).issubset(set(objects[i]) | set(objects[j]))
            shared_endpoint_cases += any(set(a) & set(b) for a, b in combinations(objects, 2))
            checked += 1
    assert checked == 729 and assignments == 11664
    return {"complete_four_selector_zero_set_and_pair_site_models": checked,
            "Boolean_assignments": assignments, "models_with_shared_endpoints": shared_endpoint_cases}


def prepare(data, deadline):
    domains, moments, plan = [data[k] for k in ("domains", "moments", "current_plan")]
    actions = domains["signature_actions"]
    assert len(actions) == 12 and actions == moments["selector_actions"]
    assert all(sorted(g) == list(range(480)) for g in actions)
    action_index = {tuple(g): i for i, g in enumerate(actions)}
    assert len(action_index) == 12 and tuple(range(480)) in action_index
    composition = [[action_index[tuple(g[h[a]] for a in range(480))] for h in actions] for g in actions]
    assert domains["selector_orbits"] == moments["selector_orbits"]
    literal_pairs = list(combinations(range(480), 2))
    assert len(literal_pairs) == 114960
    assert all(pair_id(a, b) == i for i, (a, b) in enumerate(literal_pairs))
    pmap, orbits = moments["pair_to_orbit"], moments["pair_orbits"]
    assert len(pmap) == 114960 and len(orbits) == 9742
    assert sorted(i for orbit in orbits for i in orbit) == list(range(114960))
    zeros = {x - 5847 for x in domains["original_Z_zero_columns"]}
    assert len(zeros) == 389 and zeros == set(moments["zero_pair_orbits"])
    zero_ids = {i for p in zeros for i in orbits[p]}
    saved_zero = {p["pair_id"]: p for p in moments["zero_moment_certificates"]}
    assert len(saved_zero) == len(moments["zero_moment_certificates"]) == 4410
    assert set(saved_zero) == zero_ids
    kinds = Counter()
    for i in sorted(zero_ids):
        row = saved_zero[i]
        assert sorted((row["anchor"], row["other"])) == list(literal_pairs[i])
        kinds[row["kind"]] += 1
        if row["kind"] == "quota-one nonnegative lifted equality":
            equality = moments["original_selector_equalities"][row["selector_Gram_row"]]
            assert equality["family"] == "Gram" and equality["quota"] == 1
            assert all(a in equality["support"] for a in literal_pairs[i])
        else:
            assert row["kind"] == "certified binary motif times selector"
            assert row["literal_polynomial"] == "z_a*(z_a+z_b-1)=z_a*z_b"
    assert kinds == {"quota-one nonnegative lifted equality": 4320,
                     "certified binary motif times selector": 90}
    for g in actions:
        tick(deadline)
        assert {pair_id(g[a], g[b]) for a, b in (literal_pairs[i] for i in zero_ids)} == zero_ids
    old_to_new = {old: new for new, old in enumerate(domains["new15038_to_original15589"])}
    assert plan["source_sha256"] == "b3029a3a197ec31305f74dead2b28f51beaf219cb2e9e289dc8f250db42a6943"
    assert plan["old_to_target_columns"][:15038] == list(range(15038))
    assert plan["target_to_old_columns"][:15038] == list(range(15038))
    records = []
    for po, orbit in enumerate(orbits):
        tick(deadline)
        assert orbit == sorted(set(orbit)) and 1 <= len(orbit) <= 12
        assert all(pmap[i] == po for i in orbit)
        a, b = literal_pairs[orbit[0]]
        images = [pair_id(g[a], g[b]) for g in actions]
        assert set(images) == set(orbit)
        assert all(images.count(i) == 12 // len(orbit) for i in orbit)
        if po in zeros:
            assert 5847 + po not in old_to_new
            continue
        column = old_to_new[5847 + po]
        domain = plan["target_variable_domains"][column]
        assert len(domain) % 2 == 0 and domain
        assert all(type(x) is int for x in domain)
        assert all(domain[i] <= domain[i + 1] for i in range(0, len(domain), 2))
        assert all(domain[i] + 1 < domain[i + 1] for i in range(1, len(domain) - 1, 2))
        assert 0 <= domain[0] <= domain[-1] <= len(orbit)
        records.append({"pair_orbit": po, "literal_pair_ids": orbit,
                        "original_column": 5847 + po, "count_column": column,
                        "selector_orbits": domains["pair_orbit_selector_blocks"][po],
                        "anchor_transports": [images.index(i) for i in orbit],
                        "orbit_size_upper_bound": len(orbit), "current_domain": domain})
    assert len(records) == 9353
    assert sorted(r["count_column"] for r in records) == list(range(5685, 15038))
    sizes = Counter(len(r["literal_pair_ids"]) for r in records)
    assert sizes == {3: 12, 6: 263, 12: 9078}
    graph_controls = clique.controls()
    endpoint_checks = endpoint_controls()
    two_controls = []
    for case in data["two_proofs"]["proof"]["cases"]:
        left = [p[0] for p in case["literal_matching"]]
        index = {a: i for i, a in enumerate(left)}
        adjacency = [0] * 12
        for star in case["transported_star_certificates"]:
            adjacency[index[star["anchor"]]] = sum(1 << index[a] for a in star["possible_neighbors"])
        certificate = clique.maximum_clique(adjacency)
        assert certificate["maximum"] == case["proved_count_upper_bound"] == 2
        two_controls.append({"pair_orbit": case["pair_orbit"], "maximum": 2,
                             "certificate": certificate})
    tick(deadline)
    return {"status": "PASS: complete retained-Z scope; production graphs unqueried",
            "retained_orbits": records, "removed_zero_orbits": sorted(zeros),
            "retained_pair_sites": sum(len(r["literal_pair_ids"]) for r in records),
            "orbit_size_histogram": dict(sizes), "pair_orbits_total": 9742,
            "literal_pair_sites_total": 114960, "retained_orbit_count": 9353,
            "prior_zero_literal_pairs": 4410, "prior_zero_certificate_kinds": dict(kinds),
            "all_zero_set_action_checks": 12 * 4410, "actual_action_composition": composition,
            "all_orbit_anchor_images_checked": 12 * 9742,
            "maximum_full_pair_compatibility_checks": sum(n * (n - 1) // 2 * count for n, count in sizes.items()),
            "maximum_literal_endpoint_pair_checks": 6 * sum(n * (n - 1) // 2 * count for n, count in sizes.items()),
            "maximum_anchor_subset_states": sum((1 << (n - 1)) * count for n, count in sizes.items()),
            "maximum_full_subset_states_without_transitivity": sum((1 << n) * count for n, count in sizes.items()),
            "current_upper_bound_histogram": dict(Counter(r["current_domain"][-1] for r in records)),
            "controls": {"clique_helper": graph_controls, "endpoint_unions": endpoint_checks,
                         "previous_two_proofs": two_controls},
            "limits": LIMITS, "full_family_graphs_constructed": 0,
            "host_graph_automorphism_assumed": False,
            "comparison_does_not_claim_independence_from_all_existing_inequalities": True}


def scan_context(data):
    moments = data["moments"]
    pairs = list(combinations(range(480), 2))
    zero_ids = {p["pair_id"] for p in moments["zero_moment_certificates"]}
    return {"pairs": pairs, "zero_ids": zero_ids,
            "zero_neighbors": zero_neighbors(480, (pairs[i] for i in zero_ids)),
            "actions": data["domains"]["signature_actions"]}


def check_graph_actions(pairs, adjacency, scope, context):
    positions = {pair: i for i, pair in enumerate(pairs)}
    for gi, g in enumerate(context["actions"]):
        move = [positions[tuple(sorted((g[a], g[b])))] for a, b in pairs]
        assert sorted(move) == list(range(len(pairs)))
        for i in range(len(pairs)):
            mapped = sum(1 << move[j] for j in range(len(pairs)) if (adjacency[i] >> j) & 1)
            assert mapped == adjacency[move[i]]
    for i, gi in enumerate(scope["anchor_transports"]):
        g = context["actions"][gi]
        assert tuple(sorted((g[pairs[0][0]], g[pairs[0][1]]))) == pairs[i]


def principal(adjacency, vertices):
    return [sum(1 << j for j, b in enumerate(vertices) if (adjacency[a] >> b) & 1) for a in vertices]


def produce_one(scope, context, deadline):
    tick(deadline)
    pairs = [context["pairs"][i] for i in scope["literal_pair_ids"]]
    adjacency, witnesses = compatibility(pairs, context["zero_neighbors"])
    check_graph_actions(pairs, adjacency, scope, context)
    neighbors = [i for i in range(len(pairs)) if (adjacency[0] >> i) & 1]
    proof = clique.maximum_clique(principal(adjacency, neighbors), lambda: tick(deadline))
    optimum = 1 + proof["maximum"]
    selected_objects = [0] + [neighbors[i] for i in proof["clique"]]
    selected = sorted({a for i in selected_objects for a in pairs[i]})
    assert all(pair_id(a, b) not in context["zero_ids"] for a, b in combinations(selected, 2))
    assert sum(a in selected and b in selected for a, b in pairs) == optimum
    return {"pair_orbit": scope["pair_orbit"], "count_column": scope["count_column"],
            "adjacency": adjacency,
            "incompatibility_zero_pairs": [[i, j, pair_id(*w)] for i, j, w in witnesses],
            "anchor_neighbors": neighbors, "anchor_clique_certificate": proof,
            "maximum_compatible_pair_objects": optimum,
            "attaining_partial_selector_set": selected,
            "previous_current_upper_bound": scope["current_domain"][-1],
            "improves_current_upper_bound": optimum < scope["current_domain"][-1],
            "improves_orbit_size_bound": optimum < len(pairs)}


def verify_one(row, scope, context):
    assert row["pair_orbit"] == scope["pair_orbit"] and row["count_column"] == scope["count_column"]
    pairs = [context["pairs"][i] for i in scope["literal_pair_ids"]]
    # Independent literal-union reconstruction, rather than the producer's bitset test.
    adjacency, witnesses = [0] * len(pairs), []
    for i, j in combinations(range(len(pairs)), 2):
        union = sorted(set(pairs[i]) | set(pairs[j]))
        forbidden = [pair_id(a, b) for a, b in combinations(union, 2)
                     if pair_id(a, b) in context["zero_ids"]]
        if forbidden:
            witnesses.append([i, j, forbidden[0]])
        else:
            adjacency[i] |= 1 << j
            adjacency[j] |= 1 << i
    assert adjacency == row["adjacency"] and witnesses == row["incompatibility_zero_pairs"]
    check_graph_actions(pairs, adjacency, scope, context)
    neighbors = [i for i in range(len(pairs)) if (adjacency[0] >> i) & 1]
    assert neighbors == row["anchor_neighbors"]
    optimum = 1 + clique.verify(principal(adjacency, neighbors), row["anchor_clique_certificate"])
    assert optimum == row["maximum_compatible_pair_objects"]
    selected = row["attaining_partial_selector_set"]
    assert selected == sorted(set(selected)) and all(type(a) is int and 0 <= a < 480 for a in selected)
    assert all(pair_id(a, b) not in context["zero_ids"] for a, b in combinations(selected, 2))
    assert sum(a in selected and b in selected for a, b in pairs) == optimum
    assert row["previous_current_upper_bound"] == scope["current_domain"][-1]
    assert row["improves_current_upper_bound"] == (optimum < scope["current_domain"][-1])
    assert row["improves_orbit_size_bound"] == (optimum < len(pairs))


def empty_summary():
    return {"completed_orbits": 0, "clique_bound_histogram": Counter(),
            "anchor_neighborhood_size_histogram": Counter(), "subset_recurrences": 0,
            "improved_orbit_size_bounds": 0, "improved_current_bounds": []}


def record_summary(state, row):
    state["completed_orbits"] += 1
    state["clique_bound_histogram"][row["maximum_compatible_pair_objects"]] += 1
    state["anchor_neighborhood_size_histogram"][len(row["anchor_neighbors"])] += 1
    state["subset_recurrences"] += len(row["anchor_clique_certificate"]["subset_values"])
    state["improved_orbit_size_bounds"] += row["improves_orbit_size_bound"]
    if row["improves_current_upper_bound"]:
        state["improved_current_bounds"].append({"pair_orbit": row["pair_orbit"], "count_column": row["count_column"],
                                               "old_upper": row["previous_current_upper_bound"],
                                               "new_upper": row["maximum_compatible_pair_objects"]})


def write(path, record):
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = canonical(record) + b"\n"
    with path.open("xb") as stream:
        stream.write(gzip.compress(raw, mtime=0) if path.suffix == ".gz" else raw)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["prepare", "scan", "replay"])
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--preparation", type=Path)
    parser.add_argument("--record", type=Path)
    parser.add_argument("--ledger", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    start = time.monotonic()
    source = sha(Path(__file__).read_bytes())
    seconds = LIMITS[{"prepare": "preparation_seconds", "scan": "scan_seconds", "replay": "cold_seconds"}[args.mode]]
    deadline = start + seconds
    data = load(args.root, deadline)
    if args.mode == "prepare":
        assert args.preparation is args.record is args.ledger is None
        result = {"schema": "conway99.f0.pair_orbit_packing.preparation.v1",
                  "source_sha256": source, "helper_sha256": HELPER_SHA, "inputs": INPUTS,
                  "scope": prepare(data, deadline), "seconds": time.monotonic() - start}
        write(args.output, result)
        print(json.dumps({"status": result["scope"]["status"], "seconds": result["seconds"],
                          "orbits": result["scope"]["retained_orbit_count"],
                          "anchor_subset_bound": result["scope"]["maximum_anchor_subset_states"]}))
        return
    assert args.preparation is not None and args.ledger is not None
    prep_raw = args.preparation.read_bytes()
    prep = json.loads(gzip.decompress(prep_raw) if args.preparation.suffix == ".gz" else prep_raw)
    assert prep["source_sha256"] == source and prep["helper_sha256"] == HELPER_SHA
    assert prep["inputs"] == json.loads(json.dumps(INPUTS)) and prep["scope"]["limits"] == LIMITS
    scopes = prep["scope"]["retained_orbits"]
    assert len(scopes) == 9353
    context = scan_context(data)
    del data
    initialization = time.monotonic() - start
    state, raw_hash, raw_bytes = empty_summary(), hashlib.sha256(), 0
    terminal = "COMPLETE"
    error = None
    if args.mode == "scan":
        assert args.record is None
        args.ledger.parent.mkdir(parents=True, exist_ok=True)
        with args.ledger.open("xb") as sink:
            with gzip.GzipFile(filename="", mode="wb", fileobj=sink, mtime=0) as stream:
                try:
                    for scope in scopes:
                        row = produce_one(scope, context, deadline)
                        raw = canonical(row) + b"\n"
                        if raw_bytes + len(raw) > LIMITS["uncompressed_ledger_bytes"]:
                            raise TimeoutError("declared uncompressed certificate budget")
                        stream.write(raw)
                        raw_hash.update(raw)
                        raw_bytes += len(raw)
                        record_summary(state, row)
                except (TimeoutError, AssertionError, KeyError, ValueError) as exc:
                    terminal = "UNKNOWN" if isinstance(exc, TimeoutError) else "ERROR"
                    error = {"type": type(exc).__name__, "message": str(exc)}
        result = {"schema": "conway99.f0.pair_orbit_packing.scan.v1",
                  "status": terminal + ": retained-Z pair packing scan", "complete": state["completed_orbits"] == len(scopes),
                  "source_sha256": source, "helper_sha256": HELPER_SHA,
                  "preparation_sha256": sha(prep_raw), "inputs": INPUTS,
                  "ledger_sha256": sha(args.ledger.read_bytes()), "ledger_raw_sha256": raw_hash.hexdigest(),
                  "ledger_raw_bytes": raw_bytes, "summary": state, "error": error,
                  "initialization_seconds": initialization, "seconds": time.monotonic() - start,
                  "limits": LIMITS, "optimizer_calls": 0, "graph_or_incidence_exclusion_claimed": False}
        write(args.output, result)
    else:
        assert args.record is not None
        record_raw = args.record.read_bytes()
        saved = json.loads(gzip.decompress(record_raw) if args.record.suffix == ".gz" else record_raw)
        assert saved["source_sha256"] == source and saved["helper_sha256"] == HELPER_SHA
        assert saved["preparation_sha256"] == sha(prep_raw)
        assert saved["ledger_sha256"] == sha(args.ledger.read_bytes())
        with gzip.open(args.ledger, "rb") as stream:
            try:
                for i, raw in enumerate(stream):
                    tick(deadline)
                    assert i < len(scopes)
                    row = json.loads(raw)
                    verify_one(row, scopes[i], context)
                    record_summary(state, row)
                    raw_hash.update(raw)
                    raw_bytes += len(raw)
                assert state["completed_orbits"] == saved["summary"]["completed_orbits"]
                assert json.loads(json.dumps(state)) == saved["summary"]
                assert raw_hash.hexdigest() == saved["ledger_raw_sha256"]
                assert raw_bytes == saved["ledger_raw_bytes"]
                assert saved["complete"] == (state["completed_orbits"] == len(scopes))
                terminal = "PASS"
            except (TimeoutError, AssertionError, KeyError, ValueError) as exc:
                terminal = "UNKNOWN" if isinstance(exc, TimeoutError) else "ERROR"
                error = {"type": type(exc).__name__, "message": str(exc)}
        result = {"status": terminal + ": independent literal graph and clique-certificate replay",
                  "source_sha256": source, "helper_sha256": HELPER_SHA,
                  "record_sha256": sha(record_raw), "preparation_sha256": sha(prep_raw),
                  "complete_saved_prefix_checked": terminal == "PASS",
                  "checked_orbits": state["completed_orbits"], "error": error,
                  "initialization_seconds": initialization, "seconds": time.monotonic() - start,
                  "optimizer_calls": 0, "maximum_clique_searches": 0}
        write(args.output, result)
    print(json.dumps({"status": result["status"], "seconds": result["seconds"],
                      "completed_orbits": state["completed_orbits"], "error": error}))


if __name__ == "__main__":
    main()
