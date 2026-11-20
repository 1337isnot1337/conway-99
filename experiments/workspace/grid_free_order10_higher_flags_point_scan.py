"""Reusable exact separator for all nine r4s3 and both r2s4 blocks.

FullScanner(data,raw,scale,cache_path,reduced_hash), scan and replay use
the existing 550-coordinate cut schema. A separate manifest combines the
unchanged nine-root tensor cache with the sixteen exact symbolic r2s4
products. All labelled stabilizer factors and all flag diagonals remain.
"""

import argparse
from fractions import Fraction
import gzip
import json
from pathlib import Path
import pickle
import signal
import time

import numpy as np
from scipy import sparse

import grid_free_order10_higher_flags_domains as domains
import grid_free_order10_r8s1 as forms
import grid_free_order10_r8s1_scan as directions
import grid_free_order10_scaled as files


DOMAIN_SOURCE_SHA = 'a2fb1b18940423cdd6d36bce91bac54cbe3eecc8622c2418642b8a9559c8c6f0'
DOMAIN_SHA = 'ccee69da0b0fa9eb111143c6a97a791ab88c7d7ce7004d690ab2ec286c4c2144'
PRODUCT_SOURCE_SHA = '32b39c98538bd5358e64e7e794c9f6464704ea7f1fe9f6f171d9243f4af88a36'
PRODUCT_PREPARATION_SHA = '07d6e6b22fe77c784a5540672c245cb21691707edf209c53cf722eb101a8197f'
R4_SOURCE_SHA = '0b391b83587e258b24f0bb9f25b556990a3e9a007a5bb96d7944b4e5d5a4d722'
R4_SCAN_SHA = 'c70c9efc5588e0c15b9899770a137b37937f2037456f02e6b58077bb6165bcab'
R4_CACHE_SHA = '7707ae4036a0f5889a6356e6d658e742aa969d7385652cb2635418607c6aa943'
FRESH_REPLAY_SHA = '0a6a50182903345149d9d6c61df745bb175bdeeb28bcd5bf0ba4cefa83c32802'
DIRECTION_SHA = '71f06ef752adff6d49f88136b9e82f054f6485a2b2867c2cd4ef9f7ef7f82887'
FORM_SHA = '77e27f09dde9a9c2d57082a60abbab5ac7698875856c7856fe1dc376d6998469'


def make_manifest(domain_path,product_preparation,r4_scan,fresh_replay,output):
    assert files.digest(Path(domains.__file__)) == DOMAIN_SOURCE_SHA
    for path,expected in ((domain_path,DOMAIN_SHA),(product_preparation,PRODUCT_PREPARATION_SHA),
                          (r4_scan,R4_SCAN_SHA),(fresh_replay,FRESH_REPLAY_SHA)):
        assert files.digest(path) == expected
    prepared = json.loads(product_preparation.read_text())
    result = json.loads(r4_scan.read_text())
    fresh = json.loads(fresh_replay.read_text())
    assert prepared['source_sha256'] == PRODUCT_SOURCE_SHA
    assert result['source_sha256'] == R4_SOURCE_SHA
    assert result['complete_generation'] and result['complete_full_family_scan']
    assert fresh['complete'] and fresh['completed_supported_entries'] == 78
    assert fresh['certificate_sha256'] == R4_SCAN_SHA
    cache = Path(result['generated_cache_path'])
    assert files.digest(cache) == result['generated_cache_sha256'] == R4_CACHE_SHA
    manifest = {'format':1,'family':'complete induced labelled r4s3 and r2s4 blocks',
                'source_sha256':files.digest(Path(__file__)),
                'domain_path':str(domain_path),'domain_sha256':DOMAIN_SHA,
                'catalogue_path':prepared['catalogue_path'],'catalogue_sha256':prepared['catalogue_sha256'],
                'product_source_sha256':PRODUCT_SOURCE_SHA,
                'point_independent_tensors':True,'root_or_flag_zero_pruning':False,
                'prism_zero_projection_applied_to_cache':False,
                'r4s3_root_types':list(range(8,17)),'r2s4_root_types':[2,3],
                'full_root_count':11,'full_flag_count':890,'full_lower_entries':90256,
                'seed_cut_independent_replay_path':str(fresh_replay),
                'seed_cut_independent_replay_sha256':FRESH_REPLAY_SHA,
                'cache_parts':[
                    {'kind':'r4s3_tensor_cache','path':str(cache),'sha256':R4_CACHE_SHA},
                    {'kind':'r2s4_symbolic_products','path':str(product_preparation),
                     'sha256':PRODUCT_PREPARATION_SHA}]}
    assert not output.exists()
    files.save(output,manifest)
    print(json.dumps(manifest,indent=2),flush=True)
    return manifest


def cache_contents(data,cache_path):
    """Validate both complete families and return their eleven tensors."""
    cache_path = Path(cache_path)
    assert files.digest(Path(domains.__file__)) == DOMAIN_SOURCE_SHA
    manifest = json.loads(cache_path.read_text())
    assert manifest['format'] == 1 and manifest['source_sha256'] == files.digest(Path(__file__))
    assert manifest['product_source_sha256'] == PRODUCT_SOURCE_SHA
    assert manifest['point_independent_tensors'] and not manifest['root_or_flag_zero_pruning']
    assert not manifest['prism_zero_projection_applied_to_cache']
    domain_path = Path(manifest['domain_path'])
    assert files.digest(domain_path) == manifest['domain_sha256'] == DOMAIN_SHA
    prepared = json.loads(domain_path.read_text())
    assert prepared['source_sha256'] == DOMAIN_SOURCE_SHA
    assert manifest['catalogue_sha256'] == prepared['catalogue_sha256'] == domains.CATALOGUE_SHA
    records = {record['root_type']:record for family in prepared['families'] for record in family['records']}
    r4, r2 = set(data[1][4]), set(data[1][2])
    assert r4 == set(manifest['r4s3_root_types']) and r2 == set(manifest['r2s4_root_types'])
    assert len(r4) == 9 and len(r2) == 2 and set(records) == r4 | r2
    blocks, bindings = [], []
    kinds = set()
    for part in manifest['cache_parts']:
        path = Path(part['path'])
        assert files.digest(path) == part['sha256']
        assert part['kind'] not in kinds
        kinds.add(part['kind'])
        if part['kind'] == 'r4s3_tensor_cache':
            assert part['sha256'] == R4_CACHE_SHA
            payload = pickle.loads(gzip.decompress(path.read_bytes()))
            assert payload['source_sha256'] == R4_SOURCE_SHA
            assert payload['product_source_sha256'] == PRODUCT_SOURCE_SHA
            assert payload['domain_sha256'] == DOMAIN_SHA
            assert payload['point_independent_tensors'] and not payload['root_or_flag_zero_pruning']
            assert payload['complete_family'] and set(payload['full_family_roots']) == r4
            assert set(payload['completed_root_types']) == r4
            assert {root for root,_,_ in payload['blocks']} == r4
            blocks.extend(payload['blocks'])
        else:
            assert part['kind'] == 'r2s4_symbolic_products'
            assert part['sha256'] == PRODUCT_PREPARATION_SHA
            payload = json.loads(path.read_text())
            assert payload['source_sha256'] == PRODUCT_SOURCE_SHA
            assert payload['domain_sha256'] == DOMAIN_SHA
            assert {block['root_type'] for block in payload['small_r2s4_symbolic_blocks']} == r2
            for block in payload['small_r2s4_symbolic_blocks']:
                root = block['root_type']
                domain_flags = records[root]['flag_domain']
                flags = [{'size':item['size'],'rows':tuple(item['rows']),
                          'masks':tuple(item['root_masks']),'type':item['type'],
                          'stabilizer':item['root_fixing_free_stabilizer']} for item in domain_flags]
                assert [list(flag['rows']) for flag in flags] == block['flag_rows']
                assert [flag['stabilizer'] for flag in flags] == block['stabilizers']
                rr,cc,vv,seen = [],[],[],set()
                for entry in block['entries']:
                    i,j = entry['flag_indices']
                    assert 0 <= j <= i < len(flags) and (i,j) not in seen
                    seen.add((i,j))
                    terms = entry['labelled_embedding_terms']
                    assert len({index for index,_ in terms}) == len(terms)
                    for index,value in terms:
                        assert type(index) is int and 0 <= index < 48965
                        assert type(value) is int and value > 0
                        rr.append(i*(i+1)//2+j)
                        cc.append(index)
                        vv.append(value)
                assert seen == {(i,j) for i in range(len(flags)) for j in range(i+1)}
                tensor = sparse.csr_matrix((np.array(vv,dtype=np.int64),(rr,cc)),
                                           shape=(len(flags)*(len(flags)+1)//2,48965),dtype=np.int64)
                blocks.append((root,flags,tensor))
        bindings.append({'kind':part['kind'],'path':str(path),'sha256':part['sha256']})
    assert kinds == {'r4s3_tensor_cache','r2s4_symbolic_products'}
    roots = [root for root,_,_ in blocks]
    assert len(roots) == len(set(roots)) == 11 and set(roots) == r4 | r2
    for root,flags,tensor in blocks:
        r = len(data[0][root])
        expected = records[root]['flag_domain']
        assert len(flags) == records[root]['flags'] == len(expected)
        assert tensor.format == 'csr' and tensor.has_canonical_format
        assert tensor.shape == (len(flags)*(len(flags)+1)//2,48965)
        assert tensor.data.dtype.kind == 'i' and np.all(tensor.data > 0)
        assert max(np.asarray(tensor.sum(axis=1)).ravel(),default=0) <= (567 if r == 4 else 75096)
        for i,(flag,item) in enumerate(zip(flags,expected,strict=True)):
            assert flag['size'] == item['size'] and tuple(flag['rows']) == tuple(item['rows'])
            assert tuple(flag['masks']) == tuple(item['root_masks'])
            assert flag['type'] == item['type'] and flag['stabilizer'] == item['root_fixing_free_stabilizer']
            assert domains.caps(flag['rows']) and all(row.bit_count() >= 3 for row in flag['rows'][r:])
            assert tuple(row & ((1 << r)-1) for row in flag['rows'][:r]) == tuple(data[0][root])
            first, diagonal = i*(i+1)//2, i*(i+1)//2+i
            start,end = tensor.indptr[first],tensor.indptr[first+1]
            assert end-start == 1 and int(tensor.indices[start]) == flag['type'] and int(tensor.data[start]) == 1
            small_order_terms = {}
            for k in range(tensor.indptr[diagonal],tensor.indptr[diagonal+1]):
                index,value = int(tensor.indices[k]),int(tensor.data[k])
                assert len(data[0][index]) >= len(flag['rows'])
                if len(data[0][index]) == len(flag['rows']):
                    small_order_terms[index] = value
            assert small_order_terms == {flag['type']:flag['stabilizer']}
    blocks.sort(key=lambda item:(len(item[1]),item[0]))
    coverage = {'cached_root_count':11,'cache_root_types':sorted(roots),
                'r4s3_root_types':sorted(r4),'r2s4_root_types':sorted(r2),
                'r4s3_root_count':9,'r2s4_root_count':2,
                'covers_complete_r4s3_family':True,'covers_complete_r2s4_family':True,
                'covers_full11_families':True,
                'cached_flag_count':sum(len(flags) for _,flags,_ in blocks),
                'cached_lower_entries':sum(tensor.shape[0] for _,_,tensor in blocks),
                'cached_tensor_nonzeros':sum(tensor.nnz for _,_,tensor in blocks),
                'maximum_block_order':max(len(flags) for _,flags,_ in blocks),
                'root_or_flag_zero_pruning':False,'prism_zero_projection_applied_to_cache':False,
                'all_labelled_stabilizer_factors_preserved':True}
    assert coverage['cached_flag_count'] == manifest['full_flag_count'] == 890
    assert coverage['cached_lower_entries'] == manifest['full_lower_entries'] == 90256
    return blocks,coverage,bindings


class FullScanner(directions.FullScanner):
    def __init__(self,data,raw,scale,cache_path,reduced_hash):
        assert files.digest(Path(directions.__file__)) == DIRECTION_SHA
        assert files.digest(Path(forms.__file__)) == FORM_SHA
        self.data,self.raw,self.scale = data,raw,scale
        self.cache_path = Path(cache_path)
        self.cache_sha256 = files.digest(self.cache_path)
        self.reduced_cache_sha = reduced_hash
        self.blocks,self.coverage,self.cache_parts = cache_contents(data,self.cache_path)
        self.lookup = {root:(flags,tensor) for root,flags,tensor in self.blocks}
        assert raw.shape == (48965,550) and not np.any(raw % scale)
        self.forms = sparse.csr_matrix(raw//scale)

    @staticmethod
    def synchronize(result,records):
        negatives,unique,known,unconfirmed = [],[],{},[]
        for record in records:
            cut = record['negative']
            if cut is not None:
                key = tuple(cut['coefficients'])
                if key not in known:
                    known[key] = len(unique)
                    unique.append({'coefficients':cut['coefficients'],
                                   'exact_value_at_proposal':cut['exact_value_at_proposal'],
                                   'new_coordinate_support':[j for j in range(58,550) if cut['coefficients'][j]]})
                negative = {key:value for key,value in cut.items()
                            if key not in ('coefficients','exact_value_at_proposal')}
                negative['core_cut_index'] = known[key]
                negatives.append(negative)
            elif record['smallest'] is not None and record['smallest'] < -1e-8:
                unconfirmed.append({'root_type':record['root'],'eigenvalue':record['smallest']})
        result.update(blocks_scanned=len(records),root_types_scanned=[record['root'] for record in records],
                      negative_blocks=negatives,unique_core_cuts=unique,
                      unconfirmed_numeric_negatives=unconfirmed,
                      exact_zero_rows_removed=sum(record['removed'] for record in records))

    def scan(self,proposal,path,seconds=180):
        assert 0 < seconds <= 180
        proposal,path = Path(proposal),Path(path)
        point,numerators,denominator = directions.exact_point(proposal)
        result = {'source_sha256':files.digest(Path(__file__)),
                  'proposal_path':str(proposal),'proposal_sha256':files.digest(proposal),
                  'cache_path':str(self.cache_path),'cache_sha256':self.cache_sha256,
                  'cache_parts':self.cache_parts,'coverage':self.coverage,
                  'reduced_cache_sha256':self.reduced_cache_sha,
                  'point_float':point,'point_numerators':numerators,'point_denominator':denominator,
                  'root_blocks_total':11,'full_family_root_blocks':11,
                  'blocks_scanned':0,'negative_blocks':[],'unique_core_cuts':[],
                  'unconfirmed_numeric_negatives':[],'exact_zero_rows_removed':0,
                  'nonbinary_diagonal_shortcut':False,'stabilizer_divisor_used':False,
                  'optimizer_called':False,'PSD_feasibility_certified':False}
        records,timed_out = [],False
        started = time.monotonic()

        def deadline(_signum,_frame):
            raise TimeoutError('bounded complete higher-flag separation')

        previous = signal.signal(signal.SIGALRM,deadline)
        signal.setitimer(signal.ITIMER_REAL,seconds)
        try:
            induced = self.count_numerators(numerators)
            result['negative_exact_induced_forms'] = sum(value < 0 for value in induced)
            result['minimum_exact_induced_numerator'] = min(induced)
            embeddings = [value*aut for value,aut in zip(induced,self.data[2])]
            for root,flags,tensor in self.blocks:
                matrix = self.matrix(tensor,len(flags),embeddings)
                vector,quadratic,smallest,removed = self.negative(matrix)
                negative = None
                if vector is not None:
                    terms,divisor = forms.induced_form(tensor,vector,self.data[2])
                    value = sum(coefficient*induced[index] for index,coefficient in terms)
                    assert value*divisor == quadratic < 0
                    core,common = forms.reduced_form(terms,self.raw,self.scale)
                    core_value = sum(a*x for a,x in zip(core,numerators))
                    assert core_value*common == value < 0
                    rational = Fraction(core_value,denominator)
                    negative = {'root_type':root,'root_size':len(self.data[0][root]),'order':len(flags),
                                'integer_vector':vector,'quadratic_numerator':quadratic,
                                'primitive_induced_count_form':terms,'induced_form_gcd':divisor,
                                'primitive_induced_numerator':value,'core_form_gcd':common,
                                'coefficients':core,'exact_value_at_proposal':[rational.numerator,rational.denominator],
                                'smallest_numeric_eigenvalue':smallest}
                records.append({'root':root,'negative':negative,'smallest':smallest,'removed':removed})
                if len(records) % 4 == 0:
                    self.synchronize(result,records)
                    files.save(path,result)
        except TimeoutError:
            timed_out = True
        finally:
            signal.setitimer(signal.ITIMER_REAL,0)
            signal.signal(signal.SIGALRM,previous)
        self.synchronize(result,records)
        scanned = {record['root'] for record in records}
        complete = len(records) == 11 and not timed_out
        result.update(status='exact higher-flag separators found' if result['negative_blocks'] else
                             'no exact separator in scanned higher-flag blocks; PSD not certified',
                      timed_out=timed_out,complete_scan=complete,complete_cached_family_scan=complete,
                      complete_r4s3_scan=set(self.coverage['r4s3_root_types']) <= scanned,
                      complete_r2s4_scan=set(self.coverage['r2s4_root_types']) <= scanned,
                      complete_full11_scan=set(self.coverage['cache_root_types']) <= scanned,
                      exact_negative_block_count=len(result['negative_blocks']),
                      unique_integer_cut_count=len(result['unique_core_cuts']),
                      seconds=time.monotonic()-started)
        files.save(path,result)
        print(json.dumps({key:result[key] for key in ('status','blocks_scanned','complete_r4s3_scan',
              'complete_r2s4_scan','complete_full11_scan','exact_negative_block_count',
              'unique_integer_cut_count','seconds')},indent=2),flush=True)
        return result

    def replay(self,path):
        path = Path(path)
        result = json.loads(path.read_text())
        assert result['source_sha256'] == files.digest(Path(__file__))
        assert result['cache_sha256'] == self.cache_sha256 and result['cache_parts'] == self.cache_parts
        assert result['coverage'] == self.coverage
        assert result['reduced_cache_sha256'] == self.reduced_cache_sha
        proposal = Path(result['proposal_path'])
        assert files.digest(proposal) == result['proposal_sha256']
        point,numerators,denominator = directions.exact_point(proposal)
        assert point == result['point_float'] and numerators == result['point_numerators']
        assert denominator == result['point_denominator']
        induced = self.count_numerators(numerators)
        embeddings = [value*aut for value,aut in zip(induced,self.data[2])]
        used = set()
        for block in result['negative_blocks']:
            flags,tensor = self.lookup[block['root_type']]
            assert len(flags) == block['order'] and len(self.data[0][block['root_type']]) == block['root_size']
            vector = block['integer_vector']
            assert len(vector) == len(flags) and all(type(value) is int for value in vector)
            matrix = self.matrix(tensor,len(flags),embeddings)
            v = np.array(vector,dtype=object)
            quadratic = int(v@matrix@v)
            assert quadratic == block['quadratic_numerator'] < 0
            terms,divisor = forms.induced_form(tensor,vector,self.data[2])
            assert terms == block['primitive_induced_count_form'] and divisor == block['induced_form_gcd']
            value = sum(coefficient*induced[index] for index,coefficient in terms)
            assert value == block['primitive_induced_numerator'] and value*divisor == quadratic
            core,common = forms.reduced_form(terms,self.raw,self.scale)
            assert common == block['core_form_gcd']
            index = block['core_cut_index']
            cut = result['unique_core_cuts'][index]
            assert core == cut['coefficients']
            rational = Fraction(sum(a*x for a,x in zip(core,numerators)),denominator)
            assert [rational.numerator,rational.denominator] == cut['exact_value_at_proposal']
            assert rational < 0
            used.add(index)
        assert len(result['negative_blocks']) == result['exact_negative_block_count']
        assert used == set(range(result['unique_integer_cut_count']))
        return {'status':'exact complete-family higher-flag cached replay PASS',
                'source_sha256':files.digest(Path(__file__)),'cache_sha256':self.cache_sha256,
                'negative_blocks':len(result['negative_blocks']),'unique_integer_cuts':len(used),
                'coverage':self.coverage,'eigensystems_recomputed':False,
                'fresh_product_reconstruction_performed':False,'optimizer_called':False,
                'PSD_feasibility_certified':False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('domains','product-preparation','r4-scan','fresh-replay','output'):
        parser.add_argument('--'+name,type=Path,required=True)
    args = parser.parse_args()
    make_manifest(args.domains,args.product_preparation,args.r4_scan,args.fresh_replay,args.output)
