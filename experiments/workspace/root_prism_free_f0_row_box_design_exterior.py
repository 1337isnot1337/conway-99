"""Symmetric exterior models for the saved all-row-box-feasible incidence.

The first component and its sixty distinct triple columns are fixed.
The second component and its alignment/incidence remain unrestricted.
The frozen earlier exterior builder is reused only as a pure CNF
encoder on the newly reconstructed data; its old inputs are not used.
No SAT or LP discovery command is exposed by this preparation source.
"""

import argparse
from collections import Counter
import gzip
import hashlib
from itertools import combinations
import json
from pathlib import Path
import tempfile
import time

import root_prism_free_f0_incidence as incidence
import root_prism_free_f0_first_design_exterior as encoder


ROOT = incidence.ROOT
LOGS = ROOT/'experiments/logs/root-prism-free'
CANDIDATE = LOGS/'f0-incidence-row-loop-run01/iteration00/candidate.json'
CANDIDATE_SHA = '9e38e41273ad247021854236a56a4e9dd0cdc74b7156867904b7d19fe2d64e46'
ROWS = LOGS/'f0-incidence-row-loop-run01/iteration00/rows.json'
ROWS_SHA = 'dfaee7888eccfa0f673212e054e9824f4aac9256e745a282574ef758b7e79519'
COLD = LOGS/'f0-incidence-row-loop-run01-cold-replay.json'
COLD_SHA = '8640b7b338277389966a0097d4496f04dcbf4da286fccc8f3f8917d7f245453a'
ROW_DOMAIN = LOGS/'f0-exterior-row-domains02.json.gz'
ROW_DOMAIN_SHA = '665563b75fa6fc23caa9a002621cc4047809af28543b52b5c2a7ffa592d05dd4'
SOURCES = {
    'root_prism_free_f0_incidence.py': '00cd6e683a8bfb602cfd29f8dbb3481be0f87df55f2963ae98613f2af9146971',
    'root_prism_free_f0_first_design_exterior.py': 'f0c5105526b9374935b4ba961859261249f44f2b311d98138ac3c8aeb5ed56cd'}
digest, canonical, portable = incidence.digest, incidence.canonical, incidence.portable


def load_json(path):
    raw = path.read_bytes()
    return json.loads(gzip.decompress(raw) if path.suffix == '.gz' else raw)


def save(path, record):
    raw = canonical(record)+b'\n'
    path.write_bytes(gzip.compress(raw, mtime=0) if path.suffix == '.gz' else json.dumps(record, indent=2).encode()+b'\n')


def inputs(complete_replay=False):
    for name, expected in SOURCES.items():
        assert digest(Path(__file__).with_name(name)) == expected
    for path, expected in [(CANDIDATE, CANDIDATE_SHA), (ROWS, ROWS_SHA),
                           (COLD, COLD_SHA), (ROW_DOMAIN, ROW_DOMAIN_SHA)]:
        assert digest(path) == expected
    domain, conflicts = incidence.load(0, complete_replay)
    candidate = load_json(CANDIDATE)
    selected = candidate['selected_signature_ids']
    assert incidence.inspect(selected, domain, conflicts) == candidate['original_incidence_and_twelve_old_cuts']['base_incidence_witness']
    stored = load_json(ROW_DOMAIN)
    assert stored['signature_domain'] == domain['signature_domain']
    assert stored['component_core_rows'] == domain['core_rows']
    design = [domain['signature_domain'][i] for i in selected]
    masks = [sum(1 << i for i in triple) for triple in design]
    adjacency = [(row >> 3)&((1 << 18)-1) for row in domain['core_rows'][3:21]]
    assert len(masks) == len(set(masks)) == 60 and all(mask.bit_count() == 3 for mask in masks)
    assert len(adjacency) == 18 and all(row.bit_count() == 3 for row in adjacency)
    targets = [[2-int(mask >> i & 1)-(adjacency[i]&mask).bit_count() for i in range(18)] for mask in masks]
    assert targets == [stored['row_targets'][a] for a in selected]
    assert all(sum(q) == 24 and all(value in (0, 1, 2) for value in q) for q in targets)
    overlaps = [[(a&b).bit_count() for b in masks] for a in masks]
    assert all(overlaps[u][v] <= 2 for u in range(60) for v in range(u))
    edges = [(u, v) for u in range(60) for v in range(u)
             if overlaps[u][v] <= 1
             and all(targets[u][i] > 0 for i in design[v])
             and all(targets[v][i] > 0 for i in design[u])]
    reference = [(u, v) for u in range(60) for v in range(u)
                 if selected[v] in stored['possible_neighbor_signature_ids'][selected[u]]]
    assert edges == reference and len(edges) == 1220
    cold = load_json(COLD)
    assert cold['status'].endswith('PASS') and cold['exact_rational_row_boxes'] == 60
    return {'design': design, 'design_source_indices': selected,
            'component_adjacency_rows': adjacency, 'component_core_rows': domain['core_rows'],
            'masks': masks, 'targets': targets, 'overlaps': overlaps, 'edge_domain': edges,
            'Gram': domain['Gram'], 'input_incidence_inspector_passed': True}


def linear_rows(data):
    size, core_size = len(data['masks']), len(data['component_adjacency_rows'])
    incident = [[] for _ in range(size)]
    for e, (u, v) in enumerate(data['edge_domain']):
        incident[u].append((v, e))
        incident[v].append((u, e))
    rows = []
    for v in range(size):
        rows.append({'kind': 'degree', 'vertex': v, 'support': sorted(e for _, e in incident[v]), 'rhs': 8})
        for i in range(core_size):
            rows.append({'kind': 'mixed', 'vertex': v, 'core_vertex': i,
                         'support': sorted(e for w, e in incident[v] if data['masks'][w] >> i & 1),
                         'rhs': data['targets'][v][i]})
    assert len(rows) == 1140
    assert Counter(row['kind'] for row in rows) == {'degree': 60, 'mixed': 1080}
    assert sum(len(row['support']) for row in rows) == 8*len(data['edge_domain'])
    assert all(0 <= row['rhs'] <= len(row['support']) for row in rows)
    return rows


def cap_coverage(data):
    neighbor_sets = [set() for _ in range(60)]
    edges = {tuple(sorted(edge)): e for e, edge in enumerate(data['edge_domain'])}
    for u, v in data['edge_domain']:
        neighbor_sets[u].add(v)
        neighbor_sets[v].add(u)
    records = []
    for u, v in combinations(range(60), 2):
        c = data['overlaps'][u][v]
        centers = sorted(neighbor_sets[u]&neighbor_sets[v])
        direct = edges.get((u, v))
        assert u not in centers and v not in centers
        if c == 2:
            assert direct is None
        records.append({'pair': [u, v], 'first_component_common_neighbors': c,
                        'cap': 2-c, 'direct_edge_index': direct, 'path_centers': centers})
    assert len(records) == 1770
    return records


def controls():
    # Known nine-point rook graph: all mixed identities and full pair caps
    # hold after the root plus four neighbors are chosen as the core.
    adjacency = [sum(1 << j for j in range(9) if j != i and (j//3 == i//3 or j%3 == i%3)) for i in range(9)]
    core = [0, 1, 2, 3, 6]
    outside = [4, 5, 7, 8]
    mixed = 0
    for a in outside:
        for i in core:
            core_common = sum((adjacency[i] >> j & 1)*(adjacency[a] >> j & 1) for j in core)
            outer_common = sum((adjacency[i] >> b & 1)*(adjacency[a] >> b & 1) for b in outside)
            assert core_common+outer_common+(adjacency[i] >> a & 1) == 2
            mixed += 1
    for a, b in combinations(outside, 2):
        assert (adjacency[a]&adjacency[b]).bit_count()+(adjacency[a] >> b & 1) == 2
    assert all(sum(adjacency[a] >> b & 1 for b in outside) == 2 for a in outside)
    return {'nine_rook_mixed_equations': mixed, 'nine_rook_outside_pair_caps': 6,
            'nine_rook_outside_degrees': [2]*4, 'optimizer_or_solver_called': False}


def prepare(model_path, cnf_path):
    assert not model_path.exists() and not cnf_path.exists()
    started = time.monotonic()
    data = inputs()
    rows, caps = linear_rows(data), cap_coverage(data)
    cnf, formula = encoder.build(data)
    assert formula['primary_variables'] == 1220
    assert formula['constraints']['degree_rows'] == 60
    assert formula['constraints']['mixed_Gram_rows'] == 1080
    assert formula['constraints']['outside_pair_caps'] == 1770
    assert formula['constraints']['common_neighbor_variables'] == sum(len(row['path_centers']) for row in caps if row['cap'])
    assert formula['constraints']['zero_capacity_pair_clauses'] == sum(len(row['path_centers']) for row in caps if not row['cap'])
    cnf.to_file(cnf_path)
    count = len(data['edge_domain'])
    lp = {'undirected_primary_variables': count, 'equations': len(rows),
          'degree_equations': 60, 'mixed_equations': 1080,
          'primary_lower_bound': 0, 'primary_upper_bound': 1,
          'equation_nonzeros': sum(len(row['support']) for row in rows),
          'explicit_upper_slack_standard_form_rows': len(rows)+count,
          'explicit_upper_slack_standard_form_variables': 2*count,
          'explicit_upper_slack_standard_form_nonzeros': sum(len(row['support']) for row in rows)+2*count,
          'pair_caps_in_linear_relaxation': False,
          'rows_sha256': hashlib.sha256(canonical(rows)).hexdigest()}
    model = {'status': 'fixed new60 incidence; symmetric LP and complete partial-cap CNF prepared, no query',
        'source_sha256': digest(Path(__file__)), 'dependency_source_hashes': SOURCES,
        'candidate_sha256': CANDIDATE_SHA, 'row_boxes_sha256': ROWS_SHA,
        'incidence_cold_replay_sha256': COLD_SHA, 'complete_row_domain_sha256': ROW_DOMAIN_SHA,
        'data': data, 'linear_rows': rows, 'cap_coverage': caps, 'LP_inventory': lp,
        'formula': formula, 'cnf': str(cnf_path), 'cnf_sha256': digest(cnf_path),
        'cnf_bytes': cnf_path.stat().st_size, 'controls': controls(),
        'scope': 'one saved first-component0 incidence; second component and alignment/incidence free',
        'fixed_second_component_or_graph_symmetry': False,
        'all_first_incidences_or_component0_excluded': False,
        'full_graph_constructed': False, 'optimizer_or_SAT_called': False,
        'seconds': time.monotonic()-started}
    save(model_path, model)
    print(json.dumps({k: v for k, v in model.items() if k not in ('data', 'linear_rows', 'cap_coverage')}, indent=2), flush=True)


def checked_model(path, require_cnf=False):
    model = load_json(path)
    assert model['source_sha256'] == digest(Path(__file__))
    assert model['dependency_source_hashes'] == SOURCES
    for name, expected in SOURCES.items():
        assert digest(Path(__file__).with_name(name)) == expected
    assert model['candidate_sha256'] == digest(CANDIDATE) == CANDIDATE_SHA
    assert model['row_boxes_sha256'] == digest(ROWS) == ROWS_SHA
    assert model['incidence_cold_replay_sha256'] == digest(COLD) == COLD_SHA
    assert model['complete_row_domain_sha256'] == digest(ROW_DOMAIN) == ROW_DOMAIN_SHA
    if require_cnf:
        assert digest(Path(model['cnf'])) == model['cnf_sha256']
    return model


def replay(model_path, output):
    assert not output.exists()
    model = checked_model(model_path)
    data = inputs(True)
    assert json.loads(canonical(data)) == model['data']
    assert linear_rows(data) == model['linear_rows']
    assert cap_coverage(data) == model['cap_coverage']
    assert controls() == model['controls']
    cnf, formula = encoder.build(data)
    assert formula == model['formula']
    with tempfile.TemporaryDirectory(prefix='conway-f0-rowbox-exterior-') as directory:
        path = Path(directory)/'full.cnf'
        cnf.to_file(path)
        assert digest(path) == model['cnf_sha256']
    report = {'status': 'cold complete incidence domain,1220 shared edges,1140 linear rows and1770-cap CNF replay PASS',
        'source_sha256': digest(Path(__file__)), 'model_sha256': digest(model_path),
        'cnf_sha256': model['cnf_sha256'], 'primary_edges': 1220,
        'formula': formula, 'LP_inventory': model['LP_inventory'],
        'optimizer_or_solver_called': False, 'full_graph_constructed': False}
    save(output, report)
    print(json.dumps(report, indent=2), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    prep = commands.add_parser('prepare')
    prep.add_argument('--model', type=Path, required=True)
    prep.add_argument('--cnf', type=Path, required=True)
    check = commands.add_parser('replay')
    check.add_argument('--model', type=Path, required=True)
    check.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.command == 'prepare':
        prepare(args.model.resolve(), args.cnf.resolve())
    else:
        replay(args.model.resolve(), args.output.resolve())
