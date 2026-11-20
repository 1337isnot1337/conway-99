"""Bounded NumPy transport audit for a finite integer LP; never calls run()."""
from pathlib import Path
import hashlib
import json
import os
import time

for _key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[_key] = "1"

OPTIONS = {"solver": "simplex", "presolve": "off", "threads": 1,
    "parallel": "off", "random_seed": 0, "simplex_strategy": 1,
    "output_flag": False, "log_to_console": False}
BLOCK_ROWS = 256


def deadline_check(deadline):
    if time.monotonic() >= deadline:
        raise TimeoutError("bounded native transport deadline")


def validate_arrays(arrays, variables, lower, upper, deadline):
    import numpy as np
    names = ("coefficients", "column_indices", "row_pointers", "row_lower", "row_upper")
    for name in names:
        a = arrays[name]
        assert isinstance(a, np.ndarray) and a.ndim == 1 and a.flags.c_contiguous
        assert a.dtype.kind in "iu"
    c, j, p = (arrays[k] for k in names[:3])
    l, u = arrays["row_lower"], arrays["row_upper"]
    n, m, nnz = variables, len(l), len(c)
    assert type(n) is int and 0 < n < 2**31 and 0 <= m < 2**31 and nnz < 2**31
    assert len(j) == nnz and len(p) == m+1 and len(u) == m
    assert int(p[0]) == 0 and int(p[-1]) == nnz and np.all(p[1:] >= p[:-1])
    assert np.all(l <= u)
    assert len(lower) == len(upper) == n
    assert all(type(a) is type(b) is int and 0 <= a <= b <= 1 for a, b in zip(lower, upper))
    for a in (c, l, u):
        if len(a):
            assert max(abs(int(a.min())), abs(int(a.max()))) < 2**53
    assert not nnz or (int(j.min()) >= 0 and int(j.max()) < n)
    assert np.all(c != 0)
    for first in range(0, m, BLOCK_ROWS):
        deadline_check(deadline)
        last = min(m, first+BLOCK_ROWS)
        lo, hi = int(p[first]), int(p[last])
        cols = j[lo:hi]
        if len(cols) > 1:
            bad = cols[1:] <= cols[:-1]
            boundaries = p[first+1:last].astype(np.int64)-lo-1
            boundaries = boundaries[(boundaries >= 0) & (boundaries < len(bad))]
            bad[boundaries] = False
            assert not bad.any(), "duplicate or unordered column within a row"
    return {"variables": n, "rows": m, "nonzeros": nnz}


def build_native(arrays, variables, lower, upper, deadline):
    import highspy
    import numpy as np
    shape = validate_arrays(arrays, variables, lower, upper, deadline)
    h = highspy.Highs()
    try:
        for name, value in OPTIONS.items():
            assert h.setOptionValue(name, value) == highspy.HighsStatus.kOk
        deadline_check(deadline)
        # The raw-array overload avoids a second Python HighsLp matrix wrapper.
        # It copies no 10-million-entry Python lists.
        status = h.passModel(variables, shape["rows"], shape["nonzeros"],
            int(highspy.MatrixFormat.kRowwise), int(highspy.ObjSense.kMinimize), 0.0,
            np.zeros(variables, dtype=np.float64),
            np.asarray(lower, dtype=np.float64), np.asarray(upper, dtype=np.float64),
            arrays["row_lower"].astype(np.float64), arrays["row_upper"].astype(np.float64),
            arrays["row_pointers"].astype(np.int32),
            arrays["column_indices"].astype(np.int32, copy=False),
            arrays["coefficients"].astype(np.float64), np.zeros(variables, dtype=np.int32))
        assert status == highspy.HighsStatus.kOk
        assert h.getRunTime() == 0.0 and not h.getSolution().value_valid
        return h
    except BaseException:
        h.clear()
        raise


def audit_columns(h, variables, lower, upper):
    import highspy
    import numpy as np
    status, count, costs, lows, highs, entries = h.getCols(
        variables, np.arange(variables, dtype=np.int32))
    assert status == highspy.HighsStatus.kOk and count == variables
    assert all(isinstance(x, np.ndarray) for x in (costs, lows, highs))
    assert np.array_equal(costs, np.zeros(variables))
    assert np.array_equal(lows, lower) and np.array_equal(highs, upper)
    assert h.getObjectiveSense() == (highspy.HighsStatus.kOk, highspy.ObjSense.kMinimize)
    assert h.getObjectiveOffset() == (highspy.HighsStatus.kOk, 0.0)
    return int(entries)


def audit_block(arrays, first, last, row_result, entry_result):
    import highspy
    import numpy as np
    status, count, lows, highs, nnz = row_result
    estatus, starts, columns, values = entry_result
    assert status == estatus == highspy.HighsStatus.kOk and count == last-first
    assert all(isinstance(x, np.ndarray) for x in (lows, highs, starts, columns, values))
    assert starts.dtype.kind in "iu" and columns.dtype.kind in "iu" and values.dtype.kind == "f"
    assert np.array_equal(lows, arrays["row_lower"][first:last])
    assert np.array_equal(highs, arrays["row_upper"][first:last])
    p = arrays["row_pointers"]
    begin, end = int(p[first]), int(p[last])
    assert int(nnz) == len(columns) == len(values) == end-begin
    assert len(starts) in (count, count+1)
    if len(starts) == count:
        starts = np.concatenate((starts, np.asarray([nnz], dtype=starts.dtype)))
    assert np.array_equal(starts, p[first:last+1]-begin)
    expected_columns = arrays["column_indices"][begin:end]
    expected_values = arrays["coefficients"][begin:end]
    reordered = 0
    if not (np.array_equal(columns, expected_columns) and np.array_equal(values, expected_values)):
        for k in range(count):
            lo, hi = int(starts[k]), int(starts[k+1])
            order = np.argsort(columns[lo:hi], kind="stable")
            actual = columns[lo:hi][order]
            assert len(actual) < 2 or np.all(actual[1:] > actual[:-1])
            assert np.array_equal(actual, expected_columns[lo:hi])
            assert np.array_equal(values[lo:hi][order], expected_values[lo:hi])
            reordered += 1
    return {"rows": count, "nonzeros": int(nnz), "reordered_rows": reordered,
        "returned_array_bytes": sum(x.nbytes for x in (lows, highs, starts, columns, values))}


def audit_native(h, arrays, variables, lower, upper, deadline):
    import numpy as np
    shape = validate_arrays(arrays, variables, lower, upper, deadline)
    assert h.getNumCol() == variables and h.getNumRow() == shape["rows"]
    assert h.getNumNz() == shape["nonzeros"]
    assert audit_columns(h, variables, lower, upper) == shape["nonzeros"]
    blocks, maximum, reordered = 0, 0, 0
    for first in range(0, shape["rows"], BLOCK_ROWS):
        deadline_check(deadline)
        last = min(shape["rows"], first+BLOCK_ROWS)
        ids = np.arange(first, last, dtype=np.int32)
        check = audit_block(arrays, first, last,
            h.getRows(len(ids), ids), h.getRowsEntries(len(ids), ids))
        blocks += 1
        maximum = max(maximum, check["returned_array_bytes"])
        reordered += check["reordered_rows"]
    assert h.getRunTime() == 0.0 and not h.getSolution().value_valid
    return dict(shape, exact_integer_input=True, exact_all_native_coefficients_and_bounds=True,
        all_zero_objective=True, blocks=blocks, block_rows=BLOCK_ROWS,
        maximum_returned_array_bytes=maximum, reordered_rows=reordered,
        whole_sparse_vector_python_getters=0, native_solver_calls=0)


def reset_box(h, lower, upper):
    import highspy
    import numpy as np
    n = len(lower)
    assert len(upper) == n
    assert all(type(a) is type(b) is int and 0 <= a <= b <= 1 for a, b in zip(lower, upper))
    assert h.changeColsBounds(n, np.arange(n, dtype=np.int32),
        np.asarray(lower, dtype=np.float64), np.asarray(upper, dtype=np.float64)) == highspy.HighsStatus.kOk
    audit_columns(h, n, lower, upper)
    return hashlib.sha256(json.dumps([lower, upper], separators=(",", ":")).encode()).hexdigest()


def controls(output):
    import highspy
    import numpy as np
    start = time.monotonic()
    deadline = start+30
    arrays = {"coefficients": np.asarray([1,-2,3,1,-1,-1,2,-4], dtype=np.int64),
        "column_indices": np.asarray([0,2,1,3,0,1,2,3], dtype=np.int32),
        "row_pointers": np.asarray([0,2,2,4,7,8], dtype=np.int64),
        "row_lower": np.asarray([-3,0,-2,0,-4], dtype=np.int64),
        "row_upper": np.asarray([4,0,5,1,0], dtype=np.int64)}
    lower, upper = [0]*4, [1]*4
    h = build_native(arrays, 4, lower, upper, deadline)
    try:
        audit = audit_native(h, arrays, 4, lower, upper, deadline)
        checks = []
        for first, last in ((0,2),(1,2),(2,5),(4,5)):
            ids = np.arange(first,last,dtype=np.int32)
            checks.append(audit_block(arrays,first,last,h.getRows(len(ids),ids),h.getRowsEntries(len(ids),ids)))
        resets = []
        for lo, hi in [([0,1,0,0],[0,1,1,1]),([1,0,0,0],[1,0,1,0]),(lower,upper)]:
            resets.append(reset_box(h,lo,hi))
        ids = np.arange(5,dtype=np.int32)
        rr, ee = h.getRows(5,ids), h.getRowsEntries(5,ids)
        rejected = 0
        altered = []
        for which in ("coefficient","column","start","lower","upper","count"):
            r = list(rr); e = list(ee)
            if which == "coefficient": e[3] = e[3].copy(); e[3][0] += 1
            elif which == "column": e[2] = e[2].copy(); e[2][0] = 1
            elif which == "start": e[1] = e[1].copy(); e[1][1] += 1
            elif which == "lower": r[2] = r[2].copy(); r[2][0] += 1
            elif which == "upper": r[3] = r[3].copy(); r[3][0] += 1
            else: r[1] += 1
            altered.append((tuple(r),tuple(e)))
        for r,e in altered:
            try:
                audit_block(arrays,0,5,r,e)
            except AssertionError:
                rejected += 1
            else:
                raise AssertionError("malformed native block was accepted")
        assert rejected == 6
        assert h.getRunTime() == 0.0 and not h.getSolution().value_valid
        report = {"status":"PASS_TINY_SIGNED_RAW_ARRAY_TRANSPORT_NO_SOLVE",
            "source_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "highs_version":h.version(),"matrix_audit":audit,"explicit_blocks":checks,
            "bound_reset_hashes":resets,"tampered_native_blocks_rejected":rejected,
            "native_model_loads":1,"native_solver_calls":0,"full_case_matrix_loaded":False,
            "seconds":time.monotonic()-start}
    finally:
        h.clear()
    assert not Path(output).exists()
    Path(output).write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")
    return report


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--controls",type=Path,required=True)
    args = parser.parse_args()
    print(json.dumps(controls(args.controls)),flush=True)

