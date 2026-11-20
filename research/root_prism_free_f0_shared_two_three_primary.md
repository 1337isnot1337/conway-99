# Equality solvability at powers of two and three

For every integral selector vector satisfying the exact original Gram and population equations, the unrestricted degree-plus-mixed edge equality system has a rational solution whose denominators are all coprime to six. Consequently it has a solution modulo every modulus of the form 2^r 3^s, with r and s nonnegative integers.

This statement includes all 68,394 eligible edges as unrestricted variables. It leaves edge activation, nonnegativity, upper bounds, integer adjacency, and the primes at least five unresolved. It does not construct a graph or exclude a component.

## Matrix and previously checked facts

Let A be the 9,120 by 68,394 integer matrix containing all 480 degree equations and all 8,640 mixed equations. For selector vector x, the degree RHS at anchor a is 8x_a, and mixed RHS i is q_a[i]x_a. The row order and complete eligible domain are fixed in the modulo-four configuration.

The complete rational mixed-kernel certificate gives rational rank 7,731 and exact compatibility of every rational left-kernel identity with the original Gram equations. Each degree row is one third of the sum of its eighteen mixed rows over the rationals. The same identity holds on the RHS because every target vector sums to 24. Thus A also has rational rank 7,731, and its equality system is rationally compatible whenever the original Gram equations hold.

The independent characteristic-two calculation gives rank 7,713 and no new selector congruence modulo the original Gram rows. Adding the degree rows does not change that conclusion: modulo two, each degree equation is the sum of its eighteen mixed equations.

The independent characteristic-three calculation explicitly includes the degree rows. It gives rank 7,731, equal to the rational rank.

The independent modulo-four cold check gives eighteen vectors 2w in the original row module modulo four. It directly checks the original-row combination for each vector and proves that the binary classes w are independent modulo the binary row span.

## The Smith-factor argument

Write an integer Smith normal form P A Q = D, where P and Q are unimodular integer matrices. There are 7,731 nonzero diagonal factors. Exactly 7,713 are odd because that is the rank modulo two.

Let U be the binary row span of A. Let H consist of the binary vectors w such that 2w lies in the row module of A modulo four. The inclusion U in H follows by doubling any original row combination.

In Smith coordinates, the dimension of H/U equals the number of nonzero diagonal factors divisible by two but not by four. An odd factor contributes a direction already in U. A factor equal to two times an odd integer contributes one additional half-even direction. A factor divisible by four contributes no such direction modulo four.

The eighteen independently checked classes therefore prove that at least eighteen factors have 2-adic valuation one. The 7,713 odd factors and these eighteen factors already exhaust the rational rank 7,731. There are exactly eighteen even factors, each with valuation one, and no nonzero factor is divisible by four.

The rank modulo three equals the rational rank. Hence none of the nonzero Smith factors is divisible by three.

## A single rational solution with denominator coprime to six

Take any integral selector x satisfying the exact original Gram equations, and let b be its degree-plus-mixed RHS. The complete rational-kernel identities force all zero Smith-coordinate RHS entries of P b to vanish exactly.

The complete characteristic-two projection guarantees a solution to A y = b modulo two. Consequently each of the eighteen even Smith-coordinate RHS entries is even. Divide each nonzero transformed RHS by its Smith factor. At an even factor, first cancel a factor two from the numerator. The remaining denominator is odd, and it is not divisible by three. The free coordinates may be set to zero.

Transforming this rational vector back by Q preserves the property that every denominator is coprime to six. Each such denominator is invertible modulo 2^r 3^s. Reducing the same rational solution modulo that modulus proves the stated compatibility for every pair r,s.

No explicit Smith transformation is needed for this existence argument. The rank and half-even witnesses establish the relevant valuations. No claim is made about divisibility by primes at least five or about a simultaneous integer edge solution.

## Evidence and scope

[The binding record](../experiments/logs/root-prism-free/f0-shared-two-three-primary-corollary01.json) pins all seven accepted rank, kernel, producer, cold, and owner records used here. It also states the proof steps and the unresolved constraints. This is a separate deduction after the accepted modulo-four cold calculation; none of the earlier result files is changed or relabelled.
