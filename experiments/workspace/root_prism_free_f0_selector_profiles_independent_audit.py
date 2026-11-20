"""Independent literal-subset audit of the42 selector-orbit profile tables.

No subject module is imported. Gram capacities are recomputed from the
literal21-core, and subsets are visited by combinations rather than masks.
"""
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
    "record": ("f0-selector-orbit-profiles01.json.gz", "93c891e7eef037e5869e5c8e13c3cf31d0ad253cb6caf5cd38930b09715e085d"),
    "domain": ("f0-orbit-populations02-domains.json.gz", "4f079468530dba0746512cc4afce01666b2a63a2c8f35f66a4660a4fe3bab8ab"),
    "baseline": ("f0-boolean-fractional-model.json.gz", "703206929c9c85a40ac4ddcbfb1708c716c288482cf50c77a32249404e35b782"),
}
SUBJECT = "4e8d8c15024798bb83e4c10b64c9cf78fdc905e3e9f2d453ec7f28ca80b7f1ba"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def read(key):
    name, expected = INPUTS[key]
    raw = (LOGS / name).read_bytes()
    assert sha(raw) == expected
    return json.loads(gzip.decompress(raw))


def main():
    started = time.monotonic()
    subject = ROOT / "experiments/workspace/root_prism_free_f0_selector_orbit_profiles.py"
    assert sha(subject.read_bytes()) == SUBJECT
    record, domain, baseline = read("record"), read("domain"), read("baseline")
    assert record["source_sha256"] == SUBJECT
    data = baseline["validation"]
    core, signatures = data["core"], data["triples"]
    assert len(core) == 21 and len(signatures) == 480
    gram = []
    gram_index = {}
    for i in range(18):
        for j in range(i, 18):
            u, v = i + 3, j + 3
            value = (14 if i == j else 1 if core[u] >> v & 1 else 2) - (core[u] & core[v]).bit_count()
            assert value >= 0
            gram_index[i, j] = len(gram)
            gram.append((i, j, value))
    contributions = [[gram_index[i, j] for i in h for j in h if i <= j] for h in signatures]
    assert all(len(x) == 6 for x in contributions)
    literal_pairs = list(combinations(range(480), 2))
    pair_ids = {pair: p for p, pair in enumerate(literal_pairs)}
    pair_to_orbit, orbit_members = {}, []
    for p, (a, b) in enumerate(literal_pairs):
        if (a, b) in pair_to_orbit:
            continue
        images = sorted({tuple(sorted((g[a], g[b]))) for g in domain["signature_actions"]})
        assert images[0] == (a, b)
        q = len(orbit_members)
        orbit_members.append(sorted(pair_ids[x] for x in images))
        for ab in images:
            assert ab not in pair_to_orbit
            pair_to_orbit[ab] = q
    assert len(orbit_members) == 9742 and len(pair_to_orbit) == 114960
    assert sha(canonical(orbit_members)) == domain["literal_orbit_member_hashes"]["pair"]
    zero = set(domain["original_Z_zero_columns"])
    reverse = {o: j for j, o in enumerate(domain["new15038_to_original15589"])}
    totals, per_orbit, seen_columns = Counter(), [], set()
    for orbit_id, table in enumerate(record["tables"]):
        assert time.monotonic() - started < 60
        orbit = domain["selector_orbits"][orbit_id]
        assert orbit == table["literal_selectors"] and table["selector_orbit"] == orbit_id
        local = {a: i for i, a in enumerate(orbit)}
        within = list(combinations(orbit, 2))
        forbidden = {ab for ab in within if 5847 + pair_to_orbit[ab] in zero}
        retained = {ab: reverse[5847 + pair_to_orbit[ab]] for ab in within if ab not in forbidden}
        columns = sorted(set(retained.values()))
        assert table["count_columns"] == [orbit_id] + columns
        assert not seen_columns.intersection(columns)
        seen_columns.update(columns)
        expected_forbidden = {tuple(p["literal_pair"]) for p in table["forced_zero_literal_pairs"]}
        assert expected_forbidden == forbidden
        expected_retained = {tuple(p["literal_pair"]): p["count_column"] for p in table["retained_literal_pair_map"]}
        assert expected_retained == retained
        capacities = []
        for index, (i, j, quota) in enumerate(gram):
            mask = sum(1 << local[a] for a in orbit if i in signatures[a] and j in signatures[a])
            if mask.bit_count() > quota:
                capacities.append({"original_Gram_row": index, "local_support_mask": mask,
                                   "quota": quota, "core_pair": [i, j]})
        assert capacities == table["nontrivial_original_Gram_capacities"]
        profiles, dispositions, by_size = Counter(), Counter(), Counter()
        for size in range(len(orbit) + 1):
            for subset in combinations(orbit, size):
                pairs = list(combinations(subset, 2))
                if any(ab in forbidden for ab in pairs):
                    dispositions["proved_pair_zero"] += 1
                    continue
                row_counts = Counter(g for a in subset for g in contributions[a])
                if any(count > gram[g][2] for g, count in row_counts.items()):
                    dispositions["original_Gram_capacity"] += 1
                    continue
                pair_counts = Counter(retained[ab] for ab in pairs)
                profile = tuple([size] + [pair_counts[c] for c in columns])
                assert sum(profile[1:]) == size * (size - 1) // 2
                profiles[profile] += 1
                dispositions["accepted_local_subset"] += 1
                by_size[size] += 1
        saved = {tuple(p["counts"]): p["literal_subset_count"] for p in table["profiles"]}
        assert len(saved) == len(table["profiles"]) and dict(profiles) == saved
        assert dict(dispositions) == table["subsets_by_disposition"]
        assert {str(k): v for k, v in sorted(by_size.items())} == table["accepted_subsets_by_size"]
        assert sum(dispositions.values()) == table["subsets_examined"] == 1 << len(orbit)
        for p in table["profiles"]:
            mask = p["representative_local_mask"]
            assert 0 <= mask < 1 << len(orbit)
            subset = [a for i, a in enumerate(orbit) if mask >> i & 1]
            pc = Counter(retained[ab] for ab in combinations(subset, 2))
            assert p["counts"] == [len(subset)] + [pc[c] for c in columns]
        totals.update(examined=1 << len(orbit), accepted=dispositions["accepted_local_subset"], profiles=len(profiles))
        per_orbit.append({"orbit": orbit_id, "examined": 1 << len(orbit),
                          "accepted": dispositions["accepted_local_subset"], "profiles": len(profiles)})
    assert totals == {"examined": 155904, "accepted": 64144, "profiles": 5733}
    assert len(seen_columns) == 320 and len(per_orbit) == 42
    report = {"status": "PASS: independent literal Gram/subset/profile census",
              "source_sha256": sha(Path(__file__).read_bytes()), "subject_source_sha256": SUBJECT,
              "inputs": {k: {"path": str((LOGS / p).relative_to(ROOT)), "sha256": h} for k,(p,h) in INPUTS.items()},
              "all171_Gram_quotas_reconstructed_from_literal21core": True,
              "all9742_pair_orbits_reconstructed_from12_actions": True,
              "literal_subsets_checked": totals["examined"], "accepted_subsets": totals["accepted"],
              "all5733_profile_multiplicities_and_representatives_checked": True,
              "within_orbit_pair_columns": 320, "per_orbit": per_orbit,
              "complete_subject_source_read": True,
              "necessity": "Every incidence restricts to an enumerated local subset; nonnegative Gram counts and proved zero pairs justify every rejection. Deduplication is by equal count tuples, not an assumed graph automorphism.",
              "subject_imported": False, "solver_calls": 0, "optimizer_calls": 0,
              "global_incidence_or_graph_feasibility_claimed": False,
              "seconds": time.monotonic() - started, "cooperative_limit_seconds": 60}
    output = LOGS / "f0-selector-orbit-profiles-independent-audit.json"
    with output.open("x") as stream:
        json.dump(report, stream, indent=2)
        stream.write("\n")
    print(json.dumps({"status": report["status"], "path": str(output.relative_to(ROOT)),
                      "sha256": sha(output.read_bytes()), "seconds": report["seconds"]}, indent=2))


if __name__ == "__main__":
    main()
