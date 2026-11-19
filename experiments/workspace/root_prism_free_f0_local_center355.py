"""Complete local Boolean neighbor model for F0 center signature 355.

This is one necessary projection. The 218 neighbor bits remain distinct,
including two bits whose averaged edge coordinates coincide. Preparation
builds the CNF and runs only synthetic cardinality controls, not this model.
"""
import argparse
from collections import Counter
import gzip
import hashlib
from itertools import combinations, product
import json
from pathlib import Path
import time

import pysat
from pysat.card import CardEnc, EncType
from pysat.formula import IDPool
from pysat.solvers import Glucose4

ROOT = Path(__file__).resolve().parents[2]
BASE = "experiments/logs/root-prism-free/"
CENTER = 355
INPUTS = {
    "domain": (BASE+"f0-boolean-fractional-model.json.gz",
               "703206929c9c85a40ac4ddcbfb1708c716c288482cf50c77a32249404e35b782"),
    "edge_zeros": (BASE+"f0-edge-motif-census01.json.gz",
                   "397e8bf110e03a5accb5e6c1f27b2fb5525100acb67427c66669e188e74159d1"),
    "paths": (BASE+"f0-path-prism-cuts01.json.gz",
              "d7ce1862d52cb4c9011efe73deb438db2b4e33a3fade1d5b803569005f2d7886"),
    "inventory": (BASE+"f0-local-conflict-inventory01.json.gz",
                  "cbfdad339ab84cb7eeb6b221e10be3c4c1db4fb70932de3a28e62ee4642cb7e0"),
    "inventory_preparation": (BASE+"f0-local-conflict-inventory01-model-preparation.json",
                              "a1cd24f263b9712aeb7f4ecb1b69467f698c83527199c4fc063a3c63ccee5406"),
    "complete_replay": (BASE+"f0-local-conflict-inventory01-suffix-replay.json",
                        "ae85e2c9cbe19b72ad23231c6ee28ac135098eb078088780d4bd0988bd28cb5e"),
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def mask(sites):
    return sum(1 << i for i in sites)


def literal_path_proof(core, triples, witness):
    a, b, c, x, y, z = witness[:6]
    assert b == CENTER and len({a, b, c}) == len({x, y, z}) == 3
    rows = core[:]+[0, 0, 0]
    for v, sid in ((21, a), (22, b), (23, c)):
        for i in triples[sid]:
            rows[v] |= 1 << (i+3)
            rows[i+3] |= 1 << v
    for v, w in ((21, 22), (22, 23)):
        rows[v] |= 1 << w
        rows[w] |= 1 << v
    sites = [21, 22, x+3, 23, y+3, z+3]
    induced = [sum(((rows[v] >> w) & 1) << j for j, w in enumerate(sites))
               for v in sites]
    assert induced == [38, 13, 19, 50, 44, 25]
    assert (rows[21] & rows[23]).bit_count() >= 2
    return sorted((a, c))


def load_instance():
    loaded = {}
    for name, (path, digest) in INPUTS.items():
        raw = (ROOT/path).read_bytes()
        assert sha(raw) == digest
        loaded[name] = json.loads(gzip.decompress(raw) if path.endswith(".gz") else raw)
    data = loaded["domain"]["validation"]
    core, triples, edges = data["core"], data["triples"], data["edges"]
    record = next(r for r in loaded["inventory"]["representative_records"] if r["center"] == CENTER)
    assert record["literal_neighbor_variables_untied"] and record["center_is_conditioned_selected"]
    assert loaded["complete_replay"]["complete_centers"] == 42
    assert loaded["complete_replay"]["production_record_raw_sha256"] == sha(canonical(loaded["inventory"]))
    assert loaded["complete_replay"]["status"].startswith("PASS:")
    assert len(core) == 21 and len(triples) == 480 and len(edges) == 68394
    assert triples[CENTER] == [6, 11, 13]
    ymap = {e: 42+o for o, orbit in enumerate(data["edge_orbits"]) for e in orbit}
    zeros = set(loaded["edge_zeros"]["forced_zero_original_Y_variables"])
    live = sorted((c if a == CENTER else a, ei) for ei, (a, c) in enumerate(edges)
                  if CENTER in (a, c) and ymap[ei] not in zeros)
    neighbors = [a for a, _ in live]
    edge_ids = [e for _, e in live]
    assert neighbors == record["neighbor_ids"] and edge_ids == record["neighbor_edge_ids"]
    assert len(neighbors) == len(set(neighbors)) == 218 and CENTER not in neighbors
    quotient = [ymap[e] for e in edge_ids]
    assert quotient == record["neighbor_quotient_Y_columns"] and len(set(quotient)) == 217
    component = [row >> 3 for row in core[3:]]
    target = [2-int(i in triples[CENTER])-sum((component[i] >> j) & 1 for j in triples[CENTER])
              for i in range(18)]
    assert target == record["mixed_quotas"] == data["targets"][CENTER]
    assert sum(target) == 24 and all(q in (0, 1, 2) for q in target)
    rows = [{"component_site": i, "variables": [k+1 for k, a in enumerate(neighbors) if i in triples[a]],
             "demand": target[i]} for i in range(18)]
    assert sum(len(r["variables"]) for r in rows) == 3*218
    assert all(len(triples[a]) == 3 for a in neighbors)
    assert record["degree_from_quotas"] == 8
    path_pairs, path_proofs = set(), []
    for pi in record["published_path_pair_ids"]:
        p = loaded["paths"]["paths"][pi]
        assert p[0] == CENTER and p[5] == 2
        witness = loaded["paths"]["literal_witnesses"][p[3]]
        assert literal_path_proof(core, triples, witness) == p[1:3]
        assert (p[1], p[2]) not in path_pairs
        path_pairs.add((p[1], p[2]))
        path_proofs.append([pi, p[3], p[6]])
    motifs = set(map(tuple, data["motif_pairs"]))
    assert len(motifs) == 90
    adj = {a: int(bits, 16) for a, bits in zip(neighbors, record["full_conflict_adjacency_hex"])}
    quota_one = mask(i for i, q in enumerate(target) if q == 1)
    h = {a: mask(triples[a]) for a in neighbors}
    conflicts, reasons = [], Counter()
    for ia, ic in combinations(range(218), 2):
        a, c = neighbors[ia], neighbors[ic]
        common = h[a] & h[c]
        reason = ("mixed quota one" if common & quota_one else
                  "two common core sites" if common.bit_count() >= 2 else
                  "literal path prism" if (a, c) in path_pairs else
                  "certified selector motif" if (a, c) in motifs else None)
        assert bool((adj[a] >> c) & 1) == bool((adj[c] >> a) & 1) == (reason is not None)
        if reason is not None:
            conflicts.append([ia+1, ic+1])
            reasons[reason] += 1
    assert len(conflicts) == 5495
    universe = mask(neighbors)
    assert all(((adj[a] >> a) & 1) == 0 and (adj[a] & ~universe) == 0 for a in neighbors)
    center_orbit = data["selector_orbits"][record["orbit_id"]]
    assert center_orbit == record["center_orbit"] and len(center_orbit) == 12
    transports = [r for r in loaded["inventory_preparation"]["center_transports"] if r[0] in center_orbit]
    assert len(transports) == 12 and all(r[2] == CENTER for r in transports)
    instance = {
        "schema": "conway99.f0-local-center355-native-model.v1", "center": CENTER,
        "center_signature": triples[CENTER], "center_selector_orbit": center_orbit,
        "center_transports": transports, "center_is_selected": True,
        "neighbors": neighbors, "neighbor_signatures": [triples[a] for a in neighbors],
        "neighbor_edge_ids": edge_ids, "neighbor_quotient_Y_columns": quotient,
        "primitive_variables": 218, "primitive_bits_are_distinct": True,
        "quotient_equalities_imposed": 0, "mixed_rows": rows,
        "population_row": {"variables": list(range(1, 219)), "demand": 8},
        "population_is_redundant_by_three_times_sum": True,
        "conflicts": conflicts, "conflict_provenance_counts": dict(reasons),
        "literal_path_proof_references": path_proofs,
        "all218_candidates_retained": True, "all5495_conflicts_retained": True,
        "other_component_and_alignment_free": True,
        "global_selector_population_or_Gram_system_added": False,
        "neighbors_mutual_matching_added": False,
        "scope": "Necessary local eight-neighbor projection only. SAT is not a graph completion.",
    }
    return instance, core


def encode(n, mixed_rows, conflicts, population=None):
    pool = IDPool(start_from=n+1)
    clauses = []
    assert conflicts == sorted(conflicts) and len({tuple(p) for p in conflicts}) == len(conflicts)
    for a, c in conflicts:
        assert 1 <= a < c <= n
        clauses.append([-a, -c])
    rows = mixed_rows + ([] if population is None else [population])
    count_sizes = []
    for row in rows:
        literals, demand = row["variables"], row["demand"]
        assert literals == sorted(set(literals)) and all(1 <= v <= n for v in literals)
        assert type(demand) is int and 0 <= demand <= len(literals)
        cnf = CardEnc.equals(lits=literals, bound=demand, vpool=pool, encoding=EncType.seqcounter)
        assert all(all(type(lit) is int and lit and abs(lit) <= max(pool.top, n) for lit in c) for c in cnf.clauses)
        clauses.extend(cnf.clauses)
        count_sizes.append({"support": len(literals), "demand": demand, "clauses": len(cnf.clauses)})
    variables = max(n, pool.top)
    assert all(abs(lit) <= variables for c in clauses for lit in c)
    return clauses, variables, count_sizes


def dimacs(clauses, variables):
    return ("p cnf "+str(variables)+" "+str(len(clauses))+"\n"+
            "".join(" ".join(map(str, row))+" 0\n" for row in clauses)).encode()


def controls():
    equality_cases = equality_solves = 0
    domains = [(n, q) for n in range(7) for q in range(n+1)]+[(10, 2), (10, 8)]
    for n, q in domains:
        row = {"variables": list(range(1, n+1)), "demand": q}
        clauses, variables, _ = encode(n, [row], [])
        assert variables >= n
        with Glucose4(bootstrap_with=clauses) as solver:
            for bits in product((0, 1), repeat=n):
                assumptions = [i+1 if bit else -(i+1) for i, bit in enumerate(bits)]
                assert bool(solver.solve(assumptions=assumptions)) == (sum(bits) == q)
                equality_solves += 1
        equality_cases += 1
    pair_cases = 0
    pairs = list(combinations(range(1, 5), 2))
    for edge_mask in range(1 << len(pairs)):
        conflicts = [list(p) for k, p in enumerate(pairs) if (edge_mask >> k) & 1]
        clauses, _, _ = encode(4, [], conflicts)
        for bits in product((0, 1), repeat=4):
            native = all(not(bits[a-1] and bits[c-1]) for a, c in conflicts)
            encoded = all(any(bits[abs(lit)-1] == (lit > 0) for lit in clause) for clause in clauses)
            assert native == encoded
            pair_cases += 1
    signatures = [(0,1,2),(3,4,5),(6,7,8),(9,10,11),(12,13,14),(15,16,17),
                  (0,3,6),(9,12,15),(1,4,7),(2,5,8),(10,13,16),(11,14,17)]
    selected = set(range(1, 9))
    toy_rows = [{"variables": [i+1 for i, h in enumerate(signatures) if v in h],
                 "demand": sum(v in signatures[i-1] for i in selected)} for v in range(18)]
    toy_pairs = [list(p) for p in combinations(range(1, 13), 2)
                 if not set(p) <= selected and sum(p) % 3 == 0]
    clauses, _, _ = encode(12, toy_rows, toy_pairs, {"variables": list(range(1, 13)), "demand": 8})
    with Glucose4(bootstrap_with=clauses) as solver:
        assert solver.solve(assumptions=[i if i in selected else -i for i in range(1, 13)])
    return {"cardinality_domains": equality_cases, "exhaustive_cardinality_assignment_queries": equality_solves,
            "four_variable_conflict_graph_assignment_checks": pair_cases,
            "known_eight_neighbor_eighteen_row_positive_control": True,
            "production_center355_queries": 0}


def inspect_witness(instance, core, selected):
    assert selected == sorted(set(selected)) and len(selected) == 8
    assert all(type(v) is int and 1 <= v <= 218 for v in selected)
    chosen = set(selected)
    observed = [sum(v in chosen for v in row["variables"]) for row in instance["mixed_rows"]]
    assert observed == [row["demand"] for row in instance["mixed_rows"]]
    assert all(not (a in chosen and c in chosen) for a, c in instance["conflicts"])
    assert sum(observed) == 24
    signatures = [instance["center_signature"]]+[instance["neighbor_signatures"][v-1] for v in selected]
    partial = core[:]+[0]*9
    for outside, h in enumerate(signatures, start=21):
        for i in h:
            partial[outside] |= 1 << (i+3)
            partial[i+3] |= 1 << outside
    for neighbor in range(22, 30):
        partial[21] |= 1 << neighbor
        partial[neighbor] |= 1 << 21
    assert partial[21].bit_count() == 11
    assert all((partial[i] & partial[j]).bit_count() <= 2-((partial[i] >> j) & 1)
               for i, j in combinations(range(30), 2))
    return {"status": "PASS: exact native local Boolean neighbor witness",
            "selected_primitive_variables": selected,
            "selected_neighbor_ids": [instance["neighbors"][v-1] for v in selected],
            "selected_neighbor_signatures": [instance["neighbor_signatures"][v-1] for v in selected],
            "all18_mixed_counts": observed, "exterior_neighbor_count": 8,
            "conflict_constraints_checked": 5495, "visible_partial_vertices": 30,
            "visible_common_neighbor_caps_checked": 435,
            "partial_adjacency_rows": partial, "global_graph_completion_claimed": False}


def build():
    instance, core = load_instance()
    clauses, variables, row_sizes = encode(218, instance["mixed_rows"], instance["conflicts"],
                                          instance["population_row"])
    raw = dimacs(clauses, variables)
    model = {"schema": "conway99.f0-local-center355-CNF.v1",
             "source_sha256": sha(Path(__file__).read_bytes()),
             "inputs": {k: {"path": p, "sha256": h} for k, (p, h) in INPUTS.items()},
             "pysat_version": pysat.__version__, "cardinality_encoding": "EncType.seqcounter",
             "native_instance_sha256": sha(canonical(instance)), "cnf_sha256": sha(raw),
             "primitive_variables": 218, "total_variables": variables,
             "auxiliary_variables": variables-218, "clauses": len(clauses), "cnf_bytes": len(raw),
             "binary_conflict_clauses": 5495, "count_rows": row_sizes,
             "center_selector_orbit": instance["center_selector_orbit"],
             "literal_to_quotient_map_is_metadata_only": True,
             "conditional_UNSAT_conclusion": "Only a checked UNSAT proof excludes the selected center and its twelve core relabelings.",
             "SAT_scope": "Eight local neighbors satisfying the recorded necessary constraints; no full incidence or graph completion."}
    return instance, core, clauses, variables, raw, model


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, required=True)
    args = parser.parse_args()
    assert not args.directory.exists()
    started = time.monotonic()
    instance, _, _, _, raw, model = build()
    tested = controls()
    args.directory.mkdir(parents=True)
    (args.directory/"instance.json").write_bytes(canonical(instance)+b"\n")
    (args.directory/"model.cnf").write_bytes(raw)
    (args.directory/"model.json").write_text(json.dumps(model, indent=2)+"\n")
    result = {"status": "PASS: complete center355 model preparation; no production query",
              "source_sha256": model["source_sha256"],
              "instance_file_sha256": sha((args.directory/"instance.json").read_bytes()),
              "model_file_sha256": sha((args.directory/"model.json").read_bytes()),
              "cnf_sha256": model["cnf_sha256"], "total_variables": model["total_variables"],
              "clauses": model["clauses"], "controls": tested,
              "production_queries": 0, "seconds": time.monotonic()-started}
    (args.directory/"preparation.json").write_text(json.dumps(result, indent=2)+"\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
