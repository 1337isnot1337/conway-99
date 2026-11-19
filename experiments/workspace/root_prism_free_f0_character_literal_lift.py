"""Complete inverse character-profile tables and a future selector-moment lift.

Preparation only: no real count candidate or optimizer is queried by the CLI.
The fixed-candidate CSP realizes N, original Z populations, and signed sums.
Exterior edge populations Y and a graph completion are outside its scope.
"""
import argparse
from collections import Counter, defaultdict
import gzip
import hashlib
from itertools import combinations
import json
from pathlib import Path
import time

import root_prism_free_f0_literal_lift_csp as csp

ROOT = Path(__file__).resolve().parents[2]
PREFIX = "experiments/logs/root-prism-free/"
INPUTS = {
    "domains": ("f0-orbit-populations02-domains.json.gz", "4f079468530dba0746512cc4afce01666b2a63a2c8f35f66a4660a4fe3bab8ab"),
    "domain_replay": ("f0-orbit-populations02-independent-replay.json", "a8bb55cbf773ea75a8cd1d5a18b50281ecbe08f6074cea04fb2d75799138273a"),
    "moments": ("f0-second-moments-preparation02.json.gz", "404d91da35c798ba248887c22a7500957947e24b71d5197dc44432460e6d219e"),
    "profiles": ("f0-selector-orbit-profiles01.json.gz", "93c891e7eef037e5869e5c8e13c3cf31d0ad253cb6caf5cd38930b09715e085d"),
    "profile_replay": ("f0-selector-orbit-profiles01-cold.json", "cb10cd7dc77236d9caed7c7b8a410a33f7b998bea8d257b500d3c9f8561a76f8"),
    "characters": ("f0-character-populations01.json.gz", "139d06a3383f8fc79d677972ce052ce29966e8b3406e7d1e7d1077aea7c2cef6"),
    "character_replay": ("f0-character-populations01-cold.json", "1fdc14c0bda54f0b5e63b23a3b7d5f85d9afd92ea418b4931d53b644444e814b"),
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def read_context(root=ROOT):
    data = {}
    for name, (path, digest) in INPUTS.items():
        raw = (root / PREFIX / path).read_bytes()
        assert sha(raw) == digest, name
        data[name] = json.loads(gzip.decompress(raw) if path.endswith(".gz") else raw)
    for name in ("domain_replay", "profile_replay", "character_replay"):
        assert data[name]["status"].startswith("PASS"), name
    return data


def tick(deadline):
    if time.monotonic() >= deadline:
        raise TimeoutError("literal-lift preparation deadline")


def pair_id(a, b):
    if a > b:
        a, b = b, a
    assert 0 <= a < b < 480
    return a * (959 - a) // 2 + b - a - 1


def selected_positions(mask):
    return list(csp.bits(mask))


def prepare_inverse(context, deadline, completed=None):
    domains, moments, profiles, characters = [
        context[k] for k in ("domains", "moments", "profiles", "characters")]
    orbits = domains["selector_orbits"]
    assert len(orbits) == 42 and orbits == moments["selector_orbits"]
    assert sorted(a for orbit in orbits for a in orbit) == list(range(480))
    owners = [None] * 480
    for oi, orbit in enumerate(orbits):
        assert orbit == sorted(set(orbit)) and len(orbit) in (6, 12)
        for a in orbit:
            owners[a] = oi
    old_to_new = {old: new for new, old in enumerate(domains["new15038_to_original15589"])}
    assert len(old_to_new) == 15038 and all(old_to_new[i] == i for i in range(42))
    zero_pairs = {old - 5847 for old in domains["original_Z_zero_columns"]}
    assert len(zero_pairs) == 389 and min(zero_pairs) >= 0
    pmap = moments["pair_to_orbit"]
    pair_orbits = moments["pair_orbits"]
    assert len(pmap) == 114960 and len(pair_orbits) == 9742
    assert sorted(k for members in pair_orbits for k in members) == list(range(114960))
    assert all(pmap[k] == po for po, members in enumerate(pair_orbits) for k in members)
    block_ids = defaultdict(list)
    for po, block in enumerate(domains["pair_orbit_selector_blocks"]):
        i, j = block
        assert 0 <= i <= j < 42
        block_ids[i, j].append(po)
    # Independently classify every literal pair by its two selector owners.
    for a, b in combinations(range(480), 2):
        po = pmap[pair_id(a, b)]
        assert domains["pair_orbit_selector_blocks"][po] == sorted([owners[a], owners[b]])
    tables, histogram, accepted_total = [], Counter(), 0
    max_populations = []
    for oi, (base, refined) in enumerate(zip(profiles["tables"], characters["local_tables"])):
        tick(deadline)
        orbit = orbits[oi]
        assert base["selector_orbit"] == refined["selector_orbit"] == oi
        assert base["literal_selectors"] == orbit
        assert base["count_columns"] == refined["count_columns"]
        columns = refined["count_columns"]
        assert columns[0] == oi
        count_position = {j: k for k, j in enumerate(columns)}
        signing_ids = refined["signed_population_columns"]
        signings = [characters["signed_populations"][j] for j in signing_ids]
        assert all(p["selector_orbit"] == oi and p["literal_selectors"] == orbit
                   and p["signed_population"] == j for p, j in zip(signings, signing_ids))
        local_position = {a: i for i, a in enumerate(orbit)}
        capacities = []
        for ri, row in enumerate(moments["original_selector_equalities"][:171]):
            support_mask = sum(1 << local_position[a] for a in row["support"] if a in local_position)
            if support_mask.bit_count() > row["quota"]:
                capacities.append({"original_Gram_row": ri, "local_support_mask": support_mask,
                                   "quota": row["quota"], "core_pair": row["core_pair"]})
        assert capacities == base["nontrivial_original_Gram_capacities"]
        local_pairs, forbidden = [], []
        for u, v in combinations(range(len(orbit)), 2):
            po = pmap[pair_id(orbit[u], orbit[v])]
            mask = (1 << u) | (1 << v)
            if po in zero_pairs:
                forbidden.append(mask)
            else:
                local_pairs.append((mask, old_to_new[5847 + po]))
        assert forbidden == [p["local_mask"] for p in base["forced_zero_literal_pairs"]]
        inverse = defaultdict(list)
        disposition = Counter()
        old_stream, signed_stream = hashlib.sha256(), hashlib.sha256()
        for mask in range(1 << len(orbit)):
            if mask % 256 == 0:
                tick(deadline)
            if any(mask & f == f for f in forbidden):
                disposition["proved_pair_zero"] += 1
                old_stream.update(canonical([mask, "proved_pair_zero"]) + b"\n")
                continue
            failed = next((c for c in capacities
                           if (mask & c["local_support_mask"]).bit_count() > c["quota"]), None)
            if failed is not None:
                disposition["original_Gram_capacity"] += 1
                old_stream.update(canonical([mask, "original_Gram_capacity",
                                              failed["original_Gram_row"]]) + b"\n")
                continue
            counts = [mask.bit_count()] + [0] * (len(columns) - 1)
            for pairmask, column in local_pairs:
                if mask & pairmask == pairmask:
                    counts[count_position[column]] += 1
            assert sum(counts[1:]) == counts[0] * (counts[0] - 1) // 2
            signed = [sum(p["signs"][j] for j in selected_positions(mask)) for p in signings]
            key = tuple(counts + signed)
            inverse[key].append(mask)
            disposition["accepted_local_subset"] += 1
            old_stream.update(canonical([mask, counts]) + b"\n")
            signed_stream.update(canonical([mask, list(key)]) + b"\n")
        assert dict(disposition) == base["subsets_by_disposition"]
        assert old_stream.hexdigest() == base["all_subset_dispositions_sha256"]
        assert signed_stream.hexdigest() == refined["accepted_mask_and_profile_stream_sha256"]
        assert sorted(inverse) == [tuple(p["counts_and_signed_populations"]) for p in refined["profiles"]]
        entries = []
        for ti, profile in enumerate(refined["profiles"]):
            key = tuple(profile["counts_and_signed_populations"])
            masks = inverse[key]
            assert masks == sorted(set(masks))
            assert len(masks) == profile["literal_subset_count"]
            assert masks[0] == profile["representative_local_mask"]
            entries.append({"tuple_index": ti, "counts_and_signed_populations": list(key),
                            "local_masks": masks})
            histogram[len(masks)] += 1
        all_masks = [mask for entry in entries for mask in entry["local_masks"]]
        assert len(all_masks) == len(set(all_masks)) == refined["accepted_literal_subsets"]
        accepted_total += len(all_masks)
        max_populations.append(max(mask.bit_count() for mask in all_masks))
        tables.append({"selector_orbit": oi, "literal_selectors": orbit,
                       "count_columns": columns,
                       "signed_population_columns": signing_ids,
                       "profiles": entries,
                       "accepted_literal_masks": len(all_masks),
                       "maximum_tuple_preimages": max(len(e["local_masks"]) for e in entries)})
        if completed is not None:
            completed.append({"selector_orbit": oi, "tuples": len(entries),
                              "accepted_literal_masks": len(all_masks)})
    assert len(tables) == 42 and accepted_total == 64144
    assert sum(histogram.values()) == 19331
    assert histogram == {1: 418, 3: 17280, 6: 1237, 9: 96, 12: 300}
    cross = []
    for i, j in combinations(range(42), 2):
        grid = [[pmap[pair_id(a, b)] for b in orbits[j]] for a in orbits[i]]
        used = sorted({po for row in grid for po in row})
        assert used == block_ids[i, j]
        assert Counter(po for row in grid for po in row) == {
            po: len(pair_orbits[po]) for po in used}
        cross.append({"selector_orbits": [i, j], "original_pair_orbits": used,
                      "literal_pair_orbit_grid": grid,
                      "proved_zero_pair_orbits": [po for po in used if po in zero_pairs]})
    within_ids = sorted(po for (i, j), ids in block_ids.items() if i == j for po in ids)
    cross_ids = sorted(po for block in cross for po in block["original_pair_orbits"])
    assert len(cross) == 861 and sorted(within_ids + cross_ids) == list(range(9742))
    bound_choices = sum(tables[i]["maximum_tuple_preimages"] * tables[j]["maximum_tuple_preimages"]
                        for i, j in combinations(range(42), 2))
    bound_literal_visits = sum(tables[i]["maximum_tuple_preimages"] * tables[j]["maximum_tuple_preimages"]
                              * max_populations[i] * max_populations[j]
                              for i, j in combinations(range(42), 2))
    return {
        "schema": "conway99.f0-character-literal-lift-preparation.v1",
        "status": "COMPLETE_INVERSE_TABLE_AND_BINARY_CSP_PREPARATION",
        "sources": {"domain": sha(Path(__file__).read_bytes()),
                    "csp_kernel": sha(Path(csp.__file__).read_bytes())},
        "inputs": {k: {"path": PREFIX + p, "sha256": h} for k, (p, h) in INPUTS.items()},
        "inverse_tables": tables, "cross_pair_blocks": cross,
        "original_zero_pair_orbits": sorted(zero_pairs),
        "original_within_pair_orbits": within_ids,
        "original_pair_orbit_sizes": [len(x) for x in pair_orbits],
        "literal_selector_to_orbit": owners,
        "new15038_to_original15589": domains["new15038_to_original15589"],
        "inventory": {"selector_orbits": 42, "literal_selectors": 480,
                      "refined_tuples": 19331, "accepted_literal_masks": accepted_total,
                      "tuple_preimage_histogram": {str(k): v for k, v in sorted(histogram.items())},
                      "maximum_domain_size": 12, "binary_constraints": 861,
                      "original_pair_orbits": 9742, "within_pair_orbits": len(within_ids),
                      "cross_pair_orbits": len(cross_ids), "proved_zero_pair_orbits": 389,
                      "cross_literal_pairs": sum(len(orbits[i]) * len(orbits[j])
                                                 for i, j in combinations(range(42), 2)),
                      "candidate_choice_pair_bound_from_per_orbit_maxima": bound_choices,
                      "candidate_literal_histogram_visit_bound": bound_literal_visits,
                      "all_production_candidates_queried": 0, "optimizer_calls": 0},
        "scope": "Complete preimages of the saved local refined profiles. A candidate-specific binary CSP realizes N, every original Z pair population including zeros, and the oriented signed sums. Exterior Y edges are not realized. Original selector equalities are checked separately on every returned literal witness. Rejection concerns only one fixed count assignment."
    }


def exact_integer(value):
    if type(value) is int:
        return value
    assert isinstance(value, str) and value and value not in ("-0", "+0")
    parsed = int(value)
    assert str(parsed) == value
    return parsed


def normalized_projection(preparation, candidate):
    result = {}
    for name, length in (("selector_populations", 42), ("original_pair_populations", 9742),
                         ("signed_populations", 118)):
        assert isinstance(candidate[name], list) and len(candidate[name]) == length
        result[name] = [exact_integer(x) for x in candidate[name]]
    assert all(0 <= n <= len(t["literal_selectors"])
               for n, t in zip(result["selector_populations"], preparation["inverse_tables"]))
    assert all(0 <= p <= size for p, size in zip(result["original_pair_populations"],
                                                preparation["original_pair_orbit_sizes"]))
    assert all(result["original_pair_populations"][po] == 0
               for po in preparation["original_zero_pair_orbits"])
    assert all(-6 <= x <= 6 for x in result["signed_populations"])
    return result


def projection_from_count_columns(preparation, count_populations, signed_populations):
    """Exact adapter: Y is deliberately omitted, never interpreted as selector pairs."""
    assert len(count_populations) == 15038
    counts = [exact_integer(x) for x in count_populations]
    pairs = [0] * 9742
    for new, old in enumerate(preparation["new15038_to_original15589"]):
        if old >= 5847:
            pairs[old - 5847] = counts[new]
    return normalized_projection(preparation, {
        "selector_populations": counts[:42], "original_pair_populations": pairs,
        "signed_populations": signed_populations})


def candidate_problem(preparation, candidate, seconds=30):
    """Build exact binary relations only; do not search a production candidate."""
    deadline = time.monotonic() + seconds
    point = normalized_projection(preparation, candidate)
    Ns, Ps, Ls = [point[k] for k in ("selector_populations", "original_pair_populations", "signed_populations")]
    current_to_old = preparation["new15038_to_original15589"]
    chosen, tuple_ids, missing = [], [], []
    for table in preparation["inverse_tables"]:
        values = [Ns[j] if j < 42 else Ps[current_to_old[j] - 5847]
                  for j in table["count_columns"]]
        values += [Ls[j] for j in table["signed_population_columns"]]
        match = next((p for p in table["profiles"] if p["counts_and_signed_populations"] == values), None)
        chosen.append([] if match is None else match["local_masks"])
        tuple_ids.append(None if match is None else match["tuple_index"])
        if match is None:
            missing.append({"selector_orbit": table["selector_orbit"], "required_tuple": values})
    relations, comparisons = [], 0
    for block in preparation["cross_pair_blocks"]:
        tick(deadline)
        i, j = block["selector_orbits"]
        grid = block["literal_pair_orbit_grid"]
        target = {po: Ps[po] for po in block["original_pair_orbits"] if Ps[po]}
        rows = []
        for a in chosen[i]:
            allowed = 0
            for index, b in enumerate(chosen[j]):
                counts = Counter(grid[u][v] for u in selected_positions(a)
                                 for v in selected_positions(b))
                comparisons += 1
                if dict(counts) == target:
                    allowed |= 1 << index
            rows.append(allowed)
        relations.append({"variables": [i, j], "rows": rows})
    problem = {"domain_sizes": list(map(len, chosen)), "relations": relations}
    csp.canonical_problem(problem)
    return {"projection": point, "projection_sha256": sha(canonical(point)),
            "local_tuple_indices": tuple_ids, "literal_mask_domains": chosen,
            "missing_local_profiles": missing, "problem": problem,
            "problem_sha256": sha(canonical(problem)),
            "choice_pair_comparisons": comparisons,
            "all_original_zero_pair_targets_explicit": True,
            "independent_local_relabeling_used": False, "exterior_Y_edges_in_scope": False}


def projection_of_selection(preparation, context, selected):
    selected = sorted(selected)
    assert selected == sorted(set(selected)) and all(type(a) is int and 0 <= a < 480 for a in selected)
    Ns, Ps = [0] * 42, [0] * 9742
    for a in selected:
        Ns[preparation["literal_selector_to_orbit"][a]] += 1
    pmap = context["moments"]["pair_to_orbit"]
    for a, b in combinations(selected, 2):
        Ps[pmap[pair_id(a, b)]] += 1
    chosen = set(selected)
    Ls = [sum(w for a, w in zip(p["literal_selectors"], p["signs"]) if a in chosen)
          for p in context["characters"]["signed_populations"]]
    return {"selector_populations": Ns, "original_pair_populations": Ps, "signed_populations": Ls}


def verify_literal_witness(preparation, context, bundle, assignment):
    csp.check_assignment(bundle["problem"], assignment)
    selected, masks = [], []
    for i, value in enumerate(assignment):
        mask = bundle["literal_mask_domains"][i][value]
        masks.append(mask)
        orbit = preparation["inverse_tables"][i]["literal_selectors"]
        selected.extend(orbit[j] for j in selected_positions(mask))
    selected.sort()
    actual = projection_of_selection(preparation, context, selected)
    assert actual == bundle["projection"]
    # Directly check all original rows. Moment realization alone must not be
    # mislabeled a complete selector-incidence solution, let alone a graph.
    selected_set = set(selected)
    checks = [{"row": ri, "observed": sum(a in selected_set for a in row["support"]),
               "required": row["quota"]}
              for ri, row in enumerate(context["moments"]["original_selector_equalities"])]
    assert len(checks) == 172
    failures = [r for r in checks if r["observed"] != r["required"]]
    return {"status": "EXACT_LITERAL_SELECTOR_MOMENT_LIFT",
            "selected_literal_signatures": selected, "local_masks": masks,
            "selector_population_checks": 42, "original_pair_population_checks": 9742,
            "signed_population_checks": 118,
            "proved_zero_pair_checks": len(preparation["original_zero_pair_orbits"]),
            "original_selector_equalities": checks,
            "all_original_selector_equalities_pass": not failures,
            "failed_original_selector_row_ids": [r["row"] for r in failures],
            "exterior_Y_edges_realized": False, "graph_completion_claimed": False}


def reconstruction_controls(preparation, context):
    # Tiny synthetic selector subsets exercise the actual pair maps and fixed
    # character orientation. They are not proposed 60-vertex incidences.
    zeros = set(preparation["original_zero_pair_orbits"])
    first = preparation["inverse_tables"][0]["literal_selectors"][0]
    pair = next([first, b] for table in preparation["inverse_tables"][1:]
                for b in table["literal_selectors"]
                if context["moments"]["pair_to_orbit"][pair_id(first, b)] not in zeros)
    records = []
    for selected in ([], [first], pair):
        point = projection_of_selection(preparation, context, selected)
        bundle = candidate_problem(preparation, point)
        result = csp.solve(bundle["problem"], seconds=2, maximum_nodes=256)
        assert result["status"] == "SAT"
        replay = csp.replay(bundle["problem"], result)
        witness = verify_literal_witness(preparation, context, bundle, result["assignment"])
        assert not witness["all_original_selector_equalities_pass"]
        records.append({"synthetic_selection": selected, "projection_sha256": bundle["projection_sha256"],
                        "candidate_domain_sizes": bundle["problem"]["domain_sizes"],
                        "CSP_status": result["status"], "CSP_replay": replay,
                        "exact_witness": witness})
    bad = projection_of_selection(preparation, context, pair)
    po = context["moments"]["pair_to_orbit"][pair_id(*pair)]
    assert bad["original_pair_populations"][po] == 1
    bad["original_pair_populations"][po] = 0
    bundle = candidate_problem(preparation, bad)
    assert not bundle["missing_local_profiles"]
    result = csp.solve(bundle["problem"], seconds=2, maximum_nodes=256)
    assert result["status"] == "UNSAT"
    replay = csp.replay(bundle["problem"], result)
    return {"synthetic_positive_reconstructions": records,
            "negative_control": {"modified_original_pair_orbit": po,
                                 "fixed_pair_target": 0, "local_profiles_all_present": True,
                                 "projection_sha256": bundle["projection_sha256"],
                                 "problem_sha256": bundle["problem_sha256"],
                                 "result": result, "replay": replay},
            "synthetic_sets_are_graph_incidence_candidates": False,
            "production_candidates_evaluated": 0}


def write(path, value):
    raw = canonical(value) + b"\n"
    if str(path).endswith(".gz"):
        raw = gzip.compress(raw, mtime=0)
    with path.open("xb") as out:
        out.write(raw)
    return sha(raw)


def replay_reconstruction_controls(preparation, context, saved):
    """Check saved literal witnesses and the negative tree, without searching."""
    positives = saved["synthetic_positive_reconstructions"]
    assert len(positives) == 3
    for record in positives:
        point = projection_of_selection(preparation, context, record["synthetic_selection"])
        bundle = candidate_problem(preparation, point)
        assert bundle["projection_sha256"] == record["projection_sha256"]
        assert bundle["problem"]["domain_sizes"] == record["candidate_domain_sizes"]
        masks = record["exact_witness"]["local_masks"]
        assignment = [domain.index(mask) for domain, mask in zip(bundle["literal_mask_domains"], masks)]
        assert verify_literal_witness(preparation, context, bundle, assignment) == record["exact_witness"]
    negative = saved["negative_control"]
    point = projection_of_selection(preparation, context, positives[-1]["synthetic_selection"])
    po = negative["modified_original_pair_orbit"]
    assert point["original_pair_populations"][po] == 1 and negative["fixed_pair_target"] == 0
    point["original_pair_populations"][po] = 0
    bundle = candidate_problem(preparation, point)
    assert not bundle["missing_local_profiles"]
    assert bundle["projection_sha256"] == negative["projection_sha256"]
    assert bundle["problem_sha256"] == negative["problem_sha256"]
    assert csp.replay(bundle["problem"], negative["result"]) == negative["replay"]
    assert negative["result"]["status"] == "UNSAT"
    return {"positive_literal_witnesses": len(positives), "negative_CSP_trees": 1,
            "synthetic_searches_repeated": False, "optimizer_calls": 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "replay"))
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--record", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seconds", type=float, default=30)
    args = parser.parse_args()
    assert 0 < args.seconds <= 60
    started = time.monotonic()
    completed = []
    try:
        context = read_context(args.root)
        result = prepare_inverse(context, started + args.seconds, completed)
        if args.mode == "replay":
            assert args.record is not None
            raw = args.record.read_bytes()
            saved = json.loads(gzip.decompress(raw) if str(args.record).endswith(".gz") else raw)
            assert {k: v for k, v in saved.items() if k not in
                    ("kernel_controls", "reconstruction_controls")} == result
            checked = replay_reconstruction_controls(result, context, saved["reconstruction_controls"])
            result = {"status": "PASS: inverse tables, complete pair coverage and saved literal/CSP witnesses replayed",
                      "source_sha256": sha(Path(__file__).read_bytes()),
                      "record_sha256": sha(raw), "inventory": result["inventory"],
                      "saved_control_witnesses": checked, "kernel_controls_repeated": False,
                      "production_candidates_evaluated": 0, "optimizer_calls": 0,
                      "seconds": time.monotonic() - started}
        else:
            result["kernel_controls"] = csp.controls()
            result["reconstruction_controls"] = reconstruction_controls(result, context)
        tick(started + args.seconds)
    except Exception as error:
        result = {"status": "INCOMPLETE_PREPARATION" if isinstance(error, TimeoutError) else "PREPARATION_ERROR",
                  "source_sha256": sha(Path(__file__).read_bytes()),
                  "exception_type": type(error).__name__, "exception": str(error),
                  "completed_tables": completed, "seconds": time.monotonic() - started,
                  "production_candidates_evaluated": 0, "optimizer_calls": 0}
        write(args.output, result)
        raise
    digest = write(args.output, result)
    print(json.dumps({"status": result["status"], "sha256": digest,
                      "inventory": result["inventory"], "seconds": time.monotonic() - started}, indent=2))


if __name__ == "__main__":
    main()
