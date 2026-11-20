"""Exact row modules over Z/4 using binary low and high coefficient planes.

A row is (edge_vector, original_row_multipliers, selector_rhs). All three
vectors are carried through the same unit row operations. No division by
two occurs in a proof vector or right-hand side.
"""
from itertools import product
import time

ZERO = (0, 0)


def add(first, second):
    a0, a1 = first
    b0, b1 = second
    return a0 ^ b0, a1 ^ b1 ^ (a0 & b0)


def negative(value):
    return value[0], value[1] ^ value[0]


def scale(value, coefficient):
    assert type(coefficient) is int
    coefficient %= 4
    if coefficient == 0:
        return ZERO
    if coefficient == 1:
        return value
    if coefficient == 2:
        return 0, value[0]
    return negative(value)


def subtract(first, second, coefficient=1):
    return add(first, scale(second, -coefficient))


def coefficient(value, column):
    return (value[0] >> column & 1) + 2 * (value[1] >> column & 1)


def encode(items):
    combined = {}
    for column, value in items:
        assert type(column) is int and column >= 0 and type(value) is int
        combined[column] = (combined.get(column, 0) + value) % 4
    return (sum(1 << j for j, c in combined.items() if c & 1),
            sum(1 << j for j, c in combined.items() if c & 2))


def terms(value):
    union = value[0] | value[1]
    result = []
    while union:
        bit = union & -union
        column = bit.bit_length() - 1
        result.append([column, coefficient(value, column)])
        union ^= bit
    return result


def row_scale(row, value):
    return tuple(scale(part, value) for part in row)


def row_subtract(first, second, value=1):
    return tuple(subtract(a, b, value) for a, b in zip(first, second))


def decompose(rows, check=lambda: None):
    """Return a spanning unit/even row basis and complete left-kernel generators.

The returned zero residuals plus twice every surviving even row generate
the full left kernel, since the even pivots are independent over F2.
"""
    units, deferred = {}, []
    operations = 0
    for original in rows:
        check()
        row = original
        while row[0][0]:
            if operations % 1024 == 0:
                check()
            pivot = (row[0][0] & -row[0][0]).bit_length() - 1
            c = coefficient(row[0], pivot)
            assert c in (1, 3)
            if pivot not in units:
                units[pivot] = row_scale(row, c)  # 1 and 3 are their own inverses.
                break
            row = row_subtract(row, units[pivot], c)
            operations += 1
        if row[0][0] == 0:
            deferred.append(row)
    unit_mask = sum(1 << p for p in units)
    even, zero = {}, []
    cleanup = even_operations = 0
    for original in deferred:
        check()
        vector, proof, rhs = original
        assert vector[0] == 0
        while vector[1] & unit_mask:
            if cleanup % 1024 == 0:
                check()
            occupied = vector[1] & unit_mask
            pivot = (occupied & -occupied).bit_length() - 1
            old_vector, old_proof, old_rhs = units[pivot]
            # Subtracting twice a vector affects only its low plane.
            vector = (0, vector[1] ^ old_vector[0])
            proof = (proof[0], proof[1] ^ old_proof[0])
            rhs = (rhs[0], rhs[1] ^ old_rhs[0])
            cleanup += 1
        row = vector, proof, rhs
        assert not row[0][0] and not (row[0][1] & unit_mask)
        while row[0][1]:
            if even_operations % 1024 == 0:
                check()
            pivot = (row[0][1] & -row[0][1]).bit_length() - 1
            if pivot not in even:
                even[pivot] = row
                break
            row = row_subtract(row, even[pivot])
            even_operations += 1
        if row[0] == ZERO:
            zero.append(row)
    generators = [("zero_residual", row) for row in zero]
    generators += [("doubled_even", row_scale(even[pivot], 2)) for pivot in sorted(even)]
    assert all(row[0] == ZERO for _, row in generators)
    assert len(generators) == len(rows) - len(units)
    return {"units": units, "even": even, "zero": zero, "generators": generators,
            "unit_mask": unit_mask, "rows": len(rows), "unit_operations": operations,
            "unit_cleanup_operations": cleanup, "even_operations": even_operations}


def reduce_vector(value, decomposition):
    """Return remainder and original-row coefficients whose combination was removed."""
    witness = ZERO
    units, even = decomposition["units"], decomposition["even"]
    for pivot in sorted(units):
        c = coefficient(value, pivot)
        if c & 1:
            row = units[pivot]
            value = subtract(value, row[0], c)
            witness = add(witness, scale(row[1], c))
    assert not (value[0] & decomposition["unit_mask"])
    while value[1] & decomposition["unit_mask"]:
        occupied = value[1] & decomposition["unit_mask"]
        pivot = (occupied & -occupied).bit_length() - 1
        row = units[pivot]
        value = value[0], value[1] ^ row[0][0]
        witness = witness[0], witness[1] ^ row[1][0]
    for pivot in sorted(even):
        if value[1] >> pivot & 1:
            row = even[pivot]
            value = subtract(value, row[0])
            witness = add(witness, row[1])
    return value, witness


def controls():
    started = time.monotonic()
    vectors = list(product(range(4), repeat=3))
    arithmetic = 0
    for first in vectors:
        a = encode(enumerate(first))
        for second in vectors:
            b = encode(enumerate(second))
            assert terms(add(a, b)) == [[i, (x + y) % 4] for i, (x, y) in enumerate(zip(first, second)) if (x + y) % 4]
            for multiplier in (1, 2, 3):
                expected = [(x - multiplier * y) % 4 for x, y in zip(first, second)]
                assert terms(subtract(a, b, multiplier)) == [[i, c] for i, c in enumerate(expected) if c]
            arithmetic += 1
    matrices = memberships = kernel_checks = row_witnesses = 0
    vectors2 = list(product(range(4), repeat=2))
    for entries in product(range(4), repeat=4):
        matrix = [entries[:2], entries[2:]]
        rhs_matrix = [(1, 3), (2, 1)]
        rows = [(encode(enumerate(row)), encode([(i, 1)]), encode(enumerate(rhs_matrix[i]))) for i, row in enumerate(matrix)]
        result = decompose(rows)
        true_span = {tuple(sum(c * matrix[i][j] for i, c in enumerate(v)) % 4 for j in range(2)) for v in vectors2}
        true_kernel = {v for v in vectors2 if all(sum(c * matrix[i][j] for i, c in enumerate(v)) % 4 == 0 for j in range(2))}
        for proposed in vectors2:
            remainder, witness = reduce_vector(encode(enumerate(proposed)), result)
            assert (remainder == ZERO) == (proposed in true_span)
            expected = [(proposed[j] - sum(c * matrix[i][j] for i, c in terms(witness))) % 4 for j in range(2)]
            assert terms(remainder) == [[j, c] for j, c in enumerate(expected) if c]
            memberships += 1
        generators = [row[1] for _, row in result["generators"]]
        generated = set()
        for scalars in product(range(4), repeat=len(generators)):
            vector = ZERO
            for c, row in zip(scalars, generators):
                vector = add(vector, scale(row, c))
            generated.add(tuple(coefficient(vector, j) for j in range(2)))
        assert generated == true_kernel
        kernel_checks += 1
        for row in list(result["units"].values()) + list(result["even"].values()) + [row for _, row in result["generators"]]:
            for actual, initial in ((row[0], matrix), (row[2], rhs_matrix)):
                expected = [sum(c * initial[i][j] for i, c in terms(row[1])) % 4 for j in range(2)]
                assert terms(actual) == [[j, c] for j, c in enumerate(expected) if c]
            row_witnesses += 1
        matrices += 1
    return {"status": "PASS_EXHAUSTIVE_SMALL_MOD4_ARITHMETIC_MODULE_AND_KERNEL_CONTROLS",
            "three_coordinate_vector_pairs": arithmetic, "subtraction_multipliers_per_pair": 3,
            "all_two_by_two_matrices": matrices, "all_ambient_memberships_checked": memberships,
            "complete_annihilator_generations_checked": kernel_checks, "carried_row_witnesses_checked": row_witnesses,
            "optimizer_calls": 0, "native_imports": 0, "seconds": time.monotonic() - started}
