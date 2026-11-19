"""Map retained a=2 proof clauses to their original mathematical rows.

This performs no SAT or LP solve. It regenerates each formula as a stream,
matches its SHA256, and attributes every retained input clause to a source
count equation, packing clause, path implication, or exterior cap.
"""

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

from pysat.card import CardEnc, EncType
from pysat.formula import IDPool

from complement_rook_a2_fixed_certificate import clauses
from complement_rook_a2_fixed_completion import cap_plan, digest, domain


ROOT = Path(__file__).resolve().parents[2]
LOGS = ROOT/'experiments/logs/grids-and-triangles'


def inspect_case(case):
    prefix = 'complement-rook-a2-fixed-case'+str(case)
    model_path = LOGS/(prefix+'-model.json')
    certificate_path = LOGS/(prefix+'-certificate.json')
    model = json.loads(model_path.read_text())
    certificate = json.loads(certificate_path.read_text())
    assert digest(model_path) == certificate['model_manifest_sha256']
    for name, expected in model['source_hashes'].items():
        assert digest(Path(__file__).with_name(name)) == expected
    core_path = ROOT/certificate['core_file']
    assert digest(core_path) == certificate['core_sha256']
    retained = list(clauses(core_path))
    wanted = {tuple(sorted(clause)) for clause in retained}
    found = {}
    groups = {}
    hasher = hashlib.sha256()
    hasher.update(f"p cnf {model['variables']} {model['clauses']}\n".encode())
    generated_count = 0
    max_variable = 0

    def consume(new_clauses, tag, detail):
        nonlocal generated_count, max_variable
        for clause in new_clauses:
            assert clause
            hasher.update((' '.join(map(str, clause))+' 0\n').encode())
            generated_count += 1
            max_variable = max(max_variable, max(map(abs, clause)))
            key = tuple(sorted(clause))
            if key in wanted and key not in found:
                found[key] = tag
                groups.setdefault(tag, {**detail, 'retained_input_clauses': []})
                groups[tag]['retained_input_clauses'].append(list(clause))

    rows, signatures, need, edges, detail = domain(ROOT/model['census_path'], case)
    assert detail['selected_signature_sha256'] == model['selected_signature_sha256']
    pool = IDPool()
    variables = {edge: pool.id(('edge', *edge)) for edge in edges}
    incident = [[] for _ in signatures]
    for (a, b), variable in variables.items():
        incident[a].append((b, variable))
        incident[b].append((a, variable))
    counts = set()
    for t in range(72):
        for i in range(28):
            literals = [variable for s, variable in incident[t]
                        if i == 27 or i in signatures[s]]
            key = (tuple(literals), need[t][i])
            if key in counts:
                continue
            counts.add(key)
            assert 0 <= need[t][i] <= len(literals)
            encoded = CardEnc.equals(literals, need[t][i], vpool=pool,
                                     encoding=EncType.seqcounter)
            consume(encoded.clauses, ('count', t, i), {
                'kind': 'degree' if i == 27 else 'mixed',
                'outside_vertex': t, 'core_row': None if i == 27 else i,
                'target': need[t][i], 'edge_literals': literals,
            })
    assert (max_variable, generated_count) == (model['base_variables'], model['base_clauses'])
    plan = cap_plan(variables, signatures)
    packing = {}
    for a, b, overlap, _, paths in plan:
        if overlap == 2:
            for w, first, second in paths:
                packing.setdefault(tuple(sorted((-first, -second))), (a, b, w))
    for clause in sorted(packing):
        a, b, w = packing[clause]
        consume([clause], ('packing', *clause), {
            'kind': 'packing', 'outside_pair': [a, b],
            'core_overlap': 2, 'common_neighbor': w,
        })
    for a, b, overlap, direct, paths in plan:
        if overlap == 2:
            continue
        terms = [] if direct is None else [direct]
        for w, first, second in paths:
            path = pool.id(('path', a, b, w))
            consume([[-first, -second, path]], ('path', a, b, w), {
                'kind': 'path', 'outside_pair': [a, b],
                'common_neighbor': w, 'path_variable': path,
                'edge_variables': [first, second],
            })
            terms.append(path)
        if len(terms) > 2-overlap:
            encoded = CardEnc.atmost(terms, 2-overlap, vpool=pool,
                                     encoding=EncType.seqcounter)
            consume(encoded.clauses, ('cap', a, b), {
                'kind': 'cap', 'outside_pair': [a, b], 'core_overlap': overlap,
                'target': 2-overlap, 'direct_edge_variable': direct,
                'candidate_common_neighbors': [w for w, _, _ in paths],
            })
    assert generated_count == model['clauses'] and max_variable == model['variables']
    assert hasher.hexdigest() == model['cnf_sha256']
    assert set(found) == wanted
    graph_variables = sorted({abs(v) for clause in retained for v in clause
                              if abs(v) <= len(edges)})
    group_counts = Counter(group['kind'] for group in groups.values())
    clause_counts = Counter(groups[found[tuple(sorted(clause))]]['kind'] for clause in retained)
    result = {
        'case_index': case, 'full_cnf_sha256': model['cnf_sha256'],
        'model_manifest_sha256': digest(model_path),
        'certificate_sha256': digest(certificate_path),
        'retained_clauses': len(retained), 'all_retained_clauses_attributed': True,
        'group_counts': dict(group_counts), 'clause_counts': dict(clause_counts),
        'edge_variables_in_retained_formula': len(graph_variables),
        'used_graph_edges': [[v, *edges[v-1]] for v in graph_variables],
        'coordinate_triples': detail['coordinate_triples'],
        'groups': list(groups.values()),
    }
    return result


def run(output):
    cases = []
    for case in range(4):
        inspected = inspect_case(case)
        cases.append(inspected)
        print(json.dumps({key: inspected[key] for key in
                          ('case_index', 'retained_clauses', 'group_counts',
                           'clause_counts', 'edge_variables_in_retained_formula')}), flush=True)
    record = {
        'status': 'all four full-CNF stream hashes and retained-clause origins verified',
        'scope': 'proof inspection only; no new solve or broader exclusion',
        'source_sha256': digest(Path(__file__)), 'cases': cases,
    }
    output.write_text(json.dumps(record, indent=2)+'\n')
    return record


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    run(args.output)
