"""Exact one-bound delta and tiny propagation control; no case4 closure."""
import argparse
import ast
import hashlib
import json
from pathlib import Path

import rook_case4_face111_primary_closure as old
import rook_case4_face111_primary_closure_v2 as new

ROOT=Path(__file__).resolve().parents[2]
OLD_SHA='b3338d44b20342b645f2ebabe61ab3b6abc843933b798e1750f31103f6d1b103'
NEW_SHA='983d62f91f4bd7ce53e1a11897d41dbf3a093b7fd426659fce4069973caa169e'
SUB='experiments/logs/grids-and-triangles/rook-case4-face111-closure-v2-substitutions.json'
SUB_SHA='afeb3020233a06a9a981ca3c78b72321bc56fcba4bff8ad562ed3557357ff1dc'
FACE='experiments/logs/grids-and-triangles/rook-case4-face99-parity-face-certificate.json'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def prove():
    first,second=Path(old.__file__),Path(new.__file__)
    assert sha(first.read_bytes())==OLD_SHA and sha(second.read_bytes())==NEW_SHA
    change=(ROOT/SUB).read_bytes();assert sha(change)==SUB_SHA
    transformed=first.read_text()
    for item in json.loads(change)['replacements']:
        assert transformed.count(item['old'])==1
        transformed=transformed.replace(item['old'],item['new'])
    assert transformed==second.read_text()
    functions=lambda source:{n.name:ast.dump(n,include_attributes=False) for n in ast.parse(source).body if isinstance(n,ast.FunctionDef)}
    f,g=functions(first.read_text()),functions(second.read_text())
    assert f.keys()==g.keys()
    assert [name for name in f if f[name]!=g[name]]==['load']
    before,bnative,brows,braw,bunits,bseed=old.load(ROOT,ROOT/FACE)
    after,anative,arows,araw,aunits,aseed=new.load(ROOT,ROOT/FACE)
    assert braw==araw and bunits==aunits and bseed==aseed
    assert len(bseed)==111 and len(brows)==len(arows)==2384
    assert len(bnative)==len(anative)==2273
    assert [i for i in range(2384) if brows[i]!=arows[i]]==[2272]
    expected=dict(brows[2272],upper=1)
    assert brows[2272]['lower']==1 and brows[2272]['upper']==42
    assert arows[2272]==expected and arows[2271]==brows[2271]
    rules=new.rules
    selected=rules.row([[0,1]],1,1,'known_one',0)
    weak=rules.row([[0,1],[1,1]],1,2,'cover_lower',1)
    exact=rules.row([[0,1],[1,1]],1,1,'proved_equality',1)
    t0=rules.propagate(2,[selected,weak],b'',[],1)
    t1=rules.propagate(2,[selected,exact],b'',[],1)
    assert t0['values']==[1,-1] and t1['values']==[1,0]
    assert rules.verify_trace(2,[selected,weak],b'',t0)['complete_fixed_point_rechecked']
    assert rules.verify_trace(2,[selected,exact],b'',t1)['complete_fixed_point_rechecked']
    return {'status':'PASS: only second cover upper42 changes to the proved upper1',
        'source_sha256':sha(Path(__file__).read_bytes()),'old_source_sha256':OLD_SHA,'new_source_sha256':NEW_SHA,
        'explicit_substitution_sha256':SUB_SHA,
        'unchanged_functions':[name for name in f if f[name]==g[name]],
        'changed_native_row':2272,'old_range':[1,42],'new_range':[1,1],
        'all_other2383_rows_identical':True,'complete_registry_identical':True,
        'all111_seed_units_identical':True,'H1_retained_with_range':[1,42],
        'original_integer_rows_sha256':after['original_integer_rows_sha256'],
        'augmented_rows_sha256':after['augmented_integer_rows_sha256'],
        'exactly_one_tiny_control_and_independent_reason_replay':True,
        'case4_closure_run':False,'optimizer_calls':0}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    assert not a.output.exists();result=prove();a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
