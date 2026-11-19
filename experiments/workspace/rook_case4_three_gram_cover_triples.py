"""Exact native-capacity projection for the new three-Gram-row parity cover.

No optimizer or full-cover matrix is loaded. Each rejected triple retains one
original nonnegative native upper-capacity witness. Survivors prove no lift.
"""
import argparse
import hashlib
import itertools
import json
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[2]
BASE = "experiments/logs/grids-and-triangles/"
INPUTS = {
    "native": (BASE+"complement-rook-35core-case0004-native-cpsat-model.json", "a9004e97a2d166bf8b162609cfb538eae0dd4d26942b6df5119b6a88d65ec476"),
    "model": (BASE+"rook-case4-face112-weighted-parity-model01/model.json", "c6cd72c995ce1a47db90fe7263f643131bc555ed50e329c7734536f5cf870ac3"),
    "cut": (BASE+"rook-case4-full-span-cycle-run01/separation-00/cut.json", "498058a2dbf5eab0e8460f7e46af29c5ce10ea42894d755ae846d0c24c2efa07"),
    "cut_cold": (BASE+"rook-case4-full-span-cycle-run01/separation-00/proof.json", "06365dcbe4f51983105e8d59802a699fd059685d7541a6ea7784e639b74a78e6"),
}
SECONDS = 10

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def write(path, value):
    with path.open("x") as stream:
        json.dump(value, stream, indent=2)
        stream.write("\n")

def load():
    data = {}
    for key, (name, expected) in INPUTS.items():
        raw = (ROOT/name).read_bytes()
        assert sha(raw) == expected, key
        data[key] = json.loads(raw)
    inv, cut = data["native"]["primary_inventory"], data["cut"]
    H, zeros = cut["active_original_support"], set(data["model"]["fixed_zero_columns"])
    assert len(H) == 27 and H == sorted(set(H)) and len(zeros) == 112 and not set(H)&zeros
    assert cut["original_Gram_row_ids"] == [214,344,582]
    coefficients = [0]*1214
    rhs = 0
    for rid in cut["original_Gram_row_ids"]:
        row = inv["Gram_rows"][rid]
        rhs += row[2]
        for a in row[3]:
            coefficients[a] += 1
    assert rhs == 3 and coefficients == cut["full_original1214_integer_coefficients"]
    assert [a for a in range(1214) if coefficients[a]%2 and a not in zeros] == H
    assert cut["forbidden_ones"] == []
    Q = [[a, coefficients[a]//2] for a in range(1214) if a not in zeros and coefficients[a] >= 2]
    for a in range(1214):
        if a not in zeros:
            assert coefficients[a] == (a in H)+2*(coefficients[a]//2)
    rows = []
    for rid, (i,j,q,members) in enumerate(inv["Gram_rows"]):
        rows.append({"native_row":rid,"kind":"Gram","source_id":rid,"upper":q,"members":members})
    for rid, (signature,members) in enumerate(inv["original_signature_rows"]):
        rows.append({"native_row":630+rid,"kind":"signature","source_id":rid,"upper":1,"members":members})
    for rid, row in enumerate(inv["triple_rows"]):
        rows.append({"native_row":816+rid,"kind":"triple","source_id":rid,"upper":1,"members":row["members"]})
    for rid, clause in enumerate(inv["Gram_conflict_clauses"]):
        assert clause and all(type(v) is int and v < 0 for v in clause)
        rows.append({"native_row":2181+rid,"kind":"conflict","source_id":rid,"upper":len(clause)-1,
                     "members":sorted(-v-1 for v in clause)})
    assert len(rows)==2211
    for row in rows:
        assert len(set(row["members"])) == len(row["members"])
        assert all(type(a) is int and 0<=a<1214 for a in row["members"])
        assert type(row["upper"]) is int and row["upper"]>=0
    theorem = {"original_Gram_row_ids":[214,344,582],"RHS":3,"H":H,"full1214_coefficients":coefficients,
               "proved_zero_substitutions":sorted(zeros),"Q_terms":Q,"identity":"H + 2 Q = 3",
               "integer_H_values":[1,3],"H_equals_three_forces_zero":[a for a,c in Q],
               "H_equals_one_forces_Q":1}
    return rows,theorem

def definition():
    return {"source_sha256":sha(Path(__file__).read_bytes()),"inputs":INPUTS,"seconds":SECONDS,
            "scope":"All C(27,3) triples; original 2211 nonnegative native upper capacities only",
            "omitted_signed_native_rows":60,"full_coordinate_cover_rows_loaded":False,
            "optimizer_calls":0}

def scan(output):
    start=time.monotonic()
    rows,theorem=load()
    H=theorem["H"];index={a:i for i,a in enumerate(H)}
    projected=[]
    for row in rows:
        support=sorted(set(row["members"])&set(H))
        if len(support)>row["upper"] and row["upper"]<3:
            projected.append({k:v for k,v in row.items() if k!="members"}|{"support":support})
    masks=[sum(1<<index[a] for a in row["support"]) for row in projected]
    rejected=[];surviving=[]
    for triple in itertools.combinations(H,3):
        assert time.monotonic()-start < SECONDS
        mask=sum(1<<index[a] for a in triple)
        for row,mask_row in zip(projected,masks):
            if (mask&mask_row).bit_count()>row["upper"]:
                rejected.append({"triple":list(triple),"native_row":row["native_row"],
                                 "intersection":sorted(set(triple)&set(row["support"]))})
                break
        else:
            surviving.append(list(triple))
    assert len(rejected)+len(surviving)==2925
    result={"status":"COMPLETE_NATIVE_CAPACITY_PROJECTION","definition":definition(),"theorem":theorem,
            "original_upper_capacity_rows":len(rows),"projected_rows":projected,
            "triples_checked":2925,"rejected_count":len(rejected),"surviving_count":len(surviving),
            "rejected":rejected,"surviving":surviving,
            "H_equals_three_excluded":not surviving,"H_equals_one_proved":not surviving,
            "survivor_extension_or_graph_feasibility_claimed":False,"seconds":time.monotonic()-start}
    write(output,result)
    print(json.dumps({k:result[k] for k in ["status","triples_checked","rejected_count","surviving_count","seconds"]}))

def replay(saved,output):
    start=time.monotonic()
    raw=saved.read_bytes(); result=json.loads(raw)
    assert result["definition"]==json.loads(json.dumps(definition()))
    rows,theorem=load();assert result["theorem"]==theorem
    H=theorem["H"]; all_triples=list(itertools.combinations(H,3))
    expected_projected=[{k:v for k,v in row.items() if k!="members"}|
                        {"support":sorted(set(row["members"])&set(H))} for row in rows
                        if len(set(row["members"])&set(H))>row["upper"] and row["upper"]<3]
    assert result["projected_rows"]==expected_projected
    rejected={tuple(r["triple"]):r for r in result["rejected"]}
    surviving={tuple(r) for r in result["surviving"]}
    assert len(rejected)==len(result["rejected"]) and len(surviving)==len(result["surviving"])
    assert not set(rejected)&surviving and set(rejected)|surviving==set(all_triples)
    for triple in all_triples:
        assert time.monotonic()-start < SECONDS
        violations=[row for row in expected_projected if sum(a in row["support"] for a in triple)>row["upper"]]
        if triple in rejected:
            record=rejected[triple];assert violations and record["native_row"]==violations[0]["native_row"]
            row=rows[record["native_row"]]
            assert record["intersection"]==[a for a in triple if a in row["members"]]
            assert len(record["intersection"])>row["upper"]
        else:
            assert not violations
    assert result["triples_checked"]==2925 and result["rejected_count"]==len(rejected)
    assert result["surviving_count"]==len(surviving)
    assert result["H_equals_three_excluded"]==result["H_equals_one_proved"]==(not surviving)
    report={"status":"PASS","definition":definition(),"result_sha256":sha(raw),"triples_checked":2925,
            "original_coordinate_identity_checked":1214,"rejected_witnesses":len(rejected),
            "surviving_triples_checked_against_every_projected_row":len(surviving),
            "optimizer_calls":0,"seconds":time.monotonic()-start}
    write(output,report);print(json.dumps(report))

if __name__=="__main__":
    if not __debug__:
        raise RuntimeError("assertions required")
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode",choices=["run","replay"])
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--saved",type=Path)
    args=parser.parse_args()
    if args.mode=="run":scan(args.output)
    else:replay(args.saved,args.output)
