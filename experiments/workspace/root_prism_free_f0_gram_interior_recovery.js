"use strict";

/* Exact recovery of the F0 base Gram interior point.
 * Run with Node from any directory. Only standard Node modules are needed.
 * The pure checkF0Interior function is also executable in a plain JS runtime.
 */
function checkF0Interior(inputs) {
  const expected = {
    "f0-exterior-row-domains02.json.gz": "665563b75fa6fc23caa9a002621cc4047809af28543b52b5c2a7ffa592d05dd4",
    "f0-quadratic-allocation-preparation.json.gz": "7ab2ec935cdbbb7035a0fd95d5a7ca514aed508b7d5efbe953c5265176733589"
  };
  function check(ok, message) { if (!ok) throw new Error(message); }
  function same(a, b) { return JSON.stringify(a) === JSON.stringify(b); }
  function popcount(value) {
    let count = 0;
    while (value) { value &= value - 1; count++; }
    return count;
  }
  for (const name of Object.keys(expected)) {
    check(inputs[name].sha256 === expected[name], "input digest binding");
  }
  const domain = inputs["f0-exterior-row-domains02.json.gz"].data;
  const prepared = inputs["f0-quadratic-allocation-preparation.json.gz"].data;
  const core = domain.component_core_rows;
  check(same(core, prepared.component_core_rows) && core.length === 21, "core identity");
  check(core.every(row => Number.isInteger(row) && row >= 0 && row < 2 ** 21), "core row range");
  for (let i = 0; i < 21; i++) {
    check(!(core[i] >> i & 1), "core diagonal");
    for (let j = 0; j < 21; j++) {
      check((core[i] >> j & 1) === (core[j] >> i & 1), "core symmetry");
    }
  }
  const adjacency = core.slice(3).map(row => row >> 3 & ((1 << 18) - 1));
  const gram = Array.from({length: 18}, (_, i) =>
    Array.from({length: 18}, (_, j) =>
      12 * Number(i === j) + 2 - popcount(core[3+i] & core[3+j]) -
      (core[3+i] >> (3+j) & 1)));
  const triples = [];
  for (let a = 0; a < 18; a++) for (let b = a+1; b < 18; b++) for (let c = b+1; c < 18; c++) {
    const h = [a, b, c];
    if ([0, 1, 2].some(f => h.filter(i => Math.floor(i/6) === f).length > 2)) continue;
    if (gram[a][b] === 0 || gram[a][c] === 0 || gram[b][c] === 0) continue;
    if (adjacency.some((row, i) => h.reduce((s, j) => s + Number(i === j || (row >> j & 1)), 0) > 2)) continue;
    triples.push(h);
  }
  check(triples.length === 480 && same(triples, domain.signature_domain) &&
    same(triples, prepared.signature_domain), "complete triple domain");
  const motifs = domain.motif_pairs;
  check(motifs.length === 90 && motifs.every(([a,b]) => Number.isInteger(a) &&
    Number.isInteger(b) && 0 <= a && a < b && b < 480), "motif pairs");
  const actions = prepared.verified_core_actions;
  const range = n => Array.from({length:n}, (_,i) => i);
  check(actions.length === 12, "action count");
  check(new Set(actions.map(a => a.signature_image.join(","))).size === 12, "distinct actions");
  const positions = new Map(triples.map((h,a) => [h.join(","), a]));
  for (const action of actions) {
    const move = action.component_image, image = action.signature_image;
    check(same([...move].sort((a,b) => a-b), range(18)), "component permutation");
    check(same([...image].sort((a,b) => a-b), range(480)), "signature permutation");
    for (let a = 0; a < 480; a++) {
      check(image[a] === positions.get(triples[a].map(i => move[i]).sort((a,b) => a-b).join(",")),
        "signature transport");
    }
    for (let i = 0; i < 18; i++) for (let j = 0; j < 18; j++) {
      check(gram[i][j] === gram[move[i]][move[j]], "Gram transport");
    }
  }
  const candidates = prepared.saved_candidates;
  check(candidates.length === 153, "saved incidence count");
  const counts = Array(480).fill(0), samples = new Set();
  let denominator = 0;
  for (const candidate of candidates) {
    const selected = candidate.selected_signature_ids;
    check(selected.length === 60 && new Set(selected).size === 60 &&
      selected.every(a => Number.isInteger(a) && a >= 0 && a < 480), "saved selector range");
    for (const action of actions) {
      const image = selected.map(a => action.signature_image[a]).sort((a,b) => a-b);
      const chosen = new Set(image);
      check(chosen.size === 60, "transported selector count");
      check(motifs.every(([a,b]) => !(chosen.has(a) && chosen.has(b))), "binary motif condition");
      const observed = Array.from({length:18}, () => Array(18).fill(0));
      for (const a of image) {
        counts[a]++;
        for (const i of triples[a]) for (const j of triples[a]) observed[i][j]++;
      }
      check(same(observed, gram), "literal transported Gram identity");
      samples.add(image.join(","));
      denominator++;
    }
  }
  check(denominator === 1836 && samples.size === 1836, "complete distinct incidence average");
  const minimum = Math.min(...counts), maximum = Math.max(...counts);
  check(minimum === 24 && maximum === 851 && maximum < denominator, "strict coordinate bounds");
  check(counts.reduce((a,b) => a+b, 0) === 60 * denominator, "population equality");
  const weighted = Array.from({length:18}, () => Array(18).fill(0));
  for (let a = 0; a < 480; a++) for (const i of triples[a]) for (const j of triples[a]) {
    weighted[i][j] += counts[a];
  }
  check(same(weighted, gram.map(row => row.map(v => denominator * v))), "direct rational Gram identity");
  const motifSlacks = motifs.map(([a,b]) => denominator - counts[a] - counts[b]);
  check(Math.min(...motifSlacks) === 1505 && Math.max(...motifSlacks) === 1711, "strict motif slacks");
  return {
    status: "PASS: exact base Gram interior point recovered from published inputs",
    checker: "experiments/workspace/root_prism_free_f0_gram_interior_recovery.js",
    input_sha256: expected,
    conditional_scope: "F0 component 0, base Gram and motif constraints only",
    directly_checked_binary_incidences: denominator,
    distinct_binary_incidences: samples.size,
    numerators: counts,
    common_denominator: denominator,
    minimum_coordinate: "2/153",
    maximum_coordinate: "851/1836",
    checked_gram_equalities: 171,
    checked_motif_inequalities: 90,
    minimum_motif_slack_numerator: Math.min(...motifSlacks),
    maximum_motif_slack_numerator: Math.max(...motifSlacks),
    base_constraints_cannot_fix_any_selector: true,
    later_capacity_constraints_checked: false,
    optimizer_called: false,
    graph_constructed_or_component_excluded: false
  };
}

if (typeof module !== "undefined") module.exports = {checkF0Interior};
if (typeof require !== "undefined" && require.main === module) {
  const fs = require("node:fs"), path = require("node:path");
  const zlib = require("node:zlib"), crypto = require("node:crypto");
  const root = path.resolve(__dirname, "../..");
  const names = ["f0-exterior-row-domains02.json.gz", "f0-quadratic-allocation-preparation.json.gz"];
  const inputs = {};
  for (const name of names) {
    const raw = fs.readFileSync(path.join(root, "experiments/logs/root-prism-free", name));
    inputs[name] = {sha256: crypto.createHash("sha256").update(raw).digest("hex"),
      data: JSON.parse(zlib.gunzipSync(raw).toString("utf8"))};
  }
  process.stdout.write(JSON.stringify(checkF0Interior(inputs), null, 2) + "\n");
}
