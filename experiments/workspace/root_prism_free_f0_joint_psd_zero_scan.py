"""Joint PSD scan with certified-zero row filtering and gap-size metadata.

The frozen domain/kernel cache is reused unchanged. Only this preparation's
current-row index is rebuilt, after substituting the162 explicit Y zeros.
All cuts still come from the reviewed literal PSD constructors. No optimizer
is called. Numerical size labels never establish redundancy or feasibility.
"""
import argparse
from collections import Counter
from fractions import Fraction
from itertools import product
import json
import math
from pathlib import Path
import time

import root_prism_free_f0_joint_psd_scan as base

ROOT, LOGS = base.ROOT, base.LOGS
PARENT_SHA = "7441635b50e19846e48261614daf0a69a605cce8d32a15cd90f7a4cbafc1ce73"
PARENT_INPUTS = {
    "preparation": ("f0-joint-psd-preparation03.json", "94a4b20c380836c4e430d1a551c55a547c03c6a119680d74e73723193112082e"),
    "cache": ("f0-joint-psd-cache01.json.gz", "6d293340386e77e0bf0b0a7b006744523d75eb7e90ef0fd371c3eed5eb82801e"),
    "cold": ("f0-joint-psd-preparation03-cold-replay.json", "e0c8e127ff72714705d7c178b4418e30c5f2cad50bed992a8a8d97b38145a2b4"),
}
TINY_RELATIVE = Fraction(1, 10**10)
sha, canonical, save_new, load_json = base.sha, base.canonical, base.save_new, base.load_json


def bindings():
    assert sha(Path(base.__file__).read_bytes()) == PARENT_SHA
    return {"source_sha256": sha(Path(__file__).read_bytes()), "parent_source_sha256": PARENT_SHA,
            "parent_inputs": {k: list(v) for k, v in PARENT_INPUTS.items()},
            "base_bindings": base.bindings(), "relative_size_label_threshold": str(TINY_RELATIVE)}


def load_parent():
    bindings()
    for key, (name, expected) in PARENT_INPUTS.items():
        assert sha((LOGS/name).read_bytes()) == expected, key
    cold = load_json(LOGS/PARENT_INPUTS["cold"][0])
    assert cold["status"].startswith("PASS") and cold["source_sha256"] == PARENT_SHA
    assert cold["preparation_sha256"] == PARENT_INPUTS["preparation"][1]
    return base.load_prepared(LOGS/PARENT_INPUTS["preparation"][0], LOGS/PARENT_INPUTS["cache"][0])


def project_row(row, zeros):
    terms = [[j, c] for j, c in row["terms"] if j not in zeros]
    divisor = math.gcd(abs(row["rhs"]), *(abs(c) for j, c in terms)) or 1
    answer = base.normalized_row({"terms": terms, "rhs": row["rhs"]})
    assert answer == {"terms": [[j, c//divisor] for j, c in terms], "rhs": row["rhs"]//divisor}
    return answer, divisor


def filter_preparation():
    model = base.read_input("model")
    assert sha(canonical(model)) == base.MODEL_SHA
    matrix = model["matrix"]
    assert sha(canonical(matrix)) == base.MATRIX_SHA
    witnesses = []
    for index, row in enumerate(matrix["equalities"]):
        if row["rhs"] == 0 and len(row["terms"]) == 1:
            j, c = row["terms"][0]
            assert type(c) is int and c
            witnesses.append({"variable": j, "equality_row": index, "coefficient": c})
    zeros = sorted({w["variable"] for w in witnesses})
    assert len(zeros) == 162 and all(42 <= j < base.PAIR_OFFSET for j in zeros)
    zero_set, indexed = set(zeros), {}
    for kind in ("equalities", "inequalities"):
        for index, row in enumerate(matrix[kind]):
            for sign in ((1, -1) if kind == "equalities" else (1,)):
                oriented = {"terms": [[j, sign*c] for j, c in row["terms"]], "rhs": sign*row["rhs"]}
                projected, divisor = project_row(oriented, zero_set)
                indexed.setdefault(base.row_key(projected), []).append([kind, index, sign])
    rows = [[key, indexed[key]] for key in sorted(indexed)]
    return {"schema": "f0-joint-psd-zero-filter-v1", "bindings": bindings(),
            "certified_zero_variables": zeros, "single_coordinate_equality_witnesses": witnesses,
            "existing_rows_after_zero_substitution": rows,
            "existing_rows_sha256": sha(canonical(rows)),
            "oriented_parent_row_origins": sum(len(v) for k, v in rows),
            "existing_primitive_rows_after_zero_substitution": len(rows),
            "domain_or_kernel_reconstruction_performed": False}


def projected_evaluation(certificate, zeros, denominator, numerators, literal_check):
    original = certificate["row"]
    row, divisor = project_row(original, zeros)
    gap = sum(c*numerators[j] for j, c in row["terms"])-row["rhs"]*denominator
    removed = sum(c*numerators[j] for j, c in original["terms"] if j in zeros)
    assert int(literal_check["gap_numerator"]) == divisor*gap+removed
    return row, {"violated": gap > 0, "gap_numerator": str(gap), "denominator": str(denominator),
                 "positive_projection_divisor": divisor, "removed_zero_term_numerator": str(removed),
                 "certified_zero_substitutions": len(zeros), "proposal_zero_values_assumed": False}


def classify(row, literal_check, projected_check, existing, seen):
    key = base.row_key(row)
    if not literal_check["violated"]:
        return "NONPOSITIVE_LITERAL_GAP", key
    if not projected_check["violated"]:
        return "NONPOSITIVE_GAP_AFTER_CERTIFIED_ZEROS", key
    if base.unit_box_implied(row):
        return "UNIT_BOX_IMPLIED_AFTER_ZEROS", key
    if key in existing:
        return "EXISTING_ROW_AFTER_ZEROS", key
    if key in seen:
        return "DUPLICATE_NEW_ROW_AFTER_ZEROS", key
    return "RETAIN", key


def significance(row, projected_check, eigenvalue, matrix_norm):
    gap = Fraction(int(projected_check["gap_numerator"]), int(projected_check["denominator"]))
    size = max(1, abs(row["rhs"])+sum(abs(c) for j, c in row["terms"]))
    relative = gap/size
    tolerance = float(TINY_RELATIVE)*max(1.0, matrix_norm)
    return {"exact_absolute_gap": str(gap), "unit_box_coefficient_norm": size,
            "relative_row_gap_exact": str(relative), "relative_gap_at_most_1e_minus10": relative <= TINY_RELATIVE,
            "numerical_direction_eigenvalue_hex": float(eigenvalue).hex(),
            "numerical_matrix_infinity_norm_hex": float(matrix_norm).hex(),
            "numerical_zero_scale_tolerance_hex": tolerance.hex(),
            "numerically_significant_negative_direction": eigenvalue < -tolerance,
            "large_gap_and_direction_heuristic": relative > TINY_RELATIVE and eigenvalue < -tolerance,
            "strict_strength_or_nonredundancy_proved": False,
            "size_labels_are_heuristics_only": True}


def controls():
    checks = 0
    for coefficients in product(range(-2, 3), repeat=3):
        for rhs in (-1, 0, 1):
            original = {"terms": [[j, c] for j, c in enumerate(coefficients) if c], "rhs": rhs}
            row, divisor = project_row(original, {1})
            for a, c in product((0, 1), repeat=2):
                point = [a, 0, c]
                lhs = sum(v*point[j] for j, v in original["terms"])
                projected = sum(v*point[j] for j, v in row["terms"])
                assert lhs-rhs == divisor*(projected-row["rhs"])
                checks += 1
    row = {"terms": [[0, 6], [1, -15], [2, -12]], "rhs": 0}
    projected, divisor = project_row(row, {1})
    assert projected == {"terms": [[0, 1], [2, -2]], "rhs": 0} and divisor == 6
    nums = [4, 1, 1]
    literal = {"violated": False, "gap_numerator": "-3"}
    answer, check = projected_evaluation({"row": row}, {1}, 8, nums, literal)
    assert answer == projected and check["gap_numerator"] == "2"
    assert classify(projected, literal, check, {}, {})[0] == "NONPOSITIVE_LITERAL_GAP"
    assert base.row_key(projected) == base.row_key({"terms": [[0, 3], [2, -6]], "rhs": 0})
    large = significance(projected, {"gap_numerator": "1", "denominator": "1"}, -1.0, 1.0)
    tiny = significance(projected, {"gap_numerator": "1", "denominator": str(10**16)}, -1e-16, 1.0)
    assert large["large_gap_and_direction_heuristic"] and not tiny["large_gap_and_direction_heuristic"]
    return {"status": "PASS: exact zero substitution, positive gcd, residual identity and labels",
            "literal_boolean_equivalences": checks, "nonzero_proposal_zero_coordinate_control": True,
            "numerical_size_labels_do_not_establish_redundancy": True, "eigendecompositions": 0, "optimizer_calls": 0}


def prepare(filter_path):
    parent, cache, domain, kernels = load_parent()
    filtered = filter_preparation()
    tested = controls()
    save_new(filter_path, filtered)
    return {"status": "PASS: certified-zero adapter prepared; parent domain/cache unchanged",
            **bindings(), "limits": base.limits(), "filter_file_sha256": sha(Path(filter_path).read_bytes()),
            "filter_canonical_sha256": sha(canonical(filtered)), "controls": tested,
            "parent_controls_reused_sha256": sha(canonical(parent["controls"])),
            "certified_zero_variables": len(filtered["certified_zero_variables"]),
            "existing_primitive_rows_after_zero_substitution": filtered["existing_primitive_rows_after_zero_substitution"],
            "oriented_parent_row_origins": filtered["oriented_parent_row_origins"],
            "domain_or_kernel_reconstruction_performed": False, "eigendecompositions": 0, "optimizer_calls": 0}


def load_prepared(preparation_path, filter_path):
    parent, cache, domain, kernels = load_parent()
    prepared, filtered = load_json(preparation_path), load_json(filter_path)
    bound = bindings()
    assert all(prepared[k] == v for k, v in bound.items()) and filtered["bindings"] == bound
    assert prepared["limits"] == base.limits()
    assert prepared["filter_file_sha256"] == sha(Path(filter_path).read_bytes())
    assert prepared["filter_canonical_sha256"] == sha(canonical(filtered))
    assert prepared["parent_controls_reused_sha256"] == sha(canonical(parent["controls"]))
    return prepared, filtered, domain, kernels


def scan(preparation_path, filter_path, output_path, seconds):
    assert 0 < seconds <= base.SCAN_SECONDS and not Path(output_path).exists()
    started = time.monotonic()
    deadline = started+seconds
    result = {"status": "RUNNING", **bindings(), "limits": base.limits(),
        "preparation_sha256": sha(Path(preparation_path).read_bytes()), "requested_seconds": seconds,
        "families": [], "attempts": [], "cuts": [], "eigendecompositions": 0, "optimizer_calls": 0,
        "proposal_feasibility_claimed": False, "PSD_feasibility_claimed": False}
    base.schur.atomic_result(output_path, result)
    try:
        prepared, filtered, domain, kernels = load_prepared(preparation_path, filter_path)
        denominator, numerators, values = base.proposal()
        result["proposal_common_denominator"] = str(denominator)
        zeros = set(filtered["certified_zero_variables"])
        existing, seen = dict(filtered["existing_rows_after_zero_substitution"]), {}
        import numpy as np
        from threadpoolctl import threadpool_limits
        for family in base.FAMILIES:
            base.tick(deadline)
            record = {"family": family, "status": "RUNNING", "directions": [], "retained_cuts": 0}
            result["families"].append(record)
            floating = base.matrix(np, domain, kernels, family, values)
            norm = float(np.max(np.sum(np.abs(floating), axis=1)))
            tolerance = float(TINY_RELATIVE)*max(1.0, norm)
            base.tick(deadline)
            with threadpool_limits(limits=1):
                eigenvalues, eigenvectors = np.linalg.eigh(floating)
            result["eigendecompositions"] += 1
            assert np.isfinite(eigenvalues).all() and np.isfinite(eigenvectors).all() and math.isfinite(norm)
            record.update({"minimum_eigenvalue_hex": float(eigenvalues[0]).hex(),
                "matrix_infinity_norm_hex": norm.hex(), "zero_scale_tolerance_hex": tolerance.hex(),
                "numerical_negative_eigenvalues": int(np.count_nonzero(eigenvalues < 0)),
                "numerically_significant_negative_eigenvalues": int(np.count_nonzero(eigenvalues < -tolerance)),
                "minimum_is_numerical_zero_scale": abs(eigenvalues[0]) <= tolerance})
            for index in range(base.DIRECTIONS):
                base.tick(deadline)
                direction = eigenvectors[:, index]
                record["directions"].append({"index": index, "eigenvalue_hex": float(eigenvalues[index]).hex(),
                    "vector_hex": [float(v).hex() for v in direction]})
                direction = direction/np.max(np.abs(direction))
                for scale in base.SCALES:
                    base.tick(deadline)
                    vector = [int(v) for v in np.rint(direction*scale)]
                    certificate = base.make_cut(domain, kernels, family, vector)
                    literal = base.evaluate(domain, kernels, family, certificate, denominator, numerators)
                    row, projected = projected_evaluation(certificate, zeros, denominator, numerators, literal)
                    decision, key = classify(row, literal, projected, existing, seen)
                    attempt = {"family": family, "direction_index": index, "scale": scale,
                        "vector": certificate["vector"], "projected_row_sha256": key,
                        "literal_evaluation": literal, "projected_evaluation": projected, "disposition": decision}
                    if decision == "RETAIN":
                        assert record["retained_cuts"] < base.PER_FAMILY and len(result["cuts"]) < base.TOTAL_CUTS
                        attempt["retained_index"] = len(result["cuts"])
                        seen[key] = len(result["cuts"])
                        result["cuts"].append({"family": family, "certificate": certificate, "row": row,
                            "literal_evaluation": literal, "projected_evaluation": projected,
                            "direction_index": index, "scale": scale,
                            "numerical_row_rule": base.numerical_row_rule(row),
                            "significance": significance(row, projected, float(eigenvalues[index]), norm)})
                        record["retained_cuts"] += 1
                    elif decision == "EXISTING_ROW_AFTER_ZEROS":
                        attempt["existing_origins"] = existing[key]
                    elif decision == "DUPLICATE_NEW_ROW_AFTER_ZEROS":
                        attempt["duplicate_of"] = seen[key]
                    result["attempts"].append(attempt)
                    if record["retained_cuts"] == base.PER_FAMILY:
                        break
                base.schur.atomic_result(output_path, result)
                if record["retained_cuts"] == base.PER_FAMILY:
                    break
            record["status"] = "CUT_LIMIT" if record["retained_cuts"] == base.PER_FAMILY else "COMPLETE_DIRECTIONS"
            base.schur.atomic_result(output_path, result)
        result["status"] = "EXACT_NEW_CUTS" if result["cuts"] else "NO_RETAINED_NEW_SEPARATOR"
    except TimeoutError as exc:
        result["status"], result["message"] = "TIME_LIMIT_PARTIAL", str(exc)
    except Exception as exc:
        result["status"], result["message"] = "ERROR", repr(exc)
        raise
    finally:
        result["elapsed_seconds"] = time.monotonic()-started
        result["cooperative_overrun_seconds"] = max(0, result["elapsed_seconds"]-seconds)
        result["disposition_counts"] = dict(Counter(a["disposition"] for a in result["attempts"]))
        result["complete_direction_coverage"] = (len(result["families"]) == 3 and
            all(f["status"] == "COMPLETE_DIRECTIONS" for f in result["families"]))
        result["large_gap_and_direction_heuristic_cuts"] = sum(c["significance"]["large_gap_and_direction_heuristic"] for c in result["cuts"])
        result["no_cut_implies_PSD"] = False
        result["scope"] = "Exact necessary new rows only; size labels are heuristic. No exact feasible point or component exclusion."
        base.schur.atomic_result(output_path, result)
    return result


def replay(preparation_path, filter_path, result_path):
    started = time.monotonic()
    prepared, filtered, domain, kernels = load_prepared(preparation_path, filter_path)
    result = load_json(result_path)
    assert result["status"] not in ("RUNNING", "ERROR") and result["optimizer_calls"] == 0
    assert all(result[k] == v for k, v in bindings().items())
    assert result["preparation_sha256"] == sha(Path(preparation_path).read_bytes())
    assert result["limits"] == base.limits() and result["eigendecompositions"] <= 3
    assert len(result["cuts"]) <= base.TOTAL_CUTS and len(result["attempts"]) <= 3*base.DIRECTIONS*len(base.SCALES)
    assert [f["family"] for f in result["families"]] == list(base.FAMILIES[:len(result["families"])])
    denominator, numerators, values = base.proposal()
    if "proposal_common_denominator" in result:
        assert result["proposal_common_denominator"] == str(denominator)
    zeros, existing = set(filtered["certified_zero_variables"]), dict(filtered["existing_rows_after_zero_substitution"])
    seen, counts, positions = {}, Counter(), set()
    family_records = {f["family"]: f for f in result["families"]}
    for attempt in result["attempts"]:
        family, index, scale = attempt["family"], attempt["direction_index"], attempt["scale"]
        assert family in family_records and scale in base.SCALES and 0 <= index < base.DIRECTIONS
        assert (family, index, scale) not in positions
        positions.add((family, index, scale))
        record = family_records[family]
        direction = record["directions"][index]
        assert direction["index"] == index
        raw = [float.fromhex(v) for v in direction["vector_hex"]]
        assert len(raw) == base.N+int(family == "selector") and all(math.isfinite(v) for v in raw)
        largest = max(map(abs, raw))
        assert largest > 0
        proposed = [round(v/largest*scale) for v in raw]
        certificate = base.make_cut(domain, kernels, family, proposed)
        assert certificate["vector"] == attempt["vector"]
        literal = base.evaluate(domain, kernels, family, certificate, denominator, numerators)
        row, projected = projected_evaluation(certificate, zeros, denominator, numerators, literal)
        decision, key = classify(row, literal, projected, existing, seen)
        assert decision == attempt["disposition"] and key == attempt["projected_row_sha256"]
        assert literal == attempt["literal_evaluation"] and projected == attempt["projected_evaluation"]
        if decision == "RETAIN":
            at = len(seen)
            assert attempt["retained_index"] == at and counts[family] < base.PER_FAMILY
            expected = {"family": family, "certificate": certificate, "row": row,
                "literal_evaluation": literal, "projected_evaluation": projected,
                "direction_index": index, "scale": scale, "numerical_row_rule": base.numerical_row_rule(row),
                "significance": significance(row, projected, float.fromhex(direction["eigenvalue_hex"]),
                                              float.fromhex(record["matrix_infinity_norm_hex"]))}
            assert result["cuts"][at] == expected
            seen[key] = at
            counts[family] += 1
        elif decision == "EXISTING_ROW_AFTER_ZEROS":
            assert attempt["existing_origins"] == existing[key]
        elif decision == "DUPLICATE_NEW_ROW_AFTER_ZEROS":
            assert attempt["duplicate_of"] == seen[key]
        if decision != "RETAIN":
            assert "retained_index" not in attempt
    assert len(seen) == len(result["cuts"])
    assert result["disposition_counts"] == dict(Counter(a["disposition"] for a in result["attempts"]))
    for record in result["families"]:
        assert record["retained_cuts"] == counts[record["family"]] and len(record["directions"]) <= base.DIRECTIONS
    assert result["large_gap_and_direction_heuristic_cuts"] == sum(c["significance"]["large_gap_and_direction_heuristic"] for c in result["cuts"])
    return {"status": "PASS: zero-projected PSD inequalities, all recorded gaps and dispositions replayed",
            **bindings(), "result_sha256": sha(Path(result_path).read_bytes()),
            "retained_cuts": len(seen), "family_counts": {f: counts[f] for f in base.FAMILIES},
            "attempts": len(result["attempts"]), "large_gap_and_direction_heuristic_cuts": result["large_gap_and_direction_heuristic_cuts"],
            "domain_or_kernel_reconstruction_performed": False, "eigendecompositions": 0, "optimizer_calls": 0,
            "proposal_feasibility_claimed": False, "seconds": time.monotonic()-started}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "replay-preparation", "scan", "replay"))
    parser.add_argument("--filter", type=Path, required=True)
    parser.add_argument("--preparation", type=Path)
    parser.add_argument("--result", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seconds", type=float, default=base.SCAN_SECONDS)
    args = parser.parse_args()
    if args.mode == "prepare":
        result = prepare(args.filter)
        save_new(args.output, result)
    elif args.mode == "replay-preparation":
        prepared, filtered, domain, kernels = load_prepared(args.preparation, args.filter)
        assert filter_preparation() == filtered and controls() == prepared["controls"]
        result = {"status": "PASS: zero filter and controls cold-replayed; parent cache reused",
            **bindings(), "preparation_sha256": sha(args.preparation.read_bytes()),
            "filter_sha256": sha(args.filter.read_bytes()), "eigendecompositions": 0, "optimizer_calls": 0}
        save_new(args.output, result)
    elif args.mode == "scan":
        result = scan(args.preparation, args.filter, args.output, args.seconds)
    else:
        result = replay(args.preparation, args.filter, args.result)
        save_new(args.output, result)
    print(json.dumps({k: result[k] for k in ("status", "source_sha256", "retained_cuts", "optimizer_calls", "eigendecompositions") if k in result}, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
