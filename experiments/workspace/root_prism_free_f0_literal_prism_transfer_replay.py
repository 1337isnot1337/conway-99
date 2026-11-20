"""Independent complete literal-prism transfer replay; no producer or solver.

Reconstruct every saved six-site graph, verify all current-model implication
receipts, and recover the complete sorted proposed Boolean row family.
The accepted old censuses supply finite-family coverage, not new enumeration.
"""
import argparse
from collections import Counter
import gzip
import hashlib
from itertools import combinations, product
import json
from pathlib import Path
import resource
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
CONFIG = {"path":"experiments/logs/root-prism-free/f0-boolean-shared-prism-transfer-inventory-configuration01.json",
          "sha256":"2df2acdb2421c487af82821b1ae00ac7a1dbe50a650dea62c439bf0ef5f35586"}
PRODUCER_SHA = "ca8b9ab7f6593c93ecdcf23ab700f34619acb53752a330f11358192a1a24b54c"
COLD_SECONDS, OWNER_SECONDS = 90, 105
PASS = "PASS_COMPLETE_LITERAL_TRANSFER_INVENTORY_AWAITING_INDEPENDENT_REPLAY"
REASONS = {"0":"existing_edge_zero", "1":"existing_quota_one_mixed_row",
           "2":"inherited_zero_selector_pair", "3":"existing_core_pair_clique",
           "4":"not_proved_redundant_by_audited_criteria"}


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(",",":"),allow_nan=False).encode()


def value_sha(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def reference(path):
    path = Path(path).resolve()
    assert path.is_relative_to(ROOT)
    with path.open("rb") as f:
        digest = hashlib.file_digest(f,"sha256").hexdigest()
    return {"path":str(path.relative_to(ROOT)),"sha256":digest,"bytes":path.stat().st_size}


def raw_ref(ref):
    path = ROOT/ref["path"]
    actual = reference(path)
    assert all(actual[k] == v for k,v in ref.items())
    return path.read_bytes()


def read(ref):
    b = raw_ref(ref)
    return json.loads(gzip.decompress(b) if ref["path"].endswith(".gz") else b)


def write(path,value):
    with path.open("xb") as f:
        f.write(canonical(value)+b"\n")


def check_time(deadline):
    if time.monotonic() >= deadline:
        raise TimeoutError("independent complete prism-transfer replay deadline")


def is_prism(rows):
    if len(rows) != 6 or any(type(r) is not int or r < 0 or r >= 64 for r in rows):
        return False
    if any(r.bit_count() != 3 or r & (1<<i) for i,r in enumerate(rows)):
        return False
    if any(((rows[i]>>j)&1) != ((rows[j]>>i)&1) for i in range(6) for j in range(6)):
        return False
    triangles = [set(t) for t in combinations(range(6),3)
                 if all(rows[i] & (1<<j) for i,j in combinations(t,2))]
    return len(triangles) == 2 and not triangles[0] & triangles[1]


def six_rows(core,signatures,outside,core_sites,exterior_edges):
    a,b,c = outside
    u,v,w = core_sites
    assert len(set(outside)) == len(set(core_sites)) == 3
    assert all(0 <= z < 480 for z in outside) and all(3 <= z < 21 for z in core_sites)
    nodes = [(1,a),(1,b),(0,u),(1,c),(0,v),(0,w)]
    edge_set = {tuple(sorted(e)) for e in exterior_edges}
    def adjacent(p,q):
        if p[0] == q[0] == 0:
            return (core[p[1]] >> q[1]) & 1
        if p[0] == q[0] == 1:
            return int(tuple(sorted((p[1],q[1]))) in edge_set)
        exterior,site = (p[1],q[1]) if p[0] else (q[1],p[1])
        return int(site-3 in signatures[exterior])
    return [sum(adjacent(p,q)<<j for j,q in enumerate(nodes)) for p in nodes]


def controls():
    count = 0
    for mask in range(512):
        rows = [0]*6
        for triangle in ((0,1,2),(3,4,5)):
            for i,j in combinations(triangle,2):
                rows[i] |= 1<<j; rows[j] |= 1<<i
        for i in range(3):
            for j in range(3):
                if mask & (1<<(3*i+j)):
                    rows[i] |= 1<<(j+3); rows[j+3] |= 1<<i
        expected = all(sum((mask>>(3*i+j))&1 for j in range(3)) == 1 for i in range(3)) and all(sum((mask>>(3*i+j))&1 for i in range(3)) == 1 for j in range(3))
        assert is_prism(rows) == expected
        count += int(expected)
    assert count == 6
    one_count = path_count = 0
    for a,b,c,u,v in product((0,1),repeat=5):
        if u <= a and a+c <= 1:
            assert u+c <= 1; one_count += 1
        if u <= min(a,b) and v <= min(c,b) and a+c <= 1:
            assert u+v <= b; path_count += 1
    assert (one_count,path_count) == (16,8)
    return {"status":"PASS_INDEPENDENT_PRISM_GRAPH_AND_BOOLEAN_RECEIPT_CONTROLS",
            "all_two_triangle_cross_graphs_checked":512,"induced_prisms":count,
            "one_edge_assignments":one_count,"path_assignments":path_count,
            "producer_imports":0,"native_model_builds":0,"optimizer_calls":0}


def replay(directory,report_sha,owner_sha,output):
    started = time.monotonic(); deadline = started+COLD_SECONDS
    cfg = read(CONFIG)
    assert cfg["source_sha256"] == PRODUCER_SHA
    assert (cfg["check_seconds"],cfg["owner_seconds"]) == (30,45)
    for ref in cfg["sources"].values():
        raw_ref(ref)
    inputs = {k:read(v) for k,v in cfg["inputs"].items() if k != "model"}
    run_report_ref = {"path":str((directory/"report.json").relative_to(ROOT)),"sha256":report_sha}
    run_owner_ref = {"path":str((directory/"owner.json").relative_to(ROOT)),"sha256":owner_sha}
    report,owner = read(run_report_ref),read(run_owner_ref)
    assert report["status"] == owner["status"] == PASS and owner["report_accepted"] is True
    assert report["source_sha256"] == owner["source_sha256"] == PRODUCER_SHA
    assert report["configuration_sha256"] == owner["configuration_sha256"] == CONFIG["sha256"]
    assert owner["report_sha256"] == report_sha and owner["maximum_seconds"] == 45
    sup = owner["supervision"]
    assert sup["status"] == "CHILD_EXITED" and sup["returncode"] == 0
    assert sup["child_reaped"] and sup["owned_process_group_stopped"] and owner["deadline_overrun_seconds"] == 0
    assert report["check_phase_seconds"] <= 30 and report["seconds"] <= 45
    archive_ref = reference(directory/"complete-inventory.json.gz")
    packed = raw_ref(archive_ref); raw = gzip.decompress(packed)
    assert (archive_ref["sha256"],len(packed),hashlib.sha256(raw).hexdigest(),len(raw)) == tuple(report["inventory"][k] for k in ("archive_sha256","archive_bytes","raw_sha256","raw_bytes"))
    saved = json.loads(raw); assert canonical(saved) == raw
    assert saved["schema"] == "conway99.f0.boolean-prism-transfer-inventory.v1"
    assert saved["inputs"] == cfg["inputs"] and saved["source_sha256"] == PRODUCER_SHA
    assert saved["configuration_sha256"] == CONFIG["sha256"] and saved["model_raw_sha256"] == cfg["model_raw_sha256"]
    assert saved["reasons"] == REASONS
    assert saved["one_edge_ledger_fields"] == ["edge_id","third_selector","old_witness_id","reason","actual_native_premise_rows"]
    assert saved["path_ledger_fields"] == ["center","edge_min","edge_max","old_path_id","reason","actual_native_premise_rows"]
    assert saved["proposed_one_edge_fields"] == ["edge_id","third_selector","old_witness_id"]
    assert saved["proposed_path_fields"] == ["center","edge_min","edge_max","old_path_id"]
    assert saved["one_edge_row_definition"] == "x_third+y_edge<=1"
    assert saved["path_row_definition"] == "y_edge_min+y_edge_max-x_center<=0"
    assert saved["proposed_order"] == "one-edge keys sorted by edge/third, then path keys sorted by center/edge-min/edge-max"
    assert report["controls"] == {"status":"PASS_BINARY_ZERO_PAIR_IMPLICATION_CONTROLS","one_edge_assignments":16,"path_assignments":8,"center_Boolean_domain_required_for_path_implication":True}
    cold,old_owner = inputs["model_cold"],inputs["model_cold_owner"]
    assert cold["status"] == "PASS_INDEPENDENT_COMPLETE_BOOLEAN_SHARED_MODEL"
    assert old_owner["status"] == "OWNED_COMPLETE_BOOLEAN_SHARED_MODEL_COLD_ACCEPTED" and old_owner["report_accepted"]
    assert old_owner["report"] == cfg["inputs"]["model_cold"]
    assert cold["source"] == old_owner["source"] == cfg["sources"]["model_cold"]
    assert old_owner["supervision"]["exit_code"] == 0 and old_owner["supervision"]["child_reaped"] and not old_owner["supervision"]["hard_timeout"]
    assert cold["preparation_inputs"]["model"] == cfg["inputs"]["model"] and cold["preparation_inputs"]["overlay"] == cfg["inputs"]["overlay"]
    from ortools.sat import cp_model_pb2 as pb
    raw_model = gzip.decompress(raw_ref(cfg["inputs"]["model"]))
    assert len(raw_model) == 33451907 and hashlib.sha256(raw_model).hexdigest() == cfg["model_raw_sha256"] == cold["native_raw_model_sha256"]
    model = pb.CpModelProto(); model.ParseFromString(raw_model)
    assert model.SerializeToString() == raw_model and (len(model.variables),len(model.constraints)) == (68934,168050)
    del raw_model,raw,packed
    domain,plan,overlay = (inputs[k] for k in ("domain","literal_plan","overlay"))
    hs,core = domain["signature_domain"],domain["component_core_rows"]
    assert hs == plan["signature_domain"] and core == plan["core_rows"]
    assert len(hs) == 480 and len(core) == 21
    hsets = list(map(set,hs)); targets = [[2-int(i in h)-sum((core[i+3]>>(j+3))&1 for j in h) for i in range(18)] for h in hsets]
    assert targets == domain["row_targets"]
    neighbors = domain["possible_neighbor_signature_ids"]
    assert len(neighbors) == 480 and all(ns == sorted(set(ns)) and a not in ns for a,ns in enumerate(neighbors))
    edges = [(a,b) for a,ns in enumerate(neighbors) for b in ns if a < b]
    assert len(edges) == 68394 and all(a in neighbors[b] for a,b in edges)
    edge_ids = {e:k for k,e in enumerate(edges)}
    assert value_sha([list(e) for e in edges]) == cold["inventory"]["edge_domain_sha256"]
    assert value_sha(hs) == cold["inventory"]["signature_domain_sha256"] and value_sha(targets) == cold["inventory"]["targets_sha256"]
    assert all(list(model.variables[a].domain) == [0,1] for a in range(480))
    assert all(list(model.variables[540+e].domain) == [0,1] and model.variables[540+e].name == "shared_edge_%03d_%03d" % pair for e,pair in enumerate(edges))
    native_checked,activation_checked,mixed_checked = set(),set(),set()
    def check_row(index,terms,bounds):
        assert type(index) is int and 0 <= index < 168050
        row = model.constraints[index]
        assert row.WhichOneof("constraint") == "linear" and not row.enforcement_literal
        assert list(row.linear.vars) == [i for i,c in terms] and list(row.linear.coeffs) == [c for i,c in terms]
        assert list(row.linear.domain) == bounds
        native_checked.add(index)
    def activation(e,v):
        assert v in edges[e]
        index = 17162+2*e+(v == edges[e][1])
        check_row(index,[[v,-1],[540+e,1]],[-1,0]); activation_checked.add(index)
        return index
    forbidden = {}
    for rid,row in enumerate(plan["original_selector_equalities"]):
        if row["quota"] == 1:
            index = plan["original_to_native_rows"][rid]
            check_row(index,[[a,1] for a in row["support"]],[1,1])
            for a,b in combinations(row["support"],2):
                assert a < b and (a,b) not in forbidden
                forbidden[a,b] = {"pair_id":a*(959-a)//2+b-a-1,"pair":[a,b],"premise":"quota-one Gram equality","original_row_id":rid,"native_row_index":index}
    assert len(forbidden) == 4320
    for mid,(a,b) in enumerate(plan["motif_pairs"]):
        index = plan["motif_to_native_rows"][mid]; check_row(index,[[a,1],[b,1]],[0,1])
        assert a < b and (a,b) not in forbidden
        forbidden[a,b] = {"pair_id":a*(959-a)//2+b-a-1,"pair":[a,b],"premise":"explicit motif conflict","motif_id":mid,"native_row_index":index}
    receipts = [forbidden[p] for p in sorted(forbidden)]
    assert len(receipts) == 4410 and receipts == saved["zero_pair_native_receipts"]
    assert [{k:v for k,v in p.items() if k != "native_row_index"} for p in receipts] == plan["zero_pair_implications"]
    zeros,cliques = {},{}
    for row in overlay["zero_rows"]:
        e,index = row["edge_id"],row["native_row_index"]
        assert e not in zeros; check_row(index,[[540+e,1]],[0,0]); zeros[e] = index
    for row in overlay["clique_rows"]:
        b,index = row["center"],row["native_row_index"]
        live = row["live_neighbors_and_edge_ids"]
        assert all(edges[e] == tuple(sorted((a,b))) for a,e in live)
        check_row(index,[[b,-1]]+[[540+e,1] for a,e in live],[-1,0])
        key = (b,tuple(row["core_pair"])); assert key not in cliques
        assert all(set(key[1]) <= hsets[a] for a,e in live)
        cliques[key] = (index,{e for a,e in live})
    assert len(zeros) == 1884 and len(cliques) == 3096
    def mixed(b,site,e1,e2):
        index = 154430+18*b+site
        expected = [[b,-1]]+[[540+edge_ids[tuple(sorted((b,a)))],1] for a in neighbors[b] if site in hsets[a]]
        expected.sort()
        check_row(index,expected,[0,0]); mixed_checked.add(index)
        assert targets[b][site] == 1 and [540+e1,1] in expected and [540+e2,1] in expected
        return index
    one,paths = inputs["one_edge"],inputs["paths"]
    for name,obj,status in (("one_edge",one,"PASS: three-vertex prism cuts cold replayed"),("paths",paths,"PASS: complete two-edge prism cuts cold replayed")):
        old_cold = inputs[name+"_cold"]
        assert old_cold["status"] == status and old_cold["record_file_sha256"] == cfg["inputs"][name]["sha256"]
        assert old_cold["record_raw_sha256"] == value_sha(obj)
        assert old_cold["source_sha256"] == obj["source_sha256"] == cfg["sources"][name]["sha256"]
    one_ledger,one_proposed,one_counts,keys = [],[],Counter(),set()
    for wid,w in enumerate(one["literal_prism_witnesses"]):
        e,c = w["edge_id"],w["third_selector"]; a,b = edges[e]
        assert w["exterior_edge"] == [a,b] and len({a,b,c}) == 3
        sites = w["sites"]; assert len(sites) == 6 and sites[0:2] == [21,22] and sites[3] == 23
        small = six_rows(core,hsets,(a,b,c),(sites[2],sites[4],sites[5]),((a,b),))
        assert small == w["induced_rows"] and is_prism(small)
        assert len(hsets[a]&hsets[c]) == len(hsets[b]&hsets[c]) == 2
        assert (e,c) not in keys; keys.add((e,c))
        options = [forbidden[p] for v in (a,b) if (p:=tuple(sorted((v,c)))) in forbidden]
        if e in zeros: reason,premises = 0,[zeros[e]]
        elif options:
            proof = min(options,key=lambda p:p["pair_id"])
            endpoint = next(v for v in (a,b) if v in proof["pair"])
            reason,premises = 2,[proof["native_row_index"],activation(e,endpoint)]
        else:
            reason,premises = 4,[]; one_proposed.append([e,c,wid])
        one_ledger.append([e,c,wid,reason,premises]); one_counts[str(reason)] += 1
    assert len(one_ledger) == 9360 and one_ledger == saved["one_edge_ledger"]
    check_time(deadline)
    assert is_prism(paths["literal_prism_rows"])
    origins = [[] for _ in paths["paths"]]; witness_keys = set()
    for wid,w in enumerate(paths["literal_witnesses"]):
        a,b,c,x,y,z,e1,e2,old_reason,pid,rid,quota,zero = w
        assert tuple(w[:6]) not in witness_keys; witness_keys.add(tuple(w[:6]))
        assert edges[e1] == tuple(sorted((a,b))) and edges[e2] == tuple(sorted((b,c)))
        actual = six_rows(core,hsets,(a,b,c),(x+3,y+3,z+3),((a,b),(b,c)))
        assert actual == paths["literal_prism_rows"]
        assert z in hsets[a]&hsets[c] and b not in (a,c)
        old = paths["paths"][pid]
        assert old[:3] == [b,min(a,c),max(a,c)] and old[5:] == [old_reason,rid,quota,zero]
        origins[pid].append(wid)
        if wid % 4096 == 0: check_time(deadline)
    assert len(witness_keys) == 107520 and len(origins) == 107418 and origins == saved["complete_path_witness_origins"]
    path_ledger,path_proposed,path_counts,keys = [],[],Counter(),set()
    for pid,old in enumerate(paths["paths"]):
        b,a,c,first,multiplicity,old_reason,old_row,quota,zero = old
        assert a < c and origins[pid] and first == origins[pid][0] and multiplicity == len(origins[pid])
        e1,e2 = sorted(edge_ids[tuple(sorted((v,b)))] for v in (a,c))
        assert (b,e1,e2) not in keys; keys.add((b,e1,e2))
        sites = sorted(hsets[a]&hsets[c]); quota_sites = [s for s in sites if targets[b][s] == 1]
        covers = [cliques[b,p] for p in combinations(sites,2) if (b,p) in cliques and {e1,e2} <= cliques[b,p][1]]
        assert len(covers) <= 1
        if e1 in zeros or e2 in zeros:
            zedge = min(e for e in (e1,e2) if e in zeros); other = e2 if zedge == e1 else e1
            reason,premises = 0,[zeros[zedge],activation(other,b)]
            assert old_reason == 0 and zero in (e1,e2) and zero in zeros
        elif quota_sites:
            reason,premises = 1,[mixed(b,quota_sites[0],e1,e2)]
            assert old_reason == 1 and quota in quota_sites
        elif (a,c) in forbidden:
            reason,premises = 2,[forbidden[a,c]["native_row_index"]]+[activation(e,v) for e in (e1,e2) for v in edges[e]]
            assert old_reason == 2
        elif covers:
            reason,premises = 3,[covers[0][0]]; assert old_reason == 2
        else:
            reason,premises = 4,[]; assert old_reason == 2
            path_proposed.append([b,e1,e2,pid])
        path_ledger.append([b,e1,e2,pid,reason,premises]); path_counts[str(reason)] += 1
        if pid % 4096 == 0: check_time(deadline)
    assert path_ledger == saved["path_ledger"]
    action_data = paths["actual_core_action_verification"]
    moves,actions = action_data["core_actions"],action_data["selector_actions"]
    assert len(moves) == len(actions) == 12
    for move,g in zip(moves,actions):
        assert sorted(move) == list(range(21)) and sorted(g) == list(range(480))
        assert all(((core[i]>>j)&1) == ((core[move[i]]>>move[j])&1) for i in range(21) for j in range(21))
        assert all(sorted(move[j+3]-3 for j in h) == hs[g[a]] for a,h in enumerate(hs))
    transported = []
    for rid,t in enumerate(paths["quotient_row_transport_witnesses"]):
        first = paths["literal_witnesses"][paths["rows"][rid]["first_literal_witness"]]
        assert t["row_id"] == rid and sorted(a for a,w in t["literal_witness_transports"]) == list(range(12))
        a,b,c,x,y,z = first[:6]
        for action,wid in t["literal_witness_transports"]:
            move,g = moves[action],actions[action]; w = paths["literal_witnesses"][wid]
            assert w[:6] == [g[a],g[b],g[c],move[x+3]-3,move[y+3]-3,move[z+3]-3]
            assert w[8] == 2 and w[10] == rid
            transported.append(w[9])
    assert len(transported) == 61488 and set(transported) == {i for i,p in enumerate(paths["paths"]) if p[5] == 2} and len(set(transported)) == 61476
    one_proposed.sort(); path_proposed.sort()
    assert one_proposed == saved["proposed_one_edge"] and path_proposed == saved["proposed_paths"]
    assert one_counts == saved["one_edge_dispositions"] == report["one_edge_dispositions"] == {"0":228,"2":7908,"4":1224}
    assert path_counts == saved["path_dispositions"] == report["path_dispositions"] == {"0":8664,"1":37278,"2":2112,"3":1368,"4":57996}
    assert len(activation_checked) == saved["existing_activation_rows_checked"] and len(mixed_checked) == saved["existing_mixed_rows_checked"]
    assert (len(one_proposed),len(path_proposed),len(one_proposed)+len(path_proposed)) == (1224,57996,59220)
    assert (report["proposed_one_edge_rows"],report["proposed_path_rows"],report["proposed_total_rows"],report["proposed_new_nonzeros"],report["following_rows_if_transferred"],report["variables_if_transferred"]) == (1224,57996,59220,176436,227270,68934)
    assert (report["complete_old_path_witnesses"],report["complete_old_one_edge_witnesses"],report["actual_native_zero_pair_receipts"],report["all_old_retained_transport_paths_covered"]) == (107520,9360,4410,61476)
    for key in ("old_census_producers_imported","old_censuses_reenumerated","CpModel_constructed","CpSolver_constructed"):
        assert saved[key] is False
    assert saved["native_rows_appended"] == saved["optimizer_calls"] == 0 and saved["unmatched_rows_not_claimed_independent"]
    assert report["native_rows_appended"] == report["optimizer_calls"] == 0 and not report["graph_constructed"] and not report["whole_component_excluded"]
    check_time(deadline)
    assert "ortools.sat.python.cp_model" not in sys.modules and "highspy" not in sys.modules
    answer = {"schema":"conway99.f0.literal-prism-transfer-independent-cold.v1",
        "status":"PASS_INDEPENDENT_COMPLETE_LITERAL_PRISM_TRANSFER",
        "source":reference(__file__),"configuration":CONFIG,"producer_report":run_report_ref,"producer_owner":run_owner_ref,
        "complete_inventory":archive_ref,"inventory_raw_sha256":report["inventory"]["raw_sha256"],
        "model_raw_sha256":cfg["model_raw_sha256"],"accepted_model_cold":cfg["inputs"]["model_cold"],
        "one_edge_six_site_graphs_reconstructed":9360,"path_six_site_graphs_reconstructed":107520,
        "unique_paths_checked":107418,"zero_pair_native_receipts_checked":4410,
        "distinct_native_premise_rows_checked":len(native_checked),"old_retained_path_transports_checked":61488,
        "proposed_one_edge_rows":1224,"proposed_path_rows":57996,"proposed_total_rows":59220,
        "proposed_one_edge_sha256":value_sha(one_proposed),"proposed_paths_sha256":value_sha(path_proposed),
        "one_edge_dispositions":dict(one_counts),"path_dispositions":dict(path_counts),
        "all_current_native_receipts_and_complete_origins_checked":True,"all_saved_six_site_graphs_and_forced_nonedge_premises_checked":True,
        "complete_old_census_coverage_reused":True,"old_censuses_reenumerated":False,
        "new_overlay_model_built_or_accepted":False,"native_model_decodes":1,"native_model_builds":0,
        "producer_imports":0,"CpModel_constructed":False,"CpSolver_constructed":False,"optimizer_calls":0,
        "graph_constructed":False,"whole_component_excluded":False,
        "seconds":time.monotonic()-started,"peak_rss_KiB":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    write(output,answer)
    return answer


if __name__ == "__main__":
    assert __debug__
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode",choices=("controls","run")); parser.add_argument("--directory",type=Path)
    parser.add_argument("--report-sha256"); parser.add_argument("--owner-sha256")
    parser.add_argument("--output",type=Path,required=True); args = parser.parse_args()
    if args.mode == "controls":
        result = controls(); result["source"] = reference(__file__); write(args.output.resolve(),result)
    else:
        assert args.directory is not None and args.report_sha256 and args.owner_sha256
        result = replay(args.directory.resolve(),args.report_sha256,args.owner_sha256,args.output.resolve())
    print(json.dumps({"status":result["status"],"seconds":result.get("seconds")}),flush=True)
