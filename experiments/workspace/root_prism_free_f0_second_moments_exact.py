"""Exact arithmetic and bounded reconstruction for the F0 second-moment LP.

No optimizer is imported or called by this module. Numerical active faces
and rounded free coordinates are proposals only; all model rows decide
whether the reconstructed point is accepted.
"""
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import re
import time

MODEL_SHA256 = "df20b045881fbb39233aa88b870f76715b1233920a00d9a53373cd8025d5de91"
MODEL_FILE_SHA256 = "404d91da35c798ba248887c22a7500957947e24b71d5197dc44432460e6d219e"
MATRIX_SHA256 = "0f97fd60d2b0b24fa75e6a3d0ee96363b98fb7ea652611d3779ef38946ae8bd1"
BASE_MODEL_FILE_SHA256 = "703206929c9c85a40ac4ddcbfb1708c716c288482cf50c77a32249404e35b782"
BASE_EXACT_SOURCE_SHA256 = "c209ee3ceef72d4a9352a3bed37d70dfe7aef8c7ced239752e4316b5b5c0afaf"
MAX_POINT_BITS = 8192
MAX_REDUCED_COLUMNS = 1600
MAX_FREE_COORDINATES = 64
MAX_DENSE_FACE_CELLS = 8_000_000
PRIME = 65521
ACTIVE_TOLERANCE = 1e-8

def canonical(data):
    return json.dumps(data, ensure_ascii=True, separators=(",", ":")).encode()

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def object_hash(data):
    return hashlib.sha256(canonical(data)).hexdigest()

def save(path, data):
    path = Path(path)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(data, indent=2) + "\n")
    temporary.replace(path)

def integer(value):
    if type(value) is int:
        return value
    if type(value) is str and re.fullmatch(r"-?(0|[1-9][0-9]*)", value):
        return int(value)
    raise ValueError("exact integer or canonical integer string required")

def tick(deadline):
    if time.monotonic() > deadline:
        raise TimeoutError("exact phase budget")

def load_model(path):
    import gzip
    raw = Path(path).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == MODEL_FILE_SHA256
    model = json.loads(gzip.decompress(raw))
    assert object_hash(model) == MODEL_SHA256
    assert object_hash(model["matrix"]) == MATRIX_SHA256
    matrix = model["matrix"]
    assert matrix["variables"] == 15589
    assert len(matrix["equalities"]) == 7165 and len(matrix["inequalities"]) == 46122
    assert sum(len(r["terms"]) for r in matrix["equalities"] + matrix["inequalities"]) == 279627
    assert matrix["lower"] == 0 and matrix["upper"] == 1
    assert model["scope"]["point_independent"] and model["scope"]["every_distinct_selector_pair_represented"]
    assert not model["scope"]["second_component_or_alignment_fixed"]
    for row in matrix["equalities"] + matrix["inequalities"]:
        assert type(row["rhs"]) is int and abs(row["rhs"]) < 2**53
        ids = [j for j, c in row["terms"]]
        assert ids == sorted(set(ids))
        assert all(type(j) is int and 0 <= j < 15589 and type(c) is int and abs(c) < 2**53
                   for j, c in row["terms"])
    base_path = Path(__file__).resolve().parents[1] / "logs/root-prism-free/f0-boolean-fractional-model.json.gz"
    base_raw = base_path.read_bytes()
    assert hashlib.sha256(base_raw).hexdigest() == BASE_MODEL_FILE_SHA256
    base = json.loads(gzip.decompress(base_raw))
    assert matrix["equalities"][:686] == base["matrix"]["equalities"]
    assert matrix["inequalities"][:11449] == base["matrix"]["inequalities"]
    # Only the loaded in-memory object is extended. The bound model bytes and
    # every mathematical row remain unchanged.
    model["_baseline"] = base
    return model


_BASE_HELPER = None


def baseline_helper():
    global _BASE_HELPER
    if _BASE_HELPER is None:
        import importlib.util
        path = Path(__file__).with_name("root_prism_free_f0_fractional_native_exact.py")
        assert digest(path) == BASE_EXACT_SOURCE_SHA256
        spec = importlib.util.spec_from_file_location("f0_original_exact_baseline", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        _BASE_HELPER = module
    return _BASE_HELPER

def common_point(values):
    denominator = 1
    for value in values:
        denominator = math.lcm(denominator, value.denominator)
        if denominator.bit_length() > MAX_POINT_BITS:
            raise ArithmeticError("point denominator resource bound")
    numerators = [value.numerator * (denominator // value.denominator) for value in values]
    common = denominator
    for value in numerators:
        common = math.gcd(common, abs(value))
    denominator //= common
    numerators = [value // common for value in numerators]
    if max([denominator.bit_length()] + [abs(v).bit_length() for v in numerators]) > MAX_POINT_BITS:
        raise ArithmeticError("point numerator resource bound")
    return {"denominator": str(denominator), "numerators": list(map(str, numerators))}

def quotient_check(matrix, point):
    denominator = integer(point["denominator"])
    values = list(map(integer, point["numerators"]))
    assert denominator > 0 and len(values) == matrix["variables"]
    failures = {"bounds": sum(v < 0 or v > denominator for v in values),
                "equalities": 0, "inequalities": 0}
    first = []
    for kind in ("equalities", "inequalities"):
        for i, row in enumerate(matrix[kind]):
            residual = sum(c * values[j] for j, c in row["terms"]) - row["rhs"] * denominator
            bad = residual != 0 if kind == "equalities" else residual > 0
            if bad:
                failures[kind] += 1
                if len(first) < 12:
                    first.append([kind, i, str(residual)])
    return {"passed": not any(failures.values()), "failures": failures, "first_failures": first}

def literal_moment_check(x, Z, selector_rows, edges, Y, zero_pairs, denominator):
    n = len(x)
    assert denominator > 0 and len(Z) == n and all(len(row) == n for row in Z)
    assert len(edges) == len(Y)
    failures = {"diagonal": 0, "symmetry": 0, "pair_bounds": 0,
                "RLT_equalities": 0, "Y_le_Z": 0, "certified_zeros": 0}
    for a in range(n):
        failures["diagonal"] += Z[a][a] != x[a]
        for b in range(a+1, n):
            value = Z[a][b]
            failures["symmetry"] += value != Z[b][a]
            failures["pair_bounds"] += not (0 <= value <= x[a] and value <= x[b]
                                            and value >= x[a]+x[b]-denominator)
        for row in selector_rows:
            failures["RLT_equalities"] += (sum(Z[a][b] for b in row["support"]) != row["quota"]*x[a])
    for (a, b), value in zip(edges, Y):
        failures["Y_le_Z"] += not (0 <= value <= Z[a][b])
    for a, b in zero_pairs:
        failures["certified_zeros"] += Z[a][b] != 0
    return {"passed": not any(failures.values()), "failures": failures,
            "full_RLT_equalities_checked": n*len(selector_rows),
            "full_pair_bound_rows_checked": 3*n*(n-1)//2,
            "full_Y_le_Z_rows_checked": len(edges),
            "full_zero_rows_checked": len(zero_pairs)}


def full_point_check(model, point):
    quotient = quotient_check(model["matrix"], point)
    if not quotient["passed"]:
        return {"passed": False, "quotient": quotient}
    values = list(map(integer, point["numerators"]))
    den = integer(point["denominator"])
    base = model["_baseline"]
    base_point = {"denominator": str(den), "numerators": list(map(str, values[:5847]))}
    baseline = baseline_helper().full_point_check(base, base_point)
    assert baseline["passed"], "preserved baseline prefix discrepancy"
    data = base["validation"]
    x = [None]*480
    Y = [None]*68394
    for o, members in enumerate(data["selector_orbits"]):
        for a in members:
            assert x[a] is None
            x[a] = values[o]
    for o, members in enumerate(data["edge_orbits"]):
        for e in members:
            assert Y[e] is None
            Y[e] = values[42+o]
    assert None not in x and None not in Y
    Boolean_bad = 0
    for row in base["Boolean_validation"]["full_rows"]:
        residual = sum(integer(c)*x[a] for a, c in row["terms"]) - integer(row["rhs"])*den
        Boolean_bad += residual > 0
    assert len(base["Boolean_validation"]["full_rows"]) == 4416
    pairs = [(a, b) for a in range(480) for b in range(a+1, 480)]
    assert len(pairs) == len(model["pair_to_orbit"]) == 114960
    Z = [[None]*480 for _ in range(480)]
    for a in range(480):
        Z[a][a] = x[a]
    for o, members in enumerate(model["pair_orbits"]):
        value = values[5847+o]
        for p in members:
            a, b = pairs[p]
            assert model["pair_to_orbit"][p] == o and Z[a][b] is None and Z[b][a] is None
            Z[a][b] = Z[b][a] = value
    assert all(None not in row for row in Z)
    zeros = [pairs[c["pair_id"]] for c in model["zero_moment_certificates"]]
    moment = literal_moment_check(x, Z, model["original_selector_equalities"],
                                 data["edges"], Y, zeros, den)
    bounds_bad = sum(v < 0 or v > den for v in x+Y)
    bounds_bad += sum(Z[a][b] < 0 or Z[a][b] > den for a, b in pairs)
    passed = moment["passed"] and Boolean_bad == 0 and bounds_bad == 0
    return {"passed": passed, "quotient": quotient, "baseline": baseline,
            "full_Boolean_rows_checked": 4416, "full_Boolean_failures": Boolean_bad,
            "literal_moments": moment, "full_bound_failures": bounds_bad,
            "full_rows_checked": 650350, "full_variable_bounds_checked": 183834,
            "common_denominator_bits": den.bit_length(),
            "maximum_numerator_bits": max(abs(v).bit_length() for v in values),
            "PSD_conditions_enforced_or_certified": False}

def evaluate_farkas(matrix, certificate):
    lam = list(map(integer, certificate["equality_multipliers"]))
    mu = list(map(integer, certificate["inequality_multipliers"]))
    assert len(lam) == len(matrix["equalities"]) and len(mu) == len(matrix["inequalities"])
    if any(v < 0 for v in mu):
        raise ValueError("nonnegative inequality multipliers required")
    combined = [0] * matrix["variables"]
    rhs = 0
    for rows, multipliers in ((matrix["equalities"], lam), (matrix["inequalities"], mu)):
        for row, value in zip(rows, multipliers):
            rhs += value * row["rhs"]
            for j, coefficient in row["terms"]:
                combined[j] += value * coefficient
    deficits = sum(max(-v, 0) for v in combined)
    gap = rhs + deficits
    return {"rhs": str(rhs), "upper_deficit_sum": str(deficits), "gap": str(gap),
            "strict_infeasibility": gap < 0, "variables": matrix["variables"],
            "equality_rows": len(lam), "inequality_rows": len(mu)}

def numerical_farkas(matrix, ray, deadline, attempts):
    assert len(ray) == len(matrix["equalities"]) + len(matrix["inequalities"])
    assert all(math.isfinite(v) for v in ray)
    exact = list(map(Fraction, ray))
    dyadic = max(v.denominator for v in exact)
    scales = [1, 2, 3, 4, 6, 12, 24, 60, 120, 720, 4096, 10**6]
    if dyadic.bit_length() <= MAX_POINT_BITS:
        scales.append(dyadic)
    equality_count = len(matrix["equalities"])
    seen = set()
    for scale in dict.fromkeys(scales):
        for orientation in (-1, 1):
            tick(deadline)
            lam = [round(orientation * scale * v) for v in exact[:equality_count]]
            mu = [max(0, round(orientation * scale * v)) for v in exact[equality_count:]]
            divisor = math.gcd(*(abs(v) for v in lam + mu))
            if divisor > 1:
                lam = [v // divisor for v in lam]
                mu = [v // divisor for v in mu]
            key = tuple(lam + mu)
            if key in seen:
                continue
            seen.add(key)
            cert = {"equality_multipliers": list(map(str, lam)),
                    "inequality_multipliers": list(map(str, mu))}
            check = evaluate_farkas(matrix, cert)
            attempts.append({"method": "exact finite-box deficits", "scale": str(scale),
                             "orientation": orientation, "gap": check["gap"]})
            if check["strict_infeasibility"]:
                return cert, check
    return None

def modular_minor(rows, columns, deadline):
    import numpy as np
    assert all(PRIME % k for k in range(2, math.isqrt(PRIME) + 1))
    if not columns or not rows:
        return {"rank": 0, "rows": [], "columns": [], "prime": PRIME}
    assert all(type(v) is int and -(1 << 63) < v < (1 << 63) for row in rows for v in row)
    matrix = np.asarray(rows, dtype=np.int64) % PRIME
    assert matrix.shape == (len(rows), columns)
    identities = list(range(len(rows)))
    selected_columns = []
    rank = 0
    for column in range(columns):
        tick(deadline)
        candidates = np.flatnonzero(matrix[rank:, column])
        if not len(candidates):
            continue
        pivot_row = rank + int(candidates[0])
        if pivot_row != rank:
            matrix[[rank, pivot_row], :] = matrix[[pivot_row, rank], :]
            identities[rank], identities[pivot_row] = identities[pivot_row], identities[rank]
        pivot = int(matrix[rank, column])
        inverse = pow(pivot, PRIME - 2, PRIME)
        assert pivot * inverse % PRIME == 1
        matrix[rank, column:] = matrix[rank, column:] * inverse % PRIME
        active = rank + 1 + np.flatnonzero(matrix[rank + 1:, column])
        if len(active):
            factors = matrix[active, column].copy()
            # Every factor and matrix entry is below65521; products fit signed int64.
            matrix[active, column:] = (matrix[active, column:] -
                factors[:, None] * matrix[rank, column:][None, :]) % PRIME
        selected_columns.append(column)
        rank += 1
        if rank == len(rows):
            break
    return {"rank": rank, "rows": identities[:rank], "columns": selected_columns, "prime": PRIME,
            "rational_rank_inferred_from_modular_rank": False}

def active_face(matrix, numeric):
    n = matrix["variables"]
    parent = list(range(n))
    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a
    def union(a, b):
        a, b = find(a), find(b)
        if a != b:
            parent[max(a, b)] = min(a, b)
    activation_count = 0
    active_other = []
    for index, row in enumerate(matrix["inequalities"]):
        residual = sum(c * numeric[j] for j, c in row["terms"]) - row["rhs"]
        if abs(residual) > ACTIVE_TOLERANCE:
            continue
        # Any active zero-RHS unit difference proposes an equality alias.
        # This includes old activation, Z<=x and Y<=Z, without changing the LP.
        if (row["rhs"] == 0 and len(row["terms"]) == 2 and
                sorted(c for _, c in row["terms"]) == [-1, 1]):
            union(row["terms"][0][0], row["terms"][1][0])
            activation_count += 1
        else:
            active_other.append(index)
    root = [find(j) for j in range(n)]
    fixed = {}
    for j, value in enumerate(numeric):
        boundary = 0 if abs(value) <= ACTIVE_TOLERANCE else 1 if abs(value - 1) <= ACTIVE_TOLERANCE else None
        if boundary is not None:
            if root[j] in fixed and fixed[root[j]] != boundary:
                raise ArithmeticError("proposed active face has conflicting fixed bounds")
            fixed[root[j]] = boundary
    free = sorted(set(root) - set(fixed))
    if len(free) > MAX_REDUCED_COLUMNS:
        raise ArithmeticError("active-face column resource bound")
    positions = {r: j for j, r in enumerate(free)}
    rows, rhs, provenance = [], [], []
    prescribed = [("equality", i, row) for i, row in enumerate(matrix["equalities"])]
    prescribed += [("active inequality", i, matrix["inequalities"][i]) for i in active_other]
    for kind, index, row in prescribed:
        dense = [0] * len(free)
        value = row["rhs"]
        for j, coefficient in row["terms"]:
            r = root[j]
            if r in fixed:
                value -= coefficient * fixed[r]
            else:
                dense[positions[r]] += coefficient
        if not any(dense):
            if value:
                raise ArithmeticError("numerically chosen active face is exactly inconsistent")
            continue
        if (len(rows)+1)*len(free) > MAX_DENSE_FACE_CELLS:
            raise ArithmeticError("active-face dense-cell resource bound")
        rows.append(dense)
        rhs.append(value)
        provenance.append([kind, index])
    return {"root": root, "fixed": fixed, "free": free, "rows": rows, "rhs": rhs,
            "provenance": provenance, "active_unit_difference_aliases_used": activation_count,
            "active_other_rows": active_other}

def recover_active_face(matrix, numeric, deadline, progress_path=None):
    from flint import fmpq, fmpq_mat
    tick(deadline)
    face = active_face(matrix, numeric)
    minor = modular_minor(face["rows"], len(face["free"]), deadline)
    pivot_rows, pivot_columns = minor["rows"], minor["columns"]
    nonpivots = sorted(set(range(len(face["free"]))) - set(pivot_columns))
    if len(nonpivots) > MAX_FREE_COORDINATES:
        raise ArithmeticError("active-face free-coordinate resource bound")
    proposed = {j: Fraction(numeric[face["free"][j]]).limit_denominator(10**9) for j in nonpivots}
    metadata = {"method": "one active-face modular minor and rational solve",
                "active_unit_difference_aliases": face["active_unit_difference_aliases_used"],
                "active_other_rows": face["active_other_rows"],
                "reduced_columns": len(face["free"]), "reduced_rows": len(face["rows"]),
                "minor": minor, "minor_original_rows": [face["provenance"][i] for i in pivot_rows],
                "free_coordinate_proposals": [[j, str(v.numerator), str(v.denominator)] for j, v in proposed.items()],
                "active_face_is_a_proposal_not_a_model_restriction": True}
    if progress_path is not None:
        save(progress_path, metadata)
    if pivot_columns:
        square = [[face["rows"][i][j] for j in pivot_columns] for i in pivot_rows]
        rhs = [Fraction(face["rhs"][i]) - sum((face["rows"][i][j] * v for j, v in proposed.items()), Fraction(0))
               for i in pivot_rows]
        tick(deadline)
        solution = fmpq_mat(square).solve(fmpq_mat([[fmpq(v.numerator, v.denominator)] for v in rhs]), algorithm="dixon")
        numerators, denominator = solution.numer_denom()
        for k, j in enumerate(pivot_columns):
            proposed[j] = Fraction(int(numerators[k, 0]), int(denominator))
        tick(deadline)
    group_values = {r: Fraction(v) for r, v in face["fixed"].items()}
    for j, r in enumerate(face["free"]):
        group_values[r] = proposed[j]
    result = [group_values[r] for r in face["root"]]
    return common_point(result), metadata

def recover_point(model, numeric, deadline, attempts, progress_path):
    matrix = model["matrix"]
    assert len(numeric) == matrix["variables"] and all(math.isfinite(v) for v in numeric)
    for maximum_denominator in (1000, 10**6, 10**9):
        tick(deadline)
        try:
            values = [Fraction(0) if abs(v) <= ACTIVE_TOLERANCE else Fraction(1) if abs(v - 1) <= ACTIVE_TOLERANCE
                      else Fraction(v).limit_denominator(maximum_denominator) for v in numeric]
            point = common_point(values)
            check = full_point_check(model, point)
            attempts.append({"method": "direct rational proposal", "maximum_denominator": maximum_denominator,
                             "quotient": check["quotient"]})
            if check["passed"]:
                return point, check, {"method": "direct rational proposal", "maximum_denominator": maximum_denominator}
        except ArithmeticError as error:
            attempts.append({"method": "direct rational proposal", "maximum_denominator": maximum_denominator, "rejected": str(error)})
    tick(deadline)
    point, metadata = recover_active_face(matrix, numeric, deadline, progress_path)
    check = full_point_check(model, point)
    attempts.append({"method": metadata["method"], "quotient": check["quotient"]})
    if check["passed"]:
        return point, check, metadata
    return None

def exact_phase(model_path, numerical_path, output_path, seconds):
    started = time.monotonic()
    deadline = started + seconds
    model = load_model(model_path)
    numerical = json.loads(Path(numerical_path).read_text())
    assert numerical["model_sha256"] == MODEL_SHA256
    result = {"kind": "unresolved", "status": "UNKNOWN: no exact certificate reconstructed",
              "model_sha256": MODEL_SHA256, "helper_source_sha256": digest(__file__),
              "numerical_file_sha256": digest(numerical_path), "requested_seconds": seconds,
              "attempts": [], "optimizer_calls": 0, "PSD_conditions_enforced_or_certified": False}
    save(output_path, result)
    try:
        ray = [float.fromhex(v) for v in numerical.get("existing_dual_ray_hex", [])]
        values = [float.fromhex(v) for v in numerical.get("col_value_hex", [])]
        phases = ("ray", "point") if "Infeasible" in numerical.get("numerical_status", "") else ("point", "ray")
        for phase in phases:
            tick(deadline)
            if phase == "point" and len(values) == model["matrix"]["variables"]:
                accepted = recover_point(model, values, deadline, result["attempts"],
                                         Path(output_path).with_name("exact-progress.json"))
                if accepted is not None:
                    point, check, method = accepted
                    result.update(kind="point", status="EXACT_LINEAR_POINT_FOUND: independent full replay pending",
                                  point=point, exact_check=check, reconstruction=method)
                    break
            if phase == "ray" and ray:
                accepted = numerical_farkas(model["matrix"], ray, deadline, result["attempts"])
                if accepted is not None:
                    certificate, check = accepted
                    result.update(kind="farkas", status="EXACT_LINEAR_FARKAS_FOUND: independent full replay pending",
                                  certificate=certificate, exact_check=check)
                    break
    except (ArithmeticError, TimeoutError) as error:
        result["status"] = "UNKNOWN: bounded exact reconstruction stopped"
        result["reconstruction_stop"] = str(error)
    except Exception as error:
        result["status"] = "ERROR: exact phase stopped"
        result["error_type"], result["error_message"] = type(error).__name__, str(error)
        raise
    finally:
        result["elapsed_seconds"] = time.monotonic() - started
        result["cooperative_overrun_seconds"] = max(0, result["elapsed_seconds"] - seconds)
        save(output_path, result)
    return result

def literal_moment_controls():
    # Two actual binary selections on four points, averaged with denominator2.
    subsets = [{0, 1}, {2, 3}]
    x = [sum(a in selected for selected in subsets) for a in range(4)]
    Z = [[sum(a in selected and b in selected for selected in subsets) for b in range(4)] for a in range(4)]
    rows = [{"support": [0, 1, 2, 3], "quota": 2},
            {"support": [0, 2], "quota": 1}, {"support": [1, 3], "quota": 1}]
    edges, Y, zeros = [[0, 1], [2, 3]], [1, 1], [[0, 2], [0, 3], [1, 2], [1, 3]]
    assert literal_moment_check(x, Z, rows, edges, Y, zeros, 2)["passed"]
    rejected = 0
    for a, b, value in ((0, 0, 0), (0, 1, 0), (0, 2, 1), (0, 1, 2), (0, 1, -1)):
        changed = [row[:] for row in Z]
        changed[a][b] = changed[b][a] = value
        assert not literal_moment_check(x, changed, rows, edges, Y, zeros, 2)["passed"]
        rejected += 1
    assert not literal_moment_check(x, Z, rows, edges, [2, 1], zeros, 2)["passed"]
    assert not literal_moment_check([2, 2], [[2, 0], [0, 2]], [], [], [], [], 2)["passed"]
    return {"positive_binary_mixture": True, "invalid_moment_mutations_rejected": rejected,
            "excess_Y_rejected": True, "Frechet_lower_bound_control": True,
            "production_model_feasibility_claimed": False}


def controls():
    model = {"variables": 2, "equalities": [{"terms": [[0, 1], [1, 1]], "rhs": 1}],
             "inequalities": [{"terms": [[0, 1], [1, -1]], "rhs": 0}]}
    assert quotient_check(model, {"denominator": "3", "numerators": ["1", "2"]})["passed"]
    assert not quotient_check(model, {"denominator": "3", "numerators": ["1", "1"]})["passed"]
    checks = 0
    for lam in range(-8, 9):
        for mu in range(9):
            assert not evaluate_farkas(model, {"equality_multipliers": [lam], "inequality_multipliers": [mu]})["strict_infeasibility"]
            checks += 1
    bad_eq = {"variables": 2, "equalities": [{"terms": [[0, 1], [1, 1]], "rhs": 3}], "inequalities": []}
    assert evaluate_farkas(bad_eq, {"equality_multipliers": [-1], "inequality_multipliers": []})["gap"] == "-1"
    bad_ineq = {"variables": 1, "equalities": [], "inequalities": [{"terms": [[0, 1]], "rhs": -1}]}
    assert evaluate_farkas(bad_ineq, {"equality_multipliers": [], "inequality_multipliers": [1]})["gap"] == "-1"
    assert evaluate_farkas(bad_eq, {"equality_multipliers": [str(-(1 << 130))], "inequality_multipliers": []})["gap"] == str(-(1 << 130))
    try:
        evaluate_farkas(model, {"equality_multipliers": [0], "inequality_multipliers": [-1]})
    except ValueError:
        pass
    else:
        raise AssertionError("negative inequality multiplier accepted")
    toy = {"variables": 3, "equalities": [{"terms": [[0, 1], [1, 1]], "rhs": 1}],
           "inequalities": [{"terms": [[0, -1], [2, 1]], "rhs": 0, "family": "activation"},
                            {"terms": [[1, -1], [2, 1]], "rhs": 0, "family": "activation"}]}
    point, metadata = recover_active_face(toy, [0.5, 0.5, 0.5], time.monotonic() + 10)
    assert quotient_check(toy, point)["passed"] and point == {"denominator": "2", "numerators": ["1", "1", "1"]}
    assert metadata["reduced_columns"] == metadata["minor"]["rank"] == 1
    swap = modular_minor([[0, 1], [1, 0]], 2, time.monotonic() + 10)
    assert swap["rank"] == 2 and swap["rows"] == [1, 0]
    return {"status": "PASS: exact point, ray, alias-face and modular controls",
            "feasible_box_multiplier_checks": checks, "strict_infeasible_controls": 3,
            "negative_inequality_multiplier_rejected": True, "large_multiplier_bits": 131,
            "positive_point_control": True, "deleted_mass_negative_control": True,
            "active_face_exact_solve_control": True, "modular_row_swap_control": True,
            "literal_second_moment_controls": literal_moment_controls(),
            "active_face_limits": {"columns": MAX_REDUCED_COLUMNS, "free_coordinates": MAX_FREE_COORDINATES, "dense_cells": MAX_DENSE_FACE_CELLS},
            "optimizer_calls": 0}
