"""Optimizer-free AST check of face81 driver's reused exact/query functions."""
import argparse
import ast
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
BINDINGS={
    'rook_case4_face81_cover_generation.py':'f9aabb56194dc875b4f196c125e14dddceb25823a27b903fb597862b4c8a4efc',
    'rook_case4_cover_generation.py':'6fb1b38194b8a5614ab7db219150dcc458f307b8a1dfb20f6fd55cd77b6325f2',
    'rook_case4_maxmin_query.py':'f5c664a20983a9a5f8a6601fe67f1d00aed701b29751b77b543ee3aa3afdd322',
}


def function(source,name):
    node=next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name==name)
    return '\n'.join(source.splitlines()[node.lineno-1:node.end_lineno])+'\n'


def adapt(source):
    for name in ('BASE_ROWS','SELECTORS','VARIABLES','ROWS','NONZEROS'):
        source=source.replace('frozen.'+name,name)
    source=source.replace(', compression_path','')
    source=source.replace('frozen.reconstruct_bound','reconstruct_bound')
    source=source.replace('frozen.reconstruct_primal','reconstruct_primal')
    source=source.replace('complete original matrix, exact compression and bounded prefix transcript',
                          'complete face81 matrix, exact zero proofs and bounded prefix transcript')
    return source


def check():
    sources={}
    for name,expected in BINDINGS.items():
        raw=(HERE/name).read_bytes()
        assert hashlib.sha256(raw).hexdigest()==expected
        sources[name]=raw.decode()
    new=sources['rook_case4_face81_cover_generation.py']
    old=sources['rook_case4_cover_generation.py']
    original=sources['rook_case4_maxmin_query.py']
    checked=[]
    for name in ('extend','full_float_matrix','inspect_numeric_point',
                 'expanded_numeric','run','replay','main','reconstruct_bound','reconstruct_primal'):
        parent=original if name in ('extend','reconstruct_bound','reconstruct_primal') else old
        expected=adapt(function(parent,name))
        if name=='main':
            expected=expected.replace("        c.add_argument('--compression', type=Path, required=True)\n",'')
            expected=expected.replace('a.compression, ','').replace('frozen.recovery.ROOT','builder.recovery.ROOT')
        if name=='reconstruct_bound':
            expected=expected.replace('complete case4 real selector relaxation with every native row and coordinate cover',
                'complete case4 real selector relaxation on the proved81-zero face with every native row and coordinate cover')
        assert ast.dump(ast.parse(function(new,name)),include_attributes=False)==ast.dump(ast.parse(expected),include_attributes=False),name
        checked.append(name)
    for name in ('BASE_ROWS','SELECTORS','VARIABLES','ROWS','NONZEROS'):
        assert 'frozen.'+name not in new
    tree=ast.parse(new)
    assigns=[n for n in tree.body if isinstance(n,ast.Assign)]
    aliases=[]
    for n in assigns:
        if isinstance(n.value,ast.Attribute) and isinstance(n.value.value,ast.Name) and n.value.value.id=='previous':
            aliases.append([n.targets[0].id,n.value.attr])
    assert ['native_once','native_once'] in aliases
    tuple_alias=next(n for n in assigns if isinstance(n.targets[0],ast.Tuple)
                     and [t.id for t in n.targets[0].elts]==['set_model','append_rows','choose_rows'])
    assert ast.dump(tuple_alias.value)==ast.dump(ast.parse('(previous.set_model,previous.append_rows,previous.choose_rows)',mode='eval').body)
    return {'status':'PASS: exact AST reuse after explicit dimension/interface substitutions',
        'source_bindings':BINDINGS,'functions_checked':checked,
        'unchanged_imported_native_helpers':['set_model','append_rows','choose_rows','native_once'],
        'old_dimension_constants_absent':True,
        'allowed_changes':['bind the new face model and its dimensions',
            'remove the old compression argument; every remaining cover is in the new pool',
            'call dimension-adapted exact reconstruction','update the explicitly stated face scope'],
        'new_loading_preparation_and_definition_functions_require_separate_source_review':True,
        'subject_imported':False,'model_rebuilt':False,'optimizer_called':False}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    assert not args.output.exists()
    report=check()
    report['control_source_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    main()
