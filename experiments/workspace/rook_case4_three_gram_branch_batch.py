"""Bounded native propagation over the complete 444-pattern case4 cover.

The audited integer propagation and replay functions are imported unchanged.
No H42=5 premise, selector-cover matrix or optimizer is used.
"""
import argparse
import gzip
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[2]
BASE="experiments/log/grids-and-triangles/"
LOGS="experiments/logs/grids-and-triangles/"
BINDINGS={
 "kernel":("experiments/workspace/rook_case4_full_span_cover_h5_full_rows.py","bb26762de18cad7107a2d49214af61947807528cb66a638efec2589cadf26216"),
 "scope_source":("experiments/workspace/rook_case4_three_gram_branch_preparation.py","fdde57b1a3a4de759ca0b04a8465f6bb97659cc7db715aed4fa5e665358c7ed5"),
 "preparation":(LOGS+"rook-case4-three-gram-branches-preparation01/preparation.json","ad3f2b14fd4f60b0d411cd5d920ec461cffed3ab7a0ddf68861b9500cad95ba3"),
 "preparation_cold":(LOGS+"rook-case4-three-gram-branches-preparation01-replay.json","769a2536abf223d5b9f6aac27b50b0623f0976e955d153165e4c7b1fceac7e2c"),
}
LIMITS={"forward_seconds":60,"per_branch_seconds":1,"cold_seconds":60,"owned_seconds":90,
        "maximum_records":444,"maximum_transcript_bytes":64*1024*1024,"automatic_retries":0}

def sha(raw):return hashlib.sha256(raw).hexdigest()
def file_sha(path):return sha(path.read_bytes())
def canonical(value):return json.dumps(value,sort_keys=True,separators=(",",":"),allow_nan=False).encode()
def ref(path):return {"path":str(path.resolve()),"sha256":file_sha(path),"bytes":path.stat().st_size}
def write(path,value):
 assert not path.exists()
 temporary=path.with_suffix(path.suffix+".tmp")
 with temporary.open("xb") as stream:
  stream.write(json.dumps(value,indent=2,allow_nan=False).encode()+b"\n");stream.flush()
 temporary.replace(path)
def checked(key):
 name,expected=BINDINGS[key];p=ROOT/name;assert file_sha(p)==expected,key;return p
def definition():
 for key in BINDINGS:checked(key)
 return {"source_sha256":file_sha(Path(__file__)),"bindings":BINDINGS,"limits":LIMITS,
         "native_rows":2271,"variables":1214,"native_terms":28784,"retained_branches":444,
         "raw_branch_cover":2835,"scope":"case4 on the112 proved global zeros; no H42 condition",
         "unchanged_imported_functions":["Pool","tiny_pool","propagate","verify_record","literal_bounds"],
         "optimizer_calls":0}
def load():
 start=time.monotonic();bound=definition()
 p=checked("kernel");spec=importlib.util.spec_from_file_location("frozen_native_branch_kernel",p)
 k=importlib.util.module_from_spec(spec);spec.loader.exec_module(k)
 assert k.np.__version__=="2.3.5"
 prep=json.loads(checked("preparation").read_bytes());cold=json.loads(checked("preparation_cold").read_bytes())
 assert cold["status"]=="PASS" and cold["preparation_sha256"]==BINDINGS["preparation"][1]
 assert cold["source_sha256"]==BINDINGS["scope_source"][1]
 assert prep["definition"]["source_sha256"]==BINDINGS["scope_source"][1]
 assert prep["retained_patterns"]==444 and prep["raw_patterns"]==2835
 assert prep["only112_global_zero_premises"] and not prep["H42_five_assumption"]
 path=checked("preparation").parent/prep["native_rows_file"]["file"];raw=path.read_bytes()
 assert sha(raw)==prep["native_rows_file"]["sha256"]
 raw=gzip.decompress(raw);assert sha(raw)==prep["native_rows_sha256"]==prep["native_rows_file"]["raw_sha256"]
 rows=json.loads(raw);assert len(rows)==2271 and sum(len(r[0]) for r in rows)==28784
 assert all(type(x) is int for r in rows for x in (r[1],r[2]))
 assert all(type(a) is type(c) is int for r in rows for a,c in r[0])
 pool=k.tiny_pool(rows,1214);originals=k.np.arange(1214,dtype=k.np.int32)
 zeros=prep["identity"]["proved_zero_columns"];positive=prep["identity"]["positive_support"]
 assert len(zeros)==112 and len(set(zeros))==112 and len(positive)==36
 states=[]
 for index,branch in enumerate(prep["retained"]):
  assert branch["branch_id"]==index and branch["status"]=="RETAINED"
  ones=branch["selected"];fixed=sorted(set(zeros)|set(branch["zero_positive_support"]))
  assert branch["zero_positive_support"]==sorted(set(positive)-set(ones))
  assert not set(fixed)&set(ones) and set(ones)<=set(positive)
  assert sha(canonical({"zeros":fixed,"ones":ones}))==branch["initial_box_sha256"]
  state=k.np.full(1214,-1,dtype=k.np.int8);state[fixed]=0;state[ones]=1;states.append(state)
 assert len(states)==444
 return k,prep,pool,originals,states,bound,time.monotonic()-start

def common_literals(states):
 if not states:return [],[]
 n=len(states[0]);assert all(len(s)==n for s in states)
 zero=[a for a in range(n) if all(int(s[a])==0 for s in states)]
 one=[a for a in range(n) if all(int(s[a])==1 for s in states)]
 return zero,one

def controls():
 cases=0
 boxes=list(itertools.product((-1,0,1),repeat=3))
 for a in boxes:
  for b in boxes:
   zero,one=common_literals([a,b])
   points=[v for s in [a,b] for v in itertools.product((0,1),repeat=3)
           if all(x<0 or x==y for x,y in zip(s,v))]
   assert zero==[i for i in range(3) if all(v[i]==0 for v in points)]
   assert one==[i for i in range(3) if all(v[i]==1 for v in points)]
   cases+=1
 assert common_literals([])==([],[])
 return {"status":"PASS","literal_union_intersection_controls":cases,"empty_case_no_vacuous_units":True,
         "case4_propagation_calls":0,"optimizer_calls":0}

def preflight(output):
 start=time.monotonic();control=controls();k,prep,pool,ids,states,bound,initial=load()
 assert time.monotonic()-start<30
 report={"status":"PREPARED_NO_CASE_PROPAGATION","definition":bound,"controls":control,
         "native_rows":pool.nrows,"native_terms":pool.nnz,"variables":pool.nvars,
         "maximum_int64_activity_bound":pool.activity_bound,"initial_boxes_checked":len(states),
         "numpy_version":k.np.__version__,"kernel_functions_copied_or_changed":False,
         "case4_propagation_calls":0,"optimizer_calls":0,"seconds":time.monotonic()-start}
 write(output,report);print(json.dumps({k:report[k] for k in ["status","seconds","native_rows","initial_boxes_checked"]}))

def check_preflight(path,bound):
 raw=path.read_bytes();p=json.loads(raw)
 assert p["status"]=="PREPARED_NO_CASE_PROPAGATION" and p["definition"]==json.loads(json.dumps(bound))
 assert p["controls"]["status"]=="PASS" and p["case4_propagation_calls"]==0
 return {"path":str(path.resolve()),"sha256":sha(raw)}

def forward(preflight_path,directory):
 k,prep,pool,ids,states,bound,initial=load();preflight_ref=check_preflight(preflight_path,bound)
 start=time.monotonic();deadline=start+LIMITS["forward_seconds"];records=[];used=0;stop="complete"
 for index,(branch,state) in enumerate(zip(prep["retained"],states)):
  if time.monotonic()>=deadline:stop="shared forward time limit";break
  t=time.monotonic();record=k.propagate(pool,state,ids,min(deadline,t+LIMITS["per_branch_seconds"]))
  record.update(index=index,raw_id=branch["raw_id"],kind=branch["kind"],selected=branch["selected"],
                initial_box_sha256=branch["initial_box_sha256"],seconds=time.monotonic()-t)
  size=len(json.dumps(record,indent=2).encode())+1
  if used+size>LIMITS["maximum_transcript_bytes"]:stop="transcript cap";break
  path=directory/f"branch-{index:03d}.json";write(path,record);records.append(ref(path));used+=size
  if record["terminal"]["status"]=="partial":stop="first partial branch";break
 statuses=[json.loads(Path(r["path"]).read_bytes())["terminal"]["status"] for r in records]
 complete=len(records)==444 and "partial" not in statuses
 result={"status":"COMPLETE_BRANCH_PREFIX" if complete else "PARTIAL_BRANCH_PREFIX","definition":bound,
         "preflight":preflight_ref,"records":records,"complete":complete,"stop":stop,
         "recorded":len(records),"unprocessed_UNKNOWN":444-len(records),
         "contradictions":sum(s.startswith("contradiction") for s in statuses),
         "fixed_points":statuses.count("fixed_point"),"partial":statuses.count("partial"),
         "initialization_seconds":initial,"forward_seconds":time.monotonic()-start,
         "transcript_bytes":used,"cold_required":True,"case4_excluded":False,"optimizer_calls":0}
 write(directory/"child-result.json",result)

def cold(preflight_path,source_directory,directory):
 k,prep,pool,ids,states,bound,initial=load();check_preflight(preflight_path,bound)
 owner_path=source_directory/"supervisor.json";owner=json.loads(owner_path.read_bytes())
 assert owner["source_sha256"]==file_sha(Path(__file__)) and owner["mode"]=="run"
 assert owner["preflight"]["sha256"]==file_sha(preflight_path)
 refs=owner["records_preserved"];assert len(refs)<=444
 start=time.monotonic();deadline=start+LIMITS["cold_seconds"];checks=[];survivors=[];partial=False
 for index,reference in enumerate(refs):
  if time.monotonic()>=deadline:break
  path=Path(reference["path"]);assert file_sha(path)==reference["sha256"]
  record=json.loads(path.read_bytes());branch=prep["retained"][index]
  assert record["index"]==index and record["raw_id"]==branch["raw_id"]
  assert record["kind"]==branch["kind"] and record["selected"]==branch["selected"]
  assert record["initial_box_sha256"]==branch["initial_box_sha256"]
  check=k.verify_record(pool,states[index],ids,record);check.update(index=index,raw_id=branch["raw_id"])
  checks.append(check)
  if check["terminal"]=="partial":partial=True
  if not check["terminal"].startswith("contradiction"):
   state=states[index].copy()
   for rid,a,value in record["trace"]:state[a]=value
   survivors.append(state)
 all_checked=len(checks)==len(refs)
 complete=owner["status"]=="CHILD_COMPLETE" and all_checked and len(checks)==444 and not partial
 zero,one=common_literals(survivors) if complete else ([],[])
 new_zero=sorted(set(zero)-set(prep["identity"]["proved_zero_columns"]))
 report={"status":"PASS" if all_checked else "PARTIAL_REPLAY","definition":bound,"forward_owner":ref(owner_path),
         "checks":checks,"all_saved_records_checked":all_checked,"all444_branches_checked":complete,
         "surviving_boxes":len(survivors),"global_zero_columns":new_zero,"global_one_columns":one,
         "global_literals_require_complete_branch_cover":True,"case4_excluded":complete and not survivors,
         "whole_graph_problem_resolved":False,"initialization_seconds":initial,
         "cold_seconds":time.monotonic()-start,"optimizer_calls":0}
 write(directory/"child-result.json",report)

def owned(mode,preflight_path,directory,source_directory=None):
 bound=definition();preflight_ref=check_preflight(preflight_path,bound)
 assert not directory.exists();directory.mkdir(parents=True)
 start=time.monotonic();command=[sys.executable,str(Path(__file__).resolve()),"_"+mode,
       "--preflight",str(preflight_path.resolve()),"--directory",str(directory.resolve())]
 if source_directory is not None:command+=["--source-directory",str(source_directory.resolve())]
 with (directory/"stdout.log").open("xb") as out,(directory/"stderr.log").open("xb") as err:
  child=subprocess.Popen(command,stdout=out,stderr=err);timeout=False
  try:code=child.wait(timeout=max(0.001,LIMITS["owned_seconds"]-(time.monotonic()-start)))
  except subprocess.TimeoutExpired:timeout=True;child.kill();code=child.wait()
 refs=[ref(p) for p in sorted(directory.glob("branch-*.json"))]
 result={"status":"CHILD_COMPLETE" if code==0 and (directory/"child-result.json").exists() else "UNKNOWN",
         "mode":mode,"source_sha256":file_sha(Path(__file__)),"preflight":preflight_ref,
         "exit_code":code,"child_reaped":True,"hard_timeout":timeout,"seconds":time.monotonic()-start,
         "records_preserved":refs,"automatic_retries":0,"case4_excluded":False,"optimizer_calls":0}
 if (directory/"child-result.json").exists():result["child_result"]=ref(directory/"child-result.json")
 write(directory/"supervisor.json",result);print(json.dumps({k:result[k] for k in ["status","seconds","exit_code"]}))

if __name__=="__main__":
 if not __debug__:raise RuntimeError("assertions required")
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument("mode",choices=["preflight","run","replay","_run","_replay"])
 parser.add_argument("--preflight",type=Path);parser.add_argument("--directory",type=Path)
 parser.add_argument("--source-directory",type=Path);parser.add_argument("--output",type=Path)
 a=parser.parse_args()
 if a.mode=="preflight":preflight(a.output)
 elif a.mode=="run":owned("run",a.preflight,a.directory)
 elif a.mode=="replay":owned("replay",a.preflight,a.directory,a.source_directory)
 elif a.mode=="_run":forward(a.preflight,a.directory)
 else:cold(a.preflight,a.source_directory,a.directory)
