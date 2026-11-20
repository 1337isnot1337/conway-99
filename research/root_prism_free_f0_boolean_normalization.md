# Boolean normalization of F0 selector inequalities

This package strengthens necessary selector inequalities for the fractional F0 model using exact equivalences on Boolean selectors. It makes no graph-automorphism assumption and does not run an optimizer.

## Guarded individual rows

An integer row potential gives positive weights c_b, positive demand d, and the necessary guarded inequality

    sum_b c_b z_b >= d z_a.

The target a is not a candidate neighbor, so it is absent from the weighted list. Define c'_b=min(c_b,d), let g be the gcd of the capped weights, and put k=ceil(d/g). The equivalent Boolean inequality is

    sum_b (c'_b/g) z_b >= k z_a.

For z_a=0, both inequalities hold because all weights are nonnegative. For z_a=1, either a selected weight was capped, in which case it alone reaches d, or no selected term changes. Dividing by g produces an integer left side; this proves the ceiling step.

The guard coefficient is deliberately excluded from the gcd. Including d would miss the integer ceiling when d is not divisible by the weight gcd. With an empty weighted list, g=1 and the inequality forces z_a=0.

These are linear inequalities valid for every binary graph selection and hence its convex hull. They can reject fractional solutions of the raw row-potential relaxation. Weight capping and integer rounding are therefore retained explicitly rather than replaced by raw potential weights.

## Shared signed rows

A shared-potential allocation gives a homogeneous signed inequality

    sum_a c_a z_a <= 0.

Let D be the sum of its positive coefficients. If D=0, every coefficient is nonpositive and the inequality is automatic in the unit box. Otherwise rewrite it as the positive-literal threshold

    sum_(c_a>0) c_a(1-z_a) + sum_(c_a<0) (-c_a)z_a >= D.

Cap each literal weight at D, divide all capped literal weights by their common gcd, and take the ceiling of D divided by that gcd. This is the ordinary Boolean threshold equivalence. Expanding the complemented literals gives a signed linear inequality again.

Each original positive coefficient is at most their sum D, so its literal weight is unchanged by capping. Their sum remains D. The common divisor therefore divides D, and the expanded right side is exactly zero. Only sufficiently large negative coefficients can be capped in this particular homogeneous conversion. This is a different derivation from the single-guard rule.

The source checks this divisibility and zero-right-side identity explicitly. It does not apply the individual guarded gcd rule to shared rows.

## Exact controls

The standalone normalizer uses BigInt arithmetic. Its exhaustive finite controls compare both Boolean truth values for 74,896 guarded assignments and 41,371 signed shared assignments. Twelve additional assignments use coefficients up to 89 bits. The controls include empty lists, all-nonpositive shared rows, both guard branches, and positive and negative coefficients.

Three exact fractional examples demonstrate why Boolean equivalence does not mean equality of the raw real relaxations:

| Operation | Raw coefficients in a <=0 row | Fractional point | Normalized violation numerator |
|---|---|---|---:|
| Guarded cap | (3,-5,-1) | (1,3/5,0) | 6 over denominator5 |
| Guarded ceiling | (3,-2,-2) | (1,1,1/2) | 1 over denominator2 |
| Shared complement cap | (2,-5) | (1,2/5) | 3 over denominator5 |

Each raw row has value zero at its example. Each normalized row has the strictly positive value shown. No LP or SAT solver participates in these checks.

## Full-registry preparation

The separate recovery source binds the complete final 3,948 individual and 456 shared records to the recovered mathematical transcript. It directly reconstructs every individual potential coefficient and all 38 shared-potential families on the complete 68,394-edge domain. The shared coefficients are checked through their explicit endpoint allocation and all twelve transports before normalization.

The preparation then checks the complete twelve-action closure of normalized rows, adding a transported row only when its core relabeling proof is explicit. For a selector-orbit-constant point, the quotient coefficient is the sum of literal coefficients in that orbit. It is not divided by orbit size.

The twelve core relabelings support convex averaging of necessary linear inequalities. They impose no automorphism on a completed graph and fix no selected incidence. Full and quotient evaluations are compared exactly at any supplied rational point.

The earlier twelve direct weighted cuts are a separate input and are not silently counted among the final 4,404 records. The frozen native fractional baseline query remains unchanged. Any stronger model and any subsequent query require their own explicit preparation.
