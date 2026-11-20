"""Read-only scope and storage inventory for a proposed full-row low50 pilot.

No NumPy/highspy import, model assembly, matrix coefficient decompression,
propagation, solver, or repeated mathematical acceptance check.
"""
from pathlib import Path
import ast
import gzip
import hashlib
import json
import struct
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[2]
LOG = ROOT / "experiments/logs/grids-and-triangles"
BINDINGS = {
    "small_specification": ("rook-case4-low54-native-lp-preparation02/specification.json.gz", "b037035bb6756bcb259cc06fc6ae22781f343fedeb38c8ec923dcb19fdb50164"),
    "small_cold": ("rook-case4-low54-native-lp-run01/cold.json", "ea492ec530c512759b93d25afc6900a2468d1f221f75aac2eb39092bd8af73f3"),
    "small_analysis": ("rook-case4-low54-native-lp-run01-analysis.json", "0e1cc245793cd1174699bd831355b92f72f7476570c083b1146515995dd6eaa6"),
    "six_cut_preparation": ("rook-case4-box-cut-lp-preparation01.json", "99dc881f2c7139eb336e6792f0acba6ba6499fecbed12b5fc92d746142d6eaf0"),
    "six_cut_preflight": ("rook-case4-box-cut-lp-preflight01.json", "05fe7ac3f17b0dfe9329251aa017022db75e335538959e13033701fc9d1062a2"),
    "six_cut_state": ("rook-case4-box-cut-lp-run01/state-numeric.json", "0d9427431e87f4a9c1f02030e3a80c23d0f3d53faacbe3ff7767d5dc6f3d6a14"),
    "six_cut_numeric": ("rook-case4-box-cut-lp-run01/numeric/result.json", "ed9be814df53efdfcda2201f591ced1caf5af5438c9c08a469997b8c73baabef"),
    "point": ("rook-case4-box-cut-lp-run01/exact/candidate.json", "7fda72c6a212a6ebe504c03a17f66c05c8545d33e4aebc651f42f817cc3a4bd9"),
    "point_cold": ("rook-case4-box-cut-lp-run01/exact/cold.json", "b69a3a38aeb911c45657871544f21897bc4f9bb6201675c1eab5f45ca8a5c317"),
}
SOURCES = {
    "adapter": ("experiments/workspace/rook_case4_box_cut_lp_adapter.py", "7f574542d4fef61915337696bd6061d98ee4bdc3eb57709b7a698b3f4cb1ed07"),
    "generation": ("experiments/workspace/rook_case4_face112_weighted_parity_generation.py", "fb4c4b853708740e1a1726cb4455a5c82a7ae3659439407f4a00a33c67c71ec7"),
    "small_helper": ("experiments/workspace/rook_case4_low54_native_lp.py", "174c084dc9df3e3e0eed5e028ad18b6c89957c51b4ddfe7c0e4bbeaaa70d5380"),
    "small_query": ("experiments/workspace/rook_case4_low54_native_lp_query.py", "2ab88406370bb1f0a695fd3d191aee411e35bec0f3ced13758266811958dbefe"),
    "small_cold": ("experiments/workspace/rook_case4_low54_native_lp_replay.py", "12906b10154ea48871ee659fb4553a7aa9c5d28846d2a5e124c152d557dfb144"),
}


def digest(b):
    return hashlib.sha256(b).hexdigest()


def ref(p):
    b = p.read_bytes()
    return {"path": str(p.relative_to(ROOT)), "bytes": len(b), "sha256": digest(b)}


def main():
    objects, inputs, sources = {}, {}, {}
    for k, (path, sha) in BINDINGS.items():
        p = LOG/path
        b = p.read_bytes()
        assert digest(b) == sha
        objects[k] = json.loads(gzip.decompress(b) if path.endswith(".gz") else b)
        inputs[k] = ref(p)
    for k, (path, sha) in SOURCES.items():
        p = ROOT/path
        assert ref(p)["sha256"] == sha
        sources[k] = ref(p)

    small, cold, analysis = objects["small_specification"], objects["small_cold"], objects["small_analysis"]
    assert cold["status"] == "PASS" and cold["exact_exclusions"] == 4
    excluded = {x["whole_cover_box_index"] for x in cold["checks"]}
    low = [x for x in small["selected54_boxes"] if x["index"] not in excluded]
    assert len(low) == 50 and len(small["all191_boxes"]) == 191
    assert [x["index"] for x in low] == analysis["unexcluded_whole_cover_indices"]
    assert analysis["all_unexcluded50_numerically_optimal"]
    assert not analysis["point_rejected_by_any_pair"]
    state, preflight, numeric, point = (objects[x] for x in ("six_cut_state", "six_cut_preflight", "six_cut_numeric", "point"))
    assert len(state["cuts"]) == 6 and not state["carried_covers"]
    assert preflight["rows"] == 167121 and preflight["nonzeros"] == 10769766
    assert preflight["initial_native_rows"] == 3077 and preflight["initial_native_nonzeros"] == 28337
    assert numeric["native_calls"] == 1 and not numeric["carried_covers_after"]
    assert point["matrix_binding"] == numeric["matrix_binding"] == preflight["matrix_binding"]

    added = []
    for family in ("proved_H42_upper_five", "proved_strengthened_H"):
        rows = [x for x in small["rows"] if x["family"] == family]
        assert len(rows) == 1
        row = rows[0]
        added.append({"family": family, "lower": row["lower"], "upper": row["upper"],
            "original_terms": row["original_terms"], "terms": row["terms"],
            "source_small_row_id": row["row_id"]})
    assert [len(x["terms"]) for x in added] == [42, 44]
    for check in cold["checks"]:
        added.append({"family": "new_exact_pair_nogood", "lower": 0, "upper": 1,
            "original_terms": check["nogood"]["terms"], "certificate": check["certificate"],
            "whole_cover_box_index": check["whole_cover_box_index"]})
    assert len(added) == 6
    rows, nonzeros = 167121+6, 10769766+42+44+8

    path, expected = state["source_bindings"]["input_bindings"]["arrays"]
    archive = ROOT/path
    assert ref(archive)["sha256"] == expected
    headers = []
    with zipfile.ZipFile(archive) as z:
        for item in z.infolist():
            with z.open(item) as f:
                lead = f.read(8)
                assert lead[:6] == b"\x93NUMPY"
                n = struct.unpack("<H" if lead[6] == 1 else "<I", f.read(2 if lead[6] == 1 else 4))[0]
                header = ast.literal_eval(f.read(n).decode().strip())
            headers.append({"entry": item.filename, "dtype": header["descr"],
                "shape": list(header["shape"]), "fortran_order": header["fortran_order"],
                "compressed_bytes": item.compress_size, "uncompressed_file_bytes": item.file_size})
    assert next(x for x in headers if x["entry"] == "coefficients.npy")["shape"] == [10767292]

    sizes = {"coefficient_int64": 8*nonzeros, "indices_int32": 4*nonzeros,
        "row_pointers_int64": 8*(rows+1), "two_row_endpoints_int64": 16*rows,
        "original_ids_uint16": 2*1102}
    dense_ray_bytes = 8*rows
    pointer = struct.calcsize("P")
    copied_value_list_upper = 56+nonzeros*(pointer+sys.getsizeof(0.0))
    copied_index_list_upper = 56+nonzeros*(pointer+sys.getsizeof(1000))
    numeric_files = sorted((LOG/"rook-case4-low54-native-lp-run01/forward").glob("numeric-*.json"))
    observations = []
    for p in numeric_files:
        b = p.read_bytes()
        v = json.loads(b)
        observations.append({"raw_bytes": len(b), "gzip_bytes": len(gzip.compress(b, mtime=0)),
            "nonzero_existing_ray_entries": None if v["ray_hex"] is None else
                sum(float.fromhex(t) != 0 for t in v["ray_hex"])})
    assert len(observations) == 54

    report = {"status": "READ_ONLY_FULL50_SCOPE_ASSESSMENT_NO_MODEL_OR_QUERY",
        "source": ref(Path(__file__)), "input_bindings": inputs, "reuse_source_bindings": sources,
        "remaining_complete_case_boxes": 187, "selected_low_boxes": 50, "unselected_high_boxes": 137,
        "selected_whole_cover_indices": [x["index"] for x in low],
        "selected_states": [{"index": x["index"], "state_sha256": x["state_sha256"],
            "positive_guard": x["selected"], "free_selectors": x["state"].count("?")} for x in low],
        "proposed_matrix": {"old_rows_preserved": 167121, "old_nonzeros_preserved": 10769766,
            "new_rows": added, "rows": rows, "nonzeros": nonzeros, "variables": 1103,
            "live_original_selectors": 1102, "proved_global_zeros": 112,
            "original_coordinate_covers_covered_by_frozen_model": 178533,
            "retained_cover_rows": 164044, "artificial_t_bounds": [0, 0],
            "all_objective_coefficients": 0, "no_positive_floor_or_new_global_zero_premise": True},
        "cached_archive": ref(archive), "only_archive_headers_decompressed": headers,
        "raw_array_storage_bytes": sizes, "total_primary_integer_CSR_bytes": sum(sizes.values()),
        "additional_float64_coefficient_copy_bytes": 8*nonzeros,
        "one_dense_float64_row_ray_bytes": dense_ray_bytes,
        "fifty_dense_float64_row_ray_bytes": 50*dense_ray_bytes,
        "estimated_large_getter_list_bytes": {"values": copied_value_list_upper,
            "indices_without_small_integer_reuse": copied_index_list_upper},
        "native_RSS_not_measured_or_predicted_as_a_bound": True,
        "previous_six_cut_native_evidence": {"native_rows": 3077, "native_nonzeros": 28337,
            "native_seconds": numeric["native_seconds"], "full_pool_was_only_scanned_afterward": True,
            "not_a_full_native_matrix_timing_benchmark": True},
        "small_pilot_numeric_storage_observation": {"raw_bytes": sum(x["raw_bytes"] for x in observations),
            "gzip_bytes": sum(x["gzip_bytes"] for x in observations),
            "nonzero_ray_entries": [x["nonzero_existing_ray_entries"] for x in observations if x["nonzero_existing_ray_entries"] is not None]},
        "proposed_transport": ["Reuse the hash-bound frozen matrix loader once; check exact full-prefix equality.",
            "Append the two accepted H42 rows and four exact pair nogoods; retain every old row.",
            "Use bounded getRows/getRowsEntries NumPy blocks for full native transport auditing; verify API layout on a tiny signed control first.",
            "Reset all1103 bounds including t=0 at every branch and read them back without full-matrix Python getters.",
            "Keep complete ray and basis arrays in lossless compressed binary records; sparse original-row multipliers decide exact acceptance."],
        "proposed_resource_contract_not_authorized": {"zero_solve_preflight_seconds": 60,
            "zero_solve_preflight_owner_seconds": 90, "branches": 50,
            "calls_per_branch": 1, "requested_native_seconds_per_branch": 2,
            "cumulative_native_seconds": 120, "forward_seconds": 240, "forward_owner_seconds": 300,
            "cold_seconds": 120, "cold_owner_seconds": 150,
            "transcript_bytes": 134217728, "automatic_retries": 0, "extra_ray_solves": 0},
        "exact_acceptance": "Any signed integer combination of finite row endpoints whose full-box minimum exceeds its combined upper endpoint; t contributes0 and112 global zeros remain explicit.",
        "full_pool_feasible_or_UNKNOWN_native_branches_remain_unresolved": True,
        "matrix_builds": 0, "native_imports": 0, "optimizer_calls": 0,
        "old_trace_replays": 0, "case4_excluded": False}
    output = LOG/"rook-case4-low50-full-row-scope01.json"
    assert not output.exists()
    output.write_text(json.dumps(report, sort_keys=True, indent=2)+"\n")
    print(json.dumps({"status": report["status"], "report": ref(output),
        "rows": rows, "nonzeros": nonzeros, "primary_CSR_bytes": sum(sizes.values()),
        "dense_ray_bytes": dense_ray_bytes, "getter_list_bytes": report["estimated_large_getter_list_bytes"]}))


if __name__ == "__main__":
    main()

