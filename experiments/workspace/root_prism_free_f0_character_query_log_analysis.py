"""Frozen-log timing and exact input-row census; no solver or model build."""
import argparse
from collections import Counter, defaultdict
from decimal import Decimal
import gzip
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
LOGS = ROOT / "experiments/logs/root-prism-free"
INPUTS = {
    "log": ("f0-character-query-run01/child.stdout.log", "436336c50eea8756075d2391f8e182b895b90e49d26b96377319f9075466b362"),
    "child": ("f0-character-query-run01/child-result.json", "e5f41f35bc6d6b8bda9cf45507765023395bb7b3fc287e6f2efdb89804a1793a"),
    "linear": ("f0-orbit-populations02-model.json.gz", "aa46e2ca9df7a5838926385e06a86acda041c8455ac3422ae1e7b0a5c4ce5437"),
    "products": ("f0-population-products02-specification.json.gz", "c83ebbc1d0d4e9b5ec5ccd60ed5e52ea2be2cb24f1de570f6bff8bb158d42e0c"),
    "profiles": ("f0-selector-orbit-profiles01.json.gz", "93c891e7eef037e5869e5c8e13c3cf31d0ad253cb6caf5cd38930b09715e085d"),
    "characters": ("f0-character-populations01.json.gz", "139d06a3383f8fc79d677972ce052ce29966e8b3406e7d1e7d1077aea7c2cef6"),
    "gram": ("f0-character-Gram-equalities01.json", "084764b528f9a75269c8e21bb0b55b480a552022b024db72a4357aca083770c7"),
    "native_preparation": ("f0-character-cpsat01/report.json", "e15c4bfcf7adaabb60258e3cffa8046eb0cd97843ae8787a24b356011d7b8a5f"),
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read(key):
    name, expected = INPUTS[key]
    raw = (LOGS / name).read_bytes()
    assert sha(raw) == expected
    if key == "log":
        return raw.decode()
    return json.loads(gzip.decompress(raw) if name.endswith(".gz") else raw)


def row_statistics(rows, bounds):
    assert rows
    magnitudes = [abs(c) for r in rows for j, c in r["terms"]]
    return {"rows": len(rows), "nonzero_terms": len(magnitudes),
            "minimum_row_width": min(len(r["terms"]) for r in rows),
            "maximum_row_width": max(len(r["terms"]) for r in rows),
            "minimum_absolute_nonzero_coefficient": min(magnitudes),
            "maximum_absolute_coefficient": max(magnitudes),
            "maximum_coefficient_bits": max(magnitudes).bit_length(),
            "maximum_absolute_rhs": max(abs(r["rhs"]) for r in rows),
            "maximum_absolute_box_sum": max(sum(abs(c) * max(abs(v) for v in bounds[j])
                                                  for j, c in r["terms"]) for r in rows)}


def analyze():
    log, child = read("log"), read("child")
    assert child["native_status"] == "UNKNOWN" and child["production_solve_calls"] == 1
    def scalar(pattern):
        matches = re.findall(pattern, log)
        assert len(matches) == 1, (pattern, matches)
        return Decimal(matches[0])
    presolve_start = scalar(r"Starting presolve at ([0-9.]+)s")
    search_setup = scalar(r"Starting search at ([0-9.]+)s")
    main_start = scalar(r"Starting subsolver 'main' search at ([0-9.]+)s")
    native_wall = Decimal(str(child["native_wall_seconds"]))
    timers = defaultdict(list)
    for seconds, name in re.findall(r"^\s+([0-9.e+\-]+)s\s+[0-9.e+\-]+d\s+\*?\[([^]]+)\]", log, re.M):
        timers[name].append(Decimal(seconds))
    assert len(timers["Probe"]) == 3
    initial_probe = scalar(r"\[Probing\].*?wall_time: ([0-9.]+)")
    rules = {name: int(n.replace("'", "")) for name, n in
             re.findall(r"rule '([^']+)'.*?applied ([0-9']+) time", log)}
    assert rules["table: expanded positive constraint"] == 84
    assert rules["new_bool: table expansion"] == 20607
    timer_summary = [{"name": name, "printed_wall_seconds": [str(v) for v in values],
                      "sum_of_printed_wall_seconds": str(sum(values))}
                     for name, values in sorted(timers.items(), key=lambda kv: -sum(kv[1]))]
    linear, spec = read("linear"), read("products")
    characters, gram = read("characters"), read("gram")
    rows = linear["matrix"]["equalities"] + linear["matrix"]["inequalities"]
    psd_ids = set(linear["row_lift"]["all92_PSD_combined_row_indices"])
    assert len(psd_ids) == 92 and sorted(psd_ids) == spec["inherited92_PSD_row_indices"]
    bounds = [[0, u] for u in spec["upper_by_variable"]]
    for p in characters["signed_populations"]:
        bounds.append([p["raw_lower"], p["raw_upper"]])
    for e in characters["product_equations"]:
        a, b = e["signed_population_factors"]
        m = bounds[15941 + a][1] * bounds[15941 + b][1]
        bounds.append([0 if a == b else -m, m])
    groups = {
        "inherited92_PSD": [r for i, r in enumerate(rows) if i in psd_ids],
        "all_other_inherited_count_rows": [r for i, r in enumerate(rows) if i not in psd_ids],
        "selector25_integer_refinements": spec["selector_integer_refinement_rows"],
        "trivial903_product_links": spec["product_link_equalities"],
        "signed2385_product_links": [{"terms": e["count_terms"] + [[16059 + i, -1]], "rhs": 0}
                                      for i, e in enumerate(characters["product_equations"])],
        "character32_Gram_rows": [{"terms": [[15941 + j, c] for j, c in e["signed_population_terms"]], "rhs": 0}
                                  for e in gram["equations"]],
    }
    census = {name: row_statistics(value, bounds) for name, value in groups.items()}
    assert sum(c["rows"] for c in census.values()) == 31064
    all_terms = sum(c["nonzero_terms"] for c in census.values())
    assert all_terms == 1308488
    native = read("native_preparation")["checks"]
    assert census["signed2385_product_links"]["nonzero_terms"] + census["character32_Gram_rows"]["nonzero_terms"] == native["new_linear_terms"]
    dense_terms = census["inherited92_PSD"]["nonzero_terms"] + census["selector25_integer_refinements"]["nonzero_terms"]
    old_tables = read("profiles")["tables"]
    old_tuples = sum(len(t["profiles"]) for t in old_tables)
    new_tuples = sum(len(t["profiles"]) for t in characters["local_tables"])
    assert (old_tuples, new_tuples) == (5733, 19331)
    return {"status": "PASS: frozen-log analysis and exact row-family census; no query",
            "source_sha256": sha(Path(__file__).read_bytes()),
            "inputs": {k: {"path": "experiments/logs/root-prism-free/" + p, "sha256": h} for k, (p, h) in INPUTS.items()},
            "native_clock_intervals_seconds": {
                "before_presolve": str(presolve_start),
                "presolve_until_search_setup": str(search_setup - presolve_start),
                "search_setup_until_main_search": str(main_start - search_setup),
                "main_search_until_native_return": str(native_wall - main_start),
                "native_total": str(native_wall),
                "timestamps_rounded_by_native_log": True},
            "named_presolve_timers": timer_summary,
            "presolve_probe_printed_seconds_sum": str(sum(timers["Probe"])),
            "search_setup_probe_printed_seconds": str(initial_probe),
            "all_named_probe_printed_seconds_sum": str(sum(timers["Probe"]) + initial_probe),
            "timer_sums_are_not_an_exhaustive_exclusive_wall_profile": True,
            "table_expansion": {"expanded_tables": 84, "new_bool_table_rule_count": 20607,
                                "new_bool_integer_rule_count": rules["new_bool: integer encoding"],
                                "old_tuples": old_tuples, "refined_tuples": new_tuples,
                                "separate_table_expansion_wall_time_available": False,
                                "old42_tables_implied_by_exact_refined_projection": True,
                                "dropping_old_tables_would_be_a_separate_equivalent_preparation": True},
            "linear_family_census": census,
            "all_linear_terms": all_terms,
            "PSD_and_integer_refinement_terms": dense_terms,
            "PSD_and_integer_refinement_term_fraction": [dense_terms, all_terms],
            "LP_observations": {"components": 4, "iterations": 10588, "added_cuts": 196,
                                "final_relaxation_linear_rows": 27052, "cut_generators": 903,
                                "first_component_final_rows": 1750, "first_component_columns": 18533,
                                "first_component_nonzeros": 123020, "separate_LP_wall_time_available": False,
                                "literal_debug_counters": {"Overflow": 0, "Bad": 70, "BadScaling": 0},
                                "debug_counter_semantics_or_causal_attribution_inferred": False},
            "interpretation": [
                "The native log directly identifies three substantial presolve probes and one search-setup probe. Their printed durations sum to68.6353seconds.",
                "All84 tables were expanded and the table rule created20607Booleans. The log does not report a separate wall-time charge for table expansion.",
                "The92 PSD rows and25 integer refinements are measured separately in the exact original row census. Term dominance is not proof of runtime dominance.",
                "The log records10588LP iterations but no LP-only wall duration or per-original-family timing. It cannot establish that large PSD coefficients caused the timeout or numerical conditioning trouble.",
                "The old42 table constraints are implied by the42 refined tables through the already certified exact projection. Removing them can be prepared with omission witnesses and unchanged full acceptance.",
                "A later bounded probing schedule or lazy exact checking of dense rows would be a separate algorithmic change. No speed or feasibility result is asserted without a new gated experiment."
            ],
            "optimizer_calls": 0, "model_rebuilt": False, "production_outcome_changed": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = analyze()
    with args.output.open("x") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
    print(json.dumps(result, indent=2))
