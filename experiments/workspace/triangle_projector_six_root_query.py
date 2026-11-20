"""Bounded exact query and replay for all thirty six-root triangle blocks."""
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
 "builder_source":"3a01408b78323129146d0856fe81231d867461eaee422536bc7e87a8c8a9fdd5",
 "preparation":"9fa1e50db6e809de53639ee3382b8803a94df85798898d243258d61c6c137a8b",
 "model_raw":"3474f83d65a7fd4ffbc84b124b147f8cafc6ab4b0fcd2ed3ba3c39eed58d1550",
 "model_gzip":"45bdb52816da961cb3a64764ee1bdd9238fbf1a3e0b33a2a22ea8a48698ba777",
 "point":"0b78eb2cfc0966f66d72b083f71315e4a079e4b25f59f276c58dd93d189b49df"
}
ROOT_IDS=[50,51,52,53,60,62,67,68,69,70,71,72,76,77,79,80,83,84,85,86,87,88,90,93,94,95,96,97,98,99]
ORDERS=[220,176,110,52,139,86,150,122,114,77,78,43,75,91,50,109,92,75,44,74,57,47,53,60,36,24,44,39,26,11]


def inputs(directory,point):
    assert base.digest(Path(base.__file__).read_bytes())==BINDINGS["base_source"]
    assert base.digest(Path(arithmetic.__file__).read_bytes())==BINDINGS["arithmetic_source"]
    builder=Path(__file__).with_name("triangle_projector_six_root_conditioning.py")
    assert base.digest(builder.read_bytes())==BINDINGS["builder_source"]
    raw=(directory/"preparation.json").read_bytes()
    assert base.digest(raw)==BINDINGS["preparation"]
    prep=json.loads(raw)
    assert prep["source_sha256"]==BINDINGS["builder_source"] and prep["complete_thirty_block_coverage"]
    compressed=(directory/"model.json.gz").read_bytes()
    assert base.digest(compressed)==BINDINGS["model_gzip"]==prep["model_gzip_sha256"]
    raw=gzip.decompress(compressed)
    assert base.digest(raw)==BINDINGS["model_raw"]==prep["model_raw_sha256"]
    specification=json.loads(raw)
    assert [b["root_type"] for b in specification["blocks"]]==ROOT_IDS
    assert [b["order"] for b in specification["blocks"]]==ORDERS
    assert [d["root_type"] for d in specification["domains"]]==ROOT_IDS
    assert sum(len(b["terms"]) for b in specification["blocks"])==230648
    raw=point.read_bytes()
    assert base.digest(raw)==BINDINGS["point"]
    counts=json.loads(raw)["induced_counts"]
    assert len(counts)==48965 and all(type(c)is int and c>=0 for c in counts)
    return specification,counts


def kernel_checks(domain,matrix):
    core=[all(matrix[i][j]==0 for j in range(len(matrix)))
          for i in domain["core_triangle_class_indices"]]
    stars=[]
    for v in range(6):
        selected=[i for i,c in enumerate(domain["classes"])
                  if c["root_intersection_mask"] & (1 << v)]
        stars.append(all(sum(row[i] for i in selected)==0 for row in matrix))
    return {"core_triangle_rows_zero":core,"root_point_star_vectors_zero":stars}


def query(args):
    assert 0<args.seconds<=30 and not args.output.exists()
    start=time.monotonic();deadline=start+args.seconds
    specification,counts=inputs(args.directory,args.point)
    terminal={"status":"INCOMPLETE","source_sha256":base.digest(Path(__file__).read_bytes()),
              "bindings":BINDINGS,"blocks":[],"complete_thirty_block_coverage":False,
              "optimizer_called":False,"six_root_blocks_included":True,
              "all_intersecting_triangle_classes_retained":True,
              "unrestricted_existence_resolved":False}
    try:
        matrices=base.contract(specification,counts)
        for domain,block in zip(specification["domains"],specification["blocks"]):
            base.check_time(deadline)
            root_id=block["root_type"];M=matrices[root_id]
            checked=kernel_checks(domain,M)
            cp=arithmetic.characteristic(M);positive=all(c>=0 for c in cp)
            record={"root_type":root_id,"order":len(M),
                    "matrix":[list(map(str,row)) for row in M],
                    "det_tI_plus_matrix_coefficients":list(map(str,cp)),
                    "exact_positive_semidefinite":positive,"kernel_checks":checked}
            terminal["blocks"].append(record)
            assert all(checked["core_triangle_rows_zero"]) and all(checked["root_point_star_vectors_zero"])
            if not positive:
                v,value=base.exact_negative_vector(M,deadline)
                form,primitive,reconstructed=arithmetic.vector_form(block,v,counts)
                assert reconstructed==value<0
                record.update(integer_negative_vector=list(map(str,v)),quadratic_value=str(value),
                              primitive_induced_count_inequality=form,primitive_value=primitive)
        base.check_time(deadline)
        terminal["complete_thirty_block_coverage"]=True
        terminal["status"]=("EXACT_ALL_THIRTY_SIX_ROOT_CONDITIONED_BLOCKS_PSD"
                            if all(b["exact_positive_semidefinite"] for b in terminal["blocks"])
                            else "EXACT_SIX_ROOT_CONDITIONED_TRIANGLE_SEPARATOR")
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
    specification,counts=inputs(args.directory,args.point)
    raw=args.result.read_bytes();saved=json.loads(raw)
    assert saved["source_sha256"]==base.digest(Path(__file__).read_bytes()) and saved["bindings"]==BINDINGS
    assert saved["complete_thirty_block_coverage"] and len(saved["blocks"])==30
    matrices=base.contract(specification,counts)
    records=[]
    for domain,block,item in zip(specification["domains"],specification["blocks"],saved["blocks"]):
        root_id=block["root_type"]
        assert domain["root_type"]==root_id==item["root_type"] and item["order"]==block["order"]
        M=matrices[root_id]
        assert M==[[int(x) for x in row] for row in item["matrix"]]
        checked=kernel_checks(domain,M)
        assert checked==item["kernel_checks"]
        assert all(checked["core_triangle_rows_zero"]) and all(checked["root_point_star_vectors_zero"])
        cp=arithmetic.characteristic(M)
        assert cp==list(map(int,item["det_tI_plus_matrix_coefficients"]))
        positive=all(c>=0 for c in cp)
        assert positive==item["exact_positive_semidefinite"]
        row={"root_type":root_id,"order":len(M),"exact_positive_semidefinite":positive,
             "kernel_checks":checked}
        if positive:
            row["nullity"]=next(i for i,c in enumerate(cp) if c)
        else:
            v=list(map(int,item["integer_negative_vector"]))
            assert len(v)==len(M)
            value=sum(v[i]*M[i][j]*v[j] for i in range(len(M)) for j in range(len(M)))
            form,primitive,reconstructed=arithmetic.vector_form(block,v,counts)
            assert reconstructed==value==int(item["quadratic_value"])<0
            assert form==item["primitive_induced_count_inequality"] and primitive==item["primitive_value"]
            row["primitive_value"]=primitive
        records.append(row)
    expected=("EXACT_ALL_THIRTY_SIX_ROOT_CONDITIONED_BLOCKS_PSD"
              if all(r["exact_positive_semidefinite"] for r in records)
              else "EXACT_SIX_ROOT_CONDITIONED_TRIANGLE_SEPARATOR")
    assert saved["status"]==expected
    report={"status":"PASS_EXACT_SIX_ROOT_CONDITIONED_QUERY_REPLAY",
            "source_sha256":base.digest(Path(__file__).read_bytes()),
            "result_sha256":base.digest(raw),"bindings":BINDINGS,
            "blocks":records,"complete_thirty_block_coverage":True,
            "tensor_generation_repeated":False,"optimizer_called":False,
            "seconds":time.monotonic()-start}
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
    args=p.parse_args()
    if args.mode=="query":
        query(args)
    else:
        assert args.result
        replay(args)


if __name__=="__main__":
    main()
