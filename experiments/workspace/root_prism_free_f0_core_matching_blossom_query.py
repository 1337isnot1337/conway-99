"""No-LP external-row search on the Fourier/literal target with 6,854 blossom rows.

Only archived plan/protobuf data are loaded in the search child. A target-
passing integer vector is PROVISIONAL until a separate restored-parent
arithmetic check and literal decoder. One owned300-second budget, at most
180 cumulative native seconds, 12 calls and16 exact violated rows per returned
vector; no unchanged-prefix retry.
"""
import argparse
import ast
import gc
import gzip
import hashlib
import importlib.util
import json
from math import isfinite
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
LOGS = ROOT / "experiments/logs/root-prism-free"
SOURCES = {'prior_no_lp_query': ('root_prism_free_f0_character_packing_no_lp_query.py',
                       'f3f704371307da14ab035eed1b2a7345bb1725babf0f01cc8e06d5b7e26475e7'),
 'prior_light_query': ('root_prism_free_f0_character_packing_light_query.py',
                       '255cc48bb3f5e8bbbcb8180b9cb024c5e92ce171dc29befbf35d0657ec196a69'),
 'runtime': ('root_prism_free_f0_character_pool_runtime.py',
             '030163f019b93ee39124e9f3171caac1e4ad79227fde9a1e831c28a938b245f8'),
 'model': ('root_prism_free_f0_core_matching_blossom_native_overlay.py',
           '45ec9069c1091f8c118a299f1806897fb52694f55814b01961f220443ff150b6'),
 'old_query': ('root_prism_free_f0_character_pool_query.py',
               '820f76ea30bff76e3c0d5d9b79601f6fba1ee11c0534676843315f575bafce39'),
 'old_character': ('root_prism_free_f0_character_cpsat.py',
                   '879cdb9be48f9377dd6bccd078f26a568d12467385e9ecb1d5b260cc56ff64e7'),
 'old_pool': ('root_prism_free_f0_character_pool_model.py',
              'b3029a3a197ec31305f74dead2b28f51beaf219cb2e9e289dc8f250db42a6943'),
 'supervisor': ('root_prism_free_f0_local_neighbors_batch.py',
                'b8e5323f92fa105ff2c0ed5b1667ac25d7c92f85f8cac45b170ddc56208f8278')}
INPUTS = {'blossom_overlay_root_review': ('f0-core-matching-blossom-native-overlay-root-gate01.json',
                                  '0bf104de680d172a50ca10d54a4b82e5025f9cb059f97be608e85ae26f45afd0'),
 'prior_no_lp_query_root_review': ('f0-character-packing-no-lp-root-source-review.json',
                                   '760b83c211d696d1b22eeb222952696cddf9bb87af2d3ffb19fb8d8765423275'),
 'model_preparation': ('f0-core-matching-blossom-native-overlay02/report.json',
                       'ddd0eac97aac5741a60778276ac1798240089a547ffb43a77629fb8736114d4e'),
 'model_cold': ('f0-core-matching-blossom-native-overlay02-cold/report.json',
                '268a2d4f97f4436823f4d36271425c856ad770f5877667941b13e403f5b9166f'),
 'native_owner': ('f0-core-matching-blossom-native-overlay02/owner-result.json',
                  '24c55ddb539e24234d44a09138fe4867da8701d5c7094e95e3285e4f02f12c3d'),
 'cold_owner': ('f0-core-matching-blossom-native-overlay02-cold/owner-result.json',
                '74ba6be30bbbacbce70e9dc7d46d8ab511cb8672157b9f45f4ad07248448871a'),
 'native_v2_root_review': ('f0-full-fourier-native-v2-root-source-review.json',
                           '0ef8d80ba79376fd3fd179857fcade823f2bf5c61f579d3b5a4cb24540191196'),
 'native_root_review': ('f0-full-fourier-native-root-source-review01.json',
                        '2741de4261e7fd3be287eae22dabc3e2a2f1261314043680471c1f13e3746f70'),
 'native_peer_review': ('f0-full-fourier-native-independent-source-review.json',
                        '05c99a3d72b3c5de376dca1ce110e96cbafa443d151318c78046371e9d154329'),
 'plan': ('f0-core-matching-blossom-native-overlay02/plan.json.gz',
          '0aeb8cd5a53362f68dff836a9792c1ccea17bef349bf4389f92ed90479032502'),
 'target_archive': ('f0-core-matching-blossom-native-overlay02/target.pb.gz',
                    'fe349215460dcf8e609d1381e357e14c6f5b7fb21ea896f59bddc91b707133a9'),
 'initial_archive': ('f0-core-matching-blossom-native-overlay02/initial.pb.gz',
                     '1f633c70a669badb8d151a7696d744c194b8ed649b4a6f90a0ea7b8142efb7ee'),
 'prior_query_controls': ('f0-character-pool-query-preparation01/preparation.json',
                          '6e0812462e4ddb9b1b331d0652edc92d14da75dd4c975eb8dbc5c8cefcd95ba1'),
 'prior_no_lp_preparation': ('f0-character-packing-no-lp-query-preparation01/preparation.json',
                             '123c940a34b590c944316a2fd606e5febcf1cedbdea3ec0f828d41b115068f37')}
TARGET_SHA = '60de781b2b324c270bac9cec30c1adbc769631dc959c1a2e2414fbc5eef96ab6'
INITIAL_SHA = '940e34316ed30532aee8c192947a7d69e54ccd7e9ebf8d85a3c4ada912a7331a'
CP_MODEL_SHA = "b5f2a3ae5c418d11af23cb77a766fa10103c8bb71703dafa1ecad74823603f25"
VARIABLES = 32296
SECONDS, NATIVE_SECONDS, MAX_CALLS, MAX_APPEND, FINALIZATION_RESERVE = 300, 180, 12, 16, 8


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


def load_source(key):
    name, expected = SOURCES[key]
    path = ROOT / "experiments/workspace" / name
    assert file_sha(path) == expected
    spec = importlib.util.spec_from_file_location("frozen_light_query_" + key, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def configuration():
    sources, inputs, records = {}, {}, {}
    for key, (name, expected) in SOURCES.items():
        path = ROOT / "experiments/workspace" / name
        assert file_sha(path) == expected
        sources[key] = {"path": str(path.relative_to(ROOT)), "sha256": expected}
    for key, (name, expected) in INPUTS.items():
        path = LOGS / name
        assert file_sha(path) == expected
        inputs[key] = {"path": str(path.relative_to(ROOT)), "sha256": expected}
        if not name.endswith(".gz"):
            records[key] = json.loads(path.read_bytes())
            assert records[key]["status"].startswith("PASS")
    model = records["model_preparation"]
    assert model["definition"]["source_sha256"] == SOURCES["model"][1]
    assert records["model_cold"]["model_report_sha256"] == INPUTS["model_preparation"][1]
    assert records["native_owner"]["report_accepted"] and records["cold_owner"]["report_accepted"]
    assert records["native_owner"]["report_sha256"] == INPUTS["model_preparation"][1]
    assert records["cold_owner"]["report_sha256"] == INPUTS["model_cold"][1]
    for key, input_key in (("plan", "plan"), ("target", "target_archive"), ("initial", "initial_archive")):
        assert model["outputs"][key]["sha256"] == INPUTS[input_key][1]
        assert model["outputs"][key]["path"] == inputs[input_key]["path"]
    assert model["outputs"]["target"]["raw_sha256"] == TARGET_SHA
    assert model["outputs"]["initial"]["raw_sha256"] == INITIAL_SHA
    assert records["prior_query_controls"]["controls"]["status"] == "PASS"
    return {"schema": "conway99.f0-core-blossom-no-lp-query.v1",
            "runner_source_sha256": file_sha(Path(__file__)), "sources": sources, "inputs": inputs,
            "target_proto_sha256": TARGET_SHA, "initial_proto_sha256": INITIAL_SHA,
            "variables": 32296, "target_constraints": 65811, "initial_constraints": 65694,
            "external_rows": 117, "maximum_owned_child_seconds": SECONDS,
            "maximum_cumulative_native_solve_seconds": NATIVE_SECONDS,
            "maximum_production_solve_calls": MAX_CALLS, "maximum_rows_appended_per_candidate": MAX_APPEND,
            "finalization_reserve_seconds": FINALIZATION_RESERVE,
            "num_search_workers": 1, "random_seed": 0, "cp_model_probing_level": 0, "linearization_level": 0,
            "row_selection": "First at most16 exact violated rows in frozen pool-ID order.",
            "later_call_requires_strictly_larger_certified_prefix": True,
            "only_plan_and_target_initial_archives_loaded_in_search_child": True,
            "source_load_inputs_or_derive_and_large_specification_not_called": True,
            "durable_per_stage_current_and_peak_RSS": True,
            "candidate_saved_before_exact_checks": True,
            "candidate_JSON_format": "plain root array of32296 integers",
            "native_infeasibility_unproved_without_independent_certificate": True,
            "full_target_pass_is_PROVISIONAL_only": True,
            "count_feasibility_claimed_by_this_driver": False,
            "separate_full_restored_parent_arithmetic_receipt_required": True,
            "independent_Fourier_literal_decoder_required_before_acceptance": True,
            "native_budget_overrun_preserves_vector_without_acceptance": True,
            "owner_avoids_duplicate_archive_hashing_worker_checks_complete_configuration": True,
            "late_or_failed_child_never_accepted": True,
            "no_hints_objective_candidate_fix_or_visitation_rows": True,
            "automatic_retry": False, "warm_start_or_speedup_claimed": False,
            "ortools_version": "9.15.6755", "installed_cp_model_source_sha256": CP_MODEL_SHA}


def check_preparation(path):
    raw = path.read_bytes(); prepared = json.loads(raw)
    assert prepared["status"] == "PASS: full-Fourier literal no-LP query preparation; no optimizer"
    assert prepared["definition"] == configuration()
    assert prepared["reuse_controls"]["status"] == "PASS"
    assert prepared["optimizer_calls"] == 0 and not prepared["CpSolver_constructed"]
    return prepared, sha(raw)


def owner_preparation_binding(path):
    """Bind the small preparation in the owner; full archive checks stay in the worker."""
    raw = path.read_bytes()
    prepared = json.loads(raw)
    assert prepared["status"] == "PASS: full-Fourier literal no-LP query preparation; no optimizer"
    bound = prepared["definition"]
    assert bound["runner_source_sha256"] == file_sha(Path(__file__))
    assert bound["target_proto_sha256"] == TARGET_SHA and bound["initial_proto_sha256"] == INITIAL_SHA
    assert bound["variables"] == VARIABLES and bound["target_constraints"] == 65811
    assert bound["initial_constraints"] == 65694 and bound["external_rows"] == 117
    assert bound["maximum_owned_child_seconds"] == SECONDS
    assert bound["maximum_cumulative_native_solve_seconds"] == NATIVE_SECONDS
    assert prepared["reuse_controls"]["status"] == "PASS"
    assert prepared["optimizer_calls"] == 0 and not prepared["CpSolver_constructed"]
    return prepared, sha(raw)


def reuse_controls():
    tree = ast.parse(Path(__file__).read_text())
    functions = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}
    native = functions["native_parameters"]
    cap_names = [n for n in ast.walk(native) if isinstance(n, ast.Name) and n.id == "NATIVE_SECONDS"]
    assert len(cap_names) == 1
    cap_names[0].id = "SECONDS"
    delta = ast.dump(ast.parse("params.linearization_level = 0").body[0], include_attributes=False)
    positions = [i for i, n in enumerate(native.body) if ast.dump(n, include_attributes=False) == delta]
    assert len(positions) == 1
    native.body.pop(positions[0])
    current = {name: ast.dump(n, include_attributes=False) for name, n in functions.items()}
    groups = {"old_query": ["native_parameters", "choose_rows"],
              "old_character": ["evaluate_proto"], "old_pool": ["pool_scan"]}
    for key, names in groups.items():
        path = ROOT / "experiments/workspace" / SOURCES[key][0]
        assert file_sha(path) == SOURCES[key][1]
        old = {n.name: ast.dump(n, include_attributes=False) for n in ast.parse(path.read_text()).body
               if isinstance(n, ast.FunctionDef)}
        assert all(current[name] == old[name] for name in names)
    value = [0, -6, 36, 1 << 81, -(1 << 81)]
    assert json.loads(canonical(value)) == value
    assert sha(canonical(value)) != sha(canonical(value) + b"\n")
    return {"status": "PASS", "complete_AST_identical_helpers": groups,
            "prior118_prefix_and_native_parameter_response_controls_bound": INPUTS["prior_query_controls"][1],
            "large_signed_integer_candidate_roundtrip_checked": True,
            "candidate_file_and_canonical_value_hashes_distinguished": True,
            "native_parameter_delta": "No-LP fields unchanged; calls are clipped to the remaining180 native seconds and300 owner seconds.",
            "native_budget_controls": native_budget_controls(),
            "installed_parameter_controls": native_parameter_controls(),
            "subject_model_modules_imported": False, "optimizer_calls": 0}



def native_parameter_controls():
    """Check installed native fields and text/wire serialization, without a solver."""
    from google.protobuf import text_format
    from ortools.sat import sat_parameters_pb2
    from ortools.sat.python import cp_model
    import ortools
    assert ortools.__version__ == "9.15.6755"
    assert file_sha(Path(cp_model.__file__)) == CP_MODEL_SHA
    field = sat_parameters_pb2.SatParameters.DESCRIPTOR.fields_by_name["linearization_level"]
    checks = []
    for seconds in (0.25, 10.0, 172.0):
        native = native_parameters(cp_model.cmh, seconds)
        assert native.linearization_level == 0
        text = str(native)
        parsed = sat_parameters_pb2.SatParameters()
        text_format.Parse(text, parsed)
        expected = {"num_search_workers": 1, "random_seed": 0,
                    "cp_model_probing_level": 0, "linearization_level": 0,
                    "max_time_in_seconds": seconds, "log_search_progress": True,
                    "log_to_stdout": True}
        assert {f.name: value for f, value in parsed.ListFields()} == expected
        assert parsed.HasField("linearization_level") and parsed.linearization_level == 0
        wire = parsed.SerializeToString(deterministic=True)
        restored = sat_parameters_pb2.SatParameters()
        restored.ParseFromString(wire)
        assert restored == parsed
        checks.append({"seconds": seconds, "exact_explicit_fields": expected,
                       "text_sha256": sha(text.encode()), "wire_sha256": sha(wire)})
    return {"status": "PASS", "installed_version": ortools.__version__,
            "field_number": field.number, "field_type": field.type,
            "installed_default_linearization_level": field.default_value,
            "roundtrips": checks, "CpSolver_constructed": False,
            "model_constructed": False, "optimizer_calls": 0}


def load_target(prepared, stage=None):
    stage = (lambda *a, **k: None) if stage is None else stage
    r = load_source("runtime")
    r.import_native(stage)
    model = json.loads((LOGS / INPUTS["model_preparation"][0]).read_bytes())
    payload = (LOGS / INPUTS["plan"][0]).read_bytes()
    assert sha(payload) == INPUTS["plan"][1]
    full = json.loads(gzip.decompress(payload))
    assert full["source_sha256"] == SOURCES["model"][1]
    assert (full["variable_count"], full["full_target_constraints"], full["initial_constraints"]) == (32296,65811,65694)
    assert full["external_pool_constraints"] == 117
    keys = ("source_sha256", "variable_count", "full_target_constraints", "initial_constraints",
            "initial_to_target_rows", "external_pool", "target_variable_domains")
    plan = {key: full[key] for key in keys}
    del payload, full; gc.collect()
    stage("runtime_plan_loaded_unused_witness_objects_released")
    protos = {}
    for name, expected in (("target", TARGET_SHA), ("initial", INITIAL_SHA)):
        path = LOGS / INPUTS[name + "_archive"][0]
        payload = path.read_bytes(); assert sha(payload) == INPUTS[name + "_archive"][1]
        raw = gzip.decompress(payload); del payload
        assert sha(raw) == expected and len(raw) == model["outputs"][name]["raw_bytes"]
        proto = r.cp_model_pb2.CpModelProto(); proto.ParseFromString(raw)
        del raw; gc.collect()
        protos[name] = proto
        stage(name + "_protobuf_loaded_decompression_buffers_released")
    target, initial = protos["target"], protos["initial"]
    assert {f.name for f, _ in target.ListFields()} == {"variables", "constraints"}
    assert len(target.variables) == len(initial.variables) == 32296
    assert len(target.constraints) == 65811 and len(initial.constraints) == 65694
    assert [list(v.domain) for v in target.variables] == plan["target_variable_domains"]
    row_ids = plan["initial_to_target_rows"]
    assert row_ids == sorted(set(row_ids)) and len(row_ids) == 65694
    pool = plan["external_pool"]
    assert [row["pool_id"] for row in pool] == list(range(117))
    external_ids = [row["target_constraint"] for row in pool]
    assert len(set(external_ids)) == 117 and not set(external_ids).intersection(row_ids)
    assert sorted(external_ids + row_ids) == list(range(65811))
    for row in pool:
        constraint = target.constraints[row["target_constraint"]]
        assert constraint.WhichOneof("constraint") == "linear"
        assert sha(constraint.SerializeToString()) == row["constraint_sha256"]
        assert len(constraint.linear.vars) == row["terms"]
    checked = r.exact_proto_check(initial, target, row_ids)
    assert checked == model["native_initial_exact_checks"]
    stage("complete_initial_embedding_domains_and117_external_rows_checked")
    return r, plan, target, initial, checked


def construct_initial(r, initial, stage):
    model = r.cp_model.CpModel()
    variables = [model.new_int_var_from_domain(r.cp_model.Domain.from_flat_intervals(list(v.domain)), v.name)
                 for v in initial.variables]
    assert [v.index for v in variables] == list(range(32296))
    for i, constraint in enumerate(initial.constraints):
        r.append_constraint(model, variables, constraint)
        if (i + 1) % 4096 == 0:
            stage("native_constraint_prefix_constructed", constraints=i + 1)
    assert len(model.proto.variables) == 32296 and len(model.proto.constraints) == 65694
    assert model.validate() == ""
    stage("complete_native_initial_construction_and_validation_passed")
    return model, variables


def provisional_record(point, target, candidate_path, preparation_sha):
    assert len(point) == 32296 and all(type(v) is int for v in point)
    assert evaluate_proto(target, point)
    return {"status": "PROVISIONAL_FULL_TARGET_PASSED_PARENT_CHECK_REQUIRED",
            "accepted": False, "count_feasibility_claimed": False,
            "full_target_checks_passed": True, "restored_original_parent_checks_passed": False,
            "candidate_path": str(candidate_path.relative_to(ROOT)),
            "candidate_file_sha256": file_sha(candidate_path),
            "canonical_integer_vector_sha256": sha(canonical(point)),
            "vector_JSON_field": "root array", "values": 32296,
            "target_proto_sha256": TARGET_SHA, "model_preparation_sha256": INPUTS["model_preparation"][1],
            "query_preparation_sha256": preparation_sha,
            "final_domain_input": {"path": str((LOGS / INPUTS["plan"][0]).relative_to(ROOT)),
                                   "sha256": INPUTS["plan"][1], "JSON_field": "target_variable_domains"},
            "all65811_native_target_constraints_checked": True,
            "literal_incidence_or_graph_claimed": False}


def native_parameters(cmh, seconds):
    assert 0 < seconds <= NATIVE_SECONDS
    params = cmh.SatParameters()
    params.num_search_workers = 1
    params.random_seed = 0
    params.cp_model_probing_level = 0
    params.linearization_level = 0
    params.max_time_in_seconds = seconds
    params.log_search_progress = True
    params.log_to_stdout = True
    return params

def choose_rows(violations, added):
    ids = [record["pool_id"] for record in violations]
    assert ids == sorted(set(ids)) and all(0 <= i < 117 for i in ids)
    assert not set(ids).intersection(added)
    assert all(type(r["gap"]) is int and r["gap"] > 0 for r in violations)
    return ids[:MAX_APPEND]

def evaluate_proto(proto, values):
    assert len(values) == len(proto.variables)
    for variable, value in zip(proto.variables, values):
        domain = list(variable.domain)
        if not any(a <= value <= b for a, b in zip(domain[::2], domain[1::2])):
            return False
    def expression(expr):
        return expr.offset + sum(c * values[j] for j, c in zip(expr.vars, expr.coeffs))
    for constraint in proto.constraints:
        kind = constraint.WhichOneof("constraint")
        if kind == "linear":
            row = constraint.linear
            value = sum(c * values[j] for j, c in zip(row.vars, row.coeffs))
            if not any(a <= value <= b for a, b in zip(row.domain[::2], row.domain[1::2])):
                return False
        elif kind == "int_prod":
            item = constraint.int_prod
            assert len(item.exprs) == 2
            if expression(item.target) != expression(item.exprs[0]) * expression(item.exprs[1]):
                return False
        else:
            assert kind == "table" and not constraint.table.negated and not constraint.table.vars
            table = constraint.table
            actual = tuple(expression(e) for e in table.exprs)
            width = len(actual)
            allowed = {tuple(table.values[i:i + width]) for i in range(0, len(table.values), width)}
            if actual not in allowed:
                return False
    return True

def pool_scan(point, target, plan):
    assert len(point) == VARIABLES and all(type(v) is int for v in point)
    violations = []
    for record in plan["external_pool"]:
        row = target.constraints[record["target_constraint"]].linear
        assert len(row.domain) == 2
        value = sum(c * point[j] for j, c in zip(row.vars, row.coeffs))
        lo, hi = row.domain
        if value < lo or value > hi:
            violations.append({"pool_id": record["pool_id"], "target_constraint": record["target_constraint"],
                               "parent_constraint": record["parent_constraint"], "family": record["family"],
                               "value": value, "lower": lo, "upper": hi, "gap": max(lo - value, value - hi)})
    return violations

def native_time_budget(deadline, now, used):
    assert all(isfinite(v) for v in (deadline, now, used)) and used >= 0
    return max(0.0, min(NATIVE_SECONDS - used, deadline - now - FINALIZATION_RESERVE))


def native_budget_controls():
    cases = [(1000, 800, 0, 180), (1000, 990, 0, 2),
             (1000, 990, 179.25, 0.75), (1000, 992, 0, 0),
             (1000, 1001, 0, 0), (1000, 100, 180, 0),
             (1000, 100, 181, 0), (1000, 990, 170, 2),
             (1000, 900, 170, 10)]
    for deadline, now, used, expected in cases:
        assert native_time_budget(deadline, now, used) == expected
    rejected = 0
    for used in (-1.0, float("inf"), float("nan")):
        try:
            native_time_budget(1000, 900, used)
        except AssertionError:
            rejected += 1
        else:
            raise AssertionError("invalid cumulative native time accepted")
    return {"status": "PASS", "explicit_deadline_and_cumulative_cases": len(cases),
            "invalid_time_inputs_rejected": rejected, "owned_seconds": SECONDS,
            "cumulative_native_seconds": NATIVE_SECONDS, "optimizer_calls": 0}


def worker(preparation_path, directory, deadline):
    started = time.monotonic()
    monitor = load_source("runtime")
    stages = []
    def stage(name, **extra):
        stages.append({"stage": name, "elapsed_seconds": time.monotonic() - started,
                       "memory": monitor.memory_snapshot(), **extra})
        save(directory / "stages.json", {"stages": stages})
        if time.monotonic() > deadline:
            raise TimeoutError("owned lightweight query deadline")
    stage("child_started_before_archive_or_native_import")
    prepared, preparation_sha = check_preparation(preparation_path)
    result = {"status": "UNKNOWN_BEFORE_INITIALIZATION", "preparation_sha256": preparation_sha,
              "target_proto_sha256": TARGET_SHA, "initial_proto_sha256": INITIAL_SHA,
              "production_solve_calls": 0, "iterations": [], "added_pool_ids": [],
              "maximum_cumulative_native_solve_seconds": NATIVE_SECONDS,
              "native_solve_wall_seconds": 0.0, "native_budget_overrun_seconds": 0.0,
              "count_feasibility_claimed": False, "literal_incidence_or_graph_claimed": False,
              "F0_excluded": False, "automatic_retry": False}
    save(directory / "progress.json", result)
    try:
        source, plan, target, initial, _ = load_target(prepared, stage)
        row_ids = list(plan["initial_to_target_rows"])
        model, variables = construct_initial(source, initial, stage)
        del initial; gc.collect()
        from google.protobuf import text_format
        from ortools.sat import cp_model_pb2
        from ortools.sat.python import cp_model
        import ortools
        assert ortools.__version__ == "9.15.6755" and sha(Path(cp_model.__file__).read_bytes()) == CP_MODEL_SHA
        added = []
        native_used = 0.0
        result["construction_seconds"] = time.monotonic() - started
        solver = cp_model.CpSolver()
        for call in range(MAX_CALLS):
            if deadline - time.monotonic() <= FINALIZATION_RESERVE:
                result["status"] = "UNKNOWN_TOTAL_LIMIT_BEFORE_NEXT_CALL"
                break
            if native_used >= NATIVE_SECONDS:
                result["status"] = "UNKNOWN_NATIVE_BUDGET_BEFORE_NEXT_CALL"
                break
            step_directory = directory / f"call{call:03d}"
            step_directory.mkdir()
            native_path = step_directory / "model.pb"
            assert model.export_to_file(str(native_path))
            native_raw = native_path.read_bytes()
            native_proto = cp_model_pb2.CpModelProto()
            native_proto.ParseFromString(native_raw)
            native_checked = source.exact_proto_check(native_proto, target, row_ids)
            if call == 0:
                assert sha(native_raw) == INITIAL_SHA and not added
            else:
                assert result["iterations"][-1]["appended_pool_ids"]
            prefix = {"call_index": call, "added_pool_ids": list(added),
                      "active_target_row_ids_sha256": sha(canonical(row_ids)),
                      "actual_model_sha256": sha(native_raw), "actual_model_bytes": len(native_raw),
                      "native_exact_checks": native_checked}
            save(step_directory / "prefix.json", prefix)
            remaining = native_time_budget(deadline, time.monotonic(), native_used)
            if remaining <= 0:
                result["status"] = "UNKNOWN_TOTAL_LIMIT_AFTER_PREFIX_SERIALIZATION"
                break
            params = native_parameters(cp_model.cmh, remaining)
            solver.parameters = params
            (step_directory / "parameters.pbtxt").write_text(str(params))
            step = {"call_index": call, "status": "NATIVE_CALL_ACTIVE",
                    "prefix_sha256": sha((step_directory / "prefix.json").read_bytes()),
                    "parameters_sha256": sha((step_directory / "parameters.pbtxt").read_bytes()),
                    "native_max_time_seconds": remaining, "appended_pool_ids": [],
                    "native_solve_wall_seconds_before": native_used,
                    "native_seconds_remaining_before": NATIVE_SECONDS - native_used}
            save(step_directory / "record.json", step)
            result.update(status="UNKNOWN_NATIVE_CALL_ACTIVE", production_solve_calls=call + 1)
            save(directory / "progress.json", result)
            stage("native_call_entering", call_index=call)
            call_started = time.monotonic()
            status = solver.solve(model)
            step["solve_wall_seconds"] = time.monotonic() - call_started
            native_used += step["solve_wall_seconds"]
            step.update(cumulative_native_solve_wall_seconds=native_used,
                        native_budget_overrun_seconds=max(0.0, native_used - NATIVE_SECONDS))
            result.update(native_solve_wall_seconds=native_used,
                          native_budget_overrun_seconds=step["native_budget_overrun_seconds"])
            native_response = solver.response_proto
            # The candidate is durable before parsing response text or any scan.
            point = list(native_response.solution)
            if point:
                assert all(type(v) is int for v in point)
                save(step_directory / "candidate.json", point)
                step.update(candidate_sha256=sha((step_directory / "candidate.json").read_bytes()),
                            candidate_values=len(point), canonical_integer_vector_sha256=sha(canonical(point)),
                            status="RETURNED_INTEGER_CANDIDATE_UNCHECKED")
                save(step_directory / "record.json", step)
            save(step_directory / "record.json", step)
            save(directory / "progress.json", result)
            stage("native_return_and_integer_vector_saved", call_index=call, integer_values=len(point))
            response_text = str(native_response)
            (step_directory / "response.pbtxt").write_text(response_text)
            response = cp_model_pb2.CpSolverResponse()
            text_format.Parse(response_text, response)
            assert point == list(response.solution)
            assert cp_model_pb2.CpSolverStatus.Name(response.status) == status.name
            step.update(native_status=status.name, native_status_code=int(response.status),
                        response_sha256=sha((step_directory / "response.pbtxt").read_bytes()),
                        native_wall_seconds=response.wall_time, native_conflicts=response.num_conflicts,
                        native_branches=response.num_branches, native_booleans=response.num_booleans,
                        native_integer_propagations=response.num_integer_propagations)
            save(step_directory / "record.json", step)
            if native_used > NATIVE_SECONDS:
                step["status"] = result["status"] = "UNKNOWN_NATIVE_BUDGET_OVERRUN"
            elif status.name in ("FEASIBLE", "OPTIMAL"):
                assert len(point) == 32296
                assert evaluate_proto(native_proto, point)
                violations = pool_scan(point, target, plan)
                scan = {"status": "PASS: exact active-prefix and all117 external-row evaluation",
                        "candidate_sha256": step["candidate_sha256"], "prefix_sha256": step["prefix_sha256"],
                        "active_constraints_checked": len(row_ids), "external_rows_checked": 117,
                        "violations": violations, "all_arithmetic_Python_integers": True}
                save(step_directory / "pool-scan.json", scan)
                step.update(pool_scan_sha256=sha((step_directory / "pool-scan.json").read_bytes()),
                            violated_external_rows=len(violations))
                if not violations:
                    step["status"] = "FULL_NATIVE_TARGET_PASSED_PARENT_CHECK_PENDING"
                    save(step_directory / "record.json", step)
                    exact = provisional_record(point, target, step_directory / "candidate.json", preparation_sha)
                    save(step_directory / "target-point-check.json", exact)
                    step.update(status="PROVISIONAL_FULL_TARGET_WITNESS",
                                target_point_check_sha256=sha((step_directory / "target-point-check.json").read_bytes()))
                    result.update(status="PROVISIONAL_FULL_TARGET_WITNESS", count_feasibility_claimed=False,
                                  provisional_call_index=call)
                else:
                    selected = choose_rows(violations, added)
                    assert selected
                    step["selected_pool_ids"] = selected
                    if call + 1 == MAX_CALLS:
                        step["status"] = result["status"] = "UNKNOWN_CALL_LIMIT_REJECTED_CANDIDATE"
                    elif native_used >= NATIVE_SECONDS:
                        step["status"] = result["status"] = "UNKNOWN_NATIVE_BUDGET_REJECTED_CANDIDATE"
                    elif deadline - time.monotonic() <= FINALIZATION_RESERVE:
                        step["status"] = result["status"] = "UNKNOWN_TOTAL_LIMIT_REJECTED_CANDIDATE"
                    else:
                        step["status"] = "EXACT_REJECTED_CANDIDATE_APPEND_PENDING"
                        save(step_directory / "record.json", step)
                        for pool_id in selected:
                            target_id = plan["external_pool"][pool_id]["target_constraint"]
                            assert target_id not in row_ids
                            source.append_constraint(model, variables, target.constraints[target_id])
                            row_ids.append(target_id)
                            added.append(pool_id)
                        assert len(model.proto.constraints) == 65694 + len(added)
                        assert model.validate() == ""
                        step.update(status="EXACT_REJECTED_CANDIDATE_CERTIFIED_ROWS_APPENDED",
                                    appended_pool_ids=selected,
                                    next_active_target_row_ids_sha256=sha(canonical(row_ids)))
                        result.update(status="UNKNOWN_NEXT_STRICT_PREFIX_PENDING", added_pool_ids=list(added))
            elif status.name == "INFEASIBLE":
                assert not point
                step["status"] = result["status"] = "UNPROVED_NATIVE_INFEASIBLE"
            elif status.name == "MODEL_INVALID":
                step["status"] = result["status"] = "ERROR_NATIVE_MODEL_INVALID"
            else:
                assert status.name == "UNKNOWN"
                step["status"] = result["status"] = "UNKNOWN_NATIVE_LIMIT"
            save(step_directory / "record.json", step)
            result["iterations"].append({"call_index": call,
                                         "record_sha256": sha((step_directory / "record.json").read_bytes()),
                                         "status": step["status"], "appended_pool_ids": step["appended_pool_ids"]})
            save(directory / "progress.json", result)
            if step["status"] != "EXACT_REJECTED_CANDIDATE_CERTIFIED_ROWS_APPENDED":
                break
        if time.monotonic() > deadline:
            result.update(status="UNKNOWN_LATE_CHILD", count_feasibility_claimed=False)
    except Exception as error:
        result.update(status="ERROR_NO_ACCEPTED_OUTCOME", count_feasibility_claimed=False,
                      error_type=type(error).__name__, message=str(error))
        raise
    finally:
        result["child_seconds"] = time.monotonic() - started
        result["terminal_memory"] = monitor.memory_snapshot()
        result["stages_sha256"] = file_sha(directory / "stages.json")
        save(directory / "child-result.json", result)

def run(preparation_path, directory):
    started = time.monotonic()
    deadline = started + SECONDS
    _, preparation_sha = owner_preparation_binding(preparation_path)
    supervisor = load_source("supervisor")
    directory.mkdir(parents=True, exist_ok=False)
    result = {"status": "UNKNOWN_BEFORE_CHILD", "preparation_sha256": preparation_sha,
              "target_proto_sha256": TARGET_SHA, "initial_proto_sha256": INITIAL_SHA,
              "runner_source_sha256": sha(Path(__file__).read_bytes()),
              "maximum_owned_child_seconds": SECONDS, "maximum_cumulative_native_solve_seconds": NATIVE_SECONDS,
              "count_feasibility_claimed": False,
              "literal_incidence_or_graph_claimed": False, "F0_excluded": False, "automatic_retry": False}
    save(directory / "result.json", result)
    command = [sys.executable, str(Path(__file__).resolve()), "_worker", "--preparation", str(preparation_path.resolve()),
               "--directory", str(directory.resolve()), "--deadline", str(deadline)]
    supervision = supervisor.supervise(command, directory, deadline)
    result["supervision"] = supervision
    if supervision["status"] == "CHILD_EXITED":
        raw = (directory / "child-result.json").read_bytes()
        child = json.loads(raw)
        assert child["preparation_sha256"] == preparation_sha
        assert child["target_proto_sha256"] == TARGET_SHA and child["initial_proto_sha256"] == INITIAL_SHA
        assert 0 <= child["production_solve_calls"] <= MAX_CALLS
        assert not child["F0_excluded"] and not child["literal_incidence_or_graph_claimed"]
        provisional = child["status"] == "PROVISIONAL_FULL_TARGET_WITNESS"
        assert not child["count_feasibility_claimed"]
        assert child["maximum_cumulative_native_solve_seconds"] == NATIVE_SECONDS
        if provisional:
            assert child["native_solve_wall_seconds"] <= NATIVE_SECONDS
            assert child["native_budget_overrun_seconds"] == 0
        assert child["stages_sha256"] == file_sha(directory / "stages.json")
        result.update(status=child["status"], child_result_sha256=sha(raw),
                      production_solve_calls=child["production_solve_calls"], count_feasibility_claimed=False,
                      full_target_candidate_provisional=provisional,
                      final_added_pool_ids=child["added_pool_ids"],
                      native_solve_wall_seconds=child["native_solve_wall_seconds"],
                      native_budget_overrun_seconds=child["native_budget_overrun_seconds"])
    else:
        result["status"] = supervision["status"]
    result["owner_seconds"] = time.monotonic() - started
    result["deadline_overrun_seconds"] = max(0, time.monotonic() - deadline)
    save(directory / "result.json", result)
    print(json.dumps(result, indent=2), flush=True)

if __name__ == "__main__":
    if not __debug__:
        raise RuntimeError("assertions are required")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "run", "_worker"))
    parser.add_argument("--preparation", type=Path)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--deadline", type=float)
    args = parser.parse_args()
    if args.mode == "prepare":
        args.directory.mkdir(parents=True, exist_ok=False)
        report = {"status": "PASS: full-Fourier literal no-LP query preparation; no optimizer",
                  "definition": configuration(), "reuse_controls": reuse_controls(),
                  "optimizer_calls": 0, "CpSolver_constructed": False}
        save(args.directory / "preparation.json", report)
        print(json.dumps(report, indent=2), flush=True)
    elif args.mode == "run":
        assert args.preparation is not None
        run(args.preparation, args.directory)
    else:
        assert args.preparation is not None and args.deadline is not None
        worker(args.preparation, args.directory, args.deadline)
