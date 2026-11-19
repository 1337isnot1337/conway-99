"""Complete rooted induced high-graph patterns with at most four free vertices.

The root is an ordered independent six-set. Each free vertex has a distinct
root-neighborhood mask of size at least three. The root permutation action
does not assume an automorphism of the unknown host graph.
"""

import argparse
import hashlib
from itertools import combinations, permutations
import json
from pathlib import Path
import time

import grid_free_order10_high_mask_graph_audit as literal


ROOT = Path(__file__).resolve().parents[2]
LOGS = ROOT / 'experiments/logs/moments-and-counts'
SCOPE = LOGS / 'order10-high-mask-graph-scope.json'
RAW = LOGS / 'order10-high-mask-graph-count01-raw.json'
AUDIT = LOGS / 'order10-high-mask-graph-count01-independent-audit.json'
SCOPE_SHA = '9733b52563e5b1937937b196ad9edeb738c141c2ca8041c27e501ca3f5cc2c94'
RAW_SHA = '05b8ef3b139995ae0fbbce24f9da3e75de7a2278cb719a2dfe4e5062a385a10d'
AUDIT_SHA = '8d8139a148fe12678561433766f3aa70f260266c196f7671b727d41ea856d673'
LITERAL_SOURCE_SHA = '6b7b128d504521b0b8a22d1c203590bbb71f6b6bc2228e59f172700b68d6c546'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def move_mask(mask, permutation):
    return sum(((mask >> i) & 1) << permutation[i] for i in range(6))


def move_graph(code, vertex_map):
    pairs = list(combinations(range(len(vertex_map)), 2))
    index = {pair: i for i, pair in enumerate(pairs)}
    return sum(1 << index[tuple(sorted((vertex_map[a], vertex_map[b])))]
               for bit, (a, b) in enumerate(pairs) if code >> bit & 1)


def adjacency(masks, code):
    rows = [0] * (6+len(masks))
    for a, mask in enumerate(masks):
        rows[6+a] = mask
        for i in range(6):
            if mask >> i & 1:
                rows[i] |= 1 << (6+a)
    for bit, (a, b) in enumerate(combinations(range(len(masks)), 2)):
        if code >> bit & 1:
            rows[6+a] |= 1 << (6+b)
            rows[6+b] |= 1 << (6+a)
    return rows


def prepare(output):
    assert not output.exists()
    started = time.monotonic()
    assert sha(SCOPE) == SCOPE_SHA and sha(RAW) == RAW_SHA and sha(AUDIT) == AUDIT_SHA
    assert sha(Path(literal.__file__)) == LITERAL_SOURCE_SHA
    scope, raw, audit = (json.loads(p.read_text()) for p in (SCOPE, RAW, AUDIT))
    assert audit['complete'] and audit['all_edge_histograms_equal'] and raw['complete']
    root_maps = list(permutations(range(6)))
    mask_maps = [[move_mask(mask, p) for mask in range(64)] for p in root_maps]
    rows, tables = [], []
    labelled_decorations = 0
    for atom in scope['representatives']:
        masks = atom['selected_high_masks']
        q = len(masks)
        if q > 4:
            continue
        index = {mask: i for i, mask in enumerate(masks)}
        stabilizers = []
        for p, image in zip(root_maps, mask_maps):
            moved = [image[mask] for mask in masks]
            if sorted(moved) == masks:
                stabilizers.append((p, [index[mask] for mask in moved]))
        assert len(stabilizers) * atom['atom_orbit_size'] == 720
        graph_count = 1 << (q*(q-1)//2)
        valid = [code for code in range(graph_count) if literal.valid(adjacency(masks, code))]
        expected = raw['records'][atom['atom_orbit']]
        assert len(valid) == expected['graphs']
        labelled_decorations += len(valid)
        unseen = set(valid)
        mapping = [-1] * graph_count
        while unseen:
            code = min(unseen)
            images = {move_graph(code, p) for _, p in stabilizers}
            assert images <= unseen and code == min(images)
            graph_stabilizer = sum(move_graph(code, p) == code for _, p in stabilizers)
            assert graph_stabilizer * len(images) == len(stabilizers)
            orbit_size = atom['atom_orbit_size'] * len(images)
            assert orbit_size * graph_stabilizer == 720
            row = len(rows)
            for member in images:
                mapping[member] = row
            rows.append({'row': row, 'presence_atom_orbit': atom['atom_orbit'],
                         'free_vertices': q, 'high_class_code': atom['high_class_code'],
                         'high_masks': masks, 'canonical_free_graph_code': code,
                         'free_pair_order': [list(pair) for pair in combinations(range(q), 2)],
                         'core_plus_free_adjacency_rows': adjacency(masks, code),
                         'root_label_orbit_size': orbit_size,
                         'root_stabilizer_size': graph_stabilizer,
                         'free_graph_orbit_size_under_atom_stabilizer': len(images),
                         'graph_codes_in_atom_stabilizer_orbit': sorted(images)})
            unseen -= images
        assert sum(value >= 0 for value in mapping) == len(valid)
        tables.append({'presence_atom_orbit': atom['atom_orbit'], 'high_masks': masks,
                       'root_atom_stabilizer_size': len(stabilizers),
                       'root_atom_orbit_size': atom['atom_orbit_size'],
                       'free_graph_code_to_row': mapping})
    assert len(tables) == 73 and labelled_decorations == 279
    report = {'status': 'complete induced high-graph row patterns and root-label orbits; no moments or optimizer',
              'complete': True, 'source_sha256': sha(Path(__file__)),
              'scope_sha256': SCOPE_SHA, 'graph_count_sha256': RAW_SHA,
              'independent_graph_count_sha256': AUDIT_SHA,
              'literal_adjacency_source_sha256': LITERAL_SOURCE_SHA,
              'root_vertices': 6, 'root_adjacency_rows': [0]*6,
              'root_group_order': 720, 'root_permutations': [list(p) for p in root_maps],
              'presence_orbits_through_degree4': len(tables),
              'decorations_before_atom_stabilizer_quotient': labelled_decorations,
              'induced_pattern_row_orbits': len(rows), 'rows': rows, 'lookup_tables': tables,
              'fixed_pattern_moment': 'Aut(unrooted core-plus-free graph) times its induced count',
              'quotient_row_rhs': 'root-label orbit size times the fixed-pattern moment',
              'free_vertices_have_distinct_high_masks': True,
              'host_graph_automorphism_assumed': False,
              'new_moments_or_product_tensors_built': False,
              'optimizer_or_solver_called': False, 'graph_existence_resolved': False,
              'seconds': time.monotonic()-started}
    output.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({key: value for key, value in report.items()
                      if key not in ('rows', 'lookup_tables', 'root_permutations')}, indent=2))
    print('result_sha256', sha(output))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    prepare(parser.parse_args().output)
