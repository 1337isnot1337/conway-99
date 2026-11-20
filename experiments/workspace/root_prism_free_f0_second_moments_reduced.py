"""Exact equivalent reduction of the frozen F0 second-moment linear model.

No optimizer is imported. Every old row is retained, a zero substitution,
an exact equality dependency, or has a stated nonnegative-row witness.
The original full point inspector remains the final acceptance rule.
"""
import argparse
from collections import Counter, defaultdict
import gzip
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import signal
import time

MODEL_SHA = "404d91da35c798ba248887c22a7500957947e24b71d5197dc44432460e6d219e"
RANK_CERT_SHA = "8505c767d4217e9dcec16d34a70276b68c44e9a7e6b1a2131198d15782a1c8df"
RANK_SOURCE_SHA = "5cb54eb3447cf340f1f3bc4bcd4e329baa31689d0604fdc6b45f9205053a5c1d"
OLD_EXACT_SHA = "3986ac84e6d891a0dc362db05f7785ae4294fe58a31a6241f0b63721de5868cd"
SECONDS = 120


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode()


def save_new(path, value):
    assert not path.exists()
    raw = json.dumps(value, sort_keys=True, indent=2).encode()+b"\n"
    path.write_bytes(gzip.compress(raw, mtime=0) if path.suffix == ".gz" else raw)


def imported(name, expected):
    path = Path(__file__).with_name(name+".py")
    assert sha(path.read_bytes()) == expected
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def terms_dict(terms):
    out = Counter()
    for j, c in terms:
        out[j] += c
    return {j: c for j, c in out.items() if c}


def terms_list(terms):
    return [[j, c] for j, c in sorted(terms.items()) if c]


def add_terms(left, right, scale=1):
    out = Counter(left)
    for j, c in right.items():
        out[j] += scale*c
    return {j: c for j, c in out.items() if c}


def key(row):
    return tuple((j, c) for j, c in row["terms"]), row["rhs"]


def normalized(terms, rhs, equality):
    terms = terms_list(terms_dict(terms))
    if not terms:
        return terms, rhs, 1
    divisor = math.gcd(abs(rhs), *(abs(c) for j, c in terms))
    if equality and terms[0][1] < 0:
        divisor = -divisor
    return [[j, c//divisor] for j, c in terms], rhs//divisor, divisor


def pair_id(a, b):
    assert 0 <= a < b < 480
    return a*(959-a)//2+b-a-1


def reconstruct_context(model, certificate):
    eq, iq = model["matrix"]["equalities"], model["matrix"]["inequalities"]
    assert len(eq) == 7165 and len(iq) == 46122
    xof = [None]*480
    for i, orbit in enumerate(model["selector_orbits"]):
        for a in orbit:
            assert xof[a] is None
            xof[a] = i
    assert None not in xof and len(model["selector_orbits"]) == 42
    def zv(a, b):
        if a == b:
            return xof[a]
        a, b = sorted((a, b))
        return 5847+model["pair_to_orbit"][pair_id(a, b)]
    source_rows = model["original_selector_equalities"]
    def lift(a, r):
        out = Counter({xof[a]: -source_rows[r]["quota"]})
        for b in source_rows[r]["support"]:
            out[zv(a, b)] += 1
        return {j: c for j, c in out.items() if c}
    mapping, scale = model["full_RLT_to_quotient"], model["full_RLT_signed_divisor"]
    assert len(mapping) == len(scale) == 82560
    for a in range(480):
        for r in range(172):
            at = 172*a+r
            raw = lift(a, r)
            q = mapping[at]
            if q < 0:
                assert q == -1 and scale[at] == 0 and not raw
            else:
                row = eq[686+q]
                assert row["family"] == "selector RLT equality" and row["rhs"] == 0
                assert scale[at] != 0
                assert raw == {j: c*scale[at] for j, c in row["terms"]}
    reps = [min(orbit) for orbit in model["selector_orbits"]]
    origins = {}
    for a in reps:
        for r in range(172):
            q = mapping[172*a+r]
            if q >= 0:
                origins.setdefault(q, [a, r])
    assert set(origins) == set(range(6090))
    basis = certificate["basis_original_rows"]
    retained_RLT = {mapping[172*a+r] for a in reps for r in basis} - {-1}
    assert len(retained_RLT) == 5360
    fixed = {}
    for i, row in enumerate(eq):
        if row["family"] == "certified zero selector moment":
            assert row["rhs"] == 0 and len(row["terms"]) == 1 and row["terms"][0][1] == 1
            variable = row["terms"][0][0]
            assert variable not in fixed
            fixed[variable] = i
    assert len(fixed) == 389 and sorted(fixed) == [5847+j for j in model["zero_pair_orbits"]]
    eq_lookup = {}
    iq_lookup = {}
    for i, row in enumerate(eq):
        eq_lookup.setdefault(key(row), i)
    for i, row in enumerate(iq):
        iq_lookup[(row["family"], key(row))] = i
    assert len(iq_lookup) == len(iq)
    return {"xof": xof, "zv": zv, "lift": lift, "mapping": mapping, "scale": scale,
            "reps": reps, "origins": origins, "retained_RLT": retained_RLT,
            "fixed": fixed, "eq_lookup": eq_lookup, "iq_lookup": iq_lookup}


def equality_dependencies(model, certificate, context):
    eq = model["matrix"]["equalities"]
    result = {}
    for q in range(6090):
        if q in context["retained_RLT"]:
            continue
        a, r = context["origins"][q]
        dep = certificate["original_row_dependencies"][r]
        left_scale = dep["denominator"]*context["scale"][172*a+r]
        right = Counter()
        for basis_row, coefficient in dep["terms"]:
            at = 172*a+basis_row
            other = context["mapping"][at]
            if other >= 0:
                assert other in context["retained_RLT"]
                right[686+other] += coefficient*context["scale"][at]
        right = {j: c for j, c in right.items() if c}
        actual = {}
        for j, c in right.items():
            actual = add_terms(actual, terms_dict(eq[j]["terms"]), c)
        expected = {j: c*left_scale for j, c in eq[686+q]["terms"]}
        assert actual == expected and left_scale != 0
        assert sum(c*eq[j]["rhs"] for j, c in right.items()) == left_scale*eq[686+q]["rhs"]
        result[686+q] = {"kind": "exact lifted equality dependency", "anchor": a,
                         "original_selector_row": r, "left_multiplier": left_scale,
                         "retained_original_equalities": terms_list(right)}
    assert len(result) == 730
    return result


def inequality_implications(model, certificate, context):
    eq, iq = model["matrix"]["equalities"], model["matrix"]["inequalities"]
    rows = model["original_selector_equalities"]
    covered = certificate["quota_one_coverage"]["chosen_row_for_each_signature"]
    lookup, eq_lookup = context["iq_lookup"], context["eq_lookup"]
    upper = {}
    frechet = {}
    zero_cert = {item["pair_id"]: item for item in model["zero_moment_certificates"]}
    for a in range(480):
        for b in range(a+1, 480):
            z = context["zv"](a, b)
            for anchor, other in ((a, b), (b, a)):
                terms = [[context["xof"][anchor], -1], [z, 1]]
                i = lookup[("Z upper activation", (tuple(map(tuple, terms)), 0))]
                if z in context["fixed"]:
                    continue  # Its substituted row is a direct box tautology.
                support_row = covered[other]
                if support_row is not None and i not in upper:
                    raw = context["lift"](anchor, support_row)
                    slack = add_terms(raw, terms_dict(iq[i]["terms"]), -1)
                    assert all(c >= 0 for c in slack.values())
                    at = 172*anchor+support_row
                    assert context["mapping"][at] >= 0
                    upper[i] = {"kind": "quota-one lifted nonnegative-row bound",
                                "anchor": anchor, "other": other, "selector_row": support_row,
                                "original_lifted_equality": 686+context["mapping"][at],
                                "equality_multiplier": context["scale"][at]}
            if z not in context["fixed"]:
                continue
            term = Counter({z: -1})
            term[context["xof"][a]] += 1
            term[context["xof"][b]] += 1
            i = lookup[("Z lower Frechet bound", (tuple(map(tuple, terms_list(term))), 1))]
            if i in frechet:
                continue
            proof = zero_cert[pair_id(a, b)]
            if proof["kind"] == "quota-one nonnegative lifted equality":
                r = proof["selector_Gram_row"]
                row = rows[r]
                assert row["quota"] == 1 and a in row["support"] and b in row["support"]
                gram_terms = Counter()
                for c in row["support"]:
                    gram_terms[context["xof"][c]] += 1
                normalized_terms, rhs, divisor = normalized(terms_list(gram_terms), 1, True)
                j = eq_lookup[(tuple(map(tuple, normalized_terms)), rhs)]
                assert j < 686 and divisor > 0
                slack = add_terms(gram_terms, terms_dict(iq[i]["terms"]), -1)
                assert all(c >= 0 for c in slack.values())
                frechet[i] = {"kind": "selector quota-one bound plus nonnegative Z",
                              "pair": [a, b], "selector_row": r,
                              "original_selector_equality": j, "multiplier": divisor}
            else:
                selector_terms = Counter()
                selector_terms[context["xof"][a]] += 1
                selector_terms[context["xof"][b]] += 1
                j = lookup[("motif", (tuple(map(tuple, terms_list(selector_terms))), 1))]
                slack = add_terms(terms_dict(iq[j]["terms"]), terms_dict(iq[i]["terms"]), -1)
                assert all(c >= 0 for c in slack.values())
                frechet[i] = {"kind": "retained motif bound plus nonnegative Z",
                              "pair": [a, b], "original_motif_inequality": j}
    links = {}
    for i, row in enumerate(iq):
        if row["family"] == "Y bounded by selector pair moment":
            positive = [j for j, c in row["terms"] if c == 1]
            negative = [j for j, c in row["terms"] if c == -1]
            assert len(positive) == len(negative) == 1 and row["rhs"] == 0
            y, z = positive[0], negative[0]
            assert 42 <= y < 5847 <= z and y not in links
            links[y] = [i, z]
    assert len(links) == 5805
    activation = {}
    for i, row in enumerate(iq):
        if row["family"] != "activation":
            continue
        pos = [j for j, c in row["terms"] if c == 1]
        neg = [j for j, c in row["terms"] if c == -1]
        assert len(pos) == len(neg) == 1 and row["rhs"] == 0 and neg[0] < 42
        j, z = links[pos[0]]
        upper_terms = [[neg[0], -1], [z, 1]]
        k = lookup[("Z upper activation", (tuple(map(tuple, upper_terms)), 0))]
        assert add_terms(terms_dict(iq[j]["terms"]), terms_dict(iq[k]["terms"])) == terms_dict(row["terms"])
        activation[i] = {"kind": "Y-to-Z plus Z upper bound",
                         "original_Y_to_Z_inequality": j, "original_Z_upper_inequality": k}
    assert len(activation) == 11365 and len(frechet) == 389
    return upper, frechet, activation


def build(model_path, rank_path):
    rank = imported("root_prism_free_f0_second_moments_rank", RANK_SOURCE_SHA)
    model, selector_matrix, selector_rhs = rank.load(model_path)
    raw = rank_path.read_bytes()
    assert sha(raw) == RANK_CERT_SHA
    certificate = json.loads(gzip.decompress(raw))
    rank_check = rank.verify(model, selector_matrix, selector_rhs, certificate)
    context = reconstruct_context(model, certificate)
    dependencies = equality_dependencies(model, certificate, context)
    upper, frechet, activation = inequality_implications(model, certificate, context)
    old = model["matrix"]
    kept_variables = [j for j in range(old["variables"]) if j not in context["fixed"]]
    position = {j: i for i, j in enumerate(kept_variables)}
    assert len(kept_variables) == 15200
    new = {"variables": len(kept_variables), "lower": 0, "upper": 1,
           "equalities": [], "inequalities": []}
    images = {"equalities": [], "inequalities": []}
    counts = Counter()
    for kind in ("equalities", "inequalities"):
        seen = {}
        for i, row in enumerate(old[kind]):
            original = terms_dict(row["terms"])
            substituted = [[position[j], c] for j, c in row["terms"] if j in position]
            if kind == "equalities" and i in dependencies:
                images[kind].append(dependencies[i])
                counts["equality_rank_dependencies"] += 1
                continue
            if kind == "inequalities":
                maximum = sum(max(c, 0) for j, c in substituted)
                if maximum <= row["rhs"]:
                    images[kind].append({"kind": "unit-box tautology after zero substitution",
                                         "maximum": maximum, "rhs": row["rhs"]})
                    counts["inequality_box_tautologies"] += 1
                    continue
                if i in upper:
                    images[kind].append(upper[i])
                    counts["Z_upper_lifted_implications"] += 1
                    continue
                if i in frechet:
                    images[kind].append(frechet[i])
                    counts["Frechet_selector_implications"] += 1
                    continue
                if i in activation:
                    images[kind].append(activation[i])
                    counts["Y_activation_implications"] += 1
                    continue
            terms, rhs, divisor = normalized(substituted, row["rhs"], kind == "equalities")
            if not terms:
                assert rhs == 0 if kind == "equalities" else rhs >= 0
                images[kind].append({"kind": "zero equality after certified substitution"})
                counts["equality_zero_after_substitution"] += 1
                continue
            k = tuple(map(tuple, terms)), rhs
            duplicate = k in seen
            if not duplicate:
                seen[k] = len(new[kind])
                new[kind].append({"terms": terms, "rhs": rhs, "family": row["family"],
                                  "first_original_row": i})
            images[kind].append({"kind": "retained scaled row", "new_row": seen[k],
                                 "original_to_new_multiplier": divisor})
            counts[("equality_" if kind == "equalities" else "inequality_")+
                   ("duplicate_after_substitution" if duplicate else "retained")] += 1
    # Every dependency refers only to a retained or identically-zero old row.
    for image in images["equalities"]:
        if image["kind"] == "exact lifted equality dependency":
            assert all(images["equalities"][j]["kind"] in
                       ("retained scaled row", "zero equality after certified substitution")
                       for j, coefficient in image["retained_original_equalities"])
    # Check the proof dependency order; no circular implication is accepted.
    for image in images["inequalities"]:
        kind = image["kind"]
        if kind == "Y-to-Z plus Z upper bound":
            assert images["inequalities"][image["original_Y_to_Z_inequality"]]["kind"] == "retained scaled row"
            assert images["inequalities"][image["original_Z_upper_inequality"]]["kind"] in (
                "retained scaled row", "quota-one lifted nonnegative-row bound",
                "unit-box tautology after zero substitution")
        elif kind == "quota-one lifted nonnegative-row bound":
            assert 0 <= image["original_lifted_equality"] < len(images["equalities"])
        elif kind == "selector quota-one bound plus nonnegative Z":
            assert images["equalities"][image["original_selector_equality"]]["kind"] == "retained scaled row"
        elif kind == "retained motif bound plus nonnegative Z":
            assert images["inequalities"][image["original_motif_inequality"]]["kind"] == "retained scaled row"
    assert sum(counts.values()) == 7165+46122
    record = {"schema": "f0-second-moments-equivalent-linear-reduction-v1",
              "source_sha256": sha(Path(__file__).read_bytes()),
              "inputs": {"original_model_sha256": MODEL_SHA, "selector_rank_sha256": RANK_CERT_SHA,
                         "selector_rank_source_sha256": RANK_SOURCE_SHA,
                         "original_full_point_inspector_sha256": OLD_EXACT_SHA},
              "scope": {"mathematically_equivalent_to_original_linear_model": True,
                        "new_inequalities_or_selector_assumptions_added": False,
                        "PSD_enforced": False, "optimizer_calls": 0},
              "matrix": new, "matrix_sha256": sha(canonical(new)),
              "kept_original_variables": kept_variables,
              "fixed_zero_original_variables": [[j, context["fixed"][j]] for j in sorted(context["fixed"])],
              "original_equality_images": images["equalities"],
              "original_inequality_images": images["inequalities"],
              "selector_rank_replay": rank_check,
              "representative_selector_anchors": context["reps"],
              "every_RLT_quotient_has_representative_origin": [context["origins"][j] for j in range(6090)],
              "all82560_literal_RLT_scalings_verified": True,
              "quota_one_covered_signatures": 468, "uncovered_signatures": certificate["quota_one_coverage"]["uncovered_signatures"],
              "counts": {"original_variables": old["variables"], "variables": new["variables"],
                         "equalities": len(new["equalities"]), "inequalities": len(new["inequalities"]),
                         "nonzeros": sum(len(r["terms"]) for kind in ("equalities", "inequalities") for r in new[kind]),
                         "row_dispositions": dict(counts),
                         "equality_families": dict(Counter(r["family"] for r in new["equalities"])),
                         "inequality_families": dict(Counter(r["family"] for r in new["inequalities"]))},
              "proof_order": ["certified zero variable substitution", "retained equalities", "exact lifted equality dependencies",
                              "retained inequalities and unit boxes", "Z upper implications", "Y activation implications",
                              "Frechet implications"],
              "reverse_direction": "Every reduced row is a positive inequality scaling or nonzero equality scaling of an original row after explicit zero substitution.",
              "forward_direction": "All original rows have exact dependency, nonnegative-row, or finite-box witnesses in original_*_images."}
    return record


def controls():
    for equality in (False, True):
        terms, rhs, divisor = normalized([[0, -4], [1, 6]], 2, equality)
        assert all(c*divisor == old for (j, c), (k, old) in zip(terms, [[0, -4], [1, 6]]))
        assert rhs*divisor == 2
        assert divisor == (-2 if equality else 2)
    # Sum Z_ac=x_a implies Z_ab<=x_a by an explicitly nonnegative remainder.
    raw = {0: -1, 2: 1, 3: 1}
    upper = {0: -1, 2: 1}
    assert add_terms(raw, upper, -1) == {3: 1}
    assert add_terms({1: 1, 2: -1}, upper) == {0: -1, 1: 1}
    # Selector pair quota implies Frechet for every nonnegative moment.
    assert add_terms({0: 1, 1: 1, 3: 1}, {0: 1, 1: 1, 2: -1}, -1) == {2: 1, 3: 1}
    for a in range(480):
        for b in range(a+1, 480):
            assert pair_id(a, b) == a*480-a*(a+1)//2+b-a-1
    return {"status": "PASS: signs, scaling, nonnegative implications and all114960 pair IDs",
            "optimizer_calls": 0}


def inspect(model_path, reduced_path, point_path):
    old_helper = imported("root_prism_free_f0_second_moments_exact", OLD_EXACT_SHA)
    old_model = old_helper.load_model(model_path)
    raw = reduced_path.read_bytes()
    reduced = json.loads(gzip.decompress(raw))
    assert reduced["source_sha256"] == sha(Path(__file__).read_bytes())
    point = json.loads(point_path.read_text())
    checked = old_helper.quotient_check(reduced["matrix"], point)
    assert checked["passed"]
    numerator = [0]*15589
    for j, value in zip(reduced["kept_original_variables"], point["numerators"]):
        numerator[j] = old_helper.integer(value)
    lifted = {"denominator": point["denominator"], "numerators": list(map(str, numerator))}
    full = old_helper.full_point_check(old_model, lifted)
    assert full["passed"]
    return {"status": "PASS: reduced and original full650350 rows/183834 bounds",
            "reduced_model_sha256": sha(raw), "point_sha256": sha(point_path.read_bytes()),
            "original_full_check": full, "optimizer_calls": 0}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("mode", choices=["prepare", "replay", "inspect"])
    p.add_argument("--model", type=Path, required=True)
    p.add_argument("--rank", type=Path)
    p.add_argument("--reduced", type=Path, required=True)
    p.add_argument("--point", type=Path)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    started = time.monotonic()
    def stop(signum, frame):
        raise TimeoutError("equivalent linear preparation limit")
    previous = signal.signal(signal.SIGALRM, stop)
    signal.setitimer(signal.ITIMER_REAL, SECONDS)
    try:
        control = controls()
        if a.mode == "inspect":
            report = inspect(a.model, a.reduced, a.point)
        else:
            assert a.rank is not None
            actual = build(a.model, a.rank)
            actual["controls"] = control
            if a.mode == "prepare":
                save_new(a.reduced, actual)
            else:
                saved = json.loads(gzip.decompress(a.reduced.read_bytes()))
                assert canonical(saved) == canonical(actual)
            report = {"status": "PASS: exact equivalent reduction "+a.mode,
                      "source_sha256": sha(Path(__file__).read_bytes()),
                      "reduced_model_sha256": sha(a.reduced.read_bytes()),
                      "canonical_model_sha256": sha(canonical(actual)),
                      "matrix_sha256": actual["matrix_sha256"], "counts": actual["counts"],
                      "controls": control, "optimizer_calls": 0}
        report["elapsed_seconds"] = time.monotonic()-started
        save_new(a.output, report)
        print(json.dumps(report, indent=2))
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


if __name__ == "__main__":
    main()

