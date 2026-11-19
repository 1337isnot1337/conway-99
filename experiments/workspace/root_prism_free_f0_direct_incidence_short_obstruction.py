"""Direct integer verification of the four-row 126 <= 117 obstruction."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = "experiments/logs/root-prism-free/"
INPUTS = {
    "baseline": (BASE + "f0-boolean-fractional-model.json.gz", "703206929c9c85a40ac4ddcbfb1708c716c288482cf50c77a32249404e35b782"),
    "model": (BASE + "f0-fixed-selection-exterior-direct01/model.json", "ec482e37e989a4657a0f7efb801c875062575fa2786efea72ba37c111974b3a9"),
    "potentials": (BASE + "f0-direct-incidence-shared-separation-run01/universal-cuts.json", "22afff749b73ecc41cde7c8afac2ad67d262524f08b0607901a3967aa3484294"),
}


def calculate():
    loaded = {}
    for key, (name, expected) in INPUTS.items():
        raw = (ROOT / name).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == expected
        loaded[key] = json.loads(gzip.decompress(raw) if name.endswith(".gz") else raw)
    base = loaded["baseline"]["validation"]
    data = loaded["model"]["data"]
    core, triples = base["core"], base["triples"]
    selected, design = data["design_source_indices"], data["design"]
    assert selected == sorted(set(selected)) and len(selected) == 60
    assert design == [triples[a] for a in selected]
    adjacency = [(row >> 3) & ((1 << 18) - 1) for row in core[3:]]
    assert adjacency == data["component_adjacency_rows"]
    for i in range(18):
        for j in range(i, 18):
            required = 12 * (i == j) + 2 - (core[3 + i] & core[3 + j]).bit_count() - (core[3 + i] >> (3 + j) & 1)
            assert sum(i in h and j in h for h in design) == required
    targets = [[2 - int(i in h) - sum(adjacency[i] >> j & 1 for j in h)
                for i in range(18)] for h in design]
    assert targets == data["targets"]
    eligible = []
    for a in range(60):
        for b in range(a):
            if (len(set(design[a]) & set(design[b])) <= 1
                    and all(targets[a][i] > 0 for i in design[b])
                    and all(targets[b][i] > 0 for i in design[a])):
                eligible.append([a, b])
    assert eligible == data["edge_domain"] and len(eligible) == 1219
    potentials = dict(loaded["potentials"]["nonzero_target_potentials"])
    assert set(potentials) == {106, 240, 318, 392}
    rows = {}
    for anchor, vector in sorted(potentials.items()):
        assert len(vector) == 18 and all(type(x) is int for x in vector)
        a = selected.index(anchor)
        neighbors = sorted(b if a == c else c for b, c in eligible if a in (b, c))
        weights = {selected[b]: sum(vector[i] for i in design[b]) for b in neighbors}
        demand = sum(v * q for v, q in zip(vector, targets[a]))
        rows[anchor] = {"potential": vector, "demand": demand,
                        "neighbor_coefficients": [[b, weights[b]] for b in sorted(weights)]}
        if anchor == 106:
            assert demand == 54
            assert {b: w for b, w in weights.items() if w > 0} == {240: 60, 318: 6, 447: 21}
        elif anchor == 392:
            assert demand == 72
            assert {b: w for b, w in weights.items() if w > 0} == {152: 12, 240: 60, 318: 12, 443: 12}
        elif anchor == 240:
            assert demand == -60
            assert {b: w for b, w in weights.items() if w} == {106: -60, 171: -60, 309: -60, 392: -60}
        else:
            assert demand == -6 and weights[106] == -6 and weights[392] == -12
            assert {b: w for b, w in weights.items() if w > 0} == {136: 6}
    assert sum(row["demand"] for row in rows.values()) == 60
    positive_shared = []
    for a, b in eligible:
        u, v = selected[a], selected[b]
        weight = (sum(potentials.get(u, [0] * 18)[i] for i in design[b])
                  + sum(potentials.get(v, [0] * 18)[i] for i in design[a]))
        if weight > 0:
            positive_shared.append([min(u, v), max(u, v), weight])
    positive_shared.sort()
    assert positive_shared == [[106, 447, 21], [136, 318, 6], [152, 392, 12], [392, 443, 12]]
    assert sum(w for a, b, w in positive_shared) == 51
    return {"status": "PASS: exact four-row shared-edge contradiction",
            "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "inputs": INPUTS, "selected_signature_ids": selected,
            "row_certificates": rows, "positive_shared_edges": positive_shared,
            "shared_total_demand": 60, "shared_positive_capacity": 51, "strict_integer_gap": 9,
            "short_variables": {"e": [106, 240], "f": [106, 318], "g": [392, 240], "h": [392, 318]},
            "short_bounds": ["54 <= 60e+6f+21", "72 <= 60g+12h+24", "e+g <= 1", "f+2h <= 2"],
            "contradictory_lower": 126, "contradictory_upper": 117,
            "integer_edges_required": False, "outside_pair_caps_required": False,
            "second_component_fixed": False, "whole_component_excluded": False,
            "optimizer_calls": 0}


if __name__ == "__main__":
    if not __debug__:
        raise RuntimeError("assertions are required")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = calculate()
    with args.output.open("x") as out:
        json.dump(result, out, indent=2, sort_keys=True)
        out.write("\n")
    print(json.dumps({"status": result["status"], "strict_integer_gap": 9,
                      "report_sha256": hashlib.sha256(args.output.read_bytes()).hexdigest()}))
