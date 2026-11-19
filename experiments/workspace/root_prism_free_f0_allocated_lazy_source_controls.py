"""AST controls for the allocated continuation and unchanged proof gate."""

import argparse
import ast
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
FILES = {
    'root_prism_free_f0_bounded_lazy_continuation.py': '361484188521fc5c741be4aa8a7e1a10a9b4e76116ae51d8d9e76b272bc78dd2',
    'root_prism_free_f0_allocated_lazy_continuation.py': '46b30a4e7c64db612cff606bd56aa05da44356547f617e977a8fa17ac0da4c8d',
    'root_prism_free_f0_bounded_lazy_continuation_certificate.py': 'a234af13fe68e33ce16d4eb70b45a147e8d804be6fbe59c608f71c98020209db',
    'root_prism_free_f0_allocated_lazy_continuation_certificate.py': '1ca1ba702f7e50aa49dba01cc6fe34bdb1f64c106abc0c5438d9c2aa397d318f'}


def calculate():
    trees = {}
    for name, expected in FILES.items():
        path = HERE/name
        assert hashlib.sha256(path.read_bytes()).hexdigest() == expected
        trees[name] = ast.parse(path.read_text())
    old, new = [trees[n] for n in list(FILES)[:2]]
    functions = [{node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)} for tree in (old, new)]
    unchanged = ['save_gzip', 'check_sources', 'formula', 'inspect_candidate', 'symmetric_candidates',
                 'explain_candidate', 'add_row_cuts', 'bound_record', 'replay_batch']
    for name in unchanged:
        assert ast.dump(functions[0][name]) == ast.dump(functions[1][name])
    changed = sorted(name for name in functions[0] if name not in unchanged)
    assert changed == ['checked_preparation', 'finish_step', 'input_state', 'prepare', 'reconstruct', 'run']
    assert set(functions[1])-set(functions[0]) == {'apply_quadratic', 'shared_family_origin'}
    limits = []
    for tree in (old, new):
        nodes = [node for node in tree.body if isinstance(node, ast.Assign)
                 and any(isinstance(t, ast.Name) and t.id == 'LIMITS' for t in node.targets)]
        assert len(nodes) == 1
        limits.append(ast.literal_eval(nodes[0].value))
    assert limits[0] == limits[1] and limits[1]['overall_seconds'] == 180
    old_proof, new_proof = [trees[n] for n in list(FILES)[2:]]
    matches = 0
    for node in new_proof.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == 'root_prism_free_f0_allocated_lazy_continuation':
                    alias.name = 'root_prism_free_f0_bounded_lazy_continuation'; matches += 1
    assert matches == 1 and ast.dump(old_proof) == ast.dump(new_proof)
    return {'status': 'unchanged candidate/clause gates, limits and full proof-wrapper AST controls PASS',
        'source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), 'file_hashes': FILES,
        'unchanged_loop_functions': unchanged, 'review_required_changed_loop_functions': changed,
        'new_loop_functions': ['apply_quadratic', 'shared_family_origin'], 'unchanged_limits': limits[1],
        'proof_wrapper_entire_AST_identical_after_single_import': True,
        'new_loop_semantics_require_separate_source_review': True, 'subject_import_or_solver_called': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    result = calculate(); args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2), flush=True)
