"""Bounded signed-integer construction for the complete case4 equalities.

Three saved modular pivot sets select rational basic-point proposals. Every
proposal must pass every original equality before Bezout composition is used.
The final 1214-coordinate integer vector is the authoritative certificate.
No binary bounds, inequalities, HNF, SNF, or optimizer are used in this task.
"""
import argparse
import gzip
import hashlib
import importlib
import importlib.metadata
from itertools import product
import json
from math import gcd
import os
from pathlib import Path
import re
import subprocess
import sys
import time

for _name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[_name] = "1"

import rook_case4_face99_affine_modular as mod

ROOT, BASE = mod.ROOT, mod.BASE
MODULAR_SOURCE_SHA = "c09b76ed3570ca0fec17c2446a8222cb9c556ad5664f665adf38a5f473b188db"
MODULAR_RESULT = BASE+"rook-case4-face99-affine-modular-run01/result.json"
MODULAR_RESULT_SHA = "e45439adddd20ddf8ec564ffe7eae3a733475ca1e281998fe42f7133b9779f7a"
MODULAR_COLD = BASE+"rook-case4-face99-affine-modular-run01-replay.json"
MODULAR_COLD_SHA = "0bf5fb3687db3fd81a5cf270cc6b30666f1c22c7318878f201d7720f8abf29b0"
PRIMES = (19, 601, 145463)
PRIME_FILES = {
    19: ("103c0284cb7afa84db4d1d417e751182680593c9be186deaf7862b239466c848",
         "0ab708814f3a5384599757b56cc202e3044822ba6f8d862acedc1a161db5831d"),
    601: ("ac6a031b918c8a3341fa0b2529ebdd0b4a63d9a062e5c085f1ce74eef67ad293",
          "5c5d3704ddc0b4e894788bb9ccdef3fdd5781c0b99d7c37cc79f6455869e6efe"),
    145463: ("2726a51540cf823c0b917f30da51a5a3f65f3ccd65a565fde3b990282405bb89",
             "be69a348be209739849274e87ec5fe2c0ad603b59f113c1ec677e4f5adeab8d8"),
}
LIMITS = {"minor_preparation_seconds": 60, "owned_exact_child_seconds": 60,
          "cold_replay_seconds": 60, "maximum_basic_solves": 3,
          "maximum_output_integer_bits": 4096, "maximum_artifact_bytes": 20 << 20,
          "owned_child_address_space_bytes": 3 << 30, "automatic_retries": 0,
          "optimizer_calls": 0, "HNF_calls": 0, "SNF_calls": 0}
sha, canonical = mod.sha, mod.canonical


def tick(deadline):
    if time.monotonic() >= deadline:
        raise TimeoutError("bounded integer-point construction or exact replay")


def integer(value):
    if type(value) is int:
        return value
    assert isinstance(value, str) and re.fullmatch(r"0|-?[1-9][0-9]*", value)
    return int(value)


def bounded(values):
    assert all(type(value) is int for value in values)
    largest = max((abs(value).bit_length() for value in values), default=0)
    if largest > LIMITS["maximum_output_integer_bits"]:
        raise ArithmeticError("saved integer output exceeds the explicit bit limit")
    return largest


def save(path, value):
    raw = (json.dumps(value, indent=2)+"\n").encode()
    if len(raw) > LIMITS["maximum_artifact_bytes"]:
        raise ArithmeticError("artifact byte limit")
    temporary = path.with_name(path.name+".partial")
    temporary.write_bytes(raw)
    temporary.replace(path)


def normalize(nums, den):
    assert type(den) is int and den > 0 and all(type(v) is int for v in nums)
    divisor = gcd(den, *nums)
    return [v//divisor for v in nums], den//divisor, divisor


def bezout(a, b):
    assert type(a) is int and type(b) is int and a > 0 and b > 0
    old_r, r, old_s, s, old_t, t = a, b, 1, 0, 0, 1
    while r:
        quotient = old_r//r
        old_r, r = r, old_r-quotient*r
        old_s, s = s, old_s-quotient*s
        old_t, t = t, old_t-quotient*t
    assert old_s*a+old_t*b == old_r == gcd(a, b)
    assert abs(old_s) <= b//old_r and abs(old_t) <= a//old_r
    return old_s, old_t, old_r


def combine(nums, den, other, other_den):
    assert len(nums) == len(other)
    u, v, g = bezout(den, other_den)
    raw = [u*a+v*b for a, b in zip(nums, other)]
    bits = bounded(raw+[g, u, v])
    answer, answer_den, divisor = normalize(raw, g)
    return answer, answer_den, {"left_multiplier": str(u), "right_multiplier": str(v),
        "left_denominator": str(den), "right_denominator": str(other_den),
        "Bezout_gcd": str(g), "normalization_divisor": str(divisor),
        "combined_denominator": str(answer_den), "maximum_saved_combination_bits": bits}


def check_equations(equations, nums, den, deadline=float("inf")):
    assert type(den) is int and den > 0 and all(type(v) is int for v in nums)
    for index, row in enumerate(equations):
        tick(deadline)
        assert sum(c*nums[a] for a, c in row["terms"]) == row["right_hand_side"]*den, \
            ("full affine equality failed", index)
    return len(equations)


def check_original(data, native, nums, den, deadline=float("inf")):
    assert len(nums) == 1214 and type(den) is int and den > 0
    bits = bounded(nums+[den])
    assert all(nums[a] == 0 for a in data["zero_columns"])
    count = 0
    for original_id, row in enumerate(native):
        if row["lower"] == row["upper"]:
            tick(deadline)
            assert sum(c*nums[a] for a, c in row["terms"]) == row["lower"]*den, \
                ("original native equality failed", original_id)
            count += 1
    assert count == 632
    reduced = [nums[a] for a in data["original_column_ids"]]
    assert check_equations(data["equations"], reduced, den, deadline) == 396
    return {"original_coordinates": 1214, "original_equality_rows": count,
            "distinct_nonempty_equations": 396, "proved_zero_coordinates": 99,
            "negative_coordinates": sum(v < 0 for v in nums),
            "positive_coordinates": sum(v > 0 for v in nums),
            "zero_coordinates": sum(v == 0 for v in nums),
            "maximum_saved_integer_bits": bits,
            "binary_or_nonnegative_feasibility_claimed": False,
            "inequalities_and_covers_checked": False}


def runtime():
    module = importlib.import_module("flint.types.fmpq_mat")
    return {"python": sys.version, "python_flint_version": importlib.metadata.version("python-flint"),
            "flint_fmpq_mat_native_sha256": sha(Path(module.__file__).read_bytes()),
            "numpy": mod.runtime(), "runtime_installed_or_modified": False}


def load_inputs(deadline=float("inf")):
    assert sha(Path(mod.__file__).read_bytes()) == MODULAR_SOURCE_SHA
    inventory_bindings, data, native = mod.load_inventory()
    result = mod.inv.checked_json(ROOT, MODULAR_RESULT, MODULAR_RESULT_SHA)
    cold = mod.inv.checked_json(ROOT, MODULAR_COLD, MODULAR_COLD_SHA)
    assert result["complete_all_planned_primes"] and cold["complete_all_planned_primes"]
    assert cold["result_sha256"] == MODULAR_RESULT_SHA and cold["status"].startswith("PASS")
    proofs = {}
    for p in PRIMES:
        tick(deadline)
        raw = (ROOT/(BASE+f"rook-case4-face99-affine-modular-run01/prime-{p}.json.gz")).read_bytes()
        assert sha(raw) == PRIME_FILES[p][0]
        plain = gzip.decompress(raw)
        assert sha(plain) == PRIME_FILES[p][1]
        proof = json.loads(plain)
        checked = mod.verify(data["equations"], 1115, proof, deadline)
        assert checked["kind"] == "consistent_complete_rowspace" and checked["rank"] == 286
        assert checked["fixed_coordinates"] == []
        proofs[p] = proof
    point = mod.inv.checked_json(ROOT, *mod.inv.INPUTS["point"])
    den = integer(point["common_denominator"])
    values = [integer(v) for v in point["extended_numerators"]]
    assert len(values) == 1116 and den == mod.inv.DENOMINATOR
    nums = [0]*1214
    for a, value in zip(data["original_column_ids"], values[:-1]):
        nums[a] = value
    check = check_original(data, native, nums, den, deadline)
    assert gcd(den, *nums) == 1
    assert den == 19*601*145463
    bindings = {"source_sha256": sha(Path(__file__).read_bytes()),
        "modular_source_sha256": MODULAR_SOURCE_SHA, "inventory": inventory_bindings,
        "modular_result_sha256": MODULAR_RESULT_SHA, "modular_cold_sha256": MODULAR_COLD_SHA,
        "prime_certificates": {str(p): {"gzip_sha256": PRIME_FILES[p][0], "raw_sha256": PRIME_FILES[p][1]}
                               for p in PRIMES},
        "saved_point_sha256": mod.inv.INPUTS["point"][1]}
    return bindings, data, native, proofs, nums, den, check


def minor_rows(equations, columns, row_ids):
    positions = {j: k for k, j in enumerate(columns)}
    return [{"terms": [[positions[j], c] for j, c in equations[i]["terms"] if j in positions],
             "right_hand_side": equations[i]["right_hand_side"]} for i in row_ids]


def select_minor(equations, columns, prime, deadline):
    """Transpose pivoting selects original rows; no rational solve occurs."""
    rank = len(columns)
    positions = {a: i for i, a in enumerate(columns)}
    transpose = [{"terms": [], "right_hand_side": 0} for _ in columns]
    for i, row in enumerate(equations):
        for a, c in row["terms"]:
            if a in positions:
                transpose[positions[a]]["terms"].append([i, c])
    proposed = mod.eliminate(transpose, len(equations), prime, deadline)
    if proposed["kind"] != "consistent_complete_rowspace" or len(proposed["pivot_columns"]) != rank:
        raise ArithmeticError("modular column set did not supply a full square minor")
    row_ids = proposed["pivot_columns"]
    transform = proposed["row_combinations"]
    inverse = [[transform[j][i] for j in range(rank)] for i in range(rank)]
    rows = minor_rows(equations, columns, row_ids)
    hadamard_squared = 1
    for row in rows:
        hadamard_squared *= sum(c*c for j, c in row["terms"])+row["right_hand_side"]**2
    certificate = {"prime": prime, "dimension": rank, "columns": columns, "equation_rows": row_ids,
        "square_rows": rows, "right_inverse_mod_prime": inverse,
        "augmented_Hadamard_squared_bound": str(hadamard_squared),
        "Cramer_numerator_denominator_bit_bound": (hadamard_squared.bit_length()+1)//2}
    check_minor(equations, certificate, deadline)
    return certificate


def check_minor(equations, certificate, deadline=float("inf")):
    p, rank = certificate["prime"], certificate["dimension"]
    assert mod.inv.prime_by_trial(p) and rank > 0
    columns, row_ids = certificate["columns"], certificate["equation_rows"]
    assert len(columns) == len(row_ids) == rank
    assert columns == sorted(set(columns)) and row_ids == sorted(set(row_ids))
    assert min(columns) >= 0 and min(row_ids) >= 0 and max(row_ids) < len(equations)
    rows = minor_rows(equations, columns, row_ids)
    assert rows == certificate["square_rows"]
    inverse = certificate["right_inverse_mod_prime"]
    assert len(inverse) == rank and all(len(row) == rank for row in inverse)
    assert all(type(v) is int and 0 <= v < p for row in inverse for v in row)
    product_norm = 1
    for i, row in enumerate(rows):
        tick(deadline)
        got = [0]*rank
        for j, coefficient in row["terms"]:
            for k, value in enumerate(inverse[j]):
                got[k] += coefficient*value
        assert [v % p for v in got] == [int(i == k) for k in range(rank)]
        product_norm *= sum(c*c for j, c in row["terms"])+row["right_hand_side"]**2
    assert product_norm > 0 and str(product_norm) == certificate["augmented_Hadamard_squared_bound"]
    assert (product_norm.bit_length()+1)//2 == certificate["Cramer_numerator_denominator_bit_bound"]
    return {"prime": p, "dimension": rank, "right_inverse_checked_with_Python_integers": True,
            "square_minor_nonsingular_over_Q": True, "determinant_coprime_to_prime": True,
            "full_rational_rowspace_rank_not_asserted": True}


def basic_solve(certificate):
    from flint import fmpq_mat
    rank = certificate["dimension"]
    matrix = [[0]*rank for _ in range(rank)]
    rhs = []
    for i, row in enumerate(certificate["square_rows"]):
        for j, c in row["terms"]:
            matrix[i][j] = c
        rhs.append([row["right_hand_side"]])
    solved = fmpq_mat(matrix).solve(fmpq_mat(rhs), algorithm="dixon")
    numerator_matrix, denominator = solved.numer_denom()
    nums, den, divisor = normalize([int(numerator_matrix[i, 0]) for i in range(rank)], int(denominator))
    bounded(nums+[den])
    assert max([den.bit_length()]+[abs(v).bit_length() for v in nums]) <= \
        certificate["Cramer_numerator_denominator_bit_bound"]
    assert gcd(den, certificate["prime"]) == 1
    return nums, den


def controls():
    euclid, compositions, modular = 0, 0, 0
    for a in range(1, 33):
        for b in range(1, 33):
            bezout(a, b)
            euclid += 1
    for a in range(1, 10):
        for b in range(1, 10):
            rows = [{"terms": [[0, a], [1, b]], "right_hand_side": 1}]
            check_equations(rows, [1, 0], a)
            check_equations(rows, [0, 1], b)
            nums, den, witness = combine([1, 0], a, [0, 1], b)
            check_equations(rows, nums, den)
            assert den == gcd(a, b)
            compositions += 1
    signed, den, witness = combine([1, 0], 2, [0, 1], 3)
    assert signed == [-1, 1] and den == 1
    toy = [{"terms": [[0, 2], [1, 3]], "right_hand_side": 1},
           {"terms": [[2, 1]], "right_hand_side": 2}]
    for p, columns in ((2, [1, 2]), (3, [0, 2]), (5, [0, 2])):
        minor = select_minor(toy, columns, p, float("inf"))
        check_minor(toy, minor)
        local, d = basic_solve(minor)
        full = [0]*3
        for j, v in zip(columns, local):
            full[j] = v
        check_equations(toy, full, d)
        modular += 1
    bad_rows = [{"terms": [[0, 1]], "right_hand_side": 1},
                {"terms": [[1, 1]], "right_hand_side": 1}]
    try:
        check_equations(bad_rows, [1, 0], 1)
    except AssertionError:
        incomplete_point_rejected = True
    else:
        raise AssertionError("minor-only proposal escaped full-row check")
    try:
        select_minor([{"terms": [[0, 4], [1, 6]], "right_hand_side": 2}], [0], 2, float("inf"))
    except ArithmeticError:
        singular_modular_minor_rejected = True
    else:
        raise AssertionError("singular modular proposal accepted")
    check_equations([{"terms": [[0, 4], [1, 6]], "right_hand_side": 2}], [-1, 1], 1)
    forged = json.loads(json.dumps(minor))
    forged["right_inverse_mod_prime"][0][0] = (forged["right_inverse_mod_prime"][0][0]+1) % 5
    try:
        check_minor(toy, forged)
    except AssertionError:
        forged_inverse_rejected = True
    else:
        raise AssertionError("forged modular inverse accepted")
    try:
        bounded([1 << LIMITS["maximum_output_integer_bits"]])
    except ArithmeticError:
        oversized_output_rejected = True
    else:
        raise AssertionError("output bit limit failed")
    try:
        subprocess.run([sys.executable, "-c", "import time; time.sleep(1)"],
                       timeout=0.05, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    except subprocess.TimeoutExpired:
        owned_child_timeout_control = True
    else:
        raise AssertionError("owned-child timeout control failed")
    return {"Bezout_controls": euclid, "rational_compositions": compositions,
        "toy_modular_minor_and_exact_solve_controls": modular,
        "minor_only_point_rejected": incomplete_point_rejected,
        "singular_modular_minor_rejected_without_infeasibility_claim": singular_modular_minor_rejected,
        "forged_inverse_rejected": forged_inverse_rejected, "oversized_output_rejected": oversized_output_rejected,
        "owned_child_timeout_reaped": owned_child_timeout_control,
        "signed_integer_control": signed, "case4_rational_solves": 0,
        "optimizer_calls": 0, "HNF_calls": 0, "SNF_calls": 0}


def prepare(directory):
    assert not directory.exists()
    directory.mkdir(parents=True)
    started = time.monotonic(); deadline = started+LIMITS["minor_preparation_seconds"]
    bindings, data, native, proofs, nums, den, point_check = load_inputs(deadline)
    control = controls()
    minors = []
    for p in PRIMES:
        tick(deadline)
        minor = select_minor(data["equations"], proofs[p]["pivot_columns"], p, deadline)
        assert minor["dimension"] == 286
        minor["original_column_ids"] = [data["original_column_ids"][j] for j in minor["columns"]]
        minor["representative_original_native_rows"] = [
            data["equations"][i]["representative_original_native_row"] for i in minor["equation_rows"]]
        assert minor["Cramer_numerator_denominator_bit_bound"] <= 945
        minors.append(minor)
    maximum_basic_bits = max(v["Cramer_numerator_denominator_bit_bound"] for v in minors)
    maximum_combination_bits = max(den.bit_length(), max(abs(v).bit_length() for v in nums))
    for minor in minors:
        maximum_combination_bits = max(maximum_combination_bits, den.bit_length()) + \
            minor["Cramer_numerator_denominator_bit_bound"]+1
    assert maximum_combination_bits <= 2869 < LIMITS["maximum_output_integer_bits"]
    selection_update_bound = (max(PRIMES)-1)**2+(max(PRIMES)-1)
    selection_dot_bound = 286*(max(PRIMES)-1)**2
    assert max(selection_update_bound, selection_dot_bound) < 2**63
    specification = {"schema": "rook-case4-face99-affine-integer-minors-v1",
        "bindings": bindings, "prime_order": list(PRIMES), "minors": minors,
        "original_coordinates": 1214, "surviving_coordinates": 1115,
        "original_equalities": 632, "distinct_nonempty_equations": 396,
        "initial_denominator": str(den), "initial_point_check": point_check,
        "limits": LIMITS,
        "arithmetic": {"transpose_selection_matrix_shape": [286, 397],
            "transpose_selection_transform_shape": [286, 286],
            "selection_matrix_and_transform_int64_bytes": 8*286*(397+286),
            "selection_update_absolute_bound": selection_update_bound,
            "selection_dense_dot_bound": selection_dot_bound,
            "maximum_basic_Cramer_output_bits": maximum_basic_bits,
            "conservative_all_compositions_output_bits": maximum_combination_bits,
            "internal_Flint_integer_bits_are_not_claimed_bounded": True},
        "scope": "Unrestricted signed-integer solution of all original native equalities on exactly the proved99-zero face. Free coordinates set to zero only in basic-point proposals; every full row must pass before use."}
    plain = canonical(specification)
    assert len(plain) <= LIMITS["maximum_artifact_bytes"]
    (directory/"minors.json.gz").write_bytes(gzip.compress(plain, mtime=0))
    record = {"status": "PASS: integer-affine construction prepared; no case4 rational solve",
        "bindings": bindings, "runtime": runtime(), "limits": LIMITS,
        "specification_gzip_sha256": sha((directory/"minors.json.gz").read_bytes()),
        "specification_raw_sha256": sha(plain), "specification_bytes": len(plain),
        "controls": control, "minor_dimensions": [m["dimension"] for m in minors],
        "minor_checks": [check_minor(data["equations"], m, deadline) for m in minors],
        "arithmetic": specification["arithmetic"], "case4_modular_minor_selection_calls": 3,
        "case4_rational_solve_calls": 0, "optimizer_calls": 0, "HNF_calls": 0, "SNF_calls": 0,
        "seconds": time.monotonic()-started}
    tick(deadline)
    save(directory/"preparation.json", record)
    return record


def prepared(directory, deadline=float("inf")):
    bindings, data, native, proofs, nums, den, point_check = load_inputs(deadline)
    prep = json.loads((directory/"preparation.json").read_bytes())
    assert prep["status"] == "PASS: integer-affine construction prepared; no case4 rational solve"
    assert prep["bindings"] == bindings and prep["limits"] == LIMITS and prep["runtime"] == runtime()
    raw = (directory/"minors.json.gz").read_bytes()
    assert sha(raw) == prep["specification_gzip_sha256"]
    plain = gzip.decompress(raw)
    assert sha(plain) == prep["specification_raw_sha256"]
    specification = json.loads(plain)
    assert specification["bindings"] == bindings and specification["limits"] == LIMITS
    assert specification["prime_order"] == list(PRIMES) and len(specification["minors"]) == 3
    assert specification["initial_denominator"] == str(den) and specification["initial_point_check"] == point_check
    for p, minor, check in zip(PRIMES, specification["minors"], prep["minor_checks"]):
        assert minor["prime"] == p and minor["dimension"] == 286
        assert minor["columns"] == proofs[p]["pivot_columns"]
        assert minor["original_column_ids"] == [data["original_column_ids"][j] for j in minor["columns"]]
        assert minor["representative_original_native_rows"] == [
            data["equations"][i]["representative_original_native_row"] for i in minor["equation_rows"]]
        assert check_minor(data["equations"], minor, deadline) == check
    return prep, specification, data, native, nums, den


def solve_child(preparation, directory):
    started = time.monotonic(); deadline = started+LIMITS["owned_exact_child_seconds"]
    record = {"status": "UNKNOWN: exact integer construction incomplete", "accepted_stages": [],
              "production_basic_solves": 0, "skipped_primes": [], "exact_integer_point_found": False,
              "optimizer_calls": 0, "HNF_calls": 0, "SNF_calls": 0}
    output = directory/"child-result.json"
    save(output, record)
    try:
        import resource
        resource.setrlimit(resource.RLIMIT_AS, (LIMITS["owned_child_address_space_bytes"],)*2)
        resource.setrlimit(resource.RLIMIT_FSIZE, (LIMITS["maximum_artifact_bytes"],)*2)
        prep, spec, data, native, nums, den = prepared(preparation, deadline)
        record["bindings"] = spec["bindings"]
        record["preparation_sha256"] = sha((preparation/"preparation.json").read_bytes())
        for minor in spec["minors"]:
            p = minor["prime"]
            if den % p:
                record["skipped_primes"].append(p)
                continue
            tick(deadline)
            record["production_basic_solves"] += 1
            assert record["production_basic_solves"] <= LIMITS["maximum_basic_solves"]
            record["pending_prime"] = p
            save(output, record)
            solve_started = time.monotonic()
            try:
                local, other_den = basic_solve(minor)
            except Exception as error:
                raise ArithmeticError("basic exact solve failed: "+type(error).__name__+": "+str(error)) from error
            elapsed = time.monotonic()-solve_started
            other = [0]*1214
            for a, value in zip(minor["original_column_ids"], local):
                other[a] = value
            point_path = directory/f"basic-prime-{p}.json"
            proposal = {"status": "RATIONAL_PROPOSAL: full equality acceptance pending", "prime": p,
                "numerators": list(map(str, other)), "common_denominator": str(other_den),
                "linear_solve_seconds": elapsed, "linear_solve_method": "fmpq_mat.solve algorithm=dixon"}
            save(point_path, proposal)
            checked = check_original(data, native, other, other_den, deadline)
            assert gcd(other_den, p) == 1
            proposal.update(status="EXACT_FULL_EQUALITY_POINT", exact_check=checked)
            save(point_path, proposal)
            # No composition is reached before the complete original-row check.
            combined, combined_den, identity = combine(nums, den, other, other_den)
            assert den % combined_den == 0 and combined_den % p != 0
            combined_check = check_original(data, native, combined, combined_den, deadline)
            combined_path = directory/f"combined-prime-{p}.json"
            combined_record = {"status": "EXACT_FULL_EQUALITY_POINT", "prime": p,
                "numerators": list(map(str, combined)), "common_denominator": str(combined_den),
                "Bezout_identity": identity, "exact_check": combined_check}
            save(combined_path, combined_record)
            record["accepted_stages"].append({"prime": p, "basic_point_file": point_path.name,
                "basic_point_sha256": sha(point_path.read_bytes()), "combined_point_file": combined_path.name,
                "combined_point_sha256": sha(combined_path.read_bytes()), "linear_solve_seconds": elapsed})
            nums, den = combined, combined_den
            record["remaining_denominator"] = str(den)
            record.pop("pending_prime", None)
            save(output, record)
        assert den == 1
        checked = check_original(data, native, nums, 1, deadline)
        final = {"status": "EXACT_SIGNED_INTEGER_AFFINE_POINT: cold replay pending",
            "source_sha256": sha(Path(__file__).read_bytes()), "original_coordinates": 1214,
            "integers": list(map(str, nums)), "common_denominator": "1", "exact_check": checked,
            "binary_graph_claimed": False, "nonnegative_point_claimed": False,
            "all_inequalities_or_covers_claimed": False}
        save(directory/"integer-point.json", final)
        record.update(status="EXACT_SIGNED_INTEGER_AFFINE_POINT: cold replay pending",
                      exact_integer_point_found=True,
                      integer_point_sha256=sha((directory/"integer-point.json").read_bytes()))
    except (ArithmeticError, AssertionError, MemoryError, TimeoutError, ValueError, ZeroDivisionError) as error:
        record.update(status="UNKNOWN: basic solve, full equality acceptance, or resource bound failed",
                      reason_type=type(error).__name__, reason=str(error))
    except Exception as error:
        record.update(status="ERROR: no unchecked affine conclusion", reason_type=type(error).__name__, reason=str(error))
        raise
    finally:
        record["seconds"] = time.monotonic()-started
        save(output, record)
    return record


def query(preparation, directory):
    assert not directory.exists()
    prep, spec, data, native, nums, den = prepared(preparation)
    directory.mkdir(parents=True)
    record = {"status": "RUNNING: one owned integer-affine exact child", "bindings": spec["bindings"],
        "preparation_sha256": sha((preparation/"preparation.json").read_bytes()), "limits": LIMITS,
        "exact_integer_point_found": False, "case4_excluded": False, "automatic_retries": 0,
        "optimizer_calls": 0, "HNF_calls": 0, "SNF_calls": 0}
    output = directory/"result.json"; save(output, record)
    started = time.monotonic()
    with (directory/"child.stdout.log").open("w") as stdout, (directory/"child.stderr.log").open("w") as stderr:
        try:
            done = subprocess.run([sys.executable, str(Path(__file__).resolve()), "_solve",
                "--preparation", str(preparation.resolve()), "--directory", str(directory.resolve())],
                stdout=stdout, stderr=stderr, timeout=LIMITS["owned_exact_child_seconds"], check=False)
            record["child_exit_code"] = done.returncode
            child_path = directory/"child-result.json"
            child = json.loads(child_path.read_bytes())
            record["child_result_sha256"] = sha(child_path.read_bytes())
            assert 0 <= child["production_basic_solves"] <= 3
            assert child["optimizer_calls"] == child["HNF_calls"] == child["SNF_calls"] == 0
            record["status"] = child["status"] if done.returncode == 0 else "UNKNOWN: owned exact child failed"
            record["exact_integer_point_found"] = done.returncode == 0 and child["exact_integer_point_found"]
        except subprocess.TimeoutExpired:
            record.update(status="UNKNOWN:60-second owned exact child hard timeout", hard_timeout=True)
        finally:
            record["owned_child_seconds"] = time.monotonic()-started
            save(output, record)
    return record


def replay(preparation, directory, output):
    assert not output.exists()
    started = time.monotonic(); deadline = started+LIMITS["cold_replay_seconds"]
    prep, spec, data, native, nums, den = prepared(preparation, deadline)
    terminal = json.loads((directory/"result.json").read_bytes())
    assert terminal["bindings"] == spec["bindings"] and terminal["limits"] == LIMITS
    assert terminal["preparation_sha256"] == sha((preparation/"preparation.json").read_bytes())
    assert terminal["optimizer_calls"] == terminal["HNF_calls"] == terminal["SNF_calls"] == 0
    assert not terminal["status"].startswith("RUNNING")
    report = {"status": "PASS: terminal bindings; no integer conclusion claimed",
        "source_sha256": sha(Path(__file__).read_bytes()), "terminal_sha256": sha((directory/"result.json").read_bytes()),
        "exact_integer_point_replayed": False, "basic_solves": 0, "optimizer_calls": 0,
        "HNF_calls": 0, "SNF_calls": 0, "stages_replayed": 0, "case4_excluded": False}
    child_path = directory/"child-result.json"
    if "child_result_sha256" in terminal:
        assert sha(child_path.read_bytes()) == terminal["child_result_sha256"]
        child = json.loads(child_path.read_bytes())
        assert 0 <= child["production_basic_solves"] <= 3
        remaining = iter(child["accepted_stages"])
        stage = next(remaining, None)
        for p in PRIMES:
            if den % p or stage is None:
                continue
            assert stage["prime"] == p
            bp, cp = directory/stage["basic_point_file"], directory/stage["combined_point_file"]
            assert sha(bp.read_bytes()) == stage["basic_point_sha256"]
            assert sha(cp.read_bytes()) == stage["combined_point_sha256"]
            basic, combined = json.loads(bp.read_bytes()), json.loads(cp.read_bytes())
            assert basic["status"] == combined["status"] == "EXACT_FULL_EQUALITY_POINT"
            other, other_den = list(map(integer, basic["numerators"])), integer(basic["common_denominator"])
            assert basic["exact_check"] == check_original(data, native, other, other_den, deadline)
            assert gcd(other_den, p) == 1
            values, new_den, identity = combine(nums, den, other, other_den)
            assert identity == combined["Bezout_identity"]
            assert combined["numerators"] == list(map(str, values)) and combined["common_denominator"] == str(new_den)
            assert combined["exact_check"] == check_original(data, native, values, new_den, deadline)
            assert den % new_den == 0 and new_den % p != 0
            nums, den = values, new_den
            report["stages_replayed"] += 1
            stage = next(remaining, None)
        assert stage is None and next(remaining, None) is None
        if terminal["exact_integer_point_found"]:
            assert child["exact_integer_point_found"] and den == 1
            final_path = directory/"integer-point.json"
            assert sha(final_path.read_bytes()) == child["integer_point_sha256"]
            final = json.loads(final_path.read_bytes())
            assert final["source_sha256"] == sha(Path(__file__).read_bytes())
            assert final["common_denominator"] == "1" and list(map(integer, final["integers"])) == nums
            checked = check_original(data, native, nums, 1, deadline)
            assert final["exact_check"] == checked
            report.update(status="PASS: original1214-coordinate signed integer point and every full-row composition",
                exact_integer_point_replayed=True, integer_point_sha256=sha(final_path.read_bytes()),
                exact_check=checked, binary_or_graph_feasibility_claimed=False)
    assert not terminal["exact_integer_point_found"] or report["exact_integer_point_replayed"]
    report["seconds"] = time.monotonic()-started
    save(output, report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "preflight", "query", "_solve", "replay"))
    parser.add_argument("--preparation", type=Path)
    parser.add_argument("--directory", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.mode == "prepare":
        assert args.directory is not None
        result = prepare(args.directory)
    elif args.mode == "preflight":
        assert args.preparation is not None and args.output is not None and not args.output.exists()
        started = time.monotonic()
        prep, spec, data, native, nums, den = prepared(args.preparation, started+60)
        result = {"status": "PASS: cold minor/inventory/preparation replay; no rational solve",
            "bindings": spec["bindings"], "preparation_sha256": sha((args.preparation/"preparation.json").read_bytes()),
            "modular_minors_replayed": len(spec["minors"]), "case4_rational_solves": 0,
            "optimizer_calls": 0, "seconds": time.monotonic()-started}
        save(args.output, result)
    elif args.mode == "query":
        assert args.preparation is not None and args.directory is not None
        result = query(args.preparation, args.directory)
    elif args.mode == "_solve":
        assert args.preparation is not None and args.directory is not None
        result = solve_child(args.preparation, args.directory)
    else:
        assert args.preparation is not None and args.directory is not None and args.output is not None
        result = replay(args.preparation, args.directory, args.output)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
