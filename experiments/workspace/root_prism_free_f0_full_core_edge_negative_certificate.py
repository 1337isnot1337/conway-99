"""Independent literal23-vertex certificates for twelve forbidden edge states.

No Schur builder, kernel source, optimizer, or eigensolver is imported.
The representative vector is obtained by a rational20-core inverse and an
explicit negative two-by-two direction. Every final check uses literal
27I-9A+J on the complete23-vertex induced graph.
"""
import argparse
from fractions import Fraction
import gzip
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOGS = ROOT/"experiments/logs/root-prism-free"
INPUTS = {
    "f0-boolean-fractional-model.json.gz": "703206929c9c85a40ac4ddcbfb1708c716c288482cf50c77a32249404e35b782",
    "f0-second-moments-preparation02.json.gz": "404d91da35c798ba248887c22a7500957947e24b71d5197dc44432460e6d219e",
    "f0-full-core-pair-minors01.json": "db03c1324658864cb18dcdd3d75885714696c9956d54fe5eea65394c950e7dc0",
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def read_inputs():
    result = []
    for name, expected in INPUTS.items():
        raw = (LOGS/name).read_bytes()
        assert sha(raw) == expected
        result.append(json.loads(gzip.decompress(raw) if name.endswith(".gz") else raw))
    return result


def inverse(matrix):
    n = len(matrix)
    work = [[Fraction(v) for v in row]+[Fraction(i == j) for j in range(n)]
            for i, row in enumerate(matrix)]
    for j in range(n):
        p = next(i for i in range(j, n) if work[i][j])
        work[j], work[p] = work[p], work[j]
        value = work[j][j]
        work[j] = [v/value for v in work[j]]
        for i in range(n):
            if i != j:
                value = work[i][j]
                work[i] = [a-value*b for a, b in zip(work[i], work[j])]
    assert all(work[i][j] == int(i == j) for i in range(n) for j in range(n))
    answer = [r[n:] for r in work]
    assert all(sum(matrix[i][k]*answer[k][j] for k in range(n)) == int(i == j)
               for i in range(n) for j in range(n))
    return answer


def adjacency23(core, first, second, edge):
    assert len(core) == 21 and len(first) == len(second) == 3 and edge in (0, 1)
    rows = list(core)+[0, 0]
    for new, signature in ((21, first), (22, second)):
        for i in signature:
            old = i+3
            rows[old] |= 1 << new
            rows[new] |= 1 << old
    if edge:
        rows[21] |= 1 << 22
        rows[22] |= 1 << 21
    assert all(not ((rows[i] >> i) & 1) for i in range(23))
    assert all(((rows[i] >> j) & 1) == ((rows[j] >> i) & 1) for i in range(23) for j in range(23))
    assert all((rows[i] & ((1 << 21)-1)) == core[i] for i in range(21))
    assert all(((rows[i] >> j) & 1) == 0 for i in range(3) for j in (21, 22))
    return rows


def projector(rows):
    n = len(rows)
    return [[27*int(i == j)-9*((rows[i] >> j) & 1)+1 for j in range(n)] for i in range(n)]


def quadratic(matrix, vector):
    return sum(vector[i]*matrix[i][j]*vector[j] for i in range(len(vector)) for j in range(len(vector)))


def representative_vector(rows):
    matrix = projector(rows)
    chosen = [0, 1]+list(range(3, 21))
    k = [[matrix[i][j] for j in chosen] for i in chosen]
    inv = inverse(k)
    u = [[matrix[i][j] for j in (21, 22)] for i in chosen]
    schur = [[Fraction(matrix[a+21][b+21])-
              sum(u[i][a]*inv[i][j]*u[j][b] for i in range(20) for j in range(20))
              for b in range(2)] for a in range(2)]
    scaled = [[v*60 for v in row] for row in schur]
    assert all(v.denominator == 1 for row in scaled for v in row)
    a, c, b = int(scaled[0][0]), int(scaled[0][1]), int(scaled[1][1])
    assert a > 0 and b > 0 and a*b-c*c == -33477
    # Fixed elementary formulas, with no numerical direction search.
    if a+b+2*c < 0:
        external = [1, 1]
    elif a+b-2*c < 0:
        external = [1, -1]
    else:
        external = [c, -a]
    assert quadratic(schur, external) < 0
    vector = [Fraction(0)]*23
    for i, site in enumerate(chosen):
        vector[site] = -sum(inv[i][j]*u[j][t]*external[t] for j in range(20) for t in range(2))
    vector[21], vector[22] = map(Fraction, external)
    assert quadratic(matrix, vector) == quadratic(schur, external)
    denominator = math.lcm(*(v.denominator for v in vector))
    integer = [int(v*denominator) for v in vector]
    divisor = math.gcd(*integer)
    integer = [v//divisor for v in integer]
    if next(v for v in integer if v) < 0:
        integer = [-v for v in integer]
    assert integer[2] == 0 and quadratic(matrix, integer) < 0
    return integer, {"chosen_positive_core": chosen,
                     "Schur_matrix": [[str(v) for v in row] for row in schur],
                     "Schur_scaled_by60": [[str(v) for v in row] for row in scaled],
                     "scaled_determinant": -33477, "external_direction": external,
                     "integer_clearing_denominator": str(denominator),
                     "positive_common_divisor": str(divisor),
                     "inverse_identity_checked": True}


def core_actions(core, triples, actions):
    supports = [frozenset(a for a, h in enumerate(triples) if i in h) for i in range(18)]
    lookup = {s: i for i, s in enumerate(supports)}
    assert len(lookup) == 18
    fibers = [frozenset(i for i in range(18) if (core[j] >> (i+3)) & 1) for j in range(3)]
    fiber_lookup = {s: i for i, s in enumerate(fibers)}
    assert len(fiber_lookup) == 3 and all(len(f) == 6 for f in fibers)
    answer = []
    for g in actions:
        assert sorted(g) == list(range(480))
        move = [lookup[frozenset(g[a] for a in support)] for support in supports]
        triangle = [fiber_lookup[frozenset(move[i] for i in fiber)] for fiber in fibers]
        whole = triangle+[i+3 for i in move]
        assert sorted(whole) == list(range(21))
        assert all(((core[i] >> j) & 1) == ((core[whole[i]] >> whole[j]) & 1)
                   for i in range(21) for j in range(21))
        assert all(sorted(move[i] for i in triples[a]) == triples[g[a]] for a in range(480))
        answer.append(whole)
    assert len({tuple(g) for g in answer}) == 12
    group = set(map(tuple, actions))
    assert len(group) == 12 and tuple(range(480)) in group
    assert all(tuple(g[h[a]] for a in range(480)) in group for g in actions for h in actions)
    return answer


def build():
    base, moments, minor = read_inputs()
    data = base["validation"]
    core, triples, edges = data["core"], data["triples"], data["edges"]
    assert len(triples) == 480 and len(edges) == 68394
    actions = moments["selector_actions"]
    maps = core_actions(core, triples, actions)
    rep = (0, 76)
    literal = adjacency23(core, triples[rep[0]], triples[rep[1]], 1)
    vector, construction = representative_vector(literal)
    value = quadratic(projector(literal), vector)
    edge_index = {tuple(e): i for i, e in enumerate(edges)}
    edge_to_orbit = {e: o for o, orbit in enumerate(data["edge_orbits"]) for e in orbit}
    records = []
    for g, core_move in zip(actions, maps):
        moved = (g[rep[0]], g[rep[1]])
        pair = tuple(sorted(moved))
        swap = moved != pair
        perm = core_move+([22, 21] if swap else [21, 22])
        candidate = [0]*23
        for i in range(23):
            candidate[perm[i]] = vector[i]
        graph = adjacency23(core, triples[pair[0]], triples[pair[1]], 1)
        assert all(((literal[i] >> j) & 1) == ((graph[perm[i]] >> perm[j]) & 1)
                   for i in range(23) for j in range(23))
        actual = quadratic(projector(graph), candidate)
        assert actual == value < 0
        nonedge = quadratic(projector(adjacency23(core, triples[pair[0]], triples[pair[1]], 0)), candidate)
        assert nonedge >= 0
        e = edge_index[pair]
        assert edge_to_orbit[e] == 3
        records.append({"pair": list(pair), "core_transport": core_move,
                        "outside_labels_swapped": swap, "adjacency_rows23": graph,
                        "integer_vector23": list(map(str, candidate)), "quadratic_value": str(actual),
                        "same_vector_nonedge_value": str(nonedge), "edge_index": e, "edge_orbit": 3})
    pairs = {tuple(r["pair"]) for r in records}
    assert len(pairs) == 12 and pairs == {tuple(r["pair"]) for r in minor["excluded_states"]}
    assert all(r["rejected_states"] == [1] and r["already_fixed_zero"] is False for r in minor["excluded_states"])
    assert {edge_index[p] for p in pairs} == set(data["edge_orbits"][3])
    return {"schema": "f0-full-core-edge-negative-literal-certificate-v1",
            "status": "PASS: twelve literal23-vertex integer negative certificates",
            "source_sha256": sha(Path(__file__).read_bytes()), "inputs": INPUTS,
            "representative_pair": list(rep), "representative_signatures": [triples[a] for a in rep],
            "representative_construction": construction, "records": records,
            "quadratic_value": str(value), "representative_squared_norm": str(sum(v*v for v in vector)),
            "maximum_absolute_vector_entry": max(map(abs, vector)),
            "all12_core_transports_checked": True, "literal_projector": "27I-9A+J",
            "forbidden_edge_orbit": 3, "quotient_Y_coordinate": 45,
            "nonedge_or_pair_selection_exclusion_claimed": False,
            "all_other_pairs_censused_here": False, "all23_adjacencies_specified": True,
            "model_sources_imported": 0, "optimizer_calls": 0, "eigendecompositions": 0,
            "scope": "These12 edge states are impossible. No component or full graph exclusion follows."}


def replay(path):
    saved = json.loads(path.read_bytes())
    actual = build()
    assert saved == actual
    # Check the saved certificate by the direct integer formula as well.
    for record in saved["records"]:
        a, v = record["adjacency_rows23"], list(map(int, record["integer_vector23"]))
        value = 27*sum(x*x for x in v)-18*sum(v[i]*v[j] for i in range(23) for j in range(i+1, 23)
                                                if (a[i] >> j) & 1)+sum(v)**2
        assert value == int(record["quadratic_value"]) < 0
    return {"status": "PASS: cold literal23-vertex certificates and all12 transports",
            "source_sha256": actual["source_sha256"], "certificate_sha256": sha(path.read_bytes()),
            "literal_vectors_checked": 12, "quadratic_value": actual["quadratic_value"],
            "optimizer_calls": 0, "eigendecompositions": 0, "all_other_pairs_censused_here": False}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("prepare", "replay"))
    parser.add_argument("--certificate", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    if args.mode == "prepare":
        result = build()
        assert not args.certificate.exists()
        args.certificate.write_text(json.dumps(result, indent=2)+"\n")
        report = {k: v for k, v in result.items() if k not in ("records", "representative_construction")}
        report["certificate_sha256"] = sha(args.certificate.read_bytes())
    else:
        report = replay(args.certificate)
    assert not args.report.exists()
    args.report.write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
