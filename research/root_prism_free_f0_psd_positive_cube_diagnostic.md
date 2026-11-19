# F0 positive PSD cube diagnostic

The one authorized forward run completed in 19.213 seconds. Its output contains 10,830 minimal positive cubes, all using the three triangle edges. It produced 10,830 triangle-cover rows and no shorter positive-only row.

This is a completed diagnostic. The full pattern table has not been independently replayed. The root agent chose a direct comparison of every output row with the already accepted parent triangle family, because the forward run proposed no additional positive-only constraints. This package does not claim an independently accepted theorem excluding shorter cubes.

## Scope and exact computation

The accepted parent census contains all 1,179,048 triples of pairwise-disjoint F0 signatures for which all three original exterior edges are eligible. Its independent replay checked the complete domain, both full-core Schur families, every proper minor, and every negative record. The parent has exactly 10,830 negative all-three-edge triples in the plus family, with no negative proper minor in this triple universe. The minus family has no negative triple.

Every positive-only forbidden cube contains the all-three-edge pattern. The complete negative parent list therefore gives the relevant search list for positive-only cubes in this declared universe. The source preserves all 10,830 records, including the 3,840 triples containing an already proved zero edge. It does not use old zero, prism or path rows when classifying a pattern.

For each selected triple, the bit order is ab, ac, bc. The program evaluated all eight edge patterns, checking the three singleton minors, three pair minors and determinant of each of the two symmetric 3-by-3 matrices using BigInt arithmetic. A pattern is PSD-compatible only if all fourteen minors are nonnegative. PSD compatibility does not establish graph feasibility.

The frozen source and its complete mathematical source review are linked below. Small controls covered all 256 forbidden-pattern sets and all 18 endpoint-activated assignments per set. They also checked the selector guards, the path homogenization, and exact nonnegative linear combinations showing that every retained positive cube implies its original triangle cover.

## Reported output

| Item | Forward output |
|---|---:|
| Negative parent triples processed | 10,830 |
| Adjacency patterns checked | 86,640 |
| Symmetric matrices checked | 173,280 |
| Principal minors checked | 1,212,960 |
| Minimal positive-cube origins | 10,830 |
| Distinct literal rows | 10,830 |
| Selector-triple rows | 0 |
| Edge plus third-selector rows | 0 |
| Homogeneous path rows | 0 |
| Triangle-cover rows | 10,830 |

The program reported seven compatible patterns for 10,578 triples and six compatible patterns for 252 triples. The plus family rejected pattern 111 for every input triple. It also rejected pattern 001 for 112 triples, 010 for 90 triples, and 100 for 50 triples. The minus family rejected none of these saved patterns. The extra single-edge records are retained with their exact existing minor strings for later analysis. This package installs no signed-edge constraints.

A compact projection copies every complete literal row key and origin, together with all 252 extra single-edge records, from the stored output. That projection performs no new determinant or PSD calculation.

## Authority and limits

- [Frozen source](../experiments/workspace/root_prism_free_f0_psd_positive_cube_census_v8.js), SHA256 `8643c9d3bf1ae6175b315a8a7300c7c34c668fe16e41162f79994f0b341e694a`.
- [Configuration](../experiments/logs/root-prism-free/f0-psd-positive-cube-v8-configuration01.json), SHA256 `32cdf292c7acc396ffafd18697c37484484d1dded8e48fabadfc468e2ff59c58`.
- [Source review](../experiments/logs/root-prism-free/f0-psd-positive-cube-v8-independent-source-review01.json), SHA256 `3e87e21aea25fd82882c027a0789676b161e72faa45f499f65293cafc6373fd0`.
- [Root main gate](../experiments/logs/root-prism-free/f0-psd-positive-cube-v8-root-gate01.json), SHA256 `08ac355ad170b42190b8e00f37b9e90f11f8057cf37a90182b508ba03a789e2e`.
- [Accepted parent cold](../experiments/logs/root-prism-free/f0-triangle-schur-independent-cold01.json), SHA256 `5436baf4d22a0d6b929162176029a1defa13ecb4446f2436655b22aa1b2de9c1`.

The run used one 60-second cooperative bound and a 32 MiB serialized-report limit, with no retry. Complete serialization used 16,254,139 bytes and finished within 19.213 seconds. Publication hashing and upload followed the completed main run. There was no native model build, optimizer call, graph construction, or F0 exclusion.

## Complete report restoration

The complete report SHA256 is `80d5b82a95fad4c5cc7ff6623950491cfc29747600345f79f2a88c9078a6af32`. Its expected Git blob ID is `f5fc7789310e6b7221b7dc12cdf2bbde1e05b539`.

A direct upload of the full JSON failed because the connector's request body exceeded 16 MiB after escaping. Four exact chunks preserve the complete bytes. The publication manifest uses the already committed restoration helper and binds every chunk, intermediate prefix, and final report. The complete concatenation was independently compared byte-for-byte with the stored original output in V8. The Python helper was not executed during the local execution outage.

From a fresh clone, restore the report with:

```sh
python experiments/workspace/exact_prefix_suffix_artifacts.py restore --manifest experiments/logs/root-prism-free/f0-psd-positive-cube-v8-census01-publication/manifest.json
```

The helper verifies all sizes and SHA256 values, creates the two temporary assembled-prefix files and the final report, and accepts an existing file only when it is byte-exact. The manifest and chunks are the durable report representation; the complete-file Git blob is not claimed uploaded.

See the [diagnostic summary](../experiments/logs/root-prism-free/f0-psd-positive-cube-v8-summary01.json), [stored projection](../experiments/logs/root-prism-free/f0-psd-positive-cube-v8-stored-projection01.json), and [restoration manifest](../experiments/logs/root-prism-free/f0-psd-positive-cube-v8-census01-publication/manifest.json).
