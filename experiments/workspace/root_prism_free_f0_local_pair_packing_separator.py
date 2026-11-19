"""One local mixed-plus-pair-packing separator, with exact universal lift.

Preparation uses no optimizer. A single bounded numerical LP can propose
potentials. Integer arithmetic on the full eligible-neighbor domain, followed
by a separately owned cold replay, is the only acceptance route for cuts.
"""
import argparse
from fractions import Fraction
import gzip
import hashlib
import importlib.metadata
import importlib.util
from itertools import combinations, product, permutations
import json
from math import gcd, isfinite
from pathlib import Path
import resource
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
WORK, LOGS = "experiments/workspace/", "experiments/logs/root-prism-free/"
ANCHOR = 178
OWNER_SECONDS, NATIVE_SECONDS = 60, 30
SCALES = [1, 2, 3, 4, 6, 12, 24, 60, 120, 720, 4096, 1048576]
SOURCES = {
    "supervisor": (WORK + "root_prism_free_f0_fixed_selection_exterior_query.py", "bbe476e5a7a13800c08265d4db541b7e8c7edf2277be03f6d06db134926891e3"),
    "previous_box_separator": (WORK + "root_prism_free_f0_exterior_row_box_separation.py", "60366da662c74ee8d3ca367dc532c16b652952101fa5725a3248fc5a53a773bd"),
    "retained_attribution": (WORK + "root_prism_free_f0_exterior_retained_attribution.py", "2d4c46c711aa7f031b89b64107376238c2f29704e8dd90ca51bbda4bceff0d76"),
}
INPUTS = {
    "baseline": (LOGS + "f0-boolean-fractional-model.json.gz", "703206929c9c85a40ac4ddcbfb1708c716c288482cf50c77a32249404e35b782"),
    "domain": (LOGS + "f0-exterior-row-domains02.json.gz", "665563b75fa6fc23caa9a002621cc4047809af28543b52b5c2a7ffa592d05dd4"),
    "selection": (LOGS + "f0-direct-literal-query-run01/selection.json", "6c1434b1dbb5a28f19707a3048cb43d64f14370856d03ef7496a3a58fabf4aaa"),
    "literal_cold": (LOGS + "f0-direct-literal-query-run01-cold/report.json", "d9a3cd90320752b08690a761e649210fccc3cef63487f0c72f52f9670226288a"),
    "exterior_cold": (LOGS + "f0-fixed-selection-exterior-query-run01-cold/report.json", "3367e029d8a28ce7195ff7897a2b020d4b3f9cffd2b44c9e955ba048dcf03363"),
    "exterior_cold_owner": (LOGS + "f0-fixed-selection-exterior-query-run01-cold/owner.json", "e600a979c1f5709016fc6bf1d6586cf4dcd30534d2d6b9dc969f19f62ab462b2"),
    "retained_attribution": (LOGS + "f0-exterior-retained-attribution01.json", "a46d4e7ac2a74fc10641db76e16b0d0d7d64be26024ee15a2ae526e113c5d932"),
}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(canonical(value) + b"\n")
    temporary.replace(path)


def read_bound(item):
    path, expected = item
    raw = (ROOT / path).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == expected, path
    return json.loads(gzip.decompress(raw) if path.endswith(".gz") else raw)


def runtime():
    assert sys.flags.optimize == 0
    return {"python_executable": sys.executable, "python_version": sys.version,
            "optimization_level": sys.flags.optimize,
            "highspy_version": importlib.metadata.version("highspy"),
            "numpy_version": importlib.metadata.version("numpy")}


def context():
    for path, expected in SOURCES.values():
        assert digest(ROOT / path) == expected
    loaded = {key: read_bound(item) for key, item in INPUTS.items()}
    baseline, domain = loaded["baseline"]["validation"], loaded["domain"]
    core, triples, selected = baseline["core"], baseline["triples"], loaded["selection"]
    assert len(core) == 21 and all(type(r) is int and 0 <= r < 1 << 21 for r in core)
    assert all(not (core[i] >> i & 1) for i in range(21))
    assert all((core[i] >> j & 1) == (core[j] >> i & 1) for i in range(21) for j in range(21))
    assert len(triples) == len(set(map(tuple, triples))) == 480
    assert all(h == sorted(set(h)) and len(h) == 3 and 0 <= h[0] < h[-1] < 18 for h in triples)
    assert selected == sorted(set(selected)) and len(selected) == 60 and ANCHOR in selected
    assert all(type(a) is int and 0 <= a < 480 for a in selected)
    assert domain["component_core_rows"] == core and domain["signature_domain"] == triples
    adjacency = [(r >> 3) & ((1 << 18) - 1) for r in core[3:]]
    assert adjacency == domain["component_adjacency_rows"]
    for i in range(18):
        for j in range(i, 18):
            expected = 12 * (i == j) + 2 - (core[i + 3] & core[j + 3]).bit_count() - (core[i + 3] >> (j + 3) & 1)
            assert sum(i in triples[a] and j in triples[a] for a in selected) == expected
    assert all(not {a, b} <= set(selected) for a, b in domain["motif_pairs"])
    targets = [[2 - int(i in h) - sum(adjacency[i] >> j & 1 for j in h) for i in range(18)] for h in triples]
    assert targets == domain["row_targets"]
    assert all(sum(q) == 24 and all(x in (0, 1, 2) for x in q) for q in targets)
    edges = baseline["edges"]
    assert len(edges) == len(set(map(tuple, edges))) == 68394
    neighbors = [[] for _ in triples]
    for a, b in edges:
        assert 0 <= a < b < 480
        neighbors[a].append(b)
        neighbors[b].append(a)
    neighbors = [sorted(n) for n in neighbors]
    assert neighbors == domain["possible_neighbor_signature_ids"]
    pairs = list(combinations(range(18), 2))
    pair_position = {p: i for i, p in enumerate(pairs)}
    pair_indices = [[pair_position[p] for p in combinations(h, 2)] for h in triples]
    identity = tuple(range(21))
    group, frontier = {identity}, [identity]
    while frontier:
        old = frontier.pop()
        for generator in domain["core_generators"]:
            image = tuple(generator[old[i]] for i in range(21))
            assert sorted(image) == list(range(21)) and set(image[:3]) == set(range(3))
            assert all((core[i] >> j & 1) == (core[image[i]] >> image[j] & 1) for i in range(21) for j in range(21))
            if image not in group:
                group.add(image)
                frontier.append(image)
    assert len(group) == 12
    positions, actions = {tuple(h): a for a, h in enumerate(triples)}, []
    for image in sorted(group):
        move = [image[i + 3] - 3 for i in range(18)]
        action = [positions[tuple(sorted(move[i] for i in h))] for h in triples]
        pair_action = [pair_position[tuple(sorted((move[i], move[j])))] for i, j in pairs]
        assert sorted(action) == list(range(480)) and sorted(pair_action) == list(range(153))
        assert all(sorted(action[b] for b in neighbors[a]) == neighbors[action[a]] for a in range(480))
        assert all(targets[a][i] == targets[action[a]][move[i]] for a in range(480) for i in range(18))
        actions.append({"core_image": list(image), "component_image": move,
                        "signature_image": action, "pair_image": pair_action})
    # Direct completeness check only at the queried anchor and its actual images.
    anchor_images = sorted({r["signature_image"][ANCHOR] for r in actions})
    for a in anchor_images:
        direct = [b for b in range(480) if b != a and len(set(triples[a]) & set(triples[b])) <= 1
                  and all(targets[a][i] > 0 for i in triples[b]) and all(targets[b][i] > 0 for i in triples[a])]
        assert direct == neighbors[a]
    inside = sorted(set(neighbors[ANCHOR]) & set(selected))
    assert len(neighbors[ANCHOR]) == 244 and len(inside) == 31
    literal = loaded["literal_cold"]
    assert literal["saved_candidate_checked_exactly"] and literal["query_owner_witness_accepted"]
    cold, owner = loaded["exterior_cold"], loaded["exterior_cold_owner"]
    assert owner["report_accepted"] and owner["fixed_selection_excluded"]
    assert owner["report_sha256"] == INPUTS["exterior_cold"][1] and owner["deadline_overrun_seconds"] == 0
    assert owner["supervision"]["child_reaped"] and cold["selection"] == selected
    assert owner["status"] == cold["status"] == "PASS_COLD_REBUILD_RETAINED_INPUTS_AND_DRAT"
    evidence = loaded["retained_attribution"]
    assert evidence["common_primary_signatures"] == [ANCHOR]
    groups = evidence["hit_groups"]
    mixed, packing = [r for r in groups if r["kind"] == "mixed"], [r for r in groups if r["kind"] == "pair_cap"]
    assert len(mixed) == 13 and sum(r["retained_clauses"] for r in mixed) == 111
    assert len(packing) == 5 and sum(r["retained_clauses"] for r in packing) == 5
    prior_pair_witnesses = []
    for r in packing:
        b, c = r["pair_signatures"]
        overlap = sorted(set(triples[b]) & set(triples[c]))
        assert b in inside and c in inside and len(overlap) == 2 and r["pair_capacity"] == 0
        prior_pair_witnesses.append({"neighbors": [b, c], "common_core_pair": overlap})
    ctx = {"triples": triples, "targets": targets, "neighbors": neighbors,
           "selected": selected, "pairs": pairs, "pair_indices": pair_indices, "actions": actions}
    description = {"source_sha256": digest(__file__), "sources": SOURCES, "inputs": INPUTS,
                   "runtime": runtime(), "anchor": ANCHOR, "anchor_triple": triples[ANCHOR],
                   "target": targets[ANCHOR], "selected_signature_ids": selected,
                   "full_eligible_neighbors": neighbors[ANCHOR], "selected_eligible_neighbors": inside,
                   "all_core_pairs": pairs, "verified_core_actions": actions,
                   "anchor_images": anchor_images, "original_full_edge_count": 68394,
                   "retained_local_UNSAT_packing_witnesses": prior_pair_witnesses,
                   "prior_box_LP_used_pair_packing": False, "new_pair_packing_in_LP": True,
                   "prior_UNSAT_used_only_to_choose_anchor": True,
                   "point_zero_or_proved_Y_zero_pruning": False,
                   "owner_seconds_per_stage": OWNER_SECONDS, "native_seconds_maximum": NATIVE_SECONDS,
                   "maximum_native_calls": 1, "rounding_scales": SCALES,
                   "additional_rounding_scale": "maximum exact binary-float denominator",
                   "whole_component_or_graph_exclusion_claimed": False}
    return ctx, json.loads(canonical(description))


def model(ctx):
    inside = sorted(set(ctx["neighbors"][ANCHOR]) & set(ctx["selected"]))
    rows = []
    for k, b in enumerate(inside):
        row = [[i, 1] for i in ctx["triples"][b]]
        row += [[18 + p, -1] for p in ctx["pair_indices"][b]] + [[171 + k, -1]]
        rows.append(sorted(row))
    result = {"sense": "minimize", "variables": 171 + len(inside), "rows": rows,
              "row_lower": "negative_infinity", "row_upper": [0] * len(inside),
              "column_lower": [-1] * 18 + [0] * (153 + len(inside)),
              "column_upper": [1] * 18 + [3] * (153 + len(inside)),
              "cost": [-q for q in ctx["targets"][ANCHOR]] + [1] * (153 + len(inside)),
              "variable_order": "18 signed site potentials;153 lexicographic nonnegative pair potentials;31 selected-neighbor positive parts",
              "nonzeros": sum(map(len, rows)), "selected_neighbor_order": inside}
    assert result["variables"] == 202 and len(rows) == 31 and result["nonzeros"] == 217
    assert all(len(r) == len({j for j, c in r}) == 7 for r in rows)
    assert all(abs(c) == 1 and 0 <= j < 202 for r in rows for j, c in r)
    return result


def elementary_form(columns, q, v, pairs, mu):
    assert len(v) == len(q) and len(mu) == len(pairs)
    assert all(type(x) is int for x in v) and all(type(x) is int and x >= 0 for x in mu)
    weights = [max(0, sum(v[i] for i in h) - sum(m for p, m in zip(pairs, mu) if set(p) <= set(h))) for h in columns]
    return sum(x * y for x, y in zip(v, q)) - sum(mu), weights


def controls():
    columns, pairs = [(0, 1), (0, 2), (1, 2), (0, 1, 2)], list(combinations(range(3), 2))
    binary_checks = fractional_checks = transport_checks = 0
    for v in product((-1, 0, 1), repeat=3):
        for mu in product((0, 1), repeat=3):
            for y in product((0, 1), repeat=4):
                if any(sum(y[j] for j, h in enumerate(columns) if set(p) <= set(h)) > 1 for p in pairs):
                    continue
                q = [sum(y[j] for j, h in enumerate(columns) if i in h) for i in range(3)]
                t, weights = elementary_form(columns, q, v, pairs, mu)
                for x in product((0, 1), repeat=4):
                    if all(y[j] <= x[j] for j in range(4)):
                        assert t <= sum(w * z for w, z in zip(weights, x))
                        binary_checks += 1
            for numerators in product((0, 1, 2), repeat=4):
                if any(sum(numerators[j] for j, h in enumerate(columns) if set(p) <= set(h)) > 2 for p in pairs):
                    continue
                q2 = [sum(numerators[j] for j, h in enumerate(columns) if i in h) for i in range(3)]
                weights = elementary_form(columns, [0] * 3, v, pairs, mu)[1]
                t2 = sum(a * b for a, b in zip(v, q2)) - 2 * sum(mu)
                assert t2 <= 2 * sum(w for w, y in zip(weights, numerators) if y)
                fractional_checks += 1
            q = [2, 1, 1]
            original = elementary_form(columns, q, v, pairs, mu)
            for permutation in permutations(range(3)):
                vp, qp, mp = [0] * 3, [0] * 3, [0] * 3
                for i in range(3):
                    vp[permutation[i]], qp[permutation[i]] = v[i], q[i]
                for p, m in zip(pairs, mu):
                    mp[pairs.index(tuple(sorted(permutation[i] for i in p)))] = m
                renamed = [tuple(sorted(permutation[i] for i in h)) for h in columns]
                assert elementary_form(renamed, qp, vp, pairs, mp) == original
                transport_checks += 1
    # At x_a=0 all incident y vanish; the right side is nonnegative for every x.
    assert all(sum(w * x for w, x in zip([0, 2, 3, 1], bits)) >= 0 for bits in product((0, 1), repeat=4))
    # Mixed equations and [0,1] boxes allow y=(1,1), but pair01 packing forbids it.
    toy_h, toy_q = [(0, 1, 2), (0, 1, 3)], [2, 2, 1, 1]
    toy_pairs = list(combinations(range(4), 2))
    toy_mu = [int(p == (0, 1)) for p in toy_pairs]
    assert [sum(i in h for h in toy_h) for i in range(4)] == toy_q
    assert elementary_form(toy_h, toy_q, [1, 0, 0, 0], toy_pairs, toy_mu) == (1, [0, 0])
    assert sum(set((0, 1)) <= set(h) for h in toy_h) == 2
    rejected_negative = False
    try:
        elementary_form(toy_h, toy_q, [1, 0, 0, 0], toy_pairs, [-1] + [0] * 5)
    except AssertionError:
        rejected_negative = True
    assert rejected_negative
    return {"binary_feasible_activation_checks": binary_checks,
            "half_integral_feasible_checks": fractional_checks, "literal_transport_checks": transport_checks,
            "inactive_anchor_control": True, "box_feasible_packing_infeasible_toy": True,
            "negative_pair_multiplier_rejected": True, "optimizer_or_SAT_calls": 0}


def form(ctx, anchor, v, mu, selection):
    assert len(v) == 18 and len(mu) == 153
    assert all(type(x) is int for x in v) and all(type(x) is int and x >= 0 for x in mu)
    t = sum(x * y for x, y in zip(v, ctx["targets"][anchor])) - sum(mu)
    raw = [[b, sum(v[i] for i in ctx["triples"][b]) - sum(mu[p] for p in ctx["pair_indices"][b])]
           for b in ctx["neighbors"][anchor]]
    positive = [[b, w] for b, w in raw if w > 0]
    capacity = sum(w for b, w in positive if b in selection)
    terms = sorted(([[anchor, t]] if t else []) + [[b, -w] for b, w in positive])
    divisor = gcd(*(abs(c) for b, c in terms)) or 1
    return {"anchor": anchor, "v": v, "mu": mu, "integer_demand": t,
            "full_signed_neighbor_weights": raw, "full_positive_neighbor_weights": positive,
            "selected_positive_capacity": capacity, "strict_integer_gap": t - capacity,
            "row_integer_divisor": divisor,
            "normalized_terms": [[b, c // divisor] for b, c in terms], "upper_bound": 0}


def certificate(ctx, lp, v, mu):
    base = form(ctx, ANCHOR, v, mu, ctx["selected"])
    assert base["strict_integer_gap"] > 0 and base["integer_demand"] > 0
    denominator = max([1] + list(map(abs, v)) + [(x + 2) // 3 for x in mu])
    by_neighbor = dict(base["full_signed_neighbor_weights"])
    normalized_point = v + mu + [max(0, by_neighbor[b]) for b in lp["selected_neighbor_order"]]
    assert all(lo * denominator <= x <= hi * denominator for lo, x, hi in
               zip(lp["column_lower"], normalized_point, lp["column_upper"]))
    assert all(sum(c * normalized_point[j] for j, c in row) <= 0 for row in lp["rows"])
    assert sum(c * x for c, x in zip(lp["cost"], normalized_point)) == -base["strict_integer_gap"]
    transports, unique = [], {}
    for index, action in enumerate(ctx["actions"]):
        move, image, pair_image = action["component_image"], action["signature_image"], action["pair_image"]
        vp, mp = [0] * 18, [0] * 153
        for i, value in enumerate(v):
            vp[move[i]] = value
        for i, value in enumerate(mu):
            mp[pair_image[i]] = value
        selected = sorted(image[b] for b in ctx["selected"])
        f = form(ctx, image[ANCHOR], vp, mp, selected)
        assert f["integer_demand"] == base["integer_demand"]
        assert f["strict_integer_gap"] == base["strict_integer_gap"]
        assert f["full_signed_neighbor_weights"] == sorted([image[b], w] for b, w in base["full_signed_neighbor_weights"])
        transports.append({"action_index": index, "transported_selection": selected, "form": f})
        unique[canonical(f["normalized_terms"])] = f["normalized_terms"]
    return {"base": base, "bounded_LP_exact_denominator": denominator,
            "bounded_LP_exact_objective_numerator": -base["strict_integer_gap"],
            "all12_transports": transports, "distinct_normalized_rows": [unique[k] for k in sorted(unique)],
            "validity_uses_no_candidate_selection_hypothesis": True,
            "requires_separate_accepted_cold_owner": True}


def verify_certificate(ctx, lp, record):
    """Recontract saved rows from literal triples and unordered core pairs."""
    base, transports = record["base"], record["all12_transports"]
    assert base["anchor"] == ANCHOR and len(transports) == 12
    for f, selected in [(base, ctx["selected"])] + [(r["form"], r["transported_selection"]) for r in transports]:
        v, mu, a = f["v"], f["mu"], f["anchor"]
        assert len(v) == 18 and all(type(x) is int for x in v)
        assert len(mu) == 153 and all(type(x) is int and x >= 0 for x in mu)
        pair_weights = dict(zip(combinations(range(18), 2), mu))
        raw = []
        for b in ctx["neighbors"][a]:
            h = ctx["triples"][b]
            value = sum(v[i] for i in h) - sum(pair_weights[(i, j)] for i, j in combinations(h, 2))
            raw.append([b, value])
        t = sum(v[i] * ctx["targets"][a][i] for i in range(18)) - sum(pair_weights.values())
        positive = [[b, w] for b, w in raw if w > 0]
        capacity = sum(w for b, w in positive if b in set(selected))
        assert f["full_signed_neighbor_weights"] == raw and f["full_positive_neighbor_weights"] == positive
        assert f["integer_demand"] == t and f["selected_positive_capacity"] == capacity
        assert f["strict_integer_gap"] == t - capacity > 0
        terms = sorted([[a, t]] + [[b, -w] for b, w in positive])
        divisor = gcd(*(abs(c) for b, c in terms)) or 1
        assert f["row_integer_divisor"] == divisor and f["upper_bound"] == 0
        assert f["normalized_terms"] == [[b, c // divisor] for b, c in terms]
    assert record == certificate(ctx, lp, base["v"], base["mu"])
    return {"literal_neighbor_weight_comparisons": 244 * 13, "all_core_pair_terms_retained": 153,
            "transported_rows": 12, "distinct_rows": len(record["distinct_normalized_rows"]),
            "base_gap": base["strict_integer_gap"], "optimizer_calls": 0}


def proposals(ctx, lp, numeric):
    assert len(numeric) == 171 and all(isfinite(x) for x in numeric)
    # Every native value is only a proposal. Clamp the advertised search box,
    # then round exact binary fractions and recheck the full integer cut.
    rational = [min(Fraction(1), max(Fraction(-1), Fraction(x))) for x in numeric[:18]]
    rational += [min(Fraction(3), max(Fraction(0), Fraction(x))) for x in numeric[18:]]
    scales = list(dict.fromkeys(SCALES + [max(x.denominator for x in rational)]))
    trials = []
    for scale in scales:
        vector = [round(scale * x) for x in rational]
        divisor = gcd(*(abs(x) for x in vector)) or 1
        vector = [x // divisor for x in vector]
        f = form(ctx, ANCHOR, vector[:18], vector[18:], ctx["selected"])
        trials.append({"scale": scale, "potential_gcd": divisor, "gap": f["strict_integer_gap"],
                       "demand": f["integer_demand"], "capacity": f["selected_positive_capacity"]})
        if f["strict_integer_gap"] > 0:
            result = certificate(ctx, lp, vector[:18], vector[18:])
            verify_certificate(ctx, lp, result)
            return trials, result
    return trials, None


def native_query(ctx, lp, directory, deadline):
    result = {"status": "UNKNOWN_BEFORE_NATIVE", "optimizer_calls": 0,
              "exact_cut_pending_cold": False, "graph_or_local_feasibility_claimed": False}
    path = directory / "proposal.json"
    save(path, result)
    import highspy
    import numpy as np
    columns = [[] for _ in range(lp["variables"])]
    for i, row in enumerate(lp["rows"]):
        for j, coefficient in row:
            columns[j].append((i, coefficient))
    starts, indices, values = [0], [], []
    for column in columns:
        indices.extend(i for i, c in column)
        values.extend(c for i, c in column)
        starts.append(len(indices))
    assert len(indices) == lp["nonzeros"] == 217
    problem = highspy.HighsLp()
    problem.num_col_, problem.num_row_ = lp["variables"], len(lp["rows"])
    problem.col_cost_ = np.asarray(lp["cost"], dtype=float)
    problem.col_lower_, problem.col_upper_ = np.asarray(lp["column_lower"], dtype=float), np.asarray(lp["column_upper"], dtype=float)
    problem.row_lower_ = np.full(len(lp["rows"]), -highspy.kHighsInf)
    problem.row_upper_ = np.zeros(len(lp["rows"]))
    problem.a_matrix_.format_ = highspy.MatrixFormat.kColwise
    problem.a_matrix_.start_ = np.asarray(starts, dtype=np.int32)
    problem.a_matrix_.index_ = np.asarray(indices, dtype=np.int32)
    problem.a_matrix_.value_ = np.asarray(values, dtype=float)
    available = min(NATIVE_SECONDS, deadline - time.monotonic() - 5)
    if available <= 0:
        result["status"] = "UNKNOWN_SETUP_EXHAUSTED_OWNER"
    else:
        solver = highspy.Highs()
        for name, value in [("output_flag", False), ("threads", 1), ("parallel", "off"),
                            ("solver", "simplex"), ("presolve", "on"), ("random_seed", 0), ("time_limit", available)]:
            assert solver.setOptionValue(name, value) == highspy.HighsStatus.kOk
        assert solver.passModel(problem) == highspy.HighsStatus.kOk
        result.update(optimizer_calls=1, requested_native_seconds=available)
        save(path, result)
        started = time.monotonic()
        run_status = solver.run()
        elapsed = time.monotonic() - started
        solution = solver.getSolution()
        numeric = list(map(float, solution.col_value))
        result.update(native_seconds=elapsed, native_overrun_seconds=max(0, elapsed - available),
                      native_run_status=str(run_status), native_model_status=str(solver.getModelStatus()),
                      returned_value_valid=bool(solution.value_valid), returned_columns_hex=[x.hex() for x in numeric])
        save(path, result)
        if elapsed > available:
            result["status"] = "UNKNOWN_NATIVE_BUDGET_OVERRUN"
        elif len(numeric) != lp["variables"] or not all(isfinite(x) for x in numeric):
            result["status"] = "UNKNOWN_NO_FINITE_COMPLETE_PROPOSAL"
        else:
            trials, exact = proposals(ctx, lp, numeric[:171])
            result["integer_trials"] = trials
            if exact is None:
                result["status"] = "UNKNOWN_NO_EXACT_LOCAL_PACKING_SEPARATOR"
            else:
                save(directory / "pending-cuts.json", exact)
                result.update(status="EXACT_LOCAL_PACKING_SEPARATOR_PENDING_COLD", exact_cut_pending_cold=True,
                              pending_cuts_sha256=digest(directory / "pending-cuts.json"))
    save(path, result)
    return result


def accepted(directory):
    owner = json.loads((directory / "owner.json").read_bytes())
    assert owner["source_sha256"] == digest(__file__) and owner["maximum_seconds"] == OWNER_SECONDS
    assert owner["report_accepted"] and owner["deadline_overrun_seconds"] == 0
    assert owner["supervision"]["child_reaped"] and owner["supervision"]["returncode"] == 0
    assert owner["report_sha256"] == digest(directory / "report.json")
    report = json.loads((directory / "report.json").read_bytes())
    assert report["status"] == owner["status"]
    return report


def worker(mode, directory, preparation, saved_directory, deadline):
    started = time.monotonic()
    ctx, definition = context()
    lp = model(ctx)
    report = {"definition": definition, "model_sha256": hashlib.sha256(canonical(lp)).hexdigest(),
              "optimizer_calls": 0, "full_graph_constructed": False, "whole_component_excluded": False,
              "cuts_require_accepted_cold_owner": True}
    if mode == "prepare":
        save(directory / "model.json", lp)
        report.update(status="PASS_PREPARATION_NO_OPTIMIZER", controls=controls(),
                      saved_model_sha256=digest(directory / "model.json"), model_dimensions=[31, 202], nonzeros=217)
    else:
        prepared = accepted(preparation)
        assert prepared["status"] == "PASS_PREPARATION_NO_OPTIMIZER" and prepared["definition"] == definition
        assert digest(preparation / "model.json") == prepared["saved_model_sha256"]
        assert json.loads((preparation / "model.json").read_bytes()) == lp
        assert prepared["model_sha256"] == report["model_sha256"]
        report["preparation_sha256"] = digest(preparation / "report.json")
        if mode == "run":
            proposal = native_query(ctx, lp, directory, deadline)
            report.update(status=proposal["status"], optimizer_calls=proposal["optimizer_calls"],
                          proposal_sha256=digest(directory / "proposal.json"))
        else:
            owner = json.loads((saved_directory / "owner.json").read_bytes())
            assert owner["source_sha256"] == digest(__file__) and owner["supervision"]["child_reaped"]
            report.update(status="PASS_COLD_UNACCEPTED_TERMINAL_NO_CUT", run_owner_sha256=digest(saved_directory / "owner.json"))
            if owner["report_accepted"]:
                run = accepted(saved_directory)
                assert run["definition"] == definition and run["preparation_sha256"] == report["preparation_sha256"]
                assert run["model_sha256"] == report["model_sha256"] and 0 <= run["optimizer_calls"] <= 1
                assert digest(saved_directory / "proposal.json") == run["proposal_sha256"]
                proposal = json.loads((saved_directory / "proposal.json").read_bytes())
                assert proposal["status"] == run["status"] and proposal["optimizer_calls"] == run["optimizer_calls"]
                report.update(status="PASS_COLD_NO_EXACT_CUT", run_report_sha256=digest(saved_directory / "report.json"))
                if proposal["exact_cut_pending_cold"]:
                    assert proposal["status"] == "EXACT_LOCAL_PACKING_SEPARATOR_PENDING_COLD"
                    assert proposal["optimizer_calls"] == 1 and proposal["native_overrun_seconds"] == 0
                    path = saved_directory / "pending-cuts.json"
                    assert digest(path) == proposal["pending_cuts_sha256"]
                    exact = json.loads(path.read_bytes())
                    checks = verify_certificate(ctx, lp, exact)
                    numeric = [float.fromhex(x) for x in proposal["returned_columns_hex"]]
                    assert len(numeric) == lp["variables"] and all(isfinite(x) for x in numeric)
                    trials, rebuilt = proposals(ctx, lp, numeric[:171])
                    assert trials == proposal["integer_trials"] and rebuilt == exact
                    save(directory / "replayed-cuts.json", exact)
                    report.update(status="PASS_COLD_EXACT_LOCAL_PACKING_CUTS", exact_checks=checks,
                                  cuts_sha256=digest(directory / "replayed-cuts.json"),
                                  distinct_normalized_rows=exact["distinct_normalized_rows"])
    report.update(seconds=time.monotonic() - started, peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    assert time.monotonic() <= deadline
    save(directory / "report.json", report)


def owned(mode, directory, preparation, saved_directory):
    started = time.monotonic()
    deadline = started + OWNER_SECONDS
    directory.mkdir(parents=True, exist_ok=False)
    command = [sys.executable, str(Path(__file__).resolve()), "_" + mode, "--directory", str(directory.resolve()), "--deadline", str(deadline)]
    if preparation is not None:
        command += ["--preparation", str(preparation.resolve())]
    if saved_directory is not None:
        command += ["--saved-directory", str(saved_directory.resolve())]
    save(directory / "owner.json", {"status": "UNKNOWN_BEFORE_CHILD", "report_accepted": False})
    name, expected = SOURCES["supervisor"]
    assert digest(ROOT / name) == expected
    spec = importlib.util.spec_from_file_location("frozen_local_pair_owner", ROOT / name)
    supervisor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(supervisor)
    supervision = supervisor.supervise(command, directory, deadline)
    owner = {"status": supervision["status"], "supervision": supervision, "source_sha256": digest(__file__),
             "maximum_seconds": OWNER_SECONDS, "report_accepted": False, "certified_new_cuts": False}
    if supervision["status"] == "CHILD_EXITED" and time.monotonic() <= deadline:
        path = directory / "report.json"
        report = json.loads(path.read_bytes())
        owner.update(status=report["status"], report_accepted=True, report_sha256=digest(path))
    owner.update(seconds=time.monotonic() - started, deadline_overrun_seconds=max(0, time.monotonic() - deadline))
    if owner["deadline_overrun_seconds"]:
        owner.update(status="UNKNOWN_HARD_DEADLINE", report_accepted=False)
    if mode == "cold" and owner["report_accepted"] and owner["status"] == "PASS_COLD_EXACT_LOCAL_PACKING_CUTS":
        owner["certified_new_cuts"] = True
    save(directory / "owner.json", owner)
    if owner["certified_new_cuts"]:
        save(directory / "certified-selector-cuts.json", {
            "status": "CERTIFIED_UNIVERSAL_LOCAL_PACKING_SELECTOR_CUTS", "rows_upper_zero": report["distinct_normalized_rows"],
            "cold_report_sha256": digest(directory / "report.json"), "cold_owner_sha256": digest(directory / "owner.json"),
            "run_owner_sha256": report["run_owner_sha256"], "source_sha256": digest(__file__),
            "scope": "Necessary selector inequalities; no new graph or whole-component conclusion."})
    print(json.dumps(owner, sort_keys=True), flush=True)


if __name__ == "__main__":
    assert sys.flags.optimize == 0
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["prepare", "run", "cold", "_prepare", "_run", "_cold"])
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--preparation", type=Path)
    parser.add_argument("--saved-directory", type=Path)
    parser.add_argument("--deadline", type=float)
    args = parser.parse_args()
    mode = args.mode.lstrip("_")
    assert mode == "prepare" or args.preparation is not None
    assert mode != "cold" or args.saved_directory is not None
    if args.mode.startswith("_"):
        assert args.deadline is not None
        worker(mode, args.directory, args.preparation, args.saved_directory, args.deadline)
    else:
        owned(mode, args.directory, args.preparation, args.saved_directory)
