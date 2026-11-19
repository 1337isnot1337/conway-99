"""Cold check of the explicit rational-kernel witnesses, no producer import.

The saved sparse vectors are checked against their skew-matrix forms.
That form proves integer edge annihilation for every pair at once. The
small saved independence minor and each Gram RHS identity are checked
directly; the full modulo-three elimination is not repeated.
"""
import gzip
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
PRODUCER = ("experiments/workspace/root_prism_free_f0_shared_rational_kernel.py", "f017f6cc2b3674b21b9fb519e585c8d61495ae4db715fe40bd2715f38d1421b5")
CERTIFICATE = ("experiments/logs/root-prism-free/f0-shared-rational-kernel01.json.gz", "e8a2d8303fe3ee67b33fbb05407b3310c36febef7e867c89acdd264b3fde0f8c")
DOMAIN = ("experiments/logs/root-prism-free/f0-exterior-row-domains02.json.gz", "665563b75fa6fc23caa9a002621cc4047809af28543b52b5c2a7ffa592d05dd4")


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read(binding):
    name, expected = binding
    raw = (ROOT / name).read_bytes()
    assert sha(raw) == expected
    return json.loads(gzip.decompress(raw) if name.endswith(".gz") else raw)


def check():
    started = time.monotonic()
    cert, domain = read(CERTIFICATE), read(DOMAIN)
    assert sha((ROOT / PRODUCER[0]).read_bytes()) == PRODUCER[1] == cert["source_sha256"]
    assert cert["status"] == "EXACT_RATIONAL_MIXED_RANK_AND_COMPLETE_KERNEL_CERTIFICATE"
    assert cert["inputs"]["domain"] == list(DOMAIN)
    lower = read(cert["inputs"]["mod3_independent"])
    assert lower["status"] == "PASS_INDEPENDENT_COMPLETE_AUGMENTED_RANK_NO_NEW_SELECTOR_CONGRUENCES"
    assert lower["modulus"] == 3 and lower["edge_variables"] == 68394
    assert lower["original_rows_processed"] == 9120 and lower["edge_rank"] == 7731
    assert lower["domain"] == list(DOMAIN)
    assert lower["source_sha256"] == cert["inputs"]["mod3_source"][1]
    assert sha((ROOT / cert["inputs"]["mod3_source"][0]).read_bytes()) == lower["source_sha256"]
    core, triples = domain["component_core_rows"], domain["signature_domain"]
    masks = [sum(1 << i for i in h) for h in triples]
    sites = [(r >> 3) & ((1 << 18) - 1) for r in core[3:]]
    q = [[2 - (mask >> i & 1) - (mask & sites[i]).bit_count() for i in range(18)] for mask in masks]
    assert q == domain["row_targets"] and all(sum(row) == 24 for row in q)
    empty = []
    for a, neighbors in enumerate(domain["possible_neighbor_signature_ids"]):
        occupied = 0
        for b in neighbors:
            occupied |= masks[b]
        empty.extend(18 * a + i for i in range(18) if not occupied >> i & 1)
    assert empty == cert["empty_mixed_row_ids"] and len(empty) == 756
    assert all(q[row // 18][row % 18] == 0 for row in empty)
    empty_set = set(empty)
    gram = []
    for i in range(18):
        for j in range(i, 18):
            rhs = 12 * (i == j) + 2 - sum((core[i + 3] >> k & 1) * (core[j + 3] >> k & 1) for k in range(21)) - (core[i + 3] >> (j + 3) & 1)
            gram.append({"site_pair": [i, j], "selector_support": [a for a, m in enumerate(masks) if m >> i & 1 and m >> j & 1], "rhs": rhs})
    gram.append({"site_pair": None, "selector_support": list(range(480)), "rhs": 60})
    assert gram == cert["original_gram_rows"]
    assert [r["site_pair"] for r in cert["skew_kernel_vectors"]] == [[i, j] for i in range(18) for j in range(i + 1, 18)]
    minor = cert["independence_minor"]
    columns = minor["column_mixed_row_ids"]
    assert len(columns) == len(set(columns)) == 153
    assert all(type(r) is int and 0 <= r < 8640 and r not in empty_set for r in columns)
    binary_rows = []
    for vector in cert["skew_kernel_vectors"]:
        i, j = vector["site_pair"]
        terms = []
        for a, m in enumerate(masks):
            if m >> j & 1:
                terms.append([18 * a + i, 1])
            if m >> i & 1:
                terms.append([18 * a + j, -1])
        assert sorted(terms) == vector["mixed_row_terms"]
        # Thus each anchor potential is M*h_a, where M_ij=1,M_ji=-1.
        # For all a,b its edge coefficient is h_b^T*M*h_a+h_a^T*M*h_b=0.
        rhs = [0] * 480
        for row, c in terms:
            a, site = divmod(row, 18)
            rhs[a] += c * q[a][site]
        assert [[a, c] for a, c in enumerate(rhs) if c] == vector["selector_rhs_terms"]
        reconstructed = [0] * 480
        constant = 0
        assert vector["gram_combination"] == sorted(vector["gram_combination"])
        assert len({r for r, _ in vector["gram_combination"]}) == len(vector["gram_combination"])
        for row, coefficient in vector["gram_combination"]:
            assert type(row) is int and 0 <= row < 172 and type(coefficient) is int
            for a in gram[row]["selector_support"]:
                reconstructed[a] += coefficient
            constant += coefficient * gram[row]["rhs"]
        assert reconstructed == rhs and constant == vector["gram_constant"] == 0
        lookup = dict(terms)
        binary_rows.append(sum((lookup.get(row, 0) % 2) << k for k, row in enumerate(columns)))
    assert [hex(r) for r in binary_rows] == minor["binary_rows_hex"]
    work = binary_rows[:]
    rank = 0
    for column in range(152, -1, -1):
        pivot = next((r for r in range(rank, 153) if work[r] >> column & 1), None)
        if pivot is None:
            continue
        work[rank], work[pivot] = work[pivot], work[rank]
        for r in range(rank + 1, 153):
            if work[r] >> column & 1:
                work[r] ^= work[rank]
        rank += 1
    assert rank == minor["rank_mod2"] == cert["projected_skew_rank_mod2"] == 153
    assert minor["determinant_mod2"] == 1
    assert cert["rational_left_nullity"] == 756 + 153 == 909
    assert cert["rational_mixed_rank_lower"] == cert["rational_mixed_rank_upper"] == cert["rational_mixed_rank"] == 8640 - 909 == lower["edge_rank"]
    assert time.monotonic() - started < 30
    return {"status": "PASS_COLD_COMPLETE_RATIONAL_KERNEL_AND_GRAM_RHS_IDENTITIES",
            "source_sha256": sha(Path(__file__).read_bytes()), "producer": PRODUCER, "certificate": CERTIFICATE,
            "domain": DOMAIN, "mod3_lower_bound": cert["inputs"]["mod3_independent"],
            "empty_rows_and_zero_rhs_checked": 756, "exact_skew_forms_checked": 153,
            "all_pair_integer_annihilation_proved_from_skew_forms": True,
            "saved_minor_dimension": 153, "saved_minor_rank_mod2": rank,
            "integer_gram_rhs_coefficients_checked": 153 * 480,
            "gram_constants_checked_zero": 153, "rational_mixed_rank": 7731,
            "complete_rational_left_kernel_dimension": 909,
            "optimizer_calls": 0, "native_imports": 0, "producer_imports": 0,
            "large_elimination_repeated": False, "all_prime_conclusion_claimed": False,
            "capacity_or_integrality_feasibility_claimed": False, "seconds": time.monotonic() - started}


if __name__ == "__main__":
    assert __debug__ and len(sys.argv) == 2
    result = check()
    with Path(sys.argv[1]).open("x") as stream:
        json.dump(result, stream, sort_keys=True, indent=2)
        stream.write("\n")
    print(json.dumps(result, sort_keys=True))
