"""Exact modulo-three elimination with explicit degree and mixed equations.

The degree equation must be present in characteristic three.  All original
eligible edge variables remain separate.  Two disjoint bit planes encode
coefficients one and two.  New selector congruences retain full witnesses.
"""
import argparse
import importlib.util
from itertools import product
import json
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[2]
HELPER = ("experiments/workspace/root_prism_free_f0_shared_mod2_projection.py",
          "a548fe26b54a559909bece50df984e0755d9321adc7e8a41d0b6e836c8b34fd5")
spec = importlib.util.spec_from_file_location("shared_mod2_domain_only", ROOT / HELPER[0])
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)
assert helper.sha((ROOT / HELPER[0]).read_bytes()) == HELPER[1]
ZERO = (0, 0)
SECONDS = 60


def add(a, b):
    a1, a2 = a
    b1, b2 = b
    return ((a1 & ~(b1 | b2)) | (b1 & ~(a1 | a2)) | (a2 & b2),
            (a2 & ~(b1 | b2)) | (b2 & ~(a1 | a2)) | (a1 & b1))


def negative(a):
    return a[1], a[0]


def subtract_multiple(a, b, coefficient):
    assert coefficient in (1, 2)
    return add(a, negative(b) if coefficient == 1 else b)


def terms(value):
    assert not (value[0] & value[1])
    return sorted([[i, c] for c, bits in enumerate(value, 1) for i in helper.bit_positions(bits)])


def encode(items):
    result = [0, 0]
    for i, value in items:
        if value % 3:
            result[value % 3 - 1] |= 1 << i
    return tuple(result)


def reduce_small(value, basis):
    witness = ZERO
    for pivot in sorted(basis):
        bit = 1 << pivot
        coefficient = 1 if value[0] & bit else 2 if value[1] & bit else 0
        if coefficient:
            vector, proof = basis[pivot]
            value = subtract_multiple(value, vector, coefficient)
            witness = add(witness, proof if coefficient == 1 else negative(proof))
    return value, witness


def basis_from(vectors):
    basis = {}
    for i, original in enumerate(vectors):
        value, subtracted = reduce_small(original, basis)
        proof = add((1 << i, 0), negative(subtracted))
        if value != ZERO:
            pivot = ((value[0] | value[1]) & -(value[0] | value[1])).bit_length() - 1
            if value[1] >> pivot & 1:
                value, proof = negative(value), negative(proof)
            basis[pivot] = (value, proof)
    return basis


def controls():
    vectors = list(product(range(3), repeat=4))
    for a in vectors:
        for b in vectors:
            x = encode(enumerate(a))
            y = encode(enumerate(b))
            assert terms(add(x, y)) == [[i, (u + v) % 3] for i, (u, v) in enumerate(zip(a, b)) if (u + v) % 3]
            assert terms(add(x, negative(y))) == [[i, (u - v) % 3] for i, (u, v) in enumerate(zip(a, b)) if (u - v) % 3]
    example = [encode([(0, 1), (2, 2)]), encode([(1, 2), (2, 1)]), encode([(0, 2), (1, 1), (2, 0)])]
    b = basis_from(example)
    assert len(b) == 2
    for original in example:
        remainder, witness = reduce_small(original, b)
        assert remainder == ZERO
        restored = ZERO
        for i, c in terms(witness):
            restored = add(restored, example[i] if c == 1 else negative(example[i]))
        assert restored == original
    return {"four_coordinate_addition_controls": 6561, "four_coordinate_subtraction_controls": 6561,
            "dependent_row_basis_controls": 3, "optimizer_calls": 0}


def direct_check(cert, triples, targets, edges, gram):
    multipliers = cert["original_row_multipliers"]
    assert multipliers == sorted(multipliers) and len({j for j, _ in multipliers}) == len(multipliers)
    degree, site = [0] * 480, [[0] * 18 for _ in range(480)]
    for row, c in multipliers:
        assert 0 <= row < 9120 and c in (1, 2)
        a, i = divmod(row, 19)
        if i == 0:
            degree[a] = c
        else:
            site[a][i - 1] = c
    for a, b in edges:
        assert (degree[a] + degree[b] + sum(site[a][i] for i in triples[b])
                + sum(site[b][i] for i in triples[a])) % 3 == 0
    rhs = [(8 * degree[a] + sum(c * q for c, q in zip(site[a], targets[a]))) % 3 for a in range(480)] + [0]
    assert [[i, c] for i, c in enumerate(rhs) if c] == cert["selector_congruence"]
    for row_id, coefficient in cert["gram_reduction_multipliers"]:
        row = gram[row_id]
        for a in row["support"]:
            rhs[a] = (rhs[a] - coefficient) % 3
        rhs[480] = (rhs[480] + coefficient * row["rhs"]) % 3
    assert [[i, c] for i, c in enumerate(rhs) if c] == cert["remainder_mod_original_gram"]
    return True


def run(directory):
    started = time.monotonic()
    directory.mkdir(parents=True, exist_ok=False)
    control = controls()
    triples, targets, edges, gram = helper.load_domain()
    rows = [0] * 9120
    for e, (a, b) in enumerate(edges):
        bit = 1 << e
        rows[19 * a] |= bit
        rows[19 * b] |= bit
        for i in triples[b]:
            rows[19 * a + 1 + i] |= bit
        for i in triples[a]:
            rows[19 * b + 1 + i] |= bit
    gram_vectors = [encode([(a, 1) for a in r["support"]] + [(480, -r["rhs"])]) for r in gram]
    gbasis = basis_from(gram_vectors)
    assert 480 not in gbasis
    basis, new_basis, certificates = {}, {}, []
    processed = additions = dependencies = zero_consequences = nonzero_consequences = 0
    halted = False
    for row_id, initial in enumerate(rows):
        if time.monotonic() - started >= SECONDS:
            halted = True
            break
        value, proof = (initial, 0), (1 << row_id, 0)
        a, i = divmod(row_id, 19)
        rhs = encode([(a, 8 if i == 0 else targets[a][i - 1])])
        while value != ZERO:
            if additions % 4096 == 0 and time.monotonic() - started >= SECONDS:
                halted = True
                break
            union = value[0] | value[1]
            pivot = (union & -union).bit_length() - 1
            coefficient = 1 if value[0] >> pivot & 1 else 2
            if pivot not in basis:
                if coefficient == 2:
                    value, proof, rhs = negative(value), negative(proof), negative(rhs)
                basis[pivot] = (value, proof, rhs)
                break
            vector, old_proof, old_rhs = basis[pivot]
            value = subtract_multiple(value, vector, coefficient)
            proof = subtract_multiple(proof, old_proof, coefficient)
            rhs = subtract_multiple(rhs, old_rhs, coefficient)
            additions += 1
        if halted:
            break
        processed += 1
        if value != ZERO:
            continue
        dependencies += 1
        if rhs == ZERO:
            zero_consequences += 1
            continue
        nonzero_consequences += 1
        remainder, gram_proof = reduce_small(rhs, gbasis)
        residual, _ = reduce_small(remainder, new_basis)
        if residual == ZERO:
            continue
        union = residual[0] | residual[1]
        pivot = (union & -union).bit_length() - 1
        new_basis[pivot] = (negative(residual) if residual[1] >> pivot & 1 else residual, ZERO)
        cert = {"original_row_multipliers": terms(proof), "selector_congruence": terms(rhs),
                "gram_reduction_multipliers": terms(gram_proof), "remainder_mod_original_gram": terms(remainder)}
        assert direct_check(cert, triples, targets, edges, gram)
        certificates.append(cert)
    archive = helper.write(directory / "certificates.json.gz", {"modulus": 3, "domain": helper.DOMAIN,
        "row_order": "480 anchors, each degree followed by18 mixed rows", "original_gram": gram,
        "certificates": certificates, "all_retained_identities_directly_checked": True})
    report = {"status": "PARTIAL_EXACT_MOD3_SHARED_PROJECTION" if halted else "COMPLETE_EXACT_MOD3_SHARED_PROJECTION",
        "source_sha256": helper.sha(Path(__file__).read_bytes()), "helper_source": HELPER, "domain": helper.DOMAIN,
        "modulus": 3, "selectors": 480, "edges": len(edges), "mixed_rows": 8640, "explicit_degree_rows": 480,
        "initial_nonempty_edge_rows": sum(bool(r) for r in rows), "processed_rows": processed,
        "edge_pivots_found": len(basis), "dependencies_processed": dependencies,
        "zero_selector_consequences": zero_consequences, "nonzero_selector_consequences": nonzero_consequences,
        "original_gram_rank": len(gbasis), "new_independent_consequences": len(certificates),
        "field_row_additions": additions, "controls": control, "certificates": archive,
        "optimizer_calls": 0, "native_imports": 0, "selected_incidence_fixed": False,
        "graph_symmetry_assumed": False, "whole_component_excluded": False,
        "deadline_seconds": SECONDS, "seconds": time.monotonic() - started}
    helper.write(directory / "report.json", report)
    return report


if __name__ == "__main__":
    assert __debug__
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.directory.resolve()), sort_keys=True))
