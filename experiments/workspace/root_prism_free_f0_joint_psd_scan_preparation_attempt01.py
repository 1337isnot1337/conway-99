"""One cached three-family PSD separation at a fixed numerical proposal.

Preparation projects certified domain records; it does not rebuild any Schur
kernel or call a numerical optimizer/eigensolver. The separately gated scan
uses one decomposition per family. Exact integer inequalities, independently
expanded literal quadratic forms, and exact dyadic proposal gaps decide cuts.
"""
import argparse
from collections import Counter
from fractions import Fraction
import gzip
import hashlib
from itertools import combinations
import json
import math
import os
from pathlib import Path
import time

for _name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[_name] = "1"

import root_prism_free_f0_selector_psd_cuts as selector
import root_prism_free_f0_full_core_schur_cuts as schur

ROOT = Path(__file__).resolve().parents[2]
LOGS = ROOT/"experiments/logs/root-prism-free"
N, PAIR_OFFSET, OLD_VARIABLES, VARIABLES = 480, 5847, 15589, 15200
FAMILIES = ("selector", "plus", "minus")
SCALES = (1, 4, 16, 64, 256, 1024)
MAX_VECTOR, DIRECTIONS, PER_FAMILY, TOTAL_CUTS, SCAN_SECONDS = 1024, 8, 16, 48, 60
SOURCE_INPUTS = {
    "root_prism_free_f0_selector_psd_cuts.py": "64fa05e1947ac0e59801a400e0b9ee61e3c08691156025509c7390732db8bab2",
    "root_prism_free_f0_full_core_schur_cuts.py": "c5489561a99de14cc0c68a3d05dbc8eb1eb3fc17e4a759b4c3d63f8d771f7d8e",
    "root_prism_free_f0_graph_schur_kernels.py": "5be66e563e53b1efc378c8adbeb39b8ddbf24f4c97077e5d43c728260d9087be",
    "root_prism_free_f0_full_core_schur_kernels.py": "141392693e8d4b7e140c329cfa4128b8794bd376713558394ef014975e2fc63f",
}
INPUTS = {
    "baseline": ("f0-boolean-fractional-model.json.gz", "703206929c9c85a40ac4ddcbfb1708c716c288482cf50c77a32249404e35b782"),
    "full": ("f0-second-moments-preparation02.json.gz", "404d91da35c798ba248887c22a7500957947e24b71d5197dc44432460e6d219e"),
    "reduced": ("f0-second-moments-reduced-model.json.gz", "73a50b431ac69ad57e10cff9aabe5c0b7d69ee075e95710b461f62b33fe2bbcf"),
    "old_kernel": ("f0-graph-schur-kernels01.json.gz", "65f1ad0d0015a6eff3d97c676fb0e188f57f9dee00e9245758a28bab2069b40d"),
    "kernel": ("f0-full-core-schur-kernels01.json.gz", "a49b8309032b2c599c637285f4a4584bb7d55659640e594df1e6fdd50bf826c1"),
    "kernel_cold": ("f0-full-core-schur-cuts-preparation01-cold-replay.json", "5450f1fe4b61002d58f8926ae92ad48abba9f653b53bfa372cf550973248e919"),
    "inverse_audit": ("f0-full-core-schur-independent-audit.json", "d8031c629bfb9f5b050c55e218b872aa68a0de08a84abff99da5e029fe572c75"),
    "inverse_cold": ("f0-full-core-schur-independent-audit-replay.json", "a857d12d96798f4ad58d8fb8ebbac8b7980b1b672e480e89c19262588f904cf0"),
    "model": ("f0-schur-path-model03.json.gz", "ad046fc05a4247a081b3cabb16693682fa5539ff557dd7b599f3c3a63e7303dd"),
    "proposal": ("f0-schur-path-query-run01/numerical.json", "bfe03cf2ec0f9d00ee7ff756112a61ab368404d4ed29c7b50377f01c5ae8327e"),
}
MODEL_SHA = "7bc4682e3df009761c55d0740a30a0629d45e894807f79e3337fc1de4fa1aff3"
MATRIX_SHA = "24da97cfaf7bdb6e73efcdf9b248d70f30e04443dada5a2c923ab112f10bc812"
KERNEL_RAW_SHA = "a963a88606a9fad78576d711f6ef7bf67eb03032176cebc2af5af700ea7c6708"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode()


def load_json(path):
    raw = Path(path).read_bytes()
    return json.loads(gzip.decompress(raw) if str(path).endswith(".gz") else raw)


def save_new(path, value):
    path = Path(path)
    assert not path.exists()
    raw = canonical(value) if path.suffix == ".gz" else (json.dumps(value, indent=2)+"\n").encode()
    path.write_bytes(gzip.compress(raw, mtime=0) if path.suffix == ".gz" else raw)


def tick(deadline):
    if time.monotonic() >= deadline:
        raise TimeoutError("joint PSD separation cooperative limit")


def bindings():
    for name, expected in SOURCE_INPUTS.items():
        assert sha(Path(__file__).with_name(name).read_bytes()) == expected, name
    return {"source_sha256": sha(Path(__file__).read_bytes()),
            "reused_source_sha256": SOURCE_INPUTS,
            "inputs": {k: list(v) for k, v in INPUTS.items()},
            "model_sha256": MODEL_SHA, "matrix_sha256": MATRIX_SHA}


def read_input(key):
    filename, expected = INPUTS[key]
    raw = (LOGS/filename).read_bytes()
    assert sha(raw) == expected, key
    plain = gzip.decompress(raw) if filename.endswith(".gz") else raw
    if key == "kernel":
        assert sha(plain) == KERNEL_RAW_SHA
    return json.loads(plain)


def orbit_map(orbits, size):
    result = [-1]*size
    for index, members in enumerate(orbits):
        assert members and members == sorted(set(members)) and len(members) <= 12
        for a in members:
            assert 0 <= a < size and result[a] == -1
            result[a] = index
    assert min(result) >= 0
    return result


def normalized_row(row):
    terms, rhs = row["terms"], row["rhs"]
    assert type(rhs) is int
    assert terms == sorted(terms) and len({j for j, c in terms}) == len(terms)
    assert all(type(j) is int and 0 <= j < VARIABLES and type(c) is int and c for j, c in terms)
    divisor = math.gcd(abs(rhs), *(abs(c) for j, c in terms)) or 1
    return {"terms": [[j, c//divisor] for j, c in terms], "rhs": rhs//divisor}


def row_key(row):
    return sha(canonical(normalized_row(row)))


def existing_rows(model):
    matrix = model["matrix"]
    assert model["matrix_sha256"] == sha(canonical(matrix)) == MATRIX_SHA
    assert matrix["variables"] == VARIABLES
    assert matrix["lower"] == [0]*VARIABLES and matrix["upper"] == [1]*VARIABLES
    assert len(matrix["equalities"]) == 6135 and len(matrix["inequalities"]) == 21629
    result = {}
    for kind in ("equalities", "inequalities"):
        for index, row in enumerate(matrix[kind]):
            for sign in ((1, -1) if kind == "equalities" else (1,)):
                oriented = {"terms": [[j, sign*c] for j, c in row["terms"]], "rhs": sign*row["rhs"]}
                result.setdefault(row_key(oriented), []).append([kind, index, sign])
    return [[key, result[key]] for key in sorted(result)]


def project_cache():
    """Project existing records and check indexing, never rebuild a kernel."""
    bound = bindings()
    baseline = read_input("baseline")["validation"]
    full = read_input("full")
    reduced = read_input("reduced")
    old = read_input("old_kernel")["domain"]
    kernel = read_input("kernel")
    cold, inverse, inverse_cold = (read_input(k) for k in ("kernel_cold", "inverse_audit", "inverse_cold"))
    assert cold["kernel_file_sha256"] == INPUTS["kernel"][1]
    assert cold["kernel_raw_sha256"] == KERNEL_RAW_SHA and cold["status"].startswith("PASS")
    assert inverse_cold["record_sha256"] == INPUTS["inverse_audit"][1] and inverse_cold["status"].startswith("PASS")
    assert cold["independent_full_core_audit_record_sha256"] == INPUTS["inverse_audit"][1]
    assert inverse["status"].startswith("PASS")
    core, triples, edges = baseline["core"], baseline["triples"], baseline["edges"]
    assert len(core) == 21 and len(triples) == N and len(edges) == 68394
    assert triples == sorted(triples) and len({tuple(h) for h in triples}) == N
    assert all(h == sorted(set(h)) and len(h) == 3 and 0 <= h[0] <= h[-1] < 18 for h in triples)
    assert edges == sorted(edges) and len({tuple(e) for e in edges}) == len(edges)
    assert all(0 <= a < b < N for a, b in edges)
    assert all(not (core[i] >> i & 1) for i in range(21))
    assert all((core[i] >> j & 1) == (core[j] >> i & 1) for i in range(21) for j in range(21))
    adjacency = [[core[i+3] >> (j+3) & 1 for j in range(18)] for i in range(18)]
    pairs = [list(p) for p in combinations(range(N), 2)]
    xo, eo, po = baseline["selector_orbits"], baseline["edge_orbits"], full["pair_orbits"]
    assert xo == full["selector_orbits"] and (len(xo), len(eo), len(po)) == (42, 5805, 9742)
    xmap, emap, pmap = orbit_map(xo, N), orbit_map(eo, len(edges)), orbit_map(po, len(pairs))
    assert pmap == full["pair_to_orbit"]
    actions, core_actions = full["selector_actions"], old["reconstructed21_core_actions"]
    group = set(map(tuple, actions))
    assert len(actions) == len(group) == len(core_actions) == 12 and tuple(range(N)) in group
    for g, cg in zip(actions, core_actions):
        assert sorted(g) == list(range(N)) and sorted(cg) == list(range(21))
        assert sorted(cg[:3]) == [0, 1, 2]
        assert all((core[i] >> j & 1) == (core[cg[i]] >> cg[j] & 1) for i in range(21) for j in range(21))
        assert all(sorted(cg[i+3]-3 for i in triples[a]) == triples[g[a]] for a in range(N))
        assert all(tuple(g[h[a]] for a in range(N)) in group for h in actions)
    edge_index = {tuple(e): i for i, e in enumerate(edges)}
    # Complete partition + the full group orbit of every representative proves
    # invariance on every member, without rerunning the eligibility census.
    for members in xo:
        assert {g[members[0]] for g in actions} == set(members)
    for members in eo:
        a, b = edges[members[0]]
        assert {edge_index[tuple(sorted((g[a], g[b])))] for g in actions} == set(members)
    for members in po:
        a, b = pairs[members[0]]
        assert {selector.pair_id(g[a], g[b]) for g in actions} == set(members)
    fixed = reduced["fixed_zero_original_variables"]
    assert len(fixed) == len({j for j, r in fixed}) == 389
    for j, r in fixed:
        assert PAIR_OFFSET <= j < OLD_VARIABLES
        row = full["matrix"]["equalities"][r]
        assert row["terms"] == [[j, 1]] and row["rhs"] == 0
    kept = reduced["kept_original_variables"]
    assert kept == sorted(set(range(OLD_VARIABLES))-{j for j, r in fixed})
    assert len(kept) == VARIABLES and kept[:PAIR_OFFSET] == list(range(PAIR_OFFSET))
    assert sha(canonical(adjacency)) == old["core_sha256"]
    assert sha(canonical(triples)) == old["triples_sha256"]
    assert sha(canonical(edges)) == old["edges_sha256"]
    assert sha(canonical(actions)) == old["selector_actions_sha256"] == kernel["selector_actions_sha256"]
    assert sha(canonical(kept)) == old["original_variable_order_sha256"] == kernel["kept_variables_sha256"]
    domain = {"core": core, "triples": triples, "edges": edges, "pairs": pairs,
              "selector_orbits": xo, "edge_orbits": eo, "pair_orbits": po,
              "xmap": xmap, "emap": emap, "pmap": pmap, "actions": actions,
              "core_actions": core_actions, "kept": kept, "fixed_zero_rows": fixed}
    del full, reduced, baseline
    model = read_input("model")
    assert sha(canonical(model)) == MODEL_SHA
    rows = existing_rows(model)
    return {"schema": "f0-joint-psd-cache-v1", "bindings": bound, "domain": domain,
            "domain_sha256": sha(canonical(domain)), "existing_rows": rows,
            "existing_rows_sha256": sha(canonical(rows)),
            "existing_row_origins": sum(len(v) for k, v in rows),
            "kernel_reconstruction_performed": False,
            "complete_eligibility_census_repeated": False}


def runtime_domain(cache):
    d = cache["domain"]
    result = dict(d, reverse={j: i for i, j in enumerate(d["kept"])},
                  fixed={j for j, r in d["fixed_zero_rows"]})
    result["full"] = {"selector_orbits": d["selector_orbits"], "pair_orbits": d["pair_orbits"]}
    return result


def load_kernel():
    saved = read_input("kernel")
    assert saved["source_sha256"] == SOURCE_INPUTS["root_prism_free_f0_full_core_schur_kernels.py"]
    assert [k["family"] for k in saved["kernels"]] == ["plus", "minus"]
    result = {}
    for k in saved["kernels"]:
        assert len(k["diagonal_x"]) == N and len(k["off_diagonal_Z"]) == 114960
        assert k["all12_actions_verified"] and k["independent_direct_inverse_audit_matched"]
        assert k["raw_quotient_coefficient_bounds"]["all"] < 2**53
        result[k["family"]] = dict(k, inverse_denominator=k["Schur_coefficient_denominator"])
    return result


def make_cut(domain, kernels, family, vector):
    assert family in FAMILIES and max(map(abs, vector)) <= MAX_VECTOR
    return selector.cut(domain, vector) if family == "selector" else schur.cut(domain, kernels[family], vector)


def evaluate(domain, kernels, family, certificate, denominator, numerators):
    return (selector.exact_violation(domain, certificate, denominator, numerators) if family == "selector"
            else schur.exact_violation(domain, kernels[family], certificate, denominator, numerators))


def unit_box_implied(row):
    return sum(max(c, 0) for j, c in row["terms"]) <= row["rhs"]


def numerical_row_rule(row):
    """Record exact dynamic range and a scale keeping every term >=2^-29."""
    inherited = schur.dyadic_row_rule(row)
    coefficients = [c for j, c in row["terms"]]
    absolute = list(map(abs, coefficients))
    if not absolute:
        return {"max_normalized_rule": inherited, "no_nonzero_coefficients": True}
    smallest, largest = min(absolute), max(absolute)
    bound = min(inherited["positive_power_of_two_scale"], smallest*(1 << 29))
    scale = 1 << (bound.bit_length()-1)
    assert Fraction(smallest, scale) >= Fraction(1, 1 << 29)
    assert largest < 2**53
    for value in coefficients+[row["rhs"]]:
        assert Fraction(float(value)/scale) == Fraction(value, scale)
    return {"minimum_nonzero_absolute_integer_coefficient": smallest,
            "maximum_absolute_integer_coefficient": largest,
            "minimum_signed_integer_coefficient": min(coefficients),
            "maximum_signed_integer_coefficient": max(coefficients),
            "coefficient_ratio_exact": str(Fraction(largest, smallest)),
            "max_normalized_rule": inherited,
            "term_preserving_positive_dyadic_scale": scale,
            "minimum_scaled_absolute_coefficient": str(Fraction(smallest, scale)),
            "maximum_scaled_absolute_coefficient": str(Fraction(largest, scale)),
            "target_minimum_scaled_coefficient": "1/536870912",
            "binary64_conversion_exact": True,
            "future_native_transport_audit_required": True}


def disposition(row, evaluation, existing, seen):
    key = row_key(row)
    if not evaluation["violated"]:
        return "NONPOSITIVE_EXACT_GAP", key
    if unit_box_implied(row):
        return "UNIT_BOX_IMPLIED", key
    if key in existing:
        return "EXISTING_ROW_OR_EQUALITY_ORIENTATION", key
    if key in seen:
        return "DUPLICATE_NEW_ROW", key
    return "RETAIN", key


def small_controls(domain, kernels):
    r = {"terms": [[0, 2], [1, -4]], "rhs": 6}
    assert normalized_row(r) == {"terms": [[0, 1], [1, -2]], "rhs": 3}
    negative = {"terms": [[j, -c] for j, c in r["terms"]], "rhs": -r["rhs"]}
    assert row_key(r) != row_key(negative)
    existing = {row_key(r): ["example"], row_key(negative): ["example"]}
    assert disposition(r, {"violated": True}, existing, {})[0] == "UNIT_BOX_IMPLIED"
    r = {"terms": [[0, 2], [1, -4]], "rhs": 0}
    existing = {row_key(r): ["example"]}
    assert disposition(r, {"violated": True}, existing, {})[0] == "EXISTING_ROW_OR_EQUALITY_ORIENTATION"
    assert disposition(r, {"violated": True}, {}, {row_key(r): 0})[0] == "DUPLICATE_NEW_ROW"
    assert disposition(r, {"violated": True}, {}, {})[0] == "RETAIN"
    assert disposition(r, {"violated": False}, {}, {})[0] == "NONPOSITIVE_EXACT_GAP"
    dynamic = numerical_row_rule({"terms": [[0, 1], [1, -(2**52-1)]], "rhs": 0})
    assert dynamic["term_preserving_positive_dyadic_scale"] == 2**29
    assert dynamic["minimum_scaled_absolute_coefficient"] == "1/536870912"
    algebra = positive = transports = 0
    synthetic = [(j % 13)-6 for j in range(VARIABLES)]
    diagonal = [int(j < 42) for j in range(VARIABLES)]
    for family in FAMILIES:
        vectors = [[(a % 7)-3 for a in range(N)], [1024]+[0]*(N-2)+[-1023]]
        if family == "selector":
            vectors = [[2]+v for v in vectors]
        for index, v in enumerate(vectors):
            certificate = make_cut(domain, kernels, family, v)
            evaluate(domain, kernels, family, certificate, 8, synthetic)
            algebra += 1
            check = evaluate(domain, kernels, family, certificate, N, diagonal)
            assert not check["violated"]
            if family == "selector":
                c, w = certificate["vector"][0], certificate["vector"][1:]
                expected = sum((c+a)**2 for a in w)
                assert int(check["literal_quadratic_numerator"]) == expected
            positive += 1
            if index == 0:
                for g in domain["actions"]:
                    moved = [0]*len(v)
                    offset = int(family == "selector")
                    if offset:
                        moved[0] = v[0]
                    for a in range(N):
                        moved[g[a]+offset] = v[a+offset]
                    assert make_cut(domain, kernels, family, moved)["row"] == certificate["row"]
                    transports += 1
    return {"status": "PASS: reused literal/full-orbit identities and new filtering controls",
            "synthetic_exact_quadratic_checks": algebra, "positive_diagonal_moment_checks": positive,
            "all12_vector_transports_by_family": transports, "filter_outcomes_tested": 5,
            "extreme_dynamic_range_scale_control": dynamic,
            "controls_claimed_full_model_feasible": False, "optimizer_calls": 0, "eigendecompositions": 0}


def limits():
    return {"family_order": list(FAMILIES), "matrix_orders": [481, 480, 480],
            "decompositions_per_family": 1, "directions_per_family": DIRECTIONS,
            "scales": list(SCALES), "maximum_vector_entry": MAX_VECTOR,
            "retained_cuts_per_family": PER_FAMILY, "retained_cuts_total": TOTAL_CUTS,
            "attempts_per_family": DIRECTIONS*len(SCALES), "maximum_seconds": SCAN_SECONDS,
            "time_limit_cooperative_between_operations": True}


def prepare(cache_path):
    cache = project_cache()
    domain, kernels = runtime_domain(cache), load_kernel()
    controls = small_controls(domain, kernels)
    save_new(cache_path, cache)
    return {"status": "PASS: joint cached scan prepared; no eigenscan or optimizer",
            **bindings(), "limits": limits(), "cache_file_sha256": sha(Path(cache_path).read_bytes()),
            "cache_canonical_sha256": sha(canonical(cache)), "domain_sha256": cache["domain_sha256"],
            "existing_rows_sha256": cache["existing_rows_sha256"],
            "existing_primitive_rows": len(cache["existing_rows"]), "existing_row_origins": cache["existing_row_origins"],
            "controls": controls, "all480_selectors_retained": True, "fixed_zero_Z_orbits": 389,
            "kernel_bounds": {f: kernels[f]["raw_quotient_coefficient_bounds"] for f in ("plus", "minus")},
            "selector_raw_bound": 36*MAX_VECTOR**2,
            "kernel_reconstruction_performed": False, "optimizer_calls": 0, "eigendecompositions": 0,
            "scope": "Necessary PSD directions for the global prism/F-free split18+18 component0 stratum; no point, exclusion or full-PSD claim."}


def load_prepared(preparation_path, cache_path):
    prepared, cache = load_json(preparation_path), load_json(cache_path)
    bound = bindings()
    assert all(prepared[k] == v for k, v in bound.items()) and cache["bindings"] == bound
    assert prepared["limits"] == limits()
    assert prepared["cache_file_sha256"] == sha(Path(cache_path).read_bytes())
    assert prepared["cache_canonical_sha256"] == sha(canonical(cache))
    assert cache["domain_sha256"] == prepared["domain_sha256"] == sha(canonical(cache["domain"]))
    assert cache["existing_rows_sha256"] == prepared["existing_rows_sha256"] == sha(canonical(cache["existing_rows"]))
    # These are the current point/model bytes, not the old proposal metadata
    # retained inside the point-independent kernel certificate.
    for key in ("proposal", "model"):
        filename, expected = INPUTS[key]
        assert sha((LOGS/filename).read_bytes()) == expected
    return prepared, cache, runtime_domain(cache), load_kernel()


def proposal():
    numeric = read_input("proposal")
    assert numeric["model_sha256"] == MODEL_SHA and numeric["value_valid"] is True
    values = [float.fromhex(h) for h in numeric["col_value_hex"]]
    assert len(values) == VARIABLES and all(math.isfinite(v) for v in values)
    ratios = [v.as_integer_ratio() for v in values]
    denominator = max(d for n, d in ratios)
    assert denominator > 0 and denominator & (denominator-1) == 0
    assert all(denominator % d == 0 for n, d in ratios)
    return denominator, [n*(denominator//d) for n, d in ratios], values


def matrix(np, domain, kernels, family, values):
    if family != "selector":
        return schur.floating_matrix(np, domain, kernels[family], values)
    old = schur.expand_old(domain, values)
    answer = np.zeros((N+1, N+1), dtype=float)
    answer[0, 0] = 1
    for a in range(N):
        answer[0, a+1] = answer[a+1, 0] = answer[a+1, a+1] = old[domain["xmap"][a]]
    for p, (a, b) in enumerate(domain["pairs"]):
        answer[a+1, b+1] = answer[b+1, a+1] = old[PAIR_OFFSET+domain["pmap"][p]]
    assert np.isfinite(answer).all() and np.array_equal(answer, answer.T)
    return answer


def scan(preparation_path, cache_path, output_path, seconds):
    assert 0 < seconds <= SCAN_SECONDS and not Path(output_path).exists()
    started, result = time.monotonic(), {"status": "RUNNING", **bindings(), "limits": limits(),
        "preparation_sha256": sha(Path(preparation_path).read_bytes()),
        "requested_seconds": seconds, "families": [], "attempts": [], "cuts": [],
        "eigendecompositions": 0, "optimizer_calls": 0, "proposal_feasibility_claimed": False}
    deadline = started+seconds
    schur.atomic_result(output_path, result)
    try:
        prepared, cache, domain, kernels = load_prepared(preparation_path, cache_path)
        denominator, numerators, values = proposal()
        result["proposal_common_denominator"] = str(denominator)
        existing, seen = dict(cache["existing_rows"]), {}
        import numpy as np
        from threadpoolctl import threadpool_limits
        for family in FAMILIES:
            tick(deadline)
            record = {"family": family, "status": "RUNNING", "directions": [], "retained_cuts": 0}
            result["families"].append(record)
            floating = matrix(np, domain, kernels, family, values)
            tick(deadline)
            with threadpool_limits(limits=1):
                eigenvalues, eigenvectors = np.linalg.eigh(floating)
            result["eigendecompositions"] += 1
            assert np.isfinite(eigenvalues).all() and np.isfinite(eigenvectors).all()
            record["minimum_eigenvalue_hex"] = float(eigenvalues[0]).hex()
            record["numerical_negative_eigenvalues"] = int(np.count_nonzero(eigenvalues < 0))
            for index in range(DIRECTIONS):
                tick(deadline)
                direction = eigenvectors[:, index]
                record["directions"].append({"index": index, "eigenvalue_hex": float(eigenvalues[index]).hex(),
                    "vector_hex": [float(v).hex() for v in direction]})
                direction = direction/np.max(np.abs(direction))
                for scale in SCALES:
                    tick(deadline)
                    vector = [int(v) for v in np.rint(direction*scale)]
                    certificate = make_cut(domain, kernels, family, vector)
                    exact = evaluate(domain, kernels, family, certificate, denominator, numerators)
                    decision, key = disposition(certificate["row"], exact, existing, seen)
                    attempt = {"family": family, "direction_index": index, "scale": scale,
                        "vector": certificate["vector"], "row_sha256": key,
                        "exact_evaluation": exact, "disposition": decision}
                    if decision == "RETAIN":
                        assert record["retained_cuts"] < PER_FAMILY and len(result["cuts"]) < TOTAL_CUTS
                        attempt["retained_index"] = len(result["cuts"])
                        seen[key] = len(result["cuts"])
                        result["cuts"].append({"family": family, "certificate": certificate,
                            "exact_evaluation": exact, "direction_index": index, "scale": scale,
                            "numerical_row_rule": numerical_row_rule(certificate["row"]),
                            "strict_strength_over_parent_LP_claimed": False})
                        record["retained_cuts"] += 1
                    elif decision == "EXISTING_ROW_OR_EQUALITY_ORIENTATION":
                        attempt["existing_origins"] = existing[key]
                    elif decision == "DUPLICATE_NEW_ROW":
                        attempt["duplicate_of"] = seen[key]
                    result["attempts"].append(attempt)
                    if record["retained_cuts"] == PER_FAMILY:
                        break
                schur.atomic_result(output_path, result)
                if record["retained_cuts"] == PER_FAMILY:
                    break
            record["status"] = "CUT_LIMIT" if record["retained_cuts"] == PER_FAMILY else "COMPLETE_DIRECTIONS"
            schur.atomic_result(output_path, result)
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
        result["complete_direction_coverage"] = (len(result["families"]) == len(FAMILIES) and
            all(f["status"] == "COMPLETE_DIRECTIONS" for f in result["families"]))
        result["no_cut_implies_PSD"] = False
        result["scope"] = "Exact necessary new rows only. No exact feasible point, component exclusion or full PSD certificate."
        schur.atomic_result(output_path, result)
    return result


def replay(preparation_path, cache_path, result_path):
    started = time.monotonic()
    prepared, cache, domain, kernels = load_prepared(preparation_path, cache_path)
    result = load_json(result_path)
    assert result["status"] not in ("RUNNING", "ERROR")
    assert all(result[k] == v for k, v in bindings().items())
    assert result["preparation_sha256"] == sha(Path(preparation_path).read_bytes())
    assert result["limits"] == limits() and result["optimizer_calls"] == 0
    assert result["eigendecompositions"] <= 3 and len(result["cuts"]) <= TOTAL_CUTS
    assert [f["family"] for f in result["families"]] == list(FAMILIES[:len(result["families"])])
    denominator, numerators, values = proposal()
    if "proposal_common_denominator" in result:
        assert result["proposal_common_denominator"] == str(denominator)
    existing, seen, counts = dict(cache["existing_rows"]), {}, Counter()
    for attempt in result["attempts"]:
        family = attempt["family"]
        assert family in FAMILIES and attempt["scale"] in SCALES
        assert 0 <= attempt["direction_index"] < DIRECTIONS
        certificate = make_cut(domain, kernels, family, attempt["vector"])
        exact = evaluate(domain, kernels, family, certificate, denominator, numerators)
        decision, key = disposition(certificate["row"], exact, existing, seen)
        assert key == attempt["row_sha256"] and exact == attempt["exact_evaluation"]
        assert decision == attempt["disposition"]
        if decision == "RETAIN":
            index = len(seen)
            assert attempt["retained_index"] == index and counts[family] < PER_FAMILY
            expected = {"family": family, "certificate": certificate, "exact_evaluation": exact,
                "direction_index": attempt["direction_index"], "scale": attempt["scale"],
                "numerical_row_rule": numerical_row_rule(certificate["row"]),
                "strict_strength_over_parent_LP_claimed": False}
            assert result["cuts"][index] == expected
            seen[key] = index
            counts[family] += 1
        elif decision == "EXISTING_ROW_OR_EQUALITY_ORIENTATION":
            assert attempt["existing_origins"] == existing[key]
        elif decision == "DUPLICATE_NEW_ROW":
            assert attempt["duplicate_of"] == seen[key]
        if decision != "RETAIN":
            assert "retained_index" not in attempt
    assert len(seen) == len(result["cuts"])
    assert result["disposition_counts"] == dict(Counter(a["disposition"] for a in result["attempts"]))
    for record in result["families"]:
        assert record["retained_cuts"] == counts[record["family"]]
        assert len(record["directions"]) <= DIRECTIONS
    return {"status": "PASS: all new PSD rows and every recorded disposition exactly replayed",
            **bindings(), "result_sha256": sha(Path(result_path).read_bytes()),
            "retained_cuts": len(seen), "family_counts": {f: counts[f] for f in FAMILIES},
            "attempts": len(result["attempts"]), "disposition_counts": result["disposition_counts"],
            "kernel_reconstruction_performed": False, "eigendecompositions": 0, "optimizer_calls": 0,
            "proposal_feasibility_claimed": False, "seconds": time.monotonic()-started}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "replay-preparation", "scan", "replay"))
    parser.add_argument("--cache", type=Path, required=True)
    parser.add_argument("--preparation", type=Path)
    parser.add_argument("--result", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seconds", type=float, default=SCAN_SECONDS)
    args = parser.parse_args()
    if args.mode == "prepare":
        result = prepare(args.cache)
        save_new(args.output, result)
    elif args.mode == "replay-preparation":
        prepared, cache, domain, kernels = load_prepared(args.preparation, args.cache)
        assert project_cache() == cache
        assert small_controls(domain, kernels) == prepared["controls"]
        result = {"status": "PASS: cold domain projection and controls replayed without kernel census",
            **bindings(), "preparation_sha256": sha(args.preparation.read_bytes()),
            "cache_sha256": sha(args.cache.read_bytes()), "optimizer_calls": 0, "eigendecompositions": 0}
        save_new(args.output, result)
    elif args.mode == "scan":
        result = scan(args.preparation, args.cache, args.output, args.seconds)
    else:
        result = replay(args.preparation, args.cache, args.result)
        save_new(args.output, result)
    print(json.dumps({k: result[k] for k in ("status", "source_sha256", "retained_cuts", "optimizer_calls", "eigendecompositions") if k in result}, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
