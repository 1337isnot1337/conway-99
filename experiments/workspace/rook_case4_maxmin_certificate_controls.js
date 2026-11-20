"use strict";
// Exact finite-box max-min certificates and exhaustive tiny controls.
// Run with: node rook_case4_maxmin_certificate_controls.js
// No dependencies, optimizer, case4 data, or filesystem access.

function invariant(ok, message) {
  if (!ok) throw new Error(message);
}

function exactUpperBound(C, lower, upper, lambda, gamma, objectiveColumn) {
  // All arithmetic in the general certificate is arbitrary-precision integer.
  const m = C.length, n = C[0].length;
  invariant(lower.length === m && upper.length === m && lambda.length === m, "row dimensions");
  invariant(Number.isInteger(objectiveColumn) && objectiveColumn >= 0 && objectiveColumn < n, "objective column");
  const g = BigInt(gamma);
  invariant(g >= 0n, "nonnegative objective multiplier");
  const c = Array(n).fill(0n);
  let endpoint = 0n;
  for (let i = 0; i < m; i++) {
    invariant(C[i].length === n, "matrix dimensions");
    const l = BigInt(lower[i]), u = BigInt(upper[i]), k = BigInt(lambda[i]);
    invariant(l <= u, "finite ordered row bounds");
    endpoint += k * (k >= 0n ? u : l);
    for (let j = 0; j < n; j++) c[j] += k * BigInt(C[i][j]);
  }
  const residual = c.map((value, j) => (j === objectiveColumn ? g : 0n) - value);
  const bound = endpoint + residual.reduce((sum, value) => sum + (value > 0n ? value : 0n), 0n);
  return {gamma: g, columnCoefficients: c, residual, rowEndpointSum: endpoint, bound};
}

function runExactControls() {
  let checked = 0, certificates = 0, forcedFacts = 0, decompositionChecks = 0;
  // Tiny-control arithmetic below is integral: points are doubled, all
  // coefficients lie in {-1,0,1}, and every intermediate has magnitude <100.
  for (let a = -1; a <= 1; a++) for (let b = -1; b <= 1; b++)
  for (let L = -2; L <= 2; L++) for (let U = L; U <= 2; U++) {
    const C = [[a,b,0],[1,0,-1],[0,1,-1]], lo = [L,0,0], hi = [U,1,1];
    const feasible = [];
    for (let x = 0; x <= 2; x++) for (let y = 0; y <= 2; y++) for (let t = 0; t <= 2; t++) {
      const z = [x,y,t], Az = C.map(row => row.reduce((s,c,j) => s+c*z[j],0));
      if (Az.every((v,i) => 2*lo[i] <= v && v <= 2*hi[i])) feasible.push({z,Az});
    }
    for (let l0 = -1; l0 <= 1; l0++) for (let l1 = -1; l1 <= 1; l1++) for (let l2 = -1; l2 <= 1; l2++)
    for (let gamma = 0; gamma <= 2; gamma++) {
      const lambda = [l0,l1,l2];
      const ub = lambda.reduce((s,l,i) => s+l*(l>=0?hi[i]:lo[i]),0);
      const c = [0,0,0];
      for (let i=0;i<3;i++) for (let j=0;j<3;j++) c[j] += lambda[i]*C[i][j];
      const r = c.map((v,j) => (j===2?gamma:0)-v);
      const B = ub+r.reduce((s,v) => s+Math.max(v,0),0);
      const big = exactUpperBound(C,lo,hi,lambda,gamma,2);
      invariant(big.bound === BigInt(B) && big.residual.every((v,j)=>v===BigInt(r[j])), "BigInt/finite control agreement");
      checked++;
      for (const {z,Az} of feasible) {
        const rowSlacks = lambda.map((l,i)=>2*l*(l>=0?hi[i]:lo[i])-l*Az[i]);
        const colSlacks = r.map((v,j)=>2*Math.max(v,0)-v*z[j]);
        const sum = [...rowSlacks,...colSlacks].reduce((s,v)=>s+v,0);
        invariant(sum===2*B-gamma*z[2], "exact slack identity");
        invariant([...rowSlacks,...colSlacks].every(v=>v>=0), "nonnegative endpoint slacks");
        invariant(gamma*z[2]<=2*B, "objective upper bound");
        decompositionChecks++;
        if (gamma>0 && B===0 && z[2]===0) {
          for (let j=0;j<2;j++) {
            if (lambda[j+1]<0) { invariant(z[j]===0, "extension zero"); forcedFacts++; }
            if (lambda[j+1]>0) { invariant(z[j]===2, "extension one"); forcedFacts++; }
            if (r[j]<0) { invariant(z[j]===0, "bound zero"); forcedFacts++; }
            if (r[j]>0) { invariant(z[j]===2, "bound one"); forcedFacts++; }
          }
          invariant(r[2]<=0, "positive t residual contradicts original feasibility");
          invariant(lambda[1]+lambda[2]<0, "zero optimum exposes a selector zero");
        }
      }
      if (gamma>0 && B===0) certificates++;
    }
  }
  invariant(checked===10935 && decompositionChecks===75006 && certificates===172 && forcedFacts===100, "complete tiny-domain coverage");
  const C = [[1,1,0],[1,0,-1],[0,1,-1]];
  const half = exactUpperBound(C,[1,0,0],[1,1,1],[1,-1,-1],2,2);
  invariant(half.bound===1n, "sharp two-times-t bound");
  const zero = exactUpperBound(C,[0,0,0],[0,1,1],[1,-1,-1],2,2);
  invariant(zero.bound===0n, "two selector zero face");
  const empty = exactUpperBound([[1,1,0]],[3],[3],[-1],0,2);
  invariant(empty.bound===-1n && empty.rowEndpointSum===-3n, "finite upper-bound Farkas control");
  return {
    status:"PASS",
    scope:"exact finite-box algebra controls only; no case4 model, optimizer, or exclusion",
    certificate_candidates:checked,
    feasible_point_decompositions_checked:decompositionChecks,
    zero_bound_objective_certificates:certificates,
    exact_forced_literal_checks:forcedFacts,
    arbitrary_precision_formula_matches_all_tiny_candidates:true,
    positive_t_residual_and_negative_extension_sum_controls:true,
    analytic_controls:["2t<=1 for x1+x2=1","2t<=0 and both selectors0 for x1+x2=0","finite-box Farkas gap-1 for x1+x2>=3"],
    optimizer_calls:0
  };
}

const result = runExactControls();
if (typeof module !== "undefined") module.exports = {exactUpperBound,runExactControls};
if (typeof console !== "undefined") console.log(JSON.stringify(result,null,2));
