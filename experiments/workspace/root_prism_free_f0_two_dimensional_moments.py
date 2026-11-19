"""Small exact arithmetic preparation for the two missing 2D core-group blocks.

Read only frozen actions, inverse profiles and count maps. No local subset
census, count candidate, full Gram block, optimizer or CSP is evaluated.
"""
import argparse
from collections import Counter
import gzip
import hashlib
from itertools import combinations, product
import json
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "experiments/logs/root-prism-free"
INPUTS = {
    "domains": ("f0-orbit-populations02-domains.json.gz", "4f079468530dba0746512cc4afce01666b2a63a2c8f35f66a4660a4fe3bab8ab"),
    "moments": ("f0-second-moments-preparation02.json.gz", "404d91da35c798ba248887c22a7500957947e24b71d5197dc44432460e6d219e"),
    "characters": ("f0-character-populations01.json.gz", "139d06a3383f8fc79d677972ce052ce29966e8b3406e7d1e7d1077aea7c2cef6"),
    "inverse": ("f0-character-literal-lift-preparation01.json.gz", "241cd14c61b465025c72ffcaa65af8e5c48e9e5a0eda7ea7d252e9d74b22db1e"),
}
I = [[1, 0], [0, 1]]
R = [[0, -1], [1, -1]]
S = [[0, 1], [1, 0]]
H = [[2, -1], [-1, 2]]


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def mul(a, b):
    return [[sum(a[i][k]*b[k][j] for k in range(2)) for j in range(2)] for i in range(2)]


def apply(a, v):
    return [sum(a[i][j]*v[j] for j in range(2)) for i in range(2)]


def transpose(a):
    return [list(row) for row in zip(*a)]


def inner(u, v):
    return sum(u[i]*H[i][j]*v[j] for i in range(2) for j in range(2))


def det2(a):
    return a[0][0]*a[1][1]-a[0][1]*a[1][0]


def det3(a):
    return sum(a[0][i]*(a[1][(i+1)%3]*a[2][(i+2)%3]-a[1][(i+2)%3]*a[2][(i+1)%3]) for i in range(3))


def pair_id(a, b):
    a, b = sorted((a, b))
    assert 0 <= a < b < 480
    return a*(959-a)//2+b-a-1


def prepare():
    start = time.monotonic()
    data = {}
    for key, (name, expected) in INPUTS.items():
        raw = (BASE/name).read_bytes()
        assert sha(raw) == expected
        data[key] = json.loads(gzip.decompress(raw))
    domains, moments, chars, inverse = [data[k] for k in ("domains", "moments", "characters", "inverse")]
    actions, orbits = domains["signature_actions"], domains["selector_orbits"]
    assert actions == moments["selector_actions"] and orbits == moments["selector_orbits"]
    assert len(actions) == 12 and all(sorted(a) == list(range(480)) for a in actions)
    index = {tuple(a): i for i, a in enumerate(actions)}
    assert len(index) == 12
    table = [[index[tuple(a[b[j]] for j in range(480))] for b in actions] for a in actions]
    assert table == chars["group"]["multiplication_table"]
    assert actions[0] == list(range(480))
    r, s, z = 3, 1, 6
    assert table[r][r] == 4 and table[4][r] == 0
    assert table[s][s] == table[z][z] == 0 and table[table[s][r]][s] == 4
    center = [g for g in range(12) if all(table[g][h] == table[h][g] for h in range(12))]
    assert center == [0, z]
    oneD = chars["group"]["characters"]
    kernel = [g for g in range(12) if all(chi[g] == 1 for chi in oneD)]
    assert kernel == [0, 3, 4]
    forms = {}
    for i, j, k in product(range(3), range(2), range(2)):
        g = table[table[[0, r, 4][i]][s if j else 0]][z if k else 0]
        assert g not in forms
        forms[g] = [i, j, k]
    assert len(forms) == 12 and det2(H) == 3 and H[0][0] > 0
    irreps, characters = {}, list(oneD)
    for epsilon, name in ((1, "central_plus"), (-1, "central_minus")):
        matrices = []
        for g in range(12):
            i, j, k = forms[g]
            matrix = mul([I, R, mul(R, R)][i], S if j else I)
            matrices.append([[epsilon**k*v for v in row] for row in matrix])
        assert all(mul(matrices[a], matrices[b]) == matrices[table[a][b]]
                   for a in range(12) for b in range(12))
        assert all(mul(mul(transpose(a), H), a) == H for a in matrices)
        chi = [a[0][0]+a[1][1] for a in matrices]
        characters.append(chi)
        irreps[name] = {"dimension": 2, "central_sign": epsilon, "matrices": matrices, "character": chi}
    orthogonality = [[sum(a[g]*b[g] for g in range(12)) for b in characters] for a in characters]
    assert orthogonality == [[12*int(i == j) for j in range(6)] for i in range(6)]
    assert sum(chi[0]**2 for chi in characters) == 12
    fixed_points = [sum(a[i] == i for i in range(480)) for a in actions]
    multiplicities = [sum(c*f for c, f in zip(chi, fixed_points))//12 for chi in characters]
    assert all(sum(c*f for c, f in zip(chi, fixed_points)) % 12 == 0 for chi in characters)
    assert multiplicities == [42, 38, 42, 38, 84, 76]
    stabilizers = [[g for g, a in enumerate(actions) if a[orbit[0]] == orbit[0]] for orbit in orbits]
    assert Counter(map(tuple, stabilizers)) == {(0,): 38, (0, 6): 4}
    for name, irrep in irreps.items():
        per_orbit = []
        for oi, stabilizer in enumerate(stabilizers):
            vectors = [u for u in ([1, 0], [0, 1])
                       if all(apply(irrep["matrices"][g], u) == u for g in stabilizer)]
            assert len(vectors) == (2 if stabilizer == [0] or irrep["central_sign"] == 1 else 0)
            per_orbit.append(len(vectors))
        irrep["multiplicity"] = sum(per_orbit)
        irrep["multiplicity_by_selector_orbit"] = per_orbit
        irrep["full_lower_entry_count_not_built"] = sum(per_orbit)*(sum(per_orbit)+1)//2
    # Only three equivariant columns in the plus block are constructed.
    columns = []
    for oi in (2, 3, 4):
        orbit, u = orbits[oi], [1, 0]
        transport = {a: next(g for g, move in enumerate(actions) if move[orbit[0]] == a) for a in orbit}
        vectors = {a: apply(irreps["central_plus"]["matrices"][g], u) for a, g in transport.items()}
        assert all(vectors[move[a]] == apply(irreps["central_plus"]["matrices"][g], vectors[a])
                   for g, move in enumerate(actions) for a in orbit)
        columns.append({"selector_orbit": oi, "anchor": orbit[0], "basis_vector": u,
                        "literal_selectors": orbit, "transports": [transport[a] for a in orbit],
                        "vectors": [vectors[a] for a in orbit]})
    old_to_new = {old: new for new, old in enumerate(inverse["new15038_to_original15589"])}
    zero_pairs = set(inverse["original_zero_pair_orbits"])
    coefficients = []
    for p in range(3):
        for q in range(p, 3):
            left, right = columns[p], columns[q]
            f = dict(zip(left["literal_selectors"], left["vectors"]))
            g = dict(zip(right["literal_selectors"], right["vectors"]))
            union = sorted(set(f) | set(g))
            diagonal = {}
            for a in union:
                c = inner(f.get(a, [0, 0]), g.get(a, [0, 0]))
                oi = inverse["literal_selector_to_orbit"][a]
                assert oi not in diagonal or diagonal[oi] == c
                diagonal[oi] = c
            pair_coeff, pair_visits = {}, Counter()
            for a, b in combinations(union, 2):
                c = inner(f.get(a, [0, 0]), g.get(b, [0, 0])) + inner(f.get(b, [0, 0]), g.get(a, [0, 0]))
                po = moments["pair_to_orbit"][pair_id(a, b)]
                assert po not in pair_coeff or pair_coeff[po] == c
                pair_coeff[po] = c; pair_visits[po] += 1
            assert all(pair_visits[po] == inverse["original_pair_orbit_sizes"][po] for po in pair_visits)
            native = Counter({oi: c for oi, c in diagonal.items() if c})
            omitted = []
            for po, c in pair_coeff.items():
                if c:
                    if po in zero_pairs:
                        omitted.append([po, c])
                    else:
                        native[old_to_new[5847+po]] += c
            coefficients.append({"matrix_entry": [p, q],
                "selector_terms": sorted([[oi, c] for oi, c in diagonal.items() if c]),
                "original_pair_terms": sorted([[po, c] for po, c in pair_coeff.items() if c]),
                "native_count_terms": sorted([[j, c] for j, c in native.items() if c]),
                "proved_zero_pair_terms": sorted(omitted),
                "literal_unordered_pair_coefficients_checked": sum(pair_visits.values())})
    chosen = []
    for column in columns[:2]:
        tab = inverse["inverse_tables"][column["selector_orbit"]]
        desired = [1]+[0]*(len(tab["count_columns"])-1)+[1]*len(tab["signed_population_columns"])
        profile = next(p for p in tab["profiles"] if p["counts_and_signed_populations"] == desired)
        assert len(profile["local_masks"]) == 3 and all(m.bit_count() == 1 for m in profile["local_masks"])
        chosen.append({"selector_orbit": column["selector_orbit"], "tuple_index": profile["tuple_index"],
                       "tuple": desired, "local_masks": profile["local_masks"]})
    table_rows = []
    for i, j in product(range(3), repeat=2):
        positions = [chosen[0]["local_masks"][i].bit_length()-1, chosen[1]["local_masks"][j].bit_length()-1]
        u, v = [columns[k]["vectors"][positions[k]] for k in range(2)]
        a, b, c = inner(u, u), inner(u, v), inner(v, v)
        determinant = u[0]*v[1]-u[1]*v[0]
        assert a*c-b*b == 3*determinant**2 and a == c == 2
        literals = [columns[k]["literal_selectors"][positions[k]] for k in range(2)]
        po = moments["pair_to_orbit"][pair_id(*literals)]
        table_rows.append({"profile_choice_indices": [i, j], "literal_pair": literals,
                           "original_pair_orbit": po, "previously_proved_zero": po in zero_pairs,
                           "vectors": [u, v], "Gram": [a, b, c], "oriented_area": determinant})
    assert Counter(row["Gram"][1] for row in table_rows) == {-1: 6, 2: 3}
    # An explicit mixture illustration checks the nonlinear scope, not a count candidate.
    vectors_a = [[1, 0]]*3
    vectors_b = [[1, 0], [0, 1], [-1, -1]]
    gram_a = [[inner(u, v) for v in vectors_a] for u in vectors_a]
    gram_b = [[inner(u, v) for v in vectors_b] for u in vectors_b]
    gram_sum = [[gram_a[i][j]+gram_b[i][j] for j in range(3)] for i in range(3)]
    assert det3(gram_a) == det3(gram_b) == 0 and det3(gram_sum) == 54
    anchors = [c["anchor"] for c in columns]
    sets = [anchors, [anchors[0], actions[r][anchors[1]], actions[4][anchors[2]]]]
    for selected, expected in zip(sets, (vectors_a, vectors_b)):
        observed = [column["vectors"][column["literal_selectors"].index(a)]
                    for column, a in zip(columns, selected)]
        assert observed == expected
    signed = [[sum(w for a, w in zip(p["literal_selectors"], p["signs"]) if a in selected)
               for p in chars["signed_populations"]] for selected in sets]
    assert signed[0] == signed[1]
    assert all(Counter(inverse["literal_selector_to_orbit"][a] for a in selected) == {2: 1, 3: 1, 4: 1}
               for selected in sets)
    assert time.monotonic()-start < 30
    return {"schema": "conway99.f0.two-dimensional-moment-scope.v1", "status": "PASS: exact small arithmetic preparation",
        "source_sha256": sha(Path(__file__).read_bytes()), "inputs": INPUTS,
        "group": {"multiplication_table": table, "normal_forms_r_i_s_j_z_k": [forms[g] for g in range(12)],
                  "generators": {"r": r, "s": s, "z": z}, "center": center, "common_character_kernel": kernel,
                  "isomorphism": "S3 x C2", "faithful_literal_action_checked": True},
        "H": H, "irreducible_character_orthogonality_times12": orthogonality,
        "irreducible_dimensions": [1, 1, 1, 1, 2, 2], "permutation_multiplicities": multiplicities,
        "selector_stabilizers": stabilizers, "two_dimensional_representations": irreps,
        "three_constructed_plus_columns": columns, "six_exact_entry_forms": coefficients,
        "small_profile_pair": {"profiles": chosen, "nine_literal_cases": table_rows,
            "unconditional_inner_products_under_these_profiles": [-1, 2],
            "inner_products_after_previous_zero_restrictions": sorted({row["Gram"][1] for row in table_rows
                                                                        if not row["previously_proved_zero"]}),
            "cases_after_previous_zero_restrictions": sum(not row["previously_proved_zero"] for row in table_rows),
            "further_previous_zero_restrictions_retained": True, "full_incidence_claimed": False},
        "integer_Gram_theorem": {"rank_bound": 2, "diagonal_even": True,
            "two_by_two_determinant": "Bpp*Bqq-Bpq^2 = 3*det[w_p,w_q]^2",
            "three_by_three_determinant": "a*d*f+2*b*c*e-a*e^2-d*c^2-f*b^2 = 0",
            "basis_or_orbit_size_divisor": 1},
        "mixture_scope_control": {"literal_selector_sets": sets, "same_all_one_dimensional_populations": True,
            "first_Gram": gram_a, "second_Gram": gram_b, "twice_mean_Gram": gram_sum,
            "twice_mean_determinant": 54, "mean_determinant": [27, 4],
            "is_full_model_or_integer_count_candidate": False,
            "scope": "One-dimensional product identities alone do not imply the 2D rank bound. No nonredundancy against all other F0 constraints is claimed."},
        "full_Gram_blocks_constructed": 0, "production_candidates_evaluated": 0,
        "new_local_subset_censuses": 0, "optimizer_calls": 0, "seconds": time.monotonic()-start}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = prepare()
    with args.output.open("xb") as out:
        out.write(canonical(result)+b"\n")
    print(json.dumps({"status": result["status"], "seconds": result["seconds"],
                      "multiplicities": result["permutation_multiplicities"]}))


if __name__ == "__main__":
    main()
