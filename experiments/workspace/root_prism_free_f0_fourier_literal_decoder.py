"""Independent exact decoding of abstract F0 Fourier/count projections.

Only preparation and its replay are exposed by the CLI. No future native
namespace, model hash, accepted receipt or production candidate is assumed.
The pure decoder separates moment realization, literal selector obligations,
finite count acceptance and exterior-edge realization.
"""
import argparse
from collections import Counter
from copy import deepcopy
import gzip
from hashlib import sha256
from itertools import combinations
import json
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "experiments/logs/root-prism-free"
INPUTS = {
    "scope": ("f0-two-dimensional-moments-scope01.json", "948e256945fc817cc75ea46c969c055b21e61832a4f2177c481884e73338223f"),
    "factorization": ("f0-nonabelian-pair-factorization01.json.gz", "627577aea4a25c15e5d2846242adda9c6b7c97164b7ba47fb9a2cab5d3988fd8"),
    "inverse": ("f0-character-literal-lift-preparation01.json.gz", "241cd14c61b465025c72ffcaa65af8e5c48e9e5a0eda7ea7d252e9d74b22db1e"),
    "inverse_cold": ("f0-character-literal-lift-preparation01-cold.json", "6cebe725527eaf28f3d075a3ad9741fcbcf50cdedd42107bdc5ebcbe857da72f"),
    "moments": ("f0-second-moments-preparation02.json.gz", "404d91da35c798ba248887c22a7500957947e24b71d5197dc44432460e6d219e"),
    "moment_cold": ("f0-second-moments-preparation02-cold-replay.json", "e495dbc7281f420caab1f3be88e9263ab8273da6ae88a7ea4e1e72c30eaa1fcd"),
    "characters": ("f0-character-populations01.json.gz", "139d06a3383f8fc79d677972ce052ce29966e8b3406e7d1e7d1077aea7c2cef6"),
    "literal_model": ("f0-boolean-fractional-model.json.gz", "703206929c9c85a40ac4ddcbfb1708c716c288482cf50c77a32249404e35b782"),
    "motifs": ("f0-pair-clauses.json.gz", "47e9d8f518fab10aee604f33df1f22c97b0d201a1af4180e4307553e4857672f"),
}
SOURCES_READ = {
    "factorization": ("root_prism_free_f0_nonabelian_pair_factorization.py", "790a929c65898d2a3bb038c9877d73dc022aa9c66d3983efe8a77ad833383871"),
    "incidence": ("root_prism_free_f0_incidence.py", "00cd6e683a8bfb602cfd29f8dbb3481be0f87df55f2963ae98613f2af9146971"),
    "motif": ("root_prism_free_f0_pair_clauses.py", "367b7f850d087067b547653d31bf4b25743f30934583252de1199cffb358daac"),
    "Boolean_inspector": ("root_prism_free_f0_boolean_fractional_model.js", "250cae6a3358d04df1f558ab4f31a641919718e59ffc7039438114de56425b8d"),
    "baseline_inspector": ("root_prism_free_f0_fractional_baseline_recovery.js", "2c7f4cf9965426d97eb025793d5912d2b51cc56dc9fced76fd66219333263af1"),
    "old_literal_lift": ("root_prism_free_f0_character_literal_lift.py", "3bf7f92502592bcda0b4dc71868a6745888c608b26d3f8e42f2771cf180c7252"),
}
REPRESENTATIONS = ["central_plus", "central_minus"]
ABSTRACT_SCHEMA = "conway99.f0.abstract-Fourier-selector-projection.v1"
LIMITS = {"seconds_per_preparation_or_replay": 60, "maximum_raw_record_bytes": 16 << 20,
          "existing_inverse_masks": 64144, "new_selector_subsets": 0,
          "optimizer_calls": 0, "production_candidate_calls": 0}


def sha(raw):
    return sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def tick(deadline):
    if time.monotonic() >= deadline:
        raise TimeoutError("abstract Fourier decoder preparation deadline")


def read(key):
    name, expected = INPUTS[key]
    raw = (BASE/name).read_bytes()
    assert sha(raw) == expected, key
    return json.loads(gzip.decompress(raw) if name.endswith(".gz") else raw)


def decimal(value):
    assert isinstance(value, str) and str(int(value)) == value
    return int(value)


def pair_id(a, b):
    a, b = sorted((a, b))
    assert 0 <= a < b < 480
    return a*(959-a)//2+b-a-1


def matrix_trace_product(a, b):
    return sum(a[i][j]*b[j][i] for i in range(2) for j in range(2))


def caps_failures(rows):
    return [[i, j, (rows[i]&rows[j]).bit_count(), 2-((rows[i] >> j)&1)]
            for i in range(len(rows)) for j in range(i)
            if (rows[i]&rows[j]).bit_count() > 2-((rows[i] >> j)&1)]


def induced(rows, sites):
    assert len(sites) == len(set(sites))
    return [sum(((rows[a] >> b)&1) << j for j, b in enumerate(sites)) for a in sites]


def motif_shape(rows, kind):
    if kind == "P":
        return len(rows) == 6 and all(r.bit_count() == 3 for r in rows) and all(
            (rows[a] >> b)&1 for part in (range(3), range(3, 6)) for a, b in combinations(part, 2)) and all(
            sum((rows[a] >> b)&1 for b in range(3, 6)) == 1 for a in range(3))
    if len(rows) != 10 or [r.bit_count() for r in rows] != [5, 5]+[3]*8 or not (rows[0]&2):
        return False
    if any((rows[a]&3).bit_count() != 1 for a in range(2, 10)):
        return False
    shell = list(range(2, 10))
    if any(sum((rows[a] >> b)&1 for b in shell) != 2 or
           sum((rows[a] >> b)&1 for b in shell if (rows[b]&3) == (rows[a]&3)) != 1 for a in shell):
        return False
    reached, pending = {2}, [2]
    while pending:
        a = pending.pop()
        for b in shell:
            if (rows[a] >> b)&1 and b not in reached:
                reached.add(b); pending.append(b)
    return len(reached) == 8


def load_context(deadline):
    for name, expected in SOURCES_READ.values():
        assert sha((ROOT/"experiments/workspace"/name).read_bytes()) == expected, name
    scope, factor, inverse, inverse_cold = [read(k) for k in ("scope", "factorization", "inverse", "inverse_cold")]
    assert inverse_cold["record_sha256"] == INPUTS["inverse"][1] and inverse_cold["status"].startswith("PASS")
    assert factor["source_sha256"] == SOURCES_READ["factorization"][1]
    moments, cold = read("moments"), read("moment_cold")
    assert cold["artifact_sha256"] == INPUTS["moments"][1] and cold["status"].startswith("PASS")
    moments = {k: moments[k] for k in ("selector_actions", "selector_orbits", "pair_to_orbit", "pair_orbits",
                                      "zero_pair_orbits", "zero_moment_certificates", "original_selector_equalities")}
    chars = read("characters")
    chars = {"group": chars["group"], "signed_populations": chars["signed_populations"]}
    model = read("literal_model")
    validation, literal_rows = model["validation"], model["Boolean_validation"]["full_rows"]
    del model
    validation = {k: validation[k] for k in ("core", "triples", "selector_orbits", "motif_pairs")}
    motif_record = read("motifs")["representatives"][0]
    orbits, actions = moments["selector_orbits"], moments["selector_actions"]
    assert len(orbits) == 42 and sorted(a for o in orbits for a in o) == list(range(480))
    assert orbits == validation["selector_orbits"]
    assert [t["literal_selectors"] for t in inverse["inverse_tables"]] == orbits
    table = scope["group"]["multiplication_table"]
    assert table == chars["group"]["multiplication_table"]
    group_inverse = [next(h for h in range(12) if table[g][h] == table[h][g] == 0) for g in range(12)]
    transports = [{a: next(g for g, move in enumerate(actions) if move[o[0]] == a) for a in o} for o in orbits]
    assert [[[a, t[a]] for a in sorted(t)] for t in transports] == factor["literal_transports"]
    one_d = chars["group"]["characters"]
    rep_matrices = {name: scope["two_dimensional_representations"][name]["matrices"] for name in REPRESENTATIONS}
    signed_index = {(p["selector_orbit"], p["character"]): j for j, p in enumerate(chars["signed_populations"])}
    assert len(signed_index) == 118
    for (oi, ci), j in signed_index.items():
        p = chars["signed_populations"][j]
        assert p["literal_selectors"] == orbits[oi]
        assert p["signs"] == [one_d[ci][transports[oi][a]] for a in orbits[oi]]
    layouts, local_columns = {}, [[] for _ in range(42)]
    for name in REPRESENTATIONS:
        layouts[name] = []
        for c in factor["Fourier_columns_in_a_b_coordinates"][name]:
            oi, k, j = c["selector_orbit"], c["matrix_column"], c["column_index"]
            assert j == len(layouts[name]) and k in (0, 1)
            expected = [[a, 2*rep_matrices[name][transports[oi][a]][0][k]-rep_matrices[name][transports[oi][a]][1][k],
                         rep_matrices[name][transports[oi][a]][1][k]] for a in orbits[oi]]
            assert expected == c["literal_a_b_coefficients"]
            layouts[name].append({"column_index": j, "selector_orbit": oi, "matrix_column": k})
            local_columns[oi].append((name, j, k))
    assert {name: len(v) for name, v in layouts.items()} == {"central_plus": 84, "central_minus": 76}
    zero_ids = set(inverse["original_zero_pair_orbits"])
    assert len(zero_ids) == 389 and zero_ids == set(moments["zero_pair_orbits"])
    zeros = moments["zero_moment_certificates"]
    assert len(zeros) == 4410 and len({z["pair_id"] for z in zeros}) == 4410
    assert {z["pair_id"] for z in zeros} == {p for oi in zero_ids for p in moments["pair_orbits"][oi]}
    by_kind = Counter()
    for z in zeros:
        a, b = sorted((z["anchor"], z["other"]))
        assert pair_id(a, b) == z["pair_id"]
        by_kind[z["kind"]] += 1
        if z["kind"] == "quota-one nonnegative lifted equality":
            row = moments["original_selector_equalities"][z["selector_Gram_row"]]
            assert row["quota"] == 1 and a in row["support"] and b in row["support"]
        else:
            assert z["kind"] == "certified binary motif times selector"
            assert [a, b] in validation["motif_pairs"]
    assert by_kind == {"quota-one nonnegative lifted equality": 4320, "certified binary motif times selector": 90}
    core, triples = validation["core"], validation["triples"]
    assert len(core) == 21 and len(triples) == 480 and len({tuple(t) for t in triples}) == 480
    assert all(t == sorted(set(t)) and len(t) == 3 and 0 <= t[0] <= t[-1] < 18 for t in triples)
    gram_rows = []
    for i in range(18):
        for j in range(i, 18):
            quota = 12*int(i == j)+2-(core[i+3]&core[j+3]).bit_count()-((core[i+3] >> (j+3))&1)
            support = [a for a, t in enumerate(triples) if i in t and j in t]
            gram_rows.append({"family": "Gram", "core_pair": [i, j], "support": support, "quota": quota})
    gram_rows.append({"family": "population", "support": list(range(480)), "quota": 60})
    assert gram_rows == moments["original_selector_equalities"]
    motif_proofs = []
    for key, kind, count in (("F_conflicts", "F", 78), ("prism_conflicts", "P", 12)):
        assert len(motif_record[key]) == count
        for ri, record in enumerate(motif_record[key]):
            a, b = record["ordered_columns"]
            assert sorted((a, b)) == record["columns"]
            rows = list(core)+[0, 0]
            for v, col in ((21, a), (22, b)):
                for i in triples[col]:
                    rows[v] |= 1 << (i+3); rows[i+3] |= 1 << v
            assert not caps_failures(rows)
            motif = induced(rows, record["motif_sites"])
            assert motif == record["induced_motif_rows"] and motif_shape(motif, kind)
            rows[21] |= 1 << 22; rows[22] |= 1 << 21
            bad = caps_failures(rows)
            assert bad
            motif_proofs.append({"kind": kind, "family_index": ri, "literal_pair": record["columns"],
                                 "edge_present_cap_failure": bad[0]})
    assert len({tuple(p) for p in validation["motif_pairs"]}) == 90
    assert sorted(p["literal_pair"] for p in motif_proofs) == sorted(validation["motif_pairs"])
    assert len(literal_rows) == 4416
    parsed_rows = []
    for row in literal_rows:
        assert set(row) == {"terms", "rhs"}
        terms = [[a, decimal(c)] for a, c in row["terms"]]
        assert all(type(a) is int and 0 <= a < 480 and c for a, c in terms)
        assert len({a for a, c in terms}) == len(terms)
        parsed_rows.append({"terms": terms, "rhs": decimal(row["rhs"])})
    assert all(r["rhs"] == 0 for r in parsed_rows)
    tick(deadline)
    return {"scope": scope, "inverse": inverse, "moments": moments, "characters": chars,
            "representations": rep_matrices, "one_d": one_d, "group_inverse": group_inverse,
            "transports": transports, "signed_index": signed_index, "layouts": layouts,
            "local_columns": local_columns, "active_one_d": factor["active_one_dimensional_characters"],
            "active_two_d": factor["active_two_dimensional_representations"],
            "validation": validation, "literal_rows": parsed_rows, "motif_proofs": motif_proofs}


def local_coordinates(ctx, oi, mask):
    orbit = ctx["moments"]["selector_orbits"][oi]
    selected = [a for i, a in enumerate(orbit) if (mask >> i)&1]
    matrices = {name: [[sum(ctx["representations"][name][ctx["transports"][oi][a]][r][c] for a in selected)
                        for c in range(2)] for r in range(2)] for name in ctx["active_two_d"][oi]}
    return {(name, j): [2*matrices[name][0][k]-matrices[name][1][k], matrices[name][1][k]]
            for name, j, k in ctx["local_columns"][oi]}


def encode_selection(ctx, selected):
    assert selected == sorted(set(selected)) and all(type(a) is int and 0 <= a < 480 for a in selected)
    inverse = ctx["inverse"]
    ns, ps = [0]*42, [0]*9742
    chosen = set(selected)
    for a in selected:
        ns[inverse["literal_selector_to_orbit"][a]] += 1
    for a, b in combinations(selected, 2):
        ps[ctx["moments"]["pair_to_orbit"][pair_id(a, b)]] += 1
    ls = [sum(w for a, w in zip(p["literal_selectors"], p["signs"]) if a in chosen)
          for p in ctx["characters"]["signed_populations"]]
    ab = {name: [[0, 0] for _ in cols] for name, cols in ctx["layouts"].items()}
    for oi, orbit in enumerate(ctx["moments"]["selector_orbits"]):
        mask = sum(1 << i for i, a in enumerate(orbit) if a in chosen)
        for (name, j), pair in local_coordinates(ctx, oi, mask).items():
            ab[name][j] = pair
    return {"schema": ABSTRACT_SCHEMA, "selector_populations": ns, "original_pair_populations": ps,
            "signed_populations": ls, "Fourier_ab": ab}


def validate_projection(ctx, point):
    assert set(point) == {"schema", "selector_populations", "original_pair_populations", "signed_populations", "Fourier_ab"}
    assert point["schema"] == ABSTRACT_SCHEMA
    for key, width in (("selector_populations", 42), ("original_pair_populations", 9742), ("signed_populations", 118)):
        assert isinstance(point[key], list) and len(point[key]) == width and all(type(v) is int for v in point[key])
    assert all(0 <= n <= len(t["literal_selectors"]) for n, t in zip(point["selector_populations"], ctx["inverse"]["inverse_tables"]))
    assert all(0 <= n <= size for n, size in zip(point["original_pair_populations"], ctx["inverse"]["original_pair_orbit_sizes"]))
    assert all(point["original_pair_populations"][po] == 0 for po in ctx["inverse"]["original_zero_pair_orbits"])
    assert all(-6 <= n <= 6 for n in point["signed_populations"])
    assert isinstance(point["Fourier_ab"], dict) and set(point["Fourier_ab"]) == set(REPRESENTATIONS)
    for name, columns in ctx["layouts"].items():
        values = point["Fourier_ab"][name]
        assert isinstance(values, list) and len(values) == len(columns)
        assert all(isinstance(p, list) and len(p) == 2 and all(type(v) is int and abs(v) <= 36 for v in p) for p in values)


def inverse_masks(ctx, point):
    """Fourier inversion, independent of inverse-table filtering."""
    masks, failures = [], []
    for oi, orbit in enumerate(ctx["moments"]["selector_orbits"]):
        matrices = {name: [[0, 0], [0, 0]] for name in ctx["active_two_d"][oi]}
        for name, j, k in ctx["local_columns"][oi]:
            a, b = point["Fourier_ab"][name][j]
            if (a+b) % 2:
                failures.append({"kind": "coordinate_parity", "selector_orbit": oi, "representation": name, "column_index": j})
                continue
            matrices[name][0][k], matrices[name][1][k] = (a+b)//2, b
        mask = 0
        for position, a in enumerate(orbit):
            g = ctx["group_inverse"][ctx["transports"][oi][a]]
            numerator = 0
            for ci in ctx["active_one_d"][oi]:
                population = point["selector_populations"][oi] if ci == 0 else point["signed_populations"][ctx["signed_index"][oi, ci]]
                numerator += ctx["one_d"][ci][g]*population
            for name, matrix in matrices.items():
                numerator += 2*matrix_trace_product(ctx["representations"][name][g], matrix)
            if numerator not in (0, len(orbit)):
                failures.append({"kind": "non_Boolean_Fourier_inverse", "selector_orbit": oi,
                                 "literal_selector": a, "numerator": numerator, "denominator": len(orbit)})
            elif numerator:
                mask |= 1 << position
        masks.append(mask)
    return masks, failures


def literal_obligations(ctx, selected):
    chosen = set(selected)
    equalities = [{"row": i, "observed": sum(a in chosen for a in r["support"]), "required": r["quota"]}
                  for i, r in enumerate(ctx["moments"]["original_selector_equalities"])]
    profiles = Counter(tuple(sum(v//6 == f for v in ctx["validation"]["triples"][a]) for f in range(3)) for a in selected)
    balanced = profiles[(1, 1, 1)]
    other = sum(n for p, n in profiles.items() if p != (1, 1, 1))
    fibers = [[sum(n for p, n in profiles.items() if p[f] == k) for k in range(3)] for f in range(3)]
    motif_failures = [p for p in ctx["motif_proofs"] if all(a in chosen for a in p["literal_pair"])]
    zero_failures = [z["pair_id"] for z in ctx["moments"]["zero_moment_certificates"]
                     if z["anchor"] in chosen and z["other"] in chosen]
    slacks = [r["rhs"]-sum(c for a, c in r["terms"] if a in chosen) for r in ctx["literal_rows"]]
    cuts_failed = [[i, v] for i, v in enumerate(slacks) if v < 0]
    failed_equalities = [r["row"] for r in equalities if r["observed"] != r["required"]]
    profile_pass = balanced == 24 and other == 36 and fibers == [[12, 36, 12]]*3
    passed = not (failed_equalities or motif_failures or zero_failures or cuts_failed) and profile_pass
    return {"all_declared_literal_selector_obligations_pass": passed,
        "original172_equalities": equalities, "failed_original_equality_ids": failed_equalities,
        "selected_population": len(selected), "signature_profile_counts": [[list(p), n] for p, n in sorted(profiles.items())],
        "profile24_36": [balanced, other], "fiber_profiles_0_1_2": fibers, "profile_obligations_pass": profile_pass,
        "F_motif_exclusions_checked": 78, "prism_exclusions_checked": 12, "failed_motif_exclusions": motif_failures,
        "literal_zero_pairs_checked": 4410, "failed_literal_zero_pair_ids": zero_failures,
        "linear_literal_selector_inequalities_checked": 4416, "failed_literal_selector_rows_and_slacks": cuts_failed,
        "all_literal_selector_slacks_sha256": sha(canonical(slacks)), "minimum_literal_selector_slack": min(slacks),
        "integer_arithmetic": "Python integers, including coefficients larger than int64"}


def decode_abstract(ctx, point):
    validate_projection(ctx, point)
    masks, failures = inverse_masks(ctx, point)
    matched = []
    for oi, tab in enumerate(ctx["inverse"]["inverse_tables"]):
        old = ctx["inverse"]["new15038_to_original15589"]
        wanted = [point["selector_populations"][j] if j < 42 else point["original_pair_populations"][old[j]-5847]
                  for j in tab["count_columns"]]+[point["signed_populations"][j] for j in tab["signed_population_columns"]]
        profiles = [p for p in tab["profiles"] if p["counts_and_signed_populations"] == wanted]
        if len(profiles) != 1:
            failures.append({"kind": "missing_or_nonunique_local_profile", "selector_orbit": oi, "matches": len(profiles)})
            matched.append(None); continue
        profile = profiles[0]
        compatible = [m for m in profile["local_masks"] if all(point["Fourier_ab"][name][j] == value
                      for (name, j), value in local_coordinates(ctx, oi, m).items())]
        if compatible != [masks[oi]]:
            failures.append({"kind": "Fourier_mask_and_complete_inverse_preimages_disagree", "selector_orbit": oi,
                             "matching_masks": compatible, "Fourier_inverse_mask": masks[oi]})
        matched.append(profile["tuple_index"])
    scope = {"finite_count_acceptance_verified": False, "native_model_bound": False,
             "averaged_model_inequalities_verified": False, "exterior_Y_edges_realized": False,
             "graph_completion_claimed": False, "F0_or_global_exclusion_claimed": False}
    if failures:
        return {"status": "REJECTED_FIXED_ABSTRACT_PROJECTION", "projection_sha256": sha(canonical(point)),
                "failures": failures, "literal_selector_checks_pass": False, **scope}
    selected = sorted(a for oi, o in enumerate(ctx["moments"]["selector_orbits"]) for i, a in enumerate(o) if masks[oi] >> i & 1)
    reconstructed = encode_selection(ctx, selected)
    differences = {key: [j for j, (a, b) in enumerate(zip(point[key], reconstructed[key])) if a != b]
                   for key in ("selector_populations", "original_pair_populations", "signed_populations")}
    assert reconstructed["Fourier_ab"] == point["Fourier_ab"]
    obligations = literal_obligations(ctx, selected)
    if any(differences.values()):
        status = "REJECTED_FIXED_ABSTRACT_PROJECTION"
    elif obligations["all_declared_literal_selector_obligations_pass"]:
        status = "EXACT_LITERAL_SELECTOR_CHECKS_PASS"
    else:
        status = "EXACT_MOMENT_DECODE_WITH_LITERAL_OBLIGATION_FAILURES"
    return {"status": status, "projection_sha256": sha(canonical(point)),
        "unique_local_masks": masks, "local_profile_indices": matched, "selected_literal_signatures": selected,
        "reconstructed_projection_sha256": sha(canonical(reconstructed)), "projection_difference_indices": differences,
        "all9742_pair_histograms_match": not differences["original_pair_populations"],
        "all389_zero_pair_targets_explicit": True, "literal_obligations": obligations,
        "literal_selector_checks_pass": status == "EXACT_LITERAL_SELECTOR_CHECKS_PASS", **scope}


def prepare(deadline):
    ctx = load_context(deadline)
    local_inventory, total, delta_checks = [], 0, 0
    for oi, tab in enumerate(ctx["inverse"]["inverse_tables"]):
        tick(deadline)
        orbit = tab["literal_selectors"]
        # A direct unit-vector Fourier inverse is independent of pair-form construction.
        for p, a in enumerate(orbit):
            local = local_coordinates(ctx, oi, 1 << p)
            for b in orbit:
                g = ctx["group_inverse"][ctx["transports"][oi][b]]
                value = sum(ctx["one_d"][ci][g]*ctx["one_d"][ci][ctx["transports"][oi][a]]
                            for ci in ctx["active_one_d"][oi])
                for name in ctx["active_two_d"][oi]:
                    matrix = [[0, 0], [0, 0]]
                    for rep, j, k in ctx["local_columns"][oi]:
                        if rep == name:
                            aa, bb = local[rep, j]; assert (aa+bb) % 2 == 0
                            matrix[0][k], matrix[1][k] = (aa+bb)//2, bb
                    value += 2*matrix_trace_product(ctx["representations"][name][g], matrix)
                assert value == len(orbit)*int(a == b)
                delta_checks += 1
        images, masks, digest = {}, set(), sha256()
        for profile in tab["profiles"]:
            for mask in profile["local_masks"]:
                coordinates = local_coordinates(ctx, oi, mask)
                key_coords = [coordinates[name, j] for name, j, k in ctx["local_columns"][oi]]
                selected = {a for i, a in enumerate(orbit) if mask >> i & 1}
                signed = [sum(w for a, w in zip(ctx["characters"]["signed_populations"][j]["literal_selectors"],
                                               ctx["characters"]["signed_populations"][j]["signs"]) if a in selected)
                          for j in tab["signed_population_columns"]]
                values = profile["counts_and_signed_populations"]
                assert values[0] == mask.bit_count() and signed == values[len(tab["count_columns"]):]
                key = canonical([mask.bit_count(), signed, key_coords])
                assert key not in images and mask not in masks
                images[key] = mask; masks.add(mask)
                digest.update(canonical([profile["tuple_index"], mask, key_coords])+b"\n")
                total += 1
                if total % 128 == 0:
                    tick(deadline)
        assert len(masks) == tab["accepted_literal_masks"]
        local_inventory.append({"selector_orbit": oi, "profile_count": len(tab["profiles"]),
                                "complete_saved_masks": len(masks), "distinct_full_Fourier_images": len(images),
                                "ordered_mask_coordinate_ledger_sha256": digest.hexdigest()})
    assert total == LIMITS["existing_inverse_masks"] and delta_checks == 5616
    fixtures = ctx["inverse"]["reconstruction_controls"]["synthetic_positive_reconstructions"]
    positive_controls = []
    for fixture in fixtures:
        point = encode_selection(ctx, fixture["synthetic_selection"])
        check = decode_abstract(ctx, point)
        assert check["status"] == "EXACT_MOMENT_DECODE_WITH_LITERAL_OBLIGATION_FAILURES"
        assert check["selected_literal_signatures"] == fixture["synthetic_selection"]
        assert check["all9742_pair_histograms_match"] and not check["literal_selector_checks_pass"]
        positive_controls.append({"synthetic_selection": fixture["synthetic_selection"], "check": check})
    base = encode_selection(ctx, fixtures[-1]["synthetic_selection"])
    altered = []
    bad = deepcopy(base); a, b = fixtures[-1]["synthetic_selection"]
    po = ctx["moments"]["pair_to_orbit"][pair_id(a, b)]
    bad["original_pair_populations"][po] = 0; altered.append(("changed_cross_pair_target", bad))
    bad = deepcopy(base); bad["Fourier_ab"]["central_plus"][0][0] += 1; altered.append(("odd_a_plus_b", bad))
    bad = deepcopy(base); bad["Fourier_ab"]["central_plus"][0][0] += 2; altered.append(("even_but_wrong_coordinate", bad))
    negative_controls = []
    for label, point in altered:
        check = decode_abstract(ctx, point)
        assert check["status"] == "REJECTED_FIXED_ABSTRACT_PROJECTION"
        negative_controls.append({"label": label, "check": check})
    malformed = []
    for label, mutator in (("missing_active_representation", lambda p: p["Fourier_ab"].pop("central_minus")),
                           ("Boolean_is_not_integer", lambda p: p["selector_populations"].__setitem__(0, True)),
                           ("float_is_not_integer", lambda p: p["Fourier_ab"]["central_plus"][0].__setitem__(0, 0.0))):
        point = deepcopy(base); mutator(point)
        try:
            validate_projection(ctx, point)
        except AssertionError:
            malformed.append(label)
        else:
            raise AssertionError("malformed abstract input accepted")
    rows = ctx["literal_rows"]
    tick(deadline)
    return {"schema": "conway99.f0.abstract-Fourier-decoder-preparation.v1", "status": "PREPARED_ABSTRACT_DECODER_ONLY",
        "source_sha256": sha(Path(__file__).read_bytes()), "inputs": INPUTS, "earlier_acceptance_sources_read": SOURCES_READ,
        "limits": LIMITS, "abstract_input_schema": {"schema": ABSTRACT_SCHEMA, "selector_populations": 42,
            "original_pair_populations": 9742, "signed_populations": 118,
            "Fourier_ab": {"central_plus": "84 ordered [a,b] pairs", "central_minus": "76 ordered [a,b] pairs"},
            "all_values_are_JSON_integers": True, "a_definition": "2*x-y", "b_definition": "y",
            "column_layouts": ctx["layouts"], "future_native_id_map_bound": False},
        "local_inventory": local_inventory, "existing_inverse_masks_checked": total,
        "direct_unit_Fourier_inverse_checks": delta_checks,
        "original_Gram_rows_reconstructed_from_literal_core": 171,
        "original_population_equality": 60, "saved_motif_proofs_replayed": ctx["motif_proofs"],
        "literal_inequality_inventory": {"rows": len(rows), "nonzero_terms": sum(len(r["terms"]) for r in rows),
            "all_terms_are_linear_selector_bits": True, "all_right_hand_sides_zero": True,
            "maximum_coefficient_bits": max(abs(c).bit_length() for r in rows for a, c in r["terms"]),
            "stored_field": "f0-boolean-fractional-model.json.gz: Boolean_validation.full_rows",
            "not_added_to_any_native_model": True},
        "positive_decoder_controls": positive_controls, "negative_decoder_controls": negative_controls,
        "malformed_input_controls_rejected": malformed,
        "production_binding": {"actual_model_specification": None, "accepted_count_receipt": None,
            "native_vector_schema": None, "production_candidate_run": False},
        "separate_obligations": ["independent finite-count acceptance", "exact decoded selector obligations",
                                 "averaged model inequalities", "exterior Y realization", "full graph completion"],
        "new_selector_subset_censuses": 0, "optimizer_calls": 0}


def main():
    if not __debug__:
        raise RuntimeError("assertions must remain enabled")
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["prepare", "replay"])
    parser.add_argument("--preparation", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    start = time.monotonic()
    try:
        record = prepare(start+LIMITS["seconds_per_preparation_or_replay"])
        if args.mode == "replay":
            assert args.preparation
            raw = args.preparation.read_bytes(); old = json.loads(raw); old.pop("seconds")
            assert canonical(record) == canonical(old)
            record = {"status": "PASS: complete abstract decoder preparation replay", "source_sha256": sha(Path(__file__).read_bytes()),
                      "preparation_sha256": sha(raw), "existing_saved_masks_replayed": 64144,
                      "production_candidates_checked": 0, "optimizer_calls": 0}
    except Exception as exc:
        record = {"status": "FAILED_ABSTRACT_PREPARATION", "source_sha256": sha(Path(__file__).read_bytes()),
                  "error": type(exc).__name__+": "+str(exc), "production_candidates_checked": 0, "optimizer_calls": 0}
    record["seconds"] = time.monotonic()-start
    raw = canonical(record)+b"\n"
    assert len(raw) <= LIMITS["maximum_raw_record_bytes"]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("xb") as out:
        out.write(raw)
    print(json.dumps({"status": record["status"], "seconds": record["seconds"], "record_sha256": sha(raw), "bytes": len(raw)}))
    if record["status"] == "FAILED_ABSTRACT_PREPARATION":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
