"""Common-core-pair clique inequalities for exterior edges in F0.

For a fixed exterior center b and distinct core sites i,j, at most one
neighbor of b can contain both i and j in its signature. Two such neighbors
would have three common neighbors b,i,j. Thus sum_a Y_ab <= x_b over this
signature bucket. This is an edge inequality, not a selector exclusion.
Inventory mode does not construct quotient inequalities or evaluate a point.
"""
import argparse
from collections import Counter, defaultdict
import gzip
import hashlib
from itertools import combinations, product
import json
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[2]
BASE = "experiments/logs/root-prism-free/"
INPUTS = {
    "domain": (BASE+"f0-boolean-fractional-model.json.gz", "703206929c9c85a40ac4ddcbfb1708c716c288482cf50c77a32249404e35b782"),
    "zeros": (BASE+"f0-edge-motif-census01.json.gz", "397e8bf110e03a5accb5e6c1f27b2fb5525100acb67427c66669e188e74159d1"),
    "reduction": (BASE+"f0-second-moments-reduced-model.json.gz", "73a50b431ac69ad57e10cff9aabe5c0b7d69ee075e95710b461f62b33fe2bbcf"),
    "actions": (BASE+"f0-graph-schur-kernels01.json.gz", "65f1ad0d0015a6eff3d97c676fb0e188f57f9dee00e9245758a28bab2069b40d"),
}
DISPOSITIONS = {0: "empty_live_bucket", 1: "one_edge_activation",
                2: "lifted_core_pair_quota_at_most_one",
                3: "mixed_center_core_quota_at_most_one", 4: "retained"}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def tick(deadline):
    if time.monotonic() >= deadline:
        raise TimeoutError("bounded common-core-pair edge-clique preparation")


def controls():
    # Every simple graph on five labelled sites, with the same CN caps.
    pairs = list(combinations(range(5), 2))
    valid_graphs = checked_buckets = 0
    for bits in range(1 << len(pairs)):
        rows = [0]*5
        for k, (i, j) in enumerate(pairs):
            if bits >> k & 1:
                rows[i] |= 1 << j
                rows[j] |= 1 << i
        if any((rows[i] & rows[j]).bit_count() > 2-((rows[i] >> j) & 1)
               for i, j in pairs):
            continue
        valid_graphs += 1
        for b in range(5):
            for i, j in combinations((v for v in range(5) if v != b), 2):
                assert (rows[b] & rows[i] & rows[j]).bit_count() <= 1
                checked_buckets += 1
    activation = quotient = 0
    for n in range(7):
        for x in (0, 1):
            for y in product((0, 1), repeat=n):
                if any(v > x for v in y) or sum(y) > 1:
                    continue
                assert sum(y) <= x
                activation += 1
        # Literal coefficient sums must retain repeated quotient columns.
        labels = [a % 3 for a in range(n)]
        counts = Counter(labels)
        for values in product(range(3), repeat=3):
            assert sum(values[j] for j in labels) == sum(c*values[j] for j, c in counts.items())
            quotient += 1
    return {"all_five_vertex_graphs_examined": 1024,
            "cap_valid_graphs": valid_graphs, "common_neighbor_bucket_checks": checked_buckets,
            "binary_activation_and_at_most_one_checks": activation,
            "coincident_quotient_column_checks": quotient}


def load():
    loaded = {}
    for name, (path, digest) in INPUTS.items():
        raw = (ROOT/path).read_bytes()
        assert sha(raw) == digest
        loaded[name] = json.loads(gzip.decompress(raw))
    d = loaded["domain"]["validation"]
    core, triples, edges, targets = (d[k] for k in ("core", "triples", "edges", "targets"))
    assert len(core) == 21 and len(triples) == 480 and len(edges) == 68394
    assert all(h == sorted(set(h)) and len(h) == 3 and 0 <= min(h) <= max(h) < 18 for h in triples)
    assert len(set(map(tuple, triples))) == 480
    assert all(((core[i] >> j) & 1) == ((core[j] >> i) & 1)
               for i in range(21) for j in range(21))
    assert all((core[i] & core[j]).bit_count() <= 2-((core[i] >> j) & 1)
               for i, j in combinations(range(21), 2))
    expected_targets = [[2-int(i in h)-sum((core[i+3] >> (j+3)) & 1 for j in h)
                         for i in range(18)] for h in triples]
    assert expected_targets == targets
    assert all(sum(row) == 24 and all(t in (0, 1, 2) for t in row) for row in targets)
    xmap = {a: o for o, group in enumerate(d["selector_orbits"]) for a in group}
    ymap = {e: 42+o for o, group in enumerate(d["edge_orbits"]) for e in group}
    assert len(xmap) == 480 and len(ymap) == 68394
    zeros = set(loaded["zeros"]["forced_zero_original_Y_variables"])
    assert len(zeros) == 162 and sum(ymap[e] in zeros for e in range(68394)) == 1884
    reverse = {j: i for i, j in enumerate(loaded["reduction"]["kept_original_variables"])}
    assert len(reverse) == 15200 and all(reverse[j] == j for j in range(5847))
    pairs = list(combinations(range(18), 2))
    pmap = {p: i for i, p in enumerate(pairs)}
    quota = [2-((core[i+3] >> (j+3)) & 1)-(core[i+3] & core[j+3]).bit_count()
             for i, j in pairs]
    assert all(q in (0, 1, 2) for q in quota)
    assert all(quota[pmap[p]] > 0 for h in triples for p in combinations(h, 2))
    buckets = defaultdict(list)
    assert edges == sorted(edges) and len(set(map(tuple, edges))) == 68394
    for ei, (a, b) in enumerate(edges):
        assert 0 <= a < b < 480 and len(set(triples[a]) & set(triples[b])) <= 1
        assert all(targets[b][j] > 0 for j in triples[a])
        assert all(targets[a][j] > 0 for j in triples[b])
        for center, neighbor in ((a, b), (b, a)):
            for pair in combinations(triples[neighbor], 2):
                buckets[center, pmap[pair]].append((neighbor, ei))
    assert sum(map(len, buckets.values())) == 2*68394*3
    return loaded, d, xmap, ymap, zeros, reverse, pairs, quota, buckets


def actions(loaded, d, xmap, ymap):
    core, triples, edges = d["core"], d["triples"], d["edges"]
    moves = loaded["actions"]["domain"]["reconstructed21_core_actions"]
    assert len(moves) == len(set(map(tuple, moves))) == 12
    lookup = {tuple(h): a for a, h in enumerate(triples)}
    edge_lookup = {tuple(e): i for i, e in enumerate(edges)}
    signatures = []
    for move in moves:
        assert sorted(move) == list(range(21)) and set(move[:3]) == set(range(3))
        assert all(((core[i] >> j) & 1) == ((core[move[i]] >> move[j]) & 1)
                   for i in range(21) for j in range(21))
        g = [lookup[tuple(sorted(move[j+3]-3 for j in h))] for h in triples]
        assert sorted(g) == list(range(480))
        signatures.append(g)
    move_index = {tuple(move): i for i, move in enumerate(moves)}
    assert tuple(range(21)) in move_index
    for i, left in enumerate(moves):
        for j, right in enumerate(moves):
            k = move_index[tuple(left[right[v]] for v in range(21))]
            assert all(signatures[k][a] == signatures[i][signatures[j][a]] for a in range(480))
    for orbit, group in enumerate(d["selector_orbits"]):
        assert sorted({g[group[0]] for g in signatures}) == group
        assert all(xmap[a] == orbit for a in group)
    for orbit, group in enumerate(d["edge_orbits"]):
        a, b = edges[group[0]]
        assert sorted({edge_lookup[tuple(sorted((g[a], g[b])))] for g in signatures}) == group
        assert all(ymap[e] == 42+orbit for e in group)
    return moves, signatures


def build(seconds, cuts):
    started = time.monotonic(); deadline = started+seconds
    loaded, d, xmap, ymap, zeros, reverse, pairs, quota, buckets = load()
    proof_controls = controls()
    triples, targets = d["triples"], d["targets"]
    counts = Counter(); ledger = []; rows = []; row_ids = {}
    for b in range(480):
        tick(deadline)
        for pi, (i, j) in enumerate(pairs):
            raw = buckets.get((b, pi), [])
            live = [(a, e) for a, e in raw if ymap[e] not in zeros]
            assert len({a for a, e in live}) == len(live)
            assert all(a != b and i in triples[a] and j in triples[a] for a, e in live)
            if not live:
                reason = 0
            elif len(live) == 1:
                reason = 1
            elif quota[pi] <= 1:
                reason = 2
            elif min(targets[b][i], targets[b][j]) <= 1:
                reason = 3
            else:
                reason = 4
                assert quota[pi] == targets[b][i] == targets[b][j] == 2
                assert b not in {a for a, e in raw}
            counts[DISPOSITIONS[reason]] += 1
            counts["all_center_core_pair_buckets"] += 1
            counts["raw_edge_memberships"] += len(raw)
            counts["known_zero_edge_memberships_removed"] += len(raw)-len(live)
            rid = -1
            if reason == 4:
                counts["retained_literal_edge_memberships"] += len(live)
                counts["retained_pair_conflict_instances"] += len(live)*(len(live)-1)//2
                counts["maximum_retained_bucket_size"] = max(counts["maximum_retained_bucket_size"], len(live))
                if cuts:
                    coeffs = Counter({reverse[xmap[b]]: -1})
                    for a, e in live:
                        coeffs[reverse[ymap[e]]] += 1
                    terms = tuple(sorted(coeffs.items()))
                    assert sum(c for v, c in terms) == len(live)-1
                    if terms not in row_ids:
                        row_ids[terms] = len(rows)
                        rows.append({"terms": [list(t) for t in terms], "rhs": 0,
                                     "first_bucket": len(ledger), "center": b, "core_pair": [i, j],
                                     "live_neighbors_and_edge_ids": [list(t) for t in live]})
                    rid = row_ids[terms]
            ledger.append([b, pi, len(raw), len(live), reason, rid])
    assert len(ledger) == counts["all_center_core_pair_buckets"] == 480*153
    assert counts["raw_edge_memberships"] == 410364
    assert counts["known_zero_edge_memberships_removed"] == 1884*6
    transports = []
    if cuts:
        moves, signatures = actions(loaded, d, xmap, ymap)
        pmap = {p: k for k, p in enumerate(pairs)}
        for rid, row in enumerate(rows):
            if rid % 100 == 0:
                tick(deadline)
            b, (i, j) = row["center"], row["core_pair"]
            mapped = []
            for k, (move, g) in enumerate(zip(moves, signatures)):
                pair = tuple(sorted((move[i+3]-3, move[j+3]-3)))
                index = g[b]*153+pmap[pair]
                assert ledger[index][4:] == [4, rid]
                mapped.append([k, index])
            transports.append(mapped)
        counts["distinct_quotient_rows"] = len(rows)
        counts["quotient_row_nonzeros"] = sum(len(r["terms"]) for r in rows)
        counts["quotient_rows_with_repeated_edge_column"] = sum(any(c > 1 for j, c in r["terms"]) for r in rows)
        counts["actual_core_row_transports"] = 12*len(rows)
    tick(deadline)
    return {"status": "COMPLETE_CORE_PAIR_EDGE_CLIQUE_"+("CUTS" if cuts else "INVENTORY"),
            "source_sha256": sha(Path(__file__).read_bytes()),
            "inputs": {k: {"path": p, "sha256": h} for k, (p, h) in INPUTS.items()},
            "controls": proof_controls, "census": dict(counts),
            "component_pairs": [list(p) for p in pairs], "core_pair_quotas": quota,
            "ledger_fields": ["center", "pair_index", "raw_size", "live_size", "disposition", "row_id"],
            "ledger": ledger, "dispositions": DISPOSITIONS, "rows": rows,
            "row_transports": transports, "all480_signatures_and68394_eligible_edges_retained": True,
            "exterior_neighbor_degree_from_mixed_targets": 8, "model_variables": 15200,
            "cuts_constructed": cuts, "point_loaded": False, "optimizer_calls": 0,
            "scope": "Necessary edge-clique rows from the common-neighbor cap. Known prism edge zeros only prune terms; all remaining candidates stay free."}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=("inventory", "cuts", "replay"))
    p.add_argument("--record", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--seconds", type=float, default=30)
    args = p.parse_args()
    assert 0 < args.seconds <= 30 and not args.output.exists()
    assert args.mode == "replay" or not args.record.exists()
    start = time.monotonic()
    try:
        result = build(args.seconds, args.mode != "inventory")
        raw = canonical(result)
        if args.mode == "replay":
            assert canonical(json.loads(gzip.decompress(args.record.read_bytes()))) == raw
        else:
            args.record.write_bytes(gzip.compress(raw, mtime=0))
        report = {"status": "PASS: common-core-pair edge-clique "+args.mode,
                  "source_sha256": result["source_sha256"],
                  "record_file_sha256": sha(args.record.read_bytes()), "record_raw_sha256": sha(raw),
                  "census": result["census"], "controls": result["controls"],
                  "cuts_constructed": result["cuts_constructed"], "point_loaded": False,
                  "optimizer_calls": 0, "seconds": time.monotonic()-start}
    except Exception as error:
        report = {"status": "INCOMPLETE_NO_COMPLETE_FAMILY_CLAIM", "mode": args.mode,
                  "source_sha256": sha(Path(__file__).read_bytes()),
                  "error_type": type(error).__name__, "message": str(error),
                  "seconds": time.monotonic()-start}
        args.output.write_text(json.dumps(report, indent=2)+"\n")
        raise
    args.output.write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
