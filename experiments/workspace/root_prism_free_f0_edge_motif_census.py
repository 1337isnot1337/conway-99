"""Complete visible P/F census for all eligible F0 exterior-edge states.

Every one of 5805 actual-core edge orbits is tested on its literal23-core.
Witnesses are transported to all68394 eligible edges. No point or solver.
In a cap-valid graph, the exclusive-neighbor shell of an edge has maximum
degree two: at most one same-side and at most one opposite-side neighbor.
Its four/eight-cycle components are exactly visible prisms/F motifs.
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
BASE = "experiments/logs/root-prism-free/"
INPUTS = {
    "domain": (BASE+"f0-boolean-fractional-model.json.gz", "703206929c9c85a40ac4ddcbfb1708c716c288482cf50c77a32249404e35b782"),
    "moments": (BASE+"f0-second-moments-preparation02.json.gz", "404d91da35c798ba248887c22a7500957947e24b71d5197dc44432460e6d219e"),
    "actions": (BASE+"f0-graph-schur-kernels01.json.gz", "65f1ad0d0015a6eff3d97c676fb0e188f57f9dee00e9245758a28bab2069b40d"),
    "control": (BASE+"f0-pair-clauses.json.gz", "47e9d8f518fab10aee604f33df1f22c97b0d201a1af4180e4307553e4857672f"),
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


def induced(rows, sites):
    assert len(sites) == len(set(sites))
    return [sum(((rows[v] >> w) & 1) << j for j, w in enumerate(sites)) for v in sites]


def caps(rows):
    assert all(not ((row >> i) & 1) for i, row in enumerate(rows))
    assert all(((rows[i] >> j) & 1) == ((rows[j] >> i) & 1)
               for i in range(len(rows)) for j in range(i))
    return all((rows[i] & rows[j]).bit_count() <= 2-((rows[i] >> j) & 1)
               for i in range(len(rows)) for j in range(i))


def is_prism(rows):
    if len(rows) != 6 or any(row.bit_count() != 3 for row in rows):
        return False
    return (all((rows[a] >> b) & 1 for side in (range(3), range(3, 6)) for a, b in combinations(side, 2))
            and all(sum((rows[a] >> b) & 1 for b in range(3, 6)) == 1 for a in range(3))
            and all(sum((rows[b] >> a) & 1 for a in range(3)) == 1 for b in range(3, 6)))


def is_f(rows):
    if len(rows) != 10 or [r.bit_count() for r in rows] != [5, 5]+[3]*8 or not (rows[0] & 2):
        return False
    if any((rows[v] & 3).bit_count() != 1 for v in range(2, 10)):
        return False
    shell = ((1 << 10)-1) ^ 3
    reached, frontier = 0, 1 << 2
    while frontier:
        reached |= frontier
        frontier = sum(1 << v for v in members(shell & ~reached)
                       if rows[v] & frontier)
    if reached != shell:
        return False
    return all((rows[v] & shell).bit_count() == 2
               and sum((rows[v] >> w) & 1 for w in range(2, 10)
                       if (rows[w] & 3) == (rows[v] & 3)) == 1 for v in range(2, 10))


def motifs(rows):
    assert caps(rows)
    counts = Counter()
    witnesses = {}
    for u in range(len(rows)):
        for v in members(rows[u] & ~((1 << (u+1))-1)):
            common = rows[u] & rows[v]
            left = rows[u] & ~(common | (1 << v))
            right = rows[v] & ~(common | (1 << u))
            assert not (left & right)
            shell = left | right
            for w in members(shell):
                assert (rows[w] & left).bit_count() <= 1
                assert (rows[w] & right).bit_count() <= 1
            remaining = shell
            while remaining:
                component = 0
                frontier = remaining & -remaining
                while frontier:
                    component |= frontier
                    next_frontier = 0
                    for w in members(frontier):
                        next_frontier |= rows[w] & shell
                    frontier = next_frontier & ~component
                remaining &= ~component
                size = component.bit_count()
                if size not in (4, 8) or any((rows[w] & shell).bit_count() != 2 for w in members(component)):
                    continue
                a, b = list(members(left & component)), list(members(right & component))
                assert len(a) == len(b) == size//2
                kind = "P" if size == 4 else "F"
                sites = [u]+a+[v]+b if kind == "P" else [u, v]+a+b
                small = induced(rows, sites)
                assert (is_prism if kind == "P" else is_f)(small)
                counts[kind] += 1
                witnesses.setdefault(kind, {"sites": sites, "induced_rows": small,
                                             "center_edge": [u, v], "shell_component": list(members(component))})
    assert counts["P"] % 3 == 0
    return {"prisms": counts["P"]//3, "F_motifs": counts["F"], "witnesses": witnesses}


def direct_prisms(rows):
    triangles = [t for t in combinations(range(len(rows)), 3)
                 if all((rows[a] >> b) & 1 for a, b in combinations(t, 2))]
    return sum(not (set(a) & set(b)) and is_prism(induced(rows, list(a)+list(b)))
               for a, b in combinations(triangles, 2))


def controls(f_fixture):
    prism = [0]*6
    for a, b in list(combinations(range(3), 2))+list(combinations(range(3, 6), 2))+[(0, 3), (1, 4), (2, 5)]:
        prism[a] |= 1 << b; prism[b] |= 1 << a
    rook = [sum(1 << j for j in range(9) if i != j and (i//3 == j//3 or i % 3 == j % 3)) for i in range(9)]
    assert is_prism(prism) and is_f(f_fixture)
    graphs = [prism, rook, f_fixture, prism+[0]*4, f_fixture+[0]*2, [0]*8]
    for original in (prism, f_fixture):
        for a in range(len(original)):
            for b in members(original[a] & ~((1 << (a+1))-1)):
                rows = original[:]
                rows[a] ^= 1 << b; rows[b] ^= 1 << a
                graphs.append(rows)
    records = []
    for rows in graphs:
        found = motifs(rows)
        assert found["prisms"] == direct_prisms(rows)
        expected_f = 1 if rows in (f_fixture, f_fixture+[0]*2) else 0
        assert found["F_motifs"] == expected_f
        records.append({"order": len(rows), "edges": sum(r.bit_count() for r in rows)//2,
                        "prisms": found["prisms"], "F_motifs": found["F_motifs"]})
    return {"exact_fixture_and_edge_deletion_controls": len(graphs), "records": records,
            "prisms_independently_counted_by_disjoint_triangle_pairs": True}


def partial(core, triples, a, b):
    rows = core[:]+[0, 0]
    for vertex, signature in ((21, triples[a]), (22, triples[b])):
        for j in signature:
            rows[vertex] |= 1 << (j+3)
            rows[j+3] |= 1 << vertex
    rows[21] |= 1 << 22; rows[22] |= 1 << 21
    return rows


def build(seconds):
    start = time.monotonic()
    deadline = start+seconds
    loaded = {}
    for key, (path, expected) in INPUTS.items():
        raw = (ROOT/path).read_bytes()
        assert sha(raw) == expected
        loaded[key] = json.loads(gzip.decompress(raw))
    data = loaded["domain"]["validation"]
    core, triples, edges = data["core"], data["triples"], data["edges"]
    actions = loaded["moments"]["selector_actions"]
    core_actions = loaded["actions"]["domain"]["reconstructed21_core_actions"]
    orbits = data["edge_orbits"]
    assert len(core) == 21 and len(triples) == 480 and len(edges) == 68394 and len(orbits) == 5805
    assert len(actions) == len(core_actions) == 12
    assert motifs(core)["witnesses"] == {}
    adjacency = [[(core[i+3] >> (j+3)) & 1 for j in range(18)] for i in range(18)]
    targets = [[2-int(i in h)-sum(adjacency[i][j] for j in h) for i in range(18)] for h in triples]
    sets = list(map(set, triples))
    recovered_edges = [[a, b] for a in range(480) for b in range(a+1, 480)
                       if len(sets[a] & sets[b]) <= 1
                       and all(targets[a][i] > 0 for i in triples[b])
                       and all(targets[b][i] > 0 for i in triples[a])]
    assert recovered_edges == edges and targets == data["targets"]
    edge_index = {tuple(e): i for i, e in enumerate(edges)}
    for g, move in zip(actions, core_actions):
        assert sorted(g) == list(range(480)) and sorted(move) == list(range(21))
        assert all(((core[i] >> j) & 1) == ((core[move[i]] >> move[j]) & 1)
                   for i in range(21) for j in range(21))
        assert all(sorted(move[i+3]-3 for i in h) == triples[g[a]] for a, h in enumerate(triples))
    fixture = loaded["control"]["representatives"][0]["F_conflicts"][0]["induced_motif_rows"]
    control = controls(fixture)
    seen = set(); records = []; counts = Counter(); zeros = []; literal_witnesses = []
    for orbit, entries in enumerate(orbits):
        if orbit % 100 == 0:
            assert time.monotonic() < deadline, "bounded motif census timed out"
        assert entries == sorted(set(entries)) and not (seen & set(entries)); seen.update(entries)
        a, b = edges[entries[0]]
        transports = {}
        for gi, g in enumerate(actions):
            moved = tuple(sorted((g[a], g[b])))
            transports.setdefault(edge_index[moved], gi)
        assert sorted(transports) == entries
        found = motifs(partial(core, triples, a, b))
        record = {"edge_orbit": orbit, "representative_edge": [a, b],
                  "literal_edge_ids": entries, **found}
        records.append(record)
        counts["edge_orbits_checked"] += 1; counts["literal_edges_covered"] += len(entries)
        kinds = sorted(found["witnesses"])
        counts["orbits_"+("_".join(kinds) if kinds else "neither")] += 1
        counts["literal_"+("_".join(kinds) if kinds else "neither")] += len(entries)
        if kinds:
            zeros.append(42+orbit)
            for ei in entries:
                gi = transports[ei]; g = actions[gi]
                mapping = core_actions[gi]+([21, 22] if g[a] < g[b] else [22, 21])
                aa, bb = edges[ei]
                rows = partial(core, triples, aa, bb)
                for kind, witness in found["witnesses"].items():
                    sites = [mapping[v] for v in witness["sites"]]
                    small = induced(rows, sites)
                    assert small == witness["induced_rows"]
                    assert (is_prism if kind == "P" else is_f)(small)
                    literal_witnesses.append({"edge_id": ei, "edge_orbit": orbit, "pair": [aa, bb],
                                              "kind": kind, "action_index": gi, "sites": sites})
        if orbit % 1000 == 0:
            print(json.dumps({"completed_edge_orbits": orbit+1, "forced_Y_zero_orbits": len(zeros)}), flush=True)
    assert seen == set(range(68394)) and len(records) == 5805
    assert time.monotonic() < deadline, "bounded motif census timed out"
    return {"status": "COMPLETE_EXACT_VISIBLE_EDGE_MOTIF_CENSUS", "source_sha256": sha(Path(__file__).read_bytes()),
            "inputs": {k: {"path": p, "sha256": h} for k, (p, h) in INPUTS.items()},
            "controls": control, "census": dict(counts), "orbits": records,
            "literal_motif_witnesses": literal_witnesses, "forced_zero_original_Y_variables": zeros,
            "full480_signature_domain_retained": True, "all68394_eligible_edges_covered": True,
            "complete_visible_P_and_F_detection_on_each_23_core": True,
            "point_loaded": False, "optimizer_calls": 0,
            "scope": "Necessary Y zeros for component0 in the globally P/F-free split18+18 case; no larger completion claim."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "replay"))
    parser.add_argument("--record", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seconds", type=float, default=60)
    args = parser.parse_args()
    assert 0 < args.seconds <= 60 and not args.output.exists()
    started = time.monotonic()
    result = build(args.seconds)
    raw = canonical(result)
    if args.mode == "prepare":
        assert not args.record.exists()
        args.record.write_bytes(gzip.compress(raw, mtime=0))
    else:
        assert canonical(json.loads(gzip.decompress(args.record.read_bytes()))) == raw
    summary = {"status": "PASS: complete edge-motif census "+("prepared" if args.mode == "prepare" else "cold replayed"),
               "source_sha256": result["source_sha256"], "record_sha256": sha(args.record.read_bytes()),
               "raw_record_sha256": sha(raw), "census": result["census"],
               "forced_Y_zero_orbits": len(result["forced_zero_original_Y_variables"]),
               "literal_motif_witnesses": len(result["literal_motif_witnesses"]),
               "point_loaded": False, "optimizer_calls": 0, "seconds": time.monotonic()-started}
    args.output.write_text(json.dumps(summary, indent=2)+"\n")
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()
