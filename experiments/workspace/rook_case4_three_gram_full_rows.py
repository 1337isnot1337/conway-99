"""Finite full-row refinement of all 260 cold-checked H27 branch boxes.

The old H5 propagation kernel is imported unchanged, but none of its H5
premises or state loaders is used. H42 has only its unconditional upper5 row.
Scope controls, matrix preparation, forward sweep and cold replay are separate.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import resource
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
BASE = "experiments/logs/grids-and-triangles/"
NATIVE_RUN = BASE + "rook-case4-three-gram-branch-batch-v2-run01"
SCOPE_REPORT = ROOT / (BASE + "rook-case4-three-gram-full-rows-scope01.json")
SOURCES = {
    "kernel": ("experiments/workspace/rook_case4_full_span_cover_h5_full_rows.py", "bb26762de18cad7107a2d49214af61947807528cb66a638efec2589cadf26216"),
    "unconditional_rows": ("experiments/workspace/rook_case4_three_gram_branch_batch_v2.py", "0226d59dc1ab724ee712dfdd2249aff34d5248db1f354f264a8726a2e1d2f3cc"),
}
INPUTS = {
    "model": (BASE + "rook-case4-face112-weighted-parity-model01/model.json", "c6cd72c995ce1a47db90fe7263f643131bc555ed50e329c7734536f5cf870ac3"),
    "arrays": (BASE + "rook-case4-face112-weighted-parity-model01/arrays.npz", "59a06470793e6959a67ae30dfb29ecf0de4c8aa74661e1335d7676aa612c1e7e"),
    "matrix_cold": (BASE + "rook-case4-face112-weighted-parity-model01-cold-replay.json", "567185c755134fcf7c15bb7be762bb2a70a503254259b2eb44a92f91abb39156"),
    "scope": (BASE + "rook-case4-three-gram-branches-preparation01/preparation.json", "ad3f2b14fd4f60b0d411cd5d920ec461cffed3ab7a0ddf68861b9500cad95ba3"),
    "scope_cold": (BASE + "rook-case4-three-gram-branches-preparation01-replay.json", "769a2536abf223d5b9f6aac27b50b0623f0976e955d153165e4c7b1fceac7e2c"),
    "native_preflight": (BASE + "rook-case4-three-gram-branch-batch-v2-preflight01.json", "98a2a09b455069be847f0f44e4f0db0db4e6591f9cdda2e0c1530de4d2d1b2c2"),
    "native_forward": (NATIVE_RUN + "/child-result.json", "43c2ad18e26f0a8a0fe7e8247a53a68e300c333e773ef721c98c8e115fe441e2"),
    "native_owner": (NATIVE_RUN + "/supervisor.json", "7d15aaba5028b03baddbcc1ce9930640f3d9964e8cad018c4f3d636b50496f4b"),
    "native_cold": (NATIVE_RUN + "-cold/child-result.json", "881ea0aaccd5e29cd80e1133b1a74a483e819390edfa7f5dd7bab2fc388cc411"),
    "native_cold_owner": (NATIVE_RUN + "-cold/supervisor.json", "5c0c3e0b2617e6a309c8e54a3359f3c13dba571fc05373c32937b6d1ddcbaedc"),
    "native_publication": (BASE + "rook-case4-three-gram-branch-batch-v2-run01-git-blobs.json", "d2bdd8cabdc6f655e0bd7f8ff3b788efbf034f975366141adf10bbbd45b39f56"),
}
LIMITS = {
    "prepare_seconds": 60, "prepare_owner_seconds": 90,
    "forward_seconds": 900, "per_branch_cooperative_seconds": 10,
    "forward_owner_seconds": 1000, "cold_seconds": 1200, "cold_owner_seconds": 1300,
    "maximum_branches": 260, "maximum_transcript_bytes": 64 * 1024 * 1024,
    "maximum_rss_kib": 1024 * 1024, "automatic_retries": 0,
}
VARIABLES, BASE_ROWS, ROWS, BASE_NNZ, NNZ = 1102, 166013, 166020, 10767292, 10767637


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def file_sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def write(path, value, replace=False):
    assert replace or not path.exists()
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("wb" if replace else "xb") as stream:
        stream.write(canonical(value) + b"\n")
        stream.flush()
    temporary.replace(path)


def ref(path):
    return {"path": str(path.resolve().relative_to(ROOT)), "sha256": file_sha(path), "bytes": path.stat().st_size}


def read_ref(reference, relative_path):
    expected = Path(relative_path)
    assert not expected.is_absolute() and ".." not in expected.parts
    recorded = Path(reference["path"])
    assert recorded.parts[-len(expected.parts):] == expected.parts
    raw = (ROOT / expected).read_bytes()
    assert len(raw) == reference["bytes"] and sha(raw) == reference["sha256"]
    return json.loads(raw)


def read_input(key):
    name, expected = INPUTS[key]
    raw = (ROOT / name).read_bytes()
    assert sha(raw) == expected, key
    return json.loads(raw)


def definition():
    return {
        "source_sha256": file_sha(Path(__file__)),
        "sources": {k: {"path": p, "sha256": h} for k, (p, h) in SOURCES.items()},
        "inputs": {k: {"path": p, "sha256": h} for k, (p, h) in INPUTS.items()},
        "limits": LIMITS, "variables": VARIABLES, "rows": ROWS, "nonzeros": NNZ,
        "unchanged_parent_rows": BASE_ROWS, "unchanged_parent_nonzeros": BASE_NNZ,
        "surviving_native_boxes": 260, "prior_native_contradictions": 184,
        "original_coordinates": 1214, "only_shared_zero_premises": 112,
        "appended_rows": "five final parity rows, unconditional H42<=5, and H42+2(x600+x922)<=5",
        "H42_equal_five_is_not_a_premise": True,
        "whole_case4_branch_cover": True, "matrices_built_once_per_child": True,
        "partial_branches_are_saved_and_not_retried": True,
        "partial_or_unprocessed_branch_blocks_whole_cover_conclusions": True,
        "imported_kernel_functions_unchanged": ["Pool", "propagate", "verify_record", "literal_bounds"],
        "optimizer_calls": 0,
    }


def modules():
    loaded = {}
    for key, (name, expected) in SOURCES.items():
        path = ROOT / name
        assert file_sha(path) == expected
        spec = importlib.util.spec_from_file_location("frozen_h27_full_rows_" + key, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        assert module.ROOT == ROOT
        loaded[key] = module
    assert loaded["kernel"].np.__version__ == "2.3.5"
    return loaded["kernel"], loaded["unconditional_rows"]


def ancestors():
    data = {key: read_input(key) for key in INPUTS if key != "arrays"}
    scope = data["scope"]
    assert scope["raw_patterns"] == 2835 and scope["retained_patterns"] == 444
    assert scope["only112_global_zero_premises"] and not scope["H42_five_assumption"]
    assert data["scope_cold"]["status"] == "PASS"
    assert data["scope_cold"]["preparation_sha256"] == INPUTS["scope"][1]
    assert data["model"]["fixed_zero_columns"] == scope["identity"]["proved_zero_columns"]
    assert len(data["model"]["fixed_zero_columns"]) == 112
    assert data["native_publication"]["status"] == "COMPLETE_FROZEN_PUBLICATION_MAP"
    assert data["native_publication"]["file_count"] == 461
    for owner_key, child_key, mode in (("native_owner", "native_forward", "run"), ("native_cold_owner", "native_cold", "replay")):
        owner = data[owner_key]
        assert owner["status"] == "CHILD_COMPLETE" and owner["exit_code"] == 0
        assert owner["child_reaped"] and not owner["hard_timeout"] and owner["mode"] == mode
        assert owner["source_sha256"] == SOURCES["unconditional_rows"][1]
        assert owner["child_result"]["sha256"] == INPUTS[child_key][1]
        assert owner["preflight"]["sha256"] == INPUTS["native_preflight"][1]
    forward, cold = data["native_forward"], data["native_cold"]
    assert forward["complete"] and forward["recorded"] == 444 and forward["partial"] == 0
    assert forward["records"] == data["native_owner"]["records_preserved"]
    assert cold["status"] == "PASS" and cold["all444_branches_checked"] and cold["all_saved_records_checked"]
    assert cold["surviving_boxes"] == 260 and len(cold["checks"]) == 444
    assert cold["forward_owner"]["sha256"] == INPUTS["native_owner"][1]
    assert len(scope["retained"]) == len(forward["records"]) == len(data["native_owner"]["records_preserved"]) == 444
    assert data["matrix_cold"]["model_sha256"] == INPUTS["model"][1]
    return data


def full_pool(kernel, rows_source, data):
    """Frozen base arrays plus seven unconditional original-coordinate rows."""
    np = kernel.np
    model = data["model"]
    assert (model["columns"], model["rows"], model["nonzeros"]) == (VARIABLES, BASE_ROWS, BASE_NNZ)
    assert model["arrays"]["sha256"] == INPUTS["arrays"][1]
    assert data["matrix_cold"]["status"].startswith("PASS:")
    array_path = ROOT / INPUTS["arrays"][0]
    assert file_sha(array_path) == INPUTS["arrays"][1]
    with np.load(array_path, allow_pickle=False) as archive:
        arrays = {name: archive[name] for name in archive.files}
    assert set(arrays) == set(model["array_sha256"])
    assert all(a.dtype.kind in "iu" for a in arrays.values())
    assert {k: sha(v.tobytes()) for k, v in arrays.items()} == model["array_sha256"]
    originals = arrays["original_column_ids"]
    assert list(map(int, originals)) == [a for a in range(1214) if a not in set(model["fixed_zero_columns"])]
    positions = {int(a): j for j, a in enumerate(originals)}
    additions = rows_source.proved_rows(kernel, data["scope"])
    assert len(additions) == 7 and sum(len(r["terms"]) for r in additions) == 345
    assert additions[5]["kind"] == "proved_H42_upper_five"
    assert (additions[5]["lower"], additions[5]["upper"]) == (0, 5)
    assert all(r["kind"] != "conditional_H_five" for r in additions)
    suffix_col, suffix_coef, ends = [], [], []
    for row in additions:
        assert all(type(x) is int for x in (row["lower"], row["upper"]))
        assert all(type(a) is type(c) is int and c != 0 and a in positions for a, c in row["terms"])
        terms = [(positions[a], c) for a, c in row["terms"]]
        assert terms == sorted(terms) and len({a for a, c in terms}) == len(terms)
        suffix_col.extend(a for a, c in terms)
        suffix_coef.extend(c for a, c in terms)
        ends.append(BASE_NNZ + len(suffix_col))
    pool = kernel.Pool(
        np.concatenate((arrays["row_pointers"], np.asarray(ends, dtype=np.int64))),
        np.concatenate((arrays["column_indices"], np.asarray(suffix_col, dtype=np.int32))),
        np.concatenate((arrays["coefficients"], np.asarray(suffix_coef, dtype=np.int64))),
        np.concatenate((arrays["row_lower"], np.asarray([r["lower"] for r in additions], dtype=np.int64))),
        np.concatenate((arrays["row_upper"], np.asarray([r["upper"] for r in additions], dtype=np.int64))),
        VARIABLES)
    assert (pool.nrows, pool.nnz) == (ROWS, NNZ)
    for actual, old in ((pool.ptr[:BASE_ROWS + 1], arrays["row_pointers"]),
                        (pool.col[:BASE_NNZ], arrays["column_indices"]),
                        (pool.coef[:BASE_NNZ], arrays["coefficients"]),
                        (pool.lower[:BASE_ROWS], arrays["row_lower"]),
                        (pool.upper[:BASE_ROWS], arrays["row_upper"])):
        assert np.array_equal(actual, old)
    return pool, originals, additions


def extract_states(kernel, data, originals):
    """Reconstruct the saved exact boxes without repeating native propagation."""
    np = kernel.np
    scope, cold = data["scope"], data["native_cold"]
    zeros, positive = set(scope["identity"]["proved_zero_columns"]), set(scope["identity"]["positive_support"])
    states, branches, terminal_counts = [], [], Counter()
    for i, (branch, old_ref, check) in enumerate(zip(scope["retained"], data["native_owner"]["records_preserved"], cold["checks"])):
        record = read_ref(old_ref, NATIVE_RUN + f"/branch-{i:03d}.json")
        assert record["index"] == check["index"] == branch["branch_id"] == i
        assert record["raw_id"] == check["raw_id"] == branch["raw_id"]
        assert record["selected"] == branch["selected"] and record["kind"] == branch["kind"]
        assert record["terminal"]["status"] == check["terminal"] and check["status"] == "PASS"
        assert len(record["trace"]) == check["forces"]
        status = check["terminal"]
        terminal_counts[status] += 1
        if status.startswith("contradiction"):
            continue
        assert status == "fixed_point"
        fixed = sorted(zeros | (positive - set(branch["selected"])))
        assert sha(canonical({"zeros": fixed, "ones": branch["selected"]})) == record["initial_box_sha256"] == branch["initial_box_sha256"]
        state = np.full(1214, -1, dtype=np.int8)
        state[fixed] = 0
        assert all(state[a] == -1 for a in branch["selected"])
        state[branch["selected"]] = 1
        for rid, a, value in record["trace"]:
            assert type(rid) is type(a) is type(value) is int
            assert 0 <= rid < 2278 and 0 <= a < 1214 and value in (0, 1) and state[a] == -1
            state[a] = value
        assert sha(state.tobytes()) == record["final_state_sha256"]
        assert all(state[a] == 0 for a in zeros)
        projected = state[originals]
        restored = np.zeros(1214, dtype=np.int8)
        restored[originals] = projected
        assert np.array_equal(restored, state)
        branches.append({"index": len(branches), "prior_branch_id": i, "raw_id": branch["raw_id"],
                         "kind": branch["kind"], "selected": branch["selected"],
                         "native_record": {"path": NATIVE_RUN + f"/branch-{i:03d}.json", "sha256": old_ref["sha256"], "bytes": old_ref["bytes"]},
                         "native_final1214_state_sha256": record["final_state_sha256"],
                         "initial_state_sha256": sha(projected.tobytes()), "native_forces": check["forces"]})
        states.append(projected)
    assert terminal_counts == {"contradiction": 184, "fixed_point": 260}
    assert len(states) == 260
    assert Counter(b["kind"] for b in branches) == {"weight3_singleton": 1, "weight1_weight2_pair": 65, "three_weight1": 194}
    return branches, np.stack(states)


def coverage_ready(total, source_complete, statuses, checked):
    return total > 0 and source_complete and len(statuses) == checked == total and "partial" not in statuses


def common_literals(states, originals):
    if not states:
        return [], []
    zero = [int(a) for j, a in enumerate(originals) if all(int(s[j]) == 0 for s in states)]
    one = [int(a) for j, a in enumerate(originals) if all(int(s[j]) == 1 for s in states)]
    return zero, one


def controls():
    projections = 0
    for n in range(1, 7):
        coefficients = [(-2, 0, 3)[j % 3] for j in range(n)]
        for zero_bits in range(1 << n):
            kept = [j for j in range(n) if not (zero_bits >> j) & 1]
            for values in itertools.product((-1, 0, 1), repeat=len(kept)):
                full = [0] * n
                for j, value in zip(kept, values):
                    full[j] = value
                def box(terms, state):
                    return (sum(c * state[j] if state[j] >= 0 else min(0, c) for j, c in terms),
                            sum(c * state[j] if state[j] >= 0 else max(0, c) for j, c in terms))
                assert box(list(enumerate(coefficients)), full) == box([(i, coefficients[j]) for i, j in enumerate(kept)], values)
                assert [full[j] for j in kept] == list(values)
                projections += 1
    coverage = 0
    for n in range(1, 6):
        for statuses in itertools.product(("contradiction", "fixed_point", "partial"), repeat=n):
            assert coverage_ready(n, True, statuses, n) == ("partial" not in statuses)
            assert not coverage_ready(n, False, statuses, n)
            assert not coverage_ready(n, True, statuses[:-1], n - 1)
            coverage += 1
    assert not coverage_ready(0, True, [], 0)
    assert common_literals([], [2, 5, 8]) == ([], [])
    assert common_literals([[0, 1, -1], [0, 1, 0]], [2, 5, 8]) == ([2], [5])
    return {"status": "PASS", "literal_projection_and_signed_box_controls": projections,
            "partial_coverage_gate_controls": coverage, "empty_family_has_no_vacuous_units": True,
            "kernel_controls_repeated": False, "case_propagation_calls": 0, "optimizer_calls": 0}


def scope_report(output):
    assert output.resolve() == SCOPE_REPORT.resolve()
    checked = {}
    for key, (name, expected) in {**SOURCES, **INPUTS}.items():
        assert file_sha(ROOT / name) == expected
        checked[key] = expected
    report = {"status": "PREPARED_SOURCE_SCOPE_ONLY", "definition": definition(), "controls": controls(),
              "dependency_file_hashes_checked": checked, "matrix_built": False,
              "subject_kernel_imported": False, "case_propagation_calls": 0, "optimizer_calls": 0}
    write(output, report)
    return report


def read_scope_report():
    report = json.loads(SCOPE_REPORT.read_bytes())
    assert report["status"] == "PREPARED_SOURCE_SCOPE_ONLY" and report["definition"] == definition()
    assert report["controls"]["status"] == "PASS"
    assert report["controls"]["literal_projection_and_signed_box_controls"] == 5460
    assert report["controls"]["partial_coverage_gate_controls"] == 363
    assert not report["matrix_built"] and not report["subject_kernel_imported"]
    assert report["case_propagation_calls"] == report["optimizer_calls"] == 0
    return report


def prepare(directory):
    started = time.monotonic()
    scope = read_scope_report()
    kernel, rows_source = modules()
    data = ancestors()
    pool, originals, additions = full_pool(kernel, rows_source, data)
    branches, states = extract_states(kernel, data, originals)
    path = directory / "states.npz"
    with path.open("xb") as stream:
        kernel.np.savez_compressed(stream, states=states, original_column_ids=originals)
    assert time.monotonic() - started <= LIMITS["prepare_seconds"]
    assert resource.getrusage(resource.RUSAGE_SELF).ru_maxrss <= LIMITS["maximum_rss_kib"]
    report = {"status": "PREPARED_FULL260_NO_CASE_PROPAGATION", "definition": definition(),
              "controls": scope["controls"], "scope_report": ref(SCOPE_REPORT), "numpy_version": kernel.np.__version__,
              "matrix": {"columns": pool.nvars, "rows": pool.nrows, "nonzeros": pool.nnz,
                         "maximum_int64_activity_bound": pool.activity_bound, "all_parent_array_prefixes_equal": True},
              "appended_rows": additions, "branches": branches,
              "prepared_states": {"file": path.name, "sha256": file_sha(path), "bytes": path.stat().st_size,
                                  "shape": list(states.shape)},
              "all444_native_record_hashes_checked": True, "prior_exact_reason_replay_repeated": False,
              "all184_prior_native_contradictions_bound": True, "projected_only112_global_zeros": True,
              "former_H5_conditional_states_loaded": False, "case_propagation_calls": 0, "optimizer_calls": 0,
              "seconds": time.monotonic() - started, "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    write(directory / "preparation.json", report)
    return report


def load_preparation(path):
    raw = path.read_bytes()
    prep = json.loads(raw)
    assert prep["status"] == "PREPARED_FULL260_NO_CASE_PROPAGATION" and prep["definition"] == definition()
    assert prep["controls"]["status"] == "PASS" and prep["case_propagation_calls"] == 0
    assert prep["scope_report"] == ref(SCOPE_REPORT) and prep["controls"] == read_scope_report()["controls"]
    preparation_owner = json.loads((path.parent / "supervisor.json").read_bytes())
    assert preparation_owner["mode"] == "prepare" and preparation_owner["status"] == "CHILD_COMPLETE"
    assert preparation_owner["exit_code"] == 0 and preparation_owner["child_reaped"] and not preparation_owner["hard_timeout"]
    assert preparation_owner["source_sha256"] == file_sha(Path(__file__))
    assert preparation_owner["child_result"]["sha256"] == sha(raw)
    kernel, rows_source = modules()
    data = ancestors()
    pool, originals, additions = full_pool(kernel, rows_source, data)
    assert prep["appended_rows"] == additions and prep["numpy_version"] == kernel.np.__version__
    assert prep["prepared_states"]["file"] == "states.npz"
    state_path = path.parent / "states.npz"
    assert file_sha(state_path) == prep["prepared_states"]["sha256"]
    with kernel.np.load(state_path, allow_pickle=False) as archive:
        assert set(archive.files) == {"states", "original_column_ids"}
        states, saved_originals = archive["states"], archive["original_column_ids"]
    assert kernel.np.array_equal(originals, saved_originals)
    assert states.dtype == kernel.np.dtype("int8") and states.shape == (260, VARIABLES)
    assert kernel.np.all((states >= -1) & (states <= 1)) and len(prep["branches"]) == 260
    for i, (branch, state) in enumerate(zip(prep["branches"], states)):
        assert branch["index"] == i and sha(state.tobytes()) == branch["initial_state_sha256"]
    actual_branches, actual_states = extract_states(kernel, data, originals)
    assert actual_branches == prep["branches"] and kernel.np.array_equal(actual_states, states)
    assert prep["matrix"] == {"columns": pool.nvars, "rows": pool.nrows, "nonzeros": pool.nnz,
                              "maximum_int64_activity_bound": pool.activity_bound, "all_parent_array_prefixes_equal": True}
    return prep, kernel, pool, originals, states


def forward(preparation_path, directory):
    initialize = time.monotonic()
    prep, kernel, pool, originals, states = load_preparation(preparation_path)
    initialization_seconds = time.monotonic() - initialize
    started = time.monotonic()
    deadline = started + LIMITS["forward_seconds"]
    records, statuses, used, stop = [], [], 0, "complete finite sweep"
    for index, (branch, state) in enumerate(zip(prep["branches"], states)):
        if time.monotonic() >= deadline:
            stop = "shared forward time bound"
            break
        one_start = time.monotonic()
        result = kernel.propagate(pool, state, originals, min(deadline, one_start + LIMITS["per_branch_cooperative_seconds"]))
        record = {"index": index, "prior_branch_id": branch["prior_branch_id"], "raw_id": branch["raw_id"],
                  "selected": branch["selected"], "initial_state_sha256": branch["initial_state_sha256"],
                  **result, "seconds": time.monotonic() - one_start}
        encoded_size = len(canonical(record)) + 1
        if used + encoded_size > LIMITS["maximum_transcript_bytes"]:
            stop = "transcript resource bound"
            break
        path = directory / f"branch-{index:03d}.json"
        write(path, record)
        records.append(ref(path))
        statuses.append(record["terminal"]["status"])
        used += encoded_size
        write(directory / "progress.json", {"records": records, "recorded": len(records),
                                             "partial": statuses.count("partial"), "next_index": index + 1}, replace=True)
        assert resource.getrusage(resource.RUSAGE_SELF).ru_maxrss <= LIMITS["maximum_rss_kib"]
        # A partial branch is preserved once, then the next distinct branch starts.
    complete = len(records) == 260 and "partial" not in statuses
    report = {"status": "COMPLETE_FULL260_PREFIX" if complete else "PARTIAL_FULL260_PREFIX",
              "definition": definition(), "preparation": ref(preparation_path), "records": records,
              "all260_attempts_recorded": len(records) == 260, "all260_nonpartial_terminals": complete,
              "recorded": len(records), "unprocessed_UNKNOWN": 260 - len(records),
              "contradictions": sum(s.startswith("contradiction") for s in statuses),
              "fixed_points": statuses.count("fixed_point"), "partial": statuses.count("partial"),
              "stop": stop, "transcript_bytes": used, "cold_required": True, "case4_excluded": False,
              "initialization_seconds": initialization_seconds, "forward_seconds": time.monotonic() - started,
              "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss, "optimizer_calls": 0}
    write(directory / "child-result.json", report)
    return report


def cold(preparation_path, source_directory, directory):
    initialize = time.monotonic()
    prep, kernel, pool, originals, states = load_preparation(preparation_path)
    initialization_seconds = time.monotonic() - initialize
    owner_path = source_directory / "supervisor.json"
    owner = json.loads(owner_path.read_bytes())
    assert owner["source_sha256"] == file_sha(Path(__file__)) and owner["mode"] == "run"
    assert owner["child_reaped"] and owner["preparation"]["sha256"] == file_sha(preparation_path)
    references = owner["records_preserved"]
    assert len(references) <= 260
    if owner["status"] == "CHILD_COMPLETE":
        assert owner["exit_code"] == 0 and not owner["hard_timeout"]
        assert owner["seconds"] <= LIMITS["forward_owner_seconds"]
        forward_result = read_ref(owner["child_result"], str(source_directory.relative_to(ROOT) / "child-result.json"))
        assert forward_result["definition"] == definition() and forward_result["records"] == references
        assert forward_result["preparation"]["sha256"] == file_sha(preparation_path)
    started = time.monotonic()
    deadline = started + LIMITS["cold_seconds"]
    checks, statuses, surviving = [], [], []
    positions = {int(a): j for j, a in enumerate(originals)}
    for index, reference in enumerate(references):
        if time.monotonic() >= deadline:
            break
        relative = str(source_directory.relative_to(ROOT) / f"branch-{index:03d}.json")
        record = read_ref(reference, relative)
        branch = prep["branches"][index]
        assert record["index"] == index and record["prior_branch_id"] == branch["prior_branch_id"]
        assert record["raw_id"] == branch["raw_id"] and record["selected"] == branch["selected"]
        assert record["initial_state_sha256"] == branch["initial_state_sha256"]
        check = kernel.verify_record(pool, states[index], originals, record)
        check.update(index=index, prior_branch_id=branch["prior_branch_id"], original_record=reference)
        write(directory / f"check-{index:03d}.json", check)
        checks.append(ref(directory / f"check-{index:03d}.json"))
        statuses.append(check["terminal"])
        if not check["terminal"].startswith("contradiction"):
            state = states[index].copy()
            for rid, original, value in record["trace"]:
                state[positions[original]] = value
            surviving.append(state)
        write(directory / "progress.json", {"checks": checks, "checked": len(checks)}, replace=True)
        assert resource.getrusage(resource.RUSAGE_SELF).ru_maxrss <= LIMITS["maximum_rss_kib"]
    all_checked = len(checks) == len(references)
    ready = coverage_ready(260, owner["status"] == "CHILD_COMPLETE", statuses, len(checks))
    zeros, ones = common_literals(surviving, originals) if ready else ([], [])
    report = {"status": "PASS" if all_checked else "PARTIAL_REPLAY", "definition": definition(),
              "preparation": ref(preparation_path), "forward_owner": ref(owner_path), "checks": checks,
              "all_saved_records_checked": all_checked, "all260_nonpartial_branches_checked": ready,
              "checked": len(checks), "checked_contradictions": sum(s.startswith("contradiction") for s in statuses),
              "checked_fixed_points": statuses.count("fixed_point"), "checked_partial": statuses.count("partial"),
              "new_global_zero_columns": zeros, "new_global_one_columns": ones,
              "prior184_contradictions_and_complete_original_branch_cover_bound": True,
              "partial_or_missing_branches_never_support_whole_cover_conclusions": True,
              "case4_excluded": ready and not surviving, "whole_graph_problem_resolved": False,
              "initialization_seconds": initialization_seconds, "cold_seconds": time.monotonic() - started,
              "optimizer_calls": 0}
    write(directory / "child-result.json", report)
    return report


def owned(mode, preparation_path, directory, source_directory=None):
    assert not directory.exists()
    directory.mkdir(parents=True)
    maximum = LIMITS[{"prepare": "prepare_owner_seconds", "run": "forward_owner_seconds", "replay": "cold_owner_seconds"}[mode]]
    started = time.monotonic()
    command = [sys.executable, str(Path(__file__).resolve()), "_" + mode, "--directory", str(directory.resolve())]
    if preparation_path is not None:
        command += ["--preparation", str(preparation_path.resolve())]
    if source_directory is not None:
        command += ["--source-directory", str(source_directory.resolve())]
    with (directory / "stdout.log").open("xb") as out, (directory / "stderr.log").open("xb") as err:
        child = subprocess.Popen(command, stdout=out, stderr=err)
        timed_out = False
        try:
            code = child.wait(timeout=max(0.001, maximum - (time.monotonic() - started)))
        except subprocess.TimeoutExpired:
            timed_out = True
            child.kill()
            code = child.wait()
    child_file = directory / ("preparation.json" if mode == "prepare" else "child-result.json")
    elapsed = time.monotonic() - started
    accepted = code == 0 and child_file.exists() and not timed_out and elapsed <= maximum
    report = {"status": "CHILD_COMPLETE" if accepted else "UNKNOWN", "mode": mode,
              "source_sha256": file_sha(Path(__file__)), "maximum_owned_seconds": maximum,
              "seconds": elapsed, "exit_code": code, "hard_timeout": timed_out, "child_reaped": True,
              "records_preserved": [ref(p) for p in sorted(directory.glob("branch-*.json"))],
              "replay_checks_preserved": [ref(p) for p in sorted(directory.glob("check-*.json"))],
              "automatic_retries": 0, "case4_excluded": False, "optimizer_calls": 0}
    if preparation_path is not None:
        report["preparation"] = ref(preparation_path)
    if child_file.exists():
        report["child_result"] = ref(child_file)
    write(directory / "supervisor.json", report)
    return report


def main():
    if not __debug__:
        raise RuntimeError("assertions are required")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("scope", "prepare", "run", "replay", "_prepare", "_run", "_replay"))
    parser.add_argument("--output", type=Path)
    parser.add_argument("--directory", type=Path)
    parser.add_argument("--preparation", type=Path)
    parser.add_argument("--source-directory", type=Path)
    args = parser.parse_args()
    if args.mode == "scope":
        result = scope_report(args.output)
    elif args.mode.startswith("_"):
        if args.mode == "_prepare":
            result = prepare(args.directory)
        elif args.mode == "_run":
            result = forward(args.preparation, args.directory)
        else:
            result = cold(args.preparation, args.source_directory, args.directory)
    else:
        result = owned(args.mode, args.preparation, args.directory, args.source_directory)
    print(json.dumps({k: v for k, v in result.items() if k in ("status", "seconds", "recorded", "checked", "case4_excluded")}), flush=True)


if __name__ == "__main__":
    main()
