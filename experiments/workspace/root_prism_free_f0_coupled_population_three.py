"""Exact coupling of the two frozen population-three signature unions.

Preparation recovers all witnesses via the common character kernel.
The separate bounded census checks literal pairs, not a count candidate.
No optimizer or large native table is constructed.
"""
import argparse
from array import array
from collections import Counter
import gzip
import hashlib
from itertools import combinations
import json
from pathlib import Path
import struct
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
BASE = "experiments/logs/root-prism-free/"
INPUTS = {
    "domains": ("f0-orbit-populations02-domains.json.gz", "4f079468530dba0746512cc4afce01666b2a63a2c8f35f66a4660a4fe3bab8ab"),
    "domain_cold": ("f0-orbit-populations02-independent-replay.json", "a8bb55cbf773ea75a8cd1d5a18b50281ecbe08f6074cea04fb2d75799138273a"),
    "moments": ("f0-second-moments-preparation02.json.gz", "404d91da35c798ba248887c22a7500957947e24b71d5197dc44432460e6d219e"),
    "characters": ("f0-character-populations01.json.gz", "139d06a3383f8fc79d677972ce052ce29966e8b3406e7d1e7d1077aea7c2cef6"),
    "joint_tables": ("f0-two-orbit-profiles01.json.gz", "6a1bc6d196358ecc618355bc64d6fe6a2b60be9fa9411afd29526c9f493995b9"),
    "joint_cold": ("f0-two-orbit-profiles01-cold.json", "afedafe2f3009849350b1682a2c329064efd9b204ab7b5a6051e5d50449fcf41"),
    "joint_source_review": ("f0-two-orbit-profiles-literature-review.json", "62348d643001fcf3f7ac1f50184e08b4bca5e84e061e6281070d4b7a33f97c24"),
}
JOINT_SOURCE = ("experiments/workspace/root_prism_free_f0_two_orbit_profiles.py",
                "8673b7590d4245efe07ae7c7da5cc18563bc7d4cb9114a76c3f0d86c30ee8f17")
LIMITS = {"preparation_seconds": 30, "census_seconds": 60, "cold_seconds": 60,
          "full_literal_pairs": 512 * 512, "optimizer_calls": 0,
          "large_native_table_builds": 0, "automatic_retries": 0}
CAPACITY_CODE = 10000


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def tick(deadline):
    if time.monotonic() >= deadline:
        raise TimeoutError("coupled population-three cooperative arithmetic deadline")


def pair_id(a, b):
    a, b = sorted((a, b))
    assert 0 <= a < b < 480
    return a * (959 - a) // 2 + b - a - 1


def read_inputs(root, deadline):
    source = (root / JOINT_SOURCE[0]).read_bytes()
    assert sha(source) == JOINT_SOURCE[1]
    result = {}
    for name, (path, digest) in INPUTS.items():
        tick(deadline)
        raw = (root / BASE / path).read_bytes()
        assert sha(raw) == digest, name
        result[name] = json.loads(gzip.decompress(raw) if path.endswith(".gz") else raw)
    for name in ("domain_cold", "joint_cold", "joint_source_review"):
        assert result[name]["status"].startswith("PASS"), name
    assert result["joint_cold"]["record_sha256"] == INPUTS["joint_tables"][1]
    return result


def native_profile(selected, table, pmap, old_to_new, signed):
    positions = {column: i for i, column in enumerate(table["count_columns"])}
    members = {a: oi for oi, orbit in table["orbit_members"] for a in orbit}
    counts = [0] * len(positions)
    for a in selected:
        counts[positions[members[a]]] += 1
    for a, b in combinations(selected, 2):
        po = pmap[pair_id(a, b)]
        counts[positions[old_to_new[5847 + po]]] += 1
    chosen = set(selected)
    signs = [sum(w for a, w in zip(p["literal_selectors"], p["signs"]) if a in chosen)
             for p in signed]
    return counts + signs


def prepare_record(context, deadline):
    domains, moments, chars, joint = [context[k] for k in ("domains", "moments", "characters", "joint_tables")]
    actions = domains["signature_actions"]
    group = chars["group"]
    kernel = [g for g in range(12) if all(c[g] == 1 for c in group["characters"])]
    assert kernel == [0, 3, 4] and group["identity"] == 0
    assert actions[0] == list(range(480))
    for g in kernel:
        assert sorted(actions[g]) == list(range(480))
        for h in kernel:
            k = group["multiplication_table"][g][h]
            assert k in kernel
            assert [actions[g][actions[h][a]] for a in range(480)] == actions[k]
    nonidentity = [g for g in kernel if g != 0]
    assert all(group["multiplication_table"][group["multiplication_table"][g][g]][g] == 0
               for g in nonidentity)
    orbits = domains["selector_orbits"]
    assert orbits == moments["selector_orbits"]
    pmap = moments["pair_to_orbit"]
    old_to_new = {old: new for new, old in enumerate(domains["new15038_to_original15589"])}
    zeros = {old - 5847 for old in domains["original_Z_zero_columns"]}
    assert len(zeros) == 389
    gram = moments["original_selector_equalities"][:171]
    assert len(gram) == 171 and all(row["family"] == "Gram" for row in gram)
    gram_lookup = {(tuple(row["support"]), row["quota"]): i for i, row in enumerate(gram)}
    gram_transports = []
    for g in kernel:
        transported = []
        for row in gram:
            key = (tuple(sorted(actions[g][a] for a in row["support"])), row["quota"])
            assert key in gram_lookup
            transported.append(gram_lookup[key])
        gram_transports.append(transported)
    quotas = [row["quota"] for row in gram]
    support_sets = [set(row["support"]) for row in gram]
    tables = []
    for ti, saved in enumerate(joint["tables"]):
        tick(deadline)
        ids = [[0, 1], [6, 7]][ti]
        assert saved["selector_orbits"] == ids
        assert saved["fixed_selected_population"] == 3
        equality = saved["inherited_count_equality"]
        assert equality["terms"] == [[i, 1] for i in ids] and equality["rhs"] == 3
        members = saved["literal_signatures"]
        assert members == sorted(a for i in ids for a in orbits[i]) and len(members) == 24
        local = {a: i for i, a in enumerate(members)}
        assert len(saved["profiles"]) == 176
        signings = [chars["signed_populations"][j] for j in saved["signed_population_columns"]]
        assert len(signings) == 6
        assert all(p["signed_population"] == j and p["selector_orbit"] in ids
                   for j, p in zip(saved["signed_population_columns"], signings))
        helper = dict(saved, orbit_members=[(i, orbits[i]) for i in ids])
        recovered, fibers = {}, []
        for profile_id, profile in enumerate(saved["profiles"]):
            representative = tuple(profile["representative_literal_subset"])
            assert len(representative) == 3 and representative == tuple(sorted(set(representative)))
            images = sorted({tuple(sorted(actions[g][a] for a in representative)) for g in kernel})
            assert len(images) == profile["literal_subset_count"] in (1, 3)
            assert images[0] == representative
            for selected in images:
                assert all(a in local for a in selected) and selected not in recovered
                assert all(pmap[pair_id(a, b)] not in zeros for a, b in combinations(selected, 2))
                assert native_profile(selected, helper, pmap, old_to_new, signings) == profile["counts_and_signed_populations"]
                contributions = [sum(a in support for a in selected) for support in support_sets]
                assert all(value <= quota for value, quota in zip(contributions, quotas))
                recovered[selected] = {"literal_signatures": list(selected), "profile_index": profile_id,
                                       "member_positions": [local[a] for a in selected],
                                       "local_mask": sum(1 << local[a] for a in selected),
                                       "Gram_contributions": contributions}
            fibers.append({"profile_index": profile_id, "literal_subsets": [list(x) for x in images]})
        assert len(recovered) == 512
        assert sum(p["literal_subset_count"] for p in saved["profiles"]) == 512
        multiplicities = Counter(len(p["literal_subsets"]) for p in fibers)
        assert multiplicities == {1: 8, 3: 168}
        selected_order = sorted(recovered)
        index = {triple: i for i, triple in enumerate(selected_order)}
        transports = []
        fixed = []
        for g in kernel:
            move = [index[tuple(sorted(actions[g][a] for a in selected))] for selected in selected_order]
            assert sorted(move) == list(range(512))
            assert all(recovered[selected_order[i]]["profile_index"] ==
                       recovered[selected_order[move[i]]]["profile_index"] for i in range(512))
            transports.append(move)
            fixed.append(sum(i == j for i, j in enumerate(move)))
        assert fixed == [512, 8, 8]
        tables.append({"selector_orbits": ids, "literal_signatures": members,
                       "count_columns": saved["count_columns"],
                       "signed_population_columns": saved["signed_population_columns"],
                       "profile_values": [p["counts_and_signed_populations"] for p in saved["profiles"]],
                       "profile_fibers": fibers,
                       "witnesses": [recovered[x] for x in selected_order],
                       "kernel_witness_actions": transports, "kernel_fixed_witness_counts": fixed,
                       "multiplicity_histogram": {str(k): v for k, v in sorted(multiplicities.items())},
                       "complete_saved_fiber_cardinalities_checked": True})
    assert len(tables) == 2 and not (set(tables[0]["literal_signatures"]) & set(tables[1]["literal_signatures"]))
    union = sorted(tables[0]["literal_signatures"] + tables[1]["literal_signatures"])
    assert len(union) == 48
    pair_action_checks = 0
    for a, b in combinations(union, 2):
        po = pmap[pair_id(a, b)]
        for g in kernel:
            assert pmap[pair_id(actions[g][a], actions[g][b])] == po
            pair_action_checks += 1
    grid = [[pmap[pair_id(a, b)] for b in tables[1]["literal_signatures"]]
            for a in tables[0]["literal_signatures"]]
    cross_ids = sorted({po for row in grid for po in row})
    expected = [po for po, (i, j) in enumerate(domains["pair_orbit_selector_blocks"])
                if i in (0, 1) and j in (6, 7)]
    assert cross_ids == expected
    assert sum(len(moments["pair_orbits"][po]) for po in cross_ids) == 576
    assert Counter(po for row in grid for po in row) == {po: len(moments["pair_orbits"][po]) for po in cross_ids}
    zero_cross = sorted(zeros & set(cross_ids))
    forbidden = [sum(1 << j for j, po in enumerate(row) if po in zeros) for row in grid]
    for left in tables[0]["witnesses"]:
        blocked = 0
        for i in left["member_positions"]:
            blocked |= forbidden[i]
        left["blocked_right_mask"] = blocked
    maxima = [[max(w["Gram_contributions"][i] for w in t["witnesses"]) for i in range(171)]
              for t in tables]
    active, redundant = [], []
    for i, quota in enumerate(quotas):
        item = {"original_Gram_row": i, "quota": quota,
                "left_maximum": maxima[0][i], "right_maximum": maxima[1][i]}
        if maxima[0][i] + maxima[1][i] > quota:
            active.append(i)
        else:
            redundant.append(item)
    live_cross = [po for po in cross_ids if po not in zeros]
    tuple_columns = []
    for table in tables:
        tuple_columns += [["count", j] for j in table["count_columns"]]
        tuple_columns += [["signed", j] for j in table["signed_population_columns"]]
    tuple_columns += [["count", old_to_new[5847 + po]] for po in live_cross]
    assert len({tuple(x) for x in tuple_columns}) == len(tuple_columns)
    fixed_products = [tables[0]["kernel_fixed_witness_counts"][g] *
                      tables[1]["kernel_fixed_witness_counts"][g] for g in range(3)]
    orbit_bound, remainder = divmod(sum(fixed_products), 3)
    assert remainder == 0 and orbit_bound == 87424
    return {
        "schema": "conway99.f0-coupled-population-three-preparation.v1",
        "status": "PREPARED_COMPLETE_LITERAL_DOMAINS_NO_CROSS_CENSUS",
        "source_sha256": sha(Path(__file__).read_bytes()),
        "inputs": {k: {"path": BASE + p, "sha256": h} for k, (p, h) in INPUTS.items()},
        "joint_source": {"path": JOINT_SOURCE[0], "sha256": JOINT_SOURCE[1]},
        "kernel_action_indices": kernel, "kernel_Gram_row_transports": gram_transports,
        "kernel_pair_orbit_checks": pair_action_checks,
        "tables": tables, "cross_pair_orbit_grid": grid,
        "cross_original_pair_orbits": cross_ids, "proved_zero_cross_pair_orbits": zero_cross,
        "retained_cross_pair_orbits": live_cross,
        "cross_pair_original_to_reduced_columns": [
            [po, old_to_new.get(5847 + po)] for po in cross_ids],
        "Gram_quotas": quotas, "active_cross_Gram_rows": active,
        "redundant_Gram_maximum_certificates": redundant,
        "tuple_columns": tuple_columns, "tuple_byte_offset": 16,
        "workload": {"left_triples": 512, "right_triples": 512, "literal_pair_cases": 262144,
                     "six_selected_signatures_per_case": 6,
                     "literal_cross_pairs_per_case": 9, "all_literal_cross_pairs_in_domain": 576,
                     "original_Gram_capacities": 171, "active_cross_Gram_rows": len(active),
                     "redundant_Gram_rows_from_independent_maxima": len(redundant),
                     "worst_cross_Gram_checks": 262144 * len(active),
                     "worst_survivor_histogram_contributions": 262144 * 9,
                     "exact_common_kernel_pair_orbits": orbit_bound,
                     "distinct_joint_tuple_upper_bound": orbit_bound,
                     "joint_tuple_width": len(tuple_columns),
                     "maximum_exact_tuple_key_payload_bytes": orbit_bound * len(tuple_columns),
                     "maximum_native_table_cells_if_later_built": orbit_bound * len(tuple_columns),
                     "maximum_u16_disposition_ledger_bytes": 524288},
        "limits": LIMITS, "production_pair_cases_scanned": 0, "optimizer_calls": 0,
        "scope": "Every six-signature restriction to the 48-signature union is one ordered pair of recovered triples. The future census imposes all extra proved-zero cross pairs and all 171 original partial Gram capacities. Common-kernel actions recover literal fibers and bound tuple storage; no graph automorphism is assumed and no native count table is built."
    }


def classify(left, right, prep):
    """Return 0, one original zero-pair orbit plus 1, or 10000 + Gram-row ID."""
    if right["local_mask"] & left["blocked_right_mask"]:
        zeros = prep["_zero_cross_set"]
        grid = prep["cross_pair_orbit_grid"]
        for i in left["member_positions"]:
            for j in right["member_positions"]:
                po = grid[i][j]
                if po in zeros:
                    return 1 + po
        raise AssertionError("blocked bit lacks a literal zero-pair witness")
    for row in prep["active_cross_Gram_rows"]:
        if left["Gram_contributions"][row] + right["Gram_contributions"][row] > prep["Gram_quotas"][row]:
            return CAPACITY_CODE + row
    return 0


def primitive_controls():
    grid = [[(2 * i + j) % 4 for j in range(3)] for i in range(3)]
    supports = [{0, 1, 3}, {1, 2, 4, 5}, {0, 2, 3, 5}]
    cases, zero_failures, capacity_failures, accepted = 0, 0, 0, 0
    histogram_checks = 0
    for lm in range(8):
        ls = [i for i in range(3) if lm >> i & 1]
        for rm in range(8):
            rs = [i for i in range(3) if rm >> i & 1]
            selected = set(ls + [3 + j for j in rs])
            fast = Counter(grid[i][j] for i in ls for j in rs)
            direct = Counter()
            for a, b in combinations(sorted(selected), 2):
                if a < 3 <= b:
                    direct[(2 * a + b - 3) % 4] += 1
            assert fast == direct and sum(fast.values()) == len(ls) * len(rs)
            histogram_checks += 1
            lc = [sum(i in support for i in ls) for support in supports]
            rc = [sum(3 + j in support for j in rs) for support in supports]
            for zp in range(16):
                zeros = {p for p in range(4) if zp >> p & 1}
                blocked = sum(1 << j for j in range(3) if any(grid[i][j] in zeros for i in ls))
                for quota in range(4):
                    if max(lc + rc) > quota:
                        continue
                    left = {"local_mask": lm, "member_positions": ls,
                            "blocked_right_mask": blocked, "Gram_contributions": lc}
                    right = {"local_mask": rm, "member_positions": rs, "Gram_contributions": rc}
                    prep = {"_zero_cross_set": zeros, "cross_pair_orbit_grid": grid,
                            "active_cross_Gram_rows": [0, 1, 2], "Gram_quotas": [quota] * 3}
                    code = classify(left, right, prep)
                    bad_pair = next((grid[i][j] for i in ls for j in rs if grid[i][j] in zeros), None)
                    bad_row = next((i for i, support in enumerate(supports)
                                    if len(selected & support) > quota), None)
                    expected = (1 + bad_pair if bad_pair is not None else
                                CAPACITY_CODE + bad_row if bad_row is not None else 0)
                    assert code == expected
                    cases += 1
                    zero_failures += 0 < code < CAPACITY_CODE
                    capacity_failures += code >= CAPACITY_CODE
                    accepted += code == 0
    assert zero_failures and capacity_failures and accepted
    for value in range(-3, 10):
        assert bytes([value + 16])[0] - 16 == value
    return {"synthetic_partition_cases": cases, "zero_pair_rejections": zero_failures,
            "mixed_capacity_rejections": capacity_failures, "accepted": accepted,
            "independent_cross_histogram_checks": histogram_checks,
            "repeated_pair_orbit_multiplicities_retained": True,
            "tuple_byte_encoding_exact": True, "production_pair_cases_scanned": 0,
            "optimizer_calls": 0}


def encode_ledger(codes):
    result = array("H", codes)
    assert result.itemsize == 2
    if sys.byteorder != "little":
        result.byteswap()
    return result.tobytes()


def cross_census(prep, deadline, maximum_prefix=262144):
    assert 0 <= maximum_prefix <= 262144
    data = dict(prep, _zero_cross_set=set(prep["proved_zero_cross_pair_orbits"]))
    lefts, rights = [t["witnesses"] for t in prep["tables"]]
    profiles = [t["profile_values"] for t in prep["tables"]]
    grid = prep["cross_pair_orbit_grid"]
    cross_ids = prep["cross_original_pair_orbits"]
    live_ids = prep["retained_cross_pair_orbits"]
    zero_ids = set(prep["proved_zero_cross_pair_orbits"])
    codes, dispositions = [], Counter()
    values = {po: 0 for po in cross_ids}
    witnesses = {po: {} for po in cross_ids}
    tuples = Counter()
    survivors, prefix, stop = 0, 0, None
    try:
        for i, left in enumerate(lefts):
            for j, right in enumerate(rights):
                if prefix == maximum_prefix:
                    break
                if prefix % 64 == 0:
                    tick(deadline)
                assert prefix == 512 * i + j
                code = classify(left, right, data)
                if code == 0:
                    hist = Counter(grid[a][b] for a in left["member_positions"]
                                   for b in right["member_positions"])
                    assert sum(hist.values()) == 9 and all(hist[po] == 0 for po in zero_ids)
                    for po in cross_ids:
                        value = hist[po]
                        assert 0 <= value <= 9
                        values[po] |= 1 << value
                        witnesses[po].setdefault(str(value), prefix)
                    key_values = (profiles[0][left["profile_index"]] +
                                  profiles[1][right["profile_index"]] +
                                  [hist[po] for po in live_ids])
                    assert len(key_values) == len(prep["tuple_columns"])
                    assert all(type(v) is int and -3 <= v <= 9 for v in key_values)
                    tuples[bytes(v + 16 for v in key_values)] += 1
                    survivors += 1
                codes.append(code)
                dispositions[code] += 1
                prefix += 1
            if prefix == maximum_prefix:
                break
    except TimeoutError as error:
        stop = str(error)
    assert len(codes) == prefix and sum(dispositions.values()) == prefix
    assert sum(tuples.values()) == survivors and dispositions[0] == survivors
    assert len(tuples) <= prep["workload"]["distinct_joint_tuple_upper_bound"]
    complete = prefix == 262144
    domain_rows = []
    column_map = dict(prep["cross_pair_original_to_reduced_columns"])
    for po in cross_ids:
        observed = [v for v in range(10) if values[po] >> v & 1]
        domain_rows.append({"original_pair_orbit": po, "original15589_column": 5847 + po,
                            "reduced15038_column": column_map[po],
                            "proved_zero_before_census": po in zero_ids,
                            "observed_values": observed,
                            "minimum": min(observed) if observed else None,
                            "maximum": max(observed) if observed else None,
                            "first_literal_pair_witness_by_value": witnesses[po],
                            "complete_domain_certified": complete})
    new_zeros = [r["original_pair_orbit"] for r in domain_rows
                 if complete and survivors > 0 and not r["proved_zero_before_census"]
                 and r["observed_values"] == [0]]
    digest = hashlib.sha256()
    for key, multiplicity in sorted(tuples.items()):
        digest.update(key)
        digest.update(struct.pack("<I", multiplicity))
    ledger = encode_ledger(codes)
    return {
        "full_literal_pair_scope": 262144, "covered_literal_pair_prefix": prefix,
        "complete": complete, "stop_reason": stop,
        "surviving_literal_pairs": survivors,
        "excluded_by_proved_zero_cross_pair": sum(n for c, n in dispositions.items() if 0 < c < CAPACITY_CODE),
        "excluded_by_original_Gram_capacity": sum(n for c, n in dispositions.items() if c >= CAPACITY_CODE),
        "disposition_code_histogram": {str(c): n for c, n in sorted(dispositions.items())},
        "disposition_encoding": "little-endian uint16; 0=survivor;1+original_pair_orbit=proved zero;10000+original_Gram_row=capacity violation",
        "disposition_ledger_sha256": sha(ledger),
        "cross_count_domains": domain_rows, "new_forced_zero_original_pair_orbits": new_zeros,
        "all_cross_counts_sum_to_nine_on_each_survivor": True,
        "distinct_joint_tuples_in_covered_prefix": len(tuples),
        "joint_tuple_multiplicity_histogram": {str(k): v for k, v in sorted(Counter(tuples.values()).items())},
        "joint_tuple_width": len(prep["tuple_columns"]),
        "exact_joint_tuple_key_payload_bytes": len(tuples) * len(prep["tuple_columns"]),
        "hypothetical_native_table_cells": len(tuples) * len(prep["tuple_columns"]),
        "joint_tuple_stream_sha256": digest.hexdigest(),
        "large_native_table_built": False, "optimizer_calls": 0,
        "global_incidence_claimed": False, "F0_exclusion_claimed": False,
        "scope": "Exact finite six-signature restrictions only. Observed count ranges and forced zeros are complete-scope necessities only when complete=true. A nonempty survivor set is not a global incidence witness."
    }, ledger


def write(path, value):
    raw = canonical(value) + b"\n"
    if str(path).endswith(".gz"):
        raw = gzip.compress(raw, mtime=0)
    with path.open("xb") as handle:
        handle.write(raw)
    return sha(raw)


def checked_preparation(path, expected_sha):
    raw = path.read_bytes()
    assert sha(raw) == expected_sha
    prep = json.loads(gzip.decompress(raw) if str(path).endswith(".gz") else raw)
    assert prep["source_sha256"] == sha(Path(__file__).read_bytes())
    assert prep["status"] == "PREPARED_COMPLETE_LITERAL_DOMAINS_NO_CROSS_CENSUS"
    assert prep["limits"] == LIMITS
    assert prep["inputs"] == {k: {"path": BASE + p, "sha256": h} for k, (p, h) in INPUTS.items()}
    assert len(prep["tables"]) == 2 and all(len(t["witnesses"]) == 512 for t in prep["tables"])
    return prep


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "scan", "replay"))
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--preparation", type=Path)
    parser.add_argument("--preparation-sha256")
    parser.add_argument("--record", type=Path)
    parser.add_argument("--ledger", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    started = time.monotonic()
    if args.mode == "prepare":
        deadline = started + LIMITS["preparation_seconds"]
        result = prepare_record(read_inputs(args.root, deadline), deadline)
        result["primitive_controls"] = primitive_controls()
        tick(deadline)
        digest = write(args.output, result)
        print(json.dumps({"status": result["status"], "sha256": digest,
                          "workload": result["workload"],
                          "production_pair_cases_scanned": 0,
                          "seconds": time.monotonic() - started}, indent=2))
        return
    assert args.preparation is not None and args.preparation_sha256 is not None
    limit = LIMITS["census_seconds"] if args.mode == "scan" else LIMITS["cold_seconds"]
    deadline = started + limit
    prep = checked_preparation(args.preparation, args.preparation_sha256)
    if args.mode == "scan":
        assert args.ledger is not None and not args.ledger.exists() and not args.output.exists()
        census, ledger = cross_census(prep, deadline)
        compressed = gzip.compress(ledger, mtime=0)
        with args.ledger.open("xb") as handle:
            handle.write(compressed)
        result = {"status": "COMPLETE_EXACT_COUPLED_UNION_CENSUS" if census["complete"] else "PARTIAL_COUPLED_UNION_CENSUS",
                  "source_sha256": sha(Path(__file__).read_bytes()),
                  "preparation_sha256": args.preparation_sha256,
                  "ledger_path": str(args.ledger), "ledger_gzip_sha256": sha(compressed),
                  "census": census, "limits": LIMITS, "seconds": time.monotonic() - started}
    else:
        assert args.record is not None and args.ledger is not None
        raw = args.record.read_bytes()
        old = json.loads(gzip.decompress(raw) if str(args.record).endswith(".gz") else raw)
        assert old["source_sha256"] == sha(Path(__file__).read_bytes())
        assert old["preparation_sha256"] == args.preparation_sha256 and old["limits"] == LIMITS
        compressed = args.ledger.read_bytes()
        assert sha(compressed) == old["ledger_gzip_sha256"]
        target_prefix = old["census"]["covered_literal_pair_prefix"]
        census, ledger = cross_census(prep, deadline, target_prefix)
        if census["covered_literal_pair_prefix"] != target_prefix:
            result = {"status": "PARTIAL_COLD_REPLAY: no full census acceptance",
                      "source_sha256": sha(Path(__file__).read_bytes()),
                      "record_sha256": sha(raw), "required_prefix": target_prefix,
                      "checked_prefix": census["covered_literal_pair_prefix"],
                      "seconds": time.monotonic() - started}
        else:
            # A saved partial prefix can stop because of its original deadline;
            # its completed cases and all associated arithmetic must still match.
            census["stop_reason"] = old["census"]["stop_reason"]
            assert ledger == gzip.decompress(compressed)
            assert census == old["census"]
            result = {"status": "PASS: complete saved literal prefix, dispositions and exact tuple/count summaries replayed",
                      "source_sha256": sha(Path(__file__).read_bytes()),
                      "record_sha256": sha(raw), "preparation_sha256": args.preparation_sha256,
                      "checked_literal_pairs": target_prefix,
                      "complete_product_scope": census["complete"],
                      "surviving_literal_pairs": census["surviving_literal_pairs"],
                      "distinct_joint_tuples": census["distinct_joint_tuples_in_covered_prefix"],
                      "optimizer_calls": 0, "seconds": time.monotonic() - started}
    digest = write(args.output, result)
    print(json.dumps({"status": result["status"], "sha256": digest,
                      "seconds": time.monotonic() - started,
                      "census": {k: v for k, v in result.get("census", {}).items()
                                 if k not in ("cross_count_domains", "disposition_code_histogram")}},
                     indent=2))


if __name__ == "__main__":
    main()
