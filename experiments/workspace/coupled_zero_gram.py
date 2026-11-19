"""Exact negative quadratic witnesses on saved 35-point norm-16 cores.

Floating point eigenvectors propose integer vectors.  Only a strictly
negative integer quadratic evaluation is accepted as a certificate.
The certificate excludes the supplied H/Z point, not its whole template.
"""
from __future__ import annotations

import argparse
from itertools import combinations
import json
from math import gcd
from pathlib import Path

import numpy as np

from coupled_zero_completion import matrices


def gram(B):
    return 12*np.eye(len(B), dtype=int)+2*np.ones(B.shape, dtype=int)-B-B@B


def negative_vector(G):
    values, vectors = np.linalg.eigh(G)
    if values[0] >= -1e-7:
        return None
    for scale in range(1, 1001):
        v = np.rint(scale*vectors[:, 0]).astype(int)
        if int(v @ G @ v) < 0:
            break
    else:
        raise RuntimeError('No exact negative integer vector found')
    # Reduce integer support and coefficients while retaining a negative value.
    changed = True
    while changed:
        changed = False
        for i in sorted(range(len(v)), key=lambda i: abs(int(v[i])), reverse=True):
            if not v[i]:
                continue
            w = v.copy(); w[i] -= np.sign(w[i])
            if int(w @ G @ w) < 0:
                v = w; changed = True
    return [int(x) for x in v]


def linear_cut(B, vector):
    """Necessary tangent inequality on the 171 variable H/Z core edges.

    For q=B0*v, positivity of 12I+2J-B-B² implies
      v'Bv + 2q'Bv <= 12v'v + 2(sum v)² + q'q.
    Here B0 is this supplied point; the inequality holds for every B
    with the same fixed P/N/H incidence and arbitrary H/Z edges.
    """
    v = np.array(vector, dtype=np.int64); q = B@v
    bound = int(12*(v@v)+2*v.sum()**2+q@q)
    terms = []
    for i, j in combinations(range(35), 2):
        coefficient = int(2*(v[i]*v[j]+q[i]*v[j]+q[j]*v[i]))
        if i >= 16:
            if coefficient:
                terms.append([i-16, j-16, coefficient])
        else:
            bound -= coefficient*int(B[i, j])
    divisor = 0
    for _, _, coefficient in terms:
        divisor = gcd(divisor, abs(coefficient))
    if divisor > 1:
        terms = [[i, j, c//divisor] for i, j, c in terms]
        bound //= divisor
    value = sum(c*int(B[i+16, j+16]) for i, j, c in terms)
    assert value > bound
    return {'coefficients': terms, 'upper_bound': bound,
            'excluded_point_value': value}


def data(orbits, points):
    blocks = {b['core']: b for b in json.loads(orbits.read_text())}
    points = {(r['core'], r['orbit']): r
              for r in json.loads(points.read_text()) if r['status'] == 'sat'}
    return blocks, points


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--orbits', type=Path,
                   default=Path('experiments/logs/eigenlattices/coupled-shells-orbits.json'))
    p.add_argument('--points', type=Path,
                   default=Path('experiments/logs/eigenlattices/coupled-shells-low-all.json'))
    p.add_argument('--output', type=Path,
                   default=Path('experiments/logs/eigenlattices/coupled-zero-gram-certificates.json'))
    p.add_argument('--verify', action='store_true')
    a = p.parse_args(); blocks, points = data(a.orbits, a.points)
    certificates = []
    if not a.verify:
        for (core, orbit), r in points.items():
            b = blocks[core]; B, _ = matrices(b, b['orbits'][orbit], r)
            G = gram(B); v = negative_vector(G)
            if v is None:
                continue
            value = int(np.array(v)@G@np.array(v))
            cut = linear_cut(B, v)
            certificates.append({'core': core, 'orbit': orbit, 'vector': v,
                                 'quadratic_value': value,
                                 'linear_cut_summary': {
                                     'upper_bound': cut['upper_bound'],
                                     'excluded_point_value': cut['excluded_point_value'],
                                     'nonzero_coefficients': len(cut['coefficients'])}})
        a.output.write_text(json.dumps(certificates, indent=2)+'\n')
    certificates = json.loads(a.output.read_text())
    for r in certificates:
        key = r['core'], r['orbit']; b = blocks[r['core']]
        B, _ = matrices(b, b['orbits'][r['orbit']], points[key]); G = gram(B)
        v = r['vector']; assert len(v) == 35 and all(type(x) is int for x in v)
        # Use Python integers for the certificate arithmetic.
        value = sum(v[i]*int(G[i, j])*v[j] for i in range(35) for j in range(35))
        assert value == r['quadratic_value'] < 0
        cut = linear_cut(B, v)
        assert r['linear_cut_summary'] == {
            'upper_bound': cut['upper_bound'],
            'excluded_point_value': cut['excluded_point_value'],
            'nonzero_coefficients': len(cut['coefficients'])}
    print('PASS:', len(certificates), 'exact negative quadratic certificates.')
    print('Scope: fixed H/Z partial points only; no incidence template excluded.')
    print('Other saved points:', len(points)-len(certificates),
          '(no negative certificate recorded; no PSD assertion made).')


if __name__ == '__main__':
    main()
