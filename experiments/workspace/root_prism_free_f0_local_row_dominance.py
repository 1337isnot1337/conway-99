"""Exact Boolean capping and same-anchor dominance for necessary selector rows.

Rows are represented by sum(c_j*x_j) <= 0. A usable row has one positive
coefficient t, at its anchor, and nonpositive coefficients elsewhere.
Original authoritative rows are never removed by this helper.
"""
from collections import defaultdict
import hashlib
import json
from math import gcd


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def key(row):
    return hashlib.sha256(canonical(row)).hexdigest()


def capped(row):
    if int(row["rhs"]) != 0:
        return None
    coefficients = defaultdict(int)
    for j, value in row["terms"]:
        assert type(j) is int and 0 <= j < 480
        coefficients[j] += int(value)
    positive = [(j, c) for j, c in coefficients.items() if c > 0]
    if len(positive) != 1:
        return None
    anchor, demand = positive[0]
    weights = [[j, min(-c, demand)] for j, c in sorted(coefficients.items()) if c < 0]
    divisor = gcd(demand, *(w for _, w in weights))
    demand //= divisor
    weights = [[j, w // divisor] for j, w in weights]
    terms = sorted([[anchor, demand]] + [[j, -w] for j, w in weights])
    result = {"row": {"terms": terms, "rhs": 0}, "anchor": anchor,
              "demand": demand, "weights": weights}
    result["key"] = key(result["row"])
    return result


def dominates(first, second):
    """First implies second if every normalized nonnegative RHS weight is <=."""
    if first["anchor"] != second["anchor"]:
        return False
    right = dict(second["weights"])
    return all(w * second["demand"] <= right.get(j, 0) * first["demand"]
               for j, w in first["weights"])


def reduce_rows(candidates, authoritative):
    """Return a frontier and one-step exact coverage witnesses for every input.

Each input item has a row and an origin. Only candidates may be removed.
Every candidate must be equivalent to its capped row on binary selectors.
Every removed candidate has a retained or authoritative dominating row.
"""
    old_by_anchor, old_by_key = defaultdict(list), {}
    old_usable = 0
    for item in authoritative:
        value = capped(item["row"])
        if value is None:
            continue
        old_usable += 1
        if value["key"] not in old_by_key:
            value["origin"] = item["origin"]
            old_by_key[value["key"]] = value
            old_by_anchor[value["anchor"]].append(value)
    unique, origins, raw_keys = {}, defaultdict(list), []
    for item in candidates:
        value = capped(item["row"])
        assert value is not None
        unique[value["key"]] = value
        origins[value["key"]].append(item["origin"])
        raw_keys.append((key(item["row"]), value["key"]))
    old_witness, frontier = {}, defaultdict(list)
    for value in sorted(unique.values(), key=lambda r: (r["anchor"], len(r["weights"]), r["key"])):
        witness = next((r for r in old_by_anchor[value["anchor"]] if dominates(r, value)), None)
        if witness is not None:
            old_witness[value["key"]] = witness["key"]
            continue
        bucket = frontier[value["anchor"]]
        if any(dominates(r, value) for r in bucket):
            continue
        frontier[value["anchor"]] = [r for r in bucket if not dominates(value, r)] + [value]
    retained = sorted((r for bucket in frontier.values() for r in bucket), key=lambda r: r["key"])
    retained_keys = {r["key"] for r in retained}
    coverage = []
    for raw_key, cap_key in raw_keys:
        value = unique[cap_key]
        if cap_key in old_witness:
            witness = old_by_key[old_witness[cap_key]]
            kind = "authoritative"
        else:
            witness = next(r for r in frontier[value["anchor"]] if dominates(r, value))
            kind = "retained"
        assert dominates(witness, value)
        assert kind == "authoritative" or witness["key"] in retained_keys
        coverage.append({"raw_row_key": raw_key, "capped_row_key": cap_key,
                         "dominator_kind": kind, "dominator_key": witness["key"]})
    return {"retained": [dict(r, origins=origins[r["key"]]) for r in retained],
            "coverage": coverage, "used_authoritative_rows": [old_by_key[k] for k in sorted(set(old_witness.values()))],
            "counts": {"raw_candidates": len(candidates), "distinct_capped_candidates": len(unique),
                       "authoritative_rows_checked": len(authoritative), "usable_authoritative_rows": old_usable,
                       "distinct_capped_authoritative_rows": len(old_by_key),
                       "capped_candidates_dominated_by_authoritative": len(old_witness),
                       "retained_capped_candidates": len(retained)},
            "all_authoritative_rows_preserved": True, "optimizer_calls": 0}
