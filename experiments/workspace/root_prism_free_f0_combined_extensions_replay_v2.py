"""Independent protobuf-only replay of the combined exact F0 extensions.

Both CLI modes are workers. The CI driver owns their separate process groups.
This source never imports the producer, CpModel, CpSolver or a native helper.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import importlib.metadata
import json
from pathlib import Path
import resource
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
OLD_VARIABLES, OLD_ROWS = 68934, 257594
FOUR_FIRST, FOUR_COUNT = 227270, 23010
STAR_FIRST, STAR_COUNT = 68934, 2448
TRIANGLE_FIRST, TRIANGLE_COUNT = 71382, 5364
FOREST_FIRST, FOREST_COUNT = 76746, 3984
STAR_ROW, TRIANGLE_ROW, FOREST_ROW = 257594, 260042, 281582
FINAL_VARIABLES, FINAL_ROWS = 80730, 297470
EDGE_FIRST, MIXED_FIRST = 540, 154430
PARENT_RAW_SHA = "4a9b24ab1a0a1758ffedab226a9c45fe7765fafc40e76e23a039c9ccd098aee2"
PARENT_RAW_BYTES = 38374405
EDGE_SHA = "411052a41a473bb7199fe277516fb60c54018dec120309622a499229579791bb"
FOUR_KEYS_SHA = "2adfcc619820604a3f49463bd0fd8109113ab7ce13bceadcc49554533b09dd1c"
RETAINED_SHA = "b53cff225273f025bc9b6d8e2cd6a654291993df8da4d0345a0dc2312b0dafac"
SCHEMA_SHA = "266b68151ffd6c9f5db22553442abd777031663d39e1cea649a8737f811d2eff"
MAIN_PASS = "PASS_INDEPENDENT_COMPLETE_COMBINED_EXTENSIONS_NATIVE_MODEL"
CONTROLS_PASS = "PASS_COMBINED_EXTENSIONS_INDEPENDENT_REPLAY_CONTROLS"


def need(condition, message):
    if not condition:
        raise ValueError(message)


def integer(value, lower, upper):
    need(type(value) is int and lower <= value <= upper, "exact integer range")
    return value


def compact(value):
    return json.dumps(value, ensure_ascii=True, separators=(",", ":"), allow_nan=False).encode("ascii")


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def value_sha(value):
    return digest(compact(value))


def file_ref(path):
    path = Path(path).resolve()
    raw = path.read_bytes()
    return {"path": str(path.relative_to(ROOT)), "sha256": digest(raw), "bytes": len(raw)}


def same_ref(a, b, message):
    need(a["path"] == b["path"] and a["sha256"] == b["sha256"], message)
    if "bytes" in a and "bytes" in b:
        need(a["bytes"] == b["bytes"], message + " byte count")


def bound_path(ref):
    relative = Path(ref["path"])
    need(not relative.is_absolute() and ".." not in relative.parts, "repository-relative input")
    path = (ROOT / relative).resolve()
    need(path.is_relative_to(ROOT), "input remains in repository")
    return path


def read_bound(ref):
    raw = bound_path(ref).read_bytes()
    need(digest(raw) == ref["sha256"], "bound SHA256: " + ref["path"])
    if "bytes" in ref:
        need(len(raw) == ref["bytes"], "bound byte count: " + ref["path"])
    if "git_blob" in ref:
        git = hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()
        need(git == ref["git_blob"], "bound Git blob: " + ref["path"])
    return raw


def decoded_bound(ref):
    raw = read_bound(ref)
    if ref["path"].endswith(".gz"):
        raw = gzip.decompress(raw)
        if "raw_sha256" in ref:
            need(digest(raw) == ref["raw_sha256"], "bound decompressed SHA256")
        if "raw_bytes" in ref:
            need(len(raw) == ref["raw_bytes"], "bound decompressed bytes")
    return raw


class Clock:
    def __init__(self, seconds):
        self.started = time.monotonic()
        self.seconds = seconds

    def elapsed(self):
        return time.monotonic() - self.started

    def check(self):
        need(self.elapsed() < self.seconds, "independent worker phase deadline")


def configuration(path, expected_sha, clock):
    raw = Path(path).read_bytes()
    need(digest(raw) == expected_sha, "exact CLI configuration SHA")
    cfg = json.loads(raw)
    need(cfg["schema"] == "conway99.f0.combined-extensions-native-configuration.v1", "configuration schema")
    same_ref(cfg["sources"]["checker"], file_ref(__file__), "current independent checker source")
    clock.check()
    return cfg, {"path": str(Path(path).resolve().relative_to(ROOT)),
                 "sha256": expected_sha, "bytes": len(raw)}


def protobuf_decoder(cfg):
    from ortools.sat import cp_model_pb2 as pb
    need(importlib.metadata.version("ortools") == "9.15.6755", "pinned ortools distribution")
    need(importlib.metadata.version("protobuf") == "6.33.6", "pinned protobuf distribution")
    need(digest(pb.DESCRIPTOR.serialized_pb) == SCHEMA_SHA, "pinned protobuf model schema")
    need(cfg["runtime"]["model_schema_sha256"] == SCHEMA_SHA, "configuration schema pin")
    return pb


def parse_model(pb, raw):
    model = pb.CpModelProto()
    consumed = model.ParseFromString(raw)
    need(consumed == len(raw) and model.SerializeToString() == raw, "complete canonical protobuf bytes")
    return model


def row_key(lower, upper, terms):
    integer(lower, -(1 << 63), (1 << 63) - 1)
    integer(upper, lower, (1 << 63) - 1)
    terms = sorted([[integer(v, 0, FINAL_VARIABLES - 1),
                     integer(c, -(1 << 63), (1 << 63) - 1)] for v, c in terms])
    need(all(c != 0 for _, c in terms), "nonzero row coefficient")
    need(len({v for v, _ in terms}) == len(terms), "one term per row variable")
    return [lower, upper, terms]


def constraint(pb, key):
    lower, upper, terms = key
    out = pb.ConstraintProto()
    out.linear.vars.extend(v for v, _ in terms)
    out.linear.coeffs.extend(c for _, c in terms)
    out.linear.domain.extend([lower, upper])
    return out


def check_row(pb, actual, key, label):
    need(actual.SerializeToString() == constraint(pb, key).SerializeToString(),
         "complete native row: " + label)


def check_variable(pb, actual, name):
    expected = pb.IntegerVariableProto(name=name)
    expected.domain.extend([0, 1])
    need(actual.SerializeToString() == expected.SerializeToString(), "complete Boolean variable " + name)


def row_digest(keys):
    h = hashlib.sha256()
    for key in keys:
        h.update(compact(key) + b"\n")
    return h.hexdigest()


def compare_fields(actual, expected, label):
    for field, value in expected.items():
        need(actual[field] == value, label + "." + field)


def check_original_namespace(parent):
    need(len(parent.variables) == OLD_VARIABLES and len(parent.constraints) == OLD_ROWS,
         "accepted parent dimensions")
    need({f.name for f, _ in parent.ListFields()} <= {"name", "variables", "constraints"},
         "no unaccepted parent top-level fields")
    need(all(list(parent.variables[i].domain) == [0, 1] for i in range(480)),
         "original selector domains")
    need(all(list(parent.variables[i].domain) == [0, 1] for i in range(EDGE_FIRST, OLD_VARIABLES)),
         "original eligible-edge domains")

def literal_graph(domain, parent, pb, clock):
    need(domain["status"] == "complete component-zero exterior-row domain preparation", "domain acceptance")
    need(domain["hypothetical_graph_symmetry_assumed"] is False, "literal signature namespace")
    full = domain["component_core_rows"]
    need(len(full) == 21, "complete fixed core")
    for a, mask in enumerate(full):
        integer(mask, 0, (1 << 21) - 1)
        need(not (mask >> a & 1), "loop-free fixed core")
        for b in range(21):
            need((mask >> b & 1) == (full[b] >> a & 1), "symmetric fixed core")
    core = [(mask >> 3) & ((1 << 18) - 1) for mask in full[3:]]
    need(core == domain["component_adjacency_rows"], "complete 18-site adjacency")
    gram = [[12 * int(i == j) + 2 - (full[i + 3] & full[j + 3]).bit_count()
             - (full[i + 3] >> (j + 3) & 1) for j in range(18)] for i in range(18)]
    signatures = []
    for i in range(18):
        for j in range(i + 1, 18):
            for k in range(j + 1, 18):
                sites = [i, j, k]
                if any(sum(v // 6 == f for v in sites) > 2 for f in range(3)):
                    continue
                if any(gram[a][b] == 0 for a, b in ((i, j), (i, k), (j, k))):
                    continue
                if any(sum(int(a == b or (core[a] >> b & 1)) for b in sites) > 2 for a in range(18)):
                    continue
                signatures.append(sites)
    need(signatures == domain["signature_domain"] and len(signatures) == 480, "all original signatures")
    sets = [set(s) for s in signatures]
    core_sets = [{j for j in range(18) if core[i] >> j & 1} for i in range(18)]
    quotas = [[2 - int(i in s) - len(core_sets[i] & s) for i in range(18)] for s in sets]
    need(quotas == domain["row_targets"] and all(sum(q) == 24 for q in quotas), "all original quotas")
    need(all(v in (0, 1, 2) for q in quotas for v in q), "mixed quota range")
    pairs = []
    for b in range(479, 0, -1):
        clock.check()
        for a in range(b):
            if len(sets[a] & sets[b]) <= 1 and all(quotas[a][i] > 0 for i in sets[b]) and all(quotas[b][i] > 0 for i in sets[a]):
                pairs.append([a, b])
    pairs.sort()
    need(len(pairs) == 68394 and value_sha(pairs) == EDGE_SHA, "complete original eligible-edge order")
    index = {}
    neighbors = [[] for _ in range(480)]
    incident = [[] for _ in range(480)]
    for e, (a, b) in enumerate(pairs):
        index[a, b] = index[b, a] = e
        neighbors[a].append(b)
        neighbors[b].append(a)
        incident[a].append((b, e))
        incident[b].append((a, e))
        check_variable(pb, parent.variables[EDGE_FIRST + e], "shared_edge_%03d_%03d" % (a, b))
    need(neighbors == domain["possible_neighbor_signature_ids"], "all original neighbor rows")
    return {"h": signatures, "sets": sets, "q": quotas, "core": core, "full_core": full,
            "gram": gram, "edges": pairs, "index": index, "neighbors": neighbors, "incident": incident}


def literal_zeros(data, graph, parent, pb):
    overlay = data["overlay"]
    need(overlay["status"] == "COMPLETE_LITERAL_PRISM_ZEROS_AND_CORE_PAIR_CLIQUES", "literal zero authority")
    need(overlay["complete_edge_order_sha256"] == EDGE_SHA and len(overlay["zero_rows"]) == 1884, "literal zero inventory")
    old, spectral, full = {}, {}, {}
    for k, record in enumerate(overlay["zero_rows"]):
        e = integer(record["edge_id"], 0, 68393)
        need(e not in old and record["variable_index"] == EDGE_FIRST + e, "unique literal zero")
        need(record["native_row_index"] == 163070 + k, "literal zero native index")
        need(record["witness"]["pair"] == graph["edges"][e], "literal zero endpoints")
        check_row(pb, parent.constraints[163070 + k], row_key(0, 0, [[EDGE_FIRST + e, 1]]), "old edge zero")
        old[e] = k
        full[e] = {"edge_id": e, "endpoints": graph["edges"][e], "literal_origin": k,
                   "literal_native_row": 163070 + k, "spectral_origin": None}
    records = data["spectral_cold"]["mathematical"]["edge_zero_rows"]
    need(len(records) == 132, "complete spectral zero family")
    added = []
    for k, record in enumerate(records):
        need(len(record) == 4, "spectral zero record")
        a, b, e, was_old = record
        integer(e, 0, 68393)
        need(type(was_old) is bool and e not in spectral, "unique exact spectral disposition")
        need(graph["edges"][e] == [a, b] and was_old == (e in old), "spectral zero literal identity")
        spectral[e] = k
        if e not in full:
            full[e] = {"edge_id": e, "endpoints": [a, b], "literal_origin": None,
                       "literal_native_row": None, "spectral_origin": None}
            added.append(e)
        full[e]["spectral_origin"] = k
    need(len(added) == 72 and len(full) == 1956, "complete accepted zero union")
    for k, e in enumerate(added):
        check_row(pb, parent.constraints[257270 + k], row_key(0, 0, [[EDGE_FIRST + e, 1]]),
                  "additional spectral zero")
    return {"old": old, "spectral": spectral, "full": full,
            "forest_ledger": [full[e] for e in sorted(full)]}


def reconstruct_stars(data, graph, zeros, parent, pb, clock):
    four, report = data["four_inventory"], data["star_inventory"]
    rows, retained = four["row_keys"], four["retained_row_ids"]
    need(len(rows) == 72468 and value_sha(rows) == FOUR_KEYS_SHA, "complete accepted four keys")
    need(len(retained) == FOUR_COUNT and retained == sorted(set(retained)) and value_sha(retained) == RETAINED_SHA,
         "complete retained four IDs")
    need(retained == data["four_certificate_replay"]["retained_row_ids"], "accepted retained certificate list")
    need(len(four["cases"]) == 73404 and len(four["row_certificate_masks"]) == 72468, "complete four origins")
    origins = {rid: [] for rid in retained}
    for case_id, record in enumerate(four["cases"]):
        need(len(record) == 7 and all(type(v) is int for v in record), "exact four origin shape")
        if record[3] in origins:
            origins[record[3]].append((case_id, record))
    pairs = {tuple(p) for p in four["core_pairs"]}
    need(len(pairs) == 48, "all accepted core pairs")
    channels, witnesses, old_keys, replacement_keys = {}, {}, [], []
    pending_replacements, pending_links = [], []
    star_cache = {}

    def star(center, i, j):
        cache_key = (center, min(i, j), max(i, j))
        if cache_key not in star_cache:
            star_cache[cache_key] = tuple(sorted(e for neighbor, e in graph["incident"][center]
                                               if i in graph["sets"][neighbor] and j in graph["sets"][neighbor]
                                               and e not in zeros["old"]))
        return star_cache[cache_key]

    def mixed(center, site):
        mid = 18 * center + site
        if mid not in witnesses:
            need(graph["q"][center][site] == 1, "channel has an actual quota-one witness")
            support = sorted(e for neighbor, e in graph["incident"][center] if site in graph["sets"][neighbor])
            key = row_key(0, 0, [[center, -1]] + [[EDGE_FIRST + e, 1] for e in support])
            check_row(pb, parent.constraints[MIXED_FIRST + mid], key, "channel mixed support")
            witnesses[mid] = {"mixed_index": mid, "native_row_index": MIXED_FIRST + mid,
                              "center": center, "site": site, "positive_original_edge_ids": support,
                              "selector_coefficient": -1}
        return witnesses[mid]

    for rank, rid in enumerate(retained):
        if rank % 128 == 0:
            clock.check()
        b, c, positive = rows[rid]
        integer(b, 0, 479)
        integer(c, b + 1, 479)
        need(positive == sorted(set(positive)), "coefficient-one positive edge order")
        central = graph["index"].get((b, c))
        need(central is not None and central in positive and central not in zeros["old"], "retained central edge")
        left, right = [], []
        for e in positive:
            integer(e, 0, 68393)
            if e == central:
                continue
            a, d = graph["edges"][e]
            if b in (a, d):
                need(c not in (a, d), "left edge is not central")
                left.append(e)
            else:
                need(c in (a, d), "every other edge lies in right star")
                right.append(e)
        need(left and right and origins[rid], "two nonempty stars and complete origins")
        left_key, right_key = (b, tuple(left)), (c, tuple(right))
        for key in (left_key, right_key):
            channels.setdefault(key, {"witnesses": set(), "origins": 0})
        for case_id, record in origins[rid]:
            e, i, j, target, qbj, qci, mask = record
            need([e, target, qbj, qci, mask] == [central, rid, 2, 2, 0], "retained exact original premise")
            need(four["row_certificate_masks"][rid] == 0, "retained zero redundancy mask")
            integer(i, 0, 17)
            integer(j, 0, 17)
            need((min(i, j), max(i, j)) in pairs and i != j, "accepted core-pair origin")
            full = graph["full_core"]
            need(not (full[i + 3] >> (j + 3) & 1) and (full[i + 3] & full[j + 3]).bit_count() == 0,
                 "original full-core pair premises")
            need(i in graph["sets"][b] and j not in graph["sets"][b] and j in graph["sets"][c] and i not in graph["sets"][c],
                 "oriented signatures")
            need(graph["q"][b][i] == graph["q"][c][j] == 1 and graph["q"][b][j] == graph["q"][c][i] == 2,
                 "complete own and cross quotas")
            need(tuple(left) == star(b, i, j) and tuple(right) == star(c, i, j), "complete original literal stars")
            for side, key, center, site in ((0, left_key, b, i), (1, right_key, c, j)):
                witness = mixed(center, site)
                need(set(key[1]) <= set(witness["positive_original_edge_ids"]), "coefficient-one mixed inclusion")
                channels[key]["witnesses"].add(witness["mixed_index"])
                channels[key]["origins"] += 1
                pending_links.append([case_id, side, key, witness["mixed_index"]])
        need(sorted([central] + left + right) == positive, "complete exact original row support")
        key = row_key(-2, 0, [[b, -1], [c, -1]] + [[EDGE_FIRST + e, 1] for e in positive])
        check_row(pb, parent.constraints[FOUR_FIRST + rank], key, "original retained four")
        old_keys.append(key)
        pending_replacements.append([rid, central, left_key, right_key])
    channel_keys = sorted(channels)
    ids = {key: k for k, key in enumerate(channel_keys)}
    rebuilt = [[center, list(support), sorted(channels[center, support]["witnesses"]),
                channels[center, support]["origins"]] for center, support in channel_keys]
    links = [[case_id, side, ids[key], mid] for case_id, side, key, mid in pending_links]
    replacements = [[rid, central, ids[left], ids[right]] for rid, central, left, right in pending_replacements]
    witness_records = [witnesses[mid] for mid in sorted(witnesses)]
    derived = report["derived"]
    need(rebuilt == derived["channels"] and links == derived["origin_links"], "all exact channels and origin links")
    need(replacements == derived["replacements"] and witness_records == derived["mixed_witnesses"],
         "every channel replacement and complete mixed receipt")
    need(len(rebuilt) == STAR_COUNT and len(links) == 46020 and len(witness_records) == 1002, "star inventory counts")
    need(sum(len(key[2]) for key in old_keys) == 401874, "complete old four term count")
    definitions = [row_key(0, 0, [[center, -1], [STAR_FIRST + k, 1]] +
                           [[EDGE_FIRST + e, 1] for e in support])
                   for k, (center, support) in enumerate(channel_keys)]
    for _, central, left, right in replacements:
        need(left != right, "different endpoint channels")
        replacement_keys.append(row_key(-2, 0, [[EDGE_FIRST + central, 1],
                                               [STAR_FIRST + left, -1], [STAR_FIRST + right, -1]]))
    need(sum(len(key[2]) for key in definitions) == 22380, "complete star definition terms")
    return {"variables": [(STAR_FIRST + k, "four_star_channel_%04d" % k) for k in range(STAR_COUNT)],
            "replacement_keys": replacement_keys, "definition_keys": definitions,
            "old_keys": old_keys, "channel_key_sha256": value_sha([[a, list(s)] for a, s in channel_keys]),
            "origin_links_sha256": value_sha(links), "mixed_receipts": len(witnesses)}

def reconstruct_triangles(data, graph, zeros, parent, pb, clock):
    forward, ledger = data["triangle_forward"], data["triangle_support_ledger"]
    report, literal, root = data["triangle_inventory"], data["triangle_literal_replay"], data["triangle_literal_root_acceptance"]
    family = next(f for f in forward["families"] if f["family"] == "plus")
    negative = family["nonpositive_determinant_records_with_nonnegative_proper_minors"]
    need(len(negative) == 10830 and value_sha(negative) == "60dd838a427e23b5d3c773e7eb8ecb9852e77a88bd0d9e1ac647e51be7965ff8",
         "complete accepted triangle cover list")
    covers, installed = {}, 0
    for k, record in enumerate(negative):
        need(len(record) == 7, "accepted negative triangle shape")
        a, b, c = record[:3]
        need(0 <= a < b < c < 480 and (a, b, c) not in covers, "distinct ordered negative triple")
        need(not (graph["sets"][a] & graph["sets"][b] or graph["sets"][a] & graph["sets"][c]
                  or graph["sets"][b] & graph["sets"][c]), "cover disjoint signatures")
        edge_ids = [graph["index"][a, b], graph["index"][a, c], graph["index"][b, c]]
        covers[a, b, c] = k
        if not set(edge_ids) & zeros["old"].keys():
            check_row(pb, parent.constraints[250280 + installed],
                      row_key(0, 2, [[EDGE_FIRST + e, 1] for e in edge_ids]), "original triangle cover")
            installed += 1
    need(installed == 6990, "all original explicitly installed triangle covers")
    initial = []
    for e in sorted(zeros["full"]):
        origins = []
        if e in zeros["old"]:
            k = zeros["old"][e]
            origins.append({"kind": "literal_overlay", "record_index": k, "native_row_index": 163070 + k})
        if e in zeros["spectral"]:
            origins.append({"kind": "spectral_zero", "record_index": zeros["spectral"][e]})
        initial.append({"edge_id": e, "endpoints": graph["edges"][e], "origins": origins})
    need(initial == ledger["initial_zero_authorities"], "every triangle initial zero authority")
    initial_index = {row["edge_id"]: k for k, row in enumerate(initial)}
    targets = []
    for k, record in enumerate(data["spectral_cold"]["mathematical"]["edge_present_requires_one_common_exterior_neighbor"]):
        need(len(record) == 4, "must-triangle spectral premise")
        a, b, e, was_old = record
        need(graph["edges"][e] == [a, b] and type(was_old) is bool and was_old == (e in zeros["old"]),
             "must-triangle exact endpoints and old-zero disposition")
        need(not graph["sets"][a] & graph["sets"][b], "must-triangle disjoint anchors")
        targets.append({"edge_id": e, "premise_index": k, "endpoints": [a, b]})
    targets.sort(key=lambda t: t["edge_id"])
    need(len(targets) == len({t["edge_id"] for t in targets}) == 132 and targets == ledger["targets"],
         "complete spectral target family")
    already = [{"edge_id": t["edge_id"], "premise_index": t["premise_index"],
                "authority": {"kind": "initial", "index": initial_index[t["edge_id"]]}}
               for t in targets if t["edge_id"] in initial_index]
    live_targets = [t for t in targets if t["edge_id"] not in initial_index]
    need(len(already) == 48 and len(live_targets) == 84 and already == ledger["initially_zero_targets"],
         "complete already-zero/live partition")
    need(ledger["certificates"] == ledger["row_keys"] == [] and ledger["new_edge_zero_count"] == 0,
         "no unbound derived zero")
    need(ledger["final_zero_edge_ids"] == sorted(zeros["full"]), "unchanged complete zero fixed point")
    need(len(ledger["support_tables"]) == len(ledger["uneliminated_targets"]) == 84, "complete support table lengths")
    normalized, triangles, rebuilt_targets = [], {}, []
    structural_count, incidence_count = 0, 0
    for table_index, target in enumerate(live_targets):
        clock.check()
        e, premise = target["edge_id"], target["premise_index"]
        a, b = target["endpoints"]
        supports = []
        for c in range(480):
            if c in (a, b):
                continue
            ac, bc = graph["index"].get((a, c)), graph["index"].get((b, c))
            if ac is None or bc is None:
                continue
            if graph["sets"][c] & (graph["sets"][a] | graph["sets"][b]):
                continue
            supports.append([c, ac, bc, covers.get(tuple(sorted((a, b, c))), -1)])
        expected_table = {"edge_id": e, "premise_index": premise, "supports": supports}
        need(ledger["support_tables"][table_index] == expected_table, "every original structural triangle support")
        live_indices = [k for k, (_, ac, bc, cover) in enumerate(supports)
                        if cover == -1 and ac not in zeros["full"] and bc not in zeros["full"]]
        need(live_indices, "surviving target support")
        need(ledger["uneliminated_targets"][table_index] ==
             {"edge_id": e, "premise_index": premise, "surviving_support_indices": live_indices},
             "every final live support index")
        normalized.append([e, premise, supports, live_indices])
        structural_count += len(supports)
        incidence_count += len(live_indices)
        triangle_keys = []
        for support_index in live_indices:
            c = supports[support_index][0]
            key = tuple(sorted((a, b, c)))
            v0, v1, v2 = key
            if key not in triangles:
                triangles[key] = {"vertices": list(key),
                                  "edge_ids": [graph["index"][v0, v1], graph["index"][v0, v2], graph["index"][v1, v2]],
                                  "origins": []}
            triangles[key]["origins"].append({"target_edge_id": e, "support_table_index": table_index,
                                              "support_index": support_index})
            triangle_keys.append(key)
        rebuilt_targets.append((target, triangle_keys))
    need(structural_count == 6540 and incidence_count == 5364, "complete structural/live triangle counts")
    normalized_hash = value_sha(normalized)
    need(normalized_hash == literal["summary"]["normalized_complete_support_records_sha256"]
         == root["normalized_complete_support_records_sha256"], "separate literal replay complete-table identity")
    keys = sorted(triangles)
    triangle_index = {key: k for k, key in enumerate(keys)}
    expected_triangles = []
    for k, key in enumerate(keys):
        t = triangles[key]
        t["origins"].sort(key=lambda o: (o["target_edge_id"], o["support_index"]))
        t["triangle_index"] = k
        t["proposed_variable_index"] = OLD_VARIABLES + k
        expected_triangles.append(t)
    expected_targets = [{"edge_id": t["edge_id"], "endpoints": t["endpoints"],
                         "required_premise_index": t["premise_index"],
                         "triangle_indices": sorted(triangle_index[key] for key in local)}
                        for t, local in rebuilt_targets]
    need(expected_triangles == report["triangles"] and expected_targets == report["targets"],
         "all distinct indicator identities and every target origin")
    need(len(keys) == TRIANGLE_COUNT and sum(len(t["origins"]) for t in expected_triangles) == 5364,
         "complete shared-indicator dimensions")
    and_keys, target_keys = [], []
    for k, t in enumerate(expected_triangles):
        variable = TRIANGLE_FIRST + k
        for edge in t["edge_ids"]:
            and_keys.append(row_key(0, 1, [[EDGE_FIRST + edge, 1], [variable, -1]]))
        and_keys.append(row_key(-2, 1, [[variable, 1]] + [[EDGE_FIRST + edge, -1] for edge in t["edge_ids"]]))
    for target in expected_targets:
        target_keys.append(row_key(0, 0, [[EDGE_FIRST + target["edge_id"], -1]] +
                                   [[TRIANGLE_FIRST + k, 1] for k in target["triangle_indices"]]))
    need(len(and_keys) == 21456 and len(target_keys) == 84, "all triangle row counts")
    need(sum(len(key[2]) for key in and_keys) == 53640 and sum(len(key[2]) for key in target_keys) == 5448,
         "all triangle term counts")
    return {"variables": [(TRIANGLE_FIRST + k, "spectral_triangle_%04d" % k) for k in range(TRIANGLE_COUNT)],
            "and_keys": and_keys, "target_keys": target_keys, "complete_support_sha256": normalized_hash,
            "structural_records": structural_count, "surviving_records": incidence_count}


def forest_block(a, b, live, variable_start, origin):
    variables = [(variable_start + k, "cap1_wedge_%d_%d_%d" % (a, b, c))
                 for k, (c, _, _) in enumerate(live)]
    total = variable_start + len(live)
    variables.append((total, "cap1_total_%d_%d" % (a, b)))
    rows, origins = [], []

    def add(kind, candidate, key):
        rows.append(key)
        origins.append([origin, kind, candidate])

    for k, (c, ac, bc) in enumerate(live):
        z, u, v = variable_start + k, EDGE_FIRST + ac, EDGE_FIRST + bc
        add(0, c, row_key(-2, 0, [[u, 1], [v, 1], [c, -1], [z, -1]]))
        add(1, c, row_key(-1, 0, [[z, 1], [u, -1]]))
        add(2, c, row_key(-1, 0, [[z, 1], [v, -1]]))
    add(3, -1, row_key(0, 0, [[total, 1]] + [[variable_start + k, -1] for k in range(len(live))]))
    add(4, -1, row_key(-1, 0, [[total, 1], [a, -1]]))
    add(5, -1, row_key(-1, 0, [[total, 1], [b, -1]]))
    for k, (c, ac, bc) in enumerate(live):
        add(6, c, row_key(-3, 0, [[EDGE_FIRST + ac, 1], [EDGE_FIRST + bc, 1],
                                 [total, 1], [variable_start + k, -1], [a, -1], [b, -1]]))
    need(len(rows) == 4 * len(live) + 3 and sum(len(key[2]) for key in rows) == 15 * len(live) + 5,
         "complete forest block accounting")
    return variables, rows, origins


def reconstruct_forests(data, graph, zeros, clock):
    derived = data["forest_inventory"]["derived"]
    need(derived["zero_union_ledger"] == zeros["forest_ledger"], "every forest zero origin")
    cap_pairs = data["spectral_cold"]["mathematical"]["overlap_zero_selected_pair_common_exterior_neighbor_cap_one"]
    need(len(cap_pairs) == len(derived["pairs"]) == 48, "all unconditional cap-one pairs")
    variables, row_keys, row_origins, normalized_cases = [], [], [], []
    previous_edge = -1
    for origin, (a, b, central) in enumerate(cap_pairs):
        clock.check()
        need(0 <= a < b < 480 and central > previous_edge and graph["edges"][central] == [a, b],
             "original ordered cap-one pair")
        previous_edge = central
        need(not graph["sets"][a] & graph["sets"][b], "accepted cap-one anchor overlap")
        live, dispositions, original_common = [], [], 0
        for c in range(480):
            ac, bc = graph["index"].get((a, c), -1), graph["index"].get((b, c), -1)
            flags = int(c in (a, b))
            flags |= 2 if ac < 0 else 0
            flags |= 4 if bc < 0 else 0
            flags |= 8 if ac in zeros["old"] else 0
            flags |= 16 if ac in zeros["spectral"] else 0
            flags |= 32 if bc in zeros["old"] else 0
            flags |= 64 if bc in zeros["spectral"] else 0
            dispositions.append([c, ac, bc, flags])
            if c not in (a, b) and ac >= 0 and bc >= 0:
                original_common += 1
            if flags == 0:
                live.append([c, ac, bc])
        need(80 <= len(live) <= 84, "actual complete nonempty forest support")
        start = FOREST_FIRST + len(variables)
        first_row = FOREST_ROW + len(row_keys)
        old_start = start - 7812
        pair = derived["pairs"][origin]
        compare_fields(pair, {"origin_index": origin, "original_spectral_cold_record": [a, b, central],
                             "anchor_pair": [a, b], "central_edge_zero_origins": zeros["full"].get(central),
                             "dispositions": dispositions, "original_common_candidates": original_common,
                             "live_common_candidates": len(live), "live_candidates": live,
                             "assumption_on_central_edge_value": None,
                             "status": "PROPOSED_COMPLETE_FOREST_EXTENSION",
                             "wedges": [[c, ac, bc, old_start + k] for k, (c, ac, bc) in enumerate(live)],
                             "aggregate_variable": old_start + len(live),
                             "native_row_start": first_row - 23988,
                             "appended_variables": len(live) + 1, "appended_rows": 4 * len(live) + 3},
                       "complete literal forest pair")
        local_variables, local_rows, local_origins = forest_block(a, b, live, start, origin)
        for k, (index, name) in enumerate(local_variables):
            candidate = live[k][0] if k < len(live) else -1
            expected = [index - 7812, name, [0, 1], origin, candidate]
            need(derived["proposed_native_variables"][len(variables) + k] == expected, "every original forest variable")
        variables.extend(local_variables)
        for key in local_rows:
            shifted = [key[0], key[1], [[v - 7812 if v >= FOREST_FIRST else v, coef] for v, coef in key[2]]]
            need(derived["proposed_native_row_keys"][len(row_keys)] == shifted, "every original forest native key")
            row_keys.append(key)
        row_origins.extend(local_origins)
        normalized_cases.append([origin, a, b, central, dispositions, live])
    need(row_origins == derived["row_origins"], "all forest native row origins")
    need(len(variables) == FOREST_COUNT and len(row_keys) == 15888 and sum(len(key[2]) for key in row_keys) == 59280,
         "complete forest native inventory")
    need(len(derived["proposed_native_variables"]) == FOREST_COUNT and len(derived["proposed_native_row_keys"]) == 15888,
         "no extra proposed forest variables or rows")
    compare_fields(derived["counts"], {"accepted_pairs": 48, "candidate_dispositions": 23040,
                                      "accepted_zero_union": 1956, "extended_pairs": 48,
                                      "endpoint_forest_skipped_pairs": 0, "new_variables": 3984,
                                      "new_rows": 15888, "new_terms": 59280,
                                      "proposed_total_variables": 72918, "proposed_total_rows": 273482},
                   "complete forest forward counts")
    literal = data["forest_literal_replay"]
    need(literal["status"] == "PASS_COMPLETE_INDEPENDENT_LITERAL_FOREST_SUPPORT_AND_ROWS",
         "complete separate literal forest acceptance")
    literal_normalized = literal["normalized"]
    canonical_derived = json.dumps(derived, sort_keys=True, ensure_ascii=True, separators=(",", ":"), allow_nan=False).encode("ascii")
    need(literal_normalized["whole_derived_canonical_sha256"] == digest(canonical_derived), "separate whole forest artifact identity")
    for key, field in (("proposed_native_row_keys", "native_row_keys_json_sha256"),
                       ("proposed_native_variables", "native_variables_json_sha256"), ("row_origins", "row_origins_json_sha256")):
        need(literal_normalized[field] == value_sha(derived[key]), "separate complete forest native inventory identity")
    return {"variables": variables, "row_keys": row_keys, "origins_sha256": value_sha(row_origins),
            "literal_dispositions_sha256": value_sha(normalized_cases),
            "all_candidate_dispositions": 48 * 480, "live_wedges": FOREST_COUNT - 48}

def restore_parent(pb, parent, actual, old_variables, old_rows, first_replaced, replacement_count, clock):
    need(len(actual.variables) >= old_variables and len(actual.constraints) >= old_rows, "model retains parent dimensions")
    for k in range(old_variables):
        need(actual.variables[k].SerializeToString() == parent.variables[k].SerializeToString(),
             "unchanged original variable message")
    for k in range(old_rows):
        if k % 2048 == 0:
            clock.check()
        if not first_replaced <= k < first_replaced + replacement_count:
            need(actual.constraints[k].SerializeToString() == parent.constraints[k].SerializeToString(),
                 "unchanged original constraint message")
    edited = pb.CpModelProto()
    edited.CopyFrom(actual)
    del edited.constraints[old_rows:]
    restored = pb.CpModelProto()
    restored.CopyFrom(edited)
    del restored.variables[old_variables:]
    for k in range(first_replaced, first_replaced + replacement_count):
        restored.constraints[k].CopyFrom(parent.constraints[k])
    need(restored.SerializeToString() == parent.SerializeToString(), "exact complete original model restoration")
    return edited.SerializeToString(), restored.SerializeToString()


def check_patch_and_suffix(pb, parent, actual, patch_raw, suffix_raw, edited_raw, full_raw, clock):
    patch, suffix = parse_model(pb, patch_raw), parse_model(pb, suffix_raw)
    need({f.name for f, _ in patch.ListFields()} <= {"variables", "constraints"}, "only approved prefix-patch fields")
    need(len(patch.variables) == FINAL_VARIABLES - OLD_VARIABLES and len(patch.constraints) == FOUR_COUNT,
         "complete prefix-patch dimensions")
    need({f.name for f, _ in suffix.ListFields()} <= {"constraints"}, "suffix contains only appended constraints")
    need(len(suffix.constraints) == FINAL_ROWS - OLD_ROWS, "complete true suffix dimensions")
    for k, variable in enumerate(patch.variables):
        need(variable.SerializeToString() == actual.variables[OLD_VARIABLES + k].SerializeToString(), "every patch variable")
    for k, row in enumerate(patch.constraints):
        need(row.SerializeToString() == actual.constraints[FOUR_FIRST + k].SerializeToString(), "every patch replacement")
    for k, row in enumerate(suffix.constraints):
        if k % 2048 == 0:
            clock.check()
        need(row.SerializeToString() == actual.constraints[OLD_ROWS + k].SerializeToString(), "every true suffix row")
    reconstructed = pb.CpModelProto()
    reconstructed.CopyFrom(parent)
    reconstructed.variables.extend(patch.variables)
    for k, row in enumerate(patch.constraints):
        reconstructed.constraints[FOUR_FIRST + k].CopyFrom(row)
    need(reconstructed.SerializeToString() == edited_raw, "exact edited-prefix reconstruction")
    need(edited_raw + suffix_raw == full_raw, "exact edited-prefix plus true suffix bytes")
    need(not full_raw.startswith(parent.SerializeToString()), "original raw prefix is explicitly changed")


def check_complete_model(pb, parent, parent_raw, actual, full_raw, stars, triangles, forests, clock):
    need(len(actual.variables) == FINAL_VARIABLES and len(actual.constraints) == FINAL_ROWS, "complete combined model dimensions")
    expected_variables = stars["variables"] + triangles["variables"] + forests["variables"]
    need([index for index, _ in expected_variables] == list(range(OLD_VARIABLES, FINAL_VARIABLES)),
         "one disjoint contiguous new variable namespace")
    for index, name in expected_variables:
        check_variable(pb, actual.variables[index], name)
    families = [
        ("star_replacement", FOUR_FIRST, stars["replacement_keys"], 23010, 69030),
        ("star_definition", STAR_ROW, stars["definition_keys"], 2448, 22380),
        ("triangle_and", TRIANGLE_ROW, triangles["and_keys"], 21456, 53640),
        ("triangle_target", TRIANGLE_ROW + 21456, triangles["target_keys"], 84, 5448),
        ("forest", FOREST_ROW, forests["row_keys"], 15888, 59280),
    ]
    counts, terms, hashes = {}, {}, {}
    for name, first, keys, count, term_count in families:
        need(len(keys) == count and sum(len(key[2]) for key in keys) == term_count, "exact complete family " + name)
        for k, key in enumerate(keys):
            if k % 2048 == 0:
                clock.check()
            check_row(pb, actual.constraints[first + k], key, name)
        counts[name], terms[name], hashes[name] = count, term_count, row_digest(keys)
    edited_raw, restored_raw = restore_parent(pb, parent, actual, OLD_VARIABLES, OLD_ROWS, FOUR_FIRST, FOUR_COUNT, clock)
    need(restored_raw == parent_raw, "restored original raw publication bytes")
    need(digest(restored_raw) == PARENT_RAW_SHA and len(restored_raw) == PARENT_RAW_BYTES, "exact parent restoration identity")
    need(actual.SerializeToString() == full_raw, "complete new raw canonical model")
    return {"family_order": [f[0] for f in families], "family_counts": counts,
            "family_terms": terms, "family_row_jsonl_sha256": hashes,
            "edited_prefix_raw": edited_raw, "restored_raw": restored_raw,
            "unchanged_original_variables_checked": OLD_VARIABLES,
            "unchanged_original_rows_checked": OLD_ROWS - FOUR_COUNT,
            "replacement_rows_checked": FOUR_COUNT, "appended_rows_checked": FINAL_ROWS - OLD_ROWS,
            "added_variables_checked": FINAL_VARIABLES - OLD_VARIABLES,
            "new_and_replacement_terms_checked": sum(terms.values()), "net_term_change": sum(terms.values()) - 401874}


def tiny_controls(pb, clock):
    def holds(keys, point):
        return all(lo <= sum(coef * point[index] for index, coef in terms) <= hi for lo, hi, terms in keys)

    star_cases = 0
    star_definition = row_key(0, 0, [[0, -1], [1, 1], [2, 1]])
    star_clause = row_key(-2, 0, [[3, 1], [2, -1], [4, -1]])
    for center in (0, 1):
        for star in range(center + 1):
            for right in (0, 1):
                for central in (0, 1):
                    for channel in (0, 1):
                        point = {0: center, 1: star, 2: channel, 3: central, 4: right}
                        exact = channel == center - star and central + star - center - right <= 0
                        need(holds([star_definition, star_clause], point) == exact, "synthetic star equality/cover identity")
                        star_cases += 1
    and_keys = [row_key(0, 1, [[e, 1], [3, -1]]) for e in range(3)]
    and_keys.append(row_key(-2, 1, [[3, 1], [0, -1], [1, -1], [2, -1]]))
    and_cases = 0
    for mask in range(8):
        for t in (0, 1):
            y = [(mask >> k) & 1 for k in range(3)]
            point = {0: y[0], 1: y[1], 2: y[2], 3: t}
            need(holds(and_keys, point) == (t == y[0] * y[1] * y[2]), "synthetic complete three-edge AND")
            and_cases += 1
    # Two common-neighbor candidates. Check the actual native forest templates
    # for every Boolean assignment satisfying original endpoint activations.
    variables, keys, _ = forest_block(0, 1, [[2, 0, 1], [3, 2, 3]], 10, 0)
    forest_cases = 0
    for mask in range(256):
        values = [(mask >> k) & 1 for k in range(8)]
        a, b, c, d, ac, bc, ad, bd = values
        if ac > min(a, c) or bc > min(b, c) or ad > min(a, d) or bd > min(b, d):
            continue
        zc, zd = ac * bc, ad * bd
        point = {0: a, 1: b, 2: c, 3: d, 540: ac, 541: bc, 542: ad, 543: bd,
                 10: zc, 11: zd, 12: zc + zd}
        need(holds(keys, point) == (zc + zd <= 1), "synthetic complete forest projection")
        forest_cases += 1
    parent = pb.CpModelProto(name="parent control")
    for k in range(3):
        variable = parent.variables.add(name="original_%d" % k)
        variable.domain.extend([0, 1])
    parent.constraints.add().CopyFrom(constraint(pb, row_key(-1, 0, [[0, -1], [1, 1]])))
    parent.constraints.add().CopyFrom(constraint(pb, row_key(0, 1, [[1, 1], [2, 1]])))
    original = parent.SerializeToString()
    model = pb.CpModelProto()
    model.CopyFrom(parent)
    model.variables.add(name="new").domain.extend([0, 1])
    model.constraints[1].CopyFrom(constraint(pb, row_key(-1, 0, [[2, 1], [3, -1]])))
    model.constraints.add().CopyFrom(constraint(pb, row_key(0, 0, [[0, -1], [3, 1]])))
    _, restored = restore_parent(pb, parent, model, 3, 2, 1, 1, clock)
    need(restored == original, "synthetic exact complete restoration")
    rejected = 0
    for mutation in ("old_variable_name", "old_variable_domain", "unmodified_row", "top_level_name"):
        bad = pb.CpModelProto()
        bad.CopyFrom(model)
        if mutation == "old_variable_name":
            bad.variables[0].name = "changed"
        elif mutation == "old_variable_domain":
            bad.variables[0].domain[-1] = 2
        elif mutation == "unmodified_row":
            bad.constraints[0].linear.coeffs[0] = 1
        else:
            bad.name = "changed top-level model name"
        try:
            restore_parent(pb, parent, bad, 3, 2, 1, 1, clock)
        except ValueError:
            rejected += 1
    need(rejected == 4, "all unauthorized original protobuf mutations rejected")
    actual = constraint(pb, row_key(-2, 0, [[1, 1], [2, -1], [3, -1]]))
    bad = pb.ConstraintProto()
    bad.CopyFrom(actual)
    bad.name = "unaccepted extra constraint metadata"
    try:
        check_row(pb, bad, row_key(-2, 0, [[1, 1], [2, -1], [3, -1]]), "metadata mutation")
    except ValueError:
        rejected += 1
    need(rejected == 5, "complete message comparison rejects row metadata")
    coefficient = 9007199254740993
    key = row_key(-coefficient, coefficient, [[0, coefficient]])
    raw = constraint(pb, key).SerializeToString()
    restored_constraint = pb.ConstraintProto()
    restored_constraint.ParseFromString(raw)
    need(restored_constraint.linear.coeffs[0] == coefficient, "integer coefficient above binary64 exact range")
    clock.check()
    return {"status": CONTROLS_PASS, "star_boolean_cases": star_cases, "three_edge_and_cases": and_cases,
            "forest_activated_boolean_cases": forest_cases, "unauthorized_mutations_rejected": rejected,
            "exact_parent_restoration_control": True, "above_binary64_integer_coefficient": coefficient,
            "actual_case_inputs_loaded": False, "actual_case_reconstruction_calls": 0}

LAYOUT = {
    "parent_variables": 68934, "parent_rows": 257594, "replacement_start": 227270,
    "replacement_count": 23010, "star_variable_start": 68934, "star_variables": 2448,
    "triangle_variable_start": 71382, "triangle_variables": 5364,
    "forest_variable_start": 76746, "forest_variables": 3984,
    "star_definition_start": 257594, "triangle_and_start": 260042,
    "triangle_target_start": 281498, "forest_row_start": 281582,
    "new_variables": 11796, "appended_rows": 39876, "variables": 80730, "rows": 297470,
}
FAMILY_ORDER = ["star_replacement", "star_definition", "triangle_and", "triangle_target", "forest"]
FAMILY_COUNTS = dict(zip(FAMILY_ORDER, [23010, 2448, 21456, 84, 15888]))
FAMILY_TERMS = dict(zip(FAMILY_ORDER, [69030, 22380, 53640, 5448, 59280]))
REQUIRED_INPUTS = {
    "parent_model", "parent_report", "parent_owner", "parent_cold", "parent_cold_owner",
    "parent_root_acceptance", "domain", "overlay", "four_inventory", "four_certificate_replay",
    "four_root_acceptance", "star_inventory", "star_finalization", "star_root_acceptance",
    "triangle_support_ledger", "triangle_literal_replay", "triangle_literal_finalization",
    "triangle_inventory", "triangle_finalization", "triangle_literal_root_acceptance",
    "forest_inventory", "forest_finalization", "forest_literal_replay", "forest_literal_finalization",
    "forest_literal_root_acceptance", "spectral_cold", "spectral_root_acceptance",
    "triangle_forward", "triangle_root_acceptance",
}


def semantic_configuration(cfg, clock):
    need(cfg["layout"] == LAYOUT and cfg["family_order"] == FAMILY_ORDER, "frozen complete layout/order")
    need(cfg["expected_family_counts"] == FAMILY_COUNTS and cfg["expected_family_terms"] == FAMILY_TERMS,
         "frozen complete family dimensions")
    need(cfg["optimizer_calls"] == cfg["automatic_retries"] == 0 and cfg["native_query_authorized"] is False,
         "construction-only configuration")
    need(cfg["independent_complete_protobuf_replay_required"] is True, "separate complete replay required")
    compare_fields(cfg["limits"], {"independent_controls_worker_seconds": 10, "independent_controls_owner_seconds": 15,
                                  "independent_cold_worker_seconds": 120, "independent_cold_owner_seconds": 135},
                   "fixed independent worker/owner bounds")
    need(REQUIRED_INPUTS <= cfg["inputs"].keys(), "complete mathematical input set")
    for ref in list(cfg["sources"].values()) + cfg.get("proofs", []) + cfg.get("reviews", []):
        read_bound(ref)
        clock.check()


def validate_successful_owner(owner, report_ref):
    need(owner["report_accepted"] is True and owner["optimizer_calls"] == 0, "accepted zero-solve owner")
    need(owner["seconds"] <= owner["maximum_seconds"] and owner.get("deadline_overrun_seconds", 0) == 0,
         "owner remained within bound")
    supervision = owner["supervision"]
    need(supervision["status"] == "CHILD_EXITED" and supervision["returncode"] == 0, "successful owned child")
    need(supervision["child_reaped"] is True and supervision["owned_process_group_stopped"] is True,
         "owned process group stopped and reaped")
    same_ref(owner["report"], report_ref, "owner report binding")


def load_inputs(cfg, clock):
    data = {}
    for name, ref in cfg["inputs"].items():
        if name != "parent_model":
            data[name] = json.loads(decoded_bound(ref))
        clock.check()
    authorities = set()
    for authority in cfg["authorities"]:
        name, status = authority["input"], authority["expected_status"]
        need(name not in authorities and status.startswith(("PASS_", "ROOT_ACCEPTS_", "OWNED_", "COMPLETE_")),
             "unique explicit accepted authority")
        need(data[name][authority.get("status_field", "status")] == status, "accepted authority status " + name)
        authorities.add(name)
    required = REQUIRED_INPUTS - {"parent_model", "domain", "overlay", "four_inventory",
                                  "triangle_support_ledger", "triangle_forward"}
    need(required <= authorities, "every required acceptance status checked")
    for link in cfg.get("authority_links", []):
        value = data[link["input"]]
        for field in link["fields"]:
            value = value[field]
        same_ref(value, cfg["inputs"][link["target"]], "complete configured authority link")
    fixed_statuses = {
        "parent_report": "PASS_COMPLETE_STRENGTHENED_LITERAL_NATIVE_PREPARATION",
        "parent_cold": "PASS_INDEPENDENT_COMPLETE_STRENGTHENED_LITERAL_NATIVE_APPEND",
        "parent_root_acceptance": "ROOT_ACCEPTS_COMPLETE_STRENGTHENED_NATIVE_MODEL_AND_INDEPENDENT_COLD",
        "four_inventory": "COMPLETE_INDEPENDENT_ORIGINAL_KEYS_AND_ACTUAL_CROSS_QUOTA_CERTIFICATES",
        "four_certificate_replay": "PASS_EVERY_ORIGINAL_ROW_ORIGIN_AND_MIXED_LINEAR_CERTIFICATE",
        "four_root_acceptance": "ROOT_ACCEPTS_COMPLETE_FOUR_EXTERIOR_RECONSTRUCTION_AND_49458_MIXED_REDUNDANCY_CERTIFICATES",
        "star_inventory": "PASS_COMPLETE_EXACT_STAR_CHANNEL_INVENTORY",
        "star_finalization": "PASS_COMPLETE_CHANNEL_INVENTORY_AND_SERIALIZATION",
        "triangle_support_ledger": "PASS_COMPLETE_TARGETED_SUPPORT_FIXED_POINT",
        "triangle_inventory": "PASS_EXACT_SHARED_TRIANGLE_INDICATOR_INVENTORY",
        "triangle_literal_replay": "PASS_COMPLETE_INDEPENDENT_LITERAL_SUPPORT_REPLAY",
        "triangle_literal_root_acceptance": "ROOT_ACCEPTS_COMPLETE_SEPARATE_LITERAL_SUPPORT_REPLAY_AND_INDICATOR_BINDINGS",
        "spectral_cold": "PASS_COMPLETE_INDEPENDENT_SPECTRAL_GAP_PAIR_CENSUS",
        "spectral_root_acceptance": "ROOT_ACCEPTS_COMPLETE_INDEPENDENT_SPECTRAL_GAP_PAIR_CENSUS",
        "triangle_root_acceptance": "ROOT_ACCEPTS_COMPLETE_INDEPENDENT_CENSUS_AND_EVERY_ZERO_DISPOSITION",
    }
    for name, status in fixed_statuses.items():
        need(data[name]["status"] == status, "fixed original acceptance " + name)
    root, cold, report = (data[k] for k in ("parent_root_acceptance", "parent_cold", "parent_report"))
    for record in (root, cold):
        compare_fields(record, {"model_raw_sha256": PARENT_RAW_SHA, "model_raw_bytes": PARENT_RAW_BYTES,
                                "variables": OLD_VARIABLES, "rows": OLD_ROWS}, "accepted parent")
    compare_fields(report["model"], {"raw_sha256": PARENT_RAW_SHA, "raw_bytes": PARENT_RAW_BYTES}, "parent preparation")
    for a, b in (("preparation", "parent_report"), ("independent_cold", "parent_cold"), ("model_archive", "parent_model")):
        same_ref(root[a], cfg["inputs"][b], "parent root authority")
    same_ref(cold["producer_report"], cfg["inputs"]["parent_report"], "parent cold producer")
    same_ref(cold["producer_owner"], cfg["inputs"]["parent_owner"], "parent cold owner")
    for owner_name, report_name in (("parent_owner", "parent_report"), ("parent_cold_owner", "parent_cold")):
        validate_successful_owner(data[owner_name], cfg["inputs"][report_name])
        need(any(item["owner"]["path"] == cfg["inputs"][owner_name]["path"] and
                 item["owner"]["sha256"] == cfg["inputs"][owner_name]["sha256"] for item in root["owners"]),
             "parent root accepts this exact owner")
    for name in ("star_inventory", "forest_inventory"):
        need(data[name]["complete"] is True and data[name]["error"] is None, "complete inventory " + name)
        need(data[name]["original_model_raw_sha256"] == PARENT_RAW_SHA, "inventory original model")
        for old, new in (("domain", "domain"), ("overlay", "overlay"),
                         ("native_root_acceptance", "parent_root_acceptance"), ("native_cold", "parent_cold")):
            same_ref(data[name]["inputs"][old], cfg["inputs"][new], "inventory original authority")
    for alias in ("star_finalization", "forest_finalization"):
        final = data[alias]
        need(final["complete"] is True and final["within_declared_bounds"] is True and final["main_calls"] == 1,
             "complete one-call inventory finalization")
        report_name = alias.replace("finalization", "inventory")
        need(final["report_bytes"] == cfg["inputs"][report_name]["bytes"], "inventory finalization byte count")
    same_ref(data["four_root_acceptance"]["complete_reconstruction"], cfg["inputs"]["four_inventory"], "complete four authority")
    same_ref(data["four_root_acceptance"]["certificate_replay"], cfg["inputs"]["four_certificate_replay"], "complete four certificate authority")
    for name in ("four_inventory", "four_certificate_replay", "four_root_acceptance"):
        same_ref(data["star_inventory"]["inputs"][name], cfg["inputs"][name], "star original four authority")
    same_ref(data["triangle_inventory"]["inputs"]["ledger"], cfg["inputs"]["triangle_support_ledger"], "indicator complete ledger")
    same_ref(data["triangle_inventory"]["inputs"]["model_acceptance"], cfg["inputs"]["parent_root_acceptance"], "indicator parent")
    same_ref(data["triangle_literal_replay"]["inputs"]["support_ledger"], cfg["inputs"]["triangle_support_ledger"], "literal support ledger")
    for prefix in ("star", "triangle_literal", "forest_literal"):
        root_name = prefix + "_root_acceptance"
        report_name = prefix + ("_replay" if prefix.endswith("_literal") else "_inventory")
        same_ref(data[root_name]["report"], cfg["inputs"][report_name], "root finite acceptance report")
        same_ref(data[root_name]["finalization"], cfg["inputs"][prefix + "_finalization"], "root finite acceptance finalization")
    for prefix in ("triangle", "triangle_literal", "forest_literal"):
        final = data[prefix + "_finalization"]
        need(final["within_declared_bounds"] is True and final["main_calls"] == 1, "finite replay/inventory finalization")
    need(data["triangle_support_ledger"]["complete"] is True and data["triangle_support_ledger"]["error"] is None,
         "complete original support ledger")
    need(data["spectral_cold"]["complete"] is True and data["spectral_cold"]["all405426_saved_integer_determinants_checked"] is True,
         "accepted exact spectral premises")
    clock.check()
    return data


def preparation_inputs(args, cfg, cfg_ref, clock):
    directory = args.preparation_directory.resolve()
    need(directory.is_relative_to(ROOT), "preparation directory remains in repository")
    report_ref, owner_ref = file_ref(directory / "report.json"), file_ref(directory / "owner.json")
    need(report_ref["sha256"] == args.report_sha256 and owner_ref["sha256"] == args.owner_sha256,
         "exact CLI preparation report/owner identities")
    report, owner = json.loads(read_bound(report_ref)), json.loads(read_bound(owner_ref))
    need(report["schema"] == "conway99.f0.combined-extensions-native-preparation.v1"
         and report["status"] == "PASS_COMPLETE_COMBINED_EXTENSIONS_NATIVE_PREPARATION", "successful native preparation")
    need(owner["schema"] == "conway99.f0.combined-extensions-native-owner.v1" and owner["status"] == report["status"],
         "successful native preparation owner")
    validate_successful_owner(owner, report_ref)
    need(owner["maximum_seconds"] == 135 and owner["mode"] == "prepare", "actual one bounded preparation")
    for record in (report, owner):
        same_ref(record["configuration"], cfg_ref, "preparation exact configuration")
        need(record["source"]["sha256"] == cfg["source_sha256"], "preparation exact source")
        read_bound(record["source"])
        need(record["optimizer_calls"] == 0 and record["CpSolver_constructed"] is False
             and record["native_query_run"] is False and record["native_optimizer_constructed"] is False,
             "preparation is zero-solve")
    same_ref(report["source"], owner["source"], "one preparation source")
    need(report["inputs"] == cfg["inputs"] and report["authorities"] == cfg["authorities"], "all actual preparation bindings")
    need(report["maximum_seconds"] == 120 and report["layout"] == LAYOUT, "actual construction limit/layout")
    compare_fields(report, {"variables": FINAL_VARIABLES, "rows": FINAL_ROWS, "parent_variables": OLD_VARIABLES,
                            "parent_rows": OLD_ROWS, "family_order": FAMILY_ORDER,
                            "family_counts": FAMILY_COUNTS, "family_terms": FAMILY_TERMS,
                            "term_change": -192096, "parent_is_complete_raw_prefix": False,
                            "edited_prefix_is_complete_raw_prefix": True}, "actual combined preparation")
    transport = report["native_transport"]
    need(transport["complete_byte_comparison"] is True and transport["public_parse_return"] is True
         and transport["native_validation"] == "", "complete actual public native transport")
    stage_raw = read_bound(report["stages"])
    need(isinstance(json.loads(stage_raw), list), "preserved preparation stage receipt")
    receipt = json.loads(read_bound(owner["owned_receipt"]))
    need(receipt["supervision"] == owner["supervision"] and receipt["mode"] == "prepare", "preserved owned preparation receipt")
    same_ref(receipt["source"], owner["source"], "owned receipt source")
    same_ref(receipt["configuration"], cfg_ref, "owned receipt configuration")
    supervision = json.loads(read_bound(receipt["supervisor_record"]))
    need(supervision == owner["supervision"], "actual preserved supervisor record")
    artifacts = report["artifacts"]
    need(set(artifacts) == {"model", "model_archive", "patch_archive", "suffix_archive", "restoration_manifest"},
         "complete exact model artifact set")
    files = {}
    for key, ref in artifacts.items():
        need(bound_path(ref).parent == directory, "owned preparation artifact directory")
        files[key] = read_bound(ref)
        clock.check()
    raw = files["model"]
    need(gzip.decompress(files["model_archive"]) == raw, "raw model and full archive identical")
    patch_raw, suffix_raw = gzip.decompress(files["patch_archive"]), gzip.decompress(files["suffix_archive"])
    manifest = json.loads(files["restoration_manifest"])
    need(manifest["schema"] == "conway99.f0.combined-extensions-restoration.v1"
         and manifest["status"] == "PASS_EXACT_COMBINED_PATCH_AND_SUFFIX_RESTORATION", "complete restoration manifest")
    same_ref(manifest["source"], report["source"], "manifest source")
    same_ref(manifest["configuration"], cfg_ref, "manifest configuration")
    same_ref(manifest["parent_model"], cfg["inputs"]["parent_model"], "manifest accepted parent")
    need(manifest["layout"] == LAYOUT and manifest["restoration"] == report["restoration"], "manifest complete restoration dimensions")
    need(manifest["artifacts"] == {k: artifacts[k] for k in artifacts if k != "restoration_manifest"},
         "manifest complete artifact identities")
    compare_fields(manifest, {"patch_variables": 11796, "patch_constraints": 23010, "suffix_constraints": 39876,
                              "parent_is_complete_raw_prefix": False, "edited_prefix_is_complete_raw_prefix": True,
                              "complete_original_parent_bytes_recovered": True}, "manifest exact patch/suffix semantics")
    compare_fields(report["model"], {"raw_bytes": len(raw), "raw_sha256": digest(raw),
                                     "archive_bytes": len(files["model_archive"]), "archive_sha256": digest(files["model_archive"])},
                   "actual model identities")
    need(report["model_raw_sha256"] == digest(raw) and report["model_raw_bytes"] == len(raw), "actual flat model identity")
    compare_fields(report["restoration"], {"parent_raw_bytes": PARENT_RAW_BYTES, "parent_raw_sha256": PARENT_RAW_SHA,
                                          "patch_raw_bytes": len(patch_raw), "patch_raw_sha256": digest(patch_raw),
                                          "suffix_raw_bytes": len(suffix_raw), "suffix_raw_sha256": digest(suffix_raw)},
                   "exact patch/suffix raw identities")
    return report, report_ref, owner_ref, raw, patch_raw, suffix_raw

def message_sequence_sha(messages):
    h = hashlib.sha256()
    for message in messages:
        raw = message.SerializeToString()
        h.update(len(raw).to_bytes(8, "big"))
        h.update(raw)
    return h.hexdigest()


def replay(args, cfg, cfg_ref, pb, clock):
    data = load_inputs(cfg, clock)
    prep, prep_ref, owner_ref, raw, patch_raw, suffix_raw = preparation_inputs(args, cfg, cfg_ref, clock)
    parent_raw = decoded_bound(cfg["inputs"]["parent_model"])
    need(len(parent_raw) == PARENT_RAW_BYTES and digest(parent_raw) == PARENT_RAW_SHA, "accepted complete original raw bytes")
    parent, actual = parse_model(pb, parent_raw), parse_model(pb, raw)
    check_original_namespace(parent)
    graph = literal_graph(data["domain"], parent, pb, clock)
    zeros = literal_zeros(data, graph, parent, pb)
    stars = reconstruct_stars(data, graph, zeros, parent, pb, clock)
    triangles = reconstruct_triangles(data, graph, zeros, parent, pb, clock)
    forests = reconstruct_forests(data, graph, zeros, clock)
    checked = check_complete_model(pb, parent, parent_raw, actual, raw, stars, triangles, forests, clock)
    edited_raw = checked.pop("edited_prefix_raw")
    restored_raw = checked.pop("restored_raw")
    check_patch_and_suffix(pb, parent, actual, patch_raw, suffix_raw, edited_raw, raw, clock)
    compare_fields(prep["restoration"], {"edited_prefix_raw_bytes": len(edited_raw),
                                        "edited_prefix_raw_sha256": digest(edited_raw)}, "exact edited prefix identity")
    for field in ("family_order", "family_counts", "family_terms", "family_row_jsonl_sha256"):
        need(prep[field] == checked[field], "producer complete family receipt " + field)
    parent_terms = sum(len(row.linear.vars) for row in parent.constraints)
    total_terms = sum(len(row.linear.vars) for row in actual.constraints)
    need(total_terms - parent_terms == checked["net_term_change"] == -192096, "exact complete model coefficient count")
    need(prep["parent_total_terms"] == parent_terms and prep["total_terms"] == total_terms, "producer total coefficient receipts")
    preservation = prep["preservation"]
    compare_fields(preservation, {"original_variable_messages_sha256": message_sequence_sha(parent.variables),
                                  "unreplaced_parent_constraint_messages_sha256": message_sequence_sha(
                                      parent.constraints[k] for k in range(OLD_ROWS)
                                      if not FOUR_FIRST <= k < FOUR_FIRST + FOUR_COUNT),
                                  "unreplaced_parent_constraints": OLD_ROWS - FOUR_COUNT,
                                  "complete_original_parent_bytes_recovered": True,
                                  "all_original_variable_messages_preserved": True,
                                  "all_unreplaced_parent_constraint_messages_preserved": True,
                                  "only_declared_replacement_span_changed": True}, "complete parent preservation receipt")
    need(len({actual.variables[k].name for k in range(OLD_VARIABLES, FINAL_VARIABLES)}) == FINAL_VARIABLES - OLD_VARIABLES,
         "all specified new variable names are distinct")
    clock.check()
    return {
        "status": MAIN_PASS, "inputs": cfg["inputs"], "authorities": cfg["authorities"],
        "preparation_report": prep_ref, "preparation_owner": owner_ref, "preparation_source": prep["source"],
        "artifacts": prep["artifacts"], "layout": LAYOUT, "restoration": prep["restoration"],
        "variables": FINAL_VARIABLES, "rows": FINAL_ROWS, "parent_variables": OLD_VARIABLES, "parent_rows": OLD_ROWS,
        "model_raw_sha256": digest(raw), "model_raw_bytes": len(raw),
        "base_restoration_sha256": digest(restored_raw), "base_restoration_bytes": len(restored_raw),
        "edited_prefix_sha256": digest(edited_raw), "edited_prefix_bytes": len(edited_raw),
        "patch_raw_sha256": digest(patch_raw), "patch_raw_bytes": len(patch_raw),
        "suffix_raw_sha256": digest(suffix_raw), "suffix_raw_bytes": len(suffix_raw),
        **checked, "parent_total_terms": parent_terms, "total_terms": total_terms,
        "complete_original_parent_bytes_recovered": True,
        "all_original_variable_messages_preserved": True, "all_unreplaced_parent_constraint_messages_preserved": True,
        "only_declared_replacement_span_changed": True,
        "all_replacement_and_appended_rows_compared_as_complete_protobuf_messages": True,
        "all_new_variable_domains_names_and_metadata_checked": True,
        "complete_native_artifacts_and_manifest_checked": True,
        "parent_is_complete_raw_prefix": False, "edited_prefix_is_complete_raw_prefix": True,
        "complete_original_signature_and_edge_namespace_reconstructed": True,
        "original_neighbor_rows_checked": 480, "original_eligible_edges": 68394, "accepted_zero_union": 1956,
        "star_exact_channel_keys_sha256": stars["channel_key_sha256"],
        "star_complete_origin_links_sha256": stars["origin_links_sha256"],
        "star_complete_origin_links_checked": 46020, "star_original_quota_one_mixed_receipts_checked": stars["mixed_receipts"],
        "star_unique_Boolean_extension_and_continuous_projection_identity_checked": True,
        "triangle_complete_support_sha256": triangles["complete_support_sha256"],
        "triangle_structural_records_checked": triangles["structural_records"],
        "triangle_surviving_records_checked": triangles["surviving_records"],
        "triangle_all_original_cover_implications_checked": 10830, "triangle_all_target_equalities_checked": 84,
        "forest_complete_dispositions_sha256": forests["literal_dispositions_sha256"],
        "forest_complete_native_origins_sha256": forests["origins_sha256"],
        "forest_complete_candidate_dispositions_checked": forests["all_candidate_dispositions"],
        "forest_live_wedges_checked": forests["live_wedges"], "forest_pairs_checked": 48,
        "forest_candidate_disjointness_or_triangle_filter_used": False,
        "forest_anchor_edge_value_assumed": False,
        "native_model_decodes": 4, "original_constraints_mathematically_reproved": False,
        "scope": "Exact original-model preservation, equivalent retained-four channel replacement, and complete proof-bound triangle/forest extensions; no solution or exclusion claim.",
    }


def write_exclusive(path, raw):
    with Path(path).open("xb") as stream:
        stream.write(raw)


def worker(args):
    maximum = 10 if args.mode == "controls" else 120
    clock = Clock(maximum)
    args.directory.mkdir(parents=True, exist_ok=False)
    try:
        cfg, cfg_ref = configuration(args.configuration, args.configuration_sha256, clock)
        semantic_configuration(cfg, clock)
        pb = protobuf_decoder(cfg)
        if args.mode == "controls":
            report = tiny_controls(pb, clock)
        else:
            need(args.preparation_directory is not None and args.report_sha256 and args.owner_sha256,
                 "main requires exact preparation directory/report/owner identities")
            report = replay(args, cfg, cfg_ref, pb, clock)
        need(not any(name.startswith("ortools.sat.python") for name in sys.modules),
             "no native CpModel/helper/Solver modules imported")
        report.update(
            schema="conway99.f0.combined-extensions-independent-" + ("controls" if args.mode == "controls" else "cold") + ".v1",
            source=file_ref(__file__), configuration=cfg_ref, maximum_seconds=maximum,
            runtime={"python": sys.version, "ortools": importlib.metadata.version("ortools"),
                     "protobuf": importlib.metadata.version("protobuf"), "model_schema_sha256": SCHEMA_SHA},
            optimizer_calls=0, producer_imports=0, native_imports=0, native_model_builds=0,
            CpModel_constructed=False, CpSolver_constructed=False, native_optimizer_constructed=False,
            protobuf_decoder_only=True, graph_constructed=False, whole_component_excluded=False,
            automatic_retries=0, seconds_before_report_serialization=clock.elapsed(),
            peak_rss_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            accepted_only_with_successful_separate_owner=True,
        )
        raw = compact(report) + b"\n"
        need(len(raw) <= 1024 * 1024, "bounded independent summary size")
        clock.check()  # Includes complete report serialization.
        write_exclusive(args.directory / "report.json", raw)
        clock.check()  # A late write exits nonzero; a PASS-shaped file alone is insufficient.
    except BaseException as error:
        failure = {"schema": "conway99.f0.combined-extensions-independent-error.v1",
                   "status": "ERROR_INDEPENDENT_COMBINED_EXTENSIONS_REPLAY", "mode": args.mode,
                   "type": type(error).__name__, "message": str(error), "seconds": clock.elapsed(),
                   "maximum_seconds": maximum, "report_accepted": False,
                   "optimizer_calls": 0, "producer_imports": 0, "native_imports": 0}
        write_exclusive(args.directory / "error.json", compact(failure) + b"\n")
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("controls", "replay"))
    parser.add_argument("--configuration", type=Path, required=True)
    parser.add_argument("--configuration-sha256", required=True)
    parser.add_argument("--preparation-directory", type=Path)
    parser.add_argument("--report-sha256")
    parser.add_argument("--owner-sha256")
    parser.add_argument("--directory", type=Path, required=True)
    worker(parser.parse_args())
