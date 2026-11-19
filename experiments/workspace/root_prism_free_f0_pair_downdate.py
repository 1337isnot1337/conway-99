"""Bounded exact two-column Gram classification via compressed types.

Generation rebuilds the complete component-pair type census, certifies
integer bounds, and runs the bound native enumerator. Only canonical new
type predicates are retained, never all full-column pairs. Replay checks
every retained predicate and all saved full39 integer negative vectors.
No SAT query is made.
"""

import argparse
from collections import Counter, defaultdict
import gzip
import hashlib
from itertools import combinations
import json
from math import gcd
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile
import time

import root_prism_free_f0_pair_gram_model as preparation


ROOT, LOGS = preparation.ROOT, preparation.LOGS
TYPE_CERT = LOGS/'f0-pair-gram-model-preparation.json.gz'
TYPE_SHA = '7b870a9df98c855f75fcd0191b5fe03589d9458ad1e3f985ba77edb066be0c59'
BOUNDS = LOGS/'f0-pair-downdate-bounds.json'
BOUNDS_SHA = '443c87ca561fa28c343d0446afa6d65ad87ad7d1f754a54a1756e5fcca7b6dfb'
NATIVE = Path(__file__).with_suffix('.cpp')
D = 4577040
FLAGS = ['same_component_selector','intersection_at_least_three','quota_one_local_pair',
         'quota_one_cross_pair','existing_component_motif']
digest, canonical = preparation.digest, preparation.canonical


def portable(path):
    return str(path.resolve().relative_to(ROOT))


def type_key(record):
    return (tuple(record[0]),tuple(record[1]),record[2],record[3],record[4],
            tuple(record[5]),record[6],record[7])


def reverse_key(key):
    return (key[1],key[0],key[3],key[2],key[4],key[5],key[6],key[7])


def load():
    assert digest(TYPE_CERT) == TYPE_SHA and digest(BOUNDS) == BOUNDS_SHA
    saved = json.loads(gzip.decompress(TYPE_CERT.read_bytes()))
    assert saved['source_sha256'] == digest(Path(preparation.__file__))
    data = preparation.load()
    domain, core, gram, pairs, columns, conflicts, single = data
    table = preparation.table_preparation(domain,conflicts,single)
    assert table == saved['bilinear_table_preparation']
    types = table['type_histogram']
    keys = [type_key(record) for record in types]
    assert keys == sorted(set(keys)) and len(keys) == 36134
    index = {key:i for i,key in enumerate(keys)}
    reverse = [index[reverse_key(key)] for key in keys]
    assert all(reverse[reverse[i]] == i and types[reverse[i]][-1] == types[i][-1] for i in range(len(types)))
    assert sum(record[-1] for record in types) == 230400
    bounds = json.loads(BOUNDS.read_text())
    nums = single['single_column_screen']['column_leverage_numerators']
    assert single['positive_quotient']['inverse_denominator'] == D == bounds['full_denominator']
    assert [min(nums),max(nums)] == bounds['full_column_numerator_range'] == [2240036,3242772]
    assert [D-max(nums),D-min(nums)] == bounds['positive_slack_range']
    lo,hi = table['integer_range']
    assert [lo,hi] == bounds['component_bilinear_numerator_range'] == [-342896,858218]
    cross = [4*lo-D//60-2*(D//36),4*hi-D//60+2*(D//36)]
    assert cross == bounds['direct_cross_numerator_range']
    assert max(map(abs,cross))**2 == bounds['cross_square_direct_upper']
    assert (D-min(nums))**2 == bounds['slack_product_upper']
    assert bounds['cross_square_direct_upper']+bounds['slack_product_upper'] == bounds['conservative_determinant_absolute_upper']
    assert bounds['conservative_determinant_absolute_upper'] < 2**63-1
    assert max(nums)**2 == bounds['Cauchy_cross_square_upper']
    assert bounds['compatible_ordered_type_combinations'] == table['compatible_ordered_type_products'] == 33578176
    assert table['represented_ordered_full_column_pairs_including_self'] == 39168**2
    return data,types,reverse,bounds


def input_bytes(types,reverse):
    lines = [f'{len(types)} {D} 2240036 3242772']
    for i,t in enumerate(types):
        values = [i,reverse[i],*t[0],*t[1],t[2],t[3],t[4],*t[5],t[6],t[7],t[8]]
        assert len(values) == 17 and all(type(v) is int for v in values)
        lines.append(' '.join(map(str,values)))
    return ('\n'.join(lines)+'\n').encode()


def controls():
    gram = [[2,1],[1,2]]
    inverse_numerator = [[2,-1],[-1,2]]
    actual = [[1,0],[0,1],[1,1]]
    assert [[sum(h[i]*h[j] for h in actual) for j in range(2)] for i in range(2)] == gram
    tested = 0
    for h,k in combinations(actual,2):
        left = sum(h[i]*inverse_numerator[i][j]*h[j] for i in range(2) for j in range(2))
        right = sum(k[i]*inverse_numerator[i][j]*k[j] for i in range(2) for j in range(2))
        cross = sum(h[i]*inverse_numerator[i][j]*k[j] for i in range(2) for j in range(2))
        assert (3-left)*(3-right)-cross*cross >= 0
        remainder = [[gram[i][j]-h[i]*h[j]-k[i]*k[j] for j in range(2)] for i in range(2)]
        assert remainder[0][0] >= 0 and remainder[1][1] >= 0
        assert remainder[0][0]*remainder[1][1]-remainder[0][1]**2 >= 0
        tested += 1
    assert (3-2)**2-2**2 == -3
    assert sum(sum(row) for row in gram)-2*2**2 == -2
    return {'actual_incidence_positive_pairs':tested,
            'duplicate_column_negative_Schur_numerator':-3,
            'duplicate_column_direct_negative_value':-2,
            'duplicate_self_control_not_exported_as_a_distinct_column_conflict':True,
            'solver_called':False}


def prepare(path,input_path):
    assert not path.exists() and not input_path.exists()
    started = time.monotonic()
    data,types,reverse,bounds = load()
    raw = input_bytes(types,reverse)
    input_path.write_bytes(gzip.compress(raw,mtime=0))
    record = {'status':'exact complete type input and int64 bounds prepared; classification not run',
              'source_sha256':digest(Path(__file__)),'native_source_sha256':digest(NATIVE),
              'model_preparation_sha256':TYPE_SHA,'bounds_sha256':BOUNDS_SHA,
              'compressed_input':portable(input_path),'compressed_input_sha256':digest(input_path),
              'raw_input_sha256':hashlib.sha256(raw).hexdigest(),'raw_input_bytes':len(raw),
              'component_pair_types':len(types),'represented_component_ordered_pairs':230400,
              'compatible_ordered_type_combinations':33578176,
              'represented_full_ordered_pairs_including_self':39168**2,
              'self_full_columns':39168,'nonself_full_unordered_pairs':39168*39167//2,
              'classification_flags':FLAGS,'arithmetic_bounds':bounds,
              'controls':controls(),
              'no_fixed_incidence_designs':True,'no_graph_symmetry_assumption':True,
              'elapsed_seconds':time.monotonic()-started}
    path.write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps(record,indent=2),flush=True)


def predicate(a,b):
    assert all(x+y == 2 for x,y in zip(a[0],b[0])) and all(x+y == 2 for x,y in zip(a[1],b[1]))
    dp = [x-1 for x in a[0]]
    dq = [x-1 for x in a[1]]
    nh = 2*(a[2]+b[2])-D//60-(D//36)*sum(x*x for x in dp)
    nk = 2*(a[3]+b[3])-D//60-(D//36)*sum(x*x for x in dq)
    cross = 2*(a[4]+b[4])-D//60-(D//36)*sum(x*y for x,y in zip(dp,dq))
    assert 2240036 <= nh <= 3242772 and 2240036 <= nk <= 3242772
    assert cross*cross <= nh*nk
    determinant = (D-nh)*(D-nk)-cross*cross
    overlap_a,overlap_b = sum(a[5]),sum(b[5])
    self_pair = overlap_a == overlap_b == 3
    flags = [overlap_a == 3 or overlap_b == 3,overlap_a+overlap_b >= 3,
             bool(a[6] or b[6]),sum(x*y for x,y in zip(a[5],b[5])) > 0,bool(a[7] or b[7])]
    mask = sum(int(value) << i for i,value in enumerate(flags))
    return nh,nk,cross,determinant,self_pair,mask


def validate_progress(progress,summary,types,single):
    groups = defaultdict(list)
    for t in types:
        groups[tuple(t[0]),tuple(t[1])].append(t)
    expected_keys = sorted(groups)
    assert len(progress) == len(expected_keys) == summary['groups_finished'] == 49
    total_types = total_pairs = total_self = 0
    for row,(p,q) in zip(progress,expected_keys):
        opposite = tuple(2-x for x in p),tuple(2-x for x in q)
        first,second = groups[p,q],groups[opposite]
        total_types += len(first)*len(second)
        total_pairs += sum(t[-1] for t in first)*sum(t[-1] for t in second)
        total_self += sum(t[-1] for t in first if sum(t[5]) == 3)*sum(t[-1] for t in second if sum(t[5]) == 3)
        assert row['stage'] == 'group' and row['completed'] is True
        assert (row['p_code'],row['q_code']) == (9*p[0]+3*p[1]+p[2],9*q[0]+3*q[1]+q[2])
        assert (row['type_combinations'],row['weighted_ordered_pairs'],row['self_ordered_pairs']) == (total_types,total_pairs,total_self)
    assert summary['status'] == 'COMPLETE'
    assert total_types == summary['type_combinations'] == 33578176
    assert total_pairs == summary['weighted_ordered_pairs'] == 1534132224
    assert total_self == summary['self_ordered_pairs'] == 39168
    assert sum(summary['all_nonself_ordered_counts_by_mask'])+total_self == total_pairs
    assert all(value % 2 == 0 for name in ('all_nonself_ordered_counts_by_mask','negative_nonself_ordered_counts_by_mask')
               for value in summary[name])
    assert summary['negative_duplicate_self_columns'] == sum(2*n > D for n in single['single_column_screen']['column_leverage_numerators'])


def read_predicates(path):
    with gzip.open(path,'rb') as stream:
        while chunk := stream.read(8*8192):
            assert len(chunk) % 8 == 0
            yield from struct.iter_unpack('<II',chunk)


def validate_predicates(path,types,reverse,summary):
    count = expanded = unordered = 0
    previous = None
    selected_samples = set()
    targets = {0,summary['canonical_new_predicates']//2,summary['canonical_new_predicates']-1}
    raw_hash = hashlib.sha256()
    for ids in read_predicates(path):
        assert previous is None or previous < ids
        previous = ids
        a,b = ids
        assert 0 <= a < len(types) and 0 <= b < len(types)
        assert ids <= (reverse[a],reverse[b])
        nh,nk,cross,det,self_pair,mask = predicate(types[a],types[b])
        assert not self_pair and mask == 0 and det < 0
        orbit = 1 if ids == (reverse[a],reverse[b]) else 2
        weight = types[a][-1]*types[b][-1]
        assert (orbit*weight) % 2 == 0
        if count in targets:
            selected_samples.add(ids)
        count += 1
        expanded += orbit
        unordered += orbit*weight//2
        raw_hash.update(struct.pack('<II',*ids))
    assert count == summary['canonical_new_predicates']
    assert expanded == summary['negative_nonself_type_counts_by_mask'][0]
    assert unordered == summary['new_unordered_full_column_pairs']
    assert 2*unordered == summary['negative_nonself_ordered_counts_by_mask'][0]
    if count:
        a,b = summary['minimum_new_type_ids']
        selected_samples.add(min((a,b),(reverse[a],reverse[b])))
    return {'canonical_predicates_checked':count,'expanded_ordered_type_predicates':expanded,
            'represented_unordered_full_column_conflicts':unordered,
            'raw_predicate_sha256':raw_hash.hexdigest(),'raw_predicate_bytes':8*count,
            'all_retained_predicates_have_mask0_and_negative_exact_determinant':True,
            'sample_type_pairs':[list(p) for p in sorted(selected_samples)]}


def primitive(vector):
    divisor = gcd(*(abs(v) for v in vector))
    assert divisor > 0
    answer = [v//divisor for v in vector]
    if next(v for v in answer if v) < 0:
        answer = [-v for v in answer]
    return answer


def residual_value(gram,vector,columns):
    before = sum(vector[i]*sum(g*vector[j] for j,g in enumerate(row)) for i,row in enumerate(gram))
    dots = [sum(vector[i] for i in column) for column in columns]
    return before,dots,before-sum(x*x for x in dots)


def sample_controls(data,types,samples):
    domain,core,gram,pairs,columns,conflicts,single = data
    if not samples:
        return []
    triples = domain['signature_domain']
    targets = {i for pair in samples for i in pair}
    index = {type_key(types[i]):i for i in targets}
    inv = single['bilinear_reduction']['component_inverse_numerator']
    vectors = [[sum(row[v] for v in h) for row in inv] for h in triples]
    diagonal = [sum(vectors[i][v] for v in h) for i,h in enumerate(triples)]
    motif_set = {tuple(item['columns']) for name in ('F_conflicts','prism_conflicts') for item in conflicts[name]}
    found = {}
    for a,h in enumerate(triples):
        p = preparation.gram_screen.profile(h)
        for c,k in enumerate(triples):
            overlap = sorted(set(h)&set(k))
            key = (p,preparation.gram_screen.profile(k),diagonal[a],diagonal[c],sum(vectors[a][v] for v in k),
                   tuple(sum(v//6 == f for v in overlap) for f in range(3)),
                   int(any(domain['Gram'][i][j] == 1 for i,j in combinations(overlap,2))),
                   int(tuple(sorted((a,c))) in motif_set))
            if key in index:
                found.setdefault(index[key],(a,c))
        if len(found) == len(targets):
            break
    assert set(found) == targets
    q = single['positive_quotient']
    keep,Q = q['kept_coordinates'],q['inverse_numerator']
    lookup = {v:i for i,v in enumerate(keep)}
    column_lookup = {tuple(pair):i for i,pair in enumerate(pairs)}
    controls = []
    for ia,ib in samples:
        a,c = found[ia]
        b,d = found[ib]
        nh,nk,cross,det,self_pair,mask = predicate(types[ia],types[ib])
        assert mask == 0 and not self_pair and det < 0
        indices = [column_lookup[a,b],column_lookup[c,d]]
        h,k = [columns[i] for i in indices]
        assert len(set(h)&set(k)) <= 2
        assert all(gram[i][j] != 1 for i,j in combinations(sorted(set(h)&set(k)),2))
        x = [lookup[v] for v in h if v in lookup]
        y = [lookup[v] for v in k if v in lookup]
        qx = [sum(row[j] for j in x) for row in Q]
        qy = [sum(row[j] for j in y) for row in Q]
        assert sum(qx[j] for j in x) == nh and sum(qy[j] for j in y) == nk
        assert sum(qx[j] for j in y) == cross
        vector = [0]*39
        for v,left,right in zip(keep,qx,qy):
            vector[v] = cross*left+(D-nh)*right
        vector = primitive(vector)
        assert residual_value(gram,vector,[h,k])[-1] < 0
        maximum = max(map(abs,vector))
        scale_used = None
        for scale in range(1,129):
            rounded = [(2*v*scale+maximum)//(2*maximum) for v in vector]
            if any(rounded) and residual_value(gram,rounded,[h,k])[-1] < 0:
                vector = primitive(rounded)
                scale_used = scale
                break
        quadratic,dots,value = residual_value(gram,vector,[h,k])
        assert value < 0
        partial = list(core)+[0,0]
        for new,column in ((39,h),(40,k)):
            for v in column:
                preparation.components.edge(partial,new,v)
        assert preparation.components.caps(partial)
        controls.append({'component_type_ids':[ia,ib],'component_members':[[a,c],[b,d]],
                         'full_column_indices':indices,'full39_columns':[h,k],
                         'Gram_leverage_numerators':[nh,nk],'inverse_cross_numerator':cross,
                         'Schur_determinant_numerator':det,'elementary_conflict_mask':mask,
                         'known41_vertex_caps_hold':True,'negative_vector':vector,
                         'negative_vector_maximum':max(map(abs,vector)),'rounding_scale_if_used':scale_used,
                         'Gram_quadratic_value':quadratic,'column_dot_products':dots,
                         'negative_remainder_value':value})
    return controls


def compile_and_run(prepared,input_raw,directory,seconds):
    started = time.monotonic()
    binary = directory/'classifier'
    compilation = subprocess.run(['g++','-O3','-std=c++17','-Wall','-Wextra','-pedantic',str(NATIVE),'-o',str(binary)],
                                 capture_output=True,text=True,timeout=min(30,seconds),check=False)
    (directory/'compile.log').write_text(compilation.stdout+compilation.stderr)
    assert compilation.returncode == 0
    input_path,predicates = directory/'types.txt',directory/'new-types.bin'
    input_path.write_bytes(input_raw)
    log,errors = directory/'classification.jsonl',directory/'classification.stderr.log'
    remaining = seconds-(time.monotonic()-started)
    assert remaining > 0
    try:
        with log.open('w') as output,errors.open('w') as error:
            run = subprocess.run([str(binary),str(input_path),str(predicates),str(remaining)],
                                 stdout=output,stderr=error,timeout=remaining,check=False)
    except subprocess.TimeoutExpired:
        return {'status':'INCOMPLETE: native hard wall limit reached','elapsed_seconds':time.monotonic()-started},None
    records = [json.loads(line) for line in log.read_text().splitlines()]
    assert records
    summary = records[-1]
    if run.returncode != 0 or summary.get('status') != 'COMPLETE':
        return {'status':'INCOMPLETE: native classification did not complete','returncode':run.returncode,
                'native_last_record':summary,'elapsed_seconds':time.monotonic()-started},None
    assert predicates.stat().st_size == 8*summary['canonical_new_predicates']
    return {'status':'COMPLETE','native_summary':summary,'incremental_groups':records[:-1],
            'native_source_sha256':digest(NATIVE),'native_binary_sha256':digest(binary),
            'compile_log_sha256':digest(directory/'compile.log'),
            'native_log_sha256':digest(log),'native_stderr_sha256':digest(errors),
            'elapsed_compile_and_classification_seconds':time.monotonic()-started},predicates


def classify(preparation_path,directory,seconds):
    assert not directory.exists() and 0 < seconds <= 120
    directory.mkdir(parents=True)
    started = time.monotonic()
    prepared = json.loads(preparation_path.read_text())
    assert prepared['source_sha256'] == digest(Path(__file__)) and prepared['native_source_sha256'] == digest(NATIVE)
    assert prepared['model_preparation_sha256'] == TYPE_SHA and prepared['bounds_sha256'] == BOUNDS_SHA
    data,types,reverse,bounds = load()
    raw = input_bytes(types,reverse)
    assert hashlib.sha256(raw).hexdigest() == prepared['raw_input_sha256']
    compressed = ROOT/prepared['compressed_input']
    assert digest(compressed) == prepared['compressed_input_sha256'] and gzip.decompress(compressed.read_bytes()) == raw
    remaining = seconds-(time.monotonic()-started)
    assert remaining > 0
    native,raw_predicates = compile_and_run(prepared,raw,directory,remaining)
    certificate = {'status':native['status'],'source_sha256':digest(Path(__file__)),
                   'native_source_sha256':digest(NATIVE),'preparation':portable(preparation_path),
                   'preparation_sha256':digest(preparation_path),'budget_seconds':seconds,
                   'native':native,'classification_flags':FLAGS,
                   'no_SAT_query':True,'full_column_pair_exported':False,'whole_component_pair_excluded':False}
    if raw_predicates is not None:
        validate_progress(native['incremental_groups'],native['native_summary'],types,data[-1])
        path = directory/'new-type-predicates.bin.gz'
        with raw_predicates.open('rb') as source,path.open('wb') as output:
            with gzip.GzipFile(fileobj=output,mode='wb',filename='',mtime=0) as zipped:
                shutil.copyfileobj(source,zipped)
        checked = validate_predicates(path,types,reverse,native['native_summary'])
        controls = sample_controls(data,types,checked['sample_type_pairs'])
        mask_counts = native['native_summary']['negative_nonself_ordered_counts_by_mask']
        reasons = Counter()
        for mask,value in enumerate(mask_counts):
            reason = next((FLAGS[i] for i in range(5) if mask >> i & 1),'new beyond all listed immediate conflicts')
            reasons[reason] += value//2
        certificate.update(status='complete exact two-column classification with all retained predicates replayed',
                           predicate_file=portable(path),predicate_file_sha256=digest(path),
                           predicate_replay=checked,full39_negative_vector_controls=controls,
                           disjoint_first_reason_negative_pair_counts=dict(reasons),
                           all_negative_unordered_pairs=sum(mask_counts)//2,
                           new_negative_unordered_pairs=checked['represented_unordered_full_column_conflicts'],
                           no_independence_from_full_Gram_equations_claimed=True)
        raw_predicates.unlink()
    certificate['elapsed_seconds']=time.monotonic()-started
    path = directory/'certificate.json'
    path.write_text(json.dumps(certificate,indent=2)+'\n')
    print(json.dumps({k:v for k,v in certificate.items() if k not in ('native','full39_negative_vector_controls')},indent=2),flush=True)


def replay(certificate_path,output):
    assert not output.exists()
    saved = json.loads(certificate_path.read_text())
    assert saved['source_sha256'] == digest(Path(__file__)) and saved['native_source_sha256'] == digest(NATIVE)
    assert saved['status'] == 'complete exact two-column classification with all retained predicates replayed'
    preparation_path = ROOT/saved['preparation']
    assert digest(preparation_path) == saved['preparation_sha256']
    data,types,reverse,bounds = load()
    validate_progress(saved['native']['incremental_groups'],saved['native']['native_summary'],types,data[-1])
    path = ROOT/saved['predicate_file']
    assert digest(path) == saved['predicate_file_sha256']
    checked = validate_predicates(path,types,reverse,saved['native']['native_summary'])
    assert checked == saved['predicate_replay']
    controls = sample_controls(data,types,checked['sample_type_pairs'])
    assert controls == saved['full39_negative_vector_controls']
    report = {'status':'complete type input, incremental coverage, all retained predicates and full39 integer controls replayed',
              'source_sha256':digest(Path(__file__)),'certificate_sha256':digest(certificate_path),
              'retained_type_predicates':checked['canonical_predicates_checked'],
              'new_unordered_full_column_conflicts':checked['represented_unordered_full_column_conflicts'],
              'full39_negative_vector_controls':len(controls),
              'native_complete_classification_rerun':False,'solver_called':False}
    output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2),flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command',required=True)
    prep = commands.add_parser('prepare')
    prep.add_argument('--manifest',type=Path,required=True)
    prep.add_argument('--input',type=Path,required=True)
    run = commands.add_parser('classify')
    run.add_argument('--preparation',type=Path,required=True)
    run.add_argument('--directory',type=Path,required=True)
    run.add_argument('--seconds',type=float,default=120)
    check = commands.add_parser('replay')
    check.add_argument('--certificate',type=Path,required=True)
    check.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    if args.command == 'prepare':
        prepare(args.manifest.resolve(),args.input.resolve())
    elif args.command == 'classify':
        classify(args.preparation.resolve(),args.directory.resolve(),args.seconds)
    else:
        replay(args.certificate.resolve(),args.output.resolve())
