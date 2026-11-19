"""Source-bound read-only review; no subject imports, census, CSP or optimizer."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FILES = {
    "domain_source": ("experiments/workspace/root_prism_free_f0_character_literal_lift.py", "3bf7f92502592bcda0b4dc71868a6745888c608b26d3f8e42f2771cf180c7252"),
    "CSP_source": ("experiments/workspace/root_prism_free_f0_literal_lift_csp.py", "15f139b54d5daebd5adbd4e4d475ff9a9734a52725abd7ac130984b5328fabfb"),
    "preparation": ("experiments/logs/root-prism-free/f0-character-literal-lift-preparation01.json.gz", "241cd14c61b465025c72ffcaa65af8e5c48e9e5a0eda7ea7d252e9d74b22db1e"),
    "cold": ("experiments/logs/root-prism-free/f0-character-literal-lift-preparation01-cold.json", "6cebe725527eaf28f3d075a3ad9741fcbcf50cdedd42107bdc5ebcbe857da72f"),
}


def main(output):
    assert not output.exists()
    values, bindings = {}, {}
    for name,(path,expected) in FILES.items():
        raw = (ROOT/path).read_bytes()
        actual = hashlib.sha256(raw).hexdigest()
        assert actual == expected, name
        bindings[name] = {"path":path,"sha256":actual,"bytes":len(raw)}
        if name.endswith("source"):
            bindings[name]["lines_read"] = len(raw.decode().splitlines())
        else:
            values[name] = json.loads(gzip.decompress(raw) if path.endswith(".gz") else raw)
    prep,cold = values["preparation"],values["cold"]
    inv = prep["inventory"]
    assert prep["status"] == "COMPLETE_INVERSE_TABLE_AND_BINARY_CSP_PREPARATION"
    assert cold["status"].startswith("PASS")
    assert cold["record_sha256"] == FILES["preparation"][1]
    assert cold["inventory"] == inv
    for key,value in {"selector_orbits":42,"literal_selectors":480,"refined_tuples":19331,
            "accepted_literal_masks":64144,"maximum_domain_size":12,
            "binary_constraints":861,"original_pair_orbits":9742,
            "proved_zero_pair_orbits":389,"all_production_candidates_queried":0,
            "optimizer_calls":0}.items():
        assert inv[key] == value
    report = {
        "status":"PASS: complete source and mathematical scope review",
        "review_source_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "bindings":bindings,
        "reviewed_source_lines":708,
        "checked_saved_inventory":inv,
        "findings":[
            "The42 disjoint selector orbits cover all480 literal selectors; every local subset is enumerated in its fixed literal order.",
            "Local deletions use only proved pair zeros and necessary original Gram capacities. Every admitted profile retains every subset preimage; signed characters retain their original orientation.",
            "The original9742 pair orbits partition all114960 literal pairs. Every pair orbit belongs either to one local table or one fixed unordered pair of selector orbits.",
            "Each of the861 binary relations compares the complete literal cross-pair histogram with the candidate target. Omitting zero entries from both dictionaries still enforces every zero target exactly.",
            "The count-column projection distinguishes Z populations from exterior Y populations and inserts all389 proved-zero pair targets explicitly.",
            "Arc-consistency deletions require absence of support in another current domain. Every replayed deletion is checked against the domains produced by prior deletions only.",
            "A split enumerates all current values in canonical order. UNSAT replay requires all children to be UNSAT and no unknown leaf; a partial tree cannot exclude the candidate.",
            "A returned assignment is checked directly, then all N, original Z and signed L populations are reconstructed from the literal selection.",
            "All172 original selector equalities are reported separately. A selector-moment lift that fails one of those rows is not promoted to an incidence solution.",
            "CSP rejection concerns only the fixed count assignment. Acceptance realizes selector moments only; exterior Y edges and a complete graph remain outside this model."
        ],
        "no_source_level_blocker_found":True,
        "subject_imported":False,"domain_or_tables_rebuilt":False,
        "controls_repeated":False,"CSP_search_called":False,
        "production_candidate_evaluated":False,"optimizer_called":False,
        "scope":"Full source reading plus saved hashes/inventory binding; no independent census or mathematical-result execution."
    }
    output.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps({"status":report["status"],"report_sha256":hashlib.sha256(output.read_bytes()).hexdigest(),"path":str(output)},indent=2))


if __name__ == "__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output",type=Path,required=True)
    main(p.parse_args().output)
