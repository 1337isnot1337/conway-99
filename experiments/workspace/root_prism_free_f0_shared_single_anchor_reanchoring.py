"""Exact fresh shared-potential census and Boolean dominance reduction.

Only the sixteen cold-accepted certificates in the supplied configuration
are examined. No historical potential bank, optimizer or native model is
loaded. Full raw rows and dominance witnesses remain separate artifacts.
"""
import argparse
from collections import Counter
import gzip
import hashlib
import importlib.util
import json
from math import gcd
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[2]
SOURCES = {
    "fixed": ("experiments/workspace/root_prism_free_f0_row_box_design_linear.py", "c0d9e70f98e94176bf78bc518b41270940b930ab69cf34b26f42b71ff31a0871"),
    "shared": ("experiments/workspace/root_prism_free_f0_shared_deficit_separator.py", "6bc6944ed00713d384251ab54e54684e6f5ea29300f9ff243df5282f522375bf"),
    "allocation": ("experiments/workspace/root_prism_free_f0_symmetric_selector_cut.py", "15ec937609b7de44b808e9de7053bb9ee080ddf732a3defd2b23577c026fe274"),
    "dominance": ("experiments/workspace/root_prism_free_f0_local_row_dominance.py", "d91591788e7f97742736df8bb6cdafaddb46939668054fb7450e351a2d276566"),
}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def digest(path):
    return sha(Path(path).read_bytes())


def read(reference):
    raw = (ROOT / reference["path"]).read_bytes()
    assert sha(raw) == reference["sha256"], reference["path"]
    return json.loads(gzip.decompress(raw) if reference["path"].endswith(".gz") else raw)


def exact_integer(value):
    assert type(value) is int or (type(value) is str and str(int(value)) == value)
    return int(value)


def normalized(row):
    terms = [[j, exact_integer(c)] for j, c in row["terms"]]
    assert all(type(j) is int and 0 <= j < 480 for j, _ in terms)
    assert len(terms) == len({j for j, _ in terms})
    terms = sorted([j, c] for j, c in terms if c)
    divisor = gcd(*(abs(c) for _, c in terms))
    assert divisor > 0
    return {"terms": [[j, c // divisor] for j, c in terms], "rhs": exact_integer(row["rhs"]) // divisor}


def save(directory, name, value):
    path = directory / name
    raw = canonical(value) + b"\n"
    encoded = gzip.compress(raw, mtime=0) if name.endswith(".gz") else raw
    with path.open("xb") as stream:
        stream.write(encoded)
    return {"path": str(path.relative_to(ROOT)), "sha256": sha(encoded), "raw_sha256": sha(raw),
            "bytes": len(encoded), "raw_bytes": len(raw)}


def domain(record):
    core, triples = record["component_core_rows"], record["signature_domain"]
    assert len(core) == 21 and len(triples) == 480 and len(set(map(tuple, triples))) == 480
    assert all(h == sorted(set(h)) and len(h) == 3 for h in triples)
    adjacency = [(r >> 3) & ((1 << 18) - 1) for r in core[3:]]
    targets = [[2 - int(i in h) - sum(adjacency[i] >> j & 1 for j in h) for i in range(18)] for h in triples]
    assert targets == record["row_targets"] and all(sum(q) == 24 for q in targets)
    neighbors = record["possible_neighbor_signature_ids"]
    for a in range(480):
        assert neighbors[a] == [b for b in range(480) if b != a and len(set(triples[a]) & set(triples[b])) <= 1
                               and all(targets[a][i] > 0 for i in triples[b])
                               and all(targets[b][i] > 0 for i in triples[a])]
    assert sum(map(len, neighbors)) == 2 * 68394
    identity = tuple(range(21))
    group, pending = {identity}, [identity]
    while pending:
        old = pending.pop()
        for generator in record["core_generators"]:
            move = tuple(generator[old[i]] for i in range(21))
            if move not in group:
                group.add(move)
                pending.append(move)
    assert len(group) == 12
    positions = {tuple(h): a for a, h in enumerate(triples)}
    actions = []
    for full in sorted(group):
        assert sorted(full) == list(range(21)) and set(full[:3]) == set(range(3))
        assert all((core[i] >> j & 1) == (core[full[i]] >> full[j] & 1) for i in range(21) for j in range(21))
        move = [full[i + 3] - 3 for i in range(18)]
        image = [positions[tuple(sorted(move[i] for i in h))] for h in triples]
        assert all(targets[a][i] == targets[image[a]][move[i]] for a in range(480) for i in range(18))
        actions.append({"component_image": move, "signature_image": image})
    return triples, targets, neighbors, actions


def accepted_runs(config):
    results = {}
    assert [item["run_number"] for item in config["runs"]] == [1, 2]
    for item in config["runs"]:
        assert digest(ROOT / item["source"]["path"]) == item["source"]["sha256"]
        run, owner, cold, cold_owner = [read(item[key]) for key in ("result", "owner", "cold", "cold_owner")]
        for receipt, field, limit in ((owner, "result", 300), (cold_owner, "cold", 60)):
            assert receipt["source_sha256"] == item["source"]["sha256"] and receipt["maximum_seconds"] == limit
            assert receipt["report_accepted"] and receipt["deadline_overrun_seconds"] == 0
            assert receipt["supervision"]["child_reaped"] and receipt["supervision"]["returncode"] == 0
            assert receipt["report_sha256"] == item[field]["sha256"]
        assert cold["status"] == "PASS_COMPLETE_CALLED_PREFIXES_AND_EXACT_CERTIFICATES" and cold["run_owner_accepted"]
        assert cold["run_result_sha256"] == item["result"]["sha256"] and cold["run_owner_sha256"] == item["owner"]["sha256"]
        assert run["status"] == owner["status"] == cold["original_run_status"] == "ITERATION_LIMIT_WITH_UNQUERIED_GROWN_PREFIX"
        assert run["definition"] == cold["definition"] and len(cold["iterations"]) == 8
        assert all(x["direct_candidate_checked"] for x in cold["iterations"])
        results[item["run_number"]] = cold
    return results


def calculate(configuration, directory, deadline):
    started = time.monotonic()
    config = json.loads(configuration.read_bytes())
    assert config["schema"] == "conway99.f0.shared-single-anchor-reanchoring.inputs.v1"
    for path, expected in SOURCES.values():
        assert digest(ROOT / path) == expected
    spec = importlib.util.spec_from_file_location("exact_local_row_dominance", ROOT / SOURCES["dominance"][0])
    dominance = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(dominance)
    receipts = accepted_runs(config)
    triples, targets, neighbors, actions = domain(read(config["domain"]))
    prefix = read(config["prefix253"])
    extra = read(config["extra48"])
    assert extra["status"] == "PASS_INDEPENDENT_COMPLETE_REANCHORED_PACKING_ARITHMETIC"
    planned = [normalized(entry["row"]) for entry in prefix]
    assert len(planned) == 253
    planned += [normalized({"terms": row, "rhs": 0}) for row in extra["new_rows_upper_zero_vs_frozen157"]]
    planned_keys = {sha(canonical(row)) for row in planned}
    assert len(planned) == len(planned_keys) == 301
    literal = [normalized(row) for row in read(config["literal_rows"])]
    assert len(literal) == 4416
    literal_keys = {sha(canonical(row)) for row in literal}
    bank, classifications, candidates = {}, [], []
    assert [(x["run_number"], x["iteration"]) for x in config["candidates"]] == [(r, i) for r in (1, 2) for i in range(8)]
    for number, item in enumerate(config["candidates"]):
        assert time.monotonic() < deadline
        selected, record, shared, lifted = [read(item[key]) for key in ("selection", "record", "shared", "lift")]
        assert selected == sorted(set(selected)) and len(selected) == 60
        assert record["index"] == item["iteration"] and record["direct_checked"]
        assert record["selection_sha256"] == item["selection"]["sha256"]
        assert record["shared_sha256"] == item["shared"]["sha256"] and record["universal_cuts_sha256"] == item["lift"]["sha256"]
        assert shared["selected_signature_ids"] == selected and shared["candidate_sha256"] == item["selection"]["sha256"]
        assert shared["exact_fixed_design_infeasibility"] and shared["cooperative_budget_overrun_seconds"] == 0
        assert receipts[item["run_number"]]["iterations"][item["iteration"]]["direct_candidate_checked"]
        original = shared["original_feasibility"]
        assert original["source_sha256"] == SOURCES["shared"][1]
        assert original["exact_fixed_design_infeasibility"]
        ray = original["integer_ray"]
        assert all(type(x) is int for x in ray)
        potentials = [[-ray[19 * a] - 3 * ray[19 * a + 1 + i] for i in range(18)] for a in range(60)]
        assert potentials == shared["fixed_capacity_potentials"]["integer_potentials60_by18"]
        local_edges = [(a, b) for a in range(60) for b in range(a) if selected[b] in neighbors[selected[a]]]
        assert len(ray) == 1140 + len(local_edges)
        weights = [sum(potentials[a][i] for i in triples[selected[b]]) + sum(potentials[b][i] for i in triples[selected[a]])
                   for a, b in local_edges]
        assert all(w <= 3 * u for w, u in zip(weights, ray[1140:]))
        assert all(u >= 0 for u in ray[1140:])
        demand = sum(sum(v * q for v, q in zip(p, targets[a])) for a, p in zip(selected, potentials))
        capacity = sum(max(w, 0) for w in weights)
        fixed = shared["fixed_capacity_potentials"]
        assert demand == fixed["total_weighted_demand"] and capacity == fixed["complete_internal_positive_edge_capacity"]
        assert demand - capacity == fixed["strict_gap"] > 0
        nz = [[a, v] for a, v in zip(selected, potentials) if any(v)]
        assert nz == lifted["nonzero_target_potentials"]
        candidates.append({"candidate_index": number, "run_number": item["run_number"], "iteration": item["iteration"],
                           "selection": selected, "selection_sha256": item["selection"]["sha256"]})
        classification = {"candidate_index": number, "nonzero_anchors": len(nz), "shared_sha256": item["shared"]["sha256"]}
        if len(nz) == 1:
            anchor, vector = nz[0]
            local = selected.index(anchor)
            delta = -ray[19 * local]
            v = [-ray[19 * local + 1 + i] for i in range(18)]
            assert vector == [3 * x + delta for x in v]
            assert sum(vector[i] * targets[anchor][i] for i in range(18)) == 3 * (sum(v[i] * targets[anchor][i] for i in range(18)) + 8 * delta)
            divisor = gcd(*(abs(x) for x in vector))
            primitive = [x // divisor for x in vector]
            classification.update(anchor=anchor, original_degree_potential=delta, original_site_potential=v,
                                  already_converted_site_potential=vector, primitive_divisor=divisor)
            for action_index, action in enumerate(actions):
                moved = [0] * 18
                for i, value in enumerate(primitive):
                    moved[action["component_image"][i]] = value
                origin = {"candidate_index": number, "anchor": anchor, "action_index": action_index,
                          "transported_anchor": action["signature_image"][anchor]}
                bank.setdefault(tuple(moved), []).append(origin)
        classifications.append(classification)
    vectors = [{"vector": list(v), "origins": bank[v]} for v in sorted(bank)]
    bank_ref = save(directory, "bank.json", {"sources": SOURCES, "configuration_sha256": digest(configuration),
                    "classifications": classifications, "bank": vectors, "candidates": candidates,
                    "degree_conversion_already_applied_in_saved_vectors": True})
    attempts, rows = [], {}
    for potential_id, item in enumerate(vectors):
        assert time.monotonic() < deadline
        vector = item["vector"]
        weights = [max(sum(vector[i] for i in h), 0) for h in triples]
        for anchor in range(480):
            demand = sum(x * y for x, y in zip(vector, targets[anchor]))
            if demand <= 0:
                attempts.append([potential_id, anchor, demand, None])
                continue
            terms = sorted([[anchor, demand]] + [[b, -weights[b]] for b in neighbors[anchor] if weights[b] > 0])
            row = normalized({"terms": terms, "rhs": 0})
            key = sha(canonical(row))
            saved = rows.setdefault(key, {"key": key, "row": row, "origins": [],
                                          "in_planned301": key in planned_keys, "in_literal4416": key in literal_keys})
            saved["origins"].append({"potential_id": potential_id, "anchor": anchor, "demand": demand})
            attempts.append([potential_id, anchor, demand, key])
    ordered = [rows[key] for key in sorted(rows)]
    selected_sets = [set(c["selection"]) for c in candidates]
    for entry in ordered:
        assert time.monotonic() < deadline
        anchor = next(j for j, c in entry["row"]["terms"] if c > 0)
        entry["candidate_violations"] = [[i, gap] for i, selected in enumerate(selected_sets) if anchor in selected
            for gap in [sum(c for j, c in entry["row"]["terms"] if j in selected)] if gap > 0]
    raw_ref = save(directory, "complete-census.json.gz", {"bank": bank_ref, "domain": config["domain"],
                    "attempts": attempts, "rows": ordered, "whole_component_excluded": False})
    fresh = [entry for entry in ordered if not entry["in_planned301"]]
    authoritative = [{"row": row, "origin": {"family": "literal4416", "index": i}} for i, row in enumerate(literal)]
    authoritative += [{"row": row, "origin": {"family": "planned301", "index": i}} for i, row in enumerate(planned)]
    reduced = dominance.reduce_rows([{"row": e["row"], "origin": {"raw_row_key": e["key"]}} for e in fresh], authoritative)
    assert time.monotonic() < deadline
    reduction_ref = save(directory, "dominance.json.gz", reduced)
    retained = reduced["retained"]
    for item in retained:
        item["candidate_violations"] = [[i, gap] for i, selected in enumerate(selected_sets) if item["anchor"] in selected
            for gap in [sum(c for j, c in item["row"]["terms"] if j in selected)] if gap > 0]
    export_ref = save(directory, "retained-rows.json", {"status": "EXACT_REANCHORED_ROWS_PENDING_INDEPENDENT_COLD",
                    "source_sha256": digest(__file__), "configuration_sha256": digest(configuration),
                    "complete_census": raw_ref, "dominance": reduction_ref, "retained": retained,
                    "rows_upper_zero": [item["row"]["terms"] for item in retained],
                    "all_planned301_and_original4416_preserved": True})
    def stats(entries):
        coefficients = [abs(c) for e in entries for _, c in e["row"]["terms"]]
        return {"rows": len(entries), "terms_min_max": [min((len(e["row"]["terms"]) for e in entries), default=0),
                    max((len(e["row"]["terms"]) for e in entries), default=0)],
                "maximum_absolute_coefficient": max(coefficients, default=0),
                "maximum_coefficient_bits": max((x.bit_length() for x in coefficients), default=0),
                "maximum_absolute_activity": max((sum(abs(c) for _, c in e["row"]["terms"]) for e in entries), default=0),
                "rows_cutting_any_accepted_candidate": sum(bool(e["candidate_violations"]) for e in entries)}
    report = {"status": "COMPLETE_EXACT_SHARED_SINGLE_ANCHOR_CENSUS_PENDING_COLD",
              "source_sha256": digest(__file__), "configuration_sha256": digest(configuration), "sources": SOURCES,
              "bank": bank_ref, "complete_census": raw_ref, "dominance": reduction_ref, "retained_rows": export_ref,
              "single_anchor_certificates": sum(c["nonzero_anchors"] == 1 for c in classifications),
              "primitive_transported_potentials": len(vectors), "anchor_potential_pairs": len(attempts),
              "positive_demand_pairs": sum(x[2] > 0 for x in attempts),
              "all_rows": stats(ordered), "new_vs_planned301": stats(fresh), "retained_frontier": stats(retained),
              "dominance_counts": reduced["counts"], "optimizer_calls": 0, "native_imports": 0,
              "historical_potential_bank_read": False, "whole_component_excluded": False,
              "seconds": time.monotonic() - started}
    assert time.monotonic() < deadline
    save(directory, "report.json", report)
    return report


if __name__ == "__main__":
    assert __debug__
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--configuration", type=Path, required=True)
    parser.add_argument("--directory", type=Path, required=True)
    args = parser.parse_args()
    directory = args.directory.resolve()
    directory.mkdir(parents=True, exist_ok=False)
    result = calculate(args.configuration, directory, time.monotonic() + 60)
    print(json.dumps({k: result[k] for k in ("status", "single_anchor_certificates", "primitive_transported_potentials",
          "positive_demand_pairs", "new_vs_planned301", "retained_frontier", "seconds")}, sort_keys=True))
