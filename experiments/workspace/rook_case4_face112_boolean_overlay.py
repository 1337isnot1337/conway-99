"""Preserve the full99-face CNF and append proved112-face constraints.

The unchanged439689-clause prefix keeps every native row and coordinate
cover. The suffix adds13 zero units, H1=H2=1, the certified pair AMO,
and the86-column sum=2 derived from the exact663 identity. A transparent
prefix counter for at-most-two uses170 fresh auxiliaries. No solver is
called during preparation or replay. The parent formula is hash-bound to
its published complete original-encoder cold replay, without a new census.
"""
import argparse
import hashlib
from itertools import combinations, product
import json
from pathlib import Path
import tempfile
import time

import rook_case4_face99_boolean_overlay as parent
import rook_case4_face111_native_bounds as exact
import rook_case4_face111_two_parity_equalities as equalities

ROOT = Path(__file__).resolve().parents[2]
BASE = "experiments/logs/grids-and-triangles/"
PARENT_SOURCE_SHA = "906a2cab0dcb6b23b6c35a9f0cd6a63a80b3dae27d8ca935892e37f2a0f89918"
EXACT_SOURCE_SHA = "df6a043f5a1f9f958536ff6c5b847b3b659c7701e609a30049b24582939ecc60"
EQUALITY_SOURCE_SHA = "195b5fc78cb6895ee7797ebf1926f1cd19d990d992d5a9e9638d44f24aa984c6"
INPUTS = {
    "parent_model": (BASE+"rook-case4-face99-boolean-preparation01/model.json", "7fddef049fd12b511556e473970999b255f41b3571d74c04fc734b29c9047c7f"),
    "parent_cold": (BASE+"rook-case4-face99-boolean-preparation01-cold.json", "58809ef709f19e2648e5ff531a8f36f5216f8f614ce572cfb767a2b3ab997d15"),
    "equalities": (BASE+"rook-case4-face111-two-parity-equalities-certificate.json", "6272996ff8c38af719b057dea6f6796efb895fdb678c69b82cc3eaff757ec606"),
    "native_model": (BASE+"rook-case4-face111-native-bounds-model01.json", "a174fde38a359f61498a0d9508beb2364ec9209f2771e9a7529a3675774008ad"),
    "bounds": (BASE+"rook-case4-face111-native-bounds-run01/certificates.jsonl", "92bd55e4987b18a17359a3d9344a58f599314cb524d5c44f881fecb5c4f4ce93"),
    "refined663": (BASE+"rook-case4-face111-native-bounds-663-denominator6.json", "4a808f495cc1e24a55e8979873fda659a6d82af48f521ffabb2c0873c067d30b"),
    "independent_bound_replay": (BASE+"rook-case4-face111-native-bounds-independent-replay.json", "5e1e01b8c5f3c5747292d65e6938263afe7a72bfff68b00ee29cf2f41b23b2a3"),
}
OLD_VARIABLES, VARIABLES = 134852, 135022
OLD_CLAUSES, NEW_CLAUSES = 439689, 441164
OLD_LITERALS, NEW_LITERALS = 13546449, 13556679
BASE_SHA, BASE_BYTES = "f3467d02ca6763391668c0cdac0a395dab23688d831b25107fcf04ea1c94ac22", 57874464
digest, save_new = parent.digest, parent.save_new


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def bindings():
    assert digest(parent.__file__) == PARENT_SOURCE_SHA
    assert digest(exact.__file__) == EXACT_SOURCE_SHA
    assert digest(equalities.__file__) == EQUALITY_SOURCE_SHA
    sources = parent.bindings()
    sources.update({Path(exact.__file__).name: EXACT_SOURCE_SHA,
                    Path(equalities.__file__).name: EQUALITY_SOURCE_SHA,
                    Path(__file__).name: digest(__file__)})
    return dict(sorted(sources.items()))


def premises(rederive=False):
    bindings(); data = {}
    for name, (path, expected) in INPUTS.items():
        raw = (ROOT/path).read_bytes(); assert sha(raw) == expected, name
        data[name] = [json.loads(line) for line in raw.splitlines()] if name == "bounds" else json.loads(raw)
    old, cold = data["parent_model"], data["parent_cold"]
    assert old["formula"]["CNF_sha256"] == cold["CNF_sha256"] == BASE_SHA
    assert cold["model_sha256"] == INPUTS["parent_model"][1] and cold["status"].startswith("PASS: full original CNF")
    assert (old["formula"]["variables"], old["formula"]["clauses"], old["formula"]["CNF_bytes"]) == (OLD_VARIABLES, OLD_CLAUSES, BASE_BYTES)
    if rederive:
        assert equalities.prove(ROOT) == data["equalities"]
        assert exact.build() == data["native_model"]
    model, equality = data["native_model"], data["equalities"]
    assert model["proved_zero_original_columns"] == equality["proved_zero_columns"]
    for proof in data["bounds"]+[data["refined663"]]:
        exact.verify(model, proof)
    refined = data["refined663"]
    multipliers = [0]*len(model["rows"])
    for row, encoded in refined["row_multipliers"]:
        multipliers[row] = int(encoded)
    upper, constant, residual = exact.bound(model["rows"], model["variables"],
        model["objectives"][16]["reduced_columns"], multipliers, 6)
    assert refined["objective_original_columns"] == [663] and refined["denominator"] == "6"
    assert upper == constant == 4 and set(residual) == {-2, 0}
    assert residual[model["kept_original_columns"].index(663)] == 0
    S = [a for a, value in zip(model["kept_original_columns"], residual) if value == -2]
    independent = data["independent_bound_replay"]
    assert independent["new_Boolean_zero"] == 663 and independent["short_identity"]["S"] == S
    assert independent["short_identity"]["identity_on_proved_face"] == "3*x_663 + sum_{a in S} x_a = 2"
    assert len(S) == 86 and 663 not in S
    zeros = sorted(equality["proved_zero_columns"]+[663])
    old_zeros = old["unit_provenance"]["all99_zero_columns"]
    assert len(zeros) == len(set(zeros)) == 112 and len(old_zeros) == 99 and set(old_zeros) <= set(zeros)
    new_zeros = sorted(set(zeros)-set(old_zeros)); assert len(new_zeros) == 13
    H = [sorted(set(support)-set(zeros)) for support in equality["live_cover_supports"]]
    assert list(map(len, H)) == [35, 41] and len(set(H[0])&set(H[1])) == 31
    pair = next(p for p in data["bounds"] if p["objective_original_columns"] == [259, 590])
    assert int(pair["upper_numerator"]) < 2*int(pair["denominator"])
    assert not (set(S)&set(zeros))
    return old, {"input_bindings": {k: {"path": p, "sha256": h} for k, (p, h) in INPUTS.items()},
                 "all112_zero_columns": zeros, "old99_zero_columns": old_zeros, "added13_zero_columns": new_zeros,
                 "unit_implications": [[-a-1] for a in new_zeros], "parity_supports": H, "parity_equal_values": [1, 1],
                 "pair_AMO": [259, 590], "sum2_support": S, "sum2_value": 2,
                 "sum2_identity": "3*x_663 + sum_{a in S} x_a = 2",
                 "three_old_Gram_pair_consequences_not_appended": [[259, 591], [259, 593], [259, 732]],
                 "no_candidate_or_symmetry_restriction": True}


def at_most_two(literals, top):
    """Prefix bits s[i,k] mean at least k true inputs through index i.

    Implications suffice: the first, second and third true inputs force a
    contradiction at the third. With at most two, actual prefix counts
    give a satisfying extension. No old variable is reused as auxiliary.
    """
    assert len(literals) >= 2 and len(set(literals)) == len(literals)
    assert all(type(v) is int and 0 < v <= top for v in literals)
    n = len(literals); s = [[top+2*i+1, top+2*i+2] for i in range(n-1)]
    clauses = [[-literals[i], s[i][0]] for i in range(n-1)]
    for i in range(1, n-1):
        clauses.extend([[-s[i-1][0], s[i][0]], [-s[i-1][1], s[i][1]],
                        [-literals[i], -s[i-1][0], s[i][1]]])
    clauses.extend([[-literals[i], -s[i-1][1]] for i in range(1, n)])
    clauses.append([-s[0][1]])
    assert len(clauses) == 5*n-7
    return clauses, top+2*(n-1), s


def suffix(proof):
    clauses = [[-a-1] for a in proof["added13_zero_columns"]]
    groups = [{"name": "new_zero_units", "start": 0, "count": len(clauses)}]
    start = len(clauses)
    H = proof["parity_supports"]
    clauses.extend([[a+1 for a in support] for support in H])
    pairs = sorted(set(pair for support in H for pair in combinations(support, 2)))
    clauses.extend([[-a-1, -b-1] for a, b in pairs])
    groups.append({"name": "two_parity_exactly_one", "start": start, "count": len(clauses)-start})
    start = len(clauses)
    clauses.append([-a-1 for a in proof["pair_AMO"]])
    groups.append({"name": "integer_pair_AMO", "start": start, "count": 1})
    start = len(clauses)
    literals = [a+1 for a in proof["sum2_support"]]
    more, top, counter = at_most_two(literals, OLD_VARIABLES)
    clauses.extend(more)
    # At least two holds exactly when deleting any one literal still
    # leaves a true literal. These86 clauses introduce no auxiliaries.
    clauses.extend([literals[:i]+literals[i+1:] for i in range(len(literals))])
    groups.append({"name": "derived_sum_exactly_two", "start": start, "count": len(clauses)-start})
    assert top == VARIABLES and len(clauses) == NEW_CLAUSES-OLD_CLAUSES == 1475
    assert sum(map(len, clauses)) == NEW_LITERALS-OLD_LITERALS == 10230
    assert len(pairs) == 950
    return clauses, {"groups": groups, "new_auxiliaries": VARIABLES-OLD_VARIABLES,
                     "counter_auxiliary_first": OLD_VARIABLES+1, "counter_auxiliary_last": top,
                     "counter_prefix_pairs": counter, "suffix_clause_count": len(clauses),
                     "suffix_literal_count": sum(map(len, clauses)), "distinct_parity_AMO_pairs": len(pairs)}


def unit_conflict(clauses, fixed):
    known = dict(fixed)
    while True:
        changed = False
        for clause in clauses:
            if any(abs(v) in known and known[abs(v)] == (v > 0) for v in clause):
                continue
            open_literals = [v for v in clause if abs(v) not in known]
            if not open_literals:
                return True
            if len(open_literals) == 1:
                v = open_literals[0]; known[abs(v)] = v > 0; changed = True
        if not changed:
            return False


def controls():
    checked = 0
    for n in range(2, 9):
        literals = list(range(1, n+1)); clauses, top, counter = at_most_two(literals, n)
        lower = [literals[:i]+literals[i+1:] for i in range(n)]
        for bits in product((False, True), repeat=n):
            assignment = dict(zip(literals, bits)); total = sum(bits)
            assert all(any(assignment[v] for v in row) for row in lower) == (total >= 2)
            if total <= 2:
                for i, pair in enumerate(counter):
                    assignment[pair[0]] = sum(bits[:i+1]) >= 1
                    assignment[pair[1]] = sum(bits[:i+1]) >= 2
                assert all(any(assignment[abs(v)] == (v > 0) for v in row) for row in clauses)
            else:
                assert unit_conflict(clauses, assignment)
            checked += 1
    return {"exact_primary_assignments_checked": checked, "at_most_two_soundness_by_unit_conflict": True,
            "at_most_two_completeness_by_actual_prefix_counts": True, "at_least_two_truth_tables": True,
            "solver_calls": 0}


def write_overlay(base_path, target, clauses):
    assert not target.exists()
    old_header = f"p cnf {OLD_VARIABLES} {OLD_CLAUSES}\n".encode()
    header = f"p cnf {VARIABLES} {NEW_CLAUSES}\n".encode()
    old_hash, body_hash, suffix_hash = hashlib.sha256(), hashlib.sha256(), hashlib.sha256()
    body_lines = body_bytes = 0
    with base_path.open("rb") as source, target.open("wb") as output:
        assert source.readline() == old_header
        old_hash.update(old_header); output.write(header)
        for chunk in iter(lambda: source.read(1 << 20), b""):
            old_hash.update(chunk); body_hash.update(chunk); output.write(chunk)
            body_lines += chunk.count(b"\n"); body_bytes += len(chunk)
        assert body_lines == OLD_CLAUSES and old_hash.hexdigest() == BASE_SHA
        assert len(old_header)+body_bytes == BASE_BYTES
        for clause in clauses:
            assert clause and all(type(v) is int and 0 < abs(v) <= VARIABLES for v in clause)
            line = (" ".join(map(str, clause))+" 0\n").encode()
            output.write(line); suffix_hash.update(line)
    return {"base_sha256": BASE_SHA, "base_clause_body_sha256": body_hash.hexdigest(),
            "base_clause_body_bytes": body_bytes, "base_clause_lines": body_lines,
            "constraint_suffix_sha256": suffix_hash.hexdigest(), "constraint_suffix_lines": len(clauses),
            "variables": VARIABLES, "clauses": NEW_CLAUSES, "CNF_sha256": digest(target),
            "CNF_bytes": target.stat().st_size}


def rebuild(cnf, progress=None):
    sources = bindings(); old, proof = premises(rederive=True)
    clauses, encoding = suffix(proof)
    base_path = Path(old["cnf_path"])
    formula = write_overlay(base_path, cnf, clauses)
    return {"source_hashes": sources, "old_model_sha256": INPUTS["parent_model"][1],
            "old_cold_sha256": INPUTS["parent_cold"][1], "case": old["case"],
            "unit_provenance": proof, "formula": formula, "suffix_encoding": encoding,
            "original_primary_columns": 1214, "remaining_primary_columns": 1102,
            "all_previous_primary_constraints_retained": True, "complete_coordinate_covers": 178533,
            "new_auxiliary_variables": 170, "all_auxiliaries_after_old134852_variables": True,
            "byte_audit": {"all439689_old_clause_bytes_preserved": True,
                           "old_complete_encoding_cold_certificate": INPUTS["parent_cold"][1],
                           "total_literal_occurrences": NEW_LITERALS},
            "full_exterior_adjacency_variables": 0, "case_index": 4,
            "candidate_basis_or_symmetry_restriction": False}


def prepare(directory, cnf):
    assert not directory.exists() and not cnf.exists()
    directory.mkdir(parents=True); cnf.parent.mkdir(parents=True, exist_ok=True)
    started = time.monotonic(); model = rebuild(cnf)
    model.update(status="PASS: complete case4 CNF plus proved112-face constraints prepared; no query",
                 complete=True, controls=controls(), cnf_path=str(cnf.resolve()),
                 production_solver_calls=0, optimizer_calls=0, elapsed_seconds=time.monotonic()-started)
    save_new(directory/"model.json", model); return model


def checked_model(directory, require_cnf=False):
    model = json.loads((directory/"model.json").read_bytes())
    assert model["complete"] and model["source_hashes"] == bindings()
    old, proof = premises()
    assert model["unit_provenance"] == proof and model["suffix_encoding"] == suffix(proof)[1]
    assert model["formula"]["base_sha256"] == BASE_SHA
    assert model["formula"]["variables"] == VARIABLES and model["formula"]["clauses"] == NEW_CLAUSES
    assert model["production_solver_calls"] == model["optimizer_calls"] == 0
    if require_cnf:
        path = Path(model["cnf_path"])
        assert digest(path) == model["formula"]["CNF_sha256"] and path.stat().st_size == model["formula"]["CNF_bytes"]
    return model


def cold(directory, output):
    assert not output.exists(); started = time.monotonic(); model = checked_model(directory)
    with tempfile.TemporaryDirectory(prefix="rook112-overlay-cold-") as temporary:
        rebuilt = rebuild(Path(temporary)/"full.cnf")
        assert all(model[k] == v for k, v in rebuilt.items())
    report = {"status": "PASS: full original CNF prefix and all112-face suffix premises cold-replayed",
              "source_hashes": bindings(), "model_sha256": digest(directory/"model.json"),
              "CNF_sha256": model["formula"]["CNF_sha256"], "variables": VARIABLES, "clauses": NEW_CLAUSES,
              "complete_parent_encoder_repeated": False, "published_parent_cold_hash_bound": True,
              "optimizer_or_solver_called": False, "elapsed_seconds": time.monotonic()-started}
    save_new(output, report); return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "replay"))
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--cnf", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    answer = prepare(args.directory, args.cnf) if args.mode == "prepare" else cold(args.directory, args.output)
    print(json.dumps({k: answer[k] for k in ("status", "elapsed_seconds", "formula", "controls") if k in answer}, indent=2), flush=True)


if __name__ == "__main__":
    main()
