"""Verified lexicographic overlay for the complete rooted Conway-99 model.

Analysis enumerates only small groups and Boolean controls. It does not
build or solve a 99-vertex CNF. The separate build command appends the
overlay to one already frozen normalized case, leaving all base files
unchanged. No graph automorphism or extra graph structure is assumed.
"""

import argparse
import hashlib
from itertools import combinations, permutations, product
import json
from pathlib import Path
import shutil

from pysat.formula import IDPool
from pysat.solvers import Solver

import root_full_caps as base
import root_full_caps_lex_coverage as coverage


def lex_clauses(left, right, pool):
    """Existential CNF for positive Boolean vectors left <=lex right.

    Equality flags only need the forward implication: if the preceding
    prefix is equal and this pair agrees, the next prefix flag is true.
    Every true equal prefix is therefore marked. On a valid comparison,
    assigning flags to exact prefix equality satisfies all clauses.
    """
    assert len(left) == len(right)
    assert all(isinstance(v, int) and v > 0 for v in left+right)
    pairs = [(x, y) for x, y in zip(left, right) if x != y]
    clauses, prefix = [], None
    for position, (x, y) in enumerate(pairs):
        guard = [] if prefix is None else [-prefix]
        clauses.append(guard+[-x, y])
        if position+1 < len(pairs):
            following = pool.id()
            clauses.append(guard+[x, y, following])
            clauses.append(guard+[-x, -y, following])
            prefix = following
    assert len(clauses) == (3*len(pairs)-2 if pairs else 0)
    return clauses


def lex_controls(maximum=6):
    independent_count = alias_count = 0
    for length in range(maximum+1):
        left = list(range(1, length+1))
        right = list(range(length+1, 2*length+1))
        pool = IDPool(start_from=2*length+1)
        clauses = lex_clauses(left, right, pool)
        clauses += [[v, -v] for v in left+right]
        with Solver(name='glucose4', bootstrap_with=clauses) as solver:
            for values in product((False, True), repeat=2*length):
                assumptions = [v if values[v-1] else -v for v in left+right]
                expected = values[:length] <= values[length:]
                assert solver.solve(assumptions=assumptions) == expected
                independent_count += 1
        for order in permutations(range(length)):
            right = [left[i] for i in order]
            pool = IDPool(start_from=length+1)
            clauses = lex_clauses(left, right, pool)
            clauses += [[v, -v] for v in left]
            with Solver(name='glucose4', bootstrap_with=clauses) as solver:
                for values in product((False, True), repeat=length):
                    assumptions = [v if values[v-1] else -v for v in left]
                    expected = values <= tuple(values[i] for i in order)
                    assert solver.solve(assumptions=assumptions) == expected
                    alias_count += 1
    assert maximum != 6 or (independent_count, alias_count) == (5461, 50363)
    return {'status': 'exact pass', 'maximum_vector_length': maximum,
            'independent_vector_assignments': independent_count,
            'permuted_vector_assignments': alias_count,
            'total_assignments': independent_count+alias_count}


def primary_domain(degree):
    rows, labels, signatures, need, edges = base.domain(degree)
    variables = {edge: i+1 for i, edge in enumerate(edges)}
    record = {'core_rows': rows, 'labels': labels, 'signatures': signatures,
              'edge_variables': [[a, b, variable] for (a, b), variable in variables.items()]}
    digest = hashlib.sha256(json.dumps(record, sort_keys=True,
                                      separators=(',', ':')).encode()).hexdigest()
    return rows, labels, signatures, need, edges, variables, digest


def lift(parts, local_image, degree=14):
    """Lift a signed-axis stabilizer to outside vertices and primary edges."""
    rows, labels, signatures, need, edges, variables, _ = primary_domain(degree)
    assert sum(parts) == (degree-2)//2
    assert sorted(local_image) == list(range(degree-2))
    assert all(local_image[i ^ 1] == (local_image[i] ^ 1) for i in range(degree-2))
    assert coverage.moved_matching(coverage.canonical_matching(parts), local_image) == \
        coverage.canonical_matching(parts)
    near_image = [0, 1]+[2+v for v in local_image]
    core_image = [0]+[1+v for v in near_image]
    index = {pair: i for i, pair in enumerate(labels)}
    outside_image = [index[tuple(sorted((near_image[a], near_image[b])))]
                     for a, b in labels]
    assert sorted(outside_image) == list(range(len(labels)))
    for i, row in enumerate(rows):
        assert sum(1 << core_image[j] for j in range(len(rows)) if row >> j & 1) == rows[core_image[i]]
    for t, signature in enumerate(signatures):
        moved = outside_image[t]
        assert tuple(sorted(core_image[i] for i in signature)) == signatures[moved]
        assert all(need[moved][core_image[i]] == need[t][i] for i in range(degree+1))
        assert need[moved][-1] == need[t][-1]
    edge_image = [variables[tuple(sorted((outside_image[a], outside_image[b])))] for a, b in edges]
    assert sorted(edge_image) == list(range(1, len(edges)+1))
    for a, b in edges:
        assert len(set(signatures[a]) & set(signatures[b])) == \
            len(set(signatures[outside_image[a]]) & set(signatures[outside_image[b]]))
    units = base.anchor_units(degree, parts, labels, variables)
    assert {edge_image[v-1] for v in units} == set(units)
    broken, _ = base.broken_rook_clauses(degree, labels, variables)
    moved_broken = {tuple(sorted(edge_image[v-1] if v > 0 else -edge_image[-v-1]
                                 for v in clause)) for clause in broken}
    assert moved_broken == {tuple(sorted(clause)) for clause in broken}
    # Relabeling sends old edge e to edge_image[e]. Thus the new coordinate
    # at j equals the old coordinate at the inverse image of j.
    right = [0]*len(edges)
    for old, new in enumerate(edge_image, 1):
        right[new-1] = old
    assert sorted(right) == list(range(1, len(edges)+1))
    return {'near_image': near_image, 'outside_image': outside_image,
            'edge_image': edge_image, 'lex_right': right}


def rook_control():
    cnf, variables, rows, labels, signatures, metadata = base.formula(4)
    near = [(0, 1), (0, 2), (1, 0), (2, 0)]
    coordinates = [(0, 0)]+near+[(near[b][0], near[a][1]) for a, b in labels]
    assert len(set(coordinates)) == 9
    grid = [[int(i != j and (p[0] == q[0] or p[1] == q[1]))
             for j, q in enumerate(coordinates)] for i, p in enumerate(coordinates)]
    assert all(sum(row) == 4 for row in grid)
    assert all(sum(grid[i][w]*grid[j][w] for w in range(9))+grid[i][j] == 2
               for i, j in combinations(range(9), 2))
    assumptions = [v if grid[5+a][5+b] else -v for (a, b), v in variables.items()]
    cnf.extend([[v] for v in base.anchor_units(4, (1,), labels, variables)])
    pool = IDPool(start_from=cnf.nv+1)
    generators = coverage.component_generators((1,))
    overlay = []
    for generator in generators:
        lifted = lift((1,), generator['image'], 4)
        overlay.extend(lex_clauses(list(range(1, 7)), lifted['lex_right'], pool))
    cnf.extend(overlay)
    with Solver(name='glucose4', bootstrap_with=cnf.clauses) as solver:
        assert solver.solve(assumptions=assumptions)
        exact = base.inspect({v for v in solver.get_model() if v > 0},
                             4, rows, labels, signatures, variables)
        assert exact['adjacency_lists'] == [[j for j in range(9) if grid[i][j]] for i in range(9)]
        assert solver.solve()
        base.inspect({v for v in solver.get_model() if v > 0},
                     4, rows, labels, signatures, variables)
    return {'status': 'direct nine-rook and free normalized overlay both pass',
            'vertices': 9, 'pair_equations_checked': 36, 'primary_edge_variables': 6,
            'generator_count': len(generators), 'lex_clauses': len(overlay),
            'broken_rook_clauses_checked': metadata['broken_rook_clauses']}


def describe(coverage_path, manifest_path):
    group = coverage.replay(coverage_path)
    assert group['axes'] == 6
    manifest = json.loads(manifest_path.read_text())
    directory = Path(__file__).resolve().parent
    for name, expected in manifest['source_hashes'].items():
        assert base.digest(directory/name) == expected
    _, _, _, _, edges, _, domain_hash = primary_domain(14)
    assert domain_hash == manifest['domain_sha256']
    metadata = manifest['metadata']
    assert metadata['edge_variables'] == len(edges) == 3486
    cases = []
    for group_case, base_case in zip(group['cases'], manifest['cases'], strict=True):
        assert group_case['index'] == base_case['index']
        parts = group_case['partition']
        assert parts == base_case['partition']
        generators, added_variables, added_clauses = [], 0, 0
        for generator in group_case['generators']:
            lifted = lift(tuple(parts), generator['image'])
            active = sum(v != i for i, v in enumerate(lifted['lex_right'], 1))
            variables = max(0, active-1)
            clauses = 3*active-2 if active else 0
            generators.append({**generator, 'moved_primary_coordinates': active,
                               'edge_image_sha256': coverage.compact_hash(lifted['edge_image']),
                               'lex_right_sha256': coverage.compact_hash(lifted['lex_right']),
                               'added_variables': variables, 'added_clauses': clauses})
            added_variables += variables
            added_clauses += clauses
        cases.append({'index': group_case['index'], 'partition': parts,
                      'stabilizer_order': group_case['stabilizer_order'],
                      'generator_count': len(generators), 'generators': generators,
                      'base_cnf_sha256': base_case['cnf_sha256'],
                      'base_variables': base_case['variables'],
                      'base_clauses': base_case['clauses'],
                      'added_variables': added_variables, 'added_clauses': added_clauses,
                      'total_variables': base_case['variables']+added_variables,
                      'total_clauses': base_case['clauses']+added_clauses})
    return {'status': 'exact coverage, domain, lift, and small Boolean controls pass; no 99-point solve',
            'scope': 'relabeling overlay for each of the eleven unrestricted normalized cases',
            'coverage': str(coverage_path), 'coverage_sha256': base.digest(coverage_path),
            'base_manifest': str(manifest_path), 'base_manifest_sha256': base.digest(manifest_path),
            'base_source_hashes': manifest['source_hashes'],
            'source_hashes': {name: base.digest(directory/name) for name in
                              ['root_full_caps_lex.py', 'root_full_caps_lex_coverage.py']},
            'domain_sha256': domain_hash, 'primary_edge_variables': len(edges),
            'lex_controls': lex_controls(), 'rook_positive_control': rook_control(),
            'graph_automorphism_assumptions': 0, 'large_cnf_built': False, 'cases': cases}


def replay(path):
    saved = json.loads(path.read_text())
    actual = describe(Path(saved['coverage']), Path(saved['base_manifest']))
    assert saved == actual
    return actual


def build(analysis_path, index, output, result_path):
    """Append a verified overlay, without rebuilding or editing the base CNF."""
    record = replay(analysis_path)
    case = record['cases'][index]
    assert case['index'] == index
    manifest = json.loads(Path(record['base_manifest']).read_text())
    original = manifest['cases'][index]
    source = Path(original['cnf_path'])
    assert base.digest(source) == case['base_cnf_sha256']
    assert output.resolve() != source.resolve()
    pool = IDPool(start_from=case['base_variables']+1)
    clauses = []
    for generator in case['generators']:
        lifted = lift(tuple(case['partition']), generator['image'])
        clauses.extend(lex_clauses(list(range(1, 3487)), lifted['lex_right'], pool))
    assert len(clauses) == case['added_clauses']
    assert pool.top == case['total_variables']
    output.parent.mkdir(parents=True, exist_ok=True)
    with source.open('rb') as incoming, output.open('wb') as outgoing:
        assert incoming.readline() == f'p cnf {case["base_variables"]} {case["base_clauses"]}\n'.encode()
        outgoing.write(f'p cnf {case["total_variables"]} {case["total_clauses"]}\n'.encode())
        shutil.copyfileobj(incoming, outgoing)
        for clause in clauses:
            outgoing.write((' '.join(map(str, clause))+' 0\n').encode())
    result = {'status': 'complete overlay CNF built; no solve',
              'analysis': str(analysis_path), 'analysis_sha256': base.digest(analysis_path),
              'source_hashes': record['source_hashes'],
              'case': case, 'cnf': str(output), 'cnf_sha256': base.digest(output)}
    base.save(result_path, result)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    analyze = sub.add_parser('analyze')
    analyze.add_argument('--coverage', type=Path, required=True)
    analyze.add_argument('--manifest', type=Path, required=True)
    analyze.add_argument('--output', type=Path, required=True)
    repeat = sub.add_parser('replay')
    repeat.add_argument('analysis', type=Path)
    construct = sub.add_parser('build')
    construct.add_argument('analysis', type=Path)
    construct.add_argument('--case', type=int, required=True)
    construct.add_argument('--cnf', type=Path, required=True)
    construct.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.command == 'analyze':
        result = describe(args.coverage, args.manifest)
        base.save(args.output, result)
    elif args.command == 'replay':
        result = replay(args.analysis)
    else:
        result = build(args.analysis, args.case, args.cnf, args.output)
    if args.command == 'build':
        print(json.dumps({'status': result['status'], 'case': result['case']['index'],
                          'variables': result['case']['total_variables'],
                          'clauses': result['case']['total_clauses'],
                          'cnf_sha256': result['cnf_sha256']}), flush=True)
    else:
        print(json.dumps({'status': result['status'], 'lex_controls': result['lex_controls'],
                          'rook_positive_control': result['rook_positive_control'],
                          'cases': [{key: case[key] for key in
                                     ['index', 'partition', 'stabilizer_order', 'generator_count',
                                      'added_variables', 'added_clauses', 'total_variables', 'total_clauses']}
                                    for case in result['cases']]}), flush=True)
