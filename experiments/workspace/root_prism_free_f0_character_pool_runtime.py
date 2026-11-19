"""Lightweight archived-protobuf loader and owned initialization-only test.

The child does not import the mathematical model builder or reconstruct its
large specification JSON. The three public-transcription helpers below are
AST-identical to the reviewed builder. No CpSolver is constructed or called.
"""
import argparse
from collections import Counter
import gc
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import resource
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
LOGS = ROOT / "experiments/logs/root-prism-free"
MODEL_SOURCE = "experiments/workspace/root_prism_free_f0_character_pool_model.py"
MODEL_SOURCE_SHA = "b3029a3a197ec31305f74dead2b28f51beaf219cb2e9e289dc8f250db42a6943"
SUPERVISOR_SOURCE = "experiments/workspace/root_prism_free_f0_local_neighbors_batch.py"
SUPERVISOR_SHA = "b8e5323f92fa105ff2c0ed5b1667ac25d7c92f85f8cac45b170ddc56208f8278"
CP_MODEL_SHA = "b5f2a3ae5c418d11af23cb77a766fa10103c8bb71703dafa1ecad74823603f25"
TARGET_SHA = "0612fd82507ac454209ba5f376654248461fc8c0506b9a4a382f5e628487d9ae"
INITIAL_SHA = "36bd4fe3650ede346bab0885abcb9cef7a96cb0e150dffc8fcf51bbe695e7d4d"
SECONDS = 60
INPUTS = {
    "model_preparation": ("f0-character-pool-model01/report.json", "ed912b419cdfe1a4b4b228382ec1cfbb58a7688476c06ea14e851a3290992f30"),
    "model_cold": ("f0-character-pool-model01-cold.json", "24a450d6d6c3bf537e6c049aaad2bf843e154a0586e463a2fc14eaff48eac2c8"),
    "model_root_review": ("f0-character-pool-model-root-source-review.json", "009257a87f45c480e741961d3329174b33c263849911d3da185ff36669470bbf"),
    "full_query_preflight": ("f0-character-pool-query-preflight01.json", "41d9e155a23f7e40546b3e546e975b2ac6434a4fae28b4e95ff8faa58becb272"),
    "plan": ("f0-character-pool-model01/plan.json.gz", "b3179e520d5913530c7d3cfae27529b5717be26c763de024b725c38959aa2aef"),
    "target": ("f0-character-pool-model01/target.pb.gz", "1a26b2ec303121e44d0100a586c568ba85387137341ccd503471a6994cba1a2f"),
    "initial": ("f0-character-pool-model01/initial.pb.gz", "5710bf3f31c076d8afa4cfc6f2207123d25d53d19dcc284607102de1a3f22dac"),
}
cp_model = None
cp_model_pb2 = None


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def file_sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def save(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(canonical(value) + b"\n")
    temporary.replace(path)


def memory_snapshot():
    current, proc_peak = None, None
    status = Path("/proc/self/status")
    if status.exists():
        for line in status.read_text().splitlines():
            if line.startswith("VmRSS:"):
                current = int(line.split()[1])
            elif line.startswith("VmHWM:"):
                proc_peak = int(line.split()[1])
    return {"current_rss_KiB": current, "proc_peak_rss_KiB": proc_peak,
            "getrusage_peak_rss_KiB": int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)}


def definition():
    assert file_sha(ROOT / MODEL_SOURCE) == MODEL_SOURCE_SHA
    assert file_sha(ROOT / SUPERVISOR_SOURCE) == SUPERVISOR_SHA
    for name, expected in INPUTS.values():
        assert file_sha(LOGS / name) == expected
    return {"schema": "conway99.f0-lightweight-native-initialization.v1",
            "source_sha256": file_sha(Path(__file__)),
            "reviewed_model_source": {"path": MODEL_SOURCE, "sha256": MODEL_SOURCE_SHA},
            "supervisor_source": {"path": SUPERVISOR_SOURCE, "sha256": SUPERVISOR_SHA},
            "inputs": {k: {"path": str((LOGS / p).relative_to(ROOT)), "sha256": h} for k, (p, h) in INPUTS.items()},
            "target_proto_sha256": TARGET_SHA, "initial_proto_sha256": INITIAL_SHA,
            "maximum_owned_initialization_seconds": SECONDS,
            "ortools_version": "9.15.6755", "installed_cp_model_source_sha256": CP_MODEL_SHA,
            "mathematical_builder_import_or_load_inputs_or_derive_called": False,
            "large_specification_JSON_loaded": False,
            "only_plan_and_target_initial_archives_are_decompressed": True,
            "native_public_construction_validation_and_byte_identity_required": True,
            "durable_current_and_peak_RSS_per_stage": True,
            "optimizer_calls": 0, "CpSolver_constructed": False,
            "future_target_witness_is_provisional_until_separate_original_parent_check": True,
            "production_query_authorized_by_this_preparation": False}


def reuse_controls():
    import ast
    def functions(text):
        return {node.name: ast.dump(node, include_attributes=False)
                for node in ast.parse(text).body if isinstance(node, ast.FunctionDef)}
    old = functions((ROOT / MODEL_SOURCE).read_text())
    new = functions(Path(__file__).read_text())
    copied = ["single_variable", "table_data", "append_constraint", "exact_proto_check"]
    assert all(old[name] == new[name] for name in copied)
    return {"status": "PASS", "complete_AST_identical_public_helpers": copied,
            "subject_builder_imported": False, "native_libraries_imported": False,
            "model_or_plan_archives_decompressed": False, "optimizer_calls": 0}


def checked_preparation(path):
    raw = path.read_bytes()
    record = json.loads(raw)
    assert record["status"] == "PASS: lightweight initialization preparation; no native import or build"
    assert record["definition"] == definition()
    assert record["reuse_controls"]["status"] == "PASS"
    return record, sha(raw)


def import_native(stage):
    global cp_model, cp_model_pb2
    stage("before_native_import")
    import ortools
    from ortools.sat import cp_model_pb2 as protobuf_module
    from ortools.sat.python import cp_model as native_module
    assert ortools.__version__ == "9.15.6755"
    assert file_sha(Path(native_module.__file__)) == CP_MODEL_SHA
    cp_model, cp_model_pb2 = native_module, protobuf_module
    stage("native_import_complete")


def single_variable(expression):
    assert list(expression.coeffs) == [1] and len(expression.vars) == 1 and expression.offset == 0
    assert expression.vars[0] >= 0
    return expression.vars[0]


def table_data(constraint):
    assert {f.name for f, _ in constraint.ListFields()} == {"table"}
    table = constraint.table
    assert not table.negated and not table.vars
    columns = [single_variable(e) for e in table.exprs]
    assert columns and len(set(columns)) == len(columns)
    width = len(columns)
    assert len(table.values) % width == 0
    tuples = [tuple(table.values[i:i + width]) for i in range(0, len(table.values), width)]
    assert tuples and len(tuples) == len(set(tuples))
    return columns, tuples


def append_constraint(model, variables, constraint):
    kind = constraint.WhichOneof("constraint")
    assert {f.name for f, _ in constraint.ListFields()} == {kind}
    if kind == "linear":
        row = constraint.linear
        assert row.vars and all(j >= 0 for j in row.vars)
        expression = cp_model.LinearExpr.weighted_sum([variables[j] for j in row.vars], list(row.coeffs))
        model.add_linear_expression_in_domain(expression, cp_model.Domain.from_flat_intervals(list(row.domain)))
    elif kind == "int_prod":
        row = constraint.int_prod
        assert len(row.exprs) == 2
        model.add_multiplication_equality(variables[single_variable(row.target)],
                                          [variables[single_variable(e)] for e in row.exprs])
    else:
        assert kind == "table"
        columns, tuples = table_data(constraint)
        model.add_allowed_assignments([variables[j] for j in columns], tuples)


def exact_proto_check(proto, target, row_ids):
    assert {f.name for f, _ in proto.ListFields()} == {"variables", "constraints"}
    assert len(proto.variables) == len(target.variables) and len(proto.constraints) == len(row_ids)
    assert list(proto.variables) == list(target.variables)
    assert all(actual == target.constraints[i] for actual, i in zip(proto.constraints, row_ids))
    census, terms, largest = Counter(), 0, 0
    magnitude = [max(abs(v.domain[0]), abs(v.domain[-1])) for v in proto.variables]
    for constraint in proto.constraints:
        kind = constraint.WhichOneof("constraint")
        census[kind] += 1
        if kind == "linear":
            row = constraint.linear
            assert len(row.vars) == len(row.coeffs) == len(set(row.vars))
            bound = sum(abs(c) * magnitude[j] for j, c in zip(row.vars, row.coeffs))
            assert bound < 1 << 62
            assert all(-(1 << 63) <= v < (1 << 63) for v in list(row.coeffs) + list(row.domain))
            largest = max(largest, bound)
            terms += len(row.vars)
        elif kind == "int_prod":
            factors = [single_variable(e) for e in constraint.int_prod.exprs]
            assert len(factors) == 2 and magnitude[factors[0]] * magnitude[factors[1]] < 1 << 62
        else:
            assert kind == "table"
            table_data(constraint)
    return {"variables": len(proto.variables), "constraints": len(proto.constraints),
            "constraint_types": dict(census), "linear_terms": terms,
            "maximum_linear_absolute_box_sum": largest,
            "all_row_coefficients_endpoints_and_product_domains_fit_signed64": True,
            "every_variable_and_constraint_compared_exactly": True,
            "objective_hints_assumptions_enforcements_or_strategy_added": False}


def load_runtime(stage):
    model = json.loads((LOGS / INPUTS["model_preparation"][0]).read_bytes())
    cold = json.loads((LOGS / INPUTS["model_cold"][0]).read_bytes())
    preflight = json.loads((LOGS / INPUTS["full_query_preflight"][0]).read_bytes())
    assert model["source_sha256"] == MODEL_SOURCE_SHA
    assert cold["preparation_sha256"] == INPUTS["model_preparation"][1]
    assert preflight["target_proto_sha256"] == TARGET_SHA and preflight["initial_proto_sha256"] == INITIAL_SHA
    assert preflight["status"] == "PASS: exact external-row query cold preflight"
    stage("bound_small_records_loaded")
    payload = (LOGS / INPUTS["plan"][0]).read_bytes()
    assert sha(payload) == INPUTS["plan"][1]
    full_plan = json.loads(gzip.decompress(payload))
    assert full_plan["source_sha256"] == MODEL_SOURCE_SHA
    assert full_plan["variable_count"] == 18444 and full_plan["full_target_constraints"] == 34398
    assert full_plan["initial_constraints"] == 34281 and full_plan["external_pool_constraints"] == 117
    keys = ("source_sha256", "variable_count", "full_target_constraints", "initial_constraints",
            "initial_to_target_rows", "external_pool", "target_variable_domains")
    plan = {key: full_plan[key] for key in keys}
    del payload, full_plan
    gc.collect()
    stage("runtime_plan_loaded_unused_witness_objects_released")
    protos = {}
    for name, expected in (("target", TARGET_SHA), ("initial", INITIAL_SHA)):
        payload = (LOGS / INPUTS[name][0]).read_bytes()
        assert sha(payload) == INPUTS[name][1]
        stage(name + "_compressed_archive_loaded")
        raw = gzip.decompress(payload)
        assert sha(raw) == expected and len(raw) == model["models"][name]["raw_proto_bytes"]
        del payload
        stage(name + "_decompressed_hash_checked")
        proto = cp_model_pb2.CpModelProto()
        proto.ParseFromString(raw)
        del raw
        protos[name] = proto
        gc.collect()
        stage(name + "_protobuf_loaded_decompression_buffers_released")
    target, initial = protos["target"], protos["initial"]
    assert len(target.variables) == len(initial.variables) == 18444
    assert len(target.constraints) == 34398 and len(initial.constraints) == 34281
    assert {f.name for f, _ in target.ListFields()} == {"variables", "constraints"}
    assert [list(v.domain) for v in target.variables] == plan["target_variable_domains"]
    rows = plan["initial_to_target_rows"]
    assert rows == sorted(set(rows)) and len(rows) == 34281
    pool = plan["external_pool"]
    assert [r["pool_id"] for r in pool] == list(range(117))
    external_ids = [r["target_constraint"] for r in pool]
    assert len(set(external_ids)) == 117 and not set(external_ids).intersection(rows)
    assert sorted(external_ids + rows) == list(range(34398))
    for entry in pool:
        row = target.constraints[entry["target_constraint"]]
        assert row.WhichOneof("constraint") == "linear"
        assert sha(row.SerializeToString()) == entry["constraint_sha256"]
        assert len(row.linear.vars) == entry["terms"]
    checked = exact_proto_check(initial, target, rows)
    assert checked == model["models"]["initial"]["checks"]
    stage("exact_initial_embedding_domains_and_all117_pool_rows_checked")
    return plan, target, initial, checked


def worker(preparation_path, directory, deadline):
    started = time.monotonic()
    stages = []
    def stage(name, **extra):
        record = {"stage": name, "elapsed_seconds": time.monotonic() - started,
                  "memory": memory_snapshot(), **extra}
        stages.append(record)
        save(directory / "stages.json", {"source_sha256": file_sha(Path(__file__)), "stages": stages,
                                         "optimizer_calls": 0, "CpSolver_constructed": False})
        if time.monotonic() > deadline:
            raise TimeoutError("owned initialization deadline")
    result = {"status": "UNKNOWN_INITIALIZATION_NOT_COMPLETE", "optimizer_calls": 0,
              "CpSolver_constructed": False, "count_feasibility_claimed": False, "F0_excluded": False}
    try:
        stage("child_started_before_native_import")
        _, preparation_sha = checked_preparation(preparation_path)
        result["preparation_sha256"] = preparation_sha
        stage("all_source_and_compressed_input_bindings_checked")
        import_native(stage)
        plan, target, initial, checked = load_runtime(stage)
        model = cp_model.CpModel()
        variables = [model.new_int_var_from_domain(cp_model.Domain.from_flat_intervals(list(v.domain)), v.name)
                     for v in initial.variables]
        assert [v.index for v in variables] == list(range(18444))
        stage("all18444_native_variables_constructed")
        for i, constraint in enumerate(initial.constraints):
            append_constraint(model, variables, constraint)
            if (i + 1) % 4096 == 0:
                stage("native_constraint_prefix_constructed", constraints=i + 1)
        stage("all34281_native_constraints_constructed")
        assert len(model.proto.variables) == 18444 and len(model.proto.constraints) == 34281
        assert model.validate() == ""
        stage("native_validation_passed")
        path = directory / "constructed-initial.pb"
        assert model.export_to_file(str(path))
        assert file_sha(path) == INITIAL_SHA and path.stat().st_size == 3973028
        stage("native_export_exact_frozen_initial_hash_passed")
        result.update(status="PASS: lightweight native initialization; no solver",
                      raw_initial_proto_sha256=INITIAL_SHA, raw_initial_proto_bytes=3973028,
                      full_target_proto_sha256=TARGET_SHA, exact_initial_checks=checked,
                      restored_parent_acceptance_performed=False,
                      only_archived_target_plan_initial_loaded=True,
                      native_model_built_with_public_constructors=True)
    except Exception as error:
        result.update(status="ERROR_INITIALIZATION_NOT_ACCEPTED", error_type=type(error).__name__, message=str(error))
        # This snapshot survives normal exceptions; previous atomic snapshots
        # survive a signal kill even when no Python finally block can run.
        stages.append({"stage": "exception", "elapsed_seconds": time.monotonic() - started,
                       "memory": memory_snapshot(), "error_type": type(error).__name__})
        save(directory / "stages.json", {"source_sha256": file_sha(Path(__file__)), "stages": stages,
                                         "optimizer_calls": 0, "CpSolver_constructed": False})
        raise
    finally:
        result.update(child_seconds=time.monotonic() - started, terminal_memory=memory_snapshot(),
                      stages_sha256=file_sha(directory / "stages.json"))
        save(directory / "child-result.json", result)


def initialize(preparation_path, directory):
    started = time.monotonic()
    deadline = started + SECONDS
    _, preparation_sha = checked_preparation(preparation_path)
    path = ROOT / SUPERVISOR_SOURCE
    spec = importlib.util.spec_from_file_location("frozen_initialization_owner", path)
    supervisor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(supervisor)
    directory.mkdir(parents=True, exist_ok=False)
    result = {"status": "UNKNOWN_BEFORE_INITIALIZATION_CHILD", "source_sha256": file_sha(Path(__file__)),
              "preparation_sha256": preparation_sha, "maximum_owned_seconds": SECONDS,
              "optimizer_calls": 0, "CpSolver_constructed": False,
              "initialization_accepted": False, "production_query_performed": False}
    save(directory / "result.json", result)
    command = [sys.executable, str(Path(__file__).resolve()), "_worker", "--preparation", str(preparation_path.resolve()),
               "--directory", str(directory.resolve()), "--deadline", str(deadline)]
    supervision = supervisor.supervise(command, directory, deadline)
    result["supervision"] = supervision
    if supervision["status"] == "CHILD_EXITED":
        raw = (directory / "child-result.json").read_bytes()
        child = json.loads(raw)
        assert child["preparation_sha256"] == preparation_sha
        assert child["status"] == "PASS: lightweight native initialization; no solver"
        assert child["optimizer_calls"] == 0 and not child["CpSolver_constructed"]
        assert child["raw_initial_proto_sha256"] == INITIAL_SHA
        assert child["full_target_proto_sha256"] == TARGET_SHA
        assert child["stages_sha256"] == file_sha(directory / "stages.json")
        result.update(status=child["status"], initialization_accepted=True, child_result_sha256=sha(raw))
    else:
        result["status"] = supervision["status"]
        if (directory / "stages.json").exists():
            result["last_durable_stages_sha256"] = file_sha(directory / "stages.json")
    result.update(owner_seconds=time.monotonic() - started, deadline_overrun_seconds=max(0, time.monotonic() - deadline))
    save(directory / "result.json", result)
    print(json.dumps(result, indent=2), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "initialize", "_worker"))
    parser.add_argument("--preparation", type=Path)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--deadline", type=float)
    args = parser.parse_args()
    if args.mode == "prepare":
        args.directory.mkdir(parents=True, exist_ok=False)
        record = {"status": "PASS: lightweight initialization preparation; no native import or build",
                  "definition": definition(), "reuse_controls": reuse_controls(),
                  "optimizer_calls": 0, "CpSolver_constructed": False}
        save(args.directory / "preparation.json", record)
        print(json.dumps(record, indent=2), flush=True)
    elif args.mode == "initialize":
        assert args.preparation is not None
        initialize(args.preparation, args.directory)
    else:
        assert args.preparation is not None and args.deadline is not None
        worker(args.preparation, args.directory, args.deadline)
