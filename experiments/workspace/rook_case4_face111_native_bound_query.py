"""One bounded warm-basis native LP scan with exact certificate acceptance.

The fixed objective order contains72 exhaustive parity patterns followed
by1071 other singleton selectors. Limits:60 seconds for the child,2 per
native call,65 seconds hard parent deadline. No accepted row is appended
during this batch. Only exact box-corrected certificates prove exclusions.
"""
import argparse
from collections import Counter
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time
from threading import Timer, Event

import rook_case4_face111_native_bounds as exact

ROOT = Path(__file__).resolve().parents[2]
BASE = "experiments/logs/grids-and-triangles/"
MODEL = BASE+"rook-case4-face111-native-bounds-model01.json"
MODEL_SHA = "a174fde38a359f61498a0d9508beb2364ec9209f2771e9a7529a3675774008ad"
EXACT_SHA = "df6a043f5a1f9f958536ff6c5b847b3b659c7701e609a30049b24582939ecc60"
SECONDS, CALL_SECONDS, HARD_SECONDS = 60.0, 2.0, 65.0


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def save(path, value):
    temporary = path.with_name(path.name+".tmp")
    temporary.write_text(json.dumps(value, indent=2)+"\n")
    os.replace(temporary, path)


def load():
    assert sha(Path(exact.__file__).read_bytes()) == EXACT_SHA
    raw = (ROOT/MODEL).read_bytes(); assert sha(raw) == MODEL_SHA
    model = json.loads(raw)
    assert model["source_sha256"] == EXACT_SHA
    assert (model["variables"], model["row_count"], model["nonzeros"], model["objective_count"]) == (1103, 1963, 25767, 1143)
    assert model["partition"]["complete_Boolean_cover"]
    return model


def native(model):
    import highspy
    import numpy as np
    from scipy.sparse import csr_matrix, csc_matrix
    starts, indices, values = [0], [], []
    for row in model["rows"]:
        indices.extend(j for j, c in row["terms"])
        values.extend(c for j, c in row["terms"])
        starts.append(len(indices))
    matrix = csr_matrix((np.asarray(values, dtype=np.float64), np.asarray(indices, dtype=np.int32), np.asarray(starts, dtype=np.int32)), shape=(model["row_count"], model["variables"]))
    lower = np.asarray([row["lower"] for row in model["rows"]], dtype=np.float64)
    upper = np.asarray([row["upper"] for row in model["rows"]], dtype=np.float64)
    h = highspy.Highs()
    h.HandleUserInterrupt = True
    options = {"output_flag": False, "solver": "simplex", "threads": 1, "random_seed": 0,
               "presolve": "on", "simplex_strategy": 1, "time_limit": CALL_SECONDS}
    for key, value in options.items():
        assert h.setOptionValue(key, value) == highspy.HighsStatus.kOk
    lp = highspy.HighsLp()
    lp.num_col_, lp.num_row_ = model["variables"], model["row_count"]
    lp.col_cost_ = np.zeros(model["variables"])
    lp.col_lower_, lp.col_upper_ = np.zeros(model["variables"]), np.ones(model["variables"])
    lp.row_lower_, lp.row_upper_ = lower, upper
    lp.a_matrix_.format_ = highspy.MatrixFormat.kRowwise
    lp.a_matrix_.start_, lp.a_matrix_.index_, lp.a_matrix_.value_ = starts, indices, values
    assert h.passModel(lp) == highspy.HighsStatus.kOk
    received = h.getLp()
    a = received.a_matrix_
    if a.format_ == highspy.MatrixFormat.kRowwise:
        transported = csr_matrix((a.value_, a.index_, a.start_), shape=matrix.shape)
    else:
        assert a.format_ == highspy.MatrixFormat.kColwise
        transported = csc_matrix((a.value_, a.index_, a.start_), shape=matrix.shape).tocsr()
    assert (transported != matrix).nnz == 0 and transported.nnz == matrix.nnz == 25767
    assert np.array_equal(received.row_lower_, lower) and np.array_equal(received.row_upper_, upper)
    assert np.array_equal(received.col_lower_, lp.col_lower_) and np.array_equal(received.col_upper_, lp.col_upper_)
    assert np.array_equal(received.col_cost_, lp.col_cost_)
    return h, matrix, lower, upper, {"native_version": h.version(), "native_all25767_coefficients_exact": True,
                                  "all_bounds_exact": True, "options": options, "optimizer_calls": 0}


def child(directory):
    started = time.monotonic(); model = load()
    h, matrix, lower, upper, audit = native(model)
    import highspy
    import numpy as np
    save(directory/"child-initialization.json", {**audit, "seconds": time.monotonic()-started})
    completed, accepted, previous = 0, 0, []
    numerical_statuses = Counter(); stop = "COMPLETE"
    with (directory/"attempts.jsonl").open("x") as attempts, (directory/"certificates.jsonl").open("x") as certificates:
        for objective_id, objective in enumerate(model["objectives"]):
            remaining = SECONDS-(time.monotonic()-started)
            if remaining <= 0:
                stop = "TIME_LIMIT_PARTIAL"; break
            for j in previous:
                assert h.changeColCost(j, 0.0) == highspy.HighsStatus.kOk
            for j in objective["reduced_columns"]:
                assert h.changeColCost(j, -1.0) == highspy.HighsStatus.kOk
            previous = objective["reduced_columns"]
            allowance = min(CALL_SECONDS, remaining)
            prior_runtime = max(0.0, float(h.getRunTime()))
            assert math.isfinite(prior_runtime)
            assert h.setOptionValue("time_limit", prior_runtime+allowance) == highspy.HighsStatus.kOk
            interrupted = Event()
            def interrupt_call():
                interrupted.set()
                h.cancelSolve()
            timer = Timer(allowance, interrupt_call); timer.daemon = True
            before = time.monotonic(); timer.start()
            try:
                native_status = h.run()
            finally:
                timer.cancel(); timer.join()
            elapsed = time.monotonic()-before
            status = h.modelStatusToString(h.getModelStatus()); numerical_statuses[status] += 1
            solution = h.getSolution()
            record = {"objective_id": objective_id, "original_columns": objective["original_columns"],
                      "required_value": objective["required_value"], "native_status": str(native_status),
                      "numerical_model_status": status, "native_seconds": elapsed,
                      "row_duals_available": bool(solution.dual_valid), "accepted_certificates": 0,
                      "per_call_interrupt_fired": interrupted.is_set()}
            if solution.value_valid:
                record["numerical_objective_hex"] = float(sum(solution.col_value[j] for j in objective["reduced_columns"])).hex()
            if solution.dual_valid:
                u = -np.asarray(solution.row_dual, dtype=np.float64)
                assert len(u) == model["row_count"]
                if np.isfinite(u).all():
                    residual = -matrix.T@u
                    residual[objective["reduced_columns"]] += 1.0
                    bound_value = float(np.dot(u, np.where(u >= 0, upper, lower))+np.maximum(residual, 0).sum())
                    record["numerical_box_upper_hex"] = bound_value.hex()
                    if bound_value < objective["required_value"]-1e-7:
                        record["proposal_row_multipliers_hex"] = [[i, float(v).hex()] for i, v in enumerate(u) if v]
                        for denominator in exact.QUANTA:
                            multipliers = [int(round(float(v)*denominator)) for v in u]
                            numerator, _, _ = exact.bound(model["rows"], model["variables"], objective["reduced_columns"], multipliers, denominator)
                            if numerator < denominator*objective["required_value"]:
                                proof = exact.certificate(model, objective_id, multipliers, denominator)
                                exact.verify(model, proof)
                                certificates.write(json.dumps(proof, sort_keys=True)+"\n"); certificates.flush()
                                record["accepted_certificates"] = 1; accepted += 1
                                break
            attempts.write(json.dumps(record, sort_keys=True)+"\n"); attempts.flush(); completed += 1
            if record["accepted_certificates"] and proof["kind"] == "NATIVE_BOX_CONTRADICTION":
                stop = "EXACT_CONTRADICTION"; break
            if interrupted.is_set() or h.getModelStatus() != highspy.HighsModelStatus.kOptimal:
                stop = "INTERRUPTED_OR_NONOPTIMAL_PARTIAL"; break
        save(directory/"child-result.json", {"status": stop, "completed_objectives": completed,
             "accepted_certificates": accepted, "numerical_statuses": dict(numerical_statuses),
             "seconds": time.monotonic()-started, "existing_dual_ray_requested": False,
             "rows_appended_during_batch": 0, "automatic_retry": False})


def replay(directory):
    model = load(); attempts_path = directory/"attempts.jsonl"; proofs_path = directory/"certificates.jsonl"
    def complete_records(path):
        raw = path.read_bytes() if path.exists() else b""
        parts = raw.split(b"\n")
        complete = [json.loads(line) for line in parts[:-1] if line]
        return complete, len(parts[-1])
    attempts, attempt_tail = complete_records(attempts_path)
    proofs, proof_tail = complete_records(proofs_path)
    assert [item["objective_id"] for item in attempts] == list(range(len(attempts)))
    ids = [proof["objective_id"] for proof in proofs]
    assert len(ids) == len(set(ids))
    for record in attempts:
        obj = model["objectives"][record["objective_id"]]
        assert record["original_columns"] == obj["original_columns"] and record["required_value"] == obj["required_value"]
    for proof in proofs:
        exact.verify(model, proof)
        assert proof["objective_id"] <= len(attempts)
    excluded = sorted(i for i in ids if i < 72)
    contradictory = any(proof["kind"] == "NATIVE_BOX_CONTRADICTION" for proof in proofs) or excluded == list(range(72))
    return {"status": "EXACT_CASE4_CONTRADICTION" if contradictory else "EXACT_NEW_RESTRICTIONS" if proofs else "UNKNOWN",
            "model_sha256": MODEL_SHA, "exact_helper_sha256": EXACT_SHA,
            "completed_objectives": len(attempts), "accepted_certificates": len(proofs),
            "excluded_partition_patterns": excluded, "complete72_pattern_cover_excluded": excluded == list(range(72)),
            "new_zero_original_columns": sorted({p["objective_original_columns"][0] for p in proofs if p["kind"] == "BOOLEAN_COORDINATE_ZERO"}),
            "new_forbidden_original_pairs": sorted([p["objective_original_columns"] for p in proofs if p["kind"] == "FORBIDDEN_BOOLEAN_PAIR"]),
            "attempts_sha256": sha(attempts_path.read_bytes()) if attempts_path.exists() else None,
            "certificates_sha256": sha(proofs_path.read_bytes()) if proofs_path.exists() else None,
            "unaccepted_incomplete_tail_bytes": {"attempts": attempt_tail, "certificates": proof_tail},
            "optimizer_called_by_replay": False, "exact_feasible_point_claimed": False,
            "unrestricted_conway_problem_solved": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "run", "child", "replay"))
    parser.add_argument("--output", type=Path)
    parser.add_argument("--directory", type=Path)
    args = parser.parse_args(); started = time.monotonic()
    if args.mode == "child":
        child(args.directory); return
    assert args.output and not args.output.exists()
    if args.mode == "prepare":
        model = load(); h, matrix, lower, upper, audit = native(model)
        report = {**audit, "status": "PASS: exact native transport and bounded query preparation",
                  "source_sha256": sha(Path(__file__).read_bytes()), "exact_source_sha256": EXACT_SHA,
                  "model_sha256": MODEL_SHA, "objectives": model["objective_count"], "partition_patterns": 72,
                  "child_seconds": SECONDS, "per_native_call_seconds": CALL_SECONDS, "hard_parent_seconds": HARD_SECONDS,
                  "quanta": exact.QUANTA, "exact_controls": exact.controls(), "seconds": time.monotonic()-started}
    elif args.mode == "run":
        assert args.directory and not args.directory.exists()
        args.directory.mkdir()
        command = [sys.executable, str(Path(__file__).resolve()), "child", "--directory", str(args.directory.resolve())]
        with (args.directory/"stdout.log").open("w") as out, (args.directory/"stderr.log").open("w") as err:
            process = subprocess.Popen(command, stdout=out, stderr=err)
            timeout = False
            try:
                code = process.wait(timeout=HARD_SECONDS)
            except subprocess.TimeoutExpired:
                timeout = True; process.kill(); code = process.wait()
        report = replay(args.directory)
        report.update(source_sha256=sha(Path(__file__).read_bytes()), owned_child_return_code=code,
                      hard_timeout=timeout, seconds=time.monotonic()-started)
    else:
        report = replay(args.directory)
        report.update(source_sha256=sha(Path(__file__).read_bytes()), cold_replay=True, seconds=time.monotonic()-started)
    save(args.output, report); print(json.dumps(report, indent=2), flush=True)


if __name__ == "__main__":
    main()
