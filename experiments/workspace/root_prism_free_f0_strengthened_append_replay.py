"""Independent protobuf-only check of the strengthened literal Boolean model.

Reconstruct all six added row blocks from accepted proof artifacts. Check each
complete ConstraintProto and the complete preserved parent bytes. This source
imports no producer, public native model API, or optimizer.
"""
import argparse
import gzip
import hashlib
import importlib.metadata
import json
import math
from pathlib import Path
import re
import resource
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parents[2]
PRODUCER_PATH = "experiments/workspace/root_prism_free_f0_strengthened_append.py"
PRODUCER_SHA = "9879d5ad46b58ab8e4e2eb58fb302e7c140a06bd3f7b3bf3cb47f82e25e99716"
PARENT_SHA = "4505234d13039159c3191918f7db729819ad6ed25f46e538d91975466d660e83"
PARENT_BYTES, PARENT_ROWS, VARIABLES = 33451907, 168050, 68934
EDGE_SHA = "411052a41a473bb7199fe277516fb60c54018dec120309622a499229579791bb"
KERNEL_RAW_SHA = "a963a88606a9fad78576d711f6ef7bf67eb03032176cebc2af5af700ea7c6708"
FOUR_KEYS_SHA = "2adfcc619820604a3f49463bd0fd8109113ab7ce13bceadcc49554533b09dd1c"
TRIANGLE_RECORDS_SHA = "60dd838a427e23b5d3c773e7eb8ecb9852e77a88bd0d9e1ac647e51be7965ff8"
FAMILIES = ["three_one_edge", "three_path", "four_retained", "triangle_cover", "spectral_edge_zero", "signed_one_edge"]
COUNTS = dict(zip(FAMILIES, [1224, 57996, 23010, 6990, 72, 252]))
TERMS = dict(zip(FAMILIES, [2448, 173988, 401874, 20970, 72, 1008]))
CHECK_SECONDS = 90
PINNED_INPUTS = {
    "parent_cold": "a907d1c0f51f893166f32b1aab136d885b412cf0aecbdfed2a938fdaaf373efb",
    "three_cold": "be7b4c812e50fa9575d961022e05f8cdbe2f414f9d5c4c522eecf23faa7bd214",
    "four_theorem_review": "3b3a41cb384105af51d3b9ae7948af857514dc9e31417a8e7e320816a42c86ed",
    "triangle_cold_summary": "8e8fe47a1527cb6d779fd05e174449983f7c3beb2409a5edf80ed682a46cdcfc",
    "spectral_cold": "e8d27725afb707867f6683604ff1f3123f8960305c721058f495883f23476349",
}
REQUIRED_AUTHORITIES = {
    "parent_cold", "parent_cold_owner", "three_cold", "three_cold_owner",
    "four_certificate_replay", "four_certificate_finalization",
    "four_root_acceptance", "four_theorem_review",
    "triangle_cold_summary", "triangle_root_acceptance",
    "spectral_cold", "spectral_root_acceptance",
    "signed_finalization", "signed_root_acceptance",
}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def reference(path):
    path = Path(path).resolve()
    data = path.read_bytes()
    return {"path": str(path.relative_to(ROOT)), "sha256": sha(data), "bytes": len(data)}


def bound_bytes(ref):
    path = (ROOT / ref["path"]).resolve()
    path.relative_to(ROOT)
    data = path.read_bytes()
    assert sha(data) == ref["sha256"], ref["path"]
    assert "bytes" not in ref or type(ref["bytes"]) is int and len(data) == ref["bytes"]
    return data


def same_reference(a, b):
    assert (a["path"], a["sha256"]) == (b["path"], b["sha256"])
    for ref in (a, b):
        if "bytes" in ref:
            assert type(ref["bytes"]) is int
            assert (ROOT / ref["path"]).stat().st_size == ref["bytes"]


def check_time(deadline):
    if time.monotonic() >= deadline:
        raise TimeoutError("independent strengthened append 90-second check deadline")


def save(path, value):
    with Path(path).open("xb") as stream:
        stream.write(canonical(value) + b"\n")


def integer(value):
    if type(value) is int:
        return value
    assert type(value) is str and re.fullmatch(r"0|-?[1-9][0-9]*", value)
    return int(value)


def key(lower, upper, entries):
    assert type(lower) is type(upper) is int and lower <= upper
    assert all(type(v) is type(c) is int and 0 <= v < VARIABLES and c != 0 for v, c in entries)
    assert len({v for v, c in entries}) == len(entries)
    return [lower, upper, sorted(entries)]


def expected_row(pb, row_key):
    lower, upper, entries = row_key
    assert key(lower, upper, entries) == row_key
    row = pb.ConstraintProto()
    row.linear.vars.extend(v for v, c in entries)
    row.linear.coeffs.extend(c for v, c in entries)
    row.linear.domain.extend([lower, upper])
    return row


def exact_row(pb, actual, row_key):
    assert actual.SerializeToString() == expected_row(pb, row_key).SerializeToString()


def signed_key(selectors, edge_ids, mask):
    assert type(mask) is int and mask in (1, 2, 4)
    assert len(selectors) == len(edge_ids) == 3
    assert all(type(v) is int and 0 <= v < 480 for v in selectors)
    assert selectors == sorted(set(selectors))
    assert all(type(e) is int and 0 <= e < 68394 for e in edge_ids)
    assert len(set(edge_ids)) == 3
    present = {1: 0, 2: 1, 4: 2}[mask]
    isolated = selectors[2 - present]
    return key(-2, 1, [[isolated, 1]] + [[540 + e, 1 if j == present else -1] for j, e in enumerate(edge_ids)])


def controls():
    from ortools.sat import cp_model_pb2 as pb
    examples = [
        key(0, 1, [[2, 1], [542, 1]]),
        key(-1, 0, [[3, -1], [541, 1], [545, 1]]),
        key(-2, 0, [[1, -1], [4, -1], [540, 1], [543, 1], [548, 1]]),
        key(0, 2, [[541, 1], [543, 1], [547, 1]]),
        key(0, 0, [[546, 1]]),
        key(-2, 1, [[4, 1], [541, -1], [543, 1], [548, -1]]),
    ]
    rejected = 0
    for wanted in examples:
        actual = expected_row(pb, wanted)
        exact_row(pb, actual, wanted)
        for change in range(8):
            altered = pb.ConstraintProto()
            altered.CopyFrom(actual)
            if change == 0:
                altered.linear.vars[0] += 1
            elif change == 1:
                altered.linear.coeffs[0] *= -1
            elif change == 2:
                altered.linear.domain[0] -= 1
            elif change == 3:
                altered.linear.domain[1] += 1
            elif change == 4:
                altered.enforcement_literal.append(0)
            elif change == 5:
                altered.name = "unexpected name"
            elif change == 6:
                altered.bool_or.literals.append(0)
            else:
                altered.MergeFromString(bytes([128, 6, 1]))
            try:
                exact_row(pb, altered, wanted)
            except AssertionError:
                rejected += 1
            else:
                raise AssertionError("mutated entire constraint accepted")
    assert rejected == 48
    assignments = 0
    for mask in (1, 2, 4):
        row = signed_key([0, 1, 2], [0, 1, 2], mask)
        for selected in range(8):
            x = [(selected >> i) & 1 for i in range(3)]
            for pattern in range(8):
                y = [(pattern >> i) & 1 for i in range(3)]
                if any(y[e] > x[a] or y[e] > x[b] for e, (a, b) in enumerate(((0, 1), (0, 2), (1, 2)))):
                    continue
                values = dict(enumerate(x))
                values.update({540 + e: y[e] for e in range(3)})
                activity = sum(values[v] * c for v, c in row[2])
                assert activity >= -2
                assert (activity > 1) == (selected == 7 and pattern == mask)
                assignments += 1
    assert assignments == 54
    assert "ortools.sat.python.cp_model" not in sys.modules
    return {
        "schema": "conway99.f0.strengthened-append-independent-controls.v1",
        "status": "PASS_STRENGTHENED_APPEND_NATIVE_ROW_CONTROLS",
        "row_families": 6, "rejected_constraint_mutations": rejected,
        "signed_guard_activated_assignments": assignments,
        "unknown_protobuf_field_rejected": True, "source": reference(__file__),
        "producer_imports": 0, "CpModel_constructed": False,
        "CpSolver_constructed": False, "optimizer_calls": 0,
    }


def load_authorities(cfg):
    loaded, raw_hashes = {}, {}
    for name, ref in cfg["inputs"].items():
        if name == "parent_model":
            continue
        data = bound_bytes(ref)
        if ref["path"].endswith(".gz"):
            data = gzip.decompress(data)
        raw_hashes[name] = sha(data)
        if "raw_sha256" in ref:
            assert raw_hashes[name] == ref["raw_sha256"]
        if "raw_bytes" in ref:
            assert len(data) == ref["raw_bytes"]
        loaded[name] = json.loads(data)
    authority_names = set()
    for rule in cfg["authorities"]:
        name = rule["input"]
        authority_names.add(name)
        assert loaded[name][rule.get("status_field", "status")] == rule["expected_status"]
    assert REQUIRED_AUTHORITIES <= authority_names
    for name, expected in PINNED_INPUTS.items():
        assert cfg["inputs"][name]["sha256"] == expected
    parent = loaded["parent_cold"]
    assert parent["status"] == "PASS_INDEPENDENT_COMPLETE_BOOLEAN_SHARED_MODEL"
    assert parent["native_raw_model_sha256"] == PARENT_SHA
    assert parent["native_raw_model_bytes"] == PARENT_BYTES
    assert parent["complete_parent_bytes_checked"] is True
    assert parent["optimizer_calls"] == 0
    same_reference(parent["preparation_inputs"]["model"], cfg["inputs"]["parent_model"])
    three = loaded["three_cold"]
    assert three["status"] == "PASS_INDEPENDENT_COMPLETE_LITERAL_PRISM_TRANSFER"
    assert three["model_raw_sha256"] == PARENT_SHA
    assert three["all_current_native_receipts_and_complete_origins_checked"] is True
    assert three["all_saved_six_site_graphs_and_forced_nonedge_premises_checked"] is True
    same_reference(three["complete_inventory"], cfg["inputs"]["three_inventory"])
    assert raw_hashes["three_inventory"] == three["inventory_raw_sha256"]
    for name, owner_name in (("parent_cold", "parent_cold_owner"), ("three_cold", "three_cold_owner")):
        owner = loaded[owner_name]
        assert owner["report_accepted"] is True
        same_reference(owner["report"], cfg["inputs"][name])
        supervision = owner["supervision"]
        assert supervision["exit_code"] == 0 and supervision["child_reaped"] is True
        assert supervision["new_process_group"] is True and supervision["hard_timeout"] is False
    assert loaded["four_theorem_review"]["status"] == "PASS_COMPLETE_STANDALONE_FOUR_EXTERIOR_PRISM_PROOF"
    four_acceptance = loaded["four_root_acceptance"]
    for field, name in (("complete_reconstruction", "four_inventory"),
                        ("certificate_replay", "four_certificate_replay"),
                        ("certificate_finalization", "four_certificate_finalization"),
                        ("proof_review", "four_theorem_review")):
        same_reference(four_acceptance[field], cfg["inputs"][name])
    bound_bytes(four_acceptance["standalone_necessary_inequality_proof"])
    assert four_acceptance["new_complete_reconstruction_is_acceptance_basis"] is True
    assert four_acceptance["every_live_case_reconstructed_and_premises_checked"] is True
    assert four_acceptance["all_saved_row_masks_and_retained_ids_checked"] is True
    assert four_acceptance["ordered_row_keys_sha256"] == FOUR_KEYS_SHA
    assert loaded["four_certificate_finalization"]["all_input_bytes_reverified"] is True
    spectral = loaded["spectral_cold"]
    assert spectral["status"] == "PASS_COMPLETE_INDEPENDENT_SPECTRAL_GAP_PAIR_CENSUS"
    assert spectral["complete"] is True and spectral["all405426_saved_integer_determinants_checked"] is True
    assert raw_hashes["kernels"] == KERNEL_RAW_SHA
    return loaded, raw_hashes

def signed_rows(loaded, edges, edge_index, old_zeros, triangle_records, deadline, facts):
    report = loaded["signed_certificates"]
    assert report["status"] == "PASS_252_PROVIDED_SINGLE_EDGE_PSD_CERTIFICATES"
    assert report["complete"] is True and report["error"] is None
    assert report["certified_records"] == report["provided_target_count"] == 252
    assert report["unprocessed_target_count"] == 0
    certificates = report["certificates"]
    assert len(certificates) == 252
    kernels = {k["family"]: k for k in loaded["kernels"]["kernels"]}
    hashes = {
        "plus": "91017b1ad1ea6ff3433e91030586ec820f939a158f8cf3aab0cbf77e4ef574ed",
        "minus": "3ec5835de875dc50cb9f349deb2bbd9bd16457657917b2e267a444d38e642b3d",
    }
    origins, seen, values = {}, set(), []
    for index, certificate in enumerate(certificates):
        if index % 32 == 0:
            check_time(deadline)
        assert certificate["certificate_index"] == index
        selectors, mask = certificate["selectors"], certificate["edge_pattern_mask"]
        assert len(selectors) == 3 and selectors == sorted(set(selectors))
        assert all(type(v) is int and 0 <= v < 480 for v in selectors)
        assert type(mask) is int and mask in (1, 2, 4)
        identity = tuple(selectors) + (mask,)
        assert identity not in seen
        seen.add(identity)
        pairs = [(selectors[0], selectors[1]), (selectors[0], selectors[2]), (selectors[1], selectors[2])]
        edge_ids = [edge_index[pair] for pair in pairs]
        assert certificate["edge_ids"] == edge_ids
        parent_index = certificate["parent_record_index"]
        assert type(parent_index) is int and 0 <= parent_index < len(triangle_records)
        assert triangle_records[parent_index][:3] == selectors
        family = certificate["rejecting_family"]
        assert family in hashes
        kernel = kernels[family]
        assert kernel["primitive_kernel_sha256"] == certificate["primitive_kernel_sha256"] == hashes[family]
        divisor = integer(kernel["common_numerator_divisor"])
        assert divisor > 0 and len(kernel["diagonal_x"]) == 480 and len(kernel["off_diagonal_Z"]) == 114960

        def primitive(value):
            value = integer(value)
            assert value % divisor == 0
            return value // divisor

        diagonal = [primitive(kernel["diagonal_x"][v]) for v in selectors]
        assert all(v > 0 for v in diagonal)
        off = []
        for bit, (a, b) in enumerate(pairs):
            position = 480 * a - a * (a + 1) // 2 + b - a - 1
            value = primitive(kernel["off_diagonal_Z"][position])
            if mask & (1 << bit):
                value += primitive(kernel["Y"])
            off.append(value)
        matrix = [diagonal[0], off[0], off[1], off[0], diagonal[1], off[2], off[1], off[2], diagonal[2]]
        assert certificate["primitive_matrix"] == [str(v) for v in matrix]
        assert len(certificate["negative_vector"]) == 3
        assert all(type(v) is str for v in certificate["negative_vector"])
        vector = [integer(v) for v in certificate["negative_vector"]]
        quadratic = sum(matrix[3 * i + j] * vector[i] * vector[j] for i in range(3) for j in range(3))
        assert quadratic < 0 and str(quadratic) == certificate["exact_quadratic_value"]
        values.append(str(quadratic))
        wanted = signed_key(selectors, edge_ids, mask)
        assert certificate["row_key"] == wanted
        present = {1: 0, 2: 1, 4: 2}[mask]
        assert certificate["present_edge_id"] == edge_ids[present]
        assert certificate["present_edge_endpoints"] == edges[edge_ids[present]]
        assert certificate["isolated_selector"] == selectors[2 - present]
        assert type(certificate["present_edge_known_zero"]) is bool
        assert certificate["present_edge_known_zero"] == (edge_ids[present] in old_zeros)
        encoded = (wanted[0], wanted[1], tuple(tuple(t) for t in wanted[2]))
        origins.setdefault(encoded, []).append(index)
    ordered = sorted(origins)
    rows = [[lo, hi, [list(t) for t in entries]] for lo, hi, entries in ordered]
    assert rows == report["row_keys"] and len(rows) == report["row_count"] == 252
    assert report["row_origins"] == [origins[k] for k in ordered]
    for row_index, encoded in enumerate(ordered):
        for origin in origins[encoded]:
            assert certificates[origin]["row_key_index"] == row_index
    assert sha(canonical(rows)) == report["row_keys_sha256"]
    facts["signed_certificates_recontracted"] = 252
    facts["signed_negative_values_sha256"] = sha(canonical(values))
    facts["signed_row_keys_sha256"] = sha(canonical(rows))
    facts["signed_pattern_census_reexecuted"] = False
    return rows


def expected_rows(loaded, edges, edge_index, deadline, facts):
    overlay = loaded["overlay"]
    assert overlay["status"] == "COMPLETE_LITERAL_PRISM_ZEROS_AND_CORE_PAIR_CLIQUES"
    assert overlay["complete_edge_order_sha256"] == EDGE_SHA
    old_zeros = set()
    for row in overlay["zero_rows"]:
        e = row["edge_id"]
        assert type(e) is int and 0 <= e < 68394 and e not in old_zeros
        assert row["variable_index"] == 540 + e
        old_zeros.add(e)
    assert len(old_zeros) == len(overlay["zero_rows"]) == 1884
    three, three_cold = loaded["three_inventory"], loaded["three_cold"]
    one, paths = three["proposed_one_edge"], three["proposed_paths"]
    assert len(one) == 1224 and one == sorted(one)
    assert len(paths) == 57996 and paths == sorted(paths)
    assert sha(canonical(one)) == three_cold["proposed_one_edge_sha256"] == "9b441e477b5efb86c197f01bbb8308b4bb1a6813c82896b2c5ca32306486720b"
    assert sha(canonical(paths)) == three_cold["proposed_paths_sha256"] == "afa12b69bfdcfc5c7265712c4704dac26d5a9f67465f3ba2ee2ad83c9ba6085c"
    assert sorted([e, c, w] for e, c, w, reason, premises in three["one_edge_ledger"] if reason == 4) == one
    assert sorted([a, e, f, p] for a, e, f, p, reason, premises in three["path_ledger"] if reason == 4) == paths
    for e, third, witness in one:
        assert all(type(v) is int for v in (e, third, witness))
        assert 0 <= e < 68394 and 0 <= third < 480 and third not in edges[e] and 0 <= witness < 9360
        yield "three_one_edge", key(0, 1, [[third, 1], [540 + e, 1]])
    for center, left, right, origin in paths:
        assert all(type(v) is int for v in (center, left, right, origin))
        assert 0 <= center < 480 and 0 <= left < right < 68394 and 0 <= origin < 107418
        assert center in edges[left] and center in edges[right]
        yield "three_path", key(-1, 0, [[center, -1], [540 + left, 1], [540 + right, 1]])

    four = loaded["four_inventory"]
    assert four["status"] == "COMPLETE_INDEPENDENT_ORIGINAL_KEYS_AND_ACTUAL_CROSS_QUOTA_CERTIFICATES"
    assert four["complete"] is True and four["failures"] == []
    keys, cases, certificates = four["row_keys"], four["cases"], four["certificates"]
    assert len(keys) == four["distinct_rows"] == 72468 and len(cases) == four["case_count"] == 73404
    assert sha(canonical(keys)) == four["ordered_row_keys_sha256"] == FOUR_KEYS_SHA
    assert four["original_edge_order_sha256"] == EDGE_SHA
    assert sum(len(r[2]) + 2 for r in keys) == four["terms"] == 1250496
    row_flags, origins = [0] * len(keys), [0] * len(keys)
    zero_cases, previous = 0, None
    for case_id, case in enumerate(cases):
        if case_id % 4096 == 0:
            check_time(deadline)
        assert len(case) == 7 and all(type(v) is int for v in case)
        e, i, j, row_id, q_left, q_right, flag = case
        assert 0 <= e < 68394 and 0 <= i < 18 and 0 <= j < 18 and i != j
        order = (e, i, j)
        assert previous is None or previous < order
        previous = order
        assert q_left in (1, 2) and q_right in (1, 2) and 0 <= flag <= 3
        if row_id == -1:
            assert e in old_zeros and flag == 0
            zero_cases += 1
            continue
        assert 0 <= row_id < len(keys) and e not in old_zeros
        a, b, positive = keys[row_id]
        assert [a, b] == edges[e] and e in positive
        row_flags[row_id] |= flag
        origins[row_id] += 1
    assert zero_cases == four["central_zero_cases"] == 936
    assert four["empty_side_cases"] == 0 and all(v == 1 for v in origins)
    assert row_flags == four["row_certificate_masks"]
    certificate_flags, seen_certificates = [0] * len(cases), set()
    for case_id, side, first, second, surplus in certificates:
        assert all(type(v) is int for v in (case_id, side, first, second, surplus))
        assert 0 <= case_id < len(cases) and side in (0, 1) and surplus >= 0
        assert (case_id, side) not in seen_certificates
        seen_certificates.add((case_id, side))
        e, i, j, row_id, q_left, q_right, flag = cases[case_id]
        assert row_id >= 0 and flag & (1 << side)
        b, c = edges[e]
        site = j if side == 0 else i
        assert first == 18 * b + site and second == 18 * c + site
        assert (q_left if side == 0 else q_right) == 1
        certificate_flags[case_id] |= 1 << side
    assert len(certificates) == 63336
    assert certificate_flags == [c[6] for c in cases]
    retained = [i for i, flag in enumerate(row_flags) if flag == 0]
    assert retained == four["retained_row_ids"] and len(retained) == 23010
    certificate_replay = loaded["four_certificate_replay"]
    assert certificate_replay["retained_row_ids"] == retained
    assert sha(canonical(retained)) == certificate_replay["retained_row_ids_sha256"] == loaded["four_root_acceptance"]["retained_row_ids_sha256"]
    assert certificate_replay["complete_coefficients_checked_for_certificates"] == len(certificates)
    assert certificate_replay["all_case_and_row_masks_compared"] is True
    assert certificate_replay["native_mixed_row_start"] == 154430
    assert loaded["four_root_acceptance"]["retained_rows"] == 23010
    assert loaded["four_root_acceptance"]["retained_terms"] == 401874
    assert sum(flag != 0 for flag in row_flags) == four["rows_with_sufficient_mixed_certificate"] == 49458
    facts["four_complete_original_rows"] = len(keys)
    facts["four_origin_cases_linked"] = len(cases)
    facts["four_mixed_certificate_links"] = len(certificates)
    facts["four_retained_row_ids_sha256"] = sha(canonical(retained))
    facts["four_ordered_original_row_keys_sha256"] = FOUR_KEYS_SHA
    facts["four_coefficient_proof_reexecution"] = False
    for row_id in retained:
        a, b, positive = keys[row_id]
        assert type(a) is type(b) is int and 0 <= a < b < 480
        assert positive == sorted(set(positive))
        assert all(type(e) is int and 0 <= e < 68394 and e not in old_zeros for e in positive)
        yield "four_retained", key(-2, 0, [[a, -1], [b, -1]] + [[540 + e, 1] for e in positive])

    family = loaded["triangle_forward"]["families"][0]
    assert family["family"] == "plus"
    records = family["nonpositive_determinant_records_with_nonnegative_proper_minors"]
    assert len(records) == 10830 and sha(canonical(records)) == TRIANGLE_RECORDS_SHA
    removed = 0
    for a, b, c, determinant, ab_minor, ac_minor, bc_minor in records:
        assert all(type(v) is int for v in (a, b, c)) and 0 <= a < b < c < 480
        assert integer(determinant) < 0
        edge_ids = [edge_index[(a, b)], edge_index[(a, c)], edge_index[(b, c)]]
        if any(e in old_zeros for e in edge_ids):
            removed += 1
            continue
        yield "triangle_cover", key(0, 2, [[540 + e, 1] for e in edge_ids])
    assert removed == 3840
    facts["triangle_existing_literal_zero_dispositions_checked"] = 10830
    facts["triangle_rows_removed_only_by_original_1884_zeros"] = removed

    spectral = loaded["spectral_forward"]["edge_zero_rows"]
    assert spectral == loaded["spectral_cold"]["mathematical"]["edge_zero_rows"] and len(spectral) == 132
    already = 0
    for a, b, e, old in spectral:
        assert all(type(v) is int for v in (a, b, e)) and 0 <= e < 68394
        assert edges[e] == [a, b] and type(old) is bool and old == (e in old_zeros)
        if old:
            already += 1
        else:
            yield "spectral_edge_zero", key(0, 0, [[540 + e, 1]])
    assert already == 60
    facts["spectral_all_132_rows_equal_complete_cold"] = True
    facts["spectral_original_literal_zeros_omitted"] = already
    for row in signed_rows(loaded, edges, edge_index, old_zeros, records, deadline, facts):
        yield "signed_one_edge", row

def replay(args):
    started = time.monotonic()
    from ortools.sat import cp_model_pb2 as pb
    import google.protobuf
    deadline = started + CHECK_SECONDS
    cfg_ref = reference(args.configuration)
    assert cfg_ref["sha256"] == args.configuration_sha256
    cfg = json.loads(bound_bytes(cfg_ref))
    assert cfg["source_sha256"] == PRODUCER_SHA
    assert sha((ROOT / PRODUCER_PATH).read_bytes()) == PRODUCER_SHA
    assert cfg["family_order"] == FAMILIES
    assert cfg["expected_family_counts"] == COUNTS and cfg["expected_family_terms"] == TERMS
    assert cfg["optimizer_calls"] == 0 and cfg["native_query_authorized"] is False
    assert importlib.metadata.version("ortools") == cfg["runtime"]["ortools"] == "9.15.6755"
    assert google.protobuf.__version__ == cfg["runtime"]["protobuf"] == "6.33.6"
    for ref in cfg["sources"].values():
        bound_bytes(ref)
    loaded, raw_hashes = load_authorities(cfg)
    check_time(deadline)
    parent = gzip.decompress(bound_bytes(cfg["inputs"]["parent_model"]))
    assert len(parent) == PARENT_BYTES and sha(parent) == PARENT_SHA

    directory = args.directory.resolve()
    report_ref, owner_ref = reference(directory / "report.json"), reference(directory / "owner.json")
    assert report_ref["sha256"] == args.report_sha256 and owner_ref["sha256"] == args.owner_sha256
    report, owner = json.loads(bound_bytes(report_ref)), json.loads(bound_bytes(owner_ref))
    status = "PASS_COMPLETE_STRENGTHENED_LITERAL_NATIVE_PREPARATION"
    assert report["schema"] == "conway99.f0.strengthened-append-preparation.v1"
    assert owner["schema"] == "conway99.f0.strengthened-append-owner.v1"
    assert report["status"] == owner["status"] == status and owner["report_accepted"] is True
    assert owner["mode"] == "prepare"
    source_ref = reference(ROOT / PRODUCER_PATH)
    for item in (report, owner):
        same_reference(item["source"], source_ref)
        same_reference(item["configuration"], cfg_ref)
        assert item["optimizer_calls"] == 0 and item["CpSolver_constructed"] is False
    same_reference(owner["report"], report_ref)
    supervision = owner["supervision"]
    assert supervision["status"] == "CHILD_EXITED" and supervision["returncode"] == 0
    assert supervision["child_reaped"] is True and supervision["owned_process_group_stopped"] is True
    assert owner["maximum_seconds"] == cfg["limits"]["prepare_owner_seconds"] == 135
    assert cfg["limits"]["prepare_worker_seconds"] == 120
    assert all(type(v) in (int, float) and math.isfinite(v) for v in (report["seconds"], owner["seconds"]))
    assert 0 <= report["seconds"] <= 120 and report["seconds"] <= owner["seconds"] <= 135
    assert owner["deadline_overrun_seconds"] == 0
    assert report["inputs"] == cfg["inputs"] and report["authorities"] == cfg["authorities"]
    assert report["runtime"]["ortools"] == "9.15.6755" and report["runtime"]["protobuf"] == "6.33.6"
    assert report["runtime"]["model_schema_sha256"] == sha(pb.DESCRIPTOR.serialized_pb)
    assert report["parent_raw_sha256"] == PARENT_SHA and report["parent_raw_bytes"] == PARENT_BYTES
    assert report["parent_rows"] == PARENT_ROWS and report["variables"] == VARIABLES
    assert report["family_order"] == FAMILIES and report["family_counts"] == COUNTS and report["family_terms"] == TERMS
    final_rows = PARENT_ROWS + sum(COUNTS.values())
    assert final_rows == report["rows"] == 257594
    for field in ("complete_parent_bytes_preserved", "parent_is_complete_raw_prefix", "no_variables_added_removed_or_identified"):
        assert report[field] is True
    for field in ("objective_hint_assumption_or_graph_symmetry_added", "native_query_run", "graph_constructed", "whole_component_excluded"):
        assert report[field] is False

    raw = (directory / "model.pb").read_bytes()
    archive = (directory / "model.pb.gz").read_bytes()
    suffix_archive = (directory / "suffix.pb.gz").read_bytes()
    assert gzip.decompress(archive) == raw
    suffix = gzip.decompress(suffix_archive)
    assert raw[:len(parent)] == parent and len(raw) == len(parent) + len(suffix)
    assert raw[len(parent):] == suffix
    model_sha = sha(raw)
    assert report["model"] == {
        "raw_bytes": len(raw), "raw_sha256": model_sha,
        "archive_bytes": len(archive), "archive_sha256": sha(archive),
        "suffix_raw_bytes": len(suffix), "suffix_raw_sha256": sha(suffix),
        "suffix_archive_bytes": len(suffix_archive), "suffix_archive_sha256": sha(suffix_archive),
    }
    native = report["native_transport"]
    assert native["native_raw_sha256"] == model_sha and native["native_raw_bytes"] == len(raw)
    assert native["complete_byte_comparison"] is True
    assert native["public_parse_return"] is True and native["public_parse_return_type"] == "bool"
    assert native["native_validation"] == "" and native["CpSolver_constructed"] is False and native["optimizer_calls"] == 0
    check_time(deadline)

    model = pb.CpModelProto()
    model.ParseFromString(raw)
    assert model.SerializeToString() == raw
    assert len(model.variables) == VARIABLES and len(model.constraints) == final_rows
    assert {field.name for field, value in model.ListFields()} <= {"name", "variables", "constraints"}
    edges = []
    for variable in model.variables[540:]:
        match = re.fullmatch(r"shared_edge_([0-9]{3})_([0-9]{3})", variable.name)
        assert match is not None and list(variable.domain) == [0, 1]
        a, b = map(int, match.groups())
        assert 0 <= a < b < 480
        edges.append([a, b])
    assert len(edges) == 68394 and sha(canonical(edges)) == EDGE_SHA
    assert len(set(tuple(edge) for edge in edges)) == 68394
    assert all(list(v.domain) == [0, 1] for v in model.variables[:480])
    edge_index = {tuple(edge): e for e, edge in enumerate(edges)}
    counts, terms = {name: 0 for name in FAMILIES}, {name: 0 for name in FAMILIES}
    digests = {name: hashlib.sha256() for name in FAMILIES}
    facts, offset, last_family = {}, PARENT_ROWS, -1
    for name, row in expected_rows(loaded, edges, edge_index, deadline, facts):
        family_index = FAMILIES.index(name)
        assert family_index >= last_family
        last_family = family_index
        assert offset < final_rows
        exact_row(pb, model.constraints[offset], row)
        counts[name] += 1
        terms[name] += len(row[2])
        digests[name].update(canonical(row) + b"\n")
        offset += 1
        if offset % 4096 == 0:
            check_time(deadline)
    assert offset == final_rows and counts == COUNTS and terms == TERMS
    row_hashes = {name: digest.hexdigest() for name, digest in digests.items()}
    assert report["family_row_jsonl_sha256"] == row_hashes
    del model.constraints[PARENT_ROWS:]
    assert len(model.constraints) == PARENT_ROWS and model.SerializeToString() == parent
    assert "ortools.sat.python.cp_model" not in sys.modules
    assert not any(name.startswith("highspy") or name.startswith("strengthened_append_transport") for name in sys.modules)
    check_time(deadline)
    result = {
        "schema": "conway99.f0.strengthened-append-independent-cold.v1",
        "status": "PASS_INDEPENDENT_COMPLETE_STRENGTHENED_LITERAL_NATIVE_APPEND",
        "source": reference(__file__), "configuration": cfg_ref,
        "producer_source": source_ref, "producer_report": report_ref, "producer_owner": owner_ref,
        "inputs": cfg["inputs"], "authorities": cfg["authorities"],
        "runtime": {"python": sys.version, "ortools": importlib.metadata.version("ortools"),
                    "protobuf": google.protobuf.__version__, "model_schema_sha256": sha(pb.DESCRIPTOR.serialized_pb)},
        "model": reference(directory / "model.pb"),
        "model_archive": reference(directory / "model.pb.gz"), "suffix_archive": reference(directory / "suffix.pb.gz"),
        "model_raw_sha256": model_sha, "model_raw_bytes": len(raw),
        "parent_raw_sha256": PARENT_SHA, "parent_raw_bytes": PARENT_BYTES,
        "parent_rows": PARENT_ROWS, "rows": final_rows, "variables": VARIABLES,
        "family_order": FAMILIES, "family_counts": counts, "family_terms": terms,
        "family_row_jsonl_sha256": row_hashes,
        "all_appended_rows_compared_exactly": sum(counts.values()),
        "all_appended_terms_checked": sum(terms.values()),
        "complete_parent_bytes_checked": True, "complete_parent_raw_byte_prefix_checked": True,
        "full_and_suffix_archives_checked": True,
        "all_variable_domains_names_and_metadata_preserved": True,
        "all_added_constraints_compared_as_complete_protobuf_messages": True,
        "family_provenance_checks": facts,
        "four_authority": "Standalone prism theorem plus complete compact reconstruction and accepted origin/coefficient replay; no unavailable old finite-census cold is used.",
        "producer_imports": 0, "protobuf_decoder_only": True, "native_model_decodes": 1,
        "native_model_builds": 0, "CpModel_constructed": False, "CpSolver_constructed": False,
        "optimizer_calls": 0, "all_pair_common_neighbor_caps_claimed": False,
        "graph_constructed": False, "whole_component_excluded": False,
        "maximum_seconds": CHECK_SECONDS, "seconds_before_report_serialization": time.monotonic() - started,
        "peak_rss_KiB": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    }
    serialized = canonical(result) + b"\n"
    check_time(deadline)
    with args.output.resolve().open("xb") as stream:
        stream.write(serialized)
    return result


if __name__ == "__main__":
    if not __debug__:
        raise RuntimeError("assertions are required")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("controls", "run"))
    parser.add_argument("--configuration", type=Path)
    parser.add_argument("--configuration-sha256")
    parser.add_argument("--directory", type=Path)
    parser.add_argument("--report-sha256")
    parser.add_argument("--owner-sha256")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.mode == "controls":
            result = controls()
            save(args.output.resolve(), result)
        else:
            assert all((args.configuration, args.configuration_sha256, args.directory, args.report_sha256, args.owner_sha256))
            result = replay(args)
        print(json.dumps({"status": result["status"], "output": reference(args.output)}, sort_keys=True), flush=True)
    except BaseException as error:
        error_path = args.output.with_name(args.output.stem + ".error.json")
        save(error_path.resolve(), {"schema": "conway99.f0.strengthened-append-independent-error.v1",
                                  "status": "UNACCEPTED_INDEPENDENT_CHECK_ERROR", "source": reference(__file__),
                                  "type": type(error).__name__, "message": str(error),
                                  "traceback": traceback.format_exc(), "optimizer_calls": 0})
        raise
