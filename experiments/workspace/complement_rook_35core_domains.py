"""Bounded exact attachment-domain census for the2,521 labelled35-cores.

Every remaining vertex has one old R/S/T signature and0,1,or2 neighbors
in the local eight. Complete domains are filtered only by necessary
Gram support and nonnegative mixed demands. No optimizer is called.
"""

import argparse
from collections import Counter, defaultdict
import gzip
import hashlib
from itertools import combinations
import json
from pathlib import Path
import time

import complement_rook_projector_schur as base_helper


ROOT = Path(__file__).resolve().parents[2]
LOGS = ROOT/'experiments/logs/grids-and-triangles'
CENSUS = LOGS/'complement-rook-local-star-census.json'
CENSUS_SHA = '832440adb66015b27d1d58dbd0cee5079f735f07553b24a789aeacbf994fe394'
PAIRS = [(i, j) for i in range(35) for j in range(i, 35)]
PAIR_INDEX = {pair: i for i, pair in enumerate(PAIRS)}
ATTACHMENTS = {d: [sum(1 << i for i in choice) for choice in combinations(range(8), d)] for d in range(3)}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode()


def sha(value):
    return hashlib.sha256(value).hexdigest()


def digest(path):
    return sha(path.read_bytes())


def matchings(remaining=tuple(range(8))):
    if not remaining:
        yield ()
        return
    a = remaining[0]
    for b in remaining[1:]:
        rest = tuple(i for i in remaining if i not in (a, b))
        for tail in matchings(rest):
            yield ((a, b),)+tail


def load_domain():
    assert digest(CENSUS) == CENSUS_SHA
    census = json.loads(CENSUS.read_text())
    assert census['source_sha256'] == digest(Path(__file__).with_name('complement_rook_local_star_census.py'))
    assert census['projector_source_sha256'] == digest(Path(base_helper.__file__))
    assert census['local_signature_sets'] == 864 and census['local_set_orbits'] == 118
    assert census['matching_choices_on_representatives'] == 2521
    rows, gram, triples, signatures, masks, edges, domain_hash = base_helper.domain()
    assert domain_hash == census['base_domain_sha256']
    group = base_helper.actions(rows, triples)
    family = {s for s, sites in enumerate(signatures) if 0 in sites}
    stabilizer = [(i, action) for i, action in enumerate(group) if {action[s] for s in family} == family]
    assert len(stabilizer) == 8
    pool = list(matchings())
    assert len(pool) == len(set(pool)) == 105
    edges = set(edges)
    cases, matching_orbits = [], []
    for orbit_index, orbit in enumerate(census['orbit_records']):
        selected = tuple(orbit['selected_signatures'])
        assert len(selected) == len(set(selected)) == 8 and set(selected) <= family
        assert Counter(triples[s][1] for s in selected) == Counter({4: 2, 5: 2, 7: 2, 8: 2})
        assert sorted(triples[s][2] for s in selected) == list(range(1, 9))
        permitted = [matching for matching in pool if all(tuple(sorted((selected[a], selected[b]))) in edges for a, b in matching)]
        assert len(permitted) == orbit['eligible_perfect_matchings']
        first = len(cases)
        lookup = {matching: first+i for i, matching in enumerate(permitted)}
        position = {s: i for i, s in enumerate(selected)}
        local_actions = []
        for action_index, action in stabilizer:
            if {action[s] for s in selected} == set(selected):
                permutation = [position[action[s]] for s in selected]
                local_actions.append((action_index, permutation))
        assert len(local_actions)*orbit['orbit_size'] == 8
        for matching_index, matching in enumerate(permitted):
            cases.append({'index': len(cases), 'local_set_orbit': orbit_index,
                          'matching_index': matching_index, 'selected_signatures': list(selected),
                          'matching': [list(edge) for edge in matching]})
        remaining = set(permitted)
        while remaining:
            representative = min(remaining)
            images = {}
            for action_index, permutation in local_actions:
                image = tuple(sorted(tuple(sorted((permutation[a], permutation[b]))) for a, b in representative))
                assert image in lookup
                images.setdefault(image, action_index)
            assert set(images) <= remaining
            members = sorted(lookup[image] for image in images)
            matching_orbits.append({'representative_case': lookup[representative], 'member_cases': members})
            for image, action_index in images.items():
                cases[lookup[image]].update(matching_orbit_representative=lookup[representative],
                                           matching_orbit_size=len(images),
                                           matching_transport_action_index=action_index)
            remaining -= set(images)
    assert len(cases) == 2521 and len(census['pattern_records']) == 864
    index = {'status': 'complete index of all2,521 matching choices over the118 local-set representatives',
             'census_sha256': CENSUS_SHA, 'base_domain_sha256': domain_hash,
             'case_count': len(cases), 'local_set_orbits': 118, 'labelled_local_sets': 864,
             'matching_orbits_after_local_stabilizers': len(matching_orbits),
             'matching_orbit_size_histogram': dict(sorted(Counter(len(orbit['member_cases']) for orbit in matching_orbits).items())),
             'matching_orbits': matching_orbits, 'cases': cases,
             'graph_automorphism_assumption': False}
    return (rows, gram, triples, signatures, masks, edges, domain_hash), index


def core_matrix(domain, case):
    rows, _, _, signatures, _, _, _ = domain
    selected, matching = case['selected_signatures'], case['matching']
    core = list(rows)+[0]*8
    for local, source in enumerate(selected, 27):
        for point in signatures[source]:
            core[local] |= 1 << point
            core[point] |= 1 << local
    for a, b in matching:
        core[27+a] |= 1 << (27+b)
        core[27+b] |= 1 << (27+a)
    assert core[0].bit_count() == 14
    gram = [[12*int(i == j)+2-(core[i] & core[j]).bit_count()-int(core[i] >> j & 1)
             for j in range(35)] for i in range(35)]
    assert all(value >= 0 for row in gram for value in row)
    assert all(value == 0 for value in gram[0])
    kernels = []
    kernels.append([int(i == 0) for i in range(35)])
    kernels.append([int(i < 9)-int(9 <= i < 18) for i in range(35)])
    kernels.append([int(i < 9)-int(18 <= i < 27) for i in range(35)])
    kernels.append([int(core[0] >> i & 1)-2*int(i < 9) for i in range(35)])
    assert all(sum(gram[i][j]*vector[j] for j in range(35)) == 0
               for vector in kernels for i in range(35))
    # On coordinates0,9,18,27 this4-by4 kernel matrix has determinant1.
    pivots = [[vector[i] for i in (0, 9, 18, 27)] for vector in kernels]
    assert pivots == [[1, 0, 0, 0], [1, -1, 0, 0], [1, 0, -1, 0], [-2, 1, 1, 1]]
    old_diagonal = sum(gram[i][i] for i in range(27))
    new_diagonal = sum(gram[i][i] for i in range(27, 35))
    new_pairs = sum(gram[i][j] for i in range(27, 35) for j in range(i+1, 35))
    assert (old_diagonal, new_diagonal, new_pairs) == (192, 80, 20)
    return core, gram, kernels


def span_basis(vectors):
    basis = {}
    for vector in vectors:
        while vector:
            pivot = vector.bit_length()-1
            if pivot in basis:
                vector ^= basis[pivot]
            else:
                basis[pivot] = vector
                break
    return basis


def binary_obstruction(basis, rhs, columns):
    remaining = rhs
    while remaining:
        pivot = remaining.bit_length()-1
        if pivot not in basis:
            break
        remaining ^= basis[pivot]
    if not remaining:
        return None
    vector = 1 << (remaining.bit_length()-1)
    for pivot in sorted(basis):
        if (basis[pivot] & vector).bit_count() % 2:
            vector |= 1 << pivot
    assert all((column & vector).bit_count() % 2 == 0 for column in columns)
    assert (rhs & vector).bit_count() % 2 == 1
    return {'row_indices': [i for i in range(len(PAIRS)) if vector >> i & 1],
            'column_parities': 'all zero', 'target_parity': 1}


def sparse_rows(domain, core, gram, columns):
    _, _, triples, signatures, masks, _, _ = domain
    row_members = [[] for _ in PAIRS]
    original_groups, triple_members = defaultdict(list), defaultdict(list)
    column_masks, outer_masks = [], []
    for column, (source, attachment) in enumerate(columns):
        mask = masks[source] | (attachment << 27)
        sites = [i for i in range(35) if mask >> i & 1]
        column_masks.append(mask)
        original_groups[source].append(column)
        indices = [PAIR_INDEX[i, j] for position, i in enumerate(sites) for j in sites[position:]]
        outer_masks.append(sum(1 << index for index in indices))
        for index in indices:
            row_members[index].append(column)
        for triple in combinations(sites, 3):
            triple_members[triple].append(column)
        p, q, t = triples[source]
        assert gram[p][18+t] == gram[9+q][18+t] == 1
    assert all(not members for (i, j), members in zip(PAIRS, row_members) if gram[i][j] == 0)
    return row_members, original_groups, triple_members, column_masks, outer_masks


def analyze_core(domain, case):
    rows, _, triples, signatures, masks, _, _ = domain
    core, gram, kernels = core_matrix(domain, case)
    closed = [row | (1 << i) for i, row in enumerate(core)]
    compatible = [sum(1 << j for j in range(35) if gram[i][j] > 0) for i in range(35)]
    all_bits = (1 << 35)-1
    forbidden = [all_bits ^ mask for mask in compatible]
    allowed_two = {attachment for attachment in ATTACHMENTS[2]
                   if all(gram[27+a][27+b] > 0 for a, b in combinations([i for i in range(8) if attachment >> i & 1], 2))}
    assert len(allowed_two) == 20
    raw_sources, raw_count, pair_count = Counter(), 0, 0
    columns = []
    for source, sites in enumerate(signatures):
        if 0 in sites:
            continue
        demand = 2-(rows[0] & masks[source]).bit_count()
        assert demand in (0, 1, 2)
        raw_sources[demand] += 1
        raw_count += len(ATTACHMENTS[demand])
        if any(masks[source] & forbidden[i] for i in sites):
            continue
        available = 255
        for point in sites:
            available &= compatible[point] >> 27
        for attachment in ATTACHMENTS[demand]:
            if attachment & ~available or (demand == 2 and attachment not in allowed_two):
                continue
            pair_count += 1
            mask = masks[source] | (attachment << 27)
            if any((row & mask).bit_count() > 2 for row in closed):
                continue
            assert all(sum(vector[i] for i in range(35) if mask >> i & 1) == 0 for vector in kernels)
            columns.append([source, attachment])
    columns.sort()
    assert raw_sources == Counter({0: 16, 1: 136, 2: 72}) and raw_count == 3120
    row_members, original_groups, triple_members, column_masks, outer_masks = sparse_rows(domain, core, gram, columns)
    coverage = []
    capacities = []
    for index, ((i, j), members) in enumerate(zip(PAIRS, row_members)):
        quota = gram[i][j]
        if quota == 0:
            continue
        groups = {columns[column][0] for column in members}
        rt = sorted({(triples[source][0], triples[source][2]) for source in groups})
        st = sorted({(triples[source][1], triples[source][2]) for source in groups})
        capacity = min(len(rt), len(st))
        coverage.append([index, len(members), len(groups), len(rt), len(st)])
        if capacity < quota:
            partition, cells = ('RT', rt) if len(rt) <= len(st) else ('ST', st)
            capacities.append({'target_Gram_row': [i, j], 'quota': quota,
                               'covering_quota_one_partition': partition, 'covering_cells': cells,
                               'capacity': capacity})
    ordinary_basis = span_basis(column_masks)
    assert len(ordinary_basis) <= 31
    outer_basis = span_basis(outer_masks)
    rhs = sum((gram[i][j] % 2) << k for k, (i, j) in enumerate(PAIRS))
    parity = binary_obstruction(outer_basis, rhs, outer_masks)
    nontrivial_triples = {triple: members for triple, members in triple_members.items() if len(members) > 1}
    nonimplied = {triple: members for triple, members in nontrivial_triples.items()
                 if all(gram[i][j] >= 2 for i, j in combinations(triple, 2))}
    return {'index': case['index'], 'local_set_orbit': case['local_set_orbit'],
            'selected_signatures': case['selected_signatures'], 'matching': case['matching'],
            'core_rows': core, 'Gram_sha256': sha(canonical(gram)),
            'column_domain_sha256': sha(canonical(columns)), 'columns': columns,
            'raw_original_source_counts_by_attachment_size': dict(sorted(raw_sources.items())),
            'raw_attachment_columns': raw_count, 'positive_Gram_support_columns': pair_count,
            'admitted_columns': len(columns), 'admitted_original_signatures': len(original_groups),
            'admitted_columns_by_attachment_size': dict(sorted(Counter(attachment.bit_count() for _, attachment in columns).items())),
            'all_Gram_rows': len(PAIRS), 'positive_Gram_rows': len(coverage),
            'Gram_row_support_counts': coverage, 'capacity_obstructions': capacities,
            'attachment_vector_rank_mod2': len(ordinary_basis),
            'attachment_vector_rank_rational': 31 if len(ordinary_basis) == 31 else None,
            'four_exact_independent_Gram_kernel_vectors': kernels,
            'Gram_outer_product_rank_mod2': len(outer_basis), 'Gram_mod2_obstruction': parity,
            'original_signature_groups_with_multiple_choices': sum(len(members) > 1 for members in original_groups.values()),
            'triple_support': {'supported_triples': len(triple_members),
                'column_triple_incidences': sum(len(members) for members in triple_members.values()),
                'nontrivial_capacity_one_rows': len(nontrivial_triples),
                'distinct_nontrivial_member_sets': len({tuple(members) for members in nontrivial_triples.values()}),
                'rows_not_already_implied_by_a_Gram_quota_one_pair': len(nonimplied),
                'maximum_support': max(map(len, triple_members.values()), default=0),
                'support_size_histogram': dict(sorted(Counter(map(len, triple_members.values())).items()))},
            'selected_vertex_count_from_old_diagonals': 64,
            'selected_attachment_counts_from_Gram': [4, 40, 20],
            'excluded_by_current_exact_checks': bool(capacities or parity),
            'binary_incidence_feasibility_claimed': False, 'full_graph_completion_claimed': False}


def generate(directory, seconds, maximum, start):
    assert not directory.exists() and 0 < seconds <= 180 and maximum > 0
    directory.mkdir(parents=True)
    started = time.monotonic()
    domain, index = load_domain()
    assert 0 <= start < len(index['cases'])
    index_path = directory/'all-core-index.json'
    index_path.write_bytes(canonical(index)+b'\n')
    archive = directory/'attachment-domains.jsonl.gz'
    raw_hash = hashlib.sha256()
    records = []
    stop = 'requested prefix limit'
    with archive.open('wb') as output, gzip.GzipFile(fileobj=output, mode='wb', filename='', mtime=0) as compressed:
        for case in index['cases'][start:start+maximum]:
            if time.monotonic()-started >= seconds:
                stop = 'wall-time bound reached before next core'
                break
            before = time.monotonic()
            record = analyze_core(domain, case)
            data = canonical(record)+b'\n'
            compressed.write(data)
            compressed.flush()
            raw_hash.update(data)
            summary = {key: record[key] for key in ('index', 'admitted_columns', 'admitted_original_signatures',
                       'column_domain_sha256', 'attachment_vector_rank_mod2', 'Gram_outer_product_rank_mod2',
                       'excluded_by_current_exact_checks')}
            records.append(summary)
            print(json.dumps({**summary, 'seconds': time.monotonic()-before,
                              'triple_rows': record['triple_support']['nontrivial_capacity_one_rows']}), flush=True)
            progress = {'status': 'bounded attachment census running', 'processed_cores': records,
                        'complete_index_cases': len(index['cases']), 'all_cores_processed': False}
            (directory/'progress.json').write_text(json.dumps(progress, indent=2)+'\n')
    if start+len(records) == len(index['cases']):
        stop = 'all indexed cores processed from requested start'
    certificate = {'status': 'bounded exact attachment-domain prefix complete; no optimizer called',
                   'source_sha256': digest(Path(__file__)), 'census_sha256': CENSUS_SHA,
                   'base_domain_sha256': domain[-1], 'index_sha256': digest(index_path),
                   'complete_index_cases': len(index['cases']),
                   'matching_orbits_after_local_stabilizers': index['matching_orbits_after_local_stabilizers'],
                   'start_core': start, 'requested_maximum_cores': maximum, 'requested_seconds': seconds,
                   'processed_cores': records, 'all_cores_processed': start == 0 and len(records) == len(index['cases']),
                   'stop_reason': stop, 'elapsed_seconds': time.monotonic()-started,
                   'archive': str(archive.relative_to(ROOT)), 'archive_sha256': digest(archive),
                   'decompressed_jsonl_sha256': raw_hash.hexdigest(),
                   'optimizer_called': False, 'binary_incidence_model_solved': False,
                   'whole_core_family_excluded': False}
    (directory/'certificate.json').write_text(json.dumps(certificate, indent=2)+'\n')
    print(json.dumps({key: value for key, value in certificate.items() if key != 'processed_cores'}, indent=2), flush=True)
    return certificate


def replay(directory):
    certificate = json.loads((directory/'certificate.json').read_text())
    assert certificate['source_sha256'] == digest(Path(__file__))
    domain, index = load_domain()
    assert canonical(index)+b'\n' == (directory/'all-core-index.json').read_bytes()
    assert digest(directory/'all-core-index.json') == certificate['index_sha256']
    archive = ROOT/certificate['archive']
    assert digest(archive) == certificate['archive_sha256']
    raw = gzip.decompress(archive.read_bytes())
    assert sha(raw) == certificate['decompressed_jsonl_sha256']
    saved = [json.loads(line) for line in raw.splitlines()]
    assert [item['index'] for item in saved] == [item['index'] for item in certificate['processed_cores']]
    for item in saved:
        actual = analyze_core(domain, index['cases'][item['index']])
        assert json.loads(json.dumps(actual)) == item
    result = {'status': 'complete case index and every saved attachment domain/row/rank/triple count replayed',
              'processed_cores': len(saved), 'all_indexed_cores': len(index['cases']),
              'all_cores_processed': certificate['all_cores_processed'], 'optimizer_called': False}
    print(json.dumps(result, indent=2), flush=True)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--seconds', type=float, default=30)
    parser.add_argument('--maximum-cores', type=int, default=32)
    parser.add_argument('--start-core', type=int, default=0)
    parser.add_argument('--replay', action='store_true')
    args = parser.parse_args()
    if args.replay:
        replay(args.directory.resolve())
    else:
        generate(args.directory.resolve(), args.seconds, args.maximum_cores, args.start_core)
