"""Exact GF(2) row reduction with forward and reverse span certificates.

Rows are (support_bits, rhs_bit, original_witness_bits). Column order is
explicit; no point, model, optimizer or case-specific data is imported.
"""
from itertools import product
import time


def tick(deadline):
    if time.monotonic() >= deadline:
        raise TimeoutError("weighted parity shared arithmetic budget")


def sites(bits):
    assert type(bits) is int and bits >= 0
    while bits:
        bit = bits & -bits
        yield bit.bit_length()-1
        bits ^= bit


def xor_rows(rows, selected):
    assert type(selected) is int and 0 <= selected < 1 << len(rows)
    mask, rhs, witness = 0, 0, 0
    for i in sites(selected):
        a, b, c = rows[i]
        mask ^= a
        rhs ^= b
        witness ^= c
    return mask, rhs, witness


def rref(rows, columns, deadline):
    assert columns == list(dict.fromkeys(columns))
    allowed = sum(1 << j for j in columns)
    assert all(type(a) is type(b) is type(c) is int and a >= 0 and b in (0,1)
               and c >= 0 and not (a & ~allowed) for a,b,c in rows)
    work = [[a,b,c,1 << i] for i,(a,b,c) in enumerate(rows)]
    rank, pivots = 0, []
    for column in columns:
        tick(deadline)
        found = next((i for i in range(rank,len(work)) if work[i][0] >> column & 1), None)
        if found is None:
            continue
        work[rank], work[found] = work[found], work[rank]
        selected = work[rank]
        for i in range(len(work)):
            if i != rank and work[i][0] >> column & 1:
                work[i] = [x ^ y for x,y in zip(work[i],selected)]
        pivots.append(column)
        rank += 1
        if rank == len(work):
            break
    assert all(a == 0 for a,b,c,d in work[rank:])
    return {"rank": rank, "pivots": pivots, "rows": work,
            "inconsistent": any(b for a,b,c,d in work[rank:])}


def remainder(mask, rhs, certificate):
    for pivot, row in zip(certificate["pivots"],certificate["rows"]):
        if mask >> pivot & 1:
            mask ^= row[0]
            rhs ^= row[1]
    return mask, rhs


def verify(rows, columns, certificate, deadline):
    rank, pivots, work = (certificate[k] for k in ("rank","pivots","rows"))
    assert len(work) == len(rows) and len(pivots) == rank
    assert 0 <= rank <= len(rows) and len(set(pivots)) == rank
    positions = {a:i for i,a in enumerate(columns)}
    assert len(positions) == len(columns)
    assert [positions[a] for a in pivots] == sorted(positions[a] for a in pivots)
    for i,(a,b,c,d) in enumerate(work):
        tick(deadline)
        assert xor_rows(rows,d) == (a,b,c), ("forward input-row witness",i)
    for i,pivot in enumerate(pivots):
        assert all((row[0] >> pivot & 1) == (i == j) for j,row in enumerate(work))
    assert all(a == 0 for a,b,c,d in work[rank:])
    inconsistent = any(b for a,b,c,d in work[rank:])
    assert certificate["inconsistent"] is inconsistent
    for i,(a,b,c) in enumerate(rows):
        tick(deadline)
        x,y = remainder(a,b,certificate)
        assert x == 0 and (y == 0 or inconsistent), ("reverse row-space inclusion",i)
    return {"coefficient_rank": rank, "augmented_rank": rank+int(inconsistent),
            "forward_original_witnesses_checked": len(work),
            "reverse_input_row_span_checks": len(rows),
            "independence_from_pivot_identity": True,
            "inconsistent": inconsistent}


def controls(deadline):
    systems, ordered_reductions, span_checks, solution_checks = 0,0,0,0
    for n in range(4):
        columns = [2*j+1 for j in range(n)]
        for m in range(4):
            for packed in product(range(1 << (n+1)), repeat=m):
                tick(deadline)
                rows = [(sum((1 << columns[j]) for j in range(n) if v >> j & 1),
                         v >> n,1 << i) for i,v in enumerate(packed)]
                exact_span = {xor_rows(rows,mask)[:2] for mask in range(1 << m)}
                for order in (columns,columns[::-1]):
                    cert = rref(rows,order,deadline)
                    verify(rows,order,cert,deadline)
                    reduced = [tuple(row[:3]) for row in cert["rows"]]
                    assert {xor_rows(reduced,mask)[:2] for mask in range(1 << m)} == exact_span
                    span_checks += 1
                    for value in range(1 << n):
                        assignment = sum(1 << columns[j] for j in range(n) if value >> j & 1)
                        old = all((a & assignment).bit_count() % 2 == b for a,b,c in rows)
                        new = all((a & assignment).bit_count() % 2 == b for a,b,c in reduced)
                        assert old == new
                        solution_checks += 1
                    ordered_reductions += 1
                systems += 1
    return {"complete_small_augmented_binary_systems": systems,
            "both_column_orders_checked": ordered_reductions,
            "full_enumerated_row_span_checks": span_checks,
            "Boolean_assignment_equivalence_checks": solution_checks,
            "inconsistency_null_rows_and_nonconsecutive_columns_included": True,
            "case_input_read": False, "optimizer_calls": 0}
