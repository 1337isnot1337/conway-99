"""Exact exterior common-neighbor checks and positive-edge circuit cuts.

For selected signatures a,b, an SRG completion requires
    common_D(a,b) + y_ab <= 2 - |h_a intersection h_b|.
Every reported cut forbids a minimal positive-edge witness to a violation.
No solver or model producer is imported. Passing these caps is not a graph.
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
DOMAIN = ("experiments/logs/root-prism-free/f0-exterior-row-domains02.json.gz",
          "665563b75fa6fc23caa9a002621cc4047809af28543b52b5c2a7ffa592d05dd4")


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def load_domain():
    raw = (ROOT / DOMAIN[0]).read_bytes()
    assert digest(raw) == DOMAIN[1]
    saved = json.loads(gzip.decompress(raw))
    core = saved["component_core_rows"]
    assert len(core) == 21 and all(type(v) is int and 0 <= v < 1 << 21 for v in core)
    assert all(not (core[i] >> i & 1) for i in range(21))
    assert all((core[i] >> j & 1) == (core[j] >> i & 1) for i in range(21) for j in range(21))
    gram = [[12 * int(i == j) + 2 - (core[i+3] & core[j+3]).bit_count()
             - (core[i+3] >> (j+3) & 1) for j in range(18)] for i in range(18)]
    triples = []
    for h in combinations(range(18), 3):
        if len({i // 6 for i in h}) == 1:
            continue
        if any(gram[i][j] == 0 for i, j in combinations(h, 2)):
            continue
        if any(sum(int(i == j or core[i+3] >> (j+3) & 1) for j in h) > 2 for i in range(18)):
            continue
        triples.append(list(h))
    assert len(triples) == 480 and triples == saved["signature_domain"]
    targets = [[2 - int(i in h) - sum(core[i+3] >> (j+3) & 1 for j in h)
                for i in range(18)] for h in triples]
    assert targets == saved["row_targets"]
    masks = [sum(1 << i for i in h) for h in triples]
    edges, neighbors = [], [[] for _ in triples]
    for a, b in combinations(range(480), 2):
        if (masks[a] & masks[b]).bit_count() > 1:
            continue
        if any(targets[a][i] == 0 for i in triples[b]) or any(targets[b][i] == 0 for i in triples[a]):
            continue
        edges.append((a, b)); neighbors[a].append(b); neighbors[b].append(a)
    assert len(edges) == 68394 and neighbors == saved["possible_neighbor_signature_ids"]
    return triples, targets, gram, edges


def adjacency(n, edges, bits):
    assert len(edges) == len(bits) and all(type(v) is int and v in (0, 1) for v in bits)
    result = [set() for _ in range(n)]
    for (a, b), value in zip(edges, bits):
        assert type(a) is int and type(b) is int and 0 <= a < b < n
        if value:
            result[a].add(b); result[b].add(a)
    return result


def verify_circuit(triples, edges, edge_ids, witness):
    a, b = witness["pair"]
    assert type(a) is int and type(b) is int and 0 <= a < b < len(triples)
    common = witness["common_vertices"]
    include = witness["include_pair_edge"]
    assert type(include) is int and include in (0, 1)
    assert common == sorted(set(common)) and all(type(v) is int and 0 <= v < len(triples) and v not in (a, b) for v in common)
    overlap = len(set(triples[a]) & set(triples[b]))
    assert 0 <= overlap <= 2 and witness["core_overlap"] == overlap
    assert len(common) + include + overlap == 3
    expected = {tuple(sorted((v, w))) for v in (a, b) for w in common}
    if include:
        expected.add((a, b))
    assert edge_ids == sorted(set(edge_ids)) and all(type(e) is int and 0 <= e < len(edges) for e in edge_ids)
    assert {tuple(edges[e]) for e in edge_ids} == expected
    assert len(edge_ids) == 2 * len(common) + include
    return True


def inspect_pairs(triples, edges, neighbors, selected):
    assert selected == sorted(set(selected))
    assert all(type(v) is int and 0 <= v < len(triples) for v in selected)
    assert len(neighbors) == len(triples)
    lookup = {tuple(pair): e for e, pair in enumerate(edges)}
    assert len(lookup) == len(edges)
    violations, by_edges = [], {}
    for a, b in combinations(selected, 2):
        overlap = len(set(triples[a]) & set(triples[b]))
        assert 0 <= overlap <= 2
        common = sorted(neighbors[a] & neighbors[b])
        adjacent = int(b in neighbors[a])
        assert adjacent == int(a in neighbors[b])
        if len(common) + adjacent <= 2 - overlap:
            continue
        violations.append({"pair": [a, b], "core_overlap": overlap, "adjacent": adjacent,
                           "common_vertices": common, "left": len(common) + adjacent, "upper": 2 - overlap})
        for include in range(adjacent + 1):
            needed = 3 - overlap - include
            for subset in combinations(common, needed):
                pairs = {tuple(sorted((v, w))) for v in (a, b) for w in subset}
                if include:
                    pairs.add((a, b))
                ids = tuple(sorted(lookup[pair] for pair in pairs))
                witness = {"pair": [a, b], "core_overlap": overlap,
                           "include_pair_edge": include, "common_vertices": list(subset)}
                verify_circuit(triples, edges, list(ids), witness)
                assert all(v in neighbors[u] for u, v in pairs)
                by_edges.setdefault(ids, []).append(witness)
    circuits = [{"edge_ids": list(ids), "upper": len(ids) - 1, "witnesses": witnesses}
                for ids, witnesses in sorted(by_edges.items())]
    assert bool(circuits) == bool(violations)
    return violations, circuits


def inspect_vector(vector):
    triples, targets, gram, edges = load_domain()
    assert isinstance(vector, list) and len(vector) == 68934
    assert all(type(v) is int for v in vector)
    assert all(v in (0, 1) for v in vector[:480] + vector[540:])
    selected = [a for a, value in enumerate(vector[:480]) if value]
    assert len(selected) == 60
    neighbors = adjacency(480, edges, vector[540:])
    for a in range(480):
        assert len(neighbors[a]) == 8 * vector[a]
        assert all(vector[b] for b in neighbors[a])
        for i in range(18):
            assert sum(i in triples[b] for b in neighbors[a]) == targets[a][i] * vector[a]
    for i in range(18):
        for j in range(i, 18):
            assert sum(i in triples[a] and j in triples[a] for a in selected) == gram[i][j]
    violations, circuits = inspect_pairs(triples, edges, neighbors, selected)
    assert all(2 <= len(c["edge_ids"]) <= 6 for c in circuits)
    return {"status": "EXACT_PAIR_CAP_VIOLATIONS" if violations else "PASS_PAIR_CAPS_RESIDUAL_UNRESOLVED",
            "selected_signature_ids": selected, "selected_edge_ids": [e for e, bit in enumerate(vector[540:]) if bit],
            "checks": {"population": 60, "degree_equations": 480, "mixed_equations": 8640,
                       "original_Gram_entries": 171, "selected_pairs": 1770},
            "violations": violations, "circuits": circuits,
            "circuit_size_histogram": dict(sorted(Counter(len(c["edge_ids"]) for c in circuits).items())),
            "edge_variable_offset": 540, "all_circuit_activities_exceed_upper_by": 1,
            "all_minimal_positive_circuits_on_violated_pairs_retained": True,
            "all_parent_linear_rows_checked": False, "all_second_component_conditions_checked": False,
            "graph_constructed": False, "whole_component_excluded": False, "optimizer_calls": 0}


def controls():
    edges = list(combinations(range(5), 2))
    assignments = 0
    circuit_checks = 0
    # Direct dense A^2+A is the independent reference for all 1024 graphs.
    # Each layout gives the designated pair overlap zero, one, or two.
    for overlap in range(3):
        first = [0, 1, 2]
        second = first[:overlap] + list(range(3, 6 - overlap))
        triples = [first, second, [6, 7, 8], [9, 10, 11], [12, 13, 14]]
        for mask in range(1 << len(edges)):
            bits = [mask >> e & 1 for e in range(len(edges))]
            neighbors = adjacency(5, edges, bits)
            matrix = [[int(j in neighbors[i]) for j in range(5)] for i in range(5)]
            direct = []
            for a, b in combinations(range(5), 2):
                left = sum(matrix[a][k] * matrix[k][b] for k in range(5)) + matrix[a][b]
                cap = 2 - len(set(triples[a]) & set(triples[b]))
                if left > cap:
                    direct.append([a, b])
            violations, circuits = inspect_pairs(triples, edges, neighbors, list(range(5)))
            assert [v["pair"] for v in violations] == direct
            for circuit in circuits:
                assert sum(bits[e] for e in circuit["edge_ids"]) == circuit["upper"] + 1
                for witness in circuit["witnesses"]:
                    verify_circuit(triples, edges, circuit["edge_ids"], witness)
                    # Every proper subgraph of this witness satisfies its own
                    # designated pair cap; the full witness violates it.
                    ids = circuit["edge_ids"]
                    a, b = witness["pair"]
                    for submask in range(1 << len(ids)):
                        local_bits = [0] * len(edges)
                        for index, edge in enumerate(ids):
                            local_bits[edge] = submask >> index & 1
                        local = adjacency(5, edges, local_bits)
                        feasible = len(local[a] & local[b]) + int(b in local[a]) <= 2 - witness["core_overlap"]
                        assert feasible == (submask != (1 << len(ids)) - 1)
                    circuit_checks += 1
            assignments += 1
    return {"status": "PASS_EXHAUSTIVE_PAIR_CAP_AND_MINIMAL_CIRCUIT_CONTROLS",
            "five_vertex_graph_assignments": assignments, "minimal_witness_truth_tables": circuit_checks,
            "production_candidate_evaluations": 0, "optimizer_calls": 0}


def main():
    assert __debug__
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("controls", "inspect"))
    parser.add_argument("--candidate", type=Path)
    parser.add_argument("--candidate-sha256")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    started = time.monotonic()
    if args.mode == "controls":
        result = controls()
    else:
        assert args.candidate is not None and args.candidate_sha256 is not None
        raw = args.candidate.read_bytes()
        assert digest(raw) == args.candidate_sha256
        result = inspect_vector(json.loads(raw))
        result["candidate"] = {"path": str(args.candidate), "sha256": digest(raw)}
        result["domain"] = {"path": DOMAIN[0], "sha256": DOMAIN[1]}
    result["source"] = {"path": str(Path(__file__).resolve().relative_to(ROOT)), "sha256": digest(Path(__file__).read_bytes())}
    result["seconds"] = time.monotonic() - started
    with args.output.open("xb") as stream:
        stream.write(canonical(result) + b"\n")
    print(json.dumps({k: result[k] for k in ("status", "seconds")}), flush=True)


if __name__ == "__main__":
    main()
