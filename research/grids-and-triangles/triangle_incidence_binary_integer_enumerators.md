# Two formal binary enumerators and their failed graph conditions

The [rank-88 proof](triangle_incidence_binary_chain_code.md) bounds the
dimension of C=ker_F2(B^T) by eleven. Two bounded integer queries tested
whether the existing weight-enumerator conditions alone ruled out dimension
eleven. They do not. Neither query constructs a code, and additional graph
conditions reject both saved formal enumerators.

## Exact scope

Both queries fix |C|=2048 and allow only the nonzero weights
36,40,44,48,52,56,60. Fifty distinct congruences retain all 99 MacWilliams
divisibility conditions modulo 2048. Numerical optimization uses the first
ten nonnegativity/forced-count inequalities only. Acceptance checks every
one of the 100 dual counts with exact integers, including its nonnegativity,
the previously proved forced words, the dual total 2^88, and the necessary
coefficientwise inclusion of a self-orthogonal code in its dual.

The exact transform uses a Krawtchouk recurrence. Preparation compares it
with the binomial formula and literal dual enumeration on the [7,3,4] and
[15,4,8] simplex codes and RM(1,3). Numerical infeasibility is never accepted
as an exclusion.

## First formal point

The first query finished in 1.123 seconds. It produced:

| Nonzero weight | 36 | 40 | 44 | 48 | 52 | 56 | 60 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Formal count A_w | 627 | 1330 | 1 | 21 | 1 | 0 | 67 |

All listed acceptance conditions pass exactly. However, its dual has
B_1=20 and B_2=189. A weight-one dual word identifies an identically zero
code coordinate. Twenty such coordinates force at least binom(20,2)=190
weight-two dual words. Thus this formal point cannot be the enumerator of
any binary linear code. The failed condition is recorded; the numerical
and exact transform records are preserved.

## Second formal point

A separate source adds B_1=0. This is a search for a possible formal point
with no zero coordinate, not an assumption imposed on all hypothetical
graphs. Its one query finished in 2.369 seconds:

| Nonzero weight | 36 | 40 | 44 | 48 | 52 | 56 | 60 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Formal count A_w | 475 | 0 | 597 | 1 | 1 | 118 | 855 |

Its exact first dual counts are B_1=0, B_2=152 and B_3=239. The elementary
zero-coordinate condition now passes. The later
[triangle-replacement theorem](triangle_incidence_binary_toggle_code.md)
requires B_3>=231+7(B_2-B_1)=1295, so this point cannot arise from the
triangle incidence kernel of the target graph. The same theorem rejects
the first formal point as well.

Both cold replays pass their original, explicitly limited acceptance
conditions. These results do not establish that dimension eleven is
possible after the new triangle constraints. They identify why ordinary
weight-enumerator checks were insufficient.

## Files

The sources are `triangle_incidence_binary_integer_enumerator.py` and
`triangle_incidence_binary_full_support_enumerator.py`. Their preparation,
query and replay records use the corresponding prefixes under
`experiments/logs/grids-and-triangles/`. Both query records retain all 100
exact dual coefficients and every numerical proposal coordinate.
