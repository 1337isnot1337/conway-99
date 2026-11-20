# Bounded completion searches with the zero forest fixed

The doubled-edge support core has two surviving incidence classes,
numbered one and two in the archived core-zero catalog. The
[structural restriction](coupled_zero_completion.md#a-stronger-forest-restriction-for-the-doubled-edge-support-core)
makes `H` independent and leaves three possible graphs on `Z`:

1. `5K2 + K1`;
2. `3K2 + P3 + 2K1`;
3. `K2 + 2P3 + 3K1`.

All six class/forest combinations were tested with a sixty-second
solver limit. Every run returned **UNKNOWN**. No completion or UNSAT
certificate was obtained, and the 447 surviving incidence classes
remain unchanged.

## A separate builder without the old zero ordering

`coupled_zero_fixed_forest.py` fixes `H` to be independent and fixes
only the chosen induced graph on the eleven zero vertices. It leaves
all 88 high/zero, 512 high/low, and 704 zero/low incidences free.

The frozen earlier builder orders zero vertices by their high
neighborhoods. Combining that ordering with an arbitrary canonical
zero forest would not be justified. The new builder does not import
that constraint. Any zero forest of the chosen type can be labeled
as the fixed representative, and all resulting high/zero incidences
remain available.

Let `B` be the variable thirty-five-point core adjacency and `N` its
incidence to the sixty-four low vertices. The new model imposes:

\[
B^2+NN^T+B=12I+2J,
\]

complete degree fourteen at every core vertex, the visible mixed-pair
bound `(B+I)N≤2J`, and off-diagonal bounds `(NᵀN)_{lm}≤2`. It also
includes the forced partition degrees, in particular `d_Z(l)-d_H(l)=1`.
All edges within the low class remain unchosen.

Low vertices with identical positive/negative support signatures are
interchangeable. Only their nineteen-bit high/zero incidence columns
are ordered. This symmetry condition preserves the fixed zero graph.
An independent read-only audit checked the equations, Boolean encoding,
indexing, and this symmetry argument without finding an unsound
restriction.

A SAT output would be checked directly on all thirty-five core degrees
and pair equations and on every visible partial common-neighbor bound.
The program saves and independently checks a DRAT proof before reporting
a verified UNSAT result. Neither outcome occurred in these six runs.

## Results

The forest index in filenames is zero-based.

| Incidence class | Forest index | Graph on Z | Variables | Clauses | Result |
| ---: | ---: | --- | ---: | ---: | --- |
| 1 | 0 | `5K2 + K1` | 237,455 | 577,141 | UNKNOWN |
| 1 | 1 | `3K2 + P3 + 2K1` | 237,238 | 576,778 | UNKNOWN |
| 1 | 2 | `K2 + 2P3 + 3K1` | 237,021 | 576,415 | UNKNOWN |
| 2 | 0 | `5K2 + K1` | 237,455 | 577,141 | UNKNOWN |
| 2 | 1 | `3K2 + P3 + 2K1` | 237,238 | 576,778 | UNKNOWN |
| 2 | 2 | `K2 + 2P3 + 3K1` | 237,021 | 576,415 | UNKNOWN |

Build times ranged from 1.23 to 2.11 seconds. The recorded solver
intervals include initialization and ranged from 60.51 to 60.78 seconds;
each solve had a sixty-second interruption timer. The runs were made
sequentially. A temporary execution-service delay did not change the
first run's recorded limit or result.

The six JSON records and six text logs are
`experiments/logs/eigenlattices/coupled-zero-fixed-forest-{1,2}-{0,1,2}.json`
and the corresponding `.log` files.

For example, reproduce the first instance with:

```bash
.venv/bin/python experiments/workspace/coupled_zero_fixed_forest.py \
  --orbit 1 --forest 0 --seconds 60 \
  --output /tmp/coupled-zero-fixed-forest-1-0.json
```

A timeout supplies no feasibility or infeasibility information. This
checkpoint records the model and the unresolved finite instances; it
does not change any proved template count.
