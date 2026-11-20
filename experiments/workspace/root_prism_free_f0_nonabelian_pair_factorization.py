"""Exact Fourier factorization of every F0 selector-pair orbit count.

This constructs linear moment forms and transport certificates only. It does
not enumerate selector subsets, build a solver, or test a count candidate.
"""
import argparse
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "experiments/logs/root-prism-free"
INPUTS = {
    "scope": ("f0-two-dimensional-moments-scope01.json", "948e256945fc817cc75ea46c969c055b21e61832a4f2177c481884e73338223f"),
    "domains": ("f0-orbit-populations02-domains.json.gz", "4f079468530dba0746512cc4afce01666b2a63a2c8f35f66a4660a4fe3bab8ab"),
    "moments": ("f0-second-moments-preparation02.json.gz", "404d91da35c798ba248887c22a7500957947e24b71d5197dc44432460e6d219e"),
    "characters": ("f0-character-populations01.json.gz", "139d06a3383f8fc79d677972ce052ce29966e8b3406e7d1e7d1077aea7c2cef6"),
    "inverse": ("f0-character-literal-lift-preparation01.json.gz", "241cd14c61b465025c72ffcaa65af8e5c48e9e5a0eda7ea7d252e9d74b22db1e"),
}
H = [[2, -1], [-1, 2]]
IDENTITY = [[1, 0], [0, 1]]
LIMITS = {"seconds": 60, "maximum_record_raw_bytes": 16 << 20,
          "literal_unordered_pairs": 114960, "new_selector_subset_censuses": 0,
          "optimizer_calls": 0}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def read(key):
    name, expected = INPUTS[key]
    raw = (BASE / name).read_bytes()
    assert sha(raw) == expected
    return json.loads(gzip.decompress(raw) if name.endswith(".gz") else raw)


def mul(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(2)) for j in range(2)] for i in range(2)]


def transpose(a):
    return [list(row) for row in zip(*a)]


def add(a, b):
    return [[a[i][j] + b[i][j] for j in range(2)] for i in range(2)]


def trace(a):
    return a[0][0] + a[1][1]


def pair_id(a, b):
    a, b = sorted((a, b))
    assert 0 <= a < b < 480
    return a * (959 - a) // 2 + b - a - 1


def derive():
    started = time.monotonic()
    deadline = started + LIMITS["seconds"]
    def tick():
        if time.monotonic() >= deadline:
            raise TimeoutError("nonabelian coefficient construction deadline")
    scope, domains, moments, characters, inverse = [read(k) for k in INPUTS]
    orbits = domains["selector_orbits"]
    actions = domains["signature_actions"]
    assert orbits == moments["selector_orbits"]
    assert actions == moments["selector_actions"]
    assert len(orbits) == 42 and sorted(a for orbit in orbits for a in orbit) == list(range(480))
    table = scope["group"]["multiplication_table"]
    assert table == characters["group"]["multiplication_table"]
    assert actions[0] == list(range(480))
    # The saved complete action is checked directly, without calling its builder.
    for g in range(12):
        for h in range(12):
            assert all(actions[g][actions[h][a]] == actions[table[g][h]][a] for a in range(480))
    inv = [next(h for h in range(12) if table[g][h] == table[h][g] == 0) for g in range(12)]
    one_d = characters["group"]["characters"]
    reps = scope["two_dimensional_representations"]
    assert list(sorted(reps)) == ["central_minus", "central_plus"] and scope["H"] == H
    stabilizers, transports = [], []
    for oi, orbit in enumerate(orbits):
        tick()
        assert inverse["inverse_tables"][oi]["literal_selectors"] == orbit
        stabilizer = [g for g in range(12) if actions[g][orbit[0]] == orbit[0]]
        assert stabilizer in ([0], [0, 6])
        assert all(table[g][h] == table[h][g] for g in stabilizer for h in range(12))
        assert len(orbit) * len(stabilizer) == 12
        stabilizers.append(stabilizer)
        transports.append({a: next(g for g in range(12) if actions[g][orbit[0]] == a) for a in orbit})
    assert Counter(map(tuple, stabilizers)) == {(0,): 38, (0, 6): 4}
    active_one_d = [[ci for ci, chi in enumerate(one_d) if all(chi[h] == 1 for h in hs)] for hs in stabilizers]
    active_two_d = [[name for name, rep in sorted(reps.items())
                     if all(rep["matrices"][h] == IDENTITY for h in hs)] for hs in stabilizers]
    for pop in characters["signed_populations"]:
        oi, ci = pop["selector_orbit"], pop["character"]
        assert ci in active_one_d[oi] and pop["anchor"] == orbits[oi][0]
        assert pop["literal_selectors"] == orbits[oi]
        assert pop["signs"] == [one_d[ci][transports[oi][a]] for a in orbits[oi]]

    # Exact Fourier inversion of every literal unit vector, including size6 orbits.
    inverse_checks = 0
    for oi, orbit in enumerate(orbits):
        for a in orbit:
            for b in orbit:
                g = table[inv[transports[oi][a]]][transports[oi][b]]
                recovered = sum(one_d[ci][g] for ci in active_one_d[oi])
                recovered += sum(2 * trace(reps[name]["matrices"][g]) for name in active_two_d[oi])
                assert recovered == len(orbit) * int(a == b)
                inverse_checks += 1
    # Pair correlations live on G/K, K=Hi*Hj. These are the only two possible K.
    quotient_checks = []
    for central in (False, True):
        subgroup = [0, 6] if central else [0]
        representatives = sorted({min(table[g][h] for h in subgroup) for g in range(12)})
        active_chi = [ci for ci, chi in enumerate(one_d) if all(chi[h] == 1 for h in subgroup)]
        active_rho = [name for name, rep in sorted(reps.items()) if all(rep["matrices"][h] == IDENTITY for h in subgroup)]
        assert len(active_chi) + 4 * len(active_rho) == len(representatives)
        for g in representatives:
            for h in representatives:
                q = table[inv[g]][h]
                value = sum(one_d[ci][q] for ci in active_chi)
                value += sum(2 * trace(reps[name]["matrices"][q]) for name in active_rho)
                assert value == len(representatives) * int(g == h)
        quotient_checks.append({"central_stabilizer": subgroup, "representatives": representatives,
                                "active_character_indices": active_chi, "active_2D_names": active_rho,
                                "exact_delta_recovery_checks": len(representatives)**2})

    # The two columns of Xi are Fourier vectors. Store integer a=2*x-y,b=y
    # coefficients, so two scalar products suffice for each Gram entry.
    columns, orbit_columns = {}, {}
    for name, rep in sorted(reps.items()):
        columns[name] = []
        orbit_columns[name] = {}
        for oi, orbit in enumerate(orbits):
            if name not in active_two_d[oi]:
                continue
            orbit_columns[name][oi] = [len(columns[name]), len(columns[name]) + 1]
            for k in range(2):
                terms = []
                for a in orbit:
                    matrix = rep["matrices"][transports[oi][a]]
                    terms.append([a, 2 * matrix[0][k] - matrix[1][k], matrix[1][k]])
                columns[name].append({"selector_orbit": oi, "matrix_column": k,
                                      "column_index": len(columns[name]),
                                      "literal_a_b_coefficients": terms})
    assert {name: len(cols) for name, cols in columns.items()} == {"central_minus": 76, "central_plus": 84}
    assert sum(len(active_one_d[oi]) + 4 * len(active_two_d[oi]) for oi in range(42)) == 480

    old_to_new = {old: new for new, old in enumerate(inverse["new15038_to_original15589"])}
    zero_pairs = set(inverse["original_zero_pair_orbits"])
    assert len(zero_pairs) == 389
    forms = {name: [] for name in reps}
    block_inventory, all_pairs, all_pair_orbits = [], 0, set()
    full_coefficients_checked = Counter()
    for i, left in enumerate(orbits):
        for j in range(i, 42):
            tick()
            right = orbits[j]
            pairs = [(a, b) for a in left for b in right if i != j or a < b]
            block_p = set(moments["pair_to_orbit"][pair_id(a, b)] for a, b in pairs)
            all_pairs += len(pairs)
            all_pair_orbits.update(block_p)
            common = sorted(set(active_two_d[i]) & set(active_two_d[j]))
            for name in common:
                matrices = reps[name]["matrices"]
                coefficients, multiplicities = {}, Counter()
                for a, b in pairs:
                    po = moments["pair_to_orbit"][pair_id(a, b)]
                    ta, tb = transports[i][a], transports[j][b]
                    g = table[inv[ta]][tb]
                    direct = mul(mul(transpose(matrices[ta]), H), matrices[tb])
                    wanted = mul(H, matrices[g])
                    assert direct == wanted
                    if i == j:
                        direct = add(direct, transpose(direct))
                        wanted = mul(H, add(matrices[g], matrices[inv[g]]))
                        assert direct == wanted
                    assert po not in coefficients or coefficients[po] == wanted
                    coefficients[po] = wanted
                    multiplicities[po] += 1
                    full_coefficients_checked[name] += 4
                assert set(coefficients) == block_p
                assert all(multiplicities[po] == inverse["original_pair_orbit_sizes"][po] for po in block_p)
                for p in range(2):
                    for q in range(2):
                        if i == j and p > q:
                            continue
                        terms = Counter({i: H[p][q]}) if i == j else Counter()
                        original_terms, zero_terms = [], []
                        for po in sorted(block_p):
                            c = coefficients[po][p][q]
                            if not c:
                                continue
                            original_terms.append([po, c])
                            if po in zero_pairs:
                                zero_terms.append([po, c])
                            else:
                                terms[old_to_new[5847 + po]] += c
                        forms[name].append({"columns": [orbit_columns[name][i][p], orbit_columns[name][j][q]],
                                            "selector_orbits": [i, j], "within_matrix_entry": [p, q],
                                            "native_count_terms": sorted([a, c] for a, c in terms.items() if c),
                                            "original_pair_terms": original_terms,
                                            "proved_zero_pair_terms": zero_terms})
            block_inventory.append({"selector_orbits": [i, j], "literal_unordered_pairs": len(pairs),
                                    "original_pair_orbits": sorted(block_p), "active_2D_names": common})
    assert all_pairs == LIMITS["literal_unordered_pairs"]
    assert all_pair_orbits == set(range(9742)) and len(block_inventory) == 903
    assert {name: len(f) for name, f in forms.items()} == {"central_minus": 2926, "central_plus": 3570}
    for name, cols in columns.items():
        assert [r["columns"] for r in forms[name]] != []
        assert sorted(tuple(r["columns"]) for r in forms[name]) == [(i, j) for i in range(len(cols)) for j in range(i, len(cols))]
    # Bind the earlier six forms by actual column labels, not by an assumed order.
    small = {(tuple(r["selector_orbits"]), tuple(r["within_matrix_entry"])): r for r in forms["central_plus"]}
    for old in scope["six_exact_entry_forms"]:
        p, q = old["matrix_entry"]
        new = small[((p + 2, q + 2), (0, 0))]
        assert new["native_count_terms"] == old["native_count_terms"]
        assert new["proved_zero_pair_terms"] == old["proved_zero_pair_terms"]
    # The diagonalized metric identity is checked coefficient by coefficient.
    # (2*x-y)(2*u-v)+3*y*v = 2*(2*x*u-x*v-y*u+2*y*v).
    assert [4, -2, -2, 4] == [2 * H[i][j] for i in range(2) for j in range(2)]
    tick()
    return {"schema": "conway99.f0.nonabelian-pair-factorization.v1",
            "status": "COMPLETE: exact coefficient and Fourier inversion construction; no solver",
            "source_sha256": sha(Path(__file__).read_bytes()), "inputs": INPUTS, "limits": LIMITS,
            "group": "S3 x C2", "H": H, "stabilizers": stabilizers,
            "active_one_dimensional_characters": active_one_d,
            "active_two_dimensional_representations": active_two_d,
            "literal_transports": [sorted(t.items()) for t in transports],
            "literal_unit_vector_inversion_checks": inverse_checks,
            "correlation_Fourier_delta_checks": quotient_checks,
            "Fourier_columns_in_a_b_coordinates": columns, "Gram_forms": forms,
            "block_inventory": block_inventory, "complete_literal_unordered_pairs": all_pairs,
            "original_pair_orbits": 9742, "full_matrix_literal_coefficients_checked": dict(full_coefficients_checked),
            "old_six_Gram_forms_recovered": True,
            "missing_integer_Fourier_coordinates": 320, "new_scalar_Gram_identities": 6496,
            "scalar_products_using_diagonal_metric": 12992,
            "existing_one_dimensional_products": 3288,
            "proposed_full_lift_products": 16280,
            "proposed_full_lift_variables_before_other_changes": 31756,
            "local_mask_tables_required_for_exact_literal_realization": True,
            "pair_histogram_equivalence_requires_all_active_irreps": True,
            "local_mask_tables_built_or_replaced": False,
            "native_model_constructed": False, "new_selector_subsets_enumerated": 0,
            "optimizer_calls": 0, "count_or_graph_feasibility_claimed": False,
            "seconds": time.monotonic() - started}


def main():
    if not __debug__:
        raise RuntimeError("assertions are required")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    result = derive()
    raw = canonical(result) + b"\n"
    assert len(raw) <= LIMITS["maximum_record_raw_bytes"]
    payload = gzip.compress(raw, mtime=0)
    with args.output.open("xb") as out:
        out.write(payload)
    print(json.dumps({"status": result["status"], "seconds": result["seconds"], "raw_bytes": len(raw),
                      "bytes": len(payload), "sha256": sha(payload),
                      "missing_coordinates": 320, "new_Gram_identities": 6496, "products": 12992}))


if __name__ == "__main__":
    main()
