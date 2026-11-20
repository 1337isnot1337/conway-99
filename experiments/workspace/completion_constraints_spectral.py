"""Exactly verified pair exclusions for exterior signatures at an SRG core.

Floating spectral calculations only locate possible cuts. Every returned cut
is checked again using integer Schur-complement determinants.
"""
from fractions import Fraction
from math import gcd, isqrt
import numpy as np
from sympy import Matrix
from sympy.polys.matrices import DomainMatrix


def gram_parameters(k, v):
    root = isqrt(4 * k - 7)
    assert root * root == 4 * k - 7
    r = (root - 1) // 2
    s = -1 - r
    for diagonal, edge, constant in ((r, -1, Fraction(k - r, v)), (-s, 1, Fraction(-(k - s), v))):
        d = constant.denominator
        yield diagonal * d, edge * d, constant.numerator


def exact_data(B, incidence, parameters):
    diagonal, edge, constant = parameters
    G = Matrix((diagonal * np.eye(len(B), dtype=int) + edge * B + constant).tolist())
    pivots = G.rref()[1]
    H = G.extract(pivots, pivots)
    _, D = H.LDLdecomposition(hermitian=False)
    assert all(D[i, i] > 0 for i in range(len(pivots)))
    numerator, denominator = DomainMatrix.from_Matrix(H).inv_den()
    num = np.array(numerator.to_Matrix().tolist(), dtype=object)
    den = int(denominator)
    common = abs(den)
    for x in num.ravel():
        common = gcd(common, abs(int(x)))
    num //= common
    den //= common
    if den < 0:
        den = -den
        num = -num
    q = (edge * incidence[:, list(pivots)] + constant).astype(object)
    product = q @ num
    residual = np.array([(diagonal + constant) * den - sum(int(a) * int(b) for a, b in zip(x, y)) for x, y in zip(product, q)], dtype=object)
    assert all(x >= 0 for x in residual)
    return edge, constant, den, q, product, residual


def pair_exclusions(B, domains, k=14, v=99):
    N = np.array([[int(i in S) for i in range(len(B))] for S in domains], dtype=np.int16)
    count = len(domains)
    intersection = N @ N.T
    keep = [np.ones((count, count), dtype=bool), intersection <= 1]
    need = 2 - N @ (B + np.eye(len(B), dtype=int))
    assert np.min(need) >= 0
    forbidden_near = (need == 0).astype(np.int16) @ N.T
    keep[1] &= (forbidden_near == 0) & (forbidden_near.T == 0)
    parameters = list(gram_parameters(k, v))
    for diagonal, edge, constant in parameters:
        G = diagonal * np.eye(len(B)) + edge * B + constant
        eigenvalues, vectors = np.linalg.eigh(G)
        active = eigenvalues > 1e-7
        F = ((edge * N + constant) @ vectors[:, active]) / np.sqrt(eigenvalues[active])
        residual = diagonal + constant - np.sum(F * F, axis=1)
        for start in range(0, count, 256):
            end = min(start + 256, count)
            product = F[start:end] @ F.T
            rhs = residual[start:end, None] * residual[None, :]
            for adjacency in (0, 1):
                lhs = (edge * adjacency + constant - product) ** 2
                keep[adjacency][start:end] &= lhs <= rhs + 1e-7
    candidates = np.transpose(np.nonzero(np.triu((intersection <= 2) & ~(keep[0] | keep[1]), 1)))
    data = [exact_data(B, N, p) for p in parameters]
    result = []
    for i, j in candidates:
        valid = False
        for adjacency in (0, 1):
            if adjacency and (intersection[i, j] >= 2 or forbidden_near[i, j] or forbidden_near[j, i]):
                continue
            ruled_out = False
            for edge, constant, den, q, product, residual in data:
                inner = sum(int(a) * int(b) for a, b in zip(product[i], q[j]))
                cross = (edge * adjacency + constant) * den - inner
                if cross * cross > int(residual[i]) * int(residual[j]):
                    ruled_out = True
                    break
            if not ruled_out:
                valid = True
                break
        if not valid:
            result.append((int(i), int(j)))
    return result
