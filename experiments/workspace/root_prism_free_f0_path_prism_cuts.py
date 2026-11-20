"""Complete visible-prism cuts from three exterior vertices and a two-edge path.

This prepares Y_ab+Y_bc<=x_b, never an edge-product variable. It retains
all literal prism witnesses and pruning dispositions, and uses only the
frozen actual-core actions for the variable quotient. No point or solver.
"""
import argparse
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import time

import root_prism_free_f0_path_prism_inventory as inventory

ROOT = Path(__file__).resolve().parents[2]
BASE = "experiments/logs/root-prism-free/"
INVENTORY_SOURCE_SHA = "0d722525b142d6c4c23476540e368950e265c7efe99a654d24bb7fbb1b441960"
INPUTS = {
    **inventory.INPUTS,
    "inventory": (BASE+"f0-path-prism-inventory01.json.gz",
                  "52a618d43128001625b337578bcd3ae4beb4fc0e2552031ab9013a77a32711db"),
    "moments": (BASE+"f0-second-moments-preparation02.json.gz",
                "404d91da35c798ba248887c22a7500957947e24b71d5197dc44432460e6d219e"),
    "actions": (BASE+"f0-graph-schur-kernels01.json.gz",
                "65f1ad0d0015a6eff3d97c676fb0e188f57f9dee00e9245758a28bab2069b40d"),
    "reduction": (BASE+"f0-second-moments-reduced-model.json.gz",
                  "73a50b431ac69ad57e10cff9aabe5c0b7d69ee075e95710b461f62b33fe2bbcf"),
}
WITNESS_FIELDS = ["a", "b", "c", "x", "y", "z", "edge_ab_id", "edge_bc_id",
                  "disposition", "path_id", "row_id", "quota_one_site",
                  "known_zero_edge_id"]
PATH_FIELDS = ["center_b", "endpoint_min", "endpoint_max", "first_witness",
               "witness_count", "disposition", "row_id", "quota_one_site",
               "known_zero_edge_id"]
DISPOSITIONS = {
    "0": "known_Y_zero_then_edge_activation",
    "1": "single_mixed_quota_one_then_edge_nonnegativity",
    "2": "retained_quotient_inequality",
}
PRISM_ROWS = [38, 13, 19, 50, 44, 25]


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def check_time(deadline, stage):
    if time.monotonic() >= deadline:
        raise TimeoutError("bounded two-edge prism preparation: "+stage)


def literal_prism(core, triples, a, b, c, x, y, z):
    assert len({a, b, c}) == len({x, y, z}) == 3
    rows = core[:]+[0, 0, 0]
    for vertex, signature in ((21, triples[a]), (22, triples[b]), (23, triples[c])):
        for j in signature:
            rows[vertex] |= 1 << (j+3)
            rows[j+3] |= 1 << vertex
    for i, j in ((21, 22), (22, 23)):
        rows[i] |= 1 << j
        rows[j] |= 1 << i
    sites = [21, 22, x+3, 23, y+3, z+3]
    assert inventory.induced(rows, sites) == PRISM_ROWS
    # Adding the omitted endpoint edge would give it at least two CN.
    assert rows[21] & rows[23] & (1 << 22)
    assert rows[21] & rows[23] & (1 << (z+3))
    assert (rows[21] & rows[23]).bit_count() >= 2
    return sites


def load_inputs():
    assert sha(Path(inventory.__file__).read_bytes()) == INVENTORY_SOURCE_SHA
    loaded = {}
    for name, (path, digest) in INPUTS.items():
        raw = (ROOT/path).read_bytes()
        assert sha(raw) == digest
        loaded[name] = json.loads(gzip.decompress(raw))
    data, masks, adjacency, ymap, zeros, neighbors, live = inventory.load_domain()
    assert data == loaded["domain"]["validation"]
    return loaded, data, masks, adjacency, ymap, zeros, neighbors, live


def validate_actions(data, actions, core_actions, ymap):
    core, triples, edges = data["core"], data["triples"], data["edges"]
    assert len(actions) == len(core_actions) == 12
    assert len(set(map(tuple, actions))) == len(set(map(tuple, core_actions))) == 12
    core_index = {tuple(p): i for i, p in enumerate(core_actions)}
    assert tuple(range(21)) in core_index
    identity = core_index[tuple(range(21))]
    assert actions[identity] == list(range(480))
    edge_index = {tuple(e): i for i, e in enumerate(edges)}
    xmap = {}
    for orbit, group in enumerate(data["selector_orbits"]):
        for a in group:
            assert a not in xmap
            xmap[a] = orbit
    assert set(xmap) == set(range(480))
    for g, move in zip(actions, core_actions):
        assert sorted(g) == list(range(480)) and sorted(move) == list(range(21))
        assert set(move[:3]) == set(range(3)) and set(move[3:]) == set(range(3, 21))
        assert all(((core[i] >> j) & 1) == ((core[move[i]] >> move[j]) & 1)
                   for i in range(21) for j in range(21))
        assert all(sorted(move[j+3]-3 for j in h) == triples[g[a]]
                   for a, h in enumerate(triples))
    compositions = []
    for i, left in enumerate(core_actions):
        for j, right in enumerate(core_actions):
            k = core_index[tuple(left[right[v]] for v in range(21))]
            assert all(actions[k][a] == actions[i][actions[j][a]] for a in range(480))
            compositions.append([i, j, k])
    for orbit, group in enumerate(data["selector_orbits"]):
        assert sorted({g[group[0]] for g in actions}) == group
        assert all(xmap[a] == orbit for a in group)
    for orbit, group in enumerate(data["edge_orbits"]):
        a, b = edges[group[0]]
        assert sorted({edge_index[tuple(sorted((g[a], g[b])))] for g in actions}) == group
        assert all(ymap[ei] == 42+orbit for ei in group)
    return xmap, edge_index, {"identity_action": identity,
                            "all_144_compositions": compositions,
                            "core_actions": core_actions,
                            "selector_actions": actions,
                            "selector_orbits_checked": 42,
                            "edge_orbits_checked": 5805,
                            "host_graph_automorphism_assumed": False}


def build(deadline, census):
    loaded, data, masks, adjacency, ymap, zeros, neighbors, live = load_inputs()
    core, triples, edges, targets = (data[k] for k in ("core", "triples", "edges", "targets"))
    actions = loaded["moments"]["selector_actions"]
    core_actions = loaded["actions"]["domain"]["reconstructed21_core_actions"]
    xmap, edge_index, action_report = validate_actions(data, actions, core_actions, ymap)
    kept = loaded["reduction"]["kept_original_variables"]
    reverse = {j: i for i, j in enumerate(kept)}
    assert len(kept) == len(reverse) == 15200
    assert all(j in reverse for j in range(5847))
    quota_one = [sum(1 << j for j, value in enumerate(row) if value == 1) for row in targets]
    ledger = loaded["inventory"]
    assert ledger["source_sha256"] == INVENTORY_SOURCE_SHA
    assert ledger["production_literal_paths_enumerated"] == 0
    paths = [(x, y, z) for y in range(18) for x in range(18) for z in range(18)
             if x != z and adjacency[y][x] and adjacency[y][z] and not adjacency[x][z]]
    assert [list(p) for p in paths] == ledger["oriented_component_paths"]
    expected_branches = {(tuple(p["core_path_x_y_z"]), p["center_b"]): p
                         for p in ledger["pattern_buckets"]}
    assert len(expected_branches) == 1584
    seen_branches = set()
    witnesses, paths_records, rows = [], [], []
    witness_index, path_ids, row_ids = {}, {}, {}
    for x, y, z in paths:
        check_time(deadline, "literal configurations")
        sites = (1 << x) | (1 << y) | (1 << z)
        ap = (1 << x) | (1 << z)
        cp = (1 << y) | (1 << z)
        abucket = sum(1 << a for a, h in enumerate(masks) if h & sites == ap)
        cbucket = sum(1 << c for c, h in enumerate(masks) if h & sites == cp)
        for b, hb in enumerate(masks):
            if hb & sites != 1 << x:
                continue
            aa, cc = abucket & neighbors[b], cbucket & neighbors[b]
            if not aa or not cc:
                continue
            key = ((x, y, z), b)
            expected = expected_branches[key]
            assert expected["raw_a_count"] == aa.bit_count()
            assert expected["raw_c_count"] == cc.bit_count()
            assert expected["live_a_count"] == (aa & live[b]).bit_count()
            assert expected["live_c_count"] == (cc & live[b]).bit_count()
            assert key not in seen_branches
            seen_branches.add(key)
            branch = Counter()
            for a in inventory.members(aa):
                for c in inventory.members(cc):
                    witness_key = (a, b, c, x, y, z)
                    assert witness_key not in witness_index
                    literal_prism(core, triples, a, b, c, x, y, z)
                    eab = edge_index[tuple(sorted((a, b)))]
                    ebc = edge_index[tuple(sorted((b, c)))]
                    zero_edge = next((ei for ei in sorted((eab, ebc)) if ymap[ei] in zeros), -1)
                    quota_site = -1
                    row_id = -1
                    if zero_edge >= 0:
                        disposition = 0
                        reason = "known_Y_zero_redundant_configurations"
                        branch["known_Y_zero_removed"] += 1
                    else:
                        common_quota = masks[a] & masks[c] & quota_one[b]
                        if common_quota:
                            disposition = 1
                            quota_site = next(inventory.members(common_quota))
                            assert targets[b][quota_site] == 1
                            assert quota_site in triples[a] and quota_site in triples[c]
                            if targets[b][z] == 1:
                                reason = "common_site_quota_one_redundant_configurations"
                                branch["shared_site_quota_one_removed"] += 1
                            else:
                                assert targets[b][z] == 2 and quota_site != z
                                reason = "third_site_quota_one_redundant_configurations"
                                branch["extra_site_quota_one_removed"] += 1
                        else:
                            disposition = 2
                            reason = "retained_literal_pattern_configurations_upper_bound_on_distinct_rows"
                            branch["retained_configuration_count"] += 1
                            counter = Counter()
                            counter[xmap[b]] -= 1
                            counter[ymap[eab]] += 1
                            counter[ymap[ebc]] += 1
                            original = tuple(sorted((j, v) for j, v in counter.items() if v))
                            assert sum(v for _, v in original) == 1
                            assert len(original) in (2, 3) and sorted(v for _, v in original) in ([-1, 2], [-1, 1, 1])
                            terms = tuple(sorted((reverse[j], v) for j, v in original))
                            if terms not in row_ids:
                                row_ids[terms] = len(rows)
                                rows.append({"terms": [list(t) for t in terms],
                                             "original_terms": [list(t) for t in original],
                                             "rhs": 0, "first_literal_witness": len(witnesses)})
                            row_id = row_ids[terms]
                    census[reason] += 1
                    path_key = (b, min(a, c), max(a, c))
                    if path_key not in path_ids:
                        path_ids[path_key] = len(paths_records)
                        paths_records.append([*path_key, len(witnesses), 0, disposition,
                                              row_id, quota_site, zero_edge])
                    path_id = path_ids[path_key]
                    path_record = paths_records[path_id]
                    assert path_record[5:] == [disposition, row_id, quota_site, zero_edge]
                    path_record[4] += 1
                    witness_index[witness_key] = len(witnesses)
                    witnesses.append([a, b, c, x, y, z, eab, ebc, disposition,
                                      path_id, row_id, quota_site, zero_edge])
                    census["literal_pattern_configurations_before_pruning"] += 1
            for name in ("known_Y_zero_removed", "shared_site_quota_one_removed",
                         "extra_site_quota_one_removed", "retained_configuration_count"):
                assert branch[name] == expected[name]
    assert seen_branches == set(expected_branches)
    for key in ("literal_pattern_configurations_before_pruning",
                "known_Y_zero_redundant_configurations",
                "common_site_quota_one_redundant_configurations",
                "third_site_quota_one_redundant_configurations",
                "retained_literal_pattern_configurations_upper_bound_on_distinct_rows"):
        assert census[key] == ledger["census"][key]
    assert len(witnesses) == 107520
    row_transports = []
    for row_id, row in enumerate(rows):
        if row_id % 100 == 0:
            check_time(deadline, "actual-core row transports")
        first = witnesses[row["first_literal_witness"]]
        a, b, c, x, y, z = first[:6]
        transports = []
        for action_id, (g, move) in enumerate(zip(actions, core_actions)):
            moved = (g[a], g[b], g[c], move[x+3]-3, move[y+3]-3, move[z+3]-3)
            wi = witness_index[moved]
            record = witnesses[wi]
            assert record[8] == 2 and record[10] == row_id
            literal_prism(core, triples, *record[:6])
            transports.append([action_id, wi])
        row_transports.append({"row_id": row_id, "literal_witness_transports": transports})
    census["distinct_literal_exterior_paths"] = len(paths_records)
    for code, name in DISPOSITIONS.items():
        census["distinct_paths_"+name] = sum(p[5] == int(code) for p in paths_records)
    census["distinct_quotient_inequalities"] = len(rows)
    census["quotient_rows_with_three_distinct_variables"] = sum(len(row["terms"]) == 3 for row in rows)
    census["quotient_rows_with_a_doubled_Y_variable"] = sum(len(row["terms"]) == 2 for row in rows)
    census["actual_core_row_transports"] = 12*len(rows)
    check_time(deadline, "final exact checks")
    return {"status": "COMPLETE_THREE_EXTERIOR_TWO_EDGE_PRISM_CUT_PREPARATION",
            "source_sha256": sha(Path(__file__).read_bytes()),
            "inventory_source_sha256": INVENTORY_SOURCE_SHA,
            "inputs": {name: {"path": path, "sha256": digest}
                       for name, (path, digest) in INPUTS.items()},
            "controls": inventory.controls(), "census": dict(census),
            "literal_witness_fields": WITNESS_FIELDS,
            "literal_witnesses": witnesses,
            "literal_prism_site_order": ["outside_a", "outside_b", "component_x",
                                         "outside_c", "component_y", "component_z"],
            "literal_prism_rows": PRISM_ROWS,
            "component_indices_shift_by_three_in_fixed_core": True,
            "path_fields": PATH_FIELDS, "paths": paths_records,
            "dispositions": DISPOSITIONS, "rows": rows,
            "actual_core_action_verification": action_report,
            "quotient_row_transport_witnesses": row_transports,
            "complete_all107520_literal_pattern_configurations": True,
            "complete_all_three_exterior_two_edge_prisms_on_fixed_core": True,
            "known_edge_zeros_and_single_mixed_quota_one_only_redundancy_pruning": True,
            "all480_signatures_retained": True, "eligible_edge_domain_size": 68394,
            "joint_reduced_model_variables": 15200,
            "quotient_coordinate_coincidences_combined_by_integer_addition": True,
            "no_edge_product_or_third_selector_moment_used": True,
            "point_loaded": False, "optimizer_calls": 0,
            "other_component_and_alignment_free": True,
            "scope": "Necessary path-edge cuts in the globally prism-free fixed component-zero branch; no complete exterior graph or point conclusion."}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=("prepare", "replay"))
    p.add_argument("--record", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--seconds", type=float, default=30)
    args = p.parse_args()
    assert 0 < args.seconds <= 30 and not args.output.exists()
    if args.mode == "prepare":
        assert not args.record.exists()
    start = time.monotonic()
    deadline = start+args.seconds
    census = Counter()
    try:
        result = build(deadline, census)
        raw = canonical(result)
        if args.mode == "prepare":
            packed = gzip.compress(raw, mtime=0)
            check_time(deadline, "serialized full record")
            args.record.write_bytes(packed)
        else:
            saved = json.loads(gzip.decompress(args.record.read_bytes()))
            assert canonical(saved) == raw
            check_time(deadline, "complete cold replay")
        report = {"status": "PASS: complete two-edge prism cuts "+("prepared" if args.mode == "prepare" else "cold replayed"),
                  "source_sha256": result["source_sha256"],
                  "record_file_sha256": sha(args.record.read_bytes()),
                  "record_raw_sha256": sha(raw),
                  "census": dict(census), "point_loaded": False, "optimizer_calls": 0,
                  "seconds": time.monotonic()-start}
    except Exception as error:
        report = {"status": "INCOMPLETE_NO_COMPLETE_CUT_FAMILY_CLAIM",
                  "source_sha256": sha(Path(__file__).read_bytes()),
                  "partial_census": dict(census),
                  "error_type": type(error).__name__, "error_message": str(error),
                  "point_loaded": False, "optimizer_calls": 0,
                  "seconds": time.monotonic()-start}
        args.output.write_text(json.dumps(report, indent=2)+"\n")
        print(json.dumps(report, indent=2), flush=True)
        raise
    args.output.write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps(report, indent=2), flush=True)


if __name__ == "__main__":
    main()
