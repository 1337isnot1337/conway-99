"""Reuse exact local packing potentials at every eligible anchor.

For any anchor a, integer site potential v and nonnegative pair potential mu,
let t = v.q_a - sum(mu), and w_b = max(v.h_b - sum_{p subset h_b} mu_p, 0).
Then t*x_a <= sum_{b in N(a)} w_b*x_b. The potential need not originate at a
or from an automorphism taking another anchor to a. This script exhausts
all 480 anchors for each of the 24 newly certified potentials. No solver
is imported. Complete raw weights and origins permit direct arithmetic replay.
"""
import argparse
from collections import Counter
import gzip
import hashlib
from itertools import combinations
import json
from math import gcd
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[2]
LOGS = "experiments/logs/root-prism-free/"
INPUTS = {'baseline': ('experiments/logs/root-prism-free/f0-boolean-fractional-model.json.gz', '703206929c9c85a40ac4ddcbfb1708c716c288482cf50c77a32249404e35b782'), 'domain': ('experiments/logs/root-prism-free/f0-exterior-row-domains02.json.gz', '665563b75fa6fc23caa9a002621cc4047809af28543b52b5c2a7ffa592d05dd4'), 'potentials4': ('experiments/logs/root-prism-free/f0-local-packing-candidate-batch-run01/anchor-004/pending-cuts.json', 'd6f0a918274c3dbf98f971a2ada760b5b2cafb5996000e5b2ea95ec0e19196ca'), 'potentials202': ('experiments/logs/root-prism-free/f0-local-packing-candidate-batch-run01/anchor-202/pending-cuts.json', '0f711530ba913b866a88453fa562302b3bc09bd6d40c9248c94080c553c733dc'), 'cuts': ('experiments/logs/root-prism-free/f0-local-packing-candidate-batch-run01-cold/certified-selector-cuts.json', 'aa3f64e1bb463edc9449148729d3e53042e8665cf17cdc730975daedacc9a1a7'), 'cold': ('experiments/logs/root-prism-free/f0-local-packing-candidate-batch-run01-cold/report.json', '8e0464c347dd87968fcbc528725a7e0124018691f9d1c65694d4ae4db37146d2'), 'owner': ('experiments/logs/root-prism-free/f0-local-packing-candidate-batch-run01-cold/owner.json', '5f8ad93f6dbde009ca1f88e63c966140d2783e71aea761b01e052d2e8e353687'), 'prefix': ('experiments/logs/root-prism-free/f0-direct-master-preparation03/initial-registry.json', '4c5ed8915a423964272d71130532ba273d18db74b77fe1380d0c1b72b394d1d7')}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(item):
    path, expected = item
    raw = (ROOT / path).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == expected, path
    return json.loads(gzip.decompress(raw) if path.endswith(".gz") else raw)


def normalized(terms):
    terms = sorted([a, c] for a, c in terms if c)
    assert len(terms) == len({a for a, c in terms})
    divisor = gcd(*(abs(c) for a, c in terms)) or 1
    return [[a, c // divisor] for a, c in terms]


def derive():
    data = {key: load(item) for key, item in INPUTS.items()}
    owner, cold = data["owner"], data["cold"]
    assert owner["report_accepted"] and owner["deadline_overrun_seconds"] == 0
    assert owner["report_sha256"] == INPUTS["cold"][1]
    assert owner["supervision"]["child_reaped"]
    assert cold["status"] == "PASS_COLD_EXACT_LOCAL_PACKING_BATCH"
    assert owner["certified_new_cuts"]
    assert data["cuts"]["cold_owner_sha256"] == INPUTS["owner"][1]
    assert data["cuts"]["cold_report_sha256"] == INPUTS["cold"][1]
    assert data["cuts"]["rows_upper_zero"] == cold["rows_upper_zero"]
    baseline, domain = data["baseline"]["validation"], data["domain"]
    core, triples = baseline["core"], baseline["triples"]
    assert len(core) == 21 and len(triples) == 480
    assert core == domain["component_core_rows"] and triples == domain["signature_domain"]
    assert len(set(map(tuple, triples))) == 480
    assert all(h == sorted(set(h)) and len(h) == 3 and 0 <= h[0] < h[-1] < 18 for h in triples)
    assert all(not (core[i] >> i & 1) for i in range(21))
    assert all((core[i] >> j & 1) == (core[j] >> i & 1) for i in range(21) for j in range(21))
    adjacency = [(r >> 3) & ((1 << 18) - 1) for r in core[3:]]
    targets = [[2 - int(i in h) - sum(adjacency[i] >> j & 1 for j in h)
                for i in range(18)] for h in triples]
    assert targets == domain["row_targets"]
    assert all(sum(q) == 24 and all(x in (0, 1, 2) for x in q) for q in targets)
    neighbors = [[] for _ in triples]
    edges = baseline["edges"]
    assert len(edges) == len(set(map(tuple, edges))) == 68394
    for a, b in edges:
        assert 0 <= a < b < 480
        neighbors[a].append(b)
        neighbors[b].append(a)
    neighbors = list(map(sorted, neighbors))
    assert neighbors == domain["possible_neighbor_signature_ids"]
    hsets = list(map(set, triples))
    for a in range(480):
        direct = [b for b in range(480) if b != a and len(hsets[a] & hsets[b]) <= 1
                  and all(targets[a][i] > 0 for i in triples[b])
                  and all(targets[b][i] > 0 for i in triples[a])]
        assert direct == neighbors[a]
    pairs = list(combinations(range(18), 2))
    pair_position = {p: k for k, p in enumerate(pairs)}
    pair_ids = [[pair_position[p] for p in combinations(h, 2)] for h in triples]
    potentials = [{"v": item["form"]["v"], "mu": item["form"]["mu"]}
                  for key in ("potentials4", "potentials202") for item in data[key]["all12_transports"]]
    assert len(potentials) == 24 and len({canonical(p) for p in potentials}) == 24
    original = {canonical(row) for row in data["cuts"]["rows_upper_zero"]}
    frozen = {canonical(entry["row"]) for entry in data["prefix"]}
    assert len(frozen) == len(data["prefix"]) == 157
    rows, attempts, positive_demands = {}, [], Counter()
    for potential_id, p in enumerate(potentials):
        v, mu = p["v"], p["mu"]
        assert len(v) == 18 and len(mu) == 153
        assert all(type(x) is int for x in v)
        assert all(type(x) is int and x >= 0 for x in mu)
        weights = [max(0, sum(v[i] for i in h) - sum(mu[k] for k in pair_ids[b]))
                   for b, h in enumerate(triples)]
        for anchor in range(480):
            demand = sum(v[i] * targets[anchor][i] for i in range(18)) - sum(mu)
            if demand <= 0:
                attempts.append([potential_id, anchor, demand, None])
                continue
            positive = [[b, weights[b]] for b in neighbors[anchor] if weights[b] > 0]
            raw = normalized([[anchor, demand]] + [[b, -w] for b, w in positive])
            # Saturation is exactly equivalent for binary selectors and positive demand.
            capped = normalized([[anchor, demand]] + [[b, -min(w, demand)] for b, w in positive])
            key = canonical(raw)
            item = rows.setdefault(key, {"row": {"terms": raw, "rhs": 0},
                                         "binary_capped_row": {"terms": capped, "rhs": 0},
                                         "origins": []})
            assert item["binary_capped_row"]["terms"] == capped
            item["origins"].append({"potential_id": potential_id, "anchor": anchor,
                                     "demand": demand, "full_positive_neighbor_weights": positive})
            attempts.append([potential_id, anchor, demand, hashlib.sha256(key).hexdigest()])
            positive_demands[demand] += 1
    assert original <= set(rows)
    ordered = [rows[k] for k in sorted(rows)]
    for item in ordered:
        item["already_in_original24"] = canonical(item["row"]["terms"]) in original
        item["already_in_frozen157"] = canonical(item["row"]) in frozen
    return {"schema": "conway99.f0.local-packing-new-bank-reanchoring.v1",
            "status": "PASS_EXACT_ALL_ANCHOR_POTENTIAL_CENSUS",
            "source_sha256": digest(__file__), "inputs": INPUTS,
            "proof": "Mixed row equalities and each common-core-pair capacity give t*x_a <= sum(w_b*x_b). At x_a=0 the right side is nonnegative. At x_a=1, replacing any positive w_b by min(w_b,t) preserves the inequality for binary selectors.",
            "potential_bank": potentials, "attempts": attempts, "rows": ordered,
            "counts": {"anchors": 480, "potentials": 12, "anchor_potential_pairs": len(attempts),
                       "positive_demand_pairs": sum(positive_demands.values()), "distinct_rows": len(rows),
                       "original_rows": len(original), "additional_rows": len(rows) - len(original),
                       "positive_demands": dict(sorted(positive_demands.items())),
                       "new_rows_vs_frozen157": sum(not item["already_in_frozen157"] for item in ordered)},
            "full_eligible_domain_reconstructed": True, "candidate_selection_used": False,
            "optimizer_calls": 0, "whole_component_excluded": False}


if __name__ == "__main__":
    if not __debug__:
        raise RuntimeError("assertions required")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    started = time.monotonic()
    record = derive()
    record["seconds"] = time.monotonic() - started
    with args.output.open("xb") as out:
        raw = canonical(record) + b"\n"
        out.write(gzip.compress(raw, mtime=0) if args.output.suffix == ".gz" else raw)
    print(json.dumps({"output": str(args.output), "sha256": digest(args.output),
                      "counts": record["counts"], "seconds": record["seconds"]}, sort_keys=True))
