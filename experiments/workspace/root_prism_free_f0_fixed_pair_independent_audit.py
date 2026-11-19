"""Independent domain and constraint-support audit of the fixed pair.

No subject builder, counter encoder, or solver is imported. Reconstruct
the joined core from the earlier component certificate, then check every
assignment variable, quota support, and necessary packing pair.
"""

from collections import Counter
import gzip
import hashlib
from itertools import combinations
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LOGS = ROOT/'experiments/logs/root-prism-free'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode()


def audit():
    model_path = LOGS/'f0-fixed-pair-model.json'
    domain_path = LOGS/'f0-components-certificate.json.gz'
    incidence_path = LOGS/'f0-incidence-case00-run01/result.json'
    assert digest(model_path) == 'db1765af0096c13a050c2817c0a367153a3fdec9ab4ae319cede8e8b6be234d3'
    assert digest(domain_path) == 'dc8aad926550cef6a8ee39aa8f4efbd056773950183b9e0ac86b195e8057c3fd'
    assert digest(incidence_path) == '64d5411e04764b0d7e7157c47b67d759e536a401fee8fe36e274943f2fda4abf'
    model = json.loads(model_path.read_text())
    for name, expected in model['source_hashes'].items():
        assert digest(Path(__file__).with_name(name)) == expected
    coupling_path = ROOT/model['coupling_certificate']
    assert digest(coupling_path) == model['coupling_certificate_sha256']
    saved = json.loads(gzip.decompress(coupling_path.read_bytes()))
    domain = json.loads(gzip.decompress(domain_path.read_bytes()))['representatives'][0]['domain']
    incidence = json.loads(incidence_path.read_text())
    selected = incidence['incidence_witness']['selected_columns']
    design = [domain['signature_domain'][i] for i in selected]
    assert len(design) == len({tuple(h) for h in design}) == 60
    assert design == saved['fixed_design']
    assert all(sum(i in h and j in h for h in design) == domain['Gram'][i][j]
               for i in range(18) for j in range(18))
    core = [0]*39
    for offset in (3, 21):
        image = list(range(3))+list(range(offset, offset+18))
        for i in range(21):
            for j in range(i):
                if domain['core_rows'][i] >> j & 1:
                    core[image[i]] |= 1 << image[j]
                    core[image[j]] |= 1 << image[i]
    assert core == list(map(int, saved['joined39_core_rows']))
    gram = [[12*int(i == j)+2-(core[i] & core[j]).bit_count()-int(core[i] >> j & 1)
             for j in range(39)] for i in range(39)]
    assert gram == saved['joined39_Gram']
    assert [row.bit_count() for row in core] == [14]*3+[4]*36
    assert all(value == 0 for row in gram[:3] for value in row)
    assert all(gram[3+i][3+j] == domain['Gram'][i][j]
               and gram[21+i][21+j] == domain['Gram'][i][j]
               and gram[3+i][21+j] == 2-int(i//6 == j//6)
               for i in range(18) for j in range(18))
    profiles = [tuple(sum(i//6 == f for i in h) for f in range(3)) for h in design]
    profile_counts = Counter(profiles)
    assert profile_counts[(1, 1, 1)] == 24
    assert sorted(profile_counts.values()) == [6]*6+[24]
    pairs = [(a, b) for a in range(60) for b in range(60)
             if all(profiles[a][f]+profiles[b][f] == 2 for f in range(3))]
    assert len(pairs) == 792 and [list(pair) for pair in pairs] == saved['fixed_both_pairs']
    assert hashlib.sha256(canonical(pairs)).hexdigest() == model['paired_domain_sha256']
    columns = [set(3+i for i in design[a]) | set(21+j for j in design[b]) for a, b in pairs]
    masks = [sum(1 << i for i in column) for column in columns]
    assert all(len(column) == 6 for column in columns)
    assert all(((core[i] | (1 << i)) & mask).bit_count() <= 2 for mask in masks for i in range(39))
    coverage = []
    for a in range(60):
        coverage.append({'kind': 'first row', 'indices': [a], 'quota': 1,
                         'support': sum(x == a for x, _ in pairs)})
    for b in range(60):
        coverage.append({'kind': 'second column', 'indices': [b], 'quota': 1,
                         'support': sum(y == b for _, y in pairs)})
    for i in range(18):
        for j in range(18):
            coverage.append({'kind': 'cross Gram', 'indices': [i, j],
                             'quota': gram[3+i][21+j],
                             'support': sum(3+i in h and 21+j in h for h in columns)})
    assert coverage == model['formula']['constraint_coverage'] and len(coverage) == 444
    packing = [[a, b] for a, b in combinations(range(792), 2)
               if pairs[a][0] != pairs[b][0] and pairs[a][1] != pairs[b][1]
               and (masks[a] & masks[b]).bit_count() > 2]
    assert len(packing) == model['formula']['packing_pair_clauses'] == 8180
    assert hashlib.sha256(canonical(packing)).hexdigest() == model['formula']['packing_pairs_sha256']
    cnf_path = Path(model['cnf'])
    assert digest(cnf_path) == model['cnf_sha256']
    clauses = [list(map(int, line.split()))[:-1] for line in cnf_path.read_text().splitlines()
               if line and line[0] not in 'cp']
    assert len(clauses) == model['formula']['clauses'] == 56096
    assert clauses[-8180:] == [[-a-1, -b-1] for a, b in packing]
    report = {'status': 'independent fixed-pair domain and constraint-support audit PASS',
              'source_sha256': digest(Path(__file__)), 'model_sha256': digest(model_path),
              'subject_source_hashes': model['source_hashes'], 'cnf_sha256': digest(cnf_path),
              'independently_reconstructed_core_vertices': 39, 'Gram_entries': 1521,
              'fixed_triples_per_side': 60, 'paired_columns': 792,
              'row_quotas': 60, 'column_quotas': 60, 'cross_Gram_quotas': 324,
              'explicit_necessary_packing_clauses': 8180,
              'subject_builder_imported': False, 'solver_called': False,
              'full_cardinality_encoding_rebuilt': False,
              'read_only_source_review_completed': True,
              'scope': 'one fixed pair of designs and identity fiber alignment; no whole-component conclusion'}
    path = LOGS/'f0-fixed-pair-independent-audit.json'
    assert not path.exists()
    path.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2), flush=True)


if __name__ == '__main__':
    audit()
