"""Source and adapter-binding audit of the F0 joint PSD/clique overlay.

This imports no subject module, rebuilds no matrix, and calls no optimizer.
The mathematical review statements record the reviewed frozen sources.
"""
import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT/"experiments/workspace"
LOGS = ROOT/"experiments/logs/root-prism-free"
SUBJECTS = {
    "root_prism_free_f0_joint_psd_clique_model.py": "5bef59a3831030047349a0f2d80b36fffb6aa99e8bfdc1f074d4b776143b459b",
    "root_prism_free_f0_joint_psd_clique_exact.py": "f16d9648a396a4c2c78b68262ce4c767351bfd69bdf66237b49b35e0fb8752fc",
    "root_prism_free_f0_joint_psd_clique_query.py": "577b120992399a0a0e958eafd0bd9d7a7344982bbb4788a60bebee7ec7437441",
    "root_prism_free_f0_joint_psd_clique_replay.py": "5804a7d10271b20c7f096b3012bdc78ee56be3054f94887575454da1475cb79d",
    "root_prism_free_f0_joint_psd_clique_native_audit.py": "cdc70cff604545a549382ac2c6677dfa7cd0bb9cfebcc6c28c8846e51383cab5",
    "root_prism_free_f0_joint_psd_clique_reuse_control.py": "857597faf2f954b465a0b56f7f5b8fd250101b6449f83ca23053f38ffde94793",
}
RECORDS = {
    "f0-joint-psd-clique-model01-preparation.json": "286382d259bb7d9e53c9af9c0e378369f15e29f803d1d553c58a044cc1e1f08f",
    "f0-joint-psd-clique-model01-cold-replay.json": "da7dce5e6485a183b3e028ca72a5be5336137d3d7091d660af3187a6f4169bdc",
    "f0-joint-psd-clique-query-preparation01.json": "2dd9ec779de923db89fd040fb171c803135986ae1e57ff64707840c024ea4148",
    "f0-joint-psd-clique-query-preflight01.json": "7bc800b968c4d2d5ed0224d83e6337880ea8376c8490e05c8bcb89588ca0a17b",
    "f0-joint-psd-clique-native-audit01.json": "3938d098e2347956a4b447eab497e9826d5a2ffdc5e42cb8bede84378c30168c",
    "f0-joint-psd-clique-reuse-controls.json": "5ec84b5fb368a19d3d86c05e8722a3b54f75273625468daa1597d59561b96e43",
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def function(source, name):
    choices = [n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef) and n.name == name]
    assert len(choices) == 1
    return ast.dump(choices[0], include_attributes=False)


def review():
    for name, expected in SUBJECTS.items():
        assert sha((WORK/name).read_bytes()) == expected
    records = {}
    for name, expected in RECORDS.items():
        raw = (LOGS/name).read_bytes()
        assert sha(raw) == expected
        records[name] = json.loads(raw)
        assert records[name]["status"].startswith("PASS")
    substitutions = []
    for name in ("query", "replay", "native-audit"):
        path = LOGS/("f0-joint-psd-clique-"+name+"-substitutions.json")
        ledger = json.loads(path.read_bytes())
        old_raw, new_raw = [(ROOT/ledger[key]).read_bytes() for key in ("parent_path", "new_path")]
        assert sha(old_raw) == ledger["parent_sha256"] and sha(new_raw) == ledger["new_sha256"]
        transformed = old_raw.decode()
        counts = []
        for old, new in ledger["exact_text_substitutions"]:
            assert old in transformed
            counts.append(transformed.count(old))
            transformed = transformed.replace(old, new)
        assert transformed.encode() == new_raw
        assert ast.dump(ast.parse(transformed), include_attributes=False) == ast.dump(ast.parse(new_raw), include_attributes=False)
        substitutions.append({"adapter": name, "ledger_sha256": sha(path.read_bytes()),
                              "old_sha256": sha(old_raw), "new_sha256": sha(new_raw),
                              "exact_replacement_occurrences": counts, "complete_text_and_AST_match": True})
    old_exact = (WORK/"root_prism_free_f0_schur_path_exact_v3.py").read_text()
    new_exact = (WORK/"root_prism_free_f0_joint_psd_clique_exact.py").read_text()
    assert sha(old_exact.encode()) == "e039d525a93ab2972ac53538060feb7b6e16dd9f671bb051d29c543b6008b794"
    assert function(old_exact.replace("len(ray_hex) == 27764", "len(ray_hex) == 28043"), "exact_phase") == function(new_exact, "exact_phase")
    old_replay = (WORK/"root_prism_free_f0_schur_path_replay_v3.py").read_text()
    new_replay = (WORK/"root_prism_free_f0_joint_psd_clique_replay.py").read_text()
    for name in ("digest", "canonical", "number", "check_integer_certificate", "controls"):
        assert function(old_replay, name) == function(new_replay, name)
    native = records["f0-joint-psd-clique-native-audit01.json"]
    assert native["optimizer_calls"] == native["Highs_run_calls"] == native["getDualRay_calls"] == 0
    assert native["entire_native_CSC_indices_values_and_row_column_bounds_equal"]
    assert native["native_getNumNz_after_passModel"] == native["nonzeros_before_passModel"] == 1086559
    return {
        "status": "PASS: complete frozen-source review and independent adapter text/AST binding checks",
        "reviewer_source_sha256": sha(Path(__file__).read_bytes()),
        "subject_source_hashes": SUBJECTS, "bound_record_hashes": RECORDS,
        "complete_adapter_substitution_checks": substitutions,
        "exact_phase_unchanged_except_ray_dimension": True,
        "standalone_finite_box_integer_arithmetic_unchanged": True,
        "mathematical_review": {
            "prefix": "All15200 variables,6135 equalities,21629 old inequalities and27764 old scales remain unchanged.",
            "PSD_rows": "The21 saved directions are reconstructed and evaluated exactly; only proved zero coordinates are removed, with a positive normalization divisor. No point coordinate is assumed zero.",
            "edge_cliques": "Each literal bucket is a genuine neighbor clique: two chosen endpoints would have the center and two fixed sites as common neighbors. The inequality is sumY<=x_center, not a selector exclusion.",
            "transports": "All12 actual core transports are checked per row. Repeated quotient edge coordinates are added by Counter; no host automorphism is assumed.",
            "scale": "Every new coefficient and right side is divided by a positive dyadic scale and checked by exact Fraction comparison. The old scale prefix is retained.",
            "query": "One IPM/no-crossover call, with180-second owned-child bound. Existing-ray extraction is guarded by getDualRayExist; absent rays cause UNKNOWN without another optimizer.",
            "exact_acceptance": "Equality multipliers are unrestricted, inequality multipliers nonnegative. The unit-box minimum of the combined form is sum min(c_j,0); strict upper-minus-minimum negativity certifies infeasibility.",
            "scope": "Only92 specified PSD directions are enforced. A numerical proposal is not exact feasibility, and a numerical infeasibility result is not an exclusion."
        },
        "reported_model_counts_not_recomputed_here": {"variables": 15200, "equalities": 6135,
            "inequalities": 21908, "rows": 28043, "nonzeros": 1086559, "appended_rows": 279,
            "new_PSD_rows": 21, "core_pair_clique_rows": 258},
        "native_transport_gate_hash_bound_not_rerun": True,
        "subject_modules_imported": False, "models_rebuilt": 0, "censuses_repeated": 0,
        "eigenscans": 0, "optimizer_calls": 0, "graph_or_component_exclusion_claimed": False}


if __name__ == "__main__":
    path = LOGS/"f0-joint-psd-clique-independent-source-review.json"
    assert not path.exists()
    result = review()
    path.write_text(json.dumps(result, indent=2)+"\n")
    print(json.dumps(result, indent=2))
