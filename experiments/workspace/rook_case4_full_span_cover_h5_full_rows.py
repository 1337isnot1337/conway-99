"""Prepare and replay exact Boolean propagation on 183 conditional H=5 states.

The complete cached selector matrix is retained. Five already proved parity
cuts, the proved 44-term inequality and H=5 are appended. No optimizer is used.
Preparation, one bounded forward prefix and its cold replay are separate modes.
"""
from __future__ import annotations

import argparse
import hashlib
import heapq
import itertools
import json
import os
from pathlib import Path
import resource
import subprocess
import sys
import time

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
BASE = "experiments/logs/grids-and-triangles/"
INPUTS = {
    "model": (BASE+"rook-case4-face112-weighted-parity-model01/model.json", "c6cd72c995ce1a47db90fe7263f643131bc555ed50e329c7734536f5cf870ac3"),
    "arrays": (BASE+"rook-case4-face112-weighted-parity-model01/arrays.npz", "59a06470793e6959a67ae30dfb29ecf0de4c8aa74661e1335d7676aa612c1e7e"),
    "matrix_cold": (BASE+"rook-case4-face112-weighted-parity-model01-cold-replay.json", "567185c755134fcf7c15bb7be762bb2a70a503254259b2eb44a92f91abb39156"),
    "native": (BASE+"complement-rook-35core-case0004-native-cpsat-model.json", "a9004e97a2d166bf8b162609cfb538eae0dd4d26942b6df5119b6a88d65ec476"),
    "upper_five": (BASE+"rook-case4-full-span-cover-upper-five01.json", "1655bac4e5a5a558e58e0a685aa4dc94489ef5bfb8f065afe43ac8a6ddcd3b1f"),
    "projection": (BASE+"rook-case4-full-span-cover-native-projection01.json", "795aaaba3743f3930c1c6c3e2cb69123704bf581669ff9690ef74804b6d5c8d9"),
    "old_branches": (BASE+"rook-case4-full-span-cover-h5-branches-run01.json", "95867d8594425c4069d5aa5e30402c84a1253b000d9c59446ae105a94cfd8653"),
    "old_cold": (BASE+"rook-case4-full-span-cover-h5-branches-run01-replay.json", "f59ddd034a00d344bfef94812ec0eb595a16d01a806be1f01aec0147c9f3a70b"),
    "short_cut": (BASE+"rook-case4-full-span-cover-strengthened-cut01.json", "65128ef554e550f2b78569cadd52477ddd8fd35ddd81d480d9c1ea9048bc1da8"),
    "short_cold": (BASE+"rook-case4-full-span-cover-strengthened-cut-replay01.json", "a01b169ce78471d675f0287560cb9ac6cb0247712e0d5bd3a189c8c2ec663267"),
    "initial_registry": (BASE+"rook-case4-full-span-cycle-preparation01.json", "6be18862b4555fed0d78c404937e46512eab7d3fb3361e78cbde8af6f30c543a"),
    "parity_registry": (BASE+"rook-case4-full-span-cycle-run01/result.json", "408da79724822a1197fbda868fe73e5de70fd36b2b55a448716be2573944df32"),
    "registry_cold": (BASE+"rook-case4-full-span-cycle-run01-bindings.json", "e19e9cf1585ef885a633f50af391712d99f5e1b117fa95f36c729ead9985ebf6"),
}
LIMITS = {
    "forward_seconds": 60, "per_branch_seconds": 5, "replay_seconds": 60,
    "owned_child_seconds": 90, "maximum_branches": 183,
    "maximum_transcript_bytes": 64*1024*1024,
    "maximum_new_forces_per_branch": 1102,
    "maximum_rss_kib": 1024*1024,
    "automatic_retries": 0,
}
BASE_ROWS, ROWS, VARIABLES, BASE_NNZ = 166013, 166020, 1102, 10767292


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, separators=(",", ":"), ensure_ascii=False).encode()


def json_write(path, value):
    path = Path(path)
    assert not path.exists(), path
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(json.dumps(value, indent=2).encode()+b"\n")
        stream.flush()
        os.fsync(stream.fileno())


def reference(path):
    path = Path(path)
    return {"path": str(path), "sha256": digest(path.read_bytes()), "bytes": path.stat().st_size}


def checked_inputs(root):
    out = {}
    for key, (name, expected) in INPUTS.items():
        raw = (root/name).read_bytes()
        assert digest(raw) == expected, key
        if key != "arrays":
            out[key] = json.loads(raw)
    return out


def gram_sum(inventory, terms):
    coeff = [0]*1214
    rhs = 0
    for rid, weight in terms:
        assert type(rid) is int and 0 <= rid < 630 and type(weight) is int
        row = inventory["Gram_rows"][rid]
        rhs += weight*row[2]
        for a in row[3]:
            coeff[a] += weight
    return coeff, rhs


def verify_append_proofs(data):
    """Rebuild every appended row's original-coordinate mathematical proof."""
    inventory = data["native"]["primary_inventory"]
    theorem, short = data["upper_five"], data["short_cut"]
    zeros = set(data["model"]["fixed_zero_columns"])
    H = theorem["H"]
    assert len(H) == len(set(H)) == 42 and not (set(H) & zeros)
    assert len(zeros) == 112 and data["short_cold"]["status"] == "PASS"
    assert theorem["conditional_H_equals_five"]["prior_global_zero_columns"] == data["model"]["fixed_zero_columns"]
    assert short["needed_proved_zero_columns"] == [126,465,783,966,970,973,977]
    assert set(short["needed_proved_zero_columns"]) <= zeros
    q, b = gram_sum(inventory, [(r,1) for r in theorem["upper"]["original_row_ids"]])
    residual = [q[a]-(a in H) for a in range(1214)]
    assert b == 5 and residual == theorem["upper"]["full1214_residual"]
    assert min(residual) >= 0
    assert theorem["conditional_H_equals_five"]["new_zero_columns"] == [
        a for a in range(1214) if residual[a] > 0 and a not in zeros]
    c, b = gram_sum(inventory, [(r,1) for r in short["parity"]["original_Gram_rows"]])
    assert b == 81 and c == short["parity"]["full1214_coefficients"]
    assert [a for a in range(1214) if c[a] % 2 and a not in zeros] == H
    c, b = gram_sum(inventory, short["bound922"]["original_Gram_rows"])
    r = [c[a]-(a in H)-3*(a == 922) for a in range(1214)]
    assert b == 7 and r == short["bound922"]["full1214_nonnegative_residual"] and min(r) >= 0
    c, b = gram_sum(inventory, short["bound600"]["direct_Gram_rows"])
    r = [c[a]-3*(a in H)-4*(a == 600) for a in range(1214)]
    assert b == 18 and r == short["bound600"]["full1214_residual"]
    assert all(v == -1 if a == 783 else v >= 0 for a, v in enumerate(r))
    cap = inventory["Gram_rows"][617]
    assert cap[:3] == [30,32,1] and 600 in cap[3] and 922 in cap[3]
    wanted = sorted([[a,1] for a in H]+[[600,2],[922,2]])
    assert short["final_integer_inequality"] == {"terms":wanted, "upper":5}
    for total, a, b in itertools.product((1,3,5), (0,1), (0,1)):
        if a+b <= 1 and total+3*b <= 7 and 3*total+4*a <= 18:
            assert total+2*(a+b) <= 5
    additions = []
    registry = data["parity_registry"]["registry"]
    assert len(registry) == 5
    assert registry[:4] == data["initial_registry"]["seed_registry"]
    assert data["registry_cold"]["status"].startswith("PASS:")
    assert data["registry_cold"]["registered_cuts"] == 5
    assert data["registry_cold"]["result"]["sha256"] == INPUTS["parity_registry"][1]
    for k, entry in enumerate(registry):
        cert = entry["certificate"]
        c, b = gram_sum(inventory, [(r,1) for r in cert["original_Gram_row_ids"]])
        assert c == cert["full_original1214_integer_coefficients"]
        assert b == cert["original_Gram_rhs_sum"] and b % 2 == cert["parity_rhs"]
        support = [a for a in range(1214) if c[a] % 2 and a not in zeros]
        removed = [a for a in range(1214) if c[a] % 2 and a in zeros]
        assert removed == cert["removed_proved_zero_odd_columns"]
        forbidden = cert["forbidden_vertex_certificate"]["forbidden_ones"]
        assert len(forbidden) == len(set(forbidden)) and set(forbidden) <= set(support)
        assert len(forbidden) % 2 != b % 2
        expected = [[a,1 if a in forbidden else -1] for a in support]
        assert cert["inequality"] == {"terms":expected, "upper":len(forbidden)-1}
        additions.append({"kind":"existing_parity", "index":k,
            "terms":expected, "lower":-len(support)+len(forbidden), "upper":len(forbidden)-1})
    additions.append({"kind":"proved_strengthened_H", "index":0,
        "terms":wanted, "lower":0, "upper":5})
    additions.append({"kind":"conditional_H_five", "index":0,
        "terms":[[a,1] for a in H], "lower":5, "upper":5})
    assert len(additions) == 7
    return additions


def native_rows(data):
    """Same literal native equations as the accepted V8 trace; no propagation."""
    I = data["native"]["primary_inventory"]
    out = []
    def add(terms, lower, upper):
        collected = {}
        for a, c in terms:
            collected[a] = collected.get(a, 0)+c
        out.append((sorted((a,c) for a,c in collected.items() if c), lower, upper))
    for i,j,q,s in I["Gram_rows"]:
        add([(a,1) for a in s], q, q)
    for sig,s in I["original_signature_rows"]:
        add([(a,1) for a in s], 0, 1)
    for r in I["triple_rows"]:
        add([(a,1) for a in r["members"]], 0, 1)
    for r in I["Gram_conflict_clauses"]:
        assert all(v < 0 for v in r)
        add([(-v-1,1) for v in r], 0, len(r)-1)
    for r in I["uncapped_integer_cuts"]:
        add(r["positive_terms"]+[[r["target_column"],-r["positive_demand"]]],
            0, sum(w for a,w in r["positive_terms"]))
    assert len(out) == 2271
    add([(a,1) for a in data["upper_five"]["H"]], 5, 5)
    return out


def literal_bounds(row, state, override=None):
    lower = upper = 0
    for a, c in row[0]:
        value = int(override[1] if override is not None and a == override[0] else state[a])
        if value < 0:
            lower += min(0,c)
            upper += max(0,c)
        else:
            lower += c*value
            upper += c*value
    return lower, upper


def survivor_states(data, columns):
    """Recheck the exact old proof prefix used as each new conditional premise."""
    old, cold, projection = data["old_branches"], data["old_cold"], data["projection"]
    assert old["complete"] and len(old["records"]) == 996
    assert old["contradictions"] == 813 and old["noncontradictory_fixed_points"] == 183
    assert cold["status"] == "PASS" and cold["checked"] == 996
    assert projection["complete"] and len(projection["subsets"][5]) == 996
    theorem = data["upper_five"]
    rows = native_rows(data)
    records, states = [], []
    for rid, old_record in enumerate(old["records"]):
        assert old_record["id"] == rid and old_record["pattern"] == projection["subsets"][5][rid]
        assert cold["checks"][rid]["status"] == "PASS"
        if old_record["terminal"]["status"] != "fixed_point":
            continue
        state = [-1]*1214
        for a in theorem["conditional_H_equals_five"]["prior_global_zero_columns"]:
            state[a] = 0
        for a in theorem["conditional_H_equals_five"]["new_zero_columns"]:
            assert state[a] in (-1,0)
            state[a] = 0
        selected = set(old_record["pattern"])
        for a in theorem["H"]:
            assert state[a] in (-1,int(a in selected))
            state[a] = int(a in selected)
        for rowid, a, value in old_record["trace"]:
            assert 0 <= rowid < len(rows) and value in (0,1) and state[a] == -1
            row = rows[rowid]
            lo, hi = literal_bounds(row, state)
            assert lo <= row[2] and hi >= row[1]
            lo, hi = literal_bounds(row, state, (a,1-value))
            assert hi < row[1] or lo > row[2], ("old reason", rid, rowid, a)
            state[a] = value
        assert state.count(0) == old_record["final_zero_count"]
        assert state.count(1) == old_record["final_one_count"]
        for row in rows:
            lo, hi = literal_bounds(row, state)
            assert lo <= row[2] and hi >= row[1]
        projected = np.asarray([state[int(a)] for a in columns], dtype=np.int8)
        records.append({"prior_branch_id":rid, "pattern":old_record["pattern"],
            "prior_trace_forces":len(old_record["trace"]),
            "initial_state_sha256":digest(projected.tobytes())})
        states.append(projected)
    assert len(records) == 183
    return records, np.asarray(states, dtype=np.int8)


class Pool:
    """Integer CSR rows, with a stable column-to-entry index for exact updates."""
    def __init__(self, pointers, columns, coefficients, lower, upper, nvars):
        self.ptr = np.asarray(pointers, dtype=np.int64)
        self.col = np.asarray(columns, dtype=np.int32)
        self.coef = np.asarray(coefficients, dtype=np.int64)
        self.lower = np.asarray(lower, dtype=np.int64)
        self.upper = np.asarray(upper, dtype=np.int64)
        self.nvars, self.nrows, self.nnz = nvars, len(self.lower), len(self.coef)
        assert len(self.ptr) == self.nrows+1 and self.ptr[0] == 0 and self.ptr[-1] == self.nnz
        lengths = np.diff(self.ptr)
        assert np.all(lengths >= 0) and len(self.col) == self.nnz
        assert np.all(self.lower <= self.upper)
        assert np.all((self.col >= 0) & (self.col < nvars))
        maximum = max(abs(int(self.coef.min(initial=0))), abs(int(self.coef.max(initial=0))))
        endpoint = max(abs(int(self.lower.min(initial=0))), abs(int(self.lower.max(initial=0))),
                       abs(int(self.upper.min(initial=0))), abs(int(self.upper.max(initial=0))))
        self.activity_bound = self.nnz*maximum
        # This Python-integer check precedes all int64 sums and endpoint gaps.
        assert self.activity_bound+endpoint+maximum < 2**62
        self.entry_row = np.repeat(np.arange(self.nrows,dtype=np.int32), lengths)
        if self.nnz > 1:
            assert np.all((self.col[1:] > self.col[:-1]) |
                          (self.entry_row[1:] != self.entry_row[:-1])), "duplicate or unordered column within row"
        self.nonempty = np.flatnonzero(lengths)
        self.starts = self.ptr[self.nonempty]
        self.max_abs = np.zeros(self.nrows,dtype=np.int64)
        if self.nnz:
            self.max_abs[self.nonempty] = np.maximum.reduceat(np.abs(self.coef), self.starts)
        self.order = np.argsort(self.col, kind="stable")
        counts = np.bincount(self.col,minlength=nvars).astype(np.int64)
        self.column_ptr = np.concatenate((np.zeros(1,dtype=np.int64),np.cumsum(counts,dtype=np.int64)))
        assert self.column_ptr[-1] == self.nnz
        # Stable ordering plus strict within-row uniqueness proves that every
        # fancy-index update below touches each affected row exactly once.

    def extrema(self, state):
        assert state.shape == (self.nvars,) and np.all((state >= -1) & (state <= 1))
        lo = np.zeros(self.nrows,dtype=np.int64)
        hi = lo.copy()
        free_count = lo.copy()
        if not self.nnz:
            return lo,hi,free_count
        values = self.coef*np.maximum(state[self.col],0)
        free = state[self.col] < 0
        values[free] = np.minimum(self.coef[free],0)
        lo[self.nonempty] = np.add.reduceat(values,self.starts,dtype=np.int64)
        values[free] = np.maximum(self.coef[free],0)
        hi[self.nonempty] = np.add.reduceat(values,self.starts,dtype=np.int64)
        free_count[self.nonempty] = np.add.reduceat(free,self.starts,dtype=np.int64)
        return lo,hi,free_count

    def update(self, variable, value, lo, hi, free_count):
        entries = self.order[self.column_ptr[variable]:self.column_ptr[variable+1]]
        affected = self.entry_row[entries]
        coeff = self.coef[entries]
        # No duplicate indices: each variable appears at most once in each row.
        lo[affected] += coeff*value-np.minimum(coeff,0)
        hi[affected] += coeff*value-np.maximum(coeff,0)
        free_count[affected] -= 1
        return affected

    def row(self, rid):
        begin,end = map(int,self.ptr[rid:rid+2])
        return ([(int(a),int(c)) for a,c in zip(self.col[begin:end],self.coef[begin:end])],
                int(self.lower[rid]),int(self.upper[rid]))

    def relevant(self, rows, lo, hi, free_count):
        return rows[(free_count[rows] > 0) &
                    ((hi[rows]-self.lower[rows] < self.max_abs[rows]) |
                     (self.upper[rows]-lo[rows] < self.max_abs[rows]))]


def matrix(root, data):
    model = data["model"]
    assert (model["columns"],model["rows"],model["nonzeros"]) == (VARIABLES,BASE_ROWS,BASE_NNZ)
    assert model["arrays"]["sha256"] == INPUTS["arrays"][1]
    assert data["matrix_cold"]["status"].startswith("PASS:")
    with np.load(root/INPUTS["arrays"][0],allow_pickle=False) as archive:
        arrays = {name:archive[name] for name in archive.files}
    assert set(arrays) == set(model["array_sha256"])
    assert all(a.dtype.kind in "iu" for a in arrays.values())
    assert {k:digest(v.tobytes()) for k,v in arrays.items()} == model["array_sha256"]
    columns = arrays["original_column_ids"]
    assert list(map(int,columns)) == [a for a in range(1214) if a not in set(model["fixed_zero_columns"])]
    position = {int(a):j for j,a in enumerate(columns)}
    additions = verify_append_proofs(data)
    suffix_col, suffix_coef, ends = [],[],[]
    for row in additions:
        terms = [(position[a],c) for a,c in row["terms"]]
        assert terms == sorted(terms) and len({a for a,c in terms}) == len(terms)
        suffix_col.extend(a for a,c in terms)
        suffix_coef.extend(c for a,c in terms)
        ends.append(BASE_NNZ+len(suffix_col))
    pool = Pool(
        np.concatenate((arrays["row_pointers"],np.asarray(ends,dtype=np.int64))),
        np.concatenate((arrays["column_indices"],np.asarray(suffix_col,dtype=np.int32))),
        np.concatenate((arrays["coefficients"],np.asarray(suffix_coef,dtype=np.int64))),
        np.concatenate((arrays["row_lower"],np.asarray([r["lower"] for r in additions],dtype=np.int64))),
        np.concatenate((arrays["row_upper"],np.asarray([r["upper"] for r in additions],dtype=np.int64))),
        VARIABLES)
    assert pool.nrows == ROWS
    assert np.array_equal(pool.ptr[:BASE_ROWS+1],arrays["row_pointers"])
    assert np.array_equal(pool.col[:BASE_NNZ],arrays["column_indices"])
    assert np.array_equal(pool.coef[:BASE_NNZ],arrays["coefficients"])
    assert np.array_equal(pool.lower[:BASE_ROWS],arrays["row_lower"])
    assert np.array_equal(pool.upper[:BASE_ROWS],arrays["row_upper"])
    return pool, columns, additions


def terminal_bad(pool, lo, hi, candidates):
    bad = candidates[(hi[candidates] < pool.lower[candidates]) | (lo[candidates] > pool.upper[candidates])]
    if not len(bad):
        return None
    rid = int(bad.min())
    return {"status":"contradiction", "row":rid, "minimum":int(lo[rid]),"maximum":int(hi[rid])}


def propagate(pool, initial, originals, deadline):
    state = initial.copy()
    lo,hi,free = pool.extrema(state)
    all_rows = np.arange(pool.nrows,dtype=np.int32)
    terminal = terminal_bad(pool,lo,hi,all_rows)
    relevant = pool.relevant(all_rows,lo,hi,free)
    heap = list(map(int,relevant))
    heapq.heapify(heap)
    pending = np.zeros(pool.nrows,dtype=np.bool_)
    pending[relevant] = True
    trace, visits = [],0
    while heap and terminal is None:
        if time.monotonic() >= deadline:
            terminal = {"status":"partial","reason":"declared time bound"}
            break
        rid = heapq.heappop(heap)
        pending[rid] = False
        visits += 1
        low, high = int(lo[rid]),int(hi[rid])
        row_lower, row_upper = int(pool.lower[rid]),int(pool.upper[rid])
        begin,end = map(int,pool.ptr[rid:rid+2])
        for offset in range(begin,end):
            a,c = int(pool.col[offset]),int(pool.coef[offset])
            if state[a] >= 0:
                continue
            l0,u0 = low-min(0,c),high-max(0,c)
            l1,u1 = l0+c,u0+c
            feasible0 = u0 >= row_lower and l0 <= row_upper
            feasible1 = u1 >= row_lower and l1 <= row_upper
            if not feasible0 and not feasible1:
                terminal = {"status":"contradiction_by_binary_split","row":rid,"original_column":int(originals[a])}
                break
            if feasible0 == feasible1:
                continue
            value = int(feasible1)
            trace.append([rid,int(originals[a]),value])
            assert len(trace) <= pool.nvars
            state[a] = value
            affected = pool.update(a,value,lo,hi,free)
            terminal = terminal_bad(pool,lo,hi,affected)
            if terminal is None:
                for nxt in pool.relevant(affected,lo,hi,free):
                    nxt = int(nxt)
                    if not pending[nxt]:
                        pending[nxt] = True
                        heapq.heappush(heap,nxt)
            break
    if terminal is None:
        terminal = {"status":"fixed_point"}
    return {"terminal":terminal,"trace":trace,"final_zero_count":int(np.count_nonzero(state == 0)),
            "final_one_count":int(np.count_nonzero(state == 1)),
            "final_state_sha256":digest(state.tobytes()),"row_visits":visits}


def verify_record(pool, initial, originals, record):
    """Trace reasons use Python integers and each current Boolean box."""
    state = initial.copy()
    position = {int(a):j for j,a in enumerate(originals)}
    for rid, original, value in record["trace"]:
        assert type(rid) is int and 0 <= rid < pool.nrows
        assert type(original) is int and original in position and value in (0,1)
        a = position[original]
        assert state[a] == -1
        row = pool.row(rid)
        assert any(j == a for j,c in row[0])
        lo,hi = literal_bounds(row,state)
        assert lo <= row[2] and hi >= row[1], "reason already contradictory"
        lo,hi = literal_bounds(row,state,(a,1-value))
        assert hi < row[1] or lo > row[2], "unproved forced literal"
        state[a] = value
    assert int(np.count_nonzero(state == 0)) == record["final_zero_count"]
    assert int(np.count_nonzero(state == 1)) == record["final_one_count"]
    assert digest(state.tobytes()) == record["final_state_sha256"]
    terminal = record["terminal"]
    if terminal["status"] == "contradiction":
        row = pool.row(terminal["row"])
        lo,hi = literal_bounds(row,state)
        assert lo == terminal["minimum"] and hi == terminal["maximum"]
        assert hi < row[1] or lo > row[2]
    elif terminal["status"] == "contradiction_by_binary_split":
        a = position[terminal["original_column"]]
        assert state[a] == -1
        row = pool.row(terminal["row"])
        for value in (0,1):
            lo,hi = literal_bounds(row,state,(a,value))
            assert hi < row[1] or lo > row[2]
    elif terminal["status"] == "fixed_point":
        # Exact sparse int64 reductions are permitted by Pool's checked global
        # activity bound. Every potentially forcing row is then checked directly.
        lo,hi,free = pool.extrema(state)
        ids = np.arange(pool.nrows,dtype=np.int32)
        assert terminal_bad(pool,lo,hi,ids) is None
        for rid in pool.relevant(ids,lo,hi,free):
            row = pool.row(int(rid))
            for a,c in row[0]:
                if state[a] < 0:
                    for value in (0,1):
                        l,u = literal_bounds(row,state,(a,value))
                        assert l <= row[2] and u >= row[1], "unexhausted fixed point"
    else:
        assert terminal["status"] == "partial"
    return {"status":"PASS","terminal":terminal["status"],"forces":len(record["trace"])}


def tiny_pool(rows, variables):
    ptr, col, coef, lower, upper = [0],[],[],[],[]
    for terms, lo, hi in rows:
        col.extend(a for a,c in terms)
        coef.extend(c for a,c in terms)
        ptr.append(len(col))
        lower.append(lo)
        upper.append(hi)
    return Pool(ptr,col,coef,lower,upper,variables)


def controls():
    """Literal Boolean controls, including repeated rows and rejected duplicates."""
    extrema_cases = update_cases = 0
    for coeff in itertools.product(range(-2,3),repeat=3):
        row = (list(enumerate(coeff)),-3,3)
        rows = [row,row,([],0,0)]
        pool = tiny_pool(rows,3)
        for values in itertools.product((-1,0,1),repeat=3):
            state = np.asarray(values,dtype=np.int8)
            lo,hi,free = pool.extrema(state)
            for r, original_row in enumerate(rows):
                l,u = literal_bounds(original_row,state)
                assert (int(lo[r]),int(hi[r])) == (l,u)
                assert free[r] == sum(state[a] < 0 for a,c in original_row[0])
            extrema_cases += 1
            for a in range(3):
                if state[a] < 0:
                    for value in (0,1):
                        l,u,f = lo.copy(),hi.copy(),free.copy()
                        affected = pool.update(a,value,l,u,f)
                        assert len(affected) == len(set(map(int,affected)))
                        modified = state.copy()
                        modified[a] = value
                        for r, original_row in enumerate(rows):
                            el,eu = literal_bounds(original_row,modified)
                            assert (int(l[r]),int(u[r])) == (el,eu)
                            assert f[r] == sum(modified[j] < 0 for j,c in original_row[0])
                        update_cases += 1
    duplicate_rejected = False
    try:
        tiny_pool([([(0,1),(0,1)],0,1)],1)
    except AssertionError:
        duplicate_rejected = True
    assert duplicate_rejected
    propagation_cases = literal_completions = 0
    examples = [
        ([([(0,2)],1,1)],[-1]),
        ([([],1,1)],[-1]),
        ([([(0,1),(1,1)],1,1), ([(1,1),(2,1)],0,1)], [1,-1,-1]),
        ([([(0,-2),(1,3)],1,1), ([(1,1)],0,1)], [-1,-1]),
    ]
    # Deterministic finite family, not a randomized case4 query.
    for seed in range(256):
        n = 1+seed % 5
        rows = []
        for rid in range(1+seed % 4):
            terms = [(a,((seed*(a+1)+3*rid+5*a) % 7)-3) for a in range(n)]
            low = ((seed+rid) % 7)-3
            high = low+(seed+2*rid) % 5
            rows.append((terms,low,high))
        initial = [-1 if (seed+a) % 3 else (seed+a) % 2 for a in range(n)]
        examples.append((rows,initial))
    for rows, initial in examples:
        n = len(initial)
        pool = tiny_pool(rows,n)
        state = np.asarray(initial,dtype=np.int8)
        originals = np.arange(n,dtype=np.int32)
        result = propagate(pool,state,originals,time.monotonic()+5)
        assert result["terminal"]["status"] != "partial"
        verify_record(pool,state,originals,result)
        feasible = []
        for point in itertools.product((0,1),repeat=n):
            if any(initial[a] >= 0 and point[a] != initial[a] for a in range(n)):
                continue
            literal_completions += 1
            if all(lo <= sum(c*point[a] for a,c in terms) <= hi for terms,lo,hi in rows):
                feasible.append(point)
        if result["terminal"]["status"].startswith("contradiction"):
            assert not feasible
        else:
            for rid,a,value in result["trace"]:
                assert all(point[a] == value for point in feasible)
        propagation_cases += 1
    # A complete replay must reject a changed forced bit, not just a hash change.
    pool = tiny_pool([([(0,1)],1,1)],1)
    initial, originals = np.asarray([-1],dtype=np.int8),np.asarray([0],dtype=np.int32)
    result = propagate(pool,initial,originals,time.monotonic()+5)
    bad = json.loads(json.dumps(result))
    bad["trace"][0][2] = 0
    rejected = False
    try:
        verify_record(pool,initial,originals,bad)
    except AssertionError:
        rejected = True
    assert rejected
    signed_parity_cases = 0
    for width in range(6):
        for parity in (0,1):
            for forbidden in itertools.product((0,1),repeat=width):
                if sum(forbidden) % 2 == parity:
                    continue
                coefficients = [1 if bit else -1 for bit in forbidden]
                upper = sum(forbidden)-1
                for point in itertools.product((0,1),repeat=width):
                    if sum(point) % 2 == parity:
                        assert sum(c*x for c,x in zip(coefficients,point)) <= upper
                        signed_parity_cases += 1
    return {"status":"PASS","extrema_states":extrema_cases,
        "single_coordinate_updates":update_cases,"complete_propagation_cases":propagation_cases,
        "literal_completions":literal_completions,
        "duplicate_column_within_row_rejected":True,"duplicate_rows_retained":True,
        "tampered_force_rejected":True,"signed_parity_vertex_cases":signed_parity_cases,
        "optimizer_calls":0,"case4_propagation_calls":0}


def prepare(root, directory):
    assert np.__version__ == "2.3.5"
    assert not directory.exists()
    directory.mkdir(parents=True)
    started = time.monotonic()
    control_report = controls()
    data = checked_inputs(root)
    pool, originals, additions = matrix(root,data)
    records, states = survivor_states(data,originals)
    state_path = directory/"states.npz"
    with state_path.open("xb") as stream:
        np.savez_compressed(stream,states=states,original_column_ids=originals)
    report = {
        "status":"PREPARED: complete cached selector rows and 183 conditional H5 states; no case propagation",
        "source_sha256":digest(Path(__file__).read_bytes()),
        "input_bindings":INPUTS,"numpy_version":np.__version__,"limits":LIMITS,
        "columns":pool.nvars,"rows":pool.nrows,"nonzeros":pool.nnz,
        "unchanged_parent_rows":BASE_ROWS,"unchanged_parent_nonzeros":BASE_NNZ,
        "all_parent_array_prefixes_equal":True,
        "all_original_coordinate_append_proofs_checked":True,
        "maximum_global_int64_activity_bound":pool.activity_bound,
        "column_incidence_index_has_no_repeated_row_within_a_column":True,
        "prepared_states":{"file":state_path.name,"sha256":digest(state_path.read_bytes()),
            "bytes":state_path.stat().st_size,"shape":list(states.shape)},
        "branches":records,"appended_rows":additions,"controls":control_report,
        "case4_propagation_calls":0,"optimizer_calls":0,
        "full_original_cover_supports_reconstructed":False,
        "seconds":time.monotonic()-started,
        "peak_rss_kib":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    }
    assert report["peak_rss_kib"] <= LIMITS["maximum_rss_kib"]
    json_write(directory/"preparation.json",report)
    return report


def load_preparation(root, path):
    report = json.loads(path.read_bytes())
    assert report["source_sha256"] == digest(Path(__file__).read_bytes())
    assert report["input_bindings"] == {k:list(v) for k,v in INPUTS.items()}
    assert report["limits"] == LIMITS and report["controls"]["status"] == "PASS"
    assert report["numpy_version"] == np.__version__ == "2.3.5"
    assert (report["rows"],report["columns"]) == (ROWS,VARIABLES)
    state_path = path.parent/report["prepared_states"]["file"]
    assert digest(state_path.read_bytes()) == report["prepared_states"]["sha256"]
    with np.load(state_path,allow_pickle=False) as archive:
        states,originals = archive["states"],archive["original_column_ids"]
    assert states.dtype == np.dtype("int8") and states.shape == (183,VARIABLES)
    assert np.all((states >= -1)&(states <= 1))
    data = checked_inputs(root)
    pool, current_columns, additions = matrix(root,data)
    assert np.array_equal(originals,current_columns)
    assert additions == report["appended_rows"] and pool.nnz == report["nonzeros"]
    for r,state in zip(report["branches"],states):
        assert digest(state.tobytes()) == r["initial_state_sha256"]
    return report,pool,originals,states


def child_forward(root, preparation, directory):
    initialized = time.monotonic()
    prep,pool,originals,states = load_preparation(root,preparation)
    initialization_seconds = time.monotonic()-initialized
    started = time.monotonic()
    deadline = started+LIMITS["forward_seconds"]
    records, total_bytes, stop = [],0,"complete"
    for index, (branch, state) in enumerate(zip(prep["branches"],states)):
        if time.monotonic() >= deadline:
            stop = "shared forward time limit"
            break
        one_start = time.monotonic()
        result = propagate(pool,state,originals,min(deadline,one_start+LIMITS["per_branch_seconds"]))
        record = {"index":index,"prior_branch_id":branch["prior_branch_id"],
            "pattern":branch["pattern"],"initial_state_sha256":branch["initial_state_sha256"],
            **result,"seconds":time.monotonic()-one_start}
        encoded = json.dumps(record,indent=2).encode()+b"\n"
        if total_bytes+len(encoded) > LIMITS["maximum_transcript_bytes"]:
            stop = "transcript cap before record acceptance"
            break
        path = directory/f"branch-{index:03d}.json"
        json_write(path,record)
        total_bytes += len(encoded)
        records.append(reference(path))
        if result["terminal"]["status"] == "partial":
            stop = "first partial branch"
            break
    statuses = [json.loads(Path(r["path"]).read_bytes())["terminal"]["status"] for r in records]
    complete = len(records) == 183 and "partial" not in statuses
    result = {
        "status":"COMPLETE_CONDITIONAL_PREFIX" if complete else "PARTIAL_CONDITIONAL_PREFIX",
        "source_sha256":digest(Path(__file__).read_bytes()),"preparation":reference(preparation),
        "records":records,"stop":stop,"complete":complete,
        "checked_input_patterns":183,"recorded_patterns":len(records),
        "unprocessed_patterns_UNKNOWN":183-len(records),
        "contradictions":sum(s.startswith("contradiction") for s in statuses),
        "full_row_fixed_points":statuses.count("fixed_point"),
        "partial_patterns":statuses.count("partial"),
        "all_H5_patterns_refuted_owner_claim":complete and all(s.startswith("contradiction") for s in statuses),
        "case4_excluded":False,"cold_replay_required_before_any_H5_exclusion":True,
        "transcript_bytes":total_bytes,"initialization_seconds":initialization_seconds,
        "forward_seconds":time.monotonic()-started,
        "peak_rss_kib":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "optimizer_calls":0,
    }
    assert result["peak_rss_kib"] <= LIMITS["maximum_rss_kib"]
    json_write(directory/"child-result.json",result)
    return result


def child_replay(root, preparation, source_directory, directory):
    initialized = time.monotonic()
    prep,pool,originals,states = load_preparation(root,preparation)
    initialization_seconds = time.monotonic()-initialized
    started = time.monotonic()
    deadline = started+LIMITS["replay_seconds"]
    forward_path = source_directory/"child-result.json"
    forward = json.loads(forward_path.read_bytes())
    assert forward["source_sha256"] == digest(Path(__file__).read_bytes())
    assert forward["preparation"]["sha256"] == digest(preparation.read_bytes())
    checks = []
    for index, ref in enumerate(forward["records"]):
        if time.monotonic() >= deadline:
            break
        path = Path(ref["path"])
        assert digest(path.read_bytes()) == ref["sha256"]
        record = json.loads(path.read_bytes())
        expected = prep["branches"][index]
        assert record["index"] == index
        assert record["prior_branch_id"] == expected["prior_branch_id"]
        assert record["pattern"] == expected["pattern"]
        assert record["initial_state_sha256"] == expected["initial_state_sha256"]
        check = verify_record(pool,states[index],originals,record)
        check.update(index=index,prior_branch_id=record["prior_branch_id"])
        checks.append(check)
    all_checked = len(checks) == len(forward["records"])
    result = {
        "status":"PASS" if all_checked else "PARTIAL_REPLAY",
        "source_sha256":digest(Path(__file__).read_bytes()),"preparation":reference(preparation),
        "forward_result":reference(forward_path),"checks":checks,
        "all_saved_records_checked":all_checked,
        "all_183_patterns_checked":all_checked and len(checks) == 183,
        "checked_contradictions":sum(c["terminal"].startswith("contradiction") for c in checks),
        "checked_fixed_points":sum(c["terminal"] == "fixed_point" for c in checks),
        "H5_excluded":all_checked and len(checks) == 183 and all(c["terminal"].startswith("contradiction") for c in checks),
        "case4_excluded":False,"old_813_refutations_bound_in_preparation":True,
        "initialization_seconds":initialization_seconds,"replay_seconds":time.monotonic()-started,
        "optimizer_calls":0,"full_row_fixed_points_checked_when_reported":True,
    }
    json_write(directory/"child-result.json",result)
    return result


def owned(mode, root, preparation, directory, source_directory=None):
    assert not directory.exists()
    directory.mkdir(parents=True)
    started = time.monotonic()
    command = [sys.executable,str(Path(__file__).resolve()),"_"+mode,
               "--root",str(root.resolve()),"--preparation",str(preparation.resolve()),
               "--directory",str(directory.resolve())]
    if source_directory is not None:
        command += ["--source-directory",str(source_directory.resolve())]
    timed_out = False
    with (directory/"stdout.log").open("xb") as out,(directory/"stderr.log").open("xb") as err:
        process = subprocess.Popen(command,stdout=out,stderr=err)
        try:
            code = process.wait(timeout=LIMITS["owned_child_seconds"])
        except subprocess.TimeoutExpired:
            timed_out = True
            process.kill()
            code = process.wait()
    complete_records = [reference(p) for p in sorted(directory.glob("branch-*.json"))]
    child_path = directory/"child-result.json"
    result = {"status":"CHILD_COMPLETE" if code == 0 and child_path.exists() else "UNKNOWN",
        "mode":mode,"child_exit_code":code,"hard_timeout":timed_out,
        "preparation":reference(preparation),"source_sha256":digest(Path(__file__).read_bytes()),
        "seconds":time.monotonic()-started,"records_preserved":complete_records,
        "automatic_retries":0,"case4_excluded":False}
    if child_path.exists():
        result["child_result"] = reference(child_path)
    json_write(directory/"supervisor.json",result)
    return result


def main():
    if not __debug__:
        raise RuntimeError("assertions are required")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode",choices=("controls","prepare","run","replay","_run","_replay"))
    parser.add_argument("--root",type=Path,default=ROOT)
    parser.add_argument("--preparation",type=Path)
    parser.add_argument("--directory",type=Path)
    parser.add_argument("--source-directory",type=Path)
    parser.add_argument("--output",type=Path)
    args = parser.parse_args()
    if args.mode == "controls":
        report = controls()
        report["source_sha256"] = digest(Path(__file__).read_bytes())
        report["numpy_version"] = np.__version__
        if args.output:
            json_write(args.output,report)
    elif args.mode == "prepare":
        report = prepare(args.root.resolve(),args.directory)
    elif args.mode == "run":
        report = owned("run",args.root,args.preparation,args.directory)
    elif args.mode == "replay":
        report = owned("replay",args.root,args.preparation,args.directory,args.source_directory)
    elif args.mode == "_run":
        report = child_forward(args.root,args.preparation,args.directory)
    else:
        report = child_replay(args.root,args.preparation,args.source_directory,args.directory)
    print(json.dumps({"status":report["status"],"source_sha256":report.get("source_sha256"),
        "seconds":report.get("seconds")}),flush=True)


if __name__ == "__main__":
    main()

