"""Exact weighted greedy clique proposals in the frozen local F0 graphs.

A local conflict clique permits at most one edge from its center. Hence
sum(Y_ba for a in clique) <= x_b, including repeated quotient columns.
Three deterministic orders and every singleton seed form the fixed search.
The search is not a maximum-weight or exhaustive clique algorithm.
"""
import argparse
from collections import Counter
import gzip
import hashlib
from itertools import product
import json
import math
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[2]
BASE = "experiments/logs/root-prism-free/"
INPUTS = {
    "inventory": (BASE+"f0-local-conflict-inventory01.json.gz", "cbfdad339ab84cb7eeb6b221e10be3c4c1db4fb70932de3a28e62ee4642cb7e0"),
    "cold_prefix": (BASE+"f0-local-conflict-inventory01-replay.json", "4717dc11e6f40007d58befc3ae968ceaaadb805c0548f797817846b3a0843be9"),
    "cold_suffix": (BASE+"f0-local-conflict-inventory01-suffix-replay.json", "ae85e2c9cbe19b72ad23231c6ee28ac135098eb078088780d4bd0988bd28cb5e"),
    "domain": (BASE+"f0-boolean-fractional-model.json.gz", "703206929c9c85a40ac4ddcbfb1708c716c288482cf50c77a32249404e35b782"),
    "point": (BASE+"f0-schur-path-query-run01/numerical.json", "bfe03cf2ec0f9d00ee7ff756112a61ab368404d4ed29c7b50377f01c5ae8327e"),
    "model": (BASE+"f0-schur-path-model03.json.gz", "ad046fc05a4247a081b3cabb16693682fa5539ff557dd7b599f3c3a63e7303dd"),
}
ORDER_NAMES = ("weight", "weight_times_degree_plus_one", "degree_then_weight")


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def indices(bits):
    assert type(bits) is int and bits >= 0
    while bits:
        low = bits & -bits
        yield low.bit_length()-1
        bits ^= low


def row_from_clique(center, clique):
    coefficients = Counter({center["orbit_id"]: -1})
    for i in clique:
        coefficients[center["neighbor_quotient_Y_columns"][i]] += 1
    return {"terms": [[j, c] for j, c in sorted(coefficients.items()) if c], "rhs": 0}


def row_key(row):
    return canonical([row["terms"], row["rhs"]]).decode()


def controls():
    activation = 0
    for n in range(1, 8):
        for b in (0, 1):
            for neighbors in product((0, 1), repeat=n):
                if all(y <= b for y in neighbors) and sum(neighbors) <= 1:
                    assert sum(neighbors) <= b
                    activation += 1
    aliases = 0
    for labels in product(range(42, 45), repeat=4):
        center = {"orbit_id": 0, "neighbor_quotient_Y_columns": labels}
        row = row_from_clique(center, list(range(4)))
        values = {0: 7, 42: 2, 43: 3, 44: 5}
        assert sum(c*values[j] for j, c in row["terms"]) == sum(values[j] for j in labels)-7
        aliases += 1
    return {"Boolean_activation_cases": activation, "quotient_alias_cases": aliases, "no_orbit_size_division": True}


def load():
    data = {}
    for name, (path, expected) in INPUTS.items():
        raw = (ROOT/path).read_bytes()
        assert sha(raw) == expected, name
        data[name] = json.loads(gzip.decompress(raw) if path.endswith(".gz") else raw)
    inv = data["inventory"]
    assert inv["complete_centers"] == 42 and inv["literal_centers_covered"] == 480
    assert data["cold_suffix"]["status"].startswith("PASS:")
    assert data["cold_suffix"]["prefix_centers"] == 20 and data["cold_suffix"]["fresh_suffix_centers"] == 22
    assert data["cold_prefix"]["completed_center_records"] == inv["representative_records"][:20]
    assert sha(canonical(inv)) == data["cold_suffix"]["production_record_raw_sha256"]
    domain = data["domain"]["validation"]
    xmap = {v: o for o, group in enumerate(domain["selector_orbits"]) for v in group}
    emap = {v: 42+o for o, group in enumerate(domain["edge_orbits"]) for v in group}
    for center in inv["representative_records"]:
        b = center["center"]; neighbors = center["neighbor_ids"]
        assert center["orbit_id"] == xmap[b] and len(set(neighbors)) == len(neighbors)
        assert center["degree_from_quotas"] == 8 and len(center["mixed_quotas"]) == 18
        adjacency = [int(s, 16) for s in center["full_conflict_adjacency_hex"]]
        n = len(neighbors)
        assert len(adjacency) == len(center["neighbor_edge_ids"]) == len(center["neighbor_quotient_Y_columns"]) == n
        for i, a in enumerate(neighbors):
            edge_id = center["neighbor_edge_ids"][i]
            assert domain["edges"][edge_id] == sorted((a, b))
            assert center["neighbor_quotient_Y_columns"][i] == emap[edge_id]
            assert adjacency[i].bit_length() <= n and not (adjacency[i] >> i & 1)
            assert all(adjacency[j] >> i & 1 for j in indices(adjacency[i]))
    point = data["point"]
    assert point["model_sha256"] == "7bc4682e3df009761c55d0740a30a0629d45e894807f79e3337fc1de4fa1aff3"
    values = [float.fromhex(s) for s in point["col_value_hex"]]
    assert len(values) == 15200 and all(math.isfinite(x) for x in values)
    ratios = [x.as_integer_ratio() for x in values]
    denominator = max(d for n, d in ratios)
    assert denominator & (denominator-1) == 0
    numerators = [n*(denominator//d) for n, d in ratios]
    assert all(denominator % d == 0 for n, d in ratios)
    # Only x and Y enter the objective; their nonnegativity makes the
    # weight-based greedy descriptions literal at this frozen proposal.
    assert all(n >= 0 for n in numerators[:5847])
    return data, numerators, denominator


def preparation():
    data, nums, den = load()
    centers = data["inventory"]["representative_records"]
    sizes = [[r["center"], len(r["neighbor_ids"])] for r in centers]
    assert len(sizes) == 42 and sum(n for b, n in sizes) == 11658 and max(n for b, n in sizes) == 339
    bound = 340*max(nums[:5847])
    return {"status": "PREPARED_FIXED_GREEDY_LOCAL_CLIQUE_SEARCH", "source_sha256": sha(Path(__file__).read_bytes()),
            "inputs": {k: {"path": p, "sha256": h} for k, (p, h) in INPUTS.items()},
            "center_neighbor_counts": sizes, "orders": list(ORDER_NAMES),
            "planned_singleton_seed_trials": 34974, "maximum_retained_new_rows": 128,
            "search_seconds_including_loading": 30, "exact_common_denominator": str(den),
            "absolute_gap_numerator_bound": str(bound), "gap_bound_bits": bound.bit_length(),
            "controls": controls(), "point_loaded": True, "greedy_trials_run": 0,
            "optimizer_calls": 0, "maximal_clique_census": False, "maximum_weight_proof": False}


def witness(center, selected, nums, den):
    selected = sorted(selected)
    assert len(selected) == len(set(selected)) and selected
    adjacency = [int(s, 16) for s in center["full_conflict_adjacency_hex"]]
    assert all(type(i) is int and 0 <= i < len(adjacency) for i in selected)
    for i in selected:
        assert all(i == j or adjacency[i] >> j & 1 for j in selected)
    row = row_from_clique(center, selected)
    value = sum(c*nums[j] for j, c in row["terms"])
    return {"center": center["center"], "local_indices": selected,
            "literal_neighbors": [center["neighbor_ids"][i] for i in selected],
            "terms": row["terms"], "rhs": 0, "gap_numerator": str(value), "gap_denominator": str(den)}


def scan(deadline):
    data, nums, den = load()
    parent = {row_key(row) for row in data["model"]["matrix"]["inequalities"]}
    completed = []; positive = {}; trials = 0; timed_out = False
    for center in data["inventory"]["representative_records"]:
        n = len(center["neighbor_ids"])
        adjacency = [int(s, 16) for s in center["full_conflict_adjacency_hex"]]
        weights = [nums[j] for j in center["neighbor_quotient_Y_columns"]]
        degrees = [a.bit_count() for a in adjacency]
        keys = [lambda i: (-weights[i], i),
                lambda i: (-weights[i]*(degrees[i]+1), -weights[i], i),
                lambda i: (-degrees[i], -weights[i], i)]
        for order_name, key in zip(ORDER_NAMES, keys):
            order = sorted(range(n), key=key); inverse = {v: i for i, v in enumerate(order)}
            reordered = [sum(1 << inverse[j] for j in indices(adjacency[i])) for i in order]
            best = None; order_trials = 0
            for seed in range(n):
                if time.monotonic() >= deadline:
                    timed_out = True; break
                chosen = [seed]; available = reordered[seed]
                while available:
                    bit = available & -available; j = bit.bit_length()-1
                    chosen.append(j); available &= reordered[j]
                original = sorted(order[i] for i in chosen)
                value = sum(weights[i] for i in original)-nums[center["orbit_id"]]
                if best is None or (value, len(original), original) > (best[0], len(best[1]), best[1]):
                    best = (value, original)
                if value > 0:
                    proof = witness(center, original, nums, den); row_id = row_key(proof)
                    if row_id not in parent:
                        positive.setdefault(row_id, proof)
                trials += 1; order_trials += 1
            completed.append({"center": center["center"], "order": order_name, "completed_seeds": order_trials,
                              "planned_seeds": n, "best": None if best is None else witness(center, best[1], nums, den)})
            if timed_out:
                break
        if timed_out:
            break
    retained = sorted(positive.values(), key=lambda row: (-int(row["gap_numerator"]), row["center"], row["local_indices"]))[:128]
    return {"status": "COMPLETE_FIXED_GREEDY_TRIALS" if not timed_out else "PARTIAL_FIXED_GREEDY_TRIALS",
            "source_sha256": sha(Path(__file__).read_bytes()), "exact_common_denominator": str(den),
            "completed_trials": trials, "order_results": completed,
            "distinct_positive_new_rows_before_cap": len(positive), "rows": retained,
            "optimizer_calls": 0, "point_feasibility_claimed": False,
            "maximal_clique_census": False, "maximum_weight_proof": False}


def replay(record):
    data, nums, den = load()
    centers = {r["center"]: r for r in data["inventory"]["representative_records"]}
    assert record["source_sha256"] == sha(Path(__file__).read_bytes())
    assert record["exact_common_denominator"] == str(den)
    seen = set(); parent = {row_key(r) for r in data["model"]["matrix"]["inequalities"]}
    for row in record["rows"]:
        assert row == witness(centers[row["center"]], row["local_indices"], nums, den)
        assert int(row["gap_numerator"]) > 0
        key = row_key(row); assert key not in seen and key not in parent; seen.add(key)
    for order in record["order_results"]:
        assert order["order"] in ORDER_NAMES and 0 <= order["completed_seeds"] <= order["planned_seeds"]
        if order["best"] is not None:
            row = order["best"]
            assert row == witness(centers[row["center"]], row["local_indices"], nums, den)
    assert sum(o["completed_seeds"] for o in record["order_results"]) == record["completed_trials"]
    assert len(record["rows"]) <= 128
    return {"status": "PASS: local clique witnesses, quotient rows and dyadic gaps", "retained_rows": len(record["rows"]),
            "saved_best_cliques_replayed": sum(o["best"] is not None for o in record["order_results"]),
            "search_repeated": False, "optimality_claimed": False, "optimizer_calls": 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "scan", "replay"))
    parser.add_argument("--preparation", type=Path, required=True)
    parser.add_argument("--record", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(); started = time.monotonic()
    assert not args.output.exists()
    if args.mode == "prepare":
        assert not args.preparation.exists()
        result = preparation(); args.preparation.write_text(json.dumps(result, indent=2)+"\n")
    else:
        prep = json.loads(args.preparation.read_bytes())
        assert prep["source_sha256"] == sha(Path(__file__).read_bytes())
        assert prep["inputs"] == {k: {"path": p, "sha256": h} for k, (p, h) in INPUTS.items()}
        if args.mode == "scan":
            assert not args.record.exists(); result = scan(started+30)
            result["preparation_sha256"] = sha(args.preparation.read_bytes())
            args.record.write_text(json.dumps(result, indent=2)+"\n")
        else:
            saved = json.loads(args.record.read_bytes())
            assert saved["preparation_sha256"] == sha(args.preparation.read_bytes())
            result = replay(saved); result["record_sha256"] = sha(args.record.read_bytes())
    summary = {k: v for k, v in result.items() if k not in ("order_results", "rows")}
    summary["seconds"] = time.monotonic()-started
    args.output.write_text(json.dumps(summary, indent=2)+"\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
