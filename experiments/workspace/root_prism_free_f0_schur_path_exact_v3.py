"""Exact finite-box acceptance for the complete path-prism overlay.

The parent helper supplies unchanged arithmetic. The new loader verifies the
entire old matrix and scale prefixes plus all 5,124 appended path rows.
Only an already-existing numerical ray is reconstructed; no optimizer runs.
"""
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import time

MODEL_SHA256 = "7bc4682e3df009761c55d0740a30a0629d45e894807f79e3337fc1de4fa1aff3"
MODEL_FILE_SHA256 = "ad046fc05a4247a081b3cabb16693682fa5539ff557dd7b599f3c3a63e7303dd"
MATRIX_SHA256 = "24da97cfaf7bdb6e73efcdf9b248d70f30e04443dada5a2c923ab112f10bc812"
SCALES_SHA256 = "0fcd8328b5ead5c51dfba7a624a69b748f38b19c894fd32c310352789e422247"
BUILDER_SHA256 = "f76c35fb3e39704e88a250938e3be1d64ad07fba197ea0405fb11ba4aeac74bd"
PARENT_HELPER_SHA256 = "1ed513c9164282de0a70c197f1a9fbfcf6f9e964e3506b3af521e2f7ea800c1b"

_path = Path(__file__).with_name("root_prism_free_f0_schur_motif_exact.py")
assert hashlib.sha256(_path.read_bytes()).hexdigest() == PARENT_HELPER_SHA256
_spec = importlib.util.spec_from_file_location("f0_path_bound_parent_exact", _path)
parent = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(parent)
digest, save, integer, tick = parent.digest, parent.save, parent.integer, parent.tick
canonical, object_hash = parent.canonical, parent.object_hash
evaluate_farkas, numerical_farkas = parent.evaluate_farkas, parent.numerical_farkas
exact_scaled, pullback_ray, controls = parent.exact_scaled, parent.pullback_ray, parent.controls


def load_model(path):
    raw = Path(path).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == MODEL_FILE_SHA256
    model = json.loads(gzip.decompress(raw))
    assert object_hash(model) == MODEL_SHA256
    assert model["source_sha256"] == BUILDER_SHA256
    assert digest(Path(__file__).with_name("root_prism_free_f0_schur_path_model_v3.py")) == BUILDER_SHA256
    matrix = model["matrix"]
    assert object_hash(matrix) == model["matrix_sha256"] == MATRIX_SHA256
    scales = model["numerical_row_scales"]
    assert object_hash(scales) == model["numerical_row_scales_sha256"] == SCALES_SHA256
    logs = Path(__file__).resolve().parents[1] / "logs/root-prism-free"
    old = parent.load_model(logs / "f0-schur-motif-model01.json.gz")
    assert model["parent"]["model_sha256"] == parent.MODEL_SHA256
    assert model["parent"]["prepared_but_unrun"] is True
    assert matrix["equalities"] == old["matrix"]["equalities"]
    assert matrix["inequalities"][:16505] == old["matrix"]["inequalities"]
    assert scales[:22640] == old["numerical_row_scales"]
    assert matrix["variables"] == 15200 and matrix["lower"] == 0 and matrix["upper"] == 1
    assert (len(matrix["equalities"]), len(matrix["inequalities"])) == (6135, 21629)
    rows = matrix["equalities"] + matrix["inequalities"]
    assert len(rows) == len(scales) == 27764
    assert sum(len(row["terms"]) for row in rows) == 905276
    assert len(model["path_cut_certificates"]) == 5124
    assert model["path_proof"]["file_sha256"] == "d7ce1862d52cb4c9011efe73deb438db2b4e33a3fade1d5b803569005f2d7886"
    for i, record in enumerate(model["path_cut_certificates"]):
        assert record["input_row_index"] == i and record["new_row_appended"] is True
        position = record["mathematical_inequality_index"]
        assert position == 16505 + i and record["combined_row_index"] == 6135 + position
        row = matrix["inequalities"][position]
        assert object_hash({"terms": row["terms"], "rhs": row["rhs"]}) == record["row_sha256"]
        assert row["rhs"] == 0 and all(0 <= j < 5847 for j, c in row["terms"])
        assert sorted(c for j, c in row["terms"]) in ([-1, 1, 1], [-1, 2])
        assert len(record["literal_witness_transports"]) == 12
        assert record["numerical_row_scale"] == scales[6135 + position]
    assert sum(len(row["terms"]) == 2 for row in matrix["inequalities"][16505:]) == 2
    for row, scale in zip(rows, scales):
        indices = [j for j, c in row["terms"]]
        assert indices == sorted(set(indices)) and all(type(j) is int and 0 <= j < 15200 for j in indices)
        for value in [row["rhs"]] + [c for j, c in row["terms"]]:
            exact_scaled(value, scale)
    assert model["scope"]["whole_PSD_cone_enforced"] is False
    assert model["scope"]["all4416_selector_predicates_and_original_RLT_rows_retained"] is True
    assert model["scope"]["complete_two_edge_exterior_prism_family_added"] is True
    return model


def exact_phase(model_path, numerical_path, output_path, seconds):
    started = time.monotonic()
    deadline = started + seconds
    model = load_model(model_path)
    numerical = json.loads(Path(numerical_path).read_text())
    assert numerical["model_sha256"] == MODEL_SHA256
    assert numerical["numerical_row_scales_sha256"] == SCALES_SHA256
    assert numerical["optimizer_calls"] == 1
    assert numerical["numerical_method"] == "ipm" and numerical["run_crossover"] == "off"
    assert numerical["existing_ray_query"] is True
    ray_hex = numerical["existing_scaled_dual_ray_hex"]
    assert len(ray_hex) == 27764 and "existing_dual_ray_hex" not in numerical
    result = {"kind": "unresolved", "status": "UNKNOWN: no exact Farkas certificate reconstructed",
              "model_sha256": MODEL_SHA256, "helper_source_sha256": digest(__file__),
              "numerical_file_sha256": digest(numerical_path), "requested_seconds": seconds,
              "numerical_row_scales_sha256": SCALES_SHA256,
              "attempts": [], "optimizer_calls": 0, "primal_recovery_attempted": False,
              "basis_recovery_attempted": False, "whole_PSD_cone_enforced": False}
    save(output_path, result)
    try:
        ray = pullback_ray(ray_hex, model["numerical_row_scales"])
        tick(deadline)
        accepted = numerical_farkas(model["matrix"], ray, deadline, result["attempts"])
        if accepted is not None:
            certificate, check = accepted
            assert check["strict_infeasibility"]
            result.update(kind="farkas", status="EXACT_LINEAR_FARKAS_FOUND: independent cold replay pending",
                          certificate=certificate, exact_check=check)
    except (ArithmeticError, TimeoutError) as error:
        result["status"] = "UNKNOWN: bounded exact ray reconstruction stopped"
        result["reconstruction_stop"] = str(error)
    except Exception as error:
        result.update(status="ERROR: exact phase stopped", error_type=type(error).__name__,
                      error_message=str(error))
        raise
    finally:
        result["elapsed_seconds"] = time.monotonic() - started
        result["cooperative_overrun_seconds"] = max(0, result["elapsed_seconds"] - seconds)
        save(output_path, result)
    return result
