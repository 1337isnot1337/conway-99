"""Direct domain/vector/byte audit for the20-case continuation overlays.

Generalizes the reviewed cases9/10 direct audit in a new source. It imports
neither overlay builder nor downdate machinery. A non-author must still
review this generalized source before the new solver queries.
"""

import argparse
from itertools import combinations
import gzip
import hashlib
import json
from pathlib import Path
import time

import complement_rook_projector_schur as base


ROOT = Path(__file__).resolve().parents[2]
LOGS = ROOT/'experiments/logs/grids-and-triangles'
BINDINGS = {
    4: (1214, 30), 5: (1157, 92), 6: (1160, 27), 7: (1230, 86),
    11: (1257, 22), 12: (1193, 57), 13: (1203, 21), 14: (1267, 65),
    15: (1286, 8), 16: (1228, 28), 17: (1330, 10), 18: (1265, 26),
    19: (1271, 6), 20: (1264, 7), 22: (1291, 8), 23: (1360, 10),
    24: (1336, 10), 25: (1399, 11), 26: (1332, 5), 27: (1325, 5),
}
assert sorted(BINDINGS) == sorted(set(range(28))-{0, 1, 2, 3, 8, 9, 10, 21})



def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(case_index, model_path, model_sha256):
    expected_columns, expected_cuts = BINDINGS[case_index]
    assert digest(model_path) == model_sha256
    model = json.loads(model_path.read_text())
    for name, expected_hash in model['source_hashes'].items():
        assert digest(Path(__file__).with_name(name)) == expected_hash
    base_path, cert_path, fragment = (ROOT/model[key] for key in ('base_model', 'certificate', 'binary_fragment'))
    for path, key in ((base_path, 'base_model'), (cert_path, 'certificate'), (fragment, 'binary_fragment')):
        assert digest(path) == model[key+'_sha256']
    original = json.loads(base_path.read_text())
    saved = json.loads(gzip.decompress(cert_path.read_bytes()))
    assert saved['case'] == model['case'] == original['case']
    assert saved['case']['index'] == case_index
    index_path = LOGS/'complement-rook-35core-domains-prefix01/all-core-index.json'
    assert digest(index_path) == saved['complete_index_sha256']
    assert json.loads(index_path.read_text())['cases'][case_index] == saved['case']
    for key in ('domain_record_sha256', 'column_domain_sha256', 'Gram_sha256'):
        assert saved[key] == model[key] == original[key]
    rows, _, _, signatures, masks, _, _ = base.domain()
    core = list(rows)+[0]*8
    for i, source in enumerate(saved['case']['selected_signatures'], 27):
        for j in signatures[source]:
            core[i] |= 1 << j
            core[j] |= 1 << i
    for a, b in saved['case']['matching']:
        core[27+a] |= 1 << (27+b)
        core[27+b] |= 1 << (27+a)
    assert core == saved['core_adjacency_bit_rows']
    gram = [[12*int(i == j)+2-(core[i]&core[j]).bit_count()-int(core[i] >> j & 1)
             for j in range(35)] for i in range(35)]
    assert gram == saved['Gram']
    columns, raw_count = [], 0
    for source, sites in enumerate(signatures):
        if 0 in sites:
            continue
        demand = 2-(rows[0]&masks[source]).bit_count()
        for attachment in range(256):
            if attachment.bit_count() != demand:
                continue
            raw_count += 1
            support = list(sites)+[27+i for i in range(8) if attachment >> i & 1]
            if any(gram[i][j] <= 0 for i in support for j in support):
                continue
            if any(sum((core[i] >> j & 1)+int(i == j) for j in support) > 2 for i in range(35)):
                continue
            columns.append([source, attachment])
    columns.sort()
    assert raw_count == 3120 and len(columns) == expected_columns and columns == saved['attachment_columns']
    full_masks = [masks[source] | (attachment << 27) for source, attachment in columns]
    witnesses = saved['scan']['additional_binary_exclusion_witnesses']
    assert not saved['scan']['single_exclusion_witnesses'] and len(witnesses) == expected_cuts
    pairs = []
    for witness in witnesses:
        a, b = witness['columns']
        assert 0 <= a < b < len(columns) and columns[a][0] != columns[b][0]
        common = [i for i in range(35) if (full_masks[a]&full_masks[b]) >> i & 1]
        assert len(common) <= 2 and all(gram[i][j] != 1 for i, j in combinations(common, 2))
        vector = witness['negative_vector']
        assert len(vector) == 35 and all(type(v) is int for v in vector)
        value = sum(vector[i]*gram[i][j]*vector[j] for i in range(35) for j in range(35))
        for column in (a, b):
            dot = sum(vector[i] for i in range(35) if full_masks[column] >> i & 1)
            value -= dot*dot
        assert value == witness['negative_quadratic_value'] and value < 0
        pairs.append([a, b])
    assert len({tuple(pair) for pair in pairs}) == expected_cuts
    expected_fragment = (f'p cnf {len(columns)} {expected_cuts}\n'+
                         ''.join(f'{-a-1} {-b-1} 0\n' for a, b in pairs)).encode()
    assert fragment.read_bytes() == expected_fragment
    old_path, new_path = Path(original['cnf']), Path(model['cnf'])
    assert digest(old_path) == original['cnf_sha256'] == model['base_cnf_sha256']
    assert digest(new_path) == model['cnf_sha256']
    variables, count = original['formula']['variables'], original['formula']['clauses']
    assert model['formula'] == {'primary_columns': len(columns), 'variables': variables,
                                'original_clauses': count, 'additional_binary_clauses': expected_cuts,
                                'clauses': count+expected_cuts}
    with old_path.open('rb') as old, new_path.open('rb') as new:
        assert old.readline() == f'p cnf {variables} {count}\n'.encode()
        assert new.readline() == f'p cnf {variables} {count+expected_cuts}\n'.encode()
        for _ in range(count):
            line = old.readline()
            assert line and new.readline() == line
        assert not old.read() and new.read() == expected_fragment.split(b'\n', 1)[1]
    return {'status': 'PASS: complete attachment domain, all direct negative vectors and exact unchanged-body overlay',
            'audit_source_sha256': digest(Path(__file__)), 'case_index': case_index,
            'model_sha256': digest(model_path), 'subject_source_hashes': model['source_hashes'],
            'base_cnf_sha256': digest(old_path), 'overlay_cnf_sha256': digest(new_path),
            'certificate_sha256': digest(cert_path), 'fragment_sha256': digest(fragment),
            'raw_attachment_columns': raw_count, 'complete_admitted_columns': len(columns),
            'full35_Gram_entries_reconstructed': 1225,
            'direct_integer_negative_vectors_checked': expected_cuts,
            'unchanged_original_clause_lines': count, 'appended_binary_clause_lines': expected_cuts,
            'new_variables': 0, 'quotient_inverse_or_Schur_formula_used': False,
            'complete_column_pair_census_recomputed': False, 'CNF_rebuilt': False, 'solver_called': False,
            'scope': 'one indexed35-core; no case exclusion is asserted by this audit',
            'non_author_source_review_is_a_separate_gate': True}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', type=int, choices=sorted(BINDINGS), required=True)
    parser.add_argument('--model', type=Path, required=True)
    parser.add_argument('--model-sha256', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    started = time.monotonic()
    result = audit(args.case, args.model.resolve(), args.model_sha256)
    result['elapsed_seconds'] = time.monotonic()-started
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2), flush=True)
