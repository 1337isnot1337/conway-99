"""Append the complete six-observable, 610-tuple Gram table to the Y target.

The old 18,444 variables and every old constraint remain unchanged.  The
six observables are exact integer count forms, with no averaging divisor.
Table multiplicities are not used as weights.  Completeness is inherited
from the hash-bound enumeration and cold certificate; this adapter checks
all saved witnesses and the literal appended protobufs without a recensus.
Preparation and cold replay each have one owned 60-second child. No solver.
"""
import argparse
import gc
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
LOGS = ROOT / "experiments/logs/root-prism-free"
SOURCES = {
    "runtime": ("root_prism_free_f0_character_pool_runtime.py", "030163f019b93ee39124e9f3171caac1e4ad79227fde9a1e831c28a938b245f8"),
    "supervisor": ("root_prism_free_f0_local_neighbors_batch.py", "b8e5323f92fa105ff2c0ed5b1667ac25d7c92f85f8cac45b170ddc56208f8278"),
    "parent": ("root_prism_free_f0_character_y_domain_overlay.py", "ff08cbcaec6787d5821af57526a708e1758007970bec58c86584bcd3d76904dd"),
    "table": ("root_prism_free_f0_two_dimensional_gram_tables.py", "7fd5cf303b7a20b31305329aece575f114a76dcb6482478aed63ac491b81b33c"),
    "vector_domains": ("root_prism_free_f0_two_dimensional_vector_domains.py", "0b2d15c2d331466acbc29b3585bec4c53de5a912424c9d50b179e5ed37d15660"),
    "scope": ("root_prism_free_f0_two_dimensional_moments.py", "31793743ba11fb56f42bcc9f383fe8b3268dae1cd8ebf6ec0271160a1d58d2fd"),
}
INPUTS = {
    "parent_preparation": ("f0-character-y-domain-overlay01/report.json", "a4a543b35bdd22357eef39524ff8015e0d4d274547c046205c806a5f52e92061"),
    "parent_cold": ("f0-character-y-domain-overlay01-cold/report.json", "851a2a4a292a891de7b38eb08212fd1a604cf72cc09dbef3af97768ebe8e21be"),
    "parent_root_review": ("f0-character-y-domain-root-source-review.json", "e5f68917dcfade4ecf36c34771490d15b248a50a77681be00637264c10d0191e"),
    "parent_plan": ("f0-character-y-domain-overlay01/plan.json.gz", "4d3a13718cdac9fcf68b119a1cd1ba009edeb21c7257d4498d5ebdf18954acc4"),
    "parent_target": ("f0-character-y-domain-overlay01/target.pb.gz", "41ff251304c8d3961ebae059581f8416f7f0a45c7cc2246be547296e7db407f0"),
    "parent_initial": ("f0-character-y-domain-overlay01/initial.pb.gz", "ca5e66f17bd53620fe7dd61102d43cb9e581af821c7709eae92dc90b4609a53a"),
    "scope": ("f0-two-dimensional-moments-scope01.json", "948e256945fc817cc75ea46c969c055b21e61832a4f2177c481884e73338223f"),
    "vector_domains": ("f0-two-dimensional-vector-domains-preparation01.json", "571b52265dc70a9e5992750d05ab0928364a68fa650716734bd3727728e135c1"),
    "table_preparation": ("f0-two-dimensional-gram-tables-preparation01.json", "71a1104cfd377f575a03afbbe4921b14a3e0504e75f1e6c891efe477ae1b5d83"),
    "table_result": ("f0-two-dimensional-gram-tables-enumeration01.json", "dd69bcdae9fd4df56a49195b8965ef89e7ae5ddf321c21e6b4547f650d7dce7a"),
    "table_cold": ("f0-two-dimensional-gram-tables-enumeration01-cold.json", "125c41ec7add01ccbcbeff1aad4788a9973c4f0e409fedacaef91846c40d7f41"),
    "table_root_review": ("f0-two-dimensional-gram-tables-root-source-review.json", "9be3f46884f64626655c9d945617f90279722fb55ad25e14348732997f8b647a"),
}
PARENT_RAW = {
    "target": "a738d318b6b8de471ee7383f1e6ea11949eed8f8ccf4892814fa2eac268ed153",
    "initial": "9d1e6a031d5c2c83a47982477d51b34fba42edf1bbcdae1bccfa9906745badfe",
}
OLD_VARIABLES = 18444
OLD_ROWS = {"target": 34398, "initial": 34281}
ORDER = [[0, 0], [0, 1], [0, 2], [1, 1], [1, 2], [2, 2]]
NAMES = ["B22", "B23", "B24", "B33", "B34", "B44"]
SECONDS = 60


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


def source_module(key):
    name, expected = SOURCES[key]
    path = ROOT / "experiments/workspace" / name
    assert file_sha(path) == expected
    spec = importlib.util.spec_from_file_location("frozen_small_gram_" + key, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read(key):
    name, expected = INPUTS[key]
    raw = (LOGS / name).read_bytes()
    assert sha(raw) == expected, key
    return json.loads(gzip.decompress(raw) if name.endswith(".gz") else raw)


def definition():
    for name, expected in SOURCES.values():
        assert file_sha(ROOT / "experiments/workspace" / name) == expected, name
    for name, expected in INPUTS.values():
        assert file_sha(LOGS / name) == expected, name
    return {
        "schema": "conway99.f0.small-Gram-overlay.v1",
        "source_sha256": file_sha(Path(__file__)),
        "sources": {k: {"path": "experiments/workspace/" + p, "sha256": h} for k, (p, h) in SOURCES.items()},
        "inputs": {k: {"path": str((LOGS / p).relative_to(ROOT)), "sha256": h} for k, (p, h) in INPUTS.items()},
        "parent_raw_protobuf_sha256": PARENT_RAW,
        "old_variables": OLD_VARIABLES, "new_observable_IDs": list(range(18444, 18450)),
        "new_variables": 6, "new_linear_definitions": 6, "new_allowed_tables": 1,
        "joint_table_tuples": 610, "target_constraints": 34405, "initial_constraints": 34288,
        "external_pool_constraints": 117, "maximum_owned_seconds_per_phase": SECONDS,
        "all_old_variables_domains_constraints_products_tables_preserved": True,
        "observable_definition_has_no_divisor": True, "table_multiplicities_used_as_weights": False,
        "inherited_complete_table_cold_certificate_required": True,
        "new_selector_subset_or_vector_tuple_censuses": 0,
        "optimizer_calls": 0, "CpSolver_constructed": False,
        "production_query_authorized_by_this_preparation": False,
    }


def intervals(values):
    values = sorted(set(values))
    assert values and all(type(v) is int for v in values)
    answer = [values[0], values[0]]
    for v in values[1:]:
        if v == answer[-1] + 1:
            answer[-1] = v
        else:
            answer.extend([v, v])
    return answer


def controls():
    for mask in range(1, 1 << 7):
        values = [i - 3 for i in range(7) if mask >> i & 1]
        flat = intervals(values)
        assert [i for lo, hi in zip(flat[::2], flat[1::2]) for i in range(lo, hi + 1)] == values
        assert all(flat[i] + 1 < flat[i + 1] for i in range(1, len(flat) - 1, 2))
    return {"status": "PASS", "exhaustive_nonempty_seven_integer_interval_controls": 127,
            "optimizer_calls": 0, "CpSolver_constructed": False}


def verified_table():
    scope, domains, prep, result, cold = [read(k) for k in
                                         ("scope", "vector_domains", "table_preparation", "table_result", "table_cold")]
    assert scope["H"] == domains["H"] == [[2, -1], [-1, 2]]
    assert domains["source_sha256"] == SOURCES["vector_domains"][1]
    assert prep["source_sha256"] == result["source_sha256"] == cold["source_sha256"] == SOURCES["table"][1]
    assert result["preparation_sha256"] == cold["preparation_sha256"] == INPUTS["table_preparation"][1]
    assert result["domain_record_sha256"] == cold["domain_record_sha256"] == INPUTS["vector_domains"][1]
    assert cold["result_sha256"] == INPUTS["table_result"][1]
    assert cold["status"].startswith("PASS") and cold["complete_full_table"]
    assert cold["stage_distinct_tuple_counts"] == [39, 39, 39, 610]
    assert cold["fresh_integer_polarization_products"] == 7942
    assert result["complete"] and result["all_joint_pair_projections_equal_pair_tables"]
    assert result["selector_orbits"] == domains["selector_orbits"] == prep["selector_orbits"] == [2, 3, 4]
    assert result["six_entry_order"] == domains["six_entry_order"] == prep["six_entry_order"] == ORDER
    forms = domains["six_native_entry_forms"]
    assert forms == prep["six_native_entry_forms"] == scope["six_exact_entry_forms"]
    assert [r["matrix_entry"] for r in forms] == ORDER
    terms = [r["native_count_terms"] for r in forms]
    assert sum(map(len, terms)) == 56
    for row in terms:
        assert row == sorted(row) and len({j for j, c in row}) == len(row)
        assert all(type(j) is type(c) is int and 0 <= j < 15038 and 0 < abs(c) <= 4 for j, c in row)
    vectors = [d["vectors"] for d in domains["domains"]]
    assert [len(v) for v in vectors] == [19, 19, 19]
    stage = result["stages"][3]
    assert stage["complete"] and stage["columns"] == [0, 1, 2]
    assert stage["expected_combinations"] == stage["visited_combinations"] == 6859
    table, witnesses = stage["tuples"], stage["first_vector_witness_indices"]
    assert len(table) == len(witnesses) == 610
    assert table == [list(t) for t in sorted(set(map(tuple, table)))]
    assert len(stage["vector_combination_multiplicities"]) == 610
    assert all(type(v) is int and v > 0 for v in stage["vector_combination_multiplicities"])
    assert sum(stage["vector_combination_multiplicities"]) == 6859
    def dot(v, w):
        return 2 * v[0] * w[0] - v[0] * w[1] - v[1] * w[0] + 2 * v[1] * w[1]
    for row, witness in zip(table, witnesses):
        assert len(row) == 6 and all(type(v) is int for v in row)
        assert len(witness) == 3 and all(type(j) is int and 0 <= j < 19 for j in witness)
        chosen = [vectors[i][j] for i, j in enumerate(witness)]
        assert row == [dot(chosen[i], chosen[j]) for i, j in ORDER]
    for saved, (i, j) in zip(result["stages"][:3], ((0, 1), (0, 2), (1, 2))):
        positions = [ORDER.index([i, i]), ORDER.index([i, j]), ORDER.index([j, j])]
        projection = [list(t) for t in sorted({tuple(row[k] for k in positions) for row in table})]
        assert saved["complete"] and saved["columns"] == [i, j]
        assert projection == saved["tuples"] and len(projection) == 39
    values = [sorted({row[i] for row in table}) for i in range(6)]
    assert values == result["joint_entry_values"]
    assert values[0] == values[3] == values[5] == [0, 2, 6, 8]
    assert values[1] == values[2] == values[4] == [-8, -6, -4, -3, -2, -1, 0, 1, 2, 3, 4, 6, 8]
    assert [2, 1, 1, 2, 1, 2] not in table
    audit = {"saved_tuple_witnesses_checked": 610, "pair_projections_checked": 3,
             "complete_enumeration_and_cold_are_hash_bound": True,
             "table_sha256": sha(canonical(table)), "terms_sha256": sha(canonical(terms)),
             "native_count_terms": 56, "maximum_old_term_absolute_coefficient": 4,
             "multiplicities_ignored_in_constraints": True}
    return terms, [intervals(v) for v in values], table, audit


def append_suffix(proto, terms, domains, table):
    assert len(proto.variables) == OLD_VARIABLES
    for name, domain in zip(NAMES, domains):
        proto.variables.add(name="f0_plus_gram_" + name, domain=domain)
    for i, terms_i in enumerate(terms):
        row = proto.constraints.add().linear
        row.vars.extend([j for j, c in terms_i] + [OLD_VARIABLES + i])
        row.coeffs.extend([-c for j, c in terms_i] + [1])
        row.domain.extend([0, 0])
    allowed = proto.constraints.add().table
    for j in range(18444, 18450):
        expression = allowed.exprs.add()
        expression.vars.append(j)
        expression.coeffs.append(1)
    allowed.values.extend(v for row in table for v in row)


def derive(runtime, stage):
    parent_report, parent_cold = [read(k) for k in ("parent_preparation", "parent_cold")]
    assert parent_report["status"].startswith("PASS") and parent_cold["status"].startswith("PASS")
    assert parent_cold["preparation_sha256"] == INPUTS["parent_preparation"][1]
    assert parent_cold["source_sha256"] == SOURCES["parent"][1]
    assert parent_cold["complete_saved_plan_and_protobuf_byte_equality"]
    full_parent = read("parent_plan")
    assert full_parent["source_sha256"] == SOURCES["parent"][1]
    assert full_parent["variable_count"] == OLD_VARIABLES
    assert full_parent["full_target_constraints"] == OLD_ROWS["target"]
    assert full_parent["initial_constraints"] == OLD_ROWS["initial"]
    assert full_parent["external_pool_constraints"] == 117
    keys = ("initial_to_target_rows", "external_pool", "target_variable_domains")
    parent = {key: full_parent[key] for key in keys}
    del full_parent
    gc.collect()
    terms, new_domains, table, table_audit = verified_table()
    stage("parent_plan_and_complete_saved_table_checked")
    from ortools.sat import cp_model_pb2
    protos = {}
    for name, expected in PARENT_RAW.items():
        archived = (LOGS / INPUTS["parent_" + name][0]).read_bytes()
        assert sha(archived) == INPUTS["parent_" + name][1]
        raw = gzip.decompress(archived)
        assert sha(raw) == expected == parent_report["outputs"][name]["raw_sha256"]
        proto = cp_model_pb2.CpModelProto()
        proto.ParseFromString(raw)
        del raw, archived
        assert {f.name for f, _ in proto.ListFields()} == {"variables", "constraints"}
        assert len(proto.variables) == OLD_VARIABLES and len(proto.constraints) == OLD_ROWS[name]
        assert [list(v.domain) for v in proto.variables] == parent["target_variable_domains"]
        append_suffix(proto, terms, new_domains, table)
        extended_hash = sha(proto.SerializeToString())
        del proto.constraints[OLD_ROWS[name]:]
        del proto.variables[OLD_VARIABLES:]
        assert sha(proto.SerializeToString()) == expected
        append_suffix(proto, terms, new_domains, table)
        assert sha(proto.SerializeToString()) == extended_hash
        protos[name] = proto
        gc.collect()
        stage(name + "_append_and_whole_parent_hash_restoration_checked")
    target, initial = protos["target"], protos["initial"]
    rows = parent["initial_to_target_rows"]
    assert rows == sorted(set(rows)) and len(rows) == OLD_ROWS["initial"]
    pool = parent["external_pool"]
    assert [r["pool_id"] for r in pool] == list(range(117))
    external = [r["target_constraint"] for r in pool]
    assert len(set(external)) == 117 and not set(external).intersection(rows)
    assert sorted(external + rows) == list(range(OLD_ROWS["target"]))
    for entry in pool:
        row = target.constraints[entry["target_constraint"]]
        assert row.WhichOneof("constraint") == "linear"
        assert sha(row.SerializeToString()) == entry["constraint_sha256"]
        assert len(row.linear.vars) == entry["terms"]
    new_rows = rows + list(range(34398, 34405))
    assert sorted(external + new_rows) == list(range(34405))
    exact = runtime.exact_proto_check(initial, target, new_rows)
    assert exact["variables"] == 18450 and exact["constraints"] == 34288
    assert exact["constraint_types"] == {"linear": 30955, "int_prod": 3288, "table": 45}
    domains = parent["target_variable_domains"] + new_domains
    activity = [sum(abs(c) * max(abs(domains[j][0]), abs(domains[j][-1]))
                    for j, c in zip(r.linear.vars, r.linear.coeffs)) for r in target.constraints[34398:34404]]
    assert max(activity) <= 272
    plan = {
        "schema": "conway99.f0.small-Gram-runtime-plan.v1", "source_sha256": file_sha(Path(__file__)),
        "variable_count": 18450, "full_target_constraints": 34405, "initial_constraints": 34288,
        "external_pool_constraints": 117, "initial_to_target_rows": new_rows,
        "external_pool": pool, "target_variable_domains": domains,
        "old_to_target_columns": list(range(18444)), "target_to_old_columns": list(range(18444)) + [None] * 6,
        "parent_plan": {"path": INPUTS["parent_plan"][0], "sha256": INPUTS["parent_plan"][1]},
        "parent_preparation_sha256": INPUTS["parent_preparation"][1],
        "parent_cold_sha256": INPUTS["parent_cold"][1], "parent_proto_sha256": PARENT_RAW,
        "small_Gram_overlay": {
            "selector_orbits": [2, 3, 4], "six_entry_order": ORDER, "observable_names": NAMES,
            "observable_ids": list(range(18444, 18450)), "linear_count_forms": terms,
            "observable_domains": new_domains, "target_suffix_rows": list(range(34398, 34405)),
            "initial_suffix_rows": list(range(34281, 34288)), "new_definition_absolute_box_sums": activity,
            "saved_table_result_sha256": INPUTS["table_result"][1],
            "saved_table_cold_sha256": INPUTS["table_cold"][1], **table_audit,
        },
        "full_target_pass_is_PROVISIONAL_until_original_parent_acceptance": True,
        "count_or_literal_or_exterior_graph_feasibility_claimed": False,
    }
    stage("all_old_maps_pool_and_appended_native_rows_checked")
    return plan, protos, exact, parent_report["inherited_full_target_signed64_upper_bound_checks"]


def archive(path, raw):
    assert len(raw) <= 64 << 20
    payload = gzip.compress(raw, mtime=0)
    with path.open("xb") as stream:
        stream.write(payload)
    return {"path": str(path.relative_to(ROOT)), "sha256": sha(payload),
            "raw_sha256": sha(raw), "raw_bytes": len(raw)}


def worker(mode, directory, deadline, parent_directory=None):
    started, stages = time.monotonic(), []
    runtime = source_module("runtime")
    def stage(label, **extra):
        stages.append({"stage": label, "elapsed_seconds": time.monotonic() - started,
                       "memory": runtime.memory_snapshot(), **extra})
        save(directory / "stages.json", {"stages": stages, "optimizer_calls": 0})
        if time.monotonic() > deadline:
            raise TimeoutError("owned six-observable overlay deadline")
    try:
        stage("started")
        bound = definition()
        control = controls()
        plan, protos, checked, inherited = derive(runtime, stage)
        if mode == "prepare":
            outputs = {"plan": archive(directory / "plan.json.gz", canonical(plan))}
            for name, proto in protos.items():
                outputs[name] = archive(directory / (name + ".pb.gz"), proto.SerializeToString())
            stage("new_small_Gram_archives_saved")
            runtime.import_native(stage)
            model = runtime.cp_model.CpModel()
            variables = [model.new_int_var_from_domain(runtime.cp_model.Domain.from_flat_intervals(list(v.domain)), v.name)
                         for v in protos["initial"].variables]
            assert [v.index for v in variables] == list(range(18450))
            for i, constraint in enumerate(protos["initial"].constraints):
                runtime.append_constraint(model, variables, constraint)
                if (i + 1) % 4096 == 0:
                    stage("native_initial_prefix_constructed", constraints=i + 1)
            assert model.validate() == ""
            export = directory / "native-initial.pb"
            assert model.export_to_file(str(export))
            assert file_sha(export) == outputs["initial"]["raw_sha256"]
            stage("native_validation_and_complete_initial_byte_identity_passed")
            report = {
                "status": "PASS: six-observable Gram table overlay and native initial preparation; no solver",
                "definition": bound, "controls": control, "outputs": outputs,
                "native_initial_exact_checks": checked,
                "inherited_full_target_signed64_upper_bound_checks": inherited,
                "old_constraints_and_domains_unchanged": True,
                "all117_external_pool_rows_and_ids_unchanged": True,
                "native_initial_public_constructor_byte_identity": True,
                "deleting_six_variables_seven_constraints_restores_parent_hashes": PARENT_RAW,
                "table_witness_and_domain_audit": plan["small_Gram_overlay"],
                "full_target_acceptance_requires_restored_parent_check": True,
                "optimizer_calls": 0, "CpSolver_constructed": False,
            }
        else:
            assert mode == "cold" and parent_directory is not None
            raw_report = (parent_directory / "report.json").read_bytes()
            old = json.loads(raw_report)
            assert old["status"].startswith("PASS") and old["definition"] == bound
            assert old["controls"] == control and old["native_initial_exact_checks"] == checked
            for name, raw in [("plan", canonical(plan))] + [(k, p.SerializeToString()) for k, p in protos.items()]:
                entry = old["outputs"][name]
                path = ROOT / entry["path"]
                assert file_sha(path) == entry["sha256"]
                assert gzip.decompress(path.read_bytes()) == raw
                assert sha(raw) == entry["raw_sha256"] and len(raw) == entry["raw_bytes"]
            stage("complete_append_plan_and_protobufs_cold_checked")
            report = {
                "status": "PASS: complete six-observable overlay cold replay; parent and enumeration proofs bound",
                "source_sha256": file_sha(Path(__file__)), "preparation_sha256": sha(raw_report),
                "definition": bound, "controls": control, "new_saved_table_witnesses_checked": 610,
                "complete_saved_plan_and_protobuf_byte_equality": True,
                "old_domains_and_constraint_prefixes_restored_exactly": PARENT_RAW,
                "native_model_construction_or_validation_repeated": False,
                "selector_subset_or_vector_tuple_census_repeated": False,
                "optimizer_calls": 0, "CpSolver_constructed": False,
            }
        report.update(seconds=time.monotonic() - started, terminal_memory=runtime.memory_snapshot(),
                      stages_sha256=file_sha(directory / "stages.json"))
        save(directory / "report.json", report)
    except Exception as error:
        save(directory / "error.json", {"error_type": type(error).__name__, "message": str(error),
                                       "memory": runtime.memory_snapshot(), "optimizer_calls": 0})
        raise


def owned(mode, directory, parent_directory=None):
    started = time.monotonic()
    deadline = started + SECONDS
    definition()
    supervisor = source_module("supervisor")
    directory.mkdir(parents=True, exist_ok=False)
    command = [sys.executable, str(Path(__file__).resolve()), "_" + mode,
               "--directory", str(directory.resolve()), "--deadline", str(deadline)]
    if parent_directory is not None:
        command.extend(("--parent-directory", str(parent_directory.resolve())))
    save(directory / "owner-result.json", {"status": "UNKNOWN_BEFORE_CHILD", "optimizer_calls": 0})
    supervision = supervisor.supervise(command, directory, deadline)
    result = {"status": supervision["status"], "supervision": supervision, "report_accepted": False,
              "source_sha256": file_sha(Path(__file__)), "maximum_owned_seconds": SECONDS,
              "optimizer_calls": 0, "CpSolver_constructed": False}
    if supervision["status"] == "CHILD_EXITED" and time.monotonic() <= deadline:
        report = json.loads((directory / "report.json").read_bytes())
        assert report["status"].startswith("PASS")
        result.update(status=report["status"], report_accepted=True, report_sha256=file_sha(directory / "report.json"))
    result.update(owner_seconds=time.monotonic() - started, deadline_overrun_seconds=max(0, time.monotonic() - deadline))
    save(directory / "owner-result.json", result)
    print(json.dumps(result, indent=2), flush=True)


if __name__ == "__main__":
    if not __debug__:
        raise RuntimeError("assertions are required")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "cold", "_prepare", "_cold"))
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--parent-directory", type=Path)
    parser.add_argument("--deadline", type=float)
    args = parser.parse_args()
    if args.mode.startswith("_"):
        assert args.deadline is not None
        worker(args.mode[1:], args.directory, args.deadline, args.parent_directory)
    else:
        owned(args.mode, args.directory, args.parent_directory)
