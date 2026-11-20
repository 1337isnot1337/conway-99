"""Trace endpoint-capacity rows to earlier lifted or mixed equalities.

This is a provenance check, not an optimizer or a second clique census.
It separates exact simple implications from the remaining rows without
claiming nonredundance against every constraint of the count model.
"""
from collections import Counter
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[2]
LOGS = ROOT / "experiments/logs/root-prism-free"
SOURCE_SHA = "7004a494e0629fc25ea7ddd3b093fcc23c2935dc060e0449cb668305685421bb"
CENSUS_SHA = "045a4de83734da3a5384a3be487d42c7b5f2d1d6977f65b024b2323a9fe2daba"
COLD_SHA = "adfd62dfab7a9e8722c61457f961e27dfb3e00e47f3062672741e07b831c984d"
MOMENTS_SHA = "404d91da35c798ba248887c22a7500957947e24b71d5197dc44432460e6d219e"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read(path, expected):
    raw = path.read_bytes()
    assert sha(raw) == expected
    return json.loads(gzip.decompress(raw) if path.suffix == ".gz" else raw)


def pair_id(a, b):
    a, b = sorted((a, b))
    assert 0 <= a < b < 480
    return a*(959-a)//2+b-a-1


def run():
    started = time.monotonic(); deadline = started+60
    source = ROOT/"experiments/workspace/root_prism_free_f0_endpoint_star_capacities.py"
    assert sha(source.read_bytes()) == SOURCE_SHA
    spec = importlib.util.spec_from_file_location("frozen_endpoint_inventory", source)
    helper = importlib.util.module_from_spec(spec); spec.loader.exec_module(helper)
    census = read(LOGS/"f0-endpoint-star-capacities-census01.json.gz", CENSUS_SHA)
    cold = read(LOGS/"f0-endpoint-star-capacities-census01-cold.json", COLD_SHA)
    assert cold["status"].startswith("PASS") and cold["record_sha256"] == CENSUS_SHA
    assert cold["source_sha256"] == census["source_sha256"] == SOURCE_SHA
    targets, scope = helper.inventory(deadline)
    assert scope == census["scope"]
    target_map = {(t["family"], t["object_orbit"], t["endpoint_orbit"]): t for t in targets}
    moments = read(LOGS/"f0-second-moments-preparation02.json.gz", MOMENTS_SHA)
    zeros = {r["pair_id"]: r for r in moments["zero_moment_certificates"]}
    eqs = moments["original_selector_equalities"]
    assert len(eqs) == 172 and len(moments["full_RLT_to_quotient"]) == 480*172
    prep = helper.read("Z_preparation")
    pairs = list(__import__("itertools").combinations(range(480), 2))
    z_objects = {r["pair_orbit"]: [pairs[p] for p in r["literal_pair_ids"]]
                 for r in prep["scope"]["retained_orbits"]}
    y_graphs = {r["edge_orbit"]: r for r in helper.read("Y_graphs")["records"]}
    z_rows = {(r["object_orbit"], r["endpoint_orbit"]): r
              for r in census["rows"] if r["family"] == "Z"}
    records = []
    for row in census["rows"]:
        helper.tick(deadline)
        t = target_map[row["family"], row["object_orbit"], row["endpoint_orbit"]]
        assert row["capacity"] == 1 and row["raw_degree"] == t["raw_degree"] == 2
        record = {"row": row}
        if row["family"] == "Z":
            objects, witnesses = z_objects[row["object_orbit"]], []
            for v, indices in t["stars"]:
                assert len(indices) == 2
                b, c = [next(a for a in objects[i] if a != v) for i in indices]
                zero = zeros[pair_id(b, c)]
                witness = {"endpoint": v, "other_endpoints": sorted((b, c)),
                           "zero_pair_id": pair_id(b, c), "zero_kind": zero["kind"]}
                if zero["kind"] == "quota-one nonnegative lifted equality":
                    r = zero["selector_Gram_row"]; equality = eqs[r]
                    assert equality["family"] == "Gram" and equality["quota"] == 1
                    assert b in equality["support"] and c in equality["support"]
                    assert v not in equality["support"]
                    full = 172*v+r
                    witness.update(original_Gram_row=r, lifted_row=full,
                                   quotient_RLT_row=moments["full_RLT_to_quotient"][full],
                                   signed_divisor=moments["full_RLT_signed_divisor"][full])
                    assert witness["quotient_RLT_row"] >= 0
                witnesses.append(witness)
            record["endpoint_witnesses"] = witnesses
            record["classification"] = ("original_Gram_RLT_and_nonnegativity" if
                all(w["zero_kind"] == "quota-one nonnegative lifted equality" for w in witnesses)
                else "uses_prior_binary_motif_zero")
        else:
            graph = y_graphs[row["object_orbit"]]
            z = z_rows.get((graph["pair_orbit"], row["endpoint_orbit"]))
            if z is not None and z["terms"][1][1] == row["terms"][1][1]:
                assert z["capacity"] == row["capacity"]
                record.update(classification="matching_Z_capacity_and_Y_le_Z", matching_Z_row=z)
            else:
                proofs = {(i, j): p for i, j, p in graph["nonedge_proofs"]}
                witnesses = []
                for v, indices in t["stars"]:
                    assert len(indices) == 2
                    reason = proofs[tuple(indices)]
                    if reason[0] == "mixed_quota_one":
                        assert reason[1] == v
                        assert v in graph["literal_edges"][indices[0]] and v in graph["literal_edges"][indices[1]]
                    witnesses.append({"endpoint": v, "edge_positions": indices, "premise": reason})
                kinds = {w["premise"][0] for w in witnesses}
                record.update(endpoint_witnesses=witnesses,
                              classification="original_mixed_quota_one_and_nonnegativity" if
                              kinds == {"mixed_quota_one"} else "additional_edge_packing_premise")
        records.append(record)
    summary = dict(Counter((r["row"]["family"]+":"+r["classification"]) for r in records))
    result = {"status": "PASS: complete endpoint-row implication provenance",
              "source_sha256": sha(Path(__file__).read_bytes()),
              "endpoint_source_sha256": SOURCE_SHA, "census_sha256": CENSUS_SHA,
              "census_cold_sha256": COLD_SHA, "moments_sha256": MOMENTS_SHA,
              "rows_checked": len(records), "summary": summary, "records": records,
              "proof_of_RLT_implication": "For each endpoint v, multiply the quota-one Gram equality containing both other endpoints by x_v. Nonnegative pair moments give their sum at most x_v. Sum over the endpoint orbit and average actual core relabelings to obtain the stated orbit-count row.",
              "proof_of_mixed_implication": "The existing mixed quota-one equality at v and its core site bounds the two incident Y variables by x_v. Sum over all endpoints; an internal edge is counted twice.",
              "unclassified_rows_not_claimed_independent_of_full_model": True,
              "case_clique_searches": 0, "optimizer_calls": 0,
              "seconds": time.monotonic()-started}
    helper.tick(deadline)
    output = LOGS/"f0-endpoint-star-capacities-implication-audit01.json.gz"
    with output.open("xb") as stream:
        stream.write(gzip.compress(helper.canonical(result)+b"\n", mtime=0))
    print(json.dumps({"status": result["status"], "summary": summary, "seconds": result["seconds"],
                      "sha256": sha(output.read_bytes())}, indent=2))


if __name__ == "__main__":
    run()
