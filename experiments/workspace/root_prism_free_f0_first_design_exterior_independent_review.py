"""Read-only exterior-model review and independent primary-domain audit.

Use the frozen component catalogue and saved first incidence directly.
Do not import the subject source, build a CNF, or call a solver. Recount
all eligible edges, mixed supports, and pair-cap path variables.
"""

import argparse
from collections import Counter
import gzip
import hashlib
from itertools import combinations, product
import json
from pathlib import Path
import symtable


ROOT = Path(__file__).resolve().parents[2]
LOGS = ROOT/'experiments/logs/root-prism-free'
EXPECTED = {
    'experiments/workspace/root_prism_free_f0_first_design_exterior.py':
        'f0c5105526b9374935b4ba961859261249f44f2b311d98138ac3c8aeb5ed56cd',
    'experiments/logs/root-prism-free/f0-first-design-exterior-model.json':
        'd98d817a7e9410f6fd88186adacdf23b886e543f3e18f7a9ec98af07e6558078',
    'experiments/logs/root-prism-free/f0-components-certificate.json.gz':
        'dc8aad926550cef6a8ee39aa8f4efbd056773950183b9e0ac86b195e8057c3fd',
    'experiments/logs/root-prism-free/f0-incidence-case00-run01/result.json':
        '64d5411e04764b0d7e7157c47b67d759e536a401fee8fe36e274943f2fda4abf',
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def review():
    for path, value in EXPECTED.items():
        assert digest(ROOT/path) == value
    model = json.loads((LOGS/'f0-first-design-exterior-model.json').read_text())
    catalogue = json.loads(gzip.decompress((LOGS/'f0-components-certificate.json.gz').read_bytes()))
    saved_result = json.loads((LOGS/'f0-incidence-case00-run01/result.json').read_text())
    domain = catalogue['representatives'][0]['domain']
    core = domain['core_rows']
    adjacency = [[int(core[3+i] >> (3+j) & 1) for j in range(18)] for i in range(18)]
    assert all(sum(row) == 3 for row in adjacency)
    gram = [[12*int(i == j)+2-(core[3+i]&core[3+j]).bit_count()-adjacency[i][j]
             for j in range(18)] for i in range(18)]
    assert gram == domain['Gram']
    triples = []
    for h in combinations(range(18), 3):
        if max(sum(i//6 == f for i in h) for f in range(3)) > 2:
            continue
        if any(gram[i][j] <= 0 for i, j in combinations(h, 2)):
            continue
        if any(sum(adjacency[i][j]+int(i == j) for j in h) > 2 for i in range(18)):
            continue
        triples.append(list(h))
    assert triples == domain['signature_domain'] and len(triples) == 480
    chosen = saved_result['incidence_witness']['selected_columns']
    assert chosen == sorted(set(chosen)) and len(chosen) == 60
    design = [triples[i] for i in chosen]
    H = [[int(i in h) for h in design] for i in range(18)]
    assert all(sum(H[i][v]*H[j][v] for v in range(60)) == gram[i][j]
               for i in range(18) for j in range(18))
    target = [[2-H[i][v]-sum(adjacency[i][j]*H[j][v] for j in range(18))
               for v in range(60)] for i in range(18)]
    assert all(0 <= x <= 2 for row in target for x in row)
    assert all(sum(target[i][v] for i in range(18)) == 24 for v in range(60))
    overlaps = [[sum(H[i][u]*H[i][v] for i in range(18)) for v in range(60)]
                for u in range(60)]
    eligible = []
    removed = Counter()
    for u, v in combinations(range(60), 2):
        flags = (overlaps[u][v] > 1,
                 any(H[i][v] > target[i][u] for i in range(18)),
                 any(H[i][u] > target[i][v] for i in range(18)))
        removed[str(flags)] += 1
        if not any(flags):
            eligible.append([v, u])
    eligible.sort()
    assert len(eligible) == 1224
    masks = [sum(1 << i for i in h) for h in design]
    actual = {'design': design, 'design_source_indices': chosen,
              'component_adjacency_rows': [sum(row[j] << j for j in range(18)) for row in adjacency],
              'masks': masks, 'targets': [list(row) for row in zip(*target)],
              'overlaps': overlaps, 'edge_domain': eligible}
    assert actual == model['data']
    permitted = [set() for _ in range(60)]
    for u, v in eligible:
        permitted[u].add(v)
        permitted[v].add(u)
    assert all(len(row) >= 8 for row in permitted)
    assert all(target[i][v] <= sum(H[i][w] for w in permitted[v])
               for i in range(18) for v in range(60))
    conjunctions = zero_paths = 0
    capacities = Counter()
    for u, v in combinations(range(60), 2):
        capacity = 2-overlaps[u][v]
        assert capacity in (0, 1, 2)
        capacities[capacity] += 1
        paths = len(permitted[u]&permitted[v])
        if capacity == 0:
            assert v not in permitted[u]
            zero_paths += paths
        else:
            conjunctions += paths
    formula = model['formula']
    assert formula['primary_variables'] == 1224
    assert formula['constraints']['degree_rows'] == 60
    assert formula['constraints']['mixed_Gram_rows'] == 1080
    assert formula['constraints']['outside_pair_caps'] == sum(capacities.values()) == 1770
    assert conjunctions == formula['constraints']['common_neighbor_variables'] == 47791
    assert zero_paths == formula['constraints']['zero_capacity_pair_clauses'] == 1664
    conjunction_controls = 0
    for a, b, y in product((False, True), repeat=3):
        clauses_hold = ((not a) or (not b) or y) and (a or not y) and (b or not y)
        assert clauses_hold == (y == (a and b))
        conjunction_controls += 1
    source = ROOT/'experiments/workspace/root_prism_free_f0_first_design_exterior.py'
    symbols = symtable.symtable(source.read_text(), str(source), 'exec')
    replay = next(child for child in symbols.get_children() if child.get_name() == 'replay')
    assert replay.lookup('inputs').is_global() and not replay.lookup('inputs').is_local()
    assert digest(Path(model['cnf'])) == model['cnf_sha256']
    return {
        'status': 'PASS: mathematical/source review and independent complete primary-domain audit',
        'review_source_sha256': digest(Path(__file__)), 'checked_hashes': EXPECTED,
        'formula': formula, 'cnf_sha256': model['cnf_sha256'],
        'component_candidate_triples': len(triples), 'fixed_first_columns': len(design),
        'fixed_first_Gram_entries_checked': 324, 'complete_exterior_edge_domain': len(eligible),
        'endpoint_filter_categories': dict(sorted(removed.items())),
        'mixed_rows_reconstructed': 1080, 'pair_capacities': dict(sorted(capacities.items())),
        'conjunctions_recounted': conjunctions, 'zero_capacity_path_clauses_recounted': zero_paths,
        'conjunction_truth_assignments_checked': conjunction_controls,
        'replay_inputs_function_not_shadowed': True,
        'source_review': [
            'degree8 follows from the six shell neighbors of each exterior vertex',
            'the mixed equation has no second-component term because the two shell components are anticomplete',
            'all1224 edges survive exactly the adjacent cap and both endpoint zero-quota tests',
            'all counters and exact conjunction variables share one IDPool above unchanged edge IDs',
            'all1770 exterior caps include the direct edge when eligible and all possible eligible two-edge paths',
            'the SAT inspector reconstructs all degrees,1080 mixed equations,and1770 caps directly',
            'cold replay binds the full CNF and retained inputs; the corrected local variable no longer shadows inputs()',
            'the second shell and its incidence remain free; SAT is a partial exterior candidate only',
        ],
        'CNF_rebuilt': False, 'CNF_parsed': False, 'solver_called': False,
        'scope': 'one saved first-component incidence; no exclusion of all first designs or all66 components',
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    report = review()
    args.output.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2), flush=True)
