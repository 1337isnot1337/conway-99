"""Unfixed39-core incidence specification and exact CNF size preparation.

This prepares supports and sizes only. It does not assemble the full CNF
or invoke a solver. Binary x_ab select all compatible complete columns;
derived component selectors compress local Gram and motif constraints.
"""

import argparse
from collections import Counter, defaultdict
from functools import lru_cache
import gzip
import hashlib
from itertools import combinations
import json
from pathlib import Path
import struct
import time

import root_prism_free_f0_pair_gram as gram_screen
import root_prism_free_f0_components as components
import root_prism_free_f0_pair_clauses as motifs


ROOT, LOGS = gram_screen.ROOT, gram_screen.LOGS
GRAM_CERT = LOGS/'f0-pair-gram-certificate.json.gz'
GRAM_SHA = 'edb85ff422222961e6bc9b36322b74bcfce455bca262d6e189d7768f9ac91c98'
PAIR_CERT = LOGS/'f0-pair-clauses.json.gz'
PAIR_SHA = '47e9d8f518fab10aee604f33df1f22c97b0d201a1af4180e4307553e4857672f'
digest, canonical = gram_screen.digest, components.canonical


def atmost_size(n, k):
    """PySAT's seqcounter variable and clause counts, including shortcuts."""
    assert 0 <= k <= n
    if k == n:
        return 0, 0
    if k == 0:
        return 0, n
    if k == n-1:
        return 0, 1
    return k*(n-k), 2*k*(n-k)+n-2*k


def equality_size(n, k):
    a, b = atmost_size(n, k), atmost_size(n, n-k)
    return a[0]+b[0], a[1]+b[1]


@lru_cache(None)
def encoding_size(kind, n, quota):
    """Only a single distinct-size counter is built, never the full formula."""
    from pysat.card import CardEnc, EncType
    assert n >= 0 and 0 <= quota <= n
    if not n:
        return {'variables': 0, 'clauses': 0, 'literal_occurrences': 0,
                'clause_length_histogram': []}
    method = CardEnc.equals if kind == 'equals' else CardEnc.atmost
    assert kind in ('equals', 'atmost')
    encoded = method(list(range(1, n+1)), quota, top_id=n, encoding=EncType.seqcounter)
    expected = equality_size(n, quota) if kind == 'equals' else atmost_size(n, quota)
    variables = max(0, encoded.nv-n)
    assert (variables, len(encoded.clauses)) == expected
    return {'variables': variables, 'clauses': len(encoded.clauses),
            'literal_occurrences': sum(map(len, encoded.clauses)),
            'clause_length_histogram': [[k, v] for k, v in sorted(Counter(map(len, encoded.clauses)).items())]}


def controls():
    counters = 0
    for n in range(17):
        for k in range(n+1):
            for kind in ('equals', 'atmost'):
                encoding_size(kind, n, k)
                counters += 1
    links = 0
    for n in range(8):
        for mask in range(1 << n):
            for u in (0, 1):
                assert (mask.bit_count()+(1-u) == 1) == (mask.bit_count() == u)
                links += 1
    # All overlap>=3 pair conflicts are exactly covered by shared triples.
    masks = list(combinations(range(7), 4))
    packing = 0
    for a, b in combinations(masks, 2):
        a, b = set(a), set(b)
        assert (len(a&b) >= 3) == bool(set(combinations(sorted(a), 3)) & set(combinations(sorted(b), 3)))
        packing += 1
    return {'counter_size_controls': counters, 'exact_link_boolean_controls': links,
            'triple_family_packing_controls': packing, 'solver_called': False,
            'full_CNF_assembled': False}


def load():
    assert digest(GRAM_CERT) == GRAM_SHA
    certificate = json.loads(gzip.decompress(GRAM_CERT.read_bytes()))
    assert certificate['source_sha256'] == digest(Path(gram_screen.__file__))
    description, domain, rows, gram, pairs, columns = gram_screen.load_core()
    assert certificate['component_description'] == description
    assert certificate['component_triples'] == domain['signature_domain']
    assert certificate['Gram'] == gram
    assert certificate['paired_column_order_sha256'] == components.sha(canonical(pairs))
    assert certificate['full_column_order_sha256'] == components.sha(canonical(columns))
    assert digest(PAIR_CERT) == PAIR_SHA
    pair_certificate = json.loads(gzip.decompress(PAIR_CERT.read_bytes()))
    assert pair_certificate['source_sha256'] == digest(Path(motifs.__file__))
    conflicts = motifs.clauses_for(domain)
    assert {'representative':0, **conflicts} == pair_certificate['representatives'][0]
    return domain, rows, gram, pairs, columns, conflicts, certificate


def supports(domain, gram, pairs, columns, conflicts):
    n = len(pairs)
    triples = domain['signature_domain']
    # Independent selectors x:1..39168; derived u/v:39169..40128.
    component_ids = [[n+1+480*side+i for i in range(480)] for side in range(2)]
    row_members = [[[] for _ in range(480)] for _ in range(2)]
    cross_members = [[[] for _ in range(18)] for _ in range(18)]
    triple_members = defaultdict(list)
    for index, ((a,b), h) in enumerate(zip(pairs, columns), 1):
        row_members[0][a].append(index)
        row_members[1][b].append(index)
        for i in triples[a]:
            for j in triples[b]:
                cross_members[i][j].append(index)
        for sites in combinations(h, 3):
            triple_members[sites].append(index)
    specs = []
    def add(kind, label, encoding, literals, quota):
        assert literals and len(literals) == len(set(literals))
        assert len({abs(x) for x in literals}) == len(literals)
        assert quota <= len(literals)
        specs.append({'kind':kind, 'label':label, 'encoding':encoding,
                      'literals':literals, 'quota':quota})
    for side in range(2):
        for triple in range(480):
            add('component link', [side,triple], 'equals',
                row_members[side][triple]+[-component_ids[side][triple]], 1)
    local_coverage = []
    for side in range(2):
        seen = {}
        for i in range(18):
            for j in range(i, 18):
                members = [component_ids[side][s] for s,h in enumerate(triples) if i in h and j in h]
                quota = domain['Gram'][i][j]
                key = tuple(members), quota
                if key not in seen:
                    seen[key] = None
                    if members:
                        seen[key] = len(specs)
                        add('component Gram', [side,i,j], 'equals', members, quota)
                    else:
                        assert quota == 0
                local_coverage.append([side,i,j,quota,len(members),seen[key]])
    for i in range(18):
        for j in range(18):
            add('cross Gram', [i,j], 'equals', cross_members[i][j], gram[3+i][21+j])
    motif_pairs = sorted({tuple(item['columns']) for name in ('F_conflicts','prism_conflicts')
                          for item in conflicts[name]})
    direct = []
    for side in range(2):
        direct.extend([-component_ids[side][a],-component_ids[side][b]] for a,b in motif_pairs)
    # Complete triple packing: local triples are covered by exact component
    # links. A quota-one Gram pair covers any containing triple. Only the
    # remaining mixed triples need new at-most-one rows.
    packing_coverage, new_families = [], []
    for sites in combinations(range(3,39), 3):
        members = triple_members.get(sites, [])
        if len(members) <= 1:
            reason = 'at most one candidate'
        elif sites[-1] < 21 or sites[0] >= 21:
            local = [v-(3 if sites[-1] < 21 else 21) for v in sites]
            index = triples.index(local)
            side = int(sites[0] >= 21)
            assert members == row_members[side][index]
            reason = 'component link at most one'
        elif any(gram[i][j] == 1 for i,j in combinations(sites, 2)):
            reason = 'quota-one Gram pair'
        else:
            assert all(gram[i][j] == 2 for i,j in combinations(sites, 2))
            assert sorted((v-3 if v<21 else v-21)//6 for v in sites) == [0,1,2]
            reason = 'explicit mixed triple capacity'
            new_families.append(list(sites))
            add('mixed triple packing', list(sites), 'atmost', members, 1)
        packing_coverage.append([list(sites),len(members),reason])
    assert len(packing_coverage) == 7140
    assert len(local_coverage) == 342
    assert sum(len(row) for table in cross_members for row in table) == 9*n
    assert sum(len(row) for side in row_members for row in side) == 2*n
    return specs, direct, {'component_Gram_positions':local_coverage,
                          'all_shell_core_triple_positions':packing_coverage,
                          'new_mixed_triple_positions':new_families,
                          'empty_central_Gram_positions':114,
                          'component_selector_ids':component_ids,
                          'component_motif_pair_count':len(motif_pairs)}


def formula_counts(specs, direct, independent_variables, component_variables):
    by_kind = defaultdict(lambda:Counter())
    by_size = Counter()
    summaries = []
    total_vars = independent_variables+component_variables
    total_clauses, literals = len(direct), sum(map(len,direct))
    for item in specs:
        n, quota = len(item['literals']), item['quota']
        statistics = encoding_size(item['encoding'], n, quota)
        count = by_kind[item['kind']]
        count['rows'] += 1
        count['support_occurrences'] += n
        for key in ('variables','clauses','literal_occurrences'):
            count[key] += statistics[key]
        total_vars += statistics['variables']
        total_clauses += statistics['clauses']
        literals += statistics['literal_occurrences']
        by_size[item['kind'],item['encoding'],n,quota] += 1
        summaries.append({k:v for k,v in item.items() if k != 'literals'} |
                         {'support_size':n,'literal_order_sha256':components.sha(canonical(item['literals']))})
    digit_bound = len(str(total_vars))
    dimacs_upper = literals*(digit_bound+2)+2*total_clauses+100
    optional_population = encoding_size('equals', 480, 60)
    return {'independent_column_variables':independent_variables,
            'derived_component_selection_variables':component_variables,
            'projected_total_variables':total_vars,'projected_total_clauses':total_clauses,
            'projected_literal_occurrences':literals,
            'safe_DIMACS_byte_upper_bound':dimacs_upper,
            'direct_component_motif_clauses':len(direct),
            'by_kind':{k:dict(v) for k,v in sorted(by_kind.items())},
            'support_size_histograms':[[*key,count] for key,count in sorted(by_size.items())],
            'constraint_support_summaries':summaries,
            'direct_clause_order_sha256':components.sha(canonical(direct)),
            'full_specification_sha256':components.sha(canonical([specs,direct])),
            'optional_two_population_rows_extra_variables':2*optional_population['variables'],
            'optional_two_population_rows_extra_clauses':2*optional_population['clauses'],
            'population_rows_in_specification':False,
            'population_60_follows_from_component_Gram_diagonal_sum':True,
            'encoding':'PySAT seqcounter with disjoint auxiliaries for every counter',
            'full_CNF_assembled':False,'solver_called':False}


def table_preparation(domain, conflicts, certificate):
    triples = domain['signature_domain']
    inv = certificate['bilinear_reduction']['component_inverse_numerator']
    denominator = certificate['bilinear_reduction']['component_inverse_denominator']
    qx = [[sum(row[v] for v in h) for row in inv] for h in triples]
    table = [[sum(qx[a][v] for v in h) for h in triples] for a in range(480)]
    assert table == [list(row) for row in zip(*table)]
    assert [table[i][i] for i in range(480)] == certificate['bilinear_reduction']['component_column_leverage_numerators']
    smallest = min(x for row in table for x in row)
    largest = max(x for row in table for x in row)
    assert -(2**31) <= smallest <= largest < 2**31
    packed = b''.join(struct.pack('<480i',*row) for row in table)
    motif_set = {tuple(item['columns']) for name in ('F_conflicts','prism_conflicts') for item in conflicts[name]}
    types = Counter()
    for a,h in enumerate(triples):
        p = gram_screen.profile(h)
        for c,k in enumerate(triples):
            q = gram_screen.profile(k)
            overlap = sorted(set(h)&set(k))
            overlap_profile = tuple(sum(v//6 == f for v in overlap) for f in range(3))
            quota_one = any(domain['Gram'][i][j] == 1 for i,j in combinations(overlap,2))
            motif = tuple(sorted((a,c))) in motif_set
            key = (p,q,table[a][a],table[c][c],table[a][c],overlap_profile,int(quota_one),int(motif))
            types[key] += 1
    profile_types = Counter()
    profile_pairs = Counter()
    for key,multiplicity in types.items():
        profile_types[key[0],key[1]] += 1
        profile_pairs[key[0],key[1]] += multiplicity
    complement = lambda p:tuple(2-x for x in p)
    type_products = sum(count*profile_types[complement(p),complement(q)]
                        for (p,q),count in profile_types.items())
    raw_products = sum(count*profile_pairs[complement(p),complement(q)]
                       for (p,q),count in profile_pairs.items())
    assert raw_products == 39168**2
    return {'component_table_size':[480,480], 'integer_denominator':denominator,
            'integer_range':[smallest,largest], 'little_endian_int32_sha256':components.sha(packed),
            'little_endian_int32_bytes':len(packed),
            'component_pair_types':len(types),
            'type_definition':['first_profile','second_profile','first_diagonal','second_diagonal',
                               'bilinear_value','intersection_profile','shared_quota_one_pair','component_motif_conflict'],
            'type_histogram':[[list(key[0]),list(key[1]),key[2],key[3],key[4],
                               list(key[5]),key[6],key[7],count]
                              for key,count in sorted(types.items())],
            'compatible_ordered_type_products':type_products,
            'represented_ordered_full_column_pairs_including_self':raw_products,
            'full_pair_classification_performed':False,
            'full_pair_conflicts_exported':False,
            'compression_is_arithmetic_classification_not_graph_symmetry':True}


def calculate():
    started = time.monotonic()
    domain, rows, gram, pairs, columns, conflicts, certificate = load()
    specs, direct, coverage = supports(domain, gram, pairs, columns, conflicts)
    result = {'status':'complete unfixed incidence supports and exact encoding-size preparation; no full CNF or solver',
              'source_sha256':digest(Path(__file__)), 'Gram_source_sha256':digest(Path(gram_screen.__file__)),
              'Gram_certificate_sha256':GRAM_SHA,'component_motif_certificate_sha256':PAIR_SHA,
              'scope':'component0 paired with component0, identity fiber alignment, full domains',
              'fixed_component_incidence_designs':False,'additional_graph_symmetry':False,
              'exterior_adjacency_variables':0,
              'column_order_sha256':certificate['full_column_order_sha256'],
              'component_profile_counts':[[list(p),c] for p,c in sorted(Counter(map(gram_screen.profile,domain['signature_domain'])).items())],
              'coverage':coverage,
              'formula':formula_counts(specs,direct,len(pairs),960),
              'bilinear_table_preparation':table_preparation(domain,conflicts,certificate),
              'controls':controls(),
              'elapsed_seconds_for_information_only':time.monotonic()-started}
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--certificate',type=Path,required=True)
    parser.add_argument('--replay',action='store_true')
    args = parser.parse_args()
    actual = calculate()
    if args.replay:
        saved = json.loads(gzip.decompress(args.certificate.read_bytes()))
        actual['elapsed_seconds_for_information_only'] = saved['elapsed_seconds_for_information_only']
        assert actual == saved
    else:
        assert not args.certificate.exists()
        args.certificate.write_bytes(gzip.compress(canonical(actual)+b'\n',mtime=0))
    formula,table = actual['formula'],actual['bilinear_table_preparation']
    print(json.dumps({'status':actual['status'],'mode':'replay' if args.replay else 'generation',
                      'projected_variables':formula['projected_total_variables'],
                      'projected_clauses':formula['projected_total_clauses'],
                      'safe_DIMACS_byte_upper_bound':formula['safe_DIMACS_byte_upper_bound'],
                      'by_kind':formula['by_kind'],
                      'mixed_triple_capacity_rows':len(actual['coverage']['new_mixed_triple_positions']),
                      'component_pair_types':table['component_pair_types'],
                      'compatible_ordered_type_products':table['compatible_ordered_type_products'],
                      'elapsed_seconds':actual['elapsed_seconds_for_information_only']},indent=2),flush=True)
