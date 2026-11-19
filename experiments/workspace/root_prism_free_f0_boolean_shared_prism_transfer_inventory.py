"""Read-only literal transfer inventory of two accepted prism censuses.

Decode the accepted Boolean model, verify actual native-row implications,
and preserve every old witness/path origin. No model is appended, no
CpModel/CpSolver is constructed, and no optimizer is called. Unmatched
rows are not claimed independent of the complete existing model.
"""
import argparse
from collections import Counter
import gzip
import hashlib
import importlib.util
from itertools import combinations, product
import json
from pathlib import Path
import resource
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
CHECK_SECONDS, OWNER_SECONDS = 30, 45
SUPERVISOR = ("experiments/workspace/root_prism_free_f0_fixed_selection_exterior_query.py",
              "bbe476e5a7a13800c08265d4db541b7e8c7edf2277be03f6d06db134926891e3")
REASONS = {0: "existing_edge_zero", 1: "existing_quota_one_mixed_row",
           2: "inherited_zero_selector_pair", 3: "existing_core_pair_clique",
           4: "not_proved_redundant_by_audited_criteria"}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def digest(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def value_sha(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def save(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(canonical(value) + b"\n")
    temporary.replace(path)


def check_time(deadline):
    if time.monotonic() >= deadline:
        raise TimeoutError("literal prism transfer inventory deadline")


def read(binding, raw=False):
    path = ROOT / binding["path"]
    data = path.read_bytes()
    assert hashlib.sha256(data).hexdigest() == binding["sha256"]
    if raw:
        return data
    return json.loads(gzip.decompress(data) if path.suffix == ".gz" else data)


def pair_id(a, b):
    assert 0 <= a < b < 480
    return a * (959 - a) // 2 + b - a - 1


def native_row(model, index):
    constraint = model.constraints[index]
    assert constraint.WhichOneof("constraint") == "linear" and not constraint.enforcement_literal
    row = constraint.linear
    assert len(row.vars) == len(row.coeffs)
    return [[int(v), int(c)] for v, c in zip(row.vars, row.coeffs)], list(row.domain)


def boolean_implication_controls():
    one_edge = path = 0
    for xa, xb, xc, y1, y2 in product((0, 1), repeat=5):
        if y1 <= xa and xa + xc <= 1:
            assert y1 + xc <= 1
            one_edge += 1
        if y1 <= min(xa, xb) and y2 <= min(xc, xb) and xa + xc <= 1:
            assert y1 + y2 <= xb
            path += 1
    return {"status": "PASS_BINARY_ZERO_PAIR_IMPLICATION_CONTROLS",
            "one_edge_assignments": one_edge, "path_assignments": path,
            "center_Boolean_domain_required_for_path_implication": True}


def inventory(configuration, directory, owner_deadline):
    from ortools.sat import cp_model_pb2 as pb
    started = time.monotonic()
    deadline = min(owner_deadline, started + CHECK_SECONDS)
    cfg = json.loads(configuration.read_bytes())
    assert cfg["schema"] == "conway99.f0.boolean-prism-transfer-inventory-configuration.v1"
    assert cfg["source_sha256"] == digest(__file__)
    assert cfg["check_seconds"] == CHECK_SECONDS and cfg["owner_seconds"] == OWNER_SECONDS
    for binding in cfg["sources"].values():
        assert digest(ROOT / binding["path"]) == binding["sha256"]
    loaded = {name: read(binding) for name, binding in cfg["inputs"].items() if name != "model"}
    cold, cold_owner = loaded["model_cold"], loaded["model_cold_owner"]
    assert cold["status"] == "PASS_INDEPENDENT_COMPLETE_BOOLEAN_SHARED_MODEL"
    assert cold_owner["status"] == "OWNED_COMPLETE_BOOLEAN_SHARED_MODEL_COLD_ACCEPTED"
    assert cold_owner["report_accepted"] and cold_owner["report"] == cfg["inputs"]["model_cold"]
    assert cold["source"] == cold_owner["source"] == cfg["sources"]["model_cold"]
    assert cold_owner["supervision"]["exit_code"] == 0 and cold_owner["supervision"]["child_reaped"]
    assert not cold_owner["supervision"]["hard_timeout"]
    assert cold["preparation_inputs"]["model"] == cfg["inputs"]["model"]
    assert cold["preparation_inputs"]["overlay"] == cfg["inputs"]["overlay"]
    raw = gzip.decompress(read(cfg["inputs"]["model"], raw=True))
    assert len(raw) == cold["native_raw_model_bytes"] == 33451907
    assert hashlib.sha256(raw).hexdigest() == cold["native_raw_model_sha256"] == cfg["model_raw_sha256"]
    model = pb.CpModelProto()
    model.ParseFromString(raw)
    assert model.SerializeToString() == raw and len(model.variables) == 68934 and len(model.constraints) == 168050
    domain, plan, overlay = loaded["domain"], loaded["literal_plan"], loaded["overlay"]
    triples = domain["signature_domain"]
    assert triples == plan["signature_domain"] and len(triples) == 480
    assert value_sha(triples) == cold["inventory"]["signature_domain_sha256"]
    assert plan["core_rows"] == domain["component_core_rows"]
    assert all(list(model.variables[a].domain) == [0, 1] for a in range(480))
    edges = []
    for a, neighbors in enumerate(domain["possible_neighbor_signature_ids"]):
        for b in neighbors:
            if a < b:
                edge = len(edges)
                edges.append([a, b])
                assert model.variables[540 + edge].name == "shared_edge_%03d_%03d" % (a, b)
                assert list(model.variables[540 + edge].domain) == [0, 1]
    assert len(edges) == 68394 and value_sha(edges) == cold["inventory"]["edge_domain_sha256"]
    edge_lookup = {tuple(e): i for i, e in enumerate(edges)}
    targets = domain["row_targets"]
    assert value_sha(targets) == cold["inventory"]["targets_sha256"]
    verified_activations = set()
    def activation(edge, endpoint):
        assert endpoint in edges[edge]
        index = 17162 + 2 * edge + int(endpoint == edges[edge][1])
        if index not in verified_activations:
            assert native_row(model, index) == ([[endpoint, -1], [540 + edge, 1]], [-1, 0])
            verified_activations.add(index)
        return index

    zero_pairs = {}
    for original_index, row in enumerate(plan["original_selector_equalities"]):
        if row["quota"] != 1:
            continue
        index = plan["original_to_native_rows"][original_index]
        assert type(index) is int
        assert native_row(model, index) == ([[a, 1] for a in row["support"]], [1, 1])
        for a, b in combinations(row["support"], 2):
            p = pair_id(a, b)
            assert p not in zero_pairs
            zero_pairs[p] = {"pair_id": p, "pair": [a, b], "premise": "quota-one Gram equality",
                             "original_row_id": original_index, "native_row_index": index}
    assert len(zero_pairs) == 4320
    for motif_id, (a, b) in enumerate(plan["motif_pairs"]):
        index = plan["motif_to_native_rows"][motif_id]
        assert native_row(model, index) == ([[a, 1], [b, 1]], [0, 1])
        p = pair_id(a, b)
        assert p not in zero_pairs
        zero_pairs[p] = {"pair_id": p, "pair": [a, b], "premise": "explicit motif conflict",
                         "motif_id": motif_id, "native_row_index": index}
    assert len(zero_pairs) == len(plan["zero_pair_implications"]) == 4410
    assert [{k: v for k, v in zero_pairs[p].items() if k != "native_row_index"} for p in sorted(zero_pairs)] == plan["zero_pair_implications"]
    zeros = {}
    for row in overlay["zero_rows"]:
        e, index = row["edge_id"], row["native_row_index"]
        assert e not in zeros and native_row(model, index) == ([[540 + e, 1]], [0, 0])
        zeros[e] = index
    assert len(zeros) == 1884
    clique_covers = {}
    for row in overlay["clique_rows"]:
        center, index = row["center"], row["native_row_index"]
        live_edges = [e for a, e in row["live_neighbors_and_edge_ids"]]
        assert native_row(model, index) == ([[center, -1]] + [[540 + e, 1] for e in live_edges], [-1, 0])
        for e1, e2 in combinations(sorted(live_edges), 2):
            key = (center, e1, e2)
            assert key not in clique_covers
            clique_covers[key] = index
    assert len(overlay["clique_rows"]) == 3096 and len(clique_covers) == 136740
    mixed = {}
    def mixed_receipt(center, site, e1, e2):
        index = 154430 + 18 * center + site
        if index not in mixed:
            terms, bounds = native_row(model, index)
            assert bounds == [0, 0] and terms[0] == [center, -1]
            assert all(540 <= v < 68934 and c == 1 for v, c in terms[1:])
            mixed[index] = {v for v, c in terms[1:]}
            assert len(mixed[index]) == len(terms) - 1
        assert 540 + e1 in mixed[index] and 540 + e2 in mixed[index]
        return index
    check_time(deadline)

    one, paths = loaded["one_edge"], loaded["paths"]
    assert one["complete_all68394_edge_coverage"] and one["all480_selectors_retained"]
    assert paths["complete_all107520_literal_pattern_configurations"] and paths["all480_signatures_retained"]
    for name, record, expected_status in (("one_edge", one, "PASS: three-vertex prism cuts cold replayed"),
                                           ("paths", paths, "PASS: complete two-edge prism cuts cold replayed")):
        replay = loaded[name + "_cold"]
        assert replay["status"] == expected_status
        assert replay["record_file_sha256"] == cfg["inputs"][name]["sha256"]
        assert replay["record_raw_sha256"] == value_sha(record)
        assert replay["source_sha256"] == record["source_sha256"] == cfg["sources"][name]["sha256"]
        assert replay["optimizer_calls"] == record["optimizer_calls"] == 0
    one_ledger, one_proposed, one_counts, one_keys = [], [], Counter(), set()
    for witness_id, witness in enumerate(one["literal_prism_witnesses"]):
        e, c = witness["edge_id"], witness["third_selector"]
        a, b = edges[e]
        assert witness["exterior_edge"] == [a, b] and c not in (a, b)
        assert len(set(triples[a]) & set(triples[c])) == len(set(triples[b]) & set(triples[c])) == 2
        assert (e, c) not in one_keys
        one_keys.add((e, c))
        pair_options = [zero_pairs[p] for v in (a, b) if (p := pair_id(*sorted((v, c)))) in zero_pairs]
        for item in witness["cut_dispositions"]:
            endpoint = item["endpoint"]
            assert endpoint in (a, b)
            p = pair_id(*sorted((endpoint, c)))
            expected_reason = ("known_Y_zero_then_pair_activation" if e in zeros else
                               "known_Z_zero_then_edge_activation" if p in zero_pairs else "retained_quotient_inequality")
            assert item["reason"] == expected_reason
        if e in zeros:
            reason, receipt = 0, [zeros[e]]
        elif pair_options:
            proof = min(pair_options, key=lambda item: item["pair_id"])
            endpoint = next(v for v in (a, b) if v in proof["pair"])
            reason, receipt = 2, [proof["native_row_index"], activation(e, endpoint)]
        else:
            reason, receipt = 4, []
            one_proposed.append([e, c, witness_id])
        one_counts[reason] += 1
        one_ledger.append([e, c, witness_id, reason, receipt])
    assert len(one_ledger) == 9360 and one_counts == {0: 228, 2: 7908, 4: 1224}
    check_time(deadline)

    assert paths["literal_witness_fields"] == ["a", "b", "c", "x", "y", "z", "edge_ab_id", "edge_bc_id", "disposition", "path_id", "row_id", "quota_one_site", "known_zero_edge_id"]
    assert paths["path_fields"] == ["center_b", "endpoint_min", "endpoint_max", "first_witness", "witness_count", "disposition", "row_id", "quota_one_site", "known_zero_edge_id"]
    origins = [[] for _ in paths["paths"]]
    for witness_id, w in enumerate(paths["literal_witnesses"]):
        assert len(w) == 13 and all(type(v) is int for v in w)
        a, b, c, x, y, z, e1, e2, old_reason, path_id_, row_id_, quota_site, zero_edge = w
        assert len({a, b, c}) == 3 and edges[e1] == sorted((a, b)) and edges[e2] == sorted((b, c))
        assert paths["paths"][path_id_][:3] == [b, min(a, c), max(a, c)]
        assert paths["paths"][path_id_][5:7] == [old_reason, row_id_]
        assert len({x, y, z}) == 3 and all(0 <= i < 18 for i in (x, y, z))
        assert z in triples[a] and z in triples[c]
        origins[path_id_].append(witness_id)
    assert len(paths["literal_witnesses"]) == 107520 and len(origins) == 107418
    path_ledger, path_proposed, path_counts, path_keys = [], [], Counter(), set()
    for path_id_, item in enumerate(paths["paths"]):
        center, a, c, first, multiplicity, old_reason, old_row, quota_site, zero_edge = item
        assert a < c and origins[path_id_] and first == origins[path_id_][0] and multiplicity == len(origins[path_id_])
        e1, e2 = sorted((edge_lookup[tuple(sorted((a, center)))], edge_lookup[tuple(sorted((c, center)))]))
        key = (center, e1, e2)
        assert key not in path_keys
        path_keys.add(key)
        common = sorted(set(triples[a]) & set(triples[c]))
        quota_sites = [i for i in common if targets[center][i] == 1]
        if e1 in zeros or e2 in zeros:
            zero = min(e for e in (e1, e2) if e in zeros)
            other = e2 if zero == e1 else e1
            reason, receipt = 0, [zeros[zero], activation(other, center)]
            assert old_reason == 0 and zero_edge in zeros and zero_edge in (e1, e2)
        elif quota_sites:
            reason, receipt = 1, [mixed_receipt(center, quota_sites[0], e1, e2)]
            assert old_reason == 1 and quota_site in quota_sites
        elif (p := pair_id(a, c)) in zero_pairs:
            reason = 2
            receipt = [zero_pairs[p]["native_row_index"]] + [activation(e, v) for e in (e1, e2) for v in edges[e]]
            assert old_reason == 2
        elif key in clique_covers:
            reason, receipt = 3, [clique_covers[key]]
            assert old_reason == 2
        else:
            reason, receipt = 4, []
            assert old_reason == 2
            path_proposed.append([center, e1, e2, path_id_])
        path_counts[reason] += 1
        path_ledger.append([center, e1, e2, path_id_, reason, receipt])
        if path_id_ % 4096 == 0:
            check_time(deadline)
    assert path_counts == {0: 8664, 1: 37278, 2: 2112, 3: 1368, 4: 57996}
    transports = []
    for rid, item in enumerate(paths["quotient_row_transport_witnesses"]):
        assert item["row_id"] == rid and len(item["literal_witness_transports"]) == 12
        for action, witness_id in item["literal_witness_transports"]:
            assert 0 <= action < 12 and paths["literal_witnesses"][witness_id][10] == rid
            transports.append(paths["literal_witnesses"][witness_id][9])
    assert len(transports) == 61488 and len(set(transports)) == 61476
    assert set(transports) == {i for i, item in enumerate(paths["paths"]) if item[5] == 2}
    one_proposed.sort()
    path_proposed.sort()
    assert len(one_proposed) + len(path_proposed) == 59220
    data = {"schema": "conway99.f0.boolean-prism-transfer-inventory.v1", "inputs": cfg["inputs"],
            "source_sha256": digest(__file__), "configuration_sha256": digest(configuration),
            "model_raw_sha256": cfg["model_raw_sha256"], "reasons": REASONS,
            "one_edge_ledger_fields": ["edge_id", "third_selector", "old_witness_id", "reason", "actual_native_premise_rows"],
            "one_edge_ledger": one_ledger, "path_ledger_fields": ["center", "edge_min", "edge_max", "old_path_id", "reason", "actual_native_premise_rows"],
            "path_ledger": path_ledger, "complete_path_witness_origins": origins,
            "zero_pair_native_receipts": [zero_pairs[p] for p in sorted(zero_pairs)],
            "proposed_one_edge_fields": ["edge_id", "third_selector", "old_witness_id"], "proposed_one_edge": one_proposed,
            "proposed_path_fields": ["center", "edge_min", "edge_max", "old_path_id"], "proposed_paths": path_proposed,
            "proposed_order": "one-edge keys sorted by edge/third, then path keys sorted by center/edge-min/edge-max",
            "one_edge_row_definition": "x_third+y_edge<=1", "path_row_definition": "y_edge_min+y_edge_max-x_center<=0",
            "one_edge_dispositions": dict(one_counts), "path_dispositions": dict(path_counts),
            "existing_activation_rows_checked": len(verified_activations), "existing_mixed_rows_checked": len(mixed),
            "old_census_producers_imported": False, "old_censuses_reenumerated": False,
            "native_rows_appended": 0, "CpModel_constructed": False, "CpSolver_constructed": False,
            "optimizer_calls": 0, "unmatched_rows_not_claimed_independent": True}
    check_time(deadline)
    elapsed = time.monotonic() - started
    raw_inventory = canonical(data)
    archive = gzip.compress(raw_inventory, compresslevel=6, mtime=0)
    (directory / "complete-inventory.json.gz").write_bytes(archive)
    result = {"status": "PASS_COMPLETE_LITERAL_TRANSFER_INVENTORY_AWAITING_INDEPENDENT_REPLAY",
              "source_sha256": digest(__file__), "configuration_sha256": digest(configuration),
              "controls": boolean_implication_controls(), "one_edge_dispositions": dict(one_counts), "path_dispositions": dict(path_counts),
              "proposed_one_edge_rows": len(one_proposed), "proposed_path_rows": len(path_proposed),
              "proposed_total_rows": 59220, "proposed_new_nonzeros": 176436, "following_rows_if_transferred": 227270,
              "variables_if_transferred": 68934, "complete_old_path_witnesses": 107520, "complete_old_one_edge_witnesses": 9360,
              "actual_native_zero_pair_receipts": 4410, "all_old_retained_transport_paths_covered": 61476,
              "inventory": {"archive_sha256": hashlib.sha256(archive).hexdigest(), "archive_bytes": len(archive),
                            "raw_sha256": hashlib.sha256(raw_inventory).hexdigest(), "raw_bytes": len(raw_inventory)},
              "check_phase_seconds": elapsed, "seconds": time.monotonic() - started,
              "peak_rss_KiB": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
              "native_rows_appended": 0, "CpModel_constructed": False, "CpSolver_constructed": False,
              "optimizer_calls": 0, "unmatched_rows_not_claimed_independent": True,
              "graph_constructed": False, "whole_component_excluded": False}
    check_time(owner_deadline)
    save(directory / "report.json", result)


def main(args):
    started = time.monotonic()
    if args.worker:
        try:
            inventory(args.configuration, args.directory, args.deadline)
        except Exception as error:
            save(args.directory / "error.json", {"type": type(error).__name__, "message": str(error)})
            raise
        return
    args.directory.mkdir(parents=True, exist_ok=False)
    path = ROOT / SUPERVISOR[0]
    assert digest(path) == SUPERVISOR[1]
    spec = importlib.util.spec_from_file_location("literal_transfer_inventory_supervisor", path)
    supervisor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(supervisor)
    deadline = started + OWNER_SECONDS
    command = [sys.executable, str(Path(__file__).resolve()), "--worker", "--configuration", str(args.configuration.resolve()),
               "--directory", str(args.directory.resolve()), "--deadline", str(deadline)]
    save(args.directory / "owner.json", {"status": "UNKNOWN_BEFORE_CHILD", "report_accepted": False})
    supervision = supervisor.supervise(command, args.directory, deadline)
    owner = {"source_sha256": digest(__file__), "configuration_sha256": digest(args.configuration),
             "maximum_seconds": OWNER_SECONDS, "supervision": supervision, "status": supervision["status"], "report_accepted": False}
    if supervision["status"] == "CHILD_EXITED" and time.monotonic() <= deadline:
        report = json.loads((args.directory / "report.json").read_bytes())
        owner.update(status=report["status"], report_accepted=True, report_sha256=digest(args.directory / "report.json"))
    owner.update(seconds=time.monotonic() - started, deadline_overrun_seconds=max(0, time.monotonic() - deadline))
    if owner["deadline_overrun_seconds"]:
        owner.update(status="UNKNOWN_HARD_DEADLINE", report_accepted=False)
    save(args.directory / "owner.json", owner)
    print(json.dumps(owner, sort_keys=True), flush=True)


if __name__ == "__main__":
    if not __debug__:
        raise RuntimeError("literal native-row receipt checks required")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--configuration", type=Path, required=True)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--deadline", type=float)
    arguments = parser.parse_args()
    assert not arguments.worker or arguments.deadline is not None
    main(arguments)
