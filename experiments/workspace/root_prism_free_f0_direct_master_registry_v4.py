"""Reuse the accepted 133-row prefix and append 24 certified packing rows.

All arithmetic, normalization, range checks, native construction and new-cut
handling are imported unchanged from the frozen registry v3. This module
only binds the accepted receipts that extend its initial 37-row registry.
"""
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LEGACY = ("experiments/workspace/root_prism_free_f0_direct_master_registry_v3.py",
          "9b5746f3cc6817515d36fb8236bb5e26d78825187914d36a3da9f1ed1f616393")
PARENT_CONTROLLER = ("experiments/workspace/root_prism_free_f0_direct_master_continuation_v3.py",
                     "7b828cd3b5c34c846b97913e25bdb860bc7e75afdd7645701503f4a9760b2784")
PACKING_SOURCE = ("experiments/workspace/root_prism_free_f0_local_packing_candidate_batch.py",
                  "d4b975f2a70b8a5ba4372c0cc226490e2ffb6962b8af25199d4686c5bd730472")
PARENT_VALUE_SHA256 = "8b0459cabaa9676f2591a4ad2251fad269a1ed05f8f687e0bbb4204a5b8ea2bd"


def _load_legacy():
    path = ROOT / LEGACY[0]
    assert hashlib.sha256(path.read_bytes()).hexdigest() == LEGACY[1]
    spec = importlib.util.spec_from_file_location("frozen_master_registry_v3", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_legacy = _load_legacy()
digest, canonical, value_sha, save = [_legacy.__dict__[name] for name in
                                     ("digest", "canonical", "value_sha", "save")]
source, read, normalized, encode_domain, add_rows = [_legacy.__dict__[name] for name in
    ("source", "read", "normalized", "encode_domain", "add_rows")]
inspect_extra, append_expected, append_native, shared_rows, matching_rows, controls = [
    _legacy.__dict__[name] for name in
    ("inspect_extra", "append_expected", "append_native", "shared_rows", "matching_rows", "controls")]
MAX_EXTRA_ROWS, MAX_ACTIVITY = _legacy.MAX_EXTRA_ROWS, _legacy.MAX_ACTIVITY
assert MAX_EXTRA_ROWS == 256 and MAX_ACTIVITY == 1 << 60


def accepted_owner(owner, source_sha256, seconds, report_sha256):
    assert owner["source_sha256"] == source_sha256
    assert owner["maximum_seconds"] == seconds
    assert owner["report_accepted"] is True and owner["deadline_overrun_seconds"] == 0
    assert owner["report_sha256"] == report_sha256
    supervision = owner["supervision"]
    assert supervision["status"] == "CHILD_EXITED" and supervision["returncode"] == 0
    assert supervision["child_reaped"] and supervision["owned_process_group_stopped"]


def context(config_path, stage):
    config = json.loads(config_path.read_bytes())
    assert config["schema"] == "conway99.f0.accepted-prefix-plus-packing-seeds.v1"
    loaded = {key: read(config, key) for key in config["inputs"]}
    for path, expected in (PARENT_CONTROLLER, PACKING_SOURCE):
        assert digest(ROOT / path) == expected
    legacy_path = ROOT / config["inputs"]["legacy_configuration"]["path"]
    ctx = _legacy.context(legacy_path, stage)
    initial = ctx["registry"]
    assert len(initial) == 37

    run, owner, cold, cold_owner, inherited, replayed = [loaded[key] for key in
        ("parent_result", "parent_owner", "parent_cold", "parent_cold_owner",
         "parent_registry", "parent_replayed_registry")]
    accepted_owner(owner, PARENT_CONTROLLER[1], 300, config["inputs"]["parent_result"]["sha256"])
    accepted_owner(cold_owner, PARENT_CONTROLLER[1], 60, config["inputs"]["parent_cold"]["sha256"])
    assert run["source_sha256"] == PARENT_CONTROLLER[1]
    assert run["status"] == owner["status"] == cold["original_run_status"] == "ITERATION_LIMIT_WITH_UNQUERIED_GROWN_PREFIX"
    assert cold["status"] == cold_owner["status"] == "PASS_COMPLETE_CALLED_PREFIXES_AND_EXACT_CERTIFICATES"
    assert cold["run_owner_accepted"] is True and cold["optimizer_calls"] == 0
    assert cold["run_result_sha256"] == config["inputs"]["parent_result"]["sha256"]
    assert cold["run_owner_sha256"] == config["inputs"]["parent_owner"]["sha256"]
    assert run["definition"] == cold["definition"]
    assert run["seed_configuration_sha256"] == config["inputs"]["legacy_configuration"]["sha256"]
    assert run["definition"]["seed_configuration"] == loaded["legacy_configuration"] == ctx["config"]
    assert run["definition"]["seed_registry_sha256"] == value_sha(initial)
    assert run["definition"]["seed_rows"] == 37
    assert run["production_solve_calls"] == len(run["iterations"]) == len(cold["iterations"]) == 8
    assert all(row["direct_candidate_checked"] for row in cold["iterations"])
    assert inherited == replayed and inherited[:37] == initial and len(inherited) == 133
    assert value_sha(inherited) == PARENT_VALUE_SHA256 == run["final_registry_sha256"] == cold["final_replayed_registry_sha256"]
    assert run["final_registry_rows"] == cold["final_replayed_registry_rows"] == 133
    assert cold["iterations"][-1]["following_registry_rows"] == 133
    reconstructed, additions = add_rows(initial, [(entry["row"], entry["origin"]) for entry in inherited[37:]])
    assert reconstructed == inherited and len(additions) == 96
    assert all(entry["origin"]["kind"] == "shared" for entry in additions)
    assert sorted((entry["origin"]["iteration"], entry["origin"]["core_action_index"]) for entry in additions) == [
        (i, action) for i in range(8) for action in range(12)]
    stage("all133_accepted_parent_rows_and_provenance_bound")

    packing, packing_cold, packing_owner, packing_gate, packing_run, packing_run_owner = [loaded[key] for key in
        ("packing_cuts", "packing_cold", "packing_owner", "packing_root_gate", "packing_run", "packing_run_owner")]
    accepted_owner(packing_run_owner, PACKING_SOURCE[1], 60, config["inputs"]["packing_run"]["sha256"])
    accepted_owner(packing_owner, PACKING_SOURCE[1], 60, config["inputs"]["packing_cold"]["sha256"])
    assert packing_owner["certified_new_cuts"] is True
    assert packing["status"] == "CERTIFIED_UNIVERSAL_LOCAL_PACKING_BATCH_CUTS"
    assert packing["source_sha256"] == PACKING_SOURCE[1]
    assert packing_gate["status"] == "PASS_FULL_SOURCE_AND_MATHEMATICAL_REVIEW"
    assert packing_gate["bindings"]["source"] == {"path": PACKING_SOURCE[0], "sha256": PACKING_SOURCE[1]}
    assert packing["cold_report_sha256"] == config["inputs"]["packing_cold"]["sha256"]
    assert packing["cold_owner_sha256"] == config["inputs"]["packing_owner"]["sha256"]
    assert packing["run_owner_sha256"] == config["inputs"]["packing_run_owner"]["sha256"]
    assert packing_cold["run_report_sha256"] == config["inputs"]["packing_run"]["sha256"]
    assert packing_cold["run_owner_sha256"] == config["inputs"]["packing_run_owner"]["sha256"]
    assert packing_cold["status"] == packing_owner["status"] == "PASS_COLD_EXACT_LOCAL_PACKING_BATCH"
    assert packing_cold["definition"]["source_sha256"] == PACKING_SOURCE[1]
    assert packing_cold["definition"]["configuration_sha256"] == packing_gate["bindings"]["configuration"]["sha256"]
    assert packing_cold["preparation_sha256"] == packing_gate["bindings"]["preparation"]["sha256"]
    assert packing_run["definition"] == packing_cold["definition"]
    assert packing_cold["anchors_checked"] == 60 and packing_cold["optimizer_calls"] == 0
    assert packing_cold["termination"] == "COMPLETE_ALL60_ANCHORS"
    assert packing["rows_upper_zero"] == packing_cold["rows_upper_zero"]
    assert len(packing["rows_upper_zero"]) == 24
    proposed = [({"terms": terms, "rhs": 0},
                 {"kind": "seed_certified_local_packing_batch", "row_index": i,
                  "certificate_sha256": config["inputs"]["packing_cuts"]["sha256"],
                  "cold_owner_sha256": config["inputs"]["packing_owner"]["sha256"]})
                for i, terms in enumerate(packing["rows_upper_zero"])]
    registry, additions = add_rows(inherited, proposed)
    assert len(additions) == 24 and len(registry) == 157
    assert registry[:133] == inherited
    stage("all157_initial_rows_bound_without_prefix_drop_or_rewrite")
    ctx.update(config=config, config_sha256=digest(config_path), registry=registry)
    return ctx
