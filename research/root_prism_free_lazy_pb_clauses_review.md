# Exact clauses from proved Boolean inequalities

The proposed clause extraction is sound. It can replace eager encodings of
the registered inequalities in a lazy separation loop. Every emitted clause
needs its own exact arithmetic derivation. A solver proof of the final CNF
does not replace that derivation.

This note reviews the mathematics and loop obligations. It does not review
an implementation or report a solver run.

## One inequality without a cardinality premise

Let $z\in\{0,1\}^N$ and let the certified inequality be

\[
\sum_{i=1}^N a_i z_i\leq b.
\]

Coefficients must be exact integers or rationals. Combine repeated variable
coefficients before extraction. Suppose a complete assignment $z^*$ violates
the inequality. For a set $F$ of fixed coordinates, define

\[
\ell(F)=\sum_{i\in F}a_i z_i^*
       +\sum_{i\notin F}\min(0,a_i).
\]

This is the exact minimum over all Boolean assignments agreeing with $z^*$
on $F$. Therefore $\ell(F)>b$ implies the clause

\[
\bigvee_{\substack{i\in F\\z_i^*=0}}z_i
\ \vee\
\bigvee_{\substack{i\in F\\z_i^*=1}}\neg z_i.
\]

Every assignment falsifying this clause agrees on $F$ and violates the
inequality. The clause is false at the current assignment, so adding it
eliminates that complete primary assignment and every auxiliary extension.
The strict inequality matters: equality with $b$ is allowed and cannot
justify a clause.

Start with every nonzero coefficient fixed. The lower bound then equals
the violating value. Releasing coordinates while retaining $\ell(F)>b$
is safe. One pass through the coordinates gives an inclusion-minimal fixed
set: a release rejected earlier cannot become valid after further releases,
because the minimum can only decrease.

A simpler equivalent formula is

\[
m=\sum_i\min(0,a_i),\qquad
\delta_i=a_i z_i^*-\min(0,a_i)\geq0,\qquad
\ell(F)=m+\sum_{i\in F}\delta_i.
\]

Zero-cost coordinates can always be released. Releasing in increasing order
of $\delta_i$ gives a minimum-cardinality clause among clauses obtained from
this single inequality and the fixed values of $z^*$. Equivalently, retain
the largest $\delta_i$ until their sum exceeds $b-m$. Arbitrary release
orders need only give inclusion-minimal clauses. For example, costs
$6,6,11$ with required sum greater than $10$ can leave two coordinates,
although retaining the coordinate of cost $11$ suffices.

## Guarded row inequality

For

\[
\sum_j w_jz_j\geq d z_a,\qquad w_j\geq0,\quad d>0,
\]

use $a_a=d$, $a_j=-w_j$, and $b=0$, combining coefficients if an index
occurs on both sides. In the usual distinct-neighbor case, a violating
assignment has $z_a^*=1$.

Without a cardinality premise, every deletion-minimal extracted clause
keeps the guard and only fixes absent neighbors. It has the form

\[
\neg z_a\ \vee\ \bigvee_{j\in C}z_j,
\]

where the exact test is $\sum_{j\notin C}w_j<d$. Selected neighbors have
zero deletion cost and do not remain in a minimal clause.

## An explicit exact-cardinality premise

Now also assume the independently established equation

\[
\sum_{i=1}^N z_i=K.
\]

For fixed coordinates $F$, let $s=\sum_{i\in F}z_i^*$ and $r=K-s$.
If $0\leq r\leq N-|F|$, sort the coefficients of **all** free variables:

\[
c_1\leq c_2\leq\cdots\leq c_{N-|F|}.
\]

The exact minimum with the cardinality premise is

\[
\ell_K(F)=\sum_{i\in F}a_i z_i^*+\sum_{j=1}^{r}c_j.
\]

This follows by choosing exactly $r$ free variables to equal one. An exchange
of a larger selected coefficient for a smaller unselected coefficient
cannot increase the objective. Hence $\ell_K(F)>b$ proves the same clause,
now from the inequality together with the cardinality equation.

Free variables with zero coefficients must be included. For example,
$a=(1,0)$, $K=1$, and $b=0$ admit $(0,1)$. Omitting the zero coefficient
would incorrectly make the minimum equal one and derive an empty clause.

If $r<0$ or $r>N-|F|$, the fixed values already contradict the cardinality
premise. A clause can then be justified from cardinality alone, with that
different reason recorded. This case cannot arise when $F$ only fixes
coordinates of a verified assignment of cardinality $K$.

Starting with all $K$ positive coordinates of $z^*$ gives $r=0$ and
$\ell_K(F)=a\cdot z^*>b$. Thus a valid initial clause has at most $K$
literals, even when the inequality has a much larger support. Greedy
deletion preserves validity. The same monotonicity argument proves
one-pass inclusion-minimality. It does not prove minimum clause width
under the cardinality premise.

## Why the F0 model has cardinality 60

The complete F0 signature domain has 480 signatures, each containing three
core vertices. Its 18 diagonal Gram margins are all ten. The exact diagonal
equations are

\[
\sum_{a:i\in h_a}z_a=10,\qquad 0\leq i<18.
\]

Summing them gives

\[
3\sum_{a=0}^{479}z_a=18\cdot10=180,
\qquad \sum_a z_a=60.
\]

The premise follows from the equations, not from the cardinalities of saved
solver candidates. The frozen base builder
`experiments/workspace/root_prism_free_f0_incidence.py` includes every diagonal
Gram equation. Duplicate identical equations can share an encoding without
changing this conclusion.

The independent read of
`experiments/logs/root-prism-free/f0-exterior-row-domains02.json.gz` confirmed
all 480 signature sizes and all 18 diagonal values. Its SHA-256 is
`665563b75fa6fc23caa9a002621cc4047809af28543b52b5c2a7ffa592d05dd4`.

## Lazy-loop coverage and termination

A model returned by the base CNF need not satisfy registered inequalities
that have not been fully encoded. Check the original incidence conditions
first, then evaluate every registered inequality exactly. If any fails,
derive a clause false at that assignment and append it before the next
query. Only a point satisfying the entire current inequality registry
should reach the existing row or shared-edge separation stage.

Every accepted clause is a necessary condition and removes the current
primary assignment. An identical primary assignment cannot return with
different auxiliary values. Without resource limits, this mechanism can
exclude at most $2^N$ distinct primary assignments, or $\binom{N}{K}$ under
the cardinality premise. This is a finite termination argument, not a
practical runtime bound.

A final assignment satisfying the CNF and every registered inequality
certifies feasibility of that finite necessary-condition model only. It
does not construct a graph. A timeout, resource stop, or unresolved row
query remains unresolved.

The derived clauses can be weaker than a full CNF encoding of all
inequalities. This affects search speed and finite-run completeness, not
soundness. An UNSAT proof of a necessary-condition subset is still useful
once every input clause is justified.

## Certificate and replay obligations

Each clause record should bind the following data:

1. The exact inequality and its earlier mathematical certificate, including
   the transport or potential that proves it.
2. The full primary universe, the violated candidate, and the fixed values
   retained in $F$.
3. The cardinality premise and its derivation when used.
4. The exact minimum, strict positive excess over $b$, and output literals.
5. The clause's position in the incremental formula and its normalized
   duplicate key.

Replay can recompute the minimum directly from the retained fixed values.
It need not trust or reproduce the greedy choices. Minimality is optional;
the strict bound and literal correspondence are the proof.

Candidate-prefix replay must distinguish the encoded clause prefix from
the full PB registry. An intermediate candidate may violate the latter:
that is the intended separation event. It must satisfy the former. The
next recorded clause must be false at that candidate and follow from its
recorded exact inequality and optional cardinality premise.

For a claimed exclusion, rebuild the final necessary CNF, verify every
arithmetic clause derivation, run a fresh proof-enabled query, and check
the resulting proof and retained-input inclusion. The arithmetic clauses
are certified premises of that CNF. They need not follow from the earlier
CNF alone. No hypothetical graph symmetry or fixed incidence assignment
is introduced by this procedure.
