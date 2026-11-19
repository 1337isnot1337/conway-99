"""Exact integer-quadratic separation for one or two F0 selector orbits.

For an integer population L, (L-k)(L-k-1) is nonnegative. Its expansion
is linear in the existing selector and pair moments. The finite family
contains all 42 single orbits, 861 unions and 861 oriented differences.
No optimizer, eigensolver or graph-symmetry assumption is used.
"""
import argparse
from collections import Counter
from fractions import Fraction
import gzip
import hashlib
from itertools import combinations, product
import json
from math import gcd
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[2]
LOGS = "experiments/logs/root-prism-free/"
INPUTS = {
    "cache": (LOGS + "f0-joint-psd-cache01.json.gz", "6d293340386e77e0bf0b0a7b006744523d75eb7e90ef0fd371c3eed5eb82801e"),
    "cache_cold": (LOGS + "f0-joint-psd-preparation03-cold-replay.json", "e0c8e127ff72714705d7c178b4418e30c5f2cad50bed992a8a8d97b38145a2b4"),
    "parent": (LOGS + "f0-joint-psd-clique-model01.json.gz", "43fff7283308cc2ed1be0936fae4b4f7b264c5961f6e6a4c9a81d123836e4f69"),
    "proposal": (LOGS + "f0-schur-path-query-run01/numerical.json", "bfe03cf2ec0f9d00ee7ff756112a61ab368404d4ed29c7b50377f01c5ae8327e"),
}
VARIABLES = 15200


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def read_input(name):
    path, expected = INPUTS[name]
    raw = (ROOT / path).read_bytes()
    assert sha(raw) == expected, name
    return json.loads(gzip.decompress(raw) if path.endswith(".gz") else raw)


def save_new(path, value):
    raw = canonical(value) + b"\n"
    if str(path).endswith(".gz"):
        raw = gzip.compress(raw, mtime=0)
    with path.open("xb") as handle:
        handle.write(raw)


def load_record(path):
    raw = path.read_bytes()
    return json.loads(gzip.decompress(raw) if str(path).endswith(".gz") else raw)


def normalized(row):
    divisor = gcd(abs(row["rhs"]), *(abs(c) for j, c in row["terms"])) or 1
    return {"terms": [[j, c // divisor] for j, c in row["terms"]], "rhs": row["rhs"] // divisor}


def row_key(row):
    return sha(canonical(normalized(row)))


def form_list():
    return ([[[i, 1]] for i in range(42)]
            + [[[i, 1], [j, 1]] for i, j in combinations(range(42), 2)]
            + [[[i, 1], [j, -1]] for i, j in combinations(range(42), 2)])


def controls():
    checks = 0
    for nplus, nminus in product(range(7), repeat=2):
        for u, v in product(range(nplus + 1), range(nminus + 1)):
            for k in range(-nminus - 1, nplus + 1):
                value = u - v
                expanded = (u * (u - 1) // 2 + v * (v - 1) // 2 - u * v
                            - k * u + (k + 1) * v + k * (k + 1) // 2)
                assert 2 * expanded == (value - k) * (value - k - 1)
                assert expanded >= 0
                checks += 1
    floor_checks = 0
    for numerator in range(-120, 121):
        mean = Fraction(numerator, 7)
        k = mean.numerator // mean.denominator
        # The second moment is constant with respect to the integer shift.
        best = k * (k + 1) - (2 * k + 1) * mean
        assert all(best <= j * (j + 1) - (2 * j + 1) * mean for j in range(-20, 21))
        floor_checks += 1
    return {"integer_population_expansions": checks, "exact_shift_minimizers": floor_checks,
            "no_solver_calls": True}


def prepare_data():
    cache, cold = read_input("cache"), read_input("cache_cold")
    assert cold["status"].startswith("PASS")
    domain = cache["domain"]
    assert sha(canonical(domain)) == cache["domain_sha256"]
    orbits, pairs = domain["selector_orbits"], domain["pairs"]
    assert len(orbits) == 42 and len(pairs) == 114960
    assert sorted(a for orbit in orbits for a in orbit) == list(range(480))
    assert pairs == [list(pair) for pair in combinations(range(480), 2)]
    xmap = {a: i for i, orbit in enumerate(orbits) for a in orbit}
    assert [xmap[a] for a in range(480)] == domain["xmap"]
    sizes = list(map(len, orbits))
    assert Counter(sizes) == {6: 4, 12: 38}
    kept = domain["kept"]
    assert len(kept) == VARIABLES and kept == sorted(set(kept))
    reverse = {old: new for new, old in enumerate(kept)}
    assert all(reverse[j] == j for j in range(5847))
    fixed = set(range(15589)) - set(kept)
    assert len(fixed) == 389 and min(fixed) >= 5847
    blocks = {(i, j): Counter() for i in range(42) for j in range(i, 42)}
    totals = Counter()
    seen = set()
    for orbit_id, orbit in enumerate(domain["pair_orbits"]):
        labels = {tuple(sorted((xmap[pairs[p][0]], xmap[pairs[p][1]]))) for p in orbit}
        assert len(labels) == 1
        label = labels.pop()
        assert all(domain["pmap"][p] == orbit_id for p in orbit)
        assert not (seen & set(orbit))
        seen.update(orbit)
        totals[label] += len(orbit)
        old = 5847 + orbit_id
        if old not in fixed:
            blocks[label][reverse[old]] += len(orbit)
    assert seen == set(range(114960))
    for (i, j), total in totals.items():
        assert total == (sizes[i] * (sizes[i] - 1) // 2 if i == j else sizes[i] * sizes[j])
    block_rows = [{"orbits": [i, j], "terms": [[a, c] for a, c in sorted(blocks[i, j].items())],
                   "literal_pairs": totals[i, j]} for i, j in sorted(blocks)]
    assert sum(len(row["terms"]) for row in block_rows) == 9742 - 389
    assert len(form_list()) == 1764
    return {"schema": "conway99.f0-orbit-integer-quadratic-preparation.v1",
            "source_sha256": sha(Path(__file__).read_bytes()),
            "inputs": {name: {"path": path, "sha256": digest} for name, (path, digest) in INPUTS.items()},
            "selector_orbits": orbits, "selector_orbit_sizes": sizes,
            "pair_population_blocks": block_rows, "literal_pair_coverage": 114960,
            "old_fixed_zero_pair_orbits": 389, "retained_pair_orbits": 9353,
            "forms": form_list(), "forms_count": 1764,
            "family_counts": {"single": 42, "union": 861, "difference": 861},
            "controls": controls(), "optimizer_calls": 0, "proposal_loaded": False,
            "formula": "(L-k)(L-k-1)>=0 for an integer signed population L; average its full quadratic expansion",
            "shift_rule": "k=floor(the exact proposal mean); this minimizes over every integer k for that form",
            "graph_automorphism_assumed": False,
            "single_graph_block_rank_one_constraints_imposed": False,
            "point_feasibility_required_for_cut_validity": False,
            "scope": "Complete stated one/two-orbit finite family only. The earlier path proposal is not a point of the current joint model."}


def make_row(preparation, form, k):
    blocks = {tuple(row["orbits"]): row["terms"] for row in preparation["pair_population_blocks"]}
    terms = Counter()
    for i, w in form:
        assert w in (-1, 1)
        terms[i] += ((2 * k + 1) * w - 1) // 2 * preparation["selector_orbit_sizes"][i]
        for j, c in blocks[i, i]:
            terms[j] -= c
    if len(form) == 2:
        (i, u), (j, v) = form
        for a, c in blocks[i, j]:
            terms[a] -= u * v * c
    return {"terms": [[j, c] for j, c in sorted(terms.items()) if c], "rhs": k * (k + 1) // 2}


def scan(preparation):
    assert preparation["source_sha256"] == sha(Path(__file__).read_bytes())
    assert preparation["forms"] == form_list()
    numerical = read_input("proposal")
    assert numerical["value_valid"] and numerical["numerical_status"] == "HighsModelStatus.kOptimal"
    ratios = [float.fromhex(value).as_integer_ratio() for value in numerical["col_value_hex"]]
    assert len(ratios) == VARIABLES
    denominator = max(b for a, b in ratios)
    assert denominator & (denominator - 1) == 0
    nums = [a * (denominator // b) for a, b in ratios]
    assert all(denominator % b == 0 for a, b in ratios)
    sizes = preparation["selector_orbit_sizes"]
    means = [sizes[i] * nums[i] for i in range(42)]
    assert all(0 <= means[i] <= sizes[i] * denominator for i in range(42))
    blocks = {tuple(row["orbits"]): sum(c * nums[j] for j, c in row["terms"])
              for row in preparation["pair_population_blocks"]}
    parent = read_input("parent")["matrix"]
    existing = set()
    for family in ("equalities", "inequalities"):
        for r in parent[family]:
            for sign in (1, -1) if family == "equalities" else (1,):
                existing.add(row_key({"terms": [[j, sign * c] for j, c in r["terms"]], "rhs": sign * r["rhs"]}))
    attempts, retained, seen = [], [], set()
    for form_id, form in enumerate(preparation["forms"]):
        mean = sum(w * means[i] for i, w in form)
        second = sum(means[i] + 2 * blocks[i, i] for i, w in form)
        if len(form) == 2:
            (i, u), (j, v) = form
            second += 2 * u * v * blocks[i, j]
        k = mean // denominator
        row = make_row(preparation, form, k)
        gap = sum(c * nums[j] for j, c in row["terms"]) - row["rhs"] * denominator
        assert -2 * gap == second - (2 * k + 1) * mean + k * (k + 1) * denominator
        key = row_key(row)
        if gap <= 0:
            disposition = "NONPOSITIVE_EXACT_GAP"
        elif sum(max(c, 0) for j, c in row["terms"]) <= row["rhs"]:
            disposition = "UNIT_BOX_IMPLIED"
        elif key in existing:
            disposition = "EXISTING_PRIMITIVE_PARENT_ROW"
        elif key in seen:
            disposition = "DUPLICATE_NEW_ROW"
        else:
            disposition = "RETAIN_VALID_ROW"
            seen.add(key)
            retained.append({"form_id": form_id, "form": form, "k": k, "row": row,
                             "exact_gap_numerator": str(gap), "row_sha256": key,
                             "strict_nonredundancy_proved": False})
        attempts.append({"form_id": form_id, "mean_numerator": str(mean),
                         "second_moment_numerator": str(second), "k": k,
                         "gap_numerator": str(gap), "row_sha256": key, "disposition": disposition})
    return {"schema": "conway99.f0-orbit-integer-quadratic-scan.v1",
            "status": "COMPLETE_EXACT_FINITE_FAMILY_SCAN",
            "source_sha256": sha(Path(__file__).read_bytes()),
            "preparation_canonical_sha256": sha(canonical(preparation)),
            "proposal_sha256": INPUTS["proposal"][1], "parent_model_sha256": INPUTS["parent"][1],
            "common_denominator": str(denominator), "attempts": attempts, "cuts": retained,
            "disposition_counts": dict(Counter(a["disposition"] for a in attempts)),
            "complete_forms": len(attempts), "all_integer_shifts_covered_by_exact_minimization": True,
            "optimizer_calls": 0, "eigendecompositions": 0,
            "proposal_feasibility_claimed": False, "F0_excluded": False,
            "cut_validity": "Exact integer population product identity; all graph relabelings retain Boolean selectors."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "scan", "replay"))
    parser.add_argument("--preparation", type=Path)
    parser.add_argument("--result", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    started = time.monotonic()
    if args.mode == "prepare":
        result = prepare_data()
    elif args.mode == "scan":
        result = scan(load_record(args.preparation))
    else:
        prep = load_record(args.preparation)
        assert prepare_data() == prep
        expected = scan(prep)
        assert load_record(args.result) == expected
        result = {"status": "PASS: complete exact orbit-population family and all recorded gaps replayed",
                  "source_sha256": sha(Path(__file__).read_bytes()),
                  "preparation_sha256": sha(args.preparation.read_bytes()),
                  "result_sha256": sha(args.result.read_bytes()),
                  "complete_forms": len(expected["attempts"]), "retained_cuts": len(expected["cuts"]),
                  "disposition_counts": expected["disposition_counts"], "optimizer_calls": 0,
                  "eigendecompositions": 0, "seconds": time.monotonic() - started}
    save_new(args.output, result)
    print(json.dumps({"mode": args.mode, "output": str(args.output), "sha256": sha(args.output.read_bytes()),
                      "status": result.get("status", "PREPARED"), "forms": result.get("complete_forms", result.get("forms_count")),
                      "retained": len(result.get("cuts", [])), "dispositions": result.get("disposition_counts"),
                      "seconds": time.monotonic() - started}, indent=2), flush=True)


if __name__ == "__main__":
    main()
