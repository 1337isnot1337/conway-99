"""Bounded exact odd-three-set matching inequalities at all 18 F0 core sites.

prepare() only binds inputs, domains, scope and arithmetic controls.
The owned census and separately owned cold replay require coordinator review.
No local-profile reconstruction, production point, native model or optimizer occurs.
"""
import argparse
from collections import Counter
import gzip
import hashlib
from itertools import combinations, islice
import json
from math import comb, gcd
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "experiments/logs/root-prism-free"
INPUTS = {
    "literal_model": ("f0-boolean-fractional-model.json.gz", "703206929c9c85a40ac4ddcbfb1708c716c288482cf50c77a32249404e35b782"),
    "domains": ("f0-orbit-populations02-domains.json.gz", "4f079468530dba0746512cc4afce01666b2a63a2c8f35f66a4660a4fe3bab8ab"),
    "live_edges": ("f0-edge-orbit-packing-preparation01.json.gz", "2d581d92545eb1d8718960471fe8c4bfe191a6a80a9f9d5d22754dc4afe0ec18"),
    "current_domains": ("f0-character-y-domain-overlay01/plan.json.gz", "4d3a13718cdac9fcf68b119a1cd1ba009edeb21c7257d4498d5ebdf18954acc4"),
    "one_proof": ("f0-core-matching-one-blossom01.json", "d5de76ce7978221843a44be9cca703e53c7153decb5088f598d016b7279088f8"),
    "one_cold": ("f0-core-matching-one-blossom01-cold.json", "71530fb3beb5c824ff93176c3dc396e3b5256a49f06f07688cde3efc1e8356c2"),
    "Y_result": ("f0-edge-orbit-packing-scan01.json.gz", "5b9614ca91185e380bbc7fd220d797c983a5a4c6756942686f51efca57be1c2d"),
    "Y_ledger": ("f0-edge-orbit-packing-scan01-ledger.jsonl.gz", "75c5ba7443d0740e4ffa35828e70c25c28ffe4e18f398d2454315901f2cc7735"),
    "Y_cold": ("f0-edge-orbit-packing-scan01-cold.json", "8965162db2cd4bfc05c129ecd5cf0a1ba2b39bcbd35f776cc60c27a52c501ded"),
}
ONE_SOURCE = ("experiments/workspace/root_prism_free_f0_core_matching_blossom.py",
              "a00a588a3c0bd366fbc6f6e8df2e0b00b0e19dc616e48a64077da7ffe03c61bf")
LIMITS = {"owner_seconds": 60, "child_seconds": 55, "raw_ledger_bytes": 64 << 20,
          "reserved_metadata_bytes": 1 << 20, "automatic_retries": 0,
          "optimizer_calls": 0, "maximum_core_sites": 18, "maximum_triples": 549480}
DISPOSITIONS = ("missing_eligible_edge", "contains_proved_zero_Y_edge", "live_three_edge_clique")


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def read_raw(name):
    filename, expected = INPUTS[name]
    raw = (BASE / filename).read_bytes()
    assert sha(raw) == expected, name
    return gzip.decompress(raw) if filename.endswith(".gz") else raw


def read(name):
    return json.loads(read_raw(name))


def binding():
    assert sha((ROOT / ONE_SOURCE[0]).read_bytes()) == ONE_SOURCE[1]
    return {"source_sha256": sha(Path(__file__).read_bytes()),
            "single_proof_source": {"path": ONE_SOURCE[0], "sha256": ONE_SOURCE[1]},
            "inputs": {k: {"path": str((BASE / p).relative_to(ROOT)), "sha256": h}
                       for k, (p, h) in INPUTS.items()}, "limits": LIMITS}


def tick(deadline):
    if time.monotonic() >= deadline:
        raise TimeoutError("finite blossom stage cooperative limit")


def normalize(terms, rhs=12):
    terms = Counter({int(j): int(c) for j, c in terms.items() if c})
    assert rhs > 0 and terms and min(terms.values()) > 0
    divisor = rhs
    for c in terms.values():
        divisor = gcd(divisor, c)
    return tuple((j, c // divisor) for j, c in sorted(terms.items())), rhs // divisor, divisor


def controls():
    assert normalize(Counter({7: 3})) == (((7, 1),), 4, 3)
    assert normalize(Counter({7: 2, 11: 2})) == (((7, 1), (11, 1)), 6, 2)
    assert normalize(Counter({7: 2, 11: 1})) == (((7, 2), (11, 1)), 12, 1)
    assert normalize(Counter({96: 1, 103: 1, 4477: 1})) == (
        ((96, 1), (103, 1), (4477, 1)), 12, 1)
    return {"positive_gcd_and_repeated_orbit_controls": 4,
            "fixed_star_truth_table_reused_from_bound_single_proof": True}


def load(deadline):
    b = binding()
    model, domain, graphs, target, proof, cold, yr, yc = [
        read(k) for k in ("literal_model", "domains", "live_edges", "current_domains",
                          "one_proof", "one_cold", "Y_result", "Y_cold")]
    tick(deadline)
    assert proof["source_sha256"] == cold["source_sha256"] == ONE_SOURCE[1]
    assert cold["status"].startswith("PASS") and cold["record_sha256"] == INPUTS["one_proof"][1]
    assert proof["orbit_count_row"]["terms"] == [[96, 1], [103, 1], [4477, 1]]
    assert yc["status"].startswith("PASS") and yc["complete_saved_prefix_checked"]
    assert yc["checked_orbits"] == 5643 and yc["record_sha256"] == INPUTS["Y_result"][1]
    assert yr["complete"] and yr["ledger_sha256"] == INPUTS["Y_ledger"][1]
    literal = model["validation"]
    triples, edges, orbits = [literal[k] for k in ("triples", "edges", "edge_orbits")]
    assert len(triples) == 480 and len(edges) == 68394 and len(orbits) == 5805
    assert edges == sorted(edges) and len({tuple(e) for e in edges}) == len(edges)
    sets = [r["possible_signatures"] for r in proof["matching_sets"]]
    assert [r["core_site"] for r in proof["matching_sets"]] == list(range(18))
    assert all(r["rhs"] == 8 for r in proof["matching_sets"])
    assert sets == [[a for a, h in enumerate(triples) if i in h and literal["targets"][a][i] == 1]
                    for i in range(18)]
    assert list(map(len, sets)) == [50] * 6 + [61] * 12
    assert sum(comb(len(U), 3) for U in sets) == LIMITS["maximum_triples"]
    edge_pos = {tuple(e): k for k, e in enumerate(edges)}
    orbit_of = [-1] * len(edges)
    for oi, members in enumerate(orbits):
        assert len(members) > 0 and 12 % len(members) == 0
        for e in members:
            assert orbit_of[e] == -1
            orbit_of[e] = oi
    assert min(orbit_of) >= 0
    inverse = {old: new for new, old in enumerate(domain["new15038_to_original15589"])}
    zeros = {j-42 for j in domain["original_Y_zero_columns"]}
    live = {r["edge_orbit"]: r for r in graphs["records"]}
    assert len(zeros) == 162 and set(live) == set(range(5805)) - zeros
    columns = {}
    for oi, r in live.items():
        assert r["literal_edge_ids"] == orbits[oi]
        assert r["literal_edges"] == [edges[e] for e in orbits[oi]]
        assert r["reduced_count_column"] == inverse[42+oi]
        columns[oi] = inverse[42+oi]
    packing = {}
    raw_ledger = read_raw("Y_ledger")
    assert sha(raw_ledger) == yr["ledger_raw_sha256"]
    for line in raw_ledger.splitlines():
        r = json.loads(line)
        oi, j = r["edge_orbit"], r["count_column"]
        assert oi in live and j == columns[oi] and j not in packing
        assert 1 <= r["bound"] <= len(orbits[oi])
        packing[j] = r["bound"]
    assert len(packing) == 5643
    boxes = target["target_variable_domains"]
    assert len(boxes) == 18444
    assert all(boxes[j][-1] <= packing[j] for j in columns.values())
    literal_rows = model["Boolean_validation"]["full_rows"]
    assert len(literal_rows) == 4416
    assert all(all(0 <= a < 480 and int(c) != 0 for a, c in r["terms"]) for r in literal_rows)
    assert domain["group_order"] == 12 and len(domain["signature_actions"]) == 12
    assert len(domain["actual_core_actions"]) == 12
    tick(deadline)
    return {"binding": b, "literal": literal, "domain": domain, "sets": sets,
            "edge_pos": edge_pos, "orbit_of": orbit_of, "columns": columns,
            "zero_orbits": zeros, "packing": packing, "boxes": boxes,
            "actions": domain["signature_actions"], "core_actions": domain["actual_core_actions"]}


def scope(data):
    sizes = list(map(len, data["sets"]))
    return {"core_sites": 18, "U_sizes": sizes,
            "triple_bounds": [comb(n, 3) for n in sizes],
            "total_triple_bound": sum(comb(n, 3) for n in sizes),
            "maximum_transported_edge_images_bound": 36 * sum(comb(n, 3) for n in sizes),
            "literal_subset_domain_reenumerated": False,
            "retained_case": "All three literal edge variables exist and their Y orbit is not a proved zero.",
            "skipped_case_justification": "A triangle with at most two live edges is already a star, whose sum is at most its endpoint selector and hence at most one.",
            "coverage_order": "core site 0..17, then lexicographic combinations of its frozen sorted U_i",
            "literal_rows_compared": 4416, "literal_identical_Y_rows": 0,
            "literal_comparison_reason": "All old literal rows use selector coordinates; each new row has nonempty edge-count support.",
            "saved_Y_packing_bounds": 5643, "current_domain_variables": 18444,
            "full_model_redundance_test_claimed": False}


def classification(data, S):
    ids = [data["edge_pos"].get(e) for e in combinations(S, 2)]
    if any(e is None for e in ids):
        return DISPOSITIONS[0], None
    ois = [data["orbit_of"][e] for e in ids]
    if any(oi in data["zero_orbits"] for oi in ois):
        return DISPOSITIONS[1], None
    return DISPOSITIONS[2], (ids, ois)


def form(data, ois):
    terms = Counter()
    for oi in ois:
        terms[data["columns"][oi]] += 12 // len(data["literal"]["edge_orbits"][oi])
    return normalize(terms)


def compare(data, key):
    terms, rhs = key
    packing_value = sum(c * data["packing"][j] for j, c in terms)
    box_value = sum(c * data["boxes"][j][-1] for j, c in terms)
    return {"identical_saved_Y_packing_row": len(terms) == 1 and terms[0][1] == 1
            and data["packing"][terms[0][0]] == rhs,
            "implied_by_saved_Y_packing_boxes": packing_value <= rhs,
            "implied_by_current_explicit_boxes": box_value <= rhs,
            "packing_box_maximum": packing_value, "current_box_maximum": box_value,
            "identical_original_literal_selector_row": False}


def witness(data, site, S, ids, ois, row_id):
    terms, rhs, divisor = form(data, ois)
    counts, transports = Counter(), []
    for g, move in zip(data["actions"], data["core_actions"]):
        T = [g[a] for a in S]
        assert all(move[site] in data["literal"]["triples"][a]
                   and data["literal"]["targets"][a][move[site]] == 1 for a in T)
        moved_ids = [data["edge_pos"][tuple(sorted((g[a], g[b])))] for a, b in combinations(S, 2)]
        assert [data["orbit_of"][e] for e in moved_ids] == ois
        counts.update(moved_ids)
        transports.append([move[site], *T, *moved_ids])
    actual_terms = {}
    for oi in set(ois):
        members = data["literal"]["edge_orbits"][oi]
        coefficients = {counts[e] for e in members}
        assert len(coefficients) == 1
        actual_terms[data["columns"][oi]] = coefficients.pop()
    assert normalize(actual_terms) == (terms, rhs, divisor)
    assert set(counts) == {e for oi in ois for e in data["literal"]["edge_orbits"][oi]}
    return {"id": row_id, "terms": [list(t) for t in terms], "rhs": rhs,
            "positive_normalization_divisor": divisor,
            "witness": {"core_site": site, "signatures": list(S), "literal_edges": ids,
                        "edge_orbits": ois, "all12_transports": transports,
                        "summed_literal_coefficients": [[e, counts[e]] for e in sorted(counts)]},
            "comparison": compare(data, (terms, rhs))}


def atomic(path, value):
    raw = canonical(value) + b"\n"
    temp = path.with_name(path.name + ".temporary")
    temp.write_bytes(raw)
    temp.replace(path)


def prepare(output):
    started = time.monotonic()
    data = load(started + LIMITS["child_seconds"])
    out = {"status": "PREPARED: exact finite blossom family; no family census",
           **data["binding"], "scope": scope(data), "controls": controls(),
           "production_family_cases_evaluated": 0, "optimizer_calls": 0,
           "preservation": "Immutable per-core chunks, including an exact final partial prefix; owner records any hard stop.",
           "seconds": time.monotonic()-started}
    assert not output.exists()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(canonical(out) + b"\n")
    return out


def check_preparation(path, data):
    prep = json.loads(path.read_bytes())
    for k, v in data["binding"].items():
        assert prep[k] == v
    assert prep["scope"] == scope(data) and prep["controls"] == controls()
    assert prep["production_family_cases_evaluated"] == 0
    return sha(path.read_bytes())


def generate(preparation, directory, seconds):
    started = time.monotonic()
    deadline = started + seconds
    report = {"status": "INITIALIZING", "complete": False, "chunks": [],
              "source_sha256": sha(Path(__file__).read_bytes()),
              "preparation_sha256": sha(preparation.read_bytes()),
              "processed_triples": 0, "distinct_rows": 0, "live_cliques": 0,
              "dispositions": {k: 0 for k in DISPOSITIONS},
              "comparison_counts": {}, "raw_chunk_bytes": 0, "optimizer_calls": 0}
    result_path = directory / "result.json"
    atomic(result_path, report)
    try:
        data = load(deadline)
        check_preparation(preparation, data)
        row_ids, comparison_counts, raw_budget_used = {}, Counter(), 0
        report["scope"] = scope(data)
        for site, U in enumerate(data["sets"]):
            start_budget = raw_budget_used
            chunk = {"core_site": site, "triple_bound": comb(len(U), 3),
                     "processed_triples": 0, "complete_core": False,
                     "dispositions": {k: 0 for k in DISPOSITIONS},
                     "live_cliques": [], "new_rows": []}
            stop = None
            for ordinal, S in enumerate(combinations(U, 3)):
                try:
                    tick(deadline)
                    # Reserve enough for one proof record before starting the next case.
                    if raw_budget_used + 16384 > LIMITS["raw_ledger_bytes"] - LIMITS["reserved_metadata_bytes"]:
                        raise BufferError("raw ledger limit")
                    disposition, case = classification(data, S)
                    if case is not None:
                        ids, ois = case
                        terms, rhs, divisor = form(data, ois)
                        key = terms, rhs
                        if key not in row_ids:
                            r = witness(data, site, S, ids, ois, len(row_ids))
                            encoded_row_bytes = len(canonical(r)) + 2
                            assert encoded_row_bytes <= 8192
                            row_ids[key] = r["id"]
                            chunk["new_rows"].append(r)
                            raw_budget_used += encoded_row_bytes
                            for name, value in r["comparison"].items():
                                if isinstance(value, bool):
                                    comparison_counts[name] += int(value)
                        item = [ordinal, *S, row_ids[key]]
                        assert len(canonical(item)) + 2 <= 128
                        chunk["live_cliques"].append(item)
                        raw_budget_used += len(canonical(item)) + 2
                    chunk["dispositions"][disposition] += 1
                    chunk["processed_triples"] += 1
                except (TimeoutError, BufferError) as exc:
                    stop = type(exc).__name__ + ": " + str(exc)
                    break
            chunk["complete_core"] = chunk["processed_triples"] == chunk["triple_bound"]
            raw = canonical(chunk) + b"\n"
            assert len(raw) <= raw_budget_used - start_budget + 4096
            assert len(raw) <= LIMITS["raw_ledger_bytes"]
            path = directory / ("core%02d.json.gz" % site)
            assert not path.exists()
            packed = gzip.compress(raw, compresslevel=6, mtime=0)
            path.write_bytes(packed)
            report["chunks"].append({"path": path.name, "sha256": sha(packed),
                                     "raw_sha256": sha(raw), "raw_bytes": len(raw),
                                     "complete_core": chunk["complete_core"]})
            report["processed_triples"] += chunk["processed_triples"]
            report["live_cliques"] += len(chunk["live_cliques"])
            report["distinct_rows"] = len(row_ids)
            report["comparison_counts"] = dict(comparison_counts)
            report["raw_chunk_bytes"] += len(raw)
            for name in DISPOSITIONS:
                report["dispositions"][name] += chunk["dispositions"][name]
            assert report["raw_chunk_bytes"] <= LIMITS["raw_ledger_bytes"]
            report["complete"] = len(report["chunks"]) == 18 and all(c["complete_core"] for c in report["chunks"])
            report["status"] = "COMPLETE" if report["complete"] else (stop or "CHECKPOINT")
            report["seconds"] = time.monotonic()-started
            atomic(result_path, report)
            if stop:
                break
    except Exception as exc:
        report["status"] = "ERROR: " + type(exc).__name__ + ": " + str(exc)
        report["seconds"] = time.monotonic()-started
        atomic(result_path, report)
        raise
    if not report["complete"] and report["status"] == "CHECKPOINT":
        report["status"] = "INCOMPLETE"
        atomic(result_path, report)
    return report


def cold(preparation, directory, output, seconds):
    started = time.monotonic()
    deadline = started + seconds
    report = {"status": "INITIALIZING", "complete_saved_prefix_checked": False,
              "checked_chunks": 0, "checked_triples": 0, "checked_live_cliques": 0,
              "checked_rows": 0, "literal_edges_transported": 0,
              "optimizer_calls": 0, "maximum_clique_searches": 0}
    atomic(output, report)
    try:
        data = load(deadline)
        report["source_sha256"] = data["binding"]["source_sha256"]
        report["preparation_sha256"] = check_preparation(preparation, data)
        raw_result = (directory / "result.json").read_bytes()
        saved = json.loads(raw_result)
        assert saved["source_sha256"] == report["source_sha256"]
        assert saved["preparation_sha256"] == report["preparation_sha256"]
        assert saved["scope"] == scope(data)
        report["record_sha256"] = sha(raw_result)
        rows, seen_keys, edge_cache = {}, {}, {}
        total_dispositions, total_comparisons = Counter(), Counter()
        total_raw = 0

        def literal_edge_average(e):
            if e not in edge_cache:
                a, b = data["literal"]["edges"][e]
                images = Counter(data["edge_pos"][tuple(sorted((g[a], g[b])))] for g in data["actions"])
                oi = data["orbit_of"][e]
                members = data["literal"]["edge_orbits"][oi]
                assert set(images) == set(members)
                assert len(set(images.values())) == 1
                edge_cache[e] = data["columns"][oi], images
            return edge_cache[e]

        for site, info in enumerate(saved["chunks"]):
            tick(deadline)
            assert info["path"] == "core%02d.json.gz" % site
            packed = (directory / info["path"]).read_bytes()
            assert sha(packed) == info["sha256"]
            raw = gzip.decompress(packed)
            assert sha(raw) == info["raw_sha256"] and len(raw) == info["raw_bytes"]
            total_raw += len(raw)
            chunk = json.loads(raw)
            U = data["sets"][site]
            assert chunk["core_site"] == site and chunk["triple_bound"] == comb(len(U), 3)
            n = chunk["processed_triples"]
            assert 0 <= n <= chunk["triple_bound"]
            assert chunk["complete_core"] == (n == chunk["triple_bound"]) == info["complete_core"]
            assert chunk["complete_core"] or site == len(saved["chunks"])-1
            pending = {r["id"]: r for r in chunk["new_rows"]}
            assert len(pending) == len(chunk["new_rows"])
            dispositions, observed_cliques, consumed = Counter(), [], set()
            for ordinal, S in enumerate(islice(combinations(U, 3), n)):
                if ordinal % 128 == 0:
                    tick(deadline)
                ids = [data["edge_pos"].get(e) for e in combinations(S, 2)]
                if any(e is None for e in ids):
                    disposition = DISPOSITIONS[0]
                elif any(data["orbit_of"][e] in data["zero_orbits"] for e in ids):
                    disposition = DISPOSITIONS[1]
                else:
                    disposition = DISPOSITIONS[2]
                    literal_counts, count_terms = Counter(), Counter()
                    for e in ids:
                        j, images = literal_edge_average(e)
                        literal_counts.update(images)
                        count_terms[j] += next(iter(images.values()))
                    terms, rhs, divisor = normalize(count_terms)
                    key = terms, rhs
                    if key not in seen_keys:
                        row_id = len(seen_keys)
                        assert row_id in pending
                        r = pending[row_id]
                        assert r["id"] == row_id and r["terms"] == [list(t) for t in terms] and r["rhs"] == rhs
                        assert r["positive_normalization_divisor"] == divisor
                        w = r["witness"]
                        assert w["core_site"] == site and w["signatures"] == list(S)
                        assert w["literal_edges"] == ids
                        assert w["edge_orbits"] == [data["orbit_of"][e] for e in ids]
                        assert w["summed_literal_coefficients"] == [[e, literal_counts[e]] for e in sorted(literal_counts)]
                        transports = []
                        for g, move in zip(data["actions"], data["core_actions"]):
                            moved = [g[a] for a in S]
                            moved_edges = [data["edge_pos"][tuple(sorted((g[a], g[b])))] for a, b in combinations(S, 2)]
                            assert all(move[site] in data["literal"]["triples"][a] and data["literal"]["targets"][a][move[site]] == 1 for a in moved)
                            transports.append([move[site], *moved, *moved_edges])
                        assert w["all12_transports"] == transports
                        assert r["comparison"] == compare(data, key)
                        seen_keys[key] = row_id
                        rows[row_id] = r
                        consumed.add(row_id)
                        for name, value in r["comparison"].items():
                            if isinstance(value, bool):
                                total_comparisons[name] += int(value)
                    observed_cliques.append([ordinal, *S, seen_keys[key]])
                dispositions[disposition] += 1
            assert consumed == set(pending)
            assert observed_cliques == chunk["live_cliques"]
            assert {k: dispositions[k] for k in DISPOSITIONS} == chunk["dispositions"]
            total_dispositions.update(dispositions)
            report["checked_chunks"] += 1
            report["checked_triples"] += n
            report["checked_live_cliques"] += len(observed_cliques)
            report["checked_rows"] = len(rows)
            report["literal_edges_transported"] = len(edge_cache)
            report["status"] = "CHECKPOINT: complete saved chunks checked"
            report["seconds"] = time.monotonic()-started
            atomic(output, report)
        assert report["checked_triples"] == saved["processed_triples"]
        assert report["checked_live_cliques"] == saved["live_cliques"]
        assert report["checked_rows"] == saved["distinct_rows"]
        assert {k: total_dispositions[k] for k in DISPOSITIONS} == saved["dispositions"]
        assert dict(total_comparisons) == saved["comparison_counts"]
        assert total_raw == saved["raw_chunk_bytes"] <= LIMITS["raw_ledger_bytes"]
        assert saved["complete"] == (len(saved["chunks"]) == 18 and all(x["complete_core"] for x in saved["chunks"]))
        report["producer_complete"] = saved["complete"]
        report["complete_saved_prefix_checked"] = True
        report["status"] = "PASS: all saved blossom coverage and literal coefficients replayed"
    except TimeoutError as exc:
        report["status"] = "INCOMPLETE: " + str(exc)
    except Exception as exc:
        report["status"] = "ERROR: " + type(exc).__name__ + ": " + str(exc)
        report["seconds"] = time.monotonic()-started
        atomic(output, report)
        raise
    report["seconds"] = time.monotonic()-started
    atomic(output, report)
    return report


def own(kind, preparation, directory, output):
    started = time.monotonic()
    if kind == "census":
        assert not directory.exists()
        directory.mkdir(parents=True)
        owner_path = directory / "owner.json"
        checkpoint = directory / "result.json"
    else:
        assert directory.is_dir() and output is not None and not output.exists()
        owner_path = output.with_name(output.stem + "-owner.json")
        assert not owner_path.exists()
        checkpoint = output
    command = [sys.executable, str(Path(__file__).resolve()), "worker-"+kind,
               "--preparation", str(preparation.resolve()), "--directory", str(directory.resolve())]
    if output is not None:
        command += ["--output", str(output.resolve())]
    record = {"status": "RUNNING", "kind": kind, "command": command,
              "source_sha256": sha(Path(__file__).read_bytes()),
              "owner_limit_seconds": LIMITS["owner_seconds"],
              "child_limit_seconds": LIMITS["child_seconds"], "optimizer_calls": 0,
              "process_reaped": False, "checkpoint_retained_if_present": True}
    atomic(owner_path, record)
    child = None
    try:
        with owner_path.with_suffix(".log").open("wb") as stream:
            child = subprocess.Popen(command, stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
            record["pid"] = child.pid
            atomic(owner_path, record)
            try:
                remaining = LIMITS["owner_seconds"] - (time.monotonic()-started)
                child.wait(timeout=max(0.001, remaining))
                record["status"] = "CHILD_EXITED"
            except subprocess.TimeoutExpired:
                record["status"] = "HARD_LIMIT"
                try:
                    os.killpg(child.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                child.wait()
            record["exit_code"] = child.returncode
            record["process_reaped"] = True
    except Exception as exc:
        record["status"] = "OWNER_ERROR: " + type(exc).__name__ + ": " + str(exc)
        raise
    finally:
        if child is not None and child.poll() is None:
            try:
                os.killpg(child.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            child.wait()
            record["process_reaped"] = True
            record["exit_code"] = child.returncode
        record["seconds"] = time.monotonic()-started
        record["checkpoint_exists"] = checkpoint.exists()
        if checkpoint.exists():
            record["checkpoint_sha256"] = sha(checkpoint.read_bytes())
        atomic(owner_path, record)
    return record


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("mode", choices=("prepare", "census", "cold", "worker-census", "worker-cold"))
    ap.add_argument("--output", type=Path)
    ap.add_argument("--preparation", type=Path)
    ap.add_argument("--directory", type=Path)
    args = ap.parse_args()
    if args.mode == "prepare":
        assert args.output is not None
        r = prepare(args.output)
    else:
        assert args.preparation is not None and args.directory is not None
        if args.mode in ("census", "cold"):
            r = own(args.mode, args.preparation, args.directory, args.output)
        elif args.mode == "worker-census":
            assert args.directory.is_dir()
            r = generate(args.preparation, args.directory, LIMITS["child_seconds"])
        else:
            assert args.output is not None and not args.output.exists()
            r = cold(args.preparation, args.directory, args.output, LIMITS["child_seconds"])
    print(json.dumps({k: r[k] for k in ("status", "complete", "seconds", "processed_triples",
                                        "distinct_rows", "checked_chunks", "process_reaped")
                      if k in r}, indent=2), flush=True)


if __name__ == "__main__":
    main()
