"""Static exact reuse controls for the separate lazy continuation.

Parse source text only. The new runner differs only in its terminal-seed
import/binding, two requested budgets, and two descriptive status labels.
Every proof-wrapper function is unchanged. No subject module is imported.
"""

import argparse
import ast
from copy import deepcopy
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
SOURCES = {
    'root_prism_free_f0_lazy_row_loop.py': '7b8301c96329ecbc6610c3dd74809793029e2e13d57027c7b7f9756bfd859e07',
    'root_prism_free_f0_lazy_row_loop_certificate.py': 'e34b8084add389df0ff1354971573c5b0fe60c5ede423b33324ee84897a14558',
    'root_prism_free_f0_lazy_continuation_seed.py': '7535defe050dbdc943ed13e414b9286fbf177621ec7abf881be95338a1adb123',
    'root_prism_free_f0_lazy_continuation.py': '156952c1239a102beb39150946199e8357ffc684d8eaf39f68ad0c575c043266',
    'root_prism_free_f0_lazy_continuation_certificate.py': '2776f9249b91b31a17d341e4d5b333aadbae7396bdf736e95197f63152d39abd'}


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
        'free480 lazy continuation from1116 proved cuts prepared; no incidence/LP query':
            'free480 lazy732-cut continuation prepared; no incidence/LP query',
        'cold lazy continuation base, all1116 exact cuts, retained explanations and population replay PASS':
            'cold lazy base, all732 exact cuts, seed explanations and population replay PASS'}

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
    old = ast.parse((HERE/'root_prism_free_f0_lazy_row_loop.py').read_text())
    new = ast.parse((HERE/'root_prism_free_f0_lazy_continuation.py').read_text())
    original_limits = ast.literal_eval(assignment(old, 'LIMITS').value)
    continued_limits = ast.literal_eval(assignment(new, 'LIMITS').value)
    assert continued_limits == dict(original_limits, maximum_row_passes=100,
                                   maximum_SAT_refinement_calls=1000)
    dependencies = ast.literal_eval(assignment(new, 'DEPENDENCIES').value)
    extra = dependencies.pop('root_prism_free_f0_lazy_continuation_seed.py')
    assert extra == SOURCES['root_prism_free_f0_lazy_continuation_seed.py']
    assert dependencies == ast.literal_eval(assignment(old, 'DEPENDENCIES').value)
    normalized = Labels().visit(deepcopy(new))
    import_replace(normalized, 'root_prism_free_f0_lazy_continuation_seed', 'root_prism_free_f0_lazy_clauses')
    assignment(normalized, 'LIMITS').value = deepcopy(assignment(old, 'LIMITS').value)
    assignment(normalized, 'DEPENDENCIES').value = deepcopy(assignment(old, 'DEPENDENCIES').value)
    assert ast.dump(normalized) == ast.dump(old)
    functions = [node.name for node in old.body if isinstance(node, ast.FunctionDef)]
    old_wrapper = ast.parse((HERE/'root_prism_free_f0_lazy_row_loop_certificate.py').read_text())
    new_wrapper = ast.parse((HERE/'root_prism_free_f0_lazy_continuation_certificate.py').read_text())
    import_replace(new_wrapper, 'root_prism_free_f0_lazy_continuation', 'root_prism_free_f0_lazy_row_loop')
    assert ast.dump(new_wrapper) == ast.dump(old_wrapper)
    proof_functions = [node.name for node in old_wrapper.body if isinstance(node, ast.FunctionDef)]
    return {'status': 'PASS: exact frozen runner/proof reuse after declared seed/limit/label changes',
        'source_sha256': digest(Path(__file__)), 'bound_sources': SOURCES,
        'unchanged_runner_functions_after_two_status_label_substitutions': functions,
        'unchanged_proof_wrapper_functions': proof_functions,
        'entire_runner_AST_otherwise_identical': True, 'entire_proof_wrapper_AST_otherwise_identical': True,
        'only_limit_changes': {'maximum_row_passes': [20, 100], 'maximum_SAT_refinement_calls': [500, 1000]},
        'continued_limits': continued_limits, 'new_mathematical_initialization_review_required': True,
        'subject_modules_imported': False, 'optimizer_or_solver_called': False, 'CNF_rebuilt': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    report = calculate()
    args.output.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2), flush=True)
