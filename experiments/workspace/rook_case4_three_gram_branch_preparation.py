"""Prepare a complete native branch cover from the three-Gram identity.

Only preparation and its exact replay are exposed. No case propagation or
optimizer is invoked. All H42-conditional premises are excluded.
"""
import argparse
import gzip
import hashlib
import itertools
import json
from pathlib import Path
import time

ROOT=Path(__file__).resolve().parents[2]
BASE="experiments/logs/grids-and-triangles/"
INPUTS={
 "native":(BASE+"complement-rook-35core-case0004-native-cpsat-model.json","a9004e97a2d166bf8b162609cfb538eae0dd4d26942b6df5119b6a88d65ec476"),
 "face":(BASE+"rook-case4-face112-weighted-parity-model01/model.json","c6cd72c995ce1a47db90fe7263f643131bc555ed50e329c7734536f5cf870ac3"),
 "triples":(BASE+"rook-case4-three-gram-cover-triples01.json","aeb570f6a61f0cd71bf2cfef83e112a0f6b344f90abcbd41f22ee3f382e0fca2"),
 "triple_cold":(BASE+"rook-case4-three-gram-cover-triples01-replay.json","2b0eed84339a0c82b5792a2ddd959b18732590dc88deb34090a01c4c76aa3d38"),
 "cut":(BASE+"rook-case4-full-span-cycle-run01/separation-00/cut.json","498058a2dbf5eab0e8460f7e46af29c5ce10ea42894d755ae846d0c24c2efa07"),
}
KERNEL=("experiments/workspace/rook_case4_full_span_cover_h5_full_rows.py","bb26762de18cad7107a2d49214af61947807528cb66a638efec2589cadf26216")
SECONDS=30

def sha(raw):
 return hashlib.sha256(raw).hexdigest()
def canonical(value):
 return json.dumps(value,separators=(",",":"),sort_keys=True).encode()
def write(path,value):
 with path.open("xb") as stream:stream.write(json.dumps(value,indent=2).encode()+b"\n")

def weighted_patterns(one,two,three):
 for a in three:yield "weight3_singleton",(a,)
 for a in one:
  for b in two:yield "weight1_weight2_pair",tuple(sorted((a,b)))
 for triple in itertools.combinations(one,3):yield "three_weight1",triple

def controls():
 cases=points=0
 for n1 in range(6):
  for n2 in range(4):
   for n3 in range(3):
    one=list(range(n1));two=list(range(n1,n1+n2));three=list(range(n1+n2,n1+n2+n3))
    listed=[p for kind,p in weighted_patterns(one,two,three)]
    assert len(listed)==len(set(listed))
    weights=[1]*n1+[2]*n2+[3]*n3
    direct=[]
    for bits in itertools.product((0,1),repeat=len(weights)):
     points+=1
     if sum(c*x for c,x in zip(weights,bits))==3:
      direct.append(tuple(a for a,x in enumerate(bits) if x))
    assert sorted(listed)==sorted(direct)
    cases+=1
 return {"status":"PASS","weighted_partition_domains":cases,"literal_Boolean_vectors":points,
         "case4_propagation_calls":0,"optimizer_calls":0}

def native_rows(inv):
 rows=[]
 def add(terms,lower,upper):
  c={}
  for a,w in terms:
   assert type(a) is int and 0<=a<1214 and type(w) is int
   c[a]=c.get(a,0)+w
  rows.append([sorted([a,w] for a,w in c.items() if w),lower,upper])
 for i,j,q,support in inv["Gram_rows"]:add([[a,1] for a in support],q,q)
 for signature,support in inv["original_signature_rows"]:add([[a,1] for a in support],0,1)
 for row in inv["triple_rows"]:add([[a,1] for a in row["members"]],0,1)
 for clause in inv["Gram_conflict_clauses"]:
  assert clause and all(type(v) is int and v<0 for v in clause)
  add([[-v-1,1] for v in clause],0,len(clause)-1)
 for row in inv["uncapped_integer_cuts"]:
  assert row["positive_demand"]>0 and all(w>0 for a,w in row["positive_terms"])
  add(row["positive_terms"]+[[row["target_column"],-row["positive_demand"]]],
      0,sum(w for a,w in row["positive_terms"]))
 assert len(rows)==2271
 assert all(all(w==1 for a,w in row[0]) for row in rows[:2211])
 return rows

def definition():
 return {"source_sha256":sha(Path(__file__).read_bytes()),"input_bindings":INPUTS,
         "future_exact_kernel":KERNEL,"preparation_seconds":SECONDS,
         "shared_global_zeros":112,"conditional_H42_assumption":False,
         "original_native_rows":2271,"complete_coordinate_covers_in_future_model":False,
         "future_propagation_scope":"all retained patterns, deterministic raw-pattern order",
         "proposed_forward_seconds":60,"proposed_per_branch_seconds":1,
         "proposed_owned_seconds":90,"proposed_cold_seconds":60,
         "case_propagation_exposed_by_this_source":False,"optimizer_calls":0}

def derive():
 started=time.monotonic()
 data={}
 for key,(name,expected) in INPUTS.items():
  raw=(ROOT/name).read_bytes();assert sha(raw)==expected,key;data[key]=json.loads(raw)
 assert sha((ROOT/KERNEL[0]).read_bytes())==KERNEL[1]
 inv=data["native"]["primary_inventory"]; cut=data["cut"]
 rows=native_rows(inv);zeros=set(data["face"]["fixed_zero_columns"])
 assert len(zeros)==112
 coefficients=[0]*1214;rhs=0
 for rid in [214,344,582]:
  row=inv["Gram_rows"][rid];rhs+=row[2]
  for a in row[3]:coefficients[a]+=1
 assert rhs==3 and coefficients==cut["full_original1214_integer_coefficients"]
 assert cut["original_Gram_row_ids"]==[214,344,582]
 groups={w:[a for a,c in enumerate(coefficients) if a not in zeros and c==w] for w in (1,2,3)}
 assert list(map(len,groups.values()))==[26,9,1] and groups[3]==[764]
 assert max(coefficients)<=3 and min(coefficients)>=0
 positive=sorted(a for group in groups.values() for a in group)
 assert len(positive)==36 and not set(positive)&zeros
 triple_result,cold=data["triples"],data["triple_cold"]
 assert cold["status"]=="PASS" and cold["result_sha256"]==INPUTS["triples"][1]
 assert cold["triples_checked"]==2925 and triple_result["triples_checked"]==2925
 assert triple_result["theorem"]["full1214_coefficients"]==coefficients
 old_rejected={tuple(r["triple"]):r for r in triple_result["rejected"]}
 old_surviving={tuple(p) for p in triple_result["surviving"]}
 assert len(old_rejected)==2562 and len(old_surviving)==363
 assert not set(old_rejected)&old_surviving
 H=groups[1]+groups[3]
 assert set(old_rejected)|old_surviving==set(itertools.combinations(sorted(H),3))
 assert all(764 not in p for p in old_surviving)
 projected=[]
 for rid,row in enumerate(rows[:2211]):
  support=sorted(set(a for a,w in row[0])&set(positive))
  if len(support)>row[2] and row[2]<3:
   projected.append((rid,set(support),row[2]))
 records=[];retained=[];direct_checked=old_checked=0
 for raw_id,(kind,pattern) in enumerate(weighted_patterns(groups[1],groups[2],groups[3])):
  assert time.monotonic()-started<SECONDS
  assert sum(coefficients[a] for a in pattern)==3
  record={"raw_id":raw_id,"kind":kind,"selected":list(pattern)}
  if kind=="three_weight1":
   old_checked+=1
   if pattern in old_rejected:
    witness=old_rejected[pattern];rid=witness["native_row"];row=rows[rid]
    intersection=sorted(a for a in pattern if any(j==a for j,w in row[0]))
    assert rid<2211 and len(intersection)>row[2] and intersection==witness["intersection"]
    record.update(status="CAPACITY_REFUTED",native_row=rid,intersection=intersection,
                  proof_origin="frozen complete triple record and cold replay")
   else:
    assert pattern in old_surviving
    record.update(status="RETAINED",proof_origin="frozen complete triple record and cold replay")
  else:
   direct_checked+=1
   witness=next(((rid,sorted(set(pattern)&support)) for rid,support,upper in projected
                 if len(set(pattern)&support)>upper),None)
   if witness is None:record.update(status="RETAINED",proof_origin="new direct capacity check")
   else:record.update(status="CAPACITY_REFUTED",native_row=witness[0],intersection=witness[1],
                      proof_origin="new direct capacity check")
  if record["status"]=="RETAINED":
   record["branch_id"]=len(retained)
   record["zero_positive_support"]=sorted(set(positive)-set(pattern))
   fixed_zero=sorted(zeros|set(record["zero_positive_support"]))
   assert not set(fixed_zero)&set(pattern)
   record["initial_box_sha256"]=sha(canonical({"zeros":fixed_zero,"ones":list(pattern)}))
   retained.append(record)
  records.append(record)
 assert len(records)==2835 and direct_checked==235 and old_checked==2600
 assert sum(r["kind"]=="three_weight1" for r in retained)==363
 metadata={"status":"PREPARED_COMPLETE_WEIGHTED_BRANCH_COVER","definition":definition(),
           "identity":{"original_Gram_rows":[214,344,582],"rhs":3,"full1214_coefficients":coefficients,
                       "proved_zero_columns":sorted(zeros),"weight_classes":groups,"positive_support":positive},
           "raw_patterns":2835,"new_directly_checked_patterns":235,"old_triple_cases_reused":2600,
           "retained_patterns":len(retained),"capacity_refuted_patterns":2835-len(retained),
           "retained_by_kind":{k:sum(r["kind"]==k for r in retained) for k in ["weight3_singleton","weight1_weight2_pair","three_weight1"]},
           "complete_native_row_count":len(rows),"native_terms":sum(len(r[0]) for r in rows),
           "native_rows_sha256":sha(canonical(rows)),"records":records,"retained":retained,
           "all_other_positive_support_coordinates_zero_in_each_branch":True,
           "only112_global_zero_premises":True,"H42_five_assumption":False,
           "global_literal_or_case_exclusion_claimed":False,"case4_propagation_calls":0,"optimizer_calls":0}
 return metadata,rows

def prepare(directory):
 assert not directory.exists();directory.mkdir(parents=True)
 start=time.monotonic();control=controls();result,rows=derive()
 raw=canonical(rows)
 with (directory/"native-rows.json.gz").open("xb") as f:f.write(gzip.compress(raw,mtime=0))
 result["native_rows_file"]={"file":"native-rows.json.gz","sha256":sha((directory/"native-rows.json.gz").read_bytes()),
                             "raw_sha256":sha(raw),"raw_bytes":len(raw)}
 result["controls"]=control;result["seconds"]=time.monotonic()-start
 write(directory/"preparation.json",result)
 print(json.dumps({k:result[k] for k in ["status","raw_patterns","retained_patterns","capacity_refuted_patterns","retained_by_kind","native_terms","seconds"]}))

def replay(directory,output):
 start=time.monotonic()
 saved_path=directory/"preparation.json";saved=json.loads(saved_path.read_bytes())
 result,rows=derive()
 for k,v in result.items():assert saved[k]==json.loads(json.dumps(v)),k
 control=controls();assert saved["controls"]==control
 entry=saved["native_rows_file"];raw=(directory/entry["file"]).read_bytes()
 assert sha(raw)==entry["sha256"] and gzip.decompress(raw)==canonical(rows)
 assert entry["raw_sha256"]==sha(canonical(rows))
 report={"status":"PASS","preparation_sha256":sha(saved_path.read_bytes()),
         "source_sha256":sha(Path(__file__).read_bytes()),"raw_patterns_checked":2835,
         "retained_patterns":result["retained_patterns"],"all_native_rows_checked":2271,
         "case4_propagation_calls":0,"optimizer_calls":0,"seconds":time.monotonic()-start}
 write(output,report);print(json.dumps(report))

if __name__=="__main__":
 if not __debug__:raise RuntimeError("assertions required")
 p=argparse.ArgumentParser(description=__doc__);p.add_argument("mode",choices=["prepare","replay","controls"])
 p.add_argument("--directory",type=Path);p.add_argument("--output",type=Path);a=p.parse_args()
 if a.mode=="prepare":prepare(a.directory)
 elif a.mode=="replay":replay(a.directory,a.output)
 else:
  result=controls();result["definition"]=definition();write(a.output,result);print(json.dumps(result))
