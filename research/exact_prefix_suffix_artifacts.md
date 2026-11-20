# Exact prefix and suffix artifacts

Large native snapshots and selector registries share substantial byte prefixes.
The publication helper stores one immutable base and the exact remaining bytes
of each target. This changes file storage only. Search inputs, model bytes,
certificate records, and replay rules remain unchanged.

The helper is `experiments/workspace/exact_prefix_suffix_artifacts.py`.
Its manifest schema is `conway99.exact-prefix-suffix-artifacts.v1`.
Each entry records the base file, its encoded and decoded lengths and SHA-256
digests, the number of decoded base bytes to retain, the suffix file and its
length and digest, and the complete target length and digest. A base uses
either the `identity` codec or gzip decompression. A native gzip target also
records the length and digest of its decompressed protobuf.

Restoration verifies all these bindings before creating a target. It accepts
an existing target only when the complete bytes match. It never overwrites an
existing file. Run Python with assertions enabled.

## Fresh clone commands

From the repository root, restore the demonstration targets with:

```sh
python experiments/workspace/exact_prefix_suffix_artifacts.py restore --manifest experiments/logs/root-prism-free/f0-exact-prefix-suffix-demo01/manifest.json
```

Restore the raw inputs for the accepted preparations 04 and 05 with:

```sh
python experiments/workspace/exact_prefix_suffix_artifacts.py restore --manifest experiments/logs/root-prism-free/f0-direct-master-preparation04-05-publication01/manifest.json
```

The manifest, helper, bases, and suffixes must be present at their recorded
repository paths. A package may reference a base already committed in an
earlier checkpoint. The command prints a receipt containing the complete
target hashes and `CREATED_EXACT` or `ALREADY_EXACT` for each file.

## Demonstration

`f0-exact-prefix-suffix-demo01/report.json` records a fresh isolated copy
containing only the helper, manifest, bases, and suffixes. The actual command
restored a run02 native snapshot and final registry. An independent complete
byte comparison accepted both outputs. A second invocation accepted the
existing exact files. The original completed run files were unchanged.

The two target files contain 1,160,036 bytes. Their suffixes contain 274,953
bytes. The native base was already committed; the demonstration's compressed
registry base contains 43,234 bytes. These figures describe this example,
not a guaranteed compression ratio.

## Creating a new package

Create a JSON list whose entries contain `base_path`, `base_codec`,
`target_path`, and `suffix_path`. Set `verify_target_gzip` to `true` for a
native gzip target. Use repository-relative paths. Then run:

```sh
python experiments/workspace/exact_prefix_suffix_artifacts.py pack --specification SPECIFICATION.json --manifest MANIFEST.json
```

Packing reads each completed target and writes new suffix and manifest files.
It does not change the source targets. Bind the resulting files in the
publication map. Preserve the complete target hashes already recorded in the
search and replay receipts.
