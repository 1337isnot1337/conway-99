"""Independent complete visible-prism audit, with a separate F-cycle check.

The production prism count lists disjoint triangle pairs on every one of
the 5,805 literal edge-orbit representatives. It imports no census/model
source. F absence is checked by walking eight-cycles in exclusive-neighbor
shells, using the independently reviewed cap argument.
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
LOGS = ROOT / "experiments/logs/root-prism-free"
INPUTS = {
    "f0-boolean-fractional-model.json.gz": "703206929c9c85a40ac4ddcbfb1708c716c288482cf50c77a32249404e35b782",
    "f0-second-moments-preparation02.json.gz": "404d91da35c798ba248887c22a7500957947e24b71d5197dc44432460e6d219e",
    "f0-edge-motif-census01.json.gz": "397e8bf110e03a5accb5e6c1f27b2fb5525100acb67427c66669e188e74159d1",
}
SUBJECT = "experiments/workspace/root_prism_free_f0_edge_motif_census.py"
SUBJECT_SHA = "b9c5556bd503d72d2508bb03eb8d1b6be9ebadb0e0c25a1b79cec9870bc79009"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def members(mask):
    while mask:
        bit = mask & -mask
        yield bit.bit_length() - 1
        mask ^= bit


def caps(rows):
    n = len(rows)
    assert all(0 <= row < 1 << n and not (row >> i & 1) for i, row in enumerate(rows))
    for a, b in combinations(range(n), 2):
        assert (rows[a] >> b & 1) == (rows[b] >> a & 1)
        assert (rows[a] & rows[b]).bit_count() <= 2 - (rows[a] >> b & 1)


def triangle_prisms(rows):
    triangles = []
    for a in range(len(rows)):
        for b in members(rows[a] & ~((1 << (a + 1)) - 1)):
            for c in members(rows[a] & rows[b] & ~((1 << (b + 1)) - 1)):
                triangles.append(((a, b, c), (1 << a) | (1 << b) | (1 << c)))
    copies = set()
    counted = 0
    for (a, ma), (b, mb) in combinations(triangles, 2):
        if ma & mb:
            continue
        if all((rows[v] & mb).bit_count() == 1 for v in a) and all(
                (rows[v] & ma).bit_count() == 1 for v in b):
            counted += 1
            copies.add(tuple(sorted(a + b)))
    # A triangular prism has exactly its two disjoint triangle faces.
    assert len(copies) == counted
    return copies


def eight_cycle_f(rows):
    copies = set()
    for u in range(len(rows)):
        for v in members(rows[u] & ~((1 << (u + 1)) - 1)):
            left = rows[u] & ~rows[v] & ~(1 << v)
            right = rows[v] & ~rows[u] & ~(1 << u)
            assert left & right == 0
            shell = left | right
            neighbors = {w: tuple(members(rows[w] & shell)) for w in members(shell)}
            for w in neighbors:
                assert (rows[w] & left).bit_count() <= 1
                assert (rows[w] & right).bit_count() <= 1
            # Walk from every possible smallest vertex. No component routine
            # or saved shell witness is used.
            for start, adjacent in neighbors.items():
                if len(adjacent) != 2:
                    continue
                walk, previous, current = [start], start, min(adjacent)
                while current != start and current not in walk and len(walk) <= len(rows):
                    if len(neighbors[current]) != 2:
                        break
                    walk.append(current)
                    following = [w for w in neighbors[current] if w != previous]
                    assert len(following) == 1
                    previous, current = current, following[0]
                if current != start or len(walk) != 8 or start != min(walk):
                    continue
                assert sum(left >> w & 1 for w in walk) == 4
                assert sum(right >> w & 1 for w in walk) == 4
                sites = (u, v) + tuple(walk)
                mask = sum(1 << w for w in sites)
                assert [(rows[w] & mask).bit_count() for w in sites] == [5, 5] + [3] * 8
                key = tuple(sorted(sites))
                assert key not in copies  # degree-five centers are intrinsic
                copies.add(key)
    return copies


def graph(core, triples, a, b):
    rows = list(core) + [0, 0]
    for vertex, signature in ((21, triples[a]), (22, triples[b])):
        for j in signature:
            rows[vertex] |= 1 << (j + 3)
            rows[j + 3] |= 1 << vertex
    rows[21] |= 1 << 22
    rows[22] |= 1 << 21
    return rows


def derive_core_maps(core, triples, actions):
    incidence = [frozenset(a for a, h in enumerate(triples) if i in h) for i in range(18)]
    index = {s: i for i, s in enumerate(incidence)}
    assert len(index) == 18
    fibers = [frozenset(i for i in range(18) if core[t] >> (i + 3) & 1) for t in range(3)]
    fiber_index = {s: i for i, s in enumerate(fibers)}
    answer = []
    for action in actions:
        assert sorted(action) == list(range(480))
        move = [index[frozenset(action[a] for a in support)] for support in incidence]
        top = [fiber_index[frozenset(move[i] for i in f)] for f in fibers]
        whole = top + [i + 3 for i in move]
        assert sorted(whole) == list(range(21))
        assert all((core[i] >> j & 1) == (core[whole[i]] >> whole[j] & 1)
                   for i in range(21) for j in range(21))
        assert all(sorted(move[i] for i in h) == triples[action[a]] for a, h in enumerate(triples))
        answer.append(whole)
    group = set(map(tuple, actions))
    assert len(group) == 12 and tuple(range(480)) in group
    assert all(tuple(g[h[a]] for a in range(480)) in group for g in actions for h in actions)
    return answer


def controls():
    def make(n, edges):
        rows = [0] * n
        for a, b in edges:
            rows[a] |= 1 << b
            rows[b] |= 1 << a
        return rows
    prism = make(6, list(combinations(range(3), 2)) + list(combinations(range(3, 6), 2))
                 + [(0, 3), (1, 4), (2, 5)])
    f = make(10, [(0, 1)] + [(0, i) for i in range(2, 6)] + [(1, i) for i in range(6, 10)]
             + [(2, 3), (4, 5), (6, 7), (8, 9), (3, 6), (7, 4), (5, 8), (9, 2)])
    rook = [sum(1 << j for j in range(9) if i != j and (i // 3 == j // 3 or i % 3 == j % 3))
            for i in range(9)]
    cases = [(prism, 1, 0), (f, 0, 1), (rook, 6, 0), (prism + [0] * 4, 1, 0),
             (f + [0] * 2, 0, 1), ([0] * 8, 0, 0)]
    for original in (prism, f):
        for a, b in combinations(range(len(original)), 2):
            if not (original[a] >> b & 1):
                continue
            deleted = original[:]
            deleted[a] ^= 1 << b
            deleted[b] ^= 1 << a
            cases.append((deleted, 0, 0))
    for rows, p, f_count in cases:
        caps(rows)
        assert len(triangle_prisms(rows)) == p and len(eight_cycle_f(rows)) == f_count
    return len(cases)


def audit():
    started = time.monotonic()
    assert sha((ROOT / SUBJECT).read_bytes()) == SUBJECT_SHA
    loaded = []
    for filename, expected in INPUTS.items():
        raw = (LOGS / filename).read_bytes()
        assert sha(raw) == expected
        loaded.append(json.loads(gzip.decompress(raw)))
    baseline, moments, subject = loaded
    data = baseline["validation"]
    core, triples, edges = data["core"], data["triples"], data["edges"]
    actions = moments["selector_actions"]
    maps = derive_core_maps(core, triples, actions)
    assert len(triples) == 480 and len(edges) == 68394
    component = [[core[i + 3] >> (j + 3) & 1 for j in range(18)] for i in range(18)]
    targets = [[2 - int(i in h) - sum(component[i][j] for j in h) for i in range(18)] for h in triples]
    assert targets == data["targets"]
    sets = list(map(set, triples))
    recovered = [[a, b] for a in range(480) for b in range(a + 1, 480)
                 if len(sets[a] & sets[b]) <= 1 and all(targets[a][i] > 0 for i in triples[b])
                 and all(targets[b][i] > 0 for i in triples[a])]
    assert recovered == edges
    index = {tuple(pair): i for i, pair in enumerate(edges)}
    assert len(data["edge_orbits"]) == len(subject["orbits"]) == 5805
    control_count = controls()
    caps(core)
    assert not triangle_prisms(core) and not eight_cycle_f(core)
    checked, histogram, zeros, all_edges = [], Counter(), [], set()
    representatives = {}
    for orbit, (entries, record) in enumerate(zip(data["edge_orbits"], subject["orbits"])):
        assert entries == sorted(set(entries)) and not all_edges.intersection(entries)
        all_edges.update(entries)
        a, b = edges[entries[0]]
        assert record["edge_orbit"] == orbit and record["literal_edge_ids"] == entries
        assert record["representative_edge"] == [a, b]
        transported = {index[tuple(sorted((g[a], g[b])))] for g in actions}
        assert transported == set(entries)
        rows = graph(core, triples, a, b)
        caps(rows)
        prisms, fs = triangle_prisms(rows), eight_cycle_f(rows)
        assert len(prisms) == record["prisms"] and len(fs) == record["F_motifs"]
        assert not fs
        histogram[len(prisms)] += 1
        checked.append([orbit, len(prisms), len(fs)])
        if prisms:
            zeros.append(42 + orbit)
            representatives[orbit] = (a, b, prisms)
        assert time.monotonic() - started < 60, "independent audit exceeded its declared bound"
    assert all_edges == set(range(68394))
    assert zeros == subject["forced_zero_original_Y_variables"] and len(zeros) == 162
    witnessed = set()
    for record in subject["literal_motif_witnesses"]:
        ei, orbit = record["edge_id"], record["edge_orbit"]
        assert ei not in witnessed and record["kind"] == "P"
        witnessed.add(ei)
        a, b = edges[ei]
        assert record["pair"] == [a, b] and ei in data["edge_orbits"][orbit]
        rows = graph(core, triples, a, b)
        sites = record["sites"]
        assert len(sites) == len(set(sites)) == 6
        first, second = sites[:3], sites[3:]
        assert all(rows[u] >> v & 1 for triangle in (first, second) for u, v in combinations(triangle, 2))
        assert all(sum(rows[u] >> v & 1 for v in second) == 1 for u in first)
        assert all(sum(rows[v] >> u & 1 for u in first) == 1 for v in second)
        ra, rb, copies = representatives[orbit]
        gi = record["action_index"]
        g, core_map = actions[gi], maps[gi]
        assert sorted((g[ra], g[rb])) == [a, b]
        mapping = core_map + ([21, 22] if g[ra] < g[rb] else [22, 21])
        old_sites = subject["orbits"][orbit]["witnesses"]["P"]["sites"]
        assert tuple(sorted(old_sites)) in copies
        assert sites == [mapping[v] for v in old_sites]
    forbidden = {ei for y in zeros for ei in data["edge_orbits"][y - 42]}
    assert witnessed == forbidden and len(witnessed) == 1884
    assert subject["census"] == {"edge_orbits_checked": 5805, "literal_edges_covered": 68394,
                                "orbits_P": 162, "literal_P": 1884,
                                "orbits_neither": 5643, "literal_neither": 66510}
    return {"status": "PASS: independent full prism census, F-cycle absence and all literal witnesses",
            "source_sha256": sha(Path(__file__).read_bytes()), "subject_sha256": SUBJECT_SHA,
            "inputs": INPUTS, "edge_orbits": 5805, "eligible_edges": 68394,
            "prism_orbits": 162, "prism_edges": 1884, "F_orbits": 0,
            "representative_prism_count_histogram": dict(sorted(histogram.items())),
            "complete_counts_sha256": sha(canonical(checked)), "controls": control_count,
            "all12_core_maps_reconstructed_and_group_checked": True,
            "all1884_literal_witnesses_and_transports_checked": True,
            "prism_method": "unordered disjoint triangle pairs, cross degree one at all six vertices",
            "F_method": "independent directed walks of eight-cycle exclusive-neighbor shells",
            "edge_shell_completeness_proof_reviewed": True,
            "scope": "Necessary Y zeros under global prism-freeness; no completion or component exclusion.",
            "subject_imports": 0, "model_rebuilds": 0, "optimizer_calls": 0,
            "seconds": time.monotonic() - started}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    result = audit()
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
