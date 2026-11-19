"""Bounded parity-cut discovery with independent, per-record proof replay.

The ordered search prefix is diagnostic. No family-exhaustion certificate is
needed for an individual original-Gram cut. Numerical/exact LP code is absent.
"""
import itertools
import json
from pathlib import Path
import time

import rook_case4_parity_cycle_v4 as previous

exact, weighted = previous.exact, previous.weighted
basis, parity = previous.basis, previous.parity


def screening_data(nums, den):
    assert den > 0 and all(type(n) is int and 0 <= n <= den for n in nums)
    return ([min(n, den-n) for n in nums], [abs(den-2*n) for n in nums],
            sum(1 << j for j, n in enumerate(nums) if 2*n > den))


def forbidden_distance(mask, rhs, minima, penalties, nearest):
    """Exact distance numerator; construct a full witness only on violation."""
    assert mask > 0 and rhs in (0, 1)
    cost, least, rest = 0, None, mask
    while rest:
        bit = rest & -rest
        a = bit.bit_length()-1
        cost += minima[a]
        least = penalties[a] if least is None else min(least, penalties[a])
        rest ^= bit
    if (mask & nearest).bit_count() % 2 == rhs:
        cost += least
    return cost


def controls():
    cases = 0
    for size in range(1, 5):
        for den in range(1, 5):
            for nums in itertools.product(range(den+1), repeat=size):
                data = screening_data(nums, den)
                for rhs in (0, 1):
                    direct = forbidden_distance((1 << size)-1, rhs, *data)
                    old = parity.closest_forbidden(list(range(size)), rhs, nums, den)
                    assert direct == old["distance_numerator"]
                    # Literal forbidden-vertex enumeration is independent of both formulas.
                    best = min(sum(den-n if z else n for z, n in zip(bits, nums))
                               for bits in itertools.product((0, 1), repeat=size)
                               if sum(bits) % 2 != rhs)
                    assert direct == best
                    cases += 1
    return {"exact_distance_literal_controls": cases,
            "case_point_scans": 0, "case_RREF": 0, "optimizer_calls": 0}


def file_bytes(value):
    return json.dumps(value, indent=2, allow_nan=False).encode()+b"\n"


def discover(state_path, directory, check_envelope, limits):
    started = time.monotonic()
    deadline = started+limits["discovery_cooperative_seconds"]
    result = {"status": "RUNNING: discovery prefix only", "state": previous.record_ref(state_path),
              "raw_prefix": 0, "distinct": 0, "duplicates": 0, "violations": 0,
              "retained": 0, "basis_files": [], "complete_cut_files": [],
              "exhaustion_certified": False, "optimizer_calls": 0}
    previous.save(directory/"result.json", result)
    certificates, seen, bytes_used = [], set(), 0
    with (directory/"evaluations.jsonl").open("xb", buffering=0) as evaluations:
        try:
            check_envelope(state_path)
            state, data = previous.checked_state(state_path, deadline)
            result["point_key"] = data["point_key"]
            allowed = state["scan_byte_allowance"]-limits["result_reserve_bytes"]
            assert allowed > 0
            existing = {entry["row_key"] for entry in state["cuts"]}
            retained_keys = set()
            slots = min(limits["cuts_per_discovery"], limits["maximum_cuts"]-len(state["cuts"]))
            assert slots > 0
            screen = screening_data(data["point"], data["denominator"])
            for order in range(2):
                certificate = basis.rref(data["rows"], data["orders"][order], deadline)
                check = weighted.verify_basis(data, order, certificate, deadline)
                assert certificate["rank"] == 286 and not certificate["inconsistent"]
                payload = exact.canonical({"order": order,
                    "certificate": weighted.pack_certificate(certificate), "check": check})
                if bytes_used+len(payload) > allowed:
                    raise TimeoutError("discovery transcript limit during basis preparation")
                path = directory/f"basis-{order:02d}.json"
                path.write_bytes(payload); bytes_used += len(payload)
                result["basis_files"].append(previous.record_ref(path))
                certificates.append(certificate)
                previous.save(directory/"result.json", result)
            for raw_id, family, indices, row in weighted.candidates(data, certificates):
                exact.tick(deadline)
                assert raw_id == result["raw_prefix"]
                if row[:2] in seen:
                    result["duplicates"] += 1
                else:
                    distance = forbidden_distance(row[0], row[1], *screen)
                    violated = distance < data["denominator"]
                    cut, envelope, envelope_raw, key = None, None, b"", None
                    if violated:
                        proposal = parity.closest_forbidden(list(basis.sites(row[0])), row[1],
                                                           data["point"], data["denominator"])
                        assert proposal["distance_numerator"] == distance and proposal["strictly_violated"]
                        form = parity.inequality(proposal)
                        key = exact.row_key(form)
                        assert key not in existing, "accepted current point violates an inherited cut"
                        if key not in retained_keys:
                            cut = weighted.full_cut(data, raw_id, family, indices, row, proposal, deadline)
                            exact.verify_cut(cut, data["gram"], data["zeros"], data["point"],
                                             data["denominator"], deadline)
                            envelope = {"state": previous.record_ref(state_path), "source_point": state["point"],
                                        "certificate": cut, "owner_checked": True,
                                        "independent_proof_replay_pending": True}
                            envelope_raw = file_bytes(envelope)
                    line = exact.canonical([raw_id, family, indices, distance])
                    if bytes_used+len(line)+len(envelope_raw) > allowed:
                        raise TimeoutError("discovery transcript limit before complete record")
                    evaluations.write(line); bytes_used += len(line)
                    if cut is not None:
                        path = directory/f"cut-{result['retained']:02d}.json"
                        assert not path.exists()
                        previous.save(path, envelope)  # temporary file then atomic rename
                        assert path.stat().st_size == len(envelope_raw)
                        bytes_used += len(envelope_raw)
                        result["complete_cut_files"].append(previous.record_ref(path))
                        retained_keys.add(key); result["retained"] += 1
                    seen.add(row[:2]); result["distinct"] += 1
                    result["violations"] += int(violated)
                result["raw_prefix"] += 1
                if result["retained"] == slots:
                    result["status"] = "DISCOVERED: declared cut quota reached; incomplete family allowed"
                    break
                if result["raw_prefix"] % 256 == 0:
                    previous.save(directory/"result.json", result)
            else:
                assert result["raw_prefix"] == limits["raw_words_per_discovery"]
                result["status"] = "STOP: finite candidate iterator ended; exhaustion not independently certified"
        except TimeoutError as exc:
            result.update(status="PARTIAL: discovery budget reached; complete cut files retained", reason=str(exc))
        except Exception as exc:
            result.update(status="ERROR: complete cut files require independent proof check",
                          error_type=type(exc).__name__, reason=str(exc))
        finally:
            result["transcript_bytes_owner_recorded"] = bytes_used
            result["seconds"] = time.monotonic()-started
            previous.save(directory/"result.json", result)
    return result


def certify(state_path, directory, check_envelope, limits):
    """Check only atomic complete proofs; never read bases or evaluation rows."""
    start = time.monotonic(); deadline = start+limits["proof_seconds"]
    state = check_envelope(state_path)
    # The source-bound native equations and prior zero face suffice here.
    # In particular, do not load either the old basis or a new search basis.
    native, model = previous.read_input("native"), previous.read_input("model")
    nums, den = previous.point_data(state["point"])
    data = {"gram": native["primary_inventory"]["Gram_rows"],
            "zeros": model["fixed_zero_columns"], "point": nums, "denominator": den}
    assert len(data["gram"]) == 630 and len(data["zeros"]) == 112
    assert all(nums[a] == 0 for a in data["zeros"])
    for _, _, quota, support in data["gram"]:
        exact.tick(deadline)
        assert sum(nums[a] for a in support) == quota*den
    assert exact.point_key(nums, den) == state["point_key"]
    existing = {entry["row_key"] for entry in state["cuts"]}
    additions, refs = [], []
    slots = min(limits["cuts_per_discovery"], limits["maximum_cuts"]-len(state["cuts"]))
    assert slots > 0
    paths = [directory/f"cut-{i:02d}.json" for i in range(slots)]
    present = [p for p in paths if p.exists()]
    assert present == paths[:len(present)], "complete records must form a prefix"
    assert set(directory.glob("cut-*.json")) == set(present), "undeclared complete cut file"
    for path in present:
        exact.tick(deadline)
        item = previous.read_record(path)
        assert item["state"] == previous.record_ref(state_path) and item["source_point"] == state["point"]
        cut = item["certificate"]
        assert 0 <= cut["raw_candidate_id"] < limits["raw_words_per_discovery"]
        checked = exact.verify_cut(cut, data["gram"], data["zeros"], data["point"],
                                   data["denominator"], deadline)
        key = exact.row_key(checked["inequality"])
        assert key not in existing and all(key != e["row_key"] for e in additions)
        ref = previous.record_ref(path); refs.append(ref)
        additions.append({"certificate": cut, "row_key": key,
                          "source_point": state["point"], "discovery_cut_file": ref})
    report = {"status": "PASS: individually complete original-Gram cut proofs",
              "state": previous.record_ref(state_path), "checked_cut_files": refs,
              "registry_additions": additions, "cuts_checked": len(additions),
              "seconds": time.monotonic()-start, "RREF_or_family_evaluations_repeated": False,
              "exhaustion_certified": False, "optimizer_calls": 0}
    assert not (directory/"proofs.json").exists()
    previous.save(directory/"proofs.json", report)
    return report
