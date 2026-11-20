"""Prepare small compatibility graphs for all retained F0 exterior-edge orbits.

Only existing literal zero, prism and common-neighbor restrictions are used.
This module does not compute a maximum clique or call an optimizer. A later
bounded certificate census may turn these graphs into edge-count bounds.
"""
import argparse
from collections import Counter
import gzip
import hashlib
from itertools import combinations
import json
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "experiments/logs/root-prism-free"
INPUTS = {
    "domain": ("f0-boolean-fractional-model.json.gz", "703206929c9c85a40ac4ddcbfb1708c716c288482cf50c77a32249404e35b782"),
    "domains": ("f0-orbit-populations02-domains.json.gz", "4f079468530dba0746512cc4afce01666b2a63a2c8f35f66a4660a4fe3bab8ab"),
    "domain_cold": ("f0-orbit-populations02-independent-replay.json", "a8bb55cbf773ea75a8cd1d5a18b50281ecbe08f6074cea04fb2d75799138273a"),
    "moments": ("f0-second-moments-preparation02.json.gz", "404d91da35c798ba248887c22a7500957947e24b71d5197dc44432460e6d219e"),
    "moment_cold": ("f0-second-moments-preparation02-cold-replay.json", "e495dbc7281f420caab1f3be88e9263ab8273da6ae88a7ea4e1e72c30eaa1fcd"),
    "one_edge": ("f0-three-vertex-prism-cuts01.json.gz", "b445ad3268cb7016a7a5df07cef9c6fda1a0c7d96fa5a560f897c9449814b194"),
    "one_edge_cold": ("f0-three-vertex-prism-cuts01-replay.json", "342ea3bf2453c60b819ab66b0f63883bd3e4261730bba0fb8f06cf3a9e3ca5aa"),
    "one_edge_review": ("f0-three-vertex-prism-independent-source-review.json", "8465bbe9e202a036026533bf2c56e2e299efb60c9013a43b5061b013743828b6"),
    "path": ("f0-path-prism-cuts01.json.gz", "d7ce1862d52cb4c9011efe73deb438db2b4e33a3fade1d5b803569005f2d7886"),
    "path_cold": ("f0-path-prism-cuts01-replay.json", "690613ccd1fd9cdf6e7c67988d9d1fac50cd751793dec53ebbadf2c5337b038f"),
    "path_review": ("f0-path-prism-independent-source-review.json", "4471e71acaa8fbbd34ebf988e32da366d647c40ccb58ca17c3f63bc89f1c212c"),
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def tick(deadline):
    if time.monotonic() >= deadline:
        raise TimeoutError("bounded edge-orbit compatibility preparation")


def pair_id(a, b):
    a, b = sorted((a, b))
    assert 0 <= a < b < 480
    return a * (959-a) // 2 + b-a-1


def read_inputs(deadline):
    data = {}
    for name, (filename, expected) in INPUTS.items():
        tick(deadline)
        raw = (BASE / filename).read_bytes()
        assert sha(raw) == expected, name
        loaded = json.loads(gzip.decompress(raw) if filename.endswith(".gz") else raw)
        if name == "domain":
            loaded = loaded["validation"]
        elif name == "moments":
            loaded = {k: loaded[k] for k in ("pair_to_orbit", "pair_orbits", "zero_pair_orbits",
                                            "zero_moment_certificates", "original_selector_equalities")}
        elif name == "one_edge":
            loaded = {k: loaded[k] for k in ("source_sha256", "literal_prism_witnesses")}
        elif name == "path":
            loaded = {k: loaded[k] for k in ("source_sha256", "literal_witness_fields", "literal_witnesses")}
        if name.endswith(("cold", "review")):
            assert loaded["status"].startswith("PASS"), name
        data[name] = loaded
    for name in ("one_edge", "path"):
        assert data[name+"_cold"]["record_file_sha256"] == INPUTS[name][1]
        assert data[name+"_cold"]["source_sha256"] == data[name]["source_sha256"]
    assert data["moment_cold"]["artifact_sha256"] == INPUTS["moments"][1]
    return data


def prepare(data, deadline):
    domain, domains, moments = [data[k] for k in ("domain", "domains", "moments")]
    core, triples, edges, targets = [domain[k] for k in ("core", "triples", "edges", "targets")]
    assert len(core) == 21 and len(triples) == 480 and len(edges) == 68394
    assert len(domain["edge_orbits"]) == 5805
    assert domain["selector_orbits"] == domains["selector_orbits"]
    expected_targets = [[2-int(j in h)-sum((core[j+3] >> (k+3)) & 1 for k in h)
                         for j in range(18)] for h in triples]
    assert expected_targets == targets
    assert all(len(h) == 3 and h == sorted(set(h)) for h in triples)
    old_to_new = {old: new for new, old in enumerate(domains["new15038_to_original15589"])}
    zero_y = set(domains["original_Y_zero_columns"])
    zero_z = {old-5847 for old in domains["original_Z_zero_columns"]}
    assert len(zero_y) == 162 and zero_z == set(moments["zero_pair_orbits"])
    pmap = moments["pair_to_orbit"]
    zero_literal, zero_kinds = {}, Counter()
    for proof_id, proof in enumerate(moments["zero_moment_certificates"]):
        a, b = proof["anchor"], proof["other"]
        k = pair_id(a, b)
        assert k == proof["pair_id"] and pmap[k] in zero_z
        zero_kinds[proof["kind"]] += 1
        if proof["kind"] == "quota-one nonnegative lifted equality":
            row_id = proof["selector_Gram_row"]
            row = moments["original_selector_equalities"][row_id]
            assert row["family"] == "Gram" and row["quota"] == 1
            assert a in row["support"] and b in row["support"]
            premise = ["original_quota_one_Gram_row", row_id]
        else:
            assert proof["kind"] == "certified binary motif times selector"
            assert proof["literal_polynomial"] == "z_a*(z_a+z_b-1)=z_a*z_b"
            premise = ["previously_cold_checked_binary_motif_zero", proof_id]
        assert k not in zero_literal
        zero_literal[k] = [k, pmap[k], premise]
    assert len(zero_literal) == 4410
    assert zero_kinds == {"quota-one nonnegative lifted equality": 4320,
                          "certified binary motif times selector": 90}
    assert set(zero_literal) == {k for k, po in enumerate(pmap) if po in zero_z}

    one_edge = {}
    for wi, witness in enumerate(data["one_edge"]["literal_prism_witnesses"]):
        ei, c = witness["edge_id"], witness["third_selector"]
        assert edges[ei] == witness["exterior_edge"] and c not in edges[ei]
        key = (ei, c)
        assert key not in one_edge
        one_edge[key] = wi
    assert len(one_edge) == 9360
    assert data["path"]["literal_witness_fields"] == [
        "a", "b", "c", "x", "y", "z", "edge_ab_id", "edge_bc_id", "disposition",
        "path_id", "row_id", "quota_one_site", "known_zero_edge_id"]
    path = {}
    for wi, witness in enumerate(data["path"]["literal_witnesses"]):
        a, b, c = witness[:3]
        ei, ej = witness[6:8]
        assert edges[ei] == sorted((a, b)) and edges[ej] == sorted((b, c))
        assert ei != ej
        path.setdefault(tuple(sorted((ei, ej))), wi)
    assert len(data["path"]["literal_witnesses"]) == 107520 and len(path) == 107418

    def first_zero(selected):
        for a, b in combinations(sorted(set(selected)), 2):
            key = pair_id(a, b)
            if key in zero_literal:
                return ["selector_zero", *zero_literal[key]]
        return None

    def conflict(ei, ej):
        a, b = edges[ei]
        c, d = edges[ej]
        reason = first_zero((a, b, c, d))
        if reason is not None:
            return reason
        for edge, candidates in ((ei, (c, d)), (ej, (a, b))):
            for third in candidates:
                if (edge, third) in one_edge:
                    return ["one_edge_prism", one_edge[edge, third]]
        key = tuple(sorted((ei, ej)))
        if key in path:
            return ["two_edge_prism", path[key]]
        common = sorted(set((a, b)).intersection((c, d)))
        assert len(common) <= 1
        if common:
            center = common[0]
            left = a if b == center else b
            right = c if d == center else d
            shared_core = sorted(set(triples[left]).intersection(triples[right]))
            if len(shared_core) >= 2:
                return ["three_common_neighbors", center, left, right, *shared_core[:2]]
            for site in shared_core:
                assert targets[center][site] >= 1
                if targets[center][site] == 1:
                    return ["mixed_quota_one", center, site, left, right]
        return None

    actions = domains["signature_actions"]
    assert len(actions) == 12 and all(sorted(g) == list(range(480)) for g in actions)
    records, dispositions = [], Counter()
    proof_counts, graph_sizes, anchor_degrees = Counter(), Counter(), Counter()
    transport_checks = 0
    for oi, members in enumerate(domain["edge_orbits"]):
        if oi % 32 == 0:
            tick(deadline)
        old_y = 42+oi
        assert 1 <= len(members) <= 12 and members == sorted(set(members))
        po = domains["edge_orbit_pair_orbits"][oi]
        assert {pair_id(*edges[e]) for e in members} == set(moments["pair_orbits"][po])
        if old_y in zero_y:
            dispositions["prior_Y_zero_orbit"] += 1
            continue
        assert old_y in old_to_new
        vertices = [edges[e] for e in members]
        local = {tuple(e): j for j, e in enumerate(vertices)}
        assert len(local) == len(vertices)
        permutations = [[local[tuple(sorted((g[a], g[b])))] for a, b in vertices] for g in actions]
        assert all(sorted(p) == list(range(len(vertices))) for p in permutations)
        assert set(p[0] for p in permutations) == set(range(len(vertices)))
        unary = [first_zero(e) for e in vertices]
        assert all(u is None for u in unary) or all(u is not None for u in unary)
        if unary[0] is not None:
            dispositions["Y_zero_from_selector_pair_zero"] += 1
            records.append({"edge_orbit": oi, "original_Y_column": old_y,
                            "reduced_count_column": old_to_new[old_y], "pair_orbit": po,
                            "literal_edge_ids": members, "unary_zero_proofs": unary,
                            "proved_count_upper_bound": 0, "clique_search_required": False})
            continue
        n = len(members)
        adjacency = [0]*n
        excluded = []
        for i, j in combinations(range(n), 2):
            reason = conflict(members[i], members[j])
            if reason is None:
                adjacency[i] |= 1 << j
                adjacency[j] |= 1 << i
            else:
                excluded.append([i, j, reason])
                proof_counts[reason[0]] += 1
        for permutation in permutations:
            for i, mask in enumerate(adjacency):
                image = sum(1 << permutation[j] for j in range(n) if mask >> j & 1)
                assert image == adjacency[permutation[i]]
                transport_checks += 1
        assert all(not (adjacency[i] >> i & 1) for i in range(n))
        assert sum(m.bit_count() for m in adjacency)//2 + len(excluded) == n*(n-1)//2
        graph_sizes[n] += 1
        degree = adjacency[0].bit_count()
        anchor_degrees[degree] += 1
        dispositions["retained_compatibility_graph"] += 1
        records.append({"edge_orbit": oi, "original_Y_column": old_y,
                        "reduced_count_column": old_to_new[old_y], "pair_orbit": po,
                        "corresponding_reduced_pair_count_column": old_to_new.get(5847+po),
                        "literal_edge_ids": members, "literal_edges": vertices,
                        "raw_count_upper_bound": len(members), "adjacency_masks": adjacency,
                        "nonedge_proofs": excluded, "actual_action_permutations": permutations,
                        "anchor": 0, "anchor_neighbors": [j for j in range(n) if adjacency[0] >> j & 1],
                        "maximum_anchor_subsets_for_future_exact_census": 1 << degree,
                        "clique_search_required": True})
    assert sum(dispositions.values()) == 5805 and len(records) == 5805-162
    tick(deadline)
    return {"schema": "conway99.f0-edge-orbit-packing-preparation.v1",
            "status": "PREPARED_COMPLETE_RETAINED_EDGE_ORBIT_GRAPHS_NO_CLIQUE_CENSUS",
            "source_sha256": sha(Path(__file__).read_bytes()),
            "inputs": {k: {"path": "experiments/logs/root-prism-free/"+f, "sha256": h} for k, (f, h) in INPUTS.items()},
            "records": records, "dispositions": dict(dispositions),
            "nonedge_reason_counts": dict(proof_counts), "graph_size_histogram": dict(graph_sizes),
            "anchor_degree_histogram": dict(anchor_degrees), "action_vertex_checks": transport_checks,
            "worst_future_anchor_subset_cases": sum(r.get("maximum_anchor_subsets_for_future_exact_census", 0) for r in records),
            "literal_zero_Gram_witnesses_checked": 4320,
            "prior_cold_checked_binary_motif_zero_premises_bound": 90,
            "prior_one_edge_prism_witnesses_bound": 9360, "prior_two_edge_prism_witnesses_bound": 107520,
            "maximum_clique_computations": 0, "optimizer_calls": 0,
            "new_motif_census_performed": False, "candidate_point_loaded": False,
            "proof": "Every selected exterior edge activates both endpoints. Every recorded incompatibility follows from an original quota-one selector pair, a previously cold-checked binary motif zero, a previously checked literal prism, three common neighbors, or an original mixed quota of one. Thus the selected edges in each orbit form a clique in its finite compatibility graph. Actual core actions make that finite graph vertex-transitive, so its clique number equals one plus the clique number of the anchor neighborhood. No automorphism of a hypothetical graph is assumed.",
            "scope": "Preparation for necessary exterior-edge count bounds in the fixed F0 conditional model. All5643 retained Y orbits are included. A later exact clique census is separate; no new positive count bound or global exclusion is claimed here."}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    started = time.monotonic()
    result = prepare(read_inputs(started+60), started+60)
    raw = gzip.compress(canonical(result)+b"\n", mtime=0)
    with args.output.open("xb") as stream:
        stream.write(raw)
    print(json.dumps({"status": result["status"], "sha256": sha(raw), "bytes": len(raw),
                      "dispositions": result["dispositions"], "nonedge_reason_counts": result["nonedge_reason_counts"],
                      "worst_future_anchor_subset_cases": result["worst_future_anchor_subset_cases"],
                      "seconds": time.monotonic()-started}, indent=2))
