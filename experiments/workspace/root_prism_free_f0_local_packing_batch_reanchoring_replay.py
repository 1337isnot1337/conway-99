"""Independent integer replay of every new-bank reanchored packing row."""
import argparse
import ast
from collections import Counter
import gzip
import hashlib
from itertools import combinations
import json
from math import gcd
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[2]
PRODUCER = "experiments/workspace/root_prism_free_f0_local_packing_batch_reanchoring_v2.py"
PRODUCER_SHA = "03be37e69e554d09e52696d3dd0a6d0be909e5261ac868f64363d57ec8b4663e"


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def primitive(terms):
    assert len(terms) == len({j for j, _ in terms})
    terms = sorted([j, c] for j, c in terms if c)
    divisor = gcd(*(abs(c) for _, c in terms)) or 1
    return [[j, c // divisor] for j, c in terms]


def replay(path):
    raw = path.read_bytes()
    record = json.loads(gzip.decompress(raw))
    producer = (ROOT / PRODUCER).read_bytes()
    assert sha(producer) == record["source_sha256"] == PRODUCER_SHA
    input_node = next(node for node in ast.parse(producer).body if isinstance(node, ast.Assign)
                      and any(isinstance(target, ast.Name) and target.id == "INPUTS" for target in node.targets))
    assert record["inputs"] == json.loads(canonical(ast.literal_eval(input_node.value)))
    data = {}
    for key, (name, expected) in record["inputs"].items():
        content = (ROOT / name).read_bytes()
        assert sha(content) == expected
        data[key] = json.loads(gzip.decompress(content) if name.endswith(".gz") else content)
    core = data["baseline"]["validation"]["core"]
    triples = data["baseline"]["validation"]["triples"]
    masks = [sum(1 << i for i in h) for h in triples]
    adjacency = [(r >> 3) & ((1 << 18) - 1) for r in core[3:]]
    targets = [[2 - ((m >> i) & 1) - (adjacency[i] & m).bit_count() for i in range(18)] for m in masks]
    assert targets == data["domain"]["row_targets"]
    neighbors = data["domain"]["possible_neighbor_signature_ids"]
    for a in range(480):
        assert neighbors[a] == [b for b in range(480) if b != a and (masks[a] & masks[b]).bit_count() <= 1
                               and all(targets[a][i] > 0 for i in triples[b])
                               and all(targets[b][i] > 0 for i in triples[a])]
    potentials = [{"v": row["form"]["v"], "mu": row["form"]["mu"]}
                  for key in ("potentials4", "potentials202") for row in data[key]["all12_transports"]]
    assert potentials == record["potential_bank"] and len(potentials) == 24
    pairs = list(combinations(range(18), 2))
    attempts, expected_rows, histogram, checked = [], {}, Counter(), 0
    for index, potential in enumerate(potentials):
        v, mu = potential["v"], potential["mu"]
        assert len(v) == 18 and all(type(x) is int for x in v)
        assert len(mu) == 153 and all(type(x) is int and x >= 0 for x in mu)
        multipliers = dict(zip(pairs, mu))
        for a in range(480):
            demand = sum(x * y for x, y in zip(v, targets[a])) - sum(mu)
            if demand <= 0:
                attempts.append([index, a, demand, None])
                continue
            positive = []
            for b in neighbors[a]:
                value = sum(v[i] for i in triples[b]) - sum(multipliers[p] for p in combinations(triples[b], 2))
                checked += 1
                if value > 0:
                    positive.append([b, value])
            row = primitive([[a, demand]] + [[b, -w] for b, w in positive])
            capped = primitive([[a, demand]] + [[b, -min(demand, w)] for b, w in positive])
            key = canonical(row)
            item = expected_rows.setdefault(key, {"row": {"terms": row, "rhs": 0},
                "binary_capped_row": {"terms": capped, "rhs": 0}, "origins": []})
            assert item["binary_capped_row"]["terms"] == capped
            item["origins"].append({"potential_id": index, "anchor": a, "demand": demand,
                                    "full_positive_neighbor_weights": positive})
            attempts.append([index, a, demand, sha(key)])
            histogram[demand] += 1
    assert attempts == record["attempts"] and len(attempts) == 11520
    original = {canonical(row) for row in data["cuts"]["rows_upper_zero"]}
    frozen = {canonical(entry["row"]) for entry in data["prefix"]}
    assert len(original) == 24 and len(frozen) == 157
    for key, item in expected_rows.items():
        item["already_in_original24"] = key in original
        item["already_in_frozen157"] = canonical(item["row"]) in frozen
    ordered = [expected_rows[key] for key in sorted(expected_rows)]
    assert ordered == record["rows"]
    fresh = [item["row"]["terms"] for item in ordered if not item["already_in_frozen157"]]
    counts = {"anchors": 480, "potentials": 24, "anchor_potential_pairs": 11520,
              "positive_demand_pairs": sum(histogram.values()), "distinct_rows": len(ordered),
              "original_rows": 24, "additional_rows": len(ordered) - 24,
              "positive_demands": {str(k): v for k, v in sorted(histogram.items())},
              "new_rows_vs_frozen157": len(fresh)}
    assert counts == record["counts"] and len(fresh) == 48
    return {"status": "PASS_INDEPENDENT_COMPLETE_REANCHORED_PACKING_ARITHMETIC",
            "source_sha256": sha(Path(__file__).read_bytes()), "producer_sha256": PRODUCER_SHA,
            "certificate_sha256": sha(raw), "counts": counts, "full_neighbor_coefficients_checked": checked,
            "new_rows_upper_zero_vs_frozen157": fresh,
            "new_rows_terms_range": [min(map(len, fresh)), max(map(len, fresh))],
            "maximum_absolute_new_coefficient": max(abs(c) for row in fresh for _, c in row),
            "maximum_absolute_new_activity": max(sum(abs(c) for _, c in row) for row in fresh),
            "all480_eligible_domains_reconstructed": True, "optimizer_calls": 0,
            "producer_imported": False, "whole_component_excluded": False}


if __name__ == "__main__":
    assert __debug__
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--certificate", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    started = time.monotonic()
    result = replay(args.certificate)
    result["seconds"] = time.monotonic() - started
    with args.output.open("xb") as stream:
        stream.write(canonical(result) + b"\n")
    print(json.dumps({"status": result["status"], "sha256": sha(args.output.read_bytes()),
                      "counts": result["counts"], "seconds": result["seconds"]}, sort_keys=True))
