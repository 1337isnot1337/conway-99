"""Exact exterior-edge orbit packing bounds and certificate replay.

The preparation independently checks each stored nonedge premise. A separate
bounded census uses the checked small-graph recurrence. Its cold replay does
not run a maximum-clique search or reconstruct any earlier motif census.
"""
import argparse
from collections import Counter
import gzip
import hashlib
from itertools import combinations
import json
from pathlib import Path
import time

import finite_graph_clique_certificate as clique
import root_prism_free_f0_edge_orbit_packing_preparation as graph_source

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "experiments/logs/root-prism-free"
HELPER_SHA = "ef97e243a4140ca741097cb8c237d080e926d5f47f2ccca01abc662ff042834b"
GRAPH_SOURCE_SHA = "e8aae22865dfaaffe043a76c872aaf1212c74a6bbb8b26301f6b61dcb541efe5"
INPUTS = {
    "graphs": ("f0-edge-orbit-packing-preparation01.json.gz", "2d581d92545eb1d8718960471fe8c4bfe191a6a80a9f9d5d22754dc4afe0ec18"),
    "graph_review": ("f0-edge-orbit-packing-literature-review.json", "ca9e0aecf5a7bc3dee2245209a2d7b23b40451d51645876aecfa19eb5615c1d7"),
    "Z_preparation": ("f0-pair-orbit-packing-preparation01.json.gz", "09412183bb01527a6fa2aeb23623b95af925767d5067bb363f10a2a8f8254a13"),
    "Z_result": ("f0-pair-orbit-packing-scan01.json.gz", "1bbba3061689f8faaf8fadcf556c0097d2b190673ab063a675259c007508b2bb"),
    "Z_cold": ("f0-pair-orbit-packing-scan01-cold.json", "c684243851efa7e12e9b9e5c7f857532421c1954233a5d9d6e24acfe5c826843"),
    "Z_ledger": ("f0-pair-orbit-packing-scan01-ledger.jsonl.gz", "4c53542bc89575b799b9e3d8b5905ae3dfe9782aa954db9d9afdf2a07c83d839"),
}
LIMITS = {"preparation_seconds": 60, "census_seconds": 60, "cold_seconds": 60,
          "uncompressed_ledger_bytes": 64*1024*1024, "optimizer_calls": 0, "automatic_retries": 0}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def tick(deadline):
    if time.monotonic() >= deadline:
        raise TimeoutError("bounded exterior-edge packing arithmetic")


def read(name):
    filename, expected = INPUTS[name]
    raw = (BASE/filename).read_bytes()
    assert sha(raw) == expected
    return json.loads(gzip.decompress(raw) if filename.endswith(".gz") else raw)


def binding():
    assert sha(Path(clique.__file__).read_bytes()) == HELPER_SHA
    assert sha(Path(graph_source.__file__).read_bytes()) == GRAPH_SOURCE_SHA
    return {"source_sha256": sha(Path(__file__).read_bytes()), "helper_sha256": HELPER_SHA,
            "graph_source_sha256": GRAPH_SOURCE_SHA,
            "inputs": {k: {"path": "experiments/logs/root-prism-free/"+f, "sha256": h} for k, (f,h) in INPUTS.items()},
            "limits": LIMITS}


def check_nonedge(reason, ei, ej, data):
    domain, moments = data["domain"], data["moments"]
    edges, triples, targets = [domain[k] for k in ("edges", "triples", "targets")]
    endpoints = set(edges[ei]) | set(edges[ej])
    kind = reason[0]
    if kind == "selector_zero":
        _, pair, po, premise = reason
        assert moments["pair_to_orbit"][pair] == po and po in moments["zero_pair_orbits"]
        assert any(graph_source.pair_id(a,b) == pair for a,b in combinations(sorted(endpoints),2))
        if premise[0] == "original_quota_one_Gram_row":
            row = moments["original_selector_equalities"][premise[1]]
            assert row["family"] == "Gram" and row["quota"] == 1
            assert any(graph_source.pair_id(a,b) == pair for a,b in combinations(sorted(set(row["support"]) & endpoints),2))
        else:
            assert premise[0] == "previously_cold_checked_binary_motif_zero"
            proof = moments["zero_moment_certificates"][premise[1]]
            assert proof["pair_id"] == pair and proof["kind"] == "certified binary motif times selector"
            assert proof["literal_polynomial"] == "z_a*(z_a+z_b-1)=z_a*z_b"
    elif kind == "one_edge_prism":
        proof = data["one_edge"]["literal_prism_witnesses"][reason[1]]
        assert proof["edge_id"] in (ei,ej)
        other = ej if proof["edge_id"] == ei else ei
        assert proof["third_selector"] in edges[other] and proof["third_selector"] not in edges[proof["edge_id"]]
    elif kind == "two_edge_prism":
        proof = data["path"]["literal_witnesses"][reason[1]]
        assert set(proof[6:8]) == {ei,ej}
    elif kind == "three_common_neighbors":
        _, center, left, right, u, v = reason
        assert {tuple(edges[ei]),tuple(edges[ej])} == {tuple(sorted((center,left))),tuple(sorted((center,right)))}
        assert len({center,left,right}) == 3 and u != v
        assert {u,v} <= set(triples[left]) & set(triples[right])
    else:
        assert kind == "mixed_quota_one"
        _, center, site, left, right = reason
        assert {tuple(edges[ei]),tuple(edges[ej])} == {tuple(sorted((center,left))),tuple(sorted((center,right)))}
        assert len({center,left,right}) == 3 and site in triples[left] and site in triples[right]
        assert targets[center][site] == 1


def prepare(deadline):
    bind = binding()
    graphs, review, zprep, zresult, zcold = [read(k) for k in ("graphs","graph_review","Z_preparation","Z_result","Z_cold")]
    assert review["status"].startswith("PASS") and review["subject"]["sha256"] == GRAPH_SOURCE_SHA
    assert graphs["source_sha256"] == GRAPH_SOURCE_SHA
    assert graphs["dispositions"] == {"prior_Y_zero_orbit":162,"retained_compatibility_graph":5643}
    assert zcold["status"].startswith("PASS") and zcold["checked_orbits"] == 9353
    assert zcold["complete_saved_prefix_checked"] and zcold["record_sha256"] == INPUTS["Z_result"][1]
    assert zresult["complete"] and zresult["summary"]["completed_orbits"] == 9353
    assert zresult["ledger_sha256"] == INPUTS["Z_ledger"][1]
    assert zprep["helper_sha256"] == HELPER_SHA and zprep["scope"]["controls"]["clique_helper"]["complete_graphs_through_five_vertices"] == 1100
    ledger = BASE/INPUTS["Z_ledger"][0]
    assert sha(ledger.read_bytes()) == INPUTS["Z_ledger"][1]
    zgraphs = {}
    with gzip.open(ledger,"rb") as stream:
        for raw in stream:
            row = json.loads(raw)
            assert row["pair_orbit"] not in zgraphs
            zgraphs[row["pair_orbit"]] = (row["adjacency"],row["maximum_compatible_pair_objects"])
    assert len(zgraphs) == 9353
    data = graph_source.read_inputs(deadline)
    domain, domains, moments = [data[k] for k in ("domain","domains","moments")]
    old_to_new = {old:new for new,old in enumerate(domains["new15038_to_original15589"])}
    expected = [oi for oi in range(5805) if 42+oi not in set(domains["original_Y_zero_columns"])]
    assert [r["edge_orbit"] for r in graphs["records"]] == expected
    reasons, additional, z_bounds = Counter(), [], []
    checked_actions = 0
    for record in graphs["records"]:
        tick(deadline)
        oi, po = record["edge_orbit"], record["pair_orbit"]
        ids, vertices, adjacency = [record[k] for k in ("literal_edge_ids","literal_edges","adjacency_masks")]
        assert ids == domain["edge_orbits"][oi] and vertices == [domain["edges"][i] for i in ids]
        assert record["original_Y_column"] == 42+oi and record["reduced_count_column"] == old_to_new[42+oi]
        assert po == domains["edge_orbit_pair_orbits"][oi]
        assert [graph_source.pair_id(*p) for p in vertices] == moments["pair_orbits"][po]
        n = clique.validate(adjacency)
        assert n == len(ids) == record["raw_count_upper_bound"]
        expected_non_edges = {(i,j) for i,j in combinations(range(n),2) if not (adjacency[i] >> j)&1}
        assert len(record["nonedge_proofs"]) == len(expected_non_edges)
        assert {(i,j) for i,j,_ in record["nonedge_proofs"]} == expected_non_edges
        for i,j,reason in record["nonedge_proofs"]:
            check_nonedge(reason,ids[i],ids[j],data)
            reasons[reason[0]] += 1
        positions = {tuple(e):i for i,e in enumerate(vertices)}
        assert len(record["actual_action_permutations"]) == 12
        for g,permutation in zip(domains["signature_actions"],record["actual_action_permutations"]):
            assert permutation == [positions[tuple(sorted((g[a],g[b])))] for a,b in vertices]
            for i,mask in enumerate(adjacency):
                assert sum(1 << permutation[j] for j in range(n) if mask >> j&1) == adjacency[permutation[i]]
                checked_actions += 1
        assert set(p[0] for p in record["actual_action_permutations"]) == set(range(n))
        assert record["anchor"] == 0 and record["anchor_neighbors"] == [j for j in range(n) if adjacency[0]>>j&1]
        zadj,zmax = zgraphs[po]
        assert len(zadj) == n and all(not (a & ~b) for a,b in zip(adjacency,zadj))
        extra = sum(b.bit_count()-a.bit_count() for a,b in zip(adjacency,zadj))//2
        if extra:
            additional.append([oi,extra])
        z_bounds.append(zmax)
    return {**bind,"status":"PASS: all stored Y-graph premises and actual actions checked; no clique census",
            "graphs":5643,"nonedge_proofs_checked":dict(reasons),"action_vertex_checks":checked_actions,
            "prior_Z_clique_bounds_in_graph_order":z_bounds,
            "orbits_with_additional_edge_conflicts":additional,
            "additional_edge_conflicts":sum(n for _,n in additional),
            "future_anchor_subset_bound":graphs["worst_future_anchor_subset_cases"],
            "small_clique_controls_reused":INPUTS["Z_preparation"][1],
            "maximum_clique_searches":0,"optimizer_calls":0,
            "scope":"Every selected edge set gives a clique in the checked orbit graph. A finite compatibility clique need not extend to an incidence or graph."}


def principal(adjacency, vertices):
    return [sum(1 << j for j,b in enumerate(vertices) if adjacency[a]>>b&1) for a in vertices]


def summary():
    return {"checked_orbits":0,"bound_histogram":Counter(),"subset_recurrences":0,
            "improved_raw_orbit_bounds":0,"improved_previous_Z_bounds":[]}


def collect(state,row):
    state["checked_orbits"] += 1
    state["bound_histogram"][row["bound"]] += 1
    state["subset_recurrences"] += len(row["certificate"]["subset_values"])
    state["improved_raw_orbit_bounds"] += row["bound"] < row["raw_orbit_bound"]
    if row["bound"] < row["prior_Z_bound"]:
        state["improved_previous_Z_bounds"].append({k:row[k] for k in ("edge_orbit","count_column","bound","prior_Z_bound")})


def write(path,value):
    raw = canonical(value)+b"\n"
    with path.open("xb") as stream:
        stream.write(gzip.compress(raw,mtime=0) if path.suffix==".gz" else raw)


if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode",choices=("prepare","census","replay"))
    parser.add_argument("--preparation",type=Path)
    parser.add_argument("--record",type=Path)
    parser.add_argument("--ledger",type=Path)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args();started=time.monotonic()
    deadline=started+LIMITS[{"prepare":"preparation_seconds","census":"census_seconds","replay":"cold_seconds"}[args.mode]]
    if args.mode=="prepare":
        result=prepare(deadline);result["seconds"]=time.monotonic()-started
    else:
        assert args.preparation is not None and args.ledger is not None
        prep_raw=args.preparation.read_bytes();prep=json.loads(gzip.decompress(prep_raw) if args.preparation.suffix==".gz" else prep_raw)
        assert all(prep[k]==v for k,v in binding().items()) and prep["status"].startswith("PASS")
        graphs=read("graphs")["records"];assert len(graphs)==len(prep["prior_Z_clique_bounds_in_graph_order"])==5643
        state=summary();digest=hashlib.sha256();raw_bytes=0;terminal="COMPLETE";error=None
        if args.mode=="census":
            assert args.record is None
            with args.ledger.open("xb") as sink:
                with gzip.GzipFile(filename="",mode="wb",fileobj=sink,mtime=0) as stream:
                    try:
                        for graph,zbound in zip(graphs,prep["prior_Z_clique_bounds_in_graph_order"]):
                            tick(deadline)
                            cert=clique.maximum_clique(principal(graph["adjacency_masks"],graph["anchor_neighbors"]),lambda:tick(deadline))
                            bound=1+cert["maximum"];assert bound<=zbound
                            row={"edge_orbit":graph["edge_orbit"],"count_column":graph["reduced_count_column"],
                                 "bound":bound,"prior_Z_bound":zbound,"raw_orbit_bound":len(graph["literal_edge_ids"]),"certificate":cert}
                            raw=canonical(row)+b"\n"
                            if raw_bytes+len(raw)>LIMITS["uncompressed_ledger_bytes"]:raise TimeoutError("raw certificate byte budget")
                            stream.write(raw);digest.update(raw);raw_bytes+=len(raw);collect(state,row)
                    except (TimeoutError,AssertionError,KeyError,ValueError) as exc:
                        terminal="UNKNOWN" if isinstance(exc,TimeoutError) else "ERROR";error={"type":type(exc).__name__,"message":str(exc)}
            result={**binding(),"status":terminal+": exact Y-orbit packing census","complete":state["checked_orbits"]==5643,
                    "preparation_sha256":sha(prep_raw),"summary":state,"error":error,
                    "ledger_sha256":sha(args.ledger.read_bytes()),"ledger_raw_sha256":digest.hexdigest(),"ledger_raw_bytes":raw_bytes,
                    "optimizer_calls":0,"graph_or_incidence_feasibility_claimed":False,"seconds":time.monotonic()-started}
        else:
            assert args.record is not None
            saved_raw=args.record.read_bytes();saved=json.loads(gzip.decompress(saved_raw) if args.record.suffix==".gz" else saved_raw)
            assert all(saved[k]==v for k,v in binding().items()) and saved["preparation_sha256"]==sha(prep_raw)
            assert saved["ledger_sha256"]==sha(args.ledger.read_bytes())
            try:
                with gzip.open(args.ledger,"rb") as stream:
                    for i,raw in enumerate(stream):
                        tick(deadline);assert i<len(graphs)
                        row=json.loads(raw);graph=graphs[i]
                        assert row["edge_orbit"]==graph["edge_orbit"] and row["count_column"]==graph["reduced_count_column"]
                        assert row["prior_Z_bound"]==prep["prior_Z_clique_bounds_in_graph_order"][i]
                        assert row["raw_orbit_bound"]==len(graph["literal_edge_ids"])
                        assert row["bound"]==1+clique.verify(principal(graph["adjacency_masks"],graph["anchor_neighbors"]),row["certificate"])
                        assert row["bound"]<=row["prior_Z_bound"]
                        collect(state,row);digest.update(raw);raw_bytes+=len(raw)
                assert json.loads(json.dumps(state))==saved["summary"]
                assert digest.hexdigest()==saved["ledger_raw_sha256"] and raw_bytes==saved["ledger_raw_bytes"]
                assert saved["complete"]==(state["checked_orbits"]==5643)
                terminal="PASS"
            except (TimeoutError,AssertionError,KeyError,ValueError) as exc:
                terminal="UNKNOWN" if isinstance(exc,TimeoutError) else "ERROR";error={"type":type(exc).__name__,"message":str(exc)}
            result={**binding(),"status":terminal+": exact saved Y-clique certificate replay",
                    "record_sha256":sha(saved_raw),"preparation_sha256":sha(prep_raw),"complete_saved_prefix_checked":terminal=="PASS",
                    "checked_orbits":state["checked_orbits"],"error":error,"maximum_clique_searches":0,"optimizer_calls":0,
                    "seconds":time.monotonic()-started}
    write(args.output,result)
    print(json.dumps({"status":result["status"],"sha256":sha(args.output.read_bytes()),"seconds":result["seconds"],
                      "summary":result.get("summary"),"error":result.get("error")},indent=2))
