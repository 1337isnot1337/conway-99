"""Exact full count target and an initial model with 117 external rows.

The full target removes only the42 basic tables implied by the42 retained
character tables, appends two certified joint tables, and intersects exact
table/product/census domains. Two common-phase rows choose a proved equivalent
representative. Every old linear row and product remains.
No optimizer or CpSolver is constructed by this preparation/replay module.
"""
import argparse
from collections import Counter, defaultdict
import gzip
import hashlib
import itertools
import json
from pathlib import Path
import time

import ortools
from google.protobuf import text_format
from ortools.sat import cp_model_pb2
from ortools.sat.python import cp_model

import root_prism_free_f0_character_cpsat as parent

ROOT = Path(__file__).resolve().parents[2]
LOGS = ROOT / "experiments/logs/root-prism-free"
PARENT_SHA = "879cdb9be48f9377dd6bccd078f26a568d12467385e9ecb1d5b260cc56ff64e7"
PARENT_PROTO_SHA = "5b43e3c026dbe71fcc8d072aa1790b80f7a81312e7b1ebf36a37612b2f726eeb"
TABLE_SOURCE_SHA = "8673b7590d4245efe07ae7c7da5cc18563bc7d4cb9114a76c3f0d86c30ee8f17"
PHASE_SOURCE_SHA = "39a12ceb362fea57944637f94f79911ddcfac3c11c9a4478406cf8f6a34025e1"
CENSUS_SOURCE_SHA = "effec5c6557cef35ac16cef3093959fc6c97882baa799e73f8078624a1d03229"
CP_MODEL_SHA = "b5f2a3ae5c418d11af23cb77a766fa10103c8bb71703dafa1ecad74823603f25"
INPUTS = {
    "parent_archive": ("f0-character-cpsat01/model.pb.gz", "81acda719e5d7a65ccfeb95bcd956785ee9283d60630aed2f8933599933f3f57"),
    "parent_preparation": ("f0-character-cpsat01/report.json", "e15c4bfcf7adaabb60258e3cffa8046eb0cd97843ae8787a24b356011d7b8a5f"),
    "parent_cold": ("f0-character-cpsat01-cold/report.json", "fd86705f404e899869234d67916c2178d77acfb9c2b847571fb897cc5f785e18"),
    "parent_review": ("f0-character-cpsat-root-source-review.json", "46712ba2491fd0066e8ea79d0ebba094cfd18b7a8be069c966e73bbf85f0402a"),
    "parent_peer": ("f0-character-cpsat-independent-sets-source-review.json", "393aed8c1c801d01b65e451db36c93f266c3b2561637f24f62bb909f7d6c1fd0"),
    "products": ("f0-population-products02-specification.json.gz", "c83ebbc1d0d4e9b5ec5ccd60ed5e52ea2be2cb24f1de570f6bff8bb158d42e0c"),
    "joint_tables": ("f0-two-orbit-profiles01.json.gz", "6a1bc6d196358ecc618355bc64d6fe6a2b60be9fa9411afd29526c9f493995b9"),
    "joint_cold": ("f0-two-orbit-profiles01-cold.json", "afedafe2f3009849350b1682a2c329064efd9b204ab7b5a6051e5d50449fcf41"),
    "joint_review": ("f0-two-orbit-profiles-literature-review.json", "62348d643001fcf3f7ac1f50184e08b4bca5e84e061e6281070d4b7a33f97c24"),
    "log_analysis": ("f0-character-query-run01-log-analysis.json", "739e3ea18cd53d23a3caebe49b4f8849bac40b5bada20a487a6ac2a4c1f5e027"),
    "phase": ("f0-character-phase-normalization01.json", "737389ccfd5290072e8dd4cb12a63bfa3a6cae2d10a6ece2793c0a891aff7e04"),
    "phase_cold": ("f0-character-phase-normalization01-cold.json", "56c67d0049db09454abc33d2801a9a66edb0b75e120df8c5f6c07f9ce65fb36b"),
    "phase_review": ("f0-character-phase-unrestricted-source-review.json", "36887b846c5cda9f352c6bc8792eee5dc75c15e8903183ba1eeb92bacdfdbaf2"),
    "census": ("f0-coupled-population-three-census01.json.gz", "bc6f74139acbc3f995bea5cfe8d61877dab5b8457b968cffe8bef6d2fb69d80d"),
    "census_preparation": ("f0-coupled-population-three-preparation01.json.gz", "a46d1080a4edebf47c843bab98598920e6490bdf50447f55fe407e86ede5d156"),
    "census_cold": ("f0-coupled-population-three-census01-cold.json", "6f70a1092952df17ad04ebfe2287a82aa71479241d4e2f17e3857dee0f78a5d4"),
    "census_review": ("f0-coupled-population-three-root-source-review.json", "12e9a0feb9f828a032e4b2a063fbadad2b43d1c131921e2b3ce9e384dddb0e8b"),
}
VARIABLES, OLD_CONSTRAINTS = 18444, 34436
TARGET_CONSTRAINTS, INITIAL_CONSTRAINTS = 34398, 34281
BASIC_START, REFINED_START = 29550, 34394


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def save_new(path, value):
    raw = canonical(value) + b"\n"
    if str(path).endswith(".gz"):
        raw = gzip.compress(raw, mtime=0)
    with path.open("xb") as stream:
        stream.write(raw)
    return {"path": str(path.relative_to(ROOT)), "sha256": sha(raw), "bytes": len(raw)}


def load_inputs():
    assert sha(Path(parent.__file__).read_bytes()) == PARENT_SHA
    assert sha(Path(__file__).with_name("root_prism_free_f0_two_orbit_profiles.py").read_bytes()) == TABLE_SOURCE_SHA
    assert sha(Path(__file__).with_name("root_prism_free_f0_character_phase.py").read_bytes()) == PHASE_SOURCE_SHA
    assert sha(Path(__file__).with_name("root_prism_free_f0_coupled_population_three.py").read_bytes()) == CENSUS_SOURCE_SHA
    assert ortools.__version__ == "9.15.6755" and sha(Path(cp_model.__file__).read_bytes()) == CP_MODEL_SHA
    data = {}
    for key, (name, expected) in INPUTS.items():
        raw = (LOGS / name).read_bytes()
        assert sha(raw) == expected, key
        if key == "parent_archive":
            raw = gzip.decompress(raw)
            assert sha(raw) == PARENT_PROTO_SHA
            proto = cp_model_pb2.CpModelProto()
            proto.ParseFromString(raw)
            data["parent_proto"] = proto
        else:
            data[key] = json.loads(gzip.decompress(raw) if name.endswith(".gz") else raw)
    assert {f.name for f, _ in proto.ListFields()} == {"variables", "constraints"}
    assert (len(proto.variables), len(proto.constraints)) == (VARIABLES, OLD_CONSTRAINTS)
    for key in ("parent_preparation", "parent_cold", "parent_review", "parent_peer", "joint_cold", "joint_review",
                "log_analysis", "phase", "phase_cold", "phase_review", "census_cold", "census_review"):
        assert data[key]["status"].startswith("PASS"), key
    assert data["parent_preparation"]["raw_proto_sha256"] == data["parent_cold"]["raw_proto_sha256"] == PARENT_PROTO_SHA
    assert data["joint_cold"]["record_sha256"] == INPUTS["joint_tables"][1]
    assert data["joint_tables"]["source_sha256"] == data["joint_cold"]["source_sha256"] == TABLE_SOURCE_SHA
    assert len(data["joint_tables"]["tables"]) == 2
    assert data["phase"]["source_sha256"] == data["phase_cold"]["source_sha256"] == PHASE_SOURCE_SHA
    assert data["phase_cold"]["record_sha256"] == INPUTS["phase"][1]
    assert data["census"]["source_sha256"] == data["census_cold"]["source_sha256"] == CENSUS_SOURCE_SHA
    assert data["census_cold"]["record_sha256"] == INPUTS["census"][1]
    assert data["census"]["preparation_sha256"] == data["census_cold"]["preparation_sha256"] == INPUTS["census_preparation"][1]
    assert data["census"]["census"]["complete"] and data["census_cold"]["complete_product_scope"]
    assert data["census_cold"]["checked_literal_pairs"] == 262144 and data["census_cold"]["surviving_literal_pairs"] == 178304
    return data


def values_from_domain(domain):
    assert len(domain) % 2 == 0
    result = set()
    for lo, hi in zip(domain[::2], domain[1::2]):
        assert type(lo) is int and type(hi) is int and lo <= hi and hi - lo <= 300
        result.update(range(lo, hi + 1))
    assert result and len(result) <= 301
    return result


def domain_from_values(values):
    values = sorted(set(values))
    assert values and all(type(v) is int for v in values)
    out = [values[0], values[0]]
    for value in values[1:]:
        if value == out[-1] + 1:
            out[-1] = value
        else:
            out.extend([value, value])
    assert values_from_domain(out) == set(values)
    return out


def single_variable(expression):
    assert list(expression.coeffs) == [1] and len(expression.vars) == 1 and expression.offset == 0
    assert expression.vars[0] >= 0
    return expression.vars[0]


def table_data(constraint):
    assert {f.name for f, _ in constraint.ListFields()} == {"table"}
    table = constraint.table
    assert not table.negated and not table.vars
    columns = [single_variable(e) for e in table.exprs]
    assert columns and len(set(columns)) == len(columns)
    width = len(columns)
    assert len(table.values) % width == 0
    tuples = [tuple(table.values[i:i + width]) for i in range(0, len(table.values), width)]
    assert tuples and len(tuples) == len(set(tuples))
    return columns, tuples


def new_table_constraint(columns, tuples):
    result = cp_model_pb2.ConstraintProto()
    for j in columns:
        expression = result.table.exprs.add()
        expression.vars.append(j)
        expression.coeffs.append(1)
    result.table.values.extend(v for row in tuples for v in row)
    assert table_data(result) == (columns, [tuple(row) for row in tuples])
    return result


def project_domains(proto, tables, products):
    """Necessary coordinate projections, then one forward product pass."""
    original = [values_from_domain(list(v.domain)) for v in proto.variables]
    domains = [set(v) for v in original]
    premises = defaultdict(list)
    for row_id, columns, tuples in tables:
        for position, j in enumerate(columns):
            allowed = {row[position] for row in tuples}
            assert allowed <= original[j]
            premises[j].append({"target_table_row": row_id, "table_position": position,
                                "allowed_values": sorted(allowed)})
            domains[j].intersection_update(allowed)
            assert domains[j], ("empty table intersection", j)
    table_witnesses = [{"variable": j, "before_domain": list(proto.variables[j].domain),
                        "table_premises": witnesses, "after_values": sorted(domains[j])}
                       for j, witnesses in sorted(premises.items())]
    product_witnesses = []
    seen_targets = set()
    factor_ids = {j for _, _, factors in products for j in factors}
    for row_id, target, factors in products:
        assert target not in factor_ids and target not in seen_targets
        seen_targets.add(target)
        a, b = factors
        before = sorted(domains[target])
        possible = {x * x for x in domains[a]} if a == b else {x * y for x in domains[a] for y in domains[b]}
        domains[target].intersection_update(possible)
        assert domains[target], ("empty product domain", target)
        product_witnesses.append({"target_product_row": row_id, "target_variable": target,
                                  "factor_variables": factors, "factor_values": [sorted(domains[a]), sorted(domains[b])],
                                  "same_variable_square": a == b, "all_factor_products": sorted(possible),
                                  "before_values": before, "after_values": sorted(domains[target])})
    return [domain_from_values(v) for v in domains], table_witnesses, product_witnesses


def derive(data):
    old = data["parent_proto"]
    omitted, witnesses = set(range(BASIC_START, BASIC_START + 42)), []
    for i in range(42):
        basic_columns, basic = table_data(old.constraints[BASIC_START + i])
        refined_columns, refined = table_data(old.constraints[REFINED_START + i])
        assert refined_columns[:len(basic_columns)] == basic_columns
        projection = {row[:len(basic_columns)] for row in refined}
        assert projection == set(basic)
        witnesses.append({"omitted_parent_constraint": BASIC_START + i,
                          "retained_refined_parent_constraint": REFINED_START + i,
                          "basic_columns": basic_columns, "refined_columns": refined_columns,
                          "basic_tuples": len(basic), "refined_tuples": len(refined),
                          "projected_tuples_sha256": sha(canonical(sorted(projection))),
                          "basic_constraint_sha256": sha(old.constraints[BASIC_START + i].SerializeToString()),
                          "refined_constraint_sha256": sha(old.constraints[REFINED_START + i].SerializeToString())})
    target = cp_model_pb2.CpModelProto()
    target.variables.extend(old.variables)
    old_to_target, target_to_old = [None] * OLD_CONSTRAINTS, []
    for i, constraint in enumerate(old.constraints):
        if i not in omitted:
            old_to_target[i] = len(target.constraints)
            target_to_old.append(i)
            target.constraints.add().CopyFrom(constraint)
    joint_witnesses = []
    phase_rows = data["phase"]["normalization_rows"]
    assert phase_rows == [{"terms": [[15941, 1], [15942, 1]], "lower": 1, "upper": 3},
                          {"terms": [[15979, 1], [15980, 1]], "lower": 1, "upper": 3}]
    for index, table in enumerate(data["joint_tables"]["tables"]):
        assert table["selector_orbits"] == ([0, 1] if index == 0 else [6, 7])
        row_id = table["inherited_count_equality_row"]
        equality = old.constraints[row_id].linear
        assert list(equality.vars) == table["selector_orbits"] and list(equality.coeffs) == [1, 1]
        assert list(equality.domain) == [3, 3]
        columns = table["count_columns"] + [15941 + j for j in table["signed_population_columns"]]
        all_tuples = [p["counts_and_signed_populations"] for p in table["profiles"]]
        assert len(columns) == 28 and len(all_tuples) == 176
        positions = {j: k for k, j in enumerate(columns)}
        retained_indices = list(range(176))
        if index == 0:
            retained_indices = [i for i, row in enumerate(all_tuples)
                                if all(p["lower"] <= sum(c * row[positions[j]] for j, c in p["terms"]) <= p["upper"]
                                       for p in phase_rows)]
            assert retained_indices == data["phase"]["normalized_first_joint_table_profile_indices"]
            assert len(retained_indices) == 44
        tuples = [all_tuples[i] for i in retained_indices]
        for orbit in table["selector_orbits"]:
            previous_columns, previous = table_data(old.constraints[REFINED_START + orbit])
            previous = set(previous)
            assert all(tuple(row[positions[j]] for j in previous_columns) in previous for row in tuples)
        assert all(sum(row[:2]) == sum(row[2:22]) == 3 for row in tuples)
        target_id = len(target.constraints)
        target.constraints.add().CopyFrom(new_table_constraint(columns, tuples))
        target_to_old.append(None)
        joint_witnesses.append({"target_constraint": target_id, "table_record_index": index,
                                "columns": columns, "tuples": len(tuples),
                                "original_tuples": 176, "retained_original_profile_indices": retained_indices,
                                "population_parent_equality": row_id,
                                "table_record_sha256": INPUTS["joint_tables"][1],
                                "all_tuple_projections_to_retained_tables_checked": True})
    phase_witnesses = []
    for row in phase_rows:
        index = len(target.constraints)
        native = target.constraints.add().linear
        native.vars.extend(j for j, c in row["terms"])
        native.coeffs.extend(c for j, c in row["terms"])
        native.domain.extend([row["lower"], row["upper"]])
        target_to_old.append(None)
        phase_witnesses.append({"target_constraint": index, "row": row,
                                "certificate_sha256": INPUTS["phase"][1],
                                "coverage": "One common phase for all signed variables, preserving all count/product values."})
    assert len(target.constraints) == TARGET_CONSTRAINTS
    tables, products = [], []
    for i, constraint in enumerate(target.constraints):
        kind = constraint.WhichOneof("constraint")
        assert {f.name for f, _ in constraint.ListFields()} == {kind}
        if kind == "table":
            columns, tuples = table_data(constraint)
            tables.append((i, columns, tuples))
        elif kind == "int_prod":
            assert len(constraint.int_prod.exprs) == 2
            products.append((i, single_variable(constraint.int_prod.target),
                             [single_variable(e) for e in constraint.int_prod.exprs]))
        else:
            assert kind == "linear" and constraint.linear.vars
    assert len(tables) == 44 and len(products) == 3288
    domains, table_domains, product_domains = project_domains(target, tables, products)
    census_domains = []
    non_count_ids = {j for _, t, factors in products for j in [t] + factors}
    for record in data["census"]["census"]["cross_count_domains"]:
        j = record["reduced15038_column"]
        if j is None:
            assert record["proved_zero_before_census"] and record["observed_values"] == [0]
            continue
        assert 42 <= j < 15038 and j not in non_count_ids
        assert record["complete_domain_certified"] and not record["proved_zero_before_census"]
        allowed = record["observed_values"]
        assert allowed == ([0, 1, 2] if j in (5699, 5812) else [0, 1, 2, 3])
        previous = list(domains[j])
        domains[j] = domain_from_values(values_from_domain(previous) & set(allowed))
        census_domains.append({"variable": j, "before_domain": previous, "after_domain": domains[j],
                               "complete_census_domain": allowed,
                               "original15589_column": record["original15589_column"],
                               "original_pair_orbit": record["original_pair_orbit"],
                               "census_record_sha256": INPUTS["census"][1]})
    assert len(census_domains) == 46
    for variable, domain in zip(target.variables, domains):
        del variable.domain[:]
        variable.domain.extend(domain)
    specification = data["products"]
    psd = specification["inherited92_PSD_row_indices"]
    assert len(psd) == len(set(psd)) == 92
    assert psd == list(range(21530, 21601)) + list(range(27440, 27461))
    dense_parent = psd + list(range(27719, 27744))
    pool = []
    for i, old_id in enumerate(dense_parent):
        target_id = old_to_target[old_id]
        assert target_id is not None and target.constraints[target_id].WhichOneof("constraint") == "linear"
        pool.append({"pool_id": i, "parent_constraint": old_id, "target_constraint": target_id,
                     "family": "held_PSD_direction" if i < 92 else "selector_integer_refinement",
                     "constraint_sha256": sha(old.constraints[old_id].SerializeToString()),
                     "terms": len(old.constraints[old_id].linear.vars)})
    assert len(pool) == 117 and sum(row["terms"] for row in pool) == 1066362
    pool_ids = {r["target_constraint"] for r in pool}
    initial_to_target = [i for i in range(TARGET_CONSTRAINTS) if i not in pool_ids]
    target_to_initial = [None] * TARGET_CONSTRAINTS
    for i, target_id in enumerate(initial_to_target):
        target_to_initial[target_id] = i
    assert len(initial_to_target) == INITIAL_CONSTRAINTS
    original_domains = [list(v.domain) for v in old.variables]
    changed = [i for i, (a, b) in enumerate(zip(original_domains, domains)) if a != b]
    plan = {"schema": "conway99.f0-character-dense-pool-target.v1",
            "source_sha256": sha(Path(__file__).read_bytes()),
            "parent_source_sha256": PARENT_SHA, "parent_proto_sha256": PARENT_PROTO_SHA,
            "table_source_sha256": TABLE_SOURCE_SHA,
            "phase_source_sha256": PHASE_SOURCE_SHA, "census_source_sha256": CENSUS_SOURCE_SHA,
            "inputs": {k: {"path": "experiments/logs/root-prism-free/" + p, "sha256": h} for k, (p, h) in INPUTS.items()},
            "variable_count": VARIABLES, "full_target_constraints": TARGET_CONSTRAINTS,
            "initial_constraints": INITIAL_CONSTRAINTS, "external_pool_constraints": 117,
            "old_to_target_columns": list(range(VARIABLES)), "target_to_old_columns": list(range(VARIABLES)),
            "parent_to_target_rows": old_to_target, "target_to_parent_rows": target_to_old,
            "initial_to_target_rows": initial_to_target, "target_to_initial_rows": target_to_initial,
            "omitted_basic_table_witnesses": witnesses, "new_joint_table_witnesses": joint_witnesses,
            "phase_normalization_witnesses": phase_witnesses,
            "table_coordinate_domain_witnesses": table_domains,
            "product_target_domain_witnesses": product_domains,
            "coupled_census_domain_witnesses": census_domains,
            "target_variable_domains": domains, "changed_domain_variables": changed,
            "domain_summary": {"table_coordinates": len(table_domains),
                               "table_changed_coordinates": sum(w["before_domain"] != domain_from_values(w["after_values"]) for w in table_domains),
                               "product_targets": len(product_domains),
                               "product_changed_coordinates": sum(w["before_values"] != w["after_values"] for w in product_domains),
                               "census_coordinates": len(census_domains),
                               "census_changed_coordinates": sum(w["before_domain"] != w["after_domain"] for w in census_domains),
                               "all_changed_coordinates": len(changed),
                               "target_domains_with_holes": sum(len(v) > 2 for v in domains),
                               "fixed_coordinates": sum(len(v) == 2 and v[0] == v[1] for v in domains)},
            "external_pool": pool,
            "full_target_keeps_all_parent_linear_rows_products_and92_PSD_directions": True,
            "basic_table_removal_equivalent_by_exact_projection": True,
            "domain_restrictions_implied_by_retained_tables_products_or_explicit_census": True,
            "new_mathematical_conditions": "Two certified population-three joint tables and46 coupled-census count domains.",
            "equivalent_common_phase_normalization_added": True,
            "normalization_is_not_a_restriction_on_every_labelled_signed_assignment": True,
            "first_joint_table_filter_equivalent_after_the_two_explicit_phase_rows": True,
            "independent_per_orbit_phase_fixed_population_or_saved_candidate_added": False,
            "complete_old_parent_required_for_final_integer_acceptance": True,
            "original_complete_cold_record_bound_not_recomputed": INPUTS["parent_cold"][1],
            "table_subset_censuses_not_repeated": True,
            "optimizer_calls": 0, "CpSolver_constructed": False}
    return plan, target


def append_constraint(model, variables, constraint):
    kind = constraint.WhichOneof("constraint")
    assert {f.name for f, _ in constraint.ListFields()} == {kind}
    if kind == "linear":
        row = constraint.linear
        assert row.vars and all(j >= 0 for j in row.vars)
        expression = cp_model.LinearExpr.weighted_sum([variables[j] for j in row.vars], list(row.coeffs))
        model.add_linear_expression_in_domain(expression, cp_model.Domain.from_flat_intervals(list(row.domain)))
    elif kind == "int_prod":
        row = constraint.int_prod
        assert len(row.exprs) == 2
        model.add_multiplication_equality(variables[single_variable(row.target)],
                                          [variables[single_variable(e)] for e in row.exprs])
    else:
        assert kind == "table"
        columns, tuples = table_data(constraint)
        model.add_allowed_assignments([variables[j] for j in columns], tuples)


def build_native(target, row_ids):
    assert len(row_ids) == len(set(row_ids)) and all(0 <= i < len(target.constraints) for i in row_ids)
    model = cp_model.CpModel()
    variables = [model.new_int_var_from_domain(cp_model.Domain.from_flat_intervals(list(v.domain)), v.name)
                 for v in target.variables]
    assert [v.index for v in variables] == list(range(len(target.variables)))
    for i in row_ids:
        append_constraint(model, variables, target.constraints[i])
    assert model.validate() == ""
    return model


def exact_proto_check(proto, target, row_ids):
    assert {f.name for f, _ in proto.ListFields()} == {"variables", "constraints"}
    assert len(proto.variables) == len(target.variables) and len(proto.constraints) == len(row_ids)
    assert list(proto.variables) == list(target.variables)
    assert all(actual == target.constraints[i] for actual, i in zip(proto.constraints, row_ids))
    census, terms, largest = Counter(), 0, 0
    magnitude = [max(abs(v.domain[0]), abs(v.domain[-1])) for v in proto.variables]
    for constraint in proto.constraints:
        kind = constraint.WhichOneof("constraint")
        census[kind] += 1
        if kind == "linear":
            row = constraint.linear
            assert len(row.vars) == len(row.coeffs) == len(set(row.vars))
            bound = sum(abs(c) * magnitude[j] for j, c in zip(row.vars, row.coeffs))
            assert bound < 1 << 62
            assert all(-(1 << 63) <= v < (1 << 63) for v in list(row.coeffs) + list(row.domain))
            largest = max(largest, bound)
            terms += len(row.vars)
        elif kind == "int_prod":
            factors = [single_variable(e) for e in constraint.int_prod.exprs]
            assert len(factors) == 2 and magnitude[factors[0]] * magnitude[factors[1]] < 1 << 62
        else:
            assert kind == "table"
            table_data(constraint)
    return {"variables": len(proto.variables), "constraints": len(proto.constraints),
            "constraint_types": dict(census), "linear_terms": terms,
            "maximum_linear_absolute_box_sum": largest,
            "all_row_coefficients_endpoints_and_product_domains_fit_signed64": True,
            "every_variable_and_constraint_compared_exactly": True,
            "objective_hints_assumptions_enforcements_or_strategy_added": False}


def selected_proto(target, row_ids):
    result = cp_model_pb2.CpModelProto()
    result.variables.extend(target.variables)
    for i in row_ids:
        result.constraints.add().CopyFrom(target.constraints[i])
    return result


def pool_scan(point, target, plan):
    assert len(point) == VARIABLES and all(type(v) is int for v in point)
    violations = []
    for record in plan["external_pool"]:
        row = target.constraints[record["target_constraint"]].linear
        assert len(row.domain) == 2
        value = sum(c * point[j] for j, c in zip(row.vars, row.coeffs))
        lo, hi = row.domain
        if value < lo or value > hi:
            violations.append({"pool_id": record["pool_id"], "target_constraint": record["target_constraint"],
                               "parent_constraint": record["parent_constraint"], "family": record["family"],
                               "value": value, "lower": lo, "upper": hi, "gap": max(lo - value, value - hi)})
    return violations


def inspect(point, data, plan, target):
    assert len(point) == VARIABLES and all(type(v) is int for v in point)
    assert parent.evaluate_proto(target, point)
    assert not pool_scan(point, target, plan)
    assert parent.evaluate_proto(data["parent_proto"], point)
    restored = parent.inspect(point, parent.read_inputs())
    return {"status": "PASS: full target and restored original parent exact integer count witness",
            "full_target_constraints_checked": TARGET_CONSTRAINTS,
            "all117_external_rows_checked": True, "all18444_exact_domains_checked": True,
            "all3288_products_checked": True, "all44_retained_tables_checked": True,
            "restored_original_parent_constraints_checked": OLD_CONSTRAINTS,
            "restored_parent_check": restored,
            "count_witness_only": True, "literal_incidence_graph_or_full_PSD_claimed": False}


def controls():
    toy = cp_model.CpModel()
    a = toy.new_int_var(-2, 2, "a")
    b = toy.new_int_var(-1, 3, "b")
    t = toy.new_int_var(-6, 6, "t")
    s = toy.new_int_var(0, 4, "s")
    toy.add(3 * a - 2 * b <= 1)
    toy.add_multiplication_equality(t, [a, b])
    toy.add_multiplication_equality(s, [a, a])
    allowed = [(-2, 0), (-2, 3), (0, 0), (0, 1), (2, 1), (2, 3)]
    toy.add_allowed_assignments([a, b], allowed)
    proto = cp_model_pb2.CpModelProto()
    text_format.Parse(str(toy.proto), proto)
    tables = [(3, [0, 1], allowed)]
    products = [(1, 2, [0, 1]), (2, 3, [0, 0])]
    domains, _, proofs = project_domains(proto, tables, products)
    assert proofs[1]["all_factor_products"] == [0, 4]
    projected = cp_model_pb2.CpModelProto()
    projected.CopyFrom(proto)
    for v, domain in zip(projected.variables, domains):
        del v.domain[:]
        v.domain.extend(domain)
    native = build_native(projected, list(range(4)))
    back = cp_model_pb2.CpModelProto()
    text_format.Parse(str(native.proto), back)
    exact_proto_check(back, projected, list(range(4)))
    assignments, accepted = 0, 0
    for point in itertools.product(range(-2, 3), range(-1, 4), range(-6, 7), range(5)):
        direct = (3 * point[0] - 2 * point[1] <= 1 and point[2] == point[0] * point[1]
                  and point[3] == point[0] ** 2 and tuple(point[:2]) in allowed)
        assert parent.evaluate_proto(proto, point) == direct
        assert parent.evaluate_proto(projected, point) == direct
        assert parent.evaluate_proto(back, point) == direct
        assignments += 1
        accepted += direct
    assert accepted > 0
    return {"status": "PASS", "signed_product_square_table_and_domain_assignments": assignments,
            "feasible_assignments": accepted, "public_constructor_transcription_checked": True,
            "integer_domain_holes_and_negative_values_checked": True,
            "optimizer_calls": 0, "CpSolver_constructed": False}


def prepare(directory):
    started = time.monotonic()
    directory.mkdir(parents=True, exist_ok=False)
    data = load_inputs()
    plan, target = derive(data)
    plan_file = save_new(directory / "plan.json.gz", plan)
    records = {}
    for name, row_ids in (("target", list(range(TARGET_CONSTRAINTS))), ("initial", plan["initial_to_target_rows"])):
        model = build_native(target, row_ids)
        path = directory / (name + ".pb")
        assert model.export_to_file(str(path))
        raw = path.read_bytes()
        proto = cp_model_pb2.CpModelProto()
        proto.ParseFromString(raw)
        checked = exact_proto_check(proto, target, row_ids)
        archive = directory / (name + ".pb.gz")
        with archive.open("xb") as stream:
            stream.write(gzip.compress(raw, mtime=0))
        records[name] = {"raw_proto_sha256": sha(raw), "raw_proto_bytes": len(raw),
                         "archive": {"path": str(archive.relative_to(ROOT)), "sha256": sha(archive.read_bytes()), "bytes": archive.stat().st_size},
                         "checks": checked, "native_validation": ""}
        del model, proto
    control = controls()
    report = {"status": "PASS: full target and initial external-row model prepared; no optimizer",
              "source_sha256": sha(Path(__file__).read_bytes()), "plan": plan_file,
              "parent_proto_sha256": PARENT_PROTO_SHA, "models": records,
              "domain_summary": plan["domain_summary"], "omitted_implied_basic_tables": 42,
              "retained_refined_tables": 42, "new_joint_tables": 2,
              "common_phase_normalization_rows": 2, "first_joint_table_tuples_after_phase": 44,
              "coupled_census_count_domains": 46,
              "external_dense_rows": 117, "full_target_retains_all_dense_rows": True,
              "controls": control, "ortools_version": ortools.__version__,
              "installed_cp_model_source_sha256": CP_MODEL_SHA,
              "optimizer_calls": 0, "CpSolver_constructed": False,
              "count_or_graph_feasibility_claimed": False, "seconds": time.monotonic() - started}
    save_new(directory / "report.json", report)
    return report


def replay(directory, output):
    started = time.monotonic()
    report_raw = (directory / "report.json").read_bytes()
    report = json.loads(report_raw)
    assert report["source_sha256"] == sha(Path(__file__).read_bytes())
    data = load_inputs()
    plan, target = derive(data)
    raw = (ROOT / report["plan"]["path"]).read_bytes()
    assert sha(raw) == report["plan"]["sha256"]
    assert json.loads(gzip.decompress(raw)) == plan
    checked = {}
    for name, row_ids in (("target", list(range(TARGET_CONSTRAINTS))), ("initial", plan["initial_to_target_rows"])):
        info = report["models"][name]
        archive = (ROOT / info["archive"]["path"]).read_bytes()
        assert sha(archive) == info["archive"]["sha256"]
        raw = gzip.decompress(archive)
        assert sha(raw) == info["raw_proto_sha256"] and len(raw) == info["raw_proto_bytes"]
        proto = cp_model_pb2.CpModelProto()
        proto.ParseFromString(raw)
        checked[name] = exact_proto_check(proto, target, row_ids)
        assert checked[name] == info["checks"]
    result = {"status": "PASS: cold exact domain, omission, row-map and native coefficient replay",
              "source_sha256": sha(Path(__file__).read_bytes()), "preparation_sha256": sha(report_raw),
              "plan_sha256": report["plan"]["sha256"], "models": checked,
              "parent_complete_cold_bound": INPUTS["parent_cold"][1],
              "old_proof_censuses_or_solver_calls_repeated": False,
              "controls_repeated": False, "optimizer_calls": 0, "CpSolver_constructed": False,
              "seconds": time.monotonic() - started}
    save_new(output, result)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "replay"))
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.mode == "prepare":
        result = prepare(args.directory.resolve())
    else:
        assert args.output is not None
        result = replay(args.directory.resolve(), args.output.resolve())
    print(json.dumps(result, indent=2), flush=True)
