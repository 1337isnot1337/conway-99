"""Independent augmented-matrix ranks over F2 and F3.

No producer is imported. Selector/constant columns precede edge columns,
Gram rows are inserted first, and highest pivots are eliminated while the
original shared rows are processed backwards. The producer uses the
opposite pivot direction and separately carries selector consequences.
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[2]
DOMAIN = ("experiments/logs/root-prism-free/f0-exterior-row-domains02.json.gz", "665563b75fa6fc23caa9a002621cc4047809af28543b52b5c2a7ffa592d05dd4")
CASES = {
    2: {"source": ("experiments/workspace/root_prism_free_f0_shared_mod2_projection.py", "a548fe26b54a559909bece50df984e0755d9321adc7e8a41d0b6e836c8b34fd5"),
        "report": ("experiments/logs/root-prism-free/f0-shared-mod2-projection01/report.json", "e794dfc28b83296833d158e0732e9b786f430f7c682f294d171a74dc2cb7eebc"),
        "owner": ("experiments/logs/root-prism-free/f0-shared-mod2-projection01-owner/supervisor.json", "355e6249ec823670abc2d43026465c93c8fd812fad7b32c9a39d28018a405e6b"), "rows_per_anchor": 18, "edge_rank": 7713},
    3: {"source": ("experiments/workspace/root_prism_free_f0_shared_mod3_projection.py", "1911a2b75fd22f5eda3dad0303d26663bc03819b14bdeae945ef89ba3833b5f7"),
        "report": ("experiments/logs/root-prism-free/f0-shared-mod3-projection01/report.json", "5f0ea9fa1e83856e24637eaa736625ccd0a38b56f70c7a3cce9403d255e96512"),
        "owner": ("experiments/logs/root-prism-free/f0-shared-mod3-projection01-owner/supervisor.json", "02238aea185afce8364e92e5500024b8787898d7cfda04ce0ffe48bae171361b"), "rows_per_anchor": 19, "edge_rank": 7731},
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read(binding):
    path, expected = binding
    raw = (ROOT / path).read_bytes()
    assert sha(raw) == expected
    return json.loads(gzip.decompress(raw) if path.endswith(".gz") else raw)


def run(prime):
    started = time.monotonic()
    deadline = started + 90
    case = CASES[prime]
    assert sha((ROOT / case["source"][0]).read_bytes()) == case["source"][1]
    report, owner = read(case["report"]), read(case["owner"])
    assert report["source_sha256"] == owner["source_sha256"] == case["source"][1]
    assert owner["status"] == "CHILD_COMPLETE" and owner["returncode"] == 0
    assert owner["child_reaped"] and not owner["hard_timeout"]
    assert owner["report"]["sha256"] == case["report"][1]
    assert report["status"] == "COMPLETE_EXACT_MOD%d_SHARED_PROJECTION" % prime
    data = read(DOMAIN)
    core, triples = data["component_core_rows"], data["signature_domain"]
    assert len(core) == 21 and len(triples) == 480
    adjacent = [{j for j in range(21) if bits >> j & 1} for bits in core]
    sets = [set(h) for h in triples]
    assert all(len(h) == 3 for h in sets) and len(set(map(tuple, triples))) == 480
    targets = [[2 - int(i in h) - sum(j + 3 in adjacent[i + 3] for j in h) for i in range(18)] for h in triples]
    assert targets == data["row_targets"] and all(sum(q) == 24 for q in targets)
    edges = [(a, b) for a in range(480) for b in range(a + 1, 480)
             if len(sets[a] & sets[b]) <= 1 and all(targets[a][i] > 0 for i in triples[b])
             and all(targets[b][i] > 0 for i in triples[a])]
    assert len(edges) == 68394
    neighbors = [set() for _ in triples]
    for a, b in edges:
        neighbors[a].add(b)
        neighbors[b].add(a)
    assert [sorted(s) for s in neighbors] == data["possible_neighbor_signature_ids"]
    gram = []
    for i in range(18):
        for j in range(i, 18):
            quota = 12 * int(i == j) + 2 - len(adjacent[i + 3] & adjacent[j + 3]) - int(j + 3 in adjacent[i + 3])
            gram.append([(a, 1) for a, h in enumerate(sets) if i in h and j in h] + [(480, -quota)])
    gram.append([(a, 1) for a in range(480)] + [(480, -60)])
    assert len(gram) == 172

    def encode(items):
        planes = [0, 0]
        for j, value in items:
            value %= prime
            if value:
                planes[value - 1] |= 1 << j
        return planes[0] if prime == 2 else tuple(planes)

    def ternary_add(first, second):
        x, y = first
        u, v = second
        return (((x ^ u) & ~(y | v)) | (y & v),
                ((y ^ v) & ~(x | u)) | (x & u))

    if prime == 3:
        for a in range(3):
            for b in range(3):
                assert ternary_add(encode([(0, a)]), encode([(0, b)])) == encode([(0, a + b)])
    basis, operations = {}, 0

    def insert(value):
        nonlocal operations
        while (value != 0 if prime == 2 else value != (0, 0)):
            if operations % 4096 == 0:
                assert time.monotonic() < deadline
            union = value if prime == 2 else value[0] | value[1]
            pivot = union.bit_length() - 1
            if pivot not in basis:
                if prime == 3 and value[1] >> pivot & 1:
                    value = value[1], value[0]
                basis[pivot] = value
                return pivot
            old = basis[pivot]
            if prime == 2:
                value ^= old
            elif value[0] >> pivot & 1:
                value = ternary_add(value, (old[1], old[0]))
            else:
                value = ternary_add(value, old)
            operations += 1
        return None

    for row in reversed(gram):
        insert(encode(row))
    gram_rank = len(basis)
    assert gram_rank == 132
    width = case["rows_per_anchor"]
    edge_rows = [0] * (480 * width)
    for e, (a, b) in enumerate(edges):
        bit = 1 << (481 + e)
        if prime == 3:
            edge_rows[width * a] ^= bit
            edge_rows[width * b] ^= bit
        offset = int(prime == 3)
        for i in triples[b]:
            edge_rows[width * a + offset + i] ^= bit
        for i in triples[a]:
            edge_rows[width * b + offset + i] ^= bit
    new_selector_pivots = []
    for row_id in range(len(edge_rows) - 1, -1, -1):
        assert time.monotonic() < deadline
        a, i = divmod(row_id, width)
        q = 8 if prime == 3 and i == 0 else targets[a][i - int(prime == 3)]
        tail = encode([(a, -q)])
        value = edge_rows[row_id] | tail if prime == 2 else (edge_rows[row_id] | tail[0], tail[1])
        pivot = insert(value)
        if pivot is not None and pivot <= 480:
            new_selector_pivots.append(pivot)
    edge_rank = sum(pivot > 480 for pivot in basis)
    assert edge_rank == report["edge_pivots_found"] == case["edge_rank"]
    assert len(edge_rows) == report["processed_rows"]
    assert len(edge_rows) - edge_rank == report["dependencies_processed"]
    assert report["zero_selector_consequences"] + report["nonzero_selector_consequences"] == report["dependencies_processed"]
    assert not new_selector_pivots and report["new_independent_consequences"] == 0
    assert len(basis) == gram_rank + edge_rank
    assert time.monotonic() < deadline
    return {"status": "PASS_INDEPENDENT_COMPLETE_AUGMENTED_RANK_NO_NEW_SELECTOR_CONGRUENCES",
            "source_sha256": sha(Path(__file__).read_bytes()), "modulus": prime, "inputs": case,
            "domain": DOMAIN, "original_gram_rows": 172, "gram_rank": gram_rank,
            "edge_variables": len(edges), "original_rows_processed": len(edge_rows),
            "edge_rank": edge_rank, "augmented_rank": len(basis),
            "new_selector_pivots": new_selector_pivots,
            "method": "original Gram rows first; opposite highest pivots and reversed shared-row order on the combined edge-selector-constant matrix",
            "source_imports": 0, "optimizer_calls": 0, "native_imports": 0,
            "selected_incidence_fixed": False, "graph_symmetry_assumed": False,
            "whole_component_excluded": False, "field_row_operations": operations,
            "deadline_seconds": 90, "seconds": time.monotonic() - started}


if __name__ == "__main__":
    assert __debug__
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prime", type=int, choices=(2, 3), required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.prime)
    with args.output.open("x") as stream:
        json.dump(result, stream, sort_keys=True, indent=2)
        stream.write("\n")
    print(json.dumps(result, sort_keys=True))
