"""Finite exact support-restricted skew gauges of one accepted shared cut.

For every site pair p<q and sign t in {-1,1}, replace the saved potential
v_a by v_a+t*(h_a[q] e_p-h_a[p] e_q) on its saved sixty-selector support.
Check unchanged demand and every internal edge weight. Recompute the full
universal allocation by exact boundary-weight differences, then transport
it under all twelve checked core actions. No optimizer is imported or run.
The generated rows require a separate independent cold before seed use.
"""
import argparse
from collections import Counter, defaultdict
import gzip
import hashlib
import importlib.util
from itertools import combinations
import json
from math import gcd
from pathlib import Path
import resource
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
WORK = "experiments/workspace/"
SOURCES = {
    "allocation": (WORK + "root_prism_free_f0_symmetric_selector_cut.py", "15ec937609b7de44b808e9de7053bb9ee080ddf732a3defd2b23577c026fe274"),
    "legacy_lift": (WORK + "root_prism_free_f0_shared_deficit_separator.py", "6bc6944ed00713d384251ab54e54684e6f5ea29300f9ff243df5282f522375bf"),
    "supervisor": (WORK + "root_prism_free_f0_fixed_selection_exterior_query.py", "bbe476e5a7a13800c08265d4db541b7e8c7edf2277be03f6d06db134926891e3"),
    "parent_controller": (WORK + "root_prism_free_f0_direct_master_continuation_v6.py", "094c143d63011c0fee6dab95e2850634fd70fb1f7564b8c3e682cb02ef2f21c8"),
}
LIMITS = {"prepare": 60, "run": 120}
MAX_ACTIVITY = 1 << 60


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def value_sha(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def digest(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def save(path, value):
    raw = canonical(value) + b"\n"
    if path.suffix == ".gz":
        raw = gzip.compress(raw, compresslevel=6, mtime=0)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(raw)
    temporary.replace(path)


def source(key):
    name, expected = SOURCES[key]
    path = ROOT / name
    assert digest(path) == expected
    spec = importlib.util.spec_from_file_location("support_skew_" + key, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check_time(deadline):
    if time.monotonic() >= deadline:
        raise TimeoutError("finite exact gauge owner deadline reached; preserve partial outputs")


def normalized(coefficients):
    assert len(coefficients) == 480 and all(type(c) is int for c in coefficients)
    divisor = gcd(*(abs(c) for c in coefficients))
    assert divisor > 0
    row = {"terms": [[a, c // divisor] for a, c in enumerate(coefficients) if c], "rhs": 0}
    assert sum(abs(c) for _, c in row["terms"]) < MAX_ACTIVITY
    return row, divisor


def actions(core, triples, targets, edges, generators):
    identity = tuple(range(21))
    group, frontier = {identity}, [identity]
    while frontier:
        old = frontier.pop()
        for generator in generators:
            image = tuple(generator[old[i]] for i in range(21))
            assert sorted(image) == list(range(21)) and set(image[:3]) == set(range(3))
            assert all((core[i] >> j & 1) == (core[image[i]] >> image[j] & 1)
                       for i in range(21) for j in range(21))
            if image not in group:
                group.add(image)
                frontier.append(image)
    assert len(group) == 12
    positions = {tuple(h): a for a, h in enumerate(triples)}
    edge_set = {tuple(edge) for edge in edges}
    result = []
    for image in sorted(group):
        move = [image[i + 3] - 3 for i in range(18)]
        action = [positions[tuple(sorted(move[i] for i in h))] for h in triples]
        assert sorted(action) == list(range(480))
        assert {tuple(sorted((action[a], action[b]))) for a, b in edges} == edge_set
        assert all(targets[action[a]][move[i]] == targets[a][i] for a in range(480) for i in range(18))
        result.append({"component_image": move, "signature_image": action})
    return result


def context(config_path, deadline):
    config = json.loads(config_path.read_bytes())
    assert config["schema"] == "conway99.f0.support-skew-gauge-configuration.v1"
    assert config["producer_sha256"] == digest(__file__)
    assert config["site_pairs"] == [list(pair) for pair in combinations(range(18), 2)]
    assert config["signs"] == [-1, 1] and config["limits"] == LIMITS
    for name, expected in SOURCES.values():
        assert digest(ROOT / name) == expected
    loaded, hashes = {}, {}
    for key, item in config["inputs"].items():
        raw = (ROOT / item["path"]).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == item["sha256"], key
        hashes[key] = item["sha256"]
        if key == "replayed_registry":
            assert item["sha256"] == config["inputs"]["registry"]["sha256"]
            continue
        loaded[key] = json.loads(gzip.decompress(raw) if item["path"].endswith(".gz") else raw)
    run, owner, cold, cold_owner = [loaded[k] for k in ("run", "run_owner", "cold", "cold_owner")]
    for receipt, report, key in [(owner, run, "run"), (cold_owner, cold, "cold")]:
        assert receipt["report_accepted"] and receipt["report_sha256"] == hashes[key]
        assert receipt["source_sha256"] == SOURCES["parent_controller"][1]
        assert receipt["status"] == report["status"] and receipt["deadline_overrun_seconds"] == 0
        assert receipt["supervision"]["child_reaped"] and receipt["supervision"]["returncode"] == 0
    assert run["status"] == "UNKNOWN_MASTER_NATIVE" and run["production_solve_calls"] == 2
    assert cold["status"] == "PASS_COMPLETE_CALLED_PREFIXES_AND_EXACT_CERTIFICATES"
    assert cold["run_result_sha256"] == hashes["run"] and cold["run_owner_sha256"] == hashes["run_owner"]
    assert cold["run_owner_accepted"] and not cold["run_outcome_relabelled"]
    assert cold["optimizer_calls"] == 0 and not cold["CpSolver_constructed"]
    assert not run["whole_component_excluded"] and not run["graph_constructed"]
    registry = loaded["registry"]
    assert len(registry) == run["final_registry_rows"] == cold["final_replayed_registry_rows"] == 12481
    assert value_sha(registry) == run["final_registry_sha256"] == cold["final_replayed_registry_sha256"] == config["parent_registry_value_sha256"]
    parent_rows = {}
    for index, entry in enumerate(registry):
        row = entry["row"]
        assert type(row["rhs"]) is int
        terms = row["terms"]
        assert terms and all(type(a) is int and 0 <= a < 480 and type(c) is int and c for a, c in terms)
        assert [a for a, _ in terms] == sorted(set(a for a, _ in terms))
        assert entry["key"] == value_sha(row)
        key = canonical(row)
        assert key not in parent_rows
        parent_rows[key] = {"parent_index": index, "parent_row_key": entry["key"]}
    selected, shared, old = [loaded[k] for k in ("selection", "shared", "universal_cuts")]
    assert selected == sorted(set(selected)) and len(selected) == 60 and all(type(a) is int for a in selected)
    record = loaded["iteration"]
    assert record["status"] == "EXACT_REFUTATION_AND_STRICT_CUT_GROWTH"
    assert record["index"] == 0 and record["new_rows"] == 12 and record["next_registry_rows"] == 12481
    assert record["shared_sha256"] == hashes["shared"] and record["universal_cuts_sha256"] == hashes["universal_cuts"]
    assert record["selection_sha256"] == hashes["selection"] == shared["candidate_sha256"]
    assert shared["selected_signature_ids"] == selected
    assert shared["exact_fixed_design_infeasibility"] and shared["cooperative_budget_overrun_seconds"] == 0
    assert not shared["exact_linear_feasibility"] and not shared["full_graph_constructed"]
    vectors = shared["fixed_capacity_potentials"]["integer_potentials60_by18"]
    assert len(vectors) == 60 and all(len(v) == 18 and all(type(x) is int for x in v) for v in vectors)
    allocation = source("allocation")
    domain = loaded["domain"]
    core, triples, targets, gram, edges = allocation.global_domain(domain)
    assert [[sum(i in triples[a] and j in triples[a] for a in selected) for j in range(18)]
            for i in range(18)] == gram
    transforms = actions(core, triples, targets, edges, domain["core_generators"])
    support = set(selected)
    potentials = [[0] * 18 for _ in range(480)]
    for a, vector in zip(selected, vectors):
        potentials[a] = list(vector)
    delta, coefficients, positive = allocation.allocate(triples, targets, edges, potentials, support)
    internal = [(a, b) for a, b in edges if a in support and b in support]
    weights = [sum(potentials[a][i] for i in triples[b]) + sum(potentials[b][i] for i in triples[a]) for a, b in internal]
    demand, capacity = sum(delta[a] for a in selected), sum(max(0, w) for w in weights)
    assert (demand, capacity, demand - capacity) == (176, 172, 4)
    row, divisor = normalized(coefficients)
    transports = []
    for index, transform in enumerate(transforms):
        image = transform["signature_image"]
        moved = sorted([[image[a], c] for a, c in row["terms"]])
        assert sum(c for a, c in moved if a in {image[b] for b in selected}) == 4 // divisor
        transports.append({"core_action_index": index, "signed_coefficients": moved,
                           "transported_selection_gap": 4 // divisor})
    baseline = {"source_sha256": SOURCES["legacy_lift"][1], "selected_signature_ids_for_allocation_only": selected,
        "nonzero_target_potentials": [[a, v] for a, v in enumerate(potentials) if any(v)],
        "complete_global_edges": len(edges), "global_edge_sha256": value_sha(edges),
        "positive_edge_count": len(positive), "positive_edge_type_counts": dict(Counter(e["kind"] for e in positive)),
        "positive_edge_allocation_sha256": value_sha(positive), "total_target_demand_at_saved_selection": demand,
        "internal_positive_capacity": capacity, "raw_gap": 4, "coefficient_gcd": divisor, "normalized_gap": 4 // divisor,
        "transported_cuts": transports, "saved_selection_is_not_a_cut_hypothesis": True, "optimizer_or_solver_called": False}
    assert baseline == old
    skew_demand = [[sum(int(q in triples[a]) * targets[a][p] for a in selected) for q in range(18)] for p in range(18)]
    assert all(skew_demand[p][q] == skew_demand[q][p] for p, q in combinations(range(18), 2))
    updates = {pair: [] for pair in combinations(range(18), 2)}
    boundary_count = 0
    for a, b in edges:
        if (a in support) == (b in support):
            continue
        inside, outside = (a, b) if a in support else (b, a)
        weight = sum(potentials[inside][i] for i in triples[outside])
        derivative = defaultdict(int)
        for p in triples[outside]:
            for q in triples[inside]:
                if p < q:
                    derivative[p, q] += 1
                elif q < p:
                    derivative[q, p] -= 1
        for pair, change in sorted(derivative.items()):
            if change:
                assert change in (-1, 1)
                updates[pair].append([inside, outside, weight, change])
        boundary_count += 1
    inventory = {"signatures": 480, "global_edges": len(edges), "internal_edges": len(internal),
                 "boundary_edges": boundary_count, "core_actions": len(transforms), "site_pairs": len(updates),
                 "signed_gauges": 306, "transported_rows_before_dedup": 3672,
                 "parent_registry_rows": len(registry), "parent_registry_value_sha256": value_sha(registry),
                 "skew_demand_matrix18_by18": skew_demand, "all153_skew_demand_identities_zero": True,
                 "boundary_derivative_entries": sum(map(len, updates.values())),
                 "boundary_derivative_inventory_sha256": value_sha([[list(pair), updates[pair]] for pair in updates]),
                 "baseline_universal_cuts_sha256": hashes["universal_cuts"],
                 "baseline_complete_certificate_reconstructed": True}
    assert len(internal) == shared["inventory"]["primary_edges"] == 1223
    check_time(deadline)
    return {"config": config, "config_sha256": digest(config_path), "hashes": hashes, "selected": selected, "support": support, "vectors": vectors,
            "potentials": potentials, "triples": triples, "targets": targets, "edges": edges, "actions": transforms,
            "coefficients": coefficients, "internal": internal, "weights": weights, "updates": updates,
            "parent_rows": parent_rows, "inventory": inventory}


def generate(ctx, directory, deadline):
    selected, triples, targets = ctx["selected"], ctx["triples"], ctx["targets"]
    rows, origins, seen, families, coverage = [], [], {}, [], []
    for p, q in combinations(range(18), 2):
        for sign in (-1, 1):
            check_time(deadline)
            index = len(families)
            potentials = [list(v) for v in ctx["potentials"]]
            for a in selected:
                potentials[a][p] += sign * int(q in triples[a])
                potentials[a][q] -= sign * int(p in triples[a])
            demand = sum(x * y for a in selected for x, y in zip(potentials[a], targets[a]))
            weights = [sum(potentials[a][i] for i in triples[b]) + sum(potentials[b][i] for i in triples[a])
                       for a, b in ctx["internal"]]
            assert demand == 176 and weights == ctx["weights"]
            coefficients = list(ctx["coefficients"])
            for a in selected:
                coefficients[a] += sign * (int(q in triples[a]) * targets[a][p] - int(p in triples[a]) * targets[a][q])
            for inside, outside, weight, derivative in ctx["updates"][p, q]:
                actual = sum(potentials[inside][i] for i in triples[outside])
                assert actual == weight + sign * derivative
                coefficients[outside] -= max(0, actual) - max(0, weight)
            assert sum(coefficients[a] for a in selected) == 4
            row, divisor = normalized(coefficients)
            families.append({"index": index, "sites": [p, q], "sign": sign,
                "local_potentials_sha256": value_sha([potentials[a] for a in selected]),
                "raw_coefficients": coefficients, "coefficient_gcd": divisor,
                "demand": demand, "capacity": 172, "raw_gap": 4,
                "internal_edge_weights_unchanged": True})
            for action_index, action in enumerate(ctx["actions"]):
                image = action["signature_image"]
                moved = {"terms": sorted([[image[a], c] for a, c in row["terms"]]), "rhs": 0}
                moved_support = {image[a] for a in selected}
                assert sum(c for a, c in moved["terms"] if a in moved_support) == 4 // divisor > 0
                key, row_key = canonical(moved), value_sha(moved)
                origin = {"gauge_index": index, "sites": [p, q], "sign": sign, "core_action_index": action_index}
                if key in ctx["parent_rows"]:
                    coverage.append(dict(origin, row_key=row_key, **ctx["parent_rows"][key]))
                else:
                    if key not in seen:
                        seen[key] = len(rows)
                        rows.append(moved["terms"])
                        origins.append({"row_key": row_key, "origins": []})
                    at = seen[key]
                    origins[at]["origins"].append(origin)
                    coverage.append(dict(origin, row_key=row_key, new_row_index=at))
            save(directory / "progress.json", {"completed_gauges": len(families), "total_gauges": 306,
                 "new_distinct_rows": len(rows), "optimizer_calls": 0})
    assert len(families) == 306 and len(coverage) == 3672
    assert len(rows) <= 3672 and 12481 + len(rows) <= 16153 < 16384
    catalogue = {"schema": "conway99.f0.complete-support-skew-gauge-census.v1", "inventory": ctx["inventory"],
                 "families": families, "transport_coverage": coverage, "all_parent_rows_must_remain": True}
    save(directory / "complete-census.json.gz", catalogue)
    export = {"status": "EXACT_SUPPORT_SKEW_GAUGE_ROWS_AWAITING_INDEPENDENT_COLD", "producer_sha256": digest(__file__),
              "configuration_sha256": ctx["config_sha256"], "input_hashes": ctx["hashes"],
              "complete_census_sha256": digest(directory / "complete-census.json.gz"),
              "rows_upper_zero": rows, "row_provenance": origins, "independent_cold_required": True,
              "all12481_parent_rows_must_remain": True, "no_rows_selected_by_old_candidate_violation": True}
    save(directory / "proposed-selector-cuts.json.gz", export)
    check_time(deadline)
    return {"complete_census_sha256": digest(directory / "complete-census.json.gz"),
            "proposed_selector_cuts_sha256": digest(directory / "proposed-selector-cuts.json.gz"),
            "complete_gauges": len(families), "complete_transports": len(coverage), "new_distinct_rows": len(rows),
            "possible_following_registry_rows": 12481 + len(rows),
            "maximum_absolute_coefficient": max((abs(c) for row in rows for _, c in row), default=0),
            "maximum_absolute_activity": max((sum(abs(c) for _, c in row) for row in rows), default=0),
            "independent_cold_required": True}


def worker(mode, configuration, directory, preparation, deadline):
    started = time.monotonic()
    try:
        ctx = context(configuration, deadline)
        report = {"source_sha256": digest(__file__), "configuration_sha256": digest(configuration),
                  "inventory": ctx["inventory"], "input_hashes": ctx["hashes"], "optimizer_calls": 0,
                  "native_solver_imported": False, "whole_component_excluded": False, "graph_constructed": False}
        if mode == "prepare":
            report["status"] = "PASS_EXACT_GAUGE_BINDINGS_BASELINE_AND_COMPLETE_INVARIANTS"
        else:
            owner = json.loads((preparation / "owner.json").read_bytes())
            prepared = json.loads((preparation / "report.json").read_bytes())
            assert owner["report_accepted"] and owner["report_sha256"] == digest(preparation / "report.json")
            assert owner["source_sha256"] == digest(__file__) and owner["deadline_overrun_seconds"] == 0
            assert owner["supervision"]["child_reaped"] and owner["supervision"]["returncode"] == 0
            assert prepared["status"] == "PASS_EXACT_GAUGE_BINDINGS_BASELINE_AND_COMPLETE_INVARIANTS"
            assert prepared["configuration_sha256"] == digest(configuration) and prepared["inventory"] == ctx["inventory"]
            report.update(generate(ctx, directory, deadline), preparation_sha256=digest(preparation / "report.json"))
            report["status"] = "PASS_COMPLETE_FINITE_GAUGE_CENSUS_AWAITING_INDEPENDENT_COLD"
        assert not any(name.split(".")[0] in {"ortools", "highspy", "scipy", "numpy"} for name in sys.modules)
        check_time(deadline)
        report.update(seconds=time.monotonic() - started, peak_rss_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        save(directory / "report.json", report)
    except Exception as error:
        save(directory / "error.json", {"type": type(error).__name__, "message": str(error)})
        raise


def owned(mode, configuration, directory, preparation):
    started = time.monotonic()
    limit = LIMITS[mode]
    directory.mkdir(parents=True, exist_ok=False)
    command = [sys.executable, str(Path(__file__).resolve()), "_" + mode, "--configuration", str(configuration.resolve()),
               "--directory", str(directory.resolve()), "--deadline", str(started + limit)]
    if preparation is not None:
        command += ["--preparation", str(preparation.resolve())]
    save(directory / "owner.json", {"status": "UNKNOWN_BEFORE_CHILD", "report_accepted": False})
    supervision = source("supervisor").supervise(command, directory, started + limit)
    owner = {"source_sha256": digest(__file__), "maximum_seconds": limit, "supervision": supervision,
             "status": supervision["status"], "report_accepted": False, "optimizer_calls": 0}
    if supervision["status"] == "CHILD_EXITED" and time.monotonic() <= started + limit:
        report = json.loads((directory / "report.json").read_bytes())
        owner.update(report_accepted=True, report_sha256=digest(directory / "report.json"), status=report["status"])
    owner.update(seconds=time.monotonic() - started, deadline_overrun_seconds=max(0, time.monotonic() - started - limit))
    if owner["deadline_overrun_seconds"]:
        owner.update(report_accepted=False, status="UNKNOWN_HARD_DEADLINE")
    save(directory / "owner.json", owner)
    print(json.dumps(owner, sort_keys=True), flush=True)


if __name__ == "__main__":
    if not __debug__:
        raise RuntimeError("exact gauge assertions required")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "run", "_prepare", "_run"))
    parser.add_argument("--configuration", type=Path, required=True)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--preparation", type=Path)
    parser.add_argument("--deadline", type=float)
    args = parser.parse_args()
    if args.mode.startswith("_"):
        assert args.deadline is not None
        worker(args.mode[1:], args.configuration, args.directory, args.preparation, args.deadline)
    else:
        assert args.mode == "prepare" or args.preparation is not None
        owned(args.mode, args.configuration, args.directory, args.preparation)
