"""Exact arithmetic for a bounded case4 LP/basis/parity cycle.

No optimizer is imported. Appended rows retain the complete frozen matrix
as a literal prefix. Saved basis restrictions are point proposals only.
"""
from collections import Counter
from fractions import Fraction
from itertools import product
from math import gcd
import hashlib
import json
import time

import numpy as np
import rook_case4_parity_polytope as parity


def tick(deadline):
    if time.monotonic() >= deadline:
        raise TimeoutError("bounded parity-cycle arithmetic")


def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"))+"\n").encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def matrix_binding(arrays):
    return {name: {"dtype": str(value.dtype), "shape": list(value.shape),
                   "sha256": sha(value.tobytes(order="C"))}
            for name, value in sorted(arrays.items())}


def point_key(nums, den):
    assert type(den) is int and den > 0 and all(type(v) is int for v in nums)
    divisor = gcd(den, *nums)
    return sha(canonical({"denominator": str(den//divisor),
                         "numerators": [str(v//divisor) for v in nums]}))


def row_key(row):
    return sha(canonical({"terms": row["terms"], "upper": row["upper"]}))


def verify_cut(cut, gram, zeros, nums, den, deadline):
    """Every coefficient comes from an actual original Gram-row sum."""
    ids = cut["original_Gram_row_ids"]
    assert ids == sorted(set(ids)) and all(type(i) is int and 0 <= i < len(gram) for i in ids)
    coefficients, total = [0]*len(nums), 0
    for i in ids:
        tick(deadline)
        _, _, quota, support = gram[i]
        total += quota
        for a in support:
            coefficients[a] += 1
    assert coefficients == cut["full_original1214_integer_coefficients"]
    assert total == cut["original_Gram_rhs_sum"]
    zero_set = set(zeros)
    odd = [a for a, c in enumerate(coefficients) if c % 2]
    support = [a for a in odd if a not in zero_set]
    removed = [a for a in odd if a in zero_set]
    assert removed == cut["removed_proved_zero_odd_columns"]
    assert hex(sum(1 << a for a in support)) == cut["active_original_support_hex"]
    rhs = total % 2
    assert rhs == cut["parity_rhs"]
    certificate = cut["forbidden_vertex_certificate"]
    assert certificate["support"] == support and certificate["parity_rhs"] == rhs
    checked = parity.check_exact(certificate, nums, den)
    assert checked["exact_violation_numerator"] > 0
    assert checked["inequality"] == cut["inequality"]
    assert checked["exact_violation_numerator"] == cut["exact_violation_numerator"]
    assert all(nums[a] == 0 for a in zeros)
    return checked


def append_rows(prefix, rows, original_ids):
    """Append signed parity inequalities; all existing array entries persist."""
    inverse = {int(a): j for j, a in enumerate(original_ids)}
    assert len(inverse) == len(original_ids)
    data, columns, pointers = [], [], []
    lower, upper = [], []
    offset = len(prefix["coefficients"])
    for row in rows:
        terms = row["terms"]
        assert terms == sorted(terms) and len({a for a, c in terms}) == len(terms)
        assert all(type(a) is type(c) is int and a in inverse and c in (-1, 1) for a, c in terms)
        assert type(row["upper"]) is int
        # Every omitted lower endpoint is the exact unit-box minimum.
        lo = sum(min(c, 0) for _, c in terms)
        assert lo <= row["upper"], "empty impossible parity must be handled as a separate certificate"
        for a, c in terms:
            columns.append(inverse[a])
            data.append(c)
        offset += len(terms)
        pointers.append(offset)
        lower.append(lo)
        upper.append(row["upper"])
    out = dict(prefix)
    for name, values in (("coefficients", data), ("column_indices", columns),
                         ("row_pointers", pointers), ("row_lower", lower),
                         ("row_upper", upper)):
        out[name] = np.concatenate((prefix[name], np.asarray(values, dtype=prefix[name].dtype)))
        assert np.array_equal(out[name][:len(prefix[name])], prefix[name]), ("immutable prefix", name)
    assert out["row_pointers"][-1] == len(out["coefficients"]) == len(out["column_indices"])
    assert len(out["row_lower"]) + 1 == len(out["row_pointers"])
    return out


def row_terms(arrays, row):
    start, end = map(int, arrays["row_pointers"][row:row+2])
    return [[int(arrays["column_indices"][p]), int(arrays["coefficients"][p])]
            for p in range(start, end)]


def fold_terms(terms, representatives, positions, fixed):
    coefficients = Counter()
    constant = 0
    for j, value in terms:
        group = representatives[j]
        if group in fixed:
            constant += value*fixed[group]
        else:
            coefficients[positions[group]] += value
    return [[j, coefficients[j]] for j in sorted(coefficients) if coefficients[j]], constant


def basis_proposal(arrays, numeric, selectors, extension_start, max_dimension, deadline):
    """Use only statuses saved by a valid basis; never infer a universal face."""
    variables = selectors+1
    assert numeric["basis_valid"] and numeric["optimal"] and numeric["solution_value_valid"]
    statuses = numeric["column_basis_status"]
    assert len(statuses) == variables
    basic, lower, upper = ("HighsBasisStatus.k"+s for s in ("Basic", "Lower", "Upper"))
    assert all(s in (basic, lower, upper) for s in statuses), "unsupported nonbasic status"
    active_ids = numeric["active_original_row_ids"]
    assert len(active_ids) == len(set(active_ids))
    active = numeric["nonbasic_original_row_status"]
    assert len({r for r, s in active}) == len(active)
    assert all(r in set(active_ids) and s in (lower, upper) for r, s in active)
    fixed_columns = {j: int(s == upper) for j, s in enumerate(statuses) if s != basic}
    assert len(active)+len(fixed_columns) == variables, "saved statuses do not give one square basis"
    aliases = set()
    for r, side in active:
        tick(deadline)
        assert 0 <= r < len(arrays["row_lower"])
        if extension_start <= r < extension_start+selectors:
            j = r-extension_start
            assert row_terms(arrays, r) == [[j, 1], [selectors, -1]]
            assert int(arrays["row_lower"][r]) == 0 and int(arrays["row_upper"][r]) == 1
            assert side == lower, "upper max-min row would force t=0; positive reconstruction refused"
            aliases.add(j)
    representatives = [selectors if j in aliases else j for j in range(variables)]
    fixed = {}
    for j, value in fixed_columns.items():
        group = representatives[j]
        assert group not in fixed or fixed[group] == value
        fixed[group] = value
    free = sorted(set(representatives)-set(fixed))
    assert 0 < len(free) <= max_dimension, "dynamic exact residual exceeds prepared size"
    positions = {j: i for i, j in enumerate(free)}
    rows = []
    for r, side in active:
        if extension_start <= r < extension_start+selectors:
            continue
        tick(deadline)
        full = row_terms(arrays, r)
        folded, constant = fold_terms(full, representatives, positions, fixed)
        endpoint = int(arrays["row_lower" if side == lower else "row_upper"][r])
        rhs = endpoint-constant
        if not folded:
            assert rhs == 0
            continue
        rows.append({"row": r, "side": side, "full_terms": full, "endpoint": endpoint,
                     "fixed_constant": constant, "reduced_terms": folded, "rhs": rhs})
    assert len(rows) == len(free), "no alternative minor or second basis is searched"
    return {"candidate_aliases": sorted(aliases),
            "fixed_nonbasic_columns": [[j, fixed_columns[j]] for j in sorted(fixed_columns)],
            "representatives": representatives,
            "fixed_groups": [[j, fixed[j]] for j in sorted(fixed)],
            "free_groups": free, "rows": rows, "dimension": len(free),
            "nonzeros": sum(len(r["reduced_terms"]) for r in rows),
            "saved_nonbasic_rows": active,
            "all_restrictions_are_point_proposals_not_universal": True}


def restore(proposal, values, denominator):
    assert len(values) == len(proposal["free_groups"]) and denominator > 0
    groups = dict(zip(proposal["free_groups"], values))
    groups.update({j: value*denominator for j, value in proposal["fixed_groups"]})
    return [groups[j] for j in proposal["representatives"]]


def verify_proposal_point(proposal, numerators, denominator):
    reduced = [numerators[j] for j in proposal["free_groups"]]
    assert restore(proposal, reduced, denominator) == numerators
    for row in proposal["rows"]:
        assert sum(c*reduced[j] for j, c in row["reduced_terms"]) == row["rhs"]*denominator
        assert sum(c*numerators[j] for j, c in row["full_terms"]) == row["endpoint"]*denominator


def solve_proposal(proposal, max_output_bits, deadline):
    """One FLINT solve. A failure is not an inconsistency certificate."""
    tick(deadline)
    from flint import fmpq_mat
    dimension = proposal["dimension"]
    matrix = [[0]*dimension for _ in range(dimension)]
    for i, row in enumerate(proposal["rows"]):
        for j, c in row["reduced_terms"]:
            matrix[i][j] = c
    start = time.monotonic()
    solved = fmpq_mat(matrix).solve(fmpq_mat([[r["rhs"]] for r in proposal["rows"]]), algorithm="dixon")
    numerator_matrix, denominator = solved.numer_denom()
    values, den = [int(numerator_matrix[i, 0]) for i in range(dimension)], int(denominator)
    assert den > 0
    common = gcd(den, *values)
    values, den = [v//common for v in values], den//common
    assert den.bit_length() <= max_output_bits
    assert all(abs(v).bit_length() <= max_output_bits for v in values)
    nums = restore(proposal, values, den)
    verify_proposal_point(proposal, nums, den)
    tick(deadline)
    return nums, den, {"method": "one fmpq_mat.solve algorithm=dixon",
                       "dimension": dimension, "seconds": time.monotonic()-start,
                       "output_bits": max(den.bit_length(), *(abs(v).bit_length() for v in nums)),
                       "internal_intermediate_bits_not_claimed_bounded": True}


def controls():
    # Arbitrary signed parity rows and zero-free immutable CSR append.
    parity_assignments, prefix_checks = 0, 0
    original_ids = np.asarray([0, 2, 5], dtype="<i4")
    prefix = {"coefficients": np.asarray([1, -1], dtype="<i8"),
              "column_indices": np.asarray([0, 3], dtype="<i4"),
              "row_pointers": np.asarray([0, 2], dtype="<i8"),
              "row_lower": np.asarray([0], dtype="<i8"),
              "row_upper": np.asarray([1], dtype="<i8"),
              "original_column_ids": original_ids}
    for rhs in (0, 1):
        for vertex in product((0, 1), repeat=3):
            if sum(vertex) % 2 == rhs:
                continue
            cert = {"support": [0, 2, 5], "parity_rhs": rhs,
                    "forbidden_ones": [j for j, b in zip(original_ids, vertex) if b]}
            cert["forbidden_ones"] = list(map(int, cert["forbidden_ones"]))
            row = parity.inequality(cert)
            appended = append_rows(prefix, [row], original_ids)
            prefix_checks += 1
            assert appended["row_pointers"].tolist() == [0, 2, 5]
            for z in product((0, 1), repeat=3):
                if sum(z) % 2 == rhs:
                    value = sum(c*z[list(original_ids).index(j)] for j, c in row["terms"])
                    assert int(appended["row_lower"][-1]) <= value <= row["upper"]
                    parity_assignments += 1
    # Dynamic dimensions with arbitrary fixed groups and shared t aliases.
    folds = 0
    for alias_mask in range(8):
        representatives = [3 if alias_mask >> j & 1 else j for j in range(3)]+[3]
        groups = sorted(set(representatives))
        for fixed_group in [None]+groups:
            fixed = {} if fixed_group is None else {fixed_group: 1}
            free = [j for j in groups if j not in fixed]
            positions = {j: i for i, j in enumerate(free)}
            for cs in product((-1, 0, 1), repeat=4):
                terms = [[j, c] for j, c in enumerate(cs) if c]
                folded, constant = fold_terms(terms, representatives, positions, fixed)
                for vals in product((0, 2), repeat=len(free)):
                    values = dict(zip(free, vals)); values.update(fixed)
                    original = [values[j] for j in representatives]
                    assert sum(c*original[j] for j, c in terms) == constant+sum(c*vals[j] for j, c in folded)
                    folds += 1
    # Complete synthetic saved statuses; no linear solve needed.
    toy = {"coefficients": np.asarray([1, 1, 1, -1, 1, -1], dtype="<i8"),
           "column_indices": np.asarray([0, 1, 0, 2, 1, 2], dtype="<i4"),
           "row_pointers": np.asarray([0, 2, 4, 6], dtype="<i8"),
           "row_lower": np.asarray([1, 0, 0], dtype="<i8"),
           "row_upper": np.asarray([1, 1, 1], dtype="<i8")}
    for nfix in (0, 1):
        statuses = ["HighsBasisStatus.kBasic"]*3
        active = [[0, "HighsBasisStatus.kLower"], [1, "HighsBasisStatus.kLower"]]
        if nfix:
            statuses[1] = "HighsBasisStatus.kUpper"
        else:
            active.append([2, "HighsBasisStatus.kLower"])
        numeric = {"basis_valid": True, "optimal": True, "solution_value_valid": True,
                   "column_basis_status": statuses, "active_original_row_ids": [0, 1, 2],
                   "nonbasic_original_row_status": active}
        proposal = basis_proposal(toy, numeric, 2, 1, 8, time.monotonic()+2)
        point, den = ([0, 1, 0], 1) if nfix else ([1, 1, 1], 2)
        verify_proposal_point(proposal, point, den)
        assert proposal["dimension"] == 1
    return {"status": "PASS", "signed_parity_assignments": parity_assignments,
            "immutable_prefix_appends": prefix_checks, "dynamic_alias_fixed_group_controls": folds,
            "saved_basis_dynamic_dimension_controls": 2,
            "optimizer_calls": 0, "production_linear_solve_calls": 0}
