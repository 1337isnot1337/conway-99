# Restrictions from the two theta series at level seven

In a hypothetical Conway graph the rank of 27I−9A+J over the field of seven elements cannot be 28, 30, or 32. Combined with the previously recorded lower bound 27, parity, and upper bound 42 this leaves 34, 36, 38, 40, and 42. The unrestricted existence question remains open in this work.

## The two lattices

Let E be the real −4 eigenspace, P its orthogonal projection, and L=E∩Z⁹⁹. Write r for the rank in the first paragraph. The discriminant identity det L=9·7ʳ is in square_certificate.md and in Djematene's 2026 archive cited there. Define

    H = E ∩ (Z⁹⁹ + (1/3) Z·1),
    K = √7 P{b ∈ Z⁹⁹ : sum b ∈ 3Z}.

Then H=√7 K*. Indeed the dual condition means having integral pairings with every difference of two coordinates and with three times each coordinate. The index [H:L] is three, since 7P times an indicator of a three-set is an element of E whose coordinates are integers plus one third. Thus det H=7ʳ. The norm of x=a+t·1 in H is sum aᵢ²−99t² for t=0,±1/3, since sum x=0. It is integral and even by applying evenness of L to 3x. Inner products in H are integral directly from the coordinates (the correction is −99tu). The squared norm of √7 Pb is 3 sum bᵢ²−bᵀAb+(sum b/3)², an even integer. Both lattices are even, integral, and of level dividing seven by scaled duality.

For x in H with nonintegral coordinates, its norm is at least 22: at fixed integral sum the least possible sum of squares of the coordinates occurs when they are as equal as possible, producing 66 coordinates ±1/3 and 33 coordinates ∓2/3. For integral x≠0 with Ax=−4x the positive and negative masses agree. If all coordinates are ±1 or zero, each site sees at least four of the opposite sign, hence the two sets have common size h with 6h ≤ 2 binom(h,2), giving h≥7. A coordinate of magnitude at least two requires opposite mass at least eight and squared norm at least 18. Therefore H has minimum at least 14.

At norm 14 the two sides form the complementary Fano point-block incidence, proved in shortest_vectors.md. Any three sites of one side determine both entire sides. Repeatedly adjoining the common neighbors of a pair on the same side is forced in the ambient graph because every such pair already has two within the core. Calculation on the seven blocks {2,4,5,6}+i modulo seven gives all fourteen sites from each of the 35 starting triples. Of the 35 triples in the positive side, 28 have a common neighbor, four per negative site. These triples cannot occur in two distinct signed vectors with the same triple positive. The graph has at most 99·binom(7,3)·8 independent triples with a common neighbor. Thus the number of norm-14 vectors is at most 990.

At norm 16 the two signs each occupy eight sites, with magnitudes one. Let e be the number of internal edges in either side. The numbers are equal by the eigenvector equation, and a site with internal degree d sees 4+d opposite sites. Counting pairs of positive sites with a negative common neighbor gives at least 48+8e and at most 56−e, so e=0. The two sides induce a bipartite four-regular graph with pair codegrees at most two. The script signed_eight.py builds its eight four-subset rows one at a time, retaining one representative under independent permutations of the sides. It tests the two codegree caps and the possibility of final degree four. There are five completed classes. To bound embeddings, fix a center with k ordered neighbors from different edges in its neighborhood, in at most 99·(7)ₖ·2ᵏ ways. A new site with two assigned neighbors has at most two choices, or only one if another common neighbor is already assigned. Three assigned neighbors also allow at most one choice. Division by the order of the side-preserving automorphism group gives respective bounds 6930, 10395, 27720, 83160, and 20790. Thus the norm-16 coefficient is at most 148995. Additional restrictions on embeddings can only decrease this number.

## Lower bounds in the dual

The 231 triangles give at least 462 norm-four vectors in K by using either sign of their indicators. At norm six the 8316 ordered nonadjacent differences and twice the 8316 induced paths on three vertices give at least 24948. Differences have coordinate sum zero and signed path indicators have sum ±3. These three classes cannot coincide under P. If Pb=0 then 7Pb=(3I−A)b+(sum b)1/9=0 forces sum b divisible by nine. At norm eight there are at least 1386 signed adjacent differences.

For larger simultaneous counts, sparse_theta.py enumerates integral b with nonzero coordinates in ±{1,2,3}. For sum zero it allows at most two positive and two negative sites. For sum three it allows at most four positive sites and one negative, and also includes all their negatives. Within one of the three classes, the difference between any two choices has each sign supported on at most five sites. Every induced subgraph on at most five vertices has spectral radius strictly below three. If the maximum degree is four it is contained in the cone over two independent edges, with largest eigenvalue (1+√17)/2. Otherwise the only potential equality component would be cubic, hence a forbidden four-clique. Applying positive definiteness of 3I−A to the two sign supports separately proves that this difference has nonzero projection. Thus every counted vector is distinct. The exact numbers of the induced graphs through five sites follow by deletion of a vertex of degree at most two and the SRG identities as in core_counts.py. The resulting lower bounds at Fourier orders 2 through 6 are 462, 24948, 1398474, 18001368, and 86356116.

## The certificate

Use q=exp(2πiz), θ=Σq^(x²+xy+2y²), and the Dedekind eta function η. For 0≤j≤14 set

    fⱼ=θ η(z)^(49−4j) η(7z)^(4j−7).

These forms have weight 22 and trivial character on Γ₀(7). The two eta congruences are satisfied and the character of the eta quotient, like that of θ, is the quadratic character of discriminant −7. Their vanishing orders at infinity and zero are j and 14−j; eta has no zeros in the upper half-plane. They are independent and span: a nonzero form cannot vanish to order 15 at infinity by the valence bound 22·8/12. The even lattice theta series of H therefore equals Σcⱼ fⱼ. Poisson summation, the eta inversion formula, and the self-similarity of the determinant-seven binary form give

    Θ_K = Σ 7^(3+r/2−2j) cⱼ f_(14−j).

Apply the bounds above, constant terms one, and nonnegativity of all coefficients. For r=28,30,32 the corresponding JSON files give nonnegative rational weights whose linear combination cancels every cⱼ and has right-hand side one, producing zero ≥ one. Each certificate only uses the coefficient constraints named in the file. level_seven_check.py independently expands the products, checks the transform on five explicit rank-44 lattices made from the determinant-seven binary form, E₈, and √7 E₈, and verifies each cancellation with exact rational arithmetic. The other even ranks have feasible scalar coefficient relaxations at the tested order. This does not produce a graph.

Primary background on lattice theta series of prime level and the Fricke involution is in [Scharlau](https://wwwold.mathematik.tu-dortmund.de/~scharlau/research/preprints/2012_scharlau_level7.pdf) and [Böcherer and Nebe](https://arxiv.org/abs/0909.1184).

## Earlier report of the same rank exclusions

The [ProofAtlas project record](https://www.proofatlas.ai/collaboration/conways-99-graph-conjecture/) reports that an earlier group eliminated ranks 28, 30 and 32 by opposite-star classifications and bordered matrix tests. It identifies some missing original search records and requests independent certificates. The five-rank frontier therefore predates our calculations. The theta certificates here derive the same exclusions without using those computer searches. The site also previously suggested the anisotropic rank-42 line lattice as a possible theta-series target.
