# Shared-row separation for the new direct incidence

The new sixty-signature incidence satisfies all 4,416 original literal
cuts but has a checked exterior contradiction. This separate calculation
asks whether its linear shared-row relaxation already has an exact dual
certificate. It does not repeat the complete exterior SAT query.

## Model and reuse

The source is
`experiments/workspace/root_prism_free_f0_direct_incidence_shared_separation.py`.
It binds the actual selection, its literal cold report, the complete
fixed-selection model and the accepted exterior DRAT cold owner.
The original 480-signature domain and all 68,394 eligible edges are retained.
The 162 proved zero edge orbits are not applied here.

For the selected sixty signatures, the model has 1,219 shared edge variables
and 1,140 degree and mixed equalities. Each edge lies in [0,1]. The separate
outside-pair caps are omitted. A feasible rational point would establish
only feasibility of this relaxation.

The adapter reuses the frozen reserved shared-separation sequence. It makes
at most one ordinary feasibility call, reserving most of the sixty-second
phase for a bounded-potential call if needed. The second LP searches a
different formulation. Neither numerical status alone certifies a result.
The actual numerical values are retained before exact reconstruction.

Let v_a be an integer eighteen-vector at selected signature a, and let q_a
be its mixed demand. For each eligible edge ab, put

\[
w_{ab}=v_a^T h_b+v_b^T h_a.
\]

A strict integer gap

\[
\sum_a v_a^Tq_a-\sum_{ab}\max(w_{ab},0)>0
\]

contradicts the shared edge equations for this selection. This check uses
the full selected edge domain and integer arithmetic.

## Universal cuts

Extend the potentials by zero to all 480 signatures. For every positive
edge weight, allocate its value to one endpoint selector. The activated
mixed identities and the bounds y_ab <= x_a, x_b then give a necessary
linear selector inequality on the complete domain. The saved selection
chooses the allocation; it is not a hypothesis of the inequality.

The frozen lift gives twelve transports under independently checked core
automorphisms. Every transported coefficient is checked, including the
allocation ordering, and all cuts are divided by their common integer
factor. A cut must have a positive exact violation at the selected incidence.

## Acceptance and scope

Preparation reconstructs the data and all twelve actions, with no optimizer.
It passes in a 1.348-second owner with peak child RSS 131,616 KiB. The
preparation report SHA-256 is
`b8b99f362372b990b69ac126448181c66d73e4cc06445d1a8e26f07fdf2c8bdb`.

The query has a 120-second owner and one shared sixty-second numerical phase.
No unchanged call is retried. A separate sixty-second cold owner rechecks
the exact candidate binding, arithmetic gap and every transported cut.
Only its accepted terminal can certify new cuts. A phase overrun prevents
cut promotion even if an exact proposal was saved.

This preparation makes no new exclusion. The incidence already has its
separate checked SAT proof. The aim here is a stronger reusable inequality;
failure to find one leaves that earlier proof intact.
