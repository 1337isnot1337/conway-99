"""Exact full21-core two-exterior-vertex PSD census; no point or optimizer."""
import argparse
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = "experiments/logs/root-prism-free/"
INPUTS = {
    "kernels": (BASE+"f0-full-core-schur-kernels01.json.gz", "a49b8309032b2c599c637285f4a4584bb7d55659640e594df1e6fdd50bf826c1"),
    "domain": (BASE+"f0-boolean-fractional-model.json.gz", "703206929c9c85a40ac4ddcbfb1708c716c288482cf50c77a32249404e35b782"),
    "moments": (BASE+"f0-second-moments-preparation02.json.gz", "404d91da35c798ba248887c22a7500957947e24b71d5197dc44432460e6d219e"),
    "reduction": (BASE+"f0-second-moments-reduced-model.json.gz", "73a50b431ac69ad57e10cff9aabe5c0b7d69ee075e95710b461f62b33fe2bbcf"),
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def build():
    data = {}
    for key, (path, expected) in INPUTS.items():
        raw = (ROOT/path).read_bytes()
        assert sha(raw) == expected
        data[key] = json.loads(gzip.decompress(raw))
    kernels = data["kernels"]["kernels"]
    assert [k["family"] for k in kernels] == ["plus", "minus"]
    edges = set(map(tuple, data["domain"]["validation"]["edges"]))
    assert len(edges) == 68394
    pairs = [(a, b) for a in range(480) for b in range(a+1, 480)]
    assert len(pairs) == 114960
    pmap = data["moments"]["pair_to_orbit"]
    fixed = {j for j, row in data["reduction"]["fixed_zero_original_variables"]}
    assert len(fixed) == 389 and len(pmap) == len(pairs)
    census = Counter()
    exclusions, equalities, minima = [], [], {}
    for k in kernels:
        assert len(k["diagonal_x"]) == 480 and min(k["diagonal_x"]) > 0
        assert len(k["off_diagonal_Z"]) == len(pairs)
        minima[k["family"]] = {"nonedge": None, "edge": None}
    for p, (a, b) in enumerate(pairs):
        already_zero = 5847+pmap[p] in fixed
        states = (0, 1) if (a, b) in edges else (0,)
        rejected = []
        for adjacency in states:
            values = {}
            for k in kernels:
                d1, d2 = k["diagonal_x"][a], k["diagonal_x"][b]
                cross = k["off_diagonal_Z"][p]+k["Y"]*adjacency
                determinant = d1*d2-cross*cross
                values[k["family"]] = determinant
                kind = "edge" if adjacency else "nonedge"
                prior = minima[k["family"]][kind]
                if prior is None or determinant < prior["determinant"]:
                    minima[k["family"]][kind] = {"determinant": determinant,
                                                 "pair": [a, b], "pair_orbit": pmap[p],
                                                 "already_fixed_zero": already_zero}
                census[k["family"]+"_"+kind+"_"+("negative" if determinant < 0 else "zero" if determinant == 0 else "positive")] += 1
            if min(values.values()) < 0:
                rejected.append(adjacency)
            if min(values.values()) == 0:
                equalities.append({"pair": [a, b], "adjacency": adjacency,
                                   "determinants": values, "already_fixed_zero": already_zero})
        if rejected:
            exclusions.append({"pair": [a, b], "pair_orbit": pmap[p],
                               "eligible_adjacency_states": list(states),
                               "rejected_states": rejected, "already_fixed_zero": already_zero})
        census["already_fixed_zero_pairs" if already_zero else "active_pairs"] += 1
    return {"status": "COMPLETE_EXACT_TWO_VERTEX_PSD_CENSUS", "source_sha256": sha(Path(__file__).read_bytes()),
            "inputs": {k: {"path": p, "sha256": h} for k, (p, h) in INPUTS.items()},
            "all480_selectors_retained": True, "all114960_pairs_retained": True,
            "eligible_adjacency_states": 114960+68394, "census": dict(census),
            "minimum_determinants": minima, "excluded_states": exclusions,
            "zero_determinant_states": equalities,
            "new_active_pair_state_exclusions": sum(not r["already_fixed_zero"] for r in exclusions),
            "optimizer_calls": 0, "point_loaded": False, "graph_existence_resolved": False,
            "scope": "Two-by-two principal minors only; no larger PSD or graph feasibility claim."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "replay"))
    parser.add_argument("--record", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = build()
    if args.mode == "prepare":
        assert not args.record.exists()
        args.record.write_text(json.dumps(result, indent=2)+"\n")
    else:
        assert json.loads(args.record.read_bytes()) == result
        assert args.output is not None and not args.output.exists()
        args.output.write_text(json.dumps({"status": "PASS: exact two-vertex PSD census replay",
                                          "source_sha256": result["source_sha256"],
                                          "record_sha256": sha(args.record.read_bytes()),
                                          "new_active_pair_state_exclusions": result["new_active_pair_state_exclusions"],
                                          "optimizer_calls": 0}, indent=2)+"\n")
    print(json.dumps({k: v for k, v in result.items() if k not in ("inputs", "excluded_states", "zero_determinant_states")}, indent=2))


if __name__ == "__main__":
    main()
