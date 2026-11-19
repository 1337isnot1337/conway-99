"""No-import source controls for the two-cover row-generation adaptation."""
import argparse
import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OLD = 'experiments/workspace/rook_case4_face99_cover_generation.py'
NEW = 'experiments/workspace/rook_case4_face99_parity_cover_generation.py'
SUBSTITUTIONS = 'experiments/logs/grids-and-triangles/rook-case4-face99-parity-driver-substitutions.json'
HASHES = {
    OLD:'53baba0038f51dd8439d14b27378663febc45cf90917ecb26524e0f6f275adbf',
    NEW:'c7459874bed464e062caee2fe23be9221cfde03ae979a33f8d54e1a305fb07fd',
    SUBSTITUTIONS:'dc7ae75c919f0b8db566791cf48f34418e81dc4605193ca84c72dc624e672a05',
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def prove():
    data = {}
    for path,expected in HASHES.items():
        raw=(ROOT/path).read_bytes()
        assert sha(raw)==expected,path
        data[path]=raw.decode()
    changes=json.loads(data[SUBSTITUTIONS])
    changed=data[OLD]
    for item in changes['replacements']:
        assert changed.count(item['old'])==1
        changed=changed.replace(item['old'],item['new'])
    assert changed==data[NEW]
    old,new=map(ast.parse,(data[OLD],data[NEW]))
    functions=lambda tree:{node.name:ast.dump(node,include_attributes=False)
        for node in tree.body if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef))}
    before,after=functions(old),functions(new)
    assert before.keys()==after.keys()
    identical=sorted(name for name in before if before[name]==after[name])
    delta=sorted(set(before)-set(identical))
    assert delta==['definition','initial_row_ids','load_inputs','prepare','reconstruct_bound','replay','source_bindings']
    assert all(name in identical for name in ('run','extend','full_float_matrix','inspect_numeric_point',
        'reconstruct_primal','expanded_numeric','checked_preparation','cold_arrays','preflight_replay'))
    assignment=lambda tree,name:next(ast.literal_eval(node.value) for node in tree.body
        if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in node.targets))
    assert assignment(old,'LIMITS')==assignment(new,'LIMITS')
    # With the two rows appended before max-min extensions, the old coordinate
    # cover pool stays exactly the same. This is a pure row-ID partition check.
    native,parent,base,rows=1966,167935,167937,169052
    initial=list(range(native))+list(range(parent,rows))
    pool=list(range(native,parent))
    assert len(initial)==3083 and len(pool)==165969
    assert set(initial).isdisjoint(pool) and set(initial)|set(pool)==set(range(rows))
    assert [parent,parent+1]==list(range(parent,base))
    assert len(range(base,rows))==1115
    return {'status':'PASS: exact source adaptation, unchanged run semantics and complete row-ID partition',
        'source_sha256':sha(Path(__file__).read_bytes()),'subject_bindings':HASHES,
        'explicit_replacements':len(changes['replacements']),
        'identical_function_count':len(identical),'identical_functions':identical,
        'changed_functions':delta,'unchanged_limits':assignment(new,'LIMITS'),
        'initial_rows':3083,'coordinate_cover_pool':165969,'full_rows':169052,
        'new_covers_always_active':True,'subject_imported':False,
        'model_rebuilt':False,'optimizer_calls':0}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    assert not args.output.exists()
    result=prove()
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
