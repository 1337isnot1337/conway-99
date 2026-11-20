"""Exact endpoint capacities from already certified finite orbit graphs.

If selected pair/edge objects form a clique in G_R, the objects incident
to a selected signature v form a clique in its endpoint star. Summing
the star bounds over selector orbit O_i gives m*P_R <= d*N_i, where m=2
for an internal orbit and m=1 for a cross orbit. No graph symmetry of a
completion is assumed. Only stars of degree at least two need a census.
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
LOGS = ROOT / "experiments/logs/root-prism-free"
INPUTS = {
    "domains": ("f0-orbit-populations02-domains.json.gz", "4f079468530dba0746512cc4afce01666b2a63a2c8f35f66a4660a4fe3bab8ab"),
    "Z_preparation": ("f0-pair-orbit-packing-preparation01.json.gz", "09412183bb01527a6fa2aeb23623b95af925767d5067bb363f10a2a8f8254a13"),
    "Z_result": ("f0-pair-orbit-packing-scan01.json.gz", "1bbba3061689f8faaf8fadcf556c0097d2b190673ab063a675259c007508b2bb"),
    "Z_ledger": ("f0-pair-orbit-packing-scan01-ledger.jsonl.gz", "4c53542bc89575b799b9e3d8b5905ae3dfe9782aa954db9d9afdf2a07c83d839"),
    "Z_cold": ("f0-pair-orbit-packing-scan01-cold.json", "c684243851efa7e12e9b9e5c7f857532421c1954233a5d9d6e24acfe5c826843"),
    "Y_graphs": ("f0-edge-orbit-packing-preparation01.json.gz", "2d581d92545eb1d8718960471fe8c4bfe191a6a80a9f9d5d22754dc4afe0ec18"),
    "Y_preparation": ("f0-edge-orbit-packing-census-preparation01.json", "3561840ec929ad68a6b4e22df8f6cad5e9a604b9828b9bc4cd63bdfa8654cdd0"),
    "Y_cold": ("f0-edge-orbit-packing-scan01-cold.json", "8965162db2cd4bfc05c129ecd5cf0a1ba2b39bcbd35f776cc60c27a52c501ded"),
}
LIMITS = {"seconds_per_stage": 60, "maximum_star_vertices": 4,
          "uncompressed_record_bytes": 16 << 20, "optimizer_calls": 0}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def binding():
    return {"source_sha256": sha(Path(__file__).read_bytes()), "limits": LIMITS,
            "inputs": {k: {"path": str((LOGS/p).relative_to(ROOT)), "sha256": h}
                       for k, (p, h) in INPUTS.items()}}


def raw_input(key):
    path, expected = INPUTS[key]
    raw = (LOGS/path).read_bytes()
    assert sha(raw) == expected
    return gzip.decompress(raw) if path.endswith(".gz") else raw


def read(key):
    return json.loads(raw_input(key))


def tick(deadline):
    if time.monotonic() > deadline:
        raise TimeoutError("endpoint-star stage deadline")


def principal(adjacency, vertices):
    return [sum(1 << j for j, b in enumerate(vertices) if adjacency[a] >> b & 1)
            for a in vertices]


def clique(adjacency, vertices):
    return all(adjacency[a] >> b & 1 for a, b in combinations(vertices, 2))


def star_certificate(adjacency):
    n = len(adjacency)
    assert 1 <= n <= LIMITS["maximum_star_vertices"]
    best = []
    for mask in range(1 << n):
        vertices = [i for i in range(n) if mask >> i & 1]
        if len(vertices) > len(best) and clique(adjacency, vertices):
            best = vertices
    failures = []
    for vertices in combinations(range(n), len(best)+1):
        nonedge = next(([a, b] for a, b in combinations(vertices, 2)
                        if not (adjacency[a] >> b & 1)), None)
        assert nonedge is not None
        failures.append([list(vertices), nonedge])
    return {"maximum": len(best), "attaining_clique": best,
            "all_next_size_nonedge_witnesses": failures}


def verify_star(adjacency, certificate):
    n, bound = len(adjacency), certificate["maximum"]
    assert 1 <= bound <= n <= LIMITS["maximum_star_vertices"]
    witness = certificate["attaining_clique"]
    assert witness == sorted(set(witness)) and len(witness) == bound
    assert all(0 <= i < n for i in witness) and clique(adjacency, witness)
    expected = list(combinations(range(n), bound+1))
    failures = certificate["all_next_size_nonedge_witnesses"]
    assert len(failures) == len(expected)
    for vertices, (saved, nonedge) in zip(expected, failures):
        assert saved == list(vertices)
        a, b = nonedge
        assert a < b and a in vertices and b in vertices
        assert not (adjacency[a] >> b & 1)
    return bound


def controls():
    cases = 0
    for n in range(1, 5):
        edges = list(combinations(range(n), 2))
        for graph in range(1 << len(edges)):
            adjacency = [0]*n
            for i, (a, b) in enumerate(edges):
                if graph >> i & 1:
                    adjacency[a] |= 1 << b
                    adjacency[b] |= 1 << a
            certificate = star_certificate(adjacency)
            assert verify_star(adjacency, certificate) == certificate["maximum"]
            cases += 1
    assert cases == 75
    return {"all_labelled_simple_graphs_on_one_through_four_vertices": cases}


def inventory(deadline):
    domains = read("domains")
    orbits = domains["selector_orbits"]
    assert len(orbits) == 42 and sorted(a for orbit in orbits for a in orbit) == list(range(480))
    orbit_of = {a: i for i, orbit in enumerate(orbits) for a in orbit}
    zprep, zresult, zcold = read("Z_preparation"), read("Z_result"), read("Z_cold")
    assert zcold["status"].startswith("PASS") and zcold["checked_orbits"] == 9353
    assert zcold["record_sha256"] == INPUTS["Z_result"][1]
    assert zresult["complete"] and zresult["ledger_sha256"] == INPUTS["Z_ledger"][1]
    pair_sites = list(combinations(range(480), 2))
    zledger_raw = raw_input("Z_ledger")
    assert sha(zledger_raw) == zresult["ledger_raw_sha256"]
    zledger = [json.loads(line) for line in zledger_raw.splitlines()]
    assert len(zledger) == 9353
    graphs = []
    for scope, record in zip(zprep["scope"]["retained_orbits"], zledger):
        assert scope["pair_orbit"] == record["pair_orbit"]
        assert scope["count_column"] == record["count_column"]
        graphs.append(("Z", scope["pair_orbit"], scope["count_column"],
                       [pair_sites[p] for p in scope["literal_pair_ids"]], record["adjacency"]))
    yprep, ycold, ygraphs = read("Y_preparation"), read("Y_cold"), read("Y_graphs")
    assert yprep["status"].startswith("PASS") and yprep["graphs"] == 5643
    assert yprep["inputs"]["graphs"]["sha256"] == INPUTS["Y_graphs"][1]
    assert ycold["status"].startswith("PASS") and ycold["checked_orbits"] == 5643
    assert ycold["preparation_sha256"] == INPUTS["Y_preparation"][1]
    assert len(ygraphs["records"]) == 5643
    for record in ygraphs["records"]:
        graphs.append(("Y", record["edge_orbit"], record["reduced_count_column"],
                       record["literal_edges"], record["adjacency_masks"]))
    targets, trivial = [], Counter()
    for family, oi, column, objects, adjacency in graphs:
        tick(deadline)
        assert len(objects) == len(adjacency) <= 12
        for a, mask in enumerate(adjacency):
            assert not mask >> a & 1 and mask < 1 << len(adjacency)
            assert all(bool(mask >> b & 1) == bool(adjacency[b] >> a & 1) for b in range(len(adjacency)))
        ends = sorted({orbit_of[a] for pair in objects for a in pair})
        assert 1 <= len(ends) <= 2
        for endpoint_orbit in ends:
            stars = [[a, [j for j, pair in enumerate(objects) if a in pair]] for a in orbits[endpoint_orbit]]
            degree_set = {len(indices) for _, indices in stars}
            assert len(degree_set) == 1
            degree = degree_set.pop()
            assert 1 <= degree <= 4
            multiplicity = 2 if len(ends) == 1 else 1
            assert sum(len(s) for _, s in stars) == multiplicity*len(objects)
            if degree == 1:
                trivial[family] += 1
                continue
            targets.append({"family": family, "object_orbit": oi, "count_column": column,
                            "endpoint_orbit": endpoint_orbit, "multiplicity": multiplicity,
                            "raw_degree": degree, "adjacency": adjacency, "stars": stars})
    return targets, {"Z_graphs": 9353, "Y_graphs": 5643, "degree_one_endpoints": dict(trivial),
                     "candidate_endpoints": len(targets),
                     "maximum_full_subsets": sum(len(t["stars"])*(1 << t["raw_degree"]) for t in targets)}


def save(path, value):
    raw = canonical(value)+b"\n"
    assert len(raw) <= LIMITS["uncompressed_record_bytes"]
    with path.open("xb") as stream:
        stream.write(gzip.compress(raw, mtime=0) if path.suffix == ".gz" else raw)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "census", "replay"))
    parser.add_argument("--preparation", type=Path)
    parser.add_argument("--record", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    start = time.monotonic(); deadline = start+LIMITS["seconds_per_stage"]
    targets, scope = inventory(deadline)
    if args.mode == "prepare":
        result = {**binding(), "status": "PREPARED: endpoint inventory and tiny controls; no case clique census",
                  "scope": scope, "controls": controls(), "case_star_searches": 0}
    else:
        prep_raw = args.preparation.read_bytes(); prep = json.loads(prep_raw)
        assert all(prep[k] == v for k, v in binding().items()) and prep["scope"] == scope
        saved = None
        if args.mode == "replay":
            raw = args.record.read_bytes(); saved = json.loads(gzip.decompress(raw))
            assert all(saved[k] == v for k, v in binding().items())
            assert saved["preparation_sha256"] == sha(prep_raw)
            assert len(saved["records"]) == len(targets)
        records, rows, stars_checked = [], [], 0
        for i, target in enumerate(targets):
            tick(deadline)
            proofs, maxima = [], []
            for j, (a, indices) in enumerate(target["stars"]):
                local = principal(target["adjacency"], indices)
                cert = star_certificate(local) if saved is None else saved["records"][i]["star_certificates"][j]
                maxima.append(verify_star(local, cert)); proofs.append(cert); stars_checked += 1
            capacity = max(maxima)
            record = {"target_index": i, "target_sha256": sha(canonical(target)),
                      "star_certificates": proofs, "capacity": capacity}
            if saved is not None:
                assert record == saved["records"][i]
            records.append(record)
            if capacity < target["raw_degree"]:
                rows.append({"family": target["family"], "object_orbit": target["object_orbit"],
                             "count_column": target["count_column"], "endpoint_orbit": target["endpoint_orbit"],
                             "terms": [[target["endpoint_orbit"], -capacity],
                                       [target["count_column"], target["multiplicity"]]],
                             "upper": 0, "raw_degree": target["raw_degree"], "capacity": capacity})
        summary = {"candidate_endpoints": len(targets), "literal_stars_checked": stars_checked,
                   "strict_degree_improvements": len(rows),
                   "improvements_by_family": dict(Counter(r["family"] for r in rows))}
        if saved is not None:
            assert summary == saved["summary"] and rows == saved["rows"]
            result = {**binding(), "status": "PASS: every saved endpoint-star proof and summed count row replayed",
                      "record_sha256": sha(raw), "summary": summary, "case_star_searches": 0}
        else:
            result = {**binding(), "status": "COMPLETE: exact conditional endpoint-capacity census",
                      "preparation_sha256": sha(prep_raw), "scope": scope, "summary": summary,
                      "records": records, "rows": rows, "full_model_nonredundance_claimed": False}
    result["seconds"] = time.monotonic()-start
    result["graph_or_incidence_feasibility_claimed"] = False
    tick(deadline); save(args.output, result)
    print(json.dumps({k: result[k] for k in ("status", "seconds", "scope", "summary") if k in result}, indent=2))


if __name__ == "__main__":
    main()
