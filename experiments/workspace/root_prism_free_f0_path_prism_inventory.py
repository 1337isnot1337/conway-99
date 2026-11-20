"""Point-independent cost inventory for three-exterior two-edge prism cuts.

No exterior path pair is enumerated here. For each core path and center
signature, bucket cardinalities give the exact number of literal pattern
configurations before row deduplication. No point or optimizer is read.
"""
import argparse
from collections import Counter
import gzip
import hashlib
from itertools import combinations, product
import json
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[2]
BASE = "experiments/logs/root-prism-free/"
INPUTS = {
    "domain": (BASE+"f0-boolean-fractional-model.json.gz",
               "703206929c9c85a40ac4ddcbfb1708c716c288482cf50c77a32249404e35b782"),
    "edge_zeros": (BASE+"f0-edge-motif-census01.json.gz",
                  "397e8bf110e03a5accb5e6c1f27b2fb5525100acb67427c66669e188e74159d1"),
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def members(bits):
    while bits:
        low = bits & -bits
        yield low.bit_length()-1
        bits -= low


def graph_from_edges(n, edges):
    rows = [0]*n
    for a, b in edges:
        assert a != b
        rows[a] |= 1 << b
        rows[b] |= 1 << a
    return rows


def induced(rows, sites):
    return [sum(((rows[v] >> w) & 1) << j for j, w in enumerate(sites))
            for v in sites]


def controls():
    prism = graph_from_edges(6, list(combinations(range(3), 2))+
                             list(combinations(range(3, 6), 2))+
                             [(0, 3), (1, 4), (2, 5)])
    split_counts = Counter()
    witnesses = []
    for outside in combinations(range(6), 3):
        core = tuple(v for v in range(6) if v not in outside)
        e = sum((prism[a] >> b) & 1 for a, b in combinations(outside, 2))
        split_counts[e] += 1
        if e != 2:
            continue
        b = next(v for v in outside if sum((prism[v] >> w) & 1 for w in outside) == 2)
        y = next(v for v in core if sum((prism[v] >> w) & 1 for w in core) == 2)
        assert sum((prism[b] >> w) & 1 for w in core) == 1
        x = next(w for w in core if (prism[b] >> w) & 1)
        z = next(w for w in core if w not in (x, y))
        assert ((prism[x] >> y) & 1) and ((prism[y] >> z) & 1)
        assert not ((prism[x] >> z) & 1)
        a = next(v for v in outside if v != b and
                 {w for w in core if (prism[v] >> w) & 1} == {x, z})
        c = next(v for v in outside if v not in (a, b))
        assert {w for w in core if (prism[c] >> w) & 1} == {y, z}
        assert not ((prism[a] >> c) & 1)
        sites = [a, b, x, c, y, z]
        small = induced(prism, sites)
        assert small == [38, 13, 19, 50, 44, 25]
        witnesses.append({"outside": list(outside), "a_b_c": [a, b, c],
                          "x_y_z": [x, y, z], "triangle_order": sites,
                          "induced_rows": small})
    assert dict(split_counts) == {3: 2, 2: 12, 1: 6}
    valid = forbidden = 0
    for xa, xb, xc, yab, ybc in product((0, 1), repeat=5):
        if yab > min(xa, xb) or ybc > min(xb, xc):
            continue
        if yab and ybc:
            assert yab+ybc-xb == 1
            forbidden += 1
        else:
            assert yab+ybc <= xb
            valid += 1
    assert valid == 12 and forbidden == 1
    return {"all_twenty_three_vertex_prism_splits": dict(split_counts),
            "all_twelve_path_splits_have_the_same_literal_pattern": witnesses,
            "activation_compatible_prism_free_boolean_assignments": valid,
            "activation_compatible_forbidden_path_assignment": forbidden}


def load_domain():
    loaded = {}
    for name, (path, digest) in INPUTS.items():
        raw = (ROOT/path).read_bytes()
        assert sha(raw) == digest
        loaded[name] = json.loads(gzip.decompress(raw))
    data = loaded["domain"]["validation"]
    core, triples, edges, targets = (data[k] for k in ("core", "triples", "edges", "targets"))
    assert len(core) == 21 and len(triples) == 480 and len(edges) == 68394
    assert len(data["selector_orbits"]) == 42 and len(data["edge_orbits"]) == 5805
    assert all(h == sorted(set(h)) and len(h) == 3 and min(h) >= 0 and max(h) < 18
               for h in triples)
    masks = [sum(1 << v for v in h) for h in triples]
    assert len(set(masks)) == 480
    adjacency = [[(core[i+3] >> (j+3)) & 1 for j in range(18)] for i in range(18)]
    assert all(adjacency[i][j] == adjacency[j][i] for i in range(18) for j in range(18))
    computed = [[2-int(i in h)-sum(adjacency[i][j] for j in h) for i in range(18)]
                for h in triples]
    assert computed == targets and all(x in (0, 1, 2) for row in targets for x in row)
    ymap = {}
    for orbit, group in enumerate(data["edge_orbits"]):
        for ei in group:
            assert ei not in ymap
            ymap[ei] = 42+orbit
    assert set(ymap) == set(range(68394))
    zeros = set(loaded["edge_zeros"]["forced_zero_original_Y_variables"])
    assert len(zeros) == 162
    neighbors = [0]*480
    live_neighbors = [0]*480
    zero_edges = 0
    assert edges == sorted(edges) and len({tuple(e) for e in edges}) == 68394
    for ei, (a, b) in enumerate(edges):
        assert 0 <= a < b < 480 and (masks[a] & masks[b]).bit_count() <= 1
        assert all(targets[a][i] > 0 for i in triples[b])
        assert all(targets[b][i] > 0 for i in triples[a])
        neighbors[a] |= 1 << b
        neighbors[b] |= 1 << a
        if ymap[ei] in zeros:
            zero_edges += 1
        else:
            live_neighbors[a] |= 1 << b
            live_neighbors[b] |= 1 << a
    assert zero_edges == 1884
    return data, masks, adjacency, ymap, zeros, neighbors, live_neighbors


def build(seconds):
    start = time.monotonic()
    deadline = start+seconds
    control = controls()
    data, masks, adjacency, ymap, zeros, neighbors, live = load_domain()
    targets = data["targets"]
    paths = [(x, y, z) for y in range(18) for x in range(18) for z in range(18)
             if x != z and adjacency[y][x] and adjacency[y][z] and not adjacency[x][z]]
    assert len(paths) == len(set(paths))
    quota_one = [sum(1 << j for j, q in enumerate(row) if q == 1) for row in targets]
    zero_targets = [sum(1 << j for j, q in enumerate(row) if q == 0) for row in targets]
    totals = Counter()
    branches = []
    for x, y, z in paths:
        assert time.monotonic() < deadline, "bounded two-edge prism inventory"
        sites = (1 << x) | (1 << y) | (1 << z)
        a_pattern = (1 << x) | (1 << z)
        c_pattern = (1 << y) | (1 << z)
        a_bucket = sum(1 << a for a, h in enumerate(masks) if h & sites == a_pattern)
        c_bucket = sum(1 << c for c, h in enumerate(masks) if h & sites == c_pattern)
        assert not (a_bucket & c_bucket)
        for b, mask_b in enumerate(masks):
            if mask_b & sites != 1 << x:
                continue
            totals["eligible_center_core_patterns"] += 1
            aa = a_bucket & neighbors[b]
            cc = c_bucket & neighbors[b]
            raw = aa.bit_count()*cc.bit_count()
            if not raw:
                continue
            assert not ((aa | cc) >> b) & 1
            a_live, c_live = aa & live[b], cc & live[b]
            after_zeros = a_live.bit_count()*c_live.bit_count()
            totals["nonempty_raw_pattern_buckets"] += 1
            totals["literal_pattern_configurations_before_pruning"] += raw
            totals["known_Y_zero_redundant_configurations"] += raw-after_zeros
            q = targets[b][z]
            assert q in (1, 2)
            common_removed = after_zeros if q == 1 else 0
            extra_removed = 0
            a_extras = c_extras = 0
            if q == 2 and after_zeros:
                for a in members(a_live):
                    extra = masks[a] ^ a_pattern
                    assert extra.bit_count() == 1 and not (extra & sites)
                    assert not (a_extras & extra)
                    a_extras |= extra
                for c in members(c_live):
                    extra = masks[c] ^ c_pattern
                    assert extra.bit_count() == 1 and not (extra & sites)
                    assert not (c_extras & extra)
                    c_extras |= extra
                assert not ((a_extras | c_extras) & zero_targets[b])
                extra_removed = (a_extras & c_extras & quota_one[b]).bit_count()
            kept = after_zeros-common_removed-extra_removed
            assert kept >= 0
            totals["common_site_quota_one_redundant_configurations"] += common_removed
            totals["third_site_quota_one_redundant_configurations"] += extra_removed
            totals["retained_literal_pattern_configurations_upper_bound_on_distinct_rows"] += kept
            totals["nonempty_retained_pattern_buckets"] += int(kept > 0)
            totals["signature_bucket_members_inspected"] += (a_live.bit_count()+c_live.bit_count()
                                                           if q == 2 and after_zeros else 0)
            branches.append({"core_path_x_y_z": [x, y, z], "center_b": b,
                             "raw_a_count": aa.bit_count(), "raw_c_count": cc.bit_count(),
                             "live_a_count": a_live.bit_count(), "live_c_count": c_live.bit_count(),
                             "shared_site_target": q,
                             "live_a_extra_mask": a_extras, "live_c_extra_mask": c_extras,
                             "known_Y_zero_removed": raw-after_zeros,
                             "shared_site_quota_one_removed": common_removed,
                             "extra_site_quota_one_removed": extra_removed,
                             "retained_configuration_count": kept})
    assert totals["literal_pattern_configurations_before_pruning"] == sum(
        totals[k] for k in ("known_Y_zero_redundant_configurations",
                           "common_site_quota_one_redundant_configurations",
                           "third_site_quota_one_redundant_configurations",
                           "retained_literal_pattern_configurations_upper_bound_on_distinct_rows"))
    assert time.monotonic() < deadline, "bounded two-edge prism inventory"
    return {"status": "COMPLETE_TWO_EDGE_PRISM_COST_AND_REDUNDANCY_INVENTORY",
            "source_sha256": sha(Path(__file__).read_bytes()),
            "inputs": {name: {"path": path, "sha256": digest}
                       for name, (path, digest) in INPUTS.items()},
            "controls": control, "oriented_component_paths": [list(t) for t in paths],
            "oriented_component_path_count": len(paths),
            "unrestricted_eligible_exterior_path_pair_bound": sum(
                b.bit_count()*(b.bit_count()-1)//2 for b in neighbors),
            "eligible_edges": 68394, "known_zero_edge_orbits": 162,
            "known_zero_literal_edges": 1884, "all480_signatures_retained": True,
            "census": dict(totals), "pattern_buckets": branches,
            "production_literal_paths_enumerated": 0,
            "distinct_literal_paths_or_quotient_rows_not_yet_counted": True,
            "quotient_requires_combining_repeated_Y_variables": True,
            "point_loaded": False, "optimizer_calls": 0,
            "other_component_and_alignment_free": True,
            "scope": "All three-exterior two-edge prism patterns counted by bucket cardinalities; no complete cut census or point result.",
            "seconds": time.monotonic()-start}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--record", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--seconds", type=float, default=10)
    args = p.parse_args()
    assert 0 < args.seconds <= 10 and not args.record.exists() and not args.output.exists()
    result = build(args.seconds)
    raw = canonical(result)
    args.record.write_bytes(gzip.compress(raw, mtime=0))
    report = {k: v for k, v in result.items() if k not in ("pattern_buckets", "oriented_component_paths")}
    report["record_sha256"] = sha(args.record.read_bytes())
    report["record_raw_sha256"] = sha(raw)
    report["record_bytes"] = args.record.stat().st_size
    args.output.write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
