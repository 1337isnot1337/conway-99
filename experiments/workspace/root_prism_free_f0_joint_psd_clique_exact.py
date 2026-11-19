"""Exact finite-box acceptance for the21-PSD/258-clique append model.

The frozen helper supplies unchanged integer/Fraction arithmetic. Loading
checks the complete parent matrix/scaling prefix and every appended row.
The bound cold record independently reconstructs all new witness rows.
Only an already-existing numerical ray is processed; no optimizer runs.
"""
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import time

MODEL_SHA256 = "e5aee717846cf7bb1b2e6072438d49b38627119fed65408d2159212f876ec21d"
MODEL_FILE_SHA256 = "43fff7283308cc2ed1be0936fae4b4f7b264c5961f6e6a4c9a81d123836e4f69"
MATRIX_SHA256 = "607b3a6b1939b70538cbaf5e5d6e395b746745bf50ced097f12d81035723a234"
SCALES_SHA256 = "ab1b87424535ab03a530119b0ac5f306c5f9b2b8e038d999ffcca2dc183ebf1a"
BUILDER_SHA256 = "5bef59a3831030047349a0f2d80b36fffb6aa99e8bfdc1f074d4b776143b459b"
COLD_SHA256 = "da7dce5e6485a183b3e028ca72a5be5336137d3d7091d660af3187a6f4169bdc"
PARENT_HELPER_SHA256 = "1ed513c9164282de0a70c197f1a9fbfcf6f9e964e3506b3af521e2f7ea800c1b"
PARENT_MODEL_SHA256 = "7bc4682e3df009761c55d0740a30a0629d45e894807f79e3337fc1de4fa1aff3"
PARENT_FILE_SHA256 = "ad046fc05a4247a081b3cabb16693682fa5539ff557dd7b599f3c3a63e7303dd"
PARENT_MATRIX_SHA256 = "24da97cfaf7bdb6e73efcdf9b248d70f30e04443dada5a2c923ab112f10bc812"
PARENT_SCALES_SHA256 = "0fcd8328b5ead5c51dfba7a624a69b748f38b19c894fd32c310352789e422247"

_path = Path(__file__).with_name("root_prism_free_f0_schur_motif_exact.py")
assert hashlib.sha256(_path.read_bytes()).hexdigest() == PARENT_HELPER_SHA256
_spec = importlib.util.spec_from_file_location("f0_joint_clique_bound_parent_exact", _path)
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
    assert object_hash(model) == MODEL_SHA256 and model["source_sha256"] == BUILDER_SHA256
    assert digest(Path(__file__).with_name("root_prism_free_f0_joint_psd_clique_model.py")) == BUILDER_SHA256
    matrix, scales = model["matrix"], model["numerical_row_scales"]
    assert object_hash(matrix) == model["matrix_sha256"] == MATRIX_SHA256
    assert object_hash(scales) == model["numerical_row_scales_sha256"] == SCALES_SHA256
    logs = Path(__file__).resolve().parents[1] / "logs/root-prism-free"
    cold_path = logs / "f0-joint-psd-clique-model01-cold-replay.json"
    assert digest(cold_path) == COLD_SHA256
    cold = json.loads(cold_path.read_text())
    assert cold["status"] == "PASS:21PSD+258clique overlay replay"
    assert cold["source_sha256"] == BUILDER_SHA256
    assert cold["model_sha256"] == MODEL_SHA256 and cold["model_file_sha256"] == MODEL_FILE_SHA256
    assert cold["matrix_sha256"] == MATRIX_SHA256 and cold["numerical_row_scales_sha256"] == SCALES_SHA256
    assert cold["checks"] == model["checks"] and cold["counts"] == model["counts"]
    old_path = logs / "f0-schur-path-model03.json.gz"
    assert digest(old_path) == PARENT_FILE_SHA256
    old = json.loads(gzip.decompress(old_path.read_bytes()))
    assert object_hash(old) == model["parent"]["model_sha256"] == PARENT_MODEL_SHA256
    assert object_hash(old["matrix"]) == PARENT_MATRIX_SHA256
    assert object_hash(old["numerical_row_scales"]) == PARENT_SCALES_SHA256
    assert matrix["equalities"] == old["matrix"]["equalities"]
    assert matrix["inequalities"][:21629] == old["matrix"]["inequalities"]
    assert scales[:27764] == old["numerical_row_scales"]
    assert matrix["variables"] == 15200 and matrix["lower"] == 0 and matrix["upper"] == 1
    assert (len(matrix["equalities"]), len(matrix["inequalities"])) == (6135, 21908)
    rows = matrix["equalities"] + matrix["inequalities"]
    assert len(rows) == len(scales) == 28043
    assert sum(len(row["terms"]) for row in rows) == 1086559
    assert len(model["append_certificates"]) == 279
    assert len(model["PSD_proofs"]) == 21 and len(model["clique_proofs"]) == 258
    for i, record in enumerate(model["append_certificates"]):
        position = 21629 + i
        assert record["new_row_appended"] is True
        assert record["mathematical_inequality_index"] == position
        assert record["combined_row_index"] == 6135 + position
        row = matrix["inequalities"][position]
        assert object_hash({"terms": row["terms"], "rhs": row["rhs"]}) == record["row_sha256"]
        assert record["numerical_row_scale"] == scales[6135 + position]
        group, index = ("PSD_proofs", i) if i < 21 else ("clique_proofs", i-21)
        proof = model[group][index]
        assert record["input_index"] == proof["input_index"] == index
        assert proof["row"] == {"terms": row["terms"], "rhs": row["rhs"]}
        if i < 21:
            assert proof["exact_literal_evaluation"]["violated"] is True
            assert proof["exact_projected_evaluation"]["violated"] is True
            assert proof["scale"] == record["numerical_row_scale"]
        else:
            assert row["rhs"] == 0 and len(proof["all12_literal_transport_indices"]) == 12
    for row, scale in zip(rows, scales):
        indices = [j for j, c in row["terms"]]
        assert indices == sorted(set(indices)) and all(type(j) is int and 0 <= j < 15200 for j in indices)
        for value in [row["rhs"]] + [c for j, c in row["terms"]]:
            exact_scaled(value, scale)
    assert model["scope"]["whole_PSD_cone_enforced"] is False
    assert model["scope"]["all4416_selector_predicates_and_original_RLT_rows_retained"] is True
    assert model["scope"]["complete258_core_pair_edge_clique_rows_added"] is True
    assert model["scope"]["root128_redundant_greedy_rows_added"] is False
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
    assert len(ray_hex) == 28043 and "existing_dual_ray_hex" not in numerical
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
