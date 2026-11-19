# Two certified cuts from the partial parity discovery

The incomplete first parity cycle saved two complete witnesses. A separate
standard-library checker has now verified each witness without reading either
RREF basis or the search-evaluation transcript. It checked every coefficient
against the original 630 Gram equations, substituted only the previously proved
112 zero coordinates, and recomputed both deficits at the accepted rational
point with denominator 337,510,679. This direct check passed in 0.074227 seconds.

For the first witness, add original Gram rows
67, 100, 147, 157, 250, 375, 397, 418, 475, and 600. Their right-hand sides sum
to 13. After the proved zero substitutions, write the coefficient sum as

\[
\sum_{a\in H_4} x_a+2\sum_a f_a x_a=13,
\qquad f_a=\lfloor c_a/2\rfloor\ge0.
\]

The odd support has 67 coordinates. Nonnegative integer selectors force its
sum to be odd and at least one. The point has
\(\sum_{a\in H_4}x_a=296113257/337510679\), so the cover deficit is
\(41397422/337510679\). The equivalent rounded capacity has 68 terms and upper
bound six. The 67-term cover is the shorter representation.

For the second witness, add original rows
161, 191, 208, 236, 248, 251, 275, 301, 338, 353, 399, 403, 405, 409, 410,
411, 605, 611, 616, and 622. Their right-hand sides sum to 27. Its identity is

\[
\sum_{a\in H_5} x_a+2\sum_a g_a x_a=27,
\qquad g_a=\lfloor c_a/2\rfloor\ge0.
\]

Here the odd support has 65 coordinates and point value
\(299466677/337510679\). The cover deficit is
\(38044002/337510679\). Its equivalent rounded capacity has 242 terms and
upper bound thirteen, so the 65-term cover is preferable.

The full original coefficient vectors, support lists, individual Gram row
endpoints and quotas, removed zero coordinates, and capacity forms are in
`rook-case4-parity-cycle-saved-cuts-direct-replay01.json`. Both cover upper
bounds also follow from their nonnegative identities: the respective ranges
are [1,13] and [1,27].

The original cycle remains an unresolved partial search with an empty accepted
registry. The direct certificate is a separate result that makes these two
inequalities usable in a later model. It establishes neither exhaustion of
the parity family nor a case-4 contradiction. No LP or new elimination was
used to obtain this direct certificate.
