"""Find exact capacity cuts from pair conflicts in the 191 surviving boxes.

Any clique of disjoint possible-box masks has capacity at most one. The
bounded Bron-Kerbosch enumeration proposes maximal cliques. Every returned
clique is separately checked against every box before it is reported as a
necessary inequality. No propagation, numerical LP or native solver runs.
"""
import argparse
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[2]
PAIR = ("experiments/logs/grids-and-triangles/rook-case4-surviving-box-pair-scan01.json.gz",
        "19d96dd0af3ebaaab33c88456872883f5a51afea53ce3c9d0d57d6e6e0ccdadc")
MAX_SECONDS, MAX_NODES = 30, 2000000


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def bound(item):
    path, digest = item
    raw = (ROOT / path).read_bytes()
    assert sha(raw) == digest
    return json.loads(gzip.decompress(raw) if path.endswith(".gz") else raw)


def bits(mask):
    while mask:
        bit = mask & -mask
        yield bit.bit_length() - 1
        mask ^= bit


def calculate():
    started = time.monotonic()
    pair = bound(PAIR)
    assert pair["status"] == "COMPLETE_EXACT_PAIR_AND_IMPLICATION_SCAN"
    boxes = bound(pair["inputs"]["boxes"])
    point = bound(pair["inputs"]["point"])
    ids = boxes["original_column_ids"]
    assert ids == pair["original_column_ids"] and len(ids) == 1102
    assert len(boxes["boxes"]) == 191
    possible = [0] * len(ids)
    for k, box in enumerate(boxes["boxes"]):
        state = box["state"]
        assert len(state) == 1102 and set(state) <= set("01?")
        assert sha(bytes(255 if value == "?" else int(value) for value in state)) == box["state_sha256"]
        for j, value in enumerate(state):
            if value != "0":
                possible[j] |= 1 << k
    assert list(map(hex, possible)) == pair["possible_box_masks_hex"]
    assert all(possible)
    adjacency = [0] * len(ids)
    conflicts = []
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            if not (possible[i] & possible[j]):
                adjacency[i] |= 1 << j
                adjacency[j] |= 1 << i
                conflicts.append([ids[i], ids[j]])
    assert conflicts == pair["conflicts"] and len(conflicts) == 2855
    active = sum(1 << j for j, mask in enumerate(adjacency) if mask)
    cliques, nodes, complete = [], 0, True

    def visit(chosen, pending, excluded):
        nonlocal nodes
        nodes += 1
        if nodes > MAX_NODES or time.monotonic() - started > MAX_SECONDS:
            raise TimeoutError("declared exact clique-enumeration bound")
        if not (pending | excluded):
            cliques.append(chosen)
            return
        pivot = max(bits(pending | excluded), key=lambda j: (pending & adjacency[j]).bit_count())
        branch = pending & ~adjacency[pivot]
        for j in bits(branch):
            visit(chosen | (1 << j), pending & adjacency[j], excluded & adjacency[j])
            pending &= ~(1 << j)
            excluded |= 1 << j

    try:
        visit(0, active, 0)
    except TimeoutError:
        complete = False
    cliques = sorted(tuple(bits(c)) for c in cliques)
    assert len(cliques) == len(set(cliques))
    numerator = list(map(int, point["exact_check"]["original1214_selector_numerators"]))
    denominator = int(point["common_denominator"])
    assert denominator == 3461944222 and len(numerator) == 1214
    records, violations = [], []
    for clique in cliques:
        assert len(clique) >= 2
        used = 0
        for j in clique:
            assert not (used & possible[j])
            used |= possible[j]
        maxima = [sum(box["state"][j] != "0" for j in clique) for box in boxes["boxes"]]
        assert max(maxima) <= 1
        extension = active
        for j in clique:
            extension &= adjacency[j]
        assert extension == 0
        support = [ids[j] for j in clique]
        excess = sum(numerator[a] for a in support) - denominator
        record = {"support": support, "upper": 1, "all191_box_maxima": maxima,
                  "current_point_excess_numerator": str(excess)}
        records.append(record)
        if excess > 0:
            violations.append(record)
    return {"schema": "conway99.rook-case4.surviving-box-cliques.v1",
            "status": "COMPLETE_MAXIMAL_CLIQUE_ENUMERATION" if complete else "PARTIAL_BOUNDED_CLIQUE_ENUMERATION",
            "source_sha256": sha(Path(__file__).read_bytes()), "pair_certificate": PAIR,
            "box_input": pair["inputs"]["boxes"], "point_input": pair["inputs"]["point"],
            "maximum_seconds": MAX_SECONDS, "maximum_search_nodes": MAX_NODES,
            "visited_search_nodes": nodes, "active_conflict_vertices": active.bit_count(),
            "conflict_edges": len(conflicts), "maximal_cliques": records,
            "size_histogram": dict(sorted(Counter(len(c) for c in cliques).items())),
            "violated_cliques": violations, "point_denominator": str(denominator),
            "novelty_against_existing_rows_claimed": False, "optimizer_calls": 0,
            "case4_excluded": False, "seconds": time.monotonic() - started}


if __name__ == "__main__":
    if not __debug__:
        raise RuntimeError("assertions required")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = calculate()
    raw = json.dumps(result, sort_keys=True, separators=(",", ":"), allow_nan=False).encode() + b"\n"
    with args.output.open("xb") as stream:
        stream.write(gzip.compress(raw, mtime=0) if args.output.suffix == ".gz" else raw)
    print(json.dumps({"path": str(args.output), "sha256": sha(args.output.read_bytes()),
                      "raw_sha256": sha(raw), "status": result["status"],
                      "maximal_cliques": len(result["maximal_cliques"]),
                      "size_histogram": result["size_histogram"],
                      "violated_cliques": [{"support": v["support"], "excess_numerator": v["current_point_excess_numerator"]}
                                            for v in result["violated_cliques"]],
                      "seconds": result["seconds"]}, sort_keys=True))
