"""Read-only source and saved-ledger review of F0 character populations.

This does not import the subject, enumerate group characters or literal
subsets, rebuild products, or call a solver. It checks input bindings and
the exact projection of the saved refined tables to the saved old tables.
The mathematical source review is recorded explicitly as such.
"""
from collections import Counter, defaultdict
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = "experiments/logs/root-prism-free/"
BINDINGS = {
    "subject_source": ("experiments/workspace/root_prism_free_f0_character_populations.py",
        "7b1759441b1d88b2d68e03d66b1f16a13be8a6cee3eefb35e2610aa107e42295"),
    "record": (BASE+"f0-character-populations01.json.gz",
        "139d06a3383f8fc79d677972ce052ce29966e8b3406e7d1e7d1077aea7c2cef6"),
    "cold": (BASE+"f0-character-populations01-cold.json",
        "1fdc14c0bda54f0b5e63b23a3b7d5f85d9afd92ea418b4931d53b644444e814b"),
    "domains": (BASE+"f0-orbit-populations02-domains.json.gz",
        "4f079468530dba0746512cc4afce01666b2a63a2c8f35f66a4660a4fe3bab8ab"),
    "profiles": (BASE+"f0-selector-orbit-profiles01.json.gz",
        "93c891e7eef037e5869e5c8e13c3cf31d0ad253cb6caf5cd38930b09715e085d"),
    "moments": (BASE+"f0-second-moments-preparation02.json.gz",
        "404d91da35c798ba248887c22a7500957947e24b71d5197dc44432460e6d219e"),
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    data = {}
    for key, (path, expected) in BINDINGS.items():
        raw = (ROOT/path).read_bytes()
        assert sha(raw) == expected, key
        if key != "subject_source":
            data[key] = json.loads(gzip.decompress(raw) if path.endswith(".gz") else raw)
    record, cold, domains, profiles, moments = [data[k] for k in ("record", "cold", "domains", "profiles", "moments")]
    assert record["source_sha256"] == cold["source_sha256"] == BINDINGS["subject_source"][1]
    assert cold["record_sha256"] == BINDINGS["record"][1] and cold["status"].startswith("PASS")
    assert record["optimizer_calls"] == record["solver_calls"] == cold["optimizer_calls"] == cold["solver_calls"] == 0
    mapping = domains["new15038_to_original15589"]
    assert len(mapping) == len(set(mapping)) == 15038 and mapping[:42] == list(range(42))
    assert len(domains["selector_orbits"]) == len(profiles["tables"]) == len(record["local_tables"]) == 42
    assert domains["selector_orbits"] == moments["selector_orbits"]
    assert domains["signature_actions"] == moments["selector_actions"]
    assert len(domains["signature_actions"]) == 12 and len(moments["pair_orbits"]) == 9742
    zeros = set(domains["original_Z_zero_columns"])
    assert len(zeros) == 389 and all(5847 <= j < 15589 for j in zeros)
    assert not zeros.intersection(mapping)
    assert all((5847+i in mapping) == (5847+i not in zeros) for i in range(9742))
    populations = record["signed_populations"]
    assert len(populations) == record["signed_population_count"] == 118
    assert [p["signed_population"] for p in populations] == list(range(118))
    counts = Counter(p["character"] for p in populations)
    assert counts == {1: 38, 2: 42, 3: 38}
    assert sum(n*(n+1)//2 for n in counts.values()) == len(record["product_equations"]) == 2385
    for p in populations:
        assert p["literal_selectors"] == domains["selector_orbits"][p["selector_orbit"]]
        assert len(p["signs"]) == len(p["literal_selectors"])
        assert set(p["signs"]) == {-1, 1} and sum(p["signs"]) == 0
    assert [t["selector_orbit"] for t in profiles["tables"]] == list(range(42))
    assert [t["selector_orbit"] for t in record["local_tables"]] == list(range(42))
    old_tuples = refined_tuples = literal_subsets = representative_checks = 0
    projections = []
    for original, refined in zip(profiles["tables"], record["local_tables"]):
        oi = original["selector_orbit"]
        assert original["literal_selectors"] == domains["selector_orbits"][oi]
        columns = original["count_columns"]
        assert columns == refined["count_columns"] and columns[0] == oi
        assert [mapping[j] for j in columns] == original["count_columns_original15589"]
        signed = [p["signed_population"] for p in populations if p["selector_orbit"] == oi]
        assert refined["signed_population_columns"] == signed
        aggregate, representatives = Counter(), defaultdict(list)
        for p in refined["profiles"]:
            values = p["counts_and_signed_populations"]
            assert len(values) == len(columns)+len(signed)
            key = tuple(values[:len(columns)])
            assert p["literal_subset_count"] > 0
            aggregate[key] += p["literal_subset_count"]
            representatives[key].append(p["representative_local_mask"])
        expected = Counter({tuple(p["counts"]): p["literal_subset_count"] for p in original["profiles"]})
        assert aggregate == expected
        for p in original["profiles"]:
            assert min(representatives[tuple(p["counts"])]) == p["representative_local_mask"]
            representative_checks += 1
        assert len(original["profiles"]) == refined["base_profile_count"]
        assert sum(aggregate.values()) == refined["accepted_literal_subsets"]
        old_tuples += len(original["profiles"])
        refined_tuples += len(refined["profiles"])
        literal_subsets += sum(aggregate.values())
        projections.append({"selector_orbit": oi, "old_profiles": len(original["profiles"]),
                            "refined_profiles": len(refined["profiles"]),
                            "literal_subset_multiplicity": sum(aggregate.values()),
                            "all_old_representatives_recovered": True})
    assert (old_tuples, refined_tuples, literal_subsets, representative_checks) == (5733, 19331, 64144, 5733)
    result = {
        "status": "PASS: complete character source and exact saved-profile projection reviewed",
        "reviewer_source_sha256": sha(Path(__file__).read_bytes()),
        "bindings": {k: {"path": p, "sha256": h} for k, (p, h) in BINDINGS.items()},
        "entire252_line_subject_source_read": True,
        "mathematical_review": [
            "For a transitive selector orbit and sign character chi, a nonzero equivariant signing exists exactly when every stabilizer element has chi=1. The anchor convention is well-defined, and the source checks full covariance.",
            "The 2048 sign maps with identity value1 exhaust every one-dimensional real sign character. Higher-dimensional real representations are outside this scope.",
            "For z transformed by a core relabeling g, L_i(gz)=chi(g)L_i(z). Same-character products are invariant, so their averaged moment matrix equals the deterministic outer product L L^T for one incidence.",
            "No graph automorphism is assumed: only relabelings of the fixed core and its complete literal selector domain are used.",
            "Count coordinates are actual literal orbit populations. Off-diagonal selector blocks therefore have coefficient sign1 or sign-1 per pair orbit; same-selector-block expansions have factor2, with the diagonal selector-population term N_i.",
            "Only original proved-zero pair columns are omitted. The map leaves selector coordinates0 through41 unchanged; all other pair terms are transported through the exact old-to-new map.",
            "Balanced signs imply L_i=N_i modulo2 and |L_i|<=min(N_i,|O_i|-N_i). Enumerating all admitted local subsets preserves joint information about every supported character on that orbit.",
            "The retained local tables use only the earlier proved pair-zero exclusions and original Gram capacities. They impose no extra assumptions about a global compatible incidence.",
        ],
        "independent_saved_ledger_checks": {
            "selector_coordinate_identity_checked": 42,
            "all_original_Z_zero_substitutions_checked": 389,
            "all_surviving_pair_coordinate_memberships_checked": 9742,
            "signed_population_metadata_checked": 118,
            "exact_table_projections": projections,
            "old_profile_tuples_and_multiplicities_checked": old_tuples,
            "old_minimum_representatives_checked": representative_checks,
            "refined_profile_tuples_read": refined_tuples,
            "accepted_subset_multiplicity": literal_subsets,
        },
        "scope_caveat": "The rank-one equations are necessary for one underlying binary incidence. Arbitrary convex mixtures of incidences need not retain rank one. These equations and local tables do not prove a globally compatible incidence.",
        "subject_imported": False, "subject_executed": False,
        "group_or_subset_census_repeated": False, "product_equations_rebuilt": False,
        "native_binary_query_repeated": False, "controls_repeated": False,
        "optimizer_calls": 0, "F0_excluded": False,
    }
    path = ROOT/(BASE+"f0-character-populations-literature-review.json")
    assert not path.exists()
    path.write_text(json.dumps(result, indent=2)+"\n")
    print(json.dumps({"status": result["status"], "report_sha256": sha(path.read_bytes()),
                      "source_sha256": result["reviewer_source_sha256"],
                      "old_profiles": old_tuples, "refined_profiles": refined_tuples,
                      "optimizer_calls": 0}, indent=2))


if __name__ == "__main__":
    main()
