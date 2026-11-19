#!/usr/bin/env python3
"""Exact edge-partition / ten-vertex-motif audit; no solver or dense cache.

The default replay uses the Python standard library.  It reconstructs the
motif, checks every possible extra edge, exhausts the 10,395 matchings on
twelve sites, and checks nonzero controls from the saved partial cores.
"""

from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
from itertools import combinations, permutations
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "experiments/logs/root-prism-free/edge-components-certificate.json"
STRUCTURE = ROOT / "experiments/logs/root-prism-free/structure-certificate.json"
PREPARATION = ROOT / "experiments/logs/moments-and-counts/grid-free-order10-scaled-preparation.json"
ROW_EXPORT = ROOT / "experiments/logs/moments-and-counts/root-prism-free-edge-component-row.json"
COUNT_POINT = ROOT / "experiments/logs/moments-and-counts/prism-zero-repair-witness.json"


def compact(value):
    return json.dumps(value, separators=(",", ":"), sort_keys=True).encode()


def digest(value):
    return sha256(compact(value)).hexdigest()


def file_record(path):
    return {"path": str(path.relative_to(ROOT)), "sha256": sha256(path.read_bytes()).hexdigest()}


def sites(mask):
    while mask:
        low = mask & -mask
        yield low.bit_length() - 1
        mask ^= low


def add_edge(rows, a, b):
    assert a != b
    rows[a] |= 1 << b
    rows[b] |= 1 << a


def check_graph(rows):
    n = len(rows)
    for i, row in enumerate(rows):
        assert row >= 0 and row >> n == 0 and not (row >> i & 1)
        for j in range(n):
            assert (row >> j & 1) == (rows[j] >> i & 1)


def cap(rows, a, b):
    return (rows[a] & rows[b]).bit_count() + (rows[a] >> b & 1)


def restricted_rows(rows, vertices):
    return [sum(((rows[a] >> b) & 1) << j for j, b in enumerate(vertices))
            for a in vertices]


def components(rows, vertices=None):
    remaining = sum(1 << v for v in vertices) if vertices is not None else (1 << len(rows)) - 1
    answer = []
    while remaining:
        frontier = remaining & -remaining
        found = 0
        while frontier:
            found |= frontier
            neighbors = 0
            for v in sites(frontier):
                neighbors |= rows[v]
            frontier = neighbors & remaining & ~found
        remaining &= ~found
        answer.append(tuple(sites(found)))
    return sorted(answer)


def motif():
    rows = [0] * 10
    add_edge(rows, 0, 1)
    for i in range(8):
        add_edge(rows, 2 + i, 2 + (i + 1) % 8)
        add_edge(rows, 0 if i % 4 < 2 else 1, 2 + i)
    assert rows == [206, 817, 521, 21, 42, 82, 161, 321, 642, 262]
    return rows


def cycle_order(rows, vertices):
    allowed = sum(1 << v for v in vertices)
    if not vertices or any((rows[v] & allowed).bit_count() != 2 for v in vertices):
        return None
    start = min(vertices)
    result = [start]
    previous, current = start, min(sites(rows[start] & allowed))
    while current != start:
        if current in result:
            return None
        result.append(current)
        nxt, = sites((rows[current] & allowed) & ~(1 << previous))
        previous, current = current, nxt
    return result if len(result) == len(vertices) else None


def center_cycle_transports(first, second):
    """All isomorphisms for this shape, using its unique centers and C8."""
    if len(first) != 10 or len(second) != 10:
        return []
    centers_a = [i for i, row in enumerate(first) if row.bit_count() == 5]
    centers_b = [i for i, row in enumerate(second) if row.bit_count() == 5]
    if len(centers_a) != 2 or len(centers_b) != 2:
        return []
    cycle_a = cycle_order(first, [i for i in range(10) if i not in centers_a])
    cycle_b = cycle_order(second, [i for i in range(10) if i not in centers_b])
    if cycle_a is None or cycle_b is None:
        return []
    answer = []
    for target_centers in permutations(centers_b):
        for direction in (1, -1):
            for offset in range(8):
                mapping = [-1] * 10
                for a, b in zip(centers_a, target_centers):
                    mapping[a] = b
                for i, a in enumerate(cycle_a):
                    mapping[a] = cycle_b[(offset + direction * i) % 8]
                assert sorted(mapping) == list(range(10))
                if all(((first[a] >> b) & 1) == ((second[mapping[a]] >> mapping[b]) & 1)
                       for a, b in combinations(range(10), 2)):
                    answer.append(mapping)
    return sorted(answer)


def chord_audit(rows):
    assert max(cap(rows, a, b) for a, b in combinations(range(10), 2)) == 2
    witnesses = []
    for a, b in combinations(range(10), 2):
        if rows[a] >> b & 1:
            continue
        changed = rows[:]
        add_edge(changed, a, b)
        bad = [(x, y) for x, y in combinations(range(10), 2) if cap(changed, x, y) > 2]
        assert bad
        x, y = bad[0]
        witnesses.append({
            "added_edge": [a, b], "violating_pair": [x, y],
            "cap_before": cap(rows, x, y), "cap_after": cap(changed, x, y),
            "common_neighbors_after": list(sites(changed[x] & changed[y])),
            "pair_adjacent_after": bool(changed[x] >> y & 1),
        })
    assert len(witnesses) == 28
    return witnesses


def prism_coordinate_audit(preparation):
    entry, = [r for r in preparation["upper_bounds"] if r["coordinate"] == 1]
    rows = entry["rows"]
    check_graph(rows)
    assert len(rows) == 6 and all(row.bit_count() == 3 for row in rows)
    triangles = [triple for triple in combinations(range(6), 3)
                 if all(rows[a] >> b & 1 for a, b in combinations(triple, 2))]
    assert len(triangles) == 2 and not set(triangles[0]).intersection(triangles[1])
    cross = [(a, b) for a in triangles[0] for b in triangles[1] if rows[a] >> b & 1]
    assert len(cross) == 3
    assert len({a for a, _ in cross}) == len({b for _, b in cross}) == 3
    extra = []
    for a, b in combinations(range(6), 2):
        if rows[a] >> b & 1:
            continue
        changed = rows[:]
        add_edge(changed, a, b)
        bad = [(x, y) for x, y in combinations(range(6), 2) if cap(changed, x, y) > 2]
        assert bad
        extra.append({"added_edge": [a, b], "violating_pair": list(bad[0])})
    assert len(extra) == 6
    return {"coordinate": 1, "catalogue_type": entry["catalogue_type"],
            "rows": rows, "triangles": [list(t) for t in triangles],
            "three_possible_center_edges": [list(e) for e in cross],
            "chord_cap_witnesses": extra}


def perfect_matchings(remaining):
    if not remaining:
        yield ()
        return
    first = remaining[0]
    for position in range(1, len(remaining)):
        second = remaining[position]
        rest = remaining[1:position] + remaining[position + 1:]
        for tail in perfect_matchings(rest):
            yield tuple(sorted(((first, second),) + tail))


def canonical_matching(partition):
    pairs, offset = [], 0
    for length in partition:
        for i in range(length):
            pairs.append(tuple(sorted((2 * (offset + i) + 1,
                                       2 * (offset + (i + 1) % length)))))
        offset += length
    assert offset == 6
    return tuple(sorted(pairs))


def matching_partition(matching):
    rows = [0] * 12
    for a in range(0, 12, 2):
        add_edge(rows, a, a ^ 1)
    for a, b in matching:
        add_edge(rows, a, b)
    return tuple(sorted(len(c) // 2 for c in components(rows)))


def edge_core(matching):
    """Complete neighborhoods of an edge, with its common neighbor at 2."""
    rows = [0] * 27
    for a, b in ((0, 1), (0, 2), (1, 2)):
        add_edge(rows, a, b)
    for i in range(12):
        add_edge(rows, 0, 3 + i)
        add_edge(rows, 1, 15 + i)
        add_edge(rows, 3 + i, 15 + i)
    for i in range(0, 12, 2):
        add_edge(rows, 3 + i, 3 + (i ^ 1))
    for i, j in matching:
        add_edge(rows, 15 + i, 15 + j)
    return rows


def frame(rows, r, a):
    assert rows[r] >> a & 1
    p, = sites(rows[r] & rows[a])
    x = tuple(sites(rows[r] & ~((1 << a) | (1 << p))))
    y = tuple(sites(rows[a] & ~((1 << r) | (1 << p))))
    assert len(x) == len(y) == 12 and not set(x).intersection(y)
    xm, ym = sum(1 << i for i in x), sum(1 << i for i in y)
    cross = {}
    for u in x:
        assert (rows[u] & xm).bit_count() == 1
        v, = sites(rows[u] & ym)
        cross[u] = v
    for v in y:
        assert (rows[v] & ym).bit_count() == 1
        assert (rows[v] & xm).bit_count() == 1
    assert len(set(cross.values())) == 12
    assert all((rows[u] & (xm | ym)).bit_count() == 2 for u in x + y)
    cycles = components(rows, x + y)
    assert all(len(c) % 4 == 0 for c in cycles)
    partition = sorted(len(c) // 4 for c in cycles)
    return {"common_neighbor": p, "x": x, "y": y, "cross": cross,
            "cycles": cycles, "partition": partition}


def direct_centered_motifs(rows, r, a):
    """Enumerate all possible four-X/four-Y copies, independently of components."""
    f = frame(rows, r, a)
    copies = []
    reference = motif()
    for four in combinations(f["x"], 4):
        vertices = (r, a) + four + tuple(f["cross"][v] for v in four)
        subgraph = restricted_rows(rows, vertices)
        if center_cycle_transports(reference, subgraph):
            copies.append(tuple(sorted(vertices[2:])))
    assert len(copies) == len(set(copies))
    return sorted(copies)


def matching_audit():
    histogram = Counter()
    census = []
    for matching in perfect_matchings(tuple(range(12))):
        partition = matching_partition(matching)
        rows = edge_core(matching)
        forward, reverse = frame(rows, 0, 1), frame(rows, 1, 0)
        assert forward["partition"] == reverse["partition"] == list(partition)
        assert forward["cycles"] == reverse["cycles"]
        assert all(len(c) == 4 * length for c, length in
                   zip(sorted(forward["cycles"], key=len), partition))
        histogram[partition] += 1
        census.append([matching, partition, sorted(map(len, forward["cycles"]))])
    assert len(census) == 10395 and len(histogram) == 11
    assert sum(histogram.values()) == 10395
    cases = []
    for partition, count in sorted(histogram.items()):
        rows = edge_core(canonical_matching(partition))
        f = frame(rows, 0, 1)
        expected = sorted(c for c in f["cycles"] if len(c) == 8)
        actual = direct_centered_motifs(rows, 0, 1)
        assert actual == expected
        assert len(actual) == partition.count(2)
        assert partition.count(1) + 2 * partition.count(2) <= 6
        cases.append({"partition": list(partition), "labelled_matchings": count,
                      "shell_cycle_sizes": sorted(map(len, f["cycles"])),
                      "one_parts": partition.count(1), "two_parts": partition.count(2),
                      "direct_centered_motif_count": len(actual)})
    zero = [c for c in cases if not c["one_parts"]]
    assert [c["partition"] for c in zero] == [[2, 2, 2], [2, 4], [3, 3], [6]]
    return {"matchings": 10395, "partitions": 11,
            "all_endpoint_reversals_preserve_partition": True,
            "all_shell_lengths_are_four_times_partition_parts": True,
            "census_sha256": digest(census), "cases": cases,
            "direct_four_X_subset_checks": 11 * 495}


def partial_audit():
    saved = json.loads(STRUCTURE.read_text())
    answer = []
    for control in saved["partial_controls"]:
        rows = [int(row) for row in control["known_adjacency_rows"]]
        check_graph(rows)
        assert len(rows) == 99
        assert all(rows[i].bit_count() == 14 for i in range(15))
        assert max(cap(rows, a, b) for a, b in combinations(range(99), 2)) <= 2
        partition = control["partition_at_all14_anchors"]
        records = []
        for anchor in range(1, 15):
            f, reverse = frame(rows, 0, anchor), frame(rows, anchor, 0)
            assert f["partition"] == reverse["partition"] == partition
            expected = sorted(c for c in f["cycles"] if len(c) == 8)
            actual = direct_centered_motifs(rows, 0, anchor)
            assert actual == expected
            records.append({"edge": [0, anchor], "shell_cycle_sizes": sorted(map(len, f["cycles"])),
                            "centered_motif_shells": [list(c) for c in actual]})
        total = sum(len(r["centered_motif_shells"]) for r in records)
        assert total == 14 * partition.count(2)
        answer.append({"partition": partition, "root_incident_centered_motif_count": total,
                       "edge_records": records,
                       "scope": "matching-complete partial core; no full SRG claimed"})
    assert [a["root_incident_centered_motif_count"] for a in answer] == [42, 14, 0, 0]
    return {"source": file_record(STRUCTURE), "controls": answer,
            "direct_four_X_subset_checks": 4 * 14 * 495}


def build():
    rows = motif()
    check_graph(rows)
    aut = center_cycle_transports(rows, rows)
    assert len(aut) == 8
    preparation = json.loads(PREPARATION.read_text())
    entry, = [r for r in preparation["upper_bounds"] if r["coordinate"] == 521]
    assert entry["catalogue_type"] == 48936 and entry["automorphisms"] == 8
    transports = center_cycle_transports(rows, entry["rows"])
    assert len(transports) == 8
    row_export = json.loads(ROW_EXPORT.read_text())
    assert row_export["coordinate"] == 521 and row_export["catalogue_type"] == 48936
    assert row_export["automorphisms"] == 8 and row_export["stored_graph_rows"] == entry["rows"]
    assert row_export["ordinary_labelled_embedding_form"] == [[521, 8]]
    assert row_export["ordinary_unlabelled_count_form"] == [[521, 1]]
    assert row_export["induced_raw_form"] == [[521, 3628800]]
    assert row_export["induced_scale"] == preparation["scale"] == 3628800
    assert row_export["induced_unlabelled_count_form"] == [[521, 1]]
    assert row_export["reduced_cache_sha256"] == preparation["reduced_cache_sha256"]
    extraction_source = ROOT / "experiments/workspace/grid_free_order10_prism_zero_moments_loop.py"
    assert row_export["source_sha256"] == sha256(extraction_source.read_bytes()).hexdigest()
    point = json.loads(COUNT_POINT.read_text())
    point_value = point["rounded_core_values"][521]
    assert point_value == 133
    return {
        "status": "exact edge-component / order-ten bridge PASS",
        "source_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
        "scope": "unconditional motif identity; four edge types require global prism-freeness",
        "motif": {"vertices": 10, "edges": 17, "rows": rows,
                  "degree_sequence": sorted((r.bit_count() for r in rows), reverse=True),
                  "unique_centers": [0, 1], "center_edge": [0, 1],
                  "automorphism_candidate_count": 32, "automorphisms": aut,
                  "automorphism_order": 8, "chord_cap_witnesses": chord_audit(rows)},
        "catalogue": {"preparation": file_record(PREPARATION), "coordinate": 521,
                      "catalogue_type": 48936, "rows": entry["rows"],
                      "explicit_isomorphism": transports[0],
                      "old_generic_upper_bound": entry["ordinary_count_upper_bound"],
                      "reduction_row_export": file_record(ROW_EXPORT),
                      "reduction_export_source": file_record(extraction_source),
                      "exported_row": row_export},
        "prism_coordinate_audit": prism_coordinate_audit(preparation),
        "matching_audit": matching_audit(),
        "partial_controls": partial_audit(),
        "count_forms": {"dimension": 550,
                        "ordinary_unlabelled": [[521, 1]],
                        "induced_unlabelled": [[521, 1]],
                        "ordinary_labelled_embeddings": [[521, 8]],
                        "unconditional_nonnegative_row": [[0, 4158], [1, -3], [521, -2]],
                        "unconditional_upper_bound": 2079,
                        "prism_free_identity": {"e_222": 3, "e_24": 1}},
        "global_minimum_edge_cases": [
            {"minimum_type": [2, 2, 2], "x521_lower": 3, "x521_upper": 2079},
            {"minimum_type": [2, 4], "x521_lower": 1, "x521_upper": 693},
            {"minimum_type": [3, 3], "x521_lower": 0, "x521_upper": 0},
            {"minimum_type": [6], "x521_lower": 0, "x521_upper": 0}],
        "global_normalization_scope": "new union over globally minimum undirected edges; not each old fixed-root case",
        "existing_count_point": {"source": file_record(COUNT_POINT), "x521": point_value,
                                 "new_upper_bound_rejects_point": False,
                                 "zero_face_contains_point": False,
                                 "scope": "count-relaxation point, not a graph"},
        "solver_called": False, "dense_reduction_loaded": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="write the deterministic certificate")
    parser.add_argument("--certificate", type=Path, default=OUT)
    args = parser.parse_args()
    result = build()
    if args.write:
        args.certificate.parent.mkdir(parents=True, exist_ok=True)
        args.certificate.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    else:
        assert json.loads(args.certificate.read_text()) == result, "certificate differs from exact replay"
    print(json.dumps({"status": result["status"], "certificate": str(args.certificate.relative_to(ROOT)),
                      "source_sha256": result["source_sha256"], "matching_count": 10395,
                      "chord_witnesses": 28, "automorphism_order": 8,
                      "ordinary_coordinate": 521, "catalogue_type": 48936,
                      "root_incident_partial_control_counts": [42, 14, 0, 0],
                      "unconditional_row": "4158 - 3*x1 - 2*x521 >= 0",
                      "solver_called": False, "dense_reduction_loaded": False}, indent=2))


if __name__ == "__main__":
    main()
