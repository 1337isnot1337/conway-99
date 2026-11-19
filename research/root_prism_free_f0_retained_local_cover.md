# A guarded neighbor cover from the retained exterior proof

The checked exterior proof for the direct literal selection uses only one
anchor's edge variables. That anchor is signature 178, with core triple
{2,8,13}. The 116 retained clauses split into 111 clauses from 13 mixed
equations and five binary exclusions. There is no degree row, mixed row at
another anchor, or positive-capacity pair encoding in this retained core.

The mixed equations use core sites
1,3,4,5,7,9,11,12,13,14,15,16,17. The binary exclusions forbid simultaneous
neighbors in these pairs:

- {58,71};
- {87,124};
- {90,124};
- {225,230};
- {230,392}.

Each excluded pair shares exactly two fixed-core neighbors. A further common
neighbor at the anchor would violate the original common-neighbor bound.

## Exact attribution

`root_prism_free_f0_exterior_retained_attribution.py` adds read-only boundary
callbacks to the frozen encoder AST. Removing those callbacks recovers the
original AST exactly. The instrumented encoder reproduces the full CNF byte
hash `d5bb8807367519fc32e7a4d05305533154d7ecf134483cde2d9ee2c96a1532a6`.
All 116 retained clauses have unique original positions. Their positions and
complete mathematical row supports are recorded in
`f0-exterior-retained-attribution01.json`.

This is an attribution of an already checked proof. It makes no new SAT,
linear-programming, or proof-checker call. The source hash is
`2d4c46c711aa7f031b89b64107376238c2f29704e8dd90ca51bbda4bceff0d76`;
the record hash is
`a46d4e7ac2a74fc10641db76e16b0d0d7d64be26024ee15a2ae526e113c5d932`.
The attribution took 1.946 seconds.

## Universal selector consequence

Let E be the complete original eligible-neighbor domain of signature 178.
It has 244 signatures. Let B be the 31 members of E selected in the refuted
incidence. Every valid incidence in this F0 domain satisfies

\[
z_{178}\le\sum_{b\in E\setminus B}z_b.
\]

This row has 214 nonzero coefficients: one coefficient +1 and 213 coefficients
−1 after putting everything on the left, with right side 0. Its violation at
the saved selection is exactly 1.

To prove the row, assume the anchor is selected and no member of E outside B
is selected. Every actual neighbor of the anchor then lies in B. Keep all 31
edge bits from the saved local domain, setting a bit to0 whenever its other
signature is absent. The actual graph's mixed equations give each of the 13
retained cardinality equalities on these bits. The five binary exclusions
also hold. Each mixed encoding has disjoint auxiliary variables, so every
satisfied equality admits an independent auxiliary extension. These extensions
would satisfy all 116 retained clauses, contradicting the already checked
DRAT proof. The argument allows any smaller selection within B; it does not
assume that all 31 old neighbors remain selected.

The proof uses no fixed choice of the second component, no assumption that
the unknown graph has a core automorphism, and no requirement that the other
old selected signatures remain present. It gives a guarded complement cover,
not a shorter positive-only incidence pattern. Twelve relabeled versions can
be derived through the previously verified core actions; their explicit
registry transport belongs to the separate master preparation.

## Direct arithmetic record and peer gate

`root_prism_free_f0_retained_local_cover.py` independently reconstructs E from
the core and checks it against the complete original edge domain. It checks
every retained primary variable, each disjoint mixed auxiliary interval, all
complete row supports and each overlap-two exclusion. It then emits the
guarded row. No encoder, optimizer or proof checker is called by this source.

Source hash:
`922ad60fed6ae46f8a3bab51ea419a56fe3703177111e48104e6a2b3e426974a`.
Record `f0-retained-local-cover01.json` hash:
`1334c9d6a1028a9a55b9d31dcec5f09760c28e3e4b811d50eec5392d11c1e094`.
The arithmetic derivation took 1.067 seconds.

The independent source and saved-clause locality review passed. Its report
`f0-retained-local-cover-independent-review.json` has hash
`da0a7d2d3114b0e745937637f417f3bc136d94f912aeb1eed3c7d91c01d4bfc2`.
That review explicitly checked the smaller-B case, all 13 supports, 144 complete
auxiliary IDs and the five exclusions. The original proof remains bound by
the accepted full cold report 3367e029 and owner e600a979.
