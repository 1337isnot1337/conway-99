"""Complete literal local-neighbor models for the 41 unqueried F0 centers.

The frozen center-355 encoder is reused without changing its module globals.
No matching constraints, quotient equalities, or production solves are added.
"""
import argparse
from collections import Counter
from fractions import Fraction
import gzip
import hashlib
import importlib.util
from itertools import combinations
import json
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[2]
BASE = "experiments/logs/root-prism-free/"
ENCODER_PATH = "experiments/workspace/root_prism_free_f0_local_center355.py"
ENCODER_SHA = "e3e7852c674ec132f1a08f4ca9ff4ea0d11a581be4f6f39d512b8114b48d3054"
REUSE = {
    "old_instance": (BASE+"f0-local-center355-preparation01/instance.json",
                     "1619eb8050ee496c2e0f8f8ca65dbc98c6fee01c259b98e91c377d2ea2b3943d"),
    "old_model": (BASE+"f0-local-center355-preparation01/model.json",
                  "1cdd8113ee62eff4b87bfaa24e4e5638ff94a3c4270a0449aa38384787598b86"),
    "old_controls": (BASE+"f0-local-center355-preparation01/preparation.json",
                     "1cf0c80b67e0956d62197d880cf2cc06e83f8ad049f0038430877b9cd86fc56a"),
    "old_result": (BASE+"f0-local-center355-pilot01/result.json",
                   "691770408d6af35c86cd06004344b51159dbd6ba8ceafd2b185b5764ee37cd0e"),
    "old_replay": (BASE+"f0-local-center355-pilot01-replay/result.json",
                   "d7f61ccc7b2916d545fab07443104fe8d01a9b71368248ed063fb1361730b217"),
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def bits(sites):
    return sum(1 << i for i in sites)


def tick(deadline):
    if deadline is not None and time.monotonic() >= deadline:
        raise TimeoutError("Local-model preparation deadline reached")


def load():
    assert sha((ROOT/ENCODER_PATH).read_bytes()) == ENCODER_SHA
    spec = importlib.util.spec_from_file_location("frozen_center355_encoder", ROOT/ENCODER_PATH)
    encoder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(encoder)
    loaded = {}
    bindings = dict(encoder.INPUTS, **REUSE)
    for name, (path, digest) in bindings.items():
        raw = (ROOT/path).read_bytes()
        assert sha(raw) == digest, path
        loaded[name] = json.loads(gzip.decompress(raw) if path.endswith(".gz") else raw)
    data = loaded["domain"]["validation"]
    core, triples, edges = data["core"], data["triples"], data["edges"]
    assert len(core) == 21 and len(triples) == 480 and len(edges) == 68394
    records = {r["center"]: r for r in loaded["inventory"]["representative_records"]}
    assert len(records) == 42 and sorted(records) == [min(o) for o in data["selector_orbits"]]
    replay = loaded["complete_replay"]
    assert replay["complete_centers"] == 42 and replay["literal_centers_covered"] == 480
    assert replay["status"].startswith("PASS:")
    assert replay["production_record_raw_sha256"] == sha(canonical(loaded["inventory"]))
    prep = loaded["inventory_preparation"]
    assert prep["center_transports"] == loaded["inventory"]["center_transports"]
    assert [row[0] for row in prep["center_transports"]] == list(range(480))
    actions, core_actions = prep["selector_actions"], prep["core_actions"]
    assert len(actions) == len(core_actions) == 12
    assert actions == loaded["paths"]["actual_core_action_verification"]["selector_actions"]
    assert core_actions == loaded["paths"]["actual_core_action_verification"]["core_actions"]
    for action, move in zip(actions, core_actions):
        assert sorted(action) == list(range(480)) and sorted(move) == list(range(21))
        assert sorted(move[:3]) == [0, 1, 2] and sorted(move[3:]) == list(range(3, 21))
        for i in range(21):
            assert bits(move[j] for j in range(21) if core[i] >> j & 1) == core[move[i]]
        for a, h in enumerate(triples):
            assert sorted(move[i+3]-3 for i in h) == triples[action[a]]
    ymap = {e: 42+o for o, orbit in enumerate(data["edge_orbits"]) for e in orbit}
    assert sorted(ymap) == list(range(len(edges)))
    zeros = set(loaded["edge_zeros"]["forced_zero_original_Y_variables"])
    live = [[] for _ in range(480)]
    for ei, (a, c) in enumerate(edges):
        if ymap[ei] not in zeros:
            live[a].append((c, ei))
            live[c].append((a, ei))
    for neighbors in live:
        neighbors.sort()
    for b, orbit_id, rep, gi in prep["center_transports"]:
        assert rep == min(data["selector_orbits"][orbit_id]) and b in data["selector_orbits"][orbit_id]
        assert actions[gi][rep] == b
        assert sorted(actions[gi][a] for a, _ in live[rep]) == [a for a, _ in live[b]]
        move = core_actions[gi]
        assert all(data["targets"][b][move[i+3]-3] == data["targets"][rep][i] for i in range(18))
    return {"loaded": loaded, "data": data, "core": core, "triples": triples,
            "records": records, "ymap": ymap, "live": live, "bindings": bindings,
            "encoder": encoder, "component": [row >> 3 for row in core[3:]]}


def literal_path(core, triples, center, witness):
    a, b, c, x, y, z = witness[:6]
    assert b == center and len({a, b, c}) == len({x, y, z}) == 3
    rows = core[:]+[0, 0, 0]
    for v, sid in ((21, a), (22, b), (23, c)):
        for i in triples[sid]:
            rows[v] |= 1 << (i+3)
            rows[i+3] |= 1 << v
    for v, w in ((21, 22), (22, 23)):
        rows[v] |= 1 << w
        rows[w] |= 1 << v
    sites = [21, 22, x+3, 23, y+3, z+3]
    induced = [sum(((rows[v] >> w) & 1) << j for j, w in enumerate(sites)) for v in sites]
    assert induced == [38, 13, 19, 50, 44, 25]
    assert (rows[21] & rows[23]).bit_count() >= 2
    return sorted((a, c))


def native(bundle, center):
    data, core, triples = bundle["data"], bundle["core"], bundle["triples"]
    record = bundle["records"][center]
    assert record["literal_neighbor_variables_untied"] and record["center_is_conditioned_selected"]
    live = bundle["live"][center]
    neighbors, edge_ids = [a for a, _ in live], [e for _, e in live]
    n = len(neighbors)
    assert neighbors == record["neighbor_ids"] and edge_ids == record["neighbor_edge_ids"]
    assert len(set(neighbors)) == n and center not in neighbors
    quotient = [bundle["ymap"][e] for e in edge_ids]
    assert quotient == record["neighbor_quotient_Y_columns"]
    target = [2-int(i in triples[center])-sum(bundle["component"][i] >> j & 1 for j in triples[center])
              for i in range(18)]
    assert target == record["mixed_quotas"] == data["targets"][center]
    assert sum(target) == 24 and all(q in (0, 1, 2) for q in target)
    assert all(len(triples[a]) == 3 for a in neighbors)
    mixed = [{"component_site": i, "variables": [k+1 for k, a in enumerate(neighbors) if i in triples[a]],
              "demand": target[i]} for i in range(18)]
    assert sum(len(row["variables"]) for row in mixed) == 3*n
    assert record["degree_from_quotas"] == 8
    path_pairs, path_references = set(), []
    paths = bundle["loaded"]["paths"]
    for identifier in record["published_path_pair_ids"]:
        p = paths["paths"][identifier]
        assert p[0] == center and p[5] == 2
        witness = paths["literal_witnesses"][p[3]]
        assert literal_path(core, triples, center, witness) == p[1:3]
        assert tuple(p[1:3]) not in path_pairs
        path_pairs.add(tuple(p[1:3]))
        path_references.append([identifier, p[3], p[6]])
    motifs = set(map(tuple, data["motif_pairs"]))
    assert len(motifs) == 90
    adj = {a: int(value, 16) for a, value in zip(neighbors, record["full_conflict_adjacency_hex"])}
    quota_one = bits(i for i, q in enumerate(target) if q == 1)
    masks = {a: bits(triples[a]) for a in neighbors}
    conflicts, reasons = [], Counter()
    for ia, ic in combinations(range(n), 2):
        a, c = neighbors[ia], neighbors[ic]
        common = masks[a] & masks[c]
        reason = ("mixed quota one" if common & quota_one else
                  "two common core sites" if common.bit_count() >= 2 else
                  "literal path prism" if (a, c) in path_pairs else
                  "certified selector motif" if (a, c) in motifs else None)
        assert bool(adj[a] >> c & 1) == bool(adj[c] >> a & 1) == (reason is not None)
        if reason is not None:
            conflicts.append([ia+1, ic+1])
            reasons[reason] += 1
    universe = bits(neighbors)
    assert all(not (adj[a] >> a & 1) and not (adj[a] & ~universe) for a in neighbors)
    assert 2*len(conflicts) == sum(adj[a].bit_count() for a in neighbors)
    orbit = data["selector_orbits"][record["orbit_id"]]
    assert orbit == record["center_orbit"]
    transports = [r for r in bundle["loaded"]["inventory_preparation"]["center_transports"] if r[0] in orbit]
    assert len(transports) == len(orbit) and all(r[2] == center for r in transports)
    return {"schema": "conway99.f0-local-neighbor-native.v1", "center": center,
            "center_signature": triples[center], "center_selector_orbit": orbit,
            "center_transports": transports, "center_is_selected": True,
            "neighbors": neighbors, "neighbor_signatures": [triples[a] for a in neighbors],
            "neighbor_edge_ids": edge_ids, "neighbor_quotient_Y_columns": quotient,
            "primitive_variables": n, "primitive_bits_are_distinct": True,
            "quotient_equalities_imposed": 0, "mixed_rows": mixed,
            "population_row": {"variables": list(range(1, n+1)), "demand": 8},
            "population_is_redundant_by_three_times_sum": True,
            "conflicts": conflicts, "conflict_provenance_counts": dict(reasons),
            "literal_path_proof_references": path_references,
            "all_candidates_and_conflicts_retained": True,
            "other_component_and_alignment_free": True,
            "global_selector_population_or_Gram_system_added": False,
            "neighbors_mutual_matching_added": False,
            "scope": "Necessary local eight-neighbor projection. SAT is not graph completion."}


def build(bundle, center):
    instance = native(bundle, center)
    encoder = bundle["encoder"]
    n = instance["primitive_variables"]
    clauses, variables, sizes = encoder.encode(n, instance["mixed_rows"], instance["conflicts"],
                                               instance["population_row"])
    raw = encoder.dimacs(clauses, variables)
    model = {"center": center, "source_sha256": sha(Path(__file__).read_bytes()),
             "encoder_source_sha256": ENCODER_SHA, "pysat_version": encoder.pysat.__version__,
             "encoding": "Frozen EncType.seqcounter with one IDPool starting at n+1",
             "native_canonical_sha256": sha(canonical(instance)), "cnf_sha256": sha(raw),
             "primitive_variables": n, "total_variables": variables,
             "auxiliary_variables": variables-n, "clauses": len(clauses), "cnf_bytes": len(raw),
             "conflicts": len(instance["conflicts"]), "count_rows": sizes,
             "density_numerator": len(instance["conflicts"]), "density_denominator": n*(n-1)//2,
             "quotient_equalities_imposed": 0, "matching_constraints_added": False,
             "SAT_scope": instance["scope"],
             "UNSAT_scope": "Only an independently checked proof excludes the selected center orbit."}
    return instance, clauses, variables, raw, model


def inspect(instance, core, selected):
    n = instance["primitive_variables"]
    assert selected == sorted(set(selected)) and len(selected) == 8
    assert all(type(v) is int and 1 <= v <= n for v in selected)
    chosen = set(selected)
    observed = [sum(v in chosen for v in row["variables"]) for row in instance["mixed_rows"]]
    assert observed == [row["demand"] for row in instance["mixed_rows"]]
    assert all(not (a in chosen and c in chosen) for a, c in instance["conflicts"])
    assert sum(observed) == 24
    signatures = [instance["center_signature"]]+[instance["neighbor_signatures"][v-1] for v in selected]
    partial = core[:]+[0]*9
    for outside, signature in enumerate(signatures, start=21):
        for i in signature:
            partial[outside] |= 1 << (i+3)
            partial[i+3] |= 1 << outside
    for neighbor in range(22, 30):
        partial[21] |= 1 << neighbor
        partial[neighbor] |= 1 << 21
    assert partial[21].bit_count() == 11
    assert all((partial[i] & partial[j]).bit_count() <= 2-(partial[i] >> j & 1)
               for i, j in combinations(range(30), 2))
    return {"status": "PASS: exact native local Boolean neighbor witness",
            "selected_primitive_variables": selected,
            "selected_neighbor_ids": [instance["neighbors"][v-1] for v in selected],
            "selected_neighbor_signatures": [instance["neighbor_signatures"][v-1] for v in selected],
            "all18_mixed_counts": observed, "exterior_neighbor_count": 8,
            "conflict_constraints_checked": len(instance["conflicts"]),
            "visible_partial_vertices": 30, "visible_common_neighbor_caps_checked": 435,
            "partial_adjacency_rows": partial, "global_graph_completion_claimed": False}


def ordered_centers(bundle):
    records = bundle["records"]
    def key(center):
        r = records[center]
        n = len(r["neighbor_ids"])
        e = sum(int(value, 16).bit_count() for value in r["full_conflict_adjacency_hex"])//2
        return -Fraction(e, n*(n-1)//2), center
    return [336]+sorted((b for b in records if b not in (336, 355)), key=key)


def prepare(directory, seconds):
    assert not directory.exists() and 0 < seconds <= 60
    directory.mkdir(parents=True)
    started = time.monotonic()
    deadline = started+seconds
    progress = {"status": "INCOMPLETE_NO_QUERY_PREPARATION", "completed_centers": []}
    try:
        bundle = load()
        centers = ordered_centers(bundle)
        assert len(centers) == len(set(centers)) == 41 and set(centers) | {355} == set(bundle["records"])
        old, _, _, old_raw, _ = build(bundle, 355)
        frozen_old = bundle["loaded"]["old_instance"]
        for key in ("center", "center_signature", "center_selector_orbit", "center_transports",
                    "neighbors", "neighbor_signatures", "neighbor_edge_ids", "neighbor_quotient_Y_columns",
                    "primitive_variables", "mixed_rows", "population_row", "conflicts",
                    "conflict_provenance_counts", "literal_path_proof_references"):
            assert old[key] == frozen_old[key], key
        assert sha(old_raw) == bundle["loaded"]["old_model"]["cnf_sha256"]
        previous = bundle["loaded"]["old_result"]
        assert previous["status"] == "SAT_EXACT_LOCAL_BOOLEAN_NEIGHBOR_WITNESS"
        assert bundle["loaded"]["old_replay"]["status"] == "PASS: exact SAT local-row and CNF replay"
        witness = inspect(old, bundle["core"], previous["native_witness"]["selected_primitive_variables"])
        assert witness == previous["native_witness"]
        assert bundle["loaded"]["old_controls"]["production_queries"] == 0
        controls = {"frozen_encoder_controls": bundle["loaded"]["old_controls"]["controls"],
                    "synthetic_solver_controls_repeated": False,
                    "center355_native_projection_and_CNF_exact_match": True,
                    "center355_exact_witness_rechecked_without_solver": True}
        entries = []
        for center in centers:
            tick(deadline)
            instance, _, _, raw, model = build(bundle, center)
            sub = directory/("center-"+str(center))
            sub.mkdir()
            instance_raw, model_raw = canonical(instance)+b"\n", canonical(model)+b"\n"
            (sub/"instance.json").write_bytes(instance_raw)
            (sub/"model.json").write_bytes(model_raw)
            (sub/"model.cnf").write_bytes(raw)
            entry = {"center": center, "directory": sub.name,
                     "instance_file_sha256": sha(instance_raw), "model_file_sha256": sha(model_raw),
                     **{k: model[k] for k in ("cnf_sha256", "primitive_variables", "total_variables",
                                              "clauses", "cnf_bytes", "conflicts", "density_numerator",
                                              "density_denominator")}}
            entries.append(entry)
            progress["completed_centers"] = entries[:]
            (directory/"progress.json").write_bytes(canonical(progress)+b"\n")
        tick(deadline)
        index = {"schema": "conway99.f0-local41-preparation.v1",
                 "status": "COMPLETE_41_LOCAL_MODELS_NO_PRODUCTION_QUERY",
                 "builder_source_sha256": sha(Path(__file__).read_bytes()),
                 "encoder": {"path": ENCODER_PATH, "sha256": ENCODER_SHA},
                 "inputs": {k: {"path": p, "sha256": h} for k, (p, h) in bundle["bindings"].items()},
                 "centers": centers, "models": entries,
                 "ordering": "Center 336 first; all other unqueried centers by decreasing exact conflict density, then increasing ID.",
                 "reused_center": 355, "reused_center_orbit": old["center_selector_orbit"],
                 "new_representatives": 41, "all_representatives": 42,
                 "new_literal_centers_covered": sum(len(bundle["records"][b]["center_orbit"]) for b in centers),
                 "all_literal_centers_covered": 480,
                 "core_rows": bundle["core"],
                 "center_transports": bundle["loaded"]["inventory_preparation"]["center_transports"],
                 "controls": controls,
                 "production_queries": 0, "matching_constraints_added": False,
                 "quotient_equalities_imposed": 0,
                 "total_CNF_variables": sum(x["total_variables"] for x in entries),
                 "total_CNF_clauses": sum(x["clauses"] for x in entries),
                 "total_CNF_bytes": sum(x["cnf_bytes"] for x in entries),
                 "seconds": time.monotonic()-started}
        (directory/"preparation.json").write_text(json.dumps(index, indent=2)+"\n")
        progress = {"status": index["status"], "completed_centers": centers,
                    "preparation_sha256": sha((directory/"preparation.json").read_bytes()),
                    "seconds": index["seconds"]}
    except Exception as error:
        progress.update(error_type=type(error).__name__, message=str(error),
                        seconds=time.monotonic()-started)
        raise
    finally:
        (directory/"progress.json").write_text(json.dumps(progress, indent=2)+"\n")
        print(json.dumps(progress, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--seconds", type=float, default=60)
    args = parser.parse_args()
    prepare(args.directory, args.seconds)
