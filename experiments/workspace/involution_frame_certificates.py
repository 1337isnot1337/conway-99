"""Encode and independently certify the single- and two-row frame obstructions."""

from itertools import combinations
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory

from pysat.card import CardEnc, EncType
from pysat.formula import CNF, IDPool


def row_cnf(rows, selected):
    labels = [pair for pair in combinations(range(7), 2) for _ in range(2)]
    h = [[1 if a in label else 2*((raised >> a) & 1) for a in range(6)]
         for raised, label in zip(rows, labels)]
    pool = IDPool()
    formula = CNF()

    def edge(kind, i, j):
        return pool.id((kind, min(i, j), max(i, j)))

    def equals(literals, target):
        if not 0 <= target <= len(literals):
            formula.append([])
        else:
            formula.extend(CardEnc.equals(literals, target, vpool=pool,
                                          encoding=EncType.seqcounter))

    def product(x, y):
        z = pool.id()
        formula.extend([[-z, x], [-z, y], [z, -x, -y]])
        return z

    for i in selected:
        other = [j for j in range(42) if i != j]
        single = [edge('present', i, j) for j in other]
        double = [edge('double', i, j) for j in other]
        entries = list(zip(other, single, double))
        for _, x, y in entries:
            formula.append([x, -y])
        equals(single, 11)
        equals(double, 1)
        for a in range(7):
            equals([v for j, x, y in entries if a in labels[j] for v in (x, y)],
                   4-2*(a in labels[i]))
        for a in range(1, 6):
            literals = []
            target = -4*(h[i][a]-h[i][0])
            for j, x, y in entries:
                weight = h[j][a]-h[j][0]
                if weight < 0:
                    target -= 2*weight
                literals.extend(([x, y] if weight >= 0 else [-x, -y])*abs(weight))
            equals(literals, target)

    for i, j in combinations(selected, 2):
        terms = [edge('present', i, j), edge('double', i, j)]
        for k in range(42):
            if k in (i, j):
                continue
            x, y = edge('present', i, k), edge('double', i, k)
            u, v = edge('present', j, k), edge('double', j, k)
            formula.append([-y, -v])
            terms.extend([product(x, u), product(x, v), product(y, u)])
        equals(terms, 4-len(set(labels[i]) & set(labels[j])))
    return formula


def certify(rows, selected, cadical, drat_trim):
    with TemporaryDirectory() as directory:
        cnf = Path(directory)/'rows.cnf'
        proof = Path(directory)/'rows.drat'
        row_cnf(rows, selected).to_file(cnf)
        result = subprocess.run([cadical, cnf, proof], capture_output=True)
        if result.returncode != 20:
            raise RuntimeError(f"CaDiCaL did not prove infeasibility for rows {selected}")
        checked = subprocess.run([drat_trim, cnf, proof], capture_output=True, check=True)
        if b's VERIFIED' not in checked.stdout:
            raise RuntimeError(f"drat-trim did not verify the proof for rows {selected}")
