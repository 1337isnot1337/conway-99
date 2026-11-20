"""Prepared finite parity search at the independently checked H3 point.

Evaluate the old family once at this new point, then two exact weighted
RREF families. Deduplicate equations across all three families. Every
retained Boolean inequality has a full original Gram-row XOR witness.
Preparation runs only synthetic reduction controls, not case elimination.
"""
import argparse
import gzip
import hashlib
from itertools import combinations
import json
from pathlib import Path
import time

import rook_case4_parity_polytope as parity
import rook_case4_weighted_parity_basis as basis

ROOT = Path(__file__).resolve().parents[2]
BASE = "experiments/logs/grids-and-triangles/"
FILES = {
    "native": (BASE+"complement-rook-35core-case0004-native-cpsat-model.json", "a9004e97a2d166bf8b162609cfb538eae0dd4d26942b6df5119b6a88d65ec476"),
    "old_basis": (BASE+"rook-case4-face112-parity-preparation01/basis.json.gz", "ad03018a2bb30dfb79fb126b76aa9863b16217eeb42f0b1e78fdaabde610c00d"),
    "old_family_cold": (BASE+"rook-case4-face112-parity-run01-replay.json", "7d5f64961f83c7714804fad3521d13c5deb1924f804a6f2b8227897bf509e710"),
    "model": (BASE+"rook-case4-face112-h3-model02/model.json", "1928eb76274865e219747f631fee2d7a327ed7acd3a845986844be13c9e34265"),
    "model_cold": (BASE+"rook-case4-face112-h3-model02-cold-replay.json", "56864810924bacb6b331db728a4ce32810d8e6f2dfe7c196e0a73e0b2f583a97"),
    "point": (BASE+"rook-case4-face112-h3-basis-run01/candidate.json", "cecacaaa1cb6974dd898f1d2b69be32a06e44e9b89a1b45e35717bc347d3b4e8"),
    "point_check": (BASE+"rook-case4-face112-h3-point-direct-check01.json", "f20cb9ffe3768591cd255dd9b148881d7c3df8df80fb881a7c59a75c6758395c"),
}
HELPER_SHA = "bb507d8d97a064bd8c56aac763b44e026c50598048b213db9399662eaaec7415"
PARITY_SHA = "048df509b05601f15d6cb4230750b36d221276cce66e625b0cf9c720ecb89062"
PRIMARY_SHA = "5a6af30f47826df629a3795ceea0a0a91b853cf8149860355ce1bd17ac0094b2"
OLD_RAW_SHA = "a73c1c4fdef2897ed133817816c1fc99675e8433a4be4b80f5fc7edf18470b40"
LIMITS = {"preparation_seconds":60, "shared_elimination_and_scan_seconds":60,
          "cold_replay_seconds":60, "raw_candidate_upper_bound":123123,
          "weighted_column_orders":2, "maximum_retained_cuts":64,
          "maximum_transcript_bytes":64 << 20, "result_reserve_bytes":1 << 20,
          "automatic_retries":0, "optimizer_calls":0}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return (json.dumps(value,sort_keys=True,separators=(",",":"))+"\n").encode()


def save(path,value):
    raw = json.dumps(value,indent=2).encode()+b"\n"
    assert len(raw) <= LIMITS["result_reserve_bytes"]
    temporary = path.with_name(path.name+".partial")
    temporary.write_bytes(raw)
    temporary.replace(path)


def source_bindings():
    assert sha(Path(basis.__file__).read_bytes()) == HELPER_SHA
    assert sha(Path(parity.__file__).read_bytes()) == PARITY_SHA
    return {"driver_sha256":sha(Path(__file__).read_bytes()),
            "row_reduction_helper_sha256":HELPER_SHA,"parity_helper_sha256":PARITY_SHA,
            "inputs":{k:list(v) for k,v in FILES.items()}}


def load(root,deadline):
    bound = source_bindings()
    raw = {}
    for key,(name,expected) in FILES.items():
        basis.tick(deadline)
        raw[key] = (root/name).read_bytes()
        assert sha(raw[key]) == expected, ("input hash",key)
    native = json.loads(raw["native"])
    inventory = native["primary_inventory"]
    assert sha(canonical(inventory).rstrip(b"\n")) == native["primary_inventory_sha256"] == PRIMARY_SHA
    gram = inventory["Gram_rows"]
    assert [(i,j) for i,j,q,s in gram] == [(i,j) for i in range(35) for j in range(i,35)]
    assert len(gram) == 630 and inventory["primary_variables"] == 1214
    for i,j,q,support in gram:
        assert type(q) is int and q >= 0 and support == sorted(set(support))
        assert all(type(a) is int and 0 <= a < 1214 for a in support)
    masks = [sum(1 << a for a in support) for i,j,q,support in gram]
    quotas = [q for i,j,q,support in gram]
    model = json.loads(raw["model"])
    zeros = model["fixed_zero_columns"]
    assert len(zeros) == 112 and zeros == sorted(set(zeros))
    kept = [a for a in range(1214) if a not in set(zeros)]
    active = sum(1 << a for a in kept)
    cold = json.loads(raw["model_cold"])
    assert cold["model_sha256"] == FILES["model"][1] and cold["status"].startswith("PASS:")
    old_raw = gzip.decompress(raw["old_basis"])
    assert sha(old_raw) == OLD_RAW_SHA
    old = json.loads(old_raw)
    assert old["known_zero_columns"] == zeros and len(old["basis"]) == 286
    rows = []
    for i,item in enumerate(old["basis"]):
        basis.tick(deadline)
        assert item["basis_index"] == i
        witness = int(item["lift"]["original_native_row_combination_hex"],16)
        assert 0 < witness < 1 << 630
        mask, rhs = 0,0
        for j in basis.sites(witness):
            mask ^= masks[j]
            rhs ^= quotas[j] % 2
        assert hex(mask) == item["lift"]["full_original_parity_hex"]
        assert hex(mask & active) == item["lift"]["active_original_support_hex"]
        assert rhs == item["lift"]["parity_rhs"]
        rows.append((mask & active,rhs,witness))
    point = json.loads(raw["point"])
    checked = json.loads(raw["point_check"])
    assert checked["exact_point_verified"] and checked["status"].startswith("PASS:")
    assert checked["input_bindings"]["candidate"] == list(FILES["point"])
    nums = list(map(int,point["exact_check"]["original1214_selector_numerators"]))
    denominator = int(point["common_denominator"])
    assert len(nums) == 1214 and denominator == 27131679103
    assert all(0 <= v <= denominator for v in nums) and all(nums[a] == 0 for a in zeros)
    assert all(nums[a] > 0 for a in kept) and denominator % 2 == 1
    assignment = sum(1 << a for a,v in enumerate(nums) if v % 2)
    for (i,j,q,support),mask in zip(gram,masks):
        assert sum(nums[a] for a in support) == q*denominator
        assert (assignment & mask).bit_count() % 2 == q % 2
    weight = {a:min(nums[a],denominator-nums[a]) for a in kept}
    orders = [sorted(kept,key=lambda a:(-weight[a],a)),
              sorted(kept,key=lambda a:(-weight[a],-a))]
    return {"bindings":bound,"gram":gram,"gram_masks":masks,"quotas":quotas,
            "rows":rows,"zeros":zeros,"kept":kept,"active":active,
            "point":nums,"denominator":denominator,"orders":orders,
            "mod2_point_assignment_hex":hex(assignment)}


def family(rows):
    selections = [(i,) for i in range(len(rows))]
    selections.extend(combinations(range(len(rows)),2))
    for indices in selections:
        mask,rhs,witness = 0,0,0
        for i in indices:
            a,b,c = rows[i]
            mask ^= a; rhs ^= b; witness ^= c
        assert mask != 0
        yield list(indices),(mask,rhs,witness)


def definition(data):
    original = {(a,b) for indices,(a,b,c) in family(data["rows"])}
    assert len(original) == 41041
    return {"input_projected_rows":286,"original_Gram_rows":630,
        "rank_not_assumed_after_projection":True,"zero_premises":data["zeros"],
        "point_sha256":FILES["point"][1],"independent_point_check_sha256":FILES["point_check"][1],
        "point_denominator":str(data["denominator"]),
        "column_order_rule":"decreasing exact min(numerator,denominator-numerator); ties by ascending original ID for order0, descending original ID for order1",
        "column_orders":data["orders"],
        "family_order":["old286 singles/pairs at the NEW point","weighted_RREF0 singles/pairs","weighted_RREF1 singles/pairs"],
        "old_equations_are_not_blanket_excluded":True,
        "deduplication":"first occurrence of exact(original support bits,parity RHS) across all three families",
        "nearest_forbidden_vertex_ties":"frozen helper: nearest bit0 at half; parity flip uses minimum absolute penalty then ascending original ID",
        "maximum_raw_words":3*41041,
        "output_cuts":"first64 distinct violated equations in family order; later exact violations counted and recorded without retaining their full cut certificate",
        "original_family_distinct_equations":len(original),
        "maximum_integer_distance_bound":str(1103*data["denominator"]),
        "budget_style":"one cooperative wall deadline shared by input checks, both eliminations, span verification, separation and transcript writes; no automatic retry",
        "limits":LIMITS,"preparation_performs_case_elimination":False}


def prepare(root,output):
    assert not output.exists()
    start = time.monotonic(); deadline = start+LIMITS["preparation_seconds"]
    data = load(root,deadline)
    control = basis.controls(deadline)
    record = {"status":"PREPARED: original plus two weighted parity families; no case elimination/scan",
        "source_bindings":source_bindings(),"definition":definition(data),
        "synthetic_controls":control,"case_RREF_calls":0,"case_parity_evaluations":0,
        "optimizer_calls":0,"elapsed_seconds":time.monotonic()-start}
    record["definition_sha256"] = sha(canonical(record["definition"]))
    save(output,record)
    return record


def prepared(root,path,deadline):
    saved = json.loads(path.read_bytes())
    assert saved["source_bindings"] == source_bindings()
    data = load(root,deadline)
    spec = definition(data)
    assert saved["definition"] == spec and saved["definition_sha256"] == sha(canonical(spec))
    return saved,data


def pack_certificate(cert):
    return {"rank":cert["rank"],"pivots":cert["pivots"],"inconsistent":cert["inconsistent"],
            "rows":[[hex(a),b,hex(c),hex(d)] for a,b,c,d in cert["rows"]]}


def unpack_certificate(cert):
    return {"rank":cert["rank"],"pivots":cert["pivots"],"inconsistent":cert["inconsistent"],
            "rows":[[int(a,16),b,int(c,16),int(d,16)] for a,b,c,d in cert["rows"]]}


def verify_basis(data,order,cert,deadline):
    report = basis.verify(data["rows"],data["orders"][order],cert,deadline)
    assert not cert["inconsistent"], "contradicts the checked odd-denominator GF2 point"
    for mask,q in zip(data["gram_masks"],data["quotas"]):
        basis.tick(deadline)
        assert basis.remainder(mask & data["active"],q % 2,cert) == (0,0)
    report.update(all_original630_Gram_rows_in_output_span=True,
        original_Gram_witnesses_only=True,
        coefficient_rank_is_complete_Gram_rank_on112_zero_face=True)
    return report


def candidates(data,certificates):
    families = [data["rows"]]
    families.extend([tuple(row[:3]) for row in cert["rows"][:cert["rank"]]] for cert in certificates)
    raw_id = 0
    for f,rows in enumerate(families):
        for indices,row in family(rows):
            yield raw_id,f,indices,row
            raw_id += 1


def full_cut(data,raw_id,family_id,indices,row,proposal,deadline):
    mask,rhs,witness = row
    coefficients, total, original = [0]*1214,0,list(basis.sites(witness))
    for i in original:
        basis.tick(deadline)
        a,b,q,support = data["gram"][i]
        total += q
        for j in support:
            coefficients[j] += 1
    odd = sum(1 << j for j,c in enumerate(coefficients) if c % 2)
    assert odd & data["active"] == mask and total % 2 == rhs
    removed = list(basis.sites(odd & ~data["active"]))
    assert set(removed) <= set(data["zeros"])
    checked = parity.check_exact(proposal,data["point"],data["denominator"])
    assert checked["exact_violation_numerator"] > 0
    return {"raw_candidate_id":raw_id,"family":family_id,"basis_indices":indices,
        "original_Gram_row_ids":original,"full_original1214_integer_coefficients":coefficients,
        "original_Gram_rhs_sum":total,"removed_proved_zero_odd_columns":removed,
        "active_original_support_hex":hex(mask),"parity_rhs":rhs,
        "forbidden_vertex_certificate":proposal,**checked,
        "scope":"binary selectors satisfying original Gram equations and the112 proved-zero premises"}


def scan(root,preparation,directory):
    assert not directory.exists(); directory.mkdir(parents=True)
    started = time.monotonic(); deadline = started+LIMITS["shared_elimination_and_scan_seconds"]
    record = {"status":"RUNNING","source_bindings":source_bindings(),
        "preparation_sha256":sha(preparation.read_bytes()),"limits":LIMITS,
        "definition_sha256":json.loads(preparation.read_bytes())["definition_sha256"],
        "basis_files":[],"raw_prefix":0,"distinct_evaluated":0,"duplicates_skipped":0,
        "violations":0,"retained_cuts":0,"complete":False,"optimizer_calls":0}
    save(directory/"result.json",record)
    certificates, seen, transcript_bytes = [],set(),0
    max_data = LIMITS["maximum_transcript_bytes"]-LIMITS["result_reserve_bytes"]
    with (directory/"evaluations.jsonl").open("xb",buffering=0) as trace, (directory/"cuts.jsonl").open("xb",buffering=0) as cuts:
        try:
            prep,data = prepared(root,preparation,deadline)
            record["definition_sha256"] = prep["definition_sha256"]
            record["point_denominator"] = str(data["denominator"])
            record["odd_denominator_consistency_witness"] = data["mod2_point_assignment_hex"]
            for order in range(2):
                cert = basis.rref(data["rows"],data["orders"][order],deadline)
                check = verify_basis(data,order,cert,deadline)
                payload = canonical({"order":order,"certificate":pack_certificate(cert),"check":check})
                if transcript_bytes+len(payload) > max_data:
                    raise TimeoutError("transcript byte cap before basis certificate")
                name = f"basis-{order:02d}.json"
                (directory/name).write_bytes(payload); transcript_bytes += len(payload)
                certificates.append(cert)
                record["basis_files"].append({"path":name,"sha256":sha(payload),"rank":cert["rank"]})
                save(directory/"result.json",record)
            assert certificates[0]["rank"] == certificates[1]["rank"]
            r = certificates[0]["rank"]
            record["planned_raw_candidates"] = 41041+r*(r+1)
            assert record["planned_raw_candidates"] <= LIMITS["raw_candidate_upper_bound"]
            for raw_id,f,indices,row in candidates(data,certificates):
                basis.tick(deadline)
                assert raw_id == record["raw_prefix"]
                key = row[:2]
                if key in seen:
                    record["duplicates_skipped"] += 1
                else:
                    proposal = parity.closest_forbidden(list(basis.sites(row[0])),row[1],data["point"],data["denominator"])
                    assert proposal is not None
                    violated = proposal["strictly_violated"]
                    retain = violated and record["retained_cuts"] < LIMITS["maximum_retained_cuts"]
                    cut = full_cut(data,raw_id,f,indices,row,proposal,deadline) if retain else None
                    entry = canonical([raw_id,f,indices,proposal["distance_numerator"]])
                    cut_raw = canonical(cut) if cut is not None else b""
                    if transcript_bytes+len(entry)+len(cut_raw) > max_data:
                        raise TimeoutError("transcript byte cap before next complete evaluation")
                    if cut_raw:
                        assert cuts.write(cut_raw) == len(cut_raw)
                    assert trace.write(entry) == len(entry)
                    transcript_bytes += len(entry)+len(cut_raw)
                    seen.add(key)
                    record["distinct_evaluated"] += 1
                    record["violations"] += int(violated)
                    record["retained_cuts"] += int(retain)
                record["raw_prefix"] += 1
                if record["raw_prefix"] % 256 == 0:
                    save(directory/"result.json",record)
            assert record["raw_prefix"] == record["planned_raw_candidates"]
            record.update(status="COMPLETE: finite three-family exact parity census",complete=True)
        except TimeoutError as error:
            record.update(status="PARTIAL: only completed exact witnesses retained",stop_reason=str(error))
        except Exception as error:
            record.update(status="ERROR: no unchecked restriction accepted",error_type=type(error).__name__,error=str(error))
            raise
        finally:
            record["transcript_bytes_excluding_reserved_result"] = transcript_bytes
            record["artifact_bindings"] = {p.name:{"sha256":sha(p.read_bytes()),"bytes":p.stat().st_size}
                for p in (directory/"evaluations.jsonl",directory/"cuts.jsonl")}
            record["elapsed_seconds"] = time.monotonic()-started
            save(directory/"result.json",record)
    return record


def replay(root,preparation,directory,output):
    assert not output.exists()
    started = time.monotonic(); deadline = started+LIMITS["cold_replay_seconds"]
    prep,data = prepared(root,preparation,deadline)
    result = json.loads((directory/"result.json").read_bytes())
    assert result["source_bindings"] == source_bindings() and result["limits"] == LIMITS
    assert result["preparation_sha256"] == sha(preparation.read_bytes())
    assert result["definition_sha256"] == prep["definition_sha256"]
    assert result["status"].startswith(("COMPLETE:","PARTIAL:"))
    certificates, bytes_read = [],0
    for order,item in enumerate(result["basis_files"]):
        raw = (directory/item["path"]).read_bytes()
        assert sha(raw) == item["sha256"]; bytes_read += len(raw)
        saved = json.loads(raw); assert saved["order"] == order
        cert = unpack_certificate(saved["certificate"])
        assert verify_basis(data,order,cert,deadline) == saved["check"]
        assert cert["rank"] == item["rank"]
        certificates.append(cert)
    assert len(certificates) <= 2
    for name,item in result["artifact_bindings"].items():
        raw = (directory/name).read_bytes()
        assert sha(raw) == item["sha256"] and len(raw) == item["bytes"]
        bytes_read += len(raw)
    assert bytes_read == result["transcript_bytes_excluding_reserved_result"]
    assert bytes_read <= LIMITS["maximum_transcript_bytes"]-LIMITS["result_reserve_bytes"]
    seen, duplicates, evaluated, violations, retained, count = set(),0,0,0,0,0
    with (directory/"evaluations.jsonl").open("rb") as trace, (directory/"cuts.jsonl").open("rb") as cuts:
        if result["raw_prefix"]:
            assert len(certificates) == 2
            for raw_id,f,indices,row in candidates(data,certificates):
                if raw_id >= result["raw_prefix"]:
                    break
                basis.tick(deadline)
                if row[:2] in seen:
                    duplicates += 1
                else:
                    proposal = parity.closest_forbidden(list(basis.sites(row[0])),row[1],data["point"],data["denominator"])
                    assert json.loads(next(trace)) == [raw_id,f,indices,proposal["distance_numerator"]]
                    violated = proposal["strictly_violated"]
                    if violated and retained < LIMITS["maximum_retained_cuts"]:
                        expected = full_cut(data,raw_id,f,indices,row,proposal,deadline)
                        assert json.loads(next(cuts)) == expected
                        retained += 1
                    seen.add(row[:2]); evaluated += 1; violations += int(violated)
                count += 1
        assert next(trace,None) is None and next(cuts,None) is None
    assert [count,evaluated,duplicates,violations,retained] == [result[k] for k in
        ("raw_prefix","distinct_evaluated","duplicates_skipped","violations","retained_cuts")]
    if len(certificates) == 2:
        assert certificates[0]["rank"] == certificates[1]["rank"]
        r = certificates[0]["rank"]
        assert result["planned_raw_candidates"] == 41041+r*(r+1) <= LIMITS["raw_candidate_upper_bound"]
        if result["complete"]:
            assert count == result["planned_raw_candidates"]
    else:
        assert count == 0 and not result["complete"]
    report = {"status":"PASS: exact row-span, current-point prefix and original-Gram cut witnesses replayed",
        "source_bindings":source_bindings(),"result_sha256":sha((directory/"result.json").read_bytes()),
        "complete_declared_families":result["complete"],"raw_prefix":count,
        "distinct_equations_checked":evaluated,"duplicates_skipped":duplicates,
        "exact_violations":violations,"retained_cuts_checked":retained,
        "RREF_elimination_repeated":False,"optimizer_calls":0,
        "elapsed_seconds":time.monotonic()-started}
    save(output,report)
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode",choices=("prepare","scan","replay"))
    p.add_argument("--root",type=Path,default=ROOT)
    p.add_argument("--preparation",type=Path)
    p.add_argument("--directory",type=Path)
    p.add_argument("--output",type=Path)
    a = p.parse_args()
    if a.mode == "prepare":
        assert a.output is not None
        result = prepare(a.root,a.output)
    elif a.mode == "scan":
        assert a.preparation is not None and a.directory is not None
        result = scan(a.root,a.preparation,a.directory)
    else:
        assert a.preparation is not None and a.directory is not None and a.output is not None
        result = replay(a.root,a.preparation,a.directory,a.output)
    print(json.dumps({k:v for k,v in result.items() if k not in ("definition","source_bindings")},indent=2),flush=True)


if __name__ == "__main__":
    main()
