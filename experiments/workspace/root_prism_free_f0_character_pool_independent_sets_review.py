"""Source-only independent review of the frozen F0 count-pool builder.

The reviewer read every subject function. This script binds that review to the
source and saved preparation; it does not import the subject, reconstruct the
model, repeat a census/control, construct a solver or evaluate a candidate.
"""
from pathlib import Path
import hashlib
import json
ROOT=Path(__file__).resolve().parents[2]
SOURCE="experiments/workspace/root_prism_free_f0_character_pool_model.py"
EXPECTED="b3029a3a197ec31305f74dead2b28f51beaf219cb2e9e289dc8f250db42a6943"
PREP="experiments/logs/root-prism-free/f0-character-pool-model01/report.json"
PREP_SHA="ed912b419cdfe1a4b4b228382ec1cfbb58a7688476c06ea14e851a3290992f30"
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
    raw=(ROOT/SOURCE).read_bytes(); assert sha(raw)==EXPECTED
    pr=(ROOT/PREP).read_bytes(); assert sha(pr)==PREP_SHA
    p=json.loads(pr); assert p["source_sha256"]==EXPECTED and p["optimizer_calls"]==0
    assert p["omitted_implied_basic_tables"]==42 and p["retained_refined_tables"]==42
    assert p["new_joint_tables"]==2 and p["external_dense_rows"]==117
    assert p["coupled_census_count_domains"]==46
    assert p["models"]["target"]["checks"]["constraints"]==34398
    assert p["models"]["initial"]["checks"]["constraints"]==34281
    report={
      "status":"PASS: complete source read; independent source-only domain, phase and row-map review",
      "review_source_sha256":sha(Path(__file__).read_bytes()),
      "subject":{"path":SOURCE,"sha256":EXPECTED,"lines":len(raw.splitlines())},
      "preparation":{"path":PREP,"sha256":PREP_SHA},
      "checked_reasoning":[
        "Each removed basic table equals the literal projection of its retained refined table; all 3288 products and parent linear rows remain.",
        "The two joint tables bind the existing population-three equalities. The first table is filtered only by the two certified simultaneous common-phase rows.",
        "Common-phase normalization preserves an equivalent representative, not every labelled signed assignment; no independent per-orbit phase is imposed.",
        "Table domains are necessary coordinate projections intersected with original domains. Product targets are distinct nonfactor variables, so the single forward pass is valid; same-factor squares are treated exactly.",
        "All46 extra count domains are bound to the complete coupled census. They contain neither a product target nor a factor, so applying them after product propagation does not invalidate that derivation.",
        "Old/target and target/initial row maps preserve order and exact constraint contents. The117 external rows remain in the complete target and are the only rows omitted from the initial relaxation.",
        "The native transcription checks every variable domain and exact constraint and includes signed integer domain holes and overflow bounds.",
        "Final candidate acceptance checks the complete target, all117 external inequalities and the original parent inspector; a count witness is not a literal graph."
      ],
      "source_imported":False,"model_or_proto_rebuilt":False,
      "census_controls_or_candidate_scan_repeated":False,"optimizer_calls":0,
      "scope_caution":"No independent execution of model construction or saved cold replay. The phase theorem and complete census are inherited source-bound premises.",
    }
    out=ROOT/"experiments/logs/root-prism-free/f0-character-pool-model-independent-sets-review.json"
    with out.open("x") as f:json.dump(report,f,indent=2);f.write("\n")
    print(json.dumps({"status":report["status"],"report":str(out.relative_to(ROOT)),"sha256":sha(out.read_bytes())}))
if __name__=="__main__":main()
