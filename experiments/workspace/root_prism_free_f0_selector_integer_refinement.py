"""Integer refinements of every previously retained selector PSD direction.

For L=sum_a w_a x_a with integer w and Boolean x, (L-k)(L-k-1)>=0.
The shifts -1 and0 imply the old L^2>=0 row by addition. A third shift
minimizes the exact quadratic at the earlier saved path proposal.
No eigensolver, optimizer or new direction search is used.
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
LOGS = ROOT / "experiments/logs/root-prism-free"
INPUTS = {
    "old_directions": ("f0-selector-psd-cuts-scan01.json.gz", "5c74497bb70d44bf2fac7002ed16b4657500c4af2518cab196684c9346449e79"),
    "new_directions": ("f0-joint-psd-zero-scan02.json.gz", "43e590c801ccb85e385253cc475ce6f6bdc09874d10b9c7571170cb2bd06d9a3"),
    "cache": ("f0-joint-psd-cache01.json.gz", "6d293340386e77e0bf0b0a7b006744523d75eb7e90ef0fd371c3eed5eb82801e"),
    "cache_cold": ("f0-joint-psd-preparation03-cold-replay.json", "e0c8e127ff72714705d7c178b4418e30c5f2cad50bed992a8a8d97b38145a2b4"),
    "proposal": ("f0-schur-path-query-run01/numerical.json", "bfe03cf2ec0f9d00ee7ff756112a61ab368404d4ed29c7b50377f01c5ae8327e"),
    "parent": ("f0-joint-psd-clique-model01.json.gz", "43fff7283308cc2ed1be0936fae4b4f7b264c5961f6e6a4c9a81d123836e4f69"),
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def read(name):
    path, expected = INPUTS[name]
    raw = (LOGS / path).read_bytes()
    assert sha(raw) == expected
    return json.loads(gzip.decompress(raw) if path.endswith(".gz") else raw)


def normalize(terms, rhs):
    terms = [[j, c] for j, c in sorted(terms.items()) if c]
    divisor = gcd(abs(rhs), *(abs(c) for j, c in terms)) or 1
    return {"terms": [[j, c // divisor] for j, c in terms], "rhs": rhs // divisor}, divisor


def row_key(row):
    return sha(canonical(normalize(dict(row["terms"]), row["rhs"])[0]))


def controls():
    count = 0
    for w in product(range(-2, 3), repeat=3):
        for x in product((0, 1), repeat=3):
            value = sum(a * b for a, b in zip(w, x))
            square = sum(w[i] ** 2 * x[i] for i in range(3))
            square += 2 * sum(w[i] * w[j] * x[i] * x[j] for i, j in combinations(range(3), 2))
            assert square == value ** 2
            for k in range(-7, 8):
                lhs = sum(((2 * k + 1) * w[i] - w[i] ** 2) // 2 * x[i] for i in range(3))
                lhs -= sum(w[i] * w[j] * x[i] * x[j] for i, j in combinations(range(3), 2))
                rhs = k * (k + 1) // 2
                assert 2 * (rhs - lhs) == (value - k) * (value - k - 1) >= 0
                count += 1
    return {"all_general_integer_weight_expansions": count, "solver_calls": 0}


def build():
    old, new, cache, cold, proposal, parent = [read(name) for name in INPUTS]
    assert cold["status"].startswith("PASS")
    domain = cache["domain"]
    assert sha(canonical(domain)) == cache["domain_sha256"]
    orbits, pairs = domain["selector_orbits"], domain["pairs"]
    assert len(orbits) == 42 and len(pairs) == 114960
    xmap, kept, pmap = domain["xmap"], domain["kept"], domain["pmap"]
    reverse = {old: new for new, old in enumerate(kept)}
    assert len(reverse) == 15200 and all(reverse[j] == j for j in range(5847))
    fixed = set(range(15589)) - set(kept)
    assert len(fixed) == 389
    assert proposal["value_valid"] and proposal["numerical_status"] == "HighsModelStatus.kOptimal"
    values = [Fraction.from_float(float.fromhex(v)) for v in proposal["col_value_hex"]]
    assert len(values) == 15200
    existing = set()
    matrix = parent["matrix"]
    zeros = {r["terms"][0][0] for r in matrix["equalities"] if r["rhs"] == 0 and len(r["terms"]) == 1}
    assert len(zeros) == 162 and all(42 <= j < 5847 for j in zeros)
    for family in ("equalities", "inequalities"):
        for r in matrix[family]:
            for sign in ((1, -1) if family == "equalities" else (1,)):
                projected = {"terms": [[j, sign * c] for j, c in r["terms"] if j not in zeros], "rhs": sign * r["rhs"]}
                existing.add(row_key(projected))
    directions = [("old", i, c) for i, c in enumerate(old["cuts"])]
    directions += [("new", i, c) for i, c in enumerate(new["cuts"]) if c["family"] == "selector"]
    assert len(directions) == 48
    audit, refinements, seen, implications = [], [], set(), []
    for source, index, cut in directions:
        cert = cut["certificate"]
        vector = cert["vector"]
        assert len(vector) == 481 and vector[0] == 0 and all(type(a) is int for a in vector)
        weights = vector[1:]
        mean_terms = {i: sum(weights[a] for a in orbit) for i, orbit in enumerate(orbits)}
        mean_terms = {i: c for i, c in mean_terms.items() if c}
        direction = {"source": source, "index": index, "vector_sha256": sha(canonical(vector)),
                     "nonzero_orbit_mean_coefficients": [[i, c] for i, c in sorted(mean_terms.items())]}
        if not mean_terms:
            direction["disposition"] = "IDENTICALLY_ZERO_MEAN_ALL_SHIFTS_IMPLIED_BY_HELD_PSD"
            direction["reason"] = "E[L]=0 identically; the minimum integer-shift value is E[L^2] at k=-1 or0."
            audit.append(direction)
            continue
        square = Counter()
        for a, w in enumerate(weights):
            square[xmap[a]] += w * w
        for p, (a, b) in enumerate(pairs):
            c = 2 * weights[a] * weights[b]
            old_col = 5847 + pmap[p]
            if c and old_col not in fixed:
                square[reverse[old_col]] += c
        square = {j: c for j, c in square.items() if c}
        divisor = cert["positive_divisor"]
        assert type(divisor) is int and divisor > 0 and cert["row"]["rhs"] == 0
        assert square == {j: -divisor * c for j, c in cert["row"]["terms"]}
        mean = sum(c * values[j] for j, c in mean_terms.items())
        second = sum(c * values[j] for j, c in square.items())
        kbest = mean.numerator // mean.denominator
        shifts = sorted({-1, 0, kbest})
        direction.update(disposition="REFINE_NONZERO_MEAN", exact_proposal_mean=str(mean),
                         exact_proposal_second_moment=str(second), shifts=shifts,
                         original_PSD_divisor=divisor, literal_square_rebuilt=True)
        audit.append(direction)
        raw_rows = {}
        for k in shifts:
            terms = {j: (2 * k + 1) * mean_terms.get(j, 0) - square.get(j, 0)
                     for j in set(mean_terms) | set(square)}
            assert all(c % 2 == 0 for c in terms.values())
            terms = {j: c // 2 for j, c in terms.items() if c}
            rhs = k * (k + 1) // 2
            row, normalization = normalize(terms, rhs)
            raw_rows[k] = (terms, rhs, row, normalization)
            gap = sum(c * values[j] for j, c in row["terms"]) - row["rhs"]
            assert 2 * normalization * gap == (2 * k + 1) * mean - second - k * (k + 1)
            key = row_key(row)
            disposition = ("EXISTING_ROW_AFTER_PROVED_ZEROS" if key in existing else
                           "DUPLICATE_REFINEMENT" if key in seen else "RETAIN_VALID_INTEGER_REFINEMENT")
            seen.add(key)
            refinements.append({"source": source, "index": index, "k": k, "row": row,
                                "positive_normalization": normalization, "row_sha256": key,
                                "exact_proposal_gap": str(gap), "disposition": disposition,
                                "strict_nonredundancy_in_full_parent_proved": False})
        summed = Counter(raw_rows[-1][0])
        for j, c in raw_rows[0][0].items():
            summed[j] += c
        assert all(summed.get(j, 0) == -square.get(j, 0) for j in range(15200))
        assert raw_rows[-1][1] == raw_rows[0][1] == 0
        implications.append({"source": source, "index": index,
                             "identity": "g_minus*new_minus + g_zero*new_zero = old_divisor*held_PSD_row",
                             "g_minus": raw_rows[-1][3], "g_zero": raw_rows[0][3],
                             "old_divisor": divisor, "all15200_coefficients_checked": True})
    assert sum(a["disposition"].startswith("IDENTICALLY") for a in audit) == 37
    assert len(implications) == 11
    return {"schema": "conway99.f0-selector-integer-refinement.v1",
            "status": "COMPLETE_EXACT_INTEGER_REFINEMENT_OF_HELD_SELECTOR_DIRECTIONS",
            "source_sha256": sha(Path(__file__).read_bytes()),
            "inputs": {k: {"path": str(Path("experiments/logs/root-prism-free") / p), "sha256": h}
                       for k, (p, h) in INPUTS.items()},
            "controls": controls(), "held_directions": 48, "zero_mean_directions": 37,
            "nonzero_mean_directions": 11, "direction_audit": audit,
            "refinements": refinements, "held_row_implication_certificates": implications,
            "disposition_counts": dict(Counter(r["disposition"] for r in refinements)),
            "exact_positive_gaps_at_earlier_path_proposal": sum(Fraction(r["exact_proposal_gap"]) > 0 for r in refinements),
            "optimizer_calls": 0, "eigendecompositions": 0,
            "graph_automorphism_assumed": False, "proposal_feasibility_claimed": False,
            "F0_excluded": False,
            "theorem": "For integer L, (L-k)(L-k-1)>=0. Boolean expansion and averaging yield each retained linear row.",
            "scope": "All48 held selector PSD directions; shifts -1 and0, plus the exact earlier-proposal optimum. Other integer directions and all graph-Schur families are outside this scope."}


def save_new(path, value):
    raw = canonical(value) + b"\n"
    if str(path).endswith(".gz"):
        raw = gzip.compress(raw, mtime=0)
    with path.open("xb") as handle:
        handle.write(raw)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "replay"))
    parser.add_argument("--record", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    started = time.monotonic()
    result = build()
    if args.mode == "replay":
        raw = args.record.read_bytes()
        saved = json.loads(gzip.decompress(raw) if str(args.record).endswith(".gz") else raw)
        assert saved == result
        result = {"status": "PASS: every literal square, integer refinement, exact gap and held-row implication replayed",
                  "source_sha256": sha(Path(__file__).read_bytes()), "record_sha256": sha(raw),
                  "held_directions": 48, "refinement_rows": len(saved["refinements"]),
                  "all11_held_row_implications_checked": True,
                  "optimizer_calls": 0, "eigendecompositions": 0, "seconds": time.monotonic() - started}
    save_new(args.output, result)
    print(json.dumps({"status": result["status"], "sha256": sha(args.output.read_bytes()),
                      "rows": len(result.get("refinements", [])), "counts": result.get("disposition_counts"),
                      "positive_gaps": result.get("exact_positive_gaps_at_earlier_path_proposal"),
                      "seconds": time.monotonic() - started}, indent=2), flush=True)


if __name__ == "__main__":
    main()
