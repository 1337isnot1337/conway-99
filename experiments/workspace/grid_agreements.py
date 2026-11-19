"""Check the three four-point maps in the tetrahedral defect argument."""
from itertools import combinations, combinations_with_replacement, product

pairs = list(combinations(range(4), 2))


def partitions():
    # Canonical fiber labels in order of first occurrence.
    for labels in product(range(4), repeat=4):
        if all(a <= 1 + max(labels[:i], default=-1) for i, a in enumerate(labels)):
            yield labels


def main():
    profiles = list(partitions())
    assert len(profiles) == 15
    checked = 0
    for maps in combinations_with_replacement(profiles, 3):
        if any(max(row.count(a) for a in row) == 4 for row in maps):
            continue
        if not all(sum(row[i] == row[j] for row in maps) == 1 for i, j in pairs):
            continue
        checked += 1
        assert all(row.count(a) <= 2 for row in maps for a in row)
    assert checked > 0
    print(f"Four-point maps: {checked} compatible unordered partition triples, no triple fiber.")


if __name__ == "__main__":
    main()
