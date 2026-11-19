"""Append the single27-term H3 cover to the complete112-face selector LP.

All166010 parent rows, all original columns and every retained cover remain
unchanged. The appended range1<=H3<=3 is checked by the direct original-row
certificate. No optimizer, additional zero, or candidate assumption is used.
"""
import argparse
import hashlib
import json
from pathlib import Path
import resource
import signal
import time

import numpy as np

import rook_case4_face112_model as parent
import rook_case4_face112_third_parity_cover as cover

ROOT, BASE = parent.ROOT, parent.BASE
recovery, closure = parent.recovery, parent.closure
PARENT_SHA = "8cfae2fc990e293f47029da2dc5a4d66b864e2547777d6a142de424133361da7"
COVER_SHA = "9da8c7edc60429b6a7bee6cd15da447e08a6ae1656a4be5b77b1dd2f5ba5bdb3"
INPUTS = dict(parent.INPUTS, **{
    "parent_model": (BASE+"rook-case4-face112-model01/model.json", "018882c8cea2a8cb9c2fc73a433d40973d20588bc5accb0fb8b0165fddc4337f"),
    "parent_arrays": (BASE+"rook-case4-face112-model01/arrays.npz", "276db9d80b2772ab6829daf7459b19043a08996dc2b45ff8769534548b8b8ca3"),
    "parent_complete_cold": (BASE+"rook-case4-face112-model01-cold-replay.json", "26f063161cbf9c0beb139b392f0b46007254176c522308d3ed2d5e3ee3c2e703"),
    "H3_certificate": (BASE+"rook-case4-face112-third-parity-cover-certificate.json", "4ab891e2d809847804b4b3d3626f9c4e498d32788d90ddb865da2ed4c98b6ef7"),
    "H3_replay": (BASE+"rook-case4-face112-third-parity-cover-replay.json", "a3b57893b112ed96a5e3dc812dfd9dd5ed0776284dbe59165335167214983a76"),
})
SELECTORS, PARENT_ROWS, ROWS = 1102, 166010, 166011
PARENT_NONZEROS, NONZEROS = 10767167, 10767194
NATIVE_ROWS, COVERS = 1960, 164044
SECONDS, RSS_KIB = 180, 1048576


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return recovery.canonical(value)


def source_bindings():
    assert digest(Path(parent.__file__).read_bytes()) == PARENT_SHA
    assert digest(Path(cover.__file__).read_bytes()) == COVER_SHA
    old = parent.source_bindings()
    return dict(old, builder_sha256=digest(Path(__file__).read_bytes()),
                unchanged112_parent_builder_sha256=PARENT_SHA,
                direct_H3_verifier_sha256=COVER_SHA)


def inputs(root):
    source_bindings()
    for name, (path, expected) in INPUTS.items():
        assert digest((root/path).read_bytes()) == expected, name
    saved, arrays = parent.load(root/INPUTS["parent_model"][0], root/INPUTS["parent_arrays"][0])
    cold = json.loads((root/INPUTS["parent_complete_cold"][0]).read_bytes())
    assert cold["model_sha256"] == INPUTS["parent_model"][1]
    assert cold["all_omission_witnesses_replayed"] and cold["all_row_column_transports_checked"]
    proof = cover.build()
    assert proof == json.loads((root/INPUTS["H3_certificate"][0]).read_bytes())
    replay = json.loads((root/INPUTS["H3_replay"][0]).read_bytes())
    assert replay["certificate_sha256"] == INPUTS["H3_certificate"][1]
    assert replay["cover_range"] == [1, 3] and replay["full1214_original_expansion"]
    assert set(proof["prior111_zero_columns"]) < set(saved["fixed_zero_columns"])
    assert set(saved["fixed_zero_columns"])-set(proof["prior111_zero_columns"]) == {663}
    return saved, arrays, proof


def integer_stream(arrays, stop):
    result = hashlib.sha256()
    pair_dtype = np.dtype([("column", "<u4"), ("coefficient", "<i8")], align=False)
    assert pair_dtype.itemsize == recovery.TERM.size == 12
    for row in range(stop):
        a, b = map(int, arrays["row_pointers"][row:row+2])
        result.update(recovery.HEADER.pack(int(arrays["row_origin_kind"][row]),
            int(arrays["row_origin_index"][row]), int(arrays["row_lower"][row]),
            int(arrays["row_upper"][row]), b-a))
        terms = np.empty(b-a, dtype=pair_dtype)
        terms["column"] = arrays["column_indices"][a:b]
        terms["coefficient"] = arrays["coefficients"][a:b]
        result.update(terms.tobytes())
    return result.hexdigest()


def append(old, base, proof):
    kept = list(map(int, base["original_column_ids"]))
    position = {a: j for j, a in enumerate(kept)}
    assert len(kept) == SELECTORS and len(proof["cover_terms"]) == 27
    assert proof["new_cover_lower"] == 1 and proof["proved_upper_with_unit_sums"] == 3
    terms = [[position[a], c] for a, c in proof["cover_terms"]]
    assert terms == sorted(terms) and len({a for a, c in terms}) == 27 and all(c == 1 for a, c in terms)
    arrays = {name: value.copy() for name, value in base.items()}
    suffix = {
        "coefficients": np.ones(27, dtype="<i8"),
        "column_indices": np.asarray([a for a, c in terms], dtype="<i4"),
        "row_pointers": np.asarray([NONZEROS], dtype="<i8"),
        "row_lower": np.asarray([1], dtype="<i8"),
        "row_upper": np.asarray([3], dtype="<i8"),
        "row_origin_kind": np.asarray([4], dtype="u1"),
        "row_origin_index": np.asarray([0], dtype="<i4"),
        "current_row_to_previous": np.asarray([-1], dtype="<i4"),
    }
    for name, extra in suffix.items():
        arrays[name] = np.concatenate((base[name], extra))
    for name, value in base.items():
        assert arrays[name].dtype == value.dtype
        assert arrays[name][:len(value)].tobytes() == value.tobytes(), ("parent array prefix", name)
        if name not in suffix:
            assert arrays[name].tobytes() == value.tobytes()
    assert len(arrays["coefficients"]) == len(arrays["column_indices"]) == NONZEROS
    assert len(arrays["row_pointers"]) == ROWS+1 and arrays["row_pointers"][-1] == NONZEROS
    assert integer_stream(arrays, PARENT_ROWS) == old["canonical_integer_stream_sha256"]
    record = {k: v for k, v in old.items() if k not in ("arrays", "controls", "preparation_seconds", "peak_rss_kib")}
    record.update({
        "status": "complete112-face LP plus one proved27-term H3 row prepared; no optimizer",
        "source_bindings": source_bindings(), "parent_input_bindings": {k: list(v) for k, v in INPUTS.items()},
        "rows": ROWS, "nonzeros": NONZEROS,
        "unchanged_parent_rows": PARENT_ROWS, "unchanged_parent_nonzeros": PARENT_NONZEROS,
        "unchanged_parent_stream_sha256": old["canonical_integer_stream_sha256"],
        "third_parity_cover_row": PARENT_ROWS,
        "third_parity_cover_original_support": proof["cover_support"],
        "third_parity_cover_range": [1, 3],
        "third_parity_cover_original_Gram_rows": [r["original_Gram_row"] for r in proof["five_original_Gram_rows"]],
        "third_parity_cover_sparse_equivalent": proof["sparse_equivalent"],
        "third_parity_cover_upper_is_existing_real_row_consequence": True,
        "new_zero_or_positive_selector_assumption": False,
        "new_rows_necessary_for_nonnegative_integer_incidences": True,
        "parent_real_feasible_set_preservation_claimed": False,
        "scope": "Every actual case4 incidence satisfies the complete frozen112-face parent and this one H3 cover. All previous rows and covers are preserved exactly; no candidate or extra zero premise is imposed.",
        "row_inventory": dict(old["row_inventory"], retained_third_integer_parity_cover=1),
        "canonical_integer_stream_sha256": integer_stream(arrays, ROWS),
        "canonical_integer_stream_format": old["canonical_integer_stream_format"]+"; kind4 is the single H3 row",
        "array_sha256": {name: digest(value.tobytes()) for name, value in arrays.items()},
        "uncompressed_array_bytes": sum(value.nbytes for value in arrays.values()),
        "all_parent_array_prefixes_equal": True,
    })
    return record, arrays


def build(root):
    saved, base, proof = inputs(root)
    rebuilt, current = parent.build(root)
    for key, value in rebuilt.items():
        if key not in ("numpy_version", "python_version"):
            assert saved[key] == value, ("cold parent field", key)
    assert set(base) == set(current)
    for name in base:
        assert np.array_equal(base[name], current[name]), ("cold parent array", name)
    return append(rebuilt, current, proof)


def load(model_path, arrays_path=None):
    model = json.loads(model_path.read_bytes())
    assert model["source_bindings"] == source_bindings()
    assert model["parent_input_bindings"] == {k: list(v) for k, v in INPUTS.items()}
    assert (model["columns"], model["rows"], model["nonzeros"]) == (SELECTORS, ROWS, NONZEROS)
    assert model["unchanged_parent_rows"] == PARENT_ROWS and model["third_parity_cover_row"] == PARENT_ROWS
    assert model["third_parity_cover_range"] == [1, 3]
    arrays_path = arrays_path or model_path.parent/model["arrays"]["path"]
    assert digest(arrays_path.read_bytes()) == model["arrays"]["sha256"]
    with np.load(arrays_path, allow_pickle=False) as archive:
        arrays = {name: archive[name] for name in archive.files}
    assert {name: digest(value.tobytes()) for name, value in arrays.items()} == model["array_sha256"]
    assert all(value.dtype.kind in "iu" for value in arrays.values())
    assert list(map(int, arrays["original_column_ids"])) == [a for a in range(1214) if a not in set(model["fixed_zero_columns"])]
    assert len(model["fixed_zero_columns"]) == 112 and not model["fixed_one_columns"]
    assert len(arrays["coefficients"]) == len(arrays["column_indices"]) == NONZEROS
    assert len(arrays["row_pointers"]) == ROWS+1 and arrays["row_pointers"][-1] == NONZEROS
    assert all(len(arrays[k]) == ROWS for k in ("row_lower", "row_upper", "row_origin_kind", "row_origin_index", "current_row_to_previous"))
    assert list(map(int, arrays["row_origin_kind"][-7:])) == [2, 2, 3, 3, 3, 3, 4]
    a, b = map(int, arrays["row_pointers"][-2:])
    assert (a, b) == (PARENT_NONZEROS, NONZEROS) and np.all(arrays["coefficients"][a:b] == 1)
    assert [int(arrays["original_column_ids"][j]) for j in arrays["column_indices"][a:b]] == model["third_parity_cover_original_support"]
    assert [int(arrays["row_lower"][-1]), int(arrays["row_upper"][-1])] == [1, 3]
    assert arrays["current_row_to_previous"][-1] == -1
    return model, arrays


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=("prepare", "replay"))
    p.add_argument("--root", type=Path, default=ROOT)
    p.add_argument("--directory", type=Path)
    p.add_argument("--model", type=Path)
    p.add_argument("--output", type=Path)
    args = p.parse_args()
    started = time.monotonic()
    def expired(_signum, _frame):
        raise TimeoutError("bounded180second H3 overlay preparation/replay")
    handler = signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, SECONDS)
    try:
        if args.mode == "prepare":
            assert args.directory is not None and not args.directory.exists()
            args.directory.mkdir(parents=True)
            old, base, proof = inputs(args.root.resolve())
            model, arrays = append(old, base, proof)
            path = args.directory/"arrays.npz"
            with path.open("xb") as stream:
                np.savez_compressed(stream, **arrays)
            model["arrays"] = {"path": "arrays.npz", "sha256": digest(path.read_bytes()), "bytes": path.stat().st_size}
            model["preparation_seconds"] = time.monotonic()-started
            model["peak_rss_kib"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            assert model["peak_rss_kib"] <= RSS_KIB
            model_path = args.directory/"model.json"
            recovery.write_json(model_path, model)
            loaded, stored = load(model_path, path)
            for name, value in arrays.items():
                assert np.array_equal(value, stored[name])
            output = args.directory/"preparation.json"
            status = "PASS: unchanged complete112 parent prefix and single H3 row prepared"
        else:
            assert args.model is not None and args.output is not None and not args.output.exists()
            model_path = args.model
            model, stored = load(model_path)
            current, arrays = build(args.root.resolve())
            for key, value in current.items():
                if key not in ("numpy_version", "python_version"):
                    assert model[key] == value, ("cold overlay field", key)
            for name, value in arrays.items():
                assert np.array_equal(value, stored[name]), ("cold H3 array", name)
            output = args.output
            status = "PASS: complete original112 model and direct H3 proof cold rebuilt"
        report = {"status": status, "source_bindings": source_bindings(),
            "model_sha256": digest(model_path.read_bytes()), "columns": SELECTORS,
            "rows": ROWS, "nonzeros": NONZEROS, "unchanged_parent_rows": PARENT_ROWS,
            "appended_H3_rows": 1, "H3_range": [1, 3],
            "canonical_integer_stream_sha256": model["canonical_integer_stream_sha256"],
            "arrays": model["arrays"], "all_omission_witnesses_replayed": True,
            "all_row_column_transports_checked": True, "all_parent_array_prefixes_equal": True,
            "optimizer_calls": 0, "case4_excluded": False,
            "seconds": time.monotonic()-started, "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
        assert report["peak_rss_kib"] <= RSS_KIB
        recovery.write_json(output, report)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, handler)
    print(json.dumps(report, indent=2), flush=True)


if __name__ == "__main__":
    main()
