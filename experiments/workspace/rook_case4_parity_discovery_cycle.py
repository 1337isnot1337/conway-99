"""Append-only continuation seeded by two individually certified parity cuts.

The reviewed v4 numerical, saved-basis, full-point, and cold-check functions are
imported unchanged. A separate envelope imposes this continuation's smaller
scope. Discovery completeness is not a premise of any accepted inequality.
"""
import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

import rook_case4_parity_cycle_v4 as previous
import rook_case4_parity_discovery as discovery

ROOT, LOG = previous.ROOT, previous.LOGS
exact = previous.exact
save, read, ref, checked = previous.save, previous.read_record, previous.record_ref, previous.checked_ref
sha, canonical = exact.sha, exact.canonical

SOURCES = {
    "previous": ("experiments/workspace/rook_case4_parity_cycle_v4.py",
                 "345e091ef71dde96b3423773d5315b8733c275f0af142ab0f88ac03570ca263e"),
    "discovery": ("experiments/workspace/rook_case4_parity_discovery.py",
                  "672c5b5916ad823d7c89d566a68a49e3cf42f3a75e76d9144542cf4fe8a63bd7"),
    "saved_cut_checker": ("experiments/workspace/rook_case4_parity_cycle_saved_cuts_direct.py",
                          "faf49add2ee84402f2efdb5a050f0ac62612db118219738f4831c59e61e66c42"),
}
INPUTS = {
    "saved_cuts": (LOG+"rook-case4-parity-cycle-run01/scan-00/cuts.jsonl",
                   "9cba12a6030d06de531107cf0e28010cd81011319e0e98d363d4146349e85cd1"),
    "direct_proof": (LOG+"rook-case4-parity-cycle-saved-cuts-direct-replay01.json",
                     "c47c22e6dc438efba2be7695892c63b33f9c7afa45c42394bf0585c350947cd6"),
    "direct_gate": (LOG+"rook-case4-parity-cycle-saved-cuts-root-review.json",
                    "64e01ac79de7026cf0dc93874a9003da4f61c5f1e4db05c7f9c81d138b36a595"),
    "native_preflight": (LOG+"rook-case4-parity-cycle-preflight04.json",
                         "d3827408d08dd443093cba2d0c19e250391c142c6e97a4f04f316567c04bf264"),
}
LIMITS = {
    "LP_rounds": 2, "discoveries": 2, "cuts_per_discovery": 2, "seed_cuts": 2,
    "maximum_cuts": 6, "raw_words_per_discovery": 123123,
    "discovery_cooperative_seconds": 45, "discovery_hard_seconds": 60,
    "proof_seconds": 10, "numerical_seconds": 180, "exact_seconds": 60,
    "exact_cold_seconds": 60, "cumulative_native_seconds": 120,
    "native_calls_per_round": 30, "maximum_native_calls": 60,
    "transcript_bytes": 64 << 20, "result_reserve_bytes": 1 << 20,
    "maximum_declared_child_seconds": 740, "whole_cycle_hard_seconds": 900,
    "maximum_dynamic_exact_dimension": 512, "maximum_exact_output_bits": 4096,
    "threads": 1, "automatic_retries": 0,
}
REUSED = ["numeric_stage", "numeric_records", "finite_bound", "inspect_point",
          "exact_stage", "replay_numeric", "exact_cold", "load_matrix"]


def bindings():
    sources = {}
    for name, (path, expected) in SOURCES.items():
        assert sha((ROOT/path).read_bytes()) == expected, ("changed source", name)
        sources[name] = {"path": path, "sha256": expected}
    assert Path(previous.__file__).resolve() == ROOT/SOURCES["previous"][0]
    assert Path(discovery.__file__).resolve() == ROOT/SOURCES["discovery"][0]
    for name in REUSED:
        assert Path(getattr(previous, name).__code__.co_filename).resolve() == Path(previous.__file__).resolve()
    return {"controller_sha256": sha(Path(__file__).read_bytes()), "sources": sources,
            "reused_v4_bindings": previous.source_bindings(),
            "inputs": {k: list(v) for k, v in INPUTS.items()},
            "numeric_exact_cold_functions_imported_unchanged": REUSED}


def bound_input(name):
    path, expected = INPUTS[name]
    raw = (ROOT/path).read_bytes(); assert sha(raw) == expected, ("changed input", name)
    return [json.loads(line) for line in raw.splitlines()] if name == "saved_cuts" else json.loads(raw)


def input_ref(name):
    path, expected = INPUTS[name]
    return {"path": path, "sha256": expected}


def seed_registry():
    proof, cuts = bound_input("direct_proof"), bound_input("saved_cuts")
    bound_input("direct_gate")
    assert proof["status"] == "PASS: two complete necessary cuts and their exact point deficits"
    assert proof["source_sha256"] == SOURCES["saved_cut_checker"][1]
    assert proof["inputs"]["cuts"] == list(INPUTS["saved_cuts"])
    assert proof["inputs"]["point"] == list(previous.INPUTS["point"])
    assert len(cuts) == len(proof["cuts"]) == LIMITS["seed_cuts"]
    assert [c["raw_candidate_id"] for c in cuts] == [73296, 76530]
    registry = []
    for cut, result in zip(cuts, proof["cuts"]):
        assert result["raw_candidate_id"] == cut["raw_candidate_id"]
        assert result["full_original1214_integer_coefficients"] == cut["full_original1214_integer_coefficients"]
        assert result["signed_inequality"] == cut["inequality"]
        assert result["exact_cover_deficit_numerator"] == cut["exact_violation_numerator"] > 0
        registry.append({"certificate": cut, "row_key": exact.row_key(cut["inequality"]),
                         "source_point": previous.seed_point_ref(), "direct_proof": input_ref("direct_proof")})
    assert len({e["row_key"] for e in registry}) == len(registry)
    return registry


def definition():
    flight = bound_input("native_preflight")
    assert flight["status"].startswith("PASS:") and flight["optimizer_calls"] == 0
    assert flight["source_bindings"] == previous.source_bindings()
    registry = seed_registry()
    assert previous.PREFIX_ROWS == 167115 and previous.PREFIX_NNZ == 10769496
    assert previous.SELECTORS == 1102 and previous.VARIABLES == 1103
    assert previous.LIMITS["cumulative_native_seconds"] == LIMITS["cumulative_native_seconds"]
    assert previous.LIMITS["native_calls_per_round"] == LIMITS["native_calls_per_round"]
    assert previous.LIMITS["numerical_phase_seconds"] == LIMITS["numerical_seconds"]
    assert previous.LIMITS["exact_seconds"] == previous.LIMITS["exact_cold_seconds"] == 60
    assert previous.LIMITS["maximum_dynamic_exact_dimension"] == LIMITS["maximum_dynamic_exact_dimension"]
    return {"bindings": bindings(), "limits": LIMITS,
            "base_extended_rows": previous.PREFIX_ROWS, "base_nonzeros": previous.PREFIX_NNZ,
            "variables": previous.VARIABLES, "positive_selector_domain": previous.SELECTORS,
            "seed_registry_sha256": sha(canonical(registry)),
            "initial_rows": previous.PREFIX_ROWS+len(registry),
            "initial_nonzeros": previous.PREFIX_NNZ+sum(len(e["certificate"]["inequality"]["terms"]) for e in registry),
            "maximum_rows": previous.PREFIX_ROWS+LIMITS["maximum_cuts"],
            "maximum_nonzeros": previous.PREFIX_NNZ+previous.SELECTORS*LIMITS["maximum_cuts"],
            "initial_point": previous.seed_point_ref(), "native_preflight": input_ref("native_preflight"),
            "all_old_rows_and_original_coordinate_checks_retained": True,
            "discovery_exhaustion_is_not_an_acceptance_premise": True,
            "source_point_prefix_length_recorded_separately_from_later_cuts": True,
            "basis_aliases_and_fixed_values_are_proposals_only": True,
            "case4_scope_only": True}


def prepare(output):
    assert not output.exists()
    started = time.monotonic(); value = definition()
    controls = discovery.controls()
    result = {"status": "PREPARED: saved cuts seed a bounded append-only discovery continuation",
              "definition": value, "definition_sha256": sha(canonical(value)),
              "seed_registry": seed_registry(), "controls": controls,
              "no_new_case_discovery_or_optimizer": True,
              "seconds": time.monotonic()-started}
    save(output, result); return result


def checked_preparation(path):
    prep = read(path); value = definition()
    assert prep["definition"] == value and prep["definition_sha256"] == sha(canonical(value))
    assert prep["seed_registry"] == seed_registry()
    assert prep["status"].startswith("PREPARED:")
    return prep


def preflight(preparation, output):
    """One cached-array append check; no full model rebuild or native solve."""
    assert not output.exists()
    start = time.monotonic(); deadline = start+60
    prep = checked_preparation(preparation)
    data = previous.domain(deadline)
    old, arrays, pool = previous.load_matrix(data, prep["seed_registry"], deadline)
    assert len(arrays["row_lower"]) == prep["definition"]["initial_rows"] == 167117
    assert len(arrays["coefficients"]) == prep["definition"]["initial_nonzeros"] == 10769628
    old_flight = bound_input("native_preflight")
    runtime = old.runtime_binding()
    assert runtime == old_flight["runtime_binding"]
    appendix = []
    for i, entry in enumerate(prep["seed_registry"]):
        row = previous.PREFIX_ROWS+i
        terms = exact.row_terms(arrays, row)
        original = [[int(arrays["original_column_ids"][j]), c] for j, c in terms]
        assert original == entry["certificate"]["inequality"]["terms"]
        assert int(arrays["row_upper"][row]) == entry["certificate"]["inequality"]["upper"] == -1
        assert int(arrays["row_lower"][row]) == -len(terms)
        appendix.append({"row": row, "terms": original,
                         "lower": int(arrays["row_lower"][row]), "upper": -1})
    exact.tick(deadline)
    result = {"status": "PASS: immutable cached167115-row prefix plus two certified cuts",
              "preparation": ref(preparation), "bindings": bindings(),
              "definition_sha256": prep["definition_sha256"], "matrix_binding": exact.matrix_binding(arrays),
              "rows": len(arrays["row_lower"]), "nonzeros": len(arrays["coefficients"]),
              "appended_rows": appendix, "runtime_binding": runtime,
              "reused_native_preflight": input_ref("native_preflight"),
              "optimizer_calls": 0, "new_native_model_transport_calls": 0,
              "original_cover_supports_reconstructed": False, "seconds": time.monotonic()-start}
    save(output, result); return result


def checked_flight(preparation, preflight_path):
    prep = checked_preparation(preparation); flight = read(preflight_path)
    assert flight["preparation"] == ref(preparation) and flight["bindings"] == bindings()
    assert flight["definition_sha256"] == prep["definition_sha256"]
    assert flight["status"].startswith("PASS:") and flight["optimizer_calls"] == 0
    return prep, flight


def check_envelope(path):
    """Check the new contract without altering imported v4 module globals."""
    state = read(path); context = state["continuation"]
    assert context["bindings"] == bindings() and context["limits"] == LIMITS
    prep = checked(context["preparation"]); flight = checked(context["preflight"])
    assert prep["definition"]["bindings"] == bindings()
    assert prep["definition"]["limits"] == LIMITS
    assert prep["definition_sha256"] == sha(canonical(prep["definition"]))
    assert flight["preparation"] == context["preparation"] and flight["bindings"] == bindings()
    assert flight["definition_sha256"] == prep["definition_sha256"] and flight["status"].startswith("PASS:")
    assert state["source_bindings"] == previous.source_bindings() and state["limits"] == previous.LIMITS
    assert state["native_preflight"] == input_ref("native_preflight")
    assert LIMITS["seed_cuts"] <= len(state["cuts"]) <= LIMITS["maximum_cuts"]
    assert state["cuts"][:2] == prep["seed_registry"] == seed_registry()
    assert 0 <= context["point_accepted_cut_count"] <= len(state["cuts"])
    for entry in state["cuts"][2:]:
        proof = checked(entry["proof_record"])
        assert proof["status"] == "PASS: individually complete original-Gram cut proofs"
        stripped = {k: v for k, v in entry.items() if k != "proof_record"}
        assert stripped in proof["registry_additions"]
    return state


def state_payload(point, registry, native_seconds, carried, transcript_bytes,
                  preparation, preflight_path, accepted_count):
    state = previous.state_payload(point, registry, native_seconds, carried, transcript_bytes)
    state["native_preflight"] = input_ref("native_preflight")
    state["continuation"] = {"bindings": bindings(), "limits": LIMITS,
                             "preparation": ref(preparation), "preflight": ref(preflight_path),
                             "point_accepted_cut_count": accepted_count}
    return state


def owned(mode, state_path, directory, seconds):
    directory.mkdir(parents=True, exist_ok=True)
    label = mode.removeprefix("_"); start = time.monotonic()
    with (directory/(label+".stdout.log")).open("xb") as out, (directory/(label+".stderr.log")).open("xb") as err:
        try:
            process = subprocess.run([sys.executable, str(Path(__file__).resolve()), mode,
                "--state", str(state_path.resolve()), "--directory", str(directory.resolve())],
                stdout=out, stderr=err, timeout=seconds, check=False)
            record = {"exit_code": process.returncode, "hard_timeout": False}
        except subprocess.TimeoutExpired:
            record = {"exit_code": None, "hard_timeout": True}
    record.update(mode=mode, state=ref(state_path), hard_seconds=seconds,
                  seconds=time.monotonic()-start, artifacts=previous.stage_files(directory))
    return record


def stage_ok(record):
    return not record["hard_timeout"] and record["exit_code"] == 0


def controller(preparation, preflight_path, directory):
    start = time.monotonic(); deadline = start+LIMITS["whole_cycle_hard_seconds"]-5
    prep, flight = checked_flight(preparation, preflight_path)
    registry = list(prep["seed_registry"]); point = previous.seed_point_ref(); accepted_count = 0
    nums, den = previous.point_data(point); key = exact.point_key(nums, den)
    seen_points = {key}; carried = []
    result = {"status": "RUNNING", "bindings": bindings(), "limits": LIMITS,
              "preparation": ref(preparation), "preflight": ref(preflight_path),
              "registry": registry, "stages": [], "LP_rounds": 0, "discoveries": 0,
              "native_calls": 0, "native_seconds": 0.0, "discovery_transcript_bytes": 0,
              "point_history": [{"point": point, "point_key": key, "accepted_cut_count": 0,
                                 "accepted_extended_rows": previous.PREFIX_ROWS}],
              "latest_exact_point": point, "latest_exact_point_accepted_cut_count": 0,
              "case4_exclusion_verified": False, "exact_zero_face_found": False,
              "whole_graph_problem_resolved": False, "exhaustion_certified": False}
    target = directory/"result.json"; save(target, result)
    try:
        for round_id in range(LIMITS["LP_rounds"]):
            exact.tick(deadline)
            if result["native_seconds"] >= LIMITS["cumulative_native_seconds"]:
                result["status"] = "UNRESOLVED: cumulative native budget reached"; break
            state = state_payload(point, registry, result["native_seconds"], carried,
                result["discovery_transcript_bytes"], preparation, preflight_path, accepted_count)
            state_path = directory/f"state-numeric-{round_id:02d}.json"; save(state_path, state)
            numeric_dir = directory/f"numeric-{round_id:02d}"
            record = owned("_numeric", state_path, numeric_dir, LIMITS["numerical_seconds"])
            result["stages"].append(record); result["LP_rounds"] += 1
            if (numeric_dir/"result.json").exists():
                numerical = read(numeric_dir/"result.json")
                result["native_calls"] += numerical["native_calls"]
                result["native_seconds"] += numerical["native_seconds"]
            else:
                numerical = None
            save(target, result)
            assert result["native_calls"] <= LIMITS["maximum_native_calls"]
            if not stage_ok(record) or numerical is None or not numerical["complete"] or not numerical["iterations"]:
                result["status"] = "UNRESOLVED: numerical stage incomplete; no retry"; break
            exact_state = dict(state, numerical_result=ref(numeric_dir/"result.json"))
            exact_state_path = directory/f"state-exact-{round_id:02d}.json"; save(exact_state_path, exact_state)
            exact_dir = directory/f"exact-{round_id:02d}"
            record = owned("_exact", exact_state_path, exact_dir, LIMITS["exact_seconds"])
            result["stages"].append(record); save(target, result)
            if not stage_ok(record) or not (exact_dir/"result.json").exists():
                result["status"] = "UNRESOLVED: exact proposal unfinished"; break
            outcome = read(exact_dir/"result.json")
            record = owned("_exact_cold", exact_state_path, exact_dir, LIMITS["exact_cold_seconds"])
            result["stages"].append(record); save(target, result)
            if not stage_ok(record) or not (exact_dir/"cold.json").exists():
                result["status"] = "UNRESOLVED: cold arithmetic unfinished"; break
            cold = read(exact_dir/"cold.json")
            assert cold["status"].startswith("PASS:") and cold["result"] == ref(exact_dir/"result.json")
            if outcome["exact_certificate_found"]:
                assert cold["exact_certificate_replayed"]
                result["exact_certificate"] = outcome["certificate"]
                result["exact_certificate_cold"] = ref(exact_dir/"cold.json")
                result["case4_exclusion_verified"] = cold["kind"] == "exact_infeasibility"
                result["exact_zero_face_found"] = cold["kind"] == "exact_zero_face"
                result["status"] = "EXACT: case4 relaxation infeasible" if result["case4_exclusion_verified"] else "EXACT: new zero face; no domain mutation"
                break
            if not outcome["exact_point_found"] or not cold["exact_point_replayed"]:
                result["status"] = "UNRESOLVED: exact basis proposal failed full acceptance"; break
            point = {"candidate": outcome["candidate"], "cold": ref(exact_dir/"cold.json")}
            accepted_count = len(registry); nums, den = previous.point_data(point)
            key = exact.point_key(nums, den)
            result["latest_exact_point"] = point
            result["latest_exact_point_accepted_cut_count"] = accepted_count
            result["latest_exact_point_accepted_extended_rows"] = previous.PREFIX_ROWS+accepted_count
            if key in seen_points:
                result["status"] = "UNRESOLVED: repeated exact point; discovery not repeated"; break
            seen_points.add(key)
            result["point_history"].append({"point": point, "point_key": key,
                "accepted_cut_count": accepted_count, "accepted_extended_rows": previous.PREFIX_ROWS+accepted_count})
            carried = numerical["carried_covers_after"]
            save(target, result)
            if result["discovery_transcript_bytes"]+LIMITS["result_reserve_bytes"] >= LIMITS["transcript_bytes"]:
                result["status"] = "UNRESOLVED: transcript budget reached"; break
            discovery_state = state_payload(point, registry, result["native_seconds"], carried,
                result["discovery_transcript_bytes"], preparation, preflight_path, accepted_count)
            discovery_path = directory/f"state-discovery-{round_id:02d}.json"; save(discovery_path, discovery_state)
            discovery_dir = directory/f"discovery-{round_id:02d}"
            record = owned("_discover", discovery_path, discovery_dir, LIMITS["discovery_hard_seconds"])
            result["stages"].append(record); result["discoveries"] += 1
            # A hard stop or incomplete prefix cannot invalidate an atomic complete proof.
            charged = sum(p.stat().st_size for p in discovery_dir.iterdir() if p.is_file())+LIMITS["result_reserve_bytes"]
            result["discovery_transcript_bytes"] += charged
            save(target, result)
            if result["discovery_transcript_bytes"] > LIMITS["transcript_bytes"]:
                result["status"] = "UNRESOLVED: transcript cap; proofs retained but not adopted"; break
            proof_record = owned("_proofs", discovery_path, discovery_dir, LIMITS["proof_seconds"])
            result["stages"].append(proof_record); save(target, result)
            if not stage_ok(proof_record) or not (discovery_dir/"proofs.json").exists():
                result["status"] = "UNRESOLVED: individual proof replay incomplete"; break
            proof = read(discovery_dir/"proofs.json")
            assert proof["status"] == "PASS: individually complete original-Gram cut proofs"
            assert proof["state"] == ref(discovery_path)
            additions = [dict(entry, proof_record=ref(discovery_dir/"proofs.json")) for entry in proof["registry_additions"]]
            assert len(additions) <= LIMITS["cuts_per_discovery"]
            assert proof["cuts_checked"] == len(additions)
            registry.extend(additions); assert len(registry) <= LIMITS["maximum_cuts"]
            result["registry"] = registry
            result["later_cuts_not_satisfied_by_latest_point"] = len(registry)-accepted_count
            save(target, result)
            if not additions:
                result["status"] = "UNRESOLVED: no checked new cut from bounded discovery"; break
            if round_id+1 == LIMITS["LP_rounds"]:
                result["status"] = "UNRESOLVED: round cap; checked rejecting cuts retained for a later model"; break
        else:
            result["status"] = "UNRESOLVED: declared continuation ended"
    except Exception as exc:
        result.update(status="UNRESOLVED: controller error; completed proofs preserved",
                      error_type=type(exc).__name__, reason=str(exc))
    finally:
        result["seconds"] = time.monotonic()-start
        result["source_and_state_artifacts"] = [ref(p) for p in sorted(directory.glob("state-*.json"))]
        result["registered_cut_count"] = len(registry)
        result["registered_extended_rows"] = previous.PREFIX_ROWS+len(registry)
        save(target, result)
    return result


def run(preparation, preflight_path, directory):
    assert not directory.exists(); directory.mkdir(parents=True)
    start = time.monotonic()
    with (directory/"controller.stdout.log").open("xb") as out, (directory/"controller.stderr.log").open("xb") as err:
        process = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), "_controller",
            "--preparation", str(preparation.resolve()), "--preflight", str(preflight_path.resolve()),
            "--directory", str(directory.resolve())], stdout=out, stderr=err, start_new_session=True)
        timeout = False
        try:
            code = process.wait(timeout=LIMITS["whole_cycle_hard_seconds"])
        except subprocess.TimeoutExpired:
            timeout = True; os.killpg(process.pid, signal.SIGKILL); code = process.wait()
    report = {"status": "UNKNOWN: whole-cycle guard" if timeout else "UNKNOWN: controller error" if code else "owned continuation child terminated",
              "bindings": bindings(), "preparation": ref(preparation), "preflight": ref(preflight_path),
              "hard_timeout": timeout, "exit_code": code, "automatic_retries": 0,
              "hard_seconds": LIMITS["whole_cycle_hard_seconds"], "seconds": time.monotonic()-start}
    if (directory/"result.json").exists():
        report["result"] = ref(directory/"result.json")
    save(directory/"supervisor.json", report); return report


def verify(preparation, preflight_path, directory, output):
    """Chronological bindings, not a repeated scan, solver or point checker."""
    assert not output.exists(); start = time.monotonic()
    checked_flight(preparation, preflight_path)
    result, supervisor = read(directory/"result.json"), read(directory/"supervisor.json")
    assert supervisor["result"] == ref(directory/"result.json")
    assert result["bindings"] == supervisor["bindings"] == bindings() and result["limits"] == LIMITS
    assert result["preparation"] == supervisor["preparation"] == ref(preparation)
    assert result["preflight"] == supervisor["preflight"] == ref(preflight_path)
    registry = result["registry"]
    assert registry[:2] == seed_registry() and len(registry) <= LIMITS["maximum_cuts"]
    assert result["LP_rounds"] <= 2 and result["discoveries"] <= 2 and result["native_calls"] <= 60
    modes = [item["mode"] for item in result["stages"]]
    assert modes.count("_numeric") == result["LP_rounds"] and modes.count("_discover") == result["discoveries"]
    hard = {"_numeric": 180, "_exact": 60, "_exact_cold": 60, "_discover": 60, "_proofs": 10}
    checked_files = 0
    for item in result["stages"]:
        state = check_envelope(ROOT/item["state"]["path"])
        assert ref(ROOT/item["state"]["path"]) == item["state"]
        assert state["cuts"] == registry[:len(state["cuts"])]
        assert item["hard_seconds"] == hard[item["mode"]]
        for artifact in item["artifacts"]:
            assert sha((ROOT/artifact["path"]).read_bytes()) == artifact["sha256"]
            checked_files += 1
    for entry in registry[2:]:
        proof = checked(entry["proof_record"])
        assert proof["status"] == "PASS: individually complete original-Gram cut proofs"
        assert {k: v for k, v in entry.items() if k != "proof_record"} in proof["registry_additions"]
        assert entry["discovery_cut_file"] in proof["checked_cut_files"]
    for state_ref in result["source_and_state_artifacts"]:
        checked(state_ref)
    keys = set()
    assert len(result["point_history"]) <= 3
    for item in result["point_history"]:
        nums, den = previous.point_data(item["point"])
        assert exact.point_key(nums, den) == item["point_key"] and item["point_key"] not in keys
        keys.add(item["point_key"])
        count = item["accepted_cut_count"]
        assert item["accepted_extended_rows"] == previous.PREFIX_ROWS+count
        if count:
            point = checked(item["point"]["candidate"])
            assert point["registry_sha256"] == sha(canonical(registry[:count]))
    latest = result["latest_exact_point"]
    count = result["latest_exact_point_accepted_cut_count"]
    if count:
        assert checked(latest["candidate"])["registry_sha256"] == sha(canonical(registry[:count]))
    if result["case4_exclusion_verified"] or result["exact_zero_face_found"]:
        cold = checked(result["exact_certificate_cold"])
        assert cold["exact_certificate_replayed"]
        assert result["case4_exclusion_verified"] == (cold["kind"] == "exact_infeasibility")
        assert result["exact_zero_face_found"] == (cold["kind"] == "exact_zero_face")
    report = {"status": "PASS: continuation bindings and exact point-prefix ancestry",
              "bindings": bindings(), "supervisor": ref(directory/"supervisor.json"),
              "result": ref(directory/"result.json"), "stage_artifacts_bound": checked_files,
              "registered_cuts": len(registry), "latest_point_accepted_cut_count": count,
              "later_registered_cuts": len(registry)-count,
              "case_RREF_scan_optimizer_elimination_or_point_check_repeated": False,
              "exhaustion_certified": False, "seconds": time.monotonic()-start}
    save(output, report); return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "preflight", "run", "verify", "_controller",
                                         "_discover", "_proofs", "_numeric", "_exact", "_exact_cold"))
    for name in ("preparation", "preflight", "state", "directory", "output"):
        parser.add_argument("--"+name, type=Path)
    args = parser.parse_args()
    if args.mode == "prepare": result = prepare(args.output)
    elif args.mode == "preflight": result = preflight(args.preparation, args.output)
    elif args.mode == "run": result = run(args.preparation, args.preflight, args.directory)
    elif args.mode == "verify": result = verify(args.preparation, args.preflight, args.directory, args.output)
    elif args.mode == "_controller": result = controller(args.preparation, args.preflight, args.directory)
    elif args.mode == "_discover": result = discovery.discover(args.state, args.directory, check_envelope, LIMITS)
    elif args.mode == "_proofs": result = discovery.certify(args.state, args.directory, check_envelope, LIMITS)
    else:
        check_envelope(args.state)
        functions = {"_numeric": previous.numeric_stage, "_exact": previous.exact_stage,
                     "_exact_cold": previous.exact_cold}
        result = functions[args.mode](args.state, args.directory)
    print(json.dumps({k: v for k, v in result.items() if k in
        ("status", "seconds", "rows", "nonzeros", "LP_rounds", "discoveries", "native_calls", "native_seconds")}), flush=True)


if __name__ == "__main__":
    main()
