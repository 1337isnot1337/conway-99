"""Compare frozen Z packing bounds with exact endpoint-activation bounds.

This consumes completed certificates. It does not reconstruct compatibility
graphs, search cliques, inspect a numerical point, or run an optimizer.
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
    "plan": ("f0-character-pool-model01/plan.json.gz", "b3179e520d5913530c7d3cfae27529b5717be26c763de024b725c38959aa2aef"),
    "preparation": ("f0-pair-orbit-packing-preparation01.json.gz", "09412183bb01527a6fa2aeb23623b95af925767d5067bb363f10a2a8f8254a13"),
    "scan": ("f0-pair-orbit-packing-scan01.json.gz", "1bbba3061689f8faaf8fadcf556c0097d2b190673ab063a675259c007508b2bb"),
    "cold": ("f0-pair-orbit-packing-scan01-cold.json", "c684243851efa7e12e9b9e5c7f857532421c1954233a5d9d6e24acfe5c826843"),
}
LEDGER = ("f0-pair-orbit-packing-scan01-ledger.jsonl.gz", "4c53542bc89575b799b9e3d8b5905ae3dfe9782aa954db9d9afdf2a07c83d839")


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def run(root, deadline):
    data = {}
    for key, (name, digest) in INPUTS.items():
        raw = (root / BASE / name).read_bytes()
        assert sha(raw) == digest
        data[key] = json.loads(gzip.decompress(raw) if name.endswith(".gz") else raw)
    cold, scan = data["cold"], data["scan"]
    assert cold["status"].startswith("PASS") and cold["complete_saved_prefix_checked"]
    assert cold["checked_orbits"] == 9353 and scan["complete"]
    assert cold["record_sha256"] == INPUTS["scan"][1]
    assert cold["preparation_sha256"] == INPUTS["preparation"][1]
    scopes = data["preparation"]["scope"]["retained_orbits"]
    selector_orbits = data["domains"]["selector_orbits"]
    domains = data["plan"]["target_variable_domains"]
    assert data["plan"]["old_to_target_columns"][:15038] == list(range(15038))
    maxima = [d[-1] for d in domains[:42]]
    pairs = list(combinations(range(480), 2))
    raw = (root / BASE / LEDGER[0]).read_bytes()
    assert sha(raw) == LEDGER[1] == scan["ledger_sha256"]
    rows = [json.loads(line) for line in gzip.decompress(raw).splitlines()]
    assert len(rows) == len(scopes) == 9353
    records, tally, degree_checks = [], Counter(), 0
    for row, scope in zip(rows, scopes):
        if time.monotonic() >= deadline:
            raise TimeoutError("activation comparison deadline")
        po, column = scope["pair_orbit"], scope["count_column"]
        assert row["pair_orbit"] == po and row["count_column"] == column
        current = domains[column][-1]
        assert current == scope["current_domain"][-1] == row["previous_current_upper_bound"]
        bound = row["maximum_compatible_pair_objects"]
        literal = [pairs[k] for k in scope["literal_pair_ids"]]
        i, j = scope["selector_orbits"]
        assert [i, j] == data["domains"]["pair_orbit_selector_blocks"][po]
        record = {"pair_orbit": po, "count_column": column, "selector_orbits": [i, j],
                  "packing_upper_bound": bound, "current_pair_upper_bound": current,
                  "packing_stricter_than_current_box": bound < current}
        tally["retained_orbits"] += 1
        tally["packing_stricter_than_current_box"] += bound < current
        if i == j:
            assert all(a in selector_orbits[i] and b in selector_orbits[i] for a, b in literal)
            record["scope"] = "within-orbit; compare only with the existing profile-derived domain"
            tally["within_orbit"] += 1
            tally["within_orbit_packing_stricter_than_current_domain"] += bound < current
        else:
            left, right = set(selector_orbits[i]), set(selector_orbits[j])
            assert not left & right
            assert all((a in left and b in right) or (b in left and a in right) for a, b in literal)
            n = len(literal)
            assert n % len(left) == n % len(right) == 0
            left_degree, right_degree = n // len(left), n // len(right)
            endpoint_counts = Counter(a for pair in literal for a in pair)
            assert all(endpoint_counts[a] == left_degree for a in left)
            assert all(endpoint_counts[a] == right_degree for a in right)
            degree_checks += len(left) + len(right)
            endpoint_bounds = [left_degree * maxima[i], right_degree * maxima[j]]
            activation = min(endpoint_bounds)
            record.update(scope="cross-orbit", endpoint_degrees=[left_degree, right_degree],
                          selector_population_upper_bounds=[maxima[i], maxima[j]],
                          endpoint_activation_upper_bounds=endpoint_bounds,
                          inherited_activation_upper_bound=activation,
                          packing_stricter_than_activation=bound < activation,
                          packing_stricter_than_both_current_and_activation=bound < min(current, activation))
            tally["cross_orbit"] += 1
            tally["cross_packing_stricter_than_activation"] += bound < activation
            tally["cross_packing_stricter_than_both_current_and_activation"] += bound < min(current, activation)
            tally["cross_current_box_improvements_not_below_activation"] += bound < current and bound >= activation
        records.append(record)
    assert tally["packing_stricter_than_current_box"] == len(scan["summary"]["improved_current_bounds"])
    assert tally["cross_orbit"] + tally["within_orbit"] == 9353
    return {"status": "PASS: exact endpoint-activation comparison of the frozen complete packing census",
            "inputs": INPUTS, "ledger": LEDGER,
            "current_selector_population_upper_bounds": maxima,
            "summary": dict(tally), "literal_uniform_endpoint_degree_checks": degree_checks,
            "records": records, "maximum_clique_searches": 0, "compatibility_graphs_reconstructed": 0,
            "optimizer_calls": 0, "candidate_points_loaded": 0,
            "independence_from_all_existing_inequalities_claimed": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    start = time.monotonic()
    result = run(args.root, start + 10)
    result.update(source_sha256=sha(Path(__file__).read_bytes()), seconds=time.monotonic() - start)
    raw = (json.dumps(result, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()
    with args.output.open("xb") as stream:
        stream.write(gzip.compress(raw, mtime=0))
    print(json.dumps({"status": result["status"], "summary": result["summary"], "seconds": result["seconds"]}))
