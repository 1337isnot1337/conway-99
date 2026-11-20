"""Exact acceptance for the reduced F0 model plus32 selector-PSD directions.

The numerical matrix uses positive power-of-two row scales. Existing numerical
ray multipliers are divided by those scales as Fractions before reconstruction.
All accepted points retain every original literal check plus32 full480 squares.
"""
from fractions import Fraction
import gzip
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import time

MODEL_SHA256 = "d098a4b84405823aa38e9d2def7b675c6166507f7350937f1dc0f65af7274dcd"
MODEL_FILE_SHA256 = "3302546078e2277c8ce30d032110bb527c6a986a74f76fc1f78451bf4da4b804"
MATRIX_SHA256 = "b49a35a0c19e43a70bc8957f0fe09e03f17113ff67caab40a4d4fa63307cca01"
SCALES_SHA256 = "7d9c593cbf3e2ab127bc37575029acf236edc21018e9e5a6e5d8199f7b5ebc57"
BUILDER_SHA256 = "1c21e5eb27db84dba33f782c7755e18433b2ce087328b87d89f74a0698090a8b"
PARENT_HELPER_SHA256 = "0ade9c2f04415b325e7f217023dd072abaf4b8cdf60cd9fe07a2cfe93e416536"

_path = Path(__file__).with_name("root_prism_free_f0_second_moments_reduced_exact.py")
assert hashlib.sha256(_path.read_bytes()).hexdigest() == PARENT_HELPER_SHA256
_spec = importlib.util.spec_from_file_location("f0_bound_reduced_exact", _path)
parent = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(parent)
digest, save, integer, tick = parent.digest, parent.save, parent.integer, parent.tick
common_point, quotient_check = parent.common_point, parent.quotient_check
evaluate_farkas, numerical_farkas = parent.evaluate_farkas, parent.numerical_farkas
recover_active_face = parent.recover_active_face
MAX_POINT_BITS, ACTIVE_TOLERANCE = parent.MAX_POINT_BITS, parent.ACTIVE_TOLERANCE


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode()


def object_hash(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def exact_scaled(value, scale):
    assert type(value) is int and abs(value) < 2**53
    assert type(scale) is int and scale > 0 and scale & (scale-1) == 0
    f = float(value)/scale
    numerator, denominator = f.as_integer_ratio()
    assert numerator*scale == value*denominator
    return f


def pullback_ray(hex_values, scales):
    assert len(hex_values) == len(scales)
    result = []
    for h, scale in zip(hex_values, scales):
        assert type(h) is str and type(scale) is int and scale > 0 and scale & (scale-1) == 0
        value = float.fromhex(h)
        assert math.isfinite(value)
        # Do not divide in binary64: a valid small multiplier could underflow.
        result.append(Fraction(value)/scale)
    return result


def load_model(path):
    raw = Path(path).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == MODEL_FILE_SHA256
    model = json.loads(gzip.decompress(raw))
    assert object_hash(model) == MODEL_SHA256
    assert model["source_sha256"] == BUILDER_SHA256
    assert digest(Path(__file__).with_name("root_prism_free_f0_selector_psd_model.py")) == BUILDER_SHA256
    assert object_hash(model["matrix"]) == MATRIX_SHA256
    scales = model["numerical_row_scales"]
    assert object_hash(scales) == model["numerical_row_scales_sha256"] == SCALES_SHA256
    logs = Path(__file__).resolve().parents[1]/"logs/root-prism-free"
    reduced = parent.load_model(logs/"f0-second-moments-reduced-model.json.gz")
    matrix = model["matrix"]
    assert matrix["variables"] == 15200 and matrix["lower"] == 0 and matrix["upper"] == 1
    assert matrix["equalities"] == reduced["matrix"]["equalities"]
    assert matrix["inequalities"][:15719] == reduced["matrix"]["inequalities"]
    assert len(matrix["equalities"]) == 5973 and len(matrix["inequalities"]) == 15751
    rows = matrix["equalities"]+matrix["inequalities"]
    assert len(rows) == len(scales) == 21724 and scales[:21692] == [1]*21692
    assert sum(len(r["terms"]) for r in rows) == 380052
    assert len(model["cut_certificates"]) == 32
    for i, certificate in enumerate(model["cut_certificates"]):
        assert certificate["scan_cut"] == i
        assert certificate["mathematical_inequality_index"] == 15719+i
        assert certificate["combined_row_index"] == 21692+i
        assert certificate["numerical_positive_scale"] == scales[21692+i]
        assert certificate["zero_coordinates_substituted"] == 389
        assert type(certificate["positive_divisor"]) is int and certificate["positive_divisor"] > 0
        v = certificate["vector"]
        assert len(v) == 481 and all(type(a) is int for a in v) and any(v)
        assert max(map(abs, v)) <= 4096 and v[0] == 0
        row = rows[21692+i]
        assert row["family"] == "augmented selector PSD" and row["PSD_cut"] == i
        assert row["rhs"] == 0
        largest = max(abs(c) for j, c in row["terms"])
        assert scales[21692+i] == 1 << (largest.bit_length()-1)
    for row, scale in zip(rows, scales):
        indices = [j for j, c in row["terms"]]
        assert indices == sorted(set(indices))
        assert all(type(j) is int and 0 <= j < 15200 for j in indices)
        for value in [row["rhs"]]+[c for j, c in row["terms"]]:
            exact_scaled(value, scale)
    assert model["scope"]["whole_PSD_cone_enforced"] is False
    assert model["scope"]["exact_necessary_PSD_directions"] == 32
    assert model["scope"]["all_original_linear_rows_retained"] is True
    assert model["scope"]["all4416_selector_cuts_retained"] is True
    model["_reduced"] = reduced
    return model


def full_psd_directions(model, point):
    den = integer(point["denominator"])
    reduced_values = list(map(integer, point["numerators"]))
    assert den > 0 and len(reduced_values) == 15200
    reduced = model["_reduced"]
    full = reduced["_original"]
    restored = [0]*15589
    for j, value in zip(reduced["kept_original_variables"], reduced_values):
        restored[j] = value
    x = [None]*480
    for orbit, members in enumerate(full["selector_orbits"]):
        for a in members:
            assert x[a] is None
            x[a] = restored[orbit]
    assert None not in x
    pairs = [(a, b) for a in range(480) for b in range(a+1, 480)]
    assert len(pairs) == len(full["pair_to_orbit"]) == 114960
    z = [restored[5847+o] for o in full["pair_to_orbit"]]
    checked = []
    for i, certificate in enumerate(model["cut_certificates"]):
        c, v = certificate["vector"][0], certificate["vector"][1:]
        quadratic = c*c*den
        quadratic += sum((v[a]*v[a]+2*c*v[a])*x[a] for a in range(480))
        quadratic += 2*sum(v[a]*v[b]*value for (a, b), value in zip(pairs, z))
        row = model["matrix"]["inequalities"][15719+i]
        residual = sum(k*reduced_values[j] for j, k in row["terms"])-row["rhs"]*den
        assert quadratic == -certificate["positive_divisor"]*residual
        checked.append(str(quadratic))
    return {"passed": all(integer(q) >= 0 for q in checked),
            "full480_quadratic_numerators": checked, "denominator": str(den),
            "directions_checked": 32, "whole_PSD_cone_checked": False}


def full_point_check(model, point):
    quotient = quotient_check(model["matrix"], point)
    if not quotient["passed"]:
        return {"passed": False, "quotient": quotient}
    full = parent.full_point_check(model["_reduced"], point)
    assert full["passed"], "unchanged original full point acceptance discrepancy"
    psd = full_psd_directions(model, point)
    assert psd["passed"], "literal/quotient PSD-direction discrepancy"
    return {"passed": True, "quotient": quotient, "original_full_check": full,
            "full_rows_checked": 650350, "full_variable_bounds_checked": 183834,
            "additional_full480_PSD_directions": psd,
            "whole_PSD_cone_enforced_or_certified": False}


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
    assert numerical["numerical_row_scales_sha256"] == SCALES_SHA256
    assert "existing_dual_ray_hex" not in numerical
    result = {"kind": "unresolved", "status": "UNKNOWN: no exact certificate reconstructed",
              "model_sha256": MODEL_SHA256, "helper_source_sha256": digest(__file__),
              "numerical_file_sha256": digest(numerical_path), "requested_seconds": seconds,
              "numerical_row_scales_sha256": SCALES_SHA256,
              "ray_pullback": "Each saved scaled multiplier is divided by its positive power-of-two row scale as an exact Fraction.",
              "attempts": [], "optimizer_calls": 0, "certified_PSD_directions_enforced": 32,
              "whole_PSD_cone_enforced_or_certified": False}
    save(output_path, result)
    try:
        ray_hex = numerical.get("existing_scaled_dual_ray_hex", [])
        ray = pullback_ray(ray_hex, model["numerical_row_scales"]) if ray_hex else []
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
    result = parent.controls()
    count = 0
    for scale in (1, 2, 64, 2**26):
        for value in range(-17, 18):
            f = exact_scaled(value, scale)
            assert Fraction(f) == Fraction(value, scale)
            for lam in (Fraction(-7, 8), Fraction(0), Fraction(5, 4)):
                pulled = pullback_ray([float(lam).hex()], [scale])[0]
                assert pulled == lam/scale
                assert pulled*value == lam*Fraction(value, scale)
                count += 1
    tiny = float.fromhex("0x0.0000000000001p-1022")
    assert tiny > 0 and tiny/(2**26) == 0
    assert pullback_ray([tiny.hex()], [2**26]) == [Fraction(1, 2**1100)]
    # A one-row infeasible box has the same strict certificate after pullback.
    matrix = {"variables": 1, "equalities": [],
              "inequalities": [{"terms": [[0, -8]], "rhs": -16}]}
    pulled = pullback_ray([float(8).hex()], [8])
    assert pulled == [1]
    certificate = {"equality_multipliers": [], "inequality_multipliers": [str(int(pulled[0]))]}
    assert evaluate_farkas(matrix, certificate)["strict_infeasibility"]
    result.update(exact_scaled_coefficient_and_dual_controls=count,
                  underflow_avoided_by_fraction_pullback=True,
                  scaled_strict_box_control=True, certified_PSD_directions=32,
                  whole_PSD_cone_enforced=False, production_optimizer_calls=0)
    return result

