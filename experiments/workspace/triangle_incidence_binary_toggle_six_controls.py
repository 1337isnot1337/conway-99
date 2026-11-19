"""Literal weighted-chain and six-word toggle controls, without optimization."""
import argparse
from collections import Counter
import hashlib
from itertools import combinations
import json
from pathlib import Path
import pickle

import triangle_chain_binary_words as chains
import triangle_incidence_binary_replacement_words as codes

CHAIN_SHA = "34bfb0832a6f1bf49db3ee6e39dd68baf4e1ce650f62723992f344f6421bed57"
CODES_SHA = "993fcdb85f2e4c50e5bb86a86d4a8a5a2ae75b3e0bac85453a25f6b4234e3c62"
OLD_REPORT_SHA = "c2e4fcda3a4f578a75ed2c01a47e816807c4ac4ee4a50d3518fb2c4d479937ef"


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def weighted_chains(graphs, levels):
    results = []
    totals = Counter()
    for n in (7, 8, 9):
        for gid in levels[n]:
            rows = tuple(graphs[gid])
            words, count = chains.chain_words(rows)
            raw_edges = unique_edges = double_words = 0
            for word, records in words.items():
                vertices = chains.members(word)
                edges = sum((rows[a] >> b) & 1 for a, b in combinations(vertices, 2))
                assert edges in (2, 3, 4) and len(records) in (1, 2)
                unique_edges += edges
                for record in records:
                    left, right = chains.members(record["left"]), chains.members(record["right"])
                    cross = sum((rows[a] >> b) & 1 for a in left for b in right)
                    assert edges == cross+1
                    raw_edges += edges
                if len(records) == 2:
                    assert edges == 4
                    double_words += 1
            assert raw_edges-unique_edges == 4*double_words
            assert len(words) == count-double_words
            assert 5*len(words)-unique_edges == 5*count-raw_edges-double_words
            edges = [(a, b) for a, b in combinations(range(n), 2) if (rows[a] >> b) & 1]
            complete_edges = all((rows[a] & rows[b]).bit_count() == 1 for a, b in edges)
            if complete_edges:
                ts = chains.triangles(rows); populations = Counter()
                for i, left in enumerate(ts):
                    for right in ts[:i]:
                        if not left & right:
                            e = sum((rows[a] >> b) & 1 for a in chains.members(left) for b in chains.members(right))
                            assert 0 <= e <= 3
                            populations[e] += 1
                c4 = 0
                for subset in combinations(range(n), 4):
                    mask = sum(1 << v for v in subset)
                    c4 += all((rows[v] & mask).bit_count() == 2 for v in subset)
                assert populations[2]+3*populations[3] == 2*c4
                assert populations[1]+2*populations[2]+3*populations[3] == count
                assert 2*populations[1]+6*populations[2]+12*populations[3] == raw_edges
                totals["complete_edge_hosts"] += 1
            if count:
                results.append({"host": gid, "chains": count, "words": len(words),
                    "raw_edge_sum": raw_edges, "unique_edge_sum": unique_edges,
                    "double_words": double_words, "all_edge_tips_present": complete_edges})
            totals["hosts"] += 1; totals["chains"] += count
            totals["raw_edge_sum"] += raw_edges; totals["unique_edge_sum"] += unique_edges
    assert totals["hosts"] == 6435 and totals["chains"] == 537
    return {"totals": dict(totals), "nonempty_hosts": results}


def six_word_controls():
    records = []
    for name, rows in codes.hosts():
        n = len(rows); r = rows[0].bit_count()//2
        ts = chains.triangles(rows); number = len(ts)
        cap_two = all((rows[a] & rows[b]).bit_count() <= 2 for a, b in combinations(range(n), 2))
        kernel = [w for w in range(1 << n) if all((w & t).bit_count() % 2 == 0 for t in ts)]
        profiles = []
        for size in range(1, 7):
            for subset in combinations(range(n), size):
                mask = sum(1 << v for v in subset)
                value = 0
                if size == 6:
                    value = sum((rows[a] >> b) & 1 for a, b in combinations(subset, 2))
                    value -= 3*sum(mask & t == t for t in ts)
                    if cap_two:
                        assert 0 <= value <= 7
                profiles.append((size, subset, value))
        disjoint, cross_total = 0, 0
        for i, left in enumerate(ts):
            for right in ts[:i]:
                if not left & right:
                    disjoint += 1
                    cross_total += sum((rows[a] >> b) & 1 for a in chains.members(left) for b in chains.members(right))
        cases = []
        for code in codes.all_subspaces(kernel):
            labels = [sum(((w >> v) & 1) << i for i, w in enumerate(sorted(code))) for v in range(n)]
            B = [1]+[0]*6; S6 = 0
            for size, subset, value in profiles:
                label = 0
                for v in subset:
                    label ^= labels[v]
                if label == 0:
                    B[size] += 1
                    if size == 6:
                        S6 += value
            expected = (5*r*B[5]-8*r*B[4]+12*r*B[3]-(10*r+3*number)*B[2]
                        +(7*r+6*number)*B[1]-12*number)
            assert S6 == expected
            assert S6 >= cross_total
            if cap_two:
                assert S6 <= 7*B[6]-(7*disjoint-cross_total)
            cases.append({"code_size": len(code), "B1_to_B6": B[1:], "S6": S6})
        records.append({"host": name, "subcodes": len(cases), "cap_two": cap_two,
                        "disjoint_triangle_pairs": disjoint, "cross_edge_sum": cross_total, "cases": cases})
    assert sum(r["subcodes"] for r in records) == 508
    return records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalogue", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    assert digest(chains.__file__) == CHAIN_SHA and digest(codes.__file__) == CODES_SHA
    prior = Path(__file__).resolve().parents[1]/"logs/grids-and-triangles/triangle-chain-binary-words-census.json"
    assert digest(prior) == OLD_REPORT_SHA and digest(args.catalogue) == chains.CATALOGUE_SHA
    data = pickle.loads(args.catalogue.read_bytes()); graphs, levels = data[:2]
    small = []
    for n, upper in ((5, 5), (6, 7)):
        values = []
        for gid in levels[n]:
            rows = graphs[gid]
            value = sum(row.bit_count() for row in rows)//2-3*len(chains.triangles(rows))
            assert 0 <= value <= upper
            values.append([gid, value])
        assert max(v for _, v in values) == upper
        small.append({"order": n, "all_hosts": len(values), "maximum_e_minus_3t": upper, "values": values})
    report = {"status": "PASS_WEIGHTED_CHAIN_AND_SIX_WORD_IDENTITIES",
        "source_sha256": digest(__file__), "chain_source_sha256": CHAIN_SHA,
        "code_control_source_sha256": CODES_SHA, "prior_collision_report_sha256": OLD_REPORT_SHA,
        "catalogue_sha256": chains.CATALOGUE_SHA, "small_induced_graph_bounds": small,
        "weighted_chains": weighted_chains(graphs, levels),
        "six_word_subcode_controls": six_word_controls(), "optimizer_calls": 0,
        "target_S6": "35B5-56B4+84B3-763B2+1435B1-2772",
        "target_chain_edge_sum": "58212-36g", "target_chain_five_edge_deficit": "66528-9g"}
    args.output.write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps({"status": report["status"], "source_sha256": report["source_sha256"],
        "weighted_chain_totals": report["weighted_chains"]["totals"],
        "subcodes": 508, "five_vertex_hosts": len(levels[5]), "six_vertex_hosts": len(levels[6])}, indent=2))


if __name__ == "__main__":
    main()
