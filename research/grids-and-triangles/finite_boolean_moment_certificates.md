# Exact certificates on finite Boolean domains

This helper converts integer polynomial candidates into exact inequalities on a supplied finite domain.
It does not construct the domain or prove that a graph must belong to it.
It does not call an optimizer.

The implementation is
[`finite_boolean_moment_certificates.py`](../../experiments/workspace/finite_boolean_moment_certificates.py).
The corrected source hash is
`cdc37c56d4e379fc3774a832d942fb4cfb2eb787746bfdd3f9071880e791ee1e`.

## Domain and moments

Let $\Omega$ be a finite set of subsets of a fixed Boolean variable set.
An atom $S\in\Omega$ specifies the variables with value one.
For a subset $T$, write

\[
X_T(S)=\mathbf 1[T\subseteq S].
\]

The supplied integer moments are $m_T$, with $m_\varnothing=g>0$.
Here $g$ is the total mass, not a normalized probability.
The helper accepts monomials of degree at most four.
It represents each subset by an integer bit mask.

Suppose nonnegative masses $w_S$ realize the moments:

\[
m_T=\sum_{S\in\Omega}w_S X_T(S).
\]

Every polynomial $p=\sum_T c_T X_T$ that is nonnegative on $\Omega$ must satisfy

\[
\langle p,m\rangle=\sum_T c_Tm_T\ge0.
\]

A strict negative value therefore excludes this moment realization.
The helper checks every supplied atom with Python integers before reporting such a certificate.

## Constant correction

For an integer polynomial $p$, compute its exact minimum

\[
a=\min_{S\in\Omega}p(S).
\]

Then $p-a$ is nonnegative throughout $\Omega$.
Its moment value is

\[
\langle p-a,m\rangle=\langle p,m\rangle-ag.
\]

This correction removes numerical errors from a proposed multiplier without using a numerical feasibility tolerance.
It yields a separator only when the corrected exact moment value is strictly negative.

## Restoring atoms removed by zero moments

Let $Z$ contain nonempty monomials whose supplied moments are exactly zero.
Define

\[
q(S)=\sum_{T\in Z}X_T(S),\qquad
\Omega_0=\{S\in\Omega:q(S)=0\}.
\]

Every atom removed from $\Omega_0$ has $q(S)\ge1$.
For a candidate $p$, let $a$ be its minimum on $\Omega_0$.
Use $a=0$ if $\Omega_0$ is empty.
Set

\[
M=\max\left(0,\max_{S\in\Omega\setminus\Omega_0}
\left\lceil\frac{a-p(S)}{q(S)}\right\rceil\right).
\]

The repaired polynomial

\[
\widetilde p=p-a+Mq
\]

is nonnegative on every original atom.
Its expectation is $\langle p,m\rangle-ag$, since each monomial in $Z$ has zero moment.
Thus the final certificate applies to the complete supplied domain.
It does not depend on retaining a restriction to zero moments.

If the retained domain is empty, the choice $p=-1$ gives the separator $q-1$.
The helper includes this boundary case in its controls.

## Exact output and replay

Both corrections combine duplicate monomials before evaluation.
They divide the repaired coefficients by their positive greatest common divisor.
The saved record includes the original polynomial, correction, primitive polynomial, and exact moment value.
It also binds the ordered atoms, all moment data, and the complete stream of final atom values by SHA-256 hashes.

The separate `replay` function checks the repair identity and primitive normalization.
It then evaluates the final polynomial on every atom and recomputes its moment value.
A numerical solver status is never used as a certificate.

The caller must separately prove domain necessity and check the translation from moments to graph counts.
For graph applications, a strict separator still needs a literal graph-product replay.
The helper records these obligations explicitly.
It also requires positive total mass; callers must handle a zero-mass root separately.

## Controls and preserved correction

The corrected control record is
[`finite-boolean-moment-certificate-controls02.json`](../../experiments/logs/moments-and-counts/finite-boolean-moment-certificate-controls02.json).
It checks four known separators and 160 actual nonnegative integer distributions.
Those distributions produce 320 nonseparating polynomials and 3,056 independent literal atom evaluations.
The controls cover duplicate terms, an empty retained domain, and coefficients with 207 bits.

The original source and control record remain preserved.
Their only error was a metadata label reporting the 202-bit scale instead of the largest 207-bit raw coefficient.
The corrected source changes that expression only.
All fourteen certificate and replay function syntax trees remain unchanged.
The correction record binds both source hashes.

An independent source and arithmetic review also passes.
It checks noncontiguous masks, multiple zero penalties, large common divisors, and 324 signed ceiling divisions.
The review does not import the subject module or repeat its controls.

To run the controls with a new output path:

```sh
.venv/bin/python experiments/workspace/finite_boolean_moment_certificates.py \
  --controls --output /tmp/conway99-finite-boolean-moment-controls.json
```

No production moment point has been separated by this helper package alone.
