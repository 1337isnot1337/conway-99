"""Direct integer-matrix replay of saved single-source partial witnesses."""

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
    assert result['status'] == 'SAT partial witness verified exactly; no complete graph claim'
    manifest_path = ROOT/result['manifest_path']
    assert sha(manifest_path) == result['manifest_sha256']
    manifest = json.loads(manifest_path.read_text())
    for name, expected in manifest['source_hashes'].items():
        assert sha(Path(__file__).with_name(name)) == expected
    point = result['partial_witness']
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
    selected = point['selected_signature_indices']
    assert selected == sorted(set(selected)) and len(selected) == 72
    assert [list(triples[s]) for s in selected] == point['selected_signature_triples']
    source = point['source_signature_index']
    assert source == manifest['source_index'] and source in selected
    assert list(triples[source]) == manifest['source_triple'] == point['source_triple']
    neighbors = point['neighbor_signature_indices']
    assert len(neighbors) == len(set(neighbors)) == 11
    assert set(neighbors) <= set(selected)-{source}
    matches = [tuple(pair) for pair in point['matching_signature_pairs']]
    assert len(matches) == len(set(matches)) == 4
    assert len({v for edge in matches for v in edge}) == 8
    assert {v for edge in matches for v in edge} <= set(neighbors)
    index = {s: 27+i for i, s in enumerate(selected)}
    adjacency = [sum(value << j for j, value in enumerate(row)) for row in B]+[0]*72
    for s in selected:
        p, q, t = triples[s]
        for i in (p, 9+q, 18+t):
            adjacency[index[s]] |= 1 << i
            adjacency[i] |= 1 << index[s]
    for v, w in [(source, w) for w in neighbors]+matches:
        assert v != w
        adjacency[index[v]] |= 1 << index[w]
        adjacency[index[w]] |= 1 << index[v]
    degrees = [row.bit_count() for row in adjacency]
    assert degrees[:27] == [14]*27 and degrees[index[source]] == 14
    assert max(degrees) == 14
    assert all(not(adjacency[i] >> i & 1) for i in range(99))
    assert all((adjacency[i] >> j & 1) == (adjacency[j] >> i & 1)
               for i, j in combinations(range(99), 2))
    counts = {(i, j): (adjacency[i] & adjacency[j]).bit_count()+int(adjacency[i] >> j & 1)
              for i, j in combinations(range(99), 2)}
    assert max(counts.values()) <= 2
    assert all(counts[i, j] == 2 for i, j in combinations(range(27), 2))
    assert all(counts[i, index[source]] == 2 for i in range(27))
    source_neighbors = [i for i in range(99) if adjacency[index[source]] >> i & 1]
    assert len(source_neighbors) == 14
    assert all(sum(adjacency[v] >> w & 1 for w in source_neighbors) == 1 for v in source_neighbors)
    parameter_a = sum((p//3 == t//3 or p % 3 == t % 3)
                      and (q//3 == t//3 or q % 3 == t % 3)
                      for p, q, t in (triples[s] for s in selected))
    assert parameter_a == point['parameter_a']
    return {'orbit': manifest['orbit'], 'source_triple': manifest['source_triple'],
            'parameter_a': parameter_a, 'result_path': str(result_path),
            'result_sha256': sha(result_path), 'manifest_sha256': sha(manifest_path),
            'status': 'independent99-point partial-matrix and source matching replay PASS',
            'selected_columns': 72, 'partial_edges': sum(degrees)//2,
            'partial_pair_caps_checked': len(counts), 'full_graph_completed': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    cases = [replay(ROOT/f'experiments/logs/grids-and-triangles/complement-rook-row-projection-{i}-result.json')
             for i in range(3)]
    record = {'status': 'all three independent partial-witness replays PASS',
              'source_sha256': sha(Path(__file__)), 'cases': cases,
              'scope': 'all three source types survive this projection; no complete graph is supplied'}
    args.output.write_text(json.dumps(record, indent=2)+'\n')
    print(json.dumps(record, indent=2), flush=True)
