"""Cache-only arithmetic controls for the complete eleven-block scanner.

This checks full cache coverage, both exact r2s4 matrices/minors, and the
independently reconstructed four-cycle cut through the new matrix API.
It loads neither the dense reduction nor an optimizer.
"""

import argparse
import json
from pathlib import Path
import pickle
import resource
import time

import numpy as np

import grid_free_order10_higher_flags_point_scan as subject
import grid_free_order10_higher_flags_small_scan as small
import grid_free_order10_r8s1 as forms
import grid_free_order10_scaled as files


SUBJECT_SHA = '5d1af5a24c9a509e35b9aeb47e47bd97eb01c09eb51fad32c2a72ceb87075c86'
SMALL_SOURCE_SHA = '6c6f3eb33ca44c052d163a7fbc095ce38d010b14f493fb2656e558acca0819a6'


def main(cache,witness,small_scan,r4_scan,fresh_replay,output):
    started = time.monotonic()
    assert files.digest(Path(subject.__file__)) == SUBJECT_SHA
    assert files.digest(Path(small.__file__)) == SMALL_SOURCE_SHA
    manifest = json.loads(cache.read_text())
    catalogue = Path(manifest['catalogue_path'])
    assert files.digest(catalogue) == manifest['catalogue_sha256']
    with catalogue.open('rb') as stream:
        data = pickle.load(stream)
    blocks,coverage,parts = subject.cache_contents(data,cache)
    assert coverage['covers_full11_families']
    lookup = {root:(flags,tensor) for root,flags,tensor in blocks}
    point = json.loads(witness.read_text())
    induced = point['induced_counts']
    assert len(induced) == 48965 and all(type(value) is int and value >= 0 for value in induced)
    embeddings = [value*aut for value,aut in zip(induced,data[2])]
    small_saved = json.loads(small_scan.read_text())
    assert small_saved['witness_sha256'] == files.digest(witness)
    small_checks,minor_count = [],0
    for block in small_saved['blocks']:
        flags,tensor = lookup[block['root_type']]
        matrix = subject.FullScanner.matrix(tensor,len(flags),embeddings)
        assert matrix.tolist() == block['matrix']
        for minor in block['principal_minors']:
            chosen = minor['indices']
            value = small.determinant([[int(matrix[i,j]) for j in chosen] for i in chosen])
            assert value == minor['determinant'] >= 0
            minor_count += 1
        small_checks.append({'root_type':block['root_type'],'matrix_matches':True,
                             'all_saved_principal_minors_recomputed':True})
    saved = json.loads(r4_scan.read_text())
    fresh = json.loads(fresh_replay.read_text())
    assert saved['witness_sha256'] == files.digest(witness)
    assert fresh['complete'] and fresh['certificate_sha256'] == files.digest(r4_scan)
    cut_checks = []
    for block in saved['negative_blocks']:
        flags,tensor = lookup[block['root_type']]
        matrix = subject.FullScanner.matrix(tensor,len(flags),embeddings)
        vector = np.array(block['integer_vector'],dtype=object)
        value = int(vector@matrix@vector)
        assert value == block['integer_quadratic_value'] < 0
        terms,divisor = forms.induced_form(tensor,list(vector),data[2])
        assert terms == block['primitive_induced_count_form']
        assert divisor == block['positive_form_gcd']
        assert sum(coefficient*induced[index] for index,coefficient in terms)*divisor == value
        cut_checks.append({'root_type':block['root_type'],'integer_quadratic_value':value,
                           'primitive_induced_terms_match':True,'positive_gcd':divisor})
    assert minor_count == 22 and len(cut_checks) == 1
    result = {'status':'complete eleven-block scanner cache/arithmetic controls PASS',
              'source_sha256':files.digest(Path(__file__)),'scanner_source_sha256':SUBJECT_SHA,
              'cache_path':str(cache),'cache_sha256':files.digest(cache),
              'cache_parts':parts,'coverage':coverage,'witness_sha256':files.digest(witness),
              'small_scan_sha256':files.digest(small_scan),'r4_scan_sha256':files.digest(r4_scan),
              'fresh_replay_sha256':files.digest(fresh_replay),
              'small_block_checks':small_checks,'exact_principal_minors_recomputed':minor_count,
              'independently_proved_cut_checks':cut_checks,
              'dense_reduction_loaded':False,'core_form_reduction_replayed':False,
              'eigensystems_computed':False,'optimizer_called':False,
              'seconds':time.monotonic()-started,
              'peak_process_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    files.save(output,result)
    print(json.dumps(result,indent=2),flush=True)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('cache','witness','small-scan','r4-scan','fresh-replay','output'):
        parser.add_argument('--'+name,type=Path,required=True)
    args = parser.parse_args()
    main(args.cache,args.witness,args.small_scan,args.r4_scan,args.fresh_replay,args.output)
