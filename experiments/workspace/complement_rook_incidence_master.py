"""Bounded incidence-master pilot with independently certified signed cuts.

The conditional oracle is the unchanged full complementary-rook necessary
model. A reusable proof-free oracle receives all252 selector truth values.
No signed-core cut enters the master before a fresh explicit-unit proof
and an independent DRAT check. Partial-SAT visitation blocks are separate.
"""

import argparse
import gc
import hashlib
from itertools import combinations
import json
from pathlib import Path
import resource
import subprocess
from threading import Timer
import time

from pysat.card import CardEnc, EncType
from pysat.formula import CNF, IDPool
from pysat.solvers import Solver

import complement_rook_a_incidence as incidence
from complement_rook_joint_split import ROOT, check_base, digest
from two_rook_iso_joint_integer import inspect_point


def relative(path):
    return str(path.resolve().relative_to(ROOT))


def master_formula():
    rows, gram, triples, signatures, counted, equations = incidence.domain()
    cnf, pool = CNF(), IDPool(start_from=253)
    for members, quota in equations:
        cnf.extend(CardEnc.equals([s+1 for s in members], quota, vpool=pool,
                                 encoding=EncType.seqcounter).clauses)
    assert len(equations) == 180
    record = {'core_rows': rows, 'gram': gram, 'triples': triples, 'signatures': signatures,
              'counted_a_signatures': counted, 'margin_equations': equations}
    domain_hash = hashlib.sha256(json.dumps(record, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    return cnf, domain_hash


def prepare(base_path, controls_path, master_path, output):
    base, _, _, _, _, _, _ = check_base(base_path)
    controls = json.loads(controls_path.read_text())
    assert controls['verified_signed_core_cuts'] == 2 and controls['exact_partial_SAT_controls'] == 4
    assert controls['source_sha256'] == digest(Path(__file__).with_name('complement_rook_incidence_master_controls.py'))
    master, master_domain = master_formula()
    master.to_file(master_path)
    record = {'status': 'baseline incidence-master pilot prepared; no large oracle run',
              'base_manifest': relative(base_path), 'base_manifest_sha256': digest(base_path),
              'base_cnf_sha256': base['cnf_sha256'], 'base_domain_sha256': base['domain_sha256'],
              'master_cnf_path': str(master_path), 'master_cnf_sha256': digest(master_path),
              'master_domain_sha256': master_domain, 'master_variables': master.nv,
              'master_clauses': len(master.clauses), 'master_gram_margins': 180,
              'joint_variables': base['variables'], 'joint_clauses': base['clauses'],
              'signature_selectors': 252, 'eligible_edge_variables': 20934,
              'maximum_designs': 8, 'oracle_seconds': 10, 'master_seconds': 10,
              'fresh_proof_seconds_including_materialization_and_bootstrap': 30,
              'DRAT_seconds': 30, 'oracle_proof_logging': False,
              'source_hashes': {name: digest(Path(__file__).with_name(name)) for name in
                                ('complement_rook_incidence_master.py', 'complement_rook_incidence_master_certificate.py',
                                 'complement_rook_joint_split.py',
                                 'complement_rook_a_incidence.py', 'two_rook_iso_joint_integer.py')},
              'controls_certificate': relative(controls_path), 'controls_certificate_sha256': digest(controls_path),
              'extra_a_bound_added': False, 'Schur_clauses_added': 0, 'full_outside_caps_imposed': False,
              'oracle_graph_constraints_added': 0, 'graph_symmetry_assumptions': 0,
              'scope': 'fixed-design probes of the unchanged necessary joint model'}
    output.write_text(json.dumps(record, indent=2)+'\n')
    print(json.dumps(record, indent=2), flush=True)
    return record


def check_model(path, require_base_cnf=True):
    record = json.loads(path.read_text())
    for name, expected in record['source_hashes'].items():
        assert digest(Path(__file__).with_name(name)) == expected
    base_path = ROOT/record['base_manifest']
    assert digest(base_path) == record['base_manifest_sha256']
    base, rows, gram, triples, signatures, needs, variables = check_base(base_path, require_base_cnf)
    assert base['cnf_sha256'] == record['base_cnf_sha256']
    assert base['domain_sha256'] == record['base_domain_sha256']
    master, master_domain = master_formula()
    # CNF serialization is simple and deterministic; no temporary file is
    # required to revalidate this small formula when the cache is absent.
    data = f'p cnf {master.nv} {len(master.clauses)}\n'+''.join(' '.join(map(str, clause))+' 0\n'
                                                            for clause in master.clauses)
    assert hashlib.sha256(data.encode()).hexdigest() == record['master_cnf_sha256']
    assert master_domain == record['master_domain_sha256']
    assert (master.nv, len(master.clauses)) == (record['master_variables'], record['master_clauses'])
    assert record['maximum_designs'] == 8 and record['oracle_seconds'] == record['master_seconds'] == 10
    assert record['fresh_proof_seconds_including_materialization_and_bootstrap'] == record['DRAT_seconds'] == 30
    assert not record['extra_a_bound_added'] and not record['full_outside_caps_imposed']
    assert record['Schur_clauses_added'] == record['oracle_graph_constraints_added'] == record['graph_symmetry_assumptions'] == 0
    assert digest(ROOT/record['controls_certificate']) == record['controls_certificate_sha256']
    return record, base, master, rows, gram, triples, signatures, variables


def full_assumptions(selected):
    assert selected == sorted(set(selected)) and len(selected) == 72
    chosen = set(selected)
    assert min(chosen) >= 0 and max(chosen) < 252
    assumptions = [s+1 if s in chosen else -(s+1) for s in range(252)]
    assert len(assumptions) == 252 and len({abs(lit) for lit in assumptions}) == 252
    return assumptions


def bounded(solver, seconds, assumptions=()):
    if seconds <= 0:
        return None
    solver.clear_interrupt()
    timer = Timer(seconds, solver.interrupt)
    timer.start()
    try:
        return solver.solve_limited(assumptions=list(assumptions), expect_interrupt=True)
    finally:
        timer.cancel()


def materialize_units(base_path, variables, clauses, units, output):
    assert len(units) == len(set(units)) and not any(-lit in units for lit in units)
    assert all(1 <= abs(lit) <= 252 for lit in units)
    with base_path.open('rb') as source, output.open('wb') as target:
        assert source.readline() == f'p cnf {variables} {clauses}\n'.encode()
        target.write(f'p cnf {variables} {clauses+len(units)}\n'.encode())
        for block in iter(lambda: source.read(1024*1024), b''):
            target.write(block)
        for unit in units:
            target.write(f'{unit} 0\n'.encode())


def clauses(path):
    current = []
    with path.open() as source:
        for line in source:
            if not line.strip() or line.lstrip().startswith(('c', 'p')):
                continue
            for token in line.split():
                value = int(token)
                if value:
                    current.append(value)
                else:
                    yield tuple(current)
                    current = []
    assert not current


def certify_core(manifest_path, model, base, selected, core, index, directory, checker):
    assert set(core) <= set(full_assumptions(selected))
    assert core == sorted(set(core), key=abs)
    prefix = directory/f'design-{index}-core'
    temporary = Path(f'/tmp/conway-complement-rook-master-design-{index}-core')
    formula, raw = temporary.with_suffix('.cnf'), temporary.with_suffix('.drat')
    record = {'status': 'fresh core proof pending', 'design_index': index,
              'manifest': relative(manifest_path), 'manifest_sha256': digest(manifest_path),
              'selected_signatures': selected, 'core_units': core,
              'learned_selector_clause': [-lit for lit in core],
              'base_cnf_sha256': base['cnf_sha256'], 'base_domain_sha256': base['domain_sha256'],
              'formula_path': str(formula), 'raw_proof_path': str(raw),
              'source_sha256': digest(Path(__file__)),
              'certificate_wrapper_sha256': digest(Path(__file__).with_name('complement_rook_incidence_master_certificate.py')),
              'certificate_creation_precedes_master_cut': True}
    started = time.monotonic()
    materialize_units(ROOT/base['cnf_path'], base['variables'], base['clauses'], core, formula)
    record['core_unit_cnf_sha256'] = digest(formula)
    cnf = CNF(from_file=str(formula))
    assert (cnf.nv, len(cnf.clauses)) == (base['variables'], base['clauses']+len(core))
    with Solver(name='glucose4', bootstrap_with=cnf.clauses, with_proof=True) as proof_solver:
        del cnf
        gc.collect()
        answer = bounded(proof_solver, 30-(time.monotonic()-started))
        record['fresh_proof_seconds'] = time.monotonic()-started
        record['fresh_proof_statistics'] = proof_solver.accum_stats()
        if answer is None:
            record['status'] = 'UNKNOWN in fresh core proof; no cut certified'
            return record
        assert answer is False, 'A reported UNSAT assumption core was SAT in the fresh explicit-unit model.'
        proof = proof_solver.get_proof()
        assert proof and proof[-1] == '0'
        raw.write_text('\n'.join(proof)+'\n')
    record['raw_proof_sha256'] = digest(raw)
    record['raw_proof_lines'] = len(proof)
    del proof
    retained_cnf = prefix.with_name(prefix.name+'-retained.cnf')
    retained_proof = prefix.with_name(prefix.name+'-retained.drat')
    drat_log = prefix.with_name(prefix.name+'-drat.log')
    print(json.dumps({'design': index, 'phase': 'fresh core UNSAT; checking DRAT',
                      'core_literals': len(core), 'proof_seconds': record['fresh_proof_seconds']}), flush=True)
    checked = subprocess.run([str(checker), str(formula), str(raw), '-t', '30', '-w',
                              '-c', str(retained_cnf), '-l', str(retained_proof)],
                             text=True, capture_output=True, timeout=35, check=False)
    drat_log.write_text(checked.stdout+checked.stderr)
    assert checked.returncode == 0 and 's VERIFIED' in checked.stdout, (checked.returncode, checked.stdout, checked.stderr)
    retained = list(clauses(retained_cnf))
    needed = {tuple(sorted(clause)) for clause in retained}
    for clause in clauses(formula):
        needed.discard(tuple(sorted(clause)))
    assert not needed
    record.update(status='explicit-core-unit proof DRAT verified; cut certified',
                  retained_cnf=relative(retained_cnf), retained_cnf_sha256=digest(retained_cnf),
                  retained_proof=relative(retained_proof), retained_proof_sha256=digest(retained_proof),
                  retained_input_clauses=len(retained), retained_proof_lines=sum(1 for _ in retained_proof.open()),
                  checker_sha256=digest(checker), drat_log=relative(drat_log),
                  full_base_rebuild_replay_pending=True)
    certificate_path = prefix.with_name(prefix.name+'-certificate.json')
    certificate_path.write_text(json.dumps(record, indent=2)+'\n')
    record['certificate_path'] = relative(certificate_path)
    record['certificate_sha256'] = digest(certificate_path)
    return record


def run(manifest_path, directory, output, checker):
    model, base, master_cnf, rows, gram, triples, signatures, variables = check_model(manifest_path)
    directory.mkdir(parents=True, exist_ok=True)
    result = {'status': 'running', 'manifest': relative(manifest_path), 'manifest_sha256': digest(manifest_path),
              'scope': 'baseline master plus certified signed cuts and separately marked partial-SAT visitation blocks',
              'maximum_designs': 8, 'oracle_seconds': 10, 'designs': [], 'certified_cuts': [],
              'partial_SAT_visitation_blocks': [], 'extra_a_bound_added': False,
              'Schur_clauses_added': 0, 'full_outside_caps_imposed': False,
              'whole_core_exclusion_established': False, 'completed_graph': None}
    def save():
        result['peak_process_rss_kib'] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        output.write_text(json.dumps(result, indent=2)+'\n')
    save()
    started = time.monotonic()
    try:
        joint = CNF(from_file=str(ROOT/base['cnf_path']))
        assert (joint.nv, len(joint.clauses)) == (base['variables'], base['clauses'])
        with Solver(name='glucose4', bootstrap_with=master_cnf.clauses) as master, Solver(
                name='glucose4', bootstrap_with=joint.clauses) as oracle:
            del joint, master_cnf
            gc.collect()
            result['oracle_bootstrap_seconds'] = time.monotonic()-started
            print(json.dumps({'phase': 'reusable proof-free oracle ready',
                              'bootstrap_seconds': result['oracle_bootstrap_seconds']}), flush=True)
            for index in range(8):
                master_started = time.monotonic()
                master_answer = bounded(master, 10)
                if master_answer is None:
                    result['status'] = 'UNKNOWN in master; pilot stopped'
                    break
                if master_answer is False:
                    result['status'] = ('master exhausted with exploratory visitation blocks; no class exclusion'
                                        if result['partial_SAT_visitation_blocks'] else
                                        'master reports exhaustion with certified cuts; separate master proof required')
                    break
                selected = sorted(v-1 for v in master.get_model() if 1 <= v <= 252)
                assert selected not in [item['selected_signatures'] for item in result['designs']]
                actual_a = sum(incidence.rook(triples[s][0], triples[s][2]) and
                               incidence.rook(triples[s][1], triples[s][2]) for s in selected)
                witness = incidence.check_witness(selected, actual_a)
                assumptions = full_assumptions(selected)
                item = {'index': index, 'selected_signatures': selected, 'a': actual_a,
                        'design_already_excluded_by_a_le_2': actual_a <= 2,
                        'full_signed_assumptions': assumptions, 'full_Gram_entries_checked': witness['full_gram_entries_checked'],
                        'master_seconds': time.monotonic()-master_started, 'status': 'oracle running',
                        'certified_cut': None, 'exploratory_visitation_block': None}
                result['designs'].append(item)
                save()
                print(json.dumps({'design': index, 'a': actual_a, 'already_excluded_a_le_2': actual_a <= 2,
                                  'phase': 'oracle assumptions solve'}), flush=True)
                oracle_started = time.monotonic()
                answer = bounded(oracle, 10, assumptions)
                item['oracle_seconds'] = time.monotonic()-oracle_started
                item['oracle_cumulative_statistics'] = oracle.accum_stats()
                if answer is None:
                    item['status'] = 'UNKNOWN; no witness or exclusion'
                    result['status'] = 'UNKNOWN in conditional oracle; pilot stopped'
                    save()
                    break
                if answer:
                    positive = {v for v in oracle.get_model() if v > 0}
                    assert all((literal > 0) == (abs(literal) in positive) for literal in assumptions)
                    point, defects = inspect_point(positive, list(range(1, 253)), variables, rows, signatures)
                    assert point['selected_signatures'] == selected
                    assert all(len(set(signatures[cut['pair'][0]]) & set(signatures[cut['pair'][1]])) < 2
                               for cut in defects), 'The model violated encoded core-pair packing.'
                    item['binary_point'] = point
                    item['cap_violation_witnesses'] = defects
                    if point['defective_pairs'] == 0:
                        item['status'] = 'exact99-vertex SRG candidate; independent verification required'
                        result['status'] = 'complete graph candidate; pilot stopped'
                        result['completed_graph'] = point
                        save()
                        break
                    item['status'] = 'SAT of necessary model with explicit exterior defects'
                    block = [-(s+1) for s in selected]
                    master.add_clause(block)
                    item['exploratory_visitation_block'] = block
                    result['partial_SAT_visitation_blocks'].append({'design_index': index, 'clause': block,
                                                                  'is_theorem': False})
                else:
                    raw_core = oracle.get_core()
                    assert raw_core is not None and set(raw_core) <= set(assumptions)
                    core = sorted(set(raw_core), key=abs)
                    item['raw_assumption_core'] = raw_core
                    item['status'] = 'oracle UNSAT; explicit-core-unit proof pending'
                    save()
                    print(json.dumps({'design': index, 'phase': 'fresh explicit-core proof', 'core_literals': len(core)}), flush=True)
                    certificate = certify_core(manifest_path, model, base, selected, core, index, directory, checker)
                    item['core_certificate'] = certificate
                    if certificate['status'].startswith('UNKNOWN'):
                        item['status'] = certificate['status']
                        result['status'] = 'UNKNOWN in fresh proof stage; pilot stopped without adding this cut'
                        save()
                        break
                    assert certificate['status'] == 'explicit-core-unit proof DRAT verified; cut certified'
                    cut = certificate['learned_selector_clause']
                    master.add_clause(cut)
                    item['certified_cut'] = cut
                    item['status'] = 'UNSAT pattern certified; signed cut added to master'
                    result['certified_cuts'].append({'design_index': index, 'clause': cut,
                                                    'certificate_path': certificate['certificate_path'],
                                                    'certificate_sha256': certificate['certificate_sha256']})
                    if not core:
                        result['status'] = 'base oracle UNSAT certified; full rebuild review required'
                        save()
                        break
                save()
                print(json.dumps({'design': index, 'status': item['status'], 'a': actual_a,
                                  'oracle_seconds': item['oracle_seconds'],
                                  'defective_pairs': item.get('binary_point', {}).get('defective_pairs'),
                                  'certified_core_size': len(item.get('raw_assumption_core', []))}), flush=True)
            else:
                result['status'] = 'eight-design pilot limit; no exhaustion or class exclusion'
            result['master_final_statistics'] = master.accum_stats()
            result['oracle_final_statistics'] = oracle.accum_stats()
    except Exception as error:
        result['status'] = 'error; pilot stopped without further cuts'
        result['error_type'] = type(error).__name__
        result['error_message'] = str(error)
        save()
        raise
    result['total_seconds'] = time.monotonic()-started
    save()
    print(json.dumps({key: value for key, value in result.items() if key not in
                      ('designs', 'certified_cuts', 'partial_SAT_visitation_blocks', 'completed_graph')}, indent=2), flush=True)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    preparation = sub.add_parser('prepare')
    for name in ('base-manifest', 'controls', 'master-cnf', 'output'):
        preparation.add_argument('--'+name, type=Path, required=True)
    runner = sub.add_parser('run')
    for name in ('manifest', 'directory', 'output', 'drat-trim'):
        runner.add_argument('--'+name, type=Path, required=True)
    args = parser.parse_args()
    if args.command == 'prepare':
        prepare(args.base_manifest, args.controls, args.master_cnf, args.output)
    else:
        run(args.manifest, args.directory, args.output, args.drat_trim)
