"""Eight-step direct540 master with exact, strictly growing selector cuts.

Every new master call has a strictly longer necessary-row prefix. Exact
matching obstructions or exact shared-row certificates supply the rows.
There is no visit clause, exterior SAT call, objective, hint or selector fix.
CP-SAT INFEASIBLE remains unproved. All saved vectors precede exact checking.
"""
import argparse
import gzip
import hashlib
import importlib.util
import json
from math import isfinite
from pathlib import Path
import resource
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
HELPER = ("experiments/workspace/root_prism_free_f0_direct_master_registry_v3.py",
          "9b5746f3cc6817515d36fb8236bb5e26d78825187914d36a3da9f1ed1f616393")
ITERATIONS, OWNER_SECONDS, TOTAL_CP_SECONDS = 8, 300, 180
CALL_SECONDS, SHARED_SECONDS, PREP_SECONDS, COLD_SECONDS, RESERVE = 60, 60, 60, 60, 8


def digest(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def value_sha(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def save(path, value):
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_bytes(canonical(value) + b"\n")
    tmp.replace(path)


def helper():
    path = ROOT / HELPER[0]
    assert digest(path) == HELPER[1]
    spec = importlib.util.spec_from_file_location("frozen_direct_master_registry", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def definition(ctx):
    return {"schema": "conway99.f0.strict-growth-direct540-master.v1", "source_sha256": digest(__file__),
            "registry_source": HELPER, "seed_configuration_sha256": ctx["config_sha256"],
            "seed_configuration": ctx["config"], "base_definition": ctx["base"].definition(),
            "shared_definition": ctx["shared_definition"], "matching_definition": ctx["matching"].definition(),
            "seed_registry_sha256": value_sha(ctx["registry"]), "seed_rows": len(ctx["registry"]),
            "variables": 540, "base_linear_rows": 4681, "initial_linear_rows": 4681 + len(ctx["registry"]),
            "maximum_iterations": ITERATIONS, "owner_seconds": OWNER_SECONDS,
            "maximum_cumulative_CP_solve_seconds": TOTAL_CP_SECONDS, "maximum_seconds_per_CP_call": CALL_SECONDS,
            "maximum_shared_seconds_per_candidate": SHARED_SECONDS, "maximum_shared_sequences": ITERATIONS,
            "maximum_original_and_bounded_LP_calls_each_per_candidate": 1,
            "preparation_owner_seconds": PREP_SECONDS, "cold_owner_seconds": COLD_SECONDS,
            "worker_count": 1, "seed": 0, "linearization_level": 0, "probing_level": 0,
            "strictly_increasing_prefix_before_every_later_call": True,
            "all_original172_equations90_motifs4416_cuts_checked_directly": True,
            "native_INFEASIBLE_is_unproved": True, "exterior_SAT_calls": 0,
            "objective_hint_selector_fix_or_visit_block": False,
            "new_cut_int64_overflow_stops_without_dropping_or_truncating_rows": True}


def prefix_snapshot(model, proto, path):
    expected = proto.SerializeToString()
    assert model.export_to_file(str(path))
    assert digest(path) == hashlib.sha256(expected).hexdigest()
    compressed = path.with_suffix(path.suffix + ".gz")
    compressed.write_bytes(gzip.compress(expected, mtime=0))
    return {"raw_sha256": digest(path), "raw_bytes": len(expected),
            "archive_sha256": digest(compressed), "rows": len(proto.constraints)}


def initialize(config_path, directory, stage, construct):
    h = helper()
    ctx = h.context(config_path, stage)
    base = ctx["base"]
    plan, raw, literal_cuts = base.load_artifacts(stage)
    cp, pb = base.import_native(stage)
    proto = base.checked_proto(pb, raw, plan)
    registry = ctx["registry"]
    model = base.construct_native(cp, proto, directory, stage) if construct else None
    h.append_expected(proto, registry)
    if construct:
        h.append_native(cp, model, registry)
        snapshot = prefix_snapshot(model, proto, directory / "initial-model.pb")
        save(directory / "initial-registry.json", registry)
    else:
        snapshot = {"raw_sha256": hashlib.sha256(proto.SerializeToString()).hexdigest(),
                    "rows": len(proto.constraints)}
    stage("37_seed_rows_and_complete_original_prefix_ready")
    return h, ctx, plan, literal_cuts, cp, pb, proto, model, snapshot


def preparation_check(preparation, ctx, snapshot):
    report = json.loads((preparation / "report.json").read_bytes())
    owner = json.loads((preparation / "owner.json").read_bytes())
    assert owner["report_accepted"] and owner["deadline_overrun_seconds"] == 0
    assert owner["source_sha256"] == digest(__file__) and owner["maximum_seconds"] == PREP_SECONDS
    assert owner["report_sha256"] == digest(preparation / "report.json")
    assert owner["supervision"]["status"] == "CHILD_EXITED" and owner["supervision"]["child_reaped"]
    assert owner["supervision"]["returncode"] == 0
    assert report["status"] == "PASS_NATIVE_PREFLIGHT_NO_SOLVER"
    assert report["definition"] == json.loads(canonical(definition(ctx)))
    assert report["initial_native"]["raw_sha256"] == snapshot["raw_sha256"]
    assert report["initial_registry_sha256"] == value_sha(ctx["registry"])
    assert report["production_solve_calls"] == 0 and report["optimizer_calls"] == 0 and not report["CpSolver_constructed"]
    return digest(preparation / "report.json")


def prepare(config_path, directory, deadline, stage):
    h, ctx, plan, cuts, cp, pb, proto, model, snapshot = initialize(config_path, directory, stage, True)
    return {"status": "PASS_NATIVE_PREFLIGHT_NO_SOLVER", "definition": definition(ctx),
            "controls": h.controls(), "initial_native": snapshot,
            "initial_registry_sha256": value_sha(ctx["registry"]), "production_solve_calls": 0,
            "CpSolver_constructed": False, "optimizer_calls": 0,
            "maximum_new_coefficient": max(abs(c) for e in ctx["registry"] for _, c in e["row"]["terms"]),
            "maximum_new_absolute_box_activity": max(sum(abs(c) for _, c in e["row"]["terms"]) for e in ctx["registry"])}


def inspect_candidate(h, ctx, values, plan, cuts, registry):
    return {"original": ctx["base"].inspect(values, plan, cuts), "additional": h.inspect_extra(values, registry)}


def run(config_path, preparation, directory, deadline, stage):
    result = {"status": "UNKNOWN_BEFORE_INITIALIZATION", "source_sha256": digest(__file__),
              "seed_configuration_sha256": digest(config_path), "iterations": [],
              "production_solve_calls": 0, "CP_solve_seconds": 0, "shared_optimizer_calls": 0,
              "native_INFEASIBLE_is_unproved": True, "whole_component_excluded": False,
              "graph_constructed": False, "automatic_same_prefix_retry": False}
    save(directory / "result.json", result)
    h, ctx, plan, cuts, cp, pb, proto, model, initial = initialize(config_path, directory, stage, True)
    prep_sha = preparation_check(preparation, ctx, initial)
    result.update(definition=definition(ctx), query_preparation_sha256=prep_sha)
    registry = ctx["registry"]
    save(directory / "registry.json", registry)
    previous_count = -1
    try:
        for index in range(ITERATIONS):
            budget = max(0.0, min(CALL_SECONDS, TOTAL_CP_SECONDS - result["CP_solve_seconds"],
                                   deadline - time.monotonic() - RESERVE))
            if budget <= 0:
                result["status"] = "UNKNOWN_MASTER_OR_OWNER_BUDGET"
                result["budget_stop"] = {"remaining_native": TOTAL_CP_SECONDS - result["CP_solve_seconds"],
                                         "remaining_owner_less_reserve": deadline - time.monotonic() - RESERVE}
                break
            assert len(registry) > previous_count
            previous_count = len(registry)
            sub = directory / ("iteration-%02d" % index)
            sub.mkdir()
            save(sub / "registry-prefix.json", registry)
            snapshot = prefix_snapshot(model, proto, sub / "prefix.pb")
            remaining_owner = deadline - time.monotonic()
            budget = max(0.0, min(CALL_SECONDS, TOTAL_CP_SECONDS - result["CP_solve_seconds"], remaining_owner - RESERVE))
            if budget <= 0:
                result["status"] = "UNKNOWN_MASTER_OR_OWNER_BUDGET"
                result["budget_stop"] = {"remaining_native": TOTAL_CP_SECONDS - result["CP_solve_seconds"],
                                         "remaining_owner_less_reserve": remaining_owner - RESERVE}
                break
            stage("master_call_%02d_entering" % index)
            solver = cp.CpSolver()
            params = ctx["base"].native_parameters(cp.cmh, budget)
            solver.parameters = params
            (sub / "parameters.pbtxt").write_text(str(params))
            round_record = {"index": index, "status": "MASTER_CALL_ACTIVE", "native_budget": budget,
                            "remaining_owner_at_budget_allocation": remaining_owner,
                            "prefix": snapshot, "registry_sha256": value_sha(registry), "registry_rows": len(registry),
                            "parameters_sha256": digest(sub / "parameters.pbtxt"), "direct_checked": False,
                            "shared_completed": False}
            save(sub / "iteration.json", round_record)
            result["iterations"].append(sub.name)
            result["production_solve_calls"] += 1
            save(directory / "result.json", result)
            started = time.monotonic()
            status = solver.solve(model)
            elapsed = time.monotonic() - started
            result["CP_solve_seconds"] += elapsed
            response = solver.response_proto
            values = list(response.solution)
            if values:
                save(sub / "candidate.json", values)
                round_record.update(candidate_sha256=digest(sub / "candidate.json"), candidate_values_sha256=value_sha(values))
            (sub / "response.pbtxt").write_text(str(response))
            round_record.update(status="MASTER_CALL_RETURNED", native_status=solver.status_name(status),
                                native_seconds=elapsed, native_overrun_seconds=max(0, elapsed - budget),
                                cumulative_native_seconds=result["CP_solve_seconds"], response_sha256=digest(sub / "response.pbtxt"))
            save(sub / "iteration.json", round_record)
            save(directory / "result.json", result)
            stage("master_returned_and_vector_saved_%02d" % index)
            if elapsed > budget or result["CP_solve_seconds"] > TOTAL_CP_SECONDS:
                result["status"] = "UNKNOWN_NATIVE_BUDGET_OVERRUN"
                break
            if status not in (cp.FEASIBLE, cp.OPTIMAL):
                result["status"] = ("UNPROVED_NATIVE_INFEASIBLE" if status == cp.INFEASIBLE else
                                    "ERROR_NATIVE_MODEL_INVALID" if status == cp.MODEL_INVALID else "UNKNOWN_MASTER_NATIVE")
                break
            check = inspect_candidate(h, ctx, values, plan, cuts, registry)
            save(sub / "direct-check.json", check)
            selected = check["original"]["selected"]
            save(sub / "selection.json", selected)
            round_record.update(direct_checked=True, direct_check_sha256=digest(sub / "direct-check.json"),
                                selection_sha256=digest(sub / "selection.json"), status="EXACT_MASTER_SAT_ORACLE_PENDING")
            save(sub / "iteration.json", round_record)
            matching = ctx["matching"].check_selection(ctx["matching_context"], selected)
            save(sub / "matching.json", matching)
            round_record["matching_sha256"] = digest(sub / "matching.json")
            save(sub / "iteration.json", round_record)
            proposals = h.matching_rows(matching, {"kind": "matching", "iteration": index,
                                                   "certificate_sha256": round_record["matching_sha256"]})
            if not proposals:
                allowance = max(0.0, min(SHARED_SECONDS, deadline - time.monotonic() - RESERVE))
                round_record["shared_allowance"] = allowance
                if allowance <= 0:
                    result["status"] = "MASTER_SAT_SHARED_ORACLE_NOT_RUN_BUDGET"
                    save(sub / "iteration.json", round_record)
                    break
                round_record.update(status="EXACT_MASTER_SAT_SHARED_ORACLE_ACTIVE", shared_allowance=allowance)
                save(sub / "iteration.json", round_record)
                shared = ctx["separator"].query(selected, ctx["triples"], ctx["targets"], ctx["neighbors"],
                                                sub / "shared.json", round_record["selection_sha256"], allowance)
                ctx["separator"].replay(shared, selected, ctx["triples"], ctx["targets"], ctx["neighbors"])
                result["shared_optimizer_calls"] += shared["optimizer_calls"]
                round_record.update(shared_completed=True, shared_sha256=digest(sub / "shared.json"))
                save(sub / "iteration.json", round_record)
                save(directory / "result.json", result)
                if shared["cooperative_budget_overrun_seconds"] > 0:
                    result["status"] = "MASTER_SAT_SHARED_ORACLE_BUDGET_OVERRUN"
                    break
                if shared["exact_linear_feasibility"]:
                    result.update(status="EXACT_MASTER_SAT_AND_SHARED_BOX_FEASIBLE", stopped_selection_sha256=round_record["selection_sha256"])
                    break
                if not shared["exact_fixed_design_infeasibility"]:
                    result.update(status="MASTER_SAT_SHARED_ORACLE_UNRESOLVED", stopped_selection_sha256=round_record["selection_sha256"])
                    break
                potentials = shared["fixed_capacity_potentials"]["integer_potentials60_by18"]
                lifted = ctx["separator"].lift(selected, potentials, ctx["triples"], ctx["targets"], ctx["neighbors"], ctx["actions"])
                save(sub / "universal-cuts.json", lifted)
                round_record["universal_cuts_sha256"] = digest(sub / "universal-cuts.json")
                save(sub / "iteration.json", round_record)
                proposals = h.shared_rows(lifted, {"kind": "shared", "iteration": index,
                                                  "certificate_sha256": round_record["universal_cuts_sha256"]})
            save(sub / "proposed-cuts.json", proposals)
            round_record["proposals_sha256"] = digest(sub / "proposed-cuts.json")
            save(sub / "iteration.json", round_record)
            assert any(sum(c * values[j] for j, c in row["terms"]) > row["rhs"] for row, _ in proposals)
            try:
                following, additions = h.add_rows(registry, proposals)
            except OverflowError as error:
                result.update(status="MASTER_SAT_EXACT_CUT_ENCODING_LIMIT", encoding_limit=str(error))
                save(sub / "iteration.json", round_record)
                break
            assert additions, "a checked violated cut cannot already be in a satisfied prefix"
            transition = {"before_registry_sha256": value_sha(registry), "after_registry_sha256": value_sha(following),
                          "proposals_sha256": digest(sub / "proposed-cuts.json"), "additions": additions}
            save(sub / "transition.json", transition)
            registry = following
            save(directory / "registry.json", registry)
            h.append_expected(proto, additions)
            h.append_native(cp, model, additions)
            round_record.update(status="EXACT_REFUTATION_AND_STRICT_CUT_GROWTH", transition_sha256=digest(sub / "transition.json"),
                                new_rows=len(additions), next_registry_rows=len(registry))
            save(sub / "iteration.json", round_record)
            result["status"] = "ITERATION_LIMIT_WITH_UNQUERIED_GROWN_PREFIX"
            save(directory / "result.json", result)
            stage("exact_cut_batch_committed_%02d" % index)
    except Exception:
        result["status"] = "ERROR_PRESERVED_PREFIX_AND_ANY_CANDIDATE"
        raise
    finally:
        result.update(final_registry_rows=len(registry), final_registry_sha256=value_sha(registry))
        save(directory / "result.json", result)
    return result


def replay(config_path, preparation, saved_directory, directory, deadline, stage):
    from google.protobuf import text_format
    from ortools.sat import sat_parameters_pb2
    h, ctx, plan, cuts, cp, pb, proto, _, initial = initialize(config_path, directory, stage, False)
    prep_sha = preparation_check(preparation, ctx, initial)
    owner = json.loads((saved_directory / "owner.json").read_bytes())
    assert owner["source_sha256"] == digest(__file__) and owner["maximum_seconds"] == OWNER_SECONDS
    accepted = owner["report_accepted"] is True
    result_path = saved_directory / "result.json"
    if not result_path.exists():
        assert not accepted
        return {"status": "PASS_ZERO_CALL_FAILURE_BINDING", "run_owner_sha256": digest(saved_directory / "owner.json"),
                "optimizer_calls": 0, "run_outcome_relabelled": False}
    result = json.loads(result_path.read_bytes())
    assert result["source_sha256"] == digest(__file__) and result["seed_configuration_sha256"] == digest(config_path)
    if "definition" in result:
        assert result["definition"] == json.loads(canonical(definition(ctx))) and result["query_preparation_sha256"] == prep_sha
    if accepted:
        assert owner["report_sha256"] == digest(result_path) and owner["deadline_overrun_seconds"] == 0
        assert owner["status"] == result["status"] and owner["supervision"]["status"] == "CHILD_EXITED"
        assert owner["supervision"]["child_reaped"] and owner["supervision"]["returncode"] == 0
    assert result["native_INFEASIBLE_is_unproved"] and not result["whole_component_excluded"]
    assert not result["graph_constructed"] and not result["automatic_same_prefix_retry"]
    names = result["iterations"]
    assert names == ["iteration-%02d" % i for i in range(len(names))] and len(names) <= ITERATIONS
    assert result["production_solve_calls"] == len(names)
    registry, used, previous, replayed, known_prefixes = ctx["registry"], 0.0, -1, [], {value_sha(ctx["registry"])}
    records, shared_calls, last_shared, encoding_refused = [], 0, None, False
    for index, name in enumerate(names):
        sub = saved_directory / name
        record = json.loads((sub / "iteration.json").read_bytes())
        records.append(record)
        assert record["index"] == index and record["registry_rows"] == len(registry) > previous
        previous = len(registry)
        assert record["registry_sha256"] == value_sha(registry)
        assert json.loads((sub / "registry-prefix.json").read_bytes()) == registry
        archived = (sub / "prefix.pb.gz").read_bytes()
        assert hashlib.sha256(archived).hexdigest() == record["prefix"]["archive_sha256"]
        actual = gzip.decompress(archived)
        assert actual == proto.SerializeToString() and hashlib.sha256(actual).hexdigest() == record["prefix"]["raw_sha256"]
        assert record["prefix"]["rows"] == len(proto.constraints) == 4681 + len(registry)
        params_raw = (sub / "parameters.pbtxt").read_bytes()
        assert hashlib.sha256(params_raw).hexdigest() == record["parameters_sha256"]
        params = sat_parameters_pb2.SatParameters()
        text_format.Parse(params_raw.decode(), params)
        expected_params = {"num_search_workers": 1, "random_seed": 0, "cp_model_probing_level": 0,
                           "linearization_level": 0, "max_time_in_seconds": record["native_budget"],
                           "log_search_progress": True, "log_to_stdout": True}
        assert {f.name: v for f, v in params.ListFields()} == expected_params
        assert 0 < record["native_budget"] <= min(CALL_SECONDS, TOTAL_CP_SECONDS - used)
        assert record["native_budget"] <= record["remaining_owner_at_budget_allocation"] - RESERVE
        if "native_status" not in record:
            assert not accepted and index == len(names) - 1
            pending = {"index": index, "status": "UNFINISHED_NATIVE_CALL_BOUND"}
            if (sub / "candidate.json").exists():
                values = json.loads((sub / "candidate.json").read_bytes())
                pending["pending_candidate_sha256"] = digest(sub / "candidate.json")
                try:
                    check = inspect_candidate(h, ctx, values, plan, cuts, registry)
                    save(directory / (name + "-pending-candidate-check.json"), check)
                    pending["pending_candidate_direct_check"] = "PASS_ARITHMETIC_ONLY_NOT_RUN_ACCEPTANCE"
                except (AssertionError, ValueError, TypeError) as error:
                    pending["pending_candidate_direct_check"] = "REJECTED"
                    pending["pending_candidate_error"] = str(error)
            replayed.append(pending)
            break
        response_raw = (sub / "response.pbtxt").read_bytes()
        assert hashlib.sha256(response_raw).hexdigest() == record["response_sha256"]
        response = pb.CpSolverResponse()
        text_format.Parse(response_raw.decode(), response)
        assert pb.CpSolverStatus.Name(response.status) == record["native_status"]
        elapsed = record["native_seconds"]
        assert isfinite(elapsed) and elapsed >= 0
        used += elapsed
        assert used == record["cumulative_native_seconds"]
        assert record["native_overrun_seconds"] == max(0, elapsed - record["native_budget"])
        proposed = None
        if (sub / "candidate.json").exists():
            values = json.loads((sub / "candidate.json").read_bytes())
            assert list(response.solution) == values
            assert record["candidate_sha256"] == digest(sub / "candidate.json") and record["candidate_values_sha256"] == value_sha(values)
            try:
                check = inspect_candidate(h, ctx, values, plan, cuts, registry)
            except (AssertionError, ValueError, TypeError) as error:
                assert not record["direct_checked"] and not (sub / "transition.json").exists()
                check = {"status": "REJECTED_UNACCEPTED_SAVED_VECTOR", "error": str(error)}
            save(directory / (name + "-candidate-check.json"), check)
            if record["direct_checked"]:
                assert record["direct_check_sha256"] == digest(sub / "direct-check.json")
                assert json.loads((sub / "direct-check.json").read_bytes()) == check
                selected = check["original"]["selected"]
                assert selected == json.loads((sub / "selection.json").read_bytes())
                assert digest(sub / "selection.json") == record["selection_sha256"]
                assert record["native_status"] in ("OPTIMAL", "FEASIBLE") and record["native_overrun_seconds"] == 0
                if "matching_sha256" in record:
                    matching = ctx["matching"].check_selection(ctx["matching_context"], selected)
                    assert digest(sub / "matching.json") == record["matching_sha256"]
                    assert matching == json.loads((sub / "matching.json").read_bytes())
                    proposed = h.matching_rows(matching, {"kind": "matching", "iteration": index,
                                                          "certificate_sha256": record["matching_sha256"]})
                if record["shared_completed"]:
                    assert proposed == []
                    shared = json.loads((sub / "shared.json").read_bytes())
                    last_shared = shared
                    assert digest(sub / "shared.json") == record["shared_sha256"]
                    assert shared["candidate_sha256"] == record["selection_sha256"]
                    assert shared["requested_seconds"] == record["shared_allowance"] <= SHARED_SECONDS
                    ctx["separator"].replay(shared, selected, ctx["triples"], ctx["targets"], ctx["neighbors"])
                    shared_calls += shared["optimizer_calls"]
                    if "universal_cuts_sha256" in record:
                        assert shared["exact_fixed_design_infeasibility"] and shared["cooperative_budget_overrun_seconds"] == 0
                        vectors = shared["fixed_capacity_potentials"]["integer_potentials60_by18"]
                        lifted = ctx["separator"].lift(selected, vectors, ctx["triples"], ctx["targets"], ctx["neighbors"], ctx["actions"])
                        assert digest(sub / "universal-cuts.json") == record["universal_cuts_sha256"]
                        assert lifted == json.loads((sub / "universal-cuts.json").read_bytes())
                        proposed = h.shared_rows(lifted, {"kind": "shared", "iteration": index,
                                                         "certificate_sha256": record["universal_cuts_sha256"]})
        else:
            assert not response.solution and not record["direct_checked"]
        if (sub / "proposed-cuts.json").exists():
            assert proposed and record["direct_checked"]
            assert digest(sub / "proposed-cuts.json") == record["proposals_sha256"]
            assert json.loads((sub / "proposed-cuts.json").read_bytes()) == json.loads(canonical(proposed))
        if (sub / "transition.json").exists():
            assert proposed and record["direct_checked"] and used <= TOTAL_CP_SECONDS
            assert any(sum(c * values[j] for j, c in row["terms"]) > row["rhs"] for row, _ in proposed)
            assert json.loads((sub / "proposed-cuts.json").read_bytes()) == json.loads(canonical(proposed))
            following, additions = h.add_rows(registry, proposed)
            assert additions
            transition = {"before_registry_sha256": value_sha(registry), "after_registry_sha256": value_sha(following),
                          "proposals_sha256": digest(sub / "proposed-cuts.json"), "additions": additions}
            assert transition == json.loads((sub / "transition.json").read_bytes())
            if "transition_sha256" in record:
                assert record["transition_sha256"] == digest(sub / "transition.json")
            registry = following
            h.append_expected(proto, additions)
            known_prefixes.add(value_sha(registry))
        else:
            assert index == len(names) - 1, "a second master call requires exact cut growth"
            if result["status"] == "MASTER_SAT_EXACT_CUT_ENCODING_LIMIT":
                assert proposed
                try:
                    h.add_rows(registry, proposed)
                except OverflowError as error:
                    assert str(error) == result["encoding_limit"]
                    encoding_refused = True
                else:
                    raise AssertionError("claimed encoding refusal did not replay")
        replayed.append({"index": index, "native_status": record["native_status"],
                         "direct_candidate_checked": record["direct_checked"], "following_registry_rows": len(registry)})
        stage("exact_prefix_candidate_and_oracle_replayed_%02d" % index)
    if (saved_directory / "registry.json").exists():
        saved_registry = json.loads((saved_directory / "registry.json").read_bytes())
        assert value_sha(saved_registry) in known_prefixes
        if accepted:
            assert saved_registry == registry and result["final_registry_sha256"] == value_sha(registry)
            assert result["final_registry_rows"] == len(registry) and result["CP_solve_seconds"] == used
    if accepted:
        assert result["shared_optimizer_calls"] == shared_calls
        assert shared_calls <= 2 * len(records)
        status, last = result["status"], records[-1] if records else {}
        if status == "UNKNOWN_MASTER_OR_OWNER_BUDGET":
            stop = result["budget_stop"]
            assert stop["remaining_native"] == TOTAL_CP_SECONDS - used
            assert min(stop.values()) <= 0
        elif status == "UNKNOWN_NATIVE_BUDGET_OVERRUN":
            assert last["native_overrun_seconds"] > 0 or used > TOTAL_CP_SECONDS
        elif status in ("UNPROVED_NATIVE_INFEASIBLE", "UNKNOWN_MASTER_NATIVE", "ERROR_NATIVE_MODEL_INVALID"):
            assert last["native_status"] == {"UNPROVED_NATIVE_INFEASIBLE": "INFEASIBLE",
                "UNKNOWN_MASTER_NATIVE": "UNKNOWN", "ERROR_NATIVE_MODEL_INVALID": "MODEL_INVALID"}[status]
        elif status == "MASTER_SAT_SHARED_ORACLE_NOT_RUN_BUDGET":
            assert last["direct_checked"] and not last["shared_completed"] and last["shared_allowance"] == 0
        elif status == "MASTER_SAT_SHARED_ORACLE_BUDGET_OVERRUN":
            assert last["direct_checked"] and last["shared_completed"] and last_shared["cooperative_budget_overrun_seconds"] > 0
        elif status in ("EXACT_MASTER_SAT_AND_SHARED_BOX_FEASIBLE", "MASTER_SAT_SHARED_ORACLE_UNRESOLVED"):
            assert last["direct_checked"] and last["shared_completed"] and last_shared["cooperative_budget_overrun_seconds"] == 0
            assert result["stopped_selection_sha256"] == last["selection_sha256"]
            assert not last_shared["exact_fixed_design_infeasibility"]
            assert last_shared["exact_linear_feasibility"] == (status == "EXACT_MASTER_SAT_AND_SHARED_BOX_FEASIBLE")
        elif status == "MASTER_SAT_EXACT_CUT_ENCODING_LIMIT":
            assert encoding_refused
        elif status == "ITERATION_LIMIT_WITH_UNQUERIED_GROWN_PREFIX":
            assert len(records) == ITERATIONS and last["status"] == "EXACT_REFUTATION_AND_STRICT_CUT_GROWTH"
        else:
            raise AssertionError("unsupported accepted terminal status: " + status)
    save(directory / "replayed-registry.json", registry)
    return {"status": "PASS_COMPLETE_CALLED_PREFIXES_AND_EXACT_CERTIFICATES", "definition": definition(ctx),
            "run_result_sha256": digest(result_path), "run_owner_sha256": digest(saved_directory / "owner.json"),
            "original_run_status": result["status"], "run_owner_accepted": accepted, "iterations": replayed,
            "final_replayed_registry_sha256": value_sha(registry), "final_replayed_registry_rows": len(registry),
            "native_INFEASIBLE_remains_unproved": True, "run_outcome_relabelled": False,
            "optimizer_calls": 0, "CpSolver_constructed": False, "graph_constructed": False}


def worker(mode, config_path, preparation, saved_directory, directory, deadline):
    started, stages = time.monotonic(), []
    def stage(name):
        stages.append({"stage": name, "seconds": time.monotonic() - started,
                       "peak_rss_KiB": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss})
        save(directory / "stages.json", stages)
        if time.monotonic() >= deadline:
            raise TimeoutError("direct master owned deadline")
    try:
        stage("started")
        if mode == "prepare":
            report = prepare(config_path, directory, deadline, stage)
        elif mode == "run":
            report = run(config_path, preparation, directory, deadline, stage)
        else:
            report = replay(config_path, preparation, saved_directory, directory, deadline, stage)
        report.update(seconds=time.monotonic() - started, peak_rss_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        save(directory / ("result.json" if mode == "run" else "report.json"), report)
    except Exception as error:
        save(directory / "error.json", {"type": type(error).__name__, "message": str(error)})
        raise


def owned(mode, config_path, directory, preparation=None, saved_directory=None):
    started = time.monotonic()
    limit = OWNER_SECONDS if mode == "run" else PREP_SECONDS if mode == "prepare" else COLD_SECONDS
    directory.mkdir(parents=True, exist_ok=False)
    command = [sys.executable, str(Path(__file__).resolve()), "_" + mode, "--configuration", str(config_path.resolve()),
               "--directory", str(directory.resolve()), "--deadline", str(started + limit)]
    if preparation is not None:
        command += ["--preparation", str(preparation.resolve())]
    if saved_directory is not None:
        command += ["--saved-directory", str(saved_directory.resolve())]
    save(directory / "owner.json", {"status": "UNKNOWN_BEFORE_CHILD", "report_accepted": False})
    supervision = helper().source("supervisor").supervise(command, directory, started + limit)
    owner = {"source_sha256": digest(__file__), "maximum_seconds": limit, "supervision": supervision,
             "status": supervision["status"], "report_accepted": False, "whole_component_excluded": False}
    path = directory / ("result.json" if mode == "run" else "report.json")
    if supervision["status"] == "CHILD_EXITED" and time.monotonic() <= started + limit:
        report = json.loads(path.read_bytes())
        owner.update(report_accepted=True, report_sha256=digest(path), status=report["status"])
    owner.update(seconds=time.monotonic() - started, deadline_overrun_seconds=max(0, time.monotonic() - started - limit))
    if owner["deadline_overrun_seconds"]:
        owner.update(report_accepted=False, status="UNKNOWN_HARD_DEADLINE")
    save(directory / "owner.json", owner)
    print(json.dumps(owner, sort_keys=True), flush=True)


if __name__ == "__main__":
    if not __debug__:
        raise RuntimeError("assertions required")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "run", "cold", "_prepare", "_run", "_cold"))
    parser.add_argument("--configuration", type=Path, required=True)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--preparation", type=Path)
    parser.add_argument("--saved-directory", type=Path)
    parser.add_argument("--deadline", type=float)
    args = parser.parse_args()
    if args.mode.startswith("_"):
        assert args.deadline is not None
        worker(args.mode[1:], args.configuration, args.preparation, args.saved_directory, args.directory, args.deadline)
    else:
        assert args.mode == "prepare" or args.preparation is not None
        assert args.mode != "cold" or args.saved_directory is not None
        owned(args.mode, args.configuration, args.directory, args.preparation, args.saved_directory)
