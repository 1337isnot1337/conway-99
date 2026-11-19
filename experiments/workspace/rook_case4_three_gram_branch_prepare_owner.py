"""Forty-second owners for one frozen small preparation and its cold replay."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/"experiments/logs/grids-and-triangles"
ENGINE=ROOT/"experiments/workspace/rook_case4_three_gram_branch_preparation.py"
ENGINE_SHA="fdde57b1a3a4de759ca0b04a8465f6bb97659cc7db715aed4fa5e665358c7ed5"
DIRECTORY=BASE/"rook-case4-three-gram-branches-preparation01"
COLD=BASE/"rook-case4-three-gram-branches-preparation01-replay.json"
SECONDS=40

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def save(path,value):
 temporary=path.with_suffix(".json.tmp")
 temporary.write_text(json.dumps(value,indent=2)+"\n");temporary.replace(path)

def main(mode):
 assert sha(ENGINE)==ENGINE_SHA
 prefix=BASE/("rook-case4-three-gram-branches-preparation01" if mode=="prepare" else "rook-case4-three-gram-branches-preparation01-replay")
 owner=Path(str(prefix)+"-owner.json");stdout=Path(str(prefix)+".stdout.log");stderr=Path(str(prefix)+".stderr.log")
 assert not owner.exists()
 if mode=="prepare":
  assert not DIRECTORY.exists()
  command=[sys.executable,str(ENGINE),"prepare","--directory",str(DIRECTORY)]
  report_path=DIRECTORY/"preparation.json"
 else:
  assert DIRECTORY.exists() and not COLD.exists()
  command=[sys.executable,str(ENGINE),"replay","--directory",str(DIRECTORY),"--output",str(COLD)]
  report_path=COLD
 start=time.monotonic()
 result={"status":"UNKNOWN_BEFORE_CHILD","mode":mode,"source_sha256":sha(Path(__file__)),
         "engine_sha256":ENGINE_SHA,"hard_seconds":SECONDS,"automatic_retries":0,"optimizer_calls":0,"case4_propagation_calls":0}
 save(owner,result)
 timed_out=False
 with stdout.open("xb") as out,stderr.open("xb") as err:
  child=subprocess.Popen(command,stdout=out,stderr=err)
  try:code=child.wait(timeout=max(0.001,SECONDS-(time.monotonic()-start)))
  except subprocess.TimeoutExpired:
   timed_out=True;child.kill();code=child.wait()
 elapsed=time.monotonic()-start
 result.update(status="UNKNOWN",exit_code=code,child_reaped=True,hard_timeout=timed_out,seconds=elapsed)
 if report_path.exists():result["report"]={"path":str(report_path.relative_to(ROOT)),"sha256":sha(report_path)}
 if code==0 and not timed_out and elapsed<=SECONDS:
  report=json.loads(report_path.read_bytes())
  assert report["case4_propagation_calls"]==report["optimizer_calls"]==0
  assert report["status"]==("PREPARED_COMPLETE_WEIGHTED_BRANCH_COVER" if mode=="prepare" else "PASS")
  result["status"]="PASS"
 result["stdout_sha256"]=sha(stdout);result["stderr_sha256"]=sha(stderr)
 save(owner,result);print(json.dumps(result),flush=True)

if __name__=="__main__":
 if not __debug__:raise RuntimeError("assertions required")
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("mode",choices=["prepare","replay"])
 main(parser.parse_args().mode)
