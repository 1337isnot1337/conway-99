"""Complete exterior-row eligibility for component zero, before incidence selection.

This records all 480 possible first-component triples and every possible
edge between two such signatures. Verified core relabelings partition the
480 row problems into orbits. No incidence or exterior solver is called.
"""

import argparse
from collections import Counter
import gzip
import hashlib
from itertools import combinations
import json
from pathlib import Path
import time

import pynauty

import root_prism_free_f0_coupling as coupling


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def build():
    started = time.monotonic()
    _, domain, saved_selection, conflicts = coupling.load()
    triples = domain['signature_domain']
    assert len(triples) == 480
    core = domain['core_rows']
    adjacency = [(row >> 3) & ((1 << 18)-1) for row in core[3:21]]
    masks = [sum(1 << i for i in triple) for triple in triples]
    targets = [[2-int(mask >> i & 1)-(adjacency[i] & mask).bit_count()
                for i in range(18)] for mask in masks]
    assert all(sum(row) == 24 and all(q in (0, 1, 2) for q in row) for row in targets)
    neighbors = [[] for _ in triples]
    for a, b in combinations(range(480), 2):
        if (masks[a] & masks[b]).bit_count() >= 2:
            continue
        if not all(targets[a][i] > 0 for i in triples[b]):
            continue
        if not all(targets[b][i] > 0 for i in triples[a]):
            continue
        neighbors[a].append(b)
        neighbors[b].append(a)
    motif_pairs = {tuple(sorted(item['columns'])) for name in ('F_conflicts', 'prism_conflicts')
                   for item in conflicts[name]}
    assert len(motif_pairs) == 90
    graph = pynauty.Graph(21, directed=False,
        adjacency_dict={i: [j for j in range(21) if core[i] >> j & 1] for i in range(21)},
        vertex_coloring=[set(range(3)), set(range(3, 21))])
    generators = pynauty.autgrp(graph)[0]
    position = {tuple(triple): i for i, triple in enumerate(triples)}
    actions = []
    for generator in generators:
        assert sorted(generator) == list(range(21)) and set(generator[:3]) == set(range(3))
        assert all(((core[i] >> j) & 1) == ((core[generator[i]] >> generator[j]) & 1)
                   for i in range(21) for j in range(21))
        move = [generator[3+i]-3 for i in range(18)]
        action = [position[tuple(sorted(move[i] for i in triple))] for triple in triples]
        assert sorted(action) == list(range(480))
        assert {tuple(sorted((action[a], action[b]))) for a, b in motif_pairs} == motif_pairs
        for a in range(480):
            assert sorted(action[b] for b in neighbors[a]) == neighbors[action[a]]
            assert all(targets[a][i] == targets[action[a]][move[i]] for i in range(18))
        actions.append(action)
    unseen, orbits = set(range(480)), []
    while unseen:
        start = min(unseen)
        orbit, frontier = {start}, [start]
        while frontier:
            a = frontier.pop()
            for action in actions:
                b = action[a]
                if b not in orbit:
                    orbit.add(b)
                    frontier.append(b)
        assert orbit <= unseen
        unseen -= orbit
        orbits.append(sorted(orbit))
    assert sorted(a for orbit in orbits for a in orbit) == list(range(480))
    selected = set(saved_selection)
    fixed_edges = [(a, b) for a in sorted(selected) for b in neighbors[a] if b in selected and b < a]
    assert len(fixed_edges) == 1224
    return {'status': 'complete component-zero exterior-row domain preparation',
            'source_sha256': digest(__file__), 'coupling_source_sha256': digest(coupling.__file__),
            'fixed_incidence_result_sha256': digest(coupling.RESULT),
            'component_core_rows': core, 'component_adjacency_rows': adjacency,
            'signature_domain': triples, 'row_targets': targets,
            'possible_neighbor_signature_ids': neighbors,
            'complete_signature_count': len(triples),
            'complete_possible_edge_count': sum(map(len, neighbors))//2,
            'possible_degree_histogram': dict(sorted(Counter(map(len, neighbors)).items())),
            'core_generators': generators, 'signature_generator_actions': actions,
            'verified_subgroup_orbits': orbits, 'orbit_count': len(orbits),
            'orbit_size_histogram': dict(sorted(Counter(map(len, orbits)).items())),
            'motif_pairs': sorted(motif_pairs),
            'motif_pairs_are_not_removed_from_edge_domain': True,
            'all_generators_preserve_core_targets_domains_and_motifs': True,
            'reproduced_saved_design_possible_edges': len(fixed_edges),
            'hypothetical_graph_symmetry_assumed': False, 'solver_called': False,
            'signature_or_core_exclusion_claimed': False,
            'seconds': time.monotonic()-started}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--replay', type=Path)
    args = parser.parse_args()
    assert not args.output.exists()
    result = build()
    if args.replay:
        old = json.loads(gzip.decompress(args.replay.read_bytes()))
        comparable = json.loads(json.dumps({k: v for k, v in result.items() if k != 'seconds'}))
        assert comparable == {k: v for k, v in old.items() if k != 'seconds'}
    content = json.dumps(result, separators=(',', ':')).encode()+b'\n'
    args.output.write_bytes(gzip.compress(content, compresslevel=9, mtime=0))
    print(json.dumps({k: v for k, v in result.items() if k not in (
        'component_core_rows', 'component_adjacency_rows', 'signature_domain', 'row_targets',
        'possible_neighbor_signature_ids', 'core_generators', 'signature_generator_actions',
        'verified_subgroup_orbits', 'motif_pairs')}, indent=2), flush=True)
    print('output_sha256', digest(args.output), flush=True)
