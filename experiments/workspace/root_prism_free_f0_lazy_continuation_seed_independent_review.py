"""Read-only source gate for the terminal-registry continuation seed.

No subject module, model builder, optimizer, SAT solver, or proof
checker is imported. The mathematical statements record a source
review; the AST and hash comparisons below are directly replayable.
"""

import argparse
import ast
import copy
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
EXPECTED = {
    'root_prism_free_f0_lazy_continuation_seed.py': '7535defe050dbdc943ed13e414b9286fbf177621ec7abf881be95338a1adb123',
    'root_prism_free_f0_lazy_continuation.py': '156952c1239a102beb39150946199e8357ffc684d8eaf39f68ad0c575c043266',
    'root_prism_free_f0_lazy_continuation_certificate.py': '2776f9249b91b31a17d341e4d5b333aadbae7396bdf736e95197f63152d39abd',
    'root_prism_free_f0_lazy_row_loop.py': '7b8301c96329ecbc6610c3dd74809793029e2e13d57027c7b7f9756bfd859e07',
    'root_prism_free_f0_lazy_row_loop_certificate.py': 'e34b8084add389df0ff1354971573c5b0fe60c5ede423b33324ee84897a14558',
    'root_prism_free_f0_lazy_clauses.py': 'cef5448b012be57277b87297d2e3ec2c017ccea1336080f4c40c2594f2ab7640',
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def named_assignment(tree, name):
    matches = [node for node in tree.body if isinstance(node, ast.Assign)
               and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)
               and node.targets[0].id == name]
    assert len(matches) == 1
    return matches[0]


def calculate():
    for name, expected in EXPECTED.items():
        assert digest(HERE / name) == expected
    old = ast.parse((HERE / 'root_prism_free_f0_lazy_row_loop.py').read_text())
    new = ast.parse((HERE / 'root_prism_free_f0_lazy_continuation.py').read_text())
    before = ast.literal_eval(named_assignment(old, 'LIMITS').value)
    after = ast.literal_eval(named_assignment(new, 'LIMITS').value)
    assert after == dict(before, maximum_row_passes=100, maximum_SAT_refinement_calls=1000)
    prior_dependencies = ast.literal_eval(named_assignment(old, 'DEPENDENCIES').value)
    new_dependencies = ast.literal_eval(named_assignment(new, 'DEPENDENCIES').value)
    assert new_dependencies == dict(prior_dependencies, **{
        'root_prism_free_f0_lazy_continuation_seed.py': EXPECTED['root_prism_free_f0_lazy_continuation_seed.py']})
    named_assignment(new, 'LIMITS').value = copy.deepcopy(named_assignment(old, 'LIMITS').value)
    named_assignment(new, 'DEPENDENCIES').value = copy.deepcopy(named_assignment(old, 'DEPENDENCIES').value)
    replacements = {
        'free480 lazy continuation from1116 proved cuts prepared; no incidence/LP query':
            'free480 lazy732-cut continuation prepared; no incidence/LP query',
        'cold lazy continuation base, all1116 exact cuts, retained explanations and population replay PASS':
            'cold lazy base, all732 exact cuts, seed explanations and population replay PASS',
    }
    imports = labels = 0
    for node in ast.walk(new):
        if isinstance(node, ast.alias) and node.name == 'root_prism_free_f0_lazy_continuation_seed':
            node.name = 'root_prism_free_f0_lazy_clauses'
            imports += 1
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and node.value in replacements:
            node.value = replacements[node.value]
            labels += 1
    assert imports == 1 and labels == 2
    assert ast.dump(new, include_attributes=False) == ast.dump(old, include_attributes=False)
    prior_wrapper = ast.parse((HERE / 'root_prism_free_f0_lazy_row_loop_certificate.py').read_text())
    new_wrapper = ast.parse((HERE / 'root_prism_free_f0_lazy_continuation_certificate.py').read_text())
    changed = 0
    for node in ast.walk(new_wrapper):
        if isinstance(node, ast.alias) and node.name == 'root_prism_free_f0_lazy_continuation':
            node.name = 'root_prism_free_f0_lazy_row_loop'
            changed += 1
    assert changed == 1
    assert ast.dump(new_wrapper, include_attributes=False) == ast.dump(prior_wrapper, include_attributes=False)
    return {
        'status': 'PASS: terminal seed and inherited continuation/proof source review',
        'source_sha256': digest(Path(__file__)), 'reviewed_source_hashes': EXPECTED,
        'independent_entire_runner_AST_comparison': True,
        'independent_entire_proof_wrapper_AST_comparison': True,
        'allowed_runner_changes': ['terminal-seed import and exact source binding',
                                   'row-pass maximum20 to100', 'SAT-call maximum500 to1000',
                                   'two descriptive status strings'],
        'unchanged_overall_seconds': after['overall_seconds'],
        'seed_source_review': {
            'complete_frozen_parent_reconstruct_required_in_both_modes': True,
            'parent_result_cold_replay_manifest_and_all_manifest_files_bound': True,
            'all1008_individual_and108_symmetric_cuts_retained': True,
            'base56994_clauses_plus1980_reverified_explanations_equal_parent58974': True,
            'all_old_registry_indices_and_exact_explanation_predicates_preserved': True,
            'only_starting_registry_digest_rebased_to_canonical_complete_contents': True,
            'clause_digest_and_full_clause_order_unchanged': True,
            'terminal_candidate_is_rechecked_after_updating_only_snapshot_fields': True,
            'terminal_candidate_not_added_as_units_assumptions_or_phases': True,
            'population60_premise_and_all12_core_actions_inherited_from_full_replay': True,
            'all480_selectors_and_second_component_remain_free': True,
            'no_visitation_block_or_new_symmetry_constraint': True,
        },
        'scope': 'Source/mathematical review and independent static comparisons only. No new certificate replay or numerical claim.',
        'subject_imported': False, 'CNF_rebuilt': False, 'registry_replayed': False,
        'optimizer_solver_or_DRAT_called': False,
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    report = calculate()
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2), flush=True)
    print('report_sha256', digest(args.output), flush=True)
