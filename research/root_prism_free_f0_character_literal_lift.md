# Literal lifting of the F0 character populations

## Result and scope

The inverse tables are complete. They recover all 64,144 admissible literal
subsets behind the 19,331 refined character-profile tuples. Every tuple has
at most 12 preimages. No production count candidate has been evaluated.

For a future fixed count assignment, the remaining selector reconstruction
is a finite constraint satisfaction problem with 42 variables and 861
constraints of arity two. Each variable chooses one literal subset from
the preimages of its prescribed local tuple. These are not binary-valued
variables: their domains have between zero and 12 members.

Preparation took 5.15 seconds. The separate cold replay passed in 22.66
seconds, including complete table reconstruction and direct checking of
the saved synthetic witnesses and rejection tree. It did not repeat the
synthetic searches. No external solver or optimizer was called.

This package concerns selector populations, selector-pair populations, and
signed character sums. It does not reconstruct the exterior edge variables
or a graph.

## Exact inverse domains

The 42 selector orbits partition the 480 literal signatures. Four orbits
have size six and 38 have size twelve. The preparation retains their
published literal order and the published orientation of every character
signing.

For each orbit, every local bitmask is examined. The same proved pair
zeros and original Gram capacities used by the frozen profile construction
are imposed. The unsigned count tuple and all supported signed sums are
then recomputed. The resulting list for each refined tuple is checked
against its saved multiplicity and minimum representative. Both the
unsigned disposition stream and the signed accepted-mask stream reproduce
their frozen hashes.

| Literal preimages of a tuple | Number of refined tuples |
| ---: | ---: |
| 1 | 418 |
| 3 | 17,280 |
| 6 | 1,237 |
| 9 | 96 |
| 12 | 300 |

A representative alone is insufficient. The full preimage list remains
available, including the nine-member lists. No independent relabeling of
one orbit is permitted.

## Pair coverage and normalization

There are 9,742 original selector-pair orbits. Exactly 358 lie within a
single selector orbit and 9,384 connect two different selector orbits.
The local tuple checks recover the former. The 861 cross-orbit
constraints recover the latter.

Every pair orbit lies wholly in one unordered pair of selector orbits.
This is checked directly for all 114,960 literal selector pairs. The cross
blocks contain 112,392 of those pairs. All 389 proved-zero pair orbits
remain explicit zero targets, including those whose count coordinates
were removed from the reduced model.

The count variables are literal populations, not orbit averages. In the
original 15,589-column namespace, columns 0 through 41 are selector
populations, columns 42 through 5,846 are exterior-edge populations, and
columns 5,847 through 15,588 are selector-pair populations. The adapter
uses the frozen map from the reduced 15,038-column namespace. It omits
the exterior-edge coordinates and restores all removed selector-pair
coordinates as zero. The 118 signed populations use their separate
published namespace.

Integer values or canonical decimal integer strings are accepted. There
is no rounding or conversion from fractional averaged coordinates.

## The fixed-candidate problem

Let \(D_i\) be the complete list of local masks whose tuple equals the
candidate's prescribed counts and signed sums on selector orbit \(i\).
A missing tuple gives an empty domain.

For \(i<j\), let \(A\in D_i\) and \(B\in D_j\). They are compatible exactly
when, for every original pair orbit \(p\) between \(i\) and \(j\),

\[
\#\{(a,b)\in A\times B:\{a,b\}\in p\}=Z_p.
\]

All masks remain literal. Repeated occurrences in one pair orbit are
counted with their actual multiplicity.

The per-orbit maximum domain sizes give an upper bound of 70,596
choice-pair comparisons for one candidate. Including the largest local
subset sizes gives at most 4,519,476 literal histogram contributions.
These bounds concern construction of the binary relations; they do not
bound the backtracking search tree.

Any actual incidence with the fixed candidate populations supplies one
allowed local mask per orbit and satisfies every binary relation.
Conversely, one simultaneous CSP assignment determines a unique Boolean
selection of literal signatures. The local tuple identities and cross
relations then recover all 42 selector populations, all 9,742 original
pair populations, and all 118 signed sums exactly. This is equivalence
for the selector-moment realization within the stated necessary local
domains.

Each returned literal witness is independently recomputed from its
selected signature IDs. The verifier also evaluates all 172 original
selector equalities directly. Those equality results are reported
separately; a moment realization that fails them cannot be called a
selector-incidence solution. Even a witness passing them leaves all
exterior-edge and graph-completion conditions unresolved.

## Finite rejection certificates

The generic kernel uses exact arc-consistency deletions and exhaustive
branching. A deletion records a variable, one current value, and another
variable with no remaining compatible value. The checker tests that
absence of support before accepting the deletion.

A contradiction leaf must contain an empty current domain. A branch node
lists every value of its chosen current domain and provides the
corresponding subtrees. A rejection is accepted only when every branch is
covered by checked contradiction subtrees. The replay checker does not
rerun propagation or choose branches.

Time and node limits produce UNKNOWN. An unknown leaf or a missing
branch cannot certify rejection. A checked rejection excludes only the
supplied fixed population assignment. It is not an F0 exclusion.

## Controls

The generic kernel was compared with direct enumeration on all 4,096
binary three-variable relation systems. There were 2,397 satisfiable and
1,699 unsatisfiable systems; four unsatisfiable cases required branching
after arc consistency. Every returned certificate was checked.

Additional controls cover an empty domain, a singleton domain, a zero
node budget, and rejection of an invalid deletion that still has support.

Three small literal selections, the empty set, \(\{0\}\), and
\(\{0,89\}\), reconstruct their exact projected moments. They intentionally
are not 60-signature incidence candidates and fail the original population
equalities. This checks the distinction between moment reconstruction and
full incidence acceptance.

A negative control keeps the local singleton tuples for signatures 0 and
89 while changing their only cross-pair target to zero. All local tuples
still exist, but the binary relation is empty. Its three exact deletions
and empty-domain certificate replay successfully.

## Frozen artifacts

- [Inverse construction and candidate adapter](../experiments/workspace/root_prism_free_f0_character_literal_lift.py)
- [Finite CSP kernel and trace checker](../experiments/workspace/root_prism_free_f0_literal_lift_csp.py)
- [Complete inverse preparation](../experiments/logs/root-prism-free/f0-character-literal-lift-preparation01.json.gz)
- [Preparation log](../experiments/logs/root-prism-free/f0-character-literal-lift-preparation01.log)
- [Cold replay](../experiments/logs/root-prism-free/f0-character-literal-lift-preparation01-cold.json)
- [Cold replay log](../experiments/logs/root-prism-free/f0-character-literal-lift-preparation01-cold.log)

The production candidate interface is not exposed by this preparation
CLI. A real candidate requires its own immutable binding, limits, and
query review.
