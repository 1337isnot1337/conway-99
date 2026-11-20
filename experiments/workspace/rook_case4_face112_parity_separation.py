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
RANK, DENOMINATOR, CANDIDATES = 286, 145446009, 41041
LIMITS = {"preparation_seconds": 60, "scan_seconds": 60, "replay_seconds": 60,
          "candidate_equations": CANDIDATES, "maximum_basis_rows_per_candidate": 2,
          "maximum_transcript_bytes": 64 << 20, "checkpoint_every_candidates": 256,
          "automatic_retries": 0, "optimizer_calls": 0}
sha, canonical = mod.sha, mod.canonical

NEW_INPUTS = {
    "H2_Gram": (BASE+"rook-case4-face99-parity-face-certificate.json", "717c3e4103dd56bdd260f52b0f50c5a06f4245b834d92194357481d3163e229e"),
    "zero663": (BASE+"rook-case4-face99-zero663-gram-capacity-certificate.json", "312d96f363eaad62c31ab685c50ec73f019a9d0742ddcbed9b1193a236113802"),
    "model112": (BASE+"rook-case4-face112-model01/model.json", "018882c8cea2a8cb9c2fc73a433d40973d20588bc5accb0fb8b0165fddc4337f"),
    "model112_cold": (BASE+"rook-case4-face112-model01-cold-replay.json", "26f063161cbf9c0beb139b392f0b46007254176c522308d3ed2d5e3ee3c2e703"),
    "point112": (BASE+"rook-case4-face112-basis-run01/candidate.json", "bb81664e8ea9faec6878ee98ec36c5ae844535e805f78fabe7c475a1f83d8ebb"),
    "point112_replay": (BASE+"rook-case4-face112-basis-run01-replay.json", "cda50fcd87c9e5009243b76442a953a0f1f6b6461baead3ecf296cce508a0c59"),
}


def new_json(key):
    path, expected = NEW_INPUTS[key]
    raw = (ROOT/path).read_bytes()
    assert sha(raw) == expected
    return json.loads(raw)


def zero_premises(native, old_zeros):
    """Expand the two short integer proofs on every original coordinate."""
    h2, c663, model, cold = (new_json(k) for k in ("H2_Gram", "zero663", "model112", "model112_cold"))
    assert len(old_zeros) == 99 and old_zeros == sorted(set(old_zeros))
    assert h2["prior_zero_columns"] == c663["prior99_zero_columns"] == old_zeros
    assert cold["model_sha256"] == NEW_INPUTS["model112"][1] and cold["status"].startswith("PASS")
    first, rhs = [0]*1214, 0
    used = set()
    for rec in h2["original_Gram_combination"]:
        i, multiplier = rec["original_native_row"], rec["multiplier"]
        assert i not in used and 0 <= i < 630; used.add(i)
        row = native[i]; assert row["lower"] == row["upper"]
        rhs += multiplier*row["lower"]
        for a, c in row["terms"]:
            first[a] += multiplier*c
    assert len(used) == 42 and rhs == h2["original_Gram_right_hand_side"] == 1
    assert first == h2["full_original_coefficients"]
    new12, support = set(h2["new_zero_columns"]), set(h2["H2_support"])
    assert len(new12) == 12 and not (new12 & set(old_zeros)) and not (new12 & support)
    for a in range(1214):
        if a not in old_zeros:
            assert first[a] == int(a in support) + 2*int(a in new12)
    # Nonnegative integer x gives every new12 coordinate zero, and H2=1.
    second, upper, used = [0]*1214, 0, set()
    for rec in c663["original_Gram_combination"]:
        i, multiplier = rec["original_Gram_row"], rec["multiplier"]
        assert i not in used and 0 <= i < 630; used.add(i)
        row = native[i]; assert row["lower"] == row["upper"]
        upper += multiplier*row["lower"]
        for a, c in row["terms"]:
            second[a] += multiplier*c
    capacity = native[681]
    assert capacity["terms"] == [[a, 1] for a in [258, 259, 260, 261, 262]]
    assert capacity["lower"] == 0 and capacity["upper"] == 1
    upper += capacity["upper"]
    for a, c in capacity["terms"]:
        second[a] += c
    assert len(used) == 143 and upper == c663["combined_upper_bound"] == 5
    assert second == c663["full_original_integer_coefficients"] and second[663] == 6
    assert 663 not in old_zeros and all(c >= 0 or a in old_zeros for a, c in enumerate(second))
    # Thus nonnegative integer x663 satisfies 6*x663<=5 and is zero.
    zeros = sorted(set(old_zeros) | new12 | {663})
    assert len(zeros) == 112 and zeros == model["fixed_zero_columns"]
    assert model["integer_cover_ranges"] == [[1, 1], [1, 1]]
    return zeros, model, {"old99_zero_premises": old_zeros,
        "twelve_zeros_from42_original_Gram_rows": sorted(new12),
        "zero663_from143_original_Gram_rows_plus_capacity681": True,
        "all1214_coefficients_reexpanded_for_each_new_proof": True,
        "new_zero_count": 13, "all_zero_count": 112,
        "no_new_modular_elimination_or_point_evaluation": True}



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
    inventory_bindings, old_data, native = mod.load_inventory()
    control = mod.inv.checked_json(ROOT, PARITY_CONTROLS, PARITY_CONTROLS_SHA)
    assert control["source_sha256"] == PARITY_SOURCE_SHA and control["formula_cases"] == 5938
    assert control["case4_point_or_domain_read"] is False and control["optimizer_calls"] == 0
    raw = (ROOT/PROOF_PATH).read_bytes(); assert sha(raw) == PROOF_SHA
    plain = gzip.decompress(raw); assert sha(plain) == PROOF_RAW_SHA
    proof = json.loads(plain); assert proof["prime"] == 2
    checked = mod.verify(old_data["equations"], 1115, proof, deadline)
    assert checked["rank"] == RANK and checked["fixed_coordinates"] == []
    cold = mod.inv.checked_json(ROOT, MODULAR_COLD, MODULAR_COLD_SHA)
    assert cold["status"].startswith("PASS") and cold["complete_all_planned_primes"]
    assert any(item["prime"] == 2 and item["rank"] == RANK for item in cold["completed"])
    zeros, model, zero_check = zero_premises(native, old_data["zero_columns"])
    kept = [a for a in range(1214) if a not in set(zeros)]
    assert len(kept) == 1102
    # New point bytes are bound only. Its coordinate values enter scan/replay.
    for key in ("point112", "point112_replay"):
        path, expected = NEW_INPUTS[key]
        assert sha((ROOT/path).read_bytes()) == expected
    bindings = {"source_sha256": sha(Path(__file__).read_bytes()),
        "modular_source_sha256": MODULAR_SOURCE_SHA, "parity_helper_sha256": PARITY_SOURCE_SHA,
        "parity_controls_sha256": PARITY_CONTROLS_SHA, "inventory": inventory_bindings,
        "mod2_certificate_gzip_sha256": PROOF_SHA, "mod2_certificate_raw_sha256": PROOF_RAW_SHA,
        "modular_cold_sha256": MODULAR_COLD_SHA,
        "new_inputs": {k: {"path": p, "sha256": h} for k, (p, h) in NEW_INPUTS.items()}}
    basis = []
    for i, (row, combination, pivot) in enumerate(zip(proof["reduced_rows"], proof["row_combinations"], proof["pivot_columns"])):
        tick(deadline)
        assert all(v in (0, 1) for v in row+combination)
        chosen = bitset(j for j, value in enumerate(combination) if value)
        old_lift = full_lift(chosen, old_data["equations"], native,
                             old_data["original_column_ids"], old_data["zero_columns"], 1214)
        assert old_lift["reduced_support_hex"] == hex(bitset(j for j, value in enumerate(row[:-1]) if value))
        assert old_lift["parity_rhs"] == row[-1]
        lifted = full_lift(chosen, old_data["equations"], native, kept, zeros, 1214)
        assert int(lifted["active_original_support_hex"], 16) == int(old_lift["active_original_support_hex"], 16) & bitset(kept)
        assert lifted["full_integer_coefficients_sha256"] == old_lift["full_integer_coefficients_sha256"]
        assert lifted["parity_rhs"] == row[-1]
        basis.append({"basis_index": i, "pivot_original_column": old_data["original_column_ids"][pivot],
                      "pre_projection_active_support_hex": old_lift["active_original_support_hex"], "lift": lifted})
    data = dict(old_data)
    data.update(original_column_ids=kept, zero_columns=zeros, zero_proof_check=zero_check,
                point_extra_unit_sums=model["integer_cover_live_original_supports"],
                point_extra_pair_bounds=model["added_pair_rows"])
    return bindings, data, native, basis


def candidates(basis):
    assert len(basis) == RANK
    identifier = 0
    selections = [(i,) for i in range(RANK)]
    selections.extend(combinations(range(RANK), 2))
    for indices in selections:
        active, combination, rhs = 0, 0, 0
        for i in indices:
            item = basis[i]
            active ^= int(item["lift"]["active_original_support_hex"], 16)
            combination ^= int(item["lift"]["equation_combination_hex"], 16)
            rhs ^= item["lift"]["parity_rhs"]
        assert active != 0
        yield {"id": identifier, "basis_indices": list(indices), "active_original_support_hex": hex(active),
               "parity_rhs": rhs, "equation_combination_hex": hex(combination)}
        identifier += 1
    assert identifier == CANDIDATES


def ledger(basis, deadline):
    digest, counts, seen = hashlib.sha256(), Counter(), set()
    number = 0
    for candidate in candidates(basis):
        tick(deadline)
        assert candidate["id"] == number
        equation = (candidate["active_original_support_hex"], candidate["parity_rhs"])
        assert equation not in seen; seen.add(equation)
        digest.update(canonical(candidate)+b"\n")
        counts[int(candidate["active_original_support_hex"], 16).bit_count()] += 1
        number += 1
    assert number == CANDIDATES and len(seen) == CANDIDATES
    assert min(counts) == 3 and max(counts) == 447 and sum(k*v for k, v in counts.items()) == 7236294
    return {"single_rows": RANK, "unordered_XOR_pairs": RANK*(RANK-1)//2,
        "all_candidates": number, "distinct_candidate_equations": len(seen),
        "duplicates": 0, "nonzero_supports": number,
        "distinctness_proof": "Complete exact set comparison of support/RHS after112-zero substitution; the old pivot-visibility proof is not assumed.",
        "ledger_sha256": digest.hexdigest(), "support_size_histogram": {str(k): v for k, v in sorted(counts.items())},
        "support_visits_in_one_complete_scan": sum(k*v for k, v in counts.items()),
        "maximum_support_size": max(counts), "minimum_support_size": min(counts),
        "conservative_integer_cost_bound": (max(counts)+1)*DENOMINATOR,
        "fixed_family_not_a_new_basis_for_all112_face_equalities": True}


def prepare(directory):
    assert not directory.exists()
    directory.mkdir(parents=True)
    started = time.monotonic(); deadline = started+LIMITS["preparation_seconds"]
    bindings, data, native, basis = load_domain(deadline)
    inventory = ledger(basis, deadline)
    assert inventory["support_visits_in_one_complete_scan"] == 7236294
    assert inventory["conservative_integer_cost_bound"] == 65159812032 < 2**36
    specification = {"schema": "rook-case4-face112-fixed-single-pair-parity-v1", "bindings": bindings,
        "basis": basis, "candidate_inventory": inventory, "limits": LIMITS,
        "original_coordinates": 1214, "surviving_coordinates": 1102, "known_zero_columns": data["zero_columns"],
        "original_equalities": 632, "distinct_nonempty_equations_before_projection": 396,
        "new_zero_proofs": data["zero_proof_check"],
        "point_denominator": DENOMINATOR, "point_values_used": False,
        "scope": "Only the286 saved F2 rows and their40755 unordered pairwise XORs, now projected through112 proved zeros. These are necessary Boolean forbidden-vertex inequalities; no new elimination, larger combination or completeness claim for all112-face parity consequences."}
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
    assert spec["new_zero_proofs"] == data["zero_proof_check"]
    inventory = ledger(basis, deadline)
    assert inventory == prep["candidate_inventory"] == spec["candidate_inventory"]
    return prep, spec, data, native, basis


def saved_point(data, native, deadline):
    point, replay = new_json("point112"), new_json("point112_replay")
    assert replay["status"].startswith("PASS") and replay["exact_point_replayed"]
    assert replay["candidate_sha256"] == NEW_INPUTS["point112"][1]
    assert replay["full_face_rows_checked"] == 167112 and replay["original_coordinate_covers_checked"] == 178533
    den = int(point["common_denominator"])
    reduced = list(map(int, point["extended_numerators"]))
    assert den == DENOMINATOR and len(reduced) == 1103 and reduced[-1] > 0
    full = [0]*1214
    for a, value in zip(data["original_column_ids"], reduced[:-1]):
        assert 0 < value < den and value >= reduced[-1]
        full[a] = value
    assert full == list(map(int, point["exact_check"]["original1214_selector_numerators"]))
    assert all(full[a] == 0 for a in data["zero_columns"])
    for i, row in enumerate(native):
        tick(deadline)
        value = sum(c*full[a] for a, c in row["terms"])
        assert row["lower"]*den <= value <= row["upper"]*den, ("original native point row", i)
    for support in data["point_extra_unit_sums"]:
        assert sum(full[a] for a in support) == den
    for a, b in data["point_extra_pair_bounds"]:
        assert full[a]+full[b] <= den
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
        "all112_zero_premises_from_checked_old_seed_and_two_short_integer_proofs": True,
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
