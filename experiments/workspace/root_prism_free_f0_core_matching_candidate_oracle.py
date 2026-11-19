"""Exact eight-vertex core-matching tests for a supplied F0 literal selection.

Preparation and controls use no production candidate. Candidate input is an
explicit list of 60 selected signature IDs, never an inferred solver vector.
Every passing local matching is only a necessary condition. An impossible
matching yields a positive eight-selector clause under the original Ui=8
equation. Native/count acceptance is deliberately a separate receipt.
"""
import argparse
from collections import Counter
from functools import lru_cache
import gzip
import hashlib
from itertools import combinations
import json
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[2]
BASE = "experiments/logs/root-prism-free/"
INPUTS = {
    "model": (BASE + "f0-boolean-fractional-model.json.gz", "703206929c9c85a40ac4ddcbfb1708c716c288482cf50c77a32249404e35b782"),
    "domains": (BASE + "f0-orbit-populations02-domains.json.gz", "4f079468530dba0746512cc4afce01666b2a63a2c8f35f66a4660a4fe3bab8ab"),
    "matching": (BASE + "f0-core-matching-one-blossom01.json", "d5de76ce7978221843a44be9cca703e53c7153decb5088f598d016b7279088f8"),
    "matching_cold": (BASE + "f0-core-matching-one-blossom01-cold.json", "71530fb3beb5c824ff93176c3dc396e3b5256a49f06f07688cde3efc1e8356c2"),
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def save(path, value):
    raw = canonical(value) + b"\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(raw)
    return sha(raw)


def matchings(vertices):
    """Pair the least remaining vertex; each perfect matching occurs once."""
    if not vertices:
        return [()]
    first, rest = vertices[0], vertices[1:]
    return [((first, other),) + tail
            for k, other in enumerate(rest)
            for tail in matchings(rest[:k] + rest[k + 1:])]


def matching_masks(n):
    edges = list(combinations(range(n), 2))
    position = {e: k for k, e in enumerate(edges)}
    witnesses = matchings(tuple(range(n)))
    masks = [sum(1 << position[e] for e in matching) for matching in witnesses]
    assert len(masks) == len(set(masks))
    assert all(sorted(v for e in m for v in e) == list(range(n)) for m in witnesses)
    return edges, witnesses, masks


def subset_dp(n, edge_mask):
    """Independent bit-subset recurrence used only for tiny controls."""
    adjacency = [0] * n
    for k, (a, b) in enumerate(combinations(range(n), 2)):
        if edge_mask >> k & 1:
            adjacency[a] |= 1 << b
            adjacency[b] |= 1 << a
    @lru_cache(None)
    def solve(remaining):
        if remaining == 0:
            return True
        bit = remaining & -remaining
        a = bit.bit_length() - 1
        rest = remaining ^ bit
        neighbors = adjacency[a] & rest
        while neighbors:
            b = neighbors & -neighbors
            if solve(rest ^ b):
                return True
            neighbors ^= b
        return False
    return solve((1 << n) - 1)


def controls():
    sizes = {}
    for n, expected in [(0, 1), (2, 1), (4, 3), (6, 15), (8, 105)]:
        edges, witnesses, masks = matching_masks(n)
        assert len(witnesses) == expected
        sizes[n] = expected
    edges, witnesses, masks = matching_masks(6)
    for graph in range(1 << len(edges)):
        assert any(graph & m == m for m in masks) == subset_dp(6, graph)
    edges8, witnesses8, masks8 = matching_masks(8)
    cases = [set(), set(edges8), {(0, 1), (2, 3), (4, 5), (6, 7)},
             {(0, i) for i in range(1, 8)},
             set(combinations(range(3), 2)) | set(combinations(range(3, 6), 2)) | {(6, 7)},
             {(a, b) for a in range(4) for b in range(4, 8)}]
    for case, expected in zip(cases, [False, True, True, False, False, True]):
        bits = sum(1 << k for k, edge in enumerate(edges8) if edge in case)
        assert any(bits & m == m for m in masks8) == subset_dp(8, bits) == expected
    return {"status": "PASS", "complete_matching_counts": sizes,
            "all_labelled_six_vertex_graphs": 32768, "eight_vertex_controls": len(cases),
            "production_candidates": 0, "optimizer_calls": 0}


def context():
    data = {}
    for key, (name, digest) in INPUTS.items():
        raw = (ROOT / name).read_bytes()
        assert sha(raw) == digest, key
        data[key] = json.loads(gzip.decompress(raw) if name.endswith(".gz") else raw)
    assert data["matching_cold"]["status"].startswith("PASS")
    assert data["matching_cold"]["record_sha256"] == INPUTS["matching"][1]
    source = data["model"]["validation"]
    core = list(map(int, source["core"]))
    triples = source["triples"]
    assert len(core) == 21 and len(triples) == 480
    G = [[12 * (i == j) + 2 - ((core[i+3] >> (j+3)) & 1) -
          (core[i+3] & core[j+3]).bit_count() for j in range(18)] for i in range(18)]
    sets = []
    for i in range(18):
        neighbors = [j for j in range(18) if core[i+3] >> (j+3) & 1]
        coefficients = [int(i in h) - sum(i in h and j in h for j in neighbors) for h in triples]
        assert set(coefficients) <= {0, 1}
        U = [a for a, c in enumerate(coefficients) if c]
        assert G[i][i] - sum(G[i][j] for j in neighbors) == 8
        record = data["matching"]["matching_sets"][i]
        assert record["core_site"] == i and record["possible_signatures"] == U and record["rhs"] == 8
        sets.append(U)
    edges, orbits = source["edges"], source["edge_orbits"]
    assert len(edges) == 68394 and len(orbits) == 5805
    assert sorted(e for orbit in orbits for e in orbit) == list(range(len(edges)))
    assert all(len(edge) == 2 and 0 <= edge[0] < edge[1] < 480 for edge in edges)
    assert len(set(map(tuple, edges))) == len(edges)
    zero_columns = data["domains"]["original_Y_zero_columns"]
    assert len(zero_columns) == len(set(zero_columns)) == 162
    zeros = {j-42 for j in zero_columns}
    assert all(0 <= oi < len(orbits) for oi in zeros)
    omitted = {e for oi in zeros for e in orbits[oi]}
    allowed = {tuple(edge) for e, edge in enumerate(edges) if e not in omitted}
    witnesses = matchings(tuple(range(8)))
    assert len(witnesses) == 105
    return {"sets": sets, "triples": triples, "G": G, "allowed": allowed,
            "omitted_edges": len(omitted), "matching_templates": witnesses}


def definition():
    return {"source_sha256": sha(Path(__file__).read_bytes()),
            "inputs": {k: {"path": p, "sha256": h} for k, (p, h) in INPUTS.items()}}


def prepare():
    started = time.monotonic()
    ctx = context()
    return {"status": "PREPARED: exact local matching oracle; no production selection",
            "definition": definition(), "controls": controls(),
            "matching_sets_sha256": sha(canonical(ctx["sets"])),
            "live_eligible_edges_sha256": sha(canonical(sorted(ctx["allowed"]))),
            "live_eligible_edges": len(ctx["allowed"]), "proved_zero_edges_omitted": ctx["omitted_edges"],
            "matching_templates": ctx["matching_templates"], "templates_per_eight_vertices": 105,
            "all18_original_Gram_coefficient_identities_checked": True,
            "production_candidates": 0, "optimizer_calls": 0, "seconds": time.monotonic()-started}


def check_selection(ctx, selected):
    assert isinstance(selected, list) and len(selected) == 60
    assert all(type(a) is int and 0 <= a < 480 for a in selected)
    assert selected == sorted(set(selected))
    S = set(selected)
    failures = []
    for i in range(18):
        for j in range(i, 18):
            total = sum(i in ctx["triples"][a] and j in ctx["triples"][a] for a in selected)
            if total != ctx["G"][i][j]:
                failures.append({"core_pair": [i, j], "actual": total, "required": ctx["G"][i][j]})
    if failures:
        return {"status": "INVALID_LITERAL_SELECTION", "original_Gram_failures": failures,
                "new_matching_cuts": [], "native_count_acceptance_checked": False}
    records, cuts = [], []
    for i, U in enumerate(ctx["sets"]):
        chosen = sorted(S.intersection(U))
        assert len(chosen) == 8
        rejection_edges, witness = [], None
        for matching in ctx["matching_templates"]:
            pairs = [tuple(sorted((chosen[a], chosen[b]))) for a, b in matching]
            missing = next((edge for edge in pairs if edge not in ctx["allowed"]), None)
            if missing is None:
                witness = pairs
                break
            rejection_edges.append(list(missing))
        if witness is not None:
            records.append({"core_site": i, "selected": chosen, "status": "MATCHABLE", "matching": witness})
        else:
            assert len(rejection_edges) == 105
            row = {"terms": [[a, 1] for a in chosen], "upper": 7}
            cuts.append(row)
            records.append({"core_site": i, "selected": chosen, "status": "NO_PERFECT_MATCHING",
                            "one_missing_edge_per_matching": rejection_edges, "literal_cut": row})
    return {"status": "REFUTED_LITERAL_SELECTION_BY_CORE_MATCHING" if cuts else "ALL18_LOCAL_MATCHINGS_EXIST",
            "sites": records, "new_matching_cuts": cuts, "original_selector_equalities_checked": 172,
            "native_count_acceptance_checked": False, "shared_exterior_graph_constructed": False,
            "graph_exists_claimed": False}


def main():
    if not __debug__:
        raise RuntimeError("assertions are required")
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("mode", choices=["prepare", "prepare-replay", "check", "check-replay"])
    ap.add_argument("--output", required=True, type=Path)
    ap.add_argument("--selection", type=Path)
    ap.add_argument("--saved", type=Path)
    args = ap.parse_args()
    assert not args.output.exists()
    started = time.monotonic()
    if args.mode.startswith("prepare"):
        result = prepare()
    else:
        raw = args.selection.read_bytes()
        selected = json.loads(raw)
        result = check_selection(context(), selected)
        result.update(definition=definition(), selection_sha256=sha(raw),
                      canonical_selection_sha256=sha(canonical(selected)), production_candidates=1,
                      optimizer_calls=0, seconds=time.monotonic()-started)
    if args.mode.endswith("replay"):
        old_raw = args.saved.read_bytes()
        old = json.loads(old_raw)
        assert {k: v for k, v in old.items() if k != "seconds"} == json.loads(canonical({k: v for k, v in result.items() if k != "seconds"}))
        result = {"status": "PASS: complete deterministic oracle replay", "definition": definition(),
                  "saved_sha256": sha(old_raw), "optimizer_calls": 0,
                  "production_candidates": 0 if args.mode.startswith("prepare") else 1,
                  "seconds": time.monotonic()-started}
    digest = save(args.output, result)
    print(json.dumps({"status": result["status"], "sha256": digest, "seconds": result["seconds"]}))


if __name__ == "__main__":
    main()
