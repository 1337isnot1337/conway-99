"""Exact cut registry and frozen contexts for a strict-growth direct540 master."""
from collections import defaultdict
import hashlib
import importlib.util
import json
from math import gcd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORK = "experiments/workspace/"
SOURCES = {
    "base": (WORK + "root_prism_free_f0_direct_literal_query.py", "d53a51dadb01e267baaca8cfcc51a2aab8ff654b74bae605a482d8d110853db6"),
    "shared_context": (WORK + "root_prism_free_f0_direct_incidence_shared_separation.py", "6c8703ed6dff75ad451cdb752bda61c84acfd0c51ca6779a9c38b7e0c0816132"),
    "matching": (WORK + "root_prism_free_f0_core_matching_candidate_oracle.py", "01adf67152884f59cf65c3b490de5b4f69c9d9bdec7a53ba8863991bfc9d0c60"),
    "cover": (WORK + "root_prism_free_f0_retained_local_cover.py", "922ad60fed6ae46f8a3bab51ea419a56fe3703177111e48104e6a2b3e426974a"),
    "supervisor": (WORK + "root_prism_free_f0_fixed_selection_exterior_query.py", "bbe476e5a7a13800c08265d4db541b7e8c7edf2277be03f6d06db134926891e3"),
}
MAX_EXTRA_ROWS, MAX_ACTIVITY = 256, 1 << 60


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def value_sha(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def save(path, value):
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_bytes(canonical(value) + b"\n")
    tmp.replace(path)


def source(key):
    name, expected = SOURCES[key]
    path = ROOT / name
    assert digest(path) == expected
    spec = importlib.util.spec_from_file_location("direct_master_" + key, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read(config, key):
    item = config["inputs"][key]
    raw = (ROOT / item["path"]).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == item["sha256"], key
    return json.loads(raw)


def normalized(terms, rhs):
    assert type(rhs) is int
    values = defaultdict(int)
    for j, c in terms:
        assert type(j) is int and 0 <= j < 480 and type(c) is int
        values[j] += c
    pairs = [[j, c] for j, c in sorted(values.items()) if c]
    assert pairs, "a constant cut needs a separate exact termination certificate"
    divisor = 0
    for _, c in pairs:
        divisor = gcd(divisor, abs(c))
    row = {"terms": [[j, c // divisor] for j, c in pairs], "rhs": rhs // divisor}
    return row


def encode_domain(row):
    lower = sum(c for _, c in row["terms"] if c < 0)
    absolute = sum(abs(c) for _, c in row["terms"])
    if absolute >= MAX_ACTIVITY or abs(row["rhs"]) >= MAX_ACTIVITY or lower > row["rhs"]:
        raise OverflowError("exact cut outside declared finite int64 encoding; preserve it and stop")
    return [lower, row["rhs"]]


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


def inspect_extra(values, registry):
    assert len(values) == 540 and all(type(x) is int for x in values)
    assert all(x in (0, 1) for x in values[:480])
    violations = []
    for entry in registry:
        row = entry["row"]
        gap = sum(c * values[j] for j, c in row["terms"]) - row["rhs"]
        if gap > 0:
            violations.append({"key": entry["key"], "gap": gap})
    assert not violations, violations
    return {"extra_rows_checked": len(registry), "registry_sha256": value_sha(registry)}


def append_expected(proto, additions):
    for entry in additions:
        row = entry["row"]
        native = proto.constraints.add().linear
        native.vars.extend(j for j, _ in row["terms"])
        native.coeffs.extend(c for _, c in row["terms"])
        native.domain.extend(encode_domain(row))


def append_native(cp_model, model, additions):
    for entry in additions:
        row = entry["row"]
        variables = [model.get_int_var_from_proto_index(j) for j, _ in row["terms"]]
        expr = cp_model.LinearExpr.weighted_sum(variables, [c for _, c in row["terms"]])
        model.add_linear_expression_in_domain(expr, cp_model.Domain.from_flat_intervals(encode_domain(row)))
    assert model.validate() == ""


def shared_rows(cuts, origin):
    assert cuts["complete_global_edges"] == 68394 and cuts["saved_selection_is_not_a_cut_hypothesis"]
    assert len(cuts["transported_cuts"]) == 12
    return [({"terms": row["signed_coefficients"], "rhs": 0},
             dict(origin, core_action_index=row["core_action_index"])) for row in cuts["transported_cuts"]]


def matching_rows(report, origin):
    assert report["status"] in ("ALL18_LOCAL_MATCHINGS_EXIST", "REFUTED_LITERAL_SELECTION_BY_CORE_MATCHING")
    return [({"terms": row["terms"], "rhs": row["upper"]}, dict(origin, local_cut_index=i))
            for i, row in enumerate(report["new_matching_cuts"])]


def context(config_path, stage):
    config = json.loads(config_path.read_bytes())
    assert config["schema"] == "conway99.f0.direct-master-seeds.v1"
    loaded = {key: read(config, key) for key in config["inputs"]}
    base, shared_root, matching, cover_source = [source(k) for k in ("base", "shared_context", "matching", "cover")]
    shared_definition, separator, selection, triples, targets, neighbors, actions = shared_root.context()
    match_ctx = matching.context()
    assert match_ctx["triples"] == triples
    assert loaded["matching_preparation"]["definition"] == matching.definition()
    assert loaded["matching_preparation"]["matching_sets_sha256"] == value_sha(match_ctx["sets"])
    assert loaded["matching_preparation"]["live_eligible_edges_sha256"] == value_sha(sorted(match_ctx["allowed"]))
    run, owner, cold, cold_owner = [loaded[k] for k in ("shared_run", "shared_owner", "shared_cold", "shared_cold_owner")]
    assert owner["report_accepted"] and owner["report_sha256"] == config["inputs"]["shared_run"]["sha256"]
    assert cold_owner["report_accepted"] and cold_owner["certified_new_cuts"]
    assert cold_owner["report_sha256"] == config["inputs"]["shared_cold"]["sha256"]
    assert cold["status"] == "PASS_COLD_EXACT_SHARED_GAP_AND_ALL12_UNIVERSAL_CUTS"
    assert cold["run_report_sha256"] == config["inputs"]["shared_run"]["sha256"]
    assert run["cuts_sha256"] == cold["cuts_sha256"] == config["inputs"]["shared_cuts"]["sha256"]
    assert run["result_sha256"] == config["inputs"]["shared_result"]["sha256"]
    shared_result = loaded["shared_result"]
    separator.replay(shared_result, selection, triples, targets, neighbors)
    assert shared_result["exact_fixed_design_infeasibility"] and shared_result["cooperative_budget_overrun_seconds"] == 0
    vectors = shared_result["fixed_capacity_potentials"]["integer_potentials60_by18"]
    assert separator.lift(selection, vectors, triples, targets, neighbors, actions) == loaded["shared_cuts"]
    seed_rows = shared_rows(loaded["shared_cuts"], {"kind": "seed_shared", "certificate_sha256": config["inputs"]["shared_cuts"]["sha256"]})
    block, block_owner, block_cold = [loaded[k] for k in ("positive_cut", "positive_owner", "positive_cold")]
    assert block["accepted_cold_owner_sha256"] == config["inputs"]["positive_owner"]["sha256"]
    assert block_owner["report_accepted"] and block_owner["fixed_selection_excluded"]
    assert block_owner["report_sha256"] == block["cold_report_sha256"] == config["inputs"]["positive_cold"]["sha256"]
    assert block_cold["status"] == "PASS_COLD_REBUILD_RETAINED_INPUTS_AND_DRAT"
    assert block["population_premise"] == 60 and block["cut"] == {"terms": [[a, 1] for a in selection], "rhs": 59}
    seed_rows.append((block["cut"], {"kind": "seed_certified_exterior", "certificate_sha256": config["inputs"]["positive_cut"]["sha256"]}))
    rebuilt_cover = cover_source.derive()
    saved_cover = loaded["local_cover"]
    assert {k: v for k, v in rebuilt_cover.items() if k != "seconds"} == {k: v for k, v in saved_cover.items() if k != "seconds"}
    assert saved_cover["saved_selection_violation"] == 1
    for i, action in enumerate(actions):
        image = action["signature_image"]
        row = normalized([[image[a], c] for a, c in saved_cover["cut"]["terms"]], saved_cover["cut"]["rhs"])
        transported = {image[a] for a in selection}
        assert sum(c for a, c in row["terms"] if a in transported) - row["rhs"] == 1
        seed_rows.append((row, {"kind": "seed_transported_local_cover", "core_action_index": i,
                               "certificate_sha256": config["inputs"]["local_cover"]["sha256"],
                               "source_review_sha256": config["inputs"]["local_cover_review"]["sha256"]}))
    registry, _ = add_rows([], seed_rows)
    assert len(registry) == 25
    stage("all_seed_certificates_and12_actual_transports_replayed")
    return {"config": config, "config_sha256": digest(config_path), "base": base, "separator": separator,
            "shared_definition": shared_definition, "matching": matching, "matching_context": match_ctx,
            "triples": triples, "targets": targets, "neighbors": neighbors, "actions": actions,
            "registry": registry, "seed_selection": selection}


def controls():
    a = normalized([[2, 6], [1, -4], [2, 2]], 7)
    assert a == {"terms": [[1, -1], [2, 2]], "rhs": 1}
    assert normalized([[2, 8], [1, -4]], 4) == a
    assert normalized([[1, -4], [2, 8]], 3)["rhs"] == 0
    registry, additions = add_rows([], [(a, {}), (a, {})])
    assert len(registry) == len(additions) == 1
    old = canonical(registry)
    try:
        add_rows(registry, [({"terms": [[0, 1], [1, 1 << 63]], "rhs": 0}, {})])
    except OverflowError:
        pass
    else:
        raise AssertionError("unsafe activity accepted")
    assert canonical(registry) == old
    return {"status": "PASS_NORMALIZATION_RHS_DEDUP_AND_ATOMIC_RANGE_REFUSAL", "solver_calls": 0}
