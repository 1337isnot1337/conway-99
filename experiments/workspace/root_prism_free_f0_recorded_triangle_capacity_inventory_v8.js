(() => {
"use strict";
const check=(v,m)=>{if(!v)throw Error(m);};
const eq=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
const pair=(a,b)=>a<b?[a,b]:[b,a];
const pk=(a,b)=>pair(a,b).join(",");
function pop(v){let n=0;for(;v;v&=v-1)n++;return n;}
function derive(D,I,O,F,L,tick){
 check(I.status==="PASS_EXACT_SHARED_TRIANGLE_INDICATOR_INVENTORY","indicator status");
 check(D.status==="complete component-zero exterior-row domain preparation","domain status");
 check(O.status==="COMPLETE_LITERAL_PRISM_ZEROS_AND_CORE_PAIR_CLIQUES","overlay status");
 check(F.status==="PASS_COMPLETE_48_PAIR_FOREST_SUPPORT_AND_LITERAL_ROW_INVENTORY"&&F.complete,"forest status");
 check(L.parent_variables===68934&&L.parent_rows===257594&&L.triangle_variable_start===71382
       &&L.triangle_variables===5364&&L.triangle_and_start===260042
       &&L.triangle_target_start===281498&&L.forest_variable_start===76746
       &&L.forest_row_start===281582&&L.variables===80730&&L.rows===297470,"layout");
 const H=D.signature_domain,Q=D.row_targets,B=D.component_core_rows;
 check(H.length===480&&Q.length===480&&B.length===21,"domain dimensions");
 const gram=(i,j)=>12*Number(i===j)+2-pop(B[i+3]&B[j+3])-((B[i+3]>>>(j+3))&1);
 const gramMap=new Map();let original=0,native=4440;
 for(let i=0;i<18;i++)for(let j=i;j<18;j++){
  const n=H.filter(h=>h.includes(i)&&h.includes(j)).length,q=gram(i,j);
  gramMap.set(pk(i,j),{original,native:n?native:null,quota:q});
  if(n)native++;else check(q===0,"empty Gram quota");original++;
 }
 check(original===171&&native===4590,"Gram row map");
 const k0=H.map(h=>{check(h.length===3,"signature width");let n=0;
  for(let i=0;i<3;i++)for(let j=i+1;j<3;j++)n+=(D.component_adjacency_rows[h[i]]>>>h[j])&1;
  check(n===0||n===1,"k0");return n;});
 for(let a=0;a<480;a++)check(H[a].reduce((s,i)=>s+Q[a][i],0)===3-2*k0[a],"overlap-one quota identity");
 check(I.triangles.length===5364&&I.targets.length===84
       &&I.target_triangle_incidences===5364,"indicator dimensions");
 const targetMap=new Map(I.targets.map((t,i)=>[t.edge_id,{...t,target_index:i}]));
 check(targetMap.size===84,"target uniqueness");
 const E=new Map(),byPair=new Map(),incident=Array.from({length:480},()=>[]);
 const tri=I.triangles;
 for(let ti=0;ti<tri.length;ti++){
  const t=tri[ti],[a,b,c]=t.vertices;
  check(t.triangle_index===ti&&0<=a&&a<b&&b<c&&c<480,"ordered triangle");
  check(t.edge_ids.length===3&&t.origins.length===1,"triangle metadata");
  check(t.edge_ids.filter(e=>targetMap.has(e)).length===1
        &&t.edge_ids.includes(t.origins[0].target_edge_id),"unique target origin");
  for(const [u,v,w]of[[a,b,c],[a,c,b],[b,c,a]]){
   const j=u===a?(v===b?0:1):2,e=t.edge_ids[j],key=pk(u,v);
   check(Number.isSafeInteger(e)&&e>=0&&e<68394,"edge id");
   check(!H[u].some(i=>H[v].includes(i)),"triangle signatures must be disjoint");
   if(!E.has(e))E.set(e,{edge_id:e,endpoints:[u,v],triangle_indices:[],thirds:[],and_upper_native_rows:[]});
   const row=E.get(e);check(eq(row.endpoints,[u,v]),"edge endpoint consistency");
   if(byPair.has(key))check(byPair.get(key)===e,"pair id consistency");else byPair.set(key,e);
   row.triangle_indices.push(ti);row.thirds.push(w);row.and_upper_native_rows.push(L.triangle_and_start+4*ti+j);
  }
  incident[a].push(ti);incident[b].push(ti);incident[c].push(ti);
 }
 for(const t of I.targets){const e=E.get(t.edge_id);check(e&&eq(e.endpoints,t.endpoints)
  &&eq(e.triangle_indices,t.triangle_indices),"target equality incidence");}
 const motifs=new Map(D.motif_pairs.map((p,i)=>[p.join(","),i])),cliques=new Map();
 O.clique_rows.forEach((r,i)=>{const c={index:i,native:r.native_row_index,
  neighbors:new Set(r.live_neighbors_and_edge_ids.map(z=>z[0]))};
  if(!cliques.has(r.center))cliques.set(r.center,[]);cliques.get(r.center).push(c);});
 const forests=new Map(F.derived.pairs.map((p,i)=>[p.anchor_pair.join(","),{...p,index:i}]));
 check(forests.size===48,"forest pairs");
 const pairReason=(a,b,c,d)=>{
  const common=H[c].filter(i=>H[d].includes(i));
  for(let i=0;i<common.length;i++)for(let j=i+1;j<common.length;j++){
   const r=gramMap.get(pk(common[i],common[j]));
   if(r.quota===1)return["selector_gram_one",common[i],common[j],r.original,r.native];
  }
  const mi=motifs.get(pk(c,d));if(mi!==undefined)return["selector_motif",mi,4591+mi];
  for(const center of[a,b])for(const i of common)if(Q[center][i]===1)
   return["mixed_one",center,i,154430+18*center+i];
  for(const center of[a,b])for(const r of cliques.get(center)||[])
   if(r.neighbors.has(c)&&r.neighbors.has(d))return["core_pair_clique",r.index,r.native];
  return null;
 };
 const edgeInventory=[...E.values()].sort((u,v)=>u.edge_id-v.edge_id),capacities=[];
 const counts={triangles:tri.length,indicator_incidences:3*tri.length,
  edges:edgeInventory.length,target_edges:84,singleton_non_target_edges:0,
  candidate_side_capacities:0,side_capacity_indicator_terms:0,side_capacity_total_terms:0,
  pair_tests:0,pairs_with_known_conflict:0,pairs_without_selected_conflict:0,
  all_pairs_known_incompatible_rows:0,forest_cap_one_rows:0,
  rows_with_selected_boolean_implication:0,rows_unresolved_by_selected_criteria:0,
  local_nonempty_rows:0,local_empty_tautologies:0,local_indicator_terms:0,
  local_total_terms:0,local_and_activation_implied_rows:0,
  side_multiplicity_histogram:{},local_cap_by_k0:{},pair_reason_counts:{}};
 for(const e of edgeInventory){
  const n=e.triangle_indices.length,[a,b]=e.endpoints;
  check(new Set(e.thirds).size===n,"distinct triangles per edge");
  if(targetMap.has(e.edge_id)){e.disposition="existing_target_equality";
   e.existing_target_native_row=L.triangle_target_start+targetMap.get(e.edge_id).target_index;continue;}
  counts.side_multiplicity_histogram[n]=(counts.side_multiplicity_histogram[n]||0)+1;
  if(n===1){e.disposition="existing_singleton_AND_upper";counts.singleton_non_target_edges++;continue;}
  e.disposition="proposed_side_capacity";e.proposal_index=capacities.length;
  const certs=[],unresolved=[];
  for(let j=0;j<n;j++)for(let k=j+1;k<n;k++){
   counts.pair_tests++;const r=pairReason(a,b,e.thirds[j],e.thirds[k]);
   if(r){certs.push([j,k,...r]);counts.pairs_with_known_conflict++;
    counts.pair_reason_counts[r[0]]=(counts.pair_reason_counts[r[0]]||0)+1;
   }else{unresolved.push([j,k]);counts.pairs_without_selected_conflict++;}
  }
  let forestWitness=null;const f=forests.get(pk(a,b));
  if(f){
   check(f.status==="PROPOSED_COMPLETE_FOREST_EXTENSION","active forest");
   const wedges=new Map(f.wedges.map(w=>[w[0],w])),witnesses=[];
   for(const c of e.thirds){const w=wedges.get(c);
    check(w&&eq(w.slice(1,3),[byPair.get(pk(a,c)),byPair.get(pk(b,c))]),"forest live wedge coverage");
    witnesses.push([c,w[3]+7812]);
   }
   const offset=f.native_row_start-257594,m=f.wedges.length,Z=f.aggregate_variable;
   check(eq(F.derived.proposed_native_row_keys[offset+3*m+1],[-1,0,[[a,-1],[Z,1]]])
    &&eq(F.derived.proposed_native_row_keys[offset+3*m+2],[-1,0,[[b,-1],[Z,1]]]),"forest Z bounds");
   forestWitness={pair_index:f.index,wedge_variables:witnesses,aggregate_variable:Z+7812,
    aggregate_equality_native_row:f.native_row_start+23988+3*m,
    aggregate_bound_native_rows:[f.native_row_start+23988+3*m+1,f.native_row_start+23988+3*m+2]};
  }
  const allPairs=unresolved.length===0,implied=allPairs||forestWitness!==null;
  if(allPairs)counts.all_pairs_known_incompatible_rows++;if(forestWitness)counts.forest_cap_one_rows++;
  if(implied)counts.rows_with_selected_boolean_implication++;else counts.rows_unresolved_by_selected_criteria++;
  const terms=[[540+e.edge_id,-1],...e.triangle_indices.map(t=>[L.triangle_variable_start+t,1])];
  capacities.push({edge_id:e.edge_id,endpoints:e.endpoints,triangle_indices:e.triangle_indices,
   third_selectors:e.thirds,proposed_native_row_key:[-1,0,terms],
   pair_conflicts:certs,pairs_not_resolved_by_selected_conflicts:unresolved,
   forest_boolean_witness:forestWitness,boolean_implication_proved:implied,
   continuous_implication_claimed:false,full_model_independence_claimed:false});
  counts.candidate_side_capacities++;counts.side_capacity_indicator_terms+=n;counts.side_capacity_total_terms+=terms.length;
 }
 tick("edge incidence and sufficient implications");
 const localRows=[],empty=[];
 for(let a=0;a<480;a++){
  const ids=incident[a],cap=2+k0[a];if(!ids.length){empty.push(a);counts.local_empty_tautologies++;continue;}
  const direct=ids.length<=cap,terms=[[a,-cap],...ids.map(t=>[L.triangle_variable_start+t,1])];
  localRows.push({selector:a,k0:k0[a],triangle_indices:ids,proposed_native_row_key:[-cap,0,terms],
   original_degree_native_row:153950+a,overlap_one_mixed_native_rows:H[a].map(i=>154430+18*a+i),
   overlap_one_degree_coefficient:3-2*k0[a],overlap_zero_degree_coefficient:5+2*k0[a],
   direct_AND_activation_implication:direct,implied_by_all_side_capacities_for_Boolean_originals:true,
   continuous_implication_from_edge_capacities_claimed:false});
  counts.local_nonempty_rows++;counts.local_indicator_terms+=ids.length;counts.local_total_terms+=terms.length;
  if(direct)counts.local_and_activation_implied_rows++;
  counts.local_cap_by_k0[k0[a]]=(counts.local_cap_by_k0[k0[a]]||0)+1;
 }
 check(eq([counts.edges,counts.target_edges,counts.singleton_non_target_edges,counts.candidate_side_capacities],
          [6300,84,3312,2904]),"edge disposition counts");
 check(eq([counts.side_capacity_indicator_terms,counts.side_capacity_total_terms,counts.pair_tests],[7416,10320,6852]),"side terms");
 check(eq([counts.local_nonempty_rows,counts.local_empty_tautologies,counts.local_indicator_terms,counts.local_total_terms],[420,60,16092,16512]),"local counts");
 check(eq([counts.all_pairs_known_incompatible_rows,counts.forest_cap_one_rows,
 counts.rows_with_selected_boolean_implication,counts.rows_unresolved_by_selected_criteria],[1548,48,1596,1308]),"sufficient implication counts");
 const example={vertices:[0,91,325,479],triangle_indices:[0,1],side_edge:16,
  positive_edge_ids:[16,170,252,25269,25351],native_side_capacity:[-1,0,[[556,-1],[71382,1],[71383,1]]],
  binary_partial_assignment_only:true,full_original_equalities_satisfied:false,graph_witness:false};
 const ps=new Set(example.positive_edge_ids),selected=new Set(example.vertices);
 for(let ti=0;ti<tri.length;ti++)check(tri[ti].edge_ids.every(e=>ps.has(e))===example.triangle_indices.includes(ti),"partial diamond AND");
 for(const t of I.targets)check(Number(ps.has(t.edge_id))===t.triangle_indices.filter(ti=>example.triangle_indices.includes(ti)).length,"partial diamond target equation");
 example.mixed_residuals=example.vertices.map(a=>{
  const ns=example.positive_edge_ids.map(e=>E.get(e).endpoints).flatMap(([u,v])=>u===a?[v]:v===a?[u]:[]);
  const used=Array(18).fill(0);for(const b of ns)for(const i of H[b])used[i]++;
  const remaining=Q[a].map((q,i)=>q-used[i]);check(remaining.every(r=>r>=0)&&ns.length<=8,"partial diamond residual");
  return[a,remaining];
 });
 example.selector_Gram_no_overdraw=true;
 for(let i=0;i<18;i++)for(let j=i;j<18;j++)check([...selected].filter(a=>H[a].includes(i)&&H[a].includes(j)).length<=gram(i,j),"partial diamond selector quota");
 check(D.motif_pairs.every(([a,b])=>!selected.has(a)||!selected.has(b)),"partial diamond selector motif");
 tick("local rows and partial countercontrol");
 return{counts,complete_edge_incidence:edgeInventory,side_capacity_proposals:capacities,
  local_capacity_proposals:localRows,local_empty_tautologies:empty,partial_diamond:example};
}
function run(payload,configurationText,sourceText,C){
 const started=Date.now(),cfg=JSON.parse(configurationText),limit=cfg.limits.total_milliseconds;
 const tick=stage=>check(Date.now()-started<=limit,"deadline after "+stage);
 check(cfg.schema==="conway99.f0.recorded-triangle-capacity-configuration.v1","configuration schema");
 check(limit===10000&&cfg.limits.maximum_report_bytes===16777216,"limits");
 check(C.sha256(C.utf8(sourceText))===cfg.source.sha256,"source hash");
 const data={},bindings={};
 for(const [key,r]of Object.entries(cfg.inputs)){
  const bytes=r.encoding==="base64-gzip"?C.base64(payload[key]):C.utf8(payload[key]);
  check(bytes.length===r.bytes&&C.sha256(bytes)===r.sha256&&C.gitBlob(bytes)===r.git_blob,"input "+key);
  const raw=r.encoding==="base64-gzip"?C.gunzip(bytes):bytes;
  if(r.raw_sha256)check(C.sha256(raw)===r.raw_sha256,"raw input "+key);
  data[key]=JSON.parse(C.ascii(raw));bindings[key]=r;tick("input "+key);
 }
 check(data.triangle_literal_root.status==="ROOT_ACCEPTS_COMPLETE_SEPARATE_LITERAL_SUPPORT_REPLAY_AND_INDICATOR_BINDINGS","triangle literal authority");
 check(data.forest_literal_root.status==="ROOT_ACCEPTS_COMPLETE_SEPARATE_LITERAL_FOREST_SUPPORT_AND_ROWS","forest literal authority");
 check(data.combined_configuration.source_sha256===cfg.combined_producer_sha256,"combined source");
 check(data.combined_configuration.inputs.triangle_inventory.sha256===cfg.inputs.indicator.sha256
  &&data.combined_configuration.inputs.forest_inventory.sha256===cfg.inputs.forest.sha256
  &&data.combined_configuration.inputs.triangle_literal_root_acceptance.sha256===cfg.inputs.triangle_literal_root.sha256
  &&data.combined_configuration.inputs.forest_literal_root_acceptance.sha256===cfg.inputs.forest_literal_root.sha256,"combined authority links");
 const result=derive(data.domain,data.indicator,data.overlay,data.forest,data.combined_configuration.layout,tick);
 const report={schema:"conway99.f0.recorded-triangle-capacity-inventory.v1",
  status:"PASS_COMPLETE_SAVED_TRIANGLE_INCIDENCE_AND_SUFFICIENT_IMPLICATION_AUDIT",
  source:cfg.source,configuration_sha256:C.sha256(C.utf8(configurationText)),input_bindings:bindings,
  complete_with_respect_to_saved_indicator_inventory:true,original_edge_domain_reenumerated:false,
  ...result,all_2904_side_proposals_preserved:true,all_420_nonempty_local_proposals_preserved:true,
  existing_native_model_changed:false,native_model_built:false,native_solver_calls:0,
  graph_constructed:false,whole_component_excluded:false,full_model_nonredundancy_claimed:false,
  inventory_milliseconds:Date.now()-started};
 const reportText=JSON.stringify(report)+"\n";check(C.utf8(reportText).length<=cfg.limits.maximum_report_bytes,"report byte cap");
 let final={schema:"conway99.f0.recorded-triangle-capacity-finalization.v1",
  status:"PASS_COMPLETE_SERIALIZATION_WITHIN_DECLARED_BOUND",report_sha256:C.sha256(C.utf8(reportText)),
  report_bytes:C.utf8(reportText).length,total_milliseconds:Date.now()-started,maximum_milliseconds:limit,
  both_texts_must_be_preserved_before_publication:true,optimizer_calls:0};
 let finalText=JSON.stringify(final)+"\n";
 if(Date.now()-started>limit){final.status="UNACCEPTED_METADATA_FINALIZATION_BUDGET_OVERRUN";final.total_milliseconds=Date.now()-started;finalText=JSON.stringify(final)+"\n";}
 return{report_text:reportText,finalization_text:finalText};
}
return{derive,run};
})()
