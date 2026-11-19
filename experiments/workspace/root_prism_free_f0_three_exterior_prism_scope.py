"""Exact scope closure for prisms with exactly three exterior vertices.

This reads the frozen one-edge and two-edge records without rebuilding
their censuses. It independently checks the fixed core and all twenty
three-vertex splits of the triangular prism. No point or optimizer.
"""
import argparse
from collections import Counter
import gzip
import hashlib
from itertools import combinations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = "experiments/logs/root-prism-free/"
INPUTS = {
    "domain": (BASE+"f0-boolean-fractional-model.json.gz",
               "703206929c9c85a40ac4ddcbfb1708c716c288482cf50c77a32249404e35b782"),
    "one_edge": (BASE+"f0-three-vertex-prism-cuts01.json.gz",
                 "b445ad3268cb7016a7a5df07cef9c6fda1a0c7d96fa5a560f897c9449814b194"),
    "two_edges": (BASE+"f0-path-prism-cuts01.json.gz",
                  "d7ce1862d52cb4c9011efe73deb438db2b4e33a3fade1d5b803569005f2d7886"),
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def triangles(rows):
    return [list(t) for t in combinations(range(len(rows)), 3)
            if all((rows[a] >> b) & 1 for a, b in combinations(t, 2))]


def build():
    loaded = {}
    for name, (path, digest) in INPUTS.items():
        raw = (ROOT/path).read_bytes()
        assert sha(raw) == digest
        loaded[name] = json.loads(gzip.decompress(raw))
    data = loaded["domain"]["validation"]
    core, triples = data["core"], data["triples"]
    assert len(core) == 21 and len(triples) == 480
    component = [row >> 3 for row in core[3:]]
    assert all(row.bit_count() == 3 for row in component)
    assert triangles(component) == []
    core_triangles = triangles(core)
    assert all(any(v < 3 for v in t) for t in core_triangles)
    exterior_masks = [sum(1 << (j+3) for j in h) for h in triples]
    assert all(mask & 7 == 0 for mask in exterior_masks)
    prism = [0]*6
    for a, b in list(combinations(range(3), 2))+list(combinations(range(3, 6), 2))+[(0, 3), (1, 4), (2, 5)]:
        prism[a] |= 1 << b
        prism[b] |= 1 << a
    splits = []
    census = Counter()
    for exterior in combinations(range(6), 3):
        root = tuple(v for v in range(6) if v not in exterior)
        edges_ext = sum((prism[a] >> b) & 1 for a, b in combinations(exterior, 2))
        edges_core = sum((prism[a] >> b) & 1 for a, b in combinations(root, 2))
        assert edges_ext == edges_core and edges_ext in (1, 2, 3)
        cross_degrees = [sum((prism[v] >> w) & 1 for w in exterior) for v in root]
        if edges_ext == 3:
            assert cross_degrees == [1, 1, 1]
        census[edges_ext] += 1
        splits.append({"exterior_sites": list(exterior), "core_sites": list(root),
                       "exterior_edges": edges_ext, "core_edges": edges_core,
                       "core_to_exterior_degrees": cross_degrees})
    assert dict(census) == {3: 2, 2: 12, 1: 6}
    one, two = loaded["one_edge"], loaded["two_edges"]
    assert one["complete_all68394_edge_coverage"]
    assert two["complete_all107520_literal_pattern_configurations"]
    assert two["complete_all_three_exterior_two_edge_prisms_on_fixed_core"]
    assert len(one["rows"]) == 715 and len(two["rows"]) == 5124
    one_rows = {tuple((int(j), int(c)) for j, c in row["terms"]) for row in one["rows"]}
    two_rows = {tuple((int(j), int(c)) for j, c in row["terms"]) for row in two["rows"]}
    assert len(one_rows) == 715 and len(two_rows) == 5124 and not (one_rows & two_rows)
    assert all(any(j >= 5847 and c > 0 for j, c in row) for row in one_rows)
    assert all(all(j < 5847 for j, c in row) for row in two_rows)
    return {"status": "PASS_COMPLETE_EXACTLY_THREE_EXTERIOR_PRISM_SCOPE",
            "source_sha256": sha(Path(__file__).read_bytes()),
            "inputs": {k: {"path": p, "sha256": h} for k, (p, h) in INPUTS.items()},
            "fixed_component_order": 18, "fixed_component_degrees": [3]*18,
            "fixed_component_triangles": [], "full_core_triangles": core_triangles,
            "every_full_core_triangle_meets_central_three": True,
            "all480_exterior_signatures_avoid_central_three": True,
            "all_twenty_prism_splits": splits, "split_counts": dict(census),
            "three_exterior_edge_case_impossible_on_this_core": True,
            "one_edge_quotient_rows": 715, "two_edge_quotient_rows": 5124,
            "distinct_combined_quotient_rows": 5839,
            "both_census_records_read_but_not_reconstructed": True,
            "complete_only_for_exactly_three_exterior_vertices_and_fixed21_core": True,
            "other_component_and_alignment_free": True,
            "point_loaded": False, "optimizer_calls": 0,
            "graph_existence_resolved": False}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    assert not args.output.exists()
    result = build()
    args.output.write_text(json.dumps(result, indent=2)+"\n")
    print(json.dumps({k: v for k, v in result.items() if k != "all_twenty_prism_splits"}, indent=2))


if __name__ == "__main__":
    main()
