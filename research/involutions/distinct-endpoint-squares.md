# The distinct-endpoint pairing of all 21 squares is impossible

At a one-fixed-point involution, the two far orbits in each of 21 squares have two-axis labels. Suppose the labels in every square share exactly one axis. Call it the center; the two other axes are its endpoints. **The 21 endpoint pairs cannot all be different.** This holds for every assignment of centers and every choice of interfaces. It includes the Fano-plane pairing as a special case.

## The 21 vectors

Use the [square Gram construction](fano-square-pairing.md). Write $u_t$ for the zero-one label column of a far orbit $t$, and $U$ for the matrix of all 42 labels. Every two-axis label occurs twice. The even far adjacency matrix $B$ has a single entry two in each row (at the other orbit of the same square), zero diagonal, and other entries zero or one. It satisfies $UB=4J-2U$. Write $S_a$ for the 12 far orbits whose labels contain axis $a$. From a row inside $S_a$ the total $B$-weight into $S_a$ is two, and from a row outside it the total is four.

For each square $s$ let $m_s$ be the sum of its two labels. With center $c$ and endpoints $p,q$ this is $2e_c+e_p+e_q$. The negative-eigenspace vector $z_s$ from the Gram construction vanishes at the fixed point and on all seven axes. At a far orbit $t$ its two values agree. Denote twice this common value by $Z_{ts}$. If $d_{ts}$ counts neighbors in square $s$ of one point in orbit $t$, the formula for $z_s$ gives
\[
 Z_{ts}=2+6\mathbf1_{t\subset s}-2d_{ts}-u_t^\top m_s.
\]
In particular $Z_{ts}=1$ in both orbits of $s$. The column $Z_s$ is odd at exactly the 20 far orbits containing precisely one of $p,q$. We have
\[
 BZ=-4Z,\qquad Z^\top Z=14K,\qquad K_{ss}=2.
\]
Here $K_{st}=4-2N_{st}-m_s^\top m_t$ for $s\ne t$. Each integer column $Z_s$ thus has squared norm 28.

Assume for contradiction that every pair of axes occurs as endpoints. The vectors $z_s/\sqrt7$ then have integral Gram matrix $K$ and squared norm two. Distinct vectors cannot coincide up to sign: their parity masks on the 42 far orbits distinguish the endpoint pairs. Two different two-element subsets of seven neither agree nor are complements. Hence distinct inner products are $0,\pm1$. Their parity is that of the endpoint intersection, so disjoint pairs are orthogonal and intersecting pairs have inner product $\pm1$.

For any three endpoint pairs through an axis, the product of their three inner products is positive. A negative product would allow sign changes making all inner products $-1$, giving a zero sum of the three signed vectors. Their $Z$ columns cannot sum to zero with those signs: the symmetric difference of the three endpoint pairs has size four, and some far label meets it once. The signs on the six pairs at each axis therefore factor into individual signs, as seen by fixing one of the six as reference. Thus $K=V^\top V$, where each column $V_s$ has entries $\pm1$ at its two endpoints and is zero elsewhere. Also $Z\equiv U^\top V$ modulo two.

## The full-rank case

The assignment $V_s\mapsto Z_s$ defines a linear map on the span of the columns of $V$, multiplying squared norms by 14. If the span is seven-dimensional, write $F$ for its $42\times7$ matrix. Its columns have squared norm 14 and satisfy $BF=-4F$.

The integer column span of $V$ then contains $2e_a$ for every axis. To see this, switch axis signs along a spanning tree of the complete endpoint graph so that its tree columns are signed differences. They generate every coordinate difference. Full rank requires a remaining column that is a signed sum of two coordinates, giving one doubled coordinate and hence all seven. Axis sign switches preserve the parity assertion. Express $2e_a$ in the integer column span and use $Z\equiv U^\top V$ to see that $2F_{:a}$ is integral and even. Thus $F$ is integral.

In each row, the parity pattern of $F$ is either $u_t$ or its complement: their difference is orthogonal modulo two to every two-axis column. If $h$ rows use the complement, the number of odd entries is $84+3h$. The total sum of squares is 98, so $84+3h\le98$ and $84+3h\equiv98\pmod4$. This forces $h=2$. If $h_a$ complemented rows have label containing $a$, its column has $14-2h_a$ odd entries. The column norm is 14, so $h_a$ is even. The two complemented rows therefore have the same label.

Choose an axis $a$ outside that label. The column $f=F_{:a}$ has 14 odd entries, so its nonzero entries are all $\pm1$, on $S_a$ and the two complemented rows. Summing the absolute-value bound from $Bf=-4f$ over $S_a$ would require
\[
48\le 12\cdot2+2\cdot4=32.
\]
Here the factors two and four are the exact column weights into $S_a$ from those two classes. This excludes full rank.

## The balanced case

A nonzero vector orthogonal to all columns of $V$ has equal absolute values at the two ends of every edge, hence at all seven axes. After switching axis signs, all columns therefore have the form $V_s=e_p-e_q$. Orient the endpoint pair from $p$ to $q$. For each far orbit $t$ there is an integer potential $h_t$ on the seven axes with $Z_{ts}=h_t(p)-h_t(q)$. Indeed the linear map on the span of the coordinate differences supplies the potential up to a constant, and every difference is integral.

First, if $t$ itself has label $\{a,b\}$, its potential has $h_t(a)=h_t(b)$. Let $s$ have endpoints $a,b$. A nonzero $Z_{ts}$ would be even. Its column has 20 odd entries and squared norm 28, so this entry would be $\pm2$, with exactly one other even entry $\pm2$ and all odd entries $\pm1$. The row at $t$ has total $B$-weight at most four into the odd entries, since they belong to $S_a$ or $S_b$ and its weight into each is two. The other even entry would have to contribute at least four in absolute value to attain $|-4Z_{ts}|=8$. Only the square mate of $t$ has weight two. Its label shares exactly one of $a,b$, so it is an odd entry. This proves the equality of the two potentials at the label of their row.

Fix a square $s$ centered at $c$ with oriented endpoints $p,q$. Order its orbits $t,t'$ by labels $\{c,p\},\{c,q\}$. For every square $j$,
\[
 Z_{tj}+Z_{t'j}=K_{sj}.
\]
Indeed the left side sums $z_j$ on the four points of $s$. In the notation of the Gram construction this is $x_s^\top z_j$, since $z_j$ vanishes on the axes and root. Applying the negative projector gives $7x_s^\top z_j=z_s^\top z_j$.

Normalize $h_t(q)=h_{t'}(q)=0$. Both potentials take value one at $p$ because both orbits have $Z_{ts}=1$. Their sum equals $V_s+\mathbf1$, by the preceding identity on every endpoint difference. The label equality gives $h_t(c)=1$ and $h_{t'}(c)=0$. All other entries of $h_t$ are even by its parity mask. Consequently $h_{t'}$ is $\mathbf1-h_t$ with coordinates $p,q$ exchanged.

Write $D(h)=\sum_{i<j}(h(i)-h(j))^2=7\sum_i h(i)^2-(\sum_i h(i))^2$. A row with two entries equal to one and five even entries has $D(h)\equiv2\pmod8$: writing the even entries as $2b_i$ and putting $b=\sum b_i$, the two terms are $7(2+4b)$ and $4(1+b)$ modulo eight. The partner has exactly the same $D$, since translation, sign and permutation preserve pair differences in square. Each square thus contributes $4$ modulo 16 to the sum of squared entries of $Z$.

Counting by the 21 squares gives $21\cdot4\equiv4\pmod{16}$. Counting by the 21 columns, each of squared norm 28, gives $21\cdot28\equiv12\pmod{16}$. This contradiction excludes the balanced case and finishes the proof.
