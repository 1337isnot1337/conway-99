"""Independent literal-product replay of higher-flag separating cuts.

Every supported product is rebuilt by merging its positive and negative
edge prescriptions and enumerating unspecified edges. Producer child DAGs,
transports, and overlap routines are not called. Cached tensors are only
comparison targets; the entire separating form is accumulated afresh.
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
SCANNER_SHA = '0b391b83587e258b24f0bb9f25b556990a3e9a007a5bb96d7944b4e5d5a4d722'


def save(path, record):
    temporary = path.with_name(path.name+'.pending')
    temporary.write_text(json.dumps(record,indent=2)+'\n')
    temporary.replace(path)


def prepare(certificate, output):
    saved = json.loads(certificate.read_text())
    assert saved['source_sha256'] == SCANNER_SHA
    assert oracle.digest(Path(__file__).with_name('grid_free_order10_higher_flags_scan.py')) == SCANNER_SHA
    assert oracle.digest(Path(oracle.__file__)) == ORACLE_SHA
    assert saved['complete_generation'] and saved['complete_full_family_scan'] and not saved['timed_out']
    records = []
    for block in saved['negative_blocks']:
        support = sum(value != 0 for value in block['integer_vector'])
        records.append({'root_type':block['root_type'],'full_flags':block['flag_count'],
                        'supported_flags':support,'supported_lower_entries':support*(support+1)//2})
    result = {'status':'independent higher-flag reconstruction prepared; not started',
              'source_sha256':oracle.digest(Path(__file__)),'oracle_source_sha256':ORACLE_SHA,
              'certificate_path':str(certificate),'certificate_sha256':oracle.digest(certificate),
              'required_blocks':len(records),'negative_blocks':records,
              'supported_lower_entries':sum(record['supported_lower_entries'] for record in records),
              'maximum_literal_completions_per_entry':698,
              'proposed_reconstruction_seconds':60,
              'dense_reduction_loaded':False,'optimizer_called':False}
    save(output,result)
    print(json.dumps(result,indent=2),flush=True)
    return result


def run(preparation, output, seconds=60):
    assert 0 < seconds <= 300 and not output.exists()
    prepared = json.loads(preparation.read_text())
    assert prepared['source_sha256'] == oracle.digest(Path(__file__))
    assert oracle.digest(Path(oracle.__file__)) == prepared['oracle_source_sha256'] == ORACLE_SHA
    certificate = Path(prepared['certificate_path'])
    assert oracle.digest(certificate) == prepared['certificate_sha256']
    saved = json.loads(certificate.read_text())
    assert saved['source_sha256'] == SCANNER_SHA
    catalogue, witness, cache = (Path(saved[key]) for key in
                                 ('catalogue_path','witness_path','generated_cache_path'))
    for path,key in ((catalogue,'catalogue_sha256'),(witness,'witness_sha256'),(cache,'generated_cache_sha256')):
        assert oracle.digest(path) == saved[key]
    with catalogue.open('rb') as stream:
        data = pickle.load(stream)
    induced = json.loads(witness.read_text())['induced_counts']
    payload = pickle.loads(gzip.decompress(cache.read_bytes()))
    assert payload['source_sha256'] == SCANNER_SHA and payload['complete_family']
    assert payload['point_independent_tensors'] and not payload['root_or_flag_zero_pruning']
    blocks = {root:(flags,tensor) for root,flags,tensor in payload['blocks']}
    result = {'status':'running independent literal-product reconstruction',
              'source_sha256':prepared['source_sha256'],'preparation_sha256':oracle.digest(preparation),
              'oracle_source_sha256':ORACLE_SHA,'certificate_sha256':prepared['certificate_sha256'],
              'catalogue_sha256':saved['catalogue_sha256'],'witness_sha256':saved['witness_sha256'],
              'cache_sha256':saved['generated_cache_sha256'],'maximum_seconds':seconds,
              'required_blocks':prepared['required_blocks'],
              'required_supported_entries':prepared['supported_lower_entries'],
              'completed_blocks':[],'producer_builder_called':False,
              'producer_overlap_enumerator_called':False,'producer_transports_called':False,
              'fresh_coefficients_from_literal_prescriptions':True,
              'saved_tensor_used_only_for_comparison':True,'eigensystems_computed':False,
              'dense_reduction_loaded':False,'optimizer_called':False}
    started = time.monotonic()
    timed_out, attempted = False, 0

    def deadline(_signum,_frame):
        raise TimeoutError('bounded higher-flag independent reconstruction')

    previous = signal.signal(signal.SIGALRM,deadline)
    signal.setitimer(signal.ITIMER_REAL,seconds)
    try:
        ids = {oracle.canonical(tuple(rows)):i for i,rows in enumerate(data[0])}
        assert len(ids) == 48965
        for block in saved['negative_blocks']:
            block_started = time.monotonic()
            root = block['root_type']
            flags,tensor = blocks[root]
            r = len(data[0][root])
            assert r == 4 and len(flags) == block['flag_count']
            vector = block['integer_vector']
            assert len(vector) == len(flags) and all(type(value) is int for value in vector)
            support = [i for i,value in enumerate(vector) if value]
            for i in support:
                flag = flags[i]
                rows = tuple(flag['rows'])
                assert len(rows) == r+flag['size']
                assert oracle.induced(rows,range(r)) == tuple(data[0][root])
                assert tuple(row & ((1 << r)-1) for row in rows[r:]) == tuple(flag['masks'])
                assert all(row.bit_count() >= 3 for row in rows[r:]) and oracle.valid(rows)
                assert all(not (rows[a] >> a & 1) for a in range(len(rows)))
                assert all(((rows[a] >> b) & 1) == ((rows[b] >> a) & 1)
                           for a in range(len(rows)) for b in range(a))
            weights, overlap_counts = Counter(), Counter()
            checked = 0
            for i in support:
                for j in support:
                    if j > i:
                        continue
                    expected, by_q = oracle.direct_product(r,tuple(flags[i]['rows']),tuple(flags[j]['rows']),ids)
                    position = i*(i+1)//2+j
                    stored = {int(tensor.indices[k]):int(tensor.data[k])
                              for k in range(tensor.indptr[position],tensor.indptr[position+1])}
                    assert expected == stored
                    weight = vector[i]*vector[j]*(1 if i == j else 2)
                    for index,multiplicity in expected.items():
                        weights[index] += weight*multiplicity*data[2][index]
                    overlap_counts.update(by_q)
                    checked += 1
                    attempted += 1
            assert checked == len(support)*(len(support)+1)//2
            terms = [[index,value] for index,value in sorted(weights.items()) if value]
            divisor = reduce(gcd,[abs(value) for _,value in terms],0)
            primitive = [[index,value//divisor] for index,value in terms]
            assert divisor == block['positive_form_gcd'] > 0
            assert primitive == block['primitive_induced_count_form']
            value = sum(coefficient*induced[index] for index,coefficient in primitive)
            assert value == block['primitive_value'] < 0
            assert value*divisor == block['integer_quadratic_value']
            cut = saved['unique_induced_count_cuts'][block['cut_index']]
            assert primitive == cut['terms'] and value == cut['exact_value_at_witness']
            record = {'root_type':root,'supported_flags':len(support),'products_reconstructed':checked,
                      'accepted_completions_by_overlap':dict(sorted(overlap_counts.items())),
                      'primitive_value':value,'integer_quadratic_value':value*divisor,
                      'full_induced_form_matches':True,'all_supported_tensor_entries_match':True,
                      'seconds':time.monotonic()-block_started}
            result['completed_blocks'].append(record)
            save(output,result)
            print(json.dumps(record),flush=True)
    except TimeoutError:
        timed_out = True
    finally:
        signal.setitimer(signal.ITIMER_REAL,0)
        signal.signal(signal.SIGALRM,previous)
    complete = len(result['completed_blocks']) == prepared['required_blocks']
    result.update(status='independent higher-flag reconstruction PASS' if complete else
                         'bounded reconstruction incomplete; unverified cuts remain unused',
                  complete=complete,timed_out=timed_out,
                  completed_block_count=len(result['completed_blocks']),
                  completed_supported_entries=sum(record['products_reconstructed'] for record in result['completed_blocks']),
                  attempted_supported_entries=attempted,seconds=time.monotonic()-started,
                  peak_process_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    save(output,result)
    print(json.dumps({key:value for key,value in result.items() if key != 'completed_blocks'},indent=2),flush=True)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command',required=True)
    prep = sub.add_parser('prepare')
    prep.add_argument('--certificate',type=Path,required=True)
    prep.add_argument('--output',type=Path,required=True)
    check = sub.add_parser('run')
    check.add_argument('--preparation',type=Path,required=True)
    check.add_argument('--output',type=Path,required=True)
    check.add_argument('--seconds',type=float,default=60)
    args = parser.parse_args()
    if args.command == 'prepare':
        prepare(args.certificate,args.output)
    else:
        run(args.preparation,args.output,args.seconds)
