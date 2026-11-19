"""Small arithmetic/source-binding record for the independent source review.

This does not import the subject sources or rebuild/contract their tensors.
The source-review statements below record a complete manual read.
"""
import argparse
import hashlib
import json
from pathlib import Path


BINDINGS = {
    "triangle_vertex_projector_moments.py": "fea5b560e4aeeb323da6e8cde2bc52571a3dc7499f0900a0a12b1f134d4a31c7",
    "triangle_vertex_projector_query.py": "c2529d20935733c835a24b2600dd195c439f68f2cf258c9eb48325ff466516d3",
    "triangle_projector_conditioned_query.py": "cd167c52b7b646a64e4faf58816212d427d1c280a45070e77a5eb8b0a29abb43",
    "triangle_incidence_projector_moments.py": "1e7a8b7380314d6dfd8ff05954a13662bc011378f5759ad675ec1bc281fa19e9",
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    here = Path(__file__).resolve().parent
    for name, expected in BINDINGS.items():
        assert hashlib.sha256((here / name).read_bytes()).hexdigest() == expected
    cases = []
    # overlap, directed adjacency sum between the two triangle indicators,
    # old triangle projector entry, new minus/plus entries.
    table = [(3, 6, 120, 4, 180), (1, 4, -20, 0, 70)]
    table += [(0, e, 7 * e - 6, 1 - e, 11 * e - 18) for e in range(4)]
    for overlap, edges, old, minus, plus in table:
        assert 27 * overlap - 9 * edges + 9 == 9 * minus
        assert 44 * overlap + 11 * edges - 18 == plus
        assert 11 * old + 110 * minus + 3 * plus + 10 == 2310 * (overlap == 3)
        cases.append(dict(overlap=overlap, directed_cross_edges=edges,
                          old=old, minus=minus, plus=plus))
    spectra = []
    for eigenvalue, multiplicity in [(14, 1), (3, 54), (-4, 44)]:
        j = 99 if eigenvalue == 14 else 0
        qm = 27 - 9 * eigenvalue + j
        qp = 44 + 11 * eigenvalue - 2 * j
        assert qm >= 0 and qp >= 0
        assert qm * (eigenvalue + 7) % 9 == 0
        spectra.append(dict(adjacency_eigenvalue=eigenvalue,
                            multiplicity=multiplicity,
                            minus_triangle_eigenvalue=qm * (eigenvalue + 7) // 9,
                            plus_triangle_eigenvalue=qp * (eigenvalue + 7)))
    report = {
        "status": "PASS: independent complete source and mathematical review",
        "reviewer_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "bindings": BINDINGS,
        "small_independent_kernel_arithmetic": cases,
        "small_independent_spectral_arithmetic": spectra,
        "reviewed": [
            "B B^T=A+7I and the two vertex-projector factorizations imply the advertised positive semidefinite triangle kernels.",
            "A shared triangle vertex gives exactly four directed cross-edge contributions; lambda=1 excludes further cross edges.",
            "The constructor enumerates each induced support as root union two triangles, every labelled root map, and every unordered triangle pair.",
            "Distinct triangles in one class contribute twice to its diagonal; two different classes contribute once to the stored lower-triangular entry. Equal triangles contribute once.",
            "Coefficients multiply unlabelled induced counts; no additional automorphism factor is required after counting every labelled root map in the representative.",
            "For each individual root embedding, conditioning on its internal triangle gives d M-diag(q) f f^T diag(q), with d=4 or180. Summation preserves positivity; global first moments are not multiplied together.",
            "The exact characteristic polynomial test is valid for a real symmetric matrix: nonnegative coefficients of det(tI+M) exclude a positive root and hence a negative eigenvalue.",
            "Negative-vector forms double off-diagonal lower entries and divide by a positive coefficient gcd. The reported primitive value is divided by the same gcd.",
            "The query and replay bind all22 blocks/574classes and mark incomplete/error paths without claiming full coverage or graph existence."
        ],
        "scope": {
            "complete_subject_source_read": True,
            "subject_imported": False,
            "tensor_rebuilt": False,
            "count_point_loaded": False,
            "matrix_contracted": False,
            "optimizer_or_query_called": False,
            "runtime_authorization_implied": False
        }
    }
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"status": report["status"], "report_sha256": hashlib.sha256(args.output.read_bytes()).hexdigest()}))


if __name__ == "__main__":
    main()
