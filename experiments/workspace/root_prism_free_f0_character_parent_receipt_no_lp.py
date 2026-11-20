"""Separate exact restored-parent arithmetic receipt for an explicit vector.

No native model or mathematical builder is imported or reconstructed.
Archived target/parent protos and the exact original row matrices are checked
sequentially with Python integers. Only the timely owner can issue the final
EXACT_COUNT_WITNESS receipt. Preparation performs no production point check.
"""
import argparse
import ast
from collections import Counter
import gc
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import resource
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
LOGS = ROOT / "experiments/logs/root-prism-free"
OWNER = ("root_prism_free_f0_local_neighbors_batch.py", "b8e5323f92fa105ff2c0ed5b1667ac25d7c92f85f8cac45b170ddc56208f8278")
EVALUATOR = ("root_prism_free_f0_character_cpsat.py", "879cdb9be48f9377dd6bccd078f26a568d12467385e9ecb1d5b260cc56ff64e7")
INPUTS = {
    "query_preparation": ("f0-character-packing-no-lp-query-preparation01/preparation.json", "123c940a34b590c944316a2fd606e5febcf1cedbdea3ec0f828d41b115068f37"),
    "model_preparation": ("f0-character-y-domain-overlay01/report.json", "a4a543b35bdd22357eef39524ff8015e0d4d274547c046205c806a5f52e92061"),
    "model_cold": ("f0-character-y-domain-overlay01-cold/report.json", "851a2a4a292a891de7b38eb08212fd1a604cf72cc09dbef3af97768ebe8e21be"),
    "plan": ("f0-character-y-domain-overlay01/plan.json.gz", "4d3a13718cdac9fcf68b119a1cd1ba009edeb21c7257d4498d5ebdf18954acc4"),
    "target": ("f0-character-y-domain-overlay01/target.pb.gz", "41ff251304c8d3961ebae059581f8416f7f0a45c7cc2246be547296e7db407f0"),
    "original_native": ("f0-character-cpsat01/model.pb.gz", "81acda719e5d7a65ccfeb95bcd956785ee9283d60630aed2f8933599933f3f57"),
    "original_preparation": ("f0-character-cpsat01/report.json", "e15c4bfcf7adaabb60258e3cffa8046eb0cd97843ae8787a24b356011d7b8a5f"),
    "original_cold": ("f0-character-cpsat01-cold/report.json", "fd86705f404e899869234d67916c2178d77acfb9c2b847571fb897cc5f785e18"),
    "domains": ("f0-orbit-populations02-domains.json.gz", "4f079468530dba0746512cc4afce01666b2a63a2c8f35f66a4660a4fe3bab8ab"),
    "counts": ("f0-orbit-populations02-model.json.gz", "aa46e2ca9df7a5838926385e06a86acda041c8455ac3422ae1e7b0a5c4ce5437"),
    "count_cold": ("f0-orbit-populations02-independent-replay.json", "a8bb55cbf773ea75a8cd1d5a18b50281ecbe08f6074cea04fb2d75799138273a"),
    "full_parent": ("f0-joint-psd-clique-model01.json.gz", "43fff7283308cc2ed1be0936fae4b4f7b264c5961f6e6a4c9a81d123836e4f69"),
    "refinements": ("f0-selector-integer-refinements01.json.gz", "68d5ea0ca4a9906e74319770924eb91f880e46cec0c3ed2ab269bb1debe7b339"),
    "refinement_cold": ("f0-selector-integer-refinements-independent-audit.json", "8a45a87eccb55fa4e5362e967ce925f38bfde25a943bb12a1a804cb4fa573cbc"),
}
TARGET_SHA = "a738d318b6b8de471ee7383f1e6ea11949eed8f8ccf4892814fa2eac268ed153"
ORIGINAL_SHA = "5b43e3c026dbe71fcc8d072aa1790b80f7a81312e7b1ebf36a37612b2f726eeb"
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


def read(key):
    name, expected = INPUTS[key]
    raw = (LOGS / name).read_bytes()
    assert sha(raw) == expected
    return json.loads(gzip.decompress(raw) if name.endswith(".gz") else raw)


def memory():
    value = {"peak_rss_KiB": int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)}
    for line in Path("/proc/self/status").read_text().splitlines():
        if line.startswith(("VmRSS:", "VmHWM:")):
            value[line.split(":")[0] + "_KiB"] = int(line.split()[1])
    return value


def definition():
    for name, expected in (OWNER, EVALUATOR):
        assert file_sha(ROOT / "experiments/workspace" / name) == expected
    for name, expected in INPUTS.values():
        assert file_sha(LOGS / name) == expected
    return {"schema": "conway99.f0-restored-parent-receipt.v1", "source_sha256": file_sha(Path(__file__)),
            "inputs": {k: {"path": str((LOGS / p).relative_to(ROOT)), "sha256": h} for k, (p, h) in INPUTS.items()},
            "target_proto_sha256": TARGET_SHA, "original_native_proto_sha256": ORIGINAL_SHA,
            "variables": 18444, "primitive_count_variables": 15038, "restored_parent_variables": 15200,
            "count_rows": 27719, "restored_parent_rows": 28043, "integer_refinements": 25,
            "deterministic_population_identities": 903,
            "original_native_constraints": 34436, "final_native_constraints": 34398,
            "maximum_owned_seconds": SECONDS,
            "subject_model_builders_imported_or_called": False,
            "large_product_specification_loaded": False,
            "all_arithmetic_Python_integers": True, "optimizer_calls": 0,
            "only_timely_owner_may_write_an_accepted_receipt": True,
            "count_witness_does_not_certify_literal_incidence_graph_or_full_PSD": True}


def rows_check(matrix, values, multiplier=1):
    assert type(multiplier) is int and multiplier > 0
    counts = {}
    for kind in ("equalities", "inequalities"):
        for row in matrix[kind]:
            terms = row["terms"]
            assert all(type(j) is int and 0 <= j < len(values) and type(c) is int for j, c in terms)
            assert type(row["rhs"]) is int
            value = sum(c * values[j] for j, c in terms)
            rhs = multiplier * row["rhs"]
            assert value == rhs if kind == "equalities" else value <= rhs
        counts[kind] = len(matrix[kind])
    return counts


def controls():
    old = ast.parse((ROOT / "experiments/workspace" / EVALUATOR[0]).read_text())
    new = ast.parse(Path(__file__).read_text())
    def selected(tree):
        return next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "evaluate_proto")
    assert ast.dump(selected(old), include_attributes=False) == ast.dump(selected(new), include_attributes=False)
    matrix = {"equalities": [{"terms": [[0, 1], [1, 2]], "rhs": 5}],
              "inequalities": [{"terms": [[0, -1], [1, 1]], "rhs": 1}]}
    assert rows_check(matrix, [1, 2]) == {"equalities": 1, "inequalities": 1}
    assert rows_check(matrix, [12, 24], 12) == {"equalities": 1, "inequalities": 1}
    refused = 0
    for values in ([2, 2], [3, 1]):
        bad = matrix if values == [2, 2] else {"equalities": matrix["equalities"],
                                             "inequalities": [{"terms": [[0, 1]], "rhs": 2}]}
        try:
            rows_check(bad, values)
        except AssertionError:
            refused += 1
    assert refused == 2
    cases = 0
    for size in (3, 6, 12):
        for count in range(size + 1):
            numerator = (12 // size) * count
            assert numerator * size == 12 * count and 0 <= numerator <= 12
            cases += 1
    return {"status": "PASS", "native_evaluator_AST_identical": True,
            "exact_signed_row_checks_and_tamper_rejections": 4,
            "orbit_size_denominator12_controls": cases,
            "production_point_checks": 0, "optimizer_calls": 0}


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

def worker(preparation_path, candidate_path, directory, deadline):
    started, stages = time.monotonic(), []
    def stage(label):
        stages.append({"stage": label, "elapsed_seconds": time.monotonic() - started, "memory": memory()})
        save(directory / "stages.json", {"stages": stages})
        if time.monotonic() > deadline:
            raise TimeoutError("owned restored-parent arithmetic deadline")
    stage("started")
    prepared_raw = preparation_path.read_bytes(); prepared = json.loads(prepared_raw)
    assert prepared["status"] == "PREPARED: exact restored-parent receipt; no production vector checked"
    assert prepared["definition"] == definition() and prepared["controls"]["status"] == "PASS"
    candidate_path = candidate_path.resolve()
    assert candidate_path.is_relative_to(ROOT) and candidate_path.stat().st_size <= 4 * 1024 * 1024
    raw = candidate_path.read_bytes(); values = json.loads(raw)
    assert type(values) is list and len(values) == 18444
    assert all(type(v) is int and abs(v).bit_length() <= 63 for v in values)
    candidate_sha, value_sha = sha(raw), sha(canonical(values))
    binding = {"candidate_path": str(candidate_path.relative_to(ROOT)), "candidate_file_sha256": candidate_sha,
               "canonical_integer_vector_sha256": value_sha, "vector_JSON_field": "root array", "values": 18444}
    model, cold = read("model_preparation"), read("model_cold")
    assert model["status"].startswith("PASS") and cold["status"].startswith("PASS")
    assert cold["preparation_sha256"] == INPUTS["model_preparation"][1]
    query = read("query_preparation")
    assert query["status"].startswith("PASS") and query["definition"]["target_proto_sha256"] == TARGET_SHA
    plan = read("plan"); final_domains = plan["target_variable_domains"]
    assert len(final_domains) == 18444
    del plan; gc.collect()
    for domain, value in zip(final_domains, values):
        assert any(lo <= value <= hi for lo, hi in zip(domain[::2], domain[1::2]))
    stage("complete_final18444_domains_checked")
    original_prepared, original_cold = read("original_preparation"), read("original_cold")
    assert original_prepared["raw_proto_sha256"] == original_cold["raw_proto_sha256"] == ORIGINAL_SHA
    assert original_cold["status"].startswith("PASS")
    from ortools.sat import cp_model_pb2
    native_checks = {}
    for key, expected, rows in (("target", TARGET_SHA, 34398), ("original_native", ORIGINAL_SHA, 34436)):
        path, archive_sha = INPUTS[key]
        payload = (LOGS / path).read_bytes(); assert sha(payload) == archive_sha
        raw = gzip.decompress(payload); del payload
        assert sha(raw) == expected
        proto = cp_model_pb2.CpModelProto(); proto.ParseFromString(raw); del raw
        assert {f.name for f, _ in proto.ListFields()} == {"variables", "constraints"}
        assert len(proto.variables) == 18444 and len(proto.constraints) == rows
        if key == "target":
            assert [list(v.domain) for v in proto.variables] == final_domains
        assert evaluate_proto(proto, values)
        native_checks[key] = {"rows": rows, "variables": 18444,
                              "kinds": dict(Counter(c.WhichOneof("constraint") for c in proto.constraints))}
        del proto; gc.collect(); stage(key + "_all_integer_rows_products_and_tables_checked")
    domains = read("domains")
    assert read("count_cold")["status"].startswith("PASS")
    count_values = values[:15038]
    sizes = domains["new15038_orbit_sizes"]
    assert len(sizes) == 15038 and all(type(s) is int and s in (3, 6, 12) for s in sizes)
    assert all(0 <= v <= size for v, size in zip(count_values, sizes))
    linear = read("counts")
    primitive = rows_check(linear["matrix"], count_values)
    assert primitive == {"equalities": 5973, "inequalities": 21746}
    del linear; gc.collect(); stage("all27719_original_primitive_count_rows_checked")
    original = domains["new15038_to_original15589"]
    assert len(original) == len(set(original)) == 15038 and original[:42] == list(range(42))
    reverse = {old: j for j, old in enumerate(original)}
    blocks = {(i, j): 0 for i in range(42) for j in range(i, 42)}
    assert len(domains["pair_orbit_selector_blocks"]) == 9742
    for po, (i, j) in enumerate(domains["pair_orbit_selector_blocks"]):
        assert 0 <= i <= j < 42
        if 5847 + po in reverse:
            blocks[i, j] += count_values[reverse[5847 + po]]
    for (i, j), total in blocks.items():
        assert total == (count_values[i] * count_values[j] if i != j else count_values[i] * (count_values[i] - 1) // 2)
    assert len(blocks) == 903
    original_sizes = domains["original15589_orbit_sizes"]
    assert len(original_sizes) == 15589 and all(s in (3, 6, 12) for s in original_sizes)
    restored_ids = domains["old15200_to_original15589"]
    assert len(restored_ids) == len(set(restored_ids)) == 15200
    scaled = [0 if old not in reverse else (12 // original_sizes[old]) * count_values[reverse[old]] for old in restored_ids]
    assert all(0 <= v <= 12 for v in scaled)
    stage("all903_population_products_and_denominator12_restoration_checked")
    parent = read("full_parent")
    restored = rows_check(parent["matrix"], scaled, 12)
    assert sum(restored.values()) == 28043
    del parent; gc.collect(); stage("all28043_restored_original_parent_rows_checked")
    refinements = read("refinements")
    assert read("refinement_cold")["status"].startswith("PASS")
    rows = [item["row"] for item in refinements["refinements"]]
    assert len(rows) == 25
    assert rows_check({"equalities": [], "inequalities": rows}, scaled, 12) == {"equalities": 0, "inequalities": 25}
    del refinements, rows; gc.collect(); stage("all25_original_integer_refinements_checked")
    report = {"status": "PASS: exact full-target and restored-parent arithmetic; owner receipt pending",
              "acceptance_source_sha256": file_sha(Path(__file__)), "checker_preparation_sha256": sha(prepared_raw),
              **binding, "target_proto_sha256": TARGET_SHA,
              "model_preparation_sha256": INPUTS["model_preparation"][1],
              "query_preparation_sha256": INPUTS["query_preparation"][1],
              "final_domain_input": {"path": str((LOGS / INPUTS["plan"][0]).relative_to(ROOT)),
                                     "sha256": INPUTS["plan"][1], "JSON_field": "target_variable_domains"},
              "canonical_final_domains_sha256": sha(canonical(final_domains)),
              "full_target_checks_passed": True, "restored_original_parent_checks_passed": True,
              "native_archive_checks": native_checks, "primitive_count_rows": primitive,
              "restored_parent_rows": restored, "deterministic_population_identities": 903,
              "original_integer_refinements": 25, "accepted": False, "count_feasibility_claimed": False,
              "literal_incidence_graph_or_full_PSD_claimed": False, "optimizer_calls": 0,
              "subject_builder_imports_or_constructions": 0, "seconds": time.monotonic() - started,
              "terminal_memory": memory(), "stages_sha256": file_sha(directory / "stages.json")}
    save(directory / "candidate-check.json", report)


def owned(preparation_path, candidate_path, directory):
    started = time.monotonic(); deadline = started + SECONDS
    definition()
    source = ROOT / "experiments/workspace" / OWNER[0]
    spec = importlib.util.spec_from_file_location("frozen_parent_receipt_owner", source)
    owner = importlib.util.module_from_spec(spec); spec.loader.exec_module(owner)
    directory.mkdir(parents=True, exist_ok=False)
    save(directory / "owner-result.json", {"status": "UNKNOWN_BEFORE_CHILD", "accepted": False,
                                          "count_feasibility_claimed": False, "optimizer_calls": 0})
    command = [sys.executable, str(Path(__file__).resolve()), "_worker", "--preparation", str(preparation_path.resolve()),
               "--candidate", str(candidate_path.resolve()), "--directory", str(directory.resolve()), "--deadline", str(deadline)]
    supervision = owner.supervise(command, directory, deadline)
    result = {"status": supervision["status"], "supervision": supervision, "maximum_owned_seconds": SECONDS,
              "acceptance_source_sha256": file_sha(Path(__file__)), "accepted": False,
              "count_feasibility_claimed": False, "optimizer_calls": 0}
    if supervision["status"] == "CHILD_EXITED" and time.monotonic() <= deadline:
        path = directory / "candidate-check.json"; child = json.loads(path.read_bytes())
        assert child["status"].startswith("PASS") and child["acceptance_source_sha256"] == result["acceptance_source_sha256"]
        assert child["full_target_checks_passed"] and child["restored_original_parent_checks_passed"]
        assert not child["accepted"] and not child["count_feasibility_claimed"]
        assert file_sha(candidate_path) == child["candidate_file_sha256"]
        assert file_sha(preparation_path) == child["checker_preparation_sha256"]
        assert child["stages_sha256"] == file_sha(directory / "stages.json")
        assert time.monotonic() <= deadline
        receipt = {**child, "status": "EXACT_COUNT_WITNESS", "accepted": True,
                   "count_feasibility_claimed": True, "arithmetic_report_sha256": file_sha(path),
                   "owner_supervision": supervision, "maximum_owned_seconds": SECONDS}
        save(directory / "receipt.json", receipt)
        result.update(status="EXACT_COUNT_WITNESS", accepted=True, count_feasibility_claimed=True,
                      receipt_sha256=file_sha(directory / "receipt.json"))
    result.update(owner_seconds=time.monotonic() - started, deadline_overrun_seconds=max(0, time.monotonic() - deadline))
    save(directory / "owner-result.json", result)
    print(json.dumps(result, indent=2), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "accept", "_worker"))
    parser.add_argument("--preparation", type=Path)
    parser.add_argument("--candidate", type=Path)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--deadline", type=float)
    args = parser.parse_args()
    if args.mode == "prepare":
        args.directory.mkdir(parents=True, exist_ok=False)
        record = {"status": "PREPARED: exact restored-parent receipt; no production vector checked",
                  "definition": definition(), "controls": controls(), "optimizer_calls": 0}
        save(args.directory / "preparation.json", record)
        print(json.dumps(record, indent=2), flush=True)
    elif args.mode == "accept":
        assert args.preparation is not None and args.candidate is not None
        owned(args.preparation, args.candidate, args.directory)
    else:
        assert args.preparation is not None and args.candidate is not None and args.deadline is not None
        worker(args.preparation, args.candidate, args.directory, args.deadline)
