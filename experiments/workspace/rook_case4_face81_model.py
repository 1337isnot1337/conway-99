"""Exact case4 selector LP on the proved81-zero face; preparation only.

All original2271 native rows and178533 coordinate covers are accounted for.
The70 Gram zeros use the frozen three/four-row proof;14 cover units complete
the81-column zero set. Only real-unit-box tautologies are omitted. No optimizer,
Boolean rounding, numerical support restriction or symmetry assumption occurs.
"""
import argparse
from array import array
from collections import Counter
import hashlib
import json
from pathlib import Path
import resource
import signal
import sys
import time

import numpy as np

import rook_case4_complete_lp_recovery as recovery
import rook_case4_four_gram_face as face

RECOVERY_SHA = 'e577327c9cc2471f119c755a49a179b9f94f1004a22de80152a4114787a7eec6'
FACE_SHA = '658a4665f156ec892824c4ea5896ee05bb0346fab62f9c3461deb10d2ccf0e46'
FACE_CERTIFICATE = 'experiments/logs/grids-and-triangles/rook-case4-four-gram-face-certificate.json'
FACE_CERT_SHA = 'c28347a46c0c9a0973e16487886d7b166f5bd008b7af2351ad4d7b4f0459cc50'
SELECTORS, ROWS, NONZEROS = 1133, 170831, 11390157
NATIVE_ROWS, NATIVE_NONZEROS, COVERS = 1984, 26358, 168847
SECONDS, RSS_KIB = 180, 1048576
EXPECTED_COUNTS = {
    'tautological_Gram':234, 'retained_Gram':396,
    'retained_original_signature':186,
    'retained_core_triple':1340, 'tautological_core_triple':25,
    'retained_Gram_conflict':4, 'tautological_Gram_conflict':26,
    'retained_uncapped_row_cut':58, 'tautological_uncapped_row_cut':2,
    'retained_cover':168847, 'tautological_cover':9686,
}


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return recovery.canonical(value)


def source_bindings():
    assert digest(Path(recovery.__file__).read_bytes()) == RECOVERY_SHA
    assert digest(Path(face.__file__).read_bytes()) == FACE_SHA
    return {'builder_sha256':digest(Path(__file__).read_bytes()),
            'published_input_recovery_sha256':RECOVERY_SHA,
            'four_Gram_proof_source_sha256':FACE_SHA,
            'four_Gram_certificate_sha256':FACE_CERT_SHA}


def checked_premises(root):
    binding = source_bindings()
    raw = (root/FACE_CERTIFICATE).read_bytes()
    assert digest(raw) == FACE_CERT_SHA
    proof = face.build(root/recovery.INPUTS['native_model']['path'])
    assert canonical(proof) == canonical(json.loads(raw))
    assert not proof['uses_integrality'] and not proof['uses_coordinate_covers']
    inventory, metadata, registry = recovery.checked_inputs(root)
    units, registry_check = recovery.audit_registry(registry, metadata)
    gram_zeros = proof['Gram_only_zero_columns_after_both_relations']
    zeros = sorted(set(gram_zeros)|set(units))
    assert len(gram_zeros) == 70 and len(units) == 14 and len(zeros) == 81
    assert len(set(gram_zeros)&set(units)) == 3
    return binding, inventory, registry, proof, registry_check, zeros


def build(root):
    assert sys.byteorder == 'little'
    binding, inventory, registry, proof, registry_check, zeros = checked_premises(root)
    original = recovery.original_rows(inventory)
    kept = [a for a in range(recovery.N) if a not in set(zeros)]
    assert len(kept) == SELECTORS
    position = {a:j for j,a in enumerate(kept)}
    active_bits = sum(1<<a for a in kept)
    coefficients, indices, pointers = array('q'), array('i'), array('q',[0])
    lower_bounds, upper_bounds = array('q'), array('q')
    kinds, identifiers = array('B'), array('i')
    counts, omitted_native, omitted_covers = Counter(), [], []
    stream = hashlib.sha256()
    maximum_coefficient = 0

    def append(kind, identifier, lower, upper, terms):
        nonlocal maximum_coefficient
        assert terms and terms == sorted(terms)
        assert len({a for a,c in terms}) == len(terms)
        assert all(0 <= a < SELECTORS and type(c) is int and c and -(1<<63) < c < 1<<63
                   for a,c in terms)
        assert -(1<<63) <= lower <= upper < 1<<63
        stream.update(recovery.HEADER.pack(kind,identifier,lower,upper,len(terms)))
        stream.update(b''.join(recovery.TERM.pack(a,c) for a,c in terms))
        coefficients.extend(c for a,c in terms)
        indices.extend(a for a,c in terms)
        pointers.append(len(indices))
        lower_bounds.append(lower)
        upper_bounds.append(upper)
        kinds.append(kind)
        identifiers.append(identifier)
        maximum_coefficient = max(maximum_coefficient,max(abs(c) for a,c in terms))

    for identifier,row in enumerate(original):
        terms,minimum,maximum,omitted = recovery.projected(
            row['terms'],row['lower'],row['upper'],position)
        if omitted:
            counts['tautological_'+row['family']] += 1
            omitted_native.append({'original_row':identifier,'family':row['family'],
                'box_minimum':minimum,'box_maximum':maximum,
                'original_lower':row['lower'],'original_upper':row['upper']})
        else:
            counts['retained_'+row['family']] += 1
            append(0,identifier,row['lower'],row['upper'],terms)
    assert len(lower_bounds) == NATIVE_ROWS and len(indices) == NATIVE_NONZEROS
    for identifier in range(178533):
        target,bits = recovery.registry_entry(registry,identifier)
        if target not in position:
            counts['tautological_cover'] += 1
            omitted_covers.append([identifier,target])
            continue
        support = bits & active_bits
        assert support and not (support>>target&1)
        terms = sorted([[position[target],-1]]+[[position[a],1]
                        for a in recovery.members(support)])
        counts['retained_cover'] += 1
        # This upper endpoint is itself a unit-box tautology. Tightening the
        # old trivial upper endpoint after substitution changes no real point.
        append(1,identifier,0,support.bit_count(),terms)
    assert dict(counts) == EXPECTED_COUNTS
    assert len(lower_bounds) == ROWS and len(coefficients) == len(indices) == NONZEROS
    assert len(pointers) == ROWS+1
    assert len(omitted_native) == 2271-NATIVE_ROWS and len(omitted_covers) == 9686
    arrays = {
        'coefficients':np.frombuffer(coefficients,dtype='<i8'),
        'column_indices':np.frombuffer(indices,dtype='<i4'),
        'row_pointers':np.frombuffer(pointers,dtype='<i8'),
        'row_lower':np.frombuffer(lower_bounds,dtype='<i8'),
        'row_upper':np.frombuffer(upper_bounds,dtype='<i8'),
        'row_origin_kind':np.frombuffer(kinds,dtype='u1'),
        'row_origin_index':np.frombuffer(identifiers,dtype='<i4'),
        'original_column_ids':np.asarray(kept,dtype='<u2'),
    }
    record = {
        'status':'complete exact81-zero-face selector LP prepared; no optimizer',
        'source_bindings':binding,'input_bindings':recovery.INPUTS,
        'primary_inventory_sha256':recovery.PRIMARY_SHA,
        'cover_certificate_sha256':recovery.COVER_CERTIFICATE_SHA,
        'four_Gram_certificate':{'path':FACE_CERTIFICATE,'sha256':FACE_CERT_SHA},
        'Gram_only_zero_columns':proof['Gram_only_zero_columns_after_both_relations'],
        'cover_unit_zero_columns':registry_check['unit_targets'],
        'fixed_zero_columns':zeros,'fixed_one_columns':[],
        'all_fixed_columns_proved_over_the_original_real_unit_box':True,
        'registry_check':registry_check,
        'case_index':4,'original_columns':1214,
        'columns':SELECTORS,'rows':ROWS,'nonzeros':NONZEROS,
        'retained_original_primary_rows':NATIVE_ROWS,
        'retained_native_nonzeros':NATIVE_NONZEROS,
        'retained_coordinate_covers':COVERS,
        'all2271_native_rows_and178533_covers_covered':True,
        'all60_uncapped_exterior_row_cuts_accounted_for':True,
        'row_inventory':dict(counts),
        'omitted_native_rows_exact_box_witnesses':omitted_native,
        'omitted_covers_fixed_zero_target_witnesses':omitted_covers,
        'cover_upper_endpoints_are_unit_box_tautologies':True,
        'canonical_integer_stream_format':'<BIqqI header(kind,original_id,lower,upper,nterms), then <Iq(reduced_column,coefficient)',
        'canonical_integer_stream_sha256':stream.hexdigest(),
        'maximum_absolute_integer_coefficient':maximum_coefficient,
        'finite_variable_bounds':{'lower':0,'upper':1},
        'row_bounds_are_finite_integers':True,
        'array_sha256':{name:digest(value.tobytes(order='C')) for name,value in arrays.items()},
        'uncompressed_array_bytes':sum(value.nbytes for value in arrays.values()),
        'numpy_version':np.__version__,'python_version':sys.version,
        'optimizer_or_solver_called':False,
        'integer_incidence_or_graph_constructed':False,'case4_excluded':False,
    }
    return record,arrays


def compare_model(saved,current):
    for key,value in current.items():
        if key not in ('numpy_version','python_version'):
            assert saved[key] == value,('rebuilt model field',key)


def load(model_path,arrays_path=None):
    binding=source_bindings()
    model=json.loads(model_path.read_text())
    assert model['source_bindings'] == binding
    assert (model['columns'],model['rows'],model['nonzeros']) == (SELECTORS,ROWS,NONZEROS)
    assert model['row_inventory'] == EXPECTED_COUNTS
    assert len(model['fixed_zero_columns']) == 81 and not model['fixed_one_columns']
    if arrays_path is None:
        arrays_path=model_path.parent/model['arrays']['path']
    assert digest(arrays_path.read_bytes()) == model['arrays']['sha256']
    with np.load(arrays_path,allow_pickle=False) as archive:
        arrays={name:archive[name] for name in archive.files}
    assert {name:digest(value.tobytes(order='C')) for name,value in arrays.items()} == model['array_sha256']
    assert all(value.dtype.kind in 'iu' for value in arrays.values())
    assert len(arrays['original_column_ids']) == SELECTORS
    assert len(arrays['coefficients']) == len(arrays['column_indices']) == NONZEROS
    assert len(arrays['row_pointers']) == ROWS+1
    assert len(arrays['row_lower']) == len(arrays['row_upper']) == ROWS
    assert arrays['row_pointers'][0] == 0 and arrays['row_pointers'][-1] == NONZEROS
    assert np.all(arrays['row_origin_kind'][:NATIVE_ROWS] == 0)
    assert np.all(arrays['row_origin_kind'][NATIVE_ROWS:] == 1)
    assert list(map(int,arrays['original_column_ids'])) == [a for a in range(1214) if a not in set(model['fixed_zero_columns'])]
    return model,arrays


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=['prepare','replay'])
    parser.add_argument('--root',type=Path,default=recovery.ROOT)
    parser.add_argument('--directory',type=Path)
    parser.add_argument('--model',type=Path)
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    started=time.monotonic()
    def deadline(_signum,_frame):
        raise TimeoutError('bounded180second exact face81 preparation/replay')
    old=signal.signal(signal.SIGALRM,deadline)
    signal.setitimer(signal.ITIMER_REAL,SECONDS)
    try:
        if args.mode=='prepare':
            assert args.directory is not None and not args.directory.exists()
            args.directory.mkdir(parents=True)
            control=recovery.controls()
            record,arrays=build(args.root.resolve())
            path=args.directory/'arrays.npz'
            temporary=args.directory/'arrays.npz.partial'
            with temporary.open('wb') as stream:
                np.savez_compressed(stream,**arrays)
            temporary.rename(path)
            with np.load(path,allow_pickle=False) as archive:
                assert set(archive.files) == set(arrays)
                for name,value in arrays.items():
                    assert np.array_equal(archive[name],value)
            record['arrays']={'path':'arrays.npz','sha256':digest(path.read_bytes()),'bytes':path.stat().st_size}
            record['controls']=control
            record['preparation_seconds']=time.monotonic()-started
            record['peak_rss_kib']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            assert record['peak_rss_kib'] <= RSS_KIB
            recovery.write_json(args.directory/'model.json',record)
            report={key:record[key] for key in ('status','source_bindings','columns','rows','nonzeros',
                'canonical_integer_stream_sha256','row_inventory','arrays','uncompressed_array_bytes',
                'controls','preparation_seconds','peak_rss_kib','optimizer_or_solver_called','case4_excluded')}
            report['model_sha256']=digest((args.directory/'model.json').read_bytes())
            recovery.write_json(args.directory/'preparation.json',report)
        else:
            assert args.model is not None and args.output is not None
            saved,stored=load(args.model)
            record,arrays=build(args.root.resolve())
            compare_model(saved,record)
            assert set(stored) == set(arrays)
            for name,value in arrays.items():
                assert np.array_equal(stored[name],value),('cold array',name)
            report={'status':'PASS: all published rows, exact81-zero proof and full face matrix rebuilt',
                'source_bindings':source_bindings(),'model_sha256':digest(args.model.read_bytes()),
                'columns':SELECTORS,'rows':ROWS,'nonzeros':NONZEROS,
                'canonical_integer_stream_sha256':record['canonical_integer_stream_sha256'],
                'all_omission_witnesses_replayed':True,'seconds':time.monotonic()-started,
                'optimizer_or_solver_called':False,'case4_excluded':False}
            recovery.write_json(args.output,report)
    finally:
        signal.setitimer(signal.ITIMER_REAL,0)
        signal.signal(signal.SIGALRM,old)
    print(json.dumps(report,indent=2),flush=True)


if __name__=='__main__':
    main()
