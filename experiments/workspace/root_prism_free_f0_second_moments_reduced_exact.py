"""Exact adapter for the equivalent reduced F0 second-moment model.

Unchanged arithmetic is imported from the hash-bound original helper.
Accepted reduced points are expanded and checked against every original row.
No optimizer is imported or called.
"""
from fractions import Fraction
import gzip
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import time

MODEL_SHA256 = "684b3a646a95d8404bf7b46a3ab170ef88b82e54fdb02aec3a34b8f9613847ae"
MODEL_FILE_SHA256 = "73a50b431ac69ad57e10cff9aabe5c0b7d69ee075e95710b461f62b33fe2bbcf"
MATRIX_SHA256 = "5e417221ed814a5a0dcb03e31820871113bcc0eb8af2856dd2ac493958d16f39"
ORIGINAL_HELPER_SHA256 = "3986ac84e6d891a0dc362db05f7785ae4294fe58a31a6241f0b63721de5868cd"
REDUCTION_SOURCE_SHA256 = "1f9549100f5bad7476fc21d1152e6637cac7f448987e57d7652204d5e8df279c"

_original_path = Path(__file__).with_name("root_prism_free_f0_second_moments_exact.py")
assert hashlib.sha256(_original_path.read_bytes()).hexdigest() == ORIGINAL_HELPER_SHA256
_spec = importlib.util.spec_from_file_location("f0_original_second_moment_exact", _original_path)
original = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(original)

digest, save, integer, tick = original.digest, original.save, original.integer, original.tick
common_point, quotient_check = original.common_point, original.quotient_check
evaluate_farkas, numerical_farkas = original.evaluate_farkas, original.numerical_farkas
recover_active_face = original.recover_active_face
MAX_POINT_BITS = original.MAX_POINT_BITS
ACTIVE_TOLERANCE = original.ACTIVE_TOLERANCE


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode()


def object_hash(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def load_model(path):
    raw = Path(path).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == MODEL_FILE_SHA256
    model = json.loads(gzip.decompress(raw))
    assert object_hash(model) == MODEL_SHA256
    assert model["source_sha256"] == REDUCTION_SOURCE_SHA256
    reduction = Path(__file__).with_name("root_prism_free_f0_second_moments_reduced.py")
    assert digest(reduction) == REDUCTION_SOURCE_SHA256
    assert object_hash(model["matrix"]) == MATRIX_SHA256
    matrix = model["matrix"]
    assert matrix["variables"] == 15200 and matrix["lower"] == 0 and matrix["upper"] == 1
    assert len(matrix["equalities"]) == 5973 and len(matrix["inequalities"]) == 15719
    assert sum(len(r["terms"]) for r in matrix["equalities"]+matrix["inequalities"]) == 183702
    assert model["scope"]["mathematically_equivalent_to_original_linear_model"] is True
    assert model["scope"]["new_inequalities_or_selector_assumptions_added"] is False
    assert model["scope"]["PSD_enforced"] is False
    for row in matrix["equalities"]+matrix["inequalities"]:
        assert type(row["rhs"]) is int and abs(row["rhs"]) < 2**53
        indices = [j for j, c in row["terms"]]
        assert indices == sorted(set(indices))
        assert all(type(j) is int and 0 <= j < 15200 and type(c) is int and abs(c) < 2**53
                   for j, c in row["terms"])
    parent_path = Path(__file__).resolve().parents[1]/"logs/root-prism-free/f0-second-moments-preparation02.json.gz"
    parent = original.load_model(parent_path)
    fixed = model["fixed_zero_original_variables"]
    assert len(fixed) == 389
    for variable, row in fixed:
        assert parent["matrix"]["equalities"][row]["terms"] == [[variable, 1]]
        assert parent["matrix"]["equalities"][row]["rhs"] == 0
    assert model["kept_original_variables"] == sorted(set(range(15589))-{j for j, row in fixed})
    # Only this in-memory object receives its separately hash-bound parent.
    model["_original"] = parent
    return model


def zero_embed(point, kept, size):
    numerator = list(map(integer, point["numerators"]))
    denominator = integer(point["denominator"])
    assert denominator > 0 and len(numerator) == len(kept)
    assert kept == sorted(set(kept)) and all(0 <= j < size for j in kept)
    result = [0]*size
    for j, value in zip(kept, numerator):
        result[j] = value
    return {"denominator": str(denominator), "numerators": list(map(str, result))}


def full_point_check(model, point):
    quotient = quotient_check(model["matrix"], point)
    if not quotient["passed"]:
        return {"passed": False, "quotient": quotient}
    restored = zero_embed(point, model["kept_original_variables"], 15589)
    full = original.full_point_check(model["_original"], restored)
    assert full["passed"], "reduced/original exact equivalence discrepancy"
    return {"passed": True, "quotient": quotient, "original_full_check": full,
            "full_rows_checked": 650350, "full_variable_bounds_checked": 183834,
            "restored_zero_coordinates": 389,
            "PSD_conditions_enforced_or_certified": False}

def recover_point(model, numeric, deadline, attempts, progress_path):
    matrix = model["matrix"]
    assert len(numeric) == matrix["variables"] and all(math.isfinite(v) for v in numeric)
    for maximum_denominator in (1000, 10**6, 10**9):
        tick(deadline)
        try:
            values = [Fraction(0) if abs(v) <= ACTIVE_TOLERANCE else Fraction(1) if abs(v - 1) <= ACTIVE_TOLERANCE
                      else Fraction(v).limit_denominator(maximum_denominator) for v in numeric]
            point = common_point(values)
            check = full_point_check(model, point)
            attempts.append({"method": "direct rational proposal", "maximum_denominator": maximum_denominator,
                             "quotient": check["quotient"]})
            if check["passed"]:
                return point, check, {"method": "direct rational proposal", "maximum_denominator": maximum_denominator}
        except ArithmeticError as error:
            attempts.append({"method": "direct rational proposal", "maximum_denominator": maximum_denominator, "rejected": str(error)})
    tick(deadline)
    point, metadata = recover_active_face(matrix, numeric, deadline, progress_path)
    check = full_point_check(model, point)
    attempts.append({"method": metadata["method"], "quotient": check["quotient"]})
    if check["passed"]:
        return point, check, metadata
    return None

def exact_phase(model_path, numerical_path, output_path, seconds):
    started = time.monotonic()
    deadline = started + seconds
    model = load_model(model_path)
    numerical = json.loads(Path(numerical_path).read_text())
    assert numerical["model_sha256"] == MODEL_SHA256
    result = {"kind": "unresolved", "status": "UNKNOWN: no exact certificate reconstructed",
              "model_sha256": MODEL_SHA256, "helper_source_sha256": digest(__file__),
              "numerical_file_sha256": digest(numerical_path), "requested_seconds": seconds,
              "attempts": [], "optimizer_calls": 0, "PSD_conditions_enforced_or_certified": False}
    save(output_path, result)
    try:
        ray = [float.fromhex(v) for v in numerical.get("existing_dual_ray_hex", [])]
        values = [float.fromhex(v) for v in numerical.get("col_value_hex", [])]
        phases = ("ray", "point") if "Infeasible" in numerical.get("numerical_status", "") else ("point", "ray")
        for phase in phases:
            tick(deadline)
            if phase == "point" and len(values) == model["matrix"]["variables"]:
                accepted = recover_point(model, values, deadline, result["attempts"],
                                         Path(output_path).with_name("exact-progress.json"))
                if accepted is not None:
                    point, check, method = accepted
                    result.update(kind="point", status="EXACT_LINEAR_POINT_FOUND: independent full replay pending",
                                  point=point, exact_check=check, reconstruction=method)
                    break
            if phase == "ray" and ray:
                accepted = numerical_farkas(model["matrix"], ray, deadline, result["attempts"])
                if accepted is not None:
                    certificate, check = accepted
                    result.update(kind="farkas", status="EXACT_LINEAR_FARKAS_FOUND: independent full replay pending",
                                  certificate=certificate, exact_check=check)
                    break
    except (ArithmeticError, TimeoutError) as error:
        result["status"] = "UNKNOWN: bounded exact reconstruction stopped"
        result["reconstruction_stop"] = str(error)
    except Exception as error:
        result["status"] = "ERROR: exact phase stopped"
        result["error_type"], result["error_message"] = type(error).__name__, str(error)
        raise
    finally:
        result["elapsed_seconds"] = time.monotonic() - started
        result["cooperative_overrun_seconds"] = max(0, result["elapsed_seconds"] - seconds)
        save(output_path, result)
    return result


def controls():
    result = original.controls()
    point = {"denominator": "3", "numerators": ["1", "2"]}
    restored = zero_embed(point, [0, 2], 3)
    assert restored == {"denominator": "3", "numerators": ["1", "0", "2"]}
    toy = {"variables": 3, "equalities": [
        {"terms": [[0, 1], [2, 1]], "rhs": 1},
        {"terms": [[1, 1]], "rhs": 0}], "inequalities": [
        {"terms": [[0, 1], [2, -1]], "rhs": 0}]}
    assert quotient_check(toy, restored)["passed"]
    bad = {"denominator": "3", "numerators": ["1", "1", "2"]}
    assert not quotient_check(toy, bad)["passed"]
    result["zero_embedding_control"] = True
    result["wrong_zero_coordinate_rejected"] = True
    result["unchanged_arithmetic_helper_sha256"] = ORIGINAL_HELPER_SHA256
    result["original_full_point_acceptance_retained"] = True
    return result

