"""Bounded all-anchor packing separation for one cold-checked incidence.

Each of sixty anchors receives at most one numerical proposal. Every retained
cut has exact integer coefficients on the complete eligible domain. Separate
cold verification, with no native import, is required before row export.
"""
import argparse
from fractions import Fraction
import hashlib
import importlib.util
from itertools import combinations
import json
from math import gcd, isfinite
from pathlib import Path
import resource
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
HELPER = ("experiments/workspace/root_prism_free_f0_local_pair_packing_separator.py",
          "750c7959439b28f4ec5c33939b84b17886037a6585de80a148f708a0287e2ee5")
MASTER = ("experiments/workspace/root_prism_free_f0_direct_master_continuation_v3.py",
          "7b828cd3b5c34c846b97913e25bdb860bc7e75afdd7645701503f4a9760b2784")
OWNER_SECONDS, CALL_SECONDS, TOTAL_NATIVE_SECONDS, RESERVE = 60, 1, 30, 5


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def value_sha(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def save(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(canonical(value) + b"\n")
    temporary.replace(path)


def load_source(binding, name):
    path, expected = binding
    assert digest(ROOT / path) == expected
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def helper():
    return load_source(HELPER, "accepted_local_packing_helper")


def context(configuration):
    config = json.loads(configuration.read_bytes())
    assert config["schema"] == "conway99.f0.local-packing-candidate-batch.inputs.v1"
    assert digest(ROOT / MASTER[0]) == MASTER[1]
    loaded = {}
    for key, item in config["inputs"].items():
        raw = (ROOT / item["path"]).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == item["sha256"], key
        loaded[key] = json.loads(raw)
    selected, vector, check, iteration = [loaded[k] for k in ("selection", "candidate", "direct_check", "iteration")]
    run, owner, cold, cold_owner = [loaded[k] for k in ("master_result", "master_owner", "master_cold", "master_cold_owner")]
    for receipt, key, limit in ((owner, "master_result", 300), (cold_owner, "master_cold", 60)):
        assert receipt["source_sha256"] == MASTER[1] and receipt["maximum_seconds"] == limit
        assert receipt["report_accepted"] and receipt["deadline_overrun_seconds"] == 0
        assert receipt["supervision"]["child_reaped"] and receipt["supervision"]["returncode"] == 0
        assert receipt["report_sha256"] == config["inputs"][key]["sha256"]
    assert run["source_sha256"] == cold["definition"]["source_sha256"] == MASTER[1]
    assert cold["status"] == "PASS_COMPLETE_CALLED_PREFIXES_AND_EXACT_CERTIFICATES" and cold["run_owner_accepted"]
    assert cold["run_result_sha256"] == config["inputs"]["master_result"]["sha256"]
    assert cold["run_owner_sha256"] == config["inputs"]["master_owner"]["sha256"]
    assert owner["status"] == run["status"] == cold["original_run_status"]
    index = iteration["index"]
    assert type(index) is int and 0 <= index < len(cold["iterations"])
    assert cold["iterations"][index]["index"] == index and cold["iterations"][index]["direct_candidate_checked"]
    assert iteration["direct_checked"] and iteration["native_overrun_seconds"] == 0
    for field in ("selection", "candidate", "direct_check"):
        assert iteration[field + "_sha256"] == config["inputs"][field]["sha256"]
    assert selected == sorted(set(selected)) and len(selected) == 60
    assert all(type(a) is int and 0 <= a < 480 for a in selected)
    assert len(vector) == 540 and all(type(x) is int for x in vector)
    assert all(x in (0, 1) for x in vector[:480])
    assert selected == [i for i, x in enumerate(vector[:480]) if x]
    assert value_sha(vector) == iteration["candidate_values_sha256"] == check["original"]["values_sha256"]
    assert check["original"]["selected"] == selected
    assert check["original"]["checked_original_equations"] == 172
    assert check["original"]["checked_original_big_integer_cuts"] == 4416
    assert check["original"]["checked_motif_conflicts"] == 90
    assert check["additional"]["extra_rows_checked"] == iteration["registry_rows"]
    assert check["additional"]["registry_sha256"] == iteration["registry_sha256"]
    h = helper()
    old_context, _ = h.context()
    ctx = dict(old_context, selected=selected)
    triples, targets, neighbors = [ctx[k] for k in ("triples", "targets", "neighbors")]
    for a in range(480):
        direct = [b for b in range(480) if b != a and len(set(triples[a]) & set(triples[b])) <= 1
                  and all(targets[a][i] > 0 for i in triples[b]) and all(targets[b][i] > 0 for i in triples[a])]
        assert direct == neighbors[a]
    description = {"schema": "conway99.f0.local-packing-candidate-batch.v1", "source_sha256": digest(__file__),
                   "helper_source": HELPER, "master_source": MASTER,
                   "configuration_sha256": digest(configuration), "configuration": config,
                   "selected_signature_ids": selected, "all60_anchors_in_fixed_order": selected,
                   "complete_eligible_edges": sum(map(len, neighbors)) // 2,
                   "candidate_index": index, "candidate_selection_is_not_a_cut_hypothesis": True,
                   "old_anchor178_used_only_for_frozen_domain_context": True,
                   "per_call_seconds": CALL_SECONDS, "cumulative_native_seconds": TOTAL_NATIVE_SECONDS,
                   "owner_seconds_per_stage": OWNER_SECONDS, "maximum_native_calls": 60,
                   "rounding_scales": h.SCALES, "additional_scale": "maximum exact binary-float denominator",
                   "local_or_graph_feasibility_claimed": False, "requires_accepted_cold_owner": True}
    assert description["complete_eligible_edges"] == 68394
    return h, ctx, json.loads(canonical(description))


def model(ctx, anchor):
    inside = sorted(set(ctx["neighbors"][anchor]) & set(ctx["selected"]))
    rows = [sorted([[i, 1] for i in ctx["triples"][b]] + [[18 + p, -1] for p in ctx["pair_indices"][b]] + [[171 + k, -1]])
            for k, b in enumerate(inside)]
    result = {"anchor": anchor, "variables": 171 + len(inside), "rows": rows,
              "column_lower": [-1] * 18 + [0] * (153 + len(inside)),
              "column_upper": [1] * 18 + [3] * (153 + len(inside)),
              "cost": [-q for q in ctx["targets"][anchor]] + [1] * (153 + len(inside)),
              "selected_neighbor_order": inside, "nonzeros": 7 * len(inside)}
    assert all(len(row) == len({j for j, _ in row}) == 7 for row in rows)
    assert all(abs(c) == 1 and 0 <= j < result["variables"] for row in rows for j, c in row)
    return result


def make_certificate(h, ctx, lp, v, mu):
    anchor = lp["anchor"]
    base = h.form(ctx, anchor, v, mu, ctx["selected"])
    assert base["strict_integer_gap"] > 0 and base["integer_demand"] > 0
    denominator = max([1] + list(map(abs, v)) + [(m + 2) // 3 for m in mu])
    weights = dict(base["full_signed_neighbor_weights"])
    exact_point = v + mu + [max(0, weights[b]) for b in lp["selected_neighbor_order"]]
    assert all(lo * denominator <= x <= hi * denominator for lo, x, hi in zip(lp["column_lower"], exact_point, lp["column_upper"]))
    assert all(sum(c * exact_point[j] for j, c in row) <= 0 for row in lp["rows"])
    assert sum(c * x for c, x in zip(lp["cost"], exact_point)) == -base["strict_integer_gap"]
    transports, unique = [], {}
    for index, action in enumerate(ctx["actions"]):
        move, image, pair_image = [action[k] for k in ("component_image", "signature_image", "pair_image")]
        vp, mp = [0] * 18, [0] * 153
        for i, value in enumerate(v):
            vp[move[i]] = value
        for i, value in enumerate(mu):
            mp[pair_image[i]] = value
        moved_selection = sorted(image[b] for b in ctx["selected"])
        f = h.form(ctx, image[anchor], vp, mp, moved_selection)
        assert f["integer_demand"] == base["integer_demand"] and f["strict_integer_gap"] == base["strict_integer_gap"]
        assert f["full_signed_neighbor_weights"] == sorted([image[b], w] for b, w in base["full_signed_neighbor_weights"])
        transports.append({"action_index": index, "transported_selection": moved_selection, "form": f})
        unique[canonical(f["normalized_terms"])] = f["normalized_terms"]
    return {"base": base, "exact_bounded_LP_denominator": denominator,
            "all12_transports": transports, "distinct_normalized_rows": [unique[k] for k in sorted(unique)],
            "selection_is_not_a_cut_hypothesis": True}


def verify_certificate(h, ctx, lp, certificate):
    assert certificate["base"]["anchor"] == lp["anchor"] and len(certificate["all12_transports"]) == 12
    checked = 0
    for f, selected in [(certificate["base"], ctx["selected"])] + [(r["form"], r["transported_selection"]) for r in certificate["all12_transports"]]:
        v, mu, a = f["v"], f["mu"], f["anchor"]
        assert len(v) == 18 and all(type(x) is int for x in v)
        assert len(mu) == 153 and all(type(x) is int and x >= 0 for x in mu)
        pair_weights = dict(zip(combinations(range(18), 2), mu))
        raw = [[b, sum(v[i] for i in ctx["triples"][b]) - sum(pair_weights[p] for p in combinations(ctx["triples"][b], 2))]
               for b in ctx["neighbors"][a]]
        t = sum(v[i] * ctx["targets"][a][i] for i in range(18)) - sum(mu)
        positive = [[b, w] for b, w in raw if w > 0]
        capacity = sum(w for b, w in positive if b in set(selected))
        assert f["full_signed_neighbor_weights"] == raw and f["full_positive_neighbor_weights"] == positive
        assert f["integer_demand"] == t > 0 and f["selected_positive_capacity"] == capacity
        assert f["strict_integer_gap"] == t - capacity > 0
        terms = sorted([[a, t]] + [[b, -w] for b, w in positive])
        divisor = gcd(*(abs(c) for _, c in terms)) or 1
        assert f["row_integer_divisor"] == divisor and f["upper_bound"] == 0
        assert f["normalized_terms"] == [[b, c // divisor] for b, c in terms]
        checked += len(raw)
    assert certificate == make_certificate(h, ctx, lp, certificate["base"]["v"], certificate["base"]["mu"])
    return checked


def propose(h, ctx, lp, numeric):
    assert len(numeric) == 171 and all(isfinite(x) for x in numeric)
    rational = [min(Fraction(1), max(Fraction(-1), Fraction(x))) for x in numeric[:18]]
    rational += [min(Fraction(3), max(Fraction(0), Fraction(x))) for x in numeric[18:]]
    scales = list(dict.fromkeys(h.SCALES + [max(x.denominator for x in rational)]))
    trials = []
    for scale in scales:
        vector = [round(scale * x) for x in rational]
        divisor = gcd(*(abs(x) for x in vector)) or 1
        vector = [x // divisor for x in vector]
        f = h.form(ctx, lp["anchor"], vector[:18], vector[18:], ctx["selected"])
        trials.append({"scale": scale, "gcd": divisor, "gap": f["strict_integer_gap"], "demand": f["integer_demand"]})
        if f["strict_integer_gap"] > 0:
            certificate = make_certificate(h, ctx, lp, vector[:18], vector[18:])
            verify_certificate(h, ctx, lp, certificate)
            return trials, certificate
    return trials, None


def native_one(lp, allowance):
    import highspy
    import numpy as np
    columns = [[] for _ in range(lp["variables"])]
    for i, row in enumerate(lp["rows"]):
        for j, coefficient in row:
            columns[j].append((i, coefficient))
    starts, indices, values = [0], [], []
    for column in columns:
        indices.extend(i for i, _ in column)
        values.extend(c for _, c in column)
        starts.append(len(indices))
    assert len(indices) == lp["nonzeros"]
    problem = highspy.HighsLp()
    problem.num_col_, problem.num_row_ = lp["variables"], len(lp["rows"])
    problem.col_cost_ = np.asarray(lp["cost"], dtype=float)
    problem.col_lower_, problem.col_upper_ = np.asarray(lp["column_lower"], dtype=float), np.asarray(lp["column_upper"], dtype=float)
    problem.row_lower_, problem.row_upper_ = np.full(len(lp["rows"]), -highspy.kHighsInf), np.zeros(len(lp["rows"]))
    problem.a_matrix_.format_ = highspy.MatrixFormat.kColwise
    problem.a_matrix_.start_ = np.asarray(starts, dtype=np.int32)
    problem.a_matrix_.index_ = np.asarray(indices, dtype=np.int32)
    problem.a_matrix_.value_ = np.asarray(values, dtype=float)
    solver = highspy.Highs()
    options = [("output_flag", False), ("threads", 1), ("parallel", "off"), ("solver", "simplex"),
               ("presolve", "on"), ("random_seed", 0), ("time_limit", allowance)]
    for key, value in options:
        assert solver.setOptionValue(key, value) == highspy.HighsStatus.kOk
    assert solver.passModel(problem) == highspy.HighsStatus.kOk
    started = time.monotonic()
    native_status = solver.run()
    elapsed = time.monotonic() - started
    solution = solver.getSolution()
    numeric = list(map(float, solution.col_value))
    return {"native_seconds": elapsed, "native_overrun_seconds": max(0, elapsed - allowance),
            "native_status": str(native_status), "native_model_status": str(solver.getModelStatus()),
            "value_valid": bool(solution.value_valid), "returned_columns_hex": [x.hex() for x in numeric],
            "options": options}, numeric


def accepted(directory):
    owner = json.loads((directory / "owner.json").read_bytes())
    assert owner["source_sha256"] == digest(__file__) and owner["maximum_seconds"] == OWNER_SECONDS
    assert owner["report_accepted"] and owner["deadline_overrun_seconds"] == 0
    assert owner["supervision"]["child_reaped"] and owner["supervision"]["returncode"] == 0
    assert owner["report_sha256"] == digest(directory / "report.json")
    report = json.loads((directory / "report.json").read_bytes())
    assert report["status"] == owner["status"]
    return report


def run_batch(h, ctx, models, directory, deadline):
    result = {"records": [], "optimizer_calls": 0, "native_seconds": 0.0, "cut_anchors": [],
              "termination": "COMPLETE_ALL60_ANCHORS", "whole_component_excluded": False}
    save(directory / "batch.json", result)
    for index, lp in enumerate(models):
        allowance = max(0.0, min(CALL_SECONDS, TOTAL_NATIVE_SECONDS - result["native_seconds"], deadline - time.monotonic() - RESERVE))
        if allowance <= 0:
            result["termination"] = "OWNER_OR_CUMULATIVE_NATIVE_BUDGET"
            break
        sub = directory / ("anchor-%03d" % lp["anchor"])
        sub.mkdir()
        record = {"index": index, "anchor": lp["anchor"], "model_sha256": value_sha(lp),
                  "allowance": allowance, "status": "NATIVE_ACTIVE", "exact_cut": False}
        save(sub / "proposal.json", record)
        result["records"].append(sub.name)
        result["optimizer_calls"] += 1
        save(directory / "batch.json", result)
        native, numeric = native_one(lp, allowance)
        record.update(native)
        result["native_seconds"] += native["native_seconds"]
        record["cumulative_native_seconds"] = result["native_seconds"]
        save(sub / "proposal.json", record)
        if native["native_overrun_seconds"] or result["native_seconds"] > TOTAL_NATIVE_SECONDS:
            record["status"] = "UNKNOWN_NATIVE_BUDGET_OVERRUN"
            result["termination"] = "NATIVE_BUDGET_OVERRUN"
        elif len(numeric) != lp["variables"] or not all(isfinite(x) for x in numeric):
            record["status"] = "UNKNOWN_NO_FINITE_COMPLETE_PROPOSAL"
        else:
            trials, certificate = propose(h, ctx, lp, numeric[:171])
            record.update(integer_trials=trials, status="NO_EXACT_CUT_FROM_THIS_PROPOSAL")
            if certificate is not None:
                save(sub / "pending-cuts.json", certificate)
                record.update(status="EXACT_CUT_PENDING_COLD", exact_cut=True,
                              pending_cuts_sha256=digest(sub / "pending-cuts.json"))
                result["cut_anchors"].append(lp["anchor"])
        save(sub / "proposal.json", record)
        save(directory / "batch.json", result)
        if result["termination"] == "NATIVE_BUDGET_OVERRUN":
            break
    save(directory / "batch.json", result)
    return {"status": "EXACT_LOCAL_PACKING_BATCH_PENDING_COLD" if result["cut_anchors"] else "NO_EXACT_LOCAL_PACKING_CUT",
            "batch_sha256": digest(directory / "batch.json"), "optimizer_calls": result["optimizer_calls"],
            "native_seconds": result["native_seconds"], "cut_anchors": result["cut_anchors"], "termination": result["termination"]}


def replay_batch(h, ctx, models, saved_directory, definition, preparation_sha256):
    owner = json.loads((saved_directory / "owner.json").read_bytes())
    assert owner["source_sha256"] == digest(__file__) and owner["supervision"]["child_reaped"]
    if not owner["report_accepted"]:
        return {"status": "PASS_COLD_UNACCEPTED_RUN_NO_CUT", "run_owner_sha256": digest(saved_directory / "owner.json")}
    run = accepted(saved_directory)
    assert run["definition"] == definition and run["preparation_sha256"] == preparation_sha256
    assert run["models_sha256"] == value_sha(models)
    assert run["batch_sha256"] == digest(saved_directory / "batch.json")
    batch = json.loads((saved_directory / "batch.json").read_bytes())
    count = len(batch["records"])
    assert 0 <= count <= 60 and batch["optimizer_calls"] == run["optimizer_calls"] == count
    assert batch["records"] == ["anchor-%03d" % lp["anchor"] for lp in models[:count]]
    used, anchors, rows, checked = 0.0, [], {}, 0
    for index, name in enumerate(batch["records"]):
        lp, sub = models[index], saved_directory / name
        record = json.loads((sub / "proposal.json").read_bytes())
        assert record["index"] == index and record["anchor"] == lp["anchor"] and record["model_sha256"] == value_sha(lp)
        allowance = record["allowance"]
        assert 0 < allowance <= min(CALL_SECONDS, TOTAL_NATIVE_SECONDS - used)
        elapsed = record["native_seconds"]
        assert isfinite(elapsed) and elapsed >= 0
        used += elapsed
        assert record["cumulative_native_seconds"] == used
        assert record["native_overrun_seconds"] == max(0, elapsed - allowance)
        assert record["options"] == [["output_flag", False], ["threads", 1], ["parallel", "off"], ["solver", "simplex"],
                                     ["presolve", "on"], ["random_seed", 0], ["time_limit", allowance]]
        numeric = [float.fromhex(x) for x in record["returned_columns_hex"]]
        if record["native_overrun_seconds"] or used > TOTAL_NATIVE_SECONDS:
            assert record["status"] == "UNKNOWN_NATIVE_BUDGET_OVERRUN" and not record["exact_cut"]
            assert index == count - 1 and batch["termination"] == "NATIVE_BUDGET_OVERRUN"
        elif len(numeric) != lp["variables"] or not all(isfinite(x) for x in numeric):
            assert record["status"] == "UNKNOWN_NO_FINITE_COMPLETE_PROPOSAL" and not record["exact_cut"]
        else:
            trials, certificate = propose(h, ctx, lp, numeric[:171])
            assert trials == record["integer_trials"] and record["exact_cut"] == (certificate is not None)
            if certificate is None:
                assert record["status"] == "NO_EXACT_CUT_FROM_THIS_PROPOSAL"
            else:
                assert record["status"] == "EXACT_CUT_PENDING_COLD"
                assert digest(sub / "pending-cuts.json") == record["pending_cuts_sha256"]
                saved = json.loads((sub / "pending-cuts.json").read_bytes())
                assert saved == certificate
                checked += verify_certificate(h, ctx, lp, saved)
                anchors.append(lp["anchor"])
                for row in certificate["distinct_normalized_rows"]:
                    rows[canonical(row)] = row
    assert used == batch["native_seconds"] == run["native_seconds"]
    assert anchors == batch["cut_anchors"] == run["cut_anchors"]
    assert batch["termination"] == run["termination"]
    if batch["termination"] == "COMPLETE_ALL60_ANCHORS":
        assert count == 60
    else:
        assert batch["termination"] in ("OWNER_OR_CUMULATIVE_NATIVE_BUDGET", "NATIVE_BUDGET_OVERRUN")
    assert run["status"] == ("EXACT_LOCAL_PACKING_BATCH_PENDING_COLD" if anchors else "NO_EXACT_LOCAL_PACKING_CUT")
    return {"status": "PASS_COLD_EXACT_LOCAL_PACKING_BATCH" if rows else "PASS_COLD_NO_EXACT_CUT",
            "run_report_sha256": digest(saved_directory / "report.json"), "run_owner_sha256": digest(saved_directory / "owner.json"),
            "anchors_checked": count, "cut_anchors": anchors, "termination": batch["termination"],
            "literal_neighbor_weights_checked": checked, "rows_upper_zero": [rows[k] for k in sorted(rows)],
            "optimizer_calls": 0}


def worker(mode, configuration, directory, preparation, saved_directory, deadline):
    started = time.monotonic()
    h, ctx, description = context(configuration)
    models = [model(ctx, a) for a in ctx["selected"]]
    report = {"definition": description, "models_sha256": value_sha(models), "optimizer_calls": 0,
              "whole_component_excluded": False, "graph_constructed": False}
    if mode == "prepare":
        save(directory / "models.json", models)
        report.update(status="PASS_ALL60_MODELS_NO_OPTIMIZER", models_file_sha256=digest(directory / "models.json"),
                      models=60, total_variables=sum(m["variables"] for m in models),
                      total_rows=sum(len(m["rows"]) for m in models), native_imports=0)
    else:
        prepared = accepted(preparation)
        assert prepared["status"] == "PASS_ALL60_MODELS_NO_OPTIMIZER" and prepared["definition"] == description
        assert prepared["models_sha256"] == report["models_sha256"]
        assert digest(preparation / "models.json") == prepared["models_file_sha256"]
        assert json.loads((preparation / "models.json").read_bytes()) == models
        report["preparation_sha256"] = digest(preparation / "report.json")
        if mode == "run":
            report.update(run_batch(h, ctx, models, directory, deadline))
        else:
            report.update(replay_batch(h, ctx, models, saved_directory, description, report["preparation_sha256"]))
    report.update(seconds=time.monotonic() - started, peak_rss_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    assert time.monotonic() <= deadline
    save(directory / "report.json", report)


def owned(mode, configuration, directory, preparation, saved_directory):
    started = time.monotonic()
    deadline = started + OWNER_SECONDS
    directory.mkdir(parents=True, exist_ok=False)
    command = [sys.executable, str(Path(__file__).resolve()), "_" + mode, "--configuration", str(configuration.resolve()),
               "--directory", str(directory.resolve()), "--deadline", str(deadline)]
    if preparation is not None:
        command += ["--preparation", str(preparation.resolve())]
    if saved_directory is not None:
        command += ["--saved-directory", str(saved_directory.resolve())]
    save(directory / "owner.json", {"status": "UNKNOWN_BEFORE_CHILD", "report_accepted": False})
    supervision = load_source(helper().SOURCES["supervisor"], "accepted_packing_batch_owner").supervise(command, directory, deadline)
    owner = {"source_sha256": digest(__file__), "maximum_seconds": OWNER_SECONDS, "supervision": supervision,
             "status": supervision["status"], "report_accepted": False, "certified_new_cuts": False}
    if supervision["status"] == "CHILD_EXITED" and time.monotonic() <= deadline:
        report = json.loads((directory / "report.json").read_bytes())
        owner.update(report_accepted=True, report_sha256=digest(directory / "report.json"), status=report["status"])
    owner.update(seconds=time.monotonic() - started, deadline_overrun_seconds=max(0, time.monotonic() - deadline))
    if owner["deadline_overrun_seconds"]:
        owner.update(report_accepted=False, status="UNKNOWN_HARD_DEADLINE")
    if mode == "cold" and owner["report_accepted"] and owner["status"] == "PASS_COLD_EXACT_LOCAL_PACKING_BATCH":
        owner["certified_new_cuts"] = True
    save(directory / "owner.json", owner)
    if owner["certified_new_cuts"]:
        save(directory / "certified-selector-cuts.json", {"status": "CERTIFIED_UNIVERSAL_LOCAL_PACKING_BATCH_CUTS",
             "rows_upper_zero": report["rows_upper_zero"], "cold_report_sha256": digest(directory / "report.json"),
             "cold_owner_sha256": digest(directory / "owner.json"), "run_owner_sha256": report["run_owner_sha256"],
             "source_sha256": digest(__file__), "scope": "Universal necessary selector rows; no whole-component exclusion."})
    print(json.dumps(owner, sort_keys=True), flush=True)


if __name__ == "__main__":
    assert sys.flags.optimize == 0
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["prepare", "run", "cold", "_prepare", "_run", "_cold"])
    parser.add_argument("--configuration", type=Path, required=True)
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
        worker(mode, args.configuration, args.directory, args.preparation, args.saved_directory, args.deadline)
    else:
        owned(mode, args.configuration, args.directory, args.preparation, args.saved_directory)
