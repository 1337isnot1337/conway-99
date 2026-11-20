"""Cold mathematical replay of the recovered allocated F0 transcript.

Runs the unchanged bound replay function in an isolated copied tree.
Optimizer entry points are disabled. This does not rerun the search.
"""
import argparse
import hashlib
import json
from pathlib import Path
import resource
import sys
import time

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--root",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--replay-output",type=Path,required=True)
    args=parser.parse_args()
    root=args.root.resolve(); output=args.output.resolve(); replay_output=args.replay_output.resolve()
    assert not output.exists() and not replay_output.exists()
    sources=root/"experiments/workspace"; logs=root/"experiments/logs/root-prism-free"
    module_path=sources/"root_prism_free_f0_allocated_lazy_continuation.py"
    prep=logs/"f0-allocated-lazy-continuation-preparation.json.gz"
    result=logs/"f0-allocated-lazy-continuation-run01/result.json"
    old=logs/"f0-allocated-lazy-continuation-run01-cold-replay.json"
    assert sha(module_path)=="46b30a4e7c64db612cff606bd56aa05da44356547f617e977a8fa17ac0da4c8d"
    assert sha(prep)=="7eecf38db3acba31bf2e24d08937235977cce1c6c93d9426795a3f0bb713fc23"
    assert sha(result)=="6955adbab024f3a3668258c5fad56592d05025acf381d4a4a71d1915b788deab"
    assert sha(old)=="4c437fb8ad028bc9aa55753cc0da33d557d884c75962531e991fc2743b2dde9a"
    attempted=[]
    def forbidden(name):
        def fail(*unused_args,**unused_kwargs):
            attempted.append(name)
            raise RuntimeError("Optimizer disabled during exact cold replay: "+name)
        return fail
    import highspy
    import scipy.optimize
    import pysat.solvers
    highspy.Highs.run=forbidden("highspy.Highs.run")
    highspy.Highs.getDualRay=forbidden("highspy.Highs.getDualRay")
    scipy.optimize.linprog=forbidden("scipy.optimize.linprog")
    scipy.optimize.milp=forbidden("scipy.optimize.milp")
    pysat.solvers.Solver.__init__=forbidden("pysat.solvers.Solver")
    sys.path.insert(0,str(sources))
    started=time.monotonic()
    report={"status":"RUNNING: frozen exact allocated transcript replay",
        "source_sha256":sha(__file__),"subject_source_sha256":sha(module_path),
        "preparation_sha256":sha(prep),"result_sha256":sha(result),
        "saved_cold_replay_sha256":sha(old),"isolated_root":str(root),
        "optimizer_calls_attempted":attempted,"original_tree_modified":False}
    output.write_text(json.dumps(report,indent=2)+"\n")
    print("Starting unchanged exact replay with optimizer calls disabled",flush=True)
    try:
        import root_prism_free_f0_allocated_lazy_continuation as loop
        assert Path(loop.__file__).resolve()==module_path.resolve()
        _,cuts,records,replayed=loop.reconstruct(prep,result)
        assert not attempted
        assert replayed==json.loads(old.read_text()), "fresh report differs from captured report"
        assert len(cuts)==4404 and len(records)==8628
        assert replayed["final_snapshot"]["individual_cuts"]==3948
        assert replayed["final_snapshot"]["symmetric_cuts"]==456
        replay_output.write_text(json.dumps(replayed,indent=2)+"\n")
        report.update(status="PASS: fresh exact replay equals the recovered pre-outage report",
            replay_output=str(replay_output),replay_output_sha256=sha(replay_output),
            final_snapshot=replayed["final_snapshot"],
            final_quadratic_snapshot=replayed["final_quadratic_snapshot"],
            checked_candidates=replayed["checked_candidates"],row_passes=replayed["row_passes"],
            exact_individual_obstructions=replayed["exact_individual_obstructions"],
            exact_individual_boxes=replayed["exact_individual_boxes"],
            exact_shared_rays=replayed["exact_shared_rays"],
            optimizer_called=False,conditional_component_excluded=False)
    except BaseException as error:
        report.update(status="ERROR: exact replay did not complete",error_type=type(error).__name__,error_message=str(error))
        raise
    finally:
        report["elapsed_seconds"]=time.monotonic()-started
        report["peak_rss_kib"]=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        output.write_text(json.dumps(report,indent=2)+"\n")
        print(json.dumps(report,indent=2),flush=True)

if __name__=="__main__":
    main()
