"""Read-only full-source/AST reuse check for the face99 query preparation."""
import argparse
import ast
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OLD = "rook_case4_face81_cover_generation.py"
NEW = "rook_case4_face99_cover_generation.py"
OLD_SHA = "f9aabb56194dc875b4f196c125e14dddceb25823a27b903fb597862b4c8a4efc"
NEW_SHA = "53baba0038f51dd8439d14b27378663febc45cf90917ecb26524e0f6f275adbf"
REPLACEMENTS = [
    ("proved81-zero", "proved99-zero"),
    ("All1984 native rows and1133", "All1966 native rows and1115"),
    ("complete168847-cover", "complete165969-cover"),
    ("rook_case4_face81_model", "rook_case4_face99_model"),
    ("d29369906b32b55a0ece17fa79025e86341269a689e8fc6dbbfd248b11985fff", "613e2de31570d56a2b1b52a164158a7ed9b80b4f8f834e550fbbc9c6e608e078"),
    ("21f3e08b0e7b8fcb0125cbb9fa8dc4d012c14563b7fb5bbc194bb0316a15962e", "c417a08853096bbb7a6d8148aca80a5f08249c19f2978f3f49a86ec0c20c301b"),
    ("3c06375df302220ee8470aa5de073a33daf1e8b7d7a98c8c94d1371472ede388", "7e75bbb360d91d6a4a424262c2c61ad5d7e0e13942a7b80a8ca39ec731ebf4af"),
    ("4d0b451ed3d8fd2712c3cd2ad136e3131cbde923f47582978a71d02589784c41", "1698c93e04c5a4682d595952a8628806da2231c801f2f7e4519db8bc09d466de"),
    ("1133, 170831, 1134, 171964, 11392423", "1115, 167935, 1116, 169050, 11014288"),
    ("NATIVE, COVER_POOL = 1984, 168847", "NATIVE, COVER_POOL = 1966, 165969"),
    ("'four_Gram_source_sha256':current['four_Gram_proof_source_sha256']", "'zero_seed_source_sha256':current['exact_zero_seed_source_sha256']"),
    ("'four_Gram_certificate_sha256':current['four_Gram_certificate_sha256']", "'zero_seed_certificate_sha256':current['exact_zero_seed_certificate_sha256']"),
    ("row170831+j", "row167935+j"),
    ("len(initial)==3117 and initial_nnz==28624", "len(initial)==3081 and initial_nnz==28207"),
    ("one of the81 proved-zero", "one of the99 proved-zero"),
    ("face81", "face99"),
]


def check():
    old, new = (HERE/OLD).read_bytes(), (HERE/NEW).read_bytes()
    assert hashlib.sha256(old).hexdigest() == OLD_SHA
    assert hashlib.sha256(new).hexdigest() == NEW_SHA
    expected = old.decode()
    counts = []
    for before, after in REPLACEMENTS:
        assert before in expected
        counts.append(expected.count(before))
        expected = expected.replace(before, after)
    assert expected == new.decode()
    tree = ast.parse(new)
    assert ast.dump(tree, include_attributes=False) == ast.dump(ast.parse(expected), include_attributes=False)
    old_tree = ast.parse(old)
    assignments = lambda t: {n.targets[0].id: n.value for n in t.body if isinstance(n, ast.Assign)
                             and isinstance(n.targets[0], ast.Name)}
    assert ast.dump(assignments(tree)["LIMITS"]) == ast.dump(assignments(old_tree)["LIMITS"])
    assert ast.dump(assignments(tree)["OPTIONS"]) == ast.dump(assignments(old_tree)["OPTIONS"])
    return {"status": "PASS: complete face99 driver equals frozen face81 driver after explicit binding/dimension substitutions",
            "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "parent_driver_sha256": OLD_SHA, "driver_sha256": NEW_SHA,
            "substitutions": [[a, b, c] for (a, b), c in zip(REPLACEMENTS, counts)],
            "all_function_names_checked": [n.name for n in tree.body if isinstance(n, ast.FunctionDef)],
            "entire_source_equality_checked": True, "entire_module_AST_checked": True,
            "unchanged_limits_and_options": True,
            "new_model_and_zero_premise_bindings_require_separate_source_review": True,
            "subject_source_imported": False, "matrix_rebuilt": False, "optimizer_called": False}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    assert not args.output.exists()
    report = check()
    args.output.write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
