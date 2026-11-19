"""Independent source, arithmetic and byte audit of the frozen 112-face overlay.

No subject module, solver, domain census, or full CNF builder is executed.
The retained native rows and earlier zero/parity proofs remain hash-bound
premises. The new bounds, suffix and existing prefix bytes are checked here.
"""
import argparse
from collections import Counter
import hashlib
from itertools import combinations
import json
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[2]
BASE = "experiments/logs/grids-and-triangles/"
SUBJECT = "experiments/workspace/rook_case4_face112_boolean_overlay.py"
SUBJECT_SHA = "6e96e8712b1af1bf355de8b69ac2dac358b73e27f8e68c9d500037ab7117d150"
MODEL = BASE + "rook-case4-face112-boolean-preparation01/model.json"
MODEL_SHA = "d4b3b0a8df5663a703932bfb4c5afcc27093fffe3304f5bdda50c9180a93cdb2"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def packed(x):
    return json.dumps(x, sort_keys=True, separators=(",", ":")).encode()


def check_bound(model, proof):
    denominator = int(proof["denominator"])
    assert denominator > 0
    objective = model["objectives"][proof["objective_id"]]
    assert objective["original_columns"] == proof["objective_original_columns"]
    assert objective["required_value"] == proof["required_value"]
    weighted = [0] * model["variables"]
    upper_rows = 0
    ids = []
    all_equalities = True
    for row_id, encoded in proof["row_multipliers"]:
        assert row_id not in ids and 0 <= row_id < len(model["rows"])
        ids.append(row_id)
        multiplier = int(encoded)
        assert multiplier
        row = model["rows"][row_id]
        all_equalities &= row["lower"] == row["upper"]
        upper_rows += multiplier * (row["upper"] if multiplier > 0 else row["lower"])
        for j, coefficient in row["terms"]:
            weighted[j] += multiplier * coefficient
    assert ids == sorted(ids)
    objective_set = set(objective["reduced_columns"])
    residual = [denominator * int(j in objective_set) - a
                for j, a in enumerate(weighted)]
    upper = upper_rows + sum(max(a, 0) for a in residual)
    assert upper == int(proof["upper_numerator"])
    assert upper_rows == int(proof["row_bound_constant_numerator"])
    assert [[j, str(a)] for j, a in enumerate(residual) if a > 0] == proof["positive_unit_box_correction"]
    assert sha(packed(residual)) == proof["full_residual_sha256"]
    assert upper < denominator * objective["required_value"]
    return {
        "objective": objective["original_columns"],
        "denominator": denominator, "upper_numerator": upper,
        "row_constant": upper_rows, "nonzero_multipliers": len(ids),
        "all_used_rows_are_equalities": bool(all_equalities),
        "residual_histogram": dict(sorted(Counter(residual).items())),
    }, weighted, residual


def expected_suffix(proof):
    clauses = [[-(a + 1)] for a in proof["added13_zero_columns"]]
    supports = proof["parity_supports"]
    clauses += [[a + 1 for a in H] for H in supports]
    pairs = set()
    for H in supports:
        pairs.update(combinations(H, 2))
    clauses += [[-(a + 1), -(b + 1)] for a, b in sorted(pairs)]
    clauses += [[-(a + 1) for a in proof["pair_AMO"]]]
    x = [a + 1 for a in proof["sum2_support"]]
    n = len(x)
    state = [(134853 + 2*i, 134854 + 2*i) for i in range(n-1)]
    counter = [[-x[i], state[i][0]] for i in range(n-1)]
    for i in range(1, n-1):
        old1, old2 = state[i-1]
        one, two = state[i]
        counter += [[-old1, one], [-old2, two], [-x[i], -old1, two]]
    counter += [[-x[i], -state[i-1][1]] for i in range(1, n)]
    counter += [[-state[0][1]]]
    clauses += counter
    clauses += [[v for j, v in enumerate(x) if j != i] for i in range(n)]
    assert (len(pairs), len(counter), len(clauses), sum(map(len, clauses))) == (950, 423, 1475, 10230)
    assert sorted(v for pair in state for v in pair) == list(range(134853, 135023))
    return clauses, state


def audit(root):
    started = time.monotonic()
    assert sha((root/SUBJECT).read_bytes()) == SUBJECT_SHA
    raw = (root/MODEL).read_bytes()
    assert sha(raw) == MODEL_SHA
    model = json.loads(raw)
    assert model["complete"] and model["production_solver_calls"] == model["optimizer_calls"] == 0
    for name, expected in model["source_hashes"].items():
        assert sha((root/"experiments/workspace"/name).read_bytes()) == expected
    data = {}
    for name, binding in model["unit_provenance"]["input_bindings"].items():
        b = (root/binding["path"]).read_bytes()
        assert sha(b) == binding["sha256"]
        data[name] = [json.loads(s) for s in b.splitlines()] if name == "bounds" else json.loads(b)
    native = data["native_model"]
    checks = []
    for proof in data["bounds"]:
        info, _, _ = check_bound(native, proof)
        checks.append(info)
    refined, weighted, residual = check_bound(native, data["refined663"])
    assert refined["objective"] == [663] and refined["denominator"] == 6
    assert refined["upper_numerator"] == refined["row_constant"] == 4
    assert refined["all_used_rows_are_equalities"]
    kept = native["kept_original_columns"]
    assert len(kept) == 1103 and kept == sorted(set(kept))
    support = [a for a, coefficient in zip(kept, weighted) if coefficient == 2]
    assert len(support) == 86 and 663 not in support
    assert all(coefficient == (6 if a == 663 else 2 if a in support else 0)
               for a, coefficient in zip(kept, weighted))
    independent = data["independent_bound_replay"]
    assert support == independent["short_identity"]["S"]
    full = independent["short_identity"]["all1214_original_integer_coefficients"]
    assert len(full) == 1214 and all(full[a] == coefficient for a, coefficient in zip(kept, weighted))
    assert independent["short_identity"]["original_integer_right_hand_side"] == 4
    equality = data["equalities"]
    zeros = sorted(equality["proved_zero_columns"] + [663])
    proof = model["unit_provenance"]
    old = data["parent_model"]
    old_zeros = old["unit_provenance"]["all99_zero_columns"]
    assert len(zeros) == len(set(zeros)) == 112
    assert len(old_zeros) == 99 and set(old_zeros) <= set(zeros)
    assert proof["all112_zero_columns"] == zeros
    assert proof["added13_zero_columns"] == sorted(set(zeros) - set(old_zeros))
    assert proof["unit_implications"] == [[-a-1] for a in proof["added13_zero_columns"]]
    H = [sorted(set(h) - set(zeros)) for h in equality["live_cover_supports"]]
    assert H == proof["parity_supports"] and list(map(len, H)) == [35, 41]
    assert len(set(H[0]) & set(H[1])) == 31
    assert proof["parity_equal_values"] == [1, 1]
    assert proof["sum2_support"] == support and proof["sum2_value"] == 2
    assert not (set(support) & set(zeros))
    pair = next(x for x in checks if x["objective"] == [259, 590])
    assert pair["upper_numerator"] < 2 * pair["denominator"]
    assert proof["pair_AMO"] == [259, 590]
    clauses, states = expected_suffix(proof)
    assert states == list(map(tuple, model["suffix_encoding"]["counter_prefix_pairs"]))
    encoded = b"".join((" ".join(map(str, c)) + " 0\n").encode() for c in clauses)
    assert sha(encoded) == model["formula"]["constraint_suffix_sha256"]

    # Compare the actual old and new files without regenerating either CNF.
    parent_path, child_path = Path(old["cnf_path"]), Path(model["cnf_path"])
    parent_hash, child_hash, body_hash = hashlib.sha256(), hashlib.sha256(), hashlib.sha256()
    lines = body_bytes = 0
    with parent_path.open("rb") as left, child_path.open("rb") as right:
        old_header, new_header = left.readline(), right.readline()
        assert old_header == b"p cnf 134852 439689\n"
        assert new_header == b"p cnf 135022 441164\n"
        parent_hash.update(old_header)
        child_hash.update(new_header)
        while True:
            b = left.read(1 << 20)
            if not b:
                break
            assert right.read(len(b)) == b
            parent_hash.update(b)
            child_hash.update(b)
            body_hash.update(b)
            lines += b.count(b"\n")
            body_bytes += len(b)
        suffix = right.read()
        assert suffix == encoded
        child_hash.update(suffix)
    assert lines == 439689 and body_bytes == 57874444
    assert parent_hash.hexdigest() == model["formula"]["base_sha256"] == old["formula"]["CNF_sha256"]
    assert child_hash.hexdigest() == model["formula"]["CNF_sha256"]
    assert body_hash.hexdigest() == model["formula"]["base_clause_body_sha256"]
    cold = data["parent_cold"]
    assert cold["CNF_sha256"] == parent_hash.hexdigest()
    assert cold["status"].startswith("PASS: full original CNF")
    return {
        "status": "PASS: source, exact suffix arithmetic and unchanged prefix bytes",
        "reviewer_source_sha256": sha(Path(__file__).read_bytes()),
        "subject_source": {"path": SUBJECT, "sha256": SUBJECT_SHA},
        "prepared_model": {"path": MODEL, "sha256": MODEL_SHA},
        "source_and_input_bindings": {"sources": model["source_hashes"], "inputs": proof["input_bindings"]},
        "exact_bound_checks": checks, "refined_663": refined,
        "identity": "3*x_663 + sum_{a in S} x_a = 2",
        "identity_support_size": 86,
        "identity_is_equality": "Every nonzero multiplier uses an equality row; all 1,103 surviving coefficients are checked.",
        "Boolean_consequence": "Nonnegative integer x_663 is zero; the other 86 terms sum to two.",
        "new_zero_units": 13,
        "parity_support_sizes": [35, 41],
        "parity_support_intersection_size": 31,
        "distinct_parity_at_most_one_pairs": 950,
        "new_clause_count": len(clauses),
        "new_literal_count": sum(map(len, clauses)),
        "new_auxiliary_range": [134853, 135022],
        "counter_proof": {
            "soundness": "The first two true inputs force the second prefix bit; any third true input contradicts its prohibition clause.",
            "completeness": "For at most two true inputs, assign each prefix bit its actual threshold value.",
            "at_least_two": "Deleting each input in turn leaves a disjunction true exactly when at least two inputs are true.",
            "subject_508_truth_controls_hash_bound_not_repeated": True,
        },
        "existing_CNFs_checked": {
            "old_clauses": lines, "old_body_bytes": body_bytes,
            "old_CNF_sha256": parent_hash.hexdigest(),
            "new_CNF_sha256": child_hash.hexdigest(),
            "new_variables": 135022, "new_clauses": 441164,
            "all_old_clause_bytes_equal": True, "all_new_clause_bytes_equal": True,
        },
        "original_native_rows_or_domain_rebuilt": False,
        "prior_zero_and_parity_proofs_rederived": False,
        "subject_imported": False, "solver_calls": 0, "optimizer_calls": 0,
        "case4_excluded": False,
        "scope": "A necessary Boolean incidence overlay. No full exterior graph or candidate symmetry is imposed.",
        "seconds": time.monotonic() - started,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, default=ROOT)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    assert not a.output.exists()
    report = audit(a.root)
    a.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items()
                      if k not in ["source_and_input_bindings", "exact_bound_checks"]}, indent=2))


if __name__ == "__main__":
    main()

