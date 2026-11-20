"""Check all possible collisions of three-triangle-chain binary words.

Two chains with the same five-point word use at most nine vertices. The
complete cap-valid catalogue through nine therefore covers every collision.
This source neither loads a putative count point nor calls an optimizer.
"""
import argparse
from collections import Counter
import hashlib
from itertools import combinations
import json
from pathlib import Path
import pickle
import time

CATALOGUE_SHA = "1e1afe93518b0b3707031eed987b19e49bb237ea85e9165ae0f25f2b07a82057"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def members(mask):
    return [i for i in range(mask.bit_length()) if mask >> i & 1]


def triangles(rows):
    return [sum(1 << v for v in triple) for triple in combinations(range(len(rows)), 3)
            if all(rows[a] >> b & 1 for a, b in combinations(triple, 2))]


def chain_words(rows):
    ts = triangles(rows)
    words = {}
    count = 0
    for middle in ts:
        neighbors = [t for t in ts if (t & middle).bit_count() == 1]
        for left, right in combinations(neighbors, 2):
            a, b = left & middle, right & middle
            if a == b:
                continue
            assert left & right == 0
            word = left ^ middle ^ right
            assert word.bit_count() == 5
            center = middle ^ a ^ b
            assert center.bit_count() == 1
            c = members(center)[0]
            outer = members(word ^ center)
            assert len(outer) == 4 and rows[c] & word == 0
            induced_degrees = [sum(rows[v] >> u & 1 for u in outer) for v in outer]
            assert sorted(induced_degrees) in ([1, 1, 1, 1], [1, 1, 2, 2], [2, 2, 2, 2])
            words.setdefault(word, []).append({"middle": middle, "left": left, "right": right,
                                                "center": c, "tips": [members(a)[0], members(b)[0]]})
            count += 1
    return words, count


def rook_on_nine(rows):
    if len(rows) != 9 or any(mask.bit_count() != 4 for mask in rows):
        return False
    return all((rows[a] & rows[b]).bit_count() == (1 if rows[a] >> b & 1 else 2)
               for a, b in combinations(range(9), 2))


def verify_host(rows):
    words, chain_count = chain_words(rows)
    doubles = []
    shapes = Counter()
    for word, records in words.items():
        assert 1 <= len(records) <= 2
        c = records[0]["center"]
        assert all(r["center"] == c for r in records)
        outer = members(word ^ (1 << c))
        edges = [(a, b) for a, b in combinations(outer, 2) if rows[a] >> b & 1]
        matchings = [(e, f) for e, f in combinations(edges, 2) if set(e).isdisjoint(f)]
        assert len(records) <= len(matchings) <= 2
        shapes[str(len(edges))] += 1
        if len(records) == 1:
            continue
        assert len(edges) == 4
        tips = records[0]["tips"] + records[1]["tips"]
        assert len(set(tips)) == 4 and not any(word >> v & 1 for v in tips)
        union = set(members(word)) | set(tips)
        assert len(union) == 9
        # Every edge of the reconstructed nine-grid belongs to one of its
        # six triangles. Literal equality rejects any added edge.
        expected = set()
        for r in records:
            for t in (r["left"], r["middle"], r["right"]):
                expected.update(tuple(sorted(e)) for e in combinations(members(t), 2))
        actual = {(a, b) for a, b in combinations(sorted(union), 2) if rows[a] >> b & 1}
        assert len(expected) == 18 and actual == expected
        ordered = sorted(union)
        induced = [sum(((rows[v] >> u) & 1) << j for j, u in enumerate(ordered)) for v in ordered]
        assert rook_on_nine(induced)
        doubles.append([word, c, sorted(tips)])
    grid_count = int(rook_on_nine(rows))
    assert len(rows) <= 9
    assert len(doubles) == 9*grid_count
    assert len(words) == chain_count - 9*grid_count
    return {"triangles": len(triangles(rows)), "chains": chain_count, "distinct_words": len(words),
            "double_words": len(doubles), "grid_count": grid_count,
            "word_shape_by_outer_edge_count": dict(shapes)}


def run(catalogue, output, seconds):
    assert 0 < seconds <= 60 and not output.exists()
    start = time.monotonic()
    raw = catalogue.read_bytes()
    assert sha(raw) == CATALOGUE_SHA
    data = pickle.loads(raw)
    graphs, levels = data[0], data[1]
    assert [len(levels[n]) for n in (7, 8, 9)] == [208, 916, 5311]
    records, totals = [], Counter()
    for n in (7, 8, 9):
        for graph_id in levels[n]:
            if time.monotonic() - start > seconds:
                raise TimeoutError("bounded complete chain-collision check")
            checked = verify_host(tuple(graphs[graph_id]))
            records.append({"catalogue_type": graph_id, "order": n, **checked})
            for key in ("chains", "distinct_words", "double_words", "grid_count"):
                totals[key] += checked[key]
    assert len(records) == 6435 and totals["grid_count"] == 1 and totals["double_words"] == 9
    # Direct independently labelled rook control.
    rook = [sum(1 << j for j in range(9) if j != i and (i//3 == j//3 or i%3 == j%3))
            for i in range(9)]
    control = verify_host(rook)
    assert control["chains"] == 18 and control["distinct_words"] == control["double_words"] == 9
    record_raw = json.dumps(records, sort_keys=True, separators=(",", ":")).encode()
    report = {"status": "PASS_COMPLETE_THREE_TRIANGLE_CHAIN_COLLISION_CENSUS",
              "source_sha256": sha(Path(__file__).read_bytes()), "catalogue_sha256": CATALOGUE_SHA,
              "all_hosts_through_collision_order": 6435, "orders": [7, 8, 9],
              "totals": dict(totals), "all_host_records_sha256": sha(record_raw),
              "host_records": records, "literal_rook_control": control,
              "unconditional_chain_count_for_99": 231*3*6**2,
              "distinct_weight_five_word_count": "24948-9*g",
              "lower_bound_using_g_at_most_120": 24948-9*120,
              "count_point_loaded": False, "optimizer_called": False,
              "graph_existence_resolved": False, "seconds": time.monotonic()-start}
    output.write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps({k: v for k, v in report.items() if k != "host_records"}, indent=2))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--catalogue", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--seconds", type=float, default=60)
    a = p.parse_args()
    run(a.catalogue, a.output, a.seconds)


if __name__ == "__main__":
    main()
