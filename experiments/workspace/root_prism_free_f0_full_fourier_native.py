"""Native Fourier/local-mask and literal-cut overlay on the complete Y target.

This adapter consumes the frozen Fourier specification and an explicitly
SHA-bound literal-layer configuration. It changes only 42 local tables and
appends the certified variables and constraints. Both complete parent protobuf
hashes must be recovered by reversing these operations. Preparation uses
public CP-SAT constructors and validation, never CpSolver. Cold replay rebuilds
the append from the same certified inputs without ancestor mathematical work.
"""
import argparse
from collections import Counter
import gc
import gzip
import hashlib
import importlib.util
import json
from math import gcd
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
LOGS = ROOT / "experiments/logs/root-prism-free"
SOURCES = {
    "runtime": ("root_prism_free_f0_character_pool_runtime.py", "030163f019b93ee39124e9f3171caac1e4ad79227fde9a1e831c28a938b245f8"),
    "supervisor": ("root_prism_free_f0_local_neighbors_batch.py", "b8e5323f92fa105ff2c0ed5b1667ac25d7c92f85f8cac45b170ddc56208f8278"),
    "specification": ("root_prism_free_f0_full_fourier_specification.py", "e22badc7cacd870898a5f077b5cc82db2b929d3d20704b7cf8103a74639a6915"),
    "parent": ("root_prism_free_f0_character_y_domain_overlay.py", "ff08cbcaec6787d5821af57526a708e1758007970bec58c86584bcd3d76904dd"),
}
INPUTS = {
    "specification": ("f0-full-fourier-specification-ci01/specification.json.gz", "929703b3a685f95fb28bc6553aef02d5c7f6c879628154c62b8ecfa7d69ba8d5"),
    "spec_preparation": ("f0-full-fourier-specification-ci01/report.json", "cd96e24126c1ffab578d69d319431d023e055a82acbc883f66e72a9bdf54c96b"),
    "spec_owner": ("f0-full-fourier-specification-ci01/owner-result.json", "6e2bae09cc008296828ce5cdbbefd3261cdfb405dec8a71ac3af68a812a6fa99"),
    "spec_cold": ("f0-full-fourier-specification-ci01-cold/report.json", "650813eddce7e0c28def494a16756f49b74e1aa13b667806174c13150647e1a5"),
    "spec_cold_owner": ("f0-full-fourier-specification-ci01-cold/owner-result.json", "8fa3be0d75775d9e953bc88099caa8d6eeba3d5ef8082e8e89a74eace5f07455"),
    "parent_preparation": ("f0-character-y-domain-overlay01/report.json", "a4a543b35bdd22357eef39524ff8015e0d4d274547c046205c806a5f52e92061"),
    "parent_cold": ("f0-character-y-domain-overlay01-cold/report.json", "851a2a4a292a891de7b38eb08212fd1a604cf72cc09dbef3af97768ebe8e21be"),
    "parent_review": ("f0-character-y-domain-root-source-review.json", "e5f68917dcfade4ecf36c34771490d15b248a50a77681be00637264c10d0191e"),
    "parent_plan": ("f0-character-y-domain-overlay01/plan.json.gz", "4d3a13718cdac9fcf68b119a1cd1ba009edeb21c7257d4498d5ebdf18954acc4"),
    "parent_target": ("f0-character-y-domain-overlay01/target.pb.gz", "41ff251304c8d3961ebae059581f8416f7f0a45c7cc2246be547296e7db407f0"),
    "parent_initial": ("f0-character-y-domain-overlay01/initial.pb.gz", "ca5e66f17bd53620fe7dd61102d43cb9e581af821c7709eae92dc90b4609a53a"),
}
SPEC_RAW_SHA = "46fa44efdbe3640984a010347a3dfb65964b35752c919f4b6aa2fd24317f1d0b"
PARENT_RAW = {
    "target": "a738d318b6b8de471ee7383f1e6ea11949eed8f8ccf4892814fa2eac268ed153",
    "initial": "9d1e6a031d5c2c83a47982477d51b34fba42edf1bbcdae1bccfa9906745badfe",
}
OLD_VARIABLES, FOURIER_VARIABLES, VARIABLES = 18444, 31756, 32296
OLD_ROWS = {"target": 34398, "initial": 34281}
FOURIER_ROWS = {"target": 54037, "initial": 53920}
FINAL_ROWS = {"target": 58957, "initial": 58840}
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


def relative_path(value):
    assert isinstance(value, str)
    path = (ROOT / value).resolve()
    assert path.is_relative_to(ROOT) and not Path(value).is_absolute()
    return path


def checked_entry(entry):
    assert set(entry) >= {"path", "sha256"}
    expected = entry["sha256"]
    assert isinstance(expected, str) and len(expected) == 64
    assert all(c in "0123456789abcdef" for c in expected)
    path = relative_path(entry["path"])
    assert file_sha(path) == expected, entry["path"]
    return path


def read_entry(entry):
    path = checked_entry(entry)
    raw = path.read_bytes()
    return json.loads(gzip.decompress(raw) if path.suffix == ".gz" else raw)


def read(key):
    name, expected = INPUTS[key]
    return read_entry({"path": str((LOGS / name).relative_to(ROOT)), "sha256": expected})


def source_module(key):
    name, expected = SOURCES[key]
    path = ROOT / "experiments/workspace" / name
    assert file_sha(path) == expected
    spec = importlib.util.spec_from_file_location("frozen_full_Fourier_" + key, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def configuration(path):
    raw = path.read_bytes()
    config = json.loads(raw)
    assert config["schema"] == "conway99.f0.full-Fourier-literal-native-configuration.v1"
    layer = config["literal_layer"]
    assert layer["sources"] and isinstance(layer["sources"], dict)
    checked_entry(layer["record"])
    for entry in layer["sources"].values():
        checked_entry(entry)
    for entry in layer.get("evidence", {}).values():
        checked_entry(entry)
    return config, sha(raw)


def definition(config_path):
    config, config_sha = configuration(config_path)
    for name, expected in SOURCES.values():
        assert file_sha(ROOT / "experiments/workspace" / name) == expected
    for name, expected in INPUTS.values():
        assert file_sha(LOGS / name) == expected
    return {
        "schema": "conway99.f0.full-Fourier-literal-native-overlay.v1",
        "source_sha256": file_sha(Path(__file__)), "configuration_sha256": config_sha,
        "sources": {k: {"path": "experiments/workspace/" + p, "sha256": h} for k, (p, h) in SOURCES.items()},
        "inputs": {k: {"path": str((LOGS / p).relative_to(ROOT)), "sha256": h} for k, (p, h) in INPUTS.items()},
        "literal_layer": config["literal_layer"], "parent_raw_protobuf_sha256": PARENT_RAW,
        "specification_raw_sha256": SPEC_RAW_SHA, "old_variables": OLD_VARIABLES,
        "Fourier_variables": FOURIER_VARIABLES, "variables": VARIABLES,
        "target_constraints": FINAL_ROWS["target"], "initial_constraints": FINAL_ROWS["initial"],
        "products": 16280, "tables": 44, "replaced_local_tables": 42,
        "unchanged_joint_tables": 2, "extended_local_tuples": 64144,
        "old_projected_local_tuples": 19331, "external_pool_constraints": 117,
        "literal_selector_Booleans": 480, "literal_radix_auxiliaries": 60,
        "literal_inverse_links": 480, "literal_cut_native_rows": 4440,
        "original_literal_selector_cuts": 4416,
        "maximum_owned_seconds_per_phase": SECONDS,
        "ancestor_mathematical_or_subset_censuses_repeated": False,
        "new_orientation_or_sign_fixing": False,
        "optimizer_calls": 0, "CpSolver_constructed": False,
        "production_query_authorized_by_this_preparation": False,
    }


def decimal_integer(value):
    assert isinstance(value, str)
    answer = int(value)
    assert str(answer) == value
    return answer


def checked_domain(domain):
    assert domain and len(domain) % 2 == 0
    assert all(type(v) is int and -(1 << 63) <= v < 1 << 63 for v in domain)
    for i in range(0, len(domain), 2):
        assert domain[i] <= domain[i + 1]
        if i:
            assert domain[i - 1] + 1 < domain[i]
    return domain


def checked_terms(terms, variables=VARIABLES):
    assert terms and all(len(pair) == 2 for pair in terms)
    assert all(type(j) is type(c) is int and 0 <= j < variables and c != 0
               and -(1 << 63) <= c < 1 << 63 for j, c in terms)
    assert len({j for j, c in terms}) == len(terms)
    return sorted(terms)


def equation_key(terms, rhs=0):
    terms = sorted((j, c) for j, c in terms if c)
    divisor = abs(rhs)
    for j, c in terms:
        divisor = gcd(divisor, abs(c))
    assert divisor
    if terms[0][1] < 0:
        divisor = -divisor
    return tuple((j, c // divisor) for j, c in terms), rhs // divisor


def controls():
    for v in [0, -1, 1, -(1 << 90), (1 << 90) + 1]:
        assert decimal_integer(str(v)) == v
    bad = ["01", "-0", "+1", "1e3", "1.0", " 1", True, 1.0]
    for value in bad:
        try:
            decimal_integer(value)
        except (AssertionError, ValueError):
            pass
        else:
            raise AssertionError("noncanonical integer accepted")
    row = [[0, 2], [5, -4], [7, 6]]
    for factor in [-7, -2, 1, 3, 11]:
        assert equation_key([[j, c * factor] for j, c in row], 12 * factor) == equation_key(row, 12)
    return {"status": "PASS", "large_integer_controls": 5, "rejected_noncanonical_controls": len(bad),
            "signed_equality_normalization_controls": 5, "optimizer_calls": 0}


def checked_specification(stage):
    preparation, cold = read("spec_preparation"), read("spec_cold")
    for key, report_key in (("spec_owner", "spec_preparation"), ("spec_cold_owner", "spec_cold")):
        owner = read(key)
        assert owner["report_accepted"] and owner["status"].startswith("PASS")
        assert owner["report_sha256"] == INPUTS[report_key][1]
        assert owner["source_sha256"] == SOURCES["specification"][1]
        assert owner["deadline_overrun_seconds"] == 0
    assert preparation["status"].startswith("PASS") and cold["status"].startswith("PASS")
    assert cold["preparation_sha256"] == INPUTS["spec_preparation"][1]
    assert cold["specification_sha256"] == INPUTS["specification"][1]
    assert preparation["source_sha256"] == cold["source_sha256"] == SOURCES["specification"][1]
    assert preparation["checks"] == cold["checks"] and preparation["counts"] == cold["counts"]
    archived = (LOGS / INPUTS["specification"][0]).read_bytes()
    assert sha(archived) == INPUTS["specification"][1]
    raw = gzip.decompress(archived)
    assert sha(raw) == SPEC_RAW_SHA == preparation["specification"]["raw_sha256"]
    spec = json.loads(raw)
    del raw, archived
    assert spec["schema"] == "conway99.f0.full-Fourier-mathematical-specification.v1"
    assert spec["definition"] == preparation["definition"] and spec["counts"] == preparation["counts"]
    assert spec["checks"] == preparation["checks"]
    assert spec["definition"]["inputs"]["parent_plan"]["sha256"] == INPUTS["parent_plan"][1]
    assert len(spec["coordinate_records"]) == 320 and len(spec["product_records"]) == 12992
    assert len(spec["Gram_links"]) == 6496 and len(spec["extended_local_tables"]) == 42
    assert len(spec["literal_inverse_rows"]) == 480 and len(spec["original_equality_expansions"]) == 172
    assert len(spec["nonempty_original_equality_ids"]) == 151
    assert len(spec["target_variable_domains"]) == FOURIER_VARIABLES
    stage("passed_Fourier_specification_and_owned_cold_bound")
    return spec


def checked_literal_layer(config, spec):
    layer = read_entry(config["literal_layer"]["record"])
    assert layer["schema"] == "conway99.f0.literal-cut-native-layer.v1"
    assert layer["base_native_variables"] == FOURIER_VARIABLES
    variables, rows = layer["variables"], layer["linear_constraints"]
    assert len(variables) == 540 and len(rows) == 4920 and len(layer["cut_records"]) == 4416
    assert [v["id"] for v in variables] == list(range(31756, 32296))
    domains = [checked_domain([decimal_integer(x) for x in v["domain"]]) for v in variables]
    assert all(d == [0, 1] for d in domains[:480])
    linear = []
    used = set()
    for row in rows:
        terms = checked_terms([[j, decimal_integer(c)] for j, c in row["terms"]])
        domain = checked_domain([decimal_integer(v) for v in row["domain"]])
        assert len(domain) == 2
        linear.append({"terms": terms, "domain": domain})
        used.update(j for j, c in terms if j >= 31756)
    assert used == set(range(31756, 32296))
    for a, (row, inverse) in enumerate(zip(linear[:480], spec["literal_inverse_rows"])):
        assert inverse["selector"] == a and inverse["denominator"] == 12
        assert row["domain"] == [0, 0]
        expected = inverse["terms"] + [[31756 + a, -12]]
        assert equation_key(row["terms"]) == equation_key(expected)
    audit = {
        "record": config["literal_layer"]["record"],
        "proof_sources_and_evidence": {k: config["literal_layer"].get(k, {}) for k in ("sources", "evidence")},
        "literal_selector_Booleans": 480, "radix_auxiliaries": 60, "linear_rows": 4920,
        "inverse_links_directly_compared_to_Fourier_certificates": 480,
        "cut_records": 4416, "cut_records_sha256": sha(canonical(layer["cut_records"])),
        "all_literal_record_terms_and_domains_copied_exactly": True,
        "literal_cut_proofs_bound_not_rederived": True,
    }
    return domains, linear, audit


def add_linear(proto, terms, domain):
    row = proto.constraints.add().linear
    row.vars.extend(j for j, c in terms)
    row.coeffs.extend(c for j, c in terms)
    row.domain.extend(domain)


def add_table(constraint, columns, tuples):
    constraint.Clear()
    table = constraint.table
    for j in columns:
        expression = table.exprs.add()
        expression.vars.append(j)
        expression.coeffs.append(1)
    table.values.extend(v for row in tuples for v in row)


def prepare_suffix(runtime, spec, literal_domains, literal_rows):
    suffix = runtime.cp_model_pb2.CpModelProto()
    domains = spec["target_variable_domains"] + literal_domains
    assert len(domains) == VARIABLES
    for domain in domains:
        checked_domain(domain)
    for record in spec["coordinate_records"]:
        j = record["native_id"]
        assert j == OLD_VARIABLES + len(suffix.variables)
        assert record["domain"] == domains[j]
        suffix.variables.add(name="f0_Fourier_" + str(j), domain=domains[j])
    for record in spec["product_records"]:
        j = record["native_id"]
        assert j == OLD_VARIABLES + len(suffix.variables) and record["domain"] == domains[j]
        suffix.variables.add(name="f0_Fourier_product_" + str(j), domain=domains[j])
        product = suffix.constraints.add().int_prod
        product.target.vars.append(j)
        product.target.coeffs.append(1)
        assert len(record["factors"]) == 2 and all(18444 <= k < 18764 for k in record["factors"])
        for k in record["factors"]:
            expression = product.exprs.add()
            expression.vars.append(k)
            expression.coeffs.append(1)
    assert len(suffix.variables) == 13312 and len(suffix.constraints) == 12992
    for row in spec["Gram_links"]:
        add_linear(suffix, checked_terms(row["terms"], FOURIER_VARIABLES), [row["rhs"], row["rhs"]])
    nonempty = []
    for row in spec["original_equality_expansions"]:
        if row["literal_zero_tautology"]:
            assert not row["terms"] and row["rhs"] == 0
            continue
        nonempty.append(row["original_row_id"])
        add_linear(suffix, checked_terms(row["terms"], FOURIER_VARIABLES), [row["rhs"], row["rhs"]])
    assert nonempty == spec["nonempty_original_equality_ids"] and len(nonempty) == 151
    assert len(suffix.constraints) == 19639
    for i, domain in enumerate(literal_domains):
        j = 31756 + i
        assert j == OLD_VARIABLES + len(suffix.variables)
        prefix = "f0_literal_" if i < 480 else "f0_literal_radix_"
        suffix.variables.add(name=prefix + str(j), domain=domain)
    for row in literal_rows:
        add_linear(suffix, row["terms"], row["domain"])
    assert len(suffix.variables) == VARIABLES - OLD_VARIABLES
    assert len(suffix.constraints) == 24559
    magnitude = [max(abs(d[0]), abs(d[-1])) for d in domains]
    activities = []
    for constraint in suffix.constraints:
        if constraint.WhichOneof("constraint") == "linear":
            row = constraint.linear
            assert all(-(1 << 63) <= v < 1 << 63 for v in list(row.coeffs) + list(row.domain))
            activity = sum(abs(c) * magnitude[j] for j, c in zip(row.vars, row.coeffs))
            assert activity < 1 << 62
            activities.append(activity)
    return suffix, domains, {"new_linear_rows": len(activities),
                            "maximum_new_linear_absolute_box_activity": max(activities),
                            "suffix_proto_sha256": sha(suffix.SerializeToString())}


def table_replacements(runtime, parent, spec):
    by_columns = {}
    for i, constraint in enumerate(parent.constraints):
        if constraint.WhichOneof("constraint") == "table":
            columns, tuples = runtime.table_data(constraint)
            key = tuple(columns)
            assert key not in by_columns
            by_columns[key] = (i, tuples)
    assert len(by_columns) == 44
    replacements, audits = {}, []
    for table in spec["extended_local_tables"]:
        old_columns, columns, tuples = table["old_columns"], table["columns"], table["tuples"]
        assert columns == old_columns + table["coordinate_columns"]
        assert len(columns) == len(set(columns)) and all(0 <= j < 18764 for j in columns)
        assert all(len(row) == len(columns) and all(type(v) is int for v in row) for row in tuples)
        assert tuples == [list(t) for t in sorted(set(map(tuple, tuples)))]
        row_id, old_tuples = by_columns[tuple(old_columns)]
        assert row_id not in replacements
        projection = sorted({tuple(row[:len(old_columns)]) for row in tuples})
        assert projection == sorted(old_tuples)
        assert len(projection) == table["old_projected_tuple_count"]
        assert sha(canonical(projection)) == table["old_projected_tuples_sha256"]
        assert len(tuples) == len(table["local_mask_witnesses"])
        assert len(set(table["local_mask_witnesses"])) == len(tuples)
        new = runtime.cp_model_pb2.ConstraintProto()
        add_table(new, columns, tuples)
        replacements[row_id] = new
        audits.append({"selector_orbit": table["selector_orbit"], "constraint": row_id,
                       "old_columns": old_columns, "new_columns": columns,
                       "old_tuples": len(old_tuples), "new_tuples": len(tuples),
                       "old_constraint_sha256": sha(parent.constraints[row_id].SerializeToString()),
                       "new_constraint_sha256": sha(new.SerializeToString()),
                       "complete_old_projection_sha256": sha(canonical(projection)),
                       "saved_mask_list_sha256": table["complete_saved_mask_list_sha256"]})
    assert len(replacements) == 42 and [r["selector_orbit"] for r in audits] == list(range(42))
    assert sum(r["old_tuples"] for r in audits) == 19331
    assert sum(r["new_tuples"] for r in audits) == 64144
    joints = sorted(i for i, tuples in by_columns.values() if i not in replacements)
    assert len(joints) == 2
    return replacements, audits, joints


def apply_and_restore(runtime, proto, name, suffix, replacements):
    assert len(proto.variables) == OLD_VARIABLES and len(proto.constraints) == OLD_ROWS[name]
    old_tables = {i: proto.constraints[i].SerializeToString() for i in replacements}
    def apply():
        for i, replacement in replacements.items():
            proto.constraints[i].CopyFrom(replacement)
        proto.variables.extend(suffix.variables)
        proto.constraints.extend(suffix.constraints)
    apply()
    new_sha = sha(proto.SerializeToString())
    assert len(proto.variables) == VARIABLES and len(proto.constraints) == FINAL_ROWS[name]
    del proto.constraints[OLD_ROWS[name]:]
    del proto.variables[OLD_VARIABLES:]
    for i, raw in old_tables.items():
        proto.constraints[i].ParseFromString(raw)
    assert sha(proto.SerializeToString()) == PARENT_RAW[name]
    apply()
    assert sha(proto.SerializeToString()) == new_sha
    return new_sha


def derive(runtime, stage, config):
    spec = checked_specification(stage)
    parent_report, parent_cold = read("parent_preparation"), read("parent_cold")
    assert parent_report["status"].startswith("PASS") and parent_cold["status"].startswith("PASS")
    assert parent_cold["preparation_sha256"] == INPUTS["parent_preparation"][1]
    assert parent_cold["complete_saved_plan_and_protobuf_byte_equality"]
    full_parent = read("parent_plan")
    assert full_parent["source_sha256"] == SOURCES["parent"][1]
    assert full_parent["variable_count"] == OLD_VARIABLES
    assert full_parent["full_target_constraints"] == OLD_ROWS["target"]
    assert full_parent["initial_constraints"] == OLD_ROWS["initial"]
    assert full_parent["external_pool_constraints"] == 117
    parent = {k: full_parent[k] for k in ("target_variable_domains", "initial_to_target_rows", "external_pool")}
    del full_parent
    assert spec["target_variable_domains"][:OLD_VARIABLES] == parent["target_variable_domains"]
    assert sha(canonical(parent["target_variable_domains"])) == spec["parent_variable_domains_sha256"]
    literal_domains, literal_rows, literal_audit = checked_literal_layer(config, spec)
    suffix, domains, suffix_audit = prepare_suffix(runtime, spec, literal_domains, literal_rows)
    del literal_domains, literal_rows
    stage("all_Fourier_and_literal_suffix_rows_and_domains_transcribed")
    protos, tables, joints, raw_hashes = {}, {}, {}, {}
    for name, expected in PARENT_RAW.items():
        archived = (LOGS / INPUTS["parent_" + name][0]).read_bytes()
        assert sha(archived) == INPUTS["parent_" + name][1]
        raw = gzip.decompress(archived)
        assert sha(raw) == expected == parent_report["outputs"][name]["raw_sha256"]
        proto = runtime.cp_model_pb2.CpModelProto()
        proto.ParseFromString(raw)
        del raw, archived
        assert {f.name for f, _ in proto.ListFields()} == {"variables", "constraints"}
        assert [list(v.domain) for v in proto.variables] == parent["target_variable_domains"]
        replacements, tables[name], joints[name] = table_replacements(runtime, proto, spec)
        raw_hashes[name] = apply_and_restore(runtime, proto, name, suffix, replacements)
        protos[name] = proto
        del replacements
        gc.collect()
        stage(name + "_table_replacement_append_and_whole_parent_restoration_checked")
    target, initial = protos["target"], protos["initial"]
    rows, pool = parent["initial_to_target_rows"], parent["external_pool"]
    assert rows == sorted(set(rows)) and len(rows) == OLD_ROWS["initial"]
    assert [r["pool_id"] for r in pool] == list(range(117))
    external = [r["target_constraint"] for r in pool]
    assert len(set(external)) == 117 and not set(external).intersection(rows)
    assert sorted(external + rows) == list(range(OLD_ROWS["target"]))
    for entry in pool:
        constraint = target.constraints[entry["target_constraint"]]
        assert constraint.WhichOneof("constraint") == "linear"
        assert sha(constraint.SerializeToString()) == entry["constraint_sha256"]
        assert len(constraint.linear.vars) == entry["terms"]
    for a, b in zip(tables["target"], tables["initial"]):
        assert a["selector_orbit"] == b["selector_orbit"]
        assert rows[b["constraint"]] == a["constraint"]
        assert a["old_constraint_sha256"] == b["old_constraint_sha256"]
        assert a["new_constraint_sha256"] == b["new_constraint_sha256"]
    new_rows = rows + list(range(OLD_ROWS["target"], FINAL_ROWS["target"]))
    assert sorted(external + new_rows) == list(range(FINAL_ROWS["target"]))
    assert [list(v.domain) for v in target.variables] == domains
    checked = runtime.exact_proto_check(initial, target, new_rows)
    full_checked = runtime.exact_proto_check(target, target, list(range(FINAL_ROWS["target"])))
    assert checked["variables"] == full_checked["variables"] == VARIABLES
    assert checked["constraint_types"] == {"linear": 42516, "int_prod": 16280, "table": 44}
    assert full_checked["constraint_types"] == {"linear": 42633, "int_prod": 16280, "table": 44}
    plan = {
        "schema": "conway99.f0.full-Fourier-literal-runtime-plan.v1",
        "source_sha256": file_sha(Path(__file__)),
        "variable_count": VARIABLES, "full_target_constraints": FINAL_ROWS["target"],
        "initial_constraints": FINAL_ROWS["initial"], "external_pool_constraints": 117,
        "initial_to_target_rows": new_rows, "external_pool": pool, "target_variable_domains": domains,
        "old_to_target_columns": list(range(OLD_VARIABLES)),
        "target_to_old_columns": list(range(OLD_VARIABLES)) + [None] * (VARIABLES - OLD_VARIABLES),
        "parent_plan": {"path": INPUTS["parent_plan"][0], "sha256": INPUTS["parent_plan"][1]},
        "parent_preparation_sha256": INPUTS["parent_preparation"][1],
        "parent_cold_sha256": INPUTS["parent_cold"][1], "parent_proto_sha256": PARENT_RAW,
        "specification_sha256": INPUTS["specification"][1], "specification_raw_sha256": SPEC_RAW_SHA,
        "specification_preparation_sha256": INPUTS["spec_preparation"][1],
        "specification_cold_sha256": INPUTS["spec_cold"][1],
        "literal_layer": literal_audit, "suffix_audit": suffix_audit,
        "local_table_replacements": tables, "unchanged_joint_table_rows": joints,
        "new_column_intervals": {"Fourier_coordinates": [18444, 18764], "Fourier_products": [18764, 31756],
                                 "literal_selectors": [31756, 32236], "literal_radix_auxiliaries": [32236, 32296]},
        "target_row_intervals": {"Fourier_products": [34398, 47390], "Gram_links": [47390, 53886],
                                "original_equalities": [53886, 54037], "literal_inverse": [54037, 54517],
                                "literal_cut_rows": [54517, 58957]},
        "initial_row_intervals": {"Fourier_products": [34281, 47273], "Gram_links": [47273, 53769],
                                 "original_equalities": [53769, 53920], "literal_inverse": [53920, 54400],
                                 "literal_cut_rows": [54400, 58840]},
        "original_selector_equations_certified": 172,
        "nonempty_original_equality_ids": spec["nonempty_original_equality_ids"],
        "literal_zero_equalities_omitted": 21, "new_orientation_or_sign_fixing": False,
        "all92_held_PSD_rows_and117_external_pool_rows_preserved": True,
        "complete_parent_hash_restoration": PARENT_RAW,
        "full_target_pass_is_PROVISIONAL_until_original_parent_and_literal_checks": True,
        "count_or_literal_or_exterior_graph_feasibility_claimed": False,
    }
    del spec, suffix, parent, target, initial
    gc.collect()
    stage("all_maps_pool_rows_bounds_and_native_constraint_groups_checked")
    return plan, protos, checked, full_checked


def archive(path, raw):
    assert len(raw) <= 64 << 20
    payload = gzip.compress(raw, mtime=0)
    with path.open("xb") as stream:
        stream.write(payload)
    return {"path": str(path.relative_to(ROOT)), "sha256": sha(payload),
            "raw_sha256": sha(raw), "raw_bytes": len(raw), "bytes": len(payload)}


def worker(mode, directory, deadline, config_path, saved_directory=None):
    started, stages = time.monotonic(), []
    runtime = source_module("runtime")
    def stage(label, **extra):
        stages.append({"stage": label, "elapsed_seconds": time.monotonic() - started,
                       "memory": runtime.memory_snapshot(), **extra})
        save(directory / "stages.json", {"stages": stages, "optimizer_calls": 0})
        if time.monotonic() > deadline:
            raise TimeoutError("owned full Fourier native overlay deadline")
    try:
        stage("started")
        bound = definition(config_path)
        config, config_sha = configuration(config_path)
        control = controls()
        runtime.import_native(stage)
        plan, protos, checked, full_checked = derive(runtime, stage, config)
        plan["configuration_sha256"] = config_sha
        if mode == "prepare":
            outputs = {"plan": archive(directory / "plan.json.gz", canonical(plan))}
            for name, proto in protos.items():
                outputs[name] = archive(directory / (name + ".pb.gz"), proto.SerializeToString())
            del proto
            del protos["target"]
            gc.collect()
            stage("archives_saved_full_target_released_before_public_construction")
            initial = protos["initial"]
            model = runtime.cp_model.CpModel()
            variables = [model.new_int_var_from_domain(runtime.cp_model.Domain.from_flat_intervals(list(v.domain)), v.name)
                         for v in initial.variables]
            assert [v.index for v in variables] == list(range(VARIABLES))
            for i, constraint in enumerate(initial.constraints):
                runtime.append_constraint(model, variables, constraint)
                if (i + 1) % 4096 == 0:
                    stage("native_initial_prefix_constructed", constraints=i + 1)
            assert model.validate() == ""
            export = directory / "native-initial.pb"
            assert model.export_to_file(str(export))
            assert file_sha(export) == outputs["initial"]["raw_sha256"]
            stage("native_validation_and_complete_initial_byte_identity_passed")
            report = {
                "status": "PASS: complete Fourier and literal native overlay; no solver",
                "definition": bound, "controls": control, "outputs": outputs,
                "native_initial_exact_checks": checked, "full_target_exact_checks": full_checked,
                "native_initial_public_constructor_byte_identity": True,
                "all117_external_pool_rows_and_ids_unchanged": True,
                "whole_parent_protobuf_hashes_restored": PARENT_RAW,
                "all42_old_local_table_projections_checked": True,
                "literal_inverse_links_checked": 480, "literal_cut_proofs_bound_not_rederived": True,
                "suffix_audit": plan["suffix_audit"],
                "optimizer_calls": 0, "CpSolver_constructed": False,
            }
        else:
            assert mode == "cold" and saved_directory is not None
            saved_raw = (saved_directory / "report.json").read_bytes()
            old = json.loads(saved_raw)
            assert old["status"].startswith("PASS") and old["definition"] == bound
            assert old["controls"] == control
            assert old["native_initial_exact_checks"] == checked and old["full_target_exact_checks"] == full_checked
            for name, raw in [("plan", canonical(plan))] + [(k, p.SerializeToString()) for k, p in protos.items()]:
                entry = old["outputs"][name]
                path = ROOT / entry["path"]
                assert file_sha(path) == entry["sha256"]
                assert gzip.decompress(path.read_bytes()) == raw
                assert sha(raw) == entry["raw_sha256"] and len(raw) == entry["raw_bytes"]
            stage("complete_overlay_plan_and_both_protobufs_cold_checked")
            report = {
                "status": "PASS: complete Fourier and literal native overlay cold replay",
                "source_sha256": file_sha(Path(__file__)), "preparation_sha256": sha(saved_raw),
                "definition": bound, "controls": control,
                "complete_saved_plan_and_protobuf_byte_equality": True,
                "whole_parent_protobuf_hashes_restored": PARENT_RAW,
                "native_model_construction_or_validation_repeated": False,
                "ancestor_mathematical_or_subset_censuses_repeated": False,
                "optimizer_calls": 0, "CpSolver_constructed": False,
            }
        report.update(seconds=time.monotonic() - started, terminal_memory=runtime.memory_snapshot(),
                      stages_sha256=file_sha(directory / "stages.json"))
        save(directory / "report.json", report)
    except Exception as error:
        save(directory / "error.json", {"error_type": type(error).__name__, "message": str(error),
                                       "memory": runtime.memory_snapshot(), "optimizer_calls": 0})
        raise


def owned(mode, directory, config_path, saved_directory=None):
    started = time.monotonic()
    deadline = started + SECONDS
    definition(config_path)
    supervisor = source_module("supervisor")
    directory.mkdir(parents=True, exist_ok=False)
    command = [sys.executable, str(Path(__file__).resolve()), "_" + mode,
               "--directory", str(directory.resolve()), "--deadline", str(deadline),
               "--configuration", str(config_path.resolve())]
    if saved_directory is not None:
        command.extend(("--saved-directory", str(saved_directory.resolve())))
    save(directory / "owner-result.json", {"status": "UNKNOWN_BEFORE_CHILD", "optimizer_calls": 0})
    supervision = supervisor.supervise(command, directory, deadline)
    result = {"status": supervision["status"], "supervision": supervision, "report_accepted": False,
              "source_sha256": file_sha(Path(__file__)), "configuration_sha256": file_sha(config_path),
              "maximum_owned_seconds": SECONDS, "optimizer_calls": 0, "CpSolver_constructed": False}
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
    parser.add_argument("--configuration", type=Path, required=True)
    parser.add_argument("--saved-directory", type=Path)
    parser.add_argument("--deadline", type=float)
    args = parser.parse_args()
    if args.mode.startswith("_"):
        assert args.deadline is not None
        worker(args.mode[1:], args.directory, args.deadline, args.configuration, args.saved_directory)
    else:
        owned(args.mode, args.directory, args.configuration, args.saved_directory)
