"""Independent complete allocation replay of the 306 finite skew gauges.

Only the Python standard library is imported. Every base gauge is allocated
from all original edges. Every transported positive allocation is rebuilt
with the transported original endpoint order after complete action checks.
"""
import argparse
from itertools import combinations, permutations
import gzip
import hashlib
import json
from math import gcd
from pathlib import Path
import resource
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
LOGS = "experiments/logs/root-prism-free/"
BINDINGS = {
    "configuration": (LOGS+"f0-support-skew-gauge-configuration01.json", "c53ae366cf1fcbee15fc403bcf1a5fc2138fc673137c98f78370f599ed05c0b8"),
    "report": (LOGS+"f0-support-skew-gauge-run01/report.json", "4cba8f521f56fa84cc5df34e46a86deadbff0f5cd74e8369d539faf9240866d7"),
    "owner": (LOGS+"f0-support-skew-gauge-run01/owner.json", "a515deae91df73c01f3dedd2d5873ec109ee3731a41b18e3365442745e3d129e"),
    "census": (LOGS+"f0-support-skew-gauge-run01/complete-census.json.gz", "612ec034b7dc81fd422010a74c01be9b469e7b3de92b4ea88055732e9d13047b"),
    "export": (LOGS+"f0-support-skew-gauge-run01/proposed-selector-cuts.json.gz", "90e529ca530d7b7047edbfe47b8c90643692bc54af1840fcab9be39bfe286fc1"),
}
SECONDS = 120
OWNER_SECONDS = 135


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def value_sha(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def read(pair):
    path, expected = pair
    raw = (ROOT / path).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == expected, path
    return json.loads(gzip.decompress(raw) if path.endswith(".gz") else raw)


def write(path, value):
    raw = canonical(value) + b"\n"
    with path.open("xb") as stream:
        stream.write(raw)
    return {"path": str(path.relative_to(ROOT)), "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}


def allocation(triples, targets, edges, potentials, support, order=None):
    assert all(not any(potentials[a]) for a in range(len(triples)) if a not in support)
    delta = [sum(v * q for v, q in zip(vector, target)) for vector, target in zip(potentials, targets)]
    coefficients, positives, internal_weights = list(delta), [], []
    order = list(range(len(triples))) if order is None else order
    for a, b in edges:
        va, vb, ha, hb = potentials[a], potentials[b], triples[a], triples[b]
        weight = va[hb[0]] + va[hb[1]] + va[hb[2]] + vb[ha[0]] + vb[ha[1]] + vb[ha[2]]
        inside_a, inside_b = a in support, b in support
        if inside_a and inside_b:
            internal_weights.append(weight)
        if weight <= 0:
            continue
        assert inside_a or inside_b
        if inside_a and inside_b:
            endpoint, kind = (a if order[a] < order[b] else b), "internal"
        else:
            endpoint, kind = (b if inside_a else a), "boundary"
        coefficients[endpoint] -= weight
        positives.append((a, b, weight, endpoint, kind))
    return delta, coefficients, positives, internal_weights


def transport(delta, positives, support, image):
    n = len(delta)
    assert sorted(image) == list(range(n))
    inverse = [0] * n
    for a, b in enumerate(image):
        inverse[b] = a
    moved_support = {image[a] for a in support}
    moved = [0] * n
    for a, value in enumerate(delta):
        moved[image[a]] = value
    for a, b, weight, endpoint, kind in positives:
        ia, ib, chosen = image[a], image[b], image[endpoint]
        if ia in moved_support and ib in moved_support:
            actual = ia if inverse[ia] < inverse[ib] else ib
            assert kind == "internal"
        else:
            actual = ib if ia in moved_support else ia
            assert kind == "boundary" and ((ia in moved_support) != (ib in moved_support))
        assert chosen == actual
        moved[chosen] -= weight
    return moved


def controls():
    triples = [[0, 1, 2]] * 3
    targets = [[1, 0, 0], [0, 0, 0], [0, 0, 0]]
    edges, potentials, support = [[0, 1], [0, 2], [1, 2]], [[2, 0, 0], [-1, 1, 0], [0, 0, 0]], {0, 1}
    delta, coefficients, positive, _ = allocation(triples, targets, edges, potentials, support)
    assert coefficients == [0, 0, -2]
    for image in permutations(range(3)):
        inverse = [image.index(a) for a in range(3)]
        moved_edges = sorted([sorted([image[a], image[b]]) for a, b in edges])
        moved_potentials = [potentials[inverse[a]] for a in range(3)]
        moved_targets = [targets[inverse[a]] for a in range(3)]
        moved_support = {image[a] for a in support}
        direct = allocation(triples, moved_targets, moved_edges, moved_potentials, moved_support, inverse)[1]
        assert transport(delta, positive, support, image) == direct
    image = [1, 0, 2]
    incorrect = allocation(triples, [targets[1], targets[0], targets[2]], edges,
                           [potentials[1], potentials[0], potentials[2]], {0, 1})[1]
    assert incorrect != transport(delta, positive, support, image)
    return {"status": "PASS_INDEPENDENT_GAUGE_ALLOCATION_TRANSPORT_CONTROLS", "vertex_permutations": 6,
            "changed_numeric_endpoint_order_detected": True, "optimizer_calls": 0, "native_imports": 0}


def domain(saved):
    core = saved["component_core_rows"]
    assert len(core) == 21 and all(type(row) is int and 0 <= row < (1 << 21) for row in core)
    assert all(not (core[i] >> i & 1) for i in range(21))
    assert all((core[i] >> j & 1) == (core[j] >> i & 1) for i in range(21) for j in range(21))
    gram = [[12*int(i == j)+2-(core[3+i]&core[3+j]).bit_count()-((core[3+i]>>(3+j))&1) for j in range(18)] for i in range(18)]
    triples = []
    for h in combinations(range(18), 3):
        if any(sum(j//6 == f for j in h) == 3 for f in range(3)):
            continue
        if any(gram[i][j] == 0 for i, j in combinations(h, 2)):
            continue
        if any(sum(int(i == j or ((core[3+i] >> (3+j)) & 1)) for j in h) > 2 for i in range(18)):
            continue
        triples.append(list(h))
    assert triples == saved["signature_domain"] and len(triples) == 480
    targets = [[2-int(i in h)-sum((core[3+i] >> (3+j)) & 1 for j in h) for i in range(18)] for h in triples]
    assert targets == saved["row_targets"] and all(sum(q) == 24 and min(q) >= 0 for q in targets)
    sets = list(map(set, triples))
    edges, neighbors = [], [[] for _ in triples]
    for a, b in combinations(range(480), 2):
        if len(sets[a] & sets[b]) > 1 or any(targets[a][i] == 0 for i in triples[b]) or any(targets[b][i] == 0 for i in triples[a]):
            continue
        edges.append([a, b]); neighbors[a].append(b); neighbors[b].append(a)
    assert len(edges) == 68394 and neighbors == saved["possible_neighbor_signature_ids"]
    return core, triples, targets, gram, edges


def core_actions(core, triples, targets, edges, generators):
    group = {tuple(range(21))}
    changed = True
    while changed:
        expanded = group | {tuple(old[g[i]] for i in range(21)) for old in group for g in generators}
        changed = expanded != group
        group = expanded
    assert len(group) == 12
    position = {tuple(h): a for a, h in enumerate(triples)}
    edge_set = set(map(tuple, edges))
    result = []
    for g in sorted(group):
        assert sorted(g) == list(range(21)) and set(g[:3]) == set(range(3))
        assert all((core[i] >> j & 1) == (core[g[i]] >> g[j] & 1) for i in range(21) for j in range(21))
        sites = [g[i+3]-3 for i in range(18)]
        image = [position[tuple(sorted(sites[i] for i in h))] for h in triples]
        assert sorted(image) == list(range(480))
        assert {tuple(sorted([image[a], image[b]])) for a, b in edges} == edge_set
        assert all(targets[image[a]][sites[i]] == targets[a][i] for a in range(480) for i in range(18))
        result.append(image)
    return result


def run(output):
    started = time.monotonic()
    def check():
        if time.monotonic() - started >= SECONDS:
            raise TimeoutError("independent complete gauge replay deadline")
    config, report, owner, census, export = [read(BINDINGS[k]) for k in ("configuration", "report", "owner", "census", "export")]
    assert owner["report_accepted"] and owner["report_sha256"] == BINDINGS["report"][1]
    assert owner["deadline_overrun_seconds"] == 0 and owner["supervision"]["child_reaped"] and owner["supervision"]["returncode"] == 0
    assert owner["source_sha256"] == report["source_sha256"] == config["producer_sha256"]
    assert report["status"] == owner["status"] == "PASS_COMPLETE_FINITE_GAUGE_CENSUS_AWAITING_INDEPENDENT_COLD"
    assert report["configuration_sha256"] == export["configuration_sha256"] == BINDINGS["configuration"][1]
    assert report["complete_census_sha256"] == export["complete_census_sha256"] == BINDINGS["census"][1]
    assert report["proposed_selector_cuts_sha256"] == BINDINGS["export"][1]
    assert report["optimizer_calls"] == 0 and not report["native_solver_imported"]
    inputs = {}
    for name, ref in config["inputs"].items():
        if name == "replayed_registry":
            raw = (ROOT / ref["path"]).read_bytes()
            assert hashlib.sha256(raw).hexdigest() == ref["sha256"] == config["inputs"]["registry"]["sha256"]
        else:
            inputs[name] = read((ref["path"], ref["sha256"]))
    hashes = {name: ref["sha256"] for name, ref in config["inputs"].items()}
    assert report["input_hashes"] == export["input_hashes"] == hashes
    previous, previous_owner, cold, cold_owner = [inputs[k] for k in ("run", "run_owner", "cold", "cold_owner")]
    for receipt, name in ((previous_owner, "run"), (cold_owner, "cold")):
        assert receipt["report_accepted"] and receipt["report_sha256"] == hashes[name]
        assert receipt["deadline_overrun_seconds"] == 0 and receipt["supervision"]["child_reaped"] and receipt["supervision"]["returncode"] == 0
    assert cold["status"] == "PASS_COMPLETE_CALLED_PREFIXES_AND_EXACT_CERTIFICATES"
    assert cold["run_result_sha256"] == hashes["run"] and cold["run_owner_sha256"] == hashes["run_owner"]
    registry = inputs["registry"]
    assert len(registry) == previous["final_registry_rows"] == cold["final_replayed_registry_rows"] == 12481
    assert value_sha(registry) == previous["final_registry_sha256"] == cold["final_replayed_registry_sha256"] == config["parent_registry_value_sha256"]
    parent = {}
    for i, entry in enumerate(registry):
        row = entry["row"]
        assert type(row["rhs"]) is int and all(type(a) is int and 0 <= a < 480 and type(c) is int and c for a, c in row["terms"])
        assert [a for a, _ in row["terms"]] == sorted({a for a, _ in row["terms"]})
        assert entry["key"] == value_sha(row) and entry["key"] not in parent
        parent[entry["key"]] = (i, row)
    selected, shared, iteration = [inputs[k] for k in ("selection", "shared", "iteration")]
    assert selected == sorted(set(selected)) and len(selected) == 60 and all(type(a) is int and 0 <= a < 480 for a in selected)
    assert shared["selected_signature_ids"] == selected and shared["candidate_sha256"] == hashes["selection"]
    assert iteration["shared_sha256"] == hashes["shared"] and iteration["selection_sha256"] == hashes["selection"]
    assert iteration["universal_cuts_sha256"] == hashes["universal_cuts"]
    core, triples, targets, gram, edges = domain(inputs["domain"])
    assert [[sum(i in triples[a] and j in triples[a] for a in selected) for j in range(18)] for i in range(18)] == gram
    actions = core_actions(core, triples, targets, edges, inputs["domain"]["core_generators"])
    support = set(selected)
    baseline = [[0]*18 for _ in triples]
    values = shared["fixed_capacity_potentials"]["integer_potentials60_by18"]
    assert len(values) == 60 and all(len(v) == 18 and all(type(x) is int for x in v) for v in values)
    for a, v in zip(selected, values):
        baseline[a] = list(v)
    delta0, coeff0, positive0, internal0 = allocation(triples, targets, edges, baseline, support)
    assert sum(delta0[a] for a in selected) == 176 and sum(max(0, w) for w in internal0) == 172 and sum(coeff0[a] for a in selected) == 4
    old = inputs["universal_cuts"]
    assert old["raw_gap"] == 4 and old["total_target_demand_at_saved_selection"] == 176 and old["internal_positive_capacity"] == 172
    assert old["global_edge_sha256"] == value_sha(edges)
    assert old["positive_edge_allocation_sha256"] == value_sha([{"edge": [a,b], "weight": w, "allocated_endpoint": endpoint, "kind": kind} for a,b,w,endpoint,kind in positive0])
    expected_family = [(p, q, sign) for p, q in combinations(range(18), 2) for sign in (-1, 1)]
    assert config["site_pairs"] == [list(pair) for pair in combinations(range(18), 2)] and config["signs"] == [-1,1]
    assert len(census["families"]) == len(expected_family) == 306 and len(census["transport_coverage"]) == 3672
    assert census["inventory"] == report["inventory"] and census["all_parent_rows_must_remain"]
    assert export["all12481_parent_rows_must_remain"] and export["no_rows_selected_by_old_candidate_violation"]
    exported, provenance = export["rows_upper_zero"], export["row_provenance"]
    assert len(exported) == len(provenance) == report["new_distinct_rows"]
    recovered_rows, recovered_origins, seen, family_checks = [], [], {}, []
    checked_allocations = 0
    for index, (p, q, sign) in enumerate(expected_family):
        check()
        potentials = [list(v) for v in baseline]
        for a in selected:
            potentials[a][p] += sign * int(q in triples[a])
            potentials[a][q] -= sign * int(p in triples[a])
        delta, coefficients, positive, internal = allocation(triples, targets, edges, potentials, support)
        assert internal == internal0 and sum(delta[a] for a in selected) == 176
        assert sum(max(0, w) for w in internal) == 172 and sum(coefficients[a] for a in selected) == 4
        divisor = gcd(*(abs(c) for c in coefficients))
        assert divisor > 0 and 4 % divisor == 0
        family = {"index": index, "sites": [p,q], "sign": sign, "local_potentials_sha256": value_sha([potentials[a] for a in selected]),
                  "raw_coefficients": coefficients, "coefficient_gcd": divisor, "demand": 176, "capacity": 172,
                  "raw_gap": 4, "internal_edge_weights_unchanged": True}
        assert family == census["families"][index]
        for action_index, image in enumerate(actions):
            moved = transport(delta, positive, support, image)
            assert all(moved[image[a]] == coefficients[a] for a in range(480))
            assert sum(moved[image[a]] for a in selected) == 4
            row = {"terms": [[a, c//divisor] for a, c in enumerate(moved) if c], "rhs": 0}
            assert all(c % divisor == 0 for c in moved)
            key = value_sha(row)
            origin = {"gauge_index": index, "sites": [p,q], "sign": sign, "core_action_index": action_index}
            if key in parent:
                parent_index, old_row = parent[key]
                assert row == old_row
                expected = dict(origin, row_key=key, parent_index=parent_index, parent_row_key=key)
            else:
                if key not in seen:
                    seen[key] = len(recovered_rows)
                    recovered_rows.append(row["terms"])
                    recovered_origins.append({"row_key": key, "origins": []})
                at = seen[key]
                assert recovered_rows[at] == row["terms"]
                recovered_origins[at]["origins"].append(origin)
                expected = dict(origin, row_key=key, new_row_index=at)
            assert expected == census["transport_coverage"][12*index+action_index]
            checked_allocations += len(positive)
        family_checks.append({"index": index, "raw_coefficients_sha256": value_sha(coefficients), "positive_edges": len(positive), "raw_gap": 4})
    assert recovered_rows == exported and recovered_origins == provenance
    assert len(recovered_rows) == report["new_distinct_rows"] and 12481+len(recovered_rows) == report["possible_following_registry_rows"]
    assert max(abs(c) for row in recovered_rows for _, c in row) == report["maximum_absolute_coefficient"]
    assert max(sum(abs(c) for _, c in row) for row in recovered_rows) == report["maximum_absolute_activity"]
    check()
    assert not any(name.split(".")[0] in {"highspy", "ortools", "numpy", "scipy"} for name in sys.modules)
    result = {"status": "PASS_INDEPENDENT_COMPLETE_SUPPORT_SKEW_GAUGE_ALLOCATIONS",
              "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "bindings": {k: {"path": v[0], "sha256": v[1]} for k,v in BINDINGS.items()},
              "accepted_parent_registry_value_sha256": value_sha(registry), "parent_rows": 12481,
              "gauges_recomputed": 306, "complete_base_edge_weights_checked": 306*68394,
              "transports_checked": 3672, "transported_positive_allocations_rebuilt": checked_allocations,
              "all_transports_use_original_endpoint_order": True,
              "all_actions_checked_on_complete_edge_domain": True,
              "new_distinct_rows": len(recovered_rows), "following_registry_rows_if_all_parent_rows_preserved": 12481+len(recovered_rows),
              "all_provenance_and_parent_matches_checked": True,
              "new_rows_value_sha256": value_sha(recovered_rows), "family_checks": family_checks,
              "complete_census_is_finite_not_exhaustive_of_all_skew_potentials": True,
              "optimizer_calls": 0, "native_imports": 0, "whole_component_excluded": False,
              "seconds": time.monotonic()-started, "peak_rss_KiB": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    write(output, result)
    return result


if __name__ == "__main__":
    assert __debug__
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("controls", "run"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.mode == "controls":
        result = controls()
        result["source_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        write(args.output.resolve(), result)
    else:
        result = run(args.output.resolve())
    print(json.dumps({"status": result["status"], "seconds": result.get("seconds")}), flush=True)
