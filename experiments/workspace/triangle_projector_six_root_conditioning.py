"""Six-root triangle-intersection Schur tensors, prepared without a point.

All thirty triangle-containing roots of order six and every triangle
class meeting the root are retained. Ordered labelled flag products are
converted to unlabelled triangle-class products by exact stabilizers.
"""
import argparse
from collections import Counter
from functools import lru_cache
import gzip
from itertools import combinations, permutations, product
import json
from math import comb, factorial
from pathlib import Path
import time

import pynauty

import triangle_incidence_projector_moments as base

BASE_SHA = "1e7a8b7380314d6dfd8ff05954a13662bc011378f5759ad675ec1bc281fa19e9"
SCOPE_SOURCE_SHA = "d25c7cfdb94fa79f0100990752a3c941011dd62e230c02b71472657f715f1b65"
SCOPE_SHA = "78e62efc423f7acd498368207607c5dfc5572dd1840accebe46c38141aeb331f"
ROOT_IDS = [50,51,52,53,60,62,67,68,69,70,71,72,76,77,79,80,83,84,85,86,87,88,90,93,94,95,96,97,98,99]
ORDERS = [220,176,110,52,139,86,150,122,114,77,78,43,75,91,50,109,92,75,44,74,57,47,53,60,36,24,44,39,26,11]
CHUNKS = [[50,94,95,97,98,99],[51,62,72,79,85,86],[67,71,80,84,88,90],[60,69,76,77,93,96],[52,53,68,70,83,87]]


def class_key(c):
    return c["root_intersection_mask"], tuple(c["outside_masks"])


def classify(rows, triangle, root):
    inside = sum(1 << i for i, v in enumerate(root) if v in triangle)
    root_set = set(root)
    outside = tuple(sorted(sum(((rows[v] >> u) & 1) << i for i, u in enumerate(root))
                           for v in triangle if v not in root_set))
    return inside, outside


def stabilizer(c):
    answer=1
    for count in Counter(c["outside_masks"]).values():
        answer*=factorial(count)
    return answer


def completion_bound(a,b):
    return sum(comb(a,q)*comb(b,q)*factorial(q)*(1 << ((a-q)*(b-q)))
               for q in range(min(a,b)+1))


def load_scope(path):
    assert base.digest(Path(base.__file__).read_bytes()) == BASE_SHA
    source=Path(__file__).with_name("triangle_projector_intersecting_root_scope_v2.py")
    assert base.digest(source.read_bytes()) == SCOPE_SOURCE_SHA
    raw=path.read_bytes()
    assert base.digest(raw) == SCOPE_SHA
    report=json.loads(raw)
    assert report["source_sha256"] == SCOPE_SOURCE_SHA
    assert report["complete_five_and_six_root_coverage"]
    domains=[d for d in report["roots"] if d["root_order"]==6]
    assert [d["root_type"] for d in domains]==ROOT_IDS
    assert [d["class_count"] for d in domains]==ORDERS
    assert sum(d["partial_injection_and_free_edge_candidate_bound"] for d in domains)==2967175
    return domains


def products(root,left,right,census):
    """Every ordered pair of labelled extensions has one overlap map."""
    r=len(root);a=len(left["outside_masks"]);b=len(right["outside_masks"])
    left_triangle=tuple(i for i in range(r) if left["root_intersection_mask"] & (1 << i)) + tuple(range(r,r+a))
    for overlap in range(min(a,b)+1):
        for chosen in combinations(range(b),overlap):
            for images in permutations(range(a),overlap):
                census["partial_injections_considered"]+=1
                mapping={j:r+i for j,i in zip(chosen,images)}
                if any(right["outside_masks"][j] != left["outside_masks"][i]
                       for j,i in zip(chosen,images)):
                    census["mask_incompatible_partial_injections"]+=1
                    continue
                fresh=iter(range(r+a,r+a+b-overlap))
                right_map=tuple(mapping[j] if j in mapping else next(fresh) for j in range(b))
                n=r+a+b-overlap
                rows=list(left["literal_rows"])+[0]*(n-r-a)
                for j,v in enumerate(right_map):
                    mask=right["outside_masks"][j]
                    for u in range(r):
                        if mask & (1 << u):
                            rows[u] |= 1 << v
                            rows[v] |= 1 << u
                for u,v in combinations(right_map,2):
                    rows[u] |= 1 << v
                    rows[v] |= 1 << u
                rows=tuple(rows)
                if not base.cap_valid(rows):
                    census["initial_union_cap_failures"]+=1
                    continue
                left_only=sorted(set(range(r,r+a))-set(right_map))
                right_only=sorted(set(right_map)-set(range(r,r+a)))
                unknown=list(product(left_only,right_only))
                assert len(unknown)==(a-overlap)*(b-overlap)
                right_triangle=tuple(sorted(tuple(i for i in range(r) if right["root_intersection_mask"] & (1 << i)) + right_map))
                def visit(index,current):
                    if index==len(unknown):
                        census["complete_cap_valid_unions"]+=1
                        assert classify(current,left_triangle,tuple(range(r)))==class_key(left)
                        assert classify(current,right_triangle,tuple(range(r)))==class_key(right)
                        yield current,left_triangle,right_triangle
                        return
                    yield from visit(index+1,current)
                    u,v=unknown[index]
                    changed=list(current)
                    changed[u] |= 1 << v
                    changed[v] |= 1 << u
                    changed=tuple(changed)
                    if base.cap_valid(changed):
                        yield from visit(index+1,changed)
                    else:
                        census["cross_edge_cap_prunings"]+=1
                yield from visit(0,rows)


def build_block(domain,graphs,aut,identify,deadline):
    root=tuple(domain["root_rows"]);classes=domain["classes"]
    det=domain["core_triangle_gram_determinant"]
    adj=domain["core_triangle_gram_adjugate"]
    core=tuple(tuple(t) for t in domain["core_triangles"])
    k=len(core);n=len(classes)
    assert len(root)==6 and k in (1,2) and det>0
    terms=[];census=Counter();samples={}
    for i,left in enumerate(classes):
        for j,right in enumerate(classes[:i+1]):
            base.check_time(deadline)
            den=stabilizer(left)*stabilizer(right)
            constant=sum(left["core_triangle_cross_values"][a]*adj[a][b]*right["core_triangle_cross_values"][b]
                         for a in range(k) for b in range(k))
            upper=completion_bound(len(left["outside_masks"]),len(right["outside_masks"]))
            census["unpruned_completion_upper_bound"]+=upper
            acc=Counter()
            for rows,lt,rt in products(root,left,right,census):
                graph_id=identify(rows)
                assert 6<=len(rows)<=10
                value=det*base.kernel(rows,lt,rt)-constant
                acc[graph_id]+=int(aut[graph_id])*value
                tag=":".join(map(str,(len(rows),len(set(lt)&set(rt)),den,(value>0)-(value<0))))
                samples.setdefault(tag,graph_id)
            for graph_id,numerator in sorted(acc.items()):
                assert numerator % den == 0, (domain["root_type"],i,j,graph_id,den,numerator)
                coefficient=numerator//den
                census["exact_stabilizer_divisions"]+=1
                if coefficient:
                    terms.append([i*(i+1)//2+j,graph_id,coefficient])
            census["completed_lower_entries"]+=1
    assert census["completed_lower_entries"]==n*(n+1)//2
    assert census["unpruned_completion_upper_bound"]==domain["partial_injection_and_free_edge_candidate_bound"]
    assert census["complete_cap_valid_unions"]<=census["unpruned_completion_upper_bound"]
    zeros=set(domain["core_triangle_class_indices"])
    for entry,_,coefficient in terms:
        a=0
        while (a+1)*(a+2)//2<=entry:
            a+=1
        b=entry-a*(a+1)//2
        assert a not in zeros and b not in zeros
        assert type(coefficient)is int and coefficient
    return {"root_type":domain["root_type"],"order":n,"lower_entries":n*(n+1)//2,
            "terms":terms,"census":dict(sorted(census.items())),
            "sample_graphs":samples,"all_core_triangle_rows_zero_coefficientwise":True}


def code(rows):
    return sum(((rows[a]>>b)&1)<<i for i,(a,b) in enumerate(combinations(range(len(rows)),2)))


def root_maps(domains):
    out={}
    for d in domains:
        root=tuple(d["root_rows"])
        for p in permutations(range(6)):
            target=base.induced(root,p)
            inverse=tuple(p.index(i) for i in range(6))
            assert base.induced(target,inverse)==root
            key=code(target)
            if key not in out:
                out[key]=[d["root_type"],set()]
            assert out[key][0]==d["root_type"]
            out[key][1].add(inverse)
    for d in domains:
        for root_id,maps in out.values():
            if root_id==d["root_type"]:
                assert len(maps)==d["root_automorphisms"]
    return {key:(root_id,sorted(maps)) for key,(root_id,maps) in out.items()}


def direct_host(rows,specification,maps):
    domains={d["root_type"]:d for d in specification["domains"]}
    labels={root_id:{class_key(c):i for i,c in enumerate(d["classes"])}
            for root_id,d in domains.items()}
    matrices={root_id:[[0]*d["class_count"] for _ in d["classes"]]
              for root_id,d in domains.items()}
    triangles=base.triangles(rows);embeddings=0;pairs=0
    for root in combinations(range(len(rows)),6):
        key=code(base.induced(rows,root))
        if key not in maps:
            continue
        root_id,transports=maps[key];domain=domains[root_id]
        det=domain["core_triangle_gram_determinant"];adj=domain["core_triangle_gram_adjugate"]
        for p in transports:
            labelled=tuple(root[i] for i in p)
            root_set=set(labelled)
            selected=[t for t in triangles if root_set.intersection(t)]
            types=[labels[root_id][classify(rows,t,labelled)] for t in selected]
            core=[tuple(sorted(labelled[i] for i in t)) for t in domain["core_triangles"]]
            q=[[base.kernel(rows,t,u) for t in core] for u in selected]
            for u,t in enumerate(selected):
                assert q[u]==domain["classes"][types[u]]["core_triangle_cross_values"]
            M=matrices[root_id];k=len(core)
            for u,left in enumerate(selected):
                for v,right in enumerate(selected):
                    value=det*base.kernel(rows,left,right)-sum(q[u][a]*adj[a][b]*q[v][b]
                                                             for a in range(k) for b in range(k))
                    M[types[u]][types[v]]+=value
                    pairs+=1
            embeddings+=1
    return matrices,embeddings,pairs


def controls(data,specification,deadline):
    graphs,levels,_,_=data
    maps=root_maps(specification["domains"])
    lookup={(len(graphs[i]),pynauty.certificate(base.nauty(graphs[i]))):i
            for n in range(6,11) for i in levels[n]}
    hosts={d["root_type"] for d in specification["domains"]}
    for block in specification["blocks"]:
        hosts.update(block["sample_graphs"].values())
    records=[]
    for graph_id in sorted(hosts):
        base.check_time(deadline)
        rows=graphs[graph_id]
        counts=[0]*len(graphs)
        for n in range(6,len(rows)+1):
            for subset in combinations(range(len(rows)),n):
                pos=graph_id if n==len(rows) else lookup[n,pynauty.certificate(base.nauty(base.induced(rows,subset)))]
                counts[pos]+=1
        actual,embeddings,pairs=direct_host(rows,specification,maps)
        reconstructed=base.contract(specification,counts)
        assert actual==reconstructed,(graph_id,"independent ordered-pair host control")
        records.append({"host_type":graph_id,"order":len(rows),
                        "labelled_root_embeddings":embeddings,"ordered_triangle_pairs":pairs,
                        "all_included_full_blocks_equal":True,
                        "matrix_sha256":base.digest(base.canonical(actual))})
    assert any(r["order"]==10 and r["ordered_triangle_pairs"] for r in records)
    return records


def prepare(args):
    assert 0<args.seconds<=180 and 0<args.chunk_seconds<=60 and not args.directory.exists()
    start=time.monotonic();deadline=start+args.seconds
    domains=load_scope(args.scope)
    by_root={d["root_type"]:d for d in domains}
    assert len(CHUNKS)==5 and all(len(chunk)==6 for chunk in CHUNKS)
    assert sorted(i for chunk in CHUNKS for i in chunk)==ROOT_IDS
    data=base.load_catalogue(args.catalogue)
    graphs,levels,aut,_=data
    lookup={(len(graphs[i]),pynauty.certificate(base.nauty(graphs[i]))):i
            for n in range(6,11) for i in levels[n]}
    @lru_cache(maxsize=150000)
    def identify(rows):
        assert base.cap_valid(rows)
        return lookup[len(rows),pynauty.certificate(base.nauty(rows))]
    args.directory.mkdir(parents=True)
    blocks_by_root={}
    chunk_records=[]
    report={"status":"INCOMPLETE","source_sha256":base.digest(Path(__file__).read_bytes()),
            "base_source_sha256":BASE_SHA,"scope_source_sha256":SCOPE_SOURCE_SHA,
            "scope_sha256":SCOPE_SHA,"catalogue_sha256":base.CATALOGUE_SHA,
            "completed_root_types":[],"completed_chunk_indices":[],
            "complete_thirty_block_coverage":False,"count_point_loaded":False,
            "optimizer_called":False,"limits":{"overall_seconds":args.seconds,
                                               "per_chunk_seconds":args.chunk_seconds}}
    try:
        for chunk_index,ids in enumerate(CHUNKS):
            base.check_time(deadline)
            chunk_start=time.monotonic()
            chunk_deadline=min(deadline,chunk_start+args.chunk_seconds)
            selected=[by_root[i] for i in ids]
            chunk={"schema":"conway99.six-root-conditioned-triangle-chunk.v1",
                   "catalogue_sha256":base.CATALOGUE_SHA,"scope_sha256":SCOPE_SHA,
                   "domains":selected,"blocks":[],
                   "kernel":"det(C)Q(U,V)-q_U^T adj(C)q_V",
                   "normalization":"Labelled ordered flag products times Aut(union), divided by the product of outside-mask factorial stabilizers after collecting each induced type.",
                   "all_intersecting_triangle_classes_retained":True,
                   "count_point_loaded":False,"optimizer_called":False}
            for d in selected:
                block=build_block(d,graphs,aut,identify,chunk_deadline)
                chunk["blocks"].append(block)
                blocks_by_root[d["root_type"]]=block
                raw=base.canonical(block)
                (args.directory/("root-"+str(d["root_type"])+".json.gz")).write_bytes(gzip.compress(raw,mtime=0))
                report["completed_root_types"].append(d["root_type"])
                print(json.dumps({"chunk":chunk_index,"completed_root":d["root_type"],
                                  "order":block["order"],"tensor_nonzeros":len(block["terms"]),
                                  "valid_union_completions":block["census"]["complete_cap_valid_unions"]}),flush=True)
            host_controls=controls(data,chunk,chunk_deadline)
            base.check_time(chunk_deadline)
            raw=base.canonical(chunk);compressed=gzip.compress(raw,mtime=0)
            name="chunk-"+str(chunk_index)+".json.gz"
            (args.directory/name).write_bytes(compressed)
            chunk_record={"status":"COMPLETE_CHUNK_WITH_LITERAL_HOST_CONTROLS",
                          "chunk_index":chunk_index,"root_types":ids,
                          "source_sha256":report["source_sha256"],
                          "model_path":name,"model_raw_sha256":base.digest(raw),
                          "model_gzip_sha256":base.digest(compressed),
                          "tensor_nonzeros":sum(len(b["terms"]) for b in chunk["blocks"]),
                          "candidate_completion_upper_bound":sum(d["partial_injection_and_free_edge_candidate_bound"] for d in selected),
                          "small_host_controls":host_controls,
                          "seconds":time.monotonic()-chunk_start}
            chunk_text=json.dumps(chunk_record,indent=2)+"\n"
            report_name="chunk-"+str(chunk_index)+"-preparation.json"
            (args.directory/report_name).write_text(chunk_text)
            chunk_records.append({"chunk_index":chunk_index,"root_types":ids,
                                  "report_path":report_name,
                                  "report_sha256":base.digest(chunk_text.encode()),
                                  "model_raw_sha256":chunk_record["model_raw_sha256"],
                                  "model_gzip_sha256":chunk_record["model_gzip_sha256"],
                                  "host_controls":len(host_controls),"seconds":chunk_record["seconds"]})
            report["completed_chunk_indices"].append(chunk_index)
            report["chunks"]=chunk_records
            (args.directory/"progress.json").write_text(json.dumps(report,indent=2)+"\n")
            print(json.dumps({"completed_chunk":chunk_index,"seconds":chunk_record["seconds"],
                              "host_controls":len(host_controls)}),flush=True)
        specification={"schema":"conway99.six-root-conditioned-triangle-moments.v1",
                       "catalogue_sha256":base.CATALOGUE_SHA,"scope_sha256":SCOPE_SHA,
                       "domains":domains,"blocks":[blocks_by_root[i] for i in ROOT_IDS],
                       "kernel":"det(C)Q(U,V)-q_U^T adj(C)q_V",
                       "normalization":"Labelled ordered flag products times Aut(union), divided by the product of outside-mask factorial stabilizers after collecting each induced type.",
                       "chunk_certificates":chunk_records,
                       "all_intersecting_triangle_classes_retained":True,
                       "count_point_loaded":False,"optimizer_called":False}
        base.check_time(deadline)
        raw=base.canonical(specification);compressed=gzip.compress(raw,mtime=0)
        (args.directory/"model.json.gz").write_bytes(compressed)
        all_blocks=specification["blocks"]
        report.update(status="COMPLETE_POINT_INDEPENDENT_SIX_ROOT_CONDITIONED_PREPARATION",
                      complete_thirty_block_coverage=True,block_orders=ORDERS,
                      classes=sum(ORDERS),lower_entries=sum(b["lower_entries"] for b in all_blocks),
                      tensor_nonzeros=sum(len(b["terms"]) for b in all_blocks),
                      valid_union_completions=sum(b["census"]["complete_cap_valid_unions"] for b in all_blocks),
                      exact_stabilizer_divisions=sum(b["census"]["exact_stabilizer_divisions"] for b in all_blocks),
                      candidate_completion_upper_bound=2967175,
                      model_raw_sha256=base.digest(raw),model_gzip_sha256=base.digest(compressed),
                      model_raw_bytes=len(raw),model_gzip_bytes=len(compressed),
                      all_core_triangle_rows_zero_coefficientwise=True,
                      independent_host_controls=sum(c["host_controls"] for c in chunk_records),
                      point_query_requires_separate_gate=True)
    except Exception as error:
        report.update(status="INCOMPLETE_NO_FULL_TENSOR_CLAIM",
                      error_type=type(error).__name__,error_message=str(error))
        raise
    finally:
        report["seconds"]=time.monotonic()-start
        (args.directory/"preparation.json").write_text(json.dumps(report,indent=2)+"\n")
        print(json.dumps(report,indent=2),flush=True)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--catalogue",type=Path,required=True)
    p.add_argument("--scope",type=Path,required=True)
    p.add_argument("--directory",type=Path,required=True)
    p.add_argument("--seconds",type=float,default=180)
    p.add_argument("--chunk-seconds",type=float,default=60)
    args=p.parse_args()
    prepare(args)


if __name__=="__main__":
    main()
