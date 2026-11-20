"""Preserve 253 accepted rows and append complete exact reanchored families.

The explicit registry bound is raised from 256 to 16384. add_rows is a new
function with that bound; no imported function's globals are modified.
All normalization, coefficient bounds and native row construction remain
the frozen implementation. The new packing rows are replayed as integers.
"""
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LEGACY = ("experiments/workspace/root_prism_free_f0_direct_master_registry_v4.py",
          "417eec796fed2f5704801f07de59a54107bfa08c59f15e4c0a1fffa6fec04a15")
PARENT_CONTROLLER = ("experiments/workspace/root_prism_free_f0_direct_master_continuation_v4.py",
                     "4c2950a430e2951b1afb337b2fb5392b36266c554194624caca20b5c28f4085f")
REANCHOR_REPLAY = ("experiments/workspace/root_prism_free_f0_local_packing_batch_reanchoring_replay.py",
                   "c91726c37f65bcc93b6bfdcb77449139e92ae0c2778925272fdf5518953ab689")
CENSUS_REPLAY = ("experiments/workspace/root_prism_free_f0_shared_single_anchor_reanchoring_replay.py",
                 "76df109a6d68bb16b7ddf90f9de3dd9240ec3699f363c88fa58f0965b3070629")
CENSUS_EXPORT = ("experiments/workspace/root_prism_free_f0_shared_single_anchor_export.py",
                 "b79cb59d0bc4e57129d425a0d1d1d1fd058f80c3eb4d27bd99a43181f1eb0b52")
PARENT_VALUE_SHA256 = "60b1fb603fac83d953f87a51ae5e9675c40f1a79d0e1a4855d70839e2255dc98"


def load_module(binding, name):
    path, expected = binding
    path = ROOT / path
    assert hashlib.sha256(path.read_bytes()).hexdigest() == expected
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_legacy = load_module(LEGACY, "frozen_master_registry_v4")
digest, canonical, value_sha, save = [_legacy.__dict__[name] for name in
                                     ("digest", "canonical", "value_sha", "save")]
source, normalized, encode_domain = [_legacy.__dict__[name] for name in
                                    ("source", "normalized", "encode_domain")]
inspect_extra, append_expected, append_native, shared_rows, matching_rows = [
    _legacy.__dict__[name] for name in
    ("inspect_extra", "append_expected", "append_native", "shared_rows", "matching_rows")]
accepted_owner = _legacy.accepted_owner
assert _legacy.MAX_EXTRA_ROWS == 256 and _legacy.MAX_ACTIVITY == 1 << 60
MAX_EXTRA_ROWS, MAX_ACTIVITY = 16384, _legacy.MAX_ACTIVITY


def read(config, name):
    item = config["inputs"][name]
    data = (ROOT / item["path"]).read_bytes()
    assert hashlib.sha256(data).hexdigest() == item["sha256"]
    raw = gzip.decompress(data) if item["path"].endswith(".gz") else data
    if "raw_sha256" in item:
        assert hashlib.sha256(raw).hexdigest() == item["raw_sha256"]
    return json.loads(raw)


def add_rows(registry, proposed):
    """Validate the complete batch before changing the append-only registry."""
    seen = {entry["key"] for entry in registry}
    additions = []
    for row, origin in proposed:
        row = normalized(row["terms"], row["rhs"])
        encode_domain(row)
        key = value_sha(row)
        if key not in seen:
            seen.add(key)
            additions.append({"key": key, "row": row, "origin": origin})
    if len(registry) + len(additions) > MAX_EXTRA_ROWS:
        raise OverflowError("exact registry row limit reached; preserve proposed cuts and stop")
    return registry + additions, additions


def controls():
    old = _legacy.controls()
    proposed = [({"terms": [[0, 1]], "rhs": rhs}, {"toy": rhs}) for rhs in range(MAX_EXTRA_ROWS + 1)]
    registry, additions = add_rows([], proposed[:MAX_EXTRA_ROWS])
    assert len(registry) == len(additions) == MAX_EXTRA_ROWS
    before = canonical(registry)
    try:
        add_rows(registry, proposed[MAX_EXTRA_ROWS:])
    except OverflowError:
        pass
    else:
        raise AssertionError("first row beyond declared capacity accepted")
    assert canonical(registry) == before
    assert _legacy.MAX_EXTRA_ROWS == 256
    return {"status": "PASS_FROZEN_ARITHMETIC_AND_NEW16384_ROW_BOUNDARY",
            "legacy_controls": old, "accepted_boundary_rows": MAX_EXTRA_ROWS,
            "refused_whole_batch_rows": 1, "legacy_globals_unchanged": True,
            "solver_calls": 0}


def context(config_path, stage):
    config = json.loads(config_path.read_bytes())
    assert config["schema"] == "conway99.f0.accepted-prefix-plus-reanchored-seeds.v1"
    loaded = {key: read(config, key) for key in config["inputs"]}
    assert digest(ROOT / PARENT_CONTROLLER[0]) == PARENT_CONTROLLER[1]
    legacy_path = ROOT / config["inputs"]["legacy_configuration"]["path"]
    ctx = _legacy.context(legacy_path, stage)
    initial = ctx["registry"]
    assert len(initial) == 157
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
    assert run["definition"]["seed_rows"] == 157
    assert run["production_solve_calls"] == len(run["iterations"]) == len(cold["iterations"]) == 8
    assert all(row["direct_candidate_checked"] for row in cold["iterations"])
    assert inherited == replayed and inherited[:157] == initial and len(inherited) == 253
    assert value_sha(inherited) == PARENT_VALUE_SHA256 == run["final_registry_sha256"] == cold["final_replayed_registry_sha256"]
    assert run["final_registry_rows"] == cold["final_replayed_registry_rows"] == 253
    assert cold["iterations"][-1]["following_registry_rows"] == 253
    reconstructed, additions = add_rows(initial, [(entry["row"], entry["origin"]) for entry in inherited[157:]])
    assert reconstructed == inherited and len(additions) == 96
    assert all(entry["origin"]["kind"] == "shared" for entry in additions)
    assert sorted((entry["origin"]["iteration"], entry["origin"]["core_action_index"]) for entry in additions) == [
        (i, action) for i in range(8) for action in range(12)]
    stage("all253_accepted_parent_rows_and_provenance_bound")

    certificate = config["reanchoring_certificate"]
    certificate_path = ROOT / certificate["path"]
    assert digest(certificate_path) == certificate["sha256"]
    checker = load_module(REANCHOR_REPLAY, "frozen_independent_reanchoring_replay")
    fresh = checker.replay(certificate_path)
    saved = loaded["reanchoring_cold"]
    assert canonical(fresh) == canonical({k: v for k, v in saved.items() if k != "seconds"})
    assert fresh["status"] == "PASS_INDEPENDENT_COMPLETE_REANCHORED_PACKING_ARITHMETIC"
    assert fresh["source_sha256"] == REANCHOR_REPLAY[1]
    assert fresh["certificate_sha256"] == certificate["sha256"]
    assert fresh["all480_eligible_domains_reconstructed"] and fresh["optimizer_calls"] == 0
    terms_list = fresh["new_rows_upper_zero_vs_frozen157"]
    assert len(terms_list) == fresh["counts"]["new_rows_vs_frozen157"] == 48
    proposed = [({"terms": terms, "rhs": 0},
                 {"kind": "seed_reanchored_local_packing", "row_index": i,
                  "certificate_sha256": certificate["sha256"],
                  "independent_replay_sha256": config["inputs"]["reanchoring_cold"]["sha256"],
                  "independent_replay_source_sha256": REANCHOR_REPLAY[1]})
                for i, terms in enumerate(terms_list)]
    registry, additions = add_rows(inherited, proposed)
    assert len(additions) == 48 and len(registry) == 301
    assert registry[:253] == inherited
    stage("all301_parent_and_packing_rows_bound_without_prefix_drop_or_rewrite")

    assert digest(ROOT / CENSUS_REPLAY[0]) == CENSUS_REPLAY[1]
    assert digest(ROOT / CENSUS_EXPORT[0]) == CENSUS_EXPORT[1]
    census_cold, census_export = loaded["shared_census_cold"], loaded["shared_census_export"]
    assert census_cold["status"] == "PASS_INDEPENDENT_COMPLETE_SHARED_CENSUS_AND_DIRECT_COVERAGE"
    assert census_cold["source_sha256"] == CENSUS_REPLAY[1]
    assert census_cold["prefix253_value_sha256"] == PARENT_VALUE_SHA256
    assert census_cold["complete_attempts_checked"] == 54720
    assert census_cold["complete_raw_rows_checked"] == 12204
    assert census_cold["direct_coverage_witnesses_checked"] == 12168
    assert census_cold["optimizer_calls"] == census_cold["native_imports"] == 0
    assert not census_cold["producer_reducer_or_dominance_imported"]
    assert census_cold["all_original4416_and_planned301_must_remain"]
    assert census_export["status"] == "CERTIFIED_COMPLETE_SHARED_SINGLE_ANCHOR_REANCHORED_ROWS"
    assert census_export["source_sha256"] == CENSUS_EXPORT[1]
    assert census_export["inputs"]["cold_source"] == list(CENSUS_REPLAY)
    assert census_export["inputs"]["cold"] == [config["inputs"]["shared_census_cold"]["path"], config["inputs"]["shared_census_cold"]["sha256"]]
    assert census_export["independent_cold_raw_sha256"] == config["inputs"]["shared_census_cold"]["raw_sha256"]
    assert census_export["full_export_raw_sha256"] == census_cold["retained_export_sha256"]
    assert census_export["configuration_sha256"] == census_cold["configuration_sha256"]
    assert census_export["bank_sha256"] == census_cold["bank_sha256"]
    assert census_export["complete_census"]["sha256"] == census_cold["complete_census_sha256"]
    assert census_export["dominance"]["sha256"] == census_cold["dominance_sha256"]
    assert census_export["prefix253_value_sha256"] == PARENT_VALUE_SHA256
    peer = loaded["shared_census_peer"]
    assert census_export["inputs"]["peer_review"] == [config["inputs"]["shared_census_peer"]["path"], config["inputs"]["shared_census_peer"]["sha256"]]
    assert peer["status"] == "PASS_COMPLETE_INDEPENDENT_REPLAY_SOURCE_REVIEW" and not peer["blockers"]
    assert peer["cold"]["sha256"] == config["inputs"]["shared_census_cold"]["raw_sha256"]
    assert census_export["all_original4416_and_planned301_must_remain"] and census_export["no_rows_selected_or_removed_during_export"]
    assert census_export["optimizer_calls"] == census_export["native_imports"] == 0
    assert census_export["rows_upper_zero"] == census_cold["rows_upper_zero"]
    assert len(census_export["rows_upper_zero"]) == len(census_export["row_provenance"]) == 12168
    proposed = [({"terms": terms, "rhs": 0},
                 {"kind": "seed_certified_reanchored_shared", "row_index": i,
                  "certificate_sha256": config["inputs"]["shared_census_export"]["sha256"],
                  "independent_cold_raw_sha256": config["inputs"]["shared_census_cold"]["raw_sha256"],
                  "row_provenance": provenance})
                for i, (terms, provenance) in enumerate(zip(census_export["rows_upper_zero"], census_export["row_provenance"]))]
    complete, additions = add_rows(registry, proposed)
    assert len(additions) == 12168 and len(complete) == 12469
    assert all(entry["key"] == entry["origin"]["row_provenance"]["capped_row_key"] for entry in additions)
    assert complete[:301] == registry and complete[:253] == inherited
    stage("all12469_initial_rows_bound_without_prefix_drop_or_rewrite")
    ctx.update(config=config, config_sha256=digest(config_path), registry=complete,
               maximum_registry_rows=MAX_EXTRA_ROWS)
    return ctx
