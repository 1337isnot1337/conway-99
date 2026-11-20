"""Two vertex-derived triangle projectors on every four-root triangle class.

Preparation is point-independent. Literal induced-subset coefficients are
rebuilt for both kernels, and the earlier Q tensor is recovered exactly.
Two additional kernels condition separately on a triangle inside the root.
"""
import argparse
from collections import Counter
import gzip
from itertools import combinations
import json
from pathlib import Path
import time

import pynauty

import triangle_incidence_projector_moments as base
import triangle_incidence_projector_full_classes as full

BASE_SHA="1e7a8b7380314d6dfd8ff05954a13662bc011378f5759ad675ec1bc281fa19e9"
FULL_SHA="d26499a0eec07c2c80a28818f0a40319fc0b14f54140a28253c820eb00d44f2a"
FULL_PREP_SHA="48a3788a0ca55dd445971f71dba46be49f4291b0ddd6b920beebb5de87e66fb7"
FULL_RAW_SHA="819aa1954ce038865404433995eb401ad7111cad0a21992f4ba8c42e3e04687c"
FULL_GZIP_SHA="9305dffa83a024f574321dd5843244724d3cd82b569c0749d2ed135ccdc01938"
FIRST_SHA="3c3b957f6cfaebafa448804d9c61759b3a0fc448c484a7b590095f831ecc6184"
SCALAR_RAW_SHA="9b6d6e133f1d9c685bc19ca174cb3a6fa1d7b5976be49e112a0702b44bcaac6e"
SCALAR_GZIP_SHA="782e4c3738adeda2596e25bc05062fb56252547777e26e68a0428afb3a3cb5cd"
ROOTS=list(range(8,17))
ORDERS=[107,93,72,49,79,58,41,34,41]


def kernels(rows,left,right):
    overlap=len(set(left)&set(right))
    if overlap==3:
        assert left==right
        return 4,180
    if overlap==1:
        return 0,70
    assert overlap==0
    edges=sum((rows[a]>>b)&1 for a in left for b in right)
    assert 0<=edges<=3
    return 1-edges,11*edges-18


def load_inputs(args):
    assert base.digest(Path(base.__file__).read_bytes())==BASE_SHA
    assert base.digest(Path(full.__file__).read_bytes())==FULL_SHA
    raw=(args.full_directory/"preparation.json").read_bytes()
    assert base.digest(raw)==FULL_PREP_SHA
    prep=json.loads(raw)
    compressed=(args.full_directory/"model.json.gz").read_bytes()
    assert base.digest(compressed)==FULL_GZIP_SHA==prep["model_gzip_sha256"]
    raw=gzip.decompress(compressed)
    assert base.digest(raw)==FULL_RAW_SHA==prep["model_raw_sha256"]
    old=json.loads(raw)
    assert old["all_triangle_classes_included"]
    assert [d["root_type"] for d in old["domains"]]==ROOTS
    assert [b["order"] for b in old["blocks"]]==ORDERS
    raw=args.first_moments.read_bytes()
    assert base.digest(raw)==FIRST_SHA
    first=json.loads(raw)
    assert first["all_574_classes_retained"]
    assert [d["root_type"] for d in first["domains"]]==ROOTS
    compressed=args.scalar_model.read_bytes()
    assert base.digest(compressed)==SCALAR_GZIP_SHA
    raw=gzip.decompress(compressed)
    assert base.digest(raw)==SCALAR_RAW_SHA
    scalar=json.loads(raw)
    assert [d["root_type"] for d in scalar["domains"]]==[14,15]
    for d,f in zip(old["domains"],first["domains"]):
        assert [full.class_key(c) for c in d["classes"]]==[full.class_key(c) for c in f["classes"]]
    return old,first,scalar


def terms(counter):
    return [[entry,graph,value] for (entry,graph),value in sorted(counter.items()) if value]


def as_counter(block):
    out=Counter()
    for entry,graph,value in block["terms"]:
        assert (entry,graph) not in out
        out[entry,graph]=value
    return out


def block(root,order,counter):
    out=terms(counter)
    assert all(0<=e<order*(order+1)//2 and type(v)is int for e,_,v in out)
    return {"root_type":root,"order":order,"lower_entries":order*(order+1)//2,"terms":out}


def locate(entry):
    a=0
    while (a+1)*(a+2)//2<=entry:
        a+=1
    return a,entry-a*(a+1)//2


def conditioned(domains,first,families):
    output={"minus_conditioned":[],"plus_conditioned":[]}
    core_data=[]
    first_by_id={d["root_type"]:d for d in first["domains"]}
    for d in domains:
        root=tuple(d["root_rows"])
        cores=base.triangles(root)
        if not cores:
            continue
        assert d["root_type"] in (14,15) and len(cores)==1
        T=cores[0]
        literal=first_by_id[d["root_type"]]["classes"]
        cross=[[],[]]
        core_index=None
        for i,c in enumerate(literal):
            U=tuple(v for v in range(4) if c["root_intersection_mask"]&(1<<v))+tuple(range(4,len(c["literal_rows"])))
            pair=kernels(c["literal_rows"],T,U)
            for j in range(2):
                cross[j].append(pair[j])
            if len(c["outside_masks"])==0 and set(U)==set(T):
                assert core_index is None
                core_index=i
        assert core_index is not None
        scalar=as_counter(next(b for b in families["scalar"] if b["root_type"]==d["root_type"]))
        saved={}
        for name,diag,q in zip(("minus","plus"),(4,180),cross):
            original=as_counter(next(b for b in families[name] if b["root_type"]==d["root_type"]))
            counter=Counter({key:diag*value for key,value in original.items()})
            for (entry,gid),value in scalar.items():
                i,j=locate(entry)
                counter[entry,gid]-=q[i]*q[j]*value
            answer=block(d["root_type"],len(q),counter)
            assert all(core_index not in locate(entry) for entry,_,_ in answer["terms"])
            output[name+"_conditioned"].append(answer)
            saved[name]={"core_diagonal":diag,"cross":q}
        core_data.append({"root_type":d["root_type"],"triangle":list(T),
                          "class_index":core_index,"kernels":saved,
                          "both_core_class_rows_zero_coefficientwise":True})
    assert [x["root_type"] for x in core_data]==[14,15]
    return output,core_data


def construct(data,old,first,scalar,deadline):
    graphs,levels,aut,_=data
    original,root_maps=base.domains_and_root_maps(graphs,levels,aut)
    assert [d["root_type"] for d in original]==ROOTS
    domains=old["domains"]
    labels={d["root_type"]:{full.class_key(c):i for i,c in enumerate(d["classes"])} for d in domains}
    tensors={name:{rid:Counter() for rid in ROOTS} for name in ("minus","plus","scalar","Q")}
    census=Counter()
    samples={}
    for order in range(4,11):
        for graph_id in levels[order]:
            if graph_id%128==0:
                base.check_time(deadline)
            rows=graphs[graph_id]
            triangles=base.triangles(rows)
            for ti,left in enumerate(triangles):
                for right in triangles[:ti+1]:
                    union=set(left)|set(right)
                    extra_count=4+len(union)-order
                    if extra_count<0 or extra_count>min(4,len(union)):
                        continue
                    rest=tuple(v for v in range(order) if v not in union)
                    qm,qp=kernels(rows,left,right)
                    q=base.kernel(rows,left,right)
                    for extra in combinations(sorted(union),extra_count):
                        root=tuple(sorted(rest+extra))
                        assert len(root)==4 and set(root)|union==set(range(order))
                        rid,maps=root_maps[base.graph_code(base.induced(rows,root))]
                        ls,rs=len(set(left)&set(root)),len(set(right)&set(root))
                        tag=str(len(set(left)&set(right)))+":"+str(qm)+":"+str(min(ls,rs))+":"+str(max(ls,rs))
                        samples.setdefault(tag,graph_id)
                        census["unlabelled_root_and_triangle_pair_decompositions"]+=1
                        for p in maps:
                            labelled=tuple(root[i] for i in p)
                            a=labels[rid][full.full_classify(rows,left,labelled)]
                            b=labels[rid][full.full_classify(rows,right,labelled)]
                            if a<b:
                                a,b=b,a
                            multiplier=2 if left!=right and a==b else 1
                            key=(a*(a+1)//2+b,graph_id)
                            for name,value in (("minus",qm),("plus",qp),("scalar",1),("Q",q)):
                                tensors[name][rid][key]+=multiplier*value
                            census["labelled_root_decompositions"]+=1
    families={}
    for name in tensors:
        families[name]=[block(d["root_type"],len(d["classes"]),tensors[name][d["root_type"]]) for d in domains]
    assert families["Q"]==old["blocks"]
    for prior in scalar["blocks"]:
        assert next(b for b in families["scalar"] if b["root_type"]==prior["root_type"])["terms"]==prior["terms"]
    identities=0
    for d,f in zip(domains,first["domains"]):
        rid=d["root_type"]
        diagonal=Counter()
        for i,c in enumerate(f["classes"]):
            diagonal[i*(i+1)//2+i,c["catalogue_type"]]=c["coefficient"]
        allkeys=set(diagonal)
        for name in tensors:
            allkeys.update(tensors[name][rid])
        for key in allkeys:
            lhs=(11*tensors["Q"][rid][key]+110*tensors["minus"][rid][key]
                 +3*tensors["plus"][rid][key]+10*tensors["scalar"][rid][key])
            assert lhs==2310*diagonal[key],(rid,key)
            identities+=1
    derived,core=conditioned(domains,first,families)
    families.update(derived)
    specification={"schema":"conway99.triangle-vertex-projectors.v1",
        "catalogue_sha256":base.CATALOGUE_SHA,"domains":domains,"families":families,
        "conditioned_core_data":core,
        "kernel_entries":{"minus":{"diagonal":4,"intersection":0,"disjoint":"1-e","scale":21,"rank":44},
                          "plus":{"diagonal":180,"intersection":70,"disjoint":"11e-18","scale":770,"rank":54}},
        "normalization":"Every unlabelled triangle pair and labelled root map in each induced graph; off-diagonal class entries once, equal-class distinct triangles twice. Coefficients multiply unlabelled induced counts.",
        "query_families":["minus","plus","minus_conditioned","plus_conditioned"],
        "coefficientwise_projector_partition_identities":identities,
        "old_Q_full_tensor_reconstructed_exactly":True,
        "old_two_scalar_tensors_reconstructed_exactly":True,
        "all_574_triangle_classes_retained":True,
        "census":dict(census),"control_graph_ids":samples,
        "count_point_loaded":False,"optimizer_called":False}
    return specification,root_maps


def factorization_control(rows,triangles):
    checked=0
    for T in triangles:
        for U in triangles:
            qm,qp=kernels(rows,T,U)
            minus=sum(27*int(a==b)-9*((rows[a]>>b)&1)+1 for a in T for b in U)
            plus=sum(44*int(a==b)+11*((rows[a]>>b)&1)-2 for a in T for b in U)
            assert minus==9*qm and plus==qp
            assert 11*base.kernel(rows,T,U)+110*qm+3*qp+10==2310*int(T==U)
            checked+=1
    return checked


def direct_host(rows,specification,root_maps):
    families=specification["query_families"]+["scalar","Q"]
    out={name:{b["root_type"]:[[0]*b["order"] for _ in range(b["order"])]
               for b in specification["families"][name]} for name in families}
    labels={d["root_type"]:{full.class_key(c):i for i,c in enumerate(d["classes"])}
            for d in specification["domains"]}
    ts=base.triangles(rows)
    embeds=pairs=0
    factor=factorization_control(rows,ts)
    for chosen in combinations(range(len(rows)),4):
        rid,maps=root_maps[base.graph_code(base.induced(rows,chosen))]
        for p in maps:
            root=tuple(chosen[i] for i in p)
            types=[labels[rid][full.full_classify(rows,T,root)] for T in ts]
            contained=[T for T in ts if set(T)<=set(root)]
            assert len(contained)<=1
            for i,T in enumerate(ts):
                for j,U in enumerate(ts):
                    qm,qp=kernels(rows,T,U)
                    for name,value in (("minus",qm),("plus",qp),("scalar",1),("Q",base.kernel(rows,T,U))):
                        out[name][rid][types[i]][types[j]]+=value
                    if contained:
                        vm,vp=kernels(rows,contained[0],T)
                        wm,wp=kernels(rows,contained[0],U)
                        out["minus_conditioned"][rid][types[i]][types[j]]+=4*qm-vm*wm
                        out["plus_conditioned"][rid][types[i]][types[j]]+=180*qp-vp*wp
                    pairs+=1
            embeds+=1
    return out,embeds,pairs,factor


def controls(data,specification,root_maps,deadline):
    graphs,levels,_,_=data
    lookup={(len(graphs[i]),pynauty.certificate(base.nauty(graphs[i]))):i
            for n in range(4,11) for i in levels[n]}
    reports=[]
    hosts=sorted(set(specification["control_graph_ids"].values())|set(ROOTS))
    for gid in hosts:
        base.check_time(deadline)
        rows=graphs[gid]
        counts=[0]*len(graphs)
        for n in range(4,len(rows)+1):
            for vertices in combinations(range(len(rows)),n):
                pos=gid if n==len(rows) else lookup[n,pynauty.certificate(base.nauty(base.induced(rows,vertices)))]
                counts[pos]+=1
        actual,embeds,pairs,factor=direct_host(rows,specification,root_maps)
        for name in actual:
            assert actual[name]==base.contract({"blocks":specification["families"][name]},counts),(gid,name)
        reports.append({"host_type":gid,"order":len(rows),"labelled_root_embeddings":embeds,
                        "ordered_triangle_pairs":pairs,"literal_factorization_checks":factor,
                        "all_families_equal":True})
    assert any(r["order"]==10 and r["ordered_triangle_pairs"] for r in reports)
    return reports


def prepare(args):
    assert 0<args.seconds<=120 and not args.directory.exists()
    start=time.monotonic();deadline=start+args.seconds
    report={"status":"INCOMPLETE","source_sha256":base.digest(Path(__file__).read_bytes()),
        "base_source_sha256":BASE_SHA,"full_source_sha256":FULL_SHA,
        "parent_full_preparation_sha256":FULL_PREP_SHA,"parent_full_raw_sha256":FULL_RAW_SHA,
        "first_moments_sha256":FIRST_SHA,"scalar_raw_sha256":SCALAR_RAW_SHA,
        "count_point_loaded":False,"optimizer_called":False,"query_requires_separate_gate":True}
    args.directory.mkdir(parents=True)
    try:
        old,first,scalar=load_inputs(args)
        data=base.load_catalogue(args.catalogue)
        specification,maps=construct(data,old,first,scalar,deadline)
        raw=base.canonical(specification);compressed=gzip.compress(raw,mtime=0)
        (args.directory/"model.json.gz").write_bytes(compressed)
        report.update(model_raw_sha256=base.digest(raw),model_gzip_sha256=base.digest(compressed),
                      model_raw_bytes=len(raw),model_gzip_bytes=len(compressed),
                      block_orders=ORDERS,classes=574,query_blocks=22,
                      family_block_counts={name:len(b) for name,b in specification["families"].items()},
                      family_tensor_nonzeros={name:sum(len(b["terms"]) for b in blocks) for name,blocks in specification["families"].items()},
                      coefficientwise_projector_partition_identities=specification["coefficientwise_projector_partition_identities"],
                      old_Q_full_tensor_reconstructed_exactly=True,
                      old_two_scalar_tensors_reconstructed_exactly=True,
                      all_574_triangle_classes_retained=True)
        checks=controls(data,specification,maps,deadline)
        base.check_time(deadline)
        report.update(status="COMPLETE_POINT_INDEPENDENT_TRIANGLE_VERTEX_PROJECTOR_PREPARATION",
                      small_host_controls=checks,all_conditioned_core_rows_zero_coefficientwise=True,
                      complete_query_family_coverage=True)
    except Exception as error:
        report.update(status="INCOMPLETE_NO_WHOLE_MODEL_CLAIM",error_type=type(error).__name__,error_message=str(error))
        raise
    finally:
        report["seconds"]=time.monotonic()-start
        (args.directory/"preparation.json").write_text(json.dumps(report,indent=2)+"\n")
        print(json.dumps({k:v for k,v in report.items() if k!="small_host_controls"},indent=2),flush=True)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--catalogue",type=Path,required=True)
    p.add_argument("--full-directory",type=Path,required=True)
    p.add_argument("--first-moments",type=Path,required=True)
    p.add_argument("--scalar-model",type=Path,required=True)
    p.add_argument("--directory",type=Path,required=True)
    p.add_argument("--seconds",type=float,default=120)
    prepare(p.parse_args())


if __name__=="__main__":
    main()
