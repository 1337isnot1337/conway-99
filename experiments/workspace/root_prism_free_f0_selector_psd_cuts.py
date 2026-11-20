"""Exact augmented-selector moment cuts; numerical vectors are proposals only.

No linear optimizer is imported or called. Preparation and replay use integers.
The optional scan makes one symmetric eigendecomposition of the full481 matrix.
"""
import argparse
from collections import defaultdict
import gzip
import hashlib
from itertools import combinations, product
import json
import math
import os
from pathlib import Path
import time

for _name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[_name] = "1"

ROOT = Path(__file__).resolve().parents[2]
LOGS = ROOT/"experiments/logs/root-prism-free"
FULL_FILE = "f0-second-moments-preparation02.json.gz"
FULL_FILE_SHA256 = "404d91da35c798ba248887c22a7500957947e24b71d5197dc44432460e6d219e"
REDUCED_FILE = "f0-second-moments-reduced-model.json.gz"
REDUCED_FILE_SHA256 = "73a50b431ac69ad57e10cff9aabe5c0b7d69ee075e95710b461f62b33fe2bbcf"
REDUCED_MODEL_SHA256 = "684b3a646a95d8404bf7b46a3ab170ef88b82e54fdb02aec3a34b8f9613847ae"
POSITIVE_CONTROL_FILE = "f0-incidence-case00-run01/result.json"
POSITIVE_CONTROL_SHA256 = "64d5411e04764b0d7e7157c47b67d759e536a401fee8fe36e274943f2fda4abf"
N, X_ORBITS, PAIR_OFFSET, OLD_VARIABLES = 480, 42, 5847, 15589
MAX_VECTOR_ENTRY = 4096
SCALES = (1, 4, 16, 64, 256, 1024, 4096)
MAX_DIRECTIONS, MAX_CUTS = 8, 32


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode()


def save_new(path, value):
    path = Path(path)
    assert not path.exists()
    path.write_text(json.dumps(value, indent=2)+"\n")


def pair_id(a, b):
    assert a != b
    if a > b:
        a, b = b, a
    return a*(2*N-a-1)//2+b-a-1


def load_domain():
    full_raw, reduced_raw = (LOGS/FULL_FILE).read_bytes(), (LOGS/REDUCED_FILE).read_bytes()
    assert sha(full_raw) == FULL_FILE_SHA256 and sha(reduced_raw) == REDUCED_FILE_SHA256
    full, reduced = json.loads(gzip.decompress(full_raw)), json.loads(gzip.decompress(reduced_raw))
    assert sha(canonical(reduced)) == REDUCED_MODEL_SHA256
    xmap = [-1]*N
    for orbit, members in enumerate(full["selector_orbits"]):
        for a in members:
            assert xmap[a] == -1
            xmap[a] = orbit
    assert min(xmap) >= 0 and len(full["selector_orbits"]) == X_ORBITS
    pairs = list(combinations(range(N), 2))
    assert len(pairs) == 114960
    assert all(pair_id(a, b) == p for p, (a, b) in enumerate(pairs))
    pmap = full["pair_to_orbit"]
    assert len(pmap) == len(pairs) and len(full["pair_orbits"]) == 9742
    for orbit, members in enumerate(full["pair_orbits"]):
        assert members == [p for p in members if pmap[p] == orbit]
    assert sorted(p for members in full["pair_orbits"] for p in members) == list(range(len(pairs)))
    actions = full["selector_actions"]
    action_set = {tuple(g) for g in actions}
    assert len(actions) == len(action_set) == 12 and tuple(range(N)) in action_set
    for g in actions:
        assert sorted(g) == list(range(N))
        for h in actions:
            assert tuple(g[h[a]] for a in range(N)) in action_set
        assert all(xmap[g[a]] == xmap[a] for a in range(N))
        assert all(pmap[pair_id(g[a], g[b])] == pmap[p] for p, (a, b) in enumerate(pairs))
    for members in full["selector_orbits"]:
        assert {g[members[0]] for g in actions} == set(members)
    for members in full["pair_orbits"]:
        a, b = pairs[members[0]]
        assert {pair_id(g[a], g[b]) for g in actions} == set(members)
    assert max(map(len, full["selector_orbits"])) <= 12
    assert max(map(len, full["pair_orbits"])) <= 12
    fixed = reduced["fixed_zero_original_variables"]
    assert len(fixed) == 389
    for j, row in fixed:
        assert PAIR_OFFSET <= j < OLD_VARIABLES
        assert full["matrix"]["equalities"][row]["terms"] == [[j, 1]]
        assert full["matrix"]["equalities"][row]["rhs"] == 0
    kept = reduced["kept_original_variables"]
    assert kept == sorted(set(range(OLD_VARIABLES))-{j for j, row in fixed})
    assert len(kept) == 15200 and kept[:PAIR_OFFSET] == list(range(PAIR_OFFSET))
    reverse = {j: i for i, j in enumerate(kept)}
    return {"full": full, "reduced": reduced, "pairs": pairs, "xmap": xmap, "pmap": pmap,
            "actions": actions, "kept": kept, "reverse": reverse,
            "fixed": {j for j, row in fixed}}


def primitive_vector(vector):
    assert len(vector) == N+1 and all(type(v) is int for v in vector)
    assert any(vector) and max(map(abs, vector)) <= MAX_VECTOR_ENTRY
    divisor = math.gcd(*vector)
    assert divisor > 0
    vector = [v//divisor for v in vector]
    if next(v for v in vector if v) < 0:
        vector = [-v for v in vector]
    return vector


def literal_coefficients(vector):
    c, v = vector[0], vector[1:]
    diagonal = [-a*a-2*c*a for a in v]
    off_diagonal = [-2*v[a]*v[b] for a in range(len(v)) for b in range(a+1, len(v))]
    return diagonal, off_diagonal, c*c


def raw_quotient(domain, vector):
    diagonal, off, rhs = literal_coefficients(vector)
    terms = defaultdict(int)
    for a, value in enumerate(diagonal):
        terms[domain["xmap"][a]] += value
    for p, value in enumerate(off):
        terms[PAIR_OFFSET+domain["pmap"][p]] += value
    # An independent orbit-sum expression checks every aggregated coefficient.
    for o, members in enumerate(domain["full"]["selector_orbits"]):
        assert terms[o] == -sum(vector[a+1]**2+2*vector[0]*vector[a+1] for a in members)
    for o, members in enumerate(domain["full"]["pair_orbits"]):
        assert terms[PAIR_OFFSET+o] == -2*sum(vector[domain["pairs"][p][0]+1]*
                                                    vector[domain["pairs"][p][1]+1] for p in members)
    assert all(abs(c) <= 36*MAX_VECTOR_ENTRY**2 for c in terms.values())
    reduced = sorted((domain["reverse"][j], c) for j, c in terms.items()
                     if c and j not in domain["fixed"])
    assert all(j < X_ORBITS or j >= PAIR_OFFSET for j, c in reduced)
    return reduced, rhs, {"literal_diagonal_sha256": sha(canonical(diagonal)),
                         "literal_off_diagonal_sha256": sha(canonical(off)),
                         "zero_coordinates_substituted": len(domain["fixed"])}


def cut(domain, vector):
    vector = primitive_vector(vector)
    terms, rhs, literal = raw_quotient(domain, vector)
    divisor = math.gcd(rhs, *(abs(c) for j, c in terms))
    divisor = divisor or 1
    row = {"terms": [[j, c//divisor] for j, c in terms], "rhs": rhs//divisor}
    assert rhs % divisor == 0 and all(c % divisor == 0 for j, c in terms)
    return {"vector": vector, "row": row, "positive_divisor": divisor, **literal,
            "unit_box_implied": sum(max(c, 0) for j, c in row["terms"]) <= row["rhs"]}


def rational_proposal(numeric):
    assert numeric["model_sha256"] == REDUCED_MODEL_SHA256
    values = [float.fromhex(v) for v in numeric["col_value_hex"]]
    assert len(values) == 15200 and all(math.isfinite(v) for v in values)
    ratios = [v.as_integer_ratio() for v in values]
    denominator = max(d for a, d in ratios)
    assert denominator > 0 and denominator & (denominator-1) == 0
    assert all(denominator % d == 0 for a, d in ratios)
    return denominator, [a*(denominator//d) for a, d in ratios], values


def exact_violation(domain, certificate, denominator, numerators):
    row = certificate["row"]
    gap = sum(c*numerators[j] for j, c in row["terms"])-row["rhs"]*denominator
    # Compute the squared-linear-form expansion separately in all480 coordinates.
    old = [0]*OLD_VARIABLES
    for j, value in zip(domain["kept"], numerators):
        old[j] = value
    c, v = certificate["vector"][0], certificate["vector"][1:]
    quadratic = c*c*denominator
    quadratic += sum((v[a]*v[a]+2*c*v[a])*old[domain["xmap"][a]] for a in range(N))
    quadratic += 2*sum(v[a]*v[b]*old[PAIR_OFFSET+domain["pmap"][p]]
                       for p, (a, b) in enumerate(domain["pairs"]))
    assert quadratic == -certificate["positive_divisor"]*gap
    return {"violated": gap > 0, "gap_numerator": str(gap), "denominator": str(denominator),
            "literal_quadratic_numerator": str(quadratic),
            "proposal_feasibility_claimed": False}


def basic_controls():
    count = 0
    for n in range(1, 5):
        for vector in product((-1, 0, 1), repeat=n+1):
            diagonal, off, rhs = literal_coefficients(vector)
            pairs = list(combinations(range(n), 2))
            for binary in product((0, 1), repeat=n):
                lhs = sum(a*z for a, z in zip(diagonal, binary))
                lhs += sum(c*binary[a]*binary[b] for c, (a, b) in zip(off, pairs))
                square = (vector[0]+sum(a*z for a, z in zip(vector[1:], binary)))**2
                assert rhs-lhs == square >= 0
                count += 1
    # A non-PSD proposal may be separated without being assumed feasible.
    vector = (0, 1, -1)
    diagonal, off, rhs = literal_coefficients(vector)
    x, z = (1, 1), 2
    lhs = sum(c*v for c, v in zip(diagonal, x))+off[0]*z
    assert lhs > rhs
    return {"status": "PASS: literal square identities", "Boolean_evaluations": count,
            "infeasible_proposal_can_suggest_valid_cut": True, "optimizer_calls": 0,
            "eigendecompositions": 0}


def domain_controls(domain):
    raw = (LOGS/POSITIVE_CONTROL_FILE).read_bytes()
    assert sha(raw) == POSITIVE_CONTROL_SHA256
    selected = json.loads(raw)["incidence_witness"]["selected_columns"]
    assert len(selected) == len(set(selected)) == 60
    zero_pairs = {domain["pairs"][c["pair_id"]] for c in domain["full"]["zero_moment_certificates"]}
    assert all(not ({a, b} <= set(selected)) for a, b in zero_pairs)
    samples = [[], [0], selected]
    vectors = [
        [1]+[int(a % 17 == 0)-int(a % 19 == 0) for a in range(N)],
        [-2]+[(a % 5)-2 for a in range(N)],
        [7]+[int(a in selected)*3-int(a % 7 == 0) for a in range(N)],
    ]
    checks, transports = 0, 0
    for vector in vectors:
        certificate = cut(domain, vector)
        for g in domain["actions"]:
            moved = [vector[0]]+[0]*N
            for a in range(N):
                moved[g[a]+1] = vector[a+1]
            assert cut(domain, moved)["row"] == certificate["row"]
            transports += 1
        for sample in samples:
            images = [{g[a] for a in sample} for g in domain["actions"]]
            old = [0]*OLD_VARIABLES
            for o, members in enumerate(domain["full"]["selector_orbits"]):
                values = {sum(a in image for image in images) for a in members}
                assert len(values) == 1
                old[o] = values.pop()
            for o, members in enumerate(domain["full"]["pair_orbits"]):
                a, b = domain["pairs"][members[0]]
                old[PAIR_OFFSET+o] = sum(a in image and b in image for image in images)
            assert all(old[j] == 0 for j in domain["fixed"])
            values = [old[j] for j in domain["kept"]]
            check = exact_violation(domain, certificate, len(images), values)
            expected = sum((certificate["vector"][0]+sum(certificate["vector"][a+1] for a in image))**2
                           for image in images)
            assert int(check["literal_quadratic_numerator"]) == expected >= 0
            assert not check["violated"]
            checks += 1
    return {"status": "PASS: full480 averaged-square controls", "full_domain_controls": checks,
            "literal_group_transports": transports, "zero_substitution_checked": True,
            "full_linear_feasibility_claimed_for_controls": False, "optimizer_calls": 0,
            "eigendecompositions": 0}


def preparation():
    domain = load_domain()
    return {"status": "PASS: exact augmented-selector PSD extraction prepared; no production scan",
            "source_sha256": sha(Path(__file__).read_bytes()),
            "inputs": {FULL_FILE: FULL_FILE_SHA256, REDUCED_FILE: REDUCED_FILE_SHA256,
                       POSITIVE_CONTROL_FILE: POSITIVE_CONTROL_SHA256},
            "counts": {"full_selectors": N, "augmented_order": N+1, "distinct_full_pairs": 114960,
                       "selector_orbits": X_ORBITS, "pair_orbits": 9742, "zero_orbits": 389,
                       "reduced_variables": 15200},
            "basic_controls": basic_controls(), "domain_controls": domain_controls(domain),
            "planned_scan_limits": {"eigendecompositions": 1, "directions": MAX_DIRECTIONS,
                                   "rounding_scales": SCALES, "retained_cuts": MAX_CUTS,
                                   "maximum_integer_vector_entry": MAX_VECTOR_ENTRY},
            "raw_quotient_coefficient_absolute_bound": 36*MAX_VECTOR_ENTRY**2,
            "all_raw_cut_coefficients_exact_in_binary64": True,
            "proposal_must_be_exactly_feasible": False, "PSD_feasibility_certified": False,
            "linear_optimizer_calls": 0}


def scan(preparation_path, numeric_path, output, seconds):
    assert 0 < seconds <= 60 and not Path(output).exists()
    started = time.monotonic()
    prepared = json.loads(Path(preparation_path).read_text())
    assert prepared["source_sha256"] == sha(Path(__file__).read_bytes())
    assert prepared["inputs"] == {FULL_FILE: FULL_FILE_SHA256, REDUCED_FILE: REDUCED_FILE_SHA256,
                                 POSITIVE_CONTROL_FILE: POSITIVE_CONTROL_SHA256}
    domain = load_domain()
    raw = Path(numeric_path).read_bytes()
    numeric = json.loads(raw)
    denominator, numerators, values = rational_proposal(numeric)
    import numpy as np
    old = np.zeros(OLD_VARIABLES, dtype=float)
    old[domain["kept"]] = values
    matrix = np.zeros((N+1, N+1), dtype=float)
    matrix[0, 0] = 1.0
    for a in range(N):
        matrix[0, a+1] = matrix[a+1, 0] = matrix[a+1, a+1] = old[domain["xmap"][a]]
    for p, (a, b) in enumerate(domain["pairs"]):
        matrix[a+1, b+1] = matrix[b+1, a+1] = old[PAIR_OFFSET+domain["pmap"][p]]
    assert np.isfinite(matrix).all()
    result = {"status": "RUNNING: numerical proposal, exact valid-cut acceptance",
              "source_sha256": sha(Path(__file__).read_bytes()),
              "preparation_sha256": sha(Path(preparation_path).read_bytes()),
              "numerical_file_sha256": sha(raw), "numerical_source_sha256": numeric.get("source_sha256"),
              "model_sha256": REDUCED_MODEL_SHA256,
              "proposing_status": numeric.get("numerical_status"), "proposing_value_valid": numeric.get("value_valid"),
              "proposal_feasibility_claimed": False, "eigendecompositions": 0,
              "optimizer_calls": 0, "cuts": [], "attempts": [], "PSD_certified": False}
    if time.monotonic()-started >= seconds:
        result["status"] = "UNKNOWN: setup exhausted spectral-scan allowance"
    else:
        eigenvalues, eigenvectors = np.linalg.eigh(matrix)
        result["eigendecompositions"] = 1
        result["lowest_numerical_eigenvalues_hex"] = [float(v).hex() for v in eigenvalues[:MAX_DIRECTIONS]]
        seen = set()
        stop = False
        for direction in range(MAX_DIRECTIONS):
            if eigenvalues[direction] >= 0:
                continue
            eigenvector = eigenvectors[:, direction]
            maximum = max(abs(float(v)) for v in eigenvector)
            assert maximum > 0
            for scale in SCALES:
                if time.monotonic()-started >= seconds or len(result["cuts"]) >= MAX_CUTS:
                    stop = True
                    break
                vector = [int(round(scale*float(v)/maximum)) for v in eigenvector]
                certificate = cut(domain, vector)
                key = canonical(certificate["row"])
                if key in seen:
                    continue
                seen.add(key)
                check = exact_violation(domain, certificate, denominator, numerators)
                record = {"direction": direction, "scale": scale, "row_sha256": sha(key),
                          "unit_box_implied": certificate["unit_box_implied"], **check}
                result["attempts"].append(record)
                if check["violated"] and not certificate["unit_box_implied"]:
                    result["cuts"].append({"certificate": certificate, "proposing_check": check,
                                           "direction": direction, "scale": scale})
            if stop:
                break
        result["status"] = ("EXACT_VALID_PSD_CUTS_FOUND; no feasibility conclusion" if result["cuts"]
                            else "NO_RETAINED_CUT; no PSD or feasibility conclusion")
        result["scan_stopped_at_limit"] = stop
    result["elapsed_seconds"] = time.monotonic()-started
    result["requested_seconds"] = seconds
    result["cooperative_overrun_seconds"] = max(0, result["elapsed_seconds"]-seconds)
    save_new(output, result)
    return result


def replay(preparation_path, numeric_path, result_path):
    domain = load_domain()
    result = json.loads(Path(result_path).read_text())
    assert result["source_sha256"] == sha(Path(__file__).read_bytes())
    assert result["preparation_sha256"] == sha(Path(preparation_path).read_bytes())
    raw = Path(numeric_path).read_bytes()
    assert result["numerical_file_sha256"] == sha(raw)
    denominator, numerators, values = rational_proposal(json.loads(raw))
    assert result["optimizer_calls"] == 0 and result["PSD_certified"] is False
    assert result["proposal_feasibility_claimed"] is False
    for item in result["cuts"]:
        certificate = cut(domain, item["certificate"]["vector"])
        assert certificate == item["certificate"] and not certificate["unit_box_implied"]
        check = exact_violation(domain, certificate, denominator, numerators)
        assert check == item["proposing_check"] and check["violated"]
    return {"status": "PASS: all retained cuts follow exact augmented-square identities",
            "result_sha256": sha(Path(result_path).read_bytes()), "cuts_replayed": len(result["cuts"]),
            "full_selectors": N, "full_pair_positions": 114960, "optimizer_calls": 0,
            "eigendecompositions": 0, "proposal_feasibility_claimed": False,
            "model_infeasibility_claimed": False, "PSD_feasibility_certified": False}


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="mode", required=True)
    p = sub.add_parser("prepare")
    p.add_argument("--output", type=Path, required=True)
    p = sub.add_parser("scan")
    p.add_argument("--preparation", type=Path, required=True)
    p.add_argument("--numeric", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--seconds", type=float, default=60)
    p = sub.add_parser("replay")
    p.add_argument("--preparation", type=Path, required=True)
    p.add_argument("--numeric", type=Path, required=True)
    p.add_argument("--result", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.mode == "prepare":
        record = preparation()
        save_new(args.output, record)
    elif args.mode == "scan":
        record = scan(args.preparation, args.numeric, args.output, args.seconds)
    else:
        record = replay(args.preparation, args.numeric, args.result)
        save_new(args.output, record)
    print(json.dumps({k: v for k, v in record.items() if k not in ("cuts", "attempts")}, indent=2))


if __name__ == "__main__":
    main()

