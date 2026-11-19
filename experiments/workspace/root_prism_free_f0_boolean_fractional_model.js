"use strict";
/* Assemble and exactly validate the fractional baseline plus every recovered
   Boolean-normalized selector inequality. This file never calls an optimizer. */
const fs=require("fs"),path=require("path"),crypto=require("crypto"),zlib=require("zlib");
const check=(ok,message)=>{if(!ok)throw new Error(message);};
const sha=x=>crypto.createHash("sha256").update(x).digest("hex");
const BIND={
  baseline_model_file:"eb872efde0768eb514c954c57a1f8049785980d2a73e158f1d29842cc0a072cb",
  baseline_model:"a30179bd5b2b7c58bb5458a3371a947997da17288a355452469d47a59ab81413",
  normalization_preparation:"5be0ea987bff89e45359508a6ba52eb6178653c86ffb9763af8467f468103bab",
  normalization_source:"4a408ad6b959fda943878c0765dd9b05fe7885082648f1edd1091326448e19e5",
  normalization_cold:"5bd4e15c5623bcac3a28a60ae971887a6a6c2304a1dda7948f26df0164cac72c",
  normalizer:"e5e880d3d7a114ad8e61447e126fd0502f4597af1a7f14eb9ffdc4a79274ece6",
  structural_input:"ef4018f26c48e9eb90bf544d41678778d71b587994096383023c8836e70bca6e",
  direct_cut_certificate:"3b5c302f9a9e3bfce6175de7c73cb835cc89f88e63148de15d59085b1da974c0",
  baseline_inspector:"2c7f4cf9965426d97eb025793d5912d2b51cc56dc9fced76fd66219333263af1"
};
function stable(x){
  if(typeof x==="bigint")return x.toString();
  if(Array.isArray(x))return x.map(stable);
  if(x&&typeof x==="object")return Object.fromEntries(Object.keys(x).sort().map(k=>[k,stable(x[k])]));
  return x;
}
const canonical=x=>JSON.stringify(stable(x)),hash=x=>sha(canonical(x));
function boundModule(name,digest){
  const p=path.join(__dirname,name);check(sha(fs.readFileSync(p))===digest,"source "+name);return require(p);
}
const norm=boundModule("root_prism_free_f0_boolean_normalization.js",BIND.normalizer);
const {integer,gcd,normalizeGuarded}=norm;
function safe(x){x=integer(x);const n=Number(x);check(Number.isSafeInteger(n)&&BigInt(n)===x,"safe exact numerical coefficient");return n;}
function read(p,digest){const b=fs.readFileSync(p);check(sha(b)===digest,"file "+p);return JSON.parse((p.endsWith(".gz")?zlib.gunzipSync(b):b).toString("utf8"));}
function unbound(p){const b=fs.readFileSync(p);return JSON.parse((p.endsWith(".gz")?zlib.gunzipSync(b):b).toString("utf8"));}
function literalRow(terms){return {terms:terms.map(([a,c])=>[a,String(integer(c))]).filter(([,c])=>c!=="0").sort((a,b)=>a[0]-b[0]),rhs:"0"};}
function primitiveQuotient(row,orbitOf){
  const c=Array(42).fill(0n);for(const[a,w]of row.terms)c[orbitOf[a]]+=integer(w);
  let g=c.reduce((d,v)=>gcd(d,v),integer(row.rhs));if(g===0n)g=1n;
  const terms=c.map((v,i)=>[i,v/g]).filter(([,v])=>v!==0n),rhs=integer(row.rhs)/g;
  return {terms,rhs,divisor:String(g),
    unit_box_tautology:terms.every(([,v])=>v<=0n)&&rhs>=0n};
}
function directCuts(certificate,validation,input,prepared){
  const record=certificate.row_certificate,triples=validation.triples,targets=validation.targets;
  check(record.transported_cuts.length===12&&record.integer_target_value===6,"direct cut count and base demand");
  const neighbors=Array.from({length:480},()=>[]);
  for(const[a,b]of validation.edges){neighbors[a].push(b);neighbors[b].push(a);}
  const positions=new Map(triples.map((h,a)=>[h.join(","),a])),output=[],details=[];
  for(const cut of record.transported_cuts){
    const move=cut.component_relabeling,ai=input.component_actions.findIndex(p=>canonical(p)===canonical(move));
    check(ai>=0,"direct core map belongs to the complete verified group");
    const action=triples.map(h=>positions.get(h.map(i=>move[i]).sort((a,b)=>a-b).join(",")));
    check(canonical(action)===canonical(prepared.signature_actions[ai]),"direct complete signature action");
    const a=action[record.target_signature],v=Array(18).fill(0n);
    for(let i=0;i<18;i++)v[move[i]]=integer(record.integer_vector[i]);
    check(a===cut.target_signature&&canonical(v.map(safe))===canonical(cut.integer_vector),"literal direct potential transport");
    check(canonical(triples[a])===canonical(cut.target_triple),"direct target triple");
    const demand=v.reduce((s,t,i)=>s+t*BigInt(targets[a][i]),0n);check(demand===6n,"direct demand");
    const weights=[];
    for(const b of neighbors[a]){
      const w=triples[b].reduce((s,i)=>s+v[i],0n);if(w>0n)weights.push([b,w]);
    }
    check(weights.length===55&&canonical(weights.map(([b,w])=>[b,safe(w)]))===canonical(cut.positive_integer_weights),"all direct positive terms");
    const normalized=normalizeGuarded(a,weights,demand);
    check(normalized.demand===2n&&normalized.divisor===3n,"direct threshold normalization");
    check(canonical(normalized.weights.map(([b,w])=>[b,safe(w)]))===canonical(cut.binary_capped_weights),"literal direct normalized weights");
    output.push(literalRow(normalized.terms));
    details.push({target:a,core_action_index:ai,demand:"6",divisor:"3",normalized_demand:"2",positive_terms:55});
  }
  const keys=new Set(output.map(hash));check(keys.size===12,"distinct direct rows");
  let transports=0;
  for(const r of output)for(const action of prepared.signature_actions){
    check(keys.has(hash(literalRow(r.terms.map(([a,c])=>[action[a],c])))),"full direct group closure");transports++;
  }
  return {rows:output,details,complete_transport_checks:transports};
}
function build(modelPath,preparationPath,structuralInput,directPath,coldPath){
  const base=read(modelPath,BIND.baseline_model_file);check(sha(JSON.stringify(base))===BIND.baseline_model,"baseline canonical model");
  const prepared=read(preparationPath,BIND.normalization_preparation);
  const cold=read(coldPath,BIND.normalization_cold);
  check(prepared.source_sha256===BIND.normalization_source&&cold.source_sha256===BIND.normalization_source,"normalization source/cold binding");
  check(cold.status.startsWith("PASS: cold exact normalization")&&cold.preparation_file_sha256===BIND.normalization_preparation,"cold exact gate");
  check(prepared.counts.closed_normalized_rows===4404&&prepared.quotient_rows.length===76,"complete normalized row inventory");
  const input=read(structuralInput,BIND.structural_input),certificate=read(directPath,BIND.direct_cut_certificate);
  check(canonical(base.validation.selector_orbits)===canonical(prepared.selector_orbits),"same42 selector orbits");
  const orbitOf=Array(480).fill(-1);
  prepared.selector_orbits.forEach((orbit,o)=>orbit.forEach(a=>{check(orbitOf[a]===-1,"disjoint orbits");orbitOf[a]=o;}));
  check(orbitOf.every(o=>o>=0),"full selector coverage");
  const direct=directCuts(certificate,base.validation,input,prepared);
  const full=prepared.closed_full_rows.map(x=>x.row).concat(direct.rows),suffix=[],keys=new Map(),mapping=[];
  let maxFullBits=0,maxQuotientBits=0,tautologies=0,directExtraRows=0;
  for(let i=0;i<full.length;i++){
    const r=full[i];
    for(const[,v]of r.terms){const x=integer(v);maxFullBits=Math.max(maxFullBits,(x<0n?-x:x).toString(2).length);}
    const q=primitiveQuotient(r,orbitOf);
    if(!q.unit_box_tautology)for(const[,v]of q.terms)maxQuotientBits=Math.max(maxQuotientBits,(v<0n?-v:v).toString(2).length);
    if(q.unit_box_tautology){mapping.push({matrix_inequality:null,divisor:q.divisor,unit_box_tautology:true});tautologies++;continue;}
    const numericalRow={terms:q.terms.map(([a,v])=>[a,safe(v)]),rhs:safe(q.rhs)};
    const key=canonical(numericalRow);let j=keys.get(key);
    if(j===undefined){
      j=base.matrix.inequalities.length+suffix.length;keys.set(key,j);
      suffix.push({...numericalRow,family:"Boolean-normalized selector",full_cut_row:i});
      if(i>=4404)directExtraRows++;
    }
    mapping.push({matrix_inequality:j,divisor:q.divisor,unit_box_tautology:false});
  }
  check(suffix.length===76+directExtraRows,"recovered76 prefix preserved");
  for(let i=0;i<4404;i++){
    const old=prepared.closed_to_quotient[i],newMap=mapping[i];
    check(old.unit_box_tautology===newMap.unit_box_tautology&&old.divisor===newMap.divisor,"normalized quotient map agreement");
    if(!old.unit_box_tautology){
      const original=prepared.quotient_rows[old.row],actual=suffix[newMap.matrix_inequality-base.matrix.inequalities.length];
      check(canonical(original.terms.map(([a,c])=>[a,safe(c)]))===canonical(actual.terms)&&safe(original.rhs)===actual.rhs,"literal coefficient-sum quotient agreement");
    }
  }
  const matrix={...base.matrix,inequalities:base.matrix.inequalities.concat(suffix)};
  check(canonical(matrix.equalities)===canonical(base.matrix.equalities),"all baseline equalities preserved");
  check(canonical(matrix.inequalities.slice(0,base.matrix.inequalities.length))===canonical(base.matrix.inequalities),"all baseline inequality prefix preserved");
  for(const r of matrix.equalities.concat(matrix.inequalities)){
    check(Number.isSafeInteger(r.rhs),"exact RHS");
    for(const[j,c]of r.terms)check(Number.isSafeInteger(j)&&j>=0&&j<5847&&Number.isSafeInteger(c),"exact sparse coefficient");
  }
  const model=stable({schema:"f0-fractional-baseline-plus-4416-Boolean-cuts-v1",
    source_sha256:sha(fs.readFileSync(__filename)),input_bindings:BIND,
    scope:{all480_selectors_free:true,all68394_shared_edges_free:true,convex_group_averaging:true,graph_automorphism_assumed:false,
      fixed_incidence:false,second_component_or_alignment_fixed:false,global_prism_and_F_free_split18_component_zero_only:true,
      final4404_normalized_rows_and_earlier12_direct_cuts_included:true,whole_problem_excluded:false,optimizer_called:false},
    matrix,validation:base.validation,baseline_matrix_sha256:hash(base.matrix),matrix_sha256:hash(matrix),
    Boolean_validation:{full_rows:full,full_to_matrix:mapping,direct_cut_replay:direct.details,
      direct_transport_checks:direct.complete_transport_checks,prepared_full_transport_checks:prepared.counts.complete_transport_evaluations},
    counts:{variables:5847,selector_orbits:42,edge_orbits:5805,equalities:matrix.equalities.length,
      baseline_inequalities:base.matrix.inequalities.length,added_quotient_inequalities:suffix.length,
      inequalities:matrix.inequalities.length,nonzeros:matrix.equalities.concat(matrix.inequalities).reduce((s,r)=>s+r.terms.length,0),
      final_registry_rows:4404,earlier_direct_rows:12,full_Boolean_rows:full.length,
      unit_box_quotient_tautologies:tautologies,direct_new_quotient_rows:directExtraRows,
      maximum_literal_coefficient_bits:maxFullBits,maximum_new_quotient_coefficient_bits:maxQuotientBits,
      numerical_row_scaling_required:false,all_quotient_numerical_coefficients_exact_in_binary64:true}
  });
  return {model,baseline:base};
}
function inspect(model,baseline,point){
  const module=boundModule("root_prism_free_f0_fractional_baseline_recovery.js",BIND.baseline_inspector);
  const base=module.inspectF0FractionalBaseline(baseline.validation,{matrix:baseline.matrix,motif_pairs:baseline.validation.motif_pairs},point);
  check(base.status==="PASS: exact fractional baseline point","exact baseline control");
  const d=integer(point.denominator),z=point.numerators.map(integer),orbitOf=Array(480).fill(-1);
  model.validation.selector_orbits.forEach((orbit,o)=>orbit.forEach(a=>{orbitOf[a]=o;}));
  const literal=orbitOf.map(o=>z[o]),rows=model.matrix,eq=[],ineq=[],full=[];
  for(let i=0;i<rows.equalities.length;i++){
    const r=rows.equalities[i],v=r.terms.reduce((s,[j,c])=>s+BigInt(c)*z[j],0n)-BigInt(r.rhs)*d;
    if(v!==0n)eq.push([i,String(v)]);
  }
  const iq=rows.inequalities.map(r=>r.terms.reduce((s,[j,c])=>s+BigInt(c)*z[j],0n)-BigInt(r.rhs)*d);
  for(let i=0;i<iq.length;i++)if(iq[i]>0n)ineq.push([i,String(iq[i])]);
  const values=model.Boolean_validation.full_rows.map(r=>r.terms.reduce((s,[a,c])=>s+integer(c)*literal[a],0n)-integer(r.rhs)*d);
  for(let i=0;i<values.length;i++){
    const map=model.Boolean_validation.full_to_matrix[i];
    if(map.unit_box_tautology)check(values[i]<=0n,"discarded quotient tautology");
    else check(values[i]===integer(map.divisor)*iq[map.matrix_inequality],"exact full/quotient cut lift");
    if(values[i]>0n)full.push([i,String(values[i])]);
  }
  const passed=eq.length+ineq.length+full.length===0;
  return {status:passed?"PASS: exact rational point satisfies complete baseline and all4416 normalized selector rows":"FAIL: combined model point",
    baseline_check:base,full_Boolean_rows_checked:values.length,combined_full_rows_checked:base.full_rows_checked+values.length,
    full_bounds_checked:base.full_variable_bounds_checked,quotient_equalities_checked:rows.equalities.length,
    quotient_inequalities_checked:rows.inequalities.length,failures:{equalities:eq,inequalities:ineq,full_Boolean:full},
    direct_cut_slack_numerators:values.slice(4404).map(v=>String(-v)),
    common_denominator:String(d),denominator_bits:d.toString(2).length,
    optimizer_called:false,graph_constructed:false,component_excluded:false};
}
function writeFresh(p,value){
  check(!fs.existsSync(p),"fresh output "+p);fs.mkdirSync(path.dirname(p),{recursive:true});
  const b=Buffer.from(canonical(value)+"\n"),out=p.endsWith(".gz")?zlib.gzipSync(b,{level:9,mtime:0}):b;
  fs.writeFileSync(p,out,{flag:"wx"});return {path:p,sha256:sha(out),canonical_sha256:hash(value),bytes:out.length};
}
if(require.main===module){
  const a=process.argv.slice(2);check(a.length===8,"prepare|replay BASELINE PREPARATION STRUCTURAL_INPUT DIRECT_CERTIFICATE COLD_REPLAY EXACT_POINT OUTPUT_PREFIX");
  const {model,baseline}=build(a[1],a[2],a[3],a[4],a[5]);
  const exact=unbound(a[6]);check(exact.kind==="point"&&exact.model_sha256===BIND.baseline_model,"baseline exact witness");
  const result=inspect(model,baseline,exact.point);check(result.status.startsWith("PASS:"),"positive model control");
  if(a[0]==="prepare"){
    const modelFile=writeFresh(a[7]+".json.gz",model);
    const pointFile=writeFresh(a[7]+"-point.json",{source_sha256:sha(fs.readFileSync(__filename)),model_sha256:hash(model),model_file_sha256:modelFile.sha256,
      original_exact_file_sha256:sha(fs.readFileSync(a[6])),point:exact.point,exact_check:result});
    const report={status:"PASS: combined model is exactly feasible; no new optimizer needed",source_sha256:sha(fs.readFileSync(__filename)),
      counts:model.counts,model_file:modelFile,point_file:pointFile,exact_check:result};
    writeFresh(a[7]+"-report.json",report);process.stdout.write(JSON.stringify(report,null,2)+"\n");
  }else{
    check(a[0]==="replay","valid mode");
    const saved=unbound(a[7]+".json.gz"),point=unbound(a[7]+"-point.json");
    check(canonical(saved)===canonical(model),"cold complete mathematical model");
    check(point.model_sha256===hash(model)&&point.model_file_sha256===sha(fs.readFileSync(a[7]+".json.gz")),"cold model binding");
    check(canonical(point.point)===canonical(exact.point)&&canonical(point.exact_check)===canonical(result),"cold full point replay");
    const report={status:"PASS: cold combined model and complete exact point replay",source_sha256:sha(fs.readFileSync(__filename)),
      model_file_sha256:sha(fs.readFileSync(a[7]+".json.gz")),point_file_sha256:sha(fs.readFileSync(a[7]+"-point.json")),
      counts:model.counts,exact_check:result,optimizer_called:false};
    writeFresh(a[7]+"-cold-replay.json",report);process.stdout.write(JSON.stringify(report,null,2)+"\n");
  }
}
module.exports={build,inspect};

