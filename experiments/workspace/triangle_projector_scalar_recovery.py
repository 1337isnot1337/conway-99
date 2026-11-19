"""Recover two complete scalar triangle-class moment tensors.

For a core triangle T, every class value d_C=Q(T,U) is nonzero, so
N_CD=(120 M_Q,CD-M_conditioned,CD)/(d_C*d_D) coefficientwise.
This is a direct certificate for a scalar family contained in the span
of the complete induced r=4,s=3 flag moment family.
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
import triangle_projector_conditioned_query as arithmetic

BASE_SHA = "1e7a8b7380314d6dfd8ff05954a13662bc011378f5759ad675ec1bc281fa19e9"
FULL_SHA = "d26499a0eec07c2c80a28818f0a40319fc0b14f54140a28253c820eb00d44f2a"
ARITHMETIC_SHA = "cd167c52b7b646a64e4faf58816212d427d1c280a45070e77a5eb8b0a29abb43"
FULL_RAW_SHA = "819aa1954ce038865404433995eb401ad7111cad0a21992f4ba8c42e3e04687c"
CONDITIONED_RAW_SHA = "8bd186531a14656a2ecf06857742532b26ff53fa3fb4f75cc2b6bd8322e51ef6"
FIRST_MOMENTS_SHA = "3c3b957f6cfaebafa448804d9c61759b3a0fc448c484a7b590095f831ecc6184"


def checks():
    assert base.digest(Path(base.__file__).read_bytes()) == BASE_SHA
    assert base.digest(Path(full.__file__).read_bytes()) == FULL_SHA
    assert base.digest(Path(arithmetic.__file__).read_bytes()) == ARITHMETIC_SHA


def model_at(directory, expected):
    report = json.loads((directory/"preparation.json").read_text())
    compressed = (directory/"model.json.gz").read_bytes()
    assert base.digest(compressed) == report["model_gzip_sha256"]
    raw = gzip.decompress(compressed)
    assert base.digest(raw) == expected == report["model_raw_sha256"]
    return json.loads(raw)


def construct(parent, conditioned, first):
    parents = {b["root_type"]: b for b in parent["blocks"]}
    parent_domains = {d["root_type"]: d for d in parent["domains"]}
    first_domains = {d["root_type"]: d for d in first["domains"]}
    blocks = []
    divisibility = 0
    constant_rows = 0
    for domain, block in zip(conditioned["domains"], conditioned["blocks"]):
        root_id = block["root_type"]
        assert domain["classes"] == parent_domains[root_id]["classes"]
        values = domain["fixed_triangle_cross_values"]
        assert len(values) == block["order"] and all(values)
        for c, saved in zip(domain["classes"], values):
            rows = full.extension(domain["root_rows"], *full.class_key(c))
            triangle = tuple(i for i in range(4) if c["root_intersection_mask"] & (1 << i)) + tuple(range(4,len(rows)))
            assert base.kernel(rows, tuple(domain["fixed_triangle"]), triangle) == saved
        acc = Counter()
        for entry, graph_id, coefficient in parents[root_id]["terms"]:
            acc[entry, graph_id] += 120*coefficient
        for entry, graph_id, coefficient in block["terms"]:
            acc[entry, graph_id] -= coefficient
        terms = []
        for (entry, graph_id), numerator in sorted(acc.items()):
            i, j = arithmetic.location(entry)
            divisor = values[i]*values[j]
            assert numerator % divisor == 0
            coefficient = numerator//divisor
            assert coefficient >= 0
            divisibility += 1
            if coefficient:
                terms.append([entry, graph_id, coefficient])
        by_entry = {}
        for entry, graph_id, coefficient in terms:
            by_entry.setdefault(entry, {})[graph_id] = coefficient
        fixed = domain["fixed_triangle_class"]
        for i, first_form in enumerate(first_domains[root_id]["classes"]):
            a,b = max(i,fixed),min(i,fixed)
            assert by_entry.get(a*(a+1)//2+b,{}) == {
                first_form["catalogue_type"]: first_form["coefficient"]}
            constant_rows += 1
        blocks.append({"root_type": root_id, "order": block["order"],
                       "lower_entries": block["lower_entries"], "terms": terms})
    return {"schema":"conway99.triangle-class-scalar-recovery.v1",
            "parent_full_Q_raw_sha256":FULL_RAW_SHA,
            "conditioned_raw_sha256":CONDITIONED_RAW_SHA,
            "first_moments_sha256":FIRST_MOMENTS_SHA,
            "domains":conditioned["domains"], "blocks":blocks,
            "coefficientwise_exact_divisions":divisibility,
            "all_scalar_tensor_coefficients_nonnegative":True,
            "constant_row_first_moment_form_identities":constant_rows,
            "all_full_class_domains_retained":True, "count_point_loaded":False,
            "new_pair_products_enumerated":False}


def direct_gram(rows, specification, root_maps):
    matrices={d["root_type"]:[[0]*len(d["classes"]) for _ in d["classes"]]
              for d in specification["domains"]}
    maps={d["root_type"]:{full.class_key(c):i for i,c in enumerate(d["classes"])}
          for d in specification["domains"]}
    ts=base.triangles(rows)
    embeddings=0
    for root in combinations(range(len(rows)),4):
        root_id,transports=root_maps[base.graph_code(base.induced(rows,root))]
        if root_id not in maps:
            continue
        for transport in transports:
            labelled=tuple(root[i] for i in transport)
            counts=Counter(maps[root_id][full.full_classify(rows,t,labelled)] for t in ts)
            M=matrices[root_id]
            for i,a in counts.items():
                for j,b in counts.items():
                    M[i][j]+=a*b
            embeddings+=1
    return matrices,embeddings


def controls(data,specification,deadline):
    graphs,levels,aut,_=data
    _,root_maps=base.domains_and_root_maps(graphs,levels,aut)
    lookup={(len(graphs[i]),pynauty.certificate(base.nauty(graphs[i]))):i
            for n in range(4,10) for i in levels[n]}
    hosts=[i for n in range(4,8) for i in levels[n]]
    hosts += [39980,39983,43703,45101,48916,48963]
    report=[]
    for graph_id in hosts:
        base.check_time(deadline)
        rows=graphs[graph_id]
        counts=[0]*len(graphs)
        for size in range(4,len(rows)+1):
            for subset in combinations(range(len(rows)),size):
                pos=graph_id if size==len(rows) else lookup[size,pynauty.certificate(base.nauty(base.induced(rows,subset)))]
                counts[pos]+=1
        actual,embeddings=direct_gram(rows,specification,root_maps)
        computed=base.contract(specification,counts)
        assert actual==computed,(graph_id,"literal scalar Gram")
        report.append({"host_type":graph_id,"order":len(rows),
                       "labelled_root_embeddings":embeddings,
                       "both_full_scalar_blocks_equal":True,
                       "matrix_digest":base.digest(base.canonical(actual))})
    assert len(report)==306
    return report


def prepare(args):
    assert 0<args.seconds<=60 and not args.directory.exists()
    start=time.monotonic();deadline=start+args.seconds
    checks()
    parent=model_at(args.full_directory,FULL_RAW_SHA)
    conditioned=model_at(args.conditioned_directory,CONDITIONED_RAW_SHA)
    raw=args.first_moments.read_bytes()
    assert base.digest(raw)==FIRST_MOMENTS_SHA
    specification=construct(parent,conditioned,json.loads(raw))
    data=base.load_catalogue(args.catalogue)
    host_controls=controls(data,specification,deadline)
    base.check_time(deadline)
    raw=base.canonical(specification)
    compressed=gzip.compress(raw,mtime=0)
    args.directory.mkdir(parents=True)
    (args.directory/"model.json.gz").write_bytes(compressed)
    report={"status":"COMPLETE_POINT_INDEPENDENT_SCALAR_TRIANGLE_RECOVERY",
            "source_sha256":base.digest(Path(__file__).read_bytes()),
            "base_source_sha256":BASE_SHA,"full_source_sha256":FULL_SHA,
            "arithmetic_source_sha256":ARITHMETIC_SHA,
            "model_raw_sha256":base.digest(raw),"model_gzip_sha256":base.digest(compressed),
            "model_raw_bytes":len(raw),"model_gzip_bytes":len(compressed),
            "parent_full_Q_raw_sha256":FULL_RAW_SHA,"conditioned_raw_sha256":CONDITIONED_RAW_SHA,
            "first_moments_sha256":FIRST_MOMENTS_SHA,"catalogue_sha256":base.CATALOGUE_SHA,
            "block_orders":[b["order"] for b in specification["blocks"]],
            "tensor_nonzeros":sum(len(b["terms"]) for b in specification["blocks"]),
            "coefficientwise_exact_divisions":specification["coefficientwise_exact_divisions"],
            "constant_row_first_moment_form_identities":specification["constant_row_first_moment_form_identities"],
            "small_host_controls":host_controls,"count_point_loaded":False,
            "new_pair_products_enumerated":False,"optimizer_called":False,
            "seconds":time.monotonic()-start}
    (args.directory/"preparation.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps({k:v for k,v in report.items() if k!="small_host_controls"},indent=2))


def inputs(args):
    checks()
    raw=(args.directory/"preparation.json").read_bytes()
    prep=json.loads(raw)
    assert prep["source_sha256"]==base.digest(Path(__file__).read_bytes())
    specification=model_at(args.directory,prep["model_raw_sha256"])
    assert [b["order"] for b in specification["blocks"]]==[41,34]
    assert specification["parent_full_Q_raw_sha256"]==FULL_RAW_SHA
    assert specification["conditioned_raw_sha256"]==CONDITIONED_RAW_SHA
    point_raw=args.point.read_bytes()
    assert base.digest(point_raw)==base.POINT_SHA
    counts=json.loads(point_raw)["induced_counts"]
    assert len(counts)==48965 and all(type(x)is int and x>=0 for x in counts)
    return specification,counts,base.digest(raw),prep["model_raw_sha256"]


def query(args):
    assert 0<args.seconds<=30 and not args.output.exists()
    start=time.monotonic();deadline=start+args.seconds
    specification,counts,prep_sha,model_sha=inputs(args)
    terminal={"status":"INCOMPLETE","source_sha256":base.digest(Path(__file__).read_bytes()),
              "preparation_sha256":prep_sha,"model_raw_sha256":model_sha,
              "point_sha256":base.POINT_SHA,"blocks":[],"complete_two_block_coverage":False,
              "optimizer_called":False,"unrestricted_existence_resolved":False}
    try:
        matrices=base.contract(specification,counts)
        for block in specification["blocks"]:
            base.check_time(deadline)
            M=matrices[block["root_type"]]
            cp=arithmetic.characteristic(M)
            positive=all(c>=0 for c in cp)
            record={"root_type":block["root_type"],"order":len(M),
                    "matrix":[list(map(str,row)) for row in M],
                    "det_tI_plus_matrix_coefficients":list(map(str,cp)),
                    "exact_positive_semidefinite":positive}
            if not positive:
                vector,value=base.exact_negative_vector(M,deadline)
                form,primitive,reconstructed=arithmetic.vector_form(block,vector,counts)
                assert reconstructed==value<0
                record.update(integer_negative_vector=list(map(str,vector)),
                              quadratic_value=str(value),primitive_induced_count_inequality=form,
                              primitive_value=primitive)
            terminal["blocks"].append(record)
        base.check_time(deadline)
        terminal["complete_two_block_coverage"]=True
        terminal["status"]=("EXACT_BOTH_FULL_SCALAR_TRIANGLE_BLOCKS_PSD"
                            if all(b["exact_positive_semidefinite"] for b in terminal["blocks"])
                            else "EXACT_SCALAR_TRIANGLE_SEPARATOR")
    except Exception as error:
        terminal.update(status="INCOMPLETE_NO_WHOLE_MODEL_CONCLUSION",
                        error_type=type(error).__name__,error_message=str(error))
        raise
    finally:
        terminal["seconds"]=time.monotonic()-start
        args.output.write_text(json.dumps(terminal,indent=2)+"\n")
        print(json.dumps({k:v for k,v in terminal.items() if k!="blocks"},indent=2))


def replay(args):
    assert not args.output.exists()
    start=time.monotonic()
    specification,counts,prep_sha,model_sha=inputs(args)
    raw=args.result.read_bytes();saved=json.loads(raw)
    assert saved["source_sha256"]==base.digest(Path(__file__).read_bytes())
    assert saved["preparation_sha256"]==prep_sha and saved["model_raw_sha256"]==model_sha
    assert saved["point_sha256"]==base.POINT_SHA and saved["complete_two_block_coverage"]
    assert len(saved["blocks"])==2
    matrices=base.contract(specification,counts)
    records=[]
    for block,item in zip(specification["blocks"],saved["blocks"]):
        assert item["root_type"]==block["root_type"] and item["order"]==block["order"]
        M=matrices[block["root_type"]]
        assert M==[[int(x) for x in row] for row in item["matrix"]]
        cp=arithmetic.characteristic(M)
        assert cp==list(map(int,item["det_tI_plus_matrix_coefficients"]))
        positive=all(c>=0 for c in cp)
        assert positive==item["exact_positive_semidefinite"]
        record={"root_type":block["root_type"],"order":len(M),"exact_positive_semidefinite":positive}
        if positive:
            record["nullity"]=next(i for i,c in enumerate(cp) if c)
        else:
            v=list(map(int,item["integer_negative_vector"]))
            assert len(v)==len(M)
            value=sum(v[i]*M[i][j]*v[j] for i in range(len(M)) for j in range(len(M)))
            form,primitive,reconstructed=arithmetic.vector_form(block,v,counts)
            assert reconstructed==value==int(item["quadratic_value"])<0
            assert form==item["primitive_induced_count_inequality"] and primitive==item["primitive_value"]
            record["primitive_value"]=primitive
        records.append(record)
    expected=("EXACT_BOTH_FULL_SCALAR_TRIANGLE_BLOCKS_PSD" if all(b["exact_positive_semidefinite"] for b in records)
              else "EXACT_SCALAR_TRIANGLE_SEPARATOR")
    assert saved["status"]==expected
    result={"status":"PASS_EXACT_SCALAR_TRIANGLE_QUERY_REPLAY",
            "source_sha256":base.digest(Path(__file__).read_bytes()),"result_sha256":base.digest(raw),
            "model_raw_sha256":model_sha,"preparation_sha256":prep_sha,
            "point_sha256":base.POINT_SHA,"blocks":records,"complete_two_block_coverage":True,
            "tensor_generation_repeated":False,"optimizer_called":False,"seconds":time.monotonic()-start}
    args.output.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode",choices=["prepare","query","replay"])
    p.add_argument("--directory",type=Path,required=True)
    p.add_argument("--full-directory",type=Path)
    p.add_argument("--conditioned-directory",type=Path)
    p.add_argument("--first-moments",type=Path)
    p.add_argument("--catalogue",type=Path)
    p.add_argument("--point",type=Path)
    p.add_argument("--output",type=Path)
    p.add_argument("--result",type=Path)
    p.add_argument("--seconds",type=float,default=30)
    args=p.parse_args()
    if args.mode=="prepare":
        assert args.full_directory and args.conditioned_directory and args.first_moments and args.catalogue
        prepare(args)
    elif args.mode=="query":
        assert args.point and args.output
        query(args)
    else:
        assert args.point and args.output and args.result
        replay(args)


if __name__=="__main__":
    main()
