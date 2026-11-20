"""Independent read-only audit of the first split18-component model.

Reconstruct the21-core, all admissible triples, Gram row coverage, and
every saved two-column forbidden motif. No subject builder is imported;
no CNF is rebuilt and no solver is called.
"""

from collections import Counter
import gzip
import hashlib
from itertools import combinations, permutations
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LOGS = ROOT/'experiments/logs/root-prism-free'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canon(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode()


def all_matchings(sites):
    if not sites:
        yield []
        return
    first = sites[0]
    for second in sites[1:]:
        rest = [x for x in sites if x not in (first, second)]
        for tail in all_matchings(rest):
            yield [(first, second)]+tail


def add(rows, a, b):
    rows[a] |= 1 << b
    rows[b] |= 1 << a


def cap_failures(rows):
    return [(a, b, (rows[a] & rows[b]).bit_count(), (rows[a] >> b) & 1)
            for a, b in combinations(range(len(rows)), 2)
            if (rows[a] & rows[b]).bit_count()+((rows[a] >> b) & 1) > 2]


def connected(rows, vertices):
    seen, todo = {min(vertices)}, [min(vertices)]
    while todo:
        a = todo.pop()
        for b in vertices-seen:
            if rows[a] >> b & 1:
                seen.add(b)
                todo.append(b)
    return seen == vertices


def run():
    model_path = LOGS/'f0-incidence-case00-model.json'
    model = json.loads(model_path.read_text())
    assert model['case'] == 0 and model['complete_component_cover_size'] == 66
    for name, expected in model['source_hashes'].items():
        assert digest(Path(__file__).with_name(name)) == expected
    domain_path, pair_path = ROOT/model['domain_certificate'], ROOT/model['pair_certificate']
    assert digest(domain_path) == model['domain_certificate_sha256']
    assert digest(pair_path) == model['pair_certificate_sha256']
    catalogue = json.loads(gzip.decompress(domain_path.read_bytes()))
    pair_certificate = json.loads(gzip.decompress(pair_path.read_bytes()))
    representative = catalogue['representatives'][0]
    saved = representative['domain']

    first = [i ^ 1 for i in range(6)]
    alternatives = []
    for pairs in all_matchings(list(range(6))):
        partner = [None]*6
        for a, b in pairs:
            partner[a], partner[b] = b, a
        if all(partner[i] != first[i] for i in range(6)):
            alternatives.append(partner)
    alternatives.sort()
    assert len(alternatives) == 8
    derangements = [q for q in permutations(range(6)) if all(q[i] != i for i in range(6))]
    assert len(derangements) == 265
    p_index, r_index, q_index = representative['description']
    second, third, q = alternatives[p_index], alternatives[r_index], derangements[q_index]
    core = [0]*21
    for a, b in combinations(range(3), 2):
        add(core, a, b)
    for fiber, matching in enumerate((first, second, third)):
        for a in range(6):
            add(core, fiber, 3+6*fiber+a)
            add(core, 3+6*fiber+a, 3+6*fiber+matching[a])
    for a in range(6):
        add(core, 3+a, 9+a)
        add(core, 3+a, 15+a)
        add(core, 9+a, 15+q[a])
    assert core == saved['core_rows'] and not cap_failures(core)
    shell = [row >> 3 for row in core[3:]]
    assert shell == saved['shell_rows']
    gram = [[12*int(i == j)+2-(core[3+i] & core[3+j]).bit_count()-int(core[3+i] >> (3+j) & 1)
             for j in range(18)] for i in range(18)]
    assert gram == saved['Gram']
    assert sum(gram[i][i] for i in range(18)) == 180
    assert all(sum(gram[i][i] for i in range(6*f, 6*f+6)) == 60 for f in range(3))
    assert all(sum(gram[i][j] for i in range(6*f, 6*f+6) for j in range(6*f, 6*f+6)) == 84
               for f in range(3))

    columns = []
    for triple in combinations(range(18), 3):
        if max(Counter(i//6 for i in triple).values()) > 2:
            continue
        if any(gram[i][j] <= 0 for i, j in combinations(triple, 2)):
            continue
        if any(sum((shell[i] >> j & 1)+int(i == j) for j in triple) > 2 for i in range(18)):
            continue
        columns.append(list(triple))
    assert columns == saved['signature_domain'] and len(columns) == 480
    assert hashlib.sha256(canon(columns)).hexdigest() == saved['signature_domain_sha256']
    assert all(sorted(Counter(i//6 for i in h).values()) in ([1,1,1], [1,2]) for h in columns)

    coverage, identities = [], {}
    for i in range(18):
        for j in range(i, 18):
            members = [s+1 for s, h in enumerate(columns) if i in h and j in h]
            key = tuple(members), gram[i][j]
            identities.setdefault(key, len(identities))
            coverage.append([i, j, gram[i][j], len(members), identities[key]])
    assert coverage == model['formula']['Gram_position_coverage']
    assert len(coverage) == 171 and len(identities) == 151

    record = pair_certificate['representatives'][0]
    evidence, conflicts = [], set()
    for family, expected in (('F_conflicts', 78), ('prism_conflicts', 12)):
        assert len(record[family]) == expected
        for witness in record[family]:
            a, b = witness['ordered_columns']
            assert sorted((a, b)) == witness['columns'] and a != b
            partial = core[:]+[0, 0]
            for source, selector in ((21, a), (22, b)):
                for site in columns[selector]:
                    add(partial, source, 3+site)
            assert not cap_failures(partial)
            sites = witness['motif_sites']
            assert len(sites) == len(set(sites)) and {21,22} <= set(sites)
            motif = [sum(int(partial[v] >> w & 1) << j for j, w in enumerate(sites)) for v in sites]
            assert motif == witness['induced_motif_rows']
            if family == 'F_conflicts':
                assert len(motif) == 10 and [row.bit_count() for row in motif] == [5,5]+[3]*8
                assert motif[0] >> 1 & 1
                sides = [{i for i in range(2,10) if motif[center] >> i & 1} for center in (0,1)]
                assert list(map(len, sides)) == [4,4] and not sides[0] & sides[1]
                for side in sides:
                    assert all(sum(motif[i] >> j & 1 for j in side) == 1 for i in side)
                assert all(sum(motif[i] >> j & 1 for j in sides[1]) == 1 for i in sides[0])
                assert connected(motif, set(range(2,10)))
                assert sum(row.bit_count() for row in motif) == 34
            else:
                assert len(motif) == 6 and all(row.bit_count() == 3 for row in motif)
                assert all(motif[i] >> j & 1 for triangle in ((0,1,2),(3,4,5)) for i,j in combinations(triangle,2))
                assert all(sum(motif[i] >> j & 1 for j in (3,4,5)) == 1 for i in (0,1,2))
            joined = partial[:]
            add(joined, 21, 22)
            failures = cap_failures(joined)
            assert failures
            conflicts.add(tuple(sorted((a,b))))
            evidence.append({'family': family, 'columns': sorted((a,b)),
                             'unknown_edge_forbidden_by_cap_witness': list(failures[0])})
    assert len(conflicts) == 90 == model['formula']['motif_conflict_clauses']
    assert digest(Path(model['cnf'])) == model['cnf_sha256']
    with Path(model['cnf']).open() as stream:
        header = stream.readline().split()
    assert header == ['p','cnf','28308','56550']
    result = {'status': 'PASS: independent component, full triple domain, Gram rows, and all90 motif clauses',
              'audit_source_sha256': digest(Path(__file__)), 'model_sha256': digest(model_path),
              'subject_source_hashes': model['source_hashes'],
              'domain_certificate_sha256': digest(domain_path), 'pair_certificate_sha256': digest(pair_path),
              'case': 0, 'columns': 480, 'Gram_positions': 171, 'distinct_Gram_equations': 151,
              'F_conflicts': 78, 'prism_conflicts': 12, 'explicit_forced_nonedge_witnesses': evidence,
              'population_from_diagonal_sum': 60, 'per_fiber_occupancies_0_1_2': [12,36,12],
              'profile111': 24, 'profile210_total': 36,
              'CNF_hash_checked': model['cnf_sha256'], 'CNF_rebuilt': False, 'solver_called': False,
              'all66_census_reexecuted': False,
              'scope': 'necessary one-component model under global prism-free, F-free, split18+18 assumptions'}
    output = LOGS/'f0-incidence-independent-audit.json'
    assert not output.exists()
    output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({key:value for key,value in result.items() if key != 'explicit_forced_nonedge_witnesses'}, indent=2))


if __name__ == '__main__':
    run()
