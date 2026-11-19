"""Exact separation by single and pairwise-XOR rows of the saved F2 basis.

Preparation is point-independent apart from immutable input-file bindings.
Only scan mode evaluates the saved rational point. Every emitted Boolean
inequality carries its complete original-row parity derivation and zero
premises. No optimizer, larger row combination, or graph symmetry is used.
"""
import argparse
from collections import Counter
import gzip
import hashlib
from itertools import combinations
import json
from pathlib import Path
import time

import rook_case4_face99_affine_modular as mod
import rook_case4_parity_polytope as parity

ROOT, BASE = mod.ROOT, mod.BASE
MODULAR_SOURCE_SHA = "c09b76ed3570ca0fec17c2446a8222cb9c556ad5664f665adf38a5f473b188db"
PARITY_SOURCE_SHA = "048df509b05601f15d6cb4230750b36d221276cce66e625b0cf9c720ecb89062"
PARITY_CONTROLS = BASE+"rook-case4-parity-polytope-controls01.json"
PARITY_CONTROLS_SHA = "2358071f1ec985c06d938e8986679edf625f7336f47eb4b533740de98f7dfcbd"
PROOF_PATH = BASE+"rook-case4-face99-affine-modular-run01/prime-2.json.gz"
PROOF_SHA = "2b2ea2cca576ac60424557442325ad8ed57a1e43f1027c77e5055189183c5600"
PROOF_RAW_SHA = "ebbb485a638515758a2576db9f8216e90d792f62b6b96d00c96c651157967ab3"
MODULAR_COLD = BASE+"rook-case4-face99-affine-modular-run01-replay.json"
MODULAR_COLD_SHA = "0bf5fb3687db3fd81a5cf270cc6b30666f1c22c7318878f201d7720f8abf29b0"
RANK, DENOMINATOR, CANDIDATES = 286, 1661041997, 41041
LIMITS = {"preparation_seconds": 60, "scan_seconds": 60, "replay_seconds": 60,
          "candidate_equations": CANDIDATES, "maximum_basis_rows_per_candidate": 2,
          "maximum_transcript_bytes": 64 << 20, "checkpoint_every_candidates": 256,
          "automatic_retries": 0, "optimizer_calls": 0}
sha, canonical = mod.sha, mod.canonical


def tick(deadline):
    if time.monotonic() >= deadline:
        raise TimeoutError("bounded exact parity preparation, scan, or replay")


def bitset(indices):
    value = 0
    for i in indices:
        assert type(i) is int and i >= 0
        value |= 1 << i
    return value


def sites(bits):
    assert type(bits) is int and bits >= 0
    while bits:
        low = bits & -bits
        yield low.bit_length()-1
        bits ^= low


def save(path, value):
    raw = (json.dumps(value, indent=2)+"\n").encode()
    assert len(raw) <= LIMITS["maximum_transcript_bytes"]
    temporary = path.with_name(path.name+".partial")
    temporary.write_bytes(raw)
    temporary.replace(path)


def full_lift(combination, equations, native, kept, zeros, dimension):
    assert combination >= 0 and combination.bit_length() <= len(equations)
    coefficients, rhs, original_ids = [0]*dimension, 0, []
    for i in sites(combination):
        original_id = equations[i]["representative_original_native_row"]
        row = native[original_id]
        assert row["lower"] == row["upper"]
        original_ids.append(original_id)
        rhs += row["lower"]
        for a, value in row["terms"]:
            coefficients[a] += value
    assert len(set(original_ids)) == len(original_ids)
    odd = bitset(a for a, value in enumerate(coefficients) if value % 2)
    active = bitset(kept)
    zero_set = set(zeros)
    removed = [a for a in sites(odd & ~active)]
    assert set(removed) <= zero_set
    reduced = bitset(j for j, a in enumerate(kept) if coefficients[a] % 2)
    return {"equation_combination_hex": hex(combination),
        "original_native_row_combination_hex": hex(bitset(original_ids)),
        "original_native_row_count": len(original_ids),
        "full_original_dimension": dimension,
        "full_integer_coefficients_sha256": sha(canonical(coefficients)),
        "full_integer_right_hand_side": rhs,
        "full_original_parity_hex": hex(odd),
        "removed_proved_zero_odd_columns": removed,
        "active_original_support_hex": hex(odd & active),
        "reduced_support_hex": hex(reduced), "parity_rhs": rhs % 2}


def controls():
    native = [
        {"terms": [[0, 1], [1, 1], [3, 1]], "lower": 1, "upper": 1},
        {"terms": [[1, 1], [2, 1], [3, 1]], "lower": 0, "upper": 0},
        {"terms": [[0, -1], [2, 2], [3, -3]], "lower": -1, "upper": -1},
    ]
    equations = [{"representative_original_native_row": i} for i in range(3)]
    lifts = [full_lift(mask, equations, native, [0, 1, 2], [3], 4) for mask in range(8)]
    comparisons = 0
    for a in range(8):
        for b in range(8):
            c = lifts[a ^ b]
            for name in ("full_original_parity_hex", "active_original_support_hex", "reduced_support_hex"):
                assert int(c[name], 16) == int(lifts[a][name], 16) ^ int(lifts[b][name], 16)
            assert c["parity_rhs"] == lifts[a]["parity_rhs"] ^ lifts[b]["parity_rhs"]
            comparisons += 1
    assert lifts[3]["active_original_support_hex"] == hex((1 << 0) | (1 << 2))
    assert lifts[3]["parity_rhs"] == 1
    assert lifts[1]["removed_proved_zero_odd_columns"] == [3]
    return {"exact_XOR_original_row_lift_controls": comparisons,
            "signed_original_coefficients_and_rhs_checked": True,
            "only_declared_zero_premise_removed": True,
            "case4_point_read": False, "optimizer_calls": 0}


def load_domain(deadline):
    assert sha(Path(mod.__file__).read_bytes()) == MODULAR_SOURCE_SHA
    assert sha(Path(parity.__file__).read_bytes()) == PARITY_SOURCE_SHA
    inventory_bindings, data, native = mod.load_inventory()
    control = mod.inv.checked_json(ROOT, PARITY_CONTROLS, PARITY_CONTROLS_SHA)
    assert control["source_sha256"] == PARITY_SOURCE_SHA and control["formula_cases"] == 5938
    assert control["case4_point_or_domain_read"] is False and control["optimizer_calls"] == 0
    raw = (ROOT/PROOF_PATH).read_bytes()
    assert sha(raw) == PROOF_SHA
    plain = gzip.decompress(raw)
    assert sha(plain) == PROOF_RAW_SHA
    proof = json.loads(plain)
    assert proof["prime"] == 2
    checked = mod.verify(data["equations"], 1115, proof, deadline)
    assert checked["rank"] == RANK and checked["fixed_coordinates"] == []
    cold = mod.inv.checked_json(ROOT, MODULAR_COLD, MODULAR_COLD_SHA)
    assert cold["status"].startswith("PASS") and cold["complete_all_planned_primes"]
    assert any(item["prime"] == 2 and item["rank"] == RANK for item in cold["completed"])
    # Point bytes are bound here, but their values are not parsed or used.
    for key in ("point", "point_replay"):
        path, expected = mod.inv.INPUTS[key]
        assert sha((ROOT/path).read_bytes()) == expected
    bindings = {"source_sha256": sha(Path(__file__).read_bytes()),
        "modular_source_sha256": MODULAR_SOURCE_SHA, "parity_helper_sha256": PARITY_SOURCE_SHA,
        "parity_controls_sha256": PARITY_CONTROLS_SHA, "inventory": inventory_bindings,
        "mod2_certificate_gzip_sha256": PROOF_SHA, "mod2_certificate_raw_sha256": PROOF_RAW_SHA,
        "modular_cold_sha256": MODULAR_COLD_SHA,
        "point": {"path": mod.inv.INPUTS["point"][0], "sha256": mod.inv.INPUTS["point"][1]},
        "point_full_replay": {"path": mod.inv.INPUTS["point_replay"][0], "sha256": mod.inv.INPUTS["point_replay"][1]}}
    kept, zeros = data["original_column_ids"], data["zero_columns"]
    basis = []
    for i, (row, combination, pivot) in enumerate(zip(proof["reduced_rows"], proof["row_combinations"], proof["pivot_columns"])):
        tick(deadline)
        assert all(v in (0, 1) for v in row+combination)
        chosen = bitset(j for j, value in enumerate(combination) if value)
        lifted = full_lift(chosen, data["equations"], native, kept, zeros, 1214)
        assert lifted["reduced_support_hex"] == hex(bitset(j for j, value in enumerate(row[:-1]) if value))
        assert lifted["parity_rhs"] == row[-1]
        basis.append({"basis_index": i, "pivot_original_column": kept[pivot], "lift": lifted})
    return bindings, data, native, basis


def candidates(basis):
    assert len(basis) == RANK
    identifier = 0
    selections = [(i,) for i in range(RANK)]
    selections.extend(combinations(range(RANK), 2))
    pivot_mask = bitset(item["pivot_original_column"] for item in basis)
    for indices in selections:
        active, combination, rhs, expected_pivots = 0, 0, 0, 0
        for i in indices:
            item = basis[i]
            active ^= int(item["lift"]["active_original_support_hex"], 16)
            combination ^= int(item["lift"]["equation_combination_hex"], 16)
            rhs ^= item["lift"]["parity_rhs"]
            expected_pivots ^= 1 << item["pivot_original_column"]
        assert active & pivot_mask == expected_pivots
        assert expected_pivots.bit_count() == len(indices) and active != 0
        yield {"id": identifier, "basis_indices": list(indices), "active_original_support_hex": hex(active),
               "parity_rhs": rhs, "equation_combination_hex": hex(combination)}
        identifier += 1
    assert identifier == CANDIDATES


def ledger(basis, deadline):
    digest, counts = hashlib.sha256(), Counter()
    number = 0
    for candidate in candidates(basis):
        tick(deadline)
        assert candidate["id"] == number
        digest.update(canonical(candidate)+b"\n")
        counts[int(candidate["active_original_support_hex"], 16).bit_count()] += 1
        number += 1
    assert number == CANDIDATES
    return {"single_rows": RANK, "unordered_XOR_pairs": RANK*(RANK-1)//2,
        "all_candidates": number, "distinct_candidate_equations": number,
        "duplicates": 0, "nonzero_supports": number,
        "distinctness_proof": "Distinct one/two-element subsets of the286 pivot coordinates remain visible in every corresponding support.",
        "ledger_sha256": digest.hexdigest(), "support_size_histogram": {str(k): v for k, v in sorted(counts.items())},
        "support_visits_in_one_complete_scan": sum(k*v for k, v in counts.items()),
        "maximum_support_size": max(counts),
        "conservative_integer_cost_bound": (max(counts)+1)*DENOMINATOR}


def prepare(directory):
    assert not directory.exists()
    directory.mkdir(parents=True)
    started = time.monotonic(); deadline = started+LIMITS["preparation_seconds"]
    bindings, data, native, basis = load_domain(deadline)
    inventory = ledger(basis, deadline)
    assert inventory["support_visits_in_one_complete_scan"] <= 45760715
    assert inventory["conservative_integer_cost_bound"] <= 1853722868652 < 2**41
    specification = {"schema": "rook-case4-face99-single-pair-parity-v1", "bindings": bindings,
        "basis": basis, "candidate_inventory": inventory, "limits": LIMITS,
        "original_coordinates": 1214, "surviving_coordinates": 1115, "known_zero_columns": data["zero_columns"],
        "original_equalities": 632, "distinct_nonempty_equations": 396,
        "point_denominator": DENOMINATOR, "point_values_used": False,
        "scope": "Only the286 saved F2 basis rows and their40755 unordered pairwise XORs; necessary Boolean forbidden-vertex inequalities; no larger combinations."}
    plain = canonical(specification)
    assert len(plain) <= LIMITS["maximum_transcript_bytes"]
    (directory/"basis.json.gz").write_bytes(gzip.compress(plain, mtime=0))
    report = {"status": "PASS: complete parity proposal domain prepared; point not evaluated",
        "bindings": bindings, "specification_gzip_sha256": sha((directory/"basis.json.gz").read_bytes()),
        "specification_raw_sha256": sha(plain), "candidate_inventory": inventory,
        "lift_controls": controls(), "limits": LIMITS, "all286_original1214_coordinate_lifts_checked": True,
        "point_values_used": False, "point_file_bytes_bound_only": True,
        "optimizer_calls": 0, "larger_basis_combinations": 0,
        "seconds": time.monotonic()-started}
    save(directory/"preparation.json", report)
    return report


def prepared(directory, deadline):
    bindings, data, native, basis = load_domain(deadline)
    prep = json.loads((directory/"preparation.json").read_bytes())
    assert prep["status"] == "PASS: complete parity proposal domain prepared; point not evaluated"
    assert prep["bindings"] == bindings and prep["limits"] == LIMITS
    raw = (directory/"basis.json.gz").read_bytes()
    assert sha(raw) == prep["specification_gzip_sha256"]
    plain = gzip.decompress(raw)
    assert sha(plain) == prep["specification_raw_sha256"]
    spec = json.loads(plain)
    assert spec["bindings"] == bindings and spec["basis"] == basis and spec["limits"] == LIMITS
    assert spec["known_zero_columns"] == data["zero_columns"]
    inventory = ledger(basis, deadline)
    assert inventory == prep["candidate_inventory"] == spec["candidate_inventory"]
    return prep, spec, data, native, basis


def saved_point(data, native, deadline):
    point = mod.inv.checked_json(ROOT, *mod.inv.INPUTS["point"])
    replay = mod.inv.checked_json(ROOT, *mod.inv.INPUTS["point_replay"])
    assert replay["status"].startswith("PASS") and replay["exact_point_replayed"]
    assert replay["candidate_sha256"] == mod.inv.INPUTS["point"][1]
    den = int(point["common_denominator"])
    reduced = list(map(int, point["extended_numerators"]))
    assert den == DENOMINATOR and len(reduced) == 1116
    full = [0]*1214
    for a, value in zip(data["original_column_ids"], reduced[:-1]):
        assert 0 < value < den
        full[a] = value
    assert all(full[a] == 0 for a in data["zero_columns"])
    for i, row in enumerate(native):
        tick(deadline)
        value = sum(c*full[a] for a, c in row["terms"])
        assert row["lower"]*den <= value <= row["upper"]*den, ("original native point row", i)
    return full, den


def evaluate(candidate, full, den):
    support = list(sites(int(candidate["active_original_support_hex"], 16)))
    certificate = parity.closest_forbidden(support, candidate["parity_rhs"], full, den)
    assert certificate is not None
    return certificate, [candidate["id"], certificate["distance_numerator"],
        certificate["nearest_rounding_parity"],
        -1 if certificate["flipped_coordinate"] is None else certificate["flipped_coordinate"]]


def cut_record(candidate, certificate, data, native, full, den):
    assert certificate["strictly_violated"]
    check = parity.check_exact(certificate, full, den)
    assert check["exact_violation_numerator"] > 0
    lifted = full_lift(int(candidate["equation_combination_hex"], 16), data["equations"],
                       native, data["original_column_ids"], data["zero_columns"], 1214)
    assert lifted["active_original_support_hex"] == candidate["active_original_support_hex"]
    assert lifted["parity_rhs"] == candidate["parity_rhs"]
    return {"candidate_id": candidate["id"], "basis_indices": candidate["basis_indices"],
        "row": {"support_original_hex": candidate["active_original_support_hex"],
                "positive_original_hex": hex(bitset(certificate["forbidden_ones"])),
                "upper": check["inequality"]["upper"],
                "terms_sha256": sha(canonical(check["inequality"]["terms"]))},
        "distance_numerator": certificate["distance_numerator"], "denominator": den,
        "exact_violation_numerator": check["exact_violation_numerator"], "lift": lifted}


def scan(preparation, directory):
    assert not directory.exists()
    directory.mkdir(parents=True)
    started = time.monotonic(); deadline = started+LIMITS["scan_seconds"]
    terminal = {"status": "RUNNING: exact Boolean parity separation", "complete": False,
        "evaluated_candidates": 0, "violated_inequalities": 0, "case4_excluded": False,
        "limits": LIMITS, "optimizer_calls": 0, "automatic_retries": 0}
    output = directory/"result.json"; save(output, terminal)
    evaluation_path, cuts_path = directory/"evaluations.jsonl", directory/"cuts.jsonl"
    transcript_bytes = 0
    try:
        prep, spec, data, native, basis = prepared(preparation, deadline)
        full, den = saved_point(data, native, deadline)
        terminal.update(bindings=spec["bindings"], preparation_sha256=sha((preparation/"preparation.json").read_bytes()),
                        candidate_ledger_sha256=spec["candidate_inventory"]["ledger_sha256"],
                        original2271_native_point_rows_rechecked=True)
        with evaluation_path.open("wb") as evaluations, cuts_path.open("wb") as cuts:
            for candidate in candidates(basis):
                tick(deadline)
                certificate, compact = evaluate(candidate, full, den)
                evaluation_bytes = canonical(compact)+b"\n"
                cut_bytes = b""
                if certificate["strictly_violated"]:
                    cut_bytes = canonical(cut_record(candidate, certificate, data, native, full, den))+b"\n"
                if transcript_bytes+len(evaluation_bytes)+len(cut_bytes) > LIMITS["maximum_transcript_bytes"]:
                    raise MemoryError("combined transcript byte limit; candidate not inserted")
                evaluations.write(evaluation_bytes)
                if cut_bytes:
                    cuts.write(cut_bytes)
                    terminal["violated_inequalities"] += 1
                transcript_bytes += len(evaluation_bytes)+len(cut_bytes)
                terminal["evaluated_candidates"] += 1
                if terminal["evaluated_candidates"] % LIMITS["checkpoint_every_candidates"] == 0:
                    evaluations.flush(); cuts.flush()
                    save(output, terminal)
            assert terminal["evaluated_candidates"] == CANDIDATES
            terminal.update(status="COMPLETE_EXACT_PARITY_SCAN: cold replay pending", complete=True)
    except (TimeoutError, MemoryError) as error:
        terminal.update(status="PARTIAL_EXACT_PARITY_SCAN: checked prefix only", reason=str(error))
    except Exception as error:
        terminal.update(status="ERROR: no full-family conclusion", reason_type=type(error).__name__, reason=str(error))
        raise
    finally:
        terminal["transcript_bytes"] = transcript_bytes
        for name, path in (("evaluations", evaluation_path), ("cuts", cuts_path)):
            if path.exists():
                terminal[name+"_sha256"] = sha(path.read_bytes())
        terminal["seconds"] = time.monotonic()-started
        save(output, terminal)
    return terminal


def replay(preparation, directory, output):
    assert not output.exists()
    started = time.monotonic(); deadline = started+LIMITS["replay_seconds"]
    prep, spec, data, native, basis = prepared(preparation, deadline)
    full, den = saved_point(data, native, deadline)
    terminal = json.loads((directory/"result.json").read_bytes())
    assert terminal["bindings"] == spec["bindings"] and terminal["limits"] == LIMITS
    assert terminal["preparation_sha256"] == sha((preparation/"preparation.json").read_bytes())
    assert terminal["candidate_ledger_sha256"] == spec["candidate_inventory"]["ledger_sha256"]
    assert terminal["status"].startswith(("COMPLETE_", "PARTIAL_"))
    assert terminal["complete"] == (terminal["evaluated_candidates"] == CANDIDATES)
    for name in ("evaluations", "cuts"):
        assert sha((directory/(name+".jsonl")).read_bytes()) == terminal[name+"_sha256"]
    checked, violations, minimum_cost = 0, 0, None
    with (directory/"evaluations.jsonl").open("rb") as evaluations, (directory/"cuts.jsonl").open("rb") as cuts:
        for candidate in candidates(basis):
            if checked == terminal["evaluated_candidates"]:
                break
            tick(deadline)
            certificate, compact = evaluate(candidate, full, den)
            assert json.loads(evaluations.readline()) == compact
            if minimum_cost is None or certificate["distance_numerator"] < minimum_cost:
                minimum_cost = certificate["distance_numerator"]
            if certificate["strictly_violated"]:
                assert json.loads(cuts.readline()) == cut_record(candidate, certificate, data, native, full, den)
                violations += 1
            checked += 1
        assert evaluations.read() == b"" and cuts.read() == b""
    assert checked == terminal["evaluated_candidates"] and violations == terminal["violated_inequalities"]
    report = {"status": "PASS: exact parity-distance and full original-row proof replay",
        "source_sha256": sha(Path(__file__).read_bytes()), "terminal_sha256": sha((directory/"result.json").read_bytes()),
        "complete": terminal["complete"], "evaluated_candidates": checked, "violated_inequalities": violations,
        "minimum_distance_numerator": minimum_cost, "denominator": den,
        "all_emitted_1214_coordinate_lifts_rebuilt": True,
        "all99_zero_premises_from_frozen_seed_only": True,
        "optimizer_calls": 0, "case4_excluded": False, "seconds": time.monotonic()-started}
    save(output, report)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "preflight", "scan", "replay"))
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
        prep, spec, data, native, basis = prepared(args.preparation, started+60)
        result = {"status": "PASS: complete parity domain cold replay; point not evaluated",
            "bindings": spec["bindings"], "preparation_sha256": sha((args.preparation/"preparation.json").read_bytes()),
            "candidate_inventory": spec["candidate_inventory"], "point_values_used": False,
            "optimizer_calls": 0, "seconds": time.monotonic()-started}
        save(args.output, result)
    elif args.mode == "scan":
        assert args.preparation is not None and args.directory is not None
        result = scan(args.preparation, args.directory)
    else:
        assert args.preparation is not None and args.directory is not None and args.output is not None
        result = replay(args.preparation, args.directory, args.output)
    print(json.dumps(result, indent=2))
