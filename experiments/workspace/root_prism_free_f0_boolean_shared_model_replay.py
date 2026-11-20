"""Independent exact checker for the complete Boolean shared-edge model.

The complete frozen parent bytes, every appended Boolean equation, and all
proof-bound prism/clique mappings are checked. No producer, allocation
helper, CpModel, or CpSolver is imported.
"""
import argparse
from collections import Counter
import gzip
import hashlib
from itertools import combinations
import json
from pathlib import Path
import resource
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
SECONDS = 120
OWNER_SECONDS = 135


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def value_sha(value):
    return sha(canonical(value))


def reference(path):
    with path.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    return {"path": str(path.relative_to(ROOT)), "sha256": digest}


def read(binding, raw=False):
    data = (ROOT / binding["path"]).read_bytes()
    assert sha(data) == binding["sha256"]
    if raw:
        return data
    return json.loads(gzip.decompress(data) if binding["path"].endswith(".gz") else data)


def write(path, value):
    raw = canonical(value) + b"\n"
    with path.open("xb") as stream:
        stream.write(raw)
    return reference(path)


def domain(saved):
    core = saved["component_core_rows"]
    assert len(core) == 21 and all(type(r) is int and 0 <= r < (1 << 21) for r in core)
    assert all(not (core[i] >> i & 1) for i in range(21))
    assert all((core[i] >> j & 1) == (core[j] >> i & 1) for i in range(21) for j in range(21))
    gram = [[12*int(i == j)+2-(core[i+3]&core[j+3]).bit_count()-((core[i+3]>>(j+3))&1) for j in range(18)] for i in range(18)]
    triples = []
    for h in combinations(range(18), 3):
        if any(all(i//6 == block for i in h) for block in range(3)):
            continue
        if any(gram[i][j] == 0 for i, j in combinations(h, 2)):
            continue
        if any(sum(int(i == j or ((core[i+3]>>(j+3))&1)) for j in h) > 2 for i in range(18)):
            continue
        triples.append(list(h))
    assert triples == saved["signature_domain"] and len(triples) == 480
    targets = [[2-int(i in h)-sum((core[i+3]>>(j+3))&1 for j in h) for i in range(18)] for h in triples]
    assert targets == saved["row_targets"] and all(sum(q) == 24 and all(v in (0,1,2) for v in q) for q in targets)
    sets = list(map(set, triples))
    edges, neighbors, incident = [], [[] for _ in triples], [[] for _ in triples]
    for a, b in combinations(range(480), 2):
        if len(sets[a]&sets[b]) > 1 or any(targets[a][i] == 0 for i in triples[b]) or any(targets[b][i] == 0 for i in triples[a]):
            continue
        e = len(edges)
        edges.append([a,b]); neighbors[a].append(b); neighbors[b].append(a)
        incident[a].append((b,e)); incident[b].append((a,e))
    assert len(edges) == 68394 and neighbors == saved["possible_neighbor_signature_ids"]
    return {"core":core,"triples":triples,"targets":targets,"gram":gram,"edges":edges,"incident":incident}


def core_actions(ctx, moves):
    core, triples, targets, edges = [ctx[k] for k in ("core","triples","targets","edges")]
    group = set(map(tuple,moves))
    assert len(moves) == len(group) == 12 and tuple(range(21)) in group
    assert all(tuple(g[h[i]] for i in range(21)) in group for g in moves for h in moves)
    lookup = {tuple(h):a for a,h in enumerate(triples)}
    edge_set = set(map(tuple,edges))
    output = []
    for move in moves:
        assert sorted(move) == list(range(21)) and set(move[:3]) == set(range(3))
        assert all((core[i]>>j&1) == (core[move[i]]>>move[j]&1) for i in range(21) for j in range(21))
        sites = [move[i+3]-3 for i in range(18)]
        image = [lookup[tuple(sorted(sites[i] for i in h))] for h in triples]
        assert sorted(image) == list(range(480))
        assert {tuple(sorted((image[a],image[b]))) for a,b in edges} == edge_set
        assert all(targets[image[a]][sites[i]] == targets[a][i] for a in range(480) for i in range(18))
        output.append((sites,image))
    return output


def literal_prism_zeros(ctx, census):
    core, triples, edges = [ctx[k] for k in ("core","triples","edges")]
    witnessed = {}
    for index,item in enumerate(census["literal_motif_witnesses"]):
        e = item["edge_id"]
        assert type(e) is int and 0 <= e < len(edges) and e not in witnessed and item["kind"] == "P"
        a,b = edges[e]
        assert item["pair"] == [a,b]
        rows = list(core)+[0,0]
        for vertex,signature in ((21,triples[a]),(22,triples[b])):
            for site in signature:
                rows[vertex] |= 1 << (site+3)
                rows[site+3] |= 1 << vertex
        rows[21] |= 1 << 22; rows[22] |= 1 << 21
        sites = item["sites"]
        assert len(sites) == len(set(sites)) == 6 and all(type(v) is int and 0 <= v < 23 for v in sites)
        left,right = sites[:3],sites[3:]
        assert all(rows[u]>>v&1 for side in (left,right) for u,v in combinations(side,2))
        assert all(sum(rows[u]>>v&1 for v in right) == 1 for u in left)
        assert all(sum(rows[v]>>u&1 for u in left) == 1 for v in right)
        witnessed[e] = index
    assert len(witnessed) == 1884
    return witnessed


def clique_buckets(ctx, zeros, record, actions, check):
    triples,targets,gram,edges,incident = [ctx[k] for k in ("triples","targets","gram","edges","incident")]
    pairs = list(combinations(range(18),2)); pair_index = {p:i for i,p in enumerate(pairs)}
    assert record["component_pairs"] == [list(p) for p in pairs]
    assert len(record["ledger"]) == 480*153 and len(record["rows"]) == 258 and len(record["row_transports"]) == 258
    buckets = {}
    for center in range(480):
        check()
        grouped = [[] for _ in pairs]
        for neighbor,e in incident[center]:
            for pair in combinations(triples[neighbor],2):
                grouped[pair_index[pair]].append([neighbor,e])
        for pi,(i,j) in enumerate(pairs):
            raw = grouped[pi]
            live = [[a,e] for a,e in raw if e not in zeros]
            if not live:
                reason = 0
            elif len(live) == 1:
                reason = 1
            elif gram[i][j] <= 1:
                reason = 2
            elif min(targets[center][i],targets[center][j]) <= 1:
                reason = 3
            else:
                reason = 4
                assert gram[i][j] == targets[center][i] == targets[center][j] == 2
            ordinal = center*153+pi
            saved = record["ledger"][ordinal]
            assert saved[:5] == [center,pi,len(raw),len(live),reason]
            if reason == 4:
                assert type(saved[5]) is int and 0 <= saved[5] < 258
                buckets[ordinal] = {"center":center,"pair":[i,j],"live":live,"proof_row":saved[5]}
            else:
                assert saved[5] == -1
    assert len(buckets) == 3096
    edge_lookup = {tuple(pair):e for e,pair in enumerate(edges)}
    coverage = {}
    for rid,row in enumerate(record["rows"]):
        center,pair,live = row["center"],row["core_pair"],row["live_neighbors_and_edge_ids"]
        ordinal = center*153+pair_index[tuple(pair)]
        assert row["first_bucket"] == ordinal
        assert buckets[ordinal] == {"center":center,"pair":pair,"live":live,"proof_row":rid}
        moved_indices = []
        for ai,(sites,image) in enumerate(actions):
            moved_pair = sorted(sites[i] for i in pair)
            moved_center = image[center]
            target = moved_center*153+pair_index[tuple(moved_pair)]
            moved_live = [[image[a],edge_lookup[tuple(sorted((moved_center,image[a])))]] for a,e in live]
            moved_live.sort(key=lambda item:item[1])
            assert buckets[target] == {"center":moved_center,"pair":moved_pair,"live":moved_live,"proof_row":rid}
            assert target not in coverage
            coverage[target] = {"proof_row":rid,"core_action_index":ai}
            moved_indices.append([ai,target])
        assert moved_indices == record["row_transports"][rid]
    assert set(coverage) == set(buckets)
    return [(ordinal,buckets[ordinal],coverage[ordinal]) for ordinal in sorted(buckets)]


def check_linear(actual, variables, coefficients, lower, upper):
    expected = type(actual)()
    expected.linear.vars.extend(variables)
    expected.linear.coeffs.extend(coefficients)
    expected.linear.domain.extend([lower,upper])
    assert actual.SerializeToString() == expected.SerializeToString()


def check_variable(actual, name, bounds):
    expected = type(actual)()
    expected.name = name
    expected.domain.extend(bounds)
    assert actual.SerializeToString() == expected.SerializeToString()


def inspect_base(model, parent, parent_raw, ctx, check):
    assert len(parent.variables) == 540 and len(parent.constraints) == 17162
    assert parent.SerializeToString() == parent_raw
    assert len(model.variables) == 68934 and len(model.constraints) == 168050
    retained = type(model)()
    retained.CopyFrom(model)
    del retained.variables[540:]; del retained.constraints[17162:]
    assert retained.SerializeToString() == parent_raw
    del retained
    assert {field.name for field,_ in model.ListFields()} <= {"name","variables","constraints"}
    assert all(list(parent.variables[a].domain) == [0,1] for a in range(480))
    edges,incident,triples,targets = [ctx[k] for k in ("edges","incident","triples","targets")]
    for e,(a,b) in enumerate(edges):
        if e%4096 == 0:
            check()
        check_variable(model.variables[540+e],"shared_edge_%03d_%03d"%(a,b),[0,1])
    cursor = 17162
    for e,(a,b) in enumerate(edges):
        if e%4096 == 0:
            check()
        for center in (a,b):
            check_linear(model.constraints[cursor],[center,540+e],[-1,1],-1,0)
            cursor += 1
    assert cursor == 153950
    for a in range(480):
        variables = [a]+[540+e for b,e in incident[a]]
        check_linear(model.constraints[cursor],variables,[-8]+[1]*(len(variables)-1),0,0)
        cursor += 1
    assert cursor == 154430
    empty = 0
    for a in range(480):
        check()
        for site in range(18):
            variables = [540+e for b,e in incident[a] if site in triples[b]]
            coefficients = [1]*len(variables)
            if targets[a][site]:
                variables = [a]+variables; coefficients = [-targets[a][site]]+coefficients
            empty += int(not variables)
            check_linear(model.constraints[cursor],variables,coefficients,0,0)
            cursor += 1
    assert cursor == 163070 and empty == 756
    return cursor


BASE_CONFIGURATION = {"path":"experiments/logs/root-prism-free/f0-boolean-shared-model-configuration01.json",
                      "sha256":"e3ec62ae3b9bb6d98170960c4ef24b4c18a0cea07dc0e53ee8301a29d343dba0"}
PARENT_CONTROLLER_SHA = "094c143d63011c0fee6dab95e2850634fd70fb1f7564b8c3e682cb02ef2f21c8"


def base_context():
    config = read(BASE_CONFIGURATION)
    assert config["schema"] == "conway99.f0.boolean-shared-model-configuration.v1"
    assert config["base_builder_sha256"] == "5a1e8026683a7782fce6ec2a2947748356ac9cd5adf32dd2a0663b0dd60bfca2"
    data = {}
    for name,binding in config["inputs"].items():
        if name in ("registry","replayed_registry","parent_model"):
            assert reference(ROOT/binding["path"]) == binding
        else:
            data[name] = read(binding)
    assert config["inputs"]["registry"]["sha256"] == config["inputs"]["replayed_registry"]["sha256"]
    run,owner,cold,cold_owner,iteration = [data[k] for k in ("parent_run","parent_owner","parent_cold","parent_cold_owner","parent_iteration")]
    for receipt,report,name in ((owner,run,"parent_run"),(cold_owner,cold,"parent_cold")):
        assert receipt["report_accepted"] and receipt["report_sha256"] == config["inputs"][name]["sha256"]
        assert receipt["source_sha256"] == PARENT_CONTROLLER_SHA and receipt["status"] == report["status"]
        assert receipt["deadline_overrun_seconds"] == 0 and receipt["supervision"]["child_reaped"] and receipt["supervision"]["returncode"] == 0
    assert run["status"] == "UNKNOWN_MASTER_NATIVE" and run["production_solve_calls"] == 2
    assert cold["status"] == "PASS_COMPLETE_CALLED_PREFIXES_AND_EXACT_CERTIFICATES"
    assert cold["run_result_sha256"] == config["inputs"]["parent_run"]["sha256"]
    assert cold["run_owner_sha256"] == config["inputs"]["parent_owner"]["sha256"]
    assert cold["run_owner_accepted"] and not cold["run_outcome_relabelled"]
    assert not run["whole_component_excluded"] and not run["graph_constructed"]
    assert iteration["index"] == 1 and iteration["native_status"] == "UNKNOWN" and not iteration["direct_checked"]
    assert iteration["registry_rows"] == run["final_registry_rows"] == cold["final_replayed_registry_rows"] == 12481
    assert iteration["registry_sha256"] == run["final_registry_sha256"] == cold["final_replayed_registry_sha256"] == config["parent_registry_value_sha256"]
    assert iteration["prefix"]["archive_sha256"] == config["inputs"]["parent_model"]["sha256"]
    raw = gzip.decompress(read(config["inputs"]["parent_model"],raw=True))
    assert len(raw) == iteration["prefix"]["raw_bytes"] == 24078662
    assert sha(raw) == iteration["prefix"]["raw_sha256"] == config["parent_model_raw_sha256"] == "fcc1f092f60338a791bf497bb8c9e76200d51260133aa2bc4ef1274bd1ecb9ec"
    assert iteration["prefix"]["rows"] == 17162
    assert run["definition"]["shared_definition"]["inputs"]["domain"] == [config["inputs"]["domain"]["path"],config["inputs"]["domain"]["sha256"]]
    return config,raw,domain(data["domain"])


def controls():
    from ortools.sat import cp_model_pb2 as pb
    row = pb.ConstraintProto()
    row.linear.vars.extend([0,2]); row.linear.coeffs.extend([-1,1]); row.linear.domain.extend([-1,0])
    check_linear(row,[0,2],[-1,1],-1,0)
    for x in (0,1):
        for y in (0,1):
            assert (-1 <= y-x <= 0) == (y <= x)
    mutations = []
    for kind in ("variable","coefficient","lower","upper","enforcement"):
        changed = pb.ConstraintProto(); changed.CopyFrom(row)
        if kind == "variable": changed.linear.vars[1] = 3
        elif kind == "coefficient": changed.linear.coeffs[0] = 1
        elif kind == "lower": changed.linear.domain[0] = 0
        elif kind == "upper": changed.linear.domain[1] = 1
        else: changed.enforcement_literal.append(0)
        try:
            check_linear(changed,[0,2],[-1,1],-1,0)
        except AssertionError:
            mutations.append(kind)
        else:
            raise AssertionError("mutated row escaped the exact checker")
    empty = pb.ConstraintProto(); empty.linear.domain.extend([0,0])
    check_linear(empty,[],[],0,0)
    big = (1 << 54)+3
    large = pb.ConstraintProto(); large.linear.vars.append(0); large.linear.coeffs.append(big); large.linear.domain.extend([-big,big])
    check_linear(large,[0],[big],-big,big)
    variable = pb.IntegerVariableProto(); variable.name = "edge"; variable.domain.extend([0,1])
    check_variable(variable,"edge",[0,1])
    variable.domain[1] = 2
    try:
        check_variable(variable,"edge",[0,1])
    except AssertionError:
        mutations.append("variable_domain")
    else:
        raise AssertionError("changed Boolean domain escaped the checker")
    assert "ortools.sat.python.cp_model" not in sys.modules
    return {"status":"PASS_BOOLEAN_SHARED_INDEPENDENT_PROTOBUF_CONTROLS",
            "mutation_rejections":mutations,"Boolean_endpoint_truth_assignments":4,
            "empty_equation_checked":True,"integer_above_binary64_exact_range":big,
            "producer_imports":0,"CpModel_constructed":False,"CpSolver_constructed":False,"optimizer_calls":0}


OVERLAY_CONFIGURATION = {"path":"experiments/logs/root-prism-free/f0-boolean-shared-model-configuration02.json",
                         "sha256":"7b35ad5aa8b66323b8cd5a30fc6f1265d56d59b2477426b9e1794b3f7aa82a9a"}
PREPARATION = "experiments/logs/root-prism-free/f0-boolean-shared-native-preparation01/"
PREP_BINDINGS = {
    "report":{"path":PREPARATION+"report.json","sha256":"ecdc3405f803d8e5815dba2555f4c9884018de69aff0b756a132e26c0a0a8471"},
    "owner":{"path":PREPARATION+"owner.json","sha256":"1235205d26e3df428e83b666a5f7145db6c66f8c40677ec41a0ba9a86e601b5f"},
    "model":{"path":PREPARATION+"model.pb.gz","sha256":"5d2e705f10f5a04f593a486ca271f0a6e06dc981c95ffc977054c6fdce906036"},
    "overlay":{"path":PREPARATION+"overlay-proof.json.gz","sha256":"4f75f8480ac0e73572a19affc9f17df9f54a9b3aefbeef62832c13bffb8fc183"},
}


def run(output):
    started = time.monotonic()
    def check():
        if time.monotonic()-started >= SECONDS:
            raise TimeoutError("complete Boolean model independent cold deadline")
    cfg = read(OVERLAY_CONFIGURATION)
    base_cfg,parent_raw,ctx = base_context()
    assert all(cfg[k] == value for k,value in base_cfg.items())
    assert cfg["active_builder_sha256"] == "062737362b889823c8fd2c068bcdd08feac2737214cc7bbd1f3802ec31ea6c71"
    for path,expected in (("experiments/workspace/root_prism_free_f0_boolean_shared_model.py",cfg["base_builder_sha256"]),
                          ("experiments/workspace/root_prism_free_f0_boolean_shared_model_v2.py",cfg["active_builder_sha256"])):
        assert reference(ROOT/path)["sha256"] == expected
    assert cfg["transport_controls"]["configuration"] == BASE_CONFIGURATION
    controls_report = read(cfg["transport_controls"]["report"])
    controls_owner = read(cfg["transport_controls"]["owner"])
    assert controls_owner["report_accepted"] and controls_owner["report_sha256"] == cfg["transport_controls"]["report"]["sha256"]
    assert controls_owner["source_sha256"] == controls_report["source_sha256"] == cfg["base_builder_sha256"]
    assert controls_report["configuration_sha256"] == BASE_CONFIGURATION["sha256"]
    assert controls_owner["status"] == controls_report["status"] == "PASS_PUBLIC_NATIVE_TEXT_TRANSPORT_EXACT_BYTES_AND_INVALID_INDEX_REJECTION"
    assert controls_owner["deadline_overrun_seconds"] == 0 and controls_owner["supervision"]["child_reaped"] and controls_owner["supervision"]["returncode"] == 0
    report,owner = read(PREP_BINDINGS["report"]),read(PREP_BINDINGS["owner"])
    assert owner["report_accepted"] and owner["report_sha256"] == PREP_BINDINGS["report"]["sha256"]
    assert owner["status"] == report["status"] == "PASS_COMPLETE_BOOLEAN_SHARED_MODEL_NATIVE_PREPARATION"
    assert owner["source_sha256"] == report["source_sha256"] == cfg["active_builder_sha256"]
    assert owner["configuration_sha256"] == report["configuration_sha256"] == OVERLAY_CONFIGURATION["sha256"]
    assert owner["deadline_overrun_seconds"] == 0 and owner["supervision"]["child_reaped"] and owner["supervision"]["returncode"] == 0
    assert not report["CpSolver_constructed"] and report["optimizer_calls"] == 0 and not report["native_query_run"]
    assert report["stages"]["model_phase_seconds"] <= 90 and report["seconds"] <= 120
    archive = read(PREP_BINDINGS["model"],raw=True)
    raw = gzip.decompress(archive)
    assert len(archive) == report["model"]["archive_bytes"] and sha(archive) == report["model"]["archive_sha256"]
    assert len(raw) == report["model"]["raw_bytes"] == report["native_transport"]["native_raw_bytes"] == 33451907
    assert sha(raw) == report["model"]["raw_sha256"] == report["native_transport"]["native_raw_sha256"] == "4505234d13039159c3191918f7db729819ad6ed25f46e538d91975466d660e83"
    assert (ROOT/PREPARATION/"model.pb").read_bytes() == raw
    assert report["native_transport"]["public_parse_return"] is True and report["native_transport"]["native_validation"] == ""
    assert report["native_transport"]["complete_byte_comparison"] and not report["native_transport"]["CpSolver_constructed"]
    overlay_archive = read(PREP_BINDINGS["overlay"],raw=True)
    overlay_raw = gzip.decompress(overlay_archive)
    assert len(overlay_archive) == report["overlay"]["archive_bytes"] and sha(overlay_archive) == report["overlay"]["archive_sha256"]
    assert len(overlay_raw) == report["overlay"]["raw_bytes"] and sha(overlay_raw) == report["overlay"]["raw_sha256"]
    overlay = json.loads(overlay_raw)
    assert canonical(overlay) == overlay_raw
    loaded = {name:read(binding) for name,binding in cfg["overlay_inputs"].items()}
    motifs,motif_cold,cliques,clique_cold,actions_record = [loaded[k] for k in ("motifs","motif_cold","cliques","clique_cold","actions")]
    for name,record in (("motifs",motifs),("cliques",cliques)):
        source = cfg["proof_sources"][name]
        assert reference(ROOT/source["path"]) == source and record["source_sha256"] == source["sha256"]
    assert motif_cold["status"] == "PASS: complete edge-motif census cold replayed"
    assert motif_cold["record_sha256"] == cfg["overlay_inputs"]["motifs"]["sha256"]
    assert motif_cold["raw_record_sha256"] == value_sha(motifs) and motif_cold["source_sha256"] == motifs["source_sha256"]
    assert clique_cold["status"] == "PASS: common-core-pair edge-clique replay"
    assert clique_cold["record_file_sha256"] == cfg["overlay_inputs"]["cliques"]["sha256"]
    assert clique_cold["record_raw_sha256"] == value_sha(cliques) and clique_cold["source_sha256"] == cliques["source_sha256"]
    assert cliques["inputs"]["zeros"] == cfg["overlay_inputs"]["motifs"]
    assert cliques["inputs"]["actions"] == motifs["inputs"]["actions"] == cfg["overlay_inputs"]["actions"]
    assert motifs["status"] == "COMPLETE_EXACT_VISIBLE_EDGE_MOTIF_CENSUS" and motifs["all68394_eligible_edges_covered"] and motifs["full480_signature_domain_retained"]
    assert cliques["status"] == "COMPLETE_CORE_PAIR_EDGE_CLIQUE_CUTS" and cliques["all480_signatures_and68394_eligible_edges_retained"]
    assert all(record["optimizer_calls"] == 0 for record in (motifs,motif_cold,cliques,clique_cold))
    from ortools.sat import cp_model_pb2 as pb
    parent,model = pb.CpModelProto(),pb.CpModelProto()
    parent.ParseFromString(parent_raw); model.ParseFromString(raw)
    assert model.SerializeToString() == raw
    cursor = inspect_base(model,parent,parent_raw,ctx,check)
    base_model = pb.CpModelProto(); base_model.CopyFrom(model); del base_model.constraints[163070:]
    base_raw_sha = sha(base_model.SerializeToString()); del base_model
    assert base_raw_sha == report["inventory"]["complete_base_raw_sha256"]
    witnessed = literal_prism_zeros(ctx,motifs)
    assert motif_cold["literal_motif_witnesses"] == len(witnessed) == 1884
    zero_rows = []
    for e in sorted(witnessed):
        wi = witnessed[e]
        zero_rows.append({"edge_id":e,"variable_index":540+e,"witness_index":wi,
                          "witness":motifs["literal_motif_witnesses"][wi],"native_row_index":cursor})
        check_linear(model.constraints[cursor],[540+e],[1],0,0)
        cursor += 1
    assert cursor == 164954
    moves = actions_record["domain"]["reconstructed21_core_actions"]
    actions = core_actions(ctx,moves)
    assert value_sha(ctx["triples"]) == actions_record["domain"]["triples_sha256"]
    assert value_sha(ctx["edges"]) == actions_record["domain"]["edges_sha256"]
    assert value_sha([image for sites,image in actions]) == actions_record["domain"]["selector_actions_sha256"]
    assert cliques["core_pair_quotas"] == [ctx["gram"][i][j] for i,j in combinations(range(18),2)]
    assert cliques["ledger_fields"] == ["center","pair_index","raw_size","live_size","disposition","row_id"]
    buckets = clique_buckets(ctx,witnessed,cliques,actions,check)
    clique_rows = []
    for ordinal,item,origin in buckets:
        center,live = item["center"],item["live"]
        clique_rows.append({"native_row_index":cursor,"ledger_index":ordinal,"center":center,"core_pair":item["pair"],
                            "live_neighbors_and_edge_ids":live,"original_quotient_row_id":origin["proof_row"],
                            "original_action_index":origin["core_action_index"]})
        variables = [center]+[540+e for a,e in live]
        check_linear(model.constraints[cursor],variables,[-1]+[1]*len(live),-1,0)
        cursor += 1
    assert cursor == 168050
    counts = Counter()
    for center,pi,nraw,nlive,reason,rid in cliques["ledger"]:
        counts["disposition_%d"%reason] += 1
        counts["raw_edge_memberships"] += nraw
        counts["known_zero_edge_memberships_removed"] += nraw-nlive
        if reason == 4:
            counts["retained_literal_edge_memberships"] += nlive
    expected_overlay = {"schema":"conway99.f0.boolean-shared-overlay-proof.v1",
        "status":"COMPLETE_LITERAL_PRISM_ZEROS_AND_CORE_PAIR_CLIQUES",
        "inputs":cfg["overlay_inputs"],"proof_sources":cfg["proof_sources"],"zero_rows":zero_rows,"clique_rows":clique_rows,
        "complete_old_ledger_value_sha256":value_sha(cliques["ledger"]),"complete_edge_order_sha256":value_sha(ctx["edges"]),
        "counts":dict(counts),"all_73440_buckets_checked":True,"complete_258_by_12_transport_mapping_checked":True,
        "quotient_variable_ids_used_in_native_rows":False,"all_original_edge_variables_retained":True,"optimizer_calls":0}
    assert overlay == expected_overlay
    expected_inventory = {"variables":68934,"original_variables":540,"Boolean_edges":68394,"rows":168050,
        "complete_parent_rows":17162,"parent_selector_registry_rows":12481,"endpoint_activation_rows":136788,
        "degree_rows":480,"mixed_rows":8640,"explicit_empty_mixed_rows":756,"complete_parent_bytes_preserved_as_submodel":True,
        "signature_domain_sha256":value_sha(ctx["triples"]),"edge_domain_sha256":value_sha(ctx["edges"]),
        "targets_sha256":value_sha(ctx["targets"]),"selector_fix_or_graph_symmetry":False,"objective_hint_or_assumption":False,
        "CpSolver_constructed":False,"optimizer_calls":0,"prism_zero_rows":1884,"literal_core_pair_clique_rows":3096,
        "complete_base_raw_sha256":base_raw_sha,"complete_base_rows_preserved_as_submodel":True}
    assert expected_inventory == report["inventory"]
    assert "ortools.sat.python.cp_model" not in sys.modules and "highspy" not in sys.modules
    check()
    result = {"status":"PASS_INDEPENDENT_COMPLETE_BOOLEAN_SHARED_MODEL",
        "source":reference(Path(__file__).resolve()),"configuration":OVERLAY_CONFIGURATION,"preparation_inputs":PREP_BINDINGS,
        "native_raw_model_sha256":sha(raw),"native_raw_model_bytes":len(raw),"exact_parent_raw_sha256":sha(parent_raw),
        "inventory":expected_inventory,"all_appended_rows_compared_exactly":150888,
        "all68394_Boolean_variable_domains_and_names_checked":True,"complete_parent_bytes_checked":True,
        "all1884_literal_prism_witnesses_checked":True,"all73440_core_pair_buckets_reconstructed":True,
        "complete258_by12_clique_provenance_checked":True,"overlay_raw_sha256":sha(overlay_raw),
        "protobuf_decoder_only":True,"producer_imports":0,"CpModel_constructed":False,"CpSolver_constructed":False,
        "optimizer_calls":0,"native_query_run":False,"whole_component_excluded":False,"graph_constructed":False,
        "all_exterior_pair_common_neighbor_caps_claimed":False,
        "seconds":time.monotonic()-started,"peak_rss_KiB":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    write(output,result)
    return result


if __name__ == "__main__":
    assert __debug__
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode",choices=("controls","run"))
    parser.add_argument("--output",type=Path,required=True)
    args = parser.parse_args()
    if args.mode == "controls":
        result = controls(); result["source"] = reference(Path(__file__).resolve()); write(args.output.resolve(),result)
    else:
        result = run(args.output.resolve())
    print(json.dumps({"status":result["status"],"seconds":result.get("seconds")}),flush=True)
