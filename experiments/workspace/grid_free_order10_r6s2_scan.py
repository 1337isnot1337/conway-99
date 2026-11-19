"""Bounded separation of an exact count point by the fixed r6,s2 subfamily.

The selected roots are fixed by the prepared flag-count limit, independently
of the point. Completed tensors are saved without zero-row pruning. Every
accepted negative vector and induced-count inequality uses exact integers.
This driver loads no reduced core matrix and calls no optimizer.
"""

import argparse
import gzip
import json
from pathlib import Path
import pickle
import resource
import signal
import time

import numpy as np
from threadpoolctl import threadpool_limits

import grid_free_order10_r6s2 as family
import grid_free_order10_r8s1 as forms
import grid_free_order10_r8s1_scan as directions
import grid_free_order10_scaled as counts


FAMILY_SHA = '3772c728ec764dbec0142865696bb747c06e47b29495964af867103618b75a6d'
PREPARATION_SHA = '1ff172888ebdd1a139710cb25e0a0f29c8044a1d81ba4972c0085f9827d691ea'
DIRECTION_SHA = '71f06ef752adff6d49f88136b9e82f054f6485a2b2867c2cd4ef9f7ef7f82887'


def inputs(preparation):
    assert counts.digest(preparation) == PREPARATION_SHA
    assert counts.digest(Path(family.__file__)) == FAMILY_SHA
    assert counts.digest(Path(directions.__file__)) == DIRECTION_SHA
    assert counts.digest(Path(forms.__file__)) == family.TRANSPORT_SOURCE_SHA
    saved = json.loads(preparation.read_text())
    assert saved['source_sha256'] == FAMILY_SHA
    catalogue, witness = Path(saved['catalogue_path']), Path(saved['witness_path'])
    assert counts.digest(catalogue) == saved['catalogue_sha256'] == family.CATALOGUE_SHA
    assert counts.digest(witness) == saved['witness_sha256'] == family.WITNESS_SHA
    with catalogue.open('rb') as stream:
        data = pickle.load(stream)
    point = json.loads(witness.read_text())
    induced = point['induced_counts']
    assert len(induced) == len(data[0]) == 48965
    assert all(type(value) is int and value >= 0 for value in induced)
    assert not saved['point_dependent_flag_or_root_pruning']
    records = {record['root_type']: record for record in saved['all_62_root_domains']}
    selected = saved['selected_root_types']
    assert selected == [root for root in data[1][6] if 1 < records[root]['flags'] <= 512]
    assert len(selected) == 55 and sum(records[root]['lower_entries'] for root in selected) == 1042819
    return saved, data, point, records, sorted(selected, key=lambda root: (records[root]['flags'], root))


def manifest(preparation, output):
    saved, data, point, records, order = inputs(preparation)
    result = {'status': 'bounded r6s2 scanner prepared; no large generation or scan',
              'source_sha256': counts.digest(Path(__file__)), 'family_source_sha256': FAMILY_SHA,
              'direction_source_sha256': DIRECTION_SHA, 'form_source_sha256': family.TRANSPORT_SOURCE_SHA,
              'family_preparation_path': str(preparation), 'family_preparation_sha256': PREPARATION_SHA,
              'catalogue_sha256': family.CATALOGUE_SHA, 'witness_sha256': family.WITNESS_SHA,
              'selected_blocks': 55, 'selected_lower_entries': 1042819,
              'largest_selected_order': max(records[root]['flags'] for root in order),
              'root_visit_order': order, 'visit_rule': 'increasing flag count, then root type',
              'oversize_roots_omitted': saved['oversize_root_types'],
              'root_or_flag_zero_pruning': False,
              'maximum_scan_seconds': 180, 'threads': 1,
              'maximum_free_edge_completion_choices_per_two_by_two_entry': 26,
              'fixed_width_sign_evaluation_used': False,
              'negative_cuts_exported_in': 'unlabelled induced catalogue counts',
              'core_form_reduction_performed': False, 'dense_reduction_loaded': False,
              'optimizer_called': False, 'PSD_feasibility_certified_by_scan': False}
    counts.save(output, result)
    print(json.dumps(result, indent=2), flush=True)
    return result


def save_cache(path, blocks, selected, complete):
    payload = {'format': 1, 'family': 'induced r6s2 whole-flag outside degree at least3',
               'source_sha256': counts.digest(Path(__file__)), 'family_source_sha256': FAMILY_SHA,
               'catalogue_sha256': family.CATALOGUE_SHA, 'point_independent_tensors': True,
               'root_or_flag_zero_pruning': False, 'selected_root_types': selected,
               'completed_root_types': [root for root, _, _ in blocks],
               'complete_selected_subfamily': complete, 'blocks': blocks}
    temporary = path.with_name(path.name+'.pending')
    temporary.write_bytes(gzip.compress(pickle.dumps(payload, protocol=5), mtime=0))
    temporary.replace(path)


def scan(preparation, scanner_manifest, output, cache_path, seconds=180):
    assert 0 < seconds <= 180 and not output.exists()
    prepared = json.loads(scanner_manifest.read_text())
    assert prepared['source_sha256'] == counts.digest(Path(__file__))
    assert prepared['family_preparation_sha256'] == counts.digest(preparation)
    saved, data, point, records, order = inputs(preparation)
    assert order == prepared['root_visit_order']
    induced = point['induced_counts']
    embeddings = [count*aut for count, aut in zip(induced, data[2])]
    builder = family.Builder(data)
    result = {'status': 'running bounded r6s2 generation and exact separation',
              'source_sha256': counts.digest(Path(__file__)), 'family_source_sha256': FAMILY_SHA,
              'family_preparation_path': str(preparation), 'family_preparation_sha256': PREPARATION_SHA,
              'scanner_manifest_path': str(scanner_manifest), 'scanner_manifest_sha256': counts.digest(scanner_manifest),
              'catalogue_path': saved['catalogue_path'], 'catalogue_sha256': family.CATALOGUE_SHA,
              'witness_path': saved['witness_path'], 'witness_sha256': family.WITNESS_SHA,
              'maximum_seconds': seconds, 'selected_root_types': saved['selected_root_types'],
              'root_visit_order': order, 'full_family_root_count': 62,
              'oversize_roots_omitted': saved['oversize_root_types'],
              'blocks': [], 'negative_blocks': [], 'unique_induced_count_cuts': [],
              'unconfirmed_numeric_negatives': [], 'optimizer_called': False,
              'dense_reduction_loaded': False, 'PSD_feasibility_certified': False}
    counts.save(output, result)
    blocks, known = [], {}
    timed_out = False
    started = time.monotonic()

    def deadline(_signum, _frame):
        raise TimeoutError('bounded r6s2 generation and separation')

    previous = signal.signal(signal.SIGALRM, deadline)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        for root in order:
            block_started = time.monotonic()
            flags, tensor = builder.block(root)
            assert len(flags) == records[root]['flags']
            row_sums = np.asarray(tensor.sum(axis=1)).ravel()
            assert max(row_sums, default=0) <= 26
            matrix = family.exact_matrix(tensor, len(flags), embeddings)
            assert np.array_equal(matrix[0, :], np.array([embeddings[flag['type']] for flag in flags], dtype=object))
            vector, quadratic, smallest, removed = directions.FullScanner.negative(matrix)
            record = {'root_type': root, 'flag_count': len(flags), 'lower_entries': tensor.shape[0],
                      'tensor_nonzeros': tensor.nnz, 'maximum_tensor_row_sum': int(max(row_sums, default=0)),
                      'smallest_numeric_eigenvalue': smallest, 'exact_zero_rows_removed_for_eigensystem': removed,
                      'exact_negative_direction': vector is not None}
            if vector is not None:
                terms, divisor = forms.induced_form(tensor, vector, data[2])
                value = sum(coefficient*induced[index] for index, coefficient in terms)
                assert value*divisor == quadratic < 0
                key = tuple(tuple(item) for item in terms)
                if key not in known:
                    known[key] = len(result['unique_induced_count_cuts'])
                    result['unique_induced_count_cuts'].append({'terms': terms, 'exact_value_at_witness': value})
                result['negative_blocks'].append({'root_type': root, 'flag_count': len(flags),
                    'integer_vector': vector, 'integer_quadratic_value': quadratic,
                    'primitive_induced_count_form': terms, 'positive_form_gcd': divisor,
                    'primitive_value': value, 'cut_index': known[key]})
            elif smallest is not None and smallest < -1e-8:
                result['unconfirmed_numeric_negatives'].append({'root_type': root, 'eigenvalue': smallest})
            flag_records = [{'size': flag['size'], 'masks': flag['masks'], 'edge': flag['edge'],
                             'rows': flag['rows'], 'type': flag['type']} for flag in flags]
            blocks.append((root, flag_records, tensor))
            record['seconds'] = time.monotonic()-block_started
            result['blocks'].append(record)
            result.update(blocks_completed=len(blocks), exact_negative_blocks=len(result['negative_blocks']),
                          unique_induced_count_cut_count=len(result['unique_induced_count_cuts']),
                          seconds_so_far=time.monotonic()-started)
            counts.save(output, result)
            print(json.dumps(record), flush=True)
    except TimeoutError:
        timed_out = True
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)
    # A deadline can arrive between the small result/cache append steps.
    # Keep only wholly committed blocks, then rebuild cut indices exactly.
    recorded_roots = {record['root_type'] for record in result['blocks']}
    blocks = [block for block in blocks if block[0] in recorded_roots]
    completed_roots = {root for root, _, _ in blocks}
    result['blocks'] = [record for record in result['blocks'] if record['root_type'] in completed_roots]
    result['negative_blocks'] = [block for block in result['negative_blocks']
                                 if block['root_type'] in completed_roots]
    result['unconfirmed_numeric_negatives'] = [record for record in result['unconfirmed_numeric_negatives']
                                               if record['root_type'] in completed_roots]
    result['unique_induced_count_cuts'] = []
    known = {}
    for block in result['negative_blocks']:
        terms = block['primitive_induced_count_form']
        key = tuple(tuple(item) for item in terms)
        if key not in known:
            known[key] = len(result['unique_induced_count_cuts'])
            result['unique_induced_count_cuts'].append({'terms': terms,
                                                       'exact_value_at_witness': block['primitive_value']})
        block['cut_index'] = known[key]
    complete = len(blocks) == len(order) and not timed_out
    save_cache(cache_path, blocks, saved['selected_root_types'], complete)
    result.update(status='exact r6s2 negative directions found' if result['negative_blocks'] else
                         'no exact separator in completed selected blocks; PSD not certified',
                  timed_out=timed_out, complete_selected_subfamily_scan=complete,
                  complete_full_family_scan=False, blocks_completed=len(blocks),
                  exact_negative_blocks=len(result['negative_blocks']),
                  unique_induced_count_cut_count=len(result['unique_induced_count_cuts']),
                  generated_cache_path=str(cache_path), generated_cache_sha256=counts.digest(cache_path),
                  lower_entries_completed=sum(tensor.shape[0] for _, _, tensor in blocks),
                  tensor_nonzeros_completed=sum(tensor.nnz for _, _, tensor in blocks),
                  verified_transports=builder.transport_engine.transports_checked,
                  product_entries_attempted=builder.entries_built,
                  seconds=time.monotonic()-started,
                  peak_process_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    counts.save(output, result)
    print(json.dumps({key: value for key, value in result.items() if key not in
                     ('blocks', 'negative_blocks', 'unique_induced_count_cuts', 'root_visit_order', 'selected_root_types')}, indent=2), flush=True)
    return result


def replay(certificate, output):
    result = json.loads(certificate.read_text())
    assert result['source_sha256'] == counts.digest(Path(__file__))
    assert result['family_source_sha256'] == counts.digest(Path(family.__file__)) == FAMILY_SHA
    _, data, point, records, _ = inputs(Path(result['family_preparation_path']))
    path = Path(result['generated_cache_path'])
    assert counts.digest(path) == result['generated_cache_sha256']
    payload = pickle.loads(gzip.decompress(path.read_bytes()))
    assert payload['source_sha256'] == result['source_sha256']
    assert payload['family_source_sha256'] == FAMILY_SHA and payload['point_independent_tensors']
    assert not payload['root_or_flag_zero_pruning']
    blocks = {root: (flags, tensor) for root, flags, tensor in payload['blocks']}
    induced = point['induced_counts']
    embeddings = [count*aut for count, aut in zip(induced, data[2])]
    used = set()
    for block in result['negative_blocks']:
        flags, tensor = blocks[block['root_type']]
        assert len(flags) == block['flag_count'] == records[block['root_type']]['flags']
        vector = block['integer_vector']
        assert len(vector) == len(flags) and all(type(value) is int for value in vector)
        matrix = family.exact_matrix(tensor, len(flags), embeddings)
        v = np.array(vector, dtype=object)
        quadratic = int(v@matrix@v)
        assert quadratic == block['integer_quadratic_value'] < 0
        terms, divisor = forms.induced_form(tensor, vector, data[2])
        assert terms == block['primitive_induced_count_form']
        assert divisor == block['positive_form_gcd']
        value = sum(coefficient*induced[index] for index, coefficient in terms)
        assert value == block['primitive_value'] and value*divisor == quadratic
        saved = result['unique_induced_count_cuts'][block['cut_index']]
        assert saved['terms'] == terms and saved['exact_value_at_witness'] == value
        used.add(block['cut_index'])
    assert used == set(range(result['unique_induced_count_cut_count']))
    report = {'status': 'exact saved-tensor r6s2 cut replay PASS',
              'certificate_sha256': counts.digest(certificate), 'negative_blocks': len(result['negative_blocks']),
              'unique_induced_count_cuts': len(used), 'optimizer_called': False,
              'numerical_eigensystems_recomputed': False, 'tensor_construction_rebuilt': False,
              'PSD_feasibility_certified': False}
    counts.save(output, report)
    print(json.dumps(report, indent=2), flush=True)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    prep = sub.add_parser('prepare')
    prep.add_argument('--family-preparation', type=Path, required=True)
    prep.add_argument('--output', type=Path, required=True)
    run = sub.add_parser('scan')
    for name in ('family-preparation', 'scanner-manifest', 'output', 'cache'):
        run.add_argument('--'+name, type=Path, required=True)
    run.add_argument('--seconds', type=float, default=180)
    check = sub.add_parser('replay')
    check.add_argument('--certificate', type=Path, required=True)
    check.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    with threadpool_limits(limits=1):
        if args.command == 'prepare':
            manifest(args.family_preparation, args.output)
        elif args.command == 'scan':
            scan(args.family_preparation, args.scanner_manifest, args.output, args.cache, args.seconds)
        else:
            replay(args.certificate, args.output)
