#!/usr/bin/env python3
"""Prepare and probe x521=0 in the frozen prism-zero order-ten count model.

The only model change is one numerical column upper bound, from one to
zero.  Positive ordinary-count DP scales, every row, and all 25 exact
seed cuts remain unchanged.  Preparation calls no optimizer.  A run
contains exactly one IPM call of at most 120 seconds.  Numerical output
alone is never an infeasibility certificate or a graph.
"""

from __future__ import annotations

import argparse
from fractions import Fraction
import gc
import hashlib
from itertools import product
import json
import math
from pathlib import Path
import pickle
import resource
from threading import Timer
import time

import highspy
import numpy as np
from threadpoolctl import threadpool_limits

import grid_free_order10_prism_zero_moments_loop as parent


ROOT = Path(__file__).resolve().parents[2]
COUNTS = parent.counts
BASELINE = parent.baseline
PARENT_SOURCE_SHA = "a65dc6b31ebebe7bcd14398f685537f642081a7517c2e0ec94eb96246ad6e473"
PARENT_PREPARATION = ROOT / "experiments/logs/moments-and-counts/prism-zero-order10-ipm-zero-closure-preparation.json"
PARENT_PREPARATION_SHA = "fce82618e5beef610d70fadbf7b0e5d955a43496c05c3621b78ee270ff87c820"
PARENT_MODEL_SHA = "62664e9c7d7fd5abe9ca61585e10f0d3714bbd72509dca0e7a54d725cbd5943e"
POSITIVE_WITNESS = ROOT / "experiments/logs/moments-and-counts/prism-zero-order10-ipm-zero-closure-round0-rounded-counts.json"
POSITIVE_WITNESS_SHA = "3f75ad72024829c91995f3b22d50f89cd709af6b6d9d3b0806c5ee05f3097326"
PREFIX = ROOT / "experiments/logs/moments-and-counts/prism-zero-order10-x521-face"
DEFAULT_PREPARATION = PREFIX.with_name(PREFIX.name + "-preparation.json")
DEFAULT_CACHE = Path("/tmp/conway99-prism-zero-x521-face-model.pickle")


def source_sha():
    return COUNTS.digest(Path(__file__))


def relative(path):
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def compact_hash(value):
    return hashlib.sha256(json.dumps(value, separators=(",", ":"), sort_keys=True).encode()).hexdigest()


def read_parent():
    assert COUNTS.digest(Path(parent.__file__)) == PARENT_SOURCE_SHA
    assert COUNTS.digest(PARENT_PREPARATION) == PARENT_PREPARATION_SHA
    saved = json.loads(PARENT_PREPARATION.read_text())
    assert saved["source_sha256"] == PARENT_SOURCE_SHA
    assert saved["dependency_hashes"] == parent.dependencies()
    for key, name in saved["inputs"].items():
        assert COUNTS.digest(Path(name)) == saved["input_hashes"][key]
    assert saved["model"]["numerical_model_sha256"] == PARENT_MODEL_SHA
    return saved


def face_bounds(active, lower, column_upper, positive_dp_upper):
    assert 521 in active and len(set(active)) == len(active)
    position = active.index(521)
    assert lower[position] == 0 and column_upper[position] == 1
    assert positive_dp_upper[521] > 0
    result = column_upper.copy()
    result[position] = 0
    assert np.flatnonzero(result != column_upper).tolist() == [position]
    assert column_upper[position] == 1
    return result, position


def small_controls():
    active = [1, 521, 549]
    lower, column_upper = np.zeros(3), np.ones(3)
    dp = [1] * 550
    dp[1], dp[521], dp[549] = 13, 19404, 9
    before = dp[:]
    changed, position = face_bounds(active, lower, column_upper, dp)
    assert position == 1 and dp == before
    assert lower.tolist() == [0, 0, 0] and column_upper.tolist() == [1, 1, 1]
    assert changed.tolist() == [1, 0, 1]
    checked, on_face = 0, 0
    # Use exact fractions to check x_j=U_j*y_j before and after changing
    # the domain; all row evaluations and positive U_j remain identical.
    for values in product([Fraction(i, 4) for i in range(5)], repeat=3):
        ordinary = [dp[j] * value for j, value in zip(active, values)]
        numerical_bound_holds = all(lo <= value <= hi for lo, value, hi in zip(lower, values, changed))
        assert numerical_bound_holds == (ordinary[1] == 0)
        row_in_ordinary = 7 - 2 * ordinary[0] + 3 * ordinary[1] + 5 * ordinary[2]
        row_in_scaled = 7 - 26 * values[0] + 58212 * values[1] + 45 * values[2]
        assert row_in_ordinary == row_in_scaled
        checked += 1
        on_face += numerical_bound_holds
    assert (checked, on_face) == (125, 25)
    return {"exact_scaled_assignments": checked, "assignments_on_face": on_face,
            "input_bounds_not_mutated": True, "positive_DP_scales_unchanged": True,
            "all_row_evaluations_unchanged": True, "optimizer_called": False}


def point_check(bundle, point, require_face):
    zeros = bundle["metadata"]["prism_zero_core_coordinates"]
    required = zeros + ([521] if require_face else [])
    assert len(point) == 550 and point[0] == 1
    assert all(type(x) is int for x in point)
    assert all(point[j] == 0 for j in required)
    exact = COUNTS.exact_candidate(bundle["data"], bundle["scale"], bundle["raw"],
                                   point, bundle["upper"], False)
    cut_values = [sum(a * x for a, x in zip(cut["coefficients"], point)) for cut in bundle["seed"]]
    assert len(cut_values) == 25
    exact.update(exact_held_cut_values=cut_values,
                 negative_held_cuts=sum(value < 0 for value in cut_values),
                 held_cut_coefficients_sha256=parent.vector_hash(bundle["seed"]),
                 required_zero_coordinates=sorted(required),
                 required_zeros_hold=True, x521_fixed_to_zero=require_face,
                 PSD_feasibility_certified=False,
                 graph_constructed=False)
    exact["exact_count_and_25_cut_witness"] = "induced_counts" in exact and not exact["negative_held_cuts"]
    return exact


def assemble():
    saved = read_parent()
    inputs = {key: Path(value) for key, value in saved["inputs"].items()}
    data, scale, raw, metadata, numeric, seed, scanner, bridge = parent.model(**inputs)
    assert metadata == saved["model"] and seed == saved["initial_cuts"]
    matrix, rhs, lower, column_upper, fixed, upper = numeric
    assert matrix.format == "csc" and matrix.shape == (47645, 547) and matrix.nnz == 5430251
    assert BASELINE.numerical_model_hash(matrix, rhs, lower, column_upper) == PARENT_MODEL_SHA
    active = metadata["active_core_coordinates"]
    dp_sha = compact_hash(upper)
    changed, position = face_bounds(active, lower, column_upper, upper)
    assert position == 518 and upper[521] == 19404
    assert sum(column_upper > 0) == 491 and sum(changed > 0) == 490
    assert 521 not in metadata["prism_zero_core_coordinates"]
    assert compact_hash(upper) == dp_sha
    restored = changed.copy()
    restored[position] = 1
    assert BASELINE.numerical_model_hash(matrix, rhs, lower, restored) == PARENT_MODEL_SHA
    new_sha = BASELINE.numerical_model_hash(matrix, rhs, lower, changed)
    report = {"rows": 47645, "stored_columns": 547, "free_columns": 490, "nonzeros": 5430251,
              "parent_numerical_model_sha256": PARENT_MODEL_SHA,
              "numerical_model_sha256": new_sha, "only_changed_column_index": position,
              "only_changed_ordinary_coordinate": 521,
              "changed_numerical_bound": {"old_lower": 0, "old_upper": 1, "new_lower": 0, "new_upper": 0},
              "ordinary_coordinate_DP_scale": upper[521], "all_DP_scales_sha256": dp_sha,
              "positive_DP_bounds_and_scalings_unchanged": True,
              "all_rows_and_rhs_unchanged": True, "exact_seed_cuts": 25,
              "seed_coefficients_sha256": parent.vector_hash(seed),
              "active_core_coordinates": active,
              "required_zero_coordinates": sorted(metadata["prism_zero_core_coordinates"] + [521]),
              "restoring_one_bound_reproduces_parent_hash": True,
              "additional_motif_inequality_added": False,
              "additional_zero_propagation_added": False,
              "fixed_order_nine_point": False,
              "objective": "zero; pure feasibility"}
    bundle = {"source_sha256": source_sha(), "data": data, "scale": scale, "raw": raw,
              "metadata": metadata, "matrix": matrix, "rhs": rhs, "lower": lower,
              "column_upper": changed, "fixed": fixed, "upper": upper, "seed": seed,
              "model_report": report, "bridge": bridge}
    del scanner
    gc.collect()
    return saved, bundle


def prepare(output, cache):
    started = time.monotonic()
    saved, bundle = assemble()
    assert COUNTS.digest(POSITIVE_WITNESS) == POSITIVE_WITNESS_SHA
    old = json.loads(POSITIVE_WITNESS.read_text())
    control = point_check(bundle, old["rounded_core_values"], require_face=False)
    assert control["exact_count_and_25_cut_witness"]
    assert control["induced_counts"] == old["induced_counts"]
    assert old["rounded_core_values"][521] == 116
    positive = {"path": relative(POSITIVE_WITNESS), "sha256": POSITIVE_WITNESS_SHA,
                "exact_induced_counts_checked": len(control["induced_counts"]),
                "original_equations_checked": control["original_equations_checked"],
                "held_cuts_checked": 25, "minimum_cut_value": min(control["exact_held_cut_values"]),
                "x521": 116, "satisfies_parent_model": True, "satisfies_new_face": False}
    h, options = BASELINE.supported_options(120)
    cache.parent.mkdir(parents=True, exist_ok=True)
    pending = cache.with_name(cache.name + ".pending")
    with pending.open("wb") as stream:
        pickle.dump(bundle, stream, protocol=5)
    pending.replace(cache)
    result = {"status": "x521-zero count-face model prepared; no optimization run",
              "source_sha256": source_sha(),
              "parent_source_sha256": PARENT_SOURCE_SHA,
              "parent_preparation_path": relative(PARENT_PREPARATION),
              "parent_preparation_sha256": PARENT_PREPARATION_SHA,
              "dependency_hashes": saved["dependency_hashes"],
              "parent_input_hashes": saved["input_hashes"],
              "model": bundle["model_report"], "small_controls": small_controls(),
              "parent_positive_control": positive,
              "cache": {"path": str(cache), "sha256": COUNTS.digest(cache), "bytes": cache.stat().st_size},
              "highs_version": h.version(), "supported_options": options,
              "maximum_solver_calls": 1, "maximum_solver_seconds": 120,
              "infeasibility_requires_exact_certificate": True,
              "feasibility_requires_exact_count_replay": True,
              "scope": "globally prism-free count relaxation with x521=0; not a graph search",
              "optimizer_called": False,
              "preparation_seconds": time.monotonic() - started,
              "peak_process_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    COUNTS.save(output, result)
    print(json.dumps({key: value for key, value in result.items() if key not in ("model", "dependency_hashes", "parent_input_hashes")}, indent=2), flush=True)
    print(json.dumps({key: value for key, value in bundle["model_report"].items()
                      if key not in ("active_core_coordinates", "required_zero_coordinates")}, indent=2), flush=True)
    return result


def load_prepared(preparation, rebuild=False):
    saved = json.loads(preparation.read_text())
    parent_saved = read_parent()
    assert saved["source_sha256"] == source_sha()
    assert saved["parent_source_sha256"] == PARENT_SOURCE_SHA
    assert saved["parent_preparation_sha256"] == PARENT_PREPARATION_SHA
    assert saved["dependency_hashes"] == parent_saved["dependency_hashes"]
    assert saved["parent_input_hashes"] == parent_saved["input_hashes"]
    assert saved["small_controls"] == small_controls()
    if rebuild:
        _, bundle = assemble()
    else:
        cache = Path(saved["cache"]["path"])
        assert cache.stat().st_size == saved["cache"]["bytes"]
        assert COUNTS.digest(cache) == saved["cache"]["sha256"]
        with cache.open("rb") as stream:
            bundle = pickle.load(stream)
    assert bundle["source_sha256"] == source_sha() and bundle["model_report"] == saved["model"]
    actual = BASELINE.numerical_model_hash(bundle["matrix"], bundle["rhs"], bundle["lower"], bundle["column_upper"])
    assert actual == saved["model"]["numerical_model_sha256"]
    return saved, bundle


def run(preparation, output, prefix, seconds):
    assert 0 < seconds <= 120
    assert not output.exists(), "refusing to overwrite an existing bounded run"
    saved, bundle = load_prepared(preparation)
    matrix, rhs = bundle["matrix"], bundle["rhs"]
    h, options = BASELINE.supported_options(seconds)
    assert h.version() == saved["highs_version"]
    h.HandleUserInterrupt = True
    lp = highspy.HighsLp()
    lp.num_col_, lp.num_row_ = matrix.shape[1], matrix.shape[0]
    lp.col_cost_, lp.col_lower_, lp.col_upper_ = np.zeros(matrix.shape[1]), bundle["lower"], bundle["column_upper"]
    lp.row_lower_, lp.row_upper_ = np.full(matrix.shape[0], -highspy.kHighsInf), rhs
    lp.a_matrix_.format_ = highspy.MatrixFormat.kColwise
    lp.a_matrix_.start_, lp.a_matrix_.index_, lp.a_matrix_.value_ = matrix.indptr, matrix.indices, matrix.data
    assert h.passModel(lp) == highspy.HighsStatus.kOk
    result = {"status": "running one bounded x521-zero count-face IPM probe",
              "source_sha256": source_sha(), "preparation_sha256": COUNTS.digest(preparation),
              "numerical_model_sha256": saved["model"]["numerical_model_sha256"],
              "solver_calls": 1, "solver_seconds_limit": seconds, "options": options,
              "exact_infeasibility_certificate": False, "exact_count_witness": False,
              "PSD_feasibility_certified": False, "graph_constructed": False}
    COUNTS.save(output, result)
    print(json.dumps({"starting_single_IPM_call": True, "seconds": seconds,
                      "numerical_model_sha256": result["numerical_model_sha256"]}), flush=True)
    started = time.monotonic()
    timer = Timer(seconds, h.cancelSolve)
    timer.start()
    try:
        run_status = h.run()
    except BaseException as error:
        result.update(status="stopped on solver exception; unresolved",
                      exception_type=type(error).__name__, exception=str(error),
                      solver_seconds=time.monotonic() - started)
        COUNTS.save(output, result)
        raise
    finally:
        timer.cancel()
    status = h.getModelStatus()
    result.update(numerical_status=str(status), highs_run_status=str(run_status),
                  solver_seconds=time.monotonic() - started)
    returned = BASELINE.returned_data(h)
    returned.update(source_sha256=source_sha(), preparation_sha256=COUNTS.digest(preparation),
                    numerical_model_sha256=result["numerical_model_sha256"], numerical_status=str(status))
    raw_path = prefix.with_name(prefix.name + "-solver-data.json.gz")
    parent.raw_save(raw_path, returned)
    result.update(returned_data_path=relative(raw_path), returned_data_sha256=COUNTS.digest(raw_path),
                  returned_value_valid=returned["value_valid"], returned_dual_valid=returned["dual_valid"],
                  solver_info=returned["info"], dual_ray_extraction_performed=False)
    result["status"] = "numerical solver returned; exact verification pending"
    COUNTS.save(output, result)
    values = returned["column_values"]
    active = bundle["metadata"]["active_core_coordinates"]
    if returned["value_valid"] and len(values) == len(active) and all(type(v) is float and math.isfinite(v) for v in values):
        ordinary = [value * bundle["upper"][j] for j, value in zip(active, values)]
        proposal = {"status": "numerical proposal; exact feasibility not yet certified",
                    "source_sha256": source_sha(), "preparation_sha256": COUNTS.digest(preparation),
                    "numerical_model_sha256": result["numerical_model_sha256"],
                    "numerical_status": str(status), "required_zero_coordinates": saved["model"]["required_zero_coordinates"],
                    "real_proposal": {"active_coordinates": active, "scaled_values": values,
                                      "ordinary_core_values": ordinary, "exact_real_feasibility_certified": False}}
        proposal_path = prefix.with_name(prefix.name + "-proposal.json")
        COUNTS.save(proposal_path, proposal)
        result.update(proposal_path=relative(proposal_path), proposal_sha256=COUNTS.digest(proposal_path))
    if status == highspy.HighsModelStatus.kOptimal:
        assert "proposal_path" in result
        point = [0] * 550
        point[0] = 1
        for coordinate, value in zip(active, ordinary):
            point[coordinate] = min(bundle["upper"][coordinate], max(0, int(round(value))))
        for coordinate in saved["model"]["required_zero_coordinates"]:
            point[coordinate] = 0
        checked = point_check(bundle, point, require_face=True)
        checked.update(source_sha256=source_sha(), preparation_sha256=COUNTS.digest(preparation),
                       numerical_model_sha256=result["numerical_model_sha256"])
        checked_path = prefix.with_name(prefix.name + "-rounded-counts.json")
        COUNTS.save(checked_path, checked)
        result.update(rounded_counts_path=relative(checked_path), rounded_counts_sha256=COUNTS.digest(checked_path),
                      rounded_count_status=checked["status"], rounded_negative_held_cuts=checked["negative_held_cuts"],
                      exact_count_witness=checked["exact_count_and_25_cut_witness"])
        result["status"] = ("exact integral x521-zero count and 25-cut witness verified"
                            if result["exact_count_witness"] else
                            "numerical optimum only; rounded point failed exact verification")
    elif status == highspy.HighsModelStatus.kInfeasible:
        result["status"] = "numerical infeasibility indication only; exact dual proof required"
    else:
        result["status"] = "stopped on numerical solver status; unresolved"
    result["peak_process_rss_kib"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    COUNTS.save(output, result)
    print(json.dumps(result, indent=2), flush=True)
    return result


def replay_witness(preparation, witness, rebuild):
    saved, bundle = load_prepared(preparation, rebuild=rebuild)
    original = json.loads(witness.read_text())
    assert original["source_sha256"] == source_sha()
    assert original["preparation_sha256"] == COUNTS.digest(preparation)
    assert original["numerical_model_sha256"] == saved["model"]["numerical_model_sha256"]
    checked = point_check(bundle, original["rounded_core_values"], require_face=True)
    for key, value in checked.items():
        assert original[key] == value, key
    assert checked["exact_count_and_25_cut_witness"]
    report = {"status": "exact x521-zero count-face witness replay PASS",
              "source_sha256": source_sha(), "witness_sha256": COUNTS.digest(witness),
              "full_model_rebuilt": rebuild, "induced_counts_checked": len(checked["induced_counts"]),
              "original_equations_checked": checked["original_equations_checked"],
              "exact_seed_cuts_checked": 25, "required_zero_coordinates": 59,
              "optimizer_called": False, "PSD_feasibility_certified": False, "graph_constructed": False}
    print(json.dumps(report, indent=2), flush=True)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prep = commands.add_parser("prepare")
    prep.add_argument("--output", type=Path, default=DEFAULT_PREPARATION)
    prep.add_argument("--cache", type=Path, default=DEFAULT_CACHE)
    solve = commands.add_parser("run")
    solve.add_argument("--preparation", type=Path, default=DEFAULT_PREPARATION)
    solve.add_argument("--output", type=Path, default=PREFIX.with_name(PREFIX.name + "-result.json"))
    solve.add_argument("--prefix", type=Path, default=PREFIX)
    solve.add_argument("--seconds", type=float, default=120)
    replay = commands.add_parser("replay-witness")
    replay.add_argument("--preparation", type=Path, default=DEFAULT_PREPARATION)
    replay.add_argument("--witness", type=Path, default=PREFIX.with_name(PREFIX.name + "-rounded-counts.json"))
    replay.add_argument("--rebuild", action="store_true")
    args = parser.parse_args()
    with threadpool_limits(limits=1):
        if args.command == "prepare":
            prepare(args.output, args.cache)
        elif args.command == "run":
            run(args.preparation, args.output, args.prefix, args.seconds)
        else:
            replay_witness(args.preparation, args.witness, args.rebuild)


if __name__ == "__main__":
    main()
