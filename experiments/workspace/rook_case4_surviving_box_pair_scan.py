"""Exact binary pair consequences of the 191 accepted surviving boxes.

P_i is the set of boxes in which coordinate i is not forced zero. O_i is the
set in which it is forced one. Disjoint P_i,P_j imply x_i+x_j<=1. Inclusion
P_i subset O_j implies x_i<=x_j. The old accepted cover supplies completeness;
this finite scan neither propagates nor rebuilds the retained row matrix.
"""
import argparse
import gzip
import hashlib
from itertools import combinations
import json
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[2]
BASE = "experiments/logs/grids-and-triangles/"
INPUTS = {
    "boxes": (BASE + "rook-case4-box-low-face-scan01/child/box-inputs.json.gz", "29fbaf96aa14a89089136a30951f4f597f068ae0481ab1b1f87c297395ec4aab"),
    "replay": (BASE + "rook-case4-box-low-face-scan01/independent-replay.json", "69fb21a3589bed904b859f1a8272aa26116ad7ab59931a4513ab16ffa60d91b0"),
    "owner": (BASE + "rook-case4-box-low-face-scan01/replay-supervisor.json", "b4698735b836178796a30c8594e5ee8145e280bcbe39b635b7d0fb750cac34fa"),
    "replay_source": ("experiments/workspace/rook_case4_box_low_face_units_replay.py", "20ad8ab6046d3db1efedb63c9e96eb2f25f3c9a915a45cb01349fda1cdcbc6e5"),
    "point": (BASE + "rook-case4-full-span-cycle-run01/exact-01/candidate.json", "819d0e909ecf7e357404eb063ba744bc8e4c0e38e0ee63848b1712b02b248b04"),
    "point_cold": (BASE + "rook-case4-full-span-cycle-run01/exact-01/cold.json", "cd59a3db0586c02a204fe8e3f23df4970b72416ff235319060a8fa1cb34e5bb8"),
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read(item):
    path, digest = item
    raw = (ROOT / path).read_bytes()
    assert sha(raw) == digest, path
    if path.endswith(".py"):
        return None
    return json.loads(gzip.decompress(raw) if path.endswith(".gz") else raw)


def calculate():
    started = time.monotonic()
    data = {key: read(item) for key, item in INPUTS.items()}
    spec, replay, owner = data["boxes"], data["replay"], data["owner"]
    assert replay["status"] == "PASS_INDEPENDENT_H27_LOW_FACE_CUT_AND_CAPACITY_EQUIVALENCE"
    assert replay["all260_cold_record_bindings_checked"]
    assert replay["inputs"]["boxes"] == list(INPUTS["boxes"])
    assert owner["status"] == "CHILD_COMPLETE" and owner["exit_code"] == 0
    assert owner["child_reaped"] and not owner["hard_timeout"]
    assert owner["source_sha256"] == INPUTS["replay_source"][1]
    assert owner["independent-replay.json"]["sha256"] == INPUTS["replay"][1]
    ids, boxes = spec["original_column_ids"], spec["boxes"]
    assert ids == sorted(set(range(1214)) - set(spec["proved_zero_columns"])) and len(ids) == 1102
    assert len(boxes) == len({b["index"] for b in boxes}) == 191
    possible, forced = [0] * len(ids), [0] * len(ids)
    box_indices = []
    for position, box in enumerate(boxes):
        state = box["state"]
        assert len(state) == len(ids) and set(state) <= set("01?")
        assert sha(bytes(255 if s == "?" else int(s) for s in state)) == box["state_sha256"]
        box_indices.append(box["index"])
        for i, value in enumerate(state):
            if value != "0":
                possible[i] |= 1 << position
            if value == "1":
                forced[i] |= 1 << position
    assert all(p for p in possible)
    assert all(o != (1 << 191) - 1 for o in forced)
    point, cold = data["point"], data["point_cold"]
    assert cold["exact_point_replayed"] and cold["candidate_sha256"] == INPUTS["point"][1]
    numerator = list(map(int, point["exact_check"]["original1214_selector_numerators"]))
    denominator = int(point["common_denominator"])
    assert denominator == 3461944222 and len(numerator) == 1214
    conflicts, implications = [], []
    for i, j in combinations(range(len(ids)), 2):
        if not (possible[i] & possible[j]):
            conflicts.append([ids[i], ids[j]])
    for i in range(len(ids)):
        for j in range(len(ids)):
            if i != j and not (possible[i] & ~forced[j]):
                implications.append([ids[i], ids[j]])
    violated_conflicts = [[a, b, str(numerator[a] + numerator[b] - denominator)]
                          for a, b in conflicts if numerator[a] + numerator[b] > denominator]
    violated_implications = [[a, b, str(numerator[a] - numerator[b])]
                             for a, b in implications if numerator[a] > numerator[b]]
    return {"schema": "conway99.rook-case4.surviving-box-pair-scan.v1",
            "status": "COMPLETE_EXACT_PAIR_AND_IMPLICATION_SCAN",
            "source_sha256": sha(Path(__file__).read_bytes()), "inputs": INPUTS,
            "box_order": box_indices, "original_column_ids": ids,
            "possible_box_masks_hex": list(map(hex, possible)),
            "forced_one_box_masks_hex": list(map(hex, forced)),
            "conflicts": conflicts, "implications": implications,
            "unordered_pairs_checked": len(ids) * (len(ids) - 1) // 2,
            "ordered_distinct_pairs_checked": len(ids) * (len(ids) - 1),
            "conflict_count": len(conflicts), "implication_count": len(implications),
            "latest_point_denominator": str(denominator),
            "violated_conflicts": violated_conflicts, "violated_implications": violated_implications,
            "novelty_against_all_existing_rows_claimed": False,
            "new_global_unit": False, "optimizer_calls": 0,
            "new_propagation_or_large_matrix_rebuild": False,
            "case4_excluded": False, "seconds": time.monotonic() - started}


if __name__ == "__main__":
    if not __debug__:
        raise RuntimeError("assertions required")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = calculate()
    raw = json.dumps(result, sort_keys=True, separators=(",", ":"), allow_nan=False).encode() + b"\n"
    with args.output.open("xb") as out:
        out.write(gzip.compress(raw, mtime=0) if args.output.suffix == ".gz" else raw)
    print(json.dumps({"path": str(args.output), "sha256": sha(args.output.read_bytes()),
                      "raw_sha256": sha(raw), "conflicts": result["conflict_count"],
                      "implications": result["implication_count"],
                      "violated_conflicts": len(result["violated_conflicts"]),
                      "violated_implications": len(result["violated_implications"]),
                      "seconds": result["seconds"]}, sort_keys=True))
