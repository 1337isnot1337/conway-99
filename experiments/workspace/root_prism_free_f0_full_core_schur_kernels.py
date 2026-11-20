"""Exact full21-core graph-projector Schur kernels; no numerical point.

The plus principal core has rank20. Its compatible third triangle row adds no
further condition beyond two triangle rows. The minus principal core is PD.
The complete kernel is reconstructed from the verified old18 inverse and an
independently checked three-vertex residual block.
"""
import argparse
from fractions import Fraction
import gzip
import hashlib
import json
import math
from pathlib import Path
import time

import root_prism_free_f0_graph_schur_kernels as old

ROOT, LOGS = old.ROOT, old.LOGS
OLD_SOURCE_SHA256 = "5be66e563e53b1efc378c8adbeb39b8ddbf24f4c97077e5d43c728260d9087be"
OLD_CERTIFICATE_SHA256 = "65f1ad0d0015a6eff3d97c676fb0e188f57f9dee00e9245758a28bab2069b40d"
AUDIT_SOURCE_SHA256 = "0988a97703673a2ef2d6f8afb204e06edba14bb9065c0c2361e5ac79840fb6a9"
AUDIT_RECORD_SHA256 = "d8031c629bfb9f5b050c55e218b872aa68a0de08a84abff99da5e029fe572c75"
AUDIT_SOURCE = "root_prism_free_f0_full_core_schur_audit.py"
AUDIT_RECORD = "f0-full-core-schur-independent-audit.json"
MAX_VECTOR_ENTRY = 1024


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode()


def tick(deadline):
    if time.monotonic() >= deadline:
        raise TimeoutError("full-core exact kernel preparation budget")


def load_inputs(deadline=float("inf")):
    assert sha(Path(old.__file__).read_bytes()) == OLD_SOURCE_SHA256
    assert sha(Path(__file__).with_name(AUDIT_SOURCE).read_bytes()) == AUDIT_SOURCE_SHA256
    raw = (LOGS/AUDIT_RECORD).read_bytes()
    assert sha(raw) == AUDIT_RECORD_SHA256
    audit = json.loads(raw)
    assert audit["source_sha256"] == AUDIT_SOURCE_SHA256 and audit["status"].startswith("PASS")
    raw = (LOGS/"f0-graph-schur-kernels01.json.gz").read_bytes()
    assert sha(raw) == OLD_CERTIFICATE_SHA256
    saved = json.loads(gzip.decompress(raw))
    domain = old.load_domain(deadline)
    expected = [old.family_kernel(domain, family, deadline) for family in old.FAMILIES]
    assert saved["kernels"] == expected and saved["source_sha256"] == OLD_SOURCE_SHA256
    return domain, {k["family"]: k for k in expected}, audit


def fiber_data(domain):
    core, triples = domain["core"], domain["triples"]
    assert all(((core[i] >> j) & 1) == int(i != j) for i in range(3) for j in range(3))
    fibers = [[j for j in range(18) if (core[i] >> (j+3)) & 1] for i in range(3)]
    assert all(len(f) == 6 for f in fibers)
    assert sorted(j for f in fibers for j in f) == list(range(18))
    assert all(sum(row[j] for j in f) == 1 for row in domain["adjacency"] for f in fibers)
    eta = [[sum(j in h for j in f) for f in fibers] for h in triples]
    deviation = [[v-1 for v in row] for row in eta]
    assert all(sum(row) == 0 and max(row) <= 1 and min(row) >= -1 for row in deviation)
    for g, whole in zip(domain["actions"], domain["core_actions"]):
        assert sorted(whole[:3]) == [0, 1, 2]
        assert all(deviation[g[a]][whole[i]] == deviation[a][i] for a in range(480) for i in range(3))
    return fibers, eta, deviation


def residual_block(domain, prior, deviation, expected):
    d, e, c = (prior[k] for k in ("global_diagonal", "global_adjacency", "global_constant"))
    den, num = prior["inverse_denominator"], prior["inverse_numerator"]
    core = domain["core"]
    whole = [[d*int(i == j)+e*((core[i] >> j) & 1)+c for j in range(21)] for i in range(21)]
    r = [[whole[i][j+3] for j in range(18)] for i in range(3)]
    rn = [[sum(r[i][a]*num[a][j] for a in range(18)) for j in range(18)] for i in range(3)]
    schur = [[Fraction(whole[i][j])-Fraction(sum(rn[i][a]*r[j][a] for a in range(18)), den)
              for j in range(3)] for i in range(3)]
    assert [[str(v) for v in row] for row in schur] == expected["triangle_schur"]
    q = []
    for a, h in enumerate(domain["triples"]):
        u = [c+e*int(j in h) for j in range(18)]
        value = [Fraction(c)-Fraction(sum(rn[i][j]*u[j] for j in range(18)), den) for i in range(3)]
        closed = ([-3*v for v in deviation[a]] if prior["family"] == "plus" else
                  [-Fraction(77, 41)-Fraction(11, 4)*v for v in deviation[a]])
        assert value == closed
        q.append(value)
    chosen = expected["selected_core_vertices"]
    assert chosen == ([0, 1]+list(range(3, 21)) if prior["family"] == "plus" else list(range(21)))
    selected = [[whole[i][j] for j in chosen] for i in chosen]
    pivots = old.positive_ldl(selected)
    assert [str(Fraction(int(a), int(b))) for a, b in pivots] == expected["selected_core_positive_LDL_pivots"]
    types = sorted(set(map(tuple, deviation)))
    assert len(types) == 7
    controls = 0
    for a in types:
        for b in types:
            dot = sum(x*y for x, y in zip(a, b))
            if prior["family"] == "plus":
                assert schur == [[Fraction(18*int(i == j)-6) for j in range(3)] for i in range(3)]
                assert all(sum(row) == 0 for row in q)
                qa, qb = [-3*x for x in a], [-3*x for x in b]
                direct = sum(x*y for x, y in zip(qa, qb))/Fraction(18)
                assert direct == Fraction(dot, 2)
            else:
                # Exact inverse using the constant and sum-zero subspaces.
                inv = [[Fraction(2, 33)*(int(i == j)-Fraction(1, 3))+Fraction(41, 6930)
                        for j in range(3)] for i in range(3)]
                assert all(sum(schur[i][k]*inv[k][j] for k in range(3)) == int(i == j)
                           for i in range(3) for j in range(3))
                qa = [-Fraction(77, 41)-Fraction(11, 4)*x for x in a]
                qb = [-Fraction(77, 41)-Fraction(11, 4)*x for x in b]
                direct = sum(qa[i]*inv[i][j]*qb[j] for i in range(3) for j in range(3))
                assert direct == Fraction(77, 410)+Fraction(11*dot, 24)
            controls += 1
    return {"triangle_Schur": [[str(v) for v in row] for row in schur],
            "selected_core_vertices": chosen, "selected_core_positive_LDL_pivots": pivots,
            "rank21": 20 if prior["family"] == "plus" else 21,
            "all480_residual_cross_vectors": [[str(v) for v in row] for row in q],
            "exact_profile_product_controls": controls,
            "plus_null_compatibility_checked": prior["family"] == "plus"}


def full_kernel(domain, prior, deviation, expected, deadline):
    family = prior["family"]
    residual = residual_block(domain, prior, deviation, expected)
    constant, dot_weight = ((Fraction(0), Fraction(1, 2)) if family == "plus" else
                            (Fraction(77, 410), Fraction(11, 24)))
    old_den = prior["inverse_denominator"]
    initial_den = math.lcm(old_den, constant.denominator, dot_weight.denominator)
    multiplier = initial_den//old_den
    cc, dd = int(constant*initial_den), int(dot_weight*initial_den)
    diagonal = [multiplier*v-cc-dd*sum(x*x for x in deviation[a])
                for a, v in enumerate(prior["diagonal_x"])]
    off = [multiplier*v-cc-dd*sum(x*y for x, y in zip(deviation[a], deviation[b]))
           for v, (a, b) in zip(prior["off_diagonal_Z"], domain["pairs"])]
    y = multiplier*prior["Y"]
    common = math.gcd(initial_den, *diagonal, *off, y)
    den = initial_den//common
    assert all(v % common == 0 for v in diagonal+off+[y])
    diagonal, off, y = [v//common for v in diagonal], [v//common for v in off], y//common
    assert math.gcd(den, *diagonal, *off, y) == 1 and min(diagonal) > 0
    # Check the rational correction again entry by entry after denominator reduction.
    assert all(Fraction(diagonal[a], den) == Fraction(prior["diagonal_x"][a], old_den)
               -constant-dot_weight*sum(x*x for x in deviation[a]) for a in range(480))
    for p, (a, b) in enumerate(domain["pairs"]):
        if p % 4096 == 0:
            tick(deadline)
        assert Fraction(off[p], den) == Fraction(prior["off_diagonal_Z"][p], old_den) \
            -constant-dot_weight*sum(x*w for x, w in zip(deviation[a], deviation[b]))
    assert Fraction(y, den) == prior["global_adjacency"]
    divisor = math.gcd(*diagonal, *off, y)
    ordered = [diagonal[a] if a == b else off[old.pair_id(a, b)]
               for a in range(480) for b in range(a, 480)]+[y]
    primitive = [v//divisor for v in ordered]
    assert den == expected["coefficient_common_denominator"]
    assert divisor == expected["positive_common_divisor"]
    assert sha(canonical(primitive)) == expected["primitive_kernel_sha256"]
    assert max(map(abs, primitive)) == expected["primitive_kernel_maximum_absolute_coefficient"]
    for g in domain["actions"]:
        tick(deadline)
        assert all(diagonal[g[a]] == diagonal[a] for a in range(480))
        assert all(off[old.pair_id(g[a], g[b])] == off[p] for p, (a, b) in enumerate(domain["pairs"]))
    bounds = {
        "x": max(len(o)*max(abs(diagonal[a]) for a in o) for o in domain["selector_orbits"])*MAX_VECTOR_ENTRY**2,
        "Z": max(2*len(o)*max(abs(off[p]) for p in o) for o in domain["pair_orbits"])*MAX_VECTOR_ENTRY**2,
        "Y": 2*max(map(len, domain["edge_orbits"]))*abs(y)*MAX_VECTOR_ENTRY**2}
    bounds["all"] = max(bounds.values())
    assert bounds["all"] < 2**53
    scale = 1 << max(max(map(abs, diagonal)), max(map(abs, off)), abs(y)).bit_length()
    for value in diagonal+off+[y]:
        assert Fraction(float(value)/scale) == Fraction(value, scale)
    return {"family": family, "Schur_coefficient_denominator": den,
            "common_numerator_divisor": divisor, "denominator_before_reduction": initial_den,
            "positive_reduction_factor": common,
            "diagonal_x": diagonal, "off_diagonal_Z": off, "Y": y,
            "correction_constant": str(constant), "correction_dot_coefficient": str(dot_weight),
            "residual_block_certificate": residual, "primitive_kernel_sha256": sha(canonical(primitive)),
            "independent_direct_inverse_audit_matched": True, "full_entries_checked": 115440,
            "all12_actions_verified": True, "maximum_vector_entry": MAX_VECTOR_ENTRY,
            "raw_quotient_coefficient_bounds": bounds, "bound_bits": bounds["all"].bit_length(),
            "primitive_quotient_coefficient_bounds": {k: v//divisor for k, v in bounds.items()},
            "proposing_matrix_positive_dyad_scale": scale,
            "diagonal_range": [min(diagonal), max(diagonal)], "pair_range": [min(off), max(off)],
            "diagonal_correction_applied": True}


def build(seconds=120):
    started = time.monotonic()
    deadline = started+seconds
    domain, prior, audit = load_inputs(deadline)
    fibers, eta, deviation = fiber_data(domain)
    results = [full_kernel(domain, prior[name], deviation, audit["families"][i], deadline)
               for i, name in enumerate(("plus", "minus"))]
    tick(deadline)
    return {"schema": "f0-full21-core-Schur-kernels-v1", "source_sha256": sha(Path(__file__).read_bytes()),
            "inputs": {"old_source_sha256": OLD_SOURCE_SHA256, "old_certificate_sha256": OLD_CERTIFICATE_SHA256,
                       "independent_audit_source_sha256": AUDIT_SOURCE_SHA256,
                       "independent_audit_record_sha256": AUDIT_RECORD_SHA256},
            "proposal_sha256": old.PROPOSAL_SHA256, "proposal_model_sha256": old.CURRENT_MODEL_SHA256,
            "fibers": fibers, "fiber_counts": eta, "fiber_deviations": deviation,
            "selector_actions_sha256": sha(canonical(domain["actions"])),
            "kept_variables_sha256": sha(canonical(domain["kept"])),
            "kernels": results, "maximum_vector_entry": MAX_VECTOR_ENTRY,
            "scope": {"all480_selectors_retained": True, "fixed_zero_pair_orbits": 389,
                      "component": 0, "split_shell": "18+18", "global_prism_and_F_zero": True,
                      "other_component_and_alignment_free": True, "per_embedding_Schur_before_averaging": True,
                      "plus_uses_positive20core_with_compatible21st_row": True,
                      "minus_uses_positive21core": True, "no_graph_automorphism_assumption": True,
                      "proposing_point_feasibility_assumed": False, "optimizer_calls": 0,
                      "point_contractions": 0, "eigendecompositions": 0}}


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
    started = time.monotonic()
    result = build(args.seconds)
    raw = canonical(result)
    if args.mode == "prepare":
        assert not args.certificate.exists()
        args.certificate.write_bytes(gzip.compress(raw, mtime=0))
    else:
        assert canonical(json.loads(gzip.decompress(args.certificate.read_bytes()))) == raw
    report = {"status": "PASS: full21-core Schur kernels "+("prepared" if args.mode == "prepare" else "cold replayed"),
              "source_sha256": result["source_sha256"], "certificate_file_sha256": sha(args.certificate.read_bytes()),
              "certificate_raw_sha256": sha(raw), "scope": result["scope"],
              "families": [{k: v for k, v in r.items()
                            if k not in ("diagonal_x", "off_diagonal_Z", "residual_block_certificate")}
                           for r in result["kernels"]], "seconds": time.monotonic()-started}
    save_new(args.report, report)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
