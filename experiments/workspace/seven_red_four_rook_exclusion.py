"""Exact algebraic audit of the seven-red/four-rook remainder contradiction."""

import argparse
from collections import Counter
from itertools import permutations, product
import json
from pathlib import Path

import sympy as sp


def run(output=None):
    r,p,x,t = sp.symbols('r p x t')
    s1 = 7*p-56+3*r
    s2 = 12*r-112-s1
    s3 = 104-s2+12*s1
    polynomial = (x+4)*(x+1)**2
    assert sp.expand(polynomial) == x**3+6*x**2+9*x+4
    # With t=x+4>=0 this is visibly nonnegative.
    assert sp.expand(polynomial.subs(x,t-4)-t*(t-3)**2) == 0
    polynomial_trace = sp.expand(s3+6*s2+9*s1+4*r)
    assert polynomial_trace == 112*(p+r)-1352
    compression_slack = sp.expand(32-4*r-s1)
    assert compression_slack == 88-7*(p+r)
    maximum_integer_sum = 88//7
    maximum_trace = 112*maximum_integer_sum-1352
    assert maximum_integer_sum == 12 and maximum_trace == -8
    b, cross_triangles = 7,39
    h_trace = -8*b
    h_square = 4*b*(b+3)
    h_cube = -32*b-24*b*(b-1)+b*(b-1)*(b-2)+2*cross_triangles
    assert (h_trace,h_square,h_cube) == (-56,280,-944)
    assert h_cube == -840-104
    points = list(product(range(3),repeat=2))
    rook = [[int(i != j and (a == c or b == d)) for j,(c,d) in enumerate(points)]
            for i,(a,b) in enumerate(points)]
    E9 = [[3*int(i == j)-3*rook[i][j]+1 for j in range(9)] for i in range(9)]
    allowed = set()
    for sigma,tau,swap in product(permutations(range(3)),permutations(range(3)),(False,True)):
        permutation = tuple(3*sigma[b if swap else a]+tau[a if swap else b] for a,b in points)
        if any(rook[i][permutation[i]] for i in range(9)):
            continue
        fixed = sum(i == permutation[i] for i in range(9))
        character9 = sum(E9[permutation[i]][i] for i in range(9))
        assert character9 == 3*fixed+9 and character9 % 9 == 0
        allowed.add((permutation,fixed,character9//9))
    assert len(allowed) == 11
    result = {'red_bases': 7, 'u_rook_grids': 4,
              'red_negative_space_dimension': 28,
              'red_block_traces': [h_trace,h_square,h_cube],
              'energy': 112, 'cubic_value': 104,
              'compression_slack': str(compression_slack),
              'nonnegative_polynomial': str(sp.expand(polynomial)),
              'nonnegative_factorization_after_shift': 't*(t-3)^2, t=x+4>=0',
              'polynomial_trace': str(polynomial_trace),
              'maximum_integer_p_plus_r': maximum_integer_sum,
              'maximum_polynomial_trace': maximum_trace,
              'allowed_holonomies_checked': len(allowed),
              'negative_character_histogram': dict(sorted(Counter(row[2] for row in allowed).items())),
              'contradiction_verified': True}
    if output:
        Path(output).parent.mkdir(parents=True,exist_ok=True)
        Path(output).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result),flush=True)


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--output')
    args=parser.parse_args()
    run(args.output)
