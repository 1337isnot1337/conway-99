"""Static reuse checks for the bounded-fallback lazy continuation.

The runner changes only the exact-seed import, source bindings and two
status labels. Its limits and every query/prefix/replay function remain
unchanged. The fresh/cold proof wrapper changes only its runner import.
"""

import argparse
import ast
from copy import deepcopy
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
SOURCES = {
    'root_prism_free_f0_lazy_continuation.py': '156952c1239a102beb39150946199e8357ffc684d8eaf39f68ad0c575c043266',
    'root_prism_free_f0_lazy_continuation_certificate.py': '2776f9249b91b31a17d341e4d5b333aadbae7396bdf736e95197f63152d39abd',
    'root_prism_free_f0_bounded_lazy_seed.py': '4fee27c4fc99297d40cc24bf7adadcd4839df6e37ffc3bc1426cb368113c2715',
    'root_prism_free_f0_shared_bounded_fallback.py': '46ff20ca4269b71b80c2fd7e3ba2fec4f369b7dca3d4e08272a935cdfde72f1a',
    'root_prism_free_f0_bounded_lazy_continuation.py': '361484188521fc5c741be4aa8a7e1a10a9b4e76116ae51d8d9e76b272bc78dd2',
    'root_prism_free_f0_bounded_lazy_continuation_certificate.py': 'a234af13fe68e33ce16d4eb70b45a147e8d804be6fbe59c608f71c98020209db'}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def assignment(tree, name):
    found = [node for node in tree.body if isinstance(node, ast.Assign)
             and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)
             and node.targets[0].id == name]
    assert len(found) == 1
    return found[0]


class Labels(ast.NodeTransformer):
    substitutions = {
        'free480 bounded-fallback lazy continuation from1368 proved cuts prepared; no incidence/LP query':
            'free480 lazy continuation from1116 proved cuts prepared; no incidence/LP query',
        'cold bounded-fallback lazy base, all1368 exact cuts, retained explanations and population replay PASS':
            'cold lazy continuation base, all1116 exact cuts, retained explanations and population replay PASS'}

    def visit_Constant(self, node):
        if isinstance(node.value, str) and node.value in self.substitutions:
            return ast.copy_location(ast.Constant(self.substitutions[node.value]), node)
        return node


def import_replace(tree, old, new):
    matches = 0
    for node in tree.body:
        if isinstance(node, ast.Import):
            for item in node.names:
                if item.name == old:
                    item.name = new
                    matches += 1
    assert matches == 1


def calculate():
    for name, expected in SOURCES.items():
        assert digest(HERE/name) == expected
    old = ast.parse((HERE/'root_prism_free_f0_lazy_continuation.py').read_text())
    new = ast.parse((HERE/'root_prism_free_f0_bounded_lazy_continuation.py').read_text())
    limits = ast.literal_eval(assignment(old, 'LIMITS').value)
    assert ast.literal_eval(assignment(new, 'LIMITS').value) == limits
    dependencies = ast.literal_eval(assignment(new, 'DEPENDENCIES').value)
    assert dependencies.pop('root_prism_free_f0_bounded_lazy_seed.py') == SOURCES['root_prism_free_f0_bounded_lazy_seed.py']
    assert dependencies.pop('root_prism_free_f0_shared_bounded_fallback.py') == SOURCES['root_prism_free_f0_shared_bounded_fallback.py']
    old_dependencies = ast.literal_eval(assignment(old, 'DEPENDENCIES').value)
    del old_dependencies['root_prism_free_f0_lazy_continuation_seed.py']
    assert dependencies == old_dependencies
    normalized = Labels().visit(deepcopy(new))
    import_replace(normalized, 'root_prism_free_f0_bounded_lazy_seed', 'root_prism_free_f0_lazy_continuation_seed')
    assignment(normalized, 'DEPENDENCIES').value = deepcopy(assignment(old, 'DEPENDENCIES').value)
    assert ast.dump(normalized) == ast.dump(old)
    old_wrapper = ast.parse((HERE/'root_prism_free_f0_lazy_continuation_certificate.py').read_text())
    new_wrapper = ast.parse((HERE/'root_prism_free_f0_bounded_lazy_continuation_certificate.py').read_text())
    import_replace(new_wrapper, 'root_prism_free_f0_bounded_lazy_continuation', 'root_prism_free_f0_lazy_continuation')
    assert ast.dump(new_wrapper) == ast.dump(old_wrapper)
    return {'status': 'PASS: entire frozen runner and proof ASTs after declared seed/binding/status substitutions',
        'source_sha256': digest(Path(__file__)), 'bound_sources': SOURCES,
        'unchanged_limits': limits,
        'unchanged_runner_functions_after_two_status_substitutions':
            [node.name for node in old.body if isinstance(node, ast.FunctionDef)],
        'unchanged_proof_wrapper_functions':
            [node.name for node in old_wrapper.body if isinstance(node, ast.FunctionDef)],
        'entire_runner_AST_otherwise_identical': True,
        'entire_proof_wrapper_AST_otherwise_identical': True,
        'new_seed_and_shared_helper_require_separate_mathematical_source_review': True,
        'subject_modules_imported': False, 'CNF_rebuilt': False,
        'optimizer_or_solver_called': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    report = calculate()
    args.output.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2), flush=True)
