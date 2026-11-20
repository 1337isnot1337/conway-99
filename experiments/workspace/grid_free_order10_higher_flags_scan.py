"""Bounded complete r4s3 generation and exact-count-point separation.

The reusable tensors retain every prepared flag and are independent of the
count point. Numerical directions are accepted only after exact quadratic
and induced-form contraction checks. There is no optimizer or dense core
reduction. The complete r2s4 family is evaluated separately.
"""

import argparse
from collections import Counter
import gzip
import json
from pathlib import Path
import pickle
import resource
import signal
import time

import numpy as np
from threadpoolctl import threadpool_limits

import grid_free_order10_higher_flags_products as products
import grid_free_order10_r8s1 as forms
import grid_free_order10_r8s1_scan as directions
import grid_free_order10_scaled as files


PRODUCT_SHA = '32b39c98538bd5358e64e7e794c9f6464704ea7f1fe9f6f171d9243f4af88a36'
PRODUCT_PREPARATION_SHA = '07d6e6b22fe77c784a5540672c245cb21691707edf209c53cf722eb101a8197f'
DIRECTION_SHA = '71f06ef752adff6d49f88136b9e82f054f6485a2b2867c2cd4ef9f7ef7f82887'
FORM_SHA = '77e27f09dde9a9c2d57082a60abbab5ac7698875856c7856fe1dc376d6998469'
WITNESS_SHA = '190c779b4a8758d9df90ccc13a54538d8e120710e224b9150dd3aa4b591bd53d'
SMALL_SCAN_SHA = '7db3f850e35aa321a74354037733e5693d6fd22d35342bf4a2e53c017b1f7f6e'


def inputs(product_preparation, witness, small_scan):
    assert files.digest(Path(products.__file__)) == PRODUCT_SHA
    assert files.digest(product_preparation) == PRODUCT_PREPARATION_SHA
    assert files.digest(Path(directions.__file__)) == DIRECTION_SHA
    assert files.digest(Path(forms.__file__)) == FORM_SHA
    assert files.digest(witness) == WITNESS_SHA
    assert files.digest(small_scan) == SMALL_SCAN_SHA
    prepared = json.loads(product_preparation.read_text())
    domain_path = Path(prepared['domain_path'])
    assert files.digest(domain_path) == prepared['domain_sha256']
    domains = json.loads(domain_path.read_text())
    catalogue = Path(prepared['catalogue_path'])
    assert files.digest(catalogue) == prepared['catalogue_sha256']
    with catalogue.open('rb') as stream:
        data = pickle.load(stream)
    point = json.loads(witness.read_text())
    assert point['exact_count_and_held_cut_witness'] and point['held_cut_count'] == 47
    assert point['negative_induced_rows'] == point['nonintegral_induced_rows'] == 0
    assert point['original_equations_checked'] == 180445
    assert len(point['induced_counts']) == 48965
    assert all(type(value) is int and value >= 0 for value in point['induced_counts'])
    small = json.loads(small_scan.read_text())
    assert small['witness_sha256'] == WITNESS_SHA and not small['exact_cuts']
    assert small['principal_minors_checked'] == 22
    assert all(block['positive_semidefinite_exactly'] for block in small['blocks'])
    family = next(item for item in domains['families'] if item['root_size'] == 4)
    records = {record['root_type']:record for record in family['records']}
    assert set(records) == set(data[1][4]) and len(records) == 9
    assert sum(record['flags'] for record in records.values()) == 883
    assert sum(record['complexity']['lower_entries'] for record in records.values()) == 90240
    order = sorted(records, key=lambda root:(records[root]['flags'],root))
    return prepared, domains, data, point, records, order


def prepare(product_preparation, witness, small_scan, output):
    started = time.monotonic()
    prepared, domains, data, point, records, order = inputs(product_preparation,witness,small_scan)
    paths = {'product_preparation':product_preparation,'witness':witness,'small_scan':small_scan}
    result = {'status':'complete nine-root r4s3 generation and scan prepared; not started',
              'source_sha256':files.digest(Path(__file__)),'product_source_sha256':PRODUCT_SHA,
              'direction_source_sha256':DIRECTION_SHA,'form_source_sha256':FORM_SHA,
              'inputs':{key:str(path) for key,path in paths.items()},
              'input_hashes':{key:files.digest(path) for key,path in paths.items()},
              'domain_sha256':prepared['domain_sha256'],'catalogue_path':prepared['catalogue_path'],
              'catalogue_sha256':prepared['catalogue_sha256'],'witness_sha256':WITNESS_SHA,
              'root_visit_order':order,'root_dimensions':[[root,records[root]['flags']] for root in order],
              'full_family_roots':sorted(order),'full_family_flags':883,'full_family_lower_entries':90240,
              'maximum_block_order':332,'maximum_unfiltered_completion_choices_per_entry':698,
              'maximum_mask_matched_completion_choices_per_entry':567,
              'root_mask_matched_completion_bound_all_entries':37180575,
              'maximum_generation_and_scan_seconds':300,'threads':1,
              'reusable_cache_is_point_independent':True,'root_or_flag_zero_pruning':False,
              'nonbinary_diagonal_shortcut':False,'free_stabilizer_divisor':False,
              'all_overlap_multiplicities_retained':True,
              'tiny_r2s4_exact_PSD_at_same_witness':True,
              'negative_cuts_exported_in':'unlabelled induced catalogue counts',
              'fresh_product_reconstruction_required_before_cut_use':True,
              'dense_reduction_loaded':False,'optimizer_called':False,
              'preparation_seconds':time.monotonic()-started,
              'peak_process_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    files.save(output,result)
    print(json.dumps(result,indent=2),flush=True)
    return result


def synchronize(result, generated, scanned):
    result['generated_blocks'] = [record for _,_,_,record in generated]
    result['root_types_generated'] = [root for root,_,_,_ in generated]
    result['blocks_generated'] = len(generated)
    result['blocks_scanned'] = len(scanned)
    result['root_types_scanned'] = [record['root_type'] for record in scanned]
    result['scanned_blocks'] = [{key:value for key,value in record.items() if key != 'negative'} for record in scanned]
    negatives, unique, known, unconfirmed = [], [], {}, []
    for record in scanned:
        if record['negative'] is not None:
            negative = dict(record['negative'])
            key = tuple(tuple(term) for term in negative['primitive_induced_count_form'])
            if key not in known:
                known[key] = len(unique)
                unique.append({'terms':negative['primitive_induced_count_form'],
                               'exact_value_at_witness':negative['primitive_value']})
            negative['cut_index'] = known[key]
            negatives.append(negative)
        elif record['smallest_numeric_eigenvalue'] is not None and record['smallest_numeric_eigenvalue'] < -1e-8:
            unconfirmed.append({'root_type':record['root_type'],'eigenvalue':record['smallest_numeric_eigenvalue']})
    result['negative_blocks'] = negatives
    result['unique_induced_count_cuts'] = unique
    result['exact_negative_blocks'] = len(negatives)
    result['unique_induced_count_cut_count'] = len(unique)
    result['unconfirmed_numeric_negatives'] = unconfirmed


def save_cache(path, generated, order, catalogue_sha, domain_sha):
    roots = [root for root,_,_,_ in generated]
    payload = {'format':1,'family':'induced r4s3 with labelled extension variables',
               'source_sha256':files.digest(Path(__file__)),'product_source_sha256':PRODUCT_SHA,
               'domain_sha256':domain_sha,'catalogue_sha256':catalogue_sha,
               'point_independent_tensors':True,'root_or_flag_zero_pruning':False,
               'full_family_roots':sorted(order),'completed_root_types':roots,
               'complete_family':set(roots) == set(order),
               'blocks':[(root,flags,tensor) for root,flags,tensor,_ in generated]}
    pending = path.with_name(path.name+'.pending')
    pending.write_bytes(gzip.compress(pickle.dumps(payload,protocol=5),mtime=0))
    pending.replace(path)


def run(preparation, output, cache, seconds=300):
    assert 0 < seconds <= 300 and not output.exists() and not cache.exists()
    saved = json.loads(preparation.read_text())
    assert saved['source_sha256'] == files.digest(Path(__file__))
    paths = {key:Path(value) for key,value in saved['inputs'].items()}
    for key,path in paths.items():
        assert files.digest(path) == saved['input_hashes'][key]
    prepared, domains, data, point, records, order = inputs(**paths)
    assert order == saved['root_visit_order']
    embeddings = [value*aut for value,aut in zip(point['induced_counts'],data[2])]
    builder = products.Builder(data,domains)
    generated, scanned = [], []
    result = {'status':'running bounded complete r4s3 generation and scan',
              'source_sha256':saved['source_sha256'],'product_source_sha256':PRODUCT_SHA,
              'preparation_path':str(preparation),'preparation_sha256':files.digest(preparation),
              'catalogue_path':prepared['catalogue_path'],'catalogue_sha256':prepared['catalogue_sha256'],
              'domain_sha256':prepared['domain_sha256'],
              'witness_path':str(paths['witness']),'witness_sha256':WITNESS_SHA,
              'full_family_root_types':sorted(order),'root_visit_order':order,
              'maximum_seconds':seconds,'root_or_flag_zero_pruning':False,
              'optimizer_called':False,'dense_reduction_loaded':False,
              'PSD_feasibility_certified':False,'fresh_product_reconstruction_completed':False}
    started = time.monotonic()
    timed_out = False

    def deadline(_signum,_frame):
        raise TimeoutError('bounded complete r4s3 generation and scan')

    previous = signal.signal(signal.SIGALRM,deadline)
    signal.setitimer(signal.ITIMER_REAL,seconds)
    try:
        for root in order:
            block_started = time.monotonic()
            flags,tensor = builder.block(root)
            assert len(flags) == records[root]['flags']
            assert tensor.shape == (len(flags)*(len(flags)+1)//2,48965)
            assert tensor.data.dtype.kind == 'i' and np.all(tensor.data > 0)
            sums = np.asarray(tensor.sum(axis=1)).ravel()
            assert int(max(sums,default=0)) <= 567
            plain = [{key:value for key,value in flag.items() if key != 'transport'} for flag in flags]
            generation = {'root_type':root,'flag_count':len(flags),'lower_entries':tensor.shape[0],
                          'tensor_nonzeros':tensor.nnz,'maximum_tensor_row_sum':int(max(sums,default=0)),
                          'generation_seconds':time.monotonic()-block_started}
            generated.append((root,plain,tensor,generation))
            matrix = directions.FullScanner.matrix(tensor,len(flags),embeddings)
            vector,quadratic,smallest,removed = directions.FullScanner.negative(matrix)
            negative = None
            if vector is not None:
                terms,divisor = forms.induced_form(tensor,vector,data[2])
                value = sum(coefficient*point['induced_counts'][index] for index,coefficient in terms)
                assert value*divisor == quadratic < 0
                negative = {'root_type':root,'flag_count':len(flags),'integer_vector':vector,
                            'integer_quadratic_value':quadratic,'primitive_induced_count_form':terms,
                            'positive_form_gcd':divisor,'primitive_value':value}
            scanned.append({'root_type':root,'flag_count':len(flags),'negative':negative,
                            'smallest_numeric_eigenvalue':smallest,'exact_zero_rows_removed':removed,
                            'generation_and_scan_seconds':time.monotonic()-block_started})
            synchronize(result,generated,scanned)
            result['seconds_so_far'] = time.monotonic()-started
            files.save(output,result)
            print(json.dumps({**generation,'exact_negative_direction':negative is not None,
                              'seconds_total':time.monotonic()-started}),flush=True)
    except TimeoutError:
        timed_out = True
    finally:
        signal.setitimer(signal.ITIMER_REAL,0)
        signal.signal(signal.SIGALRM,previous)
    synchronize(result,generated,scanned)
    save_cache(cache,generated,order,prepared['catalogue_sha256'],prepared['domain_sha256'])
    result.update(status='exact r4s3 separators found' if result['negative_blocks'] else
                         'no exact separator in completed r4s3 blocks; PSD not certified',
                  timed_out=timed_out,complete_generation=len(generated) == 9,
                  complete_full_family_scan=len(scanned) == 9 and not timed_out,
                  lower_entries_completed=sum(tensor.shape[0] for _,_,tensor,_ in generated),
                  tensor_nonzeros_completed=sum(tensor.nnz for _,_,tensor,_ in generated),
                  generated_cache_path=str(cache),generated_cache_sha256=files.digest(cache),
                  transport_checks=builder.engine.transports_checked,
                  seconds=time.monotonic()-started,
                  peak_process_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    files.save(output,result)
    print(json.dumps({key:value for key,value in result.items() if key not in
          ('generated_blocks','scanned_blocks','negative_blocks','unique_induced_count_cuts')},indent=2),flush=True)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command',required=True)
    first = sub.add_parser('prepare')
    for name in ('product-preparation','witness','small-scan','output'):
        first.add_argument('--'+name,type=Path,required=True)
    run_parser = sub.add_parser('run')
    for name in ('preparation','output','cache'):
        run_parser.add_argument('--'+name,type=Path,required=True)
    run_parser.add_argument('--seconds',type=float,default=300)
    args = parser.parse_args()
    with threadpool_limits(limits=1):
        if args.command == 'prepare':
            prepare(args.product_preparation,args.witness,args.small_scan,args.output)
        else:
            run(args.preparation,args.output,args.cache,args.seconds)
