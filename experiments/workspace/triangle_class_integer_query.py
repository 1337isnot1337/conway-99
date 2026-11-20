"""Exact bounded query/replay of all prepared integer triangle-count tests."""
import argparse
from collections import Counter
import gzip
from itertools import product
import json
from math import gcd
from pathlib import Path
import time

import triangle_incidence_projector_moments as base
import triangle_class_integer_preparation as domain_code

BINDINGS = {
    "domain_source": "edc1c76522a4925f8bdd22575d918f7eb995682c4f9b0c10ada80d48b89afca7",
    "domain_preparation": "95a5755cd76cb3b213397405a62cb56d6dc14a9f0646fcaaced2cd8b71f569a8",
    "domain_model_raw": "6cae28c70273af79ea484acb1d8ae8e827696360bee5dfa73956cf25811bfc81",
    "domain_model_gzip": "b85aff09c1e53965d3ec548b8a2d3cdc194bd85fb8eb7c97d4a819aa07306c60",
    "scalar_model_raw": "88430ae5002742a0551c555a0798c07684c730932ee1d546864bf170105b76bd",
    "scalar_model_gzip": "56620a3a04a298073ebd9c7988e6579805ceb997c1b1814b79f846767a028992",
    "point": "0b78eb2cfc0966f66d72b083f71315e4a079e4b25f59f276c58dd93d189b49df",
}


def load_inputs(args):
    assert base.digest(Path(domain_code.__file__).read_bytes()) == BINDINGS["domain_source"]
    assert base.digest(Path(base.__file__).read_bytes()) == domain_code.BINDINGS["base_source"]
    raw = (args.directory / "preparation.json").read_bytes()
    assert base.digest(raw) == BINDINGS["domain_preparation"]
    preparation = json.loads(raw)
    assert preparation["complete_21_root_coverage"] and preparation["classes"] == 1296
    packed = (args.directory / "model.json.gz").read_bytes()
    assert base.digest(packed) == BINDINGS["domain_model_gzip"]
    raw = gzip.decompress(packed)
    assert base.digest(raw) == BINDINGS["domain_model_raw"]
    ledger = json.loads(raw)
    assert ledger["all_1296_classes_retained"] and ledger["complete_signed_support_at_most_two"]
    assert [r["root_type"] for r in ledger["roots"]] == list(range(17, 38))
    packed = args.scalar_model.read_bytes()
    assert base.digest(packed) == BINDINGS["scalar_model_gzip"]
    raw = gzip.decompress(packed)
    assert base.digest(raw) == BINDINGS["scalar_model_raw"]
    scalar = json.loads(raw)
    assert [d["root_type"] for d in scalar["domains"]] == list(range(17, 38))
    raw = args.point.read_bytes()
    assert base.digest(raw) == BINDINGS["point"]
    point = json.loads(raw)
    counts = point["induced_counts"]
    core = point["rounded_core_values"]
    assert len(counts) == 48965 and all(type(x) is int and x >= 0 for x in counts)
    assert len(core) == 550 and core[0] == 1 and all(type(x) is int and x >= 0 for x in core)
    return ledger, scalar, counts, core[:58]


def interval_values(first, second, mass, lower, upper):
    assert 0 <= mass and lower <= upper and lower * mass <= first <= upper * mass
    if mass == 0:
        assert first == second == 0
    if lower == upper:
        assert second == lower * lower * mass
        return [], lower, 0
    values = [(a, second - (2 * a + 1) * first + a * (a + 1) * mass)
              for a in range(lower, upper)]
    shift, value = min(values, key=lambda x: (x[1], x[0]))
    if mass:
        a = first // mass
        unrestricted = second - (2 * a + 1) * first + a * (a + 1) * mass
        assert value == unrestricted
    return values, shift, value


def controls():
    tested = 0
    for lo in range(-4, 4):
        for hi in range(lo, 5):
            for x in range(lo, hi + 1):
                for y in range(lo, hi + 1):
                    for wx, wy in ((1, 0), (1, 1), (2, 3)):
                        g = wx + wy
                        p = wx * x + wy * y
                        q = wx * x * x + wy * y * y
                        vals, a, value = interval_values(p, q, g, lo, hi)
                        assert value >= 0 and all(v >= 0 for _, v in vals)
                        assert value == min(q - (2 * k + 1) * p + k * (k + 1) * g
                                            for k in range(-12, 13))
                        tested += 1
    for lo in range(-7, 8):
        for hi in range(lo, 15):
            vals, a, value = interval_values(0, 0, 0, lo, hi)
            assert value == 0 and all(v == 0 for _, v in vals)
            tested += 1
    assert interval_values(1, 0, 1, 0, 2)[2] == -1
    tested += 1
    return {"status": "PASS_EXACT_INTERVAL_AND_MINIMIZER_CONTROLS",
            "cases": tested, "includes_negative_endpoints_zero_mass_and_a_separator": True}


def exact_form(entries, first, root_form, support, shift, counts):
    form = domain_code.polynomial(entries, first, root_form, support, shift)
    divisor = 0
    for coefficient in form.values():
        divisor = gcd(divisor, abs(coefficient))
    assert divisor > 0
    primitive = [[i, a // divisor] for i, a in domain_code.terms(form)]
    value = sum(a * counts[i] for i, a in primitive)
    return primitive, divisor, value


def evaluate(ledger, scalar, counts, core, deadline, report, progress=False):
    totals = Counter()
    example_hashes = set()
    primitive_core_values = [sum(a * x for a, x in zip(form, core))
                             for form in ledger["distinct_candidate_core_forms"]]
    report["distinct_candidate_core_forms"] = len(primitive_core_values)
    report["negative_primitive_core_forms"] = sum(x < 0 for x in primitive_core_values)
    for position, root in enumerate(ledger["roots"]):
        base.check_time(deadline)
        rid = root["root_type"]
        block = scalar["families"]["scalar"][position]
        assert block["root_type"] == rid
        matrix = base.contract({"blocks": [block]}, counts)[rid]
        first_forms = [Counter({i: a}) for i, a in scalar["first_moment_forms"][position]["forms"]]
        first = [sum(a * counts[i] for i, a in f.items()) for f in first_forms]
        root_form = Counter(dict(root["root_mass_induced_form"]))
        mass = sum(a * counts[i] for i, a in root_form.items())
        if mass == 0:
            assert not any(first) and not any(x for row in matrix for x in row)
        assert len(first) == len(root["class_bounds"])
        for n, bound in zip(first, root["class_bounds"]):
            assert bound["lower"] * mass <= n <= bound["upper"] * mass
        for group in root["partitions"]:
            members, quota = group["members"], group["quota"]
            assert sum(first[i] for i in members) == quota * mass
            assert all(sum(matrix[i][j] for j in members) == quota * first[i]
                       for i in range(len(first)))
        entries = domain_code.scalar_entries(block)
        record = {"root_type": rid, "root_mass": mass, "class_first_moments": first,
                  "scalar_matrix_sha256": base.digest(base.canonical(matrix)),
                  "vector_minimum_schema": ["shift", "value", "negative_shifts", "zero_shifts", "positive_shifts"],
                  "vector_minima": [], "negative_vectors": 0, "constant_vectors": 0}
        coordinate_values = {}
        for vi, (i, j, sign, lower, upper, classifications) in enumerate(root["vectors"]):
            if vi % 256 == 0:
                base.check_time(deadline)
            p = first[i] + (sign * first[j] if j >= 0 else 0)
            q = matrix[i][i] + (2 * sign * matrix[i][j] + matrix[j][j] if j >= 0 else 0)
            values, shift, value = interval_values(p, q, mass, lower, upper)
            assert len(values) == len(classifications)
            negatives = zeros = positives = 0
            for (a, v), reason in zip(values, classifications):
                tag = reason[0]
                if tag in ("Z", "E"):
                    assert v == 0
                elif tag in ("I", "O", "F"):
                    assert v >= 0
                elif tag == "T":
                    assert v == coordinate_values[reason[1], reason[2]]
                elif tag == "C":
                    cv = primitive_core_values[reason[1]]
                    assert (v == 0) == (cv == 0)
                    if cv:
                        assert v % cv == 0 and v // cv > 0
                else:
                    raise AssertionError(tag)
                if j < 0:
                    coordinate_values[i, a] = v
                negatives += v < 0
                zeros += v == 0
                positives += v > 0
                totals["shift_" + tag] += 1
            record["vector_minima"].append([shift, value, negatives, zeros, positives])
            record["negative_vectors"] += value < 0
            record["constant_vectors"] += lower == upper
            totals["vectors"] += 1
            totals["shifts"] += len(values)
            totals["negative_shifts"] += negatives
            totals["zero_shifts"] += zeros
            totals["positive_shifts"] += positives
            totals["negative_vectors"] += value < 0
            if value < 0:
                support = [(i, 1)] + ([] if j < 0 else [(j, sign)])
                form, divisor, primitive = exact_form(entries, first_forms, root_form, support, shift, counts)
                assert primitive * divisor == value < 0
                key = base.digest(base.canonical(form))
                if key not in example_hashes and len(report["negative_examples"]) < 64:
                    example_hashes.add(key)
                    report["negative_examples"].append({
                        "root_type": rid, "vector_index": vi, "support": support,
                        "integer_shift": shift, "first_moment": p, "second_moment": q,
                        "root_mass": mass, "exact_value": value, "positive_gcd": divisor,
                        "primitive_induced_count_form": form, "primitive_value": primitive,
                        "fresh_literal_product_replay_required_before_optimization": True,
                    })
        report["roots"].append(record)
        report["totals"] = dict(totals)
        if progress:
            print(json.dumps({"completed_root": rid, "negative_vectors": record["negative_vectors"]}), flush=True)
    assert totals["vectors"] == 127296 and totals["shifts"] == 366356
    assert totals["negative_shifts"] + totals["zero_shifts"] + totals["positive_shifts"] == 366356
    assert len(report["roots"]) == 21
    assert (totals["negative_vectors"] > 0) == (report["negative_primitive_core_forms"] > 0)
    base.check_time(deadline)
    report["complete_21_root_127296_vector_366356_shift_coverage"] = True
    report["status"] = ("EXACT_COMPLETE_TRIANGLE_CLASS_INTEGER_FAMILY_PASSED"
                        if not totals["negative_vectors"] else "EXACT_TRIANGLE_CLASS_INTEGER_SEPARATORS")


def blank_report():
    return {"status": "INCOMPLETE", "source_sha256": base.digest(Path(__file__).read_bytes()),
            "bindings": BINDINGS, "roots": [], "totals": {}, "negative_examples": [],
            "negative_example_limit": 64, "all_1296_classes_retained": True,
            "complete_21_root_127296_vector_366356_shift_coverage": False,
            "optimizer_called": False, "spectral_search_called": False,
            "graph_existence_resolved": False}


def query(args):
    assert 0 < args.seconds <= 30 and not args.output.exists()
    start = time.monotonic()
    report = blank_report()
    try:
        ledger, scalar, counts, core = load_inputs(args)
        evaluate(ledger, scalar, counts, core, start + args.seconds, report, True)
    except Exception as error:
        report.update(status="INCOMPLETE_NO_COMPLETE_FAMILY_CONCLUSION",
                      error_type=type(error).__name__, error_message=str(error))
        raise
    finally:
        report["seconds"] = time.monotonic() - start
        args.output.write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps({k: v for k, v in report.items() if k not in ("roots", "negative_examples")}, indent=2))


def replay(args):
    assert not args.output.exists()
    start = time.monotonic()
    raw = args.result.read_bytes()
    saved = json.loads(raw)
    assert saved["complete_21_root_127296_vector_366356_shift_coverage"]
    ledger, scalar, counts, core = load_inputs(args)
    rebuilt = blank_report()
    evaluate(ledger, scalar, counts, core, float("inf"), rebuilt)
    assert {k: v for k, v in saved.items() if k != "seconds"} == rebuilt
    report = {"status": "PASS_EXACT_TRIANGLE_CLASS_INTEGER_QUERY_REPLAY",
              "source_sha256": base.digest(Path(__file__).read_bytes()), "bindings": BINDINGS,
              "result_sha256": base.digest(raw), "totals": rebuilt["totals"],
              "complete_21_root_127296_vector_366356_shift_coverage": True,
              "optimizer_called": False, "spectral_search_called": False,
              "tensor_generation_repeated": False, "seconds": time.monotonic() - start}
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["controls", "query", "replay"])
    parser.add_argument("--directory", type=Path)
    parser.add_argument("--scalar-model", type=Path)
    parser.add_argument("--point", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--result", type=Path)
    parser.add_argument("--seconds", type=float, default=30)
    args = parser.parse_args()
    if args.mode == "controls":
        assert not args.output.exists()
        report = controls()
        report["source_sha256"] = base.digest(Path(__file__).read_bytes())
        args.output.write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps(report, indent=2))
    elif args.mode == "query":
        query(args)
    else:
        assert args.result
        replay(args)


if __name__ == "__main__":
    main()

