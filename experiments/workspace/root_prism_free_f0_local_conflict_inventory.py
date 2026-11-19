"""Bounded, point-independent local F0 neighbor-conflict inventory.

Only representative centers are quotiented. Every live neighbor remains a
distinct Boolean variable. No clique search, odd-cycle search, local
feasibility solve, fractional point, or optimizer is used.
"""
import argparse
from collections import Counter
import gzip
import hashlib
from itertools import combinations, product
import json
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[2]
BASE = "experiments/logs/root-prism-free/"
INPUTS = {
    "domain": (BASE+"f0-boolean-fractional-model.json.gz",
               "703206929c9c85a40ac4ddcbfb1708c716c288482cf50c77a32249404e35b782"),
    "edge_zeros": (BASE+"f0-edge-motif-census01.json.gz",
                   "397e8bf110e03a5accb5e6c1f27b2fb5525100acb67427c66669e188e74159d1"),
    "moments": (BASE+"f0-second-moments-preparation02.json.gz",
                "404d91da35c798ba248887c22a7500957947e24b71d5197dc44432460e6d219e"),
    "paths": (BASE+"f0-path-prism-cuts01.json.gz",
              "d7ce1862d52cb4c9011efe73deb438db2b4e33a3fade1d5b803569005f2d7886"),
    "core_cliques": (BASE+"f0-core-pair-edge-cliques01.json.gz",
                     "728f3de4ed0febf90f4062820b5a58c8e31335ebc7e65d354872c7bc8d38370e"),
}
N = 480
QUOTA_ZERO_KIND = "quota-one nonnegative lifted equality"
MOTIF_ZERO_KIND = "certified binary motif times selector"
LAYER_NAMES = ("base_mixed_and_lifted_Gram",
               "plus_published_core_pair_cliques",
               "plus_published_path_prisms",
               "plus_semantic_selector_motif_conflicts")


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def members(bits):
    while bits:
        low = bits & -bits
        yield low.bit_length()-1
        bits -= low


def bitset(values):
    result = 0
    for value in values:
        assert not (result >> value) & 1
        result |= 1 << value
    return result


def pair_id(a, b):
    assert 0 <= a < b < N
    return a*(2*N-a-1)//2+b-a-1


def tick(deadline, stage):
    if deadline is not None and time.monotonic() >= deadline:
        raise TimeoutError("bounded local-conflict inventory: "+stage)


def graph(vertices, pairs=(), cliques=()):
    adjacency = [0]*N
    universe = bitset(vertices)
    for clique in cliques:
        assert clique & ~universe == 0
        for a in members(clique):
            adjacency[a] |= clique ^ (1 << a)
    for a, c in pairs:
        assert a != c and (universe >> a) & 1 and (universe >> c) & 1
        adjacency[a] |= 1 << c
        adjacency[c] |= 1 << a
    return adjacency


def union(*graphs):
    result = [0]*N
    for adjacency in graphs:
        for a, row in enumerate(adjacency):
            result[a] |= row
    return result


def edge_count(adjacency):
    count = sum(row.bit_count() for row in adjacency)
    assert count % 2 == 0
    return count//2


def triangle_count(adjacency, vertices, deadline=None):
    total = 0
    for index, a in enumerate(vertices):
        if index % 64 == 0:
            tick(deadline, "triangle counts")
        above_a = adjacency[a] >> (a+1) << (a+1)
        for c in members(above_a):
            common_above_c = (adjacency[a] & adjacency[c]) >> (c+1)
            total += common_above_c.bit_count()
    return total


def degeneracy(adjacency, vertices, deadline=None):
    remaining = set(vertices)
    degree = {a: adjacency[a].bit_count() for a in vertices}
    maximum = 0
    order = []
    while remaining:
        if len(order) % 32 == 0:
            tick(deadline, "degeneracy")
        a = min(remaining, key=lambda x: (degree[x], x))
        maximum = max(maximum, degree[a])
        order.append([a, degree[a]])
        remaining.remove(a)
        for c in members(adjacency[a]):
            if c in remaining:
                degree[c] -= 1
    return maximum, order


def controls():
    checked = 0
    pairs = list(combinations(range(5), 2))
    for bits in range(1 << len(pairs)):
        edges = [pair for i, pair in enumerate(pairs) if (bits >> i) & 1]
        adjacency = graph(range(5), edges)
        assert edge_count(adjacency) == len(edges)
        direct_triangles = sum(all((adjacency[a] >> c) & 1
                                   for a, c in combinations(triple, 2))
                               for triple in combinations(range(5), 3))
        assert triangle_count(adjacency, list(range(5))) == direct_triangles
        direct_degeneracy = max(min((adjacency[a] & subset).bit_count()
                                    for a in members(subset))
                                for subset in range(1, 1 << 5))
        assert degeneracy(adjacency, list(range(5)))[0] == direct_degeneracy
        checked += 1
    activation = 0
    for xa, xb, xc, yab, ybc in product((0, 1), repeat=5):
        if yab > min(xa, xb) or ybc > min(xb, xc) or xa*xc:
            continue
        assert yab+ybc <= xb
        activation += 1
    # Scaled by two. Activation, pair-moment Frechet bounds and Z_ac=0
    # alone do not imply the homogeneous edge conflict.
    x = [1, 1, 1]
    z = {(0, 1): 1, (1, 2): 1, (0, 2): 0}
    assert all(max(0, x[a]+x[c]-2) <= value <= min(x[a], x[c])
               for (a, c), value in z.items())
    assert z[0, 1]+z[1, 2] > x[1]
    return {"all_five_vertex_graphs": checked,
            "direct_edge_triangle_and_degeneracy_comparisons": 3*checked,
            "selector_conflict_activation_controls": activation,
            "fractional_pair_bounds_alone_counterexample_denominator": 2}


def load(deadline=None):
    loaded = {}
    for name, (path, digest) in INPUTS.items():
        tick(deadline, "input "+name)
        raw = (ROOT/path).read_bytes()
        assert sha(raw) == digest, path
        loaded[name] = json.loads(gzip.decompress(raw))
    data = loaded["domain"]["validation"]
    core, triples, edges, targets = (data[k] for k in ("core", "triples", "edges", "targets"))
    assert len(core) == 21 and len(triples) == N and len(edges) == 68394
    assert len(set(map(tuple, triples))) == N
    assert all(h == sorted(set(h)) and len(h) == 3 and 0 <= min(h) <= max(h) < 18
               for h in triples)
    masks = [bitset(h) for h in triples]
    assert all(((core[i] >> j) & 1) == ((core[j] >> i) & 1)
               for i in range(21) for j in range(21))
    component = [row >> 3 for row in core[3:]]
    assert all(row.bit_count() == 3 for row in component)
    expected_targets = [[2-int(i in h)-sum((component[i] >> j) & 1 for j in h)
                         for i in range(18)] for h in triples]
    assert targets == expected_targets
    assert all(sum(row) == 24 and all(q in (0, 1, 2) for q in row) for row in targets)
    xmap = {a: o for o, orbit in enumerate(data["selector_orbits"]) for a in orbit}
    ymap = {e: 42+o for o, orbit in enumerate(data["edge_orbits"]) for e in orbit}
    assert len(xmap) == N and len(data["selector_orbits"]) == 42
    assert len(ymap) == len(edges) and len(data["edge_orbits"]) == 5805
    zeros = set(loaded["edge_zeros"]["forced_zero_original_Y_variables"])
    assert len(zeros) == 162
    edge_lookup = {tuple(edge): i for i, edge in enumerate(edges)}
    assert len(edge_lookup) == len(edges) and edges == sorted(edges)
    raw_neighbors, live = [0]*N, [0]*N
    for e, (a, b) in enumerate(edges):
        assert 0 <= a < b < N and (masks[a] & masks[b]).bit_count() <= 1
        assert all(targets[a][i] > 0 for i in triples[b])
        assert all(targets[b][i] > 0 for i in triples[a])
        raw_neighbors[a] |= 1 << b
        raw_neighbors[b] |= 1 << a
        if ymap[e] not in zeros:
            live[a] |= 1 << b
            live[b] |= 1 << a
    assert sum(row.bit_count() for row in live) == 2*(68394-1884)
    moments, path, clique = loaded["moments"], loaded["paths"], loaded["core_cliques"]
    gram = moments["original_selector_equalities"]
    assert len(gram) == 172 and gram[-1]["quota"] == 60
    for rid, ((i, j), row) in enumerate(zip(((i, j) for i in range(18) for j in range(i, 18)),
                                          gram[:-1])):
        quota = (14-core[i+3].bit_count() if i == j else
                 2-((core[i+3] >> (j+3)) & 1)-(core[i+3] & core[j+3]).bit_count())
        assert row["family"] == "Gram" and row["core_pair"] == [i, j]
        assert row["quota"] == quota
        assert row["support"] == [a for a, h in enumerate(triples) if i in h and j in h]
    assert gram[-1]["support"] == list(range(N))
    quota_rows = [(rid, bitset(row["support"])) for rid, row in enumerate(gram[:-1])
                  if row["quota"] == 1]
    zero_certificates = moments["zero_moment_certificates"]
    quota_pairs, motif_pairs = {}, {}
    for ci, cert in enumerate(zero_certificates):
        a, c = cert["anchor"], cert["other"]
        assert cert["pair_id"] == pair_id(a, c)
        if cert["kind"] == QUOTA_ZERO_KIND:
            rid = cert["selector_Gram_row"]
            assert gram[rid]["quota"] == 1
            assert a in gram[rid]["support"] and c in gram[rid]["support"]
            assert cert["full_RLT_row"] == 172*a+rid
            assert (a, c) not in quota_pairs
            quota_pairs[a, c] = ci
        else:
            assert cert["kind"] == MOTIF_ZERO_KIND and (a, c) not in motif_pairs
            motif_pairs[a, c] = ci
    assert len(quota_pairs) == 4320 and len(motif_pairs) == 90
    assert set(quota_pairs) == {pair for _, support in quota_rows
                                for pair in combinations(members(support), 2)}
    assert set(motif_pairs) == set(map(tuple, data["motif_pairs"]))
    assert not (set(quota_pairs) & set(motif_pairs))
    actions = path["actual_core_action_verification"]["selector_actions"]
    core_actions = path["actual_core_action_verification"]["core_actions"]
    assert actions == moments["selector_actions"] and len(actions) == len(core_actions) == 12
    group_index = {tuple(move): k for k, move in enumerate(core_actions)}
    assert len(group_index) == 12 and tuple(range(21)) in group_index
    for move, g in zip(core_actions, actions):
        assert sorted(move) == list(range(21)) and set(move[:3]) == {0, 1, 2}
        assert sorted(g) == list(range(N))
        assert all(((core[i] >> j) & 1) == ((core[move[i]] >> move[j]) & 1)
                   for i in range(21) for j in range(21))
        assert all(sorted(move[i+3]-3 for i in h) == triples[g[a]]
                   for a, h in enumerate(triples))
        assert all(targets[g[a]][move[i+3]-3] == targets[a][i]
                   for a in range(N) for i in range(18))
        for pair_set in (quota_pairs, motif_pairs):
            assert {tuple(sorted((g[a], g[c]))) for a, c in pair_set} == set(pair_set)
    for left, g in zip(core_actions, actions):
        for right, h in zip(core_actions, actions):
            k = group_index[tuple(left[right[i]] for i in range(21))]
            assert all(actions[k][a] == g[h[a]] for a in range(N))
    center_transports = []
    for orbit_id, orbit in enumerate(data["selector_orbits"]):
        rep = min(orbit)
        assert sorted({g[rep] for g in actions}) == orbit
        for g in actions:
            assert bitset(g[a] for a in members(live[rep])) == live[g[rep]]
            assert bitset(g[a] for a in members(raw_neighbors[rep])) == raw_neighbors[g[rep]]
        for b in orbit:
            gi = next(i for i, g in enumerate(actions) if g[rep] == b)
            g = actions[gi]
            assert bitset(g[a] for a in members(live[rep])) == live[b]
            assert bitset(g[a] for a in members(raw_neighbors[rep])) == raw_neighbors[b]
            center_transports.append([b, orbit_id, rep, gi])
    center_transports.sort()
    assert [r[0] for r in center_transports] == list(range(N))
    # Check the saved full orbit transports, not a new prism census.
    retained_paths = {}
    by_center_paths = [[] for _ in range(N)]
    for pi, record in enumerate(path["paths"]):
        b, a, c = record[:3]
        if record[5] == 2:
            assert (b, a, c) not in retained_paths
            retained_paths[b, a, c] = pi
            by_center_paths[b].append(pi)
            assert (live[b] >> a) & 1 and (live[b] >> c) & 1 and a < c
    transported_paths = set()
    for rid, saved in enumerate(path["quotient_row_transport_witnesses"]):
        tick(deadline, "saved path transports")
        assert saved["row_id"] == rid
        first = path["literal_witnesses"][path["rows"][rid]["first_literal_witness"]]
        a, b, c, x, y, z = first[:6]
        assert [gi for gi, _ in saved["literal_witness_transports"]] == list(range(12))
        for gi, wi in saved["literal_witness_transports"]:
            g, move = actions[gi], core_actions[gi]
            witness = path["literal_witnesses"][wi]
            assert witness[:6] == [g[a], g[b], g[c], move[x+3]-3,
                                   move[y+3]-3, move[z+3]-3]
            assert witness[8] == 2 and witness[10] == rid
            key = (g[b], min(g[a], g[c]), max(g[a], g[c]))
            assert retained_paths[key] == witness[9]
            transported_paths.add(key)
    assert transported_paths == set(retained_paths) and len(retained_paths) == 61476
    # Recover the frozen clique buckets exclusively by their saved transports.
    by_center_cliques = [[] for _ in range(N)]
    seen_buckets = set()
    pair_index = {tuple(pair): i for i, pair in enumerate(clique["component_pairs"])}
    for rid, (row, transports) in enumerate(zip(clique["rows"], clique["row_transports"])):
        b, (i, j) = row["center"], row["core_pair"]
        assert [gi for gi, _ in transports] == list(range(12))
        for gi, ledger_index in transports:
            g, move = actions[gi], core_actions[gi]
            target_pair = tuple(sorted((move[i+3]-3, move[j+3]-3)))
            target_b = g[b]
            assert ledger_index == 153*target_b+pair_index[target_pair]
            ledger_row = clique["ledger"][ledger_index]
            assert ledger_row[0] == target_b and ledger_row[4:] == [4, rid]
            support = sorted(g[a] for a, _ in row["live_neighbors_and_edge_ids"])
            assert len(support) == ledger_row[3] and len(set(support)) == len(support)
            assert all((live[target_b] >> a) & 1 and all(v in triples[a] for v in target_pair)
                       for a in support)
            assert ledger_index not in seen_buckets
            seen_buckets.add(ledger_index)
            by_center_cliques[target_b].append(
                {"ledger_index": ledger_index, "row_id": rid, "action_id": gi,
                 "core_pair": list(target_pair), "neighbor_bits": bitset(support)})
    assert seen_buckets == {i for i, row in enumerate(clique["ledger"]) if row[4] == 4}
    assert len(seen_buckets) == 3096 and len(clique["rows"]) == 258
    site_bits = [bitset(a for a, h in enumerate(triples) if i in h) for i in range(18)]
    tick(deadline, "completed domain preparation")
    return {"data": data, "masks": masks, "raw_neighbors": raw_neighbors, "live": live,
            "xmap": xmap, "ymap": ymap, "edge_lookup": edge_lookup,
            "gram": gram, "quota_rows": quota_rows, "quota_pairs": quota_pairs,
            "motif_pairs": motif_pairs, "site_bits": site_bits,
            "path": path, "clique": clique, "by_center_paths": by_center_paths,
            "by_center_cliques": by_center_cliques,
            "center_transports": center_transports, "actions": actions,
            "core_actions": core_actions}


def preparation(data, proof_controls):
    d = data["data"]
    representatives = []
    for oi, orbit in enumerate(d["selector_orbits"]):
        b = min(orbit)
        vertices = list(members(data["live"][b]))
        representatives.append({"center": b, "orbit_id": oi, "orbit_size": len(orbit),
                                "live_neighbors": len(vertices), "mixed_quotas": d["targets"][b],
                                "local_degree": 8, "pair_bound": len(vertices)*(len(vertices)-1)//2,
                                "saved_retained_path_pairs": len(data["by_center_paths"][b]),
                                "saved_retained_core_pair_buckets": len(data["by_center_cliques"][b])})
    return {"schema": "conway99.f0-local-conflict-preparation.v1",
            "source_sha256": sha(Path(__file__).read_bytes()),
            "inputs": {k: {"path": p, "sha256": h} for k, (p, h) in INPUTS.items()},
            "controls": proof_controls, "representatives": representatives,
            "center_transports": data["center_transports"],
            "selector_actions": data["actions"], "core_actions": data["core_actions"],
            "coverage": {"centers": 480, "representatives": 42, "actual_core_actions": 12,
                         "live_eligible_edges": 66510, "distinct_literal_neighbors_untied": True,
                         "mixed_equations_per_center": 18, "target_sum": 24,
                         "neighbor_signature_weight": 3, "implied_local_degree": 8,
                         "frozen_path_pairs": 61476, "frozen_clique_buckets": 3096,
                         "quota_one_selector_zero_pairs": 4320, "motif_selector_zero_pairs": 90},
            "work_bounds": {"representative_neighbor_pair_bound": sum(r["pair_bound"] for r in representatives),
                            "representative_vertex_count": sum(r["live_neighbors"] for r in representatives),
                            "maximum_neighbors": max(r["live_neighbors"] for r in representatives),
                            "inventory_seconds": 10, "threads": 1},
            "layers": list(LAYER_NAMES),
            "scope": "Complete inventory of the listed conflict families only; no claim that they give every local obstruction.",
            "homogeneous_coverage_scope": "Recorded base implications and published rows; no assertion that every published row is installed in the latest numerical LP.",
            "semantic_motif_layer": "A missing homogeneous row is not inferred from Z_ac=0 and activation alone.",
            "point_loaded": False, "optimizer_calls": 0, "graph_inventory_executed": False,
            "maximal_clique_search": False, "odd_cycle_search": False, "local_feasibility_solve": False}


def graph_summary(adjacency, vertices, deadline):
    universe = bitset(vertices)
    assert all((row & ~universe) == 0 and not ((row >> a) & 1)
               for a, row in enumerate(adjacency))
    assert all((adjacency[c] >> a) & 1 for a in vertices for c in members(adjacency[a]))
    degrees = [adjacency[a].bit_count() for a in vertices]
    return {"vertices": len(vertices), "edges": edge_count(adjacency),
            "degree_histogram": {str(k): v for k, v in sorted(Counter(degrees).items())},
            "minimum_degree": min(degrees, default=0), "maximum_degree": max(degrees, default=0),
            "triangles": triangle_count(adjacency, vertices, deadline),
            "adjacency_sha256": sha(canonical([format(adjacency[a], "x") for a in vertices]))}


def center_inventory(data, b, deadline):
    d, universe = data["data"], data["live"][b]
    vertices = list(members(universe))
    mixed = [(i, universe & data["site_bits"][i]) for i, q in enumerate(d["targets"][b]) if q == 1]
    lifted = [(rid, universe & support) for rid, support in data["quota_rows"]]
    base = graph(vertices, cliques=[s for _, s in mixed+lifted])
    buckets = data["by_center_cliques"][b]
    clique_layer = graph(vertices, cliques=[r["neighbor_bits"] for r in buckets])
    after_clique = union(base, clique_layer)
    path_ids = data["by_center_paths"][b]
    path_pairs = [tuple(data["path"]["paths"][pi][1:3]) for pi in path_ids]
    path_layer = graph(vertices, pairs=path_pairs)
    after_path = union(after_clique, path_layer)
    motif_certificates = [(a, c, ci) for (a, c), ci in data["motif_pairs"].items()
                          if (universe >> a) & 1 and (universe >> c) & 1]
    motif_layer = graph(vertices, pairs=[(a, c) for a, c, _ in motif_certificates])
    complete = union(after_path, motif_layer)
    quota_pairs = [(a, c, ci) for (a, c), ci in data["quota_pairs"].items()
                   if (universe >> a) & 1 and (universe >> c) & 1]
    assert all((base[a] >> c) & 1 for a, c, _ in quota_pairs)
    summaries = [graph_summary(g, vertices, deadline) for g in (base, after_clique, after_path, complete)]
    assert all(summaries[i]["edges"] <= summaries[i+1]["edges"] and
               summaries[i]["triangles"] <= summaries[i+1]["triangles"] for i in range(3))
    deg, deletion = degeneracy(complete, vertices, deadline)
    # This is a count of triangles containing a newly added edge, not a
    # search for maximal cliques or a nonredundancy certificate for their rows.
    additions = [{"layer": LAYER_NAMES[i], "new_pairs": summaries[i]["edges"]-summaries[i-1]["edges"],
                  "triangles_with_a_new_pair": summaries[i]["triangles"]-summaries[i-1]["triangles"]}
                 for i in range(1, 4)]
    covered_paths = [sum((g[a] >> c) & 1 for a, c in path_pairs) for g in (base, after_clique)]
    covered_motifs = [sum((g[a] >> c) & 1 for a, c, _ in motif_certificates)
                      for g in (base, after_clique, after_path)]
    edge_ids = [data["edge_lookup"][tuple(sorted((a, b)))] for a in vertices]
    return {"center": b, "orbit_id": data["xmap"][b],
            "center_orbit": d["selector_orbits"][data["xmap"][b]],
            "neighbor_ids": vertices, "neighbor_edge_ids": edge_ids,
            "neighbor_quotient_Y_columns": [data["ymap"][e] for e in edge_ids],
            "literal_neighbor_variables_untied": True, "center_is_conditioned_selected": True,
            "mixed_quotas": d["targets"][b],
            "degree_from_quotas": 8,
            "mixed_quota_one_cliques": [[i, format(s, "x")] for i, s in mixed],
            "lifted_Gram_quota_one_cliques": [[i, format(s, "x")] for i, s in lifted],
            "published_core_pair_buckets": [{**r, "neighbor_bits": format(r["neighbor_bits"], "x")}
                                            for r in buckets],
            "published_path_pair_ids": path_ids,
            "semantic_motif_zero_certificates": [list(t) for t in motif_certificates],
            "quota_one_zero_pairs_already_covered": len(quota_pairs),
            "path_pairs_covered_by_base": covered_paths[0],
            "path_pairs_covered_after_core_cliques": covered_paths[1],
            "motif_pairs_covered_by_base": covered_motifs[0],
            "motif_pairs_covered_after_core_cliques": covered_motifs[1],
            "motif_pairs_covered_after_path_rows": covered_motifs[2],
            "layer_statistics": dict(zip(LAYER_NAMES, summaries)), "layer_additions": additions,
            "full_conflict_adjacency_hex": [format(complete[a], "x") for a in vertices],
            "full_graph_degeneracy": deg, "degeneracy_deletion_order": deletion,
            "new_triangles_are_not_asserted_linearly_independent": True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "inventory", "replay"))
    parser.add_argument("--preparation", type=Path, required=True)
    parser.add_argument("--record", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seconds", type=float, default=10)
    args = parser.parse_args()
    assert 0 < args.seconds <= 10 and not args.output.exists()
    if args.mode == "prepare":
        assert not args.preparation.exists()
    else:
        assert args.record is not None and (args.mode == "replay" or not args.record.exists())
    started = time.monotonic()
    completed = []
    report = {}
    try:
        # Preparation validates frozen ledgers but does not build a conflict
        # graph. The separate production budget includes input loading.
        deadline = None if args.mode == "prepare" else started+args.seconds
        data = load(deadline)
        proof_controls = controls()
        prep = preparation(data, proof_controls)
        if args.mode == "prepare":
            args.preparation.write_bytes(canonical(prep)+b"\n")
            report = {"status": "PASS: local-conflict source/domain preparation",
                      "preparation_sha256": sha(args.preparation.read_bytes()),
                      "source_sha256": prep["source_sha256"], "coverage": prep["coverage"],
                      "work_bounds": prep["work_bounds"], "controls": proof_controls,
                      "graph_inventory_executed": False, "point_loaded": False, "optimizer_calls": 0}
        else:
            assert prep == json.loads(args.preparation.read_bytes())
            for row in prep["representatives"]:
                tick(deadline, "next center")
                completed.append(center_inventory(data, row["center"], deadline))
            tick(deadline, "complete graph inventory")
            result = {"schema": "conway99.f0-local-conflict-inventory.v1",
                      "status": "COMPLETE_LISTED_LOCAL_CONFLICT_INVENTORY",
                      "source_sha256": prep["source_sha256"],
                      "preparation_sha256": sha(args.preparation.read_bytes()),
                      "inputs": prep["inputs"], "center_transports": prep["center_transports"],
                      "representative_records": completed, "complete_centers": 42,
                      "literal_centers_covered": 480,
                      "point_loaded": False, "optimizer_calls": 0,
                      "maximal_clique_search": False, "odd_cycle_search": False,
                      "local_feasibility_solve": False, "graph_existence_resolved": False,
                      "scope": prep["scope"], "homogeneous_coverage_scope": prep["homogeneous_coverage_scope"]}
            raw = canonical(result)
            if args.mode == "replay":
                assert canonical(json.loads(gzip.decompress(args.record.read_bytes()))) == raw
            else:
                args.record.write_bytes(gzip.compress(raw, mtime=0))
            report = {"status": "PASS: complete local-conflict "+args.mode,
                      "source_sha256": prep["source_sha256"], "record_sha256": sha(args.record.read_bytes()),
                      "record_raw_sha256": sha(raw), "representative_centers": len(completed),
                      "literal_centers_covered": 480, "point_loaded": False, "optimizer_calls": 0}
    except Exception as error:
        report = {"status": "INCOMPLETE_NO_COMPLETE_INVENTORY_CLAIM", "mode": args.mode,
                  "source_sha256": sha(Path(__file__).read_bytes()),
                  "error_type": type(error).__name__, "message": str(error),
                  "completed_center_records": completed, "point_loaded": False, "optimizer_calls": 0}
        if args.mode != "prepare" and args.mode != "replay" and args.record is not None:
            args.record.write_bytes(gzip.compress(canonical(report), mtime=0))
        report["seconds"] = time.monotonic()-started
        args.output.write_text(json.dumps(report, indent=2)+"\n")
        raise
    report["seconds"] = time.monotonic()-started
    args.output.write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
