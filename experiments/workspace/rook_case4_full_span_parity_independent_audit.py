"""Artifact-only full-span parity preparation audit; no subject import or solve."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[2]
LOG = "experiments/logs/grids-and-triangles/"
SUBJECT = "experiments/workspace/rook_case4_full_span_parity_separation.py"
SUBJECT_SHA = "893c7b0ba5d849daf29ed6a5668fb937efda854103d99812e84a68df66f27207"
PREPARATION = LOG+"rook-case4-full-span-parity-preparation01/preparation.json"
PREPARATION_SHA = "0b2de700e4cd088ffb7a52726b0aef4cf8e3d0eeb4ade2d2dfacdf9dc7dbdd90"
INPUTS = {
    "native": (LOG+"complement-rook-35core-case0004-native-cpsat-model.json", "a9004e97a2d166bf8b162609cfb538eae0dd4d26942b6df5119b6a88d65ec476"),
    "basis": (LOG+"rook-case4-face112-parity-preparation01/basis.json.gz", "ad03018a2bb30dfb79fb126b76aa9863b16217eeb42f0b1e78fdaabde610c00d"),
    "zero_model": (LOG+"rook-case4-face112-weighted-parity-model01/model.json", "c6cd72c995ce1a47db90fe7263f643131bc555ed50e329c7734536f5cf870ac3"),
    "zero_model_cold": (LOG+"rook-case4-face112-weighted-parity-model01-cold-replay.json", "567185c755134fcf7c15bb7be762bb2a70a503254259b2eb44a92f91abb39156"),
    "point": (LOG+"rook-case4-parity-discovery-cycle-run02/exact-01/candidate.json", "23de7244e4e4efb1ef82ff649008b1236bb389888ffbb923edf4017cfe1bc2e3"),
    "point_cold": (LOG+"rook-case4-parity-discovery-cycle-run02/exact-01/cold.json", "a043d06fc2df9cc6c87c240bc3799a87e997abb31c7755c97dc12b3ba396bc49"),
}


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def bound_bytes(path, expected):
    raw = (ROOT/path).read_bytes()
    assert digest(raw) == expected, path
    return raw


def read_json(path, expected):
    raw = bound_bytes(path, expected)
    return json.loads(gzip.decompress(raw) if path.endswith('.gz') else raw)


def selected(mask, width):
    assert 0 <= mask < (1 << width)
    return [i for i in range(width) if (mask >> i) & 1]


def run():
    started = time.monotonic()
    deadline = started+60
    def clock():
        if time.monotonic() >= deadline:
            raise TimeoutError('independent preparation audit budget')
    bound_bytes(SUBJECT, SUBJECT_SHA)
    preparation = read_json(PREPARATION, PREPARATION_SHA)
    assert preparation['source_sha256'] == SUBJECT_SHA
    assert preparation['inputs'] == {k:list(v) for k,v in INPUTS.items()}
    data = {name:read_json(*binding) for name,binding in INPUTS.items()}
    spec_binding = preparation['specification']
    raw = gzip.decompress(bound_bytes(spec_binding['path'],spec_binding['sha256']))
    assert digest(raw) == spec_binding['raw_sha256'] and len(raw) == spec_binding['raw_bytes']
    spec = json.loads(raw)
    assert spec['inputs'] == preparation['inputs']
    assert data['zero_model_cold']['model_sha256'] == INPUTS['zero_model'][1]
    assert data['zero_model_cold']['status'].startswith('PASS:')
    assert data['point_cold']['candidate_sha256'] == INPUTS['point'][1]
    assert data['point_cold']['exact_point_replayed'] is True
    assert data['point_cold']['registry_sha256'] == data['point']['registry_sha256']
    assert data['point_cold']['full_face_rows_checked'] == 167118
    zeros = data['zero_model']['fixed_zero_columns']
    assert zeros == sorted(set(zeros)) and len(zeros) == 112
    assert data['basis']['known_zero_columns'] == spec['fixed_zero_columns'] == zeros
    kept = [j for j in range(1214) if j not in set(zeros)]
    assert spec['kept_original_columns'] == kept and len(kept) == 1102
    active = sum(1 << j for j in kept)
    inventory = data['native']['primary_inventory']
    encoded = json.dumps(inventory,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
    assert digest(encoded) == data['native']['primary_inventory_sha256']
    gram = inventory['Gram_rows']
    assert len(gram) == 630 and inventory['primary_variables'] == 1214
    assert [(r[0],r[1]) for r in gram] == [(i,j) for i in range(35) for j in range(i,35)]
    denominator = int(data['point']['common_denominator'])
    numerators = list(map(int,data['point']['exact_check']['original1214_selector_numerators']))
    assert denominator == int(spec['denominator']) == 67336409858
    assert len(numerators) == 1214 and spec['point_numerators1214'] == list(map(str,numerators))
    assert all(numerators[j] == 0 for j in zeros)
    assert all(0 < numerators[j] <= denominator for j in kept)
    gram_masks, gram_rhs = [], []
    for i,j,quota,support in gram:
        assert type(quota) is int and quota >= 0
        assert support == sorted(set(support)) and all(type(a) is int and 0 <= a < 1214 for a in support)
        assert sum(numerators[a] for a in support) == denominator*quota
        gram_masks.append(sum(1 << a for a in support)); gram_rhs.append(quota%2)
    saved = data['basis']['basis']; assert len(saved) == 286
    masks, rhs = [], []
    witness_terms = 0
    for i,item in enumerate(saved):
        clock(); assert item['basis_index'] == i
        witness = int(item['lift']['original_native_row_combination_hex'],16)
        ids = selected(witness,630); assert ids
        # Rebuild integer products, rather than reuse the subject's bitset XOR.
        coefficients = [0]*1214; total = 0
        for r in ids:
            total += gram[r][2]
            for a in gram[r][3]: coefficients[a] += 1
        full = sum((c%2) << a for a,c in enumerate(coefficients))
        projected = full & active
        assert spec['basis_original_Gram_witness_hex'][i] == hex(witness)
        assert spec['basis_full_original_mask_hex'][i] == item['lift']['full_original_parity_hex'] == hex(full)
        assert spec['basis_projected_mask_hex'][i] == item['lift']['active_original_support_hex'] == hex(projected)
        assert spec['basis_rhs'][i] == item['lift']['parity_rhs'] == total%2
        assert sum(c*n for c,n in zip(coefficients,numerators)) == total*denominator
        masks.append(projected); rhs.append(total%2); witness_terms += len(ids)
    # Validate a triangular rank witness; no elimination is repeated.
    span = spec['span_certificate']; triangular = span['triangular_rows']
    assert span['rank'] == 286 and len(triangular) == 286
    pivots = set()
    def combination(value):
        mask, parity = 0,0
        for i in selected(int(value,16),286): mask ^= masks[i]; parity ^= rhs[i]
        return mask,parity
    for row in triangular:
        clock(); mask,parity = combination(row['basis_choice_hex'])
        assert mask > 0 and row['mask_hex'] == hex(mask) and row['rhs'] == parity
        assert row['pivot'] == mask.bit_length()-1 and row['pivot'] not in pivots
        pivots.add(row['pivot'])
    representations = span['original_Gram_to_basis_choice_hex']; assert len(representations) == 630
    for r, choice in enumerate(representations):
        assert combination(choice) == (gram_masks[r]&active,gram_rhs[r])
    # Independently transpose the full original-coordinate witness masks.
    columns = [[i for i in range(286) if masks[i] & (1 << a)] for a in kept]
    weights = [min(numerators[a],denominator-numerators[a]) for a in kept]
    penalties = [abs(denominator-2*numerators[a]) for a in kept]
    nearest = [int(2*numerators[a] > denominator) for a in kept]
    for key,value in [('column_choice_indices',columns),('weights',weights),('penalties',penalties),('nearest_bits',nearest)]:
        assert spec[key] == value, key
    assert spec['weighted_upper'] == denominator-1
    assert spec['worst_weighted_unit_box_activity'] == sum(weights)+sum(penalties) < (1 << 62)
    namespaces = {'choice':[0,286],'support':[286,1388],'flip':[1388,2490],'beta':2490}
    assert spec['namespaces'] == namespaces and spec['variables'] == 2491 and spec['constraints'] == 2208
    from ortools.sat import cp_model_pb2
    model_raw = bound_bytes(preparation['proto']['path'],preparation['proto']['sha256'])
    assert len(model_raw) == preparation['proto']['bytes']
    proto = cp_model_pb2.CpModelProto(); proto.ParseFromString(model_raw)
    assert {descriptor.name for descriptor,value in proto.ListFields()} == {'variables','constraints'}
    assert len(proto.variables) == 2491 and len(proto.constraints) == 2208
    names = [f'choice_{i}' for i in range(286)]+[f'support_{a}' for a in kept]+[f'flip_{a}' for a in kept]+['beta']
    for var,name in zip(proto.variables,names): assert var.name == name and list(var.domain) == [0,1]
    expected = [[*column,-(286+j)-1] for j,column in enumerate(columns)]
    expected.append([i for i,b in enumerate(rhs) if b]+[-2491])
    expected.append([2490]+[286+j for j,b in enumerate(nearest) if b]+list(range(1388,2490)))
    for index,literals in enumerate(expected):
        c = proto.constraints[index]
        assert c.WhichOneof('constraint') == 'bool_xor' and not c.enforcement_literal
        assert list(c.bool_xor.literals) == literals
    for j in range(1102):
        c = proto.constraints[1104+j]
        assert c.WhichOneof('constraint') == 'linear' and not c.enforcement_literal
        assert len(c.linear.vars) == 2 and len(c.linear.coeffs) == 2
        assert dict(zip(c.linear.vars,c.linear.coeffs)) == {286+j:-1,1388+j:1}
        assert list(c.linear.domain) == [-1,0]
    c = proto.constraints[2206]
    assert c.WhichOneof('constraint') == 'at_most_one' and not c.enforcement_literal
    assert list(c.at_most_one.literals) == list(range(1388,2490))
    c = proto.constraints[2207]
    assert c.WhichOneof('constraint') == 'linear' and not c.enforcement_literal
    terms = {286+j:w for j,w in enumerate(weights) if w}
    terms.update({1388+j:p for j,p in enumerate(penalties) if p})
    assert len(c.linear.vars) == len(c.linear.coeffs) == len(terms)
    assert dict(zip(c.linear.vars,c.linear.coeffs)) == terms
    assert list(c.linear.domain) == [0,denominator-1]
    for binding in preparation['runtime_binding']['files'].values():
        assert digest(Path(binding['path']).read_bytes()) == binding['sha256']
    clock()
    return {'status':'PASS: independent coefficient, witness, rank-certificate and native-proto audit',
            'audit_source_sha256':digest(Path(__file__).read_bytes()),
            'subject_source_sha256':SUBJECT_SHA,'preparation_sha256':PREPARATION_SHA,
            'specification_sha256':spec_binding['sha256'],'proto_sha256':preparation['proto']['sha256'],
            'inputs':INPUTS,'original_Gram_equations_checked':630,'original_coordinates':1214,
            'kept_coordinates':1102,'proved_zero_premises':112,'basis_witnesses_checked':286,
            'original_row_terms_in_basis_witnesses':witness_terms,'exact_rank':286,
            'original_equation_span_representations_checked':630,
            'column_basis_coefficients_checked':286*1102,'native_variables_checked':2491,
            'native_constraints_checked':2208,'native_XOR_rows_checked':1104,
            'native_weighted_terms_checked':len(terms),'point_Gram_check':True,
            'subject_imports':0,'native_model_rebuilds':0,'eliminations_repeated':0,
            'optimizer_calls':0,'parity_searches':0,'case4_exclusion_claimed':False,
            'zero_proof_scope':'uses source-bound previously accepted112-zero model; does not rederive that ancestry',
            'seconds':time.monotonic()-started}


def main():
    if not __debug__: raise RuntimeError('assertions are required')
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args(); assert not args.output.exists()
    result=run(); args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'status':result['status'],'seconds':result['seconds']}))


if __name__=='__main__': main()
