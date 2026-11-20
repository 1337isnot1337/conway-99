"""Independent literal check of every passing saved-set matching.

No diagnostic source is imported and no rejected matching is rerun.
Adjacency matrices are reconstructed from the immutable core/signatures.
"""
import argparse
import gzip
import hashlib
from itertools import combinations
import json
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[2]
BASE = "experiments/logs/root-prism-free/"
INPUTS = {
    "point": (BASE+"f0-local-center355-pilot01/result.json",
              "691770408d6af35c86cd06004344b51159dbd6ba8ceafd2b185b5764ee37cd0e"),
    "diagnostic": (BASE+"f0-local-center355-matching-diagnostic02.json",
                    "18375b3c9f1a32eb62abdd7ea118f609dd712cee080227bb23d41cf910fc0d5d"),
    "domain": (BASE+"f0-boolean-fractional-model.json.gz",
               "703206929c9c85a40ac4ddcbfb1708c716c288482cf50c77a32249404e35b782"),
    "edge_zeros": (BASE+"f0-edge-motif-census01.json.gz",
                   "397e8bf110e03a5accb5e6c1f27b2fb5525100acb67427c66669e188e74159d1"),
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def triangle_pairs(matrix):
    n = len(matrix)
    triangles = []
    for a, b in combinations(range(n), 2):
        if not matrix[a][b]:
            continue
        for c in range(b+1, n):
            if matrix[a][c] and matrix[b][c]:
                triangles.append((a, b, c))
    prisms = []
    for t, u in combinations(triangles, 2):
        if len(set(t+u)) != 6:
            continue
        cross = [[matrix[a][b] for b in u] for a in t]
        if all(sum(row) == 1 for row in cross) and all(sum(cross[i][j] for i in range(3)) == 1 for j in range(3)):
            prisms.append([list(t), list(u)])
    return triangles, prisms


def run():
    started = time.monotonic()
    loaded = {}
    for name, (path, digest) in INPUTS.items():
        raw = (ROOT/path).read_bytes()
        assert sha(raw) == digest
        loaded[name] = json.loads(gzip.decompress(raw) if path.endswith(".gz") else raw)
    rook = [[int(a != b and (a//3 == b//3 or a % 3 == b % 3)) for b in range(9)] for a in range(9)]
    assert len(triangle_pairs(rook)[1]) == 6
    d = loaded["domain"]["validation"]
    point, diagnostic = loaded["point"], loaded["diagnostic"]
    assert point["status"] == "SAT_EXACT_LOCAL_BOOLEAN_NEIGHBOR_WITNESS"
    assert diagnostic["status"] == "COMPLETE_SAVED_NEIGHBOR_MATCHING_DIAGNOSTIC"
    cases = diagnostic["passing_matchings"]
    assert len(cases) == 10 and len({tuple(map(tuple, c["matching"])) for c in cases}) == 10
    witness = point["native_witness"]
    selected = witness["selected_neighbor_ids"]
    assert len(selected) == 8 and selected == sorted(set(selected))
    signatures = [d["triples"][a] for a in selected]
    assert signatures == witness["selected_neighbor_signatures"]
    assert [sum(i in h for h in signatures) for i in range(18)] == d["targets"][355]
    edges = {tuple(e): i for i, e in enumerate(d["edges"])}
    ymap = {e: 42+o for o, orbit in enumerate(d["edge_orbits"]) for e in orbit}
    zero = set(loaded["edge_zeros"]["forced_zero_original_Y_variables"])
    checked = []
    for case in cases:
        pairs = case["matching"]
        assert len(pairs) in (2, 3)
        endpoints = [a for edge in pairs for a in edge]
        assert len(set(endpoints)) == len(endpoints) and all(0 <= a < 7 for a in endpoints)
        matrix = [[0]*30 for _ in range(30)]
        for a in range(21):
            for b in range(21):
                matrix[a][b] = (d["core"][a] >> b) & 1
        for a, h in enumerate([d["triples"][355]]+signatures, start=21):
            for i in h:
                matrix[a][i+3] = matrix[i+3][a] = 1
        for a in range(22, 30):
            matrix[21][a] = matrix[a][21] = 1
        for a, b in pairs:
            assert not (set(signatures[a]) & set(signatures[b]))
            key = tuple(sorted((selected[a], selected[b])))
            assert key in edges and ymap[edges[key]] not in zero
            matrix[22+a][22+b] = matrix[22+b][22+a] = 1
        assert all(matrix[a][b] == matrix[b][a] and (a != b or matrix[a][b] == 0)
                   for a in range(30) for b in range(30))
        for a, b in combinations(range(30), 2):
            common = sum(matrix[a][j]*matrix[b][j] for j in range(30))
            assert common+matrix[a][b] <= 2
        neighbors = [a for a in range(30) if matrix[21][a]]
        assert len(neighbors) == 11
        local_degrees = [sum(matrix[a][b] for b in neighbors) for a in neighbors]
        assert all(q <= 1 for q in local_degrees)
        assert sum(q == 0 for q in local_degrees) == 7-2*len(pairs) == case["unmatched_X_count"]
        triangles, prisms = triangle_pairs(matrix)
        assert not prisms
        checked.append({"matching": pairs,
                        "signature_edges": [[selected[a], selected[b]] for a, b in pairs],
                        "triangle_count": len(triangles), "cap_checks": 435,
                        "unmatched_X_count": case["unmatched_X_count"],
                        "partial_adjacency_rows": [sum(value << b for b, value in enumerate(row)) for row in matrix]})
    return {"status": "PASS: all ten claimed matching witnesses checked independently",
            "source_sha256": sha(Path(__file__).read_bytes()),
            "inputs": {k: {"path": p, "sha256": h} for k, (p, h) in INPUTS.items()},
            "subject_source_imported": False, "rejected_matching_ledger_repeated": False,
            "positive_rook_control_prisms": 6, "passing_cases_checked": 10,
            "visible_cap_checks": 4350, "checked_matchings": checked,
            "optimizer_calls": 0, "graph_completion_claimed": False,
            "scope": "The saved eight-neighbor set admits all ten listed visible matching extensions. This checks their positivity, not the rejection ledger.",
            "seconds": time.monotonic()-started}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    result = run()
    args.output.write_text(json.dumps(result, indent=2)+"\n")
    print(json.dumps({k: v for k, v in result.items() if k != "checked_matchings"}, indent=2))
