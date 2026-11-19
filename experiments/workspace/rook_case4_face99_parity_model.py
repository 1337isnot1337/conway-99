"""Append exactly two proved integer covers to the complete face99 real LP.

The old 167935 rows and all 1115 surviving selector coordinates are unchanged.
Preparation and cold replay call no optimizer. These new rows are necessary
for nonnegative integral incidences; the resulting feasible set is a real
relaxation, not an assertion that the old real feasible set is preserved.
"""
import argparse
import hashlib
import json
from pathlib import Path
import resource
import signal
import time

import numpy as np

import rook_case4_face99_model as parent
import rook_case4_face99_parity_covers as covers

recovery = parent.recovery
ROOT = recovery.ROOT
BASE = 'experiments/logs/grids-and-triangles/'
PARENT_SHA = '613e2de31570d56a2b1b52a164158a7ed9b80b4f8f834e550fbbc9c6e608e078'
COVERS_SHA = '2420988060354e9e77806de86040a566ece9d2f5af27b1a216135ea7e86495cc'
INPUTS = {
    'parent_model': (BASE+'rook-case4-face99-model01/model.json', 'c417a08853096bbb7a6d8148aca80a5f08249c19f2978f3f49a86ec0c20c301b'),
    'parent_arrays': (BASE+'rook-case4-face99-model01/arrays.npz', '7e75bbb360d91d6a4a424262c2c61ad5d7e0e13942a7b80a8ca39ec731ebf4af'),
    'parent_cold': (BASE+'rook-case4-face99-model01-cold-replay.json', '3ff14b5eb5ccda648e5f4f811ae9c9b2119013083670cf30ec7d5dea5afdccec'),
    'cover_certificate': (BASE+'rook-case4-face99-parity-cover-certificate.json', '644a7f637fb8ea42fd49a99487ead6eb544370ae463c9e303e86e8934d2f1a81'),
    'cover_replay': (BASE+'rook-case4-face99-parity-cover-replay.json', 'f7a2a30c4fc0930d08afd31a4fbb16184e08074e202ee3fc42b11954d3e6f79b'),
}
SELECTORS, PARENT_ROWS, ROWS = 1115, 167935, 167937
PARENT_NONZEROS, NONZEROS = 11012058, 11012142
NATIVE_ROWS, COVERS, NEW_COVERS = 1966, 165969, 2
SECONDS, RSS_KIB = 180, 1048576


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return recovery.canonical(value)


def source_bindings():
    assert digest(Path(parent.__file__).read_bytes()) == PARENT_SHA
    assert digest(Path(covers.__file__).read_bytes()) == COVERS_SHA
    old = parent.source_bindings()
    return dict(old, builder_sha256=digest(Path(__file__).read_bytes()),
                unchanged_parent_builder_sha256=PARENT_SHA,
                direct_integer_cover_verifier_sha256=COVERS_SHA)


def inputs(root):
    source_bindings()
    for name, (path, expected) in INPUTS.items():
        assert digest((root/path).read_bytes()) == expected, name
    model, arrays = parent.load(root/INPUTS['parent_model'][0], root/INPUTS['parent_arrays'][0])
    cold = json.loads((root/INPUTS['parent_cold'][0]).read_bytes())
    assert cold['model_sha256'] == INPUTS['parent_model'][1]
    assert cold['all_omission_witnesses_replayed']
    proof = covers.prove()
    assert canonical(proof) == canonical(json.loads((root/INPUTS['cover_certificate'][0]).read_bytes()))
    replay = json.loads((root/INPUTS['cover_replay'][0]).read_bytes())
    assert replay['certificate_sha256'] == INPUTS['cover_certificate'][1]
    assert replay['original_equation_counts'] == [33,35]
    assert replay['odd_right_hand_sides'] == [45,47]
    assert len(proof['new_linear_rows']) == 2
    assert model['fixed_zero_columns'] == json.loads((root/covers.INPUTS['zeros'][0]).read_bytes())['seed_zero_columns']
    return model, arrays, proof


def integer_stream(arrays, stop):
    result = hashlib.sha256()
    pair_dtype = np.dtype([('column','<u4'), ('coefficient','<i8')], align=False)
    assert pair_dtype.itemsize == recovery.TERM.size == 12
    for r in range(stop):
        a,b = map(int, arrays['row_pointers'][r:r+2])
        result.update(recovery.HEADER.pack(int(arrays['row_origin_kind'][r]),
            int(arrays['row_origin_index'][r]),int(arrays['row_lower'][r]),
            int(arrays['row_upper'][r]),b-a))
        terms = np.empty(b-a,dtype=pair_dtype)
        terms['column'] = arrays['column_indices'][a:b]
        terms['coefficient'] = arrays['coefficients'][a:b]
        result.update(terms.tobytes())
    return result.hexdigest()


def append_covers(old, base, proof):
    kept = list(map(int,base['original_column_ids']))
    position = {a:j for j,a in enumerate(kept)}
    assert len(kept) == SELECTORS
    appended = []
    for row in proof['new_linear_rows']:
        assert row['lower'] == 1 and row['upper'] == 42 and len(row['terms']) == 42
        assert all(c == 1 and a in position for a,c in row['terms'])
        terms = [[position[a],c] for a,c in row['terms']]
        assert terms == sorted(terms) and len(set(a for a,c in terms)) == 42
        appended.append(terms)
    arrays = {
        'coefficients':np.concatenate((base['coefficients'],np.ones(84,dtype='<i8'))),
        'column_indices':np.concatenate((base['column_indices'],np.asarray([a for row in appended for a,c in row],dtype='<i4'))),
        'row_pointers':np.concatenate((base['row_pointers'],np.asarray([PARENT_NONZEROS+42,PARENT_NONZEROS+84],dtype='<i8'))),
        'row_lower':np.concatenate((base['row_lower'],np.ones(2,dtype='<i8'))),
        'row_upper':np.concatenate((base['row_upper'],np.full(2,42,dtype='<i8'))),
        'row_origin_kind':np.concatenate((base['row_origin_kind'],np.full(2,2,dtype='u1'))),
        'row_origin_index':np.concatenate((base['row_origin_index'],np.arange(2,dtype='<i4'))),
        'original_column_ids':base['original_column_ids'].copy(),
    }
    for name, original in base.items():
        assert np.array_equal(arrays[name][:len(original)],original), ('unchanged prefix',name)
    assert len(arrays['coefficients']) == len(arrays['column_indices']) == NONZEROS
    assert len(arrays['row_pointers']) == ROWS+1 and arrays['row_pointers'][-1] == NONZEROS
    assert integer_stream(arrays,PARENT_ROWS) == old['canonical_integer_stream_sha256']
    # All inherited omission witnesses and all original-domain descriptions stay
    # available in the new record; no parent row is removed or reordered.
    record = {k:v for k,v in old.items() if k not in
              ('arrays','controls','preparation_seconds','peak_rss_kib')}
    record.update({
        'status':'complete face99 LP plus two exact integer covers prepared; no optimizer',
        'source_bindings':source_bindings(),'parent_input_bindings':{k:list(v) for k,v in INPUTS.items()},
        'rows':ROWS,'nonzeros':NONZEROS,
        'unchanged_parent_rows':PARENT_ROWS,'unchanged_parent_nonzeros':PARENT_NONZEROS,
        'unchanged_parent_stream_sha256':old['canonical_integer_stream_sha256'],
        'added_integer_covers':NEW_COVERS,'added_integer_cover_nonzeros':84,
        'added_integer_cover_row_ids':[PARENT_ROWS,PARENT_ROWS+1],
        'new_cover_original_supports':[p['cover_support'] for p in proof['proofs']],
        'new_cover_original_Gram_equation_counts':[33,35],
        'new_cover_original_integer_right_hand_sides':[45,47],
        'new_rows_necessary_for_nonnegative_integer_incidences':True,
        'parent_real_feasible_set_preservation_claimed':False,
        'row_inventory':dict(old['row_inventory'],retained_integer_parity_cover=2),
        'canonical_integer_stream_sha256':integer_stream(arrays,ROWS),
        'canonical_integer_stream_format':old['canonical_integer_stream_format']+'; kind2 denotes the two integer-cover rows',
        'array_sha256':{name:digest(value.tobytes(order='C')) for name,value in arrays.items()},
        'uncompressed_array_bytes':sum(value.nbytes for value in arrays.values()),
        'all_parent_array_prefixes_equal':True,
    })
    return record,arrays


def build(root):
    saved,base,proof = inputs(root)
    rebuilt,current = parent.build(root)
    parent.compare_model(saved,rebuilt)
    assert set(base) == set(current)
    for name in base:
        assert np.array_equal(base[name],current[name]),('cold parent',name)
    return append_covers(rebuilt,current,proof)


def compare_model(saved,current):
    parent.compare_model(saved,current)


def load(model_path,arrays_path=None):
    model = json.loads(model_path.read_bytes())
    assert model['source_bindings'] == source_bindings()
    assert model['parent_input_bindings'] == {k:list(v) for k,v in INPUTS.items()}
    assert (model['columns'],model['rows'],model['nonzeros']) == (SELECTORS,ROWS,NONZEROS)
    assert model['unchanged_parent_rows'] == PARENT_ROWS and model['added_integer_covers'] == 2
    assert model['added_integer_cover_row_ids'] == [PARENT_ROWS,PARENT_ROWS+1]
    if arrays_path is None:
        arrays_path = model_path.parent/model['arrays']['path']
    assert digest(arrays_path.read_bytes()) == model['arrays']['sha256']
    with np.load(arrays_path,allow_pickle=False) as archive:
        arrays = {name:archive[name] for name in archive.files}
    assert {name:digest(value.tobytes(order='C')) for name,value in arrays.items()} == model['array_sha256']
    assert all(value.dtype.kind in 'iu' for value in arrays.values())
    assert list(map(int,arrays['original_column_ids'])) == [a for a in range(1214) if a not in set(model['fixed_zero_columns'])]
    assert len(model['fixed_zero_columns']) == 99 and not model['fixed_one_columns']
    assert len(arrays['coefficients']) == len(arrays['column_indices']) == NONZEROS
    assert len(arrays['row_pointers']) == ROWS+1 and arrays['row_pointers'][-1] == NONZEROS
    assert all(len(arrays[name]) == ROWS for name in ('row_lower','row_upper','row_origin_kind','row_origin_index'))
    assert np.all(arrays['row_origin_kind'][:NATIVE_ROWS] == 0)
    assert np.all(arrays['row_origin_kind'][NATIVE_ROWS:PARENT_ROWS] == 1)
    assert list(map(int,arrays['row_origin_kind'][PARENT_ROWS:])) == [2,2]
    for i,support in enumerate(model['new_cover_original_supports']):
        r = PARENT_ROWS+i
        a,b = map(int,arrays['row_pointers'][r:r+2])
        assert b-a == 42 and np.all(arrays['coefficients'][a:b] == 1)
        assert [int(arrays['original_column_ids'][j]) for j in arrays['column_indices'][a:b]] == support
        assert int(arrays['row_lower'][r]) == 1 and int(arrays['row_upper'][r]) == 42
    return model,arrays


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=('prepare','replay'))
    parser.add_argument('--directory',type=Path)
    parser.add_argument('--model',type=Path)
    parser.add_argument('--output',type=Path)
    parser.add_argument('--root',type=Path,default=ROOT)
    args = parser.parse_args()
    started = time.monotonic()
    def expired(_signum,_frame):
        raise TimeoutError('bounded180second exact parity overlay preparation/replay')
    old_handler = signal.signal(signal.SIGALRM,expired)
    signal.setitimer(signal.ITIMER_REAL,SECONDS)
    try:
        if args.mode == 'prepare':
            assert args.directory is not None and not args.directory.exists()
            args.directory.mkdir(parents=True)
            old,base,proof = inputs(args.root.resolve())
            model,arrays = append_covers(old,base,proof)
            path = args.directory/'arrays.npz'
            with path.open('wb') as stream:
                np.savez_compressed(stream,**arrays)
            model['arrays']={'path':'arrays.npz','sha256':digest(path.read_bytes()),'bytes':path.stat().st_size}
            model['preparation_seconds']=time.monotonic()-started
            model['peak_rss_kib']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            assert model['peak_rss_kib'] <= RSS_KIB
            recovery.write_json(args.directory/'model.json',model)
            loaded,stored = load(args.directory/'model.json',path)
            for name,value in arrays.items():
                assert np.array_equal(value,stored[name])
            output = args.directory/'preparation.json'
            status = 'PASS: exact unchanged parent prefix and two necessary integer covers prepared'
        else:
            assert args.model is not None and args.output is not None
            model,stored = load(args.model)
            current,arrays = build(args.root.resolve())
            compare_model(model,current)
            for name,value in arrays.items():
                assert np.array_equal(value,stored[name]),('cold overlay',name)
            output = args.output
            status = 'PASS: complete original domain and two integer-cover proofs rebuilt'
        report={'status':status,'source_bindings':source_bindings(),
            'model_sha256':digest((args.directory/'model.json' if args.mode=='prepare' else args.model).read_bytes()),
            'columns':SELECTORS,'rows':ROWS,'nonzeros':NONZEROS,
            'unchanged_parent_rows':PARENT_ROWS,'appended_integer_covers':2,
            'canonical_integer_stream_sha256':model['canonical_integer_stream_sha256'],
            'arrays':model['arrays'],'optimizer_calls':0,'case4_excluded':False,
            'seconds':time.monotonic()-started,
            'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
        assert report['peak_rss_kib'] <= RSS_KIB
        recovery.write_json(output,report)
    finally:
        signal.setitimer(signal.ITIMER_REAL,0)
        signal.signal(signal.SIGALRM,old_handler)
    print(json.dumps(report,indent=2),flush=True)


if __name__ == '__main__':
    main()
