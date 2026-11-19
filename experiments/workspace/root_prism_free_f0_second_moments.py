"""Point-independent second selector moments for the conditional F0 component.

Preparation only: no optimizer, SAT solver or semidefinite solver is imported.
All full selector pairs remain represented. Certified zero moments are added
as explicit equalities; they are not used to silently remove variables.
"""
import argparse
from collections import Counter, defaultdict
from fractions import Fraction
import gzip
import hashlib
from itertools import combinations
import json
import math
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[2]
LOGS = ROOT/"experiments/logs/root-prism-free"
INPUTS = {
    "f0-boolean-fractional-model.json.gz": "703206929c9c85a40ac4ddcbfb1708c716c288482cf50c77a32249404e35b782",
    "f0-boolean-normalized-registry-preparation.json.gz": "5be0ea987bff89e45359508a6ba52eb6178653c86ffb9763af8467f468103bab",
    "f0-fractional-structural-recovery-input.json": "ef4018f26c48e9eb90bf544d41678778d71b587994096383023c8836e70bca6e",
    "f0-incidence-case00-run01/result.json": "64d5411e04764b0d7e7157c47b67d759e536a401fee8fe36e274943f2fda4abf",
}
N, BASE_VARIABLES = 480, 5847


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("ascii")


def tick(deadline):
    if time.monotonic() > deadline:
        raise TimeoutError("second-moment preparation time limit")


def load():
    output = {}
    for name, expected in INPUTS.items():
        raw = (LOGS/name).read_bytes()
        assert digest(raw) == expected, name
        output[name] = json.loads(gzip.decompress(raw) if name.endswith(".gz") else raw)
    return output


def pair_id(a, b):
    assert a != b
    if a > b:
        a, b = b, a
    return a*(2*N-a-1)//2+b-a-1


def clean_terms(terms):
    return tuple(sorted((j, int(c)) for j, c in terms.items() if c))


def equality_key(terms):
    terms = clean_terms(terms)
    if not terms:
        return (), 0
    divisor = math.gcd(*(abs(c) for j, c in terms))
    if terms[0][1] < 0:
        divisor = -divisor
    return tuple((j, c//divisor) for j, c in terms), divisor


def inverse(matrix):
    n = len(matrix)
    rows = [[Fraction(v) for v in row]+[Fraction(i == j) for j in range(n)]
            for i, row in enumerate(matrix)]
    for j in range(n):
        pivot = next(i for i in range(j, n) if rows[i][j])
        rows[j], rows[pivot] = rows[pivot], rows[j]
        d = rows[j][j]
        rows[j] = [v/d for v in rows[j]]
        for i in range(n):
            if i == j or not rows[i][j]:
                continue
            d = rows[i][j]
            rows[i] = [x-d*y for x, y in zip(rows[i], rows[j])]
    answer = [row[n:] for row in rows]
    denominator = math.lcm(*(v.denominator for row in answer for v in row))
    numerator = [[int(v*denominator) for v in row] for row in answer]
    assert [[sum(matrix[i][k]*numerator[k][j] for k in range(n)) for j in range(n)]
            for i in range(n)] == [[denominator*int(i == j) for j in range(n)] for i in range(n)]
    return numerator, denominator


def psd_ldl(matrix, strict=False):
    n = len(matrix)
    a = [[Fraction(v) for v in row] for row in matrix]
    assert all(a[i][j] == a[j][i] for i in range(n) for j in range(n))
    pivots = []
    for k in range(n):
        d = a[k][k]
        assert d >= 0 and (d > 0 if strict else True)
        pivots.append([str(d.numerator), str(d.denominator)])
        if not d:
            assert all(a[k][j] == 0 for j in range(k+1, n))
            continue
        for i in range(k+1, n):
            for j in range(i, n):
                a[i][j] -= a[i][k]*a[k][j]/d
                a[j][i] = a[i][j]
    return pivots


def projector_data(adjacency, triples, selector_orbits, pair_orbits, pairs, deadline):
    result = []
    for diagonal, edge_coefficient, constant, name in (
            (27, -9, 1, "27I-9A+J"),
            (44, 11, -2, "44I+11A-2J")):
        k = [[diagonal*int(i == j)+edge_coefficient*adjacency[i][j]+constant
              for j in range(18)] for i in range(18)]
        ldl = psd_ldl(k, strict=True)
        numerator, denominator = inverse(k)
        cross = [[constant+edge_coefficient*int(i in h) for i in range(18)] for h in triples]
        multiplied = [[sum(numerator[i][j]*u[j] for j in range(18)) for i in range(18)] for u in cross]
        def value(a, b):
            return sum(cross[a][i]*multiplied[b][i] for i in range(18))
        diagonal_values = []
        for orbit in selector_orbits:
            observed = {value(a, a) for a in orbit}
            assert len(observed) == 1
            diagonal_values.append(observed.pop())
        off_diagonal = []
        for orbit in pair_orbits:
            observed = {value(*pairs[p]) for p in orbit}
            assert len(observed) == 1
            off_diagonal.append(observed.pop())
        tick(deadline)
        result.append({
            "name": name, "core_matrix": k, "positive_LDL_pivots": ldl,
            "inverse_denominator": str(denominator),
            "inverse_numerator": [[str(v) for v in row] for row in numerator],
            "projector_cross_vector": {"constant": constant, "incidence_coefficient": edge_coefficient},
            "H_diagonal_by_selector_orbit": list(map(str, diagonal_values)),
            "H_off_diagonal_by_pair_orbit": list(map(str, off_diagonal)),
            "basic_PSD": {"diagonal_x_coefficient": diagonal+constant,
                          "off_diagonal_Z_coefficient": constant, "Y_coefficient": edge_coefficient},
            "Schur_PSD": {
                "common_positive_denominator": str(denominator),
                "diagonal_x_coefficients": [str((diagonal+constant)*denominator-v) for v in diagonal_values],
                "off_diagonal_Z_coefficients": [str(constant*denominator-v) for v in off_diagonal],
                "Y_coefficient": str(edge_coefficient*denominator)},
            "full_H_entries_checked": N*(N+1)//2,
            "maximum_H_numerator_bits": max(abs(v).bit_length() for v in diagonal_values+off_diagonal),
            "mixed_quota_targets_used_as_projector_cross_vectors": False,
        })
    return result


def rook_projector_controls():
    # A concrete nine-vertex rook graph gives independent positive controls
    # for the fixed projector constants and block-Schur formulas.
    a = [[int(i != j and (i//3 == j//3 or i%3 == j%3)) for j in range(9)] for i in range(9)]
    core, outside = [0, 1, 3], [2, 4, 5, 6, 7, 8]
    output = []
    for d, e, c in ((27, -9, 1), (44, 11, -2)):
        whole = [[d*int(i == j)+e*a[i][j]+c for j in range(9)] for i in range(9)]
        psd_ldl(whole)
        k = [[whole[i][j] for j in core] for i in core]
        psd_ldl(k, strict=True)
        num, den = inverse(k)
        cross = [[c+e*a[i][b] for i in core] for b in outside]
        schur = [[Fraction(whole[b][f])-Fraction(
            sum(cross[j][u]*num[u][v]*cross[l][v] for u in range(3) for v in range(3)), den)
            for l, f in enumerate(outside)] for j, b in enumerate(outside)]
        pivots = psd_ldl(schur)
        assert all(schur[j][l] == Fraction(d*int(j == l)+e*a[b][f]+c) -
            Fraction(sum(cross[j][u]*num[u][v]*cross[l][v] for u in range(3) for v in range(3)), den)
            for j, b in enumerate(outside) for l, f in enumerate(outside))
        output.append({"diagonal": d, "edge": e, "constant": c,
                       "whole_projector_PSD": True, "core_positive_definite": True,
                       "Schur_positive_semidefinite": True, "Schur_LDL_pivots": pivots})
    return output


def calculate(seconds):
    started = time.monotonic()
    deadline = started+seconds
    saved = load()
    base = saved["f0-boolean-fractional-model.json.gz"]
    prior = saved["f0-boolean-normalized-registry-preparation.json.gz"]
    original = saved["f0-fractional-structural-recovery-input.json"]
    data = base["validation"]
    triples, core = data["triples"], data["core"]
    adjacency = [[core[i+3] >> (j+3) & 1 for j in range(18)] for i in range(18)]
    assert all(sum(row) == 3 for row in adjacency)
    gram = [[12*int(i == j)+2-(core[i+3]&core[j+3]).bit_count()-(core[i+3] >> (j+3) & 1)
             for j in range(18)] for i in range(18)]
    component_actions = original["component_actions"]
    positions = {tuple(h): i for i, h in enumerate(triples)}
    actions = []
    for move in component_actions:
        assert sorted(move) == list(range(18))
        fiber_move = [move[6*f]//6 for f in range(3)]
        assert all(move[i]//6 == fiber_move[i//6] for i in range(18))
        full = fiber_move+[3+move[i] for i in range(18)]
        assert sorted(full) == list(range(21))
        assert all((core[i] >> j & 1) == (core[full[i]] >> full[j] & 1) for i in range(21) for j in range(21))
        actions.append([positions[tuple(sorted(move[i] for i in h))] for h in triples])
    assert actions == prior["signature_actions"] and len(actions) == 12
    action_set = {tuple(p) for p in actions}
    assert len(action_set) == 12 and tuple(range(N)) in action_set
    for left in actions:
        for right in actions:
            assert tuple(left[right[a]] for a in range(N)) in action_set
    selector_orbits = data["selector_orbits"]
    x_orbit = [-1]*N
    for o, members in enumerate(selector_orbits):
        for a in members:
            assert x_orbit[a] == -1
            x_orbit[a] = o
        assert {action[members[0]] for action in actions} == set(members)
    assert len(selector_orbits) == 42 and min(x_orbit) >= 0
    pairs = list(combinations(range(N), 2))
    assert all(pair_id(a, b) == i for i, (a, b) in enumerate(pairs))
    pair_orbit = [-1]*len(pairs)
    pair_orbits = []
    for p, (a, b) in enumerate(pairs):
        if pair_orbit[p] >= 0:
            continue
        members = sorted({pair_id(action[a], action[b]) for action in actions})
        assert members[0] == p
        o = len(pair_orbits)
        for q in members:
            assert pair_orbit[q] == -1
            pair_orbit[q] = o
        pair_orbits.append(members)
    burnside = []
    for action in actions:
        fixed = sum(action[a] == a for a in range(N))
        two_cycles = sum(action[a] != a and action[action[a]] == a for a in range(N))//2
        burnside.append({"fixed_selectors": fixed, "two_cycles": two_cycles,
                         "fixed_distinct_unordered_pairs": math.comb(fixed, 2)+two_cycles})
    assert len(pair_orbits) == sum(x["fixed_distinct_unordered_pairs"] for x in burnside)//12 == 9742
    tick(deadline)

    gram_pairs = [(i, j) for i in range(18) for j in range(i, 18)]
    selector_rows = [{"family": "Gram", "core_pair": [i, j],
                      "support": [a for a, h in enumerate(triples) if i in h and j in h],
                      "quota": gram[i][j]} for i, j in gram_pairs]
    selector_rows.append({"family": "population", "support": list(range(N)), "quota": 60})
    assert len(selector_rows) == 172 and all(row["support"] or row["quota"] == 0 for row in selector_rows)
    rlt_rows, rlt_index, full_map, full_factor = [], {}, [], []
    for a in range(N):
        for row in selector_rows:
            terms = Counter()
            for b in row["support"]:
                terms[x_orbit[a] if a == b else BASE_VARIABLES+pair_orbit[pair_id(a, b)]] += 1
            terms[x_orbit[a]] -= row["quota"]
            key, factor = equality_key(terms)
            if not key:
                full_map.append(-1); full_factor.append(0)
                continue
            if key not in rlt_index:
                rlt_index[key] = len(rlt_rows)
                rlt_rows.append({"terms": [list(t) for t in key], "rhs": 0, "family": "selector RLT equality"})
            full_map.append(rlt_index[key]); full_factor.append(factor)
        tick(deadline)
    core_pair_id = {pair: i for i, pair in enumerate(gram_pairs)}
    row_actions = [[core_pair_id[tuple(sorted((move[i], move[j])))] for i, j in gram_pairs]+[171]
                   for move in component_actions]
    for ai, action in enumerate(actions):
        for a in range(N):
            for r in range(172):
                i, j = 172*a+r, 172*action[a]+row_actions[ai][r]
                assert full_map[i] == full_map[j] and full_factor[i] == full_factor[j]
    tick(deadline)

    zero_pairs = {}
    for r, row in enumerate(selector_rows[:-1]):
        if row["quota"] != 1:
            continue
        for a, b in combinations(row["support"], 2):
            p = pair_id(a, b)
            assert p not in zero_pairs
            assert a in row["support"] and b in row["support"]
            # Multiplying the quota-one row by z_a and Z_aa=x_a gives
            # a sum of nonnegative off-diagonal moments equal to zero.
            terms = rlt_rows[full_map[172*a+r]]["terms"]
            assert all(j >= BASE_VARIABLES and c > 0 for j, c in terms)
            zero_pairs[p] = {"pair_id": p, "kind": "quota-one nonnegative lifted equality",
                             "anchor": a, "other": b, "selector_Gram_row": r,
                             "full_RLT_row": 172*a+r}
    quota_zeros = len(zero_pairs)
    for a, b in data["motif_pairs"]:
        p = pair_id(a, b)
        assert p not in zero_pairs
        # z_a(z_a+z_b-1)<=0 gives Z_ab<=0; combine Z_ab>=0.
        zero_pairs[p] = {"pair_id": p, "kind": "certified binary motif times selector",
                         "anchor": a, "other": b,
                         "literal_polynomial": "z_a*(z_a+z_b-1)=z_a*z_b"}
    assert quota_zeros == 4320 and len(zero_pairs) == 4410
    zero_orbits = sorted({pair_orbit[p] for p in zero_pairs})
    for o in zero_orbits:
        assert set(pair_orbits[o]) <= set(zero_pairs)
    zero_rows = [{"terms": [[BASE_VARIABLES+o, 1]], "rhs": 0,
                  "family": "certified zero selector moment"} for o in zero_orbits]

    inequalities, inequality_ids = [], {}
    bound_map_hash = hashlib.sha256()
    def add_inequality(terms, rhs, family):
        key = (clean_terms(terms), rhs)
        if key not in inequality_ids:
            inequality_ids[key] = len(inequalities)
            inequalities.append({"terms": [list(t) for t in key[0]], "rhs": rhs, "family": family})
        return inequality_ids[key]
    for p, (a, b) in enumerate(pairs):
        z = BASE_VARIABLES+pair_orbit[p]
        indices = []
        for endpoint in (a, b):
            indices.append(add_inequality(Counter({z: 1, x_orbit[endpoint]: -1}), 0, "Z upper activation"))
        terms = Counter({z: -1})
        terms[x_orbit[a]] += 1; terms[x_orbit[b]] += 1
        indices.append(add_inequality(terms, 1, "Z lower Frechet bound"))
        bound_map_hash.update(canonical(indices))
    moment_bound_rows = len(inequalities)
    edge_links = []
    for e, members in enumerate(data["edge_orbits"]):
        observed = {pair_orbit[pair_id(*data["edges"][i])] for i in members}
        assert len(observed) == 1
        o = observed.pop()
        q = add_inequality(Counter({42+e: 1, BASE_VARIABLES+o: -1}), 0, "Y bounded by selector pair moment")
        edge_links.append({"edge_orbit": e, "pair_orbit": o, "inequality": q})
    assert len({x["pair_orbit"] for x in edge_links}) == len(edge_links) == 5805
    assert all(pair_id(*edge) not in zero_pairs for edge in data["edges"])
    tick(deadline)

    # Actual binary first-component designs control only the RLT/selector block.
    # They are known not to give feasible shared exterior edges and are not
    # asserted to satisfy the later4416 necessary selector cuts.
    chosen = saved["f0-incidence-case00-run01/result.json"]["incidence_witness"]["selected_columns"]
    assert len(chosen) == len(set(chosen)) == 60
    images = [set(action[a] for a in chosen) for action in actions]
    x_count = [sum(a in selected for selected in images) for a in range(N)]
    z_count = [sum(a in selected and b in selected for selected in images) for a, b in pairs]
    for row in selector_rows:
        assert all(sum(b in selected for b in row["support"]) == row["quota"] for selected in images)
    values = [0]*(BASE_VARIABLES+len(pair_orbits))
    for o, members in enumerate(selector_orbits):
        observed = {x_count[a] for a in members}; assert len(observed) == 1; values[o] = observed.pop()
    for o, members in enumerate(pair_orbits):
        observed = {z_count[p] for p in members}; assert len(observed) == 1; values[BASE_VARIABLES+o] = observed.pop()
    for row in rlt_rows+zero_rows:
        assert sum(c*values[j] for j, c in row["terms"]) == 0
    for row in inequalities[:moment_bound_rows]:
        assert sum(c*values[j] for j, c in row["terms"]) <= 12*row["rhs"]
    assert all(z_count[p] == 0 for p in zero_pairs)
    control = {"status": "PASS: averaged known binary designs satisfy only the selector/RLT/moment-bound block",
               "binary_images": 12, "population": 60, "common_denominator": 12,
               "RLT_quotient_equalities_checked": len(rlt_rows), "certified_zero_rows_checked": len(zero_rows),
               "moment_bounds_checked": moment_bound_rows,
               "full_shared_model_or4416_cut_feasibility_claimed": False}
    tick(deadline)
    projectors = projector_data(adjacency, triples, selector_orbits, pair_orbits, pairs, deadline)
    rook = rook_projector_controls()
    tick(deadline)

    matrix = {
        "variables": BASE_VARIABLES+len(pair_orbits), "lower": 0, "upper": 1,
        "equalities": base["matrix"]["equalities"]+rlt_rows+zero_rows,
        "inequalities": base["matrix"]["inequalities"]+inequalities,
    }
    assert matrix["equalities"][:686] == base["matrix"]["equalities"]
    assert matrix["inequalities"][:11449] == base["matrix"]["inequalities"]
    counts = {
        "full_selector_variables": 480, "full_edge_variables": 68394,
        "full_distinct_selector_pair_variables": len(pairs),
        "full_total_variables_with_diagonal_aliases": 480+68394+len(pairs),
        "selector_orbits": 42, "edge_orbits": 5805, "selector_pair_orbits": len(pair_orbits),
        "quotient_variables": matrix["variables"], "full_RLT_equalities": N*172,
        "trivial_full_RLT_equalities": full_map.count(-1),
        "distinct_quotient_RLT_equalities": len(rlt_rows),
        "RLT_group_transport_checks": N*172*12,
        "quota_one_forced_zero_pairs": quota_zeros, "motif_forced_zero_pairs": 90,
        "total_certified_zero_pairs": len(zero_pairs), "certified_zero_pair_orbits": len(zero_orbits),
        "full_moment_bound_rows": 3*len(pairs), "quotient_moment_bound_rows": moment_bound_rows,
        "full_Y_le_Z_rows": 68394, "quotient_Y_le_Z_rows": len(edge_links),
        "combined_linear_equalities": len(matrix["equalities"]),
        "combined_linear_inequalities": len(matrix["inequalities"]),
        "combined_linear_nonzeros": sum(len(r["terms"]) for r in matrix["equalities"]+matrix["inequalities"]),
        "retained_full_Boolean_selector_rows": 4416,
        "PSD_matrix_order": 480, "augmented_selector_moment_PSD_order": 481,
        "projector_core_order": 18,
    }
    specification = {
        "schema": "f0-complete-second-selector-moments-preparation-v1",
        "source_sha256": digest(Path(__file__).read_bytes()), "inputs": INPUTS,
        "scope": {"point_independent": True, "all480_selectors_and68394_edges_retained": True,
                  "every_distinct_selector_pair_represented": True,
                  "Z_diagonal_equals_x": True, "certified_zero_pairs_kept_as_variables": True,
                  "graph_automorphism_assumed": False, "convex_core_group_averaging": True,
                  "component_zero_global_prism_and_F_free_split18_only": True,
                  "second_component_or_alignment_fixed": False,
                  "optimizer_called": False, "semidefinite_solver_called": False,
                  "whole_problem_excluded": False},
        "counts": counts, "matrix": matrix,
        "selector_actions": actions, "selector_orbits": selector_orbits,
        "selector_pair_order": "lexicographic(a,b),0<=a<b<480",
        "pair_orbits": pair_orbits, "pair_to_orbit": pair_orbit,
        "Burnside": burnside, "original_selector_equalities": selector_rows,
        "full_RLT_to_quotient": full_map, "full_RLT_signed_divisor": full_factor,
        "zero_moment_certificates": [zero_pairs[p] for p in sorted(zero_pairs)],
        "zero_pair_orbits": zero_orbits, "full_moment_bound_map_sha256": bound_map_hash.hexdigest(),
        "edge_to_selector_pair_links": edge_links,
        "PSD_requirements": {
            "selector_matrix": "Z positive semidefinite",
            "augmented_selector_matrix": "[[1,x^T],[x,Z]] positive semidefinite",
            "basic_projectors": "27diag(x)-9Y+Z and44diag(x)+11Y-2Z positive semidefinite",
            "Schur_rule": "subtract H_ab*Z_ab with H_ab=u_a^T K_inverse u_b; use Z_aa=x_a",
            "projectors": projectors,
            "noneligible_Y_entries": "identically zero by the complete universal edge domain",
            "PSD_constraints_not_implicitly_linearized": True},
        "controls": {"selector_RLT_positive_control": control, "rook9_projector_Schur_controls": rook},
        "baseline_prefix_sha256": digest(canonical(base["matrix"])),
        "linear_matrix_sha256": digest(canonical(matrix)),
        "new_linear_coefficients_maximum_bits": max(abs(c).bit_length()
            for row in rlt_rows+zero_rows+inequalities for j, c in row["terms"]),
    }
    return specification, time.monotonic()-started


def save_fresh(path, record):
    raw = canonical(record)+b"\n"
    if path.suffix == ".gz":
        raw = gzip.compress(raw, mtime=0)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as handle:
        handle.write(raw)
    return {"path": str(path.resolve().relative_to(ROOT)), "bytes": len(raw), "sha256": digest(raw)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "replay"))
    parser.add_argument("--output-prefix", type=Path, required=True)
    parser.add_argument("--seconds", type=float, default=120)
    args = parser.parse_args()
    assert 0 < args.seconds <= 120
    specification, elapsed = calculate(args.seconds)
    path = Path(str(args.output_prefix)+".json.gz")
    if args.mode == "prepare":
        artifact = save_fresh(path, specification)
        report = {"status": "PASS: complete exact RLT/PSD preparation; no optimizer",
                  "source_sha256": specification["source_sha256"], "artifact": artifact,
                  "canonical_sha256": digest(canonical(specification)),
                  "counts": specification["counts"], "controls": specification["controls"],
                  "linear_matrix_sha256": specification["linear_matrix_sha256"],
                  "new_linear_coefficients_maximum_bits": specification["new_linear_coefficients_maximum_bits"],
                  "projector_inverse_denominators": [x["inverse_denominator"] for x in specification["PSD_requirements"]["projectors"]],
                  "projector_H_numerator_bits": [x["maximum_H_numerator_bits"] for x in specification["PSD_requirements"]["projectors"]],
                  "seconds": elapsed, "optimizer_called": False}
        save_fresh(Path(str(args.output_prefix)+"-report.json"), report)
    else:
        old = json.loads(gzip.decompress(path.read_bytes()))
        assert specification == old
        report = {"status": "PASS: complete cold second-moment preparation replay",
                  "source_sha256": specification["source_sha256"], "artifact_sha256": digest(path.read_bytes()),
                  "canonical_sha256": digest(canonical(specification)), "counts": specification["counts"],
                  "seconds": elapsed, "optimizer_called": False}
        save_fresh(Path(str(args.output_prefix)+"-cold-replay.json"), report)
    print(json.dumps(report, indent=2), flush=True)


if __name__ == "__main__":
    main()
