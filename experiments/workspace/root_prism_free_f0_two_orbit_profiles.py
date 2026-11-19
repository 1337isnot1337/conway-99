"""Exact joint tables for the two 24-signature unions of population three.

The inherited count equalities fix N0+N1=N6+N7=3. Each union therefore
requires only C(24,3)=2024 subsets. Keep the full cross-pair populations
and all six compatible signed populations, with no solver or symmetry.
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
    "count_model": ("f0-orbit-populations02-model.json.gz", "aa46e2ca9df7a5838926385e06a86acda041c8455ac3422ae1e7b0a5c4ce5437"),
    "count_replay": ("f0-orbit-populations02-independent-replay.json", "a8bb55cbf773ea75a8cd1d5a18b50281ecbe08f6074cea04fb2d75799138273a"),
    "moments": ("f0-second-moments-preparation02.json.gz", "404d91da35c798ba248887c22a7500957947e24b71d5197dc44432460e6d219e"),
    "characters": ("f0-character-populations01.json.gz", "139d06a3383f8fc79d677972ce052ce29966e8b3406e7d1e7d1077aea7c2cef6"),
    "character_replay": ("f0-character-populations01-cold.json", "1fdc14c0bda54f0b5e63b23a3b7d5f85d9afd92ea418b4931d53b644444e814b"),
    "literal_profile_audit": ("f0-selector-orbit-profiles-independent-audit.json", "e532fe58350ad856104333fba05b8601d776cbb98b76b3ce855ce8fa2a4be9a2"),
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def read(name):
    filename, expected = INPUTS[name]
    raw = (LOGS / filename).read_bytes()
    assert sha(raw) == expected, name
    return json.loads(gzip.decompress(raw) if filename.endswith(".gz") else raw)


def pair_id(a, b):
    a, b = sorted((a, b))
    assert 0 <= a < b < 480
    return a*(959-a)//2+b-a-1


def build(deadline):
    domains, model, cold, moments, chars, char_cold, audit = [read(name) for name in INPUTS]
    assert all(r["status"].startswith("PASS") for r in (cold, char_cold, audit))
    orbits = domains["selector_orbits"]
    assert orbits == moments["selector_orbits"]
    old_to_new = {old: j for j, old in enumerate(domains["new15038_to_original15589"])}
    zeros = set(domains["original_Z_zero_columns"])
    pmap = moments["pair_to_orbit"]
    gram = moments["original_selector_equalities"][:171]
    assert all(row["family"] == "Gram" for row in gram)
    tables = []
    for row_id, orbit_ids in ((1, [0, 1]), (3, [6, 7])):
        equality = model["matrix"]["equalities"][row_id]
        assert equality["terms"] == [[i, 1] for i in orbit_ids] and equality["rhs"] == 3
        members = sorted(a for i in orbit_ids for a in orbits[i])
        assert len(members) == len(set(members)) == 24
        member_set = set(members)
        owner = {a: i for i in orbit_ids for a in orbits[i]}
        pair_orbits = [po for po, block in enumerate(domains["pair_orbit_selector_blocks"])
                       if all(i in orbit_ids for i in block)]
        assert sum(domains["original15589_orbit_sizes"][5847+po] for po in pair_orbits) == 276
        retained = [old_to_new[5847+po] for po in pair_orbits if 5847+po not in zeros]
        columns = orbit_ids+sorted(retained)
        index = {j: k for k, j in enumerate(columns)}
        signed = [p for p in chars["signed_populations"] if p["selector_orbit"] in orbit_ids]
        assert len(signed) == 6
        weights = {p["signed_population"]: dict(zip(p["literal_selectors"], p["signs"])) for p in signed}
        for a, b in combinations(members, 2):
            assert pmap[pair_id(a, b)] in pair_orbits
        supports = [set(r["support"]) & member_set for r in gram]
        tuples, dispositions, projection_ids = {}, Counter(), {i: set() for i in orbit_ids}
        previous_index = {i: {tuple(p["counts_and_signed_populations"]): k
                              for k, p in enumerate(chars["local_tables"][i]["profiles"])} for i in orbit_ids}
        stream = hashlib.sha256()
        for step, selected in enumerate(combinations(members, 3)):
            if step % 128 == 0 and time.monotonic() >= deadline:
                raise TimeoutError("finite two-orbit table preparation")
            pos = [pmap[pair_id(a, b)] for a, b in combinations(selected, 2)]
            forbidden = next((po for po in pos if 5847+po in zeros), None)
            if forbidden is not None:
                dispositions["proved_pair_zero"] += 1
                stream.update(canonical([list(selected), "proved_pair_zero", forbidden])+b"\n")
                continue
            failed = next((i for i, (support, r) in enumerate(zip(supports, gram))
                           if sum(a in support for a in selected) > r["quota"]), None)
            if failed is not None:
                dispositions["original_Gram_capacity"] += 1
                stream.update(canonical([list(selected), "original_Gram_capacity", failed])+b"\n")
                continue
            counts = [0]*len(columns)
            for a in selected:
                counts[index[owner[a]]] += 1
            for po in pos:
                counts[index[old_to_new[5847+po]]] += 1
            values = [sum(weights[p["signed_population"]].get(a, 0) for a in selected) for p in signed]
            assert sum(counts[:2]) == sum(counts[2:]) == 3
            signed_point = dict(zip([p["signed_population"] for p in signed], values))
            point = dict(zip(columns, counts))
            for i in orbit_ids:
                old = chars["local_tables"][i]
                projected = tuple([point[j] for j in old["count_columns"]]
                                  + [signed_point[j] for j in old["signed_population_columns"]])
                projection_ids[i].add(previous_index[i][projected])
            key = tuple(counts+values)
            if key not in tuples:
                tuples[key] = {"counts_and_signed_populations": list(key),
                               "representative_literal_subset": list(selected), "literal_subset_count": 0}
            tuples[key]["literal_subset_count"] += 1
            dispositions["accepted_literal_subset"] += 1
            stream.update(canonical([list(selected), list(key)])+b"\n")
        assert sum(dispositions.values()) == 2024
        assert sum(p["literal_subset_count"] for p in tuples.values()) == dispositions["accepted_literal_subset"]
        assert tuples
        tables.append({"selector_orbits": orbit_ids, "literal_signatures": members,
                       "inherited_count_equality_row": row_id, "inherited_count_equality": equality,
                       "fixed_selected_population": 3, "literal_subsets_examined": 2024,
                       "dispositions": dict(dispositions), "count_columns": columns,
                       "signed_population_columns": [p["signed_population"] for p in signed],
                       "all_original_pair_orbits": pair_orbits,
                       "proved_zero_original_pair_orbits": [po for po in pair_orbits if 5847+po in zeros],
                       "all_subset_dispositions_sha256": stream.hexdigest(),
                       "profiles": [tuples[k] for k in sorted(tuples)],
                       "single_orbit_profile_indices_with_a_joint_extension": {str(i): sorted(v) for i, v in projection_ids.items()},
                       "no_graph_automorphism_or_local_relabeling_assumed": True})
    return {"schema": "conway99.f0-two-orbit-population-three-tables.v1",
            "status": "COMPLETE_EXACT_TWO_ORBIT_TABLES_NO_SOLVER",
            "source_sha256": sha(Path(__file__).read_bytes()),
            "inputs": {k: {"path": "experiments/logs/root-prism-free/"+v[0], "sha256": v[1]}
                       for k, v in INPUTS.items()},
            "tables": tables, "literal_subsets_examined": 4048,
            "accepted_literal_subsets": sum(t["dispositions"]["accepted_literal_subset"] for t in tables),
            "distinct_joint_tuples": sum(len(t["profiles"]) for t in tables),
            "signed_population_IDs_use_character_local_namespace": True,
            "validity": "The inherited count equation fixes exactly three selected signatures in each24-member union. The actual subset appears in the complete enumeration, violates no proved-zero pair or original Gram capacity, and has exactly the recorded within/cross-pair and signed populations.",
            "scope": "Two separate pair-of-orbit unions. Cross-compatibility between these two unions and all other orbits remains untested.",
            "optimizer_calls": 0, "solver_calls": 0, "F0_excluded": False, "global_incidence_claimed": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "replay"))
    parser.add_argument("--record", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    started = time.monotonic()
    result = build(started+60)
    if args.mode == "replay":
        raw = args.record.read_bytes()
        assert json.loads(gzip.decompress(raw)) == result
        result = {"status": "PASS: both complete24-signature population-three tables replayed",
                  "source_sha256": sha(Path(__file__).read_bytes()), "record_sha256": sha(raw),
                  "literal_subsets_examined": result["literal_subsets_examined"],
                  "accepted_literal_subsets": result["accepted_literal_subsets"],
                  "distinct_joint_tuples": result["distinct_joint_tuples"],
                  "solver_calls": 0, "seconds": time.monotonic()-started}
    raw = canonical(result)+b"\n"
    if str(args.output).endswith(".gz"):
        raw = gzip.compress(raw, mtime=0)
    with args.output.open("xb") as handle:
        handle.write(raw)
    print(json.dumps({"status": result["status"], "sha256": sha(raw),
                      "subsets": result["literal_subsets_examined"],
                      "accepted": result["accepted_literal_subsets"],
                      "tuples": result["distinct_joint_tuples"],
                      "seconds": time.monotonic()-started}, indent=2))
