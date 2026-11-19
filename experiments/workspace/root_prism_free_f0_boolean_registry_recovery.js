"use strict";
/* Exact recovery and Boolean strengthening of the final 4,404-cut F0 registry.
   No optimizer, SAT call or graph-automorphism assumption appears here. */
const fs=require("fs"),path=require("path"),crypto=require("crypto"),zlib=require("zlib");
const check=(ok,message)=>{if(!ok)throw new Error(message);};
const sha=x=>crypto.createHash("sha256").update(x).digest("hex");
const expected={
  normalizer:"e5e880d3d7a114ad8e61447e126fd0502f4597af1a7f14eb9ffdc4a79274ece6",
  lossless_reader:"fce582be152a5257352a9fd49536e8b26e6ba21a579514542c2a3e883e7d27e9",
  lossless_converter:"795836b0bff4e9ad55e1e2c44954d719058fcaec81e0a84dbd9fb668dafdcff2",
  lossless_transfer:"c990af1c45cd9683110ee293cb0f13f741a4ed96c16641dae18f3d521708b5a3",
  structural:"0a1beefc85a807d5073676b0de380ff714d855e8a9a84c8e6010786a18e39b2b",
  structural_input:"ef4018f26c48e9eb90bf544d41678778d71b587994096383023c8836e70bca6e",
  structural_specification:"5b2a8715c9cad3217b72479dd12c733f5b8b73d878cbb70df154167b7e386525",
  individual:"6acd86b609230632c42b345ba0d1742ca3a3155cf216271f74508acaa71f1e41",
  shared:"6ea36f93085ab07e641e5148fb9a297b9d9bdd9abd6ff36922fde5f112ccd71d",
  quadratic:"29610083a8ce62eca87fb53e9cadbcdc5cca94cb8c24952a213cc19e876a8871",
  cold_mathematical:"4c437fb8ad028bc9aa55753cc0da33d557d884c75962531e991fc2743b2dde9a",
  fresh_cold_wrapper:"81208a5c05fa028a6daccfd7e725f9cbe7b1342e872742fce854e67e851ec9e7",
  baseline:"2c7f4cf9965426d97eb025793d5912d2b51cc56dc9fced76fd66219333263af1",
  native_model:"a30179bd5b2b7c58bb5458a3371a947997da17288a355452469d47a59ab81413"
};
function boundModule(name,digest){
  const p=path.join(__dirname,name);check(sha(fs.readFileSync(p))===digest,"source binding "+name);return require(p);
}
const norm=boundModule("root_prism_free_f0_boolean_normalization.js",expected.normalizer);
const {integer,gcd,normalizeGuarded,normalizeShared}=norm;
const lossless=boundModule("root_prism_free_f0_lossless_registry_input.js",expected.lossless_reader);
const {pythonCanonical,pyHash}=lossless;
function stable(x){
  if(typeof x==="bigint")return x.toString();
  if(Array.isArray(x))return x.map(stable);
  if(x&&typeof x==="object")return Object.fromEntries(Object.keys(x).sort().map(k=>[k,stable(x[k])]));
  return x;
}
const canonical=x=>JSON.stringify(stable(x));
const objectHash=x=>sha(canonical(x));
function number(x){x=integer(x);const n=Number(x);return Number.isSafeInteger(n)&&BigInt(n)===x?n:x;}
function equal(a,b,message){check(pythonCanonical(a)===pythonCanonical(b),message);}
function checkedJSON(p,digest){
  const raw=fs.readFileSync(p);check(sha(raw)===digest,"input binding "+p);
  return JSON.parse((p.endsWith(".gz")?zlib.gunzipSync(raw):raw).toString("utf8"));
}
function unboundJSON(p){const raw=fs.readFileSync(p);return JSON.parse((p.endsWith(".gz")?zlib.gunzipSync(raw):raw).toString("utf8"));}
const loadRegistry=root=>lossless.loadRegistry(root);
function row(terms,rhs=0n){
  const sorted=terms.map(([a,c])=>[a,integer(c)]).filter(([,c])=>c!==0n).sort((x,y)=>x[0]-y[0]);
  check(sorted.every(([a],i)=>Number.isSafeInteger(a)&&a>=0&&a<480&&(i===0||sorted[i-1][0]<a)),"row ids");
  return {terms:sorted.map(([a,c])=>[a,String(c)]),rhs:String(integer(rhs))};
}
function moved(r,image){return row(r.terms.map(([a,c])=>[image[a],c]),r.rhs);}
function pyTerms(terms){return terms.map(([a,c])=>[a,number(c)]);}
function dot(v,q){return v.reduce((s,x,i)=>s+integer(x)*integer(q[i]),0n);}
function prepare(root,structuralInput,coldWrapperPath){
  const started=Date.now();
  const cold=checkedJSON(path.join(root,"recovered-cold-mathematical-report01.json"),expected.cold_mathematical);
  const wrapper=checkedJSON(coldWrapperPath,expected.fresh_cold_wrapper);
  check(wrapper.status==="PASS: fresh exact replay equals the recovered pre-outage report","fresh mathematical gate");
  check(wrapper.optimizer_called===false&&wrapper.optimizer_calls_attempted.length===0,"no optimizer in cold replay");
  check(wrapper.replay_output_sha256===expected.cold_mathematical,"fresh report binding");
  check(cold.final_snapshot.individual_cuts===3948&&cold.final_snapshot.symmetric_cuts===456,"complete final registry");
  const input=checkedJSON(structuralInput,expected.structural_input);
  const structural=boundModule("root_prism_free_f0_fractional_structural_recovery.js",expected.structural);
  const built=structural.buildF0FractionalStructure(input),s=built.specification;
  check(sha(JSON.stringify(s))===expected.structural_specification,"complete structural specification");
  const {individual,shared,quadratic,lossless_report}=loadRegistry(root);
  check(individual.length===3948&&shared.length===456&&quadratic.length===38,"input counts");
  const triples=s.triples,targets=s.targets,edges=s.edges,n=480;
  const neighbors=Array.from({length:n},()=>[]);
  for(const[a,b]of edges){neighbors[a].push(b);neighbors[b].push(a);}
  for(const list of neighbors)check(list.every((x,i)=>i===0||list[i-1]<x),"ordered complete neighbor domain");
  const lookup=new Map(triples.map((h,a)=>[h.join(","),a]));
  const actions=input.component_actions.map(move=>triples.map(h=>{
    const image=lookup.get(h.map(i=>move[i]).sort((a,b)=>a-b).join(","));check(image!==undefined,"complete action");return image;
  }));
  check(actions.length===12,"twelve actual core actions");
  const originalRows=[],normalizations=[];
  let individualCapped=0,individualCeiling=0,individualChanged=0,positiveRawTerms=0;
  for(let index=0;index<individual.length;index++){
    const cut=individual[index],a=cut.target,v=cut.integer_vector;
    check(Number.isSafeInteger(a)&&a>=0&&a<n&&v.length===18,"row target and vector");
    v.forEach(integer);
    const demand=dot(v,targets[a]);check(demand===integer(cut.demand)&&demand>0n,"exact row demand");
    const weights=[];
    for(const b of neighbors[a]){
      const value=triples[b].reduce((z,i)=>z+integer(v[i]),0n);
      if(value>0n)weights.push([b,value]);
    }
    equal(pyTerms(weights),cut.weights,"all exact positive row terms");
    positiveRawTerms+=weights.length;
    const normalized=normalizeGuarded(a,weights,demand);
    const predicate={target:a+1,demand:number(normalized.demand),terms:pyTerms(normalized.weights).map(([b,w])=>[b+1,w])};
    check(pyHash(predicate)===cut.normalized_predicate_sha256,"historical Boolean predicate");
    const capped=weights.filter(([,w])=>w>demand).length,ceiling=demand%normalized.divisor!==0n;
    if(capped)individualCapped++;if(ceiling)individualCeiling++;if(capped||ceiling)individualChanged++;
    originalRows.push(row(normalized.terms,normalized.rhs));
    normalizations.push({family:"individual",index,target:a,raw_predicate_sha256:pyHash({target:a,demand:cut.demand,weights:cut.weights}),
      historical_boolean_predicate_sha256:cut.normalized_predicate_sha256,raw_demand:String(demand),
      divisor:String(normalized.divisor),normalized_demand:String(normalized.demand),
      capped_term_count:capped,integer_ceiling_used:ceiling,origin:cut.origin});
  }
  // Reconstruct every raw shared cut from the full arbitrary integer potential,
  // the complete edge domain and its explicit endpoint allocation.
  const reconstructedShared=new Map(),familyChecks=[];
  let positiveSharedTerms=0;
  for(let fi=0;fi<quadratic.length;fi++){
    const family=quadratic[fi];check(family.family_index===fi,"family ordering");
    const selected=family.selected_generation_signature_ids,selectedSet=new Set(selected);
    check(selected.length===60&&selectedSet.size===60&&selected.every(a=>Number.isSafeInteger(a)&&a>=0&&a<n),"allocation support");
    const potential=Array.from({length:n},()=>Array(18).fill(0n)),seen=new Set();
    for(const[a,v]of family.nonzero_target_potentials){
      check(Number.isSafeInteger(a)&&a>=0&&a<n&&!seen.has(a)&&v.length===18&&selectedSet.has(a),"supported potential");
      seen.add(a);potential[a]=v.map(integer);check(potential[a].some(x=>x!==0n),"nonzero potential");
    }
    const demand=potential.map((v,a)=>dot(v,targets[a])),positive=[];
    for(const[a,b]of edges){
      const value=triples[b].reduce((z,i)=>z+potential[a][i],0n)+triples[a].reduce((z,i)=>z+potential[b][i],0n);
      if(value>0n)positive.push([a,b,value]);
    }
    equal(demand.map(number),family.target_demands,"all shared demands");
    equal(positive.map(([a,b,w])=>[a,b,number(w)]),family.positive_edges,"all positive shared edge weights");
    positiveSharedTerms+=positive.length;
    const coefficients=demand.slice();
    for(const[a,b,w]of positive){const endpoint=!selectedSet.has(a)?a:!selectedSet.has(b)?b:a;coefficients[endpoint]-=w;}
    equal(coefficients.map(number),family.old_allocation_raw_coefficients,"complete endpoint allocation");
    const divisor=coefficients.reduce((g,c)=>gcd(g,c),0n);check(divisor>0n&&divisor===integer(family.old_allocation_coefficient_gcd),"shared primitive gcd");
    const baseTerms=coefficients.map((c,a)=>[a,c/divisor]).filter(([,c])=>c!==0n);
    const gap=selected.reduce((z,a)=>z+demand[a],0n)-positive.reduce((z,[a,b,w])=>z+(selectedSet.has(a)&&selectedSet.has(b)?w:0n),0n);
    check(gap===integer(family.generation_raw_gap)&&gap>0n&&gap/divisor===integer(family.generation_normalized_gap),"generation gap");
    const demandTerms=demand.map((d,a)=>[a,d]).filter(([,d])=>d!==0n);
    check(pyHash([pyTerms(demandTerms),positive.map(([a,b,w])=>[a,b,number(w)])])===family.base_quadratic_predicate_sha256,"base potential hash");
    check(family.transports.length===12,"complete family transports");
    for(let ai=0;ai<12;ai++){
      const image=actions[ai],terms=baseTerms.map(([a,c])=>[image[a],c]).sort((x,y)=>x[0]-y[0]);
      const termsNumeric=pyTerms(terms),predicate=pyHash(termsNumeric);
      const md=demandTerms.map(([a,d])=>[image[a],number(d)]).sort((x,y)=>x[0]-y[0]);
      const mp=positive.map(([a,b,w])=>[Math.min(image[a],image[b]),Math.max(image[a],image[b]),number(w)]).sort((x,y)=>x[0]-y[0]||x[1]-y[1]);
      const t=family.transports[ai];
      check(t.core_action_index===ai&&t.existing_linear_predicate_sha256===predicate&&t.quadratic_predicate_sha256===pyHash([md,mp]),"literal shared transport");
      check(integer(t.known_generation_selection_raw_gap)===gap,"transport generation gap");
      check(!reconstructedShared.has(predicate),"distinct complete shared predicates");
      reconstructedShared.set(predicate,{terms:termsNumeric,family_index:fi,core_action_index:ai});
    }
    familyChecks.push({family_index:fi,positive_edges:positive.length,supported_potentials:seen.size,raw_gap:String(gap),coefficient_gcd:String(divisor)});
  }
  check(reconstructedShared.size===456,"complete reconstructed shared registry");
  let sharedCapped=0,sharedTautologies=0;
  for(let index=0;index<shared.length;index++){
    const cut=shared[index],bound=reconstructedShared.get(cut.predicate_sha256);
    check(bound!==undefined&&pyHash(cut.signed_coefficients)===cut.predicate_sha256,"shared raw predicate binding");
    equal(cut.signed_coefficients,bound.terms,"shared full terms");
    const normalized=normalizeShared(cut.signed_coefficients),threshold=normalized.positive_threshold;
    const capped=cut.signed_coefficients.filter(([,c])=>integer(c)<-threshold).length;
    if(normalized.tautology)sharedTautologies++;else if(capped)sharedCapped++;
    originalRows.push(row(normalized.terms,normalized.rhs));
    normalizations.push({family:"shared",index,potential_family_index:bound.family_index,core_action_index:bound.core_action_index,
      raw_predicate_sha256:cut.predicate_sha256,positive_literal_threshold:String(threshold),divisor:String(normalized.divisor),
      normalized_literal_threshold:String(normalized.threshold),capped_term_count:normalized.tautology?0:capped,
      tautology:normalized.tautology,origin:cut.origin});
  }
  const closed=[],lookupRow=new Map(),originalToClosed=[];
  function add(r,origin){
    const key=objectHash(r);let index=lookupRow.get(key);
    if(index===undefined){index=closed.length;lookupRow.set(key,index);closed.push({row:r,first_origin:origin,origins:[]});}
    closed[index].origins.push(origin);return index;
  }
  for(let i=0;i<originalRows.length;i++)originalToClosed.push(add(originalRows[i],{kind:"normalized original",index:i}));
  const initialUnique=closed.length;
  // Full group images are individually justified by relabeling the complete
  // literal core and universal cut, regardless of saved-list closure.
  for(let i=0;i<initialUnique;i++)for(let ai=0;ai<12;ai++){
    const r=moved(closed[i].row,actions[ai]),key=objectHash(r);
    if(!lookupRow.has(key))add(r,{kind:"justified core transport",source_row:i,core_action_index:ai});
  }
  const transportTable=closed.map(entry=>actions.map(image=>{
    const result=lookupRow.get(objectHash(moved(entry.row,image)));check(result!==undefined,"full normalized closure");return result;
  }));
  const orbitOf=Array(n).fill(-1);s.selector_orbits.forEach((orbit,o)=>orbit.forEach(a=>{check(orbitOf[a]<0,"disjoint selector orbits");orbitOf[a]=o;}));
  check(orbitOf.every(o=>o>=0)&&s.selector_orbits.length===42,"selector orbit coverage");
  const quotient=[],quotientLookup=new Map(),closedToQuotient=[],tautologies=[];
  for(let i=0;i<closed.length;i++){
    const r=closed[i].row,coefficient=Array(42).fill(0n);
    for(const[a,c]of r.terms)coefficient[orbitOf[a]]+=integer(c);
    let divisor=coefficient.reduce((g,c)=>gcd(g,c),integer(r.rhs));if(divisor===0n)divisor=1n;
    const primitive={terms:coefficient.map((c,o)=>[o,String(c/divisor)]).filter(([,c])=>c!=="0"),rhs:String(integer(r.rhs)/divisor)};
    if(primitive.terms.every(([,c])=>integer(c)<=0n)&&integer(primitive.rhs)>=0n){
      tautologies.push({closed_row:i,zero_row:primitive.terms.length===0,divisor:String(divisor)});
      closedToQuotient.push({row:null,divisor:String(divisor),unit_box_tautology:true});continue;
    }
    const key=objectHash(primitive);let qi=quotientLookup.get(key);
    if(qi===undefined){qi=quotient.length;quotientLookup.set(key,qi);quotient.push({...primitive,full_rows:[]});}
    quotient[qi].full_rows.push(i);closedToQuotient.push({row:qi,divisor:String(divisor),unit_box_tautology:false});
  }
  // All images must have the same literal coefficient sums, not averages.
  for(let i=0;i<closed.length;i++)for(let ai=0;ai<12;ai++){
    const j=transportTable[i][ai];check(canonical(closedToQuotient[i])===canonical(closedToQuotient[j]),"transported quotient identity");
  }
  const specification={
    schema:"f0-boolean-normalized-final-registry-v2-lossless",
    source_sha256:sha(fs.readFileSync(__filename)),
    input_bindings:{...expected,final_registry_state_sha256:cold.final_snapshot.registry_state_sha256},
    scope:{component_zero_global_prism_and_F_free_split18:true,all480_selectors_free:true,second_component_or_alignment_fixed:false,
      final_4404_registry:true,earlier12_direct_weighted_cuts_included:false,Boolean_normalization_not_raw_fractional_equivalence:true,
      native_baseline_formula_changed:false,optimizer_called:false},
    lossless_input_replay:lossless_report,
    controls:norm.normalizationControls(),
    counts:{individual_records:3948,shared_records:456,raw_records:4404,potential_families:38,
      recomputed_positive_individual_terms:positiveRawTerms,recomputed_positive_shared_edges:positiveSharedTerms,
      individual_rows_with_caps:individualCapped,individual_rows_with_integer_ceiling:individualCeiling,
      individual_rows_changed_by_Boolean_strengthening:individualChanged,shared_rows_with_caps:sharedCapped,
      shared_tautologies:sharedTautologies,original_unique_normalized_rows:initialUnique,
      newly_justified_transport_rows:closed.length-initialUnique,closed_normalized_rows:closed.length,
      complete_transport_evaluations:closed.length*12,unit_box_quotient_tautologies:tautologies.length,
      nontrivial_distinct_quotient_rows:quotient.length,quotient_nonzeros:quotient.reduce((z,r)=>z+r.terms.length,0)},
    selector_orbits:s.selector_orbits,signature_actions:actions,individual_and_shared_normalizations:normalizations,
    reconstructed_shared_families:familyChecks,original_to_closed_row:originalToClosed,
    closed_full_rows:closed,complete_transport_table:transportTable,
    closed_to_quotient:closedToQuotient,discarded_unit_box_tautologies:tautologies,
    quotient_rows:quotient,
    quotient_rule:"Sum literal coefficients over each of42 selector orbits, then divide only by an exact common divisor. No orbit-size division."
  };
  return {specification:stable(specification),elapsed_seconds:(Date.now()-started)/1000};
}
function writeFresh(p,value){
  check(!fs.existsSync(p),"fresh output "+p);fs.mkdirSync(path.dirname(p),{recursive:true});
  const raw=Buffer.from(canonical(value)+"\n","utf8");fs.writeFileSync(p,p.endsWith(".gz")?zlib.gzipSync(raw,{level:9,mtime:0}):raw,{flag:"wx"});
  return {path:p,file_sha256:sha(fs.readFileSync(p)),canonical_sha256:objectHash(value),bytes:fs.statSync(p).size};
}
function pointCheck(modelPath,exactPath,preparationPath,recoveryRoot){
  const model=unboundJSON(modelPath),exact=unboundJSON(exactPath),prepared=unboundJSON(preparationPath);
  check(sha(JSON.stringify(model))===expected.native_model&&exact.model_sha256===expected.native_model&&exact.kind==="point","exact baseline point input");
  check(prepared.source_sha256===sha(fs.readFileSync(__filename)),"normalization source binding");
  const baseline=boundModule("root_prism_free_f0_fractional_baseline_recovery.js",expected.baseline);
  const fullCheck=baseline.inspectF0FractionalBaseline(model.validation,{matrix:model.matrix,motif_pairs:model.validation.motif_pairs},exact.point);
  check(fullCheck.status==="PASS: exact fractional baseline point","independent full baseline point control");
  const numerators=exact.point.numerators.map(integer),denominator=integer(exact.point.denominator);
  const orbitOf=Array(480).fill(-1);prepared.selector_orbits.forEach((orbit,o)=>orbit.forEach(a=>{orbitOf[a]=o;}));
  const literal=orbitOf.map(o=>numerators[o]);check(literal.every(x=>x>=0n&&x<=denominator),"literal bounds");
  const {individual,shared}=loadRegistry(recoveryRoot);
  for(const cut of individual){
    const value=integer(cut.demand)*literal[cut.target]-cut.weights.reduce((z,[a,w])=>z+integer(w)*literal[a],0n);
    check(value<=0n,"raw individual cut must follow from baseline");
  }
  for(const cut of shared)check(cut.signed_coefficients.reduce((z,[a,c])=>z+integer(c)*literal[a],0n)<=0n,"raw shared cut must follow from baseline");
  const fullValues=prepared.closed_full_rows.map(entry=>entry.row.terms.reduce((z,[a,c])=>z+integer(c)*literal[a],0n)-integer(entry.row.rhs)*denominator);
  const quotientValues=prepared.quotient_rows.map(r=>r.terms.reduce((z,[o,c])=>z+integer(c)*numerators[o],0n)-integer(r.rhs)*denominator);
  for(let i=0;i<fullValues.length;i++){
    const link=prepared.closed_to_quotient[i];
    if(link.unit_box_tautology)check(fullValues[i]<=0n,"discarded unit-box row");
    else check(fullValues[i]===integer(link.divisor)*quotientValues[link.row],"exact full/quotient point values");
  }
  const fullViolations=fullValues.flatMap((value,i)=>value>0n?[{row:i,violation_numerator:String(value),normalization_origins:prepared.closed_full_rows[i].origins}]:[]);
  const quotientViolations=quotientValues.flatMap((value,i)=>value>0n?[{row:i,violation_numerator:String(value)}]:[]);
  return {status:quotientViolations.length?"EXACT POINT REJECTED by Boolean-normalized selector cuts":"PASS: exact baseline point also satisfies all normalized rows",
    source_sha256:sha(fs.readFileSync(__filename)),preparation_file_sha256:sha(fs.readFileSync(preparationPath)),
    model_file_sha256:sha(fs.readFileSync(modelPath)),exact_file_sha256:sha(fs.readFileSync(exactPath)),
    native_model_sha256:expected.native_model,full_baseline_check:fullCheck,
    common_denominator:String(denominator),raw_individual_cuts_checked:individual.length,raw_shared_cuts_checked:shared.length,
    normalized_full_rows_checked:fullValues.length,distinct_quotient_rows_checked:quotientValues.length,
    normalized_full_violation_count:fullViolations.length,normalized_quotient_violation_count:quotientViolations.length,
    full_violations:fullViolations,quotient_violations:quotientViolations,optimizer_called:false,whole_component_excluded:false};
}
if(require.main===module){
  const a=process.argv.slice(2),mode=a[0];
  if(mode==="prepare"){
    check(a.length===5,"prepare RECOVERY_ROOT STRUCTURAL_INPUT COLD_WRAPPER OUTPUT_PREFIX");
    const built=prepare(a[1],a[2],a[3]),output=writeFresh(a[4]+".json.gz",built.specification);
    const report={status:"PASS: complete exact final-registry Boolean normalization and quotient preparation",source_sha256:built.specification.source_sha256,
      counts:built.specification.counts,controls:built.specification.controls,output,elapsed_seconds:built.elapsed_seconds,scope:built.specification.scope};
    const reportFile=writeFresh(a[4]+"-report.json",report);process.stdout.write(JSON.stringify({report,report_file:reportFile},null,2)+"\n");
  }else if(mode==="replay"){
    check(a.length===6,"replay RECOVERY_ROOT STRUCTURAL_INPUT COLD_WRAPPER PREPARATION OUTPUT");
    const built=prepare(a[1],a[2],a[3]),saved=unboundJSON(a[4]);equal(built.specification,saved,"complete cold normalization replay");
    const report={status:"PASS: cold exact normalization, all raw certificates, group closure and quotient rows replayed",
      source_sha256:built.specification.source_sha256,preparation_file_sha256:sha(fs.readFileSync(a[4])),canonical_sha256:objectHash(saved),
      counts:saved.counts,elapsed_seconds:built.elapsed_seconds,optimizer_called:false};
    writeFresh(a[5],report);process.stdout.write(JSON.stringify(report,null,2)+"\n");
  }else if(mode==="point"){
    check(a.length===6,"point MODEL EXACT PREPARATION RECOVERY_ROOT OUTPUT");
    const report=pointCheck(a[1],a[2],a[3],a[4]);writeFresh(a[5],report);process.stdout.write(JSON.stringify({...report,full_violations:undefined},null,2)+"\n");
  }else throw new Error("mode must be prepare, replay or point");
}
module.exports={prepare,pointCheck};
