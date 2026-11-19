"""Exact global sign normalization for the F0 character count model.

This finite preparation checks table closure and the action on every signed
product and Gram row. It makes no optimizer call and changes no frozen model.
"""
import argparse
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "experiments/logs/root-prism-free"
INPUTS = {
    "characters": ("f0-character-populations01.json.gz", "139d06a3383f8fc79d677972ce052ce29966e8b3406e7d1e7d1077aea7c2cef6"),
    "character_cold": ("f0-character-populations01-cold.json", "1fdc14c0bda54f0b5e63b23a3b7d5f85d9afd92ea418b4931d53b644444e814b"),
    "gram": ("f0-character-Gram-equalities01.json", "084764b528f9a75269c8e21bb0b55b480a552022b024db72a4357aca083770c7"),
    "gram_cold": ("f0-character-Gram-equalities01-cold.json", "482ccc5f26d4668ef1f45fab6200eeb2328b92e0b949b7e026052c1354cd1f7f"),
    "joint": ("f0-two-orbit-profiles01.json.gz", "6a1bc6d196358ecc618355bc64d6fe6a2b60be9fa9411afd29526c9f493995b9"),
    "joint_cold": ("f0-two-orbit-profiles01-cold.json", "afedafe2f3009849350b1682a2c329064efd9b204ab7b5a6051e5d50449fcf41"),
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def build():
    started = time.monotonic()
    data = {}
    for name, (filename, expected) in INPUTS.items():
        raw = (BASE / filename).read_bytes()
        assert sha(raw) == expected
        data[name] = json.loads(gzip.decompress(raw) if filename.endswith(".gz") else raw)
        if name.endswith("cold"):
            assert data[name]["status"].startswith("PASS")
    chars, gram, joint = [data[x] for x in ("characters", "gram", "joint")]
    populations = chars["signed_populations"]
    lookup = {(p["character"], p["selector_orbit"]): p["signed_population"] for p in populations}
    group = chars["group"]
    phase_actions = {}
    for g in range(12):
        phase = tuple(c[g] for c in group["characters"][1:])
        assert phase[2] == phase[0] * phase[1]
        phase_actions.setdefault(phase, []).append(g)
    assert set(phase_actions) == {(a, b, a*b) for a in (-1, 1) for b in (-1, 1)}
    assert all(len(actions) == 3 for actions in phase_actions.values())
    phases = sorted(phase_actions)
    product_checks = 0
    for equation in chars["product_equations"]:
        a, b = equation["signed_population_factors"]
        ci = equation["character"]
        assert populations[a]["character"] == populations[b]["character"] == ci
        for phase in phases:
            assert phase[ci-1] ** 2 == 1
            product_checks += 1
    gram_checks = 0
    for row in gram["equations"]:
        assert row["rhs"] == 0
        assert all(populations[j]["character"] == row["character"] for j, _ in row["signed_population_terms"])
        gram_checks += len(phases)
    records = []
    for kind, tables in (("local", chars["local_tables"]), ("joint", joint["tables"])):
        for ti, table in enumerate(tables):
            assert time.monotonic() - started < 30
            count_width = len(table["count_columns"])
            signed_ids = table["signed_population_columns"]
            profiles = table["profiles"]
            keys = [tuple(p["counts_and_signed_populations"]) for p in profiles]
            index = {key: i for i, key in enumerate(keys)}
            assert len(index) == len(keys)
            mult = [p["literal_subset_count"] for p in profiles]
            permutations = []
            for phase in phases:
                permutation = []
                for key in keys:
                    transformed = key[:count_width] + tuple(
                        v * phase[populations[j]["character"]-1]
                        for j, v in zip(signed_ids, key[count_width:]))
                    assert transformed in index
                    permutation.append(index[transformed])
                assert sorted(permutation) == list(range(len(keys)))
                assert all(mult[i] == mult[j] for i, j in enumerate(permutation))
                permutations.append(permutation)
            records.append({"family": kind, "table_index": ti, "tuples": len(keys),
                            "four_phase_permutations_sha256": sha(canonical(permutations)),
                            "count_coordinates_fixed": True, "tuple_multiplicities_preserved": True})
    anchor = joint["tables"][0]
    assert anchor["selector_orbits"] == [0, 1]
    assert anchor["inherited_count_equality"]["terms"] == [[0, 1], [1, 1]]
    assert anchor["inherited_count_equality"]["rhs"] == 3
    anchor_ids = [[lookup[ci, oi] for oi in (0, 1)] for ci in (1, 2, 3)]
    positions = {j: len(anchor["count_columns"]) + k for k, j in enumerate(anchor["signed_population_columns"])}
    patterns, normalized_patterns = Counter(), Counter()
    normalized_indices = []
    phase_counts = Counter()
    for i, profile in enumerate(anchor["profiles"]):
        key = profile["counts_and_signed_populations"]
        sums = tuple(sum(key[positions[j]] for j in ids) for ids in anchor_ids)
        assert all(s % 2 == 1 and abs(s) <= 3 for s in sums)
        patterns[sums] += profile["literal_subset_count"]
        phase = (1 if sums[0] > 0 else -1, 1 if sums[1] > 0 else -1)
        phase = phase + (phase[0]*phase[1],)
        normalized = tuple(x*s for x, s in zip(sums, phase))
        assert normalized[0] >= 1 and normalized[1] >= 1
        assert sum(sums[0]*p[0] >= 1 and sums[1]*p[1] >= 1 for p in phases) == 1
        normalized_patterns[normalized] += profile["literal_subset_count"]
        phase_counts[phase] += 1
        if sums[0] >= 1 and sums[1] >= 1:
            normalized_indices.append(i)
    assert len(patterns) == 20 and sum(patterns.values()) == 512
    assert set(normalized_patterns) == {(1, 1, -1), (1, 1, 3), (1, 3, 1), (3, 1, 1), (3, 3, 3)}
    assert len(normalized_indices) == 44 and set(phase_counts.values()) == {44}
    assert sum(anchor["profiles"][i]["literal_subset_count"] for i in normalized_indices) == 128
    return {"schema": "conway99.f0-character-phase-normalization.v1",
            "status": "PASS: exact four-phase model symmetry and unique normalization",
            "source_sha256": sha(Path(__file__).read_bytes()),
            "inputs": {k: {"path": "experiments/logs/root-prism-free/"+f, "sha256": h} for k, (f, h) in INPUTS.items()},
            "phase_actions": [{"phase": list(p), "actual_action_indices": phase_actions[p]} for p in phases],
            "all_count_and_product_variables_fixed": True,
            "signed_population_phase": [p["character"] for p in populations],
            "signed_product_invariance_checks": product_checks,
            "homogeneous_Gram_row_phase_checks": gram_checks,
            "table_closure": records,
            "anchor_selector_orbits": [0, 1], "anchor_population": 3,
            "anchor_signed_local_ids_by_character": anchor_ids,
            "native_signed_offset": 15941,
            "normalization_rows": [{"terms": [[15941+j, 1] for j in ids], "lower": 1, "upper": 3}
                                   for ids in anchor_ids[:2]],
            "normalized_first_joint_table_profile_indices": normalized_indices,
            "first_joint_profiles_before": 176, "first_joint_profiles_after": 44,
            "first_joint_literal_subsets_before": 512, "first_joint_literal_subsets_after": 128,
            "possible_anchor_signed_sums": [list(p) for p in sorted(patterns)],
            "normalized_anchor_signed_sums": [list(p) for p in sorted(normalized_patterns)],
            "optimizer_calls": 0, "frozen_native_model_modified": False,
            "proof": "N0+N1=3 makes each character sum odd. A common phase (a,b,ab) uniquely makes the first two sums positive. The phase leaves every count and same-character product fixed, multiplies each homogeneous character-Gram row by one sign, and permutes every retained local and joint table. Thus every feasible count/signed assignment has exactly one normalized phase representative. This is a model symmetry, not a graph-automorphism assumption.",
            "scope": "Equivalent symmetry reduction for the documented character model and its two joint tables. The 117 count-only dense rows are invariant. No independent per-orbit sign choices are allowed. These two normalization rows are not unconditional constraints on every labelled signed assignment."}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "replay"))
    parser.add_argument("--record", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    started = time.monotonic()
    result = build()
    if args.mode == "replay":
        raw = args.record.read_bytes()
        assert json.loads(raw) == result
        result = {"status": "PASS: all phase actions, products, rows, tables and normalization replayed",
                  "source_sha256": sha(Path(__file__).read_bytes()), "record_sha256": sha(raw),
                  "optimizer_calls": 0, "seconds": time.monotonic()-started}
    raw = canonical(result)+b"\n"
    with args.output.open("xb") as handle:
        handle.write(raw)
    print(json.dumps({"status": result["status"], "sha256": sha(raw),
                      "seconds": time.monotonic()-started}, indent=2))
