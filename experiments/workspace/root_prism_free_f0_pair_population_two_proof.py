"""Two exact pair-population bounds from literal quota-one incompatibilities.

Only the two specified 12-pair orbits are inspected.  The 26 base witnesses
and their actual core transports prove triangle-free compatibility graphs.
No population-three equation, optimizer, or large subset census is used.
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
BASE = "experiments/logs/root-prism-free/"
INPUTS = {
    "domains": ("f0-orbit-populations02-domains.json.gz", "4f079468530dba0746512cc4afce01666b2a63a2c8f35f66a4660a4fe3bab8ab"),
    "domain_cold": ("f0-orbit-populations02-independent-replay.json", "a8bb55cbf773ea75a8cd1d5a18b50281ecbe08f6074cea04fb2d75799138273a"),
    "moments": ("f0-second-moments-preparation02.json.gz", "404d91da35c798ba248887c22a7500957947e24b71d5197dc44432460e6d219e"),
}
LEFT = [0, 1, 4, 5, 88, 91, 92, 95, 210, 211, 214, 215]
CASES = [
    {
        "pair_orbit": 25, "right_selector_orbit": 7, "reduced_column": 5699,
        "right": [26, 145, 30, 149, 83, 144, 87, 148, 82, 25, 86, 29],
        "neighbors": [88, 92, 95, 214],
        "excluded": [[1, 0, 1, 0], [4, 0, 4, 3], [5, 0, 5, 4],
                     [91, 0, 144, 143], [210, 210, 26, 143],
                     [211, 26, 25, 3087], [215, 26, 29, 3089]],
        "inside": [[88, 92, 88, 92, 3], [88, 95, 88, 95, 4],
                   [88, 214, 83, 86, 3089], [92, 95, 92, 95, 0],
                   [92, 214, 87, 86, 3087], [95, 214, 95, 86, 143]],
    },
    {
        "pair_orbit": 146, "right_selector_orbit": 6, "reduced_column": 5812,
        "right": [147, 27, 151, 31, 146, 81, 150, 85, 24, 80, 28, 84],
        "neighbors": [95, 211, 214, 215],
        "excluded": [[1, 0, 1, 0], [4, 0, 4, 3], [5, 0, 5, 4],
                     [88, 147, 146, 2684], [91, 91, 147, 23],
                     [92, 147, 150, 2688], [210, 0, 24, 23]],
        "inside": [[95, 211, 85, 80, 2688], [95, 214, 214, 85, 23],
                   [95, 215, 85, 84, 2684], [211, 214, 211, 214, 4],
                   [211, 215, 211, 215, 3], [214, 215, 214, 215, 0]],
    },
]


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def pair_id(a, b):
    a, b = sorted((a, b))
    assert 0 <= a < b < 480
    return a * (959 - a) // 2 + b - a - 1


def tick(deadline):
    if time.monotonic() >= deadline:
        raise TimeoutError("small pair-population proof deadline")


def load(root, deadline):
    data = {}
    for key, (name, expected) in INPUTS.items():
        tick(deadline)
        raw = (root / BASE / name).read_bytes()
        assert digest(raw) == expected, key
        data[key] = json.loads(gzip.decompress(raw) if name.endswith(".gz") else raw)
    assert data["domain_cold"]["status"].startswith("PASS")
    return data


def prove(data, deadline):
    domains, moments = data["domains"], data["moments"]
    actions = domains["signature_actions"]
    assert actions == moments["selector_actions"] and len(actions) == 12
    assert all(sorted(g) == list(range(480)) for g in actions)
    assert domains["selector_orbits"] == moments["selector_orbits"]
    assert domains["selector_orbits"][0] == LEFT
    assert sorted(g[0] for g in actions) == LEFT
    pmap = moments["pair_to_orbit"]
    zeros = {c - 5847 for c in domains["original_Z_zero_columns"]}
    assert zeros == set(moments["zero_pair_orbits"]) and len(zeros) == 389
    zero_proofs = {p["pair_id"]: p for p in moments["zero_moment_certificates"]}
    assert len(zero_proofs) == len(moments["zero_moment_certificates"]) == 4410
    old_to_new = {old: new for new, old in enumerate(domains["new15038_to_original15589"])}

    def zero_witness(a, b, expected):
        k = pair_id(a, b)
        assert pmap[k] == expected and expected in zeros
        proof = zero_proofs[k]
        assert sorted((proof["anchor"], proof["other"])) == sorted((a, b))
        row_id = proof["selector_Gram_row"]
        row = moments["original_selector_equalities"][row_id]
        assert row["family"] == "Gram" and row["quota"] == 1
        assert a in row["support"] and b in row["support"]
        return {"literal_pair": sorted((a, b)), "pair_id": k, "pair_orbit": expected,
                "original_Gram_row": row_id, "quota": 1}

    records = []
    for case in CASES:
        tick(deadline)
        po = case["pair_orbit"]
        right = case["right"]
        matching = dict(zip(LEFT, right))
        assert len(set(right)) == 12 and not set(LEFT).intersection(right)
        assert sorted(right) == domains["selector_orbits"][case["right_selector_orbit"]]
        assert domains["pair_orbit_selector_blocks"][po] == [0, case["right_selector_orbit"]]
        assert {pair_id(a, matching[a]) for a in LEFT} == set(moments["pair_orbits"][po])
        assert all(pmap[pair_id(a, matching[a])] == po for a in LEFT) and po not in zeros
        assert old_to_new[5847 + po] == case["reduced_column"]
        assert all(g[matching[a]] == matching[g[a]] for g in actions for a in LEFT)
        neighbors = case["neighbors"]
        assert len(neighbors) == len(set(neighbors)) == 4 and 0 not in neighbors
        assert sorted(row[0] for row in case["excluded"]) == sorted(set(LEFT) - {0} - set(neighbors))
        assert sorted(tuple(row[:2]) for row in case["inside"]) == list(combinations(neighbors, 2))
        base = []
        for other, a, b, z in case["excluded"]:
            assert {a, b}.issubset({0, matching[0], other, matching[other]})
            base.append(dict(objects=[0, other], zero=zero_witness(a, b, z)))
        for left, other, a, b, z in case["inside"]:
            assert {a, b}.issubset({left, matching[left], other, matching[other]})
            base.append(dict(objects=[left, other], zero=zero_witness(a, b, z)))
        assert len(base) == 13
        for other in neighbors:
            union = {0, matching[0], other, matching[other]}
            assert all(pmap[pair_id(a, b)] not in zeros for a, b in combinations(sorted(union), 2))
        stars = []
        adjacency = {}
        for gi, g in enumerate(actions):
            tick(deadline)
            anchor = g[0]
            mapped_neighbors = sorted(g[a] for a in neighbors)
            adjacency[anchor] = mapped_neighbors
            witnesses = []
            for row in base:
                a, b = row["zero"]["literal_pair"]
                witness = zero_witness(g[a], g[b], row["zero"]["pair_orbit"])
                objects = sorted(g[a] for a in row["objects"])
                assert set(witness["literal_pair"]).issubset(
                    {objects[0], matching[objects[0]], objects[1], matching[objects[1]]})
                witnesses.append(dict(objects=objects, zero=witness))
            stars.append({"anchor": anchor, "actual_core_action": gi,
                          "possible_neighbors": mapped_neighbors, "zero_witnesses": witnesses})
        assert len(adjacency) == 12
        assert all(a in adjacency[b] for a in LEFT for b in adjacency[a])
        assert all(not set(adjacency[a]).intersection(adjacency[b])
                   for a in LEFT for b in adjacency[a])
        positive_pair = [0, neighbors[0]]
        positive_selection = sorted({a for t in positive_pair for a in (t, matching[t])})
        assert all(pmap[pair_id(a, b)] not in zeros for a, b in combinations(positive_selection, 2))
        assert sum(a in positive_selection and matching[a] in positive_selection for a in LEFT) == 2
        records.append({
            "pair_orbit": po, "original_column": 5847 + po,
            "reduced_count_column": case["reduced_column"],
            "literal_matching": [[a, matching[a]] for a in LEFT],
            "selector_orbits": [0, case["right_selector_orbit"]],
            "pair_population_definition": "sum z_a*z_b over the listed 12 literal pairs",
            "base_anchor": 0, "base_possible_neighbors": neighbors,
            "base_zero_witnesses": base,
            "used_zero_pair_orbits": sorted({r["zero"]["pair_orbit"] for r in base}),
            "transported_star_certificates": sorted(stars, key=lambda x: x["anchor"]),
            "compatibility_vertex_count": 12, "compatibility_edge_count": 24,
            "compatibility_degree_histogram": dict(sorted(Counter(map(len, adjacency.values())).items())),
            "maximum_compatible_pair_objects": 2,
            "partial_selector_set_attaining_two_under_zero_constraints": positive_selection,
            "proved_count_upper_bound": 2,
            "host_graph_automorphism_assumed": False,
        })
    return {"status": "PASS: two direct pair-zero packing bounds",
            "cases": records, "base_zero_witnesses": 26,
            "transported_zero_witnesses": 312, "matching_equivariance_checks": 288,
            "original_quota_one_zeros_checked_directly": True,
            "population_three_premise_used": False,
            "extra_Gram_capacity_premise_used": False,
            "full_incidence_or_graph_existence_claimed": False,
            "optimizer_calls": 0, "large_subset_censuses": 0}


def write(path, record):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as stream:
        json.dump(record, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["prove", "replay"])
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--record", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    start = time.monotonic()
    source_sha = digest(Path(__file__).read_bytes())
    proof = prove(load(args.root, start + 10), start + 10)
    # JSON normalization makes integer histogram keys portable on replay.
    proof = json.loads(json.dumps(proof, sort_keys=True, allow_nan=False))
    if args.mode == "prove":
        assert args.output is None
        result = {"schema": "conway99.f0.pair_population_two_proof.v1",
                  "source_sha256": source_sha, "inputs": INPUTS, "proof": proof,
                  "seconds": time.monotonic() - start}
        write(args.record, result)
    else:
        assert args.output is not None
        raw = args.record.read_bytes()
        saved = json.loads(raw)
        assert saved["source_sha256"] == source_sha
        assert saved["inputs"] == json.loads(json.dumps(INPUTS))
        assert saved["proof"] == proof
        result = {"status": "PASS: complete direct proof cold replay",
                  "source_sha256": source_sha, "record_sha256": digest(raw),
                  "cases": 2, "transported_zero_witnesses": 312,
                  "seconds": time.monotonic() - start, "optimizer_calls": 0}
        write(args.output, result)
    print(json.dumps({"status": proof["status"], "mode": args.mode,
                      "seconds": result["seconds"]}, sort_keys=True))


if __name__ == "__main__":
    main()
