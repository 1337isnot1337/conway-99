"""Source-only signed-character append review; no subject import or solve."""
import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = "experiments/workspace/root_prism_free_f0_character_cpsat.py"
SOURCE_SHA = "879cdb9be48f9377dd6bccd078f26a568d12467385e9ecb1d5b260cc56ff64e7"
PARENT = "experiments/workspace/root_prism_free_f0_population_profile_cpsat.py"
PARENT_SHA = "a5b4485f4f30cdcb640d7cb63a5d4b1df4828e8f092f164fdad5a4a21260a67b"
PREP = "experiments/logs/root-prism-free/f0-character-cpsat01/report.json"
COLD = "experiments/logs/root-prism-free/f0-character-cpsat01-cold/report.json"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    raw = (ROOT/SOURCE).read_bytes()
    assert sha(raw) == SOURCE_SHA and sha((ROOT/PARENT).read_bytes()) == PARENT_SHA
    tree = ast.parse(raw)
    constants = {}
    for node in tree.body:
        if not isinstance(node,ast.Assign) or len(node.targets) != 1:
            continue
        try:
            value = ast.literal_eval(node.value)
        except (ValueError,TypeError):
            continue
        target = node.targets[0]
        if isinstance(target,ast.Name):
            constants[target.id] = value
        elif isinstance(target,ast.Tuple):
            constants.update((n.id,v) for n,v in zip(target.elts,value))
    assert [constants[k] for k in ("OLD_VARIABLES","OLD_CONSTRAINTS","SIGNED_OFFSET",
        "SIGNED_COUNT","PRODUCT_OFFSET","PRODUCT_COUNT","VARIABLES","CONSTRAINTS")] == [15941,29592,15941,118,16059,2385,18444,34436]
    assert 15941+118 == 16059 and 16059+2385 == 18444
    assert 29592+(2385+32)+2385+42 == 34436
    prep_raw,cold_raw = (ROOT/PREP).read_bytes(),(ROOT/COLD).read_bytes()
    assert sha(prep_raw) == "e15c4bfcf7adaabb60258e3cffa8046eb0cd97843ae8787a24b356011d7b8a5f"
    assert sha(cold_raw) == "fd86705f404e899869234d67916c2178d77acfb9c2b847571fb897cc5f785e18"
    prep,cold = json.loads(prep_raw),json.loads(cold_raw)
    for record in (prep,cold):
        assert record["status"].startswith("PASS:") and record["source_sha256"] == SOURCE_SHA
        assert record["raw_proto_sha256"] == "5b43e3c026dbe71fcc8d072aa1790b80f7a81312e7b1ebf36a37612b2f726eeb"
        assert record["optimizer_calls"] == 0 and not record["CpSolver_constructed"]
        assert record["namespaces"] == {"original_counts":[0,15038],"trivial_products":[15038,15941],
            "signed_populations":[15941,16059],"signed_products":[16059,18444]}
    assert prep["checks"] == cold["checks"]
    report = {"status":"PASS: complete signed-character append/inspector source review",
        "review_source_sha256":sha(Path(__file__).read_bytes()),
        "subject":{"path":SOURCE,"sha256":SOURCE_SHA},
        "profile_parent":{"path":PARENT,"sha256":PARENT_SHA},
        "preparation_sha256":sha(prep_raw),"cold_sha256":sha(cold_raw),
        "mathematical_and_encoding_checks":[
            "The118 local signed IDs are shifted into a disjoint native interval; the2385 product targets occupy the next disjoint interval.",
            "Balanced signs on6 or12 literal selectors justify symmetric signed bounds; squared products use nonnegative bounds and cross products retain both signs.",
            "Every signed product is linked both to its two native signed factors and to the published original-count linear form; no factor-of-two convention is introduced by the adapter.",
            "Refined42-table columns preserve the old count ordering and append translated signed IDs. Projection recovers every old profile with its literal multiplicity, using the already audited character certificate.",
            "Every32 character-Gram equality is translated through the same namespace and retains zero right side.",
            "The actual native prefix comparison preserves all15941 variables and29592 constraints, including all old tables and92 PSD directions. Added constraints have no enforcement literals or hidden top-level assumptions/hints/objective.",
            "The inspector delegates the full original count/profile checks, then independently evaluates every new signed product, count link,32 Gram rows and42 refined table memberships with Python integers.",
            "The parent count inspector directly checks all903 deterministic pair-population identities, so auxiliary product equality alone cannot bypass a pair-count link.",
            "The reported result is scoped to an exact count witness; literal selector realization, exterior edges, full PSD and graph existence are not inferred."
        ],
        "source_read_completely":True,"parent_profile_source_read_completely":True,
        "parent_count_inspector_read":True,
        "subject_imported":False,"native_proto_read_or_rebuilt":False,
        "controls_repeated":False,"character_census_repeated":False,
        "optimizer_calls":0,"scope":"Read-only source/mathematical gate and metadata bindings; relies on the frozen character/profile necessity certificates and completed native checks."}
    output = ROOT/"experiments/logs/root-prism-free/f0-character-cpsat-independent-sets-source-review.json"
    assert not output.exists()
    output.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps({"path":str(output.relative_to(ROOT)),"sha256":sha(output.read_bytes())},indent=2))


if __name__ == "__main__":
    main()
