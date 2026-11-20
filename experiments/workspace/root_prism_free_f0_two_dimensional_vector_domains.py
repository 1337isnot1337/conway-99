"""Prepare three finite A2 vector domains from frozen literal inverse masks.

No selector subsets are enumerated and no pair/triple Gram table is built.
All products of the resulting vector domains remain a separately gated stage.
"""
import argparse
from collections import Counter
import gzip
from hashlib import sha256
from itertools import combinations, product
import json
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "experiments/logs/root-prism-free"
INPUTS = {
    "scope": ("f0-two-dimensional-moments-scope01.json", "948e256945fc817cc75ea46c969c055b21e61832a4f2177c481884e73338223f"),
    "scope_review": ("f0-two-dimensional-moments-root-source-review.json", "6bca6113583b2f52f3fefffad5f67edfe75a10eaca43df4d95e3262ce0e41560"),
    "inverse": ("f0-character-literal-lift-preparation01.json.gz", "241cd14c61b465025c72ffcaa65af8e5c48e9e5a0eda7ea7d252e9d74b22db1e"),
    "inverse_cold": ("f0-character-literal-lift-preparation01-cold.json", "6cebe725527eaf28f3d075a3ad9741fcbcf50cdedd42107bdc5ebcbe857da72f"),
    "moments": ("f0-second-moments-preparation02.json.gz", "404d91da35c798ba248887c22a7500957947e24b71d5197dc44432460e6d219e"),
}
SCOPE_SOURCE = ("root_prism_free_f0_two_dimensional_moments.py", "31793743ba11fb56f42bcc9f383fe8b3268dae1cd8ebf6ec0271160a1d58d2fd")
ORBITS = [2, 3, 4]
DIRECTIONS = [[1, 0], [0, 1], [-1, -1]]
ENTRY_ORDER = [[0, 0], [0, 1], [0, 2], [1, 1], [1, 2], [2, 2]]
LIMITS = {"preparation_seconds": 30, "future_seconds_per_stage": 30,
          "maximum_saved_record_bytes": 4 << 20, "maximum_local_masks_visited": 2187,
          "maximum_future_pair_vector_combinations": 1083,
          "maximum_future_triple_vector_combinations": 6859, "optimizer_calls": 0}


def sha(raw):
    return sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def tick(deadline):
    if time.monotonic() >= deadline:
        raise TimeoutError("three-vector-domain preparation deadline")


def read(key):
    name, expected = INPUTS[key]
    raw = (BASE/name).read_bytes()
    assert sha(raw) == expected, key
    return json.loads(gzip.decompress(raw) if name.endswith(".gz") else raw)


def norm(v):
    a, b = v
    return 2*(a*a-a*b+b*b)


def pair_id(a, b):
    a, b = sorted((a, b))
    assert 0 <= a < b < 480
    return a*(959-a)//2+b-a-1


def prepare(deadline):
    scope, review, inverse, cold, moments = [read(k) for k in INPUTS]
    assert sha((ROOT/"experiments/workspace"/SCOPE_SOURCE[0]).read_bytes()) == SCOPE_SOURCE[1]
    assert scope["source_sha256"] == review["source_sha256"] == SCOPE_SOURCE[1]
    assert review["record_sha256"] == INPUTS["scope"][1]
    assert cold["record_sha256"] == INPUTS["inverse"][1]
    assert scope["H"] == [[2, -1], [-1, 2]]
    assert [c["selector_orbit"] for c in scope["three_constructed_plus_columns"]] == ORBITS
    forms = {tuple(f["matrix_entry"]): f for f in scope["six_exact_entry_forms"]}
    assert sorted(forms) == [tuple(e) for e in ENTRY_ORDER]
    zero_pairs = set(inverse["original_zero_pair_orbits"])
    # A 27-color-count grid and a 25-coordinate grid are not selector censuses.
    color_vectors = sorted({(n0-n2, n1-n2) for n0, n1, n2 in product(range(3), repeat=3)})
    hexagon = sorted((a, b) for a in range(-2, 3) for b in range(-2, 3)
                     if max(0, a, b)-min(0, a, b) <= 2)
    assert color_vectors == hexagon and len(hexagon) == 19
    vector_index = {v: j for j, v in enumerate(hexagon)}
    domains, masks_visited = [], 0
    for ci, column in enumerate(scope["three_constructed_plus_columns"]):
        tick(deadline)
        oi = column["selector_orbit"]
        table = inverse["inverse_tables"][oi]
        literals, vectors = column["literal_selectors"], column["vectors"]
        assert column["basis_vector"] == [1, 0]
        assert table["selector_orbit"] == oi and table["literal_selectors"] == literals
        assert len(literals) == len(vectors) == 12 and len(set(literals)) == 12
        assert Counter(map(tuple, vectors)) == Counter({tuple(v): 4 for v in DIRECTIONS})
        colors, matching = [], []
        for direction in DIRECTIONS:
            positions = [i for i, v in enumerate(vectors) if v == direction]
            pairs = []
            for a, b in combinations(positions, 2):
                po = moments["pair_to_orbit"][pair_id(literals[a], literals[b])]
                if po in zero_pairs:
                    pairs.append({"local_positions": [a, b], "literal_selectors": [literals[a], literals[b]],
                                  "original_pair_orbit": po})
                    matching.append([a, b])
            assert len(pairs) == 2
            assert sorted(i for p in pairs for i in p["local_positions"]) == positions
            colors.append({"direction": direction, "local_positions": positions,
                           "literal_selectors": [literals[i] for i in positions],
                           "proved_zero_matching": pairs, "maximum_selected": 2})
        assert len(matching) == 6 and sorted(i for p in matching for i in p) == list(range(12))
        all_zero = [[a, b] for a, b in combinations(range(12), 2)
                    if moments["pair_to_orbit"][pair_id(literals[a], literals[b])] in zero_pairs]
        assert sorted(matching) == all_zero
        seen, frequencies, first, profile_rows = set(), Counter(), {}, []
        for profile in table["profiles"]:
            tick(deadline)
            row = profile["counts_and_signed_populations"]
            assert len(row) == len(table["count_columns"])+len(table["signed_population_columns"])
            count_values = dict(zip(table["count_columns"], row[:len(table["count_columns"])]))
            diagonal = sum(c*count_values[j] for j, c in forms[ci, ci]["native_count_terms"])
            ids = set()
            assert profile["local_masks"]
            for mask in profile["local_masks"]:
                assert type(mask) is int and 0 <= mask < (1 << 12) and mask not in seen
                seen.add(mask); masks_visited += 1
                assert masks_visited <= LIMITS["maximum_local_masks_visited"]
                assert all(not (mask >> a & 1 and mask >> b & 1) for a, b in matching)
                counts = [sum(mask >> i & 1 for i in c["local_positions"]) for c in colors]
                assert max(counts) <= 2 and sum(counts) == mask.bit_count() == count_values[oi]
                v = tuple(sum(vectors[i][k] for i in range(12) if mask >> i & 1) for k in range(2))
                assert v == (counts[0]-counts[2], counts[1]-counts[2])
                assert norm(v) == diagonal
                frequencies[v] += 1; ids.add(vector_index[v])
                witness = {"tuple_index": profile["tuple_index"], "local_mask": mask,
                           "color_counts": counts, "population": mask.bit_count()}
                first.setdefault(v, witness)
            profile_rows.append({"tuple_index": profile["tuple_index"], "Gram_diagonal": diagonal,
                                 "vector_indices": sorted(ids), "literal_preimages": len(profile["local_masks"])})
        assert len(seen) == table["accepted_literal_masks"] == 3**6 == 729
        assert sorted(frequencies) == hexagon
        assert [p["tuple_index"] for p in profile_rows] == list(range(len(profile_rows)))
        domains.append({"selector_orbit": oi, "literal_selectors": literals, "colors": colors,
            "complete_saved_mask_count": len(seen), "profile_count": len(profile_rows),
            "matching_choice_cardinality": 3**6,
            "saved_masks_equal_all_matching_independent_sets_by_inclusion_and_cardinality": True,
            "vectors": [list(v) for v in hexagon],
            "vector_literal_multiplicities": [frequencies[v] for v in hexagon],
            "vector_witnesses": [first[v] for v in hexagon],
            "profile_vector_domains": profile_rows,
            "complete_saved_mask_list_sha256": sha(canonical(sorted(seen)))})
    assert masks_visited == 2187
    sizes = [len(d["vectors"]) for d in domains]
    pair_work = [{"column_indices": [i, j], "selector_orbits": [ORBITS[i], ORBITS[j]],
                  "ordered_vector_combinations": sizes[i]*sizes[j]} for i, j in combinations(range(3), 2)]
    pair_total = sum(p["ordered_vector_combinations"] for p in pair_work)
    triple_total = sizes[0]*sizes[1]*sizes[2]
    assert pair_total == LIMITS["maximum_future_pair_vector_combinations"]
    assert triple_total == LIMITS["maximum_future_triple_vector_combinations"]
    diagonal_values = sorted({norm(v) for v in hexagon})
    assert diagonal_values == [0, 2, 6, 8]
    assert all(all(0 <= j < 15038 and type(c) is int for j, c in forms[tuple(e)]["native_count_terms"])
               for e in ENTRY_ORDER)
    tick(deadline)
    return {"schema": "conway99.f0.two-dimensional-vector-domains.v1",
        "status": "COMPLETE_VECTOR_DOMAIN_PREPARATION", "source_sha256": sha(Path(__file__).read_bytes()),
        "inputs": INPUTS, "scope_source": SCOPE_SOURCE, "limits": LIMITS,
        "H": scope["H"], "selector_orbits": ORBITS, "domains": domains,
        "native_count_namespace": {"existing_count_ids": [0, 15038], "full_target_ids": [0, 18444],
                                   "new_variables_allocated": 0},
        "six_entry_order": ENTRY_ORDER,
        "six_native_entry_forms": [forms[tuple(e)] for e in ENTRY_ORDER],
        "future_entry_domains": {"diagonal_values": diagonal_values,
                                  "off_diagonal_integer_interval_from_Cauchy": [-8, 8]},
        "future_pair_work": pair_work, "future_pair_combinations": pair_total,
        "future_triple_combinations": triple_total,
        "conservative_future_tuple_payload_bytes_at256_per_combination": 256*(pair_total+triple_total),
        "preparation_controls": {"bounded_color_count_triples": 27, "coordinate_grid_sites": 25,
                                 "attainable_vectors_per_orbit": 19,
                                 "positive_metric_leading_minor": 2, "metric_determinant": 3,
                                 "profile_norms_checked_on_saved_masks": masks_visited},
        "scope": {"one_literal_assignment_or_one_common_relabeling_orbit": True,
                  "arbitrary_mixtures_supported": False, "cross_orbit_selector_compatibility_enforced": False,
                  "existing_inverse_domains_complete": True,
                  "pair_Gram_tables_built": False, "triple_Gram_table_built": False,
                  "production_count_candidate_checked": False, "new_selector_subset_censuses": 0,
                  "full_isotypic_blocks_built": 0, "optimizer_calls": 0}}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists(), "preserve existing frozen artifacts"
    start = time.monotonic()
    try:
        record = prepare(start+LIMITS["preparation_seconds"])
    except Exception as exc:
        record = {"schema": "conway99.f0.two-dimensional-vector-domains.v1", "status": "INCOMPLETE_PREPARATION",
                  "source_sha256": sha(Path(__file__).read_bytes()), "error": type(exc).__name__+": "+str(exc),
                  "pair_Gram_tables_built": False, "triple_Gram_table_built": False, "optimizer_calls": 0}
    record["seconds"] = time.monotonic()-start
    raw = canonical(record)+b"\n"
    assert len(raw) <= LIMITS["maximum_saved_record_bytes"]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(raw)
    print(json.dumps({"status": record["status"], "seconds": record["seconds"],
                      "record_sha256": sha(raw), "bytes": len(raw),
                      "pair_combinations_not_run": record.get("future_pair_combinations"),
                      "triple_combinations_not_run": record.get("future_triple_combinations")}))
    if record["status"] != "COMPLETE_VECTOR_DOMAIN_PREPARATION":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
