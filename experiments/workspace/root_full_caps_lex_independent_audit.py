"""Independent small group/lift/Boolean audit, with no SAT or CNF rebuild."""

import argparse
import ast
from collections import deque
import hashlib
from itertools import combinations, permutations, product
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LOGS = ROOT / 'experiments/logs/root-full-caps-lex'
EXPECTED = {
    'root_full_caps_lex.py': '736ccdd9060144eded621dc409a7ebd8ff4f3c3fb081ba606994c05a3f24a848',
    'root_full_caps_lex_coverage.py': '9f5ca4aed852b5fbf29a65dd02244bc83a5ceab99254e4d66c831da6ac16c27a',
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compact(value):
    return hashlib.sha256(json.dumps(value, separators=(',', ':')).encode()).hexdigest()


def pair_preserving_maps(axes):
    """Recursive endpoint-image construction, independent of owner enumeration."""
    def visit(image, remaining):
        if not remaining:
            yield tuple(image)
            return
        for a in sorted(remaining):
            for first, second in ((2*a, 2*a+1), (2*a+1, 2*a)):
                yield from visit(image+[first, second], remaining-{a})
    yield from visit([], set(range(axes)))


def canonical(parts):
    edges = []
    offset = 0
    for size in parts:
        for j in range(size):
            edges.append(tuple(sorted((2*(offset+j)+1, 2*(offset+(j+1) % size)))))
        offset += size
    return sorted(edges)


def closure(images):
    identity = tuple(range(12))
    seen, queue = {identity}, deque([identity])
    while queue:
        p = queue.popleft()
        for g in images:
            q = tuple(p[g[i]] for i in range(12))
            if q not in seen:
                seen.add(q)
                queue.append(q)
    return seen


def direct_boolean_check(source):
    # Execute only the reviewed pure clause-producing function, not imports,
    # solver controls, model construction, or the source module's main body.
    tree = ast.parse(source.read_text())
    fn = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
              and node.name == 'lex_clauses')
    namespace = {}
    exec(compile(ast.Module(body=[fn], type_ignores=[]), str(source), 'exec'), namespace)
    lex = namespace['lex_clauses']

    class Pool:
        def __init__(self, primary):
            self.top = primary
        def id(self):
            self.top += 1
            return self.top

    checked = 0
    for n in range(5):
        left = list(range(1, n+1))
        comparisons = [(2*n, list(range(n+1, 2*n+1)))]
        comparisons += [(n, [i+1 for i in p]) for p in permutations(range(n))]
        for primary, right in comparisons:
            pool = Pool(primary)
            clauses = lex(left, right, pool)
            masks = [(sum(1 << (v-1) for v in clause if v > 0),
                      sum(1 << (-v-1) for v in clause if v < 0)) for clause in clauses]
            for values in range(1 << primary):
                expected = tuple((values >> (i-1)) & 1 for i in left) <= \
                    tuple((values >> (i-1)) & 1 for i in right)
                actual = any(all((bits & positive) or ((~bits) & negative)
                                 for positive, negative in masks)
                             for auxiliary in range(1 << (pool.top-primary))
                             for bits in (values | (auxiliary << primary),))
                assert actual == expected
                checked += 1
    assert checked == 784
    return checked


def audit():
    directory = ROOT / 'experiments/workspace'
    for name, expected in EXPECTED.items():
        assert sha(directory/name) == expected
    coverage = json.loads((LOGS/'coverage.json').read_text())
    analysis = json.loads((LOGS/'analysis.json').read_text())
    assert analysis['source_hashes'] == EXPECTED
    assert analysis['coverage_sha256'] == sha(LOGS/'coverage.json')
    assert analysis['base_manifest_sha256'] == sha(ROOT/analysis['base_manifest'])
    for name, expected in analysis['base_source_hashes'].items():
        assert sha(directory/name) == expected

    ambient = set(pair_preserving_maps(6))
    assert len(ambient) == 46080
    assert compact(sorted(ambient)) == coverage['ambient_group_sha256']
    labels = [pair for pair in combinations(range(14), 2) if pair[0] ^ 1 != pair[1]]
    label_index = {pair: i for i, pair in enumerate(labels)}
    edges = list(combinations(range(84), 2))
    edge_index = {pair: i+1 for i, pair in enumerate(edges)}
    signatures = [(a+1, b+1) for a, b in labels]
    rows = [sum(1 << i for i in range(1, 15))]
    rows += [1 | (1 << (1+(a ^ 1))) for a in range(14)]
    domain = {'core_rows': rows, 'labels': labels, 'signatures': signatures,
              'edge_variables': [[a, b, edge_index[a, b]] for a, b in edges]}
    domain_sha = hashlib.sha256(json.dumps(domain, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    assert domain_sha == analysis['domain_sha256']
    broken = set()
    for a, b in combinations(range(7), 2):
        cell = [label_index[2*a+s, 2*b+t] for s, t in product(range(2), repeat=2)]
        sides = [(cell[0], cell[1]), (cell[0], cell[2]), (cell[1], cell[3]), (cell[2], cell[3])]
        variables = [edge_index[tuple(sorted(pair))] for pair in sides]
        for missing in range(4):
            broken.add(tuple(sorted(v if i == missing else -v for i, v in enumerate(variables))))
    assert len(broken) == 84

    cases = []
    for case, model in zip(coverage['cases'], analysis['cases'], strict=True):
        parts = case['partition']
        matching = canonical(parts)
        assert matching == [tuple(edge) for edge in case['canonical_matching']]
        partner = [None]*12
        for a, b in matching:
            partner[a], partner[b] = b, a
        stabilizer = {g for g in ambient if all(g[partner[i]] == partner[g[i]] for i in range(12))}
        assert len(stabilizer) == case['stabilizer_order']
        assert compact(sorted(stabilizer)) == case['stabilizer_sha256']
        generators = [tuple(g['image']) for g in case['generators']]
        assert closure(generators) == stabilizer
        units = {edge_index[tuple(sorted((label_index[0, 2+a], label_index[0, 2+b])))]
                 for a, b in matching}
        added_variables = added_clauses = 0
        for g, owner in zip(generators, model['generators'], strict=True):
            near = (0, 1)+tuple(2+i for i in g)
            core = (0,)+tuple(1+i for i in near)
            assert all(sum(1 << core[j] for j in range(15) if rows[i] >> j & 1) == rows[core[i]]
                       for i in range(15))
            outside = [label_index[tuple(sorted((near[a], near[b])))] for a, b in labels]
            moved_edges = [edge_index[tuple(sorted((outside[a], outside[b])))] for a, b in edges]
            assert sorted(moved_edges) == list(range(1, 3487))
            assert {moved_edges[v-1] for v in units} == units
            moved_broken = {tuple(sorted(moved_edges[v-1] if v > 0 else -moved_edges[-v-1]
                                         for v in clause)) for clause in broken}
            assert moved_broken == broken
            inverse = [None]*3486
            for old, new in enumerate(moved_edges, 1):
                inverse[new-1] = old
            assert compact(moved_edges) == owner['edge_image_sha256']
            assert compact(inverse) == owner['lex_right_sha256']
            active = sum(old != new for old, new in enumerate(inverse, 1))
            assert owner['moved_primary_coordinates'] == active
            nv, nc = max(0, active-1), (3*active-2 if active else 0)
            assert (nv, nc) == (owner['added_variables'], owner['added_clauses'])
            added_variables += nv
            added_clauses += nc
        assert added_variables == model['added_variables']
        assert added_clauses == model['added_clauses']
        assert model['total_variables'] == model['base_variables']+added_variables
        assert model['total_clauses'] == model['base_clauses']+added_clauses
        cases.append({'index': case['index'], 'partition': parts,
                      'stabilizer_order': len(stabilizer), 'generator_count': len(generators),
                      'exact_edge_and_inverse_hashes_match': True,
                      'added_variables': added_variables, 'added_clauses': added_clauses})
    return {
        'status': 'independent stabilizer/lift/lex audit PASS',
        'source_hashes': EXPECTED,
        'audit_source_sha256': sha(Path(__file__)),
        'coverage_sha256': sha(LOGS/'coverage.json'),
        'analysis_sha256': sha(LOGS/'analysis.json'),
        'ambient_maps_independently_enumerated': len(ambient),
        'primary_edges': len(edges),
        'pure_Boolean_cases_checked': direct_boolean_check(directory/'root_full_caps_lex.py'),
        'cases': cases,
        'proof_review': [
            'A lexicographically minimum primary assignment in each finite stabilizer orbit satisfies every generator comparison.',
            'A relabeling need not fix the completed graph; every orbit image remains a valid normalized primary graph.',
            'New edge coordinate j equals the old coordinate at its inverse edge image.',
            'Identical variable positions are always equal and can be skipped.',
            'Forward equality flags force every actually equal prefix; exact equality flags extend every valid comparison.',
            'Overlay auxiliaries start after the maximum variable of the full base CNF and are fresh across generators.',
            'The build command preserves every base clause and appends the overlay under an updated DIMACS header.'
        ],
        'solver_called': False,
        'large_CNF_built': False,
        'base_CNF_rebuilt': False,
        'limits': 'This audit certifies the relabeling overlay, not a solution or exclusion of any99-vertex case.'
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--replay', type=Path)
    args = parser.parse_args()
    result = audit()
    if args.output:
        args.output.write_text(json.dumps(result, indent=2)+'\n')
    if args.replay:
        assert result == json.loads(args.replay.read_text())
    print(result['status'])
    print('46080 maps,11 full stabilizers,784 direct Boolean cases; no solver or large CNF.')
