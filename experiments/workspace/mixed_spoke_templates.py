"""Generate four-mixed-edge two-full-axis templates modulo rooted sign changes."""
from itertools import combinations, permutations, product

AXES = range(5)
MIXED = {(i, j) for i in (0, 1) for j in (2, 3)}
PERMS = list(permutations(range(4)))
# Signed characters ordered by the full-axis bit, the other bit, and their product.
CHARS = [[(-1) ** ((a & mask).bit_count()) for a in range(4)] for mask in (1, 2, 3)]


def transport(p, i, j):
    return sum(CHARS[i][a] * CHARS[j][p[a]] for a in range(4)) // 4


def sign_arrays():
    rows = []
    for i in AXES:
        aligned = [j for j in AXES if i != j and (i, j) not in MIXED]
        choices = []
        for positive in combinations(aligned, len(aligned) // 2):
            choices.append(tuple(1 if j in positive else -int(j in aligned) for j in AXES))
        rows.append(choices)
    yield from (p for p in product(*rows) if all(sum(col) == 0 for col in zip(*p)))


def canonical(p):
    candidates = []
    for perm in permutations(AXES):
        for transpose in (False, True):
            def image(i, j):
                return (perm[j], perm[i]) if transpose else (perm[i], perm[j])
            if {image(i, j) for i, j in MIXED} != MIXED:
                continue
            for sign in (-1, 1):
                candidates.append(tuple(sign * p[a][b] for i, j in product(AXES, repeat=2)
                                        for a, b in [image(i, j)]))
    return min(candidates)


def main():
    arrays = list(sign_arrays())
    patterns = sorted({canonical(p) for p in arrays})
    assert len(arrays) == 38 and len(patterns) == 5
    for pattern in patterns:
        for types in product((1, 2), repeat=4):
            domains = []
            for i, j in product(AXES, repeat=2):
                if i == j:
                    domains.append(0)
                    continue
                if (i, j) in MIXED:
                    # The leaf-bit switches at the two row and two column indices
                    # normalize the first orientation independently.
                    allowed = [k for k, p in enumerate(PERMS)
                               if transport(p, types[i], 0) == (1 if j == 2 else -1)
                               and transport(p, 0, types[j]) == (1 if i == 0 else -1)]
                    assert len(allowed) == 1
                else:
                    allowed = [k for k, p in enumerate(PERMS)
                               if transport(p, 0, 0) == pattern[5*i+j]]
                    assert len(allowed) == 4
                domains.append(sum(1 << k for k in allowed))
            print(*domains)


if __name__ == '__main__':
    main()
