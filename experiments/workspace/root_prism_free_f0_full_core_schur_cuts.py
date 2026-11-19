"""Full21-core two-family Schur cuts; spectra only propose vectors.

Preparation/replay use exact arithmetic and make no eigendecomposition.
The separately gated scan uses one full480 decomposition per family.
"""
import argparse
from fractions import Fraction
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

import root_prism_free_f0_graph_schur_kernels as kernels
import root_prism_free_f0_full_core_schur_kernels as full_core

ROOT, LOGS = kernels.ROOT, kernels.LOGS
KERNEL_SOURCE_SHA256 = "141392693e8d4b7e140c329cfa4128b8794bd376713558394ef014975e2fc63f"
KERNEL_FILE = "f0-full-core-schur-kernels01.json.gz"
KERNEL_FILE_SHA256 = "a49b8309032b2c599c637285f4a4584bb7d55659640e594df1e6fdd50bf826c1"
KERNEL_RAW_SHA256 = "a963a88606a9fad78576d711f6ef7bf67eb03032176cebc2af5af700ea7c6708"
PROPOSAL_FILE = "f0-selector-psd-query-run01/numerical.json"
PROPOSAL_SHA256 = kernels.PROPOSAL_SHA256
MODEL_SHA256 = kernels.CURRENT_MODEL_SHA256
N, PAIR_OFFSET, OLD_VARIABLES = 480, 5847, 15589
MAX_VECTOR_ENTRY = 1024
SCALES = (1, 4, 16, 64, 256, 1024)
MAX_DIRECTIONS_PER_FAMILY = 8
MAX_CUTS_PER_FAMILY, MAX_CUTS = 16, 32
MAX_SCAN_SECONDS = 60
FAMILY_ORDER = ("plus", "minus")


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode()


def save_new(path, value):
    path = Path(path)
    assert not path.exists()
    path.write_text(json.dumps(value, indent=2)+"\n")


def atomic_result(path, value):
    path = Path(path)
    raw = canonical(value)
    if path.suffix == ".gz":
        raw = gzip.compress(raw, mtime=0)
    temporary = path.with_name(path.name+".tmp")
    temporary.write_bytes(raw)
    temporary.replace(path)


def read_result(path):
    raw = Path(path).read_bytes()
    return json.loads(gzip.decompress(raw) if Path(path).suffix == ".gz" else raw)


def tick(deadline):
    if time.monotonic() >= deadline:
        raise TimeoutError("graph-Schur exact/scan budget")


def bindings():
    assert sha(Path(full_core.__file__).read_bytes()) == KERNEL_SOURCE_SHA256
    assert sha(Path(kernels.__file__).read_bytes()) == full_core.OLD_SOURCE_SHA256
    return {"source_sha256": sha(Path(__file__).read_bytes()),
            "kernel_source_sha256": KERNEL_SOURCE_SHA256,
            "kernel_file_sha256": KERNEL_FILE_SHA256,
            "kernel_raw_sha256": KERNEL_RAW_SHA256,
            "old_kernel_source_sha256": full_core.OLD_SOURCE_SHA256,
            "independent_full_core_audit_source_sha256": full_core.AUDIT_SOURCE_SHA256,
            "independent_full_core_audit_record_sha256": full_core.AUDIT_RECORD_SHA256,
            "proposal_sha256": PROPOSAL_SHA256, "model_sha256": MODEL_SHA256}


def load_state(deadline=float("inf")):
    bindings()
    raw = (LOGS/KERNEL_FILE).read_bytes()
    assert sha(raw) == KERNEL_FILE_SHA256
    plain = gzip.decompress(raw)
    assert sha(plain) == KERNEL_RAW_SHA256
    certificate = json.loads(plain)
    assert certificate["source_sha256"] == KERNEL_SOURCE_SHA256
    assert certificate["proposal_model_sha256"] == MODEL_SHA256
    assert certificate["proposal_sha256"] == PROPOSAL_SHA256
    domain, prior, audit = full_core.load_inputs(deadline)
    fibers, eta, deviation = full_core.fiber_data(domain)
    expected = [full_core.full_kernel(domain, prior[name], deviation, audit["families"][i], deadline)
                for i, name in enumerate(FAMILY_ORDER)]
    assert certificate["kernels"] == expected
    assert certificate["maximum_vector_entry"] == MAX_VECTOR_ENTRY
    assert certificate["fibers"] == fibers and certificate["fiber_counts"] == eta
    assert certificate["fiber_deviations"] == deviation
    assert certificate["selector_actions_sha256"] == sha(canonical(domain["actions"]))
    assert certificate["kept_variables_sha256"] == sha(canonical(domain["kept"]))
    # The unchanged exact-gap routine calls its positive matrix denominator
    # "inverse_denominator". Here it is the common Schur coefficient denominator,
    # not a claim about the denominator of an entire full-core matrix inverse.
    adapted = {k["family"]: {**k, "inverse_denominator": k["Schur_coefficient_denominator"]}
               for k in expected}
    return domain, adapted


def primitive_vector(vector):
    assert len(vector) == N and all(type(v) is int for v in vector)
    assert any(vector) and max(map(abs, vector)) <= MAX_VECTOR_ENTRY
    divisor = math.gcd(*vector)
    vector = [v//divisor for v in vector]
    if next(v for v in vector if v) < 0:
        vector = [-v for v in vector]
    return vector


def literal_coefficients(kernel, vector, edges, pairs):
    """Negative of D*v^T*S*v, using three disjoint kinds of primary variables."""
    assert len(vector) == len(kernel["diagonal_x"])
    diagonal = [-d*v*v for d, v in zip(kernel["diagonal_x"], vector)]
    edge = [-2*kernel["Y"]*vector[a]*vector[b] for a, b in edges]
    pair = [-2*d*vector[a]*vector[b] for d, (a, b) in zip(kernel["off_diagonal_Z"], pairs)]
    return diagonal, edge, pair


def raw_quotient(domain, kernel, vector):
    diagonal, edge, pair = literal_coefficients(kernel, vector, domain["edges"], domain["pairs"])
    terms = [0]*OLD_VARIABLES
    for a, c in enumerate(diagonal):
        terms[domain["xmap"][a]] += c
    for e, c in enumerate(edge):
        terms[42+domain["emap"][e]] += c
    for p, c in enumerate(pair):
        terms[PAIR_OFFSET+domain["pmap"][p]] += c
    # Recompute each orbit sum directly, without the three literal arrays.
    for orbit, members in enumerate(domain["selector_orbits"]):
        assert terms[orbit] == -sum(kernel["diagonal_x"][a]*vector[a]**2 for a in members)
    for orbit, members in enumerate(domain["edge_orbits"]):
        assert terms[42+orbit] == -2*kernel["Y"]*sum(
            vector[domain["edges"][e][0]]*vector[domain["edges"][e][1]] for e in members)
    for orbit, members in enumerate(domain["pair_orbits"]):
        assert terms[PAIR_OFFSET+orbit] == -2*sum(
            kernel["off_diagonal_Z"][p]*vector[domain["pairs"][p][0]]*
            vector[domain["pairs"][p][1]] for p in members)
    bound = kernel["raw_quotient_coefficient_bounds"]
    assert max(map(abs, terms[:42])) <= bound["x"]
    assert max(map(abs, terms[42:PAIR_OFFSET])) <= bound["Y"]
    assert max(map(abs, terms[PAIR_OFFSET:])) <= bound["Z"]
    assert max(map(abs, terms)) < 2**53
    reduced = [[domain["reverse"][j], c] for j, c in enumerate(terms)
               if c and j not in domain["fixed"]]
    return reduced, {"literal_x_sha256": sha(canonical(diagonal)),
                     "literal_Y_sha256": sha(canonical(edge)),
                     "literal_Z_sha256": sha(canonical(pair)),
                     "full_raw_quotient_sha256": sha(canonical(terms)),
                     "raw_maximum_coefficient_bits": max(abs(c).bit_length() for c in terms),
                     "fixed_zero_coordinates_substituted": len(domain["fixed"])}


def dyadic_row_rule(row):
    values = [abs(c) for j, c in row["terms"]]
    largest = max(values, default=0)
    scale = 1 << (largest.bit_length()-1) if largest else 1
    assert largest < 2**53
    for j, c in row["terms"]:
        assert Fraction(float(c)/scale) == Fraction(c, scale)
    return {"positive_power_of_two_scale": scale,
            "largest_coefficient_bits": largest.bit_length(),
            "smallest_nonzero_scaled_absolute_coefficient": str(Fraction(min(values), scale)) if values else None,
            "largest_scaled_absolute_coefficient": str(Fraction(largest, scale)),
            "binary64_conversion_exact": True,
            "small_coefficients_may_still_affect_conditioning": True}


def cut(domain, kernel, vector):
    vector = primitive_vector(vector)
    terms, literal = raw_quotient(domain, kernel, vector)
    divisor = math.gcd(*(abs(c) for j, c in terms)) if terms else 1
    assert divisor > 0
    row = {"terms": [[j, c//divisor] for j, c in terms], "rhs": 0}
    return {"family": kernel["family"], "vector": vector, "row": row,
            "positive_divisor": divisor, **literal, "numerical_row_rule": dyadic_row_rule(row)}


def rational_proposal(path):
    raw = Path(path).read_bytes()
    assert sha(raw) == PROPOSAL_SHA256
    numerical = json.loads(raw)
    assert numerical["model_sha256"] == MODEL_SHA256
    assert numerical["value_valid"] is True
    values = [float.fromhex(v) for v in numerical["col_value_hex"]]
    assert len(values) == 15200 and all(math.isfinite(v) for v in values)
    ratios = [v.as_integer_ratio() for v in values]
    denominator = max(d for n, d in ratios)
    assert denominator > 0 and denominator & (denominator-1) == 0
    assert all(denominator % d == 0 for n, d in ratios)
    return denominator, [n*(denominator//d) for n, d in ratios], values


def expand_old(domain, values):
    assert len(values) == len(domain["kept"]) == 15200
    old = [0]*OLD_VARIABLES
    for j, value in zip(domain["kept"], values):
        old[j] = value
    assert all(old[j] == 0 for j in domain["fixed"])
    return old


def literal_quadratic(domain, kernel, vector, old):
    value = sum(kernel["diagonal_x"][a]*vector[a]**2*old[domain["xmap"][a]] for a in range(N))
    value += 2*kernel["Y"]*sum(vector[a]*vector[b]*old[42+domain["emap"][e]]
                              for e, (a, b) in enumerate(domain["edges"]))
    value += 2*sum(d*vector[a]*vector[b]*old[PAIR_OFFSET+domain["pmap"][p]]
                   for p, (d, (a, b)) in enumerate(zip(kernel["off_diagonal_Z"], domain["pairs"])))
    return value


def exact_violation(domain, kernel, certificate, denominator, numerators):
    gap = sum(c*numerators[j] for j, c in certificate["row"]["terms"])
    quadratic = literal_quadratic(domain, kernel, certificate["vector"], expand_old(domain, numerators))
    assert quadratic == -certificate["positive_divisor"]*gap
    return {"violated": gap > 0, "gap_numerator": str(gap), "proposal_denominator": str(denominator),
            "literal_scaled_quadratic_numerator": str(quadratic),
            "literal_Schur_quadratic_denominator": str(denominator*kernel["inverse_denominator"]),
            "proposal_feasibility_claimed": False}


def inverse(matrix):
    n = len(matrix)
    work = [[Fraction(v) for v in row]+[Fraction(i == j) for j in range(n)]
            for i, row in enumerate(matrix)]
    for j in range(n):
        pivot = next(i for i in range(j, n) if work[i][j])
        work[j], work[pivot] = work[pivot], work[j]
        factor = work[j][j]
        work[j] = [v/factor for v in work[j]]
        for i in range(n):
            if i != j:
                factor = work[i][j]
                work[i] = [a-factor*b for a, b in zip(work[i], work[j])]
    assert all(work[i][j] == int(i == j) for i in range(n) for j in range(n))
    return [row[n:] for row in work]


def psd_ldl(matrix):
    n = len(matrix)
    work = [[Fraction(v) for v in row] for row in matrix]
    assert all(work[i][j] == work[j][i] for i in range(n) for j in range(n))
    pivots = []
    for k in range(n):
        p = work[k][k]
        assert p >= 0
        pivots.append(str(p))
        if not p:
            assert all(work[i][k] == 0 for i in range(k+1, n))
            continue
        for i in range(k+1, n):
            for j in range(i, n):
                work[i][j] -= work[i][k]*work[k][j]/p
                work[j][i] = work[i][j]
    return pivots


def rook_controls():
    adjacency = [[int(i != j and (i//3 == j//3 or i % 3 == j % 3)) for j in range(9)]
                 for i in range(9)]
    core = [0, 1, 3]
    outside = [i for i in range(9) if i not in core]
    pairs = list(combinations(range(len(outside)), 2))
    edges = [(a, b) for a, b in pairs if adjacency[outside[a]][outside[b]]]
    vectors = [[1]*6, [1, -2, 3, 0, -1, 2], [0, 1, 0, -1, 1, 0]]
    reports = []
    for family, d, e, c, ignored in kernels.FAMILIES:
        whole = [[d*int(i == j)+e*adjacency[i][j]+c for j in range(9)] for i in range(9)]
        whole_pivots = psd_ldl(whole)
        k = [[whole[i][j] for j in core] for i in core]
        k_inv = inverse(k)
        den = math.lcm(*(v.denominator for row in k_inv for v in row))
        num = [[int(v*den) for v in row] for row in k_inv]
        cross = [[whole[i][a] for i in core] for a in outside]
        h = [[sum(cross[a][i]*num[i][j]*cross[b][j] for i in range(3) for j in range(3))
              for b in range(6)] for a in range(6)]
        kernel = {"diagonal_x": [(d+c)*den-h[a][a] for a in range(6)],
                  "off_diagonal_Z": [c*den-h[a][b] for a, b in pairs], "Y": e*den}
        schur = [[Fraction(whole[outside[a]][outside[b]])-Fraction(h[a][b], den)
                  for b in range(6)] for a in range(6)]
        schur_pivots = psd_ldl(schur)
        checks = 0
        for z in product((0, 1), repeat=6):
            for v in vectors:
                w = [z[a]*v[a] for a in range(6)]
                u = [sum(cross[a][i]*w[a] for a in range(6)) for i in range(3)]
                extended = [Fraction(0)]*9
                for i, site in enumerate(core):
                    extended[site] = -sum(k_inv[i][j]*u[j] for j in range(3))
                for a, site in enumerate(outside):
                    extended[site] = Fraction(w[a])
                direct = sum(extended[i]*whole[i][j]*extended[j] for i in range(9) for j in range(9))
                other = sum(Fraction(w[a])*schur[a][b]*w[b] for a in range(6) for b in range(6))
                diagonal, edge, pair = literal_coefficients(kernel, v, edges, pairs)
                negative = sum(d*z[a] for a, d in enumerate(diagonal))
                negative += sum(t*z[a]*z[b] for t, (a, b) in zip(edge, edges))
                negative += sum(t*z[a]*z[b] for t, (a, b) in zip(pair, pairs))
                assert direct == other and direct >= 0 and negative == -den*direct
                checks += 1
        reports.append({"family": family, "full_graph_LDL": whole_pivots,
                        "Schur_LDL": schur_pivots, "literal_binary_controls": checks})
    return {"status": "PASS: exact nine-rook padded Schur controls",
            "families": reports, "number_of_graphs": 1,
            "graph_is_SRG99_control": False, "all64_masks_and3_vectors_per_family": True}


def full_domain_controls(domain, by_family, deadline):
    vectors = [[(a % 7)-3 for a in range(N)],
               [1024 if a == 0 else (-1023 if a == N-1 else 0) for a in range(N)],
               [int(a % 19 == 0)-2*int(a % 23 == 0) for a in range(N)]]
    algebra = diagonal_positive = transports = 0
    for family in FAMILY_ORDER:
        kernel = by_family[family]
        for index, vector in enumerate(vectors):
            tick(deadline)
            certificate = cut(domain, kernel, vector)
            synthetic = [(j % 13)-6 for j in range(15200)]
            evaluation = exact_violation(domain, kernel, certificate, 8, synthetic)
            assert evaluation["proposal_feasibility_claimed"] is False
            algebra += 1
            # A diagonal selector distribution only tests this PSD form.
            # It is not claimed to satisfy population60 or the incidence rows.
            values = [int(j < 42) for j in range(15200)]
            evaluation = exact_violation(domain, kernel, certificate, N, values)
            assert int(evaluation["literal_scaled_quadratic_numerator"]) > 0
            assert evaluation["violated"] is False
            diagonal_positive += 1
            if index == 0:
                for g in domain["actions"]:
                    tick(deadline)
                    moved = [0]*N
                    for a in range(N):
                        moved[g[a]] = vector[a]
                    assert cut(domain, kernel, moved)["row"] == certificate["row"]
                    transports += 1
    return {"status": "PASS: literal full480/quotient/zero/transport controls",
            "literal_synthetic_equalities": algebra, "positive_diagonal_moment_controls": diagonal_positive,
            "literal_vector_transports": transports,
            "arbitrary_synthetic_points_claimed_feasible": False,
            "diagonal_controls_claimed_full_model_feasible": False}


def limits():
    return {"family_order": list(FAMILY_ORDER), "families": 2,
            "decompositions_per_family": 1, "directions_per_family": MAX_DIRECTIONS_PER_FAMILY,
            "scales": list(SCALES), "maximum_vector_entry": MAX_VECTOR_ENTRY,
            "cuts_per_family": MAX_CUTS_PER_FAMILY, "total_cuts": MAX_CUTS,
            "maximum_scan_seconds": MAX_SCAN_SECONDS,
            "time_limit_is_cooperative_between_bounded_operations": True}


def preparation(seconds=120):
    started = time.monotonic()
    deadline = started+seconds
    domain, by_family = load_state(deadline)
    rook = rook_controls()
    full = full_domain_controls(domain, by_family, deadline)
    tick(deadline)
    return {"status": "PASS: full21-core graph-Schur extraction prepared; no production scan",
            **bindings(), "limits": limits(), "rook_controls": rook, "full_domain_controls": full,
            "kernel_bounds": {f: by_family[f]["raw_quotient_coefficient_bounds"] for f in FAMILY_ORDER},
            "matrix_dyad_scales": {f: by_family[f]["proposing_matrix_positive_dyad_scale"] for f in FAMILY_ORDER},
            "original_variables": OLD_VARIABLES, "retained_variables": 15200,
            "conditioned_core_order": 21, "positive_core_orders": {"plus": 20, "minus": 21},
            "residual_profile_product_controls": 98,
            "fixed_zero_pairs": 389, "all480_selectors_retained": True,
            "optimizer_calls": 0, "eigendecompositions": 0,
            "scope": "Full21-core conditioning for component0 in the globally prism/F-free split18+18 case; second component/alignment free.",
            "spectral_proposals_need_not_satisfy_the_linear_model": True}


def floating_matrix(np, domain, kernel, values):
    old = expand_old(domain, values)
    scale = kernel["proposing_matrix_positive_dyad_scale"]
    matrix = np.zeros((N, N), dtype=float)
    for a in range(N):
        matrix[a, a] = (float(kernel["diagonal_x"][a])/scale)*old[domain["xmap"][a]]
    for p, (a, b) in enumerate(domain["pairs"]):
        value = (float(kernel["off_diagonal_Z"][p])/scale)*old[PAIR_OFFSET+domain["pmap"][p]]
        matrix[a, b] = matrix[b, a] = value
    for e, (a, b) in enumerate(domain["edges"]):
        value = (float(kernel["Y"])/scale)*old[42+domain["emap"][e]]
        matrix[a, b] += value
        matrix[b, a] += value
    assert np.isfinite(matrix).all() and np.array_equal(matrix, matrix.T)
    return matrix


def scan(prepared_path, proposal_path, output_path, seconds):
    assert 0 < seconds <= MAX_SCAN_SECONDS and not Path(output_path).exists()
    prepared_raw = Path(prepared_path).read_bytes()
    prepared = json.loads(prepared_raw)
    assert all(prepared[k] == v for k, v in bindings().items())
    assert prepared["limits"] == limits() and prepared["eigendecompositions"] == 0
    started = time.monotonic()
    deadline = started+seconds
    result = {"status": "RUNNING", **bindings(), "preparation_sha256": sha(prepared_raw),
              "limits": limits(), "requested_seconds": seconds, "optimizer_calls": 0,
              "families": [], "cuts": [], "attempts": [], "eigendecompositions": 0,
              "linear_feasibility_claimed": False, "PSD_feasibility_claimed": False}
    atomic_result(output_path, result)
    try:
        domain, by_family = load_state(deadline)
        denominator, numerators, values = rational_proposal(proposal_path)
        result["proposal_common_denominator"] = str(denominator)
        import numpy as np
        from threadpoolctl import threadpool_limits
        seen = {}
        for family in FAMILY_ORDER:
            tick(deadline)
            kernel = by_family[family]
            record = {"family": family, "status": "RUNNING", "directions": [], "cuts": 0,
                      "matrix_positive_dyad_scale": kernel["proposing_matrix_positive_dyad_scale"]}
            result["families"].append(record)
            matrix = floating_matrix(np, domain, kernel, values)
            tick(deadline)
            with threadpool_limits(limits=1):
                eigenvalues, eigenvectors = np.linalg.eigh(matrix)
            result["eigendecompositions"] += 1
            assert np.isfinite(eigenvalues).all() and np.isfinite(eigenvectors).all()
            record["smallest_eigenvalue_hex"] = float(eigenvalues[0]).hex()
            record["numerical_negative_eigenvalues"] = int(np.count_nonzero(eigenvalues < 0))
            for index in range(MAX_DIRECTIONS_PER_FAMILY):
                tick(deadline)
                direction = eigenvectors[:, index]
                record["directions"].append({"index": index, "eigenvalue_hex": float(eigenvalues[index]).hex(),
                                             "vector_hex": [float(v).hex() for v in direction]})
                direction = direction/np.max(np.abs(direction))
                for scale in SCALES:
                    tick(deadline)
                    rounded = [int(v) for v in np.rint(direction*scale)]
                    certificate = cut(domain, kernel, rounded)
                    evaluation = exact_violation(domain, kernel, certificate, denominator, numerators)
                    attempt = {"family": family, "direction_index": index, "scale": scale,
                               "vector": certificate["vector"], "row_sha256": sha(canonical(certificate["row"])),
                               "exact_evaluation": evaluation}
                    if evaluation["violated"]:
                        key = sha(canonical(certificate["row"]))
                        if key in seen:
                            attempt["duplicate_of"] = seen[key]
                        else:
                            assert record["cuts"] < MAX_CUTS_PER_FAMILY and len(result["cuts"]) < MAX_CUTS
                            attempt["retained_index"] = len(result["cuts"])
                            seen[key] = len(result["cuts"])
                            result["cuts"].append({**certificate, "exact_evaluation": evaluation,
                                                   "direction_index": index, "scale": scale})
                            record["cuts"] += 1
                    result["attempts"].append(attempt)
                    if record["cuts"] >= MAX_CUTS_PER_FAMILY:
                        break
                atomic_result(output_path, result)
                if record["cuts"] >= MAX_CUTS_PER_FAMILY:
                    break
            record["status"] = ("CUT_LIMIT" if record["cuts"] >= MAX_CUTS_PER_FAMILY else "COMPLETE_DIRECTIONS")
            atomic_result(output_path, result)
        result["status"] = "EXACT_CUTS" if result["cuts"] else "NO_RETAINED_SEPARATOR"
    except TimeoutError as exc:
        result["status"], result["message"] = "TIME_LIMIT_PARTIAL", str(exc)
    except Exception as exc:
        result["status"], result["message"] = "ERROR", repr(exc)
        raise
    finally:
        result["elapsed_seconds"] = time.monotonic()-started
        result["cooperative_overrun_seconds"] = max(0.0, result["elapsed_seconds"]-seconds)
        result["family_scan_coverage_complete"] = (
            len(result["families"]) == 2 and all(x["status"] == "COMPLETE_DIRECTIONS" for x in result["families"]))
        result["scope"] = "Retained exact necessary cuts only; no point/exclusion/full-PSD conclusion."
        atomic_result(output_path, result)
    return result


def replay(result_path, preparation_path, proposal_path, seconds=120):
    started = time.monotonic()
    deadline = started+seconds
    result = read_result(result_path)
    assert result["status"] not in ("RUNNING", "ERROR")
    assert all(result[k] == v for k, v in bindings().items())
    assert result["preparation_sha256"] == sha(Path(preparation_path).read_bytes())
    prepared = json.loads(Path(preparation_path).read_bytes())
    assert all(prepared[k] == v for k, v in bindings().items())
    assert result["limits"] == prepared["limits"] == limits()
    assert result["optimizer_calls"] == 0 and result["eigendecompositions"] <= 2
    assert len(result["cuts"]) <= MAX_CUTS
    assert [x["family"] for x in result["families"]] == list(FAMILY_ORDER[:len(result["families"])])
    domain, by_family = load_state(deadline)
    denominator, numerators, values = rational_proposal(proposal_path)
    if "proposal_common_denominator" in result:
        assert result["proposal_common_denominator"] == str(denominator)
    seen, counts = {}, {f: 0 for f in FAMILY_ORDER}
    for attempt in result["attempts"]:
        tick(deadline)
        family = attempt["family"]
        assert family in FAMILY_ORDER and attempt["scale"] in SCALES
        assert 0 <= attempt["direction_index"] < MAX_DIRECTIONS_PER_FAMILY
        certificate = cut(domain, by_family[family], attempt["vector"])
        key = sha(canonical(certificate["row"]))
        evaluation = exact_violation(domain, by_family[family], certificate, denominator, numerators)
        assert key == attempt["row_sha256"] and evaluation == attempt["exact_evaluation"]
        if evaluation["violated"]:
            if key in seen:
                assert attempt["duplicate_of"] == seen[key] and "retained_index" not in attempt
            else:
                assert attempt["retained_index"] == len(seen)
                retained = {**certificate, "exact_evaluation": evaluation,
                            "direction_index": attempt["direction_index"], "scale": attempt["scale"]}
                assert result["cuts"][len(seen)] == retained
                seen[key] = len(seen)
                counts[family] += 1
        else:
            assert "retained_index" not in attempt and "duplicate_of" not in attempt
    assert len(seen) == len(result["cuts"])
    for record in result["families"]:
        assert record["cuts"] == counts[record["family"]] <= MAX_CUTS_PER_FAMILY
        assert len(record["directions"]) <= MAX_DIRECTIONS_PER_FAMILY
    return {"status": "PASS: all retained Schur inequalities and proposal gaps exactly replayed",
            **bindings(), "result_file_sha256": sha(Path(result_path).read_bytes()),
            "retained_cuts": len(seen), "family_counts": counts, "attempts_replayed": len(result["attempts"]),
            "full_original_pair_positions": 114960, "all480_selectors_retained": True,
            "eigendecompositions": 0, "optimizer_calls": 0, "seconds": time.monotonic()-started,
            "proposal_feasibility_claimed": False, "no_cut_means_PSD_claimed": False}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("prepare", "replay-preparation", "scan", "replay"))
    parser.add_argument("--preparation", type=Path)
    parser.add_argument("--proposal", type=Path, default=LOGS/PROPOSAL_FILE)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--result", type=Path)
    parser.add_argument("--seconds", type=float)
    args = parser.parse_args()
    if args.mode == "prepare":
        result = preparation(args.seconds or 120)
        save_new(args.output, result)
    elif args.mode == "replay-preparation":
        expected = json.loads(args.preparation.read_bytes())
        result = preparation(args.seconds or 120)
        assert result == expected
        result = {"status": "PASS: cold exact preparation replay", **bindings(),
                  "preparation_sha256": sha(args.preparation.read_bytes()), "optimizer_calls": 0,
                  "eigendecompositions": 0}
        save_new(args.output, result)
    elif args.mode == "scan":
        assert args.preparation is not None
        result = scan(args.preparation, args.proposal, args.output, args.seconds or MAX_SCAN_SECONDS)
    else:
        assert args.preparation is not None and args.result is not None
        result = replay(args.result, args.preparation, args.proposal, args.seconds or 120)
        save_new(args.output, result)
    print(json.dumps({k: result[k] for k in ("status", "source_sha256", "optimizer_calls", "eigendecompositions")
                      if k in result}, sort_keys=True))


if __name__ == "__main__":
    main()
