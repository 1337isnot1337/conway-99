"""Point-independent scope of intersecting-triangle Schur blocks.

All catalogue roots of orders five and six containing a triangle are
retained. Every triangle class meeting its root is enumerated. This file
does not build pair-product tensors or load a count point.
"""
import argparse
from collections import Counter
from itertools import combinations, combinations_with_replacement, permutations
import json
from math import comb, factorial
from pathlib import Path
import time

from flint import fmpz_mat
import triangle_incidence_projector_moments as base

BASE_SHA = "1e7a8b7380314d6dfd8ff05954a13662bc011378f5759ad675ec1bc281fa19e9"


def extension(root, inside, masks):
    r = len(root)
    vertices = [i for i in range(r) if inside & (1 << i)]
    assert len(vertices) + len(masks) == 3
    if not all((root[a] >> b) & 1 for a, b in combinations(vertices, 2)):
        return None
    if not all(mask & inside == inside for mask in masks):
        return None
    rows = list(root) + [0] * len(masks)
    for j, mask in enumerate(masks, r):
        rows[j] = mask
        for i in range(r):
            if mask & (1 << i):
                rows[i] |= 1 << j
    for a, b in combinations(range(r, len(rows)), 2):
        rows[a] |= 1 << b
        rows[b] |= 1 << a
    return tuple(rows)


def determinant(matrix):
    return 1 if not matrix else int(fmpz_mat(matrix).det())


def adjugate(matrix):
    n = len(matrix)
    return [[(-1 if (i+j) % 2 else 1) *
             determinant([[matrix[a][b] for b in range(n) if b != i]
                          for a in range(n) if a != j])
             for j in range(n)] for i in range(n)]


def completion_bound(a, b):
    # Every partial injection is included. Only edges between the two
    # exclusive free sets remain unspecified. Mask consistency and caps
    # may remove choices, so this is a conservative enumeration bound.
    return sum(comb(a, q) * comb(b, q) * factorial(q) * (1 << ((a-q)*(b-q)))
               for q in range(min(a, b)+1))


def literal_automorphisms(rows):
    return [p for p in permutations(range(len(rows)))
            if all(((rows[a] >> b) & 1) == ((rows[p[a]] >> p[b]) & 1)
                   for a, b in combinations(range(len(rows)), 2))]


def root_scope(root_id, root, aut, deadline):
    r = len(root)
    core_triangles = base.triangles(root)
    assert core_triangles
    core_gram = [[base.kernel(root, a, b) for b in core_triangles]
                 for a in core_triangles]
    det = determinant(core_gram)
    principal = [determinant([row[:j] for row in core_gram[:j]])
                 for j in range(1, len(core_gram)+1)]
    assert all(d > 0 for d in principal)
    adj = adjugate(core_gram)
    k = len(core_triangles)
    assert all(sum(core_gram[i][a] * adj[a][j] for a in range(k)) ==
               (det if i == j else 0) for i in range(k) for j in range(k))
    automorphisms = literal_automorphisms(root)
    assert len(automorphisms) == int(aut)
    classes = []
    rejected = Counter()
    attempted = 0
    for size in (1, 2, 3):
        for sites in combinations(range(r), size):
            inside = sum(1 << v for v in sites)
            eligible = [m for m in range(1 << r) if m & inside == inside]
            for masks in combinations_with_replacement(eligible, 3-size):
                attempted += 1
                if attempted % 512 == 0:
                    base.check_time(deadline)
                rows = extension(root, inside, masks)
                if rows is None:
                    rejected["prescribed_triangle_missing"] += 1
                    continue
                if not base.cap_valid(rows):
                    rejected["visible_common_neighbor_cap"] += 1
                    continue
                triangle = tuple(sites) + tuple(range(r, len(rows)))
                assert triangle in base.triangles(rows)
                q = [base.kernel(rows, t, triangle) for t in core_triangles]
                classes.append({"root_intersection_mask": inside,
                                "outside_masks": list(masks),
                                "literal_rows": list(rows),
                                "core_triangle_cross_values": q})
    keys = [(c["root_intersection_mask"], tuple(c["outside_masks"])) for c in classes]
    assert len(set(keys)) == len(keys)
    assert len(classes) + sum(rejected.values()) == attempted
    core_classes = [keys.index((sum(1 << v for v in t), ())) for t in core_triangles]
    # All core-triangle rows of the Schur kernel vanish by adjugate identity.
    checked = 0
    for i, position in enumerate(core_classes):
        assert classes[position]["core_triangle_cross_values"] == [core_gram[a][i] for a in range(k)]
        for c in classes:
            q = c["core_triangle_cross_values"]
            assert det*q[i] == sum(core_gram[i][a]*adj[a][b]*q[b]
                                  for a in range(k) for b in range(k))
            checked += 1
    profile = Counter(len(c["outside_masks"]) for c in classes)
    pair_profile = Counter()
    for a in range(3):
        for b in range(a, 3):
            pairs = profile[a] * profile[b] if a != b else profile[a]*(profile[a]+1)//2
            pair_profile[str(a)+","+str(b)] = pairs
    lower = len(classes)*(len(classes)+1)//2
    assert sum(pair_profile.values()) == lower
    raw_bound = sum(count*completion_bound(*map(int, key.split(",")))
                    for key, count in pair_profile.items())
    noncore_profile = Counter(profile)
    noncore_profile[0] = 0
    noncore_bound = sum((noncore_profile[a]*noncore_profile[b] if a != b else
                         noncore_profile[a]*(noncore_profile[a]+1)//2) * completion_bound(a, b)
                        for a in range(3) for b in range(a, 3))
    kernel_generators = [[int(j == index) for j in range(len(classes))]
                         for index in core_classes]
    kernel_generators += [[int(c["root_intersection_mask"] & (1 << v) != 0)
                           for c in classes] for v in range(r)]
    known_kernel_rank = int(fmpz_mat(kernel_generators).rank())
    return {"root_type": root_id, "root_order": r, "root_rows": list(root),
            "root_automorphisms": len(automorphisms),
            "core_triangles": [list(t) for t in core_triangles],
            "core_triangle_gram": core_gram, "leading_principal_determinants": principal,
            "core_triangle_gram_determinant": det, "core_triangle_gram_adjugate": adj,
            "classes": classes, "class_count": len(classes), "lower_entries": lower,
            "outside_vertex_profile": dict(sorted(profile.items())),
            "core_triangle_class_indices": core_classes,
            "core_triangle_zero_row_identities": checked,
            "known_core_and_root_star_kernel_rank": known_kernel_rank,
            "quotient_order_after_known_kernels": len(classes)-known_kernel_rank,
            "raw_class_candidates": attempted, "rejected_candidates": dict(sorted(rejected.items())),
            "class_pair_profile": dict(sorted(pair_profile.items())),
            "partial_injection_and_free_edge_candidate_bound": raw_bound,
            "bound_after_omitting_proved_core_zero_rows": noncore_bound,
            "largest_single_flag_order": r+max(profile),
            "largest_pair_union_order": r+2*max(profile)}


def run(args):
    assert 0 < args.seconds <= 60 and not args.output.exists()
    start = time.monotonic()
    deadline = start + args.seconds
    assert base.digest(Path(base.__file__).read_bytes()) == BASE_SHA
    graphs, levels, aut, _ = base.load_catalogue(args.catalogue)
    result = {"schema": "conway99.intersecting-triangle-root-scope.v1",
              "status": "INCOMPLETE", "source_sha256": base.digest(Path(__file__).read_bytes()),
              "base_source_sha256": BASE_SHA, "catalogue_sha256": base.CATALOGUE_SHA,
              "roots": [], "complete_five_and_six_root_coverage": False,
              "count_point_loaded": False, "pair_tensors_generated": False,
              "optimizer_called": False}
    try:
        missing_triangles = Counter()
        for order in (5, 6):
            for root_id in levels[order]:
                base.check_time(deadline)
                root = graphs[root_id]
                if not base.triangles(root):
                    missing_triangles[order] += 1
                    continue
                result["roots"].append(root_scope(root_id, root, aut[root_id], deadline))
        summaries = []
        for order in (5, 6):
            selected = [d for d in result["roots"] if d["root_order"] == order]
            summaries.append({"root_order": order, "all_catalogue_types": len(levels[order]),
                              "triangle_free_root_types": missing_triangles[order],
                              "retained_roots": len(selected),
                              "core_triangle_count_census": dict(sorted(Counter(len(d["core_triangles"]) for d in selected).items())),
                              "classes": sum(d["class_count"] for d in selected),
                              "largest_block": max(d["class_count"] for d in selected),
                              "lower_entries": sum(d["lower_entries"] for d in selected),
                              "quotient_lower_entries": sum((d["quotient_order_after_known_kernels"]*(d["quotient_order_after_known_kernels"]+1))//2 for d in selected),
                              "core_zero_row_identities": sum(d["core_triangle_zero_row_identities"] for d in selected),
                              "partial_injection_and_free_edge_candidate_bound": sum(d["partial_injection_and_free_edge_candidate_bound"] for d in selected),
                              "bound_after_omitting_proved_core_zero_rows": sum(d["bound_after_omitting_proved_core_zero_rows"] for d in selected)})
        result.update(status="COMPLETE_POINT_INDEPENDENT_INTERSECTING_TRIANGLE_SCOPE",
                      complete_five_and_six_root_coverage=True, summaries=summaries,
                      all_triangle_classes_meeting_root_retained=True,
                      single_class_free_label_stabilizer="product of factorials of outside-mask multiplicities",
                      conditioned_kernel="det(C) Q(U,V) - q_U^T adj(C) q_V, C=Q on all core triangles",
                      candidate_bound_table={str(a)+","+str(b): completion_bound(a,b)
                                             for a in range(3) for b in range(a,3)},
                      no_point_dependent_pruning=True)
        base.check_time(deadline)
    except Exception as error:
        result.update(status="INCOMPLETE_NO_FULL_SCOPE_CLAIM",
                      error_type=type(error).__name__, error_message=str(error))
        raise
    finally:
        result["seconds"] = time.monotonic()-start
        args.output.write_text(json.dumps(result, indent=2)+"\n")
        print(json.dumps({k: v for k,v in result.items() if k != "roots"}, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalogue", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seconds", type=float, default=60)
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
