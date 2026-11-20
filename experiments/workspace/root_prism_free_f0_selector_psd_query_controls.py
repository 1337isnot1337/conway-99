"""Focused exact acceptance and unchanged-control-flow checks for32 PSD cuts.

The old incidence gives only a positive selector-moment control. It is not
claimed to satisfy the strengthened incidence/edge linear model.
"""
import ast
from fractions import Fraction
import hashlib
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LOGS = ROOT/"experiments/logs/root-prism-free"
HELPER_SHA = "9834bf571545ab401cc7667e818a19c956d09b4636d577cc5de961d313be746b"
DRIVER_SHA = "5e9ebe327f6ae5ccbb85d0697faca359b9517d17b9a8f0ccf375317eab1e44b3"
POSITIVE_SHA = "64d5411e04764b0d7e7157c47b67d759e536a401fee8fe36e274943f2fda4abf"
NUMERICAL_SHA = "20674e3a41842e42232df60e24abf3f34a5a5c8ec9a16a258d4906bb58562fd9"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def functions(path):
    return {node.name: ast.dump(node, include_attributes=False)
            for node in ast.parse(Path(path).read_text()).body if isinstance(node, ast.FunctionDef)}


def main():
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args=parser.parse_args()
    assert not args.output.exists()
    here=Path(__file__).resolve().parent
    helper_path=here/"root_prism_free_f0_selector_psd_exact.py"
    driver_path=here/"root_prism_free_f0_selector_psd_query.py"
    assert sha(helper_path)==HELPER_SHA and sha(driver_path)==DRIVER_SHA
    spec=importlib.util.spec_from_file_location("f0_psd_control_exact",helper_path)
    exact=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(exact)
    old_helper=functions(here/"root_prism_free_f0_second_moments_reduced_exact.py")
    old_driver=functions(here/"root_prism_free_f0_second_moments_ipm_query.py")
    new_helper,new_driver=functions(helper_path),functions(driver_path)
    assert old_helper["recover_point"]==new_helper["recover_point"]
    unchanged=["owned_child","version_check","main","controls"]
    for name in unchanged:
        assert old_driver[name]==new_driver[name],name
    model=exact.load_model(LOGS/"f0-selector-psd-model01.json.gz")
    reduced=model["_reduced"]
    full=reduced["_original"]
    positive_path=LOGS/"f0-incidence-case00-run01/result.json"
    assert sha(positive_path)==POSITIVE_SHA
    selected=json.loads(positive_path.read_text())["incidence_witness"]["selected_columns"]
    assert len(selected)==len(set(selected))==60
    images=[{g[a] for a in selected} for g in full["selector_actions"]]
    assert len(images)==12
    old=[0]*15589
    for orbit,members in enumerate(full["selector_orbits"]):
        values={sum(a in image for image in images) for a in members}
        assert len(values)==1
        old[orbit]=values.pop()
    pairs=[(a,b) for a in range(480) for b in range(a+1,480)]
    for orbit,members in enumerate(full["pair_orbits"]):
        values={sum(pairs[p][0] in image and pairs[p][1] in image for image in images) for p in members}
        assert len(values)==1
        old[5847+orbit]=values.pop()
    assert all(old[j]==0 for j,row in reduced["fixed_zero_original_variables"])
    point={"denominator":"12","numerators":[str(old[j]) for j in reduced["kept_original_variables"]]}
    positive=exact.full_psd_directions(model,point)
    assert positive["passed"] and positive["directions_checked"]==32
    expected=[]
    for cert in model["cut_certificates"]:
        c,v=cert["vector"][0],cert["vector"][1:]
        expected.append(str(sum((c+sum(v[a] for a in image))**2 for image in images)))
    assert positive["full480_quadratic_numerators"]==expected
    numerical_path=LOGS/"f0-second-moments-ipm-query-run01/numerical.json"
    assert sha(numerical_path)==NUMERICAL_SHA
    numeric=json.loads(numerical_path.read_text())
    fractions=[Fraction(float.fromhex(h)) for h in numeric["col_value_hex"]]
    den=max(v.denominator for v in fractions)
    assert all(den%v.denominator==0 for v in fractions)
    proposed={"denominator":str(den),"numerators":[str(v.numerator*(den//v.denominator)) for v in fractions]}
    negative=exact.full_psd_directions(model,proposed)
    assert not negative["passed"] and all(int(v)<0 for v in negative["full480_quadratic_numerators"])
    record={"status":"PASS: exact literal PSD acceptance and unchanged bounded control flow",
            "source_sha256":sha(__file__),"helper_source_sha256":HELPER_SHA,
            "driver_source_sha256":DRIVER_SHA,"unchanged_helper_functions":["recover_point"],
            "unchanged_driver_functions":unchanged,
            "positive_moment_control":{"source_sha256":POSITIVE_SHA,"images":12,"squares_checked":32,
                "full480_quadratic_numerators":expected,"production_linear_feasibility_claimed":False},
            "negative_proposal_control":{"source_sha256":NUMERICAL_SHA,"denominator":str(den),
                "strict_negative_directions":32,"full480_quadratic_numerators":negative["full480_quadratic_numerators"],
                "proposing_point_feasibility_claimed":False},
            "optimizer_calls":0,"eigendecompositions":0}
    args.output.write_text(json.dumps(record,indent=2)+"\n")
    print(json.dumps({"status":record["status"],"output_sha256":sha(args.output)}))


if __name__=="__main__":
    main()

