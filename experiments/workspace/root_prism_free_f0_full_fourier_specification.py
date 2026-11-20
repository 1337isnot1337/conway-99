"""Complete Fourier local-mask tables, product identities and inverse rows.

This is finite exact preparation, not a solver. It extends the saved accepted
local masks instead of enumerating subsets again. Both complete 2D blocks are
retained, including within-orbit entries. All 172 original selector equations
have inverse certificates; the 21 literal 0=0 equations need no native row.
"""
import argparse
from collections import Counter
import gc
import gzip
import hashlib
import importlib.util
import json
from math import gcd
from pathlib import Path
import resource
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
LOGS = ROOT / "experiments/logs/root-prism-free"
SOURCES = {
    "algebra": ("root_prism_free_f0_nonabelian_pair_factorization.py", "790a929c65898d2a3bb038c9877d73dc022aa9c66d3983efe8a77ad833383871"),
    "inverse": ("root_prism_free_f0_character_literal_lift.py", "3bf7f92502592bcda0b4dc71868a6745888c608b26d3f8e42f2771cf180c7252"),
    "parent": ("root_prism_free_f0_character_y_domain_overlay.py", "ff08cbcaec6787d5821af57526a708e1758007970bec58c86584bcd3d76904dd"),
    "supervisor": ("root_prism_free_f0_local_neighbors_batch.py", "b8e5323f92fa105ff2c0ed5b1667ac25d7c92f85f8cac45b170ddc56208f8278"),
}
INPUTS = {
    "algebra": ("f0-nonabelian-pair-factorization01.json.gz", "627577aea4a25c15e5d2846242adda9c6b7c97164b7ba47fb9a2cab5d3988fd8"),
    "algebra_source_review": ("f0-nonabelian-pair-factorization-literature-review.json", "c39fcb87ac886463aa3124dc946fab387fb3a739951956f25848b476a9eba86b"),
    "algebra_note_review": ("f0-nonabelian-pair-factorization-note-literature-review.json", "49a6c199098c8f76591efe6bbb602373093f9267d7b6cc524a53eca9d6c8dd09"),
    "scope": ("f0-two-dimensional-moments-scope01.json", "948e256945fc817cc75ea46c969c055b21e61832a4f2177c481884e73338223f"),
    "inverse": ("f0-character-literal-lift-preparation01.json.gz", "241cd14c61b465025c72ffcaa65af8e5c48e9e5a0eda7ea7d252e9d74b22db1e"),
    "inverse_cold": ("f0-character-literal-lift-preparation01-cold.json", "6cebe725527eaf28f3d075a3ad9741fcbcf50cdedd42107bdc5ebcbe857da72f"),
    "characters": ("f0-character-populations01.json.gz", "139d06a3383f8fc79d677972ce052ce29966e8b3406e7d1e7d1077aea7c2cef6"),
    "moments": ("f0-second-moments-preparation02.json.gz", "404d91da35c798ba248887c22a7500957947e24b71d5197dc44432460e6d219e"),
    "phase": ("f0-character-phase-normalization01.json", "737389ccfd5290072e8dd4cb12a63bfa3a6cae2d10a6ece2793c0a891aff7e04"),
    "phase_cold": ("f0-character-phase-normalization01-cold.json", "56c67d0049db09454abc33d2801a9a66edb0b75e120df8c5f6c07f9ce65fb36b"),
    "parent_plan": ("f0-character-y-domain-overlay01/plan.json.gz", "4d3a13718cdac9fcf68b119a1cd1ba009edeb21c7257d4498d5ebdf18954acc4"),
    "parent_preparation": ("f0-character-y-domain-overlay01/report.json", "a4a543b35bdd22357eef39524ff8015e0d4d274547c046205c806a5f52e92061"),
    "parent_cold": ("f0-character-y-domain-overlay01-cold/report.json", "851a2a4a292a891de7b38eb08212fd1a604cf72cc09dbef3af97768ebe8e21be"),
}
REPRESENTATION_ORDER = ("central_plus", "central_minus")
OLD_VARIABLES, COORDINATE_STOP, VARIABLES = 18444, 18764, 31756
SECONDS = 60


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def file_sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def save(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(canonical(value) + b"\n")
    temporary.replace(path)


def read(key):
    name, expected = INPUTS[key]
    raw = (LOGS / name).read_bytes()
    assert sha(raw) == expected, key
    return json.loads(gzip.decompress(raw) if name.endswith(".gz") else raw)


def definition():
    for name, expected in SOURCES.values():
        assert file_sha(ROOT / "experiments/workspace" / name) == expected, name
    for name, expected in INPUTS.values():
        assert file_sha(LOGS / name) == expected, name
    return {
        "schema": "conway99.f0.full-Fourier-specification.v1", "source_sha256": file_sha(Path(__file__)),
        "sources": {k: {"path": "experiments/workspace/" + p, "sha256": h} for k, (p, h) in SOURCES.items()},
        "inputs": {k: {"path": str((LOGS / p).relative_to(ROOT)), "sha256": h} for k, (p, h) in INPUTS.items()},
        "maximum_owned_seconds": SECONDS, "maximum_raw_specification_bytes": 32 << 20,
        "coordinate_order": "central_plus then central_minus; saved column_index; a then b",
        "coordinate_namespace": [18444, 18764], "product_namespace": [18764, 31756],
        "original_selector_equations_certified": 172, "literal_zero_equalities_omitted": 21,
        "nonempty_inverse_equalities_appended": 151, "new_Gram_entries": 6496, "new_products": 12992,
        "resulting_target_constraints": 54037, "resulting_initial_constraints": 53920,
        "independent_fourier_orientation_or_sign_fixing": False,
        "new_selector_subset_census": False, "native_model_built": False, "optimizer_calls": 0,
    }


def intervals(values):
    values = sorted(set(values))
    assert values and all(type(v) is int for v in values)
    result = [values[0], values[0]]
    for v in values[1:]:
        if v == result[-1] + 1:
            result[-1] = v
        else:
            result.extend([v, v])
    return result


def primitive(terms, rhs):
    terms = sorted([int(j), int(c)] for j, c in terms.items() if c)
    divisor = abs(rhs)
    for j, c in terms:
        divisor = gcd(divisor, abs(c))
    divisor = divisor or 1
    assert rhs % divisor == 0
    return {"terms": [[j, c // divisor] for j, c in terms], "rhs": rhs // divisor,
            "positive_divisor": divisor}


def mul(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(2)) for j in range(2)] for i in range(2)]


def derive(stage):
    algebra, scope, inverse = [read(k) for k in ("algebra", "scope", "inverse")]
    inverse_cold = read("inverse_cold")
    assert algebra["source_sha256"] == SOURCES["algebra"][1]
    assert algebra["complete_literal_unordered_pairs"] == 114960 and algebra["original_pair_orbits"] == 9742
    assert algebra["new_scalar_Gram_identities"] == 6496 and algebra["missing_integer_Fourier_coordinates"] == 320
    assert inverse_cold["status"].startswith("PASS") and inverse_cold["record_sha256"] == INPUTS["inverse"][1]
    assert inverse["inventory"]["accepted_literal_masks"] == 64144
    for key in ("algebra_source_review", "algebra_note_review", "phase_cold", "parent_cold"):
        assert read(key)["status"].startswith("PASS")
    full = read("characters")
    characters = {k: full[k] for k in ("group", "signed_populations")}
    del full
    full = read("moments")
    moments = {k: full[k] for k in ("selector_orbits", "selector_actions", "original_selector_equalities")}
    del full
    full = read("parent_plan")
    assert full["source_sha256"] == SOURCES["parent"][1]
    assert (full["variable_count"], full["full_target_constraints"], full["initial_constraints"]) == (18444, 34398, 34281)
    assert full["external_pool_constraints"] == 117
    old_domains = full["target_variable_domains"]
    del full
    gc.collect()
    stage("frozen_algebra_masks_actions_and_parent_domains_loaded")
    orbits, actions = moments["selector_orbits"], moments["selector_actions"]
    assert len(orbits) == 42 and sorted(a for orbit in orbits for a in orbit) == list(range(480))
    assert [t["literal_selectors"] for t in inverse["inverse_tables"]] == orbits
    assert len(actions) == 12 and actions[0] == list(range(480))
    group = scope["group"]["multiplication_table"]
    assert group == characters["group"]["multiplication_table"]
    inverses = [next(h for h in range(12) if group[g][h] == group[h][g] == 0) for g in range(12)]
    for g in range(12):
        for h in range(12):
            assert all(actions[g][actions[h][a]] == actions[group[g][h]][a] for a in range(480))
    reps = scope["two_dimensional_representations"]
    assert scope["H"] == algebra["H"] == [[2, -1], [-1, 2]]
    transports = [dict(t) for t in algebra["literal_transports"]]
    for oi, orbit in enumerate(orbits):
        assert set(transports[oi]) == set(orbit)
        assert all(actions[g][orbit[0]] == a for a, g in transports[oi].items())
    signed_by_key = {(p["character"], p["selector_orbit"]): p for p in characters["signed_populations"]}
    assert len(signed_by_key) == 118

    coordinates, by_column, by_orbit = [], {}, [[] for _ in range(42)]
    for name in REPRESENTATION_ORDER:
        columns = algebra["Fourier_columns_in_a_b_coordinates"][name]
        assert len(columns) == (84 if name == "central_plus" else 76)
        assert [c["column_index"] for c in columns] == list(range(len(columns)))
        for col in columns:
            oi, k = col["selector_orbit"], col["matrix_column"]
            assert k in (0, 1) and [r[0] for r in col["literal_a_b_coefficients"]] == orbits[oi]
            ids = []
            for part, position in (("a", 1), ("b", 2)):
                j = OLD_VARIABLES + len(coordinates)
                coeffs = [[a, row[position]] for row in col["literal_a_b_coefficients"] for a in [row[0]]]
                record = {"native_id": j, "representation": name, "column_index": col["column_index"],
                          "selector_orbit": oi, "matrix_column": k, "part": part,
                          "literal_coefficients": coeffs}
                coordinates.append(record); by_orbit[oi].append(record); ids.append(j)
            by_column[name, col["column_index"]] = ids
    assert [c["native_id"] for c in coordinates] == list(range(18444, 18764))
    assert by_column["central_plus", 0] == [18444, 18445]
    assert by_column["central_minus", 0] == [18612, 18613]
    coordinate_index = {c["native_id"]: c for c in coordinates}
    values_by_coordinate = {c["native_id"]: set() for c in coordinates}

    # The same physical group element acts on every orbit and representation.
    # Literal-unit equivariance plus saved mask-set closure proves new-table
    # closure without recomputing Fourier features for 12 copies of each mask.
    equivariance_checks = 0
    for name in REPRESENTATION_ORDER:
        for oi, orbit in enumerate(orbits):
            cols = [c for c in algebra["Fourier_columns_in_a_b_coordinates"][name] if c["selector_orbit"] == oi]
            if not cols:
                continue
            assert len(cols) == 2 and [c["matrix_column"] for c in cols] == [0, 1]
            matrices = {}
            for a in orbit:
                entries = [next(row for row in c["literal_a_b_coefficients"] if row[0] == a) for c in cols]
                assert all((row[1] + row[2]) % 2 == 0 for row in entries)
                matrices[a] = [[(r[1] + r[2]) // 2 for r in entries], [r[2] for r in entries]]
                assert matrices[a] == reps[name]["matrices"][transports[oi][a]]
            for g in range(12):
                for a in orbit:
                    assert matrices[actions[g][a]] == mul(reps[name]["matrices"][g], matrices[a])
                    equivariance_checks += 1

    tables, mask_action_checks = [], 0
    for oi, saved in enumerate(inverse["inverse_tables"]):
        orbit, local = orbits[oi], by_orbit[oi]
        local_position = {a: k for k, a in enumerate(orbit)}
        old_columns = saved["count_columns"] + [15941 + j for j in saved["signed_population_columns"]]
        assert old_columns[0] == oi and len(old_columns) == len(set(old_columns))
        assert all(0 <= j < OLD_VARIABLES for j in old_columns)
        new_columns = [c["native_id"] for c in local]
        coefficient_lists = [[c for a, c in rec["literal_coefficients"]] for rec in local]
        old_rows, extended = [], {}
        for profile in saved["profiles"]:
            prefix = profile["counts_and_signed_populations"]
            assert len(prefix) == len(old_columns) and all(type(v) is int for v in prefix)
            old_rows.append(prefix)
            for mask in profile["local_masks"]:
                assert type(mask) is int and 0 <= mask < 1 << len(orbit) and mask.bit_count() == prefix[0]
                selected = [k for k in range(len(orbit)) if mask >> k & 1]
                suffix = [sum(coeffs[k] for k in selected) for coeffs in coefficient_lists]
                for j, v in zip(new_columns, suffix):
                    values_by_coordinate[j].add(v)
                row = tuple(prefix + suffix)
                assert row not in extended
                extended[row] = mask
        rows = sorted(extended)
        masks = [extended[row] for row in rows]
        assert len(rows) == len(set(masks)) == saved["accepted_literal_masks"]
        assert sorted({row[:len(old_columns)] for row in rows}) == list(map(tuple, old_rows))
        mask_set = set(masks)
        assert 0 in mask_set and all(1 << k in mask_set for k in range(len(orbit)))
        for g in range(12):
            permutation = [local_position[actions[g][a]] for a in orbit]
            assert sorted(permutation) == list(range(len(orbit)))
            image = {0: 0}
            for mask in sorted(mask_set):
                if mask:
                    bit = mask & -mask
                    image[mask] = image[mask ^ bit] | (1 << permutation[bit.bit_length() - 1])
                assert image[mask] in mask_set
                mask_action_checks += 1
        tables.append({"selector_orbit": oi, "literal_selectors": orbit,
                       "old_columns": old_columns, "coordinate_columns": new_columns,
                       "columns": old_columns + new_columns, "tuples": [list(row) for row in rows],
                       "local_mask_witnesses": masks, "old_projected_tuple_count": len(old_rows),
                       "old_projected_tuples_sha256": sha(canonical(old_rows)),
                       "complete_saved_mask_list_sha256": sha(canonical(sorted(mask_set)))})
        stage("extended_local_table_checked", selector_orbit=oi, tuples=len(rows))
    assert sum(len(t["tuples"]) for t in tables) == 64144
    assert sum(t["old_projected_tuple_count"] for t in tables) == 19331
    assert mask_action_checks == 64144 * 12
    for rec in coordinates:
        values = sorted(values_by_coordinate[rec["native_id"]])
        rec["attainable_values"] = values
        rec["domain"] = intervals(values)
    all_domains = list(old_domains) + [c["domain"] for c in coordinates]
    assert len(all_domains) == COORDINATE_STOP

    inverse_rows, unit_checks = [], 0
    for oi, orbit in enumerate(orbits):
        scale = 12 // len(orbit)
        assert scale * len(orbit) == 12
        for a in orbit:
            g = inverses[transports[oi][a]]
            row = Counter({oi: scale})
            for ci in algebra["active_one_dimensional_characters"][oi]:
                if ci == 0:
                    assert characters["group"]["characters"][ci] == [1] * 12
                    continue
                signing = signed_by_key[ci, oi]
                row[15941 + signing["signed_population"]] += scale * characters["group"]["characters"][ci][g]
            for name in algebra["active_two_dimensional_representations"][oi]:
                matrix = reps[name]["matrices"][g]
                cols = [c for c in algebra["Fourier_columns_in_a_b_coordinates"][name] if c["selector_orbit"] == oi]
                for k, col in enumerate(cols):
                    aa, bb = by_column[name, col["column_index"]]
                    row[aa] += scale * matrix[k][0]
                    row[bb] += scale * (matrix[k][0] + 2 * matrix[k][1])
            terms = sorted([j, c] for j, c in row.items() if c)
            for b in orbit:
                unit = {oi: 1}
                for signing in characters["signed_populations"]:
                    if signing["selector_orbit"] == oi:
                        unit[15941 + signing["signed_population"]] = signing["signs"][orbit.index(b)]
                for rec in by_orbit[oi]:
                    unit[rec["native_id"]] = dict(rec["literal_coefficients"])[b]
                assert sum(c * unit[j] for j, c in terms) == 12 * int(a == b)
                unit_checks += 1
            inverse_rows.append({"selector": a, "selector_orbit": oi, "denominator": 12, "terms": terms})
    inverse_rows.sort(key=lambda r: r["selector"])
    assert [r["selector"] for r in inverse_rows] == list(range(480))
    assert unit_checks == sum(len(orbit) ** 2 for orbit in orbits)
    original_rows = moments["original_selector_equalities"]
    assert len(original_rows) == 172
    equality_records, nonempty = [], []
    for ri, original in enumerate(original_rows):
        coefficients = Counter()
        for a in original["support"]:
            for j, c in inverse_rows[a]["terms"]:
                coefficients[j] += c
        row = primitive(coefficients, 12 * original["quota"])
        empty = not row["terms"]
        if empty:
            assert not original["support"] and original["quota"] == row["rhs"] == 0
        else:
            nonempty.append(ri)
        equality_records.append({"original_row_id": ri, "original_row": original,
                                 "inverse_denominator": 12, "literal_zero_tautology": empty, **row})
    assert len(nonempty) == 151 and len(equality_records) - len(nonempty) == 21
    stage("all480_inverse_rows_and172_original_equations_checked")

    products, gram_links = [], []
    for name in REPRESENTATION_ORDER:
        columns = algebra["Fourier_columns_in_a_b_coordinates"][name]
        forms = algebra["Gram_forms"][name]
        assert sorted(tuple(r["columns"]) for r in forms) == [(i, j) for i in range(len(columns)) for j in range(i, len(columns))]
        for fi, form in enumerate(forms):
            factors = [by_column[name, i] for i in form["columns"]]
            product_ids = []
            for part in range(2):
                left, right = factors[0][part], factors[1][part]
                avalues, bvalues = [coordinate_index[j]["attainable_values"] for j in (left, right)]
                values = sorted({a * a for a in avalues} if left == right else {a * b for a in avalues for b in bvalues})
                j = COORDINATE_STOP + len(products)
                assert max(abs(v) for v in values) < 1 << 62
                products.append({"native_id": j, "representation": name, "form_index": fi,
                                 "part": "a" if part == 0 else "b", "factors": [left, right],
                                 "square": left == right, "attainable_values": values, "domain": intervals(values)})
                all_domains.append(intervals(values)); product_ids.append(j)
            coefficients = Counter({j: 2 * c for j, c in form["native_count_terms"]})
            coefficients[product_ids[0]] -= 1
            coefficients[product_ids[1]] -= 3
            assert all(0 <= j < 15038 for j, c in form["native_count_terms"])
            gram_links.append({"representation": name, "form_index": fi, "columns": form["columns"],
                               "selector_orbits": form["selector_orbits"], "native_count_terms": form["native_count_terms"],
                               "products": product_ids, "terms": sorted([j, c] for j, c in coefficients.items() if c),
                               "rhs": 0, "within_orbit_retained": form["selector_orbits"][0] == form["selector_orbits"][1]})
    assert len(products) == 12992 and len(gram_links) == 6496 and len(all_domains) == VARIABLES
    assert [p["native_id"] for p in products] == list(range(18764, 31756))
    magnitudes = [max(abs(d[0]), abs(d[-1])) for d in all_domains]
    activities = [sum(abs(c) * magnitudes[j] for j, c in row["terms"]) for row in gram_links + equality_records]
    assert max(activities) < 1 << 62
    assert all(-(1 << 63) <= v < 1 << 63 for row in gram_links + equality_records for j, v in row["terms"])
    assert all(-(1 << 63) <= row["rhs"] < 1 << 63 for row in equality_records)
    stage("all12992_products_and6496_Gram_links_checked")
    return {
        "schema": "conway99.f0.full-Fourier-mathematical-specification.v1", "definition": definition(),
        "status": "COMPLETE_EXACT_SPECIFICATION; no native model or optimizer",
        "coordinate_records": coordinates, "extended_local_tables": tables,
        "product_records": products, "Gram_links": gram_links,
        "literal_inverse_rows": inverse_rows, "original_equality_expansions": equality_records,
        "nonempty_original_equality_ids": nonempty, "target_variable_domains": all_domains,
        "parent_variable_domains_sha256": sha(canonical(old_domains)),
        "counts": {"old_variables": 18444, "new_coordinates": 320, "new_products": 12992,
                   "total_variables": 31756, "replaced_local_tables": 42, "new_local_tuples": 64144,
                   "old_local_profile_projection_tuples": 19331, "new_Gram_links": 6496,
                   "original_equations_certified": 172, "literal_zero_equalities_omitted": 21,
                   "nonempty_original_equalities_appended": 151, "target_constraints": 54037,
                   "initial_constraints": 53920, "external_pool_constraints": 117,
                   "total_products": 16280, "target_linear_constraints": 37713, "target_tables": 44},
        "checks": {"literal_unit_inverse_checks": unit_checks, "literal_forward_equivariance_checks": equivariance_checks,
                   "saved_mask_action_membership_checks": mask_action_checks,
                   "all42_table_projections_recover_frozen_profiles": True,
                   "maximum_new_linear_absolute_box_activity": max(activities),
                   "maximum_new_coordinate_absolute_value": max(magnitudes[18444:18764]),
                   "maximum_new_product_absolute_value": max(magnitudes[18764:]),
                   "all_new_integer_coefficients_and_box_activities_fit_signed64": True,
                   "one_common_group_phase_only": True, "new_orientation_fixing": False,
                   "all_within_orbit_2D_identities_retained": True},
        "scope": "A future accepted full-count point determines one Boolean selector set and its pair histograms. Literal averaged-cut obligations require their own direct check. Exterior Y realization is separate.",
        "new_selector_subset_census": False, "native_model_built": False, "optimizer_calls": 0,
        "count_or_literal_or_graph_feasibility_claimed": False,
    }


def worker(mode, directory, deadline, saved_directory=None):
    started, stages = time.monotonic(), []
    def stage(name, **extra):
        stages.append({"stage": name, "elapsed_seconds": time.monotonic() - started,
                       "peak_rss_KiB": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss, **extra})
        save(directory / "stages.json", {"stages": stages, "optimizer_calls": 0})
        if time.monotonic() > deadline:
            raise TimeoutError("owned Fourier specification deadline")
    try:
        stage("started")
        spec = derive(stage)
        raw = canonical(spec)
        assert len(raw) <= 32 << 20
        if mode == "prepare":
            payload = gzip.compress(raw, mtime=0)
            path = directory / "specification.json.gz"
            with path.open("xb") as stream:
                stream.write(payload)
            report = {"status": "PASS: complete Fourier mathematical preparation; no native model",
                      "source_sha256": file_sha(Path(__file__)), "definition": spec["definition"],
                      "specification": {"path": str(path.relative_to(ROOT)), "sha256": sha(payload),
                                        "raw_sha256": sha(raw), "raw_bytes": len(raw)},
                      "counts": spec["counts"], "checks": spec["checks"], "optimizer_calls": 0}
        else:
            assert mode == "cold" and saved_directory is not None
            prior_raw = (saved_directory / "report.json").read_bytes()
            prior = json.loads(prior_raw)
            reference = prior["specification"]
            path = ROOT / reference["path"]
            assert file_sha(path) == reference["sha256"]
            assert gzip.decompress(path.read_bytes()) == raw
            assert sha(raw) == reference["raw_sha256"] and len(raw) == reference["raw_bytes"]
            assert prior["definition"] == spec["definition"] and prior["counts"] == spec["counts"]
            report = {"status": "PASS: complete Fourier specification cold reconstruction",
                      "source_sha256": file_sha(Path(__file__)), "preparation_sha256": sha(prior_raw),
                      "specification_sha256": reference["sha256"], "counts": spec["counts"],
                      "checks": spec["checks"], "optimizer_calls": 0, "native_model_built": False}
        stage("completed")
        report.update(seconds=time.monotonic() - started, peak_rss_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                      stages_sha256=file_sha(directory / "stages.json"))
        save(directory / "report.json", report)
    except Exception as error:
        save(directory / "error.json", {"error_type": type(error).__name__, "message": str(error),
                                       "peak_rss_KiB": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                                       "optimizer_calls": 0})
        raise


def owned(mode, directory, saved_directory=None):
    started = time.monotonic()
    deadline = started + SECONDS
    definition()
    name, expected = SOURCES["supervisor"]
    path = ROOT / "experiments/workspace" / name
    assert file_sha(path) == expected
    module_spec = importlib.util.spec_from_file_location("frozen_Fourier_owner", path)
    owner = importlib.util.module_from_spec(module_spec); module_spec.loader.exec_module(owner)
    directory.mkdir(parents=True, exist_ok=False)
    command = [sys.executable, str(Path(__file__).resolve()), "_" + mode,
               "--directory", str(directory.resolve()), "--deadline", str(deadline)]
    if saved_directory is not None:
        command.extend(("--saved-directory", str(saved_directory.resolve())))
    save(directory / "owner-result.json", {"status": "UNKNOWN_BEFORE_CHILD", "optimizer_calls": 0})
    supervision = owner.supervise(command, directory, deadline)
    result = {"status": supervision["status"], "supervision": supervision, "report_accepted": False,
              "source_sha256": file_sha(Path(__file__)), "maximum_owned_seconds": SECONDS,
              "optimizer_calls": 0, "native_model_built": False}
    if supervision["status"] == "CHILD_EXITED" and time.monotonic() <= deadline:
        report = json.loads((directory / "report.json").read_bytes())
        assert report["status"].startswith("PASS")
        result.update(status=report["status"], report_accepted=True, report_sha256=file_sha(directory / "report.json"))
    result.update(owner_seconds=time.monotonic() - started, deadline_overrun_seconds=max(0, time.monotonic() - deadline))
    save(directory / "owner-result.json", result)
    print(json.dumps(result, indent=2), flush=True)


if __name__ == "__main__":
    if not __debug__:
        raise RuntimeError("assertions are required")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "cold", "_prepare", "_cold"))
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--saved-directory", type=Path)
    parser.add_argument("--deadline", type=float)
    args = parser.parse_args()
    if args.mode.startswith("_"):
        assert args.deadline is not None
        worker(args.mode[1:], args.directory, args.deadline, args.saved_directory)
    else:
        owned(args.mode, args.directory, args.saved_directory)
