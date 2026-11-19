#!/usr/bin/env python3
"""Independent small-domain/product audit of the frozen r6,s2 builder.

This uses only the small graph catalogue.  Its product oracle merges all
positive and negative adjacency prescriptions on a literal union of the
two flags, then enumerates unspecified edges directly.  It uses neither
the builder's child DAG nor its overlap enumeration or transport code.
No LP, SAT, dense reduction, or full moment-family build is performed.
"""

from __future__ import annotations

import argparse
from collections import Counter
from functools import lru_cache
from hashlib import sha256
from itertools import combinations, permutations, product
import json
from pathlib import Path
import pickle
import time

import pynauty

import grid_free_order10_r6s2 as subject


ROOT = Path(__file__).resolve().parents[2]
SUBJECT_SHA = "3772c728ec764dbec0142865696bb747c06e47b29495964af867103618b75a6d"
PREPARATION = ROOT / "experiments/logs/moments-and-counts/prism-zero-order10-r6s2-preparation.json"
PREPARATION_SHA = "1ff172888ebdd1a139710cb25e0a0f29c8044a1d81ba4972c0085f9827d691ea"
OUTPUT = ROOT / "experiments/logs/moments-and-counts/prism-zero-order10-r6s2-independent-audit.json"


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def members(mask):
    return [j for j in range(mask.bit_length()) if mask >> j & 1]


def graph(n, edges):
    rows = [0] * n
    for a, b in edges:
        rows[a] |= 1 << b
        rows[b] |= 1 << a
    return tuple(rows)


def induced(rows, vertices):
    return tuple(sum(((rows[a] >> b) & 1) << j for j, b in enumerate(vertices)) for a in vertices)


@lru_cache(maxsize=200000)
def canonical(rows):
    g = pynauty.Graph(len(rows), directed=False,
                      adjacency_dict={i: members(row) for i, row in enumerate(rows)})
    return len(rows), pynauty.certificate(g)


def valid(rows):
    for a, b in combinations(range(len(rows)), 2):
        if (rows[a] & rows[b]).bit_count() > 2 - ((rows[a] >> b) & 1):
            return False
    return True


def add_free(root, masks, mutual):
    r = len(root)
    edges = [(a, b) for a, b in combinations(range(r), 2) if root[a] >> b & 1]
    for i, mask in enumerate(masks):
        edges.extend((r + i, j) for j in members(mask))
    if len(masks) == 2 and mutual:
        edges.append((r, r + 1))
    return graph(r + len(masks), edges)


def direct_domain(root):
    r = len(root)
    keys = {(0, (), 0)}
    for mask in range(1 << r):
        if mask.bit_count() >= 3 and valid(add_free(root, (mask,), 0)):
            keys.add((1, (mask,), 0))
    equal_masks_admitted = 0
    ordered_valid_pairs = 0
    for a, b, edge in product(range(1 << r), range(1 << r), range(2)):
        if a.bit_count() + edge < 3 or b.bit_count() + edge < 3:
            continue
        if not valid(add_free(root, (a, b), edge)):
            continue
        ordered_valid_pairs += 1
        equal_masks_admitted += a == b
        keys.add((2, tuple(sorted((a, b))), edge))
    assert equal_masks_admitted == 0
    assert ordered_valid_pairs == 2 * sum(key[0] == 2 for key in keys)
    return keys, ordered_valid_pairs


def injections(s, t):
    # -1 is a fresh right vertex; all other right images are distinct
    # left-free indices.  This independent cartesian enumeration gives
    # 1,4,2 maps in the three overlap classes when s=t=2.
    for values in product(range(-1, s), repeat=t):
        shared = [value for value in values if value >= 0]
        if len(set(shared)) == len(shared):
            yield values


def direct_product(root_size, left, right, ids):
    s, t = len(left) - root_size, len(right) - root_size
    answer, overlap_counts = Counter(), Counter()
    for mapping in injections(s, t):
        fresh = root_size + s
        right_image = list(range(root_size))
        for value in mapping:
            if value == -1:
                right_image.append(fresh)
                fresh += 1
            else:
                right_image.append(root_size + value)
        prescribed = {}
        consistent = True
        for rows, image in ((left, list(range(len(left)))), (right, right_image)):
            for a, b in combinations(range(len(rows)), 2):
                pair = tuple(sorted((image[a], image[b])))
                assert pair[0] != pair[1]
                value = (rows[a] >> b) & 1
                if pair in prescribed and prescribed[pair] != value:
                    consistent = False
                    break
                prescribed[pair] = value
            if not consistent:
                break
        if not consistent:
            continue
        unknown = [pair for pair in combinations(range(fresh), 2) if pair not in prescribed]
        q = sum(value >= 0 for value in mapping)
        assert len(unknown) == (s - q) * (t - q)
        present = [edge for edge, value in prescribed.items() if value]
        for mask in range(1 << len(unknown)):
            edges = present + [edge for i, edge in enumerate(unknown) if mask >> i & 1]
            rows = graph(fresh, edges)
            if valid(rows):
                answer[ids[canonical(rows)]] += 1
                overlap_counts[q] += 1
    return answer, overlap_counts


def samples(flags):
    selected = {0}
    groups = [[], [], [], []]
    for i, flag in enumerate(flags):
        if flag["size"] == 1:
            groups[0].append(i)
        elif flag["size"] == 2:
            if flag["edge"] == 0:
                groups[1].append(i)
            elif min(mask.bit_count() for mask in flag["masks"]) == 2:
                groups[2].append(i)
            else:
                groups[3].append(i)
    for group in groups:
        if group:
            selected.update((group[0], group[-1]))
    assert len(selected) <= 9
    return sorted(selected)


def nonbinary_rook_control(data, builder, ids, preparation):
    rows = graph(9, [(a, b) for a, b in combinations(range(9), 2)
                     if a // 3 == b // 3 or a % 3 == b % 3])
    root = preparation["direct_rook_controls"]["cases"][0]["root_type"]
    root_rows = data[0][root]
    assert len(root_rows) == 3 and not any(root_rows)
    flags = builder.flags(root)
    counts = Counter()
    for size in range(10):
        for subset in combinations(range(9), size):
            counts[ids[canonical(induced(rows, subset))]] += 1
    embeddings = {i: count * data[2][i] for i, count in counts.items()}
    matrix = [[0] * len(flags) for _ in flags]
    seen, maximum = 0, 0
    for image in permutations(range(9), 3):
        if any(rows[image[a]] >> image[b] & 1 for a, b in combinations(range(3), 2)):
            continue
        free = [v for v in range(9) if v not in image]
        values = []
        for flag in flags:
            value = 0
            for extension in permutations(free, flag["size"]):
                vertices = image + extension
                if induced(rows, vertices) == flag["rows"]:
                    value += 1
            values.append(value)
        seen += 1
        maximum = max(maximum, max(values))
        for i in range(len(flags)):
            for j in range(len(flags)):
                matrix[i][j] += values[i] * values[j]
    assert seen == 36 and maximum == 2 and len(flags) == 5
    for i, left in enumerate(flags):
        for j, right in enumerate(flags):
            terms, _ = direct_product(3, left["rows"], right["rows"], ids)
            value = sum(coefficient * embeddings.get(index, 0) for index, coefficient in terms.items())
            assert value == matrix[i][j]
    examples = [{"flag": i, "masks": list(flags[i]["masks"]), "edge": flags[i]["edge"],
                 "first_moment": matrix[0][i], "second_moment": matrix[i][i]}
                for i in range(len(flags)) if matrix[i][i] > matrix[0][i]]
    assert examples and all(x["first_moment"] == 72 and x["second_moment"] == 144 for x in examples)
    return {"root_embeddings": seen, "flags": len(flags), "maximum_flag_value": maximum,
            "matrix": matrix, "nonbinary_examples": examples,
            "direct_labelled_embedding_outer_product_matches": True}


def audit():
    assert digest(Path(subject.__file__)) == SUBJECT_SHA
    assert digest(PREPARATION) == PREPARATION_SHA
    saved = json.loads(PREPARATION.read_text())
    assert saved["source_sha256"] == SUBJECT_SHA
    catalogue = Path(saved["catalogue_path"])
    assert digest(catalogue) == saved["catalogue_sha256"]
    with catalogue.open("rb") as stream:
        data = pickle.load(stream)
    ids = {canonical(tuple(rows)): i for i, rows in enumerate(data[0])}
    assert len(ids) == len(data[0]) == 48965
    builder = subject.Builder(data)
    roots = list(data[1][6])
    assert len(roots) == 62
    overlap = {f"{s},{t}": [sum(sum(v >= 0 for v in values) == q for values in injections(s, t))
                             for q in range(min(s, t) + 1)]
               for s in range(3) for t in range(3)}
    assert overlap == saved["overlap_injection_counts"] and overlap["2,2"] == [1, 4, 2]
    records, tested, order_ten_products = [], 0, 0
    for root in roots:
        flags = builder.flags(root)
        domain, ordered_pairs = direct_domain(data[0][root])
        original = {(f["size"], tuple(f["masks"]), f["edge"]) for f in flags}
        assert domain == original and len(domain) == len(flags)
        chosen = samples(flags)
        combinations_checked = 0
        for left_index in chosen:
            for right_index in chosen:
                if right_index > left_index:
                    continue
                left, right = flags[left_index], flags[right_index]
                expected, by_overlap = direct_product(6, left["rows"], right["rows"], ids)
                actual, actual_overlap = builder.product_form(root, left, right, True)
                assert actual == expected and actual_overlap == by_overlap
                assert builder.product_form(root, right, left) == expected
                order_ten_products += any(len(data[0][i]) == 10 for i in expected)
                tested += 1
                combinations_checked += 1
        records.append({"root": root, "full_domain_flags": len(flags),
                        "ordered_valid_two_free_patterns": ordered_pairs,
                        "sampled_flag_indices": chosen,
                        "unordered_products_checked_in_both_orders": combinations_checked})
        if len(records) % 16 == 0:
            print(json.dumps({"root_domains_checked": len(records), "products_checked": tested}), flush=True)
    assert order_ten_products > 0
    rook = nonbinary_rook_control(data, builder, ids, saved)
    return {"status": "independent r6s2 domain, product and free-label audit PASS",
            "source_sha256": digest(Path(__file__)), "subject_sha256": SUBJECT_SHA,
            "preparation_sha256": PREPARATION_SHA, "catalogue_sha256": saved["catalogue_sha256"],
            "overlap_counts": overlap, "root_domains_checked": 62,
            "all_equal_mask_two_free_patterns_rejected": True,
            "free_label_pair_quotient_multiplicity": 2,
            "product_oracle": "merge every edge and nonedge prescription; enumerate all unspecified pairs directly",
            "products_checked_in_both_orders": tested,
            "products_with_nonzero_order_ten_terms": order_ten_products,
            "root_records": records, "independent_nonbinary_rook_control": rook,
            "full_root_domains": 62, "fixed_size_subfamily_blocks": 55,
            "oversize_domains_not_claimed_scanned": 7,
            "no_binary_diagonal_shortcut_valid_for_full_domain": True,
            "dense_reduction_loaded": False, "optimizer_called": False,
            "full_moment_family_built": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    started = time.monotonic()
    result = audit()
    if args.write:
        OUTPUT.write_text(json.dumps(result, indent=2) + "\n")
    else:
        assert json.loads(OUTPUT.read_text()) == result
    print(json.dumps({key: value for key, value in result.items()
                      if key not in ("root_records", "independent_nonbinary_rook_control")}, indent=2), flush=True)
    print(json.dumps({"seconds": time.monotonic() - started}), flush=True)


if __name__ == "__main__":
    main()
