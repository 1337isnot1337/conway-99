"""Exact intake of an accepted native count vector for the frozen literal lift.

No local subset enumeration or optimizer is performed. The original inverse
tables, character orientation, CSP kernel and controls remain unchanged.
The future production wrapper must supply a separately accepted count receipt.
"""
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
BASE = "experiments/logs/root-prism-free/"
SOURCES = {
    "kernel": ("root_prism_free_f0_literal_lift_csp.py", "15f139b54d5daebd5adbd4e4d475ff9a9734a52725abd7ac130984b5328fabfb"),
    "lift": ("root_prism_free_f0_character_literal_lift.py", "3bf7f92502592bcda0b4dc71868a6745888c608b26d3f8e42f2771cf180c7252"),
    "supervisor": ("root_prism_free_f0_local_neighbors_batch.py", "b8e5323f92fa105ff2c0ed5b1667ac25d7c92f85f8cac45b170ddc56208f8278"),
}
INPUTS = {
    "inverse": ("f0-character-literal-lift-preparation01.json.gz", "241cd14c61b465025c72ffcaa65af8e5c48e9e5a0eda7ea7d252e9d74b22db1e"),
    "inverse_cold": ("f0-character-literal-lift-preparation01-cold.json", "6cebe725527eaf28f3d075a3ad9741fcbcf50cdedd42107bdc5ebcbe857da72f"),
    "namespace": ("f0-character-cpsat01/report.json", "e15c4bfcf7adaabb60258e3cffa8046eb0cd97843ae8787a24b356011d7b8a5f"),
    "supervisor_controls": ("f0-character-query-preparation01/preparation.json", "c480e2df6dbec03d95d3c8c1f387933b28c7e212c9e86a33d0b7f349451d4384"),
    "target_plan": ("f0-character-y-domain-overlay01/plan.json.gz", "4d3a13718cdac9fcf68b119a1cd1ba009edeb21c7257d4498d5ebdf18954acc4"),
    "target_preparation": ("f0-character-y-domain-overlay01/report.json", "a4a543b35bdd22357eef39524ff8015e0d4d274547c046205c806a5f52e92061"),
    "query_preparation": ("f0-character-packing-light-query-preparation01/preparation.json", "b8bce3bd80f42417df1fc360fc8663eb8f3f9a3c1066606c864c3ac4e24d5cb4"),
    "moments": ("f0-second-moments-preparation02.json.gz", "404d91da35c798ba248887c22a7500957947e24b71d5197dc44432460e6d219e"),
    "characters": ("f0-character-populations01.json.gz", "139d06a3383f8fc79d677972ce052ce29966e8b3406e7d1e7d1077aea7c2cef6"),
}
NAMESPACES = {"original_counts": [0, 15038], "trivial_products": [15038, 15941],
              "signed_populations": [15941, 16059], "signed_products": [16059, 18444]}
TARGET_PROTO_SHA = "a738d318b6b8de471ee7383f1e6ea11949eed8f8ccf4892814fa2eac268ed153"
LIMITS = {"owned_seconds": 60, "candidate_relation_seconds": 15, "CSP_search_seconds": 30,
          "maximum_CSP_nodes": 4096, "finalization_reserve_seconds": 10,
          "maximum_raw_output_bytes": 64 * 1024 * 1024, "CSP_search_calls": 1,
          "optimizer_calls": 0, "automatic_retries": 0}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def tick(deadline):
    if time.monotonic() >= deadline:
        raise TimeoutError("literal-lift intake deadline")


def source_module(key):
    filename, expected = SOURCES[key]
    path = ROOT / "experiments/workspace" / filename
    assert sha(path.read_bytes()) == expected
    name = path.stem
    if name in sys.modules:
        module = sys.modules[name]
        assert sha(Path(module.__file__).read_bytes()) == expected
        return module
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def read_input(key):
    name, expected = INPUTS[key]
    raw = (ROOT / BASE / name).read_bytes()
    assert sha(raw) == expected, key
    return json.loads(gzip.decompress(raw) if name.endswith(".gz") else raw)


def load_inputs(deadline):
    for filename, expected in SOURCES.values():
        assert sha((ROOT / "experiments/workspace" / filename).read_bytes()) == expected
    kernel = source_module("kernel")
    lift = source_module("lift")
    inverse, cold, namespace, controls, plan, target = [
        read_input(k) for k in ("inverse", "inverse_cold", "namespace", "supervisor_controls",
                               "target_plan", "target_preparation")]
    assert inverse["sources"] == {"domain": SOURCES["lift"][1], "csp_kernel": SOURCES["kernel"][1]}
    assert cold["status"].startswith("PASS") and cold["record_sha256"] == INPUTS["inverse"][1]
    assert cold["production_candidates_evaluated"] == cold["optimizer_calls"] == 0
    assert namespace["namespaces"] == NAMESPACES
    assert controls["controls"]["status"] == "PASS"
    assert controls["definition"]["sources"]["supervisor"]["sha256"] == SOURCES["supervisor"][1]
    assert [r["status"] for r in controls["controls"]["owned_child_stop_controls"]] == [
        "CHILD_EXITED", "ERROR_CHILD_EXIT", "UNKNOWN_HARD_DEADLINE"]
    assert inverse["kernel_controls"]["exhaustive_three_binary_variable_systems"] == 4096
    assert inverse["kernel_controls"]["false_deletion_rejected"]
    assert target["outputs"]["plan"]["sha256"] == INPUTS["target_plan"][1]
    assert target["outputs"]["target"]["raw_sha256"] == TARGET_PROTO_SHA
    assert target["definition"]["all_constraints_maps_and_variable_IDs_unchanged"]
    assert target["definition"]["all_Z_and_other_non_Y_domains_unchanged"]
    query = read_input("query_preparation")
    assert query["definition"]["target_proto_sha256"] == TARGET_PROTO_SHA
    assert query["definition"]["inputs"]["model_preparation"]["sha256"] == INPUTS["target_preparation"][1]
    assert query["definition"]["inputs"]["plan"]["sha256"] == INPUTS["target_plan"][1]
    assert query["definition"]["full_target_pass_is_PROVISIONAL_only"]
    assert query["definition"]["separate_full_restored_parent_arithmetic_receipt_required"]
    assert plan["variable_count"] == 18444
    assert plan["old_to_target_columns"] == list(range(18444))
    assert plan["target_to_old_columns"] == list(range(18444))
    domains = plan["target_variable_domains"]
    assert len(domains) == 18444
    for domain in domains:
        assert domain and len(domain) % 2 == 0 and all(type(v) is int for v in domain)
        assert all(domain[i] <= domain[i + 1] for i in range(0, len(domain), 2))
        assert all(domain[i] + 1 < domain[i + 1] for i in range(1, len(domain) - 1, 2))
    # Keep only the literal data used by the frozen witness inspector.
    moments = read_input("moments")
    moments = {k: moments[k] for k in ("pair_to_orbit", "original_selector_equalities")}
    characters = read_input("characters")
    characters = {"signed_populations": characters["signed_populations"]}
    tick(deadline)
    return inverse, domains, {"moments": moments, "characters": characters}, lift, kernel


def restore_projection(inverse, values, lift):
    assert isinstance(values, list) and len(values) == 18444
    assert all(type(v) is int for v in values)
    return lift.projection_from_count_columns(inverse, values[:15038], values[15941:16059])


def check_domains(values, domains):
    assert len(values) == len(domains) == 18444
    assert all(type(v) is int for v in values)
    failed = [i for i, (v, d) in enumerate(zip(values, domains))
              if not any(d[j] <= v <= d[j + 1] for j in range(0, len(d), 2))]
    assert not failed, ("native_domain_failures", failed)
    return {"all18444_exact_native_domains_pass": True}


def check_receipt(receipt, candidate_sha, vector_sha, query_sha, acceptance_source_sha):
    assert receipt["status"] == "EXACT_COUNT_WITNESS"
    for key in ("accepted", "count_feasibility_claimed", "full_target_checks_passed",
                "restored_original_parent_checks_passed"):
        assert receipt[key] is True, key
    assert receipt["candidate_file_sha256"] == candidate_sha
    assert receipt["canonical_integer_vector_sha256"] == vector_sha
    assert receipt["target_proto_sha256"] == TARGET_PROTO_SHA
    assert receipt["model_preparation_sha256"] == INPUTS["target_preparation"][1]
    assert receipt["query_preparation_sha256"] == query_sha
    assert query_sha == INPUTS["query_preparation"][1]
    assert receipt["acceptance_source_sha256"] == acceptance_source_sha


def admit(candidate_path, receipt_path, query_preparation_path, receipt_source_path, inverse, domains, lift):
    candidate_raw = candidate_path.read_bytes()
    receipt_raw = receipt_path.read_bytes()
    query_raw = query_preparation_path.read_bytes()
    acceptance_source_sha = sha(receipt_source_path.read_bytes())
    values, receipt = json.loads(candidate_raw), json.loads(receipt_raw)
    assert isinstance(values, list) and len(values) == 18444 and all(type(v) is int for v in values)
    vector_sha = sha(canonical(values))
    check_receipt(receipt, sha(candidate_raw), vector_sha, sha(query_raw), acceptance_source_sha)
    domain_check = check_domains(values, domains)
    projection = restore_projection(inverse, values, lift)
    return {"candidate_file_sha256": sha(candidate_raw), "canonical_integer_vector_sha256": vector_sha,
            "acceptance_receipt_sha256": sha(receipt_raw), "query_preparation_sha256": sha(query_raw),
            "acceptance_source_sha256": acceptance_source_sha,
            "model_preparation_sha256": INPUTS["target_preparation"][1],
            "target_proto_sha256": TARGET_PROTO_SHA, "native_domain_checks": domain_check,
            "projection": projection, "projection_sha256": sha(canonical(projection)),
            "native_values": values}


def receipt_controls():
    # Pure schema checks. These fixtures are not accepted graph/count points.
    valid = {"status": "EXACT_COUNT_WITNESS", "accepted": True,
             "count_feasibility_claimed": True, "full_target_checks_passed": True,
             "restored_original_parent_checks_passed": True,
             "candidate_file_sha256": "1" * 64, "canonical_integer_vector_sha256": "2" * 64,
             "target_proto_sha256": TARGET_PROTO_SHA,
             "model_preparation_sha256": INPUTS["target_preparation"][1],
             "query_preparation_sha256": INPUTS["query_preparation"][1],
             "acceptance_source_sha256": "4" * 64}
    check_receipt(valid, "1" * 64, "2" * 64, INPUTS["query_preparation"][1], "4" * 64)
    rejected = []
    for field in valid:
        bad = dict(valid)
        bad[field] = False if type(valid[field]) is bool else "PROVISIONAL_OR_WRONG_BINDING"
        try:
            check_receipt(bad, "1" * 64, "2" * 64, INPUTS["query_preparation"][1], "4" * 64)
        except AssertionError:
            rejected.append(field)
        else:
            raise AssertionError(("bad_receipt_accepted", field))
    return {"synthetic_receipt_schema_controls_only": True,
            "positive_schema_case": 1, "mutated_fields_rejected": rejected,
            "production_candidates_evaluated": 0}


def configuration(deadline):
    inverse, domains, context, lift, kernel = load_inputs(deadline)
    tables, blocks = inverse["inverse_tables"], inverse["cross_pair_blocks"]
    assert len(tables) == 42 and len(blocks) == 861
    assert sorted(a for t in tables for a in t["literal_selectors"]) == list(range(480))
    assert len(inverse["original_zero_pair_orbits"]) == 389
    assert len(inverse["new15038_to_original15589"]) == 15038
    cross = [p for b in blocks for p in b["original_pair_orbits"]]
    assert sorted(cross + inverse["original_within_pair_orbits"]) == list(range(9742))
    for table in tables:
        assert table["count_columns"][0] == table["selector_orbit"]
        assert all(inverse["new15038_to_original15589"][j] >= 5847 for j in table["count_columns"][1:])
        assert all(0 <= j < 118 for j in table["signed_population_columns"])
        assert max(len(p["local_masks"]) for p in table["profiles"]) <= 12
    controls = []
    # Reuse the saved positive literal fixtures only to test the new native-ID
    # adapter. Do not repeat any old CSP search or local subset enumeration.
    for saved in inverse["reconstruction_controls"]["synthetic_positive_reconstructions"]:
        point = lift.projection_of_selection(inverse, context, saved["synthetic_selection"])
        assert sha(canonical(point)) == saved["projection_sha256"]
        values = [0] * 18444
        values[:42] = point["selector_populations"]
        for new, old in enumerate(inverse["new15038_to_original15589"]):
            if old >= 5847:
                values[new] = point["original_pair_populations"][old - 5847]
        # Sentinels prove auxiliary namespaces are not read as signed populations.
        values[15038:15941] = [-999999] * (15941 - 15038)
        values[15941:16059] = point["signed_populations"]
        values[16059:] = [999999] * (18444 - 16059)
        assert restore_projection(inverse, values, lift) == point
        controls.append({"saved_projection_sha256": saved["projection_sha256"],
                         "exact_native_namespace_roundtrip": True,
                         "auxiliary_sentinels_are_native_candidates": False})
    tick(deadline)
    return {"schema": "conway99.f0.literal_lift_intake.preparation.v1",
            "status": "PASS: accepted-count intake prepared; no production candidate",
            "source_sha256": sha(Path(__file__).read_bytes()), "sources": SOURCES, "inputs": INPUTS,
            "target_proto_sha256": TARGET_PROTO_SHA, "native_namespaces": NAMESPACES,
            "target_domains_sha256": sha(canonical(domains)),
            "inverse_inventory": inverse["inventory"], "acceptance_status_required": "EXACT_COUNT_WITNESS",
            "accepted_receipt_boolean_fields": ["accepted", "count_feasibility_claimed",
                                               "full_target_checks_passed", "restored_original_parent_checks_passed"],
            "provisional_or_native_status_is_insufficient": True,
            "separate_source_bound_parent_acceptance_is_an_external_required_premise": True,
            "parent_acceptance_checker_not_implemented_at_this_preparation": True,
            "full_count_arithmetic_repeated_by_this_intake": False,
            "production_query_authorized_by_this_preparation": False,
            "namespace_adapter_controls": controls, "receipt_schema_controls": receipt_controls(),
            "old_controls_reexecuted": False,
            "new_local_subset_enumerations": 0, "production_candidates_evaluated": 0,
            "CSP_search_calls": 0, "optimizer_calls": 0, "limits": LIMITS,
            "scope": "Realize one accepted fixed count projection as literal selectors. Original172 selector equalities are checked separately. No exterior Y edges or full graph are realized."}


def search(admission, inverse, context, lift, kernel, deadline, checkpoint=lambda name, value: None):
    remaining = deadline - time.monotonic() - LIMITS["finalization_reserve_seconds"]
    if remaining <= 0:
        raise TimeoutError("no candidate-relation time remains")
    bundle = lift.candidate_problem(inverse, admission["projection"],
                                    seconds=min(LIMITS["candidate_relation_seconds"], remaining))
    assert bundle["projection_sha256"] == admission["projection_sha256"]
    assert len(bundle["literal_mask_domains"]) == 42 and len(bundle["problem"]["relations"]) == 861
    assert bundle["all_original_zero_pair_targets_explicit"]
    assert not bundle["independent_local_relabeling_used"] and not bundle["exterior_Y_edges_in_scope"]
    checkpoint("bundle", bundle)
    remaining = deadline - time.monotonic() - LIMITS["finalization_reserve_seconds"]
    if remaining <= 0:
        raise TimeoutError("no CSP search time remains")
    result = kernel.solve(bundle["problem"], seconds=min(LIMITS["CSP_search_seconds"], remaining),
                          maximum_nodes=LIMITS["maximum_CSP_nodes"])
    # Retain the returned partial tree before its independent arithmetic replay.
    checkpoint("CSP_result", result)
    checked = kernel.replay(bundle["problem"], result)
    witness = None
    if result["status"] == "SAT":
        witness = lift.verify_literal_witness(inverse, context, bundle, result["assignment"])
        status = ("EXACT_LITERAL_SELECTOR_GRAM_LIFT" if witness["all_original_selector_equalities_pass"]
                  else "EXACT_MOMENT_LIFT_WITH_FAILED_SELECTOR_EQUALITIES")
    elif result["status"] == "UNSAT":
        status = "FIXED_SELECTOR_COUNT_PROJECTION_UNREALIZABLE"
    else:
        assert result["status"] == "UNKNOWN"
        status = "UNKNOWN_LITERAL_LIFT"
    tick(deadline)
    return {"status": status, "bundle": bundle, "CSP_result": result, "CSP_replay": checked,
            "literal_witness": witness, "CSP_search_calls": 1,
            "fixed_native_count_assignment_rejected": result["status"] == "UNSAT",
            "F0_excluded": False, "exterior_Y_edges_realized": False, "graph_completion_claimed": False}


def replay(admission, inverse, context, lift, kernel, saved, deadline):
    bundle = lift.candidate_problem(inverse, admission["projection"],
                                    seconds=min(LIMITS["candidate_relation_seconds"], max(0.001, deadline-time.monotonic())))
    assert bundle == saved["bundle"]
    assert kernel.replay(bundle["problem"], saved["CSP_result"]) == saved["CSP_replay"]
    result = saved["CSP_result"]
    if result["status"] == "SAT":
        witness = lift.verify_literal_witness(inverse, context, bundle, result["assignment"])
        assert witness == saved["literal_witness"]
        expected = ("EXACT_LITERAL_SELECTOR_GRAM_LIFT" if witness["all_original_selector_equalities_pass"]
                    else "EXACT_MOMENT_LIFT_WITH_FAILED_SELECTOR_EQUALITIES")
    else:
        assert saved["literal_witness"] is None
        expected = ("FIXED_SELECTOR_COUNT_PROJECTION_UNREALIZABLE" if result["status"] == "UNSAT"
                    else "UNKNOWN_LITERAL_LIFT")
    assert saved["status"] == expected
    assert saved["fixed_native_count_assignment_rejected"] == (result["status"] == "UNSAT")
    assert saved["F0_excluded"] is saved["exterior_Y_edges_realized"] is saved["graph_completion_claimed"] is False
    tick(deadline)
    return {"status": "PASS: exact fixed-candidate literal-lift replay", "certified_outcome": expected,
            "CSP_search_calls": 0, "new_local_subset_enumerations": 0, "optimizer_calls": 0}
