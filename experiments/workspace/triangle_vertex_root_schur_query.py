"""One exact query for all eighteen root-vertex-conditioned triangle blocks."""
import argparse
import gzip
import json
from pathlib import Path
import time

import triangle_incidence_projector_moments as base
import triangle_projector_conditioned_query as arithmetic

BINDINGS={
 "base_source":"1e7a8b7380314d6dfd8ff05954a13662bc011378f5759ad675ec1bc281fa19e9",
 "arithmetic_source":"cd167c52b7b646a64e4faf58816212d427d1c280a45070e77a5eb8b0a29abb43",
 "builder_source":"8eee12ffbb5f78e82f52c3ab67f67c43f5b0d8fbaede98ab1c8e74f878312174",
 "preparation":"584fde1b12dad1c6e2234de53a4ab648eb82363558b1ee42eb267f624f753f74",
 "model_raw":"fbb248ba4f0c2071384f4b46e1823387c231905950387161f9edfffb71b6e52b",
 "model_gzip":"3774933c475f5fab09f8c8f693e2d9cc1902e69e7467f85b01b7fdec9b22ab44",
 "point":"0b78eb2cfc0966f66d72b083f71315e4a079e4b25f59f276c58dd93d189b49df"
}
FAMILIES=["minus","plus"]
ORDERS=[107,93,72,49,79,58,41,34,41]


def inputs(directory,point):
    assert base.digest(Path(base.__file__).read_bytes())==BINDINGS["base_source"]
    assert base.digest(Path(arithmetic.__file__).read_bytes())==BINDINGS["arithmetic_source"]
    source=Path(__file__).with_name("triangle_vertex_root_schur.py")
    assert base.digest(source.read_bytes())==BINDINGS["builder_source"]
    raw=(directory/"preparation.json").read_bytes()
    assert base.digest(raw)==BINDINGS["preparation"]
    prep=json.loads(raw)
    assert prep["complete_18_block_coverage"] and prep["blocks"]==18
    compressed=(directory/"model.json.gz").read_bytes()
    assert base.digest(compressed)==BINDINGS["model_gzip"]==prep["model_gzip_sha256"]
    raw=gzip.decompress(compressed)
    assert base.digest(raw)==BINDINGS["model_raw"]==prep["model_raw_sha256"]
    model=json.loads(raw)
    assert model["all_574_classes_retained"] and list(model["families"])==FAMILIES
    assert [d["root_type"] for d in model["domains"]]==list(range(8,17))
    assert [len(d["classes"]) for d in model["domains"]]==ORDERS
    for name in FAMILIES:
        blocks=model["families"][name]
        assert [b["root_type"] for b in blocks]==list(range(8,17))
        assert [b["order"] for b in blocks]==ORDERS
    assert [(r["family"],r["root_type"]) for r in model["exact_root_forms"]]==[(f,r) for f in FAMILIES for r in range(8,17)]
    raw=point.read_bytes()
    assert base.digest(raw)==BINDINGS["point"]
    counts=json.loads(raw)["induced_counts"]
    assert len(counts)==48965 and all(type(c)is int and c>=0 for c in counts)
    return model,counts


def kernel_checks(model,name,root_id,matrix):
    domain=next(d for d in model["domains"] if d["root_type"]==root_id)
    form=next(r for r in model["exact_root_forms"] if r["family"]==name and r["root_type"]==root_id)
    stars=[]
    for vertex in range(4):
        chosen=[i for i,c in enumerate(domain["classes"]) if c["root_intersection_mask"]&(1<<vertex)]
        stars.append(all(sum(row[i] for i in chosen)==0 for row in matrix))
    return {"constant_vector_zero":all(sum(row)==0 for row in matrix),
            "all_four_root_point_stars_zero":all(stars),
            "all_core_triangle_rows_zero":all(all(x==0 for x in matrix[i])
                                              for i in form["core_triangle_class_indices"])}

def query(args):
    assert 0<args.seconds<=30 and not args.output.exists()
    start=time.monotonic();deadline=start+args.seconds
    model,counts=inputs(args.directory,args.point)
    report={"status":"INCOMPLETE","source_sha256":base.digest(Path(__file__).read_bytes()),
            "bindings":BINDINGS,"blocks":[],"complete_18_block_coverage":False,
            "all_574_triangle_classes_retained":True,
            "optimizer_called":False,"graph_existence_resolved":False}
    try:
        for name in FAMILIES:
            matrices=base.contract({"blocks":model["families"][name]},counts)
            for block in model["families"][name]:
                base.check_time(deadline)
                rid=block["root_type"];M=matrices[rid]
                checked=kernel_checks(model,name,rid,M)
                assert all(checked.values())
                polynomial=arithmetic.characteristic(M)
                positive=all(x>=0 for x in polynomial)
                record={"family":name,"root_type":rid,"order":len(M),
                        "matrix":[list(map(str,row)) for row in M],
                        "det_tI_plus_matrix_coefficients":list(map(str,polynomial)),
                        "exact_positive_semidefinite":positive,"kernel_checks":checked}
                report["blocks"].append(record)
                if not positive:
                    vector,value=base.exact_negative_vector(M,deadline)
                    form,primitive,reconstructed=arithmetic.vector_form(block,vector,counts)
                    assert reconstructed==value<0
                    record.update(integer_negative_vector=list(map(str,vector)),quadratic_value=str(value),
                                  primitive_induced_count_inequality=form,primitive_value=primitive)
        base.check_time(deadline)
        assert len(report["blocks"])==18
        report["complete_18_block_coverage"]=True
        report["status"]=("EXACT_ALL_18_TRIANGLE_ROOT_VERTEX_SCHUR_BLOCKS_PSD"
                          if all(b["exact_positive_semidefinite"] for b in report["blocks"])
                          else "EXACT_TRIANGLE_ROOT_VERTEX_SCHUR_SEPARATOR")
    except Exception as error:
        report.update(status="INCOMPLETE_NO_WHOLE_MODEL_CONCLUSION",
                      error_type=type(error).__name__,error_message=str(error))
        raise
    finally:
        report["seconds"]=time.monotonic()-start
        args.output.write_text(json.dumps(report,indent=2)+"\n")
        print(json.dumps({k:v for k,v in report.items() if k!="blocks"},indent=2))


def replay(args):
    assert not args.output.exists()
    start=time.monotonic()
    model,counts=inputs(args.directory,args.point)
    raw=args.result.read_bytes();saved=json.loads(raw)
    assert saved["source_sha256"]==base.digest(Path(__file__).read_bytes())
    assert saved["bindings"]==BINDINGS and saved["complete_18_block_coverage"]
    assert len(saved["blocks"])==18
    records=[];position=0
    for name in FAMILIES:
        matrices=base.contract({"blocks":model["families"][name]},counts)
        for block in model["families"][name]:
            item=saved["blocks"][position];position+=1
            rid=block["root_type"];M=matrices[rid]
            assert item["family"]==name and item["root_type"]==rid and item["order"]==len(M)
            assert M==[[int(x) for x in row] for row in item["matrix"]]
            checked=kernel_checks(model,name,rid,M)
            assert checked==item["kernel_checks"] and all(checked.values())
            polynomial=arithmetic.characteristic(M)
            assert polynomial==list(map(int,item["det_tI_plus_matrix_coefficients"]))
            positive=all(x>=0 for x in polynomial)
            assert positive==item["exact_positive_semidefinite"]
            record={"family":name,"root_type":rid,"order":len(M),
                    "exact_positive_semidefinite":positive,"kernel_checks":checked}
            if positive:
                record["nullity"]=next(i for i,c in enumerate(polynomial) if c)
            else:
                vector=list(map(int,item["integer_negative_vector"]))
                assert len(vector)==len(M)
                value=sum(vector[i]*M[i][j]*vector[j] for i in range(len(M)) for j in range(len(M)))
                form,primitive,reconstructed=arithmetic.vector_form(block,vector,counts)
                assert value==reconstructed==int(item["quadratic_value"])<0
                assert form==item["primitive_induced_count_inequality"]
                assert primitive==item["primitive_value"]
                record["primitive_value"]=primitive
            records.append(record)
    expected=("EXACT_ALL_18_TRIANGLE_ROOT_VERTEX_SCHUR_BLOCKS_PSD"
              if all(b["exact_positive_semidefinite"] for b in records)
              else "EXACT_TRIANGLE_ROOT_VERTEX_SCHUR_SEPARATOR")
    assert saved["status"]==expected
    report={"status":"PASS_EXACT_TRIANGLE_ROOT_VERTEX_SCHUR_QUERY_REPLAY",
            "source_sha256":base.digest(Path(__file__).read_bytes()),
            "bindings":BINDINGS,"result_sha256":base.digest(raw),"blocks":records,
            "complete_18_block_coverage":True,"tensor_generation_repeated":False,
            "optimizer_called":False,"seconds":time.monotonic()-start}
    args.output.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode",choices=["query","replay"])
    p.add_argument("--directory",type=Path,required=True)
    p.add_argument("--point",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--result",type=Path)
    p.add_argument("--seconds",type=float,default=30)
    a=p.parse_args()
    if a.mode=="query":
        query(a)
    else:
        assert a.result
        replay(a)


if __name__=="__main__":
    main()
