(() => {
"use strict";
// Exhaustive tiny controls for the integer-to-mod4 lifting theorem.
// No Conway99 matrix, branch, optimizer, native module, or main GF(2) run.
const started = Date.now();
const deadline = started + 20000;
function insist(condition, message) { if (!condition) throw Error(message); }
function mod(x, q) { return ((x % q) + q) % q; }
function dot(a, b) { return a.reduce((s, x, i) => s + x * b[i], 0); }
function digits(value, count, radix) {
  const result = [];
  for (let i = 0; i < count; i++) { result.push(value % radix); value = Math.floor(value / radix); }
  return result;
}
function vector(mask, count) { return Array.from({length: count}, (_, i) => (mask >>> i) & 1); }
function equal(a, b) { return JSON.stringify(a) === JSON.stringify(b); }
function span(rows) {
  let values = [0];
  for (const row of rows) values = [...new Set(values.concat(values.map(x => x ^ row)))];
  return values.sort((a, b) => a - b);
}
function leftKernel(A) {
  const m = A.length, n = A[0].length, result = [];
  for (let mask = 0; mask < (1 << m); mask++) {
    const v = vector(mask, m);
    if (Array.from({length: n}, (_, j) => mod(dot(v, A.map(row => row[j])), 2)).every(x => x === 0)) result.push(mask);
  }
  return result;
}
function everyOrderedBasis(kernel) {
  const dimension = Math.log2(kernel.length), output = [];
  insist(Number.isInteger(dimension), "Kernel cardinality is not a power of two.");
  function visit(rows) {
    if (rows.length === dimension) { insist(equal(span(rows), kernel), "Incomplete basis."); output.push(rows); return; }
    const old = new Set(span(rows));
    for (const v of kernel) if (!old.has(v)) visit(rows.concat(v));
  }
  visit([]);
  return output;
}
function substitute(A, b, state) {
  const free = state.map((v, i) => v === -1 ? i : -1).filter(i => i >= 0);
  return {
    A: A.map(row => free.map(j => row[j])),
    b: b.map((rhs, i) => rhs - A[i].reduce((s, c, j) => s + (state[j] === -1 ? 0 : c * state[j]), 0)),
    free
  };
}
function baseResidues(A, b) {
  const n = A[0].length, answer = [];
  for (let mask = 0; mask < (1 << n); mask++) {
    const y = vector(mask, n);
    if (A.every((row, i) => mod(dot(row, y) - b[i], 2) === 0)) answer.push(mask);
  }
  return answer;
}
function halfRows(A, b, basis) {
  const m = A.length, n = A[0].length, rows = [];
  for (const mask of basis) {
    const v = vector(mask, m);
    const coefficient = Array.from({length: n}, (_, j) => dot(v, A.map(row => row[j])));
    insist(coefficient.every(c => mod(c, 2) === 0), "Vector is outside the left kernel.");
    const rhs = dot(v, b);
    if (mod(rhs, 2) !== 0) return {baseContradiction: true, witness: mask, rows: []};
    rows.push({coefficients: coefficient.map(c => c / 2), rhs: rhs / 2, witness: mask});
  }
  return {baseContradiction: false, rows};
}
function liftedResidues(A, b, basis, requireBase = true) {
  const half = halfRows(A, b, basis), n = A[0].length;
  if (half.baseContradiction) return [];
  const candidates = requireBase ? baseResidues(A, b) : Array.from({length: 1 << n}, (_, i) => i);
  return candidates.filter(mask => {
    const y = vector(mask, n);
    return half.rows.every(row => mod(dot(row.coefficients, y) - row.rhs, 2) === 0);
  });
}
let directAssignments = 0;
function directResidues(A, b, counted = false) {
  const n = A[0].length, answer = new Set();
  for (let encoded = 0; encoded < 4 ** n; encoded++) {
    if (counted) directAssignments++;
    const z = digits(encoded, n, 4);
    if (A.every((row, i) => mod(dot(row, z) - b[i], 4) === 0))
      answer.add(z.reduce((mask, value, i) => mask | ((value % 2) << i), 0));
  }
  return [...answer].sort((a, b) => a - b);
}
let systemBoxes = 0, basisChecks = 0, inconsistentBase = 0, changedRepresentativeChecks = 0;
const dimensions = [];
for (let m = 1; m <= 2; m++) for (let n = 1; n <= 2; n++) {
  let here = 0;
  for (let code = 0; code < 4 ** (m * n + m); code++) {
    if ((code & 63) === 0) insist(Date.now() < deadline, "Toy control deadline.");
    const values = digits(code, m * n + m, 4);
    const A = Array.from({length: m}, (_, i) => values.slice(i * n, (i + 1) * n));
    const b = values.slice(m * n);
    for (let stateCode = 0; stateCode < 3 ** n; stateCode++) {
      const state = digits(stateCode, n, 3).map(v => v - 1);
      const reduced = substitute(A, b, state), B = reduced.A, d = reduced.b;
      const base = baseResidues(B, d), kernel = leftKernel(B), bases = everyOrderedBasis(kernel);
      const exact = directResidues(B, d, true);
      if (base.length === 0) inconsistentBase++;
      for (const basis of bases) {
        const obtained = liftedResidues(B, d, basis);
        insist(equal(obtained, exact), "Lifting theorem failed.");
        if (base.length === 0) insist(halfRows(B, d, basis).baseContradiction, "Missing parity contradiction.");
        basisChecks++;
        // Replace a canonical binary witness v by v+2q. Half rows can change,
        // but their value modulo2 is unchanged on every base-parity residue.
        if (base.length !== 0) for (const witness of basis) {
          const v = vector(witness, m);
          for (let qMask = 0; qMask < (1 << m); qMask++) {
            const q = vector(qMask, m), lifted = v.map((x, i) => x + 2 * q[i]);
            for (const yMask of base) {
              const y = vector(yMask, B[0].length), residual = B.map((row, i) => dot(row, y) - d[i]);
              insist(residual.every(x => mod(x, 2) === 0), "Base parity lost.");
              insist(mod(dot(v, residual) / 2, 2) === mod(dot(lifted, residual) / 2, 2), "Integer-lift representative dependence.");
              changedRepresentativeChecks++;
            }
          }
        }
      }
      systemBoxes++; here++;
    }
  }
  dimensions.push({rows: m, originalVariables: n, branchSubstitutions: here});
}
insist(systemBoxes === 38256 && directAssignments === 151392, "Incomplete exhaustive census.");
const named = [];
function fixture(name, A, b, state, expected) {
  const r = substitute(A, b, state), bases = everyOrderedBasis(leftKernel(r.A));
  const exact = directResidues(r.A, r.b);
  insist(equal(exact, expected), "Unexpected fixture result.");
  for (const basis of bases) insist(equal(liftedResidues(r.A, r.b, basis), exact), "Fixture lifting failure.");
  named.push({name, A, b, fixedState: state, freeCoordinates: r.free, baseResidues: baseResidues(r.A, r.b), mod4LiftableResidues: exact});
}
fixture("even equation supplies a new parity unit", [[2]], [2], [-1], [1]);
fixture("mod2 consistent but mod4 impossible", [[4]], [2], [-1], []);
fixture("odd RHS prevents legal halving", [[2]], [1], [-1], []);
fixture("a fixed Boolean zero is substituted exactly", [[1]], [2], [0], []);
fixture("signed coefficients and integer division", [[-1, 1], [1, 1]], [0, 2], [-1, -1], [3]);
fixture("mod4 compatible does not mean Boolean feasible", [[1]], [2], [-1], [0]);
const A = [[1], [1], [3]], b = [0, 0, 0];
insist(equal(leftKernel(A), [0, 3, 5, 6]), "Basis-choice example kernel.");
insist(equal(liftedResidues(A, b, [3, 5], false), [0]), "First half-only example.");
insist(equal(liftedResidues(A, b, [5, 6], false), [0, 1]), "Second half-only example.");
insist(equal(liftedResidues(A, b, [3, 5]), [0]) && equal(liftedResidues(A, b, [5, 6]), [0]), "Base equations must restore basis independence.");
const incompleteA = [[2, 0], [0, 2]], incompleteB = [0, 2];
insist(equal(liftedResidues(incompleteA, incompleteB, [1]), [0, 2]), "Incomplete basis fixture.");
insist(equal(liftedResidues(incompleteA, incompleteB, [1, 2]), [2]), "Complete basis fixture.");
return {
  status: "PASS_EXHAUSTIVE_TINY_MOD4_LIFTING_AND_BRANCH_SUBSTITUTION_CONTROLS",
  dimensions, systemBoxes, directMod4Assignments: directAssignments, orderedKernelBasisChecks: basisChecks,
  inconsistentBaseParityCases: inconsistentBase, changedIntegerWitnessRepresentativeChecks: changedRepresentativeChecks,
  allResiduesModulo4OfAAndbCoveredInDeclaredDimensions: true,
  namedControls: named,
  failureOfHalfOnlyBasisIndependence: {A, b, firstBasis: [3, 5], firstHalfOnlyResidues: [0], secondBasis: [5, 6], secondHalfOnlyResidues: [0, 1], bothWithBaseResidues: [0]},
  incompleteKernelBasisCounterexample: {A: incompleteA, b: incompleteB, incompleteBasis: [1], admittedResidues: [0, 2], completeBasis: [1, 2], trueResidues: [2]},
  scope: "Tiny dimension-at-most-two systems plus named fixtures only; no Conway99 matrix or branch was read.",
  GaussianEliminationCalls: 0, nativeCalls: 0, optimizerCalls: 0, case187Calls: 0,
  elapsedMilliseconds: Date.now() - started
};
})()
