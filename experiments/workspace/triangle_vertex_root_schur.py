"""Condition the two complete triangle kernels on all four root vertices.

Only exact affine combinations of the frozen K and scalar N tensors are
formed. No catalogue product census or count-point query is performed.
"""
import argparse
from collections import Counter
import gzip
from math import gcd,lcm
import json
from pathlib import Path
import time

from flint import fmpq_mat,fmpz_mat
import pynauty

import triangle_incidence_projector_moments as base
import triangle_incidence_projector_full_classes as full
import triangle_vertex_projector_moments as prior

PRIOR_SOURCE_SHA="fea5b560e4aeeb323da6e8cde2bc52571a3dc7499f0900a0a12b1f134d4a31c7"
PRIOR_PREP_SHA="71d57c17d2c1e6b034b6511206246db3fc3abd6046bf40d992e447887163f29c"
PRIOR_RAW_SHA="c71ff13d3ac029d44d656e7a7468d7871ce499ec28cc7a2b1a7c7dd11fc9a8f9"
PRIOR_GZIP_SHA="7dfb0f2d60e81c920d38d8b3c558c9e57ec326ab97010ede251689f284907149"


def load_parent(directory):
    assert base.digest(Path(prior.__file__).read_bytes())==PRIOR_SOURCE_SHA
    assert base.digest(Path(base.__file__).read_bytes())==prior.BASE_SHA
    assert base.digest(Path(full.__file__).read_bytes())==prior.FULL_SHA
    raw=(directory/"preparation.json").read_bytes()
    assert base.digest(raw)==PRIOR_PREP_SHA
    report=json.loads(raw)
    assert report["complete_query_family_coverage"]
    packed=(directory/"model.json.gz").read_bytes()
    assert base.digest(packed)==PRIOR_GZIP_SHA
    raw=gzip.decompress(packed)
    assert base.digest(raw)==PRIOR_RAW_SHA
    model=json.loads(raw)
    assert model["all_574_triangle_classes_retained"]
    assert [d["root_type"] for d in model["domains"]]==prior.ROOTS
    return model,report


def inverse_record(root,name):
    d,e,c=(27,-9,1) if name=="minus" else (44,11,-2)
    G=[[d*int(i==j)+e*((root[i]>>j)&1)+c for j in range(4)] for i in range(4)]
    minors=[int(fmpz_mat([row[:k] for row in G[:k]]).det()) for k in range(1,5)]
    assert all(x>0 for x in minors)
    inverse=fmpq_mat(G).inv()
    den=lcm(*(int(q.q) for q in inverse.entries()))
    numerator=[[int(inverse[i,j]*den) for j in range(4)] for i in range(4)]
    assert den>0 and numerator==list(map(list,zip(*numerator)))
    assert all(sum(G[i][k]*numerator[k][j] for k in range(4))==den*int(i==j)
               for i in range(4) for j in range(4))
    return {"gram":G,"positive_leading_minors":minors,
            "inverse_numerator":numerator,"inverse_denominator":den,
            "triangle_kernel_divisor":9 if name=="minus" else 1}


def form_record(domain,name):
    root=tuple(domain["root_rows"]);inv=inverse_record(root,name)
    d,e,c=(27,-9,1) if name=="minus" else (44,11,-2)
    crosses=[];core_indices=[]
    for i,cl in enumerate(domain["classes"]):
        rows=full.extension(root,*full.class_key(cl))
        assert rows is not None and base.cap_valid(rows)
        T=tuple(v for v in range(4) if cl["root_intersection_mask"]&(1<<v))+tuple(range(4,len(rows)))
        values=[d*int(j in T)+e*sum((rows[j]>>v)&1 for v in T)+3*c for j in range(4)]
        literal=[sum(d*int(j==v)+e*((rows[j]>>v)&1)+c for v in T) for j in range(4)]
        assert values==literal
        crosses.append(values)
        if not cl["outside_masks"]:
            core_indices.append(i)
    P=inv["inverse_numerator"]
    products=[]
    for a,x in enumerate(crosses):
        for y in crosses[:a+1]:
            products.append(sum(x[i]*P[i][j]*y[j] for i in range(4) for j in range(4)))
    raw_scale=inv["triangle_kernel_divisor"]*inv["inverse_denominator"]
    common=raw_scale
    for value in products:
        common=gcd(common,abs(value))
    assert common>0 and all(v%common==0 for v in products)
    out={"root_type":domain["root_type"],"family":name,**inv,
         "crosses":crosses,"common_divisor":common,"kernel_scale":raw_scale//common,
         "correction_lower":[v//common for v in products],"core_triangle_class_indices":core_indices}
    # Exact nesting control: projection on a contained triangle lies
    # inside the root span. The unscaled 4x4 difference is PSD.
    nesting=[]
    for T in base.triangles(root):
        z=[int(i in T) for i in range(4)]
        t=sum(z[i]*inv["gram"][i][j]*z[j] for i in range(4) for j in range(4))
        assert t>0
        D=[[t*P[i][j]-inv["inverse_denominator"]*z[i]*z[j] for j in range(4)] for i in range(4)]
        cp=list(map(int,fmpz_mat([[-v for v in row] for row in D]).charpoly()))
        assert all(v>=0 for v in cp)
        nesting.append({"core_triangle":list(T),"root_gram_norm":t,
                        "projection_difference_matrix":D,"det_tI_plus_coefficients":cp})
    out["core_triangle_projection_nesting_controls"]=nesting
    return out


def construct(parent,deadline):
    domains=parent["domains"];families={"minus":[],"plus":[]};records=[]
    for name in families:
        for domain in domains:
            base.check_time(deadline)
            rid=domain["root_type"];record=form_record(domain,name);records.append(record)
            K=next(b for b in parent["families"][name] if b["root_type"]==rid)
            N=next(b for b in parent["families"]["scalar"] if b["root_type"]==rid)
            scale=record["kernel_scale"];correction=record["correction_lower"]
            answer=Counter({key:scale*value for key,value in prior.as_counter(K).items()})
            for entry,gid,value in N["terms"]:
                answer[entry,gid]-=correction[entry]*value
            out=prior.block(rid,K["order"],answer)
            zeros=set(record["core_triangle_class_indices"])
            assert all(not zeros.intersection(prior.locate(entry)) for entry,_,_ in out["terms"])
            out["all_core_triangle_rows_zero_coefficientwise"]=True
            families[name].append(out)
    assert len(records)==18
    return {"schema":"conway99.triangle-root-vertex-schur.v1","domains":domains,
            "families":families,"exact_root_forms":records,
            "parent_raw_sha256":PRIOR_RAW_SHA,"all_574_classes_retained":True,
            "new_catalogue_product_census":False,"count_point_loaded":False,
            "normalization":"A positive exact multiple of the per-embedding root-vertex Schur residual. Full scalar N_CD multiplies each root-cross inverse product.",
            "optimizer_called":False}


def host_controls(data,parent,prepared,parent_report,deadline):
    graphs,levels,aut,_=data
    _,maps=base.domains_and_root_maps(graphs,levels,aut)
    lookup={(len(graphs[i]),pynauty.certificate(base.nauty(graphs[i]))):i
            for n in range(4,11) for i in levels[n]}
    records=[]
    for control in parent_report["small_host_controls"]:
        base.check_time(deadline)
        gid=control["host_type"];rows=graphs[gid]
        direct,embeddings,pairs,_=prior.direct_host(rows,parent,maps)
        counts=[0]*len(graphs)
        from itertools import combinations
        for n in range(4,len(rows)+1):
            for vertices in combinations(range(len(rows)),n):
                pos=gid if n==len(rows) else lookup[n,pynauty.certificate(base.nauty(base.induced(rows,vertices)))]
                counts[pos]+=1
        for name,blocks in prepared["families"].items():
            reconstructed=base.contract({"blocks":blocks},counts)
            for block in blocks:
                rid=block["root_type"]
                form=next(r for r in prepared["exact_root_forms"] if r["family"]==name and r["root_type"]==rid)
                K=direct[name][rid];N=direct["scalar"][rid]
                expected=[[form["kernel_scale"]*K[a][b]-form["correction_lower"][max(a,b)*(max(a,b)+1)//2+min(a,b)]*N[a][b]
                           for b in range(len(K))] for a in range(len(K))]
                assert expected==reconstructed[rid],(name,rid,gid)
        records.append({"host_type":gid,"order":len(rows),"all_18_schur_blocks_equal":True,
                        "direct_labelled_embeddings":embeddings,"direct_ordered_triangle_pairs":pairs})
    return records


def prepare(args):
    assert 0<args.seconds<=60 and not args.directory.exists()
    start=time.monotonic();deadline=start+args.seconds
    report={"status":"INCOMPLETE","source_sha256":base.digest(Path(__file__).read_bytes()),
            "parent_source_sha256":PRIOR_SOURCE_SHA,"parent_preparation_sha256":PRIOR_PREP_SHA,
            "parent_model_raw_sha256":PRIOR_RAW_SHA,"count_point_loaded":False,
            "new_catalogue_product_census":False,"optimizer_called":False,
            "point_query_requires_separate_gate":True}
    args.directory.mkdir(parents=True)
    try:
        parent,parent_report=load_parent(args.parent_directory)
        specification=construct(parent,deadline)
        data=base.load_catalogue(args.catalogue)
        checks=host_controls(data,parent,specification,parent_report,deadline)
        base.check_time(deadline)
        raw=base.canonical(specification);packed=gzip.compress(raw,mtime=0)
        (args.directory/"model.json.gz").write_bytes(packed)
        report.update(status="COMPLETE_POINT_INDEPENDENT_TRIANGLE_ROOT_VERTEX_SCHUR_PREPARATION",
                      model_raw_sha256=base.digest(raw),model_gzip_sha256=base.digest(packed),
                      model_raw_bytes=len(raw),model_gzip_bytes=len(packed),families=2,blocks=18,
                      complete_18_block_coverage=True,distinct_classes=574,
                      positive_root_Gram_leading_minors=72,exact_inverse_entry_checks=288,
                      literal_root_cross_entry_checks=sum(4*len(r["crosses"]) for r in specification["exact_root_forms"]),
                      exact_lower_correction_products=sum(len(r["correction_lower"]) for r in specification["exact_root_forms"]),
                      tensor_nonzeros={name:sum(len(b["terms"]) for b in blocks) for name,blocks in specification["families"].items()},
                      kernel_scales=[r["kernel_scale"] for r in specification["exact_root_forms"]],
                      core_triangle_nesting_controls=sum(len(r["core_triangle_projection_nesting_controls"]) for r in specification["exact_root_forms"]),
                      small_host_controls=checks)
    except Exception as error:
        report.update(status="INCOMPLETE_NO_COMPLETE_MODEL_CLAIM",error_type=type(error).__name__,error_message=str(error))
        raise
    finally:
        report["seconds"]=time.monotonic()-start
        (args.directory/"preparation.json").write_text(json.dumps(report,indent=2)+"\n")
        print(json.dumps({k:v for k,v in report.items() if k!="small_host_controls"},indent=2))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--parent-directory",type=Path,required=True)
    p.add_argument("--catalogue",type=Path,required=True)
    p.add_argument("--directory",type=Path,required=True)
    p.add_argument("--seconds",type=float,default=60)
    prepare(p.parse_args())


if __name__=="__main__":
    main()
