"""Exact full480 graph-projector Schur kernels; point-independent preparation.

No optimizer, numerical matrix contraction, or eigendecomposition is used.
"""
import argparse
from fractions import Fraction
import gzip
import hashlib
import json
import math
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[2]
LOGS = ROOT/"experiments/logs/root-prism-free"
INPUTS = {
    "f0-boolean-fractional-model.json.gz": "703206929c9c85a40ac4ddcbfb1708c716c288482cf50c77a32249404e35b782",
    "f0-second-moments-preparation02.json.gz": "404d91da35c798ba248887c22a7500957947e24b71d5197dc44432460e6d219e",
    "f0-second-moments-reduced-model.json.gz": "73a50b431ac69ad57e10cff9aabe5c0b7d69ee075e95710b461f62b33fe2bbcf",
    "f0-selector-psd-model01.json.gz": "3302546078e2277c8ce30d032110bb527c6a986a74f76fc1f78451bf4da4b804",
}
CURRENT_MODEL_SHA256 = "d098a4b84405823aa38e9d2def7b675c6166507f7350937f1dc0f65af7274dcd"
PROPOSAL_SHA256 = "ca7ebcb40ea0b02054a79f6f6acb83f1f227325f7669b0b9336e3beed6fce5bf"
N, PAIR_OFFSET, OLD_VARIABLES, MAX_VECTOR_ENTRY = 480, 5847, 15589, 1024
FAMILIES = (("plus", 27, -9, 1, 4860), ("minus", 44, 11, -2, 3822676))


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode()


def tick(deadline):
    if time.monotonic() >= deadline:
        raise TimeoutError("exact preparation time budget")


def read_models():
    out = []
    for filename, expected in INPUTS.items():
        raw = (LOGS/filename).read_bytes()
        assert sha(raw) == expected
        out.append(json.loads(gzip.decompress(raw)))
    assert sha(canonical(out[3])) == CURRENT_MODEL_SHA256
    assert out[3]["matrix"]["variables"] == 15200
    assert out[3]["matrix"]["equalities"] == out[2]["matrix"]["equalities"]
    assert out[3]["matrix"]["inequalities"][:15719] == out[2]["matrix"]["inequalities"]
    return out


def pair_id(a, b):
    assert a != b
    if a > b:
        a, b = b, a
    return a*(2*N-a-1)//2+b-a-1


def action_on_core(core, triples, actions):
    supports = [frozenset(a for a, h in enumerate(triples) if i in h) for i in range(18)]
    assert len(set(supports)) == 18
    reverse = {s: i for i, s in enumerate(supports)}
    fibers = [frozenset(j for j in range(18) if core[i] & (1 << (j+3))) for i in range(3)]
    assert len(set(fibers)) == 3 and all(len(f) == 6 for f in fibers)
    fiber_reverse = {f: i for i, f in enumerate(fibers)}
    result = []
    for g in actions:
        h = [reverse[frozenset(g[a] for a in support)] for support in supports]
        assert sorted(h) == list(range(18))
        t = [fiber_reverse[frozenset(h[j] for j in f)] for f in fibers]
        whole = t+[j+3 for j in h]
        assert sorted(whole) == list(range(21))
        assert all(((core[i] >> j) & 1) == ((core[whole[i]] >> whole[j]) & 1)
                   for i in range(21) for j in range(21))
        assert all(sorted(h[i] for i in triples[a]) == triples[g[a]] for a in range(N))
        result.append(whole)
    return result


def load_domain(deadline=float("inf")):
    baseline, full, reduced, current = read_models()
    data = baseline["validation"]
    core, triples, edges = data["core"], data["triples"], data["edges"]
    assert len(core) == 21 and len(triples) == 480 and triples == sorted(triples)
    assert len({tuple(h) for h in triples}) == 480 and all(len(set(h)) == 3 for h in triples)
    assert all(not (core[i] >> i) & 1 for i in range(21))
    assert all(((core[i] >> j) & 1) == ((core[j] >> i) & 1) for i in range(21) for j in range(21))
    adjacency = [[(core[i+3] >> (j+3)) & 1 for j in range(18)] for i in range(18)]
    assert all(sum(row) == 3 for row in adjacency)
    targets = [[2-int(i in h)-sum(adjacency[i][j] for j in h) for i in range(18)] for h in triples]
    assert targets == data["targets"] and all(sum(q) == 24 and min(q) >= 0 for q in targets)
    pairs = [(a, b) for a in range(N) for b in range(a+1, N)]
    assert len(pairs) == 114960
    sets = list(map(set, triples))
    recovered = [[a, b] for a, b in pairs
                 if len(sets[a]&sets[b]) <= 1
                 and all(targets[a][i] > 0 for i in triples[b])
                 and all(targets[b][i] > 0 for i in triples[a])]
    assert recovered == edges and len(edges) == 68394
    selector_orbits, edge_orbits = data["selector_orbits"], data["edge_orbits"]
    pair_orbits = full["pair_orbits"]
    assert selector_orbits == full["selector_orbits"]
    assert (len(selector_orbits), len(edge_orbits), len(pair_orbits)) == (42, 5805, 9742)
    def orbit_map(orbits, size):
        answer = [-1]*size
        for orbit, members in enumerate(orbits):
            assert members and members == sorted(set(members)) and len(members) <= 12
            for a in members:
                assert answer[a] == -1
                answer[a] = orbit
        assert min(answer) >= 0
        return answer
    xmap, emap, pmap = (orbit_map(selector_orbits, N), orbit_map(edge_orbits, len(edges)),
                        orbit_map(pair_orbits, len(pairs)))
    assert pmap == full["pair_to_orbit"]
    actions = full["selector_actions"]
    group = set(map(tuple, actions))
    assert len(group) == len(actions) == 12 and tuple(range(N)) in group
    edge_index = {tuple(e): i for i, e in enumerate(edges)}
    for g in actions:
        tick(deadline)
        assert sorted(g) == list(range(N))
        assert all(tuple(g[h[a]] for a in range(N)) in group for h in actions)
        assert all(xmap[g[a]] == xmap[a] for a in range(N))
        assert all(pmap[pair_id(g[a], g[b])] == pmap[p] for p, (a, b) in enumerate(pairs))
        assert all(emap[edge_index[tuple(sorted((g[a], g[b])))]] == emap[e]
                   for e, (a, b) in enumerate(edges))
    for orbit in selector_orbits:
        assert {g[orbit[0]] for g in actions} == set(orbit)
    for orbit in pair_orbits:
        a, b = pairs[orbit[0]]
        assert {pair_id(g[a], g[b]) for g in actions} == set(orbit)
    for orbit in edge_orbits:
        a, b = edges[orbit[0]]
        assert {edge_index[tuple(sorted((g[a], g[b])))] for g in actions} == set(orbit)
    core_actions = action_on_core(core, triples, actions)
    fixed = reduced["fixed_zero_original_variables"]
    assert len(fixed) == 389
    for variable, row in fixed:
        assert PAIR_OFFSET <= variable < OLD_VARIABLES
        assert full["matrix"]["equalities"][row]["terms"] == [[variable, 1]]
        assert full["matrix"]["equalities"][row]["rhs"] == 0
    kept = reduced["kept_original_variables"]
    assert kept == sorted(set(range(OLD_VARIABLES))-{j for j, r in fixed})
    assert len(kept) == 15200
    return {"baseline": baseline, "full": full, "reduced": reduced,
            "core": core, "adjacency": adjacency, "triples": triples,
            "pairs": pairs, "edges": edges, "xmap": xmap, "emap": emap, "pmap": pmap,
            "selector_orbits": selector_orbits, "edge_orbits": edge_orbits, "pair_orbits": pair_orbits,
            "actions": actions, "core_actions": core_actions, "kept": kept,
            "reverse": {j: i for i, j in enumerate(kept)}, "fixed": {j for j, r in fixed}}


def positive_ldl(matrix):
    n = len(matrix)
    work = [[Fraction(x) for x in row] for row in matrix]
    assert all(work[i][j] == work[j][i] for i in range(n) for j in range(n))
    pivots = []
    for k in range(n):
        pivot = work[k][k]
        assert pivot > 0
        pivots.append([str(pivot.numerator), str(pivot.denominator)])
        for i in range(k+1, n):
            for j in range(i, n):
                work[i][j] -= work[i][k]*work[k][j]/pivot
                work[j][i] = work[i][j]
    return pivots


def family_kernel(domain, family, deadline):
    key, d, e, c, denominator = family
    prior = domain["full"]["PSD_requirements"]["projectors"][0 if key == "plus" else 1]
    k = [[d*int(i == j)+e*domain["adjacency"][i][j]+c for j in range(18)] for i in range(18)]
    assert k == prior["core_matrix"]
    pivots = positive_ldl(k)
    assert pivots == prior["positive_LDL_pivots"]
    assert denominator == int(prior["inverse_denominator"])
    numerator = [[int(v) for v in row] for row in prior["inverse_numerator"]]
    assert len(numerator) == 18 and all(len(row) == 18 for row in numerator)
    assert all(numerator[i][j] == numerator[j][i] for i in range(18) for j in range(18))
    assert all(sum(k[i][a]*numerator[a][j] for a in range(18)) == denominator*int(i == j)
               for i in range(18) for j in range(18))
    cross = [[c+e*int(i in h) for i in range(18)] for h in domain["triples"]]
    multiplied = [[sum(numerator[i][j]*u[j] for j in range(18)) for i in range(18)] for u in cross]
    hdiag = [sum(cross[a][i]*multiplied[a][i] for i in range(18)) for a in range(N)]
    hoff = []
    for p, (a, b) in enumerate(domain["pairs"]):
        if p % 4096 == 0:
            tick(deadline)
        value = sum(cross[a][i]*multiplied[b][i] for i in range(18))
        assert value == sum(cross[b][i]*multiplied[a][i] for i in range(18))
        hoff.append(value)
    assert all(hdiag[a] == int(prior["H_diagonal_by_selector_orbit"][domain["xmap"][a]])
               for a in range(N))
    assert all(value == int(prior["H_off_diagonal_by_pair_orbit"][domain["pmap"][p]])
               for p, value in enumerate(hoff))
    diagonal = [(d+c)*denominator-h for h in hdiag]
    off = [c*denominator-h for h in hoff]
    y = e*denominator
    assert min(diagonal) > 0
    saved = prior["Schur_PSD"]
    assert all(diagonal[a] == int(saved["diagonal_x_coefficients"][domain["xmap"][a]]) for a in range(N))
    assert all(off[p] == int(saved["off_diagonal_Z_coefficients"][domain["pmap"][p]])
               for p in range(len(off)))
    assert y == int(saved["Y_coefficient"])
    for g in domain["actions"]:
        tick(deadline)
        assert all(diagonal[g[a]] == diagonal[a] for a in range(N))
        assert all(off[pair_id(g[a], g[b])] == off[p] for p, (a, b) in enumerate(domain["pairs"]))
    diagonal_bound = max(len(members)*max(abs(diagonal[a]) for a in members)
                         for members in domain["selector_orbits"])*MAX_VECTOR_ENTRY**2
    pair_bound = max(2*len(members)*max(abs(off[p]) for p in members)
                     for members in domain["pair_orbits"])*MAX_VECTOR_ENTRY**2
    edge_bound = 2*max(map(len, domain["edge_orbits"]))*abs(y)*MAX_VECTOR_ENTRY**2
    bound = max(diagonal_bound, pair_bound, edge_bound)
    assert bound < 2**53
    matrix_scale = 1 << max(max(map(abs, diagonal)), max(map(abs, off)), abs(y)).bit_length()
    for value in diagonal+off+[y]:
        assert Fraction(float(value)/matrix_scale) == Fraction(value, matrix_scale)
    return {
        "family": key, "global_projector": prior["name"],
        "global_diagonal": d, "global_adjacency": e, "global_constant": c,
        "core_matrix": k, "positive_LDL_pivots": pivots,
        "inverse_denominator": denominator, "inverse_numerator": numerator,
        "cross_vector_rule": {"constant": c, "signature_coefficient": e},
        "diagonal_x": diagonal, "off_diagonal_Z": off, "Y": y,
        "full_H_diagonal_sha256": sha(canonical(hdiag)),
        "full_H_off_diagonal_sha256": sha(canonical(hoff)),
        "full_H_entries_verified": 115440,
        "full_diagonal_range": [min(diagonal), max(diagonal)],
        "full_pair_coefficient_range": [min(off), max(off)],
        "raw_quotient_coefficient_bounds": {"x": diagonal_bound, "Z": pair_bound, "Y": edge_bound, "all": bound},
        "maximum_vector_entry": MAX_VECTOR_ENTRY,
        "bound_bits": bound.bit_length(),
        "proposing_matrix_positive_dyad_scale": matrix_scale,
        "all12_actions_verified": True, "all_orbit_values_verified": True,
        "diagonal_rule": "(d+c)*D-H_aa; Z_aa=x_a and Y_aa=0",
        "off_diagonal_rule": "(c*D-H_ab)*Z_ab + e*D*Y_ab",
    }


def build(seconds=120):
    started = time.monotonic()
    deadline = started+seconds
    domain = load_domain(deadline)
    kernels = [family_kernel(domain, family, deadline) for family in FAMILIES]
    tick(deadline)
    return {"schema": "f0-full480-graph-projector-Schur-kernels-v1",
            "source_sha256": sha(Path(__file__).read_bytes()), "inputs": INPUTS,
            "proposal_model_sha256": CURRENT_MODEL_SHA256, "proposal_sha256": PROPOSAL_SHA256,
            "domain": {"selectors": N, "eligible_edges": len(domain["edges"]), "unordered_pairs": len(domain["pairs"]),
                       "selector_orbits": 42, "edge_orbits": 5805, "pair_orbits": 9742,
                       "fixed_zero_pair_orbits": 389, "core_order": 18,
                       "core_sha256": sha(canonical(domain["core"])),
                       "triples_sha256": sha(canonical(domain["triples"])),
                       "edges_sha256": sha(canonical(domain["edges"])),
                       "selector_actions_sha256": sha(canonical(domain["actions"])),
                       "reconstructed21_core_actions": domain["core_actions"],
                       "original_variable_order_sha256": sha(canonical(domain["kept"]))},
            "kernels": kernels, "maximum_vector_entry": MAX_VECTOR_ENTRY,
            "scope": {"all480_selectors_retained": True, "other_component_and_alignment_free": True,
                      "component": 0, "split_shell": "18+18", "global_prism_and_F_zero": True,
                      "per_embedding_Schur_before_averaging": True, "product_Z_not_xa_xb": True,
                      "no_rank_constraint_after_averaging": True, "no_graph_symmetry_assumption": True,
                      "proposing_point_feasibility_assumed": False,
                      "optimizer_calls": 0, "eigendecompositions": 0}}


def save_new(path, value):
    assert not path.exists()
    path.write_text(json.dumps(value, indent=2)+"\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("prepare", "replay"))
    parser.add_argument("--certificate", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--seconds", type=float, default=120)
    args = parser.parse_args()
    assert 0 < args.seconds <= 120
    started = time.monotonic()
    model = build(args.seconds)
    raw = canonical(model)
    if args.mode == "prepare":
        assert not args.certificate.exists()
        args.certificate.write_bytes(gzip.compress(raw, mtime=0))
    else:
        prior = json.loads(gzip.decompress(args.certificate.read_bytes()))
        assert canonical(prior) == raw
    report = {"status": "PASS: exact full480 Schur kernels "+("prepared" if args.mode == "prepare" else "cold rebuilt"),
              "source_sha256": sha(Path(__file__).read_bytes()),
              "certificate_file_sha256": sha(args.certificate.read_bytes()), "certificate_raw_sha256": sha(raw),
              "certificate_bytes": args.certificate.stat().st_size,
              "domain": model["domain"], "families": [
                  {k: f[k] for k in ("family", "inverse_denominator", "full_H_entries_verified",
                                     "full_diagonal_range", "full_pair_coefficient_range",
                                     "raw_quotient_coefficient_bounds", "bound_bits", "proposing_matrix_positive_dyad_scale")}
                  for f in model["kernels"]],
              "scope": model["scope"], "seconds": time.monotonic()-started}
    save_new(args.report, report)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()

