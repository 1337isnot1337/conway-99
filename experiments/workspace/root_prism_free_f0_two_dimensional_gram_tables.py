"""Exact small Gram tables for three saved A2 vector domains.

Preparation runs only fixed arithmetic controls. Enumeration and cold replay
are separate bounded modes. This source never builds a native model or
tests a production count assignment.
"""
import argparse
from collections import Counter
from hashlib import sha256
from itertools import combinations, islice, product
import json
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "experiments/logs/root-prism-free"
DOMAIN_SOURCE = ("root_prism_free_f0_two_dimensional_vector_domains.py", "0b2d15c2d331466acbc29b3585bec4c53de5a912424c9d50b179e5ed37d15660")
DOMAIN_RECORD = ("f0-two-dimensional-vector-domains-preparation01.json", "571b52265dc70a9e5992750d05ab0928364a68fa650716734bd3727728e135c1")
ENTRY_ORDER = [[0, 0], [0, 1], [0, 2], [1, 1], [1, 2], [2, 2]]
LIMITS = {"seconds_per_stage": 30, "maximum_raw_record_bytes": 4 << 20,
          "maximum_pair_combinations": 1083, "maximum_triple_combinations": 6859,
          "new_selector_subset_censuses": 0, "optimizer_calls": 0}


def sha(raw):
    return sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def tick(deadline):
    if time.monotonic() >= deadline:
        raise TimeoutError("small Gram-table stage deadline")


def norm(v):
    a, b = v
    return 2*(a*a-a*b+b*b)


def inner(u, v):
    return 2*u[0]*v[0]-u[0]*v[1]-u[1]*v[0]+2*u[1]*v[1]


def polar(u, v):
    numerator = norm([u[0]+v[0], u[1]+v[1]])-norm(u)-norm(v)
    assert numerator % 2 == 0
    return numerator//2


def det3(t):
    a, b, c, d, e, f = t
    return a*d*f+2*b*c*e-a*e*e-d*c*c-f*b*b


def load_domains():
    assert sha((ROOT/"experiments/workspace"/DOMAIN_SOURCE[0]).read_bytes()) == DOMAIN_SOURCE[1]
    raw = (BASE/DOMAIN_RECORD[0]).read_bytes()
    assert sha(raw) == DOMAIN_RECORD[1]
    record = json.loads(raw)
    assert record["source_sha256"] == DOMAIN_SOURCE[1]
    assert record["status"] == "COMPLETE_VECTOR_DOMAIN_PREPARATION"
    for name, expected in record["inputs"].values():
        assert sha((BASE/name).read_bytes()) == expected
    source_name, expected = record["scope_source"]
    assert sha((ROOT/"experiments/workspace"/source_name).read_bytes()) == expected
    assert record["H"] == [[2, -1], [-1, 2]] and record["selector_orbits"] == [2, 3, 4]
    assert record["six_entry_order"] == ENTRY_ORDER
    expected_vectors = [[a, b] for a in range(-2, 3) for b in range(-2, 3)
                        if max(0, a, b)-min(0, a, b) <= 2]
    assert len(expected_vectors) == 19
    for domain in record["domains"]:
        assert domain["vectors"] == expected_vectors
        assert domain["complete_saved_mask_count"] == 729 and domain["profile_count"] == 237
        assert sum(domain["vector_literal_multiplicities"]) == 729
    assert record["future_pair_combinations"] == LIMITS["maximum_pair_combinations"]
    assert record["future_triple_combinations"] == LIMITS["maximum_triple_combinations"]
    return record


def controls():
    samples = [([0, 0], [2, 1]), ([1, 0], [1, 1]), ([1, -1], [1, 2]), ([-2, -2], [2, 0])]
    for u, v in samples:
        a, b, c = norm(u), inner(u, v), norm(v)
        assert b == polar(u, v)
        assert a*c-b*b == 3*(u[0]*v[1]-u[1]*v[0])**2
    assert (norm([1, 0]), inner([1, 0], [1, 1]), norm([1, 1])) == (2, 1, 2)
    assert det3([2, 1, 1, 2, 1, 2]) == 4
    assert 36 % 3 == 0 and 3**2 < 36//3 < 4**2
    return {"fixed_vector_pairs": len(samples), "norm_polarization_checked": True,
            "pairwise_Gram_example": [2, 1, 2], "rank_three_test_tuple": [2, 1, 1, 2, 1, 2],
            "rank_three_test_determinant": 4, "norm_six_zero_cross_not_three_times_square": True,
            "production_vector_products_visited": 0}


def prepare(deadline):
    domain = load_domains()
    report = {"schema": "conway99.f0.small-Gram-table-preparation.v1", "status": "PREPARED_ONLY",
        "source_sha256": sha(Path(__file__).read_bytes()), "domain_source": DOMAIN_SOURCE,
        "domain_record": DOMAIN_RECORD, "limits": LIMITS, "controls": controls(),
        "pair_stage_columns": [[0, 1], [0, 2], [1, 2]], "joint_stage_columns": [0, 1, 2],
        "selector_orbits": [2, 3, 4], "vector_cardinalities": [19, 19, 19],
        "pair_combinations": 1083, "triple_combinations": 6859,
        "six_entry_order": ENTRY_ORDER, "six_native_entry_forms": domain["six_native_entry_forms"],
        "native_count_namespace": domain["native_count_namespace"],
        "integration": {"observable_names": ["B22", "B23", "B24", "B33", "B34", "B44"],
            "new_variable_ids_allocated": False, "observable_definition": "exact listed native linear count form; no divisor",
            "proposed_constraint": "one allowed table on the six observables in six_entry_order",
            "pair_tables": "exact projections for review; redundant if the joint table is imposed",
            "entry_domains": domain["future_entry_domains"],
            "requires_complete_result_and_cold_replay": True},
        "scope": {"actual_literal_assignment_or_common_group_orbit": True,
            "arbitrary_convex_mixtures": False, "cross_orbit_selector_conflicts_tested": False,
            "production_count_assignment_tested": False, "full_count_feasibility_claimed": False,
            "new_selector_subset_censuses": 0, "optimizer_calls": 0}}
    tick(deadline)
    return report


def load_preparation(path):
    raw = path.read_bytes()
    prep = json.loads(raw)
    assert prep["source_sha256"] == sha(Path(__file__).read_bytes())
    assert prep["status"] == "PREPARED_ONLY" and prep["limits"] == LIMITS
    assert prep["domain_source"] == list(DOMAIN_SOURCE) and prep["domain_record"] == list(DOMAIN_RECORD)
    domain = load_domains()
    assert prep["six_native_entry_forms"] == domain["six_native_entry_forms"]
    return prep, domain, sha(raw)


def collect_stage(vectors, columns, deadline):
    dimensions = [range(len(vectors[i])) for i in columns]
    expected = 1
    for dimension in dimensions:
        expected *= len(dimension)
    counts, first, visited = Counter(), {}, 0
    for choices in product(*dimensions):
        if visited % 64 == 0 and time.monotonic() >= deadline:
            break
        selected = [vectors[i][j] for i, j in zip(columns, choices)]
        if len(columns) == 2:
            u, v = selected
            row = (norm(u), inner(u, v), norm(v))
            assert row[0]*row[2]-row[1]**2 == 3*(u[0]*v[1]-u[1]*v[0])**2
        else:
            row = tuple(inner(selected[i], selected[j]) for i, j in ENTRY_ORDER)
            assert det3(row) == 0
        counts[row] += 1
        first.setdefault(row, list(choices))
        visited += 1
    rows = sorted(counts)
    return {"columns": columns, "expected_combinations": expected, "visited_combinations": visited,
            "complete": visited == expected, "tuples": [list(row) for row in rows],
            "first_vector_witness_indices": [first[row] for row in rows],
            "vector_combination_multiplicities": [counts[row] for row in rows]}


def enumerate_tables(prep_path, deadline):
    prep, domain, prep_sha = load_preparation(prep_path)
    vectors = [d["vectors"] for d in domain["domains"]]
    stages = []
    for columns in prep["pair_stage_columns"]+[prep["joint_stage_columns"]]:
        stage = collect_stage(vectors, columns, deadline)
        stages.append(stage)
        if not stage["complete"]:
            break
    complete = len(stages) == 4 and all(s["complete"] for s in stages)
    extra = {}
    if complete:
        joint = {tuple(t) for t in stages[3]["tuples"]}
        for stage, positions in zip(stages[:3], ([0, 1, 3], [0, 2, 5], [3, 4, 5])):
            assert {tuple(row[i] for i in positions) for row in joint} == {tuple(row) for row in stage["tuples"]}
        pair = {tuple(row) for row in stages[0]["tuples"]}
        assert (6, 0, 6) not in pair and (2, 1, 2) in pair
        assert (2, 1, 1, 2, 1, 2) not in joint
        extra = {"all_joint_pair_projections_equal_pair_tables": True,
                 "square_rejected_pair": [6, 0, 6],
                 "pairwise_allowed_but_joint_rank_rejected": [2, 1, 1, 2, 1, 2],
                 "joint_entry_values": [sorted({row[i] for row in joint}) for i in range(6)]}
    return {"schema": "conway99.f0.small-Gram-tables.v1",
        "status": "COMPLETE_EXACT_GRAM_TABLES" if complete else "INCOMPLETE_GRAM_TABLE_PREFIX",
        "source_sha256": sha(Path(__file__).read_bytes()), "preparation_sha256": prep_sha,
        "domain_record_sha256": DOMAIN_RECORD[1], "limits": LIMITS, "stages": stages,
        "complete": complete, "integration_requires_separate_cold_pass": True,
        "six_entry_order": ENTRY_ORDER, "selector_orbits": [2, 3, 4],
        "table_semantics": "all shared-frame Gram tuples of three independently attainable local vectors",
        "cross_orbit_selector_compatibility_tested": False, "new_selector_subset_censuses": 0,
        "production_count_candidate_checked": False, "optimizer_calls": 0, **extra}


def replay_tables(prep_path, result_path, deadline):
    prep, domain, prep_sha = load_preparation(prep_path)
    raw = result_path.read_bytes()
    result = json.loads(raw)
    assert result["source_sha256"] == sha(Path(__file__).read_bytes())
    assert result["preparation_sha256"] == prep_sha and result["domain_record_sha256"] == DOMAIN_RECORD[1]
    assert result["limits"] == LIMITS and result["six_entry_order"] == ENTRY_ORDER
    stages = result["stages"]
    assert 1 <= len(stages) <= 4 and all(s["complete"] for s in stages[:-1])
    vectors = [d["vectors"] for d in domain["domains"]]
    expected_columns = prep["pair_stage_columns"]+[prep["joint_stage_columns"]]
    visited_total = 0
    for stage, columns in zip(stages, expected_columns):
        assert stage["columns"] == columns
        dimensions = [range(len(vectors[i])) for i in columns]
        expected = 19**len(columns)
        count = stage["visited_combinations"]
        assert stage["expected_combinations"] == expected and 0 <= count <= expected
        assert stage["complete"] == (count == expected)
        observed, witnesses = Counter(), {}
        # Fresh polarization contractions; do not call the producer's inner function.
        for ordinal, choices in enumerate(islice(product(*dimensions), count)):
            if ordinal % 64 == 0:
                tick(deadline)
            selected = [vectors[i][j] for i, j in zip(columns, choices)]
            positions = [[0, 0], [0, 1], [1, 1]] if len(columns) == 2 else ENTRY_ORDER
            row = tuple(polar(selected[i], selected[j]) for i, j in positions)
            observed[row] += 1
            witnesses.setdefault(row, list(choices))
        ordered = sorted(observed)
        assert stage["tuples"] == [list(t) for t in ordered]
        assert stage["first_vector_witness_indices"] == [witnesses[t] for t in ordered]
        assert stage["vector_combination_multiplicities"] == [observed[t] for t in ordered]
        visited_total += count
    complete = len(stages) == 4 and all(s["complete"] for s in stages)
    assert result["complete"] == complete
    assert result["status"] == ("COMPLETE_EXACT_GRAM_TABLES" if complete else "INCOMPLETE_GRAM_TABLE_PREFIX")
    if complete:
        assert visited_total == 1083+6859
        joint = {tuple(t) for t in stages[3]["tuples"]}
        for stage, ids in zip(stages[:3], ([0, 1, 3], [0, 2, 5], [3, 4, 5])):
            assert {tuple(t[i] for i in ids) for t in joint} == {tuple(t) for t in stage["tuples"]}
        assert all(det3(t) == 0 for t in joint)
        assert result["all_joint_pair_projections_equal_pair_tables"] is True
        assert result["joint_entry_values"] == [sorted({t[i] for t in joint}) for i in range(6)]
        assert result["square_rejected_pair"] == [6, 0, 6] and [6, 0, 6] not in stages[0]["tuples"]
        assert result["pairwise_allowed_but_joint_rank_rejected"] == [2, 1, 1, 2, 1, 2]
        assert [2, 1, 2] in stages[0]["tuples"] and (2, 1, 1, 2, 1, 2) not in joint
    tick(deadline)
    return {"schema": "conway99.f0.small-Gram-table-cold.v1", "status": "PASS: exact saved table prefix replay",
        "source_sha256": sha(Path(__file__).read_bytes()), "preparation_sha256": prep_sha,
        "result_sha256": sha(raw), "domain_record_sha256": DOMAIN_RECORD[1],
        "complete_full_table": complete, "saved_stages_replayed": len(stages),
        "fresh_integer_polarization_products": visited_total,
        "stage_distinct_tuple_counts": [len(s["tuples"]) for s in stages],
        "literal_inverse_preparation_repeated": False,
        "new_selector_subset_censuses": 0, "production_count_candidate_checked": False, "optimizer_calls": 0}


def main():
    if not __debug__:
        raise RuntimeError("assertions must remain enabled")
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["prepare", "enumerate", "replay"])
    parser.add_argument("--preparation", type=Path)
    parser.add_argument("--result", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists(), "preserve frozen artifacts"
    start = time.monotonic()
    deadline = start+LIMITS["seconds_per_stage"]
    try:
        if args.mode == "prepare":
            record = prepare(deadline)
        elif args.mode == "enumerate":
            assert args.preparation and not args.result
            record = enumerate_tables(args.preparation, deadline)
        else:
            assert args.preparation and args.result
            record = replay_tables(args.preparation, args.result, deadline)
    except Exception as exc:
        record = {"status": "FAILED_STAGE", "mode": args.mode,
                  "source_sha256": sha(Path(__file__).read_bytes()),
                  "error": type(exc).__name__+": "+str(exc), "complete": False, "optimizer_calls": 0}
    record["seconds"] = time.monotonic()-start
    raw = canonical(record)+b"\n"
    assert len(raw) <= LIMITS["maximum_raw_record_bytes"]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("xb") as out:
        out.write(raw)
    print(json.dumps({"status": record["status"], "record_sha256": sha(raw), "bytes": len(raw),
                      "seconds": record["seconds"],
                      "stage_distinct_tuple_counts": [len(s["tuples"]) for s in record.get("stages", [])]}))
    if record["status"] in ("FAILED_STAGE", "INCOMPLETE_GRAM_TABLE_PREFIX"):
        raise SystemExit(2)


if __name__ == "__main__":
    main()
