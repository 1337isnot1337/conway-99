"""Reconstruct negative r6s2 products with the independent literal oracle.

Preparation reports the exact supported entry count and evaluates the
saved induced inequalities at a second exact count point. Reconstruction
uses no child tables or producer transports. The saved tensor is only a
comparison target; every quadratic coefficient is accumulated afresh.
"""

import argparse
from collections import Counter
from functools import reduce
import gzip
import json
from math import gcd
from pathlib import Path
import pickle
import resource
import signal
import time

import grid_free_order10_r6s2_independent_audit as oracle


ORACLE_SHA = '46bbbf5521383fc14925644e1dcb82ebeca99094b5726b8f23e3d774aa6f643f'
SCANNER_SHA = 'ca16071dd21b7d0eed9e41d7bd08678cf5ea7b7863b8cac98a2969d230d088bd'


def save(path, record):
    temporary = path.with_name(path.name+'.pending')
    temporary.write_text(json.dumps(record, indent=2)+'\n')
    temporary.replace(path)


def prepare(certificate, second_witness, output):
    saved = json.loads(certificate.read_text())
    assert saved['source_sha256'] == SCANNER_SHA
    assert oracle.digest(Path(__file__).with_name('grid_free_order10_r6s2_scan.py')) == SCANNER_SHA
    assert oracle.digest(Path(oracle.__file__)) == ORACLE_SHA
    assert saved['complete_selected_subfamily_scan'] and not saved['timed_out']
    assert saved['exact_negative_blocks'] == saved['unique_induced_count_cut_count'] == 18
    point = json.loads(second_witness.read_text())
    assert point['exact_count_and_25_cut_witness']
    assert point['original_equations_checked'] == 180445
    assert point['negative_induced_rows'] == point['nonintegral_induced_rows'] == 0
    induced = point['induced_counts']
    records = []
    for block in saved['negative_blocks']:
        support = [i for i, value in enumerate(block['integer_vector']) if value]
        records.append({'root_type': block['root_type'], 'full_flags': block['flag_count'],
                        'supported_flags': len(support),
                        'supported_lower_entries': len(support)*(len(support)+1)//2})
    face_values = [sum(coefficient*induced[index] for index, coefficient in cut['terms'])
                   for cut in saved['unique_induced_count_cuts']]
    result = {'status': 'fresh-product replay sized; no reconstruction started',
              'source_sha256': oracle.digest(Path(__file__)), 'oracle_source_sha256': ORACLE_SHA,
              'certificate_path': str(certificate), 'certificate_sha256': oracle.digest(certificate),
              'second_witness_path': str(second_witness), 'second_witness_sha256': oracle.digest(second_witness),
              'second_witness_x521': point['rounded_core_values'][521],
              'second_witness_exact_cut_values': face_values,
              'second_witness_negative_cuts': sum(value < 0 for value in face_values),
              'second_witness_scope': 'evaluation of fixed necessary forms at one exact count point; not a face exclusion',
              'negative_blocks': records,
              'supported_lower_entries': sum(record['supported_lower_entries'] for record in records),
              'maximum_supported_flag_count': max(record['supported_flags'] for record in records),
              'maximum_literal_completions_per_entry': 26,
              'proposed_reconstruction_seconds': 300,
              'dense_reduction_loaded': False, 'optimizer_called': False,
              'fresh_reconstruction_started': False}
    save(output, result)
    print(json.dumps(result, indent=2), flush=True)
    return result


def run(preparation, output, seconds=300):
    assert 0 < seconds <= 300 and not output.exists()
    prepared = json.loads(preparation.read_text())
    assert prepared['source_sha256'] == oracle.digest(Path(__file__))
    assert oracle.digest(Path(oracle.__file__)) == prepared['oracle_source_sha256'] == ORACLE_SHA
    certificate = Path(prepared['certificate_path'])
    assert oracle.digest(certificate) == prepared['certificate_sha256']
    saved = json.loads(certificate.read_text())
    assert saved['source_sha256'] == SCANNER_SHA
    catalogue = Path(saved['catalogue_path'])
    witness = Path(saved['witness_path'])
    cached = Path(saved['generated_cache_path'])
    for path, key in ((catalogue, 'catalogue_sha256'), (witness, 'witness_sha256'),
                      (cached, 'generated_cache_sha256')):
        assert oracle.digest(path) == saved[key]
    with catalogue.open('rb') as stream:
        data = pickle.load(stream)
    point = json.loads(witness.read_text())
    induced = point['induced_counts']
    payload = pickle.loads(gzip.decompress(cached.read_bytes()))
    assert payload['source_sha256'] == SCANNER_SHA
    blocks = {root: (flags, tensor) for root, flags, tensor in payload['blocks']}
    result = {'status': 'running bounded independent product reconstruction',
              'source_sha256': prepared['source_sha256'], 'preparation_sha256': oracle.digest(preparation),
              'oracle_source_sha256': ORACLE_SHA, 'certificate_sha256': prepared['certificate_sha256'],
              'catalogue_sha256': saved['catalogue_sha256'], 'witness_sha256': saved['witness_sha256'],
              'generated_cache_sha256': saved['generated_cache_sha256'],
              'maximum_seconds': seconds, 'required_blocks': len(saved['negative_blocks']),
              'required_supported_entries': prepared['supported_lower_entries'], 'completed_blocks': [],
              'producer_builder_called': False, 'producer_overlap_enumerator_called': False,
              'producer_transports_called': False, 'fresh_coefficients_from_literal_prescriptions': True,
              'saved_tensor_used_only_for_comparison': True,
              'numerical_eigensystems_recomputed': False, 'dense_reduction_loaded': False,
              'optimizer_called': False}
    save(output, result)
    started = time.monotonic()
    timed_out = False
    attempted = 0

    def deadline(_signum, _frame):
        raise TimeoutError('bounded fresh r6s2 product reconstruction')

    previous = signal.signal(signal.SIGALRM, deadline)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        ids = {oracle.canonical(tuple(rows)): i for i, rows in enumerate(data[0])}
        assert len(ids) == 48965
        for block in saved['negative_blocks']:
            block_started = time.monotonic()
            root = block['root_type']
            flags, tensor = blocks[root]
            r = len(data[0][root])
            assert r == 6 and len(flags) == block['flag_count']
            vector = block['integer_vector']
            support = [i for i, value in enumerate(vector) if value]
            for i in support:
                flag = flags[i]
                graph = oracle.add_free(data[0][root], tuple(flag['masks']), flag['edge'])
                assert graph == tuple(flag['rows']) and oracle.valid(graph)
                assert all(row.bit_count() >= 3 for row in graph[r:])
            weights = Counter()
            checked = 0
            for i in support:
                for j in support:
                    if j > i:
                        continue
                    expected, _ = oracle.direct_product(r, tuple(flags[i]['rows']), tuple(flags[j]['rows']), ids)
                    position = i*(i+1)//2+j
                    stored = {int(tensor.indices[k]): int(tensor.data[k])
                              for k in range(tensor.indptr[position], tensor.indptr[position+1])}
                    assert expected == stored
                    coefficient = vector[i]*vector[j]*(1 if i == j else 2)
                    for index, multiplicity in expected.items():
                        weights[index] += coefficient*multiplicity*data[2][index]
                    checked += 1
                    attempted += 1
            assert checked == len(support)*(len(support)+1)//2
            terms = [[index, coefficient] for index, coefficient in sorted(weights.items()) if coefficient]
            divisor = reduce(gcd, [abs(value) for _, value in terms], 0)
            primitive = [[index, value//divisor] for index, value in terms]
            assert divisor == block['positive_form_gcd'] > 0
            assert primitive == block['primitive_induced_count_form']
            value = sum(coefficient*induced[index] for index, coefficient in primitive)
            assert value == block['primitive_value'] < 0
            assert value*divisor == block['integer_quadratic_value']
            cut = saved['unique_induced_count_cuts'][block['cut_index']]
            assert primitive == cut['terms'] and value == cut['exact_value_at_witness']
            record = {'root_type': root, 'supported_flags': len(support), 'products_reconstructed': checked,
                      'primitive_value': value, 'integer_quadratic_value': value*divisor,
                      'full_induced_form_matches': True, 'all_supported_tensor_entries_match': True,
                      'seconds': time.monotonic()-block_started}
            result['completed_blocks'].append(record)
            save(output, result)
            print(json.dumps(record), flush=True)
    except TimeoutError:
        timed_out = True
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)
    completed = len(result['completed_blocks'])
    result.update(status='independent fresh-product reconstruction PASS' if completed == 18 else
                         'bounded fresh-product reconstruction incomplete; unresolved blocks retained',
                  timed_out=timed_out, complete=completed == 18,
                  completed_block_count=completed,
                  completed_supported_entries=sum(block['products_reconstructed'] for block in result['completed_blocks']),
                  attempted_supported_entries=attempted, seconds=time.monotonic()-started,
                  peak_process_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    save(output, result)
    print(json.dumps({key: value for key, value in result.items() if key != 'completed_blocks'}, indent=2), flush=True)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    prep = sub.add_parser('prepare')
    for name in ('certificate', 'second-witness', 'output'):
        prep.add_argument('--'+name, type=Path, required=True)
    check = sub.add_parser('run')
    check.add_argument('--preparation', type=Path, required=True)
    check.add_argument('--output', type=Path, required=True)
    check.add_argument('--seconds', type=float, default=300)
    args = parser.parse_args()
    if args.command == 'prepare':
        prepare(args.certificate, args.second_witness, args.output)
    else:
        run(args.preparation, args.output, args.seconds)
