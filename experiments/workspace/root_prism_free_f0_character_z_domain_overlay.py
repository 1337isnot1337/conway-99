"""Certified Z-domain intersections on the frozen lightweight count target.

No constraint, variable ID, row map or external-pool entry changes. The
complete certified 9,353-orbit ledger supplies upper bounds only. The
earlier literal/certificate cold replay is bound, not repeated. Both modes
are optimizer-free and use one owned 60-second child.
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
LOGS = ROOT / "experiments/logs/root-prism-free"
RUNTIME = ("root_prism_free_f0_character_pool_runtime.py", "030163f019b93ee39124e9f3171caac1e4ad79227fde9a1e831c28a938b245f8")
PACKING = ("root_prism_free_f0_pair_orbit_packing.py", "857987075a72476a471660f37f6a683ad2e11adfe0389fd4c9c15e7858bac788")
INPUTS = {
    "packing_preparation": ("f0-pair-orbit-packing-preparation01.json.gz", "09412183bb01527a6fa2aeb23623b95af925767d5067bb363f10a2a8f8254a13"),
    "packing_gate": ("f0-pair-orbit-packing-root-source-review.json", "39e80a54e9d6572d1edd9952b6ab0cadc241dfa68de3627ddf15491aed9070b2"),
    "packing_result": ("f0-pair-orbit-packing-scan01.json.gz", "1bbba3061689f8faaf8fadcf556c0097d2b190673ab063a675259c007508b2bb"),
    "packing_ledger": ("f0-pair-orbit-packing-scan01-ledger.jsonl.gz", "4c53542bc89575b799b9e3d8b5905ae3dfe9782aa954db9d9afdf2a07c83d839"),
    "packing_cold": ("f0-pair-orbit-packing-scan01-cold.json", "c684243851efa7e12e9b9e5c7f857532421c1954233a5d9d6e24acfe5c826843"),
    "runtime_gate": ("f0-character-pool-runtime-root-source-review.json", "85b7141c67054184ed4520bf35b2fe9cf46f1510784e44cf59d7f0b259ff1cb9"),
    "runtime_result": ("f0-character-pool-runtime-initialization01/result.json", "f71e76c23008a4f518e326727e1a0e868fc3d76c006d5d074f17a74ebe1c6091"),
}
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


def runtime():
    path = ROOT / "experiments/workspace" / RUNTIME[0]
    assert file_sha(path) == RUNTIME[1]
    spec = importlib.util.spec_from_file_location("frozen_Z_domain_runtime", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def definition():
    r = runtime()
    assert file_sha(ROOT / "experiments/workspace" / PACKING[0]) == PACKING[1]
    for name, expected in INPUTS.values():
        assert file_sha(LOGS / name) == expected
    old = json.loads((LOGS / INPUTS["runtime_result"][0]).read_bytes())
    assert old["initialization_accepted"] and old["optimizer_calls"] == 0
    assert not old["CpSolver_constructed"]
    return {"schema": "conway99.f0-certified-Z-domain-overlay.v1",
            "source_sha256": file_sha(Path(__file__)),
            "runtime_source": {"path": RUNTIME[0], "sha256": RUNTIME[1]},
            "packing_source": {"path": PACKING[0], "sha256": PACKING[1]},
            "inputs": {k: {"path": str((LOGS / p).relative_to(ROOT)), "sha256": h}
                       for k, (p, h) in INPUTS.items()},
            "frozen_parent_definition": r.definition(),
            "retained_Z_columns": [5685, 15038], "retained_Z_orbits": 9353,
            "variables": 18444, "target_constraints": 34398, "initial_constraints": 34281,
            "external_pool_rows": 117, "maximum_owned_seconds": SECONDS,
            "only_certified_Z_domain_intersections_changed": True,
            "all_constraints_maps_variable_IDs_and_pool_entries_unchanged": True,
            "all_original_holes_preserved": True, "Y_domains_changed": False,
            "literal_graph_and_clique_cold_replay_bound_not_repeated": True,
            "optimizer_calls": 0, "CpSolver_constructed": False,
            "count_feasibility_or_exclusion_claimed": False}


def validate_domain(domain):
    assert domain and len(domain) % 2 == 0 and all(type(x) is int for x in domain)
    assert all(domain[i] <= domain[i + 1] for i in range(0, len(domain), 2))
    assert all(domain[i] + 1 < domain[i + 1] for i in range(1, len(domain) - 1, 2))


def intersect_upper(domain, upper):
    validate_domain(domain)
    assert type(upper) is int
    answer = []
    for lo, hi in zip(domain[::2], domain[1::2]):
        if lo > upper:
            break
        answer.extend((lo, min(hi, upper)))
    if answer:
        validate_domain(answer)
    return answer


def intersection_controls():
    cases = 0
    for mask in range(1, 32):
        values = [i - 2 for i in range(5) if mask >> i & 1]
        domain = []
        for value in values:
            if domain and value == domain[-1] + 1:
                domain[-1] = value
            else:
                domain.extend((value, value))
        for upper in range(-3, 4):
            found = intersect_upper(domain, upper)
            literal = [v for lo, hi in zip(found[::2], found[1::2]) for v in range(lo, hi + 1)]
            assert literal == [v for v in values if v <= upper]
            cases += 1
    assert cases == 217 and intersect_upper([0, 1, 3, 3], 2) == [0, 1]
    return {"status": "PASS", "exhaustive_signed_domain_and_bound_cases": cases,
            "empty_intersections_and_holes_checked": True, "optimizer_calls": 0}


def packing_intersections(old_domains):
    def read(key):
        name, expected = INPUTS[key]
        raw = (LOGS / name).read_bytes()
        assert sha(raw) == expected
        return json.loads(gzip.decompress(raw) if name.endswith(".gz") else raw)
    prep, result, cold = [read(key) for key in ("packing_preparation", "packing_result", "packing_cold")]
    assert prep["source_sha256"] == result["source_sha256"] == cold["source_sha256"] == PACKING[1]
    assert result["preparation_sha256"] == cold["preparation_sha256"] == INPUTS["packing_preparation"][1]
    assert cold["record_sha256"] == INPUTS["packing_result"][1]
    assert cold["status"].startswith("PASS") and cold["checked_orbits"] == 9353
    assert cold["complete_saved_prefix_checked"] and cold["maximum_clique_searches"] == 0
    assert result["complete"] and result["error"] is None and result["optimizer_calls"] == 0
    assert result["summary"]["completed_orbits"] == 9353
    assert result["ledger_sha256"] == INPUTS["packing_ledger"][1]
    r = runtime()
    assert result["inputs"]["current_plan"] == list(r.INPUTS["plan"])
    scope = prep["scope"]["retained_orbits"]
    assert len(scope) == 9353 and [s["count_column"] for s in scope] == list(range(5685, 15038))
    records, improvements, bounds = [], [], Counter()
    digest, raw_bytes = hashlib.sha256(), 0
    with gzip.open(LOGS / INPUTS["packing_ledger"][0], "rb") as stream:
        for i, saved in enumerate(scope):
            line = next(stream)
            digest.update(line)
            raw_bytes += len(line)
            certificate = json.loads(line)
            col = saved["count_column"]
            old = list(old_domains[col])
            assert saved["current_domain"] == old
            assert certificate["count_column"] == col
            assert certificate["pair_orbit"] == saved["pair_orbit"]
            assert certificate["previous_current_upper_bound"] == old[-1]
            upper = certificate["maximum_compatible_pair_objects"]
            assert type(upper) is int and 1 <= upper <= saved["orbit_size_upper_bound"] <= 12
            new = intersect_upper(old, upper)
            assert new and new[0] == old[0] == 0
            changed = new != old
            assert changed == (upper < old[-1]) == certificate["improves_current_upper_bound"]
            bounds[upper] += 1
            records.append({"ledger_index": i, "ledger_record_sha256": sha(line),
                            "pair_orbit": saved["pair_orbit"], "count_column": col,
                            "certified_upper": upper, "old_domain": old, "new_domain": new})
            if changed:
                improvements.append({"pair_orbit": saved["pair_orbit"], "count_column": col,
                                     "old_upper": old[-1], "new_upper": upper})
        assert not stream.read(1)
    assert raw_bytes == result["ledger_raw_bytes"] and digest.hexdigest() == result["ledger_raw_sha256"]
    assert improvements == result["summary"]["improved_current_bounds"] and len(improvements) == 8251
    assert canonical(dict(bounds)) == canonical({int(k): v for k, v in result["summary"]["clique_bound_histogram"].items()})
    return records


def constraint_digest(proto):
    digest = hashlib.sha256()
    for row in proto.constraints:
        raw = row.SerializeToString()
        digest.update(len(raw).to_bytes(8, "big"))
        digest.update(raw)
    return digest.hexdigest()


def derive(r, stage):
    slim, target, initial, _ = r.load_runtime(stage)
    old_plan = json.loads(gzip.decompress((LOGS / r.INPUTS["plan"][0]).read_bytes()))
    assert all(old_plan[k] == value for k, value in slim.items())
    old_domains = old_plan["target_variable_domains"]
    records = packing_intersections(old_domains)
    stage("complete9353_certified_domain_intersections_replayed")
    domains = [list(domain) for domain in old_domains]
    for record in records:
        domains[record["count_column"]] = record["new_domain"]
    unchanged = [j for j in range(18444) if domains[j] == old_domains[j]]
    changed = [j for j in range(18444) if domains[j] != old_domains[j]]
    assert len(changed) == 8251 and len(unchanged) == 10193
    assert all(5685 <= j < 15038 for j in changed)
    matrices = {}
    for name, proto, expected in (("target", target, r.TARGET_SHA), ("initial", initial, r.INITIAL_SHA)):
        assert [list(v.domain) for v in proto.variables] == old_domains
        before = constraint_digest(proto)
        for j in changed:
            proto.variables[j].domain[:] = domains[j]
        assert constraint_digest(proto) == before
        for j in changed:
            proto.variables[j].domain[:] = old_domains[j]
        assert sha(proto.SerializeToString()) == expected
        for j in changed:
            proto.variables[j].domain[:] = domains[j]
        matrices[name] = {"unchanged_constraint_payload_sha256": before,
                          "restoring_old_domains_reproduces_entire_parent_proto_sha256": expected}
    plan = dict(old_plan)
    plan["source_sha256"] = file_sha(Path(__file__))
    plan["target_variable_domains"] = domains
    plan["Z_domain_overlay"] = {"parent_plan": list(r.INPUTS["plan"]),
                                "parent_source_sha256": old_plan["source_sha256"],
                                "packing_result_sha256": INPUTS["packing_result"][1],
                                "packing_cold_sha256": INPUTS["packing_cold"][1],
                                "complete_intersections": records,
                                "changed_columns": changed, "unchanged_columns": unchanged,
                                "non_Z_columns_unchanged": 9091,
                                "retained_Z_domains_unchanged": 1102}
    assert {k: v for k, v in plan.items() if k not in ("source_sha256", "target_variable_domains", "Z_domain_overlay")} == {
        k: v for k, v in old_plan.items() if k not in ("source_sha256", "target_variable_domains")}
    checks = {"target": r.exact_proto_check(target, target, list(range(34398))),
              "initial": r.exact_proto_check(initial, target, plan["initial_to_target_rows"])}
    stage("all_constraints_maps_and_non_Z_domains_preserved")
    return plan, target, initial, matrices, checks


def archive(path, raw):
    path.write_bytes(gzip.compress(raw, mtime=0))
    return {"path": str(path.relative_to(ROOT)), "sha256": file_sha(path),
            "bytes": path.stat().st_size, "raw_sha256": sha(raw), "raw_bytes": len(raw)}


def worker(mode, directory, deadline, parent_directory=None):
    r, started, stages = runtime(), time.monotonic(), []
    def stage(name, **extra):
        stages.append({"stage": name, "elapsed_seconds": time.monotonic() - started,
                       "memory": r.memory_snapshot(), **extra})
        save(directory / "stages.json", {"stages": stages, "optimizer_calls": 0})
        if time.monotonic() > deadline:
            raise TimeoutError("owned Z-domain preparation deadline")
    try:
        stage("started_before_native_import")
        bound = definition()
        controls = intersection_controls()
        stage("source_bindings_and217_domain_controls_passed")
        r.import_native(stage)
        plan, target, initial, matrices, checks = derive(r, stage)
        if mode == "prepare":
            outputs = {"plan": archive(directory / "plan.json.gz", canonical(plan))}
            for name, proto in (("target", target), ("initial", initial)):
                outputs[name] = archive(directory / (name + ".pb.gz"), proto.SerializeToString())
            stage("new_plan_and_protobuf_archives_saved")
            model = r.cp_model.CpModel()
            variables = [model.new_int_var_from_domain(r.cp_model.Domain.from_flat_intervals(list(v.domain)), v.name)
                         for v in initial.variables]
            assert [v.index for v in variables] == list(range(18444))
            for i, constraint in enumerate(initial.constraints):
                r.append_constraint(model, variables, constraint)
                if (i + 1) % 4096 == 0:
                    stage("native_initial_prefix_constructed", constraints=i + 1)
            assert model.validate() == ""
            export = directory / "native-initial.pb"
            assert model.export_to_file(str(export))
            assert file_sha(export) == outputs["initial"]["raw_sha256"]
            assert export.stat().st_size == outputs["initial"]["raw_bytes"]
            stage("native_initial_validation_and_exact_byte_identity_passed")
            report = {"status": "PASS: certified Z-domain overlay and native initial preparation; no solver",
                      "definition": bound, "controls": controls, "outputs": outputs,
                      "parent_constraint_identity": matrices, "native_exact_checks": checks,
                      "changed_Z_domains": 8251, "unchanged_Z_domains": 1102,
                      "unchanged_non_Z_domains": 9091, "unchanged_total_domains": 10193,
                      "native_initial_public_constructor_byte_identity": True,
                      "full_target_native_public_constructor_repeated": False,
                      "optimizer_calls": 0, "CpSolver_constructed": False}
        else:
            assert mode == "cold" and parent_directory is not None
            old_raw = (parent_directory / "report.json").read_bytes()
            old = json.loads(old_raw)
            assert old["definition"] == bound and old["native_exact_checks"] == checks
            assert old["parent_constraint_identity"] == matrices
            for name, raw in (("plan", canonical(plan)), ("target", target.SerializeToString()),
                              ("initial", initial.SerializeToString())):
                entry = old["outputs"][name]
                path = ROOT / entry["path"]
                assert file_sha(path) == entry["sha256"]
                assert gzip.decompress(path.read_bytes()) == raw
                assert sha(raw) == entry["raw_sha256"] and len(raw) == entry["raw_bytes"]
            stage("all_saved_Z_intersections_and_entire_protobufs_cold_replayed")
            report = {"status": "PASS: complete Z-domain overlay cold replay; inherited clique proofs bound",
                      "source_sha256": file_sha(Path(__file__)), "preparation_sha256": sha(old_raw),
                      "definition": bound, "certified_orbits_checked": 9353,
                      "changed_Z_domains": 8251, "unchanged_total_domains": 10193,
                      "all_parent_constraints_and_maps_retained": True,
                      "native_constructor_repeated": False, "optimizer_calls": 0,
                      "CpSolver_constructed": False}
        report.update(seconds=time.monotonic() - started, terminal_memory=r.memory_snapshot(),
                      stages_sha256=file_sha(directory / "stages.json"))
        save(directory / "report.json", report)
    except Exception as error:
        stage("exception", error_type=type(error).__name__, message=str(error))
        save(directory / "error.json", {"error_type": type(error).__name__, "message": str(error),
                                        "memory": r.memory_snapshot(), "optimizer_calls": 0})
        raise


def owned(mode, directory, parent_directory=None):
    started, r = time.monotonic(), runtime()
    deadline = started + SECONDS
    definition()
    path = ROOT / r.SUPERVISOR_SOURCE
    spec = importlib.util.spec_from_file_location("frozen_Z_domain_owner", path)
    owner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(owner)
    directory.mkdir(parents=True, exist_ok=False)
    command = [sys.executable, str(Path(__file__).resolve()), "_" + mode,
               "--directory", str(directory.resolve()), "--deadline", str(deadline)]
    if parent_directory is not None:
        command.extend(("--parent-directory", str(parent_directory.resolve())))
    save(directory / "owner-result.json", {"status": "UNKNOWN_BEFORE_CHILD", "optimizer_calls": 0})
    supervision = owner.supervise(command, directory, deadline)
    result = {"status": supervision["status"], "supervision": supervision,
              "source_sha256": file_sha(Path(__file__)), "optimizer_calls": 0,
              "CpSolver_constructed": False, "maximum_owned_seconds": SECONDS,
              "report_accepted": False}
    if supervision["status"] == "CHILD_EXITED" and time.monotonic() <= deadline:
        report = json.loads((directory / "report.json").read_bytes())
        assert report["status"].startswith("PASS") and report["optimizer_calls"] == 0
        result.update(status=report["status"], report_accepted=True,
                      report_sha256=file_sha(directory / "report.json"))
    result.update(owner_seconds=time.monotonic() - started,
                  deadline_overrun_seconds=max(0, time.monotonic() - deadline))
    save(directory / "owner-result.json", result)
    print(json.dumps(result, indent=2), flush=True)


if __name__ == "__main__":
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
