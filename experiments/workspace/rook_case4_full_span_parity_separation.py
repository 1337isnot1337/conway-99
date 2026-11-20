"""Prepare exact full-span parity separation at one accepted fractional point.

There is no production optimizer entry point. A future Boolean assignment must
pass inspect_assignment(), including its original1214-coordinate Gram lift.
"""
import argparse
import gzip
import hashlib
import itertools
import json
from pathlib import Path
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[2]
LOG = "experiments/logs/grids-and-triangles/"
INPUTS = {
    "native": (LOG+"complement-rook-35core-case0004-native-cpsat-model.json",
               "a9004e97a2d166bf8b162609cfb538eae0dd4d26942b6df5119b6a88d65ec476"),
    "basis": (LOG+"rook-case4-face112-parity-preparation01/basis.json.gz",
              "ad03018a2bb30dfb79fb126b76aa9863b16217eeb42f0b1e78fdaabde610c00d"),
    "zero_model": (LOG+"rook-case4-face112-weighted-parity-model01/model.json",
                   "c6cd72c995ce1a47db90fe7263f643131bc555ed50e329c7734536f5cf870ac3"),
    "zero_model_cold": (LOG+"rook-case4-face112-weighted-parity-model01-cold-replay.json",
                        "567185c755134fcf7c15bb7be762bb2a70a503254259b2eb44a92f91abb39156"),
    "point": (LOG+"rook-case4-parity-discovery-cycle-run02/exact-01/candidate.json",
              "23de7244e4e4efb1ef82ff649008b1236bb389888ffbb923edf4017cfe1bc2e3"),
    "point_cold": (LOG+"rook-case4-parity-discovery-cycle-run02/exact-01/cold.json",
                   "a043d06fc2df9cc6c87c240bc3799a87e997abb31c7755c97dc12b3ba396bc49"),
}
LIMITS = {"preparation_seconds": 60, "planned_solver_seconds": 60,
          "planned_owned_child_seconds": 120, "planned_threads": 1,
          "planned_native_calls": 1, "automatic_retries": 0,
          "maximum_proto_bytes": 16 << 20, "maximum_specification_raw_bytes": 16 << 20,
          "maximum_integer_magnitude": (1 << 62)-1}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def tick(deadline):
    if time.monotonic() >= deadline:
        raise TimeoutError("full-span preparation budget")


def sites(mask):
    while mask:
        bit = mask & -mask
        yield bit.bit_length()-1
        mask ^= bit


def number(value):
    assert type(value) is int or (type(value) is str and value == str(int(value)))
    result = int(value); assert abs(result).bit_length() <= 4096
    return result


def inputs():
    out = {}
    for name, (path, expected) in INPUTS.items():
        raw = (ROOT/path).read_bytes(); assert sha(raw) == expected, ("input", name)
        out[name] = json.loads(gzip.decompress(raw) if path.endswith(".gz") else raw)
    assert out["zero_model_cold"]["model_sha256"] == INPUTS["zero_model"][1]
    assert out["zero_model_cold"]["status"].startswith("PASS:")
    point, cold = out["point"], out["point_cold"]
    assert cold["exact_point_replayed"] and cold["candidate_sha256"] == INPUTS["point"][1]
    assert cold["registry_sha256"] == point["registry_sha256"]
    assert cold["full_face_rows_checked"] == 167118 and cold["status"].startswith("PASS:")
    return out


def span_certificate(rows, gram_rows):
    """Exact bitset row operations; this is inventory algebra, not separation."""
    pivots = {}
    for i, (mask, rhs) in enumerate(rows):
        combination = 1 << i
        while mask:
            pivot = mask.bit_length()-1
            if pivot not in pivots:
                pivots[pivot] = (mask, rhs, combination)
                break
            old_mask, old_rhs, old_combination = pivots[pivot]
            mask ^= old_mask; rhs ^= old_rhs; combination ^= old_combination
        else:
            raise AssertionError("saved286-row basis is dependent or inconsistent")
    representations = []
    for mask, rhs in gram_rows:
        combination = 0
        while mask:
            pivot = mask.bit_length()-1
            assert pivot in pivots, "original equation outside declared span"
            old_mask, old_rhs, old_combination = pivots[pivot]
            mask ^= old_mask; rhs ^= old_rhs; combination ^= old_combination
        assert rhs == 0, "inconsistent original affine equation"
        representations.append(hex(combination))
    return {"rank": len(pivots),
            "triangular_rows": [{"pivot": p, "mask_hex": hex(v[0]), "rhs": v[1],
                                  "basis_choice_hex": hex(v[2])} for p, v in sorted(pivots.items())],
            "original_Gram_to_basis_choice_hex": representations}


def specification(deadline):
    data = inputs(); inventory = data["native"]["primary_inventory"]
    assert sha(canonical(inventory)) == data["native"]["primary_inventory_sha256"]
    gram = inventory["Gram_rows"]
    assert len(gram) == 630 and inventory["primary_variables"] == 1214
    assert [(i, j) for i, j, q, s in gram] == [(i, j) for i in range(35) for j in range(i, 35)]
    zeros = data["zero_model"]["fixed_zero_columns"]
    assert zeros == sorted(set(zeros)) and len(zeros) == 112
    assert data["basis"]["known_zero_columns"] == zeros
    kept = [a for a in range(1214) if a not in set(zeros)]
    active = sum(1 << a for a in kept)
    point = data["point"]; den = number(point["common_denominator"])
    nums = [number(v) for v in point["exact_check"]["original1214_selector_numerators"]]
    assert len(nums) == 1214 and den == 67336409858
    assert all(nums[a] == 0 for a in zeros) and all(0 < nums[a] <= den for a in kept)
    gram_masks, gram_rhs = [], []
    for i, j, q, support in gram:
        tick(deadline)
        assert type(q) is int and q >= 0 and support == sorted(set(support))
        assert all(type(a) is int and 0 <= a < 1214 for a in support)
        assert sum(nums[a] for a in support) == q*den
        gram_masks.append(sum(1 << a for a in support)); gram_rhs.append(q % 2)
    rows, witnesses, full_masks = [], [], []
    saved_basis = data["basis"]["basis"]
    assert len(saved_basis) == 286
    for i, item in enumerate(saved_basis):
        tick(deadline); assert item["basis_index"] == i
        witness = int(item["lift"]["original_native_row_combination_hex"], 16)
        assert 0 < witness < 1 << 630
        mask, rhs = 0, 0
        for r in sites(witness):
            mask ^= gram_masks[r]; rhs ^= gram_rhs[r]
        assert hex(mask) == item["lift"]["full_original_parity_hex"]
        assert hex(mask & active) == item["lift"]["active_original_support_hex"]
        assert rhs == item["lift"]["parity_rhs"]
        rows.append((mask & active, rhs)); witnesses.append(hex(witness)); full_masks.append(hex(mask))
    span = span_certificate(rows, [(m & active, b) for m, b in zip(gram_masks, gram_rhs)])
    assert span["rank"] == 286
    columns = [[i for i, (mask, rhs) in enumerate(rows) if mask >> a & 1] for a in kept]
    weights = [min(nums[a], den-nums[a]) for a in kept]
    penalties = [abs(den-2*nums[a]) for a in kept]
    nearest = [int(2*nums[a] > den) for a in kept]
    rank, count = len(rows), len(kept)
    names = {"choice": [0, rank], "support": [rank, rank+count],
             "flip": [rank+count, rank+2*count], "beta": rank+2*count}
    assert rank == 286 and count == 1102 and names["beta"]+1 == 2491
    assert sum(weights)+sum(penalties) <= LIMITS["maximum_integer_magnitude"]
    tick(deadline)
    return {"schema": "conway99.rook.case4.full_span_parity_separation.v1",
            "inputs": INPUTS, "scope": "separate one exact fractional point using original Gram parity span",
            "original_columns": 1214, "fixed_zero_columns": zeros, "kept_original_columns": kept,
            "basis_original_Gram_witness_hex": witnesses, "basis_full_original_mask_hex": full_masks,
            "basis_projected_mask_hex": [hex(mask) for mask, rhs in rows],
            "basis_rhs": [rhs for mask, rhs in rows], "column_choice_indices": columns,
            "span_certificate": span, "point_numerators1214": list(map(str, nums)),
            "denominator": str(den), "weights": weights, "penalties": penalties,
            "nearest_bits": nearest, "namespaces": names, "variables": names["beta"]+1,
            "support_XOR_rows": count, "total_XOR_rows": count+2,
            "support_XOR_choice_literals": sum(map(len, columns)),
            "constraints": 2*count+4,
            "weighted_upper": den-1, "weighted_nonzeros": sum(v != 0 for v in weights+penalties),
            "worst_weighted_unit_box_activity": sum(weights)+sum(penalties),
            "all_integer_activities_fit_signed63_bits": True,
            "objective_assumptions_hints": False, "production_optimizer_calls": 0,
            "native_INFEASIBLE_is_not_an_accepted_certificate": True,
            "case4_exclusion_claimed": False, "limits": LIMITS}


def build_model(spec):
    from ortools.sat.python import cp_model
    model = cp_model.CpModel()
    rank = len(spec["basis_rhs"]); count = len(spec["kept_original_columns"])
    variables = [model.new_bool_var(f"choice_{i}") for i in range(rank)]
    variables += [model.new_bool_var(f"support_{a}") for a in spec["kept_original_columns"]]
    variables += [model.new_bool_var(f"flip_{a}") for a in spec["kept_original_columns"]]
    variables += [model.new_bool_var("beta")]
    h, z, beta = rank, rank+count, rank+2*count
    for j, support in enumerate(spec["column_choice_indices"]):
        model.add_bool_xor([variables[i] for i in support]+[variables[h+j].Not()])
    model.add_bool_xor([variables[i] for i, rhs in enumerate(spec["basis_rhs"]) if rhs]+[variables[beta].Not()])
    model.add_bool_xor([variables[beta]]+[variables[h+j] for j, f in enumerate(spec["nearest_bits"]) if f]
                      +[variables[z+j] for j in range(count)])
    for j in range(count):
        model.add_linear_constraint(variables[z+j]-variables[h+j], -1, 0)
    model.add_at_most_one([variables[z+j] for j in range(count)])
    model.add_linear_constraint(sum(w*variables[h+j] for j, w in enumerate(spec["weights"]))
                                +sum(p*variables[z+j] for j, p in enumerate(spec["penalties"])),
                                0, spec["weighted_upper"])
    assert len(model.proto.variables) == spec["variables"] and len(model.proto.constraints) == spec["constraints"]
    assert model.validate() == ""
    return model


def literal_proto_check(proto, spec):
    assert {f.name for f, v in proto.ListFields()} == {"variables", "constraints"}
    assert len(proto.variables) == spec["variables"] and len(proto.constraints) == spec["constraints"]
    for var in proto.variables:
        assert list(var.domain) == [0, 1]
    rank = len(spec["basis_rhs"]); count = len(spec["kept_original_columns"])
    h, z, beta = rank, rank+count, rank+2*count
    expected_xor = [[*columns, -(h+j)-1] for j, columns in enumerate(spec["column_choice_indices"])]
    expected_xor += [[i for i, rhs in enumerate(spec["basis_rhs"]) if rhs]+[-beta-1]]
    expected_xor += [[beta]+[h+j for j, f in enumerate(spec["nearest_bits"]) if f]+list(range(z,z+count))]
    for i, literals in enumerate(expected_xor):
        c = proto.constraints[i]
        assert c.WhichOneof("constraint") == "bool_xor" and not c.enforcement_literal
        assert list(c.bool_xor.literals) == literals
    for j in range(count):
        c = proto.constraints[count+2+j]
        assert c.WhichOneof("constraint") == "linear" and not c.enforcement_literal
        assert dict(zip(c.linear.vars,c.linear.coeffs)) == {h+j:-1,z+j:1}
        assert len(c.linear.vars) == 2 and list(c.linear.domain) == [-1,0]
    c = proto.constraints[2*count+2]
    assert c.WhichOneof("constraint") == "at_most_one" and not c.enforcement_literal
    assert list(c.at_most_one.literals) == list(range(z,z+count))
    c = proto.constraints[2*count+3]
    assert c.WhichOneof("constraint") == "linear" and not c.enforcement_literal
    terms = {h+j:w for j,w in enumerate(spec["weights"]) if w}
    terms.update({z+j:p for j,p in enumerate(spec["penalties"]) if p})
    assert len(c.linear.vars) == len(terms) and dict(zip(c.linear.vars,c.linear.coeffs)) == terms
    assert list(c.linear.domain) == [0,spec["weighted_upper"]]
    return {"all_variables_and_constraint_literals_checked": True,
            "XOR_rows": len(expected_xor), "weighted_terms": len(terms), "optimizer_calls": 0}


def evaluate_proto(proto, values):
    if len(values) != len(proto.variables) or any(v not in (0,1) for v in values): return False
    def truth(literal): return values[literal] if literal >= 0 else 1-values[-literal-1]
    for c in proto.constraints:
        assert not c.enforcement_literal
        kind = c.WhichOneof("constraint")
        if kind == "bool_xor":
            if sum(map(truth,c.bool_xor.literals)) % 2 != 1: return False
        elif kind == "at_most_one":
            if sum(map(truth,c.at_most_one.literals)) > 1: return False
        else:
            assert kind == "linear"
            value = sum(a*values[j] for j,a in zip(c.linear.vars,c.linear.coeffs))
            if not any(c.linear.domain[i] <= value <= c.linear.domain[i+1] for i in range(0,len(c.linear.domain),2)): return False
    return True


def controls():
    from ortools.sat import cp_model_pb2
    checked, equations, count = 0, 0, 0
    with tempfile.TemporaryDirectory(prefix="rook_parity_controls_") as temp:
        for masks, count in [([3],2),([3,5],3)]:
            rank = len(masks)
            for rhs in itertools.product((0,1),repeat=rank):
                for nums in ([1]*count,[0]+[2]*(count-1),[2]+[1]*(count-1),
                             [3]*count,[4]+[2]*(count-1),[1]+[3]*(count-1)):
                    den = 4; columns = [[i for i,m in enumerate(masks) if m>>j&1] for j in range(count)]
                    spec = {"basis_rhs":list(rhs),"kept_original_columns":list(range(count)),
                            "column_choice_indices":columns,"weights":[min(n,den-n) for n in nums],
                            "penalties":[abs(den-2*n) for n in nums],"nearest_bits":[int(2*n>den) for n in nums],
                            "weighted_upper":den-1,"variables":rank+2*count+1,"constraints":2*count+4}
                    model = build_model(spec); path = Path(temp)/"toy.pb"; assert model.export_to_file(str(path))
                    proto = cp_model_pb2.CpModelProto(); proto.ParseFromString(path.read_bytes())
                    literal_proto_check(proto,spec)
                    for values in itertools.product((0,1),repeat=spec["variables"]):
                        u,h,z,beta = values[:rank],values[rank:rank+count],values[rank+count:rank+2*count],values[-1]
                        wanted_h = [sum(u[i] for i,m in enumerate(masks) if m>>j&1)%2 for j in range(count)]
                        wanted_beta = sum(u[i]*rhs[i] for i in range(rank))%2
                        forbidden = [spec["nearest_bits"][j]^z[j] for j in range(count)]
                        distance = sum((den-nums[j] if forbidden[j] else nums[j]) for j in range(count) if h[j])
                        wanted = (list(h)==wanted_h and beta==wanted_beta and sum(z)<=1 and
                                  all(z[j]<=h[j] for j in range(count)) and
                                  (sum(forbidden[j] for j in range(count) if h[j])+beta)%2==1 and distance<den)
                        assert evaluate_proto(proto,values) == wanted
                        checked += 1
                    # Compare optional-one-flip existence with every forbidden vertex.
                    for u in itertools.product((0,1),repeat=rank):
                        mask,r = 0,0
                        for i,bit in enumerate(u):
                            if bit: mask^=masks[i];r^=rhs[i]
                        support=list(sites(mask))
                        full = [sum(den-nums[a] if b else nums[a] for a,b in zip(support,bits))
                                for bits in itertools.product((0,1),repeat=len(support)) if sum(bits)%2!=r]
                        flips=[]
                        for flip in [None]+support:
                            bits=[spec['nearest_bits'][a]^(a==flip) for a in support]
                            if sum(bits)%2!=r: flips.append(sum(den-nums[a] if b else nums[a] for a,b in zip(support,bits)))
                        assert (min(full) if full else None) == (min(flips) if flips else None)
                        equations += 1
    return {"serialized_proto_Boolean_assignments":checked,"one_flip_completeness_controls":equations,
            "native_optimizer_calls":0,"production_points_searched":0}


def inspect_assignment(spec, values, data):
    assert len(values) == spec["variables"] and all(type(v) is int and v in (0,1) for v in values)
    rank=len(spec["basis_rhs"]);count=len(spec["kept_original_columns"])
    u,h,z,beta = values[:rank],values[rank:rank+count],values[rank+count:rank+2*count],values[-1]
    assert h == [sum(u[i] for i in col)%2 for col in spec["column_choice_indices"]]
    assert beta == sum(u[i]*b for i,b in enumerate(spec["basis_rhs"]))%2
    assert sum(z)<=1 and all(zj<=hj for zj,hj in zip(z,h))
    assert (beta+sum(f*hj for f,hj in zip(spec["nearest_bits"],h))+sum(z))%2==1
    den=int(spec["denominator"])
    cost=sum(w*hj+p*zj for w,p,hj,zj in zip(spec["weights"],spec["penalties"],h,z))
    assert cost<=den-1
    witness=0
    for i,bit in enumerate(u):
        if bit:witness^=int(spec["basis_original_Gram_witness_hex"][i],16)
    gram=data["native"]["primary_inventory"]["Gram_rows"]
    coefficients=[0]*1214;rhs=0;ids=list(sites(witness))
    for r in ids:
        _,_,quota,support=gram[r];rhs+=quota
        for a in support:coefficients[a]+=1
    zeros=set(spec["fixed_zero_columns"])
    support=[a for a,c in enumerate(coefficients) if c%2 and a not in zeros]
    assert support == [a for a,hj in zip(spec["kept_original_columns"],h) if hj]
    assert rhs%2==beta and support
    forbidden=[a for a,f,hj,zj in zip(spec["kept_original_columns"],spec["nearest_bits"],h,z) if hj and (f^zj)]
    assert len(forbidden)%2 != beta
    one=set(forbidden);terms=[[a,1 if a in one else -1] for a in support];upper=len(forbidden)-1
    nums=list(map(int,spec["point_numerators1214"]))
    assert all(nums[a]==0 for a in zeros)
    assert sum(c*n for c,n in zip(coefficients,nums))==rhs*den
    deficit=sum(c*nums[a] for a,c in terms)-upper*den
    assert deficit==den-cost>0
    return {"status":"EXACT_VIOLATED_PARITY_CUT","original_Gram_row_ids":ids,
            "full_original1214_integer_coefficients":coefficients,"original_Gram_rhs_sum":rhs,
            "parity_rhs":beta,"active_original_support":support,"forbidden_ones":forbidden,
            "removed_proved_zero_odd_columns":[a for a,c in enumerate(coefficients) if c%2 and a in zeros],
            "inequality":{"terms":terms,"upper":upper},"exact_deficit_numerator":str(deficit),
            "point_denominator":str(den),"case4_excluded":False,"whole_graph_claimed":False}


def runtime_binding():
    import ortools
    from ortools.sat import cp_model_pb2
    from ortools.sat.python import cp_model,cp_model_helper
    import google.protobuf
    return {"python":sys.version,"ortools":ortools.__version__,"protobuf":google.protobuf.__version__,
            "files":{name:{"path":str(Path(module.__file__).resolve()),"sha256":sha(Path(module.__file__).read_bytes())}
                     for name,module in [('cp_model',cp_model),('cp_model_pb2',cp_model_pb2),('cp_model_helper',cp_model_helper)]}}


def prepare(directory):
    assert not directory.exists();directory.mkdir(parents=True)
    started=time.monotonic();deadline=started+LIMITS["preparation_seconds"]
    control=controls();spec=specification(deadline)
    raw=canonical(spec)+b"\n";assert len(raw)<=LIMITS["maximum_specification_raw_bytes"]
    compressed=gzip.compress(raw,mtime=0);(directory/'specification.json.gz').write_bytes(compressed)
    model=build_model(spec);path=directory/'model.pb';assert model.export_to_file(str(path))
    binary=path.read_bytes();assert len(binary)<=LIMITS["maximum_proto_bytes"]
    from ortools.sat import cp_model_pb2
    proto=cp_model_pb2.CpModelProto();proto.ParseFromString(binary)
    checked=literal_proto_check(proto,spec);tick(deadline)
    result={"status":"PREPARED: complete original-Gram dual-span separation; no production query",
            "source_sha256":sha(Path(__file__).read_bytes()),"inputs":INPUTS,"limits":LIMITS,
            "specification":{"path":str((directory/'specification.json.gz').relative_to(ROOT)),"sha256":sha(compressed),"raw_sha256":sha(raw),"raw_bytes":len(raw)},
            "proto":{"path":str(path.relative_to(ROOT)),"sha256":sha(binary),"bytes":len(binary)},
            "runtime_binding":runtime_binding(),"controls":control,"native_proto_check":checked,
            "inventory":{k:spec[k] for k in ['variables','constraints','support_XOR_rows','total_XOR_rows','support_XOR_choice_literals','weighted_nonzeros','weighted_upper','worst_weighted_unit_box_activity']},
            "rank":spec['span_certificate']['rank'],"all630_original_Gram_equations_in_span":True,
            "production_optimizer_calls":0,"case4_excluded":False,"seconds":time.monotonic()-started}
    (directory/'preparation.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    return result


def main():
    if not __debug__:raise RuntimeError('assertions are required')
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=('prepare',))
    parser.add_argument('--directory',type=Path,required=True)
    args=parser.parse_args()
    try:result=prepare(args.directory.resolve())
    except Exception as exc:
        failure={'status':'PREPARATION_ERROR','source_sha256':sha(Path(__file__).read_bytes()),'error':repr(exc),'production_optimizer_calls':0}
        args.directory.mkdir(parents=True,exist_ok=True)
        (args.directory/'failure.json').write_text(json.dumps(failure,indent=2)+'\n')
        raise
    print(json.dumps({'status':result['status'],'seconds':result['seconds'],'inventory':result['inventory']}))


if __name__=='__main__':main()
