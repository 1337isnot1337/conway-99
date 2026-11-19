# F0 direct master: preparation for the third continuation

The accepted run02 registry has 253 rows. Its final strengthened prefix was
not queried. This continuation preserves every parent entry and its provenance,
then appends 48 independently checked local packing rows and all 12,168
independently checked shared-potential rows. The initial registry has 12,469
rows. All 4,681 original native constraints remain, including the complete
4,416-row literal cut family.

The shared-potential census checked 54,720 anchor and potential pairs. Its
accepted independent replay reconstructed every row and direct coverage
witness. The continuation binds that replay and the complete ordered export;
it does not repeat the census during model setup. Rows were not selected by
whether they cut a previously observed candidate.

Registry V5 owns its concrete `add_rows` function and an explicit capacity of
16,384 rows. This replaces the old capacity of 256 while preserving complete
batch validation and refusal on overflow. The 253 parent rows remain byte
equivalent as registry entries. The next 48 and 12,168 rows retain their
certified order and full provenance.

Registry V6 changes only native variable lookup. It caches the 480 existing
selector handles once per append call. Coefficients, domains, row order,
validation, and the complete expected/native protobuf comparison remain.
All 15 controller function bodies match V5. Separate source reviews accepted
both versions.

Preparations 04 and 05 both passed without a solver or optimizer call. Their
native snapshots and registry bytes are identical. The native model has
540 variables, 17,150 constraints, and 2,031,768 linear terms. Its raw protobuf
has 24,013,622 bytes and SHA-256
`6c92f28dc9bacf8fd41eebcde41f79884b73d137b1185af3215b1134f93f4f47`.
Its gzip has 3,083,428 bytes. The initial registry JSON has 21,145,617 bytes.

Preparation 04 used 44.856 seconds of owner time; preparation 05 used 48.245
seconds. The cache preserves semantics, but these measurements do not show
an overall setup speed improvement. Both owners accepted their reports and
reaped all children without an overrun.

Root gate03 authorizes one V6 continuation under configuration04 and accepted
preparation05. Limits remain eight master calls, at most 60 seconds per call,
180 cumulative CP seconds, and 300 seconds of owner time. Shared separation
uses at most 60 seconds per candidate, clipped to the remaining owner time.
A newly certified row is required before another master call. The separate
cold replay retains its 60-second owner limit.

The preparation publication package stores exact compressed bases and a
restoration manifest for the large raw files. See
`research/exact_prefix_suffix_artifacts.md` for the fresh-clone command.
The helper changes storage only and preserves every complete raw-file hash.
Search results and their scope belong to the separate terminal package.

Neither these preparations nor a native infeasibility status proves exclusion
of the whole F0 component. No strongly regular graph is claimed here.
