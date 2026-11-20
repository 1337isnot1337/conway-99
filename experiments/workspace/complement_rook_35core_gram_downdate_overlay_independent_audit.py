"""Read-only byte and binding audit of the886-clause35-core overlay."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
LOGS=ROOT/'experiments/logs/grids-and-triangles'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    model_path=LOGS/'complement-rook-35core-case0002-gram-downdate-overlay-model.json'
    assert digest(model_path)=='ee602e06e7b94f91e210bccaa3636fbad746b5ab5098e9929cf9eae778194e32'
    model=json.loads(model_path.read_text())
    for name,expected in model['source_hashes'].items():
        assert digest(Path(__file__).with_name(name))==expected
    base_path=ROOT/model['base_model']
    assert digest(base_path)==model['base_model_sha256']
    base=json.loads(base_path.read_text())
    old,new=Path(base['cnf']),Path(model['cnf'])
    assert digest(old)==base['cnf_sha256']==model['base_cnf_sha256']
    assert digest(new)==model['cnf_sha256']=='f23dba5ab0cbb266dad36d99d4f7b8e226b2ee1e6bbe181b025612b9845b8db3'
    fragment=ROOT/model['binary_fragment']
    assert digest(fragment)==model['binary_fragment_sha256']
    direct_path=LOGS/'complement-rook-35core-case0002-gram-downdate-independent-audit.json'
    direct=json.loads(direct_path.read_text())
    assert direct['certificate_sha256']==model['certificate_sha256']
    assert direct['clause_fragment_sha256']==model['binary_fragment_sha256']
    assert direct['direct_integer_negative_vectors_checked']==886
    assert direct['audit_source_sha256']==digest(Path(__file__).with_name('complement_rook_35core_gram_downdate_independent_audit.py'))
    with old.open('rb') as first,new.open('rb') as second,fragment.open('rb') as extra:
        assert first.readline()==b'p cnf 114512 233919\n'
        assert second.readline()==b'p cnf 114512 234805\n'
        assert extra.readline()==b'p cnf 1287 886\n'
        for _ in range(233919):
            line=first.readline()
            assert line and second.readline()==line
        assert not first.read()
        expected=extra.read()
        assert expected.count(b'\n')==886 and second.read()==expected
    report={'status':'PASS: read-only exact original body and886 certified binary suffix',
            'audit_source_sha256':digest(Path(__file__)),'overlay_source_sha256':model['source_hashes']['complement_rook_35core_gram_downdate_overlay.py'],
            'overlay_model_sha256':digest(model_path),'overlay_cnf_sha256':digest(new),
            'base_cnf_sha256':digest(old),'direct_vector_audit_sha256':digest(direct_path),
            'unchanged_original_clause_lines':233919,'appended_binary_clause_lines':886,
            'new_auxiliary_variables':0,'CNF_rebuilt':False,'solver_called':False,
            'read_only_source_review':'Bindings, unchanged original domain/body, negative primary literal signs, fresh proof-enabled60-second solver, retained-input inclusion and full-rebuild proof replay are sound.',
            'scope':'One indexed35-core case2; no wider exclusion.'}
    output=LOGS/'complement-rook-35core-case0002-gram-downdate-overlay-independent-audit.json'
    assert not output.exists()
    output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2),flush=True)


if __name__=='__main__':
    main()
