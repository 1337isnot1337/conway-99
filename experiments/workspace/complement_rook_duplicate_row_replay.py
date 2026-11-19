"""Replay duplicate-row partial witnesses by direct99-point integer matrices."""

import argparse
import hashlib
from itertools import combinations, product
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def replay(result_path):
    result = json.loads(result_path.read_text())
    assert result['status'] == 'SAT two-row partial witness verified; no complete graph claim'
    manifest_path = ROOT/result['manifest_path']
    assert sha(manifest_path) == result['manifest_sha256']
    manifest = json.loads(manifest_path.read_text())
    for name, expected in manifest['source_hashes'].items():
        assert sha(Path(__file__).with_name(name)) == expected
    coverage_path = ROOT/manifest['coverage_path']
    assert sha(coverage_path) == manifest['coverage_sha256']
    coverage = json.loads(coverage_path.read_text())
    case = coverage['cases'][manifest['case_index']]
    assert case['representative_tips'] == manifest['representative_tips']
    assert case['orbit_size'] == result['covered_tip_pairs']
    B = [[0]*27 for _ in range(27)]
    for i, j in combinations(range(27), 2):
        a, p = divmod(i, 9)
        b, q = divmod(j, 9)
        rook = p != q and (p//3 == q//3 or p % 3 == q % 3)
        value = int(p == q) if a != b else int((p != q and not rook) if a == 2 else rook)
        B[i][j] = B[j][i] = value
    G = [[12*int(i == j)+2-B[i][j]-sum(B[i][k]*B[k][j] for k in range(27))
          for j in range(27)] for i in range(27)]
    triples = []
    for p, q, t in product(range(9), repeat=3):
        sites = (p, 9+q, 18+t)
        need = [2-sum(B[i][j]+int(i == j) for j in sites) for i in range(27)]
        if min(need) >= 0 and all(G[i][j] > 0 for i, j in combinations(sites, 2)):
            triples.append((p, q, t))
    assert len(triples) == 252
    point = result['partial_witness']
    selected = point['selected_signature_indices']
    assert selected == sorted(set(selected)) and len(selected) == 72
    assert [list(triples[s]) for s in selected] == point['selected_signature_triples']
    sources = point['source_signature_indices']
    assert sources == manifest['source_indices'] and set(sources) <= set(selected)
    assert [list(triples[s]) for s in sources] == manifest['source_triples'] == point['source_triples']
    assert [triples[s] for s in sources] == [(0, 4, t) for t in case['representative_tips']]
    chosen = point['neighbor_signature_indices']
    matches = [[tuple(pair) for pair in pairs] for pairs in point['matching_signature_pairs']]
    assert len(chosen) == len(matches) == 2
    assert not set(chosen[0]) & set(chosen[1])
    for j in range(2):
        assert len(chosen[j]) == len(set(chosen[j])) == 11
        assert set(chosen[j]) <= set(selected)-set(sources)
        assert len(matches[j]) == len(set(matches[j])) == 4
        endpoints = {v for edge in matches[j] for v in edge}
        assert len(endpoints) == 8 and endpoints <= set(chosen[j])
    index = {s: 27+i for i, s in enumerate(selected)}
    adjacency = [sum(value << j for j, value in enumerate(row)) for row in B]+[0]*72
    sites = {s: (triples[s][0], 9+triples[s][1], 18+triples[s][2]) for s in selected}
    assert all(sum(i in sites[s] and j in sites[s] for s in selected) == G[i][j]
               for i in range(27) for j in range(27))
    for s in selected:
        for i in sites[s]:
            adjacency[index[s]] |= 1 << i
            adjacency[i] |= 1 << index[s]
    edges = set()
    for j, source in enumerate(sources):
        edges.update(tuple(sorted((source, w))) for w in chosen[j])
        edges.update(matches[j])
    assert len(edges) == 30
    for v, w in edges:
        assert v != w
        adjacency[index[v]] |= 1 << index[w]
        adjacency[index[w]] |= 1 << index[v]
    degrees = [row.bit_count() for row in adjacency]
    assert degrees[:27] == [14]*27 and all(degrees[index[s]] == 14 for s in sources)
    assert max(degrees) == 14 and sum(degrees)//2 == 327
    assert all(not(adjacency[i] >> i & 1) for i in range(99))
    assert all((adjacency[i] >> j & 1) == (adjacency[j] >> i & 1)
               for i, j in combinations(range(99), 2))
    pair_counts = {(i, j): (adjacency[i] & adjacency[j]).bit_count()+int(adjacency[i] >> j & 1)
                   for i, j in combinations(range(99), 2)}
    assert max(pair_counts.values()) <= 2
    assert all(pair_counts[i, j] == 2 for i, j in combinations(range(27), 2))
    assert all(pair_counts[i, index[s]] == 2 for i in range(27) for s in sources)
    for source in sources:
        local = [i for i in range(99) if adjacency[index[source]] >> i & 1]
        assert len(local) == 14
        assert all(sum(adjacency[v] >> w & 1 for w in local) == 1 for v in local)
    a = sum((p//3 == t//3 or p % 3 == t % 3)
            and (q//3 == t//3 or q % 3 == t % 3)
            for p, q, t in (triples[s] for s in selected))
    assert a == point['parameter_a']
    for member in case['members']:
        transform = coverage['stabilizer'][member['stabilizer_index']]
        image = transform['signature_permutation']
        mapped_sources = [image[s] for s in sources]
        assert sorted(triples[s][2] for s in mapped_sources) == member['tips']
        assert all(triples[s][:2] == (0, 4) for s in mapped_sources)
        assert [member['tips'].index(triples[s][2]) for s in mapped_sources] == member['row_order']
        assert len({image[s] for s in selected}) == 72
    return {'case_index': manifest['case_index'], 'tips': case['representative_tips'],
            'covered_tip_pairs': case['orbit_size'], 'parameter_a': a,
            'status': 'independent two-source partial99-matrix replay PASS',
            'result_path': str(result_path), 'result_sha256': sha(result_path),
            'manifest_sha256': sha(manifest_path), 'coverage_sha256': sha(coverage_path),
            'gram_entries_checked': 729, 'partial_pair_caps_checked': 4851,
            'partial_edges': 327, 'full_graph_completed': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    cases = [replay(ROOT/f'experiments/logs/grids-and-triangles/complement-rook-duplicate-row-{i}-result.json')
             for i in range(8)]
    assert sum(case['covered_tip_pairs'] for case in cases) == 21
    record = {'status': 'all eight two-source partial witnesses replayed independently',
              'source_sha256': sha(Path(__file__)), 'covered_tip_pairs': 21,
              'cases': cases, 'scope': 'all forced tip-pair cases survive this projection; no complete graph'}
    args.output.write_text(json.dumps(record, indent=2)+'\n')
    print(json.dumps(record, indent=2), flush=True)
