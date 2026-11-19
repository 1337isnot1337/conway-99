"""Complete necessary within-orbit count tables from all literal subsets.

Every selector orbit has six or twelve members. Enumerate all its subsets,
apply the proved pair zeros and each original Gram capacity, and record
the exact selector/pair orbit populations. No solver or graph symmetry
assumption occurs. The 42 tables concern separate local restrictions.
"""
import argparse
from collections import Counter
import gzip
import hashlib
from itertools import combinations
import json
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[2]
LOGS = ROOT / "experiments/logs/root-prism-free"
INPUTS = {
    "domains": ("f0-orbit-populations02-domains.json.gz", "4f079468530dba0746512cc4afce01666b2a63a2c8f35f66a4660a4fe3bab8ab"),
    "domain_replay": ("f0-orbit-populations02-independent-replay.json", "a8bb55cbf773ea75a8cd1d5a18b50281ecbe08f6074cea04fb2d75799138273a"),
    "moments": ("f0-second-moments-preparation02.json.gz", "404d91da35c798ba248887c22a7500957947e24b71d5197dc44432460e6d219e"),
    "baseline": ("f0-boolean-fractional-model.json.gz", "703206929c9c85a40ac4ddcbfb1708c716c288482cf50c77a32249404e35b782"),
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def read(name):
    path, expected = INPUTS[name]
    raw = (LOGS / path).read_bytes()
    assert sha(raw) == expected
    return json.loads(gzip.decompress(raw) if path.endswith(".gz") else raw)


def pair_id(a, b):
    a, b = sorted((a, b))
    assert 0 <= a < b < 480
    return a * (959 - a) // 2 + b - a - 1


def build(deadline):
    domains, cold, moments, baseline = [read(name) for name in INPUTS]
    assert cold["status"].startswith("PASS")
    orbits = domains["selector_orbits"]
    assert orbits == moments["selector_orbits"] == baseline["validation"]["selector_orbits"]
    assert len(orbits) == 42 and Counter(map(len, orbits)) == {6: 4, 12: 38}
    assert sorted(a for orbit in orbits for a in orbit) == list(range(480))
    column_map = {old: new for new, old in enumerate(domains["new15038_to_original15589"])}
    assert len(column_map) == 15038 and all(column_map[i] == i for i in range(42))
    fixed = set(domains["original_Z_zero_columns"])
    assert len(fixed) == 389 and all(j >= 5847 for j in fixed)
    pmap = moments["pair_to_orbit"]
    rows = moments["original_selector_equalities"]
    assert len(rows) == 172 and all(r["family"] == "Gram" for r in rows[:171])
    # Reconstruct each literal support directly from its core coordinates.
    triples = baseline["validation"]["triples"]
    for row in rows[:171]:
        i, j = row["core_pair"]
        support = [a for a, h in enumerate(triples) if i in h and j in h]
        assert support == row["support"] and type(row["quota"]) is int and row["quota"] >= 0
    tables, total_masks, total_valid, total_profiles = [], 0, 0, 0
    seen_current_pair_columns = set()
    for orbit_id, orbit in enumerate(orbits):
        if time.monotonic() >= deadline:
            raise TimeoutError("finite profile-table preparation deadline")
        n = len(orbit)
        local = {a: i for i, a in enumerate(orbit)}
        pairs, forbidden = [], []
        for i, j in combinations(range(n), 2):
            a, b = orbit[i], orbit[j]
            po = pmap[pair_id(a, b)]
            assert domains["pair_orbit_selector_blocks"][po] == [orbit_id, orbit_id]
            old = 5847 + po
            pair = {"local_mask": (1 << i) | (1 << j), "literal_pair": [a, b], "original_pair_orbit": po}
            if old in fixed:
                forbidden.append(pair)
            else:
                pair["count_column"] = column_map[old]
                pairs.append(pair)
        pair_columns = sorted({p["count_column"] for p in pairs})
        expected_columns = sorted(column_map[5847 + j] for j, block in enumerate(domains["pair_orbit_selector_blocks"])
                                  if block == [orbit_id, orbit_id] and 5847 + j not in fixed)
        assert pair_columns == expected_columns
        assert not (seen_current_pair_columns & set(pair_columns))
        seen_current_pair_columns.update(pair_columns)
        pindex = {j: i + 1 for i, j in enumerate(pair_columns)}
        capacities = []
        for row_id, row in enumerate(rows[:171]):
            mask = sum(1 << local[a] for a in row["support"] if a in local)
            if mask.bit_count() > row["quota"]:
                capacities.append({"original_Gram_row": row_id, "local_support_mask": mask,
                                   "quota": row["quota"], "core_pair": row["core_pair"]})
        profiles = {}
        dispositions, valid_by_size = Counter(), Counter()
        mask_profile_hash = hashlib.sha256()
        for mask in range(1 << n):
            if mask % 256 == 0 and time.monotonic() >= deadline:
                raise TimeoutError("finite profile-table enumeration deadline")
            if any(mask & p["local_mask"] == p["local_mask"] for p in forbidden):
                dispositions["proved_pair_zero"] += 1
                mask_profile_hash.update(canonical([mask, "proved_pair_zero"]) + b"\n")
                continue
            failed = next((c for c in capacities if (mask & c["local_support_mask"]).bit_count() > c["quota"]), None)
            if failed is not None:
                dispositions["original_Gram_capacity"] += 1
                mask_profile_hash.update(canonical([mask, "original_Gram_capacity", failed["original_Gram_row"]]) + b"\n")
                continue
            profile = [mask.bit_count()] + [0] * len(pair_columns)
            for pair in pairs:
                if mask & pair["local_mask"] == pair["local_mask"]:
                    profile[pindex[pair["count_column"]]] += 1
            assert sum(profile[1:]) == profile[0] * (profile[0] - 1) // 2
            assert all(0 <= value <= domains["new15038_orbit_sizes"][column]
                       for column, value in zip([orbit_id] + pair_columns, profile))
            key = tuple(profile)
            if key not in profiles:
                profiles[key] = {"counts": profile, "representative_local_mask": mask, "literal_subset_count": 0}
            profiles[key]["literal_subset_count"] += 1
            dispositions["accepted_local_subset"] += 1
            valid_by_size[profile[0]] += 1
            mask_profile_hash.update(canonical([mask, profile]) + b"\n")
        assert sum(dispositions.values()) == 1 << n
        assert sum(p["literal_subset_count"] for p in profiles.values()) == dispositions["accepted_local_subset"]
        assert tuple([0] * (len(pair_columns) + 1)) in profiles
        table = {"selector_orbit": orbit_id, "literal_selectors": orbit,
                 "count_columns": [orbit_id] + pair_columns,
                 "count_columns_original15589": [domains["new15038_to_original15589"][j] for j in [orbit_id] + pair_columns],
                 "subsets_examined": 1 << n, "subsets_by_disposition": dict(dispositions),
                 "accepted_subsets_by_size": {str(k): v for k, v in sorted(valid_by_size.items())},
                 "forced_zero_literal_pairs": forbidden, "retained_literal_pair_map": pairs,
                 "nontrivial_original_Gram_capacities": capacities,
                 "all_subset_dispositions_sha256": mask_profile_hash.hexdigest(),
                 "profiles": [profiles[k] for k in sorted(profiles)],
                 "maximum_selector_population": max(valid_by_size),
                 "group_equivalence_assumed_for_deduplication": False}
        tables.append(table)
        total_masks += 1 << n
        total_valid += dispositions["accepted_local_subset"]
        total_profiles += len(profiles)
    assert total_masks == 155904 and len(tables) == 42
    return {"schema": "conway99.f0-selector-orbit-count-profiles.v1",
            "status": "COMPLETE_EXACT_SUBSET_PROFILE_TABLES_NO_SOLVER",
            "source_sha256": sha(Path(__file__).read_bytes()),
            "inputs": {name: {"path": str(Path("experiments/logs/root-prism-free") / path), "sha256": digest}
                       for name, (path, digest) in INPUTS.items()},
            "tables": tables, "selector_orbits": 42, "literal_subsets_examined": total_masks,
            "accepted_literal_subsets": total_valid, "distinct_profile_tuples": total_profiles,
            "within_orbit_pair_count_columns": len(seen_current_pair_columns),
            "maximum_population_histogram": {str(k): v for k, v in sorted(Counter(t["maximum_selector_population"] for t in tables).items())},
            "count_model_variables": 15038, "count_integer_variables_assumed": True,
            "graph_automorphism_assumed": False, "solver_calls": 0, "optimizer_calls": 0,
            "global_incidence_claimed": False, "F0_excluded": False,
            "validity": "An actual incidence restricts to one enumerated subset in each orbit. Proved pair zeros forbid every literal pair in those pair orbits. Each partial Gram sum is at most its global quota. Pair orbit populations are literal pair counts, so its exact local tuple appears in this table.",
            "scope": "Complete within-orbit restrictions from the389 pair-zero orbits and171 original Gram capacities only. Cross-orbit compatibility and a shared global incidence remain untested."}


def save(path, value):
    raw = canonical(value) + b"\n"
    if str(path).endswith(".gz"):
        raw = gzip.compress(raw, mtime=0)
    with path.open("xb") as handle:
        handle.write(raw)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "replay"))
    parser.add_argument("--record", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    started = time.monotonic()
    result = build(started + 60)
    if args.mode == "replay":
        raw = args.record.read_bytes()
        saved = json.loads(gzip.decompress(raw) if str(args.record).endswith(".gz") else raw)
        assert saved == result
        result = {"status": "PASS: all155904 literal subsets and42 complete count-profile tables replayed",
                  "source_sha256": sha(Path(__file__).read_bytes()), "record_sha256": sha(raw),
                  "literal_subsets_examined": result["literal_subsets_examined"],
                  "accepted_literal_subsets": result["accepted_literal_subsets"],
                  "distinct_profile_tuples": result["distinct_profile_tuples"],
                  "solver_calls": 0, "optimizer_calls": 0, "seconds": time.monotonic() - started}
    save(args.output, result)
    print(json.dumps({"status": result["status"], "sha256": sha(args.output.read_bytes()),
                      "subsets": result["literal_subsets_examined"], "accepted": result["accepted_literal_subsets"],
                      "profiles": result["distinct_profile_tuples"],
                      "maximum_population_histogram": result.get("maximum_population_histogram"),
                      "seconds": time.monotonic() - started}, indent=2), flush=True)


if __name__ == "__main__":
    main()
