"""Complete three-chunk five-root triangle kernels and vertex Schur forms.

All 21 roots and all 1296 intersecting-triangle classes are retained.
Preparation is point-independent and never calls an optimizer.
"""
import argparse
from collections import Counter
from functools import lru_cache
import gzip
from itertools import combinations
from math import gcd,lcm
import json
from pathlib import Path
import time

from flint import fmpq_mat,fmpz_mat
import pynauty

import triangle_incidence_projector_moments as base
import triangle_projector_five_root_conditioning as products
import triangle_vertex_projector_moments as kernels

PRODUCT_SOURCE_SHA="578f8db7c51c7f5b934e7f7275b295a9a5908bf09d5f6a9d9662366914046e5c"
KERNEL_SOURCE_SHA="fea5b560e4aeeb323da6e8cde2bc52571a3dc7499f0900a0a12b1f134d4a31c7"
SCOPE_SOURCE_SHA="5a88cc3eab81b421e62cbcd22c6363431bc7a1056a23aae03b0425e69acefdd1"
SCOPE_SHA="09d44f9ae753f23b400d168486cd54ca813b12857536488a8b3064995c390efb"
OLD_Q_PREP_SHA="ed9e636277398aadb39077a344456412619bd40ea970717ebffdb148102ef73c"
OLD_Q_RAW_SHA="9011737fb1459d5c6c4db1dca51f777c49b3306b3ce27ca336096961ed768a06"
OLD_Q_GZIP_SHA="395d56df140bcdc30554ef8bed48663d11f006abb5cd72f1d94aff018f216ff8"
ROOTS=list(range(17,38))
CHUNKS=[[17,28,31,34,35,36,37],[18,20,21,26,29,30,32],[19,22,23,24,25,27,33]]
CHUNK_BOUNDS=[585705,460959,451518]
FAMILIES=["minus","plus","scalar","Q","minus_schur","plus_schur"]


def load_inputs(args):
    assert base.digest(Path(base.__file__).read_bytes())==kernels.BASE_SHA
    assert base.digest(Path(products.__file__).read_bytes())==PRODUCT_SOURCE_SHA
    assert base.digest(Path(kernels.__file__).read_bytes())==KERNEL_SOURCE_SHA
    p=Path(__file__).with_name("triangle_all_five_root_scope.py")
    assert base.digest(p.read_bytes())==SCOPE_SOURCE_SHA
    raw=args.scope.read_bytes();assert base.digest(raw)==SCOPE_SHA
    scope=json.loads(raw)
    assert scope["complete_all_21_root_coverage"]
    assert [d["root_type"] for d in scope["roots"]]==ROOTS
    assert sum(d["class_count"] for d in scope["roots"])==1296
    assert sum(d["partial_injection_and_free_edge_candidate_bound"] for d in scope["roots"])==1498182
    raw=(args.old_q_directory/"preparation.json").read_bytes()
    assert base.digest(raw)==OLD_Q_PREP_SHA
    packed=(args.old_q_directory/"model.json.gz").read_bytes()
    assert base.digest(packed)==OLD_Q_GZIP_SHA
    raw=gzip.decompress(packed);assert base.digest(raw)==OLD_Q_RAW_SHA
    old=json.loads(raw)
    assert [d["root_type"] for d in old["domains"]]==[26,27,28,32,33,34,35,37]
    return scope["roots"],old


def root_schur(domain,name,K,N):
    root=domain["root_rows"];r=5
    d,e,c=(27,-9,1) if name=="minus" else (44,11,-2)
    G=[[d*int(i==j)+e*((root[i]>>j)&1)+c for j in range(r)] for i in range(r)]
    minors=[int(fmpz_mat([row[:k] for row in G[:k]]).det()) for k in range(1,r+1)]
    assert all(x>0 for x in minors)
    inverse=fmpq_mat(G).inv()
    den=lcm(*(int(x.q) for x in inverse.entries()))
    P=[[int(inverse[i,j]*den) for j in range(r)] for i in range(r)]
    assert den>0 and all(sum(G[i][k]*P[k][j] for k in range(r))==den*int(i==j)
                        for i in range(r) for j in range(r))
    crosses=[];zeros=[]
    for index,cl in enumerate(domain["classes"]):
        rows=cl["literal_rows"]
        T=tuple(v for v in range(r) if cl["root_intersection_mask"]&(1<<v))+tuple(range(r,len(rows)))
        q=[d*int(i in T)+e*sum((rows[i]>>v)&1 for v in T)+3*c for i in range(r)]
        assert q==[sum(d*int(i==v)+e*((rows[i]>>v)&1)+c for v in T) for i in range(r)]
        crosses.append(q)
        if not cl["outside_masks"]:
            zeros.append(index)
    correction=[]
    for i,x in enumerate(crosses):
        for y in crosses[:i+1]:
            correction.append(sum(x[a]*P[a][b]*y[b] for a in range(r) for b in range(r)))
    scale=den*(9 if name=="minus" else 1)
    divisor=scale
    for x in correction:
        divisor=gcd(divisor,abs(x))
    assert divisor>0 and all(x%divisor==0 for x in correction)
    scale//=divisor;correction=[x//divisor for x in correction]
    result=Counter({key:scale*value for key,value in kernels.as_counter(K).items()})
    for entry,gid,value in N["terms"]:
        result[entry,gid]-=correction[entry]*value
    block=kernels.block(domain["root_type"],len(crosses),result)
    assert all(not set(zeros).intersection(kernels.locate(entry)) for entry,_,_ in block["terms"])
    form={"root_type":domain["root_type"],"family":name,"gram":G,
          "positive_leading_minors":minors,"inverse_numerator":P,"inverse_denominator":den,
          "crosses":crosses,"common_divisor":divisor,"kernel_scale":scale,
          "correction_lower":correction,"core_triangle_class_indices":zeros}
    return block,form


def build_root(domain,aut,identify,old,deadline):
    classes=domain["classes"];r=domain["root_type"]
    counters={name:Counter() for name in ("minus","plus","scalar","Q")}
    census=Counter();samples={}
    for i,left in enumerate(classes):
        for j,right in enumerate(classes[:i+1]):
            base.check_time(deadline)
            den=products.stabilizer(left)*products.stabilizer(right)
            assert den==left["outside_label_stabilizer"]*right["outside_label_stabilizer"]
            accum={name:Counter() for name in counters}
            census["candidate_bound"]+=products.completion_bound(len(left["outside_masks"]),len(right["outside_masks"]))
            for rows,T,U in products.products(tuple(domain["root_rows"]),left,right,census):
                assert 5<=len(rows)<=9
                gid=identify(rows);km,kp=kernels.kernels(rows,T,U);q=base.kernel(rows,T,U)
                for name,value in (("minus",km),("plus",kp),("scalar",1),("Q",q)):
                    accum[name][gid]+=int(aut[gid])*value
                tag=":".join(map(str,(len(rows),len(set(T)&set(U)),den,(km>0)-(km<0),(kp>0)-(kp<0))))
                samples.setdefault(tag,gid)
            entry=i*(i+1)//2+j
            for name,acc in accum.items():
                for gid,numerator in sorted(acc.items()):
                    assert numerator%den==0,(r,i,j,gid,name,den)
                    census["exact_stabilizer_divisions"]+=1
                    value=numerator//den
                    if value:
                        counters[name][entry,gid]=value
            census["lower_entries"]+=1
    assert census["lower_entries"]==domain["lower_entries"]
    assert census["candidate_bound"]==domain["partial_injection_and_free_edge_candidate_bound"]
    first=[]
    for index,cl in enumerate(classes):
        gid=identify(tuple(cl["literal_rows"]));div=cl["outside_label_stabilizer"]
        assert int(aut[gid])%div==0
        first.append([gid,int(aut[gid])//div])
    D=Counter({(i*(i+1)//2+i,gid):value for i,(gid,value) in enumerate(first)})
    keys=set(D)
    for counter in counters.values():
        keys.update(counter)
    for key in keys:
        assert (11*counters["Q"][key]+110*counters["minus"][key]
                +3*counters["plus"][key]+10*counters["scalar"][key])==2310*D[key]
    families={name:kernels.block(r,len(classes),counter) for name,counter in counters.items()}
    prior=next((d for d in old["domains"] if d["root_type"]==r),None)
    old_q_checked=False
    if prior:
        assert [(c["root_intersection_mask"],c["outside_masks"]) for c in prior["classes"]]==[(c["root_intersection_mask"],c["outside_masks"]) for c in classes]
        det=prior["core_triangle_gram_determinant"];adj=prior["core_triangle_gram_adjugate"]
        answer=Counter({key:det*value for key,value in counters["Q"].items()})
        for (entry,gid),value in counters["scalar"].items():
            a,b=kernels.locate(entry)
            x=prior["classes"][a]["core_triangle_cross_values"];y=prior["classes"][b]["core_triangle_cross_values"]
            answer[entry,gid]-=value*sum(x[i]*adj[i][j]*y[j] for i in range(len(x)) for j in range(len(y)))
        expected=next(b for b in old["blocks"] if b["root_type"]==r)
        assert kernels.terms(answer)==expected["terms"]
        old_q_checked=True
    forms=[]
    for name in ("minus","plus"):
        answer,form=root_schur(domain,name,families[name],families["scalar"])
        families[name+"_schur"]=answer;forms.append(form)
    return {"root_type":r,"domain":domain,"families":families,"root_schur_forms":forms,
            "first_moment_forms":first,"coefficient_partition_identities":len(keys),
            "old_conditioned_Q_tensor_matched":old_q_checked,
            "census":dict(census),"control_graph_ids":samples}


def root_maps(domains):
    return products.root_maps(domains)


def direct_host(rows,domains,maps):
    labels={d["root_type"]:{(c["root_intersection_mask"],tuple(c["outside_masks"])):i for i,c in enumerate(d["classes"])}
            for d in domains}
    out={name:{d["root_type"]:[[0]*d["class_count"] for _ in range(d["class_count"])] for d in domains}
         for name in ("minus","plus","scalar","Q")}
    ts=base.triangles(rows);embeddings=pairs=0
    for chosen in combinations(range(len(rows)),5):
        key=products.code(base.induced(rows,chosen))
        if key not in maps:
            continue
        rid,transports=maps[key]
        for p in transports:
            root=tuple(chosen[i] for i in p);root_set=set(root)
            selected=[T for T in ts if root_set.intersection(T)]
            types=[labels[rid][products.classify(rows,T,root)] for T in selected]
            for i,T in enumerate(selected):
                for j,U in enumerate(selected):
                    km,kp=kernels.kernels(rows,T,U)
                    for name,value in (("minus",km),("plus",kp),("scalar",1),("Q",base.kernel(rows,T,U))):
                        out[name][rid][types[i]][types[j]]+=value
                    pairs+=1
            embeddings+=1
    return out,embeddings,pairs


def controls(data,records,deadline):
    graphs,levels,_,_=data;domains=[r["domain"] for r in records];maps=root_maps(domains)
    lookup={(len(graphs[i]),pynauty.certificate(base.nauty(graphs[i]))):i
            for n in range(5,10) for i in levels[n]}
    hosts={r["root_type"] for r in records}
    for record in records:
        hosts.update(record["control_graph_ids"].values())
    result=[]
    for gid in sorted(hosts):
        base.check_time(deadline);rows=graphs[gid]
        counts=[0]*len(graphs)
        for n in range(5,len(rows)+1):
            for vertices in combinations(range(len(rows)),n):
                pos=gid if n==len(rows) else lookup[n,pynauty.certificate(base.nauty(base.induced(rows,vertices)))]
                counts[pos]+=1
        direct,embeddings,pairs=direct_host(rows,domains,maps)
        for name in FAMILIES:
            reconstructed=base.contract({"blocks":[r["families"][name] for r in records]},counts)
            for record in records:
                rid=record["root_type"]
                if name in direct:
                    expected=direct[name][rid]
                else:
                    original=name.removesuffix("_schur")
                    form=next(f for f in record["root_schur_forms"] if f["family"]==original)
                    K=direct[original][rid];N=direct["scalar"][rid]
                    expected=[[form["kernel_scale"]*K[a][b]-form["correction_lower"][max(a,b)*(max(a,b)+1)//2+min(a,b)]*N[a][b]
                               for b in range(len(K))] for a in range(len(K))]
                assert expected==reconstructed[rid],(gid,rid,name)
        result.append({"host_type":gid,"order":len(rows),"labelled_root_embeddings":embeddings,
                       "ordered_triangle_pairs":pairs,"all_chunk_families_equal":True})
    assert any(c["order"]==9 and c["ordered_triangle_pairs"] for c in result)
    return result


def specification(records):
    return {"schema":"conway99.all-five-root-triangle-kernels.v1",
            "catalogue_sha256":base.CATALOGUE_SHA,"scope_sha256":SCOPE_SHA,
            "domains":[r["domain"] for r in records],
            "families":{name:[r["families"][name] for r in records] for name in FAMILIES},
            "root_schur_forms":[f for r in records for f in r["root_schur_forms"]],
            "first_moment_forms":[{"root_type":r["root_type"],"forms":r["first_moment_forms"]} for r in records],
            "all_intersecting_triangle_classes_retained":True,
            "constant_class_vector_is_not_assumed_to_be_a_kernel":True,
            "root_point_star_kernels_apply_to_Q_and_schur":True,
            "new_point_query_requires_separate_gate":True,
            "count_point_loaded":False,"optimizer_called":False}


def prepare(args):
    assert 0<args.seconds<=120 and 0<args.chunk_seconds<=60 and not args.directory.exists()
    start=time.monotonic();deadline=start+args.seconds
    domains,old=load_inputs(args);by_id={d["root_type"]:d for d in domains}
    assert sorted(i for chunk in CHUNKS for i in chunk)==ROOTS
    for chunk,bound in zip(CHUNKS,CHUNK_BOUNDS):
        assert len(chunk)==7 and sum(by_id[i]["partial_injection_and_free_edge_candidate_bound"] for i in chunk)==bound
    data=base.load_catalogue(args.catalogue);graphs,levels,aut,_=data
    lookup={(len(graphs[i]),pynauty.certificate(base.nauty(graphs[i]))):i for n in range(5,10) for i in levels[n]}
    @lru_cache(maxsize=150000)
    def identify(rows):
        assert base.cap_valid(rows)
        return lookup[len(rows),pynauty.certificate(base.nauty(rows))]
    args.directory.mkdir(parents=True)
    completed={};chunk_reports=[]
    report={"status":"INCOMPLETE","source_sha256":base.digest(Path(__file__).read_bytes()),
            "product_source_sha256":PRODUCT_SOURCE_SHA,"kernel_source_sha256":KERNEL_SOURCE_SHA,
            "scope_source_sha256":SCOPE_SOURCE_SHA,"scope_sha256":SCOPE_SHA,
            "old_Q_raw_sha256":OLD_Q_RAW_SHA,"catalogue_sha256":base.CATALOGUE_SHA,
            "completed_roots":[],"completed_chunks":[],"complete_21_root_coverage":False,
            "count_point_loaded":False,"optimizer_called":False,
            "limits":{"overall_seconds":args.seconds,"chunk_seconds":args.chunk_seconds}}
    try:
        for ci,ids in enumerate(CHUNKS):
            base.check_time(deadline);chunk_start=time.monotonic();chunk_deadline=min(deadline,chunk_start+args.chunk_seconds)
            selected=[]
            for rid in ids:
                record=build_root(by_id[rid],aut,identify,old,chunk_deadline)
                completed[rid]=record;selected.append(record)
                raw=base.canonical(record)
                (args.directory/("root-"+str(rid)+".json.gz")).write_bytes(gzip.compress(raw,mtime=0))
                report["completed_roots"].append(rid)
                (args.directory/"progress.json").write_text(json.dumps(report,indent=2)+"\n")
                print(json.dumps({"chunk":ci,"root":rid,"classes":by_id[rid]["class_count"],
                                  "candidate_bound":record["census"]["candidate_bound"]}),flush=True)
            checked=controls(data,selected,chunk_deadline);base.check_time(chunk_deadline)
            model=specification(selected);raw=base.canonical(model);packed=gzip.compress(raw,mtime=0)
            model_path="chunk-"+str(ci)+".json.gz";(args.directory/model_path).write_bytes(packed)
            chunk={"status":"COMPLETE_CHUNK_WITH_LITERAL_HOST_CONTROLS","chunk":ci,"root_types":ids,
                   "source_sha256":report["source_sha256"],"candidate_bound":CHUNK_BOUNDS[ci],
                   "model_path":model_path,"model_raw_sha256":base.digest(raw),"model_gzip_sha256":base.digest(packed),
                   "small_host_controls":checked,"seconds":time.monotonic()-chunk_start}
            name="chunk-"+str(ci)+"-preparation.json";text=json.dumps(chunk,indent=2)+"\n";(args.directory/name).write_text(text)
            chunk_reports.append({"chunk":ci,"root_types":ids,"preparation_path":name,
                                  "preparation_sha256":base.digest(text.encode()),
                                  "model_raw_sha256":base.digest(raw),"model_gzip_sha256":base.digest(packed),
                                  "controls":len(checked),"seconds":chunk["seconds"]})
            report["completed_chunks"].append(ci);report["chunks"]=chunk_reports
            (args.directory/"progress.json").write_text(json.dumps(report,indent=2)+"\n")
            print(json.dumps({"completed_chunk":ci,"controls":len(checked),"seconds":chunk["seconds"]}),flush=True)
        records=[completed[rid] for rid in ROOTS]
        assert sum(r["old_conditioned_Q_tensor_matched"] for r in records)==8
        model=specification(records);model["chunk_certificates"]=chunk_reports
        raw=base.canonical(model);packed=gzip.compress(raw,mtime=0)
        (args.directory/"model.json.gz").write_bytes(packed);base.check_time(deadline)
        report.update(status="COMPLETE_ALL_21_FIVE_ROOT_TRIANGLE_KERNEL_AND_SCHUR_PREPARATION",
                      complete_21_root_coverage=True,classes=1296,lower_entries_per_family=64296,
                      family_blocks={name:21 for name in FAMILIES},
                      family_nonzeros={name:sum(len(r["families"][name]["terms"]) for r in records) for name in FAMILIES},
                      candidate_union_bound=1498182,
                      exact_stabilizer_divisions=sum(r["census"]["exact_stabilizer_divisions"] for r in records),
                      coefficient_partition_identities=sum(r["coefficient_partition_identities"] for r in records),
                      all_eight_old_Q_tensors_recovered=True,
                      positive_root_Gram_leading_minors=210,exact_inverse_entries=1050,
                      literal_host_controls=sum(c["controls"] for c in chunk_reports),
                      model_raw_sha256=base.digest(raw),model_gzip_sha256=base.digest(packed),
                      model_raw_bytes=len(raw),model_gzip_bytes=len(packed),
                      constant_class_vector_is_not_assumed_to_be_a_kernel=True,
                      point_query_requires_separate_gate=True)
    except Exception as error:
        report.update(status="INCOMPLETE_NO_COMPLETE_FAMILY_CLAIM",error_type=type(error).__name__,error_message=str(error))
        raise
    finally:
        report["seconds"]=time.monotonic()-start
        (args.directory/"preparation.json").write_text(json.dumps(report,indent=2)+"\n")
        print(json.dumps(report,indent=2),flush=True)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--catalogue",type=Path,required=True)
    p.add_argument("--scope",type=Path,required=True)
    p.add_argument("--old-q-directory",type=Path,required=True)
    p.add_argument("--directory",type=Path,required=True)
    p.add_argument("--seconds",type=float,default=120)
    p.add_argument("--chunk-seconds",type=float,default=60)
    prepare(p.parse_args())


if __name__=="__main__":
    main()
