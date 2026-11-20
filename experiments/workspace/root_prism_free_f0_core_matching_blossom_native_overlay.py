"""Append the 6,854 frozen core-matching blossom rows to native02.

Preparation is standard-library arithmetic only. Build and cold modes each
run under one owned 60-second deadline. They never construct a solver.
All old variables, constraints, tables, products and 117 pool IDs survive.
"""
import argparse
from collections import Counter
import gc
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
LOG = "experiments/logs/root-prism-free/"
WORK = "experiments/workspace/"
SOURCES = {
    "query": (WORK + "root_prism_free_f0_full_fourier_query.py", "a8eff9c09fdd2a31482d23e3c83b11424fab32462e9b1431c3d899b6b8034955"),
    "runtime": (WORK + "root_prism_free_f0_character_pool_runtime.py", "030163f019b93ee39124e9f3171caac1e4ad79227fde9a1e831c28a938b245f8"),
    "supervisor": (WORK + "root_prism_free_f0_local_neighbors_batch.py", "b8e5323f92fa105ff2c0ed5b1667ac25d7c92f85f8cac45b170ddc56208f8278"),
    "inventory": (WORK + "root_prism_free_f0_core_matching_blossom_inventory.py", "6455d5c3967eb4f7aa22c690ab89f7572cf31ab9c5f7975927c6096caa39513c"),
}
INPUTS = {
    "parent_report": (LOG + "f0-full-fourier-literal-native02/report.json", "d2cc38f284420c461fd191ce4ebfb9dbc16cf6cfd03f8ca1d2e00842bb92e9c4"),
    "parent_cold": (LOG + "f0-full-fourier-literal-native02-cold/report.json", "5433cc1765e164f6c9df603cb0bfff6c62b5c6779c8f7e5391fff3c8e68a654c"),
    "parent_plan": (LOG + "f0-full-fourier-literal-native02/plan.json.gz", "b7914f80201dc0803faecb5ec1b5e3a405daee6621e2a44021929571573576b9"),
    "parent_target": (LOG + "f0-full-fourier-literal-native02/target.pb.gz", "277449dc6d999207fbc77d452d1f351011791b1093cdda7875fc309d972381dd"),
    "parent_initial": (LOG + "f0-full-fourier-literal-native02/initial.pb.gz", "3f8833a098695b058a70841757ffb7e20bcb86531027eeef3c55c586ecd5d6ac"),
    "inventory_report": (LOG + "f0-core-matching-blossom-inventory01/report.json", "5e5ba4687a85c30d75647c54e76b5713caa295f2a9e77f8722f10c3e8dd4382d"),
    "all_rows": (LOG + "f0-core-matching-blossom-inventory01/all-rows.json.gz", "c922c61e1728c5166293e8c8e7348135541c04ab93870f2cafaef8c872ef067b"),
    "selected_rows": (LOG + "f0-core-matching-blossom-inventory01/selected-rows.json.gz", "3af95cde2c2ef9a097401374c856137dca67eb07e16add887f9eaf93a89e4969"),
    "omitted_rows": (LOG + "f0-core-matching-blossom-inventory01/omitted-rows.json.gz", "8ce0a7fbab5f25dd8c0dbe6c854df0a234db14c2f11d790268d2f63543c22b6b"),
    "family_result": (LOG + "f0-core-matching-blossom-family-run01/result.json", "901ead85d602598336d1031f1ebc58cacf18ab9c258cd73654b04c6eca635b86"),
    "family_cold": (LOG + "f0-core-matching-blossom-family-run01-cold.json", "664074cc423d925778e3e4e4898db996fdec0f30c6e0bf633b5e2a74ca796bc1"),
    "family_gate": (LOG + "f0-core-matching-blossom-family-root-gate01.json", "976e31eec53c14dd95ab21137935b9b7c052891de0bce72f11dabd25fdcc4331"),
}
PARENT_RAW = {
    "target": "4e0ec33cb363299a9e199ce33a30a937a85d2f96969965f54833ed38464a911b",
    "initial": "cf4c7cf7cb21087f443f5bdd6f2781a02e13091b7329d7f05fe78820182e179d",
}
PARENT_COUNTS = {"target": 58957, "initial": 58840}
NEW_COUNTS = {"target": 65811, "initial": 65694}
VARIABLES, ADDED, SECONDS = 32296, 6854, 60


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


def read(key):
    relative, expected = INPUTS[key]
    raw = (ROOT / relative).read_bytes()
    assert sha(raw) == expected
    return json.loads(gzip.decompress(raw) if relative.endswith(".gz") else raw)


def load_source(key):
    relative, expected = SOURCES[key]
    path = ROOT / relative
    assert file_sha(path) == expected
    spec = importlib.util.spec_from_file_location("frozen_blossom_overlay_" + key, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def definition():
    for relative, expected in list(SOURCES.values()) + list(INPUTS.values()):
        assert file_sha(ROOT / relative) == expected
    return {
        "schema": "conway99.f0.core-blossom-native-overlay.v1",
        "source_sha256": file_sha(Path(__file__)),
        "sources": {k: {"path": p, "sha256": h} for k, (p, h) in SOURCES.items()},
        "inputs": {k: {"path": p, "sha256": h} for k, (p, h) in INPUTS.items()},
        "parent_raw_protobuf_sha256": PARENT_RAW,
        "variables": VARIABLES, "appended_rows": ADDED, "appended_nonzeros": 20542,
        "target_constraints": NEW_COUNTS["target"], "initial_constraints": NEW_COUNTS["initial"],
        "unchanged_products": 16280, "unchanged_tables": 44, "external_pool_constraints": 117,
        "all_row_inventory": 8894, "omitted_by_explicit_boxes": 2040,
        "maximum_owned_build_seconds": SECONDS, "maximum_owned_cold_seconds": SECONDS,
        "native_solver_calls": 0, "CpSolver_constructed": False,
        "new_domain_or_objective_or_symmetry_restrictions": False,
        "count_or_literal_or_exterior_graph_feasibility_claimed": False,
        "automatic_retry": False,
    }


def row_core(row):
    return {key: row[key] for key in ("id", "terms", "rhs", "witness_ref")}


def semantic_inputs():
    parent, prior_report, prior_cold = read("parent_plan"), read("parent_report"), read("parent_cold")
    assert prior_report["status"].startswith("PASS") and prior_cold["status"].startswith("PASS")
    assert prior_cold["preparation_sha256"] == INPUTS["parent_report"][1]
    assert (parent["variable_count"], parent["full_target_constraints"], parent["initial_constraints"]) == (VARIABLES, 58957, 58840)
    for name in ("target", "initial", "plan"):
        key = "parent_" + name
        assert prior_report["outputs"][name]["sha256"] == INPUTS[key][1]
        if name != "plan":
            assert prior_report["outputs"][name]["raw_sha256"] == PARENT_RAW[name]
    domains = parent["target_variable_domains"]
    assert len(domains) == VARIABLES and parent["external_pool_constraints"] == 117
    embedding = parent["initial_to_target_rows"]
    assert len(embedding) == 58840 and embedding == sorted(set(embedding))
    pool = parent["external_pool"]
    assert [r["pool_id"] for r in pool] == list(range(117))
    assert sorted(embedding + [r["target_constraint"] for r in pool]) == list(range(58957))

    report = read("inventory_report")
    records = {key: read(key + "_rows") for key in ("all", "selected", "omitted")}
    assert report["status"].startswith("PASS") and report["new_family_cases_enumerated"] == 0
    assert (report["all_rows"], report["selected_rows"], report["omitted_rows"]) == (8894, 6854, 2040)
    common = records["all"]
    assert common["definition"]["source_sha256"] == SOURCES["inventory"][1]
    for key, record in records.items():
        assert record["definition"] == common["definition"]
        assert record["proof_chunks"] == common["proof_chunks"]
        assert report["files"][key]["sha256"] == INPUTS[key + "_rows"][1]
        assert len(record["rows"]) == report["files"][key]["rows"]
    result, cold, gate = read("family_result"), read("family_cold"), read("family_gate")
    assert result["complete"] and result["status"] == "COMPLETE"
    assert cold["producer_complete"] and cold["complete_saved_prefix_checked"]
    assert cold["record_sha256"] == INPUTS["family_result"][1]
    assert (cold["checked_chunks"], cold["checked_rows"], cold["checked_triples"]) == (18, 8894, 549480)
    assert gate["status"].startswith("PASS")
    assert len(common["proof_chunks"]) == len(result["chunks"]) == 18
    for site, (bound, chunk) in enumerate(zip(common["proof_chunks"], result["chunks"])):
        assert bound["path"] == LOG + "f0-core-matching-blossom-family-run01/core%02d.json.gz" % site
        assert bound["sha256"] == chunk["sha256"] and bound["raw_sha256"] == chunk["raw_sha256"]
        assert file_sha(ROOT / bound["path"]) == bound["sha256"]

    rows, selected, omitted = [records[k]["rows"] for k in ("all", "selected", "omitted")]
    assert [r["id"] for r in rows] == list(range(8894))
    assert sorted(r["id"] for r in selected + omitted) == list(range(8894))
    assert [r["id"] for r in selected] == sorted(set(r["id"] for r in selected))
    assert [r["id"] for r in omitted] == sorted(set(r["id"] for r in omitted))
    for row in selected + omitted:
        assert row_core(row) == rows[row["id"]]
    largest, all_terms, selected_terms = 0, 0, 0
    for row in rows:
        terms = row["terms"]
        assert 2 <= len(terms) <= 3 and terms == sorted(terms)
        assert len(set(j for j, _ in terms)) == len(terms) and row["rhs"] in (6, 12)
        assert all(type(j) is int and type(c) is int and 42 <= j < 15038 and c in (1, 2) for j, c in terms)
        assert all(domains[j][0] >= 0 for j, _ in terms)
        value = sum(c * domains[j][-1] for j, c in terms)
        assert 0 <= value < 1 << 62
        largest = max(largest, value)
        all_terms += len(terms)
    omitted_upper_checks = 0
    for row in omitted:
        assert [j for j, _ in row["upper_bounds"]] == [j for j, _ in row["terms"]]
        saved = dict(row["upper_bounds"])
        for j, _ in row["terms"]:
            assert domains[j][-1] <= saved[j]
            omitted_upper_checks += 1
        assert sum(c * saved[j] for j, c in row["terms"]) == row["box_maximum"] <= row["rhs"]
    selected_terms = sum(len(row["terms"]) for row in selected)
    assert (all_terms, selected_terms, omitted_upper_checks) == (26662, 20542, 6120)
    audit = {
        "all_rows": 8894, "selected_rows": 6854, "omitted_rows": 2040,
        "complete_disjoint_row_partition": True, "selected_nonzeros": selected_terms,
        "native_upper_bounds_checked_against_saved_omission_bounds": omitted_upper_checks,
        "omitted_rows_proved_by_actual_native02_domains": True,
        "all_selected_coordinates_nonnegative": True,
        "maximum_new_linear_absolute_box_sum": largest,
        "proof_chunks_bound_without_family_reenumeration": 18,
        "new_native_linear_domain": "0 <= sum(c_j Y_j) <= rhs; lower bound follows from unchanged nonnegative domains",
    }
    return parent, selected, audit


def make_plan(parent, selected, audit, conf):
    return {
        "schema": "conway99.f0.core-blossom-runtime-plan.v1",
        "source_sha256": conf["source_sha256"],
        "configuration_sha256": sha(canonical(conf)),
        "parent_plan": conf["inputs"]["parent_plan"],
        "parent_preparation": conf["inputs"]["parent_report"],
        "parent_cold": conf["inputs"]["parent_cold"],
        "parent_proto_sha256": PARENT_RAW,
        "variable_count": VARIABLES,
        "full_target_constraints": NEW_COUNTS["target"],
        "initial_constraints": NEW_COUNTS["initial"],
        "initial_to_target_rows": parent["initial_to_target_rows"] + list(range(58957, 65811)),
        "external_pool_constraints": 117, "external_pool": parent["external_pool"],
        "target_variable_domains": parent["target_variable_domains"],
        "all_column_IDs_and_domains_unchanged": True,
        "appended_rows": [{"blossom_row_id": row["id"], "target_constraint": 58957 + i,
                           "initial_constraint": 58840 + i, "witness_ref": row["witness_ref"]}
                          for i, row in enumerate(selected)],
        "compact_inventory": {k: conf["inputs"][k] for k in ("inventory_report", "all_rows", "selected_rows", "omitted_rows")},
        "complete_box_omission_audit": audit,
        "full_target_pass_is_PROVISIONAL_until_original_parent_and_literal_checks": True,
        "count_or_literal_or_exterior_graph_feasibility_claimed": False,
        "optimizer_calls": 0,
    }


def prepare(output):
    assert not output.exists()
    started = time.monotonic()
    conf = definition()
    _, _, audit = semantic_inputs()
    record = {
        "status": "PASS: blossom append-only metadata preparation; no native import or construction",
        "definition": conf, "semantic_audit": audit, "seconds": time.monotonic() - started,
        "native_imported": False, "protobufs_parsed": False,
        "model_constructed": False, "optimizer_calls": 0, "CpSolver_constructed": False,
    }
    save(output, record)
    return record


def checked_preparation(path):
    raw = path.read_bytes()
    prepared = json.loads(raw)
    assert prepared["status"] == "PASS: blossom append-only metadata preparation; no native import or construction"
    assert prepared["definition"] == definition()
    assert not prepared["model_constructed"] and prepared["optimizer_calls"] == 0
    parent, selected, audit = semantic_inputs()
    assert audit == prepared["semantic_audit"]
    return prepared, sha(raw), parent, selected, audit


def packed_write(directory, name, raw):
    path = directory / name
    assert not path.exists()
    packed = gzip.compress(raw, compresslevel=6, mtime=0)
    path.write_bytes(packed)
    return {"path": str(path.relative_to(ROOT)), "sha256": sha(packed), "bytes": len(packed),
            "raw_sha256": sha(raw), "raw_bytes": len(raw)}


def exact_model_audit(runtime, target, initial, parent, selected, stage):
    for name, proto in (("target", target), ("initial", initial)):
        assert {field.name for field, _ in proto.ListFields()} == {"variables", "constraints"}
        assert len(proto.variables) == VARIABLES and len(proto.constraints) == NEW_COUNTS[name]
        assert [list(v.domain) for v in proto.variables] == parent["target_variable_domains"]
        for i, row in enumerate(selected):
            constraint = proto.constraints[PARENT_COUNTS[name] + i]
            assert {f.name for f, _ in constraint.ListFields()} == {"linear"}
            assert list(constraint.linear.vars) == [j for j, _ in row["terms"]]
            assert list(constraint.linear.coeffs) == [c for _, c in row["terms"]]
            assert list(constraint.linear.domain) == [0, row["rhs"]]
        raw = proto.SerializeToString()
        clone = runtime.cp_model_pb2.CpModelProto()
        clone.ParseFromString(raw)
        del raw
        del clone.constraints[PARENT_COUNTS[name]:]
        assert sha(clone.SerializeToString()) == PARENT_RAW[name]
        del clone
        gc.collect()
        stage(name + "_complete_parent_hash_restored_and_suffix_compared")
    row_ids = parent["initial_to_target_rows"] + list(range(58957, 65811))
    exact = runtime.exact_proto_check(initial, target, row_ids)
    assert exact["constraint_types"] == {"linear": 49370, "int_prod": 16280, "table": 44}
    assert exact["linear_terms"] == 798592 + 20542
    assert exact["variables"] == VARIABLES and exact["constraints"] == 65694
    assert Counter(c.WhichOneof("constraint") for c in target.constraints) == {"linear": 49487, "int_prod": 16280, "table": 44}
    for row in parent["external_pool"]:
        constraint = target.constraints[row["target_constraint"]]
        assert sha(constraint.SerializeToString()) == row["constraint_sha256"]
    return exact


def worker(mode, preparation, directory, model_directory, deadline):
    started = time.monotonic()
    stages = []
    def stage(name, **extra):
        stages.append({"stage": name, "seconds": time.monotonic() - started, **extra})
        save(directory / "stages.json", stages)
        if time.monotonic() >= deadline:
            raise TimeoutError("owned deadline")
    report = {"status": "INCOMPLETE", "optimizer_calls": 0, "CpSolver_constructed": False}
    save(directory / "report.json", report)
    try:
        prepared, prepared_sha, parent, selected, audit = checked_preparation(preparation)
        stage("frozen_inputs_partition_and_actual_omission_bounds_checked")
        query = load_source("query")
        runtime, loaded_plan, target, initial, _ = query.load_target(None, stage)
        assert loaded_plan["initial_to_target_rows"] == parent["initial_to_target_rows"]
        assert loaded_plan["external_pool"] == parent["external_pool"]
        plan = make_plan(parent, selected, audit, prepared["definition"])
        if mode == "build":
            for name, proto in (("target", target), ("initial", initial)):
                for i, row in enumerate(selected):
                    linear = proto.constraints.add().linear
                    linear.vars.extend(j for j, _ in row["terms"])
                    linear.coeffs.extend(c for _, c in row["terms"])
                    linear.domain.extend([0, row["rhs"]])
                    if (i + 1) % 1024 == 0:
                        stage(name + "_append_prefix", appended=i + 1)
            exact = exact_model_audit(runtime, target, initial, parent, selected, stage)
            outputs = {}
            for name, value in (("target", target), ("initial", initial)):
                outputs[name] = packed_write(directory, name + ".pb.gz", value.SerializeToString())
                stage(name + "_saved")
            outputs["plan"] = packed_write(directory, "plan.json.gz", canonical(plan) + b"\n")
            report = {
                "status": "PASS: complete append-only blossom protobuf overlay; no solver",
                "definition": prepared["definition"], "preparation_sha256": prepared_sha,
                "outputs": outputs, "native_initial_exact_checks": exact,
                "whole_parent_protobuf_hashes_restored": PARENT_RAW,
                "all117_pool_rows_and_IDs_unchanged": True,
                "all44_tables_and16280_products_unchanged": True,
                "native_public_constructor_not_repeated": True,
                "new_linear_rows_checked_directly_against_frozen_certificates": 2 * ADDED,
                "omission_audit": audit, "optimizer_calls": 0, "CpSolver_constructed": False,
            }
        else:
            assert mode == "cold" and model_directory is not None
            del target, initial
            gc.collect()
            built_raw = (model_directory / "report.json").read_bytes()
            built = json.loads(built_raw)
            assert built["status"] == "PASS: complete append-only blossom protobuf overlay; no solver"
            assert built["definition"] == prepared["definition"] and built["preparation_sha256"] == prepared_sha
            saved = {}
            for name in ("target", "initial", "plan"):
                info = built["outputs"][name]
                assert (ROOT / info["path"]).resolve() == (model_directory / (name + (".json.gz" if name == "plan" else ".pb.gz"))).resolve()
                packed = (ROOT / info["path"]).read_bytes()
                assert sha(packed) == info["sha256"] and len(packed) == info["bytes"]
                raw = gzip.decompress(packed)
                assert sha(raw) == info["raw_sha256"] and len(raw) == info["raw_bytes"]
                if name == "plan":
                    assert json.loads(raw) == plan
                else:
                    value = runtime.cp_model_pb2.CpModelProto()
                    value.ParseFromString(raw)
                    saved[name] = value
                del packed, raw
                stage(name + "_saved_archive_bound")
            exact = exact_model_audit(runtime, saved["target"], saved["initial"], parent, selected, stage)
            assert exact == built["native_initial_exact_checks"]
            assert built["omission_audit"] == audit
            report = {
                "status": "PASS: cold prefix restoration, complete suffix and omission replay",
                "definition": prepared["definition"], "preparation_sha256": prepared_sha,
                "model_report_sha256": sha(built_raw),
                "whole_parent_protobuf_hashes_restored": PARENT_RAW,
                "all_saved_plan_and_appended_coefficients_checked": True,
                "native_initial_exact_checks": exact, "omission_audit": audit,
                "family_census_or_model_construction_repeated": False,
                "optimizer_calls": 0, "CpSolver_constructed": False,
            }
        stage("complete")
        report["seconds"] = time.monotonic() - started
        save(directory / "report.json", report)
    except Exception as error:
        save(directory / "report.json", {
            "status": "ERROR_OR_INCOMPLETE", "error_type": type(error).__name__,
            "message": str(error), "seconds": time.monotonic() - started,
            "optimizer_calls": 0, "CpSolver_constructed": False,
        })
        raise


def owned(mode, preparation, directory, model_directory):
    assert not directory.exists()
    directory.mkdir(parents=True)
    started = time.monotonic()
    deadline = started + SECONDS
    raw = preparation.read_bytes()
    record = json.loads(raw)
    assert record["definition"]["source_sha256"] == file_sha(Path(__file__))
    owner = {"status": "UNKNOWN_BEFORE_CHILD", "report_accepted": False, "maximum_seconds": SECONDS,
             "preparation_sha256": sha(raw), "optimizer_calls": 0, "CpSolver_constructed": False}
    save(directory / "owner-result.json", owner)
    command = [sys.executable, str(Path(__file__).resolve()), "_worker", "--worker-mode", mode,
               "--preparation", str(preparation.resolve()), "--directory", str(directory.resolve()),
               "--deadline", repr(deadline)]
    if model_directory is not None:
        command += ["--model-directory", str(model_directory.resolve())]
    supervisor = load_source("supervisor")
    supervised = supervisor.supervise(command, directory, deadline)
    owner["supervisor"] = supervised
    owner["seconds"] = time.monotonic() - started
    if supervised["status"] == "CHILD_EXITED" and owner["seconds"] <= SECONDS:
        report_raw = (directory / "report.json").read_bytes()
        report = json.loads(report_raw)
        owner["report_accepted"] = report["status"].startswith("PASS")
        owner["report_sha256"] = sha(report_raw)
        owner["status"] = "PASS" if owner["report_accepted"] else "ERROR_OR_INCOMPLETE"
    else:
        owner["status"] = supervised["status"]
    save(directory / "owner-result.json", owner)
    return owner


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "build", "cold", "_worker"))
    parser.add_argument("--preparation", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--directory", type=Path)
    parser.add_argument("--model-directory", type=Path)
    parser.add_argument("--worker-mode", choices=("build", "cold"))
    parser.add_argument("--deadline", type=float)
    args = parser.parse_args()
    if args.mode == "prepare":
        assert args.output is not None
        result = prepare(args.output)
    elif args.mode == "_worker":
        assert args.preparation is not None and args.directory is not None and args.deadline is not None
        worker(args.worker_mode, args.preparation, args.directory, args.model_directory, args.deadline)
        return
    else:
        assert args.preparation is not None and args.directory is not None
        assert (args.mode == "cold") == (args.model_directory is not None)
        result = owned(args.mode, args.preparation, args.directory, args.model_directory)
    print(json.dumps({k: result[k] for k in ("status", "seconds", "report_accepted") if k in result}, indent=2))


if __name__ == "__main__":
    main()
