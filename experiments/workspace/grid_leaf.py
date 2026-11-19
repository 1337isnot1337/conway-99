"""Check the eight-point necessary conditions for a fifteen-grid root."""
from collections import Counter
from itertools import combinations, permutations, product

PAIRS = list(combinations(range(8), 2))


def hub(v):
    return (v % 4) // 2


def matchings(vertices):
    if not vertices:
        yield ()
        return
    first, *others = vertices
    for i, second in enumerate(others):
        for rest in matchings(others[:i] + others[i + 1:]):
            yield ((first, second),) + rest


def leaf_graphs():
    local = list(matchings(range(4)))
    for left, right, across in product(local, local, permutations(range(4))):
        neighbors = [set() for _ in range(8)]
        edges = list(left) + [(a + 4, b + 4) for a, b in right]
        edges += [(a, b + 4) for a, b in enumerate(across)]
        for a, b in edges:
            neighbors[a].add(b)
            neighbors[b].add(a)
        if any(sum(hub(a) == hub(b) == h for a, b in edges) > 2 for h in (0, 1)):
            continue
        if any(sum(y % 4 == signed for y in neighbors[x]) > 1
               for x in range(8) for signed in (x % 4, (x % 4) ^ 1)):
            continue
        if min(residual(neighbors)) >= 0:
            yield neighbors


def residual(neighbors):
    return [2 - (b in neighbors[a]) - len(set(neighbors[a]) & set(neighbors[b]))
            - (a // 4 == b // 4) - (a % 4 == b % 4) for a, b in PAIRS]


def canonical(neighbors):
    results = []
    for swap, flip_u, flip_v, flip_leaf in product(range(2), repeat=4):
        perm = [(v // 4 ^ flip_leaf) * 4 + (hub(v) ^ swap) * 2
                + (v % 2 ^ (flip_v if hub(v) else flip_u)) for v in range(8)]
        result = [()] * 8
        for v in range(8):
            result[perm[v]] = tuple(sorted(perm[w] for w in neighbors[v]))
        results.append(tuple(result))
    return min(results)


def can_factor(neighbors):
    counts = residual(neighbors)
    all_matchings = list(matchings(range(8)))
    indices = [[PAIRS.index(e) for e in matching] for matching in all_matchings]

    def extend(depth, start):
        if depth == 6:
            return not any(counts)
        for i in range(start, len(indices)):
            if depth == 0 and any(hub(a) == hub(b) for a, b in all_matchings[i]):
                continue
            selected = indices[i]
            if all(counts[j] for j in selected):
                for j in selected:
                    counts[j] -= 1
                if extend(depth + 1, 0 if depth == 0 else i):
                    return True
                for j in selected:
                    counts[j] += 1
        return False

    return extend(0, 0)


def main():
    classes = Counter(canonical(graph) for graph in leaf_graphs())
    factored = sum(can_factor(graph) for graph in classes)
    assert (sum(classes.values()), len(classes), factored) == (114, 23, 23)
    print("Eight-point graphs: 114 labeled, 23 orbits, all 23 admit six matchings.")


if __name__ == "__main__":
    main()
