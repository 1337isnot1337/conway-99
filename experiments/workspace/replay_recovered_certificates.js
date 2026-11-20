"use strict";
// Runs the already-reviewed finite checkers in fresh Node child processes.
// No solver, optimizer, dependency installation, or branch mutation.
const fs = require("node:fs");
const path = require("node:path");
const crypto = require("node:crypto");
const {spawnSync} = require("node:child_process");
const {isDeepStrictEqual} = require("node:util");
const root = path.resolve(__dirname, "../..");
const destination = process.argv[2];
if (!destination || fs.existsSync(destination)) throw new Error("A fresh output directory is required");
fs.mkdirSync(destination, {recursive: false});
const json = p => JSON.parse(fs.readFileSync(path.join(root, p), "utf8"));
const workspace = "experiments/workspace/";
const f0 = "experiments/logs/root-prism-free/";
const moments = "experiments/logs/moments-and-counts/";
const rook = "experiments/logs/session-ab2f/";
const point = moments + "prism-zero-order10-all-flags-x521-face-loop01-round0-rounded-counts.json";
const structuralInput = f0 + "f0-fractional-structural-recovery-input.json";
const motifInput = f0 + "f0-fractional-motif-recovery-input.json";
const interior = f0 + "f0-gram-interior-recovery-certificate.json";
const rookOutput = path.join(destination, "rook-gram-replay.json");
const cases = [
  {name: "core16", script: "high_graph_core16_recovery_check.js", args: []},
  {name: "f0-interior", script: "root_prism_free_f0_gram_interior_recovery.js", args: [], expected: interior},
  {name: "f0-structural", script: "root_prism_free_f0_fractional_structural_recovery.js", args: [structuralInput], expected: f0 + "f0-fractional-structural-recovery.json"},
  {name: "f0-baseline", script: "root_prism_free_f0_fractional_baseline_recovery.js", args: [structuralInput, motifInput, interior], expected: f0 + "f0-fractional-baseline-recovery.json"},
  {name: "root49-full", script: "root49_packing_moment_recovery_check.js",
   args: ["query", moments + "order10-root49-public-recovery-inputs.json",
     moments + "order10-high-mask-packing-other-roots-scope01.json", point],
   expected: moments + "order10-root49-packing-moment-recovery-result.json"},
  {name: "root49-independent", script: "root49_packing_moment_recovery_replay.js",
   args: [moments + "order10-root49-packing-moment-recovery-preparation.json",
     point, moments + "order10-root49-packing-moment-recovery-result.json"]},
  {name: "rook-gram", script: "rook_case4_gram_support_reconstruction.js",
   args: ["verify", rook + "rook-case4-gram-support-input.json",
     rook + "rook-case4-gram-support-result.json", rookOutput], resultFile: rookOutput},
  {name: "rook-maxmin-controls", script: "rook_case4_maxmin_certificate_controls.js", args: []}
];
const summary = {status: "RUNNING", node: process.version,
  commit: process.env.GITHUB_SHA || null, optimizer_calls: 0, records: []};
const summaryPath = path.join(destination, "summary.json");
const writeSummary = () => fs.writeFileSync(summaryPath, JSON.stringify(summary, null, 2) + "\n");
writeSummary();
for (const item of cases) {
  const sourcePath = workspace + item.script;
  const source = fs.readFileSync(path.join(root, sourcePath));
  const sha256 = crypto.createHash("sha256").update(source).digest("hex");
  const started = Date.now();
  const run = spawnSync(process.execPath, [sourcePath, ...item.args],
    {cwd: root, encoding: "utf8", timeout: 30000, maxBuffer: 4 * 1024 * 1024});
  if (run.status !== 0 || run.error) {
    summary.status = "FAILED";
    summary.records.push({name: item.name, source: sourcePath, sha256,
      status: run.status, signal: run.signal, error: String(run.error || ""),
      stderr: run.stderr, seconds: (Date.now() - started) / 1000});
    writeSummary();
    throw new Error("Checker failed: " + item.name);
  }
  const result = item.resultFile
    ? JSON.parse(fs.readFileSync(item.resultFile, "utf8")) : JSON.parse(run.stdout);
  if (item.expected && !isDeepStrictEqual(result, json(item.expected))) {
    summary.status = "FAILED_OUTPUT_MISMATCH";
    summary.records.push({name: item.name, source: sourcePath, sha256,
      expected: item.expected});
    fs.writeFileSync(path.join(destination, item.name + "-actual.json"), JSON.stringify(result, null, 2) + "\n");
    writeSummary();
    throw new Error("Frozen artifact differs: " + item.name);
  }
  if (!item.resultFile) fs.writeFileSync(path.join(destination, item.name + ".json"),
    JSON.stringify(result, null, 2) + "\n");
  const record = {name: item.name, source: sourcePath, sha256,
    seconds: (Date.now() - started) / 1000, status: "PASS",
    frozen_artifact_compared: item.expected || null};
  summary.records.push(record);
  writeSummary();
  process.stdout.write(JSON.stringify(record) + "\n");
}
summary.status = "PASS";
summary.checkers = cases.length;
writeSummary();
process.stdout.write("CONWAY99_RECOVERY_SUMMARY_BEGIN\n" + JSON.stringify(summary) +
  "\nCONWAY99_RECOVERY_SUMMARY_END\n");
