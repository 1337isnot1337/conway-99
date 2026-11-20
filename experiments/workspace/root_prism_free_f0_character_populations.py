"""Exact signed orbit populations for the core group's real characters.

For a one-dimensional sign character, compatible selector-orbit sums
transform by a common sign. Their averaged second moments are therefore
products of deterministic signed populations. This construction adds no
graph-automorphism assumption and makes no solver query.
"""
import argparse
from collections import Counter, defaultdict
import gzip
import hashlib
from itertools import combinations, combinations_with_replacement, product
import json
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[2]
LOGS = ROOT / "experiments/logs/root-prism-free"
INPUTS = {
    "domains": ("f0-orbit-populations02-domains.json.gz", "4f079468530dba0746512cc4afce01666b2a63a2c8f35f66a4660a4fe3bab8ab"),
    "domain_replay": ("f0-orbit-populations02-independent-replay.json", "a8bb55cbf773ea75a8cd1d5a18b50281ecbe08f6074cea04fb2d75799138273a"),
    "moments": ("f0-second-moments-preparation02.json.gz", "404d91da35c798ba248887c22a7500957947e24b71d5197dc44432460e6d219e"),
    "profiles": ("f0-selector-orbit-profiles01.json.gz", "93c891e7eef037e5869e5c8e13c3cf31d0ad253cb6caf5cd38930b09715e085d"),
    "profile_replay": ("f0-selector-orbit-profiles01-cold.json", "cb10cd7dc77236d9caed7c7b8a410a33f7b998bea8d257b500d3c9f8561a76f8"),
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


def tick(deadline):
    if time.monotonic() >= deadline:
        raise TimeoutError("character-population finite preparation limit")


def group_characters(actions):
    index = {tuple(a): i for i, a in enumerate(actions)}
    assert len(index) == 12
    identity = index[tuple(range(480))]
    multiplication = [[index[tuple(a[b[j]] for j in range(480))]
                       for b in actions] for a in actions]
    characters = []
    for signs in product((1, -1), repeat=11):
        chi = list(signs)
        chi.insert(identity, 1)
        if all(chi[multiplication[a][b]] == chi[a]*chi[b]
               for a in range(12) for b in range(12)):
            characters.append(chi)
    assert characters[0] == [1]*12 and len(characters) == 4
    assert all(sum(a*b for a, b in zip(c, d)) == (12 if c == d else 0)
               for c in characters for d in characters)
    return {"identity": identity, "multiplication_table": multiplication,
            "maps_examined_with_identity_value_one": 2048, "characters": characters}


def build(deadline):
    domains, replay, moments, profiles, profile_replay = [read(name) for name in INPUTS]
    assert replay["status"].startswith("PASS") and profile_replay["status"].startswith("PASS")
    orbits, actions = domains["selector_orbits"], domains["signature_actions"]
    assert orbits == moments["selector_orbits"] and actions == moments["selector_actions"]
    group = group_characters(actions)
    column_map = {old: new for new, old in enumerate(domains["new15038_to_original15589"])}
    zeros = set(domains["original_Z_zero_columns"])
    literal_pairs = list(combinations(range(480), 2))
    assert len(literal_pairs) == 114960
    populations, signings, character_records = [], {}, []
    for character, chi in enumerate(group["characters"][1:], start=1):
        supported, unsupported = [], []
        for oi, orbit in enumerate(orbits):
            anchor = orbit[0]
            stabilizer = [g for g, a in enumerate(actions) if a[anchor] == anchor]
            assert len(stabilizer)*len(orbit) == 12
            if any(chi[g] == -1 for g in stabilizer):
                unsupported.append({"selector_orbit": oi, "stabilizer": stabilizer})
                continue
            weights = {a: next(chi[g] for g, move in enumerate(actions) if move[anchor] == a)
                       for a in orbit}
            assert all(weights[move[anchor]] == chi[g] for g, move in enumerate(actions))
            assert all(weights[move[a]] == chi[g]*weights[a]
                       for g, move in enumerate(actions) for a in orbit)
            assert sum(weights.values()) == 0 and set(weights.values()) == {-1, 1}
            local_id = len(populations)
            populations.append({"signed_population": local_id, "character": character,
                                "selector_orbit": oi, "literal_selectors": orbit,
                                "signs": [weights[a] for a in orbit],
                                "anchor": anchor, "stabilizer": stabilizer,
                                "raw_lower": -len(orbit)//2, "raw_upper": len(orbit)//2,
                                "parity_equals_selector_population": True})
            signings[character, oi] = (local_id, weights)
            supported.append(oi)
        character_records.append({"character": character, "values": chi,
                                  "supported_selector_orbits": supported,
                                  "unsupported_selector_orbits": unsupported})
    assert [len(c["supported_selector_orbits"]) for c in character_records] == [38, 42, 38]
    assert len(populations) == 118

    equations, coefficient_visits = [], 0
    pair_orbits = moments["pair_orbits"]
    blocks = domains["pair_orbit_selector_blocks"]
    for character in character_records:
        ci = character["character"]
        rows, removed = defaultdict(list), defaultdict(list)
        for po, members in enumerate(pair_orbits):
            if po % 512 == 0:
                tick(deadline)
            oi, oj = blocks[po]
            if (ci, oi) not in signings or (ci, oj) not in signings:
                continue
            wi, wj = signings[ci, oi][1], signings[ci, oj][1]
            signs = set()
            for k in members:
                a, b = literal_pairs[k]
                if a not in wi:
                    a, b = b, a
                assert a in wi and b in wj
                signs.add(wi[a]*wj[b])
                coefficient_visits += 1
            assert len(signs) == 1
            sign = signs.pop()
            old = 5847+po
            coefficient = sign*(2 if oi == oj else 1)
            if old in zeros:
                removed[oi, oj].append([po, coefficient])
            else:
                rows[oi, oj].append([column_map[old], coefficient])
        for oi, oj in combinations_with_replacement(character["supported_selector_orbits"], 2):
            terms = list(rows[oi, oj])
            if oi == oj:
                terms.append([oi, 1])
            terms.sort()
            assert len({j for j, c in terms}) == len(terms)
            equations.append({"character": ci, "selector_orbits": [oi, oj],
                              "signed_population_factors": [signings[ci, oi][0], signings[ci, oj][0]],
                              "count_terms": terms, "fixed_zero_original_pair_terms": removed[oi, oj],
                              "equation": "sum(count_terms) = product(signed_population_factors)"})
    assert len(equations) == 2385

    # Keep the full joint local information about all supported characters.
    # The old table projection, including multiplicities, must be unchanged.
    refined, accepted, examined = [], 0, 0
    for table in profiles["tables"]:
        oi, orbit = table["selector_orbit"], table["literal_selectors"]
        columns = table["count_columns"]
        index = {j: k for k, j in enumerate(columns)}
        signed = [p for p in populations if p["selector_orbit"] == oi]
        tuples, projected = {}, Counter()
        rejected, mask_stream = Counter(), hashlib.sha256()
        for mask in range(1 << len(orbit)):
            if mask % 256 == 0:
                tick(deadline)
            examined += 1
            if any(mask & p["local_mask"] == p["local_mask"] for p in table["forced_zero_literal_pairs"]):
                rejected["proved_pair_zero"] += 1
                continue
            if any((mask & c["local_support_mask"]).bit_count() > c["quota"]
                   for c in table["nontrivial_original_Gram_capacities"]):
                rejected["original_Gram_capacity"] += 1
                continue
            counts = [mask.bit_count()]+[0]*(len(columns)-1)
            for pair in table["retained_literal_pair_map"]:
                if mask & pair["local_mask"] == pair["local_mask"]:
                    counts[index[pair["count_column"]]] += 1
            values = [sum(w for j, w in enumerate(p["signs"]) if mask >> j & 1) for p in signed]
            assert all((v-counts[0]) % 2 == 0 and abs(v) <= min(counts[0], len(orbit)-counts[0])
                       for v in values)
            key = tuple(counts+values)
            if key not in tuples:
                tuples[key] = {"counts_and_signed_populations": list(key),
                               "representative_local_mask": mask, "literal_subset_count": 0}
            tuples[key]["literal_subset_count"] += 1
            projected[tuple(counts)] += 1
            accepted += 1
            mask_stream.update(canonical([mask, list(key)])+b"\n")
        assert projected == Counter({tuple(p["counts"]): p["literal_subset_count"] for p in table["profiles"]})
        assert rejected == Counter({k: v for k, v in table["subsets_by_disposition"].items()
                                    if k != "accepted_local_subset"})
        diagonal = [e for e in equations if e["selector_orbits"] == [oi, oi]]
        for key in tuples:
            point = dict(zip(columns, key[:len(columns)]))
            signed_point = dict(zip([p["signed_population"] for p in signed], key[len(columns):]))
            for equation in diagonal:
                a, b = equation["signed_population_factors"]
                assert a == b
                assert sum(c*point[j] for j, c in equation["count_terms"]) == signed_point[a]**2
        refined.append({"selector_orbit": oi, "count_columns": columns,
                        "signed_population_columns": [p["signed_population"] for p in signed],
                        "base_profile_count": len(table["profiles"]),
                        "accepted_literal_subsets": sum(projected.values()),
                        "profiles": [tuples[k] for k in sorted(tuples)],
                        "accepted_mask_and_profile_stream_sha256": mask_stream.hexdigest(),
                        "exact_original_table_projection_checked": True,
                        "all_character_square_equations_checked": len(diagonal)})
    assert examined == 155904 and accepted == 64144
    tick(deadline)
    return {"schema": "conway99.f0-real-character-populations.v1",
            "status": "COMPLETE_EXACT_CHARACTER_PRODUCT_AND_LOCAL_PROFILE_PREPARATION",
            "source_sha256": sha(Path(__file__).read_bytes()),
            "inputs": {k: {"path": "experiments/logs/root-prism-free/"+v[0], "sha256": v[1]}
                       for k, v in INPUTS.items()},
            "group": group, "nontrivial_characters": character_records,
            "signed_populations": populations, "signed_population_count": len(populations),
            "product_equations": equations, "product_equation_count": len(equations),
            "literal_pair_coefficient_checks": coefficient_visits,
            "product_equation_count_terms": sum(len(e["count_terms"]) for e in equations),
            "local_tables": refined, "refined_profile_tuples": sum(len(t["profiles"]) for t in refined),
            "literal_subsets_examined": examined, "accepted_literal_subsets": accepted,
            "count_model_variables": 15038, "signed_population_IDs_are_separate_local_namespace": True,
            "graph_automorphism_assumed": False, "solver_calls": 0, "optimizer_calls": 0,
            "F0_excluded": False, "global_incidence_claimed": False,
            "validity": "For a compatible signing w_i, w_i(g(a))=chi(g)w_i(a). Thus L_i=sum(w_i(a)z_a) transforms by chi(g), and L_i*L_j is unchanged under group averaging. Its literal pair expansion has constant coefficients on each pair orbit. Only proved-zero pair populations are removed. The refined local tables enumerate all allowed literal subsets and preserve the full old projection.",
            "scope": "Necessary products for the three nontrivial real one-dimensional characters and exact within-orbit signed profiles. Higher-dimensional representations and cross-orbit literal compatibility are not imposed."}


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
        result = {"status": "PASS: complete character products and refined local profiles replayed",
                  "source_sha256": sha(Path(__file__).read_bytes()), "record_sha256": sha(raw),
                  "signed_population_count": result["signed_population_count"],
                  "product_equation_count": result["product_equation_count"],
                  "refined_profile_tuples": result["refined_profile_tuples"],
                  "solver_calls": 0, "optimizer_calls": 0, "seconds": time.monotonic()-started}
    raw = canonical(result)+b"\n"
    if str(args.output).endswith(".gz"):
        raw = gzip.compress(raw, mtime=0)
    with args.output.open("xb") as handle:
        handle.write(raw)
    print(json.dumps({"status": result["status"], "sha256": sha(raw),
                      "signed_populations": result["signed_population_count"],
                      "product_equations": result["product_equation_count"],
                      "profiles": result["refined_profile_tuples"],
                      "seconds": time.monotonic()-started}, indent=2), flush=True)
