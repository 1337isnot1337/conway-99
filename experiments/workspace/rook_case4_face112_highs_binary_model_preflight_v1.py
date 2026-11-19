"""Exact compact binary model for the proved 112-zero case4 face.

The original native rows are reconstructed from their frozen inventory.
The complete coordinate-cover registry remains external. All arithmetic
used to accept a proposed Boolean point is performed with Python integers.
This module does not call an optimizer.
"""
import argparse
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import struct
import time

ROOT = Path(__file__).resolve().parents[2]
BASE = "experiments/logs/grids-and-triangles/"
INPUTS = {
    "native": (BASE+"complement-rook-35core-case0004-native-cpsat-model.json",
        "a9004e97a2d166bf8b162609cfb538eae0dd4d26942b6df5119b6a88d65ec476"),
    "common_rows": (BASE+"rook-case4-face112-branch-batch-preparation01/rows.json",
        "361f04e0176d0ac53bed09ff9c7cdf33d76608b99c3a2426f0cf35345da46a55"),
    "base_model": (BASE+"rook-case4-face112-model01/model.json",
        "018882c8cea2a8cb9c2fc73a433d40973d20588bc5accb0fb8b0165fddc4337f"),
    "base_cold": (BASE+"rook-case4-face112-model01-cold-replay.json",
        "26f063161cbf9c0beb139b392f0b46007254176c522308d3ed2d5e3ee3c2e703"),
    "base_arrays": (BASE+"rook-case4-face112-model01/arrays.npz",
        "276db9d80b2772ab6829daf7459b19043a08996dc2b45ff8769534548b8b8ca3"),
    "registry": (BASE+"complement-rook-35core-case0004-lazy-native-registry.bin.gz",
        "c32e31d9ce6ec6168cea1c9f6c6ea4165a2ca7a8f2144a59a31e5a1d6da7b543"),
    "guard_source": ("experiments/workspace/rook_case4_face112_disjoint_guard_cuts.py",
        "171955320ea6b20fadaa8b2bb6a14d82dbd4476c3bc45c902392d824dac17eaa"),
    "guards": (BASE+"rook-case4-face112-disjoint-guard-cuts01.json",
        "9ef2b90b12a08911970952fca73da4d788f99997e71349433d54429c02c49efc"),
    "guards_cold": (BASE+"rook-case4-face112-disjoint-guard-cuts01-replay.json",
        "1300434903fa41f05f993eb1bc9943947e65a061920033f22767c783dfe6429c"),
    "guards_peer": (BASE+"rook-case4-face112-disjoint-guard-cuts-independent-sets-source-review.json",
        "507b613e02320cbe83a7a3f54a1e0535559bda658d975bd24667390f2261ce43"),
    "h3_source": ("experiments/workspace/rook_case4_face112_third_parity_cover.py",
        "9da8c7edc60429b6a7bee6cd15da447e08a6ae1656a4be5b77b1dd2f5ba5bdb3"),
    "h3": (BASE+"rook-case4-face112-third-parity-cover-certificate.json",
        "4ab891e2d809847804b4b3d3626f9c4e498d32788d90ddb865da2ed4c98b6ef7"),
    "h3_cold": (BASE+"rook-case4-face112-third-parity-cover-replay.json",
        "a3b57893b112ed96a5e3dc812dfd9dd5ed0776284dbe59165335167214983a76"),
    "sum_two": (BASE+"rook-case4-face111-native-bounds-independent-replay.json",
        "5e1e01b8c5f3c5747292d65e6938263afe7a72bfff68b00ee29cf2f41b23b2a3"),
}
N, LIVE, ORIGINAL_COVERS, RETAINED_COVERS = 1214, 1102, 178533, 164044
RAW_SHA = "3b819e29bc9aacdb5217b151f32b35cb186aa3b8a93a37784edc912ddac36736"
ROW_CANONICAL_SHA = "6b8005f1e9d848e2843056f285f2d16a1dce8c4bea207f95af3fd6472778eb59"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def save_new(path, value):
    assert not path.exists(), path
    path.write_bytes(json.dumps(value, indent=2, allow_nan=False).encode()+b"\n")


def checked_time(deadline):
    if deadline is not None and time.monotonic() >= deadline:
        raise TimeoutError("owned search or replay deadline")


def cover(raw, identifier):
    at = 154*identifier
    assert 0 <= identifier < ORIGINAL_COVERS
    return struct.unpack_from("<H", raw, at)[0], int.from_bytes(raw[at+2:at+154], "little")


def members(bits):
    while bits:
        bit = bits & -bits
        yield bit.bit_length()-1
        bits ^= bit


def integer_row(terms, lower, upper, family, source):
    coefficients = Counter()
    for a, c in terms:
        assert type(a) is type(c) is int and 0 <= a < N
        coefficients[a] += c
    assert type(lower) is type(upper) is int and lower <= upper
    return {"terms": [[a, c] for a, c in sorted(coefficients.items()) if c],
            "lower": lower, "upper": upper, "family": family, "source": source}


def original_rows(inventory):
    result = [integer_row([[a, 1] for a in support], q, q, "Gram", [i, j])
              for i, j, q, support in inventory["Gram_rows"]]
    result += [integer_row([[a, 1] for a in support], 0, 1, "original_signature", i)
               for i, support in inventory["original_signature_rows"]]
    result += [integer_row([[a, 1] for a in r["members"]], 0, 1, "core_triple", r["triple"])
               for r in inventory["triple_rows"]]
    for i, clause in enumerate(inventory["Gram_conflict_clauses"]):
        assert len(clause) == 2 and all(a < 0 for a in clause)
        result.append(integer_row([[-a-1, 1] for a in clause], 0, 1, "Gram_conflict", i))
    for i, cut in enumerate(inventory["uncapped_integer_cuts"]):
        terms, demand = cut["positive_terms"], cut["positive_demand"]
        assert demand > 0 and all(type(w) is int and w > 0 for a, w in terms)
        result.append(integer_row(terms+[[cut["target_column"], -demand]], 0,
                                  sum(w for a, w in terms), "uncapped_row_cut", i))
    assert len(result) == 2271
    assert Counter(r["family"] for r in result) == {
        "Gram": 630, "original_signature": 186, "core_triple": 1365,
        "Gram_conflict": 30, "uncapped_row_cut": 60}
    return result


def load_inputs(root, deadline=None):
    data = {}
    for key, (name, expected) in INPUTS.items():
        checked_time(deadline)
        raw = (root/name).read_bytes()
        assert sha(raw) == expected, key
        if name.endswith(".json"):
            data[key] = json.loads(raw)
        elif key == "registry":
            data[key] = gzip.decompress(raw)
    registry = data["registry"]
    assert len(registry) == 154*ORIGINAL_COVERS and sha(registry) == RAW_SHA
    base = data["base_model"]
    assert data["base_cold"]["status"].startswith("PASS")
    assert data["base_cold"]["model_sha256"] == INPUTS["base_model"][1]
    assert (base["columns"], base["rows"], base["nonzeros"]) == (1102, 166010, 10767167)
    common = data["common_rows"]["rows"]
    assert len(common) == 2390 and sha(canonical(common)) == ROW_CANONICAL_SHA
    assert data["common_rows"]["canonical_rows_sha256"] == ROW_CANONICAL_SHA
    inventory = data["native"]["primary_inventory"]
    assert sha(canonical(inventory)) == data["native"]["primary_inventory_sha256"]
    native = original_rows(inventory)
    assert native == common[:2271]
    assert [r["family"] for r in common[2271:2277]] == ["integer_parity_cover"]*2+["certified_native_bound_pair"]*4
    assert [[r["lower"], r["upper"]] for r in common[2271:2277]] == [[1, 1]]*2+[[0, 1]]*4
    assert [[a for a, c in r["terms"]] for r in common[2273:2277]] == [[259,590],[259,591],[259,593],[259,732]]
    zeros = base["fixed_zero_columns"]
    assert zeros == sorted(set(zeros)) and len(zeros) == 112 and 663 in zeros
    assert common[2277:2389] == [
        integer_row([[a, 1]], 0, 0, "proved_integer_zero", a) for a in zeros]
    sum_row = common[-1]
    assert len(sum_row["terms"]) == 86 and all(c == 1 for a, c in sum_row["terms"])
    assert sum_row["lower"] == sum_row["upper"] == 2
    assert [a for a, c in sum_row["terms"]] == data["sum_two"]["short_identity"]["S"]
    assert sum_row["source"] == INPUTS["sum_two"][1]
    guards = data["guards"]["certificate"]
    assert guards["all64_retained_branches_cold_checked"]
    assert guards["source_sha256"] == INPUTS["guard_source"][1]
    assert data["guards_cold"]["certificate_sha256"] == INPUTS["guards"][1]
    assert data["guards_cold"]["status"].startswith("PASS")
    cuts = guards["retained_cuts"]
    assert len(cuts) == guards["retained_cut_count"] == 227
    assert [r["cut_id"] for r in cuts] == list(range(227))
    assert sum(len(r["terms"]) for r in cuts) == 1681
    h3 = data["h3"]["sparse_equivalent"]
    assert h3 == {"target": 803, "positive_support": [401,402,405,590,591,592,593,594,595],
                  "terms": [[a, -1] for a in [401,402,405,590,591,592,593,594,595]]+[[803, 1]],
                  "upper": 0}
    assert data["h3_cold"]["certificate_sha256"] == INPUTS["h3"][1]
    assert data["h3_cold"]["status"].startswith("PASS") and data["h3_cold"]["full1214_original_expansion"]
    assert data["h3"]["zero663_required"] is False
    added = [integer_row(c["terms"], sum(min(0, w) for a, w in c["terms"]),
                         c["upper"], "proved_disjoint_guard_cut", c["cut_id"]) for c in cuts]
    added.append(integer_row(h3["terms"], -9, 0, "proved_H3_sparse_cut", INPUTS["h3"][1]))
    data["acceptance_rows"] = common+added
    data["initial_original_rows"] = common[:2277]+added[:227]+[sum_row, added[-1]]
    assert len(data["acceptance_rows"]) == 2618 and len(data["initial_original_rows"]) == 2506
    data["kept"] = [a for a in range(N) if a not in set(zeros)]
    assert len(data["kept"]) == LIVE
    return data


def definition(data, deadline=None):
    kept = data["kept"]
    position = {a: i for i, a in enumerate(kept)}
    active_bits = sum(1 << a for a in kept)
    rows, omitted = [], []
    for i, row in enumerate(data["initial_original_rows"]):
        checked_time(deadline)
        terms = [[position[a], c] for a, c in row["terms"] if a in position]
        lower_box = sum(min(0, c) for a, c in terms)
        upper_box = sum(max(0, c) for a, c in terms)
        tautology = lower_box >= row["lower"] and upper_box <= row["upper"]
        if i < 2271 and tautology:
            omitted.append({"original_native_row": i, "box_minimum": lower_box, "box_maximum": upper_box,
                            "original_lower": row["lower"], "original_upper": row["upper"]})
            continue
        assert terms and not tautology
        rows.append({"terms": terms, "lower": row["lower"], "upper": row["upper"],
                     "family": row["family"], "source": row["source"],
                     "original_row_index": i})
    assert len(omitted) == 311
    assert omitted == data["base_model"]["omitted_native_rows_exact_box_witnesses"] or [
        {k: v for k, v in r.items() if k != "family"} for r in data["base_model"]["omitted_native_rows_exact_box_witnesses"]] == omitted
    assert len(rows) == 2195 and sum(len(r["terms"]) for r in rows) == 27515
    assert len(rows[:1966]) == 1966
    pool, removed = [], []
    for i in range(ORIGINAL_COVERS):
        if i % 128 == 0:
            checked_time(deadline)
        target, support = cover(data["registry"], i)
        assert target < N and support < 1 << N and not (support >> target & 1)
        if target not in position:
            removed.append([i, target])
        else:
            assert support & active_bits
            pool.append(i)
    assert len(pool) == RETAINED_COVERS and len(removed) == 14489
    assert removed == data["base_model"]["omitted_covers_fixed_zero_target_witnesses"]
    return {
        "schema": "conway99.rook-face112-highs-binary-model.v1",
        "source_sha256": sha(Path(__file__).read_bytes()),
        "inputs": {k: {"path": p, "sha256": h} for k, (p, h) in INPUTS.items()},
        "original_variables": N, "binary_variables": LIVE,
        "original_column_ids": kept, "fixed_zero_columns": data["base_model"]["fixed_zero_columns"],
        "initial_rows": rows, "initial_row_count": len(rows), "initial_nonzeros": 27515,
        "retained_original_native_rows": 1960, "parity_equalities": 2, "certified_pair_rows": 4,
        "grouped_cuts": 227, "sum86_equals_two_rows": 1, "H3_sparse_rows": 1,
        "row_family_counts": dict(Counter(r["family"] for r in rows)),
        "omitted_original_native_rows": omitted,
        "original_cover_count": ORIGINAL_COVERS, "external_cover_pool": pool,
        "external_cover_pool_count": len(pool), "omitted_cover_zero_targets": removed,
        "complete_original_cover_registry_raw_sha256": RAW_SHA,
        "exact_acceptance_row_count_in_original_coordinates": 2618,
        "all_original_native_and_cover_rows_checked_on_acceptance": True,
        "variable_bounds": [0, 1], "all_variables_integer": True, "objective": "zero feasibility",
        "maximum_absolute_coefficient": max(abs(c) for r in rows for a, c in r["terms"]),
        "symmetry_equalities_added": 0, "fixed_branch_assumptions_added": [],
        "incidence_witness_is_not_graph_completion": True, "case4_excluded": False,
        "optimizer_calls": 0,
    }


def compare_base_arrays(data, model, root):
    import numpy as np
    with np.load(root/INPUTS["base_arrays"][0], allow_pickle=False) as archive:
        arrays = {name: archive[name] for name in archive.files}
    assert {name: sha(a.tobytes(order="C")) for name, a in arrays.items()} == data["base_model"]["array_sha256"]
    assert list(map(int, arrays["original_column_ids"])) == model["original_column_ids"]
    ids = list(range(1960))+list(range(166004,166010))
    for old_id, row in zip(ids, model["initial_rows"][:1966]):
        lo, hi = map(int, arrays["row_pointers"][old_id:old_id+2])
        assert [[int(a), int(c)] for a, c in zip(arrays["column_indices"][lo:hi], arrays["coefficients"][lo:hi])] == row["terms"]
        assert [int(arrays["row_lower"][old_id]), int(arrays["row_upper"][old_id])] == [row["lower"], row["upper"]]
    assert list(map(int, arrays["row_origin_index"][1960:166004])) == model["external_cover_pool"]
    assert all(int(k) == 1 for k in arrays["row_origin_kind"][1960:166004])
    return {"all1966_base_native_rows_compared": True,
            "all164044_external_pool_origin_ids_compared": True,
            "base_array_hashes_checked": True, "no_base_model_rebuilt": True}


def cover_row(raw, identifier, position):
    target, support = cover(raw, identifier)
    assert target in position
    members_live = [a for a in members(support) if a in position]
    assert members_live and target not in members_live
    return {"terms": sorted([[position[target], -1]]+[[position[a], 1] for a in members_live]),
            "lower": 0, "upper": len(members_live),
            "family": "original_coordinate_cover", "source": identifier}


def inspect_binary(point, data, deadline=None, literal_cover_check=False):
    assert len(point) == N and all(type(x) is int and x in (0, 1) for x in point)
    row_violations = []
    for i, row in enumerate(data["acceptance_rows"]):
        checked_time(deadline)
        value = sum(c*point[a] for a, c in row["terms"])
        if not row["lower"] <= value <= row["upper"]:
            row_violations.append({"row_index": i, "family": row["family"], "source": row["source"],
                                   "value": value, "lower": row["lower"], "upper": row["upper"]})
    selected = sum(1 << a for a, value in enumerate(point) if value)
    violations = []
    for i in range(ORIGINAL_COVERS):
        if i % 128 == 0:
            checked_time(deadline)
        target, support = cover(data["registry"], i)
        if point[target]:
            satisfied = (any(point[a] for a in members(support)) if literal_cover_check else bool(selected & support))
            if not satisfied:
                violations.append(i)
    return {"binary_coordinates_checked": N, "selected_columns": list(members(selected)),
            "original_integer_rows_checked": len(data["acceptance_rows"]),
            "original_coordinate_covers_checked": ORIGINAL_COVERS,
            "row_violations": row_violations, "cover_violations": violations,
            "accepted_exact_incidence": not row_violations and not violations,
            "full_graph_completion_claimed": False}


def load_model(path, root, deadline=None):
    model = json.loads(path.read_bytes())
    assert model["source_sha256"] == sha(Path(__file__).read_bytes())
    data = load_inputs(root, deadline)
    assert model == definition(data, deadline)
    return model, data


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "replay"))
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    started = time.monotonic()
    data = load_inputs(args.root)
    model = definition(data)
    if args.mode == "prepare":
        compare = compare_base_arrays(data, model, args.root)
        save_new(args.model, model)
    else:
        assert json.loads(args.model.read_bytes()) == model
        compare = {"compact_rows_rebuilt_from_original_inventory": True,
                   "base_dense_array_reloaded": False, "optimizer_calls": 0}
    record = {"status": "PASS: compact binary model "+args.mode,
        "source_sha256": sha(Path(__file__).read_bytes()),
        "model_sha256": sha(args.model.read_bytes()), "binary_variables": LIVE,
        "initial_rows": 2195, "initial_nonzeros": 27515,
        "external_cover_pool": RETAINED_COVERS, "exact_original_cover_checks": ORIGINAL_COVERS,
        "comparison": compare, "optimizer_calls": 0, "seconds": time.monotonic()-started}
    save_new(args.output, record)
    print(json.dumps(record, indent=2))
