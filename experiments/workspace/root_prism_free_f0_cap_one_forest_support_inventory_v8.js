(() => {
"use strict";
const PIN={
 codec:"fbccc2396bfbe6085576f02468ef0acd23182445837c02abd5d05e00b9e87a00",
 edges:"411052a41a473bb7199fe277516fb60c54018dec120309622a499229579791bb",
 cold:"e8d27725afb707867f6683604ff1f3123f8960305c721058f495883f23476349",
 theorem:"66008cb63184240d897f55f2333bbb5153e26031cd4cb96c134767a9e5723cea",
 theorem_review:"59879fd63bab3c81969e8ba978f172077ee37c1b9375093c2ecac38f982802ec",
 model:"4a9b24ab1a0a1758ffedab226a9c45fe7765fafc40e76e23a039c9ccd098aee2"
};
const LIMITS={inventory_ms:30000,total_ms:60000,report_bytes:16777216,max_new_variables:22992,max_new_rows:91920,max_new_terms:344400};
const OLD_VARS=68934,OLD_ROWS=257594,EDGE_START=540,ENDPOINT_START=17162;
function need(test,message){if(!test)throw Error(message);}
function eq(a,b,message){need(JSON.stringify(a)===JSON.stringify(b),message);}
function integer(x,lo,hi){need(Number.isSafeInteger(x)&&x>=lo&&x<=hi,"integer range");return x;}
function pop(x){let n=0;for(;x;x&=x-1)n++;return n;}
function sorted(a,lo,hi){need(Array.isArray(a),"integer array");let old=lo-1;for(const x of a){integer(x,lo,hi);need(x>old,"strict order");old=x;}}
function hash(c,s){return c.sha256(c.utf8(s));}
function same(a,b){need(a.path===b.path&&a.sha256===b.sha256,"reference identity");if(a.bytes!==undefined&&b.bytes!==undefined)need(a.bytes===b.bytes,"reference bytes");}
function loadInputs(cfg,payload,c,tick){
 const names=["domain","overlay","spectral_cold","spectral_root_acceptance","native_root_acceptance","native_cold","forest_theorem","forest_review"];
 eq(Object.keys(cfg.inputs).sort(),names.slice().sort(),"exact input keys");eq(Object.keys(payload).sort(),names.slice().sort(),"exact payload keys");
 const out={};
 for(const name of names){
  tick();const ref=cfg.inputs[name],text=payload[name];need(typeof text==="string","input string");
  const archived=ref.encoding==="base64_gzip"?c.base64(text):c.utf8(text);
  need(archived.length===ref.bytes&&c.sha256(archived)===ref.sha256&&c.gitBlob(archived)===ref.git_blob,"input binding "+name);
  const raw=ref.encoding==="base64_gzip"?c.gunzip(archived):archived;
  if(ref.raw_sha256)need(c.sha256(raw)===ref.raw_sha256,"raw input binding "+name);
  out[name]=ref.kind==="text"?c.ascii(raw):JSON.parse(c.ascii(raw));
 }
 const sc=out.spectral_cold,sr=out.spectral_root_acceptance,nr=out.native_root_acceptance,nc=out.native_cold,fr=out.forest_review;
 need(cfg.inputs.spectral_cold.sha256===PIN.cold&&cfg.inputs.forest_theorem.sha256===PIN.theorem&&cfg.inputs.forest_review.sha256===PIN.theorem_review,"fixed mathematical authority");
 need(sc.status==="PASS_COMPLETE_INDEPENDENT_SPECTRAL_GAP_PAIR_CENSUS"&&sc.complete===true,"accepted complete spectral cold");
 need(sc.all114960_saved_pair_records_checked===true&&sc.all405426_saved_integer_determinants_checked===true,"complete state acceptance");
 need(sc.mathematical.state_mask_histogram["0:1:3:3"]===48,"complete cap-one class");
 need(sr.status==="ROOT_ACCEPTS_COMPLETE_INDEPENDENT_SPECTRAL_GAP_PAIR_CENSUS"&&sr.extra_overlap_zero_common_neighbor_cap_one===48,"spectral root acceptance");
 same(sr.cold,cfg.inputs.spectral_cold);
 need(sc.input_bindings.archives.domain.archive_sha256===cfg.inputs.domain.sha256&&sc.input_bindings.archives.overlay.archive_sha256===cfg.inputs.overlay.sha256,"same domain and old-zero authority");
 need(nr.status==="ROOT_ACCEPTS_COMPLETE_STRENGTHENED_NATIVE_MODEL_AND_INDEPENDENT_COLD","native root acceptance");
 need(nc.status==="PASS_INDEPENDENT_COMPLETE_STRENGTHENED_LITERAL_NATIVE_APPEND"&&nc.complete_parent_bytes_checked===true,"accepted complete native parent");
 same(nr.independent_cold,cfg.inputs.native_cold);
 need(nr.model_raw_sha256===PIN.model&&nc.model_raw_sha256===PIN.model,"fixed current model");
 need(nr.variables===OLD_VARS&&nc.variables===OLD_VARS&&nr.rows===OLD_ROWS&&nc.rows===OLD_ROWS,"original native dimensions");
 need(nr.family_counts.spectral_edge_zero===72&&nc.family_counts.spectral_edge_zero===72,"all72 additional zero rows retained");
 need(fr.status==="PASS_COMPLETE_CONDITIONAL_POLYHEDRAL_THEOREM","forest theorem peer acceptance");same(fr.theorem,cfg.inputs.forest_theorem);
 return out;
}
function domainGraph(d,tick,c){
 need(d.status==="complete component-zero exterior-row domain preparation"&&d.hypothetical_graph_symmetry_assumed===false,"complete literal domain");
 const h=d.signature_domain,q=d.row_targets,core=d.component_adjacency_rows;
 need(h.length===480&&q.length===480&&core.length===18,"domain dimensions");
 const masks=h.map(s=>{need(s.length===3,"weight-three signature");sorted(s,0,17);return s.reduce((m,i)=>m|(1<<i),0);});
 need(new Set(masks).size===480,"distinct signatures");
 for(let a=0;a<480;a++){tick();need(q[a].length===18,"all18 quotas");for(let i=0;i<18;i++)need(q[a][i]===2-((masks[a]>>>i)&1)-pop(core[i]&masks[a]),"quota reconstruction");}
 const edges=[],neighbors=Array.from({length:480},()=>[]),index=new Int32Array(480*480);index.fill(-1);
 for(let a=0;a<480;a++){tick();for(let b=a+1;b<480;b++){
  if(pop(masks[a]&masks[b])>1||h[a].some(i=>q[b][i]<=0)||h[b].some(i=>q[a][i]<=0))continue;
  const e=edges.length;edges.push([a,b]);neighbors[a].push(b);neighbors[b].push(a);index[480*a+b]=index[480*b+a]=e;
 }}
 need(edges.length===68394&&hash(c,JSON.stringify(edges))===PIN.edges,"complete original edge namespace");
 eq(neighbors,d.possible_neighbor_signature_ids,"all original neighbor lists");
 return {h,q,masks,edges,index};
}
function zeroUnion(overlay,spectral,g){
 need(overlay.status==="COMPLETE_LITERAL_PRISM_ZEROS_AND_CORE_PAIR_CLIQUES"&&overlay.complete_edge_order_sha256===PIN.edges,"old literal-zero authority");
 need(overlay.zero_rows.length===1884,"all1884 old zero rows");
 const old=new Map(),added=new Map(),all=new Map();
 for(let k=0;k<overlay.zero_rows.length;k++){
  const z=overlay.zero_rows[k],e=integer(z.edge_id,0,68393);need(!old.has(e),"distinct old zeros");
  need(z.native_row_index===163070+k&&z.variable_index===EDGE_START+e,"old zero native identity");eq(z.witness.pair,g.edges[e],"old zero endpoints");
  old.set(e,k);all.set(e,{edge_id:e,endpoints:g.edges[e],literal_origin:k,literal_native_row:z.native_row_index,spectral_origin:null});
 }
 const records=spectral.mathematical.edge_zero_rows;need(records.length===132,"all132 spectral zero rows");
 let overlap=0;const seen=new Set();
 for(let k=0;k<records.length;k++){
  const r=records[k];need(r.length===4,"spectral zero record");const [a,b,e,wasOld]=r;integer(e,0,68393);
  need(typeof wasOld==="boolean"&&!seen.has(e),"spectral zero identity");seen.add(e);eq(g.edges[e],[a,b],"spectral zero endpoints");
  need(wasOld===old.has(e),"complete old-zero disposition");if(wasOld)overlap++;
  added.set(e,k);if(!all.has(e))all.set(e,{edge_id:e,endpoints:g.edges[e],literal_origin:null,literal_native_row:null,spectral_origin:null});
  all.get(e).spectral_origin=k;
 }
 need(overlap===60&&all.size===1956&&records.length-overlap===72,"exact1956 accepted zero union");
 return {old,spectral:added,all,ledger:Array.from(all.values()).sort((a,b)=>a.edge_id-b.edge_id)};
}
function row(lower,upper,terms){
 const combined=new Map();for(const [v,a]of terms){integer(v,0,100000);integer(a,-1,1);combined.set(v,(combined.get(v)||0)+a);}
 const ordered=Array.from(combined).filter(x=>x[1]!==0).sort((a,b)=>a[0]-b[0]);
 need(ordered.length===terms.length,"distinct nonzero row variables");
 return [lower,upper,ordered];
}
function block(a,b,live,firstVar,firstRow,origin){
 const variables=[],rows=[],rowOrigins=[],wedges=[],m=live.length;
 for(let i=0;i<m;i++){const v=firstVar+i,w=live[i];variables.push([v,"cap1_wedge_"+a+"_"+b+"_"+w.c,[0,1],origin,w.c]);wedges.push([w.c,w.edge_a,w.edge_b,v]);}
 const Z=firstVar+m;variables.push([Z,"cap1_total_"+a+"_"+b,[0,1],origin,-1]);
 const add=(kind,c,key)=>{rows.push(key);rowOrigins.push([origin,kind,c]);};
 for(const [c,ea,eb,z]of wedges){
  add(0,c,row(-2,0,[[EDGE_START+ea,1],[EDGE_START+eb,1],[c,-1],[z,-1]]));
  add(1,c,row(-1,0,[[z,1],[EDGE_START+ea,-1]]));
  add(2,c,row(-1,0,[[z,1],[EDGE_START+eb,-1]]));
 }
 add(3,-1,row(0,0,[[Z,1],...wedges.map(w=>[w[3],-1])]));
 add(4,-1,row(-1,0,[[Z,1],[a,-1]]));add(5,-1,row(-1,0,[[Z,1],[b,-1]]));
 for(const [c,ea,eb,z]of wedges)add(6,c,row(-3,0,[[EDGE_START+ea,1],[EDGE_START+eb,1],[Z,1],[z,-1],[a,-1],[b,-1]]));
 need(rows.length===4*m+3&&rows.reduce((n,r)=>n+r[2].length,0)===15*m+5,"complete extended block size");
 return {variables,rows,rowOrigins,wedges,aggregate_variable:Z,native_row_start:firstRow};
}
function endpointForest(n,allowed,edges){
 const adj=Array.from({length:n},()=>[]);
 for(const e of allowed){const [a,b]=edges[e];adj[a].push([b,e]);adj[b].push([a,e]);}
 const seen=new Uint8Array(n),parent=new Int32Array(n);parent.fill(-1);
 const roots=[],receipts=[];
 for(let root=0;root<n;root++)if(!seen[root]){
  roots.push(root);seen[root]=1;const queue=[root];
  for(let k=0;k<queue.length;k++){
   const a=queue[k];for(const [b,e]of adj[a]){
    if(b===parent[a])continue;need(!seen[b],"allowed support must be a forest");
    seen[b]=1;parent[b]=a;queue.push(b);
    const side=edges[e][0]===b?0:1;need(edges[e][side]===b,"endpoint receipt");
    receipts.push([b,a,e,ENDPOINT_START+2*e+side]);
   }
  }
 }
 need(receipts.length===allowed.length&&roots.length+receipts.length===n,"complete forest orientation");
 need(new Set(receipts.map(r=>r[0])).size===receipts.length,"injective nonroot endpoint assignment");
 return {status:"ENDPOINT_FOREST_IMPLIES_EVERY_ROOT_OMITTED_SUBSET_ROW",vertices:n,
  complete_allowed_original_edge_ids:allowed,base_component_roots:roots,parent_endpoint_receipts:receipts,
  receipt_fields:["child_selector","parent_selector","original_edge_id","native_activation_row"],
  arbitrary_root_rule:"Reverse the unique parent path from the requested root to its base component root; leave other components rooted as saved. Restrict that orientation to any vertex subset. Each retained edge is bounded by a distinct nonroot endpoint selector; unused nonroot selectors contribute nonnegative slack.",
  other_rows_or_triangle_assumptions_used:false};
}
function inventory(data,c,tick){
 const g=domainGraph(data.domain,tick,c),z=zeroUnion(data.overlay,data.spectral_cold,g);
 const originals=data.spectral_cold.mathematical.overlap_zero_selected_pair_common_exterior_neighbor_cap_one;
 need(originals.length===48,"all48 accepted unconditional cap-one pairs");
 const variables=[],rows=[],rowOrigins=[],pairs=[],seen=new Set();let previous=-1,terms=0;
 for(let origin=0;origin<originals.length;origin++){
  tick();const input=originals[origin];need(input.length===3,"cap-one origin");const [a,b,central]=input;
  integer(a,0,479);integer(b,a+1,479);integer(central,0,68393);
  need(central>previous&&!seen.has(a+","+b),"original cap-one order and uniqueness");previous=central;seen.add(a+","+b);
  eq(g.edges[central],[a,b],"cap-one original edge identity");need(pop(g.masks[a]&g.masks[b])===0,"accepted overlap-zero pair");
  const dispositions=[],live=[],allowed=new Set();let originalCommon=0;
  for(let candidate=0;candidate<480;candidate++){
   const ea=g.index[480*a+candidate],eb=g.index[480*b+candidate];let flags=candidate===a||candidate===b?1:0;
   if(ea<0)flags|=2;if(eb<0)flags|=4;
   if(z.old.has(ea))flags|=8;if(z.spectral.has(ea))flags|=16;
   if(z.old.has(eb))flags|=32;if(z.spectral.has(eb))flags|=64;
   dispositions.push([candidate,ea,eb,flags]);
   if(candidate===a||candidate===b)continue;
   if(ea>=0&&eb>=0)originalCommon++;
   if(ea>=0&&!z.all.has(ea))allowed.add(ea);
   if(eb>=0&&!z.all.has(eb))allowed.add(eb);
   // No disjoint-signature or triangle-cover filter is permitted here.
   if(flags===0)live.push({c:candidate,edge_a:ea,edge_b:eb});
  }
  need(dispositions.length===480&&live.length<=478,"complete candidate universe");
  const pair={origin_index:origin,original_spectral_cold_record:input.slice(),anchor_pair:[a,b],
   central_edge_zero_origins:z.all.get(central)||null,dispositions,original_common_candidates:originalCommon,
   live_common_candidates:live.length,live_candidates:live.map(w=>[w.c,w.edge_a,w.edge_b]),assumption_on_central_edge_value:null};
  if(live.length<=1){
   pair.status="SKIPPED_ONLY_BY_ENDPOINT_FOREST_IMPLICATION";
   pair.endpoint_forest_certificate=endpointForest(480,Array.from(allowed).sort((a,b)=>a-b),g.edges);
   pair.appended_variables=0;pair.appended_rows=0;
  }else{
   const part=block(a,b,live,OLD_VARS+variables.length,OLD_ROWS+rows.length,origin);
   pair.status="PROPOSED_COMPLETE_FOREST_EXTENSION";
   pair.wedges=part.wedges;pair.aggregate_variable=part.aggregate_variable;pair.native_row_start=part.native_row_start;
   pair.appended_variables=part.variables.length;pair.appended_rows=part.rows.length;
   for(const v of part.variables)variables.push(v);for(const r of part.rows){rows.push(r);terms+=r[2].length;}for(const p of part.rowOrigins)rowOrigins.push(p);
  }
  pairs.push(pair);
  need(variables.length<=LIMITS.max_new_variables&&rows.length<=LIMITS.max_new_rows&&terms<=LIMITS.max_new_terms,"proved complete-family size bounds");
 }
 need(pairs.length===48&&rowOrigins.length===rows.length,"all pair and row origins");
 return {zero_union_ledger:z.ledger,pairs,proposed_native_variables:variables,proposed_native_row_keys:rows,row_origins:rowOrigins,
  counts:{accepted_pairs:48,candidate_dispositions:48*480,accepted_zero_union:1956,
   extended_pairs:pairs.filter(p=>p.status==="PROPOSED_COMPLETE_FOREST_EXTENSION").length,
   endpoint_forest_skipped_pairs:pairs.filter(p=>p.status==="SKIPPED_ONLY_BY_ENDPOINT_FOREST_IMPLICATION").length,
   new_variables:variables.length,new_rows:rows.length,new_terms:terms,
   proposed_total_variables:OLD_VARS+variables.length,proposed_total_rows:OLD_ROWS+rows.length}};
}
function forestRows(A,B,t,u,v,maxSubset){
 const m=t.length;
 for(let mask=0;mask<(1<<m);mask++){
  if(maxSubset!==undefined&&pop(mask)>maxSubset)continue;
  let E=0,X=A+B;for(let i=0;i<m;i++)if(mask&(1<<i)){E+=u[i]+v[i];X+=t[i];}
  if(E>X-A||E>X-B)return false;for(let i=0;i<m;i++)if((mask&(1<<i))&&E>X-t[i])return false;
 }
 return true;
}
function controls(){
 const started=Date.now();let grid=0,binary=0,keyChecks=0;
 for(let D=1;D<=2;D++)for(let m=0;m<=2;m++){
  const length=2+3*m,total=(D+1)**length;
  for(let encoded=0;encoded<total;encoded++){
   let n=encoded;const values=[];for(let i=0;i<length;i++){values.push(n%(D+1));n=Math.floor(n/(D+1));}
   const [A,B]=values,t=[],u=[],v=[];let active=true;
   for(let i=0;i<m;i++){t.push(values[2+3*i]);u.push(values[3+3*i]);v.push(values[4+3*i]);if(u[i]>A||v[i]>B||u[i]>t[i]||v[i]>t[i])active=false;}
   if(!active)continue;grid++;
   const p=u.map((x,i)=>Math.max(0,x+v[i]-t[i])),P=p.reduce((x,y)=>x+y,0);
   const good=P<=A&&P<=B&&u.every((x,i)=>x+v[i]+P-p[i]<=A+B);
   need(good===forestRows(A,B,t,u,v),"all subsets versus minimal extension");
   const live=t.map((_,i)=>({c:2+i,edge_a:2*i,edge_b:2*i+1})),part=block(0,1,live,OLD_VARS,OLD_ROWS,0);
   const point=new Map([[0,A],[1,B],[part.aggregate_variable,P]]);
   for(let i=0;i<m;i++){point.set(2+i,t[i]);point.set(EDGE_START+2*i,u[i]);point.set(EDGE_START+2*i+1,v[i]);point.set(OLD_VARS+i,p[i]);}
   const rowsPass=part.rows.every(r=>{const q=r[2].reduce((s,[j,a])=>s+a*point.get(j),0);return r[0]*D<=q&&q<=r[1]*D;});
   need(rowsPass===good,"literal native key signs and domains");keyChecks+=part.rows.length;
   if(D===1){binary++;const common=u.reduce((s,x,i)=>s+x*v[i],0);need(good===(common<=1),"Boolean common-neighbor cap");}
  }
 }
 need(forestRows(4,4,[4],[3],[3]),"real single-wedge example");
 need(![0,4].some(z=>z>=2&&z<=3),"real original/integer auxiliary distinction");
 need(forestRows(4,4,[4,4,4],[3,3,3],[3,3,3],2)&&!forestRows(4,4,[4,4,4],[3,3,3],[3,3,3]),"larger-subset strengthening");
 const e=[[0,2],[1,2],[0,3],[1,4]],receipt=endpointForest(5,[0,1,2,3],e);
 need(receipt.base_component_roots.length===1&&receipt.parent_endpoint_receipts.length===4,"single-common-neighbor endpoint forest");
 let cyclicRejected=false;try{endpointForest(4,[0,1,2,3],[[0,2],[1,2],[0,3],[1,3]]);}catch(_){cyclicRejected=true;}
 need(cyclicRejected,"two-common-neighbor cycle is not skippable");
 need(Date.now()-started<10000,"tiny control bound");
 return {status:"PASS_SYNTHETIC_FOREST_PROJECTION_NATIVE_KEYS_AND_SKIP_CONTROLS",activated_grid_assignments:grid,
  binary_assignments:binary,literal_row_key_evaluations:keyChecks,disjoint_signature_filter_used:false,
  actual_domain_inputs_read:0,actual_pair_inventories:0,native_models:0,optimizer_calls:0,elapsed_ms:Date.now()-started};
}
function run(configurationText,payload,codecText,sourceText){
 const started=Date.now(),c=eval(codecText),cfg=JSON.parse(configurationText);let inventoryStarted=null,inventoryElapsed=null,derived=null,error=null;
 const tick=()=>{need(Date.now()-started<LIMITS.total_ms,"total deadline");if(inventoryStarted!==null)need(Date.now()-inventoryStarted<LIMITS.inventory_ms,"inventory deadline");};
 try{
  need(hash(c,codecText)===PIN.codec,"exact codec");
  need(cfg.schema==="conway99.f0.cap-one-forest-support-configuration.v1","configuration schema");
  need(hash(c,sourceText)===cfg.source.sha256&&c.gitBlob(c.utf8(sourceText))===cfg.source.git_blob,"frozen source");
  eq(Object.keys(cfg.limits).sort(),Object.keys(LIMITS).sort(),"limit keys");for(const key of Object.keys(LIMITS))need(cfg.limits[key]===LIMITS[key],"fixed limit "+key);
  need(cfg.native_model_builds===0&&cfg.optimizer_calls===0&&cfg.planned_main_calls===1&&cfg.automatic_retries===0,"one finite optimizer-free inventory");
  const data=loadInputs(cfg,payload,c,tick);tick();inventoryStarted=Date.now();derived=inventory(data,c,tick);tick();inventoryElapsed=Date.now()-inventoryStarted;
 }catch(e){error={name:e.name,message:String(e.message)};}
 const report={schema:"conway99.f0.cap-one-forest-support-inventory.v1",
  status:derived&&error===null?"PASS_COMPLETE_48_PAIR_FOREST_SUPPORT_AND_LITERAL_ROW_INVENTORY":"UNACCEPTED_FOREST_SUPPORT_INVENTORY",
  complete:!!derived&&error===null,source:cfg.source,configuration_sha256:hash(c,configurationText),inputs:cfg.inputs,
  limits:LIMITS,error,derived,inventory_phase_ms:inventoryElapsed,original_model_raw_sha256:PIN.model,
  encoding:{disposition_fields:["candidate","original_edge_ac_or_minus1","original_edge_bc_or_minus1","reason_bitmask"],
   reason_bits:{anchor:1,edge_ac_unavailable:2,edge_bc_unavailable:4,edge_ac_literal_zero:8,edge_ac_spectral_zero:16,edge_bc_literal_zero:32,edge_bc_spectral_zero:64},
   variable_fields:["native_index","name","domain","original_cap_one_index","candidate_or_minus1_for_total"],
   row_key_fields:["lower","upper","sorted_variable_coefficient_pairs"],row_origin_fields:["original_cap_one_index","kind","candidate_or_minus1"],
   row_kinds:{wedge_lower:0,wedge_upper_ac:1,wedge_upper_bc:2,total_definition:3,total_anchor_a:4,total_anchor_b:5,candidate_root:6},
   original_variables_retained:OLD_VARS,original_rows_retained:OLD_ROWS,
   complete_support_uses_only_original_eligibility_and_accepted_zero_union:true,
   signature_disjointness_or_triangle_cover_pruning:false,assumption_on_anchor_edge_value:false,
   future_model_requires_separate_literal_completeness_check_and_full_native_replay:true},
  native_model_built:false,existing_model_changed:false,optimizer_calls:0,graph_constructed:false,whole_component_excluded:false};
 const serialized=JSON.stringify(report)+"\n";for(let i=0;i<serialized.length;i++)need(serialized.charCodeAt(i)<128,"ASCII report");
 const elapsed=Date.now()-started,within=elapsed<LIMITS.total_ms&&serialized.length<=LIMITS.report_bytes;
 return {report,serialized,finalization:{schema:"conway99.f0.cap-one-forest-support-finalization.v1",
  status:report.complete&&within?"PASS_COMPLETE_FOREST_INVENTORY_AND_SERIALIZATION":"UNACCEPTED_PARTIAL_OR_RESOURCE_BOUND",
  complete:report.complete&&within,elapsed_ms:elapsed,inventory_phase_ms:inventoryElapsed,report_bytes:serialized.length,
  within_declared_bounds:within,main_calls:1,automatic_retries:0,publication_hashes_outside_main:true}};
}
return {controls,run};
})()
