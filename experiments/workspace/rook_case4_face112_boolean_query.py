"""One gated proof-capable binary query on the exact112-zero case4 face.

No query runs during preparation. The complete old formula is retained
with proved112-face units, cardinalities and a pair constraint. SAT is only an incidence witness. UNSAT
requires direct DRAT followed by a cold full-formula/input/DRAT replay.
Timeout, memory/proof-size refusal, or unchecked proof remains unresolved.
"""
import argparse
import json
import os
from pathlib import Path
import resource
import subprocess
import sys
import tempfile
import time

for _thread_variable in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[_thread_variable] = "1"

import pysat.solvers as solver_api
import pysolvers
import complement_rook_35core_case0004_coordinate_cover_cadical as prior
import rook_case4_face112_boolean_overlay as overlay

ROOT = overlay.ROOT
OVERLAY_SHA = "6e96e8712b1af1bf355de8b69ac2dac358b73e27f8e68c9d500037ab7117d150"
PRIOR_SHA = "1921f71964795d819e0369c9679dc1526df97c29bb1920a932c7ca449ba3de25"
OLD_PREPARATION = ROOT/"experiments/logs/grids-and-triangles/complement-rook-35core-case0004-coordinate-cover-cadical-preparation.json"
OLD_PREPARATION_SHA = "e7a4185a300a48edbe01d7103da8e765dab1ad9653e2678992d3f1c4e986d731"
BACKEND = "cadical300"
LIMITS = {"production_queries": 1, "automatic_retries": 0,
          "owned_child_wall_seconds_including_imports_bootstrap_solve_and_export": 180,
          "direct_DRAT_seconds": 60, "cold_DRAT_seconds": 60,
          "checker_timeout_grace_seconds": 5, "tiny_DRAT_seconds": 10,
          "child_address_space_bytes": 3 << 30, "child_single_file_hard_bytes": 256 << 20,
          "accepted_binary_proof_bytes": 64 << 20, "accepted_text_proof_bytes": 128 << 20,
          "retained_CNF_bytes": 128 << 20, "retained_proof_bytes": 128 << 20,
          "retained_distinct_input_clauses": 250000}
digest, normalized = overlay.digest, prior.normalized


def portable(path):
    path = Path(path).resolve()
    return str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)


def location(path):
    p = Path(path)
    return p if p.is_absolute() else ROOT/p


def save(path, value):
    path = Path(path)
    temporary = path.with_name(path.name+".tmp")
    temporary.write_text(json.dumps(value, indent=2)+"\n")
    temporary.replace(path)


def source_hashes():
    assert digest(overlay.__file__) == OVERLAY_SHA
    assert digest(prior.__file__) == PRIOR_SHA
    answer = overlay.bindings()
    answer[Path(prior.__file__).name] = PRIOR_SHA
    answer[Path(__file__).name] = digest(__file__)
    return dict(sorted(answer.items()))


def resource_caps():
    """Hard OS limits, also applied to the separate proof checker process."""
    resource.setrlimit(resource.RLIMIT_AS, (LIMITS["child_address_space_bytes"],)*2)
    resource.setrlimit(resource.RLIMIT_FSIZE, (LIMITS["child_single_file_hard_bytes"],)*2)


def checker_binding(path):
    path = Path(path).resolve()
    assert path.is_file() and os.access(path, os.X_OK)
    return {"path": str(path), "sha256": digest(path), "bytes": path.stat().st_size}


def run_checker(checker, cnf, proof, log, seconds, retained=None, trimmed=None):
    assert seconds in (LIMITS["tiny_DRAT_seconds"], LIMITS["direct_DRAT_seconds"], LIMITS["cold_DRAT_seconds"])
    assert not log.exists()
    command = [str(checker), str(cnf), str(proof), "-t", str(seconds), "-w"]
    if retained is not None:
        assert trimmed is not None and not retained.exists() and not trimmed.exists()
        command += ["-c", str(retained), "-l", str(trimmed)]
    started = time.monotonic()
    with log.open("wb") as stream:
        try:
            done = subprocess.run(command, stdout=stream, stderr=subprocess.STDOUT,
                                  preexec_fn=resource_caps,
                                  timeout=seconds+LIMITS["checker_timeout_grace_seconds"], check=False)
            code, timed_out = done.returncode, False
        except subprocess.TimeoutExpired:
            code, timed_out = None, True
    raw = log.read_bytes()
    passed = not timed_out and code == 0 and b"s VERIFIED" in raw
    if retained is not None and passed:
        passed = (retained.is_file() and trimmed.is_file()
                  and retained.stat().st_size <= LIMITS["retained_CNF_bytes"]
                  and trimmed.stat().st_size <= LIMITS["retained_proof_bytes"])
    return {"passed": passed, "returncode": code, "timed_out": timed_out,
            "requested_seconds": seconds, "elapsed_seconds": time.monotonic()-started,
            "log": portable(log), "log_sha256": digest(log), "checker_sha256": digest(checker)}


def retained_inclusion(full_path, retained_path):
    assert retained_path.stat().st_size <= LIMITS["retained_CNF_bytes"]
    needed = set(); line_count = 0
    for clause in prior.previous.original.read_clauses(retained_path):
        needed.add(prior.previous.clause_key(clause)); line_count += 1
        assert len(needed) <= LIMITS["retained_distinct_input_clauses"]
    found = set(); groups = [set() for _ in range(6)]
    boundaries = [218863, 218893, 261071, 439604, overlay.OLD_CLAUSES]
    for i, clause in enumerate(prior.previous.read_full_clauses(full_path, overlay.VARIABLES, overlay.NEW_CLAUSES)):
        key = prior.previous.clause_key(clause)
        if key in needed:
            groups[sum(i >= b for b in boundaries)].add(key); found.add(key)
    assert found == needed
    previous = set(); attributed = {}
    for name, group in zip(("original_incidence", "Gram_conflicts", "weighted_rows", "coordinate_covers", "previous85_units", "new112_face_constraints"), groups):
        attributed[name] = len(group-previous); previous.update(group)
    return {"all_retained_inputs_in_full_formula": True, "retained_input_clause_lines": line_count,
            "retained_distinct_input_clauses": len(needed), "first_available_family_counts": attributed,
            "old_complete_formula_only": needed <= set.union(*groups[:5])}


def prepare(model_directory, model_cold, output, control_directory, checker):
    assert not output.exists() and not control_directory.exists()
    control_directory.mkdir(parents=True)
    sources = source_hashes()
    model = overlay.checked_model(model_directory, True)
    cold = json.loads(model_cold.read_bytes())
    assert cold["status"].startswith("PASS: full original CNF")
    assert cold["model_sha256"] == digest(model_directory/"model.json")
    assert cold["CNF_sha256"] == model["formula"]["CNF_sha256"]
    assert cold["source_hashes"] == overlay.bindings()
    assert digest(OLD_PREPARATION) == OLD_PREPARATION_SHA
    accepted, _ = prior.checked_preparation(OLD_PREPARATION, True, False)
    assert accepted["backend"] == BACKEND
    runtime = prior.runtime_binding(BACKEND)
    proof_control = next(c for c in accepted["backend_attempts"] if c["passed"])
    assert proof_control["backend"] == BACKEND
    proof = location(proof_control["proof"])
    tiny_cnf = proof.parent/"unsat.cnf"
    tiny = run_checker(checker, tiny_cnf, proof, control_directory/"tiny-drat.log", LIMITS["tiny_DRAT_seconds"])
    assert tiny["passed"]
    record = {"status": "PASS: one face112 proof-capable query prepared; no query", "complete": True,
              "source_hashes": sources, "limits": LIMITS, "backend": BACKEND, "runtime": runtime,
              "model_directory": portable(model_directory), "model_sha256": digest(model_directory/"model.json"),
              "model_cold": portable(model_cold), "model_cold_sha256": digest(model_cold),
              "CNF_sha256": model["formula"]["CNF_sha256"], "formula": model["formula"],
              "unit_provenance": model["unit_provenance"], "checker": checker_binding(checker),
              "old_tiny_backend_control_preparation_sha256": OLD_PREPARATION_SHA,
              "current_checker_on_existing_tiny_proof": tiny, "tiny_solver_queries_repeated": 0,
              "production_solver_calls": 0, "assumptions": [], "symmetry_restrictions": 0,
              "candidate_basis_or_fractional_values_used": False,
              "SAT_scope": "Exact partial64-column incidence only; full previous inspector plus112zeros and all new cardinalities required.",
              "UNSAT_scope": "Only indexed35-core case4, after direct and cold full-formula/input/DRAT checks."}
    overlay.save_new(output, record)
    return record


def checked(preparation, require_cnf=False, require_runtime=False):
    prep = json.loads(preparation.read_bytes())
    assert prep["complete"] and prep["source_hashes"] == source_hashes()
    assert prep["limits"] == LIMITS and prep["backend"] == BACKEND
    assert prep["assumptions"] == [] and prep["production_solver_calls"] == 0
    directory = location(prep["model_directory"])
    assert digest(directory/"model.json") == prep["model_sha256"]
    assert digest(location(prep["model_cold"])) == prep["model_cold_sha256"]
    model = overlay.checked_model(directory, require_cnf)
    assert prep["formula"] == model["formula"] and prep["unit_provenance"] == model["unit_provenance"]
    assert prep["CNF_sha256"] == model["formula"]["CNF_sha256"]
    if require_runtime:
        assert prep["runtime"] == prior.runtime_binding(BACKEND)
        assert prep["checker"] == checker_binding(prep["checker"]["path"])
    return prep, model


class ResourceRefusal(Exception):
    pass


def inspect_selected(selected, model):
    proof = model["unit_provenance"]
    assert selected == sorted(set(selected)) and not(set(selected) & set(proof["all112_zero_columns"]))
    result = prior.previous.inspect_selected(selected)
    chosen = set(selected)
    assert [len(chosen & set(support)) for support in proof["parity_supports"]] == [1, 1]
    assert len(chosen & set(proof["sum2_support"])) == 2
    assert len(chosen & set(proof["pair_AMO"])) <= 1
    return {"original_full_inspector": result, "all112_proved_zeros_checked": True,
            "both_parity_equalities_checked": True, "derived86_column_sum_two_checked": True,
            "integer_pair_AMO_checked": True, "selected_columns": selected, "full_graph_claimed": False}


def child(preparation, directory):
    resource_caps()
    assert not directory.exists()
    directory.mkdir(parents=True)
    started = time.monotonic()
    record = {"status": "RUNNING: owned proof-enabled child", "source_hashes": source_hashes(),
              "preparation_sha256": digest(preparation), "production_solve_calls": 0,
              "assumptions": [], "limits": LIMITS, "partial_proof_accepted": False}
    try:
        prep, model = checked(preparation, True, True)
        record.update(CNF_sha256=prep["CNF_sha256"], runtime=prep["runtime"], backend=BACKEND)
        with solver_api.Solver(name=BACKEND, with_proof=True) as solver:
            assert type(solver.solver).__name__ == "Cadical300"
            count = 0
            for clause in prior.previous.read_full_clauses(Path(model["cnf_path"]), overlay.VARIABLES, overlay.NEW_CLAUSES):
                solver.add_clause(clause); count += 1
            assert count == overlay.NEW_CLAUSES
            record.update(bootstrap_clauses=count, bootstrap_seconds=time.monotonic()-started,
                          production_solve_calls=1)
            save(directory/"progress.json", record)
            print(json.dumps({"phase": "solve", "bootstrap_seconds": record["bootstrap_seconds"]}), flush=True)
            answer = solver.solve()
            record.update(solve_return_seconds=time.monotonic()-started, solver_statistics=solver.accum_stats())
            if answer is True:
                positive = {v for v in solver.get_model() if v > 0}
                selected = [a for a in range(1214) if a+1 in positive]
                record.update(status="SAT: exact parent inspector pending", selected_columns=selected)
            else:
                assert answer is False
                native = solver.solver
                assert native.prfile is not None
                pysolvers.flushpr(native.prfp)
                size = os.fstat(native.prfile.fileno()).st_size
                record["binary_proof_bytes"] = size
                if size > LIMITS["accepted_binary_proof_bytes"]:
                    raise ResourceRefusal("completed binary proof exceeds accepted export limit")
                proof = solver.get_proof()
                assert proof is not None
                appended = not proof or proof[-1] != "0"
                if appended:
                    proof.append("0")
                raw = directory/"raw.drat"
                total = 0
                with raw.open("wb") as stream:
                    for line in proof:
                        data = (line+"\n").encode("ascii"); total += len(data)
                        if total > LIMITS["accepted_text_proof_bytes"]:
                            raise ResourceRefusal("completed text proof exceeds accepted export limit")
                        stream.write(data)
                record.update(status="UNSAT: direct proof check pending", raw_proof=portable(raw),
                              raw_proof_sha256=digest(raw), raw_proof_bytes=total,
                              terminal_empty_clause_appended=appended)
    except (ResourceRefusal, MemoryError, OSError) as error:
        record.update(status="UNKNOWN: resource or proof-export refusal", reason_type=type(error).__name__, reason=str(error))
    except Exception as error:
        record.update(status="ERROR: no unchecked terminal accepted", reason_type=type(error).__name__, reason=str(error))
        raise
    finally:
        record.update(elapsed_seconds=time.monotonic()-started,
                      peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        save(directory/"result.json", record)
    return record


def solve(preparation, directory):
    assert not directory.exists()
    prep, model = checked(preparation, True, True)
    directory.mkdir(parents=True)
    path = directory/"result.json"; started = time.monotonic()
    result = {"status": "RUNNING: one owned face112 child", "source_hashes": source_hashes(),
              "preparation_sha256": digest(preparation), "model_sha256": prep["model_sha256"],
              "CNF_sha256": prep["CNF_sha256"], "limits": LIMITS,
              "backend": BACKEND, "runtime": prep["runtime"], "assumptions": [],
              "production_child_count": 1, "automatic_retries": 0,
              "case4_excluded": False, "full_graph_found": False}
    save(path, result)
    def timeout(pid, elapsed):
        result.update(status="UNKNOWN:180-second owned child timeout", pid=pid,
                      elapsed_at_timeout=elapsed, partial_proof_accepted=False)
        save(path, result)
    try:
        process = prior.owned_child([sys.executable, str(Path(__file__).resolve()), "child",
                                     "--preparation", str(preparation.resolve()),
                                     "--directory", str((directory/"child").resolve())],
                                    directory/"child.log",
                                    LIMITS["owned_child_wall_seconds_including_imports_bootstrap_solve_and_export"], timeout)
        result["child_process"] = process
        if process["timed_out"]:
            assert result["status"].startswith("UNKNOWN:") and process["child_reaped"]
        elif process["returncode"] != 0:
            result.update(status="UNKNOWN: child failed or reached an OS resource limit",
                          partial_proof_accepted=False)
        else:
            child_path = directory/"child/result.json"
            record = json.loads(child_path.read_bytes())
            assert record["source_hashes"] == source_hashes() and record["preparation_sha256"] == digest(preparation)
            assert record["limits"] == LIMITS and record["assumptions"] == []
            assert record["production_solve_calls"] <= 1
            result.update(child_result=portable(child_path), child_result_sha256=digest(child_path))
            if record["status"].startswith("UNKNOWN:"):
                result.update(status=record["status"], resource_reason=record.get("reason"), partial_proof_accepted=False)
            else:
                assert record["CNF_sha256"] == prep["CNF_sha256"]
                assert record["runtime"] == prep["runtime"] and record["backend"] == BACKEND
                assert record["bootstrap_clauses"] == overlay.NEW_CLAUSES and record["production_solve_calls"] == 1
                if record["status"].startswith("SAT:"):
                    result["partial_witness"] = inspect_selected(record["selected_columns"], model)
                    result["status"] = "SAT: full exact incidence inspector and112-face constraints passed"
                else:
                    assert record["status"].startswith("UNSAT:")
                    raw = location(record["raw_proof"])
                    assert digest(raw) == record["raw_proof_sha256"] and raw.stat().st_size <= LIMITS["accepted_text_proof_bytes"]
                    result.update(status="UNSAT: direct DRAT pending", raw_proof=portable(raw), raw_proof_sha256=digest(raw))
                    save(path, result)
                    retained, proof = directory/"retained.cnf", directory/"retained.drat"
                    check = run_checker(Path(prep["checker"]["path"]), Path(model["cnf_path"]), raw,
                                        directory/"direct-drat.log", LIMITS["direct_DRAT_seconds"], retained, proof)
                    result["direct_check"] = check
                    if not check["passed"]:
                        result["status"] = "UNKNOWN: completed UNSAT answer lacks a checked direct proof"
                    else:
                        inclusion = retained_inclusion(Path(model["cnf_path"]), retained)
                        result["retained_certificate"] = {"cnf": portable(retained), "cnf_sha256": digest(retained),
                            "proof": portable(proof), "proof_sha256": digest(proof), "input_inclusion": inclusion}
                        result["status"] = "UNSAT with direct DRAT: cold full-formula/input/DRAT replay required"
    except Exception as error:
        result.update(status="ERROR: no unchecked exclusion promoted", reason_type=type(error).__name__, reason=str(error))
        raise
    finally:
        result["elapsed_seconds"] = time.monotonic()-started
        save(path, result)
    return result


def replay(preparation, directory, output):
    assert not output.exists()
    prep, model = checked(preparation)
    result_path = directory/"result.json"
    result = json.loads(result_path.read_bytes())
    assert result["source_hashes"] == source_hashes() and result["preparation_sha256"] == digest(preparation)
    assert result["model_sha256"] == prep["model_sha256"] and result["CNF_sha256"] == prep["CNF_sha256"]
    assert result["limits"] == LIMITS and result["assumptions"] == [] and result["automatic_retries"] == 0
    assert result["production_child_count"] == 1 and result["case4_excluded"] is False
    assert result["backend"] == BACKEND and result["runtime"] == prep["runtime"]
    started = time.monotonic()
    report = {"status": "RUNNING: cold complete formula replay", "source_hashes": source_hashes(),
              "preparation_sha256": digest(preparation), "result_sha256": digest(result_path),
              "CNF_sha256": prep["CNF_sha256"], "case4_excluded": False,
              "complete_graph": False, "solver_query_called": False}
    try:
        with tempfile.TemporaryDirectory(prefix="rook112-binary-terminal-cold-") as temporary:
            full = Path(temporary)/"full.cnf"
            rebuilt = overlay.rebuild(full)
            assert all(model[k] == v for k, v in rebuilt.items())
            assert digest(full) == prep["CNF_sha256"]
            report["cold_formula_seconds"] = time.monotonic()-started
            if "child_result" in result:
                assert digest(location(result["child_result"])) == result["child_result_sha256"]
            if result["status"].startswith("SAT:"):
                actual = inspect_selected(result["partial_witness"]["selected_columns"], model)
                assert normalized(actual) == result["partial_witness"]
                report["status"] = "PASS: cold full formula and exact partial incidence including112zeros"
            elif result["status"].startswith("UNSAT with direct DRAT:"):
                assert result["direct_check"]["passed"]
                assert digest(location(result["direct_check"]["log"])) == result["direct_check"]["log_sha256"]
                item = result["retained_certificate"]
                retained, proof = location(item["cnf"]), location(item["proof"])
                assert digest(retained) == item["cnf_sha256"] and digest(proof) == item["proof_sha256"]
                assert proof.stat().st_size <= LIMITS["retained_proof_bytes"]
                inclusion = retained_inclusion(full, retained)
                assert inclusion == item["input_inclusion"]
                checker = Path(prep["checker"]["path"])
                assert checker_binding(checker) == prep["checker"]
                verified = run_checker(checker, retained, proof, output.with_suffix(".drat.log"), LIMITS["cold_DRAT_seconds"])
                assert verified["passed"]
                report.update(status="PASS: cold full formula, every unit premise, retained inclusion and DRAT",
                              case4_excluded=True, excluded_indexed_core=4,
                              input_inclusion=inclusion, cold_DRAT=verified)
            else:
                assert result["status"].startswith(("UNKNOWN:", "ERROR:"))
                if result.get("child_process", {}).get("timed_out"):
                    assert result["child_process"]["child_reaped"] and result["partial_proof_accepted"] is False
                report["status"] = "PASS: cold complete formula and unresolved terminal binding; no exclusion"
    except Exception as error:
        report.update(status="ERROR: cold proof or binding not certified", case4_excluded=False,
                      reason_type=type(error).__name__, reason=str(error))
        raise
    finally:
        report["elapsed_seconds"] = time.monotonic()-started
        save(output, report)
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=("prepare", "child", "solve", "replay"))
    p.add_argument("--model-directory", type=Path)
    p.add_argument("--model-cold", type=Path)
    p.add_argument("--controls-directory", type=Path)
    p.add_argument("--preparation", type=Path)
    p.add_argument("--directory", type=Path)
    p.add_argument("--output", type=Path)
    p.add_argument("--drat-trim", type=Path, default=Path("/workspace/scratch/ab2f4d4412fd/drat-trim"))
    a = p.parse_args()
    if a.mode == "prepare":
        assert all(v is not None for v in (a.model_directory, a.model_cold, a.output, a.controls_directory))
        answer = prepare(a.model_directory.resolve(), a.model_cold.resolve(), a.output.resolve(),
                         a.controls_directory.resolve(), a.drat_trim.resolve())
    else:
        assert a.preparation is not None and a.directory is not None
        if a.mode == "child":
            answer = child(a.preparation.resolve(), a.directory.resolve())
        elif a.mode == "solve":
            answer = solve(a.preparation.resolve(), a.directory.resolve())
        else:
            assert a.output is not None
            answer = replay(a.preparation.resolve(), a.directory.resolve(), a.output.resolve())
    print(json.dumps({k: answer[k] for k in ("status", "elapsed_seconds", "case4_excluded") if k in answer}, indent=2), flush=True)


if __name__ == "__main__":
    main()
