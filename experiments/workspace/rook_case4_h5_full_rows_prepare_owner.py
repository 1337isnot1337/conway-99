"""One bounded preparation call; frozen propagation engine remains unchanged."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[2]
ENGINE=ROOT/"experiments/workspace/rook_case4_full_span_cover_h5_full_rows.py"
ENGINE_SHA="bb26762de18cad7107a2d49214af61947807528cb66a638efec2589cadf26216"
BASE=ROOT/"experiments/logs/grids-and-triangles"
DIRECTORY=BASE/"rook-case4-full-span-cover-h5-full-rows-preparation01"
OWNER=BASE/"rook-case4-full-span-cover-h5-full-rows-preparation01-owner.json"
STDOUT=BASE/"rook-case4-full-span-cover-h5-full-rows-preparation01.stdout.log"
STDERR=BASE/"rook-case4-full-span-cover-h5-full-rows-preparation01.stderr.log"
SECONDS=90

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def save(value):
    tmp=OWNER.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(value,indent=2)+"\n")
    tmp.replace(OWNER)

def main():
    assert sha(ENGINE)==ENGINE_SHA
    assert not DIRECTORY.exists() and not OWNER.exists()
    start=time.monotonic()
    result={"status":"UNKNOWN_BEFORE_PREPARATION","source_sha256":sha(Path(__file__)),
        "engine_sha256":ENGINE_SHA,"hard_seconds":SECONDS,"automatic_retries":0,
        "branch_propagation_calls":0,"optimizer_calls":0}
    save(result)
    command=[sys.executable,str(ENGINE),"prepare","--root",str(ROOT),"--directory",str(DIRECTORY)]
    with STDOUT.open("xb") as out,STDERR.open("xb") as err:
        child=subprocess.Popen(command,stdout=out,stderr=err)
        timed_out=False
        try:
            code=child.wait(timeout=max(0.001,SECONDS-(time.monotonic()-start)))
        except subprocess.TimeoutExpired:
            timed_out=True
            child.kill()
            code=child.wait()
    elapsed=time.monotonic()-start
    result.update(status="UNKNOWN",child_exit_code=code,child_reaped=True,hard_timeout=timed_out,seconds=elapsed)
    p=DIRECTORY/"preparation.json"
    if p.exists():
        result["preparation"]={"path":str(p.relative_to(ROOT)),"sha256":sha(p)}
    if code==0 and not timed_out and elapsed<=SECONDS:
        report=json.loads(p.read_bytes())
        assert report["source_sha256"]==ENGINE_SHA and report["case4_propagation_calls"]==report["optimizer_calls"]==0
        assert (report["rows"],report["columns"])==(166020,1102)
        result["status"]="PASS: one preparation completed; no branch run"
    result["stdout_sha256"]=sha(STDOUT)
    result["stderr_sha256"]=sha(STDERR)
    save(result)
    print(json.dumps(result),flush=True)

if __name__=="__main__":
    if not __debug__:raise RuntimeError("assertions required")
    main()
