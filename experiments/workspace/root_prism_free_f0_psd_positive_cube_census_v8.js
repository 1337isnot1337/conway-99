(() => {
"use strict";
const SCHEMA="conway99.f0.psd-positive-cube-census.v1";
const EDGE_ENDPOINTS=[[0,1],[0,2],[1,2]];
const EXPECTED_TRIANGLES=10830,EXPECTED_PATTERNS=86640,MAX_CUBES=32490;
function insist(ok,message){if(!ok)throw Error(message);}
function count(mask){let n=0;while(mask){mask&=mask-1;n++;}return n;}
function pairId(a,b){if(a>b)[a,b]=[b,a];insist(a<b,"distinct pair");return a*(959-a)/2+b-a-1;}
function completions(positive){let result=0;for(let p=0;p<8;p++)if((p&positive)===positive)result|=1<<p;return result;}
function positiveCubes(forbidden){
 insist(Number.isInteger(forbidden)&&forbidden>=0&&forbidden<256,"forbidden pattern mask");
 const result=[];
 for(let positive=0;positive<8;positive++){
  const inside=completions(positive);if((inside&~forbidden)!==0)continue;
  let minimal=true;const witnesses=[];
  for(let bit=0;bit<3;bit++)if(positive&(1<<bit)){
   const relaxed=positive&~(1<<bit);let witness=-1;
   for(let pattern=0;pattern<8;pattern++)if((pattern&relaxed)===relaxed&&((forbidden>>>pattern)&1)===0){witness=pattern;break;}
   if(witness<0){minimal=false;break;}witnesses.push([bit,witness]);
  }
  if(minimal)result.push({positive_mask:positive,completion_mask:inside,removal_witnesses:witnesses});
 }
 insist(result.length<=3,"positive cube antichain bound");
 insist((result.length>0)===Boolean(forbidden&128),"positive cube contains 111");
 return result;
}
function normalize(terms){
 const sums=new Map();for(const [variable,coefficient] of terms)sums.set(variable,(sums.get(variable)||0)+coefficient);
 return [...sums].filter(([,coefficient])=>coefficient!==0).sort((a,b)=>a[0]-b[0]);
}
function literalRow(triple,edgeIds,positive){
 const chosen=[0,1,2].filter(i=>positive&(1<<i)),covered=new Set();
 for(const e of chosen)for(const v of EDGE_ENDPOINTS[e])covered.add(v);
 const isolated=[0,1,2].filter(v=>!covered.has(v));
 let terms=chosen.map(e=>[540+edgeIds[e],1]),upper=chosen.length+isolated.length-1,lower=0;
 let kind=chosen.length===0?"selector_triple":chosen.length===1?"edge_and_third_selector":chosen.length===2?"homogeneous_path":"triangle";
 if(chosen.length===2){
  const center=EDGE_ENDPOINTS[chosen[0]].find(v=>EDGE_ENDPOINTS[chosen[1]].includes(v));
  insist(center!==undefined&&isolated.length===0&&upper===1,"two-edge path incidence");
  terms.push([triple[center],-1]);lower=-1;upper=0;
 }else for(const v of isolated)terms.push([triple[v],1]);
 return {kind,terms:normalize(terms),lower,upper};
}
function dominanceWitness(triple,edgeIds,positive,row){
 const chosen=[0,1,2].filter(i=>positive&(1<<i)),components=[{multiplier:chosen.length===0||chosen.length===1?2:1,terms:row.terms,upper:row.upper}];
 let scale=1,kind;
 if(chosen.length===3)kind="same_triangle_row";
 else if(chosen.length===2){
  kind="path_plus_center_and_missing_edge_upper_bounds";
  const center=EDGE_ENDPOINTS[chosen[0]].find(v=>EDGE_ENDPOINTS[chosen[1]].includes(v)),missing=[0,1,2].find(e=>!chosen.includes(e));
  components.push({multiplier:1,terms:[[triple[center],1]],upper:1},{multiplier:1,terms:[[540+edgeIds[missing],1]],upper:1});
 }else if(chosen.length===1){
  kind="twice_guarded_edge_plus_activations_and_edge_lower_bound";
  const isolated=[0,1,2].find(v=>!EDGE_ENDPOINTS[chosen[0]].includes(v));
  for(const e of [0,1,2].filter(e=>e!==chosen[0]))components.push({multiplier:1,terms:[[540+edgeIds[e],1],[triple[isolated],-1]],upper:0});
  components.push({multiplier:1,terms:[[540+edgeIds[chosen[0]],-1]],upper:0});
 }else{
  kind="twice_selector_cover_plus_all_six_activations";scale=2;
  for(let e=0;e<3;e++)for(const v of EDGE_ENDPOINTS[e])components.push({multiplier:1,terms:[[540+edgeIds[e],1],[triple[v],-1]],upper:0});
 }
 const sum=normalize(components.flatMap(c=>c.terms.map(([v,k])=>[v,k*c.multiplier]))),upper=components.reduce((s,c)=>s+c.multiplier*c.upper,0);
 insist(JSON.stringify(sum)===JSON.stringify(edgeIds.map(e=>[540+e,scale]).sort((a,b)=>a[0]-b[0]))&&upper===2*scale,"exact triangle-cover implication");
 return {kind,triangle_scale:scale};
}
function principalMinors(diagonal,off){
 const [a,b,c]=diagonal,[d,e,f]=off;
 return [a,b,c,a*b-d*d,a*c-e*e,b*c-f*f,a*b*c+2n*d*e*f-a*f*f-b*e*e-c*d*d];
}
function permutationDeterminant(matrix){
 const permutations=[[0,1,2],[0,2,1],[1,0,2],[1,2,0],[2,0,1],[2,1,0]];let sum=0n;
 for(const p of permutations){let inversions=0;for(let i=0;i<3;i++)for(let j=i+1;j<3;j++)if(p[i]>p[j])inversions++;
  sum+=(inversions%2?-1n:1n)*matrix[0][p[0]]*matrix[1][p[1]]*matrix[2][p[2]];}
 return sum;
}
function controls(guards){
 let determinantChecks=0,assignmentChecks=0,positiveCubesChecked=0,dominanceChecks=0,allInvalidPatternCoverageCounterexamples=0;
 for(let a=-1;a<=1;a++)for(let b=-1;b<=1;b++)for(let c=-1;c<=1;c++)for(let d=-1;d<=1;d++)for(let e=-1;e<=1;e++)for(let f=-1;f<=1;f++){
  const [A,B,C,D,E,F]=[a,b,c,d,e,f].map(BigInt),minors=principalMinors([A,B,C],[D,E,F]);
  insist(minors[6]===permutationDeterminant([[A,D,E],[D,B,F],[E,F,C]]),"independent determinant control");determinantChecks++;
 }
 const large=(1n<<54n)+3n;
 insist(principalMinors([large,large+1n,large+2n],[large-1n,2n,-3n])[6]===permutationDeterminant([[large,large-1n,2n],[large-1n,large+1n,-3n],[2n,-3n,large+2n]]),"large exact determinant");determinantChecks++;
 insist(principalMinors([1n,1n,1n],[2n,0n,0n])[3]<0n,"negative proper minor control");
 insist(principalMinors([-1n,1n,1n],[0n,0n,0n])[0]<0n,"negative singleton control");
 insist(principalMinors([2n,2n,2n],[-1n,-1n,-1n]).every(v=>v>=0n),"singular PSD control");
 for(let forbidden=0;forbidden<256;forbidden++){
  const own=positiveCubes(forbidden),reference=guards.primeCubes(forbidden).filter(c=>c.cube.every(v=>v!==0));
  const wanted=reference.map(c=>c.cube.reduce((s,v,i)=>s+(v===1?(1<<i):0),0)).sort((a,b)=>a-b);
  insist(JSON.stringify(own.map(c=>c.positive_mask))===JSON.stringify(wanted),"independent positive prime-cube comparison");
  let covered=0;const rows=[];
  for(const cube of own){
   const found=reference.find(c=>c.completions===cube.completion_mask);insist(found!==undefined,"completion set");
   for(const [bit,pattern] of cube.removal_witnesses)insist(((forbidden>>>pattern)&1)===0&&(pattern&(cube.positive_mask&~(1<<bit)))===(cube.positive_mask&~(1<<bit)),"minimality witness");
   covered|=cube.completion_mask;const row=literalRow([0,1,2],[0,1,2],cube.positive_mask);rows.push(row);
   dominanceWitness([0,1,2],[0,1,2],cube.positive_mask,row);dominanceChecks++;positiveCubesChecked++;
  }
  if(covered!==forbidden)allInvalidPatternCoverageCounterexamples++;
  for(let selection=0;selection<8;selection++)for(let pattern=0;pattern<8;pattern++){
   const x=[0,1,2].map(i=>(selection>>>i)&1),y=[0,1,2].map(i=>(pattern>>>i)&1);
   if(EDGE_ENDPOINTS.some(([a,b],e)=>y[e]>x[a]||y[e]>x[b]))continue;
   const pass=rows.every(row=>{const activity=row.terms.reduce((s,[v,k])=>s+k*(v<3?x[v]:y[v-540]),0);return row.lower<=activity&&activity<=row.upper;});
   const expected=selection!==7||((covered>>>pattern)&1)===0;insist(pass===expected,"positive-cube activation and guard control");assignmentChecks++;
   if(selection!==7||((forbidden>>>pattern)&1)===0)insist(pass,"PSD-compatible activated assignment rejected");
  }
 }
 insist(assignmentChecks===4608&&allInvalidPatternCoverageCounterexamples>0,"control coverage");
 return {status:"PASS_EXACT_PSD_POSITIVE_CUBE_CONTROLS",exact_determinant_checks:determinantChecks,small_determinant_checks:determinantChecks-1,large_integer_checks:1,large_integer_entry:large.toString(),
  forbidden_pattern_sets:256,activated_assignments_checked:assignmentChecks,positive_cubes_checked:positiveCubesChecked,linear_triangle_dominance_checks:dominanceChecks,
  positive_only_cubes_do_not_cover_all_bad_patterns:allInvalidPatternCoverageCounterexamples,negative_proper_and_singleton_controls:true,
  singular_PSD_control:true,production_kernel_inputs_used:false,native_model_builds:0,optimizer_calls:0};
}
function assertParentCold(cold,parent,parentConfiguration,coldConfiguration,configuration,codec){
 insist(cold.schema==="conway99.f0.triangle-schur-independent-cold.v1"&&cold.status==="PASS_COMPLETE_INDEPENDENT_CENSUS_AND_LITERAL_ZERO_DISPOSITION"&&cold.complete===true,"complete accepted parent cold");
 insist(cold.source_sha256===configuration.sources.parent_cold.sha256&&cold.configuration_sha256===configuration.inputs.parent_cold_configuration.sha256,"parent cold implementation authority");
 insist(coldConfiguration.source.sha256===configuration.sources.parent_cold.sha256&&coldConfiguration.forward_producer_sha256===configuration.sources.parent.sha256,"parent cold configuration authority");
 insist(parent.configuration_sha256===configuration.inputs.parent_configuration.sha256&&parentConfiguration.source.sha256===configuration.sources.parent.sha256,"parent forward configuration authority");
 insist(cold.selectors===480&&cold.original_eligible_edges===68394&&cold.pairwise_disjoint_signature_edges===49320&&cold.pairwise_disjoint_eligible_triangles===1179048,"parent cold complete universe");
 insist(cold.progress.completed_maximum_vertex_exclusive===480&&cold.progress.triangles===1179048&&cold.error===null,"parent cold complete enumeration");
 insist(cold.old_zero_edges_removed_before_census===false&&cold.producer_or_classifier_math_executed===false&&cold.optimizer_calls===0,"independent unpruned parent census");
 const bound=cold.input_bindings.forward,expected=configuration.inputs.parent_forward;
 insist(bound.raw_sha256===expected.sha256&&bound.raw_bytes===expected.bytes&&bound.git_blob===expected.git_blob_sha,"cold binds complete forward bytes");
 for(const name of ["domain","kernels"]){
  const actual=cold.input_bindings[name],wanted=configuration.inputs[name];
  insist(actual.archive_sha256===wanted.archive_sha256&&actual.raw_sha256===wanted.raw_sha256&&actual.git_blob===wanted.archive_git_blob,"cold shares exact kernel and domain inputs");
 }
 insist(cold.input_bindings.audit.raw_sha256===configuration.inputs.audit.sha256,"cold shares independent kernel audit");
 insist(cold.families.length===2&&parent.families.length===2,"two parent families");
 for(let i=0;i<2;i++){
  const actual=cold.families[i],expected=parent.families[i],name=i===0?"plus":"minus";
  insist(actual.family===name&&expected.family===name&&actual.primitive_kernel_sha256===expected.primitive_kernel_sha256,"parent family identity");
  insist(JSON.stringify(actual.counts)===JSON.stringify(expected.counts)&&actual.counts.negative_proper_minor===0,"complete parent minor counts");
  const a=JSON.stringify(actual.nonpositive_determinant_records_with_nonnegative_proper_minors),b=JSON.stringify(expected.nonpositive_determinant_records_with_nonnegative_proper_minors);
  insist(a===b&&codec.sha256(codec.utf8(a))===actual.nonpositive_records_sha256,"complete ordered negative-list cold replay");
 }
 insist(cold.families[0].nonpositive_records_sha256==="60dd838a427e23b5d3c773e7eb8ecb9852e77a88bd0d9e1ac647e51be7965ff8","fixed complete 10830-triangle list");
}
function run(bundle,codec,configurationText){
 const started=Date.now(),configuration=JSON.parse(configurationText),configurationSha256=codec.sha256(codec.utf8(configurationText));
 const ledger=[],rows=[],seen=new Map(),failures=[];
 const limits=configuration.limits;let complete=false,decoded=null,checkedMinors=0,checkedMatrices=0,originCount=0;
 const tick=()=>insist(Date.now()-started<limits.maximum_ms,"positive cube census deadline");
 const readText=(name,text)=>{
  const bytes=codec.utf8(text),ref=configuration.inputs[name];insist(bytes.length===ref.bytes&&codec.sha256(bytes)===ref.sha256,"bound text "+name);
  if(ref.git_blob_sha)insist(codec.gitBlob(bytes)===ref.git_blob_sha,"bound Git blob "+name);
  return JSON.parse(text);
 };
 const familyInvalidPatterns=[Array(8).fill(0),Array(8).fill(0)],compatibleCounts=Array(9).fill(0),cubeCounts=Array(8).fill(0);
 try{
  insist(configuration.schema==="conway99.f0.psd-positive-cube-configuration.v1","configuration schema");
  insist(limits.maximum_ms===60000&&limits.maximum_triangles===EXPECTED_TRIANGLES&&limits.maximum_patterns===EXPECTED_PATTERNS,"main bounds");
  insist(limits.maximum_cube_origins===MAX_CUBES&&limits.maximum_unique_rows===MAX_CUBES&&limits.maximum_serialized_bytes===33554432,"record bounds");
  insist(configuration.old_edge_zero_pruning===false&&configuration.positive_cubes_only===true,"PSD-only scope");
  for(const [key,ref] of Object.entries(configuration.sources)){
   const text=bundle[key+"_source_text"];insist(typeof text==="string","bound source text "+key);
   const bytes=codec.utf8(text);insist(bytes.length===ref.bytes&&codec.sha256(bytes)===ref.sha256&&codec.gitBlob(bytes)===ref.git_blob_sha,"bound source "+key);
  }
  const readArchive=name=>{
   const ref=configuration.inputs[name],archive=codec.base64(bundle[name+"_base64"]);
   insist(archive.length===ref.archive_bytes&&codec.sha256(archive)===ref.archive_sha256&&codec.gitBlob(archive)===ref.archive_git_blob,"archive "+name);
   const raw=codec.gunzip(archive,4194304);insist(raw.length===ref.raw_bytes&&codec.sha256(raw)===ref.raw_sha256,"raw "+name);
   return JSON.parse(codec.ascii(raw));
  };
  const domain=readArchive("domain"),kernels=readArchive("kernels"),audit=readText("audit",bundle.audit_text),
   parent=readText("parent_forward",bundle.parent_forward_text),cold=readText("parent_cold",bundle.parent_cold_text),
   guardControls=readText("guard_controls",bundle.guard_controls_text),parentConfiguration=readText("parent_configuration",bundle.parent_configuration_text),
   coldConfiguration=readText("parent_cold_configuration",bundle.parent_cold_configuration_text);
  insist(guardControls.status==="PASS_EXHAUSTIVE_PARTIAL_CUBE_ACTIVATION_GUARDS"&&guardControls.exact_oracle_checks===4608&&guardControls.source.sha256===configuration.sources.guard.sha256,"guard control authority");
  insist(audit.status==="PASS: exact full-core Schur corrections; no point query"&&audit.families.every(f=>f.all_115440_full_vs_old_kernel_entries_checked===true),"accepted full-core kernel audit");
  insist(parent.status==="COMPLETE_EXACT_TRIANGLE_PRINCIPAL_MINOR_CENSUS"&&parent.source_sha256===configuration.sources.parent.sha256,"parent census authority");
  insist(parent.pairwise_disjoint_eligible_triangles===1179048&&parent.original_eligible_edges===68394&&!parent.old_prism_zero_or_path_rows_used,"parent scope");
  assertParentCold(cold,parent,parentConfiguration,coldConfiguration,configuration,codec);
  const expectedCounts=[{negative_proper_minor:0,negative_determinant:10830,zero_determinant:0,positive_determinant:1168218},
   {negative_proper_minor:0,negative_determinant:0,zero_determinant:0,positive_determinant:1179048}];
  for(let i=0;i<2;i++)for(const [key,value] of Object.entries(expectedCounts[i]))insist(parent.families[i].counts[key]===value,"complete parent counts");
  const negatives=parent.families[0].nonpositive_determinant_records_with_nonnegative_proper_minors;
  insist(negatives.length===EXPECTED_TRIANGLES&&parent.families[1].nonpositive_determinant_records_with_nonnegative_proper_minors.length===0,"complete negative list");
  const core=domain.component_core_rows,triples=domain.signature_domain,q=domain.row_targets;
  insist(core.length===21&&triples.length===480&&q.length===480,"fixed domain dimensions");
  const adjacency=core.slice(3).map(v=>v>>>3),masks=triples.map(t=>{insist(t.length===3&&t.every((v,i)=>Number.isInteger(v)&&v>=0&&v<18&&(i===0||t[i-1]<v)),"signature");return t.reduce((s,v)=>s|(1<<v),0);});
  for(let a=0;a<480;a++)for(let i=0;i<18;i++)insist(q[a][i]===2-((masks[a]>>>i)&1)-count(adjacency[i]&masks[a]),"quota reconstruction");
  const edgeIds=new Int32Array(480*480).fill(-1),recovered=Array.from({length:480},()=>[]);let edgeCount=0;
  for(let a=0;a<480;a++)for(let b=a+1;b<480;b++){
   if(count(masks[a]&masks[b])>1||!triples[b].every(i=>q[a][i]>0)||!triples[a].every(i=>q[b][i]>0))continue;
   edgeIds[a*480+b]=edgeIds[b*480+a]=edgeCount++;recovered[a].push(b);recovered[b].push(a);
  }
  insist(edgeCount===68394&&JSON.stringify(recovered)===JSON.stringify(domain.possible_neighbor_signature_ids),"complete original edge namespace");
  insist(kernels.source_sha256==="141392693e8d4b7e140c329cfa4128b8794bd376713558394ef014975e2fc63f"&&kernels.kernels.length===2&&audit.families.length===2,"kernel source and families");
  const families=kernels.kernels.map((k,index)=>{
   const divisor=index===0?1:11,name=index===0?"plus":"minus";
   insist(k.family===name&&k.common_numerator_divisor===divisor&&k.diagonal_x.length===480&&k.off_diagonal_Z.length===114960,"kernel structure");
   insist(k.Y===(index===0?-540:2797080)&&k.Schur_coefficient_denominator===(index===0?60:254280),"positive kernel scaling");
   insist(k.diagonal_x.concat(k.off_diagonal_Z,[k.Y]).every(v=>Number.isSafeInteger(v)&&v%divisor===0),"exact primitive entries");
   const diagonal=k.diagonal_x.map(v=>v/divisor),off=k.off_diagonal_Z.map(v=>v/divisor),y=k.Y/divisor,ordered=[];
   for(let a=0;a<480;a++)for(let b=a;b<480;b++)ordered.push(a===b?diagonal[a]:off[pairId(a,b)]);ordered.push(y);
   const hash=codec.sha256(codec.utf8(JSON.stringify(ordered)));
   insist(hash===k.primitive_kernel_sha256&&hash===audit.families[index].primitive_kernel_sha256&&hash===parent.families[index].primitive_kernel_sha256,"independent primitive kernel identity");
   return {name,diagonal:diagonal.map(BigInt),off:off.map(BigInt),y:BigInt(y),primitive_kernel_sha256:hash};
  });
  decoded={parent_forward_sha256:configuration.inputs.parent_forward.sha256,parent_cold_sha256:configuration.inputs.parent_cold.sha256,
   family_kernel_sha256:families.map(f=>f.primitive_kernel_sha256),original_edge_count:edgeCount};
  tick();let previous=null;
  for(let ti=0;ti<negatives.length;ti++){
   if(ti%64===0)tick();insist(ledger.length<limits.maximum_triangles,"triangle record limit");
   const saved=negatives[ti],[a,b,c]=saved,triple=[a,b,c];
   insist(triple.every(Number.isInteger)&&0<=a&&a<b&&b<c&&c<480&&saved.length===7&&BigInt(saved[3])<0n,"negative parent record");
   insist(previous===null||a>previous[0]||(a===previous[0]&&(b>previous[1]||(b===previous[1]&&c>previous[2]))),"strict negative-triple order");previous=triple;
   insist((masks[a]&masks[b])===0&&(masks[a]&masks[c])===0&&(masks[b]&masks[c])===0,"pairwise disjoint signatures");
   const ids=[edgeIds[a*480+b],edgeIds[a*480+c],edgeIds[b*480+c]];insist(ids.every(e=>e>=0),"three eligible edges");
   const pairs=[pairId(a,b),pairId(a,c),pairId(b,c)],diagonal=families.map(f=>triple.map(v=>f.diagonal[v])),offZero=families.map(f=>pairs.map(p=>f.off[p]));
   const patternRecords=[];let compatible=0;const familyMasks=[0,0];
   for(let pattern=0;pattern<8;pattern++){
    insist(ti*8+pattern<limits.maximum_patterns,"pattern record limit");
    const record=[];let invalid=0;
    for(let fi=0;fi<2;fi++){
     const off=offZero[fi].map((v,e)=>v+((pattern&(1<<e))?families[fi].y:0n)),minors=principalMinors(diagonal[fi],off);
     let bad=false;for(const value of minors){if(value<0n)bad=true;checkedMinors++;}checkedMatrices++;
     if(bad){invalid|=1<<fi;familyInvalidPatterns[fi][pattern]++;}else familyMasks[fi]|=1<<pattern;
     record.push(...minors.slice(3).map(String));
     if(pattern===7&&fi===0)insist(minors[6].toString()===saved[3]&&JSON.stringify(minors.slice(3,6).map(String))===JSON.stringify(saved.slice(4)),"parent negative triangle exact replay");
     if(pattern===7&&fi===1)insist(minors.every(v=>v>=0n),"parent minus 111 consistency");
    }
    record.push(invalid);patternRecords.push(record);if(invalid===0)compatible|=1<<pattern;
   }
   insist((compatible&128)===0,"input triangle pattern is forbidden");
   const forbidden=(~compatible)&255,cubes=positiveCubes(forbidden),cubeRecords=[];
   compatibleCounts[count(compatible)]++;
   for(const cube of cubes){
    insist(originCount<limits.maximum_cube_origins,"cube origin limit");originCount++;cubeCounts[cube.positive_mask]++;
    const row=literalRow(triple,ids,cube.positive_mask),key=JSON.stringify([row.lower,row.upper,row.terms]);
    let rowId=seen.get(key);
    if(rowId===undefined){insist(rows.length<limits.maximum_unique_rows,"unique row limit");rowId=rows.length;seen.set(key,rowId);rows.push({...row,row_id:rowId,origins:[]});}
    insist(rows[rowId].kind===row.kind,"full literal row identity");rows[rowId].origins.push([ti,cube.positive_mask]);
    cubeRecords.push({...cube,row_id:rowId});
   }
   insist(cubeRecords.length>0,"each parent triangle has a positive minimal cube");
   const witness=cubeRecords[0],domination=dominanceWitness(triple,ids,witness.positive_mask,rows[witness.row_id]);
   ledger.push({index:ti,selectors:triple,edge_ids:ids,diagonal_minors:diagonal.map(v=>v.map(String)),
    primitive_off_diagonal_zero:offZero.map(v=>v.map(String)),patterns:patternRecords,compatible_pattern_mask:compatible,
    family_PSD_masks:familyMasks,positive_cubes:cubeRecords,
    triangle_cover_dominance:{row_id:witness.row_id,positive_mask:witness.positive_mask,...domination}});
  }
  insist(ledger.length===EXPECTED_TRIANGLES&&checkedMatrices===EXPECTED_PATTERNS*2&&checkedMinors===EXPECTED_PATTERNS*14,"complete exact minor coverage");
  insist(rows.reduce((s,r)=>s+r.origins.length,0)===originCount,"complete row origin preservation");tick();complete=true;
 }catch(error){failures.push({name:error.name,message:error.message});}
 const result={schema:SCHEMA,status:complete?"COMPLETE_EXACT_PSD_POSITIVE_CUBE_CENSUS":"INCOMPLETE_PSD_POSITIVE_CUBE_CENSUS",complete,
  definition:"Three selected signatures; bit0=ab, bit1=ac, bit2=bc. Compatibility means all principal minors are nonnegative in both accepted full-core Schur families.",
  pattern_fields:["plus_ab_minor","plus_ac_minor","plus_bc_minor","plus_determinant","minus_ab_minor","minus_ac_minor","minus_bc_minor","minus_determinant","invalid_family_mask"],
  family_names:["plus","minus"],matrix_singleton_minors_stored_once_per_triple:true,all_arithmetic_for_minors:"BigInt",
  configuration_sha256:configurationSha256,input_bindings:configuration.inputs,source_bindings:configuration.sources,limits,decoded_authority:decoded,
  literal_namespace:{selector_variables:[0,479],edge_offset:540,original_edges:68394,total_existing_variables:68934},
  full_parent_disjoint_eligible_triangles:1179048,required_negative_triangles:EXPECTED_TRIANGLES,processed_triangles:ledger.length,
  pattern_records:ledger.length*8,matrices_checked:checkedMatrices,principal_minors_checked:checkedMinors,positive_cube_origins:originCount,
  distinct_literal_rows:rows.length,compatible_pattern_count_histogram:compatibleCounts,family_invalid_pattern_counts:familyInvalidPatterns,
  positive_mask_origin_counts:cubeCounts,old_edge_zero_rows_used:false,old_prism_or_path_rows_used:false,new_cut_novelty_claimed:false,
  positive_cubes_only:true,coverage_of_all_forbidden_patterns_claimed:false,complete_positive_cube_scope_conditional_on_parent_cold:true,
  PSD_compatibility_is_not_graph_feasibility:true,all_parent_triangle_covers_have_explicit_linear_dominators:complete,
  ledger,rows,failures,native_model_builds:0,optimizer_calls:0,graph_constructed:false,whole_component_excluded:false,
  seconds:(Date.now()-started)/1000};
 let serialized=JSON.stringify(result),serializedBytes=codec.utf8(serialized).length;
 const completedSeconds=(Date.now()-started)/1000;
 if(serializedBytes>limits.maximum_serialized_bytes||completedSeconds*1000>=limits.maximum_ms){
  result.complete=false;result.status="INCOMPLETE_PSD_POSITIVE_CUBE_CENSUS";result.all_parent_triangle_covers_have_explicit_linear_dominators=false;
  result.failures.push({name:"FinalizationLimit",message:"complete serialization exceeded the declared byte or time bound"});
  result.seconds=completedSeconds;serialized=JSON.stringify(result);serializedBytes=codec.utf8(serialized).length;
 }
 return {result,serialized,finalization:{serialized_bytes:serializedBytes,seconds:(Date.now()-started)/1000,maximum_ms:limits.maximum_ms,complete_within_time_and_bytes:result.complete}};

}
return {controls,run};
})()