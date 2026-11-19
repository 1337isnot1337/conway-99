# Strengthened F0 native model preparation

Checkpoint 82 accepts three exact constraint packages and freezes a new native
append configuration. The native model has not yet been built or queried.
The endpoint remains an explicit SRG(99,14,1,2) or a contradiction covering every
such graph. Neither endpoint has been reached.

The scope here is the existing globally prism-free F0 split18+18 branch. The
second shell component and its relative alignment remain free. These results
do not exclude the whole F0 branch or any other component type.

## Accepted constraint packages

The [spectral-gap theorem](root_prism_free_f0_spectral_gap_pair_minor.md) gives
a necessary positive semidefinite matrix for an actual completion. The forward
pair census and its [independent complete replay](../experiments/logs/root-prism-free/f0-spectral-gap-pair-independent-cold01.json)
agree on all 114,960 pairs and 405,426 integer states. They reject 330 states.
The resulting 132 edge zeros include 60 already among the original 1,884
literal zeros; this append uses the other 72. All six selector-pair covers are
already implied by original unit Gram rows, so none is appended. The
[root acceptance](../experiments/logs/root-prism-free/f0-spectral-gap-pair-root-acceptance01.json)
also records further common-neighbor restrictions that are not represented
in this model.

The [compact four-exterior reconstruction](root_prism_free_f0_four_exterior_cross_quota_independent_result.md)
reproduces all 72,468 original row keys, 73,404 cases and 1,250,496 terms. The
complete report is retained as one file and three exact chunks. Root's
[independent coefficient replay](../experiments/logs/root-prism-free/f0-four-exterior-cross-quota-certificate-replay01.json)
checks every origin and all 63,336 sufficient certificates against full
sparse vectors of the original mixed equations. It proves that 49,458 rows
are implied by two original mixed equalities and nonnegative edge variables.
The retained list has 23,010 rows and 401,874 terms. Its canonical JSON SHA256
is b53cff225273f025bc9b6d8e2cd6a654291993df8da4d0345a0dc2312b0dafac.
The check takes 15.758 seconds; the wrapper, including exact input bindings
and complete serialization, takes 37.143 seconds.

Every retained row is necessary by the complete
[standalone local prism proof](root_prism_free_f0_four_exterior_prism_outage_proof.md).
The new reconstruction checks that proof's premises at every live origin.
The old unpublished finite-census files are not used as available inputs.
No original parent row is removed, and failure of the sufficient mixed
certificate test is not a nonredundancy theorem.

The [targeted signed-edge checker](root_prism_free_f0_single_edge_schur_certificates_terminal.md)
proves all 252 supplied one-edge patterns with explicit integer vectors and
strictly negative quadratic forms. The completed wrapper takes 12.982
seconds. Root then reconstructs every primitive matrix entry from the
accepted kernels and checks each vector with a separate expanded contraction,
in reverse certificate order. The
[literal root replay](../experiments/logs/root-prism-free/f0-signed-edge-literal-replay01.json)
also compares every original edge ID, isolated-selector guard, native row key
and origin index. It passes in 0.736 seconds; complete input verification and
serialization take 7.306 seconds. There are 252 distinct signed rows, all
certified by the plus kernel, and none has its present edge among the old
literal zeros. This validates the supplied rows individually; it does not
claim completeness of the earlier eight-pattern diagnostic.

## Frozen append

The [configuration](../experiments/logs/root-prism-free/f0-strengthened-native-configuration01.json)
binds all 26 input artifacts and 19 accepted authority statuses.

| Appended family | Rows | Terms |
| --- | ---: | ---: |
| Existing three-exterior one-edge transfers | 1,224 | 2,448 |
| Existing three-exterior path transfers | 57,996 | 173,988 |
| Retained four-exterior rows | 23,010 | 401,874 |
| Accepted triangle covers outside the old zero family | 6,990 | 20,970 |
| Spectral edge zeros outside the old zero family | 72 | 72 |
| Individually certified signed-edge rows | 252 | 1,008 |
| Total appended | 89,544 | 600,360 |

The expected complete model has 257,594 rows and the same 68,934 variables.
The full 168,050-row parent remains byte for byte. Its raw SHA256 is
4505234d13039159c3191918f7db729819ad6ed25f46e538d91975466d660e83.

The [producer](../experiments/workspace/root_prism_free_f0_strengthened_append.py)
constructs the six blocks in the listed order, requires an exact native
export round trip, and saves the full gzip model plus a lossless gzip suffix.
Removing the appended constraints must reproduce the original parent bytes.
The [independent checker](../experiments/workspace/root_prism_free_f0_strengthened_append_replay.py)
uses the protobuf decoder only. It reconstructs each expected row and compares
every complete constraint message, including domains, enforcement fields and
metadata. It also checks both archives, all provenance links, and all 252
signed quadratic certificates from raw kernels.

The local execution environment remains unavailable. The frozen
[CI driver](../experiments/workspace/root_prism_free_f0_strengthened_ci.py)
is prepared for a separately reviewed workflow. Native controls have a
15-second owner limit, the preparation has a 120-second worker and
135-second owner limit, and the independent main replay has a 90-second
worker and 105-second owner limit. Controls and main results must pass their
actual process owners, including successful exit, child reaping and process
group termination. No optimizer is called by this package.

At this checkpoint the native source, configuration and independent checker
are unrun. A successful preparation and complete independent replay are
required before a later query can use the resulting model. Historical failed
attempts and unrun configurations remain preserved.
