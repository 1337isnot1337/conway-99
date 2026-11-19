/* Independent archive-to-native replay of the exact F0 literal layer. */
"use strict";
const fs = require("fs");
const path = require("path");
const zlib = require("zlib");
const vm = require("vm");
const crypto = require("crypto");
const ROOT = path.resolve(__dirname, "../..");
const EXPECTED_PRODUCER = "f9af8c9fcafcc070533cc5ad65c788023e782520dcea4a1a3ac46d3636a0badb";
const RADIX = ["experiments/workspace/root_prism_free_f0_literal_cut_radix.js", "e484e0e374e5579c75f3bfe9bdac2fa837acf75525d42d6c8f231a560856446c"];
const ROWS = ["experiments/logs/root-prism-free/f0-literal-cut-export-ci01/literal-rows.json.gz", "051282b7c8256fa3cad6edd9e9490290cfdfa5f6bef46b609bc32bdd63189b63", "3877ba7ec41c4f85f2d1623cfc5d20fa0d258c8c8319fa5dcd7313f580ac305e"];
const SPEC = ["experiments/logs/root-prism-free/f0-full-fourier-specification-ci01/specification.json.gz", "929703b3a685f95fb28bc6553aef02d5c7f6c879628154c62b8ecfa7d69ba8d5", "46fa44efdbe3640984a010347a3dfb65964b35752c919f4b6aa2fd24317f1d0b"];
const PREP = ["experiments/logs/root-prism-free/f0-full-fourier-specification-ci01/report.json", "cd96e24126c1ffab578d69d319431d023e055a82acbc883f66e72a9bdf54c96b"];
const COLD = ["experiments/logs/root-prism-free/f0-full-fourier-specification-ci01-cold/report.json", "650813eddce7e0c28def494a16756f49b74e1aa13b667806174c13150647e1a5"];
const OFFSET = 31756, COUNT = 480, FIRST_AUX = 32236, SAFE = (1n << 62n) - 1n;
const assert = (x, m) => { if (!x) throw Error(m); };
const sha = x => crypto.createHash("sha256").update(x).digest("hex");
const abs = x => x < 0n ? -x : x;
const max = (...x) => x.reduce((a, b) => a > b ? a : b);
function bound(entry) {
  const raw = fs.readFileSync(path.join(ROOT, entry[0]));
  assert(sha(raw) === entry[1], "input binding " + entry[0]);
  if (entry[0].endsWith(".gz")) {
    const plain = zlib.gunzipSync(raw);
    assert(sha(plain) === entry[2], "raw input binding");
    return JSON.parse(plain);
  }
  return JSON.parse(raw);
}
function main(directory, output) {
  const started = Date.now();
  const producer = fs.readFileSync(path.join(ROOT, "experiments/workspace/root_prism_free_f0_literal_cut_layer.py"));
  assert(sha(producer) === EXPECTED_PRODUCER, "producer binding");
  const radixSource = fs.readFileSync(path.join(ROOT, RADIX[0]), "utf8");
  assert(sha(radixSource) === RADIX[1], "radix source binding");
  const api = vm.runInThisContext(radixSource, {filename: RADIX[0]});
  assert(api.sha256(radixSource) === RADIX[1], "independent source hash");
  const radix = api.bindSource(RADIX[1]);
  const same = (a, b) => api.canonical(a) === api.canonical(b);
  const rows = bound(ROWS), spec = bound(SPEC), prep = bound(PREP), cold = bound(COLD);
  assert(prep.status.startsWith("PASS") && cold.status.startsWith("PASS"), "spec receipts");
  assert(cold.preparation_sha256 === PREP[1] && cold.specification_sha256 === SPEC[1], "spec cold ancestry");
  const reportRaw = fs.readFileSync(path.join(directory, "report.json")), report = JSON.parse(reportRaw);
  const layerArchive = fs.readFileSync(path.join(ROOT, report.layer.path));
  assert(sha(layerArchive) === report.layer.sha256 && layerArchive.length === report.layer.bytes, "layer archive");
  const layerRaw = zlib.gunzipSync(layerArchive);
  assert(sha(layerRaw) === report.layer.raw_sha256 && layerRaw.length === report.layer.raw_bytes, "layer raw");
  const layer = JSON.parse(layerRaw);
  assert(layer.schema === "conway99.f0.literal-cut-native-layer.v1", "layer schema");
  assert(layer.definition.source_sha256 === EXPECTED_PRODUCER && same(layer.definition, report.definition), "definition");
  const expectedInputs = Object.fromEntries([["rows", ROWS], ["specification", SPEC], ["preparation", PREP], ["cold", COLD], ["radix", RADIX]].map(([k, v]) => [k, {path:v[0], sha256:v[1]}]));
  assert(same(layer.definition.inputs, expectedInputs), "complete input bindings");
  assert(layer.definition.rows_raw_sha256 === ROWS[2] && layer.definition.specification_raw_sha256 === SPEC[2], "raw definition bindings");
  assert(layer.base_native_variables === OFFSET && layer.binary_offset === OFFSET && layer.binary_count === COUNT && layer.auxiliary_start === FIRST_AUX && layer.next_variable === 32296, "namespace");
  assert(layer.variables.length === 540 && layer.linear_constraints.length === 4920 && layer.cut_records.length === 4416, "inventory");
  assert(rows.length === 4416 && rows.reduce((n, r) => n + r.terms.length, 0) === 442308, "original inventory");
  const domains = spec.target_variable_domains.map(d => [BigInt(d[0]), BigInt(d[d.length-1])]);
  assert(domains.length === OFFSET, "parent domain inventory");
  for (let i = 0; i < layer.variables.length; i++) {
    const v = layer.variables[i];
    assert(v.id === OFFSET + i && Array.isArray(v.domain) && v.domain.length === 2, "variable ID/domain");
    const lo = BigInt(v.domain[0]), hi = BigInt(v.domain[1]);
    assert(lo <= hi && v.domain[0] === lo.toString() && v.domain[1] === hi.toString(), "canonical domain");
    if (i < COUNT) assert(v.kind === "literal" && v.selector === i && same(v.domain, ["0", "1"]), "literal Boolean domain");
    domains.push([lo, hi]);
  }
  for (let a = 0; a < COUNT; a++) {
    const inverse = spec.literal_inverse_rows[a];
    assert(inverse.selector === a && inverse.denominator === 12, "inverse identity");
    const expected = {terms:inverse.terms.map(([j,c]) => [j, String(c)]).concat([[OFFSET+a,"-12"]]), domain:["0","0"]};
    assert(same(layer.linear_constraints[a], expected), "literal inverse link " + a);
  }
  let linearOffset = COUNT, nextAux = FIRST_AUX, direct = 0, large = 0, satisfying = 0, violating = 0;
  const radixChecks = [];
  const patterns = [
    Array(COUNT).fill(0), Array(COUNT).fill(1),
    Array.from({length:COUNT}, (_,i) => i < 60 ? 1 : 0),
    Array.from({length:COUNT}, (_,i) => i % 2),
  ];
  for (let rowId = 0; rowId < rows.length; rowId++) {
    const original = rows[rowId], shifted = {terms:original.terms.map(([j,c]) => [OFFSET+j,c]), rhs:original.rhs};
    const rec = layer.cut_records[rowId];
    assert(rec.original_row_id === rowId && rec.original_row_sha256 === sha(api.canonical(original)) && rec.shifted_row_sha256 === sha(api.canonical(shifted)), "literal archive row binding");
    assert(rec.linear_offset === linearOffset && rec.first_auxiliary === nextAux, "ordered row/variable allocation");
    const coefficientBound = shifted.terms.reduce((n, [,c]) => n + abs(BigInt(c)), 0n) + abs(BigInt(shifted.rhs));
    if (coefficientBound <= SAFE) {
      direct++;
      assert((rowId < 4164 || rowId >= 4176) && rec.route === "direct" && rec.linear_count === 1 && rec.auxiliary_count === 0 && rec.radix_digits === 0, "direct route");
      const lower = shifted.terms.reduce((n, [,c]) => n + (BigInt(c) < 0n ? BigInt(c) : 0n), 0n);
      assert(same(layer.linear_constraints[linearOffset], {terms:shifted.terms, domain:[lower.toString(),shifted.rhs]}), "direct row exactness");
      linearOffset++;
    } else {
      large++;
      assert(rowId >= 4164 && rowId < 4176 && rec.route === "radix" && rec.linear_count === 3 && rec.auxiliary_count === 5 && rec.radix_digits === 3, "radix route");
      const options = {binaryCount:COUNT,binaryOffset:OFFSET,firstAux:nextAux,baseBits:30,maxDigits:128};
      const encoding = radix.encodeRow(shifted, options);
      encoding.linear_rows = layer.linear_constraints.slice(linearOffset,linearOffset+3).map((row,j) => ({limb:j,terms:row.terms,domain:row.domain}));
      encoding.auxiliary_variables = layer.variables.slice(nextAux-OFFSET,nextAux-OFFSET+5).map(v => {
        assert(v.row === rowId, "auxiliary original row");
        return {id:v.id,kind:v.kind,limb:v.limb,domain:v.domain};
      });
      radixChecks.push(radix.verifyEncoding(encoding, shifted, options));
      for (const values of patterns) {
        const activity = shifted.terms.reduce((n, [j,c]) => n + BigInt(c)*BigInt(values[j-OFFSET]), 0n);
        const result = radix.completeWitness(encoding, values);
        if (activity <= BigInt(shifted.rhs)) {
          assert(result.status === "EXACT_AUXILIARY_WITNESS", "missing actual-row witness"); satisfying++;
          radix.checkWitness(encoding, values, result.auxiliary_values);
        } else {
          assert(result.status === "ORIGINAL_ROW_VIOLATED" && result.auxiliary_values === null, "invalid actual-row witness"); violating++;
        }
      }
      linearOffset += 3; nextAux += 5;
    }
  }
  assert(direct === 4404 && large === 12 && linearOffset === 4920 && nextAux === 32296, "complete coverage");
  let maximumActivity = 0n, nativeTerms = 0;
  for (const row of layer.linear_constraints) {
    let lo = 0n, hi = 0n, absolute = 0n, previous = -1;
    for (const [j,text] of row.terms) {
      assert(Number.isSafeInteger(j) && j > previous && j < domains.length, "native ID uniqueness"); previous = j;
      const c = BigInt(text); assert(c !== 0n && c.toString() === text, "canonical native coefficient");
      const a = c*domains[j][0], b = c*domains[j][1];
      lo += a < b ? a : b; hi += a > b ? a : b; absolute += max(abs(a),abs(b)); nativeTerms++;
    }
    const bounds = row.domain.map(BigInt);
    assert(bounds[0] <= bounds[1] && bounds.map(String).join(",") === row.domain.join(","), "native linear domain");
    assert(lo >= -SAFE && hi <= SAFE && hi-lo <= (1n<<63n)-1n, "native activity bound");
    assert(absolute + max(...bounds.map(abs)) <= SAFE, "native absolute residual bound");
    maximumActivity = max(maximumActivity,absolute);
  }
  const domainSum = domains.reduce((n,[lo,hi]) => n + max(abs(lo),abs(hi),hi-lo), 0n);
  assert(domainSum < (1n<<63n)-1n, "whole model domain budget");
  assert(layer.arithmetic.maximum_new_sum_absolute_term_bounds === maximumActivity.toString() && layer.arithmetic.whole_final_variable_domain_sum === domainSum.toString(), "arithmetic metadata");
  assert(same(layer.counts,report.counts) && same(layer.arithmetic,report.arithmetic), "report metadata");
  const result = {
    schema:"conway99.f0.literal-layer-independent-replay.v1",
    status:"PASS: every literal cut and inverse link independently replayed",
    source_sha256:sha(fs.readFileSync(__filename)),producer_sha256:EXPECTED_PRODUCER,
    preparation_sha256:sha(reportRaw),layer_sha256:report.layer.sha256,layer_raw_sha256:report.layer.raw_sha256,
    literal_archive_sha256:ROWS[1],literal_archive_raw_sha256:ROWS[2],specification_sha256:SPEC[1],
    counts:{original_rows:4416,original_terms:442308,inverse_links:480,direct_rows:direct,radix_rows:large,radix_equalities:36,radix_auxiliaries:60,added_native_rows:4920,added_native_terms:nativeTerms,final_variables:domains.length},
    arithmetic:{maximum_sum_absolute_term_bounds:maximumActivity.toString(),whole_final_variable_domain_sum:domainSum.toString()},
    actual_radix_row_synthetic_patterns:{satisfying,violating,total:satisfying+violating,production_candidates:0},
    radix_contraction_checks:radixChecks.map(r => ({original_row_sha256:r.original_row_sha256,coefficients:r.weighted_original_coefficients_checked,carry_cancellations:r.internal_carry_cancellations_checked})),
    seconds:(Date.now()-started)/1000,optimizer_calls:0,native_model_built:false,
    native_model_validator_executed:false,
    scope:"Exact finite layer only. Native integration, candidate acceptance, exterior edges and unrestricted graph existence remain separate."
  };
  fs.writeFileSync(output,JSON.stringify(result,null,2)+"\n",{flag:"wx"});
  process.stdout.write(JSON.stringify({status:result.status,seconds:result.seconds})+"\n");
}
if (process.argv.length !== 4) throw Error("Usage: node literal_cut_layer_replay.js DIRECTORY OUTPUT");
main(path.resolve(process.argv[2]),path.resolve(process.argv[3]));
