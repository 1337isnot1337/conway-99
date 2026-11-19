"""Finite-box Farkas acceptance for the frozen Schur/prism model.

This query stage accepts only an exact infeasibility certificate recovered
from a dual ray that already existed after the one numerical call. It does
not reconstruct a primal point or basis, and it calls no optimizer.
"""
from fractions import Fraction
import gzip
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import time

MODEL_SHA256 = "92d6a65bcfffd3f5c6f2518b5fe4d1ebefb874eb6e72e15229a690ee9198ae19"
MODEL_FILE_SHA256 = "5f039eb2864f838cf15df987ca7eebef1600eb4085afb3083538dc5514fdb889"
MATRIX_SHA256 = "74a83420ac5585a0fa840092aa64d5b7c6732a0f42a32a10adb6af4df504c364"
SCALES_SHA256 = "6874a86bbb22f1ad383de3622374776774d42b56ea31e39d6e1022a57babf4ef"
BUILDER_SHA256 = "077e371e399346ab513ac41a717b181a3e11285ccda38600f12586f61b4375f5"
PARENT_FILE_SHA256 = "3302546078e2277c8ce30d032110bb527c6a986a74f76fc1f78451bf4da4b804"
PARENT_MATRIX_SHA256 = "b49a35a0c19e43a70bc8957f0fe09e03f17113ff67caab40a4d4fa63307cca01"
FARKAS_HELPER_SHA256 = "3986ac84e6d891a0dc362db05f7785ae4294fe58a31a6241f0b63721de5868cd"

_path = Path(__file__).with_name("root_prism_free_f0_second_moments_exact.py")
assert hashlib.sha256(_path.read_bytes()).hexdigest() == FARKAS_HELPER_SHA256
_spec = importlib.util.spec_from_file_location("f0_schur_motif_bound_Farkas", _path)
base = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(base)
digest, save, integer, tick = base.digest, base.save, base.integer, base.tick
evaluate_farkas, numerical_farkas = base.evaluate_farkas, base.numerical_farkas


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode()


def object_hash(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def exact_scaled(value, scale):
    assert type(value) is int and abs(value) < 2**53
    assert type(scale) is int and scale > 0 and scale & (scale - 1) == 0
    converted = float(value) / scale
    assert Fraction(converted) == Fraction(value, scale)
    return converted


def pullback_ray(hex_values, scales):
    assert len(hex_values) == len(scales)
    result = []
    for h, scale in zip(hex_values, scales):
        assert isinstance(h, str) and type(scale) is int and scale > 0 and scale & (scale - 1) == 0
        value = float.fromhex(h)
        assert math.isfinite(value)
        result.append(Fraction(value) / scale)
    return result


def load_model(path):
    raw = Path(path).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == MODEL_FILE_SHA256
    model = json.loads(gzip.decompress(raw))
    assert object_hash(model) == MODEL_SHA256
    assert model["source_sha256"] == BUILDER_SHA256
    assert digest(Path(__file__).with_name("root_prism_free_f0_schur_motif_model.py")) == BUILDER_SHA256
    matrix = model["matrix"]
    assert object_hash(matrix) == model["matrix_sha256"] == MATRIX_SHA256
    scales = model["numerical_row_scales"]
    assert object_hash(scales) == model["numerical_row_scales_sha256"] == SCALES_SHA256
    parent_path = Path(__file__).resolve().parents[1] / "logs/root-prism-free/f0-selector-psd-model01.json.gz"
    assert digest(parent_path) == PARENT_FILE_SHA256
    parent = json.loads(gzip.decompress(parent_path.read_bytes()))
    assert object_hash(parent["matrix"]) == PARENT_MATRIX_SHA256
    assert matrix["equalities"][:5973] == parent["matrix"]["equalities"]
    assert matrix["inequalities"][:15751] == parent["matrix"]["inequalities"]
    assert matrix["variables"] == 15200 and matrix["lower"] == 0 and matrix["upper"] == 1
    assert (len(matrix["equalities"]), len(matrix["inequalities"])) == (6135, 16505)
    assert scales[:5973] == parent["numerical_row_scales"][:5973]
    assert scales[5973:6135] == [1] * 162
    assert scales[6135:6135 + 15751] == parent["numerical_row_scales"][5973:]
    rows = matrix["equalities"] + matrix["inequalities"]
    assert len(rows) == len(scales) == 22640
    assert sum(len(row["terms"]) for row in rows) == 889906
    assert (len(model["zero_certificates"]), len(model["Schur_cut_certificates"]),
            len(model["three_exterior_certificates"])) == (162, 39, 715)
    for record in model["zero_certificates"]:
        row = matrix["equalities"][record["mathematical_equality_index"]]
        assert row["terms"] == [[record["reduced_variable"], 1]] and row["rhs"] == 0
    for record in model["Schur_cut_certificates"] + model["three_exterior_certificates"]:
        position = record["mathematical_inequality_index"]
        assert record["combined_row_index"] == 6135 + position
        row = matrix["inequalities"][position]
        assert object_hash({"terms": row["terms"], "rhs": row["rhs"]}) == record["row_sha256"]
    for row, scale in zip(rows, scales):
        indices = [j for j, c in row["terms"]]
        assert indices == sorted(set(indices)) and all(type(j) is int and 0 <= j < 15200 for j in indices)
        for value in [row["rhs"]] + [c for j, c in row["terms"]]:
            exact_scaled(value, scale)
    assert model["scope"]["whole_PSD_cone_enforced"] is False
    assert model["scope"]["all4416_selector_predicates_and_original_RLT_rows_retained"] is True
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
    assert len(ray_hex) == 22640 and "existing_dual_ray_hex" not in numerical
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


def controls():
    toy = {"variables": 2, "lower": 0, "upper": 1,
           "equalities": [{"terms": [[0, 1], [1, 1]], "rhs": 1}],
           "inequalities": [{"terms": [[0, 1]], "rhs": 1}]}
    count = 0
    for lam in range(-4, 5):
        for mu in range(5):
            check = evaluate_farkas(toy, {"equality_multipliers": [lam], "inequality_multipliers": [mu]})
            assert not check["strict_infeasibility"]
            count += 1
    bad = {"variables": 1, "lower": 0, "upper": 1,
           "equalities": [{"terms": [[0, 1]], "rhs": 2}], "inequalities": []}
    assert evaluate_farkas(bad, {"equality_multipliers": [-1], "inequality_multipliers": []})["gap"] == "-1"
    scaling = 0
    for scale in (1, 2, 2**10, 2**30):
        for value in (-2**31 + 1, -7, -1, 0, 1, 7, 2**31 - 1):
            assert Fraction(exact_scaled(value, scale)) == Fraction(value, scale)
            for multiplier in (Fraction(-7, 8), Fraction(0), Fraction(5, 4)):
                pulled = pullback_ray([float(multiplier).hex()], [scale])[0]
                assert pulled * value == multiplier * Fraction(value, scale)
                scaling += 1
    tiny = float.fromhex("0x0.0000000000001p-1022")
    assert pullback_ray([tiny.hex()], [2**30])[0] > 0 and tiny / 2**30 == 0
    return {"status": "PASS: finite-box signs and exact scaled-ray pullback",
            "feasible_Farkas_controls": count, "strict_infeasible_controls": 1,
            "scaling_controls": scaling, "subnormal_pullback_preserved_exactly": True,
            "optimizer_calls": 0, "primal_or_basis_reconstruction": False}
