"""Independent cheap domain audit; never imports a SAT builder or solver."""

import argparse
from itertools import combinations, permutations, product
import hashlib
import json
from pathlib import Path


SOURCE_SHA256 = '8cc529d12ef897234e1d04bab388e54e88186c7163c8182ece6a518a2a082bc6'
ROOT = Path(__file__).resolve().parents[2]
LOGS = ROOT / 'experiments/logs/grids-and-triangles'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rook(p, q):
    return p != q and (p // 3 == q // 3 or p % 3 == q % 3)


def reconstruct():
    B = [[0] * 27 for _ in range(27)]
    for i, j in combinations(range(27), 2):
        a, p = divmod(i, 9)
        b, q = divmod(j, 9)
        if a == b:
            edge = rook(p, q) if a < 2 else not rook(p, q)
        else:
            edge = p == q
        B[i][j] = B[j][i] = int(edge)
    rows = [sum(v << j for j, v in enumerate(row)) for row in B]
    G = [[12 * int(i == j) + 2 - B[i][j]
          - sum(B[i][k] * B[k][j] for k in range(27))
          for j in range(27)] for i in range(27)]
    triples = [(p, q, t) for p, q, t in product(range(9), repeat=3)
               if p != q and not rook(p, q) and t not in (p, q)]
    signatures = [(p, 9 + q, 18 + t) for p, q, t in triples]
    assert len(signatures) == 252
    assert signatures == [(p, 9 + q, 18 + t)
                          for p, q, t in product(range(9), repeat=3)
                          if all(G[i][j] > 0 for i, j in combinations((p, 9 + q, 18 + t), 2))]
    needs = [[2 - sum(B[i][j] + int(i == j) for j in sites)
              for i in range(27)] for sites in signatures]
    masks = [sum(1 << i for i in sites) for sites in signatures]
    assert all(sum(row) == 6 for row in B)
    assert all(min(row) >= 0 and sum(row) == 33 for row in needs)
    assert all(not B[i][j] for sites in signatures for i, j in combinations(sites, 2))
    eligible = [[(masks[s] & masks[t]).bit_count() <= 1
                 and all(needs[s][i] > 0 for i in signatures[t])
                 and all(needs[t][i] > 0 for i in signatures[s])
                 for t in range(252)] for s in range(252)]
    return B, rows, G, triples, signatures, needs, masks, eligible


def audit():
    source = ROOT / 'experiments/workspace/complement_rook_duplicate_row_projection.py'
    assert sha(source) == SOURCE_SHA256
    coverage_path = LOGS / 'complement-rook-duplicate-row-coverage.json'
    coverage = json.loads(coverage_path.read_text())
    assert coverage['source_sha256'] == SOURCE_SHA256
    B, rows, G, triples, signatures, needs, masks, eligible = reconstruct()
    index = {triple: i for i, triple in enumerate(triples)}
    tips = [t for t in range(9) if (0, 4, t) in index]
    assert tips == [1, 2, 3, 5, 6, 7, 8] and G[0][13] == 2

    point_maps = set()
    for rp in permutations(range(3)):
        for cp in permutations(range(3)):
            for transposed in (False, True):
                image = []
                for p in range(9):
                    r, c = divmod(p, 3)
                    if transposed:
                        r, c = c, r
                    image.append(3 * rp[r] + cp[c])
                point_maps.add(tuple(image))
    assert len(point_maps) == 72
    stabilizer = []
    for points in sorted(point_maps):
        for swap in (False, True):
            image_pair = (points[4], points[0]) if swap else (points[0], points[4])
            if image_pair != (0, 4):
                continue
            core = [9 * (1 - a if swap and a < 2 else a) + points[p]
                    for a in range(3) for p in range(9)]
            sigmap = [index[(points[q], points[p], points[t]) if swap else
                            (points[p], points[q], points[t])] for p, q, t in triples]
            assert all(B[i][j] == B[core[i]][core[j]] and G[i][j] == G[core[i]][core[j]]
                       for i in range(27) for j in range(27))
            assert all(tuple(sorted(core[i] for i in signatures[s])) == signatures[sigmap[s]]
                       for s in range(252))
            stabilizer.append({'point_permutation': list(points),
                               'swap_first_two_bases': swap,
                               'core_permutation': core,
                               'signature_permutation': sigmap})
    stabilizer.sort(key=lambda g: g['core_permutation'])
    assert len(stabilizer) == 4 and stabilizer == coverage['stabilizer']
    remaining = set(combinations(tips, 2))
    assert len(remaining) == 21
    orbits = []
    for case in coverage['cases']:
        rep = tuple(case['representative_tips'])
        assert rep == min(remaining)
        images = {tuple(sorted(g['point_permutation'][t] for t in rep)) for g in stabilizer}
        assert images <= remaining and len(images) == case['orbit_size']
        assert images == {tuple(member['tips']) for member in case['members']}
        for member in case['members']:
            points = stabilizer[member['stabilizer_index']]['point_permutation']
            mapped = [points[t] for t in rep]
            assert sorted(mapped) == member['tips']
            assert [member['tips'].index(t) for t in mapped] == member['row_order']
        remaining -= images
        orbits.append({'representative': list(rep), 'size': len(images),
                       'members': [list(p) for p in sorted(images)]})
    assert not remaining and len(orbits) == 8
    assert [o['size'] for o in orbits] == [4, 1, 4, 2, 2, 2, 2, 4]

    equations = {(tuple(s + 1 for s, sites in enumerate(signatures) if i in sites and j in sites), G[i][j])
                 for i in range(27) for j in range(i, 27)}
    case_records = []
    for ci, orbit in enumerate(orbits):
        sources = [index[0, 4, t] for t in orbit['representative']]
        assert (masks[sources[0]] & masks[sources[1]]).bit_count() == 2
        assert not eligible[sources[0]][sources[1]]
        systems = []
        for s in sources:
            neighbors = [w for w in range(252) if eligible[s][w]]
            zero = [w for w in neighbors if not masks[s] & masks[w]]
            one = [w for w in neighbors if masks[s] & masks[w]]
            pairs = [(v, w) for v, w in combinations(zero, 2)
                     if not masks[v] & masks[w] and eligible[v][w]]
            packing = [(v, w) for v, w in combinations(neighbors, 2)
                       if (masks[v] & masks[w]).bit_count() >= 2]
            assert not set(sources) & set(neighbors)
            assert all(needs[s][i] == 1 for i in signatures[s])
            systems.append({'source': s, 'neighbors': neighbors, 'zero': zero,
                            'one': one, 'matching_pairs': pairs, 'packing_pairs': packing})
        common = sorted(set(systems[0]['neighbors']) & set(systems[1]['neighbors']))
        primary = [tuple(sorted((system['source'], w))) for system in systems for w in system['neighbors']]
        assert len(primary) == len(set(primary))
        assert all(edge not in set(primary) for system in systems for edge in system['matching_pairs'])

        next_id = 253
        nvars = []
        for system in systems:
            nvars.append([(w, next_id + k) for k, w in enumerate(system['neighbors'])])
            next_id += len(system['neighbors'])
        mvars = []
        for system in systems:
            mvars.append([[v, w, next_id + k] for k, (v, w) in enumerate(system['matching_pairs'])])
            next_id += len(system['matching_pairs'])
        exact_domain = {'core_rows': rows, 'core_gram': G, 'signatures': signatures,
                        'mixed_demands': needs, 'sources': sources, 'systems': systems,
                        'disjointness_candidates': common,
                        'selector_variables': [(s, s + 1) for s in range(252)],
                        'neighbor_variables': nvars, 'pairing_variables': mvars}
        domain_hash = hashlib.sha256(json.dumps(exact_domain, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
        manifest_path = LOGS / f'complement-rook-duplicate-row-{ci}-model.json'
        manifest = json.loads(manifest_path.read_text())
        assert manifest['domain_sha256'] == domain_hash
        assert manifest['coverage_sha256'] == sha(coverage_path)
        assert manifest['source_indices'] == sources
        assert manifest['covered_tip_pairs'] == orbit['size']
        assert manifest['distinct_gram_counts'] == len(equations)
        assert manifest['neighbor_variables'] == [len(s['neighbors']) for s in systems]
        assert manifest['matching_variables'] == [len(s['matching_pairs']) for s in systems]
        assert manifest['packing_clauses'] == [len(s['packing_pairs']) for s in systems]
        assert manifest['disjointness_clauses'] == len(common)
        for name, expected in manifest['source_hashes'].items():
            assert sha(source.with_name(name)) == expected
        case_records.append({'case': ci, 'tip_pair': orbit['representative'],
                             'covered_pairs': orbit['size'], 'source_indices': sources,
                             'neighbors': [len(s['neighbors']) for s in systems],
                             'matching_pairs': [len(s['matching_pairs']) for s in systems],
                             'packing_pairs': [len(s['packing_pairs']) for s in systems],
                             'disjointness_clauses': len(common),
                             'domain_sha256': domain_hash,
                             'manifest_domain_hash_match': True})
    assert [r['disjointness_clauses'] for r in case_records] == [119, 123, 126, 131, 121, 137, 127, 139]

    # Separate local matching witnesses must not be equated as global edges.
    copies = set()
    for ms, mt, su, sv, tu, tv in product((0, 1), repeat=6):
        if ms <= min(su, sv) and mt <= min(tu, tv) and su + tu <= 1 and sv + tv <= 1:
            assert not (ms and mt)
            copies.add((ms, mt))
    assert copies == {(0, 0), (1, 0), (0, 1)}

    return {
        'status': 'independent two-source coverage/domain/necessity audit PASS',
        'builder_sha256': SOURCE_SHA256,
        'audit_source_sha256': sha(Path(__file__)),
        'coverage_sha256': sha(coverage_path),
        'core_relabelings_examined': 144,
        'ordered_normalized_RS_stabilizer_order': 4,
        'tip_pairs_covered': 21,
        'orbits': orbits,
        'cases': case_records,
        'shared_incidence_selectors': 252,
        'parameter_a_unrestricted': True,
        'fixed_incidence_witness': False,
        'graph_automorphism_assumption': False,
        'source_review': [
            'The Gram equation at core pair R0,S4 forces exactly two of the seven tip signatures.',
            'All21 unordered choices are explicitly transported by actual core/domain relabelings.',
            'Each source has all27 mixed equations, degree11, eight zero-overlap and three one-overlap neighbors.',
            'The two sources have two core common neighbors, hence are nonadjacent with disjoint exterior neighborhoods.',
            'Every neighbor bit activates the same shared signature selector.',
            'Matching copies express edges used inside one source neighborhood; an inactive copy asserts no global nonedge.',
            'Primary source-edge domains are distinct and do not intersect either matching domain.',
            'All primary IDs precede cardinality auxiliary allocation; extraction uses the same primary allocation.',
            'The union of the two selected row systems has30 distinct exterior edges and satisfies the asserted partial caps.'
        ],
        'solver_called': False,
        'CNF_rebuilt': False,
        'proof_rebuilt': False,
        'limits': 'Necessary two-row projection only; no full exterior graph or SAT/UNSAT outcome is certified here.'
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--replay', type=Path)
    args = parser.parse_args()
    result = audit()
    if args.replay:
        assert result == json.loads(args.replay.read_text())
    if args.output:
        args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(result['status'])
    print('All8 domain hashes match; all21 tip-pair transports checked; no solver/CNF/proof rebuild.')
