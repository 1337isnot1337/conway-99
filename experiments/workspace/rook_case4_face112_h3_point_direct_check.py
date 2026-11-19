"""Independent bounded arithmetic check of the saved H3 rational point.

Reuse the completed full-model cold binding; do not rebuild a model, import
the model/basis sources, call an optimizer, or repeat exact elimination.
All CSR arithmetic uses signed int64 only after a Python-integer absolute
sum bound proves that every product and partial sum fits. Original native
constraints are separately evaluated with Python integers. Original covers
are decoded directly from the immutable little-endian registry.
"""
import argparse
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import signal
import time

ROOT = Path(__file__).resolve().parents[2]
BASE = "experiments/logs/grids-and-triangles/"
FILES = {
    "model": (BASE+"rook-case4-face112-h3-model02/model.json", "1928eb76274865e219747f631fee2d7a327ed7acd3a845986844be13c9e34265"),
    "arrays": (BASE+"rook-case4-face112-h3-model02/arrays.npz", "4e2de2786d3036cf995953791192500cb4aaa5b0c5079f3d97ea465a4cf64e46"),
    "model_cold": (BASE+"rook-case4-face112-h3-model02-cold-replay.json", "56864810924bacb6b331db728a4ce32810d8e6f2dfe7c196e0a73e0b2f583a97"),
    "numerical_cold": (BASE+"rook-case4-face112-h3-generation-run01-replay.json", "e682e859b538e97a40786c445fa628cc26dd3a962172d0308b29d0cab48a2de5"),
    "candidate": (BASE+"rook-case4-face112-h3-basis-run01/candidate.json", "cecacaaa1cb6974dd898f1d2b69be32a06e44e9b89a1b45e35717bc347d3b4e8"),
    "native": (BASE+"complement-rook-35core-case0004-native-cpsat-model.json", "a9004e97a2d166bf8b162609cfb538eae0dd4d26942b6df5119b6a88d65ec476"),
    "covers": (BASE+"complement-rook-35core-case0004-lazy-native-registry.bin.gz", "c32e31d9ce6ec6168cea1c9f6c6ea4165a2ca7a8f2144a59a31e5a1d6da7b543"),
    "failed_cold_log": (BASE+"rook-case4-face112-h3-basis-run01-replay.log", "a00941c98b51f697db63b2349ebfc2689b5119a866c5cbc691c75be9347dd433"),
}
PRIMARY_SHA = "5a6af30f47826df629a3795ceea0a0a91b853cf8149860355ce1bd17ac0094b2"
RAW_COVERS_SHA = "3b819e29bc9aacdb5217b151f32b35cb186aa3b8a93a37784edc912ddac36736"
SECONDS, ROW_BATCH, COVER_BATCH = 60, 2048, 512
I64 = (1 << 63)-1


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def save(path, value):
    assert not path.exists()
    temporary = path.with_name(path.name+".partial")
    temporary.write_text(json.dumps(value, indent=2)+"\n")
    temporary.replace(path)


def tick(deadline):
    if time.monotonic() >= deadline:
        raise TimeoutError("independent60second point arithmetic bound")


def bound_inputs(root):
    values = {}
    for key, (name, expected) in FILES.items():
        raw = (root/name).read_bytes()
        assert sha(raw) == expected, ("input hash", key)
        values[key] = raw
    model = json.loads(values["model"])
    cold = json.loads(values["model_cold"])
    numeric = json.loads(values["numerical_cold"])
    assert cold["status"].startswith("PASS:") and numeric["status"].startswith("PASS:")
    assert cold["model_sha256"] == FILES["model"][1]
    assert cold["arrays"]["sha256"] == model["arrays"]["sha256"] == FILES["arrays"][1]
    assert cold["all_parent_array_prefixes_equal"]
    assert cold["all_omission_witnesses_replayed"] and cold["all_row_column_transports_checked"]
    assert (model["columns"], model["rows"], model["nonzeros"]) == (1102, 166011, 10767194)
    assert (numeric["original_rows_rebuilt"], numeric["extended_rows_rebuilt"]) == (166011, 167113)
    assert numeric["retained_cover_pool_checked"] == 164044 and numeric["native_calls_recorded"] == 1
    assert not numeric["optimizer_called_by_replay"]
    assert b'TimeoutError' in values["failed_cold_log"]
    return values, model


def int64_row_values(np, arrays, nums, denominator, deadline):
    """Every intermediate is bounded by a checked absolute row-sum majorant."""
    p, c, v = (arrays[k] for k in ("row_pointers", "column_indices", "coefficients"))
    lower, upper = arrays["row_lower"], arrays["row_upper"]
    assert all(a.dtype.kind == "i" for a in (p, c, v, lower, upper))
    assert len(p) == len(lower)+1 == len(upper)+1 and int(p[0]) == 0
    assert int(p[-1]) == len(c) == len(v)
    widths = np.diff(p)
    assert np.all(widths > 0) and np.all(lower <= upper)
    assert int(np.min(c)) >= 0 and int(np.max(c)) < len(nums)
    assert all(type(n) is int and 0 <= n <= denominator <= I64 for n in nums)
    # Avoid abs(INT64_MIN), and calculate all safety products as Python ints.
    assert int(np.min(v)) > -(1 << 62) and int(np.max(v)) < (1 << 62)
    max_coefficient = max(abs(int(np.min(v))), abs(int(np.max(v))))
    max_terms, max_num = int(np.max(widths)), max(nums)
    absolute_sum_bound = max_coefficient*max_terms*max_num
    endpoint_bound = max(abs(int(np.min(lower))), abs(int(np.max(lower))),
                         abs(int(np.min(upper))), abs(int(np.max(upper))))*denominator
    assert absolute_sum_bound <= I64 and endpoint_bound <= I64
    n = np.asarray(nums, dtype="<i8")
    result, digest = [], hashlib.sha256()
    for first in range(0, len(lower), ROW_BATCH):
        tick(deadline)
        last = min(first+ROW_BATCH, len(lower))
        begin, end = int(p[first]), int(p[last])
        products = v[begin:end]*n[c[begin:end]]
        sums = np.add.reduceat(products, p[first:last]-begin)
        assert np.all(lower[first:last]*denominator <= sums), ("CSR lower", first)
        assert np.all(sums <= upper[first:last]*denominator), ("CSR upper", first)
        digest.update(sums.astype("<i8", copy=False).tobytes())
        result.extend(map(int, sums))
    return result, {"rows": len(lower), "terms": len(v),
        "maximum_coefficient_absolute": max_coefficient,
        "maximum_row_terms": max_terms,
        "proved_absolute_product_and_partial_sum_bound": str(absolute_sum_bound),
        "proved_scaled_endpoint_absolute_bound": str(endpoint_bound),
        "signed_int64_maximum": str(I64), "row_activity_sha256": digest.hexdigest()}


def controls(np, deadline):
    cases = 0
    for offset in range(32):
        nums = [(offset+3*j) % 17 for j in range(9)]
        terms = [[(j, ((j+2*i+offset) % 11)-5) for j in range(9) if (j+i) % 4]
                 for i in range(7)]
        reference = [sum(nums[j]*c for j, c in row) for row in terms]
        ptr = [0]
        for row in terms:
            ptr.append(ptr[-1]+len(row))
        arrays = {"row_pointers": np.asarray(ptr, dtype="<i8"),
            "column_indices": np.asarray([j for row in terms for j, c in row], dtype="<i4"),
            "coefficients": np.asarray([c for row in terms for j, c in row], dtype="<i8"),
            "row_lower": np.asarray([-100]*7, dtype="<i8"),
            "row_upper": np.asarray([100]*7, dtype="<i8")}
        got, _ = int64_row_values(np, arrays, nums, 17, deadline)
        assert got == reference
        cases += len(terms)
    # Each one-hot bit is decoded in original-coordinate order, including
    # byte boundaries and the final partially used byte.
    masks = np.zeros((1214, 152), dtype=np.uint8)
    for i in range(1214):
        masks[i, i//8] = 1 << (i % 8)
    bits = np.unpackbits(masks, axis=1, bitorder="little")[:, :1214]
    assert np.array_equal(bits, np.eye(1214, dtype=np.uint8))
    probe = np.asarray([(7*i+3) % 29 for i in range(1214)], dtype="<i8")
    assert np.array_equal(bits.astype("<i8") @ probe, probe)
    refused = False
    try:
        int64_row_values(np, arrays, [I64]*9, I64, deadline)
    except AssertionError:
        refused = True
    assert refused
    return {"signed_sparse_rows_compared_with_Python_integers": cases,
        "original_cover_bit_positions_checked": 1214,
        "unsafe_integer_arithmetic_refused": True, "optimizer_calls": 0}


def original_native(inventory, point, den, deadline):
    counts = Counter()
    for i, j, q, support in inventory["Gram_rows"]:
        assert sum(point[a] for a in support) == q*den, ("original Gram", i, j)
        counts["Gram"] += 1
    for signature, support in inventory["original_signature_rows"]:
        assert sum(point[a] for a in support) <= den, ("signature", signature)
        counts["signature"] += 1
    for item in inventory["triple_rows"]:
        assert sum(point[a] for a in item["members"]) <= den
        counts["triple"] += 1
    for clause in inventory["Gram_conflict_clauses"]:
        assert len(clause) == 2 and all(type(x) is int and x < 0 for x in clause)
        assert sum(point[-x-1] for x in clause) <= den
        counts["Gram_conflict"] += 1
    for item in inventory["uncapped_integer_cuts"]:
        tick(deadline)
        terms = item["positive_terms"]
        assert all(type(w) is int and w > 0 for a, w in terms)
        d, a = item["positive_demand"], item["target_column"]
        assert type(d) is int and d > 0
        value = sum(w*point[b] for b, w in terms)-d*point[a]
        assert 0 <= value <= sum(w for b, w in terms)*den
        counts["uncapped_row_cut"] += 1
    assert counts == {"Gram": 630, "signature": 186, "triple": 1365,
                      "Gram_conflict": 30, "uncapped_row_cut": 60}
    return dict(counts)


def all_covers(np, compressed, point, den, deadline):
    raw = gzip.decompress(compressed)
    assert sha(raw) == RAW_COVERS_SHA and len(raw) == 178533*154
    packed = np.frombuffer(raw, dtype=np.uint8).reshape(178533, 154)
    assert np.all((packed[:, -1] & 192) == 0)
    targets = packed[:, 0].astype(np.int64)+256*packed[:, 1].astype(np.int64)
    assert np.all(targets < 1214)
    assert np.all((packed[np.arange(178533), 2+targets//8] >> (targets % 8)) & 1 == 0)
    assert 1214*den <= I64
    values = np.asarray(point, dtype="<i8")
    activity_sha = hashlib.sha256()
    for first in range(0, 178533, COVER_BATCH):
        tick(deadline)
        last = min(first+COVER_BATCH, 178533)
        bits = np.unpackbits(packed[first:last, 2:], axis=1, bitorder="little")[:, :1214]
        sums = bits.astype("<i8") @ values
        assert np.all(sums >= values[targets[first:last]]), ("original cover", first)
        activity_sha.update(sums.astype("<i8", copy=False).tobytes())
    return {"original_covers_checked": 178533, "raw_registry_sha256": RAW_COVERS_SHA,
        "little_endian_signature_bit_order": True, "all_guard_columns_checked": True,
        "safe_integer_sum_bound": str(1214*den), "cover_activity_sha256": activity_sha.hexdigest()}


def check(np, values, model, root, deadline):
    with np.load(root/FILES["arrays"][0], allow_pickle=False) as archive:
        arrays = {name: archive[name] for name in archive.files}
    assert {k: sha(v.tobytes()) for k, v in arrays.items()} == model["array_sha256"]
    candidate = json.loads(values["candidate"])
    den = int(candidate["common_denominator"])
    nums = [int(v) for v in candidate["extended_numerators"]]
    assert len(nums) == 1103 and 0 < den <= I64
    assert all(0 <= v <= den for v in nums) and nums[-1] > 0
    ids = list(map(int, arrays["original_column_ids"]))
    zeros = model["fixed_zero_columns"]
    assert len(zeros) == 112 and len(set(zeros)) == 112
    assert ids == [a for a in range(1214) if a not in set(zeros)]
    point = [0]*1214
    for a, v in zip(ids, nums[:-1]):
        point[a] = v
    assert [str(v) for v in point] == candidate["exact_check"]["original1214_selector_numerators"]
    assert sum(point) == 64*den and all(point[a] == 0 for a in zeros)
    _, csr = int64_row_values(np, arrays, nums[:-1], den, deadline)
    assert csr["rows"] == 166011 and csr["terms"] == 10767194
    assert all(0 <= v-nums[-1] <= den for v in nums[:-1])
    for support in model["integer_cover_live_original_supports"]:
        assert sum(point[a] for a in support) == den
    for a, b in model["added_pair_rows"]:
        assert point[a]+point[b] <= den
    assert model["third_parity_cover_range"] == [1,3]
    h3 = sum(point[a] for a in model["third_parity_cover_original_support"])
    assert den <= h3 <= 3*den
    native = json.loads(values["native"])
    inventory = native["primary_inventory"]
    assert native["complete"] and native["case_index"] == 4
    assert sha(canonical(inventory)) == native["primary_inventory_sha256"] == PRIMARY_SHA
    assert inventory["primary_variables"] == 1214
    native_checked = original_native(inventory, point, den, deadline)
    covers = all_covers(np, values["covers"], point, den, deadline)
    return {"status": "PASS: independent exact full H3 selector point arithmetic",
        "base_CSR": csr, "maxmin_extension_rows_checked": 1102,
        "full_face_rows_checked": 167113, "full_variable_bounds_checked": 1103,
        "original_native_family_counts": native_checked, **covers,
        "all_original1214_bounds_and112_zeros_checked": True,
        "population": 64, "both_unit_sums_checked": True,
        "all_four_pair_bounds_checked": True, "H3_range_checked": [1,3],
        "H3_numerator": str(h3), "common_denominator": str(den),
        "t_numerator": str(nums[-1]), "strictly_positive_t": True,
        "binary_incidence_or_graph_claimed": False, "case4_excluded": False}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=("prepare", "check"))
    p.add_argument("--root", type=Path, default=ROOT)
    p.add_argument("--preparation", type=Path)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    assert not args.output.exists()
    started = time.monotonic()
    record = {"status": "UNRESOLVED: independent point arithmetic pending",
        "source_sha256": sha(Path(__file__).read_bytes()),
        "input_bindings": {k: list(v) for k, v in FILES.items()},
        "seconds_limit": SECONDS, "model_rebuilt": False,
        "subject_source_imported": False, "optimizer_calls": 0,
        "linear_solve_calls": 0, "exact_point_verified": False}
    def expired(signum, frame):
        raise TimeoutError("independent60second point arithmetic signal bound")
    previous = signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, SECONDS)
    try:
        import numpy as np
        record["numpy_version"] = np.__version__
        deadline = started+SECONDS
        values, model = bound_inputs(args.root)
        if args.mode == "prepare":
            record["controls"] = controls(np, deadline)
            record["status"] = "PREPARED: independent direct arithmetic; no case point evaluation"
            record["point_values_evaluated"] = False
        else:
            assert args.preparation is not None
            prep = json.loads(args.preparation.read_bytes())
            assert prep["status"].startswith("PREPARED:")
            for key in ("source_sha256", "input_bindings", "seconds_limit", "numpy_version"):
                assert prep[key] == record[key]
            record["preparation_sha256"] = sha(args.preparation.read_bytes())
            record["exact_arithmetic"] = check(np, values, model, args.root, deadline)
            record["status"] = record["exact_arithmetic"]["status"]
            record["exact_point_verified"] = True
    except (AssertionError, TimeoutError, ValueError, OverflowError) as error:
        record.update(status="UNRESOLVED: direct arithmetic failed or reached its bound",
                      failure_type=type(error).__name__, failure=str(error))
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)
        record["elapsed_seconds"] = time.monotonic()-started
        save(args.output, record)
    print(json.dumps(record, indent=2), flush=True)


if __name__ == "__main__":
    main()
