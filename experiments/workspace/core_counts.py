"""Exact reduction to counts of spanning subgraphs with minimum degree three.

The first column of every form is its constant. Remaining columns count
ordinary (not necessarily induced) unlabelled copies of the listed cores.
"""
import argparse
from collections import Counter
from functools import lru_cache
from itertools import combinations
from math import factorial, gcd
from pathlib import Path
from functools import reduce

import numpy as np
from pynauty import certificate

from subgraph_counts import build, identities, members, nauty


def delete_vertex(rows, x):
    keep = (1 << x) - 1
    return tuple((r & keep) | ((r >> 1) & ~keep) for i, r in enumerate(rows) if i != x)


def edge(rows, a, b, toggle=False):
    result = list(rows)
    if toggle:
        result[a] ^= 1 << b
        result[b] ^= 1 << a
    else:
        result[a] |= 1 << b
        result[b] |= 1 << a
    return tuple(result)


def reduce_counts(data, v, k):
    graphs, levels, aut, _ = data
    order = len(levels)-1
    scale = factorial(order)
    cores = [i for i, g in enumerate(graphs) if g and min(r.bit_count() for r in g) >= 3]
    coords = {g: j+1 for j, g in enumerate(cores)}
    cols = 1 + len(cores)
    ids = {(len(g), certificate(nauty(g))): i for i, g in enumerate(graphs) if g}
    @lru_cache(maxsize=200000)
    def lookup(g):
        if not g:
            return 0
        return ids.get((len(g), certificate(nauty(g))), -1)
    inj = np.zeros((len(graphs)+1, cols), dtype=object)  # the final row is the forbidden type
    inj[0,0] = 1
    induced = np.zeros((len(graphs), cols), dtype=object)
    induced[0,0] = scale
    for n, level in enumerate(levels[1:], 1):
        deletion = {}
        for i in level:
            g = graphs[i]
            if i in coords:
                inj[i, coords[i]] = aut[i]
            else:
                x = min(range(n), key=lambda a: g[a].bit_count())
                neighbors = [a-(a>x) for a in members(g[x])]
                h = delete_vertex(g, x)
                base = inj[lookup(h)]
                if not neighbors:
                    inj[i] = (v-n+1) * base
                elif len(neighbors) == 1:
                    a, = neighbors
                    inj[i] = k * base
                    for b in range(n-1):
                        if b != a:
                            inj[i] -= inj[lookup(edge(h,a,b))]
                else:
                    a, b = neighbors
                    inj[i] = 2 * base - inj[lookup(edge(h,a,b))]
                    for u in range(n-1):
                        if u != a and u != b:
                            inj[i] -= inj[lookup(edge(edge(h,a,u),b,u))]
            deletion[i] = Counter(lookup(edge(g,a,b,True)) for a,b in combinations(range(n),2) if g[a] >> b & 1)
        start = level[0]
        term = np.array([inj[i] * (scale // aut[i]) for i in level], dtype=object)
        total = term.copy()
        for r in range(1, 1 + max(sum(d.values()) for d in deletion.values())):
            nxt = np.zeros_like(term)
            for i in level:
                for h, times in deletion[i].items():
                    nxt[h-start] += times * term[i-start]
            if np.any(nxt % r):
                raise ArithmeticError('edge deletion multiplicities')
            term = nxt // r
            total += (-1 if r%2 else 1) * term
        induced[start:level[-1]+1] = total
    return cores, scale, inj[:-1], induced


def primitive(row):
    g = reduce(gcd, row, 0)
    return tuple(int(x)//g for x in row) if g else ()


def exact_conditions(data, v, k, scale, induced):
    eqs = set()
    for eq in identities(data, v, k):
        form = np.zeros(induced.shape[1], dtype=object)
        for j, value in eq.items():
            if j:
                form += value * induced[j-1]
            else:
                form[0] += value * scale
        key = primitive(form)
        if key:
            eqs.add(key)
    return sorted(eqs)


def solve(data, v, k, cores, scale, inj, induced, timeout):
    import z3
    eqs = exact_conditions(data, v, k, scale, induced)
    vs = [z3.Int('count_%d'%i) for i in cores]
    def expr(row):
        return int(row[0]) + sum(int(c)*x for c,x in zip(row[1:],vs) if c)
    s = z3.Solver()
    s.set(timeout=timeout*1000)
    feasible = {primitive(row) for row in induced}
    feasible.discard(())
    for row in feasible:
        s.add(expr(row) >= 0)
    for row in eqs:
        s.add(expr(row) == 0)
    # Divisibility of ordinary counts suffices also for induced counts since
    # the inverse edge-subset transform has integer coefficients.
    congruences = set()
    for row, modulus in zip(inj, data[2]):
        r = tuple(int(c) % modulus for c in row)
        common = reduce(gcd, r, modulus)
        modulus //= common
        if modulus > 1:
            congruences.add((tuple(c//common for c in r), modulus))
    for r, modulus in sorted(congruences):
        s.add(expr(r) % modulus == 0)
    print('core variables', len(vs), 'nonnegative forms',len(feasible),'nonzero equalities',len(eqs),'congruences',len(congruences),flush=True)
    status = s.check()
    print('integer system', status,flush=True)
    if status == z3.sat:
        x = np.array([1]+[s.model().eval(var, model_completion=True).as_long() for var in vs], dtype=object)
        raw = induced @ x
        assert all(c % scale == 0 and c >= 0 for c in raw)
        totals = raw // scale
        original = 0
        for eq in identities(data, v, k):
            assert sum(value * (totals[j-1] if j else 1) for j,value in eq.items()) == 0
            original += 1
        print('exact witness checked against',original,'integer equations; core counts',list(x[1:]),flush=True)
    if status == z3.unknown:
        print(s.reason_unknown(),flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('order', type=int)
    p.add_argument('--parameters',nargs=2,type=int,default=[99,14])
    p.add_argument('--seconds',type=int,default=90)
    a = p.parse_args()
    data = build(a.order)
    info = reduce_counts(data,*a.parameters)
    solve(data,*a.parameters,*info,a.seconds)
