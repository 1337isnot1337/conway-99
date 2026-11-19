"""Distinct proof kind for the cold whole-branch-cover capacity row.

The five old parity entries are copied byte-for-byte at the JSON-value level.
The sixth entry is a box-cover consequence and is never passed to a parity
verifier. This helper reads small accepted artifacts; it does not re-run
propagation, a row-pool rebuild, or the original trace checker.
"""
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[2]
LOG = "experiments/logs/grids-and-triangles/"
RUN = LOG + "rook-case4-box-low-face-scan01/"
PROOF_KIND = "cold_complete_branch_box_capacity"
SUPPORT = [23, 260, 399, 403, 406, 761, 762, 763, 764, 765, 803]
INPUTS = {
    "prior_terminal": (LOG + "rook-case4-full-span-cycle-run01/result.json", "408da79724822a1197fbda868fe73e5de70fd36b2b55a448716be2573944df32"),
    "point": (LOG + "rook-case4-full-span-cycle-run01/exact-01/candidate.json", "819d0e909ecf7e357404eb063ba744bc8e4c0e38e0ee63848b1712b02b248b04"),
    "point_cold": (LOG + "rook-case4-full-span-cycle-run01/exact-01/cold.json", "cd59a3db0586c02a204fe8e3f23df4970b72416ff235319060a8fa1cb34e5bb8"),
    "scan": (RUN + "child/result.json", "d5d69b0155c9f60c90164ab7e6e7bc01268bbc706c448e70796727236c3a7c9d"),
    "boxes": (RUN + "child/box-inputs.json.gz", "29fbaf96aa14a89089136a30951f4f597f068ae0481ab1b1f87c297395ec4aab"),
    "direct_replay": (RUN + "independent-replay.json", "69fb21a3589bed904b859f1a8272aa26116ad7ab59931a4513ab16ffa60d91b0"),
    "direct_owner": (RUN + "replay-supervisor.json", "b4698735b836178796a30c8594e5ee8145e280bcbe39b635b7d0fb750cac34fa"),
    "direct_source": ("experiments/workspace/rook_case4_box_low_face_units_replay.py", "20ad8ab6046d3db1efedb63c9e96eb2f25f3c9a915a45cb01349fda1cdcbc6e5"),
    "full_cold": (LOG + "rook-case4-three-gram-full-rows-run01-cold/child-result.json", "cda4f7a1b27b991827cd794c917a1a9ed9442e3b77bb6044f1d191f4f084399e"),
    "full_cold_owner": (LOG + "rook-case4-three-gram-full-rows-run01-cold/supervisor.json", "76f32ef2fb7c0d105eb49037ba3cc8522e78a47e4d39984c6107252b2c3723cd"),
}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def reference(key):
    path, digest = INPUTS[key]
    return {"path": path, "sha256": digest}


def read(key):
    name, digest = INPUTS[key]
    raw = (ROOT / name).read_bytes()
    assert sha(raw) == digest, key
    if name.endswith(".py"):
        return None
    return json.loads(gzip.decompress(raw) if name.endswith(".gz") else raw)


def bindings():
    return {"source_sha256": sha(Path(__file__).read_bytes()), "inputs": {k: list(v) for k, v in INPUTS.items()},
            "proof_kind": PROOF_KIND, "capacity_support": SUPPORT, "capacity_upper": 1}


def source_point():
    return {"candidate": reference("point"), "cold": reference("point_cold")}


def frozen_entry():
    row = {"terms": [[a, 1] for a in SUPPORT], "upper": 1}
    return {"proof_kind": PROOF_KIND,
            "certificate": {"status": "EXACT_COLD_BRANCH_BOX_CAPACITY", "inequality": row,
                            "direct_replay": reference("direct_replay"), "box_inputs": reference("boxes"),
                            "scope": "all integer case4 solutions on the proved112-zero face",
                            "source_point_excess_numerator": "37621464", "denominator": "3461944222"},
            "row_key": sha(canonical(row) + b"\n"), "source_point": source_point(),
            "proof_bindings": bindings()}


def frozen_registry():
    terminal = read("prior_terminal")
    assert terminal["registered_cut_count"] == terminal["latest_exact_point_accepted_cut_count"] == 5
    assert terminal["later_cuts_not_satisfied_by_latest_point"] == 0
    assert terminal["latest_exact_point"] == source_point()
    registry = terminal["registry"]
    assert len(registry) == 5 and all("proof_kind" not in e for e in registry)
    assert frozen_entry()["row_key"] not in {e["row_key"] for e in registry}
    return registry + [frozen_entry()]


def verify_entry(entry, gram, zeros, deadline):
    assert time.monotonic() < deadline and entry == frozen_entry()
    read("direct_source")
    report, owner, scan, spec = (read(k) for k in ("direct_replay", "direct_owner", "scan", "boxes"))
    full_owner = read("full_cold_owner")
    assert full_owner["child_result"]["sha256"] == INPUTS["full_cold"][1]
    for old_owner in (owner, full_owner):
        assert old_owner["status"] == "CHILD_COMPLETE" and old_owner["exit_code"] == 0
        assert old_owner["child_reaped"] and not old_owner["hard_timeout"]
    assert owner["source_sha256"] == INPUTS["direct_source"][1]
    assert owner["independent-replay.json"]["sha256"] == INPUTS["direct_replay"][1]
    assert report["status"] == "PASS_INDEPENDENT_H27_LOW_FACE_CUT_AND_CAPACITY_EQUIVALENCE"
    assert report["all260_cold_record_bindings_checked"]
    assert report["inputs"]["boxes"] == list(INPUTS["boxes"])
    assert report["inputs"]["result"] == list(INPUTS["scan"])
    cold = read("full_cold")
    assert cold["status"] == "PASS" and cold["all260_nonpartial_branches_checked"]
    assert cold["checked"] == 260 and cold["checked_contradictions"] == 69
    assert cold["checked_fixed_points"] == 191 and cold["checked_partial"] == 0
    assert cold["prior184_contradictions_and_complete_original_branch_cover_bound"]
    assert zeros == spec["proved_zero_columns"] == scan["identity"]["proved_zero_columns"]
    assert len(zeros) == 112 and zeros == sorted(set(zeros))
    kept = [a for a in range(1214) if a not in set(zeros)]
    assert kept == spec["original_column_ids"] and len(kept) == 1102
    positions = {a: j for j, a in enumerate(kept)}
    coefficient, rhs = [0] * 1214, 0
    for rid in (214, 344, 582):
        _, _, quota, members = gram[rid]
        assert type(quota) is int and members == sorted(set(members))
        rhs += quota
        for a in members:
            coefficient[a] += 1
    assert rhs == 3 and coefficient == scan["identity"]["full1214_coefficients"]
    assert min(coefficient) >= 0 and max(coefficient) == 3
    h = [a for a in kept if coefficient[a] % 2]
    q = [a for a in kept if coefficient[a] // 2]
    assert len(h) == 27 and len(q) == 10 and all(coefficient[a] // 2 == 1 for a in q)
    assert sorted(q + [23]) == SUPPORT
    seen, counts, maxima, low_indices = set(), Counter(), [], []
    assert len(spec["boxes"]) == 191
    direct_bounds = {b["index"]: b for b in report["all191_box_bounds"]}
    assert len(direct_bounds) == 191
    for box in spec["boxes"]:
        index, state = box["index"], box["state"]
        assert index not in seen and 0 <= index < 260
        seen.add(index)
        assert len(state) == 1102 and set(state) <= set("01?")
        assert sha(bytes(255 if c == "?" else int(c) for c in state)) == box["state_sha256"]
        assert all(state[positions[a]] in "01" for a in sorted(set(h) | set(q)))
        hv = sum(int(state[positions[a]]) for a in h)
        qv = sum(int(state[positions[a]]) for a in q)
        assert hv + 2 * qv == 3 and hv in (1, 3)
        if hv == 1:
            assert state[positions[23]] == "0"
            low_indices.append(index)
        counts[hv] += 1
        maximum = sum(state[positions[a]] != "0" for a in SUPPORT)
        assert maximum <= 1 and maximum == direct_bounds[index]["capacity_maximum"]
        maxima.append(maximum)
    assert counts == {1: 54, 3: 137} and low_indices == scan["low_box_indices"]
    assert report["equivalent_capacity"] == {"terms": [[a, 1] for a in SUPPORT], "lower": 0, "upper": 1}
    point, pc = read("point"), read("point_cold")
    assert pc["status"].startswith("PASS:") and pc["exact_point_replayed"]
    assert pc["candidate_sha256"] == INPUTS["point"][1]
    den = int(point["common_denominator"])
    nums = list(map(int, point["exact_check"]["original1214_selector_numerators"]))
    assert len(nums) == 1214 and den == 3461944222
    assert sum(nums[a] for a in SUPPORT) - den == 37621464
    assert time.monotonic() < deadline
    return entry["certificate"]
