(() => {
"use strict";
// Source-only preparation. No run is authorized by this factory or configuration.
const PIN={
 codec:"fbccc2396bfbe6085576f02468ef0acd23182445837c02abd5d05e00b9e87a00",
 edges:"411052a41a473bb7199fe277516fb60c54018dec120309622a499229579791bb",
 rows:"2adfcc619820604a3f49463bd0fd8109113ab7ce13bceadcc49554533b09dd1c",
 retained:"b53cff225273f025bc9b6d8e2cd6a654291993df8da4d0345a0dc2312b0dafac",
 model:"4a9b24ab1a0a1758ffedab226a9c45fe7765fafc40e76e23a039c9ccd098aee2"
};
const LIMITS={inventory_ms:30000,total_ms:60000,report_bytes:16777216,channels:21600};
const OLD_VARIABLES=68934,OLD_ROWS=257594,FOUR_START=227270,MIXED_START=154430;
function need(x,m){if(!x)throw Error(m);}
function eq(a,b,m){need(JSON.stringify(a)===JSON.stringify(b),m);}
function integer(x,lo,hi){need(Number.isSafeInteger(x)&&x>=lo&&x<=hi,"integer range");return x;}
function pop(x){let n=0;for(;x;x&=x-1)n++;return n;}
function order(a,b){for(let i=0;i<Math.min(a.length,b.length);i++)if(a[i]!==b[i])return a[i]-b[i];return a.length-b.length;}
function hash(c,s){return c.sha256(c.utf8(s));}
function same(a,b){need(a.path===b.path&&a.sha256===b.sha256,"authority reference");if(a.bytes!==undefined&&b.bytes!==undefined)need(a.bytes===b.bytes,"authority bytes");}
function sortedInts(a,lo,hi){need(Array.isArray(a),"array");let p=lo-1;for(const x of a){integer(x,lo,hi);need(x>p,"strict integer order");p=x;}}
function inputs(cfg,payload,c,tick){
 const names=["domain","overlay","four_inventory","four_finalization","four_certificate_replay",
 "four_certificate_finalization","four_root_acceptance","native_root_acceptance","native_cold"];
 eq(Object.keys(cfg.inputs).sort(),names.slice().sort(),"exact input family");
 eq(Object.keys(payload).sort(),names.slice().sort(),"exact payload family");
 const data={};
 for(const name of names){
  tick();const r=cfg.inputs[name],s=payload[name];need(typeof s==="string","text or base64 input");
  const archive=r.encoding==="base64_gzip"?c.base64(s):c.utf8(s);
  need(archive.length===r.bytes&&c.sha256(archive)===r.sha256&&c.gitBlob(archive)===r.git_blob,"input binding "+name);
  const raw=r.encoding==="base64_gzip"?c.gunzip(archive):archive;
  if(r.raw_sha256)need(c.sha256(raw)===r.raw_sha256,"raw binding "+name);
  data[name]=JSON.parse(c.ascii(raw));
 }
 const f=data.four_inventory,fin=data.four_finalization,replay=data.four_certificate_replay;
 const rf=data.four_certificate_finalization,root=data.four_root_acceptance,nr=data.native_root_acceptance,nc=data.native_cold;
 need(f.status==="COMPLETE_INDEPENDENT_ORIGINAL_KEYS_AND_ACTUAL_CROSS_QUOTA_CERTIFICATES"&&f.complete===true,"complete accepted four inventory");
 need(fin.status==="COMPLETE_FORWARD_AND_SERIALIZATION_WITHIN_DECLARED_BOUNDS"&&fin.complete_within_declared_bounds===true,"four finalization");
 same(fin.report,cfg.inputs.four_inventory);
 need(replay.status==="PASS_EVERY_ORIGINAL_ROW_ORIGIN_AND_MIXED_LINEAR_CERTIFICATE","four certificate replay");
 need(rf.status==="PASS_COMPLETE_ARTIFACT_REPLAY_AND_SERIALIZATION_WITHIN_BOUND","four replay finalization");
 need(root.status==="ROOT_ACCEPTS_COMPLETE_FOUR_EXTERIOR_RECONSTRUCTION_AND_49458_MIXED_REDUNDANCY_CERTIFICATES","four root acceptance");
 same(root.complete_reconstruction,cfg.inputs.four_inventory);same(root.certificate_replay,cfg.inputs.four_certificate_replay);
 same(root.certificate_finalization,cfg.inputs.four_certificate_finalization);
 need(nr.status==="ROOT_ACCEPTS_COMPLETE_STRENGTHENED_NATIVE_MODEL_AND_INDEPENDENT_COLD","native root acceptance");
 same(nr.independent_cold,cfg.inputs.native_cold);
 need(nc.status==="PASS_INDEPENDENT_COMPLETE_STRENGTHENED_LITERAL_NATIVE_APPEND"&&nc.complete_parent_bytes_checked===true,"native cold acceptance");
 need(nr.model_raw_sha256===PIN.model&&nc.model_raw_sha256===PIN.model,"fixed native model");
 need(nr.variables===OLD_VARIABLES&&nc.variables===OLD_VARIABLES&&nr.rows===OLD_ROWS&&nc.rows===OLD_ROWS,"fixed native size");
 need(nr.family_counts.four_retained===23010&&nr.family_terms.four_retained===401874,"accepted native four counts");
 need(nc.all_appended_rows_compared_exactly===89544&&nc.all_appended_terms_checked===600360,"complete native family replay");
 need(root.ordered_row_keys_sha256===PIN.rows&&f.ordered_row_keys_sha256===PIN.rows,"accepted original key hash");
 need(hash(c,JSON.stringify(f.row_keys))===PIN.rows,"actual complete original keys");
 eq(f.retained_row_ids,replay.retained_row_ids,"retained list equality");
 sortedInts(f.retained_row_ids,0,72467);
 need(f.retained_row_ids.length===23010&&hash(c,JSON.stringify(f.retained_row_ids))===PIN.retained,"actual retained IDs");
 need(root.retained_row_ids_sha256===PIN.retained&&replay.retained_row_ids_sha256===PIN.retained,"retained authority");
 need(root.retained_rows===23010&&root.retained_terms===401874&&root.all_saved_row_masks_and_retained_ids_checked===true,"accepted retained family");
 need(f.row_keys.length===72468&&f.cases.length===73404&&f.core_pairs.length===48,"complete saved inventory sizes");
 return data;
}
function graph(d,o,c,tick){
 need(d.status==="complete component-zero exterior-row domain preparation"&&d.hypothetical_graph_symmetry_assumed===false,"literal domain");
 const h=d.signature_domain,q=d.row_targets,core=d.component_adjacency_rows;
 need(h.length===480&&q.length===480&&core.length===18,"domain dimensions");
 const masks=h.map(s=>{need(s.length===3,"weight three");sortedInts(s,0,17);return s.reduce((m,i)=>m|(1<<i),0);});
 need(new Set(masks).size===480,"distinct signatures");
 for(let a=0;a<480;a++){tick();need(q[a].length===18,"18 quotas");for(let i=0;i<18;i++)need(q[a][i]===2-((masks[a]>>>i)&1)-pop(core[i]&masks[a]),"actual mixed quota");}
 const edges=[],neighbors=Array.from({length:480},()=>[]),index=new Int32Array(480*480);index.fill(-1);
 for(let a=0;a<480;a++){tick();for(let b=a+1;b<480;b++){
  if(pop(masks[a]&masks[b])>1||h[a].some(i=>q[b][i]<=0)||h[b].some(i=>q[a][i]<=0))continue;
  const e=edges.length;edges.push([a,b]);neighbors[a].push(b);neighbors[b].push(a);index[480*a+b]=index[480*b+a]=e;
 }}
 need(edges.length===68394&&hash(c,JSON.stringify(edges))===PIN.edges,"original eligible edge IDs");
 eq(neighbors,d.possible_neighbor_signature_ids,"all original neighbor lists");
 need(o.status==="COMPLETE_LITERAL_PRISM_ZEROS_AND_CORE_PAIR_CLIQUES"&&o.complete_edge_order_sha256===PIN.edges&&o.zero_rows.length===1884,"old literal zero authority");
 const zeros=new Set();
 for(let k=0;k<o.zero_rows.length;k++){const z=o.zero_rows[k];integer(z.edge_id,0,68393);need(!zeros.has(z.edge_id),"distinct old zeros");
  need(z.variable_index===540+z.edge_id&&z.native_row_index===163070+k,"old zero native identity");eq(z.witness.pair,edges[z.edge_id],"old zero endpoints");zeros.add(z.edge_id);}
 return {h,q,core,masks,edges,neighbors,index,zeros};
}
function inventory(data,c,tick,progress){
 const f=data.four_inventory,g=graph(data.domain,data.overlay,c,tick),origins=Array.from({length:72468},()=>[]);
 for(let k=0;k<f.cases.length;k++){if((k&1023)===0)tick();const a=f.cases[k];need(a.length===7&&a.every(Number.isSafeInteger),"saved case shape");
  if(a[3]>=0){integer(a[3],0,72467);origins[a[3]].push(k);}}
 const channels=[],channelIndex=new Map(),mixed=new Map(),starCache=new Map(),replacements=[],links=[];
 const corePairs=new Set(f.core_pairs.map(p=>{need(p.length===2,"core pair");integer(p[0],0,17);integer(p[1],p[0]+1,17);return p.join(",");}));
 need(corePairs.size===48,"distinct accepted core pairs");
 function mixedWitness(center,site){
  const key=18*center+site;if(mixed.has(key))return mixed.get(key);
  need(g.q[center][site]===1,"quota-one witness");
  const edges=g.neighbors[center].filter(a=>(g.masks[a]&(1<<site))!==0).map(a=>g.index[480*center+a]).sort((a,b)=>a-b);
  const record={mixed_index:key,native_row_index:MIXED_START+key,center,site,positive_original_edge_ids:edges,selector_coefficient:-1};
  mixed.set(key,record);return record;
 }
 function star(center,i,j){
  const pair=[Math.min(i,j),Math.max(i,j)],key=center+":"+pair.join(",");
  need(corePairs.has(pair.join(",")),"accepted core pair");
  if(starCache.has(key))return starCache.get(key);
  const both=(1<<i)|(1<<j),out=g.neighbors[center].filter(a=>(g.masks[a]&both)===both)
   .map(a=>g.index[480*center+a]).filter(e=>!g.zeros.has(e)).sort((a,b)=>a-b);
  need(out.length>0,"accepted nonempty star");starCache.set(key,out);return out;
 }
 function channel(center,starEdges,witness){
  const support=new Set(witness.positive_original_edge_ids);
  for(const e of starEdges)need(support.has(e),"actual mixed coefficient support includes star");
  const key=JSON.stringify([center,starEdges]);let id=channelIndex.get(key);
  if(id===undefined){need(channels.length<LIMITS.channels,"proved channel capacity");
   id=channels.length;channelIndex.set(key,id);channels.push({center,star_edges:starEdges.slice(),mixed_witnesses:new Set(),origin_count:0});}
  channels[id].mixed_witnesses.add(witness.mixed_index);channels[id].origin_count++;return id;
 }
 let oldTerms=0,starOccurrences=0;
 for(let rank=0;rank<f.retained_row_ids.length;rank++){
  tick();const rowId=f.retained_row_ids[rank],row=f.row_keys[rowId];need(row.length===3,"retained row key");
  const [b,d,positive]=row;integer(b,0,479);integer(d,b+1,479);sortedInts(positive,0,68393);
  const central=g.index[480*b+d];need(central>=0&&!g.zeros.has(central)&&positive.includes(central),"retained central edge");
  const left=[],right=[];
  for(const e of positive){if(e===central)continue;const [u,v]=g.edges[e];
   if(u===b||v===b){need(u!==d&&v!==d,"side not central");left.push(e);}
   else {need(u===d||v===d,"every term belongs to a star");right.push(e);}}
  need(left.length>0&&right.length>0,"both nonempty retained stars");
  need(origins[rowId].length>0,"all retained rows have origins");
  let channelPair=null;
  for(const caseId of origins[rowId]){
   const [e,i,j,r,ql,qr,flags]=f.cases[caseId];
   need(e===central&&r===rowId&&ql===2&&qr===2&&flags===0&&f.row_certificate_masks[rowId]===0,"accepted retained origin");
   integer(i,0,17);integer(j,0,17);need(i!==j&&!(g.core[i]&(1<<j))&&pop(g.core[i]&g.core[j])===0,"original core pair premises");
   need((g.masks[b]&(1<<i))&&!(g.masks[b]&(1<<j))&&(g.masks[d]&(1<<j))&&!(g.masks[d]&(1<<i)),"oriented first signatures");
   need(g.q[b][i]===1&&g.q[d][j]===1&&g.q[b][j]===2&&g.q[d][i]===2,"actual own and cross quotas");
   eq(left,star(b,i,j),"complete left live star");eq(right,star(d,i,j),"complete right live star");
   const wm=mixedWitness(b,i),wn=mixedWitness(d,j),cb=channel(b,left,wm),cd=channel(d,right,wn);
   if(channelPair!==null)eq(channelPair,[cb,cd],"all origins use the same exact channels");channelPair=[cb,cd];
   links.push([caseId,0,cb,wm.mixed_index],[caseId,1,cd,wn.mixed_index]);
  }
  const union=[central,...left,...right].sort((a,b)=>a-b);eq(union,positive,"coefficient-one exact row identity");
  oldTerms+=positive.length+2;starOccurrences+=left.length+right.length;
  replacements.push([rowId,central,...channelPair]);progress.retained_rows_processed=rank+1;
 }
 need(oldTerms===401874&&starOccurrences===332844&&replacements.length===23010,"accepted retained term totals");
 const ordered=channels.map((v,id)=>({id,...v})).sort((a,b)=>a.center-b.center||order(a.star_edges,b.star_edges));
 const relabel=new Int32Array(channels.length);ordered.forEach((v,k)=>{relabel[v.id]=k;});
 for(const r of replacements){r[2]=relabel[r[2]];r[3]=relabel[r[3]];need(r[2]!==r[3],"distinct endpoint channels");}
 for(const a of links)a[2]=relabel[a[2]];
 const finalChannels=ordered.map((v,k)=>[v.center,v.star_edges,Array.from(v.mixed_witnesses).sort((a,b)=>a-b),v.origin_count]);
 const mixedRows=Array.from(mixed.values()).sort((a,b)=>a.mixed_index-b.mixed_index);
 const channelTerms=finalChannels.reduce((n,v)=>n+v[1].length+2,0),C=finalChannels.length;
 need(C<=21600,"at most 480 times 3 times 15 distinct center/core-pair stars");
 progress.complete=true;
 return {channels:finalChannels,origin_links:links,replacements,mixed_witnesses:mixedRows,
  counts:{retained_rows:23010,old_four_terms:oldTerms,old_star_occurrence_terms:starOccurrences,
   channel_variables:C,channel_equalities:C,unique_star_edge_terms:channelTerms-2*C,
   channel_equality_terms:channelTerms,three_term_rows:23010,three_term_row_terms:69030,
   replacement_block_rows:C+23010,replacement_block_terms:channelTerms+69030,
   term_change_vs_old_four:channelTerms+69030-oldTerms,
   proposed_model_variables:OLD_VARIABLES+C,proposed_model_rows:OLD_ROWS+C,
   complete_origin_links:links.length,unique_quota_one_mixed_witnesses:mixedRows.length}};
}
function run(configurationText,payload,codecText,sourceText){
 const started=Date.now(),c=eval(codecText),cfg=JSON.parse(configurationText),progress={complete:false,retained_rows_processed:0};
 let data=null,derived=null,error=null,inventoryStarted=null;
 const tick=()=>{const now=Date.now();need(now-started<LIMITS.total_ms,"total deadline");
  if(inventoryStarted!==null)need(now-inventoryStarted<LIMITS.inventory_ms,"inventory deadline");};
 try{
  need(hash(c,codecText)===PIN.codec,"exact codec");need(cfg.schema==="conway99.f0.four-star-channel-configuration.v1","configuration schema");
  need(hash(c,sourceText)===cfg.source.sha256&&c.gitBlob(c.utf8(sourceText))===cfg.source.git_blob,"source binding");
  eq(cfg.limits,LIMITS,"fixed limits");need(cfg.native_model_builds===0&&cfg.optimizer_calls===0,"inventory only");
  data=inputs(cfg,payload,c,tick);tick();inventoryStarted=Date.now();
  derived=inventory(data,c,tick,progress);tick();
 }catch(e){error={name:e.name,message:String(e.message)};}
 const report={schema:"conway99.f0.four-star-channel-inventory.v1",
  status:derived&&error===null?"PASS_COMPLETE_EXACT_STAR_CHANNEL_INVENTORY":"PARTIAL_OR_UNACCEPTED_STAR_CHANNEL_INVENTORY",
  complete:!!derived&&error===null,source:cfg.source,configuration_sha256:hash(c,configurationText),inputs:cfg.inputs,
  limits:LIMITS,progress,error,derived,original_model_raw_sha256:PIN.model,
  encoding:{old_variables:OLD_VARIABLES,new_variable_start:OLD_VARIABLES,old_four_start:FOUR_START,
   channel_fields:["center","sorted_star_original_edge_ids","quota_one_mixed_indices","origin_count"],
   origin_link_fields:["original_case_id","side_0_left_1_right","channel_id","mixed_index"],
   replacement_fields:["original_row_id","central_original_edge_id","left_channel_id","right_channel_id"],
   channel_variable:"p[channel]=68934+channel",
   equality:"p[channel] + sum(y_e for e in star) - x_center = 0",
   inequality:"y_central - p[left] - p[right] in [-2,0]",
   optional_boolean_clause:"not y_central or p[left] or p[right]",
   native_clause_literal_indices:"[-(540+central_edge_id)-1,68934+left_channel,68934+right_channel]",
   proposed_row_order:"Unchanged rows before old four block; all channel equalities; three-term rows in retained order; unchanged remaining rows.",
   projected_real_polyhedron_preserved_with_linear_clause_relaxation:true,
   integer_feasible_projection_preserved:true,unique_channel_extension:true,
   root_gate_and_independent_native_replay_required_before_any_future_model_use:true},
  native_model_built:false,existing_model_changed:false,solver_calls:0,controls_run:0,
  graph_constructed:false,whole_component_excluded:false,seconds_before_serialization:(Date.now()-started)/1000};
 const serialized=JSON.stringify(report)+"\n";for(let i=0;i<serialized.length;i++)need(serialized.charCodeAt(i)<128,"ASCII report");
 const elapsed=Date.now()-started,within=elapsed<LIMITS.total_ms&&serialized.length<=LIMITS.report_bytes;
 return {report,serialized,finalization:{schema:"conway99.f0.four-star-channel-finalization.v1",
  status:report.complete&&within?"PASS_COMPLETE_CHANNEL_INVENTORY_AND_SERIALIZATION":"UNACCEPTED_PARTIAL_OR_RESOURCE_BOUND",
  complete:report.complete&&within,elapsed_ms:elapsed,inventory_ms:inventoryStarted===null?null:Date.now()-inventoryStarted,
  report_bytes:serialized.length,within_declared_bounds:within,main_calls:1,automatic_retries:0,
  publication_hashes_outside_main:true}};
}
return {run};
})()
