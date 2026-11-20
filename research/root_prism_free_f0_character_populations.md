# Signed population constraints for F0

The 12 checked core relabelings have four real one-dimensional characters.
The trivial character gives the existing orbit-population products. The
three nontrivial characters give 118 signed population variables and 2,385
further product identities. Complete local subset enumeration gives 19,331
joint count and signed-population tuples. Both constructions have exact
cold replays and a separate source and mathematical review.

These are necessary conditions for one hypothetical incidence in the fixed
component-zero F0 branch. No graph automorphism is assumed. They are not
conditions on every convex mixture of incidences, and no feasibility or
nonexistence conclusion follows from preparation alone.

## Orbit signings

Let G be the checked group of 12 relabelings. A real sign character is a map
chi from G to {1,-1} with chi(gh)=chi(g)chi(h). The construction exhausts
all 2,048 maps with value one at the identity. Exactly four are characters.

Fix a selector orbit O_i and an anchor a_i. A signing w_i on O_i with

    w_i(g a) = chi(g) w_i(a),     w_i(a_i)=1

exists precisely when chi is one on the stabilizer of a_i. If this holds,
define w_i(g a_i)=chi(g). The stabilizer condition makes the definition
independent of the chosen g. The checker verifies this transformation law
for every action and every member of every compatible orbit.

The three nontrivial characters support 38, 42 and 38 selector orbits,
respectively. The four size-six orbits, with IDs 18, 23, 27 and 29, are
incompatible with the first and third characters. Every size-twelve orbit
has trivial stabilizer and supports all four characters.

For a Boolean incidence z, define

    L_chi,i = sum(w_i(a) z_a for a in O_i).

Each L is an integer. Its parity equals N_i, and

    |L_chi,i| <= min(N_i, |O_i|-N_i).

For a nontrivial character the signs are balanced. Thus the raw bounds are
-6 through 6 for 114 of the signed populations and -3 through 3 for four.
The exact local tables can impose smaller or disconnected domains.

## Why the second-moment block has rank at most one

Relabeling the incidence by g multiplies every L for the same character
by chi(g). Consequently the product of two such signed populations is
unchanged. If the original pair-orbit population is P_R, expansion gives

    L_chi,i L_chi,j = sum(s_chi,R P_R),           i != j,
    L_chi,i^2      = N_i + 2 sum(s_chi,R P_R),  i == j,

where the sum runs over pair orbits with the specified selector-orbit
endpoints. The sign s_chi,R is w_i(a)w_j(b) for a representative pair.
It is constant on the whole pair orbit because chi(g)^2=1.

The construction checks that constancy for all 322,440 relevant literal
pair occurrences across the three characters. It removes only the 389
already proved-zero pair populations. The 2,385 equations have 26,313
retained count terms. The factor two occurs only in a square expansion;
cross-orbit products count each unordered pair once.

Equivalently, the matrix of these character moments is L_chi L_chi^T.
It is positive semidefinite and has rank at most one. The existing finite
PSD directions did not explicitly enforce this product representation.
No claim of independence from every other retained condition is made.

This argument averages relabelings of one incidence. Averaging several
different incidences instead can give a matrix of larger rank. Such a
mixture does not justify replacing the deterministic products by products
of average signed populations.

## Joint local tables

The original 42 local tables record each permitted subset's ordinary
population and within-orbit pair populations. The refined tables append
all compatible signed populations of the same subset. They enumerate the
same 155,904 subsets, retaining the same 64,144 literal subsets.

There are 19,331 distinct refined tuples. Projecting them back gives all
5,733 original tuples, with their original multiplicities and minimum
representative masks. The independent review checks this projection from
the saved records without importing the construction source. Every signed
square identity is also checked on every refined tuple.

All signed coordinates in a row come from one literal subset. Treating
the three characters as independent local sign choices would lose this
condition. A table row still need not extend to a compatible selection in
the other orbits or to an exterior graph.

## Explicit signed Gram equations

A separate construction projects all 172 original Gram and population
equations through each nontrivial character. For an original support S,
the coefficient of L_chi,i before primitive normalization is

    (12/|O_i|) * sum(w_i(a) for a in O_i intersect S).

To prove the equation directly, sum the twelve transported original rows
with coefficients chi(g). Each transport has the same quota; their
weighted right-hand side is zero. The resulting literal row agrees with
the displayed signed-population expansion at all 480 coordinates.

All 516 combinations are checked, for 247,680 literal coefficient
comparisons. Primitive normalization leaves 32 homogeneous equations with
377 terms. Each retained row stores an original-row integer combination
and the signed divisor used for normalization.

| Character | Signed populations | Distinct equations | Exact rational rank |
| --- | --- | --- | --- |
| 1 | 38 | 10 | 9 |
| 2 | 42 | 11 | 9 |
| 3 | 38 | 11 | 10 |

These equations are explicit propagation rows. The complete original
selector-multiplied Gram equations imply that the square of each such
homogeneous linear form is zero. The character product representation
turns that quadratic identity into the square of the signed-population
form. Its square being zero forces the linear form itself to be zero.
The explicit rows expose this implication directly to the solver; they
are not claimed as an independent increase in mathematical strength.

## Frozen records

- [Character and profile source](../experiments/workspace/root_prism_free_f0_character_populations.py),
  SHA256 `7b1759441b1d88b2d68e03d66b1f16a13be8a6cee3eefb35e2610aa107e42295`.
- [Product and joint table record](../experiments/logs/root-prism-free/f0-character-populations01.json.gz),
  SHA256 `139d06a3383f8fc79d677972ce052ce29966e8b3406e7d1e7d1077aea7c2cef6`.
- [Complete cold replay](../experiments/logs/root-prism-free/f0-character-populations01-cold.json),
  SHA256 `1fdc14c0bda54f0b5e63b23a3b7d5f85d9afd92ea418b4931d53b644444e814b`.
- [Independent product/profile review](../experiments/logs/root-prism-free/f0-character-populations-literature-review.json),
  SHA256 `f5164ac7a59cd75c9fdd3c74364e772701038c9c8347c15ae9b6c7990c110149`.
- [Original-Gram combination source](../experiments/workspace/root_prism_free_f0_character_gram.py),
  SHA256 `5de0969699b445286b437deec69fb31cfcdab22400c6fbfa959b488117808c8b`.
- [Primitive Gram equations](../experiments/logs/root-prism-free/f0-character-Gram-equalities01.json),
  SHA256 `084764b528f9a75269c8e21bb0b55b480a552022b024db72a4357aca083770c7`.
- [Gram combination cold replay](../experiments/logs/root-prism-free/f0-character-Gram-equalities01-cold.json),
  SHA256 `482ccc5f26d4668ef1f45fab6200eeb2328b92e0b949b7e026052c1354cd1f7f`.
- [Independent Gram certificate review](../experiments/logs/root-prism-free/f0-character-Gram-literature-review.json),
  SHA256 `3e5c3b3e834f3f33f2043397d168a36e94e6355a45c38a57e5065547e0abdddb`.

The character and profile preparation took 8.50 seconds; its cold replay
took 3.44 seconds. The Gram construction and cold replay took 15.92 and
3.12 seconds. No optimizer, incidence search or eigenvalue calculation
ran in these preparations.
