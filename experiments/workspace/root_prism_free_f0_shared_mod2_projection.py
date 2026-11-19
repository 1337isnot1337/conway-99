"""Exact binary selector consequences of all original shared mixed rows.

Every exterior edge remains a separate variable.  No orbit averaging or
graph symmetry is imposed.  Saved nonzero consequences carry original-row
multipliers; direct replay checks every eligible edge coefficient.
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[2]
DOMAIN = ("experiments/logs/root-prism-free/f0-exterior-row-domains02.json.gz",
          "665563b75fa6fc23caa9a002621cc4047809af28543b52b5c2a7ffa592d05dd4")
GRAM_SOURCE = ("experiments/workspace/root_prism_free_f0_direct_literal_model.py",
               "b500336db29820777afb59076384a48382fa54453fce5b232a072719893cea40")
SECONDS = 60


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read(binding):
    path, expected = binding
    raw = (ROOT / path).read_bytes()
    assert sha(raw) == expected
    return json.loads(gzip.decompress(raw))


def write(path, value):
    raw = canonical(value) + b"\n"
    with path.open("xb") as stream:
        stream.write(gzip.compress(raw, mtime=0) if path.suffix == ".gz" else raw)
    return {"path": str(path.relative_to(ROOT)), "sha256": sha(path.read_bytes()), "raw_sha256": sha(raw)}


def bit_positions(value):
    while value:
        bit = value & -value
        yield bit.bit_length() - 1
        value ^= bit


def load_domain():
    data = read(DOMAIN)
    core, triples = data["component_core_rows"], data["signature_domain"]
    assert len(core) == 21 and len(triples) == len(set(map(tuple, triples))) == 480
    assert all(h == sorted(set(h)) and len(h) == 3 for h in triples)
    assert all(not (r >> i & 1) for i, r in enumerate(core))
    assert all((core[i] >> j & 1) == (core[j] >> i & 1) for i in range(21) for j in range(21))
    targets = [[2 - int(i in h) - sum(core[i + 3] >> (j + 3) & 1 for j in h)
                for i in range(18)] for h in triples]
    assert targets == data["row_targets"] and all(sum(q) == 24 and min(q) >= 0 for q in targets)
    masks = [sum(1 << i for i in h) for h in triples]
    edges = []
    neighbors = [[] for _ in triples]
    for a in range(480):
        for b in range(a + 1, 480):
            if ((masks[a] & masks[b]).bit_count() <= 1
                and all(targets[a][i] > 0 for i in triples[b])
                and all(targets[b][i] > 0 for i in triples[a])):
                edges.append([a, b])
                neighbors[a].append(b)
                neighbors[b].append(a)
    assert neighbors == data["possible_neighbor_signature_ids"] and len(edges) == 68394
    gram = []
    for i in range(18):
        for j in range(i, 18):
            quota = 12 * int(i == j) + 2 - (core[i + 3] & core[j + 3]).bit_count() - (core[i + 3] >> (j + 3) & 1)
            support = [a for a, h in enumerate(triples) if i in h and j in h]
            gram.append({"core_pair": [i, j], "support": support, "rhs": quota})
    gram.append({"core_pair": None, "support": list(range(480)), "rhs": 60})
    assert len(gram) == 172
    return triples, targets, edges, gram


def small_basis(vectors):
    basis = {}
    for original_id, value in enumerate(vectors):
        witness = 1 << original_id
        while value:
            pivot = (value & -value).bit_length() - 1
            if pivot not in basis:
                basis[pivot] = (value, witness)
                break
            v, w = basis[pivot]
            value ^= v
            witness ^= w
    return basis


def reduce_small(value, basis):
    witness = 0
    for pivot in sorted(basis):
        if value >> pivot & 1:
            v, w = basis[pivot]
            value ^= v
            witness ^= w
    return value, witness


def direct_check(certificate, triples, targets, edges, gram):
    multipliers = certificate["mixed_row_ids"]
    assert multipliers == sorted(set(multipliers)) and all(0 <= j < 8640 for j in multipliers)
    site_masks = [0] * 480
    rhs = 0
    for row in multipliers:
        a, i = divmod(row, 18)
        site_masks[a] ^= 1 << i
        if targets[a][i] & 1:
            rhs ^= 1 << a
    hm = [sum(1 << i for i in h) for h in triples]
    assert all(((site_masks[a] & hm[b]).bit_count() + (site_masks[b] & hm[a]).bit_count()) % 2 == 0
               for a, b in edges)
    assert list(bit_positions(rhs)) == certificate["selector_support"]
    assert certificate["selector_rhs"] == 0
    for row_id in certificate["gram_reduction_row_ids"]:
        row = gram[row_id]
        rhs ^= sum(1 << a for a in row["support"]) | ((row["rhs"] & 1) << 480)
    assert list(bit_positions(rhs)) == certificate["remainder_mod_original_gram"]
    return True


def run(directory):
    started = time.monotonic()
    directory.mkdir(parents=True, exist_ok=False)
    assert sha((ROOT / GRAM_SOURCE[0]).read_bytes()) == GRAM_SOURCE[1]
    triples, targets, edges, gram = load_domain()
    rows = [0] * 8640
    for e, (a, b) in enumerate(edges):
        bit = 1 << e
        for i in triples[b]:
            rows[18 * a + i] |= bit
        for i in triples[a]:
            rows[18 * b + i] |= bit
    gram_vectors = [sum(1 << a for a in row["support"]) | ((row["rhs"] & 1) << 480) for row in gram]
    gbasis = small_basis(gram_vectors)
    assert 480 not in gbasis, "original Gram system would have a parity contradiction"
    basis, new_basis, certificates = {}, {}, []
    dependencies, zero_consequences, nonzero_consequences = 0, 0, 0
    processed, additions, halted, checked_certificates = 0, 0, False, 0
    for row_id, initial in enumerate(rows):
        if time.monotonic() - started >= SECONDS:
            halted = True
            break
        value, proof = initial, 1 << row_id
        a, i = divmod(row_id, 18)
        rhs = (1 << a) if targets[a][i] & 1 else 0
        while value:
            if additions % 4096 == 0 and time.monotonic() - started >= SECONDS:
                halted = True
                break
            pivot = (value & -value).bit_length() - 1
            if pivot not in basis:
                basis[pivot] = (value, proof, rhs)
                break
            v, p, r = basis[pivot]
            value ^= v
            proof ^= p
            rhs ^= r
            additions += 1
        if halted:
            break
        processed += 1
        if value:
            continue
        dependencies += 1
        if not rhs:
            zero_consequences += 1
            continue
        nonzero_consequences += 1
        remainder, gram_witness = reduce_small(rhs, gbasis)
        residual, _ = reduce_small(remainder, new_basis)
        if not residual:
            continue
        pivot = (residual & -residual).bit_length() - 1
        new_basis[pivot] = (residual, 1 << len(certificates))
        cert = {"mixed_row_ids": list(bit_positions(proof)),
                "selector_support": list(bit_positions(rhs)), "selector_rhs": 0,
                "gram_reduction_row_ids": list(bit_positions(gram_witness)),
                "remainder_mod_original_gram": list(bit_positions(remainder))}
        assert direct_check(cert, triples, targets, edges, gram)
        certificates.append(cert)
        checked_certificates += 1
    all_certificates_checked = checked_certificates == len(certificates)
    artifact = write(directory / "certificates.json.gz", {"domain": DOMAIN, "original_gram": gram,
        "certificates": certificates, "all_edge_coefficients_even": all_certificates_checked,
        "independent_mod_original_gram": len(new_basis), "entire_current_constraint_independence_claimed": False})
    report = {"status": "PARTIAL_EXACT_MOD2_SHARED_PROJECTION" if halted else "COMPLETE_EXACT_MOD2_SHARED_PROJECTION",
        "source_sha256": sha(Path(__file__).read_bytes()), "domain": DOMAIN, "gram_source": GRAM_SOURCE,
        "selected_incidence_fixed": False, "graph_symmetry_assumed": False,
        "selectors": 480, "edges": len(edges), "mixed_rows": 8640,
        "initial_nonempty_rows": sum(bool(v) for v in rows), "processed_rows": processed,
        "edge_pivots_found": len(basis), "dependencies_processed": dependencies,
        "zero_selector_consequences": zero_consequences, "nonzero_selector_consequences": nonzero_consequences,
        "original_gram_parity_rank": len(gbasis), "new_independent_consequences": len(certificates),
        "xor_additions": additions, "certificates": artifact,
        "all_retained_identities_directly_checked_on68394_edges": all_certificates_checked,
        "optimizer_calls": 0, "native_imports": 0, "whole_component_excluded": False,
        "deadline_seconds": SECONDS, "seconds": time.monotonic() - started}
    write(directory / "report.json", report)
    return report


if __name__ == "__main__":
    assert __debug__
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.directory.resolve()), sort_keys=True))
