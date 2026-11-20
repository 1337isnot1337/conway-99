"""Independent integer reconstruction of the fresh shared-row census.

This verifier imports no producer, reducer, optimizer or native model.
It checks every potential/anchor attempt, raw row, and final direct coverage
witness. Authoritative rows remain a premise that the next master retains.
"""
import argparse
from collections import defaultdict
import gzip
import hashlib
import json
from math import gcd
from pathlib import Path
import resource
import time

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ("experiments/logs/root-prism-free/f0-shared-single-anchor-reanchoring-configuration01.json",
          "42b6a6651435adbfb81d33819917f870df2d69f7205878d01899ea9a2ef8ba53")
BANK = ("experiments/logs/root-prism-free/f0-shared-single-anchor-reanchoring01/bank.json",
        "ba861832d39d865e62b648ba6e342f8f960075f96d3f48861952794c128e9fa0")
CENSUS = ("experiments/logs/root-prism-free/f0-shared-single-anchor-reanchoring01/complete-census.json.gz",
          "8741c7ff5cdeba72e330b0ec4ecf51f10e55f9f2491904d3e2eba1f7ce70974c")
PRODUCER = ("experiments/workspace/root_prism_free_f0_shared_single_anchor_reanchoring.py",
            "878e7058cd6aab4761adf56e2ca90e0cbc199d463a1824d26da0171632793676")
REDUCER = ("experiments/workspace/root_prism_free_f0_shared_single_anchor_reduction.py",
           "b25311bbc83bd81015b25f0063596ee7d2259f99732ec0498489ffd48464c441")


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def key(value):
    return sha(canonical(value))


def read(reference):
    if isinstance(reference, tuple):
        reference = {"path": reference[0], "sha256": reference[1]}
    content = (ROOT / reference["path"]).read_bytes()
    assert sha(content) == reference["sha256"]
    raw = gzip.decompress(content) if reference["path"].endswith(".gz") else content
    if "raw_sha256" in reference:
        assert sha(raw) == reference["raw_sha256"]
        assert len(raw) == reference["raw_bytes"] and len(content) == reference["bytes"]
    return json.loads(raw)


def integer(value):
    assert type(value) is int or (type(value) is str and str(int(value)) == value)
    return int(value)


def normalize(row):
    terms = sorted([j, integer(c)] for j, c in row["terms"] if integer(c))
    assert all(type(j) is int and 0 <= j < 480 for j, _ in terms)
    assert len(terms) == len({j for j, _ in terms}) and terms
    divisor = gcd(*(abs(c) for _, c in terms))
    return {"terms": [[j, c // divisor] for j, c in terms], "rhs": integer(row["rhs"]) // divisor}


def cap(row):
    row = normalize(row)
    positive = [(j, c) for j, c in row["terms"] if c > 0]
    if row["rhs"] != 0 or len(positive) != 1:
        return None
    anchor, demand = positive[0]
    result = normalize({"terms": [[anchor, demand]] + [[j, -min(-c, demand)] for j, c in row["terms"] if c < 0], "rhs": 0})
    anchor, demand = next((j, c) for j, c in result["terms"] if c > 0)
    return {"row": result, "anchor": anchor, "demand": demand,
            "weights": [[j, -c] for j, c in result["terms"] if c < 0], "key": key(result)}


def implies(first, second):
    if first["anchor"] != second["anchor"]:
        return False
    a, b = dict(first["weights"]), dict(second["weights"])
    return all(a.get(j, 0) * second["demand"] <= b.get(j, 0) * first["demand"] for j in a.keys() | b.keys())


def replay(directory, deadline):
    def check_time():
        assert time.monotonic() < deadline, "independent exact replay deadline"
    config, bank, census = read(CONFIG), read(BANK), read(CENSUS)
    for path, expected in (PRODUCER, REDUCER):
        assert sha((ROOT / path).read_bytes()) == expected
    assert bank["configuration_sha256"] == CONFIG[1]
    assert census["bank"]["sha256"] == BANK[1] and census["domain"] == config["domain"]
    cold_by_run = {}
    for item in config["runs"]:
        run, owner, cold, cold_owner = [read(item[name]) for name in ("result", "owner", "cold", "cold_owner")]
        assert sha((ROOT / item["source"]["path"]).read_bytes()) == item["source"]["sha256"]
        for receipt, report_name, limit in ((owner, "result", 300), (cold_owner, "cold", 60)):
            assert receipt["source_sha256"] == item["source"]["sha256"] and receipt["maximum_seconds"] == limit
            assert receipt["report_accepted"] and receipt["deadline_overrun_seconds"] == 0
            assert receipt["report_sha256"] == item[report_name]["sha256"]
            assert receipt["supervision"]["returncode"] == 0 and receipt["supervision"]["child_reaped"]
        assert cold["status"] == "PASS_COMPLETE_CALLED_PREFIXES_AND_EXACT_CERTIFICATES" and cold["run_owner_accepted"]
        assert cold["run_result_sha256"] == item["result"]["sha256"] and cold["run_owner_sha256"] == item["owner"]["sha256"]
        assert run["definition"] == cold["definition"] and len(cold["iterations"]) == 8
        assert run["status"] == cold["original_run_status"] == "ITERATION_LIMIT_WITH_UNQUERIED_GROWN_PREFIX"
        cold_by_run[item["run_number"]] = cold
    prefix = read(config["prefix253"])
    assert len(prefix) == 253 and key(prefix) == cold_by_run[2]["final_replayed_registry_sha256"]
    extra = read(config["extra48"])
    planned = [normalize(e["row"]) for e in prefix] + [normalize({"terms": r, "rhs": 0}) for r in extra["new_rows_upper_zero_vs_frozen157"]]
    literal = [normalize(r) for r in read(config["literal_rows"])]
    planned_keys, literal_keys = {key(r) for r in planned}, {key(r) for r in literal}
    assert len(planned) == len(planned_keys) == 301 and len(literal) == 4416

    d = read(config["domain"])
    core, triples = d["component_core_rows"], d["signature_domain"]
    masks = [sum(1 << i for i in h) for h in triples]
    adj = [(r >> 3) & ((1 << 18) - 1) for r in core[3:]]
    targets = [[2 - (m >> i & 1) - (m & adj[i]).bit_count() for i in range(18)] for m in masks]
    assert targets == d["row_targets"] and all(sum(q) == 24 for q in targets)
    neighbors = [[b for b in range(480) if b != a and (masks[a] & masks[b]).bit_count() <= 1
                  and all(targets[a][i] > 0 for i in triples[b]) and all(targets[b][i] > 0 for i in triples[a])] for a in range(480)]
    assert neighbors == d["possible_neighbor_signature_ids"] and sum(map(len, neighbors)) == 136788
    group, queue = {tuple(range(21))}, [tuple(range(21))]
    for old in queue:
        for gen in d["core_generators"]:
            moved = tuple(gen[old[i]] for i in range(21))
            if moved not in group:
                group.add(moved)
                queue.append(moved)
    assert len(group) == 12
    positions = {tuple(h): a for a, h in enumerate(triples)}
    actions = []
    for move in sorted(group):
        assert sorted(move) == list(range(21)) and set(move[:3]) == {0, 1, 2}
        assert all((core[i] >> j & 1) == (core[move[i]] >> move[j] & 1) for i in range(21) for j in range(21))
        sigma = [move[i + 3] - 3 for i in range(18)]
        image = [positions[tuple(sorted(sigma[i] for i in h))] for h in triples]
        assert all(targets[image[a]][sigma[i]] == targets[a][i] for a in range(480) for i in range(18))
        actions.append((sigma, image))
    vectors, classifications, candidates = defaultdict(list), [], []
    assert [(x["run_number"], x["iteration"]) for x in config["candidates"]] == [(r, i) for r in (1, 2) for i in range(8)]
    for number, item in enumerate(config["candidates"]):
        check_time()
        selection, record, shared, lift = [read(item[k]) for k in ("selection", "record", "shared", "lift")]
        assert len(selection) == 60 and selection == sorted(set(selection))
        assert record["selection_sha256"] == item["selection"]["sha256"] and record["direct_checked"]
        assert record["shared_sha256"] == item["shared"]["sha256"] and record["universal_cuts_sha256"] == item["lift"]["sha256"]
        assert cold_by_run[item["run_number"]]["iterations"][item["iteration"]]["direct_candidate_checked"]
        ray = shared["original_feasibility"]["integer_ray"]
        assert all(type(x) is int for x in ray)
        v = [[-3 * ray[19 * a + i + 1] - ray[19 * a] for i in range(18)] for a in range(60)]
        assert v == shared["fixed_capacity_potentials"]["integer_potentials60_by18"]
        edges = [(a, b) for a in range(60) for b in range(a) if selection[b] in neighbors[selection[a]]]
        assert len(ray) == 1140 + len(edges)
        weights = [sum(v[a][i] for i in triples[selection[b]]) + sum(v[b][i] for i in triples[selection[a]]) for a, b in edges]
        assert all(u >= 0 and w <= 3 * u for w, u in zip(weights, ray[1140:]))
        demand = sum(sum(x * y for x, y in zip(p, targets[a])) for a, p in zip(selection, v))
        fixed = shared["fixed_capacity_potentials"]
        assert demand == fixed["total_weighted_demand"]
        assert sum(max(w, 0) for w in weights) == fixed["complete_internal_positive_edge_capacity"]
        assert demand - sum(max(w, 0) for w in weights) == fixed["strict_gap"] > 0
        nz = [[a, p] for a, p in zip(selection, v) if any(p)]
        assert nz == lift["nonzero_target_potentials"]
        classification = {"candidate_index": number, "nonzero_anchors": len(nz), "shared_sha256": item["shared"]["sha256"]}
        candidates.append({"candidate_index": number, "run_number": item["run_number"], "iteration": item["iteration"],
                           "selection": selection, "selection_sha256": item["selection"]["sha256"]})
        if len(nz) == 1:
            anchor, potential = nz[0]
            index = selection.index(anchor)
            degree = -ray[19 * index]
            site = [-ray[19 * index + i + 1] for i in range(18)]
            assert potential == [degree + 3 * x for x in site]
            divisor = gcd(*(abs(x) for x in potential))
            primitive = [x // divisor for x in potential]
            classification.update(anchor=anchor, original_degree_potential=degree, original_site_potential=site,
                                  already_converted_site_potential=potential, primitive_divisor=divisor)
            for action_index, (sigma, image) in enumerate(actions):
                inverse = [sigma.index(i) for i in range(18)]
                moved = tuple(primitive[inverse[i]] for i in range(18))
                vectors[moved].append({"candidate_index": number, "anchor": anchor, "action_index": action_index,
                                       "transported_anchor": image[anchor]})
        classifications.append(classification)
    expected_bank = [{"vector": list(v), "origins": vectors[v]} for v in sorted(vectors)]
    assert expected_bank == bank["bank"] and classifications == bank["classifications"] and candidates == bank["candidates"]
    assert len(expected_bank) == 114 and sum(x["nonzero_anchors"] == 1 for x in classifications) == 10
    rows = {e["key"]: e for e in census["rows"]}
    assert len(rows) == 12204 and list(rows) == sorted(rows)
    origins, attempts, seen = defaultdict(list), census["attempts"], set()
    assert len(attempts) == 114 * 480
    for pi, item in enumerate(expected_bank):
        check_time()
        v = item["vector"]
        weights = [max(sum(v[i] for i in h), 0) for h in triples]
        for a in range(480):
            demand = sum(x * y for x, y in zip(v, targets[a]))
            entry = attempts[480 * pi + a]
            assert entry[:3] == [pi, a, demand]
            if demand <= 0:
                assert entry[3] is None
                continue
            row = normalize({"terms": [[a, demand]] + [[b, -weights[b]] for b in neighbors[a] if weights[b]], "rhs": 0})
            k = key(row)
            assert entry[3] == k and rows[k]["row"] == row
            origins[k].append({"potential_id": pi, "anchor": a, "demand": demand})
            seen.add(k)
    assert seen == set(rows)
    selected = [set(c["selection"]) for c in candidates]
    for k, entry in rows.items():
        check_time()
        assert entry["origins"] == origins[k] and entry["in_planned301"] == (k in planned_keys)
        assert entry["in_literal4416"] == (k in literal_keys)
        violations = [[i, gap] for i, support in enumerate(selected)
                      for gap in [sum(c for j, c in entry["row"]["terms"] if j in support)] if gap > 0]
        assert violations == entry["candidate_violations"]

    report_raw = (directory / "report.json").read_bytes()
    report = json.loads(report_raw)
    assert report["source_sha256"] == REDUCER[1] and report["complete_census"]["sha256"] == CENSUS[1]
    reduced, exported = read(report["dominance"]), read(report["retained_rows"])
    authority = [(r, {"family": "literal4416", "index": i}) for i, r in enumerate(literal)]
    authority += [(r, {"family": "planned301", "index": i}) for i, r in enumerate(planned)]
    old, usable = {}, 0
    for row, origin in authority:
        item = cap(row)
        if item is not None:
            usable += 1
            item["origin"] = origin
            old.setdefault(item["key"], item)
    fresh = [e for e in census["rows"] if not e["in_planned301"]]
    capped, cap_origins = {}, defaultdict(list)
    for e in fresh:
        value = cap(e["row"])
        assert value is not None
        capped[value["key"]] = value
        cap_origins[value["key"]].append({"raw_row_key": e["key"]})
    retained = {e["key"]: e for e in reduced["retained"]}
    assert len(retained) == len(reduced["retained"]) and list(retained) == sorted(retained)
    for k, item in retained.items():
        assert item == dict(capped[k], origins=cap_origins[k])
    assert len(reduced["coverage"]) == len(fresh)
    used_old, old_dominated = set(), set()
    for raw, witness in zip(fresh, reduced["coverage"]):
        check_time()
        value = cap(raw["row"])
        assert witness["raw_row_key"] == raw["key"] and witness["capped_row_key"] == value["key"]
        kind, dk = witness["dominator_kind"], witness["dominator_key"]
        assert kind in ("authoritative", "retained")
        target = old[dk] if kind == "authoritative" else retained[dk]
        assert implies(target, value)
        if kind == "authoritative":
            used_old.add(dk)
            old_dominated.add(value["key"])
    assert reduced["used_authoritative_rows"] == [old[k] for k in sorted(used_old)]
    expected_counts = {"raw_candidates": len(fresh), "distinct_capped_candidates": len(capped),
                       "authoritative_rows_checked": len(authority), "usable_authoritative_rows": usable,
                       "distinct_capped_authoritative_rows": len(old), "capped_candidates_dominated_by_authoritative": len(old_dominated),
                       "retained_capped_candidates": len(retained)}
    assert expected_counts == reduced["counts"] == report["dominance_counts"]
    expected_export = []
    for item in reduced["retained"]:
        violations = [[i, gap] for i, support in enumerate(selected)
                      for gap in [sum(c for j, c in item["row"]["terms"] if j in support)] if gap > 0]
        expected_export.append(dict(item, candidate_violations=violations))
    assert exported["retained"] == expected_export
    assert exported["rows_upper_zero"] == [item["row"]["terms"] for item in expected_export]
    assert reduced["all_authoritative_rows_preserved"] and exported["all_planned301_and_original4416_preserved"]
    assert report["rows_removed_from_planned301"] == report["rows_removed_from_literal4416"] == 0
    assert report["optimizer_calls"] == report["native_imports"] == 0 and not report["first_attempt_terminal_accepted"]
    check_time()
    return {"status": "PASS_INDEPENDENT_COMPLETE_SHARED_CENSUS_AND_DIRECT_COVERAGE",
            "source_sha256": sha(Path(__file__).read_bytes()), "producer_sha256": PRODUCER[1], "reducer_sha256": REDUCER[1],
            "configuration_sha256": CONFIG[1], "bank_sha256": BANK[1], "complete_census_sha256": CENSUS[1],
            "reduction_report_sha256": sha(report_raw), "dominance_sha256": report["dominance"]["sha256"],
            "retained_export_sha256": report["retained_rows"]["sha256"], "prefix253_value_sha256": key(prefix),
            "all480_domains_reconstructed": True, "exact_degree_conversion_checked_on16_rays": True,
            "single_anchor_certificates": 10, "primitive_transported_potentials": 114,
            "complete_attempts_checked": len(attempts), "complete_raw_rows_checked": len(rows),
            "direct_coverage_witnesses_checked": len(fresh), "dominance_counts": expected_counts,
            "rows_upper_zero": exported["rows_upper_zero"], "all_original4416_and_planned301_must_remain": True,
            "minimal_under_all_boolean_implications_claimed": False, "optimizer_calls": 0, "native_imports": 0,
            "producer_reducer_or_dominance_imported": False, "whole_component_excluded": False}


if __name__ == "__main__":
    assert __debug__
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reduction-directory", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    started = time.monotonic()
    result = replay(args.reduction_directory, started + 120)
    result.update(seconds=time.monotonic() - started, peak_rss_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    assert result["seconds"] < 120
    with args.output.open("xb") as stream:
        stream.write(canonical(result) + b"\n")
    print(json.dumps({k: result[k] for k in ("status", "complete_raw_rows_checked", "direct_coverage_witnesses_checked", "dominance_counts", "seconds", "peak_rss_KiB")}, sort_keys=True))
