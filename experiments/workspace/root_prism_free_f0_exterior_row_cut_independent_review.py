"""Small independent domain, transport, guard, and byte review; no solver.

This does not rerun the retained exterior proof or its clause attribution.
It checks the integer row inequalities directly, reconstructs every actual
core relabeling, and compares the prepared formula with its unchanged base.
"""

import argparse
import gzip
import hashlib
from itertools import combinations, product
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LOGS = ROOT / 'experiments/logs/root-prism-free'
WORK = ROOT / 'experiments/workspace'
BINDINGS = {
    'root_prism_free_f0_first_design_exterior_row_audit.py':
        'd9e70f8d0f979505b0c5f264969e3b72f300d1f2da0491b41b760301c9e666df',
    'root_prism_free_f0_exterior_row_cut_overlay.py':
        '0a1739251220c3b27564cc9ea0d2e64bad4c9aa8db9a93182fc7cc91ea7c0353',
}
FILES = {
    'f0-exterior-row-cut-overlay-model.json':
        '15d924357d89ab74f554ffa58a8da7559f7f5684711bf57e49f2eb23dcbccb7b',
    'f0-incidence-case00-model.json':
        '16deda266149f5123a1db3833cfebf22d6bdfe4426b1424fcc51ccbfdc38f0a1',
    'f0-first-design-exterior-row-certificate.json.gz':
        '3b5c302f9a9e3bfce6175de7c73cb835cc89f88e63148de15d59085b1da974c0',
    'f0-pair-gram-certificate.json.gz':
        'edb85ff422222961e6bc9b36322b74bcfce455bca262d6e189d7768f9ac91c98',
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode()


def calculate():
    for name, expected in BINDINGS.items():
        assert sha((WORK / name).read_bytes()) == expected
    saved = {}
    for name, expected in FILES.items():
        raw = (LOGS / name).read_bytes()
        assert sha(raw) == expected
        saved[name] = json.loads(gzip.decompress(raw) if name.endswith('.gz') else raw)
    old = saved['f0-pair-gram-certificate.json.gz']
    joined = list(map(int, old['joined_core_rows']))
    core = [r & ((1 << 21) - 1) for r in joined[:21]]
    A = [[(core[i + 3] >> (j + 3)) & 1 for j in range(18)] for i in range(18)]
    G = [[12 * (i == j) + 2 - (joined[i + 3] & joined[j + 3]).bit_count()
          - A[i][j] for j in range(18)] for i in range(18)]
    triples = [list(h) for h in combinations(range(18), 3)
               if max(sum(v // 6 == f for v in h) for f in range(3)) <= 2
               and all(G[i][j] > 0 for i, j in combinations(h, 2))
               and all(sum((i == j) + A[i][j] for j in h) <= 2 for i in range(18))]
    assert triples == old['component_triples'] and len(triples) == 480
    positions = {tuple(h): i for i, h in enumerate(triples)}
    masks = [sum(1 << i for i in h) for h in triples]
    Q = [[2 - sum((i == j) + A[i][j] for j in h) for i in range(18)] for h in triples]
    cert = saved['f0-first-design-exterior-row-certificate.json.gz']['row_certificate']
    cuts = cert['transported_cuts']
    assert len(cuts) == 12 and len({c['target_signature'] for c in cuts}) == 12
    base = cert['base_cut']
    base_vector = base['integer_vector']
    moves = []
    clauses = []
    for cut in cuts:
        move = cut['component_relabeling']
        assert sorted(move) == list(range(18))
        root_move = [move[6 * i] // 6 for i in range(3)]
        full_move = root_move + [j + 3 for j in move]
        assert sorted(full_move) == list(range(21))
        assert all((core[i] >> j & 1) == (core[full_move[i]] >> full_move[j] & 1)
                   for i in range(21) for j in range(21))
        moves.append(tuple(full_move))
        action = [positions[tuple(sorted(move[j] for j in h))] for h in triples]
        assert sorted(action) == list(range(480))
        assert sha(canonical(action)) == cut['signature_action_sha256']
        target = cut['target_signature']
        assert target == action[base['target_signature']]
        vector = cut['integer_vector']
        assert all(vector[move[i]] == base_vector[i] for i in range(18))
        possible = [b for b in range(480) if b != target
                    and (masks[b] & masks[target]).bit_count() <= 1
                    and all(Q[target][i] > 0 for i in triples[b])
                    and all(Q[b][i] > 0 for i in triples[target])]
        assert len(possible) == 232
        assert sum(vector[i] * Q[target][i] for i in range(18)) == 6
        positive = [[b, sum(vector[i] for i in triples[b])] for b in possible
                    if sum(vector[i] for i in triples[b]) > 0]
        assert positive == cut['positive_integer_weights']
        assert len(positive) == 55 and all(w % 3 == 0 for b, w in positive)
        weights = [[b, min(2, w // 3)] for b, w in positive]
        assert weights == cut['binary_capped_weights']
        one = [b for b, w in weights if w == 1]
        two = [b for b, w in weights if w == 2]
        assert (len(one), len(two)) == (36, 19)
        expected = [[-target - 1] + [b + 1 for b in one + two]]
        expected += [[-target - 1, -a - 1] + [b + 1 for b in one + two if b != a] for a in one]
        assert expected == cut['guarded_clauses']
        clauses.extend(expected)
    group = set(moves)
    assert len(group) == 12 and tuple(range(21)) in group
    assert all(tuple(g[h[i]] for i in range(21)) in group for g in group for h in group)
    assert clauses == cert['all_guarded_clauses']
    assert len({tuple(sorted(c)) for c in clauses}) == 444

    # Independent exhaustive small Boolean control for the clause pattern.
    controls = 0
    for n in range(5):
        for m in range(5):
            for bits in product((0, 1), repeat=1 + n + m):
                guard, singles, doubles = bits[0], bits[1:1+n], bits[1+n:]
                truth = not guard or any(singles) or any(doubles)
                truth = truth and all(not guard or not singles[i] or any(doubles)
                                      or any(singles[j] for j in range(n) if j != i) for i in range(n))
                assert truth == (sum(singles) + 2 * sum(doubles) >= 2 * guard)
                controls += 1
    assert controls == 1922

    model = saved['f0-exterior-row-cut-overlay-model.json']
    baseline = saved['f0-incidence-case00-model.json']
    old_raw = Path(baseline['cnf']).read_bytes()
    new_raw = Path(model['cnf']).read_bytes()
    assert sha(old_raw) == baseline['cnf_sha256'] == model['base_cnf_sha256']
    assert sha(new_raw) == model['cnf_sha256']
    old_lines, new_lines = old_raw.splitlines(), new_raw.splitlines()
    assert old_lines[0] == b'p cnf 28308 56550'
    assert new_lines[0] == b'p cnf 28308 56994'
    assert new_lines[1:56551] == old_lines[1:]
    assert new_lines[56551:] == [(' '.join(map(str, c)) + ' 0').encode() for c in clauses]
    assert sha(canonical(clauses)) == model['clause_suffix_sha256']
    assert model['fixed_incidence_design'] is False and model['graph_symmetry_constraints'] is False
    return {
        'status': 'independent exact row-cut transport, Boolean guard and unchanged-prefix audit PASS',
        'source_sha256': sha(Path(__file__).read_bytes()),
        'reviewed_source_hashes': BINDINGS, 'checked_artifact_hashes': FILES,
        'complete_signature_domain': 480, 'cut_targets': [c['target_signature'] for c in cuts],
        'actual_core_relabelings_checked': 12, 'group_compositions_checked': 144,
        'universal_neighbors_per_target': 232, 'positive_terms_per_cut': 55,
        'integer_demand': 6, 'weight_divisor': 3, 'capped_threshold': 2,
        'guard_truth_assignments': controls, 'unchanged_base_clause_lines': 56550,
        'exact_added_primary_clauses': 444, 'new_auxiliaries': 0,
        'base_CNF_sha256': baseline['cnf_sha256'], 'overlay_CNF_sha256': model['cnf_sha256'],
        'necessity': 'Multiply the actual selected target row by v; discard nonpositive products; '
                     'use neighbor activation y_b<=x_b. Divide positive weights by3 and cap at2. '
                     'Each guarded cut is necessary for every completion in the stated component case.',
        'scope': model['scope'], 'base_builder_imported': False, 'CNF_rebuilt': False,
        'solver_or_optimizer_called': False, 'retained_DRAT_or_attribution_replayed': False,
        'source_review': 'The inspector checks the original incidence plus all cuts and claims only '
                         'partial incidence. Cold proof replay binds the complete formula and retained '
                         'input inclusion. No fixed incidence or graph automorphism is imposed.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    report = calculate()
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
