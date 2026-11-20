"""One proof-enabled SAT pilot and separate certificate replay for center 355.

Preparation only binds the completed small CNF. A run makes at most one
Glucose4 solve_limited call. UNSAT remains unverified until a separately
invoked DRAT checker accepts the proof against a freshly rebuilt CNF.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import threading
import time

ROOT = Path(__file__).resolve().parents[2]
BASE = "experiments/logs/root-prism-free/f0-local-center355-preparation01/"
BINDINGS = {
    "builder": ("experiments/workspace/root_prism_free_f0_local_center355.py",
                "e3e7852c674ec132f1a08f4ca9ff4ea0d11a581be4f6f39d512b8114b48d3054"),
    "instance": (BASE+"instance.json", "1619eb8050ee496c2e0f8f8ca65dbc98c6fee01c259b98e91c377d2ea2b3943d"),
    "model": (BASE+"model.json", "1cdd8113ee62eff4b87bfaa24e4e5638ff94a3c4270a0449aa38384787598b86"),
    "CNF": (BASE+"model.cnf", "fcb2e5af81712b914acc491de241917d6093461ef990f5b78e86c79df3deedae"),
    "builder_preparation": (BASE+"preparation.json",
                            "1cf0c80b67e0956d62197d880cf2cc06e83f8ad049f0038430877b9cd86fc56a"),
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def configuration():
    for path, digest in BINDINGS.values():
        assert sha((ROOT/path).read_bytes()) == digest
    return {
        "schema": "conway99.f0-local-center355-pilot-preparation.v1",
        "runner_source_sha256": sha(Path(__file__).read_bytes()),
        "bindings": {k: {"path": p, "sha256": h} for k, (p, h) in BINDINGS.items()},
        "center": 355, "primary_bits": 218, "variables": 5408, "clauses": 16105,
        "maximum_solver_seconds": 30, "solver_threads": 1, "production_solve_calls": 1,
        "clock_scope": "Solver initialization plus its single solve_limited call; deterministic model rebuild and exact verification are reported separately.",
        "proof_enabled": True, "UNSAT_requires_separate_DRAT_verification": True,
        "unknown_proof_is_never_used": True,
        "SAT_requires_native_rows_and_visible_caps": True,
        "local_neighbor_bits_untied": True, "matching_condition_added": False,
        "source_contains_no_other_center_query": True,
        "scope": "Necessary local eight-neighbor projection. A SAT witness is not an SRG or full incidence completion.",
    }


def rebuild():
    conf = configuration()
    spec = importlib.util.spec_from_file_location("frozen_f0_local_center355", ROOT/BINDINGS["builder"][0])
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    instance, core, clauses, variables, raw, model = builder.build()
    assert instance == json.loads((ROOT/BINDINGS["instance"][0]).read_bytes())
    assert model == json.loads((ROOT/BINDINGS["model"][0]).read_bytes())
    assert raw == (ROOT/BINDINGS["CNF"][0]).read_bytes()
    return conf, builder, instance, core, clauses, variables, raw


def check_sat(assignment, clauses, variables, instance, core, builder):
    assert all(type(lit) is int and 1 <= abs(lit) <= variables for lit in assignment)
    literals = set(assignment)
    assert len(literals) == len(assignment) and not any(-lit in literals for lit in literals)
    assert all((v in literals) != (-v in literals) for v in range(1, 219))
    assert all(any(lit in literals for lit in clause) for clause in clauses)
    chosen = [v for v in range(1, 219) if v in literals]
    return builder.inspect_witness(instance, core, chosen)


def solve_once(conf, builder, instance, core, clauses, variables, directory, seconds):
    started = time.monotonic()
    interrupted = [False]
    result = {
        "status": "UNKNOWN_BEFORE_INITIALIZATION", "solver": "Glucose4",
        "solver_limit_seconds": seconds, "proof_enabled": True, "production_solve_calls": 0,
        "CNF_sha256": BINDINGS["CNF"][1], "primary_bits": 218, "center": 355,
    }
    with builder.Glucose4(bootstrap_with=clauses, with_proof=True) as solver:
        remaining = seconds-(time.monotonic()-started)
        if remaining <= 0:
            result["status"] = "UNKNOWN_INITIALIZATION_EXHAUSTED_LIMIT"
        else:
            def interrupt():
                interrupted[0] = True
                solver.interrupt()
            timer = threading.Timer(remaining, interrupt)
            timer.daemon = True
            timer.start()
            try:
                result["production_solve_calls"] = 1
                answer = solver.solve_limited(expect_interrupt=True)
            finally:
                timer.cancel()
                timer.join()
            if answer is True:
                assignment = solver.get_model()
                model_raw = canonical(assignment)+b"\n"
                (directory/"solver-model.json").write_bytes(model_raw)
                result["solver_model_sha256"] = sha(model_raw)
                result["native_witness"] = check_sat(assignment, clauses, variables, instance, core, builder)
                result["status"] = "SAT_EXACT_LOCAL_BOOLEAN_NEIGHBOR_WITNESS"
            elif answer is False:
                proof = solver.get_proof()
                assert isinstance(proof, list) and all(isinstance(line, str) for line in proof)
                proof_raw = ("\n".join(proof)+("\n" if proof else "")).encode()
                (directory/"proof.drat").write_bytes(proof_raw)
                result.update(status="SOLVER_UNSAT_AWAITING_SEPARATE_PROOF_CHECK",
                              proof_sha256=sha(proof_raw), proof_bytes=len(proof_raw))
            else:
                assert answer is None
                result["status"] = "UNKNOWN_INTERRUPTED"
    result["interrupt_requested"] = interrupted[0]
    result["solver_and_verification_seconds"] = time.monotonic()-started
    result["graph_completion_claimed"] = False
    return result


def replay_run(builder, instance, core, clauses, variables, raw, run_directory, directory, checker):
    result_path = run_directory/"result.json"
    result_raw = result_path.read_bytes()
    result = json.loads(result_raw)
    assert result["runner_source_sha256"] == sha(Path(__file__).read_bytes())
    assert result["bindings"] == configuration()["bindings"]
    assert result["CNF_sha256"] == sha(raw)
    report = {"run_result_sha256": sha(result_raw), "CNF_sha256": sha(raw),
              "production_solve_calls": 0, "fresh_CNF_rebuild": True, "graph_completion_claimed": False}
    if result["status"] == "SAT_EXACT_LOCAL_BOOLEAN_NEIGHBOR_WITNESS":
        model_raw = (run_directory/"solver-model.json").read_bytes()
        assert sha(model_raw) == result["solver_model_sha256"]
        witness = check_sat(json.loads(model_raw), clauses, variables, instance, core, builder)
        assert witness == result["native_witness"]
        report.update(status="PASS: exact SAT local-row and CNF replay", native_witness=witness)
    elif result["status"] == "SOLVER_UNSAT_AWAITING_SEPARATE_PROOF_CHECK":
        assert checker is not None and checker.is_file(), "A separate DRAT checker is required."
        proof = run_directory/"proof.drat"
        assert sha(proof.read_bytes()) == result["proof_sha256"]
        cnf = directory/"replayed-model.cnf"
        cnf.write_bytes(raw)
        process = subprocess.run([str(checker.resolve()), str(cnf.resolve()), str(proof.resolve())],
                                 text=True, capture_output=True, timeout=30, check=False)
        (directory/"drat-check.log").write_text(process.stdout+process.stderr)
        assert process.returncode == 0
        assert re.search(r"(?m)^s VERIFIED(?:\s|$)", process.stdout) is not None
        report.update(status="PASS: independently checked UNSAT local certificate",
                      checker_sha256=sha(checker.read_bytes()),
                      checker_log_sha256=sha((directory/"drat-check.log").read_bytes()),
                      proof_sha256=result["proof_sha256"],
                      excluded_center_selector_orbit=instance["center_selector_orbit"])
    else:
        assert result["status"].startswith("UNKNOWN")
        report["status"] = "UNKNOWN: model binding replayed; no proof or exclusion accepted"
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "run", "replay"))
    parser.add_argument("--preparation", type=Path, required=True)
    parser.add_argument("--directory", type=Path)
    parser.add_argument("--run-directory", type=Path)
    parser.add_argument("--checker", type=Path)
    parser.add_argument("--seconds", type=float, default=30)
    args = parser.parse_args()
    assert 0 < args.seconds <= 30
    started = time.monotonic()
    conf = configuration()
    if args.mode == "prepare":
        assert not args.preparation.exists()
        args.preparation.write_bytes(canonical(conf)+b"\n")
        print(json.dumps({"status": "PREPARED: no production solver call",
                          "source_sha256": conf["runner_source_sha256"],
                          "preparation_sha256": sha(args.preparation.read_bytes()),
                          "variables": 5408, "clauses": 16105}, indent=2))
        return
    assert conf == json.loads(args.preparation.read_bytes())
    assert args.directory is not None and not args.directory.exists()
    args.directory.mkdir(parents=True)
    report = {}
    try:
        _, builder, instance, core, clauses, variables, raw = rebuild()
        if args.mode == "run":
            report = solve_once(conf, builder, instance, core, clauses, variables, args.directory, args.seconds)
        else:
            assert args.run_directory is not None
            report = replay_run(builder, instance, core, clauses, variables, raw,
                                args.run_directory, args.directory, args.checker)
    except Exception as error:
        report = {"status": "ERROR_NO_VALIDATED_OUTCOME", "error_type": type(error).__name__,
                  "message": str(error), "graph_completion_claimed": False}
        raise
    finally:
        report["runner_source_sha256"] = conf["runner_source_sha256"]
        report["bindings"] = conf["bindings"]
        report["pilot_preparation_sha256"] = sha(args.preparation.read_bytes())
        report["total_seconds"] = time.monotonic()-started
        (args.directory/"result.json").write_text(json.dumps(report, indent=2)+"\n")
        print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
