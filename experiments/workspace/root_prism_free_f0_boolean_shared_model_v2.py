"""Complete literal Boolean shared model with certified prism/clique rows.

Keep the frozen 12,481-row selector registry and all 68,394 eligible edge
variables. Append 1,884 witnessed prism zeros and all 3,096 retained literal
core-pair cliques to the frozen base. Native preparation never constructs a
CpSolver. Complete standard/native protobuf bytes must agree.
"""
import argparse
from collections import Counter
import gzip
import hashlib
import importlib.util
from itertools import combinations
import json
from pathlib import Path
import resource
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
BASE_SOURCE = ("experiments/workspace/root_prism_free_f0_boolean_shared_model.py",
               "5a1e8026683a7782fce6ec2a2947748356ac9cd5adf32dd2a0663b0dd60bfca2")
MODEL_SECONDS = 90
OWNER_SECONDS = 120
FINAL_VARIABLES = 68934
FINAL_ROWS = 168050


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def import_base():
    path = ROOT / BASE_SOURCE[0]
    assert sha(path) == BASE_SOURCE[1]
    spec = importlib.util.spec_from_file_location("Boolean_shared_frozen_base", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check_prism(core, triples, pair, sites):
    assert len(sites) == len(set(sites)) == 6
    assert all(type(v) is int and 0 <= v < 23 for v in sites)
    rows = list(core) + [0, 0]
    rows[21] = 1 << 22
    rows[22] = 1 << 21
    for exterior, signature in zip((21, 22), pair):
        for i in triples[signature]:
            rows[exterior] |= 1 << (i + 3)
            rows[i + 3] |= 1 << exterior
    for left in combinations(sites, 3):
        right = tuple(v for v in sites if v not in left)
        if all(rows[a] >> b & 1 for triangle in (left, right) for a, b in combinations(triangle, 2)):
            if all(sum(rows[a] >> b & 1 for b in right) == 1 for a in left):
                if all(sum(rows[b] >> a & 1 for a in left) == 1 for b in right):
                    return
    raise AssertionError("saved six-site set is not an induced triangular prism")


def proof_overlay(base, ctx, deadline):
    cfg = ctx["configuration"]
    loaded = {name: base.read_bound(binding) for name, binding in cfg["overlay_inputs"].items()}
    motifs, motif_cold, cliques, clique_cold, actions = [loaded[k] for k in
        ("motifs", "motif_cold", "cliques", "clique_cold", "actions")]
    for key, record in (("motifs", motifs), ("cliques", cliques)):
        source = cfg["proof_sources"][key]
        assert sha(ROOT / source["path"]) == source["sha256"] == record["source_sha256"]
    assert motifs["status"] == "COMPLETE_EXACT_VISIBLE_EDGE_MOTIF_CENSUS"
    assert motifs["all68394_eligible_edges_covered"] and motifs["full480_signature_domain_retained"]
    assert motif_cold["status"] == "PASS: complete edge-motif census cold replayed"
    assert motif_cold["record_sha256"] == cfg["overlay_inputs"]["motifs"]["sha256"]
    assert motif_cold["raw_record_sha256"] == base.value_sha(motifs)
    assert motif_cold["source_sha256"] == motifs["source_sha256"]
    assert cliques["status"] == "COMPLETE_CORE_PAIR_EDGE_CLIQUE_CUTS"
    assert cliques["all480_signatures_and68394_eligible_edges_retained"]
    assert clique_cold["status"] == "PASS: common-core-pair edge-clique replay"
    assert clique_cold["record_file_sha256"] == cfg["overlay_inputs"]["cliques"]["sha256"]
    assert clique_cold["record_raw_sha256"] == base.value_sha(cliques)
    assert clique_cold["source_sha256"] == cliques["source_sha256"]
    assert cliques["inputs"]["zeros"] == cfg["overlay_inputs"]["motifs"]
    assert cliques["inputs"]["actions"] == motifs["inputs"]["actions"] == cfg["overlay_inputs"]["actions"]
    assert all(item["optimizer_calls"] == 0 for item in (motifs, motif_cold, cliques, clique_cold))

    zero_witnesses = {}
    for witness_index, witness in enumerate(motifs["literal_motif_witnesses"]):
        edge = witness["edge_id"]
        assert type(edge) is int and 0 <= edge < 68394 and edge not in zero_witnesses
        assert witness["kind"] == "P" and witness["pair"] == ctx["edges"][edge]
        check_prism(ctx["core"], ctx["triples"], witness["pair"], witness["sites"])
        zero_witnesses[edge] = {"edge_id": edge, "variable_index": 540 + edge,
            "witness_index": witness_index, "witness": witness}
    assert len(zero_witnesses) == motif_cold["literal_motif_witnesses"] == 1884
    zeros = set(zero_witnesses)
    zero_rows = [zero_witnesses[e] for e in sorted(zeros)]
    for offset, row in enumerate(zero_rows):
        row["native_row_index"] = 163070 + offset
    base.check_time(deadline)

    pairs = list(combinations(range(18), 2))
    pair_index = {pair: index for index, pair in enumerate(pairs)}
    quota = [ctx["gram"][i][j] for i, j in pairs]
    assert cliques["component_pairs"] == [list(pair) for pair in pairs]
    assert cliques["core_pair_quotas"] == quota
    assert cliques["ledger_fields"] == ["center", "pair_index", "raw_size", "live_size", "disposition", "row_id"]
    assert len(cliques["ledger"]) == 73440 and len(cliques["rows"]) == len(cliques["row_transports"]) == 258
    buckets = [[] for _ in range(73440)]
    for center in range(480):
        for neighbor, edge in ctx["incident"][center]:
            for pair in combinations(ctx["triples"][neighbor], 2):
                buckets[153 * center + pair_index[pair]].append([neighbor, edge])
    literal_rows, by_ledger = [], {}
    counts = Counter()
    for center in range(480):
        for pi, (i, j) in enumerate(pairs):
            index = center * 153 + pi
            raw = buckets[index]
            live = [item for item in raw if item[1] not in zeros]
            reason = (0 if not live else 1 if len(live) == 1 else 2 if quota[pi] <= 1
                      else 3 if min(ctx["targets"][center][i], ctx["targets"][center][j]) <= 1 else 4)
            saved = cliques["ledger"][index]
            assert saved[:5] == [center, pi, len(raw), len(live), reason]
            counts["disposition_%d" % reason] += 1
            counts["raw_edge_memberships"] += len(raw)
            counts["known_zero_edge_memberships_removed"] += len(raw) - len(live)
            if reason == 4:
                assert quota[pi] == ctx["targets"][center][i] == ctx["targets"][center][j] == 2
                assert 0 <= saved[5] < 258 and len(live) == len({a for a, _ in live})
                assert all(a != center and i in ctx["triples"][a] and j in ctx["triples"][a] for a, _ in live)
                row = {"native_row_index": 164954 + len(literal_rows), "ledger_index": index,
                       "center": center, "core_pair": [i, j], "live_neighbors_and_edge_ids": live,
                       "original_quotient_row_id": saved[5]}
                literal_rows.append(row)
                by_ledger[index] = row
                counts["retained_literal_edge_memberships"] += len(live)
            else:
                assert saved[5] == -1
        base.check_time(deadline)
    assert len(literal_rows) == 3096 and counts["raw_edge_memberships"] == 410364
    assert counts["known_zero_edge_memberships_removed"] == 11304
    assert counts["retained_literal_edge_memberships"] == 30528
    assert [counts["disposition_%d" % k] for k in range(5)] == [25128, 0, 29616, 15600, 3096]

    moves = actions["domain"]["reconstructed21_core_actions"]
    assert len(moves) == len(set(map(tuple, moves))) == 12
    lookup = {tuple(h): a for a, h in enumerate(ctx["triples"])}
    edge_lookup = {tuple(e): index for index, e in enumerate(ctx["edges"])}
    signatures = []
    for move in moves:
        assert sorted(move) == list(range(21)) and set(move[:3]) == set(range(3))
        assert all((ctx["core"][i] >> j & 1) == (ctx["core"][move[i]] >> move[j] & 1)
                   for i in range(21) for j in range(21))
        g = [lookup[tuple(sorted(move[i + 3] - 3 for i in h))] for h in ctx["triples"]]
        assert sorted(g) == list(range(480))
        signatures.append(g)
    assert base.value_sha(ctx["triples"]) == actions["domain"]["triples_sha256"]
    assert base.value_sha(ctx["edges"]) == actions["domain"]["edges_sha256"]
    assert base.value_sha(signatures) == actions["domain"]["selector_actions_sha256"]
    move_set = set(map(tuple, moves))
    assert tuple(range(21)) in move_set
    assert all(tuple(left[right[v]] for v in range(21)) in move_set for left in moves for right in moves)
    covered = set()
    for rid, representative in enumerate(cliques["rows"]):
        index = representative["first_bucket"]
        original = by_ledger[index]
        assert original["original_quotient_row_id"] == rid and representative["rhs"] == 0
        for key in ("center", "core_pair", "live_neighbors_and_edge_ids"):
            assert original[key] == representative[key]
        b = original["center"]
        i, j = original["core_pair"]
        expected_transports = []
        for action_index, (move, g) in enumerate(zip(moves, signatures)):
            pair = tuple(sorted((move[i + 3] - 3, move[j + 3] - 3)))
            image_index = g[b] * 153 + pair_index[pair]
            row = by_ledger[image_index]
            assert image_index not in covered and row["original_quotient_row_id"] == rid
            transported = sorted([g[a], edge_lookup[tuple(sorted((g[a], g[b])))]]
                                 for a, edge in original["live_neighbors_and_edge_ids"])
            assert transported == row["live_neighbors_and_edge_ids"]
            row["original_action_index"] = action_index
            expected_transports.append([action_index, image_index])
            covered.add(image_index)
        assert expected_transports == cliques["row_transports"][rid]
    assert covered == set(by_ledger) and len(covered) == 3096
    base.check_time(deadline)
    return {"schema": "conway99.f0.boolean-shared-overlay-proof.v1",
            "status": "COMPLETE_LITERAL_PRISM_ZEROS_AND_CORE_PAIR_CLIQUES",
            "inputs": cfg["overlay_inputs"], "proof_sources": cfg["proof_sources"],
            "zero_rows": zero_rows, "clique_rows": literal_rows,
            "complete_old_ledger_value_sha256": base.value_sha(cliques["ledger"]),
            "complete_edge_order_sha256": base.value_sha(ctx["edges"]),
            "counts": dict(counts), "all_73440_buckets_checked": True,
            "complete_258_by_12_transport_mapping_checked": True,
            "quotient_variable_ids_used_in_native_rows": False,
            "all_original_edge_variables_retained": True, "optimizer_calls": 0}


def prepare(base, args):
    started = time.monotonic()
    deadline = min(args.deadline, started + MODEL_SECONDS)
    ctx = base.load_context(args.configuration)
    cfg = ctx["configuration"]
    assert cfg["active_builder_sha256"] == sha(__file__)
    assert cfg["model_phase_seconds"] == MODEL_SECONDS and cfg["preparation_owner_seconds"] == OWNER_SECONDS
    assert not cfg["native_query_authorized"] and not cfg["CpSolver_construction_authorized"]
    controls = {name: base.read_bound(binding) for name, binding in cfg["transport_controls"].items()}
    report, owner = controls["report"], controls["owner"]
    assert report["source_sha256"] == owner["source_sha256"] == BASE_SOURCE[1]
    assert report["configuration_sha256"] == cfg["transport_controls"]["configuration"]["sha256"]
    assert owner["report_accepted"] and owner["report_sha256"] == cfg["transport_controls"]["report"]["sha256"]
    assert owner["status"] == report["status"] == "PASS_PUBLIC_NATIVE_TEXT_TRANSPORT_EXACT_BYTES_AND_INVALID_INDEX_REJECTION"
    assert owner["deadline_overrun_seconds"] == 0 and owner["supervision"]["child_reaped"]
    assert owner["supervision"]["returncode"] == 0 and report["valid_control"]["public_parse_return"] is True
    overlay = proof_overlay(base, ctx, deadline)
    stages = {"context_and_complete_overlay_seconds": time.monotonic() - started}
    base.save(args.directory / "stages.json", stages)
    from ortools.sat import cp_model_pb2 as pb
    expected, inventory = base.expected_base(ctx, pb, deadline)
    base_raw_sha = hashlib.sha256(expected.SerializeToString()).hexdigest()
    for row in overlay["zero_rows"]:
        assert len(expected.constraints) == row["native_row_index"]
        base.linear(expected, [row["variable_index"]], [1], 0, 0)
    for row in overlay["clique_rows"]:
        assert len(expected.constraints) == row["native_row_index"]
        variables = [row["center"]] + [540 + edge for _, edge in row["live_neighbors_and_edge_ids"]]
        base.linear(expected, variables, [-1] + [1] * (len(variables) - 1), -1, 0)
    assert len(expected.variables) == FINAL_VARIABLES and len(expected.constraints) == FINAL_ROWS
    retained = pb.CpModelProto()
    retained.CopyFrom(expected)
    del retained.constraints[163070:]
    assert hashlib.sha256(retained.SerializeToString()).hexdigest() == base_raw_sha
    del retained
    stages["expected_model_seconds"] = time.monotonic() - started
    base.save(args.directory / "stages.json", stages)
    raw = expected.SerializeToString()
    expected_raw_sha = hashlib.sha256(raw).hexdigest()
    inventory.update(rows=FINAL_ROWS, prism_zero_rows=1884, literal_core_pair_clique_rows=3096,
                     complete_base_raw_sha256=base_raw_sha, complete_base_rows_preserved_as_submodel=True)
    _, native = base.transport(expected, args.directory / "model.pb", deadline)
    assert native["public_parse_return"] is True and native["native_raw_sha256"] == expected_raw_sha
    stages["model_phase_seconds"] = time.monotonic() - started
    assert stages["model_phase_seconds"] <= MODEL_SECONDS
    base.save(args.directory / "stages.json", stages)
    del expected, _
    model_archive = gzip.compress(raw, compresslevel=6, mtime=0)
    assert gzip.decompress(model_archive) == raw
    (args.directory / "model.pb.gz").write_bytes(model_archive)
    overlay_raw = base.canonical(overlay)
    overlay_archive = gzip.compress(overlay_raw, compresslevel=6, mtime=0)
    (args.directory / "overlay-proof.json.gz").write_bytes(overlay_archive)
    base.check_time(args.deadline)
    result = {"status": "PASS_COMPLETE_BOOLEAN_SHARED_MODEL_NATIVE_PREPARATION",
              "source_sha256": sha(__file__), "base_source_sha256": BASE_SOURCE[1],
              "configuration_sha256": sha(args.configuration), "inventory": inventory,
              "native_transport": native, "stages": stages,
              "model": {"raw_sha256": expected_raw_sha, "raw_bytes": len(raw),
                        "archive_sha256": hashlib.sha256(model_archive).hexdigest(), "archive_bytes": len(model_archive)},
              "overlay": {"raw_sha256": hashlib.sha256(overlay_raw).hexdigest(), "raw_bytes": len(overlay_raw),
                          "archive_sha256": hashlib.sha256(overlay_archive).hexdigest(), "archive_bytes": len(overlay_archive)},
              "seconds": time.monotonic() - started, "peak_rss_KiB": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
              "CpSolver_constructed": False, "optimizer_calls": 0, "native_query_run": False,
              "whole_component_excluded": False, "graph_constructed": False}
    base.save(args.directory / "report.json", result)


def main(args):
    started = time.monotonic()
    base = import_base()
    if args.worker:
        try:
            prepare(base, args)
        except Exception as error:
            base.save(args.directory / "error.json", {"type": type(error).__name__, "message": str(error)})
            raise
        return
    args.directory.mkdir(parents=True, exist_ok=False)
    path = ROOT / base.SUPERVISOR[0]
    assert sha(path) == base.SUPERVISOR[1]
    spec = importlib.util.spec_from_file_location("Boolean_shared_overlay_supervisor", path)
    supervisor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(supervisor)
    deadline = started + OWNER_SECONDS
    command = [sys.executable, str(Path(__file__).resolve()), "--worker", "--configuration", str(args.configuration.resolve()),
               "--directory", str(args.directory.resolve()), "--deadline", str(deadline)]
    base.save(args.directory / "owner.json", {"status": "UNKNOWN_BEFORE_CHILD", "report_accepted": False})
    supervision = supervisor.supervise(command, args.directory, deadline)
    owner = {"source_sha256": sha(__file__), "configuration_sha256": sha(args.configuration),
             "maximum_seconds": OWNER_SECONDS, "supervision": supervision, "status": supervision["status"],
             "report_accepted": False, "CpSolver_constructed": False, "optimizer_calls": 0}
    if supervision["status"] == "CHILD_EXITED" and time.monotonic() <= deadline:
        report = json.loads((args.directory / "report.json").read_bytes())
        assert report["source_sha256"] == sha(__file__) and report["configuration_sha256"] == sha(args.configuration)
        assert report["inventory"]["variables"] == FINAL_VARIABLES and report["inventory"]["rows"] == FINAL_ROWS
        owner.update(report_accepted=True, report_sha256=sha(args.directory / "report.json"), status=report["status"])
    owner.update(seconds=time.monotonic() - started, deadline_overrun_seconds=max(0, time.monotonic() - deadline))
    if owner["deadline_overrun_seconds"]:
        owner.update(report_accepted=False, status="UNKNOWN_HARD_DEADLINE")
    base.save(args.directory / "owner.json", owner)
    print(json.dumps(owner, sort_keys=True), flush=True)


if __name__ == "__main__":
    if not __debug__:
        raise RuntimeError("complete native preparation assertions required")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--configuration", type=Path, required=True)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--deadline", type=float)
    arguments = parser.parse_args()
    assert not arguments.worker or arguments.deadline is not None
    main(arguments)
