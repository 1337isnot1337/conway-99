"""Check every direct mixed/core-pair alternative for three residual rows."""
import gzip
import hashlib
import json
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[2]
LOGS = ROOT/"experiments/logs/root-prism-free"
INPUTS = {
    "domain": ("f0-boolean-fractional-model.json.gz", "703206929c9c85a40ac4ddcbfb1708c716c288482cf50c77a32249404e35b782"),
    "graphs": ("f0-edge-orbit-packing-preparation01.json.gz", "2d581d92545eb1d8718960471fe8c4bfe191a6a80a9f9d5d22754dc4afe0ec18"),
    "graph_cold": ("f0-edge-orbit-packing-census-preparation01.json", "3561840ec929ad68a6b4e22df8f6cad5e9a604b9828b9bc4cd63bdfa8654cdd0"),
    "audit": ("f0-endpoint-star-capacities-implication-audit01.json.gz", "9928c3937576444bb6bbc33e3b5bc8631effe06ffbaede1f5aa4061483c35595"),
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read(key):
    name, expected = INPUTS[key]
    raw = (LOGS/name).read_bytes(); assert sha(raw) == expected
    return json.loads(gzip.decompress(raw) if name.endswith(".gz") else raw)


def main():
    start = time.monotonic()
    domain, graphs, checked, audit = [read(k) for k in INPUTS]
    domain = domain["validation"]
    assert checked["status"].startswith("PASS")
    assert checked["inputs"]["graphs"]["sha256"] == INPUTS["graphs"][1]
    assert audit["status"].startswith("PASS")
    core, triples, targets = [domain[k] for k in ("core", "triples", "targets")]
    assert len(core) == 21 and len(triples) == len(targets) == 480
    assert targets == [[2-int(j in h)-sum((core[j+3] >> (k+3)) & 1 for k in h)
                       for j in range(18)] for h in triples]
    graph_of = {r["edge_orbit"]: r for r in graphs["records"]}
    residual = [r for r in audit["records"] if r["classification"] == "additional_edge_packing_premise"]
    assert [r["row"]["count_column"] for r in residual] == [2855, 2917, 2935]
    records = []
    for previous in residual:
        row = previous["row"]; graph = graph_of[row["object_orbit"]]
        witnesses = []
        for saved in previous["endpoint_witnesses"]:
            v = saved["endpoint"]; positions = saved["edge_positions"]
            assert len(positions) == 2 and all(v in graph["literal_edges"][i] for i in positions)
            other = [next(a for a in graph["literal_edges"][i] if a != v) for i in positions]
            common = sorted(set(triples[other[0]]) & set(triples[other[1]]))
            one = [j for j in common if targets[v][j] <= 1]
            assert all(targets[v][j] == 1 for j in one)
            witnesses.append({"endpoint": v, "other_endpoints": other, "common_core_sites": common,
                              "mixed_target_values": [targets[v][j] for j in common],
                              "quota_one_sites": one, "common_core_pair_available": len(common) >= 2})
        mixed = all(w["quota_one_sites"] for w in witnesses)
        assert all(len(w["common_core_sites"]) == 1 for w in witnesses)
        records.append({"row": row, "all_literal_stars": witnesses,
                        "implied_by_original_mixed_quota_one_equalities": mixed})
    assert [r["row"]["count_column"] for r in records if r["implied_by_original_mixed_quota_one_equalities"]] == [2855]
    result = {"status": "PASS: all direct mixed-site and common-core-pair alternatives checked",
              "source_sha256": sha(Path(__file__).read_bytes()), "inputs": INPUTS, "records": records,
              "additional_mixed_implications": 1, "remaining_count_columns": [2917, 2935],
              "total518_rows_with_simple_implication_witness": 516,
              "full_model_nonredundance_claimed": False,
              "case_clique_searches": 0, "optimizer_calls": 0, "seconds": time.monotonic()-start}
    assert result["seconds"] < 60
    out = LOGS/"f0-endpoint-star-capacities-additional-mixed-check01.json"
    with out.open("x") as stream:
        json.dump(result, stream, indent=2); stream.write("\n")
    print(json.dumps({"status": result["status"], "seconds": result["seconds"], "sha256": sha(out.read_bytes()),
                      "remaining_count_columns": result["remaining_count_columns"]}, indent=2))


if __name__ == "__main__":
    main()
