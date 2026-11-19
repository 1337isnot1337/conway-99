"""A universal guarded cover from the certified one-anchor exterior core.

If the anchor is selected and every selected eligible neighbor belongs to B,
its actual edge bits on B satisfy all retained mixed rows and pair clauses.
The checked DRAT core forbids that. Hence at least one eligible signature
outside B must be selected. No solver, encoding or proof checker is called.
"""
import gzip
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
BASE = "experiments/logs/root-prism-free/"
INPUTS = {
    "attribution": (BASE + "f0-exterior-retained-attribution01.json", "a46d4e7ac2a74fc10641db76e16b0d0d7d64be26024ee15a2ae526e113c5d932"),
    "model": (BASE + "f0-fixed-selection-exterior-direct01/model.json", "ec482e37e989a4657a0f7efb801c875062575fa2786efea72ba37c111974b3a9"),
    "baseline": (BASE + "f0-boolean-fractional-model.json.gz", "703206929c9c85a40ac4ddcbfb1708c716c288482cf50c77a32249404e35b782"),
    "cold": (BASE + "f0-fixed-selection-exterior-query-run01-cold/report.json", "3367e029d8a28ce7195ff7897a2b020d4b3f9cffd2b44c9e955ba048dcf03363"),
    "owner": (BASE + "f0-fixed-selection-exterior-query-run01-cold/owner.json", "e600a979c1f5709016fc6bf1d6586cf4dcd30534d2d6b9dc969f19f62ab462b2"),
    "retained": (BASE + "f0-fixed-selection-exterior-query-run01/retained.cnf", "aa4e78e057ed8b70e88ce4a003e0e8d1b47a62bdac1d0c36b5e40e95e46b962a"),
    "proof": (BASE + "f0-fixed-selection-exterior-query-run01/retained.drat", "4847c6e13804286495cfe90237dbd2acc1bffc683111ca793eb7cd9b72300176"),
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read(key, raw=False):
    name, expected = INPUTS[key]
    data = (ROOT / name).read_bytes()
    assert sha(data) == expected
    return data if raw else json.loads(gzip.decompress(data) if name.endswith(".gz") else data)


def derive():
    started = time.monotonic()
    att, model, baseline, cold, owner = [read(k) for k in ("attribution", "model", "baseline", "cold", "owner")]
    proof = read("proof", raw=True)
    assert proof and owner["fixed_selection_excluded"] and owner["report_accepted"]
    assert owner["report_sha256"] == INPUTS["cold"][1]
    assert cold["status"] == "PASS_COLD_REBUILD_RETAINED_INPUTS_AND_DRAT"
    assert cold["retained_cnf_sha256"] == INPUTS["retained"][1]
    assert cold["retained_proof_sha256"] == INPUTS["proof"][1]
    assert att["status"] == "PASS_COMPLETE_RETAINED_CLAUSE_ATTRIBUTION"
    assert att["removing_read_only_markers_recovers_original_AST"]
    assert att["complete_CNF_byte_hash_reproduced"] == model["cnf_sha256"] == cold["full_CNF_sha256"]
    data = model["data"]
    selected, edges = data["design_source_indices"], data["edge_domain"]
    assert att["common_primary_endpoints"] == [23] and att["common_primary_signatures"] == [178]
    vertex, anchor = 23, 178
    groups = {g["group_id"]: g for g in att["hit_groups"]}
    core = baseline["validation"]["core"]
    triples = baseline["validation"]["triples"]
    masks = [sum(1 << i for i in h) for h in triples]
    adjacency = [(row >> 3) & ((1 << 18) - 1) for row in core[3:21]]
    targets = [[2 - int(mask >> i & 1) - (adjacency[i] & mask).bit_count() for i in range(18)] for mask in masks]
    assert selected[vertex] == anchor and triples[anchor] == [2, 8, 13]
    assert targets[anchor] == data["targets"][vertex]
    eligible = [b for b in range(480) if b != anchor and (masks[b] & masks[anchor]).bit_count() <= 1
                and all(targets[anchor][i] > 0 for i in triples[b])
                and all(targets[b][i] > 0 for i in triples[anchor])]
    saved_edges = baseline["validation"]["edges"]
    assert eligible == sorted(v if u == anchor else u for u, v in saved_edges if anchor in (u, v))
    available = sorted(set(eligible).intersection(selected))
    incident = {i + 1: (v if u == vertex else u) for i, (u, v) in enumerate(edges) if vertex in (u, v)}
    assert sorted(selected[v] for v in incident.values()) == available
    retained = []
    for line in read("retained", raw=True).decode().splitlines():
        if line and line[0] not in "cp":
            row = list(map(int, line.split()))
            assert row[-1] == 0
            retained.append(row[:-1])
    assert retained == [r["retained_clause"] for r in att["retained_clause_attribution"]]
    aux_seen, row_witnesses, pair_witnesses = set(), [], []
    for g in groups.values():
        if g["kind"] == "mixed":
            assert g["a"] == vertex and g["anchor_signature"] == anchor
            site = g["core_site"]
            expected = [[var, selected[v]] for var, v in incident.items() if site in triples[selected[v]]]
            assert expected == g["complete_row_terms"] and g["target"] == targets[anchor][site]
            auxiliaries = set(range(g["first_auxiliary_after"] + 1, g["last_auxiliary"] + 1))
            assert not (auxiliaries & aux_seen)
            aux_seen.update(auxiliaries)
            row_witnesses.append({"site": site, "target": g["target"], "support": [b for _, b in expected]})
        else:
            assert g["kind"] == "pair_cap" and g["pair_capacity"] == 0
            b, c = g["pair_signatures"]
            assert (masks[b] & masks[c]).bit_count() == 2
            pair_witnesses.append({"pair": [b, c], "shared_core_sites": sorted(set(triples[b]) & set(triples[c]))})
    for entry in att["retained_clause_attribution"]:
        row, g = entry["retained_clause"], groups[entry["group_id"]]
        if g["kind"] == "mixed":
            support = {var for var, _ in g["complete_row_terms"]}
            for literal in row:
                var = abs(literal)
                if var <= len(edges):
                    assert var in support and var in incident
                else:
                    assert g["first_auxiliary_after"] < var <= g["last_auxiliary"]
        else:
            assert len(row) == 2 and all(literal < 0 and -literal in incident for literal in row)
            assert sorted(selected[incident[-literal]] for literal in row) == sorted(g["pair_signatures"])
    outside = sorted(set(eligible) - set(available))
    terms = sorted([[anchor, 1]] + [[b, -1] for b in outside])
    violation = sum(coef for b, coef in terms if b in selected)
    assert violation == 1 and anchor not in eligible
    return {"status": "EXACT_UNIVERSAL_GUARDED_NEIGHBOR_COVER", "source_sha256": sha(Path(__file__).read_bytes()),
            "inputs": INPUTS, "anchor": anchor, "anchor_triple": triples[anchor],
            "complete_original_eligible_neighbors": eligible, "saved_available_neighbors": available,
            "outside_saved_neighbor_domain": outside, "mixed_rows": row_witnesses,
            "zero_capacity_pairs": pair_witnesses, "retained_clauses_checked": len(retained),
            "all_retained_primary_variables_incident_to_anchor": True,
            "all_retained_auxiliaries_local_to_disjoint_mixed_encodings": True,
            "cut": {"terms": terms, "rhs": 0}, "saved_selection_violation": violation,
            "validity": "Actual anchor neighbors confined to B satisfy these mixed rows and pair AMOs; the independently checked retained core is UNSAT.",
            "all_other_selectors_free": True, "second_component_free": True,
            "new_SAT_or_LP_calls": 0, "DRAT_repeated": False,
            "shorter_positive_incidence_pattern_claimed": False, "seconds": time.monotonic() - started}


if __name__ == "__main__":
    if not __debug__:
        raise RuntimeError("assertions required")
    path = Path(sys.argv[1])
    assert not path.exists()
    result = derive()
    path.write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n")
    print(json.dumps({"status": result["status"], "seconds": result["seconds"],
                      "sha256": sha(path.read_bytes()), "terms": len(result["cut"]["terms"]),
                      "available_neighbors": len(result["saved_available_neighbors"]),
                      "eligible_neighbors": len(result["complete_original_eligible_neighbors"])}))
