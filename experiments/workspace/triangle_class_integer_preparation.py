"""Point-independent integer coordinate/pair triangle-count preparation.

All 1296 five-root classes and all signed supports of size at most two
remain in the ledger. No count point, eigensystem or optimizer is used.
"""
import argparse
from collections import Counter
from functools import lru_cache
import gzip
from itertools import combinations, permutations
import json
from math import gcd
from pathlib import Path
import pickle
import time

import triangle_incidence_projector_moments as base

BINDINGS = {
    "base_source": "1e7a8b7380314d6dfd8ff05954a13662bc011378f5759ad675ec1bc281fa19e9",
    "model_gzip": "56620a3a04a298073ebd9c7988e6579805ceb997c1b1814b79f846767a028992",
    "model_raw": "88430ae5002742a0551c555a0798c07684c730932ee1d546864bf170105b76bd",
    "reduction": "8ac6843d1294ab3d24e6b71942ee653c1c86cc858d74101e8d2e8a3c53bca07c",
}
REASONS = {
    "Z": "zero as an induced-count coefficient form",
    "I": "nonnegative induced-count coefficients",
    "E": "zero under the frozen order-nine extension reduction",
    "O": "nonnegative ordinary-core coefficients after exact reduction",
    "F": "endpoint factorial of a nonnegative integer class combination",
    "T": "translation or reflection of a coordinate inequality",
    "C": "remaining candidate; no point evaluation performed",
}


def terms(form):
    return tuple((i, a) for i, a in sorted(form.items()) if a)


def add(target, form, coefficient=1):
    for i, a in form.items():
        target[i] += coefficient * a


def scalar_entries(block):
    entries = [Counter() for _ in range(block["order"] * (block["order"] + 1) // 2)]
    for position, graph, coefficient in block["terms"]:
        assert coefficient > 0
        entries[position][graph] += coefficient
    return entries


def entry(entries, i, j):
    return entries[max(i, j) * (max(i, j) + 1) // 2 + min(i, j)]


def partitions(domain, degree=14):
    root = domain["root_rows"]
    classes = domain["classes"]
    internal = base.triangles(root)
    result = []
    for v in range(5):
        contained = [i for i, c in enumerate(classes)
                     if c["root_intersection_mask"] & (1 << v)]
        result.append({"kind": "point_star", "vertices": [v],
                       "members": contained, "quota": degree // 2})
        exactly = [i for i, c in enumerate(classes)
                   if c["root_intersection_mask"] == 1 << v]
        quota = degree // 2 - root[v].bit_count() + sum(v in t for t in internal)
        result.append({"kind": "two_outside", "vertices": [v],
                       "members": exactly, "quota": quota})
        for w in range(5):
            if v == w:
                continue
            members = []
            for i, c in enumerate(classes):
                if c["root_intersection_mask"] & (1 << v):
                    multiplicity = sum(bool(m & (1 << w)) for m in c["outside_masks"])
                    assert multiplicity <= 1
                    if multiplicity:
                        members.append(i)
            quota = 2 - ((root[v] >> w) & 1) - (root[v] & root[w]).bit_count()
            assert quota >= 0
            result.append({"kind": "outside_common_neighbors", "vertices": [v, w],
                           "members": members, "quota": quota})
    return result


def bounds(domain, groups):
    constants = {i: 1 for i, c in enumerate(domain["classes"]) if not c["outside_masks"]}
    result = []
    for i, c in enumerate(domain["classes"]):
        low = constants.get(i, 0)
        possibilities = []
        for gi, group in enumerate(groups):
            if i in group["members"]:
                remaining = group["quota"] - sum(value for j, value in constants.items()
                                                if j != i and j in group["members"])
                possibilities.append((remaining, gi))
        assert possibilities
        upper = min(a for a, _ in possibilities)
        if c["root_intersection_mask"].bit_count() >= 2 or any(m.bit_count() >= 3 for m in c["outside_masks"]):
            upper = min(upper, 1)
        if i in constants:
            upper = 1
        assert 0 <= low <= upper <= 7
        witnesses = [gi for a, gi in possibilities if a == upper]
        result.append({"lower": low, "upper": upper,
                       "upper_partition_witnesses": witnesses,
                       "constant": i in constants})
    return result, constants


def complement(i, bound, groups, constants):
    if bound["constant"]:
        return Counter()
    if not bound["upper_partition_witnesses"]:
        return None
    group = groups[bound["upper_partition_witnesses"][0]]
    return Counter({j: 1 for j in group["members"] if j != i and j not in constants})


def polynomial(entries, first, root_form, support, shift):
    form = Counter()
    for i, a in support:
        add(form, first[i], -(2 * shift + 1) * a)
        for j, b in support:
            if j <= i:
                add(form, entry(entries, i, j), a * b * (1 if i == j else 2))
    add(form, root_form, shift * (shift + 1))
    return form


def factorial_form(entries, first, weights):
    """E[R(R-1)] for R=sum nonnegative integer weights times class counts."""
    assert all(type(w) is int and w >= 0 for w in weights.values())
    out = Counter()
    for i, a in weights.items():
        add(out, entry(entries, i, i), a * a)
        add(out, first[i], -a)
        for j, b in weights.items():
            if j < i:
                add(out, entry(entries, i, j), 2 * a * b)
    assert all(a >= 0 for a in out.values())
    return out


def vector_bounds(i, j, sign, class_bounds, groups, constants, entries):
    bi = class_bounds[i]
    if j < 0:
        return bi["lower"], bi["upper"], Counter() if bi["constant"] else Counter({i: 1}), complement(i, bi, groups, constants)
    bj = class_bounds[j]
    if sign == 1:
        low = bi["lower"] + bj["lower"]
        upper = bi["upper"] + bj["upper"]
        lower_rep = Counter({k: 1 for k in (i, j) if k not in constants})
        ci = complement(i, bi, groups, constants)
        cj = complement(j, bj, groups, constants)
        upper_rep = None if ci is None or cj is None else ci + cj
        for group in groups:
            if i in group["members"] and j in group["members"]:
                candidate = group["quota"] - sum(value for k, value in constants.items()
                                                if k not in (i, j) and k in group["members"])
                if candidate < upper:
                    upper = candidate
                    upper_rep = Counter({k: 1 for k in group["members"]
                                         if k not in (i, j) and k not in constants})
        if not terms(entry(entries, i, j)):
            candidate = max(bi["upper"], bj["upper"])
            if candidate < upper:
                upper = candidate
                upper_rep = None
    else:
        low = bi["lower"] - bj["upper"]
        upper = bi["upper"] - bj["lower"]
        cj = complement(j, bj, groups, constants)
        ci = complement(i, bi, groups, constants)
        lower_rep = None if cj is None else cj + (Counter({i: 1}) if i not in constants else Counter())
        upper_rep = None if ci is None else ci + (Counter({j: 1}) if j not in constants else Counter())
    assert low <= upper
    return low, upper, lower_rep, upper_rep


def rook_controls(domains):
    rook = tuple(sum(1 << j for j in range(9)
                     if j != i and (i // 3 == j // 3 or i % 3 == j % 3))
                 for i in range(9))
    by_rows = {tuple(d["root_rows"]): d for d in domains}
    ts = base.triangles(rook)
    count = comparisons = 0
    for chosen in permutations(range(9), 5):
        root = base.induced(rook, chosen)
        if root not in by_rows:
            continue
        domain = by_rows[root]
        ids = {(c["root_intersection_mask"], tuple(c["outside_masks"])): i
               for i, c in enumerate(domain["classes"])}
        actual = [0] * len(ids)
        root_set = set(chosen)
        for triangle in ts:
            if not root_set.intersection(triangle):
                continue
            inside = sum(1 << i for i, v in enumerate(chosen) if v in triangle)
            outside = sorted(sum(((rook[v] >> w) & 1) << i for i, w in enumerate(chosen))
                             for v in triangle if v not in root_set)
            actual[ids[inside, tuple(outside)]] += 1
        groups = partitions(domain, 4)
        bb, _ = bounds(domain, groups)
        for group in groups:
            assert sum(actual[i] for i in group["members"]) == group["quota"]
            comparisons += 1
        assert all(b["lower"] <= n <= b["upper"] for b, n in zip(bb, actual))
        count += 1
    assert count > 0
    return {"rook_labelled_root_embeddings": count, "exact_partition_comparisons": comparisons,
            "all_coordinate_bounds_checked": True}


def load_inputs(args):
    assert base.digest(Path(base.__file__).read_bytes()) == BINDINGS["base_source"]
    packed = args.model.read_bytes()
    assert base.digest(packed) == BINDINGS["model_gzip"]
    raw = gzip.decompress(packed)
    assert base.digest(raw) == BINDINGS["model_raw"]
    model = json.loads(raw)
    assert [d["root_type"] for d in model["domains"]] == list(range(17, 38))
    assert sum(len(d["classes"]) for d in model["domains"]) == 1296
    raw = args.reduction.read_bytes()
    assert base.digest(raw) == BINDINGS["reduction"]
    graphs, levels, aut, cores, scale, inj, induced = pickle.loads(raw)
    assert len(graphs) == 6535 and len(cores) == 57 and scale == 362880
    assert induced.shape == (6535, 58)
    assert all(int(x) % scale == 0 for x in induced.flat)
    reduced = tuple(tuple(int(x) // scale for x in row) for row in induced)
    for d in model["domains"]:
        assert list(graphs[d["root_type"]]) == d["root_rows"]
        assert aut[d["root_type"]] == d["root_automorphisms"]
    return model, reduced


def prepare(args):
    assert 0 < args.seconds <= 60 and not args.directory.exists()
    started = time.monotonic()
    deadline = started + args.seconds
    model, reduction = load_inputs(args)
    @lru_cache(maxsize=50000)
    def reduced(form):
        answer = [0] * 58
        for graph, coefficient in form:
            assert 0 <= graph < 6535 and type(coefficient) is int
            row = reduction[graph]
            answer = [x + coefficient * y for x, y in zip(answer, row)]
        return tuple(answer)
    records = []
    census = Counter()
    candidate_ids = {}
    candidate_forms = []
    args.directory.mkdir(parents=True)
    report = {"status": "INCOMPLETE", "source_sha256": base.digest(Path(__file__).read_bytes()),
              "bindings": BINDINGS, "count_point_loaded": False, "optimizer_called": False,
              "spectral_search_called": False, "completed_roots": []}
    try:
        control = rook_controls(model["domains"])
        for position, domain in enumerate(model["domains"]):
            base.check_time(deadline)
            rid = domain["root_type"]
            classes = domain["classes"]
            entries = scalar_entries(model["families"]["scalar"][position])
            first = [Counter({gid: coefficient}) for gid, coefficient in model["first_moment_forms"][position]["forms"]]
            root_form = Counter({rid: domain["root_automorphisms"]})
            groups = partitions(domain)
            bb, constants = bounds(domain, groups)
            row_identities = 0
            for group in groups:
                difference = Counter()
                for i in group["members"]:
                    add(difference, first[i])
                add(difference, root_form, -group["quota"])
                assert not any(reduced(terms(difference)))
                census["first_partition_identities"] += 1
                for i in range(len(classes)):
                    difference = Counter()
                    for j in group["members"]:
                        add(difference, entry(entries, i, j))
                    add(difference, first[i], -group["quota"])
                    assert not any(reduced(terms(difference))), (rid, group, i)
                    row_identities += 1
                base.check_time(deadline)
            for i, bound in enumerate(bb):
                difference = entry(entries, i, i).copy()
                add(difference, first[i], -1)
                assert all(a >= 0 for a in difference.values())
                if bound["upper"] <= 1:
                    assert not terms(difference)
                    census["binary_literal_identities"] += 1
                if i in constants:
                    assert terms(first[i]) == terms(root_form)
                    assert all(terms(entry(entries, i, j)) == terms(first[j]) for j in range(len(classes)))
                census["coordinate_upper_bound_" + str(bound["upper"])] += 1
            all_vectors = [(i, -1, 1) for i in range(len(classes))]
            all_vectors += [(i, j, sign) for i in range(len(classes))
                            for j in range(i + 1, len(classes)) for sign in (1, -1)]
            ledger = []
            for vi, (i, j, sign) in enumerate(all_vectors):
                if vi % 128 == 0:
                    base.check_time(deadline)
                support = [(i, 1)] + ([] if j < 0 else [(j, sign)])
                lo, hi, lower_rep, upper_rep = vector_bounds(i, j, sign, bb, groups, constants, entries)
                classifications = []
                translated = j >= 0 and (i in constants or j in constants)
                for shift in range(lo, hi):
                    census["integer_shifts"] += 1
                    if translated:
                        if j in constants:
                            target, target_shift = i, shift - sign * constants[j]
                        elif sign == 1:
                            target, target_shift = j, shift - constants[i]
                        else:
                            target, target_shift = j, constants[i] - shift - 1
                        assert bb[target]["lower"] <= target_shift < bb[target]["upper"]
                        classifications.append(["T", target, target_shift])
                        census["T"] += 1
                        continue
                    form = polynomial(entries, first, root_form, support, shift)
                    tt = terms(form)
                    if not tt:
                        reason = "Z"
                    elif all(a >= 0 for _, a in tt):
                        reason = "I"
                    else:
                        rr = reduced(tt)
                        if not any(rr):
                            reason = "E"
                        elif all(a >= 0 for a in rr):
                            reason = "O"
                        else:
                            representation = lower_rep if shift == lo else None
                            if shift == hi - 1 and upper_rep is not None:
                                representation = upper_rep
                            if representation is not None:
                                witness = factorial_form(entries, first, representation)
                                difference = form.copy()
                                add(difference, witness, -1)
                                assert not any(reduced(terms(difference)))
                                reason = "F"
                            else:
                                divisor = 0
                                for a in rr:
                                    divisor = gcd(divisor, abs(a))
                                assert divisor > 0
                                primitive = tuple(a // divisor for a in rr)
                                if primitive not in candidate_ids:
                                    candidate_ids[primitive] = len(candidate_forms)
                                    candidate_forms.append(list(primitive))
                                reason = "C"
                                classifications.append([reason, candidate_ids[primitive]])
                                census[reason] += 1
                                continue
                    classifications.append([reason])
                    census[reason] += 1
                ledger.append([i, j, sign, lo, hi, classifications])
                census["vectors"] += 1
            record = {"root_type": rid, "root_mass_induced_form": list(map(list, terms(root_form))),
                      "partitions": groups, "class_bounds": bb,
                      "second_partition_identities": row_identities,
                      "vector_ledger_schema": ["i", "j_or_minus_one", "second_sign", "lower", "upper", "shift_classes_in_increasing_order"],
                      "vectors": ledger}
            records.append(record)
            census["second_partition_identities"] += row_identities
            report["completed_roots"].append(rid)
            raw = base.canonical(record)
            (args.directory / ("root-" + str(rid) + ".json.gz")).write_bytes(gzip.compress(raw, mtime=0))
            print(json.dumps({"completed_root": rid, "vectors": len(ledger),
                              "distinct_remaining_core_forms": len(candidate_forms)}), flush=True)
        assert census["vectors"] == 127296 and len(records) == 21
        base.check_time(deadline)
        full = {"schema": "conway99.five-root-triangle-integer-preparation.v1",
                "bindings": BINDINGS, "reason_codes": REASONS, "roots": records,
                "distinct_candidate_core_forms": candidate_forms,
                "all_1296_classes_retained": True, "complete_signed_support_at_most_two": True,
                "constant_shift_cases_follow_nonnegative_root_mass": True,
                "all_other_integer_shifts_follow_bounds_and_recorded_intervals": True,
                "current_count_point_not_loaded": True}
        raw = base.canonical(full)
        packed = gzip.compress(raw, mtime=0)
        (args.directory / "model.json.gz").write_bytes(packed)
        base.check_time(deadline)
        report.update(status="COMPLETE_INTEGER_COORDINATE_PAIR_PREPARATION_NO_POINT_QUERY",
                      complete_21_root_coverage=True, classes=1296,
                      census=dict(census), distinct_candidate_core_forms=len(candidate_forms),
                      literal_rook_controls=control, reduction_cache_info=str(reduced.cache_info()),
                      model_raw_sha256=base.digest(raw), model_gzip_sha256=base.digest(packed),
                      model_raw_bytes=len(raw), model_gzip_bytes=len(packed))
    except Exception as error:
        report.update(status="INCOMPLETE_NO_COMPLETE_FAMILY_CLAIM",
                      error_type=type(error).__name__, error_message=str(error))
        raise
    finally:
        report["seconds"] = time.monotonic() - started
        (args.directory / "preparation.json").write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps(report, indent=2), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--reduction", type=Path, required=True)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--seconds", type=float, default=60)
    prepare(parser.parse_args())


if __name__ == "__main__":
    main()

