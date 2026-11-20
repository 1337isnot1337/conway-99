"""One exact core-neighborhood matching/blossom certificate for F0.

This reads frozen finite data, proves one transported count inequality, and
checks its explicitly local comparison. It performs no subset census,
candidate contraction, model construction, or optimizer call.
"""
import argparse
from collections import Counter
from fractions import Fraction
import gzip
import hashlib
from itertools import combinations
import json
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "experiments/logs/root-prism-free"
INPUTS = {
    "literal_model": ("f0-boolean-fractional-model.json.gz", "703206929c9c85a40ac4ddcbfb1708c716c288482cf50c77a32249404e35b782"),
    "domains": ("f0-orbit-populations02-domains.json.gz", "4f079468530dba0746512cc4afce01666b2a63a2c8f35f66a4660a4fe3bab8ab"),
    "live_edges": ("f0-edge-orbit-packing-preparation01.json.gz", "2d581d92545eb1d8718960471fe8c4bfe191a6a80a9f9d5d22754dc4afe0ec18"),
    "current_domains": ("f0-character-y-domain-overlay01/plan.json.gz", "4d3a13718cdac9fcf68b119a1cd1ba009edeb21c7257d4498d5ebdf18954acc4"),
}
SITE, SIGNATURES = 0, (1, 47, 61)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def read(name):
    filename, expected = INPUTS[name]
    raw = (BASE / filename).read_bytes()
    assert sha(raw) == expected
    return json.loads(gzip.decompress(raw))


def controls():
    accepted = []
    pairs = list(combinations(range(1, 4), 2))
    for mask in range(8):
        adjacency = [0] * 4
        for v in range(1, 4):
            adjacency[0] |= 1 << v
            adjacency[v] |= 1
        for k, (a, b) in enumerate(pairs):
            if mask >> k & 1:
                adjacency[a] |= 1 << b
                adjacency[b] |= 1 << a
        caps = all((adjacency[a] & adjacency[b]).bit_count() <=
                   (1 if adjacency[a] >> b & 1 else 2)
                   for a, b in combinations(range(4), 2))
        assert caps == (mask.bit_count() <= 1)
        if caps:
            accepted.append(mask)
    half = [Fraction(1, 2)] * 3
    assert all(half[a] + half[b] <= 1 for a, b in combinations(range(3), 2))
    assert sum(half) == Fraction(3, 2) > 1
    return {"four_vertex_fixed_star_graphs": 8, "cap_valid_masks": accepted,
            "triangle_half_vector_passes_three_pair_conflicts": True,
            "triangle_half_vector_violates_matching_odd_set": True}


def certificate():
    started = time.monotonic()
    model, domains, live, target = [read(k) for k in INPUTS]
    d = model["validation"]
    triples, targets, edges, edge_orbits = [d[k] for k in ("triples", "targets", "edges", "edge_orbits")]
    core = list(map(int, d["core"]))
    assert len(core) == 21 and len(triples) == 480 and len(edges) == 68394
    D = [(row >> 3) & ((1 << 18) - 1) for row in core[3:]]
    assert all(row.bit_count() == 3 for row in D)
    masks = [sum(1 << i for i in h) for h in triples]
    assert all(len(h) == 3 for h in triples)
    G = [[12 * (i == j) + 2 - ((core[3+i] >> (3+j)) & 1) -
          (core[3+i] & core[3+j]).bit_count() for j in range(18)] for i in range(18)]
    matching_sets, quota_proofs = [], []
    for i in range(18):
        neighbors = [j for j in range(18) if D[i] >> j & 1]
        U = []
        for a, h in enumerate(triples):
            q = 2 - (i in h) - (D[i] & masks[a]).bit_count()
            assert q == targets[a][i]
            coefficient = int(i in h) - sum(i in h and j in h for j in neighbors)
            assert coefficient == int(i in h and q == 1)
            if i in h:
                assert q in (0, 1)
                assert coefficient == q
                if q == 1:
                    U.append(a)
        rhs = G[i][i] - sum(G[i][j] for j in neighbors)
        assert G[i][i] == 10 and rhs == 8
        matching_sets.append(U)
        quota_proofs.append({"core_site": i, "possible_signatures": U,
                            "Gram_combination": [[i, i, 1]] + [[min(i,j), max(i,j), -1] for j in neighbors],
                            "rhs": 8, "coefficient_identity_checked_on": 480})
    assert set(SIGNATURES) <= set(matching_sets[SITE])
    assert [triples[a] for a in SIGNATURES] == [[0, 2, 8], [0, 9, 10], [0, 11, 15]]
    edge_position = {tuple(e): j for j, e in enumerate(edges)}
    orbit_of = {e: oi for oi, members in enumerate(edge_orbits) for e in members}
    old_to_new = {old: new for new, old in enumerate(domains["new15038_to_original15589"])}
    live_by_orbit = {r["edge_orbit"]: r for r in live["records"]}
    primitive_edges = list(combinations(SIGNATURES, 2))
    original_orbits = [orbit_of[edge_position[e]] for e in primitive_edges]
    assert original_orbits == [69, 76, 4554]
    for oi in original_orbits:
        r = live_by_orbit[oi]
        assert r["literal_edge_ids"] == edge_orbits[oi]
        assert r["reduced_count_column"] == old_to_new[42+oi]
    assert domains["group_order"] == 12
    core_actions, actions = domains["actual_core_actions"], domains["signature_actions"]
    assert len(core_actions) == len(actions) == 12
    transported, counts = [], Counter()
    for move, action in zip(core_actions, actions):
        assert sorted(move) == list(range(18))
        fibers = [move[6*f] // 6 for f in range(3)]
        assert sorted(fibers) == list(range(3))
        assert all(move[i] // 6 == fibers[i // 6] for i in range(18))
        full_action = fibers + [3+j for j in move]
        assert sorted(full_action) == list(range(21))
        assert set(full_action[:3]) == set(range(3))
        assert all(((core[i] >> j) & 1) == ((core[full_action[i]] >> full_action[j]) & 1)
                   for i in range(21) for j in range(21))
        assert sorted(action) == list(range(480))
        assert all(sorted(move[i] for i in triples[a]) == triples[action[a]] for a in range(480))
        moved = [action[a] for a in SIGNATURES]
        assert all(move[SITE] in triples[a] and targets[a][move[SITE]] == 1 for a in moved)
        ids = [edge_position[tuple(sorted((action[a], action[b])))] for a, b in primitive_edges]
        assert [orbit_of[e] for e in ids] == original_orbits
        counts.update(ids)
        transported.append({"core_site": move[SITE], "signatures": moved, "literal_edge_ids": ids})
    terms = []
    for oi in original_orbits:
        members = edge_orbits[oi]
        assert len(members) == 12
        assert {counts[e] for e in members} == {1}
        terms.append([old_to_new[42+oi], 1])
    assert terms == [[96, 1], [103, 1], [4477, 1]]
    assert set(counts) == set(e for oi in original_orbits for e in edge_orbits[oi])
    selector_orbit = {a: i for i, O in enumerate(domains["selector_orbits"]) for a in O}
    endpoint_orbits = [selector_orbit[a] for a in SIGNATURES]
    assert endpoint_orbits == [0, 22, 25]
    assert all(len(domains["selector_orbits"][i]) == 12 for i in endpoint_orbits)
    boxes = target["target_variable_domains"]
    values = {0: 3, 22: 12, 25: 12, 96: 1, 103: 2, 4477: 10}
    for j, value in values.items():
        domain = boxes[j]
        assert any(domain[k] <= value <= domain[k+1] for k in range(0, len(domain), 2))
    star_rows = [
        {"terms": [[96, 1], [103, 1], [0, -1]], "rhs": 0},
        {"terms": [[96, 1], [4477, 1], [22, -1]], "rhs": 0},
        {"terms": [[103, 1], [4477, 1], [25, -1]], "rhs": 0},
    ]
    star_values = [sum(c * values[j] for j, c in r["terms"]) for r in star_rows]
    assert star_values == [0, -1, 0] and all(v <= 0 for v in star_values)
    activity = sum(c * values[j] for j, c in terms)
    assert activity == 13 > 12
    return {
        "schema": "conway99.f0.core-matching-one-blossom.v1",
        "status": "PASS: one exact transported matching inequality; local comparison only",
        "source_sha256": sha(Path(__file__).read_bytes()),
        "inputs": {k: {"path": str((BASE/p).relative_to(ROOT)), "sha256": h}
                   for k, (p, h) in INPUTS.items()},
        "matching_sets": quota_proofs,
        "literal_pattern": {"core_site": SITE, "signatures": list(SIGNATURES),
                            "triples": [triples[a] for a in SIGNATURES],
                            "edge_pairs": [list(e) for e in primitive_edges],
                            "inequality_rhs": 1},
        "all_actual_core_transports": transported,
        "summed_literal_edge_coefficients": [[e, counts[e]] for e in sorted(counts)],
        "orbit_count_row": {"terms": terms, "rhs": 12, "original_edge_orbits": original_orbits},
        "local_comparison": {"current_domains": {str(j): boxes[j] for j in values},
                             "integer_values": {str(j): v for j, v in values.items()},
                             "star_rows": star_rows, "star_row_activities": star_values,
                             "new_row_activity": activity, "new_row_violation": 1,
                             "full_model_point_claimed": False,
                             "other_rows_or_profile_tables_checked": False},
        "controls": controls(),
        "limits": {"optimizer_calls": 0, "new_subset_censuses": 0, "production_candidates": 0,
                   "native_models_built": 0, "full_model_nonredundance_claimed": False},
        "seconds": time.monotonic() - started,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--replay", type=Path)
    args = ap.parse_args()
    assert not args.output.exists()
    record = certificate()
    if args.replay:
        old = json.loads(args.replay.read_bytes())
        assert {k: v for k, v in old.items() if k != "seconds"} == {k: v for k, v in record.items() if k != "seconds"}
        record = {"status": "PASS: exact single-blossom proof replay",
                  "source_sha256": record["source_sha256"], "record_sha256": sha(args.replay.read_bytes()),
                  "all_actual_core_transports": 12, "original_Gram_coefficient_checks": 8640,
                  "optimizer_calls": 0, "seconds": record["seconds"]}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(canonical(record) + b"\n")
    print(json.dumps({"status": record["status"], "sha256": sha(args.output.read_bytes()),
                      "seconds": record["seconds"]}, indent=2))


if __name__ == "__main__":
    main()
