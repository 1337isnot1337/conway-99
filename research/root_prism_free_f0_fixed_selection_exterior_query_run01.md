# The direct literal incidence has no exterior completion

The single fixed-selection exterior query is certified UNSAT. Its direct
DRAT check and separate full domain/CNF rebuild, retained-input check and
second DRAT pass all completed within their declared limits. This excludes
one first incidence with the second component and its alignment free.

The selection is the exact 60-signature witness from the direct literal
540-variable query. That earlier witness passed all 172 original selector
equations, 90 motif conflicts and 4,416 literal cuts. Root's separate local
matching check also found a perfect matching at each of the 18 core sites.
Those checks did not supply a single consistent exterior graph; the present
necessary exterior formula proves that none exists for this selection.

## Exact certificates

The complete CNF has 1,219 primary edge variables, 165,148 variables and
423,682 clauses. It encodes 60 degree equations, 1,080 mixed equations and
1,770 outside-pair caps. Its SHA-256 is
`d5bb8807367519fc32e7a4d05305533154d7ecf134483cde2d9ee2c96a1532a6`.

The run is `experiments/logs/root-prism-free/f0-fixed-selection-exterior-query-run01`.

| Artifact | SHA-256 |
| --- | --- |
| Run result | `f475d5541af80b30df25dcabbaa517853cbd4ab4d431537e3fd2b08a4384f3cf` |
| Accepted run owner | `f4a213e3b2ce1fcfd634b27eed1d95680af9b414552793af3928ad78f04144fe` |
| Raw proof | `323f57581ff810cdde368ee8a42415a4e1fca5fdd8e16fb8225ec7b21f996f65` |
| Retained CNF | `aa4e78e057ed8b70e88ce4a003e0e8d1b47a62bdac1d0c36b5e40e95e46b962a` |
| Retained proof | `4847c6e13804286495cfe90237dbd2acc1bffc683111ca793eb7cd9b72300176` |

The raw proof has 21,044 bytes. The retained CNF contains 116 original clauses
in 1,733 bytes; the retained proof has 1,912 bytes. Multiset inclusion was
checked against the complete frozen formula and checked again against the
freshly rebuilt formula.

The separate cold directory is `f0-fixed-selection-exterior-query-run01-cold`.
Its report hash is
`3367e029d8a28ce7195ff7897a2b020d4b3f9cffd2b44c9e955ba048dcf03363`;
its accepted owner hash is
`e600a979c1f5709016fc6bf1d6586cf4dcd30534d2d6b9dc969f19f62ab462b2`.
The two DRAT checks used the bound checker and both returned `s VERIFIED`.

## Timing and scope

The native initialization and single solve took 1.074944 seconds, including
1.037326 seconds of initialization. The direct proof check took 0.666747
seconds. The complete run owner took 2.277820 seconds against its 180-second
limit. The separate cold owner took 3.142400 seconds against 60 seconds,
including 0.215149 seconds for its proof check. Both owners accepted their
completed children with zero overrun and reaped them. No query was repeated.

After accepting the cold replay, the owner emitted
`certified-selector-cut.json`, SHA-256
`171e4f1000111717f412b6aa50bd25e03e68d6a2e7ffde7fb100366899824a32`.
For the frozen selection S, it states

\[
\sum_{a\in S}z_a\le59.
\]

The exact population-60 premise makes this a necessary selector cut in the
same F0 component-zero setting. It rejects this first incidence only. It
does not exclude the entire component or the complete graph problem.

The retained-clause attribution and any smaller arithmetic consequence are
separate work. Neither is claimed by this terminal package.

The cold `rebuilt.cnf` is byte-identical to the already published model CNF.
Its duplicate bytes may be omitted from publication only with an explicit
path, byte-length and SHA-256 restoration binding in the terminal manifest.
