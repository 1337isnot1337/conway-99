"""Direct F0 literal-selector model with every certified selector cut.

The target has 480 Boolean selectors and the existing 60 exact radix
auxiliaries. It is a necessary first-incidence model, not an exterior graph
completion. This module builds or replays a finite model and never constructs
a solver. Production query preparation remains separate.
"""
import argparse
from collections import Counter
import gc
import gzip
import hashlib
import importlib.util
from itertools import combinations, product
import json
from pathlib import Path
import resource
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
LOGS = ROOT / "experiments/logs/root-prism-free"
OFFSET, SELECTORS, VARIABLES = 31756, 480, 540
RADIX, SAFE, SECONDS = 1 << 30, (1 << 62) - 1, 60
CP_MODEL_SHA = "b5f2a3ae5c418d11af23cb77a766fa10103c8bb71703dafa1ecad74823603f25"
SOURCES = {
    "layer": ("root_prism_free_f0_literal_cut_layer.py", "f9af8c9fcafcc070533cc5ad65c788023e782520dcea4a1a3ac46d3636a0badb"),
    "layer_cold": ("root_prism_free_f0_literal_cut_layer_replay.js", "5ff42605875628362849f73bb5cbcc7e4950bf072a3cb40a27114d386656c883"),
    "domain": ("root_prism_free_f0_exterior_row_domains.py", "1aefd23dfc50b6460e694436a1243942bf4ade5df9b61205adfc8562d51241c7"),
    "motifs": ("root_prism_free_f0_pair_clauses.py", "367b7f850d087067b547653d31bf4b25743f30934583252de1199cffb358daac"),
    "moments": ("root_prism_free_f0_second_moments.py", "29b1c26550ecc858c0cf35b8f527d61bcfba8a4078b14ff6ca90d914d300df18"),
    "supervisor": ("root_prism_free_f0_local_neighbors_batch.py", "b8e5323f92fa105ff2c0ed5b1667ac25d7c92f85f8cac45b170ddc56208f8278"),
}
INPUTS = {
    "layer": ("f0-literal-cut-native-layer01/layer.json.gz", "dcb44159712f9c9a4f61cc61950c23d62b804a0d57709ca43afb33e3711d2b33"),
    "layer_preparation": ("f0-literal-cut-native-layer01/report.json", "7a6786d7e3871eddcb1d635b662f1d1d0fc960c51de1e878007ee62b000d22ba"),
    "layer_cold": ("f0-literal-cut-native-layer01-cold.json", "7bed3fffebe2bf026eac13961bbee1c2ba25ac04913a11b4b3f9f7dc8d6fa44b"),
    "layer_review": ("f0-literal-cut-layer-correction-literature-review.json", "ea962e763e9e131edf05ea7c5e4a2e1848e7ca0fcb933a7b300e70189c4d2a3f"),
    "cuts": ("f0-literal-cut-export-ci01/literal-rows.json.gz", "051282b7c8256fa3cad6edd9e9490290cfdfa5f6bef46b609bc32bdd63189b63"),
    "specification": ("f0-full-fourier-specification-ci01/specification.json.gz", "929703b3a685f95fb28bc6553aef02d5c7f6c879628154c62b8ecfa7d69ba8d5"),
    "specification_preparation": ("f0-full-fourier-specification-ci01/report.json", "cd96e24126c1ffab578d69d319431d023e055a82acbc883f66e72a9bdf54c96b"),
    "specification_cold": ("f0-full-fourier-specification-ci01-cold/report.json", "650813eddce7e0c28def494a16756f49b74e1aa13b667806174c13150647e1a5"),
    "domain": ("f0-exterior-row-domains02.json.gz", "665563b75fa6fc23caa9a002621cc4047809af28543b52b5c2a7ffa592d05dd4"),
    "motifs": ("f0-pair-clauses.json.gz", "47e9d8f518fab10aee604f33df1f22c97b0d201a1af4180e4307553e4857672f"),
    "moments": ("f0-second-moments-preparation02.json.gz", "404d91da35c798ba248887c22a7500957947e24b71d5197dc44432460e6d219e"),
    "moments_cold": ("f0-second-moments-preparation02-cold-replay.json", "e495dbc7281f420caab1f3be88e9263ab8273da6ae88a7ea4e1e72c30eaa1fcd"),
}
RAW_HASHES = {
    "layer": "baa27810f7f95c32a5fb88285186f28c52b3812064bbf5ab09cd8fa52b2912c8",
    "cuts": "3877ba7ec41c4f85f2d1623cfc5d20fa0d258c8c8319fa5dcd7313f580ac305e",
    "specification": "46fa44efdbe3640984a010347a3dfb65964b35752c919f4b6aa2fd24317f1d0b",
}


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


def memory():
    result = {"peak_rss_KiB": int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)}
    path = Path("/proc/self/status")
    if path.exists():
        for line in path.read_text().splitlines():
            if line.startswith("VmRSS:"):
                result["current_rss_KiB"] = int(line.split()[1])
    return result


def read(key):
    name, expected = INPUTS[key]
    payload = (LOGS / name).read_bytes()
    assert sha(payload) == expected, key
    raw = gzip.decompress(payload) if name.endswith(".gz") else payload
    assert len(raw) <= 32 << 20
    if key in RAW_HASHES:
        assert sha(raw) == RAW_HASHES[key], key
    return json.loads(raw)


def definition():
    for name, expected in SOURCES.values():
        assert file_sha(ROOT / "experiments/workspace" / name) == expected, name
    return {
        "schema": "conway99.f0.direct-literal-model-definition.v1",
        "source_sha256": file_sha(Path(__file__)),
        "sources": {k: {"path": "experiments/workspace/" + p, "sha256": h}
                    for k, (p, h) in SOURCES.items()},
        "inputs": {k: {"path": str((LOGS / p).relative_to(ROOT)), "sha256": h}
                   for k, (p, h) in INPUTS.items()},
        "raw_input_hashes": RAW_HASHES,
        "variables": 540, "literal_Booleans": 480, "radix_auxiliaries": 60,
        "linear_constraints": 4681, "native_cut_rows": 4440,
        "original_cuts": 4416, "original_selector_equations": 172,
        "nonempty_selector_equations": 151, "motif_conflicts": 90,
        "certified_zero_pairs_implied": 4410,
        "products": 0, "tables": 0, "external_pool": 0,
        "scope": "Necessary direct first-incidence conditions in the frozen prism-free F0 slice.",
        "all480_literal_selectors_free": True,
        "graph_or_incidence_symmetry_assumed": False,
        "Fourier_count_or_edge_variables_retained": False,
        "literal_cut_layer_inverse_links_retained": False,
        "no_objective_hint_assumption_or_visit_block": True,
        "candidate_requires_direct_original_172_90_4416_integer_checks": True,
        "native_infeasible_status_is_not_a_proof": True,
        "ortools_version": "9.15.6755", "cp_model_source_sha256": CP_MODEL_SHA,
        "maximum_owned_seconds_per_prepare_or_cold": SECONDS,
        "optimizer_calls": 0, "CpSolver_constructed": False,
    }


def decimal(value):
    assert type(value) is str and str(int(value)) == value
    return int(value)


def parsed_row(row, shift=0):
    assert set(row) == {"terms", "domain"}
    terms = [[j - shift, decimal(c)] for j, c in row["terms"]]
    assert all(type(j) is int and c != 0 for j, c in terms)
    assert [j for j, c in terms] == sorted({j for j, c in terms})
    domain = [decimal(v) for v in row["domain"]]
    assert len(domain) == 2 and domain[0] <= domain[1]
    return {"terms": terms, "domain": domain}


def pair_id(a, b):
    assert 0 <= a < b < SELECTORS
    return a * (959 - a) // 2 + b - a - 1


def caps_failures(rows):
    return [[a, b, (rows[a] & rows[b]).bit_count(), 2 - ((rows[a] >> b) & 1)]
            for a in range(len(rows)) for b in range(a)
            if (rows[a] & rows[b]).bit_count() > 2 - ((rows[a] >> b) & 1)]


def induced(rows, sites):
    assert len(sites) == len(set(sites)) and all(0 <= v < len(rows) for v in sites)
    return [sum(((rows[a] >> b) & 1) << j for j, b in enumerate(sites)) for a in sites]


def motif_shape(rows, kind):
    if kind == "P":
        return (len(rows) == 6 and all(r.bit_count() == 3 for r in rows)
                and all((rows[a] >> b) & 1 for part in (range(3), range(3, 6))
                        for a, b in combinations(part, 2))
                and all(sum((rows[a] >> b) & 1 for b in range(3, 6)) == 1 for a in range(3))
                and all(sum((rows[b] >> a) & 1 for a in range(3)) == 1 for b in range(3, 6)))
    assert kind == "F"
    if len(rows) != 10 or [r.bit_count() for r in rows] != [5, 5] + [3] * 8 or not (rows[0] & 2):
        return False
    if any((rows[a] & 3).bit_count() != 1 for a in range(2, 10)):
        return False
    shell = range(2, 10)
    if any(sum((rows[a] >> b) & 1 for b in shell) != 2
           or sum((rows[a] >> b) & 1 for b in shell if (rows[b] & 3) == (rows[a] & 3)) != 1
           for a in shell):
        return False
    reached, pending = {2}, [2]
    while pending:
        a = pending.pop()
        for b in shell:
            if (rows[a] >> b) & 1 and b not in reached:
                reached.add(b)
                pending.append(b)
    return len(reached) == 8


def checked_original_equations(domain, spec):
    core, triples = domain["component_core_rows"], domain["signature_domain"]
    assert len(core) == 21 and all(type(r) is int and 0 <= r < 1 << 21 for r in core)
    assert all(not ((core[a] >> a) & 1) for a in range(21))
    assert all(((core[a] >> b) & 1) == ((core[b] >> a) & 1)
               for a in range(21) for b in range(21))
    assert len(triples) == 480 and len({tuple(t) for t in triples}) == 480
    assert all(t == sorted(set(t)) and len(t) == 3 and 0 <= t[0] <= t[-1] < 18 for t in triples)
    rows = []
    for i in range(18):
        for j in range(i, 18):
            quota = 12 * int(i == j) + 2 - (core[i + 3] & core[j + 3]).bit_count() - ((core[i + 3] >> (j + 3)) & 1)
            support = [a for a, t in enumerate(triples) if i in t and j in t]
            rows.append({"family": "Gram", "core_pair": [i, j], "support": support, "quota": quota})
    rows.append({"family": "population", "support": list(range(480)), "quota": 60})
    expansions = spec["original_equality_expansions"]
    assert [r["original_row_id"] for r in expansions] == list(range(172))
    assert rows == [r["original_row"] for r in expansions]
    nonempty = [i for i, r in enumerate(rows) if r["support"]]
    assert nonempty == spec["nonempty_original_equality_ids"] and len(nonempty) == 151
    assert all(r["quota"] == 0 for r in rows if not r["support"])
    assert all(expansions[i]["literal_zero_tautology"] == (not r["support"]) for i, r in enumerate(rows))
    return rows, nonempty


def checked_motifs(domain, all_motifs):
    assert all_motifs["source_sha256"] == SOURCES["motifs"][1]
    record = all_motifs["representatives"][0]
    assert record["representative"] == 0
    core, triples, proofs = domain["component_core_rows"], domain["signature_domain"], []
    for key, kind, expected in (("F_conflicts", "F", 78), ("prism_conflicts", "P", 12)):
        assert len(record[key]) == expected
        for index, item in enumerate(record[key]):
            a, b = item["ordered_columns"]
            assert 0 <= a < 480 and 0 <= b < 480 and a != b
            assert item["columns"] == sorted((a, b))
            rows = list(core) + [0, 0]
            for v, column in ((21, a), (22, b)):
                for i in triples[column]:
                    rows[v] |= 1 << (i + 3)
                    rows[i + 3] |= 1 << v
            assert not caps_failures(rows)
            motif = induced(rows, item["motif_sites"])
            assert motif == item["induced_motif_rows"] and motif_shape(motif, kind)
            rows[21] |= 1 << 22
            rows[22] |= 1 << 21
            bad = caps_failures(rows)
            assert bad
            proofs.append({"pair": item["columns"], "kind": kind, "family_index": index,
                           "motif_sites": item["motif_sites"], "edge_present_cap_failure": bad[0]})
    pairs = sorted(p["pair"] for p in proofs)
    assert len(pairs) == len({tuple(p) for p in pairs}) == 90
    assert pairs == domain["motif_pairs"]
    return pairs, sorted(proofs, key=lambda p: p["pair"])


def checked_zero_implications(rows, motif_pairs, moments, cold):
    assert cold["status"].startswith("PASS")
    assert cold["artifact_sha256"] == INPUTS["moments"][1]
    assert moments["source_sha256"] == cold["source_sha256"] == SOURCES["moments"][1]
    assert moments["original_selector_equalities"] == rows
    implied = {}
    for row_id, row in enumerate(rows):
        if row["quota"] == 1:
            for a, b in combinations(row["support"], 2):
                p = pair_id(a, b)
                assert p not in implied
                implied[p] = {"pair_id": p, "pair": [a, b], "premise": "quota-one Gram equality",
                              "original_row_id": row_id}
    assert len(implied) == 4320
    for motif_id, (a, b) in enumerate(motif_pairs):
        p = pair_id(a, b)
        assert p not in implied
        implied[p] = {"pair_id": p, "pair": [a, b], "premise": "explicit motif conflict",
                      "motif_id": motif_id}
    saved = moments["zero_moment_certificates"]
    assert len(saved) == len(implied) == 4410
    assert len({z["pair_id"] for z in saved}) == 4410
    assert {p for oi in moments["zero_pair_orbits"] for p in moments["pair_orbits"][oi]} == set(implied)
    assert len(moments["zero_pair_orbits"]) == 389
    for z in saved:
        p = z["pair_id"]
        a, b = sorted((z["anchor"], z["other"]))
        assert p == pair_id(a, b) and implied[p]["pair"] == [a, b]
        if z["kind"] == "quota-one nonnegative lifted equality":
            assert implied[p]["premise"] == "quota-one Gram equality"
            assert implied[p]["original_row_id"] == z["selector_Gram_row"]
        else:
            assert z["kind"] == "certified binary motif times selector"
            assert implied[p]["premise"] == "explicit motif conflict"
    return [implied[p] for p in sorted(implied)]


def checked_cut_remap(layer, originals, prep, cold):
    assert layer["schema"] == "conway99.f0.literal-cut-native-layer.v1"
    assert layer["base_native_variables"] == layer["binary_offset"] == OFFSET
    assert layer["binary_count"] == SELECTORS and layer["next_variable"] == OFFSET + VARIABLES
    assert prep["status"].startswith("PASS") and cold["status"].startswith("PASS")
    assert prep["definition"]["source_sha256"] == cold["producer_sha256"] == SOURCES["layer"][1]
    assert cold["source_sha256"] == SOURCES["layer_cold"][1]
    assert cold["preparation_sha256"] == INPUTS["layer_preparation"][1]
    assert cold["layer_sha256"] == prep["layer"]["sha256"] == INPUTS["layer"][1]
    assert cold["layer_raw_sha256"] == prep["layer"]["raw_sha256"] == RAW_HASHES["layer"]
    assert cold["literal_archive_sha256"] == INPUTS["cuts"][1]
    assert cold["literal_archive_raw_sha256"] == RAW_HASHES["cuts"]
    assert len(layer["variables"]) == 540 and len(layer["linear_constraints"]) == 4920
    assert [v["id"] for v in layer["variables"]] == list(range(OFFSET, OFFSET + VARIABLES))
    variables = []
    for index, old in enumerate(layer["variables"]):
        item = dict(old, id=index, domain=[decimal(v) for v in old["domain"]])
        assert len(item["domain"]) == 2 and item["domain"][0] <= item["domain"][1]
        if index < 480:
            assert item["kind"] == "literal" and item["selector"] == index and item["domain"] == [0, 1]
        variables.append(item)
    rows = [parsed_row(r, OFFSET) for r in layer["linear_constraints"][480:]]
    assert all(0 <= j < VARIABLES for row in rows for j, c in row["terms"])
    assert [{"terms": [[j + OFFSET, str(c)] for j, c in r["terms"]],
             "domain": list(map(str, r["domain"]))} for r in rows] == layer["linear_constraints"][480:]
    restored_variables = [dict(v, id=v["id"] + OFFSET, domain=list(map(str, v["domain"]))) for v in variables]
    assert restored_variables == layer["variables"]
    assert len(originals) == 4416 and sum(len(r["terms"]) for r in originals) == 442308
    records, next_row, next_auxiliary = [], 0, 480
    assert len(layer["cut_records"]) == 4416
    for cut_id, (original, old) in enumerate(zip(originals, layer["cut_records"])):
        assert set(original) == {"terms", "rhs"} and decimal(original["rhs"]) == 0
        terms = [[j, decimal(c)] for j, c in original["terms"]]
        assert all(type(j) is int and 0 <= j < 480 and c != 0 for j, c in terms)
        assert [j for j, c in terms] == sorted({j for j, c in terms})
        assert old["original_row_id"] == cut_id and old["original_row_sha256"] == sha(canonical(original))
        shifted = {"terms": [[j + OFFSET, c] for j, c in original["terms"]], "rhs": original["rhs"]}
        assert old["shifted_row_sha256"] == sha(canonical(shifted))
        start, width = old["linear_offset"] - 480, old["linear_count"]
        assert start == next_row and old["first_auxiliary"] - OFFSET == next_auxiliary
        if old["route"] == "direct":
            assert cut_id not in range(4164, 4176)
            assert width == 1 and old["auxiliary_count"] == old["radix_digits"] == 0
            assert rows[start] == {"terms": terms, "domain": [sum(min(0, c) for j, c in terms), 0]}
        else:
            assert old["route"] == "radix" and 4164 <= cut_id < 4176
            assert width == old["radix_digits"] == 3 and old["auxiliary_count"] == 5
            bound = len(terms) + 2
            for limb in range(3):
                assert variables[next_auxiliary + limb] == {
                    "id": next_auxiliary + limb, "kind": "slack", "row": cut_id,
                    "limb": limb, "domain": [0, RADIX - 1]}
            for limb in range(1, 3):
                assert variables[next_auxiliary + 2 + limb] == {
                    "id": next_auxiliary + 2 + limb, "kind": "carry", "row": cut_id,
                    "limb": limb, "domain": [-bound, bound]}
            contracted = Counter()
            for limb in range(3):
                expected = [[j, (-1 if c < 0 else 1) * ((abs(c) // (RADIX ** limb)) % RADIX)]
                            for j, c in terms]
                expected = [t for t in expected if t[1]]
                expected.append([next_auxiliary + limb, 1])
                if limb:
                    expected.append([next_auxiliary + 2 + limb, 1])
                if limb < 2:
                    expected.append([next_auxiliary + 3 + limb, -RADIX])
                expected.sort()
                assert rows[start + limb] == {"terms": expected, "domain": [0, 0]}
                for j, c in expected:
                    contracted[j] += c * RADIX ** limb
            expected = dict(terms)
            expected.update({next_auxiliary + limb: RADIX ** limb for limb in range(3)})
            assert {j: c for j, c in contracted.items() if c} == expected
            assert max([sum(-c for j, c in terms if c < 0)] + [abs(c) for j, c in terms]) < RADIX ** 3
            next_auxiliary += 5
        records.append(dict(old, linear_offset=start, first_auxiliary=old["first_auxiliary"] - OFFSET))
        next_row += width
    assert next_row == 4440 and next_auxiliary == 540
    return variables, rows, records


def derive(stage):
    bound = definition()
    domain = read("domain")
    assert domain["source_sha256"] == SOURCES["domain"][1]
    spec = read("specification")
    spec_preparation, spec_cold = read("specification_preparation"), read("specification_cold")
    assert spec_preparation["status"].startswith("PASS") and spec_cold["status"].startswith("PASS")
    assert spec_cold["preparation_sha256"] == INPUTS["specification_preparation"][1]
    assert spec_cold["specification_sha256"] == INPUTS["specification"][1]
    originals, nonempty = checked_original_equations(domain, spec)
    del spec
    motifs, motif_proofs = checked_motifs(domain, read("motifs"))
    moments = read("moments")
    zeros = checked_zero_implications(originals, motifs, moments, read("moments_cold"))
    del moments
    stage("all172_original_rows_90_motifs_and4410_zero_implications_checked")
    layer, cuts = read("layer"), read("cuts")
    read("layer_review")
    variables, rows, cut_records = checked_cut_remap(layer, cuts, read("layer_preparation"), read("layer_cold"))
    inverse_hash = sha(canonical(layer["linear_constraints"][:480]))
    del layer, cuts
    stage("all4416_cut_rows_remapped_and_full_retained_layer_restored")
    gram_map = [None] * 172
    for original_id in nonempty:
        row = originals[original_id]
        gram_map[original_id] = len(rows)
        rows.append({"terms": [[j, 1] for j in row["support"]], "domain": [row["quota"], row["quota"]]})
    motif_map = []
    for a, b in motifs:
        motif_map.append(len(rows))
        rows.append({"terms": [[a, 1], [b, 1]], "domain": [0, 1]})
    assert len(rows) == 4681
    maximum_activity, terms_count = 0, 0
    for row in rows:
        absolute = sum(abs(c) * max(abs(variables[j]["domain"][0]), abs(variables[j]["domain"][1]))
                       for j, c in row["terms"])
        assert absolute + max(map(abs, row["domain"])) <= SAFE
        assert all(-(1 << 63) <= v < 1 << 63 for _, v in row["terms"])
        assert all(-(1 << 63) <= v < 1 << 63 for v in row["domain"])
        maximum_activity = max(maximum_activity, absolute)
        terms_count += len(row["terms"])
    plan = {
        "schema": "conway99.f0.direct-literal-model.v1", "definition": bound,
        "variables": variables, "linear_constraints": rows,
        "original_selector_equalities": originals, "original_to_native_rows": gram_map,
        "motif_pairs": motifs, "motif_to_native_rows": motif_map, "motif_proofs": motif_proofs,
        "zero_pair_implications": zeros, "cut_records": cut_records,
        "core_rows": domain["component_core_rows"], "signature_domain": domain["signature_domain"],
        "literal_cut_input": bound["inputs"]["cuts"],
        "literal_layer_variable_shift": -OFFSET, "discarded_inverse_links": 480,
        "discarded_inverse_prefix_sha256": inverse_hash,
        "retained_literal_layer_variables_and_rows_restored_exactly": True,
        "counts": {"variables": 540, "literal_Booleans": 480, "radix_auxiliaries": 60,
                   "linear_constraints": 4681, "linear_terms": terms_count,
                   "original_cuts": 4416, "direct_cut_rows": 4404, "radix_rows": 36,
                   "original_equations": 172, "nonempty_equations": 151, "literal_zero_equations": 21,
                   "motifs": 90, "zero_pair_implications": 4410, "explicit_extra_zero_rows": 0,
                   "products": 0, "tables": 0, "external_pool": 0},
        "maximum_linear_absolute_box_activity": maximum_activity,
        "numerical_coefficients_rounded_or_scaled": False,
        "optimizer_calls": 0, "CpSolver_constructed": False,
    }
    stage("direct540_mathematical_plan_complete")
    return plan


def inspect(values, plan, cuts):
    assert type(values) is list and len(values) == 540 and all(type(v) is int for v in values)
    for value, variable in zip(values, plan["variables"]):
        assert variable["domain"][0] <= value <= variable["domain"][1]
    bits = values[:480]
    assert all(v in (0, 1) for v in bits)
    for row in plan["linear_constraints"]:
        total = sum(c * values[j] for j, c in row["terms"])
        assert row["domain"][0] <= total <= row["domain"][1]
    assert len(plan["original_selector_equalities"]) == 172
    for row in plan["original_selector_equalities"]:
        assert sum(bits[j] for j in row["support"]) == row["quota"]
    assert len(plan["motif_pairs"]) == 90
    for a, b in plan["motif_pairs"]:
        assert bits[a] + bits[b] <= 1
    assert len(cuts) == 4416
    for row in cuts:
        assert sum(decimal(c) * bits[j] for j, c in row["terms"]) <= decimal(row["rhs"])
    for witness in plan["zero_pair_implications"]:
        a, b = witness["pair"]
        assert bits[a] * bits[b] == 0
    selected = [a for a, value in enumerate(bits) if value]
    assert len(selected) == 60
    profiles = Counter(tuple(sum(v // 6 == f for v in plan["signature_domain"][a]) for f in range(3))
                       for a in selected)
    assert profiles[(1, 1, 1)] == 24 and sum(n for p, n in profiles.items() if p != (1, 1, 1)) == 36
    for f in range(3):
        assert [sum(n for p, n in profiles.items() if p[f] == k) for k in range(3)] == [12, 36, 12]
    return {
        "status": "PASS: exact direct literal-model witness; exterior graph not checked",
        "values_sha256": sha(canonical(values)), "selected": selected,
        "checked_native_rows": 4681, "checked_original_equations": 172,
        "checked_motif_conflicts": 90, "checked_original_big_integer_cuts": 4416,
        "checked_zero_pair_consequences": 4410, "profile24_36_and_fiber12_36_12": True,
        "graph_existence_claimed": False, "core_matching_checked": False,
    }


def controls():
    count = 0
    original = {"terms": [[31756, "-7"], [31757, "3"], [31758, "11"]], "domain": ["-7", "9"]}
    shifted = parsed_row(original, OFFSET)
    for values in product((0, 1), repeat=3):
        a = sum(decimal(c) * values[j - OFFSET] for j, c in original["terms"])
        b = sum(c * values[j] for j, c in shifted["terms"])
        assert a == b and (-7 <= a <= 9) == (shifted["domain"][0] <= b <= shifted["domain"][1])
        count += 1
    for values in product((0, 1), repeat=5):
        if sum(values) == 1:
            assert all(values[a] * values[b] == 0 for a, b in combinations(range(5), 2))
        count += 1
    for bad in (True, 1, "01", "-0", "1.0", "1e3", "+1"):
        try:
            decimal(bad)
        except (AssertionError, ValueError):
            pass
        else:
            raise AssertionError("noncanonical decimal accepted")
    return {"status": "PASS", "exact_remap_and_quota_controls": count,
            "rejected_noncanonical_decimal_controls": 7, "solver_calls": 0}


def proto_from_plan(pb2, plan):
    proto = pb2.CpModelProto()
    for j, variable in enumerate(plan["variables"]):
        assert variable["id"] == j
        proto.variables.add(name=("f0_literal_" if j < 480 else "f0_radix_") + str(j),
                            domain=variable["domain"])
    for row in plan["linear_constraints"]:
        native = proto.constraints.add().linear
        native.vars.extend(j for j, c in row["terms"])
        native.coeffs.extend(c for j, c in row["terms"])
        native.domain.extend(row["domain"])
    assert {f.name for f, _ in proto.ListFields()} == {"variables", "constraints"}
    assert len(proto.variables) == 540 and len(proto.constraints) == 4681
    assert all(c.WhichOneof("constraint") == "linear" and not c.enforcement_literal for c in proto.constraints)
    return proto


def archive(path, raw):
    assert len(raw) <= 32 << 20
    payload = gzip.compress(raw, mtime=0)
    with path.open("xb") as stream:
        stream.write(payload)
    return {"path": str(path.relative_to(ROOT)), "sha256": sha(payload),
            "raw_sha256": sha(raw), "bytes": len(payload), "raw_bytes": len(raw)}


def worker(mode, directory, deadline, saved_directory=None):
    started, stages = time.monotonic(), []
    def stage(label):
        stages.append({"stage": label, "elapsed_seconds": time.monotonic() - started, "memory": memory()})
        save(directory / "stages.json", {"stages": stages, "optimizer_calls": 0})
        if time.monotonic() > deadline:
            raise TimeoutError("direct literal model owned deadline")
    try:
        stage("started")
        checks = controls()
        plan = derive(stage)
        stage("before_native_import")
        import ortools
        from ortools.sat import cp_model_pb2
        from ortools.sat.python import cp_model
        assert ortools.__version__ == "9.15.6755"
        assert file_sha(Path(cp_model.__file__)) == CP_MODEL_SHA
        stage("native_import_complete")
        proto = proto_from_plan(cp_model_pb2, plan)
        raw = proto.SerializeToString()
        stage("exact_protobuf_complete")
        if mode == "prepare":
            outputs = {"plan": archive(directory / "plan.json.gz", canonical(plan)),
                       "model": archive(directory / "model.pb.gz", raw)}
            model = cp_model.CpModel()
            variables = [model.new_int_var_from_domain(cp_model.Domain.from_flat_intervals(list(v.domain)), v.name)
                         for v in proto.variables]
            assert [v.index for v in variables] == list(range(540))
            for constraint in proto.constraints:
                row = constraint.linear
                expr = cp_model.LinearExpr.weighted_sum([variables[j] for j in row.vars], list(row.coeffs))
                model.add_linear_expression_in_domain(expr, cp_model.Domain.from_flat_intervals(list(row.domain)))
            assert model.validate() == ""
            export = directory / "native-model.pb"
            assert model.export_to_file(str(export)) and file_sha(export) == sha(raw)
            stage("native_validation_and_complete_export_byte_identity_passed")
            report = {"status": "PASS: direct540 exact model and native validation; no solve",
                      "definition": plan["definition"], "controls": checks, "outputs": outputs,
                      "counts": plan["counts"], "maximum_linear_absolute_box_activity":
                      plan["maximum_linear_absolute_box_activity"],
                      "native_public_constructor_byte_identity": True,
                      "all4416_original_cut_records_and_zero_implications_checked": True,
                      "optimizer_calls": 0, "CpSolver_constructed": False}
        else:
            assert mode == "cold" and saved_directory is not None
            old_raw = (saved_directory / "report.json").read_bytes()
            old = json.loads(old_raw)
            assert old["status"].startswith("PASS") and old["definition"] == plan["definition"]
            assert old["controls"] == checks and old["counts"] == plan["counts"]
            for key, actual in (("plan", canonical(plan)), ("model", raw)):
                entry = old["outputs"][key]
                payload = (ROOT / entry["path"]).read_bytes()
                assert sha(payload) == entry["sha256"]
                assert gzip.decompress(payload) == actual
                assert sha(actual) == entry["raw_sha256"] and len(actual) == entry["raw_bytes"]
            stage("complete_saved_model_and_every_literal_obligation_cold_checked")
            report = {"status": "PASS: direct540 mathematical and protobuf cold replay",
                      "definition": plan["definition"], "controls": checks,
                      "preparation_sha256": sha(old_raw), "counts": plan["counts"],
                      "complete_plan_and_protobuf_byte_equality": True,
                      "native_model_construction_or_validation_repeated": False,
                      "optimizer_calls": 0, "CpSolver_constructed": False}
        report.update(seconds=time.monotonic() - started, terminal_memory=memory(),
                      stages_sha256=file_sha(directory / "stages.json"))
        save(directory / "report.json", report)
    except Exception as error:
        save(directory / "error.json", {"error_type": type(error).__name__, "message": str(error),
                                       "memory": memory(), "optimizer_calls": 0})
        raise


def owned(mode, directory, saved_directory=None):
    started = time.monotonic()
    deadline = started + SECONDS
    name, expected = SOURCES["supervisor"]
    path = ROOT / "experiments/workspace" / name
    assert file_sha(path) == expected
    spec = importlib.util.spec_from_file_location("frozen_direct_literal_supervisor", path)
    supervisor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(supervisor)
    directory.mkdir(parents=True, exist_ok=False)
    command = [sys.executable, str(Path(__file__).resolve()), "_" + mode,
               "--directory", str(directory.resolve()), "--deadline", str(deadline)]
    if saved_directory is not None:
        command.extend(("--saved-directory", str(saved_directory.resolve())))
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
    parser.add_argument("--saved-directory", type=Path)
    parser.add_argument("--deadline", type=float)
    args = parser.parse_args()
    if args.mode.startswith("_"):
        assert args.deadline is not None
        worker(args.mode[1:], args.directory, args.deadline, args.saved_directory)
    else:
        owned(args.mode, args.directory, args.saved_directory)
