"""Separate certified Y-domain layer over the immutable checked Z overlay.

All 5,643 retained Y columns receive their certified clique upper bound.
Only domain intersections change. Every original constraint, table, product,
external-pool entry and variable ID is preserved. No graph or clique census
is repeated; no CpSolver is constructed. Preparation and cold each have one
owned 60-second child.
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
Z_SOURCE = ("root_prism_free_f0_character_z_domain_overlay.py", "723841fafdfc151ef68e5b3877479361d38b84a06b86b83d9a7f69e0aed3460d")
Y_SOURCE = ("root_prism_free_f0_edge_orbit_packing.py", "694803bd3255fc3259290dac498e7ff2fa9cc2fb400ef7db552cf064c9329129")
INPUTS = {
    "Z_native": ("f0-character-z-domain-overlay01/report.json", "944cb8f1fdafd1e26260d3def404ffd7afde43e2fe93e97a6a258cc9bcbda6bd"),
    "Z_direct": ("f0-character-z-domain-overlay01-direct-replay/report.json", "39c002b640cdba66f18f4b3ea4282780089caf9aca47516cf4854075ccef9037"),
    "Z_direct_owner": ("f0-character-z-domain-overlay01-direct-replay/owner-result.json", "0bd6ee66bd208637bc67319dc2e4e099294d5205ab1ac1c958a2ceb4b85f4059"),
    "Z_plan": ("f0-character-z-domain-overlay01/plan.json.gz", "99a312d9a2694431adc30d5cbe8f7f344ea91e6f9ebe8fc997ba8e6d0df52ddf"),
    "Z_target": ("f0-character-z-domain-overlay01/target.pb.gz", "6ed622ba17fe8ee02fd8aff5fbf0192909719da298775e898c01465dfbb910b4"),
    "Z_initial": ("f0-character-z-domain-overlay01/initial.pb.gz", "9a7948ae71c545115917d426856a134df3ab466ee1c1dc6c8656e0e449a39332"),
    "Y_preparation": ("f0-edge-orbit-packing-census-preparation01.json", "3561840ec929ad68a6b4e22df8f6cad5e9a604b9828b9bc4cd63bdfa8654cdd0"),
    "Y_review": ("f0-edge-orbit-packing-census-literature-review.json", "e9e944e4618fcf1cb352d77901c228436462e1d20e970fd9e08ae0250373fe4c"),
    "Y_result": ("f0-edge-orbit-packing-scan01.json.gz", "5b9614ca91185e380bbc7fd220d797c983a5a4c6756942686f51efca57be1c2d"),
    "Y_cold": ("f0-edge-orbit-packing-scan01-cold.json", "8965162db2cd4bfc05c129ecd5cf0a1ba2b39bcbd35f776cc60c27a52c501ded"),
    "Y_ledger": ("f0-edge-orbit-packing-scan01-ledger.jsonl.gz", "75c5ba7443d0740e4ffa35828e70c25c28ffe4e18f398d2454315901f2cc7735"),
}
PARENT_RAW = {"target": "7deafd3d162f505873eaa2dfc2b532294ac99b058b54b84ba7cce73444016df1",
              "initial": "3337449ad74d102ba772d3d07472bf95ef378ba722118aa31be255e1c261e395"}
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


def helpers():
    path = ROOT / "experiments/workspace" / Z_SOURCE[0]
    assert file_sha(path) == Z_SOURCE[1]
    spec = importlib.util.spec_from_file_location("frozen_Y_layer_Z_helpers", path)
    z = importlib.util.module_from_spec(spec); spec.loader.exec_module(z)
    return z, z.runtime()


def read(key):
    name, expected = INPUTS[key]
    raw = (LOGS / name).read_bytes()
    assert sha(raw) == expected
    return json.loads(gzip.decompress(raw) if name.endswith(".gz") else raw)


def definition():
    z, _ = helpers()
    assert file_sha(ROOT / "experiments/workspace" / Y_SOURCE[0]) == Y_SOURCE[1]
    for name, expected in INPUTS.values():
        assert file_sha(LOGS / name) == expected
    return {"schema": "conway99.f0-certified-Y-domain-overlay.v1",
            "source_sha256": file_sha(Path(__file__)), "Z_source_sha256": Z_SOURCE[1],
            "Y_packing_source_sha256": Y_SOURCE[1], "frozen_Z_definition": z.definition(),
            "inputs": {k: {"path": str((LOGS / p).relative_to(ROOT)), "sha256": h} for k, (p, h) in INPUTS.items()},
            "retained_Y_columns": [42, 5685], "retained_Y_orbits": 5643,
            "variables": 18444, "target_constraints": 34398, "initial_constraints": 34281,
            "external_pool_rows": 117, "maximum_owned_seconds": SECONDS,
            "same_frozen_interval_intersection_helper_used": True,
            "all_Z_and_other_non_Y_domains_unchanged": True,
            "all_constraints_maps_and_variable_IDs_unchanged": True,
            "graph_or_clique_census_repeated": False, "optimizer_calls": 0,
            "CpSolver_constructed": False, "count_feasibility_or_exclusion_claimed": False}


def derive(stage):
    z, r = helpers()
    native, direct, owner = [read(k) for k in ("Z_native", "Z_direct", "Z_direct_owner")]
    assert native["status"].startswith("PASS") and native["definition"]["source_sha256"] == Z_SOURCE[1]
    assert direct["status"].startswith("PASS") and direct["subject_source_sha256"] == Z_SOURCE[1]
    assert owner["report_accepted"] and owner["report_sha256"] == INPUTS["Z_direct"][1]
    parent = read("Z_plan")
    assert parent["source_sha256"] == Z_SOURCE[1]
    old_domains = parent["target_variable_domains"]
    assert len(old_domains) == 18444
    prep, result, cold, review = [read(k) for k in ("Y_preparation", "Y_result", "Y_cold", "Y_review")]
    assert prep["source_sha256"] == result["source_sha256"] == cold["source_sha256"] == Y_SOURCE[1]
    assert review["status"].startswith("PASS")
    assert result["preparation_sha256"] == cold["preparation_sha256"] == INPUTS["Y_preparation"][1]
    assert cold["record_sha256"] == INPUTS["Y_result"][1]
    assert cold["status"].startswith("PASS") and cold["checked_orbits"] == 5643
    assert cold["complete_saved_prefix_checked"] and cold["maximum_clique_searches"] == 0
    assert result["complete"] and result["error"] is None
    assert result["summary"]["checked_orbits"] == 5643
    assert result["ledger_sha256"] == INPUTS["Y_ledger"][1]
    assert len(prep["prior_Z_clique_bounds_in_graph_order"]) == 5643
    domains, records, improved_Z, histogram = [list(d) for d in old_domains], [], [], Counter()
    digest, raw_bytes, edge_orbits = hashlib.sha256(), 0, []
    with gzip.open(LOGS / INPUTS["Y_ledger"][0], "rb") as stream:
        for i, col in enumerate(range(42, 5685)):
            line = next(stream); digest.update(line); raw_bytes += len(line)
            proof = json.loads(line)
            assert proof["count_column"] == col
            oi, upper, prior = proof["edge_orbit"], proof["bound"], proof["prior_Z_bound"]
            assert all(type(v) is int for v in (oi, upper, prior, proof["raw_orbit_bound"]))
            assert 0 <= oi < 5805 and 1 <= upper <= prior <= proof["raw_orbit_bound"] <= 12
            assert prior == prep["prior_Z_clique_bounds_in_graph_order"][i]
            old = old_domains[col]
            assert old[0] == 0 and old[-1] <= proof["raw_orbit_bound"]
            new = z.intersect_upper(old, upper)
            assert new and new[0] == 0
            domains[col] = new
            edge_orbits.append(oi); histogram[upper] += 1
            records.append({"ledger_index": i, "ledger_record_sha256": sha(line), "edge_orbit": oi,
                            "count_column": col, "certified_upper": upper, "prior_Z_bound": prior,
                            "old_domain": old, "new_domain": new})
            if upper < prior:
                improved_Z.append({k: proof[k] for k in ("edge_orbit", "count_column", "bound", "prior_Z_bound")})
        assert not stream.read(1)
    assert edge_orbits == sorted(set(edge_orbits)) and len(edge_orbits) == 5643
    assert raw_bytes == result["ledger_raw_bytes"] and digest.hexdigest() == result["ledger_raw_sha256"]
    assert dict(histogram) == {int(k): v for k, v in result["summary"]["bound_histogram"].items()}
    assert improved_Z == result["summary"]["improved_previous_Z_bounds"] and len(improved_Z) == 62
    changed = [j for j in range(18444) if domains[j] != old_domains[j]]
    unchanged = [j for j in range(18444) if domains[j] == old_domains[j]]
    assert all(42 <= j < 5685 for j in changed)
    assert all(domains[j] == old_domains[j] for j in list(range(42)) + list(range(5685, 18444)))
    stage("all5643_Y_domains_and_all12801_non_Y_domains_checked", changed_Y_domains=len(changed))
    plan = dict(parent)
    plan["source_sha256"] = file_sha(Path(__file__))
    plan["target_variable_domains"] = domains
    plan["Y_domain_overlay"] = {"parent_plan": list(INPUTS["Z_plan"]),
                                "parent_source_sha256": Z_SOURCE[1],
                                "Y_result_sha256": INPUTS["Y_result"][1], "Y_cold_sha256": INPUTS["Y_cold"][1],
                                "complete_intersections": records, "changed_columns": changed,
                                "unchanged_columns": unchanged, "non_Y_domains_unchanged": 12801,
                                "improved_over_transferred_Z_bound": 62}
    assert {k: v for k, v in plan.items() if k not in ("source_sha256", "target_variable_domains", "Y_domain_overlay")} == {
        k: v for k, v in parent.items() if k not in ("source_sha256", "target_variable_domains")}
    from ortools.sat import cp_model_pb2
    protos = {}
    for name, expected in PARENT_RAW.items():
        raw = gzip.decompress((LOGS / INPUTS["Z_" + name][0]).read_bytes())
        assert sha(raw) == expected
        proto = cp_model_pb2.CpModelProto(); proto.ParseFromString(raw)
        del raw
        assert [list(v.domain) for v in proto.variables] == old_domains
        for j in changed:
            proto.variables[j].domain[:] = domains[j]
        for j in changed:
            proto.variables[j].domain[:] = old_domains[j]
        assert sha(proto.SerializeToString()) == expected
        for j in changed:
            proto.variables[j].domain[:] = domains[j]
        protos[name] = proto
        gc.collect()
        stage(name + "_entire_Z_parent_hash_restored_by_domain_replacement")
    check = r.exact_proto_check(protos["initial"], protos["target"], plan["initial_to_target_rows"])
    # Domain subsets cannot increase any absolute row box sum or product bound.
    # The 1.3M-term target arithmetic census already passed in the Z preparation.
    return plan, protos, check, native["native_exact_checks"]["target"]


def worker(mode, directory, deadline, parent_directory=None):
    z, r = helpers(); started, stages = time.monotonic(), []
    def stage(label, **extra):
        stages.append({"stage": label, "elapsed_seconds": time.monotonic() - started,
                       "memory": r.memory_snapshot(), **extra})
        save(directory / "stages.json", {"stages": stages, "optimizer_calls": 0})
        if time.monotonic() > deadline:
            raise TimeoutError("owned Y-domain overlay deadline")
    try:
        stage("started")
        bound = definition()
        plan, protos, checked, inherited = derive(stage)
        changes = len(plan["Y_domain_overlay"]["changed_columns"])
        if mode == "prepare":
            outputs = {"plan": z.archive(directory / "plan.json.gz", canonical(plan))}
            for name, proto in protos.items():
                outputs[name] = z.archive(directory / (name + ".pb.gz"), proto.SerializeToString())
            stage("new_Y_archives_saved")
            r.import_native(stage)
            model = r.cp_model.CpModel()
            variables = [model.new_int_var_from_domain(r.cp_model.Domain.from_flat_intervals(list(v.domain)), v.name)
                         for v in protos["initial"].variables]
            assert [v.index for v in variables] == list(range(18444))
            for i, constraint in enumerate(protos["initial"].constraints):
                r.append_constraint(model, variables, constraint)
                if (i + 1) % 4096 == 0:
                    stage("native_initial_prefix_constructed", constraints=i + 1)
            assert model.validate() == ""
            export = directory / "native-initial.pb"
            assert model.export_to_file(str(export))
            assert file_sha(export) == outputs["initial"]["raw_sha256"]
            stage("native_initial_validation_and_exact_byte_identity_passed")
            report = {"status": "PASS: certified Y-domain layer and native initial preparation; no solver",
                      "definition": bound, "outputs": outputs, "native_initial_exact_checks": checked,
                      "inherited_full_target_signed64_upper_bound_checks": inherited,
                      "inherited_upper_bounds_remain_valid_by_domain_inclusion": True,
                      "changed_Y_domains": changes, "unchanged_Y_domains": 5643 - changes,
                      "unchanged_non_Y_domains": 12801, "improved_over_transferred_Z_bounds": 62,
                      "all_constraints_and_maps_unchanged": True,
                      "native_initial_public_constructor_byte_identity": True,
                      "restoring_old_domains_reproduces_Z_parent_raw_hashes": PARENT_RAW,
                      "optimizer_calls": 0, "CpSolver_constructed": False}
        else:
            assert mode == "cold" and parent_directory is not None
            old_raw = (parent_directory / "report.json").read_bytes(); old = json.loads(old_raw)
            assert old["definition"] == bound and old["native_initial_exact_checks"] == checked
            for name, raw in [("plan", canonical(plan))] + [(k, p.SerializeToString()) for k, p in protos.items()]:
                entry = old["outputs"][name]; path = ROOT / entry["path"]
                assert file_sha(path) == entry["sha256"]
                assert gzip.decompress(path.read_bytes()) == raw
                assert sha(raw) == entry["raw_sha256"] and len(raw) == entry["raw_bytes"]
            stage("all_saved_Y_domains_and_complete_protobufs_cold_checked")
            report = {"status": "PASS: complete Y-domain layer cold replay; graph proofs bound",
                      "source_sha256": file_sha(Path(__file__)), "preparation_sha256": sha(old_raw),
                      "definition": bound, "all5643_Y_domains_checked": True,
                      "all12801_non_Y_domains_unchanged": True, "changed_Y_domains": changes,
                      "complete_saved_plan_and_protobuf_byte_equality": True,
                      "native_model_construction_or_validation_repeated": False,
                      "optimizer_calls": 0, "CpSolver_constructed": False}
        report.update(seconds=time.monotonic() - started, terminal_memory=r.memory_snapshot(),
                      stages_sha256=file_sha(directory / "stages.json"))
        save(directory / "report.json", report)
    except Exception as error:
        stage("exception", error_type=type(error).__name__, message=str(error))
        save(directory / "error.json", {"error_type": type(error).__name__, "message": str(error),
                                        "memory": r.memory_snapshot(), "optimizer_calls": 0})
        raise


def owned(mode, directory, parent_directory=None):
    started = time.monotonic(); deadline = started + SECONDS
    _, r = helpers(); definition()
    path = ROOT / r.SUPERVISOR_SOURCE
    spec = importlib.util.spec_from_file_location("frozen_Y_domain_owner", path)
    owner = importlib.util.module_from_spec(spec); spec.loader.exec_module(owner)
    directory.mkdir(parents=True, exist_ok=False)
    command = [sys.executable, str(Path(__file__).resolve()), "_" + mode,
               "--directory", str(directory.resolve()), "--deadline", str(deadline)]
    if parent_directory is not None:
        command.extend(("--parent-directory", str(parent_directory.resolve())))
    save(directory / "owner-result.json", {"status": "UNKNOWN_BEFORE_CHILD", "optimizer_calls": 0})
    supervision = owner.supervise(command, directory, deadline)
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
