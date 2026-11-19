"use strict";

// Exact baseline preparation and rational primary inspector. No optimizer.
// The terminal selector-cut registry is deliberately not part of this baseline.

function completeF0FractionalBaseline(structure,motifInput,sha256Ascii) {
  const check=(ok,m)=>{if(!ok)throw new Error(m);};
  const hash=x=>sha256Ascii(JSON.stringify(x));
  const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
  check(hash(structure)==="5b2a8715c9cad3217b72479dd12c733f5b8b73d878cbb70df154167b7e386525","frozen structural specification");
  check(motifInput.source_sha256==="665563b75fa6fc23caa9a002621cc4047809af28543b52b5c2a7ffa592d05dd4","published motif binding");
  const motifs=motifInput.motif_pairs;
  check(motifs.length===90&&motifs.every(p=>p.length===2&&p.every(Number.isSafeInteger)&&0<=p[0]&&p[0]<p[1]&&p[1]<480),"motif domain");
  const motifIndex=new Map(motifs.map((p,i)=>[p.join(","),i]));check(motifIndex.size===90,"distinct motifs");
  const tripleIndex=new Map(structure.triples.map((p,i)=>[p.join(","),i]));
  const signatureActions=structure.core_actions.map(g=>structure.triples.map(h=>{
    const image=h.map(i=>g[i+3]-3).sort((a,b)=>a-b),result=tripleIndex.get(image.join(","));
    check(result!==undefined,"signature action");return result;
  }));
  const motifActions=signatureActions.map(g=>motifs.map(([a,b])=>{
    const p=[g[a],g[b]].sort((a,b)=>a-b),result=motifIndex.get(p.join(","));
    check(result!==undefined,"complete literal motif closure");return result;
  }));
  const motifOrbitIds=Array(90).fill(-1),motifOrbits=[];
  for(let i=0;i<90;i++)if(motifOrbitIds[i]<0){
    const group=[...new Set(motifActions.map(g=>g[i]))].sort((a,b)=>a-b),id=motifOrbits.length;
    for(const j of group){check(motifOrbitIds[j]<0,"motif orbit disjointness");motifOrbitIds[j]=id;}
    motifOrbits.push(group);
  }
  for(const g of motifActions)for(let i=0;i<90;i++)check(motifOrbitIds[i]===motifOrbitIds[g[i]],"motif orbit closure");
  const fixed=motifActions.map(g=>g.reduce((s,j,i)=>s+Number(i===j),0));
  check(fixed.reduce((s,x)=>s+x,0)===12*motifOrbits.length,"motif Burnside");
  const selectorOrbit=Array(480);
  structure.selector_orbits.forEach((group,o)=>group.forEach(a=>selectorOrbit[a]=o));
  const motifRows=[],motifRowIds=[],motifRowLookup=new Map();
  for(const[a,b]of motifs){
    const oa=selectorOrbit[a],ob=selectorOrbit[b];
    const row=oa===ob?[[oa,2]]:[[oa,1],[ob,1]].sort((a,b)=>a[0]-b[0]);
    const key=JSON.stringify(row);
    if(!motifRowLookup.has(key)){motifRowLookup.set(key,motifRows.length);motifRows.push(row);}
    motifRowIds.push(motifRowLookup.get(key));
  }
  for(const group of motifOrbits)check(new Set(group.map(i=>motifRowIds[i])).size===1,"literal motif quotient");
  const equalities=[],gramToEquality=[],mixedToEquality=[];
  for(const row of structure.gram_rows){
    if(row.terms.length===0){check(row.rhs===0,"zero Gram row");gramToEquality.push(-1);}
    else{gramToEquality.push(equalities.length);equalities.push({terms:row.terms,rhs:row.rhs,family:"Gram"});}
  }
  const populationEquality=equalities.length;
  equalities.push({terms:structure.population,rhs:60,family:"population"});
  for(const row of structure.mixed_rows){
    if(row.length===0)mixedToEquality.push(-1);
    else{mixedToEquality.push(equalities.length);equalities.push({terms:row,rhs:0,family:"mixed"});}
  }
  const inequalities=structure.activation_rows.map(terms=>({terms,rhs:0,family:"activation"}));
  const motifOffset=inequalities.length;
  for(const terms of motifRows)inequalities.push({terms,rhs:1,family:"motif"});
  const variables=structure.selector_orbits.length+structure.edge_orbits.length;
  for(const row of [...equalities,...inequalities]){
    check(row.terms.every(([j,c])=>Number.isSafeInteger(j)&&0<=j&&j<variables&&Number.isSafeInteger(c)&&c!==0),"matrix integers");
    check(row.terms.every(([j],i)=>i===0||row.terms[i-1][0]<j),"matrix sorted unique columns");
  }
  const matrix={variables,equalities,inequalities,lower:0,upper:1};
  const coverage={
    gram_full_to_equality:structure.gram_row_ids.map(i=>gramToEquality[i]),
    population_equality:populationEquality,
    mixed_full_to_equality:structure.mixed_row_ids.map(i=>mixedToEquality[i]),
    activation_full_to_inequality:structure.activation_ids,
    motif_full_to_inequality:motifRowIds.map(i=>motifOffset+i)
  };
  for(let control=0;control<4;control++){
    const z=Array.from({length:variables},(_,j)=>(13*j+7+control*19)%29);
    for(let i=0;i<90;i++){
      const[a,b]=motifs[i],direct=z[selectorOrbit[a]]+z[selectorOrbit[b]];
      const row=inequalities[coverage.motif_full_to_inequality[i]];
      check(direct===row.terms.reduce((s,[j,c])=>s+c*z[j],0),"full/quotient motif evaluation");
    }
  }
  const specification={structural_specification_sha256:hash(structure),motif_pairs:motifs,motif_orbits:motifOrbits,motif_rows:motifRows,coverage,matrix};
  const histogram={};for(const o of motifOrbits)histogram[o.length]=(histogram[o.length]||0)+1;
  const report={
    status:"PASS: complete structural plus motif baseline prepared; terminal selector cuts not included",
    scope:"Necessary fractional first-component-zero model in the global prism-free/F-free split-shell stratum; no second incidence fixed",
    motif_input_git_blob:"41b0f73b9f6a0061d49859fbd4e32564cea2db17",
    motif_source_sha256:motifInput.source_sha256,
    counts:{variables,selector_orbits:42,edge_orbits:5805,full_equalities:8812,full_inequalities:136878,full_rows:145690,quotient_equalities:equalities.length,quotient_inequalities:inequalities.length,quotient_rows:equalities.length+inequalities.length,full_motif_rows:90,motif_orbits:motifOrbits.length,literal_motif_rows:motifRows.length,equality_nonzeros:equalities.reduce((s,r)=>s+r.terms.length,0),inequality_nonzeros:inequalities.reduce((s,r)=>s+r.terms.length,0)},
    motif_orbit_histogram:histogram,
    motif_burnside_fixed_points:fixed,
    controls:{all_1080_literal_motif_transports_checked:true,literal_rational_motif_evaluation_checks:360,all_full_rows_have_explicit_quotient_maps:true},
    bindings:{motif_pairs_sha256:hash(motifs),motif_orbits_sha256:hash(motifOrbits),matrix_sha256:hash(matrix),coverage_sha256:hash(coverage),baseline_specification_sha256:hash(specification)},
    limitations:{earlier_12_weighted_cuts_included:false,terminal_4404_selector_cuts_included:false,equivalence_to_Boolean_normalized_cut_registry_claimed:false,optimizer_called:false,feasible_shared_point_found:false,component_excluded:false}
  };
  return {specification,report};
}

function inspectF0FractionalBaseline(structure,baseline,point) {
  const check=(ok,m)=>{if(!ok)throw new Error(m);};
  const den=BigInt(point.denominator);check(den>0n,"positive rational denominator");
  const nums=point.numerators.map(BigInt),nx=structure.selector_orbits.length,nv=nx+structure.edge_orbits.length;
  check(nums.length===nv,"quotient point width");
  const selectorOrbit=Array(480),edgeOrbit=Array(structure.edges.length);
  structure.selector_orbits.forEach((g,o)=>g.forEach(a=>selectorOrbit[a]=o));
  structure.edge_orbits.forEach((g,o)=>g.forEach(e=>edgeOrbit[e]=o));
  const x=selectorOrbit.map(o=>nums[o]),y=edgeOrbit.map(o=>nums[nx+o]);
  const fail={bounds:0,Gram:0,population:0,mixed:0,activation:0,motif:0};
  for(const n of [...x,...y])if(n<0n||n>den)fail.bounds++;
  const gram=Array.from({length:18},()=>Array(18).fill(0n));
  structure.triples.forEach((h,a)=>{for(const i of h)for(const j of h)gram[i][j]+=x[a];});
  function pop(n){let k=0;while(n){n&=n-1;k++;}return k;}
  for(let i=0;i<18;i++)for(let j=i;j<18;j++){
    const q=12*Number(i===j)+2-pop(structure.core[i+3]&structure.core[j+3])-(structure.core[i+3]>>(j+3)&1);
    if(gram[i][j]!==BigInt(q)*den)fail.Gram++;
  }
  if(x.reduce((s,z)=>s+z,0n)!==60n*den)fail.population++;
  const mixed=Array.from({length:480},()=>Array(18).fill(0n));
  structure.edges.forEach(([a,b],e)=>{
    for(const i of structure.triples[b])mixed[a][i]+=y[e];
    for(const i of structure.triples[a])mixed[b][i]+=y[e];
    if(y[e]>x[a])fail.activation++;if(y[e]>x[b])fail.activation++;
  });
  for(let a=0;a<480;a++)for(let i=0;i<18;i++)if(mixed[a][i]!==BigInt(structure.targets[a][i])*x[a])fail.mixed++;
  for(const[a,b]of baseline.motif_pairs)if(x[a]+x[b]>den)fail.motif++;
  let eqFail=0,ineqFail=0,quotientBoundFail=0;
  for(const n of nums)if(n<0n||n>den)quotientBoundFail++;
  for(const row of baseline.matrix.equalities)if(row.terms.reduce((s,[j,c])=>s+BigInt(c)*nums[j],0n)!==BigInt(row.rhs)*den)eqFail++;
  for(const row of baseline.matrix.inequalities)if(row.terms.reduce((s,[j,c])=>s+BigInt(c)*nums[j],0n)>BigInt(row.rhs)*den)ineqFail++;
  const fullPass=Object.values(fail).every(v=>v===0),quotientPass=eqFail+ineqFail+quotientBoundFail===0;
  check(fullPass===quotientPass,"literal full versus quotient feasibility");
  return {status:fullPass?"PASS: exact fractional baseline point":"FAIL: point does not satisfy fractional baseline",full_violation_counts:fail,quotient_violation_counts:{equalities:eqFail,inequalities:ineqFail,bounds:quotientBoundFail},full_rows_checked:145690,full_variable_bounds_checked:68874,quotient_rows_checked:baseline.matrix.equalities.length+baseline.matrix.inequalities.length};
}

function checkF0BaselineInteriorProjection(structure,baseline,certificate) {
  const check=(ok,m)=>{if(!ok)throw new Error(m);};
  check(certificate.common_denominator===1836&&certificate.numerators.length===480,"known interior control");
  const nums=structure.selector_orbits.map(group=>{
    const n=certificate.numerators[group[0]];check(group.every(a=>certificate.numerators[a]===n),"interior is invariant");return String(n);
  });
  nums.push(...Array(structure.edge_orbits.length).fill("0"));
  const result=inspectF0FractionalBaseline(structure,baseline,{numerators:nums,denominator:"1836"});
  const f=result.full_violation_counts;
  check(f.bounds===0&&f.Gram===0&&f.population===0&&f.activation===0&&f.motif===0,"positive selector projection");
  check(f.mixed===7884&&result.quotient_violation_counts.equalities===667,"zero-edge negative control");
  return {status:"PASS: exact positive selector projection and rejected zero-edge extension",interior_certificate_git_blob:"6396da7dd3d5fd1df30a88cc3ea847154d62ef38",selector_denominator:1836,selector_bounds_Gram_population_and_90_motifs_pass:true,zero_edge_extension_full_mixed_failures:7884,zero_edge_extension_quotient_mixed_failures:667,feasible_shared_point_claimed:false};
}

if (typeof module !== "undefined") {
  module.exports = {completeF0FractionalBaseline, inspectF0FractionalBaseline,
    checkF0BaselineInteriorProjection};
}
if (typeof require !== "undefined" && require.main === module) {
  const fs = require("node:fs"), path = require("node:path"), crypto = require("node:crypto");
  if (process.argv.length !== 5) {
    throw new Error("Usage: node baseline.js structural-input.json motif-input.json interior-certificate.json");
  }
  const sourcePath = path.join(__dirname, "root_prism_free_f0_fractional_structural_recovery.js");
  const rawSource = fs.readFileSync(sourcePath);
  if (crypto.createHash("sha256").update(rawSource).digest("hex") !==
      "0a1beefc85a807d5073676b0de380ff714d855e8a9a84c8e6010786a18e39b2b") {
    throw new Error("frozen structural source mismatch");
  }
  const api = require(sourcePath);
  api.checkHashControls();
  const expected = [
    "fbe9445d9f247fbbfbaccff367b0ff05afb2442a",
    "41b0f73b9f6a0061d49859fbd4e32564cea2db17",
    "6396da7dd3d5fd1df30a88cc3ea847154d62ef38"
  ];
  const raw = process.argv.slice(2).map((p, i) => {
    const bytes = fs.readFileSync(p);
    const blob = crypto.createHash("sha1").update("blob " + bytes.length + "\0").update(bytes).digest("hex");
    if (blob !== expected[i]) throw new Error("literal input Git blob mismatch");
    return bytes;
  });
  const inputs = raw.map(b => JSON.parse(b.toString("utf8")));
  const structural = api.buildF0FractionalStructure(inputs[0]);
  const built = completeF0FractionalBaseline(structural.specification, inputs[1], api.sha256Ascii);
  built.report.interior_control = checkF0BaselineInteriorProjection(
    structural.specification, built.specification, inputs[2]);
  const native = crypto.createHash("sha256").update(JSON.stringify(built.specification)).digest("hex");
  if (native !== built.report.bindings.baseline_specification_sha256) {
    throw new Error("native and portable baseline hashes disagree");
  }
  built.report.source_path = "experiments/workspace/root_prism_free_f0_fractional_baseline_recovery.js";
  built.report.source_sha256 = crypto.createHash("sha256").update(fs.readFileSync(__filename)).digest("hex");
  built.report.literal_input_sha256 = raw.map(b => crypto.createHash("sha256").update(b).digest("hex"));
  process.stdout.write(JSON.stringify(built.report, null, 2) + "\n");
}
